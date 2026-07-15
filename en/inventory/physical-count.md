---
title: Physical Count
description: Periodic count of every item at a location to reconcile system balances against reality.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Physical Count

> **At a Glance**
> **Module purpose:** Full count of every item at a location for the current counting period, entered and submitted by a single generic role, with variance reconciled directly into stock-in/stock-out documents at final submit &nbsp;·&nbsp; **Audience:** any user holding the `inventory_management.physical_count` permission — no distinct approver, auditor, or configuration role exists in code &nbsp;·&nbsp; **Key entities/tables:** `tb_physical_count_period`, `tb_physical_count`, `tb_physical_count_detail`, three comment tables, four `enum_physical_count_*` enums &nbsp;·&nbsp; **Sub-pages:** 10

![Physical Count screen](/screenshots/physical-count/index.png)

![Physical Count detail screen](/screenshots/physical-count/detail.png)

## 1. Overview

A **Physical Count** is a full count of every item at a location for the current counting period, used to reconcile the system's book balance against what is actually on the shelf. The real implementation (`../carmen-inventory-frontend-react/routes/inventory-management/physical-count/`) is a single continuous flow with no distinct persona hand-off: a user opens the location list for the current period (`physical-count`), starts or resumes a count for one location (`physical-count/:id/entry`), enters `actual_qty` per product line, submits the sheet for review (`physical-count/:id/review`), and confirms the final submit — which is also the step that reconciles every non-zero-variance line into a pair of stock-in/stock-out documents. Every action in this flow is gated by one CRUD permission key, `inventory_management.physical_count` (`constant/permissions.ts`); no separate approver, auditor, or configuration role, route, or permission was found anywhere in the frontend, backend, or Bruno collection for this module.

Two routes are still wired into the router but are **not reachable from any real navigation path**: `physical-count/new` and `physical-count/:id` both render `PcForm` (`pc-form.tsx`), a pre-refactor create/edit form whose only field is `department_id` — the type it edits is explicitly commented `// Legacy type (used by old form)` in `types/physical-count.ts`. No button anywhere in the list screen links to `/new`, and the real create action (`pc-component.tsx`'s `handleAction`) creates a count directly via `POST /physical-counts` and navigates straight to `/:id/entry`, never to `/:id`. Treat these two routes and the `use-pc-table.tsx` hook that backs them as orphaned pre-refactor code.

## 2. Business Context

Physical count is a regulatory and audit baseline, not a discretionary task. External auditors require a documented count at period-end to certify the inventory line on the balance sheet, and most hospitality groups have internal policy mandating cycle counts on high-risk categories at higher frequency. A complete, signed-off count is the evidence that the inventory value carried on the books is real — without it, the closing valuation is unsupported and the audit opinion is at risk.

The financial accuracy stakes are immediate. Hospitality operations run on thin food and beverage margins, and uncounted shrinkage compounds quickly: theft, spoilage, miss-pours, transfer errors, and miscategorised consumption all erode book accuracy between counts. Period-end physical count is where that drift is detected and quantified — making the count one of the largest correcting mechanisms against inventory value in many operations. A late or incomplete count means a misstated stock position and downstream errors in menu engineering and procurement forecasting.

## 3. Key Concepts

- **Count Sheet**: The working document for one location's physical count — one `tb_physical_count` row plus its `tb_physical_count_detail` lines. The product list is the union of (a) products formally assigned to the location via `tb_product_location` and (b) any product with a non-zero net quantity in `tb_inventory_transaction_detail` at that location, so items with "phantom" stock are always caught even if not formally assigned. A count sheet is created **already `in_progress`** — `start_counting_at`/`start_counting_by_id` are stamped immediately on creation (`physical-count.service.ts` `create()`), not on the counter's first line entry. A **Refresh** action on the entry screen (`PATCH .../physical-counts/:id/refresh`) re-runs the same union query and appends any newly-qualifying products to an in-progress sheet.
- **Location Count Requirement** (not "frozen vs live"): `tb_location.physical_count_type` (`enum_physical_count_type`, `yes`/`no`, default `no`) is a per-location admin flag edited on the location's own config form (`master-data/location`, filter chips "Count"/"Not Count"). It marks whether a location is **required** for the period-end physical-count gate (`period-end.validate.ts`'s `validatePhysicalCount` requires `location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`). It is **not** a per-document frozen-vs-live counting mode: the *document*-level field of the same name (`tb_physical_count.physical_count_type`) is never set by `create()`, so every created count document simply keeps the Prisma default (`yes`). No code anywhere — frontend or backend, including the good-received-note and store-requisition services — checks for an in-progress count before allowing a posting at that location; there is no location lock.
- **Variance**: `diff_qty = actual_qty − on_hand_qty` per line, computed by the backend (not the client). Critically, `on_hand_qty` is **not** a snapshot captured when the sheet is created — it stays `0` on every line until the counter clicks **Submit for Review**, at which point `reviewItems()` recomputes `on_hand_qty` for every line as the **current, live** sum of `tb_inventory_transaction_detail.qty` at that location (no date cut-off). A quantity typed and saved mid-count therefore shows a variance against a stale `0` book quantity until that review step runs; only the review-time recomputation is meaningful. No tolerance threshold, percentage-based flagging, or recount mechanism of any kind exists in the frontend or backend for this module.
- **Save vs Submit for Review vs Submit**: three distinct backend calls drive one document to completion. **Save** (`PATCH .../save`, any time, repeatable) stamps `counted_at`/`counted_by_id` on the lines submitted and recomputes each line's `diff_qty` against whatever `on_hand_qty` is currently stored (usually still `0` before the first review). **Submit for Review** (`PATCH .../review`, once all lines have a value) recomputes the live `on_hand_qty`/`diff_qty` for every line and moves the user to the `/review` screen, but does **not** change `tb_physical_count.status` — it stays `in_progress`. **Submit** (`PATCH .../submit`, from the review screen) is the terminal action described below. `submit()` rejects with `"<N> products have not been counted yet"` if any line's `counted_at` is still null — since only Save stamps `counted_at`, a line whose only value came from typing-then-Submit-for-Review (without an intervening Save) can reach the review screen with a real `actual_qty` but a null `counted_at`, and would then block the final Submit; this edge case is unconfirmed in practice but is a direct reading of the two service methods.
- **Rollup at Submit**: on `submit()`, the backend groups every non-zero-variance line by sign and, in one transaction, creates **at most one** `tb_stock_in` (all positive-variance lines) and **at most one** `tb_stock_out` (all negative-variance lines) — both inserted **already `doc_status = completed`**, mirroring the same "create() posts completed unconditionally" pattern already confirmed for the [inventory-adjustment](/en/inventory/inventory-adjustment) module's own Stock In/Out screens. Unlike those screens, this rollup does **not** call `InventoryTransactionService.executeAdjustmentIn`/`executeAdjustmentOut` — no import or call to either helper exists in `physical-count.service.ts`. No `tb_inventory_transaction` row is written by this action, `adjustment_type_id` is left `null` on both created headers (no reason code), and no `info`/structured field links the new stock-in/out back to the source `tb_physical_count` — the only trace is a shared, human-readable `description`/line `note` string ("Physical Count Adjustment - Period: …"). Per-line `cost_per_unit` is priced by one tenant-wide costing method read once per submit (`enum_business_unit_config_key.physical_count_costing_method`, default `last_receiving`; no UI screen was found that sets this key).

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Counter (any user holding `inventory_management.physical_count`) | The single, undifferentiated role for this module: opens the location list, starts or resumes a count, enters `actual_qty` line by line, flags damaged/unfamiliar items via comments, submits for review, and confirms the final submit. |

