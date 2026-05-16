---
title: Query Dataset
description: SQL Workbench — execute ad-hoc SELECTs and create / browse / drop tenant views, stored procedures, and functions used as reusable data sources by reports and dashboards.
published: true
date: 2026-05-16T17:00:00.000Z
tags: system-config, query, dataset, sql, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Query Dataset

## 1. Purpose

Query Dataset (rendered as **SQL Workbench** in the UI) is the Sysadmin-only screen at `/system-admin/query-dataset` for running ad-hoc read-only queries and creating / browsing / dropping reusable database objects — **views**, **stored procedures**, and **functions** — directly inside the tenant database. The output of these objects becomes the data source for [[reporting-audit/report]] templates, dashboard tiles, and one-off operational queries: rather than embedding raw SQL inline in every report, a Sysadmin builds (or installs) a `v_pr_summary` / `v_inventory_position` view here, then a report or widget binds to that named object.

Unlike most carmen tables, **there is no `tb_query_dataset` row** for each saved object — the "registry" is the live PostgreSQL catalog (`pg_class`, `pg_proc`) scoped to the tenant's current schema. The Workbench reads, mutates, and removes those catalog entries directly under tenant-scoped credentials. This makes query-datasets immediately usable by any SQL-aware consumer (Carmen's own services, BI tools connected to the same database) at the cost of moving "what queries exist" out of Prisma's domain.

The companion `tb_widget_workspace` table (`name`, `query` text) does persist saved user dashboards keyed by their author, but that is a *widget* concern — the SQL Workbench itself is stateless across sessions: edits are committed to the database catalog, and reload-from-catalog is the recovery path.

## 2. Prisma Model(s) OR Data Model

No bespoke table. The "data model" is the PostgreSQL catalog plus a thin set of API endpoints.

### 2.1 PostgreSQL catalog projections

The Workbench's left-sidebar tree is populated by four catalog queries executed against `current_schema()` (the tenant's schema):

```
tables     → pg_class    WHERE relkind = 'r'   (excluding extension-owned)
views      → pg_class    WHERE relkind = 'v'   (excluding extension-owned)
procedures → pg_proc     WHERE prokind IN ('p','f')
columns    → pg_attribute joined to pg_class for table/view/materialised-view cols
```

The frontend `DbObjectsResponse` therefore has the shape:

```jsonc
{
  "tables":     [{ "schema": "tenant_t01", "name": "tb_purchase_request" }, ...],
  "views":      [{ "schema": "tenant_t01", "name": "v_pr_summary" }, ...],
  "procedures": [{ "schema": "tenant_t01", "name": "sp_close_period", "kind": "procedure" }, ...],
  "columns":    [{ "table": "tb_purchase_request", "column": "id", "data_type": "uuid" }, ...]
}
```

### 2.2 Object definition (for editing)

When the user clicks an existing view / procedure / function in the tree, the Workbench fetches its `pg_get_viewdef` or `pg_get_functiondef` text and loads it into the editor as `CREATE OR REPLACE VIEW "<schema>"."<name>" AS …`, ready to edit and re-save.

### 2.3 Save / Drop contract

`POST /api/config/:bu_code/sql-query/save` accepts:

```jsonc
{
  "name": "v_pr_summary",                       // required when bare SELECT
  "sql_text": "SELECT id, doc_no FROM tb_pr",  // full DDL or bare SELECT
  "query_type": "view"                          // "view" | "stored_procedure" | "function"
}
```

If `sql_text` is a bare `SELECT` and `query_type` is `view`, the server wraps it with `CREATE OR REPLACE VIEW "<name>" AS …`. Otherwise the full `CREATE OR REPLACE …` DDL must be supplied. `DELETE /api/config/:bu_code/sql-query/db-objects?type=…&schema=…&name=…` drops the named object.

### 2.4 Related (not the same)

- `tb_widget_workspace` — author-scoped saved dashboard queries (`{ name, query }`) for the widget canvas; separate from the catalog objects this page manages.
- `tb_report_job.report_type` / `tb_report_schedule.report_type` — string keys mapped to report definitions that may *consume* a query-dataset view, but the mapping itself is in the reports module.

## 3. Usage / Cross-References

- [[reporting-audit/report]] — report templates bind to a view created here as their data source. The report engine pages the view with parameters injected via report-side filters.
- [[reporting-audit/widget]] — dashboard widgets execute against views or, for ad-hoc tiles, draft SQL stored in `tb_widget_workspace`. Re-usable widget queries should be promoted to views here so they survive widget deletion.
- [[reporting-audit/schedule]] — scheduled reports consume the same views.
- [[access-control/permission]] — only roles holding the `sql-query.execute` / `sql-query.save` / `sql-query.drop` App IDs see this screen. Database-level permissions on the views themselves follow PostgreSQL grants on the tenant schema. (*Inferred — to be verified.*)
- [[system-config/period]] — period-close objects (`sp_close_period`, `v_period_snapshot`) typically live here as functions / views the costing engine calls.

