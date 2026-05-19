---
title: ใบสั่งซื้อ (Purchase Order) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum สำหรับโมดูล purchase-order
published: true
date: 2026-05-20T00:00:00.000Z
tags: purchase-order, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — Data Model

> **At a Glance**
> **ตาราง:** `tb_purchase_order` &nbsp;·&nbsp; `tb_purchase_order_detail` &nbsp;·&nbsp; `tb_purchase_order_comment` &nbsp;·&nbsp; `tb_purchase_order_detail_comment` &nbsp;·&nbsp; `tb_purchase_order_detail_tb_purchase_request_detail` (bridge PR↔PO)
> **กลุ่มผู้ใช้:** Developer / Auditor (ใช้อ้างอิงสำหรับ dev)
> **FK สำคัญ:** detail `→ tb_product` / `tb_tax_profile` / `tb_unit` ×2 (order + base); header `→ tb_vendor` / `tb_currency` / `tb_credit_term`; bridge `→ tb_purchase_request_detail` (many-to-many รองรับการรวม PR และการแปลงบางส่วน); back-relation จาก `tb_good_received_note_detail` (GRN ปลายน้ำ)
> **รูปแบบ audit:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; counter ต่อบรรทัด `received_qty` / `cancelled_qty`; snapshot workflow บน header JSON

> **แหล่งอ้างอิง:** Prisma schema ฝั่ง backend อ่านที่นี่ก่อนเสมอเมื่อเขียนหรือแก้ไขหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ภายในแต่ละ package เป็นสำเนา auto-generate ไม่ใช่แหล่งทางการ

## 1. ภาพรวม

โมดูล purchase-order เป็นเจ้าของห้าเอนทิตีใน tenant schema: ส่วนหัวเอกสาร PO (`tb_purchase_order`), line item ของมัน (`tb_purchase_order_detail`), comment สำหรับ workflow / activity-log ทั้งระดับ header และระดับบรรทัด (`tb_purchase_order_comment`, `tb_purchase_order_detail_comment`), และตาราง bridge (`tb_purchase_order_detail_tb_purchase_request_detail`) ที่ลิงก์บรรทัด PO กลับไปยังบรรทัด PR ต้นทางหนึ่งหรือมากกว่าหนึ่งบรรทัด เช่นเดียวกับ PR การติดตาม workflow stage ไม่ได้อยู่ในตารางเฉพาะ — มันเก็บอยู่ในส่วนหัวเป็น JSON columns (`workflow_history`, `workflow_current_stage`, `stages_status`) บวกกับ foreign key เข้าไปยัง config `tb_workflow` ที่ใช้ร่วมกัน ในขณะที่ timeline ของเหตุการณ์ stage-transition ที่ persisted ก็ถูก capture ผ่าน comment table

PO อยู่ **ปลายน้ำของ [purchase-request](/th/inventory/purchase-request)** และ **ต้นน้ำของ [good-receive-note](/th/inventory/good-receive-note)** ในห่วงโซ่ procure-to-pay ลิงก์ PR-to-PO ทำผ่านตาราง bridge ที่กล่าวข้างต้น; bridge เดียวกันนี้ capture ปริมาณที่รับและ FOC ต่อ PR-line รองรับทั้งการรวม PR (หลาย PR lines → หนึ่ง PO line) และการแปลงบางส่วน (หนึ่ง PR line → หลาย PO lines) บรรทัด PO มี column `received_qty` และ `cancelled_qty` แบบ running เพื่อให้ "pending qty" ที่ใช้ได้สำหรับ GRN คือ `order_qty − received_qty − cancelled_qty`; ความสัมพันธ์จาก PO detail ไปยัง GRN detail (`tb_good_received_note_detail`) คือสิ่งที่ปิดวงจร แถวของ PO detail ยังอ้างอิงถึง [product](/th/inventory/product), `tb_tax_profile`, และ `tb_unit` (สองครั้ง — สำหรับ order UoM และ base UoM), และ header อ้างอิง `tb_vendor`, `tb_currency`, และ `tb_credit_term` เอนทิตี PO ทั้งหมดอยู่ใน tenant Prisma schema; platform schema ไม่มี model purchase-order

