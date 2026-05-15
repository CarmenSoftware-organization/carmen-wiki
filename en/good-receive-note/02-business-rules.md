---
title: Good Receive Note (GRN) — Business Rules
description: Validation, calculation, authorization, posting, three-way-match, and cross-module rules for good-receive-note.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — Business Rules

## 1. Overview

This page captures the operational business rules that govern a Good Receive Note (GRN) document through its lifecycle: input validation at create / edit / commit time, monetary calculation (line and header, including extra-cost allocation in three modes), authorization gates by role and document status, posting effects on each transition of `enum_good_received_note_status`, three-way match against the upstream PO and the downstream vendor invoice, and cross-module rules with [[purchase-order]], [[inventory]], [[vendor-pricelist]], and [[costing]]. The GRN is the central anchor of the procure-to-pay matching leg: until a GRN commits, no inventory is incremented and no AP accrual is raised; once committed, the PO line advances toward fulfilment and the GRN becomes the evidence that completes the three-way match.

Two structural points colour every rule below and are worth restating up front. **First**, lot number, expiry date, and FIFO / average-cost layer data **do not live on the GRN line** — they live on `tb_inventory_transaction_detail` and are reached via `tb_good_received_note_detail_item.inventory_transaction_id`. The GRN detail_item is the receipt-event cursor; the inventory transaction is the lot store (see [[good-receive-note/01-data-model]] § 5 item 3). So rules referencing "lot info" enforce the linkage to a valid inventory transaction at commit, not column-level checks on the GRN. **Second**, extra-cost allocation has **three** modes in the canonical Prisma model — `manual`, `by_value`, and `by_qty` — not the five (`MANUAL`, `BY_VALUE`, `BY_QUANTITY`, `BY_WEIGHT`, `BY_VOLUME`) that some legacy carmen/docs files claim; `by_weight` and `by_volume` are not implemented at the schema level. The rules below treat the Prisma enum (`enum_allocate_extra_cost_type`) as canonical.

## 2. Validation Rules

