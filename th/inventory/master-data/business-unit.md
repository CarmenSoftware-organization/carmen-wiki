---
title: หน่วยธุรกิจ (Business Unit)
description: หน่วยปฏิบัติการ / นิติบุคคล (property หรือ BU) ที่กำหนด scope ของทุกธุรกรรม — เป็นเจ้าของ calculation method, default currency และ module subscription
published: true
date: 2026-07-29T05:09:51.000Z
tags: master-data, business-unit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# หน่วยธุรกิจ (Business Unit)

> **At a Glance**
> **เจ้าของ:** Sysadmin &nbsp;·&nbsp; **ตาราง:** `tb_business_unit` (platform) &nbsp;·&nbsp; **ใช้โดย:** เอกสารธุรกรรมทุกใบ &nbsp;·&nbsp; Scope บนสุด — เป็นเจ้าของวิธี costing, default currency และการเปิดใช้งาน module

![หน่วยธุรกิจ (Business Unit) screen](/screenshots/master-data/business-unit.png)

## 1. คืออะไร / ใครใช้

**Business Unit (BU)** คือ scope บนสุดที่เอกสาร, user role และรายงานทุกตัวผูกอยู่ — โดยทั่วไปคือหนึ่ง **property** (โรงแรม) ใน **cluster** (กลุ่ม) ที่สำคัญที่สุดคือ BU เป็นเจ้าของ **calculation method ของ costing** (`average` หรือ `fifo`) ที่ขับเคลื่อน valuation ของทุกการเคลื่อนไหวสต๊อก BU ยังเป็นเจ้าของ default currency, identity ของบริษัท/โรงแรม, format default (date, time, money, qty), metadata การ connection และการเปิดใช้งาน module

**บริหารจัดการโดย** Sysadmin ที่ platform admin console **อ่านโดย** ทุก backend service (ทุก query มี BU-scoped) และโดยเฉพาะ costing engine

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง BU | Platform admin → BU listing → **New** | บังคับ: `cluster_id`, `code`, `name`, `calculation_method` |
| ตั้ง default currency | BU detail → Identity tab | ต้องอ้างอิงแถว active ใน [master-data/currency](/th/inventory/master-data/currency) |
| สลับ costing method | BU detail → Costing tab | บล็อกกลางงวด; ต้อง snapshot สิ้นงวด + recost — ดู Edge Cases |
| เปิด / ปิด module | BU detail → Modules tab | เขียนไปยัง `tb_business_unit_tb_module`; ซ่อน UI แต่รักษาข้อมูล |
| Mark HQ | ตั้ง `is_hq = true` | หนึ่ง HQ ต่อ cluster (app invariant) |
| ยกเลิกการใช้งาน BU | Toggle `is_active` | บล็อก login ใหม่, รักษาข้อมูลทั้งหมด |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code already in use in cluster" | `code` ซ้ำใน `cluster_id` เดียวกัน | เลือก code อื่น |
| **ยังไม่ยืนยัน** — ฟอร์มแก้ไขไม่มีข้อจำกัดฝั่ง client | `CalculationSettingsSection.tsx` ของ `carmen-platform` render `calculation_method` เป็น `<select>` (`average`/`fifo`) ที่แก้ไขได้เสมอ ไม่มี disabled state, warning หรือการเช็คกลางงวดที่พบใน component; ยังไม่ได้ตรวจสอบว่า backend microservice command `business-units.update` บังคับ block หรือไม่ในรอบนี้ | เดิมหน้านี้ระบุว่า "cannot change calculation method mid-period" เป็น error ที่บังคับใช้จริง; ให้ถือว่า**ยังไม่ยืนยัน** ไม่ใช่ guard ที่รับประกันแน่นอน |
| "Default currency must be active" — **ยังไม่ยืนยัน** | ไม่พบ disabled state หรือ validation ที่ผูก `default_currency_id` กับ flag `is_active` ของสกุลเงินเป้าหมายในฟอร์มแก้ไขรอบนี้ | ให้ถือว่ายังไม่ยืนยัน |
| "Cannot delete BU — active users / open documents / non-zero balances" — **ยังไม่ยืนยัน** | `deleteBusinessUnit` ใน gateway เป็น proxy บาง ๆ ไปยัง microservice command `business-units.delete`; guard ถ้ามี ยังไม่ได้ตรวจสอบในรอบนี้ | ให้ถือว่ายังไม่ยืนยัน ไม่ใช่การบล็อกที่รับประกันแน่นอน |

## 4. Edge Cases

- **การสลับ calculation-method — guard ยังไม่ยืนยัน** การพลิก `average` ↔ `fifo` จะทำลาย valuation ประวัติย้อนหลังในทางหลักการ แต่ฟอร์มแก้ไขของ `carmen-platform` ไม่มี disabled state หรือ warning บนฟิลด์นี้เลย และยังไม่ได้ตรวจสอบว่า backend microservice บล็อกกลางงวดหรือไม่ในรอบนี้ ให้ถือว่า "ระบบปฏิเสธกลางงวด" เป็น design intent ไม่ใช่ guard ที่ยืนยันแล้ว
- **`is_hq` invariant** หนึ่ง BU ต่อ cluster บรรจุ `is_hq = true` — บังคับใช้ระดับ app ไม่ใช่ DB
- **การปิด module รักษาข้อมูล** การลบ module ผ่าน `tb_business_unit_tb_module` ซ่อน UI; ข้อมูลธุรกรรมพื้นฐานไม่ถูกแตะ
- **การ inactivate สกุลเงิน — ยังไม่ยืนยัน** ยังไม่ได้ตรวจสอบว่า platform บล็อกการ inactivate สกุลเงินที่เป็น `default_currency_id` ของ BU หรือไม่ในรอบนี้ (การเช็คที่เทียบเท่ากันฝั่ง Inventory ยืนยันแล้วว่า**ไม่มีอยู่**บน path การอัปเดต `tb_currency` เอง — ดู [master-data/currency](/th/inventory/master-data/currency))
- **Tenant DB connection** `db_connection` JSON ชี้ BU ไปยัง tenant schema; การตั้งค่าผิดทำให้ BU ทั้งหมด offline

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: platform schema (`packages/prisma-shared-schema-platform/prisma/schema.prisma`) BU อยู่ที่ระดับ platform เพราะ user และ cluster ครอบคลุมข้าม tenant

