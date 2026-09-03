---
title: My Approval Dashboard Widget
description: "REMOVED, historical reference only — never actually rendered on /dashboard: a proposed personal approval task-queue widget listing PR/PO/SR documents awaiting the signed-in user's approval action. The real, live equivalent is the Procurement module's My Approval page (/procurement/approval)."
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, my-approval, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# My Approval Dashboard Widget

> **At a Glance**
> **Route:** none — never rendered anywhere &nbsp;·&nbsp; **Status:** **Removed 2026-06-27; was dead code even before that** — this widget was never mounted on the live `/dashboard` page, despite this page's prior claim of "Live". The real, live personal approval inbox is a **different page**: [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) (`/procurement/approval`)

## Implementation status (verified 2026-07-16)

**This page's prior "Live" status claim was wrong.** It documented `dashboard-my-approval.tsx` (formerly `routes/dashboard/_components/dashboard-my-approval.tsx`), which rendered the grouped PR/PO/SR approval tables described below, embedded inside `/dashboard`. Checking `dashboard-component.tsx` (both today's version and the version prior to the 2026-06-27 cleanup) shows the live `/dashboard` page has only ever rendered a greeting header plus the "Saved Widgets" grid — it never imported or mounted `dashboard-my-approval.tsx`. The component file was deleted, along with 7 siblings, in commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27), whose message confirms it was dead code with "no importers anywhere."

The `useApprovalPending` / `useApprovalPendingSummary` hooks this page describes (`hooks/use-approval.ts`) **are** real and live — but they power the Procurement module's **My Approval** page at `/procurement/approval` (a genuine, routed screen; see [purchase-request/my-approval](/en/inventory/purchase-request/my-approval)), not any section of `/dashboard`. This deleted widget's "View All →" link (described below) pointed at that same real page, which is the one place to actually see and act on pending approvals.

Everything else below describes this never-mounted, now-deleted dashboard widget — kept only as historical reference. Treat every "Live" / "mounted" / route claim in the rest of this page as void.

## 1. What & Who

The **My Approval** section is a widget rendered inside the `/dashboard` page. It displays documents awaiting the current user's approval action, grouped into three collapsible sections — Purchase Requests, Purchase Orders, and Store Requisitions — each with a count badge and a table of pending items.

This widget is the dashboard-level summary of what the full [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) page shows. It is limited to the 10 most recent items per fetch (`perpage: 10`).

**Layout:**
- Section header "Pending My Approval" with a warning badge showing total count.
- Three subsections (PR / PO / SR), each with a coloured left border (module colour), count badge, and an item table.
- PR / SR tables: Doc No, Requester, Department, Stage, Date.
- PO table: Doc No, Vendor, Amount, Stage, Date.
- "View All →" link at the bottom navigates to `/procurement/approval` when items exist.

**Audience**

- **HOD / Department Head** — primary approver; uses the PR section to action pending requests.
- **Procurement Manager** — uses the PO section to approve purchase orders.
- **Store Manager** — uses the SR section to approve store requisitions from their store.

## 2. Tiles & Drill-downs

| Section | What it shows | Drill-down |
|---|---|---|
| **Purchase Requests** | PR items awaiting current user's approval (`doc_type = pr`) — Doc No, Requester, Dept, Stage, Date | → [purchase-request](/en/inventory/purchase-request) detail for each row |
| **Purchase Orders** | PO items awaiting approval (`doc_type = po`) — Doc No, Vendor, Amount, Stage, Date | → [purchase-order](/en/inventory/purchase-order) detail for each row |
| **Store Requisitions** | SR items awaiting approval (`doc_type = sr`) — Doc No, Requester, Dept, Stage, Date | → [store-requisition](/en/inventory/store-requisition) detail for each row |
| **Summary badge** | Total count across all types from `useApprovalPendingSummary` | — |
| **View All** | Appears when any items exist | → `/procurement/approval` (full approval module) |

Items are sorted by `doc_date` descending from the API. The widget shows up to `perpage: 10` combined items; for the full queue use [purchase-request/my-approval](/en/inventory/purchase-request/my-approval).

## 3. Common Questions

