---
title: หมวดหมู่อุปกรณ์ (Equipment Category)
description: การจัดกลุ่มตามฟังก์ชันสำหรับอุปกรณ์ครัว — preparation, cooking, holding, refrigeration, dispense, cleaning ฯลฯ
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, equipment, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# หมวดหมู่อุปกรณ์ (Equipment Category)

> **At a Glance**
> **เจ้าของ:** Chef / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_recipe_equipment_category` &nbsp;·&nbsp; **รูปทรง:** แบน (ไม่มี `parent_id`) &nbsp;·&nbsp; **ลูก:** [recipe/equipment](/th/inventory/recipe/equipment) ผ่าน `category_id` &nbsp;·&nbsp; **ใช้โดย:** filter ของ equipment picker, dashboard maintenance, checklist การ fit-out

![หมวดหมู่อุปกรณ์ (Equipment Category) screen](/screenshots/recipe/equipment-category.png)

## 1. คืออะไรและใครใช้

หมวดหมู่อุปกรณ์จัดกลุ่มอุปกรณ์ครัวตาม **ฟังก์ชัน** — ค่าทั่วไปคือ `Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense` และ `Cleaning` ขับเคลื่อนการกรองใน equipment picker กำหนดขอบเขต dashboard maintenance และป้อน checklist การ fit-out ของ property ("ครัวนี้มีอย่างน้อยหนึ่งชิ้นในทุกหมวดหมู่หรือไม่?")

**taxonomy แบน** — ไม่มี `parent_id` ต่างจาก [recipe/category](/th/inventory/recipe/category) ที่เชิงลำดับชั้น การจำแนกย่อยใช้ฟิลด์ `station` อิสระบนแถวอุปกรณ์ **ดูแลโดย Chef** (หรือ **Product Admin**) ภายใต้ Operation Plan → Equipment Category tenant ส่วนใหญ่ seed ครั้งเดียวตอน onboarding และไม่ค่อยแก้

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Seed หมวดหมู่เริ่มต้น | Operation Plan → Equipment Category → **+ New** | seed ทั่วไป: `Preparation`, `Cooking`, `Holding`, `Refrigeration`, `Dispense`, `Cleaning`, `Smallwares`, `Other` |
| เปลี่ยนชื่อหมวดหมู่ | edit dialog → `name` | trigger การรีเฟรช fan-out ของ `category_name` บนอุปกรณ์ที่เกี่ยวข้อง |
| ปลดประจำการหมวดหมู่ | edit dialog → `is_active = false` | ซ่อนจาก picker อุปกรณ์ในประวัติไม่ได้รับผลกระทบ |
| Hard-delete หมวดหมู่ | App ปฏิเสธถ้ามี ref ของอุปกรณ์ | ใช้ soft-delete + inactive แทน |
| ตรวจสอบ route ที่เป็น canonical | `/operation-plan/equipment-category/` | route เก่า `/recipe-equipment-category/` อาจมีอยู่ — ยืนยันการ wire |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Name already exists" | `@@unique([name, deleted_at])` ละเมิด | เลือกชื่ออื่น (หรือ restore แถวที่ลบ) |
| "Name is required" | ฟิลด์จำเป็นว่าง | กรอกก่อน save |
| "Cannot delete: equipment references this category" | guard ที่ชั้น app — DB FK เป็น `NoAction` และจะไม่บล็อก | reassign หรือปลดประจำการอุปกรณ์ที่อ้างอิงก่อน |
| แถวอุปกรณ์แสดง `category_name` เก่าหลังเปลี่ยนชื่อ | handler fan-out ไม่ได้ wire หรือข้าม | save หมวดหมู่ใหม่ หรือ save แถวอุปกรณ์ใหม่ |
| Picker แสดงรายการดูเหมือนซ้ำ | สอง route (`equipment-category` / `recipe-equipment-category`) wire คู่ขนาน | ตรวจสอบว่าการ navigate production ไปที่ route canonical |

## 4. Edge Cases

- **ไม่มีลำดับชั้น** schema ไม่มี `parent_id` — การจำแนกย่อยต้องใช้ `station` บนแถวอุปกรณ์ หรือเปิด schema change
- **FK เป็น `onDelete: NoAction`** ในฝั่งอุปกรณ์ DB ไม่ cascade ก็ไม่บล็อก application ต้องปฏิเสธ hard-delete เพื่อหลีกเลี่ยง string `category_name` ที่ค้าง
- **`category_name` ที่ denormalise** บนอุปกรณ์ดูแลโดย application — ยืนยันว่าการ fan-out การเปลี่ยนชื่อถูก wire ใน handler ของ save ก่อนสันนิษฐาน auto-propagation
- **สอง route ของ frontend** ในประวัติ render เอนทิตีเดียวกัน (`equipment-category` canonical vs. `recipe-equipment-category` legacy) — ตรวจสอบว่าตัวไหนใน build ปัจจุบัน

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_recipe_equipment_category`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `Cooking`, `Refrigeration`) |
| `description`, `note` | `String? @db.VarChar` | Yes | ข้อความอิสระ / โน้ตภายใน |
| `is_active` | `Boolean?` | Yes | flag active, default `true` |
| `info`, `dimension` | `Json?` | Yes | metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `recipe_equipment_category_name_u` index บน `name` reverse relation `tb_recipe_equipment` แสดงลูกผ่าน `category_id` (`onDelete: NoAction` บนฝั่งอุปกรณ์)

## 6. กติกาทางธุรกิจ

- **ความไม่ซ้ำ** `name` ไม่ซ้ำในแถวที่ไม่ถูกลบ (บังคับใช้ที่ DB)
- **โครงสร้างแบน** ไม่มี `parent_id` — ไม่สามารถสร้าง model ลำดับชั้น ใช้ `station` บนอุปกรณ์ หรือ schema change
- **Deletion guards** FK `onDelete: NoAction` — DB จะไม่ป้องกัน application ต้องปฏิเสธ hard-delete ในขณะที่มี ref ของอุปกรณ์ soft-delete + inactive คือการปลดประจำการที่รองรับ
- **การกระจายการเปลี่ยนชื่อ** ควรรีเฟรช `category_name` ที่ denormalise บนทุกแถว `tb_recipe_equipment` ที่เกี่ยวข้องผ่าน fan-out ของ application (FK เป็น `onUpdate: NoAction`)
- **การ validate** `name` จำเป็น
- **วงจรชีวิต** หมวดหมู่ inactive ยังอ่านได้บนอุปกรณ์ในประวัติ ซ่อนจาก picker

## 7. Cross-References

- [recipe/equipment](/th/inventory/recipe/equipment) — ลูกผ่าน `category_id` มี `category_name` ที่ denormalise
- [recipe](/th/inventory/recipe) — โดยอ้อม equipment-category ปรากฏเป็น filter ใน equipment picker ของขั้นตอนการเตรียม
- [recipe/03-user-flow-chef](/th/inventory/recipe/03-user-flow-chef) — Chef ใช้ filter หมวดหมู่เมื่อหยิบอุปกรณ์

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment_category` (lines ~5226-5247)
- **Frontend routes:** `../carmen-inventory-frontend/app/(root)/operation-plan/equipment-category/` (canonical); `../carmen-inventory-frontend/app/(root)/operation-plan/recipe-equipment-category/` (legacy — ยืนยันการ wire)
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
