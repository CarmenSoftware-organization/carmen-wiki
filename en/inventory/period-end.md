---
title: Period End
description: End-of-period close orchestrator — gates costing snapshot, GL handoff, and backdating lock once Physical Count and Spot Check requirements are met.
published: true
date: 2026-05-17T07:00:16.000Z
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Period End

> **At a Glance**
> **Owner:** Finance (trigger) &nbsp;·&nbsp; Inventory Manager (prerequisite checklist) &nbsp;·&nbsp; **Process:** orchestrator over `tb_period` / `tb_period_snapshot` &nbsp;·&nbsp; **Trigger:** monthly close on the open period &nbsp;·&nbsp; **Writes to:** costing snapshot + GL handoff + backdating lock &nbsp;·&nbsp; **1-liner:** freezes the period and produces the per-lot snapshot.

![Period End screen](/screenshots/inventory/period-end.png)

## 1. What & Who

Period End is the **run-the-close ceremony** — one button that says "this accounting period is finished" and produces three durable outputs: a frozen costing snapshot per `(location, product, lot)`, a GL handoff package, and a flipped period status that rejects further backdated posting. The ceremony itself does not transact stock; it freezes it.

- **Finance** — only role that may flip `tb_period.status`
- **Inventory Manager** — clears the prerequisite checklist
- **Cost Engine** — silent third actor that computes the per-lot snapshot

## 2. Common Tasks

> **Prerequisite checklist — must be 100% green before Finance can flip the period:**
> - [ ] Every **GRN** for the period is `completed` (no `draft` / `in_progress`)
> - [ ] Every **SR** is `completed` or `cancelled`
> - [ ] Every **inventory-adjustment / wastage / stock-in / stock-out** is `posted` or `voided`
> - [ ] Every **Spot Check** for the period is `completed`
> - [ ] Every **Physical Count** is `finalised` with variances posted as adjustments
> - [ ] Every **Credit Note** is `posted` (drives `COST_CALC_005` FX revaluation)

| Task | Where | Notes |
|---|---|---|
| Run prerequisite checklist (read-only) | Inventory Management → Period End → Prerequisites | Returns offending document IDs; Inventory Manager clears them |
| Trigger close on the open period | Period End → **Close** (Finance only) | Cost Engine computes snapshot, status flips `open → closed` |
| Verify snapshot wrote | Period End → Snapshot tab | One `tb_period_snapshot` row per `(location, product, lot)` with non-zero activity |
| Confirm ledger event posted | Open [[inventory/transaction]] → filter `inventory_doc_type = 'close'` | Close itself appears on the ledger |
| Lock after audit sign-off | Period End → **Lock** (Finance) | Flips `closed → locked` — terminal |
| Reopen a period (rare) | Period End → **Reopen** (Finance, audited) | Logged on `tb_period_comment`; only while `closed`, never `locked` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Close blocked: documents in non-terminal state" | Any GRN / SR / adjustment / count still `draft` or `in_progress` | Open the listed IDs and complete / cancel them |
| "Spot Check pending" | One or more spot checks for the period not `completed` | Finalise in [[spot-check]] |
| "Physical Count pending" | Count not `finalised`, or variances not posted as adjustments | Finalise in [[physical-count]] |
| "Period is closed / locked" on submit of any doc | `document_date` falls inside a `closed` / `locked` period | Use a current-period date, or raise a manual JV |
| "Snapshot row already exists" | Re-running close while `status = open` | Safe — snapshot is keyed `(period_id, snapshot_at)` and replaces |
| Cannot lock | Period not yet `closed` | Close first, then lock after audit |

## 4. Edge Cases

- **Idempotency.** Close is re-runnable while `status = open`; the snapshot replaces, never duplicates (unique on `(period_id, snapshot_at, deleted_at)`).
- **Backdating lock.** With `status IN ('closed', 'locked')`, ANY document carrying a date inside `[start_at, end_at]` is rejected at submit time — no escape hatch except a JV.
- **`locked` is terminal.** Re-open from `locked` is not a normal path; requires explicit Finance unlock authority.
- **Cost-layer attribution.** Every `tb_inventory_transaction_cost_layer` row carries `period_id` and `at_period` (YYMM) stamped at posting; the snapshot trusts this stamp and does NOT re-derive from document date.
- **Period uniqueness.** Exactly one non-deleted period per YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`).

---

## 5. Process (Dev)

Period End is **not a single Prisma table** — it is a process over several:

| Table | Role |
|---|---|
| `tb_period` | Status row that flips `open → closed → locked`. Carries `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at`. |
| `tb_period_snapshot` | One row per `(period_id, location, product, lot)` with opening / receipt / issue / adjustment / closing qty and total cost. The audit anchor. |
| `tb_period_comment` | Free-text log of close-out notes, attachments, variance explanations, reviewer sign-off. |
| `tb_inventory_transaction_cost_layer` | Each layer carries `period_id` and `at_period`; snapshot is derived from a `GROUP BY` over these. |
| `tb_inventory_transaction` | A `close` (and later `open`) event is written via `enum_inventory_doc_type` so the close itself appears on the ledger. |

`tb_period.status` is `enum_period_status { open, closed, locked }` — `open` allows posting, `closed` blocks new posts but allows certain reversals, `locked` is terminal.

## 6. Lifecycle

```
1. Inventory Manager clears prerequisite checklist (Section 2)
2. Finance triggers close on the open tb_period row:
   - Cost Engine computes per-lot closing balance from tb_inventory_transaction_cost_layer
   - INSERT tb_period_snapshot rows per (location, product, lot) with non-zero activity
   - INSERT tb_inventory_transaction rows with inventory_doc_type = 'close'
   - tb_period.status flips open -> closed
3. GL handoff (read-only): Finance exports snapshot + journal entries
4. Optional later: Finance flips closed -> locked after audit sign-off
```

Status flips are logged on `tb_period_comment` with `created_by_id` and timestamp.

## 7. Cross-References

- [[system-config/period]] &nbsp;·&nbsp; [[costing]] &nbsp;·&nbsp; [[physical-count]] &nbsp;·&nbsp; [[spot-check]]
- [[good-receive-note]] &nbsp;·&nbsp; [[inventory-adjustment]] &nbsp;·&nbsp; [[store-requisition]]
- [[inventory/transaction]] — the close writes a `close` ledger row
- [[reporting-audit]] — close-out reports read `tb_period_snapshot`

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period` (~1172-1203), `tb_period_snapshot` (~1239-1292), `tb_period_comment` (~1205-1237), `enum_period_status` (~1166-1170), `enum_inventory_doc_type` (~208-216), `tb_inventory_transaction_cost_layer` (~1123-1164).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/inventory-management/period-end/`.
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md`.
- **Test cases:** `Test_case/System_Process/tx-09-end-period-close.md`; `Test_case/System_Process/INDEX.md` § Process Execution Swim Lane.