ส่วนหัวบรรจุ context ของผู้ขาย สกุลเงิน อัตราแลกเปลี่ยน และ credit-term ครั้งเดียวสำหรับทั้ง PO — โดยการออกแบบ ทุกบรรทัดบน PO หนึ่งใบใช้ผู้ขายและสกุลเงินเดียวกัน ซึ่งเป็นเหตุผลที่ flow การแปลง PR-to-PO ต้อง group PR ที่เลือกด้วย `(vendor, currency)` ก่อน fan-out ค่า default ของ `tb_purchase_order.po_type` คือ `purchase_request` ซึ่งทำให้การสร้างผ่าน PR-sourced เป็นเส้นทางมาตรฐาน; `manual` เป็นทางเลือกสำหรับ PO ที่สร้างโดย procurement เท่านั้นโดยไม่มี PR ต้นน้ำ

## 2. เอนทิตี

### 2.1 tb_purchase_order

ส่วนหัวเอกสาร PO บรรจุหมายเลขอ้างอิง context ของผู้ขาย / สกุลเงิน / credit-term, snapshot ของ workflow, ยอดรวม และ column audit ส่วนหัวหนึ่งมีหลาย detail row และหลาย comment

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generate ด้วย `gen_random_uuid()` |
| `po_no` | `String @db.VarChar` | No | หมายเลขอ้างอิง PO ที่อ่านง่ายสำหรับมนุษย์ |
| `po_status` | `enum_purchase_order_doc_status` | Yes | สถานะเอกสาร; default `draft` |
| `po_type` | `enum_purchase_order_type` | No | โหมดการสร้าง PO; default `purchase_request` (PR-sourced เป็นเส้นทางมาตรฐาน) |
| `description` | `String` | Yes | คำอธิบาย / เหตุผลที่ใส่บน header |
| `order_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่สั่งซื้อที่กำหนดบน header |
| `delivery_date` | `DateTime @db.Timestamptz(6)` | Yes | วันส่งของที่ต้องการระดับ header |
| `workflow_id` | `String @db.Uuid` | Yes | FK อ้างอิงไปยัง `tb_workflow` row (ไม่มี Prisma `@relation` ประกาศไว้บน model นี้ — selection resolve ที่ application) |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ workflow |
| `workflow_history` | `Json @db.JsonB` | Yes | Timeline ของ stage-transition แบบ append-only; default `[]` แต่ละ entry มี `stage`, `action`, `message`, `by`, `at` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Slug ของ stage ที่กำลังถือ PO อยู่ |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Slug ของ stage ที่เพิ่งปล่อย PO |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Slug ของ stage ถัดไปในห่วงโซ่ |
| `user_action` | `Json @db.JsonB` | Yes | Metadata ของ pending-action, default `{}` โดยทั่วไป `{ "execute": [{ "id": "<user-id>" }, ...] }` ระบุผู้ที่ดำเนินการต่อได้ |
| `last_action` | `enum_last_action` | Yes | Action ล่าสุดที่ดำเนินการกับเอกสาร; default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ `last_action` |
| `last_action_by_id` | `String @db.Uuid` | Yes | User id ที่ดำเนินการ `last_action` |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้ดำเนินการ |
| `vendor_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_vendor.id` — ผู้ขายรายเดียวของ PO |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้ขาย |
| `currency_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_currency.id` — สกุลเงินที่ใช้บันทึก transaction สำหรับ PO ทั้งใบ |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสกุลเงิน |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราแลกเปลี่ยน transaction-to-base; default `1` |
| `approval_date` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp เมื่อ PO ถูกอนุมัติ |
| `email` | `String @db.VarChar` | Yes | อีเมลที่ใช้เมื่อส่ง PO ให้ผู้ขาย |
| `buyer_id` | `String @db.Uuid` | Yes | ID ของ buyer / procurement officer |
| `buyer_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อแสดงผลของ buyer |
| `credit_term_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_credit_term.id` |
| `credit_term_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ credit term |
| `credit_term_value` | `Int @db.Integer` | Yes | Snapshot ของ credit term เป็นวัน; default `0` |
| `remarks` | `String @db.VarChar` | Yes | หมายเหตุ free-text สำหรับผู้ขายหรือ audit trail |
| `history` | `Json @db.JsonB` | Yes | ประวัติ audit ระดับ header; default `[]` แต่ละ entry มี `po_status`, `action`, `by`, `at` |
| `total_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up ของ `order_qty` บรรทัด (เทียบเท่า base-UoM); default `0` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up ของ `net_amount` บรรทัด; default `0` |
| `total_tax` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up ของ `tax_amount` บรรทัด; default `0` |
| `total_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Roll-up ของ `total_price` บรรทัด (net + tax); default `0` |
| `is_active` | `Boolean` | Yes | PO ยัง active หรือไม่; default `true` |
| `note` | `String @db.VarChar` | Yes | หมายเหตุ free-text ที่แนบกับ header |
| `info` | `Json @db.JsonB` | Yes | Extension bag สำหรับ attribute ของ header เฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | Array ของ cost-dimension (project, cost-centre, job code, ฯลฯ); default `[]` |
| `doc_version` | `Int @db.Integer` | No | Counter version แบบ optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | User id ที่สร้าง row |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด; default `now()` |
| `updated_by_id` | `String @db.Uuid` | Yes | User id ที่ update row ล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; non-null หมายถึง logically deleted |
| `deleted_by_id` | `String @db.Uuid` | Yes | User id ที่ soft-delete row |

**Constraints:** `@id` บน `id` FKs: `credit_term_id → tb_credit_term.id` (`NoAction`); `currency_id → tb_currency.id` ผ่าน named relation `tb_purchase_order_currency_idTotb_currency` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`) หมายเหตุ: `workflow_id` เก็บเป็น UUID แต่ไม่มี Prisma `@relation` บน model นี้
**Indexes:** `@@unique([po_no, deleted_at])` ชื่อ `PO_po_no_u`; `@@index([po_no])` ชื่อ `PO_po_no_idx`; `@@index([vendor_id])` ชื่อ `PO_vendor_id_idx`

