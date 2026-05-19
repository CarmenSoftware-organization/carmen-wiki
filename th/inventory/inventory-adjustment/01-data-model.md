---
title: การปรับสต๊อก (Inventory Adjustment) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล inventory-adjustment
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory-adjustment, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Data Model

> **At a Glance**
> **ตาราง:** `tb_adjustment_type` (ตัวจำแนก reason) &nbsp;·&nbsp; `tb_stock_in` / `tb_stock_in_detail` (ขาเข้า) &nbsp;·&nbsp; `tb_stock_out` / `tb_stock_out_detail` (ขาออก) &nbsp;·&nbsp; ตาราง `_comment` แยกตามระดับ
> **กลุ่มผู้ใช้:** Developer / Auditor (เอกสารอ้างอิงสำหรับ dev)
> **FK สำคัญ:** `stock_in_detail.inventory_transaction_id` / `stock_out_detail.inventory_transaction_id → tb_inventory_transaction` (เติมตอน post); detail `→ tb_product`; header `→ tb_location` / `tb_adjustment_type` ลิงก์ rollup ผลต่างจาก [[physical-count]] / [[spot-check]] เป็น JSON เท่านั้น (`info.countId`) ไม่มี FK
> **รูปแบบ audit:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; **สองต้นเอกสารคู่ขนาน ไม่มี parent `tb_inventory_adjustment` ร่วม** — ทิศทางถูก gate ด้วย `tb_adjustment_type.type ∈ {STOCK_IN, STOCK_OUT}`

> **แหล่งความจริง:** Prisma schema ของ backend อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใต้แต่ละ package เป็นสำเนาที่ generate ขึ้นโดยอัตโนมัติ และไม่ใช่ตัวที่มีอำนาจ

## 1. ภาพรวม

โมดูล Inventory Adjustment คือ **เลเยอร์เอกสาร** สำหรับการแก้ไข stock-in / stock-out ด้วยมือ — write-offs, write-ons, ของพบใหม่, การปรับจากการหมดอายุ / เสียหาย / แตกหัก, การ rollup ผลต่างจากการนับ และการเปลี่ยนปริมาณ / มูลค่าใด ๆ ที่ไม่ไหลผ่านเอกสาร procurement (GRN), บริโภค (Store Requisition) หรือเอกสารนับด้วยตัวเอง ต่างจากโมดูลเอกสารอื่น ๆ โมดูล adjustment **ไม่ได้เป็นเจ้าของโมเดล `tb_inventory_adjustment` เดี่ยว** ใน Prisma schema canonical: รูปแบบที่ persist คือ **สองต้นเอกสารคู่ขนาน** — `tb_stock_in` (ขาเข้า / ทิศทาง write-on) และ `tb_stock_out` (ขาออก / ทิศทาง write-off) — เชื่อมด้วยตารางจำแนกร่วม `tb_adjustment_type` ที่แยกเหตุผลของ adjustment (เช่น `FOUND_STOCK`, `COUNT_OVERAGE`, `BREAKAGE`, `EXPIRY_WRITE_OFF`) และมี key เป็น `enum_adjustment_type` (`STOCK_IN` / `STOCK_OUT`)

ทั้ง `tb_stock_in` และ `tb_stock_out` ดำเนินตามโครงสร้างหลักของเอกสาร — header (`si_no` / `so_no`, `si_date` / `so_date`, location, adjustment-type, `doc_status`, workflow, comments, attachments) บวกแถวรายละเอียดลูก (ต่อ product พร้อม `qty`, `cost_per_unit`, `total_cost` และ back-reference `inventory_transaction_id` ไปยัง ledger ของ [[inventory]]) Enum `doc_status` ของ header (`draft` → `in_progress` → `completed` → `cancelled` / `voided`) ถือสถานะ workflow; การ post จุดชนวนที่การเปลี่ยนผ่าน `in_progress → completed` และเขียนแถว `tb_inventory_transaction` ที่มี `inventory_doc_type = stock_in` / `stock_out` พร้อม `inventory_transaction_id` ของ detail ถูกประทับลงไป ข้อมูล lot อยู่ที่ฝั่ง inventory transaction (`current_lot_no` / `from_lot_no` บน `tb_inventory_transaction_detail`, `lot_no` / `lot_index` บน `tb_inventory_transaction_cost_layer`) **ไม่ใช่** บนแถว detail ของ stock-in / stock-out — รูปแบบที่แตกต่างนี้แชร์กับ [[good-receive-note]] (`GRN_*` data-model § 5 ข้อ 3)

โมดูลนี้อยู่ **ระหว่างพื้นที่ปฏิบัติการและ ledger ของ inventory** เป็นปลายน้ำของ (a) [[physical-count]] / [[spot-check]] — ผลต่างการนับสร้างเอกสาร rollup `tb_stock_in` (เกิน) และ/หรือ `tb_stock_out` (ขาด) ที่ auto-stage ภายใต้อำนาจ Inventory Controller, (b) กิจกรรม ad-hoc ในพื้นที่ — Store Keeper สร้าง `tb_stock_in` สำหรับของพบใหม่ และ `tb_stock_out` สำหรับการแตก / หมดอายุ และ (c) การเรียกคืน / จัดประเภทใหม่ — Sysadmin หรือ Inventory Controller สร้าง adjustments สำหรับการโอนกรรมสิทธิ์ consignment-to-inventory และการแก้ไขข้อมูล migration เป็นต้นน้ำของ [[inventory]] — adjustment ที่อนุมัติแล้วทุกตัวเขียน `tb_inventory_transaction` หนึ่งแถวต่อบรรทัด detail ด้วย `enum_transaction_type = adjustment_in` / `adjustment_out` ใน cost-layer ledger ป้อน [[costing]] สำหรับการสร้าง FIFO layer / refresh weighted-average และสร้างการ posting GL ที่ key ด้วยบัญชีที่ map จาก adjustment-type

## 2. เอนทิตี

