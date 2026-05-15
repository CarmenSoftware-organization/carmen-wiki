---
title: ใบสั่งซื้อ — แบบจำลองข้อมูล
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล purchase-order (อิงจาก Prisma schema)
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — แบบจำลองข้อมูล

> **แหล่งข้อมูลอ้างอิงหลัก (Source of truth):** Prisma schema ฝั่ง backend อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อเขียนหรือปรับปรุงหน้านี้
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ในแต่ละ package เป็นไฟล์ที่ถูกสร้างขึ้นอัตโนมัติ ไม่ใช่แหล่งอ้างอิง

## 1. ภาพรวม

โมดูล purchase-order เป็นเจ้าของเอนทิตีจำนวน 5 รายการในสคีมาฝั่ง tenant ได้แก่ ส่วนหัวเอกสาร PO (`tb_purchase_order`), บรรทัดรายการ (`tb_purchase_order_detail`), คอมเมนต์ / activity log ทั้งระดับหัวเอกสารและระดับบรรทัด (`tb_purchase_order_comment`, `tb_purchase_order_detail_comment`), และตารางสะพาน (`tb_purchase_order_detail_tb_purchase_request_detail`) ที่ผูกบรรทัด PO กลับไปยังบรรทัด PR ต้นทางได้หนึ่งหรือหลายรายการ เช่นเดียวกับ PR การติดตามขั้นตอน workflow ไม่ได้แยกเป็นตารางต่างหาก แต่เก็บแบบ inline บนหัวเอกสารในรูปคอลัมน์ JSON (`workflow_history`, `workflow_current_stage`, `stages_status`) ร่วมกับ foreign key ไปยังตารางตั้งค่ากลาง `tb_workflow` ส่วนไทม์ไลน์เหตุการณ์เปลี่ยน stage ที่ persist ลงฐานข้อมูลจะถูกเก็บผ่านตารางคอมเมนต์

PO อยู่ **ปลายน้ำของ [[purchase-request]]** และ **ต้นน้ำของ [[good-receive-note]]** ในห่วงโซ่ procure-to-pay การเชื่อม PR→PO ทำผ่านตารางสะพานที่กล่าวข้างต้น ตารางเดียวกันนี้ยังเก็บ qty ที่รับและ qty FOC ต่อบรรทัด PR ที่ถูก allocate รองรับทั้ง PR consolidation (หลายบรรทัด PR → หนึ่งบรรทัด PO) และ partial conversion (หนึ่งบรรทัด PR → หลายบรรทัด PO) บรรทัด PO มีคอลัมน์ running `received_qty` และ `cancelled_qty` เพื่อให้ "qty คงเหลือ" สำหรับ GRN คือ `order_qty − received_qty − cancelled_qty` ความสัมพันธ์จากบรรทัด PO ไปยังบรรทัด GRN (`tb_good_received_note_detail`) คือสิ่งที่ปิดวงจรนี้ บรรทัด PO ยังอ้างอิง [[product]], `tb_tax_profile`, และ `tb_unit` (สองครั้ง — สำหรับ order UoM และ base UoM) ส่วนหัวเอกสารอ้างอิง `tb_vendor`, `tb_currency`, และ `tb_credit_term` เอนทิตี PO ทั้งหมดอยู่ในสคีมา Prisma ฝั่ง tenant — สคีมาฝั่ง platform ไม่มีโมเดล purchase-order

ส่วนหัวเก็บบริบทของ vendor, currency, exchange-rate และ credit-term เพียงครั้งเดียวต่อ PO — โดยการออกแบบ ทุกบรรทัดของ PO เดียวกันต้องใช้ vendor และ currency เดียวกัน ซึ่งเป็นเหตุผลที่ flow แปลง PR เป็น PO ต้องจัดกลุ่ม PR ที่เลือกตาม `(vendor, currency)` ก่อนกระจาย ค่า default ของ `tb_purchase_order.po_type` คือ `purchase_request` ซึ่งทำให้การสร้างจาก PR เป็น path มาตรฐาน ส่วน `manual` เป็นทางเลือกสำหรับ PO ที่สร้างจากฝั่งจัดซื้อโดยไม่มี PR ต้นทาง

