---
title: Application Config
description: Generic key-value application settings — real, actively-used backing store (config-email, signature settings) consumed key-by-key by specific features, but there is no general Sysadmin browse/edit screen and no permission guard on the read/write endpoints.
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Config

> **At a Glance**
> **Owner:** No one screen — each key is managed by the frontend feature that owns it (e.g. Email Configuration writes `report_email`) &nbsp;·&nbsp; **Table:** `tb_application_config` (+ `tb_application_user_config`) &nbsp;·&nbsp; **Used by:** confirmed real for `report_email` (SMTP) and signature settings; **no generic "Application Settings" admin screen exists** &nbsp;·&nbsp; **No permission guard** on the read/write endpoints beyond basic authentication.

## Implementation status (verified 2026-07-16)

`tb_application_config` is a real, actively-written table — but it is consumed **key-by-key by specific features**, not through a general-purpose Sysadmin editor:

- **No "System Config → Application Settings" screen exists.** There is no `application-config` path in `../carmen-inventory-frontend-react/routes/router.tsx` and no such directory under `routes/system-admin/`. The only frontend consumer is `hooks/use-app-config.ts` (`useAppConfigByKey`, `useUpsertAppConfig`, `useTestEmail`), called by name-specific features: [system-config/config-email](/en/inventory/system-config/config-email) (key `report_email`) and the workflow signature-candidates screen (`signature-config.tsx`). Nothing lets a Sysadmin browse or edit an arbitrary key.
- **No permission guard on the controller.** `config_app-config.controller.ts` applies only `KeycloakGuard` (authentication) at the class level — there is no `AppIdGuard` or `RequirePlatformPermission` decorator on any of its list/get/upsert endpoints (unlike, for example, [system-config/document](/en/inventory/system-config/document)'s controller, which gates every endpoint with a named `AppIdGuard('documents.*')`). The "App ID `app-config.upsert`" gate described lower on this page, and on [system-config/config-email](/en/inventory/system-config/config-email), **is not implemented in the backend** — any authenticated caller with a valid registered `x-app-id` can read and write every tenant-wide config row, including SMTP credentials. Enforcement, if any, exists only as frontend navigation/route-level gating, not a server-side check.

The schema, JSONB shape, and resolution-order description below remain accurate for the rows that are real (`report_email`, `signature-candidates`-adjacent settings); the "Common Tasks" table has been corrected to remove the non-existent general admin screen.

## 1. What & Who

Application Config is the **generic key-value store** for settings that do not warrant a dedicated schema. Two tables share the same shape: `tb_application_config` holds tenant-wide settings (confirmed real usage: the `report_email` SMTP profile, consumed by [system-config/config-email](/en/inventory/system-config/config-email)), and `tb_application_user_config` holds per-user preference overrides (table column order, saved filters, theme, default location) — this second table's actual frontend usage was not independently re-verified in this pass. Both store the value as JSONB so any shape — string, number, object, array — works without a migration.

This pattern is the *escape hatch* — small settings that would otherwise pollute the schema as one-column tables live here under a stable key. The trade-off: schema does not enforce shape — consumers must validate at read-time (confirmed: `report_email` is Zod-validated by `ReportEmailSchema` in `app-config.service.ts`).

**Maintained by** whichever frontend feature owns a given key (no general Sysadmin editor). **Read by** the specific feature that defined the key — not "every list view," which was unconfirmed and has been removed.

## 2. Common Tasks

There is no general editor — only the feature-specific tasks below were confirmed.

| Task | Where | Notes |
|---|---|---|
| Configure outbound SMTP | [system-config/config-email](/en/inventory/system-config/config-email) | Writes `tb_application_config` key `report_email` via `useUpsertAppConfig` |
| Look up signature candidates for a document type | Workflow signature settings (`signature-config.tsx`) | Reads via `useSignatureCandidates`, backed by the same app-config service |
| Add a new tenant-wide key | Backend code change | No admin UI — a new feature must call `useAppConfigByKey`/`useUpsertAppConfig` with its own key and add its own screen |
| Reorder columns (per user) | ~~Drag in any list view~~ | Unconfirmed this pass — not re-verified against `tb_application_user_config` |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Key collision on insert | Existing non-deleted row | Update existing or pick different key |
| Value rejected at runtime | Zod schema mismatch (confirmed for `report_email`'s `ReportEmailSchema`) | Fix shape per consumer's contract |
| Any authenticated user can read/write a config key | No permission guard on `config_app-config.controller.ts` | Confirmed gap — flagged for Task 5/6 follow-up, not fixed by this pass |
| Secret leaked | Stored credentials in config | Move to env / secrets manager — config is human-editable; note `report_email`'s `smtp.password` *is* encrypted at rest (see [system-config/config-email](/en/inventory/system-config/config-email)) |

## 4. Edge Cases

- **Schema by convention.** No DB-level shape enforcement on `value` — consuming code owns the shape.
- **No backend permission check.** Confirmed absent — see Implementation status above.
- **No secrets in plaintext.** `report_email`'s password field is the one confirmed exception that gets encrypted before storage; no other key was confirmed to carry a secret.
- **Hard-delete is fine** for tenant-wide rows (fall back to compile-time defaults) — unconfirmed this pass, carried from prior documentation.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_application_config`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `key` | `String @db.VarChar` | No | Setting key. Confirmed real: `report_email`. |
| `value` | `Json @db.JsonB` | No | Default `{}`. Shape is application-defined per key. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-concurrency token — confirmed used (see `PATCH` payload in [system-config/config-email](/en/inventory/system-config/config-email)). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([key, deleted_at])`. Index on `[key]`.

### 5.2 `tb_application_user_config`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | Owner (cross-schema to platform `tb_user`). |
| `key` | `String @db.VarChar` | No | Preference key. Not independently re-verified this pass. |
| `value` | `Json @db.JsonB` | No | Default `{}`. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-concurrency token. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, key, deleted_at])`. Index on `[user_id, key]`. No FK to `tb_user` (cross-schema).

## 6. Business Rules

- **Uniqueness (schema-level).** `key` unique among non-deleted in tenant table; `(user_id, key)` unique in user table.
- **Schema by convention.** Consumers validate shape at read-time; confirmed for `report_email` via `ReportEmailSchema`.
- **No backend permission check** on `tb_application_config` reads/writes — see Implementation status above.
- **Resolution order, key namespace convention, hard-delete-is-fine** — carried from prior documentation as design intent; not independently re-verified this pass.
- **Sensitive values.** `report_email`'s `smtp.password` is the one confirmed encrypted-at-rest field; no blanket "forbidden" enforcement was found for other keys.

## 7. Cross-References

- [system-config/config-email](/en/inventory/system-config/config-email) — the one confirmed real consumer (`report_email` key).
- Workflow signature settings (`signature-config.tsx`) — confirmed real consumer via `useSignatureCandidates`.
- Other modules' "list-view prefs via `tb_application_user_config`" — not independently re-verified this pass; kept as unconfirmed design intent.
- [access-control/user](/en/inventory/access-control/user) — `user_id` resolution.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — alternative store for dashboard configs.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~5287-5301), `tb_application_user_config` (lines ~5304-5319).
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts`.
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts` — confirmed no `AppIdGuard`/`RequirePlatformPermission` on any route.
- **Frontend:** no general admin screen. Consumers: `../carmen-inventory-frontend-react/hooks/use-app-config.ts` (`useAppConfigByKey`, `useUpsertAppConfig`, `useTestEmail`, `useSignatureCandidates`), used by `routes/system-admin/config-email/` and `routes/system-admin/signature-config.tsx`.
