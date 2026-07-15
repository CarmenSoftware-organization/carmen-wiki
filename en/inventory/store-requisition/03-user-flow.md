---
title: Store Requisition — User Flow
description: Document lifecycle and persona-specific flow files for store-requisition.
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — User Flow

> **At a Glance**
> **Module:** [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; **Personas:** Requester &nbsp;·&nbsp; Approver &nbsp;·&nbsp; Fulfiller &nbsp;·&nbsp; Receiver &nbsp;·&nbsp; Audit / Config
> **Workflow lifecycle:** Draft → In Progress (approval + fulfilment sub-stages) → Completed (with Cancelled / Voided branches)
> **Drill into per-persona views below for action-level detail**

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `store-requisition` module. A Store Requisition (SR) is the document that records an **internal stock movement between locations** — a header row in `tb_store_requisition` together with one or more `tb_store_requisition_detail` lines. An SR may be a *consumption pull* (`sr_type = issue`, stock leaves inventory and lands as expense on the destination outlet's cost-centre) or an *inventory transfer* (`sr_type = transfer`, stock physically moves between two inventory-holding locations). The SR is the **system of record for internal stock movement**: until it commits, no inventory is decremented at source and no expense / inventory entry is raised at destination; once committed, the source on-hand falls, the destination either receives stock or absorbs cost, and the inventory transactions (with their lot, expiry, and cost-layer data) are written through the linked `tb_inventory_transaction`.

Section 2 below is the **global state machine** — the canonical list of legal transitions across the five values of `enum_doc_status` (`draft`, `in_progress`, `completed`, `cancelled`, `voided`), independent of who acts. Each per-persona file (linked from Section 3) describes that persona's *path through* the state machine — their entry point, the actions available to them, the decision branches they face, and the handoff that ends their involvement. Section 4 then summarises the cross-persona handoffs that stitch the individual paths together. Read this overview first to anchor the lifecycle, then drill into the persona file that matches your role.

A note on workflow stages: unlike GRN where approval and fulfilment are separate header statuses, the SR collapses both phases under the single `in_progress` value. The `workflow_current_stage` field is what distinguishes "awaiting approver" from "awaiting fulfiller" from "awaiting receiver acknowledgement". So the state machine in Section 2 lists only the legal `doc_status` moves; intra-`in_progress` stage advances (approve, send-back, route to fulfiller) are workflow-internal and do not change `doc_status`.

## 2. Document Lifecycle

> ⚠️ **Corrected this pass.** The previous version of this section described `cancelled` as a real, reachable state (requester withdrawal, all-lines-rejected auto-cancel) and `voided` as a separate Inventory-Controller/Sysadmin-only administrative path. Direct reads of `store-requisition.service.ts` show neither is accurate: `cancelled` is never assigned by any current service method, and `voided` is set unconditionally by the same whole-document reject action any current-stage actor can invoke. See [01-data-model.md](./01-data-model.md) §5 item 11 and [02-business-rules.md](./02-business-rules.md) §5 for the full correction.

The SR document status is stored on `tb_store_requisition.doc_status` and constrained to the five values declared in the shared `enum_doc_status`: `draft` (initial editable state, no stock impact, line entry by requester), `in_progress` (submitted and under workflow control; still no stock impact until the final stage), `completed` (single posting event has fired — inventory decremented at source, cost-layer consumed, destination receives stock or an unposted expense, document locked), `cancelled` (enum-defined but not reachable by any current code path), and `voided` (the confirmed destination of a whole-document reject; no inventory impact). The transitions below cover the legal moves between them; everything else is rejected by the workflow engine. Downstream effects (source on-hand decrement, destination on-hand increment for `transfer`) fire on the final workflow-stage advance only — see [02-business-rules.md](./02-business-rules.md) Section 5 for posting rules. GL/journal-entry posting is unconfirmed in current source.

```mermaid
stateDiagram-v2
    [*] --> draft: create (Requester — manual or recipe auto-create)
    draft --> in_progress: submit (Requester — SR_VAL_001-009 pass)
    draft --> [*]: soft-delete (Requester — own draft only)
    in_progress --> in_progress: approve / trim / reject line (whoever holds current stage)
    in_progress --> in_progress: send back for correction (current stage to an earlier stage)
    in_progress --> completed: final stage advance records issued_qty (same generic approve action)
    in_progress --> voided: whole-document reject (whoever holds current stage)
    completed --> [*]
    voided --> [*]

    note right of in_progress
        Approve and "issue" both call the same POST .../approve endpoint;
        the document completes when the resulting workflow_next_stage is '-'.
        Sub-stage tracked via workflow_current_stage, not doc_status.
        No lot-selection UI exists -- lots are FIFO-assigned automatically.
    end note
```

> ℹ️ **Note — intra-`in_progress` stages:** The `in_progress` self-loop covers however many stages the tenant's `tb_workflow` configuration defines, all sharing the same `doc_status`. The actual sub-stage is tracked via `tb_store_requisition.workflow_current_stage`. There is no confirmed distinction in the backend between an "approval" stage and a "fulfilment" stage beyond which `enum_stage_role` tag the current stage carries (`approve` vs `issue`) — both act through the identical `/approve` endpoint.

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Requester | Requester is a member of `department_id`; permitted to act between `from_location_id` and `to_location_id`; `sr_no` assigned per tenant numbering policy. Header may be partially populated; lines may be empty. |
| `(none)` | auto-create from recipe demand | `draft` | System (cross-ref [recipe](/en/inventory/recipe)) | The recipe module computes ingredient quantities for a destination outlet's production / banquet event and posts an SR `draft` for the outlet's requester to review and submit. `info.recipe_id` carries the back-reference. |
| `draft` | edit / save | `draft` | Requester (owner) | Header and line validation rules in [02-business-rules.md](./02-business-rules.md) Section 2 pass at save (warn-only for some) or block on submit; document remains editable. |
| `draft` | submit | `in_progress` | Requester (owner) | All submit-time rules pass (`SR_VAL_001`–`SR_VAL_009`): source / destination locations set and compatible with `sr_type`, source-availability check passes (per tenant config: hard block or soft warn), at least one line with `requested_qty > 0`. Workflow engine routes to first stage and populates `user_action.execute`. |
| `draft` | soft-delete (only confirmed pre-submit withdrawal) | `(deleted)` | Requester (own draft) | Confirmed restricted to `doc_status = draft`; there is no confirmed `in_progress` withdrawal action. |
| `in_progress` | approve / trim / reject line (mix of approve+reject in one call; not mixable with review) | `in_progress` | Whoever is in `user_action.execute` for the current stage | `approved_qty ≤ requested_qty` per `SR_VAL_010`. `workflow_current_stage` advances when all lines at the current stage have been actioned. Segregation-of-duties checks (`requester ≠ approver`, `approver ≠ issuer`) are unconfirmed — no such code was found. |
| `in_progress` | send back (`/review`, whole-call action) | `in_progress` | Whoever is in `user_action.execute` for the current stage | Returns the document to an earlier stage (typically requester) with `review_message`; `doc_status` unchanged. |
| `in_progress` | final stage advance, records `issued_qty` | `completed` | Whoever is in `user_action.execute` for the stage tagged `enum_stage_role.issue` | Same `/approve` endpoint as any other stage; completes when `workflow_next_stage === '-'`. Triggers source on-hand decrement and, for `sr_type = transfer`, destination on-hand increment, via `executeTransferOnComplete`. Lot assignment is automatic FIFO. |
| `in_progress` | whole-document reject | `voided` | Whoever is in `user_action.execute` for the current stage | Not restricted to an "admin" role — the same reject action is available to whoever currently holds the stage. Reason text optional per the reject dialog (maxLength 256, no minimum). No inventory impact (the SR never posted). |
| `completed` | (no further status transition) | `completed` | — | Terminal state. Corrections require a compensating adjustment in `[inventory-adjustment](/en/inventory/inventory-adjustment)`; the SR itself remains locked. No confirmed receiver-acknowledgement or discrepancy-flag action exists against a `completed` SR — see [03-user-flow-receiver.md](./03-user-flow-receiver.md). |
| `voided` | (no further action) | `voided` | — | Terminal state. Retained for audit. |

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the persona role; clicking the link opens the per-persona view. The five-persona grouping collapses the six raw carmen/docs personas (Store Manager, Warehouse Supervisor, Department Head, Finance Manager, Inventory Controller, System Administrator + Auditor) into five operational roles.

- [Requester](./03-user-flow-requester.md) — Outlet Manager who identifies stock needs at the consuming location, creates the SR, adds items with `requested_qty` and required date, attaches supporting notes, submits the document for approval, and tracks status.
- [Approver](./03-user-flow-approver.md) — Department Head who reviews submitted requisitions against operational need and source availability; approves, trims `approved_qty` down from `requested_qty`, rejects lines, or sends it back for correction. Per-line approval signature persisted directly on `tb_store_requisition_detail`.
- [Fulfiller](./03-user-flow-fulfiller.md) — Whoever holds the workflow stage tagged `enum_stage_role.issue` (Store Keeper), who records `issued_qty` per line via the same generic approve action the Approver uses. Lots are FIFO-assigned automatically; there is no lot-selection UI.
- [Receiver](./03-user-flow-receiver.md) — **Corrected this pass: unconfirmed as a distinct persona.** No receiver route, permission key, or discrepancy-flag mechanism was found in current source; see the page for what is and isn't confirmed.
- [Audit / Config](./03-user-flow-audit-config.md) — **Corrected this pass: largely unconfirmed.** The "Inventory Controller / Finance / Sysadmin / Auditor" workspace this page previously described (RBAC console, GL verification, SoD-relaxation thresholds) has no matching route or code; see the page for what is and isn't confirmed.

## 4. Cross-Persona Handoffs

The table below captures the moments where the SR moves from one persona's responsibility to another's. Each handoff is anchored to the document state (and where relevant the `workflow_current_stage`) at the point of transfer.

| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Requester | Submit for approval | Approver | `in_progress` (first stage; `user_action.execute` populated with first-stage users) |
| Approver | Send back for correction | Requester | `in_progress` (workflow routed back to requester stage; per-line `review_message` written) |
| Approver | All lines approved at final approval stage | Fulfiller (next stage's users, same `/approve` mechanism) | `in_progress` (workflow advances; `user_action.execute` populated with users at the next stage) |
| Approver / Fulfiller | Whole-document reject | (terminal — `voided`) | `voided`, not `cancelled` — see the correction note in Section 2. No inventory impact. |
| Fulfiller | Records `issued_qty`, final stage completes | (no confirmed downstream persona) | `completed` (source on-hand decremented; destination on-hand incremented for `transfer` or no destination on-hand change for `issue`; lot data auto-assigned on linked inventory transaction). No confirmed "Receiver" handoff exists — see [03-user-flow-receiver.md](./03-user-flow-receiver.md). |
| Fulfiller | Hits at-issue stock-out and records partial | — | `completed` (with `issued_qty < approved_qty` on one or more lines). No confirmed alerting/notification mechanism specific to this case was found. |
| Recipe (auto-create) | Recipe demand computed for production / banquet | Requester | `draft` (pre-populated by the recipe module; `info.recipe_id` carries back-reference) |

Rows describing a "Receiver" or "Inventory Controller / Sysadmin / Finance" persona acting on the SR after commit were removed this pass — see [03-user-flow-receiver.md](./03-user-flow-receiver.md) and [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) for what was checked and what remains unconfirmed.

## 5. References

- `../carmen/docs/store-requisitions/SR-User-Experience.md` — carmen/docs user-experience source: persona descriptions (Store Manager / Warehouse Supervisor / Department Head / Finance Manager), user journeys (Create / Approve / Process), and the legacy 6-state lifecycle diagram (`Draft → Submitted → UnderReview → Approved → InProcess → Fulfilled → Completed`) — note that diagram is **not** canonical here; this page follows the Prisma five-value `enum_doc_status` (`draft / in_progress / completed / cancelled / voided`).
- `../carmen/docs/store-requisitions/SR-Overview.md` — carmen/docs module overview: purpose, scope, audience, integration points; the Section 2 lifecycle and the Section 4 handoffs are aligned to the Prisma enum, not to the Overview's `In Process / Complete / Reject / Void / Draft` five-state which collapses into the Prisma enum as documented in [01-data-model.md](./01-data-model.md) Section 5 item 1.
- `../carmen/docs/store-requisitions/Store Requisitions.md` — Use cases UC-64 (Approve), UC-65 (Deny), UC-66 (Modify), UC-67 (Monitor), UC-68 (Create and Manage), UC-69 (Approve and Record Stock as Issued); the Requester, Approver, and Fulfiller persona files draw their primary-flow steps from these.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_doc_status`, `enum_sr_type`, and the three-quantity invariant (`requested_qty / approved_qty / issued_qty`) referenced throughout Section 2.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting effects and authorization gates referenced by each row of Section 2.
- Related modules: [inventory](/en/inventory/inventory) (downstream — on commit the source's on-hand falls and the destination's rises for `transfer`; lot, expiry, and cost-layer data live on the linked inventory transaction), [costing](/en/inventory/costing) (source-location FIFO / moving-average feeds the issued unit cost), [recipe](/en/inventory/recipe) (auto-create path for recipe-driven ingredient pulls), [good-receive-note](/en/inventory/good-receive-note) (inter-location transfers may pair an SR-OUT at source with a GRN-IN at destination), [inventory-adjustment](/en/inventory/inventory-adjustment) (post-commit corrections).
