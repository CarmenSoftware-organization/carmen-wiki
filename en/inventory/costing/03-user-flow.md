---
title: Costing — User Flow
description: Cost-flow lifecycle and persona-specific flow files for costing.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — User Flow

> **At a Glance**
> **Module:** [costing](/en/inventory/costing) &nbsp;·&nbsp; **Personas:** none distinct — see the correction note below; the module has no persona-gated screen
> **Workflow lifecycle:** Cost-layer row born (inbound) → picked (FIFO/WA outbound) → revalued (credit-note) → period-close anchor (average-method only writes `tb_period_snapshot`; FIFO carries lots forward instead) → period-open rollforward.
> **Drill into per-persona pages below — each is a correction page pointing at the real behaviour**

> **Correction (verified 2026-07-22):** the three per-persona pages linked from Section 3 (Finance, Inventory Controller, Auditor) previously documented dedicated screens — a valuation-policy console, a sub-ledger ↔ GL reconciliation dashboard, an adjustment cost-pick-preview approval queue, a read-only audit workspace — none of which exist. The engine has **no persona-gated UI of its own**: it runs as a side effect of GRN commit, SR issue, inventory-adjustment creation, credit-note approval, and period-end close, each gated only by that source document's own generic permission. `enum_stage_role` (the only workflow-role enum in the tenant schema) is `{create, approve, purchase, issue, view_only}` — no `finance` or `auditor` member. This mirrors the identical correction already made on [inventory/03-user-flow](/en/inventory/inventory/03-user-flow), which found "no Finance role, GL reconciliation, or period-lock flow exists" for the same period-end surface this module's engine plugs into.

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `costing` module. Costing is unusual relative to its sibling document modules — there is no single workflow document on which a draft → saved → committed lifecycle plays out, and there is no separate document tree at all. Costing is a **behaviour layer over the inventory cost-layer ledger**, so the lifecycle to describe is the **lifecycle of a unit cost** at `(location_id, product_id, lot_no)`: it is **born** on an inbound `tb_inventory_transaction_cost_layer` row (a GRN receipt sets `cost_per_unit`; under Average the running average is recomputed), it is **picked** by every subsequent outbound (FIFO from oldest lot; Average at the prevailing running average), it is **revalued** by credit-note-amount adjustments (`diff_amount`), and — **on average-method business units only** — it is **rolled forward** at period close into the next period's opening cost and locked into `tb_period_snapshot`. FIFO-method business units carry residual lots forward as `close_period`/`open_period` cost-layer rows and never write a snapshot row at all.

Section 2 below describes the **cost-flow lifecycle** — the canonical set of legal transitions on a unit cost, from inbound creation through outbound consumption through period rollforward. There is no "persona's path through this state space" to document, because no persona-specific screen exists: whoever holds the relevant document's permission (GRN commit, SR approve, adjustment create, credit-note approve, or `inventory_management.period_end.execute`) triggers the same engine the same way. Section 3 links to the three correction pages that explain what was previously claimed and where the real behaviour actually lives. Section 4 has been reduced to the one real cross-module handoff this module participates in.

## 2. Cost-Flow Lifecycle

### 2.0 Transaction → Cost Engine Sequence

Costing has no per-document state machine (no `draft → saved → committed` lifecycle). The cost engine is invoked by inventory-affecting transactions. The diagram below is re-verified against `inventory-transaction.service.ts` and `period-end.close-transaction.helper.ts` / `period-end.close-average.helper.ts` directly; it mirrors the Process Execution Swim Lane design intent captured in the real planning-stage document set at `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/INDEX.md` and `proc-03-cost-calculation.md` (a requirements-gathering document, not a verified test spec — an earlier draft of this page cited this same set under a non-existent `Test_case/System_Process/` path with fabricated capture dates; see [02-business-rules](/en/inventory/costing/02-business-rules) § 5.1 for the correction).

