---
title: Dashboard Dataset
description: Read-only admin catalog of code-registered data feeds in micro-data (62 definitions, seven shapes, per-shape supported_renders) that dashboard widgets pull from — distinct from widget layout and SQL-authored views.
published: true
date: 2026-09-23T10:06:26.000Z
tags: system-config, dashboard, dataset, widget, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Dashboard Dataset

> **At a Glance**
> **Owner:** Sysadmin (read-only catalog) &nbsp;·&nbsp; **Backing:** Code-registered in the **micro-data** service (`GET /api/dashboard/datasets`), proxied by backend-gateway over HTTP — **no dedicated tenant table** &nbsp;·&nbsp; **Used by:** [reporting-audit/widget](/en/inventory/reporting-audit/widget) (widget picker), dashboard tiles &nbsp;·&nbsp; **Permission / licence:** `dashboard.dataset.view` / `dashboard.dataset` (`module-list.ts:736-742`; licence routes `app:datasets`, `app:dashboard-lab`) &nbsp;·&nbsp; **62 registered definitions** (`ENTRIES` in `../micro-data/service/dashboard/registry.go`, counted 2026-09-22: 16 `scalar`, 9 `scalar_delta`, 6 `time_series`, 21 `categorical`, 7 `ranked`, 3 `matrix`) across inventory, workflow, document, procurement, product, vendor, recipe, and equipment categories; a seventh shape, `table`, exists in the model (`model/dashboard.go:17`) but no registry entry uses it yet. A prior version said 68.

![Dashboard Dataset screen](/screenshots/system-config/dashboard-dataset.png)

## Implementation status (re-verified 2026-09-22)

- **`supported_renders` is on the catalog entry** (BE `6dfe58992`, 2026-09-07; `swagger/response.ts:50-57`, FE `types/dashboard-dataset.ts:19`): the backend owns the list of widget render types a shape can be drawn as (`dashboard.SupportedRenders(shape)` in `../micro-data/service/widget_service.go:94-114`), and `PATCH` on a widget with a `widget_type` outside that list is rejected as `ErrInvalidWidget` instead of rendering a broken tile.
- **Gateway → micro-data calls carry `x-internal-token`** since BE `c94a625ed` (2026-09-21) — without it the whole dashboard answered 401 after micro-data's internal-token middleware landed. Nothing changes for the browser, which still calls the gateway.
- The PR/PO/SR/GRN "pending" KPI tiles moved from per-document `fn_dash_*_pending` functions to `document.{pr,po,sr,grn}-pending` entries over shared `v_dash_*_base` views (registry comment `:20-25`); ids of the form `workflow.<doc>-pending-approval` for those four no longer exist.

## 1. What & Who

Dashboard Dataset is the **read-only admin catalog screen** at `/system-admin/dashboard-dataset`. It exposes every named data feed that dashboard widgets can subscribe to. Each dataset entry is a **code-registered definition** in the **micro-data** microservice (Go), executed against the tenant database and proxied to the gateway over HTTP — not a sysadmin-editable database row. The catalog is fixed per application version; sysadmins browse and search it to understand what feeds are available before placing or configuring widgets.

**How it differs from the other two related concepts:**

| Concept | Nature | Editable? | Stored in |
|---|---|---|---|
| **Dashboard Dataset** (this page) | Named data feed catalog — query runs against tenant DB and returns typed data | Read-only; updated by code deployment | **micro-data** service (Go), served at `/api/dashboard/datasets` |
| [system-config/query-dataset](/en/inventory/system-config/query-dataset) | SQL Workbench — admin authors tenant views / stored procedures / functions | Sysadmin creates/drops catalog objects | PostgreSQL catalog (`pg_class`, `pg_proc`) |
| [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) | Saved dashboard widget tiles — which datasets are shown, in what order | BU admins (BU tiles) + each user (personal tiles) | `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` (tenant DB, lines ~6185/~6205 — a prior version cited `tb_widget_dashboard`/`tb_widget_dashboard_item`/`tb_widget_default_layout`, none of which exist in any Prisma schema) |

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
| `shape` | `enum_dataset_shape` | One of: `scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`, `table` (model only, unused in the registry). Determines the payload structure the widget renderer expects. |
| `category` | `string` | Functional grouping. Values seen in the registry: `inventory`, `workflow`, `document`, `movement`, `spend`, `variance`, … |
| `unit` | `string?` | Display-only hint, e.g. `items`, `฿`, `%`. |
| `supported_renders` | `string[]?` | Widget render types legal for this shape (backend-owned; 2026-09-07). |

### 5.2 `enum_dataset_shape` — payload contracts

| Shape | Payload structure | Typical widget |
|---|---|---|
| `scalar` | `{ value: number }` | KPI tile |
| `scalar_delta` | `{ value: number; prev: number; change?: string }` | KPI tile with trend arrow |
| `time_series` | `Array<{ date: string; value: number }>` | Line / area / sparkline chart |
| `categorical` | `Array<{ label: string; value: number; color?: string }>` | Bar / pie / donut chart |
| `ranked` | `Array<{ rank: number; label: string; value: number; extras?: … }>` | Ranked bar / data table |
| `matrix` | `{ rows: string[]; cols: string[]; values: number[][] }` | Heatmap / cross-tab table |
| `table` | `{ columns: [{ key, label, type? }]; rows: [{ <key>: <val> }] }` | Data table (declared in `model/dashboard.go:17`; no registry entry yet) |

