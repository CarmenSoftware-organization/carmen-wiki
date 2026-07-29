---
title: SQL Workbench
description: Admin console (/sql-workbench, added 2026-07-09) that runs arbitrary SQL and browses/creates/drops views, stored procedures, and functions against a chosen tenant's database — the confirmed carmen-platform frontend for the backend service documented in the Inventory book's Query Dataset page.
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/sql-workbench, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# SQL Workbench

> **At a Glance**
> **Screen:** `SqlWorkbench` (`/sql-workbench`, added 2026-07-09) &nbsp;·&nbsp; **Route gate:** `sql_workbench.read` &nbsp;·&nbsp; **Write gate:** `sql_workbench.manage` — separately controls whether Run/Save/Drop render at all &nbsp;·&nbsp; **Sidebar:** "SQL Workbench" entry in the Platform group &nbsp;·&nbsp; **Backend:** the exact `config_sql-query` controller family documented from the backend side in [Query Dataset](/en/inventory/system-config/query-dataset) — this page is that service's confirmed frontend

## 1. Overview

SQL Workbench is a per-tenant SQL console: pick a business unit, browse its live tables/views/procedures/functions, load an existing object's definition into an editor, run arbitrary SQL against it, and save the editor contents back as a new or replaced view/procedure/function. It is reached from the sidebar's Platform group and is one of the newest screens in carmen-platform (added 2026-07-09, alongside [Tenant Migrations](/en/platform/business-units/tenant-migrations) and [Report Form Groups](/en/platform/report-templates/form-groups) as the three most recent Bucket-A additions this resync round covers).

This is not a new backend capability — it is a new **frontend** for one. The Inventory book's [Query Dataset](/en/inventory/system-config/query-dataset) page documents the exact same backend controller family (`config_sql-query.controller.ts` calling `SqlQueryService.execute/saveDdl/listDbObjects/getDbObjectDefinition/dropDbObject` in `micro-business`) and had, as of its last verified pass, concluded "no frontend screen that calls it" — that search was scoped to `carmen-inventory-frontend-react`, which is still true; it did not check the separate Platform admin product. `SqlWorkbench.tsx`'s service layer (`sqlQueryService.ts`) calls the identical `/api/config/:bu_code/sql-query/*` routes, confirming this screen is the real-world answer to that page's "no confirmed frontend screen" finding — just built in a different repository than the one that page's search covered.

## 2. Business Context

The backend service was designed so that report and dashboard authors could create reusable database views/functions/procedures directly in a tenant schema, for [Report Templates](/en/platform/report-templates) and dashboard widgets to consume later. Before this screen existed, that meant calling the API directly (e.g. via Bruno) with no browsing UI. SQL Workbench turns that into an ordinary admin workflow: select a BU, see what already exists in its schema, and iterate on a view/procedure/function without leaving the browser — while also functioning as a general emergency-access SQL console for support engineers, since `execute` accepts any statement type.

## 3. Key Concepts

