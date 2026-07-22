---
title: Costing — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for costing.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Test Scenarios

> **At a Glance**
> **Module:** [costing](/en/inventory/costing) &nbsp;·&nbsp; **Total scenarios:** 11 cross-cutting engine scenarios (see Section 3) — no persona split
> **Run order:** none required — every scenario below is a direct consequence of an upstream document post; there is no separate costing-side approval sequence
> **Correction (verified 2026-07-22):** the ~102 scenarios previously spread across this page and three per-persona pages (Finance, Inventory Controller, Auditor) targeted screens that don't exist — a valuation-policy console, a GL reconciliation dashboard, a cost-pick-preview approval queue, an audit workspace. They are removed rather than re-fabricated; the three per-persona files are now correction pages (Section 2).

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `costing` module. Costing has no document lifecycle and no persona-gated screen of its own (see [03-user-flow](./03-user-flow.md)), so there is no "per-persona happy path" structure to test here — every cost-flow effect is a side effect of an upstream document post (GRN commit, SR issue, credit-note approval, inventory-adjustment creation, period-end close), each already covered by that document's own module. What's left to test **specifically at the costing layer** is the cost-pick arithmetic itself: does the engine pick the right lot, compute the right average, revalue the right row, and carry the right balance forward — independent of which document triggered it. Section 3 lists those scenarios directly (no persona column, since none of them are gated by anything beyond the triggering document's own permission).

## 2. Former Per-Persona Files (now corrections)

- [Finance scenarios](./04-test-scenarios-finance.md) — correction page.
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md) — correction page.
- [Auditor scenarios](./04-test-scenarios-auditor.md) — correction page.

## 3. Engine Scenarios

Each row is a self-contained cost-pick scenario. "Trigger" names the document action that invokes the engine — there is no separate costing-side actor to name, since the engine has no permission gate of its own beyond the trigger's.

