---
title: Extra Cost Type
description: Catalogue of GRN landed-cost categories (freight, duty, handling) with per-instance allocation modes (by value, by qty, manual).
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, extra-cost-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Extra Cost Type

## 1. Purpose

Extra costs are the freight, duty, handling, and other landed-cost components that need to be allocated onto received goods so the unit cost in inventory reflects the *delivered* cost, not just the invoice line. The catalogue table `tb_extra_cost_type` holds the named categories (e.g. `Freight`, `Customs Duty`, `Brokerage`), and the transactional table `tb_extra_cost` is an instance of an extra cost attached to a specific GRN with a chosen allocation mode.

The allocation mode is per-instance and lives on `tb_extra_cost.allocate_extra_cost_type` — values are `by_value`, `by_qty`, or `manual`. `by_value` spreads proportional to line value, `by_qty` spreads proportional to received quantity, `manual` lets the user enter a per-line amount directly.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_extra_cost_type`

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

### 2.2 `tb_extra_cost`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Free-text label for this instance. |
| `good_received_note_id` | `String? @db.Uuid` | Yes | FK to `tb_good_received_note` — which GRN the cost is attached to. |
| `allocate_extra_cost_type` | `enum_allocate_extra_cost_type?` | Yes | `manual`, `by_value`, or `by_qty`. |
| `description`, `note` | `String?` | Yes | Free text. |
| `info`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `name` (`extra_cost_name_idx`). FK to `tb_good_received_note` `onDelete: NoAction`. Reverse relations to `tb_extra_cost_detail` and `tb_extra_cost_comment`. (`tb_extra_cost_detail` carries the per-line breakdown including the FK to `tb_extra_cost_type`.)

`enum_allocate_extra_cost_type` values: `manual`, `by_value`, `by_qty`.

## 3. Usage / Cross-References

- [[good-receive-note]] — sole consumer. Each GRN can attach multiple `tb_extra_cost` instances; the allocation runs at posting time and feeds into the per-line landed unit cost.
- [[costing]] — landed unit cost from GRN is what the costing engine consumes for inventory valuation, so misallocated extra costs distort costing.

## 4. Configuration UI

`tb_extra_cost_type` is managed by **Product Admin** under the Master Data area as a simple list + edit dialog. `tb_extra_cost` instances are created inside the GRN edit screen.

## 5. Business Rules

- **Uniqueness.** `tb_extra_cost_type.name` is unique among non-deleted rows.
- **Deletion guards.** An extra-cost type referenced by any GRN extra-cost detail cannot be hard-deleted. Inactivate instead.
- **Validation.** When `allocate_extra_cost_type = manual`, every GRN line must receive an explicit amount; system rejects posting if any line is blank.
- **Allocation invariants.** `by_value` and `by_qty` must produce a sum of allocated amounts equal to the parent `tb_extra_cost` total within rounding tolerance.
- **Lifecycle.** Inactive types stay readable on historical GRNs but are hidden from new GRN pickers.
- **Re-allocation.** Changing `allocate_extra_cost_type` on a posted GRN requires a recalc step; the system either reposts the GRN or refuses the change.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (lines ~4828-4851), `tb_extra_cost` (lines ~4694-4718), `enum_allocate_extra_cost_type` (lines ~109-113).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/extra-cost-type/`.
- **Cross-module:** see Section 3.
