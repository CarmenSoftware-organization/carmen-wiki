---
title: การคำนวณต้นทุน (Costing) — Business Rules
description: การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting การปลายงวด และกฎข้ามโมดูลสำหรับ costing
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, business-rules, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `COST_VAL_*` validation &nbsp;·&nbsp; `COST_CALC_*` calc &nbsp;·&nbsp; `COST_POST_*` posting &nbsp;·&nbsp; `COST_XMOD_*` cross-module — กลุ่ม `COST_AUTH_*` ถูกลบออก 2026-07-22 (การแก้ไข Section 4; ไม่มีชั้น RBAC แยก)
> **จำนวนกฎ:** ประมาณ 75 กฎ หลังรอบแก้ไข 2026-07-22 (ลบบางแถวของ `COST_VAL_*`/`COST_POST_*`/`COST_XMOD_*` เพราะยังไม่ยืนยัน, ลบ `COST_AUTH_*` ทั้งสิบข้อ)
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา
> **Status lifecycle:** Section 5.1 (ที่มี) carry Live UI vs BRD discrepancy callouts

> **แก้ไข (ยืนยันแล้ว 2026-07-22):** ฉบับร่างก่อนหน้าของหน้านี้อ้างเอกสารชุดหนึ่งที่ `Test_case/System_Process/*.md` พร้อม capture date ที่กุขึ้นเอง และปฏิบัติกับคำตอบในเอกสารนั้นเหมือนเป็นข้อเท็จจริงที่ยืนยันจาก code เอกสารชุดนั้นมีอยู่จริงแต่ **ถูกอ้าง path ผิดและระบุแหล่งที่มาผิด** — ที่จริงอยู่ที่ `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/*.md` (`INDEX.md`, `proc-03-cost-calculation.md`, `tx-01-grn.md` … `tx-11-wastage-report.md`) และเป็น **เอกสารระดับวางแผน/requirements** ไม่ใช่ test spec ที่ QA ยืนยันแล้ว — ตาราง P4 ของเอกสารเองบันทึกคำตอบเป็น `"User confirmed <date>"` (จาก session รวบรวม requirement) ไม่ใช่พฤติกรรมระบบที่สังเกตจริง รอบนี้ตรวจสอบทุก claim ที่ฉบับร่างก่อนหน้าอ้างจากเอกสารนี้กับ `carmen-turborepo-backend-v2` โดยตรง พบการแก้ไขสองจุด: (1) เอกสารวางแผนเองระบุใน § "What This Process Does NOT Do" ว่า **"does not generate GL journal entries"** — แต่ฉบับร่างก่อนหน้ากลับเพิ่ม GL posting แบบ `Dr`/`Cr` ทั่ว Section 3 และ 5 ที่ไม่มีอยู่ทั้งในเอกสารวางแผนและใน code; claim เกี่ยวกับ GL ทั้งหมดด้านล่างถูกลบออก (สอดคล้องกับข้อค้นพบเดียวกันบน [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) § 5's GL caveat) (2) เอกสารวางแผน P4 Q1 บันทึก "costing method ล็อกที่ implementation ไม่สามารถเปลี่ยนหลัง go-live" เป็น **เจตนาการออกแบบ** ที่ stakeholder ยืนยัน — ฉบับร่างก่อนหน้ากลับแปลงเป็น validation rule ที่ code บังคับ (`COST_VAL_009` อ้างทั่วทั้งหน้าว่าบล็อกการเปลี่ยนวิธีเมื่อมี non-zero on-hand); การค้นหาทั้ง repo ไม่พบ guard เช่นนั้นเลยใน `carmen-turborepo-backend-v2` (ดู [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 5 item 4) `COST_VAL_009` ถูกลบออกจาก Section 2 และทุกแถวกฎที่อ้างถึง

## 1. ภาพรวม

หน้านี้บันทึกกฎทางธุรกิจที่ดำเนินการกำกับ **โมดูล costing** — เอนจินที่เลือก `cost_per_unit` สำหรับทุก outbound stock movement, รีเฟรช `average_cost_per_unit` ทุก inbound, และ — เฉพาะ business unit ที่ใช้วิธี average — เขียน period-locked `closing_cost_per_unit` ที่ปลายงวด เนื่องจาก costing **ไม่ใช่** โมดูล document แยก — เป็นชั้นพฤติกรรมเหนือ ledger ของ [inventory](/th/inventory/inventory) — ชุดกฎตรงนี้ดูต่างจาก GRN / PR / SR catalogues: ไม่มี document lifecycle ของตัวเอง ไม่มี save / approve / commit progression ไม่มี `doc_status` แต่กฎข้างล่างอธิบาย **เอนจินอ่าน configuration อย่างไร เลือก cost อย่างไร ดำเนินการ arithmetic อย่างไร รีเฟรช average อย่างไร และ anchor ขอบเขตงวดอย่างไร** ทุกกฎ **invoke จาก** inventory transaction post หรือ period-end run ที่อยู่ในโมดูล inventory; โมดูล costing เป็นเจ้าของ logic ของกฎ ไม่ใช่ trigger ไม่มีชั้น RBAC authority แยกซ้อนทับ engine — ดู Section 4

โครงสร้างสองจุดให้สีแก่ทุกกฎข้างล่าง **ประการแรก** **วิธี costing ตั้งค่าที่ business unit ไม่ใช่ per product** (ตาม [costing/01-data-model](/th/inventory/costing/01-data-model) § 5 item 1) เอนจิน resolve วิธีผ่าน `tb_business_unit.calculation_method` (platform schema, default `average`) ครั้งเดียวต่อการเรียก — โดยปกติที่จุดเริ่มต้นของ inventory transaction post — และ apply กับทุก detail line ใน transaction ไม่มี per-product override; mixed FIFO / WA ข้าม products ที่ business unit เดียวกัน **ไม่ใช่** การตั้งค่าที่รองรับ **ประการที่สอง** ทุก cost ที่เลือกตอน post คือ **immutable on write** — เมื่อเขียนไป `tb_inventory_transaction_cost_layer.cost_per_unit` ค่าเป็นส่วนหนึ่งของ historical ledger และไม่สามารถแก้ไขได้แม้วิธีที่ตั้งค่าจะเปลี่ยน Cost revaluation เกิดขึ้นผ่าน (a) credit-note-amount adjustment เขียน `diff_amount` และคำนวณ `cost_per_unit` ของ lot ต้นทางใหม่ตาม `INV_CALC_011` หรือ (b) period-end EOP rollforward ที่ carry closing cost ไปข้างหน้าโดยไม่เปลี่ยน คุณสมบัติทั้งสอง — วิธีเดียวต่อ business unit, immutable cost บน layer row — คือสิ่งที่ทำให้ audit trail ของ costing ป้องกันได้ข้ามงวด

## 2. กฎการตรวจสอบ (Validation Rules)

Rule IDs ตาม `COST_VAL_NNN` Validation ทำงาน **ตอน cost-pick** — เมื่อ inventory transaction post invoke costing engine เพื่อเติม `cost_per_unit` / `average_cost_per_unit` บน cost-layer row ที่จะเขียน ไม่มี save-time หรือ commit-time split; engine ถูกเรียกครั้งเดียวต่อ cost-layer row และคืน valid cost หรือ fail parent transaction

| Rule ID | เงื่อนไข | บังคับเมื่อใด | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `COST_VAL_001` | บริบท business unit resolve เป็น `tb_business_unit` row พร้อม `calculation_method ∈ {average, fifo}` (default `average` ตาม platform schema) หาก JWT / `x-app-id` ไม่ resolve เป็น business unit ที่รู้จัก engine ปฏิเสธการเลือก | ตอน cost-pick | ปฏิเสธ inventory transaction พร้อม `"Cannot resolve costing method: business_unit context missing or invalid."` Parent transaction rollback ตาม `INV_VAL_001` cascade |
| `COST_VAL_002` | สำหรับ **FIFO** cost-pick บน outbound: อย่างน้อยหนึ่ง `tb_inventory_transaction_cost_layer` row exists ที่ `(location_id, product_id)` พร้อม `in_qty − Σ subsequent out_qty > 0` | ตอน cost-pick (outbound) | ปฏิเสธพร้อม `"FIFO: no available cost layer at (location, product) to consume."` Parent transaction ปฏิเสธตาม `INV_VAL_005` (no-negative-balance) |
| `COST_VAL_003` | สำหรับ **WA** cost-pick บน outbound: อย่างน้อย inbound layer หนึ่งมีอยู่ที่ `(location_id, product_id)` เพื่อให้ `average_cost_per_unit` ถูก initialise | ตอน cost-pick (outbound) | ปฏิเสธพร้อม `"Weighted Average: no prior inbound layer at (location, product) to read average from."` |
| `COST_VAL_004` | `cost_per_unit` ที่ engine คืนเป็น non-negative และ finite Constraint เดียวกับ `INV_VAL_007` แต่บังคับใช้เฉพาะที่ cost-pick boundary | ตอน cost-pick | ปฏิเสธพร้อม `"Cost-pick produced an invalid cost_per_unit (negative or non-finite): <value>."` |
| `COST_VAL_005` | สำหรับ **WA** inbound recompute: ค่าเฉลี่ยใหม่คำนวณที่ precision 5dp เต็มก่อนปัดเศษ; inputs intermediate (`prior_on_hand`, `prior_average`, `in_qty`, `in_cost_per_unit`) เป็น non-negative; divisor `(prior_on_hand + in_qty)` เป็นบวกแน่นอน | ตอน cost-pick (inbound, WA เท่านั้น) | ปฏิเสธพร้อม `"Weighted Average recompute: invalid inputs (negative qty / negative cost / zero total qty)."` |
| `COST_VAL_006` | สำหรับ **credit-note-amount** adjustments (`enum_transaction_type = credit_note_amount`): lot ต้นทางที่ระบุโดย `lot_no, lot_index` มีอยู่ใน `tb_inventory_transaction_cost_layer`, ยังไม่ได้ถูกใช้หมด, และ credit-note `diff_amount` เป็น signed | ตอน cost-pick (credit-note path) | ปฏิเสธพร้อม `"Credit-note-amount adjustment: originating lot not found or fully drained without remaining cost rebasing context."` ตาม `INV_VAL_011` |
| `COST_VAL_007` | สำหรับ **count-variance** posts (count completes → `tb_stock_in` / `tb_stock_out` rollup) count-costing source ที่ตั้งค่า (`enum_physical_count_costing_method`) resolve เป็น valid cost | ตอน cost-pick (count-variance) | ปฏิเสธพร้อม `"Count-variance valuation: configured count-costing-method <X> cannot resolve a cost (missing standard_cost / no prior layer)."` |
| `COST_VAL_008` | สำหรับ **end-of-period rollforward** (`enum_transaction_type ∈ {close_period, open_period, eop_in, eop_out}`): snapshot rows ของ closing period คำนวณก่อน open-period rollforward เริ่ม | Period-end orchestration | ปฏิเสธ rollforward run พร้อม `"Cannot rollforward period <YYMM> → next: closing snapshot for <N> (location, product, lot) keys is missing or has null closing_cost_per_unit."` |
| ~~`COST_VAL_009`~~ | **ลบออก — ไม่ใช่กฎจริง** เอกสารออกแบบระดับวางแผน (`docs/persona-doc/System Process/proc-03-cost-calculation.md` P4 Q1 ใน `carmen-inventory-frontend-e2e`) บันทึก "costing method ล็อกที่ implementation ไม่สามารถเปลี่ยนหลัง go-live" เป็น **เจตนาการออกแบบที่ stakeholder ยืนยัน** ไม่ใช่ guard ที่ implement จริง `tb_business_unit.calculation_method` ถูกเขียนจากหน้าจอ platform/cluster-admin (`platform_business-units.controller.ts`); การค้นหาทั้ง repo ของ `carmen-turborepo-backend-v2` ไม่พบการตรวจ on-hand, ไม่พบ drain precondition, และไม่พบ path การปฏิเสธใด ๆ ใน write path นั้นเลย | — | ไม่ถูกบังคับ ถ้า tenant เปลี่ยน `calculation_method` ทั้งที่มี non-zero on-hand วันนี้ ไม่มีอะไรใน backend หยุดได้ — cost-layer rows ที่มีอยู่แล้วยังคง `cost_per_unit`/`average_cost_per_unit` ที่เลือกไว้แล้ว (immutable ตาม Section 4) แต่ movement ใหม่จะใช้ logic cost-pick ของวิธีใหม่ทันที ทำเครื่องหมายเป็นช่องว่างจริงถ้าเรื่องนี้สำคัญกับผู้ใช้เป้าหมาย — ปัจจุบันไม่มีการป้องกัน |
| `COST_VAL_010` | Cost-pick บน **transfers** ระหว่าง locations: `transfer_in` cost equal `transfer_out` cost | ตอน cost-pick (transfer) | ปฏิเสธพร้อม `"Transfer cost mismatch: transfer_in.cost_per_unit must equal transfer_out.cost_per_unit."` |
| `COST_VAL_011` | Cost-pick บน **direct-cost locations** (`tb_location.location_type = direct`): engine **ไม่ run** เพราะ receipt expensed ตอนรับ | ตอน cost-pick (direct location) | ไม่มี error; engine คืน "skipped — direct location, no cost layer required" |
| ~~`COST_VAL_012`~~ | **ลบออก — ไม่มี branch cost-pick เฉพาะ consignment** การค้นหาทั้ง repo ใน `inventory-transaction.service.ts` สำหรับ `consignment` ให้ผลลัพธ์เป็นศูนย์ branch ประเภทที่ตั้งเดียวที่ cost engine แยกจัดการเป็นพิเศษคือ `direct` (Section 5 `COST_POST_005`); location ประเภท `consignment` ถูก cost เหมือน inventory-type receiving location ทั่วไป | — | — |

## 3. กฎการคำนวณ (Calculation Rules)

ค่าการเงินทั้งหมด store เป็น `Decimal(20, 5)` บน cost-layer และ detail rows Display rounding เป็น half-up ไป 2 ตำแหน่งสำหรับ currency amounts และ 3 ตำแหน่งสำหรับปริมาณ Computations intermediate carry precision 5dp เต็ม

Rule IDs ตาม `COST_CALC_NNN` กฎเหล่านี้ **delegate ไป** หรือ **align กับ** inventory-module rules `INV_CALC_001`–`INV_CALC_012`

| Rule ID | สูตร |
| ------- | ------- |
| `COST_CALC_001` (FIFO outbound cost-pick) | เมื่อ `tb_business_unit.calculation_method = fifo` และ cost-pick เป็น outbound: iterate `tb_inventory_transaction_cost_layer` rows ที่ `(location_id, product_id)` ordered ตาม `lot_seq_no` ascending, ดูเฉพาะ rows ที่มี positive remaining balance สำหรับ lot ที่ consume แต่ละ lot ผลิต **หนึ่ง** outbound cost-layer row ที่ `cost_per_unit = lot.cost_per_unit` และ `out_qty = min(lot.remaining, total_out_qty − already_consumed)` Stop เมื่อ `total_out_qty` ถูก consume ครบ Equivalent กับ `INV_CALC_005` |
| `COST_CALC_002` (WA outbound cost-pick) | เมื่อ `calculation_method = average` และ cost-pick เป็น outbound: อ่าน `tb_inventory_transaction_cost_layer.average_cost_per_unit` ล่าสุดที่ `(location_id, product_id)` ผลิต **หนึ่ง** outbound cost-layer row ที่ `cost_per_unit = current_average` Average **ไม่** อัปเดตโดย outbound Equivalent กับ `INV_CALC_006` |
| `COST_CALC_003` (WA inbound recompute) | เมื่อ `calculation_method = average` และ cost-pick เป็น inbound: `new_average = (prior_on_hand × prior_average + in_qty × in_cost_per_unit) / (prior_on_hand + in_qty)` ปัดเศษเป็น 5dp Equivalent กับ `INV_CALC_007` |
| `COST_CALC_004` (FIFO inbound layer creation) | เมื่อ `calculation_method = fifo` และ cost-pick เป็น inbound: สร้าง cost-layer row ใหม่ พร้อม `in_qty > 0`, `cost_per_unit = received_cost`, `lot_no = current_lot_no`, `lot_index = 1`, `lot_seq_no = max(existing lot_seq_no at (location, product)) + 1` `average_cost_per_unit` ก็คำนวณและเก็บแม้ภายใต้ FIFO |
| `COST_CALC_005` (Credit-note-amount lot revaluation) | เมื่อ `enum_transaction_type = credit_note_amount`: เขียน cost-layer row พร้อม `in_qty = 0, out_qty = 0, diff_amount = signed_amount` คำนวณ `cost_per_unit` ของ lot ต้นทางใหม่: `new_lot_cost_per_unit = (original_lot_total_cost + diff_amount) / original_lot_qty` ส่วนที่ **บริโภคไปแล้ว** ไม่ปรับย้อนหลัง Equivalent กับ `INV_CALC_011` |
| `COST_CALC_006` (Period snapshot — closing cost-per-unit) | ที่ period close: `closing_cost_per_unit = closing_total_cost / closing_qty` Equivalent กับ `INV_CALC_010` |
| `COST_CALC_007` (Period rollforward — opening cost preservation) | ที่ period open: `opening_qty / opening_cost_per_unit / opening_total_cost = previous_period.closing_qty / closing_cost_per_unit / closing_total_cost` สำหรับ FIFO, `open_period` cost-layer rows เก็บการแยก **per-lot** เพื่อให้ FIFO sequence carry ข้ามขอบเขต Equivalent กับ `INV_CALC_008` |
| `COST_CALC_008` (Count-variance valuation — by `enum_physical_count_costing_method`) | resolve cost ตาม `enum_physical_count_costing_method` ที่ตั้งค่า: `standard` → `tb_product.standard_cost`; `last` → cost-layer `cost_per_unit` ล่าสุด; `average` → `average_cost_per_unit` ล่าสุด; `last_receiving` → inbound layer ล่าสุด |
| `COST_CALC_009` (Standard cost — recipe baseline) | `tb_product.standard_cost` อ่านโดย recipe costing และโดย `enum_physical_count_costing_method = standard` **ไม่** อ่านโดย FIFO / WA cost-pick การอัปเดต `standard_cost` เป็น prospective |
| `COST_CALC_010` (Rounding) | การปัดเศษทั้งหมดเป็น half-up Stored values ใช้ column precision (`Decimal(20, 5)`); computations intermediate carry 5dp กฎเดียวกับ `INV_CALC_012` Display: 2dp สำหรับ currency, 3dp สำหรับปริมาณ |

### 3.1 ตัวอย่างที่ทำงาน (FIFO, business unit `BU-A` พร้อม `calculation_method = fifo`)

Products สองตัวที่ business unit เดียวกันเป็น FIFO ทั้งคู่ (วิธีเป็น per business unit ไม่ใช่ per product) พิจารณา product `P-1` ที่ `LOC-A` ไม่มี on-hand ก่อน:

- **Inbound 1** (GRN, `good_received_note`): `in_qty = 100`, `cost_per_unit = ฿10.00`, assigned `lot_no = LOT-1`, `lot_index = 1`, `lot_seq_no = 1`
  - Cost-layer row: `in_qty = 100, cost_per_unit = ฿10.00, total_cost = ฿1,000.00, average_cost_per_unit = ฿10.00` (shadow WA)
- **Inbound 2** (GRN): `in_qty = 50`, `cost_per_unit = ฿14.00`, `lot_no = LOT-2`, `lot_index = 1`, `lot_seq_no = 2`
  - Cost-layer row: `in_qty = 50, cost_per_unit = ฿14.00, total_cost = ฿700.00, average_cost_per_unit = (100×10.00 + 50×14.00)/150 = ฿11.33333`
- **Outbound** (SR issue): `out_qty = 80` FIFO consume `LOT-1` ก่อน (`lot_seq_no = 1`)
  - Cost-layer row: `out_qty = 80, cost_per_unit = ฿10.00, total_cost = ฿800.00, from_lot_no = LOT-1` ตาม `COST_CALC_001`
  - `LOT-1` remaining: `100 − 80 = 20`; `LOT-2` ไม่ถูกแตะที่ `50`
  - On-hand valuation: `20 × 10.00 + 50 × 14.00 = ฿900.00`
- **Outbound** (SR issue): `out_qty = 30` FIFO consume `LOT-1` ที่เหลือ (`20 units at ฿10.00`) บวก `10 units` จาก `LOT-2 (at ฿14.00)`
  - Cost-layer row 1: `out_qty = 20, cost_per_unit = ฿10.00, total_cost = ฿200.00, from_lot_no = LOT-1`
  - Cost-layer row 2: `out_qty = 10, cost_per_unit = ฿14.00, total_cost = ฿140.00, from_lot_no = LOT-2`
  - นี่คือ **two-row FIFO outbound** — SR detail line เดียวผลิต cost-layer rows หลายแถว
  - On-hand valuation: `LOT-2: 40 × 14.00 = ฿560.00`

### 3.2 ตัวอย่างที่ทำงาน (WA, business unit `BU-B` พร้อม `calculation_method = average`)

Product `P-1` เดียวกันที่ `LOC-A` movements ทางกายภาพเดียวกัน แต่ที่ business unit ต่างที่ตั้ง WA:

- **Inbound 1**: `in_qty = 100, cost_per_unit = ฿10.00`
  - Cost-layer row: `in_qty = 100, cost_per_unit = ฿10.00, total_cost = ฿1,000.00, average_cost_per_unit = ฿10.00`
- **Inbound 2**: `in_qty = 50, cost_per_unit = ฿14.00`
  - Cost-layer row: `in_qty = 50, cost_per_unit = ฿14.00, total_cost = ฿700.00, average_cost_per_unit = ฿11.33333` ตาม `COST_CALC_003`
- **Outbound** (SR issue): `out_qty = 80` WA อ่าน average ปัจจุบัน `฿11.33333` ตาม `COST_CALC_002`
  - Cost-layer row (single): `out_qty = 80, cost_per_unit = ฿11.33333, total_cost = ฿906.67`
  - Average **ไม่เปลี่ยน**: `฿11.33333`
  - On-hand: `(100 + 50 − 80) = 70 units × ฿11.33333 = ฿793.33`
- **Outbound** (SR issue): `out_qty = 30`
  - Cost-layer row (single): `out_qty = 30, cost_per_unit = ฿11.33333, total_cost = ฿340.00`
  - On-hand: `40 × 11.33333 = ฿453.33`

Physical flow เดียวกัน COGS total ต่าง (FIFO ผลิต `฿800 + ฿200 + ฿140 = ฿1,140`; WA ผลิต `฿906.67 + ฿340.00 = ฿1,246.67`) ความต่างคือ **เพียง** cost-pick rule; qty ledger เหมือนกัน ในสถานการณ์ราคาขาขึ้น FIFO COGS ต่ำกว่าและ ending-inventory value สูงกว่า — ดู [`calculation-methods.md`](./calculation-methods.md) § 5

### 3.3 ตัวอย่างที่ทำงาน (Credit-note-amount revaluation)

ต่อจาก § 3.1 (FIFO): vendor ลดราคา `฿100.00` หลังรับการซื้อ `LOT-2` (เดิม `50 units at ฿14.00, total ฿700.00`) Credit note post เป็น `enum_transaction_type = credit_note_amount`:

- Cost-layer row: `in_qty = 0, out_qty = 0, diff_amount = −฿100.00, transaction_type = credit_note_amount, lot_no = LOT-2`
- `LOT-2` revalued ตาม `COST_CALC_005`: `new_cost_per_unit = (700.00 + (−100.00)) / 50 = ฿12.00`
- Outbound ถัดไปที่ consume จาก `LOT-2` หยิบ `cost_per_unit = ฿12.00` (ไม่ใช่ `฿14.00`); portions ที่บริโภคแล้ว (10 units ที่บริโภคใน outbound ที่สองของ § 3.1 ที่ `฿14.00`) **ไม่** ถูกปรับย้อนหลัง — variance ไหลผ่าน `diff_amount` บน cost-layer ledger เท่านั้น ไม่มีการ post general ledger เกิดขึ้นเลยในเส้นทางนี้ (ไม่มีโค้ด journal-entry อยู่ใน backend); `diff_amount` คือบันทึกถาวรทั้งหมดของการ revalue นี้

## 4. กฎการกำหนดสิทธิ์ (Authorization Rules)

**แก้ไข (ยืนยันแล้ว 2026-07-22):** ฉบับก่อนหน้าของ section นี้กำหนดกฎ `COST_AUTH_NNN` สิบข้อบน RBAC split แบบ Finance / Finance Manager / Inventory Controller / Auditor ซึ่งไม่มีอยู่จริงสำหรับโมดูลนี้ การตรวจสอบกับซอร์สพบว่า: `enum_stage_role` (enum role เดียวใน tenant schema) คือ `{create, approve, purchase, issue, view_only}` — ไม่มีสมาชิก `finance` หรือ `auditor`; `constant/permissions.ts` ใน frontend ไม่มี key เฉพาะ finance หรือ auditor เลย; permission key เดียวที่แตะโมดูลนี้คือ `inventory_management.period_end.view` / `.execute` ทั่วไป (เปิด/ปิดงวด ดู [inventory/period-end](/th/inventory/inventory/period-end)) และ permission CRUD ทั่วไปของแต่ละ source document เอง (เช่น `procurement.credit_note`) ไม่มี tier การอนุมัติ cost-impact ไม่มีการแยก "requester vs. executor" สำหรับการเปลี่ยน configuration และ — ตามการแก้ไขใน Section 2 — ไม่มีการบล็อกที่ code บังคับสำหรับการเปลี่ยน `calculation_method` สอดคล้องกับข้อค้นพบ Finance/Auditor เดียวกันที่ยืนยันแล้วบน [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) § 4

Authorization บนโมดูล costing **บางจริง** — engine เป็น system service ที่ invoke โดย inventory transaction posts gate ด้วย permission ที่ action ที่เรียกมันต้องมีอยู่แล้วเท่านั้น:

| ผู้กระทำ | ทำอะไรได้ | Gate |
| -------- | ---------- | ---- |
| ผู้ถือ `inventory_management.period_end.execute` | จุดชนวนการปิดงวด ซึ่งรัน logic FIFO lot-carry หรือ Average close-and-snapshot ตามที่อธิบายใน Section 5 | `AppIdGuard('period_end.close')` ที่ backend; ไม่มีการตรวจชื่อ role |
| ผู้ถือ `inventory_management.period_end.view` | ดูงวดปัจจุบันและ pre-close review checklist | `AppIdGuard('period_end.findOne' / 'findReview')` |
| ผู้มี permission commit GRN, อนุมัติ SR issue, post inventory adjustment, หรืออนุมัติ credit-note | จุดชนวน cost-pick engine โดยอ้อมเป็นผลข้างเคียงของ permission gate ของเอกสารนั้นเอง (`procurement.*`, `inventory_management.*`) — ไม่มีการตรวจ authorization เพิ่มเติมเฉพาะ costing บนนี้ | ตาม permission ของ source document นั้น ดูหน้า business-rules ของโมดูลนั้นเอง |
| Platform / cluster admin | ตั้งค่า `tb_business_unit.calculation_method` บน business-unit record (`platform_business-units.controller.ts`) | อยู่นอก route ของ wiki module นี้ |
| ทุกคน | ไม่สามารถแก้ `cost_per_unit` หรือ `average_cost_per_unit` บน `tb_inventory_transaction_cost_layer` row ที่ post แล้วผ่าน UI หรือ API ใด ๆ ที่พบในรอบนี้ | ไม่มี update/patch endpoint สำหรับ cost-layer table; การแก้ไขไหลผ่าน credit-note-amount adjustment (`diff_amount`) หรือ compensating stock-in/stock-out ซึ่งทั้งคู่เขียนแถวใหม่แทนที่จะแก้แถวเดิม |

ไม่มีขั้นตอน "ใครทวน cost-pick preview ก่อนอนุมัติ": [inventory-adjustment](/th/inventory/inventory-adjustment) § 1 (ยืนยันแล้ว) พบว่า `tb_stock_in` / `tb_stock_out` documents post ทันทีเมื่อสร้าง — `StockInService.create()` / `StockOutService.create()` เขียน `doc_status = completed` และเรียก ledger ในการเรียกเดียวกัน ไม่ว่า client จะส่งปุ่มไหนมา ไม่มี draft state ไม่มี approval queue จึงไม่มีหน้าจอที่ "Inventory Controller" แยกต่างหากจะทวน FIFO/Average cost-pick preview ก่อน commit

## 5. กฎการ Posting (Posting Rules)

"Posting" ของโมดูล costing คือ cost-layer row write ที่ engine ทำในขณะที่ inventory transaction post กฎข้างล่างอธิบาย **engine เขียนอะไร** บน cost-layer row สำหรับแต่ละ `enum_transaction_type`

Rule IDs ตาม `COST_POST_NNN`

| Rule ID | Trigger | Costing-engine effect |
| ------- | ------- | --------------------- |
| `COST_POST_001` | Inbound ไป inventory-type location (`enum_transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`) | Engine เลือก inbound cost (จาก source document) เขียน cost-layer row: `in_qty > 0`, `cost_per_unit = picked_cost`, `lot_no = current_lot_no`, `lot_index = 1`, `lot_seq_no = max(existing) + 1` ตาม `COST_CALC_004` รีเฟรช `average_cost_per_unit` ตาม `COST_CALC_003` |
| `COST_POST_002` | Outbound จาก inventory-type location (`enum_transaction_type ∈ {issue, adjustment_out, transfer_out}`) | Engine resolve `calculation_method` ของ business unit **FIFO branch** ตาม `COST_CALC_001` **WA branch** ตาม `COST_CALC_002` Average **ไม่** รีเฟรช |
| `COST_POST_003` | Credit-note-amount adjustment (`enum_transaction_type = credit_note_amount`) | Engine เขียน cost-layer row พร้อม `in_qty = 0`, `out_qty = 0`, `diff_amount = signed_amount`, `transaction_type = credit_note_amount`, `lot_no = originating_lot` อัปเดต `cost_per_unit` ของ lot ต้นทางตาม `COST_CALC_005` |
| `COST_POST_004` | Credit-note-quantity adjustment (`enum_transaction_type = credit_note_quantity`) | Engine ปฏิบัติเป็น outbound: เขียน cost-layer row พร้อม `out_qty = credit_qty`, `cost_per_unit = originating_lot.cost_per_unit`, `from_lot_no = originating_lot` |
| `COST_POST_005` | Receipt ไป direct-cost location | **แก้ไขแล้ว:** engine **ไม่** skip layer — `createFifoTransaction` / `createAverageTransaction` เขียนแถว cost-layer ขาเข้าตามปกติ แล้วเขียนแถวขาออกชดเชยอัตโนมัติทันที (`createDirectExpenseOut`) ที่ต้นทุนเดียวกันภายใต้ transaction header เดียวกัน เพื่อให้ยอดคงเหลือสุทธิของ location เป็นศูนย์ Direct receipt ถูกยกเว้นจากการคำนวณ weighted-average (ไม่มีผลต่อ `average_cost_per_unit`) ไม่มีผลกับ GL — ไม่มีโค้ด journal-posting ที่ใดใน backend |
| ~~`COST_POST_006`~~ | **ลบออก — ไม่มี posting branch เฉพาะ consignment** (ดู `COST_VAL_012` ที่ถูกลบด้านบน) Consignment-location receipt ถูก cost เหมือน inventory-type receipt ทั่วไป | — |
| `COST_POST_007` | Period close (`enum_inventory_doc_type = close`) | Invoke จาก `PeriodEndService.closeCurrent` gate ด้วย `inventory_management.period_end.execute` ของผู้เรียกเท่านั้น — ไม่มี RBAC ระดับ engine แยก **เฉพาะ business unit ที่ใช้วิธี average:** สำหรับแต่ละ bucket `(location_id, product_id)` คำนวณ `closing_qty / closing_cost_per_unit / closing_total_cost` ตาม `COST_CALC_006` และเขียนไป `tb_period_snapshot` บวกแถว cost-layer `close_period` **business unit ที่ใช้วิธี FIFO:** ไม่มีการเขียนแถว `tb_period_snapshot` เลย — `findAllRemainingLots` + `writeCloseTransaction` นำยอดคงเหลือของ lot ไปต่อเป็นแถว cost-layer `close_period` แทน (`period-end.close-transaction.helper.ts`) การแยกนี้พลาดง่ายถ้าอ่านแค่เส้นทาง average |
| `COST_POST_008` | Period open (`enum_inventory_doc_type = open`) | Chained กับ `COST_POST_007` เขียน `open_period` cost-layer rows สำหรับงวดถัดไปที่ `cost_per_unit = previous.closing_cost_per_unit`, `lot_seq_no` รักษาตาม `COST_CALC_007` |
| `COST_POST_009` | Count-variance posting | Engine resolve count-costing source ตาม `enum_physical_count_costing_method` และเลือก cost ตาม `COST_CALC_008` |
| `COST_POST_010` | Standard-cost change บน `tb_product.standard_cost` | **ไม่มีผลกับ cost-layer** Standard cost เป็น reference value; การอัปเดตไม่เขียน cost-layer row การเปลี่ยนเป็น prospective |

State diagram สำหรับ cost-layer write (degenerate, single-state, mirror inventory):

```
[*] → cost-layer row written (with cost_per_unit + average_cost_per_unit set at post time)
   → (immutable: no edit; revaluation only via credit-note-amount diff_amount, or
      period-end rollforward writing open_period / close_period anchor rows)
```

### 5.1 Cost Method × Trigger Mapping — เอกสารวางแผน vs Code

Costing ไม่มี per-document status lifecycle Engine cost ถูก invoke โดย inventory-affecting transactions ตารางข้างล่าง map แต่ละ trigger transaction กับผล Average (AVCO) และ FIFO คอลัมน์ "Notes / Source" อ้างเอกสารวางแผนจริงที่ `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/*.md` เมื่อมี บวก code path ที่รอบนี้ตรวจสอบแต่ละแถวใหม่ — ฉบับร่างก่อนหน้าอ้างเอกสารชุดเดียวกันนี้ด้วย path ที่ไม่มีอยู่จริง (`Test_case/System_Process/...`) พร้อม "capture date" ที่กุขึ้นเอง path และการตรวจสอบ code ที่ถูกต้องอยู่ด้านล่าง "AVCO" คือคำที่เอกสารวางแผนใช้เรียกสิ่งเดียวกับที่ Prisma schema เรียก `average`

| Trigger transaction | AVCO effect | FIFO effect | Notes / Source |
|---|---|---|---|
| GRN (stock-in) | Re-average: `new_avg = (prior_qty × prior_avg + in_qty × in_cost) / (prior_qty + in_qty)` | เพิ่ม cost layer ใหม่; `lot_seq_no` increment | `COST_CALC_003` / `COST_CALC_004`; ยืนยันใน `InventoryTransactionService.createFifoTransaction` / `createAverageTransaction`; เจตนาออกแบบใน `tx-01-grn.md` |
| CRN (credit note) | Re-average; qty ลบจาก on-hand | Layer เก่าที่สุดถูก consume ที่ต้นทุน lot ต้นทาง (`credit_note_quantity`) หรือ lot revalued (`credit_note_amount` ผ่าน `diff_amount`) | `COST_POST_003` / `COST_POST_004`; ยืนยันใน code (`createFifoCreditNoteQty/Amount`, `createAverageCreditNoteQty/Amount`) |
| Stock In adjustment | Re-average (same as GRN inbound path) | เพิ่ม cost layer ใหม่ที่ unit cost ที่ป้อนด้วยมือ | `COST_CALC_003` / `COST_CALC_004`; ยืนยัน — ทั้ง GRN และ manual stock-in เรียก inbound cost-pick path เดียวกัน |
| Stock Out adjustment | Cost held | Cost layer เก่าที่สุดถูก consume ก่อน | `COST_CALC_001` / `COST_CALC_002`; ยืนยันใน code |
| Issues (SR / stock-issue) | Cost held (เหมือน stock-out) | Cost layer เก่าที่สุดถูก consume | `COST_POST_002`; ยืนยันใน code |
| Physical Count — variance exists | Re-average per direction | Overage → cost layer ใหม่; shortage → layer เก่าที่สุดถูก consume | `COST_CALC_008`; count-variance cost source คือ `enum_physical_count_costing_method` แยกจาก AVCO/FIFO pick ปกติ — ดู [01-data-model](/th/inventory/costing/01-data-model) § 2.6 ว่าการเขียน cost-layer ของ count-variance rollup ถูกตรวจสอบแยกในรอบ resync ของ physical-count เองหรือไม่ ไม่ได้ตรวจซ้ำในรอบนี้ |
| Physical Count — no variance | **NOT triggered** | **NOT triggered** | ไม่มี qty change; ไม่มี cost-layer write — สอดคล้องกับโมเดล `Σin − Σout` ของ `getLocationBalance` |
| Store Requisition (SR) | Cost pass-through | Cost pass-through | `COST_POST_002` เอกสารวางแผน (`proc-03-cost-calculation.md` P1/P2) เรียกสิ่งนี้ว่า "no recalculation — internal movement at book value"; code ยืนยันว่า cost engine ถูก invoke เพื่อเลือก cost ของ layer ที่มีอยู่ แต่ไม่สร้าง FIFO layer ใหม่และไม่ re-average |
| Spot Check | **PENDING** | **PENDING** | ยืนยันแยกในรอบ resync ของโมดูล spot-check เอง: `submit()` ไม่มีผล posting ใด ๆ เลย — ดู [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) § 5.1 |
| End Period Close | วิธี average: lock period cost, เขียน `tb_period_snapshot` | วิธี FIFO: นำยอด lot ไปต่อ, **ไม่เขียน** `tb_period_snapshot` | `COST_POST_007` / `COST_POST_008`; ยืนยันใน `period-end.close-transaction.helper.ts` / `period-end.close-average.helper.ts` — ดูการแก้ไขบน `COST_POST_007` ด้านบน |

### 5.2 Discrepancy Callouts — เอกสารวางแผน vs Code

> ⚠️ **SR cost-pick เป็น pass-through — ไม่มี AVCO re-average, ไม่มี FIFO layer ใหม่** Store Requisition ย้ายสินค้าจาก inventory location ไป Direct หรือ Consignment destination ที่ existing unit cost Engine cost ถูก invoke (ตาม `COST_POST_002`) เพื่อเลือก existing layer cost แต่ AVCO ไม่ re-average และ FIFO ไม่สร้าง layer ใหม่ ยืนยันกับ `inventory-transaction.service.ts` โดยตรง; เหตุผลการออกแบบ ("internal movement at book value, no value gained or lost") ระบุอยู่ในเอกสารวางแผน `proc-03-cost-calculation.md` § "SR Exception — Why No Recalc" (`../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/`)

> ⚠️ **Costing method ไม่มีการล็อกที่ code บังคับ แม้จะมีเจตนาออกแบบ** เอกสารวางแผนบันทึก "costing method ล็อกที่ implementation ไม่สามารถเปลี่ยนหลัง go-live" เป็น **requirement ที่ stakeholder ยืนยัน** — แต่ไม่ใช่สิ่งที่ code ปัจจุบันทำ ดู `COST_VAL_009` ที่ถูกลบใน Section 2: ไม่มีการตรวจ on-hand ไม่มี drain precondition และไม่มี rejection path ใด ๆ ใน write path ของ `tb_business_unit.calculation_method` (`platform_business-units.controller.ts`) ถือว่านี่เป็นช่องว่างจริงระหว่างเจตนาการออกแบบกับ implementation ไม่ใช่กฎที่บังคับใช้

> ⚠️ **Physical Count cost source ตั้งค่าได้ ไม่ใช่ fixed** Count-variance posts ใช้ `enum_physical_count_costing_method` (`standard`, `last`, `average`, `last_receiving`) เพื่อเลือก unit cost สำหรับ variance — แยกจาก AVCO/FIFO cost-pick บนธุรกรรมปกติ ทั้ง `carmen/docs` และเอกสารวางแผนชุด `System Process` ไม่ได้ระบุ enum นี้โดยชื่อ Source: [01-data-model](/th/inventory/costing/01-data-model) § 2.6; `COST_CALC_008`

> ⚠️ **เส้นทาง CRN lot cost reversal — ต้องตรวจสอบซ้ำกับรอบ resync ของโมดูล credit-note เอง** ว่า CRN กลับ lot cost ของ GRN เดิมหรือใช้ cost ปัจจุบันถูกบันทึกเป็น "TBC" ในเอกสารวางแผน (`proc-03-cost-calculation.md` P4 Q5) ตอนที่เขียน Prisma engine มีสอง code path แยกกัน — `credit_note_quantity` (คืนที่ต้นทุน lot ต้นทาง) และ `credit_note_amount` (revalue ผ่าน `diff_amount`) — ยืนยันว่าทั้งคู่มีอยู่ใน `inventory-transaction.service.ts` ส่วน UX flow ไหน trigger path ไหนยังไม่ได้ตรวจสอบซ้ำในรอบนี้

> ⚠️ **การเก็บ cost multi-currency — ยังไม่ได้ตรวจสอบในรอบนี้** ว่า cost เก็บใน base currency เท่านั้นหรือพร้อม FX conversion ที่ preserve ต่อ layer ถูกบันทึกเป็น "TBC" ในเอกสารวางแผน (`proc-03-cost-calculation.md` P4 Q6) และยังไม่ได้ตรวจสอบซ้ำกับ `inventory-transaction.service.ts` ในรอบนี้ ตัวอย่างที่ทำงานทั้งหมดในหน้านี้สมมติ single currency (Thai Baht `฿`)

## 6. กฎข้ามโมดูล (Cross-Module Rules)

Rule IDs ตาม `COST_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | ---- |
| `COST_XMOD_001` | [inventory](/th/inventory/inventory) | Cost-layer ledger `tb_inventory_transaction_cost_layer` เป็นของโมดูล inventory; costing engine คือ **ชั้นพฤติกรรม** ที่อ่านและเขียน ledger ทุก cost-pick ในโมดูลนี้ invoke จาก `INV_POST_001`–`INV_POST_010` event |
| `COST_XMOD_002` | [good-receive-note](/th/inventory/good-receive-note) | GRN commit (`saved → committed`) invoke `COST_POST_001` `cost_per_unit` ที่เขียนคือ unit cost ของ GRN line **หลัง extra-cost allocation** |
| `COST_XMOD_003` | [store-requisition](/th/inventory/store-requisition) | SR issue ที่อนุมัติ invoke `COST_POST_002` สำหรับ outbound ที่ source location ไม่มีหน้าจอ cost-pick preview ในแอป — เอกสาร SR post ผ่าน approval chain ปกติโดยไม่มีขั้นตอนทวน cost แยกที่พบในรอบนี้ สำหรับ inter-location transfers, `COST_VAL_010` บังคับ `transfer_in.cost_per_unit = transfer_out.cost_per_unit` |
| `COST_XMOD_004` | [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) | Count variance post ผ่าน `COST_POST_009` Source ของ valuation คือ `enum_physical_count_costing_method` ตาม `COST_CALC_008` |
| `COST_XMOD_005` | [inventory-adjustment](/th/inventory/inventory-adjustment) | Manual `tb_stock_in` / `tb_stock_out` adjustments invoke `COST_POST_001` (inbound) หรือ `COST_POST_002` (outbound) |
| `COST_XMOD_006` | Credit note (vendor) | Vendor credit notes invoke `COST_POST_003` (amount-only — revaluation) หรือ `COST_POST_004` (quantity-only) เส้นทาง credit-note-amount คือ **กลไก cost-revaluation canonical** ในระบบ — ไม่มี update/patch endpoint บน cost-layer table สำหรับการแก้ cost โดยตรงแบบอื่นเลย |
| `COST_XMOD_007` | [recipe](/th/inventory/recipe) | Recipe costing อ่าน `tb_inventory_transaction_cost_layer.average_cost_per_unit` (ล่าสุดที่ `(location, product)`) สำหรับ recipe's ingredient cost basis ภายใต้ WA |
| `COST_XMOD_008` | [product](/th/inventory/product) | `tb_product.standard_cost` คือ recipe baseline และ `standard` count-costing source ตาม `COST_CALC_009` การอัปเดต `standard_cost` เป็น prospective |
| ~~`COST_XMOD_009`~~ | ~~Finance / GL~~ | **ลบออกเพราะยังไม่ยืนยัน** ไม่พบโค้ด reconciliation ระหว่าง inventory กับ GL, GL control account, หรือกลไก reconciliation-exception ที่ใดใน backend เลย — สอดคล้องกับข้อค้นพบเดียวกันบน [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) `INV_XMOD_008` ซึ่งถูกแก้ไขเป็น "Removed as unconfirmed" แล้วในรอบ resync ของโมดูล inventory เมื่อ 2026-07-15 `tb_period_snapshot.closing_total_cost` (เฉพาะงวดที่ใช้วิธี average) คือสิ่งที่ใกล้เคียงที่สุดกับตัวเลข period-end valuation ที่โมดูลนี้ผลิต ส่วนว่าระบบปลายน้ำใดใช้ค่านี้เป็นตัวเลขงบดุลหรือไม่อยู่นอกขอบเขตของโมดูลนี้ |
| `COST_XMOD_010` | All movement-generating modules | Costing engine เป็น **chokepoint เดียว** สำหรับ cost-flow ทุก cost-layer row เขียนโดย engine; ทุกตัวเลข COGS ในระบบ trace กลับไปยัง engine-written row |

## 7. References

- `../carmen/docs/costing/enhanced-costing-engine.md`
- Sibling: [calculation-methods.md](./calculation-methods.md)
- Sibling: [01-data-model.md](./01-data-model.md)
- Related: [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_VAL_001`–`INV_VAL_013`, `INV_CALC_001`–`INV_CALC_012`, `INV_POST_001`–`INV_POST_012`, `INV_XMOD_001`–`INV_XMOD_010` (หลายข้อถูกแก้ไขในรอบ 2026-07-15) — หมายเหตุแก้ไข § 4 ของหน้านั้นคือแหล่งที่มาของการเขียนใหม่ Section 4 ของหน้านี้ (ไม่พบ role gate แยกเหนือ engine)
- Related: [good-receive-note/02-business-rules](/th/inventory/good-receive-note/02-business-rules) — extra-cost allocation rules
- Related: [product](/th/inventory/product)
- Backend rule implementation (เมื่อเพิ่ม): `../carmen-turborepo-backend-v2/apps/`
