---
title: Good Receive Note (GRN) — User Flow — Finance
description: Why no three-way-match / AP-posting Finance persona was confirmed for good-receive-note in current source, and what is actually confirmed.
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, finance, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — User Flow — Finance

> **At a Glance**
> **What this page documents:** why the previously-described "Finance" flow (extra-cost allocation review, three-way match, AP posting, period close) does not match current source, and what is actually confirmed.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page described a Finance Officer / AP Clerk running a three-way match (PO ↔ GRN ↔ vendor invoice), posting an AP-side journal (`Dr GRN Clearing / Cr AP-Trade`), and a Finance Manager performing period-close sign-off with GRN-Clearing aging. None of this was found in current source:
>
> - A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `journal`, `ledger`, `accounts_payable`, `three-way`, `vendor_invoice`, `VendorInvoice`, and `tb_invoice` returned **zero hits**. There is no vendor-invoice-capture screen, no AP-posting endpoint, and no match algorithm anywhere in the current codebase.
> - `enum_stage_role` (the workflow-stage-role enum shared with PR / PO / GRN) has no `finance` member.
> - The good-received-note backend module (`good-received-note.service.ts`, `good-received-note.logic.ts`) has exactly four lifecycle operations — `save`, `commit`, `reject`, `voidGrnById` — none of which touch a journal, ledger, or AP entity.
> - The one **real**, adjacent AP-touching feature in the product is **Credit Note** (`tb_credit_note`, confirmed real Prisma table with a genuine FK back to `tb_good_received_note`) — a document that posts an AP-adjacent debit memo against a prior GRN. It is a real, separate document type; it is not a three-way match and does not involve vendor-invoice capture. It lives under the `purchase-order` module's pages, not this one.

## What is and is not confirmed

| Claim | Status |
| --- | --- |
| Extra-cost allocation mode tag (`manual` / `by_value` / `by_qty`) stored on `tb_extra_cost` | **Confirmed** — real Prisma enum `enum_allocate_extra_cost_type` (three values only; no `by_weight` / `by_volume`). |
| Extra-cost amount actually split across GRN lines and fed into the FIFO / average cost-layer calculation | **Unconfirmed.** The frontend extra-cost panel (`grn-extra-cost-fields.tsx`) captures one flat amount per extra-cost type with the mode as a label — there is no per-line allocation-breakdown UI. The backend's cost-layer creation code (`inventory-transaction.service.ts`) reads only the detail_item's own `base_net_amount`; no extra-cost term was found in that computation. |
| Three-way match (PO ↔ GRN ↔ vendor invoice) | **Not implemented.** No invoice entity, capture screen, or match algorithm found. |
| AP-journal posting (`Dr GRN Clearing / Cr AP-Trade`) | **Not implemented.** No journal / ledger code found anywhere in the module. |
| `post_type` field distinguishing `ap` / `consignment` / `cash` | **Confirmed as a schema field** (`tb_good_received_note.post_type`); **unconfirmed as behavior** — no conditional logic keyed on it was found anywhere in the backend. |
| Finance Manager period-close sign-off, GRN-Clearing aging report | **Not implemented.** No period-close feature specific to this module was found. |
| Finance Officer as a distinct workflow-stage role | **Not implemented.** `enum_stage_role` has no `finance` value. |

Until an invoicing / AP feature is confirmed to exist (in this repo or a sibling backend service not yet surveyed), do not treat any "three-way match", "AP posting", "GRN Clearing", or "period-close sign-off" claim elsewhere in this module's pages as live behavior. Where [02-business-rules.md](./02-business-rules.md) still lists `GRN_POST_006`–`GRN_POST_009` or `GRN_XMOD_007`, those rule IDs are now flagged there as **not implemented** rather than described as working rules — kept only so that cross-references from other pages continue to resolve to an explanation.

## References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the corrected four-state lifecycle; the posting event is `draft → saved`, not commit.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the persona whose save posts inventory and advances the PO; no confirmed downstream handoff to a Finance persona.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — owns vendor-side resolution for receiving variance; any credit-note negotiation happens off-document.
- Sibling: [02-business-rules.md](./02-business-rules.md) §5 / §6 — the corrected posting-rule table (`GRN_POST_006`–`GRN_POST_009`, `GRN_XMOD_007` marked not implemented).
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — legacy design source for the three-way-match / AP concept; treat as design intent, not verified current behavior.
- Related, confirmed-real document: [purchase-order/credit-note](/en/inventory/purchase-order/credit-note).
