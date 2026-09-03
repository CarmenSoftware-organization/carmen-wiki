---
title: การปรับสต๊อก (Inventory Adjustment) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล inventory-adjustment
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Data Model

> **At a Glance**
> **ตาราง:** `tb_adjustment_type` (ตัวจำแนก reason) &nbsp;·&nbsp; `tb_stock_in` / `tb_stock_in_detail` (ขาเข้า) &nbsp;·&nbsp; `tb_stock_out` / `tb_stock_out_detail` (ขาออก) &nbsp;·&nbsp; ตาราง `_comment` แยกตามระดับ
> **กลุ่มผู้ใช้:** Developer / Auditor (เอกสารอ้างอิงสำหรับ dev)
> **FK สำคัญ:** `stock_in_detail.inventory_transaction_id` / `stock_out_detail.inventory_transaction_id → tb_inventory_transaction` (ประทับตอนสร้าง ไม่ใช่ตอน post แยกต่างหาก); detail `→ tb_product`; header `→ tb_location` / `tb_adjustment_type`
> **รูปแบบ audit:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; **สองต้นเอกสารคู่ขนาน ไม่มี parent `tb_inventory_adjustment` ร่วม**

> **แหล่งความจริง:** Prisma schema ของ backend อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`

## 1. ภาพรวม

โมดูล Inventory Adjustment คือ **เลเยอร์เอกสาร** สำหรับการแก้ไข stock-in / stock-out ด้วยมือ — write-offs, write-ons, ของพบใหม่, การปรับจากการหมดอายุ / เสียหาย / แตกหัก ที่ไม่ไหลผ่านเอกสาร procurement (GRN) หรือบริโภค (Store Requisition) ต่างจากโมดูลเอกสารอื่น ๆ โมดูล adjustment **ไม่ได้เป็นเจ้าของโมเดล `tb_inventory_adjustment` เดี่ยว** ใน Prisma schema canonical: รูปแบบที่ persist คือ **สองต้นเอกสารคู่ขนาน** — `tb_stock_in` (ขาเข้า) และ `tb_stock_out` (ขาออก) — เชื่อมด้วยตารางจำแนกร่วม `tb_adjustment_type` ที่ถือ `code` / `name` (เช่น `FOUND_STOCK`, `BREAKAGE`) และมี key เป็น `enum_adjustment_type` (`stock_in` / `stock_out` / `eop_in` / `eop_out`)

ทั้ง `tb_stock_in` และ `tb_stock_out` ดำเนินตามโครงสร้างหลักของเอกสาร — header (`si_no` / `so_no`, `si_date` / `so_date`, location, adjustment-type, `doc_status`, คอลัมน์ workflow, comments) บวกแถวรายละเอียดลูก (ต่อ product พร้อม `qty`, `cost_per_unit`, `total_cost` และ back-reference `inventory_transaction_id` ไปยัง ledger ของ [inventory](/th/inventory/inventory)) คอลัมน์ `doc_status` ของ header มีค่า default เป็น `draft` ใน schema แต่ **`StockInService.create()` / `StockOutService.create()` เขียน `doc_status: enum_doc_status.completed` โดยตรงเสมอ ในทรานแซกชันฐานข้อมูลเดียวกับการเขียน ledger** — ไม่มี code path ใดในโมดูลนี้ที่สร้างแถว `draft`, `in_progress` หรือ `cancelled` ได้เลย; ทั้งสามค่าอยู่ใน `enum_doc_status` ที่ใช้ร่วมกัน แต่เข้าไม่ถึงผ่านการสร้าง stock-in/stock-out การ post จึงเกิดขึ้น **ตอนสร้าง** ไม่ใช่ตอนเปลี่ยนสถานะภายหลัง และเขียนแถว `tb_inventory_transaction` ที่มี `inventory_doc_type = stock_in` / `stock_out` พร้อม `inventory_transaction_id` ของ detail ถูกประทับลงไป ข้อมูล lot อยู่ที่ฝั่ง inventory transaction (`current_lot_no` / `from_lot_no` บน `tb_inventory_transaction_detail`, `lot_no` / `lot_index` บน `tb_inventory_transaction_cost_layer` ทั้งคู่สร้างโดยระบบ — prefix `ADI-`/`ADO-`) **ไม่ใช่** บนแถว detail ของ stock-in / stock-out และไม่มี UI เลือก lot ใด ๆ ใน frontend ของโมดูลนี้

โมดูลนี้อยู่ **ระหว่างพื้นที่ปฏิบัติการและ ledger ของ inventory** เมธอด `submit()` ของ [physical-count](/th/inventory/physical-count) สร้างแถว `tb_stock_in` (ส่วนเกิน) / `tb_stock_out` (ขาด) โดยตรงที่ `doc_status = completed` โดยไม่ตั้งค่า `adjustment_type_id` — รอบนี้ยืนยันเพียงการสร้างแถว แต่ไม่ได้ตรวจสอบว่า path นั้นเรียก `executeAdjustmentIn`/`executeAdjustmentOut` ของ ledger แบบเดียวกับหน้าจอ stock-in/stock-out ที่สร้างด้วยมือหรือไม่ — ควรตรวจสอบซ้ำในรอบ resync ของโมดูล `physical-count` เอง ทุกการเขียน stock-in/stock-out เรียก `InventoryTransactionService` ตัวเดียวกับที่ GRN, SR และ period-end ใช้ ป้อน [costing](/th/inventory/costing) สำหรับการสร้าง FIFO layer / refresh weighted-average การค้นหาทั่วทั้งโมดูลนี้สำหรับ `journal`, `ledger` และโค้ดลงบัญชี GL ไม่พบผลลัพธ์ใด ๆ — ไม่มีการเชื่อมต่อบัญชี/GL ในโมดูลนี้

## 2. เอนทิตี

### 2.1 tb_adjustment_type

**ตัวจำแนก reason-code** สำหรับทั้งเอกสาร `tb_stock_in` และ `tb_stock_out` แถว reason-code มี `code` (เช่น `BREAKAGE`, `FOUND_STOCK`), `name` ที่อ่านได้, ทิศทางผ่าน `enum_adjustment_type` (สี่ค่า — ดู Section 4) และ `description` ที่เป็นข้อความอิสระ Reason code ถูกดูแลบนหน้าจอ master data แยกต่างหาก (`/config/adjustment-type`, [master-data/adjustment-type](/th/inventory/master-data/adjustment-type)) และตอนสร้างเอกสาร adjustment มีหน้าที่เพียงกรองรายการ reason ตามทิศทางฝั่ง frontend (`ADJUSTMENT_TYPE.STOCK_IN` / `STOCK_OUT` ใน `types/adjustment-type.ts`) ไม่มีฟิลด์บัญชี GL, flag บังคับแนบเอกสาร หรือ flag ตรวจสอบคุณภาพบนตารางนี้ และไม่มีโค้ดใดในโมดูลนี้อ่านหรือเขียน key ที่รู้จักบน `info`/`dimension` เลย

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `doc_version` | `Int @db.Integer` | No | ตัวนับ optimistic-concurrency; default `0` |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()` |
| `code` | `String @db.VarChar` | No | Reason-code mnemonic เช่น `BREAKAGE`, `FOUND_STOCK` Unique ภายใน `deleted_at` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงสำหรับ UI picker |
| `type` | `enum_adjustment_type` | No | ตัวจำแนกทิศทาง: `stock_in` หรือ `stock_out` สำหรับ adjustment ที่ผู้ใช้สร้าง (กรอง picker ฝั่ง frontend เท่านั้น — ดู § 5 ข้อ 2); `eop_in`/`eop_out` เป็นค่าสงวนสำหรับ period-end ที่ picker ของโมดูลนี้ไม่แสดง |
| `description` | `String @db.VarChar` | Yes | คำอธิบายแบบข้อความอิสระ |
| `is_active` | `Boolean` | Yes | Default `true` Reason ที่ inactive ถูกซ่อนจาก picker ของเอกสารใหม่ แต่ยังอ่านได้บนเอกสารประวัติ |
| `note` | `String @db.VarChar` | Yes | บันทึกแบบข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ไม่พบ key ที่รู้จักถูกอ่านหรือเขียนที่ไหนในโมดูลนี้เลย ทั้ง frontend และ backend |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` ไม่พบ key ที่รู้จักถูกใช้งาน |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete; non-null ซ่อนแถวจาก picker ของเอกสารใหม่ |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` Back-relations: many `tb_stock_in`, many `tb_stock_out`
**Indexes:** `@@unique([code, deleted_at])` เป็น `AT1_code_u`; `@@index([code])` เป็น `AT1_code_idx`

