---
title: Inventory Transaction Log
description: Append-only ledger of every inventory-affecting event — GRN, SR, adjustment, wastage, count variance, period flip — and the source of truth for balance computation.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, transaction, audit, ledger, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Transaction Log

> **At a Glance**
> **Owner:** System (read-only for users) &nbsp;·&nbsp; **Tables:** `tb_inventory_transaction` (header) + `_detail` + `_cost_layer` &nbsp;·&nbsp; ***Trigger:** every source-document posting (`good_received_note` / `store_requisition` / `stock_in` / `stock_out` / `credit_note` / `close` / `open`); count variances create stock-in/stock-out **rows** but those rows are not posted to the ledger (see [physical-count](/en/inventory/physical-count)) &nbsp;·&nbsp; **Used by:** balance computation + audit trace &nbsp;·&nbsp; **1-liner:** the immutable event tape; **append-only, never updated, never deleted**.

![Inventory Transaction Log screen](/screenshots/inventory/transaction.png)

## 1. What & Who

The Inventory Transaction Log is the **immutable event tape** of every quantity movement at every location. Each row is one event together with the affected `(product, location, lot, qty, unit-cost)` picked at posting time. **Rows are NEVER updated and NEVER deleted** — a correction is a new opposite-sign row, never a mutation of the old one.

- **Testers / Support / Finance** — read the timeline at `/inventory-management/transaction` to trace any balance back to its source document
- **Cost Engine** — uses the `_cost_layer` rows for AVCO / FIFO consumption
- **Period Close** — `GROUP BY` over the cost layers becomes `tb_inventory_period_snapshot` (average-method tenants)
- **Document screens** — GRN / SI / SO / CN detail pages call `GET …/{id}/stock-movements` (`buildStockMovements`, `stock-movement.helper.ts`, 2026-09-17) to show the ledger lines this document wrote, and the product cell opens the **stock panel dialog** (`components/share/inventory-dialog.tsx`, `useProductInventory` → `PRODUCT_INVENTORY` endpoint) listing lots and movements

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
| Balance looks wrong | A source document posted at a different event than expected — GRN posts on **save** for average-method BUs and on **commit** for FIFO BUs (`postsInventoryAtSave`, `good-received-note.ledger.ts`); a stock-in / stock-out posts only on `PATCH …/commit`, never on create | Re-derive from the ledger; the cost-layer sum is the only balance there is |
| Movement dated last month is rejected / lands in an unexpected period | Since 2026-08-31 the period stamp comes from the **document date**: GRN and stock-in resolve `findOpenPeriodForDate(doc_date)` and fail if no open/locked period covers it (`STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD`, 422; GRN throws `No open period covers …`); stock-out must be dated inside the **current** period (`STOCK_OUT_DATE_NOT_CURRENT_PERIOD`, 422, message names the period and its date range); SR issues/transfers use `resolveDocumentPeriod` — the document date's open period, falling back to the current period; movements without a document date (void reversals, CN) still use `resolveCurrentPeriod` | Re-date the document into an open period; closed-period *value* is additionally protected by the credit-note repricing guard |
| PC ref-type filter returns nothing | The frontend offers a `PC (physical_count)` pill, but `enum_inventory_doc_type` has no `physical_count` value — count corrections arrive as `stock_in` / `stock_out` documents | Filter by SI / SO instead |
| Cost differs from current product cost | `cost_per_unit` snapshot at posting; not re-fetched | Correct by design — except a Credit Note Amount against an open-period lot, which DOES re-price the lot (closed-period lots book a `diff_amount` instead) |
| Stock-out commit fails with `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` | `STOCK_OUT_INSUFFICIENT_STOCK` (400) — `StockOutService.commit` pre-checks every line against `getOnHandQty` before touching the ledger; the ledger's own guard (`Insufficient stock. Requested: …, Available: …`) is the second line of defence | Reduce the quantity or receive stock first |

## 4. Edge Cases