## 2. เอนทิตี

### 2.1 tb_purchase_order

ส่วนหัวเอกสาร PO เก็บเลขที่อ้างอิง บริบทของ vendor / currency / credit-term, ภาพรวม workflow, ยอดรวม และคอลัมน์ audit หนึ่งหัวเอกสารมีบรรทัดรายการและคอมเมนต์ได้หลายรายการ

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก สร้างผ่าน `gen_random_uuid()` |
| `po_no` | `String @db.VarChar` | ไม่ | เลขที่อ้างอิง PO แบบมนุษย์อ่านได้ |
| `po_status` | `enum_purchase_order_doc_status` | ใช่ | สถานะเอกสาร; default `draft` |
| `po_type` | `enum_purchase_order_type` | ไม่ | โหมดการสร้าง PO; default `purchase_request` (สร้างจาก PR เป็น path มาตรฐาน) |
| `description` | `String` | ใช่ | คำอธิบาย / เหตุผลแบบ free-text บนหัวเอกสาร |
| `order_date` | `DateTime @db.Timestamptz(6)` | ใช่ | วันที่สั่งซื้อบนหัวเอกสาร |
| `delivery_date` | `DateTime @db.Timestamptz(6)` | ใช่ | วันที่ต้องการส่งระดับหัวเอกสาร |
| `workflow_id` | `String @db.Uuid` | ใช่ | อ้างอิงไปยังแถวใน `tb_workflow` (ไม่ประกาศ Prisma `@relation` บนโมเดลนี้ — application เป็นผู้ resolve) |
| `workflow_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ workflow |
| `workflow_history` | `Json @db.JsonB` | ใช่ | ไทม์ไลน์เปลี่ยน stage แบบ append-only; default `[]` แต่ละรายการมี `stage`, `action`, `message`, `by`, `at` |
| `workflow_current_stage` | `String @db.VarChar` | ใช่ | slug ของ stage ที่ถือ PO อยู่ในขณะนี้ |
| `workflow_previous_stage` | `String @db.VarChar` | ใช่ | slug ของ stage ก่อนหน้า |
| `workflow_next_stage` | `String @db.VarChar` | ใช่ | slug ของ stage ถัดไป |
| `user_action` | `Json @db.JsonB` | ใช่ | metadata ของ action ที่ค้างอยู่; default `{}` ปกติเป็น `{ "execute": [{ "id": "<user-id>" }, ...] }` ระบุผู้ที่ทำต่อได้ |
| `last_action` | `enum_last_action` | ใช่ | action ล่าสุดที่กระทำกับเอกสาร; default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาของ `last_action` |
| `last_action_by_id` | `String @db.Uuid` | ใช่ | user id ที่กระทำ `last_action` |
| `last_action_by_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อผู้กระทำ |
| `vendor_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_vendor.id` — vendor เดียวของ PO นี้ |
| `vendor_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ vendor |
| `currency_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_currency.id` — สกุลเงินทำรายการของทั้ง PO |
| `currency_code` | `String @db.VarChar` | ใช่ | snapshot รหัสสกุลเงิน |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราแลกเปลี่ยนจากสกุลทำรายการไปสกุลฐาน; default `1` |
| `approval_date` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่ PO ถูกอนุมัติ |
| `email` | `String @db.VarChar` | ใช่ | อีเมลที่ใช้เมื่อส่ง PO ให้ vendor |
| `buyer_id` | `String @db.Uuid` | ใช่ | id ของผู้จัดซื้อ / buyer |
| `buyer_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ buyer |
| `credit_term_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_credit_term.id` |
| `credit_term_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ credit term |
| `credit_term_value` | `Int @db.Integer` | ใช่ | snapshot จำนวนวันของ credit term; default `0` |
| `remarks` | `String @db.VarChar` | ใช่ | หมายเหตุ free-text สำหรับ vendor หรือ audit trail |
| `history` | `Json @db.JsonB` | ใช่ | ประวัติ audit ระดับหัวเอกสาร; default `[]` แต่ละรายการมี `po_status`, `action`, `by`, `at` |
| `total_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | roll-up ของ `order_qty` ระดับบรรทัด (เทียบเท่า base UoM); default `0` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | roll-up ของ `net_amount` ระดับบรรทัด; default `0` |
| `total_tax` | `Decimal @db.Decimal(20, 5)` | ใช่ | roll-up ของ `tax_amount` ระดับบรรทัด; default `0` |
| `total_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | roll-up ของ `total_price` ระดับบรรทัด (net + tax); default `0` |
| `is_active` | `Boolean` | ใช่ | สถานะใช้งานของ PO; default `true` |
| `note` | `String @db.VarChar` | ใช่ | บันทึก free-text บนหัวเอกสาร |
| `info` | `Json @db.JsonB` | ใช่ | extension bag สำหรับฟิลด์เฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | ใช่ | array ของ cost dimension (project, cost-centre, job code ฯลฯ); default `[]` |
| `doc_version` | `Int @db.Integer` | ไม่ | ตัวนับเวอร์ชันสำหรับ optimistic concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | ใช่ | user id ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่อัปเดตล่าสุด; default `now()` |
| `updated_by_id` | `String @db.Uuid` | ใช่ | user id ของผู้อัปเดตล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete; ค่าที่ไม่ใช่ null หมายถึงถูกลบเชิงตรรกะ |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | user id ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `credit_term_id → tb_credit_term.id` (`NoAction`); `currency_id → tb_currency.id` ผ่าน named relation `tb_purchase_order_currency_idTotb_currency` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`) หมายเหตุ: `workflow_id` เก็บเป็น UUID แต่ไม่มี Prisma `@relation` บนโมเดลนี้
**Indexes:** `@@unique([po_no, deleted_at])` ชื่อ `PO_po_no_u`; `@@index([po_no])` ชื่อ `PO_po_no_idx`; `@@index([vendor_id])` ชื่อ `PO_vendor_id_idx`