### 2.2 tb_stock_in

**Header เอกสาร adjustment ขาเข้า** หนึ่งแถวต่อหนึ่งเหตุการณ์ stock-in ถือเลขที่เอกสาร (`si_no`), วันที่เอกสาร (`si_date`), location (ปลายทางของขาเข้า), `adjustment_type` ที่เลือก, คอลัมน์ `doc_status` และคอลัมน์ workflow ชุดหนึ่ง บวกคอลัมน์ audit-trail มาตรฐาน Comments แขวนอยู่กับ `tb_stock_in_comment`; แถว detail ต่อ product แขวนอยู่กับ `tb_stock_in_detail` **คอลัมน์ `workflow_*` และ `user_action` มีอยู่บนตารางนี้ แต่ `stock-in.service.ts` ไม่เคยตั้งค่าหรืออ่านมันเลย** — โมดูลนี้ไม่มีการเรียก workflow orchestrator ที่ไหนใน code การสร้าง/อัปเดต/void จึงเป็นโครงที่ตายแล้ว ไม่ใช่ feature ที่ทำงานจริง

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `si_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่เอกสาร ตรวจสอบฝั่ง client เทียบกับช่วงงวดปัจจุบัน (Zod ใน `ia-form-schema.ts`); ไม่พบการตรวจสอบเทียบเท่าใน `StockInService.create()`/`update()` |
| `si_no` | `String @db.VarChar` | Yes | เลขที่ stock-in ที่อ่านได้; unique ภายใน `deleted_at` สร้างผ่าน running-code service (รูปแบบ `STOCK-IN`) |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระระดับ header; optional (สูงสุด 256 ตัวอักษรฝั่ง client) ไม่บังคับ |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK ไป `tb_adjustment_type.id` (`onDelete: NoAction`) picker กรองเหลือ `type = stock_in` ฝั่ง client เท่านั้น; backend ตรวจสอบเพียงว่าแถวที่อ้างอิงมีอยู่จริง ไม่ตรวจ `type` |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot ของ reason code ที่เลือก |
| `doc_status` | `enum_doc_status` | No | Schema default `draft`; **`StockInService.create()` เขียน `completed` เสมอ** — `in_progress` และ `cancelled` ไม่เคยถูกกำหนดโดยโค้ดของโมดูลนี้ `voided` เข้าถึงได้เฉพาะผ่าน void endpoint (ดู [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) § 5) |
| `location_id` | `String @db.Uuid` | Yes | FK ไป `tb_location.id` — location ปลายทางสำหรับขาเข้า |
| `location_code` | `String @db.VarChar` | Yes | Snapshot ของรหัส location |
| `location_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ location |
| `workflow_id` | `String @db.Uuid` | Yes | ไม่ถูกใช้โดยโมดูลนี้ (ดูหมายเหตุด้านบน) |
| `workflow_name` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_history` | `Json @db.JsonB` | Yes | ไม่ถูกใช้โดยโมดูลนี้; default `{}` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_next_stage` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `user_action` | `Json @db.JsonB` | Yes | ไม่ถูกใช้โดยโมดูลนี้; default `{}` |
| `last_action` | `enum_last_action` | Yes | Schema default `submitted`; ไม่พบว่าโมดูลนี้เปลี่ยนสถานะนี้ |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | ไม่พบว่าโมดูลนี้ตั้งค่า |
| `last_action_by_id` | `String @db.Uuid` | Yes | ไม่พบว่าโมดูลนี้ตั้งค่า |
| `last_action_by_name` | `String @db.VarChar` | Yes | ไม่พบว่าโมดูลนี้ตั้งค่า |
| `note` | `String @db.VarChar` | Yes | บันทึกแบบข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` `create()` ส่งผ่านค่าที่ client ให้มาโดยไม่แก้ไข (`info: item.info || null`); ไม่มี key ที่รู้จักถูก interpret โดย backend ของโมดูลนี้ |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` ส่งผ่านโดยไม่แก้ไข ไม่มี key ที่รู้จักถูก interpret |
| `doc_version` | `Int @db.Integer` | No | ตัวนับ optimistic-concurrency; default `0` ตรวจสอบใน `where` clause ของ update |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete **`voidStockIn()` ตั้งค่านี้พร้อมกับ `doc_status = voided`** ในการ update ครั้งเดียวกัน — เอกสารที่ void แล้วจึงหลุดจากทุก query ที่กรอง `deleted_at: null` รวมทั้ง list และ detail endpoint เอกสารที่ void แล้วไม่ใช่แค่ถูก flag badge แต่เข้าถึงไม่ได้ผ่าน API ปกติอีกต่อไป |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`) Back-relations: many `tb_stock_in_detail`, many `tb_stock_in_comment`
**Indexes:** `@@unique([si_no, deleted_at])` เป็น `SI1_si_no_u`; `@@index([si_no])` เป็น `SI0_si_no_idx`

### 2.3 tb_stock_in_detail

**บรรทัด detail ต่อ product บนเอกสาร stock-in** หนึ่งแถวต่อบรรทัดสินค้าที่ได้รับผลกระทบ; ถือ `qty` (บวกสำหรับขาเข้า), `cost_per_unit`, `total_cost` และ back-reference `inventory_transaction_id` ที่ลิงก์ไปยังแถว ledger ของ [inventory](/th/inventory/inventory) เนื่องจากการสร้างจะ post เสมอ (§ 1) `inventory_transaction_id` จึงถูกเติมในทุกแถวจริง — ไม่มีช่วง draft ที่ค่านี้เป็น null `cost_per_unit` ให้ผู้ใช้กรอกได้บนหน้าจอนี้ (เติมเริ่มต้นจากค่าเฉลี่ยปัจจุบันของ location เป็นข้อเสนอ) และเป็นค่าที่ ledger ใช้จริงในการสร้าง cost layer Comments และ attachments ต่อบรรทัด detail แขวนอยู่กับ `tb_stock_in_detail_comment`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK ไป `tb_inventory_transaction.id` — ประทับในทรานแซกชันเดียวกับการสร้างเอกสาร |
| `stock_in_id` | `String @db.Uuid` | No | FK ไป `tb_stock_in.id` |
| `sequence_no` | `Int` | Yes | ลำดับบรรทัดภายในเอกสาร; default `1` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระสำหรับบรรทัด |
| `comment` | `String @db.VarChar` | Yes | Comment ข้อความอิสระสำหรับบรรทัด |
| `product_id` | `String @db.Uuid` | No | FK ไป `tb_product.id` บังคับ; ต้องมีแถว `tb_product` จริง ไม่งั้น `create()` ปฏิเสธด้วย `"Product not found: <ids>"` |
| `product_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot แบบ localised |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณขาเข้าใน UoM base Zod ฝั่ง client บังคับ `qty >= 1` (ไม่ใช่แค่ `> 0` — ปริมาณเศษส่วนต่ำกว่า 1 ถูกปฏิเสธโดยฟอร์ม); default `0` |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยใน base currency ผู้ใช้กรอกบนบรรทัด Stock-In (เติมเริ่มต้นจากค่าเฉลี่ยปัจจุบันของ location เป็นข้อเสนอ แก้ไขได้); default `0` ส่งตรงไปยัง `executeAdjustmentIn` เป็นต้นทุนของ layer ใหม่ |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit` คำนวณฝั่ง client; default `0` |
| `note` | `String @db.VarChar` | Yes | บันทึกแบบข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ส่งผ่านโดยไม่แก้ไขโดย `create()`; ไม่มี key ที่รู้จัก (ไม่มีฟิลด์ lot/expiry — โมดูลนี้ไม่มี UI สำหรับป้อน lot) |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` ส่งผ่านโดยไม่แก้ไข |
| `doc_version` | `Int @db.Integer` | No | ตัวนับ optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_in_id → tb_stock_in.id` (`NoAction`) Back-relations: many `tb_stock_in_detail_comment`
**Indexes:** `@@unique([stock_in_id, product_id, dimension, deleted_at])` เป็น `SIT1_stock_in_product_dimension_u`; `@@index([stock_in_id, product_id])` เป็น `SIT2_stock_in_product_idx`; `@@index([stock_in_id])` เป็น `SIT2_stock_in_idx`

ตารางคอมเมนต์ / ไฟล์แนบของโมดูลนี้ถูกแยกไปอีกหน้า — ดู [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/inventory-adjustment/01a-data-model-comments)

### 2.4 tb_stock_out

**Header เอกสาร adjustment ขาออก** เป็นภาพสะท้อนของ `tb_stock_in` ด้วย `so_no` / `so_date` ฟิลด์ workflow / status / audit เหมือนกัน (และไม่ถูกใช้เหมือนกันด้วย — ดู § 2.2) ลูกตาราง comment / detail / detail-comment ก็เหมือนกัน

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `so_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่เอกสาร |
| `so_no` | `String @db.VarChar` | Yes | เลขที่ stock-out ที่อ่านได้; unique ภายใน `deleted_at` สร้างผ่าน running-code service (รูปแบบ `STOCK-OUT`) |
| `description` | `String @db.VarChar` | Yes | คำอธิบายระดับ header; optional |
| `adjustment_type_id` | `String @db.Uuid` | Yes | FK ไป `tb_adjustment_type.id` (`onDelete: NoAction`) Picker กรองเหลือ `type = stock_out` ฝั่ง client เท่านั้น |
| `adjustment_type_code` | `String @db.VarChar` | Yes | Snapshot |
| `doc_status` | `enum_doc_status` | No | Schema default `draft`; `StockOutService.create()` เขียน `completed` เสมอ — headline finding เดียวกับ `tb_stock_in` (§ 2.2) |
| `location_id` | `String @db.Uuid` | Yes | FK ไป `tb_location.id` — location ต้นทางสำหรับขาออก |
| `location_code` | `String @db.VarChar` | Yes | Snapshot |
| `location_name` | `String @db.VarChar` | Yes | Snapshot |
| `workflow_id` | `String @db.Uuid` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_name` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_history` | `Json @db.JsonB` | Yes | ไม่ถูกใช้โดยโมดูลนี้; default `{}` |
| `workflow_current_stage` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_previous_stage` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `workflow_next_stage` | `String @db.VarChar` | Yes | ไม่ถูกใช้โดยโมดูลนี้ |
| `user_action` | `Json @db.JsonB` | Yes | ไม่ถูกใช้โดยโมดูลนี้; default `{}` |
| `last_action` | `enum_last_action` | Yes | Schema default `submitted`; ไม่พบว่าโมดูลนี้เปลี่ยนสถานะนี้ |
| `last_action_at_date` | `DateTime @db.Timestamptz(6)` | Yes | ไม่พบว่าโมดูลนี้ตั้งค่า |
| `last_action_by_id` | `String @db.Uuid` | Yes | ไม่พบว่าโมดูลนี้ตั้งค่า |
| `last_action_by_name` | `String @db.VarChar` | Yes | ไม่พบว่าโมดูลนี้ตั้งค่า |
| `note` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; ส่งผ่านโดยไม่แก้ไข ไม่มี key ที่รู้จัก |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; ส่งผ่านโดยไม่แก้ไข |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `adjustment_type_id → tb_adjustment_type.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`) Back-relations: many `tb_stock_out_detail`, many `tb_stock_out_comment`
**Indexes:** `@@unique([so_no, deleted_at])` เป็น `SO1_so_no_u`; `@@index([so_no])` เป็น `SO0_so_no_idx`

### 2.5 tb_stock_out_detail

**บรรทัด detail ต่อ product บนเอกสาร stock-out** รูปทรงคล้าย `tb_stock_in_detail` แต่ `cost_per_unit`/`total_cost` **ไม่เคยถูกเขียนโดย `create()` เลย** — การ insert ตั้งค่าเพียง `product_id`, `qty`, `description`, `note`, `info`, `dimension` ทั้งสองคอลัมน์ต้นทุนคงเป็นค่า default `0` ของ schema สำหรับทุกแถว stock-out detail Grid รายการซ่อนคอลัมน์ `cost_per_unit` ทั้งหมดสำหรับ Stock-Out (`ia-item-table.tsx` กรองออกจากคอลัมน์ที่แสดง) ต้นทุนจริงถูกแก้ไขอัตโนมัติโดย ledger ในเวลาที่เขียน — FIFO บริโภคจาก layer เก่าสุดก่อน, Average ใช้ค่าเฉลี่ยปัจจุบันของ BU — และอยู่เฉพาะบน `tb_inventory_transaction_detail`/`tb_inventory_transaction_cost_layer` ไม่ใช่ตารางนี้

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | Yes | FK ไป `tb_inventory_transaction.id`; ประทับตอนสร้าง |
| `stock_out_id` | `String @db.Uuid` | No | FK ไป `tb_stock_out.id` |
| `sequence_no` | `Int` | Yes | ลำดับบรรทัด; default `1` |
| `description` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `comment` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `product_id` | `String @db.Uuid` | No | FK ไป `tb_product.id` |
| `product_code` | `String @db.VarChar` | Yes | Snapshot |
| `product_name` | `String @db.VarChar` | Yes | Snapshot |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot แบบ localised |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณขาออก กรอกบวกบนฟอร์ม; default `0` Zod ฝั่ง client บังคับ `qty >= 1` |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | **เป็น `0` เสมอ** บนตารางนี้ — `create()` ไม่เคยตั้งค่าให้ stock-out (ดูหมายเหตุด้านบน) |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | **เป็น `0` เสมอ** บนตารางนี้ด้วยเหตุผลเดียวกัน; frontend คำนวณ preview ฝั่ง client (`useProductLastReceiving`) แต่ไม่เคย persist ที่นี่ |
| `note` | `String @db.VarChar` | Yes | ข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}` ส่งผ่านโดยไม่แก้ไข ไม่มี key ที่รู้จัก (ไม่มีฟิลด์ lot-override — โมดูลนี้ไม่มี UI สำหรับ lot) |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]` ส่งผ่านโดยไม่แก้ไข |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FKs: `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`); `stock_out_id → tb_stock_out.id` (`NoAction`) Back-relations: many `tb_stock_out_detail_comment`
**Indexes:** `@@unique([stock_out_id, product_id, dimension, deleted_at])` เป็น `SOT1_stock_out_product_dimension_u`; `@@index([stock_out_id, product_id])` เป็น `SOT2_stock_out_product_idx`; `@@index([stock_out_id])` เป็น `SOT2_stock_out_idx`

## 3. ความสัมพันธ์

```
tb_adjustment_type  (master ของ reason-code — ทิศทาง stock_in/stock_out, กรองฝั่ง client เท่านั้น)
    │  enum_adjustment_type ∈ {stock_in, stock_out, eop_in, eop_out}
    │
    ├─1──*──► tb_stock_in   (เอกสารขาเข้า — doc_status เป็น "completed" เสมอตอนสร้าง)
    │           │
    │           ├─1──*──► tb_stock_in_detail   (บรรทัดต่อ product, cost_per_unit ผู้ใช้กรอก)
    │           │           │
    │           │           ├──► tb_inventory_transaction (inventory_transaction_id, ประทับตอนสร้าง)
    │           │           ├──► tb_product
    │           │           └─1──*──► tb_stock_in_detail_comment
    │           │
    │           ├─1──*──► tb_stock_in_comment (comment ระดับ header)
    │           └──► tb_location  (location_id — ปลายทางของขาเข้า)
    │
    └─1──*──► tb_stock_out  (เอกสารขาออก — doc_status เป็น "completed" เสมอตอนสร้าง)
                │
                ├─1──*──► tb_stock_out_detail   (บรรทัดต่อ product, cost_per_unit/total_cost เป็น 0 เสมอ)
                │           │
                │           ├──► tb_inventory_transaction (inventory_transaction_id, ประทับตอนสร้าง)
                │           ├──► tb_product
                │           └─1──*──► tb_stock_out_detail_comment
                │
                ├─1──*──► tb_stock_out_comment
                └──► tb_location  (location_id — ต้นทางของขาออก)


