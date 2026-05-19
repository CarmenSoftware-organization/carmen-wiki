---
title: ใบรับสินค้า (Goods Receive Note) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล good-receive-note
published: true
date: 2026-05-20T00:00:00.000Z
tags: good-receive-note, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# ใบรับสินค้า (Goods Receive Note) — Data Model

> **At a Glance**
> **ตาราง:** `tb_good_received_note` &nbsp;·&nbsp; `tb_good_received_note_detail` &nbsp;·&nbsp; `tb_good_received_note_detail_item` &nbsp;·&nbsp; `tb_good_received_note_comment` &nbsp;·&nbsp; `tb_good_received_note_detail_comment`
> **ผู้ใช้:** Developer / Auditor (อ้างอิงสำหรับ dev)
> **FK สำคัญ:** detail `→ tb_purchase_order_detail` (บรรทัด PO ต้นทาง); `detail_item.inventory_transaction_id → tb_inventory_transaction` (UUID เท่านั้น ไม่มี `@relation` — ledger inventory ปลายทาง); detail `→ tb_location` / `tb_product`; header `→ tb_vendor` / `tb_currency`
> **รูปแบบ Audit:** `created_*` / `updated_*` / `deleted_*` มาตรฐานบนทั้งห้าตาราง; ลายเซ็น workflow ต่อบรรทัด + `workflow_history` JSON บน header

> **แหล่งความจริง:** Prisma schema ของ backend อ่านสิ่งเหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใต้แต่ละ package เป็น copy ที่สร้างอัตโนมัติ ไม่ใช่ตัวอ้างอิงหลัก

## 1. ภาพรวม

โมดูล good-receive-note เป็นเจ้าของเอนทิตี tenant-schema ห้าตัว: header เอกสาร GRN (`tb_good_received_note`) รายการสินค้า (`tb_good_received_note_detail`) แถวเหตุการณ์รับของต่อบรรทัด (`tb_good_received_note_detail_item`) ที่บันทึกปริมาณรับ/FOC/รับจริงพร้อมภาพถ่ายการคำนวณราคาและภาษีสำหรับแต่ละเหตุการณ์รับของ และตาราง comment สำหรับ workflow / activity log ทั้งระดับ header และระดับบรรทัด (`tb_good_received_note_comment`, `tb_good_received_note_detail_comment`) เช่นเดียวกับ PR และ PO การติดตามขั้นตอน workflow ไม่ใช่ตารางเฉพาะ — JSON columns บน header (`workflow_history`, `workflow_current_stage` ฯลฯ) บวกตาราง comment รวมกันเป็นบันทึกถาวรของ timeline workflow ส่วน `tb_workflow` ที่ใช้ร่วมกันถูกอ้างอิงด้วย `workflow_id` แต่ไม่มี Prisma `@relation`

GRN อยู่ **ปลายน้ำของ [purchase-order](/th/inventory/purchase-order)** และ **ต้นน้ำของ [inventory](/th/inventory/inventory)** ในห่วงโซ่ procure-to-pay การเชื่อมโยงกับ PO ผ่านสองคอลัมน์บน `tb_good_received_note_detail` — `purchase_order_id` และ `purchase_order_detail_id` — โดย `purchase_order_detail_id` เป็นตัวที่มี Prisma `@relation` ชัดเจนกลับไปยัง `tb_purchase_order_detail` ทั้งสองคอลัมน์เป็น nullable เพื่อให้ตารางบรรทัดเดียวกันสามารถแทน GRN แบบ manual ที่ไม่มี PO ต้นทาง (กำหนดโดย enum `doc_type`) เมื่อ commit ผลปลายทางของ GRN จะกระจาย: ทุกบรรทัด resolve เป็นหนึ่งหรือหลายแถวใน `tb_inventory_transaction` / `tb_inventory_transaction_detail` (ผ่าน `tb_good_received_note_detail_item.inventory_transaction_id`) ซึ่งเป็นที่ที่การเพิ่มของคงคลัง cost layer และข้อมูล lot/expiry อยู่จริง `received_qty` ของบรรทัด PO เลื่อนไปข้างหน้า และ GRN เองเปลี่ยน `draft` → `saved` → `committed` GRN ยังเป็นหลักสำคัญของ **three-way match** (PO ↔ GRN ↔ ใบกำกับจากผู้ขาย) — leg ที่จับคู่แล้วคือสิ่งที่ปลดล็อกการ posting AP ปลายทาง

ประเด็นโครงสร้างที่น่าสังเกต: เอนทิตี `tb_good_received_note_detail_item` ไม่มีเทียบเท่าใน PR หรือ PO ในขณะที่บรรทัด PO เป็น triple ของ qty/unit/price เดียว บรรทัดของ GRN สามารถครอบคลุม **หลายเหตุการณ์รับของ** (การส่งของแบบแยก สต๊อกที่ผสม lot ลงในบรรทัดเดียวกัน FOC bundle ที่รับพร้อมสต๊อกที่จ่ายเงิน) แต่ละเหตุการณ์เป็นแถว `detail_item` ที่บรรจุ triple `order_qty` / `received_qty` / `foc_qty` ของตนเองและภาพถ่ายการเงิน (tax, discount, price, สกุลเงินฐาน) ที่คำนวณ ณ ขณะรับ — และแต่ละเหตุการณ์ยังบรรจุ `inventory_transaction_id` ซึ่งเป็น link ไปยังฝั่ง inventory ที่ข้อมูล lot number, expiry date และ cost-layer อยู่ ดังนั้นในขณะที่ PRD ของ carmen/docs อธิบาย lot/expiry เป็นฟิลด์ **บนบรรทัด GRN เอง** ความเป็นจริงใน Prisma คือมันอยู่บน inventory transaction ที่ link มา แถว `detail_item` คือ cursor เหตุการณ์รับและสะพาน ดูส่วน 5 สำหรับความแตกต่างนี้

