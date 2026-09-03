---
title: Inventory
description: Stock balances, locations, and the period-end process — the core of the inventory ERP.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Inventory

> **At a Glance**
> **Module purpose:** System of record for stock movement (product × location × lot) — the append-only transaction ledger feeding costing, plus the period-end close &nbsp;·&nbsp; **Screens:** `/inventory-management/transaction` (read-only ledger), `/inventory-management/period-end` + `/review` (close) &nbsp;·&nbsp; **Key tables:** `tb_inventory_transaction` (+ `_detail`, `_cost_layer`), `tb_period`, `tb_period_snapshot` (average-method tenants only) &nbsp;·&nbsp; **Sub-pages:** 14

![Inventory screen](/screenshots/inventory/index.png)

## 1. Overview

The Inventory module is the system of record for stock movement across the property. There is **no persisted balance row** — on-hand at `(location, product, lot)` is always the derived sum of the cost-layer ledger (`Σ in_qty − Σ out_qty`), and every balance figure elsewhere in the product (PR on-hand dialog, spot-check system qty) reads from the same sum. Unit cost travels with each layer so that quantity and valuation move together.

All quantity changes flow through **inventory transactions**. A transaction is classified by `enum_inventory_doc_type` — `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, or `open` — and points at the source document that generated it. The transaction has **no workflow status of its own**: it is written already-posted when the source document reaches its posting event (GRN **save**, SR approve-at-final-stage, inventory-adjustment completion, credit-note completion, period close). A receipt to a `direct`-type location additionally writes an automatic offsetting issue at the same cost, netting on-hand to zero ("consumed on arrival"); no GL/journal posting exists for any movement (see [01 — Data Model](/en/inventory/inventory/01-data-model) § 1).

At the end of each accounting period the module runs the **period-end close**: open documents and physical counts are checked as blocking gates, then every lot's remaining balance is zeroed in the closing period and re-created in the next one at the same cost. On average-method tenants the close also writes `tb_period_snapshot` rows (opening / movement-buckets / closing per product × location); FIFO tenants carry lots forward without a snapshot. New movements always stamp into the current open period — backdated rows never enter a closed period.

## 2. Business Context

In hospitality operations, inventory is where food cost lives. Most of the property's variable cost — F&B raw materials, housekeeping supplies, minibar stock — sits in this module before it becomes COGS. Getting the balance right matters for three reasons:

- **Food cost control.** Plate cost, recipe yield, and menu profitability all depend on accurate stock movements feeding the costing module. Phantom inventory hides shrinkage; missing receipts inflate margins on paper.
- **Audit visibility.** Hospitality groups operate under tight audit cycles. Every stock movement must trace to a source document (GRN, requisition, count sheet, write-off authorisation), and the period-end lock has to be defensible to external auditors.
- **Regulatory and group reporting.** Inventory valuation feeds the balance sheet; movement classification (inventory vs. direct expense vs. consignment) determines whether spend hits assets or P&L. Mixed methods are common in hotel chains and the module has to keep them straight per location.

This module sits between **Procurement** (receipts in) and **Operations** (requisitions out), and is the data source the **Costing** module reads for valuation.

## 3. Key Concepts

- **Stock Balance (derived)**: The on-hand quantity of a product at a location, optionally split by lot. **Not a table** — always computed as `Σ cost_layer.in_qty − Σ out_qty` for the key. No `allocated` / `available` / `inTransit` columns exist; anything of that shape is derived from open-document state at read time.
- **Location Type**: Classifies a storage location as `inventory` (ordinary accruing balance), `direct` (receipt auto-issues itself out at the same cost — net on-hand zero, "consumed on arrival"), or `consignment` (no distinct code path found — behaves like `inventory` for cost-layer and counting purposes). No confirmed GL effect for any of the three.
- **Inventory Transaction**: An immutable, posted record of a quantity change. Classified by source module (`enum_inventory_doc_type`) on the header and by cost-flow effect (`enum_transaction_type` — `good_received_note`, `issue`, `transfer_in/out`, `adjustment_in/out`, `credit_note_*`, `eop_*`, `close_period`, `open_period`) on the cost layer. References its source document polymorphically; movements are the atomic unit the audit trail is built from.
- **Period-End Close**: The gate-checked close of an accounting period (`open → closed` on `tb_period.status`). Blocking gates: in-progress PR/PO/SR, mid-state GRN/CN, and incomplete physical counts at required locations. The close zeroes every surviving lot (`CLOSE-…`) and re-creates it in the auto-provisioned next period (`OPEN-…`); on average-method tenants it also writes the `tb_period_snapshot` buckets. Backdating is handled by re-dating (movements always stamp into the open period), not by rejection.
- **Valuation Method**: The cost-flow assumption — `fifo` or `average` — configured **per business unit** (`tb_business_unit.calculation_method`, platform schema; default `average`), not per product. Applied uniformly by the posting engine when movements consume inventory. See [costing](/en/inventory/costing) for the calculation rules; this module stores the inputs (lots, dates, costs) the engine needs.

## 4. Roles and Personas

The system defines no inventory-module roles — access is by permission key (`constant/permissions.ts`), and the "personas" used in this module's user-flow / test-scenario pages are documentation groupings over those keys, not system entities:

| Persona (doc grouping) | Real access surface |
|------|----------------|
| Store Keeper | Reads the transaction ledger (`inventory_management.view`); authors adjustments in the sibling [inventory-adjustment](/en/inventory/inventory-adjustment) module (`inventory_management.stock_in.*` / `.stock_out.*`) and counts in [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check). |
| Inventory Controller / period-end operator | Runs the period-end review and close (`inventory_management.period_end.view` / `.execute`). No approval queue, variance dashboard, or threshold routing exists in this module. |
| Finance | **No Finance role or GL surface exists** — `enum_stage_role` has no `finance` member and no journal-posting code was found; see the correction pages [User Flow — Finance](/en/inventory/inventory/03-user-flow-finance) and [01 — Data Model](/en/inventory/inventory/01-data-model) § 1. |

## 5. Related Modules

**Cross-module flow:**
- [costing](/en/inventory/costing) — costing is calculated against inventory balances; every stock movement updates valuation
- [good-receive-note](/en/inventory/good-receive-note) — GRN is the primary upstream source of stock receipts
- [store-requisition](/en/inventory/store-requisition) — store requisitions are the primary downstream consumer
- [inventory-adjustment](/en/inventory/inventory-adjustment) — manual corrections to balances
- [physical-count](/en/inventory/physical-count) — periodic full count
- [spot-check](/en/inventory/spot-check) — partial verification counts

**Master configuration:**
- [master-data/unit](/en/inventory/master-data/unit) — base, order, and recipe units of measure for every product balance
- [master-data/location](/en/inventory/master-data/location) — warehouse and storage locations that anchor every stock balance
- [master-data/business-unit](/en/inventory/master-data/business-unit) — tenant/property scope that segregates balances and movements
- [system-config/period](/en/inventory/system-config/period) — accounting period that gates posting and locks the snapshot
- [system-config/dimension](/en/inventory/system-config/dimension) — analytical dimensions carried in the `dimension` JSON on transactions and cost layers
- [access-control/user-location](/en/inventory/access-control/user-location) — restricts which locations a user can transact against
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — movement and balance-change activity log for audit

## 6. Reference Sources

- Concepts: `../carmen/docs/inventory-management/`
- Concepts: `../carmen/docs/Inventory/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/inventory/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](/en/inventory/inventory/02-business-rules) — Validation, calculation, authorization, posting, and cross-module rules.
- [03 — User Flow](/en/inventory/inventory/03-user-flow) — Movement and period lifecycle, plus persona index.
  - [Store Keeper](/en/inventory/inventory/03-user-flow-store-keeper)
  - [Inventory Controller](/en/inventory/inventory/03-user-flow-inventory-controller)
  - [Finance](/en/inventory/inventory/03-user-flow-finance)
  - [Audit / Config](/en/inventory/inventory/03-user-flow-audit-config)
- [04 — Test Scenarios](/en/inventory/inventory/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Store Keeper](/en/inventory/inventory/04-test-scenarios-store-keeper)
  - [Inventory Controller](/en/inventory/inventory/04-test-scenarios-inventory-controller)
  - [Finance](/en/inventory/inventory/04-test-scenarios-finance)
  - [Audit / Config](/en/inventory/inventory/04-test-scenarios-audit-config)