| # | Scenario | Trigger | Pre-condition | Expected end state |
| - | -------- | ------- | -------------- | ------------------- |
| 1 | FIFO outbound spanning two lots | SR issue / stock-out exceeding the oldest lot's balance | Product at a FIFO-method business unit; two existing lots at the source location with different `lot_seq_no` and `cost_per_unit`; issue qty larger than the oldest lot's remaining balance. | Single outbound `tb_inventory_transaction`; **two** outbound cost-layer rows — first consumes the oldest lot fully at its `cost_per_unit`, second consumes the remainder from the next-oldest lot per `COST_CALC_001` / `COST_POST_002`. |
| 2 | Average inbound recompute | GRN commit | Product at an Average-method business unit; existing on-hand at one cost; new GRN receipt at a different cost. | GRN commit writes the inbound cost-layer row; `average_cost_per_unit = (prior_on_hand × prior_average + in_qty × in_cost) / (prior_on_hand + in_qty)` per `COST_CALC_003`; the subsequent outbound at this `(location, product)` reads the new average. |
| 3 | Credit-note-amount revaluation | Credit-note approval (`procurement.credit_note`) | `committed` GRN exists with a lot at `cost_per_unit = X`; vendor concedes a `−฿100` price reduction post-receipt; credit-note raised at `pending`. | On approval: cost-layer row written with `in_qty = 0, out_qty = 0, diff_amount = −฿100, transaction_type = credit_note_amount`; originating lot's `cost_per_unit` recalculated per `COST_CALC_005`; downstream FIFO consumption from the lot picks up the revalued cost; already-consumed portions are **not** retroactively adjusted. No GL entry — none exists. |
| 4 | Count-variance valuation by configured method | Physical-count / spot-check variance rollup (see that module's own resync for whether it actually reaches the ledger) | Tenant configured `enum_physical_count_costing_method = last_receiving`. | Count-derived line's `cost_per_unit` resolved by `COST_CALC_008` reading the most recent inbound layer at `(location, product)`. |
| 5 | Period-end close (FIFO) — no snapshot written | `inventory_management.period_end.execute` → Close period | Closing period at `open`; all blocking documents terminal, physical counts complete; FIFO business unit with residual lots at multiple `(location, product)` keys. | `close_period` / `open_period` cost-layer rows carry every residual lot forward with `lot_seq_no` preserved (`COST_POST_007` / `COST_POST_008`). **No `tb_period_snapshot` row is written** — confirm this directly, since it is easy to assume the snapshot table is written on every close. |
| 6 | Period-end close (Average) — snapshot written | Same trigger, Average business unit | Closing period; running `average_cost_per_unit` per `(location, product)`. | `tb_period_snapshot` rows written per `(location, product)` with `closing_cost_per_unit = current_running_average`; single `open_period` cost-layer row per key carries the closing average into the next period. |
| 7 | Calculation-method change with non-zero on-hand — currently unguarded | Platform/cluster admin changes `tb_business_unit.calculation_method` | Business unit at `calculation_method = average` with non-zero on-hand for at least one product. | **No guard exists.** The save succeeds regardless of on-hand quantity — see [02-business-rules](./02-business-rules.md) § 2 (`COST_VAL_009` removed). New movements immediately apply the new method; existing cost-layer rows keep their already-picked cost. Worth testing precisely because a tester might expect this to be blocked. |
| 8 | Standard-cost update — no cost-layer effect | Product standard-cost edit | `tb_product.standard_cost` updated for a product; tenant `enum_physical_count_costing_method = standard`. | `tb_product.standard_cost` updated; **no cost-layer effect** (`COST_POST_010` — prospective only). Subsequent count-variance posts at the product pick the new value. |
| 9 | Transfer cost mismatch — rejected | Inter-location transfer post | Source location FIFO cost-pick produces `transfer_out.cost_per_unit = ฿10`; an attempt sets `transfer_in.cost_per_unit = ฿12`. | Rejected per `COST_VAL_010`: `transfer_in.cost_per_unit` must equal `transfer_out.cost_per_unit`. |
| 10 | Direct-location receipt — auto-issued, not held as inventory | GRN receipt to a `tb_location.location_type = direct` location | — | Inbound cost-layer row written, then an automatic offsetting outbound (`createDirectExpenseOut`) at the same cost under the same transaction header — net on-hand is zero. Direct receipts are excluded from the Average computation. No GL effect. |
| 11 | Store Requisition — cost pass-through, no re-average, no new lot | SR issue to a Direct or Consignment destination | Existing lot at the source location. | The engine is invoked (`COST_POST_002`) and picks the existing layer's cost, but does **not** re-average (Average method) and does **not** create a new FIFO layer — the outbound consumes the existing lot at its existing `cost_per_unit`. |

## 4. E2E Test Mapping

The costing module is **partially exercised** by the inventory + GRN + credit-note + SR Playwright specs. There is **no dedicated `costing.spec.ts`** because every cost-flow effect fans out from an upstream transaction post.

| Spec | Engine scenarios covered (Section 3) |
| ---- | ------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | Period-end list/permission/validation coverage exists; per this pass's reading of the spec file, the **Close workflow**, **Close action**, and **Detail page** describe blocks are explicitly labelled `Feature pending` / `Backend only` in the spec itself — the FIFO-vs-Average rollforward mechanics (Scenarios 5, 6) are **not** exercised end-to-end by this spec today, only its list/permission surface is. |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) | Inbound cost-layer writes on GRN commit are exercised indirectly through the Stock Movements describe block (Scenario 2, 10); no per-lot cost assertion confirmed in this pass. |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) | SR-driven outbound (Scenario 1, 11) exercised indirectly; no per-lot cost-layer assertion confirmed in this pass. |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) | Credit-note inventory effect (Scenario 3) exercised indirectly; cost-layer `diff_amount` assertion not confirmed in this pass. |

Treat every "exercised indirectly" row above as **not yet confirmed** at the cost-layer assertion level — the referenced specs exist and cover the source document's own flow, but this pass did not open each spec file to check whether it makes cost-layer-specific assertions (exact `cost_per_unit`, `lot_seq_no`, `diff_amount` values). Re-verify before citing any of these as "tested" in a QA plan. Scenarios 4, 7, 8, 9 have no confirmed E2E coverage at all in this pass — treat as manual / planned.

## 5. References

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — period-end E2E; several describe blocks explicitly marked pending in the spec file itself.
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts), [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts), [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — source-document specs whose Stock Movements / inventory-effect describe blocks indirectly exercise the engine.
- Sibling: [03-user-flow.md](./03-user-flow.md) — the corrected lifecycle and the correction notes for the three former persona pages.
- Sibling: [02-business-rules.md](./02-business-rules.md) — the validation, calculation, and posting rules each scenario above verifies.
- Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO and Average algorithm pseudocode plus numerical examples; the worked examples in [02-business-rules.md](./02-business-rules.md) § 3.1 / 3.2 align with the calculation-methods narrative.
- Former per-persona pages (now corrections): [Finance](./04-test-scenarios-finance.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Auditor](./04-test-scenarios-auditor.md).
