---
title: Master Data
description: Business master data referenced by transactional documents — units, departments, locations, shelves, vendors, currencies, tax profiles, chart of accounts, cost centres, and related catalogs.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: master-data, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Master Data

> **At a Glance**
> **Module purpose:** Catalogue of named records (units, vendors, currencies, locations, tax profiles, reason codes) that transactional documents reference via FK + denormalised snapshot &nbsp;·&nbsp; **Audience:** Product Admin, Configurator, Sysadmin &nbsp;·&nbsp; **Key entities/tables:** `tb_unit`, `tb_vendor`, `tb_currency` + `tb_exchange_rate`, `tb_tax_profile`, `tb_location`, `tb_location_shelf`, `tb_chart_of_accounts`, `tb_cost_center` &nbsp;·&nbsp; **Sub-pages:** 17

![Master Data screen](/screenshots/master-data/index.png)

## 1. Overview

Master data is the set of named records that transactional documents *reference* but do not own. Units, departments, locations, shelves, delivery points, business units, currencies, vendors, tax profiles, credit terms, extra-cost types, adjustment types, credit-note reasons, the chart of accounts, and cost centres all live here. (Pricelist templates are a separate entity, owned by the [vendor-pricelist](/en/inventory/vendor-pricelist) module's `vendor-management/price-list-template` route — not part of this module.) Each one is small on its own, and each one is referenced by many transactional rows.

**A note on scope (re-verified 2026-09-22):** the frontend's actual `/config/*` route tree (`routes/config/`) now has 15 leaf screens — `unit`, `department`, `location`, `shelf`, `delivery-point`, `currency`, `exchange-rate`, `tax-profile`, `credit-term`, `extra-cost`, `adjustment-type`, `credit-note-reason`, `business-type`, `chart-of-accounts`, `chart-of-account-mapping`. Since the 2026-07-29 baseline `certification` moved to `routes/vendor-management/certification` and `eco` moved to `routes/product-management/eco` (frontend commit `ac1e7c56`, 2026-09-03), so they are no longer Configuration screens — see [vendor](/en/inventory/master-data/vendor) § 5.5 and [product/01-data-model](/en/inventory/product/01-data-model) § 2.10 respectively. Three screens/entities were added in the same window and now have sub-pages: [shelf](/en/inventory/master-data/shelf), [chart-of-accounts](/en/inventory/master-data/chart-of-accounts), and [cost-center](/en/inventory/master-data/cost-center) (backend + Bruno only — no `/config/*` route yet). `chart-of-account-mapping` (renamed from "Account Mapping" on 2026-09-20, frontend `11ec09a3`) is a **read-only list that still renders the in-repo mock `coam-mock.ts`** — it has no gateway endpoint; the backend's `LICENSE_ONLY_RESOURCES` map (`permission.route-map.ts:429-432`) says exactly that, and its licence key `configuration.chart_of_account_mapping` is locked at the frontend only. It gets no sub-page until an endpoint exists. Conversely, two of this module's wiki sub-pages — [vendor](/en/inventory/master-data/vendor) and [business-unit](/en/inventory/master-data/business-unit) — document entities whose real UI lives outside `/config/*` (`vendor-management/vendor` and the separate `carmen-platform` admin app, respectively); they are kept here as cross-references because inventory documents and the costing engine depend on them, not because their screens live under Configuration → Master Data.

Two principles drive how this umbrella is organised. First, **snapshot semantics**: documents store an FK to a master record *and* a denormalised display copy (name, rate, code) so that historical documents render correctly even if the master record is later renamed or inactivated. Second, **soft-delete with active flag**: every entity uses `is_active` + `deleted_at` to retire records without breaking referential integrity, so the standard answer to "delete X" is "inactivate X".

The umbrella spans both Prisma schemas. Most entities live in the **tenant** schema (the per-property data store), but `business-unit` and `currency-iso` are **platform**-level (shared across tenants), and `currency` is mixed — its ISO reference is platform, its enabled-currencies list and dated rates are tenant.

## 2. Audience

Product Admin and Configurator manage these. Sysadmin oversees integration and RBAC, and is the sole owner of `business-unit` and platform-level `currency-iso` configuration.

## 3. Entity List

| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [unit](/en/inventory/master-data/unit) | Units of measure plus per-product conversions | Product Admin |
| [department](/en/inventory/master-data/department) | Organisational departments and user-to-department mappings | Product Admin / Sysadmin |
| [location](/en/inventory/master-data/location) | Inventory, direct, and consignment locations with count behaviour | Product Admin |
| [delivery-point](/en/inventory/master-data/delivery-point) | Physical drop-off points for vendor deliveries | Product Admin |
| [business-unit](/en/inventory/master-data/business-unit) | The operating unit — owns calculation method and default currency | Sysadmin |
| [currency](/en/inventory/master-data/currency) | Enabled currencies, ISO reference, and dated exchange-rate history | Product Admin / Sysadmin |
| [exchange-rate](/en/inventory/master-data/exchange-rate) | Dated FX rate history feeding document snapshots and costing FX revaluation | Product Admin |
| [vendor](/en/inventory/master-data/vendor) | Suppliers with addresses, contacts, and business-type taxonomy | Product Admin |
| [vendor-business-type](/en/inventory/master-data/vendor-business-type) | Classifies vendors by business type (manufacturer, distributor, service, …) | Product Admin |
| [tax-profile](/en/inventory/master-data/tax-profile) | Named tax rate definitions | Product Admin |
| [credit-term](/en/inventory/master-data/credit-term) | Vendor payment terms (NET 30, COD, etc.) | Product Admin |
| [extra-cost-type](/en/inventory/master-data/extra-cost-type) | GRN landed-cost categories with allocation modes | Product Admin |
| [adjustment-type](/en/inventory/master-data/adjustment-type) | Coded reasons for stock-in / stock-out adjustments | Product Admin |
| [credit-note-reason](/en/inventory/master-data/credit-note-reason) | Coded reasons for credit notes raised against GRN | Product Admin |
| [shelf](/en/inventory/master-data/shelf) | BU-wide shelf master (walk order for counts) assigned per product-location | Product Admin |
| [chart-of-accounts](/en/inventory/master-data/chart-of-accounts) | GL account codes (nature / type / category, file + Carmen GL import) | Sysadmin / Finance |
| [cost-center](/en/inventory/master-data/cost-center) | Cost-center groups, cost centers, and per-center account allow-list — API only | Sysadmin / Finance |

### 3.1 Added since the 2026-07-29 baseline

| Entity | Table (tenant) | Migration | HTTP (gateway) | Bruno | Frontend |
| ------ | -------------- | --------- | -------------- | ----- | -------- |
| Shelf | `tb_location_shelf` | `20260814150000_add_location_shelf` → `20260820120000_rename_location_shelf_to_shelf` (drops `location_id`) → `20260904131500_rename_shelf_and_user_location` (back to `tb_location_shelf`) | `api/config/:bu_code/shelves` | `config/location-shelves/*` (6) | `routes/config/shelf/` |
| Chart of accounts | `tb_chart_of_accounts` + `enum_chart_of_accounts_{nature,type,category,use_in}` | `20260820140000_add_account_code` → `20260827140000_rename_account_code_to_chart_of_accounts` → `20260909170000_gl_core_master` (adds `category`, `is_require_cost_center`, `account_group_id`) | `api/config/:bu_code/chart-of-accounts` (+ `/import`, `/import-from-interface/carmen-gl`) | `config/chart-of-accounts/*` (8) | `routes/config/chart-of-accounts/` |
| Cost center | `tb_cost_center_group`, `tb_cost_center`, `tb_cost_center_account` | `20260904103000_add_cost_center` | `api/config/:bu_code/cost-center-groups`, `api/config/:bu_code/cost-centers` (+ `PUT :id/accounts`) | `config/cost-center-groups/*` (6), `config/cost-centers/*` (7) | none |

### 3.2 Table renames since the baseline

Three junction/master tables were renamed on 2026-09-04 with no column changes; update any query or seed that still uses the old name:

| Old | New | Migration |
| --- | --- | --------- |
| `tb_user_location` | `tb_location_user` | `20260904131500_rename_shelf_and_user_location` |
| `tb_product_master_eco_label` | `tb_eco_label` | `20260904133000_rename_eco_label_and_certificate` |
| `tb_vendor_master_certificate` | `tb_certificate` | `20260904133000_rename_eco_label_and_certificate` |

### 3.3 Default sort on config list endpoints (2026-09-13)

Every master-data `findAll` now passes its `?sort=` through `withDefaultSort()` (`apps/micro-business/src/common/libs/default-sort.ts`): when the caller sends no non-blank sort directive, a per-entity fallback is applied so paging is stable (`id:asc` is always the final tiebreaker). The fallbacks that matter for this module:

| Fallback | Entities |
| -------- | -------- |
| `code:asc, name:asc` | location, department, currency, adjustment-type |
| `code:asc` | vendor, chart-of-accounts, cost-center, cost-center-group, product, product-category / sub-category / item-group |
| `name:asc` | unit, delivery-point, credit-term, extra-cost-type, vendor-business-type, credit-note-reason, eco-label (`product-master-eco-label`), certificate (`vendor-master-certificate`) |
| `name:asc, tax_rate:asc` | tax-profile |
| `sequence_no:asc, code:asc` | shelf |
| `created_at:desc` | exchange-rate and every `*-comment` list |

### 3.4 Entity references are nested objects (2026-09-17)

List and detail responses on the config controllers no longer emit flat `<entity>_id` / `<entity>_name` pairs for their foreign keys; they emit a nested `{ id, name, ... }` object (`@ExpandRefs` / `@Serialize` on the gateway — e.g. exchange-rate rows carry `currency: { id, code, name }`, department detail carries `department_users[].user`, location detail carries `delivery_point`). The frontend types under `types/*.ts` were realigned in the same window (`75244fde`, `b55294b3`, `f8d4026c`). Snapshot columns such as `tb_location.delivery_point_name` still exist in the schema but are no longer what the UI reads.

## 4. Cross-Module Dependencies

- [purchase-request](/en/inventory/purchase-request) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/department](/en/inventory/master-data/department), [master-data/location](/en/inventory/master-data/location), [master-data/vendor](/en/inventory/master-data/vendor), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [master-data/currency](/en/inventory/master-data/currency), [master-data/exchange-rate](/en/inventory/master-data/exchange-rate).
- [purchase-order](/en/inventory/purchase-order) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/vendor](/en/inventory/master-data/vendor), [master-data/currency](/en/inventory/master-data/currency), [master-data/exchange-rate](/en/inventory/master-data/exchange-rate), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [master-data/credit-term](/en/inventory/master-data/credit-term), [master-data/delivery-point](/en/inventory/master-data/delivery-point).
- [good-receive-note](/en/inventory/good-receive-note) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/vendor](/en/inventory/master-data/vendor), [master-data/currency](/en/inventory/master-data/currency), [master-data/exchange-rate](/en/inventory/master-data/exchange-rate), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [master-data/extra-cost-type](/en/inventory/master-data/extra-cost-type), [master-data/credit-note-reason](/en/inventory/master-data/credit-note-reason), [master-data/delivery-point](/en/inventory/master-data/delivery-point), [master-data/location](/en/inventory/master-data/location).
- [store-requisition](/en/inventory/store-requisition) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/location](/en/inventory/master-data/location), [master-data/department](/en/inventory/master-data/department).
- [inventory](/en/inventory/inventory) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/location](/en/inventory/master-data/location), [master-data/business-unit](/en/inventory/master-data/business-unit).
- [inventory-adjustment](/en/inventory/inventory-adjustment) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/location](/en/inventory/master-data/location), [master-data/adjustment-type](/en/inventory/master-data/adjustment-type), [master-data/credit-note-reason](/en/inventory/master-data/credit-note-reason).
- [physical-count](/en/inventory/physical-count) requires [master-data/location](/en/inventory/master-data/location), [master-data/unit](/en/inventory/master-data/unit). It does **not** use [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) — its variance rollup creates stock-in/out rows with `adjustment_type_id` left `null` (confirmed this pass; see the adjustment-type page's Cross-References).
- [spot-check](/en/inventory/spot-check) requires [master-data/location](/en/inventory/master-data/location) only. It does **not** use [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) — it never creates a stock-in/out row at all (confirmed this pass).
- [costing](/en/inventory/costing) requires [master-data/business-unit](/en/inventory/master-data/business-unit) (for `calculation_method`), [master-data/currency](/en/inventory/master-data/currency), and [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) (for dated FX revaluation).
- [vendor-pricelist](/en/inventory/vendor-pricelist) requires [master-data/vendor](/en/inventory/master-data/vendor), [master-data/currency](/en/inventory/master-data/currency), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [templates/price-list](/en/inventory/templates/price-list).
- [product](/en/inventory/product) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/tax-profile](/en/inventory/master-data/tax-profile).
- [recipe](/en/inventory/recipe) requires [master-data/unit](/en/inventory/master-data/unit).
- [physical-count](/en/inventory/physical-count) and [spot-check](/en/inventory/spot-check) can read [master-data/shelf](/en/inventory/master-data/shelf) walk order via the `shelf_*` columns on `tb_product_location`; no count code was found that sorts by it yet (see the shelf page).

