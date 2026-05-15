---
title: Inventory Adjustment — Test Scenarios — Finance
description: Finance's test cases (happy path, permission, validation, edge cases) for inventory adjustments.
published: true
date: 2026-05-15T13:00:00.000Z
tags: inventory-adjustment, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Finance

This page captures the test scenarios that the Finance persona directly drives in the `inventory-adjustment` module. Finance owns **cost-impact and GL-mapping verification**: approving above-Controller-threshold adjustments (large recall / damage / theft write-offs), verifying the resolved `info.glAccount` matches the chart of accounts, reconciling inventory sub-ledger against GL at period close, and signing off on period-end adjustment activity ahead of Finance Manager's `tb_period.status` close per [[inventory]] `INV_AUTH_006`. Scenarios are grouped into **happy paths** (large-cost approval, GL-mapping verification, period-end review and sign-off, void initiation), **RBAC** (Finance scope vs Controller / Finance-Manager scope), **validation** (re-checked rules at approval), and **edge cases** around recovery routing, period-reopen scenarios, cost-anomaly investigation.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| FN-HP-01 | Approve Controller-forwarded recall write-off (large cost) | Finance `finance@blueledgers.com` logged in; Controller-forwarded `tb_stock_out` at `doc_status = in_progress`, reason `RECALL_WRITE_OFF`, total `฿85,000` (above Controller threshold `฿10,000`); recall notice attached; lots match notice. | 1. Open Finance Approval queue. 2. Open document. 3. Verify recall context: vendor notice, lot numbers, geographic scope match. 4. Verify FIFO cost-pick `฿42.50` from `LOT-2023-Q4` against GRN cost history and [[vendor-pricelist]] — within range. 5. Verify `info.glAccount` resolves to `6540 — Product Recall Loss` (active in current period). 6. Verify `dimension.department` matches the responsible cost-centre. 7. Click **Approve**. | `tb_stock_out.doc_status = in_progress → completed` per `ADJ_POST_002`. Outbound `tb_inventory_transaction`; cost-layer rows (FIFO, multi-row if spanning lots); GL `Dr 6540 Product Recall Loss ฿85,000 / Cr Inventory ฿85,000`. `workflow_history` records `finance_approved`. Maps to parent Scenario 3. |
| FN-HP-02 | Reject due to GL-mapping issue | Controller-forwarded `tb_stock_out` reason `BREAKAGE` (`info.glAccount = "6510"`), but the document concerns a vendor-recall scenario where the correct reason is `RECALL_WRITE_OFF` (`6540`). | 1. Open document. 2. Notice the reason / scenario mismatch. 3. Click **Reject** with comment "Reason should be `RECALL_WRITE_OFF`, not `BREAKAGE` — different GL account". | Document returns to `draft` for Store-Keeper edit + Controller re-forward with corrected reason. Finance does not directly override the reason; the document re-cycles through the threshold ladder with the correct classification. |
| FN-HP-03 | Send-back to Controller for additional evidence | Controller-forwarded `tb_stock_out` lacks insurance-claim reference; reason is `THEFT_WRITE_OFF` (large cost). | 1. Open document. 2. Comment "Insurance claim reference required before approval; confirm with security incident report." 3. Click **Send back to Controller**. | Document stays `in_progress`; Controller re-engages, requests Store Keeper to attach insurance reference, Controller re-forwards. |
| FN-HP-04 | Approve with parallel credit-note flow | Recall write-off with parallel vendor-credit recovery in flight via [[good-receive-note]] credit-note module. | 1. Open document. 2. Verify the parallel credit-note `tb_credit_note` exists and is approved. 3. Approve the adjustment write-off at full cost (the credit-note recovers the cost separately as a reduction in AP). 4. Optional: comment cross-linking the credit-note for audit. | `tb_stock_out.doc_status = completed`; inventory effect applied. The credit-note separately posts `Dr AP / Cr <vendor-recovery account>`. Net P&L impact = write-off less recovery. |
| FN-HP-05 | Period-end review and sign-off (happy path) | All `completed` adjustments in `2026-04` period; aggregate variance vs GL Inventory control = `฿0` (within tolerance); no flagged anomalies. | 1. Open Period-end Review for `2026-04`. 2. Review per-reason cost-impact aggregate (totals match expected operational range). 3. Verify reconciliation passes (variance ≤ tolerance). 4. No outliers flagged. 5. Click **Period Approve**. | Period adjustment activity approved by Finance. Finance Manager (same user or different) performs `tb_period.status = open → closed` per [[inventory]] `INV_AUTH_006`. Period close cascades the inventory-side `INV_POST_009` / `INV_POST_010` per [[inventory]]. |
| FN-HP-06 | Initiate void on previously-posted adjustment | `completed` `tb_stock_in` from prior week identified post-fact as duplicate (the same vendor-replacement event was reported twice by two SKs). | 1. Finance opens the duplicate. 2. Click **Void** → Create compensating reversal. 3. Compensating `tb_stock_out` form pre-fills with `info.voidsAdjustmentId = <original_id>`. 4. Finance approves directly (Finance authority covers compensating reversal). 5. Compensating posts; original `doc_status = voided`. | Per `ADJ_POST_004` two-step. On-hand restored to pre-duplicate state. Original inventory transaction NOT edited per [[inventory]] `INV_POST_012`. Auditor inspects void-chain per `ADJ_AUTH_009` (and FN-HP-08-equivalent in audit-config). |
| FN-HP-07 | Approve direct-cost-impact-flagged adjustment | Anomaly alert fires on a posted adjustment (cost-per-unit > 3× 90-day vendor avg); reactive review entry. | 1. Open the alert / adjustment detail. 2. Investigate the cost-layer history: prior receipt at high price during supply shock; cost is defensible. 3. Annotate finding in comment; close the anomaly flag. | No state change on the adjustment itself (already `completed`); Finance review documented in comment. Anomaly resolved with annotation. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| FN-PERM-01 | Approve above-Controller-threshold `in_progress` documents | **Allow per `ADJ_AUTH_005`.** Finance is the third signature in the threshold ladder; covers above-Controller-threshold adjustments. |
| FN-PERM-02 | Approve below-Controller-threshold documents directly | **Allow (over-approval).** Finance can approve any threshold tier (acts as a higher authority). Typical flow has Controller approving below-Controller-threshold; Finance approving below-Controller-threshold is rare but permitted (e.g. Controller out of office). |
| FN-PERM-03 | Finance attempts to edit `completed` document | **Deny per `ADJ_VAL_013`.** Must use void + compensating reversal. |
| FN-PERM-04 | Finance configures `tb_adjustment_type` or thresholds | **Deny — Sysadmin required.** Per `ADJ_AUTH_008`. Finance can request configuration changes but not execute them. |
| FN-PERM-05 | Finance performs `tb_period.status = closed → locked` | **Deny — Finance Manager required.** Per [[inventory]] `INV_AUTH_006`, period close / lock requires Finance Manager (a distinct elevated role; some tenants assign to the same user). The adjustment-module Finance role signs off the adjustment-side of period end; Finance Manager fires the period-status transition. |
| FN-PERM-06 | Finance void initiates compensating reversal | **Allow per `ADJ_AUTH_007` / `ADJ_POST_004`.** Finance can initiate void on any `completed` document (same as Inventory Controller). |
| FN-PERM-07 | Finance creates a new adjustment directly | **Allow.** Finance has create authority (any role above Store Keeper can create); typical use is the `DATA_FIX` reason for sub-ledger / GL reconciliation correction. |
| FN-PERM-08 | Finance attempts to back-post into a `closed` period | **Deny per `ADJ_VAL_011` / [[inventory]] `INV_VAL_008`.** Re-open is Finance Manager scope per [[inventory]] `INV_AUTH_006`. Finance requests re-open; Finance Manager grants if exceptional. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| FN-VAL-01 | Approve fails on stale on-hand (`ADJ_VAL_012`) | Document at Finance approval; another posting consumed from the lot leaving insufficient on-hand. | Same as IC-VAL-01: live recheck rejects approval; document returns to `draft`; Store Keeper re-picks. |
| FN-VAL-02 | Approve fails on closed period (`ADJ_VAL_011`) | Period closes between Controller forward and Finance approval. | Rejection per [[inventory]] `INV_VAL_008`; Finance can request Finance Manager re-open or coordinate current-period restatement. |
| FN-VAL-03 | Approve fails on inactive GL account | Resolved `info.glAccount` references a GL account locked for the document's date (e.g. retired during chart-of-accounts restructure). | Rejection at approval with `"GL account <code> is not active for the document date."` Finance coordinates with Sysadmin to update the reason-code's GL mapping; document returns to `draft` (or re-cycles after Sysadmin fix). |
| FN-VAL-04 | Period-end approve fails on sub-ledger / GL variance | Reconciliation variance > tolerance. | Sign-off blocked with `"Inventory sub-ledger and GL Inventory control account differ by ฿<X>; investigate before sign-off."` Finance investigates, posts corrective `DATA_FIX` adjustment, re-runs reconciliation. |
| FN-VAL-05 | Period-end approve fails on outstanding count-variance hold | Controller has not signed off open count-variance items per parent Scenario 18. | Sign-off blocked with `"Inventory Controller has not signed off variances for the period."` Finance communicates the hold; Controller resolves; Finance re-runs. Maps to parent Scenario 18. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| FN-EDGE-01 | Finance approves at exact Controller threshold boundary | Document cost `฿10,000.00` exactly. | **Controller could have approved; Finance also can (over-approval).** Activity log shows Finance as approver. |
| FN-EDGE-02 | Multi-reason document forwarded by Controller | A single multi-line document with mixed reasons (`BREAKAGE` × 2 lines, `EXPIRY_WRITE_OFF` × 1 line). | Finance verifies GL mapping per line — each line's reason resolves to its own `info.glAccount`. Approval posts a single inventory transaction with multiple details; multiple cost-layer rows; multiple GL credit / debit lines. |
| FN-EDGE-03 | Period reconciliation tolerance applied | Tenant has ±`฿1.00` rounding tolerance configured; variance = `฿0.75`. | Reconciliation passes (within tolerance); sign-off proceeds. Variance > `฿1.00` triggers `FN-VAL-04` block. |
| FN-EDGE-04 | Period re-open after close (Finance Manager scope) | External audit identifies missing adjustment in `2026-03` (closed); Finance Manager re-opens. | Finance Manager fires `tb_period.status = closed → open` per [[inventory]] `INV_AUTH_006`. Audit-grade justification logged. Finance raises corrective adjustment in re-opened period; submits / approves. Finance Manager re-closes before next regular period close. Maps to parent Scenario covered indirectly. |
| FN-EDGE-05 | Currency rounding outlier on FIFO multi-row | Stock-out for qty 7 spanning 3 lots at different costs; total computed at full 5dp; sum of 2dp-rounded line totals differs from 2dp-rounded grand total by `฿0.01`. | Finance accepts the rounding-residual within `ADJ_CALC_011` tolerance; ledger stores 5dp on each row so the audit trail is precise; display 2dp may show the cent residual on the rolled-up view. |
| FN-EDGE-06 | Cost anomaly alert on a duplicate-post candidate | Posted adjustment with cost outside historical range; Finance investigates and identifies it as a duplicate-post (already covered by another adjustment for the same event). | Finance initiates void via compensating reversal per FN-HP-06; original moves to `voided`. Anomaly resolved. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — handoff scenarios where Finance is the protagonist: 3 (above-Controller-threshold approval), 13 (void initiation by Finance), 18 (period-end variance hold).
- User flow: [03-user-flow-finance.md](./03-user-flow-finance.md) — primary 10-step approval flow; period-end review flow; decision branches (cost-anomaly approve/reject/send-back, recovery routing, period close tolerance, re-open scope).
- Business rules: [02-business-rules.md](./02-business-rules.md) — `ADJ_AUTH_005` (Finance approval), `ADJ_AUTH_007` (Finance void), `ADJ_POST_002` (post fan-out), `ADJ_POST_004` (void), `ADJ_XMOD_007` (Finance / GL reconciliation).
- E2E specs: [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — period-end approval gate, variance hold, re-open scenarios. Finance fixture user `finance@blueledgers.com`.
- Cross-link: [[inventory]] — `INV_AUTH_005` (Finance approval scope), `INV_AUTH_006` (Finance Manager period transitions), `INV_XMOD_008` (inventory-to-GL reconciliation).
- Cross-link: [[good-receive-note]] — Finance may chain credit-note flow for vendor-recall recovery against the originating GRN.
- Cross-link: [[vendor-pricelist]] — cost-anomaly historical reference.
- Cross-link: [[costing]] — FIFO / WA cost picks Finance verifies on outbound adjustments.