| Question | Answer |
|---|---|
| What does "pending my approval" mean exactly? | The document is at a workflow stage where the current user's role is the designated approver — determined by `workflow_current_stage` matching the user's approval role. |
| Why do I see PO items in the PR section? | Data is partitioned by `doc_type` on the frontend from a single API response (`root.purchase_requests`, `root.purchase_orders`, `root.store_requisitions`). If mixed items appear, check the backend normalization in `hooks/use-approval.ts` → `normalizePR/PO/SR`. |
| Is this the same queue as the full Approval module? | Same data source, but the widget caps at `perpage: 10`. Click "View All" for the full list with pagination and search. |
| Why does the total badge say 5 but I only see 3 rows? | Summary count (`useApprovalPendingSummary` → `GET /api/proxy/api/my-approve/pending`) and the list (`useApprovalPending` → `GET /api/proxy/api/my-approve`) are separate queries that may differ by timing. |
| Do approvals done in this widget update the count immediately? | Not from this widget — clicking the doc-no link navigates away to the full detail page. After approving there and returning, the `CACHE_DYNAMIC` stale window (1 min) controls when counts refresh. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| Sections show "No items" despite having pending documents in the system | Current user is not the designated approver for those documents | Verify the workflow stage → approver-role mapping in [system-config/workflow](/en/inventory/system-config/workflow) |
| Warning badge shows 0 but item tables are non-empty | `useApprovalPendingSummary` and `useApprovalPending` are independent queries; timing difference | Reload the page — both will sync within `CACHE_DYNAMIC` window |
| Amount column on PO shows ฿0 | `total_amount` is null/0 in the API response for that PO | Verify PO line amounts are saved correctly in [purchase-order](/en/inventory/purchase-order) |
| "View All" link is not visible | `allItems.length === 0` — widget conditionally renders the link only when items exist | Verify the approval fetch is returning data; check DevTools network for `my-approve` |
| Loading skeleton persists indefinitely | `useApprovalPending` query is in loading state — likely `buCode` not resolved | Check `useBuCode` hook; ensure the user session has a valid BU context |

---

## 5. Data Sources (Dev)

- **Approval list** — `GET /api/proxy/api/my-approve` (+ `bu_code` query param) → response shape: `{ data: { purchase_requests: [...], purchase_orders: [...], store_requisitions: [...] } }`. Hook: `useApprovalPending({ perpage: 10 })` (`hooks/use-approval.ts`). Items are normalized by `normalizePR`, `normalizePO`, `normalizeSR` into `ApprovalItem[]`.
- **Approval summary** — `GET /api/proxy/api/my-approve/pending` → `ApprovalPendingSummary { total, pr, po, sr }`. Hook: `useApprovalPendingSummary`. Used for badge counts only.
- **API constants** (`constant/api-endpoints.ts`): `APPROVAL_PENDING = "/api/proxy/api/my-approve"`, `APPROVAL_PENDING_SUMMARY = "/api/proxy/api/my-approve/pending"`.
- **ApprovalItem shape** (`types/approval.ts`): `{ id, doc_type, doc_no, doc_date, requestor_name, department_name, vendor_name, total_amount, workflow_current_stage, ... }`.

## 6. Refresh Cadence

`CACHE_DYNAMIC` — TanStack Query staleTime 1 minute for both `useApprovalPending` and `useApprovalPendingSummary`. Refetch on window focus; no background polling. After taking approval action in the detail page, return to `/dashboard` to trigger a focus-refetch.

## 7. Related Modules

- [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) — **the real, live page** (`/procurement/approval`) — full approval queue with pagination, search, and approval actions across PR/PO/SR
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [store-requisition](/en/inventory/store-requisition) — transactional sources the real approval page draws from
- [system-config/workflow](/en/inventory/system-config/workflow) — workflow stage and approver-role definitions
- [dashboard/my-pending](/en/inventory/dashboard/my-pending) — sibling widget with the same fate (never mounted, now deleted)
- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the real, live `/dashboard` page; it does **not** host this widget and never did

## 8. Reference Sources

- **Component (deleted 2026-06-27):** `routes/dashboard/_components/dashboard-my-approval.tsx` in `../carmen-inventory-frontend-react`
- **Deletion commit:** `03891e3d` — "refactor(dashboard): convert to idiomatic structure, drop dead demo code"
- **Hooks (real and live, but power `/procurement/approval` — not `/dashboard`):** `../carmen-inventory-frontend-react/hooks/use-approval.ts` — `useApprovalPending`, `useApprovalPendingSummary`
- **Types:** `../carmen-inventory-frontend-react/types/approval.ts` — `ApprovalItem`, `ApprovalPendingSummary`, `RawApprovalPR`, `RawApprovalPO`, `RawApprovalSR`
- **API constants:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` → `APPROVAL_PENDING`, `APPROVAL_PENDING_SUMMARY`
- **Colour mapping:** `../carmen-inventory-frontend-react/constant/module-color-map.ts` → `getModuleColor`