### 2.1 tb_adjustment_type

**ตัวจำแนก reason-code** สำหรับทั้งเอกสาร `tb_stock_in` และ `tb_stock_out` แถว reason-code มี `code` (เช่น `BREAKAGE`, `FOUND_STOCK`), `name` ที่อ่านได้, ทิศทางที่ถูกจำกัดผ่าน `enum_adjustment_type` (`STOCK_IN` หรือ `STOCK_OUT` — สังเกตว่า enum ของ Prisma มีเพียงสองค่าทิศทาง; "BOTH" เป็นความสะดวกของ application layer ไม่ใช่ค่าใน schema) และ `description` ที่เป็นข้อความอิสระ Reason code เป็น master data ที่ดูแลโดย System Administrator ภายใต้ [[inventory]]-`INV_AUTH_008` และใช้ตอนสร้างเอกสาร adjustment เพื่อขับเคลื่อน (i) การกรองรายการ reason ตามทิศทาง, (ii) การ map บัญชี GL สำหรับ journal entry ที่จะเกิดขึ้น (resolve ฝั่ง application ผ่าน JSON `info` / `dimension`, ไม่มีคอลัมน์ Prisma สำหรับ `gl_account`) และ (iii) การจัดประเภทเพื่อการรายงาน

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()` |
| `code` | `String @db.VarChar` | No | Reason-code mnemonic เช่น `BREAKAGE`, `EXPIRY_WRITE_OFF`, `FOUND_STOCK`, `COUNT_OVERAGE`, `COUNT_SHORTAGE`, `RECALL_REPLACEMENT`, `VENDOR_FREE_REPLACEMENT`, `DATA_FIX` Unique ภายใน `deleted_at` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงสำหรับ UI picker |
| `type` | `enum_adjustment_type` | No | ตัวจำแนกทิศทาง: `STOCK_IN` หรือ `STOCK_OUT` กรองรายการ reason ที่แสดงบนเอกสารที่สอดคล้อง |
| `description` | `String @db.VarChar` | Yes | คำอธิบายแบบข้อความอิสระ |
| `is_active` | `Boolean` | Yes | Default `true` Reason ที่ inactive ถูกซ่อนจาก picker ของเอกสารใหม่ แต่ยังอ่านได้บนเอกสารประวัติ |
| `note` | `String @db.VarChar` | Yes | บันทึกแบบข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ใช้ทั่วไป: flags `glAccount`, `requiresDocument`, `requiresQualityCheck` จาก interface `AdjustmentReason` ของ carmen/docs — ดู Section 5 ข้อ 2 ด้านล่าง |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete; non-null ซ่อนแถวจาก picker ของเอกสารใหม่ |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` Back-relations: many `tb_stock_in`, many `tb_stock_out`
**Indexes:** `@@unique([code, deleted_at])` เป็น `AT1_code_u`; `@@index([code])` เป็น `AT1_code_idx`

### 2.2 tb_stock_in

**Header เอกสาร adjustment ขาเข้า** หนึ่งแถวต่อหนึ่งเหตุการณ์ stock-in ถือเลขที่เอกสาร (`si_no`), วันที่เอกสาร (`si_date`), location (ปลายทางของขาเข้า), `adjustment_type` ที่เลือก (แถวใน `tb_adjustment_type` ที่ `type = STOCK_IN`), วงจรชีวิต `doc_status`, สถานะ workflow (current / previous / next stage, history, executor list) และคอลัมน์ audit-trail มาตรฐาน Comments และ attachments แขวนอยู่กับ `tb_stock_in_comment`; แถว detail ต่อ product แขวนอยู่กับ `tb_stock_in_detail`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `si_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่เอกสาร ขับเคลื่อนการตรวจสอบ period containment ตอน post ตาม [[inventory]] `INV_VAL_008` |
| `si_no` | `String @db.VarChar` | Yes | เลขที่ stock-in ที่อ่านได้; unique ภายใน `deleted_at` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระระดับ header ว่าทำไม adjustment กำลังเกิดขึ้น |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK ไป `tb_adjustment_type.id` (`onDelete: NoAction`) จำกัดที่ application layer ให้แถว `type = STOCK_IN` |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot ของ reason code ที่เลือก |
| `doc_status` | `enum_doc_status` | No | `draft` (default), `in_progress`, `completed`, `cancelled`, `voided` การ post จุดชนวนที่ `in_progress → completed` |
| `location_id` | `String @db.Uuid` | Yes | FK ไป `tb_location.id` — location ปลายทางสำหรับขาเข้า |
| `location_code` | `String @db.VarChar` | Yes | Snapshot ของรหัส location |
| `location_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ location |
| `workflow_id` | `String @db.Uuid` | Yes | Reference ไป workflow definition (`tb_workflow`) ที่ควบคุมเอกสารนี้ |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ workflow |
| `workflow_history` | `Json @db.JsonB` | Yes | Array ของการเปลี่ยน stage: `[{stage, action, message, by: {id, name}, at}]`; default `{}` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | ชื่อ stage ของ workflow ปัจจุบัน |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Stage ก่อนหน้า |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Stage ถัดไป (คำนวณโดย workflow engine) |
| `user_action` | `Json @db.JsonB` | Yes | Execute list: `{execute: [{id: <user_uuid>}, ...]}`; default `{}` ชุดผู้ใช้ที่ได้รับอนุญาตให้ดำเนินการ action ของ stage ปัจจุบัน |
| `last_action` | `enum_last_action` | Yes | `submitted` (default), `approved`, `reviewed`, `rejected` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | เวลาที่ action ล่าสุดถูกดำเนินการ |
| `last_action_by_id` | `String @db.Uuid` | Yes | ID ผู้ทำ action ล่าสุด |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot ชื่อแสดงของ actor |
| `note` | `String @db.VarChar` | Yes | บันทึกแบบข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ใช้ทั่วไป: count-source reference (เช่น `{ countId: "<count_uuid>" }` สำหรับเอกสาร rollup) |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง (Store Keeper หรือ Inventory Controller) |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`) Back-relations: many `tb_stock_in_detail`, many `tb_stock_in_comment`
**Indexes:** `@@unique([si_no, deleted_at])` เป็น `SI1_si_no_u`; `@@index([si_no])` เป็น `SI0_si_no_idx`

### 2.3 tb_stock_in_detail

**บรรทัด detail ต่อ product บนเอกสาร stock-in** หนึ่งแถวต่อบรรทัดสินค้าที่ได้รับผลกระทบ; ถือ `qty` (บวกสำหรับขาเข้า), `cost_per_unit`, `total_cost` และ back-reference `inventory_transaction_id` ที่ลิงก์ไปยังแถว ledger ของ [[inventory]] ที่สร้างตอน post Comments และ attachments ต่อบรรทัด detail แขวนอยู่กับ `tb_stock_in_detail_comment`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK ไป `tb_inventory_transaction.id` — เติมเฉพาะตอน post (`completed`); null ขณะ `draft` |
| `stock_in_id` | `String @db.Uuid` | No | FK ไป `tb_stock_in.id` |
| `sequence_no` | `Int` | Yes | ลำดับบรรทัดภายในเอกสาร; default `1` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระสำหรับบรรทัด |
| `comment` | `String @db.VarChar` | Yes | Comment ข้อความอิสระสำหรับบรรทัด |
| `product_id` | `String @db.Uuid` | No | FK ไป `tb_product.id` บังคับ |
| `product_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot แบบ localised |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณขาเข้าใน UoM base บวกสำหรับ stock-in ตามธรรมเนียม (เครื่องหมายใช้ที่ฝั่ง inventory-side detail ตาม [[inventory]] `INV_VAL_004`); default `0` |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยใน base currency ณ ขณะ post; default `0` ผู้ใช้กรอกสำหรับ lot ใหม่ (ต้องได้รับอนุมัติจาก Controller); auto-fill จาก cost-layer ล่าสุดของ lot ที่มีอยู่สำหรับ lot ที่มีอยู่ |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`; default `0` |
| `note` | `String @db.VarChar` | Yes | บันทึกแบบข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ใช้ทั่วไป: `{ lotNo, expiryDate, isNewLot, evidenceAttachments: [...] }` ซึ่งสะท้อน interface `AdjustmentItem` / `Lot` ของ carmen/docs — ดู Section 5 ข้อ 3 |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency counter; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_in_id → tb_stock_in.id` (`NoAction`) Back-relations: many `tb_stock_in_detail_comment`
**Indexes:** `@@unique([stock_in_id, product_id, dimension, deleted_at])` เป็น `SIT1_stock_in_product_dimension_u`; `@@index([stock_in_id, product_id])` เป็น `SIT2_stock_in_product_idx`; `@@index([stock_in_id])` เป็น `SIT2_stock_in_idx`

