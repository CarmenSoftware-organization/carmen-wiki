---
title: Widget Workspace Dashboard
description: The live /dashboard — a personalised drag-and-drop 12-column workspace where each user pins dataset-backed widgets (KPI, gauge, pie, bar, line, area, table) and status-pipeline cards from the micro-data catalog.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: dashboard, widget-workspace, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget Workspace Dashboard

> **At a Glance**
> **Route:** `/dashboard` &nbsp;·&nbsp; **For:** All operator roles post-login &nbsp;·&nbsp; **Status:** **Live** — backed by real API endpoints; dataset content depends on the micro-data dataset registry &nbsp;·&nbsp; **Scope:** Personal — each user's own saved widget layout, per business unit &nbsp;·&nbsp; **License feature:** `dashboard.widget` (`constant/module-list.ts`; license catalog `app:dashboard-widgets`)

## Implementation status (re-verified 2026-09-22)

Re-verified against `carmen-inventory-frontend-react`, `carmen-turborepo-backend-v2` and `micro-data` at HEAD. Since the 2026-07 pass the page grew four features, all live: **(1)** per-widget render switching (`widget_type` on `PATCH`, validated by micro-data against the dataset's shape, 2026-09-07 `74e3c795`), **(2)** a gauge card plus a **12-column grid with a per-widget size** stored in a new `display` JSONB column (2026-09-07 `493c78f0`; tenant migration `20260907143700_add_dashboard_widget_display`, micro-data migration `130_dash_widget_display`), **(3)** per-widget lazy loading — each card fetches its own value only when scrolled into view (`db046517`), and **(4)** a widget **parameter/display dialog** plus full-width **status-group cards** (`f72f951c`). One correction to the previous version of this page: the backend that serves this page is **micro-data (Go, HTTP)**, not `micro-cluster` over TCP — see §5.

## 1. What & Who

The Widget Workspace is the **only page on the `/dashboard` route** — there is no separate set of named domain sub-pages behind it. (A prior version of this wiki claimed it "replaces" six mock pages at `/dashboard/pr`, `/dashboard/po`, etc.; those never existed as routes — see the sibling [dashboard/main](/en/inventory/dashboard/main), [pr](/en/inventory/dashboard/pr), etc. pages, each flagged as historical-only.) The page renders a personalised, drag-and-drop grid of widgets, each bound to a dataset from the micro-data catalog.

> **Naming note (corrected 2026-07-16, backend attribution corrected 2026-09-22):** The real backend tables are `tb_dashboard_personal_widget` (this page's data — tenant schema, `packages/prisma-shared-schema-tenant/prisma/schema.prisma` `model tb_dashboard_personal_widget`: `dataset_id`, `widget_type`, `title`, `order_index`, `params`, `display`, scoped by `user_id`) and its sibling `tb_dashboard_bu_widget` (BU-scoped; CRUD exists in the backend but **no frontend caller** exists — see [reporting-audit/widget](/en/inventory/reporting-audit/widget)). Both are read and written by the **micro-data** Go service (`micro-data/controller/dashboard_controller.go`, `/api/dashboard/personal-widgets*`); the NestJS gateway's `DashboardPersonalWidgetsService` is a thin HTTP proxy that now must attach the shared `x-internal-token` (`INTERNAL_RPC_SECRET`) on every call — micro-data guards every route except `/health`, `/` and Swagger with `GinInternalAuth` (`micro-data/routes/routes.go`; gateway fix `c94a625ed`, 2026-09-21 — without the header the whole dashboard answers 401). A prior version of this note cited four other tables as real — **all four are gone or never existed**: `tb_widget_dashboard`, `tb_widget_dashboard_item`, and `tb_widget_default_layout` never appear in any Prisma schema or in micro-data/micro-report; `tb_widget_workspace` briefly existed (migration `20260512180928_widget_system_replace_dashboard`) and was dropped by `20260521040013_remove_widget_system`.

**Layout (`routes/dashboard/dashboard-component.tsx`, `sortable-widget-item.tsx`):**
- Greeting header (time-of-day + user full name) rendered from user profile.
- "Saved Widgets" section with a live count of renderable cards and the "+ Add widget" picker (`LookupDataset`).
- **Status-group cards** (if any) render first, full-width, outside the drag grid — see §1.2.
- The widget grid is a CSS grid of **12 columns on `lg`, 6 on `md`, 1 on mobile**, with fixed **4 rem rows** (`auto-rows-[4rem]`). Each card spans `display.width` columns × `display.height` rows (`components/dashboard-widget/widget-display.ts` `gridClasses()`); on `md` the width is halved. Cards are sorted by `order_index`.
- Each card is draggable via `@dnd-kit/core` (6 px activation distance). Collision detection is `pointerWithin` with a `closestCorners` fallback (`bc38a34c`) so unequal-size cards land where the pointer is; dropping reorders the list and PATCH-updates `order_index` optimistically (`(index + 1) * 10`).
- Each card's data is fetched **only when the card scrolls into view** (`useInViewport` → `onVisible`), one query per widget (`useQueries`).
- Hover controls per card: drag handle · **chart-type dropdown** (only when more than one render is available) · **gear** (opens the param/display dialog; shown whenever the dataset is still in the catalog) · delete.
- Empty state: decorative placeholder with chip hints (KPI / Pie / Bar).

### 1.1 Widget shapes and render types

The dataset is the owner of its **shape** (data kind); the **render** (`widget_type`) is a widget-level, user-changeable choice. micro-data advertises the compatible set per dataset as `supported_renders` (`micro-data/service/dashboard/dashboard.go` `SupportedRenders()`), and the frontend intersects it with the cards it can actually draw (`components/dashboard-widget/render-support.ts` `RENDERERS`):

| Shape (dataset) | Backend `supported_renders` | Frontend cards | Default on add |
|---|---|---|---|
| `scalar`, `scalar_delta` | `kpi`, `gauge` | `kpi`, `gauge` | `kpi` |
| `time_series` | `line`, `area`, `bar`, `sparkline` | `line`, `area`, `bar` | `line` |
| `categorical` | `bar`, `pie`, `table` | `pie`, `bar`, `table` | `pie` |
| `ranked` | `bar`, `table` | `pie`, `bar`, `table` | `bar` |
| `table` | `table` | `table` | `table` |
| `matrix` | `heatmap`, `table` | — (no converter yet) | not pickable |

The picker (`SUPPORTED_SHAPES` in `routes/dashboard/widget-shape.ts`) offers all six non-matrix shapes. `enum_dashboard_widget_type` still has 9 values (`kpi`/`line`/`area`/`bar`/`pie`/`heatmap`/`gauge`/`table`/`sparkline`); `sparkline` and `heatmap` have no card in the frontend. Switching the render is optimistic in the cache and `PATCH`es `{ widget_type }`; micro-data answers **400** when the shape cannot be drawn that way (`micro-data/service/widget_service.go` `validateRender()` — e.g. a pie of a scalar).

### 1.2 Status-group cards

A status-group card is a **frontend-only encoding** stored as an ordinary personal-widget row (`routes/dashboard/status-group.ts`): `dataset_id = "group@document.{pr|po|sr}-count"`, `params.statuses` (comma list), `params.time_range` (`@today` / `@3days` / `@7days` / `@1month`) and `params.owner_visibility` (`@everyone` / `@current_user`). The picker lists them as six extra entries ("PR/PO/SR summary (status pipeline)" × everyone/mine). micro-data never executes the `group@` id — the card itself calls `POST /api/{bu}/dashboard-lab/datasets/document.{doc}-by-status` with those params and lays the counts out as a pipeline of status tiles (read-only — the tiles carry no navigation handler at HEAD). Default status sets: PR `draft, in_progress, approved, completed`; PO `draft, in_progress, approved, sent_or_print, completed` (PO enum change 2026-09-14); SR `draft, in_progress, completed`. Group cards are not part of the drag grid.

### 1.3 Parameters and display settings

Datasets that declare `params[]` (only the `dashboard-lab` catalog endpoint returns descriptors: `name`, `label`, `type` `text|int`, `required`, `default`, `options`) open `WidgetConfigDialog` before the widget is created; parameterised datasets may be pinned more than once (e.g. a 30-day and a 365-day trend). The same dialog edits **display** settings for every widget: size (`width × height` from a per-type list — `widget-display.ts` `SIZE_OPTIONS`), `decimals` (0–4), and for gauges `min`, `max` and one `thresholds[0] {value, color}`. Defaults when unset: `kpi` 3×2, `gauge` 3×3, `pie`/`bar`/`line`/`area` 6×3, `table` 12×4; a size below the type's minimum is clamped on render (relevant after a render switch). `display` is stored opaquely — micro-data checks only that it is a JSON object ≤ 8 KB (`maxDisplayBytes`), so the frontend can add keys without a backend release. (The gateway swagger text still describes an older `width: 1|2|4, height: "sm"|"md"|"lg"` shape — the frontend's `types/dashboard-widget.ts` `WidgetDisplay` is the authority.)

**Audience**

- **Any logged-in user** — every operator builds their own workspace per business unit. There is no predefined layout; the workspace starts empty and grows as the user pins widgets.
- **Developers** — the compositing layer is `dashboard-component.tsx`; card rendering is `SortableWidgetItem` → `WidgetRouter` (`components/dashboard-widget/dashboard-widget-grid.tsx`).

## 2. Tiles & Drill-downs

The Widget Workspace has no fixed tile set — the grid is fully dynamic and personal to each user:

| Widget Card | Data source | Add via |
|---|---|---|
| Any pinned dataset (6 shapes) | `GET /api/{bu}/dashboard-lab/widgets/{widget_id}/data?scope=personal` — micro-data loads the widget's stored `dataset_id` + `params` and returns `{ meta, data }` | "+ Add widget" picker (+ param dialog when the dataset has params) |
| Status-group card | `POST /api/{bu}/dashboard-lab/datasets/document.{doc}-by-status` with `{ params: { time_range, owner_visibility } }` | "+ Add widget" picker → "PR/PO/SR summary (status pipeline)" |
| `table`-shaped datasets (e.g. `document.pr-table`) | Rows carry a hidden `id` column (`TableColumn.type = "id"`, micro-data `dbfde10`) so a row click opens the document (`3bd0b68f`) | picker |

Tile colours follow the dataset id prefix (`inventory.*` → Inventory Management, otherwise Procurement) via `inferModuleName` / `inferSubTile` in `widget-shape.ts`.

## 3. Common Questions

| Question | Answer |
|---|---|
| Why does the page show a greeting rather than tiles? | The workspace loads the user's saved widget list — if empty, it shows the empty-state prompt. Add at least one widget via the "+ Add widget" picker. |
| Where do the available datasets come from? | `LookupDataset` queries `GET /api/{bu}/dashboard-lab/datasets` (`hooks/use-dashboard-dataset.ts`, `CACHE_STATIC`) — the code-registered registry in `micro-data/service/dashboard/registry.go`; see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset). |
| Why can I add the same dataset twice? | Only datasets **with** parameters can be pinned more than once; parameter-less datasets already pinned are excluded from the picker (`excludeIds`). |
| Why is the chart-type button missing on a card? | Only one render is available for that shape after intersecting `supported_renders` with the frontend cards (e.g. `table`). |
| Why did switching to gauge/pie fail? | micro-data rejected the render for that dataset's shape (400, `validateRender`); the list is re-fetched and the card reverts. |
| Can I reset my layout to the default? | Not exposed in UI. No default-layout table exists (`tb_dashboard_personal_widget` has no seed concept — each user's grid starts empty). |
| Why does drag-and-drop sometimes revert? | Reordering is optimistic — the TanStack Query cache is updated immediately, then one PATCH per moved widget fires. If a PATCH fails a toast error appears; the cache is not automatically reverted for reorders (type switches and group time-range changes do invalidate on error). |
| Why is a widget I pinned in another BU missing here? | Widgets are stored in the BU's tenant schema and datasets resolve per BU; a widget whose dataset 404s in the current BU is silently dropped from the grid (`renderable` filter). |
| Where is `order_index` stored? | On the `tb_dashboard_personal_widget` row, incremented by 10 per slot. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Whole page shows a load error / every dashboard 401s | Gateway → micro-data call missing `x-internal-token` (`INTERNAL_RPC_SECRET` mismatch between services) | Ops: align `INTERNAL_RPC_SECRET` across backend-gateway and micro-data (`c94a625ed`) |
| `GET /api/me/dashboard-widgets?bu_code=` returns 500 | Backend-side (see `routes/dashboard/CLAUDE.md` in the frontend repo — reproduced direct and via proxy) | Report to the backend team; the page degrades to the error banner |
| Workspace loads but shows no widgets | User has no saved widgets yet | Click "+ Add widget" to pin at least one dataset |
| "+ Add widget" picker shows an empty list | Catalog fetch failed, or all parameter-less supported datasets are already pinned | Check `GET /api/{bu}/dashboard-lab/datasets`; parameterised datasets can still be added |
| Card stays a skeleton | The card has not entered the viewport yet (lazy load), or its data query is pending | Scroll to it; check the per-widget `dashboard-lab/widgets/{id}/data` call |
| Gauge shows an odd scale | `display.max` not set — the frontend estimates a rounded max above the current value (`gaugeRange()`, `isEstimated`) | Set `max` (and `min`) in the gear dialog |
| Save in the gear dialog fails with 400 | `display` over 8 KB, or `params` failed the dataset's param validation | Reduce the display object; check `params` against the dataset descriptors |
| Drag-and-drop does not activate | Pointer moved less than 6 px before release (activation constraint) | Press and drag at least 6 px before releasing |
| Order reverts after refresh | PATCH request failed | Check the browser console for the toast error; backend validation on `order_index` (must be ≥ 0) |

---

## 5. Data Sources (Dev)

All personal-widget calls carry `?bu_code=` because the rows live in the selected BU's tenant schema (`routes/dashboard/use-my-dashboard-widgets.ts`).

- **Saved widget list** — `GET /api/me/dashboard-widgets?bu_code=` → `{ items: WidgetConfig[], count }`. Hook: `useMyDashboardWidgets` (`CACHE_DYNAMIC`).
- **Widget value** — `GET /api/{bu}/dashboard-lab/widgets/{widget_id}/data?scope=personal` → `{ meta, data }` (gateway `dashboard-lab.controller.ts` `widgetData`, micro-data `/api/dashboard-lab/widgets/{id}/data`; `scope` defaults to `bu`). Query options: `myDashboardWidgetDataQueryOptions(buCode, widgetId, enabled)` — `enabled` flips when the card is in view. Bruno: `_uncategorized/dashboard-lab/GET-widget-data-dashboard-lab.bru`.
- **Dataset catalog** — `GET /api/{bu}/dashboard-lab/datasets` → `{ items: DashboardDataset[], count }` with `params[]` descriptors and `supported_renders[]` per dataset (`6dfe58992`). Hook: `useDashboardDatasets` (`CACHE_STATIC`). Bruno: `GET-list-dashboard-lab.bru`.
- **Preview / group tiles** — `POST /api/{bu}/dashboard-lab/datasets/{dataset_id}` with `{ params }` → `{ meta, data }`. Hook: `useDashboardDatasetPreview`. Bruno: `POST-preview-dashboard-lab.bru`.
- **Create widget** — `POST /api/me/dashboard-widgets?bu_code=` with `{ dataset_id, widget_type, title?, order_index?, params?, display? }` → `{ id }` (201). Hook: `useCreateMyDashboardWidget`.
- **Update widget** — `PATCH /api/me/dashboard-widgets/{id}?bu_code=` with any of `{ title, order_index, params, widget_type, display }` — `params` and `display` **replace** the whole object (not merge); `widget_type` is validated against the dataset shape (400). Hook: `useUpdateMyDashboardWidget`. Bruno: `_uncategorized/dashboard-widgets/PATCH-update-dashboard-widgets-dashboard-widgets.bru`.
- **Bulk reorder** — `PATCH /api/me/dashboard-widgets/reorder?bu_code=` with `{ items: [{ id, order_index }] }` (atomic, micro-data `PersonalReorder` in one transaction) — exists on the gateway and in Bruno (`PATCH-reorder-dashboard-widgets.bru`) but the page currently issues one `PATCH /{id}` per moved widget instead.
- **Delete widget** — `DELETE /api/me/dashboard-widgets/{id}?bu_code=` (soft delete). Hook: `useDeleteMyDashboardWidget`.
- **Bundled alternative (unused by this page)** — `GET /api/{bu}/dashboard-widgets/me` returns the same personal list with `{ meta, data }` attached per item in one round-trip (`system-widgets.controller.ts` `@Get('me')`); no frontend caller.
- **Backend table:** `tb_dashboard_personal_widget` (tenant schema) — `id`, `user_id`, `dataset_id` (VarChar 100), `widget_type` (`enum_dashboard_widget_type`), `title`, `order_index` (default 0), `params` (JSONB), `display` (JSONB, added by `20260907143700_add_dashboard_widget_display` / micro-data `130_dash_widget_display.up.sql`, `IF NOT EXISTS` on both sides so either migration path may run first), `doc_version`, standard audit columns; index `[user_id, deleted_at]`. Served by **micro-data** (`controller/dashboard_controller.go` → `service/widget_service.go` → `db/widget_repo.go`), fronted by `backend-gateway`'s `DashboardPersonalWidgetsController` (`api/me/dashboard-widgets`, `KeycloakGuard` + `x-app-id`) whose service `fetch`es `http://DATASET_SERVICE_HOST:DATASET_SERVICE_HTTP_PORT/api/dashboard/personal-widgets…` with the `x-internal-token` header. No default/seed layout exists.

## 6. Refresh Cadence

- **Widget list** — `CACHE_DYNAMIC` (TanStack Query, staleTime 1 min). Refetched on focus; no polling.
- **Widget data** — one query per widget, `CACHE_DYNAMIC`, started when the card first enters the viewport; a param/display save invalidates only that widget's data query.
- **Catalog** — `CACHE_STATIC` (the registry is code, changes only on deploy).
- **Reorder / render switch / group time-range** — optimistic cache update, then PATCH; the list is invalidated on error for render switch and time-range, not for reorder.

## 7. Related Modules

- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — data-model reference for the widget tables (BU + personal), micro-data endpoints, validation rules
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — the code-registered dataset catalog that populates the picker
- [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) — the real, live approval inbox (`/procurement/approval`); the status-group "mine" preset is the closest dashboard equivalent
- [dashboard/my-pending](/en/inventory/dashboard/my-pending), [dashboard/my-approval](/en/inventory/dashboard/my-approval), [dashboard/pr](/en/inventory/dashboard/pr), [dashboard/main](/en/inventory/dashboard/main) — **historical only**; demo files deleted 2026-06-27, never routed

## 8. Reference Sources

- **Route:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard.route.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx` (grid, dnd, lazy visibility set, add/config/type-switch handlers)
- **Cards & helpers:** `routes/dashboard/sortable-widget-item.tsx` (drag handle, render dropdown, gear, delete), `status-group.ts` + `status-group-card.tsx`, `widget-config-dialog.tsx` + `widget-param-fields.tsx` + `widget-display-fields.tsx`, `widget-shape.ts`; `components/dashboard-widget/widget-display.ts` (grid sizes, gauge range, thresholds), `render-support.ts` (shape ↔ render), `dashboard-widget-grid.tsx` (`WidgetRouter`, cards, `LazyWidget`)
- **Hooks:** `routes/dashboard/use-my-dashboard-widgets.ts` (moved out of `hooks/` on 2026-08-28, `0d9757f3`), `hooks/use-dashboard-dataset.ts`
- **Types:** `types/dashboard-widget.ts` (`WidgetConfig`, `WidgetDisplay`, `DatasetParam`, `TableColumn`, shape guards), `types/dashboard-dataset.ts` (`supported_renders`)
- **API constants:** `constant/api-endpoints.ts` → `MY_DASHBOARD_WIDGETS`, `MY_DASHBOARD_WIDGET_BY_ID`, `DASHBOARD_LAB_DATASETS`, `DASHBOARD_LAB_DATASET_EXEC`, `DASHBOARD_LAB_WIDGET_DATA`
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-personal-widgets.controller.ts` + `.service.ts` (HTTP proxy, `x-internal-token`), `swagger/response.ts` (`WidgetUpdateRequestDto.widget_type`/`display`), `dashboard-lab/dashboard-lab.controller.ts` (`GET widgets/:widget_id/data`)
- **micro-data:** `../micro-data/controller/dashboard_controller.go`, `service/widget_service.go` (`validateRender`, `validateDisplay`, 8 KB cap), `service/dashboard/dashboard.go` (`SupportedRenders`), `service/dashboard/lab.go` (catalog with `params`/`supported_renders`), `service/dashboard/document.go` (`document.*` datasets, table rows with `id`), `model/dashboard.go`, `migrations/tenant/130_dash_widget_display.up.sql`
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dashboard_personal_widget`, `tb_dashboard_bu_widget`, `enum_dashboard_widget_type`; migration `20260907143700_add_dashboard_widget_display`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/dashboard-lab/*`, `_uncategorized/dashboard-widgets/*` (`GET-me`, `PATCH-reorder`, `PATCH-update`, `POST-create`, `GET-module-config`)
- **Backend design (historical):** `../carmen-turborepo-backend-v2/docs/superpowers/archive/widget/2026-05-12-widget-backend-design.md`