### 2.2 tb_purchase_order_comment

รายการคอมเมนต์ / activity log ที่ผูกกับหัวเอกสาร PO เช่นเดียวกับ PR ไม่มีตาราง `tb_purchase_order_workflow` แยกต่างหาก — ตารางคอมเมนต์นี้ร่วมกับคอลัมน์ JSON workflow บนหัวเอกสารเป็นบันทึก persistent ของไทม์ไลน์ workflow แต่ละแถวเป็นคอมเมนต์ของผู้ใช้ (`type = user`) หรือเหตุการณ์ระบบ (`type = system`) เช่นการเปลี่ยน stage

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_order_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_purchase_order.id` |
| `type` | `enum_comment_type` | ไม่ | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | ใช่ | user id ของผู้เขียน (null สำหรับเหตุการณ์ `system`) |
| `message` | `String` | ใช่ | เนื้อหาคอมเมนต์ free-text |
| `attachments` | `Json @db.JsonB` | ใช่ | array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_order_id → tb_purchase_order.id` (`NoAction` ทั้ง delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจากคีย์หลัก

### 2.3 tb_purchase_order_detail

บรรทัดรายการของ PO เก็บการอ้างอิง product, ชุด qty / unit แบบคู่ (order UoM และ base UoM — ต่างจาก PR ที่ใช้สามชุด requested/approved/FOC; FOC บน PO เป็นแค่ boolean ต่อบรรทัด), ภาษีและส่วนลด, ยอดบรรทัดทั้งสกุลทำรายการและสกุลฐาน, running received / cancelled qty และประวัติ stage ระดับบรรทัด

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_order_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_purchase_order.id` รองรับบรรทัดร่างที่ยังไม่ผูกหัวเอกสารได้ |
| `description` | `String` | ใช่ | คำอธิบายบรรทัด (มักใช้แทนชื่อสินค้าในกรณี free-text) |
| `comment` | `String @db.VarChar` | ใช่ | คอมเมนต์ระดับบรรทัด |
| `sequence_no` | `Int` | ใช่ | ลำดับบรรทัดใน PO; default `1` |
| `is_active` | `Boolean` | ใช่ | สถานะใช้งานของบรรทัด; default `true` |
| `product_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_product.id` (จำเป็น) |
| `product_code` | `String @db.VarChar` | ใช่ | snapshot โค้ดสินค้า |
| `product_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อสินค้าภาษาท้องถิ่น |
| `product_sku` | `String @db.VarChar` | ใช่ | snapshot SKU |
| `order_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty ในหน่วยสั่งซื้อ; default `0` |
| `order_unit_id` | `String @db.Uuid` | ใช่ | UoM ที่ใช้ตอนสั่ง |
| `order_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | ใช่ | conversion factor จาก order UoM ไป base UoM; default `0` |
| `order_unit_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ order UoM |
| `base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | `order_qty × order_unit_conversion_factor`; default `0` |
| `base_unit_id` | `String @db.Uuid` | ใช่ | inventory base UoM ณ ตอนสั่ง |
| `base_unit_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ base UoM |
| `is_foc` | `Boolean` | ใช่ | `true` เมื่อบรรทัดนี้เป็น free-of-charge; default `false` |
| `tax_profile_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | ใช่ | snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราภาษีที่มีผล; default `0` |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | ยอดภาษีในสกุลทำรายการ; default `0` |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | ยอดภาษีในสกุลฐาน; default `0` |
| `is_tax_adjustment` | `Boolean` | ใช่ | `true` เมื่อผู้ใช้ override ยอดภาษีเอง; default `false` |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | ใช่ | อัตราส่วนลด %; default `0` |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | ยอดส่วนลดในสกุลทำรายการ; default `0` |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | ยอดส่วนลดในสกุลฐาน; default `0` |
| `is_discount_adjustment` | `Boolean` | ใช่ | `true` เมื่อผู้ใช้ override ยอดส่วนลดเอง; default `false` |
| `price` | `Decimal @db.Decimal(20, 5)` | ใช่ | ราคาต่อหน่วยในสกุลทำรายการ; default `0` |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `price × order_qty` (สกุลทำรายการ); default `0` |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | `sub_total_price − discount_amount`; default `0` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `net_amount + tax_amount`; default `0` |
| `base_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `price × exchange_rate`; default `0` |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `base_price × order_qty`; default `0` |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | ใช่ | `base_sub_total_price − base_discount_amount`; default `0` |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | ใช่ | `base_net_amount + base_tax_amount`; default `0` |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | ยอด qty ที่รับสะสม (ในหน่วย order UoM) จาก GRN; default `0` |
| `cancelled_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty ที่ถูกยกเลิก / write-off ออกจากบรรทัดนี้; default `0` |
| `history` | `Json @db.JsonB` | ใช่ | ไทม์ไลน์ stage ระดับบรรทัด (`seq`, `name`, `status`, `to_stage`, `message`, `by_id`, `by_name`, `at_date`); default `[]` |
| `stages_status` | `Json @db.JsonB` | ใช่ | cursor stage ระดับบรรทัด — array ของ `{ seq, name, status }`; default `{}` |
| `current_stage_status` | `String @db.VarChar` | ใช่ | สำเนาทำงานของสถานะ stage ปัจจุบัน |
| `note` | `String @db.VarChar` | ใช่ | บันทึก free-text บนบรรทัด |
| `info` | `Json @db.JsonB` | ใช่ | extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | ใช่ | cost dimension ระดับบรรทัด; default `[]` |
| `doc_version` | `Int @db.Integer` | ไม่ | เวอร์ชันสำหรับ optimistic concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `purchase_order_id → tb_purchase_order.id`; `product_id → tb_product.id` (จำเป็น); `tax_profile_id → tb_tax_profile.id`; named `@relation` ไป `tb_unit` สองชุด — `tb_purchase_order_detail_order_unit_idTotb_unit` สำหรับ `order_unit_id` และ `tb_purchase_order_detail_base_unit_idTotb_unit` สำหรับ `base_unit_id` มี back-relation ไป `tb_good_received_note_detail`, `tb_purchase_order_detail_comment`, และ `tb_purchase_order_detail_tb_purchase_request_detail`
**Indexes:** `@@unique([purchase_order_id, sequence_no, deleted_at])` ชื่อ `PO1_purchase_order_detail_sequence_no_u`; `@@index([purchase_order_id])` ชื่อ `PO1_purchase_order_detail_idx`

### 2.4 tb_purchase_order_detail_comment

ตารางคู่ระดับบรรทัดของ `tb_purchase_order_comment` เก็บคอมเมนต์และเหตุการณ์ระบบที่ผูกกับบรรทัด PO เดียว — ปกติใช้ระหว่างการอนุมัติเพื่อบันทึกการตัดสินใจระดับ stage และระหว่างการส่งของเพื่อบันทึกการสื่อสารกับ vendor ต่อบรรทัด

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `purchase_order_detail_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_purchase_order_detail.id` |
| `type` | `enum_comment_type` | ไม่ | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | ใช่ | user id ของผู้เขียน (null สำหรับเหตุการณ์ `system`) |
| `message` | `String` | ใช่ | เนื้อหาคอมเมนต์ free-text |
| `attachments` | `Json @db.JsonB` | ใช่ | array ของไฟล์แนบ; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_order_detail_id → tb_purchase_order_detail.id` (`NoAction` ทั้ง delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจากคีย์หลัก

### 2.5 tb_purchase_order_detail_tb_purchase_request_detail

ตารางสะพานที่ผูกบรรทัด PO เข้ากับบรรทัด PR ต้นทางหนึ่งหรือหลายรายการ แถวเดียวกันยัง denormalise snapshot ของ qty / unit / location จากฝั่ง PR และเก็บ qty ที่รับและ FOC ต่อบรรทัด PR ที่ถูก allocate ดังนั้นตารางสะพานจึงเป็นทั้งตารางเชื่อมและ cursor สำหรับ "บรรทัด PR นี้ถูกบรรทัด PO นี้ครอบคลุมไปแล้วเท่าไร" ดูฝั่ง PR ได้ที่ [[purchase-request]] § 2

| ฟิลด์ | Prisma Type | ค่าว่างได้ | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | ไม่ | คีย์หลัก |
| `po_detail_id` | `String @db.Uuid` | ไม่ | FK ไป `tb_purchase_order_detail.id` |
| `pr_detail_id` | `String @db.Uuid` | ใช่ | FK ไป `tb_purchase_request_detail.id` เป็น nullable เพื่อให้บรรทัด PO ที่ไม่ได้มาจาก PR (manual PO) ยังเขียนแถว bridge ได้หากต้องการ |
| `pr_detail_order_unit_id` | `String @db.Uuid` | ใช่ | snapshot UoM จากบรรทัด PR ต้นทาง |
| `pr_detail_order_unit_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ UoM ของบรรทัด PR |
| `pr_detail_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty ที่ใช้จากบรรทัด PR (ในหน่วย PR-line UoM); default `0` |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty ที่รับสะสมจากการ allocate นี้; default `0` |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty FOC ที่ allocate จากบรรทัด PR นี้; default `0` |
| `location_id` | `String @db.Uuid` | ใช่ | snapshot คลัง / สถานที่จากบรรทัด PR |
| `location_code` | `String @db.VarChar` | ใช่ | snapshot |
| `location_name` | `String @db.VarChar` | ใช่ | snapshot |
| `delivery_point_id` | `String @db.Uuid` | ใช่ | snapshot จุดส่งจากบรรทัด PR |
| `delivery_point_name` | `String @db.VarChar` | ใช่ | snapshot |
| `pr_detail_base_qty` | `Decimal @db.Decimal(20, 5)` | ใช่ | qty ในหน่วยฐานเทียบเท่าของ `pr_detail_qty`; default `0` |
| `pr_detail_base_unit_id` | `String @db.Uuid` | ใช่ | snapshot base UoM จากบรรทัด PR |
| `pr_detail_base_unit_name` | `String @db.VarChar` | ใช่ | snapshot ชื่อ base UoM |
| `created_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาสร้าง |
| `created_by_id` | `String @db.Uuid` | ใช่ | id ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลาที่อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | ใช่ | id ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | ใช่ | เวลา soft-delete |
| `deleted_by_id` | `String @db.Uuid` | ใช่ | id ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `po_detail_id → tb_purchase_order_detail.id` (`NoAction`); `pr_detail_id → tb_purchase_request_detail.id` (`NoAction`); `delivery_point_id → tb_delivery_point.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`)
**Indexes:** `@@unique([po_detail_id, pr_detail_id, deleted_at])` ชื่อ `PO1_purchase_order_purchase_request_detail_u`; `@@index([po_detail_id, pr_detail_id])` ชื่อ `PO1_purchase_order_purchase_request_detail_idx`; `@@index([pr_detail_id])` ชื่อ `PO1_purchase_request_detail_idx`

