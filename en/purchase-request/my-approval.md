---
title: My Approval
description: Personal approval queue surfacing every PR (and related document) the current user must act on — single pane across modules.
published: true
date: 2026-05-16T17:00:00.000Z
tags: purchase-request, approval, workflow, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# My Approval

## 1. Purpose

The **My Approval** surface (`/procurement/approval`) is the per-user inbox that aggregates every workflow stage currently assigned to the signed-in user across approvable document types — primarily Purchase Requests, but also Purchase Orders, Credit Notes, and any other module where the workflow engine drives stage gating. Where opening each module individually shows *all* of that module's documents, **My Approval shows only the slice the current user must act on right now**. It exists so a procurement manager who supervises 200 PRs a day doesn't have to walk the PR list filtering by status — the inbox does that work.

The page is **read-and-act** only — it does not own any persisted entity. It is a projection over workflow state held on each source document.

## 2. Prisma Model(s)

**There is no `tb_my_approval` table.** The page is a query/view backed by the workflow-state columns embedded in every approvable document. It scans those documents and surfaces the subset whose active stage matches the signed-in user.

### 2.1 Query pattern

For every approvable document type (PR, PO, CN, store requisition, etc.), the same column shape is queried:

| Column on source table | Purpose in My Approval |
| --- | --- |
| `workflow_id` | Identifies which workflow definition gates this document. |
| `workflow_current_stage` | The stage to match against the user's role / membership. |
| `workflow_previous_stage`, `workflow_next_stage` | Used to render Send-Back targets and the "next approver" preview column. |
| `workflow_history` (JSON) | `[{stage, action, message, by:{id,name}, at}, …]` — the audit trail rendered on row expansion. |
| `user_action` (JSON) | `{ execute: [{id}, …] }` — **the authoritative filter**: the row appears in My Approval only if the signed-in user's id is in this array. |
| `last_action`, `last_action_at_date`, `last_action_by_id`, `last_action_by_name` | Most recent transition — shown on the inbox row. |
| `doc_status` (per-module enum) | Surface-level filter — only `in_progress` (or equivalent "awaiting action" status) is listed. |

These columns are present identically on `tb_purchase_request`, `tb_purchase_order`, `tb_credit_note`, and other approvable tables (see Section 4 of [[purchase-order/credit-note]] for the CN shape). The page issues a parallel query per document type and unions the rows.

### 2.2 The `user_action.execute[]` array

The decisive piece is the `execute[]` array on `user_action`. The workflow engine populates it on each stage transition based on the stage's role / approver-list configuration in [[system-config/workflow]]:

- **Role-based stage** — every user holding the configured role is enumerated and added to `execute[]`.
- **Named-approver stage** — the named user(s) are added directly.
- **Threshold-routed stage** — the threshold rule resolves to a role or named user, which is then enumerated.

A user sees a row in My Approval **iff** their id is in `execute[]` for that document's `workflow_current_stage`. Once the user (or any peer in the same `execute[]`) acts, the engine recomputes the array for the next stage and the row drops off this user's inbox.

## 3. Workflow / Lifecycle

My Approval is **read-only as a page** — it has no own status. Behaviour is entirely a projection:

- **Row appears** when the engine populates a document's `execute[]` with the signed-in user's id.
- **Row disappears** when the user (or a peer) approves, rejects, sends-back, or split-rejects, transitioning the document to its next stage and recomputing `execute[]`.
- **Row state mirrors the source document.** If the source is cancelled or voided out-of-band (e.g. by an admin), the row drops off the inbox immediately on next refresh.

Approve / reject / send-back actions invoke the same backend endpoints exposed by each module's detail page — the inbox is purely a routing convenience. Bulk approve fans out one transaction per row.

## 4. Usage / Cross-References

- [[purchase-request]] — primary document type. The inbox typically renders PR rows that need approval at every stage of the PR workflow.
- [[purchase-order]] — POs that require manual approval (price-threshold, vendor-risk, or budget-override stages) surface here.
- [[purchase-order/credit-note]] — CRNs awaiting approval render here under the same workflow-state contract.
- [[system-config/workflow]] — stage definition, role mapping, threshold rules, and the rule that populates `user_action.execute[]`.
- [[access-control/application-role]] — role-to-permission mapping that determines which documents the user is *eligible* to see; combined with `execute[]` membership to gate visibility.
- [[purchase-request/03-user-flow-approver]] — approver persona walkthrough referencing the inbox.

## 5. Business Rules

- **Identity filter.** A row is visible only when the signed-in user's id is in `user_action.execute[]`. No additional role check is required at this layer — the engine has already resolved roles to users when it wrote the array.
- **No row reordering.** The inbox sorts by `last_action_at_date` descending by default; secondary sort by document type, then `cn_no` / `pr_no` / `po_no`. The user may override sort but no field becomes write-protected.
- **Read-only inbox.** No fields on the inbox row itself are editable. Mutating actions are limited to the workflow transitions (approve / reject / send-back / split-reject) and go through the source document's API contract.
- **Concurrency.** When two peers act on the same row simultaneously, the second action receives a `409 Conflict` because the engine has already advanced `workflow_current_stage`. The UI re-queries and the row drops off.
- **Soft-deleted rows hidden.** Rows where `deleted_at IS NOT NULL` on the source document are excluded.
- **Period-closed documents excluded.** If the source document's posting period has closed since the workflow began, the row remains visible but the action buttons disable — finance must reopen the period or void the document.
- **Multi-tenancy.** Each query is scoped by the active tenant context; cross-tenant approvals are not possible.
- **Audit.** Every action taken from the inbox appends one entry to `workflow_history` on the source document. The inbox itself does not own an audit trail.

## 6. References

- **Prisma (no own table):** workflow-state columns on `tb_purchase_request`, `tb_purchase_order`, `tb_credit_note`, etc. — see `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (the `workflow_*` and `user_action` block is replicated on each approvable model; CN example at lines 358-376).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/approval/`.
- **Carmen docs:** `../carmen/docs/business-analysis/my-approvals-ba.md`; approver experience in `../carmen/docs/purchase-request-management/PR-User-Experience.md`.
- **Cross-module:** see Section 4.
