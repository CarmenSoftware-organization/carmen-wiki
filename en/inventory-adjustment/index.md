---
title: Inventory Adjustment
description: Manual corrections to stock balances — write-offs, write-ons, reclassifications.
published: true
date: 2026-05-15T13:00:00.000Z
tags: inventory-adjustment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Inventory Adjustment

## 1. Overview

An **Inventory Adjustment** is a controlled correction to inventory quantity and/or value outside of the normal procurement and consumption flows. Each adjustment is a document with a header — reference number, date, type (`IN` or `OUT`), location, department, reason code, description, attached evidence — and one or more item lines. Each line carries the product, lot detail (when the item is lot-tracked), unit cost, quantity, and a computed line total; the header rolls these up as `inQty`, `outQty`, and `totalCost`.

Adjustments follow a tightly bounded lifecycle: `Draft` (editable, no stock impact) → `Posted` (immutable, stock and GL updated) → `Void` (reverses a posted adjustment via a separate transaction). A draft can be edited freely, but once posted the document is locked — corrections require a void plus a new adjustment. Posting also triggers stock-movement creation, FIFO layer or weighted-average cost recalculation per the item's costing method, and automatic journal entries against the GL account mapped from the reason code.

Adjustments are used whenever stock changes outside the normal documents: damaged goods discovered in storage, expired items written off, theft or shrinkage write-offs, found stock recovered during a sweep, count variances from physical-count or spot-check posted as structured adjustments, and reclassifications between locations or units of measure. The module supports both positive (`IN` — write-on) and negative (`OUT` — write-off) directions, with lot-level granularity for batch-tracked products.

## 2. Business Context

Adjustments are the one channel that lets stock change without a matching upstream procurement or downstream consumption document, so they sit under audit scrutiny by default. Hospitality groups operate on tight food-cost margins; an unexplained or unapproved adjustment can mask shrinkage, theft, or process failure, and unbalanced books at period close are not defensible to external auditors. The module's controls — mandatory reason codes, supporting-document attachments, role-segregated approval, posting-only stock impact, and an immutable post-state — exist to make every correction explainable.

The financial side mirrors this. Each posted adjustment generates journal entries: a write-off (`OUT`) debits an expense or loss account mapped from the reason code and credits inventory, reducing balance-sheet stock value; a found-stock entry (`IN`) debits inventory and credits a gain/recovery account. Reason codes are configured per direction (`IN`, `OUT`, or `BOTH`) and carry their own GL mapping, so the same physical event (e.g. damage write-off vs. expiry write-off) lands in distinct accounts for cost analysis. Period-end validation rejects any adjustment dated into a closed period, protecting locked valuations.

Operationally, adjustments are also the formal landing point for variances detected by **physical-count** (full count) and **spot-check** (partial verification). When a count variance is confirmed, the system creates an adjustment document for the variance lines and routes it through the same approval and posting flow as an ad-hoc adjustment, so all stock corrections share one audit trail.

## 3. Key Concepts

