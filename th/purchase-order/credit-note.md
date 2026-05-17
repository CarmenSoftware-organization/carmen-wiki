---
title: ใบลดหนี้ (Credit Note)
description: เอกสารใบลดหนี้จากผู้ขายที่กลับรายการบางส่วนหรือทั้งหมดของ PO/GRN ก่อนหน้า — ปรับยอด AP และอาจคืนสินค้าหรือ revalue ต้นทุน inventory layer
published: true
date: 2026-05-17T07:00:36.000Z
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ใบลดหนี้ (Credit Note)

> **At a Glance**
> **เจ้าของ:** ฝ่ายจัดซื้อ / AP &nbsp;·&nbsp; **ตาราง:** `tb_credit_note` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** ใช้นิยามเดียวกับฝั่ง PO &nbsp;·&nbsp; **เอกสารต้นทาง:** [[good-receive-note]] &nbsp;·&nbsp; การปรับยอดหลังรับของกับ GRN เดิม — กลับยอด AP และคืนสินค้าหรือ revalue ต้นทุน

![ใบลดหนี้ (Credit Note) screen](/assets/screenshots/purchase-order/credit-note.png)

## 1. ภาพรวมและผู้ใช้งาน

**ใบลดหนี้ (Credit Note — CRN)** คือเอกสารสำหรับการแก้ไขหลังการรับสินค้าในห่วงโซ่ procure-to-pay เมื่อผู้ขายเรียกเก็บเกิน, จัดส่งของชำรุดหรือขาด, หรือให้ส่วนลดย้อนหลัง CRN จะเป็นเอกสารที่บันทึกการกลับรายการกับ GRN ต้นทาง และกลับยอด AP liability ที่เคยตั้งไว้ มีสองชนิดคือ **`quantity_return`** ที่คืนสินค้าจริง (ลด stock, กลับ cost layer) และ **`amount_discount`** ที่แก้ราคาอย่างเดียว (ไม่กระทบสต๊อก, revalue ต้นทุน lot)

**สร้างโดย** ฝ่ายจัดซื้อเมื่อได้รับ credit invoice จากผู้ขาย &nbsp;·&nbsp; **อนุมัติโดย** ผู้อนุมัติใน workflow (ใช้เส้นทางเดียวกับ PO) &nbsp;·&nbsp; **อ่านโดย** ฝ่าย AP (เป็นต้นทาง debit memo) และ costing engine

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ตั้ง CN กับ GRN | จัดซื้อ → ใบลดหนี้ → **สร้างใหม่** | เลือก GRN; รายการจะ pre-fill จากปริมาณที่รับ |
| เลือก `quantity_return` กับ `amount_discount` | Header field `credit_note_type` | Return จะย้ายสต๊อก; Discount แค่ revalue ต้นทุน |
| ตั้งค่า return-to-stock vs write-off | (อัตโนมัติ) | Engine จะคืนเข้า FIFO lot เดิม; ถ้า lot ถูกใช้หมดแล้ว จะลง variance ที่บัญชี write-off — ดู [[costing]] `COST_XMOD_006` |
| โพสต์ CN ไปยัง AP | เมื่อ `doc_status = completed` | ออก AP debit memo เสมอ (มูลค่า `base_total_price`) |
| ระบุเลขที่ credit invoice ของผู้ขาย | Header `invoice_no` / `tax_invoice_no` | จำเป็นสำหรับ AP three-way match |
| Void CN ที่ posted แล้ว | Detail → **Void** | ทำได้เฉพาะตอนงวด posting ยังเปิด; จะกลับ posting ทุกรายการ |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | วิธีแก้ |
|---|---|---|
| "GRN required for quantity_return" | ชนิดเป็น `quantity_return` แต่ `grn_id` ว่าง | เลือก GRN ต้นทาง |
| "Return qty exceeds receipted - already returned" | ปริมาณคืนสะสมจะเกิน lot | ลดปริมาณ หรือแบ่งหลาย lot |
| "Tax rate must match GRN snapshot" | ต้องตั้ง `is_tax_adjustment = true` สำหรับภาษีย้อนหลัง | toggle `is_tax_adjustment` บนบรรทัด |
| "Period is closed — cannot void" | งวด posting ของ CRN ปิดแล้ว | ใช้ JV แก้แทน |
| "Rate not in history" | ไม่มี `tb_exchange_rate` ของวัน `cn_date` สำหรับ currency | เพิ่ม rate แล้วเปิด CRN ใหม่ (ดู [[master-data/exchange-rate]]) |
| "User not authorised at this stage" | ผู้ใช้ที่ลงชื่ออยู่ไม่อยู่ใน `user_action.execute[]` | รอผู้อนุมัติที่ถูกต้อง หรือ escalate |

