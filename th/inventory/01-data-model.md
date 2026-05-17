---
title: คลังสินค้า — แบบจำลองข้อมูล (Inventory — Data Model)
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล inventory
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า — แบบจำลองข้อมูล (Inventory — Data Model)

> **At a Glance**
> **ตาราง:** `tb_inventory_transaction` &nbsp;·&nbsp; `tb_inventory_transaction_detail` &nbsp;·&nbsp; `tb_inventory_transaction_cost_layer` &nbsp;·&nbsp; `tb_location` &nbsp;·&nbsp; `tb_product_location` &nbsp;·&nbsp; `tb_period` &nbsp;·&nbsp; `tb_period_snapshot`
> **ผู้ใช้งาน:** Developer / Auditor (อ้างอิงสำหรับนักพัฒนา)
> **FK สำคัญ:** `inventory_doc_no` เป็น **polymorphic** (ไม่มี `@relation`) — resolve ไปยัง `tb_good_received_note` / `tb_store_requisition` / `tb_stock_in` / `tb_stock_out` / `tb_credit_note` / `tb_period` ตาม `inventory_doc_type`; cost-layer `→ tb_period`; โมดูลฝั่ง source กลับมาเข้าหาผ่าน column UUID `inventory_transaction_id`
> **รูปแบบ audit:** `created_*` / `updated_*` / `deleted_*` มาตรฐานบนตารางส่วนใหญ่; **`tb_inventory_transaction_detail` ไม่มี soft-delete** — การกลับรายการ post compensating row แทน ไม่มี `tb_stock_balance` — on-hand derive จาก cost-layer rows ตั้งแต่ snapshot ล่าสุด

> **Source of truth:** Prisma schema ของ Backend ต้องอ่านเหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใต้แต่ละ package เป็น auto-generated copies และไม่ใช่ของจริง

## 1. ภาพรวม

โมดูล Inventory คือ **ระบบบันทึกหลักของการเคลื่อนไหวสต๊อกและการตีมูลค่า on-hand** ทั่วทั้งทรัพย์สิน ไม่เหมือนโมดูลที่เน้นเอกสาร ([[purchase-request]], [[purchase-order]], [[good-receive-note]]) inventory ไม่อาศัยอยู่บน tree header → detail → comment เดียว มันคือ **family ของ record ที่เชื่อมกันด้วย movement** — ทุกการเปลี่ยนปริมาณในระบบไหลผ่าน `tb_inventory_transaction` (header ของ movement) และลูก `tb_inventory_transaction_detail` (บรรทัด ledger ต่อสินค้า / ต่อ lot) โดยมี record คงรูปแบบของ cost-flow เก็บบน `tb_inventory_transaction_cost_layer` (FIFO / weighted-average layers, key โดย `lot_no` และ `lot_index`) Location ถูกกำหนดบน `tb_location` ด้วย `location_type` (`inventory`, `direct` หรือ `consignment`) ที่กำหนดว่า movement post ไปยังสินทรัพย์ inventory ค่าใช้จ่าย หรือ memo register พารามิเตอร์สต๊อกต่อสินค้า / ต่อตำแหน่ง (par, min, max, reorder) อยู่บน `tb_product_location` ขอบเขตงวดถูก anchor โดย `tb_period` (งวดบัญชี) และ `tb_period_snapshot` (row opening / closing balance ที่ lock ต่อ `period × location × product × lot`); enum สถานะของงวด (`open` → `closed` → `locked`) gate การ post ย้อนหลัง

โมดูลตั้งอยู่ **ที่ศูนย์กลางของห่วงโซ่ procure-to-pay / requisition-to-consume** เป็นปลายน้ำของ [[good-receive-note]] (การรับ post `enum_inventory_doc_type = good_received_note` transactions), [[store-requisition]] (การเบิก post `store_requisition` transactions), [[physical-count]] และ [[spot-check]] (การนับ post adjustment_in / adjustment_out transactions) และ [[inventory-adjustment]] (manual stock-in / stock-out transactions) เป็นต้นน้ำของ [[costing]] ซึ่งอ่าน cost-layer ledger เพื่อคำนวณ COGS และ unit-cost ป้อนกลับไปยังโมดูล source การออกแบบ single-table-as-ledger เป็นเจตนา: ทุก movement ของสต๊อกที่เป็นเจ้าของ ไม่ว่าจะมาจากโมดูล source ใด จะลงใน `tb_inventory_transaction` เพื่อให้ trace ทั้งไปและกลับ (movement → cost layer → period snapshot → on-hand) เดียวรองรับทั้ง audit และ recall

จุดโครงสร้างที่น่าสังเกต: **ไม่มี `tb_stock_balance` model ใน canonical Prisma schema** ยอด on-hand ถูก derive — ณ จุดเวลาใด ๆ ยอดปัจจุบันสำหรับ `(location_id, product_id, lot_no)` คือผลรวมเชิงพีชคณิตของ `tb_inventory_transaction_cost_layer.in_qty` ที่ไม่ถูก soft-delete ทั้งหมด ลบ `out_qty` สำหรับ lot นั้นตั้งแต่ `closing_qty` ของ snapshot งวดล่าสุด `closing_qty` ของ period snapshot คือ anchor ที่ lock; movement หลัง snapshot คือ delta เทียบกับมัน `inventory-management-prd.md` และเอกสารอนุพันธ์อ้างถึงเอนทิตี `InventoryStatus` / `StockBalance` ที่มี column `QuantityOnHand`, `LastUnitCost`, `TotalCost` — interface นั้นเป็น application-layer-derived ไม่ใช่ row ใน schema ดู Section 5 สำหรับความแตกต่างนี้

## 2. เอนทิตี

### 2.1 tb_inventory_transaction