### 2.2 tb_purchase_order_comment

รายการ workflow / activity-log ที่แนบกับ header PO เช่นเดียวกับ PR ไม่มีตาราง `tb_purchase_order_workflow` เฉพาะ — comment table นี้ บวกกับ JSON workflow columns บน header คือบันทึก persistent ของ timeline workflow แต่ละ row เป็นไม่ user comment (`type = user`) ก็เป็น system event (`type = system`) เช่น stage transition

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_order_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_order.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | User id ผู้เขียน (null สำหรับ entry `system`) |
| `message` | `String` | Yes | เนื้อหา comment free-text |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ผู้ update |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_order_id → tb_purchase_order.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 2.3 tb_purchase_order_detail

Line item ของ PO บรรจุ product reference, คู่ order-qty และ base-qty (qty/UoM เดี่ยวต่างจาก PR ที่บรรจุ triple ของ requested/approved/FOC — FOC บน PO เป็น boolean ต่อบรรทัด), tax และ discount, ยอดรวมบรรทัดในสกุลเงิน transaction และ base, ปริมาณ received / cancelled แบบ running และประวัติ workflow stage ต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_order_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_purchase_order.id` Nullable เพื่อรองรับ draft lines ที่ยังไม่แนบกับ header |
| `description` | `String` | Yes | คำอธิบายบรรทัด (มัก override ชื่อสินค้าสำหรับ free-text lines) |
| `comment` | `String @db.VarChar` | Yes | Comment ระดับบรรทัด |
| `sequence_no` | `Int` | Yes | การจัดลำดับบรรทัดภายใน PO; default `1` |
| `is_active` | `Boolean` | Yes | บรรทัด active หรือไม่; default `true` |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` Required |
| `product_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้าเฉพาะถิ่น |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `order_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณใน order UoM; default `0` |
| `order_unit_id` | `String @db.Uuid` | Yes | UoM ที่ใช้ตอนสั่ง |
| `order_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | Conversion factor จาก order UoM ไปยัง base UoM; default `0` |
| `order_unit_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ order UoM |
| `base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `order_qty × order_unit_conversion_factor`; default `0` |
| `base_unit_id` | `String @db.Uuid` | Yes | Inventory base UoM ตอนสั่ง |
| `base_unit_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ base UoM |
| `is_foc` | `Boolean` | Yes | `true` เมื่อบรรทัด free-of-charge; default `false` |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | Yes | Snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราภาษี effective; default `0` |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีในสกุลเงิน transaction; default `0` |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีในสกุลเงิน base; default `0` |
| `is_tax_adjustment` | `Boolean` | Yes | `true` เมื่อผู้ใช้ override จำนวนภาษีด้วยมือ; default `false` |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราส่วนลด %; default `0` |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดในสกุลเงิน transaction; default `0` |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดในสกุลเงิน base; default `0` |
| `is_discount_adjustment` | `Boolean` | Yes | `true` เมื่อผู้ใช้ override ส่วนลดด้วยมือ; default `false` |
| `price` | `Decimal @db.Decimal(20, 5)` | Yes | ราคาต่อหน่วยในสกุลเงิน transaction; default `0` |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × order_qty` (สกุลเงิน transaction); default `0` |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `sub_total_price − discount_amount`; default `0` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `net_amount + tax_amount`; default `0` |
| `base_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × exchange_rate`; default `0` |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_price × order_qty`; default `0` |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `base_sub_total_price − base_discount_amount`; default `0` |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_net_amount + base_tax_amount`; default `0` |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ยอดสะสมของปริมาณที่รับ (ใน order UoM) จาก GRN; default `0` |
| `cancelled_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณที่ยกเลิก / write off จากบรรทัดนี้; default `0` |
| `history` | `Json @db.JsonB` | Yes | Timeline stage ต่อบรรทัด (`seq`, `name`, `status`, `to_stage`, `message`, `by_id`, `by_name`, `at_date`); default `[]` |
| `stages_status` | `Json @db.JsonB` | Yes | Stage cursor ต่อบรรทัด — array ของ `{ seq, name, status }`; default `{}` |
| `current_stage_status` | `String @db.VarChar` | Yes | Working copy ของ status stage ปัจจุบัน Prisma schema ประกาศ `enum_stage_action { submit, approve, reject, review, pending }` (pass enum-cleanup พฤษภาคม 2026) ที่เจตนาใช้ type คอลัมน์นี้; ตัวคอลัมน์ยังเป็น `String?` จนกว่า migration ที่วางแผนไว้จะ validate ค่าประวัติและ retype ถือว่าค่านอก `enum_stage_action` เป็นข้อมูล legacy ที่ migration จะ normalise |
| `note` | `String @db.VarChar` | Yes | หมายเหตุ free-text แนบกับบรรทัด |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | Cost dimensions ต่อบรรทัด; default `[]` |
| `doc_version` | `Int @db.Integer` | No | Version แบบ optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ผู้ update |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ผู้ soft-delete |

