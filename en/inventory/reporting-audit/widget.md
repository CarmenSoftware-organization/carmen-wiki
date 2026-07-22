---
title: Widget
description: Dashboard widget entity — BU-scoped and per-user tiles bound to a code-registered dataset catalog, served by the micro-data Go service. The tb_widget_workspace / tb_widget_dashboard / tb_widget_dashboard_item / tb_widget_default_layout family this page previously documented does not exist.
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

> **At a Glance**
> **Owner:** End users (personal widgets) + BU members implicitly (BU widgets — no distinct "BU admin" edit gate found) &nbsp;·&nbsp; **Tables:** `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` (tenant schema) &nbsp;·&nbsp; **Used by:** the [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) `/dashboard` screen (personal) and the per-module landing dashboards under Procurement / Inventory-management / Vendor-management / Product-management / Operation-plan / Config (BU) &nbsp;·&nbsp; **Served by:** micro-data (Go)

## Implementation status (verified 2026-07-22)

The previous version of this page documented a `tb_widget_dashboard` / `tb_widget_dashboard_item` / `tb_widget_default_layout` / `tb_widget_workspace` table family as the live widget system. A repo-wide search of every Prisma schema (tenant, platform, file) found **zero `model tb_widget_*` declarations of any kind** — `tb_widget_dashboard`, `tb_widget_dashboard_item`, and `tb_widget_default_layout` never existed. `tb_widget_workspace` *did* exist briefly — created by migration `20260512180928_widget_system_replace_dashboard` (tenant schema) — but was dropped nine days later by migration `20260521040013_remove_widget_system` (`DROP TABLE IF EXISTS "tb_widget_workspace" CASCADE`, alongside `tb_widget_dashboard`, `tb_widget_dashboard_item`, `tb_widget_default_layout`, and `tb_widget_comment` in the same migration). No data-explorer/saved-query feature exists anywhere in the current frontend or backend to have used it.

The real, currently-live widget tables are `tb_dashboard_bu_widget` and `tb_dashboard_personal_widget` — both described below. This page is rewritten to describe them.

## 1. What & Who

The widget entity is the **dashboard tile layer** — a placement of a code-registered [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) feed (`dataset_id`), rendered as a chart (`widget_type`), on either a business unit's shared dashboard or a single user's personal dashboard. There are exactly two tables, both **tenant-scoped** (resolved by `bu_code` — the tenant schema *is* the BU, so neither table carries a `business_unit_id` column):

- `tb_dashboard_bu_widget` — a widget on a business unit's shared dashboard. Powers the per-module landing dashboards (e.g. `procurement-dashboard.tsx` → `useProcurementWidgets` → `GET api/:bu_code/dashboard-widgets/bu`), **not** this reporting-audit module's own screens.
- `tb_dashboard_personal_widget` — a widget on one user's personal dashboard, scoped by `user_id`. Powers the `/dashboard` route's Widget Workspace — see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) for the full UI walkthrough (add/reorder/delete, drag-and-drop, empty state).

There is no default-layout table and no seeding mechanism — a new user's personal dashboard starts empty; a new BU's shared dashboard starts empty. There is no saved-query / data-explorer feature of any kind — `dataset_id` always references a fixed entry in the code-registered [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog, never a user-authored query.

**Maintained by** end users (their own personal widgets). BU widgets have no distinct "BU admin" gate found in the backend-gateway controllers — the CRUD endpoints below carry no extra role check beyond standard authentication, so in practice any authenticated user with `bu_code` context can create/edit/delete a BU widget. **Read by** [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) (personal) and each module's own landing dashboard component (BU).

### 1.1 Where widget CRUD runs (micro-data)

Widget create/read/update/delete is hosted by the **micro-data** service (Go), not micro-cluster. `micro-data/controller/dashboard_controller.go`'s own doc comment states it explicitly: *"exposes the dashboard dataset catalogue/execution and the BU + personal widget CRUD over HTTP. The backend-gateway calls these instead of micro-business (datasets) / micro-cluster (widgets)."* The backend-gateway's `DashboardBuWidgetsService` / `DashboardPersonalWidgetsService` are thin HTTP proxies (`fetch` to `DATASET_SERVICE_HOST:DATASET_SERVICE_HTTP_PORT`) — they hold no business logic and no direct DB connection of their own.

| Scope | micro-data endpoints (proxied by backend-gateway) |
|---|---|
| **BU widgets** | `GET/POST /api/dashboard/bu-widgets?bu_code=` · `GET/PATCH/DELETE /api/dashboard/bu-widgets/:id?bu_code=` |
| **Personal widgets** | `GET/POST /api/dashboard/personal-widgets?user_id=&bu_code=` · `GET/PATCH/DELETE /api/dashboard/personal-widgets/:id?user_id=&bu_code=` · `POST /api/dashboard/personal-widgets/reorder?user_id=&bu_code=` (atomic bulk `order_index` update) |

The gateway-facing routes the frontend actually calls are `api/me/dashboard-widgets` (personal, resolves `user_id` from the auth header) and the equivalent BU controller — see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) §5 and §8 for the exact frontend hooks and gateway controllers.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a personal widget | `/dashboard` → **+ Add widget** | Picker filters the dataset catalog by supported shape (`scalar`, `scalar_delta`, `categorical`); see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) |
| Reorder personal widgets | `/dashboard` → drag a widget card | Optimistic `order_index` update, then `POST .../personal-widgets/reorder` |
| Delete a personal widget | `/dashboard` → widget card menu | `DELETE .../personal-widgets/:id` — soft delete (`deleted_at`) |
| Add/edit a BU widget | Each module's own landing dashboard (e.g. `/procurement`) | Same CRUD shape as personal widgets, scoped by `bu_code` only |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Personal widget not visible to a teammate | Expected — personal widgets are `user_id`-scoped, never shared | Use a BU widget on the module's own landing dashboard instead |
| Widget card shows an error state | `dataset_id` fetch failed or the dataset was removed from the catalog | Remove and re-add from the picker; see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) |
| 404 on widget update/delete | `PersonalFindOne`/`BuFindByID` filters `deleted_at IS NULL` — id already soft-deleted or never existed | Re-fetch the widget list |
| Reorder appears to fail silently | `PersonalReorder` updates rows in a loop inside one DB transaction — a mid-batch failure rolls back the whole reorder | Retry; check the PATCH response for the specific id that failed |

