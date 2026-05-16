---
title: GRN Dashboard
description: Goods Receive Note KPIs — receiving-now / received-today / MTD / YTD counts, tabbed pending PO by day-band, overdue PO with critical highlight, incomplete and over-received GRN tables, plus top vendors and category spend.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, good-receive-note, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# GRN Dashboard

## 1. Purpose

GRN Dashboard at `/dashboard/grn` is the receiver's operations board. It answers *"what's hitting the dock today, what's late, and where are receipts disagreeing with the order?"* The page leads with four KPI cards (Receiving Now, Received Today, MTD, YTD), then arranges four data tables in a 2×2 grid (Pending PO by day-band tabs, Overdue PO, Incomplete GRNs, Over-Received GRNs), and closes with two analytics charts on YTD spend.

The Pending PO block is interactive — a three-button tab strip (TODAY / THIS WEEK / NEXT WEEK) swaps the table data client-side without a page navigation.

## 2. Tiles / Widgets

| Tile | Type | What it shows | Drill-down | Data source (current) |
|---|---|---|---|---|
| Receiving Now | KPI card | Integer count, arrow icon, primary colour | (Inferred) → [[good-receive-note]] in-progress | `mock/grn.ts` → `grnKpi.receivingNow` |
| Received Today | KPI card | Integer count, check icon, success colour | (Inferred) → [[good-receive-note]] today | `mock/grn.ts` → `grnKpi.receivedToday` |
| GRN Total (MTD) | KPI card | Integer count, calendar icon | (Inferred) → [[good-receive-note]] month-to-date | `mock/grn.ts` → `grnKpi.grnMtd` |
| GRN Total (YTD) | KPI card | Formatted number, package icon | (Inferred) → [[good-receive-note]] year-to-date | `mock/grn.ts` → `grnKpi.grnYtd` |
| Pending Purchase Orders (PO) | Tabbed table — Today / This Week / Next Week | PO ID, Supplier Name, Expected Date, Items Count, Total Amount, Priority badge (`High` / `Medium` / `Low`) | (Inferred) → [[purchase-order]] | `mock/grn.ts` → `pendingPoToday` / `pendingPoThisWeek` / `pendingPoNextWeek` |
| Overdue Purchase Orders | Table with critical highlight | PO ID, Supplier, Original Due Date, Days Overdue (red badge `OVERDUE` if ≥ 10 days, otherwise red number), Items Count | (Inferred) → [[purchase-order]] | `mock/grn.ts` → `overduePos` (threshold `OVERDUE_THRESHOLD = 10`) |
| Incomplete GRNs (Partial Receipts) | Table | GRN ID, PO ID, Supplier, Qty Ordered, Qty Received, Variance %, "Partially Received" info badge | (Inferred) → [[good-receive-note]] | `mock/grn.ts` → `incompleteGrns` |
| Over-Received GRNs (Excess Receipts) | Table | GRN ID (with AlertTriangle), PO ID, Supplier, PO Amount, GRN Amount, Excess Amount, Variance % | (Inferred) → [[good-receive-note]] | `mock/grn.ts` → `overReceivedGrns` |
| Top 5 Vendors by Purchase YTD (USD Millions) | Horizontal bar chart | Vendor name + `$NM` value labels | (Inferred) → [[vendor-pricelist]] | `mock/grn.ts` → `topVendorsYtd` |
| Purchasing Spend by Category | Grouped vertical bar chart | Current Month vs YTD Total per category | — | `mock/grn.ts` → `spendByCategory` |

The 10-day overdue threshold (`OVERDUE_THRESHOLD`) is hard-coded in `dashboard-grn.tsx` — production should source this from a configurable SLA setting.

## 3. Data Sources

Currently mocked. Expected live mapping:

- KPI cards — count queries on [[good-receive-note]] filtered by `status` ("in progress" for Receiving Now, `commit_date = today` for Received Today, etc.).
- Pending PO tabs — [[purchase-order]] lines grouped by `expected_delivery_date` bucket (today / this-week / next-week) where no [[good-receive-note]] line has been committed.
- Overdue PO — [[purchase-order]] lines where `expected_delivery_date < CURRENT_DATE` AND not fully received. Days overdue = `CURRENT_DATE - expected_delivery_date`.
- Incomplete / Over-Received GRNs — both join committed [[good-receive-note]] lines back to their [[purchase-order]] line; "incomplete" is `received_qty < ordered_qty`, "over-received" is `received_qty > ordered_qty`. Variance % is computed on the frontend.
- Top Vendors YTD — sum on GRN line amount grouped by `vendor_id`, top 5.
- Spend by Category — sum on GRN line amount grouped by [[master-data/product-category]], split current month vs YTD.

## 4. Refresh Cadence

Static mock today. The four KPI cards and the Receiving Now figure should refetch frequently once wired (dock activity is real-time-ish); recommend `CACHE_DYNAMIC` (1-minute stale) at minimum. The Top Vendors YTD chart can use `CACHE_NORMAL` (5-minute stale) since YTD totals change slowly.

## 5. Audience & Persona

- **Receiver / Dock Operator** — primary. Watches Pending PO tabs to prep for the day, Overdue PO to escalate to Purchasing, and Receiving Now to know who's at the dock right now.
- **Inventory Controller** — uses Incomplete and Over-Received GRN tables for variance investigation before committing to inventory.
- **Procurement Manager** — reviews Top Vendors YTD and Spend by Category for supplier performance.

## 6. Related Modules

- [[good-receive-note]] — transactional system-of-record
- [[purchase-order]] — upstream commitment behind every pending / overdue row
- [[inventory]] — downstream stock impact once GRN commits
- [[vendor-pricelist]] — vendor master for the Top Vendors chart
- [[costing]] — variance handling for over-received quantities tied to commit-time costing

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/grn/page.tsx` — page shell
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-grn.tsx` — `DashboardGrn` composition (KPI cards, pending PO tabs, overdue PO, incomplete GRNs, over-received GRNs, top vendors, spend by category)
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/grn.ts` — fixture data
- `../carmen-inventory-frontend/messages/en.json` → `dashboard.grn.title` = "Goods Receive Note Dashboard"
