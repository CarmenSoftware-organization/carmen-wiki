---
title: Costing
description: Inventory valuation methods (FIFO, Weighted Average) and the costing engine that calculates COGS and ending inventory value.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: costing, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Costing

> **At a Glance**
> **Module purpose:** Per-transaction valuation engine that picks `cost_per_unit` for every outbound stock movement and refreshes `average_cost_per_unit` for every inbound, under a single FIFO-or-Average method set **per business unit** &nbsp;·&nbsp; **Audience:** developers/testers working on inventory valuation — the module has no distinct in-app persona, just the generic `inventory_management.*` permission gates &nbsp;·&nbsp; **Key entities/tables:** `tb_inventory_transaction_cost_layer` (the cost-flow ledger, now with `extra_cost_amount`), `tb_inventory_period_snapshot` (renamed from `tb_period_snapshot` on 2026-09-16; average-method periods only), `tb_business_unit.calculation_method`, [costing/calculation-methods](/en/inventory/costing/calculation-methods) &nbsp;·&nbsp; **Sub-pages:** 11
> **Re-verified 2026-09-22** against `carmen-turborepo-backend-v2` HEAD. Changes since 2026-07-29: extra cost is allocated into landed cost (`20260910130000_add_cost_layer_extra_cost`); FOC quantity enters stock; average-costed units post a GRN's movement at **save** (FIFO at commit); `tb_period*` → `tb_inventory_period*`; lot numbers are `<location_code><YYMM><run>`; a GL module exists but is not wired to inventory (see §1).

## 1. Overview

The Costing module is the valuation engine of the inventory ERP. It consumes the stream of stock movements produced by the Inventory module and, for every outgoing transaction, picks the **Cost of Goods Sold (COGS)** unit cost; for every incoming transaction, it writes the cost basis of the new stock and (under Weighted Average) refreshes the running average. The engine runs per-transaction rather than as a periodic batch — a GRN's inbound cost-layer rows are written inside the same database transaction as the GRN transition that posts it: **commit** on FIFO business units, **save** on average business units (`GoodReceivedNoteLogic.save()` / `commit()` → `postGrnLedger()` → `InventoryTransactionService.createFromGoodReceivedNote()`, `inventory-transaction.service.ts:841-1250`), so balances and valuation stay in step with quantities. The inbound cost the engine receives is the **landed cost**: `(base_net_amount + allocated extra cost) / (received_base_qty + foc_base_qty)`, rounded to **2 dp** (`stockQtyOf` / `stockCostOf`, `:73-92`; `Math.round(x × 100) / 100`, `:941,1134`).

Two cost-flow assumptions are supported: **FIFO**, which preserves each receipt as a distinct lot (`tb_inventory_transaction_cost_layer`, ordered by `lot_seq_no`) and consumes the oldest lot first, and **Weighted Average Cost (WAC)**, which blends every receipt into a single rolling average (`average_cost_per_unit`). **Corrected 2026-09-22:** the average is maintained **per product across all locations of the business unit** — `getNetTotals(tx, productId)` (`:1487-1509`) nets every live layer of the product regardless of `location_id`, and the new average is stamped on every non-direct layer of the product (`:1236-1247`); location only enters the on-hand check (`getLocationBalance`). The method is **not** configurable per product or per category — it is a single `tb_business_unit.calculation_method` value (platform schema, `average` | `fifo`, default `average`) that applies to every product at that business unit; `InventoryTransactionService.getCalculationMethod(bu_code)` (`:402-408`) reads it once and applies it uniformly. There is no code path that mixes FIFO and Average within one business unit, and no in-app screen to change it — it is a platform/cluster-admin field on the business unit record, outside this module's own routes. See [01-data-model](/en/inventory/costing/01-data-model) § 5 for the full divergence from earlier per-product framing.

Outputs land in two places: the cost-layer row itself carries the picked `cost_per_unit` / `average_cost_per_unit` (and, since 2026-09-10, the `extra_cost_amount` share of `total_cost`) for every consumer to read; and, at period close, `tb_inventory_period_snapshot` locks the period's opening/receipt/issue/adjustment/closing cost columns — but **only when the business unit's method is `average`** (`period-end.close-average.helper.ts:480`). The FIFO close path carries lot balances forward as `close_period`/`open_period` cost-layer rows instead and does not write a snapshot at all (`period-end.close-transaction.helper.ts`). **GL posting — precise status 2026-09-22:** a general-ledger module now exists (`apps/micro-business/src/gl/`; `GlPostingService.post()` at `gl-posting.service.ts:293` posts a `tb_gl_jv` into `tb_gl_balance`), but nothing in `inventory-transaction.service.ts`, `good-received-note.*.ts`, or `period-end.*.ts` imports or calls it; the only JV writers are the JV module itself (`gl-jv.service.ts:214`, source `manual`), template runs (`gl-jv-template.service.ts:786`), and the posting service's reversal / closing vouchers (`gl-posting.service.ts:571,909,1116`); `enum_gl_jv_source.inventory` (`schema.prisma:4733`) has no writer. **No inventory movement, GRN, or period-end close posts to the GL ledger today** — no `Dr`/`Cr` fan-out, no GL control account, no inventory-to-GL reconciliation. Detailed FIFO vs. WAC algorithms, numerical examples, and the trade-offs between the two methods are covered in the sub-page below — this landing page only orients.