**Constraints:** `@id` บน `id` FKs: `purchase_order_id → tb_purchase_order.id`; `product_id → tb_product.id` (required); `tax_profile_id → tb_tax_profile.id`; named `@relation` FKs สองตัวเข้า `tb_unit` — `tb_purchase_order_detail_order_unit_idTotb_unit` สำหรับ `order_unit_id` และ `tb_purchase_order_detail_base_unit_idTotb_unit` สำหรับ `base_unit_id` Back-relations ไปยัง `tb_good_received_note_detail`, `tb_purchase_order_detail_comment`, และ `tb_purchase_order_detail_tb_purchase_request_detail`
**Indexes:** `@@unique([purchase_order_id, sequence_no, deleted_at])` ชื่อ `PO1_purchase_order_detail_sequence_no_u`; `@@index([purchase_order_id])` ชื่อ `PO1_purchase_order_detail_idx`

### 2.4 tb_purchase_order_detail_comment

คู่ระดับบรรทัดของ `tb_purchase_order_comment` Capture comment และ system event ที่แนบกับ PO line เดียว — ใช้ระหว่าง approval เพื่อบันทึกการตัดสินใจระดับ stage และระหว่างการ fulfilment เพื่อ log การแลกเปลี่ยนกับผู้ขายต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_order_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_order_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | User id ผู้เขียน (null สำหรับ entry `system`) |
| `message` | `String` | Yes | เนื้อหา comment free-text |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ attachments; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ผู้ update |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_order_detail_id → tb_purchase_order_detail.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 2.5 tb_purchase_order_detail_tb_purchase_request_detail

