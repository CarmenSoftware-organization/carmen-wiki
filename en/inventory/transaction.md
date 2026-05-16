---
title: Inventory Transaction Log
description: Append-only ledger of every inventory-affecting event — GRN, SR, adjustment, wastage, count variance, period flip — and the source of truth for balance computation.
published: true
date: 2026-05-17T08:00:00.000Z
tags: inventory, transaction, audit, ledger, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Transaction Log

> **At a Glance**
> **Owner:** System (read-only for users) &nbsp;·&nbsp; **Tables:** `tb_inventory_transaction` (header) + `_detail` + `_cost_layer` &nbsp;·&nbsp; **Trigger:** every source-document posting (GRN / SR / adjustment / wastage / count / close) &nbsp;·&nbsp; **Used by:** balance computation + audit trace &nbsp;·&nbsp; **1-liner:** the immutable event tape; **append-only, never updated, never deleted**.

## 1. What & Who

The Inventory Transaction Log is the **immutable event tape** of every quantity movement at every location. Each row is one event together with the affected `(product, location, lot, qty, unit-cost)` picked at posting time. **Rows are NEVER updated and NEVER deleted** — a correction is a new opposite-sign row, never a mutation of the old one.

- **Testers / Support / Finance** — read the timeline at `/inventory-management/transaction` to trace any balance back to its source document
- **Cost Engine** — uses the `_cost_layer` rows for AVCO / FIFO consumption
- **Period Close** — `GROUP BY` over the cost layers becomes `tb_period_snapshot`

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Find a movement by source-document reference | Transaction Log → filter by `inventory_doc_no` | Composite index `(inventory_doc_type, inventory_doc_no)` makes this one-query |
| See cost-layer impact of a posting | Open detail → Cost Layer tab | Shows `lot_no`, `lot_index`, `in_qty` / `out_qty`, `cost_per_unit`, `average_cost_per_unit` |
| Verify a GRN posting wrote to the ledger | Filter `inventory_doc_type = 'good_received_note'` and the GRN id | One header row + one detail row per GRN line + one cost-layer row per lot |
| Trace an SR transfer (two sides) | Filter by SR id | Pair of OUT @ source (`transfer_out`) and IN @ destination (`transfer_in`) |
| Audit a period close | Filter `inventory_doc_type IN ('close', 'open')` | The close itself appears on the ledger |
| Diagnose a balance mismatch | Sum `qty` for the `(location, product, lot)` key | Must equal the cached `InventoryStatus.QuantityOnHand` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Cannot edit transaction" in UI | Ledger is read-only by design | Correct via opposite-sign source document (void / reverse) |
| Balance disagrees with InventoryStatus cache | Cache stale or corrupted | Re-derive from ledger (system maintenance job); ledger is source of truth |
| "Period is closed" on source-document submit | `document_date` inside a `closed` / `locked` period | The ledger NEVER receives a row whose period is closed — fix at source |
| Two transaction rows for one GRN | Original + reversal pair | Expected for void / reverse — the pair IS the audit trail |
| Cost differs from current product cost | `cost_per_unit` snapshot at posting; not re-fetched | Correct by design; re-approving a doc does NOT re-cost an existing transaction |

## 4. Edge Cases

- **Append-only.** No `UPDATE` or `DELETE` in normal operation. `deleted_at` is set only for soft-purge, never for "correction".
- **No standalone insert.** Rows are inserted only by source-document workflow transitions — never by user action. The Frontend is read-only.
- **Cost snapshot at posting.** `cost_per_unit` is picked at the moment the source document posts. AVCO uses the running average snapshot; FIFO picks the oldest open lot layer.
- **Lot lineage.** `from_lot_no` and `current_lot_no` capture splits / merges / consumption. FIFO consumption order is enforced via `(lot_at_date, lot_seq_no)` on the cost layer.
- **Period stamp != document date.** Every cost-layer row stamps `period_id` and `at_period` (YYMM) at insert; `tb_period_snapshot` groups by THIS stamp, not by document date.
- **Void = new row.** A reversal inserts a new transaction with negative qty linked back to the original by application-layer reference; the original row never changes.