Rule IDs follow `GRN_VAL_NNN`. Header rules (001–005) run on every save and on commit; line rules (006–010) run per line on save and on commit; aggregate / at-commit rules (011–014) run only at the `saved → committed` transition.

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `GRN_VAL_001` | `tb_good_received_note.vendor_id` references a non-soft-deleted `tb_vendor` row. Required by submit time; nullable on early drafts to support multi-PO consolidation that resolves vendor later. | Save (warn), commit (block) | Reject on commit with "Vendor is required and must be from the approved vendor list." |
| `GRN_VAL_002` | `tb_good_received_note.currency_id` references a non-soft-deleted `tb_currency`; `exchange_rate > 0` and `exchange_rate_date` is set. | Create, edit, commit | Reject with "Transaction currency and a positive exchange rate are required." |
| `GRN_VAL_003` | `grn_date` (receipt date) is not null and not in the future beyond tenant tolerance; when present, `invoice_date <= grn_date + tenant_invoice_grace_days`. | Edit, commit | Reject with "Receipt date is required and invoice date must be consistent with the receipt." |
| `GRN_VAL_004` | When `doc_type = purchase_order`, at least one line carries `purchase_order_detail_id`. When `doc_type = manual`, no line has `purchase_order_detail_id`. | Save line, commit | Reject with "PO reference is required for PO-sourced GRNs and must be absent for manual GRNs." |
| `GRN_VAL_005` | `(invoice_no, vendor_id)` combination is unique across non-soft-deleted GRNs (legacy BR-01: invoice-uniqueness for transaction sequence). | Commit | Reject with "An invoice with this number has already been received from this vendor." |
| `GRN_VAL_006` | Each `tb_good_received_note_detail` row has non-null `product_id` and `location_id`, both referencing active, non-soft-deleted rows in `tb_product` / `tb_location`. | Save line, commit | Reject the line with "Product and receiving location are required on every GRN line." |
| `GRN_VAL_007` | Each `tb_good_received_note_detail` row has at least one non-soft-deleted `tb_good_received_note_detail_item` (the receipt-event row); on each detail_item, `received_qty > 0` (paid receipt) **or** `foc_qty > 0` (free-of-charge receipt). A line with neither is invalid. | Save line, commit | Reject the line with "Each line must record either a received quantity or a free-of-charge quantity greater than zero." |
| `GRN_VAL_008` | On every detail_item, `received_unit_id` is non-null and `received_unit_conversion_factor > 0`; `received_base_qty = Round(received_qty × received_unit_conversion_factor, 3)`. Same rule applies to the `order_*` and `foc_*` triples when their respective qty is non-zero. | Save line, commit | Reject the line with "Each receipt event must specify a valid receiving UoM with a positive conversion factor." |
| `GRN_VAL_009` | When the detail line references a PO line (`purchase_order_detail_id` is set), the receipt unit either matches the PO line's `order_unit_id` or has a conversion factor to the same `base_unit_id` as the PO line; the receiving quantity (in base UoM) does not exceed `(order_qty − received_qty − cancelled_qty)` on the PO line (pending qty). Tenant tolerance for over-receipt may relax this. | Save line, commit | Reject the line with "Receipt quantity exceeds the pending quantity on PO line `<po_no>:<seq>`; over-receipt tolerance not enabled." |
| `GRN_VAL_010` | On every detail_item, monetary fields are non-negative: `tax_rate >= 0`, `discount_rate >= 0`, `base_price >= 0`. When `is_tax_adjustment = true` or `is_discount_adjustment = true`, an explicit override amount must be persisted. | Save line, commit | Reject the line with "Tax / discount rate and unit price must be non-negative; manual override requires an explicit amount." |
| `GRN_VAL_011` | At commit, the GRN has at least one non-soft-deleted `tb_good_received_note_detail` row, and that row has at least one non-soft-deleted detail_item. | Commit | Reject with "GRN must contain at least one line with a recorded receipt event before it can be committed." |
| `GRN_VAL_012` | At commit, every detail_item that increments inventory (`received_qty > 0` or `foc_qty > 0`, and the product is `inventory` type — not consignment-only, not non-inventory expense) has produced a valid `tb_inventory_transaction` row whose `tb_inventory_transaction_detail` children carry a non-null `lot_no` (system-generated or user-supplied) and, when the product is flagged perishable, `expiry_date`. This is the linkage check, not a column-on-GRN check (see Section 1, point 1). | Commit | Reject with "Lot information is required for inventory items at commit; line `<seq>` is missing lot data on the linked inventory transaction." |
| `GRN_VAL_013` | At commit, for every PO-sourced line (`purchase_order_detail_id` set), the referenced PO has `po_status ∈ {sent, partial}`. A line whose PO has status `voided`, `closed`, `completed`, `draft`, or `in_progress` cannot post. | Commit | Reject with "Cannot receive against PO `<po_no>`: PO status `<status>` does not permit receiving. Voided POs are rejected outright." |
| `GRN_VAL_014` | Extra-cost allocation, when extra costs are present, has been completed before commit: every `tb_extra_cost` row tied to this GRN either has `allocate_extra_cost_type = manual` with persisted per-item allocations summing to the extra-cost net amount, or has `by_value` / `by_qty` and the application has computed and persisted the allocations into the per-item financial snapshot. Unallocated extra costs block commit. | Commit | Reject with "Extra costs must be allocated to lines before commit." (PRD §5.4 / `BR-EC-01`.) |

## 3. Calculation Rules

All monetary values are stored as `Decimal(20, 5)` at the row level; tax and discount **rates** are stored as `Decimal(15, 5)`; the exchange rate is `Decimal(15, 5)` on the GRN header. Display rounding is half-up to 2 decimals for currency amounts, 3 decimals for quantities, and 5 decimals for rates. Intermediate computations always re-read the rounded value of the prior step (matching the PR / PO catalogue, which the GRN technical spec inherits as `GRN_041`–`GRN_065`).

Rule IDs follow `GRN_CALC_NNN`.

