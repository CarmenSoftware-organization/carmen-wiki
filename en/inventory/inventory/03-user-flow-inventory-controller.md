---
title: Inventory — User Flow — Inventory Controller
description: Inventory Controller's flow within the inventory module — balance accuracy, variance review, count coordination, stock policy.
published: true
date: 2026-05-17T11:00:00.000Z
tags: inventory, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller &nbsp;·&nbsp; **Module:** [[inventory]] &nbsp;·&nbsp; **Workflow stages:** Approve adjustments above Store Keeper threshold (`draft → in_progress → completed`) &nbsp;·&nbsp; coordinate physical-count and spot-check programmes &nbsp;·&nbsp; tune per-product / per-location stock policy &nbsp;·&nbsp; pre-period-end variance sign-off &nbsp;·&nbsp; **Key permissions:** approve above threshold (`INV_AUTH_003`); stock-policy edits (`INV_AUTH_004`); count programme owner
> **What this persona does:** Owns balance accuracy — approves above-threshold adjustments, coordinates counts, and signs off variance before Finance closes the period.

## 1. Role in This Module

The **Inventory Controller** persona owns **balance accuracy** across the property. They are the second-line authority that the Store Keeper escalates to and the first-line authority that Finance escalates from. Within the inventory module their work spans four threads: (1) **approve adjustments above the Store Keeper threshold** — every `tb_stock_in` and `tb_stock_out` document above the auto-approve cap routes to the Controller per `INV_AUTH_003`, and the Controller is the role that fires the `draft → in_progress → completed` advance on these documents; (2) **coordinate the count programme** — schedule physical counts (`tb_physical_count` driven by `tb_location.physical_count_type = yes`), run spot checks for high-velocity / high-value products, review the resulting variance per `INV_XMOD_003` / `INV_XMOD_004`, and decide which variances post (approve), which need recount (return to Store Keeper), and which need investigation (Finance handoff); (3) **maintain per-product / per-location stock policy** — par / min / max / reorder columns on `tb_product_location` driven by consumption patterns and lead time per `INV_AUTH_004`, including the suggestion engine that surfaces stock-policy outliers; (4) **pre-period-end variance sign-off** — the Controller is the gate that the Finance period-close run waits on: every count-variance adjustment in the period must be posted (approved or rejected) before Finance closes the period. Critically, the Inventory Controller does **not** post inventory-to-GL reconciliation entries (that is Finance's `INV_AUTH_005`), does **not** lock the period (that is Finance Manager's `INV_AUTH_006`), and does **not** configure location type / costing method / adjustment-type reason codes (that is Sysadmin's `INV_AUTH_008`). Segregation of duties carries through: a Controller who is also a Store Keeper at a specific location cannot approve their own document; the system routes such cases to a peer Controller or to Finance.

## 2. Entry Point and Primary Flow

**Entry points:** Five paths, all consequences of upstream activity routing into the Controller's queue or initiating from the Controller's calendar.

- **Adjustment approval queue** — `tb_stock_in` and `tb_stock_out` documents at `doc_status = in_progress` awaiting Controller approval; ordered by submitted-at ascending. Drives the daily approval flow (Section 2.1 below).
- **Count-variance dashboard** — count documents at `tb_count_stock.status = completed` with variance lines staged; drives the count-cycle approval flow (Section 2.2 below).
- **Count calendar / schedule** — `tb_physical_count_period` upcoming events and ad-hoc spot-check launches; drives count initiation (handed off to Store Keeper at the location for execution; full flow in [[physical-count]] / [[spot-check]]).
- **Stock policy dashboard** — `tb_product_location` rows with replenishment alerts (on-hand below `min_qty`, above `max_qty`), and the Controller's policy-edit screen for par / min / max / reorder.
- **Period-end pre-flight** — a dashboard rolled up from open variance documents, unposted count adjustments, and the Controller's variance-review-signoff checklist for the closing period.

### 2.1 Adjustment approval flow (Store Keeper-initiated, 6 steps)

1. **Open the adjustment approval queue.** The screen lists `tb_stock_in` and `tb_stock_out` documents at `doc_status = in_progress` with their originator (Store Keeper), location, reason code (`adjustment_type_id`), total cost impact (`Σ qty × cost_per_unit`), and any supporting attachments.
2. **Open a specific document.** The screen renders the lines, the lot-level detail, and the cost-pick preview (FIFO from oldest lot, or current weighted-average, per the product's costing method) for any outbound lines. The Controller cross-checks the discrepancy against the originating evidence — count sheet, photo of damage, vendor RMA, lot-label scan.
3. **Decide outcome.** **Approve** if the discrepancy is genuine and the reason code is appropriate. **Reject** with comment if the discrepancy looks like a counting error or the wrong reason code was picked (e.g. write-off recorded as breakage when it should be expiry — the GL classification differs). **Adjust and approve** for line-level fixes (changing the `qty` on one line; correcting a lot pick) where the overall document is sound but a line needs attention.
4. **Cost-impact gate check.** If the document's total cost impact exceeds the Controller's threshold, the screen flags it for **Finance approval** — the Controller's approval moves the document to a Finance-pending sub-state; Finance is the role that completes the approval for very-large write-offs. For normal Controller-threshold documents, the Controller's approval is terminal.
5. **Approve fires the post.** On Controller approval at the Controller's threshold: `tb_stock_in.doc_status = completed` (or `tb_stock_out.doc_status = completed`); inventory transaction writes per `INV_POST_001` / `INV_POST_002`; cost-layer rows write per the inbound / outbound type; on-hand at `(location, product, lot)` advances. The Controller's queue refreshes; the Store Keeper sees the document at `completed` in their activity log.
6. **Reject returns to Store Keeper.** On Controller rejection: `doc_status = draft` with the Controller's comment on the document's activity log; the Store Keeper sees the rejection in their inbox and edits / re-submits or voids per their flow (Section 2 of `[03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md)`).

### 2.2 Count-variance review flow (count-initiated, 7 steps)

1. **Open the count-variance dashboard.** Lists count documents (`tb_count_stock`) at `status = completed` with their location, count window, total variance amount, and per-line breakdown (overage / shortage / lot-mismatch).
2. **Open a specific count.** The screen renders per-product variance lines: system qty vs counted qty vs variance, lot-level breakdown, cost impact per line at the system's most recent cost-layer cost. Re-count attachments and Store Keeper notes are visible.
3. **Per-line decision.** For each variance line, decide: **post** (variance is genuine; will write a `tb_stock_in` (overage) / `tb_stock_out` (shortage) document automatically on commit), **re-count** (variance is suspicious; routes back to the Store Keeper for re-count), or **investigate** (variance is large and unexplained; routes to Finance for an investigation flag without posting yet).
4. **Cost-impact aggregation.** The screen sums the cost impact of all `post` decisions in the count; if the aggregate exceeds the Controller's threshold, the post-on-commit gate routes to Finance approval (analogous to step 4 of Section 2.1).
5. **Commit decisions.** Click **Commit count decisions** — the system creates one `tb_stock_in` document (rolling up all overage lines from this count) and one `tb_stock_out` document (rolling up all shortage lines), each with `adjustment_type_id` set to a count-derived reason code (`COUNT_OVERAGE` / `COUNT_SHORTAGE`); each document carries the count reference on its `info` JSON or activity log.
6. **Posts fire.** The stock-in and stock-out documents auto-advance through `draft → in_progress → completed` because Controller approval is implicit in the count-commit action (the Controller is the actor on the commit). Inventory transactions write per Section 2.1 step 5; on-hand reconciles to the counted qty.
7. **Update the count document.** `tb_count_stock.status = completed_posted` (or similar terminal state); the count record is closed with the variance breakdown preserved for audit; subsequent on-hand reads return the corrected balance.

The decision branches and the stock-policy / period-end pre-flight flows are summarised in Section 3.

## 3. Decision Branches

- **Approve adjustment vs reject for re-evaluation.** Approve when the discrepancy is documented (photo, count sheet, RMA reference) and the reason code is appropriate. Reject and return to the Store Keeper if (a) the evidence is missing or insufficient, (b) the reason code is wrong (causing wrong GL classification — e.g. `BREAKAGE` vs `EXPIRY` route to different GL accounts), (c) the cost-per-unit on a stock-in (existing lot) doesn't match the lot's recorded cost.
- **Below vs above Controller threshold.** Below — Controller approval is terminal; document posts on approval. Above — Controller approval moves the document to a Finance-pending sub-state; Finance is the role that fires the post per the threshold-routing chain in `INV_AUTH_005`. The threshold is configured by Sysadmin per `INV_AUTH_008`.
- **Count variance: post / re-count / investigate.** **Post** when the variance is plausible (within normal shrinkage / overage range, or explained by a known event like recall write-off) and below the Controller's per-line threshold. **Re-count** when the variance is suspicious — significantly larger than historical shrinkage rate, or affecting a high-value product with no known event. **Investigate** when the variance is large enough to suggest systemic issues (large overage suggests missed inbound; large shortage suggests theft or large unrecorded breakage) — Finance is the next stop with a no-post flag.
- **Stock-policy outlier vs normal.** Replenishment alerts surface when on-hand drops below `min_qty` (suggesting reorder) or rises above `max_qty` (suggesting overstock). The Controller may **act** on the alert (raise a `[[purchase-request]]` to replenish, or initiate a transfer to redistribute), **adjust the policy** (revise `min_qty` / `max_qty` / `re_order_qty` / `par_qty` on `tb_product_location` if the alert reveals a stale policy), or **dismiss** (one-off event, no policy change). Policy edits apply prospectively; existing on-hand is unaffected.
- **Period-end variance signoff vs hold.** **Sign off** when (a) no `in_progress` adjustment documents remain in the closing period, (b) every count run for the period is `completed_posted`, (c) no `investigate`-flagged count variance is unresolved. **Hold** when any of those gates is open — the Controller communicates the hold to Finance with the open items and the expected resolution date. Period close cannot run without Controller sign-off per the cross-persona handoff in `[03-user-flow.md](./03-user-flow.md)` Section 4.

## 4. Exit Point / Handoffs

The Inventory Controller's involvement on a given movement / count / period ends at one of four boundaries:

- **Adjustment approved and posted.** Below-Controller-threshold approval fires the post; document `completed`; inventory transaction written; on-hand advanced. The Controller's queue refreshes; no further action on this document. The Store Keeper sees `completed` in their activity log.
- **Adjustment escalated to Finance.** Above-Controller-threshold approval moves the document to Finance-pending; handoff to **Finance** ([03-user-flow-finance.md](./03-user-flow-finance.md)) for cost-impact approval per `INV_AUTH_005`. The Controller re-engages only if Finance rejects (the document returns to `draft` with Finance's comment) or asks for additional supporting evidence.
- **Count variance committed.** The count-commit fires the stock-in / stock-out rollup posts; the count document moves to `completed_posted`; on-hand is reconciled. Handoff back to **Store Keeper** if any line was returned for re-count; handoff to **Finance** if any line was `investigate`-flagged (with the no-post hold).
- **Period-end variance sign-off.** The Controller signs off; handoff to **Finance** for the inventory-to-GL reconciliation and the period-close run per `INV_POST_009`. The Controller re-engages only if Finance flags a reconciliation variance that requires Controller-side investigation (typically a counted-but-not-posted variance the Controller's signoff missed).

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical movement-and-period lifecycle, the cross-persona handoff table that anchors Store Keeper → Inventory Controller (adjustment approval) and Inventory Controller → Finance (cost-impact approval, period-end sign-off) boundaries.
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — upstream persona that initiates the `tb_stock_in` / `tb_stock_out` documents the Controller approves, and that executes the physical / spot counts whose variance the Controller reviews.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — downstream persona for above-Controller-threshold approvals and for the period-end inventory-to-GL reconciliation.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator who configures the `tb_adjustment_type` reason-code list (which the Controller's rejection logic depends on for correct GL classification) and the Controller / Finance approval thresholds; Auditor who reviews the Controller's approval audit trail.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `tb_stock_in` / `tb_stock_out` shape, `tb_product_location` (the policy table the Controller maintains under `INV_AUTH_004`), `tb_count_stock` / `tb_physical_count_period` (the count documents the Controller reviews), `enum_inventory_doc_type` values (`stock_in`, `stock_out`).
- Sibling: [02-business-rules.md](./02-business-rules.md) — authorization rules `INV_AUTH_003` (Controller approval right), `INV_AUTH_004` (stock policy edit), `INV_AUTH_010` (Controller cannot approve their own document), plus posting rules `INV_POST_001` (inbound post on Controller approval) / `INV_POST_002` (outbound post), and cross-module rules `INV_XMOD_003` / `INV_XMOD_004` (count-variance posting), `INV_XMOD_005` (manual adjustment routing).
- Related: [[physical-count]] — the count programme the Controller coordinates; the count document's `tb_count_stock` lifecycle is owned by the physical-count module's persona files. This page covers only the inventory-side post arising from a completed count.
- Related: [[spot-check]] — mid-period partial counts; same posting path as physical-count.
- Related: [[inventory-adjustment]] — generic name for the manual `tb_stock_in` / `tb_stock_out` flow the Controller approves; reason code (`adjustment_type_id`) distinguishes the specific use case.
- Related: [[costing]] — the cost-pick preview the Controller reviews on outbound (FIFO from oldest lot vs current weighted-average) reads from `tb_inventory_transaction_cost_layer` per the product's costing method.
- Related: [[product]] — carries the `costing_method` field that drives the cost-pick preview. Sysadmin owns the configuration; the Controller's approval flow consumes it.