No distinct Count Lead, Approver/Finance Reviewer, Auditor, or Sysadmin role, permission key, route, or workflow stage was found for this module in the frontend, backend, or Bruno collection — the persona split documented in earlier drafts of this wiki module does not exist in the current implementation. The sub-pages in § 7 below retain a Count Lead / Counter / Audit-Config split as a page-organisation device only (mirroring the single real screen's actions from two angles); `03-user-flow-audit-config.md` and `04-test-scenarios-audit-config.md` are correction pages for the confirmed-absent third group.

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — the physical count's variance rollup targets the same `tb_stock_in`/`tb_stock_out` tables the inventory ledger reads, but (per § 3 above) this rollup does not itself write a `tb_inventory_transaction` row
- [inventory-adjustment](/en/inventory/inventory-adjustment) — the rollup creates raw `tb_stock_in`/`tb_stock_out` rows, but bypasses that module's own service layer (no reason code, no linkage field)
- [spot-check](/en/inventory/spot-check) — a narrower, separate module for partial counts; not a child of `tb_physical_count_period`

**Master configuration:**
- [master-data/unit](/en/inventory/master-data/unit) — unit of measure for each count line (`inventory_unit_id`)
- [master-data/location](/en/inventory/master-data/location) — the location being counted, and the source of the `physical_count_type` (count-required) flag described in § 3
- [system-config/period](/en/inventory/system-config/period) — the fiscal period a count runs under (`tb_period` → `tb_physical_count_period`); period-end close blocks on incomplete counts at required locations (`period-end.validate.ts`)

## 6. Reference Sources

- Concepts: no `carmen/docs` source folder exists for this module; two aspirational planning documents exist in the E2E repo but do not match the current implementation — see the discrepancy notes on [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) § 5.1
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/` and `physical-count-period/`
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/physical-count*/`
- E2E tests: `../carmen-inventory-frontend-e2e/` — no Playwright spec exists for this module (`ls tests/ | grep -i 'physical\|count'`); planning-stage docs exist at `docs/persona-doc/System Process/tx-08-physical-stocktake.md`, `docs/test-cases/750-physical-count.md`, and `docs/user-stories/750-physical-count.md`

## 7. Pages in This Module

- [physical-count/01-data-model](/en/inventory/physical-count/01-data-model) — entities, fields, relationships, enums (`tb_physical_count_period`, `tb_physical_count`, `tb_physical_count_detail` plus three comment tables; four enums).
- [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) — validation, calculation, authorization, posting, cross-module rules (`PHC_VAL_*` / `PHC_CALC_*` / `PHC_AUTH_*` / `PHC_POST_*` / `PHC_XMOD_*`).
- [physical-count/03-user-flow](/en/inventory/physical-count/03-user-flow) — document lifecycle overview + persona index.
  - [physical-count/03-user-flow-count-lead](/en/inventory/physical-count/03-user-flow-count-lead) — the list screen: current-period locations, KPI tiles, start/resume actions.
  - [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter) — the entry + review screens: line entry, notes, import/export, final submit.
  - [physical-count/03-user-flow-audit-config](/en/inventory/physical-count/03-user-flow-audit-config) — correction page: no Approver/Auditor/Sysadmin surface exists.
- [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) — test scenarios overview + end-to-end scenarios + E2E mapping target.
  - [physical-count/04-test-scenarios-count-lead](/en/inventory/physical-count/04-test-scenarios-count-lead) — list-screen scenarios.
  - [physical-count/04-test-scenarios-counter](/en/inventory/physical-count/04-test-scenarios-counter) — entry/review-screen scenarios.
  - [physical-count/04-test-scenarios-audit-config](/en/inventory/physical-count/04-test-scenarios-audit-config) — correction page (mirrors the user-flow correction page).

> **Status:** re-synced against the live frontend (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`), backend (`physical-count.service.ts`, `physical-count-period.service.ts`, `period-end.validate.ts`), Prisma schema, and Bruno collection. No E2E Playwright spec exists yet for this module; the two planning-stage documents in the E2E repo (`tx-08-physical-stocktake.md`, `750-physical-count.md`) describe a materially different, not-yet-built design (own transaction type, GL-posted `FINALIZED` status, location transaction lock, tolerance/recount) — see [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) § 5.1 for the point-by-point comparison.
