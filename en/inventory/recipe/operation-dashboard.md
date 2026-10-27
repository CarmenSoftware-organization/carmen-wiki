---
title: Operation Plan Dashboard
description: The /operation-plan landing screen — 10 system-template KPI/chart tiles (recipe + equipment) read from the backstage widget-template table via a gateway config route, plus a BU widget section; each tile lazily loading its dataset; not a user-configurable widget board.
published: true
date: 2026-10-27T00:00:00.000Z
tags: recipe, operation-plan, dashboard, widget, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:00:00.000Z
---

# Operation Plan Dashboard

> **At a Glance**
> **Route:** `/operation-plan` (index) &nbsp;·&nbsp; **Component:** `operation-dashboard.tsx` &nbsp;·&nbsp; **Data:** `GET /api/{bu_code}/dashboard-widgets/operation-plan/config` (config only, since 2026-09-07) + one lazy `GET /api/{bu_code}/datasets/{dataset_id}` per tile &nbsp;·&nbsp; **Tiles:** 10 system templates (5 KPI, 5 chart) covering recipe + equipment, read from the platform's dashboard-widget template table (module `operation-plan`) &nbsp;·&nbsp; **System tiles are not editable by the tenant**; a separate **BU widget section** is appended below them (since 2026-10).

> **Re-verified 2026-10-27 — source of the tiles changed.** The gateway file `system-widgets.config.ts` (`OPERATION_PLAN_WIDGETS`) is **gone** (commit `3ea25956f`). `DashboardSystemWidgetsController` now calls `SystemWidgetCache.forBu(bu_code, 'operation-plan')`, which reads active system templates through the `DashboardTemplates.findActiveSystem` RPC (backstage database, cached 60 s) and hides templates by BU `allow_business_unit` / `deny_business_unit` (deny wins; empty list = no restriction). The same ten rows are seeded by `packages/prisma-shared-schema-backstage/prisma/seed.dashboard-widget-template.data.ts` (`seed_key` `system.operation-plan.*`), so a default install still shows the §5 tiles, but an operator can now edit, reorder, retitle or restrict them per BU in the Backstage dashboard-template admin. Titles are bilingual: each row carries `title` plus `title_i18n` `{ en, th }`. The controller class is now guarded by `BuCodePathQueryMatchGuard` (a `bu_code` in the query must match the path). On the page, `operation-dashboard.tsx` renders `<BuWidgetSection module="operation-plan">` after the system tiles (BU-curated widgets from `tb_dashboard_bu_widget`, hidden when the backend has none and the user cannot add) — see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace). Where the older text below says the tiles are hardcoded in gateway source, read it as "seeded system templates".

> **Re-verified 2026-09-22.** Two changes since 2026-07-29: **(1)** the page no longer waits for one bundled response — `useOperationPlanWidgets()` → `useDashboardWidgetConfigs("operation-plan")` (`hooks/use-dashboard-widgets.ts`) calls the new `…/dashboard-widgets/operation-plan/config` route (`374aad8e5`; gateway returns the hardcoded config without touching the database, 404 falls back to the old bundled route) with `CACHE_STATIC`, and each tile is a `LazyWidget` that fetches `GET /api/{bu}/datasets/{dataset_id}` only when scrolled into view (`db046517`). A broken dataset therefore shows as an error on **that tile**, not a silent disappearance. **(2)** Tiles are laid out on the shared 12-column / 4 rem-row grid with `gridClasses(widget_type, display)`, and the four sections are keyed by render type (KPI + gauge · Trends = line/area · Comparison = bar · Distribution = pie), sorted by `order_index` within each.

![Operation Plan dashboard](/screenshots/operation-plan/index.png)

## 1. What & Who

