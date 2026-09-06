---
title: Database Pools
description: CRUD registry of shared, platform-managed Postgres connection targets (tb_database_pool) — the single source of tenant database credentials since tb_business_unit.db_connection was physically dropped in favor of database_pool_id + db_schema.
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, database-pools
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Database Pools

> **At a Glance**
> **Module purpose:** Registry of shared, platform-managed database servers that business units point their tenant schema at — the module that owns `tb_database_pool`, the table `tb_business_unit.database_pool_id` was repointed to after `db_connection` was dropped &nbsp;·&nbsp; **Screens:** `DatabasePoolManagement` (list, `/platform/database-pools`) and `DatabasePoolEdit`, used for both create (`/platform/database-pools/new`) and edit (`/platform/database-pools/:id/edit`) &nbsp;·&nbsp; **Nav entry:** `permission: 'database_pool.read'`, group `navGroup.database` (alongside [Platform Migrations](/en/platform/platform-migrations) and `sql_workbench`) &nbsp;·&nbsp; **Feature flag:** `database_pools` &nbsp;·&nbsp; **`superAdminOnly`:** No — gated by ordinary RBAC permissions, not a super-admin flag &nbsp;·&nbsp; **Two-permission model:** `database_pool.read` (list/get, and — see §4 — the **only** permission the frontend route guard checks on all three routes including `/new` and `/:id/edit`) and `database_pool.manage` (create/update/delete, enforced by `<Can>` on every mutating control **and** re-checked inside the submit handler) &nbsp;·&nbsp; **Secrets:** every pool carries a plaintext-in, ciphertext-at-rest `password`; the API masks it as `••••••` in every response and has **no reveal endpoint** anywhere in this codebase &nbsp;·&nbsp; **e2e suite:** **none** — `../carmen-platform-e2e/tests/` has no `database-pools` directory &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

A database pool is a named connection profile to one physical Postgres server — host, port, database name, username, and an encrypted password — that one or more business units share. `DatabasePoolManagement.tsx` (`../carmen-platform/src/pages/DatabasePoolManagement.tsx`, 467 lines) lists every non-deleted pool as a single collapsed **DSN** per row (`username@host:port/database`, built by the shared `poolDsn()` helper) with a one-click copy button, an Active/Inactive badge, and standard audit columns. `DatabasePoolEdit.tsx` (`../carmen-platform/src/pages/DatabasePoolEdit.tsx`, 672 lines) is the same component for both creating a new pool (`/platform/database-pools/new`) and editing an existing one (`/platform/database-pools/:id/edit`); its read mode renders as a plain record (`RecordRow` label/value pairs), not a locked-looking form.

This module exists because `tb_business_unit` no longer stores its own database credentials. Until a migration in `../carmen-turborepo-backend-v2` on 2026-08-13, a business unit's tenant connection lived in its own `db_connection` JSON blob (host/port/database/schema/user/password, including a **plaintext** password). Migration `20260813000000_database_pool_additive` (commit `343b8c16b`) added `tb_database_pool` and the `database_pool_id`/`db_schema` columns on `tb_business_unit` **alongside** the old blob; a one-off backfill script (`packages/prisma-shared-schema-platform/prisma/migrate.database-pool.ts`) deduplicated every business unit's `db_connection` into encrypted pool rows and repointed each BU at one; then migration `20260813010000_database_pool_drop_db_connection` (commit `7f825bb20`) physically dropped the `db_connection` column for good. See [Data Model](/en/platform/database-pools/data-model) §2 for the full field table and §5 for exactly how this page's account of the relationship lines up with [Business Units](/en/platform/business-units) and [Tenant Migrations](/en/platform/tenant-migrations).

## 2. Business Context