create() เขียน header ที่ doc_status = completed พร้อมเขียนแถว ledger
ในทรานแซกชันฐานข้อมูลเดียวกัน — ไม่มีขั้นตอน posting แยกต่างหาก:
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

- **สองต้นเอกสารคู่ขนาน หนึ่งตัวจำแนก** `tb_stock_in` และ `tb_stock_out` เป็นโมเดล Prisma อิสระที่มีรูปทรงเหมือนกัน; คอลัมน์ `type` ของแถว `tb_adjustment_type` ถูกใช้โดย frontend เพื่อกรองว่า reason ตัวไหนแสดงบน picker ของเอกสารไหน แต่การตรวจสอบ header ฝั่ง backend ยืนยันเพียงว่าแถว `tb_adjustment_type` ที่อ้างอิงมีอยู่จริง — ไม่ตรวจซ้ำว่า `type` ตรงกับทิศทางของเอกสาร ข้อจำกัดนี้จึงเป็นฝั่ง client เท่านั้น
- **Back-reference ของ inventory transaction ถูกเติมตอนสร้าง ไม่ใช่ตอนขั้นตอน "post" ภายหลัง** แต่ละแถว detail ถือ `inventory_transaction_id` เป็น FK ที่ nullable แต่เนื่องจาก `create()` เขียนแถว ledger ในทรานแซกชันเดียวกับเอกสารเสมอ ทุกแถวจริงจึงมีค่านี้เติมแล้ว — ไม่มีช่วง draft ที่ค่านี้เป็น null ต่างจาก [good-receive-note](/th/inventory/good-receive-note) ที่ `save()` (ไม่ใช่ `commit()`) เป็นเหตุการณ์ mutation-และ-post เดี่ยวที่คล้ายกัน แต่อย่างน้อยเกิดขึ้นในขั้นตอนที่ต่างจากการสร้างเอกสาร
- **ไม่มีข้อมูล lot ที่ไหนใน UI ของโมดูลนี้เลย** Identity ของ lot (`current_lot_no` / `from_lot_no` บน `tb_inventory_transaction_detail`, `lot_no` / `lot_index` บน `tb_inventory_transaction_cost_layer`) ถูกสร้างขึ้นเชิงกลไกโดย ledger (prefix `ADI-`/`ADO-`) — ไม่มี lot-picker, ฟิลด์ป้อน lot หรือฟิลด์วันหมดอายุที่ไหนใน `ia-item-fields.tsx` / `ia-item-table.tsx` / `ia-form-schema.ts`
- **`adjustment_type_code` คือ snapshot ไม่ใช่ live join** เอกสารทั้งสอง persist รหัส snapshot บน header เพื่อ performance และ audit; การลบ / เปลี่ยนชื่อ reason code หลัง post ไม่เปลี่ยนเอกสารประวัติย้อนหลัง
- **การประกาศ `@relation` FK ทั้งหมดที่ระบุชัดเจนใช้ `onDelete: NoAction, onUpdate: NoAction`** — ความถูกต้องของการอ้างอิงรักษาโดย soft-delete ระดับ application (`deleted_at`) ไม่ใช่ cascade

