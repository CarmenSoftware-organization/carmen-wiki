---
title: การคำนวณต้นทุน (Costing) — Test Scenarios
description: 14 scenario ระดับ cost-pick engine ที่ตัดข้ามและ E2E mapping สำหรับ costing — ไม่มีการแบ่ง persona ดูสามหน้าแก้ไขสำหรับสิ่งที่ถูกลบ
published: true
date: '2026-09-23T01:30:00.000Z'
tags: costing, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios

> **At a Glance**
> **Module:** [costing](/th/inventory/costing) &nbsp;·&nbsp; **Scenarios ทั้งหมด:** 14 scenario ระดับ engine ที่ตัดข้าม (ดู Section 3) — ไม่มีการแบ่ง persona
> **ลำดับการรัน:** ไม่จำเป็นต้องมี — ทุก scenario ด้านล่างเป็นผลโดยตรงจากการ post เอกสารต้นทาง ไม่มีลำดับ approval แยกฝั่ง costing
> **แก้ไข (ยืนยันแล้ว 2026-07-22):** ~102 scenarios ที่เคยกระจายอยู่บนหน้านี้และสามหน้า per-persona (Finance, Inventory Controller, Auditor) เล็งไปที่หน้าจอที่ไม่มีอยู่จริง — valuation-policy console, GL reconciliation dashboard, cost-pick-preview approval queue, audit workspace ถูกลบออกแทนการกุขึ้นใหม่; สามหน้า per-persona ตอนนี้เป็นหน้าแก้ไข (Section 2)
> **ตรวจสอบซ้ำ 2026-09-22:** แก้ไข scenario 2, 5, 6, 10 (ค่าเฉลี่ยต่อสินค้าที่ 2 ตำแหน่งและโพสต์ตอน GRN **save**; เปลี่ยนชื่อตาราง snapshot; direct receipt); เพิ่ม scenario 12–14 (landed cost พร้อม extra cost + FOC; การถอน GRN บน BU แบบ average; การ resolve งวดตาม `grn_date`)

