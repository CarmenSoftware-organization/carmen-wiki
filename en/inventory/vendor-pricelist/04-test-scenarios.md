---
title: Vendor Pricelist — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for vendor-pricelist.
published: true
date: 2026-05-19T23:55:00.000Z
tags: vendor-pricelist, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios

> **At a Glance**
> **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist) &nbsp;·&nbsp; **Total scenarios:** ~12 cross-persona + per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Purchaser, Vendor, Finance, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenario set of the `vendor-pricelist` module. The pricelist lifecycle spans four personas — Purchaser (collapsing Purchasing Staff + Purchasing Manager), Vendor (external), Finance (Officer + Manager), and Audit / Config (Auditor + System Administrator) — and test coverage is split accordingly: each persona has a dedicated file (linked in Section 3) that enumerates that persona's functional, authorization (where applicable), validation, edge, and golden-journey scenarios. This overview file gives the global picture: who is in scope, what each persona's tests cover at the headline level, the cross-persona handoff scenarios that stitch the individual journeys into a complete end-to-end flow, and the mapping from each scenario back to the E2E / API / integration tests that exercise it.

Scope of testing on the vendor-pricelist module covers four broad areas: **functional coverage** of every action across the three tiers (template create / edit / activate, campaign launch / pause / cancel, vendor portal entry / submit / resubmit, pricelist review / approve / reject / inactivate), **RBAC / authorization** of who can perform each action (Purchaser create / edit / approve, Manager high-value approval, Vendor portal access via token, Finance Manager multi-currency co-signoff, Sysadmin configuration + token revocation, Auditor read-only across the chain), **edge cases** around MOQ-tier boundary cases, multi-currency handling, concurrent vendor sessions, token expiry and revocation races, optimistic-concurrency on the pricelist row, and the validation-rule registry, and **three-way-match downstream behaviour** at GRN / invoice posting against the active pricelist (handed back to Finance and to the Purchaser per [purchase-order/02-business-rules](/en/inventory/purchase-order/02-business-rules) § `PO_POST_008` / `PO_POST_009`).

## 2. Personas in Scope

- **Purchaser** — Builds templates, runs campaigns (request-for-pricing), sends invitations, reviews submitted pricelists, approves / rejects, manages preferred-vendor flags, manually uploads emailed submissions. The Purchasing Manager scenarios on the same file extend with high-value approval, business-rule configuration toggles, and multi-currency sign-off. Owns ~24+ scenarios across template, campaign, pricelist review, golden journey.
- **Vendor** — External party. Token-authenticated portal session is the **only** in-system surface for an external party in this module. Drives state through `tb_pricelist.submitted_at` write and the implicit `(none) → draft` insert. Owns happy-path and validation scenarios; the Permission / Authorization section is reduced to a single N/A row because the vendor has no Carmen login (the portal-token policy itself is tested as a Sysadmin-side configuration concern).
- **Finance** — Read-only on the pricelist itself (`VPL_AUTH_009`); writes only via comments and via the Finance Manager's co-signoff comment for multi-currency / high-value pricelists. Variance investigation drives most scenarios; downstream three-way-match coverage lives in the [purchase-order](/en/inventory/purchase-order) module's Finance scenarios and is referenced through cross-persona handoffs.
- **Audit / Config** — Auditor (read-only across the chain — templates, campaigns, invitations, pricelists, validation results, activity logs, downstream consumption) and System Administrator (configuration only — numbering, RBAC, portal-token policy, email integration, validation rules, currency / FX sources, audit retention; plus the per-invitation token-revocation right). Behaviour is largely off the transactional happy path; documented separately in Section 3 for completeness.

## 3. Persona Test Files

- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Vendor scenarios](./04-test-scenarios-vendor.md) — shorter than other persona files; Permission / Authorization section reduced to one N/A row per [03-user-flow-vendor.md](./03-user-flow-vendor.md) Section 1.
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The scenarios below trace the pricelist across multiple personas. Each row anchors the handoff sequence to the document state at the boundary and the expected end state. They are derived from the handoff table in [03-user-flow.md](./03-user-flow.md) Section 4.

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-VPL-01 | Full happy path — single-vendor, single-currency, below threshold | Purchaser (template + campaign) → Vendor (portal submit) → Purchaser (approve) → downstream PR / PO / GRN | Active template, vendor in catalogue with contact email | Pricelist `active`; downstream PR-line defaults from this pricelist |
| X-VPL-02 | High-value approval — Manager gate | Purchaser → Vendor → Purchasing Manager (approve) | Submitted pricelist projected aggregate exceeds high-value threshold | Pricelist `active`; Manager `system` signoff on activity log |
| X-VPL-03 | Multi-currency approval — Manager + Finance Manager co-signoff | Purchaser → Vendor → Purchasing Manager + Finance Manager (parallel) → activation | Submitted pricelist currency differs from tenant base and crosses FX threshold | Pricelist `active`; both Manager + Finance Manager `system` signoffs |
| X-VPL-04 | Reject and resubmit | Purchaser → Vendor → Purchaser (reject) → Vendor (correct + resubmit) → Purchaser (approve) | Submitted pricelist with validator warning | Pricelist `active` after second submit cycle |
| X-VPL-05 | Email-method submission (vendor refuses portal) | Purchaser (issue email template) → Vendor (returns Excel by email) → Purchaser (upload on vendor's behalf) → Purchaser (approve) | Vendor confirmed via campaign contact that they cannot use the portal | Pricelist `active`; `submission_method = email`; `system` comment captures email source + uploading staff |
| X-VPL-06 | Variance against active pricelist on GRN | Purchaser (active pricelist) → Receiver (GRN posts with price gap) → Finance (variance audit) → Purchaser (action) | Active pricelist; GRN unit price diverges beyond tolerance | Variance categorised; pricelist either `inactive` (if out-of-date) or `active` unchanged (if vendor over-bill or FX-only) |
| X-VPL-07 | Token revoked mid-flight | Purchaser (invite) → Vendor (in-progress draft) → Sysadmin (revoke) → Purchaser (re-issue or abandon) | Vendor has saved a draft; token compromised | Invitation `expired`; vendor portal access `401`; draft preserved for audit |
| X-VPL-08 | Auto-expire at campaign end | Purchaser (launch) → Vendor (no submission) → (cron auto-expire) | `end_date` passes with invitation still `pending` or `in-progress` | Invitation `expired`; token revoked; pricelist `(none)` or `draft` (preserved) |
| X-VPL-09 | Validation `quality_score` below threshold routes to Manager | Purchaser → Vendor → (validator scores low) → Purchasing Manager (review + decide) | Vendor's data is poor-quality but submitted | Either `active` with Manager override + on-file low score, or `draft + submitted_at = NULL` after rejection |
| X-VPL-10 | Auditor finds segregation violation; Manager remediates | Auditor (chain audit) → Manager (inactivate per audit recommendation) | High-value pricelist approved by the same user who edited rows | Pricelist `inactive`; audit case file closed; fresh campaign launched |
| X-VPL-11 | Sysadmin config change preserves in-flight snapshot | Sysadmin (changes RBAC mid-flight) → in-flight pricelist (continues under old snapshot) → new pricelist (uses new RBAC) | Pricelist mid-Manager-review at moment of save | In-flight pricelist activates under old RBAC; next new pricelist uses new RBAC |
| X-VPL-12 | Active pricelist correction via inactivate + new campaign | Purchaser (inactivate) → Purchaser (launch fresh campaign) → Vendor (re-submit) → Purchaser (approve) | Active pricelist found to contain an error after activation | Old pricelist `inactive` (historical); new pricelist `active`; downstream consumers fall over to the new one on next read |

## 5. E2E Test Mapping

No dedicated Playwright spec exists for the `vendor-pricelist` module today; the carmen/docs `tasks.md` lists pricelist E2E as a roadmap item. Coverage today is split across:

- **API / integration tests on the backend** — exercise template / campaign / pricelist CRUD, validation-engine output, portal-token middleware, and configuration-audit-log writes. Located under `../carmen-turborepo-backend-v2/apps/<service>/test/` once the vendor-pricelist service module is built; tracked in `tasks.md` § Implementation Tasks.
- **Cross-module E2E** — the `vendor-pricelist` interactions are exercised indirectly through the downstream-consumer specs:
  - `../carmen-inventory-frontend-e2e/tests/4*-pr*.spec.ts` — PR-line preferred-vendor defaulting and missing-pricelist coverage handling.
  - `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` and `402-po-purchaser-journey.spec.ts` — PO snapshot from active pricelist at PR-to-PO conversion + the From Price List wizard (TC-PO-060205..TC-PO-060208).
  - `../carmen-inventory-frontend-e2e/tests/4*-grn*.spec.ts` — GRN variance check at posting against active pricelist.
- **Vendor portal harness** — the secure portal under `app/(main)/vendor-portal/[token]/` (carmen/docs `design.md` § Phase 5) has its own harness layer for token-authenticated session testing; this is a separate test bed from the main Carmen E2E because the vendor portal is an unauthenticated public surface that uses token exchange.
- **Audit / configuration tests** — exercised at the API / integration level (cross-module audit and config services). Audit-log queries and configuration-management surfaces have no dedicated UI E2E.

Each persona test file's Section 5 notes "no dedicated vendor-pricelist E2E spec yet — see roadmap item in `tasks.md`" and cross-references the indirect coverage paths above. Where a scenario is exercised by a downstream-module spec, the persona file calls out the spec file and the relevant test-case id.

## 6. References

- `../carmen/docs/vendor-pricelist-management/tasks.md` — roadmap item: dedicated vendor-pricelist E2E spec; until completed, coverage runs through API / integration tests and downstream-consumer E2E.
- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` — `From Price List` wizard scenarios cover the read-side of pricelist consumption (TC-PO-060205..TC-PO-060208).
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts` — PR-to-PO conversion snapshot of active pricelist price; verifies `VPL_XMOD_003`.
- Sibling: [03-user-flow.md](./03-user-flow.md) § 4 (handoff source) — every cross-persona scenario in Section 4 maps to a handoff in this table.
- Sibling: [02-business-rules.md](./02-business-rules.md) § 5 (posting + transition rules), § 6 (cross-module rules `VPL_XMOD_001`–`VPL_XMOD_009`).
- Sibling: [01-data-model.md](./01-data-model.md) — entities, enums, unique constraints, and the divergence table that scenarios reference.
