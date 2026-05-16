---
title: Inventory — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for inventory.
published: true
date: 2026-05-17T11:00:00.000Z
tags: inventory, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios

> **At a Glance**
> **Module:** [[inventory]] &nbsp;·&nbsp; **Total scenarios:** ~17 cross-persona + ~115 per-persona &nbsp;·&nbsp; **Personas covered:** Store Keeper, Inventory Controller, Finance, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `inventory` module. It groups coverage by the four personas that interact with inventory movements and period state (Store Keeper, Inventory Controller, Finance, Audit / Config), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and maps every cross-persona scenario back to the Playwright spec [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) (the canonical inventory-side E2E surface) plus the inventory-adjacent specs `720-stock-issue.spec.ts` (stock-out via the issue path) and `501-grn.spec.ts` Stock Movements describe block (inventory side of GRN commit). The scope is deliberately wider than a pure functional pass: each persona file includes **functional happy paths** (movement posts, period transitions, approvals), **RBAC / permission-denial cases** (Store Keeper attempts above-threshold approval, Controller attempts period lock, Sysadmin attempts to post a transaction), **edge cases** (concurrent posts, FIFO consumption spanning lots, weighted-average recompute on inbound, period-boundary movements, locked-period restatement), **count-variance posting** (overage / shortage / lot-mismatch), and **period-end orchestration** (close, open-next, lock, re-open within audit window).

The cross-persona scenarios in Section 4 are the integration layer above the per-persona suites. They describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Store Keeper raises stock-in → Inventory Controller approves → posts to inventory; Inventory Controller signs off variance → Finance reconciles → Finance Manager closes period → locks period*. Section 5 maps the inventory-relevant E2E describe blocks back to those journeys so gaps in automated coverage are visible; note that the inventory module is partially covered by the canonical E2E surfaces (period-end, stock-issue, and GRN stock-movement) — many fine-grained inventory-side concerns are validated through the upstream module specs, with the per-persona test files cataloguing scenarios that may be manual / planned.

## 2. Personas in Scope

- **Store Keeper**: floor-level operator who initiates `tb_stock_in` / `tb_stock_out` documents for routine non-GRN / non-SR adjustments and executes physical / spot counts at the location level.
- **Inventory Controller**: balance-accuracy owner who approves above-threshold adjustments, reviews and commits count-variance lines, maintains per-product / per-location stock policy, and signs off on variance before period close.
- **Finance**: valuation authority who approves above-Controller-threshold adjustments, runs the inventory-to-GL reconciliation, orchestrates the period-end run (close + open-next), and (as Finance Manager) advances `tb_period.status` from `closed` to `locked`.
- **Audit / Config**: System Administrator who owns `tb_location` / costing-method / `tb_adjustment_type` / period / threshold / RBAC / integration config, and Auditor who runs read-only audit-log queries, lot-recall traces, and period-snapshot reconciliation queries.

## 3. Persona Test Files