> **Executable coverage (E2E repo `../carmen-inventory-frontend-e2e/`):** **ไม่มี** catalog page, gap report หรือ spec ของ `costing` — `docs/test-cases/COVERAGE.md` ไม่มี route costing coverage ที่รันได้ใกล้เคียงที่สุดคือ `tests/501-grn.spec.ts` (76 case; กลุ่ม Stock Movements), `tests/601-cn.spec.ts`, `tests/701-sr.spec.ts`, `tests/900-period-end.spec.ts` และ gap report `docs/test-cases/gaps/501-grn-core-gap.md` (62) / `501-grn-from-po-gap.md` (24) ไม่มีอันไหน assert ค่า cost-layer หน้านี้ไม่ได้ mirror สิ่งเหล่านั้น

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
| 2 | Average inbound recompute | GRN **save** (`draft → saved`) บน BU แบบ average | Product ที่ Average-method business unit; on-hand สุทธิเดิม 100 @ ฿10.00 (location ใดก็ได้); GRN receipt ใหม่ 50 @ landed ฿14.00 | **Save** ไม่ใช่ commit เขียน inbound cost-layer row (`tb_inventory_transaction.info.posted_at_save = true`); `average_cost_per_unit = Round2((1,000 + 700) / 150) = ฿11.33` per `COST_CALC_003` ประทับบน layer ใหม่ **และทุก layer ที่ยังมีชีวิตของสินค้าที่ทุก location**; issue ถัดไปที่ location ใดก็ตามอ่าน ฿11.33 จากนั้น commit เพิ่มยอด PO โดยไม่มีการเขียน ledger ครั้งที่สอง |
| 3 | Credit-note-amount revaluation | Credit-note approval (`procurement.credit_note`) | `committed` GRN exists with lot at `cost_per_unit = X`; vendor ลดราคา `−฿100` หลังรับ; credit-note ที่ `pending` | ตอนอนุมัติ: cost-layer row เขียนพร้อม `in_qty = 0, out_qty = 0, diff_amount = −฿100, transaction_type = credit_note_amount`; lot ต้นทาง's `cost_per_unit` recalculated per `COST_CALC_005`; downstream FIFO consumption จาก lot หยิบ cost ที่ revalued; portions ที่บริโภคแล้ว **ไม่** ถูกปรับย้อนหลัง ไม่มี GL entry — ไม่มีอยู่จริง |
| 4 | Count-variance valuation by configured method | Physical-count / spot-check variance rollup (ดูรอบ resync ของโมดูลนั้นเองว่าถึง ledger จริงหรือไม่) | Tenant configured `enum_physical_count_costing_method = last_receiving` | Count-derived line's `cost_per_unit` resolved by `COST_CALC_008` reading inbound layer ล่าสุดที่ `(location, product)` |
| 5 | Period-end close (FIFO) — ไม่เขียน snapshot | `inventory_management.period_end.execute` → Close period | Closing period ที่ `open`; blocking document ทั้งหมด terminal, physical count เสร็จ; FIFO business unit with residual lots at multiple `(location, product)` keys | แถว cost-layer `close_period` / `open_period` นำทุก lot คงเหลือไปต่อพร้อม `lot_seq_no` preserved (`COST_POST_007` / `COST_POST_008`) **ไม่มีการเขียนแถว `tb_inventory_period_snapshot` เลย** — ยืนยันข้อนี้โดยตรง เพราะง่ายที่จะสมมติว่า snapshot table ถูกเขียนทุกครั้งที่ปิดงวด |
| 6 | Period-end close (Average) — เขียน snapshot | Trigger เดียวกัน, Average business unit | Closing period; `average_cost_per_unit` ระดับสินค้าประทับบนทุก layer | `tb_inventory_period_snapshot` rows เขียนต่อ `(location, product)` พร้อม `closing_cost_per_unit = ค่าเฉลี่ยปัจจุบัน`; แถว `open_period` cost-layer เดี่ยวต่อ key นำ closing average เข้างวดถัดไป |
| 7 | เปลี่ยนวิธีคำนวณทั้งที่มี non-zero on-hand — ปัจจุบันไม่มีการป้องกัน | Platform/cluster admin เปลี่ยน `tb_business_unit.calculation_method` | Business unit ที่ `calculation_method = average` with non-zero on-hand สำหรับอย่างน้อยหนึ่งสินค้า | **ไม่มี guard อยู่จริง** การ save สำเร็จไม่ว่าปริมาณ on-hand เท่าไหร่ — ดู [02-business-rules](./02-business-rules.md) § 2 (`COST_VAL_009` ถูกลบ) Movement ใหม่ใช้วิธีใหม่ทันที; cost-layer rows ที่มีอยู่แล้วคง cost ที่เลือกไว้แล้ว คุ้มค่าจะ test เพราะ tester อาจคาดว่าจะถูกบล็อก |
| 8 | Standard-cost update — ไม่มีผลกับ cost-layer | แก้ไข standard cost ของสินค้า | `tb_product.standard_cost` updated สำหรับสินค้าหนึ่ง; tenant `enum_physical_count_costing_method = standard` | `tb_product.standard_cost` updated; **ไม่มีผลกับ cost-layer** (`COST_POST_010` — prospective เท่านั้น) Count-variance posts ถัดไปสำหรับสินค้านั้นหยิบค่าใหม่ |
| 9 | Transfer cost mismatch — ปฏิเสธ | Inter-location transfer post | Source location FIFO cost-pick ผลิต `transfer_out.cost_per_unit = ฿10`; ความพยายามตั้ง `transfer_in.cost_per_unit = ฿12` | ปฏิเสธ per `COST_VAL_010`: `transfer_in.cost_per_unit` ต้องเท่ากับ `transfer_out.cost_per_unit` |
| 10 | Direct-location receipt — auto-issue ทันที ไม่เก็บเป็นสต๊อก | GRN receipt ไป location ที่ `tb_location.location_type = direct` | — | Inbound cost-layer row เขียน แล้วเขียนแถวขาออกชดเชยอัตโนมัติ (`createDirectExpenseOut`) ที่ cost เดียวกันภายใต้ transaction header เดียวกัน — ยอดคงเหลือสุทธิเป็นศูนย์ Direct receipt ถูกยกเว้นจากการคำนวณ Average และ layer ของมันมี `average_cost_per_unit = 0` ไม่มีผลกับ GL |
| 11 | Store Requisition — cost pass-through, ไม่ re-average, ไม่มี lot ใหม่ | SR issue ไป Direct หรือ Consignment destination | Lot ที่มีอยู่แล้วที่ source location | Engine ถูก invoke (`COST_POST_002`) และเลือก cost ของ layer ที่มีอยู่ แต่**ไม่** re-average (วิธี Average) และ**ไม่**สร้าง FIFO layer ใหม่ — outbound consume lot ที่มีอยู่ที่ `cost_per_unit` เดิม |
| 12 | Landed cost — extra cost และ FOC ใน layer | GRN commit (FIFO) / save (average) | ส่วนหัว extra cost แบบ `by_value` โดย detail รวม ฿200 (สกุลเงินเอกสาร, `exchange_rate = 1`); บรรทัด A `received_base_qty = 10`, `foc_base_qty = 1`, `base_net_amount = ฿1,192.25`; บรรทัด B `received_base_qty = 4`, `base_net_amount = ฿356.00` | ส่วนแบ่ง `200 × 11/15 = ฿146.67` (A) และ `200 × 4/15 = ฿53.33` (B) (`by_value` ถ่วงตามปริมาณสต๊อกรวม FOC); A: `qty = 11`, `cost_per_unit = Round2(1,338.92 / 11) = ฿121.72`, layer `extra_cost_amount ≈ 146.67`; B: `qty = 4`, `cost_per_unit = Round2(409.33 / 4) = ฿102.33` ด้วย `by_qty`: ฿100 ต่อบรรทัด; ด้วย `manual`: ฿0 ต่อบรรทัด `Σ extra_cost_amount` ข้าม layer ของ GRN = ฿200.00 |
| 13 | ถอน GRN บน BU แบบ average ก่อน commit | Void / reject / แก้ไข qty ของ GRN สถานะ `saved` บน BU แบบ average | สถานะจาก Scenario 2 (การเคลื่อนไหวโพสต์ตอน save) (a) ยังไม่มีอะไรถูกใช้ (b) store requisition ใช้ไปแล้ว 20 จาก 50 หน่วยที่รับ | (a) ส่วนหัวการเคลื่อนไหวและ layer ของมันถูก soft-delete, `detail_item.inventory_transaction_id` ถูกล้าง, ค่าเฉลี่ยของสินค้าประทับกลับเป็น ฿10.00; การแก้ไขโพสต์การเคลื่อนไหวใหม่ด้วยตัวเลขใหม่ (b) `GRN_RECEIPT_ALREADY_CONSUMED` (409); ไม่มีอะไรเปลี่ยน BU แบบ FIFO: ไม่มีอะไรให้ถอนก่อน commit |
| 14 | การ resolve งวดตามวันที่รับ | GRN commit / approve (BU ใดก็ได้), save (BU แบบ average) | `grn_date` อยู่ในงวด `closed` หรือวันที่ที่ไม่มีงวดใดครอบคลุม; มีอีกงวดที่ `open` | `GRN_DATE_OUTSIDE_OPEN_PERIOD` (422) — การเคลื่อนไหว **ไม่** ถูก re-date เข้างวดเปิด (`resolvePeriodForDate` เทียบ `resolveCurrentPeriod`) `grn_date` ที่วันสุดท้ายของงวดเปิดถูกยอมรับ (เปรียบเทียบระดับวัน) งวดที่ชื่อเช่น `4904` ครอบคลุม 2026-03-31…2049-04-30 ถูกจับคู่ตามช่วง ไม่ใช่ตาม label `YYMM`; `at_period` ของ layer copy label นั้น |