## 2. เอนทิตี

### 2.1 tb_good_received_note

Header เอกสาร GRN บรรจุหมายเลขอ้างอิง บริบท vendor/currency/credit-term ข้อมูลใบกำกับและการรับ snapshot workflow flag consignment/cash ยอดรวม header ในสกุลธุรกรรมและสกุลฐาน และคอลัมน์ audit มาตรฐาน หนึ่ง header มีหลายแถว detail หลาย comment และหลายแถว extra-cost (`tb_extra_cost`)

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key สร้างผ่าน `gen_random_uuid()` |
| `grn_no` | `String @db.VarChar` | Yes | หมายเลขอ้างอิง GRN ที่มนุษย์อ่านได้ Nullable เพื่อรองรับ GRN ที่ยังเป็น draft และยังไม่ได้รับการกำหนดหมายเลข |
| `grn_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่รับ — เมื่อสินค้าได้รับการรับจริง |
| `invoice_no` | `String @db.VarChar` | Yes | หมายเลขใบกำกับจากผู้ขาย (ใช้ใน three-way match) |
| `invoice_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่ใบกำกับจากผู้ขาย |
| `description` | `String @db.VarChar` | Yes | คำอธิบาย free-text บน header |
| `doc_status` | `enum_good_received_note_status` | No | สถานะเอกสาร default `draft` |
| `doc_type` | `enum_good_received_note_type` | No | โหมดการสร้าง GRN default `purchase_order` (PO-sourced เป็นเส้นทางมาตรฐาน) |
| `vendor_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_vendor.id` |
| `vendor_name` | `String @db.VarChar` | Yes | snapshot ชื่อผู้ขาย |
| `currency_id` | `String @db.Uuid` | No | FK ไปยัง `tb_currency.id` — สกุลธุรกรรมของ GRN จำเป็น |
| `currency_code` | `String @db.VarChar` | Yes | snapshot รหัสสกุลเงิน |
| `exchange_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราแลกเปลี่ยน transaction-to-base default `1` |
| `exchange_rate_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่มีผลของอัตราแลกเปลี่ยนที่ใช้ |
| `workflow_id` | `String @db.Uuid` | Yes | FK ไปยังแถว `tb_workflow` (ไม่มี Prisma `@relation` — การเลือกถูก resolve โดย application) |
| `workflow_name` | `String @db.VarChar` | Yes | snapshot ชื่อ workflow |
| `workflow_history` | `Json @db.JsonB` | Yes | timeline การเปลี่ยนขั้น append-only default `{}` รายการบรรจุ `stage`, `action`, `message`, `by`, `at` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | slug ของขั้นที่ถือ GRN อยู่ |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | slug ของขั้นที่เพิ่งปล่อย GRN |
| `workflow_next_stage` | `String @db.VarChar` | Yes | slug ของขั้นถัดไปในห่วงโซ่ |
| `user_action` | `Json @db.JsonB` | Yes | metadata ของ action ที่ pending อยู่ default `{}` ปกติ `{ "execute": [{ "id": "<user-id>" }, ...] }` |
| `last_action` | `enum_last_action` | Yes | action ล่าสุดบนเอกสาร default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | timestamp ของ `last_action` |
| `last_action_by_id` | `String @db.Uuid` | Yes | user id ที่ทำ `last_action` |
| `last_action_by_name` | `String @db.VarChar` | Yes | snapshot ชื่อผู้ทำ action |
| `is_consignment` | `Boolean` | Yes | `true` เมื่อ GRN บันทึก consignment-in (ผู้ขายเป็นเจ้าของ) default `false` |
| `is_cash` | `Boolean` | Yes | `true` เมื่อการรับเป็นการซื้อเงินสด (ไม่ก่อภาระ AP) default `false` |
| `signature_image_url` | `String @db.VarChar` | Yes | URL / token รูปลายเซ็นของผู้รับ |
| `received_by_id` | `String @db.Uuid` | Yes | user id ของผู้รับ |
| `received_by_name` | `String @db.VarChar` | Yes | snapshot ชื่อแสดงของผู้รับ |
| `received_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp ของการรับจริง |
| `credit_term_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_credit_term.id` (ไม่ประกาศ Prisma `@relation`) |
| `credit_term_name` | `String @db.VarChar` | Yes | snapshot ชื่อ credit term |
| `credit_term_days` | `Int` | Yes | snapshot จำนวนวันของ credit term |
| `payment_due_date` | `DateTime @db.Timestamptz(6)` | Yes | คำนวณ `invoice_date + credit_term_days` persisted |
| `net_amount` | `Decimal @db.Decimal(15, 5)` | No | roll-up ของ `net_amount` บรรทัด (สกุลธุรกรรม) default `0` |
| `base_net_amount` | `Decimal @db.Decimal(15, 5)` | No | roll-up ของ `base_net_amount` บรรทัด (สกุลฐาน) default `0` |
| `total_amount` | `Decimal @db.Decimal(15, 5)` | No | roll-up ของ `total_price` บรรทัด (net + tax สกุลธุรกรรม) default `0` |
| `base_total_amount` | `Decimal @db.Decimal(15, 5)` | No | roll-up ของ `base_total_price` บรรทัด (สกุลฐาน) default `0` |
| `is_active` | `Boolean` | Yes | GRN ยัง active หรือไม่ default `true` |
| `note` | `String @db.VarChar` | Yes | หมายเหตุ free-text แนบกับ header |
| `info` | `Json @db.JsonB` | Yes | กระเป๋าขยายสำหรับ attribute header เฉพาะ tenant default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension (project, cost-centre, job code ฯลฯ) default `[]` |
| `doc_version` | `Int @db.Integer` | No | ตัวนับ version สำหรับ optimistic-concurrency default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | user id ที่สร้างแถว |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด default `now()` |
| `updated_by_id` | `String @db.Uuid` | Yes | user id ที่อัปเดตแถวล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete ค่าที่ไม่ใช่ null หมายถึงถูกลบทางตรรกะ |
| `deleted_by_id` | `String @db.Uuid` | Yes | user id ที่ soft-delete แถว |

**ข้อจำกัด:** `@id` บน `id` FKs: `currency_id → tb_currency.id` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`) หมายเหตุ: `credit_term_id` และ `workflow_id` ถูกเก็บเป็น UUID แต่ไม่มี Prisma `@relation` บน model นี้ — ถูก resolve โดย application back-relations: หลาย `tb_good_received_note_detail` หลาย `tb_good_received_note_comment` หลาย `tb_extra_cost` หลาย `tb_credit_note`
**Indexes:** `@@unique([grn_no, deleted_at])` เป็น `goodreceivednote_grn_no_u`; `@@index([grn_no])` เป็น `goodreceivednote_grn_no_idx`