## 3. ความสัมพันธ์

```
tb_workflow
    │  (เก็บ workflow_id แต่ไม่มี Prisma @relation บน tb_purchase_order)
    ▼
tb_purchase_order ──1──*──► tb_purchase_order_comment
    │  1
    │
    │ * purchase_order_id
    ▼
tb_purchase_order_detail ──1──*──► tb_purchase_order_detail_comment
    │
    │ FK references (snapshot แบบ denormalise บนแถว)
    ├──► tb_product           (จำเป็น, product_id)
    ├──► tb_tax_profile       (tax_profile_id)
    └──► tb_unit  ×2          (order_unit_id, base_unit_id — named relations)

tb_purchase_order (FK ระดับหัวเอกสาร)
    ├──► tb_vendor             (vendor_id)
    ├──► tb_currency           (currency_id — named relation)
    └──► tb_credit_term        (credit_term_id)

tb_purchase_request_detail ──*──*──► tb_purchase_order_detail
    ผ่าน bridge tb_purchase_order_detail_tb_purchase_request_detail
    (po_detail_id, pr_detail_id) — หลายบรรทัด PR → หนึ่งบรรทัด PO
    (consolidation); หนึ่งบรรทัด PR → หลายบรรทัด PO (partial conversion)
    แถว bridge ยังอ้างอิง tb_location และ tb_delivery_point

tb_purchase_order_detail ──1──*──► tb_good_received_note_detail
    (บรรทัด GRN อ้างกลับมาที่บรรทัด PO ที่ตนเติม;
     "qty คงเหลือ" = order_qty − received_qty − cancelled_qty)
```

