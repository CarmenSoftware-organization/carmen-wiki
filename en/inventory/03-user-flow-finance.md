---
title: Inventory — User Flow — Finance
description: Finance's flow within the inventory module — valuation verification, inventory-to-GL reconciliation, period close and lock.
published: true
date: 2026-05-15T12:00:00.000Z
tags: inventory, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Finance

## 1. Role in This Module

The **Finance** persona covers the **Finance Officer / Inventory Accountant** at the day-to-day reconciliation desk plus the **Finance Manager / Controller** at the period-close and period-lock boundary. Finance is the **valuation authority** on the inventory module — the role that owns the bridge between the physical-stock sub-ledger (`tb_inventory_transaction_cost_layer`) and the financial GL Inventory control account, and the role that signs off on the period-end run that locks the sub-ledger to a snapshot. Within the inventory module Finance's work spans four threads: (1) **approve cost-impact adjustments above the Inventory Controller threshold** per `INV_AUTH_005` — typically large recall write-offs, large damaged-stock write-offs, audit-flagged adjustments where the cost impact warrants Finance review; (2) **inventory-to-GL reconciliation** — periodic (typically weekly or monthly) reconciliation of the sub-ledger sum of cost-layer activity against the GL Inventory control account net change per `INV_XMOD_008`; (3) **period-end run** — orchestrate the close-of-period checklist after Inventory Controller sign-off, post the period's inventory-to-GL reconciliation journal entry, fire `INV_POST_009` (close) and `INV_POST_010` (open next) via the period-end job, and verify the resulting `tb_period_snapshot` rows balance to the GL; (4) **period-lock progression** at the Finance Manager level — advance `tb_period.status` from `closed` to `locked` per `INV_AUTH_006` / `INV_POST_011` after the audit window passes. Critically, Finance does **not** create or edit `tb_inventory_transaction` rows directly — corrections always go through a stock-in / stock-out / credit-note document that Finance approves; Finance is the approval authority, not the data-entry hand.

## 2. Entry Point and Primary Flow

**Entry points:** Four paths, each anchored to a different Finance activity.

- **Cost-impact approval queue** — `tb_stock_in` / `tb_stock_out` documents flagged for Finance approval after Inventory Controller approval per the threshold chain in `INV_AUTH_005`. Drives Section 2.1.
- **Inventory-to-GL reconciliation dashboard** — periodic (e.g. weekly) run comparing `Σ tb_inventory_transaction_cost_layer.total_cost + Σ diff_amount` for the period against the GL Inventory control account net change. Drives Section 2.2.
- **Period-end orchestration dashboard** — the period-close run after the Inventory Controller's variance sign-off; lists pre-close checklist items, the reconciliation status, and the close trigger. Drives Section 2.3.
- **Period-lock dashboard** (Finance Manager) — view of `closed` periods past the audit window awaiting `closed → locked` advance.

### 2.1 Cost-impact approval flow (Controller-escalated, 5 steps)

1. **Open the cost-impact approval queue.** Lists documents at the Finance-pending sub-state — `tb_stock_in` / `tb_stock_out` rows that the Inventory Controller has approved but whose cost impact exceeds the Controller threshold and routes to Finance per `INV_AUTH_005`. Sorted by submitted-at ascending, with cost impact and reason code visible.
2. **Open a specific document.** Reviews the Controller's evaluation: the originating evidence (count sheet, photo, vendor RMA), the reason code (`adjustment_type_id`), the line-level breakdown, and the cost-pick preview for outbound. Cross-checks against the financial implications — does the write-off hit the right GL account based on the reason code? Is the cost-per-unit defensible against the lot's recorded cost?
3. **Decide outcome.** **Approve** for genuinely large but defensible adjustments (large recall write-off with vendor agreement, mass expiry write-off documented by the QA inspection). **Reject** with comment for adjustments whose financial implications need additional support (request engagement-letter evidence on a large damage claim, request a second count on a large unexplained shortage). **Investigate** for adjustments whose pattern suggests systemic issues (write-off concentrated on a single product / vendor / lot) — routes to the Audit / Controller escalation chain outside the document workflow.
4. **Approve fires the post.** On Finance approval: `tb_stock_in.doc_status = completed` (or `tb_stock_out.doc_status = completed`); inventory transaction writes per `INV_POST_001` / `INV_POST_002`; GL journal entry posts to the appropriate accounts (Dr Department Expense / Cr Inventory for a write-off, etc.); the activity log records `{ action: 'approved', actor_id: finance, threshold: above_controller }`. The Inventory Controller sees the document at `completed`.
5. **Reject returns to Controller.** On Finance rejection: the document returns to the Controller's queue with Finance's comment; the Controller either resubmits with additional evidence, returns to the Store Keeper for re-evaluation, or voids the document.

