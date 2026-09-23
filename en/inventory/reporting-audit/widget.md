---
title: Widget
description: Dashboard widget entity — per-user (and BU-scoped, backend-only) tiles bound to a code-registered dataset catalog, served by micro-data over HTTP behind the gateway; 2026-09 display column, render switching, config-only module route.
published: true
date: 2026-09-23T10:06:26.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

> **At a Glance**
> **Owner:** End users (personal widgets) &nbsp;·&nbsp; **Tables:** `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` (tenant schema) &nbsp;·&nbsp; **Used by:** the [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) `/dashboard` screen (personal). The BU table has full CRUD in micro-data + gateway but **no frontend caller**; the per-module landing dashboards use hardcoded **system widgets**, not BU rows &nbsp;·&nbsp; **Served by:** micro-data (Go, HTTP + `x-internal-token`)

![Widget screen](/screenshots/reporting-audit/widget.png)

## Implementation status (re-verified 2026-09-22)

Corrections and additions since the 2026-07-22 version:

1. **BU widgets do not power the module dashboards.** `useProcurementWidgets` / `useInventoryWidgets` / `useOperationPlanWidgets` … call `GET /api/{bu}/dashboard-widgets/{module}/config` (new on 2026-09-07, `374aad8e5` — returns the hardcoded `system-widgets.config.ts` entries without executing any dataset; 404 falls back to the older bundled `GET .../dashboard-widgets/{module}`), and each tile then lazy-loads `GET /api/{bu}/datasets/{dataset_id}` when scrolled into view. `GET /api/{bu}/dashboard-widgets/bu` and `DASHBOARD_BU_WIDGET*` have **zero references** in `carmen-inventory-frontend-react`. The `procurement-dashboard.tsx → …/dashboard-widgets/bu` example on the previous page was wrong (already flagged by [recipe/operation-dashboard](/en/inventory/recipe/operation-dashboard) §6).
2. **New `display` JSONB column on both tables** (tenant migration `20260907143700_add_dashboard_widget_display`; micro-data `130_dash_widget_display`) — per-widget presentation (grid `width`/`height`, `decimals`, gauge `min`/`max`/`thresholds`). micro-data stores it opaquely, checking only that it is a JSON object ≤ 8 KB (`service/widget_service.go` `maxDisplayBytes`).
3. **`widget_type` is now editable on `PATCH`** and validated against the dataset's shape (`validateRender()` → 400 with the allowed list); the catalog advertises the compatible set as `supported_renders` per dataset (`SupportedRenders()` in `service/dashboard/dashboard.go`).
4. **Every gateway → micro-data call must carry `x-internal-token`** (`INTERNAL_RPC_SECRET`); micro-data guards all routes except `/health`, `/`, `/swagger` (`6d86790`, gateway fix `c94a625ed` 2026-09-21).
5. The `/dashboard` picker now offers six shapes (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `table`) — not three — and creates the first render allowed by `supported_renders` ∩ frontend cards.

## 1. What & Who

The widget entity is the **dashboard tile layer** — a placement of a code-registered [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) feed (`dataset_id`), rendered as a chart (`widget_type`), with dataset parameters (`params`) and presentation settings (`display`), on either a business unit's shared dashboard or a single user's personal dashboard. There are exactly two tables, both **tenant-scoped** (the tenant schema *is* the BU, so neither carries a `business_unit_id`):

- `tb_dashboard_bu_widget` — a widget on a business unit's shared dashboard. Backend complete; **no screen uses it today** (see status note).
- `tb_dashboard_personal_widget` — a widget on one user's personal dashboard, scoped by `user_id`. Powers the `/dashboard` route — see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) for the full UI walkthrough (add with params, render switch, size/gauge settings, drag-and-drop, status-group cards, lazy loading).

There is no default-layout table and no seeding mechanism — a new user's personal dashboard starts empty. There is no saved-query / data-explorer feature — `dataset_id` always references a fixed entry in the micro-data registry (`service/dashboard/registry.go`), never a user-authored query. The frontend additionally encodes **status-group cards** as personal rows with `dataset_id = "group@document.{pr|po|sr}-count"`; micro-data never executes those ids.

