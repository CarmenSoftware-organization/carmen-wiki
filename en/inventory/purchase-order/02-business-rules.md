---
title: Purchase Order — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for purchase-order.
published: true
date: 2026-07-29T05:45:00.000Z
tags: purchase-order, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Business Rules

> **At a Glance**
> **Rule families:** `PO_VAL_*` validation &nbsp;·&nbsp; `PO_AUTH_*` permission &nbsp;·&nbsp; `PO_CALC_*` calc &nbsp;·&nbsp; `PO_POST_*` posting &nbsp;·&nbsp; `PO_XMOD_*` cross-module
> **Rule count:** approximately 60 rules
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page captures the operational business rules that govern a Purchase Order (PO) document through its lifecycle: input validation at create / edit / submit time, monetary calculation (line and header), authorization gates by workflow stage role, posting effects on each transition of `enum_purchase_order_doc_status`, and cross-module rules with [purchase-request](/en/inventory/purchase-request), [good-receive-note](/en/inventory/good-receive-note), [vendor-pricelist](/en/inventory/vendor-pricelist), and [inventory](/en/inventory/inventory). A prior version of this page also described an amount-threshold approval gate and a three-way-match against a vendor invoice; the three-way-match claim was not found in current source (§ 5). **The amount-threshold claim was itself corrected in error by an earlier resync pass** — a follow-up pass confirmed the mechanism is real: the workflow assigned to a PO can carry `routing_rules` that route on `total_amount` (see § 4, `PO_AUTH_004`), just not the fixed, PO-specific "high-value threshold" field originally described. See § 4 for the corrected rule and the Discrepancy log for detail.

The rules below are synthesised from the legacy carmen/docs PO business analysis, the corresponding PR business-rule catalogue (Section 3 of `purchase-request-ba.md` and `PR-Module-Structure.md`, since PO inherits the same calculation, rounding, and approval philosophy), and the canonical Prisma data model documented in [purchase-order/01-data-model](/en/inventory/purchase-order/01-data-model). Where the legacy carmen/docs and Prisma disagree, Prisma is canonical — in particular for status values (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) and for the PR↔PO bridge linkage rather than a single FK on the PO line.

## 2. Validation Rules

