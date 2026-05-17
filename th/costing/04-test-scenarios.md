---
title: การคำนวณต้นทุน — Test Scenarios
description: Test cases ตาม persona, cross-persona scenarios, และ E2E mapping สำหรับ costing
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน — Test Scenarios

> **At a Glance**
> **Module:** [[costing]] &nbsp;·&nbsp; **Scenarios ทั้งหมด:** ~18 cross-persona + ~84 per-persona &nbsp;·&nbsp; **Personas ครอบคลุม:** Finance, Inventory Controller, Auditor
> **ลำดับการรัน:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Drill-down per-persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด test-scenarios ของโมดูล `costing` Group ความครอบคลุมตาม 3 personas ที่ interact กับ cost-flow lifecycle (Finance, Inventory Controller, Auditor) inventory ไฟล์ test per-persona จับ cross-persona handoff scenarios ที่เย็บ paths บุคคลเข้าด้วยกัน และ map cross-persona scenario ทุก scenario กลับไปยัง canonical inventory + GRN + credit-note E2E surfaces เนื่องจาก costing **ไม่มี dedicated spec file** — ทุก cost-flow effect fan out จาก upstream transaction post Scope กว้างกว่า functional pass แท้ ๆ: ไฟล์ per-persona แต่ละไฟล์รวม **functional happy paths**, **RBAC / permission-denial cases**, **edge cases**, และ **method-consistency audits**

Cross-persona scenarios ใน Section 4 คือ integration layer ด้านบน suites per-persona พวกเขาอธิบาย journeys end-to-end ที่ข้าม handoff boundary ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) Section 4 Section 5 map inventory + GRN + credit-note E2E describe blocks กลับไปยัง journeys เหล่านั้นเพื่อให้เห็น gap ในการครอบคลุมอัตโนมัติ

## 2. Personas ในขอบเขต

- **Finance**: valuation authority ที่เป็นเจ้าของนโยบาย (FIFO vs WA per business unit, count-costing method, standard-cost cadence) อนุมัติ credit-note-amount revaluations รัน sub-ledger ↔ GL reconciliation orchestrate period-end valuation และ (เป็น Finance Manager) advance `tb_period.status = closed → locked`
- **Inventory Controller**: engine-input cleanliness owner ที่ review FIFO / WA cost-pick previews บน adjustment approvals ตรวจสอบ new-lot cost basis เทียบ vendor pricelists ตรวจสอบ valuation variances ที่ Finance surface และ triage cost anomalies เชิงรุกบน cost-layer ledger
- **Auditor**: read-only reviewer ที่รัน cost-flow chain-of-custody traces, period-end snapshot verification, FIFO-vs-WA shadow drift audits, และ configuration history audits; deliverable คือ audit report

## 3. ไฟล์ Test ของ Persona

- [Finance scenarios](./04-test-scenarios-finance.md)
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md)
- [Auditor scenarios](./04-test-scenarios-auditor.md)

## 4. Cross-Persona / Handoff Scenarios

ตารางข้างล่างคือ integration layer แต่ละ row spans อย่างน้อย handoff หนึ่งจาก [03-user-flow.md](./03-user-flow.md) Section 4 และจบที่ cost-layer ledger ใน terminal หรือ steady state

