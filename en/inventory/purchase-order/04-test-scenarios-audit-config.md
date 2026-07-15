---
title: Purchase Order — Test Scenarios — Audit & Config
description: Why no dedicated audit-workspace or PO-specific configuration test scenarios exist for purchase-order in current source, and what is confirmed instead.
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor + System Administrator) — **no dedicated audit-workspace or PO-specific configuration workbench confirmed in current source** &nbsp;·&nbsp; **Module:** [purchase-order](/en/inventory/purchase-order)
> **E2E coverage:** none confirmed for a dedicated workspace; the underlying activity-log fields (`workflow_history`, `tb_purchase_order_comment`) are exercised incidentally by every other persona's spec.

> ⚠️ **Major correction this pass.** The previous version of this page listed ~30 scenarios (AUD-HP-01 through AUD-EDGE-06) covering a "Procurement Activity Queries" workspace (query templates, export-approval workflow, case-file notes) and a PO-specific "Configuration workspace" (numbering-scheme editor, RBAC editor, PR-to-PO grouping-rule editor, approval-delegation-window manager, deadlock detection). No route, component, or backend endpoint matching either workspace was found in current source. See [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) for the full correction and the searches run. This pattern (an elaborate audit/config narrative with no matching route) was also flagged as unverified in the `purchase-request` module's prior resync pass; this pass's broader searches found nothing supporting it anywhere in the product, so it is corrected here rather than merely deferred again.

## What Was Removed and Why

| Removed scenario group | Reason |
|---|---|
| AUD-HP-01 through AUD-HP-05 (Auditor query workspace, chain drill-down, export approval) | No "Audit workspace" or "Procurement Activity Queries" route/component found. |
| AUD-HP-06 through AUD-HP-09 (Sysadmin numbering/RBAC/grouping-rule/delegation config) | No PO-specific configuration workbench found; numbering and workflow-stage configuration are generic system-config screens (see [system-config/workflow](/en/inventory/system-config/workflow), [system-config/running-code](/en/inventory/system-config/running-code)), not PO-specific pages with the described editors. |
| AUD-PERM-01 through AUD-PERM-07, AUD-VAL-01 through AUD-VAL-08, AUD-EDGE-01 through AUD-EDGE-06 | All depend on the non-existent workspaces above. |

## What Is Confirmed Instead

- Any user with read access to a PO can see its `workflow_history` and `tb_purchase_order_comment` on the detail page itself — this is the real, confirmed "audit trail" surface. Whether a distinct Auditor role gates this differently from any other viewer was not confirmed.
- Workflow-stage definitions (`stage_role`, `user_action.execute[]`) and document numbering (`po_no` generation) are configured through the generic system-config module, shared across PR, PO, GRN, and other document types — not through a PO-specific screen. See the system-config module's own pages (out of scope for this iteration) for what is actually confirmed there.
- No PO-specific RBAC editor, integration-settings screen, or delegation-window manager was found.

## References

- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — the full correction, including the exact searches run and what they returned.
- Sibling: [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) — the confirmed remediation path (cancel / close / reject) for a stuck PO, in place of the removed Sysadmin-escalation scenarios.
- Related (generic config, not PO-specific): [system-config/workflow](/en/inventory/system-config/workflow), [system-config/running-code](/en/inventory/system-config/running-code).
