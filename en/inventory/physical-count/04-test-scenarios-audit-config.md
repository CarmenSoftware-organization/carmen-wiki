---
title: Physical Count — Test Scenarios — Audit & Config
description: Approver / Finance Reviewer, Auditor, and Sysadmin test cases for the physical-count module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: physical-count, test-scenarios, audit, config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Approver / Finance Reviewer + Auditor + Sysadmin) &nbsp;·&nbsp; **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **Scenarios:** ~30 (skeleton)
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no `physical-count` Playwright spec exists at `../carmen-inventory-frontend-e2e/`; scenarios are manual / planned coverage. Rollup approval scenarios cross-reference [inventory-adjustment](/en/inventory/inventory-adjustment) specs.

## 1. Persona Scope

The **Audit / Config** persona group collapses three roles whose touch on the physical-count module is approval, observation, or configuration. The scenarios below exercise the actions catalogued in [physical-count/03-user-flow-audit-config](/en/inventory/physical-count/03-user-flow-audit-config) Section 3 — rollup adjustment review/approve/reject (Approver / Finance), in-progress observation and full-chain inspection (Auditor), tolerance / costing-method / reason-code configuration (Sysadmin). Authority anchor `PHC_AUTH_003`. Note: the **rollup approval action lands on [inventory-adjustment](/en/inventory/inventory-adjustment) documents, not on `tb_physical_count`** — many scenarios below cross-reference [inventory-adjustment/04-test-scenarios-finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance) and [inventory-adjustment/04-test-scenarios-audit-config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config).

## 2. Functional — Happy Paths

| # | Scenario | Persona | Pre-condition | Expected outcome |
| - | -------- | ------- | ------------- | ---------------- |
| AC-F-01 | Review rollup variance adjustment | Approver / Finance | Rollup `tb_stock_in` / `tb_stock_out` in `in_progress`; `info.countId` populated. | Reviewer sees variance lines + drill-through to source `tb_physical_count`. |
| AC-F-02 | Approve rollup adjustment | Approver / Finance | Variance within historical norms; ADJ-side validations pass. | Adjustment `completed`; `tb_inventory_transaction` written; GL journal entry posted. Per [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) approval path. |
| AC-F-03 | Reject rollup adjustment | Approver / Finance | Variance anomalous (e.g. 30% on tracked category). | Adjustment returned to `draft`; Count Lead notified; investigation may trigger fresh recount. |
| AC-F-04 | Auditor observes count in progress | Auditor | Count document in `in_progress`. | Read-only view: live `actual_qty` entries, zone-assignments, recount flags. Auditor may attach observation note as `tb_physical_count_comment`. |
| AC-F-05 | Auditor inspects full chain | Auditor | Period `completed`; rollup adjustments `completed`. | Read-only trace: count sheet → recount records → approvals → posted adjustments → inventory transactions → journal entries. No gaps. |
| AC-F-06 | Sysadmin configures tolerance threshold | Sysadmin | New tenant policy. | Tenant default updated; future counts use new threshold per `PHC_VAL_007`. |
| AC-F-07 | Sysadmin configures default costing-method | Sysadmin | Tenant policy change (e.g. switch from `last` to `average`). | Tenant default updated; future rollups value variance per `PHC_CALC_003` with new method. |
| AC-F-08 | Sysadmin maps reason codes for rollup | Sysadmin | New tenant onboarding. | `tb_adjustment_type` rows for `COUNT_OVERAGE` (`type = STOCK_IN`) and `COUNT_SHORTAGE` (`type = STOCK_OUT`) created with `info.glAccount`. Per [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) § 2.1. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| AC-R-01 | Auditor attempts to edit count | Auditor role only. | Edit rejected; read-only enforced for Auditor at all three levels (period, document, detail). |
| AC-R-02 | Approver / Finance attempts to edit count detail | Approver role. | Edit rejected; approval action only on rollup `tb_stock_in` / `tb_stock_out`, not on `tb_physical_count_detail` itself. |
| AC-R-03 | Sysadmin attempts to perform a count | Sysadmin role only. | If Sysadmin lacks Count Lead role, count actions rejected. Sysadmin configures, does not operate. |
| AC-R-04 | Approver / Finance approval — SoD with Count Lead | Same user is both Count Lead and Approver on the count. | SoD check rejects: approver must differ from count submitter. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| AC-V-01 | `INV_VAL_008` (inherited) | Rollup adjustment submit into `closed` period. | `"Cannot post into period <YYMM>: period is closed."` Finance Manager must re-open. |
| AC-V-02 | `ADJ_VAL_002` (downstream) | Sysadmin mis-maps `COUNT_OVERAGE` to `type = STOCK_OUT`. | Reason-code save rejected at adjustment-type form per direction validation in [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) `ADJ_VAL_002`. |
| AC-V-03 | `PHC_AUTH_003` | Auditor attempts to approve rollup adjustment. | Action rejected; Auditor is read-only on the rollup approval path. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| AC-E-01 | Approver / Finance approves overage and shortage from same count | Two rollup adjustments approved as one Approver session. | Both `tb_stock_in` and `tb_stock_out` `completed`; both write `tb_inventory_transaction`. Net effect = `Σ diff_qty × cost_per_unit`. |
| AC-E-02 | Tolerance threshold change effective dates | Threshold tightened from 5% to 2% mid-period. | In-flight counts retain 5% (snapshotted); new counts use 2%. Verified via parallel-count test. |
| AC-E-03 | Costing-method change after rollup posted | Sysadmin changes from `last` to `average` after a rollup is already `completed`. | Posted rollup unchanged (immutable); future rollups use `average`. |
| AC-E-04 | Auditor SoD compliance query | Auditor queries for counts where Count Lead = Approver. | Audit query returns flagged pairs; verifies the SoD rule `AC-R-04` is enforced. |
| AC-E-05 | Approver / Finance partial approval | Approver tries to approve only some lines in the rollup adjustment. | Not supported — rollup adjustment approves as a whole; partial approval requires returning to `draft` and splitting at Count Lead level. |

