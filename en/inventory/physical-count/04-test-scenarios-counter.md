---
title: Physical Count — Test Scenarios — Counter
description: Counter / Store Keeper test cases for the physical-count module.
published: true
date: 2026-05-19T23:55:00.000Z
tags: physical-count, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios — Counter

> **At a Glance**
> **Persona:** Counter (Counter / Store Keeper) &nbsp;·&nbsp; **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **Scenarios:** ~30 (skeleton)
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no `physical-count` Playwright spec exists at `../carmen-inventory-frontend-e2e/`; scenarios are manual / planned coverage.

## 1. Persona Scope

**Counter** = Counter / Store Keeper. The floor-level worker who enters `actual_qty` per line in their assigned zone, flags damaged / unlabelled items, and signs off completed zones. The scenarios below exercise the actions catalogued in [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter) Section 3 — opening assigned sheets, entering counts, flagging items, adding comments, zone-completion signoff. Authority anchor `PHC_AUTH_002`.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| C-F-01 | Open assigned count sheet | Counter has zone-grant; count document in `pending`. | Zone-scoped lines visible; `on_hand_qty` (book) hidden if blind-count tenant policy is on. |
| C-F-02 | Enter first `actual_qty` on a line | Count document in `pending`; counter has zone-grant. | Count document advances to `in_progress`; `start_counting_at` / `start_counting_by_id` stamped on `tb_physical_count`. |
| C-F-03 | Enter `actual_qty` matching `on_hand_qty` | Line in counter's zone. | `actual_qty` saved; `diff_qty = 0`; `counted_at` / `counted_by_id` stamped on `tb_physical_count_detail`. |
| C-F-04 | Enter `actual_qty` > `on_hand_qty` (overage) | Line in counter's zone. | `actual_qty` saved; `diff_qty > 0`; line within tolerance bands if applicable. |
| C-F-05 | Enter `actual_qty` < `on_hand_qty` (shortage) | Line in counter's zone. | `actual_qty` saved; `diff_qty < 0`; line eligible for tolerance check at Count Lead level. |
| C-F-06 | Enter `actual_qty = 0` (zero on shelf) | Line with `on_hand_qty > 0`. | `actual_qty = 0` saved; `diff_qty = -on_hand_qty` (full shortage); line flagged at Count Lead level if exceeds threshold. |
| C-F-07 | Flag damaged / unlabelled / unfamiliar item | Line in counter's zone. | `tb_physical_count_detail_comment` row created with photo attachment; Count Lead is notified. |
| C-F-08 | Add count-level comment | Document in `in_progress`. | `tb_physical_count_comment` row created (e.g. `"zone B fully counted, awaiting bin re-stock check"`). |
| C-F-09 | Edit own line before submit | Counter previously entered `actual_qty`. | `actual_qty` updated; `counted_at` re-stamped; audit log retains previous-value via comment-thread. |
| C-F-10 | Sign off completed zone | All zone lines have non-null `actual_qty`. | Notification fires to Count Lead; counter cannot submit the document. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| C-R-01 | Counter attempts to enter line outside zone | Counter has zone-grant for zone A; tries to edit zone B line. | Rejected per `PHC_AUTH_004` with zone-scope error. |
| C-R-02 | Counter attempts to submit count document | All zone lines counted; Counter clicks submit. | Submit action not available to Counter per `PHC_AUTH_002`; UI guides counter to "complete zone" sign-off only. |
| C-R-03 | Counter attempts to edit a `completed` document | Document in `completed`. | Edit rejected per `PHC_VAL_008` (immutable). |
| C-R-04 | Counter without zone-grant attempts to view sheet | Counter has Counter role but no zone-grant at the location. | Document not visible in "My count assignments"; direct URL access rejected. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| C-V-01 | `PHC_VAL_005` | Counter enters negative `actual_qty`. | `"Counted quantity must be zero or positive."` |
| C-V-02 | `PHC_VAL_005` | Counter enters non-numeric `actual_qty`. | Input rejected at form level with type error. |
| C-V-03 | `PHC_VAL_004` (Count Lead facing) | Counter leaves line blank (never enters `actual_qty`). | At Count Lead submit, the document blocks with `"Cannot submit count — <N> of <M> lines remain uncounted."` Counter must enter the value. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| C-E-01 | Recount of own line — rejected | Original counter A tries to enter recount on a flagged line. | Recount must be performed by a different counter; UI prevents re-entry by same `counted_by_id`. |
| C-E-02 | Mobile / handheld scanner barcode mismatch | Counter scans barcode that doesn't match the line's `product_code`. | Scanner UI rejects; counter must locate correct line or flag as unfamiliar. |
| C-E-03 | Network drop mid-count | Counter loses connection while entering `actual_qty`. | Local cache retains entry; sync resumes on reconnect; idempotent retry. |
| C-E-04 | Two counters on same zone (concurrent) | Two counters share zone-grant on the same `tb_physical_count`. | Last-write-wins on per-line basis; comment-thread shows both counters' actions in audit log. |
| C-E-05 | Counter assigned to multiple zones | Same counter, two zone-grants on the same document. | Counter sees both zones; can enter freely across them. |
| C-E-06 | Frozen-mode count — counter sees blocked transactions | Live attempt to receive at counted location is blocked per `PHC_VAL_006`; counter aware but not blocked from continuing count. | Counter continues normally; receiving area shows lock until count completes. |

## 6. Configuration / Audit-Trail

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| C-C-01 | Blind-count tenant policy | `on_hand_qty` hidden from counter view; only product, UoM, and blank `actual_qty` shown. | Counter cannot bias entry against book; Count Lead view retains `on_hand_qty`. |
| C-C-02 | Audit log per-line counted-by stamp | Every line entered. | `tb_physical_count_detail.counted_by_id` and `counted_at` populated; audit trail intact. |
| C-C-03 | Comment thread with photo attachment | Counter flags damaged item with phone photo. | `tb_physical_count_detail_comment.attachments` carries `[{originalName, fileToken, contentType}]`. |

> **TODO:** Expand every row with explicit error messages and UI behaviour assertions once frontend / E2E sources are authored. Cross-link to cmobile-side scenarios if the PWA owns the counter UI.

## 7. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — Counter UI behaviour source; check `../cmobile/` for the PWA-side count sheet implementation if applicable.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related: [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter), [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_AUTH_002`, `PHC_AUTH_004`, `PHC_VAL_004`–`PHC_VAL_005`), [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) (cross-persona handoff scenarios).
