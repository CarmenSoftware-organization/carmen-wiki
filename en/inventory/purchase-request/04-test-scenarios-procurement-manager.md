---
title: Purchase Request — Test Scenarios — Procurement Manager
description: Procurement Manager's test cases (escalated / high-value approval) for purchase-request.
published: true
date: 2026-07-15T10:20:00.000Z
tags: purchase-request, test-scenarios, procurement-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios — Procurement Manager

> **At a Glance**
> **Persona:** Procurement Manager / General Manager (escalated / high-value approve stage — same UI as the base Approver chain) &nbsp;·&nbsp; **Module:** [purchase-request](/en/inventory/purchase-request) &nbsp;·&nbsp; **Scenarios:** ~7
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation
> **E2E coverage:** no dedicated Procurement Manager persona-journey spec exists yet; escalation / high-value paths are exercised via the `gmTest` fixture in `tests/301-pr.spec.ts` in `../carmen-inventory-frontend-e2e/`

This page captures the test scenarios that the Procurement Manager persona drives in the `purchase-request` module. As documented in [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md), the current source has no dedicated Procurement Manager screen — the persona is an `approve`-role stage in the **same** workflow as the base Approver chain, reached either through threshold-based escalation (`PR_AUTH_005`) or direct workflow routing. Scenarios below are the escalated-stage subset of the base Approver scenarios in [04-test-scenarios-approver.md](./04-test-scenarios-approver.md); that page's line-level, delegation, and threshold-boundary scenarios apply verbatim here.

> ⚠️ **Discrepancy note:** an earlier revision of this page described a "configurational surface" (Vendor Allocation Rules scoring weights, per-vendor priority overrides, Stuck PR Oversight bulk actions) with ~20 additional scenarios. No matching screen, route, or endpoint was found in `../carmen-inventory-frontend-react/` or `../carmen-turborepo-backend-v2/` during this pass — see the discrepancy log entry in the resync progress log. Those scenarios have been removed rather than carried forward as fiction.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| PM-HP-01 | Receive and review an escalated PR | PR `pr_status = in_progress`, routed to the Procurement Manager because `base_total_amount` breached the configured threshold (`PR_AUTH_005`), or by direct workflow routing | Open **My Pending**; open the escalated PR; review header, lines, Budget Impact, and Activity Log (full upstream Approver comments visible). | PR detail loads with the same read-mostly / Edit Mode UI as the base Approver chain; action bar shows the standard bulk toolbar. |
| PM-HP-02 | Approve an escalated PR at the final stage | PR at the Procurement Manager's stage, which is the chain's last `approve`-role stage | Enter Edit Mode, select all, bulk **Approve**, confirm. | `PR_POST_005` fires: `pr_status` flips `in_progress → approved`; PR becomes eligible for the separate Convert-to-PO dialog. |
| PM-HP-03 | Reject a very-high-value PR | PR assigned to the Procurement Manager / General Manager for approval (`TC-PR-060005`) | Open the PR; click **Reject**; enter a reason; confirm. | `pr_status` flips to `voided`; requestor notified; Auditor can review the reason post-hoc. |
| PM-HP-04 | Send an escalated PR back for revision | PR at the escalated stage; justification insufficient | Bulk **Send for Review** with a reason. | `workflow_current_stage` moves back one step (or all the way to the Requestor's create stage, returning `pr_status` to `draft`, depending on workflow configuration). |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| PM-PERM-01 | Procurement Manager opens a PR at their assigned escalated stage | **Allow** — identical rights to the base Approver chain (`PR_AUTH_002`, `PR_AUTH_003`, `PR_AUTH_004`). |
| PM-PERM-02 | Procurement Manager opens a PR still at an earlier stage (e.g. Budget Controller) not yet escalated | **Deny action, read-only** (if visible at all) — `user_action.execute[]` for the current stage does not include the Procurement Manager. |
| PM-PERM-03 | Procurement Manager attempts to edit vendor / unit price / discount / tax on a line | **Deny.** Those fields are reserved for the `purchase`-role stage per `PR_AUTH_008`; the escalated approve-role stage only gets `approved_qty` per `PR_VAL_013`. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| PM-VAL-01 | Reject / Send for Review without a reason | Reason field left empty, Confirm clicked | Reject — Confirm stays disabled or the server rejects the call; a reason is mandatory for both actions. |
| PM-VAL-02 | Adjust `approved_qty` beyond `requested_qty` | `approved_qty` set above `requested_qty` on a line, Approve clicked | `PR_VAL_013` — reject with "Approved quantity must be positive and may not exceed requested quantity". |

## 4. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoff `X-PR-05` (threshold escalation)
- User flow: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md)
- Business rules: [02-business-rules.md](./02-business-rules.md) Section 4 (`PR_AUTH_005` threshold routing, `PR_AUTH_006` delegation), Section 5 (`PR_POST_003`, `PR_POST_005`, `PR_POST_006`)
- Sibling: [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) — base Approver scenarios this set extends verbatim (line-level validation, delegation, threshold-boundary edge cases)
- E2E: **Gap** — no dedicated `30X-pr-procurement-manager-journey.spec.ts` exists. Escalation / high-value scenarios are exercised via the `gmTest` fixture in `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` (e.g. `TC-PR-060005`).
- Cross-link: [purchase-order](/en/inventory/purchase-order) — downstream module receiving the final-approved PR for conversion
