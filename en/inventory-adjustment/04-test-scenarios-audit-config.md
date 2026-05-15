---
title: Inventory Adjustment — Test Scenarios — Audit / Config
description: Auditor and System Administrator test cases for inventory adjustments.
published: true
date: 2026-05-15T13:00:00.000Z
tags: inventory-adjustment, test-scenarios, audit, sysadmin, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Audit / Config

This page captures the test scenarios that the **Audit / Config** persona group — Auditor (read-only audit-trail inspection) and System Administrator (master-data and configuration CRUD) — drives in the `inventory-adjustment` module. Both roles are **non-transactional** in the document lifecycle: they don't raise, approve, edit, or void adjustment documents. Sysadmin scenarios are largely exercised by the E2E spec [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) (reason-code admin CRUD); Auditor scenarios are typically manual / planned audit-query patterns. Sections are grouped into **happy paths** (reason-code add/edit/deactivate, threshold change, audit-trail review, SoD compliance check, lot-recall trace, void-chain verification), **RBAC / permission** (configuration scope, read-only scope, sensitive-export approval), **validation** (Sysadmin master-data CRUD validation, audit-query input validation), and **edge cases** around configuration timing (apply prospectively, in-flight document inheritance), audit-export approval gates, and historical configuration snapshots.

## 1. Happy Path

### 1.1 System Administrator scenarios

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| AC-HP-01 | Sysadmin adds new reason code with GL-account mapping | Sysadmin `admin@blueledgers.com` logged in; new business case (insurance-claimable losses). | 1. Admin module → Master Data → Adjustment Types → New. 2. Enter `code = INSURANCE_WRITE_OFF`, `name = "Insurance Write-Off"`, `type = STOCK_OUT`, `description`. 3. Set `info.glAccount = "6535"`, `info.requiresDocument = true`, `info.requiresQualityCheck = true`. 4. Save. | New `tb_adjustment_type` row created; `@@unique([code, deleted_at])` enforced. Available in pickers for new documents immediately. Sysadmin audit log records the change. Maps to parent Scenario 19. Exercised by [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) `TC-AT-010005` (validation) / `TC-AT-010006` (create). |
| AC-HP-02 | Sysadmin edits an existing reason code | Existing `BREAKAGE` reason; Sysadmin updates `info.glAccount` from `"6510"` (general breakage) to `"6512"` (F&B-specific breakage) due to chart-of-accounts restructure. | 1. Admin module → Adjustment Types → Search "BREAKAGE". 2. Open the row. 3. Update `info.glAccount` to `"6512"`. 4. Save. | Updated row; new GL mapping applies prospectively to new submitted documents. Existing `completed` documents retain their original GL mapping via cost-layer snapshot pattern per `ADJ_XMOD_007`. Audit log records before/after. |
| AC-HP-03 | Sysadmin deactivates obsolete reason code | Existing `OLD_DATA_FIX` reason no longer in use after process change. | 1. Admin module → Adjustment Types → Search "OLD_DATA_FIX". 2. Toggle `is_active = false`. 3. Save. | Reason hidden from new-document pickers; remains readable on historical documents per `tb_adjustment_type.is_active`. Soft-delete (`deleted_at` non-null) is more aggressive — used if the reason was created in error; rare. |
| AC-HP-04 | Sysadmin changes auto-approve threshold | Tenant decides to raise auto-approve from `฿500` to `฿1,000`. | 1. Admin module → Thresholds. 2. Change auto-approve from `500` to `1000`. 3. Save with effective date. | Threshold applied prospectively at new submits per `ADJ_AUTH_002`. Existing `draft` documents inherit at submit time. Existing `in_progress` documents retain the threshold-routing they entered with. Audit-logged. |
| AC-HP-05 | Sysadmin assigns user-location scope | New Store Keeper `sk2@blueledgers.com` needs scope for `LOC-B` and `LOC-C`. | 1. Admin module → RBAC → User Locations. 2. Select `sk2@blueledgers.com`. 3. Add `LOC-B` and `LOC-C` to scope. 4. Save. | `tb_user_location` rows created. SK can now raise adjustments at those locations per `ADJ_AUTH_001`. |