### 5.1 `tb_business_unit`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `cluster_id` | `String @db.Uuid` | No | FK ไปยัง `tb_cluster` |
| `code` | `String @db.VarChar(30)` | No | รหัส BU แบบสั้น |
| `name` | `String` | No | ชื่อแสดงผล |
| `alias_name` | `String? @db.VarChar(10)` | Yes | Alias สั้นที่ใช้ใน numbering |
| `description`, `info` | — | Yes | Free text / JSON metadata |
| `is_hq` | `Boolean?` | Yes | Mark HQ BU ใน cluster (default `true`) |
| `is_active` | `Boolean?` | Yes | Active flag |
| `db_connection`, `config` | `Json?` | Yes | Tenant DB connection / per-BU config blobs |
| `default_currency_id` | `String? @db.Uuid` | Yes | Default currency (tenant currency catalogue) |
| `calculation_method` | `enum_calculation_method` | No | `average` (default) หรือ `fifo` **แหล่งความจริงสำหรับ costing** |
| `max_license_users` | `Int?` | Yes | License cap |
| Company info: `branch_no`, `company_name`, `company_address`, `company_email`, `company_tel`, `company_zip_code`, `tax_no` | `String?` | Yes | Identity ทางกฎหมาย |
| Hotel info: `hotel_name`, `hotel_address`, `hotel_email`, `hotel_tel`, `hotel_zip_code` | `String?` | Yes | Identity ปฏิบัติการ |
| Format settings: `date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format`, `timezone`, `amount_format`, `quantity_format`, `perpage_format`, `recipe_format` | mixed | Yes | UI default `timezone` default `Asia/Bangkok` |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.2 `tb_business_unit_tb_module`

ตาราง link ไปยัง `tb_module`; index บน `(business_unit_id, module_id, deleted_at)` FK cascade `NoAction`

### 5.3 `enum_calculation_method`

```
enum enum_calculation_method {
  average
  fifo
}
```

หมายเหตุ: enum ชื่อเดียวกันใน tenant schema ใช้ `FIFO` / `AVG`; นิยาม platform เป็น authoritative สำหรับคอลัมน์นี้

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ภายใน cluster (app-enforced); `name` unique ตามธรรมเนียมด้วย
- **Deletion guards — ยังไม่ยืนยัน** `deleteBusinessUnit` ของ gateway เป็น proxy บาง ๆ ไปยัง microservice command `business-units.delete`; ยังไม่ได้ตรวจสอบว่าผู้ใช้ที่ active, เอกสารที่เปิดอยู่ หรือยอด non-zero บล็อกการลบจริงหรือไม่ในรอบนี้
- **Validation** `cluster_id`, `code`, `name`, `calculation_method` บังคับ
- **Lifecycle** `is_active = false` บล็อก login, รักษาข้อมูล
- **การเปลี่ยน calculation method** — **design intent, guard ยังไม่ยืนยัน** การพลิก `average` ↔ `fifo` ตามหลักการควรตามวินัย period-close + recost แต่ตามที่ระบุใน Section 4 (Edge Cases; และ Section 3 การตรวจสอบและข้อผิดพลาด) ฟอร์มแก้ไขของ `carmen-platform` ไม่มี disabled state หรือข้อจำกัดกลางงวดบนฟิลด์นี้เลย และยังไม่ได้ตรวจสอบว่า backend microservice บังคับใช้หรือไม่ในรอบนี้ — ให้ถือว่า "ต้องตามวินัย period-close + recost" เป็น design intent ไม่ใช่ guard ที่ยืนยันแล้ว
- **`is_hq` invariant** หนึ่ง HQ ต่อ cluster

## 7. การอ้างอิงข้ามโมดูล

- [costing](/th/inventory/costing) — อ่าน `calculation_method` ต่อ BU
- [inventory](/th/inventory/inventory) — ยอดคงเหลือและ valuation scope ต่อ BU
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [vendor-pricelist](/th/inventory/vendor-pricelist) — เอกสารธุรกรรมทุกใบ BU-scoped
- [access-control](/th/inventory/access-control) — การ map user-to-BU ขับเคลื่อน header `x-app-id`
- [reporting-audit](/th/inventory/reporting-audit) — รายงาน filter / roll up ตาม BU

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (lines ~117-202), `tb_business_unit_tb_module` (lines ~204-223), `enum_calculation_method` (lines ~112-115)
- **Frontend:** `../carmen-platform/src/pages/BusinessUnitEdit.tsx` + `businessUnitEdit/sections/CalculationSettingsSection.tsx` (platform admin dashboard)
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_business-units/platform_business-units.service.ts` (proxy บาง ๆ ไปยัง microservice `business-units` ที่ยังไม่ได้ตรวจสอบในรอบนี้)