| Rule ID | Formula |
| ------- | ------- |
| `GRN_CALC_001` (line subtotal) | `sub_total_price = Round(base_price × received_qty, 2)` in transaction currency. FOC qty is excluded from `sub_total_price` (PRD §3.4.5.5; the FOC portion is recorded as a separate detail_item row with `foc_qty` but no price contribution). |
| `GRN_CALC_002` (line discount) | `discount_amount = Round(Round(sub_total_price, 2) × discount_rate, 2)` unless `is_discount_adjustment = true`, in which case the persisted override wins. |
| `GRN_CALC_003` (line net, tax-exclusive pricing) | `net_amount = Round(Round(sub_total_price, 2) − Round(discount_amount, 2), 2)`. Tax is then `tax_amount = Round(Round(net_amount, 2) × tax_rate, 2)` unless `is_tax_adjustment = true`. |
| `GRN_CALC_004` (line tax-inclusive variant) | When the entered unit price already includes tax: `tax_amount = Round((sub_total_price − discount_amount) × tax_rate / (100 + tax_rate × 100), 2)`; `net_amount = sub_total_price − discount_amount − tax_amount`. `total_price` is unchanged. (PRD §3.4.5.5.) |
| `GRN_CALC_005` (line total) | `total_price = Round(Round(net_amount, 2) + Round(tax_amount, 2), 2)`. Tax-inclusive variant must satisfy `total_price = sub_total_price − discount_amount`. |
| `GRN_CALC_006` (variance) | `variance_qty = received_qty − order_qty` (per detail_item, in receiving UoM). Negative variance is partial receipt; positive is over-receipt (subject to `GRN_VAL_009`). Variance does not write back to the GRN row — it surfaces in the comparison view between the detail_item's `order_qty` and `received_qty`. |
| `GRN_CALC_007` (header roll-ups) | `tb_good_received_note.net_amount = Round(Σ Round(detail_item.net_amount, 2), 2)`; `total_amount = Round(Σ Round(detail_item.total_price, 2), 2)` plus allocated extra-cost tax (see `GRN_CALC_010`). Roll-ups are computed across active, non-soft-deleted detail_items of active lines. |
| `GRN_CALC_008` (base conversion) | For each money column `X` in transaction currency, `base_X = Round(Round(X, 2) × exchange_rate (5 dp), 2)`. Concretely `base_price`, `base_sub_total_price`, `base_discount_amount`, `base_net_amount`, `base_tax_amount`, `base_total_price`; the GRN header carries `base_net_amount` and `base_total_amount` roll-ups. |
| `GRN_CALC_009` (extra-cost — `manual`) | The user enters a per-line allocation amount; the sum of allocations across lines must equal `tb_extra_cost.net_amount` (tolerance ≤ `0.01` in transaction currency). Each allocated amount is written into the per-item financial snapshot and is included in `Last Cost` (PRD §3.4.5.5). |
| `GRN_CALC_010` (extra-cost — `by_value`) | `line_allocation = Round(Round(extra_cost_total, 2) × (line.net_amount / Σ line.net_amount), 2)`. Last line absorbs the rounding remainder so that `Σ allocations = extra_cost_total` (within ≤ `0.01`). |
| `GRN_CALC_011` (extra-cost — `by_qty`) | `line_allocation = Round(Round(extra_cost_total, 2) × (line.received_base_qty / Σ line.received_base_qty), 2)`. Quantities are summed in base UoM because lines may use different receiving UoMs. Last-line remainder rule same as `by_value`. |
| `GRN_CALC_012` (Last Cost — costing feed) | `Last Cost per unit = Round((line.net_amount + Σ line.extra_cost_allocations) / (received_qty + foc_qty), 5)`. This is what flows to the FIFO / average-cost layer in [[costing]] via the linked `tb_inventory_transaction_cost_layer.cost_per_unit`. Note: FOC qty is included in the denominator for Last Cost but excluded from `Last Price` (which is `net_amount / received_qty`). |
| `GRN_CALC_013` (rounding mode) | All rounding is half-up to the column precision (currency 2dp, quantity 3dp, rate / FX 5dp). |

### 3.1 Worked example (฿ THB transaction currency, tax-exclusive pricing)

Two lines, vendor in THB, `exchange_rate = 1.00000` (no FX), one extra-cost line allocated `by_value`.

- **Line 1** (one detail_item): `received_qty = 10.000`, `base_price = ฿125.50`, `discount_rate = 5%`, `tax_rate = 7%`.
  - `sub_total_price = Round(125.50 × 10.000, 2) = ฿1,255.00`
  - `discount_amount = Round(1,255.00 × 0.05, 2) = ฿62.75`
  - `net_amount = Round(1,255.00 − 62.75, 2) = ฿1,192.25`
  - `tax_amount = Round(1,192.25 × 0.07, 2) = ฿83.46`
  - `total_price = Round(1,192.25 + 83.46, 2) = ฿1,275.71`
