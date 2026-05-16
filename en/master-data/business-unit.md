---
title: Business Unit
description: The legal/operating unit (property or BU) that scopes every transaction — owns calculation method, default currency, and module subscriptions.
published: true
date: 2026-05-17T11:00:00.000Z
tags: master-data, business-unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_business_unit` (platform) &nbsp;·&nbsp; **Used by:** every transactional document &nbsp;·&nbsp; Top-level scope — owns costing method, default currency, and module enablement.

## 1. What & Who

A **Business Unit (BU)** is the top-level scope every document, user role, and report is bound to — usually one **property** (hotel) inside a **cluster** (group). Crucially, the BU owns the **costing calculation method** (`average` or `fifo`) that drives valuation of every stock movement. The BU also owns the default currency, company/hotel identity, format defaults (date, time, money, qty), connection metadata, and module enablement.

**Maintained by** Sysadmin at the platform admin console. **Read by** every backend service (every query is BU-scoped) and the costing engine in particular.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a BU | Platform admin → BU listing → **New** | Required: `cluster_id`, `code`, `name`, `calculation_method` |
| Set default currency | BU detail → Identity tab | Must reference an active row in [[master-data/currency]] |
| Switch costing method | BU detail → Costing tab | Blocked mid-period; requires period-end snapshot + recost — see Edge Cases |
| Enable / disable a module | BU detail → Modules tab | Writes to `tb_business_unit_tb_module`; hides UI but preserves data |
| Mark HQ | Set `is_hq = true` | Exactly one HQ per cluster (app invariant) |
| Deactivate a BU | Toggle `is_active` | Blocks new logins, preserves all data |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use in cluster" | Duplicate `code` within the same `cluster_id` | Pick a different code |
| "Calculation method required" | Form submitted without `average` / `fifo` | Pick one — there is no default |
| "Cannot change calculation method mid-period" | Switch attempted with open postings | Close period, snapshot, recost, then change |
| "Default currency must be active" | `default_currency_id` points to an inactive row | Activate the currency first |
| "Cannot delete BU — active users / open documents / non-zero balances" | Deletion guard | Wind down operations first, then soft-delete |

## 4. Edge Cases

- **Calculation-method switch.** Flipping `average` ↔ `fifo` retro-actively breaks historical valuation. System should reject mid-period and require period-end snapshot + audit-approved recost before activation.
- **`is_hq` invariant.** Exactly one BU per cluster carries `is_hq = true` — app-enforced, not DB.
- **Module disable preserves data.** Removing a module via `tb_business_unit_tb_module` hides UI; underlying transactional data is untouched.
- **Currency inactivation.** A currency that is the BU `default_currency_id` cannot be inactivated.
- **Tenant DB connection.** `db_connection` JSON points the BU at its tenant schema; misconfiguration takes the whole BU offline.

---

## 5. Data Model (Dev)

Source: platform schema (`packages/prisma-shared-schema-platform/prisma/schema.prisma`). BU is platform-level because users and clusters span tenants.

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
| `db_connection`, `config` | `Json?` | Yes | Tenant DB connection / per-BU config blobs. |
| `default_currency_id` | `String? @db.Uuid` | Yes | Default currency (tenant currency catalogue). |
| `calculation_method` | `enum_calculation_method` | No | `average` (default) or `fifo`. **Source of truth for costing.** |
| `max_license_users` | `Int?` | Yes | License cap. |
| Company info: `branch_no`, `company_name`, `company_address`, `company_email`, `company_tel`, `company_zip_code`, `tax_no` | `String?` | Yes | Legal-entity identity. |
| Hotel info: `hotel_name`, `hotel_address`, `hotel_email`, `hotel_tel`, `hotel_zip_code` | `String?` | Yes | Operating identity. |
| Format settings: `date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format`, `timezone`, `amount_format`, `quantity_format`, `perpage_format`, `recipe_format` | mixed | Yes | UI defaults. `timezone` defaults `Asia/Bangkok`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.2 `tb_business_unit_tb_module`

Link table to `tb_module`; index on `(business_unit_id, module_id, deleted_at)`. FKs cascade `NoAction`.

### 5.3 `enum_calculation_method`

```
enum enum_calculation_method {
  average
  fifo
}
```

Note: same enum name in tenant schema uses `FIFO` / `AVG`; the platform definition is authoritative for this column.

## 6. Business Rules

- **Uniqueness.** `code` unique within a cluster (app-enforced); `name` also unique by convention.
- **Deletion guards.** Active users, open documents, or non-zero balances all block deletion.
- **Validation.** `cluster_id`, `code`, `name`, `calculation_method` required.
- **Lifecycle.** `is_active = false` blocks logins, preserves data.
- **Calculation method change** must follow period-close + recost discipline.
- **`is_hq` invariant.** Exactly one HQ per cluster.

## 7. Cross-References

- [[costing]] — reads `calculation_method` per BU.
- [[inventory]] — balances and valuation scoped per BU.
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — every transactional document is BU-scoped.
- [[access-control]] — user-to-BU mapping drives the `x-app-id` header.
- [[reporting-audit]] — reports filter / roll up by BU.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (lines ~79-144), `tb_business_unit_tb_module` (lines ~146-164), `enum_calculation_method` (lines ~74-77).
- **Frontend:** `../carmen-platform/src/` (platform admin dashboard).
