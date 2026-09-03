---
title: Credit Note
description: Vendor-issued credit document reversing all or part of a prior PO / GRN — reverses the inventory cost layer (returns goods or revalues cost); AP/GL posting is unconfirmed (design intent only, no such code exists).
published: true
date: 2026-07-29T10:00:00.000Z
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Credit Note

> **At a Glance**
> **Owner:** Procurement / AP &nbsp;·&nbsp; **Table:** `tb_credit_note` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** reuses PO-side definition &nbsp;·&nbsp; **Upstream:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; Post-receipt offset against a prior GRN — reverses the inventory cost layer (returns goods or revalues cost); AP/GL posting is unconfirmed — no such code exists in the backend (design intent).

![Credit Note screen](/screenshots/purchase-order/credit-note.png)

![Credit Note detail screen](/screenshots/purchase-order/credit-note-detail.png)

## 1. What & Who

A **Credit Note (CRN)** is the post-receipt correction instrument in procure-to-pay. When a vendor over-bills, ships defective or short goods, or grants a retrospective rebate, the CRN documents the offset against the originating GRN and reverses the inventory cost layer. **Unconfirmed:** no AP-liability-posting code exists anywhere in the credit-note backend (see § 4). Two variants: **`quantity_return`** physically returns goods (decrements stock, reverses the cost layer) and **`amount_discount`** is a pure price correction (no inventory movement, revalues lot cost).

