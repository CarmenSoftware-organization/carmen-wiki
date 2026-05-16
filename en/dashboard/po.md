---
title: PO Dashboard
description: Purchase Order summary tiles — six-stage pipeline, pending PRs and overdue deliveries, on-time / completeness gauges, category spend, top vendors, and over-received variance flagging.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, purchase-order, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# PO Dashboard

## 1. Purpose

PO Dashboard at `/dashboard/po` is the purchaser's cockpit. It answers *"which POs are in flight, which are slipping, and where am I exposed?"* The page leads with a six-tile pipeline strip across the top, follows with two action tables (Pending PRs for PO creation, Overdue Deliveries) on the left and a stack of KPI gauges + spend visualisations on the right, then closes with a full-width Over-Received POs table that flags receipts exceeding the order quantity.

Two KPI gauges (semicircular) call out the most-watched purchasing metrics: On-Time Delivery % and Order Completeness %.

## 2. Tiles / Widgets

| Tile | Type | What it shows | Drill-down | Data source (current) |
|---|---|---|---|---|
| PO Pipeline | Six-card grid | Stages: Not Sent, Sent, Partial, Closed, Completed, Rejected — each with icon, count, and progress bar | (Inferred) → [[purchase-order]] filtered by status | `mock/po.ts` → `poPipelineSummary` |
| Pending PRs for PO Creation | Table | PR ID, Requester, Dept, Date Approved, status badge (`Pending PO` / `Hold for Info` / `Overdue Follow-up`) | (Inferred) → [[purchase-request]] | `mock/po.ts` → `pendingPrsForPo` |
| Overdue Deliveries List | Table | PO ID, Vendor, Dept, Due Date, "N days overdue" in destructive colour | (Inferred) → [[purchase-order]] | `mock/po.ts` → `overdueDeliveries` |
| On-Time Delivery | Gauge (semicircle) | Single percent (0-100), warning colour | — | `mock/po.ts` → `poKpi.onTimeDelivery` |
| Order Completeness | Gauge (semicircle) | Single percent (0-100), success colour | — | `mock/po.ts` → `poKpi.orderCompleteness` |
| Category Spend (Cur Mo vs YTD) | Donut + legend with two amounts per row | Categories with current-month and YTD amount | — | `mock/po.ts` → `categorySpend` |
| Top 5 Vendors by Spend | Horizontal bar chart | Vendor name + amount labels | (Inferred) → [[vendor-pricelist]] | `mock/po.ts` → `topVendorsBySpend` |
| Delivery Schedule | Three stat cards | Today / This Week / Next Week delivery counts (success / primary / destructive tints) | (Inferred) → [[good-receive-note]] today's expected | `mock/po.ts` → `deliverySchedule` |
| Over-Received POs (Received > Ordered) | Table | PO Number, Material Name, Material Code, Vendor, Ordered Qty, Received Qty, Variance (`+N`), "Variance Flagged" badge | (Inferred) → [[good-receive-note]] | `mock/po.ts` → `overReceivedPos` |

Currency labels render as USD (`$`) in the current mock — production should localise to BU base currency.

## 3. Data Sources

Currently mocked. Expected live mapping:

- Pipeline buckets — group-count on [[purchase-order]] by `status` (mapped to the six PoPipelineKey values).
- Pending PRs for PO — [[purchase-request]] where `workflow_current_stage = "approved"` and `po_id IS NULL`, augmented with the SLA-based status badge (`Pending PO` < N days, `Overdue Follow-up` ≥ N days).
- Overdue Deliveries — [[purchase-order]] lines where `expected_delivery_date < CURRENT_DATE` and not fully received against [[good-receive-note]].
- On-Time Delivery / Order Completeness — period KPIs computed by [[reporting-audit]] over committed GRNs against PO expected dates and quantities.
- Category Spend — sum on PO line amount grouped by [[master-data/product-category]], split current-month vs YTD.
- Top Vendors — sum on PO total amount grouped by `vendor_id`, top 5.
- Delivery Schedule — count of PO lines where `expected_delivery_date` falls in today / this week / next week.
- Over-Received POs — join of [[purchase-order]] line to committed [[good-receive-note]] lines where `received_qty > ordered_qty`.

## 4. Refresh Cadence

Static mock today. Live wiring will inherit `CACHE_DYNAMIC` (1-min stale time) from the proxy hooks. The Overdue Deliveries and Over-Received tables are time-sensitive — testers should verify they recompute on tab focus once wired.

## 5. Audience & Persona

- **Purchaser** — primary. Triages Pending PRs (to issue new POs), chases Overdue Deliveries, and watches On-Time % as a personal KPI.
- **Procurement Manager** — uses Top Vendors and Category Spend for supplier-mix reviews; watches Over-Received variance for control breaches.
- **Receiver** — glances at Delivery Schedule (Today / This Week / Next Week) to prep dock staffing.

## 6. Related Modules

- [[purchase-order]] — transactional system-of-record
- [[purchase-request]] — upstream feed for Pending PRs for PO Creation
- [[good-receive-note]] — downstream receipts that drive On-Time, Completeness, and Over-Received tiles
- [[vendor-pricelist]] — vendor master behind the Top Vendors bar
- [[reporting-audit]] — query datasets for the KPI gauges

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/po/page.tsx` — page shell
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-po.tsx` — `DashboardPo` composition (pipeline, pending PRs, overdue, gauges, category spend, top vendors, delivery schedule, over-received)
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/po.ts` — fixture data
- `../carmen-inventory-frontend/messages/en.json` → `dashboard.po.title` = "Purchase Order Dashboard"
