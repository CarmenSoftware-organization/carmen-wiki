---
title: การคำนวณต้นทุน — Test Scenarios — Finance
description: Test cases ของ Finance (valuation policy, อนุมัติ credit-note revaluation, sub-ledger ↔ GL reconciliation, period-end valuation, period lock) สำหรับ costing
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน — Test Scenarios — Finance

> **At a Glance**
> **Persona:** Finance (Officer / Cost Controller + Finance Manager) &nbsp;·&nbsp; **Module:** [[costing]] &nbsp;·&nbsp; **Scenarios:** ~34
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** map ไปยัง `601-cn.spec.ts`, `900-period-end.spec.ts`, `501-grn.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้จับ test scenarios ที่ persona Finance (Finance Officer / Cost Controller สำหรับ policy ประจำวันและ reconciliation, บวก Finance Manager สำหรับ period-lock authority) ขับเคลื่อนโดยตรงในโมดูล `costing` Finance คือ valuation authority — role ที่เป็นเจ้าของนโยบาย `tb_business_unit.calculation_method`, การเลือก `enum_physical_count_costing_method`, cadence `tb_product.standard_cost`, reconciliation tolerance, การอนุมัติ credit-note-amount revaluation per `COST_AUTH_005`, sub-ledger ↔ GL reconciliation per `COST_XMOD_009`, period-end valuation orchestration per `COST_POST_007` / `COST_POST_008`, และ (ที่ Finance Manager level) `closed → locked` advance per `COST_AUTH_006` Finance **ไม่** แก้ `cost_per_unit` โดยตรง per `COST_AUTH_010`; cost revaluation flows ผ่าน credit-notes, compensating stock-in / stock-out, หรือ period-end rollforward

Scenarios group เป็น **happy paths** (credit-note approval, reconciliation pass, period close + open-next, period lock, method change after drain), **RBAC** (Finance Officer vs Finance Manager vs Sysadmin), **validation** (reconciliation above tolerance, close-with-open-credit-notes, method-change-with-on-hand, credit-note revaluation drives lot cost negative) และ **edge cases** (FX revaluation at period end, multi-period reconciliation, locked-period restatement, standard-cost cadence boundary)

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| FIN-HP-01 | อนุมัติ credit-note-amount revaluation (vendor concession) | `committed` GRN exists with `LOT-X` at `cost_per_unit = ฿14.00`, `qty = 50`, `total_cost = ฿700.00`; vendor concedes `฿100.00` reduction; credit-note `pending`; Finance Officer logged in | 1. เปิด credit-note approval queue 2. เปิด credit-note เฉพาะ; review evidence 3. ยืนยัน post-revaluation cost preview: `new_cost_per_unit = (700 + (−100)) / 50 = ฿12.00` 4. คลิก **Approve** | Credit-note `doc_status = approved`; `INV_POST_007` fires; `COST_POST_003` writes cost-layer row ใหม่ที่ `(LOT-X)`: `in_qty = 0, out_qty = 0, diff_amount = −฿100.00`. `LOT-X` `cost_per_unit` recalculated เป็น `฿12.00` per `COST_CALC_005`. GL: Dr AP `฿100.00` / Cr Inventory `฿100.00` Map ไปยัง parent Scenario 3 |
| FIN-HP-02 | Sub-ledger ↔ GL reconciliation pass within tolerance | Current open period `2026-05`; tolerance = `฿1.00`; Sub-ledger sum for `LOC-A`: `฿100,234.56`; GL Inventory net change for `LOC-A` = `฿100,234.00` (variance `฿0.56`) | 1. เปิด reconciliation dashboard 2. Review per-location summary 3. ยืนยัน `LOC-A` variance `฿0.56 ≤ ฿1.00` 4. คลิก **Mark reconciliation clean for 2026-05 (LOC-A)** | Reconciliation clean recorded; activity log: `{ event: 'reconciliation_clean', period: '2026-05', location: 'LOC-A', variance: '฿0.56' }`. ไม่มี journal posted |
| FIN-HP-03 | Reconciliation variance above tolerance — missed credit-note revaluation GL leg | `LOC-A` variance `฿100.00`; drill identifies `credit_note_amount` revaluation ที่ post ไป cost-layer ถูกต้องแต่ GL journal missed | 1. เปิด reconciliation drill for `LOC-A` 2. ระบุ credit-note `CN-X` 3. Post compensating GL journal: `Dr Inventory ฿100.00 / Cr GRN Clearing ฿100.00` 4. Re-run reconciliation; variance ตกต่ำกว่า tolerance 5. Mark clean | Compensating GL journal posted; reconciliation passes; activity log บันทึก resolution. Cost-layer ledger ไม่เปลี่ยน Map ไปยัง parent Scenario 14 |
| FIN-HP-04 | Period-end close — FIFO business unit | Closing period `2026-04`; FIFO business unit with residual lots; Controller signed off variance; reconciliation clean; ทุก source documents terminal | 1. เปิด period-end orchestration dashboard for `2026-04` 2. ยืนยัน pre-close checklist clear 3. ยืนยัน cost-layer-to-snapshot rollup preview 4. คลิก **Close period 2026-04** | `INV_POST_009` + `COST_POST_007` run: `tb_period_snapshot` rows written per `(period_id, location_id, product_id, lot_no, lot_index)` per `COST_CALC_006`; `close_period` cost-layer rows write Chained `COST_POST_008` writes `open_period` cost-layer rows for `2026-05` carrying `lot_seq_no` from closed lots per `COST_CALC_007`. `tb_period.status = open → closed` on `2026-04` Map ไปยัง parent Scenario 5 |
| FIN-HP-05 | Period-end close — WA business unit | เหมือน FIN-HP-04 แต่ WA business unit | Steps เหมือนกัน | Snapshot row per `(location, product)` carrying `closing_cost_per_unit = current_running_average`; single `open_period` cost-layer row per `(location, product)` opening `2026-05` Map ไปยัง parent Scenario 6 |
| FIN-HP-06 | Period close blocked by open credit-note | Closing period `2026-04`; `tb_credit_note` หนึ่ง at `pending` with transaction date in `2026-04` | 1. เปิด period-end dashboard 2. ยืนยัน pre-close checklist (red flag on open credit-note) 3. คลิก **Close period 2026-04** | **Reject at close** — server returns `"Cannot close period 2026-04: 1 credit-note remains at pending. Resolve before closing."` Period stays `open` |
| FIN-HP-07 | Finance Manager locks closed period | `2026-03` at `tb_period.status = closed`; 60-day audit window passed; external audit signed off; Finance Manager logged in | 1. เปิด period-lock dashboard 2. Filter ไป `2026-03` 3. ยืนยัน audit sign-off 4. คลิก **Lock period 2026-03** | `tb_period.status = closed → locked`; `tb_period_snapshot.closing_cost_per_unit` / `closing_total_cost` permanent immutable for `2026-03`; ไม่มี re-open path Map ไปยัง parent Scenario 5 + 6 lock leg |
| FIN-HP-08 | Standard-cost monthly cadence update | Tenant's monthly standard-cost batch; N products with cost updates; tenant has `enum_physical_count_costing_method = standard` | 1. เปิด standard-cost batch interface 2. Upload / enter updated `standard_cost` per product 3. Save | `tb_product.standard_cost` updated per product; configuration-history written; **ไม่มี cost-layer effect** per `COST_POST_010` Map ไปยัง parent Scenario 9 |
| FIN-HP-09 | Calculation-method change after drain | Business unit `BU-A` at `calculation_method = average` with non-zero on-hand; Finance coordinates drain; confirmed zero on-hand; Sysadmin re-attempts change ไป `fifo` | 1. Finance ยืนยัน drain complete 2. Sysadmin saves `calculation_method = fifo` 3. Configuration-history entry | `tb_business_unit.calculation_method = fifo` persisted; subsequent inbound assigns `lot_seq_no`; subsequent outbound consumes FIFO Map ไปยัง parent Scenario 8 |
| FIN-HP-10 | Period re-open for audit-flagged revaluation in closed period | Period `2026-04` at `closed` within audit window; external audit identifies vendor credit-note that should have revalued `LOT-Y` in `2026-04`; Finance Manager re-opens | 1. เปิด period orchestration for `2026-04` 2. คลิก **Re-open period 2026-04** 3. Enter justification 4. Confirm | `tb_period.status = closed → open`; Finance approves credit-note; `COST_POST_003` writes revaluation; `LOT-Y` cost recalculated; Finance re-runs close → re-writes `tb_period_snapshot`; period re-closes Map ไปยัง parent Scenario 15 |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| FIN-PERM-01 | Finance Officer อนุมัติ credit-note-amount revaluation | **Allow per `COST_AUTH_005`** Finance อนุมัติ; engine fires revaluation ภายใต้ system context |
| FIN-PERM-02 | Finance Officer รัน reconciliation และ post compensating GL journals | **Allow per `COST_XMOD_009`** Reconciliation read scope + GL journal post เป็น Finance-Officer rights |
| FIN-PERM-03 | Finance Officer พยายาม lock period | **Deny — Finance Manager only per `COST_AUTH_006`** ปุ่ม **Lock** ซ่อนสำหรับ Finance Officer; API returns `"Period lock requires the Finance Manager role."` |
| FIN-PERM-04 | Finance Manager re-opens closed period | **Allow พร้อม audit log per `COST_AUTH_006` / `INV_AUTH_006`** Justification required; re-open audit-logged Locked periods ไม่สามารถ re-open |
| FIN-PERM-05 | ใครก็ตามพยายาม re-open locked period | **Deny per `COST_AUTH_006`** Server returns `"Period <YYMM> is locked; locked periods cannot be re-opened by any role."` |
| FIN-PERM-06 | Finance Officer พยายาม edit `cost_per_unit` บน posted cost-layer row | **Deny — immutable per `COST_AUTH_010`** API call returns `"Cost-layer rows are immutable. Use credit-note-amount or compensating adjustment for cost corrections."` |
| FIN-PERM-07 | Finance Officer พยายามเปลี่ยน `tb_business_unit.calculation_method` | **Deny — Sysadmin only per `COST_AUTH_001`** Finance เป็น requester / coordinator; Sysadmin executes |
| FIN-PERM-08 | Finance Officer อัปเดต `tb_product.standard_cost` (in-app batch interface) | **Allow per Finance / cost-control authority** — RBAC underlying สำหรับ `tb_product` writes ตั้งค่าให้ Finance มี `standard_cost` write scope |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| FIN-VAL-01 | อนุมัติ credit-note revaluation ที่จะขับ lot cost ติดลบ | Credit-note `diff_amount = −฿1,000.00` on `LOT-Z` (original `total_cost = ฿700`, qty 50); revaluation จะผลิต `new_cost_per_unit = (700 − 1000)/50 = −฿6.00` | **Reject at approve** per `COST_VAL_004`: server returns `"Credit-note-amount revaluation would drive cost_per_unit below zero (calculated: −฿6.00). Reject or reduce diff_amount."` |
| FIN-VAL-02 | Reconciliation marked clean with above-tolerance variance | Finance Officer คลิก **Mark clean** บน `LOC-A` variance `฿250.00` (เหนือ `฿1.00` tolerance) | **Reject at mark-clean** — server returns `"Variance ฿250.00 exceeds tolerance ฿1.00; resolve via compensating journal or corrective adjustment before marking clean."` |
| FIN-VAL-03 | Period close attempted with `in_progress` source documents | Period `2026-04` close attempted while `tb_credit_note` at `pending` | **Reject at close** per FIN-HP-06 logic — server returns `"Cannot close period 2026-04: <N> source documents at non-terminal state."` |
| FIN-VAL-04 | Period close without Controller variance sign-off | เหมือน inventory module — Finance คลิก close ขณะ Controller ยังไม่ signed off | **Reject at close** — server returns `"Inventory Controller has not signed off variance review."` |
| FIN-VAL-05 | Period close with unresolved cost-layer-to-snapshot rollup gap | Cost-layer rollup preview shows key with null `closing_cost_per_unit` | **Reject at close** per `COST_VAL_008` — server returns `"Cannot rollforward period <YYMM>: closing snapshot for <N> (location, product, lot) keys is missing or has null closing_cost_per_unit."` |
| FIN-VAL-06 | Method change submitted with non-zero on-hand | Finance / Sysadmin attempts `calculation_method` change on business unit with `Σ on-hand > 0` | **Reject at impact preview** per `COST_VAL_009` — server returns `"Cannot change calculation_method on business unit <code>: <N> products have non-zero on-hand. Drain stock or run elevated migration."` Map ไปยัง parent Scenario 7 |
| FIN-VAL-07 | Standard-cost update entered as negative | Finance enters `standard_cost = −฿5.00` for product | **Reject at save** — shape validation `"standard_cost must be non-negative."` |
| FIN-VAL-08 | Lock attempted with open audit-correction requests | Finance Manager attempts to lock `2026-04` (closed) while one open audit-correction request remains | **Reject at lock** — server returns `"Cannot lock period 2026-04: 1 open audit-correction request remains."` |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| FIN-EDGE-01 | Credit-note revaluation drives lot cost exactly to zero | Credit-note `diff_amount = −฿700` on `LOT-Z` (original `total_cost = ฿700`, qty 50); revaluation produces `cost_per_unit = ฿0.00` | **Allow — boundary inclusive** `≥ 0` passes `COST_VAL_004` Lot's cost `฿0.00`; subsequent FIFO consumption from lot at `฿0.00` (free goods) |
| FIN-EDGE-02 | Reconciliation variance exactly at tolerance | Variance `฿1.00` exactly equals tolerance `฿1.00` | **Boundary inclusive — clean** `≤ tolerance` is clean |
| FIN-EDGE-03 | FX revaluation at period end (multi-currency inventory) | Foreign-currency-sourced lot; FX rate at period close differs from receipt-time FX | **Snapshot ใช้ receipt-time cost; FX revaluation เป็น separate GL journal** `tb_period_snapshot.closing_cost_per_unit` ใช้ cost-layer's `cost_per_unit` (บันทึกใน base currency at receipt-time FX) |
| FIN-EDGE-04 | Multi-period reconciliation (prior period still open) | `2026-03` และ `2026-04` ทั้งคู่ `open` | **Allow reconciliation on current period; close order enforced** Sub-ledger sums per period scoped on `at_period` (`YYMM`) |
| FIN-EDGE-05 | Locked-period correction via current-period restatement | `2026-03` is `locked`; auditor identifies missed cost-impact; Finance posts corrective adjustment with current date in `2026-05` referencing `2026-03` | **Posts cleanly in `2026-05`** Transaction date `2026-05`; `note` field links back to `2026-03` |
| FIN-EDGE-06 | Concurrent credit-note approvals on different lots of same product | Officer A approves `CN-1` for `LOT-X` at `T`; Officer B approves `CN-2` for `LOT-Y` at `T+200ms` | **Both succeed; no contention** Each revaluation writes distinct cost-layer row |
| FIN-EDGE-07 | Standard-cost update at period boundary | Finance updates `tb_product.standard_cost` บน last day of `2026-04` ที่ `23:55`; count-variance ที่ `2026-04-30 23:59` posts | **Snapshot rule — count-variance reads `standard_cost` at post time** `enum_physical_count_costing_method = standard` resolves ไปยังค่าที่ใช้งานที่ post timestamp |
| FIN-EDGE-08 | Decimal precision in `diff_amount` aggregation | Credit-note revaluation `diff_amount = −฿0.00001` (5dp full precision); aggregation across thousands of revaluation rows | **Per-row 5dp; aggregate rounded to 2dp; absorbed into reconciliation tolerance per `COST_CALC_010`** |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-finance.md](./03-user-flow-finance.md)
- Business rules: [02-business-rules.md](./02-business-rules.md)
- Sibling: [04-test-scenarios-inventory-controller.md](./04-test-scenarios-inventory-controller.md)
- Sibling: [04-test-scenarios-auditor.md](./04-test-scenarios-auditor.md)
- E2E specs: [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts), [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts), [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts)
- Cross-link: [[inventory/04-test-scenarios-finance]]
- Cross-link: [[good-receive-note]]
- Cross-link: [[inventory-adjustment]]
- Cross-link: credit-note