หมายเหตุ:

- **หัวเอกสาร → บรรทัด** เป็น 1-to-many `purchase_order_id` ของบรรทัดเป็น nullable เพื่อรองรับบรรทัดร่าง / scratch แต่ application layer บังคับเป็น 1-to-many ในทางปฏิบัติ
- **หัวเอกสาร → คอมเมนต์** และ **บรรทัด → คอมเมนต์** เป็น 1-to-many ทั้งคู่ ตารางคอมเมนต์เป็นบันทึก persistent ของ workflow activity ส่วนคอลัมน์ JSON บนหัวเอกสาร (`workflow_history`, `stages_status`) เป็น cursor inline
- **PR ↔ PO** เป็น many-to-many ผ่าน `tb_purchase_order_detail_tb_purchase_request_detail` เพื่อรองรับ PR consolidation (หลายบรรทัด PR → หนึ่งบรรทัด PO) และ partial conversion (หนึ่งบรรทัด PR → หลายบรรทัด PO) ตาราง bridge ยังเป็น cursor ต่อ allocation สำหรับ qty ที่รับและ FOC
- **PO → GRN** เป็น 1-to-many ผ่าน back-relation `tb_purchase_order_detail.tb_good_received_note_detail` `received_qty` ของบรรทัด PO ถูกอัปเดตเมื่อมีการ post GRN; ถ้า `received_qty < order_qty − cancelled_qty` หมายความว่าบรรทัด PO ยังมีของค้างส่ง
- **กติกา vendor / currency**: vendor, currency, exchange-rate และ credit-term อยู่บนหัวเอกสาร ไม่ใช่บรรทัด ดังนั้นทุกบรรทัดของ PO เดียวกันต้องใช้ vendor และ currency เดียวกัน ซึ่งเป็นเหตุผลที่การแปลง PR เป็น PO ต้องจัดกลุ่ม PR ตาม `(vendor, currency)` ก่อน
- ประกาศ FK `@relation` ทุกตัวใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้น referential integrity ถูกรักษาผ่าน soft-delete (`deleted_at`) ในระดับ application ไม่ใช่ cascade

