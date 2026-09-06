---
title: Tenant Migrations
description: Fleet-wide screen that checks and applies pending tenant-database schema migrations across every business unit; every action is restricted to super-admins.
published: true
date: '2026-09-06T23:45:00.000Z'
tags: book/platform, tenant-migrations
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Tenant Migrations

> **At a Glance**
> **Screen:** `TenantMigrationManagement` (+ `FleetSync`, `DeployConsole`) at `/tenant-migrations`, added `../carmen-platform` commit `c59bbba` (2026-06-30) &nbsp;·&nbsp; **Route gate:** `cluster.read` — reused from [Clusters](/en/platform/clusters), the same key that also gates [Business Units](/en/platform/business-units) — plus this module's own `tenant_migrations` feature flag on `PrivateRoute`, checked after the permission gate &nbsp;·&nbsp; **Action gate:** every Check / Apply / Deploy-all action is additionally restricted to `isSuperAdmin` on the frontend and, at the backend `TenantMigrationGuard`, to a super-admin session **or** a matching `x-deploy-token` header &nbsp;·&nbsp; **Sidebar:** its own "Tenant Migrations" entry in the Organization group (`src/components/nav/platformNav.ts:14`) — not nested under Business Units or Clusters, despite sharing their permission key &nbsp;·&nbsp; **Kill switch:** `TENANT_MIGRATION_API_ENABLED`, an env var that is **off by default** — every endpoint, including status checks, 403s until it is explicitly set to `true` &nbsp;·&nbsp; **Relationship:** fleet-wide table view of the same backend capability the per-BU `TenantMigrationCard` on [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.5 exposes for one BU at a time &nbsp;·&nbsp; **e2e suite:** none — every claim below is sourced from implementation, not test coverage

## 1. Overview

Tenant Migrations is the platform's fleet-wide console for the tenant-schema Prisma migrations every business unit's own database must eventually pick up. It lives at its own top-level route, `/tenant-migrations`, with its own sidebar entry in the Organization group — not nested under [Business Units](/en/platform/business-units) or [Clusters](/en/platform/clusters), even though its route reuses their `cluster.read` permission key and its row list comes from the same `businessUnitService.getAll({ perpage: 1000, sort: 'code:asc' })` call the Business Units list page uses. `TenantMigrationManagement.tsx` lists every business unit returned by that call in one table and lets an operator check, apply, or batch-deploy pending migrations across the whole fleet from a single screen — the same underlying backend capability the per-BU `TenantMigrationCard` on the [Business Units edit page](/en/platform/business-units/ui-screens) §4.5 exposes for one BU at a time (§3.5).

Reaching the page and seeing the BU table needs only `cluster.read` plus this module's own `tenant_migrations` feature flag — a broad gate shared with two other sidebar entries that key off the same permission ([clusters](/en/platform/clusters), [business-units](/en/platform/business-units)). Every actual migration operation is a separate, much narrower story: the frontend disables every button — including the read-only Check — for a non-super-admin, and the backend's `TenantMigrationGuard` sits in front of the entire underlying controller regardless of what the frontend does (§4). Historically, this module's content lived as a sub-page of Business Units (`business-units/tenant-migrations.md`); it has been relocated here because `/tenant-migrations` has always been its own route, its own nav entry, and its own feature key (`tenant_migrations`, distinct from `business_units`) — the [Business Units](/en/platform/business-units) page now links here for the fleet-wide picture and keeps only the embedded per-BU card's story on its own sub-page.

## 2. Business Context

A Carmen deployment runs one Prisma-managed schema per business unit (property/hotel), all sharing the same migration history defined in one `@repo/prisma-shared-schema-tenant` package. Whenever that package gains a new migration, every tenant schema across every cluster needs `prisma migrate deploy` run against it before the corresponding application code can rely on the new columns/tables — and a hospitality operator can have dozens of properties on differently-paced rollout schedules. Without a fleet view, an operator would have to open each BU's own edit page and check its Technical tab one at a time; this screen exists specifically to answer "which tenants are behind, and by how much" in one glance (`FleetSync`, §3.1), and to let a super-admin (or a CI/CD pipeline via a deploy token, §4.2) push all of them forward — or roll through the whole fleet in one batch — without leaving the page.

## 3. Key Concepts

### 3.1 Screen layout