### 2.4 tb_stock_in_comment

**Comment / attachment ระดับเอกสาร** บน stock-in ถือ `message` ข้อความอิสระและ array JSON `attachments` ของ S3-token records (รูปความเสียหาย, vendor RMA, สแกน count sheet) ติด tag user-vs-system ผ่าน `enum_comment_type`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `stock_in_id` | `String @db.Uuid` | No | FK ไป `tb_stock_in.id` |
| `type` | `enum_comment_type` | No | `user` (default) หรือ `system` |
| `user_id` | `String @db.Uuid` | Yes | ผู้ใช้ที่เขียน comment |
| `message` | `String` | Yes | เนื้อหา comment ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ `{originalName, fileToken, contentType}`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `stock_in_id → tb_stock_in.id` (`NoAction`)

### 2.5 tb_stock_in_detail_comment

**Comment / attachment ระดับบรรทัด** บนแถว detail ของ stock-in รูปทรงเดียวกับ `tb_stock_in_comment` แต่ผูกกับบรรทัดเฉพาะ — ใช้สำหรับ "รูปความเสียหายเฉพาะของสินค้านี้" หรือ "vendor RMA สำหรับสินค้านี้"

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `stock_in_detail_id` | `String @db.Uuid` | No | FK ไป `tb_stock_in_detail.id` |
| `type` | `enum_comment_type` | No | `user` (default) หรือ `system` |
| `user_id` | `String @db.Uuid` | Yes | ผู้ใช้ |
| `message` | `String` | Yes | ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ attachment records; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `stock_in_detail_id → tb_stock_in_detail.id` (`NoAction`)

### 2.6 tb_stock_out

**Header เอกสาร adjustment ขาออก** เป็นภาพสะท้อนของ `tb_stock_in` ด้วย `so_no` / `so_date` และ `adjustment_type_id` ที่จำกัดที่ application layer ให้แถว `type = STOCK_OUT` ฟิลด์ workflow / status / audit เหมือนกัน; ลูกตาราง comment / detail / detail-comment ก็เหมือนกัน

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `so_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่เอกสาร |
| `so_no` | `String @db.VarChar` | Yes | เลขที่ stock-out ที่อ่านได้; unique ภายใน `deleted_at` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายระดับ header |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK ไป `tb_adjustment_type.id` (`onDelete: NoAction`) จำกัดที่ application layer ให้แถว `type = STOCK_OUT` |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot |
| `doc_status` | `enum_doc_status` | No | `draft` default; วงจรชีวิตเหมือนกับ stock-in |
| `location_id` | `String @db.Uuid` | Yes | FK ไป `tb_location.id` — location ต้นทางสำหรับขาออก |
| `location_code` | `String @db.VarChar` | Yes | Snapshot |
| `location_name` | `String @db.VarChar` | Yes | Snapshot |
| `workflow_id` | `String @db.Uuid` | Yes | Reference ของ workflow definition |
| `workflow_name` | `String @db.VarChar` | Yes | Snapshot |
| `workflow_history` | `Json @db.JsonB` | Yes | Array ประวัติ; default `{}` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | Stage ปัจจุบัน |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | Stage ก่อนหน้า |
| `workflow_next_stage` | `String @db.VarChar` | Yes | Stage ถัดไป |
| `user_action` | `Json @db.JsonB` | Yes | Execute list; default `{}` |
| `last_action` | `enum_last_action` | Yes | Default `submitted` |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | เวลาที่ action ล่าสุดถูกดำเนินการ |
| `last_action_by_id` | `String @db.Uuid` | Yes | Actor |
| `last_action_by_name` | `String @db.VarChar` | Yes | Snapshot ชื่อ actor |
| `note` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`) Back-relations: many `tb_stock_out_detail`, many `tb_stock_out_comment`
**Indexes:** `@@unique([so_no, deleted_at])` เป็น `SO1_so_no_u`; `@@index([so_no])` เป็น `SO0_so_no_idx`