**header ของ movement** ทุกการเปลี่ยนปริมาณในระบบสร้างเพียง row เดียวที่นี่ จำแนกโดย `inventory_doc_type` (โมดูลต้นน้ำที่สร้าง movement) และชี้ไปยังเอกสาร source ผ่าน `inventory_doc_no` ไม่มี `doc_status`, ไม่มี `vendor_id`, ไม่มี `currency_id` และไม่มี header totals — inventory transaction คือ record ledger ที่ post แล้ว ไม่ใช่เอกสาร workflow Header ไม่มีการ roll-up ทางการเงินระดับ header; การตีมูลค่าอยู่ทั้งหมดบน detail rows และ cost-layer children

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()` |
| `inventory_doc_type` | `enum_inventory_doc_type` | No | จำแนกโมดูล source: `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open` กำหนดว่า `inventory_doc_no` resolve เข้าตารางเอกสาร source ใด |
| `inventory_doc_no` | `String @db.Uuid` | No | UUID ของเอกสาร source (เช่น `tb_good_received_note.id`, `tb_store_requisition.id`, `tb_stock_in.id`) Resolve ในระดับแอปตาม `inventory_doc_type`; ไม่มี Prisma `@relation` เพราะตารางเป้าหมายเป็น polymorphic |
| `note` | `String @db.VarChar` | Yes | บันทึก free-text แนบกับ movement |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension สำหรับ metadata movement เฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension (project, cost-centre, job code); default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | user id ที่ post movement |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดตล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete; non-null หมายถึงถูก reverse เชิงตรรกะ |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` **ไม่มี FKs** ประกาศด้วย `@relation` บน column เอกสาร source — link source เป็น polymorphic และ resolve ที่ application layer Back-relations: many `tb_inventory_transaction_detail`, many `tb_credit_note_detail`, many `tb_stock_in_detail`, many `tb_stock_out_detail`, many `tb_store_requisition_detail`
**Indexes:** `@@index([inventory_doc_no])` เป็น `inventorytransaction_inventory_doc_no_idx`; `@@index([inventory_doc_type])` เป็น `inventorytransaction_inventory_doc_type_idx`; `@@index([inventory_doc_type, inventory_doc_no])` เป็น `inventorytransaction_inventory_doc_type_inventory_doc_no_idx`

### 2.2 tb_inventory_transaction_detail

**บรรทัด ledger ต่อสินค้า / ต่อ lot** หนึ่ง transaction row สร้าง detail row หนึ่ง row ต่อสินค้าที่ได้รับผลกระทบ (ในกรณีส่วนใหญ่) — detail row คือสิ่งที่ถือ `qty`, `cost_per_unit`, `total_cost`, location และ lot-trace fields `from_lot_no` (lot source เมื่อ movement บริโภคจาก layer ที่มีอยู่) และ `current_lot_no` (lot ที่สร้างใหม่หรือได้รับผลกระทบจาก movement) Detail ยังเป็นสะพานเข้าสู่ `tb_inventory_transaction_cost_layer` — ทุก cost-flow effect (การสร้าง FIFO layer, การ recompute weighted-average, EOP rollforward) อยู่บน cost-layer rows ที่ห้อยจากเอนทิตีนี้

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | No | FK ไปยัง `tb_inventory_transaction.id` |
| `from_lot_no` | `String @db.VarChar` | Yes | lot source ที่ movement บริโภคจาก (set บน issues / transfers / adjustments-out ที่ FIFO เลือก layer ที่มีอยู่) |
| `current_lot_no` | `String @db.VarChar` | Yes | lot ที่สร้างใหม่โดย movement นี้ (set บน receipts / adjustments-in / transfers-in ที่เปิด layer ใหม่) |
| `location_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_location.id` Nullable สำหรับ rollup ระดับระบบ (close / open) ไม่มี `@relation` ประกาศบน column นี้ |
| `location_code` | `String @db.VarChar` | Yes | snapshot ของ location code |
| `product_id` | `String @db.Uuid` | No | FK reference ไปยัง `tb_product.id` จำเป็น ไม่มี `@relation` ประกาศบน column นี้ |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ signed ใน base UoM: บวก = inbound (receipt / adjustment-in) ลบ = outbound (issue / adjustment-out) Default `0` |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยใน base currency ณ เวลา post; default `0` สำหรับ inbound คือ layer cost; สำหรับ outbound คือ cost ที่เลือกโดยกฎ costing (FIFO จาก layer ที่บริโภค หรือ moving-average ณ เวลา post) |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit`; default `0` Signed ตาม `qty` |
| `note` | `String @db.VarChar` | Yes | บันทึก free-text |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |

**Constraints:** `@id` บน `id` FK `inventory_transaction_id → tb_inventory_transaction.id` (`NoAction`) Note: `location_id` และ `product_id` เก็บบน row แต่ **ไม่มี Prisma `@relation`** — เป็น lookup ที่ resolve ระดับแอป ไม่มี column soft-delete บนเอนทิตีนี้ (ไม่เหมือนอื่น ๆ ส่วนใหญ่); การกลับรายการทำโดยเขียน compensating transaction ที่ negate `qty` ไม่ใช่โดย `deleted_at`
**Indexes:** `@@index([inventory_transaction_id])` เป็น `inventorytransactiondetail_inventory_transaction_id_idx`

### 2.3 tb_inventory_transaction_cost_layer

**record cost-flow** — store canonical ของสถานะ FIFO / weighted-average หนึ่ง cost-layer row ต่อ event การบริโภคหรือสร้าง layer ต่อ movement สำหรับ movement inbound row ถือ `in_qty > 0` และ `lot_no` / `lot_index` ใหม่; สำหรับ outbound row ถือ `out_qty > 0` และ `from_lot_no` ที่ resolve โดยการเรียง FIFO บน `lot_seq_no` Row ยังเก็บ `average_cost_per_unit` เพื่อให้สินค้า weighted-average อ่าน moving average หลัง movement โดยไม่ต้อง re-aggregate ประวัติทั้งหมด `at_period` (`YYMM`) และ `period_id` ผูก layer กับงวดบัญชีสำหรับ snapshot rollup

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_inventory_transaction_detail.id` |
| `lot_no` | `String @db.VarChar` | Yes | ตัวระบุ lot — สำหรับ inbound คือ lot ใหม่ที่สร้าง; สำหรับ outbound คือ lot ที่บริโภคจาก |
| `lot_index` | `Int` | No | หมายเลขลำดับภายใน lot; default `1` Lots ที่มี `lot_no` เดียวกัน (เช่น split หรือ re-opened) แยกแยะโดย `lot_index` |
| `location_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_location.id` Nullable สำหรับ rows period-rollup |
| `location_code` | `String @db.VarChar` | Yes | Snapshot |
| `lot_at_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่มีผลของ layer (วันรับสำหรับ inbound, วันบริโภคสำหรับ outbound) |
| `lot_seq_no` | `Int` | Yes | anchor การเรียง FIFO ภายใน `(location_id, product_id)`; default `1` `lot_seq_no` ที่ต่ำกว่าถูกบริโภคก่อนภายใต้ FIFO |
| `product_id` | `String @db.Uuid` | Yes | FK reference ไปยัง `tb_product.id` |
| `parent_lot_no` | `String @db.VarChar` | Yes | เมื่อ layer ถูกสร้างจาก transfer / split / re-pack คือ lot ต้นกำเนิด |
| `period_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_period.id` — งวดบัญชีที่บรรจุ event ของ layer นี้ |
| `at_period` | `String @db.VarChar` | Yes | งวดในรูป `YYMM` (denormalised จาก `tb_period.period`) |
| `transaction_type` | `enum_transaction_type` | Yes | จำแนกอิสระจาก `inventory_doc_type`: `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period` |
| `in_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ inbound; default `0` Non-zero สำหรับ event layer inbound |
| `out_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ outbound; default `0` Non-zero สำหรับ event layer outbound |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยบน event layer นี้; default `0` |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `(in_qty − out_qty) × cost_per_unit` (หรือเทียบเท่าเฉพาะกฎ); default `0` |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนผลต่างที่ใช้สำหรับ credit-note-amount adjustments และ EOP price-revaluation; default `0` |
| `average_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | moving-average unit cost หลัง movement ที่ `(location_id, product_id)`; default `0` |
| `note` | `String @db.VarChar` | Yes | Free-text |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FKs: `inventory_transaction_detail_id → tb_inventory_transaction_detail.id` (`NoAction`); `period_id → tb_period.id` (`NoAction`) Note: `location_id` และ `product_id` เก็บโดยไม่มี `@relation` ชื่อ map `tb_inventory_transaction_clos_inventory_transaction_detail_fkey` สะท้อนการตั้งชื่อ "closing balance" ก่อนหน้า
**Indexes:** `@@unique([lot_no, lot_index])` เป็น `inventorytransactionclosingbalance_lotno_lot_index_u` (lot identity); `@@index([lot_no, lot_index])` เป็น `inventorytransactioncostlayer_lotno_lot_index_idx`

