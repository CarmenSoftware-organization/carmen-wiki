---
title: การคำนวณต้นทุน (Costing) — Test Scenarios
description: Test cases ตาม persona, cross-persona scenarios, และ E2E mapping สำหรับ costing
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios

> **At a Glance**
> **Module:** [costing](/th/inventory/costing) &nbsp;·&nbsp; **Scenarios ทั้งหมด:** 11 scenario ระดับ engine ที่ตัดข้าม (ดู Section 3) — ไม่มีการแบ่ง persona
> **ลำดับการรัน:** ไม่จำเป็นต้องมี — ทุก scenario ด้านล่างเป็นผลโดยตรงจากการ post เอกสารต้นทาง ไม่มีลำดับ approval แยกฝั่ง costing
> **แก้ไข (ยืนยันแล้ว 2026-07-22):** ~102 scenarios ที่เคยกระจายอยู่บนหน้านี้และสามหน้า per-persona (Finance, Inventory Controller, Auditor) เล็งไปที่หน้าจอที่ไม่มีอยู่จริง — valuation-policy console, GL reconciliation dashboard, cost-pick-preview approval queue, audit workspace ถูกลบออกแทนการกุขึ้นใหม่; สามหน้า per-persona ตอนนี้เป็นหน้าแก้ไข (Section 2)

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด test-scenarios ของโมดูล `costing` Costing ไม่มี document lifecycle และไม่มีหน้าจอที่ gate ด้วย persona ของตัวเอง (ดู [03-user-flow](./03-user-flow.md)) จึงไม่มีโครงสร้าง "per-persona happy path" ให้ test ที่นี่ — ทุก cost-flow effect เป็นผลข้างเคียงของการ post เอกสารต้นทาง (GRN commit, SR issue, credit-note approval, การสร้าง inventory-adjustment, period-end close) ซึ่งแต่ละอย่างครอบคลุมแล้วโดยโมดูลของตัวเอง สิ่งที่เหลือให้ test **เฉพาะที่ชั้น costing** คือ arithmetic ของ cost-pick เอง: engine เลือก lot ถูกไหม คำนวณ average ถูกไหม revalue แถวถูกไหม และนำยอดคงเหลือไปต่อถูกไหม — ไม่ขึ้นกับว่าเอกสารไหน trigger Section 3 ลิสต์ scenario เหล่านั้นตรง ๆ (ไม่มีคอลัมน์ persona เพราะไม่มีอันไหนถูก gate ด้วยอะไรนอกจาก permission ของเอกสารที่ trigger เอง)

## 2. ไฟล์ Per-Persona เดิม (ตอนนี้เป็นการแก้ไข)

- [Finance scenarios](./04-test-scenarios-finance.md) — หน้าแก้ไข
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md) — หน้าแก้ไข
- [Auditor scenarios](./04-test-scenarios-auditor.md) — หน้าแก้ไข

## 3. Engine Scenarios

แต่ละแถวคือ cost-pick scenario ที่ครบในตัวเอง "Trigger" ระบุ action ของเอกสารที่ invoke engine — ไม่มีผู้กระทำฝั่ง costing แยกให้ระบุ เพราะ engine ไม่มี permission gate ของตัวเองนอกจากของ trigger