### 2.7 tb_stock_out_detail

**บรรทัด detail ต่อ product บนเอกสาร stock-out** ภาพสะท้อนของ `tb_stock_in_detail` โดยที่ semantic ของ cost-per-unit กลับด้าน: ที่ stock-out, `cost_per_unit` มักจะถูก **เลือกตอน post โดย costing engine** (FIFO จาก layer เก่าที่สุด หรือ weighted-average ปัจจุบัน) ตาม [[inventory]] `INV_CALC_005` / `INV_CALC_006` — ต้นทุนที่ผู้ใช้กรอกบน draft เป็น preview ไม่ใช่ต้นทุนสุดท้ายที่มีอำนาจ (ซึ่ง resolve บน cost-layer ledger)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK ไป `tb_inventory_transaction.id`; เติมตอน post |
| `stock_out_id` | `String @db.Uuid` | No | FK ไป `tb_stock_out.id` |
| `sequence_no` | `Int` | Yes | ลำดับบรรทัด; default `1` |
| `description` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `comment` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `product_id` | `String @db.Uuid` | No | FK ไป `tb_product.id` |
| `product_code` | `String @db.VarChar` | Yes | Snapshot |
| `product_name` | `String @db.VarChar` | Yes | Snapshot |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot แบบ localised |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณขาออก (กรอกบวกบนเอกสาร; เครื่องหมายบน inventory-side detail เป็นลบตาม [[inventory]] `INV_VAL_004`); default `0` |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Preview ต้นทุนต่อหน่วยบน draft; ต้นทุนสุดท้ายเลือกตอน post โดย costing engine; default `0` |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`; default `0` |
| `note` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ใช้ทั่วไป: lot-override pick (`{lotNo}` เมื่อผู้ใช้ override FIFO default สำหรับ expiry-write-off), evidence attachments |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_out_id → tb_stock_out.id` (`NoAction`) Back-relations: many `tb_stock_out_detail_comment`
**Indexes:** `@@unique([stock_out_id, product_id, dimension, deleted_at])` เป็น `SOT1_stock_out_product_dimension_u`; `@@index([stock_out_id, product_id])` เป็น `SOT2_stock_out_product_idx`; `@@index([stock_out_id])` เป็น `SOT2_stock_out_idx`

### 2.8 tb_stock_out_comment, tb_stock_out_detail_comment

ภาพสะท้อนของ `tb_stock_in_comment` / `tb_stock_in_detail_comment` สำหรับเอกสารขาออก รูปทรงคอลัมน์เหมือนกัน; FKs ไปยัง `tb_stock_out.id` / `tb_stock_out_detail.id` ตามลำดับ ใช้สำหรับการแนบรูปความเสียหายบนบรรทัด write-off, references ของ recall-RMA, บันทึก sign-off ของ count-shortage

## 3. ความสัมพันธ์

```
tb_adjustment_type  (master ของ reason-code — ทิศทาง STOCK_IN หรือ STOCK_OUT)
    │  enum_adjustment_type ∈ {STOCK_IN, STOCK_OUT}
    │
    ├─1──*──► tb_stock_in   (เอกสาร adjustment ขาเข้า, วงจรชีวิต doc_status)
    │           │
    │           ├─1──*──► tb_stock_in_detail   (บรรทัดต่อ product)
    │           │           │
    │           │           ├──► tb_inventory_transaction (inventory_transaction_id,
    │           │           │     เติมตอน post — สถานะ completed)
    │           │           ├──► tb_product
    │           │           └─1──*──► tb_stock_in_detail_comment
    │           │
    │           ├─1──*──► tb_stock_in_comment (attachments / messages ระดับ header)
    │           └──► tb_location  (location_id — ปลายทางของขาเข้า)
    │
    └─1──*──► tb_stock_out  (เอกสาร adjustment ขาออก, วงจรชีวิต doc_status)
                │
                ├─1──*──► tb_stock_out_detail   (บรรทัดต่อ product)
                │           │
                │           ├──► tb_inventory_transaction (inventory_transaction_id)
                │           ├──► tb_product
                │           └─1──*──► tb_stock_out_detail_comment
                │
                ├─1──*──► tb_stock_out_comment
                └──► tb_location  (location_id — ต้นทางของขาออก)


ที่ post (doc_status: in_progress → completed), แต่ละบรรทัด detail เขียน
    ▼
tb_inventory_transaction  (header: inventory_doc_type ∈ {stock_in, stock_out},
                                   inventory_doc_no = tb_stock_in.id / tb_stock_out.id)
    │
    └─1──*──► tb_inventory_transaction_detail  (qty มีเครื่องหมายตามทิศทาง,
                                                  cost_per_unit, total_cost,
                                                  from_lot_no / current_lot_no)
                │
                └─1──*──► tb_inventory_transaction_cost_layer
                            (enum_transaction_type ∈ {adjustment_in, adjustment_out},
                             lot_no, lot_seq_no, in_qty / out_qty,
                             cost_per_unit, average_cost_per_unit)
```

หมายเหตุ:

- **สองต้นเอกสารคู่ขนาน หนึ่งตัวจำแนก** `tb_stock_in` และ `tb_stock_out` เป็นโมเดล Prisma อิสระที่มีรูปทรงเหมือนกัน; คอลัมน์ `type` ของแถว `tb_adjustment_type` gate ว่าต้นเอกสารใดที่ reason-code นั้นใช้ได้ ไม่มี parent `tb_inventory_adjustment` ร่วม — การ join กิจกรรมขาเข้าและขาออกสำหรับการรายงานคือ `UNION` ที่ application / read-model layer (โดยทั่วไปจากแถว `tb_inventory_transaction` ที่แชร์)
- **back-reference ของ inventory transaction เป็น anchor ของการ integration** แต่ละแถว detail ถือ `inventory_transaction_id` เป็น FK **nullable** ที่เติมเฉพาะตอน post (สถานะ `completed`) ขณะ `draft` / `in_progress` คอลัมน์เป็น null และไม่มีผลกระทบ inventory นี่สะท้อนรูปแบบ `tb_good_received_note_detail_item.inventory_transaction_id` ใน [[good-receive-note]] และรูปแบบเดียวกันใน [[store-requisition]] detail
- **ข้อมูล lot ไม่อยู่บน adjustment detail** JSON `info` ของแถว detail มักจะถือ `{lotNo, expiryDate}` สำหรับ draft / view ที่ผู้ใช้เห็น แต่ identity lot canonical persist ที่ฝั่ง inventory (`tb_inventory_transaction_detail.current_lot_no` / `from_lot_no` และ `tb_inventory_transaction_cost_layer.lot_no` / `lot_index`) นี่คือรูปแบบที่แตกต่างเดียวกันที่กล่าวถึงใน data-model ของ [[good-receive-note]] § 5 ข้อ 3 และ data-model ของ [[inventory]] § 5 ข้อ 11
- **Adjustment type ถูกจำกัดตามทิศทาง** ในขณะที่โมเดล Prisma `tb_stock_in.adjustment_type_id` และ `tb_stock_out.adjustment_type_id` เป็น FK ที่ไม่ได้พิมพ์ไปยัง `tb_adjustment_type` ทั้งคู่ application layer กรอง picker เพื่อให้เอกสาร `tb_stock_in` สามารถอ้างอิงแถว `adjustment_type` ที่ `type = STOCK_IN` เท่านั้น (และในทางกลับกัน) นี่คือที่มาของ interface `AdjustmentReason.type: 'IN' | 'OUT' | 'BOTH'` ของ carmen/docs — ดู Section 5 ข้อ 1
- **`adjustment_type_code` คือ snapshot ไม่ใช่ live join** เอกสารทั้งสอง persist รหัส snapshot บน header เพื่อ performance และ audit; การลบ / เปลี่ยนชื่อ reason code หลัง post ไม่เปลี่ยนเอกสารประวัติย้อนหลัง
- **การประกาศ `@relation` FK ทั้งหมดที่ระบุชัดเจนใช้ `onDelete: NoAction, onUpdate: NoAction`** — ความถูกต้องของการอ้างอิงรักษาโดย soft-delete ระดับ application (`deleted_at`) และโดย guard ของ doc-status / posting ไม่ใช่ cascade

## 4. Enums

- **`enum_adjustment_type`**: ตัวจำแนกทิศทางบน `tb_adjustment_type.type` สองค่า ไม่มี default ประกาศ (ทุก reason code ต้องระบุทิศทาง):
  - `STOCK_IN` — เหตุผลขาเข้า / write-on กรองเข้า reason-picker ของ `tb_stock_in` รหัสทั่วไป: `FOUND_STOCK`, `COUNT_OVERAGE`, `RECALL_REPLACEMENT`, `VENDOR_FREE_REPLACEMENT`, `DATA_FIX`
  - `STOCK_OUT` — เหตุผลขาออก / write-off กรองเข้า reason-picker ของ `tb_stock_out` รหัสทั่วไป: `BREAKAGE`, `EXPIRY_WRITE_OFF`, `THEFT_WRITE_OFF`, `COUNT_SHORTAGE`, `RECALL_WRITE_OFF`
- **`enum_doc_status`**: วงจรชีวิตเอกสารบน `tb_stock_in.doc_status` / `tb_stock_out.doc_status` Default `draft` ห้าค่า:
  - `draft` — แก้ไขได้ ไม่มีผลกระทบ inventory; เอกสารลบได้
  - `in_progress` — submit เพื่ออนุมัติ; อยู่ใน queue ของ Inventory Controller (เหนือ threshold) หรือ auto-advance (ต่ำกว่า threshold)
  - `completed` — สถานะ active ปลายทาง; การ post จุดชนวนแล้ว; มีหนึ่งแถว `tb_inventory_transaction` ต่อบรรทัด detail; เอกสาร immutable
  - `cancelled` — ปลายทาง inactive; ผู้ใช้ / ผู้อนุมัติยกเลิกก่อน post; ไม่มีผลกระทบ inventory
  - `voided` — ปลายทาง inactive; เอกสาร void หลังจากนั้น; ถ้า post แล้ว ต้องมีการชดเชย inventory transaction (รายการ ledger ต้นฉบับไม่ถูกแก้ไขตาม [[inventory]] `INV_POST_012`)
- **`enum_last_action`**: ตัวจำแนก action ล่าสุดของ workflow บน `tb_stock_in.last_action` / `tb_stock_out.last_action` Default `submitted` สี่ค่า: `submitted`, `approved`, `reviewed`, `rejected` ขับเคลื่อนการแสดง workflow-history และการ route ผู้ตรวจ
- **`enum_comment_type`**: บน `tb_stock_in_comment.type` / `tb_stock_in_detail_comment.type` / `tb_stock_out_comment.type` / `tb_stock_out_detail_comment.type` Default `user` สองค่า: `user` (ผู้ใช้เขียน), `system` (ระบบสร้าง เช่น บันทึกการเปลี่ยนสถานะ, การเตือนหลักฐานที่ต้องการ)