- **Append-only.** No `UPDATE` or `DELETE` in normal operation. `deleted_at` is set only for soft-purge, never for "correction".
- **No standalone insert.** Rows are inserted only by source-document workflow transitions — never by user action. The Frontend is read-only.
- **Cost snapshot at posting.** `cost_per_unit` is picked at the moment the source document posts. AVCO uses the running average snapshot; FIFO picks the oldest open lot layer.
- **Lot lineage.** `from_lot_no` and `current_lot_no` capture splits / merges / consumption. FIFO consumption order is enforced via `(lot_at_date, lot_seq_no)` on the cost layer.
- **Period stamp = document date's period (since 2026-08-31).** Every cost-layer row stamps `period_id` and `at_period` (YYMM) at insert; GRN receipts and stock-in layers take the open period covering `grn_date` / `si_date` (`resolvePeriodForDate`, throws if none), SR consumption/transfers take the document date's period with a fallback to the current period (`resolveDocumentPeriod`), and movements without a document date use `resolveCurrentPeriod`. Period aggregation and the close's lot sweep group by this stamp.
- **Correction = new rows via a source document.** There is no reversal endpoint on the ledger itself; corrections arrive as credit-note or stock-in/stock-out documents which post their own new transactions. `deleted_at` is never set by any current inventory code path.
- **Direct-location receipts are two-legged.** A GRN receipt to a `location_type = direct` location posts the inbound layer **plus** an automatic offsetting `issue` layer (`createDirectExpenseOut`) under the same header — net on-hand zero.
- **One lot format everywhere.** Every layer's `lot_no` is `buildLotNo({ locationCode, atPeriod, seqNo })` → `{location_code}{YYMM}{seq4}` (e.g. `MK26090007`), with `lot_seq_no` running per `at_period`; receipts, issues, adjustments, credit-note re-pricing pairs and the close/open carry-over all share it (`common/helpers/lot-number.helper.ts`, 2026-07-30).
- **Stock-in lines carry `expired_at`.** `tb_stock_in_detail.expired_at` (migration `20260731120000_add_inflow_price_expiry`) is captured per line and drives the near-expiry list in [wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting); the ledger itself has no expiry column.

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
| `good_received_note_detail_item_id` | `String @db.Uuid?` | Yes | Back-pointer to the GRN line that received this lot (migration `20260810160000_add_grn_item_inventory_transaction_detail`); lets wastage reporting and the GRN stock-movement view walk from a receipt line to its lot. |
| `qty` | `Decimal(20,5)?` | Yes | Signed; positive = increase, negative = decrease. |
| `cost_per_unit`, `total_cost` | `Decimal(20,5)?` | Yes | Cost snapshot at posting time. |
| Audit columns | — | Yes | `created_*`, `updated_*`. **No soft-delete on detail rows.** |

### 5.3 `tb_inventory_transaction_cost_layer`

Per-lot FIFO layer with `lot_no`, `lot_index`, `in_qty` / `out_qty`, `cost_per_unit`, `extra_cost_amount` (GRN extra cost apportioned into landed cost, migration `20260910130000_add_cost_layer_extra_cost`), `diff_amount`, `average_cost_per_unit`, `period_id → tb_inventory_period`, `at_period`, and `transaction_type` (`enum_transaction_type`: `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`). `@@unique([lot_no, lot_index])`. Drives FIFO consumption order at issue time.

### 5.4 Event-type matrix

