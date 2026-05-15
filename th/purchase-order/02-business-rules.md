---
title: ใบสั่งซื้อ — กฎทางธุรกิจ
description: กฎ validation, การคำนวณ, การอนุมัติ, การ post, three-way match, และ cross-module สำหรับโมดูล purchase-order
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — กฎทางธุรกิจ

## 1. ภาพรวม

หน้านี้รวบรวมกฎทางธุรกิจที่บังคับใช้กับเอกสารใบสั่งซื้อ (PO) ตลอดวงจรชีวิต ได้แก่ การตรวจสอบความถูกต้องของข้อมูล (validation) ที่ขั้นตอนสร้าง / แก้ไข / submit, การคำนวณยอดเงินทั้งระดับบรรทัดและระดับหัวเอกสาร, การควบคุมสิทธิ์ตามบทบาทและตามเกณฑ์มูลค่า, ผลของการเปลี่ยนสถานะแต่ละ transition ของ `enum_purchase_order_doc_status`, three-way match กับ GRN และใบแจ้งหนี้ของผู้ขาย, และกฎ cross-module ที่เกี่ยวข้องกับ [[purchase-request]], [[good-receive-note]], [[vendor-pricelist]], และ [[inventory]]

กฎด้านล่างนี้สังเคราะห์มาจากเอกสาร business analysis ของ PO ใน carmen/docs, แค็ตตาล็อกกฎฝั่ง PR (Section 3 ของ `purchase-request-ba.md` และ `PR-Module-Structure.md` — เนื่องจาก PO สืบทอดปรัชญาเดียวกันทั้งเรื่องการคำนวณ การปัดเศษ และการอนุมัติ), และแบบจำลองข้อมูล Prisma ที่อ้างอิงใน [[purchase-order/01-data-model]] หากกรณีที่ carmen/docs และ Prisma ไม่ตรงกัน ให้ถือว่า Prisma เป็นแหล่งอ้างอิงหลัก — โดยเฉพาะค่าของสถานะ (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) และการใช้ตารางสะพานเชื่อม PR↔PO แทนการมี FK เดียวบนบรรทัด PO

## 2. กฎ Validation

รหัสกฎใช้รูปแบบ `PO_VAL_NNN` กฎระดับหัวเอกสาร (001–006) จะถูกเรียกใช้ทุกครั้งที่บันทึกและที่ submit, กฎระดับบรรทัด (007–011) จะถูกเรียกใช้ต่อบรรทัดทั้งที่บันทึกและที่ submit, ส่วนกฎระดับรวม (012–016) จะถูกเรียกใช้เฉพาะตอน submit เท่านั้น

