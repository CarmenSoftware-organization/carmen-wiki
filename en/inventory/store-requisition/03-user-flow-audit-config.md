---
title: Store Requisition — User Flow — Audit & Config
description: Inventory Controller, Finance, Sysadmin, and Auditor flow within the store-requisition module — largely unconfirmed persona; documents what is and is not verified in current source.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: store-requisition, user-flow, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — User Flow — Audit & Config

> **At a Glance**
> **Persona:** Inventory Controller + Finance + Sysadmin + Auditor — **largely unconfirmed as distinct SR-module personas in current source** &nbsp;·&nbsp; **Module:** [store-requisition](/en/inventory/store-requisition)
> **What this page documents:** why the previously-described oversight/configuration workspace (variance dashboard, admin-void console, GL-verification queue, RBAC/workflow console, SoD-relaxation thresholds) does not match current source, and what is actually confirmed.

> ⚠️ **Major correction this pass.** The previous version of this page described four sub-roles with dedicated screens: an Inventory Controller variance dashboard and pre-commit admin-void console, a Finance GL-reconciliation queue and closed-period gate, a Sysadmin workflow/RBAC/SoD-relaxation-threshold configuration console, and an Auditor read-only signature-trace tool. A repo-wide check against current source confirmed almost none of it:
> - **No admin-void console.** `store-requisition.service.ts` has no `void`/`admin-void` method at all. The only way `doc_status` reaches `voided` is `StoreRequisitionService.reject()` — the same whole-document reject action available to whoever holds the current workflow stage, not an Inventory-Controller-exclusive path. See [03-user-flow-approver.md](./03-user-flow-approver.md) and [02-business-rules.md](./02-business-rules.md) § 5.
> - **No SR → GL posting.** *Updated 2026-09-22:* a GL core now exists in the backend (`apps/micro-business/src/gl/`, migrations `20260909170000_gl_core_master`, `20260914030000_gl_core_jv_ledger`), but `grep -rn store_requisition apps/micro-business/src/gl/` returns zero hits — nothing in the SR commit path creates a journal, so there is still nothing SR-specific for a "Finance" role to verify or reconcile here.
> - **Closed-period gate — now real, but not a Finance action.** *Updated 2026-09-22:* `logic/sr-date.helper.ts` (2026-09-18) refuses to issue an SR whose `sr_date` is outside an open inventory period (`SR_DATE_OUTSIDE_OPEN_PERIOD`) and asks the actor for a date pattern when today is outside every open period. The gate is enforced on the requester's submit and the issuer's approve call; the period master itself is generic system config ([system-config/period](/en/inventory/system-config/period)), not an SR console.
> - **No RBAC/workflow console or SoD-relaxation config specific to SR.** `tb_workflow` is a real, shared configuration table (also used by PR/PO/GRN), and `enum_stage_role` has no `finance` member. A repo-wide search for `delegat` found nothing anywhere in this module or the workflow orchestrator. **The generic amount-based routing-rule config, however, is real and was wrongly dismissed in an earlier version of this correction:** the workflow's `routing_rules` (configured from the **Routing** tab of `/system-admin/workflow`, shared by PR/PO/SR) can route on `total_amount` — for SR, computed by `sr-workflow.mapper.ts` — evaluated by `evaluateCondition`/`findNextStep` in `workflows.navagation.service.ts`. It is generic system-config, not an SR-specific Sysadmin screen and not an SoD-relaxation mechanism. See `SR_XMOD_008` in [02-business-rules.md](./02-business-rules.md).
> - **No variance-dashboard route or component** was found in `routes/store-operation/store-requisition/`.
> - **No Auditor-specific read-only role or route** was found; any audit trail available is the same `workflow_history` / per-line `history` JSON any user with read access to the SR can already see.
>
> This page is kept (rather than deleted) because the module's persona set names these roles in the landing page's legacy role table and the parent [03-user-flow.md](./03-user-flow.md) cross-persona table. The content below documents the correction rather than repeating the fabricated workspace. See the module progress-log Discrepancy entry for the full source-check trail.

