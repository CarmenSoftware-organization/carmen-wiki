---
title: Inventory — User Flow — Audit & Config (correction)
description: Correction page — no inventory audit workspace or configuration console exists; real configuration lives in master-data, system-config, and access-control.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, audit-config, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Audit & Config (correction)

> **At a Glance**
> **Status:** corrected 2026-07-15 — the "inventory audit-log workspace" and "inventory configuration console" previously documented here (lot-recall trace tool, period-snapshot reconciliation query, threshold/RBAC/integration panels, impact-preview engine) **do not exist in the product**.
> **What is real:** the read-only Transaction Log at `/inventory-management/transaction`, plus generic configuration screens in other modules.

## 1. What this page previously claimed, and why it was removed

An earlier draft described two dedicated workspaces: an Auditor screen (audit-log query, forward/backward lot-recall trace, period-snapshot reconciliation, watermarked sensitive-field export with co-approval) and a Sysadmin "inventory configuration console" (panels for locations, per-product costing method, adjustment types, periods, approval thresholds, RBAC scope, integration-endpoint dual-write cutover, with impact previews and configuration history). Verification against current source found no matching route, component, or endpoint — the same config-workbench fabrication pattern already confirmed absent in the purchase-request, purchase-order, good-receive-note, and store-requisition passes. Specifics:

- No route under `/inventory-management/` beyond `transaction`, `period-end(/review)`, `inventory-adjustment`, `physical-count`, `spot-check` (see `routes/router.tsx`).
- No `threshold` configuration exists anywhere in the backend inventory services; no per-product costing method exists to configure (the method is `tb_business_unit.calculation_method` — a platform BU setting).
- No lot-trace or snapshot-reconciliation query tool exists; lot lineage *data* is real (`from_lot_no` / `current_lot_no` / `parent_lot_no`) but the only UI over it is the transaction list.
- No impact-preview, drain-requirement, dual-write, or configuration-history mechanism was found.

## 2. Where the real configuration lives

| Formerly claimed here | Real screen / owner |
|---|---|
| Location definition (`location_type`, `physical_count_type`) | [master-data/location](/en/inventory/master-data/location) (`/config/location`) |
| Adjustment reason codes (`tb_adjustment_type`) | Config module (`/config/adjustment-type`) — see [inventory-adjustment](/en/inventory/inventory-adjustment) |
| Costing method | `tb_business_unit.calculation_method` — platform-level BU setting (Carmen Platform), not configurable in this product's UI |
| Period definitions / lock | [system-config/period](/en/inventory/system-config/period) (`/system-admin/period`) |
| User/role/permission scope | [access-control](/en/inventory/access-control) (`/system-admin/user`, `/role`, permission keys) |
| Activity / audit log | [reporting-audit/activity](/en/inventory/reporting-audit/activity) (`/system-admin/activity-log`) and the read-only [transaction](/en/inventory/inventory/transaction) ledger |

## 3. What an auditor can actually do today

- Read the append-only ledger at `/inventory-management/transaction` (`inventory_management.view`): filter by date range, direction, location, category, ref-type; trace `parent_document_no` back to the source document.
- Follow lot lineage in data via `from_lot_no` / `current_lot_no` on `tb_inventory_transaction_detail` and `parent_lot_no` on the cost layers — by query, not by a dedicated trace tool.
- Review closed periods on `/inventory-management/period-end` (history list) and the `close` / `open` ledger rows the close writes.

## 4. References

- Frontend routes: `../carmen-inventory-frontend-react/routes/router.tsx` (the definitive inventory-management route list).
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` (no audit/config service exists in this scope).
- Parent overview: [03-user-flow](/en/inventory/inventory/03-user-flow).
