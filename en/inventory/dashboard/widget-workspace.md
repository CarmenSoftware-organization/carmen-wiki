---
title: Widget Workspace Dashboard
description: The live production dashboard at /dashboard — a personalised drag-and-drop workspace where each user pins dataset-backed KPI, pie, and bar widgets drawn from the system dataset catalog.
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, widget-workspace, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget Workspace Dashboard

> **At a Glance**
> **Route:** `/dashboard` &nbsp;·&nbsp; **For:** All operator roles post-login &nbsp;·&nbsp; **Status:** **Live** — backed by real API endpoints; dataset content depends on backend dataset population &nbsp;·&nbsp; **Scope:** Personal — each user's own saved widget layout

## 1. What & Who

The Widget Workspace is the **actual production dashboard** that loads when a user navigates to `/dashboard`. It replaces the static mock-data pages (`/dashboard/pr`, `/dashboard/po`, etc., which remain as standalone domain views). The page renders a personalised, drag-and-drop grid of widgets, each bound to a dataset from the system catalog.

> **Naming note:** This page documents the dashboard **layout** tables — `tb_widget_dashboard` (dashboard header) + `tb_widget_dashboard_item` (per-tile rows), seeded from `tb_widget_default_layout`. The similarly-named backend table `tb_widget_workspace` is a **different concept**: per-user saved data-explorer queries that surface in the data-explorer panel (not the dashboard grid) — see [reporting-audit/widget](/en/inventory/reporting-audit/widget) for the full multi-table data model.

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
| `categorical` | Pie / bar chart card |

**Audience**

- **Any logged-in user** — every operator builds their own workspace. There is no predefined layout; the workspace starts empty and grows as the user pins widgets.
- **Developers** — the compositing layer is `dashboard-component.tsx`; widget rendering is handled by `AppTile` / `SortableWidgetItem`.

## 2. Tiles & Drill-downs

Unlike the named domain dashboards (pr, po, grn…), the Widget Workspace has no fixed tile set. The grid is fully dynamic:

| Widget Card | Data source | Add via |
|---|---|---|
| Any `scalar` / `scalar_delta` dataset | `GET /api/proxy/api/me/dashboard-widgets` returns saved list; individual data fetched by `dataset_id` | "+ Add widget" picker |
| Any `categorical` dataset | Same endpoint, renders as pie/bar | "+ Add widget" picker |

Drill-downs from widget cards depend on the dataset definition and are not fixed by the workspace itself. Tile colours follow the dataset category and module-color-map conventions.

## 3. Common Questions

| Question | Answer |
|---|---|
| Why does the page show a greeting rather than tiles? | The workspace loads the user's saved widget list — if empty, it shows the empty-state prompt. Add at least one widget via the "+ Add widget" picker. |
| Where do the available datasets come from? | The "Add widget" picker calls `LookupDataset`, which queries the dataset catalog. Datasets are defined and seeded by backend; see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset). |
| Is this the same as the PR / PO / GRN dashboards in the sidebar? | No. Those six pages (`/dashboard/pr` etc.) are **domain-specific mock pages** (pipeline + tables). This workspace is the **live personalised widget grid** on the root `/dashboard` route. |
| Can I reset my layout to the default? | Not yet exposed in UI. Backend stores a `tb_widget_default_layout` table with seed items per scope; a reset-to-default action can be added as a future endpoint. |
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
- **Backend tables:** `tb_widget_dashboard` (dashboard container), `tb_widget_dashboard_item` (per-slot item with `sort_order`, `type`, `config`). Personal scope: `created_by_id = current_user`. Default seed layout: `tb_widget_default_layout` (scope = `personal`).

## 6. Refresh Cadence

- **Widget list** — `CACHE_DYNAMIC` (TanStack Query, staleTime 1 min). Refetched on focus; no polling.
- **Widget data** — fetched per `dataset_id` when the card mounts; cadence depends on dataset definition.
- **Reorder** — optimistic cache update on drag-end, then PATCH fires; no explicit refresh needed.

## 7. Related Modules

- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — data-model reference for the widget system (dataset shapes, widget types, DB schema)
- [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — admin UI for curating the dataset catalog that populates the picker
- [dashboard/my-pending](/en/inventory/dashboard/my-pending) — companion section on `/dashboard` showing personal pending counts
- [dashboard/my-approval](/en/inventory/dashboard/my-approval) — companion section on `/dashboard` showing personal approval task queue
- [dashboard/pr](/en/inventory/dashboard/pr) — domain-specific PR mock dashboard (separate route)
- [dashboard/main](/en/inventory/dashboard/main) — cross-module landing domain dashboard

## 8. Reference Sources

- **Page shell:** `../carmen-inventory-frontend-react/routes/dashboard/page.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-component.tsx`
- **Sortable item:** `../carmen-inventory-frontend-react/routes/dashboard/_components/sortable-widget-item.tsx`
- **Hooks:** `../carmen-inventory-frontend-react/hooks/use-my-dashboard-widgets.ts` — `useMyDashboardWidgets`, `useCreateMyDashboardWidget`, `useUpdateMyDashboardWidget`, `useDeleteMyDashboardWidget`
- **Types:** `../carmen-inventory-frontend-react/types/dashboard-widget.ts` — `WidgetConfig`, `WidgetConfigListResponse`, `DatasetShape`, `WidgetType`
- **API constants:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` → `MY_DASHBOARD_WIDGETS`, `MY_DASHBOARD_WIDGET_BY_ID`
- **Backend design:** `../carmen-turborepo-backend-v2/docs/superpowers/archive/widget/2026-05-12-widget-backend-design.md`
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md`
