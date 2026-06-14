---
title: Dashboard Dataset
description: Read-only admin catalog of code-registered data feeds — the named, typed data sources that dashboard widgets pull from, distinct from the user widget workspace layout and from SQL-authored query-dataset views.
published: true
date: 2026-06-09T00:00:00.000Z
tags: system-config, dashboard, dataset, widget, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Dashboard Dataset

> **At a Glance**
> **Owner:** Sysadmin (read-only catalog) &nbsp;·&nbsp; **Backing:** Code-registered in the **micro-data** service (`GET /api/dashboard/datasets`), proxied by backend-gateway over HTTP — **no dedicated tenant table** &nbsp;·&nbsp; **Used by:** [reporting-audit/widget](/en/inventory/reporting-audit/widget) (widget picker), dashboard tiles &nbsp;·&nbsp; **68 shaped feeds** (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`) across inventory, workflow, procurement, product, vendor, recipe, and equipment categories.

## 1. What & Who

Dashboard Dataset is the **read-only admin catalog screen** at `/system-admin/dashboard-dataset`. It exposes every named data feed that dashboard widgets can subscribe to. Each dataset entry is a **code-registered definition** in the **micro-data** microservice (Go), executed against the tenant database and proxied to the gateway over HTTP — not a sysadmin-editable database row. The catalog is fixed per application version; sysadmins browse and search it to understand what feeds are available before placing or configuring widgets.

**How it differs from the other two related concepts:**

| Concept | Nature | Editable? | Stored in |
|---|---|---|---|
| **Dashboard Dataset** (this page) | Named data feed catalog — query runs against tenant DB and returns typed data | Read-only; updated by code deployment | **micro-data** service (Go), served at `/api/dashboard/datasets` |
| [system-config/query-dataset](/en/inventory/system-config/query-dataset) | SQL Workbench — admin authors tenant views / stored procedures / functions | Sysadmin creates/drops catalog objects | PostgreSQL catalog (`pg_class`, `pg_proc`) |
| [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) | Per-user saved dashboard layout — which datasets are shown, in what size, in what order | Each user edits their own layout | `tb_widget_dashboard` + `tb_widget_dashboard_item`, seeded by `tb_widget_default_layout` (tenant DB) |

**Maintained by** Engineering (code releases). **Browsed by** Sysadmin to audit available feeds. **Consumed by** the widget picker inside the dashboard `Add widget` dialog.

Each dataset executes inside a **read-only transaction** with `SET LOCAL search_path` pinned to the caller's tenant schema, so a single deployed catalog serves every tenant safely. The backend-gateway is a thin proxy: `GET /api/dashboard/datasets` lists the catalogue (`{items,count}`) and `GET /api/dashboard/datasets/:id?bu_code=&user_id=` executes one feed (`{meta,data}`).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Browse the full dataset catalog | System Admin → Dashboard Dataset | Lists all feeds grouped by category |
| Search for a specific dataset | Search bar at top of page | Filters by id, name, description, or category |
| Identify the shape of a dataset | `shape` badge on each card | See §5.1 for shape meanings |
| Add a dataset to a widget | Dashboard → Add widget → dataset picker | Opens a popover backed by this catalog |
| Preview a dataset's live value | Dashboard widget preview | Calls `GET /api/:bu_code/datasets/:dataset_id` |
| Add a new dataset feed | Code change in **micro-data** service | Engineering task — requires deployment |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Page shows "No datasets available" | Business unit context not resolved or API returned empty | Check `bu_code` in session; confirm microservice is running |
| Dataset missing from catalog | Not yet registered in code registry | Engineering must add a `DatasetDefinition` entry and deploy |
| Widget errors on load after picking dataset | Dataset `id` references removed or renamed across deployments | Re-select a current dataset from the catalog |
| 403 on `/system-admin/dashboard-dataset` route | User lacks Sysadmin role or App ID permission | Grant via [access-control/application-role](/en/inventory/access-control/application-role) |
| Dataset returns stale value | Catalog list is cached (`CACHE_STATIC`); individual values use `CACHE_DYNAMIC` (1-minute TTL) | Hard-refresh the page or wait for cache expiry |

## 4. Edge Cases

- **No database backing for the catalog.** The list endpoint reads from a compile-time registry — there is no `tb_dashboard_dataset` table to query or migrate. Adding feeds requires a code release.
- **Shape contract is strict.** Each dataset declares one of six shapes (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`). The frontend widget renderer narrows on `meta.shape`; a shape mismatch between registry and frontend code causes a render error.
- **Tenant-scoped execution.** When a widget fetches data, **micro-data** runs the query inside a read-only transaction with `SET LOCAL search_path` pinned to the caller's tenant schema (`bu_code`) — every query is confined to the correct tenant schema; cross-tenant data access is impossible.
- **Categories are soft.** `category` is a free string on the registry entry (common values: `inventory`, `workflow`, `movement`, `spend`, `variance`). The UI groups cards alphabetically by category; unknown future categories appear automatically.
- **Cache split.** The catalog list is `CACHE_STATIC` (long-lived); individual dataset payloads use `CACHE_DYNAMIC` (1-minute). Stale catalog entries survive until the next hard-refresh.
- **`unit` is display-only.** The `unit` field (e.g. `items`, `฿`, `%`, `days`) is a hint for the widget tile label — it does not affect data computation.

---

## 5. Data Shape (Dev)

