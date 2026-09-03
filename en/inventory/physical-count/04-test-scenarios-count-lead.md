---
title: Physical Count — Test Scenarios — List Screen
description: List-screen test cases for the physical-count module.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, count-lead, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios — List Screen

> **At a Glance**
> **Screen:** `physical-count` (`pc-component.tsx`) &nbsp;·&nbsp; **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **Role:** any user holding `inventory_management.physical_count` (same role as [04-test-scenarios-counter.md](/en/inventory/physical-count/04-test-scenarios-counter))
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no `physical-count` Playwright spec exists; scenarios are manual/planned coverage.

## 1. Scope

The scenarios below exercise the list screen's actions catalogued in [physical-count/03-user-flow-count-lead](/en/inventory/physical-count/03-user-flow-count-lead) § 3 — period auto-provisioning, filtering, and starting/resuming a count.

## 2. Functional — Happy Paths

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| L-F-01 | Load the list screen for a brand-new fiscal period | No `tb_physical_count_period` exists yet for the current open `tb_period`. | `GET /physical-count-periods/current` auto-creates one at `status: draft`; the location list renders. |
| L-F-02 | Start a count for a not-started, required location | Location has `location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`; no `tb_physical_count` for it this period; the physical-count period is already `counting`. | `POST /physical-counts` succeeds; document created at `in_progress`; navigates to `/:id/entry`. |
| L-F-03 | Resume an in-progress location | Location already has a `tb_physical_count` at `in_progress`. | Navigates directly to `/:id/entry`; no new document created. |
| L-F-04 | Filter by KPI tile | Click "In Progress" tile. | Only in-progress location cards remain visible. |
| L-F-05 | Search by name or code | Type a partial location name/code. | List narrows to matching locations, client-side. |
| L-F-06 | Include not-counted locations | Check "Include not-counted locations". | Locations with `physical_count_type = no` are added to the list, still restricted to active inventory/consignment locations. |
| L-F-07 | Switch to a previous period | Pick a closed period from the period dropdown. | Badge shows "Previous Period"; that period's locations render read-only-in-effect (starting a *new* count against a closed period's document set is not part of this screen's normal flow). |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | Expected outcome |
| - | -------- | ------------- | ---------------- |
| L-R-01 | User without `inventory_management.physical_count` opens the list screen | Permission not granted. | Access denied per the generic permission-gate mechanism shared across the product; no module-specific override exists. |

## 4. Validation — Negative Tests

| # | Rule | Scenario | Expected error |
| - | ---- | -------- | -------------- |
| L-V-01 | `PHC_VAL_001` | Start a count while the physical-count period is still `draft` (the state it is auto-provisioned into). | `POST /physical-counts` rejects with `"Physical Count Period is not in counting status"` — see the confirmed gap noted in [03-user-flow.md](./03-user-flow.md) § 2 (no code path was found that transitions a period from `draft` to `counting`). |
| L-V-02 | `PHC_VAL_002` | Start a count for a location that has since been soft-deleted. | Rejected with a location-not-found error. |

## 5. Edge Cases

| # | Scenario | Expected outcome |
| - | -------- | ---------------- |
| L-E-01 | Click a completed location's card | No action fires — the card renders as a plain label, not a button, once `physical_count_status = completed`; there is currently no route from this screen into a completed count's detail. |
| L-E-02 | Start a count twice in quick succession for the same location (double-click) | `create()`'s idempotent-resume path (`PHC_VAL_003`) means a second call returns the same document's `id`/`doc_version` rather than creating a duplicate. |
| L-E-03 | A location with zero eligible products | `product_total = 0` at creation; the count can still reach `completed` immediately since there is nothing to count and no lines block `PHC_VAL_004`. |

## 6. References

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/pc-component.tsx`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (`create`), `.../physical-count-period/physical-count-period.service.ts` (`findCurrent`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related: [physical-count/03-user-flow-count-lead](/en/inventory/physical-count/03-user-flow-count-lead), [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_VAL_001`–`003`, `PHC_AUTH_001`), [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) (end-to-end scenarios).
