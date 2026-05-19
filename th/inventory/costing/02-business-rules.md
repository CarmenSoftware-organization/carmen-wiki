---
title: การคำนวณต้นทุน (Costing) — Business Rules
description: การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting การปลายงวด และกฎข้ามโมดูลสำหรับ costing
published: true
date: 2026-05-19T23:55:00.000Z
tags: costing, business-rules, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `COST_VAL_*` validation &nbsp;·&nbsp; `COST_AUTH_*` permission &nbsp;·&nbsp; `COST_CALC_*` calc &nbsp;·&nbsp; `COST_POST_*` posting &nbsp;·&nbsp; `COST_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 85 กฎ
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **Status lifecycle:** Section 5.1 (ที่มี) carry Live UI vs BRD discrepancy callouts

## 1. ภาพรวม

หน้านี้บันทึกกฎทางธุรกิจที่ดำเนินการกำกับ **โมดูล costing** — เอนจินที่เลือก `cost_per_unit` สำหรับทุก outbound stock movement, รีเฟรช `average_cost_per_unit` ทุก inbound, และเขียน period-locked `closing_cost_per_unit` ที่ปลายงวด เนื่องจาก costing **ไม่ใช่** โมดูล document แยก — เป็นชั้นพฤติกรรมเหนือ ledger ของ [inventory](/th/inventory/inventory) — ชุดกฎตรงนี้ดูต่างจาก GRN / PR / SR catalogues: ไม่มี document lifecycle ของตัวเอง ไม่มี save / approve / commit progression ไม่มี `doc_status` แต่กฎข้างล่างอธิบาย **เอนจินอ่าน configuration อย่างไร เลือก cost อย่างไร ดำเนินการ arithmetic อย่างไร รีเฟรช average อย่างไร anchor ขอบเขตงวดอย่างไร และ gate Finance authorities เหนือ resulting valuation อย่างไร** ทุกกฎ **invoke จาก** inventory transaction post หรือ period-end run ที่อยู่ในโมดูล inventory; โมดูล costing เป็นเจ้าของ logic ของกฎ ไม่ใช่ trigger

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
| `COST_VAL_009` | การเปลี่ยนวิธี costing บน active business unit ถูก **บล็อก** ถ้า product ใด ๆ ที่ business unit นั้นมี non-zero on-hand | ที่ configuration save | ปฏิเสธพร้อม `"Cannot change calculation_method on business unit <code>: <N> products have non-zero on-hand. Drain stock or run elevated migration script."` Mirror `INV_XMOD_009` |
| `COST_VAL_010` | Cost-pick บน **transfers** ระหว่าง locations: `transfer_in` cost equal `transfer_out` cost | ตอน cost-pick (transfer) | ปฏิเสธพร้อม `"Transfer cost mismatch: transfer_in.cost_per_unit must equal transfer_out.cost_per_unit."` |
| `COST_VAL_011` | Cost-pick บน **direct-cost locations** (`tb_location.location_type = direct`): engine **ไม่ run** เพราะ receipt expensed ตอนรับ | ตอน cost-pick (direct location) | ไม่มี error; engine คืน "skipped — direct location, no cost layer required" |
| `COST_VAL_012` | Cost-pick บน **consignment locations** (`tb_location.location_type = consignment`): engine เขียน cost-layer row พร้อมต้นทุนรับ (สำหรับ memo register) แต่ flag row เป็น consignment | ตอน cost-pick (consignment location) | ไม่มี error; engine เขียน flagged cost-layer row |

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
- Outbound ถัดไปที่ consume จาก `LOT-2` หยิบ `cost_per_unit = ฿12.00` (ไม่ใช่ `฿14.00`); portions ที่บริโภคแล้ว (10 units ที่บริโภคใน outbound ที่สองของ § 3.1 ที่ `฿14.00`) **ไม่** ถูกปรับย้อนหลัง

## 4. กฎการกำหนดสิทธิ์ (Authorization Rules)

Rule IDs ตาม `COST_AUTH_NNN` Authorization บนโมดูล costing คือ **บาง** — engine เป็น system service ที่ invoke โดย inventory transaction posts และ per-movement authorization gates อยู่บนโมดูล inventory (`INV_AUTH_001`–`INV_AUTH_010`) และ source-module documents (GRN, SR, count, credit-note) กฎข้างล่างครอบคลุม **costing-specific** authorities

| Rule ID | Subject | สิทธิ์ | Constraint |
| ------- | ------- | ----- | ---------- |
| `COST_AUTH_001` | System Administrator | Configure `tb_business_unit.calculation_method` (FIFO ↔ average) | Sysadmin-only Mirror `INV_AUTH_008` Change ถูกบล็อกบน business unit ที่มี non-zero on-hand ตาม `COST_VAL_009` |
| `COST_AUTH_002` | System Administrator | Configure `enum_physical_count_costing_method` (count-variance source) | Sysadmin-only |
| `COST_AUTH_003` | System Administrator | Update `tb_product.standard_cost` (reference / standard cost) | จัดการโดย cost-control function ภายใน Finance โดยทั่วไป แต่ configuration write underlying เป็น Sysadmin / product-config |
| `COST_AUTH_004` | Finance | อ่านและอนุมัติ cost-impact reports | Finance มี read เต็มบน `tb_inventory_transaction_cost_layer` และ `tb_period_snapshot` Mirror `INV_AUTH_005`'s read scope |
| `COST_AUTH_005` | Finance | อนุมัติ credit-note-amount adjustments | Finance อนุมัติ `tb_credit_note` document; inventory module fires `INV_POST_007` ซึ่ง invoke costing engine's `COST_CALC_005` revaluation |
| `COST_AUTH_006` | Finance Manager | เซ็นรับรอง period-end valuation (locked `tb_period_snapshot.closing_total_cost`) | Period-end valuation sign-off เป็นส่วนของ Finance Manager's `closed → locked` advance ตาม `INV_AUTH_006` |
| `COST_AUTH_007` | Inventory Controller | อ่าน cost-pick previews บน outbound documents ที่กำลังอนุมัติ | Read-only Same read scope บน `tb_inventory_transaction_cost_layer` เหมือน inventory; ไม่มี write |
| `COST_AUTH_008` | Auditor | Read-only access to full cost-layer ledger, period snapshots, configuration history | Mirror `INV_AUTH_009` |
| `COST_AUTH_009` | System / scheduled job | Run cost-pick engine | Engine เป็น system service ที่ invoke โดย inventory transaction posts ภายใต้ RBAC ของ actor |
| `COST_AUTH_010` | All transactional roles | ไม่สามารถแก้ `cost_per_unit` หรือ `average_cost_per_unit` บน posted cost-layer row | Cost-layer rows เป็น immutable ตาม inventory module's `INV_POST_012` |

## 5. กฎการ Posting (Posting Rules)

"Posting" ของโมดูล costing คือ cost-layer row write ที่ engine ทำในขณะที่ inventory transaction post กฎข้างล่างอธิบาย **engine เขียนอะไร** บน cost-layer row สำหรับแต่ละ `enum_transaction_type`

Rule IDs ตาม `COST_POST_NNN`

| Rule ID | Trigger | Costing-engine effect |
| ------- | ------- | --------------------- |
| `COST_POST_001` | Inbound ไป inventory-type location (`enum_transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`) | Engine เลือก inbound cost (จาก source document) เขียน cost-layer row: `in_qty > 0`, `cost_per_unit = picked_cost`, `lot_no = current_lot_no`, `lot_index = 1`, `lot_seq_no = max(existing) + 1` ตาม `COST_CALC_004` รีเฟรช `average_cost_per_unit` ตาม `COST_CALC_003` |
| `COST_POST_002` | Outbound จาก inventory-type location (`enum_transaction_type ∈ {issue, adjustment_out, transfer_out}`) | Engine resolve `calculation_method` ของ business unit **FIFO branch** ตาม `COST_CALC_001` **WA branch** ตาม `COST_CALC_002` Average **ไม่** รีเฟรช |
| `COST_POST_003` | Credit-note-amount adjustment (`enum_transaction_type = credit_note_amount`) | Engine เขียน cost-layer row พร้อม `in_qty = 0`, `out_qty = 0`, `diff_amount = signed_amount`, `transaction_type = credit_note_amount`, `lot_no = originating_lot` อัปเดต `cost_per_unit` ของ lot ต้นทางตาม `COST_CALC_005` |
| `COST_POST_004` | Credit-note-quantity adjustment (`enum_transaction_type = credit_note_quantity`) | Engine ปฏิบัติเป็น outbound: เขียน cost-layer row พร้อม `out_qty = credit_qty`, `cost_per_unit = originating_lot.cost_per_unit`, `from_lot_no = originating_lot` |
| `COST_POST_005` | Receipt ไป direct-cost location | Engine **ไม่เขียน** cost-layer row ตาม `COST_VAL_011` Engine คืน "skipped — direct location" |
| `COST_POST_006` | Receipt ไป consignment location | Engine เขียน memo cost-layer row พร้อม `in_qty = consignment_qty`, `cost_per_unit = consignment_unit_cost` flagged ผ่าน `dimension` / `info` JSON เป็น consignment |
| `COST_POST_007` | Period close (`enum_inventory_doc_type = close`) | System-scope post ตาม `COST_AUTH_009` คำนวณ `closing_qty / closing_cost_per_unit / closing_total_cost` ตาม `COST_CALC_006` และเขียนไป `tb_period_snapshot` |
| `COST_POST_008` | Period open (`enum_inventory_doc_type = open`) | Chained กับ `COST_POST_007` เขียน `open_period` cost-layer rows สำหรับงวดถัดไปที่ `cost_per_unit = previous.closing_cost_per_unit`, `lot_seq_no` รักษาตาม `COST_CALC_007` |
| `COST_POST_009` | Count-variance posting | Engine resolve count-costing source ตาม `enum_physical_count_costing_method` และเลือก cost ตาม `COST_CALC_008` |
| `COST_POST_010` | Standard-cost change บน `tb_product.standard_cost` | **ไม่มีผลกับ cost-layer** Standard cost เป็น reference value; การอัปเดตไม่เขียน cost-layer row การเปลี่ยนเป็น prospective |

State diagram สำหรับ cost-layer write (degenerate, single-state, mirror inventory):

```
[*] → cost-layer row written (with cost_per_unit + average_cost_per_unit set at post time)
   → (immutable: no edit; revaluation only via credit-note-amount diff_amount, or
      period-end rollforward writing open_period / close_period anchor rows)
