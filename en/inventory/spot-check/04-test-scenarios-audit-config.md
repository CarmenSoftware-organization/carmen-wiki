---
title: Spot Check — Test Scenarios — Audit & Config
description: Auditor and Sysadmin test cases for the spot-check module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, test-scenarios, audit, config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor read-only + Sysadmin config) &nbsp;·&nbsp; **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **Scenarios:** ~23
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** none — no spot-check Playwright spec exists yet in `../carmen-inventory-frontend-e2e/tests/`

## 1. Persona Scope

The **Audit / Config** persona group collapses two roles whose touch on the spot-check module is observation or configuration. The scenarios below exercise the actions catalogued in [spot-check/03-user-flow-audit-config](/en/inventory/spot-check/03-user-flow-audit-config) Section 3 — in-progress observation and full-chain inspection (Auditor), tolerance / default-size / default-method / reason-code configuration (Sysadmin, implicit). Authority anchor `SPC_AUTH_003`. Note: the **rollup approval action lands on [inventory-adjustment](/en/inventory/inventory-adjustment) documents, not on `tb_spot_check`** — many scenarios below cross-reference [inventory-adjustment/04-test-scenarios-finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance) and [inventory-adjustment/04-test-scenarios-audit-config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config).

## 2. Functional — Happy Paths

| # | Scenario | Persona | Pre-condition | Expected outcome |
| - | -------- | ------- | ------------- | ---------------- |
| AC-F-01 | Auditor observes spot check in progress | Auditor | Spot check in `in_progress`. | Read-only view: live `actual_qty` entries, counter assignment, recount flags. Auditor may attach observation note as `tb_spot_check_comment`. |
| AC-F-02 | Auditor inspects full chain | Auditor | Spot check `completed`; rollup adjustment `completed`. | Read-only trace: spot-check sheet → recount records → approvals → posted adjustment → inventory transaction → journal entry. No gaps. |
| AC-F-03 | Auditor verifies SoD on rollup approval | Auditor | Rollup adjustment `completed`. | Auditor query confirms `tb_stock_in.created_by_id` ≠ approval `last_action_by_id`. |
| AC-F-04 | Sysadmin configures tolerance threshold | Sysadmin | New tenant policy. | Tenant default updated; future spot checks use new threshold per `SPC_VAL_006`. |
| AC-F-05 | Sysadmin configures default sampling size | Sysadmin | Tenant policy change. | Tenant default updated; future spot checks default to new `size` unless overridden. |
| AC-F-06 | Sysadmin configures default sampling method | Sysadmin | Tenant policy change (e.g. switch from `random` to `high_value`). | Tenant default updated; future spot checks default to new `method`. |
| AC-F-07 | Sysadmin maps reason codes for rollup | Sysadmin | New tenant onboarding. | `tb_adjustment_type` rows for `SPOT_CHECK_OVERAGE` (`type = STOCK_IN`) and `SPOT_CHECK_SHORTAGE` (`type = STOCK_OUT`) created with `info.glAccount` — or aliased to existing `COUNT_*` codes per tenant convention. Per [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) § 2.1. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| AC-R-01 | Auditor attempts to edit spot check | Auditor role only. | Edit rejected; read-only enforced for Auditor at both levels (header, detail). |
| AC-R-02 | Auditor attempts to void spot check | Auditor role only. | Action rejected; only Inventory Controller can void per `SPC_AUTH_001`. |
| AC-R-03 | Sysadmin attempts to perform a spot check | Sysadmin role only. | If Sysadmin lacks Inventory Controller role, spot-check actions rejected. Sysadmin configures, does not operate. |
| AC-R-04 | Approval — SoD with spot-check submitter | Same user is both Inventory Controller (spot-check) and Approver (rollup adjustment). | SoD check rejects on the [inventory-adjustment](/en/inventory/inventory-adjustment) side: rollup approver must differ from spot-check submitter. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| AC-V-01 | `INV_VAL_008` (inherited) | Rollup adjustment submit into `closed` period. | `"Cannot post into period <YYMM>: period is closed."` Finance Manager must re-open. |
| AC-V-02 | `ADJ_VAL_002` (downstream) | Sysadmin mis-maps `SPOT_CHECK_OVERAGE` to `type = STOCK_OUT`. | Reason-code save rejected at adjustment-type form per direction validation in [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) `ADJ_VAL_002`. |
| AC-V-03 | `SPC_AUTH_003` | Auditor attempts to approve rollup adjustment. | Action rejected; Auditor is read-only on the rollup approval path. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| AC-E-01 | Approval of overage and shortage from same spot check (cross-module) | Two rollup adjustments approved on the [inventory-adjustment](/en/inventory/inventory-adjustment) side. | Both `tb_stock_in` and `tb_stock_out` `completed`; both write `tb_inventory_transaction`. Net effect = `Σ diff_qty × cost_per_unit`. |
| AC-E-02 | Tolerance threshold change effective dates | Threshold tightened from 5% to 2% mid-day. | In-flight spot checks retain 5% (snapshotted); new spot checks use 2%. Verified via parallel spot-check test. |
| AC-E-03 | Default-`method` change after spot check generated | Sysadmin changes default from `random` to `high_value` after a `random` spot check is already `in_progress`. | In-flight spot check unchanged (uses `random` per its own `method` field); future spot checks default to `high_value`. |
| AC-E-04 | Auditor SoD compliance query | Auditor queries for spot checks where submitter = rollup approver. | Audit query returns flagged pairs; verifies the SoD rule `AC-R-04` is enforced. |
| AC-E-05 | Spot check voided after rollup adjustment is `in_progress` | Inventory Controller tries to void after adjustment is routed for approval. | Void rejected because rollup is already downstream; reversal must go through [inventory-adjustment](/en/inventory/inventory-adjustment). |

