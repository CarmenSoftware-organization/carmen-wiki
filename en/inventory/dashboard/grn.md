---
title: GRN Dashboard
description: Goods Receive Note KPIs — receiving-now / received-today / MTD / YTD counts, tabbed pending PO by day-band, overdue PO with critical highlight, incomplete and over-received GRN tables, plus top vendors and category spend.
published: true
date: 2026-05-19T23:55:00.000Z
tags: dashboard, good-receive-note, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# GRN Dashboard

> **At a Glance**
> **Route:** `/dashboard/grn` &nbsp;·&nbsp; **For:** Receiver &nbsp;·&nbsp; Inventory Controller &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; **Status:** **Mock-data today**; live wiring pending

![GRN Dashboard screen](/screenshots/dashboard/grn.png)

## 1. What & Who

Receiver's operations board. Answers *"what's hitting the dock today, what's late, and where are receipts disagreeing with the order?"*

**Layout:** 4 KPI cards (top: Receiving Now / Received Today / MTD / YTD) → 2×2 grid of tables (Pending PO by day-band, Overdue PO, Incomplete GRNs, Over-Received GRNs) → 2 YTD spend charts (bottom).

The Pending PO block is interactive — a 3-button tab strip (TODAY / THIS WEEK / NEXT WEEK) swaps the table client-side without navigation.

**Audience**

- **Receiver / Dock Operator** — primary. Watches Pending PO tabs to prep the day, Overdue PO to escalate, Receiving Now to know who's at the dock.
- **Inventory Controller** — uses Incomplete and Over-Received tables for variance investigation before committing.
- **Procurement Manager** — reviews Top Vendors YTD and Spend by Category for supplier performance.

## 2. Tiles & Drill-downs

| Tile | What it shows | Drill-down (when live) |
|---|---|---|
| **Receiving Now** | Integer count, arrow icon (primary colour) | → [good-receive-note](/en/inventory/good-receive-note) in-progress |
| **Received Today** | Integer count, check icon (success colour) | → [good-receive-note](/en/inventory/good-receive-note) today |
| **GRN Total (MTD)** | Integer count, calendar icon | → [good-receive-note](/en/inventory/good-receive-note) month-to-date |
| **GRN Total (YTD)** | Formatted number, package icon | → [good-receive-note](/en/inventory/good-receive-note) year-to-date |
| **Pending Purchase Orders** | Tabs Today / This Week / Next Week — PO, Supplier, Expected Date, Items, Total, Priority (`High` / `Medium` / `Low`) | → [purchase-order](/en/inventory/purchase-order) |
| **Overdue Purchase Orders** | PO, Supplier, Original Due Date, Days Overdue (red `OVERDUE` badge if ≥ 10 days), Items | → [purchase-order](/en/inventory/purchase-order) |
| **Incomplete GRNs (Partial Receipts)** | GRN, PO, Supplier, Qty Ordered, Qty Received, Variance %, "Partially Received" badge | → [good-receive-note](/en/inventory/good-receive-note) |
| **Over-Received GRNs (Excess Receipts)** | GRN (AlertTriangle), PO, Supplier, PO Amount, GRN Amount, Excess, Variance % | → [good-receive-note](/en/inventory/good-receive-note) |
| **Top 5 Vendors by Purchase YTD** | Horizontal bar with `$NM` value labels | → [vendor-pricelist](/en/inventory/vendor-pricelist) |
| **Purchasing Spend by Category** | Grouped vertical bar: Cur Month vs YTD per category | — |

The 10-day threshold (`OVERDUE_THRESHOLD`) is hard-coded in `dashboard-grn.tsx` — production should source from a configurable SLA setting.

## 3. Common Questions

