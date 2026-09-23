---
title: Good Receive Note (GRN) — Test Scenarios — Purchaser
description: Purchaser's test cases (happy path, permission, validation, edge cases) for good-receive-note.
published: true
date: '2026-09-22T18:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser (Procurement Officer + Department Manager) &nbsp;·&nbsp; **Module:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; **Scenarios:** ~12
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** maps to `501-grn.spec.ts` in `../carmen-inventory-frontend-e2e/`
> **Re-verified 2026-09-22:** the PO advances at **commit**, not at save; PO statuses are `approved` / `sent_or_print` / `partial` / `completed`; a price-deviation check against the **PO price** now exists at save (`GRN_VAL_007`) — there is still no pricelist check, no `accepted_qty`, no three-way match, and no segregation of duties.

> **Executable coverage:** `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (76 cases; Purchaser-relevant groups listed in §5) and `docs/test-cases/gaps/501-grn-core-gap.md` (62) — permission-denial cases use the Requestor-role fixture.

This page captures the test scenarios that the Purchaser persona (the **Purchaser / Procurement Officer** who raised the upstream PO, plus the **Department Manager** subset) directly drives in the `good-receive-note` module. The Purchaser is a **review-only** participant on the GRN — they do **not** create the GRN at the dock, do **not** save it, and do **not** commit (commit is what posts inventory and advances the PO — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)). "Own PO" scoping below is a working convention — the backend does not filter the GRN list by `buyer_id`.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| PUR-HP-01 | Open a `saved` / `committed` GRN against an own PO in read mode | Purchaser is the `buyer_id` of PO `PO-X` at `po_status ∈ {sent_or_print, partial}`; Receiver has driven a GRN against `PO-X` to `committed` (posted inventory, advanced the PO). | 1. Open the PO module's Receiving History tab for `PO-X` (or the GRN's **Reference documents** list, `GET …/ref`). 2. Click into the GRN row. | The GRN read view opens; header shows `doc_status`, vendor, `grn_date`, currency, exchange rate; line rows show `order_qty` / `order_price`, `received_qty` / `received_price`, `foc_qty`, `expired_at`; the action column shows the source-document link; the Stock Movement tab lists the lots; no edit, save, commit, or void affordance is rendered for a user without the corresponding permission keys. Maps to TC-GRN-010001. |
| PUR-HP-02 | Review a clean receipt — no vendor contact needed | A committed GRN against own PO `PO-X` where every line satisfies `received_qty = order_qty`. | 1. Open the GRN. 2. Compare the line-level ordered / received columns. | No vendor-side action is fired; no PO amendment raised; the GRN document itself is **not** edited; the PO line transitioned at the Receiver's commit (`sent_or_print → completed`). |
| PUR-HP-03 | Review a short receipt and chase the vendor | Committed GRN against own PO `PO-Y` (`order_qty = 10`) with `received_qty = 6`; Receiver wrote a variance comment; `po_status = partial`. | 1. Open the GRN. 2. Confirm `received_qty (6) < order_qty (10)`. 3. Read the Receiver's comment. 4. Contact the vendor outside the GRN document. 5. Write a comment recording the vendor's response. | Vendor chase fires off-document; the GRN itself is unchanged; source PO stays at `po_status = partial` with pending = 4; when the follow-up shipment arrives, the Receiver commits a second GRN which advances `received_qty` to 10 and flips `po_status → completed`. |
| PUR-HP-04 | Price-deviation protection before the document reaches review | Product `price_deviation_limit = 10`; PO line `order_price = ฿100`; Receiver enters `received_price = ฿120`. | 1. Receiver clicks **Save**. | The document never reaches `saved` — `GRN_DEVIATION_LIMIT_EXCEEDED` (`kind = price`) is returned at save, so the Purchaser is not asked to review an over-priced receipt. With `received_price = ฿108` it saves and the Purchaser sees the 8 % variance on the line. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| PUR-PERM-01 | Purchaser opens a GRN in read mode | **Allow** with `procurement.goods_received_note.view` (`GET …/:id`, guard `goodReceivedNote.findOne`). Header, lines, Stock Movement (once committed), attachments, and activity log are visible; edit / save / commit / void buttons are hidden when the user lacks `.update` / `.commit` / `.delete`. Maps to TC-GRN-010001. |
| PUR-PERM-02 | Purchaser attempts to open a GRN whose source PO they do **not** own | **Allowed by the backend** — there is no `buyer_id` scope on `findAll` / `findOne` (re-checked 2026-09-22). A user **without** `procurement.goods_received_note.view` gets `403` from the gateway guard and the list route redirects. Maps to TC-GRN-010003 (permission denial, not ownership). |
| PUR-PERM-03 | Purchaser attempts to modify a GRN header / line | **Deny only by permission key.** Without `.update` the `PATCH …/:id` and detail endpoints return `403`; there is no role-name message and no segregation-of-duties rule — a Purchaser who also holds `.update` can edit a `draft`. Maps to TC-GRN-080005. |
| PUR-PERM-04 | Purchaser attempts to create a GRN | **Deny by permission key** (`goodReceivedNote.create` → `403`); the **New** button is hidden without `.create`. |
| PUR-PERM-05 | Purchaser attempts to save or commit a `saved` GRN | **Deny by permission key** — both `PATCH …/save` and `PATCH …/commit` are behind `goodReceivedNote.commit` (`403` without it). No "Inventory Manager role" message exists. Maps to TC-GRN-110002. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| PUR-VAL-01 | Purchaser without the commit key calls the commit endpoint directly | A `saved` GRN sits against own PO `PO-X`; Purchaser (no `procurement.goods_received_note.commit`) calls `PATCH …/commit`. | **Reject 403** from `AppIdGuard('goodReceivedNote.commit')`; `doc_status` stays `saved`. Maps to TC-GRN-110002. |
| PUR-VAL-02 | Purchaser attempts to edit a line on a `saved` GRN | `saved` GRN with `received_qty = 10`; Purchaser calls `PATCH …/:id/details/:detail_id` (or the detail delete). | **Reject** — `GRN_NON_DRAFT_NO_UPDATE_DETAIL` / `_DELETE_DETAIL` (400) regardless of permission, because detail endpoints are `draft`-only; the correct path is to comment and ask the Receiver to void and re-raise (or, after commit, to raise a credit note). |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| PUR-EDGE-01 | Multi-PO consolidation review — single GRN spanning two of the Purchaser's POs | Same vendor delivers in one truck covering `PO-A` (one line, pending 4) and `PO-B` (two lines, pending 6 each); Receiver consolidates into one GRN with three lines per RCV-EDGE-04 (see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)) and commits. | Opening the GRN renders all three lines; the **Reference documents** list (`GET …/ref`) shows both POs; a short line's variance is scoped to the PO line it sits against. Both POs' `received_qty` advanced in the same commit transaction. Maps to TC-GRN-040002, TC-GRN-040004 (stubs) and gap `501-grn-from-po-gap.md`. |
| PUR-EDGE-02 | Credit note after commit — one product per GRN once | Committed GRN with products P1 and P2; a credit note for P1 already exists. | `GET …/good-received-notes/vendor/:vendor_id/cn` still lists the GRN (P2 un-credited); after P2 is credited too, the GRN drops out of the list (`findFullyCreditedGrnIds`, `good-received-note.service.ts:494-552`); a second credit note for P1 on the same GRN is refused by the credit-note module. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoffs that pivot off the Purchaser.
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — happy-path source for Section 1 above.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — upstream test set that creates, saves, and commits (posts) the GRN.
- Sibling: [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) — correction page: why no credit-note / three-way-match handoff test scenarios exist.
- Business rules being verified: [02-business-rules.md](./02-business-rules.md) — segregation-of-duties (`GRN_AUTH_010`, marked unconfirmed this pass) referenced in PUR-PERM-03, PUR-VAL-01, PUR-VAL-02.
- Cross-link: [purchase-order](/en/inventory/purchase-order) — upstream module owned by this persona; the source of `order_price`, `po_status` (`approved` / `sent_or_print` / `partial` / `completed`), and the activity log.
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (76 cases). Purchaser-relevant groups: **TC-GRN-010001** (View GRN List), **TC-GRN-010003** (Insufficient Permissions), **TC-GRN-080005** (Edit Line Item — denial), **TC-GRN-110002** (No Permission to Commit), **TC-GRN-040002 / 040004** (Create from Multiple POs — stubs; real wizard cases are in `docs/test-cases/gaps/501-grn-from-po-gap.md`).