| # | Scenario | Personas ตามลำดับ | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | FIFO outbound ข้ามสอง lots — Controller approves | Inventory Controller | Product ที่ FIFO-configured business unit; 2 lots ที่ source location ต่าง `lot_seq_no` และ `cost_per_unit`; SR-approved issue สำหรับ qty มากกว่า balance ของ lot เก่าที่สุด | Outbound `tb_inventory_transaction` เดียว; outbound cost-layer rows **2 แถว** — แรก consume lot เก่าที่สุดเต็มที่ `cost_per_unit`, สอง consume ที่เหลือจาก lot ถัดไปที่ `cost_per_unit` per `COST_CALC_001` / `COST_POST_002` |
| 2 | WA inbound recompute — Controller approves | Inventory Controller | Product ที่ WA-configured business unit; on-hand existing ที่ cost หนึ่ง; GRN receipt ใหม่ที่ cost ต่างกัน | GRN commit เขียน inbound cost-layer row; `average_cost_per_unit = (prior_on_hand × prior_average + in_qty × in_cost) / (prior_on_hand + in_qty)` per `COST_CALC_003` |
| 3 | Credit-note-amount revaluation — Finance approves | Inventory Controller (variance surfaced) → Finance | `committed` GRN exists with lot at `cost_per_unit = X`; vendor concession `−฿100`; credit-note ที่ `pending` | Finance approves; `INV_POST_007` → `COST_POST_003`; cost-layer row เขียนพร้อม `diff_amount = −฿100`; lot ต้นทาง's `cost_per_unit` recalculated per `COST_CALC_005`; GL: Dr AP / Cr Inventory ฿100 |
| 4 | Count-variance valuation by configured method | Inventory Controller → (per-tenant configured `physical_count_costing_method`) | Physical count completes with variance lines; tenant configured `enum_physical_count_costing_method = last_receiving` | `tb_stock_in` / `tb_stock_out` ต่อทิศทาง; แต่ละ line's `cost_per_unit` resolved by `COST_CALC_008` |
| 5 | Period-end valuation rollforward (FIFO) — Finance closes | Inventory Controller → Finance → Finance Manager | Closing period ที่ `open`; Controller signed off; reconciliation passes; FIFO business unit | Finance closes period: `INV_POST_009` + `COST_POST_007`; `COST_POST_008` writes `open_period` cost-layer rows with `lot_seq_no` preserved per `COST_CALC_007` |
| 6 | Period-end valuation rollforward (WA) — Finance closes | เหมือน Scenario 5 แต่ WA business unit | Closing period; running `average_cost_per_unit` per `(location, product)` | `COST_POST_007` writes snapshot with `closing_cost_per_unit = current_running_average`; `COST_POST_008` writes single `open_period` cost-layer row per `(location, product)` |
| 7 | Calculation-method change blocked by non-zero on-hand | System Administrator | Existing business unit ที่ `calculation_method = average` with non-zero on-hand; Sysadmin attempts ไป `fifo` | Impact preview ปฏิเสธ per `COST_VAL_009` Configuration ไม่ saved |
| 8 | Calculation-method change after drain — happy path | Finance → Store Keeper → Inventory Controller → System Administrator | Drain coordinated; Sysadmin re-attempts | Impact preview passes; Sysadmin saves; `tb_business_unit.calculation_method = fifo` persisted; movement ใหม่ใช้ FIFO |
| 9 | Standard-cost update — recipe baseline + count-variance | Finance | Monthly batch; N products; tenant `enum_physical_count_costing_method = standard` | `tb_product.standard_cost` updated; **no cost-layer effect** per `COST_POST_010` |
| 10 | Cost-pick preview anomaly — Controller rejects stock-out | Store Keeper → Inventory Controller | FIFO; stale 6-month-old lot at `lot_seq_no = 1` with anomalously high cost | Controller ปฏิเสธพร้อมคอมเมนต์; document กลับไปยัง Store Keeper ที่ `draft`; ไม่มี cost-layer row เขียน |
| 11 | Lot-cost chain-of-custody trace — recall investigation | Auditor | Lot `LOT-RECALL-42` introduced by GRN, partially issued, partially written off, with credit-note-amount revaluation | Backward trace + Forward trace; report exports |
| 12 | Period-snapshot verification — Auditor reconciles | Auditor | Closed period `2026-04`; Auditor runs independent reconstruction | Per-key reconciliation: snapshot's `closing_total_cost` equals independent reconstruction; clean — verification report exports |
| 13 | FIFO-WA shadow drift — within tolerance | Auditor | FIFO business unit; period of normal activity | Each row's `average_cost_per_unit` matches independent WA recompute within rounding tolerance; verification clean |
| 14 | Sub-ledger ↔ GL reconciliation variance — Finance resolves | Inventory Controller (drill) → Finance | Reconciliation pass surfaces `฿156` variance; drill identifies missed GL journal | Finance posts compensating GL journal; reconciliation re-runs to within tolerance |
| 15 | Period re-open for credit-note revaluation in closed period | Auditor flags → Finance Manager re-opens → Finance approves credit-note → Finance closes again | Period `2026-04` at `closed` within audit window; external audit identifies missed credit-note | Finance Manager re-opens; credit-note posted; `COST_POST_003` writes; Finance re-runs close |
| 16 | Transfer cost mismatch attempt — rejected | (negative test) | Source location FIFO produces `transfer_out.cost_per_unit = ฿10`; manual override sets `transfer_in = ฿12` | Post ปฏิเสธ per `COST_VAL_010` |
| 17 | Direct-cost location receipt — no cost-layer row | Store Keeper (via GRN) | GRN receipt to location with `tb_location.location_type = direct` | Header + detail เขียน; **no cost-layer row** per `COST_VAL_011` / `COST_POST_005`. GL: Dr Department Expense / Cr AP |
| 18 | Consignment location receipt — memo cost layer | Store Keeper (via GRN) | GRN receipt to `location_type = consignment` location | Cost-layer row เขียนพร้อม consignment flag per `COST_POST_006`; **no** AP debit, **no** Inventory credit at receipt |

