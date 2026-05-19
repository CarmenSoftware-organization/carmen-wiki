---
title: สินค้า (Product) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum สำหรับโมดูลสินค้า
published: true
date: 2026-05-19T23:55:00.000Z
tags: product, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — Data Model

> **At a Glance**
> **ตาราง:** `tb_product` &nbsp;·&nbsp; `tb_product_category` → `tb_product_sub_category` → `tb_product_item_group` (การจำแนก 3 ระดับ) &nbsp;·&nbsp; `tb_unit` &nbsp;·&nbsp; `tb_unit_conversion` &nbsp;·&nbsp; `tb_product_location` &nbsp;·&nbsp; `tb_product_tb_vendor`
> **กลุ่มผู้ใช้:** Developer / Auditor (อ้างอิงสำหรับ dev)
> **FK สำคัญ:** product `→ tb_unit` (`inventory_unit_id`), `→ tb_product_item_group`, `→ tb_tax_profile`; unit-conversion `→ tb_product` + สอง `→ tb_unit`; product-location `→ tb_location` ถูกอ้างถึงโดยทุกตารางธุรกรรมปลายน้ำผ่าน `product_id` (PR / PO / GRN / SR / count / inventory ledger / recipe)
> **รูปแบบ audit:** `created_*` / `updated_*` / `deleted_*` มาตรฐานเหมือนกันทุกเอนทิตี ความไม่ซ้ำกำหนดขอบเขตด้วย `deleted_at` **วิธีการคิดต้นทุนไม่ได้อยู่บน product** — อยู่ที่ `tb_business_unit.calculation_method`

> **แหล่งความจริง:** Prisma schema ของ backend อ่านสิ่งเหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใต้แต่ละแพ็กเกจเป็นสำเนาที่สร้างอัตโนมัติ ไม่ใช่ฉบับทางการ

## 1. ภาพรวม

โมดูลสินค้าเป็น **system of record สำหรับแคตตาล็อกที่เอกสารธุรกรรมทุกใบอ้างอิง** ต่างจากโมดูลที่เน้นเอกสาร (PR, PO, GRN, SR) ที่มีเอกสาร workflow พร้อมต้นไม้ header → detail → comment ต้นไม้ของสินค้าเป็น **family ของตารางข้อมูลหลัก** ที่ยึดด้วย `tb_product` สินค้าแต่ละตัวระบุด้วย UUID `id` และ `code`/`name` ที่มนุษย์อ่านได้ อยู่ในห่วงโซ่การจำแนก (`tb_product_item_group → tb_product_sub_category → tb_product_category`) วัดด้วย `tb_unit` คลังฐาน มีการแปลงหน่วยที่เป็นทางเลือก (`tb_unit_conversion` พร้อม `enum_unit_type ∈ {order_unit, ingredient_unit}`) ถูกเปิดใช้ที่คลังจัดเก็บผ่าน `tb_product_location` (มี `min_qty` / `max_qty` / `re_order_qty` / `par_qty` ต่อคลัง) และอาจมีการ map ผู้ขายผ่าน `tb_product_tb_vendor` ตัว product เองมีฟิลด์ header ที่เล็กแต่สำคัญ: `code`, `name`, `local_name`, `description`, `inventory_unit_id`, `product_status_type` (`enum_product_status_type = active | inactive | discontinued`), `product_item_group_id`, `is_used_in_recipe`, `is_sold_directly`, `barcode`, `sku`, `price_deviation_limit`, `qty_deviation_limit`, `standard_cost`, `tax_profile_id` / `tax_profile_name` / `tax_rate`, `is_active` พร้อม JSON ส่วนขยาย (`info`, `dimension`, `certification`) thread ของ comment (`tb_product_comment` พร้อมตาราง comment คู่ขนานบนทุกระดับการจำแนก) ให้ surface ของบทสนทนาที่ตรวจสอบได้ที่ใช้ทุกที่ใน ERP

โมดูลนี้อยู่ **ที่รากของ dependency ของทุกโมดูลธุรกรรม** บรรทัด PR ทุกบรรทัด บรรทัด PO บรรทัด GRN บรรทัด SR บรรทัดนับ วัตถุดิบในสูตร ธุรกรรมคลังสินค้า และแถวของ cost-layer มี reference `product_id` ไม่มีการ post ธุรกรรมบน product — วงจรชีวิตคือ `create → active → deprecated (inactive) → soft-deleted` มี gate ด้วยการตรวจสอบการใช้งาน (สินค้าที่มีคลังไม่เป็นศูนย์ มีเอกสารเปิด หรือถูกอ้างอิงโดยสูตร active ไม่สามารถ soft-delete) ต้นไม้การจำแนก (`category → sub-category → item-group`) มี tax-profile และ ค่าความคลาดเคลื่อน default ที่ cascade product สามารถ override ค่าระดับหมวดหมู่ได้แต่ส่วนใหญ่เก็บไว้ในการสืบทอดเพื่อให้แคตตาล็อกสอดคล้อง การแปลงหน่วยถูกตรวจสอบ **ความสอดคล้องสองทิศทาง** ที่ application layer (`from_unit_qty × conversion_factor = to_unit_qty` ต้อง round-trip) และ engine resolve qty ของบรรทัดเอกสารใด ๆ กลับเป็นหน่วยฐานโดยใช้แถว `tb_unit_conversion`