Rule IDs follow `PO_VAL_NNN`. Header rules (001–006) run on every save and on submit; line rules (007–011) run per line on save and on submit; aggregate rules (012–016) run only at submit time.

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PO_VAL_001` | `tb_purchase_order.po_no` is non-empty and unique among non-soft-deleted rows (`@@unique([po_no, deleted_at])`). | Create, edit, submit | Reject with "PO reference number is required and must be unique." DB-level fallback via the unique index. |
| `PO_VAL_002` | `vendor_id` references an active, non-soft-deleted `tb_vendor` row. | Create, edit, submit | Reject with "Vendor is required and must be from the approved vendor list." |
| `PO_VAL_003` | `currency_id` references a non-soft-deleted `tb_currency` row; `exchange_rate > 0`. | Create, edit, submit | Reject with "Transaction currency and a positive exchange rate are required." |
| `PO_VAL_004` | `po_type` is one of `enum_purchase_order_type` (`manual`, `purchase_request`, `pricelist`); default `purchase_request`. | Create | Reject with "PO type must be `manual`, `purchase_request`, or `pricelist`." |
| `PO_VAL_005` | `credit_term_id` references a non-soft-deleted `tb_credit_term` row when the vendor requires it. | Submit | Reject with "Credit term is required for this vendor." |
| `PO_VAL_006` | `order_date` is not null and `delivery_date >= order_date`. | Edit, submit | Reject with "Delivery date must be on or after the order date." |
| `PO_VAL_007` | Each `tb_purchase_order_detail` row has a non-null `product_id` referencing an active, non-soft-deleted `tb_product`. | Save line, submit | Reject the line with "Product is required." |
| `PO_VAL_008` | `order_qty > 0` and `order_unit_id` is non-null. | Save line, submit | Reject the line with "Order quantity must be greater than zero and a unit of measure is required." |
| `PO_VAL_009` | `order_unit_conversion_factor > 0`; `base_qty = order_qty × order_unit_conversion_factor` rounded to 3 decimals. | Save line, submit | Reject the line with "Order UoM must have a positive conversion factor to base UoM." Recompute `base_qty` on save. |
| `PO_VAL_010` | `price >= 0` (zero allowed only when `is_foc = true`). | Save line, submit | Reject the line with "Unit price must be non-negative; price of 0 requires the FOC flag." |
| `PO_VAL_011` | `tax_rate >= 0` and `discount_rate >= 0`; when `is_tax_adjustment = true` or `is_discount_adjustment = true` the override amount must be persisted by the application. | Save line, submit | Reject the line with "Tax / discount rate must be non-negative; manual override requires an explicit amount." |
| `PO_VAL_012` | PO has at least one non-soft-deleted `tb_purchase_order_detail` row at submit time. | Submit | Reject with "PO must contain at least one line item." |
| `PO_VAL_013` | Every line on the PO shares the header `vendor_id` and `currency_id` context (single-vendor / single-currency invariant). | Submit | Reject with "All lines on a PO must share the header vendor and currency. Split into separate POs by vendor+currency." |
| `PO_VAL_014` | When `po_type = purchase_request`, every line carries at least one bridge row in `tb_purchase_order_detail_tb_purchase_request_detail` whose `pr_detail_qty > 0`. | Submit | Reject with "PR-sourced PO lines must be linked to an originating PR line via the bridge table." |
| `PO_VAL_015` | Status transitions follow the state machine in Section 5; out-of-order transitions are blocked. | On status change | Reject with "Invalid status transition from `<from>` to `<to>`." |
| `PO_VAL_016` | Amendments to vendor, currency, or any line on a PO whose `po_status` is not `draft` or `in_progress` are blocked. After `sent`, only `cancelled_qty` and per-line note may be updated. | Edit on non-draft PO | Reject with "PO can no longer be amended at status `<status>`. Void or close instead." |

## 3. Calculation Rules

All monetary values are stored as `Decimal(20, 5)` at the row level; tax and discount **rates** are stored as `Decimal(15, 5)`; the exchange rate is `Decimal(15, 5)` on the PO header. Display rounding is half-up (banker's rounding for ties on .5) to 2 decimals for currency amounts, 3 decimals for quantities, and 5 decimals for rates. Intermediate computations always re-read the rounded value of the prior step (this matches `PR_046`–`PR_055` from the PR BA, which PO inherits).

Rule IDs follow `PO_CALC_NNN`.

| Rule ID | Formula |
| ------- | ------- |
| `PO_CALC_001` (line subtotal) | `sub_total_price = Round(price × order_qty, 2)`. |
| `PO_CALC_002` (line discount) | `discount_amount = Round(Round(sub_total_price, 2) × discount_rate, 2)` unless `is_discount_adjustment = true`, in which case the persisted override wins. |
| `PO_CALC_003` (line net) | `net_amount = Round(Round(sub_total_price, 2) − Round(discount_amount, 2), 2)`. |
| `PO_CALC_004` (line tax) | `tax_amount = Round(Round(net_amount, 2) × tax_rate, 2)` unless `is_tax_adjustment = true` (override). |
| `PO_CALC_005` (line total) | `total_price = Round(Round(net_amount, 2) + Round(tax_amount, 2), 2)`. |
| `PO_CALC_006` (base conversion) | For each money column `X` in the transaction currency, the base column `base_X = Round(Round(X, 2) × exchange_rate (5 dp), 2)`. Concretely `base_price`, `base_sub_total_price`, `base_discount_amount`, `base_net_amount`, `base_tax_amount`, `base_total_price`. |
| `PO_CALC_007` (FOC handling) | When `is_foc = true`, the line contributes `0` to `sub_total_price`, `discount_amount`, `tax_amount`, and `total_price`, but `order_qty` and `base_qty` still roll up to `tb_purchase_order.total_qty`. |
| `PO_CALC_008` (header subtotal) | `tb_purchase_order.total_price = Round(Σ Round(net_amount, 2), 2)` across non-soft-deleted, active lines. |
| `PO_CALC_009` (header tax) | `tb_purchase_order.total_tax = Round(Σ Round(tax_amount, 2), 2)`. |
| `PO_CALC_010` (header grand total) | `tb_purchase_order.total_amount = Round(Round(total_price, 2) + Round(total_tax, 2), 2)`. Equivalent to `Σ Round(line.total_price, 2)`. |
| `PO_CALC_011` (header qty) | `tb_purchase_order.total_qty = Round(Σ Round(base_qty, 3), 3)` — quantity is summed in base UoM only because lines may use different order UoMs. |
| `PO_CALC_012` (rounding mode) | All rounding uses half-up (banker's) mode as per PR_047; regional number formatting is applied at presentation only, not at storage (PR_050). |

### 3.1 Worked example (฿ THB transaction currency)

Two lines, vendor in THB, exchange rate to base THB = 1.00000 (no FX).

- Line 1: `order_qty = 10.000`, `price = ฿125.50`, `discount_rate = 5%`, `tax_rate = 7%`, `is_foc = false`.
  - `sub_total_price = Round(125.50 × 10.000, 2) = ฿1,255.00`
  - `discount_amount = Round(1,255.00 × 0.05, 2) = ฿62.75`
  - `net_amount = Round(1,255.00 − 62.75, 2) = ฿1,192.25`
  - `tax_amount = Round(1,192.25 × 0.07, 2) = ฿83.46`
  - `total_price = Round(1,192.25 + 83.46, 2) = ฿1,275.71`
- Line 2: `order_qty = 4.000`, `price = ฿89.00`, `discount_rate = 0%`, `tax_rate = 7%`, `is_foc = false`.
  - `sub_total_price = ฿356.00`; `discount_amount = ฿0.00`; `net_amount = ฿356.00`
  - `tax_amount = Round(356.00 × 0.07, 2) = ฿24.92`
  - `total_price = ฿380.92`
- Header roll-up:
  - `total_price = Round(1,192.25 + 356.00, 2) = ฿1,548.25`
  - `total_tax = Round(83.46 + 24.92, 2) = ฿108.38`
  - `total_amount = Round(1,548.25 + 108.38, 2) = ฿1,656.63`

If a third FOC line is added (`order_qty = 1.000`, `price = 0`, `is_foc = true`), `total_qty` increases by 1.000 (in base UoM) but `total_amount` is unchanged.

## 4. Authorization Rules

Rule IDs follow `PO_AUTH_NNN`. Authorization is enforced by RBAC at the API layer; the rules below identify the policy, not the implementation. Role names mirror the carmen/docs RBAC table.

> ⚠️ **Correction (this pass, verified against current source):** the previous version of this table described a tenant-configurable "high-value threshold" that routed approval to the Procurement Manager, a Procurement-Manager-only "Void" action reachable from any non-terminal status, and a segregation-of-duties check (buyer ≠ GRN poster) enforced at GRN creation. The Void and segregation-of-duties claims were not found in current source: a repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `segregation` and `SoD` returned zero relevant hits, and `enum_stage_role` (`create`, `approve`, `purchase`, `issue`, `view_only`) has no deviation-aware member; `PO_AUTH_007` and `PO_AUTH_010` below are corrected accordingly.
>
> **The amount-threshold claim was wrongly dismissed in that same earlier pass** — an initial search for the literal word `threshold` found nothing because the live mechanism uses different vocabulary. `tb_workflow.data.routing_rules`, evaluated by `evaluateCondition`/`findNextStep` in `workflows.navagation.service.ts` on every submit and every approve action, can route a PO's next stage on a condition field (`total_amount` — Σ line `total_price`, mapped by `po-workflow.mapper.ts`; also `department` or `category`) against a configured value using an operator (`eq`, `gt`, `lt`, `gte`, `lte`, `between`), then `SKIP_STAGE` or jump to a named `NEXT_STAGE`. It is configured from the generic **Routing** tab of `/system-admin/workflow` (`wf-routing.tsx` + `wf-routing-constants.ts`) — shared by PR, PO, and SR workflows (the orchestrator's own docstring: "used across PR, PO, and SR"), not a PO-specific screen, and is a per-workflow configuration choice, not a fixed platform rule. `PO_AUTH_004` below is corrected accordingly.

| Rule ID | Subject | Right | Constraint |
| ------- | ------- | ----- | ---------- |
| `PO_AUTH_001` | Procurement Officer | Create PO (`po_status = draft`) | Any of `manual`, `purchase_request`, or `pricelist` `po_type`. |
| `PO_AUTH_002` | Procurement Officer | Edit PO | Only while `po_status ∈ {draft, in_progress}` and the user is the assigned buyer or holds the current `workflow_current_stage`. |
| `PO_AUTH_003` | Procurement Officer | Submit PO (`draft → in_progress`) | At least one line; passes Section 2 validation. |
| `PO_AUTH_004` | Whichever stage role is assigned to the workflow's final stage (commonly Procurement Manager, but purely a workflow-configuration choice) | Approve PO at the final workflow stage (`in_progress → sent`) | The `sent` transition itself is gated only by `isFinalApproval = (workflow_next_stage === '-')` in `purchase-order.logic.ts` — reaching the terminal stage, not an amount comparison. **Confirmed, corrected this pass:** which stage counts as "final" for a given PO can itself be amount-driven — the assigned workflow's `routing_rules` can evaluate `total_amount` (Σ line `total_price`, `po-workflow.mapper.ts`) on every submit/approve and skip or jump stages accordingly (`evaluateCondition`/`findNextStep` in `workflows.navagation.service.ts`), so a small-value PO can reach `sent` in fewer stages than a high-value one on the same workflow. This is a per-workflow configuration choice (the **Routing** tab of `/system-admin/workflow`) — a workflow with no routing rules approves every PO through the same fixed stage sequence regardless of amount. A `category`-based rule would silently never match — no mapper emits a document-level `category` field (source comment, `workflows.navagation.service.ts` ~L455-456). No pricelist-deviation-percentage condition field exists (only `total_amount`, `department`, `category` are supported), so deviation-based rerouting specifically remains unconfirmed (see `PO_XMOD_006`). A single-stage workflow lets the same user who holds that one stage both create and finally approve. |
| `PO_AUTH_005` | Procurement Manager | Delete PO | Only while `po_status = draft` (soft-delete via `deleted_at`). |
| `PO_AUTH_006` | Whichever user holds the final workflow stage | Transmit PO to vendor (`sent`) | Bundled into the same final-stage approve call — sets `tb_purchase_order.email` and `approval_date` on the same transition; there is no separate manual "Send to Vendor" step in the approval flow itself. |
| `PO_AUTH_007` | Any approver at the current stage | Reject PO (`in_progress → voided`, direct and terminal) | Only reachable from `in_progress`, via the `/reject` endpoint. There is no distinct "void" action and no path to `voided` from `draft`, `sent`, or `partial` — ending a PO from those statuses uses **Cancel** (`draft`/`in_progress`/`sent → closed`) or **Close** (`sent`/`partial`/`in_progress → closed`) instead, both of which write the remainder to `cancelled_qty`. |
| `PO_AUTH_008` | Inventory Manager (Receiver) | Create GRN against PO; close PO (`{sent, partial, in_progress} → closed` early termination) | GRN creation requires `po_status ∈ {sent, partial}` (`findOnePoForGrn`); the Close endpoint additionally allows `in_progress` (`closePO` in `purchase-order.service.ts`). |
| `PO_AUTH_009` | Read-only role(s) with PO view/export access | View, export reports | Read-only across all statuses. No distinct "Finance Officer" role or permission key was confirmed in current source. |
| `PO_AUTH_010` | — | — (unconfirmed) | **Unverified / likely not implemented.** No code path in the GRN or PO services checks `buyer_id` / `last_action_by_id` against the GRN-posting user; a repo-wide search for `segregation` found no matches. Treat any "Purchaser ≠ Receiver enforced at GRN creation" claim elsewhere in this module as design intent, not live behavior. |
| `PO_AUTH_011` | Workflow-derived authorization | Stage-gated approval | The set of users in `tb_purchase_order.user_action.execute` at the current `workflow_current_stage` is the only set permitted to advance the document; all other approval attempts are rejected. |

## 5. Posting Rules

Status values are the literal members of `enum_purchase_order_doc_status` documented in [purchase-order/01-data-model](/en/inventory/purchase-order/01-data-model) § 4: `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`. There is no separate GL "posting" for the PO document itself; PO posting is the act of mutating the status, recording the audit trail (`history`, `workflow_history`), and triggering downstream side effects. Inventory-side effects happen at GRN posting (owned by the GRN/inventory modules); a prior version of this sentence also asserted GL posting "at three-way-match success (AP invoice)" — that feature is not implemented (see `PO_POST_008`/`PO_POST_009` below).

Rule IDs follow `PO_POST_NNN`.

| Rule ID | Transition / Event | Effects |
| ------- | ------------------ | ------- |
| `PO_POST_001` | Create (→ `draft`) | Insert `tb_purchase_order` with `po_status = draft`, `doc_version = 0`, `total_qty = total_price = total_tax = total_amount = 0`. Append to `history`: `{ po_status: 'draft', action: 'created', by, at }`. |
| `PO_POST_002` | Submit (`draft → in_progress`) | Recompute all roll-ups (`PO_CALC_008`–`PO_CALC_011`). Set `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user`. Initialise `workflow_history`, `workflow_current_stage = <first stage>`, `stages_status = [...]`, and populate `user_action.execute` from the workflow stage definition. Append `history` entry. Soft commitment on budget/inventory is created downstream by the workflow. |
| `PO_POST_003` | Approve (within `in_progress`) | Append `workflow_history` entry; advance `workflow_current_stage`. Update `user_action.execute` for the next stage. `last_action = approved`. No status change yet — the PO stays `in_progress` until the final approval stage. |
| `PO_POST_004` | Final approval (`in_progress → sent`) | Set `po_status = sent`, `approval_date = now()`, `last_action = approved`. Append `history`. Send PO to vendor via the application's email/transmit layer **on the same transition** — there is no separate manual "Send to Vendor" action in the live UI (the `APPROVED → SENT` step is auto). From this point on, the PO is a vendor-facing commitment. Confirmed in `purchase-order.logic.ts` `approve()`: `po_status: isFinalApproval ? sent : in_progress`. |
| `PO_POST_005` | Send-back / Review (`in_progress` stays `in_progress`) | **Corrected this pass** — the `/review` endpoint does **not** change `po_status`. It only resets `workflow_current_stage` / `workflow_previous_stage` to an earlier stage (typically the creator/"purchase" stage — `buildReviewWorkflow` in `workflow-orchestrator.service.ts` navigates back via `workflows.navigate-back-to-stage` and returns no `po_status` field), sets `last_action = reviewed`, and appends `workflow_history`. When the destination is the creator-only stage, only the original buyer/creator can act next (functionally similar to editing a draft, but the persisted `po_status` remains `in_progress`, not `draft`). Optional reason text is appended to `tb_purchase_order_comment`. |
| `PO_POST_006` | GRN partial receipt (`sent → partial` or `partial → partial`) | For each affected PO line, the GRN posting increments `tb_purchase_order_detail.received_qty` by the GRN quantity (in order UoM). If `received_qty < order_qty − cancelled_qty` for at least one line, set `po_status = partial`. Bridge rows `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` are updated proportionally to retain PR-side allocation visibility. |
| `PO_POST_007` | GRN full receipt (`sent → completed` or `partial → completed`) | When every active line satisfies `received_qty = order_qty − cancelled_qty`, set `po_status = completed`. Append `history`. PO is closed normally — no further GRNs accepted. |
| `PO_POST_008` | ~~Three-way match success~~ — **not implemented** | **Unverified / likely fabricated.** A repo-wide search of the frontend and backend for `three-way`, `threeWay`, `vendor_invoice`, `VendorInvoice`, and `tb_invoice` returned zero hits. No vendor-invoice-capture screen, AP-posting endpoint, or match algorithm exists in current source. Do not treat this rule as live behavior; see the Discrepancy log. |
| `PO_POST_009` | ~~Three-way match failure~~ — **not implemented** | Same finding as `PO_POST_008` — no invoice/AP module exists to hold a match in dispute. |
| `PO_POST_010` | Cancel (`{draft, in_progress, sent} → closed`) | `cancel()` in `purchase-order.service.ts`: sets `po_status = closed`; for each line, writes `cancelled_qty = order_qty − received_qty`. No `is_active` field is touched. This is the withdraw-the-commitment action, distinct from Close below only in its allowed source-status set. |
| `PO_POST_010b` | Reject (`in_progress → voided`, direct, terminal) | `reject()` in `purchase-order.service.ts`: sets `po_status = voided` directly (does **not** set `is_active = false` — that claim in an earlier version of this rule was not confirmed in code). Only reachable from `in_progress`; there is no path to `voided` from `draft`, `sent`, or `partial`. `voided` is terminal. |
| `PO_POST_011` | Close (`{sent, partial, in_progress} → closed` early-termination) | `closePO()` in `purchase-order.service.ts`: sets `po_status = closed`; for each line with `cancelledQty = orderQty − receivedQty > 0`, writes it to `cancelled_qty` so `received_qty + cancelled_qty = order_qty`. Used when the vendor cannot supply the outstanding quantity. Distinct from `completed` (full receipt). `closed` is terminal. |
| `PO_POST_012` | Soft delete | `deleted_at = now()`, `deleted_by_id = user`. Only allowed at `draft` per `PO_AUTH_005`. Row remains in the database; all unique indexes include `deleted_at` so a new PO can reuse the same `po_no`. |

State diagram (Prisma-canonical, corrected this pass):

```
[*] → draft → in_progress → sent → partial → completed
       ↓ ↑        ↓  ↑        ↓       ↓         ↑
   (soft-  (send-back:      (cancel)  ↓     (full receipt)
    delete) stage resets,     ↓       ↓
             stays              ↓       └→ closed (early term./close/cancel)
             in_progress)        ↓
                          (reject) → voided  (in_progress only, direct & terminal)
