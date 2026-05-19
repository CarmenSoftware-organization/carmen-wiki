---
title: หน่วยนับ (Unit)
description: หน่วยนับและการแปลงระหว่างหน่วยที่ใช้โดยเอกสารธุรกรรมและระเบียนสินค้าทุกใบ
published: true
date: 2026-05-19T23:55:00.000Z
tags: master-data, unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# หน่วยนับ (Unit)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_unit`, `tb_unit_conversion` &nbsp;·&nbsp; **ใช้โดย:** product, recipe, PR / PO / GRN / SR / inventory / costing &nbsp;·&nbsp; หน่วย inventory + order และตัวคูณระหว่างกัน

![หน่วยนับ (Unit) screen](/screenshots/master-data/unit.png)

## 1. คืออะไร / ใครใช้

**หน่วยนับ** เป็นแคตตาล็อกของทุกหน่วยที่ใช้สำหรับปริมาณ ราคา และยอดคงเหลือ — ทั้งหน่วย **inventory/ingredient** (kg, L, each) และหน่วย **order/purchase** (case-of-12, sack-25kg) ทุกบรรทัดที่มีราคาหรือนับใน Carmen บรรจุการอ้างอิงหน่วยอย่างน้อยหนึ่งรายการ ดังนั้นนี่คือชิ้นส่วนข้อมูลหลักที่เล็กที่สุดที่สัมผัสกับทุกโมดูลธุรกรรม

ตารางคู่กัน `tb_unit_conversion` เก็บ **ตัวคูณระหว่างสองหน่วย** เลือก scope ต่อสินค้าได้ Conversion ขับเคลื่อนการแปลง purchase-to-inventory ใน GRN, การคำนวณ yield ของ recipe และการเปรียบเทียบ pricelist ระหว่างผู้ขายที่เสนอราคาด้วย pack size ต่างกัน **หากไม่มี conversion ที่ถูกต้อง ตัวเลข costing และยอดคงเหลือทุกตัวที่อยู่ปลายน้ำจะผิด** บริหารจัดการโดย Product Admin; อ่านโดยทุกเส้นทางธุรกรรม

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มหน่วย | Configuration → Master Data → Unit → **New** | บังคับ: `name`; `decimal_place` default `2` |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจากธุรกรรมใหม่; บรรทัดประวัติไม่เปลี่ยน |
| เพิ่ม conversion แบบ global | Conversion matrix | `product_id = NULL`; เลือก `unit_type`, from-unit/qty, to-unit/qty |
| เพิ่ม conversion ต่อสินค้า | Product detail → Conversions | ทับ global สำหรับสินค้านั้น |
| ตั้ง conversion default | Toggle `is_default` | Primary เมื่อมีหลาย conversion สำหรับคู่เดียวกัน |
| Identity conversion | from/to เหมือนกันด้วย qty เท่ากัน | อนุญาต; มิฉะนั้นต้อง from ≠ to |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Duplicate unit name" | `name` เดิม active อยู่แล้ว (case-insensitive) | Reactivate แถวที่มี หรือเลือกชื่ออื่น |
| "Conversion qty must be > 0" | `from_unit_qty` หรือ `to_unit_qty` เป็นศูนย์/ค่าลบ | ใส่ค่าบวก |
| "Same-unit conversion needs equal qty" | `from_unit_id == to_unit_id` แต่ qty ต่าง | ใช้ identity (`1 = 1`) หรือเลือกคู่อื่น |
| "Conversion already exists for this product/pair" | ละเมิด unique constraint | แก้แถวที่มี |
| "Cannot delete — unit in use" | สินค้า, recipe หรือ posting ที่ active อ้างอิงหน่วย | ใช้ inactivate แทน |

## 4. Edge Cases

