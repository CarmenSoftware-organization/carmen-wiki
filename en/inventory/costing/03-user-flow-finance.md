---
title: Costing — User Flow — Finance (correction)
description: Correction page — no Finance role, valuation-policy console, GL reconciliation dashboard, or period-lock flow exists in the costing module.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — User Flow — Finance (correction)

> **At a Glance**
> **Status:** corrected 2026-07-22 — the Finance persona flow previously documented here (a valuation-policy console, a sub-ledger ↔ GL reconciliation dashboard, a credit-note revaluation approval queue, a period-end valuation orchestration dashboard, and a Finance-Manager-only period-lock dashboard) **does not exist in the product**.
> **What is real:** whoever holds `inventory_management.period_end.execute` runs the period-end close (documented on [inventory/period-end](/en/inventory/inventory/period-end) and [inventory/03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller)); credit-notes are approved under the generic `procurement.credit_note` permission with no finance-specific gate.

## 1. What this page previously claimed, and why it was removed

An earlier draft described a Finance Officer / Cost Controller / Finance Manager persona spanning five threads: owning the FIFO-vs-Average valuation policy per business unit, running a periodic inventory-sub-ledger ↔ GL reconciliation with configurable tolerance, approving credit-note-amount revaluations with a GL `Dr AP / Cr Inventory` posting, orchestrating the period-end close, and — as Finance Manager — advancing the period from `closed` to a permanently `locked` state. Verification against current source found none of it:

- **No Finance role or permission key exists.** `enum_stage_role` (the only workflow-role enum in the tenant schema) is `{create, approve, purchase, issue, view_only}` — no `finance` member. `constant/permissions.ts` in the frontend has no finance-scoped key anywhere near period-end or credit-note.
- **No GL/journal code exists anywhere in the backend.** A repo-wide search of `carmen-turborepo-backend-v2` for journal/ledger posting from cost-layer writes found nothing. The planning-stage design document this module's rules cite (`../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/proc-03-cost-calculation.md`) states this directly in its own text: **"Does not generate GL journal entries (separate accounting integration — TBC)."**
- **No reconciliation dashboard, tolerance, or compensating-journal mechanism exists.** Nothing in `inventory-transaction.service.ts` or `period-end.service.ts` compares cost-layer activity against any external ledger.
- **No "method locked, drain required to change" guard exists.** The planning doc records this as a stakeholder-confirmed *design intent* (P4 Q1), but `tb_business_unit.calculation_method`'s write path (`platform_business-units.controller.ts`, platform/cluster-admin surface) has no on-hand check anywhere.
- **No lock/reopen flow exists in this module.** `period-end.controller.ts` exposes only `find-all` / `find-current` / `close` / `find-review`. `enum_period_status.locked` is set by a separate `period` service behind [system-config/period](/en/inventory/system-config/period).

This mirrors the identical Finance-persona findings already confirmed in [inventory/03-user-flow-finance](/en/inventory/inventory/03-user-flow-finance), [purchase-order](/en/inventory/purchase-order/03-user-flow-finance), [good-receive-note](/en/inventory/good-receive-note/03-user-flow-finance), and [store-requisition](/en/inventory/store-requisition).

## 2. Where the real behaviour lives

| Formerly claimed here | Actual mechanism | Page |
|---|---|---|
| Finance owns the FIFO/Average valuation policy | Set once on `tb_business_unit.calculation_method` by a platform/cluster admin at business-unit setup — a single value for the whole business unit, no per-product override | [costing/01-data-model](/en/inventory/costing/01-data-model) § 2.4 |
| Finance runs sub-ledger ↔ GL reconciliation | No GL exists to reconcile against | [costing/02-business-rules](/en/inventory/costing/02-business-rules) § 6 (`COST_XMOD_009` removed) |
| Finance approves credit-note-amount revaluation | Approved under `procurement.credit_note`, same as any other credit-note; the cost-layer revaluation (`diff_amount`) is a side effect of that approval, not a separate finance-scoped action | [costing/02-business-rules](/en/inventory/costing/02-business-rules) § 3 `COST_CALC_005` |
| Finance orchestrates period-end close | Anyone with `inventory_management.period_end.execute` clicks **Close period** on `/inventory-management/period-end/review` | [inventory/period-end](/en/inventory/inventory/period-end) |
| Finance Manager locks the period after an audit window | `locked` is managed by the system-config period service, not here | [system-config/period](/en/inventory/system-config/period) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts` (the complete endpoint surface), `.../inventory-transaction/inventory-transaction.service.ts` (no GL fan-out).
- Planning doc (design intent, not verified-against-code): `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/proc-03-cost-calculation.md`.
- Parent overview: [03-user-flow](./03-user-flow.md).
- Cross-link: [inventory/03-user-flow-finance](/en/inventory/inventory/03-user-flow-finance) — the identical correction on the sibling module this engine plugs into.
