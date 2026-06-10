---
title: Applications — Data Model
description: The tb_application and tb_application_api tables, asymmetric read/write shapes, PUT replace semantics, the generated api-catalog, and the schema-only tb_application_role family.
published: true
date: 2026-06-10T12:30:00.000Z
tags: book/platform, applications, data-model
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications — Data Model

> **At a Glance**
> **Tables:** `tb_application` &nbsp;·&nbsp; `tb_application_api` (1:N grant rows) &nbsp;·&nbsp; **Enums:** none — `api_name` is free-form VarChar &nbsp;·&nbsp; **Identity:** `tb_application.id` (UUID) is the `x-app-id` value; no separate app-id column &nbsp;·&nbsp; **Grant fork:** `allow_all` boolean — when true, `tb_application_api` rows are irrelevant &nbsp;·&nbsp; **Write shape:** asymmetric — read returns flat `api_names: string[]`, writes send `details.add[]` with **replace semantics** &nbsp;·&nbsp; **Catalog:** not a table — a generated file in backend-gateway served by `/api-system/applications/api-catalog`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The Applications module owns two tables. `tb_application` is the client registry: one row per machine caller, holding identity (`name`, `description`), status (`is_active`), and the grant-mode switch (`allow_all`). Its `id` doubles as the credential — the UUID a client must send as the `x-app-id` header — so the row needs no key or secret column of its own.

`tb_application_api` is the explicit grant list: one row per (application, `api_name`) pair. It only matters when the parent's `allow_all` is `false`; with `allow_all = true` the backend's `AppIdGuard` passes without consulting it. There is **no table for the selectable catalog**: the set of valid `api_name` values is a generated TypeScript file in the backend gateway (§5.1), not reference data in Postgres.

Both tables carry the platform-standard audit trio and soft-delete-aware unique constraints (`deleted_at` participates in each `@@unique`), so a deleted application name or a removed grant can be re-created without a key collision.

## 2. Entities

### 2.1 `tb_application`

The registered API client. Schema line 75.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` — **this UUID is the `x-app-id` value** clients send on every request |
| `name` | `String @db.VarChar` | No | Application name; unique among live rows |
| `description` | `String?` | Yes | Optional free-text description |
| `is_active` | `Boolean?` | Yes | Default `true`; Active/Inactive badge in the SPA |
| `allow_all` | `Boolean?` | Yes | Default `false`; `true` grants every guarded endpoint and makes `tb_application_api` rows irrelevant |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id (FK to `tb_user`) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id (FK to `tb_user`) |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `created_by_id` / `updated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([name, deleted_at])` — map `"application_name_deleted_at_u"` — one live row per name; a soft-deleted name can be reused

**Indexes:**
- `@@index([name, deleted_at])` — map `"application_name_deleted_at_idx"`

### 2.2 `tb_application_api`

One explicit API grant: this application may call endpoints guarded by this `api_name`. Schema line 98.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `application_id` | `String @db.Uuid` | No | FK to `tb_application.id` |
| `api_name` | `String @db.VarChar` | No | The granted key, `resource.action` shape (e.g. `cluster.create`); free-form — validity is by convention against the generated catalog, not a DB constraint |
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
tb_application.created_by_id / updated_by_id  ──>  tb_user.id   (audit actors, Prisma FK)
tb_application_api.created_by_id / updated_by_id  ──>  tb_user.id  (audit actors, Prisma FK)
```

That is the entire graph: an application links to nothing but its grant rows and audit actors. There is no relation to clusters, business units, or (beyond audit) users — application identity is platform-global. Note that `onDelete: NoAction` means deleting a `tb_application` row at the database level would not cascade into `tb_application_api`; in practice the platform soft-deletes, so orphan handling is an application-layer concern.

## 4. Enums

This module defines **no enums**. `api_name` is a free-form `VarChar`: the valid vocabulary is open-ended, extended whenever a new `AppIdGuard('...')` call lands in the backend gateway and the catalog is regenerated — no schema change involved. The grant mode is the plain boolean `allow_all`, not a mode enum.

## 5. Divergences from carmen-platform SPA shape

