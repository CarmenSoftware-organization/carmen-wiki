---
title: Applications — Data Model
description: The tb_application, tb_application_api and tb_application_bypass_user tables (incl. service-status and app-secret columns), asymmetric read/write shapes, PUT replace semantics, the generated api-catalog, and the schema-only tb_application_role family.
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, applications, data-model
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications — Data Model

> **At a Glance**
> **Tables:** `tb_application` &nbsp;·&nbsp; `tb_application_api` (1:N grant rows) &nbsp;·&nbsp; `tb_application_bypass_user` (users exempt from maintenance/read-only) &nbsp;·&nbsp; **Enums:** none — `api_name` is free-form VarChar &nbsp;·&nbsp; **Identity:** `tb_application.id` (UUID) is the `x-app-id` value; no separate app-id column &nbsp;·&nbsp; **Grant fork:** `allow_all` boolean — when true, `tb_application_api` rows are irrelevant &nbsp;·&nbsp; **Write shape:** asymmetric — read returns flat `api_names: string[]`, writes send `details.add[]` with **replace semantics** &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` on both tables (added 2026-06-12), enforced as an optimistic lock on `PUT`/`POST` &nbsp;·&nbsp; **Catalog:** not a table — a generated file in backend-gateway served by `/api-system/applications/api-catalog`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The Applications module owns three tables. `tb_application` is the client registry: one row per machine caller, holding identity (`name`, `description`), service status (`status` and its message/until/changed-by columns), the grant-mode switch (`allow_all`), and an optional second credential, the `x-app-secret` (`require_secret`, ciphertext and last-4 columns). Its `id` is the UUID a client must send as the `x-app-id` header; the secret is separate and, unless `require_secret` is on, optional.

`tb_application_bypass_user` lists users who keep full access while their application is in `maintenance` or `read_only` (never in `disabled`).

`tb_application_api` is the explicit grant list: one row per (application, `api_name`) pair. It only matters when the parent's `allow_all` is `false`; with `allow_all = true` the backend's `AppIdGuard` passes without consulting it. There is **no table for the selectable catalog**: the set of valid `api_name` values is a generated TypeScript file in the backend gateway (§5.1), not reference data in Postgres.

`tb_application` and `tb_application_api` carry the platform-standard audit trio and soft-delete-aware unique constraints (`deleted_at` participates in each `@@unique`), so a deleted application name or a removed grant can be re-created without a key collision.

## 2. Entities

### 2.1 `tb_application`

The registered API client. Schema line 65.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` — **this UUID is the `x-app-id` value** clients send on every request |
| `name` | `String @db.VarChar` | No | Application name; unique among live rows |
| `description` | `String?` | Yes | Optional free-text description |
| `is_active` | `Boolean?` | Yes | Default `true`. Legacy flag: the SPA no longer writes it (`toWritePayload` omits it by design) and the API read model derives it from `status` (`isActiveFor(status)`); the SPA reads it only as a fallback when `status` is absent (`statusOf()`) |
| `allow_all` | `Boolean?` | Yes | Default `false`; `true` grants every guarded endpoint and makes `tb_application_api` rows irrelevant |
| `device` | `String @db.VarChar` | No | Default `"web"`; the device class this application identifies as. Free-form at the DB level; the SPA constrains it to `mobile` / `web` / `desktop` / `pos` (`DeviceType` / `DEVICE_OPTIONS`). Read by the backend-gateway app-allowlist (`getDevice(appId)`) to apply device-specific behaviour — e.g. the [GRN mobile draft-only list filter](/en/inventory/good-receive-note/02-business-rules) |
| `status` | `String @db.VarChar` | No | Default `"running"`; one of `running` / `maintenance` / `read_only` / `disabled`. The CHECK constraint lives in the migration, not in Prisma |
| `status_message` | `String?` | Yes | Text shown to callers/users while not running (SPA caps it at 1000 characters) |
| `status_until` | `DateTime? @db.Timestamptz(6)` | Yes | Announced "expected back" time; display-only — nothing switches the status back automatically. The service rejects a non-ISO value |
| `status_changed_at` / `status_changed_by_id` | `DateTime?` / `String? @db.Uuid` | Yes | Who last changed the status and when (FK to `tb_user`; the API returns `status_changed_by_name`) |
| `require_secret` | `Boolean` | No | Default `false`; when true the gateway rejects requests lacking a valid `x-app-secret` (`401 APP_SECRET_INVALID`). CHECK in the migration: only allowed when `secret_ciphertext` is set |
| `secret_ciphertext` | `String?` | Yes | `enc:v1:<iv>:<tag>:<ct>` — AES-256-GCM via `@repo/secret-crypto` with `SECRET_ENCRYPTION_KEY`; decrypted only in micro-cluster. Never sent to the SPA |
| `secret_last4` | `String? @db.VarChar(4)` | Yes | Last four characters of the plaintext, set together with the ciphertext; drives the masked stub and `has_secret` |
| `secret_rotated_at` / `secret_rotated_by_id` | `DateTime?` / `String? @db.Uuid` | Yes | Last generate/rotate (the API returns `secret_rotated_by_name`) |
| `secret_previous_ciphertext` / `secret_previous_expires_at` | `String?` / `DateTime?` | Yes | The pre-rotation secret, still accepted until the expiry (24 h after a rotation, `APP_SECRET_GRACE_MS`); the read model drops an expiry already in the past |
| `doc_version` | `Int` | No | Default `0`; optimistic-concurrency token, added platform-wide (35 tables) on 2026-06-12 (`8e53bbe`). `ApplicationEdit` sends it on every `POST`/`PUT`; a stale write is rejected with `409` and the SPA reloads the record with a conflict toast instead of overwriting silently |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id (FK to `tb_user`) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id (FK to `tb_user`) |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `created_by_id` / `updated_by_id` / `status_changed_by_id` / `secret_rotated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([name, deleted_at])` — map `"application_name_deleted_at_u"` — one live row per name; a soft-deleted name can be reused

