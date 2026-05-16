---
title: PR Dashboard
description: Purchase Request summary tiles — pipeline by stage, sent-back/rejected lists, personal vs department spending, and the approver task queue.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, purchase-request, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# PR Dashboard

## 1. Purpose

PR Dashboard at `/dashboard/pr` is a personal-requisitions cockpit. The page header reads "MY PR – PERSONAL REQUISITIONS DASHBOARD" with a date subtitle, signalling that the surface is scoped to the signed-in user's work rather than a system-wide view. It answers two questions for a requester or approver: *"where are my PRs stuck?"* and *"what's waiting on me right now?"*

The layout is a five-stage pipeline strip at the top, two tables (Sent Back, Rejected) on the left, a spending donut + bar pair on the right, and a full-width Awaiting Approval task queue at the bottom.

## 2. Tiles / Widgets

| Tile | Type | What it shows | Drill-down | Data source (current) |
|---|---|---|---|---|
| PR Summary (Status Pipeline) | Five-step pipeline strip with icons + arrows | Stages: Requests, In Process, Approved, PO Generated, Received — each with count and progress bar | (Inferred) → [[purchase-request]] filtered by stage | `mock/pr.ts` → `prPipelineSummary` |
| Sent Back PRs | Table | PR Number, Item Name, Date Sent, Sender, Reason — with CornerUpLeft icon | (Inferred) → [[purchase-request]] detail | `mock/pr.ts` → `sentBackPrs` |
| PRs Rejected & Item Rejects | Table | PR Number/Item ID, Material Name, Requester, Rejected By, Reason — with XCircle icon | (Inferred) → [[purchase-request]] detail | `mock/pr.ts` → `rejectedPrs` |
| My Spending (Personal) | Donut chart | Personal spend split by 3 categories with external-label percent | — | `mock/pr.ts` → `personalSpending` |
| Department Spending (F&B Dept) | Horizontal bar chart | 3 categories (Food, Beverage, Guest Supply) with amount labels | — | `mock/pr.ts` → `departmentSpending` |
| PRs Awaiting Approval (Task Queue) | Table with status badge | PR Number, Item Name, Requester, Dept, Date Requested, Status (`Awaiting HOD Approve` / `Awaiting PO`), "Direct details" action | (Inferred) → [[purchase-request]] detail | `mock/pr.ts` → `awaitingApprovalQueue` |

Currency formatting in the spending charts uses USD (`$`) in the current mock — this is a sample-data quirk; production should follow the BU base currency rule from [[master-data/exchange-rate]].

## 3. Data Sources

Currently mocked. Expected live mapping:

- Pipeline counts — group-count on [[purchase-request]] by workflow stage. The five buckets collapse the underlying `workflow_current_stage` values (see [[system-config/workflow]]) into Requests / In Process / Approved / PO Generated / Received.
- Sent Back / Rejected tables — `workflow_action_history` rows filtered to `action ∈ {send_back, reject}` joined back to [[purchase-request]] for material name and requester.
- Personal vs Department spending — sum on PR line amount grouped by [[master-data/product-category]], scoped first by `requestor_id = current_user` then by `department_id`.
- Awaiting Approval — equivalent to `useApprovalPending({ doc_type: "pr" })` defined in `hooks/use-approval.ts` once wired.

## 4. Refresh Cadence

Static mock today. Once wired through `useApprovalPending`, the TanStack Query default applies with no explicit `staleTime` override — refetch on window focus, no polling interval. The pending-count badges shown in the sidebar (separate from this page) use `CACHE_DYNAMIC` (1-minute stale time).

## 5. Audience & Persona

- **Requester** — primary audience. Watches the Sent Back and Rejected tables to fix and resubmit, and the pipeline strip to see their own PRs progress.
- **HOD / Approver** — uses the Awaiting Approval task queue at the bottom as a work-list; the `Awaiting HOD Approve` badge specifically targets HOD action.
- **Procurement** — checks `Awaiting PO` badged rows to see what's been HOD-approved and is ready to convert into a [[purchase-order]].

## 6. Related Modules

- [[purchase-request]] — the transactional system-of-record behind every tile
- [[purchase-request/my-approval]] — drill destination for the task queue
- [[purchase-order]] — downstream conversion target for `PO Generated` stage
- [[good-receive-note]] — downstream `Received` stage
- [[system-config/workflow]] — stage definitions that drive the pipeline buckets

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/pr/page.tsx` — page shell
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-pr.tsx` — `DashboardPr` composition (PR pipeline, sent-back, rejected, spending, awaiting approval)
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/pr.ts` — fixture data
- `../carmen-inventory-frontend/messages/en.json` → `dashboard.pr.title` = "Purchase Request Dashboard"
- `../carmen-inventory-frontend/hooks/use-approval.ts` — `useApprovalPending` for the awaiting-approval task queue (not yet mounted on this page)