- [Store Keeper scenarios](./04-test-scenarios-store-keeper.md)
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the system in a terminal or steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the system state required to begin; "Expected end state" anchors the inventory transaction posting, cost-layer / on-hand effect, and period state.

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Routine inbound stock-in (below threshold, auto-approve) | Store Keeper | Source: found-stock for an existing lot; `tb_user_location` scope present; total cost impact below the tenant Store-Keeper auto-approve threshold; period `open`. | `tb_stock_in.doc_status = completed`; one `tb_inventory_transaction` row (`inventory_doc_type = stock_in`, `enum_transaction_type = adjustment_in`); one inbound cost-layer row (`in_qty > 0`); on-hand at `(location, product, lot)` advances; no handoff. |
| 2 | Above-threshold stock-out routes to Inventory Controller | Store Keeper → Inventory Controller | Source: breakage write-off; total cost impact above auto-approve threshold but below Finance threshold; period `open`. | After Controller approval: `tb_stock_out.doc_status = completed`; one outbound `tb_inventory_transaction`; outbound cost-layer (FIFO or WA cost pick depending on product); on-hand reduced. Activity log records `{ actor: controller, action: 'approve_post' }`. |
| 3 | Large-cost adjustment routes Controller → Finance | Store Keeper → Inventory Controller → Finance | Source: recall write-off; total cost impact above Controller threshold; period `open`. | After Finance approval: `tb_stock_out.doc_status = completed`; outbound inventory transaction; cost-layer rows; on-hand reduced. GL entry posts to the recall-write-off account per the adjustment reason code. |
| 4 | Physical count with variance — overage and shortage lines | Store Keeper → Inventory Controller | Scheduled count for `tb_location.physical_count_type = yes`; count document at `tb_count_stock.status = completed` with variance lines; some overage, some shortage; aggregate cost below Controller threshold. | On Controller commit-of-count: rollup `tb_stock_in` (overage) + `tb_stock_out` (shortage) auto-advance to `completed`; one or more inventory transactions per rollup; cost-layer rows; on-hand reconciled to counted qty; count document at `completed_posted`. |
| 5 | Period-end happy path (no variance, no holds) | Inventory Controller → Finance → Finance Manager | All in-flight adjustments / counts / GRNs / SRs for the period at terminal state; Controller variance sign-off done; inventory-to-GL reconciliation passes. | Finance runs close: `tb_period.status = open → closed`; `tb_period_snapshot` rows written per `(period, location, product, lot)`; `close_period` + `open_period` cost-layer rows written; next period at `open`. After audit window: Finance Manager runs lock — `tb_period.status = closed → locked`. |
| 6 | Period-end variance-flagged hold | Inventory Controller → Finance | Pending count variance line at `investigate` flag from a prior count run; Controller has not signed off the period. | Finance close run **blocked** — Controller has not signed off the variance. Finance communicates the hold; Controller resolves the investigation; signs off; Finance re-runs close. |
| 7 | FIFO outbound spanning two lots | Store Keeper (via SR) | Product with `costing_method = FIFO`; two existing lots at the source location with different `lot_seq_no` and different `cost_per_unit`; SR-approved issue for a qty larger than the oldest lot's balance. | Single outbound `tb_inventory_transaction`; **two** outbound cost-layer rows — one consuming the oldest lot fully at its `cost_per_unit`, one consuming the remainder from the next-oldest lot at its `cost_per_unit`. On-hand reduced accordingly per `INV_CALC_005`. |
| 8 | Weighted-average inbound recompute | Store Keeper (via GRN) | Product with `costing_method = WEIGHTED_AVERAGE`; existing on-hand at one cost; new GRN receipt at a different cost. | GRN commit writes inbound inventory transaction; cost-layer row carries new `cost_per_unit` and recomputed `average_cost_per_unit = (prior_on_hand × prior_average + in_qty × in_cost) / (prior_on_hand + in_qty)` per `INV_CALC_007`. Subsequent outbound at this location reads the new average. |
| 9 | Concurrent inbound to same location / product / lot | Store Keeper (×2) | Two sessions / Store Keepers post inbound to the same `(location, product, lot)` simultaneously (e.g. two GRN commits in the same minute, or two count-overage stock-ins). | Both inventory transactions post successfully (no row-level lock conflict because inserts are append-only); cost-layer rows for both ordered by `lot_seq_no`; on-hand at `(location, product, lot)` advances by the sum. FIFO ordering preserved; weighted-average recomputed sequentially. |
| 10 | Negative-balance attempt rejected | Store Keeper | Outbound stock-out attempted for qty larger than the current `(location, product, lot)` on-hand; tenant policy is "no negative balance" (default per `INV_VAL_005`). | Submit rejected pre-post with `"Outbound movement would drive on-hand at (location, product, lot) below zero. Available: X, requested: Y."` Document stays at `draft`; no inventory transaction written; Store Keeper either reduces qty, picks a different lot, or escalates to Controller. |
| 11 | Backdated post into a closed period rejected | Store Keeper / Inventory Controller / Finance | Source document with a transaction date inside a `closed` period; user attempts to submit / approve. | Submit / approve rejected per `INV_VAL_008` with `"Cannot post into period <YYMM>: period is closed. Re-open the period or post a current-period restatement."` No inventory transaction written. Finance Manager re-open is an audit-logged elevated action; `locked` periods cannot be re-opened. |
| 12 | Credit-note amount adjustment — post-receipt price reduction | Finance | `committed` GRN exists; vendor concedes a price reduction post-receipt; credit-note (`tb_credit_note`) approved at Finance. | `tb_inventory_transaction` written (`inventory_doc_type = credit_note`, `enum_transaction_type = credit_note_amount`); cost-layer row with `in_qty = out_qty = 0`, `diff_amount = signed_amount`; originating lot's `cost_per_unit` adjusted per `INV_CALC_011`; downstream consumption from the lot picks up the revalued cost. |
| 13 | Lot-recall trace — chain-of-custody from GRN to consumption | Audit / Config (Auditor) | A lot affected by a vendor recall; the lot was introduced by a `committed` GRN, partially issued via SR, partially written off via stock-out, with a credit-note amount adjustment applied. | Backward trace returns the GRN that introduced the lot. Forward trace returns all downstream movements consuming from the lot: SR issues, stock-out write-offs, credit-note quantity adjustments. Chain-of-custody report renders both directions; no transaction state change. |
| 14 | Direct-cost location receipt (no balance impact) | Store Keeper | GRN receipt to a location with `tb_location.location_type = direct` (e.g. a kitchen station); product receipt qty positive. | `tb_inventory_transaction` written for audit; **no cost-layer row** per `INV_POST_003`; GL: `Dr Department Expense / Cr AP` directly; no on-hand at the direct location (direct locations carry no balance). |
| 15 | Consignment location receipt (memo only) | Store Keeper | GRN receipt to a `location_type = consignment` location; vendor-owned stock. | `tb_inventory_transaction` written; consignment-flagged cost-layer row written (memo register); **no Inventory asset debit, no AP credit at receipt** per `INV_POST_004`. On consumption (separate scenario), AP and COGS post simultaneously per `INV_POST_005`. |
| 16 | Sysadmin location-type change blocked by non-zero on-hand | Audit / Config (Sysadmin) | Existing `inventory`-type location with non-zero on-hand; Sysadmin attempts to change `location_type` to `direct`. | Impact preview rejects per `INV_AUTH_008` drain requirement; configuration not saved; Sysadmin must drain the on-hand first (transfer / write off) before re-attempting. |
| 17 | Period re-open (audit-window correction) | Finance Manager | Period at `tb_period.status = closed`, within the audit window; external auditor identifies an exceptional adjustment required. | Finance Manager re-opens (`closed → open`) per `INV_AUTH_006` with audit-grade justification; the corrective adjustment posts as a new movement in the re-opened period; Finance re-closes the period before next-period close. Audit log records the re-open and re-close. |

