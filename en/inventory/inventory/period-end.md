---
title: Period End
description: End-of-period close — a review checklist over open documents and physical counts, and a one-click close that carries lot balances into the next period.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Period End

> **At a Glance**
> **Owner:** any user holding `inventory_management.period_end.execute` (view: `.view`) &nbsp;·&nbsp; **Process:** review + close over `tb_period` &nbsp;·&nbsp; **Screens:** `/inventory-management/period-end` (current period card + closed-period history) and `/inventory-management/period-end/review` (blocking-document checklist + **Close period**) &nbsp;·&nbsp; **Writes:** `close`/`open` carry-over transactions, `tb_period.status = closed`, next period auto-created; `tb_period_snapshot` only on average-method tenants &nbsp;·&nbsp; **1-liner:** freezes the period by zeroing every surviving lot and re-opening it in the next period.

![Period End screen](/screenshots/inventory/period-end.png)

## 1. What & Who

Period End is the **run-the-close ceremony** — the review screen shows what still blocks the close, and the **Close period** button (destructive-styled, disabled until every gate is green) freezes the current period. The close itself is a stock transaction: every lot with a remaining balance is zeroed in the closing period (`CLOSE-…` lots) and re-created in the next period (`OPEN-…` lots) at the same cost.

- **Period-end operator** — any user with `inventory_management.period_end.execute` triggers the close; `*.view` users can inspect the screens
- **Upstream document owners** — clear the blocking PR / PO / SR / GRN / CN documents
- **Counters** — every required location must have a `completed` physical count before close

## 2. Common Tasks

> **Blocking-document gates — the Close button stays disabled until all are green** (`validatePeriodEnd`, re-checked server-side inside a row lock at close time):
> - [ ] No **PR** in the period date range still `in_progress` with `workflow_next_stage ≠ '-'`
> - [ ] No **PO** in the period still `in_progress` with `workflow_next_stage ≠ '-'`
> - [ ] No **SR** in the period still `in_progress` with `workflow_next_stage ≠ '-'`
> - [ ] No **GRN** in a middle state — `doc_status` must be `draft`, `committed`, or `voided` (**a `draft` GRN does *not* block**; only in-between states do)
> - [ ] No **CN** in a middle state — must be `draft`, `completed`, `cancelled`, or `voided`
> - [ ] Every required location (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) has a **completed physical count** for this period
>
> Spot checks are **not** a close gate — `validatePeriodEnd` has no spot-check validator.

| Task | Where | Notes |
|---|---|---|
| See the current period | Period End (`/inventory-management/period-end`) | Card shows period code (YYMM), fiscal year/month, start/end dates, status badge, note; "current" = the earliest period with `status ∈ {open, locked}` |
| Browse closed periods | Same page, history list below the card | `GET /period-ends` returns **closed** periods only, newest first |
| Start the close | **Start close** button on the card → `/inventory-management/period-end/review` | Review page loads `GET /period-ends/review` |
| Review blocking documents | Review page — one card per module (PR / PO / GRN / CN / SR) with count + complete/incomplete badge | Clicking a card opens the document-list dialog for that module |
| Track count progress | Review page — physical-count section, one row per required location with counted/total progress | Clicking an in-progress row deep-links to `/inventory-management/physical-count/{id}/entry` |
| Close the period | **Close period** (destructive button, confirm dialog) | Fires `POST /period-ends`; on success returns to the list page |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| **Close period** button disabled ("not ready to close") | A module card is `incomplete` or a required location's count is not `completed`. Note the frontend also treats a module with **zero** documents in the period as incomplete (`is_complete = count > 0 && …`), while the backend gate counts zero blockers — a quirk to be aware of when testing empty periods | Resolve the listed documents / counts, refresh |
| `Cannot close period: incomplete documents {…}` | Backend re-validation failed — a blocking document appeared between the review load and the click | Refresh the review; resolve; re-close |
| `Period already closed` | Concurrency race — another session closed the period while this one was mid-close (`SELECT … FOR UPDATE` re-check) | Refresh; nothing to do |
| "No current period" empty state | No `tb_period` row with `status ∈ {open, locked}` exists | Create/verify periods via [system-config/period](/en/inventory/system-config/period) |
| A backdated document "went into the wrong month" | Working as designed — movements are stamped into the current **open** period regardless of document date (`resolveCurrentPeriod`); closed periods never receive rows and backdating is never rejected | None |

## 4. Edge Cases

