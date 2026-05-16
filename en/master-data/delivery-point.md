---
title: Delivery Point
description: Physical drop-off points for vendor deliveries — referenced by purchase orders and GRNs and joined to inventory locations.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, delivery-point, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Delivery Point

## 1. Purpose

A delivery point is the physical address a vendor ships goods to — a loading dock, a back-of-house entrance, a remote-site receiving bay. Purchase orders carry the delivery point so the vendor knows where to drop off; the GRN records the actual receiving point against the PO; and one or more inventory locations can be tagged as fed-from a given delivery point so that GRN routing has a sensible default destination.

A property typically has a handful of delivery points (Main Dock, Banquet Dock, Spa Receiving) regardless of how many inventory locations exist downstream.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_delivery_point`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Main Dock`). |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `deliverypoint_name_u`. Index on `name`. Reverse relations to `tb_location`, `tb_purchase_request_detail`, and PO-PR linkage tables.

## 3. Usage / Cross-References

- [[purchase-order]] — PO header carries delivery-point reference so the vendor knows where to deliver.
- [[good-receive-note]] — GRN inherits the PO's delivery point and may override it on receipt.
- [[master-data/location]] — each inventory location can be tagged with a default delivery point.
- [[purchase-request]] — PR detail lines can hold a delivery-point hint that propagates into the resulting PO.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area. Listing screen plus a simple edit dialog (name + active).

## 5. Business Rules

- **Uniqueness.** `name` is unique among non-deleted rows (DB-enforced via `@@unique`).
- **Deletion guards.** A delivery point referenced by open POs, GRNs, or active locations cannot be deleted; mark inactive instead.
- **Validation.** `name` is required.
- **Lifecycle.** Inactive delivery points stay readable on historical documents but are hidden from PO/GRN pickers.
- **Rename propagation.** Renaming a delivery point updates the master record only; documents store the ID, so display refreshes automatically. Locations that snapshot the name (`tb_location.delivery_point_name`) need a backfill if the rename must show on legacy lookups.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_delivery_point` (lines ~623-646).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/delivery-point/`.
- **Cross-module:** see Section 3.
