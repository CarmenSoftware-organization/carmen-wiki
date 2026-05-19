---
title: หน่วยธุรกิจ (Business Unit)
description: หน่วยปฏิบัติการ / นิติบุคคล (property หรือ BU) ที่กำหนด scope ของทุกธุรกรรม — เป็นเจ้าของ calculation method, default currency และ module subscription
published: true
date: 2026-05-17T07:28:28.000Z
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
| ตั้ง default currency | BU detail → Identity tab | ต้องอ้างอิงแถว active ใน [[master-data/currency]] |
| สลับ costing method | BU detail → Costing tab | บล็อกกลางงวด; ต้อง snapshot สิ้นงวด + recost — ดู Edge Cases |
| เปิด / ปิด module | BU detail → Modules tab | เขียนไปยัง `tb_business_unit_tb_module`; ซ่อน UI แต่รักษาข้อมูล |
| Mark HQ | ตั้ง `is_hq = true` | หนึ่ง HQ ต่อ cluster (app invariant) |
| ยกเลิกการใช้งาน BU | Toggle `is_active` | บล็อก login ใหม่, รักษาข้อมูลทั้งหมด |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code already in use in cluster" | `code` ซ้ำใน `cluster_id` เดียวกัน | เลือก code อื่น |
| "Calculation method required" | Form ส่งโดยไม่มี `average` / `fifo` | เลือกหนึ่ง — ไม่มี default |
| "Cannot change calculation method mid-period" | พยายามสลับขณะมี posting เปิดอยู่ | ปิดงวด, snapshot, recost แล้วเปลี่ยน |
| "Default currency must be active" | `default_currency_id` ชี้ไปแถว inactive | Activate สกุลเงินก่อน |
| "Cannot delete BU — active users / open documents / non-zero balances" | Deletion guard | Wind down operation ก่อน แล้ว soft-delete |

## 4. Edge Cases

- **การสลับ calculation-method** การพลิก `average` ↔ `fifo` ทำลาย valuation ประวัติย้อนหลัง ระบบควรปฏิเสธกลางงวดและต้อง snapshot สิ้นงวด + recost ที่ audit อนุมัติแล้วก่อนเปิดใช้
- **`is_hq` invariant** หนึ่ง BU ต่อ cluster บรรจุ `is_hq = true` — บังคับใช้ระดับ app ไม่ใช่ DB
- **การปิด module รักษาข้อมูล** การลบ module ผ่าน `tb_business_unit_tb_module` ซ่อน UI; ข้อมูลธุรกรรมพื้นฐานไม่ถูกแตะ
- **การ inactivate สกุลเงิน** สกุลเงินที่เป็น BU `default_currency_id` ไม่สามารถ inactivate ได้
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
- **Deletion guards** ผู้ใช้ที่ active, เอกสารที่เปิดอยู่ หรือยอด non-zero ทั้งหมดบล็อกการลบ
- **Validation** `cluster_id`, `code`, `name`, `calculation_method` บังคับ
- **Lifecycle** `is_active = false` บล็อก login, รักษาข้อมูล
- **การเปลี่ยน calculation method** ต้องตามวินัย period-close + recost
- **`is_hq` invariant** หนึ่ง HQ ต่อ cluster

## 7. การอ้างอิงข้ามโมดูล

- [[costing]] — อ่าน `calculation_method` ต่อ BU
- [[inventory]] — ยอดคงเหลือและ valuation scope ต่อ BU
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — เอกสารธุรกรรมทุกใบ BU-scoped
- [[access-control]] — การ map user-to-BU ขับเคลื่อน header `x-app-id`
- [[reporting-audit]] — รายงาน filter / roll up ตาม BU

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (lines ~79-144), `tb_business_unit_tb_module` (lines ~146-164), `enum_calculation_method` (lines ~74-77)
- **Frontend:** `../carmen-platform/src/` (platform admin dashboard)