## 4. E2E Test Mapping

โมดูล costing **exercised บางส่วน** โดย inventory + GRN + credit-note + SR Playwright specs **ไม่มี dedicated `costing.spec.ts`** เพราะทุก cost-flow effect fan out จากการ post เอกสารต้นทาง

| Spec | Engine scenarios covered (Section 3) |
| ---- | ------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | มี list/permission/validation coverage สำหรับ period-end; ตามที่รอบนี้อ่าน spec file describe block **Close workflow**, **Close action**, และ **Detail page** ถูกระบุชัดเจนว่า `Feature pending` / `Backend only` ใน spec เอง — mechanics การ rollforward แบบ FIFO-vs-Average (Scenario 5, 6) **ไม่** ถูก exercise แบบ end-to-end โดย spec นี้วันนี้ มีแค่พื้นผิว list/permission ที่ถูกทดสอบ |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) | Inbound cost-layer write บน GRN commit ถูก exercise โดยอ้อมผ่าน Stock Movements describe block (Scenario 2, 10, 12 — แท็บแสดงเฉพาะ GRN ที่ `committed` และเรียก `GET …/stock-movements` จริง); 57 จาก 76 case ของ spec ไม่มี assertion (`docs/test-cases/SPEC-HEALTH.md`) จึงไม่มี per-lot cost assertion |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) | SR-driven outbound (Scenario 1, 11) ถูก exercise โดยอ้อม; ไม่ยืนยัน cost-layer assertion ในรอบนี้ |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) | Credit-note inventory effect (Scenario 3) ถูก exercise โดยอ้อม; ไม่ยืนยัน `diff_amount` assertion ในรอบนี้ |