- **BU switcher (`⌘/Ctrl+B`)**: the workbench operates on exactly one business unit's tenant database at a time, chosen from a searchable switcher dialog (`BuSwitcher`). Switching BUs discards the currently loaded object, editor contents, and any result panel — nothing carries over between tenants.
- **Connection bar**: a persistent header strip showing the selected BU's code/name/cluster, a stable per-tenant colour swatch (`buHueColor`), and a **read-only** / **read / write** badge driven by whether the session holds `sql_workbench.manage` — so an operator can see at a glance whether they can mutate the tenant they're pointed at, not just which tenant it is.
- **DB object tree**: a sidebar listing the selected tenant's tables, views, and procedures/functions (from `GET .../sql-query/db-objects`, backed by `pg_class`/`pg_proc` catalog queries — no bespoke `tb_*` registry table exists for this domain; see [Query Dataset](/en/inventory/system-config/query-dataset) §5 for the exact catalog projections). Clicking a **table** row pre-fills the editor with `SELECT * FROM <name> LIMIT 100;`; clicking a **view/procedure/function** loads its live definition (`pg_get_viewdef`/`pg_get_functiondef`) into the editor as ready-to-resave `CREATE OR REPLACE …` DDL.
- **SQL editor**: a CodeMirror-based editor (`SqlEditor`) with `Ctrl/⌘+Enter` bound to Run. The Run button (and the Ctrl/⌘+Enter shortcut) is omitted entirely — not just disabled — when the session lacks `sql_workbench.manage`, because the frontend cannot reliably distinguish a read-only `SELECT` from DML/DDL client-side (the same `sqlValidator.ts` used elsewhere is explicitly UI-feedback-only, not a security boundary) and so gates the whole executor rather than pretending to allow a safe read-only path through.
- **Object name + Type fields**: above the editor, a name input and a View/Stored Procedure/Function select describe what Save will create — required for a bare `SELECT` saved as a view; ignored (the DDL's own `CREATE ... name` wins) when the editor already contains full `CREATE OR REPLACE` DDL.
- **Result panel**: shows row count, execution time (ms), and column count in its header, a scrollable table (client-paginated at 50/100/200/500 rows per page) with per-cell truncation and a `NULL` italic marker, a CSV export button, and — on error — the raw error text plus a best-effort "error referenced line N" hint parsed from common Postgres error phrasing.
- **Destructive-statement confirmation**: before running, the client-side `classifyStatements()` flags any leading `DROP`/`TRUNCATE`/`DELETE`/`UPDATE`/`ALTER`/`GRANT`/`REVOKE` keyword as destructive and additionally flags an `UPDATE`/`DELETE` with no `WHERE` clause as "unguarded" — both trigger a confirm dialog naming the specific keywords found (and, for an unguarded write, an extra warning that it will affect all rows) before the request is sent. This is UI-only friction, not a safety net; see §4.
- **Drop**: with an object loaded and `sql_workbench.manage` held, a **Drop** button in the page header permanently removes it from the schema after a confirm dialog — the same one-way operation `DELETE .../sql-query/db-objects` performs when called directly (documented in [Query Dataset](/en/inventory/system-config/query-dataset) §2/§4).

## 4. Roles and Personas

The `/sql-workbench` route carries `requiredPermission="sql_workbench.read"` on `PrivateRoute` — a session without that grant sees `<Forbidden>` inside the normal `<Layout>` shell, matching every other gated Platform route. Within the page, `hasPermission('sql_workbench.manage')` (`canManage`) is the sole gate deciding whether Run, Save, and Drop render at all; there is no third tier and no per-action split between them — a session either has both read (browse) and write (mutate) capability, or read-only browsing alone.

| Surface | Gate | Key |
|---|---|---|
| `/sql-workbench` route | `requiredPermission` | `sql_workbench.read` |
| Sidebar "SQL Workbench" entry | `permission` filter | `sql_workbench.read` |
| Run button + Ctrl/⌘+Enter shortcut | rendered only if `canManage` | `sql_workbench.manage` |
| Save button | rendered only if `canManage` | `sql_workbench.manage` |
| Drop button | rendered only if `canManage` (and an object is loaded) | `sql_workbench.manage` |

Both keys are seeded in the platform permission catalog (`seed.platform-permission.data.ts`): `sql_workbench.read` — "Open the SQL Workbench, browse database objects, and run read-only queries against a business unit's database" — and `sql_workbench.manage` — "Run write/DDL SQL … and create/drop views, stored procedures, and functions." Of the platform's built-in role bundles (`seed.platform-role-permission.data.ts`), only `platform_admin` (via `sql_workbench.*`) and `cluster_admin` (via the blanket `*`) carry either key by default — `support_manager`, `support_staff`, and `security_officer` have neither, so SQL Workbench (in any capacity) is not part of the default support-tier role set.

> **Confirmed gap, mirrors the Inventory book's finding.** The `sql_workbench.read` description above promises "read-only queries," and the frontend enforces that promise by hiding Run/Save/Drop for a read-only session — but at the backend, only the `POST .../execute` route actually carries `@RequirePlatformPermission('sql_workbench.manage')`. The other four routes this page depends on (`GET db-objects`, `GET db-objects/definition`, `POST save`, `DELETE db-objects`) carry **no permission guard beyond authentication**, confirmed in [Query Dataset](/en/inventory/system-config/query-dataset) (Implementation status, §3, §6). In other words: a `sql_workbench.read`-only session cannot Save or Drop from this UI, but nothing stops that same session from calling `POST .../sql-query/save` or `DELETE .../sql-query/db-objects` directly (e.g. via Bruno) — the UI's read/write split is not backed by a matching server-side split on those two routes. `execute` itself, the one route that *is* guarded, is also the one route that is **not** read-only despite its permission's name: `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` skips the forbidden-keyword blocklist entirely, so a `sql_workbench.manage` grant (not `.read`) is what actually lets an operator run `DROP`/`ALTER`/multi-statement scripts through Run — matching this page's own Run-button gating, but leaving the permission-catalog description of `.read` as "read-only queries" not fully accurate to what a `.read`-only caller can reach outside this UI.

## 5. Related Modules

- [Query Dataset](/en/inventory/system-config/query-dataset) — the Inventory book's documentation of the exact same backend service from the API/data-shape side: catalog projections, the `execute`/`save`/`db-objects` contract, the `allowDangerous` validator finding, and the confirmed permission-guard gap on four of the five routes. Read that page for backend request/response shapes; this page covers the carmen-platform screen that now calls it.
- [Business Units](/en/platform/business-units) — supplies the BU list the switcher searches (`businessUnitService.getAll`) and the `db_connection` each BU carries, which is what makes a tenant database reachable at all.
- [Report Templates](/en/platform/report-templates) — the intended downstream consumer of views/functions created here, via `source_name`/`source_params` data-source binding; linkage not independently re-verified this pass.
- [Platform RBAC](/en/platform/rbac) — owns the `sql_workbench.read`/`.manage` permission keys and the role-bundle assignments summarized in §4.

## 6. Reference Sources

- `../carmen-platform/src/pages/sqlWorkbench/SqlWorkbench.tsx` and sibling components (`ConnectionBar`, `BuSwitcher`, `DbObjectTree`, `SqlEditor`, `ResultPanel`) — the page and its parts.
- `../carmen-platform/src/services/sqlQueryService.ts` — `getDbObjects`, `getDefinition`, `executeSql`, `saveDdl`, `dropObject`; the doc comment on why aborting `executeSql` does not cancel the tenant-side query.
- `../carmen-platform/src/utils/sqlValidator.ts` — `extractTopLevelStatements`, `classifyStatements`, explicitly documented as client-side UI feedback only, not a security boundary.
- `../carmen-platform/src/App.tsx:297` — the `/sql-workbench` route (`requiredPermission="sql_workbench.read"`); `src/components/Layout.tsx:67` — the sidebar entry.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` — the `sql_workbench.read`/`.manage` catalog entries; `seed.platform-role-permission.data.ts` — role-bundle assignment.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts` and `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/{sql-query.service.ts,sql-validator.ts}` — the backend this page calls, documented in full from `../carmen-inventory-frontend-react`'s backend-only perspective in [Query Dataset](/en/inventory/system-config/query-dataset).

## 7. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
