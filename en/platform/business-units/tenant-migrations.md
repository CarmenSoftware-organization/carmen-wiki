---
title: Business Units — Tenant Migrations
description: Fleet-wide standalone screen (/tenant-migrations) that checks and applies pending tenant-database schema migrations across every business unit — reuses cluster.read at the route, but every actual action is additionally gated to super-admin, both client-side and at the backend guard.
published: true
date: 2026-07-29T09:46:00.000Z
tags: book/platform, business-units, tenant-migrations
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Business Units — Tenant Migrations

> **At a Glance**
> **Screen:** `TenantMigrationManagement` (`/tenant-migrations`, added 2026-06-30) &nbsp;·&nbsp; **Route gate:** `cluster.read` (reused, same key as [Business Units](/en/platform/business-units)) &nbsp;·&nbsp; **Action gate:** every Check/Apply/Deploy action is additionally restricted to `isSuperAdmin` — client-side AND at the backend `TenantMigrationGuard` &nbsp;·&nbsp; **Sidebar:** "Tenant Migrations" entry in the Organization group &nbsp;·&nbsp; **Relationship:** fleet-wide list view of the same operation the per-BU `TenantMigrationCard` on [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.13 performs for one BU at a time

## 1. Overview

Tenant Migrations is a standalone page, not a sub-route of Business Units — but it operates on exactly the same domain object (every active `business_unit` row) and the same backend capability as the **Tenant Migrations** card already documented on the [Business Units edit page](/en/platform/business-units/ui-screens) §4.13. Where that card checks and applies migrations for the one BU currently being edited, this page (`TenantMigrationManagement.tsx`, reached from the sidebar's Organization group, not from any Business Units screen) lists **every** business unit in one table and lets an operator check, apply, or batch-deploy across the whole fleet from a single view.

The page loads its row list from the ordinary `businessUnitService.getAll()` endpoint (the same one the Business Units list page uses), so **reaching the page and seeing the BU table requires only `cluster.read`** — the identical route-reuse pattern Business Units already uses for its own three routes (see [Business Units — Roles and Personas](/en/platform/business-units) §4). Every actual migration operation, however, is a separate story: both the frontend and the backend restrict Check/Apply/Deploy-all to super-admin sessions only (§3). This split — broad read access to the list, narrow write access to the actions — mirrors the per-BU card's own gating (§4.13 there: "any editor sees it, actions super-admin gated") except that here even the read-only **status check** is included in the restriction, because unlike the BU edit page (which only shows the card for one BU already scoped by `cluster.update`), this page's whole purpose is fleet-wide migration state, which the backend treats as a single super-admin-only capability regardless of which BU is being asked about.

## 2. Screen Layout

- **Header** — `PageHeader` titled "Tenant migrations", subtitle "Check which tenant databases are behind on schema migrations, and roll them out."
- **Fleet Sync summary card** (`FleetSync`) — a horizontal card showing `{in-sync count} / {total BUs}` in large monospace type, a three-segment (green/amber/red) progress bar for in-sync/behind/errored, and a legend row with counts plus a running total of pending migrations across all behind tenants. Before the first "Check all" run it shows "Not checked yet" instead of the bar. The card's action slot on the right holds **Check all**, **Deploy all**, and **Export** buttons.
- **Deploy Console** (`DeployConsole`) — only rendered while a "Deploy all" batch is in flight: a dark terminal-style panel with a progress bar (applied/total for the BU currently migrating), the current BU code, and a scrolling, colour-coded log line per completed BU (green for applied/up-to-date, red for failed).
- **Search box** — client-side filter over the BU table (code/name), focusable via the global search shortcut.
- **BU table** (`DataTable`, 3 sticky-left columns) — columns: **Code** (links to `/business-units/:id/edit`), **Name**, **Status** (a badge — "In sync" / "N behind" / "Error" / "Not checked" — plus an inline "Applying X/Y … current-migration-name" line while a per-row Apply is streaming, or an inline error message), **Pending** (count), **Last checked** (HH:MM:SS, client-local), and a row-actions column (icon-only **Check** and, only when that row has pending migrations, **Apply**).
- **Empty state** — "No business units" with a "Go to Business Units" button, shown when the fleet has zero BUs (not zero pending migrations).
- A dev-only `DevDebugSheet` shows the raw `GET /api-system/business-units` response.

If the BU list is paginated server-side beyond what a single fetch (`perpage: 1000`) returns, a warning banner reads "Showing N of M business units. Increase the page size to see all." — the page does not itself paginate through the rest.

## 3. Actions & Gating

| Action | UI trigger | Backend call | Gate |
|---|---|---|---|
| List business units | page load | `businessUnitService.getAll({ perpage: 1000, sort: 'code:asc' })` | `cluster.read` (same as [Business Units list](/en/platform/business-units/ui-screens)) |
| Check (single row) | row action icon | `GET /api-system/tenant/migrations/:bu_id/status` | Backend: super-admin bearer token or a matching `x-deploy-token`. Frontend: button disabled with a "Super-admin required." tooltip when `!isSuperAdmin` |
| Check all | Fleet Sync card button | one `GET .../status` call per BU, concurrency-limited to 4 in flight (`mapWithConcurrency`) | Same as Check |
| Apply (single row) | row Apply icon → confirm dialog | `POST /api-system/tenant/migrations/:bu_id/deploy/stream` (NDJSON progress) | Same as Check |
| Deploy all | Fleet Sync card button → confirm dialog | `POST /api-system/tenant/migrations/all/deploy/stream` (NDJSON progress, one BU at a time server-side) | Same as Check |
| Export | Fleet Sync card button | client-side CSV of code/name/status/pending/last-checked from already-loaded state | None — exports whatever the table currently shows |

Every migration-domain endpoint above sits behind the backend's `TenantMigrationGuard` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts`), which requires **one** of: a super-admin Keycloak session, or a matching `x-deploy-token` header (a CI/CD deploy credential, compared with `timingSafeEqual`) — there is no `cluster.*` or other RBAC permission path into it at all. The whole controller can also be disabled outright by the `TENANT_MIGRATION_API_ENABLED` feature flag, in which case every call (including status checks) 403s with "Tenant migration API is disabled" regardless of who is asking. The frontend's `disabledReason = !isSuperAdmin ? 'Super-admin required.' : null` is therefore a UI convenience that matches, rather than substitutes for, a real server-side check — unlike the confirmed gaps documented for [SQL Workbench](/en/platform/sql-workbench) and [Query Dataset](/en/inventory/system-config/query-dataset), the tenant-migrations backend guard is not bypassable by calling the API directly with a non-super-admin session.

## 4. Relationship to the Business Units edit page

- The per-BU `TenantMigrationCard` on [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.13 and this page call the **same** `tenantMigrationService` (`getStatus`, `deployStream`, `deployAllStream`) and the same backend controller — there is exactly one implementation of "check status" and "apply migrations," surfaced from two screens.
- There is **no in-app link** from the Business Units edit page to this fleet-wide page, or back — read directly from both components' source; the only way to this page is the sidebar's "Tenant Migrations" entry (Organization group) or typing the URL. A BU's own edit page has no "view in fleet list" affordance, and this page's row-level "Code" link goes straight to that BU's edit page, not to a filtered version of itself.
- Streaming a deploy from either screen is genuinely fire-and-forget once started: the frontend's `AbortController` on unmount/navigation only stops the **browser** from waiting on the NDJSON stream — the code comment in `tenantMigrationService.ts` and this page's own source are explicit that the backend's `runBuStream`/`deployAllStream` are deliberately **not** torn down on client disconnect, so a migration already running continues to completion (or its own `spawnPrisma` timeout) even if the operator navigates away mid-stream. There is no cancel/rollback endpoint for this domain.

## 5. Known Gaps and Edge Cases

- **`POST :bu_id/resolve` has no frontend caller anywhere in carmen-platform.** The backend exposes a real endpoint (`tenant-migrations.controller.ts` `resolve()`) to mark a stuck/failed migration as `applied` or `rolled-back` by name — confirmed by direct source read of `tenantMigrationService.ts`, `TenantMigrationManagement.tsx`, and `TenantMigrationCard.tsx`, none of which reference `resolve`. An operator who hits a stuck migration (the controller's own Swagger notes a `409` "A migration operation is already running") has no UI path to un-stick it; it must be called directly (e.g. via Bruno).
- **Deploy-all only guards the *next* BU, not the one in flight.** The batch stream's own backend comment (`tenant_migration.service.ts:504-518`) states cancellation stops the batch from starting the next tenant — the BU currently mid-migration when a disconnect happens runs to completion regardless.
- **The `TENANT_MIGRATION_API_ENABLED` flag is fleet-wide and all-or-nothing** — there is no per-BU or per-environment toggle visible from this screen; when it is off, every row's Check/Apply fails identically with "Tenant migration API is disabled," which this page's row error text would show verbatim rather than as a distinguishable "flag is off" state.
- **No indication of the deploy-token path in the UI.** The backend accepts an `x-deploy-token` header as an alternative to a super-admin session (intended for CI/CD), but this SPA screen only ever authenticates as the signed-in operator — the token path is not something this page exercises or surfaces.

## 6. References

- `../carmen-platform/src/pages/TenantMigrationManagement.tsx`, `src/pages/tenantMigration/{FleetSync,DeployConsole}.tsx` — the standalone page, summary card, and batch-deploy console.
- `../carmen-platform/src/services/tenantMigrationService.ts` — `getStatus`, `deployStream`, `deployAllStream`, and the doc comments on stream-abort semantics.
- `../carmen-platform/src/components/TenantMigrationCard.tsx` — the per-BU embedded card documented in [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.13, sharing the same service.
- `../carmen-platform/src/App.tsx:145` — the `/tenant-migrations` route (`requiredPermission="cluster.read"`); `src/components/Layout.tsx:55` — the sidebar entry.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/tenant-migrations/tenant-migrations.controller.ts` — `status`, `deploy`, `deploy/stream`, `resolve` endpoints.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/tenant-migration.guard.ts` — the super-admin-or-deploy-token guard applied to the whole controller; `envConfig.TENANT_MIGRATION_API_ENABLED` feature flag.
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/tenant-migrations/` — Bruno requests for `status`, `deploy`, `deploy-stream`, `resolve`.
- [Business Units](/en/platform/business-units) and [Business Units — UI Screens](/en/platform/business-units/ui-screens) §4.13 — the per-BU card and the `cluster.*` key-reuse gotcha this page inherits.
