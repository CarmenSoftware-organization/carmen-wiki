---
title: Purchase Request — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-request.
published: true
date: 2026-05-20T00:00:00.000Z
tags: purchase-request, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios

> **At a Glance**
> **Module:** [purchase-request](/en/inventory/purchase-request) &nbsp;·&nbsp; **Total scenarios:** ~10 cross-persona + per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Requestor, Approver, Purchaser, Procurement Manager, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `purchase-request` module. It enumerates the personas under test, points to a dedicated per-persona scenarios file for each, and captures the cross-persona handoff paths that no single persona owns end-to-end. Coverage spans three dimensions: **functional** (happy paths plus expected validation errors as captured in [02-business-rules.md](./02-business-rules.md)), **RBAC / authorization** (each persona is restricted to the actions allowed at its stage of [03-user-flow.md](./03-user-flow.md) Section 2), and **edge / negative** (boundary values, missing pre-conditions, send-back loops, split-rejects, escalations, and administrative voids).

Per-persona scenarios — Happy Path, Permission / Authorization, Validation / Error, and Edge Cases — live in the five files linked in Section 3 and follow the layout in `.specs/templates/04-test-scenarios.md`. The cross-persona table in Section 4 below picks up at the handoff boundaries listed in [03-user-flow.md](./03-user-flow.md) Section 4 and chains them into full end-to-end paths suitable for golden / regression runs. Section 5 ties each scenario back to a concrete Playwright spec in `../carmen-inventory-frontend-e2e/tests/`.

## 2. Personas in Scope

- **Requestor**: Creates and submits PRs; responds to send-backs by editing and resubmitting; cancels own drafts.
- **Approver**: Multi-stage approval chain (Department Head, Budget Controller, Finance Officer / Manager); approve / reject / send-back / split-reject per stage.
- **Purchaser**: Validates vendor allocation and pricing; consolidates and converts approved PRs to POs; can bounce a PR back to the Approver chain.
- **Procurement Manager**: High-value approval override; tunes vendor ranking and Allocate Vendor rules; absorbs escalated PRs.
- **Audit / Config**: Auditor (read-only review of PRs and activity log); System Administrator (workflow stage configuration, threshold setup, delegation rules, administrative voids).

## 3. Persona Test Files