## 4. Enums

- **`enum_adjustment_type`**: ตัวจำแนกทิศทางบน `tb_adjustment_type.type` สี่ค่า ไม่มี default ประกาศ:
  - `stock_in` — กรองเข้า reason picker ของ Stock-In
  - `stock_out` — กรองเข้า reason picker ของ Stock-Out
  - `eop_in` / `eop_out` — ใช้โดย engine period-end (แสดงผ่านหน้ารายการ gateway ที่รวม `inventory-adjustments`, tag โดย filter `wantIn`/`wantOut` ใน `inventory-adjustments.service.ts`); ไม่ปรากฏใน reason picker ของหน้าจอสร้างทั้งสองแบบ
- **`enum_doc_status`**: คอลัมน์วงจรชีวิตเอกสารบน `tb_stock_in.doc_status` / `tb_stock_out.doc_status` Schema default `draft` มีห้าค่าบน enum ที่ใช้ร่วมกัน แต่มีเพียงสองค่าที่โมดูลนี้กำหนดเองจริง ๆ:
  - `draft` — เป็นเพียง default ของ schema; ไม่เคยถูกกำหนดโดย `create()`
  - `in_progress` — ไม่เคยถูกกำหนดที่ไหนในโค้ดของโมดูลนี้
  - `completed` — ค่าที่ `create()` เขียนเสมอ ไม่ว่า client จะส่ง `doc_status` มาเป็นอะไรก็ตาม
  - `cancelled` — ไม่เคยถูกกำหนดที่ไหนในโค้ดของโมดูลนี้
  - `voided` — กำหนดเฉพาะโดย void endpoint (`voidStockIn` / `voidStockOut`) ซึ่งตั้งค่า `deleted_at` ไปพร้อมกันด้วย (ดูหมายเหตุ § 2.2) — แต่ปุ่ม Void ของ UI เข้าไม่ถึงสำหรับเอกสารที่ persist แล้ว (ดู landing page § 1) การเปลี่ยนสถานะนี้จึงต้องการการเรียก API โดยตรงในปัจจุบัน
