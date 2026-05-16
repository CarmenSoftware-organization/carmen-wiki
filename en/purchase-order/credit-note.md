---
title: Credit Note
description: Vendor-issued credit document reversing all or part of a prior PO / GRN — adjusts AP liability and either cost-revalues the inventory layer or returns goods.
published: true
date: 2026-05-16T17:00:00.000Z
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Credit Note

## 1. Purpose

A **Credit Note (CRN)** is the post-receipt correction instrument in the procure-to-pay chain: when a vendor over-bills, ships defective or short goods, or grants a retrospective discount, the CRN documents the offset against the originating GRN (and, by extension, its PO). The CRN sits *after* `Good Receive Note` has posted — it is the only authoritative way to undo the AP liability and, where goods are physically returned, undo the cost layer that GRN created. Two variants exist:

- **`quantity_return`** — physical return-to-vendor. Consumes inventory cost layers, decrements on-hand, and reverses the AP accrual proportional to the returned quantity.
- **`amount_discount`** — pure price correction or retrospective rebate. No inventory movement; AP liability and the lot's unit cost are revalued by the credit amount.

Reason codes are configured in [[master-data/credit-note-reason]] (`tb_credit_note_reason`); the cost-side effect is owned by the costing engine via `COST_POST_003` (credit-note amount revaluation) and `COST_XMOD_006` (credit-note cost-chain rebuild). FX-bearing CRNs trigger `COST_CALC_005` to re-resolve the rate on the CRN date — see [[master-data/exchange-rate]].

## 2. Prisma Model(s)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`).

### 2.1 `tb_credit_note`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cn_no` | `String? @db.VarChar` | Yes | CRN reference number; unique among non-deleted rows. |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — drives FX rate resolution. |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `in_progress` → `completed` / `cancelled` / `voided`. |
| `credit_note_type` | `enum_credit_note_type` | No | `quantity_return` or `amount_discount`. |
| `vendor_id`, `vendor_name` | `String? @db.Uuid` / `VarChar` | Yes | Snapshot from `tb_vendor` at draft. |
| `grn_id`, `grn_no`, `grn_date` | mixed | Yes | Anchor GRN — required for `quantity_return`, optional for `amount_discount`. |
| `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` | mixed | Yes | Optional pricelist reference if the credit ties back to a quoted price. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Currency snapshot + FX rate resolved on `cn_date`. |
| `cn_reason_id`, `cn_reason_name`, `cn_reason_description` | mixed | Yes | FK + snapshot to `tb_credit_note_reason`. |
| `invoice_no`, `invoice_date`, `tax_invoice_no`, `tax_invoice_date` | mixed | Yes | Vendor's credit-invoice reference for AP matching. |
| `workflow_id`, `workflow_name`, `workflow_history`, `workflow_current_stage`, `workflow_previous_stage`, `workflow_next_stage` | mixed | Yes | Workflow engine state (see Section 3). |
| `user_action` | `Json? @default("{}") @db.JsonB` | Yes | `{ execute: [{ id }] }` — users who may act at the current stage. |
| `last_action`, `last_action_at_date`, `last_action_by_id`, `last_action_by_name` | mixed | Yes | Most recent transition. |
| `note`, `description`, `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([cn_no, deleted_at])` map `creditnote_cn_no_u`; `@@index([cn_no])`. FKs to `tb_vendor`, `tb_currency`, `tb_good_received_note`, `tb_credit_note_reason` — all `onDelete: NoAction` so a CRN survives soft-deletion of any master record.

### 2.2 `tb_credit_note_detail`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `credit_note_id`, `sequence_no` | mixed | No / No / Yes | PK and parent FK; line ordinal (default `1`). |
| `inventory_transaction_id` | `String? @db.Uuid` | Yes | FK to the originating `tb_inventory_transaction` row for `quantity_return`. Null for `amount_discount`. |
| `location_id`, `location_code`, `location_name`, `delivery_point_id`, `delivery_point_name` | mixed | Yes | Where the original receipt landed — return is sourced from the same location. |
| `product_id`, `product_code`, `product_name`, `product_local_name`, `product_sku` | mixed | No / Yes | Product snapshot. |
| `return_qty`, `return_unit_id`, `return_unit_name`, `return_conversion_factor`, `return_base_qty` | `Decimal(20,5)` / mixed | Yes | Return quantity in user-entered unit + converted base-unit value. `0` for `amount_discount`. |
| `price` | `Decimal(20,5)` | Yes | Unit price applied to the credit — typically equals the GRN line price. |
| `tax_profile_id`, `tax_profile_name`, `tax_rate`, `tax_amount`, `base_tax_amount`, `is_tax_adjustment` | mixed | Yes | Tax snapshot + base-currency conversion. |
| `discount_rate`, `discount_amount`, `base_discount_amount`, `is_discount_adjustment` | mixed | Yes | Discount snapshot + base-currency conversion. |
| `extra_cost_amount`, `base_extra_cost_amount` | `Decimal(20,5)` | Yes | Allocated extra-cost adjustment (e.g. freight credit). |
| `sub_total_price`, `net_amount`, `total_price` | `Decimal(20,5)` | Yes | Line money totals in transaction currency. |
| `base_price`, `base_sub_total_price`, `base_net_amount`, `base_total_price` | `Decimal(20,5)` | Yes | Same totals in BU base currency. |
| `info`, `dimension`, `doc_version`, audit | — | Yes | Standard metadata. |