**Indexes:**
- `@@index([name, deleted_at])` — map `"application_name_deleted_at_idx"`

### 2.2 `tb_application_bypass_user`

Schema line 112. One row per (application, user) exemption.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `application_id` | `String @db.Uuid` | No | FK to `tb_application.id`, `onDelete: Cascade` |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user.id` |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Who added the row |

`@@unique([application_id, user_id])` (`application_bypass_user_app_user_u`) and `@@index([user_id])`. No `deleted_at`/`doc_version`: the list is replaced wholesale by `PUT …/bypass-users`, which also returns `400` for unknown user ids. The gateway checks it per request (`appAllowlistStore.isBypassUser`).

### 2.3 `tb_application_api`

One explicit API grant: this application may call endpoints guarded by this `api_name`. Schema line 126.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `application_id` | `String @db.Uuid` | No | FK to `tb_application.id` |
| `api_name` | `String @db.VarChar` | No | The granted key, `resource.action` shape (e.g. `cluster.create`); free-form — validity is by convention against the generated catalog, not a DB constraint |
| `doc_version` | `Int` | No | Default `0`; same optimistic-lock counter as `tb_application` above. Not independently surfaced by the SPA — grant rows are always rewritten in bulk via the parent application's replace-semantics `PUT` |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id (FK to `tb_user`) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id (FK to `tb_user`) |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `application_id` → `tb_application.id` (`onDelete: NoAction, onUpdate: NoAction`)
- FK: `created_by_id` / `updated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([application_id, api_name, deleted_at])` — map `"application_api_app_name_deleted_at_u"` — one live grant per (application, key); a removed grant can be re-added

**Indexes:**
- `@@index([application_id, deleted_at])` — map `"application_api_app_deleted_at_idx"` — drives "grants of application X" (the read model's `api_names` flattening and the guard lookup)

## 3. Relationships

```
tb_application  1 ─── M  tb_application_api          (Prisma FK, NoAction/NoAction)
tb_application  1 ─── M  tb_application_bypass_user   (Prisma FK, onDelete Cascade)
tb_application_bypass_user.user_id  ──>  tb_user.id
tb_application.created_by_id / updated_by_id / status_changed_by_id / secret_rotated_by_id  ──>  tb_user.id   (Prisma FK)
tb_application_api.created_by_id / updated_by_id  ──>  tb_user.id  (audit actors, Prisma FK)
```

That is the entire graph: an application links to its grant rows, its bypass users and audit/status/secret actors. There is no relation to clusters or business units — application identity is platform-global. Note that `onDelete: NoAction` means deleting a `tb_application` row at the database level would not cascade into `tb_application_api`; in practice the platform soft-deletes, so orphan handling is an application-layer concern.

## 4. Enums

This module defines **no Prisma enums**; the service status is a plain `VarChar` guarded by a migration CHECK, and the SPA's `ApplicationStatus` union is `'running' | 'maintenance' | 'read_only' | 'disabled'` (`src/types/index.ts`). `api_name` is a free-form `VarChar`: the valid vocabulary is open-ended, extended whenever a new `AppIdGuard('...')` call lands in the backend gateway and the catalog is regenerated — no schema change involved. The grant mode is the plain boolean `allow_all`, not a mode enum. The `device` column is likewise a free-form `VarChar` (default `"web"`), **not** a DB enum: the database accepts any string, while the SPA constrains the value to the fixed set `mobile` / `web` / `desktop` / `pos` via the `DeviceType` union and `DEVICE_OPTIONS`.

## 5. Divergences from carmen-backstage SPA shape

The SPA types live in `../carmen-backstage/src/types/index.ts` (`Application`, `ApplicationWritePayload`, `ApiCatalogGroup`); the translation layer is `src/services/applicationService.ts`. The read and write models are deliberately **asymmetric**:

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `Application.api_names: string[]` (flat) | `Application` | `tb_application_api` join rows | The API flattens grant rows into key strings; the SPA never sees grant-row ids |
| `Application.status*`, `bypass_users[]` (detail only), `has_secret`, `require_secret`, `secret_last4`, `secret_rotated_*`, `secret_previous_expires_at` | `Application` | status/secret columns above | Secret fields are a derived read model: `has_secret` = `secret_last4` present; the plaintext and ciphertext never leave micro-cluster except through the reveal/rotate endpoints. All optional in the type because older backends omit them |
| Status, bypass and secret writes | `updateStatus`, `setBypassUsers`, `rotateSecret`, `revealSecret`, `setSecretEnforcement` | same columns / `tb_application_bypass_user` | **Not part of the `PUT` payload** — each has its own endpoint (§6), so a form save can never take an application down or change its secret as a side effect. `toWritePayload` drops `is_active` for exactly that reason |
| `ApplicationWritePayload.details: { add: { api_name }[] }` | `toWritePayload` in `applicationService.ts` | same join rows | Writes wrap each key as `{ api_name }` under `details.add`; entries are trimmed and blanks dropped. **`details` is omitted entirely when `allow_all` is true** |
| `PUT` = **replace semantics** | `applicationService.update` | n/a | Every save sends the full desired set in `details.add` — contrast RBAC roles, whose `PUT` sends `{ add, remove }` deltas. Do not port the delta pattern here (or vice versa) |
| "App ID" chip on the edit screen | `ApplicationIdentityHero.tsx` (moved out of the form itself since the last sync — no longer a Settings-card field row) | not a column | Display label for the record `id`; there is no `app_id` column or DTO field |
| `doc_version` round-trip | `ApplicationFormData` payload, `getDocVersion`/`isVersionConflict` | `tb_application.doc_version` | New since the last sync — aligned on both sides, not a divergence; listed for completeness since it postdates the original comparison pass |
| `ApiCatalogGroup { module, api_names[] }` | `getApiCatalog` | **no table** | The catalog is `app-api-catalog.generated.ts` in backend-gateway, emitted by the `AppIdGuard` scan (§5.1) |
| Catalog envelope tolerance | `getApiCatalog` | n/a | The endpoint returns `{ api_names: string[], groups?: ApiCatalogGroup[] }`, optionally inside the standard `{ data }` envelope; the service also tolerates a bare `string[]`. When `groups` is missing or fails the per-element runtime guard, the client derives identical groups via `groupApiNames()` (`src/utils/apiCatalog.ts`: module = prefix before the first `.`; dotless names are their own module; `actionOf()` = text after the first dot) — same split rule as the backend generator, so fallback output equals server output |
| `ApplicationSummaryData` (Registry band) | `getRegistrySummary` → `GET /api-system/applications/summary` | n/a — a live aggregate query, not a table | Unfiltered, fleet-wide counts: `total`/`active`/`inactive`/`full_access`/`scoped`/`devices[]`, plus optional `statuses` (count per status) and `secrets` (`enforced` / `unenforced` / `none`) objects that the band renders as extra segments when present, and a `deleted` (soft-deleted, fleet-wide) count that is **on the wire but not rendered** by `ApplicationRegistrySummary` today. Replaced a client-side `perpage: -1` sweep on 2026-08-24 (`99a93c8`, one of 5 pages migrated the same day) |
| API reach (`reachOf()`) | `utils/apiReach.ts`, called by `ApplicationReachCell` (list) and `ApplicationIdentityHero` (edit) | n/a — computed client-side against the loaded catalog | Not a stored fact: `granted`/`anchored`/`full`/`modules`/`percent` are derived on every render from `allow_all`, `api_names`, and the catalog size fetched separately (`getApiCatalog()`). One function feeds both screens so the list and the detail page can never disagree about what counts as "full access" |
| Audit shape read via `normalizeAudit()`/`auditColumns()` | `ApplicationManagement.tsx` (since `a85a166`, 2026-08-22 — this was one of the 5 Management tables migrated off a bespoke `fmt()`) | audit id columns | `normalizeAudit()` tries the **nested** `audit.created`/`audit.updated` shape first and falls back to the **flat** `created_at`/`created_by_name` columns only when nested is absent — not the reverse. The `updated` actor is included only when `everEdited` (an actor name is present, or its `at` differs from `created.at`), not by comparing `updated_at === created_at` |

### 5.1 The catalog endpoint and generator

`GET /api-system/applications/api-catalog` serves the contents of `apps/backend-gateway/src/backstage/applications/app-api-catalog.generated.ts`, which `scripts/generate-app-api-catalog/run.ts` produces by scanning every `.ts` file under the gateway source for `new AppIdGuard('<api_name>')` calls (regex match), de-duplicating, sorting, and grouping by module. The file exports both the flat `APP_API_CATALOG` and `APP_API_CATALOG_GROUPS`. It must never be hand-edited — regenerate with `bun run scripts/generate-app-api-catalog/run.ts` after adding guards.

### 5.2 Schema-only: the `tb_application_role` family

The platform schema also contains `tb_application_role` (line 19), `tb_application_role_tb_permission` (line 44), and `tb_user_tb_application_role` (line 805). Despite the `application` prefix, they are **not part of this module's machine-client model**: they describe business-unit-scoped role bundles (`tb_application_role.business_unit_id` → `tb_business_unit`) joining `tb_permission` rows to users — an in-product RBAC vocabulary for the inventory application, not grants for `x-app-id` callers. The Platform SPA has **no surface for them** — no page, service, or type references them, re-confirmed 2026-07-29 — so they are documented here only to disambiguate the naming; no field tables are warranted until a UI exists. (Note: the generated `api_name` catalog does carry `application-role.*`/`application-role-permission.*`/`application-permission.*` guarded endpoints — these are backend-gateway routes with no client in this SPA, a separate observation from the schema-only tables above; do not conflate the two.)

## 6. References

REST surface consumed by `applicationService.ts`:

| Method + Path | Purpose | Notes |
|---|---|---|
| `GET /api-system/applications` | List | Paginated; search fields `name`, `description`; `advance` filters `status: { in: [...] }` and `device`; rows may nest `audit` |
| `POST /api-system/applications` | Create | `details.add` present only when `allow_all` is false |
| `GET /api-system/applications/:id` | Detail | Returns flat `api_names: string[]` |
| `PUT /api-system/applications/:id` | Update | **Replace semantics** — full desired set in `details.add` |
| `PATCH /api-system/applications/:id/status` | Change service status | Body `{ status, status_message?, status_until?, doc_version? }`; `409 APP_SELF_LOCK` if the target is the caller's own app and `status` is not `running`; permission `application.update` |
| `PUT /api-system/applications/:id/bypass-users` | Replace bypass list | Body `{ user_ids }`; replace semantics; `application.update` |
| `POST /api-system/applications/:id/secret/rotate` | Generate / rotate secret | Returns the new plaintext once; previous stays valid 24 h; `application.secret.manage` |
| `GET /api-system/applications/:id/secret` | Reveal secret | `404` when none; every reveal is audit-logged; `application.secret.reveal` |
| `PATCH /api-system/applications/:id/secret/enforcement` | Turn `require_secret` on/off | Body `{ require_secret, doc_version? }`; `400 APP_SECRET_MISSING`, `409 APP_SECRET_SELF_LOCK`; `application.secret.manage` |
| `DELETE /api-system/applications/:id` | Delete | Reached only from the list row dropdown |
| `GET /api-system/applications/api-catalog` | Selectable `api_name` catalog | `{ api_names, groups? }`, envelope-tolerant; client grouping fallback |
| `GET /api-system/applications/summary` | Registry aggregate for the list's Registry band | Unfiltered — describes the whole registry, not the current search/advance view; no `paginate` block. New since the last sync (was a client-side `perpage: -1` sweep before 2026-08-24) |

Backend commit/PR references above are all in `../carmen-turborepo-backend` or `../carmen-backstage` as already named at each citation; the sections below repeat the primary/secondary split for this page's own reference list.

**Primary (source of truth):**
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `tb_application` (line 65), `tb_application_bypass_user` (line 112), `tb_application_api` (line 126); schema-only family at lines 19, 44, 805. Re-read 2026-10-27 at origin/main: the status columns, secret columns and the bypass table are new since the 2026-09-05 read.
- `../carmen-turborepo-backend/scripts/generate-app-api-catalog/run.ts` — the catalog generator (`AppIdGuard` scan, grouping rule, output path).
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/applications/app-api-catalog.generated.ts` — the generated catalog: 1,140 `api_name` keys across 181 module groups as counted 2026-10-27 (was 900/148 on 2026-09-05).

