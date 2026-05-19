---
title: Spot Check — Test Scenarios — Counter
description: Counter test cases for the spot-check module.
published: true
date: 2026-05-17T11:00:00.000Z
tags: spot-check, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios — Counter

> **At a Glance**
> **Persona:** Counter (floor-level data entry) &nbsp;·&nbsp; **Module:** [[spot-check]] &nbsp;·&nbsp; **Scenarios:** ~26
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** none — no spot-check Playwright spec exists yet in `../carmen-inventory-frontend-e2e/tests/`

## 1. Persona Scope

**Counter** — the floor-level worker who enters `actual_qty` per line on assigned spot checks, flags damaged / unlabelled items, and signs off completed sheets. The scenarios below exercise the actions catalogued in [[spot-check/03-user-flow-counter]] Section 3 — opening assigned sheets, entering counts, flagging items, adding comments, completion signoff. Authority anchor `SPC_AUTH_002`.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| C-F-01 | Open assigned spot-check sheet | Counter has location-grant; spot check in `pending`. | Detail lines visible; `on_hand_qty` (book) hidden if blind-count tenant policy is on (TODO confirm). |
| C-F-02 | Enter first `actual_qty` on a line | Spot check in `pending`; counter has location-grant. | Spot check advances to `in_progress`. |
| C-F-03 | Enter `actual_qty` matching `on_hand_qty` | Line on assigned spot check. | `actual_qty` saved; `diff_qty = 0`; `counted_at` / `counted_by_id` stamped on `tb_spot_check_detail`. |
| C-F-04 | Enter `actual_qty` > `on_hand_qty` (overage) | Line on assigned spot check. | `actual_qty` saved; `diff_qty > 0`; line within tolerance bands if applicable. |
| C-F-05 | Enter `actual_qty` < `on_hand_qty` (shortage) | Line on assigned spot check. | `actual_qty` saved; `diff_qty < 0`; line eligible for tolerance check at controller level. |
| C-F-06 | Enter `actual_qty = 0` (zero on shelf) | Line with `on_hand_qty > 0`. | `actual_qty = 0` saved; `diff_qty = -on_hand_qty` (full shortage); line flagged at controller level if exceeds threshold. |
| C-F-07 | Flag damaged / unlabelled / unfamiliar item | Line on assigned spot check. | `tb_spot_check_detail_comment` row created with photo attachment; Inventory Controller notified. |
| C-F-08 | Add spot-check-level comment | Spot check in `in_progress`. | `tb_spot_check_comment` row created (e.g. `"shelf restock under way, recommend recount line 4"`). |
| C-F-09 | Edit own line before submit | Counter previously entered `actual_qty`. | `actual_qty` updated; `counted_at` re-stamped; audit log retains previous-value via comment-thread. |
| C-F-10 | Sign off completed sheet | All lines have non-null `actual_qty`. | Notification fires to Inventory Controller; counter cannot submit the document. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| C-R-01 | Counter attempts to enter line outside location | Counter has location-grant for Location A; tries to edit a Location B spot check. | Rejected per `SPC_AUTH_004` with location-scope error. |
| C-R-02 | Counter attempts to submit spot check | All lines counted; Counter clicks submit. | Submit action not available to Counter per `SPC_AUTH_002`; UI guides counter to "complete sheet" sign-off only. |
| C-R-03 | Counter attempts to edit a `completed` spot check | Spot check in `completed`. | Edit rejected per `SPC_VAL_007` (immutable). |
| C-R-04 | Counter without location-grant attempts to view sheet | Counter has Counter role but no location-grant. | Document not visible in "My spot-check assignments"; direct URL access rejected. |
| C-R-05 | Counter attempts to void spot check | Counter clicks void. | Action not available; only Inventory Controller can void per `SPC_AUTH_001`. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| C-V-01 | `SPC_VAL_005` | Counter enters negative `actual_qty`. | `"Counted quantity must be zero or positive."` |
| C-V-02 | `SPC_VAL_005` | Counter enters non-numeric `actual_qty`. | Input rejected at form level with type error. |
| C-V-03 | `SPC_VAL_004` (controller-facing) | Counter leaves line blank (never enters `actual_qty`). | At Inventory Controller submit, the document blocks with `"Cannot submit spot check — <N> of <M> lines remain uncounted."` Counter must enter the value. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| C-E-01 | Recount of own line — discouraged | Original counter A tries to enter recount on a flagged line. | Convention: recount by a different counter; UI may warn but not hard-block (TODO confirm). |
| C-E-02 | Mobile / handheld scanner barcode mismatch | Counter scans barcode that doesn't match the line's `product_code`. | Scanner UI rejects; counter must locate correct line or flag as unfamiliar. |
| C-E-03 | Network drop mid-count | Counter loses connection while entering `actual_qty`. | Local cache retains entry; sync resumes on reconnect; idempotent retry. |
| C-E-04 | Two counters on same spot check (concurrent) | Two counters share location-grant on the same `tb_spot_check`. | Last-write-wins on per-line basis; comment-thread shows both counters' actions in audit log. |
| C-E-05 | Spot check voided while counter is entering | Inventory Controller voids; counter has unsaved entry. | Subsequent save rejected with `"Spot check is voided."`; counter's partial entries preserved up to void time. |

## 6. Configuration / Audit-Trail

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| C-C-01 | Blind-count tenant policy (if applicable) | `on_hand_qty` hidden from counter view; only product, UoM, and blank `actual_qty` shown. | Counter cannot bias entry against book; Inventory Controller view retains `on_hand_qty`. (TODO confirm tenant policy applies to spot-check.) |
| C-C-02 | Audit log per-line counted-by stamp | Every line entered. | `tb_spot_check_detail.counted_by_id` and `counted_at` populated; audit trail intact. |
| C-C-03 | Comment thread with photo attachment | Counter flags damaged item with phone photo. | `tb_spot_check_detail_comment.attachments` carries `[{originalName, fileToken, contentType}]`. |

> **TODO:** Expand every row with explicit error messages and UI behaviour assertions once frontend / E2E sources are authored. Cross-link to cmobile-side scenarios if the PWA owns the counter UI. Confirm blind-count policy applicability for spot-check.

## 7. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — Counter UI behaviour source; check `../cmobile/` for the PWA-side spot-check sheet implementation if applicable.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists.
- Related: [[spot-check/03-user-flow-counter]], [[spot-check/02-business-rules]] (`SPC_AUTH_002`, `SPC_AUTH_004`, `SPC_VAL_004`–`SPC_VAL_005`), [[spot-check/04-test-scenarios]] (cross-persona handoff scenarios), [[physical-count/04-test-scenarios-counter]] (full-count counterpart scenarios).
