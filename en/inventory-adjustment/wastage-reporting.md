---
title: Wastage Reporting
description: Specialised stock-out flavour for spoilage, breakage, expiry, and theft — categorised so finance can analyse loss patterns by reason, outlet, and period.
published: true
date: 2026-05-17T08:00:00.000Z
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Wastage Reporting

> **At a Glance**
> **Owner:** Store Keeper (submit) &nbsp;·&nbsp; Inventory Controller (approve) &nbsp;·&nbsp; **Table:** `tb_stock_out` with `adjustment_type = 'wastage'` flavour (NOT a separate table) &nbsp;·&nbsp; **Trigger:** spoilage / breakage / expiry / theft / sample &nbsp;·&nbsp; **Writes to:** ledger as `stock_out` / `adjustment_out` &nbsp;·&nbsp; **1-liner:** OUT-only variant of [[inventory-adjustment]] with mandatory reason and wastage GL account.

## 1. What & Who

Wastage Reporting is a **variant of [[inventory-adjustment]]** for stock that disappeared without a sale: spoilage, breakage, expiry, theft, sample / staff consumption, other-loss. **It is not a separate document type** — every wastage entry is a `tb_stock_out` row whose `adjustment_type_id` resolves to a wastage-flavoured reason. The variant exists so finance can break out loss by reason for cost-control reporting.

How it differs from a generic adjustment:

- **OUT only** — no return-to-stock counterpart
- **Reason mandatory** — submit rejected without a recognised wastage reason
- **Loss / expense GL** — credit side maps to a wastage expense account, not generic adjustment

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Record a wastage entry | Store Operation → Wastage Reporting → **New** | Pick location, reason, product, qty, lot |
| Pick a reason code | Reason field on header | Filters `tb_adjustment_type` to `STOCK_OUT` wastage-flavoured rows: `SPOIL`, `BREAK`, `EXPIRY`, `THEFT`, `SAMPLE`, `OTHER` |
| Attach evidence | Comments tab on the document | Photos of broken bottles / expiry labels (mandatory for high-loss reason codes) |
| Submit for approval | **Submit** action | Flips `draft → in_progress`, routes to Inventory Controller |
| Approve and post | Inventory Controller → **Approve** | Posts `tb_inventory_transaction` (stock_out / adjustment_out), debits Wastage Expense, credits Inventory |
| Reverse a wastage entry | New wastage with negative qty | Only correction path — never edit the original; reference original in `note` |
| Run loss-by-reason report | [[reporting-audit]] | Per-outlet, per-period, per-reason aggregation |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Reason required" | `adjustment_type_id` null at submit | Pick a wastage reason from the catalogue |
| "Invalid reason for this surface" | A `STOCK_IN` or non-wastage `STOCK_OUT` reason chosen | Pick a wastage-flavoured `STOCK_OUT` reason only |
| "Evidence required for THEFT / EXPIRY" | High-loss reason without an attachment | Upload photo / damage report to `tb_stock_out_comment` |
| "Lot has zero balance" | Lot-tracked product at the source location is empty | Choose a different lot or correct on-hand first |
| "Period is closed" | `so_date` inside a closed period | Use today's date, or raise a manual JV |
| "Submit and approve must be different users" | Same user attempted both actions | Route to a different approver (segregation of duties) |
| Cannot edit a completed document | `doc_status = completed` is immutable | Issue a reversal (negative-qty wastage) |

## 4. Edge Cases

- **Variant, not a separate table.** Same schema as stock-out — discriminator is `adjustment_type_id`. Test plans that look for a `tb_wastage` table will find none.
- **Cost basis snapshot at submit.** `cost_per_unit` is picked from the active costing method (AVCO snapshot or oldest FIFO layer) and not editable.
- **No edit after post.** Once `doc_status = completed`, no field is mutable. Correction is a new opposite-sign wastage referencing the original in `note`.
- **Reversal is append-only.** The original row is never `UPDATE`d — the pair is the audit trail (matches [[inventory/transaction]] append-only semantics).
- **GL routing.** Credit side resolves from `tb_adjustment_type` GL mapping — a wastage expense account, NOT the generic adjustment expense.
- **Period gate.** Same as every inventory document — backdating into a closed period is rejected.