จุดโครงสร้างหลายจุดควรย้ำตั้งแต่ต้น **ประการแรก** canonical schema **แบนและเรียบกว่าที่ carmen/docs PRD อธิบาย** — ไม่มีโมเดล `tb_product_variant`, ไม่มีตาราง key-value แบบมี type `tb_product_attribute`, ไม่มีตาราง `tb_product_media`, ไม่มีโมเดล `tb_product_carbon_footprint` คุณสมบัติ ตัวแปร สื่อ ข้อมูลความยั่งยืน และ certification ถูกเก็บใน **JSON extension bag** (`info`, `dimension`, `certification`) บน `tb_product` หรืออ้างอิงผ่าน JSON `attachments` อิสระบนตาราง comment Section 5 รวบรวมความแตกต่างเหล่านี้แบบครบ **ประการที่สอง** `tb_product_location` **ไม่ได้** มี on-hand qty — เป็น **แถวของนโยบายสต๊อก** เท่านั้น (min / max / par / reorder) on-hand qty derive จาก inventory cost-layer ledger (ดู [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 5 รายการ 1) **ประการที่สาม** **วิธีการคิดต้นทุนไม่ได้อยู่บน product** — อยู่บน `tb_business_unit.calculation_method` (platform schema, `enum_calculation_method = average | fifo`) และใช้กับ product ทุกตัวที่ business unit นั้น product มี `standard_cost` (ต้นทุนอ้างอิงที่ใช้โดยวิธี count-costing `standard` และโดย recipe baselining) แต่ไม่ใช่ตัวเลือก FIFO / WA เอง

## 2. เอนทิตี

### 2.1 tb_product

**แถว product master** แหล่งความจริงเดียวสำหรับเอกลักษณ์ของสินค้า ทุกตารางธุรกรรมอื่น join กลับมาที่แถวนี้ผ่าน `product_id`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key; `gen_random_uuid()` |
| `code` | `String @db.VarChar` | No | code สินค้าที่มนุษย์อ่านได้ ใช้เป็น lookup key บน picker บนป้ายบาร์โค้ด (เมื่อไม่ได้ตั้ง `barcode` แยก) และบนทุกบรรทัดเอกสารปลายน้ำ ไม่ซ้ำภายใน `(code, name, deleted_at)` ตาม index `product_code_name_u` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผลภาษาอังกฤษ / หลัก มี index |
| `local_name` | `String? @db.VarChar` | Yes | ชื่อท้องถิ่น (เช่นภาษาไทยสำหรับ property ในไทย) แสดงบนใบเสร็จและบน UI ภาษาท้องถิ่น |
| `description` | `String? @db.VarChar` | Yes | คำอธิบายยาวอิสระ |
| `inventory_unit_id` | `String @db.Uuid` | No | FK ไปยัง `tb_unit.id` — **หน่วยคลังฐาน** ที่ทุกยอด ต้นทุน และการประเมินมูลค่าสำหรับสินค้านี้ถูกเก็บ ไม่สามารถเปลี่ยนได้เมื่อสินค้ามีธุรกรรมคลังใด ๆ (ไม่มีการบังคับใช้ที่ schema กฎทางธุรกิจ) |
| `inventory_unit_name` | `String @db.VarChar` | No | snapshot ของชื่อแสดงผลของหน่วยฐาน default `""` |
| `product_status_type` | `enum_product_status_type` | No | สถานะวงจรชีวิต: `active` (ปรากฏบน picker พร้อมใช้สำหรับธุรกรรมใหม่), `inactive` (frozen ชั่วคราว — รักษาประวัติ ไม่รวมในเอกสารใหม่ ย้อนกลับได้) หรือ `discontinued` (end-of-life ชัดเจน — exclude เหมือน `inactive` แต่ส่งสัญญาณการเลิกใช้ถาวรสำหรับรายงานปลายน้ำ / การ suppress การ re-order) default `active` ดู Section 4 สำหรับกฎ transition |
| `product_item_group_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_product_item_group.id` — โหนดการจำแนกที่เป็นใบไม้ (category → sub-category → **item-group → product**) nullable สำหรับการ import ที่ยังไม่ได้จำแนก แต่แคตตาล็อก production ต้องการ |
| `is_used_in_recipe` | `Boolean?` | Yes | default `true` มาร์คสินค้าว่ามีสิทธิ์ปรากฏบนบรรทัดวัตถุดิบของสูตร ปิดสำหรับสินค้าทรัพย์สินคงที่ / ไม่ใช่ของบริโภค (สารทำความสะอาด อุปกรณ์) |
| `is_sold_directly` | `Boolean?` | Yes | default `false` มาร์คสินค้าว่าเป็น item ที่ขายได้บน POS (เช่น เครื่องดื่มในขวดที่ขายข้ามเคาน์เตอร์ ไม่ใช่แค่ใช้ในสูตร) ขับเคลื่อนการมีอยู่ของ menu-item linkage |
| `barcode` | `String? @db.VarChar` | Yes | ตัวระบุที่สแกนได้ (UPC, EAN, CODE128 ฯลฯ) lookup key หลักสำหรับการรับ / หยิบ / นับบนมือถือ กฎทางธุรกิจบังคับความไม่ซ้ำภายใน `(barcode, deleted_at)` ไม่ได้ประกาศ Prisma `@unique` ดังนั้น constraint รันใน application code |
| `sku` | `String? @db.VarChar` | Yes | ตัวระบุ Stock Keeping Unit (โดยทั่วไปแยกจาก `code` และ `barcode` — ใช้โดย integration ภายนอก / POS / ระบบ e-commerce) |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ค่าความคลาดเคลื่อนเป็น % ที่ใช้โดยกฎ procurement / receiving (`PR_VAL_*`, `GRN_VAL_*`) เพื่อ flag บรรทัดเอกสารปลายน้ำที่ราคาเบี่ยงจาก master มากกว่านี้ 0–100% ตามธรรมเนียม |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ความคิดเดียวกับ `price_deviation_limit` แต่สำหรับ qty (เช่น ที่สั่ง vs ที่รับ) |
| `standard_cost` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ต้นทุนอ้างอิง / มาตรฐานต่อหน่วยฐาน ใช้โดยวิธี count-costing `standard` (`enum_physical_count_costing_method = standard`) และโดย recipe baseline costing ไม่ถูกบริโภคโดย FIFO / WA cost-pick engine — พวกเขาอ่าน `cost_per_unit` ของ cost-layer |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` — tax profile (หมวด VAT, tax rule set) ที่ใช้กับสินค้าบนธุรกรรมปลายน้ำ โดยทั่วไปสืบทอดจากห่วงโซ่การจำแนก (`tb_product_item_group.tax_profile_id` หรือ `tb_product_sub_category.tax_profile_id` หรือ `tb_product_category.tax_profile_id`) การตั้งค่าระดับสินค้า override |
| `tax_profile_name` | `String? @db.VarChar` | Yes | snapshot ของชื่อ tax profile |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | default `0` snapshot ของอัตราจาก tax profile ในเวลา sync ล่าสุด |
| `is_active` | `Boolean?` | Yes | default `true` flag ปิดแบบ hard (ต่างจาก `product_status_type` — `is_active = false` ลบสินค้าจากทุก picker รวมถึง admin view; `product_status_type = inactive` หรือ `discontinued` ลบจาก picker ธุรกรรมใหม่แต่ admin ยังเห็น) |
| `note` | `String? @db.VarChar` | Yes | โน้ตอิสระ |
| `info` | `Json? @db.JsonB` | Yes | extension bag สำหรับคุณสมบัติเฉพาะ tenant (อายุการเก็บรักษา คำแนะนำการจัดเก็บ ขนาด สี สารก่อภูมิแพ้ บรรจุภัณฑ์ — สิ่งที่ canonical PRD อธิบายว่า "attribute" อยู่ที่นี่เป็น JSON) default `{}` |
| `dimension` | `Json? @db.JsonB` | Yes | array cost-dimension (project, cost-centre, job code) สำหรับ dimension default บนเอกสารปลายน้ำ default `[]` |
| `certification` | `Json? @db.JsonB` | Yes | extension bag สำหรับข้อมูล certification (organic, fair-trade, halal, kosher, sustainability rating, คะแนน carbon footprint) default `{}` |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | timestamp การสร้าง default เป็น `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | id ของผู้สร้าง |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ของผู้อัปเดต |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | timestamp soft-delete; non-null หมายถึงถูกลบเชิงตรรกะ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK: `inventory_unit_id → tb_unit.id` (`NoAction`); `product_item_group_id → tb_product_item_group.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`)
**Indexes:** `@@unique([code, name, deleted_at])` เป็น `product_code_name_u`; `@@index([code])` เป็น `product_code_idx`; `@@index([name])` เป็น `product_name_idx`
**Back-relations:** list ที่ครอบคลุมรวมถึง `tb_count_stock_detail`, `tb_credit_note_detail`, `tb_good_received_note_detail`, `tb_pricelist_detail`, `tb_product_location`, `tb_product_tb_vendor`, `tb_purchase_request_detail`, `tb_purchase_request_template_detail`, `tb_stock_in_detail`, `tb_stock_out_detail`, `tb_store_requisition_detail`, `tb_unit_conversion`, `tb_pricelist_template_detail`, `tb_spot_check_detail`, `tb_physical_count_detail`, `tb_product_comment`, `tb_recipe_ingredient`, `tb_purchase_order_detail` ทุกตารางธุรกรรมปลายน้ำของคลังสินค้าอ้างอิง product

