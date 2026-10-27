---
title: Purchase Order — User Flow — Finance
description: Finance's flow within the purchase-order module — unconfirmed persona; documents what is and is not verified in current source.
published: true
date: '2026-10-27T00:00:00.000Z'
tags: purchase-order, user-flow, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — User Flow — Finance

> **At a Glance**
> **Persona:** Finance — **unconfirmed as a distinct persona in current source** &nbsp;·&nbsp; **Module:** [purchase-order](/en/inventory/purchase-order)
> **What this page documents:** why the previously-described "Finance" flow (pre-transmission sign-off + three-way match + AP posting) does not match current source, and what is actually confirmed.

> ⚠️ **Major correction this pass.** The previous version of this page described a **Finance Manager** pre-transmission review stage and a **Finance Officer / AP** persona running a three-way match (PO ↔ GRN ↔ vendor invoice) with GL account postings, purchase-price-variance handling, and FX-adjustment entries. None of this was found in current source:
> - A repo-wide search of `carmen-turborepo-backend` and `carmen-frontend` for `three-way`, `threeWay`, `vendor_invoice`, `VendorInvoice`, and `tb_invoice` returned **zero hits**. There is no vendor-invoice-capture screen, no AP-posting endpoint, and no match algorithm anywhere in the current codebase.
> - `enum_stage_role` (`create`, `approve`, `purchase`, `issue`, `view_only`) has no `finance`-specific member — a "Finance stage" would just be a generic `approve` stage assigned to a Finance-titled user, same as any other approver.
> - The one piece of corroborating evidence for a Finance-adjacent actor is the e2e fixture user `fc@blueledgers.com`, which `04-test-scenarios.md` documents as the **Procurement Manager (FC Approver)** persona — i.e. current test fixtures treat "FC" and "Procurement Manager" as the same approval-stage actor, not as a separate Finance persona.
> - The one **real**, adjacent AP-touching feature in this module is [Credit Note](/en/inventory/purchase-order/credit-note) — a genuine, implemented document (`tb_credit_note`, real Prisma line numbers, real routes) that offsets a prior GRN and reverses / revalues its inventory cost layer. **It does not post an AP debit memo** — re-verified 2026-09-22: no AP or GL write exists anywhere in `credit-note.service.ts` / `credit-note.logic.ts` (a prior version of this bullet said it did). It is not a three-way match and does not involve vendor-invoice capture.
> - Re-checked 2026-09-22 against source HEAD: still zero hits for `three-way`, `vendor_invoice`, `tb_invoice` in both repos. The only new finance-adjacent code since the baseline is the GL core-master work (`tb_gl_jv_*`, `tb_chart_of_accounts`, budget / JV templates, 2026-08 → 2026-09), which has **no** hook from the PO module — no PO status transition writes a journal.
>
> **Re-checked 2026-10-27 (backend `c9d788829`, frontend `391062b5`).** The "zero hits" statements above were true on 2026-09-22 and are no longer: an **AP module** landed on 2026-09-23 (`6ba8f2b8b`) — backend `apps/micro-business/src/ap/` (`ap-invoice`, `ap-payment`), gateway `api/:bu_code/ap-invoice` and `ap-payment`, tenant tables `tb_ap_invoice*` with `doc_type ∈ {invoice, debit_note, credit_note, deposit}`, SPA screens `routes/accounting/accounts-payable`. What it does and does not do for the PO module:
> - AP invoices are built from **committed, AP-posted GRN items** (`GET ap-invoice/grn-candidates`, `POST ap-invoice/from-grn`); each source row carries `matched_qty`, checked against the GRN's received quantity and against other live invoices (`ap-invoice.posting.ts`). Nothing under `src/ap` references a purchase order or a price tolerance, so **PO ↔ invoice and PO ↔ GRN ↔ invoice three-way match remain unimplemented**.
> - The AP `credit_note` is an AP document type (running code `AP-CN`, `ap-invoice.running-code.ts`) that an invoice can reference (`reference-candidates`); it is **not** linked to the procurement [Credit Note](/en/inventory/purchase-order/credit-note) (`tb_credit_note`), which no AP or GL code reads.
> - The SPA's AP screens run on `createApMockRepository` (`use-accounts-payable.ts`); the "3-Way Matching Verification" panel in `ap-invoice-detail.tsx` is a demo with a hard-coded GRN number (`GRN-2026-0815`), not a live match.
> - The PO module still has no hook into AP or GL: no PO status transition writes a journal or an AP row.
>
> This page is kept (rather than deleted) because the module's persona set names Finance in the landing page's legacy role table; the content below documents the correction rather than repeating the fabricated flow. See the module progress-log Discrepancy entry for the full source-check trail.