```

`completed`, `closed`, and `voided` are terminal. `draft` accepts soft-delete. `closed` is reachable from `draft`/`in_progress`/`sent` (cancel) or `sent`/`partial`/`in_progress` (close) — there is no separate "void" action outside the in-workflow `reject`.

### 5.1 Status Lifecycle — Correction Notes

> ⚠️ **This section previously presented a "Live UI vs BRD" mapping sourced from a historical BA test-case document (`Test_case/Purchase_Order/Purchaser/INDEX.md`, capture date 2026-04-26) that asserted a distinct `APPROVED` status and a `REJECTED` status returning the PO to the Purchaser. Neither is a real Prisma enum member, and re-verifying against current source this pass turned up a different, simpler reality — corrected below.**

The Prisma enum `enum_purchase_order_doc_status` (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) is exhaustive — there is no `approved` or `rejected` member. What was previously labelled "`APPROVED`" is not a persisted status: final-stage approval and transmission happen in the same `approve()` call and land directly on `sent` (`PO_POST_004`). What was previously labelled "`REJECTED`" is the direct, terminal `in_progress → voided` transition (`PO_POST_010b`) — there is no intermediate state and no return to `draft`. A UI badge reading "Rejected" (seen in `403-po-approver-journey.spec.ts` `TC-PO-070311`) is consistent with a `voided` PO whose `last_action = rejected`, not with a distinct persisted status.

Separately, **"send-back"** (the `/review` action) does not move `po_status` at all — see `PO_POST_005` above. A prior version of this page conflated "send-back" and "reject" as the same `in_progress → draft` transition; they are two different endpoints with two different effects, and neither actually reaches `draft` from `in_progress`.

No vendor-acknowledgement status (`ACKNOWLEDGED`) exists in current source; where a vendor's acceptance is recorded at all, it would be a `tb_purchase_order_comment` entry, not a status value — this specific claim was not directly verified this pass and should be treated as unconfirmed rather than corrected.

## 6. Cross-Module Rules

Rule IDs follow `PO_XMOD_NNN`.

| Rule ID | Related module | Rule |
| ------- | -------------- | ---- |
| `PO_XMOD_001` | [purchase-request](/en/inventory/purchase-request) | When `po_type = purchase_request`, the PO must be created via the PR-to-PO conversion flow (a 2-step dialog, `po-from-pr-dialog.tsx`: select whole PRs → review the grouped PO(s)), which groups selected approved PR lines by `(vendor_id, delivery_date, currency_id)` — confirmed via `buildPoGroupKey` in `purchase-order.service.ts` — and produces one PO per group. Each resulting PO line carries one or more bridge rows in `tb_purchase_order_detail_tb_purchase_request_detail` linking it back to the originating PR line(s) (`PO_VAL_014`). Both endpoints (`POST .../purchase-orders/group-pr`, `POST .../purchase-orders/confirm-pr`) list `Permissions: None` in Bruno; the frontend dialog chain has no `hasPermission` check. |
| `PO_XMOD_002` | [purchase-request](/en/inventory/purchase-request) | The bridge supports consolidation (many PR lines → one PO line) and partial conversion (one PR line → many PO lines). The PR line is considered fully converted only when `Σ bridge.pr_detail_qty` for that `pr_detail_id` equals the PR line's approved quantity. |
| `PO_XMOD_003` | [good-receive-note](/en/inventory/good-receive-note) | A GRN may only be created against a PO whose `po_status ∈ {sent, partial}` (`PO_AUTH_008`). The GRN detail back-references `tb_purchase_order_detail.id`; the pending quantity available for receipt is `order_qty − received_qty − cancelled_qty` per `PO_POST_006`. |
| `PO_XMOD_004` | [good-receive-note](/en/inventory/good-receive-note) | Receiving a quantity that would exceed the pending qty is rejected unless tenant configuration permits over-receipt within a tolerance; otherwise the GRN line is capped at the pending qty. |
| `PO_XMOD_005` | [vendor-pricelist](/en/inventory/vendor-pricelist) | At PR-to-PO conversion, the system snapshots `price` from the active vendor pricelist for the `(vendor, product, currency)` tuple. If no active pricelist row exists, the PR's last-known price is used and a `system` comment is appended flagging the missing pricelist coverage. |
| `PO_XMOD_006` | [vendor-pricelist](/en/inventory/vendor-pricelist) | **Partially unverified, partially corrected this pass.** Whether a buyer's price override against the pricelist snapshot is logged as a distinct "deviation entry" was not directly confirmed. The second half of the original claim — that deviations above a *pricelist-tolerance band specifically* force-route the PO to a "high-value approval stage" — remains **not implemented as a deviation-aware mechanism**: the routing condition fields supported by `tb_workflow.data.routing_rules` are only `total_amount`, `department`, and `category` (`wf-routing-constants.ts`) — there is no pricelist-deviation-percentage field to route on. **However, amount-threshold routing itself is real** (see `PO_AUTH_004`) — a workflow can route on the PO's plain `total_amount`, which is a coarser trigger than a deviation percentage (it fires on the PO's size, not on how far its price strayed from the pricelist) but does mean a large-value PO can be escalated to an additional stage regardless of whether any line deviates from its pricelist price. Approval stage count and assignment otherwise come only from the workflow definition. |
| `PO_XMOD_007` | ~~AP / Three-way match~~ — **not implemented** | **Unverified / likely fabricated**, same finding as `PO_POST_008`/`PO_POST_009`: no invoice, AP-posting, or three-way-match code exists in `carmen-turborepo-backend-v2` or `carmen-inventory-frontend-react`. GRN posting's accrual/GL effects, if any, live entirely in the GRN/inventory/costing modules — not verified as part of this PO-module pass. |
| `PO_XMOD_008` | [inventory](/en/inventory/inventory) | Inventory on-hand is **not** incremented by PO posting — it is incremented only when the GRN posts (which is in scope for the GRN module). The PO contributes the "on-order" pipeline quantity that inventory planning reads via `order_qty − received_qty − cancelled_qty` on active PO lines. |
| `PO_XMOD_009` | [inventory](/en/inventory/inventory) | The PO line's `base_qty` (computed in base UoM via `PO_CALC_011`) is the quantity that inventory reservations and projected-on-hand calculations read; the order UoM is for vendor-facing display only. |

## 7. References

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — PO consolidated BA (Section 1.3 Business Rules, Section 1.4 System Calculation Rules, Section 6.1 State Diagram, Section 2.5 RBAC). State labels are reconciled to the Prisma enum values per [purchase-order/01-data-model](/en/inventory/purchase-order/01-data-model) § 5.
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — validation, error-type, and workflow-state structures inherited by PO.
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — Section 3 (Business Rules) and Section 3.6 (System Calculation Rules); PO's calculation rules (`PO_CALC_*`) are the direct PR-rule counterparts (`PR_036`–`PR_055`).
- Sibling: `en/purchase-order/01-data-model.md` — canonical Prisma model, enum values, and the bridge-table linkage that Section 5 and Section 6 rely on.
- Backend rule implementation: `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-order/` — `purchase-order.service.ts` and `purchase-order.logic.ts` implement the status guards, workflow transitions, and GRN-facing queries verified in this pass. No three-way-match orchestration exists there (see § 5 / § 6).
