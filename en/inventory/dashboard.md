---
title: Dashboard
description: Cross-module dashboard surface — landing screen plus per-domain KPI views (PR, PO, GRN, Inventory, SR) that summarise live counts, aging, and exception buckets without opening each module.
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Dashboard

> **At a Glance**
> **Route:** `/dashboard` (server-redirects to `/dashboard/main`) &nbsp;·&nbsp; **For:** All operator roles post-login &nbsp;·&nbsp; **Status:** **Mock-data today**; live hooks defined but not mounted

![Dashboard screen](/screenshots/dashboard/index.png)

## 1. What & Who

The Dashboard module is the first screen most operators see after login. A sidebar group exposes six sibling pages — one per operational domain — each a read-only collage of tiles, tables, and charts that answers *"what needs my attention today?"* without opening the underlying transactional module.

**Production vs. mock dashboards:** The root `/dashboard` route loads the **live [widget-workspace](/en/inventory/dashboard/widget-workspace)** — a drag-and-drop personalised widget grid backed by real API endpoints. The six named sub-pages (`/dashboard/pr`, `/dashboard/po`, etc.) are **domain-specific mock-data pages** that remain for developer reference and QA testing but are not the primary operator-facing dashboard.

Three design notes that matter to developers and testers:

- The **six named pages** are **mock-data-driven** today via `app/(root)/dashboard/mock/*.ts`. Live count hooks (`useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`, `useApprovalPending`) exist but are **not yet mounted** on these pages.
- The **widget-workspace** (`/dashboard`) and its companion sections **my-pending** and **my-approval** are **live** — hooks are mounted and endpoints are wired.
- Tile colour stripes resolve via longest-prefix match in `constant/module-color-map.ts` (`--sub-pr`, `--sub-po`, `--sub-grn`, `--sub-store-requisition`, `--module-inventory`).

**Audience**

| Persona | Lands on | Why |
|---|---|---|
| Requestor | [dashboard/sr](/en/inventory/dashboard/sr), [dashboard/pr](/en/inventory/dashboard/pr) | Own pending requisitions and sent-back items |
| Approver (HOD, Procurement Manager) | [dashboard/pr](/en/inventory/dashboard/pr), [dashboard/po](/en/inventory/dashboard/po) | Approval queue + bottleneck pipeline |
| Purchaser | [dashboard/po](/en/inventory/dashboard/po) | Open POs, overdue deliveries, vendor performance |
| Receiver | [dashboard/grn](/en/inventory/dashboard/grn) | Pending POs to receive today/week, partial receipts |
| Inventory Controller / Store Manager | [dashboard/inventory](/en/inventory/dashboard/inventory) | Slow-moving stock, replenishment, PST status |
| Executive | [dashboard/main](/en/inventory/dashboard/main) | Cross-domain spend, budget utilisation, top vendors |

## 2. Pages in This Module

**Live production dashboard**

- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the `/dashboard` route; personalised drag-and-drop widget grid backed by live datasets; each user builds their own layout
- [dashboard/my-pending](/en/inventory/dashboard/my-pending) — personal pending-count widget (PR / PO / SR) showing documents awaiting the current user's own action
- [dashboard/my-approval](/en/inventory/dashboard/my-approval) — personal approval task-queue widget listing documents awaiting the current user's approval, grouped by type

**Domain-specific mock dashboards (dev/QA reference)**

- [dashboard/main](/en/inventory/dashboard/main) — landing dashboard with cross-module KPIs (spend, pending PRs, open POs, budget)
- [dashboard/pr](/en/inventory/dashboard/pr) — Purchase Request pipeline, sent-back/rejected, approval queue
- [dashboard/po](/en/inventory/dashboard/po) — Purchase Order pipeline, overdue deliveries, on-time / completeness gauges
- [dashboard/grn](/en/inventory/dashboard/grn) — Goods Receive Note KPIs, pending PO by day-band, incomplete/over-received GRNs
- [dashboard/inventory](/en/inventory/dashboard/inventory) — stock pipeline, slow-moving, replenishment, PST status, expired items
- [dashboard/sr](/en/inventory/dashboard/sr) — Store Requisition pipeline, sent-back, awaiting approval, consumption charts

---

## 3. Data Sources (Dev)

When live wiring is enabled, each tile resolves to one of three backend surfaces:

- **My-pending counts** — `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (see `constant/api-endpoints.ts`). Returns `{ pending: number }` per doc type.
- **Approval queue** — `GET /api/proxy/api/approval/pending` and `/summary`. Returns `ApprovalItem[]` grouped by `doc_type` (`pr` / `po` / `sr`) with `workflow_current_stage`, `doc_date`, `total_amount`.
- **Per-domain aggregates** — pipeline / KPI numbers (currently mock) will eventually resolve to query-dataset reports from [reporting-audit](/en/inventory/reporting-audit), not per-row scans of transactional tables.

See each sub-page for tile-to-endpoint mapping.

## 4. Related Modules

- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory) — transactional sources behind every tile
- [reporting-audit](/en/inventory/reporting-audit) — query datasets for KPI aggregates

## 5. Reference Sources

- `../carmen-inventory-frontend-react/routes/dashboard/page.tsx` — `/dashboard` redirect to `/dashboard/main`
- `../carmen-inventory-frontend-react/routes/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx` — per-domain page shells
- `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-{main,pr,po,grn,inventory,sr}.tsx` — tile compositions
- `../carmen-inventory-frontend-react/routes/dashboard/mock/{main,pr,po,grn,inventory,sr}.ts` — current mock data
- `../carmen-inventory-frontend-react/constant/module-list.ts` — sidebar registration of the six sub-pages
- `../carmen-inventory-frontend-react/constant/module-color-map.ts` — colour-stripe assignment per route
- `../carmen-inventory-frontend-react/hooks/use-dashboard.ts`, `hooks/use-approval.ts` — live count + approval hooks (not yet wired)
