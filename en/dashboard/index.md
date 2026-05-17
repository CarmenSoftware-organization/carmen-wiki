---
title: Dashboard
description: Cross-module dashboard surface — landing screen plus per-domain KPI views (PR, PO, GRN, Inventory, SR) that summarise live counts, aging, and exception buckets without opening each module.
published: true
date: 2026-05-17T07:28:28.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Dashboard

> **At a Glance**
> **Route:** `/dashboard` (server-redirects to `/dashboard/main`) &nbsp;·&nbsp; **For:** All operator roles post-login &nbsp;·&nbsp; **Status:** **Mock-data today**; live hooks defined but not mounted

![Dashboard screen](/assets/screenshots/dashboard/index.png)

## 1. What & Who

The Dashboard module is the first screen most operators see after login. A sidebar group exposes six sibling pages — one per operational domain — each a read-only collage of tiles, tables, and charts that answers *"what needs my attention today?"* without opening the underlying transactional module.

Two design notes that matter to developers and testers:

- All six pages are **mock-data-driven** today via `app/(root)/dashboard/mock/*.ts`. Live count hooks (`useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`, `useApprovalPending`) exist but are **not yet mounted**.
- Tile colour stripes resolve via longest-prefix match in `constant/module-color-map.ts` (`--sub-pr`, `--sub-po`, `--sub-grn`, `--sub-store-requisition`, `--module-inventory`).

**Audience**

| Persona | Lands on | Why |
|---|---|---|
| Requestor | [[dashboard/sr]], [[dashboard/pr]] | Own pending requisitions and sent-back items |
| Approver (HOD, Procurement Manager) | [[dashboard/pr]], [[dashboard/po]] | Approval queue + bottleneck pipeline |
| Purchaser | [[dashboard/po]] | Open POs, overdue deliveries, vendor performance |
| Receiver | [[dashboard/grn]] | Pending POs to receive today/week, partial receipts |
| Inventory Controller / Store Manager | [[dashboard/inventory]] | Slow-moving stock, replenishment, PST status |
| Executive | [[dashboard/main]] | Cross-domain spend, budget utilisation, top vendors |

## 2. Pages in This Module

- [[dashboard/main]] — landing dashboard with cross-module KPIs (spend, pending PRs, open POs, budget)
- [[dashboard/pr]] — Purchase Request pipeline, sent-back/rejected, approval queue
- [[dashboard/po]] — Purchase Order pipeline, overdue deliveries, on-time / completeness gauges
- [[dashboard/grn]] — Goods Receive Note KPIs, pending PO by day-band, incomplete/over-received GRNs
- [[dashboard/inventory]] — stock pipeline, slow-moving, replenishment, PST status, expired items
- [[dashboard/sr]] — Store Requisition pipeline, sent-back, awaiting approval, consumption charts

---

## 3. Data Sources (Dev)

When live wiring is enabled, each tile resolves to one of three backend surfaces:

- **My-pending counts** — `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (see `constant/api-endpoints.ts`). Returns `{ pending: number }` per doc type.
- **Approval queue** — `GET /api/proxy/api/approval/pending` and `/summary`. Returns `ApprovalItem[]` grouped by `doc_type` (`pr` / `po` / `sr`) with `workflow_current_stage`, `doc_date`, `total_amount`.
- **Per-domain aggregates** — pipeline / KPI numbers (currently mock) will eventually resolve to query-dataset reports from [[reporting-audit]], not per-row scans of transactional tables.

See each sub-page for tile-to-endpoint mapping.

## 4. Related Modules

- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]] — transactional sources behind every tile
- [[reporting-audit]] — query datasets for KPI aggregates

## 5. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/page.tsx` — `/dashboard` redirect to `/dashboard/main`
- `../carmen-inventory-frontend/app/(root)/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx` — per-domain page shells
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-{main,pr,po,grn,inventory,sr}.tsx` — tile compositions
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/{main,pr,po,grn,inventory,sr}.ts` — current mock data
- `../carmen-inventory-frontend/constant/module-list.ts` — sidebar registration of the six sub-pages
- `../carmen-inventory-frontend/constant/module-color-map.ts` — colour-stripe assignment per route
- `../carmen-inventory-frontend/hooks/use-dashboard.ts`, `hooks/use-approval.ts` — live count + approval hooks (not yet wired)
