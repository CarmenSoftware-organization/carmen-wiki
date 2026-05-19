---
title: Spot Check — Test Scenarios — Inventory Controller
description: Inventory Controller test cases for the spot-check module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, test-scenarios, inventory-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (owner of the spot-check exercise) &nbsp;·&nbsp; **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **Scenarios:** ~29
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** none — no spot-check Playwright spec exists yet in `../carmen-inventory-frontend-e2e/tests/`

## 1. Persona Scope

**Inventory Controller** — the owner of the spot-check exercise. The scenarios below exercise the actions catalogued in [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller) Section 3 — spot-check creation across all three `method` values, counter assignment, progress monitoring, recount-flag resolution, override / accept variance, submit, void, and rollup routing. Authority anchor `SPC_AUTH_001`.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| IC-F-01 | Open spot check with random sampling | Inventory-type location; `size = 10`. | New `tb_spot_check` in `pending`; `method = random`; 10 detail rows sampled; `on_hand_qty` snapshot captured per line. |
| IC-F-02 | Open spot check with high-value sampling | Inventory-type location; `size = 10`. | New `tb_spot_check` in `pending`; `method = high_value`; top-10 by value-on-hand sampled. |
| IC-F-03 | Open spot check with manual selection | Inventory-type location; controller picks 3 products. | New `tb_spot_check` in `pending`; `method = manual`; 3 detail rows added explicitly. |
| IC-F-04 | Assign counter | Spot check in `pending`; counter exists with location-grant. | Counter sees the assignment in their "My spot-check assignments". |
| IC-F-05 | Monitor live progress | Spot check in `in_progress`. | Lines with `actual_qty` populated visible vs total; `SPC_CALC_004` correct (derived, not persisted). |
| IC-F-06 | Flag variance line for recount | Line with `|diff_qty| / on_hand_qty` over threshold per `SPC_VAL_006`. | Detail-comment with recount tag; submit blocked until recount flag resolved. |
| IC-F-07 | Override / accept variance with countersignature | Recount confirms original; variance not investigatable further. | Flag cleared; line eligible for rollup; comment-thread carries override countersignature stamped with `created_by_id`. |
| IC-F-08 | Submit spot check — all lines counted, no open flags | All detail lines have `actual_qty`; no open `SPC_VAL_006` flags. | `doc_status = completed`; rollup `tb_stock_in` (overage) and / or `tb_stock_out` (shortage) created with `info.spotCheckId`. |
| IC-F-09 | Route rollup adjustment for approval | Rollup adjustment in `draft` (or `in_progress` if above auto-approve). | Adjustment visible in Approver / Finance queue per `ADJ_AUTH_*`. |
| IC-F-10 | Void spot check before counting | Spot check in `pending`. | `doc_status = void`; no rollup; preserved for audit. |
| IC-F-11 | Void spot check mid-count | Spot check in `in_progress` with partial entries. | `doc_status = void`; partial entries preserved; no rollup. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| IC-R-01 | Non-Inventory-Controller attempts to open spot check | User without role attempts create. | Rejected per `SPC_AUTH_001`. |
| IC-R-02 | Inventory Controller with no scope at location | Role assigned but no `tb_user_location` for target. | Sheet-gen rejected with scope error. |
| IC-R-03 | Cross-tenant attempt | Controller from tenant A attempts to operate on tenant B spot check. | Rejected at API auth layer (multi-tenancy guard). |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| IC-V-01 | `SPC_VAL_001` | Generate `tb_spot_check` against a direct-cost location. | `"Direct-cost locations cannot be spot-checked."` |
| IC-V-02 | `SPC_VAL_002` | Submit `method = random` spot check with `size = 0`. | `"Sample size must be greater than zero for random / high_value methods."` |
| IC-V-03 | `SPC_VAL_002` | Submit `method = manual` spot check with zero detail rows. | `"Manual spot check requires at least one product line before submit."` |
| IC-V-04 | `SPC_VAL_004` | Submit with uncounted lines. | `"Cannot submit spot check — <N> of <M> lines remain uncounted."` |
| IC-V-05 | `SPC_VAL_006` | Submit with open recount-flagged lines. | `"Cannot submit — <K> variance line(s) await recount resolution."` |
| IC-V-06 | `SPC_VAL_007` | Attempt to edit a `completed` spot check. | `"Cannot edit a completed spot check. Raise a manual inventory adjustment."` |
| IC-V-07 | `SPC_VAL_008` | Attempt to void a `completed` spot check. | `"Cannot void a completed spot check — reverse via inventory adjustment."` |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| IC-E-01 | Random sample `size` exceeds available distinct products at location | Sample truncated per `SPC_VAL_003`; difference logged on `tb_spot_check.info`; sheet generated with available product count. |
| IC-E-02 | Tolerance threshold tightened mid-spot-check | In-flight spot check retains the threshold snapshotted at sheet-gen; new spot checks use the new threshold. |
| IC-E-03 | Concurrent submit attempts (Inventory Controller clicks submit twice) | Second submit no-ops (idempotent); rollup created once; audit log shows single submit. |
| IC-E-04 | All variance lines reconcile to zero | No rollup adjustment created (every `diff_qty = 0`); document `completed` with no downstream effect. |
| IC-E-05 | High-value sample with tied values | Tie-breaker by `product_code` ascending (or tenant-configured tie-breaker) ensures deterministic selection. |

## 6. Configuration / Audit-Trail

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| IC-C-01 | Inventory Controller changes counter assignment mid-check | New counter sees the spot check; previous counter loses edit access (read-only audit). |
| IC-C-02 | Audit log captures every state transition + comment | `tb_spot_check.doc_status` history + `tb_spot_check_comment` thread fully readable; `created_by_id` / `counted_by_id` populated. |
| IC-C-03 | Rollup linkage verification | `tb_stock_in.info.spotCheckId` and `tb_stock_out.info.spotCheckId` reference the source `tb_spot_check.id`. |

> **TODO:** Expand every row with explicit `tb_*` field assertions and expected error message text once frontend / E2E sources are authored. Cross-link to E2E specs once `spot-check.spec.ts` is added at `../carmen-inventory-frontend-e2e/tests/`. Verify reason-code naming (`SPOT_CHECK_*` vs reused `COUNT_*`) when defined.

## 7. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — Inventory Controller UI behaviour source.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists.
- Related: [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller), [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) (`SPC_AUTH_001`, `SPC_VAL_*`, `SPC_POST_*`), [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) (cross-persona handoff scenarios), [physical-count/04-test-scenarios-count-lead](/en/inventory/physical-count/04-test-scenarios-count-lead) (full-count counterpart scenarios).
