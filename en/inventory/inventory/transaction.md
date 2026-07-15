---
title: Inventory Transaction Log
description: Append-only ledger of every inventory-affecting event — GRN, SR, adjustment, wastage, count variance, period flip — and the source of truth for balance computation.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, transaction, audit, ledger, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Transaction Log

> **At a Glance**
> **Owner:** System (read-only for users) &nbsp;·&nbsp; **Tables:** `tb_inventory_transaction` (header) + `_detail` + `_cost_layer` &nbsp;·&nbsp; **Trigger:** every source-document posting (`good_received_note` / `store_requisition` / `stock_in` / `stock_out` / `credit_note` / `close` / `open` — count variances arrive as stock-in/stock-out) &nbsp;·&nbsp; **Used by:** balance computation + audit trace &nbsp;·&nbsp; **1-liner:** the immutable event tape; **append-only, never updated, never deleted**.

![Inventory Transaction Log screen](/screenshots/inventory/transaction.png)

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
| Diagnose a balance mismatch | Sum cost-layer `in_qty − out_qty` for the `(location, product)` key | This IS the balance — there is no separate cached balance row; every on-hand figure elsewhere in the product (PR on-hand dialog, spot-check system qty) derives from this same sum |
| Filter the list | Search box + date-range presets (Today / 7d / 30d / This month / custom), Inbound/Outbound direction, Location, Category, and ref-type pills (GRN / SR / SI / SO / PC) | Filters are URL-backed; the backend filter convention is `field:value;field\|op:v1,v2` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Cannot edit transaction" in UI | Ledger is read-only by design — the screen has no create/edit affordance at all | Correct via an opposite-direction source document (credit note, stock-in/stock-out) |
| Balance looks wrong | A source document posted unexpectedly (e.g. GRN **save** already posts — commit does not) | Re-derive from the ledger; the cost-layer sum is the only balance there is |
| Movement dated last month shows in this month's period | By design: `resolveCurrentPeriod` stamps every new movement into the **current open period** regardless of document date — backdated rows are never filed into a closed period (and never rejected for backdating either) | Nothing to fix; closed-period *value* is protected by the credit-note repricing guard, not by a posting block |
| PC ref-type filter returns nothing | The frontend offers a `PC (physical_count)` pill, but `enum_inventory_doc_type` has no `physical_count` value — count corrections arrive as `stock_in` / `stock_out` documents | Filter by SI / SO instead |
| Cost differs from current product cost | `cost_per_unit` snapshot at posting; not re-fetched | Correct by design — except a Credit Note Amount against an open-period lot, which DOES re-price the lot (closed-period lots book a `diff_amount` instead) |

## 4. Edge Cases

- **Append-only.** No `UPDATE` or `DELETE` in normal operation. `deleted_at` is set only for soft-purge, never for "correction".
- **No standalone insert.** Rows are inserted only by source-document workflow transitions — never by user action. The Frontend is read-only.
- **Cost snapshot at posting.** `cost_per_unit` is picked at the moment the source document posts. AVCO uses the running average snapshot; FIFO picks the oldest open lot layer.
- **Lot lineage.** `from_lot_no` and `current_lot_no` capture splits / merges / consumption. FIFO consumption order is enforced via `(lot_at_date, lot_seq_no)` on the cost layer.
- **Period stamp != document date.** Every cost-layer row stamps `period_id` and `at_period` (YYMM) at insert — and the stamp is always the **current open period** (`resolveCurrentPeriod`), never the document date's period. Period aggregation groups by this stamp.
- **Correction = new rows via a source document.** There is no reversal endpoint on the ledger itself; corrections arrive as credit-note or stock-in/stock-out documents which post their own new transactions. `deleted_at` is never set by any current inventory code path.
- **Direct-location receipts are two-legged.** A GRN receipt to a `location_type = direct` location posts the inbound layer **plus** an automatic offsetting `issue` layer (`createDirectExpenseOut`, lot `ISS-…`) under the same header — net on-hand zero.

---

## 5. Data Model (Dev)

Source: tenant schema. Two main tables (header + detail) plus a cost-layer table.

### 5.1 `tb_inventory_transaction` (header)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key. |
| `inventory_doc_type` | `enum_inventory_doc_type` | No | Discriminator: `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`. |
| `inventory_doc_no` | `String @db.Uuid` | No | FK-by-id to the source document of matching type. |
| `doc_version` | `Int` | No | Optimistic-concurrency counter; default `0`. Exposed in GET responses (findOne + findAll) for audit/versioning, but not used for locking — the ledger is append-only with no update endpoint. |
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
| GRN posting (fires on **save**, `draft → saved`) | `good_received_note` | IN (plus an auto `issue` OUT leg when the location is `direct`) |
| SR transfer issue | `transfer_in` + `transfer_out` | OUT @ source, IN @ destination |
| SR issue to direct-cost destination | `issue` | OUT only |
| Inventory-adjustment IN (`tb_stock_in`) | `adjustment_in` | IN |
| Inventory-adjustment / wastage OUT (`tb_stock_out`) | `adjustment_out` | OUT |
| Credit note | `credit_note_quantity` or `credit_note_amount` | OUT (qty) or value-only (`diff_amount`) |
| Period close | `close_period` (lot `CLOSE-{YYMM}-{seq}`, `out_qty` zeroes each surviving lot) | OUT, period boundary |
| Period open (next) | `open_period` (lot `OPEN-{YYMM}-{seq}`, `in_qty` re-creates each lot) | IN, period boundary |
| EOP adjustment (`eop_in` / `eop_out`) | `eop_in` / `eop_out` | carry-in/out variants surfaced through the inventory-adjustment API (`enum_adjustment_type` includes both); carry-in layers are value-locked like `open_period` |

## 6. Lifecycle / Business Rules

```
1. Source-document posting (e.g. GRN save, draft -> saved):
   - INSERT tb_inventory_transaction header
   - INSERT tb_inventory_transaction_detail per line
   - INSERT tb_inventory_transaction_cost_layer per lot_index
     (splitFifoCost may split one receipt into several layers
      for exact decimal reconciliation)
2. Correction: a NEW source document (credit note / stock-in / stock-out)
   posts its own new transaction (NEVER UPDATE the original)
3. Period close: INSERT headers with inventory_doc_type = 'close' and 'open'
```

- **Append-only.** Corrections are new rows via new source documents.
- **Source linkage.** `(inventory_doc_type, inventory_doc_no)` is the back-pointer; the list screen resolves it into `parent_document_no` (GRN/SI/SO/SR/CN number, or the period code for close/open).
- **No backdating into closed periods — by re-dating, not rejection.** Every new row is stamped into the current open period (`resolveCurrentPeriod`); the ledger never receives a closed-period row because the stamp ignores the document date.

## 7. Cross-References

- [inventory](/en/inventory/inventory) — every on-hand figure in the product is the running sum of this ledger (no persisted balance row exists)
- [costing](/en/inventory/costing) — `COST_CALC_*` rules derive from cost-layer rows
- [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/en/inventory/inventory-adjustment) &nbsp;·&nbsp; [inventory-adjustment/wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting) &nbsp;·&nbsp; [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) — source documents
- [inventory/period-end](/en/inventory/inventory/period-end) — writes `close` / `open` rows and freezes the snapshot

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_transaction` (~1048-1073), `tb_inventory_transaction_detail` (~1075-1101), `tb_inventory_transaction_cost_layer` (~1123-1164), `enum_inventory_doc_type` (~208-216), `enum_transaction_type` (~1103-1121).
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/transaction/`.
- **Module landing:** [inventory](/en/inventory/inventory) § 3 (Stock Movement key concept).
