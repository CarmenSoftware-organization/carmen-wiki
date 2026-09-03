---
title: Store Requisition — User Flow — Fulfiller
description: Fulfiller's flow within the store-requisition module — records issued_qty and advances the SR's final workflow stage; lot assignment is automatic.
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, user-flow, fulfiller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — User Flow — Fulfiller

> **At a Glance**
> **Persona:** Store Keeper / Warehouse Supervisor — whoever holds the workflow stage tagged `enum_stage_role.issue` &nbsp;·&nbsp; **Module:** [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; **Workflow stages:** in_progress (issue-tagged stage) → completed (final stage advance fires the inventory-transaction write) &nbsp;·&nbsp; **Key permissions:** record `issued_qty` via the same generic `/approve` endpoint the Approver uses; no lot-selection UI (FIFO auto-assigned)
> **What this persona does:** Records `issued_qty` at the issue-tagged stage — the same generic approve action other stages use — which, on the final advance, decrements source on-hand.
> ⚠️ **Corrected this pass.** The prior version of this page described a distinct "commit" action, a manual lot-selection sub-form, an enforced Approver ≠ Fulfiller segregation of duties with a configurable low-value threshold, and GL posting. None of these were confirmed — see the callout below and the Section 1 rewrite.

## 1. Role in This Module

The **Fulfiller** persona is whoever holds the workflow stage tagged `enum_stage_role.issue` (typically titled Store Keeper / Warehouse Supervisor) at the source location, who records `issued_qty` per line (which may be less than `approved_qty` if stock has dropped since approval). **Corrected this pass:** the frontend's "Issue" button (`useIssueStoreRequisition`) calls the exact same `POST .../approve` endpoint as the Approver's "Approve" button (`useApproveStoreRequisition`) — the only difference is the `stage_role` tag sent in the request body. There is no separate "commit" endpoint. The document becomes `completed` when this call is made at the final workflow stage (`workflow_next_stage === '-'`), which fires `executeTransferOnComplete()` in `store-requisition.logic.ts`: it writes `tb_inventory_transaction` rows via `InventoryTransactionService.executeTransfer()`, decrementing source on-hand and, for `sr_type = transfer`, incrementing destination on-hand. **Lot assignment at this step is system-computed FIFO** (`getAvailableFifoLots` / `consumeFifoLots`) — no lot-selection UI exists in the SR frontend, so there is no manual "pick a lot" action for this persona. GL/journal-entry posting from this event is unconfirmed (see [02-business-rules.md](./02-business-rules.md) `SR_POST_007`). On entry the SR is at `doc_status = in_progress` with `workflow_current_stage` pointing at the issue-tagged stage; each line the Fulfiller acts on has `approved_qty > 0` (or `0` if that line was rejected upstream) and the Approver's per-line signature is preserved on `tb_store_requisition_detail.approved_by_*`. **Unconfirmed:** whether an Approver is blocked from also holding the issue stage on the same SR — no `approved_by_id` cross-check was found in `store-requisition.service.ts`, and no SoD-relaxation threshold config was found anywhere in this module. Post-commit corrections are out of scope for this persona; they go through `[inventory-adjustment](/en/inventory/inventory-adjustment)`.

### Workflow position (Fulfiller highlighted)

```mermaid
graph LR
    approved(("in_progress\n— issue-tagged stage")) -->|"re-check source availability"| pick["Enter issued_qty per line"]:::current
    pick -->|"POST .../approve (final stage)"| completed(("completed")):::current
    pick -->|"short fulfilment\n(live on-hand < approved_qty)"| partial["Partial issuance\n(issued_qty < approved_qty)"]:::current
    partial -->|"POST .../approve"| completed
    completed -.->|"sr_type=transfer: destination on-hand +qty\nsr_type=issue into direct: no destination on-hand change"| effects[["Inventory effects (executeTransferOnComplete)"]]
    classDef current fill:#1a56db,color:#fff,stroke:#1a56db;
```

### Permission Matrix — V1 Status × Action (Fulfiller)

The Fulfiller acts at `doc_status = in_progress` while `workflow_current_stage` is tagged `enum_stage_role.issue` and the Fulfiller is in `user_action.execute`. The Fulfiller cannot exceed the Approver's `approved_qty` per line. **Corrected this pass:** no segregation-of-duties check (Approver ≠ Fulfiller) or SoD-relaxation threshold was found anywhere in `store-requisition.service.ts`.

| Action | `in_progress` (issue-tagged stage) | `completed` |
|---|---|---|
| View SR and approved quantities | ✅ (`SR_AUTH_007`) | ✅ |
| Re-check live source availability | ✅ (`SR_VAL_013` pre-check) | — |
| Enter `issued_qty` per line (`≤ approved_qty`) | ✅ (`SR_AUTH_007`, `SR_VAL_008`) | ❌ |
| Select lots for lot-controlled items | ❌ — no lot-selection UI exists; lots are FIFO-assigned automatically at the final-stage advance | ❌ |
| Enter per-line comments / attachments | ✅ | ❌ |
| Final stage advance (`in_progress → completed`) | ✅ (`SR_AUTH_007`) — same `/approve` endpoint as any other stage | ❌ |
| Short fulfilment (partial issue; `issued_qty < approved_qty`) | ✅ (`SR_POST_012`) | — |
| Advance at final stage where Fulfiller = line Approver | Unconfirmed whether blocked — no SoD check found in code | — |
| Edit header / line quantities above `approved_qty` | ❌ | ❌ |
| Whole-document reject (`in_progress → voided`) | ✅ — same generic reject action any current-stage actor can invoke; not a distinct "void" right | ❌ |

> ℹ️ **Corrected — no distinct "commit" or "3-variant" mechanism found.** Both `sr_type = transfer` and `sr_type = issue` complete through the identical `/approve` call when `workflow_next_stage === '-'`; `executeTransfer()`'s only branching is whether the destination `location_type` is `direct` (expensed immediately, on-hand stays 0) or `inventory` (on-hand increments). There is no separate "Complete" action distinct from recording `issued_qty` and advancing the final stage.

## 2. Entry Point and Primary Flow

**Entry point:** One confirmed path into the issuance action.

- **The SR list, filtered to the issue stage** — list view filtered to `(doc_status = 'in_progress', workflow_current_stage = '<issue-tagged stage>', user_action.execute CONTAINS me)`; the Fulfiller opens an SR from here. **Unconfirmed:** whether the list additionally filters by `from_location_id IN my_locations` — no such location-scoping check was found in `store-requisition.service.ts`.

**Primary flow (happy path):**

1. **Open the SR at the source.** The detail view shows the destination outlet, `sr_type`, expected date, requester, the approver's signature on each line (`approved_by_name`, `approved_date_at`, `approved_message`), and the lines with `approved_qty` (in the product's UoM).
2. **Re-check source availability at the moment of issue.** The screen surfaces live source on-hand per line — this is what `SR_VAL_013` re-checks at the final stage advance. If live on-hand has fallen below `approved_qty` since approval, the Fulfiller will need to short-fulfil (decision branch below).
3. **Pick the items physically and enter `issued_qty` per line.** What was actually picked, in the product's UoM; the screen enforces `0 ≤ issued_qty ≤ approved_qty` per `SR_VAL_008`.
4. **Capture additional context.** Per-line free-text comments; attachments write to `tb_store_requisition_detail_comment`.
5. **Click Issue.** This calls the identical `POST .../approve` endpoint the Approver's "Approve" button uses (`useIssueStoreRequisition` and `useApproveStoreRequisition` are the same mutation, differing only in the `stage_role` tag). When this is the final stage (`workflow_next_stage === '-'`), the document becomes `completed` and `executeTransferOnComplete()` fires.
6. **Inventory fan-out fires.** For each line with `issued_qty > 0`, `InventoryTransactionService.executeTransfer()` inserts a `tb_inventory_transaction` row (`inventory_doc_type = store_requisition`) with `tb_inventory_transaction_detail` child(ren) carrying `lot_no` (system-assigned FIFO), `expiry_date`, and `cost_per_unit`; stamps the id on `tb_store_requisition_detail.inventory_transaction_id`; decrements source on-hand; for `sr_type = transfer` increments destination on-hand (for `sr_type = issue` into a `direct` location, the transfer-in nets to zero — no destination on-hand change). GL/journal-entry posting is unconfirmed.
7. **Document state transitions.** `doc_status = in_progress → completed`; `workflow_history` gets the final entry. The SR is now locked against further edits. **Corrected this pass:** no confirmed downstream "Receiver" handoff exists — see [03-user-flow-receiver.md](./03-user-flow-receiver.md).

