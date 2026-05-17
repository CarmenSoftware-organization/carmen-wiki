---
title: เงื่อนไขการชำระเงิน (Credit Term)
description: เงื่อนไขการชำระเงินกับผู้ขาย (NET 30, COD ฯลฯ) ที่เลือกบนใบสั่งซื้อเพื่อขับเคลื่อนวันครบกำหนดและตาราง accounts payable
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, credit-term, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เงื่อนไขการชำระเงิน (Credit Term)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_credit_term` &nbsp;·&nbsp; **ใช้โดย:** ใบสั่งซื้อ (default ต่อผู้ขาย) &nbsp;·&nbsp; เงื่อนไขการชำระเงินแบบมีชื่อ — `name` + `value` (จำนวนวัน)

![เงื่อนไขการชำระเงิน (Credit Term) screen](/assets/screenshots/master-data/credit-term.png)

## 1. คืออะไร / ใครใช้

Credit term เข้ารหัสข้อตกลงการจ่ายเงินกับ supplier เป็นระเบียนแบบมีชื่อพร้อมจำนวนวัน: `NET 30` แปลว่าจ่ายภายใน 30 วันหลัง invoice date; `COD` (`value = 0`) แปลว่าจ่าย ณ การส่งของ PO อ้างอิง credit term เพื่อให้ **ตารางบัญชีเจ้าหนี้** มีเป้าหมาย due-date ที่เป็นรูปธรรม

เอนทิตีนี้น้อยที่สุดโดยตั้งใจ — `name`, `value` (วัน) และ flag `is_active` อะไรที่ซับซ้อนกว่านี้ (ส่วนลด early payment, ตารางแบบ tier) อยู่ใน application logic ไม่ใช่บนระเบียนนี้ **บริหารจัดการโดย** Product Admin; **อ่านโดย** developer และ tester ใน PO และเส้นทาง AP

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มเงื่อนไขใหม่ | Configuration → Master Data → Credit Term → **New** | บังคับ: `name`; `value` default `0` (COD) |
| ยกเลิกการใช้งานเงื่อนไข | Toggle `is_active` | ซ่อนจาก picker PO ใหม่; PO ประวัติยังเก็บเงื่อนไข |
| เปลี่ยนจำนวนวัน | แก้ `value` | PO ใหม่ default เป็นค่าใหม่; PO ประวัติเก็บ due date ไว้แล้ว |
| ตั้ง default ต่อผู้ขาย | รายละเอียดของ [[master-data/vendor]] | App-layer; ไม่ได้อยู่บนระเบียนนี้ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่น |
| "Value must be >= 0" | จำนวนวันติดลบ | ใช้ `0` สำหรับ COD หรือ integer บวก |
| "Name required" | `name` ว่าง | เพิ่มชื่อแสดงผล (เช่น `NET 30`) |
| "Cannot delete — referenced by open POs" | มี PO ที่เปิดอยู่ใช้เงื่อนไขนี้อย่างน้อยหนึ่ง | ใช้ inactivate แทน |

## 4. Edge Cases

- **การเปลี่ยนชื่อหรือ value** มีผลกับ PO **ใหม่** เท่านั้น; due date ถูก **คำนวณและเก็บ** บน PO ณ การสร้าง
- **เงื่อนไขที่ soft-deleted** ยัง resolve ได้บน PO ประวัติ
- **COD = `value = 0`** เป็นธรรมเนียมมาตรฐาน; due date เดียวกันวัน
- **Vendor default** อยู่ที่ app-layer — Carmen seed เงื่อนไขลงบน PO ณ การเลือกผู้ขาย แต่ user ยัง override ได้

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_credit_term`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `NET 30`, `COD`) |
| `value` | `Int? @db.Integer` | Yes | จำนวนวันหลัง invoice date จนถึง due (default `0`) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `is_active` | `Boolean?` | Yes | Active flag |
| `info`, `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `credit_term_name_u` Index บน `name` Reverse relation ไปยัง `tb_purchase_order`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `name` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards** PO ที่เปิดอยู่บล็อก hard-delete — ใช้ inactivate แทน
- **Validation** `value >= 0`; `name` บังคับ
- **Lifecycle** เงื่อนไข inactive ซ่อนจาก picker PO ใหม่; PO ประวัติยังเก็บเงื่อนไขที่กำหนดไว้
- **Snapshot semantics** PO เก็บ id ของ term; due date คำนวณ ณ การสร้าง PO และเก็บไว้ การเปลี่ยน rate/value ที่นี่ไม่ retro-edit PO ประวัติ

## 7. การอ้างอิงข้ามโมดูล

- [[purchase-order]] — PO header บรรจุ `credit_term_id`; due date = `po_date + value` วัน
- [[master-data/vendor]] — ผู้ขาย pre-assign default credit term ใน app logic; default ลงบน PO ใหม่

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_term` (lines ~4548-4572)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/credit-term/`
