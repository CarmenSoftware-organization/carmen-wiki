---
title: ประเภทอาหาร (Cuisine Type)
description: แคตตาล็อกประเภทอาหาร — label ตามภูมิภาค/สไตล์ที่ใช้กับสูตรอาหารสำหรับการแบ่งกลุ่มเมนู (ไทย อิตาเลียน ฝรั่งเศส ฟิวชัน ฯลฯ)
published: true
date: 2026-05-17T12:00:00.000Z
tags: recipe, cuisine, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ประเภทอาหาร (Cuisine Type)

> **At a Glance**
> **เจ้าของ:** Chef / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_recipe_cuisines` &nbsp;·&nbsp; **รูปทรง:** list แบน ผูกกับ enum `region` 6 ค่า &nbsp;·&nbsp; **ใช้โดย:** ส่วนหัวของ [[recipe]], filter ของ library, menu engineering &nbsp;·&nbsp; **มี:** `popular_dishes` + `key_ingredients` ที่ดูแลคัดสรร

## 1. คืออะไรและใครใช้

ประเภทอาหารคือ **แคตตาล็อกแบน** ที่ label สูตรแต่ละตัวด้วยต้นกำเนิดตามภูมิภาค / วัฒนธรรม (`Thai`, `Italian`, `Japanese`, `French` ฯลฯ) ขับเคลื่อน filter ของ menu engineering — outlet ที่มีธีมไทยดึงเฉพาะ `Thai` และรายการฟิวชันที่เลือกจาก library กลาง

แตกต่างจาก [[recipe/category]] ซึ่งเป็น *ตามฟังก์ชัน* และ *เชิงลำดับชั้น* ประเภทอาหารเป็น *ภูมิศาสตร์* และ *แบน* แต่ละแถวผูกกับ **region** ระดับสูง (`ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`) สำหรับ rollup ระดับภูมิภาค **ดูแลโดย Chef** (หรือ **Product Admin**) ภายใต้ Operation Plan → Cuisine

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม cuisine ใหม่ | Operation Plan → Cuisine → **+ New** | จำเป็นต้องมี Name + region (dropdown 6 ค่า) |
| ดูแล popular dishes / key ingredients | edit dialog → tag editor | string อิสระ ไม่มีการ validate FK ไปยัง product/recipe |
| เปลี่ยนชื่อ cuisine | edit dialog → `name` | สูตรเก็บ ID ดังนั้นการแสดงผลรีเฟรชอัตโนมัติ |
| ปลดประจำการ cuisine | edit dialog → `is_active = false` | สูตรในประวัติยังแสดง ซ่อนจาก picker |
| ย้าย cuisine ไปยัง region อื่น | edit dialog → `region` | region อยู่บนแถว cuisine เท่านั้น — ไม่ cascade |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Name already exists" | `@@unique([name, deleted_at])` ละเมิด | เลือกชื่ออื่น (หรือ restore แถวที่ลบ) |
| "Region is required" | `region` เว้นว่าง — ไม่มี fallback NULL | เลือกหนึ่งใน 6 ค่า enum |
| "Region value not allowed" | พยายามตั้ง region ที่ไม่รู้จัก | region ใหม่ต้องมีการ migrate schema |
| "Cannot delete: recipes still reference this cuisine" | `tb_recipe.cuisine_id` FK `onDelete: Restrict` | reassign สูตรแล้ว soft-delete |
| Recipe library แสดง cuisine ว่างบนสูตรเก่า | cuisine ถูก soft-delete แต่แถวยังถูกเก็บ | การอ่านยังทำงาน — restore หรือ reassign ตามต้องการ |

## 4. Edge Cases

- **ไม่มี region `OTHER`** ทุก cuisine ต้อง map กับหนึ่งใน 6 ค่า enum — การเพิ่ม region ใหม่ต้องมีการ migrate Prisma
- **Soft-delete รักษาประวัติ** สูตรที่อ้างอิง cuisine ที่ปลดประจำการยังแสดงถูกต้อง เฉพาะ picker ใหม่ที่ซ่อน
- **`popular_dishes` / `key_ingredients`** เป็น array อิสระ — ไม่ join กับ `tb_product` หรือ `tb_recipe` ดังนั้นการเปลี่ยนชื่อไม่กระจาย
- **region ของสูตร** derive ผ่าน FK ของ cuisine ไม่มีลิงก์ตรงสูตร-ภูมิภาค

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_recipe_cuisines`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `Thai`, `Northern Italian`) |
| `description`, `note` | `String? @db.VarChar` | Yes | ข้อความอิสระ / โน้ตภายใน |
| `is_active` | `Boolean?` | Yes | flag active, default `true` |
| `region` | `enum_cuisine_region` | No | `ASIA` / `EUROPE` / `AMERICAS` / `AFRICA` / `MIDDLE_EAST` / `OCEANIA` |
| `popular_dishes` | `Json @db.JsonB` | No | เมนูคลาสสิกที่คัดสรร (default `[]`) |
| `key_ingredients` | `Json @db.JsonB` | No | วัตถุดิบเอกลักษณ์ที่คัดสรร (default `[]`) |
| `info`, `dimension` | `Json?` | Yes | metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `recipe_cuisines_name_u` index บน `region` และ `name` reverse relation ไปยัง `tb_recipe.cuisine_id` พร้อม `onDelete: Restrict`

### 5.2 Enum `enum_cuisine_region`

ค่า: `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`

## 6. กติกาทางธุรกิจ

- **ความไม่ซ้ำ** `name` ไม่ซ้ำในแถวที่ไม่ถูกลบ (บังคับใช้ที่ DB)
- **region จำเป็น** ไม่มี `NULL` / `OTHER` fallback region ใหม่ต้องมีการ migrate schema
- **Deletion guards** `onDelete: Restrict` บน `tb_recipe.cuisine_id` บล็อก hard-delete ของ cuisine ที่ถูกอ้างอิง ใช้ soft-delete + inactive
- **การ validate** `name` และ `region` จำเป็น `popular_dishes` / `key_ingredients` เป็น array string อิสระ (ไม่มีการ validate FK)
- **การกระจายการเปลี่ยนชื่อ** สูตรเก็บ ID ดังนั้นการเปลี่ยนชื่อรีเฟรชอัตโนมัติบนการแสดงผล

## 7. Cross-References

- [[recipe]] — สูตรทุกตัวมี `cuisine_id` (จำเป็น) แสดงบนส่วนหัวและขับเคลื่อน filter ของ library
- [[recipe/category]] — taxonomy พี่น้องบนแกน (ตามฟังก์ชัน) ที่ต่างกัน
- [[recipe/01-data-model]] — ฟิลด์ส่วนหัวของสูตรรวมถึง FK ของ cuisine
- [[recipe/03-user-flow-chef]], [[recipe/03-user-flow-procurement-fb-ops]] — Chef หยิบ F&B Ops ใช้ cuisine + rollup ภูมิภาค

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_cuisines` (lines ~5192-5224), enum `enum_cuisine_region` (lines ~5157-5164)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/cuisine/`
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
