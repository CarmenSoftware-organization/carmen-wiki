---
title: Costing — Test Scenarios
description: 11 cross-cutting cost-pick engine scenarios and E2E mapping for costing — no persona split, see the three correction pages for what was removed.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: costing, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Test Scenarios

> **At a Glance**
> **Module:** [costing](/en/inventory/costing) &nbsp;·&nbsp; **Total scenarios:** 14 cross-cutting engine scenarios (see Section 3) — no persona split
> **Run order:** none required — every scenario below is a direct consequence of an upstream document post; there is no separate costing-side approval sequence
> **Correction (verified 2026-07-22):** the ~102 scenarios previously spread across this page and three per-persona pages (Finance, Inventory Controller, Auditor) targeted screens that don't exist — a valuation-policy console, a GL reconciliation dashboard, a cost-pick-preview approval queue, an audit workspace. They are removed rather than re-fabricated; the three per-persona files are now correction pages (Section 2).
> **Re-verified 2026-09-22:** scenarios 2, 5, 6, 10 corrected (average per product at 2 dp and posted at GRN **save**; snapshot table renamed; direct receipts); scenarios 12–14 added (landed cost with extra cost + FOC; unwind of an average-unit GRN; period resolution by `grn_date`).

> **Executable coverage (E2E repo `../carmen-inventory-frontend-e2e/`):** there is **no** `costing` catalog page, gap report, or spec — `docs/test-cases/COVERAGE.md` has no costing route. The nearest executable coverage is `tests/501-grn.spec.ts` (76 cases; Stock Movements group), `tests/601-cn.spec.ts`, `tests/701-sr.spec.ts`, `tests/900-period-end.spec.ts`, and the gap reports `docs/test-cases/gaps/501-grn-core-gap.md` (62) / `501-grn-from-po-gap.md` (24). None asserts a cost-layer value. This page does not mirror them.

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
| 2 | Average inbound recompute | GRN **save** (`draft → saved`) on an average unit | Product at an Average-method business unit; existing net on-hand 100 @ ฿10.00 (any location); new GRN receipt 50 @ landed ฿14.00. | **Save**, not commit, writes the inbound cost-layer row (`tb_inventory_transaction.info.posted_at_save = true`); `average_cost_per_unit = Round2((1,000 + 700) / 150) = ฿11.33` per `COST_CALC_003`, stamped on the new layer **and every existing live layer of the product at every location**; a subsequent issue at any location reads ฿11.33. Commit then advances the PO without a second ledger write. |
| 3 | Credit-note-amount revaluation | Credit-note approval (`procurement.credit_note`) | `committed` GRN exists with a lot at `cost_per_unit = X`; vendor concedes a `−฿100` price reduction post-receipt; credit-note raised at `pending`. | On approval: cost-layer row written with `in_qty = 0, out_qty = 0, diff_amount = −฿100, transaction_type = credit_note_amount`; originating lot's `cost_per_unit` recalculated per `COST_CALC_005`; downstream FIFO consumption from the lot picks up the revalued cost; already-consumed portions are **not** retroactively adjusted. No GL entry — none exists. |
| 4 | Count-variance valuation by configured method | Physical-count / spot-check variance rollup (see that module's own resync for whether it actually reaches the ledger) | Tenant configured `enum_physical_count_costing_method = last_receiving`. | Count-derived line's `cost_per_unit` resolved by `COST_CALC_008` reading the most recent inbound layer at `(location, product)`. |
| 5 | Period-end close (FIFO) — no snapshot written | `inventory_management.period_end.execute` → Close period | Closing period at `open`; all blocking documents terminal, physical counts complete; FIFO business unit with residual lots at multiple `(location, product)` keys. | `close_period` / `open_period` cost-layer rows carry every residual lot forward with `lot_seq_no` preserved (`COST_POST_007` / `COST_POST_008`). **No `tb_inventory_period_snapshot` row is written** — confirm this directly, since it is easy to assume the snapshot table is written on every close. |
| 6 | Period-end close (Average) — snapshot written | Same trigger, Average business unit | Closing period; product-wide `average_cost_per_unit` stamped on every layer. | `tb_inventory_period_snapshot` rows written per `(location, product)` with `closing_cost_per_unit = current average`; single `open_period` cost-layer row per key carries the closing average into the next period. |
| 7 | Calculation-method change with non-zero on-hand — currently unguarded | Platform/cluster admin changes `tb_business_unit.calculation_method` | Business unit at `calculation_method = average` with non-zero on-hand for at least one product. | **No guard exists.** The save succeeds regardless of on-hand quantity — see [02-business-rules](./02-business-rules.md) § 2 (`COST_VAL_009` removed). New movements immediately apply the new method; existing cost-layer rows keep their already-picked cost. Worth testing precisely because a tester might expect this to be blocked. |
| 8 | Standard-cost update — no cost-layer effect | Product standard-cost edit | `tb_product.standard_cost` updated for a product; tenant `enum_physical_count_costing_method = standard`. | `tb_product.standard_cost` updated; **no cost-layer effect** (`COST_POST_010` — prospective only). Subsequent count-variance posts at the product pick the new value. |
| 9 | Transfer cost mismatch — rejected | Inter-location transfer post | Source location FIFO cost-pick produces `transfer_out.cost_per_unit = ฿10`; an attempt sets `transfer_in.cost_per_unit = ฿12`. | Rejected per `COST_VAL_010`: `transfer_in.cost_per_unit` must equal `transfer_out.cost_per_unit`. |
| 10 | Direct-location receipt — auto-issued, not held as inventory | GRN receipt to a `tb_location.location_type = direct` location | — | Inbound cost-layer row written, then an automatic offsetting outbound (`createDirectExpenseOut`) at the same cost under the same transaction header — net on-hand is zero. Direct receipts are excluded from the Average computation and their layers carry `average_cost_per_unit = 0`. No GL effect. |
| 11 | Store Requisition — cost pass-through, no re-average, no new lot | SR issue to a Direct or Consignment destination | Existing lot at the source location. | The engine is invoked (`COST_POST_002`) and picks the existing layer's cost, but does **not** re-average (Average method) and does **not** create a new FIFO layer — the outbound consumes the existing lot at its existing `cost_per_unit`. |
| 12 | Landed cost — extra cost and FOC in the layer | GRN commit (FIFO) / save (average) | Extra-cost header `by_value` with details summing ฿200 (document currency, `exchange_rate = 1`); line A `received_base_qty = 10`, `foc_base_qty = 1`, `base_net_amount = ฿1,192.25`; line B `received_base_qty = 4`, `base_net_amount = ฿356.00`. | Shares `200 × 11/15 = ฿146.67` (A) and `200 × 4/15 = ฿53.33` (B) (`by_value` weights by stock qty incl. FOC); A: `qty = 11`, `cost_per_unit = Round2(1,338.92 / 11) = ฿121.72`, layer `extra_cost_amount ≈ 146.67`; B: `qty = 4`, `cost_per_unit = Round2(409.33 / 4) = ฿102.33`. With `by_qty`: ฿100 each; with `manual`: ฿0 each. `Σ extra_cost_amount` across the GRN's layers = ฿200.00. |
| 13 | Unwind an average-unit GRN before commit | Void / reject / qty edit of a `saved` GRN on an average unit | Scenario 2 state (movement posted at save). (a) Nothing consumed. (b) A store requisition consumed 20 of the 50 received units. | (a) Movement header and its layers soft-deleted, `detail_item.inventory_transaction_id` cleared, product average re-stamped back to ฿10.00; an edit re-posts a fresh movement with the new figures. (b) `GRN_RECEIPT_ALREADY_CONSUMED` (409); nothing changes. FIFO units: nothing to unwind before commit. |
| 14 | Period resolution by receipt date | GRN commit / approve (any unit), save (average unit) | `grn_date` inside a `closed` period, or a date no period covers; another period is `open`. | `GRN_DATE_OUTSIDE_OPEN_PERIOD` (422) — the movement is **not** re-dated into the open period (`resolvePeriodForDate` vs `resolveCurrentPeriod`). A `grn_date` on the last day of an open period is accepted (day-level comparison). A period named e.g. `4904` spanning 2026-03-31…2049-04-30 is matched by range, not by the `YYMM` label; the layer's `at_period` copies that label. |

## 4. E2E Test Mapping

The costing module is **partially exercised** by the inventory + GRN + credit-note + SR Playwright specs. There is **no dedicated `costing.spec.ts`** because every cost-flow effect fans out from an upstream transaction post.

| Spec | Engine scenarios covered (Section 3) |
| ---- | ------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | Period-end list/permission/validation coverage exists; per this pass's reading of the spec file, the **Close workflow**, **Close action**, and **Detail page** describe blocks are explicitly labelled `Feature pending` / `Backend only` in the spec itself — the FIFO-vs-Average rollforward mechanics (Scenarios 5, 6) are **not** exercised end-to-end by this spec today, only its list/permission surface is. |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) | Inbound cost-layer writes on GRN commit are exercised indirectly through the Stock Movements describe block (Scenarios 2, 10, 12 — the tab only renders for `committed` GRNs and calls the real `GET …/stock-movements`); 57 of the spec's 76 cases have no assertion (`docs/test-cases/SPEC-HEALTH.md`), so no per-lot cost assertion exists. |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) | SR-driven outbound (Scenario 1, 11) exercised indirectly; no per-lot cost-layer assertion confirmed in this pass. |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) | Credit-note inventory effect (Scenario 3) exercised indirectly; cost-layer `diff_amount` assertion not confirmed in this pass. |

