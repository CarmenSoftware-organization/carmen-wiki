---
title: Dashboard
description: Cross-module dashboard surface — landing screen plus per-domain KPI views (PR, PO, GRN, Inventory, SR) that summarise live counts, aging, and exception buckets without opening each module.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Dashboard

## 1. Purpose

The Dashboard module is the first screen most operators see after login. The bare `/dashboard` URL server-redirects to `/dashboard/main`, and a sidebar group exposes six sibling pages — one per operational domain. Each page is a read-only collage of tiles, tables, and charts that answers the question *"what needs my attention today?"* without requiring the user to open the underlying transactional module.

Two design notes that matter for developers and testers:

- The current frontend implementation under `app/(root)/dashboard/*` is **mock-data-driven**. Every chart, KPI card, and table reads from `app/(root)/dashboard/mock/{main,pr,po,grn,inventory,sr}.ts` rather than a live API. The live hooks `useMyPendingPrCount` / `useMyPendingPoCount` / `useMyPendingSrCount` and `useApprovalPending` exist in `hooks/use-dashboard.ts` and `hooks/use-approval.ts` and back the reusable `dashboard-my-pending.tsx` and `dashboard-my-approval.tsx` components — but those reusable widgets are **not currently mounted** on any of the six sub-dashboard pages. Treat the rendered tiles as a UI prototype until the wiring to real endpoints lands.
- Tile colour stripes come from the longest-prefix match in `constant/module-color-map.ts`, which assigns each route to a CSS variable (`--sub-pr`, `--sub-po`, `--sub-grn`, `--sub-store-requisition`, `--module-inventory`).

## 3. Data Sources

When the live wiring is enabled, each tile will resolve to one of three backend surfaces:

- **My-pending counts** — `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (see `constant/api-endpoints.ts`). Returns `{ pending: number }` per doc type.
- **Approval queue** — `GET /api/proxy/api/approval/pending` and its `/summary` sibling. Returns `ApprovalItem[]` grouped by `doc_type` (`pr` / `po` / `sr`) with `workflow_current_stage`, `doc_date`, `total_amount`, etc.
- **Per-domain aggregates** — the per-dashboard pipeline / KPI numbers (currently mock) will eventually resolve to query-dataset reports from [[reporting-audit]], not to per-row scans of the transactional tables.

See each sub-page for the specific tile-to-endpoint mapping.

## 5. Audience & Persona

| Persona | Lands on | Why |
|---|---|---|
| Requestor | [[dashboard/sr]], [[dashboard/pr]] | Their own pending requisitions and sent-back items |
| Approver (HOD, Procurement Manager) | [[dashboard/pr]], [[dashboard/po]] | Approval queue + bottleneck pipeline |
| Purchaser | [[dashboard/po]] | Open POs, overdue deliveries, vendor performance |
| Receiver | [[dashboard/grn]] | Pending POs to receive today/week, partial receipts |
| Inventory Controller / Store Manager | [[dashboard/inventory]] | Slow-moving stock, replenishment, PST status |
| Executive | [[dashboard/main]] | Cross-domain spend, budget utilisation, top vendors |

## 6. Pages in This Module

- [[dashboard/main]] — landing dashboard with cross-module KPIs (spend, pending PRs, open POs, budget)
- [[dashboard/pr]] — Purchase Request pipeline, sent-back/rejected, approval queue
- [[dashboard/po]] — Purchase Order pipeline, overdue deliveries, on-time / completeness gauges
- [[dashboard/grn]] — Goods Receive Note KPIs, pending PO by day-band, incomplete/over-received GRNs
- [[dashboard/inventory]] — stock pipeline, slow-moving, replenishment, PST status, expired items
- [[dashboard/sr]] — Store Requisition pipeline, sent-back, awaiting approval, consumption charts

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/page.tsx` — `/dashboard` redirect to `/dashboard/main`
- `../carmen-inventory-frontend/app/(root)/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx` — per-domain page shells
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-{main,pr,po,grn,inventory,sr}.tsx` — tile compositions
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/{main,pr,po,grn,inventory,sr}.ts` — current mock data
- `../carmen-inventory-frontend/constant/module-list.ts` — sidebar registration of the six sub-pages
- `../carmen-inventory-frontend/constant/module-color-map.ts` — colour-stripe assignment per route
- `../carmen-inventory-frontend/hooks/use-dashboard.ts`, `hooks/use-approval.ts` — live count + approval hooks (not yet wired to the per-domain dashboards)
