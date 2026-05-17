---
title: Credit Note
description: Vendor-issued credit document reversing all or part of a prior PO / GRN — adjusts AP liability and either cost-revalues the inventory layer or returns goods.
published: true
date: 2026-05-17T07:00:16.000Z
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Credit Note

> **At a Glance**
> **Owner:** Procurement / AP &nbsp;·&nbsp; **Table:** `tb_credit_note` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** reuses PO-side definition &nbsp;·&nbsp; **Upstream:** [[good-receive-note]] &nbsp;·&nbsp; Post-receipt offset against a prior GRN — reverses AP and either returns goods or revalues cost.

![Credit Note screen](/assets/screenshots/purchase-order/credit-note.png)

## 1. What & Who

A **Credit Note (CRN)** is the post-receipt correction instrument in procure-to-pay. When a vendor over-bills, ships defective or short goods, or grants a retrospective rebate, the CRN documents the offset against the originating GRN and reverses the AP liability. Two variants: **`quantity_return`** physically returns goods (decrements stock, reverses the cost layer) and **`amount_discount`** is a pure price correction (no inventory movement, revalues lot cost).

**Created by** Procurement when the vendor issues a credit invoice &nbsp;·&nbsp; **Approved by** workflow approvers (PO-style routing) &nbsp;·&nbsp; **Read by** AP (debit-memo source) and the costing engine.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Raise a CN against a GRN | Procurement → Credit Note → **New** | Pick the GRN; lines pre-fill from receipted quantities |
| Pick `quantity_return` vs `amount_discount` | Header `credit_note_type` | Return moves stock; discount only revalues cost |
| Set return-to-stock vs write-off | (Automatic) | Engine returns to the original FIFO lot; if lot is consumed, posts variance to write-off GL — see [[costing]] `COST_XMOD_006` |
| Apply CN to AP | Completes on `doc_status = completed` | Always emits an AP debit memo (`base_total_price`) |
| Cite vendor's credit-invoice ref | Header `invoice_no` / `tax_invoice_no` | Required for AP three-way match |
| Void a posted CN | Detail → **Void** | Only while the posting period is open; reverses every posting |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "GRN required for quantity_return" | Type is `quantity_return` but `grn_id` empty | Pick the anchor GRN |
| "Return qty exceeds receipted - already returned" | Cumulative returns would over-deplete the lot | Reduce qty or split across multiple lots |
| "Tax rate must match GRN snapshot" | `is_tax_adjustment = true` was expected for retrospective tax | Toggle `is_tax_adjustment` on the line |
| "Period is closed — cannot void" | Posting period for the CRN has closed | Raise a corrective journal voucher instead |
| "Rate not in history" | No `tb_exchange_rate` row on `cn_date` for that currency | Add a rate then re-open the CRN (see [[master-data/exchange-rate]]) |
| "User not authorised at this stage" | Signed-in user not in `user_action.execute[]` | Wait for the correct approver, or escalate |

## 4. Edge Cases

- **Money rounding.** Line money fields stored at `Decimal(20,5)`; computed totals round half-up to **2 decimals** at line level, then sum into header (matches PO/GRN rounding).
- **FX revaluation.** When `cn_date != grn_date` and currencies differ from BU base, engine resolves a fresh rate on `cn_date` and posts the delta to FX gain/loss per [[costing]] `COST_CALC_005`.
- **Return-to-stock vs write-off.** `quantity_return` reverses the FIFO lot if it still exists; if the lot is already consumed (issued via SR / stock-out), the variance lands on a configured **inventory write-off** GL account (no negative inventory).
- **Snapshot semantics.** Vendor name, product, currency, FX rate, tax rate, and pricelist refs are snapshotted at draft. Master-record edits do NOT retroactively change the CRN.
- **Voiding window.** A `completed` CRN may only be voided while its period is open. Once `tb_period.status = closed`, voiding is rejected.
- **AP always posts.** Even for `quantity_return`, a debit memo equal to `base_total_price` posts to vendor AP.

---

## 5. Data Model (Dev)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`).

### 5.1 `tb_credit_note`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cn_no` | `String? @db.VarChar` | Yes | CRN reference number; unique among non-deleted rows. |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — drives FX rate resolution. |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `in_progress` → `completed` / `cancelled` / `voided`. |
| `credit_note_type` | `enum_credit_note_type` | No | `quantity_return` or `amount_discount`. |
| `vendor_id`, `vendor_name` | `String? @db.Uuid` / `VarChar` | Yes | Snapshot from `tb_vendor` at draft. |
| `grn_id`, `grn_no`, `grn_date` | mixed | Yes | Anchor GRN — required for `quantity_return`, optional for `amount_discount`. |
| `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` | mixed | Yes | Optional pricelist reference. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Currency snapshot + FX rate on `cn_date`. |
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

`tb_credit_note_comment` and `tb_credit_note_detail_comment` follow the canonical comment shape — see [[purchase-request/01-data-model]].

## 6. Workflow / Business Rules

`doc_status`: `draft` → `in_progress` → `completed` (terminal); `cancelled` and `voided` are terminal alternatives.

- **`draft`** — editable; no GL, AP, inventory effect.
- **`in_progress`** — locked except where the active stage permits; approvers from `user_action.execute[]` per [[system-config/workflow]].
- **`completed`** — inventory posting fires for `quantity_return`; cost revaluation for `amount_discount`; AP debit memo for both.
- **`cancelled`** — terminated before completion; no postings.
- **`voided`** — reversal of a `completed` CRN within the open period; reverses every posting.

Stage routing, role mapping, and action gating reuse the **PO-side workflow definition** by default. **GRN anchor:** return lines are bounded by `receipted - already returned` on the lot. **Authorisation:** only users in `user_action.execute[]` may transition.

## 7. Cross-References

- [[purchase-order]] — the PO behind the original GRN; CRN totals roll up into PO open/received reporting.
- [[good-receive-note]] — anchor for every `quantity_return` line.
- [[costing]] — `COST_POST_003` (amount revaluation), `COST_XMOD_006` (lot cost reversal), `COST_CALC_005` (FX revaluation).
- [[master-data/credit-note-reason]] — reason taxonomy.
- [[master-data/exchange-rate]] — dated rate resolution on `cn_date`.
- [[master-data/vendor]] — vendor snapshot and AP debit-memo routing.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (lines 321-397), `tb_credit_note_detail` (lines 434-508), `tb_credit_note_comment` (lines 399-432), `tb_credit_note_detail_comment` (lines 510-543), enums `enum_credit_note_type` and `enum_credit_note_doc_status` (lines 195-206).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/credit-note/`.
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram.
