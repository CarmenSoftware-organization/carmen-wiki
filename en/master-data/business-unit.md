---
title: Business Unit
description: The legal/operating unit (property or BU) that scopes every transaction — owns calculation method, default currency, and module subscriptions.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, business-unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit

## 1. Purpose

The Business Unit (`tb_business_unit`) is the top-level scope that every transactional document, every user role, and every reporting cut is bound to. In hospitality terms it is usually a *property* (one hotel) inside a *cluster* (the group); a multi-property group has many BUs under one cluster.

Critically, the BU owns the **costing calculation method** (`average` or `fifo` via `enum_calculation_method`) — that single setting drives how every stock movement is valued downstream in the costing engine. The BU also owns the default currency, company/hotel identity fields, format settings (date, time, amount, quantity, perpage, recipe), connection metadata, and module enablement (via the `tb_business_unit_tb_module` link table).

## 2. Prisma Model(s)

Source: platform schema (`packages/prisma-shared-schema-platform/prisma/schema.prisma`). BU is platform-level because users and clusters span tenants.

### 2.1 `tb_business_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cluster_id` | `String @db.Uuid` | No | FK to `tb_cluster`. |
| `code` | `String @db.VarChar(30)` | No | Short BU code. |
| `name` | `String` | No | Display name. |
| `alias_name` | `String? @db.VarChar(10)` | Yes | Short alias used in numbering. |
| `description`, `info` | — | Yes | Free text / JSON metadata. |
| `is_hq` | `Boolean?` | Yes | Marks the headquarters BU in a cluster (default `true`). |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `db_connection`, `config` | `Json?` | Yes | Tenant DB connection / per-BU config blobs. |
| `default_currency_id` | `String? @db.Uuid` | Yes | Default currency (resolved against tenant currency catalogue). |
| `calculation_method` | `enum_calculation_method` | No | `average` (default) or `fifo`. **Source of truth for costing.** |
| `max_license_users` | `Int?` | Yes | License cap. |
| Company info: `branch_no`, `company_name`, `company_address`, `company_email`, `company_tel`, `company_zip_code`, `tax_no` | `String?` | Yes | Legal-entity identity. |
| Hotel info: `hotel_name`, `hotel_address`, `hotel_email`, `hotel_tel`, `hotel_zip_code` | `String?` | Yes | Operating identity. |
| Format settings: `date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format`, `timezone`, `amount_format`, `quantity_format`, `perpage_format`, `recipe_format` | mixed | Yes | UI rendering defaults. `timezone` defaults `Asia/Bangkok`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 2.2 `tb_business_unit_tb_module`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `business_unit_id` | `String @db.Uuid` | No | FK to `tb_business_unit`. |
| `module_id` | `String @db.Uuid` | No | FK to `tb_module`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `(business_unit_id, module_id, deleted_at)`. FKs cascade `NoAction`.

### 2.3 `enum_calculation_method`

```
enum enum_calculation_method {
  average
  fifo
}
```

Note: the same enum name also exists in the tenant schema with values `FIFO` / `AVG`; the platform definition (`average` / `fifo`) is the authoritative one for the BU column.

## 3. Usage / Cross-References

- [[costing]] — reads `calculation_method` per BU to pick the cost-flow rule. Owns the consequences of changing it.
- [[inventory]] — balances and valuation are scoped per BU.
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — every transactional document is BU-scoped.
- [[access-control]] — user-to-BU mapping drives the `x-app-id` header validation and role scope.
- [[reporting-audit]] — reports filter by BU; cluster-level reports roll up BUs.

## 4. Configuration UI

Managed by **Sysadmin** at the platform admin console. Two screens: a BU listing (one row per property in the cluster) and a BU detail screen with tabs for identity, format settings, costing method, module enablement, and currency default.

## 5. Business Rules

- **Uniqueness.** `code` is unique within a cluster (application-enforced); `name` should also be unique.
- **Deletion guards.** A BU with any active users, open documents, or non-zero stock balances cannot be deleted. Soft-delete by setting `deleted_at` only when the BU has been wound down.
- **Validation.** `cluster_id`, `code`, `name`, and `calculation_method` are required.
- **Lifecycle.** `is_active = false` blocks new logins to that BU but preserves all data.
- **`calculation_method` change.** Switching between `average` and `fifo` retro-actively breaks historical valuation. The system should reject mid-period changes and require a period-end snapshot + audit-approved recosting before the switch takes effect.
- **`is_hq` invariant.** Exactly one BU per cluster should carry `is_hq = true` (application invariant).
- **Module enablement.** Removing a module via `tb_business_unit_tb_module` should hide it from the UI but not delete any underlying transactional data.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (lines ~79-144), `tb_business_unit_tb_module` (lines ~146-164), `enum_calculation_method` (lines ~74-77).
- **Frontend route (if known):** `../carmen-platform/src/` (platform admin dashboard).
- **Cross-module:** see Section 3.
