---
title: Period End
description: End-of-period close — start the counting round, review open documents and physical counts, then a one-click close that carries lot balances into the next period.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Period End

> **At a Glance**
> **Owner:** any user holding `inventory_management.period_end.execute` (view: `.view`) &nbsp;·&nbsp; **Process:** start counting → review → close over `tb_inventory_period` (renamed from `tb_period` by migration `20260916141000_rename_tb_period_to_tb_inventory_period`) &nbsp;·&nbsp; **Screens:** `/inventory-management/period-end` (current period card + closed-period history, **Start Period Close** / **Continue Counting** button) and `/inventory-management/period-end/review` (seven document cards + physical-count progress + **Close Period**) &nbsp;·&nbsp; **Writes:** `tb_physical_count_period.status = counting` (start), `close`/`open` carry-over transactions, `tb_inventory_period.status = closed`, next period auto-created; `tb_inventory_period_snapshot` only on average-method tenants &nbsp;·&nbsp; **1-liner:** opens the counting round, then freezes the period by zeroing every surviving lot and re-opening it in the next period.

![Period End screen](/screenshots/inventory/period-end.png)

## 1. What & Who

Period End is the **run-the-close ceremony** in two irreversible steps. **Start Period Close** (added 2026-08-27, `POST /period-ends/start-counting`) opens the counting round — it moves the period's `tb_physical_count_period` from `draft` to `counting`, which is the only thing that unlocks the **Start** button in [physical-count](/en/inventory/physical-count). **Close Period** (`POST /period-ends`) then freezes the period once every gate is green. The close itself is a stock transaction: every lot with a remaining balance is zeroed in the closing period and re-created in the next period at the same cost.

- **Period-end operator** — any user with `inventory_management.period_end.execute` presses both buttons; `*.view` users can inspect the screens
- **Upstream document owners** — settle the GRN / SI / SO / SR / CN documents that block the start or the close
- **Counters** — every required location must have a `completed` physical count before close

## 2. Common Tasks

> **Two gates, checked server-side under a `SELECT … FOR UPDATE` row lock on `tb_inventory_period` (`period-end.service.ts` `startCounting` / `closeCurrent`, both re-run their validator inside the transaction):**
>
> **Start-counting gate** (`listStartCountingBlockers`, `period-end.validate.ts`) — every stock-moving document dated inside the period must be settled, otherwise the count would record an on-hand figure that is already stale:
> - [ ] No **GRN** with `doc_status ∉ {committed, voided}` — a `draft` GRN **does** block the start
> - [ ] No **Stock In** / **Stock Out** with `doc_status ∉ {completed, cancelled, voided}` — a `draft` SI/SO blocks
> - [ ] No numbered **SR** (`sr_no` not `draft-…`) still `draft` or `in_progress`
> - PR and PO never block the start — neither writes to the ledger
>
> **Close gate** (`validatePeriodEnd`) — six counters, all must be zero:
> - [ ] No numbered **SR** in the period still `in_progress` with `workflow_next_stage ≠ '-'`
> - [ ] No **GRN** in a middle state — `doc_status` must be `draft`, `committed`, or `voided` (a `draft` GRN does *not* block the close)
> - [ ] No **CN** in a middle state — must be `draft`, `completed`, `cancelled`, or `voided`
> - [ ] No **Stock In** / **Stock Out** at `in_progress` (SI/SO never reach `in_progress` through their own service — `create` writes `draft`, `commit` writes `completed` — so this counter is zero in practice)
> - [ ] Every required location (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) has a **completed physical count** for this period
>
> **PR and PO are no longer close gates** (they were in the 2026-07 code; `validatePurchaseRequest` / `validatePurchaseOrder` still exist in `period-end.validate.ts` but `validatePeriodEnd` no longer calls them). They still appear as review cards for information. Spot checks are not a gate for either step. Documents are matched by their **document date** (`grn_date`, `si_date`, `so_date`, `sr_date`, `cn_date`) inside `[start_at, end_at]`, and only **numbered** PR/SR count — a `draft-…` placeholder number is ignored (`NUMBERED_DOC`, 2026-09-18).

