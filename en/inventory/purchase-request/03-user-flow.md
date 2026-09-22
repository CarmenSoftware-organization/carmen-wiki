---
title: Purchase Request — User Flow
description: Document lifecycle and persona-specific flow files for purchase-request.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-request, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — User Flow

> **At a Glance**
> **Module:** [purchase-request](/en/inventory/purchase-request) &nbsp;·&nbsp; **Personas:** Requestor &nbsp;·&nbsp; Approver &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; Purchaser &nbsp;·&nbsp; Audit / Config
> **Workflow lifecycle:** Draft → In Progress (multi-stage approval, send-back keeps `in_progress`) → Approved → Completed (Voided only via approver Reject; drafts are soft-deleted) &nbsp;·&nbsp; **Re-verified 2026-09-22** against `purchase-request.service.ts` / `logic/purchase-request.logic.ts`
> **Drill into per-persona views below for action-level detail**

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `purchase-request` module. It covers the lifecycle of a single Purchase Request document — a PR header (`tb_purchase_request`) together with one or more PR detail lines (`tb_purchase_request_detail`) — from the moment a Requestor first saves a draft, through the multi-stage approval chain, to either conversion into a purchase order or termination by void / cancellation. The personas involved are the **Requestor** (who originates and revises the PR), the **Approver** chain (every `approve`-role stage the workflow defines — "Department Head", "Budget Controller", "Finance" are illustrative labels; the code has no budget check), the **Purchaser** (who converts the approved PR to a PO), the **Procurement Manager** (oversight and high-value approval), and the **Audit / Config** roles (Auditor for read-only review, System Administrator for workflow configuration). The role catalogue itself is defined in [the module landing](/en/inventory/purchase-request) Section 4.

Section 2 below is the **global state machine** — the canonical list of transitions across `enum_purchase_request_doc_status` values, independent of who acts. Each per-persona file (linked from Section 3) describes that persona's *path through* the state machine — their entry point, the actions available to them, the decision branches they face, and the handoff that ends their involvement. Section 4 then summarises the cross-persona handoffs that stitch the individual paths together. Read this overview first to anchor the lifecycle, then drill into the persona file that matches your role.

## 2. Document Lifecycle

The PR document status is stored on `tb_purchase_request.pr_status` and constrained to the values declared in `enum_purchase_request_doc_status`: `draft`, `in_progress`, `voided`, `approved`, `completed`. The transitions below cover the legal moves between them; everything else is rejected by the workflow engine.