- **Header** — `PageHeader` titled "Tenant migrations", subtitle "Check which tenant databases are behind on schema migrations, and roll them out."
- **Fleet Sync summary card** (`FleetSync`) — a horizontal card showing `{in-sync count} / {total BUs}` in large monospace type, a three-segment (green/amber/red) progress bar for in-sync/behind/errored, and a legend row with counts (a total-pending-migrations figure appears only once it is non-zero). Before the first "Check all" run it shows "Not checked yet" instead of the bar. The card's action slot holds **Check all**, **Deploy all**, and **Export**.
- **Deploy Console** (`DeployConsole`) — renders only while a "Deploy all" batch is in flight: a dark terminal-style panel with a progress bar (applied/total for the BU currently migrating), the current BU code, and a scrolling, colour-coded log line per completed BU (green for applied/up-to-date, red for failed).
- **Search box** — client-side filter over the BU table (code/name), focusable via the global search shortcut.
- **BU table** (`DataTable`, 3 sticky-left columns) — **Code** (links to `/business-units/:id/edit`), **Name**, **Status** (a badge — "In sync" / "N behind" / "Error" / "Not checked", plus an inline "Applying X/Y … current-migration-name" line while a row's Apply is streaming, or an inline error message), **Last checked** (HH:MM:SS, client-local), and a row-actions column (icon-only **Check**, and **Apply** only when that row has pending migrations). There is no on-screen Pending count column — the Status badge already states the count ("3 behind" / "In sync"); the CSV export (below) keeps one, since a bare number is genuinely useful there for further calculation.
- **Empty state** — "No business units" with a "Go to Business Units" button, shown when the fleet has zero BUs (not zero pending migrations).
- A dev-only `DevDebugSheet` shows the raw `GET /api-system/business-units` response.

If the BU list is paginated server-side beyond what the page's single fetch (`perpage: 1000`) returns, a warning reads "Showing N of M business units. Increase the page size to see all." — the page does not itself paginate through the rest.

### 3.2 Actions and backend calls

| Action | UI trigger | Backend call | Gate |
|---|---|---|---|
| List business units | page load | `businessUnitService.getAll({ perpage: 1000, sort: 'code:asc' })` | `cluster.read` |
| Check (single row) | row action icon | `GET /api-system/tenant/migrations/:bu_id/status` | Frontend: disabled with a "Super-admin required." tooltip when `!isSuperAdmin`. Backend: `TenantMigrationGuard` (§4.2) |
| Check all | Fleet Sync card button | one `GET .../status` call per BU, concurrency-limited to 4 in flight (`mapWithConcurrency`) | Same as Check |
| Apply (single row) | row Apply icon → confirm dialog | `POST /api-system/tenant/migrations/:bu_id/deploy/stream` (NDJSON progress) | Same as Check |
| Deploy all | Fleet Sync card button → confirm dialog | `POST /api-system/tenant/migrations/all/deploy/stream` (NDJSON progress, one BU at a time server-side) | Same as Check |
| Export | Fleet Sync card button | client-side CSV of code/name/status/pending/last-checked from already-loaded state | None — exports whatever the table currently shows |

The frontend never calls the plain, non-streaming `POST /api-system/tenant/migrations/:bu_id/deploy` — `tenantMigrationService.deploy()` is defined but has no caller anywhere in `carmen-platform` (confirmed by grep of every `tenantMigrationService.` call site); both `TenantMigrationManagement` and the per-BU `TenantMigrationCard` run every apply through the streaming variant instead.

**Deploy all's own labeling is deliberately state-dependent** (`../carmen-platform` commit `dbb1107`, 2026-09-01, which also removed the on-screen Pending column above): the button reads `variant={behindCount > 0 ? 'destructive' : 'outline'}` — destructive-red only when a nonzero number of BUs are behind, labeled with its own blast radius ("Deploy 3 behind" instead of the generic "Deploy all"), and disabled (not merely muted) once a check has run and found nothing pending. The rationale, from the button's own source comment, is that this domain has no cancel/rollback endpoint, so the most visually urgent control on the screen should not be the one an operator can least undo.

### 3.3 Migration states, and what advances or stalls one

There is no persisted "migration status" row anywhere in the platform's own schema (see [Data Model](/en/platform/tenant-migrations/data-model) §2) — every state shown on this screen is derived live, per request, by shelling out to the Prisma CLI against the target tenant database and pattern-matching its text output:

- **`up_to_date`** — `prisma migrate status` output matches `/up to date/i`.
- **`has_pending`** — output matches `/not yet been applied/i`; the specific pending migration names are then pulled out of the same text with a generic `\d{14}_[a-z0-9_]+` pattern.
- **Anything else with a non-zero exit code** falls through to a plain error (`Result.error`) — there is no dedicated "stuck" or "failed" classification in this code. A migration that previously failed partway through `migrate deploy` is reported by Prisma's own CLI in whatever wording Prisma uses for that condition, which this service does not special-case; it will not match `has_pending` or `up_to_date` and will surface to the operator as a generic status-check error.

**Advancing a migration** runs `prisma migrate deploy --schema <schema>` against the tenant's resolved connection string; a resolved connection comes from `tb_business_unit.db_schema` plus its linked `tb_database_pool` row (host/port/database/username, and a decrypted password) — **not** from a `db_connection` column, which no longer exists on `tb_business_unit` (§4.3 flags a stale comment in the frontend service file that still describes the old mechanism). On success the CLI's `Applying migration \`name\`` lines are parsed to build the "applied" list streamed back as `applying` progress events; a `done` event with `already_up_to_date: applied.length === 0` closes the stream.

**What a failed `deploy` leaves behind:** a non-zero exit from `prisma migrate deploy` is reported as a stream `error` event (or an HTTP error on the non-stream path) carrying the sanitized CLI output — the operation is not retried and nothing in this codebase inspects *which* migration failed. Per-BU and batch runs are guarded by in-memory locks (`runningBuIds` per BU, `isBatchRunning` for the fleet) that return a 409 "already running" while held, but neither lock outlives the request — there is nothing that remembers a BU was left mid-migration once the process moves on. The only endpoint built to clear a genuinely stuck migration is `POST :bu_id/resolve` (`prisma migrate resolve --applied|--rolled-back <name>`, §4.4) — confirmed by grep that no frontend code anywhere in `carmen-platform` calls it. An operator who hits a stuck migration today has no in-app path to un-stick it.

**Batch deploy only protects the *next* BU, not the one in flight.** `deployAllStream`'s own backend comment (`tenant_migration.service.ts:504-518` in `../carmen-turborepo-backend-v2`) states cancellation stops the batch from starting the next tenant; the BU currently mid-migration when a client disconnects runs to completion (or its own timeout) regardless — the frontend's `AbortController` on unmount only stops the browser from listening, per the doc comment on `tenantMigrationService._streamDeploy`. There is no cancel/rollback endpoint for this domain at all.

### 3.4 Kill switch and the CI deploy-token path

The entire tenant-migration controller sits behind `TENANT_MIGRATION_API_ENABLED`, an environment-variable boolean that **defaults to `false`** when unset (`boolFromString(false)`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/libs/config.env.ts:222`) — every call, including a plain status check, 403s with "Tenant migration API is disabled" until an operator explicitly sets it to the literal string `true`. This is a plain env var, unlike its similarly-named sibling on the separate [Platform Migrations](/en/platform/platform-migrations) module, whose own on/off switch was moved into `tb_platform_config` (`platform_migration.api_enabled`) — the comment directly above `TENANT_MIGRATION_API_ENABLED` in `config.env.ts` is about that other module, not this one; this module's switch has not moved.

Besides a super-admin session, the backend also accepts an `x-deploy-token` header (compared with `timingSafeEqual`, matched against `TENANT_DEPLOY_TOKEN`) as an alternative credential, intended for a CI/CD pipeline to trigger deploys without a human session. This SPA screen never exercises that path — it only ever authenticates as the signed-in operator — so the deploy-token route is invisible from this UI entirely; using it requires calling the API directly (e.g. via the Bruno collection, §6).

### 3.5 Relationship to the Business Units edit page

- The per-BU `TenantMigrationCard` on [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.5 and this page call the **same** `tenantMigrationService` (`getStatus`, `deployStream`, `deployAllStream`) and the same backend controller — there is exactly one implementation of "check status" and "apply migrations," surfaced from two screens. [Business Units — Tenant Migrations](/en/platform/business-units/tenant-migrations) is now a short pointer covering only that embedded card; this page is the full account of the fleet-wide screen.
- Both surfaces gate identically on `isSuperAdmin` for **every** action, Check included — re-verified directly against `TenantMigrationCard.tsx`'s `actionsDisabled` (used on its Check-status button as well as Apply), not just against `TenantMigrationManagement.tsx`. The one gate this fleet table does **not** apply that the card does is `hasDbConnection` (the BU's own pool + schema already configured): the card pre-disables its buttons when that is false, while this table lets an operator attempt Check/Apply on any row and simply surfaces whatever error `resolveConnection` throws (§3.3) once the request is made.
- There is **no in-app link** between the two screens in either direction — confirmed by reading both components' source. The only way to this page is the sidebar's "Tenant Migrations" entry or typing the URL; this page's own "Code" column links straight to that BU's edit page, not to a filtered version of itself.

## 4. Roles and Permissions

> **Key-reuse gotcha, same as Business Units:** the `/tenant-migrations` route's `cluster.read` requirement gives no hint that it opens this screen — the same key also opens [Clusters](/en/platform/clusters) and [Business Units](/en/platform/business-units). The `tenant_migrations` feature flag (§4.1) is the only switch that can turn this screen off independently of the other two.

### 4.1 Frontend gate matrix

| Surface | Gate type | Key | Notes |
|---|---|---|---|
| `/tenant-migrations` route | `requiredPermission` + `feature` | `cluster.read` + `tenant_migrations` | Reused key, dedicated feature flag |
| Sidebar "Tenant Migrations" entry | `permission` + `feature` filter | `cluster.read` / `tenant_migrations` | `navGroup.organization`, `src/components/nav/platformNav.ts:14` |
| Row Check button | `disabled={!!disabledReason \|\| busy \|\| batchRunning}` | `isSuperAdmin` | Tooltip: "Super-admin required." |
| Row Apply button (rendered only when `has_pending`) | same `disabledReason` | `isSuperAdmin` | Confirm dialog before the stream starts |
| Check all / Deploy all buttons | same `disabledReason`, plus state-dependent extra disable (§3.2) | `isSuperAdmin` | Deploy all also disables once nothing is pending |
| Export button | `disabled={loading \|\| bus.length === 0 \|\| anyBusy}` | None | Exports the client's already-loaded state only |

### 4.2 Backend enforcement

Every migration-domain endpoint sits behind `TenantMigrationGuard` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts`), applied once to the whole controller via `@UseGuards(TenantMigrationGuard)`. It requires **one** of: a matching `x-deploy-token` header (constant-time compared, §3.4), or a valid super-admin Keycloak session (`KeycloakGuard` then `PlatformSuperAdminGuard`, both must pass) — there is no `cluster.*` or other RBAC permission path into it. The guard also enforces `TENANT_MIGRATION_API_ENABLED` first, before either credential check, so a disabled flag 403s regardless of who is asking. The frontend's `disabledReason = !isSuperAdmin ? 'Super-admin required.' : null` is a UI convenience that matches, rather than substitutes for, this server-side check — unlike the confirmed gaps documented for [SQL Workbench](/en/platform/sql-workbench) and [Query Dataset](/en/inventory/system-config/query-dataset), the tenant-migrations backend guard is not bypassable by calling the API directly with a non-super-admin session.

### 4.3 Re-verified against current source: a stale comment, corrected

The frontend's `tenantMigrationService.ts` still carries this comment, unchanged since it was first written (`../carmen-platform` commit `8fc1124`, 2026-06-29): *"The backend resolves the target tenant DB from the BU's stored db_connection."* That description was overtaken by `../carmen-turborepo-backend-v2` commit `af2437074` (2026-08-13), which moved connection resolution from the retired `tb_business_unit.db_connection` JSON column to `db_schema` + the linked `tb_database_pool` row (confirmed by direct read of `resolveConnection()` in `apps/micro-business/src/tenant/tenant.service.ts` — no code path in the current tree reads `db_connection` for this purpose). The comment was never updated to match; it is documentation debt in the source, not a description of current behavior, and this page describes the pool/schema mechanism the code actually runs (§3.3).

### 4.4 Re-verified against current source: a dead error-status mapping on the stream path

The gateway's `deployStream` handler maps a pre-stream connection failure to an HTTP status by pattern-matching the error message (`resolvePreStreamErrorStatus()`, `tenant-migrations.controller.ts`), added in commit `4ca923229` (2026-06-30) when `resolveConnection` failures still read "no database connection configured" / "unsupported database provider." The same `af2437074` refactor (§4.3) changed the actual thrown messages to "is not linked to a database pool", "has no database schema configured", "has been deleted", and "is inactive" — none of which match `resolvePreStreamErrorStatus`'s regex. The practical effect: since 2026-08-13, a BU with no pool linked, no schema set, or an inactive/deleted pool returns HTTP 500 from `/deploy/stream` (the function's unmatched-message fallback) instead of the documented 422. The message text itself still reaches the operator correctly (the frontend's row `errorMsg` renders the raw text regardless of status code, and `handleMigrationError` only special-cases 403/409), so this is a real gap in the API's documented status-code contract, not a gap in what the operator sees on screen. `GET /status` and the non-streaming `POST /deploy` are unaffected — they return their status via `StdResponse.fromResult()`'s generic `ErrorCode` mapping, not this regex.

## 5. Related Modules

- [Business Units](/en/platform/business-units) — every row on this screen is a `business_unit`; the [Tenant Migrations](/en/platform/business-units/tenant-migrations) sub-page there covers only the embedded per-BU `TenantMigrationCard`, not this fleet-wide screen
- [Clusters](/en/platform/clusters) — the source of the `cluster.read` permission key this module's route and nav entry reuse
- [Database Pools](/en/platform/database-pools) — the `tb_database_pool` records a BU's `database_pool_id` points at; a pool that is inactive or soft-deleted makes that BU's tenant connection unresolvable (§3.3, §4.4)
- [Platform RBAC](/en/platform/rbac) — the permission model behind `cluster.read`, and (`rbac/permissions.md`) the route-level gate table that also lists `/tenant-migrations`
- [SQL Workbench](/en/platform/sql-workbench) — the other per-tenant, super-admin-adjacent database console, added the same release window; §4.2 above contrasts its real permission gap with this module's real (non-bypassable) one

## 6. Reference Sources

- `../carmen-platform/src/pages/TenantMigrationManagement.tsx` — the standalone fleet page: state, columns, Check/Apply/Deploy-all/Export handlers, the `activeStreamControllersRef` abort-on-unmount cleanup.
- `../carmen-platform/src/pages/tenantMigration/{FleetSync,DeployConsole}.tsx` — the summary card and the live batch-deploy console.
- `../carmen-platform/src/services/tenantMigrationService.ts` — `getStatus`, `deploy` (unused), `deployStream`, `deployAllStream`, and the doc comment on stream-abort semantics (§4.3 flags its stale `db_connection` line).
- `../carmen-platform/src/components/TenantMigrationCard.tsx` — the per-BU embedded card documented in [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.5, sharing the same service (§3.5).
- `../carmen-platform/src/App.tsx:251-256` — the `/tenant-migrations` route (`requiredPermission="cluster.read"` plus `feature="tenant_migrations"`).
- `../carmen-platform/src/components/nav/platformNav.ts:14` — the sidebar entry (`permission: 'cluster.read'`, `feature: 'tenant_migrations'`, `groupKey: 'navGroup.organization'`).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.controller.ts` — `status`, `deploy`, `deploy/stream`, `resolve` endpoints, and `resolvePreStreamErrorStatus()` (§4.4).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.service.ts` — the gateway's thin RPC proxy to micro-business.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts` — the super-admin-or-deploy-token guard (§4.2); `../carmen-turborepo-backend-v2/apps/backend-gateway/src/libs/config.env.ts:222` — `TENANT_MIGRATION_API_ENABLED`/`TENANT_DEPLOY_TOKEN` (§3.4).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/tenant_migration/tenant_migration.service.ts` — `status`, `deploy`, `deployStream`, `deployAllStream`, `resolve`, `resolveConnection`, the `runningBuIds`/`isBatchRunning` locks (§3.3).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts` — `resolveConnectionForBusinessUnit()` / `resolveConnection()`, the pool+schema connection-string builder (§4.3).
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/tenant-migrations/` — Bruno requests for `status`, `deploy`, `deploy-stream`, `resolve`.

## 7. Pages in This Module

- [Data Model](/en/platform/tenant-migrations/data-model) — why there is no persisted migration-status entity, the `tb_business_unit`/`tb_database_pool` fields that resolve a tenant connection, and edge cases in that resolution.
