---
title: Purchase Request — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-request.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-request, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios

> **At a Glance**
> **Module:** [purchase-request](/en/inventory/purchase-request) &nbsp;·&nbsp; **Total scenarios:** ~10 cross-persona + per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Requestor, Approver, Purchaser, Procurement Manager, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

> **Executable coverage (2026-09-22).** The Playwright suite in `../carmen-inventory-frontend-e2e/` is the executable spec for this module; this page does not mirror its cases. There is no `docs/test-cases/3xx-*.md` catalogue page for PR — the catalogued cases live in the gap reports and the generated user stories: `docs/test-cases/gaps/301-pr-core-gap.md` (46 cases), `gaps/301-pr-from-template-gap.md` (25), `gaps/302-pr-creator-journey-gap.md` (34), `gaps/303-pr-approver-journey-gap.md` (37), `gaps/304-pr-purchaser-journey-gap.md` (36), `gaps/311-pr-returned-flow-gap.md` (30), `gaps/201-my-approvals-gap.md` (34), `gaps/310-pr-template-gap.md` (49); stories `docs/user-stories/{201-my-approvals,301-pr,302-pr-creator-journey,303-pr-approver-journey,304-pr-purchaser-journey,310-pr-template,311-pr-returned-flow}.md`; specs `tests/301-pr.spec.ts` (197 tests), `302-pr-creator-journey.spec.ts` (70), `303-pr-approver-journey.spec.ts` (62), `304-pr-purchaser-journey.spec.ts` (61), `311-pr-returned-flow.spec.ts` (21), `201-my-approvals.spec.ts` (21), `310-pr-template.spec.ts` (61). Route coverage is tracked in `docs/test-cases/COVERAGE.md` (`/procurement/purchase-request`, `/procurement/purchase-request-template`, `/procurement/approval`; `/procurement/purchase-request/from-template` is reached by click, not `goto()`, so it reads as uncovered there).

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `purchase-request` module. It enumerates the personas under test, points to a dedicated per-persona scenarios file for each, and captures the cross-persona handoff paths that no single persona owns end-to-end. Coverage spans three dimensions: **functional** (happy paths plus expected validation errors as captured in [02-business-rules.md](./02-business-rules.md)), **RBAC / authorization** (each persona is restricted to the actions allowed at its stage of [03-user-flow.md](./03-user-flow.md) Section 2), and **edge / negative** (boundary values, missing pre-conditions, send-back loops, split-rejects, escalations, and administrative voids).

Per-persona scenarios — Happy Path, Permission / Authorization, Validation / Error, and Edge Cases — live in the five files linked in Section 3 and follow the layout in `.specs/templates/04-test-scenarios.md`. The cross-persona table in Section 4 below picks up at the handoff boundaries listed in [03-user-flow.md](./03-user-flow.md) Section 4 and chains them into full end-to-end paths suitable for golden / regression runs. Section 5 ties each scenario back to a concrete Playwright spec in `../carmen-inventory-frontend-e2e/tests/`.

## 2. Personas in Scope