### 2.4 tb_location

**คำจำกัดความของ storage / cost-centre** Location เป็น key ที่สอง (หลัง `product_id`) ของทุกยอดและ movement enum `location_type` คือการตั้งค่าที่ส่งผลที่สุดบน location: กำหนดว่าการ post จะกระทบสินทรัพย์ inventory (`inventory`), ค่าใช้จ่ายแผนก (`direct`) หรือ memo register (`consignment`)

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | location code ที่อ่านได้ |
| `name` | `String @db.VarChar` | No | ชื่อแสดง |
| `location_type` | `enum_location_type` | No | `inventory` (default — สินทรัพย์สต๊อกที่เป็นเจ้าของ), `direct` (cost centre แบบตรง — bypass inventory, post เข้าค่าใช้จ่าย), `consignment` (vendor-owned — memo เท่านั้น) |
| `description` | `String` | Yes | Free-text |
| `delivery_point_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_delivery_point.id` |
| `delivery_point_name` | `String @db.VarChar` | Yes | Snapshot |
| `physical_count_type` | `enum_physical_count_type` | No | `no` (default — location ไม่อยู่ภายใต้ physical count ตามตาราง) หรือ `yes` (นับ ณ สิ้นงวด) |
| `is_active` | `Boolean` | Yes | Default `true` |
| `note` | `String @db.VarChar` | Yes | Free-text |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `delivery_point_id → tb_delivery_point.id` (`NoAction`) Back-relations ครอบคลุมตารางปลายน้ำหลายตาราง: `tb_good_received_note_detail`, `tb_purchase_request_detail`, `tb_stock_in`, `tb_stock_out`, `tb_count_stock`, `tb_spot_check`, `tb_physical_count`, `tb_product_location`, `tb_user_location`, `tb_credit_note_detail`, `tb_store_requisition_from`, `tb_store_requisition_to`, `tb_location_comment`, `tb_purchase_request_template_detail`, `tb_purchase_order_detail_tb_purchase_request_detail`
**Indexes:** `@@unique([name, deleted_at])` เป็น `location_name_u`; `@@index([name])` เป็น `location_name_idx`; `@@index([code])` เป็น `location_code_idx`

### 2.5 tb_product_location

**row stock-policy ต่อสินค้า / ต่อ location** ถือปริมาณ par / min / max / reorder ที่ใช้โดยกฎ replenishment และ alert on-hand; **ไม่** เก็บ on-hand qty (derive จาก cost-layer ledger)

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` |
| `location_id` | `String @db.Uuid` | Yes | FK ไปยัง `tb_location.id` |
| `min_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ต่ำกว่านี้ trigger alert replenishment; default `0` |
| `max_qty` | `Decimal @db.Decimal(20, 5)` | Yes | เกินนี้ trigger alert over-stock; default `0` |
| `re_order_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณสั่งที่แนะนำเมื่อ on-hand ตกต่ำกว่า `min_qty`; default `0` |
| `par_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ระดับ par สำหรับการเติม outlet; default `0` |
| `note` | `String @db.VarChar` | Yes | Free-text |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension |
| `doc_version` | `Int` | No | counter optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FKs: `product_id → tb_product.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`)
**Indexes:** `@@unique([product_id, location_id, deleted_at])` เป็น `product_location_product_id_location_id_u`; `@@index([product_id, location_id])` เป็น `product_location_product_id_location_id_idx`