| Source doc | Cost-layer type | Direction |
|---|---|---|
| GRN posting (average BU: on **save**, re-posted when quantities change; FIFO BU: on **commit**) | `good_received_note` | IN (plus an auto `issue` OUT leg when the location is `direct`); FOC lines enter stock at zero cost and extra cost lands in `extra_cost_amount` (2026-09-10) |
| SR transfer issue | `transfer_in` + `transfer_out` | OUT @ source, IN @ destination |
| SR issue to direct-cost destination | `issue` | OUT only |
| Inventory-adjustment IN (`tb_stock_in`, on `PATCH /commit`; also the reversal leg of a stock-out void) | `adjustment_in` | IN |
| Inventory-adjustment / wastage write-off OUT (`tb_stock_out`, on `PATCH /commit` or `POST /wastage-reporting`; also the reversal leg of a stock-in void) | `adjustment_out` | OUT |
| Physical-count variance (`tb_stock_in` / `tb_stock_out` rows written `completed` by `PhysicalCountService.submit`) | — | **No ledger row** — `submit()` never calls `executeAdjustmentIn/Out` (grep of `physical-count/*.ts` for `inventoryTransactionService` returns nothing); see [physical-count](/en/inventory/physical-count) |
| Credit note | `credit_note_quantity` or `credit_note_amount` | OUT (qty) or value-only (`diff_amount`) |
| Period close | `close_period` (new lot in the closing period, `out_qty` zeroes each surviving lot, `parent_lot_no` = the old lot) | OUT, period boundary |
| Period open (next) | `open_period` (new lot in the next period, `in_qty` re-creates each lot) | IN, period boundary |
| EOP adjustment (`eop_in` / `eop_out`) | `eop_in` / `eop_out` | carry-in/out variants surfaced through the inventory-adjustment API (`enum_adjustment_type` includes both); carry-in layers are value-locked like `open_period` |

## 6. Lifecycle / Business Rules

```
1. Source-document posting (e.g. GRN save on an average BU / commit on FIFO,
   stock-in or stock-out PATCH /commit, SR final approval):
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
- **No backdating into closed periods — by rejection at the source document.** GRN / SI / SO dates must fall inside an open (SI, GRN) or the current (SO) period before they can post; the ledger resolves `at_period` from that date, so a closed period never receives a row.

## 7. Cross-References

- [inventory](/en/inventory/inventory) — every on-hand figure in the product is the running sum of this ledger (no persisted balance row exists)
- [costing](/en/inventory/costing) — `COST_CALC_*` rules derive from cost-layer rows
- [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/en/inventory/inventory-adjustment) &nbsp;·&nbsp; [inventory-adjustment/wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting) &nbsp;·&nbsp; [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) — source documents
- [inventory/period-end](/en/inventory/inventory/period-end) — writes `close` / `open` rows and freezes the snapshot

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_transaction`, `tb_inventory_transaction_detail`, `tb_inventory_transaction_cost_layer`, `enum_inventory_doc_type` (~219), `enum_transaction_type`; migrations `20260810160000_add_grn_item_inventory_transaction_detail`, `20260910130000_add_cost_layer_extra_cost`, `20260916141000_rename_tb_period_to_tb_inventory_period`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (`resolvePeriodForDate` / `resolveDocumentPeriod` / `resolveCurrentPeriod`, `executeAdjustmentIn/Out`, `createDirectExpenseOut`), `.../inventory-period.helper.ts`, `.../stock-movement.helper.ts`, `apps/micro-business/src/common/helpers/lot-number.helper.ts` (`buildLotNo`); gateway `apps/backend-gateway/src/application/inventory-transactions/` (`GET /`, `/cost-layers`, `/stock-balance`, `/locations`, `/products`, `/locations/:id/products`, `/calculation-method`). Bruno: `inventory/inventory-transaction/*`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/transaction/` (`transaction-component.tsx`, `use-transaction-table.tsx`, `transaction-summary.tsx`, `use-transaction.ts`), `components/share/inventory-dialog.tsx` + `inventory-detail-tables.tsx` (stock panel with lots + movements), `hooks/use-product-inventory.ts`.
- **E2E:** no spec exercises this screen; manual catalog `../carmen-inventory-frontend-e2e/docs/test-cases/740-stock-transaction.md` (38 cases, re-verified 2026-09-20 — confirms the ledger is read-only with no row click).
- **Module landing:** [inventory](/en/inventory/inventory) § 3 (Stock Movement key concept).