## 1. What Is and Isn't Confirmed

| Claim from the prior version | Status |
|---|---|
| A distinct "Finance Manager" pre-transmission review workflow stage | **Unconfirmed.** No `finance` stage role exists; any user can be assigned to any generic `approve` stage by workflow configuration, so a tenant *could* name an approver "Finance Manager," but no dedicated code path treats Finance differently from any other approver. |
| Three-way match (PO ↔ GRN ↔ vendor invoice) | **Not implemented.** No invoice entity, capture screen, or match algorithm found. |
| AP liability posting / GL account entries (GRN-accrual, AP-Trade, VAT-input) | **Not from the PO.** An AP module now exists (see the 2026-10-27 re-check above) and posts from AP invoices built on GRN items; no PO transition posts to AP or GL. |
| Purchase-price-variance (PPV) and FX-adjustment postings on invoice match | **Not implemented** — depends on the non-existent invoice/match feature. |
| `PO_AUTH_009` (read-only report access) | Plausible as a generic RBAC read grant, but no Finance-specific permission key was confirmed. |
| Credit Note as an AP-adjacent, post-receipt correction document | **Confirmed real** (inventory-side only; no AP posting) — see [Credit Note](/en/inventory/purchase-order/credit-note). |
| PO `approved` status as a "Finance sign-off" state | **Not that.** `approved` (new 2026-09-14) is simply the terminal outcome of whatever workflow stages the tenant configured; it exists to separate "workflow finished" from "vendor has the document" (`sent_or_print`), not to insert a Finance step. |

## 2. What To Do With This Page

Until PO-level matching is confirmed to exist (the AP module matches GRN items only), do not treat any "three-way match," "AP posting," or "Finance Manager sign-off" claim elsewhere in this module's pages as live behavior. Where those pages still reference `PO_POST_008` / `PO_POST_009` (three-way match) or `PO_XMOD_007` (AP/three-way match), [02-business-rules.md](./02-business-rules.md) § 5 / § 6 now flag those rule IDs as not implemented rather than describing them as working rules.

If Finance involvement in the PO module is a near-term product requirement, the closest existing analogue is: (a) assign a Finance-titled user to a generic `approve` workflow stage (same mechanism the Procurement Manager uses), and (b) use [Credit Note](/en/inventory/purchase-order/credit-note) for post-receipt AP corrections. Matching an invoice against the PO's price or quantity would be new functionality on top of the GRN-based AP module, not a documentation gap.

## 3. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global PO state machine; Finance is listed there as unconfirmed.
- Sibling: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md) — the real generic approve-stage mechanism that any Finance-titled approver would use today.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — GRN posting is the actual event that drives PO receipt status; the only downstream consumer is the AP module's GRN-candidate list, not an invoice-matching event on the PO.
- [Credit Note](/en/inventory/purchase-order/credit-note) — the one real, implemented AP-adjacent document in this module.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 5 (`PO_POST_008` / `PO_POST_009`, marked not implemented), § 6 (`PO_XMOD_007`, marked not implemented).
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — legacy design source for the three-way-match concept; treat as design intent, not verified current behavior.
