---
title: Inventory — Test Scenarios — Finance (correction)
description: Correction page — the Finance test suite previously documented here targeted surfaces (approval queue, GL reconciliation, period lock) that do not exist.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios — Finance (correction)

> **At a Glance**
> **Status:** corrected 2026-07-15 — the ~28 scenarios previously on this page (cost-impact approval queue, inventory-to-GL reconciliation with tolerances and compensating journals, period close orchestration with sign-off gates, period lock / re-open, FX revaluation journals) targeted surfaces with **no source backing** and were removed rather than re-fabricated.

## 1. Why these scenarios were removed

- **No Finance role or permission key exists** (`enum_stage_role` has no `finance` member; no finance-scoped key in `constant/permissions.ts`).
- **No inventory-to-GL, reconciliation, or tolerance code exists.** The 2026-09 GL core (`tb_gl_jv*`, `/api/{bu}/gl-posting`) is a manual-JV module with no inventory hook (see [01-data-model](/en/inventory/inventory/01-data-model) § 1).
- **No threshold-based approval chain exists** ([02-business-rules](/en/inventory/inventory/02-business-rules) § 4 correction).
- **No lock/re-open endpoint exists in this module** (`period-end.controller.ts`: `find-all` / `find-current` / `find-review` / `start-counting` / `close` only). The previously-cited close-blocking rules ("Controller sign-off", "reconciliation clean") are replaced by the real gates in `listStartCountingBlockers` / `validatePeriodEnd` — see [period-end](/en/inventory/inventory/period-end) § 2.

This mirrors the confirmed-fabricated Finance persona findings in the purchase-order, good-receive-note, and store-requisition modules.

## 2. Where the testable behaviour lives now

| Formerly tested here | Real test location |
|---|---|
| Period close happy path / blocked / race | [04-test-scenarios-inventory-controller](/en/inventory/inventory/04-test-scenarios-inventory-controller) IC-HP-02/05/06, IC-VAL-01–06 |
| Credit-note amount repricing (open vs closed period) | [04-test-scenarios](/en/inventory/inventory/04-test-scenarios) scenarios 5, 6, 12 |
| Backdating behaviour | [04-test-scenarios](/en/inventory/inventory/04-test-scenarios) scenario 7 (rejected at the source document since 2026-08-31) |
| Adjustment approval | No approval tier exists; adjustment document tests belong to [inventory-adjustment](/en/inventory/inventory-adjustment) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts`, `.../inventory-transaction/inventory-transaction.service.ts`.
- Parent overview: [04-test-scenarios](/en/inventory/inventory/04-test-scenarios); user-flow counterpart: [03-user-flow-finance](/en/inventory/inventory/03-user-flow-finance).