- **Line 2** (one detail_item): `received_qty = 4.000`, `base_price = ฿89.00`, `discount_rate = 0%`, `tax_rate = 7%`.
  - `sub_total_price = ฿356.00`; `discount_amount = ฿0.00`; `net_amount = ฿356.00`
  - `tax_amount = Round(356.00 × 0.07, 2) = ฿24.92`
  - `total_price = ฿380.92`
- **Extra cost** (`tb_extra_cost.net_amount = ฿200.00`, `allocate_extra_cost_type = by_value`):
  - `Σ line.net_amount = 1,192.25 + 356.00 = ฿1,548.25`
  - Line 1 allocation: `Round(200.00 × (1,192.25 / 1,548.25), 2) = Round(154.01..., 2) = ฿154.01`
  - Line 2 allocation: remainder = `200.00 − 154.01 = ฿45.99`
- **Header roll-up**:
  - `net_amount = Round(1,192.25 + 356.00, 2) = ฿1,548.25`
  - `total_amount = Round(1,275.71 + 380.92, 2) = ฿1,656.63` (excl. extra-cost tax; if the extra cost itself carries 7% VAT of `฿14.00`, the header `total_amount` reads `฿1,670.63`).
- **Last Cost feed to inventory** (Line 1, assuming `foc_qty = 0`): `(1,192.25 + 154.01) / 10.000 = ฿134.626 per base unit`. This is what the linked `tb_inventory_transaction_cost_layer.cost_per_unit` receives; FIFO and average-cost calculations downstream consume it.

If Line 1 also has a parallel FOC detail_item with `foc_qty = 1.000`, `Last Cost` becomes `(1,192.25 + 154.01) / (10.000 + 1.000) = ฿122.388` — the FOC qty enters the cost layer at the diluted unit cost.

## 4. Authorization Rules

Rule IDs follow `GRN_AUTH_NNN`. Authorization is enforced by RBAC at the API layer plus workflow-stage gating via `tb_good_received_note.user_action.execute`. Role names mirror the carmen/docs RBAC table (Receiving Clerk / Inventory Manager / Finance Officer / Procurement Officer / AP Clerk). The Receiver ≠ Purchaser segregation rule is enforced at commit time, not at create.

| Rule ID | Subject | Right | Constraint |
| ------- | ------- | ----- | ---------- |
| `GRN_AUTH_001` | Receiving Clerk (Receiver) | Create GRN (`doc_status = draft`) | Both `purchase_order` and `manual` `doc_type`. For `purchase_order`, the referenced PO must be at `sent` or `partial` (`PO_AUTH_008` on the PO side; `GRN_VAL_013` on the GRN side). |
| `GRN_AUTH_002` | Receiving Clerk | Edit GRN, add / edit lines and detail_items | Only while `doc_status ∈ {draft, saved}`. Once at `committed`, the GRN is locked. |
| `GRN_AUTH_003` | Receiving Clerk | Save (`draft → saved`) | Passes Section 2 validation through `GRN_VAL_001`–`GRN_VAL_010`. The `saved` state means review-ready; lines are still editable, but a clear handoff exists for Inventory Manager review. |
| `GRN_AUTH_004` | Inventory Manager (Store Manager) | Edit / reconcile a `saved` GRN | The Inventory Manager may correct quantities, locations, and lot data while `doc_status = saved`. Reverts the GRN to `draft` if substantive header (vendor / currency / PO reference) changes are made. |
| `GRN_AUTH_005` | Inventory Manager | Commit (`saved → committed`) | Passes all of Section 2 (including the at-commit rules `GRN_VAL_011`–`GRN_VAL_014`). The commit is the single posting event (Section 5). Below-tenant-threshold GRNs may allow the Receiving Clerk to self-commit if the workflow permits. |
| `GRN_AUTH_006` | Inventory Manager | Batch commit (PRD §3.7.2) | The Inventory Manager selects multiple `saved` GRNs and commits them as a unit. Per-GRN validation still applies; failures in any one GRN leave that GRN at `saved` and surface a per-GRN result summary. |
| `GRN_AUTH_007` | Finance Officer / AP Clerk | Adjust extra-cost allocation pre-AP-posting | Allowed while `doc_status ∈ {draft, saved}` and **before** the three-way match has cleared the GRN to AP. Once `committed` and AP-posted, allocation is frozen; corrections require a `tb_credit_note` against the GRN or a compensating inventory adjustment. |
| `GRN_AUTH_008` | Inventory Manager / Procurement Officer (elevated rights) | Void GRN (`draft → voided` or `saved → voided`) | Allowed only before commit. A `committed` GRN cannot be voided — corrections after commit go through `tb_credit_note` or [[inventory-adjustment]]. `voided` is terminal. |
| `GRN_AUTH_009` | Procurement Officer / AP Clerk | View, export reports | Read-only across all statuses. |
| `GRN_AUTH_010` | Segregation of duties — **Receiver ≠ Purchaser** | The user committing a GRN (`last_action_by_id` on the `saved → committed` transition) MUST NOT be the same user who created or transmitted the upstream PO (`tb_purchase_order.buyer_id` or the user who actioned `in_progress → sent`). | Enforced at commit. Mirror rule on the PO side is `PO_AUTH_010`. |
| `GRN_AUTH_011` | Workflow-derived authorization | Stage-gated commit | The set of users in `tb_good_received_note.user_action.execute` at the current `workflow_current_stage` is the only set permitted to advance the document; all other commit attempts are rejected. |