## 3. Decision Branches

- **At-issue stock-out (live on-hand < `approved_qty`)** — the Fulfiller sees the live on-hand below `approved_qty` on one or more lines. Reducing `issued_qty` to what is actually available and issuing anyway is the confirmed path (`SR_VAL_013` re-checks live on-hand against the entered `issued_qty`, not the original `approved_qty`); the specific system-comment wording and a distinct "skip the line" alternative described in earlier versions of this page were not directly confirmed and should be treated as illustrative.
- **Lot assignment** — **corrected this pass.** There is no lot-selection UI or "rotation policy" choice exposed to this persona; `createFifoConsumption()` in `inventory-transaction.service.ts` assigns lots automatically via `getAvailableFifoLots()` / `consumeFifoLots()`. Multi-lot consumption for a single line is a backend detail, not a Fulfiller decision.
- **Closed-period commit attempt** — **removed this pass; unconfirmed.** No `period` reference was found anywhere in `store-requisition.service.ts` or `store-requisition.logic.ts`; treat any closed-period block claim for SR as unconfirmed (see `SR_VAL_014`).
- **SoD violation at issuance** — **removed this pass; unconfirmed.** No cross-check between `approved_by_id` and the issuing user was found in code, and no SoD-relaxation threshold config exists anywhere in this module.