## 5. E2E Test Mapping

The inventory module is **partially exercised** by three Playwright spec files; there is no single `inventory.spec.ts` covering all inventory paths because most inventory effects fan out from upstream document commits. Coverage is therefore distributed.

| Spec / describe block | Cross-persona scenarios covered (Section 4) |
| --------------------- | ------------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | 5 (period-end happy path), 6 (variance-flagged hold), 11 (backdated-post rejection), 17 (period re-open) |
| [`720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) | 2 (Store-Keeper-initiated stock-out below Finance threshold), 7 (FIFO outbound spanning lots), 10 (negative-balance rejection) |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Stock Movements describe block (TC-GRN-900014) | 1 (routine inbound from a GRN commit — inventory-side effect of GRN), 8 (weighted-average inbound recompute on GRN commit), 9 (concurrent inbound on GRN commit), 14 (direct-cost location receipt), 15 (consignment location receipt) |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Commit / Void describe blocks (TC-GRN-900011, TC-GRN-900012) | 1, 14, 15 (inventory-side effect of commit and void) |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) (credit-note module) | 12 (credit-note amount adjustment — inventory-side effect) |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) (store-requisition module) | 2, 7 (SR-driven outbound and FIFO consumption) |

Gaps relative to Section 4:

- Scenario 3 (Controller → Finance large-cost approval chain) is not covered by a single spec; the approval-routing pieces live in the source-module specs (stock-in flow, stock-out flow) and the inventory effect is observed indirectly through stock-movement assertions.
- Scenario 4 (physical-count variance commit) is covered partially in the count module specs (not yet linked here); the inventory-side rollup posting is a manual / planned test.
- Scenario 13 (lot-recall trace) lives in the audit module's specs (outside the inventory module spec set); read-only audit-query specs are typically planned manual tests in the Auditor persona file.
- Scenario 16 (Sysadmin location-type change) lives in the location-config admin spec (`080-location.spec.ts`); the inventory-side blocker is a manual / planned validation.

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — canonical period-end E2E.
- [`../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) — stock-out / stock-issue path; inventory outbound surface.
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — GRN commit inventory-side effect (Stock Movements describe block).
- [`../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) — credit-note inventory effects.
- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — store-requisition inventory effects.
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation (Section 2), calculation (Section 3), authorization (Section 4), posting (Section 5), and cross-module (Section 6) rules invoked by every scenario above.
- Per-persona detail: [Store Keeper](./04-test-scenarios-store-keeper.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md).