- **Adjustment Type**: The direction of the correction. `IN` increases on-hand quantity (write-on — found stock, count surplus, returned items recovered) and posts as a `RECEIPT`-style stock movement. `OUT` decreases on-hand quantity (write-off — damage, expiry, theft, count shortage) and posts as an `ISSUE`-style movement. Stored on the header as `type: 'IN' | 'OUT'`. Each line must agree with the header type.
- **Reason Code**: Required code that classifies *why* the adjustment is happening (e.g. damage, expiry, theft, count variance, reclassification). Carries `type: 'IN' | 'OUT' | 'BOTH'` so only valid reasons appear for the chosen direction, plus `requiresDocument`, `requiresQualityCheck`, and a `glAccount` that determines the expense/gain account the posting journal hits. Reason codes are mandatory (`ADJ_CRT_004`) and validated against the adjustment type (`ADJ_VAL_006`).
- **Cost Basis**: The unit cost applied to each adjustment line. For `OUT` adjustments under weighted-average costing, the line uses the current average cost; for `OUT` under FIFO, lines consume cost from the oldest layers first. For `IN` adjustments under weighted-average, posting computes a new average — `New Average Cost = ((Old Qty × Old Cost) + (Adj Qty × Adj Cost)) / (Old Qty + Adj Qty)` (`ADJ_CALC_005`); under FIFO, a new cost layer is created. Cost must be supplied for every item (`ADJ_VAL_003`) and the line total `Item Cost = Unit Cost × Quantity` (`ADJ_CALC_001`) must equal the header `totalCost` (`ADJ_VAL_005`).
- **Lot Tracking**: For lot-controlled items, the adjustment must reference specific lot numbers (`ADJ_CRT_007`). Each line carries an array of `Lot { lotNo, quantity, uom, expiryDate? }`. On `OUT`, lot quantities cannot exceed available balance per lot (`ADJ_VAL_004`); on `IN`, new lots may be created. Lot history is preserved end-to-end so expiry-driven write-offs and recall events are traceable.
- **Approval Workflow / Status**: Adjustments move through `Draft` → `Posted` → `Void` (the only three states stored on the header). `Draft` is the working state; the adjustment is editable, no stock or GL impact has occurred, and the document can be deleted. `Posted` is the terminal active state — stock balances are updated, journal entries are written, and the document becomes immutable (`ADJ_PRC_007`). `Void` reverses a posted adjustment but is created as a *separate* transaction (`ADJ_PRC_008`) so the original posting remains in the audit trail. Status transitions, the user who made them, and timestamps are all logged.
- **Posting (Stock + GL Impact)**: Posting is the single event that mutates the world — stock is not updated until posting (`ADJ_PRC_001`). On post, the system: (1) writes a stock-movement record per line, (2) updates `InventoryStatus.QuantityOnHand`, `LastUnitCost`, and `TotalCost`, (3) creates/updates FIFO layers or `AverageCostTracking` entries per item's costing method, (4) generates `JournalEntry` rows mapped from the reason code's `glAccount` and the line's cost-centre, and (5) validates the date is within an open accounting period (`ADJ_CRT_010`, `ADJ_PRC_009`). Real-time stock validation (`ADJ_PRC_010`) prevents negative balances (`ADJ_VAL_001`).

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Store Keeper / Warehouse Staff | Identifies discrepancies on the floor, initiates the adjustment in `Draft`, attaches supporting evidence (photos, damage reports, expiry labels), and documents the reason. |
| Inventory Controller / Inventory Manager | Reviews submitted adjustments for accuracy and reasonableness, monitors variance patterns by reason and location, approves or rejects, and posts the document so it impacts stock and GL. |
| Finance Team | Verifies the cost impact and GL account mapping per reason code, reconciles inventory sub-ledger against GL, and signs off on adjustment activity at period close. |
| Department Manager | Reviews adjustments hitting the department's cost-centre, investigates unusual patterns or oversize variances, and drives corrective process changes. |
| Auditor | Inspects the adjustment trail end-to-end — reason codes, attachments, approval signatures, journal entries, and void chains — for compliance and segregation-of-duties checks. |
| System Administrator | Maintains the reason-code master (codes, type, GL mapping, document-required flag), configures user permissions and approval thresholds, and manages integration settings. |

## 5. Related Modules

- [[inventory]] — adjustments modify inventory balances directly
- [[costing]] — adjustments require a cost basis (entered manually or from costing engine)
- [[physical-count]] — count variances become adjustment documents
- [[spot-check]] — partial count variances become adjustment documents

## 6. Reference Sources

- Concepts: `../carmen/docs/inventory-adjustment/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, posting, and cross-module rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle, plus persona index.
  - [Store Keeper](./03-user-flow-store-keeper.md)
  - [Inventory Controller](./03-user-flow-inventory-controller.md)
  - [Finance](./03-user-flow-finance.md)
  - [Audit / Config](./03-user-flow-audit-config.md)
- [04 — Test Scenarios](./04-test-scenarios.md) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Store Keeper](./04-test-scenarios-store-keeper.md)
  - [Inventory Controller](./04-test-scenarios-inventory-controller.md)
  - [Finance](./04-test-scenarios-finance.md)
  - [Audit / Config](./04-test-scenarios-audit-config.md)