## 5. Posting Rules

Status values are the literal members of `enum_good_received_note_status` documented in [[good-receive-note/01-data-model]] § 4: **`draft`**, **`saved`**, **`committed`**, **`voided`**. The full lifecycle is therefore `draft → saved → committed`, with `voided` as an administrative escape from any pre-commit state. The single posting event is the `saved → committed` transition; nothing posts at `draft` or `saved`. There is no `pending_approval`, `approved`, `rejected`, `closed`, or `cancelled` value at the Prisma level (legacy carmen/docs `GRNStatus` enum is divergent — see [[good-receive-note/01-data-model]] § 5 item 1).

Rule IDs follow `GRN_POST_NNN`.

| Rule ID | Transition / Event | Effects |
| ------- | ------------------ | ------- |
| `GRN_POST_001` | Create (→ `draft`) | Insert `tb_good_received_note` with `doc_status = draft`, `doc_version = 0`, `net_amount = base_net_amount = total_amount = base_total_amount = 0`. Append to `workflow_history`: `{ stage: 'draft', action: 'created', by, at }`. No inventory, no GL, no PO impact. |
| `GRN_POST_002` | Save (`draft → saved`) | Recompute all roll-ups (`GRN_CALC_007`). Set `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user`. Initialise `workflow_current_stage` and populate `user_action.execute` from the next workflow stage. Append `workflow_history` entry. The GRN is now review-ready; **no inventory or GL impact yet** — the `saved` state is the "received but not yet posted" Prisma equivalent of the PRD's `Received` state. |
| `GRN_POST_003` | Commit (`saved → committed`) — **the posting event** | Set `doc_status = committed`, `last_action = approved` (or `submitted` per workflow), `last_action_at_date = now()`. Append `workflow_history`. Then the cross-module fan-out fires atomically: see `GRN_POST_004`–`GRN_POST_008`. |
| `GRN_POST_004` | Commit — inventory side (cross-ref [[inventory]]) | For each detail_item whose product is inventory-type and `received_qty + foc_qty > 0`, insert a `tb_inventory_transaction` (Stock In, Consignment In if `is_consignment = true`, or Non-Inventory) plus its `tb_inventory_transaction_detail` children carrying `lot_no`, `expiry_date`, `cost_per_unit`. Stamp the inserted id on `tb_good_received_note_detail_item.inventory_transaction_id`. On-hand at `(location_id, product_id)` is incremented by `received_base_qty + foc_base_qty`. Cost-layer rows in `tb_inventory_transaction_cost_layer` are created per the tenant's costing method (FIFO or moving-average); `cost_per_unit` is the `GRN_CALC_012` Last Cost figure. Consignment receipts increment a separate consignment-stock register, not regular on-hand. |
| `GRN_POST_005` | Commit — PO side (cross-ref [[purchase-order]]) | For each line with `purchase_order_detail_id` set, increment `tb_purchase_order_detail.received_qty` by `received_base_qty` (in base UoM). If after the increment `Σ received_qty < Σ (order_qty − cancelled_qty)` across active lines of that PO, set the PO's `po_status = partial` (or leave at `partial`). If `Σ received_qty = Σ (order_qty − cancelled_qty)`, set `po_status = completed`. Bridge rows on `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` are updated proportionally to keep PR-side allocation visibility. |
| `GRN_POST_006` | Commit — GL accrual for AP-pending | Post the inventory-receipt journal entry: **Dr** Inventory (or Inventory in Transit / Expense for non-inventory) at the GRN's `base_net_amount + allocated_extra_cost`; **Cr** GRN Clearing / Goods Received Not Invoiced (AP accrual) at the same amount. Tax is posted to the input-tax control account per tax-profile rules. The accrual sits in GRN Clearing until the three-way match clears it (`GRN_POST_008`). Cash GRNs (`is_cash = true`) **skip** the AP accrual and instead debit directly against the cash / vendor-direct account. |
| `GRN_POST_007` | Commit — three-way-match anchor | The committed GRN is the receiving leg of the three-way match (`PO ↔ GRN ↔ Invoice`). The GRN exposes `invoice_no`, `invoice_date`, `vendor_id`, line-level `net_amount` and `received_qty` to the AP module for matching against the vendor invoice when it arrives. Match tolerance (qty and price) is tenant-configured. Until the invoice arrives, the GRN's accrual stays open. |
| `GRN_POST_008` | Three-way match success | AP module verifies that PO line, GRN line, and vendor invoice agree on qty and price within tolerance. On success, AP clears GRN Clearing (Dr GRN Clearing, Cr Accounts Payable) and posts the vendor invoice for payment. The GRN itself is not transitioned by this event — it stays at `committed`. |
| `GRN_POST_009` | Three-way match failure | AP invoice is held in dispute. A `system` comment is appended on the GRN and on the PO. The GRN is **not** auto-voided (since `voided` is pre-commit only); resolution is via `tb_credit_note` against the GRN, amendment of the vendor invoice, or compensating inventory adjustment in [[inventory-adjustment]]. |
| `GRN_POST_010` | Void (`draft → voided` or `saved → voided`) | Set `doc_status = voided`, `is_active = false`, `last_action_at_date = now()`. No inventory or GL impact (the GRN never posted). Lines and detail_items remain readable for audit. `voided` is terminal — no transitions out. **Voiding a `committed` GRN is not allowed**; post-commit corrections use `tb_credit_note` or compensating inventory adjustment. |
| `GRN_POST_011` | Soft delete | `deleted_at = now()`, `deleted_by_id = user`. Permitted only at `draft` (per `GRN_AUTH_008` spirit). Row remains in the database; the `@@unique([grn_no, deleted_at])` index lets a new GRN reuse the same `grn_no`. |
| `GRN_POST_012` | End-of-period auto-commit (PRD §3.7.3) | A scheduled batch commits all `saved` GRNs at period close. Per-GRN validation still applies (`GRN_VAL_011`–`GRN_VAL_014`); failures stay at `saved` and surface in the period-close exception report. |

