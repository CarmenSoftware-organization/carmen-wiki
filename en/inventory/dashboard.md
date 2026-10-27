---
title: Dashboard
description: The single /dashboard landing page — a greeting header, a shared "Business unit dashboard" widget section, and a personal drag-and-drop 12-column "Saved Widgets" grid of dataset-backed cards (KPI, gauge, pie, bar, line, table, status pipelines) that each user builds for themselves.
published: true
date: 2026-10-27T00:00:00.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Dashboard

> **At a Glance**
> **Route:** `/dashboard` (root `/` redirects here) &nbsp;·&nbsp; **For:** All operator roles post-login &nbsp;·&nbsp; **Status:** **Live** — a single page: greeting header + a personal "Saved Widgets" grid backed by real API endpoints

![Dashboard screen](/screenshots/dashboard/index.png)

## Implementation status (verified 2026-07-16, re-verified 2026-10-27)

**2026-10-27 re-verification.** Still one route (`/dashboard`) and one top-level component. What changed since 2026-09-22 (FE `0713cbc9..391062b5`, backend `ef4d6f08f..c9d788829`, micro-data `7f21905..c9aa145`): **(1) a shared BU widget section** now renders above the personal grid on `/dashboard` and at the foot of every module dashboard — the BU-scoped `tb_dashboard_bu_widget` table that the 2026-09-22 text called "backend only, no UI" now has a screen (`components/dashboard-widget/bu-widget-section.tsx`, 2026-10-06); **(2) widget titles are bilingual** (`title_i18n` `{ en, th? }`, micro-data migration `132_dash_widget_title_i18n`); **(3) the shared widget components moved** out of `routes/dashboard/` into `components/dashboard-widget/` (`sortable-widget-item.tsx`, `widget-config-dialog.tsx`, `widget-param-fields.tsx`, `widget-display-fields.tsx`, `widget-shape.ts`) so the BU section and module dashboards reuse them; **(4) table widgets can link rows to documents** (`TableColumn.link`, e.g. the new `inventory.slow-moving` dataset's Type cell); **(5)** the empty state now has a real "add widget" button that opens the same picker as the header button. Details in [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) § 1.4-1.6.

**2026-09-22 re-verification (kept for history).**
**2026-09-22 re-verification.** Still one route, one component. What changed since 2026-07-29: the sidebar entry now carries `licenseFeature: "dashboard.widget"` (`constant/module-list.ts`; backend license catalog maps `app:dashboard-widgets` → `dashboard.widget`); the grid became a 12-column layout with per-widget size, gauge cards, render switching, per-widget lazy loading, a parameter/display dialog and status-group cards (see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) §1); and the dead `hooks/use-dashboard.ts` (`useMyPendingPrCount`/`PoCount`/`SrCount`) referenced below was finally **deleted** on 2026-08-31 (`02228125`, "ลบโค้ดตาย 17 ไฟล์"). `hooks/use-approval.ts` moved to `routes/procurement/approval/use-approval.ts` (2026-08-28, `0d9757f3`) and `/procurement/approval` now reads the unified `GET /api/my-pending` view instead of three per-type calls (2026-09-16, `9bd21427`).

The Dashboard module is **one route with one component**, not a sidebar group of six domain pages. `constant/module-list.ts` registers a single top-level entry, `{ name: "dashboard", path: "/dashboard" }`, with no sub-modules; `routes/router.tsx` has exactly one nested route, `{ path: "dashboard", lazy: () => import("./dashboard/dashboard.route") }`, resolving to `DashboardComponent` (greeting + a "Saved Widgets" grid, `routes/dashboard/dashboard-component.tsx`).

The eight sub-pages under this wiki module (`dashboard/main`, `pr`, `po`, `grn`, `inventory`, `sr`, `my-pending`, `my-approval`) each documented a named domain sub-page (`/dashboard/pr`, `/dashboard/po`, …) or a "companion widget" section on `/dashboard`. **None of these ever had a live route.** Checking the router history: even before the most recent cleanup, `dashboard/page.tsx` only ever rendered the same single greeting + saved-widgets component seen today — the per-domain files (`dashboard-main.tsx`, `dashboard-pr.tsx`, `dashboard-po.tsx`, `dashboard-grn.tsx`, `dashboard-inventory.tsx`, `dashboard-sr.tsx`) and the two companion-widget files (`dashboard-my-pending.tsx`, `dashboard-my-approval.tsx`) sat unrouted in `_components/`, each with its own `mock/*.ts` fixture. Commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) deleted all eight files plus the `mock/` directory, stating plainly: *"The mock-fed widgets and the my-pending/my-approval widgets were dead code carried over from the source app — no importers anywhere."*

