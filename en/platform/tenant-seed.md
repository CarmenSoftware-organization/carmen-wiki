---
title: Tenant Seed
description: Fleet-wide screen that checks which business-unit databases are missing baseline seed data (running codes, templates, adjustment types and similar) and fills the gaps by streaming a per-BU seed run.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, tenant-seed
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Tenant Seed

Every business unit has its own tenant database. A freshly created or long-lived tenant can be missing baseline rows the inventory application assumes exist: document running-code formats, vendor business types, GL journal prefixes, notification templates, adjustment types and so on. **Tenant Seed** is the console that finds those gaps across the whole fleet and fills them, create-if-missing only, without touching rows that already exist. It is the data counterpart of [Tenant Migrations](/en/platform/tenant-migrations), which handles schema changes.

> **At a Glance**
> **Screen:** `TenantSeedManagement` (+ `SeedFleetSummary`, `SeedSetPickerDialog`) at `/tenant-seeds` &nbsp;·&nbsp; **Nav:** Organization group, child of Business Units (`parentPath: '/business-units'`), `permission: 'tenant_seed.read'`, `feature: 'tenant_seeds'` (`backstageNav.ts:18`) &nbsp;·&nbsp; **Permission keys:** `tenant_seed.read` (status), `tenant_seed.apply` (seed) &nbsp;·&nbsp; **API:** `GET /api-system/tenant/seeds/:bu_id/status`, `POST /api-system/tenant/seeds/:bu_id/deploy/stream` (NDJSON) &nbsp;·&nbsp; **Kill switch:** gateway env `TENANT_MIGRATION_API_ENABLED` must be true &nbsp;·&nbsp; **Seed sets:** 8 &nbsp;·&nbsp; **Sub-pages:** 2 &nbsp;·&nbsp; **e2e suite:** none

## 1. Overview

The page lists every business unit in a table and keeps a **per-row seed state** in memory: Not checked, Seeded, N missing, No DB, or Error. Nothing is stored by the page itself; "Check" asks the backend to compare the tenant database against the seed definitions, and "Seed" streams creation of the missing rows. The same logic, scoped to one BU, is also embedded as `TenantSeedCard` on the Business Units edit page (Technical tab; see [Business Units: UI Screens](/en/platform/business-units/ui-screens) §4.5).

A **seed set** is a named group of rows with a stable key. The backend defines eight, in this order (order matters because the legacy-wiring set repoints workflows at rows the template set creates; `seed-sets/index.ts`):

| Order | Set key | Label shown | What a "row" is |
|---|---|---|---|
| 1 | `running-code` | Running codes | one `tb_config_running_code` row per document `type` |
| 2 | `vendor-business-type` | Vendor business types | one `tb_vendor_business_type` row per name |
| 3 | `gl-jv-prefix` | GL JV prefixes | one `tb_gl_jv_prefix` row per code |
| 4 | `email-templates` | Email messages | one entry inside the single `tb_application_config` JSON row for the email-templates key (a read-modify-write, not an insert) |
| 5 | `notification-templates` | Workflow notification templates | one `tb_notification_template` row per template code |
| 6 | `notification-templates-legacy` | Workflow notification wiring | three actions, not rows: `retire-legacy` (retire untouched legacy templates), `move-reject-previous` (move the reject approver slot to `previous_step` in workflow data), `fill-workflows` (fill workflow template ids) |
| 7 | `adjustment-type` | Adjustment types | one `tb_adjustment_type` row per code |
| 8 | `pos-sale-adjustment-type` | POS sale adjustment type | the POS `SALE` stock-out adjustment type, matched by `code` only |

A row counts as **present** by its natural key among non-deleted rows. A set's progress is `present/defined`.

## 2. Business Context

Defaults evolve: a release adds a new running code, a new notification template or a new system adjustment type. Existing tenants do not receive new defaults from a schema migration, because those are data. Support staff therefore need two answers per BU: "is this tenant behind?" (status, safe, read-only) and "bring it up to date" (apply). Because apply writes into a customer's real database, it is a separate permission from viewing, and the whole API sits behind an environment kill switch (§4).

## 3. Key Concepts

### 3.1 Row status