| # | Scenario | Trigger | Pre-condition | Expected end state |
| - | -------- | ------- | -------------- | ------------------- |
| 1 | FIFO outbound ข้ามสอง lots | SR issue / stock-out ที่เกิน balance ของ lot เก่าที่สุด | Product ที่ FIFO-method business unit; 2 lots ที่ source location ต่าง `lot_seq_no` และ `cost_per_unit`; qty ที่ issue มากกว่า balance คงเหลือของ lot เก่าที่สุด | Outbound `tb_inventory_transaction` เดียว; outbound cost-layer rows **2 แถว** — แรก consume lot เก่าที่สุดเต็มที่ `cost_per_unit`, สอง consume ที่เหลือจาก lot ถัดไป per `COST_CALC_001` / `COST_POST_002` |
| 2 | Average inbound recompute | GRN commit | Product ที่ Average-method business unit; on-hand existing ที่ cost หนึ่ง; GRN receipt ใหม่ที่ cost ต่างกัน | GRN commit เขียน inbound cost-layer row; `average_cost_per_unit = (prior_on_hand × prior_average + in_qty × in_cost) / (prior_on_hand + in_qty)` per `COST_CALC_003`; outbound ถัดไปที่ `(location, product)` นี้อ่าน average ใหม่ |
| 3 | Credit-note-amount revaluation | Credit-note approval (`procurement.credit_note`) | `committed` GRN exists with lot at `cost_per_unit = X`; vendor ลดราคา `−฿100` หลังรับ; credit-note ที่ `pending` | ตอนอนุมัติ: cost-layer row เขียนพร้อม `in_qty = 0, out_qty = 0, diff_amount = −฿100, transaction_type = credit_note_amount`; lot ต้นทาง's `cost_per_unit` recalculated per `COST_CALC_005`; downstream FIFO consumption จาก lot หยิบ cost ที่ revalued; portions ที่บริโภคแล้ว **ไม่** ถูกปรับย้อนหลัง ไม่มี GL entry — ไม่มีอยู่จริง |
| 4 | Count-variance valuation by configured method | Physical-count / spot-check variance rollup (ดูรอบ resync ของโมดูลนั้นเองว่าถึง ledger จริงหรือไม่) | Tenant configured `enum_physical_count_costing_method = last_receiving` | Count-derived line's `cost_per_unit` resolved by `COST_CALC_008` reading inbound layer ล่าสุดที่ `(location, product)` |
| 5 | Period-end close (FIFO) — ไม่เขียน snapshot | `inventory_management.period_end.execute` → Close period | Closing period ที่ `open`; blocking document ทั้งหมด terminal, physical count เสร็จ; FIFO business unit with residual lots at multiple `(location, product)` keys | แถว cost-layer `close_period` / `open_period` นำทุก lot คงเหลือไปต่อพร้อม `lot_seq_no` preserved (`COST_POST_007` / `COST_POST_008`) **ไม่มีการเขียนแถว `tb_period_snapshot` เลย** — ยืนยันข้อนี้โดยตรง เพราะง่ายที่จะสมมติว่า snapshot table ถูกเขียนทุกครั้งที่ปิดงวด |
| 6 | Period-end close (Average) — เขียน snapshot | Trigger เดียวกัน, Average business unit | Closing period; running `average_cost_per_unit` per `(location, product)` | `tb_period_snapshot` rows เขียนต่อ `(location, product)` พร้อม `closing_cost_per_unit = current_running_average`; แถว `open_period` cost-layer เดี่ยวต่อ key นำ closing average เข้างวดถัดไป |
| 7 | เปลี่ยนวิธีคำนวณทั้งที่มี non-zero on-hand — ปัจจุบันไม่มีการป้องกัน | Platform/cluster admin เปลี่ยน `tb_business_unit.calculation_method` | Business unit ที่ `calculation_method = average` with non-zero on-hand สำหรับอย่างน้อยหนึ่งสินค้า | **ไม่มี guard อยู่จริง** การ save สำเร็จไม่ว่าปริมาณ on-hand เท่าไหร่ — ดู [02-business-rules](./02-business-rules.md) § 2 (`COST_VAL_009` ถูกลบ) Movement ใหม่ใช้วิธีใหม่ทันที; cost-layer rows ที่มีอยู่แล้วคง cost ที่เลือกไว้แล้ว คุ้มค่าจะ test เพราะ tester อาจคาดว่าจะถูกบล็อก |
| 8 | Standard-cost update — ไม่มีผลกับ cost-layer | แก้ไข standard cost ของสินค้า | `tb_product.standard_cost` updated สำหรับสินค้าหนึ่ง; tenant `enum_physical_count_costing_method = standard` | `tb_product.standard_cost` updated; **ไม่มีผลกับ cost-layer** (`COST_POST_010` — prospective เท่านั้น) Count-variance posts ถัดไปสำหรับสินค้านั้นหยิบค่าใหม่ |
| 9 | Transfer cost mismatch — ปฏิเสธ | Inter-location transfer post | Source location FIFO cost-pick ผลิต `transfer_out.cost_per_unit = ฿10`; ความพยายามตั้ง `transfer_in.cost_per_unit = ฿12` | ปฏิเสธ per `COST_VAL_010`: `transfer_in.cost_per_unit` ต้องเท่ากับ `transfer_out.cost_per_unit` |
| 10 | Direct-location receipt — auto-issue ทันที ไม่เก็บเป็นสต๊อก | GRN receipt ไป location ที่ `tb_location.location_type = direct` | — | Inbound cost-layer row เขียน แล้วเขียนแถวขาออกชดเชยอัตโนมัติ (`createDirectExpenseOut`) ที่ cost เดียวกันภายใต้ transaction header เดียวกัน — ยอดคงเหลือสุทธิเป็นศูนย์ Direct receipt ถูกยกเว้นจากการคำนวณ Average ไม่มีผลกับ GL |
| 11 | Store Requisition — cost pass-through, ไม่ re-average, ไม่มี lot ใหม่ | SR issue ไป Direct หรือ Consignment destination | Lot ที่มีอยู่แล้วที่ source location | Engine ถูก invoke (`COST_POST_002`) และเลือก cost ของ layer ที่มีอยู่ แต่**ไม่** re-average (วิธี Average) และ**ไม่**สร้าง FIFO layer ใหม่ — outbound consume lot ที่มีอยู่ที่ `cost_per_unit` เดิม |

