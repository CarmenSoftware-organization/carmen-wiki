---
title: Vendor Management Dashboard
description: The /vendor-management landing screen — 10 hardcoded KPI/chart tiles (vendor + pricelist + RFP) sourced from a code-registered dataset catalog, not a user-configurable widget board.
published: true
date: 2026-07-29T10:15:00.000Z
tags: vendor-pricelist, vendor-management, dashboard, widget, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:15:00.000Z
---

# Vendor Management Dashboard

> **At a Glance**
> **Route:** `/vendor-management` (index) &nbsp;·&nbsp; **Component:** `vendor-dashboard.tsx` &nbsp;·&nbsp; **Data:** `GET /api/{bu_code}/dashboard-widgets/vendor-management` &nbsp;·&nbsp; **Tiles:** 10 hardcoded (7 KPI, 2 chart, 1 line) covering vendor, pricelist, and RFP &nbsp;·&nbsp; **Not editable** — no add/remove/reorder UI, no per-tenant customization.

![Vendor Management dashboard](/screenshots/vendor-management/index.png)

## 1. What & Who

The Vendor Management Dashboard is the landing screen at `/vendor-management`, shown before the user picks [Vendor](/en/inventory/vendor-pricelist), Price List, Price List Template, or [Request for Pricing](/en/inventory/vendor-pricelist/request-price-list). It renders a fixed set of **10 dashboard tiles** built from `vendor.*`, `pricelist.*`, and `rfp.*` entries in the [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog. The UI translation key is `vendorManagement.dashboard` (`title: "Vendor Overview"`, `description: "Vendor, pricelist, and RFP status"`).

Unlike [operation-dashboard](/en/inventory/recipe/operation-dashboard) (which has a bespoke layout component), this screen is a thin wrapper around the shared `DashboardWidgetGrid` component — the same one that would power any other module dashboard that chooses to reuse it. It renders one flat responsive grid instead of named sections, sorted by a fixed widget-type render-group (`kpi`/`gauge` → `sparkline` → `pie` → `bar` → `line`/`area` → `table` → `heatmap`) and then by `order_index` within each group.

**This is the same hardcoded, non-editable mechanism documented in full at [recipe/operation-dashboard](/en/inventory/recipe/operation-dashboard) §6** — a fixed TypeScript array (`VENDOR_MANAGEMENT_WIDGETS` in `system-widgets.config.ts`) with no database row backing any tile, served by a dedicated per-module endpoint on `DashboardSystemWidgetsController` (`api/:bu_code/dashboard-widgets/vendor-management`) — **not** `tb_dashboard_bu_widget`/`tb_dashboard_personal_widget` (the real, editable widget tables documented at [reporting-audit/widget](/en/inventory/reporting-audit/widget)).

**Maintained by** Engineering (code change + deploy to add/remove/reorder a tile — no admin screen exists). **Read by** any authenticated user who can load `/vendor-management` — no permission check was found gating the data endpoint itself.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View vendor-management KPIs | Navigate to `/vendor-management` | Loads automatically; no filter/date-range controls exist |
| Drill into a metric | Click a tile (visual only) | Tiles are read-only cards, not links — navigate to Vendor / Price List / Request for Pricing manually to inspect underlying records |
| Add/remove/reorder a tile | **Not possible from the UI** | Requires a code change to `system-widgets.config.ts` (backend-gateway) |
| Retry after a load error | Reload the page | One inline error banner (`dashboardWidget.loadError`) covers the whole tile set — no per-tile retry |

## 3. Validation & Errors

| Symptom | Cause | Confirmed? |
|---|---|---|
| Whole dashboard shows a load-error banner | `GET .../dashboard-widgets/vendor-management` failed | **Confirmed** — `DashboardWidgetGrid` renders one `role="alert"` banner keyed to the query's `isError` |
| A tile silently disappears from the grid | Its `dataset_id` failed to resolve (`meta`/`data` missing) | **Confirmed** — `WidgetRouter` returns `null` for any widget lacking both `meta` and `data` |
| Empty-state message ("No widget data") | All 10 configured datasets failed to resolve | **Confirmed** — gated on the post-filter widget list being empty |
| Skeleton grid shows 6 placeholder cards while loading | `SKELETON_KEYS` (`a`-`f`) is hardcoded in `dashboard-widget-grid-lazy.tsx`'s Suspense fallback | **Confirmed** — cosmetic only; the real resolved set is 10 tiles, not 6 |
| Chart library (`recharts`) briefly not loaded on first navigation | `DashboardWidgetGrid` is lazy-loaded (`React.lazy` + `Suspense`) to keep `recharts` (~100-150KB gzipped) out of first-load JS | **Confirmed**, by design — `dashboard-widget-grid-lazy.tsx`'s own code comment states this explicitly |

## 4. Edge Cases

- **No permission gate found on the data endpoint.** `DashboardSystemWidgetsController` is guarded only by `KeycloakGuard` — no permission decorator was found on the `vendor-management` route handler. This is distinct from the sidebar's own `/vendor-management/*` sub-screen gates, which use real `vendor_management.*` permission keys (e.g. `vendor_management.vendor.view`) — those keys are confirmed live in the backend permission catalog (unlike `recipe`'s `operation_plan.view` placeholder), but none of them gate this dashboard's own data call either.
- **Tiles are hardcoded, not stored.** Every business unit sees the identical 10 tiles in the identical order — nothing about tile selection, order, or title is tenant-configurable through this screen.
- **`rfp.issued-daily` is the only time-series tile** — a `line` chart despite the module having no dedicated Trends section (unlike [operation-dashboard](/en/inventory/recipe/operation-dashboard)'s explicit section grouping, this screen's shared grid just slots it after the bar/pie tiles per the fixed render-group order).
- **Two pricelist-lifecycle KPIs sit side by side with no visual distinction of urgency:** `pricelist.active-count` (a plain scalar) and `pricelist.expiring-soon` (also a plain scalar, "≤30d") render as identical `KpiCard`s — there is no color/badge escalation on the expiring-soon tile despite its operational urgency.
- **Cache.** The widget list query uses `CACHE_DYNAMIC` (`useVendorWidgets` → `useDashboardWidgets("vendor-management")`), the same tier as every other module dashboard.

