---
title: Purchase Request — Test Scenarios — Audit & Config
description: Why no dedicated audit-workspace or PR-specific configuration test scenarios exist for purchase-request in current source, and what is confirmed instead.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-request, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor + System Administrator) — **no dedicated audit-workspace or PR-specific configuration workbench confirmed in current source** &nbsp;·&nbsp; **Module:** [purchase-request](/en/inventory/purchase-request)
> **E2E coverage:** none confirmed for a dedicated workspace; the generic `/system-admin/activity-log` read path is exercised incidentally by other personas' specs, not by a dedicated audit-config journey spec.

> **Executable coverage (2026-09-22).** No PR audit / config spec, gap report or story exists in `../carmen-inventory-frontend-e2e/`; workflow configuration is covered by `docs/test-cases/1103-workflow.md` and activity log by `docs/test-cases/1109-activity-log.md` (system-config catalogue pages, outside this module). The one PR-state-changing action previously attributed to this persona — an administrative **void** — was re-checked this pass and **does not exist** (no route in `purchase-requests.controller.ts`; `voided` is written only by Reject). What a platform super-admin *can* do is delete another user's `draft` (`PR_VAL_018`).

> ⚠️ **Major correction this pass.** The previous version of this page listed roughly thirty scenarios (`AUD-HP-01` through `AUD-EDGE-06`) covering a "PR Activity Queries" audit workspace (query templates, drill-down trail, export-approval workflow, case-file flagging) and a PR-specific "Configuration workspace" (workflow-threshold editor with `effective_from` versioning, PR Type Defaults, Delegation Rules, Tax Codes, Currency Rates). This was settled against current source in `.specs/resync-2026-07-15-progress.md` (commit `df8ab13`) after reading every route in `router.tsx` and every screen component under `routes/system-admin/` and `routes/config/` — no PR-specific audit or configuration surface exists. See [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) for the full correction, the exact screen-by-screen mapping, and the searches run. This is the same pattern independently found and corrected in the `purchase-order` module — see [purchase-order/04-test-scenarios-audit-config.md](/en/inventory/purchase-order/04-test-scenarios-audit-config).

## What Was Removed and Why

| Removed scenario group | Reason |
|---|---|
| `AUD-HP-01` – `AUD-HP-04` (Auditor query-workspace, drill-down trail, export-approval, case-file flagging) | No "Audit workspace," "PR Activity Queries" route, or PR-scoped drill-down page found anywhere in `carmen-inventory-frontend-react`. |
| `AUD-HP-05` – `AUD-HP-09` (Sysadmin workflow-threshold, delegation, PR-type-default, tax/currency-master config with preview panels and `effective_from` versioning) | No PR-specific configuration workbench found. Workflow-stage and RBAC configuration are generic system-config screens (`/system-admin/workflow`, `/system-admin/user`, `/system-admin/role`); tax and currency configuration are generic master-data screens (`/config/tax-profile`, `/config/currency`, `/config/exchange-rate`) — none PR-specific, and none has a preview/forecast panel or `effective_from` versioning. **Correction (2026-07-29):** amount-threshold routing is *not* absent — the `/system-admin/workflow` screen's **Routing** tab is a real, generic, live mechanism (`tb_workflow.data.routing_rules`, evaluated by the workflow orchestrator on submit/approve); it just has no preview panel and no `effective_from` versioning. Delegation windows remain **no equivalent anywhere** in current source, generic or PR-specific. |
| `AUD-PERM-01` – `AUD-PERM-07`, `AUD-VAL-01` – `AUD-VAL-08`, `AUD-EDGE-01` – `AUD-EDGE-06` | All depend on the non-existent workspaces and configuration surfaces above. |

## What Is Confirmed Instead

- The generic **`/system-admin/activity-log`** screen lists `action` / `entity_type` / `user` events across all document types, filterable but not query-template-driven; a `purchase_request`-scoped filter is the closest equivalent to "PR Activity Queries." Any user with read access to a PR can also see its `tb_purchase_request_comment` history directly on the PR detail page (`type = system` rows immutable per `PR_POST_008`). Whether a distinct Auditor role gates either surface differently from any other reader was not confirmed.
- Workflow-stage definitions (`stage_role`, `user_action.execute[]`), tax rates, currency and exchange-rate masters, and RBAC user/role assignments are each configured through their own generic screen — `/system-admin/workflow`, `/config/tax-profile`, `/config/currency` + `/config/exchange-rate`, `/system-admin/user` + `/system-admin/role` — shared across PR, PO, GRN, and other document types, not through a PR-specific screen.
- **Correction (2026-09-22):** the previous revision called the System Administrator's elevated **void** (`PR_AUTH_007`) "the one confirmed PR-state-changing action" of this persona axis. It is not confirmed: `purchase-requests.controller.ts` exposes no void route, the PR form has no Void control, and `enum_purchase_request_doc_status.voided` is written only by the approver Reject path (`purchase-request.service.ts:2201`). The only super-admin-specific PR action is bypassing the ownership rule when **deleting a `draft`** (`isSuperAdmin` check in `purchase-request.service.ts:1677-1682`, `PR_VAL_018`), which soft-deletes the row without touching `pr_status`. `APP-VAL-10` and `REQ-PERM-06` in the sibling pages were corrected accordingly.
- A first-pass repo-wide search for the literal words `threshold` and `delegat` in both the frontend and backend found no matches for either mechanism. A follow-up pass (2026-07-29) searching for the actual implementation terms (`routing_rules`, `total_amount`, the `WfRouting` admin component, `evaluateCondition` in the workflow orchestrator) found that amount-threshold routing **is** real and live — `PR_AUTH_005` in [02-business-rules.md](./02-business-rules.md) is confirmed. Approval-delegation, by contrast, was not found by either search — `PR_AUTH_006` remains unconfirmed design intent. Both business-rules entries, and every other page in this module citing them, were corrected in the same follow-up pass.

## References

- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — the full correction, including the exact screens read and the searches run.
- Sibling: [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) — `APP-VAL-10` now uses a peer Reject (not an administrative void) as its precondition.
- Related (generic config, not PR-specific): [system-config/workflow](/en/inventory/system-config/workflow).
- Cross-link: [purchase-order/04-test-scenarios-audit-config.md](/en/inventory/purchase-order/04-test-scenarios-audit-config) — sibling module's identical correction, with the full list of searches run.
