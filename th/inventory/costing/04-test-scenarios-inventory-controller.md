---
title: การคำนวณต้นทุน (Costing) — Test Scenarios — Inventory Controller
description: Test cases ของ Inventory Controller (ทบทวน cost-pick preview, new-lot cost basis, ตรวจสอบ variance, triage cost anomaly) สำหรับ costing
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller &nbsp;·&nbsp; **Module:** [[costing]] &nbsp;·&nbsp; **Scenarios:** ~27
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** map ไปยัง `501-grn.spec.ts`, `701-sr.spec.ts`, `720-stock-issue.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้จับ test scenarios ที่ persona Inventory Controller ขับเคลื่อนโดยตรงในโมดูล `costing` Controller เป็นเจ้าของ engine-input cleanliness: lot dates และ `lot_seq_no` assignment correctness, receipt costs, adjustment cost bases (cost บน `tb_stock_in` สำหรับ new lots, picked cost บน `tb_stock_out` สำหรับ outbound), และ waste write-off cost basis Review **cost-pick preview** บน adjustment approval ทุก approval (FIFO walk vs WA current average per `COST_AUTH_007`) ตรวจสอบ new-lot cost basis เทียบ vendor pricelists / `tb_product.price_deviation_limit` ตรวจสอบ valuation variances ที่ Finance surface และ triage cost anomalies เชิงรุก

Controller **ไม่** อนุมัติ credit-note revaluations (Finance per `COST_AUTH_005`) **ไม่** advance period state (Finance Manager per `COST_AUTH_006`) **ไม่** configure `calculation_method` (Sysadmin per `COST_AUTH_001`) และไม่เคยแก้ cost-layer rows โดยตรง per `COST_AUTH_010`

Scenarios group เป็น **happy paths**, **RBAC**, **validation** และ **edge cases**

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | อนุมัติ FIFO outbound ข้ามสอง lots — cost-pick preview matches | FIFO business unit; product `P-1` at `LOC-A` with 2 lots: `LOT-1 (lot_seq_no=1, cost ฿10, remaining 20)`, `LOT-2 (lot_seq_no=2, cost ฿14, remaining 50)`; Store Keeper raises `tb_stock_out` for `qty = 30`. Cost-pick preview: 20 units from `LOT-1` at `฿10` + 10 units from `LOT-2` at `฿14` = `฿340`. Controller logged in | 1. เปิด adjustment approval queue 2. เปิด document; review cost-pick preview (two-row FIFO walk) 3. ยืนยันว่า walk ตรงกับ expected lot rotation 4. คลิก **Approve** | `tb_stock_out.doc_status = completed`; outbound `tb_inventory_transaction` เดียว; outbound cost-layer rows **2 แถว** per `COST_POST_002` / `COST_CALC_001`: row 1 (`out_qty=20, cost=฿10, from_lot_no=LOT-1`), row 2 (`out_qty=10, cost=฿14, from_lot_no=LOT-2`). `LOT-1` fully drained; `LOT-2` remaining = 40. GL: Dr Department Expense `฿340.00` / Cr Inventory `฿340.00` Map ไปยัง parent Scenario 1 |
| IC-HP-02 | อนุมัติ WA outbound at current running average | WA business unit; product `P-1` at `LOC-A` with on-hand 100 units, `average_cost_per_unit = ฿11.33333`; Store Keeper raises stock-out for 30 units. Cost-pick preview: `cost_per_unit = ฿11.33333` (single row) | 1. เปิด document; review cost-pick preview 2. ยืนยัน average ตรงกับประวัติ inbound ล่าสุด 3. คลิก **Approve** | `tb_stock_out.doc_status = completed`; outbound cost-layer row เดียว per `COST_POST_002` / `COST_CALC_002`: `out_qty = 30, cost_per_unit = ฿11.33333, total_cost = ฿340.00`. Average ไม่เปลี่ยน On-hand reduced เป็น 70 units at `฿11.33333` |
| IC-HP-03 | อนุมัติ new-lot stock-in — cost within vendor-pricelist tolerance | FIFO business unit; new-lot stock-in for `LOT-NEW` at `LOC-A`, `P-1`, qty 10, cost `฿15.50`; vendor pricelist last-price `฿15.00`; product `price_deviation_limit = 10%`. Deviation `+฿0.50` within tolerance | 1. เปิด new-lot review queue 2. เปิด document; cross-reference vendor pricelist 3. ยืนยัน `฿15.50 / ฿15.00 = 1.033 ≤ 1.10` 4. คลิก **Approve** | `tb_stock_in.doc_status = completed`; inbound cost-layer row per `COST_POST_001`: `in_qty = 10, cost_per_unit = ฿15.50, lot_no = LOT-NEW, lot_index = 1, lot_seq_no = (max + 1)`. `average_cost_per_unit` shadow recomputed per `COST_CALC_003` |
| IC-HP-04 | ปฏิเสธ anomalous-cost stock-out (FIFO stale-lot consumption) | FIFO business unit; product `P-1` at `LOC-A` has 6-month-old `LOT-1 (lot_seq_no=1, cost ฿20)` plus recent lots at `฿15`; Store Keeper raises stock-out for breakage; cost-pick preview shows FIFO consuming `LOT-1` at `฿20`. Vendor pricelist current `฿15`. Controller suspect rotation issue | 1. เปิด document; review cost-pick preview 2. ระบุ `LOT-1` เป็น stale high-cost 3. คลิก **Reject** พร้อมคอมเมนต์ | Document `doc_status = in_progress → draft`; คอมเมนต์ของ Controller บน activity log; ไม่มี cost-layer row written Map ไปยัง parent Scenario 10 |
| IC-HP-05 | ตรวจสอบ Finance-flagged variance — corrective adjustment posted | Finance reconciliation flagged variance `฿200` ที่ `LOC-A`; drill identifies stock-in row posted with `cost_per_unit = ฿20` ที่ควรเป็น `฿15`. Controller drafts compensating adjustment | 1. รับ escalation 2. Drill into cost-layer; ระบุ wrong-cost row `LAYER-X` 3. Draft compensating: stock-out ของ wrong-cost lot remaining qty plus stock-in at correct cost (`฿15`) 4. Route ผ่าน normal approval | หลัง approvals: compensating cost-layer rows written; original wrong-cost row stays (immutable); net effect คือ cost corrected เป็น `฿15`. Reconciliation variance drops Map ไปยัง parent Scenario 14 cost-side resolution |
| IC-HP-06 | Triage cost anomaly — dismiss legitimate variation | Cost-anomaly dashboard surfaces `cost_per_unit = ฿5` outbound on `P-1` at WA business unit; current `average_cost_per_unit = ฿10`. Drill reveals one-off promotional vendor discount | 1. เปิด cost-anomaly dashboard 2. Drill into outlier 3. ยืนยัน recent inbound 4. คลิก **Dismiss** with comment | Anomaly dismissed; activity log บันทึก dismissal with operational context; ไม่มี cost-layer adjustment |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| IC-PERM-01 | Controller อ่าน cost-pick previews บน adjustment documents | **Allow per `COST_AUTH_007`** Read scope บน `tb_inventory_transaction_cost_layer` + `tb_inventory_transaction_detail.cost_per_unit` |
| IC-PERM-02 | Controller อนุมัติ adjustment at picked cost | **Allow per inventory `INV_AUTH_003`** Picked cost เป็นส่วนของ document; approval commits document และ fires cost-layer write |
| IC-PERM-03 | Controller พยายาม edit `cost_per_unit` โดยตรงบน posted cost-layer row | **Deny — terminal per `COST_AUTH_010`** API returns `"Cost-layer rows are immutable."` |
| IC-PERM-04 | Controller พยายามอนุมัติ credit-note-amount revaluation | **Deny — Finance only per `COST_AUTH_005`** Credit-note approval queue ไม่ visible to Controller role |
| IC-PERM-05 | Controller พยายามเปลี่ยน `tb_business_unit.calculation_method` | **Deny — Sysadmin only per `COST_AUTH_001`** Controller สามารถ request change; Sysadmin executes; Finance coordinates drain pre-condition |
| IC-PERM-06 | Controller พยายาม lock period | **Deny — Finance Manager only per `COST_AUTH_006`** |
| IC-PERM-07 | Controller edits `tb_product.standard_cost` | **Deny by default — Finance / cost-control authority per `COST_AUTH_003`** |
| IC-PERM-08 | Controller อนุมัติ adjustment ที่ cost-impact เกิน Controller threshold | **Allow Controller's first signature; Finance-pending sub-state per inventory `INV_AUTH_005`** Finance เป็น role ที่ fires cost-layer write ที่ completion |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| IC-VAL-01 | อนุมัติ outbound เมื่อไม่มี cost-layer available (FIFO) | FIFO business unit; product `P-FRESH` at new location `LOC-NEW` ไม่มี prior inbound | **Reject at cost-pick** per `COST_VAL_002`: server returns `"FIFO: no available cost layer at (location, product) to consume."` |
| IC-VAL-02 | อนุมัติ outbound เมื่อไม่มี average initialised (WA) | WA business unit; setup เดียวกับ IC-VAL-01 | **Reject at cost-pick** per `COST_VAL_003`: server returns `"Weighted Average: no prior inbound layer at (location, product) to read average from."` |
| IC-VAL-03 | อนุมัติ new-lot stock-in with cost above price-deviation-limit | New-lot stock-in for `P-1` at `LOC-A`, qty 10, cost `฿30`; vendor pricelist last-price `฿15`; `price_deviation_limit = 10%`. Deviation `+฿15 (100%)` เหนือ tolerance | **Reject at approve** by Controller's deviation check: server returns `"Cost ฿30 exceeds pricelist last-price ฿15 by 100% (tolerance 10%); verify vendor pricing or escalate to Finance."` |
| IC-VAL-04 | อนุมัติ adjustment with negative cost บน inbound | Store Keeper enters `cost_per_unit = −฿5` บน stock-in document; Controller attempts to approve | **Reject at cost-pick** per `COST_VAL_004`: server returns `"Cost-pick produced an invalid cost_per_unit (negative or non-finite): −5.0."` |
| IC-VAL-05 | อนุมัติ transfer where source และ destination cost differ | Manual override attempt: source location FIFO produces `transfer_out.cost_per_unit = ฿10`; destination override sets `transfer_in.cost_per_unit = ฿12` | **Reject at post** per `COST_VAL_010`: server returns `"Transfer cost mismatch: transfer_in.cost_per_unit must equal transfer_out.cost_per_unit."` Map ไปยัง parent Scenario 16 |
| IC-VAL-06 | Count-variance cost cannot be resolved (configured source missing) | Tenant `enum_physical_count_costing_method = standard`; product `P-NEW` has `standard_cost = NULL` หรือ `0`; count completes with variance line | **Reject at count-rollup post** per `COST_VAL_007`: server returns `"Count-variance valuation: configured count-costing-method standard cannot resolve a cost (missing standard_cost on product)."` |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| IC-EDGE-01 | FIFO consumption ข้ามหลาย lots | FIFO product with 5 partial lots, each at different `cost_per_unit`; outbound qty consumes all 5 | **Five outbound cost-layer rows under one detail line** Each row carries its consumed lot's `cost_per_unit` และ consumed `out_qty` |
| IC-EDGE-02 | WA average exactly at column precision boundary | WA product; recompute produces `new_average = ฿11.333335`; stored at 5dp rounds to `฿11.33334` (half-up) | **Half-up rounding consistent per `COST_CALC_010`** Stored และ displayed values ตรงกับ rounding policy |
| IC-EDGE-03 | Concurrent approval บน documents affecting same lot | Controller A approves stock-out from `LOT-X` at `T`; Controller B approves different stock-out from `LOT-X` at `T+100ms` | **Both succeed ถ้า balance suffices; first-fail-fast otherwise** Both attempts read remaining qty; ถ้า combined `out_qty > LOT-X.remaining` second post fails `COST_VAL_002` / `INV_VAL_005` |
| IC-EDGE-04 | Cost-pick preview at threshold boundary | Adjustment whose aggregate cost impact = Controller threshold exactly | **Boundary inclusive — Controller approval terminal** `≤ threshold` is Controller-final; `> threshold` routes to Finance |
| IC-EDGE-05 | New-lot cost exactly at deviation tolerance | New-lot cost `฿16.50`; vendor pricelist last `฿15.00`; `price_deviation_limit = 10%` (tolerance ฿1.50). Deviation `+฿1.50 = 10%` exactly at tolerance | **Boundary inclusive — approve at tolerance** `≤ tolerance` passes; `> tolerance` rejects |
| IC-EDGE-06 | FIFO outbound เมื่อ newest layer created same minute as request | GRN committed at `T`, creating `LOT-NEW` with `lot_seq_no = max + 1`; SR-driven outbound at `T+200ms` consumes from `LOT-NEW` | **FIFO walks `lot_seq_no` ascending — consumes older lots first ไม่ใช่ LOT-NEW** เว้นแต่ older lots are exhausted |
| IC-EDGE-07 | WA average drift after credit-note revaluation | WA business unit; lot `LOT-X` revalued via credit-note-amount `diff_amount = −฿100`; running `average_cost_per_unit` shadow ควร refresh ที่ next inbound | **Average refresh deferred ไป next inbound per `COST_CALC_003`** จนกระทั่ง next inbound running average สะท้อน pre-revaluation state |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md)
- Business rules: [02-business-rules.md](./02-business-rules.md)
- Sibling: [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)
- Sibling: [04-test-scenarios-auditor.md](./04-test-scenarios-auditor.md)
- E2E specs: [`720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts), [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts), [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts)
- Cross-link: [[inventory/04-test-scenarios-inventory-controller]]
- Cross-link: [[good-receive-note]]
- Cross-link: [[vendor-pricelist]]
- Cross-link: [[physical-count]] / [[spot-check]]
- Cross-link: [[inventory-adjustment]]