### 4.1 General-ledger master (pointer only)

The 2026-09-09 `gl_core_master` migration added GL master tables that live under the same `api/config/:bu_code/*` prefix — `gl-account-groups` (`tb_gl_account_group`), `gl-jv-prefixes` (`tb_gl_jv_prefix`), and `gl-periods` (`tb_gl_period`, deliberately separate from `tb_inventory_period`). They are documented in the [general-ledger](/en/inventory/general-ledger) book section, not here; this module only owns the two entities the GL master depends on — [chart-of-accounts](/en/inventory/master-data/chart-of-accounts) (`account_group_id` → `tb_gl_account_group`) and [cost-center](/en/inventory/master-data/cost-center) (the allow-list JV lines are validated against).

## 5. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`.
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`.
- **Migrations (tenant, since 2026-07-29):** `20260814150000_add_location_shelf`, `20260820120000_rename_location_shelf_to_shelf`, `20260820140000_add_account_code`, `20260827140000_rename_account_code_to_chart_of_accounts`, `20260904103000_add_cost_center`, `20260904131500_rename_shelf_and_user_location`, `20260904133000_rename_eco_label_and_certificate`, `20260909170000_gl_core_master`, `20260909203000_add_vendor_tax_branch_rating`, `20260915120000_po_header_delivery_point`.
- **Default sort:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/libs/default-sort.ts`; per-entity fallbacks in each `master/<entity>/<entity>.service.ts` `findAll`.
- **Licence-only resources:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` (`LICENSE_ONLY_RESOURCES`, `configuration.chart_of_account_mapping`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/{010-department,020-unit,029-business-type,030-extra-cost,031-adjustment-type,032-credit-term,040-currency,041-exchange-rate,042-tax-profile,079-delivery-point,080-location,082-chart-of-accounts,083-shelf}.spec.ts` with gap reports under `docs/test-cases/gaps/` and generated user stories under `docs/user-stories/`.
- **carmen/docs:** `../carmen/docs/settings/locations.md` (referenced by [master-data/location](/en/inventory/master-data/location) only).
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
