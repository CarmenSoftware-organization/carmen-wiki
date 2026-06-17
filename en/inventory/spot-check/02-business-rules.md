---
title: Spot Check — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for spot checks.
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Business Rules

> **At a Glance**
> **Rule families:** `SPC_VAL_*` validation &nbsp;·&nbsp; `SPC_AUTH_*` permission &nbsp;·&nbsp; `SPC_CALC_*` calc &nbsp;·&nbsp; `SPC_POST_*` posting &nbsp;·&nbsp; `SPC_XMOD_*` cross-module
> **Rule count:** approximately 30 rules
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page catalogues the operational rules governing the **spot-check module** — the two-level document tree (`tb_spot_check` → `tb_spot_check_detail`) that records a targeted, partial count of selected items or storage locations. The rules below sit **above** [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) (variance rollup posts there) and **above** the ledger-level rules in [inventory/02-business-rules](/en/inventory/inventory/02-business-rules) (the final inventory effect lands there) — they govern the document lifecycle (`pending → in_progress → completed`, plus the `void` cancel path), the choice of selection `method` (random / high_value / manual), `size` of the sample, Counter assignment, recount escalation when variance breaches tolerance, and the cross-module hooks into [inventory-adjustment](/en/inventory/inventory-adjustment) / [inventory](/en/inventory/inventory) / [costing](/en/inventory/costing). Rule IDs follow `SPC_VAL_*` (validation), `SPC_CALC_*` (calculation), `SPC_AUTH_*` (authorization), `SPC_POST_*` (posting), `SPC_XMOD_*` (cross-module).

Two structural notes from [spot-check/01-data-model](/en/inventory/spot-check/01-data-model) colour every rule below: **first**, spot-check is **flat (no period parent)** — unlike physical-count there is no `tb_spot_check_period`, so the period-level rules of `PHC_VAL_001` have no analogue; instead, period containment is enforced at rollup time on the [inventory-adjustment](/en/inventory/inventory-adjustment) side per `INV_VAL_008`. **Second**, the spot-check tables do not write to the inventory ledger directly — variance posts via the `tb_stock_in` / `tb_stock_out` rollup, and the adjustment post writes `tb_inventory_transaction`. Ledger semantics are inherited from `INV_VAL_*` / `INV_CALC_*` / `INV_POST_*`. **Third**, there is currently no carmen/docs source for `SPC_*` rules — the rule IDs below are proposed scaffolding to be confirmed when the carmen/docs catalogue is authored.

## 2. Validation Rules

Rule IDs follow `SPC_VAL_NNN`. Validation runs at three boundaries: **at spot-check creation** (sheet generation), **at line-entry time** (counter typing in `actual_qty`), and **at submit** (`in_progress → completed`).

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `SPC_VAL_001` | `location_id` references an active inventory- or consignment-type location per [inventory](/en/inventory/inventory) `INV_VAL_009`. Direct-cost locations are not spot-checkable. | Create spot check | Reject with `"Direct-cost locations cannot be spot-checked."` |
| `SPC_VAL_002` | `method` is one of `random` / `high_value` / `manual`; `size > 0` when `method ∈ {random, high_value}`; `manual` method requires at least one `tb_spot_check_detail` line to be explicitly added before submit. | Create / edit spot check | Reject with method-specific error message. |
| `SPC_VAL_003` | When `method = random`, the system samples `size` distinct products from in-scope inventory at `location_id`; when `method = high_value`, the top-`size` by value-on-hand or velocity (tenant-configurable) is selected. | Sheet generation | Sample produces `size` `tb_spot_check_detail` rows; if `size` exceeds available distinct products, sample is truncated and the difference logged. |
| `SPC_VAL_004` | Every `tb_spot_check_detail` line has a non-null `actual_qty` before the document can be submitted. | Submit | Reject with `"Cannot submit spot check — <N> of <M> lines remain uncounted."` |
| `SPC_VAL_005` | `actual_qty ≥ 0` on every detail. Negative physical counts are non-sensical. | Line entry | Reject with `"Counted quantity must be zero or positive."` |
| `SPC_VAL_006` | A line whose `|diff_qty| / on_hand_qty` exceeds the tenant tolerance threshold (typical 5% or absolute 1 unit, whichever is greater) is flagged for recount; the document cannot be submitted until the line is either recounted-and-reconciled or explicitly marked "accept variance" by an Inventory Controller. | Submit | Block submit until flagged lines are resolved. |
| `SPC_VAL_007` | A completed `tb_spot_check` cannot be re-opened — corrections require a fresh spot check or a manual `tb_stock_in` / `tb_stock_out` adjustment against the same location per `SPC_POST_004`. | Edit completed | Reject with `"Cannot edit a completed spot check. Raise a manual inventory adjustment."` |
| `SPC_VAL_008` | A `pending` or `in_progress` spot check can be moved to `void` (cancel before completion); a `completed` spot check cannot be voided — the rollup adjustment (if any) is the path to reverse via [inventory-adjustment](/en/inventory/inventory-adjustment). | Void | Reject void on completed; allow on pending / in_progress. |

