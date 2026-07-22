---
title: Costing — User Flow — Auditor (correction)
description: Correction page — no read-only audit workspace, chain-of-custody trace tool, or FIFO-vs-Average shadow-drift audit screen exists in the costing module.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, auditor, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — User Flow — Auditor (correction)

> **At a Glance**
> **Status:** corrected 2026-07-22 — the Auditor persona and its dedicated "costing audit workspace" (chain-of-custody trace tool, period-end snapshot verification tool, FIFO-vs-Average shadow-drift audit, configuration-history audit) previously documented here **does not exist in the product**.
> **What is real:** the underlying data is readable through the same screens every other user reads from — the Transaction Log, the period-end review, and the [reporting-audit](/en/inventory/reporting-audit) activity log — none of them gated by an "Auditor" role.

## 1. What this page previously claimed, and why it was removed

An earlier draft described a strictly-read-only Auditor persona running three dedicated tools: a lot-level cost-flow chain-of-custody trace (forward and backward through `tb_inventory_transaction_cost_layer`), a period-end snapshot verification tool (independently reconstructing `tb_period_snapshot` from the cost-layer ledger), and a FIFO-vs-Average shadow-drift audit. Verification against current source found none of it:

- **No Auditor role or permission key exists.** `enum_stage_role` has no `auditor` member; no auditor-scoped key exists in `constant/permissions.ts`. This mirrors the identical finding on [inventory/03-user-flow-audit-config](/en/inventory/inventory/03-user-flow-audit-config) (already corrected): "No dedicated audit-only screen or permission distinct from `inventory_management.view` was found in this module."
- **No chain-of-custody trace tool, snapshot-verification tool, or shadow-drift tool exists anywhere in the frontend.** These were fully invented UI concepts with no matching route or component.
- **The "GL absorbs the difference" / "GL Inventory control-account" claims this page's audit checklist relied on do not exist** — see [02-business-rules](./02-business-rules.md) § 4/§ 6 corrections; there is no GL to audit against.
- **The `COST_VAL_009` method-change-drain guard this page's configuration-history audit checked for does not exist in code** — see [02-business-rules](./02-business-rules.md) § 2 correction.

## 2. Where the real behaviour lives

| Formerly claimed here | Actual mechanism | Page |
|---|---|---|
| Auditor runs a lot chain-of-custody trace | The Transaction Log (`/inventory-management/transaction`) is the closest real screen — a filterable, read-only ledger view open to anyone with `inventory_management.view` | [inventory/transaction](/en/inventory/inventory/transaction) |
| Auditor verifies `tb_period_snapshot` against the cost-layer ledger | No in-app reconciliation tool exists; this would be a manual query against the two tables described in [costing/01-data-model](/en/inventory/costing/01-data-model) § 2.1/2.3 | [costing/01-data-model](/en/inventory/costing/01-data-model) |
| Auditor audits configuration-change history for `calculation_method` | No configuration-history feed was found for this field in this pass | — |
| Auditor reviews activity for audit purposes | The real activity/audit-log surface lives in [reporting-audit](/en/inventory/reporting-audit), gated the same way as everything else, not by an Auditor role | [reporting-audit/activity](/en/inventory/reporting-audit/activity) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` — no audit-specific controller found for cost-layer data.
- Parent overview: [03-user-flow](./03-user-flow.md).
- Cross-link: [inventory/03-user-flow-audit-config](/en/inventory/inventory/03-user-flow-audit-config) — the identical correction already made on the sibling module.
- Cross-link: [reporting-audit](/en/inventory/reporting-audit) — the real activity-log surface, generically permissioned.