## 5. ความแตกต่างจาก carmen/docs

ชุด Inventory Adjustment ของ carmen/docs (`INV-ADJ-PRD.md`, `INV-ADJ-Business-Requirements.md`, `INV-ADJ-Business-Logic.md`, `INV-ADJ-Component-Structure.md`, `INV-ADJ-Overview.md`) อธิบายโมเดล interface ที่ศูนย์กลางอยู่ที่เอนทิตี `InventoryAdjustment` เดี่ยวที่ embed `items[]`, `lots[]`, `journal entries` และวงจรชีวิตสามสถานะ (`Draft → Posted → Void`) การตรวจสอบไขว้กับ Prisma schema canonical ได้ความแตกต่างดังต่อไปนี้:

| # | รายการ | carmen/docs บอกว่า | Prisma มี | Action |
|---|------|------------------|------------|--------|
| 1 | เอนทิตี `InventoryAdjustment` เดี่ยว | `interface InventoryAdjustment { id, date, type: 'IN' | 'OUT', status: 'Draft' | 'Posted' | 'Void', location, reason, items: StockMovementItem[], totals: {inQty, outQty, totalCost}, ... }` — โมเดลตารางเดี่ยวพร้อม discriminator `type` | **สองตารางคู่ขนาน** — `tb_stock_in` (ขาเข้า) และ `tb_stock_out` (ขาออก) — รูปทรงคอลัมน์เดียวกัน แต่ไม่มี parent `tb_inventory_adjustment` ร่วม Discriminator `type` อยู่บน `tb_adjustment_type` (ผ่าน `enum_adjustment_type`) ไม่ใช่บน header เอกสาร | ถือ Prisma เป็น canonical อัปเดต carmen/docs ให้บรรยายโมเดลสองตาราง; interface `InventoryAdjustment` คือ read-model union ของแถว stock-in และ stock-out `totals.inQty / outQty / totalCost` เป็น roll-up ที่ application derive (sum ของ `tb_stock_in_detail.qty × cost_per_unit` และ sum คู่ขนานของ `tb_stock_out_detail`) ไม่ใช่คอลัมน์ header ที่ persist |
| 2 | `AdjustmentReason.type: 'IN' | 'OUT' | 'BOTH'` | `interface AdjustmentReason { id, code, description, type: 'IN' | 'OUT' | 'BOTH', requiresDocument, requiresQualityCheck, glAccount, isActive, ... }` — สามค่าสำหรับตัวกรองทิศทาง, บวก `requiresDocument`, `requiresQualityCheck`, `glAccount` เป็นฟิลด์ first-class | `tb_adjustment_type.type` คือ enum `enum_adjustment_type` ที่มี **เพียงสองค่า**: `STOCK_IN` และ `STOCK_OUT` `BOTH` ไม่ใช่ค่าใน schema — reason code ที่ใช้ได้ทั้งสองทิศทางต้องนิยามสองครั้ง (หนึ่งแถวต่อทิศทาง) `requiresDocument`, `requiresQualityCheck`, `glAccount` **ไม่ใช่คอลัมน์ Prisma**; ถ้าใช้ อยู่ใน JSON `info` (ชื่อ key ทั่วไป `requiresDocument: boolean`, `requiresQualityCheck: boolean`, `glAccount: string`) | บรรยายความจริง enum สองค่า ทิศทาง `BOTH` ต้องการรูปแบบลงทะเบียนสองแถวใน seed data ย้าย `glAccount` และฟิลด์ flag เข้าสัญญา `info`-JSON ที่บรรยายไว้ (หรือเสนอเปลี่ยน schema ให้โปรโมตเป็นคอลัมน์) |
| 3 | `AdjustmentItem` พร้อม array `lots: Lot[]` ที่ embed | `interface StockMovementItem { id, productName, sku, location, lots: Lot[], uom, unitCost, totalCost, currentStock, adjustedStock }`; `interface Lot { lotNo, quantity, uom, expiryDate? }` — array lot ที่ embed ต่อ item พร้อม preview `currentStock` / `adjustedStock` | `tb_stock_in_detail` / `tb_stock_out_detail` **ไม่มี array `lots` ที่ embed** ข้อมูล lot persist ที่ฝั่ง inventory-transaction: `current_lot_no` / `from_lot_no` บน `tb_inventory_transaction_detail` (หนึ่งบรรทัดต่อผลกระทบ inventory; หลาย lot ⇒ แถว cost-layer หลายแถวภายใต้หนึ่ง detail) และ `lot_no` / `lot_index` บน `tb_inventory_transaction_cost_layer` view draft / ที่ผู้ใช้เห็นมักจะถือข้อมูล lot ใน JSON `info` บน detail; persistence canonical อยู่ที่ฝั่ง inventory `currentStock` / `adjustedStock` เป็น derived (ไม่ persist) | ถือ array lot เป็นเรื่อง draft / UI; identity lot canonical อยู่ที่ฝั่ง inventory บรรยายรูปทรง JSON `info` สำหรับการป้อน lot ใน draft `currentStock` / `adjustedStock` เป็นค่าของ read-model ที่คำนวณกับ `tb_inventory_transaction_cost_layer` สะท้อนกรอบของ [[good-receive-note]] § 5 ข้อ 3 |
| 4 | วงจรชีวิตสามสถานะ `Draft → Posted → Void` | `interface InventoryAdjustment.status: 'Draft' | 'Posted' | 'Void'` — สามสถานะไม่ต่อเนื่อง โดยที่ `Draft` แก้ไขได้, `Posted` เป็น immutable ปลายทาง, `Void` กลับรายการ adjustment ที่ post แล้ว | `tb_stock_in.doc_status` / `tb_stock_out.doc_status` คือ **ห้าค่า**: `draft`, `in_progress`, `completed`, `cancelled`, `voided` (`enum_doc_status` ร่วม) `completed` คือเทียบเท่า "posted" (ปลายทาง active, inventory transaction เขียนแล้ว); `voided` คือสถานะ void หลังการ post; `cancelled` คือสถานะเพิ่มเติมสำหรับเอกสารที่ยกเลิกก่อน post `in_progress` คือสถานะ workflow ที่ระบุชัดเจนระหว่าง `draft` และ `completed` ที่ carmen/docs ยุบเข้ากับ `Draft` | อัปเดต carmen/docs ให้บรรยายวงจรชีวิตห้าสถานะ การเปลี่ยนผ่าน `Draft → Posted` ใน carmen/docs ความจริงคือ `draft → in_progress → completed`; การเปลี่ยน `Posted → Void` คือ `completed → voided` พร้อมข้อจำกัดว่าต้อง post inventory transaction ชดเชยก่อนตาม [[inventory]] `INV_POST_012` / `INV_VAL_013` สถานะ `cancelled` ก่อน post เทียบเท่า "ละทิ้ง draft" และไม่มี counterpart ใน carmen/docs |
| 5 | `journalEntries: JournalEntry[]` ที่ embed บน adjustment | `interface JournalEntry { id, account, accountName, debit, credit, department, reference }` — array journal-entry ที่ embed บน interface `InventoryAdjustment` | ไม่มีโมเดล `tb_journal_entry` ใน Prisma schema canonical สำหรับ tenant Journal entries สร้างตอน post โดย application-layer GL-mapping engine อ่านจาก `info.glAccount` ของ adjustment-type และ cost-centre ของ location ที่ได้รับผลกระทบ และ **emit ไปยัง GL ledger** (Finance subsystem) — ไม่ persist บนแถว adjustment Audit trail ฝั่ง adjustment ของผลกระทบ journal-entry สร้างใหม่จาก `tb_inventory_transaction_cost_layer.total_cost` + `diff_amount` สำหรับ `inventory_doc_type = stock_in / stock_out` ที่ตรงกัน | บรรยาย journal entries เป็น artefact ปลายน้ำ ไม่ใช่ array ที่ embed Read-model ของ Finance join inventory transaction → cost-layer ledger ไปยังตาราง GL journal-entry (นอก schema นี้) Interface `JournalEntry` เป็นเรื่องของโมดูล Finance ไม่ใช่คอลัมน์ของ Inventory Adjustment |
| 6 | การหมายเลขเอกสาร — `Adjustment.id` คือ "เลขที่อ้างอิง" | "Adjustment แต่ละตัวต้องมีเลขที่อ้างอิงที่ไม่ซ้ำกัน" (ADJ_CRT_001) โดยปริยายใช้ `id` | `id` คือ UUID primary key (`gen_random_uuid()`) **เลขที่อ้างอิงที่อ่านได้** คือ `si_no` บน `tb_stock_in` และ `so_no` บน `tb_stock_out` แต่ละตัว unique ภายใน `deleted_at` สอง sequence-stream คู่ขนาน; application layer มักจะสร้างรูปแบบ `SI-YYMM-NNNNN` และ `SO-YYMM-NNNNN` | อัปเดต carmen/docs เพื่อแยก UUID `id` จาก `si_no` / `so_no` ที่อ่านได้ "เลขที่อ้างอิง" map ไปที่ `si_no` / `so_no` ไม่ใช่ `id` |
| 7 | ฟิลด์ `Department` บน adjustment | "รหัสแผนกเป็นบังคับ" (ADJ_CRT_009) — `interface InventoryAdjustment.department: string` | **ไม่มีคอลัมน์ `department_id`** บน `tb_stock_in` หรือ `tb_stock_out` ข้อมูลแผนก / cost-centre ถือผ่าน JSON `dimension` บน header (และ propagate ไปยัง `dimension` ของ inventory-transaction) รูปทรง dimension array คือ `[{type: "department", id: "<uuid>", code: "DEPT-A"}, ...]` | อัปเดต carmen/docs ให้บรรยาย JSON `dimension` เป็นตัวพาแผนก / cost-centre กฎ "department บังคับ" บังคับใช้ที่ application layer โดยการอ่าน `dimension` |
| 8 | "ต้องแนบเอกสารประกอบ" (ADJ_CRT_008) | แสดงนัยว่ามี array document-attachment บน header ของ adjustment | Attachments อยู่บน `tb_stock_in_comment` / `tb_stock_in_detail_comment` (และตาราง stock-out คู่ขนาน) เป็น JSON array `attachments` บนแถว comment ไม่มีตาราง `tb_attachment` เฉพาะสำหรับ header ของ adjustment — แถว comment เป็นตัวพา โดยที่ `message` เป็น optional และ `attachments` ถือ `[{originalName, fileToken, contentType}]` | บรรยายรูปแบบ comment-as-attachment-carrier กฎ "เอกสารประกอบที่จำเป็น" บังคับใช้โดย application โดยตรวจสอบว่ามีแถว comment อย่างน้อยหนึ่งแถวที่ `attachments` ไม่ว่างเมื่อ `info.requiresDocument = true` ของ adjustment-type |
| 9 | "ต้นทุนรวมต้องตรงกับยอด sum ของต้นทุน items" (ADJ_VAL_005) | แสดงนัยว่า `totals.totalCost` ของ header เป็นคอลัมน์ที่ persist กระทบกับ `Σ items[].totalCost` | **ไม่มีคอลัมน์ `total_cost` บน header** ของ `tb_stock_in` หรือ `tb_stock_out` Header ไม่ถือ roll-up; total cost เป็น sum ที่ derive จาก `tb_stock_in_detail.total_cost` (หรือ stock-out detail คู่ขนาน) กฎ "matches" เป็น degenerate — ไม่มีค่า header ที่จะ mismatch; read-model ของ application layer เสมอเป็น sum ของ details | ทิ้งกรอบ "match"; header ไม่มี totals กฎลดเหลือ `total_cost = qty × cost_per_unit` ต่อบรรทัด (กฎการคำนวณบรรทัดมาตรฐานที่ capture ภายใต้ `INV_CALC_001`) |
| 10 | Semantic "Date" ของ Adjustment | "วันที่ Adjustment ต้องอยู่ภายในงวดบัญชีที่เปิดอยู่" (ADJ_CRT_010) | วันที่เกี่ยวข้องคือ `tb_stock_in.si_date` / `tb_stock_out.so_date` (หรือ `created_at` ของ inventory transaction ถ้า `si_date` / `so_date` เป็น null ตอน post) การตรวจสอบ period-containment รันกับวันที่นี้ตาม [[inventory]] `INV_VAL_008` | บรรยายว่า period gate ใช้ `si_date` / `so_date` (หรือ `created_at` เป็น fallback) การตรวจสอบใช้ที่การเปลี่ยน `in_progress → completed` ไม่ใช่ตอนสร้าง draft |
| 11 | "ปริมาณ Lot ต้องไม่เกินยอดคงเหลือที่มี" (ADJ_VAL_004) | นัยว่ารันบน adjustment detail | บังคับใช้ที่ฝั่ง inventory ตอน post ตาม [[inventory]] `INV_VAL_005` (ไม่มียอดติดลบที่ `(location, product, lot_no, lot_index)`) เอกสาร adjustment detail ไม่เก็บยอดคงเหลือที่มี — อ่าน live จาก cost-layer ledger | บรรยายกฎเป็นบังคับใช้ฝั่ง inventory; เอกสาร adjustment เป็นจุดเข้า แต่การตรวจสอบเป็นของ ledger |
| 12 | "การตรวจสอบสต๊อกเรียลไทม์" (ADJ_PRC_010) | นัยว่ามีการตรวจสอบยอดคงเหลือ live ตลอด draft | การตรวจสอบ live รันที่ submit (การเปลี่ยน `in_progress`) ตาม [[inventory]] `INV_VAL_005`; ระหว่าง `draft` UI อาจแสดง preview ยอดคงเหลือ แต่การ reject ที่มีอำนาจเกิดเฉพาะที่ submit การตรวจสอบตอน post เป็นตัวสำคัญเพราะระหว่างการสร้าง draft และ submit ยอดคงเหลือสามารถเปลี่ยน (การ posting อื่นเกิดขึ้น) | ทำให้ชัดเจนว่าการตรวจสอบที่ submit ไม่ใช่ต่อเนื่อง; view draft เป็น snapshot ไม่ใช่ live guard |