> **TODO:** Confirm exact tolerance threshold formula and default values from tenant config when carmen/docs catalogue is authored. Confirm whether spot-check has a separate frozen-stock window rule analogous to `PHC_VAL_006` — none found in schema (no `enum_spot_check_type` exists). Cross-reference with E2E specs for the recount flow once they exist.

## 3. Calculation Rules

Rule IDs follow `SPC_CALC_NNN`. All quantity fields are `Decimal(20, 5)` per `tb_spot_check_detail.on_hand_qty` / `actual_qty` / `diff_qty`.

| Rule ID | Formula |
| ------- | ------- |
| `SPC_CALC_001` (variance qty) | `diff_qty = actual_qty - on_hand_qty` per line. Positive = overage (write-on); negative = shortage (write-off). Stored on `tb_spot_check_detail.diff_qty`. |
| `SPC_CALC_002` (variance %) | `variance_% = (diff_qty / on_hand_qty) × 100` when `on_hand_qty > 0`; when `on_hand_qty = 0` and `actual_qty > 0`, treat as new-discovery (100% positive). Drives tolerance-breach flagging per `SPC_VAL_006`. Not persisted; derived at read time. |
| `SPC_CALC_003` (variance value) | `variance_value = diff_qty × cost_per_unit`, where `cost_per_unit` follows the tenant's adjustment-side costing method (no dedicated spot-check costing enum exists in schema — inherits from `enum_physical_count_costing_method` defaults or the adjustment-type's configured cost basis, to be confirmed per `SPC_XMOD_003`). |
| `SPC_CALC_004` (sample size verification) | `actual_sampled_count == tb_spot_check.size` (or truncated with logged reason per `SPC_VAL_003`). Derived at read time; not persisted on header (no `product_counted` / `product_total` columns on `tb_spot_check`). |

> **TODO:** Confirm the spot-check costing-method precedence vs physical-count's `enum_physical_count_costing_method` once frontend logic is documented. Cross-link to [costing](/en/inventory/costing) for WA / FIFO valuation behaviour.

## 4. Authorization Rules

Rule IDs follow `SPC_AUTH_NNN`. Persona definitions per [spot-check](/en/inventory/spot-check) § 4 and the three-group collapse in this module's sub-pages (inventory-controller / counter / audit-config).

