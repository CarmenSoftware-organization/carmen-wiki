---
title: Extra Cost Type
description: Catalogue of GRN landed-cost categories (freight, duty, handling) with per-instance allocation modes (by value, by qty, manual).
published: true
date: 2026-05-19T23:55:00.000Z
tags: master-data, extra-cost-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Extra Cost Type

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_extra_cost_type` (catalogue) + `tb_extra_cost` (per-GRN instance) &nbsp;·&nbsp; **Used by:** GRN landed-cost allocation &nbsp;·&nbsp; Categories like Freight / Duty / Handling with `by_value` / `by_qty` / `manual` allocation modes.

![Extra Cost Type screen](/screenshots/master-data/extra-cost-type.png)

## 1. What & Who

**Extra costs** are the freight, duty, handling, and other **landed-cost** components allocated onto received goods so the **unit cost in inventory** reflects the *delivered* cost, not just the invoice line. `tb_extra_cost_type` holds the named categories (`Freight`, `Customs Duty`, `Brokerage`); `tb_extra_cost` is a per-GRN instance with a chosen **allocation mode** (`by_value`, `by_qty`, or `manual`).

`by_value` spreads proportional to line value, `by_qty` proportional to received quantity, and `manual` accepts a per-line amount directly. **Maintained by** Product Admin (catalogue) and GRN users (instances). **Read by** the costing engine — misallocated extra costs distort inventory valuation.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a cost type | Configuration → Master Data → Extra Cost Type → **New** | Required: `name` |
| Deactivate a type | Toggle `is_active` | Hidden from new GRNs; historical GRNs unaffected |
| Attach to GRN | GRN edit screen → **Extra Costs** | Creates `tb_extra_cost` row; pick allocation mode |
| Switch allocation mode on draft GRN | Same screen | Triggers recalc of per-line amounts |
| Manual allocation | Set `allocate_extra_cost_type = manual` | Every GRN line must receive an explicit amount |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name |
| "Cannot delete — referenced by GRN extra-cost detail" | FK references exist | Inactivate instead |
| "Missing allocation amount on line N" | `manual` mode with a blank line | Enter an explicit amount on every line |
| "Allocated sum doesn't equal parent" | `by_value` / `by_qty` rounding outside tolerance | Re-run allocation or adjust manually |
| "Cannot change allocation on posted GRN" | Edit attempted after posting | Reverse / repost, or refuse the change |

## 4. Edge Cases

- **`manual` mode** requires every GRN line to have an explicit amount — posting is rejected if any line is blank.
- **Rounding tolerance** — `by_value` / `by_qty` must reconcile to parent total within tolerance.
- **Re-allocation on posted GRN** requires a recalc step or is refused; never silently mutate posted cost.
- **Inactive types** stay readable on historical GRNs.
- **Costing impact** — extra costs flow into the landed unit cost the costing engine consumes; bad allocation distorts every downstream balance.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_extra_cost_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Display name (e.g. `Freight`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `extra_cost_type_name_u`. Index on `name`. Reverse relation to `tb_extra_cost_detail`.

### 5.2 `tb_extra_cost`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Free-text label. |
| `good_received_note_id` | `String? @db.Uuid` | Yes | FK to `tb_good_received_note`. |
| `allocate_extra_cost_type` | `enum_allocate_extra_cost_type?` | Yes | `manual`, `by_value`, or `by_qty`. |
| `description`, `note` | `String?` | Yes | Free text. |
| `info`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `name` (`extra_cost_name_idx`). FK to `tb_good_received_note` `onDelete: NoAction`. Reverse relations to `tb_extra_cost_detail` and `tb_extra_cost_comment`. (`tb_extra_cost_detail` carries the per-line breakdown including the FK to `tb_extra_cost_type`.)

`enum_allocate_extra_cost_type` values: `manual`, `by_value`, `by_qty`.

## 6. Business Rules

- **Uniqueness.** `tb_extra_cost_type.name` unique among non-deleted rows.
- **Deletion guards.** Referenced types cannot be hard-deleted — inactivate.
- **Validation.** `manual` mode requires every line to have an amount; system rejects posting otherwise.
- **Allocation invariants.** `by_value` and `by_qty` must sum to parent total within rounding tolerance.
- **Lifecycle.** Inactive types readable on historical GRNs; hidden from new GRN pickers.
- **Re-allocation.** Changing mode on a posted GRN requires recalc or is refused.

## 7. Cross-References

- [good-receive-note](/en/inventory/good-receive-note) — sole consumer. Each GRN can attach multiple `tb_extra_cost` instances; allocation runs at posting.
- [costing](/en/inventory/costing) — landed unit cost flows from extra-cost allocation; misallocation distorts valuation.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (lines ~4828-4851), `tb_extra_cost` (lines ~4694-4718), `enum_allocate_extra_cost_type` (lines ~109-113).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/extra-cost-type/`.
