---
title: อุปกรณ์ (Equipment)
description: ข้อมูลหลักของอุปกรณ์ครัว — อ้างอิงจากขั้นตอนการเตรียมในสูตรอาหารที่ต้องใช้เครื่องมือเฉพาะ (อ่าง sous-vide, deep fryer, smoker ฯลฯ)
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, equipment, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# อุปกรณ์ (Equipment)

> **At a Glance**
> **เจ้าของ:** Chef / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_recipe_equipment` &nbsp;·&nbsp; **Parent:** [recipe/equipment-category](/th/inventory/recipe/equipment-category) ผ่าน `category_id` &nbsp;·&nbsp; **ใช้โดย:** ขั้นตอนการเตรียมของ [recipe](/th/inventory/recipe), checklist การ fit-out, dashboard maintenance &nbsp;·&nbsp; **ติดตาม:** สเปก สถานี ปริมาณ การใช้งาน วันที่ maintenance

![อุปกรณ์ (Equipment) screen](/screenshots/recipe/equipment.png)

![อุปกรณ์ (Equipment) detail screen](/screenshots/recipe/equipment-detail.png)

## 1. คืออะไรและใครใช้

อุปกรณ์คือ master ของเครื่องมือและอุปกรณ์ครัว — ตั้งแต่เครื่องมือมือ (ตะกร้อตี mandolin) ผ่านอุปกรณ์ขนาดใหญ่ (combi-oven, blast chiller, sous-vide) ไปจนถึงอุปกรณ์ mise-en-place แบบพกพา แต่ละแถวมี **การระบุ** (`code`, `name`, `brand`, `model`, `serial_no`), **สเปก** (capacity, power), **ข้อความการใช้งาน** (operation / safety / cleaning), **ตาราง maintenance + วันที่**, **การกำหนดสถานี** และ **ตัวนับปริมาณ** (`total_qty`, `available_qty`)

**ขั้นตอนการเตรียม** ของสูตรอ้างอิงอุปกรณ์เพื่อให้ planner ของ workflow ครัวยืนยันว่า outlet มีเครื่องมือที่ต้องการก่อนนำสูตรไปใช้ การติดตามการใช้งาน (`usage_count`, `average_usage_time`) ป้อนตาราง maintenance **ดูแลโดย Chef** (หรือ **Product Admin**) ภายใต้ Operation Plan → Equipment

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มอุปกรณ์ชิ้นใหม่ | Operation Plan → Equipment → **+ New** | เลือก `category_id` กรอก code + name (จำเป็น) |
| อัปเดตวันที่ maintenance หลังบริการ | หน้ารายละเอียด → section Maintenance | ฟิลด์วันที่ธรรมดา ไม่พบ indicator "overdue" ใน source |
| มาร์คอุปกรณ์เป็นพกพา | หน้ารายละเอียด → `is_portable` | บ่งบอกว่าสามารถย้ายระหว่างสถานีได้ |
| ปรับจำนวนนับใน property | หน้ารายละเอียด → `total_qty` / `available_qty` | ทั้งสองเป็นฟิลด์ integer ธรรมดาที่ผู้ใช้แก้ตรง ๆ — ไม่มี flow checkout ที่ลด `available_qty` อัตโนมัติ |
| ปลดประจำการอุปกรณ์ | edit → `is_active = false` (soft-delete) | ยังอ้างอิงได้บนสูตรในประวัติ ซ่อนจาก picker |
| แนบคู่มือหรือรูป | หน้ารายละเอียด → `attachments` / `manuals_urls` | array JSON ของลิงก์ไฟล์ |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Code + name already in use" | `@@unique([code, name, deleted_at])` ละเมิด | เลือกคู่ที่ไม่ซ้ำ |
| "Code is required" / "Name is required" | ฟิลด์จำเป็นว่าง | กรอกก่อน save |
| dropdown หมวดหมู่ว่าง | ไม่มีแถว active ใน [recipe/equipment-category](/th/inventory/recipe/equipment-category) | seed หมวดหมู่ก่อน |
| หมวดหมู่ถูกเปลี่ยนชื่อแต่ `category_name` เก่ายังแสดง | `category_name` รีเฟรชเฉพาะเมื่อแถว **อุปกรณ์** เองถูก save (`recipe-equipment.service.ts` ค้นชื่อหมวดหมู่ ณ ตอนนั้น) — ไม่มี fan-out จากฝั่งหมวดหมู่ | save แถวอุปกรณ์ที่ได้รับผลกระทบใหม่ทีละแถวหลังเปลี่ยนชื่อหมวดหมู่ |

**ไม่ได้บังคับใช้ในปัจจุบัน (ตรวจ `recipe-equipment.service.ts` และ zod DTO ของ gateway แล้ว — ไม่มีกฎแบบนี้ในทั้งสองที่):** `available_qty <= total_qty` และ `next_maintenance_date >= last_maintenance_date` ไม่ถูก validate ที่ไหนเลย ทั้งสองฟิลด์รับ integer / วันที่ใด ๆ อย่างอิสระต่อกัน

## 4. Edge Cases

- **FK หมวดหมู่เป็น `onDelete: NoAction`** DB จะไม่ cascade หรือบล็อก — application layer ต้องปฏิเสธการลบหมวดหมู่ในขณะที่มีอุปกรณ์อ้างอิง (ดู [recipe/equipment-category](/th/inventory/recipe/equipment-category))
- **`category_name` ถูก denormalise** สำหรับแสดงผล และรีเฟรชเฉพาะตอน save ของแถวอุปกรณ์เองเท่านั้น ถือ FK (`category_id`) เป็นแหล่งความจริง string เป็น cache ที่ไม่มี fan-out การเปลี่ยนชื่อจากฝั่งหมวดหมู่
- **Flow checkout ยังไม่ได้ implement** — `available_qty` / `total_qty` มีใน schema แต่ยังไม่มี UI ที่ใช้งานหรือ validation ข้ามฟิลด์ wire วันนี้ ไม่มีอะไรป้องกัน `available_qty` เกิน `total_qty`
- **อุปกรณ์บนขั้นตอนการเตรียมถูก denormalise** ลงบน payload `tb_recipe_preparation_step.equipment` ไม่ใช่ตาราง join (ดู [recipe/01-data-model](/th/inventory/recipe/01-data-model)) หมายเหตุ: หน้าจอ create/edit สูตรปัจจุบัน (`recipe-form.tsx`) ไม่มี UI ที่อ่านหรือเขียนขั้นตอนการเตรียมเลย ดังนั้นการเชื่อมอุปกรณ์บนขั้นตอนนี้ยังเข้าถึงไม่ได้จากฟอร์มสูตรในปัจจุบัน
- **ไม่พบ badge "overdue"** `last_maintenance_date` / `next_maintenance_date` เป็นฟิลด์วันที่ธรรมดาบนฟอร์มอุปกรณ์ ไม่พบ logic เปรียบเทียบ overdue ใน component ของ frontend หรือ service ของ backend — callout นี้ควรถือเป็นความคาดหวัง (aspirational) จนกว่าจะพบ indicator สถานะ maintenance ใน source

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_recipe_equipment`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | code สั้น (เช่น `OVEN-COMBI-01`) |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description` | `String? @db.VarChar` | Yes | ข้อความอิสระ |
| `category_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_recipe_equipment_category` |
| `category_name` | `String? @db.VarChar` | Yes | สำเนาแสดงผลที่ denormalise |
| `brand`, `model`, `serial_no` | `String? @db.VarChar` | Yes | การระบุทางกายภาพ |
| `capacity`, `power_rating` | `String? @db.VarChar` | Yes | สเปกอิสระ |
| `station` | `String? @db.VarChar` | Yes | การกำหนดสถานีครัว |
| `operation_instructions`, `safety_notes`, `cleaning_instructions` | `String? @db.VarChar` | Yes | อ้างอิงการใช้งาน |
| `maintenance_schedule` | `String? @db.VarChar` | Yes | ข้อความรอบ cadence |
| `last_maintenance_date`, `next_maintenance_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่ maintenance |
| `is_active`, `is_portable` | `Boolean?` | Yes | flag วงจรชีวิต |
| `available_qty`, `total_qty`, `usage_count` | `Int?` | Yes | ตัวนับ |
| `average_usage_time` | `Decimal? @db.Decimal(20, 5)` | Yes | นาทีเฉลี่ยต่อการใช้ |
| `attachments`, `manuals_urls` | `Json? @db.JsonB` | Yes | ลิงก์ไฟล์ |
| `note`, `info`, `dimension` | — | Yes | metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, name, deleted_at])` map `recipe_equipment_code_name_u` index บน `(code, name)` และ `name` FK `category_id → tb_recipe_equipment_category.id` `onDelete: NoAction, onUpdate: NoAction`

## 6. กติกาทางธุรกิจ

- **ความไม่ซ้ำ** `(code, name)` ไม่ซ้ำในแถวที่ไม่ถูกลบ
- **FK หมวดหมู่** `NoAction` ทั้งสองทาง — application ต้อง guard การลบหมวดหมู่ในขณะที่มี ref ของอุปกรณ์
- **การ validate** `code`, `name` จำเป็น ไม่พบการตรวจข้ามฟิลด์ระหว่าง `available_qty` / `total_qty` หรือระหว่างวันที่ maintenance ทั้งสองใน `recipe-equipment.service.ts` หรือ zod DTO ของ gateway — ทั้งสองคู่เป็นฟิลด์ integer/วันที่อิสระที่ไม่ถูก validate
- **ความหมายของปริมาณ** `total_qty` และ `available_qty` เป็นตัวนับที่กรอกมือทั้งคู่ ไม่มี flow checkout อ่านหรือลดตัวใดตัวหนึ่ง
- **วงจรชีวิต** อุปกรณ์ inactive อ่านได้บนประวัติ ซ่อนจาก picker ขั้นตอนใหม่ (แม้ว่าฟอร์มสูตรปัจจุบันจะไม่มี UI เพิ่มขั้นตอนเลยก็ตาม — ดู [recipe/01-data-model](/th/inventory/recipe/01-data-model))
- **`category_name`** รีเฟรชเฉพาะเมื่อแถวอุปกรณ์เองถูก save และ `category_id` ถูก resolve ใหม่ — ไม่มี fan-out ที่ trigger จากฝั่งหมวดหมู่

## 7. Cross-References

- [recipe/equipment-category](/th/inventory/recipe/equipment-category) — taxonomy parent ผ่าน `category_id`
- [recipe](/th/inventory/recipe) — ขั้นตอนการเตรียมอ้างอิงอุปกรณ์ (denormalise ลงบนขั้นตอน)
- [recipe/01-data-model](/th/inventory/recipe/01-data-model) — จุดเชื่อมต่อของอุปกรณ์บนขั้นตอน
- [recipe/03-user-flow-chef](/th/inventory/recipe/03-user-flow-chef), [recipe/03-user-flow-outlet-manager](/th/inventory/recipe/03-user-flow-outlet-manager) — Chef ติด tag ขั้นตอน Outlet Manager ตรวจสอบ fit-out

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment` (lines ~5249-5312)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/operation-plan/equipment/`
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
