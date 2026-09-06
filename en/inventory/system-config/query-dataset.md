---
title: Query Dataset
description: SQL Workbench — a real backend admin-SQL-console service whose UI lives in the Platform SPA, not this one, and whose execute endpoint runs any SQL (including DROP/ALTER/multi-statement) rather than the read-only surface previously documented here.
published: true
date: 2026-09-06T06:45:00.000Z
tags: system-config, query, dataset, sql, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Query Dataset

> **At a Glance**
> **Owner:** Gated by two platform permissions — `sql_workbench.read` (browse) and `sql_workbench.manage` (run / save / drop), on **all five routes** since 2026-08-20 &nbsp;·&nbsp; **Storage:** PostgreSQL catalog (`pg_class`, `pg_proc`) in the tenant schema — **no `tb_query_dataset`** &nbsp;·&nbsp; **No screen in *this* product** — the console is the Platform SPA's [SQL Workbench](/en/platform/sql-workbench); no matching route/component/hook exists in `carmen-inventory-frontend-react` &nbsp;·&nbsp; **`execute` is NOT read-only** — it runs any SQL, including DDL and multiple statements.

## Implementation status (verified 2026-07-16; permissions and UI re-verified 2026-09-06)

Three claims in earlier versions of this page do not match current source and are corrected below. Items 1 and 2 were corrected on 2026-07-16; item 3 on 2026-09-06:

1. **No frontend implementation was found.** The previously-cited `routes/system-admin/query-dataset/page.tsx`, `_components/query-dataset-component.tsx`, `hooks/use-sql-query.ts`, and `lib/sql-validator.ts` (frontend mirror) **do not exist anywhere in `carmen-inventory-frontend-react`** — a repo-wide search for `query-dataset` and `sql-query` in that repo returns zero files, and `routes/router.tsx` has no `query-dataset` path under `/system-admin`. The backend service and its endpoints (below) are real, and **there is a UI — it is just not in this product.** The Platform SPA (`carmen-platform`) ships a full [SQL Workbench](/en/platform/sql-workbench) screen at `/sql-workbench` (added 2026-07-09) whose `sqlQueryService.ts` calls `/api/config/${buCode}/sql-query` — the same five endpoints documented here. Read as "no Carmen Inventory screen", not "no screen anywhere"; the original wording predates anyone checking the other SPA.
2. **`execute` is an unrestricted admin SQL console, not a read-only Run.** `SqlQueryService.execute()` calls `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` — `allowDangerous: true` skips the forbidden-keyword blocklist (`DROP`, `TRUNCATE`, `ALTER`, `GRANT`, `REVOKE`, `COPY`, `VACUUM`, `CLUSTER`, `REASSIGN`, `REINDEX`) entirely, and no `allowedLeading` restriction is passed, so `INSERT`/`UPDATE`/`DELETE`/`CREATE`/`DROP`/`ALTER` all pass, and `allowMultiple: true` permits multi-statement scripts. The controller's own Swagger description says as much: *"Runs any SQL against the tenant DB — SELECT, DML (INSERT/UPDATE/DELETE) and DDL (CREATE/ALTER/DROP/…), one or more statements."* The code comment is explicit about why: *"Access is gated by the `sql_workbench.manage` platform permission at the gateway; this validator only rejects empty/unparseable input here — it is not the security boundary."* Only `saveDdl()` (the "Save" contract in §5.3) keeps the restrictive `SELECT`/`WITH`-only or `CREATE`-only validation this page originally attributed to `execute`.

