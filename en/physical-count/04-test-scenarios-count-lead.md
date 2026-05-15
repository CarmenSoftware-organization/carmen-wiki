---
title: Physical Count — Test Scenarios — Count Lead
description: Count Lead (Inventory Controller / Manager) test cases for the physical-count module.
published: true
date: 2026-05-15T14:00:00.000Z
tags: physical-count, test-scenarios, count-lead, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios — Count Lead

## 1. Persona Scope

**Count Lead** = Inventory Controller / Inventory Manager. The owner of the count exercise. The scenarios below exercise the actions catalogued in [[physical-count/03-user-flow-count-lead]] Section 3 — period and document creation, mode selection, counter assignment, progress monitoring, recount-flag resolution, override / accept variance, submit, and rollup routing. Authority anchor `PHC_AUTH_001`.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| CL-F-01 | Open count period | `tb_period` is `open` per `INV_VAL_008`; no existing `tb_physical_count_period` for this period. | New `tb_physical_count_period` in `draft`; visible in period scheduler. |
| CL-F-02 | Generate count sheet for a single location (frozen mode) | Period in `draft` or `counting`; target location is inventory-type. | New `tb_physical_count` in `pending`; `physical_count_type = yes`; on-hand snapshot captured per product; `product_total > 0`. |
| CL-F-03 | Generate count sheet (live mode) | Same as CL-F-02. | `tb_physical_count` with `physical_count_type = no`; parallel inventory writes permitted per `PHC_VAL_006`. |
| CL-F-04 | Assign counter to zone | Count document in `pending`; counter exists. | Counter zone-grant recorded; counter sees the assignment in their "My count assignments" entry. |
| CL-F-05 | Monitor live progress | Count document in `in_progress`. | `product_counted` / `product_total` visible and updating; `PHC_CALC_004` correct. |
| CL-F-06 | Flag variance line for recount | Line with `|diff_qty| / on_hand_qty` over threshold per `PHC_VAL_007`. | Detail-comment with recount tag; submit blocked until recount flag is resolved. |
| CL-F-07 | Override / accept variance with countersignature | Recount confirms original; variance not investigatable further. | Flag cleared; line eligible for rollup; comment-thread carries override countersignature stamped with `created_by_id`. |
| CL-F-08 | Submit count — all lines counted, no open flags | `product_counted == product_total`; no open `PHC_VAL_007` flags. | `tb_physical_count.status = completed`; rollup `tb_stock_in` (overage) and / or `tb_stock_out` (shortage) created with `info.countId`. |
| CL-F-09 | Route rollup adjustment for approval | Rollup adjustment in `draft` (or `in_progress` if above auto-approve). | Adjustment visible in Approver / Finance queue per `ADJ_AUTH_*`. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| CL-R-01 | Non-Count-Lead attempts to open period | User without Count Lead role attempts `tb_physical_count_period` create. | Rejected per `PHC_AUTH_001`. |
| CL-R-02 | Count Lead with no scope at location | Count Lead role assigned but no `tb_user_location` for target location. | Sheet-gen rejected with scope error. |
| CL-R-03 | Cross-tenant attempt | Count Lead from tenant A attempts to operate on tenant B period. | Rejected at API auth layer (multi-tenancy guard). |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| CL-V-01 | `PHC_VAL_001` | Generate `tb_physical_count` for a period that is `completed`. | `"Cannot add count to a completed period."` |
| CL-V-02 | `PHC_VAL_002` | Attempt to change `physical_count_type` once document is `in_progress`. | `"Cannot change mode on a started count."` |
| CL-V-03 | `PHC_VAL_003` | Target a direct-cost location for count-sheet generation. | `"Direct-cost locations cannot be physically counted."` |
| CL-V-04 | `PHC_VAL_004` | Submit with uncounted lines. | `"Cannot submit count — <N> of <M> lines remain uncounted."` |
| CL-V-05 | `PHC_VAL_007` | Submit with open recount-flagged lines. | `"Cannot submit — <K> variance line(s) await recount resolution."` |
| CL-V-06 | `PHC_VAL_008` | Attempt to edit a `completed` count document. | `"Cannot edit a completed count. Raise a manual inventory adjustment."` |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| CL-E-01 | Counter assigned mid-count to a zone with partially-completed lines | Counter sees own zone's already-counted lines (read-only) plus uncounted lines (editable). |
| CL-E-02 | Tolerance threshold tightened mid-count | In-flight count retains the threshold snapshotted at sheet-gen; new counts use the new threshold. |
| CL-E-03 | Concurrent submit attempts (Count Lead clicks submit twice) | Second submit no-ops (idempotent); rollup created once; audit log shows single submit. |
| CL-E-04 | All variance lines reconcile within tolerance | No rollup adjustment created (every `diff_qty = 0` or below tolerance + within zero); document `completed` with no downstream effect. |
| CL-E-05 | Count spans midnight / mid-period boundary | `start_counting_at` and `completed_at` straddle dates; period-containment check uses count completion date. |

## 6. Configuration / Audit-Trail

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| CL-C-01 | Count Lead changes counter assignment mid-count | New counter sees zone; previous counter loses edit access on the zone (read-only audit). |
| CL-C-02 | Audit log captures every state transition + comment | `tb_physical_count.status` history + `tb_physical_count_comment` thread fully readable; `created_by_id` / `counted_by_id` populated. |
| CL-C-03 | Rollup linkage verification | `tb_stock_in.info.countId` and `tb_stock_out.info.countId` reference the source `tb_physical_count.id`. |

> **TODO:** Expand every row with explicit `tb_*` field assertions and expected error message text once frontend / E2E sources are authored. Cross-link to E2E specs once `physical-count.spec.ts` is added at `../carmen-inventory-frontend-e2e/tests/`.

## 7. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — Count Lead UI behaviour source.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related: [[physical-count/03-user-flow-count-lead]], [[physical-count/02-business-rules]] (`PHC_AUTH_001`, `PHC_VAL_*`, `PHC_POST_*`), [[physical-count/04-test-scenarios]] (cross-persona handoff scenarios).