### 2.2 tb_product_category

**โหนดการจำแนกระดับบนสุด** ระดับแรกของลำดับชั้นการจำแนก (`category → sub-category → item-group`) และผู้ถือ default ระดับหมวดหมู่ที่กระจายไปยังลูก

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | code หมวดหมู่ที่มนุษย์อ่านได้ |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `is_active` | `Boolean?` | Yes | default `true` |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` default ระดับหมวดหมู่สำหรับ `price_deviation_limit` ของ product สืบทอดเว้นแต่ product จะ override |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` default ระดับหมวดหมู่สำหรับ `qty_deviation_limit` ของ product |
| `is_used_in_recipe` | `Boolean?` | Yes | default `true` default ระดับหมวดหมู่สำหรับ `is_used_in_recipe` ของ product |
| `is_sold_directly` | `Boolean?` | Yes | default `false` default ระดับหมวดหมู่ |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` default ระดับหมวดหมู่ สืบทอดโดย sub-category, item-group และ product เว้นแต่ override |
| `tax_profile_name` | `String? @db.VarChar` | Yes | snapshot |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | default `0` snapshot |
| `note` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `info` | `Json? @db.JsonB` | Yes | extension bag default `{}` |
| `dimension` | `Json? @db.JsonB` | Yes | array cost-dimension default `[]` |
| `created_at` / `created_by_id` / `updated_at` / `updated_by_id` / `deleted_at` / `deleted_by_id` | audit | Yes | คอลัมน์ audit มาตรฐาน |

**Constraints:** `@id` บน `id` FK `tax_profile_id → tb_tax_profile.id` (`NoAction`)
**Indexes:** `@@unique([code, name, deleted_at])` เป็น `productcategory_code_name_u`; `@@unique([code, deleted_at])` เป็น `productcategory_code_u`; `@@index([code])` เป็น `productcategory_code_idx`; `@@index([name])` เป็น `productcategory_name_idx`
**Back-relations:** `tb_product_sub_category`, `tb_product_category_comment`

### 2.3 tb_product_sub_category

**โหนดการจำแนกระดับสอง** ห้อยจาก `tb_product_category` และมี default ที่สืบทอด / override ไปยังลูก `tb_product_item_group`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_category_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product_category.id` |
| `code` | `String @db.VarChar` | No | default `""` code ของ sub-category |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` default ระดับ sub-category สืบทอดจากหมวดหมู่ถ้าเป็นศูนย์ |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` |
| `is_used_in_recipe` | `Boolean?` | Yes | default `true` |
| `is_sold_directly` | `Boolean?` | Yes | default `false` |
| `is_active` | `Boolean?` | Yes | default `true` |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` Override falls back ไประดับหมวดหมู่ |
| `tax_profile_name` | `String? @db.VarChar` | Yes | snapshot |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | default `0` |
| `note` / `info` / `dimension` / audit | various | Yes | มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `product_category_id → tb_product_category.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`)
**Indexes:** `@@unique([code, name, deleted_at])` เป็น `productsubcategory_code_name_u`; `@@index([code])` / `@@index([name])`
**Back-relations:** `tb_product_item_group`, `tb_product_sub_category_comment`

### 2.4 tb_product_item_group

**โหนดการจำแนกระดับสาม (ใบไม้)** — ระดับที่ product ผูกโดยตรง มี default ที่สืบทอด / override สุดท้ายและเป็นจุด join ของ product กับต้นไม้การจำแนก

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_subcategory_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product_sub_category.id` หมายเหตุชื่อคอลัมน์ใช้ `subcategory` (ไม่มี underscore ระหว่าง `sub` และ `category`) โมเดล parent ใช้ `tb_product_sub_category` |
| `code` | `String @db.VarChar` | No | code ของ item-group |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `price_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` override ระดับ item-group |
| `qty_deviation_limit` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` |
| `is_used_in_recipe` | `Boolean?` | Yes | default `true` |
| `is_sold_directly` | `Boolean?` | Yes | default `false` |
| `is_active` | `Boolean?` | Yes | default `true` |
| `tax_profile_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_tax_profile.id` Override สุดท้าย falls back ผ่าน sub-category ไปยังหมวดหมู่ |
| `tax_profile_name` | `String? @db.VarChar` | Yes | snapshot |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | default `0` |
| `note` / `info` / `dimension` / audit | various | Yes | มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `product_subcategory_id → tb_product_sub_category.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`)
**Indexes:** `@@unique([code, name, product_subcategory_id, deleted_at])` เป็น `productitemgroup_code_name_product_subcategory_u`; `@@index([code])` / `@@index([name])`
**Back-relations:** `tb_product`, `tb_product_item_group_comment`

### 2.5 tb_unit

**นิยามหน่วยนับ** ทั้งหน่วยฐานคลัง (`KG`, `LITRE`, `EACH`) และหน่วยสั่งซื้อ / สูตร (`CASE`, `DOZEN`, `TBSP`) ใช้ตารางเดียวนี้ — ไม่มีคอลัมน์ `unit_type` บนตัวหน่วยเอง type เกิดจากการ join (`tb_product.inventory_unit_id` สำหรับฐาน `tb_unit_conversion` สำหรับสั่งซื้อ / สูตร)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `KG`, `CASE`) |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `is_active` | `Boolean?` | Yes | default `true` |
| `decimal_place` | `Int` | No | default `2` precision การแสดงผลสำหรับ qty ที่แสดงในหน่วยนี้ การเก็บข้อมูลพื้นฐานบน cost-layer / detail เป็น `Decimal(20, 5)` เสมอ คอลัมน์นี้ขับเคลื่อนการปัดเศษสำหรับการแสดงผลเท่านั้น |
| `note` / `info` / `dimension` / audit | various | Yes | มาตรฐาน |

**Constraints:** `@id` บน `id`
**Indexes:** `@@unique([name, deleted_at])` เป็น `unit_name_deletedat_u`; `@@index([name])` เป็น `unit_name_idx`
**Back-relations:** กว้าง — `tb_product` (เป็นฐาน), `tb_pricelist_detail`, หลายตัวแปรบน `tb_purchase_order_detail` (base / order), `tb_purchase_request_detail` (approved / foc / requested), `tb_unit_conversion` (เป็น `from_unit` และ `to_unit`), ตัวแปร GRN detail-item (foc / received / order), recipe ingredient (ingredient / inventory), physical-count detail, spot-check detail, `tb_unit_comment`

### 2.6 tb_unit_conversion

**แถว conversion factor** นิยามวิธีที่ปริมาณที่แสดงในหน่วยหนึ่งแปลเป็นอีกหน่วย กำหนดขอบเขตด้วย `product_id` (ดังนั้น `CASE` เดียวกันสามารถหมายถึง 12 `EACH` ของสินค้า A แต่ 24 `EACH` ของสินค้า B) และด้วย `unit_type` (`order_unit` สำหรับการแปลงด้าน procurement, `ingredient_unit` สำหรับการแปลงด้านสูตร)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_product.id` nullable สำหรับการแปลง "generic" (เช่น `1 KG = 1000 G`) แต่โดยทั่วไป populate ต่อ product เพราะ multiplier ต่างกัน |
| `unit_type` | `enum_unit_type` | No | `order_unit` (การแปลง procurement / receiving / vendor pricelist) หรือ `ingredient_unit` (การแปลงสูตร / การใช้) namespace ทั้งสองถูกแยกแยะเพื่อให้การแปลงหน่วยสั่งซื้อของสินค้าไม่ปนกับการ scale สูตร |
| `from_unit_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_unit.id` — หน่วยต้นทาง nullable สำหรับกรณีหายากที่ต้องการแค่ snapshot ชื่อ |
| `from_unit_name` | `String @db.VarChar` | No | snapshot ของชื่อหน่วยต้นทาง |
| `from_unit_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ปริมาณด้านต้นทางของการแปลง (เช่น `1` สำหรับ "1 CASE = 12 EACH") |
| `to_unit_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_unit.id` — หน่วยปลายทาง |
| `to_unit_name` | `String @db.VarChar` | No | snapshot |
| `to_unit_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ปริมาณด้านปลายทาง (เช่น `12` สำหรับ "1 CASE = 12 EACH") conversion factor คือ `to_unit_qty / from_unit_qty` |
| `decimal_place` | `Int` | No | default `2` precision การแสดงผล |
| `is_default` | `Boolean?` | Yes | default `false` มาร์คการแปลงนี้เป็นหน่วยสั่งซื้อ default (หรือหน่วยวัตถุดิบ default) สำหรับสินค้า — แสดงก่อนบน picker |
| `description` | `Json? @db.JsonB` | Yes | โน้ตอิสระ / โครงสร้าง default `{}` |
| `is_active` | `Boolean?` | Yes | default `true` |
| `note` / `info` / `dimension` / audit | various | Yes | มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `from_unit_id → tb_unit.id` (`NoAction`) ผ่าน relation ชื่อ `tb_unit_conversion_from_unit_idTotb_unit`; `to_unit_id → tb_unit.id` (`NoAction`) ผ่าน `tb_unit_conversion_to_unit_idTotb_unit`; `product_id → tb_product.id` (`NoAction`)
**Indexes:** `@@unique([product_id, unit_type, from_unit_id, to_unit_id, deleted_at])` เป็น `unitconversion_product_unit_type_from_unit_to_unit_deletedat_u`; `@@index([product_id, unit_type, from_unit_id, to_unit_id])`; `@@index([product_id])`

