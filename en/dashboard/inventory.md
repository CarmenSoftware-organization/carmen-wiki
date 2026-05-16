---
title: Inventory Dashboard
description: Inventory operations cockpit — status pipeline, slow-moving / replenishment / PST tables filtered by location, value by material group, expired-items alert, and consumption charts by location and category.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, inventory, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Inventory Dashboard

## 1. Purpose

Inventory Dashboard at `/dashboard/inventory` is the inventory controller's daily board. It answers *"where is stock locked, what's not moving, what needs reordering, and where is consumption running?"* The page opens with a five-step status pipeline strip, follows with a left-side stack of three location-filtered tables (Slow-Moving / Dead Stock, Replenishment, PST Status), and a right-side grid of analytics cards (Inventory Value by Material Group, Expired Items Alert, Consumption by Location, Consumption by Category).

Two of the tables expose a Location tab picker (`Main Store`, `Bar`, `Restaurant`, etc. — see `INVENTORY_LOCATIONS`) so the same widget retargets without a navigation.

## 2. Tiles / Widgets

| Tile | Type | What it shows | Drill-down | Data source (current) |
|---|---|---|---|---|
| Status Pipeline | Five-card strip with arrow connectors | Location count (Stock-Take Not Complete), Location count (Stock-Take Complete), Doc count (Uncommitted Docs Curr Mo), Item count (Expiring Items Curr Mo), Inventory Value (Curr Mo) | (Inferred) → [[physical-count]] / [[inventory]] | `mock/inventory.ts` → `inventoryPipeline` |
| Slow-Moving / Dead Stock | Table + Location tabs | Item Name, SKU, Location, Days No Movement, Est. Value | (Inferred) → [[inventory]] item detail | `mock/inventory.ts` → `slowMovingItems` |
| Inventory Replenishment (Below Par) | Table + Location tabs + Create-PR buttons | Item Name, SKU, Location, On Hand, Par Level, Max Level, Order Qty; "CREATE PR" actions | (Inferred) → [[purchase-request]] new with prefilled items | `mock/inventory.ts` → `replenishmentItems` |
| Physical Stock Take Status | Table | Location, Dept, Last Count Date, PST Status badge (`Completed` / `Awaiting Approval` / `In Progress`), SVF Name | (Inferred) → [[physical-count]] | `mock/inventory.ts` → `pstRecords` |
| Inventory Value by Material Group | Donut + adjacent bar chart + legend | Three groups (Food / Beverage / Supplies) with percent and `$K` amounts | — | `mock/inventory.ts` → `inventoryByMaterialGroup` |
| Expired Items Alert (Lot/Exp Master) | Table | Item Name (XCircle icon), Expiry Date | (Inferred) → [[inventory]] lot/expiry | `mock/inventory.ts` → `expiredItems` |
| Total Consumption by Location (Cur MO vs YTD) | Horizontal bar chart | Location + amount labels | — | `mock/inventory.ts` → `consumptionByLocation` |
| Total Consumption by Category | Horizontal bar chart + SR Awaiting Receipt callout | Category + amount labels; small bar above lists SR# awaiting receipt with "Details" link | (Inferred) → [[store-requisition]] for SR# rows | `mock/inventory.ts` → `consumptionByCategory`, `srAwaitingReceipt` |

The Replenishment table has two "CREATE PR" buttons rendered side-by-side with different styling — likely placeholders for two PR templates (e.g., normal PR vs. urgent PR). Mark this **(Inferred — to be verified against live UI)**.

## 3. Data Sources

Currently mocked. Expected live mapping:

- Status Pipeline — counts derived from [[physical-count]] (locations not yet committed for the period), [[inventory]] aggregate (uncommitted documents this month), [[inventory]] lot table filtered by expiry within the month, and the rolling inventory-value rollup.
- Slow-Moving / Dead Stock — query against [[inventory]] item-location balances joined to last-movement date; threshold for "slow" is configurable.
- Replenishment — items where `on_hand < par_level`; order qty suggestion = `max_level - on_hand` (or per [[store-requisition/stock-replenishment]] policy).
- PST Status — [[physical-count]] header records filtered to the latest count per location, with the workflow stage projecting to one of the three badge variants.
- Inventory Value by Material Group — sum on `on_hand × unit_cost` grouped by [[master-data/product-category]] root.
- Expired Items Alert — [[inventory]] lot table where `expiry_date ≤ CURRENT_DATE + N_days` (N configurable).
- Consumption by Location / Category — sum on committed [[inventory]] outbound movements (SR-issued, wastage, recipe consumption) grouped by location and category.
- SR Awaiting Receipt — [[store-requisition]] rows where `status = "issued"` and the destination location has not yet committed receipt.

## 4. Refresh Cadence

Static mock today. Once wired:

- Status Pipeline and the value rollups can use `CACHE_NORMAL` (5-minute stale) — they roll up slowly.
- Replenishment and PST Status should be `CACHE_DYNAMIC` (1-minute) — operators take action against these tables in real time.
- Consumption charts can be `CACHE_NORMAL` since they aggregate over the month / YTD.

## 5. Audience & Persona

- **Inventory Controller** — primary. Watches Slow-Moving / Dead Stock to prune dead inventory, Replenishment to keep par levels healthy, and PST Status to chase outstanding counts.
- **Store Manager** — uses the Location tab picker to scope every table to their store, and uses the "CREATE PR" buttons in Replenishment to raise new requests.
- **Finance Controller** — watches Inventory Value by Material Group as the on-hand financial exposure.
- **Compliance / QA** — watches the Expired Items Alert.

## 6. Related Modules

- [[inventory]] — transactional balances and movements behind every tile
- [[inventory-adjustment]] — variance posting after PST
- [[physical-count]], [[spot-check]] — count operations that drive the PST Status table
- [[store-requisition]] — outbound issues feeding Consumption charts and the SR Awaiting Receipt callout
- [[purchase-request]] — target of the "CREATE PR" replenishment buttons
- [[costing]] — supplies the `unit_cost` for the inventory-value donut

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/inventory/page.tsx` — page shell
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-inventory.tsx` — `DashboardInventory` composition (pipeline, slow-moving, replenishment, PST, value chart, expired alert, consumption charts)
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/inventory.ts` — fixture data including `INVENTORY_LOCATIONS`
- `../carmen-inventory-frontend/messages/en.json` → `dashboard.inventory.title` = "Inventory Dashboard"
