---
title: Inventory Adjustment — User Flow — Inventory Controller
description: Inventory Controller's flow within the inventory-adjustment module — review, variance monitoring, approval, posting, count-rollup commit.
published: true
date: 2026-05-15T13:00:00.000Z
tags: inventory-adjustment, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — User Flow — Inventory Controller

## 1. Role in This Module

The **Inventory Controller** persona (folded with Inventory Manager in the carmen/docs source, and absorbing the Department Manager review responsibility) is the **governance authority above the auto-approve threshold** and the **balance-accuracy owner** for the property. Within the inventory-adjustment module the Controller holds:

- **Approve / reject authority** on `in_progress` `tb_stock_in` / `tb_stock_out` documents within the Controller threshold band (`฿500–฿10,000` typical, between Store Keeper auto-approve and Finance) per `ADJ_AUTH_004`. Approval fires `in_progress → completed` which posts the inventory transaction and GL entry per `ADJ_POST_002`.
- **Approval authority on new-lot stock-in** regardless of cost — Store Keeper-submitted new-lot adjustments always route to Controller per `ADJ_AUTH_003`, where the Controller validates lot identity and cost-per-unit defensibility.
- **Variance-monitoring scope** — reviews adjustment patterns by reason, location, department, time of day, individual user; investigates oversize variances per `ADJ_CALC_008` variance-% calc and drives corrective process changes (training, recount, reason-code reconfiguration request to Sysadmin).
- **Count-rollup commit authority** — commits variance lines from [[physical-count]] / [[spot-check]] runs which triggers the `ADJ_POST_006` auto-rollup `tb_stock_in` / `tb_stock_out` creation; cross-references [[inventory]] `INV_XMOD_003` / `INV_XMOD_004`.
- **Direct create authority** — may raise `tb_stock_in` / `tb_stock_out` directly (e.g. when an investigation reveals a discrepancy that the Store Keeper hasn't yet reported, or when SoD per `ADJ_AUTH_010` blocks the Store Keeper from raising a write-off for a lot they received).
- **Void authority** — initiates compensating reversal for posted documents per `ADJ_POST_004`, moves the original to `voided` after the compensating post.
- **Cancel authority** on `in_progress` documents per `ADJ_AUTH_007` — when a recount or investigation concludes the adjustment isn't warranted.
- **Department Manager review responsibility** (folded into this persona group) — read-only oversight of adjustments hitting their cost-centre (resolved via the document's `dimension` JSON), notification subscription, comment / flag capability for escalation to Finance.

The Controller does **not** have above-Controller-threshold approval authority (Finance per `ADJ_AUTH_005`), does not configure reason codes / thresholds (Sysadmin per `ADJ_AUTH_008`), and does not run the period-end close (Finance Manager per [[inventory]] `INV_AUTH_006`).

The Controller's adjustment-module ownership begins when a document submits at or above threshold (or when a count commits) and ends at one of the boundaries enumerated in Section 4.

## 2. Entry Point and Primary Flow

**Entry points:** Five doors into a Controller-driven action on adjustments.

- **Inventory Adjustment module → Pending Approvals queue** — lists all `in_progress` documents within the Controller's scope (filterable by location, reason, requester, age). Documents enter this queue from Store Keeper submit at or above auto-approve threshold or for new-lot stock-in. This is the primary daily entry.
- **Inventory Adjustment module → Variance Review** — periodic dashboard showing adjustment patterns: top reasons by cost impact, locations with anomalous variance, users with outlier behaviour. Driven by `ADJ_CALC_010` period-impact aggregation.
- **Physical Count / Spot Check → Variance Commit** — at count completion, the Controller commits the variance lines which triggers `ADJ_POST_006` auto-rollup. This is the count-driven entry point.
- **Direct create — New Stock-In / Stock-Out** — same form as the Store Keeper's primary flow, used when the Controller raises an adjustment directly. Document auto-routes for Finance approval if cost exceeds the Controller threshold.
- **Notifications / Department Manager view** — read-only entry from email / dashboard notification when a cost-centre under their oversight is hit by a posted or pending adjustment.

**Primary flow (review and approve an above-threshold stock-out, 9 steps — illustrative of the approval pattern):**

1. **Open the Pending Approvals queue.** Inventory Adjustment module → Pending Approvals. The queue shows the Store-Keeper-submitted `tb_stock_out` at `doc_status = in_progress` with reason `BREAKAGE`, total cost `฿2,500` (above auto-approve threshold, below Controller threshold), creator, age (time in queue).
2. **Open the document detail.** Click into the row. The detail view shows the header (location, reason, description, department from `dimension`), the lines (product, qty, lot-pick-preview / FIFO preview, cost preview), the comments / attachments (damage photo, supervisor sign-off), and the `workflow_history` (Store Keeper submitted at `<timestamp>`).
3. **Verify the reason code matches the evidence.** Cross-check the reason (`BREAKAGE`) against the attached photo and the line description (e.g. "5 bottles dropped during transfer from pallet"). Reasons that don't match the evidence (e.g. claiming `EXPIRY_WRITE_OFF` on a non-expired lot) are flagged for follow-up.
4. **Check variance context.** Click "Show context" — the screen renders prior adjustments at this location for the same product / reason in the last 30 days, and any open counts that might explain the discrepancy. Aim: detect repeat-offender patterns (e.g. "this is the fourth `BREAKAGE` for P-1 at LOC-A this month — process problem, not a one-off").
5. **Validate cost-impact preview.** The screen renders the FIFO cost pick (`฿2,500` from `LOT-1` at `฿10.00` × 250 units, say) — verify the cost is reasonable given recent vendor prices. WA products show the moving average; outlier averages flag for investigation.
6. **Check on-hand availability.** The system re-runs `INV_VAL_005` (no negative balance) live at the moment of approval. If on-hand at the picked lot has changed since submit (e.g. another posting consumed from the same lot), the approval re-validates; rejection here returns the document to `draft` with a "stock no longer available, please re-pick lot" message to the Store Keeper.
7. **Approve, reject, request more evidence, or cancel.**
    - **Approve:** Click **Approve**. Document transitions `in_progress → completed` per `ADJ_POST_002`. Inventory transaction posts; cost-layer rows write; GL journal generates. `workflow_history` records `{stage: 'completed', action: 'approved', by: <controller_id>}`. Activity log shows the Controller as the approver.
    - **Reject:** Click **Reject**, enter rejection reason. Document returns to `draft`; Store Keeper sees the rejection in their queue with the reason in `workflow_history`; can edit and re-submit or cancel.
    - **Request evidence:** Add a comment with an evidence request. Document stays `in_progress`; Store Keeper attaches the requested evidence via comment and re-submits to re-trigger approval review.
    - **Cancel:** If a recount or investigation concludes the adjustment isn't warranted, the Controller cancels the `in_progress` document per `ADJ_AUTH_007`. `doc_status = cancelled` with reason text; terminal; no inventory effect.
8. **Post fires (on Approve).** Same fan-out as the Store Keeper's auto-approve flow per [[inventory]] `INV_POST_002`: `tb_inventory_transaction`, `tb_inventory_transaction_detail` (`qty < 0` for stock-out), one or more `tb_inventory_transaction_cost_layer` rows (FIFO multi-row or WA single per `ADJ_CALC_006` / `ADJ_CALC_007`), GL journal (`Dr Breakage Expense ฿2,500 / Cr Inventory ฿2,500`). The detail's `inventory_transaction_id` is stamped.
9. **Handoff to Finance for review** (period-end only). At period close, Finance reviews the period's adjustment-activity aggregate per the Finance flow. For day-to-day below-Finance-threshold adjustments, the Controller's approval is terminal — no further persona handoff.

The **count-variance commit** flow follows a slightly different shape:

1. Open the completed [[physical-count]] / [[spot-check]] document at `tb_count_stock.status = completed`. Variance lines are staged: per `(location, product, lot)`, the difference between physical and system qty.
2. Review each variance line — confirm the variance is real (not a counting error), classify (overage vs shortage), inspect supporting count-sheet attachments and counter signatures.
3. Click **Commit Variances**. The system per `ADJ_POST_006`:
    - Creates one `tb_stock_in` with reason `COUNT_OVERAGE` for all overage lines.
    - Creates one `tb_stock_out` with reason `COUNT_SHORTAGE` for all shortage lines.
    - Auto-advances both to `completed` under the Controller's authority (skipping the explicit approval queue).
    - Posts both per `ADJ_POST_002`.
    - Transitions `tb_count_stock.status = completed_posted`.
4. Activity log records the count as the source (`info.countId = <count_uuid>` on each rollup document).

The **direct-create** flow follows the Store Keeper's primary flow (Section 2 of [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md)) with the Controller as `created_by_id`. Above-Controller-threshold direct-create routes to Finance per `ADJ_AUTH_005`.

## 3. Decision Branches

- **Approve vs reject vs request evidence.** Approve when the reason / evidence / cost / context all support the adjustment. Reject when the reason is wrong, the evidence is missing or inconsistent, or the recount resolves the discrepancy. Request evidence when the submitter's case is plausible but the supporting attachments are missing or ambiguous (e.g. damage photo unclear, vendor RMA reference missing).
- **Variance threshold for investigation.** Adjustments above `ADJ_CALC_008` variance threshold (e.g. > 5% of on-hand at a product / location) trigger a deeper investigation: cross-check with [[physical-count]] last-count results, check the Store Keeper's recent variance history, walk the floor. Investigation may conclude with a comment-only "approved with note" or with a rejection and recount request.
- **New-lot stock-in approval.** When approving a Store-Keeper-raised new-lot stock-in, the Controller specifically validates: (a) the lot identity is well-formed and unique per `ADJ_VAL_009`; (b) the cost-per-unit is defensible (typically read from [[vendor-pricelist]] last-price or set to zero with explanatory note); (c) the new lot creation is consistent with the reason (e.g. `VENDOR_FREE_REPLACEMENT` justifies a zero-cost new lot; bare `FOUND_STOCK` of an unknown-cost lot raises eyebrows). The default cost-per-unit for true-found-stock with no prior reference is typically zero with a `DATA_FIX` reason — to avoid inflating inventory valuation on guesswork.
- **Above-Controller-threshold route to Finance.** Documents at or above the Controller threshold (typically `฿10,000` cost impact — large recall write-offs, large damage write-offs, large theft write-offs) cannot be approved by the Controller alone. The Controller reviews and either rejects, or **forwards to Finance** by re-submitting with a Finance approval annotation. Finance picks up from the Finance flow.
- **Count-rollup commit vs individual line review.** Standard count-variance commits trigger the auto-rollup per `ADJ_POST_006`. For counts with oversize aggregate variance (e.g. > 10% net cost impact), the Controller may instead choose to **reject the count** and request a recount before committing — preventing the auto-rollup from posting an unjustifiably large adjustment.
- **Department-Manager view escalation.** When the Controller (acting as Department Manager surrogate, or in liaison with one) sees a pattern of adjustments hitting a single cost-centre disproportionately, they may flag for Finance investigation and / or request a Sysadmin re-configuration of reason codes / thresholds for that cost-centre.

## 4. Exit Point / Handoffs

The Controller's involvement on a given adjustment ends at one of five boundaries:

- **Approval → post complete.** Below-Finance-threshold document approved by Controller; `doc_status = completed`; inventory transaction posted. Controller's work on this document ends; no further persona handoff. Activity log records the Controller as approver.
- **Rejection → back to Store Keeper.** Document `doc_status = draft` with rejection reason in `workflow_history`. Store Keeper re-engages.
- **Cancel → terminal inactive.** Document `doc_status = cancelled` with reason. No inventory effect. Terminal from the Controller's side.
- **Forward to Finance.** Above-Controller-threshold document routes to **Finance** ([03-user-flow-finance.md](./03-user-flow-finance.md)) for final approval. Document stays `in_progress`; Finance picks up the review.
- **Count commit → auto-rollup post.** Variance commit on a count run triggers `ADJ_POST_006` auto-rollup; rollup documents auto-advance to `completed`; count document at `completed_posted`. Controller's work on the count's adjustment side ends.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — canonical document lifecycle and cross-persona handoff table.
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — upstream persona whose submissions enter the Controller's approval queue.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — downstream persona for above-Controller-threshold approvals and period-end cost-impact review.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator who configures `tb_adjustment_type`, thresholds, and integration; Auditor who reads the Controller's approval history and SoD compliance.
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_stock_in` / `tb_stock_out` workflow / `last_action` columns the Controller reads at approval; `tb_adjustment_type` reason and `info.glAccount` the Controller validates against.
- Sibling: [02-business-rules.md](./02-business-rules.md) — `ADJ_AUTH_003` (new-lot Controller gate), `ADJ_AUTH_004` (Controller approval), `ADJ_AUTH_007` (cancel / void), `ADJ_POST_002` (post fan-out fired by Controller approve), `ADJ_POST_004` (void via compensating reversal), `ADJ_POST_006` (count-rollup auto-post), `ADJ_CALC_008` (variance %), `ADJ_CALC_010` (period impact); cross-module `ADJ_XMOD_002` / `ADJ_XMOD_003` (count rollup).
- Related: [[inventory]] — every Controller approval posts to inventory; `INV_AUTH_003` (Controller as second signature in inventory hierarchy), `INV_POST_001` / `INV_POST_002` (post effects), `INV_XMOD_003` / `INV_XMOD_004` (count-variance posting path).
- Related: [[physical-count]] — Controller commits count variances which auto-creates adjustment rollups.
- Related: [[spot-check]] — partial count; same auto-rollup pattern.
- Related: [[costing]] — Controller validates cost-per-unit defensibility on new-lot stock-in and on outlier FIFO / WA picks on stock-out.
- Related: [[good-receive-note]] — Controller may inspect the originating GRN when reviewing a large recall write-off or vendor-replacement adjustment.
- Related: [[vendor-pricelist]] — Controller cross-checks cost-per-unit on new-lot stock-in against the vendor pricelist last-price.
