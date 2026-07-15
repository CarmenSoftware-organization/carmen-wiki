---
title: หมวดหมู่อุปกรณ์ (Equipment Category)
description: การจัดกลุ่มตามฟังก์ชันสำหรับอุปกรณ์ครัว — preparation, cooking, holding, refrigeration, dispense, cleaning ฯลฯ
published: true
date: 2026-07-16T04:00:00.000Z
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
| เปลี่ยนชื่อหมวดหมู่ | edit dialog → `name` | รีเฟรช `category_name` บนแถวอุปกรณ์เฉพาะเมื่อแถวนั้นถูก save ครั้งถัดไปเท่านั้น — ไม่มี fan-out การเปลี่ยนชื่อจากฝั่งหมวดหมู่ |
| ปลดประจำการหมวดหมู่ | edit dialog → `is_active = false` | ซ่อนจาก picker อุปกรณ์ในประวัติไม่ได้รับผลกระทบ |
| Hard-delete หมวดหมู่ | App ปฏิเสธถ้ามี ref ของอุปกรณ์ | ใช้ soft-delete + inactive แทน |
| มีสอง implementation ของ frontend สำหรับตารางเดียวกันนี้ | `/operation-plan/equipment-category` (อยู่ในเมนู nav ของ Operation Plan, `constant/module-list.ts`) และ `/operation-plan/recipe-equipment-category` (มี route ใน `router.tsx` แต่ **ไม่** อยู่ในเมนู nav) ทั้งสองเรียก endpoint backend เดียวกัน `/api/proxy/api/config/{buCode}/recipe-equipment-categories` (`API_ENDPOINTS.EQUIPMENT_CATEGORIES` และ `API_ENDPOINTS.RECIPE_EQUIPMENT_CATEGORIES` resolve เป็น URL เดียวกัน) ผ่าน tree ของ component/type/hook ที่แยกกัน (`equipment-category-component.tsx` + `types/equipment-category.ts` vs. `recipe-equipment-category-component.tsx` + `types/recipe-equipment-category.ts`) | หน้าจอที่ลิงก์จาก nav คือ `equipment-category` E2E coverage เดียวในตระกูลโมดูลนี้ (`121-recipe-equipment-category.spec.ts`) กลับทดสอบตัวซ้ำ `/operation-plan/recipe-equipment-category` ที่ไม่ได้ลิงก์จาก nav แทน |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Recipe equipment category already exists" (`RECIPE_EQUIPMENT_CATEGORY_ALREADY_EXISTS`) | `@@unique([name, deleted_at])` ละเมิด | เลือกชื่ออื่น (หรือ restore แถวที่ลบ) |
| "Name is required" | ฟิลด์จำเป็นว่าง | กรอกก่อน save |
| "Cannot delete: equipment references this category" (`RECIPE_EQUIPMENT_CATEGORY_NOT_FOUND` / in-use guard) | guard ที่ชั้น app — DB FK เป็น `NoAction` และจะไม่บล็อก | reassign หรือปลดประจำการอุปกรณ์ที่อ้างอิงก่อน |
| แถวอุปกรณ์แสดง `category_name` เก่าหลังเปลี่ยนชื่อ | ไม่มี handler fan-out ใน `recipe-equipment-category.service.ts` เลย — นี่ไม่ใช่บั๊กใน handler เพราะ handler ไม่มีอยู่จริง | save แถวอุปกรณ์ที่ได้รับผลกระทบใหม่ทีละแถว |
| หน้าจอที่ดูเหมือนกันสองหน้าสำหรับข้อมูลเดียวกัน | implementation ซ้ำที่ยืนยันแล้ว (ดู §2) อ่าน/เขียนตาราง `tb_recipe_equipment_category` เดียวกัน | ใช้หน้าจอ `/operation-plan/equipment-category` ที่ลิงก์จาก nav ถือ `/operation-plan/recipe-equipment-category` เป็นตัวซ้ำ legacy ที่รอการรวม |

## 4. Edge Cases

- **ไม่มีลำดับชั้น** schema ไม่มี `parent_id` — การจำแนกย่อยต้องใช้ `station` บนแถวอุปกรณ์ หรือเปิด schema change
- **FK เป็น `onDelete: NoAction`** ในฝั่งอุปกรณ์ DB ไม่ cascade ก็ไม่บล็อก application ต้องปฏิเสธ hard-delete เพื่อหลีกเลี่ยง string `category_name` ที่ค้าง
- **`category_name` ที่ denormalise** บนอุปกรณ์รีเฟรชจากฝั่งอุปกรณ์เท่านั้น (ดู [recipe/equipment](/th/inventory/recipe/equipment)) — ยืนยันแล้วว่าไม่มี fan-out ที่ trigger จากการเปลี่ยนชื่อที่ไหนเลยใน `recipe-equipment-category.service.ts`
- **สอง route ของ frontend render เอนทิตีเดียวกัน** — ยืนยันแล้ว ไม่ใช่แค่เรื่องในอดีต: `equipment-category` (ลิงก์จาก nav) และ `recipe-equipment-category` (มี route แต่ไม่ลิงก์จาก nav และเป็นเป้าหมายเดียวของ E2E spec ตัวเดียวของโมดูล) ทั้งสองอ่าน/เขียน `tb_recipe_equipment_category` ผ่าน REST path เดียวกันข้างใต้

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
- **การกระจายการเปลี่ยนชื่อ** ยืนยันแล้วว่า **ไม่ได้ implement** — `recipe-equipment-category.service.ts` ไม่มี code ที่แตะ `tb_recipe_equipment.category_name` ตอนเปลี่ยนชื่อ string ที่ denormalise รีเฟรชเฉพาะเมื่อแถวอุปกรณ์เองถูก save ครั้งถัดไปเท่านั้น
- **การ validate** `name` จำเป็น
- **วงจรชีวิต** หมวดหมู่ inactive ยังอ่านได้บนอุปกรณ์ในประวัติ ซ่อนจาก picker
- **Frontend ซ้ำ** ตารางนี้ถูก serve โดยสอง feature directory ของ frontend ที่เป็นอิสระต่อกัน (`operation-plan/equipment-category/` และ `operation-plan/recipe-equipment-category/`) — ดู §2

## 7. Cross-References

- [recipe/equipment](/th/inventory/recipe/equipment) — ลูกผ่าน `category_id` มี `category_name` ที่ denormalise
- [recipe](/th/inventory/recipe) — โดยอ้อม equipment-category ปรากฏเป็น filter ใน equipment picker ของขั้นตอนการเตรียม
- [recipe/03-user-flow-chef](/th/inventory/recipe/03-user-flow-chef) — Chef ใช้ filter หมวดหมู่เมื่อหยิบอุปกรณ์

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment_category` (lines ~5226-5247)
- **Frontend routes:** `../carmen-inventory-frontend-react/routes/operation-plan/equipment-category/` (ลิงก์จาก nav, `constant/module-list.ts`); `../carmen-inventory-frontend-react/routes/operation-plan/recipe-equipment-category/` (มี route ใน `router.tsx` ไม่ลิงก์จาก nav — ยืนยันแล้วว่าใช้ REST endpoint เดียวกันผ่าน `constant/api-endpoints.ts`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/121-recipe-equipment-category.spec.ts` — E2E spec ตัวเดียวของโมดูล ทดสอบ `/operation-plan/recipe-equipment-category` (ตัวซ้ำที่ไม่ลิงก์จาก nav) smoke + CRUD เฉพาะ admin
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