ตารางคอมเมนต์ / ไฟล์แนบของโมดูลนี้ถูกแยกไปอีกหน้า — ดู [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/good-receive-note/01a-data-model-comments)

### 2.2 tb_good_received_note_detail

บรรทัดของ GRN ระบุสถานที่รับ สินค้าที่กำลังรับ และบรรทัด PO ต้นทาง (เมื่อมาจาก PO) หมายเหตุ ตารางนี้เก็บ **เฉพาะข้อมูลระบุ/หาตำแหน่ง** — ปริมาณจริง ราคา ภาษี และรายละเอียดต่อเหตุการณ์รับของอยู่บนแถวลูก `tb_good_received_note_detail_item` (ส่วน 2.3) หนึ่ง detail สามารถมีหลายแถว detail-item เพื่อแทนการส่งของแบบแยก lot ผสม หรือเหตุการณ์ paid-plus-FOC ที่ลงในบรรทัดเดียวกัน

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `good_received_note_id` | `String @db.Uuid` | No | FK ไปยัง `tb_good_received_note.id` |
| `sequence_no` | `Int` | No | การเรียงบรรทัดใน GRN default `1` |
| `purchase_order_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_purchase_order.id` (ไม่ประกาศ Prisma `@relation` บนคอลัมน์นี้ — มีเพียง `purchase_order_detail_id` ที่บรรจุ relation ชัดเจน) Nullable เพื่ออนุญาตบรรทัด GRN แบบ manual |
| `purchase_order_detail_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_purchase_order_detail.id` — บรรทัด PO ต้นทางที่กำลังทำให้สำเร็จ Nullable สำหรับการรับแบบ manual |
| `location_id` | `String @db.Uuid` | No | FK ไปยัง `tb_location.id` — store / สถานที่รับ จำเป็น |
| `location_code` | `String @db.VarChar` | Yes | snapshot รหัสสถานที่ |
| `location_name` | `String @db.VarChar` | Yes | snapshot ชื่อสถานที่ |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` จำเป็น |
| `product_code` | `String @db.VarChar` | Yes | snapshot รหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | snapshot ชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | snapshot ชื่อสินค้าภาษาท้องถิ่น |
| `product_sku` | `String @db.VarChar` | Yes | snapshot SKU |

**ข้อจำกัด:** `@id` บน `id` FKs: `good_received_note_id → tb_good_received_note.id`; `location_id → tb_location.id` (จำเป็น); `product_id → tb_product.id` (จำเป็น); `purchase_order_detail_id → tb_purchase_order_detail.id` (nullable) หมายเหตุ: `purchase_order_id` ถูกเก็บบนแถวแต่ไม่มี Prisma `@relation` — การ link PO ทำผ่าน relation ของ `purchase_order_detail_id` back-relations: หลาย `tb_good_received_note_detail_item` หลาย `tb_good_received_note_detail_comment`
**Indexes:** `@@unique([good_received_note_id, sequence_no])` เป็น `goodreceivednotedetail_good_received_note_id_sequence_no_u`; `@@index([good_received_note_id, sequence_no])` เป็น `goodreceivednotedetail_good_received_note_id_sequence_no_idx` หมายเหตุ: unique constraint ที่นี่ไม่รวม `deleted_at` (ต่างจาก PR / PO equivalent) ดังนั้นบรรทัดที่ soft-deleted ยังครอบครอง slot `sequence_no`

### 2.3 tb_good_received_note_detail_item

**แถวเหตุการณ์รับเฉพาะ GRN — ไม่มีเทียบเท่าใน PR หรือ PO** detail ของ GRN เดียว (ส่วน 2.2) สามารถสร้างหลายแถว `detail_item` เพื่อบันทึกการส่งของแบบแยก (หนึ่งบรรทัด สองกล่องที่มาคนละรถ) lot ผสม (หนึ่งบรรทัด สอง lot ต่างกันลงในสินค้า/สถานที่เดียวกัน) หรือ paid-plus-FOC bundle ที่ post กับบรรทัดเดียวกัน แต่ละแถวบรรจุ triple qty/unit/conversion-factor สาม parallel — `order_*`, `received_*` และ `foc_*` — บวก snapshot price-tax-discount-totals เต็ม **ทั้งสกุลธุรกรรมและสกุลฐาน** ที่คำนวณ ณ ขณะรับ `inventory_transaction_id` ของแถวคือ link ไปยังฝั่ง inventory; transaction ที่ link มา (และลูก `tb_inventory_transaction_detail`) คือที่ที่ lot number, expiry date และข้อมูล FIFO / average-cost layer อยู่จริง ดังนั้นแถว `detail_item` **ไม่ได้เป็น lot store เอง** — เป็น cursor ฝั่ง GRN สำหรับเหตุการณ์รับ และ inventory transaction คือ lot store

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `good_received_note_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_good_received_note_detail.id` |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_inventory_transaction.id` (ไม่ประกาศ Prisma `@relation`) populate ตอน commit; ลูก `tb_inventory_transaction_detail` ของแถวที่ link มาบรรจุ `lot_no`, `expiry_date`, `cost_per_unit` |
| `comment` | `String @db.VarChar` | Yes | comment free-text บนเหตุการณ์รับนี้ |
| `purchase_order_detail_purchase_request_detail_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_purchase_order_detail_tb_purchase_request_detail.id` (ไม่มี Prisma `@relation`) ชี้ไปยังแถวสะพาน PO↔PR เพื่อให้เหตุการณ์รับสามารถสืบย้อนกลับไปยังบรรทัด PR ต้นทาง |
| `order_qty` | `Decimal @db.Decimal(20, 5)` | Yes | qty ที่สั่งสำหรับเหตุการณ์นี้ (ใน order UoM) default `0` |
| `order_unit_id` | `String @db.Uuid` | Yes | UoM ที่ใช้ตอนสั่ง |
| `order_unit_name` | `String @db.VarChar` | Yes | snapshot ชื่อ order UoM |
| `order_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | conversion factor จาก order UoM ไปยัง base UoM default `0` |
| `order_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `order_qty × order_unit_conversion_factor` default `0` |
| `received_qty` | `Decimal @db.Decimal(20, 5)` | Yes | qty ที่รับสำหรับเหตุการณ์นี้ (ใน receiving UoM) default `0` นี่คือ qty ที่ post ไปยัง inventory |
| `received_unit_id` | `String @db.Uuid` | Yes | UoM ที่ใช้ตอนรับ |
| `received_unit_name` | `String @db.VarChar` | Yes | snapshot ชื่อ receiving UoM |
| `received_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | conversion factor จาก receiving UoM ไปยัง base UoM default `0` |
| `received_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `received_qty × received_unit_conversion_factor` default `0` |
| `foc_qty` | `Decimal @db.Decimal(20, 5)` | Yes | qty free-of-charge สำหรับเหตุการณ์นี้ (ใน FOC UoM) default `0` |
| `foc_unit_id` | `String @db.Uuid` | Yes | UoM ที่ใช้สำหรับส่วน FOC |
| `foc_unit_name` | `String @db.VarChar` | Yes | snapshot ชื่อ FOC UoM |
| `foc_unit_conversion_factor` | `Decimal @db.Decimal(20, 5)` | Yes | conversion factor จาก FOC UoM ไปยัง base UoM default `0` |
| `foc_base_qty` | `Decimal @db.Decimal(20, 5)` | Yes | `foc_qty × foc_unit_conversion_factor` default `0` |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | Yes | snapshot |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราภาษีที่มีผล default `0` |
| `tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีในสกุลธุรกรรม default `0` |
| `base_tax_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีในสกุลฐาน default `0` |
| `is_tax_adjustment` | `Boolean` | Yes | `true` เมื่อผู้ใช้เขียนทับจำนวนภาษีด้วยมือ default `false` |
| `discount_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราส่วนลด % default `0` |
| `discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดในสกุลธุรกรรม default `0` |
| `base_discount_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนส่วนลดในสกุลฐาน default `0` |
| `is_discount_adjustment` | `Boolean` | Yes | `true` เมื่อผู้ใช้เขียนทับส่วนลดด้วยมือ default `false` |
| `sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × received_qty` (สกุลธุรกรรม) default `0` |
| `net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `sub_total_price − discount_amount` default `0` |
| `total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `net_amount + tax_amount` default `0` |
| `base_price` | `Decimal @db.Decimal(20, 5)` | Yes | `price × exchange_rate` (ราคาต่อหน่วยสกุลฐาน) default `0` |
| `base_sub_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_price × received_qty` default `0` |
| `base_net_amount` | `Decimal @db.Decimal(20, 5)` | Yes | `base_sub_total_price − base_discount_amount` default `0` |
| `base_total_price` | `Decimal @db.Decimal(20, 5)` | Yes | `base_net_amount + base_tax_amount` default `0` |
| `note` | `String @db.VarChar` | Yes | หมายเหตุ free-text |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดต |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**ข้อจำกัด:** `@id` บน `id` FKs: `good_received_note_detail_id → tb_good_received_note_detail.id`; `tax_profile_id → tb_tax_profile.id`; FK `@relation` ที่ตั้งชื่อสามตัวไปยัง `tb_unit` — `tb_good_received_note_detail_item_order_unit_idTotb_unit` สำหรับ `order_unit_id`, `tb_good_received_note_detail_item_received_unit_idTotb_unit` สำหรับ `received_unit_id` และ `tb_good_received_note_detail_item_foc_unit_idTotb_unit` สำหรับ `foc_unit_id` หมายเหตุ: `inventory_transaction_id` และ `purchase_order_detail_purchase_request_detail_id` ถูกเก็บเป็น UUID แต่ไม่มี Prisma `@relation` บน model นี้
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key

## 3. ความสัมพันธ์

```
tb_workflow
    │  (workflow_id เก็บไว้แต่ไม่มี Prisma @relation บน tb_good_received_note)
    ▼