ตาราง bridge ที่ลิงก์ PO detail row กับ PR detail rows ต้นทางหนึ่งหรือมากกว่าหนึ่ง row เดียวกันยัง denormalise PR-side qty / unit / location snapshot และ track ปริมาณที่รับและ FOC ต่อ PR-line ดังนั้น bridge เป็นทั้งตาราง linkage และ cursor สำหรับ "ปริมาณ PR line นี้ถูกครอบคลุมโดย PO line นี้แล้วเท่าไหร่" ดู [purchase-request](/th/inventory/purchase-request) § 2 สำหรับมุมมองฝั่ง PR

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `po_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_order_detail.id` |
| `pr_detail_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_purchase_request_detail.id` Nullable เพื่ออนุญาตให้ PO lines ที่ไม่ได้มาจาก PR (manual POs) ยังเขียน bridge row ได้หากจำเป็น |
| `pr_detail_order_unit_id` | `String @db.Uuid` | Yes | Snapshot ของ UoM จาก PR line ต้นทาง |
| `pr_detail_order_unit_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ UoM ของ PR-line |
| `pr_detail_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณที่บริโภคจาก PR line (ใน UoM ของ PR-line); default `0` |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณที่รับแล้วเทียบกับ allocation นี้ของ PR-line; default `0` |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ free-of-charge ที่จัดสรรจาก PR line นี้; default `0` |
| `location_id` | `String @db.Uuid` | Yes | Snapshot store / location จาก PR line |
| `location_code` | `String @db.VarChar` | Yes | Snapshot |
| `location_name` | `String @db.VarChar` | Yes | Snapshot |
| `delivery_point_id` | `String @db.Uuid` | Yes | Snapshot จุดส่งของจาก PR line |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot |
| `pr_detail_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | เทียบเท่า base-UoM ของ `pr_detail_qty`; default `0` |
| `pr_detail_base_unit_id` | `String @db.Uuid` | Yes | Snapshot base UoM จาก PR line |
| `pr_detail_base_unit_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ base UoM |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ผู้ update |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ผู้ soft-delete |

**Constraints:** `@id` บน `id` FKs: `po_detail_id → tb_purchase_order_detail.id` (`NoAction`); `pr_detail_id → tb_purchase_request_detail.id` (`NoAction`); `delivery_point_id → tb_delivery_point.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`)
**Indexes:** `@@unique([po_detail_id, pr_detail_id, deleted_at])` ชื่อ `PO1_purchase_order_purchase_request_detail_u`; `@@index([po_detail_id, pr_detail_id])` ชื่อ `PO1_purchase_order_purchase_request_detail_idx`; `@@index([pr_detail_id])` ชื่อ `PO1_purchase_request_detail_idx`

