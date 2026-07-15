---
title: Vendor Business Type
description: Flat lookup that classifies vendors by business type (manufacturer, distributor, service, etc.) — referenced by the vendor record for reporting and filtering.
published: true
date: 2026-07-15T21:47:09.000Z
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
| **Unconfirmed** — no delete guard found | `vendor_business_type.service.ts`'s `delete()` is an unconditional soft-delete with no check for vendor references — and since there is no DB-level FK from `tb_vendor` to this table at all (see § 5.2), there is nothing for such a check to query against beyond scanning every vendor's JSON | A prior version of this page asserted "cannot delete — referenced by vendors" as an enforced error; treat it as **not enforced** |
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
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `vendor_business_type_name_u`. Index on `name`. **No reverse relation to `tb_vendor` exists in the schema** — see § 5.2.

### 5.2 How `tb_vendor` references this entity — confirmed: no FK, JSON only

A prior version of this page described `tb_vendor` holding a `business_type_id` FK column (a single "primary" type) alongside the `business_type` JSON array. A direct read of the current tenant schema (`tb_vendor` model) found **no `business_type_id` column at all** — the model has no field or `@relation` pointing at `tb_vendor_business_type`. The only link is:

| Column | Type | Purpose |
|---|---|---|
| `business_type` | `Json? @db.JsonB` (default `[]`) | Array of `{id, name}` snapshots, one per assigned type. |

This is a **loose, app-enforced reference only** — there is no foreign key, so the database does not enforce that a `business_type` JSON entry's `id` still exists on (or ever existed on) a real `tb_vendor_business_type` row, and no `onDelete` behavior applies when a type is deleted. Referential integrity here is entirely the frontend's responsibility (the vendor form's business-type picker, `vendor-form-schema.ts`).

## 6. Business Rules

- **Uniqueness.** `@@unique([name, deleted_at])` — unique among non-deleted rows only (the standard soft-delete-compound-unique pattern used throughout this module), not across all rows regardless of deletion.
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally. Since there is no FK from `tb_vendor` (only a loose JSON snapshot, § 5.2), there is also no DB-level mechanism that could enforce such a guard even if the service checked for it.
- **Validation.** `name` required and unique.
- **Lifecycle.** `is_active = false` hides the type from pickers; vendors retain their JSON snapshot regardless.
- **Rename propagation.** Renaming a type does not auto-update the `business_type` JSON on vendors — run a maintenance refresh after a rename.
- **Translation.** Keep translations in `info` JSON until a localisation table is introduced.

## 7. Cross-References

- [master-data/vendor](/en/inventory/master-data/vendor) — the vendor record that embeds a `business_type` JSON array; there is no FK, so this is a naming-only link.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelist sourcing rounds may filter by vendor business type.
- [purchase-request](/en/inventory/purchase-request) — PR preferred-vendor selection may surface business type for filtering.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_vendor_business_type` (lines ~5229-5250); `tb_vendor`'s `business_type` JSON field (lines ~3500-3552, no `business_type_id` column exists).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/vendor_business_type/vendor_business_type.service.ts`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/business-type/`.
