---
title: ประเภทธุรกิจผู้ขาย (Vendor Business Type)
description: Flat lookup สำหรับจัดประเภทผู้ขายตามลักษณะธุรกิจ (ผู้ผลิต, ผู้จัดจำหน่าย, บริการ ฯลฯ) — อ้างอิงโดยระเบียนผู้ขายเพื่อรายงานและกรองข้อมูล
published: true
date: 2026-06-04T00:00:00.000Z
tags: master-data, vendor-business-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# ประเภทธุรกิจผู้ขาย (Vendor Business Type)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_vendor_business_type` &nbsp;·&nbsp; **ใช้โดย:** ระเบียนผู้ขาย (`tb_vendor.business_type` JSON array) &nbsp;·&nbsp; Flat lookup สำหรับจัดประเภทผู้จัดหาตามลักษณะธุรกิจ (ผู้ผลิต, ผู้จัดจำหน่าย, ผู้ให้บริการ ฯลฯ)

## 1. คืออะไร / ใครใช้

**ประเภทธุรกิจผู้ขาย** คือชั้น taxonomy บน vendor master แต่ละประเภทแทนหมวดธุรกิจที่ผู้ขายดำเนินงานอยู่ — ตัวอย่างเช่น ผู้ผลิต, ผู้จัดจำหน่าย, ผู้ค้าส่ง, หรือผู้ให้บริการ ผู้ขายหนึ่งรายสามารถมีได้หลายประเภท โดยเก็บเป็น JSON array ของ `{id, name}` บน `tb_vendor.business_type`

เอนทิตีนี้เป็น **flat lookup** — ไม่มีลำดับชั้น ไม่มี logic workflow การจัดประเภทช่วยขับเคลื่อนการรายงาน (แบ่งกลุ่มค่าใช้จ่ายตามหมวดผู้จัดหา) และการกรองข้อมูล (ค้นหาผู้ขายประเภท distributor ทั้งหมดสำหรับรอบ sourcing) **บริหารจัดการโดย** Product Admin; **อ่านโดย** ทุก flow การจัดซื้อและ pricelist ที่จัดกลุ่มหรือกรองตามหมวดผู้ขาย

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มประเภทธุรกิจใหม่ | Configuration → Master Data → Vendor Business Type → **New** | บังคับ: `name`; `description` (เลือก) |
| แก้ description | Edit dialog | การเปลี่ยนชื่อไม่ propagate อัตโนมัติไปยัง JSON snapshot บน `tb_vendor`; ต้องรัน maintenance refresh |
| ยกเลิกการใช้งาน | Toggle `is_active = false` | ซ่อนจาก picker ใหม่; ระเบียนผู้ขายที่มีอยู่ยังคงอ้างอิง FK ไว้ |
| ลบ | Soft-delete (ตั้ง `deleted_at`) | ปลอดภัยเฉพาะเมื่อไม่มีผู้ขายอ้างอิงประเภทนี้ |
| ตรวจสอบว่าผู้ขายรายใดใช้ประเภทนี้ | Query `tb_vendor.business_type` JSON array | ไม่มี FK column ตรง — เก็บเป็น JSON ฝังบนผู้ขาย |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่นหรือ restore แถวที่มี |
| "Name required" | `name` ว่าง | เพิ่มชื่อแสดงผล |
| "Cannot delete — referenced by vendors" | มีผู้ขายอย่างน้อยหนึ่งรายที่ฝังประเภทนี้ใน JSON `business_type` | Deactivate แทนการลบ; หรือทำความสะอาด reference ของผู้ขายก่อน |
| ประเภทแสดงชื่อเก่าบนผู้ขาย | JSON snapshot บนผู้ขายยังไม่ได้ refresh หลังการเปลี่ยนชื่อ | รัน maintenance job เพื่อ refresh `tb_vendor.business_type` JSON ทั่วทุกผู้ขาย |

## 4. Edge Cases