## 3. ความสัมพันธ์

```
tb_workflow
    │  (workflow_id เก็บไว้แต่ไม่มี Prisma @relation บน tb_purchase_order)
    ▼
tb_purchase_order ──1──*──► tb_purchase_order_comment
    │  1
    │
    │ * purchase_order_id
    ▼
tb_purchase_order_detail ──1──*──► tb_purchase_order_detail_comment
    │
    │ FK references (denormalised snapshots บน row)
    ├──► tb_product           (required, product_id)
    ├──► tb_tax_profile       (tax_profile_id)
    └──► tb_unit  ×2          (order_unit_id, base_unit_id — named relations)

tb_purchase_order (FK ระดับ header)
    ├──► tb_vendor             (vendor_id)
    ├──► tb_currency           (currency_id — named relation)
    └──► tb_credit_term        (credit_term_id)

tb_purchase_request_detail ──*──*──► tb_purchase_order_detail
    ผ่าน bridge tb_purchase_order_detail_tb_purchase_request_detail
    (po_detail_id, pr_detail_id) — หลาย PR lines → หนึ่ง PO line
    (รวม consolidation); หนึ่ง PR line → หลาย PO lines (partial conversion)
    Bridge row ยังอ้างอิง tb_location และ tb_delivery_point

tb_purchase_order_detail ──1──*──► tb_good_received_note_detail
    (GRN detail back-reference ไปยัง PO line ที่ fulfil;
     "pending qty" = order_qty − received_qty − cancelled_qty)
```

หมายเหตุ:

- **Header → detail** เป็น 1-to-many `purchase_order_id` ของ detail nullable ซึ่งอนุญาตให้มี orphan / scratch lines แต่ถูกบังคับเป็น 1-to-many ในทางปฏิบัติโดย application layer
- **Header → comment** และ **detail → comment** ทั้งคู่เป็น 1-to-many ตาราง comment เป็นบันทึก persistent ของกิจกรรม workflow; JSON columns บน header (`workflow_history`, `stages_status`) คือ in-place cursor
- **PR ↔ PO** เป็น many-to-many ผ่าน `tb_purchase_order_detail_tb_purchase_request_detail` เพื่อรองรับ PR consolidation (PR lines หลาย → PO line หนึ่ง) และ partial conversion (PR line หนึ่ง → PO lines หลาย) Bridge ยังเป็น cursor ต่อ allocation สำหรับ received และ FOC qty
- **PO → GRN** เป็น 1-to-many ผ่าน `tb_purchase_order_detail.tb_good_received_note_detail` (back-relation) `received_qty` ของ PO line update โดยการ post GRN; `received_qty < order_qty − cancelled_qty` หมายถึง PO line ยังมี fulfilment ค้างอยู่
- **Vendor / currency invariant**: vendor, currency, exchange-rate และ credit-term อยู่บน header ไม่ใช่บรรทัด นี่หมายความว่าทุก PO line บน PO หนึ่ง ๆ ใช้ vendor และ currency เดียวกัน ซึ่งเป็นเหตุผลที่การแปลง PR-to-PO ต้อง pre-group PRs ด้วย `(vendor, currency)`
- ประกาศ FK `@relation` ทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้น referential integrity จึงรักษาโดย soft-delete ระดับ application (`deleted_at`) แทน cascade

## 4. Enums