| รหัสกฎ | เงื่อนไข | จุดที่บังคับใช้ | ข้อความ / พฤติกรรม |
| ------ | -------- | -------------- | ------------------- |
| `PO_VAL_001` | `tb_purchase_order.po_no` ต้องไม่ว่างและไม่ซ้ำในแถวที่ยังไม่ถูก soft-delete (`@@unique([po_no, deleted_at])`) | สร้าง, แก้ไข, submit | ปฏิเสธด้วยข้อความ "ต้องระบุหมายเลขอ้างอิง PO และต้องไม่ซ้ำ" มี fallback ระดับ DB ผ่าน unique index |
| `PO_VAL_002` | `vendor_id` ต้องอ้างอิงแถว `tb_vendor` ที่ยัง active และยังไม่ถูก soft-delete | สร้าง, แก้ไข, submit | ปฏิเสธด้วยข้อความ "ต้องระบุผู้ขายและต้องเป็นผู้ขายที่ได้รับการอนุมัติแล้ว" |
| `PO_VAL_003` | `currency_id` ต้องอ้างอิงแถว `tb_currency` ที่ยังไม่ถูก soft-delete และ `exchange_rate > 0` | สร้าง, แก้ไข, submit | ปฏิเสธด้วยข้อความ "ต้องระบุสกุลเงินของรายการและอัตราแลกเปลี่ยนต้องเป็นค่าบวก" |
| `PO_VAL_004` | `po_type` ต้องเป็นค่าใน `enum_purchase_order_type` (`manual`, `purchase_request`) ค่า default คือ `purchase_request` | สร้าง | ปฏิเสธด้วยข้อความ "ประเภท PO ต้องเป็น `manual` หรือ `purchase_request`" |
| `PO_VAL_005` | `credit_term_id` ต้องอ้างอิงแถว `tb_credit_term` ที่ยังไม่ถูก soft-delete ในกรณีที่ผู้ขายกำหนดให้ต้องมี | submit | ปฏิเสธด้วยข้อความ "ต้องระบุเงื่อนไขการชำระเงินสำหรับผู้ขายรายนี้" |
| `PO_VAL_006` | `order_date` ต้องไม่เป็น null และ `delivery_date >= order_date` | แก้ไข, submit | ปฏิเสธด้วยข้อความ "วันส่งมอบต้องไม่เร็วกว่าวันที่สั่งซื้อ" |
| `PO_VAL_007` | แต่ละแถว `tb_purchase_order_detail` ต้องมี `product_id` ที่ไม่เป็น null และอ้างอิงสินค้าที่ยัง active และยังไม่ถูก soft-delete | บันทึกบรรทัด, submit | ปฏิเสธบรรทัดนั้นด้วยข้อความ "ต้องระบุสินค้า" |
| `PO_VAL_008` | `order_qty > 0` และ `order_unit_id` ต้องไม่เป็น null | บันทึกบรรทัด, submit | ปฏิเสธบรรทัดด้วยข้อความ "จำนวนสั่งซื้อต้องมากกว่าศูนย์และต้องระบุหน่วยนับ" |
| `PO_VAL_009` | `order_unit_conversion_factor > 0`; `base_qty = order_qty × order_unit_conversion_factor` ปัดเศษเหลือ 3 ตำแหน่ง | บันทึกบรรทัด, submit | ปฏิเสธบรรทัดด้วยข้อความ "หน่วยนับสั่งซื้อต้องมีตัวคูณแปลงไปยังหน่วยฐานเป็นค่าบวก" และให้คำนวณ `base_qty` ใหม่ทุกครั้งที่บันทึก |
| `PO_VAL_010` | `price >= 0` (อนุญาตให้เป็น 0 เฉพาะเมื่อ `is_foc = true` เท่านั้น) | บันทึกบรรทัด, submit | ปฏิเสธบรรทัดด้วยข้อความ "ราคาต่อหน่วยต้องไม่ติดลบ; ราคา 0 ต้องเปิดธง FOC" |
| `PO_VAL_011` | `tax_rate >= 0` และ `discount_rate >= 0`; เมื่อ `is_tax_adjustment = true` หรือ `is_discount_adjustment = true` ระบบต้องบันทึกยอด override อย่างชัดเจน | บันทึกบรรทัด, submit | ปฏิเสธบรรทัดด้วยข้อความ "อัตราภาษี / ส่วนลดต้องไม่ติดลบ; การ override ด้วยตนเองต้องระบุยอดเงินที่ override" |
| `PO_VAL_012` | PO ต้องมีบรรทัด `tb_purchase_order_detail` อย่างน้อย 1 บรรทัดที่ยังไม่ถูก soft-delete ณ ตอน submit | submit | ปฏิเสธด้วยข้อความ "PO ต้องมีรายการอย่างน้อย 1 บรรทัด" |
| `PO_VAL_013` | ทุกบรรทัดของ PO ต้องใช้ `vendor_id` และ `currency_id` เดียวกับหัวเอกสาร (invariant ที่ว่า PO หนึ่งใบมีผู้ขายและสกุลเงินเดียว) | submit | ปฏิเสธด้วยข้อความ "ทุกบรรทัดของ PO ต้องใช้ผู้ขายและสกุลเงินเดียวกับหัวเอกสาร — ให้แยกเป็น PO หลายใบตาม vendor+currency" |
| `PO_VAL_014` | เมื่อ `po_type = purchase_request` ทุกบรรทัดต้องมีแถว bridge ใน `tb_purchase_order_detail_tb_purchase_request_detail` อย่างน้อย 1 แถวที่มี `pr_detail_qty > 0` | submit | ปฏิเสธด้วยข้อความ "บรรทัด PO ที่มาจาก PR ต้องเชื่อมกับบรรทัด PR ต้นทางผ่าน bridge table" |
| `PO_VAL_015` | การเปลี่ยนสถานะต้องเป็นไปตาม state machine ใน Section 5; การกระโดดข้ามจะถูกบล็อก | ตอนเปลี่ยนสถานะ | ปฏิเสธด้วยข้อความ "การเปลี่ยนสถานะจาก `<from>` ไปยัง `<to>` ไม่ถูกต้อง" |
| `PO_VAL_016` | การแก้ไข vendor, currency หรือบรรทัดใด ๆ ของ PO ที่ `po_status` ไม่ใช่ `draft` หรือ `in_progress` จะถูกบล็อก หลังจาก `sent` แล้วแก้ได้เฉพาะ `cancelled_qty` และโน้ตระดับบรรทัด | แก้ไข PO ที่ไม่ใช่ draft | ปฏิเสธด้วยข้อความ "PO ที่สถานะ `<status>` ไม่สามารถแก้ไขได้แล้ว — ให้ void หรือ close แทน" |

