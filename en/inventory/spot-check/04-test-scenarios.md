---
title: Spot Check — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for spot checks.
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios

> **At a Glance**
> **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **Total scenarios:** per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Inventory Controller, Counter, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `spot-check` module. It groups coverage by the three persona groups that interact with the spot-check lifecycle (Inventory Controller, Counter, Audit / Config — per [spot-check](/en/inventory/spot-check) § 4 plus implicit Sysadmin), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch the individual paths together, and frames the E2E mapping target — currently empty because **no `spot-check` Playwright spec exists** at `../carmen-inventory-frontend-e2e/tests/` as of this writing (verified by `ls tests/ | grep -i 'spot\|check'`).

The scope is intentionally broad even at skeleton level: each persona file is meant to grow to cover **functional happy paths** (open spot check with each `method`, enter counts, recount-and-resolve, submit, rollup post, void path), **RBAC / permission cases** (Counter attempts submit, Inventory Controller attempts cross-location operation, Auditor attempts edit), **validation** (negative tests against `SPC_VAL_001`–`SPC_VAL_008` at creation, at line entry, at submit, at recount-flagging time, at void time), **edge cases** (zero on-shelf, tolerance-boundary lines, `method = manual` with empty selection, sample size larger than available products), and **configuration / audit-trail cases** (tolerance threshold change effect, default sampling size / method change effect, audit chain inspection).

The cross-persona scenarios in Section 4 describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Inventory Controller opens random spot check → Counter performs count → Inventory Controller submits → Approver / Finance approves rollup adjustment on the [inventory-adjustment](/en/inventory/inventory-adjustment) side*; *Inventory Controller flags variance → different Counter recounts → variance reconciled → submit*; *Inventory Controller submits with overage and shortage → two rollup adjustments created*; *Auditor inspects full chain from spot-check sheet to journal entry*; *Spot check voided mid-count → no ledger effect*. Section 5 is the E2E spec map — currently a TODO target waiting for the first spot-check spec to be authored.

> **TODO:** Replace this overview's E2E framing with concrete `ls`-verified spec citations once `../carmen-inventory-frontend-e2e/tests/` adds spot-check coverage. Until then, the test scenarios catalogued in the persona files are manual / planned coverage.

## 2. Personas in Scope

- **Inventory Controller** — Owner of the exercise; per [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller).
- **Counter** — Floor-level data entry; per [spot-check/03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter).
- **Audit / Config** — Auditor + Sysadmin (implicit). Observation, configuration; per [spot-check/03-user-flow-audit-config](/en/inventory/spot-check/03-user-flow-audit-config). Note: rollup-adjustment approval (Approver / Finance) lands on the [inventory-adjustment](/en/inventory/inventory-adjustment) side, not directly on spot-check.

## 3. Persona Test Files

- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md)
- [Counter scenarios](./04-test-scenarios-counter.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the system in a terminal or steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the system state required to begin; "Expected end state" anchors `tb_spot_check.doc_status`, the rollup adjustment effect (`tb_stock_in` / `tb_stock_out` written via `info.spotCheckId` linkage to [inventory-adjustment](/en/inventory/inventory-adjustment)), and any cross-module side effects.

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Random-sample spot check — happy path | Inventory Controller → Counter → Inventory Controller → Approver / Finance (on adjustment) | Inventory-type location; no in-flight spot check. | `tb_spot_check.doc_status = completed`; rollup `tb_stock_in` / `tb_stock_out` documents posted; `tb_inventory_transaction` rows written. |
| 2 | High-value sampling — premium spirits | Inventory Controller → Counter → Inventory Controller | High-value bar location; `method = high_value`; `size = 10`. | Top-10 by value sampled; counted; variance lines within tolerance; submit fires rollup. |
| 3 | Manual selection — triggered by incident | Inventory Controller → Counter → Inventory Controller | Suspected pilferage report; `method = manual`; controller adds 3 specific products. | Three lines created on detail; counted; variance posted as rollup adjustment with `info.spotCheckId`. |
| 4 | Recount escalation — different counter | Inventory Controller → Counter (A) → Inventory Controller → Counter (B) → Inventory Controller | Counter A enters `actual_qty` triggering tolerance breach per `SPC_VAL_006`. | Recount line resolved by Counter B; variance reconciled within tolerance; submit fires rollup. |
| 5 | Recount confirms variance — accept and post | Inventory Controller → Counter (A) → Counter (B) → Inventory Controller | Recount confirms original count. | Inventory Controller overrides with countersignature; rollup posts variance line. Comment thread carries override justification. |
| 6 | Zero on-shelf vs zero counted | Counter → Inventory Controller | Line with `on_hand_qty = 5`, counter sees nothing. | Counter enters `actual_qty = 0`; `diff_qty = -5`; line flagged for recount per `SPC_VAL_006`; recount confirms; rollup as shortage. |
| 7 | Overage line | Counter → Inventory Controller | Line with `on_hand_qty = 10`, counter finds 12. | `diff_qty = +2`; rollup as overage via `tb_stock_in`. |
| 8 | Mixed overage + shortage in same spot check | Inventory Controller → Counter → Inventory Controller | Spot check with multiple positive and negative variances. | **Two** rollup documents: one `tb_stock_in` (overage lines), one `tb_stock_out` (shortage lines). Both carry `info.spotCheckId`. |
| 9 | Damaged-item flag bypasses normal count | Counter → Inventory Controller | Counter encounters damaged item on the sheet. | Detail-comment flagged with photo attachment; Inventory Controller reviews; may add line manually or refer to write-off via [inventory-adjustment](/en/inventory/inventory-adjustment) directly. |
| 10 | Counter attempts submit — rejected (RBAC) | Counter | Counter has location-grant; all lines counted. | Submit action not available to Counter per `SPC_AUTH_002`; Inventory Controller receives completion notification. |
| 11 | Counter attempts to enter count outside location — rejected | Counter | Counter has location-grant for Location A; attempts to edit a Location B spot check. | Save rejected per `SPC_AUTH_004` with location-scope error. |
| 12 | Tolerance threshold change mid-exercise | Sysadmin → Inventory Controller → Counter | Sysadmin tightens threshold from 5% to 2%. | New spot checks after change use 2%; in-flight spot check retains 5% (snapshotted at sheet-gen). Verified via tolerance-test spot check. |
| 13 | Backdated rollup posting — rejected | Inventory Controller | Period containing the rollup adjustment is `closed` per [inventory](/en/inventory/inventory) `INV_VAL_008`. | Rollup adjustment submit rejected; Inventory Controller must escalate to Finance Manager to re-open period or wait. |
| 14 | Approver / Finance rejects rollup adjustment | Inventory Controller → Approver / Finance → Inventory Controller | Variance unusually large (e.g. 50% on a tracked SKU). | Rollup `tb_stock_in` / `tb_stock_out` returned to `draft`; Inventory Controller investigates (potential mis-count, mis-categorisation); may trigger fresh spot check. |
| 15 | Auditor inspects full chain | Auditor | Spot check `completed`; rollup adjustment `completed`. | Auditor traces `tb_spot_check` → `tb_spot_check_detail` → rollup adjustment (`info.spotCheckId`) → `tb_inventory_transaction` → GL journal entry. No gaps; SoD verified (Inventory Controller ≠ rollup approver). |
| 16 | Sysadmin changes default sampling size | Sysadmin → Inventory Controller | Default `size` raised from 10 to 25. | Future random / high_value spot checks generate 25 lines by default; existing spot checks unchanged. |
| 17 | Sysadmin changes default sampling method | Sysadmin → Inventory Controller | Default `method` switched from `random` to `high_value`. | Future spot checks default to `high_value` unless explicitly overridden by controller. |
| 18 | Void spot check mid-count | Inventory Controller | Spot check in `in_progress` with partial entries. | `doc_status = void`; no rollup; partial entries preserved in audit log; `tb_inventory_transaction` untouched. |
| 19 | Concurrent counter sessions on same spot check | Counter (A) + Counter (B) — same spot check | Two counters with overlapping location-grants on the same `tb_spot_check`. | Both write to detail lines simultaneously; last-write-wins per line; audit log retains both authors. |
| 20 | `method = manual` with empty detail at submit | Inventory Controller | Controller forgot to add detail lines. | Submit rejected per `SPC_VAL_002` / `SPC_VAL_004` ("Cannot submit — 0 lines counted."). |

> **TODO:** Each row should grow to include explicit assertions on `tb_*` field values, expected error messages, and (once specs exist) E2E spec line references. Currently the rows are framing for manual / planned coverage.

## 5. E2E Spec Map

> **TODO:** No spot-check Playwright spec exists at `../carmen-inventory-frontend-e2e/tests/` as of `2026-05-15`. When the first spec is authored (target file name guess: `7XX-spot-check.spec.ts` following the stock-issue / stock-take numbering convention, or similar), populate this section with:
> - Spec file path + brief description.
> - Mapping table: cross-persona scenario number (Section 4) → spec test name.
> - Coverage gap report (which scenarios remain manual vs automated).

Until coverage exists, treat every scenario in Sections 4 and per-persona files as **manual or planned**.

## 6. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — UI behaviour source for scenario assertions.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists.
- Related: [spot-check/03-user-flow](/en/inventory/spot-check/03-user-flow) (the handoff matrix this page exercises), [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) (`SPC_VAL_*` / `SPC_AUTH_*` / `SPC_POST_*`), [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) (full-count counterpart scenarios with three-tier period structure), [inventory-adjustment/04-test-scenarios](/en/inventory/inventory-adjustment/04-test-scenarios) (rollup-side scenarios).
