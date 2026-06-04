---
title: Vendor Business Type
description: Flat lookup that classifies vendors by business type (manufacturer, distributor, service, etc.) — referenced by the vendor record for reporting and filtering.
published: true
date: 2026-06-04T00:00:00.000Z
tags: master-data, vendor-business-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Vendor Business Type

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_vendor_business_type` &nbsp;·&nbsp; **Used by:** vendor record (`tb_vendor.business_type` JSON array) &nbsp;·&nbsp; A flat lookup classifying suppliers by business nature (manufacturer, distributor, service provider, etc.).

## 1. What & Who

**Vendor Business Type** is the taxonomy layer on the vendor master. Each type represents a category of business that a supplier operates in — for example, manufacturer, distributor, wholesaler, or service provider. A vendor can carry multiple types, stored as a JSON array of `{id, name}` objects on `tb_vendor.business_type`.

The entity is a **flat lookup** — no hierarchy, no workflow logic. Classification drives reporting (segmenting spend by supplier category) and filtering (finding all distributor vendors for a sourcing round). **Maintained by** Product Admin; **read by** every procurement and pricelist flow that groups or filters by vendor category.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a business type | Configuration → Master Data → Vendor Business Type → **New** | Required: `name`; optional `description` |
| Edit description | Edit dialog | Renaming does not auto-propagate to the JSON snapshot on `tb_vendor`; a maintenance refresh is required |
| Deactivate | Toggle `is_active = false` | Hidden from new pickers; existing vendor records retain the FK reference |
| Delete | Soft-delete (set `deleted_at`) | Only safe when no vendor references this type |
| Check which vendors use a type | Query `tb_vendor.business_type` JSON array | No direct FK column — stored as embedded JSON on the vendor |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name or restore the existing row |
| "Name required" | Empty `name` | Add a display name |
| "Cannot delete — referenced by vendors" | At least one vendor embeds this type in its `business_type` JSON | Deactivate instead of deleting; or clean up vendor references first |
| Type shows stale name on vendor | Vendor JSON snapshot not refreshed after rename | Run a maintenance job to refresh `tb_vendor.business_type` JSON across all vendors |

## 4. Edge Cases

- **JSON snapshot vs. FK.** `tb_vendor.business_type` stores a JSON array of `{id, name}` — a copy of the name at the time the vendor was saved. A rename on `tb_vendor_business_type` does **not** automatically refresh all vendor snapshots; a maintenance job is required.
- **Multiple types per vendor.** A single vendor may belong to several business types simultaneously (e.g. both distributor and service provider).
- **`is_active` flag.** Unlike most lookups that use only soft-delete, this table has `is_active`; set `is_active = false` to hide from pickers without removing the record.
- **Soft-delete still resolvable.** Vendors that embedded a now-deleted type retain the `id` in their JSON; if the lookup resolves by `id`, the name will resolve from the (soft-deleted) row.
- **Translation.** Type names may be visible to vendors in documents. Until a localisation table is introduced, translations live in `info` JSON.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_vendor_business_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @unique @db.VarChar` | No | Display name (e.g. `Manufacturer`, `Distributor`, `Service`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag (default `true`). |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Decimal @db.Decimal` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name])` (DB-level unique). `@@index([name], map: "vendor_business_type_name_u")`. Reverse relation: `tb_vendor[]` (via `business_type_id` FK on `tb_vendor`).

### 5.2 How `tb_vendor` references this entity

`tb_vendor` holds **two** references:

| Column | Type | Purpose |
|---|---|---|
| `business_type_id` | `String? @db.Uuid` | FK to `tb_vendor_business_type` (single primary type, `onDelete: NoAction`). |
| `business_type` | `Json? @db.JsonB` | Denormalised JSON array `[{id, name}]` for display across all assigned types. |

The FK column (`business_type_id`) pins one authoritative type; the JSON column captures the full multi-type selection for reporting.

## 6. Business Rules

- **Uniqueness.** `name` is DB-unique (`@unique`) across all rows, including soft-deleted. No two types may share the same name.
- **Deletion guards.** A type referenced by any vendor should not be hard-deleted. Deactivate (`is_active = false`) or soft-delete when the type is no longer needed; vendors retain their JSON snapshot.
- **Validation.** `name` required and unique.
- **Lifecycle.** `is_active = false` hides the type from pickers while preserving referential integrity. Soft-delete is the final retirement step.
- **Rename propagation.** Renaming a type does not auto-update the `business_type` JSON on vendors — run a maintenance refresh after a rename.
- **Translation.** Keep translations in `info` JSON until a localisation table is introduced.

## 7. Cross-References

- [master-data/vendor](/en/inventory/master-data/vendor) — the vendor record that embeds `business_type` JSON and holds the `business_type_id` FK.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelist sourcing rounds may filter by vendor business type.
- [purchase-request](/en/inventory/purchase-request) — PR preferred-vendor selection may surface business type for filtering.

## 8. References

- **Prisma:** `../carmen/docs/prisma-schema/schema.prisma` — `tb_vendor_business_type` (lines ~2646-2667); used by `tb_vendor` (`business_type_id` FK at line ~1862, `business_type` JSON at line ~1868).
- **Frontend:** `../carmen-inventory-frontend/` — Vendor Business Type list under Configuration → Master Data.
