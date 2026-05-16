---
title: Application Config
description: Generic key-value application settings — tenant-wide configuration and per-user preference overrides stored as JSONB.
published: true
date: 2026-05-16T08:00:00.000Z
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Config

## 1. Purpose

Application Config is the **generic key-value store** for settings that do not warrant a dedicated schema. Two tables share the same shape: `tb_application_config` holds tenant-wide settings (e.g. the active `tax_profile`, feature flags, default behaviour toggles), and `tb_application_user_config` holds per-user preference overrides (table column order, saved filters, theme preference, default location). Both store the value as JSONB, so any shape — string, number, object, array — works without a migration.

This pattern is the *escape hatch* — small settings that would otherwise pollute the schema as one-column tables live here under a stable key. The trade-off is that the schema does not enforce the value shape — consumers must validate at read-time — so it should not be used for high-volume relational data or anything that needs FKs.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_application_config`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `key` | `String @db.VarChar` | No | Setting key (e.g. `tax_profile`, `default_currency`, `feature.enable_recipe_costing`). |
| `value` | `Json @db.JsonB` | No | Setting value. Default `{}`. Shape is application-defined per key. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([key, deleted_at])` map `application_config_key_u`. Index on `[key]`.

### 2.2 `tb_application_user_config`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | Owner — references the platform `tb_user.id`. |
| `key` | `String @db.VarChar` | No | Preference key (e.g. `pr_list.columns`, `default_location`, `theme`). |
| `value` | `Json @db.JsonB` | No | Preference value. Default `{}`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, key, deleted_at])` map `application_user_config_u`. Index on `[user_id, key]`. No FK to `tb_user` at the tenant schema (`user_id` resolves cross-schema to the platform `tb_user`).

## 3. Usage / Cross-References

- All modules — global config keys gate behaviour across the application (tax-profile selection, default currency, feature flags, working hours).
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]] — per-user preferences (table column order, saved filters, default location) are read on list-view render.
- [[access-control/user]] — `tb_application_user_config.user_id` resolves to the platform user record.
- [[reporting-audit/widget]] — dashboard layouts and saved widget configurations may be persisted here per user as an alternative to the dedicated widget tables.

## 4. Configuration UI

`tb_application_config` is managed by **Sysadmin** under System Configuration → Application Settings. The screen lists known keys with typed editors per key (toggle, dropdown, text, JSON). Unknown keys are shown in a raw-JSON pane for advanced edit.

`tb_application_user_config` is *not* surfaced as a config screen — it is written transparently by client code (e.g. when a user reorders columns or saves a filter). A "Reset my preferences" action under the user-profile menu issues a bulk-delete by `user_id`.

## 5. Business Rules

- **Uniqueness.** `key` is unique among non-deleted rows in `tb_application_config`; `(user_id, key)` is unique among non-deleted rows in `tb_application_user_config`.
- **Schema by convention.** No DB-level shape enforcement on `value`. The application code that consumes a key owns the shape — typically validated via a Zod schema at read-time.
- **Key namespace.** Convention: dotted-namespace keys (`feature.enable_recipe_costing`, `pr_list.columns`) to avoid collisions across modules. Reserved root namespaces: `feature.*`, `default_*`, `<module>.*`.
- **Resolution order.** Per-user value wins over tenant value when both exist for the same logical setting (e.g. `default_currency`).
- **Sensitive values.** Secrets, API keys, and credentials must not be stored here — use environment variables and the platform secrets manager. This store is human-editable and not encrypted at rest beyond standard DB encryption.
- **Deletion.** Hard-delete is fine for tenant-wide rows (the application falls back to compile-time defaults). User rows hard-delete on user removal.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~4910-4924), `tb_application_user_config` (lines ~4926-4941).
- **Seed example:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_application_config.json`.
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/application-config/`.
- **Cross-module:** see Section 3.