tb_good_received_note ──1──*──► tb_good_received_note_comment
    │  1                  ──1──*──► tb_extra_cost            (ส่วนประกอบ landed cost
    │                                                          เป็นเจ้าของโดยโมดูล extra-cost / costing)
    │                     ──1──*──► tb_credit_note           (credit note จากผู้ขายที่ออกกับ GRN นี้)
    │
    │ * good_received_note_id
    ▼
tb_good_received_note_detail ──1──*──► tb_good_received_note_detail_comment
    │  1
    │
    │ FK reference (snapshot ที่ denormalised บนแถว)
    ├──► tb_location                  (จำเป็น location_id)
    ├──► tb_product                   (จำเป็น product_id)
    └──► tb_purchase_order_detail     (optional purchase_order_detail_id — link บรรทัด PO)
    └──  (purchase_order_id เก็บบนแถวแต่ไม่มี Prisma @relation —
          header PO ถึงได้ผ่าน relation ของ purchase_order_detail)
    │
    │ * good_received_note_detail_id
    ▼
tb_good_received_note_detail_item    (แถวเหตุการณ์รับ — เฉพาะ GRN ไม่มีเทียบเท่า PR/PO)
    │
    │ FK reference
    ├──► tb_unit ×3                   (order_unit_id, received_unit_id, foc_unit_id — named relation)
    ├──► tb_tax_profile               (tax_profile_id)
    └──  (inventory_transaction_id และ purchase_order_detail_purchase_request_detail_id
          เก็บเป็น UUID แต่ไม่มี Prisma @relation — application resolve และ
          ให้ link ฝั่ง inventory และ PR-traceback ตามลำดับ)