### 2.2 Inventory-to-GL reconciliation flow (periodic, 6 steps)

1. **Open the reconciliation dashboard.** The dashboard renders, for the current `open` period (and any unsigned-off prior open periods), the sum of cost-layer activity grouped by `inventory`-type location: `Σ in_qty × cost_per_unit + Σ diff_amount` (inbound net), `Σ out_qty × cost_per_unit` (outbound), `Σ adjustment_in / adjustment_out / credit_note_*` (variance), and the resulting net inventory change. The right side renders the same figures for the GL Inventory control account.
2. **Compute variance.** For each cost-centre / location, variance = `sub_ledger_net_change − GL_net_change`. Variance below tolerance (typically a few cents per location due to rounding) is **acceptable**; variance above tolerance triggers investigation.
3. **Drill into variances.** For each above-tolerance variance, drill from the location-level summary into the cost-layer row list (the actual inventory transactions in the period) and into the GL journal row list. Common variance causes: a GRN that posted to inventory but whose AP-clearing journal hasn't fully posted, a credit-note that posted to GL but whose inventory cost-layer effect was missed, a stock-out posted with a wrong GL account assignment.
4. **Resolve variance.** **If the sub-ledger is right and the GL has the gap** — post a compensating GL journal to align (typical for late-arriving AP-clearing entries). **If the GL is right and the sub-ledger has the gap** — investigate the missed cost-layer write and post a corrective stock-in / stock-out (rare; usually indicates a data-migration gap or a bug). **If both have gaps** — investigate both, route to System Administrator if the gap is a configuration / integration issue.
5. **Document the reconciliation.** Each resolved variance is logged with the variance amount, the resolution path (compensating journal / corrective adjustment / investigation), and the actor. The reconciliation pass is signed off on the dashboard.
6. **Carry forward to period close.** A clean reconciliation pass for the period unblocks the period-end run; an unresolved variance holds the period at `open` until Finance resolves.

### 2.3 Period-end orchestration flow (close trigger, 7 steps)

1. **Wait for Inventory Controller sign-off.** The dashboard lists the Controller's pre-period-end variance sign-off (from `03-user-flow-inventory-controller.md` Section 2 / 3); period close cannot start without it. Cross-persona handoff per `03-user-flow.md` Section 4.
2. **Verify pre-close checklist clear.** All open `tb_stock_in` / `tb_stock_out` / `tb_count_stock` documents in the period are at terminal state (`completed` or `voided`). All GRN documents in the period are `committed` or `voided`. All SR documents in the period are `completed` or `voided`. Any open document in the closing period blocks the close.
3. **Run final inventory-to-GL reconciliation.** Section 2.2 flow run as the final pass for the period; reconciliation must pass (variance below tolerance per cost-centre / location).
4. **Post the period-end reconciliation journal.** Finance posts the **inventory-to-GL reconciliation entry** that absorbs any approved rounding variance and brings the GL Inventory control account exactly to the sub-ledger's closing balance. Typical entries: `Dr Inventory / Cr Inventory Rounding` or `Dr Inventory Variance / Cr Inventory` for small acceptable variances; large variances are not absorbed and block the close.
5. **Fire the period-close job.** Click **Close period**. The job (`INV_POST_009`) sweeps the period: writes `tb_period_snapshot` rows per `(location_id, product_id, lot_no, lot_index)` with opening / receipt / issue / adjustment / closing buckets per `INV_CALC_008`–`INV_CALC_010`; writes `close_period` cost-layer rows tying the closing balance to the period. Sets `tb_period.status = closed`. Chained: `INV_POST_010` (open next period) writes `open_period` cost-layer rows opening the next period at the closing balance.
6. **Verify the snapshot.** The dashboard renders the closing snapshot summary — per-location closing on-hand, closing valuation, period activity. Finance cross-checks against the GL closing balance (now equal to the sub-ledger) and against the period-end report set.
7. **Period closed.** `tb_period.status = closed`; backdated postings into this period are now rejected per `INV_VAL_008` (unless Finance Manager re-opens per `INV_AUTH_006`). The next period is `open` and accepting movements per the cross-persona handoff to Inventory Controller and Store Keeper.

### 2.4 Period-lock flow (Finance Manager only, 3 steps)

1. **Wait out the audit window.** After period close, the closed period sits at `closed` through the audit window (typically 30–60 days post-close) to allow external auditors to review and request adjustments. Re-open during this window is permitted per `INV_AUTH_006` with audit-grade justification.
2. **Verify audit sign-off received.** External auditor / internal-audit team has signed off on the closed period; no open audit-correction requests; reconciliation report stays clean.
3. **Lock the period.** Click **Lock period**. The job (`INV_POST_011`) advances `tb_period.status = closed → locked`. No further re-open by any role; corrections post into current open period as restatement.

