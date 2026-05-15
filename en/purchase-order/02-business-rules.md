---
title: Purchase Order — Business Rules
description: Validation, calculation, authorization, posting, three-way-match, and cross-module rules for purchase-order.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Business Rules

## 1. Overview

This page captures the operational business rules that govern a Purchase Order (PO) document through its lifecycle: input validation at create / edit / submit time, monetary calculation (line and header), authorization gates by role and amount threshold, posting effects on each transition of `enum_purchase_order_doc_status`, three-way-match against the GRN and the vendor invoice, and cross-module rules with [[purchase-request]], [[good-receive-note]], [[vendor-pricelist]], and [[inventory]].

The rules below are synthesised from the legacy carmen/docs PO business analysis, the corresponding PR business-rule catalogue (Section 3 of `purchase-request-ba.md` and `PR-Module-Structure.md`, since PO inherits the same calculation, rounding, and approval philosophy), and the canonical Prisma data model documented in [[purchase-order/01-data-model]]. Where the legacy carmen/docs and Prisma disagree, Prisma is canonical — in particular for status values (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) and for the PR↔PO bridge linkage rather than a single FK on the PO line.

## 2. Validation Rules

Rule IDs follow `PO_VAL_NNN`. Header rules (001–006) run on every save and on submit; line rules (007–011) run per line on save and on submit; aggregate rules (012–016) run only at submit time.

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PO_VAL_001` | `tb_purchase_order.po_no` is non-empty and unique among non-soft-deleted rows (`@@unique([po_no, deleted_at])`). | Create, edit, submit | Reject with "PO reference number is required and must be unique." DB-level fallback via the unique index. |
| `PO_VAL_002` | `vendor_id` references an active, non-soft-deleted `tb_vendor` row. | Create, edit, submit | Reject with "Vendor is required and must be from the approved vendor list." |
| `PO_VAL_003` | `currency_id` references a non-soft-deleted `tb_currency` row; `exchange_rate > 0`. | Create, edit, submit | Reject with "Transaction currency and a positive exchange rate are required." |
| `PO_VAL_004` | `po_type` is one of `enum_purchase_order_type` (`manual`, `purchase_request`); default `purchase_request`. | Create | Reject with "PO type must be `manual` or `purchase_request`." |
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

Rule IDs follow `PO_AUTH_NNN`. Authorization is enforced by RBAC at the API layer; the rules below identify the policy, not the implementation. Role names mirror the carmen/docs RBAC table; "high-value" threshold is tenant-configurable and defaults to the procurement-manager escalation level in the workflow definition referenced by `tb_purchase_order.workflow_id`.

| Rule ID | Subject | Right | Constraint |
| ------- | ------- | ----- | ---------- |
| `PO_AUTH_001` | Procurement Officer | Create PO (`po_status = draft`) | Both `manual` and `purchase_request` `po_type`. |
| `PO_AUTH_002` | Procurement Officer | Edit PO | Only while `po_status ∈ {draft, in_progress}` and the user is the assigned buyer or holds the current `workflow_current_stage`. |
| `PO_AUTH_003` | Procurement Officer | Submit PO (`draft → in_progress`) | At least one line; passes Section 2 validation. |
| `PO_AUTH_004` | Procurement Manager | Approve PO at high-value stage (`in_progress → sent` for amounts above threshold) | `tb_purchase_order.total_amount` exceeds the tenant high-value threshold defined in the workflow. Below the threshold, Procurement Officer can self-approve to `sent` if the workflow allows. |
| `PO_AUTH_005` | Procurement Manager | Delete PO | Only while `po_status = draft` (soft-delete via `deleted_at`). |
| `PO_AUTH_006` | Procurement Officer or Procurement Manager | Transmit PO to vendor (`sent`) | After approval; sets `tb_purchase_order.email` and `approval_date`. |
| `PO_AUTH_007` | Procurement Manager | Void PO (`* → voided`) | Allowed from any non-terminal status (`draft`, `in_progress`, `sent`, `partial`). Once at `voided`, no further transitions allowed. |
| `PO_AUTH_008` | Inventory Manager (Receiver) | Create GRN against PO; close PO (`partial → closed` early termination) | Allowed only when `po_status ∈ {sent, partial}`. |
| `PO_AUTH_009` | Finance Officer | View, export reports | Read-only across all statuses. |
| `PO_AUTH_010` | Segregation of duties | Purchaser ≠ Receiver | The user who created or transmitted a PO (`tb_purchase_order.buyer_id` or `last_action_by_id` on a `sent` transition) MUST NOT be the same user who posts the GRN against that PO. Enforced at GRN creation time. |
| `PO_AUTH_011` | Workflow-derived authorization | Stage-gated approval | The set of users in `tb_purchase_order.user_action.execute` at the current `workflow_current_stage` is the only set permitted to advance the document; all other approval attempts are rejected. |

## 5. Posting Rules

Status values are the literal members of `enum_purchase_order_doc_status` documented in [[purchase-order/01-data-model]] § 4: `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`. There is no separate GL "posting" for the PO document itself; PO posting is the act of mutating the status, recording the audit trail (`history`, `workflow_history`), and triggering downstream side effects. Real GL posting happens at GRN (inventory accrual) and at three-way-match success (AP invoice).

Rule IDs follow `PO_POST_NNN`.

| Rule ID | Transition / Event | Effects |
| ------- | ------------------ | ------- |
| `PO_POST_001` | Create (→ `draft`) | Insert `tb_purchase_order` with `po_status = draft`, `doc_version = 0`, `total_qty = total_price = total_tax = total_amount = 0`. Append to `history`: `{ po_status: 'draft', action: 'created', by, at }`. |
| `PO_POST_002` | Submit (`draft → in_progress`) | Recompute all roll-ups (`PO_CALC_008`–`PO_CALC_011`). Set `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user`. Initialise `workflow_history`, `workflow_current_stage = <first stage>`, `stages_status = [...]`, and populate `user_action.execute` from the workflow stage definition. Append `history` entry. Soft commitment on budget/inventory is created downstream by the workflow. |
| `PO_POST_003` | Approve (within `in_progress`) | Append `workflow_history` entry; advance `workflow_current_stage`. Update `user_action.execute` for the next stage. `last_action = approved`. No status change yet — the PO stays `in_progress` until the final approval stage. |
| `PO_POST_004` | Final approval (`in_progress → sent`) | Set `po_status = sent`, `approval_date = now()`, `last_action = approved`. Append `history`. Send PO to vendor via the application's email/transmit layer. From this point on, the PO is a vendor-facing commitment. |
| `PO_POST_005` | Reject (`in_progress → draft`) | Set `po_status = draft`, `last_action = rejected`, reset `workflow_current_stage` to start. Append rejection comment in `tb_purchase_order_comment` (type `system`). Lines remain editable. |
| `PO_POST_006` | GRN partial receipt (`sent → partial` or `partial → partial`) | For each affected PO line, the GRN posting increments `tb_purchase_order_detail.received_qty` by the GRN quantity (in order UoM). If `received_qty < order_qty − cancelled_qty` for at least one line, set `po_status = partial`. Bridge rows `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` are updated proportionally to retain PR-side allocation visibility. |
| `PO_POST_007` | GRN full receipt (`sent → completed` or `partial → completed`) | When every active line satisfies `received_qty = order_qty − cancelled_qty`, set `po_status = completed`. Append `history`. PO is closed normally — no further GRNs accepted. |
| `PO_POST_008` | Three-way match success | Verify (a) PO line, (b) GRN line, (c) vendor invoice (AP) for the same product agree on quantity (within tolerance) and price (within tolerance). On success, the AP module clears the GRN accrual and posts the vendor invoice for payment. PO itself is not transitioned by this event — it remains at whichever status reflects fulfilment (`partial` or `completed`). |
| `PO_POST_009` | Three-way match failure | AP invoice is held in dispute. A `system` comment is appended on the PO and a deviation record is opened on the vendor / vendor-pricelist side. The PO is not auto-voided; resolution is manual via amendment, credit note, or void. |
| `PO_POST_010` | Void (`* → voided` from any of `draft`, `in_progress`, `sent`, `partial`) | Set `po_status = voided`, `is_active = false`, `last_action_at_date = now()`. Reverse any soft commitments downstream (budget, vendor-side notification). If voiding from `partial`, GRNs already posted remain valid — only the unfulfilled remainder is voided. `voided` is terminal. |
| `PO_POST_011` | Close (`partial → closed` early-termination) | Set `po_status = closed`. For each line still pending fulfilment, the application writes back the remainder to `cancelled_qty` so that `received_qty + cancelled_qty = order_qty`. Used when the vendor cannot supply the remaining quantity. Distinct from `completed` (full receipt). `closed` is terminal. |
| `PO_POST_012` | Soft delete | `deleted_at = now()`, `deleted_by_id = user`. Only allowed at `draft` per `PO_AUTH_005`. Row remains in the database; all unique indexes include `deleted_at` so a new PO can reuse the same `po_no`. |

State diagram (Prisma-canonical):

```
[*] → draft → in_progress → sent → partial → completed
                ↑    ↓        ↓       ↓         ↑
              (reject)        ↓       ↓     (full receipt)
                              ↓       └→ closed (early term.)
                              ↓
        any non-terminal → voided  (admin)
