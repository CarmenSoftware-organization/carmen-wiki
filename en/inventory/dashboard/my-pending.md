---
title: My Pending Dashboard Widget
description: Personal pending-count widget on /dashboard showing the number of draft or in-progress documents awaiting the signed-in user's action across PR, PO, and SR.
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, my-pending, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# My Pending Dashboard Widget

> **At a Glance**
> **Route:** `/dashboard` (widget — not a standalone route) &nbsp;·&nbsp; **For:** Requester &nbsp;·&nbsp; Purchaser &nbsp;·&nbsp; Store Manager &nbsp;·&nbsp; **Status:** **Live** — real API endpoints; hooks are mounted and return live counts &nbsp;·&nbsp; **Scope:** Personal — counts are scoped to the signed-in user only

## 1. What & Who

The **My Pending** section is a widget rendered inside the `/dashboard` page. It shows a row of three coloured count cards — one per document type (PR / PO / SR) — each displaying the number of documents in a pending state that belong to the current user. Clicking a card navigates to the relevant transactional module filtered to the user's pending documents.

**Layout:** Three cards in a responsive grid (1 col → 2 col → 3 col), each with:
- Coloured left border (module colour from `module-color-map.ts`)
- Document-type icon (FileText / ShoppingCart / ClipboardList)
- Count number + "pending" label
- Arrow-right icon visible on hover

**Audience**

- **Requester** — sees outstanding PR drafts and submitted PRs still in the workflow.
- **Purchaser** — sees POs awaiting action.
- **Store Manager / Store Staff** — sees SR documents awaiting processing.

## 2. Tiles & Drill-downs

| Card | What it shows | Drill-down |
|---|---|---|
| **Purchase Requests** | Count of user's pending PRs (`prCount.pending`) | → [purchase-request](/en/inventory/purchase-request) list (own pending) |
| **Purchase Orders** | Count of user's pending POs (`poCount.pending`) | → [purchase-order](/en/inventory/purchase-order) list (own pending) |
| **Store Requisitions** | Count of user's pending SRs (`srCount.pending`) | → [store-requisition](/en/inventory/store-requisition) list (own pending) |

Pending means the document exists and has not yet reached a terminal state (received / completed / cancelled). Exact stage boundary is defined by the backend query behind each count endpoint.

## 3. Common Questions

| Question | Answer |
|---|---|
| What counts as "pending" for a PR? | Any PR owned by the current user that is not in a terminal state. The backend count endpoint defines the boundary — check `GET /api/proxy/api/my-pending/purchase-requests/count`. |
| Does the count include documents I submitted that are now with the approver? | Yes — pending means the document has not reached a terminal state, regardless of whose action is next. |
| Why does my count show 0 when I know I have open documents? | Ensure you are signed in with the correct user. Counts are strictly personal (`requestor_id = current_user`). If still 0, the endpoint may be returning stale cache — wait 1 min for `CACHE_DYNAMIC` to expire or refresh the page. |
| Is "My Pending" the same as the Awaiting Approval queue? | No. "My Pending" counts documents where the **current user is the requester/owner**. The Awaiting Approval queue (see [dashboard/my-approval](/en/inventory/dashboard/my-approval)) shows documents where the current user is the **next approver**. |
| Can I see pending documents for other users? | No. This widget is strictly scoped to `current_user`. For team visibility, use the domain-specific dashboards or transactional list pages. |

## 4. Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| All three counts show 0 incorrectly | Hook is mounted but the API returned an error silently | Open browser DevTools → Network tab, filter by `my-pending` — check for 4xx/5xx |
| Count does not drop after I complete a document | `CACHE_DYNAMIC` staleTime is 1 min | Wait 60 s or navigate away and return to trigger a refetch-on-focus |
| Clicking a count card navigates but the list is not filtered | Drill-down links go to the module root; no filter query param is currently passed | Navigate manually within the module to apply the pending filter |
| SR count card is missing | Component skips the card if the hook throws | Check `useMyPendingSrCount` — verify the endpoint `MY_PENDING_STORE_REQUISITIONS_COUNT` is reachable |

---

## 5. Data Sources (Dev)

- **PR count** — `GET /api/proxy/api/my-pending/purchase-requests/count` → `{ pending: number }`. Hook: `useMyPendingPrCount` (`hooks/use-dashboard.ts`). Query key: `MY_PENDING_PURCHASE_REQUESTS_COUNT`.
- **PO count** — `GET /api/proxy/api/my-pending/purchase-orders/count` → `{ pending: number }`. Hook: `useMyPendingPoCount`. Query key: `MY_PENDING_PURCHASE_ORDERS_COUNT`.
- **SR count** — `GET /api/proxy/api/my-pending/store-requisitions/count` → `{ pending: number }`. Hook: `useMyPendingSrCount`. Query key: `MY_PENDING_STORE_REQUISITIONS_COUNT`.

All three hooks use `CACHE_DYNAMIC` (staleTime 1 min). Endpoint paths are registered in `constant/api-endpoints.ts`.

Note: these same endpoint paths are used in the sidebar badge counts — the same hooks are reused across widgets and sidebar without separate fetches.

## 6. Refresh Cadence

`CACHE_DYNAMIC` — TanStack Query staleTime 1 minute. Refetch on window focus; no background polling. Counts are updated within 1 min of a document state change (or immediately after a forced refresh).

## 7. Related Modules

- [purchase-request](/en/inventory/purchase-request) — transactional module for PRs; pending-count source
- [purchase-order](/en/inventory/purchase-order) — transactional module for POs; pending-count source
- [store-requisition](/en/inventory/store-requisition) — transactional module for SRs; pending-count source
- [dashboard/my-approval](/en/inventory/dashboard/my-approval) — companion widget showing documents awaiting the user's approval action
- [dashboard/widget-workspace](/en/inventory/dashboard/widget-workspace) — the `/dashboard` page that hosts this widget

## 8. Reference Sources

- **Component:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-my-pending.tsx`
- **Hooks:** `../carmen-inventory-frontend-react/hooks/use-dashboard.ts` — `useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`
- **API constants:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` → `MY_PENDING_PURCHASE_REQUESTS_COUNT`, `MY_PENDING_PURCHASE_ORDERS_COUNT`, `MY_PENDING_STORE_REQUISITIONS_COUNT`
- **Colour mapping:** `../carmen-inventory-frontend-react/constant/module-color-map.ts` → `getModuleColor`
- **Cache config:** `../carmen-inventory-frontend-react/lib/cache-config.ts` → `CACHE_DYNAMIC`
