---
title: My Approval
description: Personal approval queue surfacing every PR (and related document) the current user must act on — single pane across modules.
published: true
date: 2026-05-17T07:00:16.000Z
tags: purchase-request, approval, workflow, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# My Approval

> **At a Glance**
> **Owner:** Any workflow approver &nbsp;·&nbsp; **Table:** *none — projection over workflow state* &nbsp;·&nbsp; **Workflow:** read-only inbox &nbsp;·&nbsp; **Upstream:** [[purchase-request]], [[purchase-order]], [[purchase-order/credit-note]] &nbsp;·&nbsp; Aggregated personal inbox of documents awaiting the signed-in user's action.

![My Approval screen](/assets/screenshots/purchase-request/my-approval.png)

## 1. What & Who

**My Approval** (`/procurement/approval`) is the per-user inbox aggregating every workflow stage assigned to the signed-in user across approvable documents — primarily Purchase Requests, but also POs, Credit Notes, and any module the workflow engine gates. Where each module shows *all* its documents, My Approval shows **only the slice the current user must act on right now**. The page is **read-and-act only** — it owns no persisted entity and is a projection over workflow state held on each source document.

**Used by** any HOD / Procurement Manager / Finance Controller who appears in a stage's approver list &nbsp;·&nbsp; **No write-back to a local table** — every action calls the source document's API.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| See pending items | Procurement → **My Approval** | Sorted by `last_action_at_date` desc by default |
| Approve a PR / PO / CN | Row → **Approve** | Calls source-doc API; row drops off on success |
| Send back a PO (or PR) | Row → **Send Back** | Routes to `workflow_previous_stage`; required for "fix-and-resubmit" |
| Reject | Row → **Reject** | Terminates the source doc workflow |
| Bulk approve | Multi-select → **Approve selected** | Fans out one transaction per row |
| Inspect history | Expand row | Renders `workflow_history` JSON entries |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Row missing from inbox | Signed-in user not in `user_action.execute[]` on the doc's current stage | Check stage configuration in [[system-config/workflow]] |
| "409 Conflict" on approve | A peer in the same `execute[]` already acted; engine has advanced the stage | UI auto-refreshes — re-check the inbox |
| Action buttons disabled | Source document's posting period has closed | Reopen the period or void the document (finance) |
| Row appears but cannot act | `deleted_at` set on the source out-of-band | Refresh — the row should drop off |
| Cross-tenant doc shown | (Cannot happen) | All queries scoped by active tenant context |

## 4. Edge Cases

- **No own table.** Every action is a write against the source document, not the inbox. The inbox itself has no audit trail — `workflow_history` lives on the source.
- **Concurrency.** Two peers acting on the same row simultaneously: the second action gets `409 Conflict` because `workflow_current_stage` has advanced. UI re-queries and the row drops off.
- **Soft-deleted source hidden.** Rows where `deleted_at IS NOT NULL` on the source are excluded.
- **Period-closed docs.** Row stays visible but action buttons disable — finance must reopen or void.
- **Identity filter only.** A row is visible **iff** the signed-in user's id is in `user_action.execute[]`. No additional role check at this layer — the engine resolved roles to user-ids when it wrote the array.
- **Multi-tenancy.** Each query scoped by active tenant context; cross-tenant approvals impossible.

---

## 5. Data Model (Dev)

**There is no `tb_my_approval` table.** The page is a query / view backed by the workflow-state columns embedded in every approvable document. It scans those documents and surfaces the subset whose active stage matches the signed-in user.

### 5.1 Query pattern

For every approvable document type (PR, PO, CN, store requisition, etc.), the same column shape is queried:

| Column on source table | Purpose in My Approval |
| --- | --- |
| `workflow_id` | Identifies which workflow definition gates this document. |
| `workflow_current_stage` | The stage matched against the user's role / membership. |
| `workflow_previous_stage`, `workflow_next_stage` | Used to render Send-Back targets and the "next approver" preview. |
| `workflow_history` (JSON) | `[{stage, action, message, by:{id,name}, at}, …]` — audit trail rendered on row expansion. |
| `user_action` (JSON) | `{ execute: [{id}, …] }` — **the authoritative filter**: row appears only if signed-in user's id is in this array. |
| `last_action`, `last_action_at_date`, `last_action_by_id`, `last_action_by_name` | Most recent transition — shown on the row. |
| `doc_status` (per-module enum) | Surface-level filter — only `in_progress` (or equivalent "awaiting action" status) is listed. |

Identical column shape on `tb_purchase_request`, `tb_purchase_order`, `tb_credit_note`, and other approvable tables. The page issues a parallel query per document type and unions the rows.

### 5.2 The `user_action.execute[]` array

Populated by the workflow engine on each stage transition based on stage configuration in [[system-config/workflow]]:

- **Role-based stage** — every user holding the configured role is enumerated into `execute[]`.
- **Named-approver stage** — the named user(s) added directly.
- **Threshold-routed stage** — threshold rule resolves to a role or named user, then enumerated.

A user sees a row **iff** their id is in `execute[]` for the doc's `workflow_current_stage`. Once any peer acts, the engine recomputes for the next stage and the row drops off.

## 6. Workflow / Business Rules

The inbox **has no own status** — behaviour is entirely a projection:

- **Row appears** when the engine populates a doc's `execute[]` with the signed-in user's id.
- **Row disappears** when the user (or peer) approves, rejects, sends-back, or split-rejects.
- **Row state mirrors source.** If the source is cancelled / voided out-of-band, the row drops off on next refresh.

Approve / reject / send-back invoke the same backend endpoints as each module's detail page — the inbox is purely a routing convenience. Bulk approve fans out one transaction per row. No fields on the inbox row itself are editable. The inbox owns no posting effect.

## 7. Cross-References

- [[purchase-request]] — primary document type; inbox typically renders PRs awaiting each stage.
- [[purchase-order]] — POs requiring manual approval (price-threshold, vendor-risk, budget-override).
- [[purchase-order/credit-note]] — CRNs awaiting approval under the same workflow-state contract.
- [[system-config/workflow]] — stage definition, role mapping, threshold rules, and the rule populating `user_action.execute[]`.
- [[access-control/application-role]] — role-to-permission mapping for eligibility.
- [[purchase-request/03-user-flow-approver]] — approver persona walkthrough.

## 8. References

- **Prisma (no own table):** workflow-state columns on `tb_purchase_request`, `tb_purchase_order`, `tb_credit_note`, etc. — `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (workflow_* and user_action block replicated on each approvable model; CN example at lines 358-376).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/approval/`.
- **Carmen docs:** `../carmen/docs/business-analysis/my-approvals-ba.md`; approver experience in `../carmen/docs/purchase-request-management/PR-User-Experience.md`.
