---
title: Main Dashboard
description: Landing dashboard surfacing top-level KPIs across PR, PO, GRN, Inventory, and SR — the single pane shown immediately after login.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, landing, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Main Dashboard

## 1. Purpose

Main Dashboard is the post-login landing surface at `/dashboard/main` (reached from the bare `/dashboard` URL via server-side redirect). It answers the question *"how is the whole procure-to-pay chain doing this month?"* — a single pane of cross-domain KPIs aimed at an executive, controller, or department head who needs a snapshot before drilling into a specific module.

The page composes four KPI cards across the top, two charts (donut + horizontal bar) in the middle row, and two analysis blocks (PR pipeline bottleneck + top-5 vendors) at the bottom. Tiles are read-only and do not link out in the current implementation — drill-down behaviour is expected once the live data wiring lands.

## 2. Tiles / Widgets

| Tile | Type | What it shows | Drill-down | Data source (current) |
|---|---|---|---|---|
| Total Spend This Month | KPI card | `฿` value with up/down arrow vs. last month and % change | (Inferred — to be verified against live UI) | `mock/main.ts` → `kpiData.totalSpendThisMonth` |
| Pending PRs Count | KPI card | Integer count + subtext "HOD Approved, Awaiting Purchase" | (Inferred) → [[purchase-request]] | `mock/main.ts` → `kpiData.pendingPrCount` |
| Open POs Count | KPI card | Integer count + subtext "Waiting for Delivery" | (Inferred) → [[purchase-order]] | `mock/main.ts` → `kpiData.openPoCount` |
| Actual Spend vs Budget | KPI card with progress bar | Percent (0-100) and description | (Inferred) | `mock/main.ts` → `kpiData.budgetUtilization` |
| Spend by Material Group | Donut chart | Five segments (Food, Beverage, Supplies, Chemicals, Others) with percent labels | — | `mock/main.ts` → `spendByMaterialGroup` |
| Spend by Business Unit / Department | Horizontal bar chart | Five departments with `฿` amount labels | — | `mock/main.ts` → `spendByDepartment` |
| PR Pipeline: Bottleneck Analysis | Stacked bar list | Six stages (Saved, Committed, Awaiting HOD, Awaiting Purchase, Approved, Rejected) with count, `฿` amount, and a "Bottleneck" badge where flagged | (Inferred) → [[purchase-request]] | `mock/main.ts` → `prPipeline` |
| Top 5 Vendors by Spend | Table | Vendor name, total spend, PO count, average delivery time (days) | (Inferred) → [[vendor-pricelist]] | `mock/main.ts` → `topVendors` |

All amounts render via `formatCurrency` which uses `฿` and Thai locale grouping (`th-TH`).

## 3. Data Sources

Current build uses static fixtures in `app/(root)/dashboard/mock/main.ts`. When live data arrives the expected mapping is:

- KPI cards — aggregate queries against the [[purchase-request]], [[purchase-order]], and ledger tables, plus a budget-vs-actual report from [[reporting-audit]].
- Spend by Material Group / Department — grouped sum on PO or GRN lines joined to [[master-data/product-category]] and [[master-data/department]].
- PR Pipeline — group-count on [[purchase-request]] by `workflow_current_stage`.
- Top Vendors — sum on PO total amount grouped by `vendor_id`, joined to [[vendor-pricelist]] for vendor name.

## 4. Refresh Cadence

Currently static (mock module-level constants — rendered once on mount). Once wired to the my-pending and approval endpoints (`hooks/use-dashboard.ts`), TanStack Query's `CACHE_DYNAMIC` profile applies: `staleTime` 1 minute, `gcTime` 5 minutes — no auto-refetch interval, refetch on window focus per default TanStack behaviour.

## 5. Audience & Persona

- **Executive / GM** — wants the four KPI cards and the spend-by-department bar in one glance.
- **Procurement Manager** — uses the PR Pipeline block to spot bottleneck stages and the Top Vendors table to gauge supplier concentration.
- **Finance Controller** — watches Budget Utilisation and the donut share of Food vs. Beverage vs. Supplies.

## 6. Related Modules

- [[dashboard]] — module index with all sibling sub-pages
- [[dashboard/pr]] — drill destination for the PR Pipeline block
- [[dashboard/po]] — drill destination for Open POs and Top Vendors
- [[purchase-request]], [[purchase-order]], [[good-receive-note]] — transactional sources behind the spend aggregates
- [[reporting-audit]] — query datasets that will eventually back the spend-by-group and budget tiles

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/main/page.tsx` — page shell, dynamic-imports `DashboardMain`
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-main.tsx` — full tile composition
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/main.ts` — current mock data
- `../carmen-inventory-frontend/messages/en.json` → `dashboard.main.title` = "Dashboard"