## 2. Business Context

Inventory valuation is a regulated activity. Both **IFRS** (IAS 2) and **US GAAP** (ASC 330) accept FIFO and Weighted Average as permissible cost-flow assumptions, but they require the choice to be applied consistently per product class and disclosed in the financial statements. The costing module is therefore an audit-facing component: every COGS figure must be traceable back to a specific receipt (FIFO) or a specific moving-average computation (WAC), and the trail has to survive an external audit cycle.

Operationally, costing is where **food cost control** lives. Plate cost, recipe profitability, and menu-engineering decisions all read from this module. If the costing engine drifts — stale lots, missed waste write-offs, incorrect average recomputation after a return — every downstream margin number drifts with it. Hospitality groups typically run on tight food-cost margins, so a one-or-two-percentage-point error in valuation translates directly into a noticeable P&L miss. This module is the contract between physical inventory movements and the financial picture the business steers by.

## 3. Key Concepts

- **COGS (Cost of Goods Sold)**: The cost picked when inventory leaves an inventory-type location for consumption (issue to a kitchen, write-off, sale through a POS-linked recipe). Written by the costing engine onto the outbound `tb_inventory_transaction_cost_layer` row at the moment of the movement. No inventory movement is posted to the GL (the GL module exists but is not called from inventory code) — the cost-layer row itself is the only durable record of the movement's cost.
- **Ending Inventory Value**: The monetary value of stock still on hand at a point in time — quantity multiplied by the unit cost determined by the active costing method. On **average-method** business units this is locked into `tb_inventory_period_snapshot` at period close; on **FIFO-method** business units it is derived from the residual cost-layer lots carried forward as `open_period` rows (no snapshot row is written).
- **FIFO (First-In, First-Out)**: A cost-flow assumption under which the oldest receipts are consumed first. Each receipt becomes a discrete **lot** with its own unit cost; the engine consumes lots in order until the issued quantity is satisfied, so older costs flow to COGS while newer costs remain in ending inventory. Under FIFO the new receipt's layers are written with `average_cost_per_unit = 0` (`inventory-transaction.service.ts:998`) — there is no "shadow average" maintained on GRN receipts.
- **Weighted Average Cost (WAC)**: A cost-flow assumption under which every receipt is blended into a single moving-average unit cost **per product** (all locations). The average is recomputed on every receipt as `Round2((Σ live layers' net cost + new total cost) / (Σ live layers' net qty + new qty))` (`calculateNewAverageCost`, `common/helpers/inventory-cost.formula.ts:90-101`; `getNetTotals` nets each layer's `in_qty − out_qty` at that layer's `cost_per_unit`). Issues are costed at the average prevailing at the time of issue; the same value is re-stamped on every live layer of the product, so reports read it without recomputing.
- **Landed cost**: What the engine values a receipt at — the line's `base_net_amount` plus its share of the GRN's extra cost (`allocateExtraCost`, `good-received-note.extra-cost.ts`: `by_qty` = equal share per line, `by_value` = weighted by stock quantity, `manual` = none), divided by `received_base_qty + foc_base_qty`. The extra-cost share is persisted per layer as `extra_cost_amount`.
- **Lot/Batch**: An identifiable group of stock from a single receipt, carrying its own quantity, receipt date, and unit cost. The lot number is `<location_code><YYMM><4-digit run>` (`common/helpers/lot-number.helper.ts`), where the run number is `lot_seq_no`, restarting at 1 each inventory period. Required for FIFO (the engine consumes lots in receipt order) and also used independently for product traceability (the ledger row links back to the GRN receipt event via `good_received_note_detail_item_id`).
- **Cost Basis**: The unit cost the engine assigns to a balance for valuation and downstream costing. Under FIFO, it is per-lot; under WAC, it is the current moving average for the product at the location. Every adjustment, return, or recipe consumption requires a cost basis from this module — the engine is the single source of truth for "what did this unit cost?".

## 4. Roles and Personas