| Rule ID | Rule |
| ------- | ---- |
| `SPC_AUTH_001` | **Inventory Controller** creates and schedules `tb_spot_check` documents, configures `method` (random / high_value / manual) and `size`, assigns counters, reviews variances, approves or rejects recount requests, and approves adjustments for posting. Single seat per spot check per tenant policy. |
| `SPC_AUTH_002` | **Counter** enters `actual_qty` on assigned `tb_spot_check_detail` lines within their location/zone, flags damaged / unlabelled items via `tb_spot_check_detail_comment`, but cannot submit the document — only the Inventory Controller can submit. |
| `SPC_AUTH_003` | **Audit / Config** group: Auditor has read-only access to all levels (header / detail) including comment threads and counted-by stamps to independently review spot-check results, recount evidence, and posted adjustments — confirming controls operating and shrinkage investigated. Sysadmin (implicit) configures tolerance thresholds, default `size`, default `method`, and reason-code mapping. |
| `SPC_AUTH_004` | Counter assignment is location-bound — a counter sees only spot-check documents for locations where they have `tb_user_location` (or equivalent location-grant). Cross-location visibility requires Inventory Controller role. |

## 5. Posting Rules

Rule IDs follow `SPC_POST_NNN`. Posting in this module refers to the variance-rollup transition (spot-check-completion → adjustment-document creation), not direct ledger writes.

| Rule ID | Rule |
| ------- | ---- |
| `SPC_POST_001` | On `tb_spot_check.doc_status = completed`, the application layer iterates `tb_spot_check_detail` and groups lines by `sign(diff_qty)`: positive → one or more `tb_stock_in` lines under reason `SPOT_CHECK_OVERAGE` (or `COUNT_OVERAGE` if aliased); negative → one or more `tb_stock_out` lines under reason `SPOT_CHECK_SHORTAGE` (or `COUNT_SHORTAGE`); zero → no rollup. |
| `SPC_POST_002` | The rollup adjustment header carries `info.spotCheckId = <tb_spot_check.id>` (and / or `info.countId` if reasons are aliased) for the audit-side join back to the spot-check source. The reason-code on `tb_adjustment_type` must exist with the appropriate direction (per [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) § 2.1). |
| `SPC_POST_003` | The cost-per-unit on each rollup line is set per `SPC_CALC_003` (inherited costing method). The Inventory Controller countersignature on the adjustment submission satisfies [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) approval per the rollup-fast-path (counter authority pre-approved at the spot check's submission). |
| `SPC_POST_004` | Once the rollup adjustment is `completed`, the spot-check document is **immutable** — any subsequent correction at the same location requires a fresh `tb_stock_in` / `tb_stock_out` raised manually (or a new spot check), not a re-open. |

### 5.1 Status Lifecycle — Live UI vs BRD Mapping

The Prisma enum `enum_spot_check_status` documented in [spot-check/01-data-model](/en/inventory/spot-check/01-data-model) § 4 is what the live schema uses. `tx-10-spot-check.md` (BR-spot-check.md v2.2.0) describes the intended status set. Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27).

> Diff legend: ✅ match · 🟡 renamed/semantically shifted · 🔴 new in live schema (no BRD equivalent)

| Live schema status (`enum_spot_check_status`) | BRD (`tx-10-spot-check.md`) equivalent | Diff | Notes |
|---|---|---|---|
| `pending` | `draft` / `pending` | 🟡 | BRD uses `draft` (created, not submitted) → `pending` (submitted, awaiting start) as two distinct states. Live schema collapses both into `pending`. Counter entering first qty triggers `pending → in_progress`. |
| `in_progress` | `in-progress` | ✅ match | Direct match. Counting underway. |
| `completed` | `completed` | ✅ match | Direct match. Terminal; satisfies End Period Close Stage 2 (BR-PE-006). |
| `void` | `cancelled` | 🟡 | BRD uses `cancelled` with a note that all entered data is preserved and no inventory changes are posted (BR-SC-007). Live schema uses `void`. |
| — | `on-hold` | 🔴 | BRD defines `on-hold` (paused; → `in-progress`, `cancelled`). No `on_hold` value exists in `enum_spot_check_status` in the Prisma schema — pause/resume may be handled via UI state or a future migration. |

> ⚠️ **Discrepancy — `draft` vs `pending` collapse:** BRD `tx-10-spot-check.md` defines two distinct pre-counting states: `draft` (created, not submitted → `pending`) and `pending` (submitted, awaiting start → `in-progress`). The live `enum_spot_check_status` has only `pending` — the create/submit distinction is not persisted as separate enum values. Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27).

