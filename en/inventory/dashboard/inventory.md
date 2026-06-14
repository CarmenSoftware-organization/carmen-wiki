---
title: Inventory Dashboard
description: Inventory operations cockpit — status pipeline, slow-moving / replenishment / PST tables filtered by location, value by material group, expired-items alert, and consumption charts by location and category.
published: true
date: 2026-05-19T23:55:00.000Z
tags: dashboard, inventory, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Dashboard

> **At a Glance**
> **Route:** `/dashboard/inventory` &nbsp;·&nbsp; **For:** Inventory Controller &nbsp;·&nbsp; Store Manager &nbsp;·&nbsp; Finance &nbsp;·&nbsp; QA &nbsp;·&nbsp; **Status:** **Mock-data today**; live wiring pending

![Inventory Dashboard screen](/screenshots/dashboard/inventory.png)

## 1. What & Who

Inventory controller's daily board. Answers *"where is stock locked, what's not moving, what needs reordering, and where is consumption running?"*

**Layout:** 5-step status pipeline (top) → left stack of 3 location-filtered tables (Slow-Moving / Replenishment / PST) → right grid of analytics (Value by Material Group / Expired Items / Consumption by Location / Consumption by Category).

Two tables expose a Location tab picker (`Main Store`, `Bar`, `Restaurant`, etc. — see `INVENTORY_LOCATIONS`) so the same widget retargets without navigation.

**Audience**

- **Inventory Controller** — primary. Watches Slow-Moving / Dead Stock, Replenishment, and PST Status.
- **Store Manager** — uses Location tab picker to scope every table; uses "CREATE PR" in Replenishment.
- **Finance Controller** — watches Inventory Value by Material Group as on-hand financial exposure.
- **Compliance / QA** — watches Expired Items Alert.

## 2. Tiles & Drill-downs

| Tile | What it shows | Drill-down (when live) |
|---|---|---|
| **Status Pipeline** | 5 cards: Stock-Take Not Complete (Loc count) / Stock-Take Complete (Loc count) / Uncommitted Docs Curr Mo (Doc count) / Expiring Items Curr Mo (Item count) / Inventory Value (Curr Mo) | → [physical-count](/en/inventory/physical-count) / [inventory](/en/inventory/inventory) |
| **Slow-Moving / Dead Stock** | Item, SKU, Location, Days No Movement, Est. Value (with Location tabs) | → [inventory](/en/inventory/inventory) item detail |
| **Inventory Replenishment (Below Par)** | Item, SKU, Location, On Hand, Par, Max, Order Qty + two "CREATE PR" buttons (Location tabs) | → [purchase-request](/en/inventory/purchase-request) new with prefilled items |
| **Physical Stock Take Status** | Location, Dept, Last Count Date, PST Status badge (`Completed` / `Awaiting Approval` / `In Progress`), SVF Name | → [physical-count](/en/inventory/physical-count) |
| **Inventory Value by Material Group** | Donut + bar + legend: Food / Beverage / Supplies with percent + `$K` | — |
| **Expired Items Alert** | Item (XCircle), Expiry Date | → [inventory](/en/inventory/inventory) lot/expiry |
| **Total Consumption by Location** | Horizontal bar with Cur Mo vs YTD amounts | — |
| **Total Consumption by Category** | Horizontal bar + SR Awaiting Receipt callout listing SR# with "Details" link | → [store-requisition](/en/inventory/store-requisition) for SR# rows |

The Replenishment table renders **two "CREATE PR" buttons** side-by-side with different styling — likely placeholders for two PR templates (e.g., normal vs. urgent). **(Inferred — to be verified against live UI)**

## 3. Common Questions