---

## 5. Data Model (Dev)

Source: tenant schema. Two main tables (header + detail) plus a cost-layer table.

### 5.1 `tb_inventory_transaction` (header)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_doc_type` | `enum_inventory_doc_type` | No | Discriminator: `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`. |
| `inventory_doc_no` | `String @db.Uuid` | No | FK-by-id to the source document of matching type. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` (deleted only for soft-purge). |

**Indexes:** on `inventory_doc_no`, on `inventory_doc_type`, composite `(inventory_doc_type, inventory_doc_no)`.

### 5.2 `tb_inventory_transaction_detail` (lines)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_transaction_id` | `String @db.Uuid` | No | FK to header. |
| `from_lot_no` / `current_lot_no` | `String?` | Yes | Lot before / after this event. |
| `location_id`, `location_code` | `String?` | Yes | Affected location. |
| `product_id` | `String @db.Uuid` | No | Affected product. |
| `qty` | `Decimal(20,5)?` | Yes | Signed; positive = increase, negative = decrease. |
| `cost_per_unit`, `total_cost` | `Decimal(20,5)?` | Yes | Cost snapshot at posting time. |
| Audit columns | — | Yes | `created_*`, `updated_*`. **No soft-delete on detail rows.** |

### 5.3 `tb_inventory_transaction_cost_layer`

Per-lot FIFO layer with `lot_no`, `lot_index`, `in_qty` / `out_qty`, `cost_per_unit`, `average_cost_per_unit`, `period_id`, `at_period`, and `transaction_type` (`enum_transaction_type`: `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`). `@@unique([lot_no, lot_index])`. Drives FIFO consumption order at issue time.

### 5.4 Event-type matrix

| Source doc | Cost-layer type | Direction |
|---|---|---|
| GRN posting | `good_received_note` | IN |
| SR transfer issue | `transfer_in` + `transfer_out` | OUT @ source, IN @ destination |
| SR issue to direct-cost | `issue` | OUT only |
| Inventory-adjustment IN | `adjustment_in` | IN |
| Inventory-adjustment / wastage OUT | `adjustment_out` | OUT |
| Credit note | `credit_note_quantity` or `credit_note_amount` | OUT (qty) or value-only |
| Period close | `eop_out` + `close_period` | period marker |
| Period open (next) | `eop_in` + `open_period` | period marker |

## 6. Lifecycle / Business Rules

```
1. Source-document posting (e.g. GRN draft -> completed):
   - INSERT tb_inventory_transaction header
   - INSERT tb_inventory_transaction_detail per line
   - INSERT tb_inventory_transaction_cost_layer per affected lot
2. Void / reverse: INSERT new rows with negative qty (NEVER UPDATE the original)
3. Period close: INSERT header with inventory_doc_type = 'close'
```

- **Append-only.** Corrections are new rows with opposite-sign qty.
- **Source linkage.** `(inventory_doc_type, inventory_doc_no)` is the back-pointer.
- **No backdating.** Posting into a closed period is rejected at source; the ledger never receives a closed-period row.

## 7. Cross-References

- [[inventory]] — current-state view (`InventoryStatus`) is the running sum of this ledger
- [[costing]] — `COST_CALC_*` rules derive from cost-layer rows
- [[good-receive-note]] &nbsp;·&nbsp; [[inventory-adjustment]] &nbsp;·&nbsp; [[inventory-adjustment/wastage-reporting]] &nbsp;·&nbsp; [[store-requisition]] &nbsp;·&nbsp; [[physical-count]] &nbsp;·&nbsp; [[credit-note]] — source documents
- [[inventory/period-end]] — writes `close` / `open` rows and freezes the snapshot

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_transaction` (~1048-1073), `tb_inventory_transaction_detail` (~1075-1101), `tb_inventory_transaction_cost_layer` (~1123-1164), `enum_inventory_doc_type` (~208-216), `enum_transaction_type` (~1103-1121).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/inventory-management/transaction/`.
- **Module landing:** [[inventory]] § 3 (Stock Movement key concept).
