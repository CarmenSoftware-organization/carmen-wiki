---
title: สกุลเงิน (Currency)
description: แคตตาล็อกสกุลเงินต่อ tenant, รายการอ้างอิง ISO และประวัติอัตราแลกเปลี่ยนแบบมีวันที่ — ขับเคลื่อนการแปลง FX ทั้งหมดบน PO, GRN, pricelist และ costing
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# สกุลเงิน (Currency)

> **At a Glance**
> **เจ้าของ:** Sysadmin (ISO seed) / Product Admin (tenant catalogue) &nbsp;·&nbsp; **ตาราง:** `tb_currency_iso`, `tb_currency`, `tb_exchange_rate` &nbsp;·&nbsp; **ใช้โดย:** ทุกเอกสารที่มีราคา + costing engine &nbsp;·&nbsp; สกุลเงินที่ tenant เปิดใช้งาน + cache อัตรา "ปัจจุบัน"

![สกุลเงิน (Currency) screen](/assets/screenshots/master-data/currency.png)

## 1. คืออะไร / ใครใช้

ข้อมูลหลักของ Currency ครอบคลุม **สามตารางใน schema สองชุด** ได้แก่ **platform ISO reference** (`tb_currency_iso`), **tenant enabled-currencies catalogue** (`tb_currency`) พร้อม cache อัตรา "ปัจจุบัน" และ **ประวัติอัตราที่มีวันที่ระดับ tenant** (`tb_exchange_rate`) เมื่อรวมกันแล้วทำให้เอกสารที่มีราคาทุกใบสามารถถูกแสดงเป็นสกุลเงินใดก็ได้ที่ tenant เปิดใช้งาน และทำให้ costing engine สามารถเลือกอัตราที่ถูกต้องสำหรับวันที่ของเอกสารได้

แต่ละ tenant เลือก subset ของสกุลเงิน ISO ที่จะเปิดใช้งาน `default_currency_id` ของ BU (ดู [[master-data/business-unit]]) ชี้ไปยังหนึ่งในแถวที่เปิดใช้งานนี้ **บริหารจัดการโดย** Sysadmin (ISO seed) และ Product Admin (tenant catalogue); **อ่านโดย** developer ในเส้นทาง FX / costing และ tester ในการทดสอบเอกสารที่มี FX

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปิดใช้งานสกุลเงินสำหรับ tenant | Configuration → Master Data → Currency → **New** | เลือก `iso_code` จาก `tb_currency_iso`; ตั้ง `is_active = true` |
| ทับศัพท์สัญลักษณ์หรือชื่อ | Edit dialog | สำเนา tenant ใน `tb_currency.symbol` / `name` ทับ ISO row |
| ตั้ง default currency ของ BU | รายละเอียดของ [[master-data/business-unit]] | ต้องอ้างอิงแถว `tb_currency` ที่ active |
| บริหารจัดการอัตรา | ดู [[master-data/exchange-rate]] | ประวัติแบบมีวันที่อยู่ที่นั่น ไม่ใช่บนเอนทิตีนี้ |
| ยกเลิกการใช้งานสกุลเงิน | Toggle `is_active` | ถูกบล็อกถ้าเป็น `default_currency_id` ของ BU ใดก็ตาม |
| Seed รหัส ISO ใหม่ | Platform DB migration | tenant ไม่สามารถเขียน `tb_currency_iso` ได้ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "ISO code not found" | `tb_currency.code` ไม่ตรงกับ `tb_currency_iso.iso_code` ใดเลย | ให้ Sysadmin seed ISO row ก่อน |
| "Exchange rate must be > 0" | ตั้งอัตรา cache เป็นศูนย์ / ค่าลบ | ใส่ค่าบวกใหม่ |
| "Cannot inactivate — set as BU default" | สกุลเงินเป็น `default_currency_id` ของ BU อย่างน้อยหนึ่งราย | เปลี่ยน BU default ก่อน |
| "Cannot delete — referenced by documents/pricelists" | Hard-delete ถูกบล็อกโดย FK | ใช้ inactivate แทน |
| เอกสารแสดง warning "rate not in history" | ไม่มี `tb_exchange_rate` row ที่ / ก่อนวันที่ของเอกสาร | เพิ่ม backdated rate ใน [[master-data/exchange-rate]] |

## 4. Edge Cases