### 1.2 Auditor scenarios

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| AC-HP-06 | Auditor reviews period adjustment trail | Auditor `audit@blueledgers.com`; period `2026-04` locked; external audit cycle. | 1. Audit module → Adjustment Trail → period `2026-04`. 2. Aggregate report renders: total stock-in, total stock-out, by reason, by location, by department, by user. 3. Drill into each high-cost item; verify approval signatures in `workflow_history`. 4. Compile audit findings. | Read-only data; no state change. Findings tracked in audit-report workflow (external). |
| AC-HP-07 | Auditor verifies SoD compliance | Period `2026-04`; SoD threshold configured at `฿5,000` per `ADJ_AUTH_010`. | 1. Audit module → SoD Compliance Report → `2026-04`. 2. Query joins `tb_stock_out` (`created_by_id`, lot) against `tb_good_received_note` (`created_by_id`, lot) for the same lot above SoD threshold. 3. Findings list flagged pairs. | Per `ADJ_AUTH_010` enforcement, violations should be zero (rejected at submit time). Historical pre-rule cases or rule-relaxed periods may surface; flagged for compliance follow-up. Maps to parent Scenario 20. |
| AC-HP-08 | Auditor runs lot-recall trace | Lot `LOT-2023-Q4` of `P-1` affected by recall; introduced by GRN, partially issued via SR, partially written off via `RECALL_WRITE_OFF` stock-out, with `tb_credit_note` amount adjustment applied. | 1. Audit module → Lot Recall Trace. 2. Enter `lot_no = LOT-2023-Q4`, `product_id = P-1`. 3. Forward trace: SR issues + stock-out write-offs + credit-note quantity rows. 4. Backward trace: originating GRN with vendor / cost / date. 5. Render chain-of-custody. | Both directions resolved via `tb_inventory_transaction` polymorphic join. Read-only; no state change. Maps to parent Scenario 21. |
| AC-HP-09 | Auditor verifies void chains | Period contains 5 `voided` `tb_stock_in` / `tb_stock_out` documents. | 1. Audit module → Void Chain Verification → `2026-04`. 2. For each `voided` doc, look up the compensating reversal via `info.voidsAdjustmentId`. 3. Verify the compensating doc is `completed` with reversed direction and same lines. 4. Findings list orphans (voided without compensating). | Per `ADJ_POST_004`, every `voided` should have a compensating reversal. Orphans flagged. Maps to parent Scenario 22. |
| AC-HP-10 | Auditor reviews specific document detail | Reactive: Finance flagged a posted document as anomalous. | 1. Audit module → Document Detail → `<si_no / so_no>`. 2. Full chain view: header, lines, attachments, `workflow_history`, resulting `tb_inventory_transaction` with cost-layer effect, GL journal. 3. Cross-check against reason code's `info.glAccount` at the time of post. | Read-only; no state change. Document detail with provenance. |
| AC-HP-11 | Auditor exports sensitive cost data (secondary approval) | Audit findings require export of cost-per-unit / vendor terms for the period. | 1. Audit module → Adjustment Trail → Export. 2. Click "Export sensitive fields". 3. System prompts for secondary-Auditor approval. 4. Second Auditor approves. 5. Export proceeds (CSV / PDF). | Per `ADJ_AUTH_009` audit pattern, sensitive-field export requires secondary approval. Both Auditors' identities recorded in export audit log. |

## 2. Permission / Authorization

