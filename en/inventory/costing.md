---
title: Costing
description: Inventory valuation methods (FIFO, Weighted Average) and the costing engine that calculates COGS and ending inventory value.
published: true
date: 2026-07-22T11:30:00.000Z
tags: costing, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Costing

> **At a Glance**
> **Module purpose:** Per-transaction valuation engine that picks `cost_per_unit` for every outbound stock movement and refreshes `average_cost_per_unit` for every inbound, under a single FIFO-or-Average method set **per business unit** &nbsp;·&nbsp; **Audience:** developers/testers working on inventory valuation — the module has no distinct in-app persona, just the generic `inventory_management.*` permission gates &nbsp;·&nbsp; **Key entities/tables:** `tb_inventory_transaction_cost_layer` (the cost-flow ledger), `tb_period_snapshot` (average-method periods only), `tb_business_unit.calculation_method`, [costing/calculation-methods](/en/inventory/costing/calculation-methods) &nbsp;·&nbsp; **Sub-pages:** 11

## 1. Overview

The Costing module is the valuation engine of the inventory ERP. It consumes the stream of stock movements produced by the Inventory module and, for every outgoing transaction, picks the **Cost of Goods Sold (COGS)** unit cost; for every incoming transaction, it writes the cost basis of the new stock and (under Weighted Average) refreshes the running average. The engine runs per-transaction rather than as a periodic batch — a GRN commit writes the inbound cost-layer row inside the same call that posts the GRN, so balances and valuation stay in step with quantities.

Two cost-flow assumptions are supported: **FIFO**, which preserves each receipt as a distinct lot (`tb_inventory_transaction_cost_layer`, ordered by `lot_seq_no`) and consumes the oldest lot first, and **Weighted Average Cost (WAC)**, which blends every receipt into a single rolling average (`average_cost_per_unit`) per `(location_id, product_id)`. The method is **not** configurable per product or per category — it is a single `tb_business_unit.calculation_method` value (platform schema, `average` | `fifo`, default `average`) that applies to every product at that business unit; `InventoryTransactionService.getCalculationMethod(bu_code)` reads it once and applies it uniformly. There is no code path that mixes FIFO and Average within one business unit, and no in-app screen to change it — it is a platform/cluster-admin field on the business unit record, outside this module's own routes. See [01-data-model](/en/inventory/costing/01-data-model) § 5 for the full divergence from earlier per-product framing.

