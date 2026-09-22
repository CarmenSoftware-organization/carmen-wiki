---
title: Application Config
description: Generic key-value settings consumed key-by-key (email profiles, email templates, interface, print/approval-flow configs). Re-verified 2026-09-22: no RBAC guard on the endpoints; licence-gated per key since 2026-09-20.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Config

> **At a Glance**
> **Owner:** No one screen — each key is managed by the frontend feature that owns it (Email Profile writes `email_profiles`, Email Template writes `email_templates`, Interface writes `interface_<category>_<brand>`) &nbsp;·&nbsp; **Table:** `tb_application_config` (+ `tb_application_user_config`) &nbsp;·&nbsp; **Used by:** nine keys with a backend Zod schema (§1.1) plus `email_templates` and the `list_views_*` / signature keys; **no generic "Application Settings" admin screen exists** &nbsp;·&nbsp; **No RBAC permission guard** on the read/write endpoints beyond authentication (re-verified 2026-09-22), except a narrow BU-admin check on `list_views_*` keys; since 2026-09-20 the **licence** layer gates three key groups separately (`configuration.email_profile`, `configuration.email_template`, `interface`).

## Implementation status (verified 2026-07-16; re-verified 2026-09-06 and 2026-09-22)

**2026-09-22 re-read of `config_app-config.controller.ts` at HEAD.** Class-level `@UseGuards(KeycloakGuard)` at `:56` is still the only guard. Routes: `GET` (`:72`), `GET :key` (`:105`), `PUT :key` (`:141`), `DELETE :key` (`:224`), `GET signature-candidates/:doc_type` (`:305`), `POST test-email` (`:353`), `POST test-email-profile` (`:395`, new 2026-08 — sends a test mail through one named sender profile, optional `to`). No `AppIdGuard`, no `@Permission`, no `RequirePlatformPermission` on any of them; `assertSharedListViewsAdmin()` (`:264`) is still called only from `PUT :key` (`:210`) and `DELETE :key` (`:245`) and still returns early for every key not matching `/^list_views_/`. **The PR #10 finding (any authenticated caller can read and write every tenant-wide config row) still stands** — but two layers were added around it that change what a caller can *reach*:

1. **Licence gating per key (2026-09-20, `84667a405`).** The global `LicenseInterceptor` resolves every request URL to a licence feature. `config:app-config` maps to `configuration.app_config` (which every BU holds), but `LICENSE_ROUTE_OVERRIDES` (`packages/prisma-shared-schema-platform/prisma/permission.route-map.ts:257-268`) re-maps `…/app-config/email_profiles` and `…/app-config/test-email-profile` → `configuration.email_profile`, `…/app-config/email_templates` → `configuration.email_template`, and the eight `…/app-config/interface_<category>_<brand>` keys → `interface`. A BU whose contract lacks the feature gets `403 LICENSE_REQUIRED` (or `LICENSE_EXPIRED` on writes) with `bu_codes`/`bu_names` in the body (`c7a0d9168`). This is a **licence** check (does the BU own the feature), not an RBAC check (may this user act) — it does not close the finding.
2. **List endpoint hides the split keys (2026-09-20, `9c52288c0`, `5ff86e322`).** `GET /app-config` now filters out `email_profiles`, `email_templates`, and any `interface_*` key (`config_app-config.service.ts:198` `isListExcluded`) so the list cannot be used to read them under the generic feature; each is readable only through `GET /app-config/:key`, which the override table covers. The service also runs `assertInterfaceEntitled()` for `interface_*` keys. Internal callers of the gateway service (e.g. `EmailLookupService`) bypass the per-key licence gate by design — the module's own comment says so.

The rest of the 2026-09-06 findings below are unchanged.

`tb_application_config` is a real, actively-written table — but it is consumed **key-by-key by specific features**, not through a general-purpose Sysadmin editor:

- **No "System Config → Application Settings" screen exists.** There is no `application-config` path in `../carmen-inventory-frontend-react/routes/router.tsx` and no such directory under `routes/system-admin/`. Frontend consumers go through `hooks/use-app-config.ts` (`useAppConfigByKey`, `useAppConfigs`, `useUpsertAppConfig`, `useTestEmail`) or their own hooks (`hooks/use-email-profiles.ts`, `hooks/use-email-templates.ts`, `routes/system-admin/interface/use-interface-config.ts`), each pinned to one key: [system-config/config-email](/en/inventory/system-config/config-email) (`email_profiles`, `email_templates`; the older `report_email` screen still exists in `routes/system-admin/config-email/` but is **no longer routed** — no `config-email` entry in `router.tsx` or `constant/module-list.ts` at HEAD), `/system-admin/interface` (`interface_*`), and the workflow signature settings. Nothing lets a Sysadmin browse or edit an arbitrary key.
- **No permission guard on the controller — re-verified 2026-09-06, still open.** `config_app-config.controller.ts` applies only `@UseGuards(KeycloakGuard)` (authentication) at the class level (`:46`); there is no `AppIdGuard` or `RequirePlatformPermission` decorator on any route (unlike, for example, [system-config/document](/en/inventory/system-config/document)'s controller, which gates every endpoint with a named `AppIdGuard('documents.*')`). Also checked and ruled out this pass: no `APP_GUARD` in the gateway's `app.module.ts` other than the rate-limiting throttler — whose own comment states it is orthogonal to authorization — and no guard registered in `config_app-config.module.ts`. **Any authenticated caller can read and write every tenant-wide config row, including SMTP credentials.**

  There is no `x-app-id` fallback: `@ApiHeaderRequiredXAppId()` declares the header for Swagger only, and no `AppIdGuard` exists here. Earlier wording on this page implying a "valid registered `x-app-id`" was required has been corrected — authentication is the only bar.

  **One exception, added since this page was written:** commit `1b76f2caa` (2026-07-29) added `assertSharedListViewsAdmin()` (`:256-287`), called from `PUT :key` (`:202`) and `DELETE :key` (`:237`). It requires a **BU-level `admin`** role for the target `bu_code`, but only for keys matching `/^list_views_/` (`:262`) — every other key returns early, unchecked. `GET`, `GET :key`, `signature-candidates` and `POST test-email` have no check at all. The role is read from the `x-bu-datas` header, which `KeycloakGuard` overwrites on every authenticated request (`keycloak.guard.ts:192`, `:211`, `:301`, `:327`), so it is not client-spoofable and fails closed when absent.

  The "App ID `app-config.upsert`" gate described lower on this page, and on [system-config/config-email](/en/inventory/system-config/config-email), **is not implemented in the backend.** Enforcement, if any, exists only as frontend navigation/route-level gating, not a server-side check.

The schema, JSONB shape, and resolution-order description below remain accurate for the rows that are real (`report_email`, `signature-candidates`-adjacent settings); the "Common Tasks" table has been corrected to remove the non-existent general admin screen.

## 1. What & Who

Application Config is the **generic key-value store** for settings that do not warrant a dedicated schema. Two tables share the same shape: `tb_application_config` holds tenant-wide settings (confirmed real usage: the `report_email` SMTP profile, consumed by [system-config/config-email](/en/inventory/system-config/config-email)), and `tb_application_user_config` holds per-user preference overrides (table column order, saved filters, theme, default location) — this second table's actual frontend usage was not independently re-verified in this pass. Both store the value as JSONB so any shape — string, number, object, array — works without a migration.

This pattern is the *escape hatch* — small settings that would otherwise pollute the schema as one-column tables live here under a stable key. The trade-off: schema does not enforce shape — consumers must validate at read-time (confirmed: `report_email` is Zod-validated by `ReportEmailSchema` in `app-config.service.ts`).

**Maintained by** whichever frontend feature owns a given key (no general Sysadmin editor). **Read by** the specific feature that defined the key — not "every list view," which was unconfirmed and has been removed.

### 1.1 Key registry at HEAD (verified 2026-09-22)

`AppConfigService.validateValue()` (`apps/micro-business/src/app-config/app-config.service.ts:488-500`) is the closest thing to a schema registry. Keys with a backend Zod schema:

| Key | Schema | Secret path (encrypted at rest, masked `***ENCRYPTED***` on read) | Owning screen / feature |
|---|---|---|---|
| `report_email` | `ReportEmailSchema` | `smtp.password` | legacy single-SMTP config (unrouted screen); `getReportEmailForSend` |
| `email_profiles` | `EmailProfilesSchema` (`{ default_profile_id, profiles[] }`) | `profiles.*.smtp.password` (wildcard — restored by id, not by index, `49162675a`) | `/system-admin/email-profile`; `getEmailProfileForSend` (PO / RFP email) |
| `gl_setting` | `GlSettingSchema` | — | GL module (out of scope) |
| `pr_approval_flow`, `po_approval_flow` | `ApprovalFlowSchema` | — | PR / PO approval-stage candidates (`min_required_last_n`) |
| `pr_print_config`, `po_print_config`, `grn_print_config`, `sr_print_config` | `PrintConfigSchema` | — | print layer |
| `interface_accounting_carmen_gl` | `InterfaceAccountingCarmenGlSchema` | `authorize_token` | `/system-admin/interface` |
| `interface_accounting_<brand>` (blueledgers, external) | `InterfaceAccountingSchema` | — | `/system-admin/interface` |
| `interface_pos_<brand>`, `interface_pms_<brand>` | `InterfacePosSchema` / `InterfacePmsSchema` (matched by pattern) | `api_key` | `/system-admin/interface` |

`email_templates` (`{ defaults, templates[] }`, seeded by `packages/prisma-shared-schema-tenant/src/seed-data/email-templates.ts`) has **no entry in `schemaByKey`** — the backend stores whatever the client sends; HTML bodies are sanitised on the frontend only (`sanitizeEmailHtml`, `types/email-template.ts`). Signature settings (`signature-candidates/:doc_type`) and `list_views_*` are read/written without a schema too.

## 2. Common Tasks

There is no general editor — only the feature-specific tasks below were confirmed.

| Task | Where | Notes |
|---|---|---|
| Manage SMTP sender profiles | `/system-admin/email-profile` — see [system-config/config-email](/en/inventory/system-config/config-email) | `PUT /app-config/email_profiles`; test one profile with `POST /app-config/test-email-profile` `{ profile_id, to? }` |
| Manage the outgoing email message library | `/system-admin/email-template` — see [system-config/config-email](/en/inventory/system-config/config-email) | `PUT /app-config/email_templates` |
| Configure an accounting / POS / PMS interface | `/system-admin/interface/:category/:brand` (`interface-registry.ts`) | `PUT /app-config/interface_<category>_<brand>`; licence-only (`interface` feature from the BU's INF licence), no permission key |
| Look up signature candidates for a document type | Workflow signature settings | `GET /app-config/signature-candidates/:doc_type` |
| Read / save a per-user preference | `GET` / `PUT api/config/:bu_code/app-user-config/:key` (`config_app-user-config.controller.ts:54,89`; Bruno `config/app-user-config/{GET-get,PUT-upsert}`) | Backed by `tb_application_user_config`; which screens use it was not traced this pass |
| Add a new tenant-wide key | Backend code change | Add a schema to `validateValue()` (and a secret path if needed), then a feature screen — there is no admin UI |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Key collision on insert | Existing non-deleted row | Update existing or pick different key |
| Value rejected at runtime | Zod schema mismatch (confirmed for `report_email`'s `ReportEmailSchema`) | Fix shape per consumer's contract |
| Any authenticated user can read/write a config key | No RBAC guard on `config_app-config.controller.ts` | **Confirmed gap — still open, re-verified 2026-09-22.** Only `list_views_*` keys are protected, and only on `PUT`/`DELETE`; the 2026-09-20 licence split gates *which BU* may reach `email_profiles` / `email_templates` / `interface_*`, not *which user* |
| `403 LICENSE_REQUIRED` / `LICENSE_EXPIRED` on `GET`/`PUT /app-config/email_profiles`, `/email_templates`, `/interface_*` | BU's contract lacks `configuration.email_profile` / `configuration.email_template` / `interface` (INF licence) | Buy / renew via the Platform; `GET /api/license` shows `features[]` / `expired_features[]` per BU |
| `GET /app-config` omits `email_profiles`, `email_templates`, `interface_*` | Expected since `9c52288c0` — read them by key | Use `GET /app-config/:key` |
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
| `key` | `String @db.VarChar` | No | Setting key. Confirmed real: see §1.1. |
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
- **Sensitive values.** Encrypted-at-rest paths are enumerated in `secretPathsFor()` (`:216-225`): `report_email.smtp.password`, `email_profiles.profiles[*].smtp.password`, `interface_accounting_carmen_gl.authorize_token`, `interface_pos_*` / `interface_pms_*` `.api_key`. A blank or masked value posted back keeps the stored secret (`3580f5142`); clearing a secret is done with `enabled: false`, not an empty string. No blanket "forbidden" enforcement exists for other keys.
- **Licence, not permission, per key group.** `configuration.app_config` covers the generic routes; `configuration.email_profile`, `configuration.email_template`, and `interface` cover their key groups (2026-09-20). RBAC resource `configuration.app_config` exists in `tb_permission` but no route in this controller checks it.

## 7. Cross-References

- [system-config/config-email](/en/inventory/system-config/config-email) — `email_profiles` + `email_templates` (and the legacy `report_email`).
- `/system-admin/interface` (no wiki page yet) — `interface_*` keys, licence-only.
- Workflow signature settings — consumer of `signature-candidates/:doc_type`.
- Other modules' "list-view prefs via `tb_application_user_config`" — not independently re-verified this pass; kept as unconfirmed design intent.
- [access-control/user](/en/inventory/access-control/user) — `user_id` resolution.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — alternative store for dashboard configs.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~5287-5301), `tb_application_user_config` (lines ~5304-5319).
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/app-config/app-config.service.ts`.
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-config/config_app-config.controller.ts` — re-read 2026-09-22: class-level `KeycloakGuard` (`:56`) only; sole authorization is `assertSharedListViewsAdmin()` (`:264`), scoped to `list_views_*`. Gateway service `config_app-config.service.ts` (`isListExcluded` `:198`, `assertInterfaceEntitled` `:94`).
- **Licence layer:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` (`LICENSE_ROUTE_OVERRIDES` `:257-268`); `apps/backend-gateway/src/license/{license.interceptor,license-route-resolver,license.evaluator}.ts`; `GET /api/license` (`license.controller.ts:40`).
- **Per-user config:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_app-user-config/config_app-user-config.controller.ts`; Bruno `config/app-user-config/`.
- **Frontend:** no general admin screen. Consumers: `../carmen-inventory-frontend-react/hooks/use-app-config.ts`, `hooks/use-email-profiles.ts`, `hooks/use-email-templates.ts`, `routes/system-admin/interface/use-interface-config.ts`; screens `routes/system-admin/email-profile/`, `routes/system-admin/email-template/`, `routes/system-admin/interface/`. `routes/system-admin/config-email/` still exists on disk but has no route.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/app-config/POST-test-email-profile-config-app-config.bru`, `config/app_config/`.