### 2.1 System Administrator

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| AC-PERM-01 | Sysadmin CRUDs `tb_adjustment_type` | **Allow per `ADJ_AUTH_008`.** Master-data scope. |
| AC-PERM-02 | Sysadmin changes thresholds (auto-approve, Controller, Finance, SoD) | **Allow per `ADJ_AUTH_008`.** Applied prospectively. Audit-logged. |
| AC-PERM-03 | Sysadmin manages `tb_user_location` scope and RBAC | **Allow.** |
| AC-PERM-04 | Sysadmin attempts to raise / approve an adjustment | **Deny — configuration-only role.** Per `ADJ_AUTH_008` constraint. The Sysadmin role does not include Store Keeper / Controller / Finance create or approve authority. (In practice, a single user may hold multiple roles; this rule covers the Sysadmin-only assignment.) |
| AC-PERM-05 | Sysadmin attempts to modify a `completed` document | **Deny per `ADJ_VAL_013`.** Immutable; void via compensating reversal required (and the Sysadmin role doesn't have that authority). |
| AC-PERM-06 | Sysadmin attempts to retroactively change historical GL mapping | **Deny — forward-only.** Reason-code GL changes apply prospectively; historical `completed` documents retain their original mapping. To "correct" historical posts, void + compensating + new submission cycle is required (Controller / Finance authority). |

### 2.2 Auditor

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| AC-PERM-07 | Auditor reads any `tb_stock_in` / `tb_stock_out` / detail / comment / attachment | **Allow per `ADJ_AUTH_009`.** Full read scope including soft-deleted and voided documents. |
| AC-PERM-08 | Auditor reads `tb_inventory_transaction` / cost-layer ledger / GL journal entries | **Allow per [[inventory]] `INV_AUTH_009`** (same read pattern, joined). |
| AC-PERM-09 | Auditor attempts to edit, approve, or void a document | **Deny — read-only.** Auditor role has no write authority on adjustment documents. |
| AC-PERM-10 | Auditor exports non-sensitive aggregate (counts, totals by reason) | **Allow.** Standard read scope. |
| AC-PERM-11 | Auditor exports sensitive fields (cost-per-unit, vendor terms) | **Allow with secondary-Auditor approval.** Per `ADJ_AUTH_009`. Single-Auditor export blocked. Maps to AC-HP-11. |
| AC-PERM-12 | Auditor attempts to change reason-code or threshold configuration | **Deny — Sysadmin required.** Per `ADJ_AUTH_008`. |

## 3. Validation / Error

### 3.1 System Administrator

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| AC-VAL-01 | Reason-code uniqueness on `code` (`@@unique([code, deleted_at])`) | Sysadmin creates new `tb_adjustment_type` with `code = BREAKAGE` (already exists, not soft-deleted). | Reject with `"Reason code <BREAKAGE> already exists."` Soft-deleted rows do not conflict (unique scope includes `deleted_at`). Mirrors `tb_adjustment_type` Prisma unique constraint. |
| AC-VAL-02 | Missing required fields | Sysadmin creates new `tb_adjustment_type` without `code` or `name` or `type`. | Reject with field-specific error: `"Code is required."` / `"Name is required."` / `"Direction (type) is required."` Exercised by [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) `TC-AT-010005`. |
| AC-VAL-03 | Invalid `info.glAccount` | Sysadmin sets `info.glAccount = "9999"` for an account that doesn't exist in the chart of accounts. | Reject with `"GL account <9999> is not a valid account."` (Validation against the Finance chart-of-accounts integration.) |
| AC-VAL-04 | Threshold change with invalid value | Sysadmin sets auto-approve threshold = `-100` (negative) or > Controller threshold. | Reject with `"Auto-approve threshold must be positive and less than Controller threshold."` |
| AC-VAL-05 | Soft-deleting a reason with active in-flight documents | Sysadmin soft-deletes `tb_adjustment_type` row that has active (`draft` / `in_progress`) referencing documents. | Block soft-delete with `"Reason <code> is in use by <N> active documents; deactivate (is_active = false) or wait for documents to complete / cancel."` Soft-delete proceeds only when no active references exist. (Historical `completed` references are allowed — they snapshot the code.) |

### 3.2 Auditor

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| AC-VAL-06 | Lot-recall trace with non-existent lot | Auditor enters `lot_no = LOT-XYZ` that has no `tb_inventory_transaction_cost_layer` rows. | "No history found for lot LOT-XYZ at product <product>." Empty trace; no error. |
| AC-VAL-07 | Sensitive-export approval timeout | Second Auditor doesn't approve within tenant-configured window (e.g. 24h). | Export request expires; first Auditor must re-submit. Audit log records the expiry. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| AC-EDGE-01 | Reason-code config change during in-flight document | SK has a `draft` document with `adjustment_type_id = X`; Sysadmin updates `X.info.glAccount` between draft creation and SK submit. | Submit uses the **current** (updated) `info.glAccount`. The draft snapshot is the document's `adjustment_type_id` reference, not the `info` JSON content — that's resolved at post time. |
| AC-EDGE-02 | Reason-code direction change blocked | Sysadmin attempts to change `tb_adjustment_type.type` from `STOCK_IN` to `STOCK_OUT` on an existing reason. | **Block** — direction change would corrupt the picker filter for historical documents that referenced it; instead, deactivate the old reason and create a new one with the desired direction. (UI may surface this as a warning rather than a hard block, depending on tenant policy.) |
| AC-EDGE-03 | Threshold change effective-dated for next period | Sysadmin sets effective date = `2026-06-01`. | Change applies only to new submits on or after `2026-06-01`. Pre-date submits use the prior threshold. |
| AC-EDGE-04 | Configuration audit query — who changed what | Auditor queries the platform audit log for all `tb_adjustment_type` changes in a period. | Returns the list with actor, timestamp, before/after JSON. Cross-references with adjustment documents posted during the same window to assess impact. |
| AC-EDGE-05 | Recall-trace performance on a hot lot | Lot has 10,000+ downstream movements (issues, transfers, write-offs, credit-notes). | Trace query runs with appropriate indices on `tb_inventory_transaction_cost_layer.lot_no, lot_index` (`inventorytransactionclosingbalance_lotno_lot_index_u`); result paginated. Read-only; no state change. |
| AC-EDGE-06 | Void-chain verification with two-deep void | A compensating reversal is itself voided (parent IC-EDGE-07). | Trace renders three documents: original → comp → comp-of-comp. Auditor inspects the rationale chain; orphan-detection looks one level only (each `voided` paired with at least one comp). |
| AC-EDGE-07 | Sensitive-export approver self-approves | First Auditor attempts to use a second login to approve their own export. | **Deny** — secondary approver must be a different user from the first. Self-approval blocked at the auth layer. |
| AC-EDGE-08 | SoD-report performance on large period | Period with 50,000+ adjustment posts. | Report runs as scheduled job (offline); generates within tenant SLA (e.g. 30 min). Auditor downloads the result when ready. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — handoff scenarios where Audit/Config is the protagonist: 19 (Sysadmin reason-code add), 20 (Auditor SoD compliance), 21 (Auditor lot-recall), 22 (Auditor void-chain verification).
- User flow: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin primary 7-step CRUD flow for reason codes; Auditor primary 7-step trail-review flow and 4-step lot-recall flow; decision branches (soft-fail vs hard-fail audit findings, add vs modify reason, threshold scope).
- Business rules: [02-business-rules.md](./02-business-rules.md) — `ADJ_AUTH_008` (Sysadmin scope), `ADJ_AUTH_009` (Auditor read scope), `ADJ_AUTH_010` (SoD), `ADJ_VAL_001` (doc number unique pattern shared with reason-code uniqueness), `ADJ_VAL_002` (reason direction), `ADJ_VAL_010` (requiresDocument flag), `ADJ_POST_004` (void chain).
- E2E specs: [`../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — canonical Sysadmin CRUD spec (TC-AT-010001..n covering list / search / pagination / create / edit / activate-toggle / validation / security cases). Fixture user `admin@blueledgers.com`.
- Cross-link: [[inventory]] — `INV_AUTH_008` (Sysadmin configuration spans location-type / costing-method / period definitions in addition to adjustment-type); `INV_AUTH_009` (Auditor read scope spanning all inventory data).
- Cross-link: [[good-receive-note]] — Auditor lot-recall trace pattern mirrors [[good-receive-note/04-test-scenarios-audit-config]] approach.
- Cross-link: [[physical-count]] / [[spot-check]] — variance-rollup adjustments cross-checked by Auditor for reasonableness and SoD compliance.