The SPA types live in `../carmen-platform/src/types/index.ts` (`Application`, `ApplicationWritePayload`, `ApiCatalogGroup`); the translation layer is `src/services/applicationService.ts`. The read and write models are deliberately **asymmetric**:

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `Application.api_names: string[]` (flat) | `Application` | `tb_application_api` join rows | The API flattens grant rows into key strings; the SPA never sees grant-row ids |
| `ApplicationWritePayload.details: { add: { api_name }[] }` | `toWritePayload` in `applicationService.ts` | same join rows | Writes wrap each key as `{ api_name }` under `details.add`; entries are trimmed and blanks dropped. **`details` is omitted entirely when `allow_all` is true** |
| `PUT` = **replace semantics** | `applicationService.update` | n/a | Every save sends the full desired set in `details.add` — contrast RBAC roles, whose `PUT` sends `{ add, remove }` deltas. Do not port the delta pattern here (or vice versa) |
| "App ID" field on the edit screen | `ApplicationEdit.tsx` | not a column | Display label for the record `id`; there is no `app_id` column or DTO field |
| `ApiCatalogGroup { module, api_names[] }` | `getApiCatalog` | **no table** | The catalog is `app-api-catalog.generated.ts` in backend-gateway, emitted by the `AppIdGuard` scan (§5.1) |
| Catalog envelope tolerance | `getApiCatalog` | n/a | The endpoint returns `{ api_names: string[], groups?: ApiCatalogGroup[] }`, optionally inside the standard `{ data }` envelope; the service also tolerates a bare `string[]`. When `groups` is missing or fails the per-element runtime guard, the client derives identical groups via `groupApiNames()` (`src/utils/apiCatalog.ts`: module = prefix before the first `.`; dotless names are their own module; `actionOf()` = text after the first dot) — same split rule as the backend generator, so fallback output equals server output |
| Flat `created_at`/`created_by_name` on list rows | `ApplicationManagement.tsx` | audit id columns | The list response may nest audit data as `audit.created/updated` `{ at, name }`; the SPA flattens and tolerates both shapes |

### 5.1 The catalog endpoint and generator

`GET /api-system/applications/api-catalog` serves the contents of `apps/backend-gateway/src/platform/applications/app-api-catalog.generated.ts`, which `scripts/generate-app-api-catalog/run.ts` produces by scanning every `.ts` file under the gateway source for `new AppIdGuard('<api_name>')` calls (regex match), de-duplicating, sorting, and grouping by module. The file exports both the flat `APP_API_CATALOG` and `APP_API_CATALOG_GROUPS`. It must never be hand-edited — regenerate with `bun run scripts/generate-app-api-catalog/run.ts` after adding guards.

### 5.2 Schema-only: the `tb_application_role` family

The platform schema also contains `tb_application_role` (line 31), `tb_application_role_tb_permission` (line 55), and `tb_user_tb_application_role` (line 580). Despite the `application` prefix, they are **not part of this module's machine-client model**: they describe business-unit-scoped role bundles (`tb_application_role.business_unit_id` → `tb_business_unit`) joining `tb_permission` rows to users — an in-product RBAC vocabulary for the inventory application, not grants for `x-app-id` callers. The Platform SPA has **no surface for them** — no page, service, or type references them as of 2026-06-10 — so they are documented here only to disambiguate the naming; no field tables are warranted until a UI exists.

## 6. References

REST surface consumed by `applicationService.ts`:

| Method + Path | Purpose | Notes |
|---|---|---|
| `GET /api-system/applications` | List | Paginated; search fields `name`, `description`; `advance` filter on `is_active`; rows may nest `audit` |
| `POST /api-system/applications` | Create | `details.add` present only when `allow_all` is false |
| `GET /api-system/applications/:id` | Detail | Returns flat `api_names: string[]` |
| `PUT /api-system/applications/:id` | Update | **Replace semantics** — full desired set in `details.add` |
| `DELETE /api-system/applications/:id` | Delete | Reached only from the list row dropdown |
| `GET /api-system/applications/api-catalog` | Selectable `api_name` catalog | `{ api_names, groups? }`, envelope-tolerant; client grouping fallback |

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application` (line 75), `tb_application_api` (line 98); schema-only family at lines 31, 55, 580.
- `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` — the catalog generator (`AppIdGuard` scan, grouping rule, output path).

**Secondary (consumer shape):**
- `../carmen-platform/src/types/index.ts` — `Application`, `ApplicationWritePayload`, `ApiCatalogGroup`.
- `../carmen-platform/src/services/applicationService.ts` — `toWritePayload`, `getApiCatalog` envelope handling and grouping fallback.
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf`, `actionOf`, `groupApiNames`.

**Cross-links:** [Applications landing](/en/platform/applications) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Platform RBAC data-model](../rbac/data-model.md) (the delta-write contrast)