The Operation Plan Dashboard is the landing screen shown at `/operation-plan` before the user picks a sub-module ([Recipe](/en/inventory/recipe), [Recipe Category](/en/inventory/recipe/category), [Cuisine](/en/inventory/recipe/cuisine), [Equipment](/en/inventory/recipe/equipment), [Equipment Category](/en/inventory/recipe/equipment-category)). It renders a fixed set of **10 dashboard tiles** — 5 KPI cards and 5 charts — built from `recipe.*` and `equipment.*` entries in the [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog. The UI translation key that names it is `operationPlan.dashboard` (`title: "Operations Overview"`, `description: "Recipe, cuisine, and equipment status across the operation plan"`).

**This is not the same mechanism as [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) or [reporting-audit/widget](/en/inventory/reporting-audit/widget).** Those pages document `tb_dashboard_bu_widget` (BU-curated, addable/removable) and `tb_dashboard_personal_widget` (per-user, addable/removable) — both real, editable widget tables served by the **micro-data** Go service. This screen's 10 tiles are a **third, separate mechanism**: *system* widget templates (rows in the backstage database, cached in the gateway) — not editable by the tenant, unlike the BU / personal widgets (as of 2026-10-27; before that they were a hardcoded TypeScript array). See §6 for the exact distinction and the one prior-page citation this corrects.

**Maintained by** Engineering (code change + deploy to add/remove/reorder a tile — there is no admin screen). **Read by** any authenticated user who can load `/operation-plan` — no permission check was found gating the data endpoint itself (see §4).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View operation-plan KPIs | Navigate to `/operation-plan` | Loads automatically; no filter/date-range controls exist |
| Drill into a metric | Click a tile (visual only) | Tiles are not links — `KpiCard`/`BarCard`/`PieCard` render read-only; to inspect the underlying data, navigate to the relevant sub-module screen manually |
| Add/remove/reorder a tile | **Not possible from the UI** | Requires a code change to `system-widgets.config.ts` (backend-gateway) — see §6 |
| Retry after a load error | Reload the page | The screen shows a single inline error banner (`dashboardWidget.loadError`) for the whole tile set; there is no per-tile retry |

## 3. Validation & Errors

| Symptom | Cause | Confirmed? |
|---|---|---|
| Whole dashboard shows a load-error banner | `GET .../dashboard-widgets/operation-plan` failed (network, auth, or a downstream micro-data error) | **Confirmed** — `operation-dashboard.tsx` renders one `role="alert"` banner keyed to `isError`, not per-tile |
| A single tile shows an error / skeleton | Its lazy `GET /api/{bu}/datasets/{dataset_id}` failed or has not fired yet (tile not in view) | **Confirmed (2026-09-22)** — per-tile query in `LazyWidget`; the rest of the grid is unaffected (replaces the pre-2026-09 "silent disappearance" behaviour) |
| Empty-state message ("No widget data") | The config route returned no entries (or all are in `HIDDEN_DATASETS`, currently empty) | **Confirmed** — `hasAny` gates the empty-state message on the config list, not on dataset results |
| Skeleton grid shows exactly 4 placeholder cards while loading | `Array.from({ length: 4 })` is hardcoded in the loading state | **Confirmed** — cosmetic only; the real resolved set is 10 tiles, not 4 |

## 4. Edge Cases

- **No per-key permission on the data endpoint.** `DashboardSystemWidgetsController` (`api/:bu_code/dashboard-widgets`) is guarded by `BuCodePathQueryMatchGuard` + `KeycloakGuard` (any authenticated user of the BU) — no `@RequirePermission`-style decorator was found on the `operation-plan` route handler, unlike the sidebar entries for `/operation-plan/*` sub-screens, which now gate on resource-level keys such as `operation_plan.recipe.view` (the old `operation_plan.view` placeholder is no longer used by any menu leaf — see [recipe](/en/inventory/recipe) §4). The dashboard landing route itself carries no permission.
- **Tiles are templates, not tenant rows.** Unlike `tb_dashboard_bu_widget`/`tb_dashboard_personal_widget`, tile selection, order and title live in the **backstage** template table (not the tenant database). By default every business unit sees the same 10 tiles in the same order; allow/deny BU lists on a template can change that per BU.
- **Layout is grouped by widget type, not by the config's own `order_index`.** The frontend groups widgets into 4 named sections (KPI incl. gauge, Trends = line/area, Comparison = bar, Distribution = pie) and sorts *within* each section by `order_index`, placing each on the shared 12-column grid via `gridClasses(widget_type, display)` — it does not render one flat grid the way the generic `DashboardWidgetGrid` component (used by [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard)) does. See §6.
- **`equipment.by-category` is the only pie-shaped tile in this set** (categorical shape) — everything else is `kpi` (scalar/scalar_delta) or `bar` (categorical/ranked rendered as bars). There is no line/area/time-series tile even though `recipe.added-daily` (a `time_series`-shaped dataset) exists in the catalog — it is not one of the 10 configured tiles for this dashboard.
- **Cache.** The config query uses `CACHE_STATIC` (`useOperationPlanWidgets` → `useDashboardWidgetConfigs("operation-plan")` — the gateway caches templates for 60 s, so the set rarely changes within a session); each tile's dataset query uses `CACHE_DYNAMIC` (1-min stale).

---

## 5. Tiles (Dev)

Source (2026-10-27): seed rows in `packages/prisma-shared-schema-backstage/prisma/seed.dashboard-widget-template.data.ts` (`module: 'operation-plan'`, `order_index` 0–9); earlier rounds read the same list from the now-deleted `system-widgets.config.ts`.

| # | `dataset_id` | Type | Title (Thai, as coded) | Section rendered in |
|---|---|---|---|---|
| 0 | `recipe.total-active` | kpi | Recipe active | Metrics |
| 1 | `recipe.added-7d` | kpi | Recipe เพิ่มใน 7 วัน | Metrics |
| 2 | `recipe.average-ingredients` | kpi | Avg ingredients / recipe | Metrics |
| 3 | `recipe.cuisines-total` | kpi | Cuisine types | Metrics |
| 4 | `equipment.total-active` | kpi | Equipment active | Metrics |
| 5 | `recipe.by-cuisine-top` | bar | Top 10 cuisine ตามจำนวน recipe | Comparison |
| 6 | `recipe.by-category-top` | bar | Top 10 recipe category | Comparison |
| 7 | `equipment.by-category` | pie | Equipment แยกตามประเภท | Distribution |
| 8 | `recipe.most-complex` | bar | Recipe ที่ใช้ ingredients มากสุด | Comparison |
| 9 | `recipe.added-daily` | line | Recipe สร้างต่อวัน (30d) | Trends |

Titles come from the template row (`title` plus `title_i18n` `{ en, th }`, e.g. "Active recipes" / "Recipe ที่ใช้งาน"); the table below shows the seed `title` column. They are **not** passed through `use-intl`; the frontend renders what the gateway returns for the title (`widget-title.ts` resolves `title_i18n`), falling back to the dataset's own `meta.name` only when the config entry has no `title` (none of these 10 do). Each `dataset_id` resolves against the query registered in `micro-data/service/dashboard/registry.go` — see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) §5 for the full catalog contract.

## 6. How this differs from the BU/personal widget system

| | This screen (`operation-plan`) | [reporting-audit/widget](/en/inventory/reporting-audit/widget) |
|---|---|---|
| Backend route | `GET api/:bu_code/dashboard-widgets/operation-plan/config` (config only; the bundled `GET …/operation-plan` remains as fallback) on `DashboardSystemWidgetsController`, then `GET api/:bu_code/datasets/:dataset_id` per tile | `GET api/:bu_code/dashboard-widgets/bu` (BU, on the separate `DashboardBuWidgetsController` — no frontend caller) or `GET api/me/dashboard-widgets` (personal, on the separate `DashboardPersonalWidgetsController` — a distinct root path, not nested under `:bu_code/dashboard-widgets/` at all) |
| Storage | Backstage dashboard-widget template rows (system templates), cached 60 s in the gateway | `tb_dashboard_bu_widget` / `tb_dashboard_personal_widget` (tenant DB rows) |
| Add / remove / reorder | Code change + deploy only | Real CRUD (`POST`/`PATCH`/`DELETE`) — BU widgets from each module's own landing dashboard, personal widgets from `/dashboard` |
| Frontend component | `operation-dashboard.tsx` — bespoke layout, 4 named sections (Metrics/Trends/Comparison/Distribution) | `DashboardWidgetGrid` (shared component, also used by [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard)) — one flat grid, sorted by widget-type render-group then `order_index` |

**Correction to a prior citation (applied to [reporting-audit/widget](/en/inventory/reporting-audit/widget) on 2026-09-22):** that page previously cited `procurement-dashboard.tsx → useProcurementWidgets → GET api/:bu_code/dashboard-widgets/bu` as an example BU-widget consumer. Reading `system-widgets.controller.ts` directly shows the actual route hit by `useProcurementWidgets`/`useOperationPlanWidgets`/`useVendorWidgets`/`useInventoryWidgets`/`useProductWidgets`/`useConfigWidgets` is `api/:bu_code/dashboard-widgets/{module}` on `DashboardSystemWidgetsController` (this page's mechanism, not the BU-widget one) — `DashboardBuWidgetsController`'s real `/bu` route lives on a genuinely separate controller, and the real personal-widget listing path the frontend actually calls (`api/me/dashboard-widgets`, via `hooks/use-my-dashboard-widgets.ts` → `MY_DASHBOARD_WIDGETS`, correctly documented at [reporting-audit/widget](/en/inventory/reporting-audit/widget) §1.1) is served by `DashboardPersonalWidgetsController` at that distinct root — not nested under `:bu_code/dashboard-widgets/` at all. `DashboardSystemWidgetsController` does carry its own `@Get('me')` handler (`api/:bu_code/dashboard-widgets/me`), which composes the same personal-widget list with live dataset values bundled in, but no frontend caller of that particular composite route was found (`useDashboardWidgets()` in `use-dashboard-widgets.ts` is only ever invoked with `procurement`/`inventory`/`product`/`config`/`vendor-management`/`operation-plan`, never `me`). This page and [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard) are the first two wiki pages to trace this distinction to source; a follow-up correction to `reporting-audit/widget.md` itself is recommended but out of scope here.

## 7. Cross-References

- [recipe](/en/inventory/recipe) — parent module; §4 "RBAC reality check" documents the current `operation_plan.*` permission keys (the dashboard route itself carries none).
- [recipe/category](/en/inventory/recipe/category), [recipe/cuisine](/en/inventory/recipe/cuisine), [recipe/equipment](/en/inventory/recipe/equipment), [recipe/equipment-category](/en/inventory/recipe/equipment-category) — the sub-modules this dashboard summarizes but does not link to.
- [vendor-pricelist/vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard) — the sibling module dashboard for Vendor Management; same backend mechanism, different frontend rendering component.
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — the code-registered catalog every `dataset_id` on this page references.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — the real, editable BU/personal widget system this screen is often conflated with; see §6 for the correction.

## 8. References

- **Frontend route:** `../carmen-frontend/routes/operation-plan/operation-plan.route.tsx` → `operation-dashboard.tsx`.
- **Frontend hook:** `../carmen-frontend/hooks/use-dashboard-widgets.ts` — `useOperationPlanWidgets()` → `useDashboardWidgetConfigs("operation-plan")`; per-tile `dashboardDatasetDataQueryOptions()` in `hooks/use-dashboard-dataset.ts`.
- **Frontend shared cards:** `../carmen-frontend/components/dashboard-widget/dashboard-widget-grid.tsx` — `LazyWidget`, `KpiCard`, `BarCard`, `PieCard`, `LineCard`, `WidgetSkeleton` (reused by this screen's bespoke layout, not the shared `DashboardWidgetGrid` wrapper); `widget-display.ts` — `gridClasses()`.
- **Gateway controller:** `../carmen-turborepo-backend/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.controller.ts` — `DashboardSystemWidgetsController`, `@Get(':module/config')` (2026-09-07) and the bundled `@Get('operation-plan')`. Bruno: `_uncategorized/dashboard-widgets/GET-module-config-dashboard-widgets.bru`, `GET-operation-plan-dashboard-widgets.bru`.
- **Gateway config:** `../carmen-turborepo-backend/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts` — `OPERATION_PLAN_WIDGETS`, `getSystemWidgets()`.
- **Dataset registry:** `../micro-data/service/dashboard/registry.go` — `recipe.*` (lines ~150-165), `equipment.*` (lines ~166-169) entries.
- **Translations:** `../carmen-frontend/messages/en.json` — `operationPlan.dashboard.title`/`.description`, `dashboardWidget.section*`.