## 6. แหล่งอ้างอิง

- **หลัก (แหล่งความจริง):** Prisma schemas ที่ list ใน header callout — โดยเฉพาะ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (แปดเอนทิตี: `tb_adjustment_type`, `tb_stock_in`, `tb_stock_in_detail`, `tb_stock_in_comment`, `tb_stock_in_detail_comment`, `tb_stock_out`, `tb_stock_out_detail`, `tb_stock_out_comment`, `tb_stock_out_detail_comment`; สี่ enums: `enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจสอบแล้วว่าไม่มีโมเดล inventory-adjustment)
- **รอง (การตรวจสอบไขว้แนวคิด):**
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md` — บทนำโมดูลและ key features; ความแตกต่าง § 5 ข้อ 4 (วงจรชีวิต), 7 (department), 8 (attachments)
  - `../carmen/docs/inventory-adjustment/INV-ADJ-PRD.md` — Product Requirements; ความแตกต่าง § 5 ข้อ 1 (single entity), 5 (journal entries), 6 (reference number)
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Requirements.md` — แคตตาล็อกกฎทางธุรกิจ (ADJ_CRT_*, ADJ_VAL_*, ADJ_PRC_*, ADJ_UI_*, ADJ_CALC_*); ที่มาของ rule IDs ที่ realign ใน [[inventory-adjustment/02-business-rules]] และ TypeScript interfaces `InventoryAdjustment` / `AdjustmentReason` / `StockMovementItem` / `Lot` / `JournalEntry` ที่ ground § 5
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Business-Logic.md` — process flows สำหรับ receive / issue / transfer / adjust / vendor-return; กรอบ FIFO / weighted-average ที่ apply กับ adjustments ใน § 5 (ผ่าน [[costing]] / [[inventory]])
  - `../carmen/docs/inventory-adjustment/INV-ADJ-Component-Structure.md` — ลำดับชั้น component (`InventoryAdjustmentList`, `InventoryAdjustmentDetail`, `InventoryAdjustmentForm`, `LotSelectionDialog`, `JournalEntryViewer`); อ้างอิงสำหรับรูปทรงข้อมูลฝั่ง UI ที่ขับเคลื่อนสัญญา JSON `info` (lot draft, attachments)
  - E2E: `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` — adjustment-type (reason-code) admin CRUD ฝั่ง master-data ของโมดูล
- โมดูลที่เกี่ยวข้อง: [[inventory]] (ledger canonical ที่การ post adjustment เขียนไป — `tb_inventory_transaction` / `tb_inventory_transaction_detail` / `tb_inventory_transaction_cost_layer` พร้อม `enum_inventory_doc_type ∈ {stock_in, stock_out}` และ `enum_transaction_type ∈ {adjustment_in, adjustment_out}`), [[costing]] (การสร้าง FIFO layer ตอน adjustment ขาเข้า, การบริโภค FIFO / refresh WA ตอน adjustment ขาออก), [[physical-count]] (rollup ผลต่าง post เป็น adjustments ตาม `INV_XMOD_003`), [[spot-check]] (ผลต่างจากการนับบางส่วน post เป็น adjustments ตาม `INV_XMOD_004`), [[good-receive-note]] (รูปแบบ data-model คู่ขนานสำหรับการเชื่อม `inventory_transaction_id` และกรอบ lot-data-on-inventory-side), [[product]] (ถือ `costing_method` ที่ gate การเลือกต้นทุนขาออกตอน post stock-out)