## 4. Exit Point / Handoffs

The Fulfiller's involvement on a given SR ends at one of two confirmed boundaries:

- **Final stage advance succeeds (`in_progress → completed`)** — the SR is locked; source on-hand has decremented; for `sr_type = transfer` the destination has received stock. **No confirmed downstream "Receiver" persona exists** — see [03-user-flow-receiver.md](./03-user-flow-receiver.md) for what was checked. Any subsequent correction is via `[inventory-adjustment](/en/inventory/inventory-adjustment)`.
- **Whole-document reject** — `in_progress → voided` (same generic reject action any current-stage actor, including this one, can invoke); the document terminates.

Post-commit reversal of a `completed` SR is not part of the routine Fulfiller path; see [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) for what is and isn't confirmed about post-commit correction.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the corrected lifecycle and cross-persona handoff table (no confirmed "Fulfiller → Receiver" or "Receiver + Inventory Controller" handoffs).
- `../carmen/docs/store-requisitions/SR-User-Experience.md` § Processing a Store Requisition — carmen/docs source for the fulfiller (named "Maria Rodriguez, Warehouse Supervisor" in the persona narrative); treat as design intent, not verified current behavior.
- `../carmen/docs/store-requisitions/Store Requisitions.md` § UC-69 (Approve Requisition and Record Stock as Issued) — use-case source; current code implements this as the same generic `/approve` action other stages use, not a distinct "commit" use case.
- Sibling: [03-user-flow-approver.md](./03-user-flow-approver.md) — the Fulfiller's `approved_qty` cap is set there; both personas act through the identical `/approve` endpoint.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — corrected this pass to document that no distinct Receiver persona was found in current source.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — corrected this pass; GL/journal verification and SoD-relaxation-threshold config were not found in current source.
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_store_requisition_detail.issued_qty`, the `inventory_transaction_id` link, and the lot-data linkage via `tb_inventory_transaction_detail` (lot lives on the inventory transaction and is FIFO-assigned automatically — see §5 items 2, 6, 12 of the data model).
- Sibling: [02-business-rules.md](./02-business-rules.md) — `SR_VAL_008` (quantity invariant `issued_qty ≤ approved_qty`), `SR_VAL_013` (live source-availability check), `SR_AUTH_007` (issue-stage authority), `SR_POST_005`–`SR_POST_006` (final-stage advance and inventory fan-out), `SR_POST_010` (whole-document reject → `voided`).
- Related: [inventory](/en/inventory/inventory) — the downstream module the final-stage advance fans out into; lot, expiry, and cost-layer data live on `tb_inventory_transaction_detail`.
- Related: [costing](/en/inventory/costing) — source-location FIFO / moving-average feeds the issued unit cost.
- Related: [good-receive-note](/en/inventory/good-receive-note) — inter-warehouse transfers described in earlier versions of this page as a "paired GRN" pattern; not independently re-verified this pass.