- **`enum_last_action`**: คอลัมน์มีอยู่ (`submitted`, `approved`, `reviewed`, `rejected`, default `submitted`) แต่ไม่พบว่า `stock-in.service.ts` / `stock-out.service.ts` อ่านหรือเขียน
- **`enum_comment_type`**: บน `tb_stock_in_comment.type` / `tb_stock_in_detail_comment.type` / `tb_stock_out_comment.type` / `tb_stock_out_detail_comment.type` Default `user` สองค่า: `user`, `system`

## 5. หมายเหตุเกี่ยวกับ carmen/docs

`../carmen/docs/inventory-adjustment/` บรรยายการออกแบบที่ศูนย์กลางอยู่ที่เอนทิตี `InventoryAdjustment` เดี่ยวที่ embed array `items[]`/`lots[]`, การลงบัญชี journal ใน GL และห่วงอนุมัติหลายบทบาทที่ gate ด้วย threshold (Store Keeper → Inventory Controller → Finance) ไม่มีข้อไหนตรงกับการทำงานจริง:

| # | กรอบของ carmen/docs | สิ่งที่โค้ดทำจริง |
|---|------|------|
| 1 | เอนทิตี `InventoryAdjustment` เดี่ยวพร้อม discriminator `type: 'IN' \| 'OUT'` | สองตารางอิสระ `tb_stock_in` และ `tb_stock_out` ไม่มี parent ร่วม — กรอบนี้ถูกต้องและคงไว้ ดู § 3 |
| 2 | Interface `AdjustmentReason` พร้อม `type: 'IN' \| 'OUT' \| 'BOTH'`, `requiresDocument`, `requiresQualityCheck`, `glAccount` | `tb_adjustment_type` มีเพียง `code`, `name`, `type` (`enum_adjustment_type`, ไม่มีค่า `BOTH`), `description`, `is_active`, `note` ไม่มีฟิลด์ `glAccount`/`requiresDocument`/`requiresQualityCheck` และไม่มีโค้ดใดในทั้ง frontend และ backend อ่านหรือเขียน key ชื่อเหล่านี้ใน JSON `info`/`dimension` เลย — นี่ไม่ใช่แค่ความแตกต่างระหว่าง JSON กับคอลัมน์ แต่แนวคิดนี้ไม่มีอยู่จริง |
| 3 | วงจรชีวิตสามสถานะ `Draft → Posted → Void` พร้อมห่วงอนุมัติที่ gate ด้วย threshold ไปยัง Inventory Controller / Finance | ไม่มีขั้นตอนอนุมัติเลย: `create()` เขียน `completed` เสมอ ไม่ว่าต้นทุนหรือ threshold ใด ๆ — การค้นหาทั่ว repo ไม่พบคำว่า `threshold` ในโค้ด backend ของโมดูลนี้เลย ดู § 4 |
| 4 | `journalEntries: JournalEntry[]` ที่ embed | ไม่มีโค้ด GL/journal ที่ไหนในโมดูลนี้ (หรือตามรอบก่อนหน้าของ module map นี้ — ไม่มีที่ไหนใน backend สำหรับ GRN/PO/SR เช่นกัน) Adjustment เป็นการเคลื่อนไหวปริมาณ/มูลค่า ledger ล้วน ๆ |
| 5 | เลขที่อ้างอิงถูกนัยว่าเป็น `id` ของ record | เลขที่อ้างอิงที่อ่านได้คือ `si_no` / `so_no` สร้างผ่าน running-code service; `id` คือ UUID primary key |
| 6 | "ต้องแนบเอกสารประกอบ" สำหรับ reason บางตัว | Comments (`tb_stock_in_comment`/`tb_stock_out_comment`, มี JSON array `attachments`) เป็นของจริงและใช้ได้อย่างอิสระ แต่ไม่มีกฎตรวจสอบใดผูก reason code กับการแนบเอกสารบังคับ — แนวคิด "reason ที่ต้องแนบเอกสาร" ไม่มีอยู่ทั้งใน schema และโค้ด |

