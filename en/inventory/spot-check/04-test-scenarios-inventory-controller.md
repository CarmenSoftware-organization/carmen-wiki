---
title: Spot Check — Test Scenarios — List & Create Screens
description: List- and create-screen test cases for the spot-check module.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, inventory-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios — List & Create Screens

> **At a Glance**
> **Screens:** `spot-check` (`sc-component.tsx`), `spot-check/location/:location_id` (`sc-form.tsx`) &nbsp;·&nbsp; **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **Role:** any user holding `inventory_management.spot_check` (same role as [04-test-scenarios-counter.md](/en/inventory/spot-check/04-test-scenarios-counter))
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no `spot-check` Playwright spec exists; scenarios are manual/planned coverage, cross-referenced against `docs/test-cases/760-spot-check.md`'s `TC-SPC-01*`/`TC-SPC-03*` rows.

## 1. Scope

The scenarios below exercise the actions catalogued in [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller) § 3 — the Locations/History list, and creating a spot check via all three sampling methods.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| L-F-01 | Load the list screen (Locations view) | Any user with the module permission. | KPI tiles (All/Resume/Not Started) and location cards render within a normal page-load window. Corresponds to `TC-SPC-010001`. |
| L-F-02 | Switch to History view | On the list screen. | View toggles to a paginated list of every spot check ever created, any status. Corresponds to `TC-SPC-010002`. |
| L-F-03 | Filter by KPI tile | Click "Resume" tile. | Only locations with a `pending`/`in_progress` spot check remain visible. Corresponds to `TC-SPC-010003`. |
| L-F-04 | Search by location name/code | Type a partial match. | List narrows client-side. Corresponds to `TC-SPC-010004`. |
| L-F-05 | Include Not Count | Check "Include Not Count". | Locations flagged `physical_count_type = no` are added to the list. Corresponds to `TC-SPC-010006`. |
| L-F-06 | Start a spot check — Random | Location has no in-flight spot check; `items ≥ 1`. | `POST /spot-checks` succeeds; document created at `pending` with `size` random detail rows; navigates to `/:id`. Corresponds to `TC-SPC-030002`. |
| L-F-07 | Start a spot check — High Value | Same, plus `items ≥ 1` and an open/locked `tb_period` exists. | Document created with the top-`items` products by value ranking. Corresponds to `TC-SPC-030003`. |
| L-F-08 | Start a spot check — Manual | Same, plus at least one product selected via the transfer picker. | Document created with exactly the selected products as detail rows. Corresponds to `TC-SPC-030004`. |
| L-F-09 | Method picker switches visible fields | On the create screen, click each method card. | Random/High Value show an Items field (High Value adds Min Value); Manual shows the product transfer picker instead. Corresponds to `TC-SPC-030005`. |
| L-F-10 | Product transfer (Manual) | Method = Manual. | Products move between Available/Selected columns; counters update; select-all and empty-search states work. Corresponds to `TC-SPC-030006`. |
| L-F-11 | Resume an in-progress location | Location has a `pending`/`in_progress` spot check. | Navigates directly to `/:id`; no new document created. Corresponds to `TC-SPC-060005`. |
| L-F-12 | Reset a spot check | Location has a `pending`/`in_progress` spot check; click Reset, confirm. | `doc_status → void`; detail rows untouched; location falls back to Not Started. Corresponds to `TC-SPC-060006`. |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| L-R-01 | User without `inventory_management.spot_check` opens the list screen | Permission not granted. | Access denied per the generic permission-gate mechanism shared across the product; no module-specific override exists. Corresponds to `TC-SPC-100001`. |
| L-R-02 | Unauthenticated user opens the list screen directly | No session. | Redirected to `/login`. Corresponds to `TC-SPC-100002`. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| L-V-01 | `SPC_VAL_002` | Start a spot check for a location with an empty eligible product pool. | `"No products found at this location"`. |
| L-V-02 | `SPC_VAL_003` | Method = Manual; leave Products Selected empty; click Create. | Client-side error under the product transfer ("at least one product required"); backend would also reject with `"product_id is required for manual selection"`. Corresponds to `TC-SPC-200002`. |
| L-V-03 | (client) | Method = Random or High Value; leave Items at `0`; click Create. | Client-side error requiring `items ≥ 1`. Corresponds to `TC-SPC-200001`. |
| L-V-04 | (client) | Method = High Value; enter a negative Min Value; click Create. | Client-side error requiring `min_value ≥ 0`. Corresponds to `TC-SPC-200003`. |
| L-V-05 | `SPC_VAL_004` | Method = High Value; no `tb_period` has `status ∈ {open, locked}`. | `SPOT_CHECK_NO_ACTIVE_PERIOD` ("No active period found"). |
| L-V-06 | `SPC_VAL_006` | Click Reset on a spot check that is already `void` or `completed` — not reachable through the shipped UI (Reset is only rendered for `pending`/`in_progress` items), but a direct API retry would hit this. | `"Spot check is already void"` / `"Completed spot check cannot be reset"`. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| L-E-01 | Manual selection includes a product outside the location's eligible pool | If it is the only product selected, creation fails with `"None of the selected products were found at this location"` (`SPC_VAL_003`); mixed with valid products, it is silently dropped. |
| L-E-02 | Start a spot check twice in quick succession for the same location | Two independent `tb_spot_check` documents are created (unlike physical-count's idempotent resume path — there is no equivalent duplicate-detection in `spot-check.service.ts`'s `create()`). Both would show under the location's Resume section, though the UI only surfaces the single latest one. |
| L-E-03 | Reset then immediately re-Start | Reset voids the old document; Start creates a brand-new one with a fresh sample — the two are entirely independent, with no data carried over. |

## 6. References

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/sc-component.tsx`, `sc-form.tsx`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (`create`, `reset`, `findCurrentByLocation`), `spot-check.logic.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; manual test-case catalog at `docs/test-cases/760-spot-check.md` (`TC-SPC-01*`/`TC-SPC-03*`/`TC-SPC-06*`/`TC-SPC-10*`/`TC-SPC-20*`).
- Related: [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller), [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) (`SPC_VAL_001`–`004`, `SPC_VAL_006`, `SPC_AUTH_001`), [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) (end-to-end scenarios).