**Correction (verified 2026-07-22, re-checked 2026-09-22):** earlier drafts of this module documented three distinct RBAC personas (Finance, Inventory Controller, Auditor) with dedicated approval queues, a valuation-policy console, a sub-ledger ↔ GL reconciliation dashboard, and a read-only audit workspace. None of that exists in the product. The engine itself has no persona-gated screen at all — it is a service invoked from GRN commit (or save on average units), store-requisition issue, inventory-adjustment commit, credit-note, and period-end. The only in-app surfaces are the two generic period-end screens (gated by `inventory_management.period_end.view` / `.execute`, not by role name) documented on [inventory/period-end](/en/inventory/inventory/period-end); `enum_stage_role` (the only role enum in the tenant schema) is `{create, approve, purchase, issue, view_only}` — it has no `finance` or `auditor` member. **Updated 2026-09-22:** the inventory-adjustment module now has a `draft` state — `StockInService.create()` writes `doc_status = draft` (`stock-in.service.ts:418`) and only `PATCH …/stock-ins/:id/commit` (`:471-575`) posts to the ledger and sets `completed` — but there is still no approval queue or cost-pick preview: the same user who created the draft commits it.

| Who (functional interest, not a distinct screen or RBAC role) | What they'd care about |
|------|----------------|
| Whoever holds `inventory_management.period_end.execute` | Runs the period-end close described on [inventory/period-end](/en/inventory/inventory/period-end); on average-method business units this triggers the `tb_inventory_period_snapshot` write. |
| Whoever creates GRNs, store requisitions, inventory adjustments, or credit notes | Their document's cost fields are exactly what the engine picks or writes — see [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment). |
| Purchasers / receivers checking "what did we pay last time" | Read-only cost endpoints on the gateway `application/cost` controller: `GET /api/:bu_code/cost/products/:product_id/last-cost` (last GRN **or** stock-in cost), `…/last-receiving` (last GRN), `…/last-receiving/unit/:unit_id` (last GRN price per received unit, `cost_per_unit = net_amount / received_qty`), `…/location/:location_id/qty/:qty` (cost estimate) — guards `product.last-cost`, `product.last-receiving`, `product.last-receiving-by-unit`, `product.cost-estimate`; Bruno `_uncategorized/cost/`. |
| Platform/cluster admin | Sets `tb_business_unit.calculation_method` at business-unit setup — outside this wiki module's own routes. |

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — costing operates on inventory movements; every IN/OUT triggers a costing calculation
- [good-receive-note](/en/inventory/good-receive-note) — GRN receipts set landed unit costs (FIFO lots) or update the product average (WAC); posted at commit on FIFO units and already at save on average units; extra cost and FOC included
- [recipe](/en/inventory/recipe) — recipe consumption uses costed quantities to derive food cost
- [inventory-adjustment](/en/inventory/inventory-adjustment) — adjustments require a cost basis from the costing engine

**Master configuration:**
- [master-data/business-unit](/en/inventory/master-data/business-unit) — tenant/property scope for the valuation ledger
- [master-data/currency](/en/inventory/master-data/currency) — transaction and base currencies plus FX rates; **confirmed 2026-09-22:** the ledger stores **base currency only** — the GRN feeds `base_net_amount` and converts the extra-cost share with `calcBase(share, exchange_rate)` (`good-received-note.ledger.ts:131`); no per-layer FX rate is kept
- [master-data/unit](/en/inventory/master-data/unit) — base unit conversion required to value any costed line
- [system-config/period](/en/inventory/system-config/period) — inventory period (`tb_inventory_period`, HTTP `/inventory-periods`, permission `system_admin.inventory_period`) that gates costing posting (a GRN's period is resolved from `grn_date` by date range, `open` or `locked` only) and locks valuation
- [system-config](/en/inventory/system-config) cost centres — `tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account` (`20260904103000_add_cost_center`) are **not linked to costing**: no inventory table carries `cost_center_id` (the only FK is `tb_gl_jv_detail.cost_center_id`); inventory rows carry a free-form `dimension` JSON only
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — costing recalculation and posting activity log for audit

## 6. Reference Sources

- Concepts: `../carmen/docs/costing/enhanced-costing-engine.md` (frozen 2026-04-27 — recipe/portion costing, not the inventory engine)
- Frontend: `../carmen-inventory-frontend-react/` — no costing screen; `routes/accounting/` is mock data
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (engine), `apps/micro-business/src/common/helpers/{inventory-cost.formula,fifo-cost-split.helper,lot-number.helper}.ts`, `apps/micro-business/src/inventory/good-received-note/good-received-note.{ledger,extra-cost}.ts` (inbound feed), `apps/micro-business/src/inventory/period-end/` (close), `apps/micro-business/src/inventory/costing/` (cost read endpoints), gateway `apps/backend-gateway/src/application/cost/`
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/cost/` (4 requests)
- E2E tests: `../carmen-inventory-frontend-e2e/` — no dedicated costing spec (see [04-test-scenarios](/en/inventory/costing/04-test-scenarios) § 4)

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