- **JSON snapshot vs. FK** `tb_vendor.business_type` เก็บ JSON array ของ `{id, name}` — สำเนาของชื่อ ณ เวลาที่บันทึกผู้ขาย การเปลี่ยนชื่อบน `tb_vendor_business_type` **ไม่** refresh snapshot ของผู้ขายโดยอัตโนมัติ; ต้องรัน maintenance job
- **หลายประเภทต่อผู้ขายหนึ่งราย** ผู้ขายรายเดียวสามารถอยู่ในหลายประเภทธุรกิจพร้อมกัน (เช่น ทั้ง distributor และ service provider)
- **`is_active` flag** ต่างจาก lookup ส่วนใหญ่ที่ใช้เฉพาะ soft-delete ตารางนี้มี `is_active`; ตั้ง `is_active = false` เพื่อซ่อนจาก picker โดยไม่ต้องลบระเบียน
- **Soft-deleted rows ยัง resolve ได้** ผู้ขายที่ฝัง type ที่ถูกลบแล้วยังเก็บ `id` ใน JSON ไว้; ถ้า lookup resolve ด้วย `id` ชื่อจะ resolve จากแถวที่ soft-deleted
- **การแปล** ชื่อประเภทอาจแสดงให้ผู้ขายเห็นในเอกสาร จนกว่าจะมีตาราง localisation การแปลอยู่ใน `info` JSON

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_vendor_business_type`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @unique @db.VarChar` | No | ชื่อแสดงผล (เช่น `Manufacturer`, `Distributor`, `Service`) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `is_active` | `Boolean?` | Yes | Active flag (default `true`) |
| `info`, `dimension` | `Json?` | Yes | Metadata มาตรฐาน |
| `doc_version` | `Decimal @db.Decimal` | No | Optimistic-lock version (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name])` (DB-level unique) `@@index([name], map: "vendor_business_type_name_u")` Reverse relation: `tb_vendor[]` (ผ่าน FK `business_type_id` บน `tb_vendor`)

### 5.2 วิธีที่ `tb_vendor` อ้างอิงเอนทิตีนี้

`tb_vendor` เก็บ **สอง** การอ้างอิง:

| Column | Type | วัตถุประสงค์ |
|---|---|---|
| `business_type_id` | `String? @db.Uuid` | FK ไปยัง `tb_vendor_business_type` (ประเภทหลักเดียว, `onDelete: NoAction`) |
| `business_type` | `Json? @db.JsonB` | JSON array แบบ denormalised `[{id, name}]` สำหรับแสดงผลทุกประเภทที่กำหนด |

FK column (`business_type_id`) กำหนดประเภทหลักหนึ่งประเภทที่มีอำนาจ; JSON column จับการเลือกหลายประเภทเพื่อการรายงาน

## 6. กติกาทางธุรกิจ

- **Uniqueness** `name` เป็น DB-unique (`@unique`) ทุกแถว รวมถึงที่ soft-deleted ไม่มีสองประเภทที่ใช้ชื่อเดียวกัน
- **Deletion guards** ประเภทที่ถูกอ้างอิงโดยผู้ขายรายใดก็ตามไม่ควร hard-delete Deactivate (`is_active = false`) หรือ soft-delete เมื่อประเภทนั้นไม่จำเป็นอีกต่อไป; ผู้ขายยังคง JSON snapshot ไว้
- **Validation** `name` บังคับและ unique
- **Lifecycle** `is_active = false` ซ่อนประเภทจาก picker ในขณะที่รักษา referential integrity Soft-delete คือขั้นตอนสุดท้ายในการปลดระวาง
- **Rename propagation** การเปลี่ยนชื่อประเภทไม่ auto-update JSON `business_type` บนผู้ขาย — รัน maintenance refresh หลังการเปลี่ยนชื่อ
- **การแปล** เก็บการแปลใน `info` JSON จนกว่าจะมีการ introduce ตาราง localisation

## 7. การอ้างอิงข้ามโมดูล

- [master-data/vendor](/th/inventory/master-data/vendor) — ระเบียนผู้ขายที่ฝัง JSON `business_type` และเก็บ FK `business_type_id`
- [vendor-pricelist](/th/inventory/vendor-pricelist) — รอบ sourcing ของ pricelist อาจกรองตามประเภทธุรกิจผู้ขาย
- [purchase-request](/th/inventory/purchase-request) — การเลือก preferred vendor ใน PR อาจแสดงประเภทธุรกิจเพื่อกรอง

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen/docs/prisma-schema/schema.prisma` — `tb_vendor_business_type` (lines ~2646-2667); ใช้โดย `tb_vendor` (FK `business_type_id` ที่ line ~1862, JSON `business_type` ที่ line ~1868)
- **Frontend:** `../carmen-inventory-frontend-react/` — Vendor Business Type list ใต้ Configuration → Master Data