### 2.7 tb_product_location

**แถวนโยบายสต๊อกต่อ product / ต่อ location** มี par / min / max / reorder qty ที่ใช้โดย logic ของ replenishment-suggestion และ over/under-stock alert **ไม่ได้** มี on-hand qty (derive จาก inventory cost-layer ledger)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` |
| `location_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_location.id` |
| `min_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ต่ำกว่านี้ trigger replenishment alert |
| `max_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` สูงกว่านี้ trigger over-stock alert |
| `re_order_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` qty สั่งซื้อที่แนะนำเมื่อ on-hand ตกต่ำกว่า `min_qty` |
| `par_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | default `0` ระดับ par สำหรับการเก็บสต๊อก outlet (เป้าหมาย on-hand) |
| `note` / `info` / `dimension` | various | Yes | มาตรฐาน |
| `doc_version` | `Int` | No | default `0` counter optimistic-concurrency ใช้เมื่อผู้ใช้หลายคนแก้นโยบายพร้อมกัน |
| audit | various | Yes | `created_at` / `created_by_id` / `updated_at` / `updated_by_id` / `deleted_at` / `deleted_by_id` มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `product_id → tb_product.id` (`NoAction`); `location_id → tb_location.id` (`NoAction`)
**Indexes:** `@@unique([product_id, location_id, deleted_at])` เป็น `product_location_product_id_location_id_u`; `@@index([product_id, location_id])`

### 2.8 tb_product_tb_vendor

**ตาราง join product–vendor** ที่ list ผู้ขายที่ supply สินค้า พร้อม code และชื่อสินค้าของผู้ขายเองสำหรับ cross-reference ใช้โดย [vendor-pricelist](/th/inventory/vendor-pricelist) และ [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) เพื่อกำหนดขอบเขต vendor picker

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_id` | `String @db.Uuid` | No | FK ไปยัง `tb_product.id` |
| `product_code` / `product_name` / `product_local_name` / `product_sku` | `String? @db.VarChar` | Yes | snapshot ของฟิลด์ master (denormalise เพื่อให้แถว join รอดจากการ re-code สินค้า) |
| `vendor_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_vendor.id` |
| `vendor_product_code` | `String? @db.VarChar` | Yes | code ของผู้ขายเองสำหรับสินค้านี้ (ใช้บน PO และ pricelist เมื่อผู้ขายคาดหวัง SKU ของตนบนเอกสาร) |
| `vendor_product_name` | `String? @db.VarChar` | Yes | ชื่อสินค้าของผู้ขายเอง |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `is_active` | `Boolean?` | Yes | default `true` |
| `note` / `info` / `dimension` / audit | various | Yes | มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `product_id → tb_product.id` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`)
**Indexes:** `@@unique([vendor_id, product_id, deleted_at])` เป็น `product_vendor_vendor_product_u`; `@@index([product_id])` เป็น `product_vendor_product_id_idx`; `@@index([vendor_id])` เป็น `product_vendor_vendor_id_idx`

### 2.9 ตาราง Comment (tb_product_comment, tb_product_category_comment, tb_product_sub_category_comment, tb_product_item_group_comment, tb_unit_comment)

แต่ละเอนทิตีในต้นไม้ของ product มี **ตาราง comment คู่ขนาน** ที่มี surface ของบทสนทนา ตาราง comment ทั้งหมดมีรูปทรงเดียวกัน: `id`, FK `<parent>_id` ไปยัง parent, `type` (`enum_comment_type`, default `user`), `user_id`, `message`, `attachments` (array JSON ของ object `{originalName, fileToken, contentType}` ที่ map ไปยังไฟล์ที่ upload S3) และคอลัมน์ audit มาตรฐาน `enum_comment_type` แยกแยะ `user` (ข้อความอิสระจากคน) จาก `system` (annotation event อัตโนมัติ — เช่น สรุป import-job, บรรทัด log สถานะ) ธรรมเนียมนี้สอดคล้องกันทั่วทุกโมดูลที่ใช้ comment

ตาราง comment คือ **surface ของบทสนทนา audit** ไม่ใช่ activity log activity log (ประวัติ workflow, การเปลี่ยนสถานะ, การเปลี่ยนฟิลด์) อยู่บน JSON `info` ของแถว parent หรือในคอลัมน์ workflow เฉพาะ ตาราง comment สำหรับการอภิปรายอิสระของมนุษย์ที่ผูกกับเอนทิตีข้อมูลหลัก

## 3. ความสัมพันธ์

```
tb_product_category
    │ 1 — *
    ▼