## 6. Configuration / Audit-Trail

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| AC-C-01 | Audit log captures every approver decision (downstream) | Approver approves or rejects rollup. | `workflow_history` on `tb_stock_in` / `tb_stock_out` records `last_action`, `last_action_by_id`, `last_action_at_date`. |
| AC-C-02 | Sysadmin reason-code change traceability | Sysadmin updates `info.glAccount` on `SPOT_CHECK_OVERAGE`. | Change audit-logged; historical posted rollup-adjustments retain the **snapshotted** GL account in their inventory-transaction GL entry per [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) § 5 item 6. |
| AC-C-03 | Auditor full-chain query | Auditor queries one spot check end-to-end. | Returns `tb_spot_check` → `tb_spot_check_detail` → rollup `tb_stock_in` / `tb_stock_out` (via `info.spotCheckId`) → `tb_inventory_transaction` → GL journal entry. |
| AC-C-04 | Auditor lists `void` spot checks | Auditor queries `doc_status = void`. | Returns voided spot checks with partial entries preserved; no associated `tb_inventory_transaction` rows. |

> **TODO:** Expand every row with explicit `tb_*` field assertions, error messages, and (once specs exist) E2E spec line references. Validate the SoD rule wording (`AC-R-04`) against carmen-platform RBAC policy. Confirm reason-code naming (`SPOT_CHECK_*` vs reused `COUNT_*`) once tenant convention is established.

## 7. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — audit query + admin configuration UI source.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists.
- Related: [spot-check/03-user-flow-audit-config](/en/inventory/spot-check/03-user-flow-audit-config), [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) (`SPC_AUTH_003`, `SPC_POST_002`), [inventory-adjustment/04-test-scenarios-finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance) (rollup approver scenarios), [inventory-adjustment/04-test-scenarios-audit-config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config) (parallel audit / config scenarios on the adjustment side), [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) (cross-persona handoff scenarios), [physical-count/04-test-scenarios-audit-config](/en/inventory/physical-count/04-test-scenarios-audit-config) (full-count counterpart scenarios including Approver/Finance flow).
