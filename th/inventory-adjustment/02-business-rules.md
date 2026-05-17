---
title: การปรับสต๊อก (Inventory Adjustment) — Business Rules
description: การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูลสำหรับการปรับสต๊อก
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory-adjustment, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Business Rules

> **At a Glance**
> **ตระกูลกฎ:** `ADJ_VAL_*` validation &nbsp;·&nbsp; `ADJ_AUTH_*` permission &nbsp;·&nbsp; `ADJ_CALC_*` calc &nbsp;·&nbsp; `ADJ_POST_*` posting &nbsp;·&nbsp; `ADJ_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 96 กฎ
> **กลุ่มผู้ใช้:** ผู้เขียนเทส + developer — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** Section 5.1 (ที่มีอยู่) มีคำเตือนความแตกต่างระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้รวบรวมกฎเชิงปฏิบัติการที่กำกับ **โมดูล inventory-adjustment** — เลเยอร์เอกสารสองตาราง (`tb_stock_in` / `tb_stock_out`) ที่บันทึกการแก้ไขปริมาณและมูลค่าสต๊อกด้วยมือ กฎด้านล่างอยู่ **เหนือ** กฎระดับ ledger ใน [[inventory/02-business-rules]] — กฎเหล่านี้กำกับวงจรชีวิตเอกสาร (`draft → in_progress → completed → cancelled / voided`), การจำกัด reason-code ตามทิศทาง, การ roll-up totals ระดับเอกสาร (ค่า derived ไม่ใช่คอลัมน์ header ที่ persist), การ route การอนุมัติตาม threshold (Store Keeper → Inventory Controller → Finance) และ hooks ข้ามโมดูลเข้า [[physical-count]] / [[spot-check]] สำหรับ rollup ผลต่าง การเขียน ledger จริง (`tb_inventory_transaction` + `tb_inventory_transaction_detail` + `tb_inventory_transaction_cost_layer`), การเลือกต้นทุน FIFO / weighted-average, guard ห้ามยอดติดลบ และการตรวจสอบ period-containment จุดชนวน **ที่ฝั่ง inventory ตอน post** และบันทึกภายใต้ `INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` / `INV_AUTH_*` ใน [[inventory]] — หน้านี้อ้างอิงมากกว่าจะทำซ้ำ

บันทึกเชิงโครงสร้างสองข้อจาก [[inventory-adjustment/01-data-model]] ทาสีกฎทุกข้อด้านล่าง: **ข้อแรก** ไม่มีโมเดล `tb_inventory_adjustment` เดี่ยว — ทุกกฎที่อ้างถึง "เอกสาร adjustment" ใช้ทั้ง `tb_stock_in` และ `tb_stock_out` แบบสมมาตร เว้นแต่ระบุทิศทาง และ `enum_adjustment_type` บน `tb_adjustment_type` จำกัดว่าต้นเอกสารใดที่ reason ใช้ได้ **ข้อสอง** แคตตาล็อก rule ID ที่ carmen/docs ใช้ (ADJ_CRT_*, ADJ_VAL_*, ADJ_PRC_*, ADJ_UI_*, ADJ_CALC_*) เป็นที่มาของ `ADJ_*` ID ในหน้านี้ แต่กฎหลายข้อถูก realign ไปสู่ความจริง Prisma: วงจรชีวิตสามสถานะของ carmen/docs (`Draft → Posted → Void`) map ไปยังวงจรชีวิตห้าสถานะ Prisma (`draft → in_progress → completed → cancelled / voided`); การตรวจสอบ "ต้นทุนรวมต้องตรงกับ header sum" (ADJ_VAL_005) เป็น degenerate เพราะไม่มีคอลัมน์ header total; การตรวจสอบ "department บังคับ" (ADJ_CRT_009) บังคับใช้ผ่าน JSON `dimension` ไม่ใช่คอลัมน์

## 2. กฎ Validation

Rule IDs ตามรูปแบบ `ADJ_VAL_NNN` Validation รันที่สองขอบเขต: **ตอนสร้าง / แก้ไข draft** (การตรวจสอบโครงสร้างระดับ form ที่ยังไม่กระทบ ledger) และ **ตอน submit** (`draft → in_progress` ถ้ามี workflow stage หรือ `draft → completed` ถ้า auto-approve ต่ำกว่า threshold) — การตรวจสอบตอน submit เป็นที่ที่กฎฝั่ง inventory `INV_VAL_*` จาก [[inventory/02-business-rules]] จุดชนวนเป็นหน่วย transactional

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `ADJ_VAL_001` | เลขที่เอกสาร `si_no` (stock-in) / `so_no` (stock-out) unique ภายใน `deleted_at` เอกสารใหม่ auto-generate `SI-YYMM-NNNNN` / `SO-YYMM-NNNNN` จาก tenant numbering service; เลขที่ผู้ใช้แก้ไขถูก reject เมื่อชนกัน Carmen-docs ADJ_CRT_001 | Save / submit | Reject ด้วย `"Stock-in/-out number <si_no/so_no> already exists for this tenant."` Auto-numbering retry สูงสุด 3 ครั้งใน race ที่หายาก; การแก้ไขด้วยมือตกลงสู่ผู้ใช้ |
| `ADJ_VAL_002` | `tb_stock_in.adjustment_type_id` (หรือ `tb_stock_out.adjustment_type_id`) ไม่เป็น null, ชี้ไปยังแถว `tb_adjustment_type` ที่ active (`is_active = true`, `deleted_at IS NULL`) และ `type` ของ reason ตรงกับทิศทางเอกสาร (`STOCK_IN` สำหรับ `tb_stock_in`, `STOCK_OUT` สำหรับ `tb_stock_out`) Carmen-docs ADJ_CRT_004 + ADJ_VAL_006 | Save / submit | Reject ด้วย `"Adjustment reason is required and must match the document direction (STOCK_IN reasons cannot be used on stock-out documents and vice versa)."` Picker กรองตามทิศทางที่ UI layer แต่กฎถูก re-check ฝั่ง server |
| `ADJ_VAL_003` | `location_id` ไม่เป็น null, อ้างอิง location ประเภท inventory- หรือ consignment- ที่ active (`enum_location_type ∈ {inventory, consignment}`, `is_active = true`, `deleted_at IS NULL`) Direct-cost locations ถูก reject ตาม [[inventory]] `INV_VAL_009` (direct location ไม่ถือยอด) Carmen-docs ADJ_CRT_003 + ADJ_VAL_008 | Save / submit | Reject ด้วย `"Location is required and must be an inventory- or consignment-type location."` สำหรับ null; `"Direct-cost locations cannot be the target of an adjustment — direct locations bypass inventory."` สำหรับประเภท direct |
| `ADJ_VAL_004` | `description` ไม่ว่างบน header (ใช้สำหรับบริบท audit) Carmen-docs ADJ_CRT_005 | Save / submit | Reject ด้วย `"Description is required for audit purposes."` Soft-fail ตอน save (warning); hard-fail ตอน submit |
| `ADJ_VAL_005` | แผนก / cost-centre populate ใน JSON `dimension` (รูปทรงทั่วไป `[{type: "department", id: "<uuid>", code: "<code>"}, ...]`) Carmen-docs ADJ_CRT_009 | Save / submit | Reject ตอน submit ด้วย `"Department / cost-centre is required (set via dimension)."` Soft-fail ตอน save (warning) Tenant config อาจผ่อนสำหรับ reason code เฉพาะ |
| `ADJ_VAL_006` | ทุกบรรทัด detail มี `product_id` ไม่เป็น null ที่อ้างอิง `tb_product` ที่ active (`is_active = true`, `deleted_at IS NULL`) และสินค้าถูกเปิดใช้งานที่ location ที่เลือก (แถว `tb_product_location` มีอยู่, `deleted_at IS NULL`) Carmen-docs ADJ_CRT_006 + ADJ_VAL_009 | Save / submit | Reject ด้วย `"Product <product_code> is not active or not enabled at location <location_code>."` Atomic rejection ของทั้งเอกสาร |
| `ADJ_VAL_007` | ทุกบรรทัด detail มี `qty > 0` (เครื่องหมายเป็น direction-implicit — เอกสารทั้งสองเก็บ `qty` บวกใน detail; inventory-side detail negate สำหรับ stock-out ตาม [[inventory]] `INV_VAL_004`) Carmen-docs ADJ_VAL_002 | Save / submit | Reject ด้วย `"Quantity must be greater than zero on every line."` Zero หรือ negative `qty` ถูก reject |
| `ADJ_VAL_008` | ทุกบรรทัด detail มี `cost_per_unit ≥ 0` บน stock-in (zero อนุญาตสำหรับ FOC / vendor-replacement; ไม่ลบเด็ดขาด) สำหรับ stock-out `cost_per_unit` ที่ผู้ใช้กรอกเป็น preview — ต้นทุนที่มีอำนาจเลือกตอน post โดย costing engine ตาม [[inventory]] `INV_CALC_005` / `INV_CALC_006` ดังนั้นค่าที่ผู้ใช้กรอกเป็น informational Carmen-docs ADJ_VAL_003 + ADJ_VAL_007 | Save / submit | Reject ด้วย `"Cost per unit must be non-negative."` |
| `ADJ_VAL_009` | สำหรับสินค้าที่ติดตาม lot: lot identity well-formed บน `info.lotNo` ของบรรทัด (lot ที่มีอยู่ต้องอยู่ที่ `(location_id, product_id)` สำหรับ stock-out และ stock-in ไป lot ที่มีอยู่; new-lot `lot_no` ต้อง unique ภายใน `(product_id, location_id)` สำหรับ stock-in new-lot) สินค้าที่เน่าเสียง่ายต้องการ `info.expiryDate` บนบรรทัด new-lot Carmen-docs ADJ_CRT_007 + ADJ_VAL_004 | Save / submit | Reject ด้วย `"Lot <lot_no> at location <location> is not available for consumption."` สำหรับ stock-out lot ที่ขาด; `"Lot <lot_no> already exists for product <product> at location <location>; lot identity must be unique."` สำหรับ stock-in new-lot ที่ชนกัน; `"Expiry date is required for perishable product <product> on new lot <lot_no>."` สำหรับ expiry ที่ขาด |
| `ADJ_VAL_010` | เมื่อ `info.requiresDocument = true` ของ adjustment-type (เช่น theft write-off, recall write-off ขนาดใหญ่, breakage ขนาดใหญ่) ต้องมีแถว comment อย่างน้อยหนึ่งแถว (`tb_stock_in_comment` / `tb_stock_out_comment`) ที่ JSON `attachments` ไม่ว่าง Carmen-docs ADJ_CRT_008 | Submit | Reject ด้วย `"Supporting document attachment is required for this adjustment reason."` การตรวจสอบฝั่ง form upload ผ่าน drag-drop; server re-check ตอน submit |
| `ADJ_VAL_011` | วันที่เอกสาร (`si_date` / `so_date` หรือ `created_at` เป็น fallback) อยู่ภายใน `tb_period` ที่ `open` งวด closed และ locked reject ตาม [[inventory]] `INV_VAL_008` Carmen-docs ADJ_CRT_010 + ADJ_PRC_009 | Submit | Reject ด้วย `"Cannot post into period <YYMM>: period is <closed/locked>. Re-open the period (closed only) or post a current-period restatement (locked)."` |
| `ADJ_VAL_012` | ปริมาณขาออก (`tb_stock_out`) ที่ `(location, product, lot)` ไม่ขับ on-hand ติดลบ — ตรวจสอบกับ cost-layer ledger แบบ live ตอน submit ตาม [[inventory]] `INV_VAL_005` เอกสาร adjustment เองไม่เก็บยอดคงเหลือที่มี; การตรวจสอบอ่าน ledger Carmen-docs ADJ_VAL_001 + ADJ_VAL_004 + ADJ_PRC_010 | Submit | Reject ด้วย `"Outbound movement would drive on-hand at (location, product, lot) below zero. Available: <X>, requested: <Y>."` เอกสารยังคงอยู่ที่ `draft`; ผู้ใช้ลด qty, เลือก lot อื่น, หรือ escalate |
| `ADJ_VAL_013` | การแก้ไขเอกสาร `completed` ถูก reject — เอกสาร immutable เมื่อ post แล้ว การแก้ไข route ผ่านรูปแบบ void + new-document compensating ตาม `ADJ_POST_004` Carmen-docs ADJ_PRC_007 + ADJ_PRC_008 | Edit | Reject ด้วย `"Cannot edit a completed adjustment. Void and create a new compensating adjustment."` |
| `ADJ_VAL_014` | Soft-delete ของ adjustment ที่ post แล้วต้องการการ reverse ชดเชยก่อนตาม [[inventory]] `INV_VAL_013` Soft-delete โดยตรงโดยไม่มี inventory transaction ชดเชยถูก reject | Soft-delete | Reject ด้วย `"Cannot soft-delete a posted adjustment without a compensating reversal."` |

## 3. กฎการคำนวณ

ฟิลด์เงินทั้งหมดเก็บเป็น `Decimal(20, 5)` บน `tb_stock_in_detail.total_cost` / `tb_stock_out_detail.total_cost` และฟิลด์ cost-layer คู่ขนาน การปัดเศษการแสดงตาม tenant policy (โดยทั่วไป 2dp สำหรับสกุลเงิน, 3dp สำหรับปริมาณ) **Header เอกสารไม่ถือคอลัมน์ total-cost** — totals เป็น derived ตอนอ่าน Rule IDs ตามรูปแบบ `ADJ_CALC_NNN`

| Rule ID | สูตร |
| ------- | ---- |
| `ADJ_CALC_001` (line total_cost) | `total_cost = qty × cost_per_unit` บนแต่ละแถว `tb_stock_in_detail` / `tb_stock_out_detail` เก็บที่ 5dp; แสดงที่ 2dp Carmen-docs ADJ_CALC_001 |
| `ADJ_CALC_002` (document inQty roll-up) | `header.inQty = Σ detail.qty` over ทุกแถว `tb_stock_in_detail` สำหรับ parent `tb_stock_in.id` scoped ไปยังแถว non-soft-deleted Derived ตอนอ่าน; ไม่มีคอลัมน์ที่ persist Carmen-docs ADJ_CALC_002 |
| `ADJ_CALC_003` (document outQty roll-up) | `header.outQty = Σ detail.qty` over ทุกแถว `tb_stock_out_detail` สำหรับ parent `tb_stock_out.id` Derived ตอนอ่าน Carmen-docs ADJ_CALC_003 |
| `ADJ_CALC_004` (document totalCost roll-up) | `header.totalCost = Σ detail.total_cost` ข้ามแถว detail ของเอกสาร Derived ตอนอ่าน การตรวจสอบ carmen-docs ADJ_VAL_005 "total cost must match" เป็น degenerate เทียบกับ derivation นี้ — ไม่มีค่า header ที่จะ mismatch |
| `ADJ_CALC_005` (Weighted-average refresh on inbound adjustment) | เมื่อ post `tb_stock_in` ไปยังสินค้า WA: `new_average = (prior_on_hand × prior_average + adj_qty × adj_cost) / (prior_on_hand + adj_qty)` เขียนลงบนแถว cost-layer ขาเข้าใหม่ตาม [[inventory]] `INV_CALC_007` Carmen-docs ADJ_CALC_005 |
| `ADJ_CALC_006` (FIFO outbound cost pick) | เมื่อ post `tb_stock_out` สำหรับสินค้า FIFO: iterate `tb_inventory_transaction_cost_layer` ที่ `(location_id, product_id)` เรียงตาม `lot_seq_no` ascending จนกว่า `out_qty` จะ satisfy แต่ละ layer ที่บริโภคสร้างแถว cost-layer ขาออกของตัวเอง; หนึ่งบรรทัด detail สามารถ span หลายแถว cost-layer ตาม [[inventory]] `INV_CALC_005` |
| `ADJ_CALC_007` (Weighted-average outbound cost pick) | เมื่อ post `tb_stock_out` สำหรับสินค้า WA: `cost_per_unit = current_average_cost(location, product)` ตอน post Average ปัจจุบันคือ `average_cost_per_unit` ล่าสุดที่ `(location_id, product_id)` บน `tb_inventory_transaction_cost_layer` ตาม [[inventory]] `INV_CALC_006` |
| `ADJ_CALC_008` (Variance %) | เมื่อแหล่งของ adjustment เป็นการนับ physical / spot: `variance_% = ((physical_count − system_qty) / system_qty) × 100` ใช้โดย count-rollup engine เพื่อ flag ผลต่างขนาดใหญ่สำหรับการสืบสวนของ Inventory Controller Carmen-docs ADJ_CALC_006 |
| `ADJ_CALC_009` (Cost variance) | เมื่อ reason ของ adjustment capture การเปลี่ยนต้นทุนต่อบรรทัด (หายาก — โดยทั่วไปใช้สำหรับ adjustments การจัดประเภทใหม่): `cost_variance = (new_cost − old_cost) × qty` Carmen-docs ADJ_CALC_007 |
| `ADJ_CALC_010` (Period impact) | `period_impact = Σ adjustment_qty × cost_per_unit` over ทุกแถว `tb_stock_in` / `tb_stock_out` ที่ `completed` ในงวด scoped ไป location / reason-code / department สำหรับการรายงาน Read-model เท่านั้น; ไม่ persist Carmen-docs ADJ_CALC_009 |
| `ADJ_CALC_011` (Rounding) | Half-up ค่าที่เก็บใช้ความแม่นยำของคอลัมน์ (`Decimal(20, 5)`); การคำนวณกลางคันถือ 5dp; การ aggregate on-the-fly re-read ค่าที่ปัดเศษแล้วจากแต่ละ step สะท้อน [[inventory]] `INV_CALC_012` |

### 3.1 ตัวอย่างที่ทำงาน (stock-out write-off, FIFO product, ฿ THB)

สินค้า FIFO `P-1` ที่ `LOC-A` พร้อมสอง lot ที่มีอยู่ในลำดับ cost-layer:
- `LOT-1` — เหลือ 5 หน่วยที่ `฿10.00` (`lot_seq_no = 1`)
- `LOT-2` — เหลือ 3 หน่วยที่ `฿12.00` (`lot_seq_no = 2`)

Store Keeper สร้าง `tb_stock_out` ด้วยเหตุผล `BREAKAGE` (`type = STOCK_OUT`), หนึ่งบรรทัด: `product_id = P-1`, `qty = 6` เมื่อ submit, post จุดชนวน:

- Inventory-side: `tb_inventory_transaction` (`inventory_doc_type = stock_out`, `inventory_doc_no = tb_stock_out.id`); หนึ่ง `tb_inventory_transaction_detail` ที่ `qty = -6`, `total_cost = -฿60 + -฿12 = -฿72.00`, `from_lot_no` set (split — ดูด้านล่าง)
- Cost-layer (ตาม `ADJ_CALC_006` / `INV_CALC_005`): สองแถวขาออกเพราะการบริโภค span lots
  - Row 1: `out_qty = 5`, `cost_per_unit = ฿10.00`, `total_cost = ฿50.00`, `lot_no = LOT-1`, `transaction_type = adjustment_out` `LOT-1` เหลือ = 0
  - Row 2: `out_qty = 1`, `cost_per_unit = ฿12.00`, `total_cost = ฿12.00`, `lot_no = LOT-2`, `transaction_type = adjustment_out` `LOT-2` เหลือ = 2
- Document side: `tb_stock_out_detail.total_cost = ฿62.00` (roll-up ของ cost-layer total ที่ application-layer เขียนตอน post สำหรับการรายงาน); `tb_stock_out_detail.cost_per_unit` เป็น informational (ค่าเฉลี่ยถ่วงน้ำหนัก FIFO `62 / 6 = ฿10.33333`)
- GL entry: `Dr <BREAKAGE expense GL account from tb_adjustment_type.info.glAccount> ฿62.00 / Cr Inventory ฿62.00`

### 3.2 ตัวอย่างที่ทำงาน (stock-in สำหรับ found stock, weighted-average product)

สินค้า WA `P-2` ที่ `LOC-A` พร้อม on-hand ปัจจุบัน 100 ที่ average `฿11.33333` (จากการรับก่อนหน้า) Store Keeper พบส่วนเกิน 10 หน่วยของ lot ที่มีอยู่ระหว่างการตรวจสอบ bin, สร้าง `tb_stock_in` ด้วยเหตุผล `FOUND_STOCK` (`type = STOCK_IN`), หนึ่งบรรทัด: `product_id = P-2`, `qty = 10`, `lot_no = LOT-X` (มีอยู่), `cost_per_unit = ฿11.33333` (auto-fill จาก cost-layer ล่าสุดของ lot)

เมื่อ submit (ต่ำกว่า threshold, auto-approve):
- Inventory-side: `tb_inventory_transaction` (`inventory_doc_type = stock_in`); `tb_inventory_transaction_detail` ที่ `qty = 10`, `cost_per_unit = ฿11.33333`, `total_cost = ฿113.33`, `current_lot_no = LOT-X`
- Cost-layer (ตาม `ADJ_CALC_005` / `INV_CALC_007`): หนึ่งแถวขาเข้า `in_qty = 10`, `cost_per_unit = ฿11.33333`, `transaction_type = adjustment_in`, `lot_no = LOT-X` Average ใหม่: `(100 × 11.33333 + 10 × 11.33333) / (100 + 10) = ฿11.33333` (ไม่เปลี่ยนเพราะต้นทุน found-stock ตรงกับ average ที่มีอยู่) Average ใหม่เขียนลงบนแถว layer ใหม่
- On-hand ที่ `(LOC-A, P-2, LOT-X)` advance 10 ตาม [[inventory]] `INV_CALC_004`
- GL: `Dr Inventory ฿113.33 / Cr <FOUND_STOCK gain / recovery GL account> ฿113.33`

ถ้าของพบใหม่ประกาศที่ต้นทุนต่างกัน (เช่น `฿12.00`) การ refresh WA จะคำนวณ `(100 × 11.33333 + 10 × 12.00) / 110 = ฿11.39394` — และความต่างของต้นทุนจะแสดงการตีมูลค่าต้นทุนใหม่ที่ capture บน `average_cost_per_unit` ของ layer ใหม่

## 4. กฎ Authorization

Rule IDs ตามรูปแบบ `ADJ_AUTH_NNN` Authorization ซ้อน RBAC (role check) บน scope ของ `tb_user_location` (location whitelist ต่อผู้ใช้) บวก **threshold ladder** ที่ตั้งค่าโดย tenant ที่ route เอกสารผลกระทบต้นทุนขนาดใหญ่ขึ้นไป Thresholds ตั้งค่าได้โดย tenant; defaults ในตารางด้านล่างสะท้อนการตั้งค่า hotel-chain ทั่วไป

| Rule ID | Subject | Right | ข้อจำกัด |
| ------- | ------- | ----- | -------- |
| `ADJ_AUTH_001` | Store Keeper | สร้างเอกสาร `tb_stock_in` / `tb_stock_out` ที่ `draft` | ภายใน scope `tb_user_location` สำหรับ `location_id` ของเอกสาร อ่าน / list scope filter ไปยัง locations ของผู้ใช้ |
| `ADJ_AUTH_002` | Store Keeper | Submit (`draft → in_progress` หรือ `draft → completed`) ต่ำกว่า threshold auto-approve | Threshold auto-approve โดยทั่วไป `฿500` aggregate ต้นทุนเอกสาร ต่ำกว่า threshold: เอกสาร auto-advance ไป `completed`, inventory transaction post ทันที ที่หรือเหนือ threshold: route ไป queue ของ Inventory Controller การจำกัด SoD ตาม `ADJ_AUTH_010` สะท้อน [[inventory]] `INV_AUTH_001` / `INV_AUTH_002` |
| `ADJ_AUTH_003` | Store Keeper | Submit stock-in สร้าง **lot ใหม่** | **route สำหรับ Controller approval เสมอ** ไม่ว่าผลกระทบต้นทุน เพราะการสร้าง lot ใหม่โดย Store Keeper เป็นเหตุการณ์อ่อนไหว (สามารถซ่อนการ manipulate ต้นทุน) กฎ below-threshold ไม่ใช้ |
| `ADJ_AUTH_004` | Inventory Controller | Approve / post เอกสาร above-Store-Keeper-threshold | Inventory Controller จุดชนวนการเปลี่ยน `in_progress → completed` สำหรับเอกสาร above-auto-approve ภายใน scope ของพวกเขา เหนือ Controller threshold (โดยทั่วไป `฿10,000` aggregate cost) เอกสาร route ต่อไปยัง Finance ตาม `ADJ_AUTH_005` สะท้อน [[inventory]] `INV_AUTH_003` |
| `ADJ_AUTH_005` | Finance | Approve เอกสาร above-Controller-threshold | Recall write-offs ขนาดใหญ่, damage write-offs ขนาดใหญ่, theft write-offs ขนาดใหญ่ route Controller → Finance Finance จุดชนวนการอนุมัติสุดท้าย `in_progress → completed` Preview ผลกระทบต้นทุนแสดงพร้อม reason-code และการ map GL-account สะท้อน [[inventory]] `INV_AUTH_005` |
| `ADJ_AUTH_006` | Department Manager | Review ของ adjustments scope แผนก | Read-only role variant สำหรับการกำกับดูแลแผนก — ไม่อนุมัติ แต่ได้รับการแจ้งเตือนบนเอกสารที่กระทบ cost-centre ของพวกเขา (resolve ผ่าน entry `department` ใน JSON `dimension`) อาจเพิ่ม comments / flag เพื่อสืบสวนของ Controller / Finance |
| `ADJ_AUTH_007` | Inventory Controller | ยกเลิกเอกสาร `draft` หรือ `in_progress`; void เอกสาร `completed` | การยกเลิกก่อน post ไม่มีผลกระทบ inventory — `doc_status` เคลื่อนไปยัง `cancelled` และเป็นปลายทาง Void หลังจาก `completed` ต้องการ inventory transaction reverse ชดเชยตาม `ADJ_POST_004`; `doc_status` เคลื่อนไปยัง `voided` หลัง transaction ชดเชย post |
| `ADJ_AUTH_008` | System Administrator | กำหนดค่า `tb_adjustment_type` reason codes (CRUD), set GL-account mapping ใน `info.glAccount`, set flags `requiresDocument` / `requiresQualityCheck`, set tenant thresholds สำหรับ auto-approve / Controller / Finance | Role config-only เท่านั้น; ไม่สามารถสร้างหรืออนุมัติ adjustments การเปลี่ยนแปลงใช้แบบ prospective; เอกสารประวัติคง snapshot ของ reason-code ตาม [[inventory-adjustment/01-data-model]] § 3 notes สะท้อน [[inventory]] `INV_AUTH_008` |
| `ADJ_AUTH_009` | Auditor | Read-only ข้าม `tb_stock_in` / `tb_stock_out` ทั้งหมด, แถว detail ของพวกเขา, comments, attachments และแถว `tb_inventory_transaction` ที่เกิดขึ้น | Full read scope รวม soft-deleted (`deleted_at` non-null) และเอกสาร voided การ trace lot-recall รวม adjustment documents กับ [[good-receive-note]] และ [[store-requisition]] data ผ่าน `tb_inventory_transaction` join ร่วม Export ฟิลด์อ่อนไหว (cost-per-unit, vendor terms ผ่านเอกสารต้นทางที่ join) ต้องการการอนุมัติรองตาม audit-pattern สะท้อน [[inventory]] `INV_AUTH_009` |
| `ADJ_AUTH_010` | Segregation of duties — Receiver / Adjuster | ผู้ใช้ที่ submit `tb_stock_out` write-off ต้องไม่เป็นผู้ใช้คนเดียวกับที่สร้างการรับต้นทาง (`tb_good_received_note.created_by_id`) สำหรับ lot ที่ถูก write off เมื่อผลกระทบต้นทุนเกิน SoD threshold การ write-off ขาดจากนับตามปกติต่ำกว่า threshold ได้รับการยกเว้น สะท้อน [[inventory]] `INV_AUTH_010` | บังคับใช้ตอน submit Server return `"You created the receipt for this lot; an independent adjuster must initiate the write-off (SoD)."` |

## 5. กฎ Posting

เอกสาร adjustment มีวงจรชีวิตห้าสถานะ Prisma `draft → in_progress → completed → cancelled / voided` (ตาม `enum_doc_status`) ผลกระทบ fan-out ด้านล่างจุดชนวนที่การเปลี่ยน `in_progress → completed` Rule IDs ตามรูปแบบ `ADJ_POST_NNN`

| Rule ID | การเปลี่ยน / เหตุการณ์ | ผลกระทบ |
| ------- | ------------------ | ------- |
| `ADJ_POST_001` | `draft → in_progress` (submit) | Validation `ADJ_VAL_001`–`ADJ_VAL_011` รัน ถ้า auto-approve (ต่ำกว่า threshold และไม่ใช่ new-lot) การเปลี่ยน cascade ไปยัง `completed` และ `ADJ_POST_002` จุดชนวนทันที ถ้าเหนือ threshold หรือ new-lot เอกสารยังคงอยู่ที่ `in_progress` รอ Controller / Finance approval `workflow_history` ต่อด้วย `{stage: 'submitted', by: <actor>, at: <now>}`; `last_action = submitted` |
| `ADJ_POST_002` | `in_progress → completed` (auto หรือผ่าน approval) | **Posting จุดชนวน** สำหรับแต่ละบรรทัด detail เขียนไปยัง inventory ledger: (1) หนึ่งแถว `tb_inventory_transaction` ด้วย `inventory_doc_type = stock_in` / `stock_out`, `inventory_doc_no = tb_stock_in.id` / `tb_stock_out.id`; (2) หนึ่งแถว `tb_inventory_transaction_detail` (`qty` มีเครื่องหมายตามทิศทางตาม [[inventory]] `INV_VAL_004`; `cost_per_unit` จากเอกสารสำหรับ stock-in, เลือกตอน post สำหรับ stock-out; `total_cost`; `from_lot_no` / `current_lot_no` resolve ตามทิศทาง); (3) หนึ่งหรือมากกว่าแถว `tb_inventory_transaction_cost_layer` ขึ้นกับ costing method (หนึ่งแถวขาเข้าสำหรับ stock-in; FIFO multi-row หรือ WA single row สำหรับ stock-out ตาม `ADJ_CALC_005` / `ADJ_CALC_006` / `ADJ_CALC_007`); (4) GL entry — `Dr/Cr` ตาม `info.glAccount` ของ adjustment-type และ `dimension.department` ของเอกสาร `inventory_transaction_id` ของแถว detail ประทับด้วย id ของ transaction ใหม่ `workflow_history` ต่อด้วย `{stage: 'completed', by: <actor>, at: <now>}` สะท้อน [[inventory]] `INV_POST_001` (stock-in) และ `INV_POST_002` (stock-out) |
| `ADJ_POST_003` | `draft / in_progress → cancelled` (ละทิ้งก่อน post) | เอกสาร `doc_status = cancelled` ไม่มีผลกระทบ inventory; ไม่ต้องการ transaction ชดเชย ข้อความเหตุผลต้องการบน action cancel; บันทึกใน `workflow_history` เอกสารคงอยู่ใน database (soft-delete optional ตาม tenant policy) สำหรับ audit |
| `ADJ_POST_004` | `completed → voided` (void หลังการกระทำ) | **สองขั้น** ก่อน, compensating `tb_stock_in` (ถ้า void stock-out) หรือ `tb_stock_out` (ถ้า void stock-in) ถูกสร้างพร้อมบรรทัดเดียวกันและ `info.voidsAdjustmentId = <original_id>`; submit และ post ตาม `ADJ_POST_002` เขียน `tb_inventory_transaction` reverse เฉพาะหลังการ post ชดเชยสำเร็จ `doc_status` ของเอกสารต้นฉบับเคลื่อนไปยัง `voided` Inventory transaction ต้นฉบับ **ไม่** ถูกแก้ไขตาม [[inventory]] `INV_POST_012` `workflow_history` บันทึก action ทั้งสอง |
| `ADJ_POST_005` | Period-rollover guard | ถ้า `si_date` / `so_date` ของเอกสารตกในงวด `closed` / `locked` `tb_period` ตอน submit `ADJ_VAL_011` reject ตาม [[inventory]] `INV_VAL_008` การ re-open งวด closed เพื่ออนุญาตการ back-post เป็นสิทธิ Finance Manager ตาม [[inventory]] `INV_AUTH_006` |
| `ADJ_POST_006` | Count-rollup auto-post | เมื่อ [[physical-count]] / [[spot-check]] ยืนยันบรรทัดผลต่างและ Inventory Controller commit count ระบบ auto-create หนึ่ง `tb_stock_in` (overage rollup) และ/หรือหนึ่ง `tb_stock_out` (shortage rollup) ด้วย `info.countId = <count_uuid>`, auto-advance ไป `completed` ภายใต้อำนาจ Controller (ข้าม queue ของ Store Keeper) และเขียน inventory transaction ตาม `ADJ_POST_002` ตาม [[inventory]] `INV_XMOD_003` / `INV_XMOD_004` |
| `ADJ_POST_007` | Direct-cost location gate | Posting ไปยัง direct-cost location ถูก **reject ตอน submit** ตาม `ADJ_VAL_003` และ [[inventory]] `INV_VAL_009` หน้าจอกรอง picker location ไปยังประเภท inventory- / consignment-; การ submit ผ่าน API โดยตรงด้วย direct-cost `location_id` return validation error |
| `ADJ_POST_008` | Consignment location handling | Posting `tb_stock_in` ไปยัง consignment location เขียน `tb_inventory_transaction` ด้วยแถว cost-layer ที่ flag เป็น consignment (ตาม `dimension` / `info`) และ **ไม่** debit Inventory หรือ credit AP — memo-only ตาม [[inventory]] `INV_POST_004` Posting `tb_stock_out` จาก consignment post COGS + AP พร้อมกันตาม [[inventory]] `INV_POST_005` การโอนกรรมสิทธิ์ consignment-to-inventory ต้องการเอกสาร stock-in การจัดประเภทใหม่ที่ระบุชัดเจนตาม [[inventory]] `INV_VAL_010` |
| `ADJ_POST_009` | Soft-delete sequencing | Soft-delete บน `completed` `tb_stock_in` / `tb_stock_out` อนุญาตเฉพาะหลังการ reverse ชดเชย post ตาม `ADJ_VAL_014` และ [[inventory]] `INV_VAL_013` Soft-delete โดยตรงข้าม flow void ถูก reject |
| `ADJ_POST_010` | UI status colour coding | ตาม carmen-docs ADJ_UI_002: `draft` amber; `in_progress` blue; `completed` green; `cancelled` grey; `voided` red Status badge render บน list และ detail views ตามความจริง `enum_doc_status` ของ [[inventory-adjustment/01-data-model]] § 2 |

แผนภาพสถานะ (ตาม Prisma `enum_doc_status`):

```
[*] → draft ──submit──> in_progress ──approve──> completed (terminal active)
        │                  │                          │
        │                  │                          └──void (compensating)──> voided (terminal)
        │                  │
        └──cancel──> cancelled (terminal)
                           │
                           └──cancel──> cancelled (terminal)
