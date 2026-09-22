---
title: Inventory — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for inventory.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios

> **At a Glance**
> **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Cross-persona scenarios:** 14 &nbsp;·&nbsp; **Personas covered:** Store Keeper (ledger), Inventory Controller (period end); Finance and Audit / Config are correction pages
> **Run order:** post source documents → verify ledger → run period-end scenarios
> **Correction (2026-07-15):** the previous ~17-scenario table asserted threshold approval chains, GL entries, backdated-post rejection, negative-balance UI errors on manual documents, consignment memo receipts, Sysadmin drain-blockers, and period lock/re-open — all confirmed unbacked by source and removed. The table below contains only source-verifiable behaviour.
> **Executable coverage (2026-09-22):** period end — `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` (list-page and permission-denial describes runnable; detail / close-workflow / close-action describes still tagged "Feature pending"), manual gap catalog `docs/test-cases/gaps/900-period-end-gap.md` (43 cases, incl. the irreversible **Start Period Close** / **Close Period** buttons), generated stories `docs/user-stories/900-period-end.md` (35). Transaction log — no spec; manual catalog `docs/test-cases/740-stock-transaction.md` (38 cases). Upstream effects — `tests/501-grn.spec.ts`, `tests/601-cn.spec.ts`, `tests/701-sr.spec.ts`, `tests/720-stock-issue.spec.ts` (SR issue views; gap report `docs/test-cases/gaps/720-stock-issue-gap.md`, 44 cases).

## 1. Overview

This page is the overview entry point for the test-scenarios set of the `inventory` module. The module's own UI surface is small (read-only Transaction Log + Period End), so most inventory *effects* are asserted from upstream module suites: GRN posting effects in `501-grn.spec.ts`, SR issue effects in `701-sr.spec.ts` / `720-stock-issue.spec.ts` (note: `720-stock-issue.spec.ts` navigates the **store-requisition** issue views, not a manual stock-out screen), credit-note effects in `601-cn.spec.ts`, and the period-end surface in `900-period-end.spec.ts` (list-page tests runnable; detail/close-workflow describe blocks are marked "Feature pending"). Backend behaviour (FIFO consumption, average recompute, direct-location auto-issue, close carry-over) is additionally covered by unit specs in `carmen-turborepo-backend-v2` (`inventory-transaction.service.spec.ts`, `period-end.*.spec.ts`).

## 2. Personas in Scope

- **Store Keeper**: verifies postings on the read-only Transaction Log (`inventory_management.view`); authors adjustments/counts in sibling modules.
- **Inventory Controller / period-end operator**: works the review checklist and runs the close (`inventory_management.period_end.view` / `.execute`).
- **Finance**: correction page — [04-test-scenarios-finance](/en/inventory/inventory/04-test-scenarios-finance); no Finance surface exists.
- **Audit / Config**: correction page — [04-test-scenarios-audit-config](/en/inventory/inventory/04-test-scenarios-audit-config); no audit/config surface exists.

## 3. Persona Test Files

- [Store Keeper scenarios](/en/inventory/inventory/04-test-scenarios-store-keeper)
- [Inventory Controller scenarios](/en/inventory/inventory/04-test-scenarios-inventory-controller)
- [Finance scenarios](/en/inventory/inventory/04-test-scenarios-finance) (correction page)
- [Audit / Config scenarios](/en/inventory/inventory/04-test-scenarios-audit-config) (correction page)