| Task | Where | Notes |
|---|---|---|
| See the current period | Period End (`/inventory-management/period-end`) | Card shows period code (YYMM), fiscal year/month, start/end dates, status icon + label, note; "current" = the earliest period with `status ∈ {open, locked}` |
| Browse closed periods | Same page, history list below the card | `GET /period-ends` returns **closed** periods only, default sort `fiscal_year desc, fiscal_month desc`, optional `?fiscal_year=YYYY` |
| Start the counting round | **Start Period Close** on the card → confirm dialog ("This cannot be undone — the round stays open until the period is closed") | Fires `POST /period-ends/start-counting`; on success navigates to `/review`. Once the round is `counting` the same button reads **Continue Counting** and just navigates (no second POST) |
| Review blocking documents | Review page — one card per module (PR / PO / GRN / CN / SR / SI / SO) with count + Complete/Incomplete badge | Clicking a card opens the document-list dialog; each row links to the source document (`pe-document-paths.ts` — SI/SO rows open `/inventory-management/inventory-adjustment/{id}?type=stock-in|stock-out`) |
| Track count progress | Review page — one location card per required location with counted/total progress | Clicking a card opens (or **creates**) that location's count — `openPhysicalCount(item, physical_count_period.id)`; cards are disabled with tooltip "Counting has not started for this period yet." until the round is `counting` |
| Close the period | **Close Period** (destructive button, confirm dialog "All transactions and physical counts in this period will be locked.") | Enabled only when the review payload's `can_close` is true; fires `POST /period-ends` (no body); on success returns to the list page |

## 3. Validation & Errors

All period-end errors come from `packages/error-catalog/src/catalog.ts`:

| Symptom / Message | Code · HTTP | Cause | Action |
|---|---|---|---|
| **Close Period** button disabled, tooltip "All transactions must be complete and all physical counts must be completed before closing." | — | The review payload's `can_close` is false (`close_blocking` has a non-zero counter). Since 2026-08-27 the frontend no longer recomputes the rule from the cards — the earlier "empty module reads incomplete" quirk is gone | Resolve the listed documents / counts, press **Refresh** |
| `Cannot close period: {total} document(s) are incomplete` | `PERIOD_END_CLOSE_BLOCKED` · 422 | Backend validation failed (either on the first check or on the re-check inside the row lock); the response `data` carries the per-type `close_blocking` counts | Refresh the review; resolve; re-close |
| `Cannot start counting: {total} document(s) in this period are still open` | `PERIOD_END_START_COUNTING_BLOCKED` · 422 | Stock-moving documents still open; `data` carries `{ counts, total, documents }` per type (`grn`, `stock_in`, `stock_out`, `sr`). The frontend renders this as the **"Finish these documents first"** dialog listing every blocker with a link, instead of a toast | Commit / void / complete the listed documents, retry |
| `Counting cannot be started for this period` | `PERIOD_END_COUNTING_NOT_ALLOWED` · 409 | Start: the period is no longer `open`, or the counting round is already `completed`. Close: another session closed the period while this one was mid-close (the closed-race path reuses this catalog entry — the old literal `Period already closed` string no longer exists) | Refresh; nothing to do |
| `No current period found` | `PERIOD_END_NO_CURRENT_PERIOD` · 404 | No `tb_inventory_period` row with `status ∈ {open, locked}` (start-counting requires `open` specifically) | Create/verify periods via [system-config/period](/en/inventory/system-config/period) (`/api/{bu}/inventory-periods`) |
| A stock-in dated last month is rejected | `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD` · 422 | Since 2026-08-31 the ledger resolves the period from the **document date** (`findOpenPeriodForDate`); SI create/commit require `si_date` inside an open/locked period, SO create/commit require `so_date` inside the **current** period (`STOCK_OUT_DATE_NOT_CURRENT_PERIOD`). See [transaction](/en/inventory/inventory/transaction) § 3 | Re-date the document into an open period |

## 4. Edge Cases