Practical effect for this wiki: the sub-pages below are kept (file count unchanged) purely as **historical reference** to a demo screen that was never reachable by a user and no longer exists on disk. Treat every route, "mock-data today," and "live wiring pending" claim in them as void — they will not go live, because the components are gone.

## 1. What & Who

The Dashboard is the first screen every operator sees after login (root `/` redirects to `/dashboard`). It renders:

- A **greeting header** — "Good Morning/Afternoon/Evening, {full name}" plus the current localized date, from the user's profile.
- A **"Business unit dashboard" section** (new 2026-10-06) — widgets an administrator pinned for the whole business unit; everyone in the BU sees the same set, and users holding `dashboard.bu_widget:create/update/delete` can add, edit, delete and reorder them. The section hides itself when the BU has no widgets and the user cannot add any, or when the backend call fails.
- A **"Saved Widgets" section** — a personal, drag-and-drop 12-column grid of dataset-backed cards (KPI, gauge, pie, bar, line, area, table) plus full-width PR/PO/SR status-pipeline cards. Each card has its own size, parameters and display settings; each user builds their own personal layout from scratch. (The admin-curated part is the BU section above; a platform administrator can also push a default BU set to many BUs — see § 3.)

See [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) for the full page reference (layout, API calls, troubleshooting).

**Audience:** every logged-in operator — there is no per-persona routing on this page. Each user's saved-widget set is entirely their own (`user_id`-scoped), so what a Requestor, Approver, or Purchaser sees in the personal grid depends only on which datasets they personally chose to pin, not on their role; the BU section above it is identical for everyone in the business unit.

## 2. Pages in This Module

**Live page**

- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the actual `/dashboard` route; personal drag-and-drop widget grid backed by live datasets

**Historical reference only — removed 2026-06-27, never had a live route**

- [dashboard/main](/en/inventory/dashboard/main) — documented a deleted `dashboard-main.tsx` demo (cross-module KPI landing tiles)
- [dashboard/pr](/en/inventory/dashboard/pr) — documented a deleted `dashboard-pr.tsx` demo (PR pipeline, sent-back/rejected)
- [dashboard/po](/en/inventory/dashboard/po) — documented a deleted `dashboard-po.tsx` demo (PO pipeline, overdue deliveries)
- [dashboard/grn](/en/inventory/dashboard/grn) — documented a deleted `dashboard-grn.tsx` demo (GRN KPIs, pending PO by day-band)
- [dashboard/inventory](/en/inventory/dashboard/inventory) — documented a deleted `dashboard-inventory.tsx` demo (stock pipeline, replenishment, PST)
- [dashboard/sr](/en/inventory/dashboard/sr) — documented a deleted `dashboard-sr.tsx` demo (SR pipeline, consumption charts)
- [dashboard/my-pending](/en/inventory/dashboard/my-pending) — documented a deleted `dashboard-my-pending.tsx` widget (personal pending counts); the underlying hooks (`useMyPendingPrCount`/`PoCount`/`SrCount`, `hooks/use-dashboard.ts`) were deleted as dead code on 2026-08-31 (`02228125`); only the `MY_PENDING_*_COUNT` endpoint constants remain declared
- [dashboard/my-approval](/en/inventory/dashboard/my-approval) — documented a deleted `dashboard-my-approval.tsx` widget (personal approval queue); the real, live equivalent is the Procurement module's **My Approval** page — see [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) (`/procurement/approval`)

---

## 3. Data Sources (Dev)