**Constraints:** `@@unique([credit_note_id, sequence_no, deleted_at])` map `creditnotedetail_credit_note_id_sequence_no_u`; `@@index([credit_note_id, sequence_no])`. FKs to `tb_credit_note`, `tb_inventory_transaction`, `tb_product`, `tb_tax_profile`, `tb_location` — all `onDelete: NoAction`.

### 2.3 Comment tables

`tb_credit_note_comment` and `tb_credit_note_detail_comment` mirror the same shape used elsewhere (type, user, message, JSON attachments, audit columns) — see [[purchase-request/01-data-model]] for the canonical comment schema.

## 3. Workflow / Lifecycle

`doc_status` values: `draft` → `in_progress` → `completed` (terminal happy path); `cancelled` and `voided` are terminal alternatives.

- **`draft`** — editable. Header and lines can be added, edited, deleted. No GL, AP, or inventory effect.
- **`in_progress`** — submitted into the workflow. Header is locked except for fields the active stage explicitly permits. Approvers are resolved from `user_action.execute[]` per [[system-config/workflow]].
- **`completed`** — all stages approved. **Inventory posting** fires for `quantity_return`; **cost revaluation** fires for `amount_discount`; **AP debit memo** fires for both. Document is read-only.
- **`cancelled`** — terminated before completion. No postings. Cannot be reactivated.
- **`voided`** — reversal of a `completed` CRN within the open period only. Reverses every posting; the original CRN row is retained for audit.

Stage routing, role mapping, and action gating (approve / reject / send-back) follow the same engine described in [[system-config/workflow]]; the CRN reuses the PO-side workflow definition by default.

## 4. Usage / Cross-References

- [[purchase-order]] — the PO the original GRN was raised against. CRN totals roll up into PO-level open vs received reporting.
- [[good-receive-note]] — the GRN line is the anchor for every `quantity_return` line; `tb_credit_note.grn_id` and `tb_credit_note_detail.inventory_transaction_id` carry the link.
- [[costing]] — `COST_POST_003` (amount-only revaluation), `COST_XMOD_006` (lot-cost reversal on return), `COST_CALC_005` (FX revaluation when the CRN date differs from GRN date).
- [[master-data/credit-note-reason]] — reason taxonomy.
- [[master-data/exchange-rate]] — dated rate resolution on `cn_date`.
- [[master-data/vendor]] — vendor snapshot and downstream AP debit-memo routing.

## 5. Business Rules

- **GRN anchor.** `quantity_return` lines require `grn_id` set and `inventory_transaction_id` on every detail — return quantity is bounded by the receipted-minus-already-returned quantity on that lot.
- **Money rounding.** Line money fields stored at `Decimal(20,5)`; computed totals round half-up to 2 decimals at line level, then sum into header (matches the PO/GRN rounding discipline in [[purchase-order/02-business-rules]]).
- **Tax handling.** Tax recalculates on the CRN line at the tax profile's *current* rate unless `is_tax_adjustment = true`, which freezes the rate from the GRN snapshot (used for retrospective tax corrections that must preserve the original rate).
- **Return-to-stock vs write-off.** `quantity_return` decrements on-hand inventory and reverses the cost layer in FIFO order. If the original lot has already been consumed (issued via SR or stock-out), the cost engine writes the variance to a configured **inventory write-off** GL account rather than negative inventory — see [[costing]] `COST_XMOD_006`.
- **FX revaluation.** When `cn_date != grn_date` and currencies differ from BU base, the engine resolves a fresh rate on `cn_date` and posts the delta to FX gain/loss per `COST_CALC_005`.
- **AP posting.** `completed` always emits a debit memo against the vendor's AP balance — even for `quantity_return`, where the posting amount equals `base_total_price` summed across lines.
- **Authorization.** Only users present in the active stage's `user_action.execute[]` may transition the CRN. Stage configuration determines per-stage edit scope (header-only, lines-only, etc.).
- **Snapshot semantics.** Vendor name, product info, currency code, exchange rate, tax rate, and pricelist references are all snapshotted on draft creation. Changes to master records do not retroactively edit the CRN — re-snapshot is an explicit action.
- **Voiding window.** A `completed` CRN may only be voided while its posting period is open. Once the period closes (`tb_period.status = closed`), voiding is rejected — finance must raise a corrective journal voucher instead.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (lines 321-397), `tb_credit_note_detail` (lines 434-508), `tb_credit_note_comment` (lines 399-432), `tb_credit_note_detail_comment` (lines 510-543), enums `enum_credit_note_type` and `enum_credit_note_doc_status` (lines 195-206).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/credit-note/`.
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram.
- **Cross-module:** see Section 4.
