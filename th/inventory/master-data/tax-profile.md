---
title: Profile ภาษี (Tax Profile)
description: นิยามอัตราภาษีแบบมีชื่อที่ถูกอ้างอิงโดยผู้ขาย สินค้า และทุกบรรทัดเอกสารที่มีราคา
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, tax-profile, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Profile ภาษี (Tax Profile)

> **At a Glance**
> **เจ้าของ:** Product Admin (หรือ Sysadmin) &nbsp;·&nbsp; **ตาราง:** `tb_tax_profile` &nbsp;·&nbsp; **ใช้โดย:** vendor, product, PR / PO / GRN / pricelist / credit note &nbsp;·&nbsp; อัตรามีชื่อ (`VAT 7%`, `Zero-rated`) — โหมดภาษีของบรรทัดตัดสินวิธีนำไปใช้

![Profile ภาษี (Tax Profile) screen](/screenshots/master-data/tax-profile.png)

## 1. คืออะไร / ใครใช้

**Tax profile** คือนิยามแบบมีชื่อที่จับคู่ label (เช่น `VAT 7%`, `Zero-rated`, `Service Charge`) กับ `tax_rate` แบบ decimal Tax profile ถูกอ้างอิงจาก **ผู้ขาย, ข้อมูลหลักสินค้า และบรรทัดเอกสารที่มีราคาส่วนใหญ่** (PR, PO, GRN, pricelist, credit note) การแยกออกจากกันสำคัญ: อัตราเปลี่ยนแปลงตามเวลาและหลาย property ปฏิบัติงานภายใต้หลายระบบพร้อมกัน

การคำนวณภาษีระดับบรรทัดเอกสารอ่านสามอย่าง: **tax profile ที่เลือก**, **โหมดภาษี** ของเอกสาร (`none` / `included` / `add` ผ่าน `enum_tax_type`) และ **base amount ของบรรทัด** Tax profile ให้ *อัตรา*; โหมดตัดสินวิธีนำไปใช้ **บริหารจัดการโดย** Product Admin; **อ่านโดย** ทุก flow ของเอกสารที่มีราคา

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม profile | Configuration → Master Data → Tax Profile → **New** | บังคับ: `name`, `tax_rate` (decimal — `0.07` = 7%) |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker ของเอกสารใหม่; บรรทัดประวัติไม่เปลี่ยน |
| อัตราใหม่จาก regulator | **สร้าง profile ใหม่** | เช่น `VAT 9%` — อย่าแก้อัตราของ profile เก่า |
| ย้าย vendor/product | Bulk update reference fields | หลังสร้าง profile ใหม่ ย้ายการอ้างอิงไปข้างหน้า |
| ตรวจสอบอัตราที่ใช้บนบรรทัด | เปิดบรรทัดเอกสาร | อัตรา snapshot, ไม่ resolve จากตารางนี้ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่นหรือ reactivate แถวที่มี |
| "Rate must be >= 0" | `tax_rate` ติดลบ | ใส่ค่าเป็นศูนย์หรือ decimal บวก |
| "Cannot delete — referenced by documents/vendors/products" | มี FK references | ใช้ inactivate แทน |
| บรรทัดแสดงอัตราเก่าหลังแก้ profile | บรรทัด snapshot อัตราต้นทาง | คาดหวัง — snapshot คือ contract |

## 4. Edge Cases

- **Snapshot semantics** บรรทัดเอกสารทุกบรรทัด snapshot อัตรา ณ เวลาที่ posting; การแก้ `tax_rate` ที่นี่ ไม่ retro-edit บรรทัดที่ posted
- **วินัยการเปลี่ยนอัตรา** เมื่อ regulator เปลี่ยน headline rate ให้ **สร้าง profile ใหม่** (เช่น `VAT 9%`) แล้วย้าย vendor/product ไปข้างหน้า — อย่าแก้ profile เก่า
- **รูปแบบ decimal** — `0.07` แทน 7%; UI ต้อง validate และแปลง
- **การ inactivate** รักษาการ lookup ประวัติให้ resolve ได้
- **`enum_tax_type`** อยู่บนแต่ละบรรทัดเอกสาร ไม่ใช่บน profile — ดูหมายเหตุ schema ใน References

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_tax_profile`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `VAT 7%`) |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | อัตราในรูป decimal (default `0`) `0.07` สำหรับ 7% |
| `is_active` | `Boolean?` | Yes | Active flag |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `taxprofile_name_deletedat_u` Index บน `name` Reverse relation ที่กว้างไปยัง PR / PO / GRN / pricelist / vendor / product / credit-note / extra-cost-detail

## 6. กติกาทางธุรกิจ

- **Uniqueness** `name` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards** การอ้างอิงเอกสาร/master ใดก็ตามบล็อก hard-delete — ใช้ inactivate
- **Validation** `tax_rate >= 0`; storage เป็นรูป decimal (`0.07` = 7%)
- **Lifecycle** profile ที่ inactive ซ่อนจาก picker ใหม่; อ่านได้บนบรรทัดประวัติ
- **Snapshot semantics** บรรทัดเอกสาร snapshot อัตรา; การแก้ที่นี่ไม่ retro-edit เอกสารประวัติ
- **วินัยการเปลี่ยนอัตรา** สร้าง profile ใหม่เสมอเมื่อ headline rate เปลี่ยน

## 7. การอ้างอิงข้ามโมดูล

- [[master-data/vendor]] — ผู้ขายเก็บ default tax profile ที่ snapshot ณ เวลา link
- [[product]] — ข้อมูลหลักสินค้าอ้างอิง default tax profile ต่อรายการ
- [[purchase-request]] — บรรทัด detail ของ PR snapshot profile id + อัตรา
- [[purchase-order]] — บรรทัด detail ของ PO snapshot; default จาก vendor/product
- [[good-receive-note]] — บรรทัด detail ของ GRN snapshot จาก PO/ด้วยมือ
- [[vendor-pricelist]] — บรรทัด detail ของ pricelist บรรจุการอ้างอิง tax profile

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_tax_profile` (lines ~1395-1429), `enum_tax_type` (lines ~96-100) — หมายเหตุ `enum_tax_type` อยู่บนแต่ละบรรทัดเอกสาร ไม่ใช่บนเอนทิตีนี้
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/tax-profile/`