3. **The permission gap this page reported is closed — do not act on the old text.** Between 2026-07-16 and 2026-08-20 this page correctly reported that only `POST .../execute` was guarded and that `save`, `db-objects` (list), `db-objects/definition` (get) and `db-objects` (drop, `DELETE`) were reachable by any authenticated caller. **That is no longer true.** Commit `525597688` (2026-08-20, `carmen-turborepo-backend-v2`, *fix(security): คุมสิทธิ์ 4 endpoint ของ SQL Workbench ที่เปิดให้สมาชิก BU ทุกคน*, closing issue #321) added `@UseGuards(PlatformPermissionGuard)` + `@RequirePlatformPermission(...)` to all four:

| Route | Permission required since 2026-08-20 |
|---|---|
| `POST .../execute` | `sql_workbench.manage` (unchanged — this one was always guarded) |
| `POST .../save` | `sql_workbench.manage` |
| `GET .../db-objects` | `sql_workbench.read` |
| `GET .../db-objects/definition` | `sql_workbench.read` |
| `DELETE .../db-objects` | `sql_workbench.manage` |

The fault the commit describes is what the old text on this page told you to expect: any member of the target business unit — "an ordinary employee with no platform role at all" — could `CREATE OR REPLACE` or `DROP` a view/procedure/function in the tenant schema, while running a plain `SELECT` required a permission. All five routes now also carry `@ApiResponse` 403 documentation matching real enforcement.

There is still no `sql-query.execute` / `.save` / `.drop` App-ID triad as some older text described, and **no `AppIdGuard` on any route in this controller** — the `x-app-id` header is declared for Swagger (`@ApiHeaderRequiredXAppId()`) but is not enforced here. Enforcement is the two `sql_workbench.*` platform permissions and nothing else.

The rest of this page (catalog projections, save/DDL contract, response shapes) still matches the backend source and is unchanged below.

## 1. What & Who

Query Dataset (internally "SQL Workbench") is a **backend admin-SQL-console service** for running arbitrary SQL and creating / browsing / dropping reusable database objects — **views**, **stored procedures**, and **functions** — directly inside the tenant database. There is currently **no frontend screen that calls it** (see Implementation status). Outputs are intended to become the data source for report templates and dashboard tiles, consumed at run time by the separate **micro-data** service.

**Audience today:** operators holding `sql_workbench.read` (browse) or `sql_workbench.manage` (run / save / drop), whether they work through the Platform SPA's [SQL Workbench](/en/platform/sql-workbench) screen or call the API directly (e.g. via Bruno). There is no audience inside *this* product, because Carmen Inventory has no screen for it. Unlike most Carmen tables, **there is no `tb_query_dataset` row** for each saved object — the registry is the live PostgreSQL catalog scoped to the tenant schema.

The views, stored procedures, and functions authored here are intended as data sources the **micro-data** service executes at run time: a report or dashboard would name one (by `builder_key` or template `name`), and micro-data resolves it via `POST /api/datasets/execute`, composes the WHERE clause from the supplied filters, fans the query across the requested business units, and returns a `Dataset` (columns + rows + totals + summary). See [reporting-audit/report](/en/inventory/reporting-audit/report) for the render side. This linkage was not independently re-verified in this pass.

## 2. Common Tasks

No UI exists *in Carmen Inventory* (see Implementation status) — these are the underlying API operations, reachable through the Platform SPA's [SQL Workbench](/en/platform/sql-workbench) or callable directly (e.g. via Bruno).

| Task | API call | Notes |
|---|---|---|
| Run arbitrary SQL | `POST .../sql-query/execute` | **Not read-only** — any statement type, multiple statements, gated by `sql_workbench.manage` |
| Save a `SELECT` as a view | `POST .../sql-query/save` with bare `SELECT` + `name` + `query_type: "view"` | Server auto-wraps as `CREATE OR REPLACE VIEW "<name>" AS …`; single-statement `SELECT`/`WITH` only |
| Create a stored procedure / function | `POST .../sql-query/save` with full DDL (`CREATE OR REPLACE PROCEDURE/FUNCTION …`) | Bare bodies are rejected — full DDL required |
| Browse existing objects | `GET .../sql-query/db-objects` | Tables / Views / Procedures / Functions / columns |
| View an object's definition | `GET .../sql-query/db-objects/definition?type=&schema=&name=` | Loads `pg_get_viewdef` / `pg_get_functiondef` |
| Drop an object | `DELETE .../sql-query/db-objects?type=&schema=&name=` | No undo; bound reports will error |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `execute` runs a `DROP TABLE` / `DELETE` / multi-statement script successfully | Expected — `execute` has no statement-type or multi-statement restriction; only `sql_workbench.manage` gates the caller | Do not treat `execute` as a safe read-only console |
| "Forbidden statement" on `save` | `save`'s bare-`SELECT` or `CREATE`-only validation rejected a `DROP`/`TRUNCATE`/etc. keyword | `save` (unlike `execute`) keeps the blocklist — rewrite as valid DDL |
| "Name is required" on save | Bare `SELECT` + Type `View` without a name | Provide the view name (quoting applied for injection safety) |
| Procedure / function save rejected | Bare body supplied | Wrap in `CREATE OR REPLACE PROCEDURE/FUNCTION …` DDL |
| `statement_timeout` after 30 s | Query exceeded budget | Add filters / indexes; transaction budget 35 s, max-wait 8 s |
| "Database is busy" | Connection pool exhausted; one retry already attempted after 500 ms | Retry later; investigate concurrent load |
| `BigInt` column returns as string in result | Expected — JSON cannot natively carry `bigint` | Cast in SQL if numeric handling needed downstream |
| Report errors after drop | Bound view / procedure removed from catalog | Re-create the object or update the report binding |
| 403 on `execute`, `save` or `DELETE db-objects` | Caller lacks `sql_workbench.manage` | Grant via the platform's permission system — see [Platform RBAC](/en/platform/rbac) |
| 403 on `GET db-objects` or `db-objects/definition` | Caller lacks `sql_workbench.read` | Same; `.read` is the browse-only grant |
| `save` / list / get-definition / drop succeed for any authenticated caller | **Historical only — fixed 2026-08-20 by `525597688`.** If you observe this today, you are on a build older than that commit | Upgrade; do not treat it as expected behaviour |

## 4. Edge Cases

- **`execute` is not read-only and not single-statement.** Confirmed via `validateSqlSafety(sql_text, { allowMultiple: true, allowDangerous: true })` — see Implementation status.
- **`save` keeps the restrictive validation** this page previously attributed to `execute`: bare `SELECT`/`WITH` single-statement for views, `CREATE`-only (multiple `CREATE` statements allowed) for pre-written DDL.
- **Tenant-scoped credentials.** `prismaTenantInstance(bu_code, user_id)` provides the connection — every query and DDL runs inside the tenant's PostgreSQL role / schema; **cross-tenant access is impossible at the database layer**, regardless of how permissive the statement-type check is.
- **No version history in Carmen.** `CREATE OR REPLACE` discards previous text.
- **Drop is destructive and immediate.** Dropped catalog entry breaks any bound report or widget on next run.
- **Bare-SELECT auto-wrap only for views.** Procedures and functions require full DDL (in `save`).
- **BigInt safety.** Result rows post-processed so `bigint` columns are stringified; column order preserved from the first row.

---

## 5. Backing Service / Data Shape (Dev)

**No bespoke table.** The "data model" is the live PostgreSQL catalog plus a thin set of API endpoints.

### 5.1 PostgreSQL catalog projections (sidebar tree)

Four catalog queries scoped to `current_schema()`:

```
tables     → pg_class    WHERE relkind = 'r'   (excluding extension-owned)
views      → pg_class    WHERE relkind = 'v'   (excluding extension-owned)
procedures → pg_proc     WHERE prokind IN ('p','f')
columns    → pg_attribute joined to pg_class for table/view/materialised-view cols
```

`DbObjectsResponse` shape:

```jsonc
{
  "tables":     [{ "schema": "tenant_t01", "name": "tb_purchase_request" }, ...],
  "views":      [{ "schema": "tenant_t01", "name": "v_pr_summary" }, ...],
  "procedures": [{ "schema": "tenant_t01", "name": "sp_close_period", "kind": "procedure" }, ...],
  "columns":    [{ "table": "tb_purchase_request", "column": "id", "data_type": "uuid" }, ...]
}
```

### 5.2 Object definition (edit flow)

Click an existing view / procedure / function → fetch `pg_get_viewdef` or `pg_get_functiondef` → load into editor as `CREATE OR REPLACE …` ready to re-save.

### 5.3 Save / Drop contract

`POST /api/config/:bu_code/sql-query/save`:

```jsonc
{
  "name": "v_pr_summary",                       // required when bare SELECT
  "sql_text": "SELECT id, doc_no FROM tb_pr",  // full DDL or bare SELECT
  "query_type": "view"                          // "view" | "stored_procedure" | "function"
}
```

`DELETE /api/config/:bu_code/sql-query/db-objects?type=…&schema=…&name=…` drops the named object.

### 5.4 Related (not the same)

- `tb_dashboard_bu_widget` / `tb_dashboard_personal_widget` — dashboard widget tiles (BU-scoped / per-user); each row stores a `dataset_id` reference into the code-registered [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog, **not** SQL text — separate from catalog objects. (A prior version cited a `tb_widget_workspace` table storing per-user ad-hoc SQL; no such model exists in any Prisma schema.)
- `tb_report_job.report_type` / `tb_report_schedule.report_type` — string keys mapped to report definitions that may *consume* a view, but the mapping lives in the reports module.

## 6. Business Rules

- **`execute` gated by `sql_workbench.manage`** — note that despite the name, `.manage` (not `.read`) is what lets an operator run *anything* through `execute`, including a plain `SELECT`.
- **`execute` allows any statement type, including DDL/DML, and multiple statements** (`allowDangerous: true`, `allowMultiple: true`) — confirmed **not** read-only, contrary to this page's prior version.
- **`save` is `CREATE`-only:** full DDL (`allowedLeading: ['CREATE']`) or bare SELECT for views (`['SELECT', 'WITH']`), and is gated by `sql_workbench.manage`.
- **`db-objects` (list/get-definition) require `sql_workbench.read`; `db-objects` (drop) requires `sql_workbench.manage`.**
- **30-second statement timeout** inside a 35 s Prisma transaction budget (8 s max-wait), on `execute`.
- **Tenant-scoped credentials** via `prismaTenantInstance(bu_code, user_id)` — cross-tenant access is impossible at the DB layer regardless of statement type.
- **Connection-pool retry** — 500 ms wait, one retry, then "Database is busy" (on both `execute` and `saveDdl`).
- **BigInt safety** on `execute` response (stringified); column order preserved.
- **Bare-SELECT view requires a name**; quoting applied for injection safety.
- **Procedures / functions must be full DDL** (in `save`).
- **No version history** — `CREATE OR REPLACE` discards previous text.

## 7. Cross-References

- [reporting-audit/report](/en/inventory/reporting-audit/report) — report templates are intended to bind to views created here; linkage not independently re-verified this pass.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — dashboard widgets reference code-registered `dataset_id`s (`tb_dashboard_bu_widget` / `tb_dashboard_personal_widget`), not ad-hoc SQL; a prior version's `tb_widget_workspace` claim was unbacked (no such table exists).
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) — scheduled reports consume the same views (unconfirmed this pass).
- [system-config/period](/en/inventory/system-config/period) — period-close objects (`sp_close_period`, `v_period_snapshot`) typically live here (unconfirmed this pass).

## 8. References

- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-query.service.ts` — `execute`, `saveDdl`, `listDbObjects`, `getDbObjectDefinition`, `dropDbObject`.
- **Backend gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_sql-query/config_sql-query.controller.ts` — re-read 2026-09-06: `PlatformPermissionGuard` + `RequirePlatformPermission` on **all five** routes (`execute` `:70-71`, `save` `:119-120`, `db-objects` `:174-175`, `db-objects/definition` `:209-210`, `DELETE db-objects` `:258-259`). No `AppIdGuard` anywhere in the file.
- **SQL safety validator:** `../carmen-turborepo-backend-v2/apps/micro-business/src/sql-query/sql-validator.ts` — `FORBIDDEN_LEADING` blocklist, `allowDangerous` bypass flag.
- **Frontend:** none found. No `query-dataset` or `sql-query` file exists anywhere in `../carmen-inventory-frontend-react` (confirmed by repo-wide search); no route in `routes/router.tsx`.
- **Related Prisma:** `tb_report_job` (line ~6101), `tb_report_schedule` (line ~6135), `tb_dashboard_bu_widget` (line ~6185), `tb_dashboard_personal_widget` (line ~6205).