Treat every "exercised indirectly" row above as **not yet confirmed** at the cost-layer assertion level — the referenced specs exist and cover the source document's own flow, but none makes cost-layer-specific assertions (exact `cost_per_unit`, `lot_seq_no`, `extra_cost_amount`, `diff_amount` values). Re-verify before citing any of these as "tested" in a QA plan. Scenarios 4, 7, 8, 9, 12, 13, 14 have no E2E coverage at all — treat as manual / API-level (`GET …/good-received-notes/:id/stock-movements` and `GET …/cost/products/:id/last-cost` are the read paths to assert against).

## 5. References

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — period-end E2E; several describe blocks explicitly marked pending in the spec file itself.
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts), [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts), [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — source-document specs whose Stock Movements / inventory-effect describe blocks indirectly exercise the engine.
- Sibling: [03-user-flow.md](./03-user-flow.md) — the corrected lifecycle and the correction notes for the three former persona pages.
- Sibling: [02-business-rules.md](./02-business-rules.md) — the validation, calculation, and posting rules each scenario above verifies.
- Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO and Average algorithm pseudocode plus numerical examples; the worked examples in [02-business-rules.md](./02-business-rules.md) § 3.1 / 3.2 align with the calculation-methods narrative.
- Former per-persona pages (now corrections): [Finance](./04-test-scenarios-finance.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Auditor](./04-test-scenarios-auditor.md).