**Secondary (consumer shape):**
- `../carmen-backstage/src/types/index.ts` — `Application` (incl. `doc_version?: number`), `ApplicationWritePayload`, `ApiCatalogGroup`, `ApplicationSummaryData`, `DeviceCount`.
- `../carmen-backstage/src/services/applicationService.ts` — `toWritePayload` (incl. `doc_version`), `getApiCatalog` envelope handling and grouping fallback, `getRegistrySummary()`.
- `../carmen-backstage/src/utils/apiCatalog.ts` — `moduleOf`, `actionOf`, `groupApiNames`, and (new) `verbOf`/`isAuthorityAction`/`countAuthority`.
- `../carmen-backstage/src/utils/apiReach.ts` — `reachOf()`, the shared reach-arithmetic function behind both the list's `ApplicationReachCell` and the edit page's `ApplicationIdentityHero`.
- `../carmen-backstage/src/utils/audit.ts` — `normalizeAudit()` (nested-first, flat-fallback; `updated` gated on `everEdited`), read by this module's `ApplicationManagement.tsx` list columns since 2026-08-22.
- `../carmen-backstage/src/utils/docVersion.ts` — `getDocVersion`/`isVersionConflict`/`notifyVersionConflict` optimistic-lock helpers used by `ApplicationEdit.tsx`.

**Cross-links:** [Applications landing](/en/backstage/applications) &nbsp;·&nbsp; [UI Screens](/en/backstage/applications/ui-screens) &nbsp;·&nbsp; [Permissions](/en/backstage/applications/permissions) &nbsp;·&nbsp; [Backstage Roles data-model](/en/backstage/rbac/data-model) (the delta-write contrast)