### 2.6 tb_period

**header งวดบัญชี** — ของพื้นฐาน time-boundary ที่กระบวนการ period-end ดำเนินการบน enum สถานะของงวด (`open`, `closed`, `locked`) gate ว่าการ post ย้อนหลังเข้างวดนี้ถูกยอมรับหรือไม่; การตรวจสอบฝั่ง movement อ่านสถานะนี้ ณ เวลา post

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `period` | `String @db.VarChar` | No | รูป `YYMM` (เช่น `2604` สำหรับ April 2026) |
| `fiscal_year` | `Int @db.Integer` | No | 4-digit fiscal year |
| `fiscal_month` | `Int @db.Integer` | No | 1-12 |
| `start_at` | `DateTime @db.Timestamptz(6)` | No | เริ่มงวด |
| `end_at` | `DateTime @db.Timestamptz(6)` | No | สิ้นงวด |
| `status` | `enum_period_status` | No | `open` (default — รับ posting), `closed` (ไม่มี movement ใหม่, snapshot คำนวณแล้ว), `locked` (audit แล้วและ immutable) |
| `note` | `String @db.VarChar` | Yes | Free-text |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` Back-relations: many `tb_period_snapshot`, many `tb_inventory_transaction_cost_layer`, many `tb_period_comment`, many `tb_physical_count_period`
**Indexes:** `@@unique([period, deleted_at])` เป็น `period_period_u`; `@@unique([fiscal_year, fiscal_month, deleted_at])` เป็น `period_fiscal_year_month_u`; `@@index([fiscal_year, fiscal_month])` เป็น `period_fiscal_year_month_idx`; `@@index([period])` เป็น `period_period_idx`

### 2.7 tb_period_snapshot

**row balance opening / closing ที่ lock ต่อ period × location × product × lot** เขียน ณ ปิดงวดเป็น anchor audit สำหรับงวดที่ปิด และเป็น opening สำหรับงวดถัดไป ถือ column qty และ cost ของ opening / movement-bucket / closing เพื่อให้รายงานอ่านกิจกรรม net ของงวดได้โดยตรงโดยไม่ต้อง re-walk cost-layer ledger

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `period_id` | `String @db.Uuid` | No | FK ไปยัง `tb_period.id` |
| `snapshot_at` | `DateTime @db.Timestamptz(6)` | No | timestamp มีผลของ snapshot |
| `location_id` | `String @db.Uuid` | No | FK reference ไปยัง `tb_location.id` |
| `location_code` | `String @db.VarChar` | Yes | Snapshot |
| `location_name` | `String @db.VarChar` | Yes | Snapshot |
| `product_id` | `String @db.Uuid` | No | FK reference ไปยัง `tb_product.id` |
| `product_code` | `String @db.VarChar` | Yes | Snapshot |
| `product_name` | `String @db.VarChar` | Yes | Snapshot |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot ที่ localised |
| `product_sku` | `String @db.VarChar` | Yes | SKU snapshot |
| `lot_no` | `String @db.VarChar` | Yes | ตัวระบุ lot (เมื่อ batch-tracked) |
| `lot_index` | `Int` | Yes | Default `1` |
| `lot_at_date` | `DateTime @db.Timestamptz(6)` | Yes | วันที่ lot ดั้งเดิม |
| `lot_seq_no` | `Int` | Yes | ลำดับ FIFO |
| `opening_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ on-hand opening สำหรับงวด |
| `opening_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วย opening |
| `opening_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `opening_qty × opening_cost_per_unit` |
| `receipt_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ inbound รวมระหว่างงวด |
| `receipt_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุน inbound รวมระหว่างงวด |
| `issue_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ outbound รวมระหว่างงวด |
| `issue_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุน outbound รวมระหว่างงวด |
| `adjustment_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ adjustment net ระหว่างงวด |
| `adjustment_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุน adjustment net ระหว่างงวด |
| `closing_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ปริมาณ on-hand closing (anchor งวด) |
| `closing_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วย closing |
| `closing_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `closing_qty × closing_cost_per_unit` |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | ผลต่างจากการกระทบยอด (ปกติจาก physical-count adjustment ที่จับใน period) |
| `note` | `String @db.VarChar` | Yes | Free-text |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `period_id → tb_period.id` (`NoAction`) Note: `location_id` และ `product_id` เก็บโดยไม่มี `@relation`
**Indexes:** `@@unique([period_id, snapshot_at, deleted_at])` เป็น `periodsnapshot_period_id_snapshot_at_u`; `@@index([period_id, snapshot_at])` เป็น `periodsnapshot_period_id_snapshot_at_idx`

## 3. ความสัมพันธ์

```
tb_inventory_transaction        (movement header — polymorphic source)
    │  inventory_doc_type ∈ {good_received_note, credit_note, store_requisition,
    │                        stock_in, stock_out, close, open}
    │  inventory_doc_no → application-resolved (no @relation):
    │       good_received_note → tb_good_received_note.id
    │       credit_note        → tb_credit_note.id
    │       store_requisition  → tb_store_requisition.id
    │       stock_in           → tb_stock_in.id
    │       stock_out          → tb_stock_out.id
    │       close / open       → tb_period.id
    │
    │ * inventory_transaction_id
    ▼
tb_inventory_transaction_detail (per-product/lot ledger line)
    │  qty (signed), cost_per_unit, total_cost,
    │  from_lot_no (outbound source layer), current_lot_no (inbound new layer)
    │
    │ FK references (no @relation declared on these)
    ├──► tb_location  (location_id)
    └──► tb_product   (product_id)
    │
    │ * inventory_transaction_detail_id
    ▼