**Maintained by** end users (their own personal widgets). BU widget endpoints carry no role check beyond `KeycloakGuard` + `x-app-id`. **Read by** [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) (personal).

### 1.1 Where widget CRUD runs (micro-data)

Widget create/read/update/delete is hosted by the **micro-data** service (Go), not micro-cluster. `micro-data/controller/dashboard_controller.go` registers the routes below; the backend-gateway's `DashboardBuWidgetsService` / `DashboardPersonalWidgetsService` are thin HTTP proxies (`fetch` to `DATASET_SERVICE_HOST:DATASET_SERVICE_HTTP_PORT`, `x-internal-token` header) with no business logic and no DB connection of their own.

| Scope | micro-data endpoints (proxied by backend-gateway) |
|---|---|
| **BU widgets** | `GET/POST /api/dashboard/bu-widgets?bu_code=` · `GET/PATCH/DELETE /api/dashboard/bu-widgets/:id?bu_code=` |
| **Personal widgets** | `GET/POST /api/dashboard/personal-widgets?user_id=&bu_code=` · `GET/PATCH/DELETE /api/dashboard/personal-widgets/:id?user_id=&bu_code=` · `POST /api/dashboard/personal-widgets/reorder?user_id=&bu_code=` (atomic bulk `order_index`) |
| **Widget value** | `GET /api/dashboard-lab/widgets/:id/data?scope=bu|personal` — executes the stored `dataset_id` + `params` |
| **Catalog / preview** | `GET /api/dashboard-lab/datasets` (with `params[]`, `supported_renders[]`), `POST /api/dashboard-lab/datasets/:id` (`{ params }`), `GET /api/dashboard/datasets[/:id]` (parameter-less) |

Gateway-facing routes the frontend calls: `api/me/dashboard-widgets[...]` (personal, `user_id` from the auth header, `?bu_code=`), `api/:bu_code/dashboard-lab/*`, `api/:bu_code/datasets/*`, `api/:bu_code/dashboard-widgets/{module}/config` (system widgets). `api/:bu_code/dashboard-widgets/bu[...]` (BU CRUD), `api/:bu_code/dashboard-widgets/me` and `.../all` (bundled values) exist but have no frontend caller.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a personal widget | `/dashboard` → **+ Add widget** | Picker lists six shapes; datasets with `params[]` open a config dialog first and may be pinned more than once |
| Change how a widget draws | `/dashboard` → card → chart-type dropdown | `PATCH { widget_type }`; 400 when the shape cannot be drawn that way |
| Resize / set decimals / gauge range | `/dashboard` → card → gear | `PATCH { params, display }` — both objects are **replaced**, not merged |
| Reorder personal widgets | `/dashboard` → drag a widget card | Optimistic `order_index` update, then one `PATCH` per moved widget (the atomic `reorder` route exists but is unused by the page) |
| Delete a personal widget | `/dashboard` → card → trash | `DELETE .../personal-widgets/:id` — soft delete (`deleted_at`) |
| Add/edit a BU widget | **No UI** | Backend-only today (Bruno `_uncategorized/dashboard-widgets/*-bu.bru`) |
| Add a tile to a module landing dashboard | Code change in `system-widgets.config.ts` | Not a DB row — see [recipe/operation-dashboard](/en/inventory/recipe/operation-dashboard) |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Every dashboard call returns 401 | Gateway did not send `x-internal-token`, or `INTERNAL_RPC_SECRET` differs between services | Ops: align the secret |
| Personal widget not visible to a teammate | Expected — personal widgets are `user_id`-scoped, never shared | No BU-widget UI exists yet |
| `PATCH` returns 400 "cannot render a … dataset (allowed: …)" | `widget_type` not in `SupportedRenders(shape)` | Pick a render from the dataset's `supported_renders` |
| `PATCH`/`POST` returns 400 on `display` | Object over 8 KB (`maxDisplayBytes`), or not a JSON object | Trim the display object |
| `PATCH` returns 400 with an empty body | `validateUpdate` requires at least one of `title`, `order_index`, `params`, `widget_type`, `display`; `order_index` must be ≥ 0 | Send a field |
| Widget card shows an error / disappears | `dataset_id` no longer resolves in this BU (retired id or dataset not in this schema) — 404 on `widgets/:id/data` | Remove and re-add; the render check lets unknown datasets through so old rows stay editable |
| 404 on widget update/delete | `PersonalFindOne`/`BuFindByID` filter `deleted_at IS NULL` — id already soft-deleted or never existed | Re-fetch the widget list |
| Reorder appears to fail silently | `PersonalReorder` updates rows in one DB transaction — a mid-batch failure rolls back the whole reorder | Retry; check the response for the failing id |

