---
title: Store Requisition — User Flow — Receiver
description: Receiver's flow within the store-requisition module — unconfirmed persona; documents what is and is not verified in current source.
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, user-flow, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — User Flow — Receiver

> **At a Glance**
> **Persona:** Receiver — **unconfirmed as a distinct persona in current source** &nbsp;·&nbsp; **Module:** [store-requisition](/en/inventory/store-requisition)
> **What this page documents:** why the previously-described "Receiver" flow (physical-receipt acknowledgement + discrepancy escalation) does not match current source, and what is actually confirmed.

> ⚠️ **Major correction this pass.** The previous version of this page described a destination-outlet Receiver persona that acknowledges physical receipt against `issued_qty` and lot data, raises formal "discrepancy" events that escalate to an Inventory Controller, and hands off resolution to `inventory-adjustment`. None of this was found in current source:
> - A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `receiver`, `discrepancy`, and a destination-acknowledgement route/component returned **zero hits** anywhere in the `store-requisition` module. There is no receiver-facing screen, no discrepancy comment-type, and no escalation event.
> - `enum_stage_role` (`create`, `approve`, `purchase`, `issue`, `view_only`) has no `receiver` member, and the SR frontend (`routes/store-operation/store-requisition/`) has no route or component named or shaped like a receiver acknowledgement screen.
> - The comment tables this page previously cited as the Receiver's write surface (`tb_store_requisition_comment`, `tb_store_requisition_detail_comment`) are **generic** — any user with read access to the SR can append a `user`-type comment via `store-requisition-comments.controller.ts` / `store-requisition-detail-comments.controller.ts`. There is no `discrepancy` sub-type, no destination-only write restriction, and no automatic escalation to any other role.
> - The SR document has no `completed → <anything>` transition at all once `completed` is reached (confirmed in `store-requisition.service.ts`) — so even a generic comment cannot move the document; that part of the prior description ("does not change `doc_status`") happened to be accidentally correct, but for the wrong reason (there is no receiver action to not-change status from, because no receiver action exists).
>
> This page is kept (rather than deleted) because the module's persona set names Receiver in the landing page's legacy role table and the parent [03-user-flow.md](./03-user-flow.md) cross-persona table. The content below documents the correction rather than repeating the fabricated flow. See the module progress-log Discrepancy entry for the full source-check trail.

## 1. What Is and Isn't Confirmed

| Claim from the prior version | Status |
|---|---|
| A destination-outlet "Receiver" persona distinct from Requester/Approver/Fulfiller | **Unconfirmed.** No route, component, or `enum_stage_role` member found. |
| Acknowledgement of physical receipt against `issued_qty` and lot data | **Not implemented.** No receiver-facing screen exists in `routes/store-operation/store-requisition/`. |
| A "discrepancy" comment type / flag distinct from an ordinary comment | **Not implemented.** `tb_store_requisition_comment.type` / `tb_store_requisition_detail_comment.type` is the generic shared `enum_comment_type` (`user` / `system`) — no discrepancy-specific value or field exists. |
| Escalation of a discrepancy to an "Inventory Controller" queue | **Not implemented.** No escalation route, notification type, or queue was found. |
| Any user with read access can append a free-text comment on a `completed` SR | **Confirmed real** — via the generic comment endpoints, available to any persona, not receiver-exclusive. |
| Paired SR + GRN pattern for inter-warehouse transfers, with the GRN side handling formal destination receipt | **Not independently re-verified this pass** — carried over from an earlier version of this page; treat as unconfirmed until the [good-receive-note](/en/inventory/good-receive-note) module's own resync pass checks it against SR specifically. |

## 2. What To Do With This Page

Until a receiver-facing acknowledgement or discrepancy-flagging feature is confirmed to exist, do not treat any "Receiver acknowledges receipt," "discrepancy flag," or "escalates to Inventory Controller" claim elsewhere in this module's pages as live behavior. The closest existing analogue today is: any user with read access to a `completed` SR can leave a free-text comment via the generic comment tables — there is no dedicated screen, no required field set, and no automatic routing.

If a formal receipt-acknowledgement feature for SR is a near-term product requirement, building it would be new functionality, not a documentation gap.

## 3. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global SR state machine; Receiver is listed there as unconfirmed, and the cross-persona handoff table no longer asserts a Fulfiller → Receiver handoff.
- Sibling: [03-user-flow-fulfiller.md](./03-user-flow-fulfiller.md) — the final workflow-stage advance is the last confirmed action on the document; nothing downstream of it was found in code.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — the "Inventory Controller" this page's prior version described as the discrepancy-resolution actor is itself unconfirmed as a distinct role — see that page's correction.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 4 (`SR_AUTH_008`, marked unconfirmed), § 5 (`SR_POST_013`, marked unconfirmed).
- `../carmen/docs/store-requisitions/SR-Overview.md` § User Roles → Receiver row — legacy design source for the receiver concept; treat as design intent, not verified current behavior.