tb_inventory_transaction_cost_layer  (FIFO / weighted-average layer event —
                                       the canonical cost-flow record)
    │  transaction_type ∈ {good_received_note, transfer_in, transfer_out,
    │                      issue, adjustment_in, adjustment_out,
    │                      credit_note_amount, credit_note_quantity,
    │                      eop_in, eop_out, close_period, open_period}
    │  in_qty / out_qty, cost_per_unit, average_cost_per_unit,
    │  lot_no, lot_index, lot_seq_no (FIFO ordering anchor),
    │  parent_lot_no (transfer/split source)
    │
    └──► tb_period   (period_id — accounting period containing the layer event)


tb_location ──1──*──► tb_product_location  (per-product stock policy:
    │                                        min/max/par/reorder — no on-hand)
    │
    └──► tb_delivery_point  (delivery_point_id)


tb_period ──1──*──► tb_period_snapshot  (locked period × location × product × lot
                                          balance row — opening/closing anchor)


tb_inventory_transaction is reached BACK from the source modules:
    tb_good_received_note_detail_item.inventory_transaction_id  (GRN receipts)
    tb_stock_in_detail.inventory_transaction_id                  (manual stock-in)
    tb_stock_out_detail.inventory_transaction_id                 (manual stock-out)
    tb_store_requisition_detail.inventory_transaction_id         (requisition issues)
    tb_credit_note_detail.inventory_transaction_id               (credit-note adj)

    All five of these source-side columns are UUID references with NO Prisma @relation;
    the link runs source → inventory in the source module's @relation set,
    and inventory → source via the polymorphic inventory_doc_no.
```

หมายเหตุ:

- **ขับเคลื่อนด้วย movement ไม่ใช่ balance-stored** ไม่มี row `tb_stock_balance` ที่ระบบอัปเดตในทุก transaction ยอด on-hand ปัจจุบันที่ `(location_id, product_id, lot_no)` คำนวณเป็น `last_snapshot.closing_qty + Σ (cost_layer.in_qty − cost_layer.out_qty)` ตั้งแต่ snapshot นั้น Query ที่ไวต่อ performance ใช้ materialised view หรืออ่านจาก `last_unit_cost` snapshot ที่ cache ไว้ในโมดูล source แต่คำตอบ canonical คือผลรวมเชิงพีชคณิตเสมอ
- **Link source แบบ polymorphic** `tb_inventory_transaction.inventory_doc_type` + `inventory_doc_no` เป็นทางเดียวที่จะ walk กลับไปยังเอกสารต้นกำเนิด; ไม่มี Prisma `@relation` เพราะตารางเป้าหมายแตกต่าง ทิศทางย้อนกลับ (column `inventory_transaction_id` ฝั่ง source บนทุกตาราง source-detail) คือ link polymorphic แบบสมมาตรโดยไม่มี `@relation`
- **enum สองตัวสำหรับ "movement type"** `enum_inventory_doc_type` จำแนก **โมดูล source** (`good_received_note`, `store_requisition` เป็นต้น) ในขณะที่ `enum_transaction_type` บน cost-layer จำแนก **cost-flow effect** (`good_received_note`, `issue`, `transfer_in`, `eop_in`, `close_period` เป็นต้น) ทับซ้อนกันแต่ไม่เหมือนกัน — GRN receipt เป็น `good_received_note` ทั้งสองแบบ แต่ store-requisition transfer สร้าง cost-layer rows สองตัว (`transfer_out` จาก source location, `transfer_in` ไป destination) ภายใต้เอกสาร `store_requisition` ตัวเดียว
- **ไม่มี header-level totals บน transaction** ไม่เหมือนเอกสาร (GRN / PO / PR) `tb_inventory_transaction` ไม่มี roll-up columns รวมผลรวม detail rows หรือ cost layers สำหรับการตีมูลค่า; period snapshot เป็นที่เดียวที่มี bucket totals pre-aggregated
- **soft-delete asymmetry** เอนทิตี inventory ส่วนใหญ่รองรับ `deleted_at` soft-delete `tb_inventory_transaction_detail` เป็นข้อยกเว้น — ไม่มี column soft-delete ในการกลับรายการ detail row ที่ post แล้ว ให้ post compensating transaction ที่ negate `qty` แทนการ soft-delete; นี่รักษา audit trail และเป็นเส้นทางที่ credit-note และ period-end-EOP flows ใช้
- **การประกาศ `@relation` FK explicit ทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction`** — referential integrity ถูกรักษาโดย soft-delete ระดับแอป (`deleted_at`) และโดย period-lock guard ไม่ใช่โดย cascade

## 4. Enums

- **`enum_inventory_doc_type`**: จำแนกโมดูล source บน `tb_inventory_transaction.inventory_doc_type` เจ็ดค่า ไม่มี default ประกาศบน column (ทุก transaction ต้องระบุ):
  - `good_received_note` — receipt จาก [[good-receive-note]] commit (`saved → committed`)
  - `credit_note` — vendor credit-note adjustment (การแก้ไขหลังรับ; เป็น quantity-only หรือ amount-only ได้)
  - `store_requisition` — issue / transfer ภายในจาก [[store-requisition]] approve / dispatch
  - `stock_in` — manual stock-in (เอกสาร `tb_stock_in` — โดยปกติใช้สำหรับ inventory-adjustment-in, found-stock หรือการแก้ไข count overage)
  - `stock_out` — manual stock-out (เอกสาร `tb_stock_out` — โดยปกติ write-off, breakage, การแก้ไข count shortage)
  - `close` — period-close rollforward (post โดยระบบ ณ การเปลี่ยนงวด)
  - `open` — period-open rollforward (post โดยระบบเป็น opening ที่จับคู่ของงวดถัดไป)
- **`enum_location_type`**: พฤติกรรมการ post สำหรับ `tb_location.location_type` Default `inventory` สามค่า:
  - `inventory` — สินทรัพย์สต๊อกที่เป็นเจ้าของ การ post debit/credit บัญชี GL **Inventory**; ติดตาม on-hand qty; ตีมูลค่าตาม costing method
  - `direct` — cost centre แบบตรง การ post **bypass สินทรัพย์ inventory** และ debit **Department Expense** โดยตรง ไม่มี on-hand ติดตาม; ไม่มีการ post consumption ภายหลัง — receipt = expense ดู `../carmen/docs/Inventory/location-type-and-financial-treatment.md` สำหรับ breakdown ของ journal-entry
  - `consignment` — สต๊อกที่ vendor เป็นเจ้าของ holding ที่ location **Memo register เท่านั้น ณ การรับ** (ไม่มีสินทรัพย์ inventory, ไม่มี AP liability); consumption post COGS และ AP liability พร้อมกัน
