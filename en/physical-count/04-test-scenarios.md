---
title: Physical Count — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for physical counts.
published: true
date: 2026-05-15T14:00:00.000Z
tags: physical-count, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `physical-count` module. It groups coverage by the three persona groups that interact with the count lifecycle (Count Lead, Counter, Audit / Config — collapsed from the four canonical personas in [[physical-count]] § 4), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch the individual paths together, and frames the E2E mapping target — currently empty because **no `physical-count` Playwright spec exists** at `../carmen-inventory-frontend-e2e/tests/` as of this writing (verified by `ls tests/ | grep -i 'physical\|count'`).

The scope is intentionally broad even at skeleton level: each persona file is meant to grow to cover **functional happy paths** (open period, generate sheet, enter counts, recount-and-resolve, submit, rollup post), **RBAC / permission cases** (Counter attempts submit, Count Lead attempts counter-zone entry, Auditor attempts edit), **validation** (negative tests against `PHC_VAL_001`–`PHC_VAL_008` at line entry, at submit, at recount-flagging time), **edge cases** (zero on-shelf, frozen-mode movement attempts, tolerance-boundary lines, mid-period counter reassignment), and **configuration / audit-trail cases** (tolerance threshold change effect, costing-method change effect, audit chain inspection).

The cross-persona scenarios in Section 4 describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Count Lead generates sheet → Counter performs count → Count Lead submits → Approver / Finance approves rollup adjustment*; *Count Lead flags variance → different Counter recounts → variance reconciled → submit*; *Count Lead submits with overage and shortage → two rollup adjustments created*; *Frozen-mode count blocks parallel GRN posting → operational reconciliation*; *Auditor inspects full chain from count sheet to journal entry*. Section 5 is the E2E spec map — currently a TODO target waiting for the first physical-count spec to be authored.

> **TODO:** Replace this overview's E2E framing with concrete `ls`-verified spec citations once `../carmen-inventory-frontend-e2e/tests/` adds physical-count coverage. Until then, the test scenarios catalogued in the persona files are manual / planned coverage.

## 2. Personas in Scope

- **Count Lead** — Inventory Controller / Inventory Manager. Owner of the exercise; per [[physical-count/03-user-flow-count-lead]].
- **Counter** — Counter / Store Keeper. Floor-level data entry; per [[physical-count/03-user-flow-counter]].
- **Audit / Config** — Approver / Finance Reviewer + Auditor + Sysadmin. Approval, observation, configuration; per [[physical-count/03-user-flow-audit-config]].

## 3. Persona Test Files

