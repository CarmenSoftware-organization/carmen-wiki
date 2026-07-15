---
title: Inventory — Test Scenarios — Inventory Controller
description: Inventory Controller's test cases for the period-end review and close.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (period-end operator) &nbsp;·&nbsp; **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Surface:** `/inventory-management/period-end` + `/review`
> **E2E:** `900-period-end.spec.ts` — list-page tests runnable; close-workflow describes marked "Feature pending"
> **Correction (2026-07-15):** the previous ~26 scenarios (adjustment approval queue, count-variance commit, stock-policy editor, variance sign-off) described surfaces that do not exist in this module; the scenarios below cover the real review/close flow.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | View the current period | A `tb_period` row with `status ∈ {open, locked}` exists | 1. Open `/inventory-management/period-end`. | Card shows period code (YYMM), fiscal year/month, start/end dates, status badge, optional note; closed-period history renders below (maps to `TC-PE-010001`). |
| IC-HP-02 | Open the review | Current period exists | 1. Click the start-close button. | Navigates to `/inventory-management/period-end/review`; `GET /period-ends/review` returns the per-module blocking-document stats (pr/po/grn/cn/sr) and per-location count progress. |
| IC-HP-03 | Drill a module card | Some PRs exist in the period | 1. Click the PR card. | Dialog lists the period's PR documents (`no`, `status`, `date`) so the blocking ones can be chased. |
| IC-HP-04 | Jump to an in-progress count | A required location has a count in progress | 1. Click the location row. | Deep-links to `/inventory-management/physical-count/{physical_count_id}/entry`. |
| IC-HP-05 | Close the period (FIFO tenant) | All gates green; BU `calculation_method = fifo` | 1. Click **Close period**. 2. Confirm. | `POST /period-ends`; success toast; return to the list. DB: `close`/`open` carry-over transactions (`CLOSE-…`/`OPEN-…` lots), `tb_period.status = closed`, next period open, `tb_physical_count_period` rows completed, **no** snapshot rows. |
| IC-HP-06 | Close the period (average tenant) | As IC-HP-05 with `calculation_method = average` | Same steps | As IC-HP-05 plus issue-layer restatement at the final average and one `tb_period_snapshot` row per `(product, location)` bucket. |
| IC-HP-07 | Verify the close on the ledger | Period just closed | 1. Open the Transaction Log. 2. Filter `close`/`open`. | The close/open pair appears with the period code as `parent_document_no`. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| IC-PERM-01 | User with `inventory_management.period_end.view` opens the pages | **Allow** (read). |
| IC-PERM-02 | User with `.execute` clicks **Close period** | **Allow** — this is the only mutation in the module (maps to `TC-PE-010002` / `TC-PE-040003` denial counterparts for users without the keys). |
| IC-PERM-03 | User without period-end keys navigates to `/period-end` | **Deny** — route guard redirects/blocks per the permission catalogue (`900-period-end.spec.ts` permission-denial describes). |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| IC-VAL-01 | Close blocked by documents | Any PR/PO/SR `in_progress` mid-workflow, GRN/CN in a mid-state, or an uncounted required location | Button disabled; forced API call returns `` `Cannot close period: incomplete documents {"pr":…}` `` with per-type counts. |
| IC-VAL-02 | Concurrency race | Two sessions close simultaneously | Second caller gets `` `Period already closed` `` (`FOR UPDATE` re-check). |
| IC-VAL-03 | Late-arriving blocker | A blocking document is created after the review loads but before the click | The in-transaction re-validation rejects with the incomplete-documents error — the stale green screen does not win. |
| IC-VAL-04 | No current period | No `open`/`locked` period exists | List page shows the no-current-period empty state (`TC-PE-010004`); review/close unavailable. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| IC-EDGE-01 | Empty module quirk | Zero documents of a type exist in the period | Frontend card computes `is_complete = count > 0 && …` → renders **incomplete** and keeps Close disabled, even though the backend gate counts zero blockers. Known FE/BE discrepancy for empty periods. |
| IC-EDGE-02 | Draft GRN in the period | A GRN still at `draft` | Does **not** block the backend close (`draft ∈` the GRN pass-list); the review card counts it against `GRN_COMPLETE = {committed, voided}` though — another card-level strictness mismatch. |
| IC-EDGE-03 | Spot checks outstanding | Spot checks incomplete at month end | Close proceeds — spot check is not a gate (`validatePeriodEnd` has no spot-check validator). |
| IC-EDGE-04 | Locked current period | The period service set `status = locked` | `findCurrent` still returns it (`status ∈ {open, locked}`); the card renders it and the close can run against it. |
| IC-EDGE-05 | Year rollover | Closing fiscal month 12 | `ensureNextPeriod` creates month 1 of the next fiscal year (`period` = next `YYMM`). |

## 5. References

- User flow: [03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller); screen reference: [period-end](/en/inventory/inventory/period-end).
- Business rules: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_POST_009`/`INV_POST_010`, `INV_CALC_008`/`INV_CALC_009`, `INV_AUTH_008`.
- E2E: `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` (TC-PE-01xxxx runnable; TC-PE-02/03/04xxxx "Feature pending").
- Backend specs: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/*.spec.ts`.