- **Saved widgets (personal)** — `GET /api/proxy/api/me/dashboard-widgets?bu_code=` lists the signed-in user's pinned widgets; `POST`/`PATCH`/`DELETE` on the same path create, update (`title`, `order_index`, `params`, `widget_type`, `display`) and remove one. Served by **micro-data** (Go) through the gateway proxy with the `x-internal-token` header. See [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) §5 for the full shape.
- **BU widgets (shared)** — `GET /api/proxy/api/{bu}/dashboard-widgets/bu?module=` (`module=main` for `/dashboard`, otherwise one of `procurement`, `inventory`, `product`, `config`, `vendor-management`, `operation-plan`, `store-operation`) returns `{ items[], count, deploy_state }`; `POST`, `PATCH /{id}`, `DELETE /{id}` and `PATCH .../bu/reorder` need `dashboard.bu_widget:create|update|delete` (the two reads carry no `@Permission`). Values come from `GET .../dashboard-lab/widgets/{id}/data?scope=bu`. Served by micro-data (`/api/dashboard/bu-widgets*`) through the gateway proxy. A platform administrator can push a default set to BUs from the Backstage dashboard-templates module (gateway `api-system/dashboard-templates`, which calls micro-data `POST /api/dashboard/bu-widgets/deploy` with mode `skip_customized` or `overwrite`; `GET .../deploy-state` reports `deployed_version` / `customized_at`); the first manual edit stamps `customized_at` and the page warns once that the BU now differs from the platform default. See [reporting-audit/widget](/en/inventory/reporting-audit/widget) § 5.
- **Widget values** — one lazy `GET /api/proxy/api/{bu}/dashboard-lab/widgets/{widget_id}/data?scope=personal` per card (executes the stored dataset + params); status-group cards use `POST .../dashboard-lab/datasets/document.{doc}-by-status`.
- **Dataset catalog** — the "+ Add Widget" picker (`LookupDataset`) queries `GET /api/proxy/api/{bu}/dashboard-lab/datasets` (with `params[]` descriptors and `supported_renders[]`), the code-registered registry served by **micro-data**; see [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset).
- **Unused endpoints still declared in `constant/api-endpoints.ts`:** `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (`MY_PENDING_*_COUNT` — their hooks were deleted 2026-08-31, zero callers). The approval queue is consumed by `/procurement/approval` (`GET /api/my-pending` + `GET /api/my-approve/pending`, see [purchase-request/my-approval](/en/inventory/purchase-request/my-approval)), not by `/dashboard`.

## 4. Related Modules

- [reporting-audit](/en/inventory/reporting-audit), [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) — dataset catalog and widget/reporting data model behind every saved widget
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory) — transactional modules a user is likely to pin datasets from, but not directly wired to this page
- [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) — the real, live personal approval inbox (`/procurement/approval`); not part of this Dashboard module

## 5. Reference Sources

- `../carmen-frontend/routes/router.tsx` — single route registration: `{ path: "dashboard", lazy: () => import("./dashboard/dashboard.route") }`
- `../carmen-frontend/routes/dashboard/dashboard.route.tsx`, `dashboard-component.tsx`, `status-group.ts`, `status-group-card.tsx` and, shared with the module dashboards since 2026-10-06, `../carmen-frontend/components/dashboard-widget/` (`bu-widget-section.tsx`, `sortable-widget-item.tsx`, `widget-config-dialog.tsx`, `widget-param-fields.tsx`, `widget-display-fields.tsx`, `widget-shape.ts`, `widget-title.ts`, `table-row-link.ts`) — the entire live page
- `../carmen-frontend/docs/dashboard-widgets.md` — generated catalogue of the dev dataset registry (`bun run docs:widgets`, 2026-10-22); a snapshot, regenerate rather than copy from it
- `../carmen-frontend/constant/module-list.ts` — single-entry sidebar registration (no sub-modules), `licenseFeature: "dashboard.widget"`
- `../carmen-frontend/hooks/use-bu-dashboard-widgets.ts` — BU-widget list/create/update/delete/reorder + data query; `../carmen-frontend/routes/dashboard/use-my-dashboard-widgets.ts` — personal-widget CRUD + per-widget data hooks actually used by the live page (moved from `hooks/` on 2026-08-28)
- `../carmen-frontend/hooks/use-dashboard.ts` — **deleted 2026-08-31** (`02228125`); the `MY_PENDING_*_COUNT` constants it used remain in `constant/api-endpoints.ts` with no callers
- `../carmen-turborepo-backend/apps/backend-gateway/src/application/dashboard-widgets/`, `dashboard-lab/` and `../micro-data/` — backend (see [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) §8)
- Deletion commit: `03891e3d` in `../carmen-frontend` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) — removed `_components/dashboard-{main,pr,po,grn,sr,inventory,my-pending,my-approval}.tsx` and `mock/{main,pr,po,grn,sr,inventory}.ts` (19 files, 6 insertions / 5,468 deletions)
