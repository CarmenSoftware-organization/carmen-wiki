---
title: Purchase Request — Test Scenarios — Audit & Config
description: Why no dedicated audit-workspace or PR-specific configuration test scenarios exist for purchase-request in current source, and what is confirmed instead.
published: true
date: 2026-07-29T04:45:21.000Z
tags: purchase-request, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor + System Administrator) — **no dedicated audit-workspace or PR-specific configuration workbench confirmed in current source** &nbsp;·&nbsp; **Module:** [purchase-request](/en/inventory/purchase-request)
> **E2E coverage:** none confirmed for a dedicated workspace; the generic `/system-admin/activity-log` read path is exercised incidentally by other personas' specs, not by a dedicated audit-config journey spec.

> ⚠️ **Major correction this pass.** The previous version of this page listed roughly thirty scenarios (`AUD-HP-01` through `AUD-EDGE-06`) covering a "PR Activity Queries" audit workspace (query templates, drill-down trail, export-approval workflow, case-file flagging) and a PR-specific "Configuration workspace" (workflow-threshold editor with `effective_from` versioning, PR Type Defaults, Delegation Rules, Tax Codes, Currency Rates). This was settled against current source in `.specs/resync-2026-07-15-progress.md` (commit `df8ab13`) after reading every route in `router.tsx` and every screen component under `routes/system-admin/` and `routes/config/` — no PR-specific audit or configuration surface exists. See [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) for the full correction, the exact screen-by-screen mapping, and the searches run. This is the same pattern independently found and corrected in the `purchase-order` module — see [purchase-order/04-test-scenarios-audit-config.md](/en/inventory/purchase-order/04-test-scenarios-audit-config).

## What Was Removed and Why

| Removed scenario group | Reason |
|---|---|
| `AUD-HP-01` – `AUD-HP-04` (Auditor query-workspace, drill-down trail, export-approval, case-file flagging) | No "Audit workspace," "PR Activity Queries" route, or PR-scoped drill-down page found anywhere in `carmen-inventory-frontend-react`. |
| `AUD-HP-05` – `AUD-HP-09` (Sysadmin workflow-threshold, delegation, PR-type-default, tax/currency-master config with preview panels and `effective_from` versioning) | No PR-specific configuration workbench found. Workflow-stage and RBAC configuration are generic system-config screens (`/system-admin/workflow`, `/system-admin/user`, `/system-admin/role`); tax and currency configuration are generic master-data screens (`/config/tax-profile`, `/config/currency`, `/config/exchange-rate`) — none PR-specific, and none has a preview/forecast panel or `effective_from` versioning. Amount-threshold routing and delegation windows have **no equivalent anywhere** in current source, generic or PR-specific. |
| `AUD-PERM-01` – `AUD-PERM-07`, `AUD-VAL-01` – `AUD-VAL-08`, `AUD-EDGE-01` – `AUD-EDGE-06` | All depend on the non-existent workspaces and configuration surfaces above. |

## What Is Confirmed Instead

- The generic **`/system-admin/activity-log`** screen lists `action` / `entity_type` / `user` events across all document types, filterable but not query-template-driven; a `purchase_request`-scoped filter is the closest equivalent to "PR Activity Queries." Any user with read access to a PR can also see its `tb_purchase_request_comment` history directly on the PR detail page (`type = system` rows immutable per `PR_POST_008`). Whether a distinct Auditor role gates either surface differently from any other reader was not confirmed.
- Workflow-stage definitions (`stage_role`, `user_action.execute[]`), tax rates, currency and exchange-rate masters, and RBAC user/role assignments are each configured through their own generic screen — `/system-admin/workflow`, `/config/tax-profile`, `/config/currency` + `/config/exchange-rate`, `/system-admin/user` + `/system-admin/role` — shared across PR, PO, GRN, and other document types, not through a PR-specific screen.
- The one confirmed PR-state-changing action available to this persona axis is the System Administrator's elevated **void** (`PR_AUTH_007` → `PR_POST_006`): `pr_status` flips to `voided`, the budget soft-commitment releases, and a mandatory-reason comment is appended. This is exercised incidentally in other personas' scenario tables (e.g. [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) `APP-VAL-10`, [04-test-scenarios-requestor.md](./04-test-scenarios-requestor.md) `REQ-PERM-06`), not in a dedicated audit-config scenario here.
- A repo-wide search for `threshold` and `delegat` in both the frontend and backend found no amount-threshold routing or approval-delegation mechanism anywhere — this also means `PR_AUTH_005` and `PR_AUTH_006` in [02-business-rules.md](./02-business-rules.md) describe unconfirmed design intent, flagged here for a follow-up business-rules correction outside this page's scope.

## References

- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — the full correction, including the exact screens read and the searches run.
- Sibling: [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) — where the confirmed `PR_AUTH_007` void is exercised as a precondition, in place of the removed Sysadmin-configuration scenarios.
- Related (generic config, not PR-specific): [system-config/workflow](/en/inventory/system-config/workflow).
- Cross-link: [purchase-order/04-test-scenarios-audit-config.md](/en/inventory/purchase-order/04-test-scenarios-audit-config) — sibling module's identical correction, with the full list of searches run.