---

## 5. Tiles (Dev)

Source: `apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts`, `VENDOR_MANAGEMENT_WIDGETS`.

| # | `dataset_id` | Type | Title (Thai, as coded) |
|---|---|---|---|
| 0 | `vendor.total-active` | kpi | Vendor active |
| 1 | `vendor.added-7d` | kpi | Vendor เพิ่มใน 7 วัน |
| 2 | `vendor.without-products` | kpi | Vendor ไม่มี product |
| 3 | `pricelist.active-count` | kpi | Pricelist active |
| 4 | `pricelist.expiring-soon` | kpi | Pricelist ใกล้หมดอายุ (30d) |
| 5 | `rfp.active` | kpi | RFP เปิดอยู่ |
| 6 | `rfp.upcoming-7d` | kpi | RFP จะเปิดใน 7 วัน |
| 7 | `pricelist.by-status` | pie | Pricelist แยกตามสถานะ |
| 8 | `pricelist.by-vendor-top` | bar | Top 10 vendor ตามจำนวน pricelist |
| 9 | `rfp.issued-daily` | line | RFP สร้างต่อวัน (30d) |

Titles are hardcoded on the config entry (in Thai in the current source), not translated via `use-intl`. Each `dataset_id` resolves against `micro-data/service/dashboard/registry.go`'s **"Vendor management module"** section — see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) §5 for the full catalog contract, including the `spend` category these 10 all share.

## 6. Cross-References

- [vendor-pricelist](/en/inventory/vendor-pricelist) — parent module; documents the four real CRUD screens (Vendor, Price List, Price List Template, Request for Pricing) this dashboard summarizes but does not link to.
- [vendor-pricelist/request-price-list](/en/inventory/vendor-pricelist/request-price-list) — source of the `rfp.*` datasets.
- [recipe/operation-dashboard](/en/inventory/recipe/operation-dashboard) — sibling module dashboard for Operation Plan; §6 there has the full comparison against the real BU/personal widget system and the citation this page's mechanism corrects.
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — the code-registered catalog every `dataset_id` on this page references.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — the real, editable BU/personal widget system this screen is often conflated with.

## 7. References

- **Frontend route:** `../carmen-inventory-frontend-react/routes/vendor-management/vendor-management.route.tsx` → `vendor-dashboard.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-dashboard-widgets.ts` — `useVendorWidgets()`.
- **Frontend shared component:** `../carmen-inventory-frontend-react/components/dashboard-widget/dashboard-widget-grid-lazy.tsx` (lazy wrapper) → `dashboard-widget-grid.tsx`'s `DashboardWidgetGrid`.
- **Gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.controller.ts` — `DashboardSystemWidgetsController`, `@Get('vendor-management')`.
- **Gateway config:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts` — `VENDOR_MANAGEMENT_WIDGETS`, `getSystemWidgets()`.
- **Dataset registry:** `../micro-data/service/dashboard/registry.go` — vendor/pricelist/RFP entries (lines ~127-147).
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `vendorManagement.dashboard.title`/`.description`.