State diagram (Prisma-canonical):

```
[*] → draft → saved → committed
        ↓       ↓
       voided  voided           (committed is terminal save via credit-note path)
```

`committed` and `voided` are terminal. `draft` accepts soft-delete.

## 6. Cross-Module Rules

Rule IDs follow `GRN_XMOD_NNN`.

| Rule ID | Related module | Rule |
| ------- | -------------- | ---- |
| `GRN_XMOD_001` | [[purchase-order]] | A GRN may only be created against a PO whose `po_status ∈ {sent, partial}`. Receiving against `voided` POs is rejected outright (`GRN_VAL_013`); receiving against `draft`, `in_progress`, `closed`, or `completed` POs is also rejected. The pending quantity available is `order_qty − received_qty − cancelled_qty` per active PO line. |
| `GRN_XMOD_002` | [[purchase-order]] | On commit, the GRN advances the PO line's `received_qty` (`GRN_POST_005`) and may move `po_status` from `sent → partial` (any partial receipt) or `* → completed` (full receipt). Multi-PO GRNs (PRD §3.2.3) iterate this per source PO — all source POs must be from the same vendor and currency. |
| `GRN_XMOD_003` | [[purchase-order]] | Receiving a quantity exceeding pending qty is rejected unless tenant config permits over-receipt tolerance; otherwise the GRN line is capped at pending qty. Cancellation feedback (`BR-02`): if the user records a cancelled portion at receipt, the cancellation writes back to `tb_purchase_order_detail.cancelled_qty`, advancing the PO toward `closed` if no pending remainder remains. |
| `GRN_XMOD_004` | [[inventory]] | Inventory on-hand is incremented **only at GRN commit** (`GRN_POST_004`) — not at GRN save, not at PO post. The increment is via insert into `tb_inventory_transaction` / `tb_inventory_transaction_detail`, reached from the GRN side through `tb_good_received_note_detail_item.inventory_transaction_id`. Consignment receipts (`is_consignment = true`) increment a parallel consignment register and do not affect owned-stock on-hand. Non-inventory items do not increment any on-hand counter; they post directly to expense. |
| `GRN_XMOD_005` | [[inventory]] | Lot number, expiry date, manufacturing date, and serial number live on `tb_inventory_transaction_detail` (and `tb_inventory_transaction_cost_layer.lot_no`), **not** on the GRN line. The GRN detail_item is the receipt-event cursor that points to the inventory transaction. UI surfaces lot data via this linkage; the divergence from the carmen/docs PRD §3.5 / Technical Spec `GRNItem.lotNumber` claim is documented in [[good-receive-note/01-data-model]] § 5 item 3. |
| `GRN_XMOD_006` | [[costing]] | Valuation at commit is per the tenant's costing method — typically FIFO or moving-average. `GRN_CALC_012`'s Last Cost per unit (net + allocated extra costs / received qty + foc qty) is the figure written to `tb_inventory_transaction_cost_layer.cost_per_unit`. The costing module is responsible for layer creation (FIFO) and weighted-average recomputation; the GRN module is responsible only for feeding the unit cost. |
| `GRN_XMOD_007` | AP / Finance / three-way match | At commit, the GRN raises an inventory-accrual liability (Dr Inventory, Cr GRN Clearing / GR-NI; `GRN_POST_006`). The accrual is cleared only when the three-way match succeeds against the vendor invoice (`GRN_POST_008`). Cash GRNs (`is_cash = true`) skip the accrual. Credit notes (`tb_credit_note` against this GRN) are the post-commit correction path. |
| `GRN_XMOD_008` | [[vendor-pricelist]] | At GRN entry, the system reads the active vendor pricelist for `(vendor_id, product_id, currency_id)` and surfaces the expected unit price next to the receiving unit price as a variance hint. When the recorded `base_price` deviates from the pricelist beyond tenant tolerance, a `system` comment is appended on the GRN line and a vendor-performance deviation event is raised for vendor scoring. Manual GRNs (`doc_type = manual`) follow the same lookup, falling back to the product's last-known purchase price if no pricelist exists. |
| `GRN_XMOD_009` | Vendor performance | Receipt variance feedback (qty variance per `GRN_CALC_006`, price variance per `GRN_XMOD_008`, on-time-delivery measured against the PO's `delivery_date`) feeds the vendor scoring system referenced under PRD §9.4. The feed is a side-effect of commit; no separate posting is required. |
| `GRN_XMOD_010` | [[inventory-adjustment]] | Post-commit corrections that are not credit-note-eligible (e.g. mis-counted lots, damaged stock discovered after putaway) flow through inventory-adjustment, not through GRN editing. A reference back to the originating `tb_good_received_note.id` is recorded on the adjustment for audit. |

## 7. References

- `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md` — System Calculation Rules (`GRN_041`–`GRN_065`) inherited as the `GRN_CALC_NNN` series above. Note: the Technical Spec's `GRNStatus` enum and 5-mode `AllocationMethod` enum are divergent from Prisma; the rules above use Prisma values (`draft`/`saved`/`committed`/`voided` and `manual`/`by_value`/`by_qty`).
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — §5 Business Rules (status transitions, inventory updates, integration `BR-01`/`BR-02`, validation), §3.7 Commit Process (individual / batch / end-of-period auto-commit), §3.4.5.5 tax-inclusive vs tax-exclusive calculation logic.
- `../carmen/docs/good-recive-note-managment/grn-create-process-doc.md` — Process flow (PO-based and manual) and validation gates at each screen, mapped above onto `GRN_VAL_*` and `GRN_AUTH_*`.
- Sibling: `en/good-receive-note/01-data-model.md` — canonical Prisma model, enum values (in particular the four-value `enum_good_received_note_status` and the three-value `enum_allocate_extra_cost_type` on `tb_extra_cost`), and the divergence catalogue that Section 1, Section 3, and Section 6 rely on.
- Backend rule implementation (when added): `../carmen-turborepo-backend-v2/apps/` — the good-received-note service module is the implementation hook for these rules (status guards, calculation utilities, inventory-transaction creation, PO-line advance, three-way-match anchor).