```mermaid
sequenceDiagram
    participant TX as Trigger Transaction
    participant INV as ① Inventory Update
    participant LOT as ② Lot Management
    participant COST as ③ Cost Calculation

    Note over TX,COST: Stock-in — GRN · Stock In (adj)
    TX->>INV: +qty at inventory location
    INV->>LOT: New lot created; lot_seq_no assigned
    LOT->>COST: AVCO re-average (COST_CALC_003) / FIFO add cost layer (COST_CALC_004)

    Note over TX,COST: Stock-out — CRN · Issues · Sales Consumption · Stock Out (adj) · Wastage Report
    TX->>INV: -qty at inventory location
    INV->>LOT: Oldest lot consumed / closed (oldest lot_seq_no first)
    LOT->>COST: AVCO cost held at prevailing average (COST_CALC_002) / FIFO oldest layer consumed (COST_CALC_001)

    Note over TX,COST: SR — Store Requisition (internal transfer, any variant)
    TX->>INV: -qty inv source / +qty direct or consignment destination
    INV->>LOT: Lot consumed at inv source — no lot at destination
    Note over COST: Cost-pick (COST_POST_002): existing layer consumed at existing cost. No AVCO re-average. No new FIFO layer. See COST_XMOD_003.

    Note over TX,COST: Physical Count — variance exists
    TX->>INV: ±qty variance (physical count transaction type)
    INV->>LOT: Lots adjusted up (overage) or consumed down (shortage)
    LOT->>COST: Recalc only if variance exists — cost source per enum_physical_count_costing_method (COST_CALC_008)

    Note over TX,COST: Physical Count — no variance
    TX->>INV: Count confirmed, no qty change
    Note over LOT,COST: NOT triggered — no lot or cost-layer write

    Note over TX,COST: Credit-note-amount revaluation
    TX->>COST: diff_amount posted to originating lot (COST_POST_003 / COST_CALC_005)
    COST->>LOT: Originating lot cost_per_unit recalculated; downstream FIFO picks revalued cost

    Note over TX,COST: End Period Close
    TX->>INV: close_period / open_period cost-layer rows written for every residual lot (both methods)
    Note over INV,COST: Average-method business units only: tb_period_snapshot rows also written (COST_POST_007). FIFO-method business units write no snapshot row at all.
```

Two state machines coexist in this module: the **per-cost-layer-row** lifecycle (degenerate — each cost-layer row is written immutable at post time, optionally revalued via a `diff_amount` row, optionally rolled forward at period close) and the **per-period** lifecycle that mirrors the inventory module's `tb_period.status`. Within this module's own routes that status only ever moves `open → closed` — the `period-end.controller.ts` message-pattern surface is `find-all` / `find-current` / `close` / `find-review` only, with no lock/re-open action. A `locked` status value exists on the enum and is set by a **separate** `period` service backing the [system-config/period](/en/inventory/system-config/period) screen, outside this module. The transitions below cover both lifecycles as this module's own routes actually support them.

### 2.1 Cost-layer transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | inbound cost-layer write (engine picks inbound cost) | `posted` | Whoever holds the source document's own permission (GRN commit, SR-approved transfer-in, count overage, stock-in creation) — no separate costing-side gate | Source document reaches the point in its own flow where it posts to the ledger. Engine writes `cost_per_unit`, `average_cost_per_unit`, `lot_seq_no` per `COST_POST_001`. |
| `(none)` | outbound cost-layer write (engine picks outbound cost via FIFO / Average) | `posted` | Whoever holds the source document's own permission (SR issue, stock-out creation, credit-note-quantity) — no separate costing-side gate | Source document terminal; `COST_VAL_002` / `COST_VAL_003` pass (consumable layer exists); FIFO consumes by `lot_seq_no` asc producing 1+ rows; Average consumes at current average producing 1 row. Engine writes the outbound rows per `COST_POST_002`. |
| `posted` | credit-note-amount revaluation | `posted` (revalued — original row still present, new `diff_amount` row added) | Whoever holds `procurement.credit_note` approval permission | Originating lot identified; `COST_VAL_006` passes. Engine writes a new cost-layer row with `in_qty = out_qty = 0, diff_amount = signed_amount` per `COST_POST_003`. The originating lot's `cost_per_unit` is recalculated per `COST_CALC_005`; downstream consumption from the same lot picks up the revalued cost. Already-consumed portions are not retroactively adjusted. |
| `posted` | period-close anchor (`close_period`) | `posted` (anchored to period) | Whoever holds `inventory_management.period_end.execute` | Period being closed has all blocking documents terminal + physical counts complete (see [inventory/period-end](/en/inventory/inventory/period-end) § 2). Engine writes `close_period` cost-layer rows for every residual lot on **both** methods; **additionally** writes `tb_period_snapshot` rows on **average-method business units only** per `COST_POST_007`. |
| `posted` | period-open rollforward (`open_period`) | `posted` (rolled forward to next period) | System-invoked, chained inside the same close transaction | Engine writes `open_period` cost-layer rows for the next period at `cost_per_unit = previous.closing_cost_per_unit`, `lot_seq_no` preserved per `COST_POST_008`. FIFO sequence carries across the boundary. |
| `posted` | (no further direct action — terminal under normal flow) | `posted` | — | The cost-layer row is immutable; no update/patch endpoint exists on the cost-layer table. Revaluation only via the credit-note path or a compensating stock-in/stock-out. |