tb_product_sub_category   (product_category_id)
    │ 1 — *
    ▼
tb_product_item_group     (product_subcategory_id — หมายเหตุ: ชื่อคอลัมน์ใช้ 'subcategory')
    │ 1 — *
    ▼
tb_product                (product_item_group_id)
    │
    ├──► tb_unit          (inventory_unit_id — หน่วยคลังฐาน)
    │
    ├──► tb_tax_profile   (tax_profile_id — override ได้; falls back ผ่าน item-group → sub-category → category)
    │
    │ 1 — *
    ▼
tb_unit_conversion        (product_id; unit_type ∈ {order_unit, ingredient_unit};
                           from_unit_id, to_unit_id → tb_unit.id)
    │
    │ 1 — *
    ▼
tb_product_location       (product_id, location_id; min/max/par/reorder — ไม่มี on-hand)
    │
    └──► tb_location

tb_product
    │ 1 — *
    ▼
tb_product_tb_vendor      (product_id, vendor_id; vendor_product_code / vendor_product_name)
    │
    └──► tb_vendor


tb_product ถูกอ้างถึง BY ทุกตารางธุรกรรมปลายน้ำ:
    tb_purchase_request_detail.product_id
    tb_purchase_order_detail.product_id
    tb_good_received_note_detail.product_id
    tb_store_requisition_detail.product_id
    tb_stock_in_detail.product_id / tb_stock_out_detail.product_id
    tb_count_stock_detail.product_id / tb_spot_check_detail.product_id / tb_physical_count_detail.product_id
    tb_credit_note_detail.product_id
    tb_pricelist_detail.product_id / tb_pricelist_template_detail.product_id
    tb_recipe_ingredient.product_id
    tb_inventory_transaction_detail.product_id (ไม่มี @relation — resolve ที่ application)
    tb_inventory_transaction_cost_layer.product_id (ไม่มี @relation — resolve ที่ application)
    tb_period_snapshot.product_id (ไม่มี @relation — resolve ที่ application)
```

หมายเหตุ:

- **ต้นไม้การจำแนกมี default ที่ cascade** `price_deviation_limit`, `qty_deviation_limit`, `is_used_in_recipe`, `is_sold_directly` และ `tax_profile_id` มีอยู่บน **ทุกระดับ** ของต้นไม้ (`tb_product_category`, `tb_product_sub_category`, `tb_product_item_group`, `tb_product`) กฎการสืบทอดของ application คืออ่านค่าที่เฉพาะที่สุดที่ไม่ใช่ศูนย์ / ไม่ใช่ null เดินขึ้นจาก product ผ่านห่วงโซ่การจำแนก สิ่งนี้ **ไม่ได้** บังคับใช้โดย Prisma — การสืบทอดเกิดที่ read time ใน service layer
- **ไม่มีโมเดล `tb_product_variant`** ตัวแปร (ขนาด สี การรวมบรรจุภัณฑ์) ไม่ได้ถูกสร้าง model เป็นตารางแยก พวกมันอยู่เป็น JSON ใน `tb_product.info` หรือเป็นแถว `tb_product` เพิ่มเติมที่แชร์ category/item-group ดู Section 5 รายการ 1
- **ไม่มีโมเดล `tb_product_attribute`** คุณสมบัติ key-value แบบมี type (PRD `attributeType ∈ {text, number, boolean, date, select, multi-select, rich-text}`) ไม่ได้ถูกสร้าง model เป็นตาราง normalise พวกมันอยู่เป็น JSON ใน `tb_product.info` ข้อกำหนด / การสืบทอด attribute ระดับหมวดหมู่ถูก document ใน carmen/docs แต่ **ไม่ได้** บังคับใช้ที่ schema ดู Section 5 รายการ 2
- **ไม่มีโมเดล `tb_product_media`** รูปภาพ / เอกสาร / วิดีโอของสินค้าไม่ได้ถูกสร้าง model เป็นตารางแยก array JSON `tb_product_comment.attachments` (reference file-token) เป็น surface ของ attachment เดียวใน canonical schema product-media ระดับ first-class (รูป primary ที่กำหนด thumbnail การเรียงลำดับ) อยู่ใน application layer หรือถูกเลื่อน ดู Section 5 รายการ 3
- **Soft-delete ใช้ทั่วโลก** ทุกเอนทิตีในโมดูลนี้มี `deleted_at` / `deleted_by_id` constraint unique รวม `deleted_at` (เช่น `product_code_name_u = (code, name, deleted_at)`) ดังนั้น code ของสินค้าที่ลบสามารถนำกลับมาใช้ได้ แถวที่ live guard ความไม่ซ้ำเฉพาะกับแถว live อื่น
- **การประกาศ FK `@relation` ที่ชัดเจนทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction`** — referential integrity ถูกรักษาโดย soft-delete ระดับ application และโดย in-use guard (สินค้าที่มี on-hand ไม่เป็นศูนย์หรือเอกสารเปิดไม่สามารถลบได้)

## 4. Enum

- **`enum_product_status_type`**: สถานะวงจรชีวิตบน `tb_product.product_status_type` default `active` สามค่า:
  - `active` — สินค้าปรากฏบน picker และพร้อมใช้สำหรับธุรกรรมใหม่
  - `inactive` — สินค้าถูก frozen เป็นสถานะ **ชั่วคราว / ย้อนกลับได้** รักษาประวัติ (ยอด เอกสาร posted สูตร) แต่ไม่รวมในเอกสารใหม่ การเปลี่ยนตรวจสอบได้และสามารถตั้งเวลาให้มีผลในวันที่อนาคตโดย application layer (ไม่มีคอลัมน์ effective-date ที่ระดับ schema) ใช้สำหรับการ pause ตามฤดูกาล การ hold เพื่อ recall และกรณีที่ revive ได้
  - `discontinued` — สินค้าถูก frozen เป็นสถานะ **end-of-life ที่ชัดเจน** การ exclude จาก picker เหมือน `inactive` แต่สัญญาณเชิงความหมายคือการเลิกใช้ถาวร (ไม่มีแผน re-introduction) ขับเคลื่อนพฤติกรรมปลายน้ำเช่นการ suppress คำแนะนำ re-order, ซ่อนจาก vendor-pricelist, prompt แทนที่ใน recipe และรายงาน end-of-life inventory ย้อนกลับได้ที่ระดับ schema แต่ทางปฏิบัติไม่แนะนำ
