---
title: SR Dashboard
description: "REMOVED 2026-06-27, historical reference only: Store Requisition cockpit — four-stage pipeline, sent-back / reject lists, time-bucketed awaiting-approval table, personal vs department consumption charts, SR awaiting receipt, and template shortcuts."
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, store-requisition, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# SR Dashboard

> **At a Glance**
> **Route:** none — `/dashboard/sr` never existed as a route &nbsp;·&nbsp; **Status:** **Removed 2026-06-27** — historical reference only; the demo component was deleted as dead code and never appeared behind any router entry

## Implementation status (verified 2026-07-16)

This page documents `dashboard-sr.tsx` (formerly `routes/dashboard/_components/dashboard-sr.tsx`) and its `mock/sr.ts` fixture. `/dashboard/sr` never existed in `routes/router.tsx` — the Dashboard sidebar entry has only ever resolved to one component, today's [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace). The demo file was deleted, with 7 siblings, in commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", `carmen-inventory-frontend-react`, 2026-06-27), whose message states it and its mock fixture had "no importers anywhere." Everything below describes that deleted, never-routed demo screen — kept only as historical reference. Treat every "mock-data today," "when live," and route claim in the rest of this page as void; none of it will go live under this page.

![SR Dashboard screen](/screenshots/dashboard/sr.png)

## 1. What & Who

Requester's working surface for inter-location stock transfers. Answers *"what have I requested, what's bouncing back, what's waiting to be approved, and what do I usually consume?"*

**Layout:** 4-tile pipeline strip (Requested / In Process / Approved / Issued) → left column with 3 stacked tables (Sent Back, Reject List, Awaiting Approval with Today/Week/Month tabs) → middle column with My Consumption donut + SR Awaiting Received list → right column with department consumption bar + "My Templates" shortcut list. Footer strip shows version and signed-in user identity — visible only on this page.

**Audience**

- **Requester / Store Staff** — primary. Watches Sent Back (Bulk Submit), uses My Templates, tracks SR Awaiting Received.
- **HOD / Approver** — uses Awaiting Approval table with day-band tabs as their work queue.
- **Department Manager** — watches Dept Consumption for category-level trends.

## 2. Tiles & Drill-downs

| Tile | What it shows | Drill-down (when live) |
|---|---|---|
| **SR Summary (Pipeline)** | 4 stages: Requested / In Process / Approved / Issued — count + sub-label | → [store-requisition](/en/inventory/store-requisition) filtered by stage |
| **Sent Back SRs** | SR#, Requester, Date Sent, Sender, Reason + **Bulk Submit** button | → [store-requisition](/en/inventory/store-requisition) detail; bulk action re-submits |
| **Reject List (SRs & Items)** | SR#, Material, Requester, Rejected By, Reason | → [store-requisition](/en/inventory/store-requisition) detail |
| **SRs Awaiting Approval** | PR No, Description, Amount, Stage — tabs Today / Week / Month | → [store-requisition](/en/inventory/store-requisition) detail |
| **My Consumption (Personal)** | Donut + centred total + 3-segment legend | — |
| **SR Awaiting Received** | Scrollable: PR No, Description, Amount | → [store-requisition](/en/inventory/store-requisition) receipt view |
| **Dept Consumption (F&B Dept)** | Horizontal bar + legend | — |
| **My Templates** | Button list of saved SR template names — click loads template | → [store-requisition](/en/inventory/store-requisition) new with template |
| **Footer** | Version, user, role, timestamp | — (hard-coded in `dashboard-sr.tsx`) |

The header column labels read "PR No" / "PR Number" inside SR tables — this is a copy/paste artefact from the PR dashboard mock; the real column refers to the SR document number. **(Inferred — to be verified against live UI; flag for frontend team.)**

## 3. Common Questions