- **Requestor**: Creates and submits PRs; responds to send-backs by editing and resubmitting; cancels own drafts.
- **Approver**: Every `approve`-role stage (illustrated as Department Head, Budget Controller, Finance); approve / reject / send-back / split per stage. No budget check exists in code (`PR_VAL_015`).
- **Purchaser**: Holds the `purchase`-role stage in the PR's own approval chain (edits vendor / pricing, then bulk-decides like any other stage); separately, once a PR is `approved`, runs the Convert-to-PO dialog in the Purchase Order module.
- **Procurement Manager**: Escalated / high-value `approve`-role stage in the same chain, using the identical Approver UI — no distinct configuration screen exists in current source.
- **Audit / Config**: Auditor (read-only review of PRs and activity log); System Administrator (workflow stage configuration, amount-threshold routing setup; super-admin delete of another user's draft). *(Administrative voids — unconfirmed, no endpoint; `PR_AUTH_007`.)* *(Delegation rules were asserted in an earlier revision — unconfirmed, no matching mechanism found; see `02-business-rules.md` `PR_AUTH_006`.)*

## 3. Persona Test Files

- [Requestor scenarios](./04-test-scenarios-requestor.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-PR-01 | Full happy path: PR created, walked through the approval chain (including its own `purchase`-role stage), and later converted to a PO from the Purchase Order module | Requestor → Department Head → Budget Controller → Finance → Purchaser (`purchase`-role stage, bulk-approves) → (separately) Convert-to-PO dialog | Active workflow with the chain's final stage tagged `purchase`; header `base_total_amount` under the high-value threshold; vendor and pricing data available | PR `approved` once the `purchase`-role stage bulk-approves (`PR_POST_005`); `completed` only after a later, separate Convert-to-PO action fully bridges its lines to one or more `tb_purchase_order` records (`PR_POST_007`) |
| X-PR-02 | Send-back loop: approver returns a PR, requestor edits and resubmits | Requestor → Approver (stage N) → Requestor → Approver (stage N) → … → final Approver | PR submitted and awaiting approval at stage N; valid send-back reason text and a target stage | PR ultimately `approved` after the second pass; `pr_status` stays `in_progress` throughout (send-back only moves `workflow_current_stage`, `purchase-request.service.ts:2052`); revision history and approver comment retained |
| X-PR-03 | Split-reject: approver rejects some lines, approves the remainder, PR continues with the surviving subset | Requestor → Approver (stage N) → next-stage Approver | PR has at least two lines; rejecting approver provides per-line reason text | PR stays `in_progress` with rejected lines flagged; surviving lines advance to the next stage; rejected lines excluded from any later PO conversion |
| X-PR-04 | Multi-PR consolidation: two approved PRs sharing vendor, delivery date, and currency are converted together into one PO | Requestor(s) → full Approver chain (×2 PRs) → Convert-to-PO dialog (Purchase Order module) | Two PRs both `approved`, both matching `(vendor, delivery_date, currency)` | The group-PR step buckets both PRs' lines into one draft-PO group; confirming creates one `tb_purchase_order`; both source PRs flip to `completed` once fully bridged (`PR_POST_007`). The current UI selects and converts whole PRs — there is no partial-line conversion. |
| X-PR-05 | Routing rule: header amount matches a `routing_rules` condition and jumps to the Procurement Manager stage | Requestor → Department Head → Budget Controller → (routing rule) → Procurement Manager | Workflow carries a `total_amount` routing rule whose target is the Procurement Manager stage (`PR_AUTH_005`) | PR is `approved` only after the Procurement Manager signs the target stage (identical Approver UI); `workflow_history` records the jump |
| X-PR-06 | Reject path: approver rejects the PR outright; workflow terminates | Requestor → Approver (any stage) | Rejecting approver provides reason text | PR `voided`, no further actions allowed, audit comment written |
| X-PR-07 | Bounce-back from the Purchaser's own `purchase`-role stage: Purchaser sends the PR back for vendor / scope clarification | Requestor → Approver chain → Purchaser (`purchase`-role stage) → prior stage or Requestor | PR is `in_progress` at the `purchase`-role stage; Purchaser cannot satisfy vendor or pricing as requested | Bulk **Send for Review** moves the PR back one stage (or to `draft` if the target is the create stage), same mechanism as any other stage's send-back |
| X-PR-08 | Administrative void by System Administrator on an in-flight PR — **not executable** | Requestor → Approver (stage N) → System Administrator | — | **Unconfirmed — no void endpoint or control exists** (`PR_AUTH_007`); the only path to `voided` is an approver Reject. Kept as a placeholder so the id stays stable. |
| X-PR-09 | Delete-own-draft: Requestor abandons a draft before submitting | Requestor only | PR is `draft` and has never been submitted; Requestor is `created_by_id` / `requestor_id` | Row soft-deleted (`deleted_at` on header and lines, `PR_POST_009`); it disappears from the list and from `sys_v_my_pending`; `pr_status` is untouched (not `voided`). A non-owner gets `PR_DELETE_FORBIDDEN`; a submitted PR gets "Only draft purchase requests can be deleted" |
| X-PR-10 | Returned-PR round trip on the canonical Playwright golden path | Requestor → HOD (Department Head) → Requestor → HOD → … | Seeded via `submitPRAsRequestor` + `sendForReviewAsHOD` helpers in the E2E suite (`tests/311-pr-returned-flow.spec.ts`) | The PR is shown at the create stage with `last_action = reviewed`, then advances again after the Requestor resubmits; `pr_status` reads `in_progress` on both legs; Workflow History reflects the full loop |

## 5. E2E Test Mapping

The Playwright suite under `../carmen-inventory-frontend-e2e/tests/` already contains PR coverage. Persona-journey specs use the `TC-PR-NNNNNN` test-case naming convention; the per-action multi-role file (`301-pr.spec.ts`) covers the action × role matrix.

### Requestor (Creator)
- `../carmen-inventory-frontend-e2e/tests/302-pr-creator-journey.spec.ts` (70 tests; gap `docs/test-cases/gaps/302-pr-creator-journey-gap.md`, 34 cases; from-template flow `TC-PR-0503xx`, gap `gaps/301-pr-from-template-gap.md`, 25 cases) — Persona-journey spec for the Requestor. Covers list / `My Pending` tab, create-PR happy path and validation errors, edit / save draft, submit-for-approval, delete-own-draft, and the smoke checks per `TC-PR-050NNN` block. Maps to Requestor scenarios in [04-test-scenarios-requestor.md](./04-test-scenarios-requestor.md).
- `../carmen-inventory-frontend-e2e/tests/311-pr-returned-flow.spec.ts` (21 tests; gap `gaps/311-pr-returned-flow-gap.md`, 30 cases) — Cross-persona Returned-PR flow (Requestor edits and resubmits a PR that an Approver sent back). Maps to X-PR-02 and X-PR-10 in Section 4 above and to the send-back scenarios in the Requestor and Approver files.

### Approver
- `../carmen-inventory-frontend-e2e/tests/303-pr-approver-journey.spec.ts` (62 tests; gap `gaps/303-pr-approver-journey-gap.md`, 37 cases) and `tests/201-my-approvals.spec.ts` (21 tests; gap `gaps/201-my-approvals-gap.md`, 34 cases) — Persona-journey spec for the Approver (HOD primary, Finance Controller for scope contrast). Covers the My Approval queue (`/procurement/approval`), edit mode in approver scope (approved-qty / item-note / delivery-point editable, vendor / unit-price read-only), bulk approve / reject / send-for-review / split via toolbar. Maps to Approver scenarios in [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) and to X-PR-02, X-PR-03, X-PR-06 in Section 4 above.

### Purchaser
- `../carmen-inventory-frontend-e2e/tests/304-pr-purchaser-journey.spec.ts` (61 tests; gap `gaps/304-pr-purchaser-journey-gap.md`, 36 cases — note its Step 3 pricing blocks skip when the item row is collapsed, see the gap report) — Persona-journey spec for the Purchaser. Covers list scoping to `Purchase` stage, edit-mode permissions (vendor / unit-price / discount / tax-profile editable, approved-qty read-only), Auto Allocate vendors, bulk approve / reject / send-for-review / split, plus the `TC-PR-070901` golden full-flow scenario. Maps to Purchaser scenarios in [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) and to X-PR-01, X-PR-04, X-PR-07 in Section 4 above.

### Procurement Manager
- No dedicated Procurement Manager spec yet. Escalation paths (X-PR-05) and high-value override are partly exercised via `gmTest` blocks in `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts`. **TODO**: add a `30X-pr-procurement-manager-journey.spec.ts` once the Procurement Manager scenarios file is published.

### Audit / Config
- No dedicated Auditor / System Administrator spec yet — config / threshold flows live in admin pages outside the PR module proper. **TODO**: add coverage under `../carmen-inventory-frontend-e2e/tests/` (workflow stage configuration, routing-rule setup). X-PR-08 (administrative void) is **not** a candidate — no such feature exists.

### Shared / Multi-Role
- `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` (197 tests; gap `gaps/301-pr-core-gap.md`, 46 cases) — Per-action × per-role coverage that pre-dates the persona-journey specs. Useful for permission / authorization regressions across `requestorTest`, `hodTest`, `fcTest`, `purchaseTest`, `gmTest`, and `noAuthTest` fixtures.
- `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts` (61 tests; gap `gaps/310-pr-template-gap.md`, 49 cases) — PR Template create / edit coverage (purchase-role + requestor-deny). Adjacent to the Purchaser scenarios file.

## 6. References

- `../carmen-inventory-frontend-e2e/` — Playwright test suite (executable spec for the rows above).
- `../carmen/docs/purchase-request-management/testing.md` — upstream testing strategy, unit / integration / E2E / performance / security levels, sample tests.
- `../carmen/docs/purchase-request-management/troubleshooting.md` — known failure modes, error codes, and resolutions that drive the Validation / Error sub-sections in each persona file.
- Sibling: [03-user-flow.md](./03-user-flow.md) — flow context, especially Section 4 (Cross-Persona Handoffs) from which Section 4 above is derived.
- Sibling: [02-business-rules.md](./02-business-rules.md) — rules being verified by the negative tests under each persona's Validation / Error block.