| Question | Answer |
|---|---|
| Why doesn't the Location tab filter all tables at once? | Each table owns its own Location state; tab picker only retargets that one widget. |
| What's the threshold for "Slow-Moving"? | Configurable threshold against last-movement date — currently mock; no central config surface today. |
| How is "Order Qty" suggested in Replenishment? | `max_level - on_hand` (or per [store-requisition/stock-replenishment](/en/inventory/store-requisition/stock-replenishment) policy). |
| Does "CREATE PR" actually create the PR? | **Inferred — to be verified against live UI.** Mock has no handler. Live wiring should pre-fill a new [purchase-request](/en/inventory/purchase-request) with the line items. |
| How is Inventory Value calculated? | `on_hand × unit_cost` grouped by [product/category](/en/inventory/product/category) root; `unit_cost` comes from [costing](/en/inventory/costing). |
| What triggers the Expired Items Alert? | [inventory](/en/inventory/inventory) lot table where `expiry_date ≤ CURRENT_DATE + N_days` (N configurable). |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Switching Location tab shows same rows | Mock fixture not partitioned by location | Live query filters on `location_id` |
| "CREATE PR" click does nothing | No handler wired in current build | (Inferred — to be verified against live UI) |
| PST Status badge missing for a known count | Mock has finite rows; live data uses latest count per location | Verify against [physical-count](/en/inventory/physical-count) header records |
| Expired Items list empty though items have expired | Mock fixture seeded with few rows | Live query reads [inventory](/en/inventory/inventory) lot table with expiry filter |
| Inventory Value chart shows `$K` not `฿K` | Mock fixture currency quirk | Production localises to BU base currency |

---

## 5. Data Sources (Dev)

- **Status Pipeline** — counts from [physical-count](/en/inventory/physical-count) (locations not committed for period), [inventory](/en/inventory/inventory) aggregate (uncommitted docs this month), [inventory](/en/inventory/inventory) lot table (expiring within month), inventory-value rollup
- **Slow-Moving / Dead Stock** — [inventory](/en/inventory/inventory) item-location balances joined to last-movement date; threshold configurable
- **Replenishment** — items where `on_hand < par_level`; order qty = `max_level - on_hand` (or per [store-requisition/stock-replenishment](/en/inventory/store-requisition/stock-replenishment))
- **PST Status** — [physical-count](/en/inventory/physical-count) header records, latest count per location; workflow stage projects to 3 badge variants
- **Inventory Value by Material Group** — sum `on_hand × unit_cost` grouped by [product/category](/en/inventory/product/category) root
- **Expired Items Alert** — [inventory](/en/inventory/inventory) lot where `expiry_date ≤ CURRENT_DATE + N_days`
- **Consumption by Location / Category** — sum committed [inventory](/en/inventory/inventory) outbound movements (SR-issued, wastage, recipe) grouped by location / category
- **SR Awaiting Receipt** — [store-requisition](/en/inventory/store-requisition) where `status = "issued"` AND destination location not yet committed receipt

## 6. Refresh Cadence

Static mock today. Once wired: Status Pipeline and value rollups → `CACHE_NORMAL` (5-min). Replenishment and PST Status → `CACHE_DYNAMIC` (1-min, operators act in real time). Consumption charts → `CACHE_NORMAL` (aggregate over month / YTD).

## 7. Related Modules

- [inventory](/en/inventory/inventory) — transactional balances and movements behind every tile
- [inventory-adjustment](/en/inventory/inventory-adjustment) — variance posting after PST
- [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check) — count operations driving PST Status
- [store-requisition](/en/inventory/store-requisition) — outbound issues feeding Consumption + SR Awaiting Receipt
- [purchase-request](/en/inventory/purchase-request) — target of "CREATE PR" replenishment buttons
- [costing](/en/inventory/costing) — supplies `unit_cost` for the inventory-value donut

## 8. Reference Sources

- **Page shell:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-inventory.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-inventory.tsx`
- **Mock data:** `../carmen-inventory-frontend-react/routes/dashboard/mock/inventory.ts` (includes `INVENTORY_LOCATIONS`)
- **i18n:** `messages/en.json` → `dashboard.inventory.title` = "Inventory Dashboard"
