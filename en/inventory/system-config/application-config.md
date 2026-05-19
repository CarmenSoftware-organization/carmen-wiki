---
title: Application Config
description: Generic key-value application settings — tenant-wide configuration and per-user preference overrides stored as JSONB.
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Config

> **At a Glance**
> **Owner:** Sysadmin (tenant) + each user (preferences) &nbsp;·&nbsp; **Table:** `tb_application_config` (+ `tb_application_user_config`) &nbsp;·&nbsp; **Used by:** all modules for feature flags + per-user prefs &nbsp;·&nbsp; Generic JSONB key-value store — the escape hatch for small settings.

## 1. What & Who

Application Config is the **generic key-value store** for settings that do not warrant a dedicated schema. Two tables share the same shape: `tb_application_config` holds tenant-wide settings (e.g. the active `tax_profile`, feature flags, default toggles), and `tb_application_user_config` holds per-user preference overrides (table column order, saved filters, theme, default location). Both store the value as JSONB so any shape — string, number, object, array — works without a migration.

This pattern is the *escape hatch* — small settings that would otherwise pollute the schema as one-column tables live here under a stable key. The trade-off: schema does not enforce shape — consumers must validate at read-time.

**Maintained by** Sysadmin (tenant settings) and end users (preferences, written transparently). **Read by** every list view, every feature-gated path.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Set tenant feature flag | System Config → Application Settings | Typed editor or raw JSON for unknown keys |
| Change tax profile | System Config → Application Settings → `tax_profile` | Drop-down editor |
| Reorder columns (per user) | Drag in any list view | Persisted automatically to `tb_application_user_config` |
| Reset my preferences | User profile menu → Reset my preferences | Bulk-delete by `user_id` |
| Add a new config key | Insert via service code | Convention: dotted namespace |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Key collision on insert | Existing non-deleted row | Update existing or pick different key |
| Value rejected at runtime | Zod schema mismatch | Fix shape per consumer's contract |
| Preference not honoured | User row missing — fell back to tenant | Verify `user_id`+`key` row exists |
| Secret leaked | Stored credentials in config | Move to env / secrets manager — config is human-editable |

## 4. Edge Cases

- **Schema by convention.** No DB-level shape enforcement on `value` — consuming code owns the shape (typically Zod-validated at read-time).
- **Resolution order.** Per-user value wins over tenant value when both exist for the same logical setting.
- **No secrets.** API keys, credentials must NOT be stored here.
- **Hard-delete is fine** for tenant-wide rows (fall back to compile-time defaults).

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_application_config`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `key` | `String @db.VarChar` | No | Setting key (e.g. `tax_profile`, `feature.enable_recipe_costing`). |
| `value` | `Json @db.JsonB` | No | Default `{}`. Shape is application-defined per key. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([key, deleted_at])`. Index on `[key]`.

### 5.2 `tb_application_user_config`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | Owner (cross-schema to platform `tb_user`). |
| `key` | `String @db.VarChar` | No | Preference key (e.g. `pr_list.columns`, `theme`). |
| `value` | `Json @db.JsonB` | No | Default `{}`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, key, deleted_at])`. Index on `[user_id, key]`. No FK to `tb_user` (cross-schema).

## 6. Business Rules

- **Uniqueness.** `key` unique among non-deleted in tenant table; `(user_id, key)` unique in user table.
- **Schema by convention.** Consumers validate shape; no DB-level enforcement.
- **Key namespace.** Dotted-namespace convention (`feature.*`, `default_*`, `<module>.*`).
- **Resolution order.** User wins over tenant for the same logical setting.
- **Sensitive values.** Forbidden — use env / secrets manager.
- **Deletion.** Hard-delete acceptable; app falls back to compile-time defaults.

## 7. Cross-References

- All modules — feature gates and per-user prefs.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check) — list-view prefs.
- [access-control/user](/en/inventory/access-control/user) — `user_id` resolution.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — alternative store for dashboard configs.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~4910-4924), `tb_application_user_config` (lines ~4926-4941).
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_application_config.json`.
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/application-config/`.
