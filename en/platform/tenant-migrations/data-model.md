---
title: Tenant Migrations — Data Model
description: There is no persisted migration-status entity — every state on this screen is derived live from tb_business_unit.db_schema plus the linked tb_database_pool row, by shelling out to the Prisma CLI against the resolved tenant connection and parsing its text output.
published: true
date: '2026-09-06T19:00:00.000Z'
tags: book/platform, tenant-migrations, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Tenant Migrations — Data Model

> **At a Glance**
> **No dedicated table.** Nothing in `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` tracks migration status, runs, or history — every state this module shows is computed on demand by running the Prisma CLI against the target tenant database and parsing its text output (§2) &nbsp;·&nbsp; **Connection resolution** reads two existing tables, not a migration-specific one: `tb_business_unit.db_schema` + the linked `tb_database_pool` row's host/port/database/username/decrypted-password (§3) &nbsp;·&nbsp; **Bookkeeping of what has/hasn't applied lives in Prisma's own `_prisma_migrations` table, inside each tenant schema** — not in the platform database this wiki otherwise documents, and not queried directly by this codebase outside of the `prisma migrate` CLI itself &nbsp;·&nbsp; **No optimistic lock, no persisted run history** — concurrency is enforced only by in-memory `Set`/boolean flags that reset on every process restart (§5)

> **Source of truth:** read these before updating this page.
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (line 176), `tb_database_pool` (line 1382)
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `resolveConnection()`, `status()`, `deployResolved()`, `runBuStream()`, `deployAllStream()`, `resolve()`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit()`
> - `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `resolveTenantUrl()`, `buildTenantUrl()`
>
> Verified against `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) and `carmen-platform` HEAD `157a65e` (2026-09-04).

## 1. Overview

This is the one module in the Platform book where "data model" is mostly an answer to *what isn't there*. There is no `tb_tenant_migration` table, no run log, no per-BU "last migration status" column — the entire screen (and the per-BU `TenantMigrationCard`, [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.5) works by resolving a business unit's own tenant-database connection string, shelling out to the Prisma CLI against it, and parsing whatever that CLI prints. The only durable state involved lives in two places neither of which this module owns: `tb_business_unit`/`tb_database_pool` in the **platform** schema (which merely locate the tenant database) and Prisma's own `_prisma_migrations` bookkeeping table inside **each tenant schema** (which Prisma itself creates and maintains, and which this codebase never reads or writes directly — only through the `prisma migrate` CLI).

## 2. No dedicated entity — state is derived, not stored

`status(bu_id)` (`tenant_migration.service.ts`) runs `prisma migrate status --schema <schema>` against the resolved connection (§3) and classifies the combined stdout+stderr by regex:

| Field returned to the frontend | How it is computed |
|---|---|
| `up_to_date` | `/up to date/i` matched against the CLI output |
| `has_pending` | `/not yet been applied/i` matched against the CLI output |
| `pending` | Every `\d{14}_[a-z0-9_]+` match in the same output, deduplicated |
| `raw` | The full output, with any `postgres(ql)://...` connection string or `DATABASE_URL=...` value redacted (`sanitize()`) |

None of this is written anywhere — the next `status` call recomputes it from scratch. A `deploy`/`deployStream` call is the same shape: `prisma migrate deploy` is run, its `Applying migration \`name\`` lines are parsed to build the "applied" list streamed to the UI, and the result (success/failure, applied names) is returned once and not persisted. The only thing that remembers a migration was applied is Prisma's own `_prisma_migrations` table inside the tenant schema itself — outside this module's (and this wiki's) scope beyond the fact that it exists and is what `migrate status`/`migrate deploy`/`migrate resolve` all read and write.

## 3. Resolving a tenant connection: `tb_business_unit` + `tb_database_pool`

`resolveConnection(bu_id)` (`tenant_migration.service.ts`) looks up one `tb_business_unit` row and its joined pool, then calls `resolveConnectionForBusinessUnit()` (`tenant.service.ts`), which throws rather than returns a connection string when any of the following holds:

| Condition checked | Thrown message (sanitized, reaches the frontend verbatim) |
|---|---|
| `tb_business_unit.database_pool_id` is null → no `tb_database_pool` join | `Business unit {code} is not linked to a database pool` |
| `tb_business_unit.db_schema` is null | `Business unit {code} has no database schema configured` |
| The joined `tb_database_pool.deleted_at` is set (soft-deleted) | `Database pool '{name}' used by business unit {code} has been deleted` |
| The joined `tb_database_pool.is_active` is false | `Database pool '{name}' used by business unit {code} is inactive` |
| `tb_database_pool.password` fails to decrypt (`decryptSecret()`, `@repo/secret-crypto`) | `Failed to decrypt the database pool password (check SECRET_ENCRYPTION_KEY...)` |

Relevant fields, `tb_business_unit` (`schema.prisma:176`):

| Field | Prisma Type | Nullable | Role here |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | The `bu_id` path parameter on every endpoint in this module |
| `code` | `String @db.VarChar(30)` | No | Named in every error message and audit-log entry; also the row link target back to `/business-units/:id/edit` |
| `database_pool_id` | `String? @db.Uuid` | **Yes** | FK to `tb_database_pool`; null means the BU was never pointed at a pool |
| `db_schema` | `String? @db.VarChar` | **Yes** | The tenant's own Postgres schema name inside that pool's database |
| `tb_database_pool` (relation) | `tb_database_pool?` | — | `onDelete: NoAction` — the pool row is never cascade-deleted; a pool with dependents can still be soft-deleted, which is exactly the "has been deleted" case above |

Relevant fields, `tb_database_pool` (`schema.prisma:1382`) — the shared, platform-managed connection target multiple BUs can point at:

| Field | Prisma Type | Nullable | Role here |
|---|---|---|---|
| `host`, `port`, `database`, `username` | `String`/`Int` | No | Fed into `buildTenantUrl()` verbatim (host/port validated by `isSafeHost`/`isSafePort`; the rest percent-encoded) |
| `password` | `String @db.VarChar` | No | Ciphertext from `encryptSecret()`; decrypted per-request by `resolveTenantUrl()`, never returned to any client |
| `is_active` | `Boolean @default(true)` | No | Checked explicitly in `resolveConnection()` even though the relation is to-one — a to-one Prisma relation still returns a soft-deleted/inactive row by default |
| `deleted_at` | `DateTime?` | Yes | Soft-delete marker, checked the same way |

The resulting URL (`buildTenantUrl()`, `@repo/db-connection-utils`): `postgresql://{user}:{password}@{host}:{port}/{database}?schema={db_schema}` — a single Postgres server hosting one physical database per pool, with each BU's tenant data isolated into its own named schema inside it via the `?schema=` query parameter, not a separate database per BU.

## 4. Concurrency: in-memory only

`TenantMigrationService` (micro-business) holds two fields that exist only for the life of the process: `runningBuIds: Set<string>` (one BU at a time) and `isBatchRunning: boolean` (one fleet-wide batch at a time). Both are checked before a `deploy`/`deployStream`/`resolve` call proceeds and return `ALREADY_EXISTS` / a 409 "already running" when held; both are cleared in a `finally` block on every path, including a client disconnect that leaves the underlying `prisma migrate deploy` child process still running (§3.3 on the [landing page](/en/platform/tenant-migrations)). **A process restart of micro-business silently drops both locks** — if a `prisma migrate deploy` child process were somehow still running across a restart (its own timeout, `TENANT_MIGRATION_TIMEOUT_MS`, defaults to 120000ms and would normally prevent this), nothing would remember the lock had been held.

## 5. Edge Cases

| Scenario | What actually happens | Source |
|---|---|---|
| A BU has no `database_pool_id` or `db_schema` set yet | `resolveConnection` throws "not linked to a database pool" / "has no database schema configured"; on the fleet table this surfaces as a per-row error on Check (no pre-check, unlike the per-BU card's `hasDbConnection` gate) | `tenant.service.ts` |
| A BU's linked pool is soft-deleted or `is_active: false` | Same error path, "has been deleted" / "is inactive" — a pool being retired silently breaks migrations for every BU still pointing at it until they are repointed | `tenant.service.ts` |
| `prisma migrate deploy` fails partway through a batch (`/deploy/all/stream`) | The failing BU is reported via `bu-complete` with `error`; the loop continues to the next BU — a genuinely stuck migration in that tenant's `_prisma_migrations` table is left exactly as Prisma's own CLI leaves it, with no in-app remediation (`resolve` has no frontend caller, [landing page](/en/platform/tenant-migrations) §3.3) | `tenant_migration.service.ts:560-586` |
| A resolve-connection failure reaches `/deploy/stream` | Falls through the gateway's stale message-pattern mapping to HTTP 500 instead of the documented 422 — the message text is still correct, only the status code is wrong (verified stale since commit `af2437074`, [landing page](/en/platform/tenant-migrations) §4.4) | `tenant-migrations.controller.ts` |
| `TENANT_MIGRATION_API_ENABLED` unset | Every endpoint 403s, including `status` — indistinguishable in the UI from a permissions problem beyond the literal message text | `config.env.ts:222` |

## 6. Recommendations

- **Fix `resolvePreStreamErrorStatus()`'s regex** (or, better, have `deployStream`/`_streamDeploy` carry the originating `ErrorCode` through to the stream's pre-start error instead of re-deriving a status from message text a second time) so a connection-resolution failure on the stream path returns the same 422 the non-streaming `/deploy` endpoint already does.
- **Update the stale `db_connection` comment** in `../carmen-platform/src/services/tenantMigrationService.ts` to describe the pool/schema mechanism, so the next person reading it does not go looking for a column that was removed months earlier.
- **Wire `resolve()` into the UI**, even minimally (e.g. a super-admin-only action on a row already in an error state), so a stuck migration does not require a direct API call to clear.
- **Consider a persisted last-run record** (BU id, migration name, outcome, timestamp) if this screen is ever expected to answer "what happened to BU X's last deploy attempt" after the fact — today that answer only exists in application logs and the tenant's own `_prisma_migrations` table.

## 7. References

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:176` (`tb_business_unit`), `:1382` (`tb_database_pool`).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `resolveConnection`, `status`, `deploy`, `deployResolved`, `deployStream`, `runBuStream`, `deployAllStream`, `resolve`, `listActiveConnectionsWithSkips`.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit`, `BusinessUnitConnectionSource`.
- `../carmen-turborepo-backend-v2/packages/db-connection-utils/src/tenant-url.ts` — `buildTenantUrl`, `resolveTenantUrl`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.controller.ts` — `resolvePreStreamErrorStatus()`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/libs/config.env.ts:222` — `TENANT_MIGRATION_API_ENABLED`, `TENANT_DEPLOY_TOKEN`.
- [Tenant Migrations](/en/platform/tenant-migrations) — the module landing page this data model supports.