- **Uniqueness บน `name` บังคับใช้ระดับ app** (ไม่มี DB unique constraint) — case-insensitive duplicate อาจรอดผ่านได้ถ้า app validation ถูก bypass
- **`decimal_place` คือ rendering เท่านั้น** — storage เป็น `Decimal(20, 5)`
- **Conversion ต่อสินค้าทับ global** — resolution เลือกแถว product-scoped ก่อน
- **Identity conversion อนุญาต** แต่เฉพาะกับ `qty` เท่ากันทั้งสองข้าง
- **หน่วย inactive** ยังอ่านได้บนเอกสารย้อนหลัง; ไม่สามารถเลือกในธุรกรรมใหม่
- **`enum_unit_type`** แยกแยะ `order_unit` กับ `ingredient_unit` — เส้นทาง resolution ต่างกันระหว่าง GRN และ recipe

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_unit`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`) |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล เช่น `kg`, `each`, `case` |
| `description` | `String? @db.VarChar` | Yes | คำอธิบายแบบ free text |
| `is_active` | `Boolean?` | Yes | Active flag, default `true` |
| `decimal_place` | `Int` | No | Precision สำหรับ render (default `2`) |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `info` | `Json?` | Yes | Metadata (`{}` default) |
| `dimension` | `Json?` | Yes | Array ของ dimension tag |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** primary key บน `id` Soft-delete ผ่าน `deleted_at` ไม่มี unique บน `name` ที่ชัดเจน — บังคับใช้ระดับ app กับแถว active

### 5.2 `tb_unit_conversion`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `product_id` | `String? @db.Uuid` | Yes | Product scope (เลือก); `NULL` = global |
| `unit_type` | `enum_unit_type` | No | `order_unit` หรือ `ingredient_unit` |
| `from_unit_id` / `from_unit_name` / `from_unit_qty` | — | Mixed | ฝั่งต้นทาง `qty` default `0`, `Decimal(20,5)` |
| `to_unit_id` / `to_unit_name` / `to_unit_qty` | — | Mixed | ฝั่งปลายทาง |
| `decimal_place` | `Int` | No | Precision render สำหรับ qty ที่แปลง |
| `is_default` | `Boolean?` | Yes | Primary เมื่อมีหลาย conversion สำหรับคู่เดียวกัน |
| `description` | `Json?` | Yes | คำอธิบาย localised |
| `is_active`, `note`, `info`, `dimension` | — | Mixed | activation / metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([product_id, unit_type, from_unit_id, to_unit_id, deleted_at])` ชื่อ `unitconversion_product_unit_type_from_unit_to_unit_deletedat_u` Index บน prefix เดียวกัน FK ทั้งสองไปยัง `tb_unit` `onDelete: NoAction`

`enum_unit_type` values: `order_unit`, `ingredient_unit`

## 6. กติกาทางธุรกิจ

- **Uniqueness** App enforce ไม่ให้ `name` หน่วย active ซ้ำ (case-insensitive) Conversion unique ต่อ `(product_id, unit_type, from_unit_id, to_unit_id)` ในแถว non-deleted
- **Deletion guards** การอ้างอิงจาก product/recipe/posting ที่ active บล็อก hard-delete — ใช้ inactivate
- **Validation** Conversion `from_unit_qty` และ `to_unit_qty` ต้อง `> 0` ทั้งคู่ คู่หน่วยเดียวกันต้อง qty เท่ากันเท่านั้น
- **Lifecycle** หน่วย inactive มองเห็นบนเอกสารย้อนหลัง; ถูก lock จากธุรกรรมใหม่
- **Decimal precision** `decimal_place` คือ rendering เท่านั้น; storage `Decimal(20,5)`

## 7. การอ้างอิงข้ามโมดูล

- [product](/th/inventory/product) — ทุกสินค้ามี order/ingredient/inventory unit refs และ conversion set ต่อสินค้า
- [recipe](/th/inventory/recipe) — บรรทัด recipe ใช้ ingredient unit; yield แปลงเป็น inventory unit
- [purchase-request](/th/inventory/purchase-request) — requested / approved / FOC qty บรรจุ unit FK
- [purchase-order](/th/inventory/purchase-order) — order_unit และ base_unit ต่อบรรทัด detail
- [good-receive-note](/th/inventory/good-receive-note) — คอลัมน์ ordered / received / FOC unit; ใช้ conversion เพื่อ post inventory qty
- [store-requisition](/th/inventory/store-requisition) — บรรทัด requisition บรรจุ unit reference
- [inventory](/th/inventory/inventory) — ยอดคงเหลือเก็บใน inventory unit; conversion แปลงจาก receipt
- [inventory-adjustment](/th/inventory/inventory-adjustment) — adjustment qty ใน inventory unit
- [costing](/th/inventory/costing) — costing engine บริโภคยอดคงเหลือใน inventory unit

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_unit` (lines ~3132-3208), `tb_unit_conversion` (lines ~3210-3246), `enum_unit_type` (lines ~254-257)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/unit/`