- **`enum_unit_type`**: ขอบเขตบน `tb_unit_conversion.unit_type` ไม่ประกาศ default จำเป็นบนทุกแถว สองค่า:
  - `order_unit` — การแปลงใช้โดย procurement / receiving / vendor-pricelist (เช่น `1 CASE = 12 EACH`) ขับเคลื่อนการแปลง qty PR / PO / GRN กลับเป็นหน่วยคลังฐาน
  - `ingredient_unit` — การแปลงใช้โดย recipe / consumption (เช่น `1 TBSP = 15 ML`) ขับเคลื่อนการแปลง qty วัตถุดิบของสูตรกลับเป็นหน่วยฐานในเวลา explosion ของ theoretical-consumption
- **`enum_comment_type`**: classifier ของ comment บนทุก `*_comment.type` default `user` ค่า: `user` (ข้อความอิสระของมนุษย์), `system` (annotation event อัตโนมัติ)

Schema ยังพึ่งพา **enum ต้นน้ำที่บริโภคโดยโมดูล product แต่ไม่ได้เป็นเจ้าของ**:

- `enum_calculation_method` (บน `tb_business_unit.calculation_method`, platform schema): `average`, `fifo` ตัวเลือกวิธีการคิดต้นทุน — **ไม่ได้อยู่บน product** ดู [costing/01-data-model](/th/inventory/costing/01-data-model) § 2.4
- `enum_physical_count_costing_method` (บนเอกสาร count): `standard`, `last`, `average`, `last_receiving` เลือกแหล่งต้นทุนที่ป้อนการ post variance ของ count `standard` อ่าน `tb_product.standard_cost` ดู [costing/01-data-model](/th/inventory/costing/01-data-model) § 2.6

## 5. ความแตกต่างจาก carmen/docs

product-management PRD ของ carmen/docs (`PROD-PRD.md`) และ product-master PRD (`product-master-prd.md`) อธิบายโมเดล interface ที่รุ่มรวยมากกว่า Prisma reality การ cross-check กับ canonical Prisma schema ให้ความแตกต่างต่อไปนี้ — คาดหวังสำหรับโมดูลข้อมูลหลักที่กว้างขนาดนี้