## 1. What Is and Isn't Confirmed

| Claim from the prior version | Status |
|---|---|
| A dedicated "Admin Void" action, restricted to Inventory Controller / System Administrator | **Not implemented as described.** The real mechanism is the whole-document `reject` action, available to whoever holds the current workflow stage; it sets `voided`, not a separately-gated administrative action. |
| Finance GL-reconciliation queue, journal-entry verification | **Not implemented for SR.** The GL module exists but has no SR hook. |
| Closed-period commit block | **Implemented (2026-09-18) as a generic date gate**, not as a Finance screen — see `SR_VAL_014`. |
| Sysadmin RBAC / workflow-config console, approval value-thresholds, SoD-relaxation thresholds | **Split finding.** A dedicated SR-specific console is unconfirmed / not found. But "approval value-thresholds" as a *generic* mechanism is confirmed real, corrected this pass: the workflow's `routing_rules` can route on `total_amount` (`SR_XMOD_008`) via the same generic `/system-admin/workflow` Routing tab PR/PO also use — not an SR-specific screen. SoD-relaxation thresholds remain unconfirmed — no such field was found for SR. |
| Auditor read-only signature-trace tool | **Unconfirmed as a distinct route.** The underlying data (`workflow_history`, per-line `history` JSON, comment threads) is real and readable by any user with SR read access — there is no confirmed Auditor-exclusive screen. |
| Recipe auto-create wiring (`[recipe](/en/inventory/recipe)` → SR draft) | **Plausible but not re-verified this pass** — carried over from an earlier version of this page; the SR side of this (an SR arriving in `draft` with `info.recipe_id` populated) is consistent with the data model, but the recipe-module trigger itself belongs to that module's own resync pass. |
| Period-end reconciliation / signoff as a distinct workflow | **Not implemented in this module** — the open-period gate exists, but reconciliation/sign-off belongs to the period-end module, not SR. |

## 2. What To Do With This Page

Until an admin-void endpoint, an SR-wired GL/journal-posting feature, or an RBAC/workflow-config console specific to this module are confirmed to exist, do not treat any "Inventory Controller admin-voids," "Finance blocks a closed-period commit," "Sysadmin configures SoD-relaxation thresholds," or "Auditor traces signatures" claim elsewhere in this module's pages as live behavior.

The closest existing analogues today are: (a) whoever holds the current workflow stage can reject the whole document (`voided`, not a separate admin path); (b) `tb_workflow` is configurable per tenant, the same generic mechanism PR/PO/GRN use — including real, generic amount-based routing rules (`SR_XMOD_008`), just not an SR-specific console and not an SoD field; (c) `workflow_history` and per-line `history` JSON are readable by anyone with SR access, which is the closest thing to an audit trail. Building dedicated variance-dashboard, GL-verification, or RBAC-console screens would be new functionality, not a documentation gap.

## 3. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global SR state machine; this persona set is listed there as largely unconfirmed.
- Sibling: [03-user-flow-approver.md](./03-user-flow-approver.md) + [03-user-flow-fulfiller.md](./03-user-flow-fulfiller.md) — the real generic `/approve` / `/reject` mechanics any workflow-stage holder (including a tenant-titled "Inventory Controller") would use today.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the discrepancy-escalation target this page's prior version described; itself unconfirmed.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 2 (`SR_VAL_014`, confirmed 2026-09-22), § 4 (`SR_AUTH_009`–`SR_AUTH_013`, corrected), § 5 (`SR_POST_007`, `SR_POST_009`, `SR_POST_010`, `SR_POST_013`, corrected), § 6 (`SR_XMOD_008` — amount-based routing confirmed real this pass; delegation remains unconfirmed).
- `../carmen/docs/store-requisitions/SR-Overview.md` § User Roles → Manager row — legacy design source for the collapsed Inventory Controller / Finance Manager / Sysadmin "Manager" role; treat as design intent, not verified current behavior.