| Status | When (`seedRowStatusOf`, `tenantSeed/seedRowState.ts`) |
|---|---|
| No DB | BU list data shows no database pool or no `db_schema` (when the list payload omits both fields the SPA assumes a DB exists and lets the backend's 422 surface as Error) |
| Error | The last check or seed on that row failed (message shown on the row) |
| Not checked | No status loaded yet |
| N missing | Status loaded and total `missing` across sets is above zero |
| Seeded | Status loaded and nothing missing |

Rows sort by badge rank (Error, Missing, Not checked, No DB, Seeded) when the Status column is sorted.

### 3.2 Idempotence

Seeding only creates what is missing, so running twice is safe. The final `done` event reports `created` (rows made this run) and `skipped` (defined rows of the selected sets that were already there). Re-running after a dropped connection is the intended recovery.

### 3.3 What "seed all" means

There is no server-side "all BUs" endpoint. **Seed all missing** is the SPA looping over BUs one at a time (sequentially, not parallel), using the status it already has: only rows currently flagged Missing are visited, restricted to the sets the operator ticked in the picker. Leaving the page stops the loop before the next BU.

## 4. Permissions and gating

| Layer | Rule |
|---|---|
| Kill switch | `TenantMigrationGuard` throws 403 "Tenant migration API is disabled" unless the gateway env `TENANT_MIGRATION_API_ENABLED` is true (default false, `config.env.ts:209`). The same guard also protects the Tenant Migrations controller (`tenant-migrations.controller.ts`). |
| CI path | A request with header `x-deploy-token` equal to `TENANT_DEPLOY_TOKEN` passes as actor `ci:deploy-token`, skipping user checks. |
| User path | Needs a valid Keycloak session and the route's key: status needs `tenant_seed.read`, deploy stream needs `tenant_seed.apply`. **Cluster-scoped grants do not count**: the user needs `is_super_admin` or the key in their backstage-wide set. |
| SPA | Route and sidebar: `tenant_seed.read` + feature flag `tenant_seeds`. The Seed and Seed-all buttons are disabled with a tooltip "Requires the tenant_seed.apply permission." unless the viewer holds `tenant_seed.apply`; Check and Check all need only `read`. |
| Default roles (seed data) | Backstage Admin holds `tenant_seed.*`; Support Manager and Support Staff hold `tenant_seed.read` only; Security Officer holds neither (`seed.backstage-role-permission.data.ts`). |

Every call logs an audit line `tenant-seed.audit` with actor (`ci:deploy-token`, `super-admin:<id>` or `backstage-user:<id>`), operation, `bu_id` and success.

## 5. Edge Cases

| Case | Behaviour |
|---|---|
| BU has no pool/schema | Row shows No DB, no actions; backend would answer 422 "no database connection configured" |
| Unknown or deleted `bu_id` | 404; malformed UUID: 400 |
| Kill switch off | Every call 403; the toast reads "Seeding is disabled, or you lack the tenant seed permission." |
| Browser closes mid-stream | Gateway unsubscribes when the **response** closes (`res.on('close')`). Micro-business checks a cancelled flag between rows, but whether the unsubscribe reaches it through the RPC stream is not verified (the SPA service comments say the same). Re-run to finish; seeding skips existing rows |
| Error mid-stream after headers sent | An `{type:'error'}` NDJSON line is written, then the stream ends; the SPA marks the row Error |

## 6. Sub-pages

- [UI Screens](/en/platform/tenant-seed/ui-screens) - summary card, table, set-picker dialog, batch progress, CSV export.
- [Lifecycle](/en/platform/tenant-seed/lifecycle) - status computation, the NDJSON protocol, per-set create logic, cancellation.

## 7. References

- SPA: `../carmen-backstage/src/pages/TenantSeedManagement.tsx`, `src/pages/tenantSeed/*`, `src/services/tenantSeedService.ts`, `src/components/TenantSeedCard.tsx`, `src/utils/seedError.ts`, types at `src/types/index.ts:406`.
- Gateway: `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/tenant-seeds/tenant-seeds.controller.ts` (`@Controller('api-system/tenant/seeds')`), guard `src/auth/guards/tenant-migration.guard.ts`.
- Micro-business: `apps/micro-business/src/authen/tenant_seed/` (`tenant_seed.service.ts`, `seed-sets/`).
- Related: [Tenant Migrations](/en/platform/tenant-migrations), [Business Units](/en/platform/business-units), [Tenant Imports](/en/platform/tenant-imports).