- [Count Lead scenarios](./04-test-scenarios-count-lead.md)
- [Counter scenarios](./04-test-scenarios-counter.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the system in a terminal or steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the system state required to begin; "Expected end state" anchors `tb_physical_count.status`, the rollup adjustment effect (`tb_stock_in` / `tb_stock_out` written via `info.countId` linkage to [[inventory-adjustment]]), and any cross-module side effects.

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Period-end full count — happy path | Count Lead → Counter → Count Lead → Approver / Finance | `tb_period` open; no other count in progress at the location. | `tb_physical_count_period.status = completed`; `tb_physical_count.status = completed`; rollup `tb_stock_in` / `tb_stock_out` documents posted; `tb_inventory_transaction` rows written. |
| 2 | Cycle count for high-value category — auto-resolved variance | Count Lead → Counter → Count Lead | Spirits sub-category; tolerance threshold 5%. | All variance within tolerance; submit fires rollup; `tb_inventory_transaction` written for non-zero `diff_qty` lines. |
| 3 | Recount escalation — different counter | Count Lead → Counter (A) → Count Lead → Counter (B) → Count Lead | Counter A enters `actual_qty` triggering tolerance breach per `PHC_VAL_007`. | Recount line resolved by Counter B; variance reconciled within tolerance; submit fires rollup. |
| 4 | Recount confirms variance — accept and post | Count Lead → Counter (A) → Counter (B) → Count Lead | Recount confirms original count. | Count Lead overrides with countersignature; rollup posts variance line. Comment thread carries override justification. |
| 5 | Frozen-mode count blocks GRN | Count Lead → Counter → (concurrent GRN attempt) → Count Lead | `physical_count_type = yes`; GRN raised at same location. | GRN post rejected per `PHC_VAL_006` with location-locked error; count completes; GRN re-attempts post-completion. |
| 6 | Live-mode count parallel to GRN | Count Lead → Counter → (concurrent GRN) → Count Lead | `physical_count_type = no`. | GRN posts normally; count's `on_hand_qty` was snapshotted at sheet-gen time so the GRN's inventory effect does not back-drift the count. Variance compared against snapshot. |
| 7 | Zero on-shelf vs zero counted | Counter → Count Lead | Line with `on_hand_qty = 5`, counter sees nothing. | Counter enters `actual_qty = 0`; `diff_qty = -5`; line flagged for recount per `PHC_VAL_007`; recount confirms; rollup as `COUNT_SHORTAGE`. |
| 8 | Overage line | Counter → Count Lead | Line with `on_hand_qty = 10`, counter finds 12. | `diff_qty = +2`; rollup as `COUNT_OVERAGE` via `tb_stock_in`. |
| 9 | Mixed overage + shortage in same count | Count Lead → Counter → Count Lead | Count document with multiple positive and negative variances. | **Two** rollup documents: one `tb_stock_in` (overage lines), one `tb_stock_out` (shortage lines). Both carry `info.countId`. |
| 10 | Damaged-item flag bypasses normal count | Counter → Count Lead | Counter encounters damaged item not on sheet. | Detail-comment flagged with photo attachment; Count Lead reviews; may add line manually or refer to write-off via [[inventory-adjustment]] directly. |
| 11 | Counter attempts submit — rejected (RBAC) | Counter | Counter has zone-grant; all zone lines counted. | Submit action not available to Counter per `PHC_AUTH_002`; Count Lead receives completion notification. |
| 12 | Counter attempts to enter count outside their zone — rejected | Counter | Counter has zone-grant for zone A; attempts to edit zone B line. | Save rejected per `PHC_AUTH_004` with zone-scope error. |
| 13 | Tolerance threshold change mid-period | Sysadmin → Count Lead → Counter | Sysadmin tightens threshold from 5% to 2%. | New counts after change use 2%; in-flight counts retain 5% (snapshotted at sheet-gen). Verified via tolerance-test count. |
| 14 | Costing-method change effect on rollup value | Sysadmin → Count Lead | Sysadmin changes default from `last` to `average`. | Future rollups value variance at current weighted average per `PHC_CALC_003`. Existing posted rollups unchanged. |
| 15 | Backdated count posting — rejected | Count Lead | Period containing the count is `closed` per [[inventory]] `INV_VAL_008`. | Rollup adjustment submit rejected; Count Lead must escalate to Finance Manager to re-open the period. |
| 16 | Approver / Finance rejects rollup adjustment | Count Lead → Approver / Finance → Count Lead | Variance unusually large (e.g. 30% on a tracked category). | Rollup `tb_stock_in` / `tb_stock_out` returned to `draft`; Count Lead investigates (potential mis-count, mis-categorisation, miss-pour); may trigger fresh recount. |
| 17 | Auditor inspects full chain | Auditor | Period `completed`; rollup adjustments `completed`. | Auditor traces `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail` → rollup adjustment (`info.countId`) → `tb_inventory_transaction` → GL journal entry. No gaps; SoD verified (Count Lead ≠ Approver). |
| 18 | Period closes with all sub-counts completed | Count Lead → System | Last sub-`tb_physical_count` reaches `completed`. | `tb_physical_count_period.status = completed` auto-transition; no further count documents accepted under the period. |
| 19 | Sysadmin adds new costing-method default | Sysadmin | Tenant chooses `last_receiving` for future rollups. | Future rollups use last-receipt cost-layer for `cost_per_unit`. Existing posted rollups untouched. |
| 20 | Concurrent counter sessions on same count | Counter (A) + Counter (B) — same count, different zones | Two counters with disjoint zone-grants on the same `tb_physical_count`. | Both write to their own detail lines simultaneously; no conflict; `product_counted` increments correctly. |

> **TODO:** Each row should grow to include explicit assertions on `tb_*` field values, expected error messages, and (once specs exist) E2E spec line references. Currently the rows are framing for manual / planned coverage.

## 5. E2E Spec Map

> **TODO:** No physical-count Playwright spec exists at `../carmen-inventory-frontend-e2e/tests/` as of `2026-05-15`. When the first spec is authored (target file name: `8XX-physical-count.spec.ts` or `90X-physical-count.spec.ts`, following the period-end / stock-issue numbering convention), populate this section with:
> - Spec file path + brief description.
> - Mapping table: cross-persona scenario number (Section 4) → spec test name.
> - Coverage gap report (which scenarios remain manual vs automated).

Until coverage exists, treat every scenario in Sections 4 and per-persona files as **manual or planned**.

## 6. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — UI behaviour source for scenario assertions.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related: [[physical-count/03-user-flow]] (the handoff matrix this page exercises), [[physical-count/02-business-rules]] (`PHC_VAL_*` / `PHC_AUTH_*` / `PHC_POST_*`), [[inventory-adjustment/04-test-scenarios]] (rollup-side scenarios, scenarios 5–6 there overlap with rows 1–9 here).