## 4. Edge Cases

- **No default/seed layout.** Unlike the previously-documented (nonexistent) `tb_widget_default_layout`, there is no seed mechanism at all — every new user's and every new BU's widget grid starts empty.
- **No workspace/saved-query concept.** `dataset_id` only ever references a fixed catalog entry; there is no user-authored query of any kind anywhere in this system.
- **No BU-widget authorization gate found.** The BU widget endpoints require `bu_code` but no additional "BU admin" role check was found in `dashboard-bu-widgets.controller.ts` — flagging as unconfirmed rather than asserting a specific admin-only rule.
- **Params are dataset-scoped config, not request context.** `WidgetCreateInput.Params` (JSONB) holds dataset-specific filter config (e.g. a status filter) set at widget-creation time — it does not carry `user_id`/`bu_code`, which are always supplied by the caller at execution time.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_dashboard_bu_widget`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `dataset_id` | `String @db.VarChar(100)` | No | References a [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog entry (no FK — code registry, not a table). |
| `widget_type` | `enum_dashboard_widget_type` | No | `kpi` / `line` / `area` / `bar` / `pie` / `heatmap` / `gauge` / `table` / `sparkline`. |
| `title` | `String? @db.VarChar(255)` | Yes | Optional override; falls back to the dataset's own display name. |
| `order_index` | `Int` | No | Default `0`. Grid position. |
| `params` | `Json? @db.JsonB` | Yes | Dataset-scoped filter config. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Optimistic-concurrency counter. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `[deleted_at]` (`tenant_dashboard_bu_widget_deleted_idx`). No `business_unit_id` column — the tenant schema itself is the BU boundary.

### 5.2 `tb_dashboard_personal_widget`

Identical shape to `tb_dashboard_bu_widget` plus a `user_id String @db.Uuid` scoping column. **Indexes:** `[user_id, deleted_at]` (`tenant_dashboard_personal_widget_user_deleted_idx`).

### 5.3 `enum_dashboard_widget_type`

`kpi`, `line`, `area`, `bar`, `pie`, `heatmap`, `gauge`, `table`, `sparkline` — 9 values. The dataset catalog itself carries 6 shapes (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`; see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset)); not every shape × type combination is exercised by the current frontend picker (the `/dashboard` picker only ever creates `kpi` or `pie` widgets — see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) §1 for the exact narrowing).

## 6. Business Rules

- **Tenant-scoped, no BU FK.** Both tables live in each tenant's own schema; `bu_code` resolution happens at the connection layer, not via a foreign key column.
- **Personal widgets are strictly per-user.** No sharing mechanism of any kind exists — `PersonalFindOne`/`PersonalFindByID` always filter by `user_id`.
- **Soft delete only.** Both tables use `deleted_at`; no hard delete found.
- **Reorder is transactional.** `PersonalReorder` wraps the batch `order_index` update in one DB transaction (`tdb.Transaction(...)` in `micro-data/db/widget_repo.go`).
- **No default/seed layout.** New personal and BU widget lists start empty — confirmed absent, not merely undocumented.

## 7. Cross-References

- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the live `/dashboard` screen this page's `tb_dashboard_personal_widget` data backs; full UI walkthrough, hooks, and gateway controllers.
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — the code-registered catalog every `dataset_id` references.
- [access-control/user](/en/inventory/access-control/user) — owner of personal widgets (`user_id`).
- [master-data/business-unit](/en/inventory/master-data/business-unit) — bounds BU-widget visibility (tenant = BU).
- All transactional modules — common dataset sources for tiles (procurement, inventory, vendor, product, recipe categories in the dataset catalog).

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_dashboard_widget_type` (line ~6155), `tb_dashboard_bu_widget` (line ~6178), `tb_dashboard_personal_widget` (line ~6198).
- **Migrations (history):** `20260512180928_widget_system_replace_dashboard` (created the now-dropped `tb_widget_workspace` family), `20260521040013_remove_widget_system` (dropped it, "Drop widget subsystem").
- **micro-data service (Go):** `../micro-data/controller/dashboard_controller.go` (HTTP handlers for both dataset execution and widget CRUD), `../micro-data/service/widget_service.go`, `../micro-data/db/widget_repo.go`, `../micro-data/model/dashboard.go`.
- **Backend gateway (proxy layer):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-bu-widgets.controller.ts` + `.service.ts`, `dashboard-personal-widgets.controller.ts` + `.service.ts`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx` + `sortable-widget-item.tsx`; `hooks/use-my-dashboard-widgets.ts`.