## 4. E2E Test Mapping

โมดูล costing **exercised บางส่วน** โดย inventory + GRN + credit-note + SR Playwright specs **ไม่มี dedicated `costing.spec.ts`** เพราะทุก cost-flow effect fan out จากการ post เอกสารต้นทาง

| Spec | Engine scenarios covered (Section 3) |
| ---- | ------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | มี list/permission/validation coverage สำหรับ period-end; ตามที่รอบนี้อ่าน spec file describe block **Close workflow**, **Close action**, และ **Detail page** ถูกระบุชัดเจนว่า `Feature pending` / `Backend only` ใน spec เอง — mechanics การ rollforward แบบ FIFO-vs-Average (Scenario 5, 6) **ไม่** ถูก exercise แบบ end-to-end โดย spec นี้วันนี้ มีแค่พื้นผิว list/permission ที่ถูกทดสอบ |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) | Inbound cost-layer write บน GRN commit ถูก exercise โดยอ้อมผ่าน Stock Movements describe block (Scenario 2, 10); ไม่ยืนยัน per-lot cost assertion ในรอบนี้ |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) | SR-driven outbound (Scenario 1, 11) ถูก exercise โดยอ้อม; ไม่ยืนยัน cost-layer assertion ในรอบนี้ |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) | Credit-note inventory effect (Scenario 3) ถูก exercise โดยอ้อม; ไม่ยืนยัน `diff_amount` assertion ในรอบนี้ |

ให้ปฏิบัติกับทุกแถว "exercised โดยอ้อม" ข้างบนว่า **ยังไม่ยืนยัน** ที่ระดับ assertion ของ cost-layer — spec ที่อ้างถึงมีอยู่จริงและครอบคลุม flow ของเอกสารต้นทางเอง แต่รอบนี้ไม่ได้เปิดแต่ละ spec file เพื่อตรวจว่ามันทำ assertion เฉพาะ cost-layer (ค่า `cost_per_unit`, `lot_seq_no`, `diff_amount` ที่แน่นอน) หรือไม่ ตรวจสอบซ้ำก่อนอ้างว่าอันไหน "tested" ใน QA plan Scenario 4, 7, 8, 9 ไม่มี E2E coverage ที่ยืนยันเลยในรอบนี้ — ถือว่าเป็น manual / planned

## 5. References

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — period-end E2E; หลาย describe block ถูกระบุ pending ใน spec file เอง
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts), [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts), [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — spec ของเอกสารต้นทางที่ describe block ผลกระทบ Stock Movements/inventory ของมันเชื่อม engine โดยอ้อม
- Sibling: [03-user-flow.md](./03-user-flow.md) — lifecycle ที่แก้ไขแล้วและหมายเหตุแก้ไขสำหรับสามหน้า persona เดิม
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation, calculation, และ posting ที่แต่ละ scenario ข้างบนตรวจสอบ
- Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO และ Average algorithm pseudocode พร้อมตัวอย่างตัวเลข ตัวอย่างที่ทำงานใน [02-business-rules.md](./02-business-rules.md) § 3.1 / 3.2 สอดคล้องกับเนื้อหา calculation-methods
- ไฟล์ per-persona เดิม (ตอนนี้เป็นการแก้ไข): [Finance](./04-test-scenarios-finance.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Auditor](./04-test-scenarios-auditor.md)