tb_good_received_note (FK ระดับ header)
    ├──► tb_currency                  (currency_id จำเป็น)
    └──► tb_vendor                    (vendor_id optional)

tb_good_received_note_detail ──1──*──► tb_inventory_transaction_detail
    ทางอ้อมผ่าน tb_good_received_note_detail_item.inventory_transaction_id
    inventory transaction คือที่เก็บอย่างเป็นทางการของ lot_no, expiry_date
    และข้อมูล FIFO / average-cost layer — ฟิลด์เหล่านี้ไม่อยู่บน GRN
    detail_item เอง

tb_purchase_order_detail ──1──*──► tb_good_received_note_detail
    back-reference บรรทัด PO; received_qty ของบรรทัด PO เพิ่มขึ้นตอน commit GRN
    ทำให้ PO เลื่อนจาก `sent` → `partial` → `completed`
```

หมายเหตุ:

- **Header → detail** เป็น 1-to-many บน `good_received_note_id` (non-nullable บน detail)
- **Detail → detail_item** เป็น 1-to-many บน `good_received_note_detail_id` (non-nullable บน item) นี่คือความแตกต่างเชิงโครงสร้างจาก PR / PO: GRN มีระดับ nesting พิเศษเพื่อรองรับการรับแบบแยก / lot ผสมบนบรรทัดที่สั่งเดียว
- **Header → comment** และ **detail → comment** เป็น 1-to-many ทั้งคู่ ตาราง comment คือบันทึกถาวรของกิจกรรม workflow ส่วน JSON columns บน header (`workflow_history`, `user_action`) คือ cursor ในที่
- **PO → GRN** เป็น 1-to-many ผ่าน `tb_good_received_note_detail.purchase_order_detail_id` (คอลัมน์ที่บรรจุ Prisma `@relation`) `purchase_order_id` ก็เก็บบนแถวด้วยแต่ denormalised — link อย่างเป็นทางการคือผ่าน `purchase_order_detail_id` ทั้งสองคอลัมน์เป็น nullable เพื่อรองรับ GRN แบบ manual (กำหนดโดย `doc_type = manual`)
- **GRN → inventory** เข้าถึงผ่าน `tb_good_received_note_detail_item.inventory_transaction_id` ซึ่งไม่มี Prisma `@relation` แต่เป็นสะพานที่ application resolve เข้าสู่ `tb_inventory_transaction` และลูก **Lot number, expiry date และข้อมูล cost-layer อยู่บน inventory transaction ไม่ใช่บน GRN detail_item**
- **GRN ↔ PR traceback** เดินผ่าน `tb_good_received_note_detail_item.purchase_order_detail_purchase_request_detail_id` ซึ่งเป็น UUID reference (ไม่มี `@relation`) ไปยังสะพาน PO↔PR — ปิดวงจร procure-to-pay จาก PR ต้นทางไปยัง inventory landing
- การประกาศ FK `@relation` ที่ชัดเจนทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้น referential integrity ถูกรักษาโดย soft-delete (`deleted_at`) ระดับ application แทนที่จะเป็น cascade

## 4. Enum

- **`enum_good_received_note_status`**: enum สถานะเอกสารสำหรับ `tb_good_received_note.doc_status` Default `draft` มีสี่ค่า:
  - `draft` — สถานะเริ่มต้นที่แก้ไขได้; พนักงานรับของยังกรอกข้อมูล qty / lot อยู่; ไม่กระทบสต๊อกหรือ GL
  - `saved` — กรอกบรรทัดเสร็จและบันทึกเอกสารเพื่อ review (เช่นโดย Inventory Manager หรือ Finance) แต่ยังไม่ commit; ยังแก้ไขได้ ยังไม่กระทบสต๊อกหรือ GL
  - `committed` — เหตุการณ์ posting เดียวเกิดขึ้นแล้ว: inventory on-hand เพิ่ม FIFO / average-cost layer อัปเดต journal entry เขียน `received_qty` ของบรรทัด PO ต้นทางเลื่อน เอกสารถูกล็อก; การแก้ไขต้องใช้ `tb_credit_note` กับ GRN นี้หรือการปรับชดเชยใน [inventory-adjustment](/th/inventory/inventory-adjustment)
  - `voided` — GRN ถูก void ก่อน commit; การรับถูกยกเลิกโดยไม่กระทบ inventory หรือ GL
- **`enum_good_received_note_type`**: โหมดการสร้าง GRN สำหรับ `tb_good_received_note.doc_type` Default `purchase_order` มีสองค่า:
  - `purchase_order` — มาจาก PO (เส้นทางมาตรฐาน) แถว detail บรรจุ `purchase_order_detail_id` การ validate qty รันกับ `order_qty − received_qty − cancelled_qty` ที่เหลือบนบรรทัด PO
  - `manual` — GRN แบบ manual ที่ไม่มี PO ต้นทาง `purchase_order_id` และ `purchase_order_detail_id` ของแถว detail เป็น null และผู้ใช้ป้อน vendor / product / qty / price โดยตรง
- **`enum_comment_type`** (ใช้ร่วมกับ PR และ PO): `user` (comment ที่มนุษย์เขียน) `system` (รายการ activity-log อัตโนมัติที่เขียนโดย workflow engine) ใช้โดยทั้ง `tb_good_received_note_comment.type` และ `tb_good_received_note_detail_comment.type`
- **`enum_last_action`** (ใช้ร่วมกับ PR และ PO): `submitted`, `approved`, `reviewed`, `rejected` — ใช้โดย `tb_good_received_note.last_action` เพื่อจับ workflow action ล่าสุด

## 5. ความแตกต่างจาก carmen/docs

`GRN-Technical-Specification.md` อธิบาย TypeScript interface model (ด้วย `GoodsReceivedNote`, `GRNItem`, `GRNExtraCost`, `GRNExtraCostAllocation` ฯลฯ) และ enum สถานะ (`DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, CANCELLED`); `grn-master-prd.md` อธิบายวงจรชีวิต 3 สถานะ (`Received` / `Draft` → `Committed` → `Voided`) และอ้างอิงถึง Department, Delivery Point และฟิลด์ระดับ lot บนบรรทัด หลายอย่างต่างจาก Prisma schema อย่างเป็นทางการ:

| # | รายการ | carmen/docs ว่า | Prisma มี | Action |
|---|------|------------------|------------|--------|
| 1 | ค่าสถานะ GRN | Technical Spec: `enum GRNStatus { DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, CANCELLED }` PRD §5.1: model 3 สถานะ `Received` / `Draft` → `Committed` → `Voided` | `enum_good_received_note_status { draft, saved, committed, voided }` — เพิ่มสถานะกลาง `saved` (review-ready) ระหว่าง `draft` และ `committed`; ไม่มี `pending_approval`, `approved`, `rejected` หรือ `cancelled` | ถือ Prisma เป็นทางการ enum ของ Technical Spec มาจากรอบ modelling เก่าและควร deprecate; model 3 สถานะของ PRD แมพใกล้เคียงแต่ขาด `saved` อัปเดตทั้งสอง |
| 2 | ฟิลด์ header ที่ไม่อยู่ใน Prisma | Technical Spec `GoodsReceivedNote` รวม `departmentId`, `locationId`, `referenceNumber`, `subtotal`, `discountAmount`, `taxAmount`, `extraCostsTotal`, `total`, `approvedBy`, `approvedAt` บน header | `tb_good_received_note` **ไม่มี** `department_id` หรือ `location_id` ใน header (location อยู่ต่อบรรทัดบน detail) **ไม่มี** `reference_number` (มีเพียง `grn_no` และ `invoice_no`) และโครงสร้างยอดรวมต่างไป (`net_amount`, `base_net_amount`, `total_amount`, `base_total_amount` — ไม่มี `subtotal`, `discount_amount`, `tax_amount` หรือ `extra_costs_total` ระดับ header — เหล่านี้ roll up จากตาราง line / extra-cost ตอนอ่าน) ไม่มี `approved_by` / `approved_at` — ข้อมูลอนุมัติอยู่ใน workflow JSON และ `last_action_*` | จัดแนว carmen/docs `GoodsReceivedNote` interface ให้ตรงกับชื่อคอลัมน์ Prisma เอกสารว่า location ของ header *ไม่* ถูก model (location ต่อบรรทัด) และ approval อยู่ใน snapshot workflow |
| 3 | ตำแหน่ง lot / expiry / serial | PRD §3.5 และ Technical Spec `GRNItem` อ้างว่า `lotNumber`, `expiryDate`, `manufacturingDate` เป็นฟิลด์ **บนบรรทัด GRN** | `tb_good_received_note_detail` และ `tb_good_received_note_detail_item` **ไม่มี** คอลัมน์ `lot_no`, `expiry_date`, `manufacturing_date` หรือ `serial_no` ข้อมูล lot และ expiry อยู่บน `tb_inventory_transaction_detail.from_lot_no` / `current_lot_no` (และ `tb_inventory_transaction_cost_layer.lot_no`) ถึงผ่าน `tb_good_received_note_detail_item.inventory_transaction_id` | อัปเดต carmen/docs ให้บรรยาย lot/expiry เป็นฟิลด์ฝั่ง inventory-transaction ที่ปรากฏ **ผ่าน** link GRN detail_item ไม่ใช่เก็บบนแถว GRN เอง GRN detail_item คือ cursor เหตุการณ์รับ; inventory transaction คือ lot store |
| 4 | สถานะระดับ item บนบรรทัด | Technical Spec `GRNItem` รวม `status: GRNItemStatus { RECEIVED, REJECTED, PARTIALLY_REJECTED }` และ `rejectedQuantity`, `rejectionReason` | `tb_good_received_note_detail` และ `tb_good_received_note_detail_item` ไม่มี enum สถานะต่อบรรทัด ไม่มี `rejected_qty` และไม่มีคอลัมน์ `rejection_reason` การยอมรับ/ปฏิเสธ model โดยเขียนเหตุการณ์ qty ปฏิเสธเป็นแถว `detail_item` เพิ่มเติมหรือเป็นรายการ `_comment` ระดับบรรทัด ไม่มี enum first-class | ทิ้ง enum `GRNItemStatus` จาก carmen/docs หรือเอกสารว่ามันเป็นฟิลด์ derived ระดับ application ไม่ใช่คอลัมน์ schema |
| 5 | การ model extra-cost allocation | Technical Spec กำหนด `GRNExtraCost` และ `GRNExtraCostAllocation` เป็นเอนทิตีที่ GRN เป็นเจ้าของ พร้อม `allocationMethod: AllocationMethod { MANUAL, BY_VALUE, BY_QUANTITY, BY_WEIGHT, BY_VOLUME }` | Prisma มี model `tb_extra_cost` แยกต่างหากพร้อม `allocate_extra_cost_type: enum_allocate_extra_cost_type { manual, by_value, by_qty }` — และมีเพียง 3 โหมด allocation (`manual`, `by_value`, `by_qty`); ไม่มี `by_weight` หรือ `by_volume` **ไม่มี** ตารางสะพาน `tb_extra_cost_allocation` — allocation ถูกคำนวณและเขียนลงใน snapshot การเงินต่อ item ไม่ persist เป็นแถวแยก model ใช้ร่วมกัน (ไม่ใช่ GRN เป็นเจ้าของ); GRN back-reference ผ่าน `tb_extra_cost.good_received_note_id` | อัปเดต carmen/docs ให้ (a) ทิ้ง `BY_WEIGHT` / `BY_VOLUME` จาก enum allocation, (b) บรรยาย `tb_extra_cost` เป็น model ใช้ร่วมกันที่ GRN แนบ ไม่ใช่ลูก GRN, และ (c) ทิ้งการอ้าง entity `GRNExtraCostAllocation` แยกต่างหาก |
| 6 | ชื่อคอลัมน์ reference number | Technical Spec: `grnNumber` PRD: "GRN Reference Number" | `tb_good_received_note.grn_no` (nullable ไม่มี length cap) | เปลี่ยนชื่อใน data dictionary ของ carmen/docs; flag ว่าคอลัมน์เป็น nullable บน draft GRN และ uniqueness บังคับใช้ร่วมกับ `deleted_at` (`@@unique([grn_no, deleted_at])`) |
| 7 | FOC บนบรรทัด | PRD §3.4.4 / §3.4.5 list `FOC quantities` และ `FOC Unit` ต่อบรรทัด | FOC model **ที่ระดับเหตุการณ์รับ** (`tb_good_received_note_detail_item.foc_qty` / `foc_unit_id` / `foc_unit_conversion_factor` / `foc_base_qty`) ไม่ใช่ระดับบรรทัด GRN ซึ่งหมายความว่าบรรทัดเดียวสามารถบันทึก paid stock และ FOC stock เป็นแถว detail_item **แยก** ภายใต้ `good_received_note_detail_id` เดียวกัน | อัปเดต carmen/docs ให้บรรยาย FOC ที่ระดับเหตุการณ์รับ; ชี้แจงว่า paid และ FOC สำหรับสินค้า/สถานที่เดียวกันปกติถูกบันทึกเป็นแถว detail_item parallel ไม่ใช่เป็นสองคอลัมน์บนบรรทัดเดียว |
| 8 | Delivery point บน header | PRD §3.4.1 list "Delivery Point" ใน header GRN | `tb_good_received_note` **ไม่มี** คอลัมน์ `delivery_point_id` บริบทการส่งถูกจับโดยปริยายผ่าน `location_id` ต่อบรรทัดและผ่าน snapshot delivery-point ของ PO ต้นทางถึงผ่าน `tb_purchase_order_detail_tb_purchase_request_detail.delivery_point_*` | ทิ้ง "Delivery Point" จาก data dictionary ของ header GRN; เอกสารว่าบริบทการส่งเป็นต่อบรรทัดผ่าน `location_id` (และสืบย้อนได้ผ่าน PR-bridge snapshot) |
| 9 | Department บน header | Technical Spec `GoodsReceivedNote.departmentId` (จำเป็น) | ไม่มีคอลัมน์ `department_id` บน `tb_good_received_note` ข้อมูล department / cost-centre อยู่ใน JSON `dimension` array (array ของ object cost-dimension) | ทิ้ง `departmentId` จาก data dictionary ของ header carmen/docs; เอกสารว่า cost-centre / department อยู่ใน `dimension` JSON ต่อแถว ซึ่งเป็น tenant-extensible cost-dimension contract |
| 10 | flag `is_consignment` / `is_cash` | PRD §3.4.1 list "Consignment checkbox" และ "Cash checkbox" บน header แต่ไม่รวมใน `GoodsReceivedNote` Technical Spec interface | ทั้งสองฟิลด์มีอยู่บน `tb_good_received_note` (`is_consignment Boolean?`, `is_cash Boolean?` ทั้งคู่ default `false`) | เพิ่มสอง boolean field ลงใน carmen/docs `GoodsReceivedNote` interface และเอกสารความหมาย (consignment-in กดผลกระทบสต๊อกที่กิจการเป็นเจ้าของ + AP; cash กดภาระ AP) |

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** Prisma schema ที่ list ใน header callout — เฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (model GRN ทั้งห้า, ทั้งสอง enum, model `tb_extra_cost` / `tb_inventory_transaction*` ที่เกี่ยวข้อง) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ยืนยันว่าไม่มี model GRN)
- **Secondary (concept cross-check):**
  - `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md` — TypeScript interface model และกฎการคำนวณ; ความแตกต่างในส่วน 5 (รายการ 1, 2, 4, 5, 9)
  - `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — PRD พร้อม list ฟิลด์ header, พฤติกรรม FOC และ prose วงจรชีวิต 3 สถานะ; ความแตกต่างในส่วน 5 (รายการ 1, 3, 6, 7, 8, 10)
- **Sibling reference:** [01-data-model.md](../purchase-order/01-data-model.md) (purchase-order) — บรรยายฝั่ง PO ของ linkage PO→GRN; อย่าทำซ้ำเนื้อหานี้ที่นี่
- โมดูลที่เกี่ยวข้อง: [purchase-order](/th/inventory/purchase-order) (ต้นทางผ่าน `purchase_order_detail_id`), [purchase-request](/th/inventory/purchase-request) (จุดเริ่ม ถึงผ่าน PO↔PR bridge id เก็บบน detail_item), [inventory](/th/inventory/inventory) (ปลายทาง — inventory transaction คือที่ที่ข้อมูล lot, expiry และ cost-layer อยู่), [costing](/th/inventory/costing) (การสร้าง FIFO / average-cost layer ตอน commit), [inventory-adjustment](/th/inventory/inventory-adjustment) (การแก้ไขหลัง commit), [vendor-pricelist](/th/inventory/vendor-pricelist) (การตรวจสอบ price-variance กับราคา GRN ต่อหน่วย), [product](/th/inventory/product) (reference สินค้าต่อบรรทัด)
