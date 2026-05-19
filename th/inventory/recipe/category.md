---
title: หมวดหมู่สูตรอาหาร (Recipe Category)
description: taxonomy หมวดหมู่เชิงลำดับชั้นสำหรับสูตรอาหาร — ขับเคลื่อน menu engineering, รายงาน cost-band และการนำทาง recipe library
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, category, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# หมวดหมู่สูตรอาหาร (Recipe Category)

> **At a Glance**
> **เจ้าของ:** Chef / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_recipe_category` &nbsp;·&nbsp; **รูปทรง:** ต้นไม้เชิงลำดับชั้น (self-FK บน `parent_id`) &nbsp;·&nbsp; **ใช้โดย:** ส่วนหัวของ [recipe](/th/inventory/recipe), menu engineering, รายงาน cost-band &nbsp;·&nbsp; **Seed:** `default_cost_settings` + `default_margins` ลงในสูตรใหม่

![หมวดหมู่สูตรอาหาร (Recipe Category) screen](/screenshots/recipe/category.png)

## 1. คืออะไรและใครใช้

หมวดหมู่สูตรอาหารคือ **การจำแนกประเภทตามฟังก์ชัน** เหนือข้อมูลหลักของสูตรอาหาร จัดเรียงเป็นต้นไม้ (เช่น `Food > Main Course > Pasta`) แต่ละหมวดหมู่มี **การตั้งค่าต้นทุน default** และ **margin default** ที่สูตรใหม่สืบทอดตอนสร้าง — ดังนั้น property บอกว่า "สูตร Main Course ทุกตัวเป้าหมาย food-cost 30%" ครั้งเดียว ไม่ใช่ต่อสูตร

แตกต่างจาก [recipe/cuisine](/th/inventory/recipe/cuisine) (label ตามภูมิภาคแบน) และ `Course Type` (enum ต่อสูตร) **ดูแลโดย Chef** (หรือ **Product Admin** ใน tenant บางตัว) ภายใต้ Operation Plan → Recipe Category

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มหมวดหมู่ย่อยใหม่ | Operation Plan → Recipe Category → ต้นไม้ → **+ Child** | สืบทอด default ของ parent สามารถ override ได้ |
| Reparent หมวดหมู่ย่อย | ลากโหนดไปวางที่ parent ใหม่ในมุมมองต้นไม้ | คำนวณ `level` ใหม่สำหรับโหนดที่ย้าย + descendant ทั้งหมด |
| แก้ % food-cost เป้าหมายของหมวดหมู่ | edit dialog → **Default Cost Settings** | กระทบเฉพาะสูตร *ใหม่* — ไม่อัปเดตสูตรเดิม |
| ปลดประจำการหมวดหมู่ | edit dialog → ตั้ง `is_active = false` | สูตรในประวัติยังอ่านได้ ซ่อนจาก picker |
| Hard-delete หมวดหมู่ | ไม่อนุญาตถ้ามีลูกหรือสูตรอ้างอิง | ใช้ soft-delete + inactive แทน |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Code already in use" | `code` ชนกันทั่ว tenant (บังคับใช้ที่ app) | เลือก code ที่ไม่ซ้ำ |
| "Name already exists under this parent" | ชื่อพี่น้องชนกัน (บังคับใช้ที่ app) | เปลี่ยนชื่อหรือเลือก parent อื่น |
| "Cannot delete: category has children" | `parent_id` FK `onDelete: Restrict` | reparent หรือ soft-delete ลูกก่อน |
| "Cannot delete: recipes still reference this category" | `tb_recipe.category_id` FK `onDelete: Restrict` | reassign สูตรแล้วปลดประจำการ |
| "Cycle detected on reparent" | การย้ายจะทำให้โหนดเป็น ancestor ของตัวเอง | เลือก parent อื่น |
| "Parent must be active" | `parent_id` อ้างอิงแถวที่ลบ/inactive | เลือก parent ที่ active |

## 4. Edge Cases

- **ความลึกของลำดับชั้น** ไม่มี cap ของ DB แต่ UI ปกติ cap ที่ 3 ระดับ (root → group → leaf) เพื่อความอ่านง่ายของ menu engineering `level` ถูก materialise ตอน insert/move
- **การกระจาย default** การอัปเดต `default_cost_settings` / `default_margins` ไม่ retroactively กระทบสูตรเดิม — พวกเขามี snapshot ของตัวเองจากตอนสร้าง
- **หมวดหมู่ inactive** ยังอ่านได้บนสูตรในประวัติ แต่ซ่อนจาก picker สร้างสูตร
- **ไม่มี DB unique constraint** บน `name` หรือ `code` — ความไม่ซ้ำบังคับใช้ที่ application ดังนั้น SQL insert ตรงสามารถ bypass ได้

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

- **ความไม่ซ้ำ (app)** `name` ไม่ซ้ำต่อ parent (พี่น้องชนกันไม่ได้) `code` ไม่ซ้ำทั่ว tenant
- **Reparenting** คำนวณ `level` ใหม่สำหรับโหนดที่ย้าย + descendant การตรวจจับ cycle ปฏิเสธการย้ายแบบ self-ancestor
- **Deletion guards** ทั้ง self-FK และ `tb_recipe.category_id` ใช้ `onDelete: Restrict` — hard-delete ถูกบล็อกในขณะที่มีลูกหรือสูตรอยู่
- **Default seed ตอน create เท่านั้น** — ไม่ retroactive ตอน update
- **การ validate** `code`, `name` จำเป็น `level >= 1` `parent_id` (ถ้าตั้ง) ต้องอ้างอิงหมวดหมู่ active ที่ไม่ถูกลบ

## 7. Cross-References

- [recipe](/th/inventory/recipe) — สูตรทุกตัวมี `category_id` (จำเป็น) อ่าน default ของหมวดหมู่ตอนสร้าง
- [recipe/cuisine](/th/inventory/recipe/cuisine) — taxonomy พี่น้องบนแกนภูมิภาค
- [recipe/01-data-model](/th/inventory/recipe/01-data-model) — บริบทโมเดลข้อมูลเต็ม
- [recipe/03-user-flow-chef](/th/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-cost-controller](/th/inventory/recipe/03-user-flow-cost-controller) — Chef หยิบ Cost Controller ตั้ง default หมวดหมู่

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_category` (lines ~5314-5350)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/category/`
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