Carmen's inventory data for each business unit lives in its own Postgres **schema**, not a wholly separate database or server — a BU's tenant connection is "which pool" (the shared server) plus "which schema" (`db_schema`, unique to that BU) inside it. Before this module existed, every business unit that happened to share a physical database server still duplicated that server's host/port/username/password on its own row — the same credential, encrypted or not, repeated once per tenant. Centralizing the connection into `tb_database_pool` means a credential rotation, a server migration, or a port change is one edit here, applied to every business unit that references the pool, instead of an edit-and-redeploy per business unit.

This also concentrates the one place in the platform schema that holds a live database credential. The password is encrypted at rest (`encryptSecret()`/`decryptSecret()`, `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts`, AES-256-GCM, format `enc:v1:<iv>:<authTag>:<ciphertext>`) under a single environment key, `SECRET_ENCRYPTION_KEY`, that `micro-cluster` (this module's own backend), `micro-business` ([Tenant Migrations](/en/platform/tenant-migrations)' backend), and `micro-notification` must all be configured with identically — a mismatch fails at **decrypt** time, not write time, so a wrong key surfaces as "cannot connect to tenant database" or "cannot send email" rather than as a config error. Both `apps/micro-cluster/src/libs/config.env.ts:99` and `apps/micro-business/src/libs/config.env.ts:98` declare `SECRET_ENCRYPTION_KEY` as a required, non-empty string (`z.string().min(1, ...)`); `crypto.util.ts`'s own `getKey()` throws immediately if the env var is unset, rather than falling back to any built-in value — checked directly in the source, not inferred from its absence. **No hardcoded default credential or key was found anywhere in this module's own encryption path** — this is a materially different situation from a sibling module in this same nav group, [Platform Migrations](/en/platform/platform-migrations) §3.1, whose deploy-token check does fall back to an empty-string default.

## 3. Key Concepts

- **Pool (`tb_database_pool` row)**: One physical Postgres server registration — `host`/`port`/`database`/`username`/`password` — plus an operator-chosen `name`, an optional `description`, an optional `note`, and `is_active`. See [Data Model](/en/platform/database-pools/data-model) §2 for the full field table.
- **DSN display, not five columns**: The list and edit-view pages never show host/port/database/username as separate fields — they compose one string, `username@host:port/database` (`poolDsn()`, `../carmen-platform/src/utils/databasePool.ts`), because those four values are one address, not four independent facts. A per-row **copy** button puts that exact string on the clipboard for pasting into `psql` or a connection tool.
- **`name` vs. the DSN**: A pool's `name` is shown only when it says something the DSN doesn't. `isDerivedName()` (same file) suppresses the name line whenever it is (case-insensitively) identical to the DSN or to `host:port/database` — the case for every pool the legacy backfill auto-created, since those were named after their own connection string.
- **`note`, distinct from `description`**: Both are free-text Prisma columns (`tb_database_pool.description`, `tb_database_pool.note` — `schema.prisma:1387`, `:1398`). `description` is an ordinary operator field. `note` is where the legacy backfill script writes a fixed string — *"Auto-created from `tb_business_unit.db_connection`"* — on every pool it created from an old BU's connection blob, so a later reader knows that record was not hand-configured. The UI renders `note` on the read view whenever set, deliberately not tucked away at the bottom of the record.
- **Password lifecycle**: A create requires a plaintext password (rejected as a validation error if blank); an update may omit it entirely to leave the stored value unchanged, or send a new plaintext value to rotate it. The API never returns the real value — every response masks it as `••••••`, and the update payload builder treats that exact mask string the same as "not sent," so the read-then-write round trip common to every other field on this form cannot accidentally resubmit the mask as a new password.
- **`is_active`**: An inactive pool stays selectable on a business unit that is already bound to it (so the picker on the [Business Units](/en/platform/business-units/ui-screens) Technical tab never silently drops a bound value) but is excluded from the option list when assigning a **new** business unit to a pool.
- **In-use delete protection**: Deleting a pool checks for any non-deleted business unit whose `database_pool_id` still points at it; if any exist, the delete is refused (409, `DATABASE_POOL_IN_USE`) and the error names up to 10 blocking business units by `code`, verbatim in the toast — deliberately not routed through the generic error redactor that would otherwise collapse it to "Please try again later." in production.
- **`doc_version` is required on every update, unconditionally**: Unlike some other entities in this codebase where the optimistic-lock token is only sent when present, `DatabasePoolUpdateDto` requires it on every `PUT`; the backend rejects an update that omits it (`COMMON_DOC_VERSION_REQUIRED`) rather than treating a missing token as "no conflict check requested."
- **Route-level permission is `database_pool.read` on all three routes** — including `/new` and `/:id/edit`. The narrower `database_pool.manage` permission is enforced only inside the page (see §4), not by the route guard.

## 4. Roles and Permissions

| Surface | Gate | Key |
|---|---|---|
| `/platform/database-pools`, `/platform/database-pools/new`, `/platform/database-pools/:id/edit` routes | `PrivateRoute requiredPermission` + `feature` | `database_pool.read` + `database_pools` (`App.tsx:507-527` — **the same single permission on all three routes**, `.manage` is never checked at the route level) |
| Sidebar "Database Pools" entry | `permission` + `feature` filter | `database_pool.read` / `database_pools` (`platformNav.ts:55`) |
| List: Add Pool button (header and empty state) | `<Can>` | `database_pool.manage` |
| List: row Edit/Delete actions menu | `<Can>` wraps the whole `DropdownMenu` | `database_pool.manage` |
| Edit page (existing pool): "Edit" button that flips the record into edit mode | `<Can>` | `database_pool.manage` |
| Edit page (existing pool): Save button in the unsaved-changes bar | `<Can>` | `database_pool.manage` |
| Edit page: `handleSubmit`'s own permission check, independent of the Save button | `hasPermission('database_pool.manage')`, returns early if false | `database_pool.manage` |
| Backend: `GET` (list/one) | `AppIdGuard('database-pool.list'\|'.get')` + `PlatformPermissionGuard` | `database_pool.read` |
| Backend: `POST`/`PUT`/`DELETE` | `AppIdGuard('database-pool.create'\|'.update'\|'.delete')` + `PlatformPermissionGuard` | `database_pool.manage` |

Two things worth calling out precisely, both confirmed by reading the code rather than inferred from the permission names:

1. **A `database_pool.read`-only session can open the *create* form.** Because `/platform/database-pools/new`'s route guard checks only `database_pool.read` (`App.tsx:517`), and `DatabasePoolEdit.tsx` starts a new pool in edit mode unconditionally (`editing = isNew`, not gated on any permission), such a session sees every field of the create form rendered and typeable. It cannot submit it through any path, though: the Save button itself only renders inside `<Can permission="database_pool.manage">`, and `handleSubmit` independently checks `hasPermission('database_pool.manage')` and returns before validating or calling the API — the same defense-in-depth pattern `BusinessUnitEdit.tsx`'s `handleSave` uses, guarding against `Ctrl/Cmd+S` and Enter-inside-a-field bypassing a hidden button. The *existing*-pool edit route has no equivalent exposure: `editing` starts `false` there and can only become `true` via the `<Can>`-gated "Edit" button, so a read-only session sees the record view only.
2. **The backend has no equivalent gap.** Every one of the five REST operations (list, get, create, update, delete) stacks both an `AppIdGuard` (an `x-app-id` allowlist check against a per-operation string like `database-pool.update` — `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/app-id.guard.ts`) and `PlatformPermissionGuard` + `RequirePlatformPermission` for the RBAC key. This is unlike [Business Units](/en/platform/business-units) §4, whose `PUT` endpoint is guarded by `AppIdGuard` alone with no RBAC check stacked on top — that gap does not exist here.

