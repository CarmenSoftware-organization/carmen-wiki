---
title: SR Dashboard
description: Store Requisition cockpit — four-stage pipeline, sent-back / reject lists, time-bucketed awaiting-approval table, personal vs department consumption charts, SR awaiting receipt, and template shortcuts.
published: true
date: 2026-05-16T17:00:00.000Z
tags: dashboard, store-requisition, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# SR Dashboard

## 1. Purpose

SR Dashboard at `/dashboard/sr` is the requester's working surface for inter-location stock transfers. It answers *"what have I requested, what's bouncing back, what's waiting to be approved, and what do I usually consume?"* The page leads with a four-tile pipeline strip (Requested / In Process / Approved / Issued), then arranges a left column with three stacked tables (Sent Back, Reject List, Awaiting Approval with Today/Week/Month tabs), a middle column with a My Consumption donut and an SR Awaiting Received list, and a right column with a department consumption bar and a "My Templates" shortcut list.

A footer strip at the bottom shows version and signed-in user identity — visible only on this page.

## 2. Tiles / Widgets

| Tile | Type | What it shows | Drill-down | Data source (current) |
|---|---|---|---|---|
| SR Summary (Status Pipeline) | Four-card strip with chevron arrows | Stages: Requested, In Process, Approved, Issued — each with count and sub-label | (Inferred) → [[store-requisition]] filtered by stage | `mock/sr.ts` → `srPipeline` |
| Sent Back SRs | Table + "Bulk Submit" button | SR#, Requester, Date Sent, Sender, Reason — with AlertCircle icon | (Inferred) → [[store-requisition]] detail; bulk action re-submits | `mock/sr.ts` → `sentBackSrs` |
| Reject List (SRs & Items) | Table | SR#, Material Name, Requester, Rejected By, Reason — with XCircle icon | (Inferred) → [[store-requisition]] detail | `mock/sr.ts` → `srRejectList` |
| SRs Awaiting Approval | Table with Today / Week / Month tabs | PR No, Description, Amount, Stage | (Inferred) → [[store-requisition]] detail | `mock/sr.ts` → `awaitingSrsToday` / `awaitingSrsWeek` / `awaitingSrsMonth` |
| My Consumption (Personal) | Donut + centred total + legend | Total `$` figure in centre with 3-segment breakdown | — | `mock/sr.ts` → `myConsumption` |
| SR Awaiting Received | Scrollable table | PR No, Description, Amount | (Inferred) → [[store-requisition]] receipt view | `mock/sr.ts` → `srAwaitingReceived` |
| Dept Consumption (F&B Dept) | Horizontal bar chart + legend | Category + amount labels | — | `mock/sr.ts` → `deptConsumption` |
| My Templates | Button list | Saved SR template names; click loads the template | (Inferred) → [[store-requisition]] new with template | `mock/sr.ts` → `myTemplates` |
| Footer | Strip | Version, user, role, timestamp | — | hard-coded in `dashboard-sr.tsx` |

The header table-row labels read "PR No" / "PR Number" inside SR tables — this is a copy/paste artefact from the PR dashboard mock. The real column refers to the SR document number. Mark this **(Inferred — to be verified against live UI)** and flag for the frontend team.

## 3. Data Sources

Currently mocked. Expected live mapping:

- Pipeline counts — group-count on [[store-requisition]] by workflow stage, projecting `workflow_current_stage` onto the four buckets.
- Sent Back / Reject List — `workflow_action_history` filtered to send-back / reject, joined back to [[store-requisition]].
- Awaiting Approval — equivalent to `useApprovalPending({ doc_type: "sr" })` from `hooks/use-approval.ts`. The three tabs differ only by date filter (today / this week / this month).
- My Consumption — sum on consumed inventory (recipe + wastage + manual) where `requestor_id = current_user`, grouped by [[master-data/product-category]].
- SR Awaiting Received — [[store-requisition]] where `status = "issued"` AND `destination_location_id IN (user's locations)` AND not yet receipted.
- Dept Consumption — same query as My Consumption but scoped by `department_id` not `requestor_id`.
- My Templates — user-saved SR templates (table TBD; could be `tb_sr_template` keyed by user_id).

## 4. Refresh Cadence

Static mock today. The "Awaiting Approval" tabs and "Sent Back" / "Reject List" should refresh on focus once wired (operators expect to see new arrivals after they take action elsewhere). `CACHE_DYNAMIC` (1-minute stale) is appropriate. Consumption charts can use `CACHE_NORMAL` (5-minute).

## 5. Audience & Persona

- **Requester / Store Staff** — primary. Watches Sent Back to fix and re-submit (via Bulk Submit), uses My Templates to speed common requests, and tracks SR Awaiting Received for their destination location.
- **HOD / Approver** — uses the Awaiting Approval table with day-band tabs as their work queue.
- **Department Manager** — watches Dept Consumption for category-level trends.

## 6. Related Modules

- [[store-requisition]] — transactional system-of-record behind every tile
- [[store-requisition/stock-replenishment]] — auto-generated SR variant that may appear in the pipeline
- [[inventory]] — backs the consumption aggregates and the awaiting-received flow
- [[purchase-request]] — sibling document type sharing the approval framework

## 7. Reference Sources

- `../carmen-inventory-frontend/app/(root)/dashboard/sr/page.tsx` — page shell
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-sr.tsx` — `DashboardSr` composition (pipeline, sent-back, reject list, awaiting approval, my consumption, awaiting received, dept consumption, templates, footer)
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/sr.ts` — fixture data including `AwaitingTab` type
- `../carmen-inventory-frontend/messages/en.json` → `dashboard.sr.title` = "Store Requisition Dashboard"
- `../carmen-inventory-frontend/hooks/use-approval.ts` — `useApprovalPending` for the awaiting-approval table (not yet mounted on this page)