- [Requestor scenarios](./04-test-scenarios-requestor.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-PR-01 | Full happy path: PR created, walked through a three-stage approval chain, and converted to a PO | Requestor → Department Head → Budget Controller → Finance → Purchaser | Active workflow with three approval stages; header `base_total_amount` under the high-value threshold; vendor and pricing data available | PR `completed`, one or more `tb_purchase_order` records linked back to the PR, soft commitment hardened into PO commitment |
| X-PR-02 | Send-back loop: approver returns a PR, requestor edits and resubmits | Requestor → Approver (stage N) → Requestor → Approver (stage N) → … → final Approver | PR submitted and awaiting approval at stage N; valid send-back reason text | PR ultimately `approved` after the second pass; revision history and approver comment retained; soft budget commitment released on send-back then re-created on resubmission |
| X-PR-03 | Split-reject: approver rejects some lines, approves the remainder, PR continues with the surviving subset | Requestor → Approver (stage N) → next-stage Approver | PR has at least two lines; rejecting approver provides per-line reason text | PR stays `in_progress` with rejected lines flagged; surviving lines advance to the next stage; rejected lines excluded from any later PO conversion |
| X-PR-04 | Partial conversion: purchaser converts only some approved lines, leaving the rest available | Requestor → full Approver chain → Purchaser | PR is `approved` with multiple lines; only a subset is needed now (e.g. preferred vendor unavailable for some lines) | At least one `tb_purchase_order` is created for the selected lines; PR header stays `approved` for the remaining lines until they are converted or aged out |
| X-PR-05 | Escalation: header amount breaches the high-value threshold and routes to the Procurement Manager | Requestor → Department Head → Budget Controller → (escalation) → Procurement Manager | Header `base_total_amount` exceeds the configured threshold for the workflow | PR is `approved` only after the Procurement Manager signs the escalated stage; stage cursor records the escalation hop |
| X-PR-06 | Reject path: approver rejects the PR outright; workflow terminates | Requestor → Approver (any stage) | Rejecting approver provides reason text | PR `voided`, soft budget commitment released, no further actions allowed, audit comment written |
| X-PR-07 | Bounce-back from Purchaser: Purchaser sends the PR back for vendor / scope clarification | Requestor → full Approver chain → Purchaser → Approver (stage N or Requestor) | PR is `approved`; Purchaser cannot satisfy vendor or pricing within scope | PR returns to the chain (or to the Requestor as a returned PR) with Purchaser's comment; depending on workflow config, status moves back to `in_progress` or `draft` |
| X-PR-08 | Administrative void by System Administrator on an in-flight PR | Requestor → Approver (stage N) → System Administrator | PR is `in_progress`; admin has reason text (e.g. duplicate, compliance) | PR `voided`, soft budget commitment released, workflow terminates; Auditor can read the void reason post-hoc |
| X-PR-09 | Cancel-own-draft: Requestor abandons a draft before submitting | Requestor only | PR is `draft` and has never been submitted | PR `voided`; no workflow stage advanced; no audit chain produced beyond the cancel event |
| X-PR-10 | Returned-PR round trip on the canonical Playwright golden path | Requestor → HOD (Department Head) → Requestor → HOD → … | Seeded via `submitPRAsRequestor` + `sendForReviewAsHOD` helpers in the E2E suite | PR moves Returned → In Progress after Requestor resubmits; status badge and Workflow History reflect the full loop |

## 5. E2E Test Mapping

The Playwright suite under `../carmen-inventory-frontend-e2e/tests/` already contains PR coverage. Persona-journey specs use the `TC-PR-NNNNNN` test-case naming convention; the per-action multi-role file (`301-pr.spec.ts`) covers the action × role matrix.

### Requestor (Creator)
- `../carmen-inventory-frontend-e2e/tests/302-pr-creator-journey.spec.ts` — Persona-journey spec for the Requestor. Covers list / `My Pending` tab, create-PR happy path and validation errors, edit / save draft, submit-for-approval, cancel-own-draft, and the smoke checks per `TC-PR-050NNN` block. Maps to Requestor scenarios in [04-test-scenarios-requestor.md](./04-test-scenarios-requestor.md).
- `../carmen-inventory-frontend-e2e/tests/311-pr-returned-flow.spec.ts` — Cross-persona Returned-PR flow (Requestor edits and resubmits a PR that an Approver sent back). Maps to X-PR-02 and X-PR-10 in Section 4 above and to the send-back scenarios in the Requestor and Approver files.

### Approver
- `../carmen-inventory-frontend-e2e/tests/303-pr-approver-journey.spec.ts` — Persona-journey spec for the Approver (HOD primary, Finance Controller for scope contrast). Covers My Approvals dashboard, edit mode in approver scope (approved-qty / item-note / delivery-point editable, vendor / unit-price read-only), bulk approve / reject / send-for-review / split via toolbar. Maps to Approver scenarios in [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) and to X-PR-02, X-PR-03, X-PR-06 in Section 4 above.

### Purchaser
- `../carmen-inventory-frontend-e2e/tests/304-pr-purchaser-journey.spec.ts` — Persona-journey spec for the Purchaser. Covers list scoping to `Purchase` stage, edit-mode permissions (vendor / unit-price / discount / tax-profile editable, approved-qty read-only), Auto Allocate vendors, bulk approve / reject / send-for-review / split, plus the `TC-PR-070901` golden full-flow scenario. Maps to Purchaser scenarios in [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) and to X-PR-01, X-PR-04, X-PR-07 in Section 4 above.

### Procurement Manager
- No dedicated Procurement Manager spec yet. Escalation paths (X-PR-05) and high-value override are partly exercised via `gmTest` blocks in `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts`. **TODO**: add a `30X-pr-procurement-manager-journey.spec.ts` once the Procurement Manager scenarios file is published.

### Audit / Config
- No dedicated Auditor / System Administrator spec yet — most config / void / threshold flows live in admin pages outside the PR module proper. **TODO**: add coverage under `../carmen-inventory-frontend-e2e/tests/` (e.g. workflow stage configuration, threshold setup, void-with-reason on an in-flight PR) once the Audit / Config scenarios file is published; X-PR-08 from Section 4 above is the priority candidate.

### Shared / Multi-Role
- `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` — Per-action × per-role coverage that pre-dates the persona-journey specs. Useful for permission / authorization regressions across `requestorTest`, `hodTest`, `fcTest`, `purchaseTest`, `gmTest`, and `noAuthTest` fixtures.
- `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts` — PR Template create / edit coverage (purchase-role + requestor-deny). Adjacent to the Purchaser scenarios file.

## 6. References

- `../carmen-inventory-frontend-e2e/` — Playwright test suite (executable spec for the rows above).
- `../carmen/docs/purchase-request-management/testing.md` — upstream testing strategy, unit / integration / E2E / performance / security levels, sample tests.
- `../carmen/docs/purchase-request-management/troubleshooting.md` — known failure modes, error codes, and resolutions that drive the Validation / Error sub-sections in each persona file.
- Sibling: [03-user-flow.md](./03-user-flow.md) — flow context, especially Section 4 (Cross-Persona Handoffs) from which Section 4 above is derived.
- Sibling: [02-business-rules.md](./02-business-rules.md) — rules being verified by the negative tests under each persona's Validation / Error block.