- **`enum_purchase_order_type`**: `manual` (PO ที่สร้างโดย procurement โดยตรงโดยไม่มี PR ต้นน้ำ), `purchase_request` (PO ที่มีต้นทางจาก PR หนึ่งหรือมากกว่าหนึ่งใบผ่าน flow การแปลง) นี่ **ยังเป็นค่า default บน `tb_purchase_order.po_type`** — หมายถึง PR-sourced เป็นเส้นทาง procure-to-pay มาตรฐาน และ `manual` คือการ opt-out ที่ชัดเจนสำหรับ PO ที่ทำโดย procurement เท่านั้น Enum เดียวกันใช้ร่วมกันระหว่าง PR และ PO documentation เพราะมันอยู่ใน namespace ของ tenant schema เพียงครั้งเดียว
- **`enum_purchase_order_doc_status`**: enum สถานะเอกสารสำหรับ `tb_purchase_order.po_status`
  - `draft` (`ร่าง`) — สถานะแก้ไขได้เริ่มต้น; PO สามารถแก้ไขได้อย่างอิสระ ไม่มี commitment กับผู้ขาย
  - `in_progress` (`กำลังดำเนินการ`) — submit แล้วและกำลังเดินผ่านห่วงโซ่ approval
  - `voided` (`โมฆะ`) — voided เชิงบริหารหลัง submission; PO ถูก terminate โดยไม่มี fulfilment
  - `sent` — PO ถูกส่งให้ผู้ขายแล้ว; รอ GRN ครั้งแรก
  - `partial` — อย่างน้อย GRN หนึ่งใบ post แล้วแต่ `received_qty < order_qty − cancelled_qty` บนอย่างน้อยหนึ่งบรรทัด; partial fulfilment
  - `closed` (annotated ใน Prisma ว่า "closed หยุดหาไม่เจอ") — PO closed ก่อน fulfilment เต็มที่ มักเพราะผู้ขายไม่สามารถจัดหา qty ที่ค้างอยู่; qty ที่เหลือถูกถือเป็น cancelled
  - `completed` (annotated ว่า "รับครบผ่าน receiving") — ทุกบรรทัดรับครบผ่าน GRN; PO ปิดปกติ
- **`enum_comment_type`** (ใช้ร่วมกับ PR): `user` (comment ที่มนุษย์เขียน), `system` (entry activity-log ที่ auto-generate โดย workflow engine) ใช้โดยทั้ง `tb_purchase_order_comment.type` และ `tb_purchase_order_detail_comment.type`
- **`enum_last_action`** (ใช้ร่วมกับ PR): `submitted`, `approved`, `reviewed`, `rejected` — ใช้โดย `tb_purchase_order.last_action` เพื่อ capture action workflow ล่าสุด

## 5. ความแตกต่างจาก carmen/docs

`purchase-order-module.md` แบบเดิมอธิบาย data dictionary ระดับสูง (โครง table แบบบาง `purchase_orders` / `purchase_order_items`) และ state-machine diagram ไม่ใช่ Prisma entities รายการด้านล่าง capture ความแตกต่างที่สำคัญที่ documentation ปลายน้ำต้อง reconcile

