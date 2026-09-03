---
title: Purchase Order — User Flow — Procurement Manager
description: Procurement Manager's flow within the purchase-order module — workflow-stage approval and override authority.
published: true
date: 2026-07-29T05:45:00.000Z
tags: purchase-order, user-flow, procurement-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — User Flow — Procurement Manager

> **At a Glance**
> **Persona:** Procurement Manager &nbsp;·&nbsp; **Module:** [purchase-order](/en/inventory/purchase-order) &nbsp;·&nbsp; **Workflow stages:** Approves at whichever stage the assigned workflow gives them (`in_progress → sent` on the final stage per `PO_POST_004`) — approve-and-transmit, send-back (stage resets, `po_status` unchanged, `PO_POST_005`), or reject to `voided` (direct, terminal); soft-delete-in-draft (`PO_AUTH_005`) &nbsp;·&nbsp; **Key permissions:** stage-gated approval (`PO_AUTH_011`); delete-in-draft (`PO_AUTH_005`)
> **What this persona does:** Acts as an approver on whichever workflow stage is configured for this role; holds delete-in-draft authority.

> ⚠️ **Corrected this pass — twice over.** The previous version of this page described a Procurement-Manager-specific "high-value approval gate" triggered by `total_amount` exceeding a tenant threshold or a pricelist-deviation percentage, plus an entire "configurational surface" (rule-tuning workbench for vendor ranking, Convert-to-PO grouping, unit-conversion factors, pricelist tolerance, and the threshold itself), a Manager-only "void from any non-terminal state," and bulk void/close actions. The configurational surface, Manager-exclusive void, pricelist-deviation-percentage routing, and bulk actions were not found in current source: a repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `segregation`, vendor-ranking, and bulk-action code returned nothing relevant; `enum_stage_role` has no deviation-aware member; and the only path to `voided` is the direct `in_progress → voided` reject, available to whichever approver holds the current stage, not reserved to this role.
>
> **The amount-threshold half of that same claim was itself wrongly dismissed by an earlier correction pass** — a follow-up search confirms `total_amount`-based stage routing is real, just not a Procurement-Manager-specific or PO-specific mechanism: it's the generic workflow `routing_rules` (`tb_workflow.data.routing_rules`, configured from the **Routing** tab of `/system-admin/workflow`, shared by PR/PO/SR) evaluated by `evaluateCondition`/`findNextStep` in `workflows.navagation.service.ts` on every submit/approve. See § 1 and the Permission Matrix below for the corrected picture.

## 1. Role in This Module

The **Procurement Manager** engages with the PO module as a **workflow-stage approver** — the same generic mechanism any `stage_role = approve` user uses. When a PO is submitted (`draft → in_progress`), the workflow definition referenced by `tb_purchase_order.workflow_id` determines how many stages exist and who is assigned to each (`user_action.execute[]`); the Procurement Manager is simply whichever user (or role) the tenant's workflow configuration puts on one or more of those stages. At the final stage, approving both authorizes and transmits the PO in the same call (`isFinalApproval = workflow_next_stage === '-'` in `purchase-order.logic.ts`) — `po_status: in_progress → sent`, `approval_date` set (`PO_POST_004`). At any non-final stage, approving only advances `workflow_current_stage` (`po_status` stays `in_progress`). The Manager can also **send back** an in-progress PO — this resets `workflow_current_stage` to an earlier stage (typically back to the creator) without changing `po_status` (`PO_POST_005`) — or **reject** it, which is a direct, terminal `in_progress → voided` transition (no intermediate state, no return to `draft`). Separately, the Manager holds **soft-delete-in-draft** authority (`PO_AUTH_005`), and, along with the Inventory Manager, can **Close** a `sent`/`partial`/`in_progress` PO early (`PO_AUTH_008`, `PO_POST_011`) — writing the remaining open quantity to `cancelled_qty`. **Confirmed, corrected this pass:** the workflow assigned to the PO can carry `routing_rules` that skip or jump stages based on `total_amount` (Σ line `total_price`) — evaluated on every submit/approve, configured generically from the **Routing** tab of `/system-admin/workflow` (shared by PR/PO/SR, not PO- or Manager-specific). No pricelist-deviation-percentage routing field, vendor-ranking configuration, or bulk-action surface was found in current source; treat any such claim elsewhere as unconfirmed design intent rather than live behavior.

