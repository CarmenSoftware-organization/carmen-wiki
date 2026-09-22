---
title: Inventory — Test Scenarios — Inventory Controller
description: Inventory Controller's test cases for the period-end review and close.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (period-end operator) &nbsp;·&nbsp; **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Surface:** `/inventory-management/period-end` + `/review`
> **E2E:** `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` — list-page tests runnable; close-workflow describes marked "Feature pending". Manual gap catalog `docs/test-cases/gaps/900-period-end-gap.md` (43 cases: TC-PE-01 list, TC-PE-02 review, TC-PE-03 start counting, TC-PE-04 close, TC-PE-31 physical-count unlock, TC-PE-32 document links).
> **Correction (2026-07-15):** the previous ~26 scenarios (adjustment approval queue, count-variance commit, stock-policy editor, variance sign-off) described surfaces that do not exist in this module; the scenarios below cover the real review/close flow.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | View the current period | A `tb_inventory_period` row with `status ∈ {open, locked}` exists | 1. Open `/inventory-management/period-end`. | Card shows period code (YYMM), fiscal year/month, start/end dates, status badge, optional note; closed-period history renders below (maps to `TC-PE-010001`). |
| IC-HP-02 | Start the counting round | Current period `open`; no open stock-moving documents | 1. Click **Start Period Close**. 2. Confirm the dialog. | `POST /period-ends/start-counting` → 200 `{ physical_count_period: { status: counting }, created }`; toast "Counting started."; navigates to `/inventory-management/period-end/review`; `GET /period-ends/review` returns `can_start_counting`, `start_blocking`, `can_close`, `close_blocking` and the per-module stats for pr/po/grn/cn/sr/si/so plus per-location count progress (maps to `TC-PE-030106`). |
| IC-HP-03 | Drill a module card | Some PRs exist in the period | 1. Click the PR card. | Dialog lists the period's PR documents (`no`, `status`, `date`), each linking to `/procurement/purchase-request/{id}`; SI/SO rows link to `/inventory-management/inventory-adjustment/{id}?type=stock-in|stock-out` (`TC-PE-020104`, `TC-PE-320102`). |
| IC-HP-04 | Open or create a location's count | Round is `counting`; a required location has no count yet | 1. Click the location card. | `POST /physical-counts` creates the count for that location and period, then deep-links to `/inventory-management/physical-count/{physical_count_id}/entry`; an existing count opens directly. Before the round is `counting` the card is disabled with "Counting has not started for this period yet." (`TC-PE-020113`). |
| IC-HP-05 | Close the period (FIFO tenant) | All gates green (`can_close: true`); BU `calculation_method = fifo` | 1. Click **Close Period**. 2. Confirm. | `POST /period-ends`; success toast; return to the list. DB: `close`/`open` carry-over transactions (new `{location_code}{YYMM}{seq4}` lots, `parent_lot_no` = old lot), `tb_inventory_period.status = closed`, next period open, `tb_physical_count_period` rows completed, **no** snapshot rows (`TC-PE-040104`). |
| IC-HP-06 | Close the period (average tenant) | As IC-HP-05 with `calculation_method = average` | Same steps | As IC-HP-05 plus issue-layer restatement at the final average and one `tb_inventory_period_snapshot` row per `(product, location)` bucket. |
| IC-HP-07 | Verify the close on the ledger | Period just closed | 1. Open the Transaction Log. 2. Filter `close`/`open`. | The close/open pair appears with the period code as `parent_document_no`. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| IC-PERM-01 | User with `inventory_management.period_end.view` opens the pages | **Allow** (read). |
| IC-PERM-02 | User with `.execute` clicks **Start Period Close** / **Close Period** | **Allow** — the two mutations in the module (gateway guard keys `period_end.startCounting` / `period_end.close`; maps to `TC-PE-010109` for the denial counterpart). |
| IC-PERM-03 | User without period-end keys navigates to `/period-end` | **Deny** — route guard redirects/blocks per the permission catalogue (`900-period-end.spec.ts` permission-denial describes). |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| IC-VAL-01 | Close blocked by documents | Any numbered SR `in_progress` mid-workflow, GRN/CN in a mid-state, or an uncounted required location | Button disabled with tooltip "All transactions must be complete and all physical counts must be completed before closing."; forced API call returns `` `Cannot close period: {total} document(s) are incomplete` `` (422) with `close_blocking` per-type counts. PR/PO in progress do not count. |
| IC-VAL-02 | Concurrency race | Two sessions close simultaneously | Second caller gets `` `Counting cannot be started for this period` `` (`PERIOD_END_COUNTING_NOT_ALLOWED`, 409 — `FOR UPDATE` re-check). |
| IC-VAL-03 | Late-arriving blocker | A blocking document is created after the review loads but before the click | The in-transaction re-validation rejects with the incomplete-documents error — the stale green screen does not win. |
| IC-VAL-04 | No current period | No `open`/`locked` period exists | List page shows the no-current-period empty state (`TC-PE-010103`); review/close unavailable (`PERIOD_END_NO_CURRENT_PERIOD`, 404). |
| IC-VAL-05 | Start counting blocked | A `draft` GRN, `draft` SI/SO, or numbered `draft`/`in_progress` SR is dated in the period | `POST /period-ends/start-counting` → 422 `` `Cannot start counting: {total} document(s) in this period are still open` ``; the "Finish these documents first" dialog lists them grouped by type with status badges and links (`TC-PE-030103`/`030104`); the round stays `draft`. |
| IC-VAL-06 | Start counting on a non-open period | Period is `locked`, or its round is already `completed` | 409 `` `Counting cannot be started for this period` ``. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| IC-EDGE-01 | Empty module card | Zero documents of a type exist in the period | The card still renders with count 0 and an Incomplete badge (`is_complete = count > 0 && …`), but the **Close Period** button follows the backend `can_close`, so the empty module does not block (`TC-PE-900201`). |
| IC-EDGE-02 | Draft GRN in the period | A GRN still at `draft` | Blocks **Start Period Close** (`listStartCountingBlockers` requires `committed`/`voided`) but does **not** block the close (`draft ∈` the close pass-list); the review card counts it as incomplete. |
| IC-EDGE-03 | Spot checks outstanding | Spot checks incomplete at month end | Close proceeds — spot check is not a gate (`validatePeriodEnd` has no spot-check validator). |
| IC-EDGE-04 | Locked current period | The period service set `status = locked` | `findCurrent` still returns it (`status ∈ {open, locked}`); the card renders it and the close can run against it. |
| IC-EDGE-05 | Year rollover | Closing fiscal month 12 | `ensureNextPeriod` creates month 1 of the next fiscal year (`period` = next `YYMM`). |
| IC-EDGE-06 | Continue Counting | Round already `counting` | The card button reads **Continue Counting** and navigates to `/review` without a second POST or confirm dialog (`TC-PE-010106`); calling the API again anyway returns `already_counting: true`. |
| IC-EDGE-07 | Lots received into the next period before the close | A GRN dated in the next (already open) period was committed before this period closed | Its layers carry `at_period` of the next period and are **not** swept by the close (`findAllRemainingLots` filters by period `end_at ≤` the closing period's). |

## 5. References

- User flow: [03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller); screen reference: [period-end](/en/inventory/inventory/period-end).
- Business rules: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_POST_009`/`INV_POST_010`, `INV_CALC_008`/`INV_CALC_009`, `INV_AUTH_008`.
- E2E: `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` (TC-PE-01xxxx runnable; TC-PE-02/03/04xxxx "Feature pending"); manual gap catalog `docs/test-cases/gaps/900-period-end-gap.md`; user stories `docs/user-stories/900-period-end.md`.
- Backend specs: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/*.spec.ts`.