| # | Item | carmen/docs บอกว่า | Prisma มี | Action |
|---|------|------------------|------------|--------|
| 1 | ค่า PO status | State diagram ใช้ `Draft → Sent → Partial / FullyReceived → Closed` บวกกับ branch `Voided` และ `Deleted` | `enum_purchase_order_doc_status { draft, in_progress, voided, sent, partial, closed, completed }` — เพิ่ม `in_progress` (state ห่วงโซ่ approval ไม่มีใน state diagram) และใช้ `completed` แทน `FullyReceived` | ถือ Prisma เป็น canonical update state diagram ให้แทรก `in_progress` ระหว่าง `draft` และ `sent` และเปลี่ยนชื่อ `FullyReceived` → `completed` `Deleted` ใน diagram คือ soft-delete flag (`deleted_at`) ไม่ใช่ค่า status |
| 2 | Column หมายเลขอ้างอิง | `purchase_orders.number VARCHAR(20)` | `tb_purchase_order.po_no VARCHAR` (ไม่มี cap ความยาวประกาศ) | เปลี่ยนชื่อ `number` → `po_no` ใน data dictionary ของ carmen/docs ตัด claim 20-char cap |
| 3 | Data dictionary ของ PO header | List `id, number, vendor_id, order_date, status, currency_code, exchange_rate, total_amount, created_by` เท่านั้น (8 columns) | `tb_purchase_order` มี ~45 columns รวมถึง workflow JSON, credit-term snapshot, buyer, history, ยอดรวมหลายตัว (`total_qty`, `total_price`, `total_tax`, `total_amount`), `is_active`, `info`, `dimension`, `doc_version` และชุด audit ครบ | Dictionary ของ carmen/docs เป็นเพียงตัวอย่าง อย่าถือเป็น spec field-complete cross-reference Section 2.1 ของหน้านี้แทน |
| 4 | Data dictionary ของ PO line | List `id, purchase_order_id, item_id, ordered_quantity, unit_price, total_amount, pr_item_id` (7 columns) | `tb_purchase_order_detail` มี ~50 columns รวมถึงคู่ `order_*` / `base_*` UoM แยก, FOC boolean, ภาษีและส่วนลดเต็ม columns, ยอดรวมสกุลเงิน transaction และ base, `received_qty`, `cancelled_qty`, workflow JSON ต่อบรรทัด นอกจากนี้: ไม่มี `pr_item_id` บน detail row — PR linkage อยู่บนตาราง bridge `tb_purchase_order_detail_tb_purchase_request_detail` | ตัด `pr_item_id` จาก claim ของ carmen/docs document ตาราง bridge เป็น PR linkage แบบ canonical Cross-reference Section 2.3 / 2.5 ของหน้านี้ |
| 5 | กลไก PR→PO traceability | "Each PO item maintains references to its originating PR" (implies column บน PO line) | Linkage คือ many-to-many bridge (`tb_purchase_order_detail_tb_purchase_request_detail`) ไม่ใช่ column FK เดียวบน PO line ที่จำเป็นเพื่อรองรับ consolidation (PR หลาย → PO หนึ่ง) และ partial conversion (PR หนึ่ง → PO หลาย) | Update prose ของ carmen/docs ให้อธิบาย bridge; model FK เดียวไม่รองรับพฤติกรรม vendor+currency grouping ที่ documented |
| 6 | ชื่อฟิลด์ status | `purchase_orders.status` | `tb_purchase_order.po_status` (column คือ `po_status` ไม่ใช่ `status`) | เปลี่ยนชื่อใน data dictionary ของ carmen/docs |
| 7 | Format หมายเลขอ้างอิง | ไม่ระบุใน carmen/docs | `po_no` เป็น `VarChar` โดยไม่มี constraint รูปแบบที่ระดับ DB; รูปแบบถูกบังคับโดย application | หมายเหตุใน carmen/docs ว่า format เป็นนโยบาย application ไม่ใช่ schema-enforced — ขนานกับ PR |

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** Prisma schemas ที่ list ใน callout ของ header — โดยเฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (ทุก PO models และ enum ทั้งสอง) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจสอบแล้วว่าไม่มี PO models)
- **Secondary (cross-check แนวคิด):** `../carmen/docs/purchase-order-management/purchase-order-module.md` — เอกสาร business-analysis ระดับสูง; ความแตกต่าง capture ใน Section 5
- **Sibling reference:** `en/purchase-request/01-data-model.md` — อธิบายฝั่ง PR ของ PR↔PO bridge อย่า duplicate เนื้อหานั้นที่นี่
- โมดูลที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request) (ต้นทาง upstream), [good-receive-note](/th/inventory/good-receive-note) (fulfilment ปลายน้ำผ่าน `received_qty`), [product](/th/inventory/product) (อ้างอิงสินค้าบรรทัด), [vendor-pricelist](/th/inventory/vendor-pricelist) (snapshot ราคา ณ เวลา PR-to-PO conversion), [inventory](/th/inventory/inventory) (context on-hand)