### Workflow position (PM approver + override paths)

```mermaid
graph LR
    inprog(("in_progress")):::current -->|"Approve (final stage)"| sent(("sent"))
    inprog -->|"Send-back<br/>(stage resets, status unchanged)"| inprog
    inprog -->|"Reject (direct, terminal)"| voided(("voided"))
    draft(("draft")) -.->|"Soft-delete<br/>(PO_AUTH_005)"| gone[["(removed)"]]
    sent -.->|"Close (PO_AUTH_008)"| closed(("closed"))
    partial(("partial")) -.->|"Close (PO_AUTH_008)"| closed
    classDef current fill:#1a56db,color:#fff,stroke:#1a56db;
```

### Permission Matrix — Action (Procurement Manager)

| Action | Availability |
|---|---|
| View PO | ✅ all statuses |
| Approve at own stage (`in_progress`) | ✅ when assigned via `user_action.execute[]` for the current stage (`PO_AUTH_011`) — authorization itself is not amount-gated, though which stage the cursor reaches can be (workflow `routing_rules`, see § 1) |
| Approve at final stage → transmit (`in_progress → sent`) | ✅ when the current stage is the workflow's final stage (`PO_POST_004`) |
| Send-back (stage resets, `po_status` unchanged) | ✅ when assigned to the current stage (`PO_POST_005`) |
| Reject (`in_progress → voided`, direct, terminal) | ✅ when assigned to the current stage — not exclusive to this role |
| Soft-delete draft (`PO_AUTH_005`) | ✅ |
| Close (`{sent, partial, in_progress} → closed`, `PO_AUTH_008`, `PO_POST_011`) | ✅ shared with Inventory Manager |
| Cancel (`{draft, in_progress, sent} → closed`) | ✅ no confirmed additional role gate |
| Edit header / lines (qty, price, tax, FOC) | ❌ (Purchaser scope, `PO_AUTH_002`) |

## 2. Entry Point and Primary Flow

**Entry point:** In-app notification when a submitted PO's workflow stage cursor lands on a stage this user is assigned to, or Sidebar → **Purchase Order** module → **My Approvals**.

**Primary flow (happy path):**

1. Receive the notification. Authorization to act, once the cursor lands on this user's stage, is purely `user_action.execute[]` membership for that stage — not an amount or deviation check. Which stage the cursor reaches, however, can itself reflect the workflow's `routing_rules` skipping or jumping stages by `total_amount` (§ 1), so a high-value PO may traverse a different stage sequence than a low-value one on the same workflow before this notification fires.
2. Open the **PO detail** page from the approval queue. Review the header (vendor, currency, exchange rate, credit term, order and delivery dates) against `PO_VAL_002`–`PO_VAL_006`. Review the linked PR via the bridge table for PR-sourced POs (`PO_XMOD_001`).
3. Walk the **Items** tab, checking the `is_foc` flag, `cancelled_qty` (should be zero at this stage), and per-line `delivery_date`. Re-validate the calculation roll-up: `total_price`, `total_tax`, `total_amount` per `PO_CALC_008`–`PO_CALC_010`.
4. Review the **Attachments** and **Comments** tabs for the vendor quote, the buyer's justification note, and any prior-stage approver comments. The `history` and `workflow_history` JSON columns surface the full chain of `created → submitted → approved` events.
5. Decide, at the item level then the document level (mirrors the e2e-confirmed flow in `403-po-approver-journey.spec.ts`):
   - **Approve** — marks item(s) Approved, then **Document Approve**. If this is the final stage: `po_status: in_progress → sent` via `PO_POST_004`, `approval_date = now()`, `last_action = approved`, and the vendor-transmit channel fires on the same transition. If not final: `po_status` stays `in_progress`, stage cursor advances.
   - **Send back** — marks item(s) Review, then **Document Send Back** with an optional reason. `workflow_current_stage` resets to an earlier stage; `po_status` stays `in_progress`; `last_action = reviewed`. The reason is appended to `tb_purchase_order_comment`.
   - **Reject** — marks item(s) Reject, then **Document Reject** with an optional reason. `po_status: in_progress → voided`, direct and terminal. `is_active` is not touched by this call.
