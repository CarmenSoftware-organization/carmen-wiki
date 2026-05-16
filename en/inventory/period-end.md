---
title: Period End
description: End-of-period close orchestrator — gates costing snapshot, GL handoff, and backdating lock once Physical Count and Spot Check requirements are met.
published: true
date: 2026-05-16T17:00:00.000Z
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Period End

## 1. Purpose

Period End is the run-the-close ceremony. It is the single button that says "this accounting period is finished" and produces three durable outputs: a frozen costing snapshot per `(location, product, lot)`, a GL handoff package, and a flipped period status that rejects any further backdated posting. The process orchestrates work that has already happened in other modules — every GRN, SR, adjustment, wastage, Spot Check, and Physical Count must already be posted/finalised when the button is pressed. The ceremony itself does not transact stock; it freezes it.

Two actors share the wheel: **Finance** owns the trigger (only Finance can flip the period), and the **Inventory Manager** monitors the prerequisite checklist and clears blockers. The Cost Engine is the silent third — it computes the per-lot snapshot rows the close depends on.

## 2. Process Model

Period End is **not a single Prisma table**; it is a process that reads and writes several. The tables involved:

| Table | Role |
| --- | --- |
| `tb_period` | The period row whose `status` flips `open → closed → locked`. Carries `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at`. |
| `tb_period_snapshot` | One row per `(period_id, location, product, lot)` with opening / receipt / issue / adjustment / closing quantities and total cost. The audit anchor downstream modules consume. |
| `tb_period_comment` | Free-text log of close-out notes and attachments (variance explanations, reviewer sign-off). |
| `tb_inventory_transaction_cost_layer` | Each cost-layer row carries `period_id` and `at_period` (YYMM) so transactions can be attributed to the period that owned them at posting time. The snapshot is derived from a `GROUP BY` over these layers. |
| `tb_inventory_transaction` | A `close` (and later `open` for next period) event row is written via `enum_inventory_doc_type` so the close itself appears on the [[inventory/transaction]] ledger. |

`tb_period.status` is `enum_period_status { open, closed, locked }`. `open` allows posting; `closed` blocks new posts but still allows certain reversals; `locked` is terminal — only Finance with explicit unlock authority can re-open.

## 3. Algorithm / Lifecycle

```
1. Prerequisite checklist (Inventory Manager clears):
   - Every GRN for the period is in completed status (no in_progress / draft)
   - Every SR is completed or cancelled (no in_progress)
   - Every inventory-adjustment, wastage, stock-in, stock-out is posted or voided
   - Every Spot Check for the period is completed
   - Every Physical Count for the period is finalised with variances posted as adjustments
   - Every Credit Note is posted (relevant for COST_CALC_005 FX revaluation)

2. Finance triggers close on the open tb_period row:
   - Cost Engine computes per-lot closing balance from tb_inventory_transaction_cost_layer
   - One tb_period_snapshot row INSERTed per (location, product, lot) with non-zero activity
   - tb_inventory_transaction rows are written with inventory_doc_type = 'close'
   - tb_period.status flips open -> closed

3. GL handoff (read-only): finance exports the snapshot + journal entries

4. Optional later: Finance flips closed -> locked once external audit has signed off
```

Backdating into a `closed` or `locked` period is rejected at the document layer; any document with `document_date` inside the period and an attempted `submit` / `post` action returns an error and the period status is surfaced in the failure message.

## 4. Usage / Cross-References

- [[system-config/period]] — the period rows this process closes
- [[costing]] — the snapshot is the costing engine's frozen output; downstream balance-sheet inventory valuation reads here
- [[physical-count]] — prerequisite: finalised count per location for the period
- [[spot-check]] — prerequisite: every spot check completed
- [[good-receive-note]], [[inventory-adjustment]], [[store-requisition]] — prerequisites: all posted/voided
- [[inventory/transaction]] — the close itself writes a `close` ledger row
- [[reporting-audit]] — close-out reports consume `tb_period_snapshot`

## 5. Business Rules

- **Trigger authority.** Only Finance role can flip `tb_period.status`. Inventory Manager can run the prerequisite checklist read-only.
- **Prerequisite gate.** Close is rejected if any document for the period is in a non-terminal state (`draft`, `in_progress`). The checklist returns the offending document IDs so the Inventory Manager can clear them.
- **Snapshot uniqueness.** `tb_period_snapshot` is keyed `@@unique([period_id, snapshot_at, deleted_at])` — re-running the close on the same period replaces the snapshot, never duplicates.
- **Idempotency.** The close is re-runnable while `status = open`. Once `closed`, re-running requires an explicit re-open by Finance (audited via `tb_period_comment`).
- **Backdating lock.** With `tb_period.status IN ('closed', 'locked')`, any document carrying a date inside `[start_at, end_at]` is rejected at submit / post time.
- **Cost layer attribution.** Every `tb_inventory_transaction_cost_layer` row carries `period_id` and `at_period` (YYMM) stamped at posting; the snapshot trusts this stamp and does not re-derive from document date.
- **Audit trail.** Every status flip is logged on `tb_period_comment` with `created_by_id` and timestamp; status-flip events also appear on `tb_inventory_transaction` with `inventory_doc_type IN ('close', 'open')`.
- **Period uniqueness.** `tb_period` is `@@unique([period, deleted_at])` and `@@unique([fiscal_year, fiscal_month, deleted_at])` — exactly one non-deleted period per YYMM.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period` (lines ~1172-1203), `tb_period_snapshot` (lines ~1239-1292), `tb_period_comment` (lines ~1205-1237), `enum_period_status` (lines ~1166-1170), `enum_inventory_doc_type` (lines ~208-216), `tb_inventory_transaction_cost_layer` (lines ~1123-1164).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/inventory-management/period-end/`.
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` — process overview.
- **Test cases:** `Test_case/System_Process/tx-09-end-period-close.md`; `Test_case/System_Process/INDEX.md` § Process Execution Swim Lane.
- **Cross-module:** see Section 4.