## 5. E2E Test Mapping

โมดูล costing **partial exercised** โดย inventory + GRN + credit-note + SR + stock-issue Playwright specs **ไม่มี dedicated `costing.spec.ts`**

| Spec / describe block | Cross-persona scenarios covered (Section 4) |
| --------------------- | ------------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | 5 (FIFO period rollforward), 6 (WA period rollforward), 15 (period re-open for revaluation) |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Stock Movements / Commit describe blocks | 2 (WA inbound recompute on GRN commit), 17 (direct-cost location receipt), 18 (consignment location receipt) |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) (store-requisition) | 1 (FIFO outbound spanning lots — SR-driven), 16 (transfer cost-mismatch rejection) |
| [`720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) | 1 (FIFO outbound spanning lots via stock-issue path), 10 (Controller rejects on anomalous cost-pick) |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) (credit-note) | 3 (credit-note-amount revaluation — cost-side effect) |
| Stock-in / Stock-out admin (no canonical spec yet) | 4 (count-variance valuation by configured method), 8 (method change after drain), 10 (cost-pick preview anomaly rejection) |
| Configuration / Sysadmin specs (likely [`080-location.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/080-location.spec.ts) and a future business-unit config spec) | 7 (method change blocked by on-hand), 9 (standard-cost update — prospective) |
| Audit module specs (outside the inventory module spec set) | 11 (lot-cost chain-of-custody), 12 (snapshot verification), 13 (FIFO-WA shadow drift), and the configuration-history audits |

Gaps relative to Section 4:

- Scenario 4 (count-variance valuation by configured method) ครอบคลุมบางส่วนโดย count module specs
- Scenario 8 (method change after drain) เป็น coordination scenario; โดยทั่วไป manual / planned migration runbook tested in staging
- Scenarios 11, 12, 13 (Auditor chain-of-custody, snapshot verification, shadow drift) เป็น read-only audit queries; โดยทั่วไป manual coverage in the Auditor persona file
- Scenario 14 (sub-ledger ↔ GL reconciliation variance with cost-side root cause) ครอบคลุมบางส่วนโดย `900-period-end.spec.ts`
- Scenarios 16, 17, 18 ส่วนใหญ่เป็น inventory-module-spec concerns พร้อม cost-side assertions

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts)
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts)
- [`../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts)
- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts)
- [`../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts)
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4
- Sibling: [02-business-rules.md](./02-business-rules.md)
- Sibling: [calculation-methods.md](./calculation-methods.md)
- Per-persona detail: [Finance](./04-test-scenarios-finance.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Auditor](./04-test-scenarios-auditor.md)