```

`completed`, `closed`, and `voided` are terminal. `draft` accepts soft-delete.

## 6. Cross-Module Rules

Rule IDs follow `PO_XMOD_NNN`.

| Rule ID | Related module | Rule |
| ------- | -------------- | ---- |
| `PO_XMOD_001` | [[purchase-request]] | When `po_type = purchase_request`, the PO must be created via the PR-to-PO conversion flow, which groups selected approved PRs by `(vendor_id, currency_id)` and produces one PO per group. Each resulting PO line carries one or more bridge rows in `tb_purchase_order_detail_tb_purchase_request_detail` linking it back to the originating PR line(s) (`PO_VAL_014`). |
| `PO_XMOD_002` | [[purchase-request]] | The bridge supports consolidation (many PR lines → one PO line) and partial conversion (one PR line → many PO lines). The PR line is considered fully converted only when `Σ bridge.pr_detail_qty` for that `pr_detail_id` equals the PR line's approved quantity. |
| `PO_XMOD_003` | [[good-receive-note]] | A GRN may only be created against a PO whose `po_status ∈ {sent, partial}` (`PO_AUTH_008`). The GRN detail back-references `tb_purchase_order_detail.id`; the pending quantity available for receipt is `order_qty − received_qty − cancelled_qty` per `PO_POST_006`. |
| `PO_XMOD_004` | [[good-receive-note]] | Receiving a quantity that would exceed the pending qty is rejected unless tenant configuration permits over-receipt within a tolerance; otherwise the GRN line is capped at the pending qty. |
| `PO_XMOD_005` | [[vendor-pricelist]] | At PR-to-PO conversion, the system snapshots `price` from the active vendor pricelist for the `(vendor, product, currency)` tuple. If no active pricelist row exists, the PR's last-known price is used and a `system` comment is appended flagging the missing pricelist coverage. |
| `PO_XMOD_006` | [[vendor-pricelist]] | When the buyer overrides a snapshot price, the delta against the pricelist is logged in `tb_purchase_order_detail_comment` as a deviation entry. Deviations above tenant tolerance route the PO to a high-value approval stage even if `total_amount` is below the threshold. |
| `PO_XMOD_007` | AP / Three-way match | On GRN posting the AP module raises an inventory-accrual liability. The accrual is cleared, and the vendor invoice is posted, only on three-way-match success per `PO_POST_008`. PO closure (`completed` or `closed`) does not by itself clear the accrual — that is AP's responsibility against the actual invoice. |
| `PO_XMOD_008` | [[inventory]] | Inventory on-hand is **not** incremented by PO posting — it is incremented only when the GRN posts (which is in scope for the GRN module). The PO contributes the "on-order" pipeline quantity that inventory planning reads via `order_qty − received_qty − cancelled_qty` on active PO lines. |
| `PO_XMOD_009` | [[inventory]] | The PO line's `base_qty` (computed in base UoM via `PO_CALC_011`) is the quantity that inventory reservations and projected-on-hand calculations read; the order UoM is for vendor-facing display only. |

## 7. References

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — PO consolidated BA (Section 1.3 Business Rules, Section 1.4 System Calculation Rules, Section 6.1 State Diagram, Section 2.5 RBAC). State labels are reconciled to the Prisma enum values per [[purchase-order/01-data-model]] § 5.
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — validation, error-type, and workflow-state structures inherited by PO.
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — Section 3 (Business Rules) and Section 3.6 (System Calculation Rules); PO's calculation rules (`PO_CALC_*`) are the direct PR-rule counterparts (`PR_036`–`PR_055`).
- Sibling: `en/purchase-order/01-data-model.md` — canonical Prisma model, enum values, and the bridge-table linkage that Section 5 and Section 6 rely on.
- Backend rule implementation (when added): `../carmen-turborepo-backend-v2/apps/` — the purchase-order service module is the implementation hook for these rules (status guards, calculation utilities, GRN posting back-references, three-way-match orchestration).