### 2.2 Per-period transitions (mirror of `tb_period.status`, within this module's own routes)

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create period | `open` | System-provisioned — `ensureNextPeriod` auto-creates the next period as part of every close | Fiscal year/month sequencing; no overlap with existing period rows. |
| `open` (or `locked`) | accept cost-layer writes | same | Whoever holds the triggering document's own permission | The engine writes cost-layer rows for any inventory transaction stamped into the currently-open period, regardless of the document's own date (`resolveCurrentPeriod` — a backdated document is re-dated into the open period, not rejected). |
| `open` (or `locked`) | close period | `closed` | Whoever holds `inventory_management.period_end.execute` | All blocking-document gates clear (see [inventory/period-end](/en/inventory/inventory/period-end) § 2). Runs atomically under a row lock with re-validation; writes lot carry-over; average-method tenants also get `tb_period_snapshot` rows; auto-provisions the next `open` period. This module's own routes (`period-end.controller.ts`) expose **only** `find-all` / `find-current` / `close` / `find-review` — there is no re-open or lock action here. |
| `closed` | — | — | — | `locked` is a status value this module can observe (period-end screens treat a `locked` period the same as `open` for the "current period" lookup) but does not set — it is written by a **separate** period service behind [system-config/period](/en/inventory/system-config/period), outside this wiki module's scope. |

## 3. Persona Index

Each linked page below is a **correction page** — it explains what was previously claimed for that "persona" and points to where the real, verified behaviour now lives. None of the three describes a screen that exists.

- [Finance](./03-user-flow-finance.md) — correction: no Finance role, valuation-policy console, GL reconciliation dashboard, or period-lock flow exists.
- [Inventory Controller](./03-user-flow-inventory-controller.md) — correction: no cost-pick-preview approval queue exists; [inventory-adjustment](/en/inventory/inventory-adjustment) documents that `tb_stock_in`/`tb_stock_out` post unconditionally on creation, with no reviewable pending state for any approver to act on.
- [Auditor](./03-user-flow-auditor.md) — correction: no read-only audit workspace, chain-of-custody trace tool, or shadow-drift audit screen exists.

## 4. Real Cross-Module Handoff

There is exactly one handoff worth documenting, and it isn't between personas — it's between modules:

| From | Trigger | To | System state at handoff |
| ---- | ------- | -- | ------------------------ |
| Any source document that posts a stock movement (GRN commit, SR issue, inventory-adjustment creation, credit-note approval) | The document reaches its own posting point | The costing engine (invoked synchronously, same call) | The engine writes the cost-layer row(s) as a side effect — there is no queue, no separate approval step, and no persona-specific review in between. |
| A movement lands in the currently-open period | — | Period-end close (`inventory_management.period_end.execute`) | Once all blocking documents clear and physical counts complete, closing the period carries every residual lot forward (both methods) and additionally snapshots `tb_period_snapshot` (average-method business units only). See [inventory/period-end](/en/inventory/inventory/period-end) § 2 for the full gate table — costing has no gates of its own beyond that page's. |

## 5. References

- `../carmen/docs/costing/enhanced-costing-engine.md` — recipe / portion / dynamic-pricing engine context; outside the cost-flow scope of this page.
- Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO vs Average algorithms, numerical examples, and the strategy-pattern design.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `tb_inventory_transaction_cost_layer`, `tb_period_snapshot`, `tb_business_unit.calculation_method`, `tb_product.standard_cost`, and the enums used in Section 2's transitions.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation, calculation, posting, and cross-module rules referenced by each transition row in Section 2, and the Section 4 correction on why there is no distinct authorization layer.
- Related: [inventory/03-user-flow](/en/inventory/inventory/03-user-flow) and [inventory/period-end](/en/inventory/inventory/period-end) — the movement-and-period lifecycle the costing engine plugs into; every cost-pick is triggered by an event on that lifecycle, and the real period-end close/gate mechanics live there, not duplicated here.
- Related modules: [good-receive-note](/en/inventory/good-receive-note) (the primary source of inbound cost-layer writes — GRN commit invokes `COST_POST_001` with the landed-cost-allocated unit price), [store-requisition](/en/inventory/store-requisition) (the primary source of outbound cost-pick — SR issue / transfer invokes `COST_POST_002`), [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check) (count-variance posts use `enum_physical_count_costing_method` to select the variance cost source per `COST_CALC_008`; spot-check does not post variance at all — see [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) § 5.1), [inventory-adjustment](/en/inventory/inventory-adjustment) (manual `tb_stock_in` / `tb_stock_out` — adjustment cost basis flows through `COST_POST_001` / `COST_POST_002`), [recipe](/en/inventory/recipe) (downstream consumer of the per-product cost basis), [product](/en/inventory/product) (carries `standard_cost` — the reference cost used by `enum_physical_count_costing_method = standard` and by recipe baseline).
