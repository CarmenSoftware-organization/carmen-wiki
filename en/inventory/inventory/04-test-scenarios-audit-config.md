---
title: Inventory — Test Scenarios — Audit & Config (correction)
description: Correction page — the Audit/Config test suite previously documented here targeted an audit workspace and configuration console that do not exist.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, audit-config, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios — Audit & Config (correction)

> **At a Glance**
> **Status:** corrected 2026-07-15 — the ~32 scenarios previously on this page (audit-log workspace queries, lot-recall trace tool, period-snapshot reconciliation queries, watermarked sensitive-field exports, location-type drain blockers, per-product costing-method changes, threshold tier edits, RBAC deadlock previews, integration dual-write cutovers) targeted surfaces with **no source backing** and were removed rather than re-fabricated.

## 1. Why these scenarios were removed

- **No audit workspace or configuration console route exists** under `/inventory-management/` (`routes/router.tsx` lists only `transaction`, `period-end(/review)`, `inventory-adjustment`, `physical-count`, `spot-check`).
- **No threshold, impact-preview, configuration-history, or dual-write mechanism exists** in the backend inventory services.
- **The costing method is not per-product** — it is `tb_business_unit.calculation_method` (platform BU setting); there is nothing to configure in this product's UI, and no drain-guard exists.
- **No dedicated lot-trace or snapshot-reconciliation tool exists**; lot lineage data (`from_lot_no` / `current_lot_no` / `parent_lot_no`) is real but only queryable via the transaction list or the database.

This mirrors the confirmed-absent config-workbench pattern from the purchase-request, purchase-order, good-receive-note, and store-requisition passes.

## 2. Where the real, testable configuration lives

| Formerly tested here | Real test location |
|---|---|
| Location create / `location_type` / `physical_count_type` | [master-data/location](/en/inventory/master-data/location) — E2E `080-location.spec.ts` |
| Adjustment-type reason codes | Config module — E2E `031-adjustment-type.spec.ts` |
| Period definitions / lock | [system-config/period](/en/inventory/system-config/period) |
| User / role / permission scope | [access-control](/en/inventory/access-control) |
| Activity log | [reporting-audit/activity](/en/inventory/reporting-audit/activity) |
| Read-only ledger inspection | [04-test-scenarios-store-keeper](/en/inventory/inventory/04-test-scenarios-store-keeper) (Transaction Log scenarios) |

## 3. References

- Frontend routes: `../carmen-inventory-frontend-react/routes/router.tsx`.
- Parent overview: [04-test-scenarios](/en/inventory/inventory/04-test-scenarios); user-flow counterpart: [03-user-flow-audit-config](/en/inventory/inventory/03-user-flow-audit-config).
