---
title: Inventory Transaction Log
description: Append-only ledger of every inventory-affecting event — GRN, SR, adjustment, wastage, count variance, period flip — and the source of truth for balance computation.
published: true
date: 2026-05-16T17:00:00.000Z
tags: inventory, transaction, audit, ledger, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Transaction Log

## 1. Purpose

The Inventory Transaction Log is the **immutable event tape** of every quantity movement at every location. Each row is one event ("a GRN line posted", "an SR was issued", "an adjustment was posted", "the period closed") together with the affected product / location / lot / qty / unit-cost picked at posting time. Rows are **never updated and never deleted**; a correction is a new row, never a mutation of the old one.

Two consumers depend on this:

1. **Balance computation.** On-hand quantity at any `(location, product, lot)` is the sum of `qty` across all transaction-detail rows for that key. The current-state view (`InventoryStatus`) is a materialised cache; the ledger is the source of truth.
2. **Audit and diagnostics.** Testers and finance staff trace any balance back through the ledger to the source document (GRN, SR, adjustment, count, close) to verify what happened and in what order.

The Frontend surfaces this as a filterable timeline at `/inventory-management/transaction`. The ledger is read-only in the UI.

## 2. Prisma Model(s)

Source: tenant schema. Two tables (header + detail) plus a cost-layer table that hangs off the detail.

### 2.1 `tb_inventory_transaction`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_doc_type` | `enum_inventory_doc_type` | No | Discriminator: `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`. |
| `inventory_doc_no` | `String @db.Uuid` | No | FK-by-id to the source document of the matching type (e.g. `tb_good_received_note.id` when `inventory_doc_type = 'good_received_note'`). |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` (deleted is set only for soft-purge; never for "correction"). |

**Indexes:** on `inventory_doc_no`, on `inventory_doc_type`, and a composite `(inventory_doc_type, inventory_doc_no)`. Reverse relations to `tb_inventory_transaction_detail`, `tb_stock_in_detail`, `tb_stock_out_detail`, `tb_store_requisition_detail`, `tb_credit_note_detail`.

### 2.2 `tb_inventory_transaction_detail`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | No | FK to header. |
| `from_lot_no` / `current_lot_no` | `String?` | Yes | Lot before / after this event (used on consumption / merge). |
| `location_id`, `location_code` | `String?` | Yes | Affected location. |
| `product_id` | `String @db.Uuid` | No | Affected product. |
| `qty` | `Decimal(20,5)?` | Yes | Signed qty; positive = increase, negative = decrease (default 0). |
| `cost_per_unit`, `total_cost` | `Decimal(20,5)?` | Yes | Unit cost picked at posting time per the active costing method (AVCO or FIFO). |
| Audit columns | — | Yes | `created_*`, `updated_*`. No soft-delete on detail rows. |

### 2.3 `tb_inventory_transaction_cost_layer`

Per-lot FIFO layer with `lot_no`, `lot_index`, `in_qty` / `out_qty`, `cost_per_unit`, `average_cost_per_unit`, `period_id`, and `transaction_type` (`enum_transaction_type`: `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`). `@@unique([lot_no, lot_index])`. Drives FIFO consumption order at issue time.

## 3. Algorithm / Append-Only Semantics

```
1. Source-document posting transition (e.g. GRN draft -> completed):
   - INSERT tb_inventory_transaction { inventory_doc_type, inventory_doc_no }
   - For each line: INSERT tb_inventory_transaction_detail
   - For each affected lot: INSERT tb_inventory_transaction_cost_layer

2. Void / reverse:
   - Never UPDATE original rows
   - INSERT new rows with negative qty; the pair is the audit trail

3. Period close: INSERT tb_inventory_transaction { inventory_doc_type: 'close' }
   so the close itself is on the ledger (see [[inventory/period-end]])
```

Event-type matrix (mapped from `enum_inventory_doc_type` × `enum_transaction_type`):

| Event | Source | Direction |
| --- | --- | --- |
| `good_received_note` / `good_received_note` | GRN posting | IN |
| `store_requisition` / `transfer_in` + `transfer_out` | SR transfer issue | OUT @ source, IN @ destination |
| `store_requisition` / `issue` | SR issue to direct-cost | OUT only |
| `stock_in` / `adjustment_in` | inventory-adjustment IN | IN |
| `stock_out` / `adjustment_out` | inventory-adjustment / wastage OUT | OUT |
| `credit_note` / `credit_note_quantity` or `credit_note_amount` | credit-note posting | OUT (qty) or value-only |
| `close` / `eop_out` + `close_period` | period-end close | period marker |
| `open` / `eop_in` + `open_period` | period-end open of next | period marker |

## 4. Usage / Cross-References

- [[inventory]] — current-state view (`InventoryStatus`) is the running sum of this ledger
- [[costing]] — cost-layer picks at posting are recorded here; `COST_CALC_*` rules derive from these rows
- [[good-receive-note]], [[inventory-adjustment]], [[inventory-adjustment/wastage-reporting]], [[store-requisition]], [[physical-count]], [[credit-note]] — source documents whose posting writes here
- [[inventory/period-end]] — period close writes `close` / `open` rows here and freezes the snapshot

## 5. Business Rules

- **Append-only.** No `UPDATE` or `DELETE` of header or detail rows in normal operation. Corrections are new rows with opposite-sign qty.
- **No standalone insert.** Rows are never inserted by user action — only by source-document workflow transitions. The Frontend is read-only.
- **Cost-snapshot at posting.** `cost_per_unit` is picked at the moment the source document posts, per the active costing method (AVCO snapshot, or oldest FIFO layer). Re-approving a document does NOT re-cost an existing transaction.
- **Source linkage.** `(inventory_doc_type, inventory_doc_no)` is the back-pointer; the indexed composite makes "show every event for GRN X" a one-query lookup.
- **Period stamp.** Every cost-layer row stamps `period_id` and `at_period` (YYMM) at insert. The stamp is what `tb_period_snapshot` groups by — not document date.
- **Lot tracking.** `from_lot_no` and `current_lot_no` capture the lot lineage (split, merge, consumption). FIFO consumption order is enforced via `(lot_at_date, lot_seq_no)` on the cost layer.
- **No backdating.** Posting into a closed period is rejected at the source document; the ledger never receives a row whose period is `closed` / `locked`.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_transaction` (lines ~1048-1073), `tb_inventory_transaction_detail` (lines ~1075-1101), `tb_inventory_transaction_cost_layer` (lines ~1123-1164), `enum_inventory_doc_type` (lines ~208-216), `enum_transaction_type` (lines ~1103-1121).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/inventory-management/transaction/`.
- **Module landing:** [[inventory]] § 3 (Stock Movement key concept).
- **Cross-module:** see Section 4.