## 4. กรณีพิเศษ

- **การปัดเศษเงิน.** Money fields เก็บที่ `Decimal(20,5)`; ยอดที่คำนวณ round half-up ที่ **2 ตำแหน่ง** ที่ระดับบรรทัด แล้ว sum ขึ้น header (ตรงกับ PO/GRN)
- **FX revaluation.** เมื่อ `cn_date != grn_date` และ currency ต่างจาก BU base, engine resolve rate ใหม่ที่ `cn_date` และโพสต์ส่วนต่างเป็น FX gain/loss ตาม [[costing]] `COST_CALC_005`
- **Return-to-stock vs write-off.** `quantity_return` จะกลับ FIFO lot เดิมถ้ายังอยู่; ถ้า lot ถูก consume หมดแล้ว (issue ผ่าน SR / stock-out) variance ลงที่บัญชี **inventory write-off** ที่ตั้งไว้ (ไม่มี negative inventory)
- **Snapshot semantics.** ชื่อผู้ขาย, สินค้า, currency, FX rate, tax rate, และ pricelist refs ถูก snapshot ตอน draft การแก้ไข master record ไม่มีผลย้อนหลังกับ CRN
- **ช่วงเวลาที่ void ได้.** CRN ที่ `completed` แล้ว void ได้เฉพาะตอนงวดเปิด เมื่อ `tb_period.status = closed` การ void จะถูกปฏิเสธ
- **AP โพสต์เสมอ.** แม้แต่ `quantity_return` ก็จะมี debit memo เท่ากับ `base_total_price` ไปที่ AP ของผู้ขาย

---

## 5. โมเดลข้อมูล (Dev)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`)