### 5.3 API endpoints

```
GET  /api/:bu_code/datasets              → { items: DatasetMeta[], count: number }
GET  /api/:bu_code/datasets/:dataset_id  → { meta: DatasetMeta, data: DatasetData<shape> }
```

Both require `Authorization: Bearer <token>` and `X-App-Id` header. The `list` response is used by the widget picker; the `get` response feeds the live widget tile. Internally the gateway no longer runs the query itself — it proxies over HTTP to the micro-data service (`GET /api/dashboard/datasets` and `GET /api/dashboard/datasets/:id?bu_code=&user_id=`), which executes the dataset and returns the result.

### 5.4 Registry location

The dataset catalog is code-registered in the **micro-data** service (Go): handlers in `../micro-data/controller/dashboard_controller.go`, dataset/widget logic in `../micro-data/service/dashboard/` (`registry.go` `ENTRIES`, plus `document.go`, `ops.go`, `replenishment.go`, `visibility.go`, `windows.go`) and `../micro-data/service/widget_service.go`, and models in `../micro-data/model/dashboard.go`. At HEAD (2026-09-22) the catalog contains **62** shaped datasets.

## 6. Business Rules

- **Read-only catalog.** Sysadmins cannot create, edit, or delete catalog entries through the UI — the catalog is code-managed.
- **Tenant-scoped queries.** Every dataset query runs in micro-data inside a read-only transaction with `SET LOCAL search_path` pinned to the caller's `bu_code` schema — all data is read from the calling tenant's schema.
- **Shape contract is rigid.** Frontend widget renderers switch on `meta.shape`; adding a new shape requires frontend and backend changes in lockstep.
- **No CRUD permissions needed to browse.** The screen is visible to Sysadmin by navigation access; no per-dataset permission granularity exists — all registered datasets are readable by any authenticated user who can load the dashboard.
- **`id` is stable per entry.** The dot-namespaced id (e.g. `workflow.pr-pending-approval`) is stored as the `dataset_id` in widget tile rows (`tb_dashboard_bu_widget` / `tb_dashboard_personal_widget`). Renaming or removing a registry entry breaks existing widget configs.

## 7. Cross-References

- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — dashboard widgets select their data source from this catalog; the `dataset_id` field on each widget row references a catalog `id`.
- [system-config/query-dataset](/en/inventory/system-config/query-dataset) — complementary admin tool: sysadmin authors tenant views / stored procedures / functions in SQL; those objects can back report templates. Dashboard Dataset feeds are code-authored, not SQL-authored.
- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — saved dashboard widget tiles stored in `tb_dashboard_bu_widget` (BU-scoped) + `tb_dashboard_personal_widget` (per-user); each tile row references a `dataset_id` from this catalog. (A prior version cited `tb_widget_dashboard`/`tb_widget_dashboard_item` and a separate `tb_widget_workspace` saved-queries table — none of these models exist in any Prisma schema; see [reporting-audit/widget](/en/inventory/reporting-audit/widget), flagged for correction in its own iteration.)
- [access-control/application-role](/en/inventory/access-control/application-role) — navigation and route access to `/system-admin/dashboard-dataset`.

## 8. References

- **micro-data service (Go):** `../micro-data/` — dashboard datasets + widget CRUD. Handlers: `controller/dashboard_controller.go`; logic: `service/dashboard/`, `service/widget_service.go`; models: `model/dashboard.go`; routes: `routes/routes.go`; overview: `README.md`.
- **Gateway proxy:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-datasets/dashboard-datasets.service.ts` — HTTP proxy to micro-data (sends `x-internal-token`, `c94a625ed`); controller `dashboard-datasets.controller.ts` exposes `GET /api/:bu_code/datasets` and `GET /api/:bu_code/datasets/:dataset_id`.
- **Nav / permission:** `../carmen-inventory-frontend-react/constant/module-list.ts:736-742` — `PERMISSIONS.dashboard.dataset.view`, `licenseFeature: "dashboard.dataset"`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1112-dashboard-dataset.md` — catalog only.
- **Swagger response DTOs:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-datasets/swagger/response.ts` — `DatasetMetaDto`, `DatasetListResponseDto`, `DatasetResponseDto`.
- **Platform enum:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `enum_dataset_shape` (line ~815).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/dashboard-dataset/dashboard-dataset.route.tsx` + `dashboard-dataset-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-dashboard-dataset.ts` — `useDashboardDatasets()`, `useDashboardDatasetDetail(id)`.
- **Frontend type:** `../carmen-inventory-frontend-react/types/dashboard-dataset.ts` — `DashboardDataset`, `DashboardDatasetShape`, `DashboardDatasetCategory`.
