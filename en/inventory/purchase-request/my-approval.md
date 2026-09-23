---
title: My Approval
description: Personal pending queue — every PR, PO and SR the signed-in user must act on, served as one sorted list from the sys_v_my_pending view via GET /api/my-pending.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-request, approval, workflow, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# My Approval

> **At a Glance**
> **Owner:** Any workflow approver (and any draft owner) &nbsp;·&nbsp; **Table:** *none — read-only view `sys_v_my_pending`* &nbsp;·&nbsp; **Workflow:** read-only inbox; every action happens on the source document &nbsp;·&nbsp; **Upstream:** [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; Aggregated personal queue of documents awaiting the signed-in user's action.

![My Approval screen](/screenshots/purchase-request/my-approval.png)

> **Re-verified 2026-09-22.** The queue was rebuilt on both sides since the previous revision of this page: the backend added a unified read model (`apps/backend-gateway/src/application/my-pending/unified/`, micro-business `src/my-pending/`, database view `sys_v_my_pending` — migration `20260916030000_add_sys_v_my_pending`), and the frontend switched to it on 2026-09-16 (`routes/procurement/approval/use-approval.ts`, commit `9bd21427` "หน้าอนุมัติใช้ /api/my-pending แทนการรวมสามกลุ่มฝั่ง client"). Credit Notes were never part of this queue — earlier revisions of this page listed them by mistake.

## 1. What & Who

**My Approval** (`/procurement/approval`, `routes/router.tsx:287-288`) is the per-user queue of every **Purchase Request, Purchase Order and Store Requisition** that still needs the signed-in user's action. Where each module lists *all* of its documents, this page shows **only the slice the current user must act on right now** — plus the user's own unsubmitted drafts. The page is **read-and-navigate only**: it owns no table, renders no Approve / Reject buttons, and every decision is taken on the source document's detail page.

**Used by** anyone named in a workflow stage's `user_action.execute[]` (HOD, Purchaser, FC, GM, …) and anyone who owns a `draft` PR / PO / SR &nbsp;·&nbsp; **No write-back** — the page only reads.

## 2. What the frontend calls today

| Purpose | Endpoint | Source |
|---|---|---|
| Queue rows (one flat, sorted, paginated list of PR + PO + SR) | `GET /api/my-pending` — query `bu_code` (optional; omitted = every business unit the user belongs to), `page`, `perpage`, `sort`, `filter`, `search`, `searchfields` | `use-approval.ts` → `API_ENDPOINTS.APPROVAL_PENDING` (`constant/api-endpoints.ts:40`); backend `my-pending.unified.controller.ts` (`AppIdGuard('my-pending.unified.findAll')`) |
| Summary cards (`total` / `pr` / `po` / `sr` counts) | `GET /api/my-approve/pending` | `use-approval.ts` → `APPROVAL_PENDING_SUMMARY` (`api-endpoints.ts:41`); backend `my-approve.controller.ts` (`AppIdGuard('my-approve.findAllPending.count')`) |

Endpoints that still exist but the approval page **no longer calls**: `GET /api/my-approve` (the older grouped response — three arrays with a pagination envelope each; `my-approve.controller.ts`), and the per-type family `GET /api/my-pending/purchase-requests`, `/purchase-orders`, `/store-requisitions` (each with `/pending` counts, `:bu_code/workflow-stages`, `:bu_code/:id` and the same submit / approve / reject / review / save verbs as the module endpoints — `apps/backend-gateway/src/application/my-pending/{purchase-request,purchase-order,store-requisition}/`). The per-type endpoints are the ones the PR list's **My Pending** tab and the mobile app use; product-line search only works there, because the unified view carries header text only. Bruno contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/my-pending/`.

## 3. Common Tasks

| Task | Where | Notes |
|---|---|---|
| See pending items | Procurement → **My Approval** | Default order `doc_date:asc` (oldest document first, `MY_PENDING_DEFAULT_SORT` in `my-pending.sql.ts`; FE `defaultSort: "doc_date:asc"` in `approval-component.tsx`), tie-broken by `doc_type, id` so paging is stable |
| Narrow to one document type | Click the **Purchase Request / Purchase Order / Store Requisition** summary card | Sets `filter=doc_type:pr` (or `po` / `sr`); **Total Pending** clears it. Filtering, search and paging all run in SQL, so `paginate.total` is the true match count |
| Search | Toolbar search box | Header text only: `doc_no`, `description`, `requestor_name`, `department_name`, `counterparty_name`, `workflow_current_stage` (`DEFAULT_SEARCH_COLUMNS`) |
| Sort by a column | Click a column header | Only allowlisted view columns sort (`COLUMN_TYPES` in `my-pending.sql.ts`); an unknown key is dropped silently and the list falls back to `doc_date` |
| Open a document | **Document** column link | `/procurement/purchase-request/:id`, `/procurement/purchase-order/:id` or `/store-operation/store-requisition/:id` (`approve-queue-list.tsx` `DOC_TYPE_CONFIG`) — approve / reject / send back there |
| Bulk approve | *Not on this page* | Mobile uses `POST /:bu_code/purchase-requests/swipe-approve` / `swipe-reject` (and the PO twin); the web queue has no multi-select |

Columns rendered by `approve-queue-list.tsx`: `#`, Document (`doc_no`, linked), Send-back marker, Type badge (`pr` / `po` / `sr`), Date (`doc_date`), Status (`doc_status`, rendered with `PR_STATUS_CONFIG` labels for every type).

## 4. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Row missing from queue | Signed-in user is not in `user_action.execute[]` on the doc's current stage, and the doc is not a `draft` the user owns | Check stage membership in [system-config/workflow](/en/inventory/system-config/workflow) |
| Row present although the user "already approved it" | The action was taken on a stale `doc_version`, or a peer acted first; the source document rejected the write (409) | Reload the source document — the queue refreshes on its 1-minute `CACHE_DYNAMIC` stale time |
| Row shows a `draft` document | Own drafts are deliberately included (`("doc_status" = 'draft' AND "owner_id" = me)` branch of the predicate) | Expected — open it and submit or delete it |
| Row for a business unit the user did not select | `bu_code` omitted → the service reads every unit the user belongs to (`resolveBuCodes`, `my-pending.service.ts`) and merges the pages in memory | Pass `bu_code` to narrow |
| Sort click "does nothing" | Sort key is not a view column | Use one of the allowlisted columns (Section 5.2) |
| Cross-tenant doc shown | Cannot happen | Each unit is queried through its own tenant connection; a unit that fails to resolve is skipped and logged |

## 5. Data Model (Dev)

**There is no `tb_my_approval` table.** Since migration `20260916030000_add_sys_v_my_pending` the queue reads the database view `sys_v_my_pending`, a `UNION ALL` of `tb_purchase_request`, `tb_purchase_order` and `tb_store_requisition` normalised to one row shape. The view is deployed per tenant schema and is re-created with `DROP VIEW … CREATE VIEW` on every change (column order and types are part of the contract).

### 5.1 Row shape (`MyPendingUnifiedItemResponseDto`, `unified/swagger/response.ts`)

| Column | PR source | PO source | SR source |
| --- | --- | --- | --- |
| `doc_type` | `'pr'` | `'po'` | `'sr'` |
| `id`, `doc_no`, `doc_date` | `id`, `pr_no`, `pr_date` | `id`, `po_no`, `order_date` | `id`, `sr_no`, `sr_date` |
| `due_date` | `NULL` | `delivery_date` | `expected_date` |
| `doc_status` | `pr_status::text` | `po_status::text` | `doc_status::text` |
| `doc_subtype` | `NULL` | `po_type` | `sr_type` |
| `description`, `workflow_id`, `workflow_name`, `workflow_current_stage`, `workflow_next_stage`, `workflow_previous_stage` | same-named columns | same | same |
| `owner_id`, `requestor_name` | `requestor_id`, `requestor_name` | `buyer_id`, `buyer_name` | `requestor_id`, `requestor_name` |
| `department_id`, `department_name` | header columns | `NULL` (a PO has no department) | header columns |
| `counterparty_name` | `NULL` | `vendor_name` | `"<from_location_name> -> <to_location_name>"` |
| `currency_code` | `NULL` | `currency_code` | `NULL` |
| `net_amount`, `total_amount` | `base_net_amount`, `base_total_amount` | `SUM(detail.base_net_amount)`, `SUM(detail.base_total_price)` | `NULL` (no money on an SR) |
| `total_qty` | `NULL` | `total_qty` | `SUM(detail.requested_qty)` |
| `last_action`, `last_action_at_date`, `last_action_by_id`, `last_action_by_name`, `user_action`, `created_at`, `created_by_id`, `doc_version` | header columns | same | same |
| `bu_code`, `bu_name` | added by the service per business unit read | | |

`user_action` is read (the mobile stage-role filter needs it) but **stripped before the row leaves the service** — it names other users. The gateway adds `@EnrichAuditUsers()`; since 2026-09-18 vendor / audit fields on the list are objects, matching the per-unit list endpoints.

### 5.2 Predicate, exclusions, indexes

```
WHERE  ("user_action" -> 'execute' @> '[{"user_id": <me>}]'::jsonb
        OR ("doc_status" = 'draft' AND "owner_id" = <me>))
  AND  <allowlisted filter predicates>
  AND  (<search columns> ILIKE '%term%')          -- when search is given
ORDER BY <caller sort, allowlisted> , "doc_type" ASC, "id" ASC
LIMIT / OFFSET                                    -- perpage = -1 fetches everything
```

- Finished documents never enter the view — the exclusion lists are copied verbatim from the three per-type pending filters: PR `NOT IN ('voided','approved','completed')`; PO `NOT IN ('voided','approved','sent_or_print','partial','closed','completed')`; SR `NOT IN ('voided','completed','cancelled')`. A `NULL` status is excluded too.
- Sortable / filterable columns (`COLUMN_TYPES`, `my-pending.sql.ts`): `doc_type`, `doc_no`, `doc_date`, `due_date`, `doc_status`, `doc_subtype`, `description`, `workflow_id`, `workflow_name`, `workflow_current_stage`, `workflow_next_stage`, `workflow_previous_stage`, `owner_id`, `requestor_name`, `department_id`, `department_name`, `counterparty_name`, `currency_code`, `net_amount`, `total_amount`, `total_qty`, `last_action`, `last_action_at_date`, `last_action_by_name`, `created_at`, `doc_version`. Filter values support comma lists (`= ANY`), `name|contains`, `name|daterange` (`from,to`).
- Indexes created by the migration: GIN `jsonb_path_ops` on `(user_action -> 'execute')` for all three tables (`ix_pr_user_action_execute`, `ix_po_user_action_execute`, `ix_sr_user_action_execute`) plus partial draft-owner indexes `ix_po_buyer_draft`, `ix_sr_requestor_draft` (`tb_purchase_request` already had `ix_pr_requestor_status`).
- **Multi-unit merge.** With no `bu_code`, `my-pending.service.ts` resolves every active membership from `tb_user_tb_business_unit`, runs the statement per tenant schema, merges the rows with the same comparator the SQL uses (`compareRows`, `NULLS LAST`) and sums `paginate.total` across units.
- **Mobile.** The `x-app-id` header selects a per-doc-type stage-role policy (`getMobileStageRoleFilter(appId, 'pr' | 'po' | 'sr')`); an SR keeps its `issue` stage, PR and PO do not.

## 6. Workflow / Business Rules

The queue **has no status of its own** — behaviour is entirely a projection:

- **Row appears** when the workflow engine writes the signed-in user's id into the document's `user_action.execute[]`, or when the user saves a `draft` they own.
- **Row disappears** when the document's status enters the exclusion list (final approve, complete, void, cancel) or when a stage transition recomputes `execute[]` without the user.
- **Approve / reject / send back** are the source module's endpoints (`PATCH /:bu_code/purchase-requests/:id/approve` etc.), each guarded by the source document's `doc_version` optimistic lock — see [system-config/doc-version](/en/inventory/system-config/doc-version). The queue itself never writes.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — primary document type; the PR list's own **My Pending** tab reads the per-type endpoint `GET /api/my-pending/purchase-requests`.
- [purchase-order](/en/inventory/purchase-order) — POs pending approval (`draft` / `in_progress` only; `approved` and `sent_or_print` are excluded).
- [store-requisition](/en/inventory/store-requisition) — SRs pending approval or issue.
- [system-config/workflow](/en/inventory/system-config/workflow) — stage definitions and the rule populating `user_action.execute[]`.
- [purchase-request/03-user-flow-approver](/en/inventory/purchase-request/03-user-flow-approver) — approver persona walkthrough.

## 8. References

- **View + indexes:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/migrations/20260916030000_add_sys_v_my_pending/migration.sql`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/my-pending/unified/` (controller, service, `swagger/response.ts`), `.../my-pending/my-approve/` (summary counts), `.../apps/micro-business/src/my-pending/` (`my-pending.sql.ts` predicate / allowlists / default sort, `my-pending.service.ts` multi-unit merge).
- **Frontend:** `../carmen-inventory-frontend-react/routes/procurement/approval/` (`approval.route.tsx`, `approval-component.tsx`, `approve-queue-list.tsx`, `use-approval.ts`), `types/approval.ts` (`RawApprovalUnified`, `ApprovalItem`, `ApprovalPendingSummary`).
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/my-pending/` (`my-approve/`, `purchase-request/`, `purchase-order/`, `store-requisition/`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/201-my-approvals.spec.ts` (21 tests), gap report `docs/test-cases/gaps/201-my-approvals-gap.md` (34 catalogued cases), generated story `docs/user-stories/201-my-approvals.md`.