> ⚠️ **Discrepancy — `on-hold` state not in schema:** BRD defines `on-hold` as a valid pause state (`in-progress → on-hold → in-progress`). The live `enum_spot_check_status` does not include an `on_hold` value — pause/resume behaviour (e.g. "staff unavailable") may be handled at the UI layer without persisting a separate enum state, or may be deferred. Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27).

> ⚠️ **Discrepancy — End Period Close Stage 2 gate not modelled in BRD posting rules:** The test-case INDEX specifies that all Spot Checks must be `completed` before End Period Close Stage 2 passes (BR-PE-006). The BRD (BR-spot-check.md v2.2.0) does not include a corresponding rule in the spot-check posting rules — the period-close gate is defined on the End Period Close side (tx-09). The wiki cross-references this in `SPC_POST_001` via the `completed` terminal state, but the live UI enforces it as an external gate, not a spot-check-internal constraint. Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27).

> ⚠️ **Discrepancy — variance posting to inventory is PENDING:** BRD (BR-spot-check.md v2.2.0) implies variance posting to QOH / lots / cost upon completion (the same rollup pattern as Physical Count). The live implementation reaches `completed` status and satisfies End Period Close Stage 2 but does **not** currently post variance adjustments to inventory, lots, or cost. Lot impact and cost impact are both marked TBC. Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27).

## 6. Cross-Module Rules

Rule IDs follow `SPC_XMOD_NNN`.

| Rule ID | Rule |
| ------- | ---- |
| `SPC_XMOD_001` | **→ [inventory-adjustment](/en/inventory/inventory-adjustment)**: spot-check variances post via the `tb_stock_in` / `tb_stock_out` document tree with reason codes `SPOT_CHECK_OVERAGE` / `SPOT_CHECK_SHORTAGE` (or aliased to `COUNT_*`). The rollup is the only path from spot check to ledger. |
| `SPC_XMOD_002` | **→ [inventory](/en/inventory/inventory)**: every rollup adjustment writes a `tb_inventory_transaction` with `enum_transaction_type = adjustment_in` / `adjustment_out`. No direct `spot_check` value exists on `enum_transaction_type`. |
| `SPC_XMOD_003` | **→ [costing](/en/inventory/costing)**: the costing-method selection on the rollup inherits the adjustment-side default (no dedicated `enum_spot_check_costing_method` exists in schema); FIFO consumption (for shortage) and WA refresh (for overage) follow `INV_CALC_005` / `INV_CALC_007` once the adjustment posts. |
| `SPC_XMOD_004` | **→ [physical-count](/en/inventory/physical-count)**: spot check is the **partial-count counterpart** of [physical-count](/en/inventory/physical-count) — narrower scope (a sample, not all items at all locations), no fiscal-period parent, ad-hoc cadence. It uses the same conceptual variance-rollup hook into [inventory-adjustment](/en/inventory/inventory-adjustment); it is **not** a child of `tb_physical_count_period`. |

> **TODO:** Verify rule IDs above against carmen/docs `SPC-*` catalogue when authored; confirm tolerance / threshold default values from production tenant config; cross-validate posting fan-out with frontend implementation in `../carmen-inventory-frontend-react/`; confirm reason-code naming (`SPOT_CHECK_*` vs reused `COUNT_*`).

## 7. References

- **Primary (Prisma):** see [spot-check/01-data-model](/en/inventory/spot-check/01-data-model) for entity / enum source citations.
- **Secondary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — naming hint search returned no top-level `spot-check` route; check nested module folders when documenting.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; document rule traceability once added.
- Related rule sets: [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_*` — full-count counterpart with three-level period structure; spot-check is the simpler two-level cousin), [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) (`ADJ_*` — variance rollup lives there), [inventory/02-business-rules](/en/inventory/inventory/02-business-rules) (`INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` — ledger semantics inherited at adjustment post), [costing](/en/inventory/costing) (FIFO / WA refresh behaviour on rollup post).
