---
title: Physical Count — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for physical counts.
published: true
date: 2026-05-17T11:00:00.000Z
tags: physical-count, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Business Rules

> **At a Glance**
> **Rule families:** `PHC_VAL_*` validation &nbsp;·&nbsp; `PHC_AUTH_*` permission &nbsp;·&nbsp; `PHC_CALC_*` calc &nbsp;·&nbsp; `PHC_POST_*` posting &nbsp;·&nbsp; `PHC_XMOD_*` cross-module
> **Rule count:** approximately 28 rules
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page catalogues the operational rules governing the **physical-count module** — the three-level document tree (`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`) that records the scheduled, end-to-end count of every item at a location. The rules below sit **above** [[inventory-adjustment/02-business-rules]] (variance rollup posts there) and **above** the ledger-level rules in [[inventory/02-business-rules]] (the final inventory effect lands there) — they govern the period-and-document lifecycle (`pending → in_progress → completed`), the choice of frozen vs live mode (`enum_physical_count_type`), counter assignment and zone discipline, recount escalation when variance breaches tolerance, valuation-method selection at variance-rollup time (`enum_physical_count_costing_method`), and the cross-module hooks into [[inventory-adjustment]] / [[inventory]] / [[costing]]. Rule IDs follow `PHC_VAL_*` (validation), `PHC_CALC_*` (calculation), `PHC_AUTH_*` (authorization), `PHC_POST_*` (posting), `PHC_XMOD_*` (cross-module).

Two structural notes from [[physical-count/01-data-model]] colour every rule below: **first**, the physical-count tables do **not** write to the inventory ledger directly — the variance rollup writes a `tb_stock_in` (overage) and / or `tb_stock_out` (shortage) to [[inventory-adjustment]], and the adjustment post is what writes `tb_inventory_transaction`. The PHC rules therefore govern the document lifecycle and the variance computation; the ledger semantics are inherited from `INV_VAL_*` / `INV_CALC_*` / `INV_POST_*`. **Second**, there is currently no carmen/docs source for `PHC_*` rules — the rule IDs below are proposed scaffolding to be confirmed when the carmen/docs catalogue is authored.

## 2. Validation Rules

Rule IDs follow `PHC_VAL_NNN`. Validation runs at three boundaries: **at count-document creation** (sheet generation), **at line-entry time** (counter typing in `actual_qty`), and **at submit** (`in_progress → completed`).

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PHC_VAL_001` | A `tb_physical_count_period` row exists in `counting` status for the target fiscal period before any `tb_physical_count` is created under it. The period must be open per [[inventory]] `INV_VAL_008`. | Create count document | Reject if no period header exists or period is `completed`. |
| `PHC_VAL_002` | `tb_physical_count.physical_count_type` is set (`yes` for frozen, `no` for live) at sheet generation; the chosen mode cannot change once `status = in_progress`. | Create / edit count document | Reject mode change on a started count. |
| `PHC_VAL_003` | `location_id` references an active inventory- or consignment-type location per [[inventory]] `INV_VAL_009`. Direct-cost locations are not countable. | Create count document | Reject with `"Direct-cost locations cannot be physically counted."` |
| `PHC_VAL_004` | Every `tb_physical_count_detail` line has a non-null `actual_qty` before the document can be submitted (`product_counted == product_total`). | Submit | Reject with `"Cannot submit count — <N> of <M> lines remain uncounted."` |
| `PHC_VAL_005` | `actual_qty ≥ 0` on every detail. Negative physical counts are non-sensical. | Line entry | Reject with `"Counted quantity must be zero or positive."` |
| `PHC_VAL_006` | When `physical_count_type = yes` (frozen), no `tb_inventory_transaction` writes are accepted at `(period, location)` between `status = in_progress` and `status = completed`. Frontend pre-check on GRN / SR / adjustment posting screens. | At any inventory-write attempt during the count window | Reject submission with `"Location is locked for physical count — wait for count completion or use the live-count mode."` |
| `PHC_VAL_007` | A line whose `|diff_qty| / on_hand_qty` exceeds the tenant tolerance threshold (typical 5% or absolute 1 unit, whichever is greater) is flagged for recount; the document cannot be submitted until the line is either recounted-and-reconciled or explicitly marked "accept variance" by an Inventory Controller. | Submit | Block submit until flagged lines are resolved. |
| `PHC_VAL_008` | A completed `tb_physical_count` cannot be re-opened — corrections require a new period or a manual `tb_stock_in` / `tb_stock_out` adjustment against the same location per `PHC_POST_004`. | Edit completed | Reject with `"Cannot edit a completed count. Raise a manual inventory adjustment."` |

> **TODO:** Confirm exact tolerance threshold formula and default values from tenant config when carmen/docs catalogue is authored. Cross-reference with E2E specs for the recount flow once they exist.

## 3. Calculation Rules

Rule IDs follow `PHC_CALC_NNN`. All quantity fields are `Decimal(20, 5)` per `tb_physical_count_detail.on_hand_qty` / `actual_qty` / `diff_qty`.

| Rule ID | Formula |
| ------- | ------- |
| `PHC_CALC_001` (variance qty) | `diff_qty = actual_qty - on_hand_qty` per line. Positive = overage (write-on); negative = shortage (write-off). Stored on `tb_physical_count_detail.diff_qty`. |
| `PHC_CALC_002` (variance %) | `variance_% = (diff_qty / on_hand_qty) × 100` when `on_hand_qty > 0`; when `on_hand_qty = 0` and `actual_qty > 0`, treat as new-discovery (100% positive). Drives tolerance-breach flagging per `PHC_VAL_007`. Not persisted; derived at read time. |
| `PHC_CALC_003` (variance value) | `variance_value = diff_qty × cost_per_unit`, where `cost_per_unit` is picked by the tenant's `enum_physical_count_costing_method`: `standard` (product master), `last` (last receipt cost), `average` (current weighted average), `last_receiving` (alias for last). |
| `PHC_CALC_004` (progress) | `progress_% = product_counted / product_total × 100` at document level; the counters are auto-updated as each detail's `actual_qty` is saved. |

> **TODO:** Confirm exact precedence of `enum_physical_count_costing_method` values against frontend logic once carmen-inventory-frontend code path is documented. Cross-link to [[costing]] for the WA / FIFO valuation behaviour.

## 4. Authorization Rules

Rule IDs follow `PHC_AUTH_NNN`. Persona definitions per [[physical-count]] § 4 and the three-group collapse in this module's sub-pages (count-lead / counter / audit-config).

| Rule ID | Rule |
| ------- | ---- |
| `PHC_AUTH_001` | **Count Lead** (Inventory Controller / Manager) creates and schedules `tb_physical_count_period` and `tb_physical_count` documents, assigns counters, configures mode (frozen vs live), and approves recount results. Single seat per period per tenant policy. |
| `PHC_AUTH_002` | **Counter** (Store Keeper / Counter) enters `actual_qty` on assigned `tb_physical_count_detail` lines within their zone, flags damaged / unlabelled items via `tb_physical_count_detail_comment`, but cannot submit the document — only the Count Lead can submit. |
| `PHC_AUTH_003` | **Audit / Config** group: Approver / Finance reviews variance-rollup adjustments (action lands on [[inventory-adjustment]] not here); Auditor has read-only access to all three levels (period / document / detail) including comment threads and counted-by stamps; Sysadmin configures tolerance thresholds and costing-method default. |
| `PHC_AUTH_004` | Counter assignment is scope-bound — a counter sees only lines whose `(location, zone)` is in their `tb_user_location` / equivalent zone-grant. Cross-zone visibility requires Count Lead role. |

## 5. Posting Rules

Rule IDs follow `PHC_POST_NNN`. Posting in this module refers to the variance-rollup transition (count-completion → adjustment-document creation), not direct ledger writes.

| Rule ID | Rule |
| ------- | ---- |
| `PHC_POST_001` | On `tb_physical_count.status = completed`, the application layer iterates `tb_physical_count_detail` and groups lines by `sign(diff_qty)`: positive → one or more `tb_stock_in` lines under reason `COUNT_OVERAGE`; negative → one or more `tb_stock_out` lines under reason `COUNT_SHORTAGE`; zero → no rollup. |
| `PHC_POST_002` | The rollup adjustment header carries `info.countId = <tb_physical_count.id>` and `info.countPeriodId = <tb_physical_count_period.id>` for the audit-side join back to the count source. The reason-code on `tb_adjustment_type` must exist with the appropriate direction (per [[inventory-adjustment/01-data-model]] § 2.1). |
| `PHC_POST_003` | The cost-per-unit on each rollup line is set per `PHC_CALC_003` (the chosen `enum_physical_count_costing_method`). The Count Lead countersignature on the adjustment submission satisfies [[inventory-adjustment/02-business-rules]] approval per the rollup-fast-path (counter authority pre-approved at the count's submission). |
| `PHC_POST_004` | Once the rollup adjustment is `completed`, the count document is **immutable** — any subsequent correction at the same location requires a fresh `tb_stock_in` / `tb_stock_out` raised manually, not a re-open of the count. |

### 5.1 Status Lifecycle — Live UI vs BRD Mapping

Two enum layers govern physical-count status. `enum_physical_count_period_status` (`draft`, `counting`, `completed`) tracks the period header; `enum_physical_count_status` (`pending`, `in_progress`, `completed`) tracks each count document. No BRD reference file exists for this module in carmen/docs — the "BRD equivalent" column below uses the functional specification in `Test_case/System_Process/tx-08-physical-stocktake.md` as the closest available BRD proxy, and where the Test_case uses different status labels the diff is noted. Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27).

> Diff legend: ✅ match · 🔴 new in live UI (no Test_case equivalent) · 🔵 Test_case only (no live enum value)

**`enum_physical_count_status` (document-level):**

| Live UI status | Test_case (`tx-08`) equivalent | Diff | Notes |
|---|---|---|---|
| `pending` | — (not named; sheet created but counting not yet started) | 🔴 new in live UI | Sheet generated by Count Lead; `on_hand_qty` snapshot captured; counter assigned. Test_case flow jumps directly from "count created" to "IN PROGRESS" without naming this pre-start state. |
| `in_progress` | `IN PROGRESS` | ✅ match | Counter entering `actual_qty` values. Location is **locked** — GRN, SR, Issues, Stock In/Out adj for that location are all blocked per `PHC_VAL_006` and `BR-01`. |
| `completed` | `COMPLETED` | ✅ match | All lines counted; Count Lead submitted; variance recorded. Rollup adjustment created per `PHC_POST_001`. Does **not** satisfy End Period Close Stage 3 alone — `FINALIZED` (GL posted) is required per `BR-02` / `BR-PE-005`. |
| — | `FINALIZED` | 🔵 Test_case only | Test_case adds a `FINALIZED` state (GL posted to the General Ledger) required for End Period Close Stage 3 per `BR-02` / `BR-PE-005`. The live Prisma `enum_physical_count_status` has no `finalized` value — GL posting is handled by the rollup adjustment (`tb_stock_in` / `tb_stock_out`) reaching `completed` in [[inventory-adjustment]], not by a status change on `tb_physical_count`. |

**`enum_physical_count_period_status` (period-level):**

| Live UI status | Test_case (`tx-08`) equivalent | Diff | Notes |
|---|---|---|---|
| `draft` | — (period planning, no Test_case term) | 🔴 new in live UI | Period header opened; no count documents created yet. Test_case does not name this state. |
| `counting` | — (active exercise, no Test_case term) | 🔴 new in live UI | Auto-transitions when first child `tb_physical_count` document is created. Test_case describes the active exercise but uses the document-level `IN PROGRESS` term, not a distinct period-level label. |
| `completed` | — (all locations counted, no Test_case term) | 🔴 new in live UI | All `tb_physical_count` rows under the period reach `completed`. Period locked from new counts. Test_case describes this state functionally (all counts finalized for period close) but uses no period-level label. |

> ⚠️ **Discrepancy — Missing `FINALIZED` status on `enum_physical_count_status`:** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) defines a three-state flow `IN PROGRESS → COMPLETED → FINALIZED`, where `FINALIZED` means the count's variance adjustments have been posted to the General Ledger and the count satisfies End Period Close Stage 3 (per `BR-02` / `BR-PE-005`). The live Prisma `enum_physical_count_status` only has `pending`, `in_progress`, `completed` — there is no `finalized` value. In the live implementation, the GL-posting milestone is tracked via the rollup adjustment document in [[inventory-adjustment]] reaching `completed`, not via a status change on `tb_physical_count` itself. Testers must therefore check the rollup `tb_stock_in` / `tb_stock_out` status — not just `tb_physical_count.status` — to confirm whether End Period Close Stage 3 is satisfied. Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27).

> ⚠️ **Discrepancy — Location lock side-effect not modelled in Prisma schema:** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) states that "transactions at a location are locked while the Physical Count is IN PROGRESS" (`BR-01`): GRN, CRN, SR, Issues, Sales, and Stock In/Out adjustments for that location are all blocked. This behaviour is governed by `PHC_VAL_006` in this wiki and enforced at the application layer (front-end pre-check on posting screens) — it is **not** a Prisma-level constraint on `tb_physical_count` itself. Testers verifying the lock must attempt to post a GRN or SR against a location that has an `in_progress` count and confirm the system rejects the attempt with the expected error message. Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27).

> ⚠️ **Discrepancy — Period-close prerequisite chain (Stage 3 gate):** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) specifies that End Period Close Stage 3 cannot pass until all Physical Counts reach `FINALIZED` (GL posted) per `BR-02` / `BR-PE-005`. A count that is `COMPLETED` but whose rollup adjustment has not yet posted is **not** sufficient — it will block period close. The live Prisma schema has no `finalized` enum value and no FK from `tb_physical_count` to the rollup adjustment — the period-close gate logic must query [[inventory-adjustment]] for rollup documents with `info.countPeriodId = <period_id>` and verify all are at `completed` status. This is an application-layer dependency not visible from the physical-count schema alone. Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27).

> ⚠️ **Discrepancy — Positive variance lot handling (TBC):** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) marks positive-variance lot creation as "TBC — new lot created or existing lot adjusted up". The current Prisma schema and rollup path (`tb_stock_in` with reason `COUNT_OVERAGE`) always create a new lot for overage quantities. The "existing lot adjusted up" path has not been confirmed. Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27).

## 6. Cross-Module Rules

Rule IDs follow `PHC_XMOD_NNN`.

| Rule ID | Rule |
| ------- | ---- |
| `PHC_XMOD_001` | **→ [[inventory-adjustment]]**: count variances post via the `tb_stock_in` / `tb_stock_out` document tree with reason codes `COUNT_OVERAGE` / `COUNT_SHORTAGE`. The rollup is the only path from count to ledger. |
| `PHC_XMOD_002` | **→ [[inventory]]**: every rollup adjustment writes a `tb_inventory_transaction` with `enum_transaction_type = adjustment_in` / `adjustment_out`. No direct `physical_count` value exists on `enum_transaction_type`. |
| `PHC_XMOD_003` | **→ [[costing]]**: the costing-method selection on the rollup follows `enum_physical_count_costing_method`; FIFO consumption (for shortage) and WA refresh (for overage) follow `INV_CALC_005` / `INV_CALC_007` once the adjustment posts. |
| `PHC_XMOD_004` | **→ [[spot-check]]**: spot-check is a narrower partial count that uses the same conceptual model and the same variance-rollup hook into [[inventory-adjustment]]; it is **not** a child of `tb_physical_count_period`. |

> **TODO:** Verify rule IDs above against carmen/docs `PHC-*` catalogue when authored; confirm tolerance / threshold default values from production tenant config; cross-validate posting fan-out with frontend implementation in `../carmen-inventory-frontend/`.

## 7. References

- **Primary (Prisma):** see [[physical-count/01-data-model]] for entity / enum source citations.
- **Secondary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — naming hint search returned no top-level `physical-count` route; check nested module folders when documenting.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists; document rule traceability once added.
- Related rule sets: [[inventory-adjustment/02-business-rules]] (`ADJ_*` — variance rollup lives there), [[inventory/02-business-rules]] (`INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` — ledger semantics inherited at adjustment post), [[costing]] (FIFO / WA refresh behaviour on rollup post).
