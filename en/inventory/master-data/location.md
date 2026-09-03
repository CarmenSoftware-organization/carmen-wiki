---
title: Location
description: Storage and consumption locations classified as inventory, direct, or consignment — drives stock posting and physical-count behaviour.
published: true
date: 2026-07-15T21:47:09.000Z
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

**Locations** are the physical or logical places where stock lives or is consumed — main warehouse, kitchen pass, bar, housekeeping cart, supplier-owned consignment shelf. The `location_type` field decides posting behaviour (confirmed against `inventory-transaction.service.ts` by the [inventory](/en/inventory/inventory) module's own resync pass — there is no GL/journal-posting code anywhere in the codebase, so "posts to GL"-style language below describes inventory-transaction layers, not ledger entries):

- **`inventory`** — carries a stock balance; receipts and issues write ordinary in/out cost-layer rows.
- **`direct`** — a receipt writes the normal inbound layer *plus* an automatic offsetting outbound layer at the same cost (net zero, excluded from the average) — not "no cost-layer row" as an earlier draft of this page implied.
- **`consignment`** — holds supplier-owned goods; has no distinct code path from `inventory` in the transaction/period-end/count filters that were checked.

The same record configures period-end count behaviour (`physical_count_type` = `yes` / `no`) and the default delivery point that ships into this location. **Maintained by** Product Admin. **Read by** every inventory posting path.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a location | Configuration → Master Data → Location → **New** | Required: `code`, `name`, `location_type` |
| Tag default delivery point | Location detail | Sets `delivery_point_id` + denormalised `delivery_point_name` |
| Set count behaviour | Toggle `physical_count_type` | `no` skips period-end count; spot check still applies |
| Deactivate | Toggle `is_active` | Hidden from pickers; historical postings preserved |
| Change `location_type` | Edit dialog | **Not actually blocked** — `update()` accepts a new value with no prior-movement check found (unconfirmed guard, see Edge Cases); doing so after postings exist would still corrupt the meaning of historical reporting |
| Assign inventory tree | Location detail screen | Restricts which products are visible at this location |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | Duplicate `code` among active rows | Pick a different code |
| **Unconfirmed** — no delete or location_type-change guard found | `locations.service.ts`'s `delete()` is an unconditional soft-delete with no non-zero-balance or open-SR/GRN-reference check; `update()` accepts a new `location_type` with no check for prior movement | A prior version of this page asserted "cannot delete — non-zero balance", "cannot delete — referenced by open SR/GRN", and "cannot change location_type after first movement" as enforced server errors — none were found this pass; treat all three as **not enforced** until re-verified |
| Delivery-point name in reports | `delivery_point_name` snapshot may differ if not kept in sync | Query `delivery_point.name` via join for authoritative value |

## 4. Edge Cases

- **`location_type` change is not blocked today.** No code in `locations.service.ts` checks for prior movement before accepting a new `location_type` on `update()`. Switching `inventory` → `direct` after postings exist would still corrupt the meaning of historical inventory-transaction reporting — treat the prior "the system rejects it" claim as unconfirmed/design-intent, not a live guard.
- **Count exemption** — `physical_count_type = no` excludes from period count but **not** from spot checks.
- **Consignment has no distinct code path (confirmed by the inventory module's own resync pass).** It is grouped with `inventory` in every filter checked (transaction, period-end validate/review, physical-count-period, spot-check, SR from-location) — treat the prior "recognised on consumption rather than receipt" claim as unconfirmed design intent, not live behavior.
- **Delivery-point coupling** — The form reads `delivery_point.name` from the nested API object, so an inactive delivery point assigned to a location still shows its name in both view and edit mode (the edit form passes it as `defaultLabel` to the lookup widget, which only lists active delivery points). The `delivery_point_name` snapshot field remains on the record for legacy references.
- **Code uniqueness is app-enforced** (no DB unique constraint).
- **Deletion is unconfirmed to be guarded.** `delete()` sets `is_active: false` + `deleted_at` unconditionally — no check for non-zero on-hand balance or open SR/GRN references was found.

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
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`. FK on `delivery_point_id` → `tb_delivery_point` `onDelete: NoAction`. Uniqueness on `code` enforced at app layer.

`enum_location_type` values: `inventory`, `direct`, `consignment`.
`enum_physical_count_type` values: `no`, `yes`.

## 6. Business Rules

- **Uniqueness.** `code` unique among active rows (app-enforced).
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally regardless of on-hand balance or open SR/GRN references.
- **Validation — unconfirmed.** No code was found that blocks changing `location_type` after first movement; `update()` accepts it freely.
- **Lifecycle.** `is_active = false` hides from pickers; preserves historical postings. An already-assigned delivery point that is later deactivated continues to display its name in the location view and edit form (the form reads `delivery_point.name` from the nested object, not the snapshot field).
- **Count exemption.** `physical_count_type = no` excludes period count, not spot check.
- **Delivery-point coupling.** The location form shows the live name from `delivery_point.name` (nested object), so the displayed label is always current. The `delivery_point_name` column is a legacy snapshot field that the UI no longer depends on for display.
- **Optimistic lock.** Location PATCH carries a `doc_version`; the client must echo the current `doc_version` on save or receive a `409 Conflict`, and the version increments on success. Scope is the `tb_location` header only — junction sub-tables (`tb_user_location`, `tb_product_location`) are not guarded.

## 7. Cross-References

- [inventory](/en/inventory/inventory) — every stock balance keyed by location; type decides whether balance is tracked.
- [good-receive-note](/en/inventory/good-receive-note) — GRN detail lines target a destination location; `location_type` decides the inventory-transaction posting behavior (no GL/journal-posting code exists anywhere in the codebase — confirmed by the [inventory](/en/inventory/inventory) module's own resync pass).
- [store-requisition](/en/inventory/store-requisition) — `from_location` / `to_location` on every issue/transfer.
- [physical-count](/en/inventory/physical-count) — counts scoped to locations with `physical_count_type = yes`.
- [spot-check](/en/inventory/spot-check) — sessions enumerate locations.
- [purchase-request](/en/inventory/purchase-request) and [purchase-order](/en/inventory/purchase-order) — detail lines may carry destination location.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location` (lines ~1328-1375), `enum_location_type` (lines ~222-226), `enum_physical_count_type` (lines ~51-54).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/location/`.
- **carmen/docs:** `../carmen/docs/settings/locations.md` — wireframes.
