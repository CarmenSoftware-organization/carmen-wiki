---
title: Wastage Reporting
description: Specialised stock-out flavour for spoilage, breakage, expiry, and theft — categorised so finance can analyse loss patterns by reason, outlet, and period.
published: true
date: 2026-05-16T17:00:00.000Z
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Wastage Reporting

## 1. Purpose

Wastage Reporting is a **variant of [[inventory-adjustment]]** dedicated to recording stock that disappeared without a sale: spoilage, breakage, expiry, theft, sample / staff consumption, and other-loss categories. It is not a separate document type at the schema level — every wastage entry is a `tb_stock_out` row whose `adjustment_type_id` resolves to a wastage-flavoured reason on `tb_adjustment_type`. The variant exists because finance needs loss broken out by reason category for cost-control reporting; lumping wastage into the generic adjustment pile makes the "% loss of revenue per outlet per period" analysis impossible.

Scope differs from a generic adjustment in three ways:
1. **OUT only** — there is no "return-to-stock" wastage; the document type is `tb_stock_out` with no `tb_stock_in` counterpart.
2. **Reason is mandatory** — a wastage record without a recognised reason category is rejected at submit.
3. **Cost lands on a loss / expense account** — the GL mapping pulled from `tb_adjustment_type` points at a wastage expense GL, not a generic inventory-adjustment expense.

## 2. Prisma Model(s)

Wastage shares schema with stock-out. The discriminator is `adjustment_type_id`.

### 2.1 `tb_stock_out` (host table)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `so_no` | `String? @db.VarChar` | Yes | Document number (e.g. `WR-2026-0001` when issued from the wastage screen). |
| `so_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — gated against `tb_period`. |
| `adjustment_type_id` | `String? @db.Uuid` | Yes | FK to `tb_adjustment_type` — must resolve to a wastage-flavoured row. |
| `adjustment_type_code` | `String? @db.VarChar` | Yes | Denormalised code (`SPOIL`, `BREAK`, `EXPIRY`, `THEFT`, `SAMPLE`, etc.). |
| `doc_status` | `enum_doc_status` | No | `draft`, `in_progress`, `completed`, `cancelled`, `voided`. |
| `location_id` / `location_code` / `location_name` | `String?` | Yes | Location whose balance is decremented. |
| `workflow_*` / `last_action_*` columns | mixed | Yes | Workflow stage, history, audit. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([so_no, deleted_at])`. Reverse relations to `tb_stock_out_detail`, `tb_stock_out_comment`.

### 2.2 `tb_stock_out_detail` (line items)

Carries `product_id`, `qty`, `cost_per_unit`, `total_cost`, lot reference, and a back-pointer `inventory_transaction_id` set at post time. `@@unique([stock_out_id, product_id, dimension, deleted_at])`.

### 2.3 `tb_adjustment_type` (reason catalogue)

| Field | Prisma Type | Description |
| --- | --- | --- |
| `code`, `name` | `String` | e.g. `SPOIL` / "Spoilage". |
| `type` | `enum_adjustment_type` | `STOCK_IN` or `STOCK_OUT` — wastage rows are always `STOCK_OUT`. |
| `is_active` | `Boolean?` | Toggles availability in the picker. |

See [[master-data/adjustment-type]] for the full reason catalogue.

## 3. Workflow / Lifecycle

```
1. Store Keeper opens Wastage Reporting / new, selects location and reason category
   - Filters tb_adjustment_type to rows where type = 'STOCK_OUT' and is wastage-flavoured
2. Adds line items: product, qty, lot (if lot-tracked)
   - cost_per_unit is computed at submit from active costing method (AVCO snapshot or oldest FIFO layer)
3. Attaches evidence (photo of broken bottles, expiry-label photos) via tb_stock_out_comment
4. Submits -> doc_status flips draft -> in_progress, workflow routes to Inventory Controller
5. Inventory Controller approves -> doc_status flips in_progress -> completed:
   - INSERT tb_inventory_transaction { inventory_doc_type: 'stock_out', inventory_doc_no = stock_out.id }
   - INSERT tb_inventory_transaction_detail per line
   - INSERT tb_inventory_transaction_cost_layer with transaction_type = 'adjustment_out'
   - On-hand at the location decremented
   - GL journal: DR Wastage Expense (from adjustment_type GL mapping), CR Inventory
6. Reversal (optional): the only correction path. A new tb_stock_out with negative qty,
   linked via tb_stock_out.note to the original. The original is never UPDATEd.
```

Compared to a generic [[inventory-adjustment]]: same lifecycle, same posting mechanics, narrower reason filter, and a distinct GL account on the credit side of the journal.

## 4. Usage / Cross-References

- [[inventory-adjustment]] — parent module; same business rules apply
- [[master-data/adjustment-type]] — reason catalogue (`SPOIL`, `BREAK`, `EXPIRY`, `THEFT`, `SAMPLE`, `OTHER`)
- [[inventory]] — on-hand decrement
- [[inventory/transaction]] — the posting writes a `stock_out` ledger row
- [[costing]] — cost-layer consumption follows FIFO / AVCO per the location's method
- [[reporting-audit]] — wastage-by-reason analytics for F&B Controller

## 5. Business Rules

- **Reason required.** `adjustment_type_id` is non-null at submit; the picker rejects "generic" adjustment reasons that are not flagged as wastage in `tb_adjustment_type`.
- **Direction.** Always `STOCK_OUT`. Attempts to use a `STOCK_IN` reason on this surface are blocked.
- **Evidence.** A photo / damage report attachment is enforced for high-loss reason codes (theft, expiry) — application-layer rule, captured on `tb_stock_out_comment`.
- **Cost basis.** `cost_per_unit` is snapshot at submit from the active costing method; not editable by the user.
- **Period gate.** `so_date` inside a closed period is rejected.
- **Lot validity.** For lot-tracked products, the lot must exist with positive balance at the source location at submit time.
- **No edit after post.** Once `doc_status = completed`, no field is mutable. Correction is a new opposite-sign wastage row referencing the original in `note`.
- **Authorization.** Submit and approve must be distinct users (segregation of duties).
- **Reporting flag.** Each wastage posting contributes to the per-outlet, per-period, per-reason loss aggregation read by the F&B Controller's dashboard.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_stock_out` (lines ~2759-2812), `tb_stock_out_detail` (lines ~2848-2886), `tb_adjustment_type` (lines ~2569-2594), `enum_adjustment_type` (lines ~2564-2567), `enum_doc_status` (lines ~187-193).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/store-operation/wastage-reporting/` — `wr-form.tsx`, `wr-form-schema.ts`, `wr-item-fields.tsx`.
- **carmen/docs:** parent under `../carmen/docs/inventory-management/` (period-end-process references wastage as a pre-close prerequisite).
- **Cross-module:** see Section 4.