| Question | Answer |
|---|---|
| Why doesn't "Received Today" tick up after I commit a GRN? | **Mock-data today** — counts come from `mock/grn.ts`. Live wiring uses `CACHE_DYNAMIC` (1-min stale) with refetch-on-focus. |
| What classifies a PO as "Overdue" vs "Critical OVERDUE"? | Overdue = `expected_delivery_date < CURRENT_DATE` AND not fully received. Critical badge fires when days-overdue ≥ `OVERDUE_THRESHOLD = 10` (currently hard-coded). |
| How is Variance % computed for partial / over receipts? | Frontend computes from `received_qty` vs `ordered_qty` on each row joined back to its [purchase-order](/en/inventory/purchase-order) line. |
| Where do day-band tabs (Today / This Week / Next Week) get their lists? | [purchase-order](/en/inventory/purchase-order) lines grouped by `expected_delivery_date` bucket where no [good-receive-note](/en/inventory/good-receive-note) line has been committed. |
| Why do YTD totals show in USD millions? | Mock fixture uses `$M`; production localises to BU base currency from [master-data/exchange-rate](/en/inventory/master-data/exchange-rate). |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Receiving Now badge stuck on same number all day | Mock has no real-time tick | Live wiring should refetch on focus and on commit-event hook |
| Overdue threshold not matching SLA policy | `OVERDUE_THRESHOLD = 10` hard-coded in component | File enhancement ticket to source from [system-config/workflow](/en/inventory/system-config/workflow) config |
| Incomplete vs Over-Received GRN both show same row | Mock fixture seeded inconsistently | Live query is mutually exclusive: `received_qty < ordered_qty` vs `received_qty > ordered_qty` |
| Tab switch (Today/This Week/Next Week) doesn't change data | Mock arrays differ but state-binding may regress | Inspect `pendingPoToday` / `pendingPoThisWeek` / `pendingPoNextWeek` |

---

## 5. Data Sources (Dev)

- **KPI cards** — count queries on [good-receive-note](/en/inventory/good-receive-note) filtered by `status` (`in progress` for Receiving Now, `commit_date = today` for Received Today, etc.)
- **Pending PO tabs** — [purchase-order](/en/inventory/purchase-order) lines grouped by `expected_delivery_date` bucket where no [good-receive-note](/en/inventory/good-receive-note) line committed
- **Overdue PO** — [purchase-order](/en/inventory/purchase-order) where `expected_delivery_date < CURRENT_DATE` AND not fully received; days overdue = `CURRENT_DATE - expected_delivery_date`
- **Incomplete / Over-Received GRNs** — join committed [good-receive-note](/en/inventory/good-receive-note) line to PO line; incomplete `received_qty < ordered_qty`, over `received_qty > ordered_qty`; Variance % computed frontend
- **Top Vendors YTD** — sum GRN-line amount grouped by `vendor_id`, top 5
- **Spend by Category** — sum GRN-line amount grouped by [product/category](/en/inventory/product/category), split current month vs YTD

## 6. Refresh Cadence

Static mock today. Once wired: KPI cards and Receiving Now should refetch frequently (dock activity is real-time-ish) — `CACHE_DYNAMIC` (1-min stale) minimum. Top Vendors YTD can use `CACHE_NORMAL` (5-min) since YTD totals change slowly.

## 7. Related Modules

- [good-receive-note](/en/inventory/good-receive-note) — transactional system-of-record
- [purchase-order](/en/inventory/purchase-order) — upstream commitment behind every pending / overdue row
- [inventory](/en/inventory/inventory) — downstream stock impact once GRN commits
- [vendor-pricelist](/en/inventory/vendor-pricelist) — vendor master for the Top Vendors chart
- [costing](/en/inventory/costing) — variance handling for over-received quantities at commit-time costing

## 8. Reference Sources

- **Page shell:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-grn.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-grn.tsx`
- **Mock data:** `../carmen-inventory-frontend-react/routes/dashboard/mock/grn.ts`
- **i18n:** `messages/en.json` → `dashboard.grn.title` = "Goods Receive Note Dashboard"
