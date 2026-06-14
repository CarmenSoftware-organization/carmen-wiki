---
title: Costing
description: Inventory valuation methods (FIFO, Weighted Average) and the costing engine that calculates COGS and ending inventory value.
published: true
date: 2026-05-19T23:55:00.000Z
tags: costing, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Costing

> **At a Glance**
> **Module purpose:** Per-transaction valuation engine that computes COGS on outgoing stock and updates cost basis on incoming stock under FIFO or Weighted Average &nbsp;·&nbsp; **Audience:** Finance, Inventory Controller, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_period_snapshot`, FIFO cost layers, `AverageCostTracking`, `JournalEntry`, [costing/calculation-methods](/en/inventory/costing/calculation-methods) &nbsp;·&nbsp; **Sub-pages:** 11

## 1. Overview

The Costing module is the valuation engine of the inventory ERP. It consumes the stream of stock movements produced by the Inventory module and, for every outgoing transaction, computes the **Cost of Goods Sold (COGS)** charged to a department or revenue centre; for every incoming transaction, it updates the **cost basis** of the affected balance. The engine runs per-transaction rather than as a periodic batch — a GRN line that posts at 14:02 is costed at 14:02, so balances and valuation stay in step with quantities.

Two cost-flow assumptions are supported, configurable per product (or globally): **FIFO**, which preserves each receipt as a distinct lot and consumes the oldest lot first, and **Weighted Average Cost (WAC)**, which blends every receipt into a single rolling average. The engine exposes the same inputs and outputs in both cases — a costed quantity, a unit cost, a journal entry, and a refreshed balance valuation — so downstream consumers (recipe costing, financial reporting, variance analysis) do not need to know which method a given product uses.

Outputs land in three places: stock balances carry an up-to-date `currentCost` and `totalValue`; outgoing movements (`ISSUE`, `WRITE_OFF`, `TRANSFER` from an inventory location) carry the realised COGS that feeds the GL; and the period-end snapshot locks the valuation that the balance sheet and food-cost reports consume. Detailed FIFO vs. WAC algorithms, numerical examples, and the trade-offs between the two methods are covered in the sub-page below — this landing page only orients.

## 2. Business Context

Inventory valuation is a regulated activity. Both **IFRS** (IAS 2) and **US GAAP** (ASC 330) accept FIFO and Weighted Average as permissible cost-flow assumptions, but they require the choice to be applied consistently per product class and disclosed in the financial statements. The costing module is therefore an audit-facing component: every COGS figure must be traceable back to a specific receipt (FIFO) or a specific moving-average computation (WAC), and the trail has to survive an external audit cycle.

Operationally, costing is where **food cost control** lives. Plate cost, recipe profitability, and menu-engineering decisions all read from this module. If the costing engine drifts — stale lots, missed waste write-offs, incorrect average recomputation after a return — every downstream margin number drifts with it. Hospitality groups typically run on tight food-cost margins, so a one-or-two-percentage-point error in valuation translates directly into a noticeable P&L miss. This module is the contract between physical inventory movements and the financial picture the business steers by.

## 3. Key Concepts

- **COGS (Cost of Goods Sold)**: The cost charged to expense when inventory leaves an inventory-type location for consumption (issue to a kitchen, write-off, sale through a POS-linked recipe). Calculated by the costing engine at the moment of the movement, posted as a debit to the consuming cost centre and a credit to the inventory asset account.
- **Ending Inventory Value**: The monetary value of stock still on hand at a point in time — quantity multiplied by the unit cost determined by the active costing method. Locked into the period-end snapshot and reported on the balance sheet. Equal to opening value plus receipts minus COGS minus adjustments.
- **FIFO (First-In, First-Out)**: A cost-flow assumption under which the oldest receipts are consumed first. Each receipt becomes a discrete **lot** with its own unit cost; the engine consumes lots in order until the issued quantity is satisfied, so older costs flow to COGS while newer costs remain in ending inventory.
- **Weighted Average Cost (WAC)**: A cost-flow assumption under which every receipt is blended into a single moving-average unit cost. The average is recomputed on every receipt as `(prevQty × prevAvg + receivedQty × receivedCost) / (prevQty + receivedQty)`. Issues are costed at the average prevailing at the time of issue; ending inventory and COGS both reflect the same blended cost.
- **Lot/Batch**: An identifiable group of stock from a single receipt, carrying its own quantity, receipt date, and unit cost. Required for FIFO (the engine consumes lots in receipt order) and also used independently for expiry tracking and product traceability.
- **Cost Basis**: The unit cost the engine assigns to a balance for valuation and downstream costing. Under FIFO, it is per-lot; under WAC, it is the current moving average for the product at the location. Every adjustment, return, or recipe consumption requires a cost basis from this module — the engine is the single source of truth for "what did this unit cost?".

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Finance | Owns the valuation policy: chooses FIFO or WAC per product class, reconciles inventory sub-ledger to the GL, signs off period-end valuation. |
| Inventory Controller | Ensures the inputs the engine relies on are clean: lot dates, receipt costs, adjustment cost bases, waste write-offs. Investigates valuation variances. |
| Auditor | Verifies that the costed COGS and ending inventory tie back to source receipts and that the costing method is applied consistently across periods. |

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — costing operates on inventory movements; every IN/OUT triggers a costing calculation
- [good-receive-note](/en/inventory/good-receive-note) — GRN receipts set unit costs (FIFO) or update averages (WAC)
- [recipe](/en/inventory/recipe) — recipe consumption uses costed quantities to derive food cost
- [inventory-adjustment](/en/inventory/inventory-adjustment) — adjustments require a cost basis from the costing engine

**Master configuration:**
- [master-data/business-unit](/en/inventory/master-data/business-unit) — tenant/property scope for the valuation ledger
- [master-data/currency](/en/inventory/master-data/currency) — transaction and base currencies plus FX rates for dual-posted COGS
- [master-data/unit](/en/inventory/master-data/unit) — base unit conversion required to value any costed line
- [system-config/period](/en/inventory/system-config/period) — accounting period that gates costing posting and locks valuation
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — costing recalculation and posting activity log for audit

## 6. Reference Sources

- Concepts: `../carmen/docs/costing/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/costing/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](/en/inventory/costing/02-business-rules) — Validation, calculation, authorization, posting, and cross-module rules.
- [03 — User Flow](/en/inventory/costing/03-user-flow) — Document lifecycle and persona index.
  - [Finance](/en/inventory/costing/03-user-flow-finance)
  - [Inventory Controller](/en/inventory/costing/03-user-flow-inventory-controller)
  - [Auditor](/en/inventory/costing/03-user-flow-auditor)
- [04 — Test Scenarios](/en/inventory/costing/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Finance](/en/inventory/costing/04-test-scenarios-finance)
  - [Inventory Controller](/en/inventory/costing/04-test-scenarios-inventory-controller)
  - [Auditor](/en/inventory/costing/04-test-scenarios-auditor)
- [Inventory Costing Methods: FIFO vs. Weighted Average](/en/inventory/costing/calculation-methods) — Method comparison and algorithms.
