---
title: Costing — Test Scenarios — Finance (correction)
description: Correction page — the Finance test suite previously documented here targeted surfaces (valuation-policy console, GL reconciliation, credit-note approval queue, period lock) that do not exist.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Test Scenarios — Finance (correction)

> **At a Glance**
> **Status:** corrected 2026-07-22 — the ~34 scenarios previously on this page (credit-note approval queue, sub-ledger ↔ GL reconciliation with tolerances and compensating journals, period-end orchestration, Finance-Manager-only period lock/re-open, standard-cost cadence) targeted surfaces with **no source backing** and were removed rather than re-fabricated.

## 1. Why these scenarios were removed

- **No Finance role or permission key exists** (`enum_stage_role` has no `finance` member; no finance-scoped key in `constant/permissions.ts`).
- **No GL/journal, reconciliation, or tolerance code exists** anywhere in `carmen-turborepo-backend-v2` — the planning-stage design doc these rules were built on top of (`../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/proc-03-cost-calculation.md`) states directly, in its own text, that it "does not generate GL journal entries."
- **No code-enforced "method locked, drain required" guard exists** — see [02-business-rules](./02-business-rules.md) § 2 (`COST_VAL_009` removed).
- **No lock/re-open endpoint exists in this module** (`period-end.controller.ts`: `find-all` / `find-current` / `close` / `find-review` only).

This mirrors the confirmed-fabricated Finance persona findings in [inventory/04-test-scenarios-finance](/en/inventory/inventory/04-test-scenarios-finance), purchase-order, good-receive-note, and store-requisition.

## 2. Where the testable behaviour lives now

| Formerly tested here | Real test location |
|---|---|
| Credit-note-amount revaluation happy path | [04-test-scenarios](./04-test-scenarios.md) Scenario 3 |
| Period-end close (FIFO / Average) happy path / blocked | [04-test-scenarios](./04-test-scenarios.md) Scenarios 5, 6; [inventory/04-test-scenarios-inventory-controller](/en/inventory/inventory/04-test-scenarios-inventory-controller) for the review-checklist gating |
| Calculation-method change | [04-test-scenarios](./04-test-scenarios.md) Scenario 7 — now documented as **unguarded**, not blocked |
| Standard-cost update | [04-test-scenarios](./04-test-scenarios.md) Scenario 8 |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts`, `.../inventory-transaction/inventory-transaction.service.ts`.
- Parent overview: [04-test-scenarios](./04-test-scenarios.md); user-flow counterpart: [03-user-flow-finance](./03-user-flow-finance.md).