## 4. Enums

- **`enum_purchase_order_type`**: `manual` (PO ที่ฝั่งจัดซื้อสร้างเองโดยไม่มี PR ต้นทาง), `purchase_request` (PO ที่สร้างจาก PR หนึ่งหรือหลายฉบับผ่าน flow แปลง) ค่านี้ **เป็น default ของ `tb_purchase_order.po_type` ด้วย** — หมายความว่าการสร้างจาก PR เป็น path มาตรฐานของ procure-to-pay และ `manual` เป็น opt-out สำหรับ PO ที่ฝั่งจัดซื้อสร้างเอง enum นี้ใช้ร่วมกันระหว่างเอกสาร PR และ PO เพราะอยู่ใน namespace สคีมา tenant เพียงครั้งเดียว
- **`enum_purchase_order_doc_status`**: enum สถานะเอกสารสำหรับ `tb_purchase_order.po_status`
  - `draft` (`ร่าง`) — สถานะแก้ไขได้เริ่มต้น แก้ PO ได้อิสระ ยังไม่ผูกพันกับ vendor
  - `in_progress` (`กำลังดำเนินการ`) — ส่งและกำลังวิ่งผ่าน approval chain
  - `voided` (`โมฆะ`) — ถูก void โดยฝ่ายบริหารหลังส่ง; PO ถูกยกเลิกโดยไม่มีการเติมของ
  - `sent` — PO ส่งให้ vendor แล้ว รอ GRN แรก
  - `partial` — มี GRN อย่างน้อยหนึ่งใบ post แล้ว แต่ `received_qty < order_qty − cancelled_qty` ในบรรทัดหนึ่งหรือมากกว่า; เติมของบางส่วน
  - `closed` (Prisma หมายเหตุ "closed หยุดหาไม่เจอ") — ปิด PO ก่อนเติมของครบ ปกติเป็นเพราะ vendor ไม่สามารถส่ง qty ที่เหลือได้; qty ที่เหลือถือเป็นการยกเลิก
  - `completed` (หมายเหตุ "รับครบผ่าน receiving") — ทุกบรรทัดรับครบผ่าน GRN; PO ปิดตามปกติ