| # | รายการ | carmen/docs บอกว่า | Prisma มี | การดำเนินการ |
|---|------|------------------|------------|--------|
| 1 | Product Variants | `PROD-PRD.md` § 3.1.3 (FR-PRD-021..030): เอนทิตี `Variant` ที่ชัดเจน พร้อม variant code ไม่ซ้ำ การคิดราคา / ต้นทุนเฉพาะตัวแปร สื่อเฉพาะตัวแปร matrix attribute ตัวแปร การติดตามคลังเฉพาะตัวแปร ข้อมูลความยั่งยืนเฉพาะตัวแปร `product-master-prd.md` § 3.2.8 ประเภท product รวม `Variant` | **ไม่มีโมเดล `tb_product_variant`** ตัวแปรถูกสร้าง model เป็น: (a) แถว `tb_product` เพิ่มเติม (แต่ละตัวแปรเป็นสินค้าของตัวเองด้วย `code` / `sku` / `barcode` ของตัวเอง แชร์ category / item-group / หน่วยฐานกับ "parent") หรือ (b) key JSON ใน `tb_product.info` สำหรับการเปลี่ยนแปลงที่ cardinality ต่ำ (เช่น `{ "variants": [{ "size": "small", "barcode": "...", "price": 95 }, ...] }`) ไม่มีคอลัมน์ความสัมพันธ์ parent-variant บน `tb_product` | ถือ Prisma เป็น canonical อัปเดต carmen/docs ให้อธิบายตัวแปรว่า "products-as-variants" (หนึ่งแถวต่อตัวแปร) สำหรับการติดตามตัวแปรคุณภาพ production หรือ "JSON variants" สำหรับการเปลี่ยนแปลง catalog-display-only "ตัวสร้าง matrix ของตัวแปร" UI ที่อธิบายใน `UI-PRD-025` อยู่เป็น frontend-only helper ที่สร้างหลายแถว `tb_product` ใน flow เดียว |
| 2 | Typed Product Attributes | `PROD-PRD.md` § 3.1.2 (FR-PRD-011..020): typed attribute (`text`, `number`, `boolean`, `date`, `select`, `multi-select`, `rich-text`) การกำหนด attribute กับสินค้า flag required / optional กฎ validation การสืบทอดจากหมวดหมู่ การอัปเดต attribute value เป็นชุด นิยาม attribute ระดับหมวดหมู่พร้อม sub-category override | **ไม่มีโมเดล `tb_product_attribute` / `tb_product_attribute_value`** Product attribute อยู่เป็น **JSON ที่ไม่ได้ type** ใน `tb_product.info` (และ "attribute default" ระดับหมวดหมู่คล้ายกันใน `tb_product_category.info`) ไม่มีการ validate ระดับ schema ของ attribute type, required-ness หรือการสืบทอด — กฎเหล่านั้นรันใน application layer (เมื่อพวกมันรันเลย) carmen/docs PRD อธิบายฟีเจอร์ที่บางส่วนเป็น aspirational | document ว่า "ระบบ attribute" เป็น **JSON-only** ที่ระดับ schema typed validation และการสืบทอดหมวดหมู่เป็นธรรมเนียมระดับ application อัปเดต carmen/docs ให้อธิบายรูปทรง JSON (`info: { attributes: { <key>: <value> } }`) และกฎระดับ application ที่ควบคุม |
| 3 | Product Media (รูป / เอกสาร / วิดีโอ / โมเดล 3D) | `PROD-PRD.md` § 3.1.4 (FR-PRD-031..040): สื่อ primary ที่กำหนด การเรียงลำดับ thumbnail การติด tag อัตโนมัติด้วย AI การส่งมอบบนมือถือ `UI-PRD-013` อ้างถึง gallery สื่อในมุมมองรายละเอียดของสินค้า | **ไม่มีโมเดล `tb_product_media`** Attachment อยู่บนตาราง comment (`tb_product_comment.attachments` — array JSON ของ `{originalName, fileToken, contentType}`) ไม่มี "รูปสินค้า" ระดับ first-class พร้อม `is_primary` / `display_order` / `thumbnail_url` Frontend อาจเลือก attachment comment แรกที่ `contentType` ขึ้นต้นด้วย `image/` เป็น primary แต่นี่คือธรรมเนียม ไม่ใช่ schema | เพิ่ม `tb_product_media` ใน backlog schema อนาคต (หรือ document ธรรมเนียม JSON ถ้าทิ้งสื่อในตาราง comment) สำหรับตอนนี้ frontend render attachment-as-media โดยไม่มี rich metadata ที่ PRD อธิบาย |
| 4 | สถานะวงจรชีวิตของสินค้า | `PROD-PRD.md` § 3.1.5 (FR-PRD-041..050) และ `product-master-prd.md`: วงจรชีวิตรวม `Active`, `Inactive`, **`Discontinued`** พร้อมการเปลี่ยนสถานะตามตารางเวลา การติดตามประวัติสถานะ การควบคุมการมองเห็นตามสถานะ การ visualise วงจรชีวิต | `enum_product_status_type` ตอนนี้มี **สามค่า**: `active`, `inactive`, `discontinued` (เพิ่มใน pass enum-cleanup พฤษภาคม 2026) ยังไม่มีตารางประวัติสถานะระดับ first-class (ประวัติ implicit อยู่บนคอลัมน์ audit และบน entry system ของ `tb_product_comment`) และไม่มีคอลัมน์ scheduled-change ระดับ schema | ค่า `discontinued` ใน enum ตรงกับ schema แล้ว การเปลี่ยนตามตารางเวลาและการรายงานประวัติสถานะยังคงเป็นความกังวลระดับ application — implement ผ่าน entry `tb_product_comment` `type = system` ตอน transition และคอลัมน์ effective-date ใน JSON `info` ถ้าจำเป็น |
| 5 | ความไม่ซ้ำและการสร้างบาร์โค้ด | `PROD-PRD.md` § 3.1.6 (FR-PRD-051..058): การสร้าง รูปแบบหลายแบบ (UPC, EAN, CODE128) การพิมพ์ การสแกน การ validate ความไม่ซ้ำ การสร้างเป็นชุด QR พร้อมข้อมูลสินค้าฝัง | `tb_product.barcode` เป็นคอลัมน์ข้อความอิสระ **ไม่มี `@unique` constraint** ที่ระดับ schema ความไม่ซ้ำบังคับใช้ที่ application (ปฏิเสธตอน create / update) การเลือกรูปแบบ (UPC vs EAN vs CODE128) อยู่ใน value แบบ implicit ไม่มี enum `barcode_format` บนสินค้า | document ว่าความไม่ซ้ำของบาร์โค้ดเป็น application-only ถ้าความไม่ซ้ำสำคัญที่ระดับ DB เพิ่ม `@@unique([barcode, deleted_at])` ใน migration ครั้งต่อไป การเลือกรูปแบบเป็นความกังวลของ frontend / การพิมพ์ |
| 6 | การติดตาม Carbon Footprint และความยั่งยืน | `PROD-PRD.md` § 3.1.7 (FR-PRD-059..066): ติดตาม carbon footprint, sustainability rating และ certification, ข้อมูลบรรจุภัณฑ์, การเปรียบเทียบความยั่งยืน, การ integrate กับ DB ของ third-party, การติดตามเป้าหมายความยั่งยืน | `tb_product.certification` เป็นคอลัมน์ `Json @db.JsonB` เดียวพร้อม default `{}` **ไม่มีโมเดล `tb_product_carbon_footprint`** ไม่มีโมเดล `tb_product_sustainability_rating` และไม่มี typing ของ certification ระดับ schema ข้อมูลความยั่งยืนทั้งหมดอยู่ใน `certification` JSON | document ธรรมเนียมรูปทรง JSON (เช่น `certification: { carbonFootprintKgCo2e: <n>, certifications: ['organic', 'fair-trade'], packagingMaterial: '...' }`) และยอมรับว่าฟีเจอร์ความยั่งยืนรุ่มรวยใน PRD เป็น application-layer หรือ schema อนาคต |
| 7 | วิธีการคิดต้นทุนต่อสินค้า (FIFO / Weighted Average) | `inventory-management-prd.md` และการอภิปรายที่ derive จาก `PROD-PRD.md` บ่งบอก `valuationMethod: FIFO | WEIGHTED_AVERAGE` ตั้งค่าต่อสินค้า | **วิธีการคิดต้นทุนไม่ได้อยู่บน `tb_product`** อยู่บน `tb_business_unit.calculation_method` (platform schema, `enum_calculation_method = average | fifo`) ใช้ทั่ว property สินค้ามี `standard_cost` (ต้นทุนอ้างอิง) แต่ไม่ใช่ตัวเลือก FIFO / WA | ปรับ carmen/docs ให้อธิบายวิธีการคิดต้นทุนเป็น **ระดับ business-unit** ไม่ใช่ต่อสินค้า document surface runtime-config `enum_business_unit_config_key.calculation_method` คู่ขนานสำหรับ override ระดับ tenant ดู [costing/01-data-model](/th/inventory/costing/01-data-model) § 2.4 |
| 8 | ความลึกของลำดับชั้นหมวดหมู่ ("ลึกได้ถึง 5 ระดับ") | `PROD-PRD.md` § 3.2.2 (FR-CAT-011): "โครงสร้างหมวดหมู่เชิงลำดับชั้นลึกได้ถึง 5 ระดับ" claim ซ้ำใน index | Prisma schema implement **3 ระดับเป๊ะ ๆ**: `tb_product_category → tb_product_sub_category → tb_product_item_group` ไม่มี `tb_product_sub_sub_category` หรือ `parent_id` self-referential บนหมวดหมู่ ห้าระดับไม่ได้รับการรองรับโดย canonical schema | อัปเดต carmen/docs ให้บอก "การจำแนกสามระดับ (หมวดหมู่ → หมวดหมู่ย่อย → กลุ่มสินค้า)" ถ้าจำเป็นต้องการลำดับชั้นที่ลึกกว่าเชิงปฏิบัติการ ต้องมาจาก schema change (`parent_id` self-referential บน `tb_product_category` และ migration ของ sub-category / item-group) |
| 9 | การ validate Conversion Factor สองทิศทาง | `PROD-PRD.md` § 3.3.2 (FR-UNT-011..020): การแปลงสองทิศทาง การ validate การแปลงวงกลม ความสมบูรณ์ของ conversion factor การแปลงซับซ้อนข้ามหลาย unit type | `tb_unit_conversion` มี `from_unit_qty` / `to_unit_qty` บนแต่ละแถว "conversion factor" คือ `to_unit_qty / from_unit_qty` ความสอดคล้องสองทิศทาง (`from → to → from` round-trip ที่แน่นอน) **validate ที่ application layer** ตอน row create / update — ไม่มี constraint ระดับ schema บังคับความสอดคล้องข้ามหลายแถวสำหรับ `(product_id, unit_type)` เดียวกัน การตรวจจับวงกลมก็เป็น application-only เช่นกัน | document ว่าการตรวจสอบสองทิศทาง / วงกลมอยู่ใน service layer ถ้ายังไม่ได้ implement log เป็น backlog item Schema อนุญาตให้แถวไม่สอดคล้องกัน application guard คือสิ่งที่ทำให้สอดคล้องกัน |
| 10 | code Sub-category เป็นทางเลือก | `PROD-PRD.md` § 3.2: บ่งบอกว่า code จำเป็นที่ทุกระดับการจำแนก | `tb_product_sub_category.code` ประกาศ `String @db.VarChar` (non-null) แต่ **มี `@default("")`** — กล่าวคือ empty string เป็น value ที่ถูกต้องที่ระดับ schema นี่ผิดปกติ `tb_product_category.code` และ `tb_product_item_group.code` non-null โดยไม่มี default | document quirk ของ schema: UI ของ application ต้องการ code บน sub-category แต่ schema อนุญาต empty string สำหรับ legacy / migration `@@unique` บน sub-category คือ `(code, name, deleted_at)` ดังนั้น sub-category ที่ code ว่างได้รับอนุญาตตราบใดที่ `name` ไม่ซ้ำใน deleted_at-scope |
| 11 | Product Template และ Bulk Operation | `PROD-PRD.md` § 3.1.1 / FR-PRD-006..008: การสร้าง / แก้เป็นชุด, product template, duplicate-as-starting-point | ไม่มีโมเดล `tb_product_template` การสร้าง / แก้เป็นชุดเป็น application-layer (CSV / Excel import) flow UI "template" เป็น frontend convenience ที่ผลิต `tb_product` insert หลายตัวใน transaction เดียว | document template และ bulk operation เป็น application-layer / frontend convenience โดยไม่มี schema backing |
| 12 | Standard vs Last Receiving Cost | `product-master-prd.md` § 3.2.6: อภิปราย Standard Cost และ "Last Receiving Cost" เป็นตัวเลขที่จับคู่กันบนสินค้า | `tb_product.standard_cost` มี **`last_receiving_cost` ไม่ใช่คอลัมน์** บน `tb_product` "last receiving cost" ที่อ้างใน carmen/docs **derive** จาก `tb_inventory_transaction_cost_layer` (แถว inbound ล่าสุดที่ `(product_id, *)` พร้อม `transaction_type ∈ {good_received_note, adjustment_in}`) source GRN / vendor / date ก็ derive จากลิงก์ source-document ของ inventory transaction | อัปเดต carmen/docs ให้อธิบาย `lastReceivingCost` เป็น **ฟิลด์ที่ derive** อ่านจาก inventory ledger ไม่ใช่คอลัมน์ที่เก็บ Header ของสินค้าแสดงผ่าน join ไม่ใช่ผ่าน column read |
| 13 | Product–Vendor Mapping พร้อม Preferred / Primary Vendor | `PROD-PRD.md` § 6.2 (IR-PROC-009): การกำหนด preferred vendor สำหรับสินค้า | `tb_product_tb_vendor` มี join product–vendor แต่ **ไม่มีคอลัมน์ `is_preferred` / `is_primary`** ผู้ขายหลายรายสามารถถูกเชื่อมโยงกับสินค้าได้และ application โดยทั่วไปใช้ราคา `tb_pricelist` ล่าสุดหรือ vendor ranking ไม่ใช่ flag | document ว่าการกำหนด preferred-vendor **derive** (pricelist ล่าสุด ราคาต่ำสุด หรือกฎที่ตั้งค่าได้ที่ application) แทนที่จะเก็บ เพิ่มคอลัมน์ `is_preferred` ไปยัง `tb_product_tb_vendor` ถ้าต้องการการกำหนด preferred-vendor ระดับ first-class |
| 14 | flag Active สองตัว | `PROD-PRD.md` § 3.1.5: enum สถานะตัวเดียว | สินค้ามี **สอง** flag Active: `product_status_type ∈ {active, inactive}` และ `is_active: Boolean? @default(true)` ความแตกต่างเชิงความหมาย (ตาม Section 2.1) คือ `product_status_type = inactive` ลบสินค้าจาก picker ธุรกรรมใหม่แต่ admin ยังเห็น `is_active = false` เป็น hard-disable ที่ลบสินค้าทุกที่ ในทางปฏิบัติ flag ทั้งสองมักถูกเก็บให้ตรงกัน | document รูปแบบ flag สองตัว แนะนำ application บังคับว่า `is_active = false` หมายถึง `product_status_type = inactive` เสมอ (ทางกลับไม่จำเป็น) |