---

## 5. Data Model (Dev)

Wastage shares schema with stock-out. Source: tenant schema.

### 5.1 `tb_stock_out` (host table)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key. |
| `so_no` | `String? @db.VarChar` | Yes | Document number (`WR-2026-0001` when issued from wastage screen). |
| `so_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — gated against `tb_period`. |
| `adjustment_type_id` | `String? @db.Uuid` | Yes | FK to `tb_adjustment_type` — must resolve to wastage-flavoured row. |
| `adjustment_type_code` | `String? @db.VarChar` | Yes | Denormalised code (`SPOIL`, `BREAK`, etc.). |
| `doc_status` | `enum_doc_status` | No | `draft`, `in_progress`, `completed`, `cancelled`, `voided`. |
| `location_id` / `location_code` / `location_name` | `String?` | Yes | Location whose balance decrements. |
| `workflow_*` / `last_action_*` | mixed | Yes | Workflow stage, history, audit. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([so_no, deleted_at])`. Reverse relations to `tb_stock_out_detail`, `tb_stock_out_comment`.

### 5.2 `tb_stock_out_detail`

Carries `product_id`, `qty`, `cost_per_unit`, `total_cost`, lot reference, and back-pointer `inventory_transaction_id` set at post. `@@unique([stock_out_id, product_id, dimension, deleted_at])`.

### 5.3 `tb_adjustment_type` (reason catalogue)

| Field | Type | Description |
|---|---|---|
| `code`, `name` | `String` | e.g. `SPOIL` / "Spoilage". |
| `type` | `enum_adjustment_type` | `STOCK_IN` or `STOCK_OUT` — wastage rows are always `STOCK_OUT`. |
| `is_active` | `Boolean?` | Toggles availability in the picker. |

See [[master-data/adjustment-type]] for the full reason catalogue.

## 6. Lifecycle / Business Rules

```
1. Store Keeper opens Wastage Reporting / new, picks location and reason
2. Adds line items: product, qty, lot (cost_per_unit snapshot at submit)
3. Attaches evidence (high-loss reasons require it)
4. Submits -> draft -> in_progress, routes to Inventory Controller
5. Inventory Controller approves -> in_progress -> completed:
   - INSERT tb_inventory_transaction { inventory_doc_type: 'stock_out' }
   - INSERT tb_inventory_transaction_detail per line
   - INSERT tb_inventory_transaction_cost_layer with transaction_type = 'adjustment_out'
   - GL: DR Wastage Expense, CR Inventory
6. Reversal (only correction path): new tb_stock_out with negative qty, note links to original
```

- **Reason required**, **direction STOCK_OUT only**, **submit ≠ approve** (segregation of duties)
- **No edit after post** — append-only correction
- **Reporting flag.** Each posting contributes to the per-outlet, per-period, per-reason loss aggregation

## 7. Cross-References

- [[inventory-adjustment]] — parent module; same business rules apply
- [[master-data/adjustment-type]] — reason catalogue
- [[inventory]] &nbsp;·&nbsp; [[inventory/transaction]] &nbsp;·&nbsp; [[costing]] &nbsp;·&nbsp; [[reporting-audit]]

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_stock_out` (~2759-2812), `tb_stock_out_detail` (~2848-2886), `tb_adjustment_type` (~2569-2594), `enum_adjustment_type` (~2564-2567), `enum_doc_status` (~187-193).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/store-operation/wastage-reporting/` — `wr-form.tsx`, `wr-form-schema.ts`, `wr-item-fields.tsx`.
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` (wastage as a pre-close prerequisite).