Outputs land in two places: the cost-layer row itself carries the picked `cost_per_unit` / `average_cost_per_unit` for every consumer (recipe costing, stock-card reports, variance analysis) to read; and, at period close, `tb_period_snapshot` locks the period's opening/receipt/issue/adjustment/closing cost columns — but **only when the business unit's method is `average`**. The FIFO close path carries lot balances forward as `close_period`/`open_period` cost-layer rows instead and does not write `tb_period_snapshot` at all (`processCloseTransactions` in `period-end.close-transaction.helper.ts`). There is no journal-entry or general-ledger posting anywhere in the backend — no `Dr`/`Cr` fan-out, no GL control account, no inventory-to-GL reconciliation code exists for this module (mirrors the identical finding already confirmed on [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 1). Detailed FIFO vs. WAC algorithms, numerical examples, and the trade-offs between the two methods are covered in the sub-page below — this landing page only orients.

## 2. Business Context

Inventory valuation is a regulated activity. Both **IFRS** (IAS 2) and **US GAAP** (ASC 330) accept FIFO and Weighted Average as permissible cost-flow assumptions, but they require the choice to be applied consistently per product class and disclosed in the financial statements. The costing module is therefore an audit-facing component: every COGS figure must be traceable back to a specific receipt (FIFO) or a specific moving-average computation (WAC), and the trail has to survive an external audit cycle.

Operationally, costing is where **food cost control** lives. Plate cost, recipe profitability, and menu-engineering decisions all read from this module. If the costing engine drifts — stale lots, missed waste write-offs, incorrect average recomputation after a return — every downstream margin number drifts with it. Hospitality groups typically run on tight food-cost margins, so a one-or-two-percentage-point error in valuation translates directly into a noticeable P&L miss. This module is the contract between physical inventory movements and the financial picture the business steers by.

## 3. Key Concepts

- **COGS (Cost of Goods Sold)**: The cost picked when inventory leaves an inventory-type location for consumption (issue to a kitchen, write-off, sale through a POS-linked recipe). Written by the costing engine onto the outbound `tb_inventory_transaction_cost_layer` row at the moment of the movement. There is no journal-entry / general-ledger posting anywhere in the backend — the cost-layer row itself is the only durable record of the movement's cost.
- **Ending Inventory Value**: The monetary value of stock still on hand at a point in time — quantity multiplied by the unit cost determined by the active costing method. On **average-method** business units this is locked into `tb_period_snapshot` at period close; on **FIFO-method** business units it is derived from the residual cost-layer lots carried forward as `open_period` rows (no snapshot row is written).
- **FIFO (First-In, First-Out)**: A cost-flow assumption under which the oldest receipts are consumed first. Each receipt becomes a discrete **lot** with its own unit cost; the engine consumes lots in order until the issued quantity is satisfied, so older costs flow to COGS while newer costs remain in ending inventory.
- **Weighted Average Cost (WAC)**: A cost-flow assumption under which every receipt is blended into a single moving-average unit cost. The average is recomputed on every receipt as `(prevQty × prevAvg + receivedQty × receivedCost) / (prevQty + receivedQty)`. Issues are costed at the average prevailing at the time of issue; ending inventory and COGS both reflect the same blended cost.
- **Lot/Batch**: An identifiable group of stock from a single receipt, carrying its own quantity, receipt date, and unit cost. Required for FIFO (the engine consumes lots in receipt order) and also used independently for expiry tracking and product traceability.
- **Cost Basis**: The unit cost the engine assigns to a balance for valuation and downstream costing. Under FIFO, it is per-lot; under WAC, it is the current moving average for the product at the location. Every adjustment, return, or recipe consumption requires a cost basis from this module — the engine is the single source of truth for "what did this unit cost?".

## 4. Roles and Personas

**Correction (verified 2026-07-22):** earlier drafts of this module documented three distinct RBAC personas (Finance, Inventory Controller, Auditor) with dedicated approval queues, a valuation-policy console, a sub-ledger ↔ GL reconciliation dashboard, and a read-only audit workspace. None of that exists in the product. The engine itself has no persona-gated screen at all — it is a service invoked from GRN commit, store-requisition issue, inventory-adjustment, credit-note, and period-end. The only in-app surfaces are the two generic period-end screens (gated by `inventory_management.period_end.view` / `.execute`, not by role name) documented on [inventory/period-end](/en/inventory/inventory/period-end); `enum_stage_role` (the only role enum in the tenant schema) is `{create, approve, purchase, issue, view_only}` — it has no `finance` or `auditor` member, and the inventory-adjustment module (the closest thing to a "who edits cost basis" screen) has no approval queue at all: `StockInService.create()` / `StockOutService.create()` post unconditionally on creation ([inventory-adjustment](/en/inventory/inventory-adjustment) § 1).

| Who (functional interest, not a distinct screen or RBAC role) | What they'd care about |
|------|----------------|
| Whoever holds `inventory_management.period_end.execute` | Runs the period-end close described on [inventory/period-end](/en/inventory/inventory/period-end); on average-method business units this triggers the `tb_period_snapshot` write. |
| Whoever creates GRNs, store requisitions, inventory adjustments, or credit notes | Their document's cost fields are exactly what the engine picks or writes — see [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment). |
| Platform/cluster admin | Sets `tb_business_unit.calculation_method` at business-unit setup — outside this wiki module's own routes. |

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — costing operates on inventory movements; every IN/OUT triggers a costing calculation
- [good-receive-note](/en/inventory/good-receive-note) — GRN receipts set unit costs (FIFO) or update averages (WAC)
- [recipe](/en/inventory/recipe) — recipe consumption uses costed quantities to derive food cost
- [inventory-adjustment](/en/inventory/inventory-adjustment) — adjustments require a cost basis from the costing engine

**Master configuration:**
- [master-data/business-unit](/en/inventory/master-data/business-unit) — tenant/property scope for the valuation ledger
- [master-data/currency](/en/inventory/master-data/currency) — transaction and base currencies plus FX rates; whether FX conversion is preserved per cost-layer row is unconfirmed against source (see [02-business-rules](/en/inventory/costing/02-business-rules) § 5.2)
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
- [03 — User Flow](/en/inventory/costing/03-user-flow) — Cost-flow lifecycle; no distinct persona exists (see correction pages below).
  - [Finance (correction)](/en/inventory/costing/03-user-flow-finance)
  - [Inventory Controller (correction)](/en/inventory/costing/03-user-flow-inventory-controller)
  - [Auditor (correction)](/en/inventory/costing/03-user-flow-auditor)
- [04 — Test Scenarios](/en/inventory/costing/04-test-scenarios) — 11 cross-cutting engine scenarios + E2E mapping.
  - [Finance (correction)](/en/inventory/costing/04-test-scenarios-finance)
  - [Inventory Controller (correction)](/en/inventory/costing/04-test-scenarios-inventory-controller)
  - [Auditor (correction)](/en/inventory/costing/04-test-scenarios-auditor)
- [Inventory Costing Methods: FIFO vs. Weighted Average](/en/inventory/costing/calculation-methods) — Method comparison and algorithms.