## 6. Configuration / Audit-Trail

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| AC-C-01 | Audit log captures every approver decision | Approver approves or rejects. | `workflow_history` on `tb_stock_in` / `tb_stock_out` records `last_action`, `last_action_by_id`, `last_action_at_date`. |
| AC-C-02 | Sysadmin reason-code change traceability | Sysadmin updates `info.glAccount` on `COUNT_OVERAGE`. | Change audit-logged; historical posted rollup-adjustments retain the **snapshotted** GL account in their inventory-transaction GL entry per [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) § 5 item 6. |
| AC-C-03 | Auditor full-chain query | Auditor queries one count end-to-end. | Returns `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail` → rollup `tb_stock_in` / `tb_stock_out` (via `info.countId`) → `tb_inventory_transaction` → GL journal entry. |
| AC-C-04 | Period close gating on count completion | Finance Manager attempts to close period with `tb_physical_count_period.status != completed`. | Period close blocked; Count Lead must complete remaining count documents first. |

> **TODO:** Expand every row with explicit `tb_*` field assertions, error messages, and (once specs exist) E2E spec line references. Validate the SoD rule wording (`AC-R-04`) against carmen-platform RBAC policy.

## 7. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — approval queue + admin configuration UI source.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related: [physical-count/03-user-flow-audit-config](/en/inventory/physical-count/03-user-flow-audit-config), [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_AUTH_003`, `PHC_POST_002`), [inventory-adjustment/04-test-scenarios-finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance) (rollup approver scenarios), [inventory-adjustment/04-test-scenarios-audit-config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config) (parallel audit / config scenarios on the adjustment side), [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) (cross-persona handoff scenarios).