**No bespoke tenant table.** The catalog is code-registered in micro-data (Go); the field tables below describe the wire contract returned to the gateway and frontend.

### 5.1 `DatasetMeta` — catalog entry shape

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Dot-namespaced identifier, e.g. `inventory.low-stock-count`. Used as the widget `dataset_id` reference. |
| `name` | `string` | Human-readable label shown on the catalog card. |
| `description` | `string?` | Optional longer description. |
| `shape` | `enum_dataset_shape` | One of: `scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`. Determines the payload structure the widget renderer expects. |
| `category` | `string` | Functional grouping. Current values: `inventory`, `workflow`, `movement`, `spend`, `variance`. |
| `unit` | `string?` | Display-only hint, e.g. `items`, `฿`, `%`. |

### 5.2 `enum_dataset_shape` — payload contracts

| Shape | Payload structure | Typical widget |
|---|---|---|
| `scalar` | `{ value: number }` | KPI tile |
| `scalar_delta` | `{ value: number; prev: number; change?: string }` | KPI tile with trend arrow |
| `time_series` | `Array<{ date: string; value: number }>` | Line / area / sparkline chart |
| `categorical` | `Array<{ label: string; value: number; color?: string }>` | Bar / pie / donut chart |
| `ranked` | `Array<{ rank: number; label: string; value: number; extras?: … }>` | Ranked bar / data table |
| `matrix` | `{ rows: string[]; cols: string[]; values: number[][] }` | Heatmap / cross-tab table |

### 5.3 API endpoints

```
GET  /api/:bu_code/datasets              → { items: DatasetMeta[], count: number }
GET  /api/:bu_code/datasets/:dataset_id  → { meta: DatasetMeta, data: DatasetData<shape> }
```

Both require `Authorization: Bearer <token>` and `X-App-Id` header. The `list` response is used by the widget picker; the `get` response feeds the live widget tile. Internally the gateway no longer runs the query itself — it proxies over HTTP to the micro-data service (`GET /api/dashboard/datasets` and `GET /api/dashboard/datasets/:id?bu_code=&user_id=`), which executes the dataset and returns the result.

### 5.4 Registry location

The dataset catalog is code-registered in the **micro-data** service (Go): handlers in `../micro-data/controller/dashboard_controller.go`, dataset/widget logic in `../micro-data/service/dashboard/` and `../micro-data/service/widget_service.go`, and models in `../micro-data/model/dashboard.go`. At the time of writing the catalog contains **68** shaped datasets across inventory, procurement, product, vendor, recipe, equipment, and config categories.

## 6. Business Rules

- **Read-only catalog.** Sysadmins cannot create, edit, or delete catalog entries through the UI — the catalog is code-managed.
- **Tenant-scoped queries.** Every dataset query runs in micro-data inside a read-only transaction with `SET LOCAL search_path` pinned to the caller's `bu_code` schema — all data is read from the calling tenant's schema.
- **Shape contract is rigid.** Frontend widget renderers switch on `meta.shape`; adding a new shape requires frontend and backend changes in lockstep.
- **No CRUD permissions needed to browse.** The screen is visible to Sysadmin by navigation access; no per-dataset permission granularity exists — all registered datasets are readable by any authenticated user who can load the dashboard.
- **`id` is stable per entry.** The dot-namespaced id (e.g. `workflow.pr-pending-approval`) is stored as the `dataset_id` in widget tile configurations in `tb_widget_dashboard_item`. Renaming or removing a registry entry breaks existing widget configs.

## 7. Cross-References

- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — dashboard widgets select their data source from this catalog; the `dataset_id` field on each widget row references a catalog `id`.
- [system-config/query-dataset](/en/inventory/system-config/query-dataset) — complementary admin tool: sysadmin authors tenant views / stored procedures / functions in SQL; those objects can back report templates. Dashboard Dataset feeds are code-authored, not SQL-authored.
- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the per-user saved dashboard layout stored in `tb_widget_dashboard` + `tb_widget_dashboard_item`; each tile row references a `dataset_id` from this catalog. (Note: `tb_widget_workspace` is a separate table for per-user saved data-explorer queries — see [reporting-audit/widget](/en/inventory/reporting-audit/widget).)
- [access-control/application-role](/en/inventory/access-control/application-role) — navigation and route access to `/system-admin/dashboard-dataset`.

## 8. References

- **micro-data service (Go):** `../micro-data/` — dashboard datasets + widget CRUD. Handlers: `controller/dashboard_controller.go`; logic: `service/dashboard/`, `service/widget_service.go`; models: `model/dashboard.go`; routes: `routes/routes.go`; overview: `README.md`.
- **Gateway proxy:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-datasets/dashboard-datasets.service.ts` — HTTP proxy to micro-data; controller `dashboard-datasets.controller.ts` exposes `GET /api/:bu_code/datasets` and `GET /api/:bu_code/datasets/:dataset_id`.
- **Swagger response DTOs:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-datasets/swagger/response.ts` — `DatasetMetaDto`, `DatasetListResponseDto`, `DatasetResponseDto`.
- **Platform enum:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `enum_dataset_shape` (line ~815).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/dashboard-dataset/page.tsx` and `_components/dashboard-dataset-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-dashboard-dataset.ts` — `useDashboardDatasets()`, `useDashboardDatasetDetail(id)`.
- **Frontend type:** `../carmen-inventory-frontend-react/types/dashboard-dataset.ts` — `DashboardDataset`, `DashboardDatasetShape`, `DashboardDatasetCategory`.