```

### 5.1 วงจรชีวิตสถานะ — การ map ระหว่าง Live UI กับ BRD

Enum Prisma `enum_doc_status` ที่บรรยายด้านบนคือสิ่งที่ Live UI ใช้ ชุด carmen/docs (`INV-ADJ-Business-Requirements.md`) บรรยายชุดสถานะที่ตั้งใจเป็นวงจรชีวิตสามสถานะ (`Draft → Posted → Void`) ตารางด้านล่าง map ทุกสถานะที่ตรวจสอบได้ใน live-UI ไปยังเทียบเท่า BRD เพื่อให้ผู้เทสและ developer สามารถ reconcile ทั้งสองได้โดยไม่กำกวม แหล่ง: `Test_case/System_Process/tx-06-stock-in-adj.md` (วันที่จับ 2026-04-27) และ `Test_case/System_Process/tx-07-stock-out-adj.md` (วันที่จับ 2026-04-27)

> Diff legend: ✅ match · 🟡 renamed · 🔴 new in live UI · 🔵 BRD only

| Live UI status | BRD equivalent | Diff | Notes |
|---|---|---|---|
| `draft` | `Draft` | ✅ match | สถานะเริ่มต้นที่แก้ไขได้ เอกสารทั้ง stock-in และ stock-out เริ่มที่นี่; ผู้สร้างกรอกบรรทัด, reason code, แผนก, attachments ไม่มีผลกระทบ inventory |
| `in_progress` | — (collapsed into `Draft` in BRD three-state model) | 🔴 new in live UI | Submit เพื่ออนุมัติ; เอกสารถูก lock ให้ผู้สร้างขณะรอ Controller หรือ Finance review เอกสารทั้ง stock-in และ stock-out variants ใช้สถานะนี้สำหรับ gate การ route above-threshold หรือ new-lot โมเดลสามสถานะของ BRD ไม่มีเทียบเท่า — ยุบเข้ากับ `Draft` |
| `completed` | `Posted` | 🟡 renamed | สถานะ active ปลายทาง; การเปลี่ยน `in_progress → completed` จุดชนวนเหตุการณ์ posting: inventory transaction เขียน, cost-layer rows สร้าง (lot ใหม่สำหรับ stock-in; การบริโภค lot เก่าก่อนสำหรับ stock-out), GL entry สร้าง Immutable หลังการ post ใช้กับทั้ง stock-in (ทิศทาง IN) และ stock-out (ทิศทาง OUT) |
| `cancelled` | — (no BRD equivalent) | 🔴 new in live UI | เอกสารยกเลิกก่อนการ post — ผู้สร้างหรือผู้ตรวจสอบละทิ้ง ไม่มีผลกระทบ inventory ปลายทาง โมเดลสามสถานะ BRD ไม่มีการยกเลิกก่อน post ที่ระบุชัดเจน; เอกสารใน BRD จะ advance ไปยัง `Posted` หรือเป็น `Void` |
| `voided` | `Void` | 🟡 renamed | Void หลังการกระทำผ่านรูปแบบ compensating reversal (`ADJ_POST_004`) เอกสาร `completed` ต้นฉบับเคลื่อนไปยัง `voided` เฉพาะหลังจาก compensating `tb_stock_in` (ถ้า void stock-out) หรือ `tb_stock_out` (ถ้า void stock-in) ได้ post Inventory transaction ต้นฉบับไม่ถูกแก้ไขตาม [[inventory]] `INV_POST_012` ใช้กับทั้งสองทิศทาง |
| — | `Draft` (editable + submitted, pre-post) | 🔵 BRD only | สถานะ `Draft` ของ BRD ครอบคลุมทั้งสถานะ `draft` และ `in_progress` ของ carmen-wiki — BRD ไม่แยก editable pre-submit จาก window submitted-awaiting-approval |

> ⚠️ **ความแตกต่าง — สองต้นเอกสารคู่ขนาน vs เอนทิตี `InventoryAdjustment` เดี่ยว:** BRD ของ carmen/docs (`INV-ADJ-Business-Requirements.md`) และนิยาม interface บรรยายเอนทิตี `InventoryAdjustment` เดี่ยวที่มี discriminator `type: 'IN' | 'OUT'` และวงจรชีวิตสามสถานะ (`Draft → Posted → Void`) การ implement live ใช้ **สองตารางเอกสารคู่ขนาน** — `tb_stock_in` (ทิศทาง IN) และ `tb_stock_out` (ทิศทาง OUT) — แต่ละตารางมี `enum_doc_status` ห้าสถานะเดียวกัน join ด้วยตัวจำแนก reason-code ร่วม `tb_adjustment_type` ซึ่ง `enum_adjustment_type` (`STOCK_IN` / `STOCK_OUT`) gate ว่าต้นเอกสารใดที่ reason ที่กำหนดสามารถปรากฏ มุมมอง single-entity ของ BRD คือ read-model union; การแยกสองตารางคือ persistence layer canonical แหล่ง: `Test_case/System_Process/tx-06-stock-in-adj.md` (วันที่จับ 2026-04-27) และ `Test_case/System_Process/tx-07-stock-out-adj.md` (วันที่จับ 2026-04-27)

> ⚠️ **ความแตกต่าง — Markers TBC ของ status flow ในแหล่ง Test_case:** ทั้ง `Test_case/System_Process/tx-06-stock-in-adj.md` และ `Test_case/System_Process/tx-07-stock-out-adj.md` annotate status flow ด้วย `TBC — verify live UI statuses` วงจรชีวิตห้าสถานะ (`draft → in_progress → completed → cancelled / voided`) ที่บรรยายใน [[inventory-adjustment/01-data-model]] § 4 คือความจริง Prisma schema canonical; markers TBC แสดงว่า phrasing ของ live UI label สำหรับแต่ละสถานะยังไม่ได้รับการ verify กับระบบที่รันอยู่ ผู้เทสควรยืนยันว่าข้อความ badge ที่แสดงตรงกับค่า enum ด้านบน แหล่ง: `Test_case/System_Process/tx-06-stock-in-adj.md` (วันที่จับ 2026-04-27) และ `Test_case/System_Process/tx-07-stock-out-adj.md` (วันที่จับ 2026-04-27)

> ⚠️ **ความแตกต่าง — ผลกระทบ Lot แตกต่างตามทิศทาง:** Stock-in adjustments (`tb_stock_in`) สร้าง **lot ใหม่** เสมอสำหรับปริมาณ adjusted-in (lot ใหม่สร้างที่ inventory location; หมายเลข lot และ metadata อาจถูกกรอกด้วยมือหรือสร้างโดยระบบ — TBC ตาม `Test_case/System_Process/tx-06-stock-in-adj.md`, วันที่จับ 2026-04-27) Stock-out adjustments (`tb_stock_out`) **บริโภค lot ที่มีอยู่จากเก่าก่อน** (การบริโภค lot FIFO; ถ้าปริมาณ adjustment span หลาย lot แต่ละตัวลดในลำดับเวลาจนกว่าปริมาณ adjustment จะ satisfy — ตาม `Test_case/System_Process/tx-07-stock-out-adj.md`, วันที่จับ 2026-04-27) ความไม่สมมาตรเชิงทิศทางนี้หมายความว่า new-lot stock-in route สำหรับ Inventory Controller approval เสมอตาม `ADJ_AUTH_003` ไม่ว่าต้นทุน ในขณะที่การเลือก lot ของ stock-out เป็น engine-driven (ผู้ใช้ไม่กรอก) ตอน post

> ℹ️ **Note — การกรอก unit cost แตกต่างตามทิศทาง:** สำหรับ stock-in, `cost_per_unit` ผู้ใช้กรอกบนบรรทัดเอกสาร (บังคับ; ใช้สำหรับ cost layer ของ lot ใหม่และการคำนวณ WA/FIFO) สำหรับ stock-out, `cost_per_unit` ที่ผู้ใช้กรอกเป็น preview draft เท่านั้น — ต้นทุนที่มีอำนาจเลือกตอน post โดย costing engine (`ADJ_CALC_006` / `ADJ_CALC_007`) BRD `ADJ_VAL_003` ใช้กับ stock-in; สำหรับ stock-out การ validate ใช้กับค่า preview เท่านั้น แหล่ง: `Test_case/System_Process/tx-06-stock-in-adj.md` (วันที่จับ 2026-04-27) และ `Test_case/System_Process/tx-07-stock-out-adj.md` (วันที่จับ 2026-04-27)

## 6. กฎข้ามโมดูล

Rule IDs ตามรูปแบบ `ADJ_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | --- |
| `ADJ_XMOD_001` | [[inventory]] | ทุก `completed` `tb_stock_in` / `tb_stock_out` เขียนหนึ่งแถว `tb_inventory_transaction` ต่อบรรทัด detail ด้วย `inventory_doc_type = stock_in` / `stock_out` และ `inventory_doc_no = tb_stock_in.id` / `tb_stock_out.id` `inventory_transaction_id` ของ detail ประทับด้วย id ของ transaction ใหม่ (ไม่มี Prisma `@relation`; application-resolve) Cost-layer ledger รับแถว `enum_transaction_type = adjustment_in` / `adjustment_out` ตาม [[inventory]] `INV_XMOD_005` |
| `ADJ_XMOD_002` | [[physical-count]] | การนับ physical ที่เสร็จสมบูรณ์สร้างบรรทัดผลต่างต่อ `(location_id, product_id, lot_no)` เมื่อ Controller commit ระบบ auto-create: (a) หนึ่ง `tb_stock_in` สำหรับบรรทัด overage (ถ้ามี) ด้วยเหตุผล `COUNT_OVERAGE`; (b) หนึ่ง `tb_stock_out` สำหรับบรรทัด shortage (ถ้ามี) ด้วยเหตุผล `COUNT_SHORTAGE` ทั้งสอง auto-advance ไป `completed` ภายใต้อำนาจ Controller เอกสารนับต้นทาง `tb_count_stock.status` เปลี่ยนไปยัง `completed_posted` Cross-reference [[inventory]] `INV_XMOD_003` |
| `ADJ_XMOD_003` | [[spot-check]] | Path posting เดียวกับ physical-count แต่ scope ไปยัง subset ของสินค้า / locations Spot-check variances post ภายใต้รูปแบบ rollup `tb_stock_in` / `tb_stock_out` เดียวกันด้วยเหตุผล `COUNT_OVERAGE` / `COUNT_SHORTAGE` (หรือเหตุผลเฉพาะ spot-check ที่ tenant configure) Cross-reference [[inventory]] `INV_XMOD_004` |
| `ADJ_XMOD_004` | [[good-receive-note]] | Vendor-replacement ของสต๊อกที่เสียหาย (เช่น vendor ส่ง free replacement นอก path credit-note) capture เป็น `tb_stock_in` ด้วยเหตุผล `VENDOR_FREE_REPLACEMENT` GRN ต้นทางไม่ถูกแก้ไข; การ replacement เป็น lot ใหม่บน inventory ledger ในที่ที่ vendor ยอมรับการลดราคาหลังการรับ path credit-note เป็นที่ต้องการ (อยู่ใน flow credit-note ของ [[good-receive-note]] ตาม [[inventory]] `INV_XMOD_007`) ไม่ใช่ adjustment |
| `ADJ_XMOD_005` | [[costing]] | Costing อ่านแถว cost-layer ที่ขับเคลื่อนโดย adjustment สำหรับลำดับการบริโภค FIFO และการ refresh weighted-average: แถว `transaction_type = adjustment_in` สร้าง layers ใหม่ (FIFO) หรือ refresh moving average (WA) ตาม `ADJ_CALC_005`; แถว `transaction_type = adjustment_out` บริโภค FIFO layers หรืออ่าน WA ปัจจุบันตาม `ADJ_CALC_006` / `ADJ_CALC_007` การเปลี่ยนต้นทุนที่ขับเคลื่อนโดย adjustment ป้อน COGS และการตีมูลค่า inventory ในวิธีเดียวกับการเคลื่อนไหว GRN / SR ตาม [[inventory]] `INV_XMOD_006` |
| `ADJ_XMOD_006` | [[product]] | `costing_method` ของสินค้า (FIFO vs WEIGHTED_AVERAGE) กำหนดการเลือกต้นทุนตอน post บน `tb_stock_out` ตาม `ADJ_CALC_006` / `ADJ_CALC_007` การเปลี่ยน costing method ของสินค้าที่มี on-hand ไม่เป็นศูนย์ถูก block ตาม [[inventory]] `INV_XMOD_009` — ข้อจำกัดเดียวกันใช้ไม่ว่า on-hand ถูกสร้างผ่าน GRN, SR transfer-in หรือ adjustment stock-in |
| `ADJ_XMOD_007` | Finance / GL | Journal entries ที่ขับเคลื่อนโดย adjustment กระทบยอดกับ inventory sub-ledger ที่ปิดงวดตาม [[inventory]] `INV_XMOD_008` `info.glAccount` ของ adjustment-type กำหนดบัญชี expense / gain (เช่น `BREAKAGE → 6510 — Breakage & Damage Expense`; `FOUND_STOCK → 4905 — Inventory Recovery`; `EXPIRY_WRITE_OFF → 6520 — Expiry Write-Off`; `THEFT_WRITE_OFF → 6530 — Shrinkage Loss`) ผลกระทบ adjustment สุทธิต่องวด sum ตามเหตุผลสำหรับรายงานผลต่าง |
| `ADJ_XMOD_008` | [[inventory]] (cross-link) | รายการค่า `enum_inventory_doc_type` ที่ valid ที่ adjustment สามารถสร้างคือ `{stock_in, stock_out}` รายการค่า `enum_transaction_type` cost-layer ที่ valid จาก adjustment คือ `{adjustment_in, adjustment_out}` โมดูล adjustment ไม่สร้างประเภท inventory transaction หรือ cost-layer อื่น ๆ (`good_received_note`, `store_requisition`, `transfer_in`, `transfer_out`, `issue`, `credit_note_*`, `eop_*`, `close_period`, `open_period`) |
| `ADJ_XMOD_009` | ทุกโมดูลที่สร้างการเคลื่อนไหว | ทุก adjustment เขียนผ่าน API `tb_inventory_transaction` เดียวกับการ post GRN / SR / count / credit-note ไม่มี ledger bypass เฉพาะ adjustment; `inventory_doc_type` polymorphic เป็นตัวแยกแยะเดียวที่ระดับ ledger นี่คือ chokepoint ที่ทำให้ audit trail ของ adjustment สอดคล้องกับแหล่งการเคลื่อนไหวอื่นตาม [[inventory]] `INV_XMOD_010` |

