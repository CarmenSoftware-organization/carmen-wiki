---
title: Spot Check — Test Scenarios — Entry & Review Screens
description: Entry- and review-screen test cases for the spot-check module.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios — Entry & Review Screens

> **At a Glance**
> **Screens:** `spot-check/:id` (`sc-entry-component.tsx`), `spot-check/:id/review` (`sc-review-component.tsx`) &nbsp;·&nbsp; **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **Role:** same role as [04-test-scenarios-inventory-controller.md](/en/inventory/spot-check/04-test-scenarios-inventory-controller)
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no `spot-check` Playwright spec exists; scenarios are manual/planned coverage, cross-referenced against `docs/test-cases/760-spot-check.md`'s `TC-SPC-06*`/`TC-SPC-07*` rows.

## 1. Scope

The scenarios below exercise the actions catalogued in [spot-check/03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter) § 3 — line entry, notes, import/export, Save For Resume, Submit For Review, and the final Submit.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| E-F-01 | Enter `actual_qty` on a line | Any status. | Value committed to local state; "counted" indicator appears. Corresponds to `TC-SPC-060001`. |
| E-F-02 | Filter pills All/Counted/Uncounted | Mixed counted/uncounted lines present. | List narrows to the selected filter; pill counts match. Corresponds to `TC-SPC-060002`. |
| E-F-03 | Attach a note and photo to a line | Any time. | `POST /spot-check-detail-comment/:detailId` creates a `tb_spot_check_detail_comment` row with the message and attachment. Corresponds to `TC-SPC-060003`. |
| E-F-04 | Use the calculator to compute a total | Product has a case/unit conversion. | Calculator returns a total written into the line's `actual_qty`. Corresponds to `TC-SPC-060003`. |
| E-F-05 | "Set X Empty to Zero" | Some lines still uncounted. | Every uncounted line becomes `0` locally and counts as counted; footer switches to Submit For Review once `uncountedCount = 0`. Corresponds to `TC-SPC-060004`. |
| E-F-06 | Save For Resume with a partial count | Some lines have values, some do not. | `PATCH .../save` stamps `counted_at`/`counted_by_id` on the submitted lines; first call also flips `pending → in_progress`; navigates back to the list. Corresponds to `TC-SPC-060001`. |
| E-F-07 | Submit For Review once every line has a value | `uncountedCount === 0`. | `PATCH .../review` recomputes `on_hand_qty`/`diff_qty` for every line from the live ledger balance; navigates to `/review`. Corresponds to `TC-SPC-070001`. |
| E-F-08 | Review screen shows correct summary tiles | Some lines match, some are overages, some are shortages. | Matches/Variances/Overages/Shortages tiles agree with each line's `diff_qty`; negative variances render in a warning colour, positive in a success colour. Corresponds to `TC-SPC-070002`. |
| E-F-09 | Submit Spot Check (final) | On the review screen. | `PATCH .../submit` sets `doc_status = completed`; navigates back to the list; no other document is created. Corresponds to `TC-SPC-070003`. |
| E-F-10 | Export the current counts | Any time. | An `.xlsx` file downloads with id, product code/name/local name/SKU, unit, and current effective `actual_qty` per row. |
| E-F-11 | Import counts from a spreadsheet | A file with matching SKUs. | Matched rows populate their lines' local values; a toast reports matched/total/skipped counts. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| E-R-01 | User without `inventory_management.spot_check` opens `:id` directly | Permission not granted. | Access denied per the generic permission-gate mechanism; no module-specific location or assignment restriction exists to test beyond this. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| V-01 | `SPC_VAL_007` | Attempt Save on a `completed` or `void` document. | `"Cannot save items when spot check is <status>"`. |
| V-02 | `SPC_VAL_007` | Save with an empty `items[]` array (e.g. a direct API call with no payload). | `SPOT_CHECK_NO_ITEMS` ("No items to save"). |
| V-03 | `SPC_VAL_008` | Click Submit Spot Check twice in a row (second click after the first already succeeded). | Second call rejected with `"Spot check is already completed"`. |
| V-04 | (doc_version) | Save/Review with a stale `doc_version` (e.g. a second tab that has not refetched after another save). | The update fails to match and is rejected; client must reload and retry. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| E-E-01 | Submit with uncounted lines | Both Submit For Review and the final Submit succeed regardless — there is no server-side completeness check (`SPC_VAL_008`); uncounted lines simply carry a full-shortage `diff_qty` into the review. |
| E-E-02 | Reopen a `completed` spot check from the History tab and click through to Submit For Review again | `reviewItems()` has no status guard and will overwrite `on_hand_qty`/`actual_qty`/`diff_qty`/`counted_at` on every detail row; only the subsequent, terminal Submit call is blocked (`"Spot check is already completed"`). |
| E-E-03 | Reopen a `void` spot check from the History tab | Same as above — `reviewItems()` proceeds without error even though the document is voided; the final Submit is separately blocked with `"Void spot check cannot be submitted"`. |
| E-E-04 | Two counters editing the same spot check concurrently | Any user with the module permission can edit any line on any spot check (no location-scoping) — last-write-wins per line on Save; no conflict beyond a stale `doc_version` on the header-level fields. |
| E-E-05 | All lines reconcile to zero variance | Final Submit succeeds; no document of any kind is created regardless of the variance outcome — this module never posts anywhere, matched or not. |
| E-E-06 | Import partially matches | Toast reports the skipped count; unmatched lines are left exactly as they were. |

## 6. References

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/sc-entry-component.tsx`, `sc-review-component.tsx`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (`saveItems`, `reviewItems`, `getReview`, `submit`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; manual test-case catalog at `docs/test-cases/760-spot-check.md` (`TC-SPC-06*`/`TC-SPC-07*`).
- Related: [spot-check/03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter), [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) (`SPC_VAL_007`–`008`, `SPC_POST_001`–`004`), [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) (end-to-end scenarios).