- **"Current" cache vs. history** `tb_currency.exchange_rate` เป็น *cache* ของ `tb_exchange_rate` ล่าสุด เอกสารใหม่ resolve ผ่านประวัติที่มีวันที่ก่อน; cache เป็น fallback (พร้อม warning)
- **การ inactivate ไม่ลบประวัติ** — เอกสารย้อนหลังยังคง render ตามอัตรา snapshot
- **BU default invariant** — สกุลเงินที่เป็น `default_currency_id` ของ BU ใดก็ตามไม่สามารถ inactivate ได้
- **Override ระดับ tenant** — `tb_currency.name` / `symbol` ทับสำเนา ISO สำหรับการแสดงผล
- **Decimal places** `tb_currency.decimal_places` ควบคุมการ render เท่านั้น — storage เป็น `Decimal(15, 5)` สำหรับอัตรา และเงินปัดเศษเป็น 2 dp

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มาแบบผสม: tenant + platform

### 5.1 `tb_currency_iso` (platform)

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `iso_code` | `String @db.VarChar` | No | รหัส ISO 4217 (`USD`, `THB`, `EUR`) |
| `name` | `String @db.VarChar(255)` | No | ชื่อเต็ม (default `Unknown`) |
| `symbol` | `String @db.VarChar(10)` | No | สัญลักษณ์ (default `Unknown`) |

**Constraints:** `@@unique([iso_code])` map `currency_iso_iso_code_u` ใช้เป็นข้อมูลอ้างอิงเท่านั้น — ไม่มี audit columns

### 5.2 `tb_currency` (tenant)

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar(3)` | No | รหัส ISO ที่ mirror มาจาก `tb_currency_iso` |
| `name` | `String @db.VarChar(100)` | No | ชื่อแสดงผลที่ tenant ทับศัพท์ได้ |
| `symbol` | `String? @db.VarChar(5)` | Yes | สัญลักษณ์ทับศัพท์ |
| `description` | `String?` | Yes | Free text (default `""`) |
| `decimal_places` | `Int?` | Yes | Default `2` |
| `is_active` | `Boolean?` | Yes | Active flag |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Cache อัตราปัจจุบันเทียบ BU default (default `1`) |
| `exchange_rate_at` | `DateTime? @db.Timestamptz(6)` | Yes | Cache timestamp |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** primary key บน `id`; uniqueness บน `code` บังคับใช้ที่ application layer มี reverse relations ไปยัง GRN, JV, PO, PR, pricelist, credit note และประวัติ exchange rate

### 5.3 `tb_exchange_rate` (tenant)

ดู [[master-data/exchange-rate]] สำหรับ schema เต็มและกฎการ resolution `@@unique([at_date, currency_id, deleted_at])`; FK ไปยัง `tb_currency` `onDelete: NoAction`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `tb_currency.code` unique ในแถว active; `tb_currency_iso.iso_code` DB-unique หนึ่ง `tb_exchange_rate` ต่อ `(at_date, currency_id)`
- **Deletion guards** การอ้างอิงจากเอกสารหรือ pricelist บล็อก hard-delete — ใช้ inactivate แทน
- **Validation** `exchange_rate > 0`; `code` ต้องตรงกับ `tb_currency_iso` row
- **Lifecycle** สกุลเงิน inactive ซ่อนจาก picker ของเอกสารใหม่; เอกสารย้อนหลัง render จาก snapshot
- **Rate resolution** Engine เลือก `at_date <= document_date` ที่ใหญ่ที่สุดสำหรับ `currency_id`; fall back ไปที่ cache `tb_currency.exchange_rate` และ flag เอกสาร
- **BU default invariant** ไม่สามารถ inactivate สกุลเงินที่เป็น `default_currency_id` ของ BU ใดก็ตาม

## 7. การอ้างอิงข้ามโมดูล

- [[master-data/exchange-rate]] — ประวัติอัตราที่มีวันที่; กฎการ resolution
- [[master-data/business-unit]] — `default_currency_id` ชี้มาที่นี่
- [[purchase-order]], [[good-receive-note]], [[purchase-request]] — เอกสารบรรจุ currency + snapshot rate
- [[vendor-pricelist]] — การเปรียบเทียบ normalise เป็น BU default ผ่านอัตราที่มีวันที่
- [[costing]] — costing resolve อัตรา ณ วันรับของเป็น BU currency

## 8. แหล่งอ้างอิง

- **Prisma (tenant):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_currency` (lines ~545-621), `tb_exchange_rate` (lines ~744-768)
- **Prisma (platform):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_currency_iso` (lines ~217-224)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/currency/`
