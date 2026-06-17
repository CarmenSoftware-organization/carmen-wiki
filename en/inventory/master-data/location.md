---
title: Location
description: Storage and consumption locations classified as inventory, direct, or consignment — drives stock posting and physical-count behaviour.
published: true
date: 2026-06-17T08:00:00.000Z
tags: master-data, location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Location

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_location` &nbsp;·&nbsp; **Used by:** inventory, GRN, SR, physical count, spot check, PR/PO &nbsp;·&nbsp; `location_type` (`inventory` / `direct` / `consignment`) decides posting behaviour.

![Location screen](/screenshots/master-data/location.png)

![Location detail screen](/screenshots/master-data/location-detail.png)

## 1. What & Who

**Locations** are the physical or logical places where stock lives or is consumed — main warehouse, kitchen pass, bar, housekeeping cart, supplier-owned consignment shelf. The `location_type` field decides posting behaviour:

- **`inventory`** — carries a stock balance, posts to inventory asset GL.
- **`direct`** — bypasses the balance, posts straight to department expense.
- **`consignment`** — holds supplier-owned goods, recognised only when consumed.

The same record configures period-end count behaviour (`physical_count_type` = `yes` / `no`) and the default delivery point that ships into this location. **Maintained by** Product Admin. **Read by** every inventory posting path.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a location | Configuration → Master Data → Location → **New** | Required: `code`, `name`, `location_type` |
| Tag default delivery point | Location detail | Sets `delivery_point_id` + denormalised `delivery_point_name` |
| Set count behaviour | Toggle `physical_count_type` | `no` skips period-end count; spot check still applies |
| Deactivate | Toggle `is_active` | Hidden from pickers; historical postings preserved |
| Change `location_type` | Edit dialog | **Blocked after first movement** — would corrupt journal history |
| Assign inventory tree | Location detail screen | Restricts which products are visible at this location |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | Duplicate `code` among active rows | Pick a different code |
| "Cannot delete — non-zero balance" | Location still holds stock | Issue out or transfer first |
| "Cannot delete — referenced by open SR/GRN" | FK references in open docs | Close documents first |
| "Cannot change location_type" | Edit attempted after first movement | Create a new location and migrate manually |
| Delivery-point name stale | `delivery_point_name` snapshot wasn't refreshed | Re-save the location or run a backfill |

## 4. Edge Cases

- **`location_type` is sticky once used** — switching `inventory` → `direct` retro-actively corrupts journal entries.
- **Count exemption** — `physical_count_type = no` excludes from period count but **not** from spot checks.
- **Consignment balances** are supplier-owned; recognised on consumption rather than receipt.
- **Delivery-point coupling** — `delivery_point_name` is denormalised, needs refresh on rename.
- **Code uniqueness is app-enforced** (no DB unique constraint).

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_location`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code, e.g. `INV1`, `KIT`. |
| `name` | `String @db.VarChar` | No | Display name. |
| `location_type` | `enum_location_type` | No | `inventory` (default), `direct`, or `consignment`. |
| `description` | `String?` | Yes | Free text. |
| `delivery_point_id` | `String? @db.Uuid` | Yes | Optional FK to `tb_delivery_point`. |
| `delivery_point_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `physical_count_type` | `enum_physical_count_type` | No | `no` (default) — skip; `yes` — include. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`. FK on `delivery_point_id` → `tb_delivery_point` `onDelete: NoAction`. Uniqueness on `code` enforced at app layer.

`enum_location_type` values: `inventory`, `direct`, `consignment`.
`enum_physical_count_type` values: `no`, `yes`.

## 6. Business Rules

- **Uniqueness.** `code` unique among active rows (app-enforced).
- **Deletion guards.** Non-zero balance or open SR/GRN references block deletion.
- **Validation.** `location_type` cannot change after first movement.
- **Lifecycle.** `is_active = false` hides from pickers; preserves historical postings.
- **Count exemption.** `physical_count_type = no` excludes period count, not spot check.
- **Delivery-point coupling.** Refresh `delivery_point_name` snapshot on rename.
- **Optimistic lock.** Location PATCH carries a `doc_version`; the client must echo the current `doc_version` on save or receive a `409 Conflict`, and the version increments on success. Scope is the `tb_location` header only — junction sub-tables (`tb_user_location`, `tb_product_location`) are not guarded.

## 7. Cross-References

- [inventory](/en/inventory/inventory) — every stock balance keyed by location; type decides whether balance is tracked.
- [good-receive-note](/en/inventory/good-receive-note) — GRN detail lines target a destination location; type drives the journal entry.
- [store-requisition](/en/inventory/store-requisition) — `from_location` / `to_location` on every issue/transfer.
- [physical-count](/en/inventory/physical-count) — counts scoped to locations with `physical_count_type = yes`.
- [spot-check](/en/inventory/spot-check) — sessions enumerate locations.
- [purchase-request](/en/inventory/purchase-request) and [purchase-order](/en/inventory/purchase-order) — detail lines may carry destination location.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location` (lines ~1294-1393), `enum_location_type` (lines ~218-222), `enum_physical_count_type` (lines ~62-65).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/location/`.
- **carmen/docs:** `../carmen/docs/settings/locations.md` — wireframes.
