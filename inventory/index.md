---
title: Inventory
description: Stock balances, locations, and the period-end process — the core of the inventory ERP.
published: true
date: 2026-05-15T07:48:00.000Z
tags: inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Inventory

## 1. Overview

The Inventory module is the system of record for stock balances across the property. A balance is keyed by **product × warehouse × location** (with optional batch/lot when batch tracking is enabled), and exposes `onHand`, `allocated`, `available`, and `inTransit` quantities alongside per-batch detail. Every balance carries a current/average unit cost so that quantity and valuation move together.

All quantity changes flow through **stock movements**. A movement has a type — `RECEIPT`, `ISSUE`, `TRANSFER`, `ADJUSTMENT`, `RETURN`, or `WRITE_OFF` — a source location, an optional destination location, line items, and a workflow status (`DRAFT` → `PENDING` → `IN_TRANSIT` → `COMPLETED` / `CANCELLED`). The movement classifies posting behaviour: an inventory location debits the inventory asset account, a direct-cost location bypasses inventory and posts straight to department expense. Returns, write-offs, and adjustments share the same movement spine but differ in journal direction and approval rules.

At the end of each accounting period the module produces a **period-end snapshot**: the final physical count is reconciled against system quantities, variances are posted as adjustments, valuation is locked, and the period is closed against backdated entries. The snapshot is the audit anchor that downstream modules (costing, financial reporting) consume.

## 2. Business Context

In hospitality operations, inventory is where food cost lives. Most of the property's variable cost — F&B raw materials, housekeeping supplies, minibar stock — sits in this module before it becomes COGS. Getting the balance right matters for three reasons:

- **Food cost control.** Plate cost, recipe yield, and menu profitability all depend on accurate stock movements feeding the costing module. Phantom inventory hides shrinkage; missing receipts inflate margins on paper.
- **Audit visibility.** Hospitality groups operate under tight audit cycles. Every stock movement must trace to a source document (GRN, requisition, count sheet, write-off authorisation), and the period-end lock has to be defensible to external auditors.
- **Regulatory and group reporting.** Inventory valuation feeds the balance sheet; movement classification (inventory vs. direct expense vs. consignment) determines whether spend hits assets or P&L. Mixed methods are common in hotel chains and the module has to keep them straight per location.

This module sits between **Procurement** (receipts in) and **Operations** (requisitions out), and is the data source the **Costing** module reads for valuation.

## 3. Key Concepts

- **Stock Balance**: The on-hand quantity of a product at a specific warehouse and location, optionally split by batch/lot. Carries `onHand`, `allocated`, `available`, and `inTransit` quantities plus current unit cost and total value. Updated by every committed stock movement.
- **Location Type**: Classifies a storage location as `INVENTORY` (stock asset, posts to inventory GL account), `DIRECT` (direct-cost centre, posts straight to department expense), or transit/special-purpose. Location type determines the journal entries a movement generates and whether the item ever appears as an asset on the balance sheet.
- **Stock Movement**: An immutable, posted record of a quantity change. Identified by type (`RECEIPT`, `ISSUE`, `TRANSFER`, `ADJUSTMENT`, `RETURN`, `WRITE_OFF`), references a source document (GRN, store requisition, count, write-off authorisation), and produces both a balance update and a journal entry. Movements are the atomic unit the audit trail is built from.
- **Period-End Snapshot**: The locked state of every stock balance at the close of an accounting period. Created after the period-end checklist (physical count → variance reconciliation → adjustment approval → valuation verification → period lock). Backdated transactions into a closed period are rejected by the system.
- **Valuation Method**: The cost-flow assumption applied to a product — `FIFO` or `WEIGHTED_AVERAGE` — configured per product (or globally) and applied by the costing engine when movements consume inventory. See [[costing]] for the calculation rules; this module stores the inputs (lots, dates, costs) the engine needs.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Store Keeper | Records day-to-day stock movements — receipts, issues, transfers — and runs physical counts at the location level. |
| Inventory Controller | Owns balance accuracy: reviews variances, approves adjustments, coordinates spot checks and full counts, signs off on period-end reconciliation. |
| Finance | Verifies valuation, reconciles inventory GL to the sub-ledger, approves journal entries from movements, and locks the period after close. |

## 5. Related Modules

- [[costing]] — costing is calculated against inventory balances; every stock movement updates valuation
- [[good-receive-note]] — GRN is the primary upstream source of stock receipts
- [[store-requisition]] — store requisitions are the primary downstream consumer
- [[inventory-adjustment]] — manual corrections to balances
- [[physical-count]] — periodic full count
- [[spot-check]] — partial verification counts

## 6. Reference Sources

- Concepts: `../carmen/docs/inventory-management/`
- Concepts: `../carmen/docs/Inventory/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

No sub-pages yet.
