---
title: Inventory — User Flow — Inventory Controller
description: Inventory Controller's flow within the inventory module — running the period-end review and close.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (period-end operator) &nbsp;·&nbsp; **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Surface in this module:** the Period End screens (`/inventory-management/period-end` + `/review`, permissions `inventory_management.period_end.view` / `.execute`) and the read-only Transaction Log &nbsp;·&nbsp; **Key actions:** **Start Period Close** (opens the counting round — gated by open stock-moving documents) and **Close Period** (gated by mid-state SR/GRN/CN/SI/SO + completed physical counts)
> **Correction (2026-07-15):** the approval queue, count-variance commit console, stock-policy dashboard, and threshold routing previously documented here were **not backed by source** — none of those screens exist. What remains for this persona in this module is the period-end review/close and ledger verification.

## 1. Role in This Module

The **Inventory Controller** persona owns balance accuracy at period boundaries. In this module that means one concrete flow: drive the month towards a closable state, then run the close. The system enforces the gates server-side (`validatePeriodEnd`, re-checked under a row lock at close time); the Controller's job is working the review checklist down to green. There is no adjustment-approval queue, no variance dashboard, and no `tb_product_location` policy editor in this module's routes — adjustments are self-contained documents in [inventory-adjustment](/en/inventory/inventory-adjustment), and count review lives in [physical-count](/en/inventory/physical-count).

## 2. Entry Point and Primary Flow

**Entry point:** Inventory Management → Period End (`/inventory-management/period-end`).

**Primary flow (close the period, 7 steps):**

1. **Open the Period End page.** The current-period card shows the period code (YYMM), fiscal year/month, start/end dates, a status badge, and an optional note. "Current" is the earliest period with `status ∈ {open, locked}`. Below the card, the history list shows previously closed periods.
2. **Start the counting round.** Click **Start Period Close** on the card and confirm the irreversible-action dialog → `POST /period-ends/start-counting`. If any GRN dated in the period is not `committed`/`voided`, any stock-in / stock-out is not `completed`/`cancelled`/`voided`, or any numbered SR is still `draft`/`in_progress`, the call returns 422 and the **"Finish these documents first"** dialog lists them with links; otherwise the period's `tb_physical_count_period` becomes `counting` and the app navigates to `/inventory-management/period-end/review` (`GET /period-ends/review`). Once the round is open the same button reads **Continue Counting** and just navigates.
3. **Work the document cards.** One card per module — PR, PO, GRN, CN, SR, SI, SO — each showing the period's document count and a Complete/Incomplete badge. Clicking a card opens a dialog listing the documents (linked to their source screens) so the Controller can chase owners. Complete means: PR `approved/completed/voided`; PO `completed/closed/voided`; SR `completed/cancelled/voided`; GRN `committed/voided`; CN `completed/cancelled/voided`; SI/SO `completed/cancelled/voided`. Only SR / GRN / CN / SI / SO feed the close gate — the PR and PO cards are informational.
4. **Work the physical-count section.** One card per required location (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) with counted/total progress; clicking a card opens that location's count — creating it (`POST /physical-counts`) if none exists yet — at `/inventory-management/physical-count/{id}/entry`. Cards stay disabled ("Counting has not started for this period yet.") until step 2 has run. Spot checks are **not** part of this gate.
5. **Close.** When the review payload reports `can_close: true` the **Close Period** button (destructive style, confirm dialog) enables; clicking fires `POST /period-ends`.
6. **The close executes atomically.** Inside one transaction: `FOR UPDATE` lock + re-validation; lot carry-over (`close` rows zeroing every lot whose period `end_at ≤` this period's, `open` rows re-creating them in the auto-provisioned next period under new `{location_code}{YYMM}{seq4}` lots; on average-method tenants also the `tb_inventory_period_snapshot` buckets); `tb_inventory_period.status = closed`; the period's `tb_physical_count_period` rows marked `completed`.
7. **Verify on the ledger.** Filter the Transaction Log for `inventory_doc_type IN ('close','open')` — the close itself is an auditable pair of ledger events.

## 3. Decision Branches

- **A module card is incomplete** — open its dialog, identify the blocking documents, and chase the owning users in the source modules. This module offers no bulk action over them.
- **A card shows zero documents and reads Incomplete** — cosmetic only: `is_complete` is `count > 0 && …`, but since 2026-08-27 the button is driven by the backend's `can_close`, so an empty module no longer blocks the close.
- **`Cannot close period: {total} document(s) are incomplete`** (`PERIOD_END_CLOSE_BLOCKED`, 422) — a blocking document appeared between the review load and the click; refresh and resolve.
- **`Cannot start counting: {total} document(s) in this period are still open`** (`PERIOD_END_START_COUNTING_BLOCKED`, 422) — rendered as the "Finish these documents first" dialog; commit/void the listed GRN / SI / SO / SR first.
- **`Counting cannot be started for this period`** (`PERIOD_END_COUNTING_NOT_ALLOWED`, 409) — on the close: another session won the close race; on the start: the period is no longer `open` or the round is already `completed`. Refresh.
- **Current period shows `locked`** — the lock came from the [system-config/period](/en/inventory/system-config/period) service; this screen still treats it as current and can close it.

## 4. Exit Point / Handoffs

- **Period closed** — the next period is already open (`ensureNextPeriod`); documents dated in it post into it, documents still dated in the closed period are rejected at SI/SO/GRN create/commit. Handoff back to daily operations.
- **Start or close blocked** — handoff to the source-module owners (GRN/CN processors, SI/SO authors, SR approvers, counters) until the gates clear.

## 5. References

- Parent overview: [03-user-flow](/en/inventory/inventory/03-user-flow).
- Sibling: [period-end](/en/inventory/inventory/period-end) — full gate table, error strings, and dev-level process detail.
- Sibling: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_POST_009` / `INV_POST_010` (close/open), `INV_CALC_008` / `INV_CALC_009` (FIFO vs average close), `INV_AUTH_008` (the `period_end.execute` gate).
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-documents-dialog.tsx`, `pe-start-blocked-dialog.tsx`, `pe-history.tsx`, `use-period-end.ts`).
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/`.
- Related: [physical-count](/en/inventory/physical-count) (the count gate), [inventory-adjustment](/en/inventory/inventory-adjustment) (corrections), [system-config/period](/en/inventory/system-config/period) (period definitions and lock).