ให้ปฏิบัติกับทุกแถว "exercised โดยอ้อม" ข้างบนว่า **ยังไม่ยืนยัน** ที่ระดับ assertion ของ cost-layer — spec ที่อ้างถึงมีอยู่จริงและครอบคลุม flow ของเอกสารต้นทางเอง แต่ไม่มีอันไหนทำ assertion เฉพาะ cost-layer (ค่า `cost_per_unit`, `lot_seq_no`, `extra_cost_amount`, `diff_amount` ที่แน่นอน) ตรวจสอบซ้ำก่อนอ้างว่าอันไหน "tested" ใน QA plan Scenario 4, 7, 8, 9, 12, 13, 14 ไม่มี E2E coverage เลย — ถือว่าเป็น manual / ระดับ API (`GET …/good-received-notes/:id/stock-movements` และ `GET …/cost/products/:id/last-cost` คือ read path ที่ใช้ assert)

## 5. References

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — period-end E2E; หลาย describe block ถูกระบุ pending ใน spec file เอง
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts), [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts), [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — spec ของเอกสารต้นทางที่ describe block ผลกระทบ Stock Movements/inventory ของมันเชื่อม engine โดยอ้อม
- Sibling: [03-user-flow.md](./03-user-flow.md) — lifecycle ที่แก้ไขแล้วและหมายเหตุแก้ไขสำหรับสามหน้า persona เดิม
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation, calculation, และ posting ที่แต่ละ scenario ข้างบนตรวจสอบ
- Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO และ Average algorithm pseudocode พร้อมตัวอย่างตัวเลข ตัวอย่างที่ทำงานใน [02-business-rules.md](./02-business-rules.md) § 3.1 / 3.2 สอดคล้องกับเนื้อหา calculation-methods
- ไฟล์ per-persona เดิม (ตอนนี้เป็นการแก้ไข): [Finance](./04-test-scenarios-finance.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Auditor](./04-test-scenarios-auditor.md)