- **`enum_transaction_type`**: cost-flow effect บน `tb_inventory_transaction_cost_layer.transaction_type` สิบสองค่า nullable บน column:
  - `good_received_note` — การสร้าง layer inbound จาก GRN receipt (`in_qty > 0`, `lot_no` ใหม่)
  - `transfer_in` — layer inbound ที่ destination จาก store-requisition transfer (`in_qty > 0`, `parent_lot_no` set)
  - `transfer_out` — layer outbound ที่ source จาก transfer (`out_qty > 0`, FIFO บริโภคโดย `lot_seq_no`)
  - `issue` — consumption outbound จาก store-requisition issue (`out_qty > 0`)
  - `adjustment_in` — inbound จาก manual stock-in (`tb_stock_in`) — found-stock, count overage เป็นต้น
  - `adjustment_out` — outbound จาก manual stock-out (`tb_stock_out`) — breakage, count shortage เป็นต้น
  - `credit_note_amount` — amount-only credit-note adjustment (`diff_amount` set; `in_qty` / `out_qty` เป็นศูนย์)
  - `credit_note_quantity` — quantity credit note (outbound compensating จาก lot ของ receipt ดั้งเดิม)
  - `eop_in` — end-of-period inbound rollforward (post โดยระบบ ผูก opening ของงวดถัดไปกับ closing ของงวดนี้)
  - `eop_out` — end-of-period outbound rollforward
  - `close_period` — anchor row period-close เขียนเข้างวดที่กำลังปิด
  - `open_period` — anchor row period-open เขียนเข้างวดถัดไป
- **`enum_period_status`**: สถานะของงวดบัญชีบน `tb_period.status` Default `open` สามค่า:
  - `open` — รับ movements (งวดเปิดปัจจุบันหรืออนาคต)
  - `closed` — period-end run, snapshot เขียนแล้ว; ไม่รับ movements ใหม่ที่มีวันที่ transaction ในงวดนี้ เว้นแต่จะ re-open อย่างชัดเจน
  - `locked` — audit แล้วและ immutable แม้แต่ admin re-open ก็ไม่ได้รับอนุญาต; การแก้ไขจะ post เข้างวดปัจจุบันที่เปิดอยู่เป็น restatement
- **`enum_physical_count_type`**: flag count-eligibility บน `tb_location.physical_count_type` Default `no` สองค่า:
  - `no` — location **ไม่ถูก** กวาดโดย physical-count run ตามตาราง (โดยปกติ direct / consignment / staging locations)
  - `yes` — location **ถูก** กวาดโดย physical count ตามตาราง

## 5. ความแตกต่างจาก carmen/docs

Inventory PRD ของ carmen/docs (`inventory-management-prd.md`), data-structure trace (`data-structure-trace.md`), เอกสาร financial-treatment (`location-type-and-financial-treatment.md`) และเอกสาร period-end process (`inventory-management/period-end-process.md`) รวมกันอธิบาย interface model ที่รวยกว่าความเป็นจริงของ Prisma — โดยเฉพาะ "balance" และ "status" interfaces หลายตัวที่ derive ใน application layer แทนที่จะ persist เป็น schema rows การตรวจสอบเทียบกับ canonical Prisma schema ให้ความแตกต่างต่อไปนี้:

