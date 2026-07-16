---
title: Widget Workspace Dashboard
description: The live production dashboard at /dashboard — a personalised drag-and-drop workspace where each user pins dataset-backed KPI, pie, and bar widgets drawn from the system dataset catalog.
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, widget-workspace, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget Workspace Dashboard

> **At a Glance**
> **Route:** `/dashboard` &nbsp;·&nbsp; **For:** All operator roles post-login &nbsp;·&nbsp; **Status:** **Live** — backed by real API endpoints; dataset content depends on backend dataset population &nbsp;·&nbsp; **Scope:** Personal — each user's own saved widget layout

## 1. What & Who

The Widget Workspace is the **only page on the `/dashboard` route** — there is no separate set of named domain sub-pages behind it. (A prior version of this wiki claimed it "replaces" six mock pages at `/dashboard/pr`, `/dashboard/po`, etc.; those never existed as routes — see the sibling [dashboard/main](/en/inventory/dashboard/main), [pr](/en/inventory/dashboard/pr), etc. pages, each now flagged as historical-only.) The page renders a personalised, drag-and-drop grid of widgets, each bound to a dataset from the system catalog.

> **Naming note (corrected 2026-07-16):** The real backend tables are `tb_dashboard_personal_widget` (this page's data — tenant schema, `packages/prisma-shared-schema-tenant/prisma/schema.prisma` line ~6205: `dataset_id`, `widget_type`, `order_index`, `params`, scoped by `user_id`) and its sibling `tb_dashboard_bu_widget` (line ~6185, BU-scoped, admin-curated widgets shown to every member of a business unit — a **different, out-of-scope** feature that feeds the per-module landing dashboards under Procurement/Inventory-management/etc., not this page). A prior version of this note cited `tb_widget_dashboard`, `tb_widget_dashboard_item`, and `tb_widget_default_layout` — **none of these tables exist** in any Prisma schema (tenant, platform, or file) or in micro-data/micro-report. The similarly-named `tb_widget_workspace` is also a distinct, separate concept (per-user saved data-explorer queries) — see [reporting-audit/widget](/en/inventory/reporting-audit/widget) for that data model.

**Layout:**
- Greeting header (time-of-day + user full name) rendered from user profile.
- "Saved Widgets" section: a responsive grid (1 col → 2 col → 4 col) of user-selected widget cards, sorted by `order_index`.
- Each card is draggable via `@dnd-kit/core` — dropping reorders the list and PATCH-updates `order_index` optimistically.
- An "+ Add widget" lookup picker filters the dataset catalog by supported shapes (`scalar`, `scalar_delta`, `categorical`) and excludes already-pinned datasets.
- Empty state: decorative placeholder with chip hints (KPI / Pie / Bar) prompting the user to add their first widget.

**Widget shapes and render types:**

| Shape | Rendered as |
|---|---|
| `scalar` | KPI number card |
| `scalar_delta` | KPI number card with delta indicator |
| `categorical` | Pie card |

The dataset type system defines 6 shapes and 9 widget types in total (`enum_dashboard_widget_type`: `kpi`/`line`/`area`/`bar`/`pie`/`heatmap`/`gauge`/`table`/`sparkline`), but this page only lets a user pin the 3 shapes above (`SUPPORTED_SHAPES` in `dashboard-component.tsx`), and the creation flow (`inferWidgetTypeFromShape`) only ever assigns `widget_type: "kpi"` (for `scalar`/`scalar_delta`) or `"pie"` (for `categorical`) — it never creates a `"bar"` widget from this page's picker, even though `SortableWidgetItem`'s `WidgetRenderer` can render a `bar` card if one exists.

**Audience**

- **Any logged-in user** — every operator builds their own workspace. There is no predefined layout; the workspace starts empty and grows as the user pins widgets.
- **Developers** — the compositing layer is `dashboard-component.tsx`; widget rendering is handled by `AppTile` / `SortableWidgetItem`.

## 2. Tiles & Drill-downs

The Widget Workspace has no fixed tile set — the grid is fully dynamic and personal to each user:

| Widget Card | Data source | Add via |
|---|---|---|
| Any `scalar` / `scalar_delta` dataset | `GET /api/proxy/api/me/dashboard-widgets` returns saved list; individual data fetched by `dataset_id` | "+ Add widget" picker |
| Any `categorical` dataset | Same endpoint, renders as pie | "+ Add widget" picker |

Drill-downs from widget cards depend on the dataset definition and are not fixed by the workspace itself. Tile colours follow the dataset category and module-color-map conventions.

## 3. Common Questions

| Question | Answer |
|---|---|
| Why does the page show a greeting rather than tiles? | The workspace loads the user's saved widget list — if empty, it shows the empty-state prompt. Add at least one widget via the "+ Add widget" picker. |
| Where do the available datasets come from? | The "Add widget" picker calls `LookupDataset`, which queries the dataset catalog. Datasets are defined and seeded by backend; see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset). |
| Is this the same as the "PR / PO / GRN dashboards" documented in this module's other sub-pages? | No — and those sub-pages never had a live route either. This workspace **is** the entirety of `/dashboard`; the named "domain dashboards" describe demo files deleted 2026-06-27 (commit `03891e3d`) that were never wired into the router. |
| Can I reset my layout to the default? | Not exposed in UI. No default-layout table was found (`tb_dashboard_personal_widget` has no seed/default concept — each user's grid starts empty); a reset action would need a new backend feature. |
| Why does drag-and-drop sometimes revert? | Reordering is optimistic — the TanStack Query cache is updated immediately, then PATCH requests fire. If any PATCH fails a toast error appears; the cache is not automatically reverted in this version. |
| Where is `order_index` stored? | In the backend table that backs `GET /api/proxy/api/me/dashboard-widgets`. Each saved widget record has an `order_index` field incremented by 10 per slot. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Workspace loads but shows no widgets | User has no saved widgets yet | Click "+ Add widget" to pin at least one dataset |
| "+ Add widget" picker shows an empty list | No datasets in the catalog, or all supported shapes already pinned | Check with admin whether datasets have been seeded; verify `system-config/dashboard-dataset` |
| Widget card shows an error state | Dataset fetch returned a non-200 or the dataset was deleted | Remove the widget and re-add from the picker; report missing datasets to admin |
| Drag-and-drop does not activate | Pointer moved less than 6 px before release (activation constraint) | Press and drag at least 6 px before releasing to initiate a drag |
| Order reverts after refresh | PATCH request failed silently | Check browser console for toast error; backend may have a validation error on `order_index` |

---

## 5. Data Sources (Dev)

- **Saved widget list** — `GET /api/proxy/api/me/dashboard-widgets` → `WidgetConfigListResponse { items: WidgetConfig[], count }`. Hook: `useMyDashboardWidgets` (`hooks/use-my-dashboard-widgets.ts`).
- **Create widget** — `POST /api/proxy/api/me/dashboard-widgets` with `{ dataset_id, widget_type, title? }`. Hook: `useCreateMyDashboardWidget`.
- **Update widget** — `PATCH /api/proxy/api/me/dashboard-widgets/:id` with `{ order_index? | title? }`. Hook: `useUpdateMyDashboardWidget`.
- **Delete widget** — `DELETE /api/proxy/api/me/dashboard-widgets/:id`. Hook: `useDeleteMyDashboardWidget`.
- **Dataset catalog** (picker) — `LookupDataset` component queries dataset catalog filtered by shape.
- **Backend table:** `tb_dashboard_personal_widget` (tenant schema, ~line 6205) — `id`, `user_id`, `dataset_id`, `widget_type` (`enum_dashboard_widget_type`: `kpi`/`line`/`area`/`bar`/`pie`/`heatmap`/`gauge`/`table`/`sparkline`), `title`, `order_index`, `params` (JSONB), `doc_version`, standard audit columns. Scoped by `user_id`, soft-deleted via `deleted_at`. Served by `micro-cluster`'s `DashboardPersonalWidgetService`/`DashboardPersonalWidgetController` (TCP `dashboard-personal-widget.*`), fronted by `backend-gateway`'s `DashboardPersonalWidgetsController` at `api/me/dashboard-widgets`. No default/seed layout exists — new users start with an empty grid.

## 6. Refresh Cadence

- **Widget list** — `CACHE_DYNAMIC` (TanStack Query, staleTime 1 min). Refetched on focus; no polling.
- **Widget data** — fetched per `dataset_id` when the card mounts; cadence depends on dataset definition.
- **Reorder** — optimistic cache update on drag-end, then PATCH fires; no explicit refresh needed.

## 7. Related Modules

- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — data-model reference for the widget system (dataset shapes, widget types, DB schema)
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — admin UI for curating the dataset catalog that populates the picker
- [dashboard/my-pending](/en/inventory/dashboard/my-pending), [dashboard/my-approval](/en/inventory/dashboard/my-approval) — **historical only**; these documented separate widget sections that were never rendered on this page (dead code, deleted 2026-06-27) — see [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) for the real, live approval inbox
- [dashboard/pr](/en/inventory/dashboard/pr), [dashboard/main](/en/inventory/dashboard/main) — **historical only**; documented demo files deleted 2026-06-27, never routed

## 8. Reference Sources

- **Route:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard.route.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx` (flattened out of `_components/` by the 2026-06-27 cleanup, commit `03891e3d`)
- **Sortable item:** `../carmen-inventory-frontend-react/routes/dashboard/sortable-widget-item.tsx`
- **Hooks:** `../carmen-inventory-frontend-react/hooks/use-my-dashboard-widgets.ts` — `useMyDashboardWidgets`, `useCreateMyDashboardWidget`, `useUpdateMyDashboardWidget`, `useDeleteMyDashboardWidget`
- **Types:** `../carmen-inventory-frontend-react/types/dashboard-widget.ts` — `WidgetConfig`, `WidgetConfigListResponse`, `DatasetShape`, `WidgetType`
- **API constants:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` → `MY_DASHBOARD_WIDGETS`, `MY_DASHBOARD_WIDGET_BY_ID`
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/dashboard-widget/dashboard-personal-widget.service.ts` + `.controller.ts`; gateway route in `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-personal-widgets.controller.ts`
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dashboard_personal_widget` (~line 6205), `tb_dashboard_bu_widget` (~line 6185), `enum_dashboard_widget_type` (~line 6162)
- **Backend design:** `../carmen-turborepo-backend-v2/docs/superpowers/archive/widget/2026-05-12-widget-backend-design.md`
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md` _(historical; this spec lived in the legacy Next.js frontend repo and was not carried over to -react)_