- **`enum_comment_type`** (ใช้ร่วมกับ PR): `user` (คอมเมนต์ที่เขียนโดยมนุษย์), `system` (รายการ activity log ที่ workflow engine สร้างอัตโนมัติ) ใช้ทั้ง `tb_purchase_order_comment.type` และ `tb_purchase_order_detail_comment.type`
- **`enum_last_action`** (ใช้ร่วมกับ PR): `submitted`, `approved`, `reviewed`, `rejected` — ใช้โดย `tb_purchase_order.last_action` เพื่อบันทึก action ล่าสุดของ workflow

## 5. Divergences from carmen/docs

เอกสารต้นทาง `purchase-order-module.md` อธิบาย data dictionary ระดับสูง (โครงร่างตาราง `purchase_orders` / `purchase_order_items` แบบบางๆ) และไดอะแกรม state machine ไม่ใช่เอนทิตี Prisma รายการด้านล่างจับความแตกต่างที่เอกสาร downstream ต้องสมานให้ตรง

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | ค่าสถานะ PO | State diagram ใช้ `Draft → Sent → Partial / FullyReceived → Closed` พร้อมแขนง `Voided` และ `Deleted` | `enum_purchase_order_doc_status { draft, in_progress, voided, sent, partial, closed, completed }` — เพิ่ม `in_progress` (สถานะระหว่าง approval chain ที่ state diagram ไม่มี) และใช้ `completed` แทน `FullyReceived` | ถือ Prisma เป็น canonical อัปเดต state diagram ให้แทรก `in_progress` ระหว่าง `draft` และ `sent` และเปลี่ยน `FullyReceived` → `completed` ส่วน `Deleted` ใน diagram คือ flag `deleted_at` (soft-delete) ไม่ใช่ค่าสถานะ |
| 2 | คอลัมน์เลขที่อ้างอิง | `purchase_orders.number VARCHAR(20)` | `tb_purchase_order.po_no VARCHAR` (ไม่ประกาศความยาวสูงสุด) | เปลี่ยน `number` → `po_no` ใน data dictionary ของ carmen/docs และถอนข้อความที่อ้าง 20 ตัวอักษร |
| 3 | Data dictionary ของหัว PO | ระบุเพียง `id, number, vendor_id, order_date, status, currency_code, exchange_rate, total_amount, created_by` (8 คอลัมน์) | `tb_purchase_order` มีประมาณ 45 คอลัมน์ รวมถึง JSON ของ workflow, snapshot credit term, buyer, history, total หลายตัว (`total_qty`, `total_price`, `total_tax`, `total_amount`), `is_active`, `info`, `dimension`, `doc_version` และชุด audit ครบถ้วน | data dictionary ของ carmen/docs เป็นเชิงตัวอย่างเท่านั้น อย่าถือเป็น spec ที่ครบฟิลด์ ให้อ้างอิง Section 2.1 ของหน้านี้แทน |
| 4 | Data dictionary ของบรรทัด PO | ระบุ `id, purchase_order_id, item_id, ordered_quantity, unit_price, total_amount, pr_item_id` (7 คอลัมน์) | `tb_purchase_order_detail` มีประมาณ 50 คอลัมน์ รวมคู่ UoM `order_*` / `base_*` แยกกัน, boolean FOC, คอลัมน์ภาษีและส่วนลดครบ, ยอดรวมในสกุลทำรายการและสกุลฐาน, `received_qty`, `cancelled_qty`, JSON ของ workflow ระดับบรรทัด นอกจากนี้: **ไม่มี** คอลัมน์ `pr_item_id` บนบรรทัด — การเชื่อม PR อยู่ที่ตารางสะพาน `tb_purchase_order_detail_tb_purchase_request_detail` | ถอน `pr_item_id` จากที่ carmen/docs อ้าง และระบุตารางสะพานเป็นช่องทาง canonical ของการเชื่อม PR ให้อ้างอิง Section 2.3 / 2.5 ของหน้านี้ |
| 5 | กลไก traceability PR→PO | "Each PO item maintains references to its originating PR" (สื่อว่ามีคอลัมน์บนบรรทัด PO) | การเชื่อมเป็น many-to-many ผ่าน bridge (`tb_purchase_order_detail_tb_purchase_request_detail`) ไม่ใช่ FK เดี่ยวบนบรรทัด ซึ่งจำเป็นเพื่อรองรับ consolidation (หลาย PR → หนึ่ง PO) และ partial conversion (หนึ่ง PR → หลาย PO) | อัปเดตข้อความ carmen/docs ให้พูดถึง bridge; แบบ single-FK จะรองรับพฤติกรรม vendor+currency grouping ที่เอกสารระบุไม่ได้ |
| 6 | ชื่อฟิลด์สถานะ | `purchase_orders.status` | `tb_purchase_order.po_status` (ชื่อคอลัมน์คือ `po_status` ไม่ใช่ `status`) | เปลี่ยนชื่อใน data dictionary ของ carmen/docs |
| 7 | รูปแบบเลขที่อ้างอิง | carmen/docs ไม่ระบุ | `po_no` เป็น `VarChar` โดยไม่มี constraint รูปแบบที่ระดับ DB; รูปแบบบังคับใช้ที่ application | ระบุใน carmen/docs ว่ารูปแบบเป็น application policy ไม่ใช่ schema-enforced — สอดคล้องกับ PR |

## 6. References

- **Primary (source of truth):** Prisma schemas ตามที่ระบุใน callout ส่วนหัว — โดยเฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (โมเดล PO และ enum ทั้งหมด) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจแล้วว่าไม่มีโมเดล PO)
- **Secondary (concept cross-check):** `../carmen/docs/purchase-order-management/purchase-order-module.md` — เอกสารวิเคราะห์ธุรกิจระดับสูง; ความแตกต่างถูกจับใน Section 5
- **Sibling reference:** `en/purchase-request/01-data-model.md` — อธิบายฝั่ง PR ของ bridge PR↔PO; ไม่ต้องทำซ้ำในหน้านี้
- โมดูลที่เกี่ยวข้อง: [[purchase-request]] (ต้นทาง), [[good-receive-note]] (ปลายทางผ่าน `received_qty`), [[product]] (อ้างอิงสินค้าระดับบรรทัด), [[vendor-pricelist]] (snapshot ราคา ณ ตอนแปลง PR → PO), [[inventory]] (บริบท on-hand)
