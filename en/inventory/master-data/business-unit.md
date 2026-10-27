---
title: Business Unit
description: The legal/operating unit (property or BU) that scopes every transaction — owns calculation method, default currency, and module subscriptions.
published: true
date: 2026-10-27T00:00:00.000Z
tags: master-data, business-unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_business_unit` (backstage schema, formerly "platform") &nbsp;·&nbsp; **Used by:** every transactional document &nbsp;·&nbsp; Top-level scope — owns costing method, default currency, and module enablement.

![Business Unit screen](/screenshots/master-data/business-unit.png)

## 1. What & Who

A **Business Unit (BU)** is the top-level scope every document, user role, and report is bound to — usually one **property** (hotel) inside a **cluster** (group). Crucially, the BU owns the **costing calculation method** (`average`, `fifo`, or `average_per_location` - the third value was added after the 2026-09-22 round; see [costing](/en/inventory/costing)) that drives valuation of every stock movement. The BU also owns the default currency, company/hotel identity, format defaults (date, time, money, qty), tenant database pointer (`database_pool_id` + `db_schema`), and module enablement.

**Maintained by** Sysadmin in the Backstage admin console (`carmen-backstage`). **Read by** every backend service (every query is BU-scoped) and the costing engine in particular.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a BU | Backstage admin → BU listing → **New** | Required: `cluster_id`, `code`, `name`, `calculation_method` |
| Set default currency | BU detail → Identity tab | `default_currency_id` renders as a **disabled** `<select>` in `carmen-backstage` (`CalculationSettingsSection.tsx:68`) — not editable from the admin UI this pass; must reference an active row in [master-data/currency](/en/inventory/master-data/currency) by convention only |
| Switch costing method | BU detail → Costing tab | Blocked mid-period; requires period-end snapshot + recost — see Edge Cases |
| Enable / disable a module | BU detail → Modules tab | Writes to `tb_business_unit_tb_module`; hides UI but preserves data |
| Mark HQ | Set `is_hq = true` | Exactly one HQ per cluster (app invariant) |
| Deactivate a BU | Toggle `is_active` | Blocks new logins, preserves all data |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | Duplicate `code` **anywhere in the system** — partial unique index `business_unit_code_global_u` (`(code) WHERE deleted_at IS NULL`, backstage-schema migration `20260904000000_business_unit_code_global_unique`); since backend PR #497 (`56d4871e9`) the backend generates the BU code itself and the form does not accept one | Let the platform assign the code |
| "Name already in use in cluster" | Duplicate `name` within the same `cluster_id` — partial unique index `business_unit_cluster_name_u` (`20260904010000_business_unit_cluster_name_unique`) | Pick a different name |
| **Unconfirmed** — the edit form imposes no client-side restriction | `carmen-backstage`'s `CalculationSettingsSection.tsx` renders `calculation_method` as a plain, always-editable `<select>` (`average` / `fifo` / `average_per_location`) with no disabled state, warning, or mid-period check found in the component; whether the backend `business-units.update` microservice command enforces a block was not traced this pass | A prior version of this page asserted "cannot change calculation method mid-period" as an enforced error; treat it as **unconfirmed** rather than a guaranteed guard |
| "Default currency must be active" — **unconfirmed** | No disabled-state or validation tying `default_currency_id` to the target currency's `is_active` flag was found in the edit form this pass | Treat as unconfirmed |
| "Cannot delete BU — active users / open documents / non-zero balances" — **unconfirmed** | `deleteBusinessUnit` in the gateway is a thin proxy to a `business-units.delete` microservice command; the guard, if any, was not traced this pass | Treat as unconfirmed rather than a guaranteed block |

## 4. Edge Cases

- **Calculation-method switch — unconfirmed guard.** Flipping the method (e.g. `average` ↔ `fifo`) would retro-actively break historical valuation in principle, but `carmen-backstage`'s edit form has no disabled state or warning on this field, and whether the backend microservice blocks it mid-period was not traced this pass. Treat "system rejects mid-period" as design intent, not a confirmed guard.
- **`is_hq` invariant.** Exactly one BU per cluster carries `is_hq = true` — app-enforced, not DB.
- **Module disable preserves data.** Removing a module via `tb_business_unit_tb_module` hides UI; underlying transactional data is untouched.
- **Currency inactivation — unconfirmed.** Whether the backstage side blocks inactivating a currency that is a BU's `default_currency_id` was not traced this pass (the equivalent check was directly confirmed **absent** on the Inventory side's own `tb_currency` update path — see [master-data/currency](/en/inventory/master-data/currency)).
- **Tenant DB pointer.** `database_pool_id` (FK → `tb_database_pool`) plus `db_schema` locate the BU's tenant schema; misconfiguration takes the whole BU offline. (An earlier version of this page described a `db_connection` JSON column - no such column exists in the model.)

---

## 5. Data Model (Dev)

Source: backstage schema (`packages/prisma-shared-schema-backstage/prisma/schema.prisma`; the package was `prisma-shared-schema-platform` until the 2026-10 rename). BU lives there rather than in a tenant schema because users and clusters span tenants.

### 5.1 `tb_business_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cluster_id` | `String @db.Uuid` | No | FK to `tb_cluster`. |
| `code` | `String @db.VarChar(30)` | No | Short BU code. |
| `name` | `String` | No | Display name. |
| `alias_name` | `String? @db.VarChar(10)` | Yes | Short alias used in numbering. |
| `description`, `info` | — | Yes | Free text / JSON metadata. |
| `is_hq` | `Boolean?` | Yes | Marks the HQ BU in a cluster (default `true`). |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `database_pool_id`, `db_schema` | `UUID?`, `VarChar?` | Yes | FK → `tb_database_pool` and the schema name locating the tenant data. |
| `config` | `Json?` | Yes | Per-BU config blob. |
| `default_currency_id` | `String? @db.Uuid` | Yes | Default currency (tenant currency catalogue). |
| `calculation_method` | `enum_calculation_method` | No | `average` (default), `fifo` or `average_per_location`. **Source of truth for costing.** |
| *(licence data)* | - | - | `max_license_users` no longer exists: it was removed from the model and the column dropped (migration `20260821000000_drop_bu_max_license_users`). The seat pool is read from the view `v_business_unit_seat` over dated `tb_business_unit_license` rows, and interface entitlements live in `tb_business_unit_interface_license`; licence data is served by `GET /api/license`, no longer by `GET /api/user/profile` (2026-09-09). |
| Company info: `branch_no`, `company_name`, `company_address`, `company_email`, `company_tel`, `company_zip_code`, `tax_no` | `String?` | Yes | Legal-entity identity. |
| Hotel info: `hotel_name`, `hotel_address`, `hotel_email`, `hotel_tel`, `hotel_zip_code` | `String?` | Yes | Operating identity. |
| Format settings: `date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format`, `timezone`, `amount_format`, `quantity_format`, `recipe_format` | mixed | Yes | UI defaults. `timezone` defaults `Asia/Bangkok`. |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.2 `tb_business_unit_tb_module`

Link table to `tb_module`; index on `(business_unit_id, module_id, deleted_at)`. FKs cascade `NoAction`.

### 5.3 `enum_calculation_method`

```
enum enum_calculation_method {
  average
  fifo
  average_per_location
}
```

The tenant schema used to carry a same-named enum with `FIFO` / `AVG`; it was unused and was dropped by tenant migration `20260928130000_drop_unused_calculation_method_enum`, so only the backstage definition exists now.

## 6. Business Rules

- **Uniqueness (corrected 2026-09-22).** `code` is unique **system-wide (across all BUs)** and server-generated (`business_unit_code_global_u`, 2026-09-04); `name` is unique within a cluster (`business_unit_cluster_name_u`). Both are partial unique indexes declared only in the migration SQL — the Prisma model still shows the older `@@unique([cluster_id, code, deleted_at])` (`business_unit_cluster_code_deleted_at_u`) alongside them.
- **Deletion guards — unconfirmed.** The gateway's `deleteBusinessUnit` is a thin proxy to a `business-units.delete` microservice command; whether active users, open documents, or non-zero balances actually block deletion was not traced this pass.
- **Validation.** `cluster_id`, `code`, `name`, `calculation_method` required.
- **Lifecycle.** `is_active = false` blocks logins, preserves data.
- **Calculation method change** — **design intent, unconfirmed guard.** Flipping `average` ↔ `fifo` should in principle follow period-close + recost discipline, but as noted in Section 4 (Edge Cases; also Section 3 Validation & Errors), `carmen-backstage`'s edit form imposes no disabled state or mid-period restriction on this field, and whether the backend microservice enforces one was not traced this pass — treat "must follow period-close + recost discipline" as design intent, not a confirmed guard.
- **`is_hq` invariant.** Exactly one HQ per cluster.

## 7. Cross-References

- [costing](/en/inventory/costing) — reads `calculation_method` per BU.
- [inventory](/en/inventory/inventory) — balances and valuation scoped per BU.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [vendor-pricelist](/en/inventory/vendor-pricelist) — every transactional document is BU-scoped.
- [access-control](/en/inventory/access-control) — user-to-BU mapping drives the `x-app-id` header.
- [reporting-audit](/en/inventory/reporting-audit) — reports filter / roll up by BU.

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `tb_business_unit` (line ~213), `enum_calculation_method` (~169), `tb_currency_iso` (~428).
- **Backstage-schema migrations:** `20260904000000_business_unit_code_global_unique`, `20260904010000_business_unit_cluster_name_unique`.
- **Frontend:** `../carmen-backstage/src/pages/BusinessUnitEdit.tsx` + `businessUnitEdit/sections/CalculationSettingsSection.tsx` (platform admin dashboard).
- **Backend:** `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_business-units/backstage_business-units.service.ts` (thin proxy to a `business-units` microservice not traced this pass).
