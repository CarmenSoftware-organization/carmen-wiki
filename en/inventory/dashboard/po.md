---
title: PO Dashboard
description: Purchase Order summary tiles — six-stage pipeline, pending PRs and overdue deliveries, on-time / completeness gauges, category spend, top vendors, and over-received variance flagging.
published: true
date: 2026-05-19T23:55:00.000Z
tags: dashboard, purchase-order, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# PO Dashboard

> **At a Glance**
> **Route:** `/dashboard/po` &nbsp;·&nbsp; **For:** Purchaser &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; Receiver &nbsp;·&nbsp; **Status:** **Mock-data today**; live wiring pending

![PO Dashboard screen](/screenshots/dashboard/po.png)

## 1. What & Who

Purchaser's cockpit. Answers *"which POs are in flight, which are slipping, and where am I exposed?"*

**Layout:** Six-tile pipeline strip (top) → action tables Pending PRs / Overdue Deliveries (left) + KPI gauges + spend visualisations (right) → full-width Over-Received POs table (bottom).

Two semicircular gauges call out the watched purchasing metrics: **On-Time Delivery %** and **Order Completeness %**.

**Audience**

- **Purchaser** — primary. Triages Pending PRs (to issue new POs), chases Overdue Deliveries, watches On-Time %.
- **Procurement Manager** — uses Top Vendors and Category Spend for supplier-mix reviews; watches Over-Received variance.
- **Receiver** — glances at Delivery Schedule (Today / This Week / Next Week) to prep dock staffing.

## 2. Tiles & Drill-downs

| Tile | What it shows | Drill-down (when live) |
|---|---|---|
| **PO Pipeline** | 6 stages: Not Sent / Sent / Partial / Closed / Completed / Rejected — count + progress bar | → [purchase-order](/en/inventory/purchase-order) filtered by status |
| **Pending PRs for PO Creation** | PR ID, Requester, Dept, Date Approved, badge (`Pending PO` / `Hold for Info` / `Overdue Follow-up`) | → [purchase-request](/en/inventory/purchase-request) |
| **Overdue Deliveries** | PO ID, Vendor, Dept, Due Date, "N days overdue" (destructive colour) | → [purchase-order](/en/inventory/purchase-order) |
| **On-Time Delivery** | Semicircle gauge, percent (warning colour) | — |
| **Order Completeness** | Semicircle gauge, percent (success colour) | — |
| **Category Spend (Cur Mo vs YTD)** | Donut + legend with two amounts per row | — |
| **Top 5 Vendors by Spend** | Horizontal bar + amount labels | → [vendor-pricelist](/en/inventory/vendor-pricelist) |
| **Delivery Schedule** | 3 stat cards: Today / This Week / Next Week counts | → [good-receive-note](/en/inventory/good-receive-note) today's expected |
| **Over-Received POs** | PO #, Material, Code, Vendor, Ordered, Received, Variance `+N`, "Variance Flagged" badge | → [good-receive-note](/en/inventory/good-receive-note) |

Currency renders as `$` in the mock — production should localise to BU base currency.

## 3. Common Questions

| Question | Answer |
|---|---|
| Why are the gauges static? | **Mock-data today** — On-Time / Completeness will resolve to query-dataset reports from [reporting-audit](/en/inventory/reporting-audit). |
| Which PRs surface in "Pending PRs for PO Creation"? | [purchase-request](/en/inventory/purchase-request) where `workflow_current_stage = "approved"` AND `po_id IS NULL`. SLA threshold drives the badge variant. |
| What flags a PO as "Overdue"? | `expected_delivery_date < CURRENT_DATE` AND not fully received against [good-receive-note](/en/inventory/good-receive-note). |
| Where does Over-Received variance get reconciled? | Join PO line → committed GRN line where `received_qty > ordered_qty`; see [costing](/en/inventory/costing) for variance posting. |
| Why is `$` showing not `฿`? | Mock fixture quirk; production localises to BU base currency. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Gauges show identical % for every BU | Mock fixture seeds the same `poKpi.onTimeDelivery` / `orderCompleteness` everywhere | Inspect `mock/po.ts` — values are static |
| Delivery Schedule "Today" empty on a known delivery day | Mock has no today-aware filter | Live wiring filters on `expected_delivery_date` against `CURRENT_DATE` |
| Over-Received row disappeared after page reload | Mock arrays are re-imported per render — stable today; not stable when live | Verify against [good-receive-note](/en/inventory/good-receive-note) commit log once wired |
| Top Vendors bar shows duplicate vendor names | Mock fixture quirk — `vendor_id` not de-duped | Live query groups by `vendor_id` and joins [vendor-pricelist](/en/inventory/vendor-pricelist) |

---

## 5. Data Sources (Dev)

- **Pipeline buckets** — group-count on [purchase-order](/en/inventory/purchase-order) by `status` → 6 `PoPipelineKey` values
- **Pending PRs for PO** — [purchase-request](/en/inventory/purchase-request) where `workflow_current_stage = "approved"` AND `po_id IS NULL`; SLA-based badge (`Pending PO` < N days, `Overdue Follow-up` ≥ N days)
- **Overdue Deliveries** — [purchase-order](/en/inventory/purchase-order) lines where `expected_delivery_date < CURRENT_DATE` AND not fully received against [good-receive-note](/en/inventory/good-receive-note)
- **On-Time Delivery / Order Completeness** — period KPIs by [reporting-audit](/en/inventory/reporting-audit) over committed GRNs against PO expected dates/quantities
- **Category Spend** — sum PO-line amount grouped by [product/category](/en/inventory/product/category), current-month vs YTD
- **Top Vendors** — sum PO total grouped by `vendor_id`, top 5
- **Delivery Schedule** — count PO lines where `expected_delivery_date` falls in today / this week / next week
- **Over-Received POs** — join [purchase-order](/en/inventory/purchase-order) line to committed [good-receive-note](/en/inventory/good-receive-note) line where `received_qty > ordered_qty`

## 6. Refresh Cadence

Static mock today. Live wiring inherits `CACHE_DYNAMIC` (1-min stale) from proxy hooks. Overdue Deliveries and Over-Received are time-sensitive — testers should verify recompute on tab focus once wired.

## 7. Related Modules

- [purchase-order](/en/inventory/purchase-order) — transactional system-of-record
- [purchase-request](/en/inventory/purchase-request) — upstream feed for Pending PRs for PO Creation
- [good-receive-note](/en/inventory/good-receive-note) — downstream receipts driving On-Time, Completeness, Over-Received
- [vendor-pricelist](/en/inventory/vendor-pricelist) — vendor master behind the Top Vendors bar
- [reporting-audit](/en/inventory/reporting-audit) — query datasets for the KPI gauges
- [costing](/en/inventory/costing) — variance handling for over-received quantities

## 8. Reference Sources

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/po/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-po.tsx`
- **Mock data:** `../carmen-inventory-frontend/app/(root)/dashboard/mock/po.ts`
- **i18n:** `messages/en.json` → `dashboard.po.title` = "Purchase Order Dashboard"