- **Close is all-or-nothing and race-guarded.** `closeCurrent` runs in one transaction with `SELECT … FOR UPDATE` on the period row and re-runs the blocking-document validation under that lock, so a document created between validate and commit cannot slip in.
- **Next period is auto-provisioned.** `ensureNextPeriod` finds-or-creates the following `tb_period` (`fiscal_month + 1`, year rollover, `status = open`) — there is no separate "open next period" step.
- **Snapshot depends on the costing method.** `tb_period_snapshot` rows are written **only** when the business unit's `calculation_method = average` (`processAverageClose`); a FIFO tenant's close writes lot carry-over transactions only, and the snapshot table stays empty.
- **Carried-forward value is locked.** `open_period` / `eop_in` layers carry the closed period's value into the new period; they are excluded from current-period re-pricing (a Credit Note Amount against a closed-period lot books a `diff_amount` instead of re-pricing).
- **`locked` is not managed here.** No lock/reopen endpoint exists in this module; `enum_period_status.locked` is set by the separate period service behind [system-config/period](/en/inventory/system-config/period). `findCurrent` treats a `locked` period as current (`status ∈ {open, locked}`), so it can still be displayed — and closed — from this screen.
- **Physical-count periods are swept on close.** `closeCurrent` marks the period's non-completed `tb_physical_count_period` rows `completed`.
- **Period uniqueness.** Exactly one non-deleted period per YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`).

---

## 5. Process (Dev)

Period End is **not a single Prisma table** — it is a process over several:

| Table | Role |
|---|---|
| `tb_period` | Status row (`enum_period_status { open, closed, locked }`). Carries `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at`. This module flips `open → closed` only. |
| `tb_inventory_transaction` (+ `_detail`, `_cost_layer`) | The close writes one `close` transaction (zeroing lots, `CLOSE-{YYMM}-{seq}`, `transaction_type = close_period`) and one `open` transaction (re-creating them in the next period, `OPEN-{YYMM}-{seq}`, `open_period`). |
| `tb_period_snapshot` | One row per `(product, location)` bucket with opening / receipt / issue / adjustment / closing qty+cost — **written only on the average-method close path**. |
| `tb_physical_count` / `tb_physical_count_period` | The count-per-required-location gate; period rows are marked `completed` on close. |

**API surface** (gateway → `period-ends` message patterns): `GET /period-ends` (closed-period history, paginated), `GET /period-ends/current`, `GET /period-ends/review` (blocking-document + count detail), `POST /period-ends` (close — no request body).

## 6. Lifecycle

```
1. Operator opens /inventory-management/period-end (current period card)
2. Start close -> /period-end/review (GET /period-ends/review):
   - per-module blocking-document cards (pr / po / grn / cn / sr)
   - per-location physical-count progress
3. Close period (POST /period-ends) -> inside ONE transaction:
   - SELECT ... FOR UPDATE on tb_period; re-validate blocking documents
   - fifo BU:  findAllRemainingLots -> writeCloseTransaction (close)
               -> writeOpenTransaction (open, next period)
     average BU: processAverageClose (restate issues at final average,
               close/open transactions, tb_period_snapshot rows)
   - tb_period.status = closed; tb_physical_count_period rows -> completed
   - next tb_period ensured (status = open)
4. New movements now stamp into the new open period automatically
```

## 7. Cross-References

- [system-config/period](/en/inventory/system-config/period) &nbsp;·&nbsp; [costing](/en/inventory/costing) &nbsp;·&nbsp; [physical-count](/en/inventory/physical-count) (close gate) &nbsp;·&nbsp; [spot-check](/en/inventory/spot-check) (not a close gate)
- [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/en/inventory/inventory-adjustment) &nbsp;·&nbsp; [store-requisition](/en/inventory/store-requisition) — blocking-document sources
- [inventory/transaction](/en/inventory/inventory/transaction) — the close writes `close` / `open` ledger rows
- [reporting-audit](/en/inventory/reporting-audit) — close-out reports read the cost layers / snapshot

## 8. References

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/` — `period-end.service.ts` (`findAll`, `findCurrent`, `closeCurrent`, `findReview`), `period-end.validate.ts` (blocking-document gates incl. the exact complete-status sets), `period-end.close-transaction.helper.ts` (FIFO lot carry-over), `period-end.close-average.helper.ts` (average close + `tb_period_snapshot` writes).
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-history.tsx`, `pe-documents-dialog.tsx`) and `hooks/use-period-end.ts` (endpoints).
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period`, `tb_period_snapshot`, `enum_period_status`, `enum_inventory_doc_type`, `tb_inventory_transaction_cost_layer`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` — list-page tests runnable; detail/close-workflow describes marked "Feature pending".
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` (concept; the implemented close differs — see § 3–5).