- **Start is idempotent; close is not.** Calling `start-counting` on a round that is already `counting` returns `{ already_counting: true }` instead of conflicting; a round at `completed` returns 409. The close, once committed, has no reopen endpoint in this module.
- **Both steps are all-or-nothing and race-guarded.** `startCounting` and `closeCurrent` each run in one transaction with `SELECT … FOR UPDATE` on the period row and re-run their validator under that lock, so a document created between validate and commit cannot slip in.
- **Which lots carry forward is decided by `end_at`, not by "whatever is left when you click".** `findAllRemainingLots` only considers cost layers whose `at_period` belongs to a period with `end_at ≤ closing period's end_at` (fixes 2026-08-31 `0a2379ebe` / `772e87ea1`) — receipts already posted into a later open period are not swept into the close.
- **Next period is auto-provisioned.** `ensureNextPeriod` (`period-end.close-transaction.helper.ts`) finds-or-creates the following `tb_inventory_period` (`fiscal_month + 1`, year rollover, `status = open`, first-to-last-day UTC) — there is no separate "open next period" step.
- **Snapshot depends on the costing method.** `tb_inventory_period_snapshot` rows are written **only** when the business unit's `calculation_method = average` (`processAverageClose`); a FIFO tenant's close writes lot carry-over transactions only. `resolveCalculationMethod` reads `tb_business_unit.calculation_method` (platform schema, column default `average`) and falls back to `fifo` if the BU row is missing.
- **Carry-over lots use the same lot format as every other layer.** `buildLotNo({ locationCode, atPeriod, seqNo })` → `{location_code}{YYMM}{seq4}` (e.g. `MK26100001`); `parent_lot_no` links the new lot back to the closed one. The old `CLOSE-…` / `OPEN-…` prefixes are gone.
- **Carried-forward value is locked.** `open_period` / `eop_in` layers (`CARRIED_IN_TRANSACTION_TYPES`) carry the closed period's value into the new period; they are excluded from current-period re-pricing (a Credit Note Amount against a closed-period lot books a `diff_amount` instead).
- **`locked` is not managed here.** No lock/reopen endpoint exists in this module; `enum_period_status.locked` is set by the inventory-period service behind [system-config/period](/en/inventory/system-config/period) (`/api/{bu}/inventory-periods`, permission key `system_admin.inventory_period`). `findCurrent` / `findReview` / `closeCurrent` treat a `locked` period as current, so it can still be displayed — and closed — from this screen; `startCounting` requires `open`.
- **Physical-count periods are swept on close.** `closeCurrent` marks the period's non-completed `tb_physical_count_period` rows `completed` (`physical_count_period_closed` in the response).
- **Period uniqueness.** Exactly one non-deleted period per YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`).

---

## 5. Process (Dev)

Period End is **not a single Prisma table** — it is a process over several:

| Table | Role |
|---|---|
| `tb_inventory_period` | Status row (`enum_period_status { open, closed, locked }`). Carries `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at`. This module flips `open → closed` only. |
| `tb_physical_count_period` | One row per period (`@@unique([period_id, deleted_at])`), `enum_physical_count_period_status { draft, counting, completed }`. `startCounting` creates it at `counting` (or moves an existing `draft` row to `counting`); `closeCurrent` marks it `completed`. |
| `tb_inventory_transaction` (+ `_detail`, `_cost_layer`) | The close writes one `close` transaction (zeroing lots, `transaction_type = close_period`, `out_qty = remaining`) and one `open` transaction (re-creating them in the next period, `open_period`, `in_qty = remaining`); `inventory_doc_no` = the period id, `note = "Close period YYMM"` / `"Open period YYMM"`. |
| `tb_inventory_period_snapshot` | One row per `(product, location)` bucket with opening / receipt / issue / adjustment / closing qty+cost — **written only on the average-method close path**. |
| `tb_physical_count` | The count-per-required-location gate (`validatePhysicalCount`). |

**API surface** (`apps/backend-gateway/src/application/period-end/period-end.controller.ts`, all under `/api/{bu_code}/period-ends`, guarded by `AppIdGuard('period_end.*')`):

| Endpoint | Guard key | Returns |
|---|---|---|
| `GET /period-ends?fiscal_year=` | `period_end.findAll` | Closed periods, paginated, newest first |
| `GET /period-ends/current` | `period_end.findOne` | Earliest `open`/`locked` period |
| `GET /period-ends/review` | `period_end.findReview` | `{ id, start_date, end_date, status, physical_count_period, can_start_counting, start_blocking: { counts, total }, can_close, close_blocking: { sr, grn, cn, stock_in, stock_out, physical_count }, details: { transaction: { pr, po, grn, cn, sr, si, so }, physical_count[] } }` — each transaction item is `{ count, complete_count, incomplete_count, is_complete, documents[] }` (`is_complete` is `count > 0 && complete_count === count`; the frontend no longer derives closability from it) |
| `POST /period-ends/start-counting` | `period_end.startCounting` | `{ period, physical_count_period: { id, status }, created, already_counting }` |
| `POST /period-ends` | `period_end.close` | Closed period row + `carry_over: { calculation_method, next_period_id, close_transaction_id, open_transaction_id, carried_lot_count, average_close? }` + `physical_count_period_closed` |

Bruno: `inventory/period-end/*` (list, current, review, close) and `_uncategorized/period-end/POST-start-counting-period-end.bru`.

## 6. Lifecycle

```
1. Operator opens /inventory-management/period-end (current period card)
2. Start Period Close (POST /period-ends/start-counting) -> inside ONE transaction:
   - SELECT ... FOR UPDATE on tb_inventory_period; require status = open
   - listStartCountingBlockers (GRN not committed/voided, SI/SO not terminal,
     numbered SR draft/in_progress) -> 422 with the document list if any
   - tb_physical_count_period: create at counting, or draft -> counting
   -> navigate to /period-end/review (GET /period-ends/review)
3. Counters create/complete a tb_physical_count per required location
   (physical-count Start is unlocked only while the round is counting)
4. Close Period (POST /period-ends) -> inside ONE transaction:
   - SELECT ... FOR UPDATE; re-run validatePeriodEnd (SR / GRN / CN / SI / SO / counts)
   - ensureNextPeriod (find-or-create next tb_inventory_period, status = open)
   - fifo BU:  findAllRemainingLots (layers whose period end_at <= this end_at)
               -> writeCloseTransaction (close) -> writeOpenTransaction (open)
     average BU: processAverageClose (restate issues at final average,
               close/open rows, tb_inventory_period_snapshot rows)
   - tb_inventory_period.status = closed; tb_physical_count_period -> completed
5. New documents dated in the next period post into it; documents dated in the
   closed period are rejected at SI/SO create/commit (see § 3)
```

## 7. Cross-References

- [system-config/period](/en/inventory/system-config/period) &nbsp;·&nbsp; [costing](/en/inventory/costing) &nbsp;·&nbsp; [physical-count](/en/inventory/physical-count) (close gate; its Start button waits for step 2) &nbsp;·&nbsp; [spot-check](/en/inventory/spot-check) (not a gate)
- [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/en/inventory/inventory-adjustment) &nbsp;·&nbsp; [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) — blocking-document sources
- [inventory/transaction](/en/inventory/inventory/transaction) — the close writes `close` / `open` ledger rows
- [reporting-audit](/en/inventory/reporting-audit) — close-out reports read the cost layers / snapshot

## 8. References

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/` — `period-end.service.ts` (`findAll`, `findCurrent`, `startCounting`, `closeCurrent`, `findReview`), `period-end.validate.ts` (`listStartCountingBlockers`, `validatePeriodEnd`, the `*_COMPLETE` status sets, `NUMBERED_DOC`), `period-end.close-transaction.helper.ts` (`findAllRemainingLots`, `ensureNextPeriod`, FIFO carry-over), `period-end.close-average.helper.ts` (average close + `tb_inventory_period_snapshot`); gateway `apps/backend-gateway/src/application/period-end/period-end.controller.ts`; `apps/micro-business/src/inventory/inventory-period.helper.ts` (document-date → period resolution used by SI/SO/GRN).
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-history.tsx`, `pe-documents-dialog.tsx`, `pe-start-blocked-dialog.tsx`, `pe-document-paths.ts`, `use-period-end.ts`), `types/period-end.ts`, labels under `inventoryManagement.periodEnd` in `messages/en.json`.
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_period`, `tb_inventory_period_snapshot`, `tb_physical_count_period`, `enum_period_status`, `enum_physical_count_period_status`, `enum_inventory_doc_type`, `tb_inventory_transaction_cost_layer`; migration `20260916141000_rename_tb_period_to_tb_inventory_period`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` — list-page describes runnable; detail / close-workflow / close-action describes still marked "Feature pending". Manual catalog: `docs/test-cases/gaps/900-period-end-gap.md` (43 cases, incl. the two irreversible buttons and the physical-count "Counting has not started" dialog), generated user stories `docs/user-stories/900-period-end.md` (35).
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` (concept, frozen 2026-04-27; the implemented two-step start/close differs — see § 2–5).