## 4. Edge Cases

- **No default/seed layout.** Every new user's and every new BU's widget grid starts empty.
- **No workspace/saved-query concept.** `dataset_id` only ever references a fixed registry entry.
- **No BU-widget authorization gate.** The BU endpoints require `bu_code` but no additional role check — moot while no UI calls them.
- **`params` are dataset-scoped config, `display` is presentation.** `params` (JSONB) holds the dataset's own parameters (e.g. `time_range`, `status`, `owner_visibility`) fixed at save time — never `user_id`/`bu_code`, which the caller supplies at execution. `display` is owned by the frontend (`types/dashboard-widget.ts` `WidgetDisplay`); the gateway swagger still describes an older `width: 1|2|4, height: "sm"|"md"|"lg"` shape.
- **Group cards live only in the personal table.** `group@…` rows are rendered entirely by the frontend, which calls the underlying `document.{doc}-by-status` dataset per card.
- **Both migration paths add `display` with `IF NOT EXISTS`**, so a tenant that ran micro-data migration 130 before the Prisma migration (or vice versa) is fine.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_dashboard_bu_widget`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `dataset_id` | `String @db.VarChar(100)` | No | References a [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) registry entry (no FK — code registry, not a table). |
| `widget_type` | `enum_dashboard_widget_type` | No | `kpi` / `line` / `area` / `bar` / `pie` / `heatmap` / `gauge` / `table` / `sparkline`. |
| `title` | `String? @db.VarChar(255)` | Yes | Optional override; falls back to the dataset's own display name. |
| `order_index` | `Int` | No | Default `0`. Grid position. |
| `params` | `Json? @db.JsonB` | Yes | Dataset parameters (replace-not-merge on `PATCH`). |
| `display` | `Json? @db.JsonB` | Yes | Presentation settings, opaque to the backend (≤ 8 KB). Added 2026-09-07. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Optimistic-concurrency counter. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `[deleted_at]` (`tenant_dashboard_bu_widget_deleted_idx`). No `business_unit_id` column — the tenant schema itself is the BU boundary.

### 5.2 `tb_dashboard_personal_widget`

Identical shape to `tb_dashboard_bu_widget` plus a `user_id String @db.Uuid` scoping column. **Indexes:** `[user_id, deleted_at]` (`tenant_dashboard_personal_widget_user_deleted_idx`).

### 5.3 `enum_dashboard_widget_type` and shape compatibility

`kpi`, `line`, `area`, `bar`, `pie`, `heatmap`, `gauge`, `table`, `sparkline` — 9 values (`model.WidgetTypes` in micro-data is the same set). The registry carries 7 shapes; the compatible renders per shape (`SupportedRenders`) are:

| Shape | Renders accepted by micro-data | Drawn by the frontend |
|---|---|---|
| `scalar`, `scalar_delta` | `kpi`, `gauge` | both |
| `time_series` | `line`, `area`, `bar`, `sparkline` | `line`, `area`, `bar` |
| `categorical` | `bar`, `pie`, `table` | all |
| `ranked` | `bar`, `table` | `bar`, `table` (+ `pie`) |
| `matrix` | `heatmap`, `table` | none |
| `table` | `table` | `table` |

A render outside the dataset's set is rejected on create and on `PATCH`; a dataset the registry no longer knows passes the canonical check only, so an unrelated edit to an old widget is not blocked.

### 5.4 Write payloads (micro-data `model/dashboard.go`)

```
WidgetCreateInput { dataset_id, widget_type, title?, order_index?, params?, display? }
WidgetUpdateInput { title?, order_index?, params?, widget_type?, display? }   -- at least one
WidgetReorderItem { id, order_index }                                         -- POST .../reorder { items: [...] }
```

## 6. Business Rules

- **Tenant-scoped, no BU FK.** Both tables live in each tenant's own schema; `bu_code` resolution happens at the connection layer.
- **Personal widgets are strictly per-user.** `PersonalFindOne`/`PersonalFindByID` always filter by `user_id`.
- **Render must fit the shape.** `validateRender()` on create and update; `supported_renders` is the single source of truth, advertised on the catalog.
- **`params` and `display` replace wholesale.** Send the full object on `PATCH`.
- **`display` is bounded, not interpreted.** 8 KB cap; the client owns the schema so a new option needs no backend release.
- **Soft delete only.** Both tables use `deleted_at`; no hard delete found.
- **Reorder is transactional.** `PersonalReorder` wraps the batch `order_index` update in one DB transaction (`db/widget_repo.go`).
- **No default/seed layout.** New personal and BU widget lists start empty.

## 7. Cross-References

- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the live `/dashboard` screen this page's `tb_dashboard_personal_widget` data backs; full UI walkthrough, hooks, and gateway controllers.
- [recipe/operation-dashboard](/en/inventory/recipe/operation-dashboard) — the hardcoded system-widget mechanism behind the module landing dashboards (config route + lazy per-tile datasets).
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — the code-registered catalog every `dataset_id` references.
- [access-control/user](/en/inventory/access-control/user) — owner of personal widgets (`user_id`).
- [master-data/business-unit](/en/inventory/master-data/business-unit) — bounds BU-widget visibility (tenant = BU).

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_dashboard_widget_type`, `tb_dashboard_bu_widget`, `tb_dashboard_personal_widget`; migrations `20260609190100_add_dashboard_widget_tables`, `20260907143700_add_dashboard_widget_display`; history `20260512180928_widget_system_replace_dashboard` / `20260521040013_remove_widget_system` (the dropped `tb_widget_*` family).
- **micro-data (Go):** `../micro-data/controller/dashboard_controller.go` (routes), `service/widget_service.go` (`validateCreate`/`validateUpdate`, `validateRender`, `validateDisplay`), `db/widget_repo.go` (`PersonalReorder`), `model/dashboard.go` (`WidgetTypes`, inputs), `service/dashboard/dashboard.go` (`SupportedRenders`), `service/dashboard/lab.go` (catalog), `routes/routes.go` + `middleware` (`GinInternalAuth`), `migrations/tenant/130_dash_widget_display.up.sql`, `api/openapi.yaml`.
- **Backend gateway (proxy layer):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-bu-widgets.controller.ts` + `.service.ts`, `dashboard-personal-widgets.controller.ts` + `.service.ts` (`x-internal-token`), `system-widgets.controller.ts` (`GET :module/config`, `GET me`, `GET all`), `system-widgets.config.ts`, `swagger/response.ts`; `dashboard-lab/`, `dashboard-datasets/`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx`, `sortable-widget-item.tsx`, `status-group.ts`, `use-my-dashboard-widgets.ts`; `hooks/use-dashboard-widgets.ts` (`useDashboardWidgetConfigs`), `hooks/use-dashboard-dataset.ts`; `components/dashboard-widget/render-support.ts`, `widget-display.ts`; `types/dashboard-widget.ts`, `types/dashboard-dataset.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/dashboard-widgets/*` (BU, personal, module, `GET-module-config`, `GET-me`, `GET-all`), `_uncategorized/dashboard-lab/*`, `_uncategorized/dashboard-datasets/*`.
