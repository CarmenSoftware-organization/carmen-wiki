---
title: Store Requisition — User Flow — Audit & Config
description: Inventory Controller, Finance, Sysadmin, and Auditor flow within the store-requisition module — largely unconfirmed persona; documents what is and is not verified in current source.
published: true
date: 2026-07-15T12:00:00.000Z
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
> - **No GL/journal-entry code at all.** A repo-wide search of `carmen-turborepo-backend-v2` for `journal` / `ledger` against this module and its `inventory-transaction` dependency returned zero hits. There is nothing for a "Finance" role to verify or reconcile.
> - **No closed-period gate.** A search for `period` in `store-requisition.service.ts`, `store-requisition.logic.ts`, and the SR DTOs returned zero hits. The inventory-transaction layer resolves a current period only to *stamp* `at_period` on the transaction row (for lot-sequencing) — it does not block anything.
> - **No RBAC/workflow console, threshold editor, or SoD-relaxation config specific to SR.** `tb_workflow` is a real, shared configuration table (also used by PR/PO/GRN), but no `threshold` or `delegat` hits were found anywhere in this module or the workflow orchestrator, and `enum_stage_role` has no `finance` member.
> - **No variance-dashboard route or component** was found in `routes/store-operation/store-requisition/`.
> - **No Auditor-specific read-only role or route** was found; any audit trail available is the same `workflow_history` / per-line `history` JSON any user with read access to the SR can already see.
>
> This page is kept (rather than deleted) because the module's persona set names these roles in the landing page's legacy role table and the parent [03-user-flow.md](./03-user-flow.md) cross-persona table. The content below documents the correction rather than repeating the fabricated workspace. See the module progress-log Discrepancy entry for the full source-check trail.

## 1. What Is and Isn't Confirmed

| Claim from the prior version | Status |
|---|---|
| A dedicated "Admin Void" action, restricted to Inventory Controller / System Administrator | **Not implemented as described.** The real mechanism is the whole-document `reject` action, available to whoever holds the current workflow stage; it sets `voided`, not a separately-gated administrative action. |
| Finance GL-reconciliation queue, journal-entry verification, closed-period commit block | **Not implemented.** No journal/ledger code and no period-closed check exist anywhere in this module. |
| Sysadmin RBAC / workflow-config console, approval value-thresholds, SoD-relaxation thresholds | **Unconfirmed / not found.** `tb_workflow` configuration is real and shared across modules, but no threshold or SoD-relaxation fields were found for SR specifically. |
| Auditor read-only signature-trace tool | **Unconfirmed as a distinct route.** The underlying data (`workflow_history`, per-line `history` JSON, comment threads) is real and readable by any user with SR read access — there is no confirmed Auditor-exclusive screen. |
| Recipe auto-create wiring (`[recipe](/en/inventory/recipe)` → SR draft) | **Plausible but not re-verified this pass** — carried over from an earlier version of this page; the SR side of this (an SR arriving in `draft` with `info.recipe_id` populated) is consistent with the data model, but the recipe-module trigger itself belongs to that module's own resync pass. |
| Period-end reconciliation / signoff as a distinct workflow | **Not implemented** — depends on the non-existent closed-period gate and journal-entry feature above. |

## 2. What To Do With This Page

Until an admin-void endpoint, a GL/journal-posting feature, a period-close gate, or an RBAC/workflow-config console specific to this module are confirmed to exist, do not treat any "Inventory Controller admin-voids," "Finance blocks a closed-period commit," "Sysadmin configures SoD-relaxation thresholds," or "Auditor traces signatures" claim elsewhere in this module's pages as live behavior.

The closest existing analogues today are: (a) whoever holds the current workflow stage can reject the whole document (`voided`, not a separate admin path); (b) `tb_workflow` is configurable per tenant, the same generic mechanism PR/PO/GRN use, with no confirmed SR-specific threshold or SoD fields; (c) `workflow_history` and per-line `history` JSON are readable by anyone with SR access, which is the closest thing to an audit trail. Building dedicated variance-dashboard, GL-verification, or RBAC-console screens would be new functionality, not a documentation gap.

## 3. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global SR state machine; this persona set is listed there as largely unconfirmed.
- Sibling: [03-user-flow-approver.md](./03-user-flow-approver.md) + [03-user-flow-fulfiller.md](./03-user-flow-fulfiller.md) — the real generic `/approve` / `/reject` mechanics any workflow-stage holder (including a tenant-titled "Inventory Controller") would use today.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the discrepancy-escalation target this page's prior version described; itself unconfirmed.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 2 (`SR_VAL_014`, marked unconfirmed), § 4 (`SR_AUTH_009`–`SR_AUTH_013`, corrected), § 5 (`SR_POST_007`, `SR_POST_009`, `SR_POST_010`, `SR_POST_013`, corrected), § 6 (`SR_XMOD_008`, marked unconfirmed).
- `../carmen/docs/store-requisitions/SR-Overview.md` § User Roles → Manager row — legacy design source for the collapsed Inventory Controller / Finance Manager / Sysadmin "Manager" role; treat as design intent, not verified current behavior.
