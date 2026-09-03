---
title: Inventory — User Flow — Inventory Controller
description: Inventory Controller's flow within the inventory module — running the period-end review and close.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (period-end operator) &nbsp;·&nbsp; **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Surface in this module:** the Period End screens (`/inventory-management/period-end` + `/review`, permissions `inventory_management.period_end.view` / `.execute`) and the read-only Transaction Log &nbsp;·&nbsp; **Key action:** **Close period** — gated by blocking documents + completed physical counts
> **Correction (2026-07-15):** the approval queue, count-variance commit console, stock-policy dashboard, and threshold routing previously documented here were **not backed by source** — none of those screens exist. What remains for this persona in this module is the period-end review/close and ledger verification.

## 1. Role in This Module

The **Inventory Controller** persona owns balance accuracy at period boundaries. In this module that means one concrete flow: drive the month towards a closable state, then run the close. The system enforces the gates server-side (`validatePeriodEnd`, re-checked under a row lock at close time); the Controller's job is working the review checklist down to green. There is no adjustment-approval queue, no variance dashboard, and no `tb_product_location` policy editor in this module's routes — adjustments are self-contained documents in [inventory-adjustment](/en/inventory/inventory-adjustment), and count review lives in [physical-count](/en/inventory/physical-count).

## 2. Entry Point and Primary Flow

**Entry point:** Inventory Management → Period End (`/inventory-management/period-end`).

**Primary flow (close the period, 7 steps):**

1. **Open the Period End page.** The current-period card shows the period code (YYMM), fiscal year/month, start/end dates, a status badge, and an optional note. "Current" is the earliest period with `status ∈ {open, locked}`. Below the card, the history list shows previously closed periods.
2. **Start the close.** Click the card's start-close button → `/inventory-management/period-end/review` (`GET /period-ends/review`).
3. **Work the blocking-document cards.** One card per module — PR, PO, GRN, CN, SR — each showing the period's document count and a complete/incomplete badge. Clicking a card opens a dialog listing the documents so the Controller can chase owners. Complete means: PR `approved/completed/voided`; PO `completed/closed/voided`; SR `completed/cancelled/voided`; GRN `committed/voided` (with `draft` also non-blocking on the backend gate); CN `completed/cancelled/voided` (with `draft` non-blocking).
4. **Work the physical-count section.** One row per required location (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) with counted/total progress; clicking an in-progress row deep-links to `/inventory-management/physical-count/{id}/entry`. Spot checks are **not** part of this gate.
5. **Close.** When all gates are green the **Close period** button (destructive style, confirm dialog) enables; clicking fires `POST /period-ends`.
6. **The close executes atomically.** Inside one transaction: `FOR UPDATE` lock + re-validation; lot carry-over (`CLOSE-…` zeroing rows, `OPEN-…` re-creation rows in the auto-provisioned next period; on average-method tenants also the `tb_period_snapshot` buckets); `tb_period.status = closed`; the period's `tb_physical_count_period` rows marked `completed`.
7. **Verify on the ledger.** Filter the Transaction Log for `inventory_doc_type IN ('close','open')` — the close itself is an auditable pair of ledger events.

## 3. Decision Branches

- **A module card is incomplete** — open its dialog, identify the blocking documents, and chase the owning users in the source modules. This module offers no bulk action over them.
- **A card shows zero documents but stays incomplete** — frontend quirk: `is_complete = count > 0 && …`, so an empty module reads incomplete even though the backend gate would pass; known discrepancy when testing empty periods.
- **`Cannot close period: incomplete documents {…}`** — a blocking document appeared between the review load and the click; refresh and resolve.
- **`Period already closed`** — another session won the close race; refresh.
- **Current period shows `locked`** — the lock came from the [system-config/period](/en/inventory/system-config/period) service; this screen still treats it as current and can close it.

## 4. Exit Point / Handoffs

- **Period closed** — the next period is already open (`ensureNextPeriod`); new movements stamp into it automatically. Handoff back to daily operations.
- **Close blocked** — handoff to the source-module owners (PR/PO/SR approvers, GRN/CN processors, counters) until the gates clear.

## 5. References

- Parent overview: [03-user-flow](/en/inventory/inventory/03-user-flow).
- Sibling: [period-end](/en/inventory/inventory/period-end) — full gate table, error strings, and dev-level process detail.
- Sibling: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_POST_009` / `INV_POST_010` (close/open), `INV_CALC_008` / `INV_CALC_009` (FIFO vs average close), `INV_AUTH_008` (the `period_end.execute` gate).
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-documents-dialog.tsx`, `pe-history.tsx`).
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/`.
- Related: [physical-count](/en/inventory/physical-count) (the count gate), [inventory-adjustment](/en/inventory/inventory-adjustment) (corrections), [system-config/period](/en/inventory/system-config/period) (period definitions and lock).