| # | Item | carmen/docs ระบุ | Prisma มี | Action |
|---|------|------------------|------------|--------|
| 1 | เอนทิตี Stock balance | interface `InventoryStatus` / `StockBalance` พร้อม `QuantityOnHand`, `QuantityAllocated`, `QuantityAvailable`, `QuantityInTransit`, `LastUnitCost`, `AverageCost`, `TotalCost` เป็น **column ที่ persist** key โดย `(location_id, product_id, lot_no)` PRD §3 และ `data-structure-trace.md` อธิบาย writes ไปยังเอนทิตีนี้ในทุก movement | **ไม่มี `tb_stock_balance` model** On-hand คำนวณเป็น `Σ cost_layer.in_qty − Σ cost_layer.out_qty` ตั้งแต่ anchor `tb_period_snapshot.closing_qty` ล่าสุด scope ที่ `(location_id, product_id, lot_no)` `LastUnitCost` และ `AverageCost` เปิดเผยผ่าน `tb_inventory_transaction_cost_layer.cost_per_unit` และ `.average_cost_per_unit` บน event layer ล่าสุด `inTransit` และ `Allocated` derive จากสถานะ open-document (transfer SR ที่ออกแต่ยังไม่รับ, การ reserve requisition ที่ยังไม่ออก) ไม่ใช่ columns | ถือว่า Prisma เป็น canonical อัปเดต carmen/docs ให้อธิบาย `InventoryStatus` เป็น **read-model / derived view** ไม่ใช่ row ที่ persist บันทึกกฎ derivation (period snapshot anchor + cost-layer sum) เพื่อให้ผู้บริโภคเข้าใจ canonical query shape |
| 2 | ชื่อเอนทิตี movement และค่าประเภท | PRD อธิบาย `StockMovement` ด้วย `type ∈ {RECEIPT, ISSUE, TRANSFER, ADJUSTMENT, RETURN, WRITE_OFF}` และสถานะ workflow (`DRAFT → PENDING → IN_TRANSIT → COMPLETED → CANCELLED`) | model สองตาราง: `tb_inventory_transaction` ถือ `inventory_doc_type` (จำแนกโมดูล source — `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open`) และ `tb_inventory_transaction_cost_layer.transaction_type` (สิบสองประเภท cost-flow ใน Section 4) **ไม่มี `RETURN`, ไม่มี `WRITE_OFF` และไม่มีสถานะ workflow บนตัว transaction** — transaction คือ posted ledger record ไม่ใช่เอกสาร workflow Returns จำลองเป็น credit notes (`credit_note_amount` / `credit_note_quantity`); write-offs จำลองเป็น `tb_stock_out` พร้อม `adjustment_type_id` ที่เหมาะสม | จัดเรียง carmen/docs ใหม่ให้อธิบาย enum สองตัว (`enum_inventory_doc_type` จำแนกโมดูล source, `enum_transaction_type` cost-flow effect) แทน type field รวมเดียว บันทึกว่า returns และ write-offs จัดเส้นทางผ่านเอกสาร credit-note / stock-out ตามลำดับ |
| 3 | สถานะ workflow ของ stock movement | PRD §3 บ่งบอก multi-state workflow บน movement (`DRAFT → PENDING → IN_TRANSIT → COMPLETED → CANCELLED`) | `tb_inventory_transaction` **ไม่มี** enum `doc_status`, **ไม่มี** `workflow_history`, **ไม่มี** `workflow_current_stage` และ **ไม่มี** `user_action` Workflow อยู่บนเอกสารโมดูล source (GRN's `enum_good_received_note_status`, SR's `enum_doc_status` เป็นต้น); inventory transaction เป็น **posted-only** — มีอยู่ก็ต่อเมื่อเอกสาร source อยู่ในสถานะ committed/posted การกลับรายการทำโดยเขียน compensating transaction (หรือโดยเอกสาร source ขยับไปสถานะ void/credit-note ที่ trigger compensating write) ไม่ใช่โดยการเปลี่ยนสถานะบน transaction row | ลบการอ้างสถานะ workflow จากคำอธิบายเอนทิตี inventory ของ carmen/docs ระบุว่า workflow อยู่บนเอกสาร source และ inventory transaction คือ artefact ที่ posted immutable |
| 4 | Valuation method บนสินค้า | PRD §3 อ้างอิง `valuationMethod: FIFO | WEIGHTED_AVERAGE` ที่กำหนดต่อสินค้า | Costing method ต่อสินค้าอยู่บน model **product** (`tb_product`) — ไม่ใช่บน inventory โมดูล inventory **บริโภค** method เมื่อเลือก cost บน transaction outbound (FIFO scan `tb_inventory_transaction_cost_layer` โดย `lot_seq_no` ascending; weighted-average อ่าน `average_cost_per_unit` ล่าสุด) | ย้ายเอกสาร valuation-method ไปใต้ [[product]] / [[costing]] Inventory บันทึกกฎ **consumption** ไม่ใช่ configuration |
| 5 | scope และรูปของ Period-end snapshot | `inventory-management/period-end-process.md` อธิบาย period-end snapshot เป็นผลลัพธ์ checklist เชิงกระบวนการพร้อมรายงาน (Inventory Valuation Report, Movement Report, Variance Report) | `tb_period_snapshot` คือ snapshot **ที่ persist** — หนึ่ง row ต่อ `(period_id, location_id, product_id, lot_no, lot_index)` ถือ buckets opening / receipt / issue / adjustment / closing ทั้ง qty และ cost รายงานถูกอ่านจากตารางนี้; ตารางเองคือ anchor audit Checklist คือกระบวนการรอบ ๆ การเขียนตาราง | อัปเดต carmen/docs เพิ่มคำจำกัดความเอนทิตี `tb_period_snapshot` บันทึกว่า snapshot คือ anchor ที่ระบบ lock ไม่ใช่เพียง output รายงาน |
| 6 | columns "Free / Allocated / Available / InTransit" qty | PRD §3 Key Concepts ระบุ `onHand`, `allocated`, `available` และ `inTransit` เป็น columns ขนานบน stock balance | ไม่มีตัวใดที่ persist บนตาราง inventory ใด ๆ `onHand` คือผลรวม derive (item 1 ข้างบน) `allocated` และ `available` derive จากสถานะ open-document: `allocated = Σ open store-requisition reservations` สำหรับ product/location; `available = onHand − allocated` `inTransit` คือ `Σ store-requisition lines ในสถานะ transfer-dispatched-but-not-received` | บันทึกกฎ derivation ใน carmen/docs และ read-model ที่เปิดเผย; ลบ framing "persisted column" |
| 7 | Direct-cost location ไม่เป็นส่วนของ inventory | `location-type-and-financial-treatment.md` กล่าวถึง Direct Location Inventory bypass balance sheet ("ไม่มี inventory asset บันทึก… Bypass balance sheet โดยสิ้นเชิง") | สอดคล้องกับ Prisma — `tb_location.location_type = direct` post transaction inbound ด้วย `Dr Department Expense / Cr AP` และ **ไม่** สร้าง `tb_inventory_transaction_cost_layer` row สำหรับ consumption (เพราะของถูก expense ทันที) cost-layer ledger บรรจุเฉพาะ movements ประเภท inventory | ไม่มีความแตกต่าง; เพิ่ม note ใน carmen/docs cross-reference `enum_location_type = direct` และระบุว่า movements direct-location ยังถูกบันทึกใน `tb_inventory_transaction` (สำหรับ audit) แต่ไม่สร้าง layer row |
| 8 | การติดตาม Consignment inventory | `location-type-and-financial-treatment.md`: consignment receipt เป็น memo-only ("Receipt: ไม่มี entry — memo record เท่านั้น"); consumption trigger `Dr COGS / Cr AP` | สอดคล้องกับ Prisma — `tb_location.location_type = consignment` ผลิต `tb_inventory_transaction` row ณ receipt (สำหรับ audit) แต่ cost-layer ledger flag consignment register แยก; consumption post COGS และ AP liability พร้อมกัน | ไม่มีความแตกต่าง; ระบุใน carmen/docs ว่า locations ประเภท consignment ยังเขียน transactions (สำหรับ audit) แต่ flag cost-layer แยก vendor-owned ออกจาก layers สต๊อกที่เป็นเจ้าของ |
| 9 | Location ↔ delivery point | `data-structure-trace.md` อธิบาย `Location` และ `DeliveryPoint` เป็นเอนทิตี peer แยก พร้อม join | `tb_location` ถือ `delivery_point_id` (nullable FK) และ `delivery_point_name` (snapshot) ตรงบน location row — delivery point คือจุด dock / รับที่เชื่อมโยงกับ location ไม่ใช่ fan-out แยก FK มี Prisma `@relation` ไป `tb_delivery_point` | อัปเดต carmen/docs บันทึก relationship 1:1 (หรือ N:1): แต่ละ location อาจมี delivery point ดีฟอลต์หนึ่งจุด; หลาย locations อาจแชร์ delivery point |
| 10 | `physical_count_type` บน location | ไม่อธิบายใน carmen/docs | Prisma มี `tb_location.physical_count_type ∈ {yes, no}` (default `no`); field gate ว่า physical-count run ตามตารางจะกวาด location หรือไม่ rows location-type บางอันใน seed data default เป็น `yes` (เช่น main warehouse) อื่น ๆ default เป็น `no` (staging / transit / direct / consignment) | เพิ่มเข้า carmen/docs เป็น configuration field บันทึกว่า locations ประเภท direct- และ consignment- โดยปกติมี `physical_count_type = no` (การนับไม่มีความหมายที่นั่น) |
| 11 | semantics ของ Transaction-detail `from_lot_no` / `current_lot_no` | `data-structure-trace.md` อธิบายหมายเลข lot เป็น fields บนเอกสาร receipt | หมายเลข lot อยู่บน `tb_inventory_transaction_detail` (`from_lot_no` สำหรับ layer source บน outbound, `current_lot_no` สำหรับ layer ใหม่บน inbound) **และ** บน `tb_inventory_transaction_cost_layer` (`lot_no` สำหรับ identity ของ layer, `parent_lot_no` สำหรับ lineage transfer/split) Linkage เอกสาร-receipt ไปยังข้อมูล lot คือ **ผ่าน** inventory transaction (เช่น `tb_good_received_note_detail_item.inventory_transaction_id` ของ GRN) ไม่ใช่บน document row เอง — เป็นรูปแบบ divergence เดียวกับที่เรียกใน [[good-receive-note]] § 5 item 3 | อัปเดต carmen/docs บันทึกข้อมูล lot ด้านฝั่ง inventory transaction เอกสาร receipt คือ UI entry-point ไม่ใช่ lot store |
| 12 | Cost-layer `diff_amount` column | ไม่อธิบายใน carmen/docs | `tb_inventory_transaction_cost_layer.diff_amount` ใช้สำหรับ credit-note-amount adjustments (vendor ยอม concede ส่วนลดราคาหลัง receipt) และสำหรับ end-of-period price revaluation; ถือ cost variance อิสระจาก in/out qty | เพิ่มเข้า carmen/docs เป็น field "cost variance บน event layer"; ระบุว่าแยกจาก `total_cost` และรวมเข้า `adjustment_total_cost` ของ period snapshot |

