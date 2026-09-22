---
title: Good Receive Note (GRN) — User Flow — Finance
description: Why no three-way-match / AP-posting Finance persona was confirmed for good-receive-note in current source, and what is actually confirmed.
published: true
date: '2026-09-22T18:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, finance, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — User Flow — Finance

> **At a Glance**
> **What this page documents:** why the previously-described "Finance" flow (extra-cost allocation review, three-way match, AP posting, period close) does not match current source, and what is actually confirmed.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page described a Finance Officer / AP Clerk running a three-way match (PO ↔ GRN ↔ vendor invoice), posting an AP-side journal (`Dr GRN Clearing / Cr AP-Trade`), and a Finance Manager performing period-close sign-off with GRN-Clearing aging. None of this was found in current source:
>
> - **Re-checked 2026-09-22.** There is still no vendor-invoice entity, capture screen, AP-posting endpoint, or match algorithm. What changed since 2026-07-15: a **general-ledger module** now exists (`apps/micro-business/src/gl/` — journal vouchers, templates, budgets, periods, posting into `tb_gl_balance`; gateway `application/gl-jv`, `gl-posting`, `gl-reports`). It is **not connected to GRN**: `GlPostingService.post()` (`gl-posting.service.ts:293`) posts a `tb_gl_jv` created by the JV module (`gl-jv.service.ts:214`, source `manual`), template runs (`gl-jv-template.service.ts:786`), or its own reversal / closing paths (`gl-posting.service.ts:571,909,1116`); `enum_gl_jv_source.ap` / `.inventory` have no writer; nothing outside `src/gl/` imports the module (only `app.module.ts` and the tenant seed). The frontend's `routes/accounting` area (JV, AP invoice/payment, AR invoice/receipt) renders **fabricated rows** from `routes/accounting/accounting-documents.ts` (`documentsFor()`) and calls no API.
> - `enum_stage_role` (the workflow-stage-role enum shared with PR / PO / GRN) has no `finance` member.
> - The good-received-note backend module now has five lifecycle operations — `save`, `commit`, `approve`, `reject` (`good-received-note.logic.ts`) and `voidGrnById` (`good-received-note.service.ts`) — none of which touch a journal, ledger, or AP entity.
> - The one **real**, adjacent AP-touching feature in the product is **Credit Note** (`tb_credit_note`, confirmed real Prisma table with a genuine FK back to `tb_good_received_note`) — a document that posts an AP-adjacent debit memo against a prior GRN (since 2026-09-21, one credit per product per GRN). It is a real, separate document type; it is not a three-way match and does not involve vendor-invoice capture. It lives under the `purchase-order` module's pages, not this one.

## What is and is not confirmed

| Claim | Status |
| --- | --- |
| Extra-cost allocation mode tag (`manual` / `by_value` / `by_qty`) stored on `tb_extra_cost` | **Confirmed** — real Prisma enum `enum_allocate_extra_cost_type` (three values only; no `by_weight` / `by_volume`). The frontend offers `by_qty` and `by_value` (`grn-extra-cost-fields.tsx:201-202`). |
| Extra-cost amount actually split across GRN lines and fed into the FIFO / average cost-layer calculation | **Confirmed live since 2026-09-10** (`f8cd9f0d9`). `allocateExtraCost()` (`good-received-note.extra-cost.ts:40-61`) splits `Σ tb_extra_cost_detail.amount` across the lines that put stock on hand — `by_qty` = equal shares, `by_value` = weighted by `received_base_qty + foc_base_qty`, `manual` = nothing — at posting time; the share is added to the line's landed cost and stored per cost layer as `extra_cost_amount` (`20260910130000_add_cost_layer_extra_cost`). There is still no per-line allocation UI and no persisted allocation table. |
| Three-way match (PO ↔ GRN ↔ vendor invoice) | **Not implemented.** No invoice entity, capture screen, or match algorithm found. |
| AP-journal posting (`Dr GRN Clearing / Cr AP-Trade`) | **Not implemented.** The GL module exists but no GRN, inventory-transaction, or period-end code calls it (grep above). |
| `post_type` field distinguishing `ap` / `consignment` / `cash` | **Confirmed as a schema field** (`tb_good_received_note.post_type`); **unconfirmed as behavior** — no conditional logic keyed on it was found anywhere in the backend. |
| Finance Manager period-close sign-off, GRN-Clearing aging report | **Not implemented.** No period-close feature specific to this module was found. |
| Finance Officer as a distinct workflow-stage role | **Not implemented.** `enum_stage_role` has no `finance` value. |

Until an invoicing / AP feature is wired to GRN (the GL module is the likely landing place — watch for a writer of `enum_gl_jv_source.ap` / `.inventory`), do not treat any "three-way match", "AP posting", "GRN Clearing", or "period-close sign-off" claim elsewhere in this module's pages as live behavior. Where [02-business-rules.md](./02-business-rules.md) still lists `GRN_POST_006`–`GRN_POST_009` or `GRN_XMOD_007`, those rule IDs are flagged there as **not implemented** — kept only so that cross-references from other pages continue to resolve to an explanation.

## References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the four-state lifecycle; the posting event is `saved → committed` (average units post stock at save).
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the persona whose commit posts inventory and advances the PO; no downstream handoff to a Finance persona.
- GL module (documented on its own wiki page, not here): `../carmen-turborepo-backend-v2/apps/micro-business/src/gl/`, gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports}/`.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — owns vendor-side resolution for receiving variance; any credit-note negotiation happens off-document.
- Sibling: [02-business-rules.md](./02-business-rules.md) §5 / §6 — the corrected posting-rule table (`GRN_POST_006`–`GRN_POST_009`, `GRN_XMOD_007` marked not implemented).
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — legacy design source for the three-way-match / AP concept; treat as design intent, not verified current behavior.
- Related, confirmed-real document: [purchase-order/credit-note](/en/inventory/purchase-order/credit-note).
