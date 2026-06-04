---
title: Master Data
description: Business master data referenced by transactional documents — units, departments, vendors, currencies, tax profiles, and related catalogs.
published: true
date: 2026-05-19T23:55:00.000Z
tags: master-data, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Master Data

> **At a Glance**
> **Module purpose:** Catalogue of named records (units, vendors, currencies, locations, tax profiles, reason codes) that transactional documents reference via FK + denormalised snapshot &nbsp;·&nbsp; **Audience:** Product Admin, Configurator, Sysadmin &nbsp;·&nbsp; **Key entities/tables:** `tb_unit`, `tb_vendor`, `tb_currency` + `tb_exchange_rate`, `tb_tax_profile`, `tb_location` &nbsp;·&nbsp; **Sub-pages:** 14

![Master Data screen](/screenshots/master-data/index.png)

## 1. Overview

Master data is the set of named records that transactional documents *reference* but do not own. Units, departments, locations, delivery points, business units, currencies, vendors, tax profiles, credit terms, extra-cost types, adjustment types, credit-note reasons, and pricelist templates all live here. Each one is small on its own, and each one is referenced by many transactional rows.

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

## 4. Cross-Module Dependencies

- [purchase-request](/en/inventory/purchase-request) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/department](/en/inventory/master-data/department), [master-data/location](/en/inventory/master-data/location), [master-data/vendor](/en/inventory/master-data/vendor), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [master-data/currency](/en/inventory/master-data/currency), [master-data/exchange-rate](/en/inventory/master-data/exchange-rate).
- [purchase-order](/en/inventory/purchase-order) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/vendor](/en/inventory/master-data/vendor), [master-data/currency](/en/inventory/master-data/currency), [master-data/exchange-rate](/en/inventory/master-data/exchange-rate), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [master-data/credit-term](/en/inventory/master-data/credit-term), [master-data/delivery-point](/en/inventory/master-data/delivery-point).
- [good-receive-note](/en/inventory/good-receive-note) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/vendor](/en/inventory/master-data/vendor), [master-data/currency](/en/inventory/master-data/currency), [master-data/exchange-rate](/en/inventory/master-data/exchange-rate), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [master-data/extra-cost-type](/en/inventory/master-data/extra-cost-type), [master-data/credit-note-reason](/en/inventory/master-data/credit-note-reason), [master-data/delivery-point](/en/inventory/master-data/delivery-point), [master-data/location](/en/inventory/master-data/location).
- [store-requisition](/en/inventory/store-requisition) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/location](/en/inventory/master-data/location), [master-data/department](/en/inventory/master-data/department).
- [inventory](/en/inventory/inventory) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/location](/en/inventory/master-data/location), [master-data/business-unit](/en/inventory/master-data/business-unit).
- [inventory-adjustment](/en/inventory/inventory-adjustment) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/location](/en/inventory/master-data/location), [master-data/adjustment-type](/en/inventory/master-data/adjustment-type), [master-data/credit-note-reason](/en/inventory/master-data/credit-note-reason).
- [physical-count](/en/inventory/physical-count) requires [master-data/location](/en/inventory/master-data/location), [master-data/unit](/en/inventory/master-data/unit), [master-data/adjustment-type](/en/inventory/master-data/adjustment-type).
- [spot-check](/en/inventory/spot-check) requires [master-data/location](/en/inventory/master-data/location), [master-data/adjustment-type](/en/inventory/master-data/adjustment-type).
- [costing](/en/inventory/costing) requires [master-data/business-unit](/en/inventory/master-data/business-unit) (for `calculation_method`), [master-data/currency](/en/inventory/master-data/currency), and [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) (for dated FX revaluation).
- [vendor-pricelist](/en/inventory/vendor-pricelist) requires [master-data/vendor](/en/inventory/master-data/vendor), [master-data/currency](/en/inventory/master-data/currency), [master-data/tax-profile](/en/inventory/master-data/tax-profile), [templates/price-list](/en/inventory/templates/price-list).
- [product](/en/inventory/product) requires [master-data/unit](/en/inventory/master-data/unit), [master-data/tax-profile](/en/inventory/master-data/tax-profile).
- [recipe](/en/inventory/recipe) requires [master-data/unit](/en/inventory/master-data/unit).

## 5. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`.
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`.
- **carmen/docs:** `../carmen/docs/settings/locations.md` (referenced by [master-data/location](/en/inventory/master-data/location) only).
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
