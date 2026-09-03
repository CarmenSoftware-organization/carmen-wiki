---
title: Costing — Test Scenarios — Auditor (correction)
description: Correction page — the Auditor test suite previously documented here targeted a chain-of-custody trace tool, snapshot verification tool, and shadow-drift audit that do not exist.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, test-scenarios, auditor, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Test Scenarios — Auditor (correction)

> **At a Glance**
> **Status:** corrected 2026-07-22 — the scenarios previously on this page (lot-level chain-of-custody trace tool, period-end snapshot verification tool, FIFO-vs-Average shadow-drift audit, configuration-history audit) targeted surfaces with **no source backing** and were removed rather than re-fabricated.

## 1. Why these scenarios were removed

- **No Auditor role or permission key exists** (`enum_stage_role` has no `auditor` member; no auditor-scoped key in `constant/permissions.ts`).
- **No chain-of-custody trace tool, snapshot-verification tool, or shadow-drift tool exists anywhere in the frontend** — this mirrors the identical finding on [inventory/03-user-flow-audit-config](/en/inventory/inventory/03-user-flow-audit-config): "No dedicated audit-only screen or permission distinct from `inventory_management.view` was found."
- **The GL and `COST_VAL_009` claims the audit checklist relied on do not exist** — see [02-business-rules](./02-business-rules.md) §§ 2, 4, 6.

## 2. Where the testable behaviour lives now

| Formerly tested here | Real test location |
|---|---|
| Cost-flow chain-of-custody trace | No in-app tool; the closest real screen is the read-only [inventory/transaction](/en/inventory/inventory/transaction) log |
| Period-snapshot vs cost-layer reconciliation | Would be a manual query against [01-data-model](./01-data-model.md) § 2.1 / § 2.3 — no in-app tool found |
| FIFO-vs-Average shadow-drift audit | The `average_cost_per_unit` shadow column is real (Section 2.6 of [01-data-model](./01-data-model.md)) but no drift-audit tool reads it |
| Configuration-history audit | No configuration-history feed found for `calculation_method` in this pass |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` — no audit-specific controller found for cost-layer data.
- Parent overview: [04-test-scenarios](./04-test-scenarios.md); user-flow counterpart: [03-user-flow-auditor](./03-user-flow-auditor.md).
- Cross-link: [inventory/04-test-scenarios-audit-config](/en/inventory/inventory/04-test-scenarios-audit-config) — the identical correction already made on the sibling module.