## 4. Cross-Persona / Integration Scenarios

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | GRN posts to the ledger | GRN operator → Store Keeper | GRN at `draft` with received quantities; `grn_date` inside an open period | Average-method BU: on **save** (`draft → saved`) one `tb_inventory_transaction` (`good_received_note`), one detail per line (with `good_received_note_detail_item_id`), inbound cost layers (`{location_code}{YYMM}{seq4}` lots); the Transaction Log row shows the GRN number and green Qty In; a later quantity edit voids and re-posts. FIFO BU: nothing on save — the same rows appear on **commit**. |
| 2 | Direct-location receipt nets to zero | GRN operator → Store Keeper | GRN line targets a `location_type = direct` location | Two legs under one transaction: inbound layer + automatic offsetting `issue` layer at the same cost; net on-hand 0; under the average method the receipt is excluded from the product average. |
| 3 | SR issue consumes FIFO lots | SR approver → Store Keeper | FIFO BU; two lots at the source location with different costs; approved SR issue larger than the oldest lot | Outbound layers consume lots oldest-first (`lot_at_date`/`lot_seq_no`); consumption spanning lots produces multiple layer rows, each at its lot's cost, `parent_lot_no` set. |
| 4 | Outbound exceeding balance is rejected | SR / adjustment operator | Available balance < requested qty at `(product, location)` | Stock-out **Commit**: `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`, 400) before any ledger write; ledger level (SR): `` `Insufficient stock. Requested: <X>, Available: <Y>` ``; no rows written. Exception: credit-note quantity consumption books `diff_amount` instead of throwing. |
| 5 | Credit-note amount against an open-period lot re-prices it | CN operator → Store Keeper | `credit_note_amount` CN against a GRN lot received in the still-open period | Cost-layer rows record the credit; the lot's value is restated (average BU: SO-at-old-average / SI-at-new-average pair); downstream consumption picks up the new cost. |
| 6 | Credit-note amount against a closed-period lot books diff only | CN operator | Same as 5 but the receiving period is `closed`/`locked` (`isLotPeriodClosed`) | The lot's value is NOT re-priced; the credit posts as a current-period `diff_amount`. |
| 7 | Document dated in a closed period is rejected | Any source operator | Stock-in dated inside a closed period; stock-out dated outside the current period | `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD` / `STOCK_OUT_DATE_NOT_CURRENT_PERIOD` (422) at create **and** at commit; nothing posts. A document dated in an open (or locked) period posts with `at_period`/`period_id` of **that** period (`findOpenPeriodForDate`), not the wall-clock period. |
| 8 | Period close blocked by documents | Inventory Controller | A numbered SR in the period is `in_progress` with `workflow_next_stage ≠ '-'`, or a GRN/CN in a mid-state, or a required location uncounted | Review payload `can_close = false`; **Close Period** disabled; forcing the API returns `Cannot close period: {total} document(s) are incomplete` (422, `data = close_blocking`). An `in_progress` PR or PO does **not** block. |
| 9 | Period close happy path (FIFO tenant) | Inventory Controller | All gates green; `calculation_method = fifo` | `close` transaction zeroes each surviving lot whose period `end_at ≤` this period's (new `{location_code}{YYMM}{seq4}` lot, `parent_lot_no` = old lot); `open` transaction re-creates them in the auto-provisioned next period; `tb_inventory_period.status = closed`; `tb_physical_count_period` rows completed; **no** `tb_inventory_period_snapshot` rows. |
| 10 | Period close happy path (average tenant) | Inventory Controller | All gates green; `calculation_method = average` | As 9, plus issue-layers restated at the final average and one `tb_inventory_period_snapshot` row per `(product, location)` bucket with opening/receipt/issue/adjustment/closing columns. |
| 11 | Concurrent close race | Inventory Controller ×2 | Two sessions click **Close Period** near-simultaneously | First close wins under the `FOR UPDATE` lock; the second gets `Counting cannot be started for this period` (`PERIOD_END_COUNTING_NOT_ALLOWED`, 409 — shared catalog entry); no double carry-over. |
| 12 | Carried-in value is locked | Inventory Controller → CN operator | Period closed (lots carried via `open_period`); CN amount raised against a pre-close lot | Carry-in layers (`open_period`, `eop_in`) are excluded from re-pricing (`CARRIED_IN_TRANSACTION_TYPES`); the credit books as current-period `diff_amount` (same as 6). |
| 13 | Start counting blocked by open stock-moving documents | Inventory Controller | A `draft` GRN, a `draft` stock-in / stock-out, or a numbered `draft`/`in_progress` SR is dated inside the period | `POST /period-ends/start-counting` → 422 `Cannot start counting: {total} document(s) in this period are still open`, `data = { counts, total, documents }`; the UI shows the "Finish these documents first" dialog with one link per document; `tb_physical_count_period` stays `draft`; an `in_progress` PR/PO does not block. |
| 14 | Start counting happy path and idempotency | Inventory Controller | No open stock-moving documents; period `open` | First call creates (or moves) the period's `tb_physical_count_period` to `counting` (`created: true` / `already_counting: false`) and navigates to `/review`; a second call returns `already_counting: true` without error; the physical-count **Start** button is now enabled for required locations. |

## 5. E2E Test Mapping

| Spec / describe block | Scenarios covered (Section 4) |
| --------------------- | ------------------------------ |
| `900-period-end.spec.ts` — "Period End — List page" (runnable) | Period card display, empty/closed states, permission denial for the list page (supports 8–11 surfaces) |
| `900-period-end.spec.ts` — Detail / Close-workflow / Close-action describes (**"Feature pending"** — placeholder tests) | 8, 9, 10, 11, 13, 14 — flagged as pending in the spec itself; the manual gap catalog `docs/test-cases/gaps/900-period-end-gap.md` (TC-PE-03xxxx start-counting, TC-PE-04xxxx close, TC-PE-31xxxx physical-count unlock) is the current executable-intent reference |
| `501-grn.spec.ts` | 1, 2 (ledger effect of GRN save) |
| `701-sr.spec.ts` / `720-stock-issue.spec.ts` (SR issue views) | 3, 4 (issue-side surfaces; FIFO assertions are backend-unit-level) |
| `601-cn.spec.ts` | 5, 6 (credit-note surfaces) |
| Backend unit specs (`inventory-transaction.service.spec.ts`, `period-end.close-transaction.helper.spec.ts`, `period-end.close-average.helper.spec.ts`, `period-end.validate.spec.ts`) | 2–7, 9–12 (the authoritative assertions for costing/close math) |

Gaps: no E2E exercises the Transaction Log screen itself (manual catalog `740-stock-transaction.md`, 38 cases); the close workflow E2E is explicitly "Feature pending".

## 6. References

- E2E: `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`, `501-grn.spec.ts`, `701-sr.spec.ts`, `720-stock-issue.spec.ts`, `601-cn.spec.ts`; catalogs `docs/test-cases/gaps/900-period-end-gap.md`, `docs/test-cases/740-stock-transaction.md`, `docs/test-cases/gaps/720-stock-issue-gap.md`.
- Backend specs: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.spec.ts` and `.../period-end/*.spec.ts`.
- Sibling: [03-user-flow](/en/inventory/inventory/03-user-flow) (lifecycle), [02-business-rules](/en/inventory/inventory/02-business-rules) (rule IDs referenced above).