```

### 5.1 Cost Method × Trigger Mapping — Live UI vs BRD

Costing ไม่มี per-document status lifecycle Engine cost ถูก invoke โดย inventory-affecting transactions ตารางข้างล่าง map แต่ละ trigger transaction กับผล AVCO (Weighted Average) และ FIFO Sources: `Test_case/System_Process/proc-03-cost-calculation.md` (capture date 2026-04-26)

| Trigger transaction | AVCO effect | FIFO effect | Notes / Source |
|---|---|---|---|
| GRN (stock-in) | Re-average: `new_avg = (prior_qty × prior_avg + in_qty × in_cost) / (prior_qty + in_qty)` | เพิ่ม cost layer ใหม่; `lot_seq_no` increment | `COST_CALC_003` / `COST_CALC_004`; `Test_case/System_Process/tx-01-grn.md` |
| CRN (credit-return) | Re-average; qty ลบจาก on-hand | Layer เก่าที่สุดถูก consume ที่ต้นทุน lot ต้นทาง (`credit_note_quantity`) หรือ lot revalued (`credit_note_amount` ผ่าน `diff_amount`) | `COST_POST_003` / `COST_POST_004` |
| Stock In adjustment | Re-average (same as GRN inbound path) | เพิ่ม cost layer ใหม่ที่ unit cost ที่ป้อนด้วยมือ | `COST_CALC_003` / `COST_CALC_004` |
| Stock Out adjustment | Cost held | Cost layer เก่าที่สุดถูก consume ก่อน | `COST_CALC_001` / `COST_CALC_002` |
| Issues | Cost held (เหมือน stock-out) | Cost layer เก่าที่สุดถูก consume | `COST_POST_002` |
| Sales Consumption (SC) | Cost held | Cost layer เก่าที่สุดถูก consume | `COST_POST_002` |
| Wastage Report (WR) | Cost held (WR approval generates Stock Out adj) | Cost layer เก่าที่สุดถูก consume | `COST_POST_002` |
| Physical Count — variance exists | Re-average per direction | Overage → cost layer ใหม่; shortage → layer เก่าที่สุดถูก consume | `COST_POST_009`; `COST_CALC_008` |
| Physical Count — no variance | **NOT triggered** | **NOT triggered** | ไม่มี qty change; ไม่มี cost-layer write |
| Store Requisition (SR) | Cost pass-through | Cost pass-through | `COST_POST_002`, `COST_XMOD_003` |
| Spot Check | **PENDING** | **PENDING** | Variance posting ยังไม่ implement ตาม `Test_case/System_Process/INDEX.md` |
| End Period Close | Lock period cost; no new recalc | Same | `COST_POST_007` / `COST_POST_008` |

### 5.2 Discrepancy Callouts — Live behaviour vs BRD / carmen/docs

> ⚠️ **SR cost-pick เป็น pass-through — ไม่มี AVCO re-average, ไม่มี FIFO layer ใหม่** Store Requisition ย้ายสินค้าจาก inventory location ไป Direct หรือ Consignment destination ที่ existing unit cost Engine cost ถูก invoke (ตาม `COST_POST_002` และ `COST_XMOD_003`) เพื่อเลือก existing layer cost แต่ AVCO ไม่ re-average และ FIFO ไม่สร้าง layer ใหม่ ยืนยันใน `Test_case/System_Process/proc-03-cost-calculation.md` P1

> ⚠️ **Costing method ล็อกที่ implementation — ไม่สามารถเปลี่ยนหลัง go-live** `tb_business_unit.calculation_method` (AVCO หรือ FIFO) ตั้งค่า per Business Unit ที่ implementation และ **ล็อกถาวร** เมื่อ inventory live `COST_VAL_009` บล็อกการเปลี่ยนใด ๆ บน business unit ที่มี non-zero on-hand

> ⚠️ **Physical Count cost source ตั้งค่าได้ ไม่ใช่ fixed** Count-variance posts ใช้ `enum_physical_count_costing_method` (`standard`, `last`, `average`, `last_receiving`) เพื่อเลือก unit cost สำหรับ variance

> ⚠️ **CRN lot cost reversal path TBC** ว่า CRN กลับ lot cost ของ GRN เดิมหรือใช้ cost ปัจจุบันยืนยันเป็น "TBC" ใน `Test_case/System_Process/proc-03-cost-calculation.md` P4 Q5

> ⚠️ **Multi-currency cost storage TBC** ว่า costs เก็บใน base currency เท่านั้นหรือพร้อม FX conversion preserved per-layer เป็น TBC ตัวอย่างปัจจุบันทั้งหมดสมมติ single currency (Thai Baht `฿`)

## 6. กฎข้ามโมดูล (Cross-Module Rules)

Rule IDs ตาม `COST_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | ---- |
| `COST_XMOD_001` | [inventory](/th/inventory/inventory) | Cost-layer ledger `tb_inventory_transaction_cost_layer` เป็นของโมดูล inventory; costing engine คือ **ชั้นพฤติกรรม** ที่อ่านและเขียน ledger ทุก cost-pick ในโมดูลนี้ invoke จาก `INV_POST_001`–`INV_POST_010` event |
| `COST_XMOD_002` | [good-receive-note](/th/inventory/good-receive-note) | GRN commit (`saved → committed`) invoke `COST_POST_001` `cost_per_unit` ที่เขียนคือ unit cost ของ GRN line **หลัง extra-cost allocation** |
| `COST_XMOD_003` | [store-requisition](/th/inventory/store-requisition) | SR issue ที่อนุมัติ invoke `COST_POST_002` สำหรับ outbound ที่ source location สำหรับ inter-location transfers, `COST_VAL_010` บังคับ `transfer_in.cost_per_unit = transfer_out.cost_per_unit` |
| `COST_XMOD_004` | [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) | Count variance post ผ่าน `COST_POST_009` Source ของ valuation คือ `enum_physical_count_costing_method` ตาม `COST_CALC_008` |
| `COST_XMOD_005` | [inventory-adjustment](/th/inventory/inventory-adjustment) | Manual `tb_stock_in` / `tb_stock_out` adjustments invoke `COST_POST_001` (inbound) หรือ `COST_POST_002` (outbound) |
| `COST_XMOD_006` | Credit note (vendor) | Vendor credit notes invoke `COST_POST_003` (amount-only — revaluation) หรือ `COST_POST_004` (quantity-only) เส้นทาง credit-note-amount คือ **กลไก cost-revaluation canonical** ในระบบ |
| `COST_XMOD_007` | [recipe](/th/inventory/recipe) | Recipe costing อ่าน `tb_inventory_transaction_cost_layer.average_cost_per_unit` (ล่าสุดที่ `(location, product)`) สำหรับ recipe's ingredient cost basis ภายใต้ WA |
| `COST_XMOD_008` | [product](/th/inventory/product) | `tb_product.standard_cost` คือ recipe baseline และ `standard` count-costing source ตาม `COST_CALC_009` การอัปเดต `standard_cost` เป็น prospective |
| `COST_XMOD_009` | Finance / GL | Period-end valuation (`tb_period_snapshot.closing_total_cost` sum) คือตัวเลขสินทรัพย์ inventory ในงบดุลสำหรับ closed period Finance Manager ล็อกค่านี้ตาม `COST_AUTH_006` |
| `COST_XMOD_010` | All movement-generating modules | Costing engine เป็น **chokepoint เดียว** สำหรับ cost-flow ทุก cost-layer row เขียนโดย engine; ทุกตัวเลข COGS ในระบบ trace กลับไปยัง engine-written row |

## 7. References

- `../carmen/docs/costing/enhanced-costing-engine.md`
- Sibling: [calculation-methods.md](./calculation-methods.md)
- Sibling: [01-data-model.md](./01-data-model.md)
- Related: [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_VAL_001`–`INV_VAL_013`, `INV_CALC_001`–`INV_CALC_012`, `INV_POST_001`–`INV_POST_012`, `INV_AUTH_001`–`INV_AUTH_010`, `INV_XMOD_001`–`INV_XMOD_010`
- Related: [good-receive-note/02-business-rules](/th/inventory/good-receive-note/02-business-rules) — extra-cost allocation rules
- Related: [product](/th/inventory/product)
- Backend rule implementation (เมื่อเพิ่ม): `../carmen-turborepo-backend-v2/apps/`
