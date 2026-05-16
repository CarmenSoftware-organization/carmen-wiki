---
title: Location
description: Storage and consumption locations classified as inventory, direct, or consignment — drives stock posting and physical-count behaviour.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Location

## 1. Purpose

Locations are the physical or logical places where stock lives or is consumed — main warehouse, kitchen pass, bar, housekeeping cart, supplier-owned consignment shelf. The `location_type` field determines posting behaviour: an `inventory` location carries a stock balance and posts to the inventory asset GL account; a `direct` location bypasses the balance and posts straight to department expense; a `consignment` location holds supplier-owned goods that are recognised only when consumed.

The same record also configures the period-end physical-count behaviour (`physical_count_type` = `yes` / `no`) and the default delivery point that ships into this location.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_location`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code, e.g. `INV1`, `KIT`. |
| `name` | `String @db.VarChar` | No | Display name. |
| `location_type` | `enum_location_type` | No | `inventory` (default), `direct`, or `consignment`. |
| `description` | `String?` | Yes | Free text. |
| `delivery_point_id` | `String? @db.Uuid` | Yes | Optional FK to `tb_delivery_point` — default delivery target for this location. |
| `delivery_point_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `physical_count_type` | `enum_physical_count_type` | No | `no` (default) — skip in count; `yes` — include in count. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`. FK on `delivery_point_id` → `tb_delivery_point` with `onDelete: NoAction`. Uniqueness on `code` is enforced at the application layer.

`enum_location_type` values: `inventory`, `direct`, `consignment`.
`enum_physical_count_type` values: `no`, `yes`.

## 3. Usage / Cross-References

- [[inventory]] — every stock balance is keyed by location; `location_type` decides whether the balance is tracked.
- [[good-receive-note]] — GRN detail lines target a destination location; type drives the journal entry.
- [[store-requisition]] — `from_location` and `to_location` on every issue/transfer requisition.
- [[physical-count]] — counts are scoped to locations with `physical_count_type = yes`.
- [[spot-check]] — spot-check sessions enumerate locations.
- [[purchase-request]] and [[purchase-order]] — detail lines may carry a destination location.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area. The listing matches the carmen/docs layout (code, name, delivery point, EOP behaviour, location type, active) and a detail screen lets the admin assign the inventory tree visible at the location.

## 5. Business Rules

- **Uniqueness.** `code` must be unique among active rows (application-enforced).
- **Deletion guards.** A location with any non-zero current balance cannot be deleted; a location referenced by open SR/GRN documents cannot be deleted.
- **Validation.** `location_type` cannot be changed after the location has booked any movements — switching `inventory` → `direct` retro-actively would corrupt historical journal entries.
- **Lifecycle.** `is_active = false` hides the location from new-document pickers; historical postings remain visible.
- **Count exemption.** Setting `physical_count_type = no` excludes the location from period-end counts but **not** from spot checks.
- **Delivery-point coupling.** If `delivery_point_id` is set, the denormalised `delivery_point_name` must be refreshed when the delivery point is renamed.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location` (lines ~1294-1393), `enum_location_type` (lines ~218-222), `enum_physical_count_type` (lines ~62-65).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/location/`.
- **carmen/docs:** `../carmen/docs/settings/locations.md` — listing screen and detail screen wireframes.
- **Cross-module:** see Section 3.