```mermaid
stateDiagram-v2
    [*] --> draft: create (Requestor)
    draft --> draft: save / edit (Requestor)
    draft --> in_progress: submit (Requestor)
    draft --> [*]: delete — soft delete, not a status (Requestor / super-admin)
    in_progress --> in_progress: approve intermediate stage
    in_progress --> in_progress: routing rule skips / jumps a stage (threshold)
    in_progress --> in_progress: send-back (review) — stage cursor moves back
    in_progress --> approved: approve final stage
    in_progress --> voided: reject (any approver)
    approved --> completed: convert to PO (Purchaser)
    voided --> [*]
    completed --> [*]
```

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Requestor | Header fields validated (`requestor_id`, `department_id`, `pr_date`, `workflow_id`); no lines required yet. |
| `draft` | save (edit) | `draft` | Requestor (owner) | PR still owned by the requestor; no workflow stage advanced. |
| `draft` | submit | `in_progress` | Requestor (owner) | `workflow_id`, `requestor_id`, `department_id`, `pr_date` present; at least one line (`PR_VAL_006`); every line buys or receives FOC (`PR_VAL_008`); `POST …/verify` (`verify_state = submit`) lists every failing rule beforehand (`PR_VAL_017`). |
| `draft` | delete | *(row soft-deleted)* | Requestor (owner: `created_by_id` or `requestor_id`) or platform super-admin | `pr_status` must be `draft`; header and lines get `deleted_at` (`PR_VAL_018` / `PR_POST_009`). **Not** a transition to `voided` — earlier revisions were wrong. |
| `in_progress` | approve (this stage, not final) | `in_progress` | Current-stage approver | Approver is assigned to the current `workflow_current_stage` with `stage_role = approve`; `last_action` becomes `approved` and the stage cursor advances. |
| `in_progress` | approve (final stage) | `approved` | Final-stage approver | Approver is assigned to the final approval stage; all prior stages have signed off (`purchase-request.service.ts:1913`). |
| `in_progress` | send-back (review) | `in_progress` | Any approver on the chain | Reason and target stage required; `workflow_current_stage` moves to the target, `last_action = reviewed`, `pr_status` is rewritten as `in_progress` (`purchase-request.service.ts:2052`) — the PR never returns to `draft`. Audit comment written. |
| `in_progress` | reject | `voided` | Any approver on the chain | Reason text required; workflow terminates with no further actions allowed (`purchase-request.service.ts:2201` — the only writer of `voided`). |
| `in_progress` | routing rule (threshold) | `in_progress` | Workflow engine | A `tb_workflow.data.routing_rules` condition on `total_amount` / `department` matches on submit or approve; the engine skips or jumps to the named stage (`PR_AUTH_005`). State unchanged but stage cursor jumps. |
| `approved` | convert to PO | `completed` | Purchaser (no permission enforced on the dialog) | All approved lines bridged into one or more `tb_purchase_order` records; the PR is closed against further conversion. |

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the persona role; clicking the link opens the per-persona view.

- [Requestor](./03-user-flow-requestor.md) — Creates and submits PRs, responds to send-backs, cancels own drafts.
- [Approver](./03-user-flow-approver.md) — Every `approve`-role stage of the chain (illustrated as Department Head → Budget Controller → Finance), with approve / send-back / reject / split actions per stage.
- [Purchaser](./03-user-flow-purchaser.md) — Picks up approved PRs, validates vendor allocation and pricing, and converts them to purchase orders.
- [Procurement Manager](./03-user-flow-procurement-manager.md) — Oversees the procurement function, approves high-value or escalated PRs, tunes vendor ranking and Allocate Vendor rules.
- [Audit / Config](./03-user-flow-audit-config.md) — Auditor (read-only review of PRs and activity log) and System Administrator (workflow stage configuration, amount-threshold routing rules; delegation rules and an administrative void are unconfirmed — no matching mechanism or endpoint found, see `PR_AUTH_006` / `PR_AUTH_007`).

## 4. Cross-Persona Handoffs

The table below captures the moments where the PR moves from one persona's responsibility to another's. Each handoff is anchored to the document state at the point of transfer.

| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Requestor | Submit | First-stage approver (typically Department Head) | `in_progress` (stage cursor on first approval stage) |
| Approver (stage N, not final) | Approve at this stage | Approver (stage N+1) | `in_progress` (stage cursor advances to next stage) |
| Approver (final stage) | Approve at final stage | Purchaser | `approved` |
| Approver (any stage) | Send-back with reason (target = create stage) | Requestor | `in_progress` at the `create` stage (revision history and approver comment retained; `pr_status` does **not** return to `draft`) |
| Workflow engine | Routing rule on `total_amount` / `department` matches | Target stage (e.g. Procurement Manager) | `in_progress` (stage cursor jumps to the rule's target stage) |
| Purchaser | Convert to PO | Purchase Order module (and indirectly Receiver / GRN downstream) | `completed` (one or more `tb_purchase_order` records generated, linked back to the PR) |
| Approver | Reject with reason | Auditor (post-hoc review only) | `voided` |

## 5. References

- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — primary source for the user-experience flows (creation, approval, vendor comparison, template usage).
- `../carmen/docs/purchase-request-management/PR-Overview.md` — module overview, user roles, integration points.
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — product requirements driving the flows.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_purchase_request_doc_status` values used in Section 2 above.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation, authorization, and posting rules referenced by each transition.