## 3. กฎการคำนวณ

ค่าทางการเงินทั้งหมดเก็บเป็น `Decimal(20, 5)` ระดับแถว, **อัตรา** ภาษีและส่วนลดเก็บเป็น `Decimal(15, 5)` ส่วน exchange rate ที่หัวเอกสาร PO เก็บเป็น `Decimal(15, 5)` การปัดเศษสำหรับการแสดงผลใช้แบบ half-up (banker's rounding สำหรับกรณี .5 พอดี) เหลือ 2 ตำแหน่งทศนิยมสำหรับยอดเงิน, 3 ตำแหน่งสำหรับจำนวน, และ 5 ตำแหน่งสำหรับอัตรา การคำนวณขั้นกลางทุกขั้นต้องอ่านค่าที่ปัดเศษแล้วของขั้นก่อนหน้าเสมอ (สอดคล้องกับกฎ `PR_046`–`PR_055` ของฝั่ง PR ที่ PO สืบทอดมา)

รหัสกฎใช้รูปแบบ `PO_CALC_NNN`

| รหัสกฎ | สูตร |
| ------ | ---- |
| `PO_CALC_001` (line subtotal) | `sub_total_price = Round(price × order_qty, 2)` |
| `PO_CALC_002` (line discount) | `discount_amount = Round(Round(sub_total_price, 2) × discount_rate, 2)` ยกเว้นเมื่อ `is_discount_adjustment = true` ให้ใช้ค่า override ที่บันทึกไว้แทน |
| `PO_CALC_003` (line net) | `net_amount = Round(Round(sub_total_price, 2) − Round(discount_amount, 2), 2)` |
| `PO_CALC_004` (line tax) | `tax_amount = Round(Round(net_amount, 2) × tax_rate, 2)` ยกเว้นเมื่อ `is_tax_adjustment = true` (override) |
| `PO_CALC_005` (line total) | `total_price = Round(Round(net_amount, 2) + Round(tax_amount, 2), 2)` |
| `PO_CALC_006` (base conversion) | สำหรับคอลัมน์เงินทุกคอลัมน์ `X` ในสกุลรายการ คอลัมน์ฝั่งฐาน `base_X = Round(Round(X, 2) × exchange_rate (5 dp), 2)` ครอบคลุม `base_price`, `base_sub_total_price`, `base_discount_amount`, `base_net_amount`, `base_tax_amount`, `base_total_price` |
| `PO_CALC_007` (FOC handling) | เมื่อ `is_foc = true` บรรทัดนั้นใส่ค่า `0` เข้าใน `sub_total_price`, `discount_amount`, `tax_amount`, และ `total_price` แต่ `order_qty` และ `base_qty` ยังถูกรวมเข้า `tb_purchase_order.total_qty` |
| `PO_CALC_008` (header subtotal) | `tb_purchase_order.total_price = Round(Σ Round(net_amount, 2), 2)` รวมเฉพาะบรรทัดที่ active และยังไม่ถูก soft-delete |
| `PO_CALC_009` (header tax) | `tb_purchase_order.total_tax = Round(Σ Round(tax_amount, 2), 2)` |
| `PO_CALC_010` (header grand total) | `tb_purchase_order.total_amount = Round(Round(total_price, 2) + Round(total_tax, 2), 2)` มีค่าเทียบเท่ากับ `Σ Round(line.total_price, 2)` |
| `PO_CALC_011` (header qty) | `tb_purchase_order.total_qty = Round(Σ Round(base_qty, 3), 3)` — ใช้ base UoM เท่านั้นเพราะบรรทัดอาจใช้ order UoM ต่างกัน |
| `PO_CALC_012` (rounding mode) | การปัดเศษทั้งหมดใช้แบบ half-up (banker's) ตาม `PR_047`; รูปแบบตัวเลขตามภูมิภาคถูกใช้เฉพาะตอนแสดงผล ไม่ใช่ตอนจัดเก็บ (`PR_050`) |

### 3.1 ตัวอย่างคำนวณ (สกุล ฿ THB)

PO มี 2 บรรทัด ผู้ขายใช้สกุล THB อัตราแลกเปลี่ยนไปยังสกุลฐาน THB = 1.00000 (ไม่มี FX)

- บรรทัดที่ 1: `order_qty = 10.000`, `price = ฿125.50`, `discount_rate = 5%`, `tax_rate = 7%`, `is_foc = false`
  - `sub_total_price = Round(125.50 × 10.000, 2) = ฿1,255.00`
  - `discount_amount = Round(1,255.00 × 0.05, 2) = ฿62.75`
  - `net_amount = Round(1,255.00 − 62.75, 2) = ฿1,192.25`
  - `tax_amount = Round(1,192.25 × 0.07, 2) = ฿83.46`
  - `total_price = Round(1,192.25 + 83.46, 2) = ฿1,275.71`
- บรรทัดที่ 2: `order_qty = 4.000`, `price = ฿89.00`, `discount_rate = 0%`, `tax_rate = 7%`, `is_foc = false`
  - `sub_total_price = ฿356.00`; `discount_amount = ฿0.00`; `net_amount = ฿356.00`
  - `tax_amount = Round(356.00 × 0.07, 2) = ฿24.92`
  - `total_price = ฿380.92`
- การรวมที่หัวเอกสาร:
  - `total_price = Round(1,192.25 + 356.00, 2) = ฿1,548.25`
  - `total_tax = Round(83.46 + 24.92, 2) = ฿108.38`
  - `total_amount = Round(1,548.25 + 108.38, 2) = ฿1,656.63`

หากเพิ่มบรรทัด FOC อีก 1 บรรทัด (`order_qty = 1.000`, `price = 0`, `is_foc = true`), `total_qty` จะเพิ่มขึ้น 1.000 (หน่วยฐาน) แต่ `total_amount` จะไม่เปลี่ยน

## 4. กฎการอนุมัติ

รหัสกฎใช้รูปแบบ `PO_AUTH_NNN` สิทธิ์การเข้าถึงถูกบังคับใช้ผ่าน RBAC ที่ชั้น API; กฎด้านล่างระบุนโยบาย ไม่ใช่ implementation ชื่อบทบาทอ้างอิงตารางใน carmen/docs; เกณฑ์ "high-value" ตั้งค่าได้ตาม tenant และมีค่า default ตามขั้นตอนของ Procurement Manager ที่กำหนดใน workflow ที่ `tb_purchase_order.workflow_id` อ้างถึง

| รหัสกฎ | ผู้กระทำ | สิทธิ์ | เงื่อนไข |
| ------ | --------- | ------- | --------- |
| `PO_AUTH_001` | Procurement Officer | สร้าง PO (`po_status = draft`) | ใช้ได้ทั้ง `po_type` แบบ `manual` และ `purchase_request` |
| `PO_AUTH_002` | Procurement Officer | แก้ไข PO | เฉพาะเมื่อ `po_status ∈ {draft, in_progress}` และผู้ใช้เป็น buyer ที่กำหนด หรือถือ `workflow_current_stage` ปัจจุบัน |
| `PO_AUTH_003` | Procurement Officer | Submit PO (`draft → in_progress`) | ต้องมีบรรทัดอย่างน้อย 1 บรรทัดและผ่าน validation ทั้งหมดใน Section 2 |
| `PO_AUTH_004` | Procurement Manager | อนุมัติ PO ที่ขั้น high-value (`in_progress → sent` สำหรับยอดเกินเกณฑ์) | `tb_purchase_order.total_amount` เกินเกณฑ์ high-value ที่กำหนดในเวิร์กโฟลว์ของ tenant กรณีต่ำกว่าเกณฑ์ Procurement Officer สามารถอนุมัติเองไปยัง `sent` ได้ถ้าเวิร์กโฟลว์อนุญาต |
| `PO_AUTH_005` | Procurement Manager | ลบ PO | เฉพาะเมื่อ `po_status = draft` เท่านั้น (soft-delete ผ่าน `deleted_at`) |
| `PO_AUTH_006` | Procurement Officer หรือ Procurement Manager | ส่ง PO ให้ผู้ขาย (`sent`) | หลังการอนุมัติ ระบบกำหนด `tb_purchase_order.email` และ `approval_date` |
| `PO_AUTH_007` | Procurement Manager | ยกเลิก PO (`* → voided`) | ทำได้จากทุกสถานะที่ยังไม่สิ้นสุด (`draft`, `in_progress`, `sent`, `partial`) เมื่อเป็น `voided` แล้วเปลี่ยนสถานะต่อไม่ได้ |
| `PO_AUTH_008` | Inventory Manager (ผู้รับสินค้า) | สร้าง GRN ที่อ้างอิง PO; ปิด PO (`partial → closed` early termination) | ทำได้เฉพาะเมื่อ `po_status ∈ {sent, partial}` |
| `PO_AUTH_009` | Finance Officer | ดูข้อมูล, export รายงาน | read-only ครอบคลุมทุกสถานะ |
| `PO_AUTH_010` | การแบ่งแยกหน้าที่ (Segregation of duties) | Purchaser ≠ Receiver | ผู้ที่สร้างหรือส่ง PO (`tb_purchase_order.buyer_id` หรือ `last_action_by_id` ของ transition ไป `sent`) ต้องไม่ใช่คนเดียวกับผู้ที่ post GRN กับ PO ใบนั้น บังคับใช้ตอนสร้าง GRN |
| `PO_AUTH_011` | การอนุมัติตามเวิร์กโฟลว์ | Stage-gated approval | ชุดผู้ใช้ใน `tb_purchase_order.user_action.execute` ที่ `workflow_current_stage` ปัจจุบันคือชุดเดียวที่ได้รับอนุญาตให้ขับเคลื่อนเอกสาร; การพยายามอนุมัติจากผู้อื่นจะถูกปฏิเสธ |

## 5. กฎการ Post

ค่าสถานะคือสมาชิกของ `enum_purchase_order_doc_status` ที่ระบุใน [[purchase-order/01-data-model]] § 4 ได้แก่ `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed` ตัวเอกสาร PO เองไม่มีการ post GL แยก; การ "post" PO หมายถึงการเปลี่ยนสถานะ การบันทึก audit trail (`history`, `workflow_history`) และการ trigger side effect ทางปลายน้ำ การ post GL จริง ๆ เกิดที่ GRN (inventory accrual) และที่ three-way match success (AP invoice)

รหัสกฎใช้รูปแบบ `PO_POST_NNN`

| รหัสกฎ | Transition / เหตุการณ์ | ผลกระทบ |
| ------ | ---------------------- | -------- |
| `PO_POST_001` | สร้าง (→ `draft`) | Insert `tb_purchase_order` ด้วย `po_status = draft`, `doc_version = 0`, `total_qty = total_price = total_tax = total_amount = 0` เพิ่มรายการใน `history`: `{ po_status: 'draft', action: 'created', by, at }` |
| `PO_POST_002` | Submit (`draft → in_progress`) | คำนวณยอดรวมใหม่ทั้งหมด (`PO_CALC_008`–`PO_CALC_011`) กำหนด `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user` ตั้ง `workflow_history` เริ่มต้น, `workflow_current_stage = <stage แรก>`, `stages_status = [...]` และเติม `user_action.execute` จากนิยาม stage ของเวิร์กโฟลว์ เพิ่มรายการ `history` การจอง budget/inventory แบบ soft commitment ถูกสร้างขึ้นทางปลายน้ำโดยเวิร์กโฟลว์ |
| `PO_POST_003` | อนุมัติ (ภายใน `in_progress`) | เพิ่มรายการ `workflow_history`; เลื่อน `workflow_current_stage` ไป stage ถัดไป อัปเดต `user_action.execute` สำหรับ stage ถัดไป กำหนด `last_action = approved` สถานะยังไม่เปลี่ยน — PO อยู่ที่ `in_progress` จนกว่าจะถึง stage อนุมัติสุดท้าย |
| `PO_POST_004` | อนุมัติขั้นสุดท้าย (`in_progress → sent`) | กำหนด `po_status = sent`, `approval_date = now()`, `last_action = approved` เพิ่มรายการ `history` ส่ง PO ให้ผู้ขายผ่านชั้น email/transmit ของแอปพลิเคชัน นับจากนี้ PO ถือเป็นข้อผูกพันที่ผู้ขายเห็นแล้ว |
| `PO_POST_005` | ปฏิเสธ (`in_progress → draft`) | กำหนด `po_status = draft`, `last_action = rejected`, รีเซ็ต `workflow_current_stage` กลับไป stage แรก เพิ่มคอมเมนต์การปฏิเสธใน `tb_purchase_order_comment` (type `system`) บรรทัดยังแก้ไขได้ |
| `PO_POST_006` | GRN รับบางส่วน (`sent → partial` หรือ `partial → partial`) | สำหรับแต่ละบรรทัด PO ที่ได้รับผลกระทบ การ post GRN จะเพิ่ม `tb_purchase_order_detail.received_qty` เท่ากับ qty ของ GRN (ใน order UoM) ถ้า `received_qty < order_qty − cancelled_qty` สำหรับอย่างน้อย 1 บรรทัด ให้กำหนด `po_status = partial` แถว bridge `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` ถูกอัปเดตตามสัดส่วนเพื่อรักษาความสามารถในการมองเห็น allocation ฝั่ง PR |
| `PO_POST_007` | GRN รับครบ (`sent → completed` หรือ `partial → completed`) | เมื่อทุกบรรทัดที่ active เป็นไปตามเงื่อนไข `received_qty = order_qty − cancelled_qty` ให้กำหนด `po_status = completed` เพิ่มรายการ `history` PO ถูกปิดตามปกติ — ไม่รับ GRN เพิ่มอีก |
| `PO_POST_008` | Three-way match สำเร็จ | ตรวจสอบว่า (a) บรรทัด PO, (b) บรรทัด GRN, และ (c) ใบแจ้งหนี้ผู้ขาย (AP) สำหรับสินค้าตัวเดียวกัน มี qty (ภายใน tolerance) และราคา (ภายใน tolerance) ตรงกัน เมื่อสำเร็จ โมดูล AP จะเคลียร์ accrual ของ GRN และ post ใบแจ้งหนี้ผู้ขายเพื่อชำระเงิน ตัว PO ไม่เปลี่ยนสถานะจากเหตุการณ์นี้ — ยังคงอยู่ที่สถานะที่สะท้อนการรับสินค้า (`partial` หรือ `completed`) |
| `PO_POST_009` | Three-way match ล้มเหลว | ใบแจ้งหนี้ AP ถูก hold อยู่ในสถานะ dispute เพิ่มคอมเมนต์ `system` บน PO และเปิดรายการ deviation ฝั่ง vendor / vendor-pricelist PO ไม่ถูก void อัตโนมัติ — การแก้ไขทำด้วยมือผ่านการแก้ไขเอกสาร, credit note หรือ void |
| `PO_POST_010` | ยกเลิก (`* → voided` จาก `draft`, `in_progress`, `sent`, หรือ `partial`) | กำหนด `po_status = voided`, `is_active = false`, `last_action_at_date = now()` reverse soft commitment ที่อาจเปิดไว้ทางปลายน้ำ (budget, การแจ้งผู้ขาย) ถ้า void จาก `partial` GRN ที่ post แล้วยังถือว่า valid — มีเพียงส่วนที่ยังไม่รับเท่านั้นที่ถูก void สถานะ `voided` เป็น terminal |
| `PO_POST_011` | ปิดเอกสาร (`partial → closed` ปิดก่อนรับครบ) | กำหนด `po_status = closed` สำหรับแต่ละบรรทัดที่ยังรับไม่ครบ แอปพลิเคชันต้องเขียน qty คงเหลือเข้าใส่ `cancelled_qty` เพื่อให้ `received_qty + cancelled_qty = order_qty` ใช้เมื่อผู้ขายไม่สามารถส่งของส่วนที่เหลือได้ ต่างจาก `completed` (รับครบ) สถานะ `closed` เป็น terminal |
| `PO_POST_012` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `draft` เท่านั้นตาม `PO_AUTH_005` แถวยังคงอยู่ในฐานข้อมูล; ทุก unique index มี `deleted_at` รวมอยู่ด้วย ดังนั้น PO ใหม่สามารถใช้ `po_no` เดิมซ้ำได้ |

State diagram (ยึด Prisma เป็นหลัก):

```
[*] → draft → in_progress → sent → partial → completed
                ↑    ↓        ↓       ↓         ↑
              (reject)        ↓       ↓     (รับครบ)
                              ↓       └→ closed (ปิดก่อนรับครบ)
                              ↓
        any non-terminal → voided  (admin)
```

`completed`, `closed`, และ `voided` เป็น terminal `draft` รองรับการ soft-delete

## 6. กฎ Cross-Module

รหัสกฎใช้รูปแบบ `PO_XMOD_NNN`

| รหัสกฎ | โมดูลที่เกี่ยวข้อง | กฎ |
| ------ | ------------------ | --- |
| `PO_XMOD_001` | [[purchase-request]] | เมื่อ `po_type = purchase_request` PO ต้องถูกสร้างผ่าน flow แปลง PR → PO ซึ่งจัดกลุ่ม PR ที่อนุมัติแล้วตาม `(vendor_id, currency_id)` และสร้าง PO หนึ่งใบต่อกลุ่ม แต่ละบรรทัด PO ที่เกิดขึ้นต้องมีแถว bridge ใน `tb_purchase_order_detail_tb_purchase_request_detail` อย่างน้อย 1 แถวที่เชื่อมกลับไปยังบรรทัด PR ต้นทาง (`PO_VAL_014`) |
| `PO_XMOD_002` | [[purchase-request]] | Bridge รองรับทั้ง consolidation (หลายบรรทัด PR → หนึ่งบรรทัด PO) และ partial conversion (หนึ่งบรรทัด PR → หลายบรรทัด PO) บรรทัด PR ถือว่าถูกแปลงครบเมื่อ `Σ bridge.pr_detail_qty` สำหรับ `pr_detail_id` นั้นเท่ากับ qty ที่ได้รับการอนุมัติของบรรทัด PR |
| `PO_XMOD_003` | [[good-receive-note]] | GRN สร้างได้เฉพาะกับ PO ที่ `po_status ∈ {sent, partial}` (`PO_AUTH_008`) เท่านั้น บรรทัด GRN อ้างอิงกลับไปยัง `tb_purchase_order_detail.id` qty คงเหลือสำหรับรับคือ `order_qty − received_qty − cancelled_qty` ต่อ `PO_POST_006` |
| `PO_XMOD_004` | [[good-receive-note]] | การรับ qty ที่จะเกิน qty คงเหลือจะถูกปฏิเสธ ยกเว้นการตั้งค่าของ tenant อนุญาตให้รับเกินภายใน tolerance ที่กำหนด มิฉะนั้นบรรทัด GRN จะถูกตัดไม่ให้เกิน qty คงเหลือ |
| `PO_XMOD_005` | [[vendor-pricelist]] | ณ การแปลง PR → PO ระบบจะ snapshot `price` จาก vendor pricelist ที่ยังใช้งานสำหรับ `(vendor, product, currency)` ที่ตรงกัน หากไม่มีแถว pricelist ที่ active จะใช้ราคาล่าสุดของ PR และเพิ่มคอมเมนต์ `system` เพื่อแจ้งว่าขาด pricelist coverage |
| `PO_XMOD_006` | [[vendor-pricelist]] | เมื่อ buyer override ราคา snapshot จะมีการบันทึก delta ระหว่าง override กับ pricelist ใน `tb_purchase_order_detail_comment` เป็น deviation entry deviation ที่เกิน tolerance ของ tenant จะ route PO ไปยังขั้นอนุมัติ high-value แม้ `total_amount` จะต่ำกว่าเกณฑ์ก็ตาม |
| `PO_XMOD_007` | AP / Three-way match | เมื่อ post GRN โมดูล AP จะตั้ง liability แบบ inventory accrual ขึ้น accrual จะถูกเคลียร์ และใบแจ้งหนี้ผู้ขายจะถูก post เพื่อชำระเงิน เฉพาะเมื่อ three-way match สำเร็จตาม `PO_POST_008` การปิด PO (`completed` หรือ `closed`) เพียงอย่างเดียวไม่เคลียร์ accrual — เป็นหน้าที่ของ AP ที่ต้อง match กับใบแจ้งหนี้จริง |
| `PO_XMOD_008` | [[inventory]] | Inventory on-hand **ไม่** ถูกเพิ่มจากการ post PO — จะถูกเพิ่มเมื่อ post GRN เท่านั้น (ซึ่งอยู่ในขอบเขตของโมดูล GRN) PO จะให้ qty "on-order" สำหรับ pipeline ที่ระบบ inventory planning อ่านผ่าน `order_qty − received_qty − cancelled_qty` บนบรรทัด PO ที่ยัง active |
| `PO_XMOD_009` | [[inventory]] | `base_qty` ของบรรทัด PO (คำนวณในหน่วยฐานผ่าน `PO_CALC_011`) คือจำนวนที่ระบบ inventory reservation และการคำนวณ projected-on-hand อ่าน; order UoM ใช้สำหรับการแสดงต่อผู้ขายเท่านั้น |

## 7. แหล่งอ้างอิง

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — เอกสาร BA รวมของ PO (Section 1.3 Business Rules, Section 1.4 System Calculation Rules, Section 6.1 State Diagram, Section 2.5 RBAC) ป้ายสถานะถูก reconcile ไปยังค่า enum ของ Prisma ตาม [[purchase-order/01-data-model]] § 5
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — โครงสร้าง validation, error type, และ workflow state ที่ PO สืบทอด
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — Section 3 (Business Rules) และ Section 3.6 (System Calculation Rules); กฎการคำนวณของ PO (`PO_CALC_*`) เป็นคู่ที่ตรงกันกับกฎฝั่ง PR (`PR_036`–`PR_055`)
- ไฟล์พี่น้อง: `en/purchase-order/01-data-model.md` — โมเดล Prisma ที่เป็น canonical, ค่า enum, และการเชื่อมตาราง bridge ที่ Section 5 และ Section 6 อ้างถึง
- การ implement กฎฝั่ง backend (เมื่อเพิ่มเข้ามา): `../carmen-turborepo-backend-v2/apps/` — โมดูล purchase-order service เป็นจุด implement กฎเหล่านี้ (status guard, calculation utility, การอ้างกลับของการ post GRN, การ orchestrate three-way match)