## 6. แหล่งอ้างอิง

- **หลัก (แหล่งความจริง):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`tb_adjustment_type`, `tb_stock_in`, `tb_stock_in_detail`, `tb_stock_in_comment`, `tb_stock_in_detail_comment`, `tb_stock_out`, `tb_stock_out_detail`, `tb_stock_out_comment`, `tb_stock_out_detail_comment`; enums `enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`)
- **Backend services:** `apps/micro-business/src/inventory/stock-in/stock-in.service.ts`, `.../stock-out/stock-out.service.ts`, `.../inventory-transaction/inventory-transaction.service.ts` (`executeAdjustmentIn`/`executeAdjustmentOut`), `apps/backend-gateway/src/application/inventory-adjustments/inventory-adjustments.service.ts` (gateway read-only ที่รวม stock-in + stock-out สำหรับหน้ารายการและ print viewer)
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/` (`ia-form.tsx`, `ia-form-schema.ts`, `ia-item-fields.tsx`, `ia-item-table.tsx`)
- **รอง (การตรวจสอบไขว้แนวคิด แทนที่ด้วยโค้ด — ดู § 5):** `../carmen/docs/inventory-adjustment/INV-ADJ-Overview.md`, `INV-ADJ-PRD.md`, `INV-ADJ-Business-Requirements.md`, `INV-ADJ-Business-Logic.md`, `INV-ADJ-Component-Structure.md`
- E2E: ไม่มี spec `inventory-adjustment` เฉพาะ; `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` ครอบคลุมเฉพาะหน้าจอ master data ของ reason code
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ledger ร่วม — `tb_inventory_transaction` / `tb_inventory_transaction_detail` / `tb_inventory_transaction_cost_layer`), [costing](/th/inventory/costing) (การสร้าง FIFO layer บน Stock-In, การบริโภค FIFO / คำนวณค่าเฉลี่ยถ่วงน้ำหนักใหม่บน Stock-Out), [physical-count](/th/inventory/physical-count) (สร้างแถว `tb_stock_in`/`tb_stock_out` โดยตรงตอน commit ผลต่าง — ดู landing page § 2), [product](/th/inventory/product)