## 6. แหล่งอ้างอิง

- **หลัก (source of truth):** Prisma schemas ที่ระบุใน header callout — เป็นรูปธรรม `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (เอนทิตี inventory ทั้งเจ็ด: `tb_inventory_transaction`, `tb_inventory_transaction_detail`, `tb_inventory_transaction_cost_layer`, `tb_location`, `tb_product_location`, `tb_period`, `tb_period_snapshot` พร้อม enum ห้าตัว `enum_inventory_doc_type`, `enum_location_type`, `enum_transaction_type`, `enum_period_status`, `enum_physical_count_type`) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (ตรวจสอบแล้วไม่มี model inventory)
- **รอง (cross-check แนวคิด):**
  - `../carmen/docs/Inventory/inventory-management-prd.md` — PRD อธิบาย `InventoryStatus` / `StockMovement` / valuation methods; ความแตกต่างใน Section 5 (items 1, 2, 3, 4, 6)
  - `../carmen/docs/Inventory/data-structure-trace.md` — data-structure trace อธิบาย relationship lot / location / delivery-point; ความแตกต่างใน Section 5 (items 9, 11)
  - `../carmen/docs/Inventory/location-type-and-financial-treatment.md` — breakdown journal-entry ต่อ location type (inventory / direct / consignment); cross-check กับ `enum_location_type` และพฤติกรรม cost-layer ledger (items 7, 8)
  - `../carmen/docs/Inventory/stock-in-detail.md` — workflow manual stock-in adjustment; cross-reference สำหรับเส้นทาง `enum_inventory_doc_type = stock_in`
  - `../carmen/docs/inventory-management/period-end-process.md` — checklist period-end และ framing snapshot; ความแตกต่างใน Section 5 (item 5 — `tb_period_snapshot` คือ anchor ที่ persist ไม่ใช่เพียง output รายงาน)
- โมดูลที่เกี่ยวข้อง: [[good-receive-note]] (receipts post `enum_inventory_doc_type = good_received_note` transactions; cross-link ไปยัง inventory transaction อยู่บน `tb_good_received_note_detail_item.inventory_transaction_id`), [[store-requisition]] (issues / transfers; SR detail ถือ `inventory_transaction_id`), [[physical-count]] (count adjustments post `tb_stock_in` / `tb_stock_out` rows map ไปยัง `adjustment_in` / `adjustment_out`), [[spot-check]] (partial counts; เส้นทาง posting เดียวกับ physical-count), [[inventory-adjustment]] (manual stock-in / stock-out สำหรับการแก้ไขที่ไม่ใช่ count), [[costing]] (บริโภค `tb_inventory_transaction_cost_layer.cost_per_unit` / `.average_cost_per_unit` สำหรับการเลือก cost outbound และสำหรับ COGS), [[product]] (ถือการกำหนดค่า costing-method ที่ cost-layer อ่าน ณ เวลา post), [[vendor-pricelist]] (price-variance เทียบกับ unit cost ของ GRN ที่รับ ทางอ้อมผ่าน layer inbound)