## 6. แหล่งอ้างอิง

- **หลัก (แหล่งความจริง):** Prisma schema ที่ list ใน header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` สำหรับเอนทิตี product (`tb_product`, `tb_product_category`, `tb_product_sub_category`, `tb_product_item_group`, `tb_unit`, `tb_unit_conversion`, `tb_product_location`, `tb_product_tb_vendor` และตาราง comment คู่ขนาน) และ enum `enum_product_status_type`, `enum_unit_type` platform schema `prisma-shared-schema-platform/prisma/schema.prisma` มี `tb_business_unit.calculation_method` และ `enum_calculation_method` อ้างจากมุมมอง costing
- **รอง (cross-check แนวคิด):**
  - `../carmen/docs/product-management/PROD-PRD.md` — PRD หลักอธิบายชุดฟีเจอร์ product-management ความแตกต่างใน Section 5 (รายการ 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14)
  - `../carmen/docs/product-management/product-master-prd.md` — product-master PRD อธิบายโครงสร้าง UI (List page, Detail page พร้อม tab, Latest Purchase tab) และข้อกำหนดเชิงฟังก์ชัน ความแตกต่างใน Section 5 (รายการ 1, 6, 12)
  - `../carmen/docs/product-management/README.md` — index ของโมดูล
  - `../carmen/docs/product-management/PROD-API-Endpoints-*.md` — แคตตาล็อก REST endpoint (Products, Categories, Units, Locations, Import-Export, Overview) ไม่ใช้สำหรับ schema authority แต่มีประโยชน์สำหรับ surface-area reference
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ทุก inventory balance และ cost-layer อ้างอิงสินค้า การเปิดใช้ / ปิดใช้ของสินค้า gate ธุรกรรมคลังใหม่), [costing](/th/inventory/costing) (บริโภค `tb_product.standard_cost` วิธีการคิดต้นทุนอยู่ที่ `tb_business_unit.calculation_method` ไม่ใช่บนสินค้า), [vendor-pricelist](/th/inventory/vendor-pricelist) (บรรทัด pricelist อ้างอิงสินค้าผ่าน `product_id` การ map ผู้ขายมาผ่าน `tb_product_tb_vendor`), [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) (ทุกบรรทัดอ้างอิงสินค้า), [store-requisition](/th/inventory/store-requisition) (บรรทัดเบิก / โอนอ้างอิงสินค้า), [recipe](/th/inventory/recipe) (บรรทัดวัตถุดิบของสูตรอ้างอิงสินค้าเป็น `product_id` และ sub-recipe อ้างอิงสูตรอื่น — สินค้าที่ `is_used_in_recipe = true` ปรากฏบน picker), [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) / [inventory-adjustment](/th/inventory/inventory-adjustment) (เอกสาร count และ adjustment อ้างอิงสินค้า)