## 7. แหล่งอ้างอิง

- `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Requirements.md` — ที่มาของแคตตาล็อกกฎ `ADJ_CRT_*`, `ADJ_VAL_*`, `ADJ_PRC_*`, `ADJ_UI_*`, `ADJ_CALC_*` ที่หน้านี้ realign ไปสู่ความจริง Prisma; interfaces `InventoryAdjustment` / `AdjustmentReason` ที่ ground § 5 ของ [[inventory-adjustment/01-data-model]]
- `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Logic.md` — process flows รวมแผนภาพ Mermaid "Adjust Inventory" ใน § 4.4; ตรวจสอบไขว้เข้า flow validation, calculation และ posting ด้านบน (note: `Draft → Posted → Void` สามสถานะของ carmen/docs ถูก realign ไปยังความจริง Prisma ห้าสถานะ)
- `../carmen/docs/inventory-adjustment/INV-ADJ-PRD.md` — UI / functional requirements (status colour-coding, lot selection dialog, FIFO override) อ้างอิงภายใต้ `ADJ_POST_010`
- `../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md` — บทบาทและความรับผิดชอบของโมดูล; cross-reference สำหรับ persona scope ภายใต้ `ADJ_AUTH_*` (note: 6 personas ยุบเป็น 4 groups — Store Keeper, Inventory Controller, Finance, Audit/Config)
- Sibling: [[inventory-adjustment/01-data-model]] — ตาราง Prisma canonical (`tb_stock_in`, `tb_stock_out`, `tb_adjustment_type` ฯลฯ), enums (`enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`) และแคตตาล็อกความแตกต่างที่ Section 1 (structural notes), Section 2 (validation), Section 5 (posting state diagram) พึ่งพา
- Sibling: [[inventory/02-business-rules]] — กฎระดับ ledger canonical (`INV_VAL_005` no-negative-balance, `INV_VAL_008` period gate, `INV_VAL_009` direct-cost gate, `INV_CALC_005` / `INV_CALC_006` cost picks, `INV_CALC_007` WA refresh, `INV_POST_001` / `INV_POST_002` inbound/outbound posting, `INV_AUTH_001`–`INV_AUTH_010` authorization, `INV_XMOD_003` / `INV_XMOD_004` / `INV_XMOD_005` กฎข้ามโมดูล count และ adjustment) ที่หน้านี้อ้างอิงมากกว่าทำซ้ำ
- การ implement กฎ Backend (เมื่อเพิ่ม): `../carmen-turborepo-backend-v2/apps/` — โมดูลบริการ stock-in / stock-out คือ hook implement สำหรับกฎเหล่านี้ (validation, threshold-based routing, transactional post, count-rollup auto-creation, GL-mapping resolution)
- E2E: [`../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — admin reason-code adjustment-type (CRUD, validation, code uniqueness) — exercise `ADJ_AUTH_008` configuration scope
