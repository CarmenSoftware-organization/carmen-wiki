---
title: อุปกรณ์ (Equipment)
description: ข้อมูลหลักของอุปกรณ์ครัว — อ้างอิงจากขั้นตอนการเตรียมในสูตรอาหารที่ต้องใช้เครื่องมือเฉพาะ (อ่าง sous-vide, deep fryer, smoker ฯลฯ)
published: true
date: 2026-05-17T12:00:00.000Z
tags: recipe, equipment, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# อุปกรณ์ (Equipment)

> **At a Glance**
> **เจ้าของ:** Chef / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_recipe_equipment` &nbsp;·&nbsp; **Parent:** [[recipe/equipment-category]] ผ่าน `category_id` &nbsp;·&nbsp; **ใช้โดย:** ขั้นตอนการเตรียมของ [[recipe]], checklist การ fit-out, dashboard maintenance &nbsp;·&nbsp; **ติดตาม:** สเปก สถานี ปริมาณ การใช้งาน วันที่ maintenance

## 1. คืออะไรและใครใช้

อุปกรณ์คือ master ของเครื่องมือและอุปกรณ์ครัว — ตั้งแต่เครื่องมือมือ (ตะกร้อตี mandolin) ผ่านอุปกรณ์ขนาดใหญ่ (combi-oven, blast chiller, sous-vide) ไปจนถึงอุปกรณ์ mise-en-place แบบพกพา แต่ละแถวมี **การระบุ** (`code`, `name`, `brand`, `model`, `serial_no`), **สเปก** (capacity, power), **ข้อความการใช้งาน** (operation / safety / cleaning), **ตาราง maintenance + วันที่**, **การกำหนดสถานี** และ **ตัวนับปริมาณ** (`total_qty`, `available_qty`)

**ขั้นตอนการเตรียม** ของสูตรอ้างอิงอุปกรณ์เพื่อให้ planner ของ workflow ครัวยืนยันว่า outlet มีเครื่องมือที่ต้องการก่อนนำสูตรไปใช้ การติดตามการใช้งาน (`usage_count`, `average_usage_time`) ป้อนตาราง maintenance **ดูแลโดย Chef** (หรือ **Product Admin**) ภายใต้ Operation Plan → Equipment

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มอุปกรณ์ชิ้นใหม่ | Operation Plan → Equipment → **+ New** | เลือก `category_id` กรอก code + name (จำเป็น) |
| อัปเดตวันที่ maintenance หลังบริการ | หน้ารายละเอียด → section Maintenance | `next_maintenance_date` ที่ผ่านแล้วแสดง badge "overdue" |
| มาร์คอุปกรณ์เป็นพกพา | หน้ารายละเอียด → `is_portable` | บ่งบอกว่าสามารถย้ายระหว่างสถานีได้ |
| ปรับจำนวนนับใน property | หน้ารายละเอียด → `total_qty` | `available_qty` ลดเมื่อ checkout (ยังไม่ได้ wire flow) |
| ปลดประจำการอุปกรณ์ | edit → `is_active = false` (soft-delete) | ยังอ้างอิงได้บนสูตรในประวัติ ซ่อนจาก picker |
| แนบคู่มือหรือรูป | หน้ารายละเอียด → `attachments` / `manuals_urls` | array JSON ของลิงก์ไฟล์ |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การแก้ไข |
|---|---|---|
| "Code + name already in use" | `@@unique([code, name, deleted_at])` ละเมิด | เลือกคู่ที่ไม่ซ้ำ |
| "Code is required" / "Name is required" | ฟิลด์จำเป็นว่าง | กรอกก่อน save |
| "available_qty cannot exceed total_qty" | กฎปริมาณบังคับใช้ที่ app | ปรับตัวนับให้สอดคล้อง |
| "Next maintenance must be ≥ last maintenance" | บังคับใช้ที่ app เมื่อตั้งวันที่ทั้งสอง | แก้วันที่ |
| dropdown หมวดหมู่ว่าง | ไม่มีแถว active ใน [[recipe/equipment-category]] | seed หมวดหมู่ก่อน |
| หมวดหมู่ถูกเปลี่ยนชื่อแต่ `category_name` เก่ายังแสดง | สำเนาแสดงผลที่ denormalise ไม่ได้รีเฟรช | save หมวดหมู่เพื่อ trigger fan-out (หรือ save อุปกรณ์ใหม่) |

## 4. Edge Cases

- **FK หมวดหมู่เป็น `onDelete: NoAction`** DB จะไม่ cascade หรือบล็อก — application layer ต้องปฏิเสธการลบหมวดหมู่ในขณะที่มีอุปกรณ์อ้างอิง (ดู [[recipe/equipment-category]])
- **`category_name` ถูก denormalise** สำหรับแสดงผล ถือ FK (`category_id`) เป็นแหล่งความจริง string เป็น cache
- **Flow checkout ยังไม่ได้ implement** — `available_qty` มีใน schema แต่ยังไม่มี UI wire วันนี้
- **อุปกรณ์บนขั้นตอนการเตรียมถูก denormalise** ลงบน payload `tb_recipe_preparation_step.equipment` ไม่ใช่ตาราง join (ดู [[recipe/01-data-model]])
- **badge maintenance overdue** เป็นภาพล้วน ๆ ไม่มีการบล็อกการใช้สูตรอัตโนมัติ

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
- **การ validate** `code`, `name` จำเป็น `available_qty <= total_qty` `next_maintenance_date >= last_maintenance_date` เมื่อตั้งทั้งสอง
- **ความหมายของปริมาณ** `total_qty` = จำนวนนับใน property `available_qty` สำรองไว้สำหรับ flow checkout
- **วงจรชีวิต** อุปกรณ์ inactive อ่านได้บนประวัติ ซ่อนจาก picker ขั้นตอนใหม่
- **`category_name`** รีเฟรชเมื่อเปลี่ยนชื่อหมวดหมู่ผ่าน fan-out ของ application — FK เป็นความจริง

## 7. Cross-References

- [[recipe/equipment-category]] — taxonomy parent ผ่าน `category_id`
- [[recipe]] — ขั้นตอนการเตรียมอ้างอิงอุปกรณ์ (denormalise ลงบนขั้นตอน)
- [[recipe/01-data-model]] — จุดเชื่อมต่อของอุปกรณ์บนขั้นตอน
- [[recipe/03-user-flow-chef]], [[recipe/03-user-flow-outlet-manager]] — Chef ติด tag ขั้นตอน Outlet Manager ตรวจสอบ fit-out

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_recipe_equipment` (lines ~5249-5312)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/operation-plan/equipment/`
- **Concept docs:** `../carmen/docs/recipe/setup-pages-spec.md`
