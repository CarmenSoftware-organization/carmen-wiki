---
title: Operation Plan Dashboard
description: The /operation-plan landing screen — 10 hardcoded KPI/chart tiles (recipe + equipment) sourced from a code-registered dataset catalog, not a user-configurable widget board.
published: true
date: 2026-07-29T10:52:30.000Z
tags: recipe, operation-plan, dashboard, widget, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:00:00.000Z
---

# Operation Plan Dashboard

> **At a Glance**
> **Route:** `/operation-plan` (index) &nbsp;·&nbsp; **Component:** `operation-dashboard.tsx` &nbsp;·&nbsp; **Data:** `GET /api/{bu_code}/dashboard-widgets/operation-plan` &nbsp;·&nbsp; **Tiles:** 10 hardcoded (5 KPI, 5 chart) covering recipe + equipment &nbsp;·&nbsp; **Not editable** — no add/remove/reorder UI, no per-tenant customization.

![Operation Plan dashboard](/screenshots/operation-plan/index.png)

## 1. What & Who

The Operation Plan Dashboard is the landing screen shown at `/operation-plan` before the user picks a sub-module ([Recipe](/en/inventory/recipe), [Recipe Category](/en/inventory/recipe/category), [Cuisine](/en/inventory/recipe/cuisine), [Equipment](/en/inventory/recipe/equipment), [Equipment Category](/en/inventory/recipe/equipment-category)). It renders a fixed set of **10 dashboard tiles** — 5 KPI cards and 5 charts — built from `recipe.*` and `equipment.*` entries in the [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog. The UI translation key that names it is `operationPlan.dashboard` (`title: "Operations Overview"`, `description: "Recipe, cuisine, and equipment status across the operation plan"`).

**This is not the same mechanism as [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) or [reporting-audit/widget](/en/inventory/reporting-audit/widget).** Those pages document `tb_dashboard_bu_widget` (BU-curated, addable/removable) and `tb_dashboard_personal_widget` (per-user, addable/removable) — both real, editable widget tables served by the **micro-data** Go service. This screen's 10 tiles are a **third, separate mechanism**: a hardcoded TypeScript array (`SystemWidgetConfig[]`) baked into the backend-gateway, with no database row backing any individual tile at all. See §6 for the exact distinction and the one prior-page citation this corrects.

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
| A tile silently disappears from the grid | Its `dataset_id` failed to resolve (`meta`/`data` missing) | **Confirmed** — `isResolved()` filters out any widget lacking both `meta` and `data` before rendering; a broken dataset just vanishes rather than showing an error tile |
| Empty-state message ("No widget data") | All 10 configured datasets failed to resolve, or the catalog entries were removed | **Confirmed** — `hasAny` gates the empty-state message against the post-filter, post-sort resolved list |
| Skeleton grid shows exactly 4 placeholder cards while loading | `Array.from({ length: 4 })` is hardcoded in the loading state | **Confirmed** — cosmetic only; the real resolved set is 10 tiles, not 4 |

## 4. Edge Cases

- **No permission gate found on the data endpoint.** `DashboardSystemWidgetsController` (`api/:bu_code/dashboard-widgets`) is guarded only by `KeycloakGuard` (any authenticated user) — no `@RequirePermission`-style decorator was found on the `operation-plan` route handler, unlike the sidebar entry for `/operation-plan/*` sub-screens which gate on `operation_plan.view`. `operation_plan.view` itself is a confirmed **frontend-only placeholder** (see [recipe](/en/inventory/recipe) §4 "RBAC reality check") — it is not consumed anywhere to guard this dashboard route or its data call.
- **Tiles are hardcoded, not stored.** Unlike `tb_dashboard_bu_widget`/`tb_dashboard_personal_widget` rows, nothing about tile selection, order, or title lives in the tenant database — the entire configuration for this screen is the `OPERATION_PLAN_WIDGETS` array in `system-widgets.config.ts` (backend-gateway). Every business unit sees the identical 10 tiles in the identical order.
- **Layout is grouped by widget type, not by the config's own `order_index`.** The frontend groups resolved widgets into 4 named sections (KPI, Trends, Comparison, Distribution) and sorts *within* each section by `order_index` — it does not render one flat grid in `order_index` order the way the generic `DashboardWidgetGrid` component (used by [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard)) does. See §6 for the code-level difference between the two dashboards' rendering paths.
- **`equipment.by-category` is the only pie-shaped tile in this set** (categorical shape) — everything else is `kpi` (scalar/scalar_delta) or `bar` (categorical/ranked rendered as bars). There is no line/area/time-series tile even though `recipe.added-daily` (a `time_series`-shaped dataset) exists in the catalog — it is not one of the 10 configured tiles for this dashboard.
- **Cache.** The widget list query uses `CACHE_DYNAMIC` (`useOperationPlanWidgets` → `useDashboardWidgets("operation-plan")`), the same caching tier as every other module dashboard.

---

## 5. Tiles (Dev)

Source: `apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts`, `OPERATION_PLAN_WIDGETS`.

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

Titles are hardcoded strings on the config entry (in Thai in the current source) — they are **not** passed through `use-intl`; the frontend renders whatever string the gateway returns for `title`, falling back to the dataset's own `meta.name` only when the config entry has no `title` (none of these 10 do). Each `dataset_id` resolves against the query registered in `micro-data/service/dashboard/registry.go` — see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) §5 for the full catalog contract.

## 6. How this differs from the BU/personal widget system

| | This screen (`operation-plan`) | [reporting-audit/widget](/en/inventory/reporting-audit/widget) |
|---|---|---|
| Backend route | `GET api/:bu_code/dashboard-widgets/operation-plan` — a fixed, per-module endpoint on `DashboardSystemWidgetsController` | `GET api/:bu_code/dashboard-widgets/bu` (BU, on the separate `DashboardBuWidgetsController`) or `GET api/me/dashboard-widgets` (personal, on the separate `DashboardPersonalWidgetsController` — a distinct root path, not nested under `:bu_code/dashboard-widgets/` at all) |
| Storage | None — a hardcoded array in gateway source (`system-widgets.config.ts`) | `tb_dashboard_bu_widget` / `tb_dashboard_personal_widget` (tenant DB rows) |
| Add / remove / reorder | Code change + deploy only | Real CRUD (`POST`/`PATCH`/`DELETE`) — BU widgets from each module's own landing dashboard, personal widgets from `/dashboard` |
| Frontend component | `operation-dashboard.tsx` — bespoke layout, 4 named sections (Metrics/Trends/Comparison/Distribution) | `DashboardWidgetGrid` (shared component, also used by [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard)) — one flat grid, sorted by widget-type render-group then `order_index` |

**Correction to a prior citation:** [reporting-audit/widget](/en/inventory/reporting-audit/widget) §1 cites `procurement-dashboard.tsx → useProcurementWidgets → GET api/:bu_code/dashboard-widgets/bu` as an example BU-widget consumer. Reading `system-widgets.controller.ts` directly shows the actual route hit by `useProcurementWidgets`/`useOperationPlanWidgets`/`useVendorWidgets`/`useInventoryWidgets`/`useProductWidgets`/`useConfigWidgets` is `api/:bu_code/dashboard-widgets/{module}` on `DashboardSystemWidgetsController` (this page's mechanism, not the BU-widget one) — `DashboardBuWidgetsController`'s real `/bu` route lives on a genuinely separate controller, and the real personal-widget listing path the frontend actually calls (`api/me/dashboard-widgets`, via `hooks/use-my-dashboard-widgets.ts` → `MY_DASHBOARD_WIDGETS`, correctly documented at [reporting-audit/widget](/en/inventory/reporting-audit/widget) §1.1) is served by `DashboardPersonalWidgetsController` at that distinct root — not nested under `:bu_code/dashboard-widgets/` at all. `DashboardSystemWidgetsController` does carry its own `@Get('me')` handler (`api/:bu_code/dashboard-widgets/me`), which composes the same personal-widget list with live dataset values bundled in, but no frontend caller of that particular composite route was found (`useDashboardWidgets()` in `use-dashboard-widgets.ts` is only ever invoked with `procurement`/`inventory`/`product`/`config`/`vendor-management`/`operation-plan`, never `me`). This page and [vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard) are the first two wiki pages to trace this distinction to source; a follow-up correction to `reporting-audit/widget.md` itself is recommended but out of scope here.

## 7. Cross-References

- [recipe](/en/inventory/recipe) — parent module; §4 "RBAC reality check" documents the `operation_plan.view` placeholder permission this dashboard's route also carries no real gate for.
- [recipe/category](/en/inventory/recipe/category), [recipe/cuisine](/en/inventory/recipe/cuisine), [recipe/equipment](/en/inventory/recipe/equipment), [recipe/equipment-category](/en/inventory/recipe/equipment-category) — the sub-modules this dashboard summarizes but does not link to.
- [vendor-pricelist/vendor-dashboard](/en/inventory/vendor-pricelist/vendor-dashboard) — the sibling module dashboard for Vendor Management; same backend mechanism, different frontend rendering component.
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — the code-registered catalog every `dataset_id` on this page references.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — the real, editable BU/personal widget system this screen is often conflated with; see §6 for the correction.

## 8. References

- **Frontend route:** `../carmen-inventory-frontend-react/routes/operation-plan/operation-plan.route.tsx` → `operation-dashboard.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-dashboard-widgets.ts` — `useOperationPlanWidgets()`.
- **Frontend shared cards:** `../carmen-inventory-frontend-react/components/dashboard-widget/dashboard-widget-grid.tsx` — `KpiCard`, `BarCard`, `PieCard`, `LineCard`, `WidgetSkeleton` (reused by this screen's bespoke layout, not the shared `DashboardWidgetGrid` wrapper).
- **Gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.controller.ts` — `DashboardSystemWidgetsController`, `@Get('operation-plan')`.
- **Gateway config:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts` — `OPERATION_PLAN_WIDGETS`, `getSystemWidgets()`.
- **Dataset registry:** `../micro-data/service/dashboard/registry.go` — `recipe.*` (lines ~150-165), `equipment.*` (lines ~166-169) entries.
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `operationPlan.dashboard.title`/`.description`, `dashboardWidget.section*`.
