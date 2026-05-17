---
title: ผู้ขาย (Vendor)
description: ผู้ขายและที่อยู่ ผู้ติดต่อ และ taxonomy ของประเภทธุรกิจ — counterparty ของทุกเอกสารจัดซื้อ
published: true
date: 2026-05-17T07:00:36.000Z
tags: master-data, vendor, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ขาย (Vendor)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_vendor`, `tb_vendor_address`, `tb_vendor_contact`, `tb_vendor_business_type` &nbsp;·&nbsp; **ใช้โดย:** PR, PO, GRN, pricelist, RFQ &nbsp;·&nbsp; ระเบียนผู้ขาย — default tax profile, credit term และ currency ลงบนเอกสารจัดซื้อ

![ผู้ขาย (Vendor) screen](/assets/screenshots/master-data/vendor.png)

## 1. คืออะไร / ใครใช้

**ผู้ขาย** คือ counterparty ภายนอกที่ property ซื้อจาก ระเบียนผู้ขายคือจุดเชื่อมระหว่างการจัดซื้อ (PR → PO → GRN), workflow pricelist (RFQ → pricelist → comparison) และบัญชี (tax profile, credit terms, payment) สี่ตารางประกอบเป็นเอนทิตี: **core** `tb_vendor` (identity + tax linkage), **หลายที่อยู่** ใน `tb_vendor_address`, **หลายผู้ติดต่อ** ใน `tb_vendor_contact` และ **taxonomy** ของประเภทธุรกิจใน `tb_vendor_business_type`

ระเบียนผู้ขาย snapshot **tax profile** ที่ระดับผู้ขายเพื่อให้เอกสารได้ default ที่สมเหตุสมผลซึ่งบรรทัดยังคง override ได้ **บริหารจัดการโดย** Product Admin; **อ่านโดย** ทุก flow จัดซื้อและ pricelist

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มผู้ขาย | Master Data → Vendor → **New** | บังคับ: `code`, `name`; เลือก `tax_profile_id` และประเภทธุรกิจ |
| เพิ่มที่อยู่ | Vendor detail → Addresses tab | มากที่สุดหนึ่งของแต่ละ `address_type` ต่อผู้ขาย |
| เพิ่มผู้ติดต่อ | Vendor detail → Contacts tab | ผู้ติดต่อหนึ่งคนต่อผู้ขายตั้งเป็น `is_primary = true` ได้ |
| บริหารจัดการประเภทธุรกิจ | Master Data → Vendor Business Type | หน้ารายการแยก; การอ้างอิงเก็บเป็น JSON `[{id, name}]` บนผู้ขาย |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker ใหม่; เอกสารย้อนหลังไม่เปลี่ยน |
| เปลี่ยน tax profile | Edit dialog | Snapshot `tax_rate` ใหม่; ไม่ retro-edit เอกสารย้อนหลัง |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code/name already in use" | `(code, name)` ซ้ำบนแถว non-deleted | เลือก identifier อื่น |
| "Address type already exists for this vendor" | พยายามเพิ่มที่อยู่ที่สองของ `address_type` เดียวกัน | แก้ที่อยู่ที่มีอยู่แทน |
| "Cannot delete — referenced by documents" | FK references จาก PR/PO/GRN/pricelist | ใช้ inactivate แทน |
| Warning "Vendor has no active contact" | ผู้ติดต่อทั้งหมด inactive หรือ deleted | เพิ่มหรือ reactivate อย่างน้อยหนึ่งผู้ติดต่อ |
| "Cannot have two primary contacts" | สองแถว `is_primary = true` | Toggle off primary เก่าก่อน |

## 4. Edge Cases

- **การเปลี่ยน tax-profile** ไม่ retro-edit เอกสารที่มีอยู่; snapshot บนแต่ละบรรทัดยังคงตามที่ posted
- **การเปลี่ยนชื่อ business-type** — `tb_vendor.business_type` JSON เก็บ array `{id, name}`; ผู้ขายยังคงเก็บชื่อเก่าจนกว่า maintenance job จะ refresh
- **Primary contact invariant** บังคับใช้ระดับ app ไม่ใช่ DB
- **Address types** — `contact_address`, `mailing_address`, `register_address`; มากที่สุดหนึ่งของแต่ละ type ต่อผู้ขาย
- **Address/contact soft-delete อิสระ** แต่ผู้ขายแต่ละรายควรเหลือผู้ติดต่อ active อย่างน้อยหนึ่งคน

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_vendor`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | รหัสผู้ขายแบบสั้น |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `business_type` | `Json? @db.JsonB` | Yes | Array ของ `{id, name}` refs ไปยัง `tb_vendor_business_type` (default `[]`) |
| `tax_profile_id` | `String? @db.Uuid` | Yes | Default tax profile สำหรับเอกสาร |
| `tax_profile_name` | `String? @db.VarChar` | Yes | สำเนาแสดงผลแบบ denormalised |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | อัตรา snapshot ณ เวลา link (default `0`) |
| `is_active` | `Boolean?` | Yes | Active flag |
| `info`, `dimension` | `Json?` | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, name, deleted_at])` map `vendor_code_name_u` Index บน `code`, `name`, `(code, name)` FK ไปยัง `tb_tax_profile` `onDelete: NoAction`

### 5.2 `tb_vendor_address`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `vendor_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_vendor` |
| `address_type` | `enum_vendor_address_type?` | Yes | `contact_address`, `mailing_address` หรือ `register_address` |
| `address_line1` | `String? @db.VarChar` | Yes | ถนน / บ้านเลขที่ / ซอย |
| `address_line2` | `String? @db.VarChar` | Yes | อาคาร / ชั้น |
| `sub_district` | `String? @db.VarChar` | Yes | ตำบล / แขวง |
| `district` | `String? @db.VarChar` | Yes | อำเภอ / เขต |
| `city` | `String? @db.VarChar` | Yes | สำหรับนอก TH |
| `province` | `String? @db.VarChar` | Yes | จังหวัด / รัฐ |
| `postal_code` | `String? @db.VarChar` | Yes | ZIP / postcode |
| `country` | `String? @db.VarChar` | Yes | ประเทศ |
| `is_active` | `Boolean?` | Yes | Active flag |
| `description`, `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([vendor_id, address_type, deleted_at])` — มากที่สุดหนึ่งของแต่ละ address type ต่อผู้ขาย Index บน `(vendor_id, address_type)` และ `vendor_id`

`enum_vendor_address_type`: `contact_address`, `mailing_address`, `register_address`

### 5.3 `tb_vendor_contact`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `vendor_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_vendor` |
| `name` | `String @db.VarChar` | No | ชื่อผู้ติดต่อ |
| `email` | `String? @db.VarChar` | Yes | Email |
| `phone` | `String? @db.VarChar` | Yes | Phone |
| `is_primary` | `Boolean?` | Yes | ผู้ติดต่อหลัก (default `false`) |
| `is_active` | `Boolean?` | Yes | Active flag |
| `description`, `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([vendor_id, name, deleted_at])` Index บน `(vendor_id, name)` และ `vendor_id`

### 5.4 `tb_vendor_business_type`

Flat lookup — `id`, `name`, `description`, `note`, `is_active`, metadata มาตรฐาน, audit columns App-enforce unique `name` ในแถว non-deleted

## 6. กติกาทางธุรกิจ

- **Uniqueness** `(code, name)` unique ในผู้ขาย non-deleted มากที่สุดหนึ่งของแต่ละ `address_type` ต่อผู้ขาย `name` ของ contact unique ภายในผู้ขาย
- **Deletion guards** การอ้างอิงจาก PR/PO/GRN/pricelist ที่เปิดอยู่บล็อก hard-delete — ใช้ inactivate
- **Validation** `code` และ `name` บังคับ `tax_rate` snapshot `tb_tax_profile` ณ เวลา link
- **Lifecycle** `is_active = false` ซ่อนจาก picker ใหม่; เอกสารที่มีอยู่ยังทำงานได้ ผู้ขายที่ active โดยไม่มี contact active ควร warn ใน UI
- **Primary contact invariant** มากที่สุดหนึ่ง `is_primary = true` ต่อผู้ขาย (app invariant)
- **การ propagate เปลี่ยน tax-profile** ไม่ retro-edit เอกสาร; snapshot ยังคงตามที่ posted
- **การเปลี่ยนชื่อ business-type** ต้องมี maintenance job มา refresh JSON snapshot บนผู้ขาย

## 7. การอ้างอิงข้ามโมดูล

- [[purchase-request]] — PR detail อาจแนะนำผู้ขายที่ต้องการ
- [[purchase-order]] — PO header bind ผู้ขายหนึ่งราย; FX, tax, credit terms default จากที่นี่
- [[good-receive-note]] — GRN inherit ผู้ขายจาก PO
- [[vendor-pricelist]] — pricelist และรอบ RFQ scope ต่อผู้ขาย
- [[master-data/tax-profile]] — default tax profile ของผู้ขาย
- [[master-data/credit-term]] — default credit term ของผู้ขายไหลเข้า PO header

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_vendor` (lines ~3249-3296), `tb_vendor_address` (lines ~3332-3365), `tb_vendor_contact` (lines ~3367-3396), `tb_vendor_business_type` (lines ~4853-…), `enum_vendor_address_type` (lines ~259-263)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/vendor-management/vendor/`
