---
title: Delivery Point
description: Physical drop-off points for vendor deliveries — referenced by purchase orders and GRNs and joined to inventory locations.
published: true
date: 2026-05-17T11:00:00.000Z
tags: master-data, delivery-point, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Delivery Point

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_delivery_point` &nbsp;·&nbsp; **Used by:** PO, GRN, locations &nbsp;·&nbsp; Physical drop-off address for vendor deliveries.

## 1. What & Who

A **delivery point** is the physical address a vendor ships goods to — a loading dock, a back-of-house entrance, a remote-site receiving bay. POs carry the delivery point so the vendor knows where to drop; the GRN records the actual receiving point; and inventory **locations** can be tagged with a default delivery point so GRN routing has a sensible destination.

A property typically has a handful of delivery points (Main Dock, Banquet Dock, Spa Receiving) regardless of how many inventory locations exist downstream. **Maintained by** Product Admin; **read by** developers and testers on PO / GRN routing.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a delivery point | Configuration → Master Data → Delivery Point → **New** | Required: `name` |
| Deactivate | Toggle `is_active` | Hidden from PO/GRN pickers; historical docs still resolve |
| Tag a location's default | [[master-data/location]] detail | Sets `tb_location.delivery_point_id` |
| Override on GRN | GRN header field | GRN inherits from PO but may override on receipt |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name |
| "Name required" | Empty `name` | Add a display name |
| "Cannot delete — referenced by POs / GRNs / locations" | FK references exist | Inactivate instead |
| Location shows stale delivery-point name | `tb_location.delivery_point_name` snapshot wasn't refreshed after rename | Backfill via maintenance job |

## 4. Edge Cases

- **Rename propagation.** Documents store the FK so display refreshes automatically. Locations that **snapshot the name** (`tb_location.delivery_point_name`) need a backfill if the rename must show on legacy lookups.
- **Inactivation** hides from pickers but leaves historical references resolvable.
- **No code field** — only `name` is the identity here.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_delivery_point`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Main Dock`). |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `deliverypoint_name_u`. Index on `name`. Reverse relations to `tb_location`, `tb_purchase_request_detail`, and PO-PR linkage tables.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Deletion guards.** References from open POs, GRNs, or active locations block hard-delete.
- **Validation.** `name` required.
- **Lifecycle.** Inactive points stay readable on historical documents; hidden from pickers.
- **Rename propagation.** Documents resolve via FK; snapshotted name on `tb_location` needs backfill.

## 7. Cross-References

- [[purchase-order]] — PO header carries delivery-point reference.
- [[good-receive-note]] — GRN inherits from PO, may override.
- [[master-data/location]] — each location can tag a default delivery point.
- [[purchase-request]] — PR detail may hold a delivery-point hint that propagates to PO.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_delivery_point` (lines ~623-646).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/delivery-point/`.
