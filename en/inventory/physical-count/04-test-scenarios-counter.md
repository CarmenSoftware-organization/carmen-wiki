---
title: Physical Count — Test Scenarios — Entry & Review Screens
description: Entry- and review-screen test cases for the physical-count module.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios — Entry & Review Screens

> **At a Glance**
> **Screens:** `physical-count/:id/entry` (`pc-entry-component.tsx`), `physical-count/:id/review` (`pc-review-component.tsx`) &nbsp;·&nbsp; **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **Role:** same role as [04-test-scenarios-count-lead.md](/en/inventory/physical-count/04-test-scenarios-count-lead)
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no `physical-count` Playwright spec exists; scenarios are manual/planned coverage.

## 1. Scope

The scenarios below exercise the actions catalogued in [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter) § 3 — line entry, notes, import/export, Save, Submit for Review, and the final Submit.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| E-F-01 | Enter `actual_qty` on a line | Document `in_progress`. | Value committed to local state on blur; "counted" badge appears once a value is present. |
| E-F-02 | Save a partial set of lines | Some lines have values, some do not. | `PATCH .../save` stamps `counted_at`/`counted_by_id` on the submitted lines; `product_counted` updates. |
| E-F-03 | Attach a note and photo to a line | Any time. | `POST /physical-count-detail-comments/:detailId` creates a `tb_physical_count_detail_comment` row with the message and attachment. |
| E-F-04 | Use the calculator to compute a total | Product has a case/unit conversion the counter wants to compute. | `CalculatorDialog` returns a total that is written into the line's `actual_qty`. |
| E-F-05 | Export the current counts | Any time. | An `.xlsx` file downloads with id, product code/name/local name/SKU, unit, and current effective `actual_qty` per row. |
| E-F-06 | Import counts from a spreadsheet | A previously-exported (or externally-prepared) file with matching SKUs. | Matched rows populate their lines' local values; a toast reports matched/total/skipped counts. |
| E-F-07 | Refresh products mid-count | A product newly qualifies for the location (assigned, or now has stock). | `PATCH .../refresh` appends the new line to the sheet; existing lines are unaffected. |
| E-F-08 | Submit for Review once every line has a value | `uncountedCount === 0`. | `PATCH .../review` recomputes `on_hand_qty`/`diff_qty` for every line from the live ledger balance; navigates to `/review`. |
| E-F-09 | Review screen shows correct summary counts | Some lines match, some are overages, some are shortages. | Matches/variances/overages/shortages counts on the review screen agree with each line's `diff_qty`. |
| E-F-10 | Final Submit with mixed variance | Every line's `counted_at != null`. | `PATCH .../submit` sets `status = completed`, creates one `tb_stock_in` (overage lines) and/or one `tb_stock_out` (shortage lines), both already `doc_status = completed`; navigates back to the list screen. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| E-R-01 | User without `inventory_management.physical_count` opens `:id/entry` directly | Permission not granted. | Access denied per the generic permission-gate mechanism; no module-specific zone or assignment restriction exists to test beyond this. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| V-01 | `PHC_VAL_006` | Attempt Save, Submit for Review, or Submit on a `completed` document. | `"Physical Count is already completed"`. |
| V-02 | `PHC_VAL_004` | Click Submit (final) while at least one line's `counted_at` is still null. | `"<N> products have not been counted yet"` — see the Save-vs-Submit-for-Review caveat below. |
| V-03 | `PHC_VAL_007` | Save/Review/Submit with a stale `doc_version` (e.g. a second tab that has not refetched after another save). | `409`-style conflict; client must reload and retry. |
| V-04 | `PHC_VAL_006` | Attempt to delete a `completed` document. | `"Cannot delete completed Physical Count"`. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| E-E-01 | Every line is typed and immediately Submitted for Review, with no intervening Save | Since Save is the only action that stamps `counted_at`, and Submit for Review does not, the final Submit on the review screen may then reject with `"<N> products have not been counted yet"` even though every line visibly has a value — a direct reading of `save()` vs. `reviewItems()` in `physical-count.service.ts`; not independently confirmed by an automated test. |
| E-E-02 | Zero on shelf | Counter enters `actual_qty = 0` explicitly (not left blank); counts as a real, complete entry — a full negative variance against whatever `on_hand_qty` the review step computes. |
| E-E-03 | Set uncounted to zero, then Submit for Review | Every previously-blank line becomes `0` locally; Submit for Review is then available and recomputes real variance for those lines against the live ledger balance. |
| E-E-04 | Import partially matches | Some spreadsheet rows do not match any line's SKU. | Toast reports the skipped count; unmatched lines are left exactly as they were. |
| E-E-05 | Mixed overage and shortage in the same submit | At least one positive- and one negative-`diff_qty` line. | Both a `tb_stock_in` and a `tb_stock_out` are created by the same final Submit call. |
| E-E-06 | All lines reconcile to zero variance | Every `diff_qty = 0`. | Final Submit succeeds; no `tb_stock_in`/`tb_stock_out` is created at all. |

## 6. References

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/pc-entry-component.tsx`, `pc-review-component.tsx`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (`save`, `reviewItems`, `submit`, `refresh`, `delete`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related: [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter), [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_VAL_004`–`007`, `PHC_POST_001`–`004`), [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) (end-to-end scenarios).