## 3. Decision Branches

- **Cost-impact approve vs reject.** Approve when the cost is defensible and the GL classification (driven by `adjustment_type_id`) is correct. Reject for missing evidence on large adjustments, wrong GL classification, or anomalous cost-per-unit. **Investigate** when the adjustment is part of a suspicious pattern — concentrated on one product / vendor / lot — without rejecting the specific document.
- **Reconciliation variance: within tolerance vs investigate vs resolve.** Within tolerance (typically a few cents per location) — accept and document. Above tolerance — drill and resolve per Section 2.2 step 4. Persistent unresolved variance — escalate to System Administrator (integration / configuration issue) or to the Audit team (potential data-integrity issue).
- **Period close gate vs hold.** Close when (a) Inventory Controller has signed off, (b) all source documents in the period are terminal, (c) the final reconciliation passes. Hold when any gate is open — communicate the hold to the affected personas with the expected resolution date.
- **Period re-open after close (within audit window).** Re-open when (a) external audit identifies a required adjustment in the closed period and the adjustment cannot be made as a current-period restatement, (b) a material correction is discovered (e.g. a credit note that should have posted in the closed period). Re-open is audit-logged; the period must be re-closed before the next regular period close.
- **Period lock — no re-open path.** Lock only when (a) the audit window has passed cleanly with no open audit-correction requests, (b) external audit has signed off. After lock, no role can re-open; any correction posts into the current open period as restatement.

## 4. Exit Point / Handoffs

Finance's involvement on a given inventory thread ends at one of four boundaries:

- **Cost-impact adjustment approved and posted.** The escalated `tb_stock_in` / `tb_stock_out` document posts; the inventory transaction and GL journal are written; the Inventory Controller's queue refreshes. Finance's involvement on this document is done.
- **Reconciliation variance resolved.** The compensating journal or corrective adjustment posts; the reconciliation pass is clean for the period; Finance signs off. Handoff (implicit) to the **Audit / Config** persona who reviews the reconciliation activity in the audit trail.
- **Period closed.** `tb_period_snapshot` rows written; `tb_period.status = closed`; backdated postings rejected. Handoff to **Inventory Controller** and **Store Keeper** for the new period's variance management; handoff to **Finance Manager** for the close-to-lock progression.
- **Period locked.** `tb_period.status = locked`; permanently immutable. Handoff to **Auditor** for the long-term audit-trail review; no further inventory-side action on this period.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the canonical movement-and-period lifecycle, the cross-persona handoff table that anchors Inventory Controller → Finance (cost-impact, period-end sign-off) and Finance → Finance Manager → Auditor (close, lock) boundaries.
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — initiator of the adjustments whose cost impact may rise to Finance threshold.
- Sibling: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md) — upstream persona that approves below-Finance-threshold adjustments and signs off on variance before period close; routes large-cost adjustments to Finance.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Auditor who reviews Finance's reconciliation activity and the period-close audit trail; Sysadmin who configures the GL account map, the costing method per product, the reconciliation tolerance, and the period definition.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `tb_inventory_transaction_cost_layer` (the sub-ledger Finance reconciles to GL), `tb_period` / `tb_period_snapshot` (the close / lock state and the snapshot rows the period-end job writes), `enum_period_status` (`open` / `closed` / `locked`), `enum_inventory_doc_type` (`close` / `open` for rollforward).
- Sibling: [02-business-rules.md](./02-business-rules.md) — authorization rules `INV_AUTH_005` (Finance cost-impact approval), `INV_AUTH_006` (Finance Manager period lock / re-open), `INV_AUTH_007` (system context for `close` / `open` postings), plus posting rules `INV_POST_009` (close), `INV_POST_010` (open next), `INV_POST_011` (lock), and cross-module rules `INV_XMOD_008` (inventory-to-GL reconciliation).
- Related: [[costing]] — the cost-layer ledger Finance reconciles is what costing reads for COGS; Finance's reconciliation activity is the audit anchor for the costing module's outputs.
- Related: [[good-receive-note]] — Finance's reconciliation drills into GRN AP-clearing journal posts when variance investigation surfaces a GRN-side gap. The GRN module's `03-user-flow-finance.md` covers the three-way-match path that creates the AP-clearing entries.
- Related: [[inventory-adjustment]] — the corrective stock-in / stock-out path Finance takes when the reconciliation surfaces a sub-ledger gap that cannot be resolved by a GL journal alone.
- Related: credit note — Finance books credit notes against GRNs; the credit-note's inventory-side effect (`credit_note_amount` / `credit_note_quantity`) is part of the reconciliation surface for the period the credit-note posts in.