6. (After approve-and-transmit) confirm the transmission outcome via the activity log, which records the channel and timestamp.
7. (Optional, override path) **Close** a `sent`/`partial`/`in_progress` PO when the vendor cannot supply the outstanding balance (`PO_AUTH_008`, `PO_POST_011`) — writes the remainder to `cancelled_qty`. Recorded in the activity log.

## 3. Decision Branches

- **If the escalated PO is technically valid but commercially questionable**: the Manager reviews the vendor quote in **Attachments** and the Purchaser's justification in **Comments**, then approves, sends back with a comment, or rejects — using the same stage-based mechanism as any approver. No separate "commercial escalation" surface was found.
- **If the vendor cannot fulfil a `sent` or `partial` PO**: the Manager (or Inventory Manager) runs **Close**, writing the remaining open quantity to `cancelled_qty` on each affected line. This lands on `closed`, not `voided` — there is no path from `sent`/`partial` to `voided`.
- **If the Manager soft-deletes a draft PO**: from the draft PO detail page, **Delete Draft** (`PO_AUTH_005`, `PO_POST_012`) sets `deleted_at` / `deleted_by_id`; the row remains in the database for audit, and the same `po_no` is freed for re-use (the unique index includes `deleted_at`).

## 4. Exit Point / Handoffs

The Procurement Manager's involvement on a given PO ends at one of the following handoffs.

- **Final approval → transmit to vendor** — `po_status: in_progress → sent` via `PO_POST_004`. Handoff is to the **Vendor**; document state at handoff is `sent`. See [03-user-flow-vendor.md](./03-user-flow-vendor.md) for the external-side flow.
- **Reject → terminal `voided`** — direct transition, no intermediate state. Handoff is to the **Auditor** for post-hoc review only; document state is `voided` (terminal).
- **Send back → revision by the assigned stage owner** — `workflow_current_stage` resets; `po_status` stays `in_progress` (not `draft`). Handoff is to whoever the earlier stage assigns (commonly the Purchaser). The Manager's involvement resumes if the resubmitted PO reaches this stage again.
- **Close** — `{sent, partial, in_progress} → closed`, remainder written to `cancelled_qty`. Terminal.

Receipt-driven transitions (`sent → partial → completed` via `PO_POST_006`/`PO_POST_007`) are not Procurement Manager actions — they are driven by the **Receiver** through GRN posting.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global PO state machine and cross-persona handoff table.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — upstream persona who submits the PO and who picks up a send-back at the earlier stage.
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — downstream external party that receives the transmitted PO at `po_status = sent`.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator who configures workflow definitions and RBAC bindings; Auditor who reviews the activity log of the Manager's approve / reject / close actions.
- Authorization rules: [02-business-rules.md](./02-business-rules.md) Section 4 — `PO_AUTH_005` (delete-in-draft), `PO_AUTH_007` (reject, corrected), `PO_AUTH_008` (early-close), `PO_AUTH_011` (workflow stage gating).
- Posting rules: [02-business-rules.md](./02-business-rules.md) Section 5 — `PO_POST_004` (final approval and transmit), `PO_POST_005` (send-back, corrected), `PO_POST_010`/`PO_POST_010b` (cancel / reject, corrected), `PO_POST_011` (early-close from partial), `PO_POST_012` (soft-delete in draft).
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — primary carmen/docs source for the PO module business analysis; treat its RBAC/threshold table as historical design intent, not verified current behavior — see [02-business-rules.md](./02-business-rules.md) § 4 note.
- Related: [purchase-request](/en/inventory/purchase-request) — upstream module; PR-to-PO conversion via the bridge table.
- Related: [good-receive-note](/en/inventory/good-receive-note) — downstream fulfilment whose receipt postings the Manager observes; close interacts with GRN state via `PO_XMOD_003`.
