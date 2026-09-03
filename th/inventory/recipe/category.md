---
title: หมวดหมู่สูตรอาหาร (Recipe Category)
description: taxonomy หมวดหมู่เชิงลำดับชั้นสำหรับสูตรอาหาร — ขับเคลื่อน menu engineering, รายงาน cost-band และการนำทาง recipe library
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, category, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# หมวดหมู่สูตรอาหาร (Recipe Category)

> **At a Glance**
> **เจ้าของ:** Chef / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_recipe_category` &nbsp;·&nbsp; **รูปทรง:** ต้นไม้เชิงลำดับชั้น (self-FK บน `parent_id`) &nbsp;·&nbsp; **ใช้โดย:** ส่วนหัวของ [recipe](/th/inventory/recipe), menu engineering, รายงาน cost-band &nbsp;·&nbsp; **Seed:** `default_cost_settings` + `default_margins` ลงในสูตรใหม่

![หมวดหมู่สูตรอาหาร (Recipe Category) screen](/screenshots/recipe/category.png)

![หมวดหมู่สูตรอาหาร (Recipe Category) detail screen](/screenshots/recipe/category-detail.png)

## 1. คืออะไรและใครใช้

หมวดหมู่สูตรอาหารคือ **การจำแนกประเภทตามฟังก์ชัน** เหนือข้อมูลหลักของสูตรอาหาร จัดเรียงเป็นต้นไม้ (เช่น `Food > Main Course > Pasta`) แต่ละหมวดหมู่มี **การตั้งค่าต้นทุน default** และ **margin default** ที่สูตรใหม่สืบทอดตอนสร้าง — ดังนั้น property บอกว่า "สูตร Main Course ทุกตัวเป้าหมาย food-cost 30%" ครั้งเดียว ไม่ใช่ต่อสูตร

แตกต่างจาก [recipe/cuisine](/th/inventory/recipe/cuisine) (label ตามภูมิภาคแบน) และ `Course Type` (enum ต่อสูตร) **ดูแลโดย Chef** (หรือ **Product Admin** ใน tenant บางตัว) ภายใต้ Operation Plan → Recipe Category

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มหมวดหมู่ย่อยใหม่ | Operation Plan → Recipe Category → **+ Add** → เลือก **Parent Category** จาก dropdown | list/grid เป็น `DataGrid` แบน (`recipe-category-component.tsx`) — ไม่มี widget ต้นไม้ `level` ถูกคำนวณฝั่ง server จาก `level + 1` ของ parent ที่เลือก |
| Reparent หมวดหมู่ | ฟอร์ม edit → เปลี่ยน dropdown **Parent Category** | คำนวณ `level` ใหม่เฉพาะแถวที่แก้เท่านั้น (`recipe-category.service.ts` `update()`) `level` ของ descendant ไม่ถูกแตะ |
| แก้ % food-cost เป้าหมายของหมวดหมู่ | หน้า edit (`/operation-plan/category/:id`) → **Default Cost Settings** | กระทบเฉพาะสูตร *ใหม่* — ไม่อัปเดตสูตรเดิม (ไม่มี code path ที่อ่าน default ของหมวดหมู่กลับเข้าแถว `tb_recipe` ที่มีอยู่แล้ว) |
| ปลดประจำการหมวดหมู่ | หน้า edit → ตั้ง `is_active = false` | สูตรในประวัติยังอ่านได้ ซ่อนจาก picker |
| Hard-delete หมวดหมู่ | ไม่อนุญาตถ้ามีลูกหรือสูตรอ้างอิง | ใช้ soft-delete + inactive แทน |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Recipe category code already exists" (`RECIPE_CATEGORY_CODE_ALREADY_EXISTS`) | `code` ชนกันทั่ว tenant แบบ case-insensitive ในแถวที่ไม่ถูกลบ (`recipe-category.service.ts`) | เลือก code ที่ไม่ซ้ำ |
| "Cannot delete: category has children" (`RECIPE_CATEGORY_HAS_SUBCATEGORIES`) | การนับลูก `parent_id` ที่ไม่ถูกลบที่ระดับ application ก่อนลบ | reparent หรือ soft-delete ลูกก่อน |
| "Cannot delete: recipes still reference this category" (`RECIPE_CATEGORY_IN_USE`) | การนับการอ้างอิง `tb_recipe.category_id` ที่ไม่ถูกลบที่ระดับ application ก่อนลบ | reassign สูตรแล้วปลดประจำการ |
| "Category cannot be its own parent" (`RECIPE_CATEGORY_CANNOT_BE_OWN_PARENT`) | เฉพาะการอ้างอิงตัวเองตรง ๆ เท่านั้น (`parent_id === id`) | เลือก parent อื่น — นี่คือการตรวจ cycle เพียงอย่างเดียว cycle หลายระดับ (reparent หมวดหมู่ไปอยู่ใต้หลานของตัวเอง) **ไม่** ถูกตรวจจับ |
| "Parent category not found" (`RECIPE_CATEGORY_PARENT_NOT_FOUND`) | `parent_id` ไม่ resolve เป็นแถวที่ไม่ถูก soft-delete | เลือก parent ที่มีอยู่จริง — การตรวจ **ไม่** บังคับให้ parent ต้อง `is_active = true` แค่ไม่ถูกลบเท่านั้น |

## 4. Edge Cases

- **ไม่มี tree UI** หน้าจอ list/detail ใช้ pattern `DataGrid` แบน + form เดียวกับหน้าจอ config อื่นทุกหน้าในโมดูลนี้ ลำดับชั้นแสดงออกผ่าน dropdown `parent_id` และตัวเลข `level` ที่ derive มาเท่านั้น ไม่ใช่ต้นไม้แบบภาพ
- **การตรวจจับ cycle ตื้น** ปฏิเสธเฉพาะการเป็น parent ของตัวเองตรง ๆ (`RECIPE_CATEGORY_CANNOT_BE_OWN_PARENT`) การ reparent หมวดหมู่ไปอยู่ใต้ descendant ของตัวเองไม่ถูกตรวจที่ไหนเลยใน `recipe-category.service.ts` และจะสร้าง cycle อย่างเงียบ ๆ
- **การกระจาย default** การอัปเดต `default_cost_settings` / `default_margins` ไม่ retroactively กระทบสูตรเดิม — พวกเขามี snapshot ของตัวเองจากตอนสร้าง (ไม่มี fan-out job ใน `recipe-category.service.ts` หรือ `recipe.service.ts`)
- **Reparenting ไม่ cascade `level`** การย้ายหมวดหมู่คำนวณ `level` ใหม่เฉพาะของหมวดหมู่นั้นเองเท่านั้น หมวดหมู่ย่อยใด ๆ ใต้มันเก็บค่า `level` เดิมไว้จนกว่าแต่ละตัวจะถูก save ใหม่ทีละตัว
- **หมวดหมู่ inactive** ยังอ่านได้บนสูตรในประวัติ แต่ซ่อนจาก picker สร้างสูตร
- **ไม่มี DB unique constraint** บน `name` หรือ `code` — ความไม่ซ้ำบังคับใช้ที่ application (case-insensitive บน `code` เท่านั้น `name` ไม่มีการตรวจความไม่ซ้ำเลย ทั้งระดับพี่น้องและทั่ว tenant) ดังนั้น SQL insert ตรงสามารถ bypass ได้

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_recipe_category`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | code สั้น (เช่น `MAIN`, `BEV-HOT`) |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description`, `note` | `String? @db.VarChar` | Yes | ข้อความอิสระ / โน้ตภายใน |
| `is_active` | `Boolean?` | Yes | flag active, default `true` |
| `parent_id` | `String? @db.Uuid` | Yes | Self-FK ไปยัง parent (null = root) |
| `level` | `Int` | No | ความลึกจาก root, default `1` Materialised |
| `default_cost_settings` | `Json @db.JsonB` | No | % food-cost เป้าหมาย, การปัดเศษ, labor/overhead — seed สูตรใหม่ |
| `default_margins` | `Json @db.JsonB` | No | เป้าหมาย gross-margin default |
| `info`, `dimension` | `Json?` | Yes | metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** Self-relation `CategoryHierarchy` บน `parent_id` พร้อม `onDelete: Restrict` reverse relation ไปยัง `tb_recipe.category_id` (ก็ `onDelete: Restrict` เช่นกัน) ไม่มี `@@unique` ที่ระดับ schema — ความไม่ซ้ำบังคับใช้ที่ application

## 6. กติกาทางธุรกิจ

- **ความไม่ซ้ำ (app)** `code` ไม่ซ้ำทั่ว tenant แบบ case-insensitive ในแถวที่ไม่ถูกลบ **ไม่มี** การตรวจความไม่ซ้ำของ `name` — หมวดหมู่ชื่อเดียวกัน (พี่น้องหรือไม่เกี่ยวข้องกัน) เป็นสิ่งที่อนุญาต
- **Reparenting** คำนวณ `level` ใหม่เฉพาะแถวที่ย้ายเท่านั้น (`parent.level + 1`) ไม่ cascade ไปยัง descendant การปฏิเสธ cycle ครอบคลุมเฉพาะการเป็น parent ของตัวเองตรง ๆ ไม่ครอบคลุม cycle ที่ลึกกว่า
- **Deletion guards** การนับที่ระดับ application (`RECIPE_CATEGORY_HAS_SUBCATEGORIES`, `RECIPE_CATEGORY_IN_USE`) บล็อกการลบในขณะที่มีลูกหรือสูตรอยู่ — ไม่ใช่ความล้มเหลวของ cascade `Restrict` ที่ระดับ database
- **Default seed ตอน create เท่านั้น** — ไม่ retroactive ตอน update
- **การ validate** `code`, `name` จำเป็น `parent_id` (ถ้าตั้ง) ต้องอ้างอิงหมวดหมู่ที่ไม่ถูก soft-delete — `is_active` ไม่ถูกตรวจบน parent

## 7. Cross-References

- [recipe](/th/inventory/recipe) — สูตรทุกตัวมี `category_id` (จำเป็น) อ่าน default ของหมวดหมู่ตอนสร้าง
- [recipe/cuisine](/th/inventory/recipe/cuisine) — taxonomy พี่น้องบนแกนภูมิภาค
- [recipe/01-data-model](/th/inventory/recipe/01-data-model) — บริบทโมเดลข้อมูลเต็ม
- [recipe/03-user-flow-chef](/th/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-cost-controller](/th/inventory/recipe/03-user-flow-cost-controller) — Chef หยิบ Cost Controller ตั้ง default หมวดหมู่

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_category` (lines ~5314-5350)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/operation-plan/category/`
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