**Created by** Procurement when the vendor issues a credit invoice &nbsp;·&nbsp; **Approved by** workflow approvers (PO-style routing) &nbsp;·&nbsp; **Read by** the costing engine. **Unconfirmed** whether AP consumes this document — no debit-memo or AP-posting code exists in the backend.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Raise a CN against a GRN | Procurement → Credit Note → **New** | Pick the GRN; lines pre-fill from receipted quantities |
| Pick `quantity_return` vs `amount_discount` | Header `credit_note_type` | Return moves stock; discount only revalues cost |
| Set return-to-stock vs write-off | (Automatic) | Engine consumes the GRN's own FIFO lots first, then falls back to other available lots for the same product+location; any variance between the CN's cost and the consumed lot's cost is recorded as `diff_amount` on the cost-layer row — **not** posted to any GL/write-off account (no such posting code exists) — see [costing](/en/inventory/costing) `COST_XMOD_006` |
| Apply CN to AP | Completes on `doc_status = completed` | **Unconfirmed** — no AP debit-memo or AP-posting code exists anywhere in the credit-note backend (design intent only); `completed` only triggers the inventory posting described in § 6 |
| Cite vendor's credit-invoice ref | Header `invoice_no` / `tax_invoice_no` | Vendor-side reference fields for AP reconciliation. **Unverified this pass:** whether these fields feed a downstream three-way-match — no such match feature was found elsewhere in the `purchase-order` module's current source (see [03-user-flow-finance.md](/en/inventory/purchase-order/03-user-flow-finance)). |
| Void a posted CN | Detail → **Void** | Only while the posting period is open; reverses every posting |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "GRN required for quantity_return" | Type is `quantity_return` but `grn_id` empty | Pick the anchor GRN |
| "Return qty exceeds receipted - already returned" | Cumulative returns would over-deplete the lot | Reduce qty or split across multiple lots |
| "Tax rate must match GRN snapshot" | `is_tax_adjustment = true` was expected for retrospective tax | Toggle `is_tax_adjustment` on the line |
| "Period is closed — cannot void" | Posting period for the CRN has closed | **Unconfirmed** — no functional JV-creation code exists; `tb_jv_header` appears only as an inert placeholder key in a generic doc-type dispatch map (`workflows.service.ts`'s `DOCUMENT_TABLE_MAP`), with `activity-registry.ts` explicitly noting no handler owns it; no compensating-entry mechanism was found for this case |
| "Rate not in history" | **Unconfirmed — no such validation found.** `exchange_rate` is a freely-editable snapshot field with no dynamic `tb_exchange_rate` lookup anywhere in the credit-note backend (zero repo-wide hits for this message) | — (see § 4 "FX rate handling") |
| "User not authorised at this stage" | Signed-in user not in `user_action.execute[]` | Wait for the correct approver, or escalate |

## 4. Edge Cases

- **Money rounding.** Line money fields stored at `Decimal(20,5)`; computed totals round half-up to **2 decimals** at line level, then sum into header (matches PO/GRN rounding).
- **FX rate handling.** `exchange_rate` is a plain snapshot field, auto-populated once — either from the selected GRN's rate or from the currency master's current rate (`cn-general-fields.tsx`) — and then freely editable. **Unconfirmed/corrected:** no dynamic rate re-resolution keyed on `cn_date` and no FX gain/loss computation exists anywhere in the credit-note backend; this mirrors the same finding already established for PO/PR/GRN in [master-data/exchange-rate](/en/inventory/master-data/exchange-rate).
- **Return-to-stock vs write-off.** `quantity_return` consumes the GRN's own FIFO lots first, then falls back to other available lots for the same product+location (still FIFO order); no negative-inventory guard blocks this path — if no stock is available anywhere, `out_qty = 0` and the CN's cost is recorded entirely as `diff_amount` on the cost-layer row. **No GL/write-off-account posting exists anywhere in the backend** — `diff_amount` is a plain column on `tb_inventory_transaction_cost_layer`, not a general-ledger entry (confirmed absent module-wide; see [inventory/02-business-rules](/en/inventory/inventory/02-business-rules)).
- **Snapshot semantics.** Vendor name, product, currency, FX rate, tax rate, and pricelist refs are snapshotted at draft. Master-record edits do NOT retroactively change the CRN.
- **Voiding window.** A `completed` CRN may only be voided while its period is open. Once `tb_period.status = closed`, voiding is rejected.
- **No AP posting exists.** Neither `quantity_return` nor `amount_discount` creates a debit memo or any AP-side record on `completed`. **Unconfirmed — design intent only:** no AP-posting code was found anywhere in the credit-note backend (`credit-note.logic.ts`, `credit-note.service.ts`, `inventory-transaction.service.ts`).

---

## 5. Data Model (Dev)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`).

### 5.1 `tb_credit_note`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cn_no` | `String? @db.VarChar` | Yes | CRN reference number; unique among non-deleted rows. |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — used to generate `cn_no` (`generateCnNo`). **Corrected:** does not drive FX rate resolution (no such code exists) and inventory posting on submit resolves the period from the actual submission time, not `cn_date`. |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `in_progress` → `completed` / `cancelled` / `voided`. |
| `credit_note_type` | `enum_credit_note_type` | No | `quantity_return` or `amount_discount`. |
| `vendor_id`, `vendor_name` | `String? @db.Uuid` / `VarChar` | Yes | Snapshot from `tb_vendor` at draft. |
| `grn_id`, `grn_no`, `grn_date` | mixed | Yes | Anchor GRN — required for `quantity_return`, optional for `amount_discount`. |
| `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` | mixed | Yes | Optional pricelist reference. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Currency + rate snapshot, auto-populated once from the selected GRN's or currency master's rate at edit time and freely editable thereafter. **Corrected:** not dynamically resolved against `cn_date` — no such code exists. |
| `cn_reason_id`, `cn_reason_name`, `cn_reason_description` | mixed | Yes | FK + snapshot to `tb_credit_note_reason`. |
| `invoice_no`, `invoice_date`, `tax_invoice_no`, `tax_invoice_date` | mixed | Yes | Vendor's credit-invoice reference for AP matching. |
| `workflow_id`, `workflow_*`, `user_action` | mixed | Yes | Workflow state (see Section 6). |
| `last_action`, `last_action_*` | mixed | Yes | Most recent transition. |
| `note`, `description`, `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([cn_no, deleted_at])` map `creditnote_cn_no_u`; `@@index([cn_no])`. FKs to `tb_vendor`, `tb_currency`, `tb_good_received_note`, `tb_credit_note_reason` — all `onDelete: NoAction`.

### 5.2 `tb_credit_note_detail`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `credit_note_id`, `sequence_no` | mixed | No / No / Yes | PK, parent FK, ordinal. |
| `inventory_transaction_id` | `String? @db.Uuid` | Yes | FK to originating `tb_inventory_transaction` for `quantity_return`. Null for `amount_discount`. |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | Original receipt location; return sources from same. |
| `product_id`, `product_*` | mixed | No / Yes | Product snapshot. |
| `return_qty`, `return_unit_*`, `return_conversion_factor`, `return_base_qty` | `Decimal(20,5)` / mixed | Yes | Return qty in user unit + base. `0` for `amount_discount`. |
| `price` | `Decimal(20,5)` | Yes | Unit price — typically the GRN line price. |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | Tax snapshot + base conversion. |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | Discount snapshot + base. |
| `extra_cost_amount`, `base_extra_cost_amount` | `Decimal(20,5)` | Yes | Allocated extra-cost credit (e.g. freight). |
| `sub_total_price`, `net_amount`, `total_price` | `Decimal(20,5)` | Yes | Line totals in transaction currency. |
| `base_*` | `Decimal(20,5)` | Yes | Same in BU base currency. |
| `info`, `dimension`, `doc_version`, audit | — | Yes | Standard metadata. |

**Constraints:** `@@unique([credit_note_id, sequence_no, deleted_at])`; `@@index([credit_note_id, sequence_no])`. FKs `onDelete: NoAction`.

### 5.3 Comment tables

`tb_credit_note_comment` and `tb_credit_note_detail_comment` follow the canonical comment shape — see [purchase-request/01-data-model](/en/inventory/purchase-request/01-data-model).

## 6. Workflow / Business Rules

`doc_status`: `draft` → `in_progress` → `completed` (terminal); `cancelled` and `voided` are terminal alternatives.

- **`draft`** — editable; no GL, AP, inventory effect.
- **`in_progress`** — locked except where the active stage permits; approvers from `user_action.execute[]` per [system-config/workflow](/en/inventory/system-config/workflow).
- **`completed`** — inventory posting fires for `quantity_return` (FIFO/average lot consumption); cost revaluation for `amount_discount` (lot re-pricing or `diff_amount` variance). **Unconfirmed — no AP debit memo or AP-posting code exists for either type** (design intent only).
- **`cancelled`** — terminated before completion; no postings.
- **`voided`** — reversal of a `completed` CRN within the open period; reverses every posting.

Stage routing, role mapping, and action gating reuse the **PO-side workflow definition** by default. **GRN anchor:** return lines are bounded by `receipted - already returned` on the lot. **Authorisation:** only users in `user_action.execute[]` may transition.

## 7. Cross-References

- [purchase-order](/en/inventory/purchase-order) — the PO behind the original GRN; CRN totals roll up into PO open/received reporting.
- [good-receive-note](/en/inventory/good-receive-note) — anchor for every `quantity_return` line.
- [costing](/en/inventory/costing) — `COST_POST_003` (amount revaluation), `COST_XMOD_006` (lot cost reversal), `COST_CALC_005` (credit-note-amount lot revaluation — corrected; not FX, as previously miscited here).
- [master-data/credit-note-reason](/en/inventory/master-data/credit-note-reason) — reason taxonomy.
- [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) — rate snapshot pattern shared with PO/PR/GRN (auto-populate once, freely editable; no dynamic re-resolution).
- [master-data/vendor](/en/inventory/master-data/vendor) — vendor snapshot. AP debit-memo routing is unconfirmed (no such code exists).

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (lines 321-397), `tb_credit_note_detail` (lines 434-508), `tb_credit_note_comment` (lines 399-432), `tb_credit_note_detail_comment` (lines 510-543), enums `enum_credit_note_type` and `enum_credit_note_doc_status` (lines 195-206).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/procurement/credit-note/`.
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram.