## 4. Configuration UI

Managed by **Sysadmin** under System Admin → Query Dataset (rendered as "SQL Workbench"). The layout is a two-pane workbench:

- **Left sidebar (`DbObjectTree`):** collapsible tree of `tables`, `views`, `procedures`, `functions` in the current tenant schema. Click a node to load its definition into the editor; a per-row spinner indicates the in-flight definition fetch.
- **Right pane:** a three-field meta strip (Object Name, Type select — `View` / `Stored Procedure` / `Function`, and a read-only "Editing: schema.name (type)" indicator when loaded), followed by the **SQL Editor** (Monaco-style, with schema-aware autocomplete fed by the `columns` projection), followed by a **Result Panel** that materialises after Run.
- **Top-right actions:** **Run** (in-editor button — executes the current selection or full text as a read-only query), **Save** (creates the view / procedure / function), **Drop** (only visible when an existing object is loaded — destructive, confirmed via browser dialog).
- **Read-only by default tip:** the editor hints "bare SELECT for view is auto-wrapped with CREATE OR REPLACE VIEW" so casual users don't need to remember DDL syntax.

## 5. Business Rules

- **Sysadmin-only.** The route is mounted under `/system-admin` and gated by the `sql-query.*` App IDs. Non-admin roles never see the navigation entry.
- **Run is read-only.** `validateSqlSafety` allows only leading `SELECT`, `WITH`, `SHOW`, `EXPLAIN`, `DESCRIBE`, `DESC` for the execute path, with `allowMultiple: false`. Any `INSERT` / `UPDATE` / `DELETE` / `DROP` / `TRUNCATE` is rejected client-side before the request is sent, and re-checked server-side.
- **Save is restricted to `CREATE`.** When the user clicks Save, the validator either requires `allowedLeading: ['CREATE']` (full DDL) or `allowedLeading: ['SELECT', 'WITH']` (bare SELECT, view only). Mixed scripts that begin with `CREATE` but contain `DROP` further down are blocked at the multi-statement check.
- **30-second statement timeout.** Every execute runs inside a transaction with `SET LOCAL statement_timeout = '30s'`, total Prisma transaction budget 35 s, max-wait 8 s. Long-running queries are killed cleanly.
- **Tenant-scoped credentials.** `prismaTenantInstance(bu_code, user_id)` provides the connection, so every query and DDL runs inside the tenant's PostgreSQL role / schema; cross-tenant access is impossible at the database layer.
- **Connection-pool retry.** If the first run fails with "connection pool exhausted", the service waits 500 ms and retries once before surfacing a "Database is busy" error.
- **BigInt safety on response.** Result rows are post-processed so `bigint` columns are stringified — JSON cannot natively carry them — and the column order is preserved from the first row.
- **Drop is destructive and confirmed.** The frontend opens a native `confirm()` before issuing `DELETE`; there is no undo. The dropped object is removed from the catalog immediately; any report or widget bound to it will error on next run until the binding is updated.
- **Bare-SELECT view requires a name.** Server validates `name` is present when wrapping a bare `SELECT` into `CREATE OR REPLACE VIEW`; quoting is applied to defend against name-based injection.
- **Procedures / functions must be full DDL.** Bare bodies are rejected; the user must supply `CREATE OR REPLACE PROCEDURE …` or `CREATE OR REPLACE FUNCTION …`.
- **No version history.** Edits are `CREATE OR REPLACE` — previous text is not retained by Carmen. If history is required, version control the DDL externally (git) and re-apply via the Workbench.

## 6. References

- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-query.service.ts` — `execute`, `saveDdl`, `listDbObjects`, `getDbObjectDefinition`, `dropDbObject`.
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts`.
- **SQL safety validator:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-validator.ts` (and the frontend mirror at `../carmen-inventory-frontend/lib/sql-validator.ts`).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/query-dataset/page.tsx` and `_components/query-dataset-component.tsx`.
- **Frontend supporting components:** `_components/db-object-tree.tsx`, `_components/sql-editor.tsx`, `_components/result-panel.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-sql-query.ts` — `useDbObjects`, `useDbObjectDefinition`, `useSqlQueryExecute`, `useSqlQuerySave`, `useSqlQueryDrop`.
- **Related Prisma:** `tb_widget_workspace` (lines ~5787-5801), `tb_report_schedule` (lines ~5685-5709), `tb_report_job` (lines ~5652-5683).
- **Cross-module:** see Section 3.