The gateway controller (`PlatformDatabasePoolsController`, `apps/backend-gateway/src/platform/platform_database-pools/platform_database-pools.controller.ts`) does no database work itself — it proxies every call over RPC (`RpcClient` / `@repo/rpc-contract`'s `DatabasePools` message patterns) to `micro-cluster`'s `DatabasePoolController` → `DatabasePoolService` (`apps/micro-cluster/src/cluster/database-pool/`), which is where the Prisma reads/writes, password encryption, and the in-use delete check actually happen.

## 5. Related Modules

- [Business Units](/en/platform/business-units) — every pool's `tb_business_unit[]` relation is the set of BUs currently pointing at it via `database_pool_id`; the BU edit page's Technical tab is the only other screen in the platform that reads a pool's `name` (never its credentials), and is the screen where `db_schema` — the other half of a resolved tenant connection — is set.
- [Tenant Migrations](/en/platform/tenant-migrations) — the module whose `resolveConnection()`/`resolveConnectionForBusinessUnit()` actually dereferences a BU's `database_pool_id` into a live Postgres connection string to run `prisma migrate` against; an inactive or soft-deleted pool is one of the documented ways that resolution fails.
- [Platform Migrations](/en/platform/platform-migrations) — shares this module's `navGroup.database` sidebar group, but migrates the platform's own shared database, not a tenant's; unrelated data paths.
- [Platform RBAC](/en/platform/rbac) — the permission model behind `database_pool.read`/`database_pool.manage`, including how a session that lacks `.manage` still opens (but cannot submit) the create form, per §4.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx:507-527` — the three routes, all three gated on `database_pool.read` only.
- `../carmen-platform/src/components/nav/platformNav.ts:55` — sidebar entry (`permission: 'database_pool.read'`, `groupKey: 'navGroup.database'`, `feature: 'database_pools'`).
- `../carmen-platform/src/pages/DatabasePoolManagement.tsx` — list page, read in full (467 lines).
- `../carmen-platform/src/pages/DatabasePoolEdit.tsx` — create/edit page, read in full (672 lines).
- `../carmen-platform/src/services/databasePoolService.ts` — REST client; masked-password handling comment.
- `../carmen-platform/src/utils/databasePool.ts` — `poolDsn()`, `isDerivedName()`.
- `../carmen-platform/src/components/Can.tsx` — permission-gated render helper referenced throughout §4.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_database-pools/{platform_database-pools.controller.ts,platform_database-pools.service.ts,swagger/request.ts,swagger/response.ts}` — gateway REST surface and RPC proxy.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/app-id.guard.ts` — the `x-app-id` allowlist guard stacked on every route.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/database-pool/{database-pool.controller.ts,database-pool.service.ts}` — the actual CRUD implementation, read in full.
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts:515-517` — `DATABASE_POOL_NOT_FOUND`/`DATABASE_POOL_NAME_EXISTS`/`DATABASE_POOL_IN_USE`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1382-1411` — `model tb_database_pool`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrate.database-pool.ts` — the one-off `db_connection` → pool backfill script, read in full.
- `../carmen-turborepo-backend-v2/packages/secret-crypto/src/crypto.util.ts` — `encryptSecret`/`decryptSecret`, `SECRET_ENCRYPTION_KEY` (fail-closed, no default).
- `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `buildTenantUrl`/`resolveTenantUrl`.
- Verified against `carmen-platform` HEAD `157a65e` (2026-09-04) and `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06).
- `../carmen-platform-e2e/tests/` — listed directly; no `database-pools` directory.

## 7. Pages in This Module

- [Data Model](/en/platform/database-pools/data-model) — the full `tb_database_pool` field table, the encryption/masking lifecycle, the `db_connection` migration history, and an explicit reconciliation with what [Business Units](/en/platform/business-units/data-model) §2.4 and [Tenant Migrations](/en/platform/tenant-migrations/data-model) §3 already say about this table.
- [UI Screens](/en/platform/database-pools/ui-screens) — a tour of `DatabasePoolManagement` (list, filters, CSV export, copy-DSN) and `DatabasePoolEdit` (create form, read-mode record view, edit mode, dialogs), including the read-permission/create-form interaction documented in §4 above.