### 5.1 `tb_credit_note`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `cn_no` | `String? @db.VarChar` | Yes | เลขอ้างอิง CRN; unique ในกลุ่ม non-deleted |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่เอกสาร — ขับเคลื่อนการ resolve FX rate |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `in_progress` → `completed` / `cancelled` / `voided` |
| `credit_note_type` | `enum_credit_note_type` | No | `quantity_return` หรือ `amount_discount` |
| `vendor_id`, `vendor_name` | `String? @db.Uuid` / `VarChar` | Yes | Snapshot จาก `tb_vendor` ตอน draft |
| `grn_id`, `grn_no`, `grn_date` | mixed | Yes | GRN ต้นทาง — จำเป็นสำหรับ `quantity_return`, optional สำหรับ `amount_discount` |
| `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` | mixed | Yes | อ้างอิง pricelist (ทางเลือก) |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Snapshot currency + FX rate ที่ `cn_date` |
| `cn_reason_id`, `cn_reason_name`, `cn_reason_description` | mixed | Yes | FK + snapshot ถึง `tb_credit_note_reason` |
| `invoice_no`, `invoice_date`, `tax_invoice_no`, `tax_invoice_date` | mixed | Yes | เลขที่ credit invoice ของผู้ขายสำหรับ AP matching |
| `workflow_id`, `workflow_*`, `user_action` | mixed | Yes | สถานะ workflow (ดู Section 6) |
| `last_action`, `last_action_*` | mixed | Yes | การเปลี่ยนสถานะล่าสุด |
| `note`, `description`, `info`, `dimension`, `doc_version` | mixed | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([cn_no, deleted_at])` map `creditnote_cn_no_u`; `@@index([cn_no])`. FKs ไปยัง `tb_vendor`, `tb_currency`, `tb_good_received_note`, `tb_credit_note_reason` — ทั้งหมด `onDelete: NoAction`

### 5.2 `tb_credit_note_detail`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `credit_note_id`, `sequence_no` | mixed | No / No / Yes | PK, parent FK, ลำดับ |
| `inventory_transaction_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_inventory_transaction` ต้นทางสำหรับ `quantity_return`; Null สำหรับ `amount_discount` |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | สถานที่รับเดิม; การคืนใช้ที่เดียวกัน |
| `product_id`, `product_*` | mixed | No / Yes | Snapshot สินค้า |
| `return_qty`, `return_unit_*`, `return_conversion_factor`, `return_base_qty` | `Decimal(20,5)` / mixed | Yes | ปริมาณคืนในหน่วยผู้ใช้ + base; `0` สำหรับ `amount_discount` |
| `price` | `Decimal(20,5)` | Yes | ราคาต่อหน่วย — มักเป็นราคาที่ GRN |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | Snapshot ภาษี + การแปลงเป็น base |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | Snapshot ส่วนลด + base |
| `extra_cost_amount`, `base_extra_cost_amount` | `Decimal(20,5)` | Yes | ค่าใช้จ่ายเพิ่ม (เช่น ค่าขนส่ง) ที่ลด |
| `sub_total_price`, `net_amount`, `total_price` | `Decimal(20,5)` | Yes | ยอดบรรทัดใน currency ธุรกรรม |
| `base_*` | `Decimal(20,5)` | Yes | ค่าเดียวกันใน BU base currency |
| `info`, `dimension`, `doc_version`, audit | — | Yes | Metadata มาตรฐาน |

**Constraints:** `@@unique([credit_note_id, sequence_no, deleted_at])`; `@@index([credit_note_id, sequence_no])`. FKs `onDelete: NoAction`

### 5.3 ตาราง Comment

`tb_credit_note_comment` และ `tb_credit_note_detail_comment` ใช้รูปแบบ comment มาตรฐาน — ดู [[purchase-request/01-data-model]]

## 6. วงจรการทำงาน / กติกาทางธุรกิจ

`doc_status`: `draft` → `in_progress` → `completed` (terminal); `cancelled` และ `voided` เป็น terminal ทางเลือก

- **`draft`** — แก้ไขได้; ยังไม่กระทบ GL, AP, inventory
- **`in_progress`** — ล็อกยกเว้นที่ stage ปัจจุบันอนุญาต; ผู้อนุมัติมาจาก `user_action.execute[]` ตาม [[system-config/workflow]]
- **`completed`** — โพสต์ inventory สำหรับ `quantity_return`; revalue ต้นทุนสำหรับ `amount_discount`; AP debit memo สำหรับทั้งคู่
- **`cancelled`** — ยุติก่อน complete; ไม่มี posting
- **`voided`** — กลับ CRN ที่ `completed` ภายในงวดที่เปิด; กลับ posting ทุกรายการ

การจัดเส้นทาง stage, mapping ของ role และการ gate action ใช้ **นิยาม workflow ฝั่ง PO** เป็น default. **GRN anchor:** บรรทัดคืนถูกจำกัดด้วย `receipted - already returned` ของ lot. **Authorisation:** เฉพาะผู้ใช้ใน `user_action.execute[]` ทำ transition ได้

## 7. ความเชื่อมโยงข้ามโมดูล

- [[purchase-order]] — PO ต้นทางของ GRN เดิม; ยอด CRN roll-up ใน PO open/received reporting
- [[good-receive-note]] — เอกสารต้นทางของทุกบรรทัด `quantity_return`
- [[costing]] — `COST_POST_003` (revalue ยอด), `COST_XMOD_006` (กลับต้นทุน lot), `COST_CALC_005` (FX revaluation)
- [[master-data/credit-note-reason]] — taxonomy ของเหตุผล
- [[master-data/exchange-rate]] — การ resolve rate ตาม `cn_date`
- [[master-data/vendor]] — Snapshot ผู้ขายและการ route AP debit memo

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (บรรทัด 321-397), `tb_credit_note_detail` (บรรทัด 434-508), `tb_credit_note_comment` (บรรทัด 399-432), `tb_credit_note_detail_comment` (บรรทัด 510-543), enums `enum_credit_note_type` และ `enum_credit_note_doc_status` (บรรทัด 195-206)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/credit-note/`
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram
