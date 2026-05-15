---
title: Physical Count — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for physical counts.
published: true
date: 2026-05-15T14:00:00.000Z
tags: physical-count, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Business Rules

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
