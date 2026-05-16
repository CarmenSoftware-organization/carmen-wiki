---
title: PR Dashboard
description: Purchase Request summary tiles — pipeline by stage, sent-back/rejected lists, personal vs department spending, and the approver task queue.
published: true
date: 2026-05-17T08:00:00.000Z
tags: dashboard, purchase-request, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# PR Dashboard

> **At a Glance**
> **Route:** `/dashboard/pr` &nbsp;·&nbsp; **For:** Requester &nbsp;·&nbsp; HOD / Approver &nbsp;·&nbsp; Procurement &nbsp;·&nbsp; **Status:** **Mock-data today**; live hooks defined but not mounted &nbsp;·&nbsp; **Scope:** Personal — the signed-in user's PRs

## 1. What & Who

Personal-requisitions cockpit. Header reads "MY PR – PERSONAL REQUISITIONS DASHBOARD". Answers two questions: *"where are my PRs stuck?"* and *"what's waiting on me right now?"*

**Layout:** Five-stage pipeline strip (top) → two tables Sent Back / Rejected (left) + spending donut + dept bar (right) → full-width Awaiting Approval queue (bottom).

**Audience**

- **Requester** — primary. Watches Sent Back / Rejected to fix and resubmit; tracks the pipeline strip.
- **HOD / Approver** — uses the Awaiting Approval task queue at the bottom; `Awaiting HOD Approve` badge targets HOD action.
- **Procurement** — checks `Awaiting PO` rows ready to convert into a [[purchase-order]].

## 2. Tiles & Drill-downs

| Tile | What it shows | Drill-down (when live) |
|---|---|---|
| **PR Summary (Pipeline)** | 5 stages: Requests / In Process / Approved / PO Generated / Received — count + progress bar | → [[purchase-request]] filtered by stage |
| **Sent Back PRs** | PR Number, Item, Date Sent, Sender, Reason | → [[purchase-request]] detail |
| **PRs Rejected & Item Rejects** | PR Number/Item ID, Material, Requester, Rejected By, Reason | → [[purchase-request]] detail |
| **My Spending (Personal)** | Donut by 3 categories with external-label percent | — |
| **Department Spending (F&B Dept)** | Horizontal bar: Food / Beverage / Guest Supply | — |
| **PRs Awaiting Approval** | PR, Item, Requester, Dept, Date, Status badge (`Awaiting HOD Approve` / `Awaiting PO`), "Direct details" action | → [[purchase-request]] detail |

Currency in spending charts renders as `$` in the mock — production should follow BU base currency from [[master-data/exchange-rate]].

## 3. Common Questions

| Question | Answer |
|---|---|
| Why don't my pipeline counts update after I submit a PR? | **Mock-data today** — counts come from `mock/pr.ts`, not from [[purchase-request]]. Live wiring will refresh on focus. |
| Where do the five stages come from? | Collapsed projection of `workflow_current_stage` (see [[system-config/workflow]]) into Requests / In Process / Approved / PO Generated / Received. |
| Is "My Spending" my PRs only, or my department's? | "My" is `requestor_id = current_user`; "Department" is `department_id` scoped — same query, different scope on PR-line amounts grouped by [[master-data/product-category]]. |
| When will Awaiting Approval go live? | Hook exists — `useApprovalPending({ doc_type: "pr" })` in `hooks/use-approval.ts` — but is **not yet mounted** on this page. |
| Why is currency showing `$` not `฿`? | Mock fixture quirk; production will localise to BU base currency. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Tile not clickable / drill goes nowhere | Drill-down routes not wired in current build | (Inferred — to be verified against live UI) |
| Numbers differ from [[purchase-request]] list | Page reads independent mock fixture, not live data | Resolves when `useApprovalPending` is mounted |
| Sent Back table empty for known sent-back PR | Mock fixture has finite seed rows | Inspect `mock/pr.ts` → `sentBackPrs` |
| `Awaiting HOD Approve` badge not refreshing after approve action | Mock is static; no event listener | Live wiring uses TanStack Query refetch-on-focus |

---

## 5. Data Sources (Dev)

- **Pipeline counts** — group-count on [[purchase-request]] by `workflow_current_stage`
- **Sent Back / Rejected** — `workflow_action_history` filtered to `action ∈ {send_back, reject}` joined to [[purchase-request]]
- **My / Department Spending** — sum PR-line amount grouped by [[master-data/product-category]], scoped by `requestor_id` / `department_id`
- **Awaiting Approval** — `useApprovalPending({ doc_type: "pr" })` (`hooks/use-approval.ts`) once wired

## 6. Refresh Cadence

Static mock today. Once wired through `useApprovalPending`, TanStack Query default applies — refetch on focus, no polling. Sidebar pending-count badges (separate from this page) use `CACHE_DYNAMIC` (1-min stale).

## 7. Related Modules

- [[purchase-request]] — transactional system-of-record
- [[purchase-request/my-approval]] — drill destination for the task queue
- [[purchase-order]] — downstream conversion target for `PO Generated`
- [[good-receive-note]] — downstream `Received` stage
- [[system-config/workflow]] — stage definitions that drive pipeline buckets

## 8. Reference Sources

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/pr/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-pr.tsx`
- **Mock data:** `../carmen-inventory-frontend/app/(root)/dashboard/mock/pr.ts`
- **i18n:** `messages/en.json` → `dashboard.pr.title` = "Purchase Request Dashboard"
- **Live hook (not mounted):** `../carmen-inventory-frontend/hooks/use-approval.ts` → `useApprovalPending`