| Question | Answer |
|---|---|
| Why does the column say "PR No" inside SR tables? | **Mock-data copy/paste artefact** from the PR dashboard fixture. The real column is the SR document number. Flag for the frontend team. |
| Does "Bulk Submit" on Sent Back actually re-submit? | (Inferred — to be verified against live UI) Mock has no handler; live wiring should batch re-submit through [store-requisition](/en/inventory/store-requisition) workflow. |
| How does the Today / Week / Month tab differ? | Same query (`useApprovalPending({ doc_type: "sr" })`), different `doc_date` filter window. |
| Where are "My Templates" stored? | TBD — likely `tb_sr_template` keyed by `user_id`. Schema not finalised. |
| How is "My Consumption" computed? | Sum on consumed inventory (recipe + wastage + manual) where `requestor_id = current_user`, grouped by [product/category](/en/inventory/product/category). |
| What lands in "SR Awaiting Received"? | [store-requisition](/en/inventory/store-requisition) where `status = "issued"` AND `destination_location_id IN (user's locations)` AND not yet receipted. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Pipeline stage count doesn't match [store-requisition](/en/inventory/store-requisition) list | Mock fixture, not live | Resolves when `useApprovalPending` is mounted |
| "Bulk Submit" click does nothing | No handler wired in current build | (Inferred — to be verified against live UI) |
| "My Templates" empty or shows other users' templates | Mock fixture is global, not user-scoped | Live wiring filters by `user_id` |
| Donut shows `$` not `฿` | Mock fixture currency quirk | Production localises to BU base currency |
| Tab switch on Awaiting Approval shows same rows | Mock arrays differ but state-binding may regress | Inspect `awaitingSrsToday` / `awaitingSrsWeek` / `awaitingSrsMonth` in `mock/sr.ts` |

---

## 5. Data Sources (Dev)

- **Pipeline counts** — group-count on [store-requisition](/en/inventory/store-requisition) by workflow stage, projecting `workflow_current_stage` onto the 4 buckets
- **Sent Back / Reject List** — `workflow_action_history` filtered to send-back / reject, joined back to [store-requisition](/en/inventory/store-requisition)
- **Awaiting Approval** — `useApprovalPending({ doc_type: "sr" })` (`hooks/use-approval.ts`); tabs differ by `doc_date` filter
- **My Consumption** — sum consumed inventory (recipe + wastage + manual) where `requestor_id = current_user`, grouped by [product/category](/en/inventory/product/category)
- **SR Awaiting Received** — [store-requisition](/en/inventory/store-requisition) where `status = "issued"` AND `destination_location_id IN (user's locations)` AND not receipted
- **Dept Consumption** — same query as My Consumption, scoped by `department_id` not `requestor_id`
- **My Templates** — user-saved SR templates (table TBD; likely `tb_sr_template` keyed by `user_id`)

## 6. Refresh Cadence

Static mock today. "Awaiting Approval" tabs and "Sent Back" / "Reject List" should refresh on focus once wired — `CACHE_DYNAMIC` (1-min stale). Consumption charts can use `CACHE_NORMAL` (5-min).

## 7. Related Modules

- [store-requisition](/en/inventory/store-requisition) — transactional system-of-record behind every tile
- [store-requisition/stock-replenishment](/en/inventory/store-requisition/stock-replenishment) — auto-generated SR variant that may appear in pipeline
- [inventory](/en/inventory/inventory) — backs consumption aggregates and the awaiting-received flow
- [purchase-request](/en/inventory/purchase-request) — sibling document type sharing the approval framework

## 8. Reference Sources

- **Page shell / composition (deleted 2026-06-27):** `routes/dashboard/_components/dashboard-sr.tsx` in `../carmen-inventory-frontend-react`
- **Mock data (deleted 2026-06-27):** `routes/dashboard/mock/sr.ts` in `../carmen-inventory-frontend-react` (included `AwaitingTab` type)
- **Deletion commit:** `03891e3d` — "refactor(dashboard): convert to idiomatic structure, drop dead demo code"
- **i18n key still present but unused:** `messages/en.json` → `dashboard.sr.title` = "Store Requisition Dashboard"
- **`useApprovalPending` hook** (`hooks/use-approval.ts`) is real and live, but powers `/procurement/approval` — see [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) — not this deleted page
