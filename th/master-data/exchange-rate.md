---
title: อัตราแลกเปลี่ยน (Exchange Rate)
description: ประวัติอัตราแปลงสกุลเงินไปยังสกุลเงินฐานแบบมีวันที่ — เอกสารธุรกรรมทุกใบ snapshot อัตราที่มีผลในวันที่ของเอกสาร
published: true
date: 2026-05-17T12:00:00.000Z
tags: master-data, exchange-rate, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# อัตราแลกเปลี่ยน (Exchange Rate)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_exchange_rate` &nbsp;·&nbsp; **ใช้โดย:** PR / PO / GRN / pricelist / costing &nbsp;·&nbsp; **Feed:** รายวัน (ด้วยมือหรือ cron)

## 1. คืออะไร / ใครใช้

Exchange Rate เก็บ **ประวัติอัตราแบบมีวันที่** ของอัตราแปลงสกุลเงินไปยังสกุลเงินฐาน เอกสารที่มีราคาทุกใบ (PR / PO / GRN / pricelist) จะ **snapshot อัตรา** ที่มีผลในวันที่นั้น ๆ ตอน submit และ **freeze ไว้** ตลอดอายุของเอกสาร — การ re-approval จะไม่ดึงค่าใหม่

**บริหารจัดการโดย** Product Admin (โดยทั่วไปทุกเช้า) **อ่านโดย** costing engine สำหรับ FX revaluation ของใบลดหนี้ (`COST_CALC_005`) และการปิดงวด

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ใส่อัตราวันนี้สำหรับสกุลเงินที่เปิดใช้งานทั้งหมด | Configuration → Exchange Rate → **Bulk daily** | Idempotent บน `(currency, date)` — รันซ้ำได้ |
| ใส่หนึ่งอัตรา (สกุลเงินเดียว) | Configuration → Exchange Rate → **Manual single-row** | เลือกสกุลเงิน เลือกวัน ใส่อัตรา |
| ตรวจสอบว่าเอกสารใช้อัตราเท่าใด | เปิด PO/GRN ดูฟิลด์ FX บนบรรทัด | เอกสาร freeze อัตราตอน submit |
| Refresh FX บน PO ที่เป็น draft | บรรทัด PO → action **Refresh FX** | PR และ GRN ไม่มี action นี้ |
| แก้อัตราผิดบนเอกสารที่ *posted* แล้ว | ไม่สามารถแก้ในที่ได้ | ออก manual journal voucher ตามนโยบาย finance |
| เปิดใช้ feed อัตโนมัติรายวัน | ตั้งค่า `micro-cronjobs` FX job | Idempotent — รันซ้ำได้; อัปเดต cache "ปัจจุบัน" ด้วย |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Exchange rate must be > 0" | อัตราเป็นศูนย์หรือค่าลบ | ใส่ค่าบวก |
| "Effective date too far in future" | `at_date` > วันนี้ + 1 วัน (horizon ที่ตั้งค่าได้) | ใช้วันที่ของวันนี้สำหรับการใส่รายวัน |
| "Currency must be active" | `tb_currency.is_active = false` สำหรับรหัสที่เลือก | activate ก่อนที่ [[master-data/currency]] |
| Duplicate rate for the same date | มีแถวสำหรับ `(currency, at_date)` อยู่แล้ว | แก้แถวที่มีอยู่; อย่าแทรกแถวที่สอง |
| "Period is closed" | `at_date` อยู่ใน [[system-config/period]] ที่ปิดแล้ว | ไม่สามารถ back-fill เข้างวดที่ปิดได้; ออก JV |
| เอกสารแสดง warning **"rate not in history"** | ไม่มี `tb_exchange_rate` row ที่หรือก่อนวันที่เอกสารสำหรับสกุลเงินนั้น | เพิ่ม backdated rate แล้วเปิดเอกสารใหม่ให้ resolution ทำงาน |

## 4. Edge Cases

- **การใส่ backdated** อนุญาตให้ทำได้แต่ **ไม่** เปลี่ยนเอกสาร ที่ snapshot ค่าอื่นไปแล้วย้อนหลัง การแก้เอกสาร posted ใช้ manual journal voucher
- **การ inactivate สกุลเงินไม่ลบประวัติอัตรา** — เอกสารย้อนหลังยังคง render ถูกต้อง
- **Precision** อัตราเก็บที่ `Decimal(15, 5)`; ยอดรวมบรรทัดเอกสารปัดเศษเป็น 2 ทศนิยม (เงิน) ตามกติกาการปัดเศษ
- **"Current" cache vs. history** `tb_currency.exchange_rate` เป็น *cache* ของ `tb_exchange_rate` ล่าสุด เอกสารใหม่ resolve ผ่านประวัติที่มีวันที่ก่อน; ถ้าไม่มีแถวที่ตรงวันเท่านั้น cache จึงทำหน้าที่เป็น fallback (พร้อม warning บนเอกสาร)

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_exchange_rate`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `at_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่มีผล (default `now()`) มีผล *ตั้งแต่* วันนี้จนกว่าจะถูกแทนที่ |
| `currency_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_currency` |
| `currency_code` | `String? @db.VarChar(3)` | Yes | สำเนาแสดงผลแบบ denormalised (`USD`, `THB`) |
| `currency_name` | `String? @db.VarChar` | Yes | สำเนาแสดงผลแบบ denormalised |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | อัตราเทียบกับ BU default currency (default `1`) |
| `note` | `String? @db.VarChar` | Yes | Free text (เช่น "Daily fix from BoT") |
| `info`, `dimension` | `Json?` | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([at_date, currency_id, deleted_at])` map `exchangerate_at_date_currency_u` — หนึ่งอัตราต่อ `(currency, date)` Index บน `(at_date, currency_id)` FK บน `currency_id` `onDelete: NoAction` เพื่อให้ประวัติอัตรารอดจากการ soft-delete สกุลเงิน

## 6. กติกาทางธุรกิจ

- **Uniqueness** หนึ่งแถว non-deleted ต่อ `(at_date, currency_id)` การใส่วันเดียวกันซ้ำ = อัปเดตแถวเดิม
- **Validation** `exchange_rate > 0`; `at_date <= วันนี้ + 1 วัน` (horizon ตั้งค่าได้); `currency_id` ต้องอ้างอิงสกุลเงินที่ active
- **Precision** เก็บที่ `Decimal(15, 5)`; ยอดรวมบรรทัดปัดเศษเป็น money precision (2 dp) ตามกติกาการปัดเศษ
- **Rate resolution** Engine เลือกแถวที่ `at_date <= document_date` ที่ใหญ่ที่สุดสำหรับสกุลเงินเอกสาร ถ้าไม่มีแถว ให้ fall back ไปที่ `tb_currency.exchange_rate` และ flag เอกสาร
- **Snapshot semantics** เมื่อเอกสารบันทึกอัตราที่ resolve ได้แล้ว มันจะ frozen การ re-approving / re-routing / re-posting จะไม่ดึงค่าใหม่ — มีเพียง "Refresh FX" ที่ชัดเจนเท่านั้น
- **Currency inactivation** ไม่ลบประวัติอัตรา การ soft-delete แถวอัตราจะลบออกจาก resolution ใหม่เท่านั้น
- **Backdated entry** อนุญาต; ไม่อัปเดตเอกสารที่ posted ย้อนหลัง
- **Period close** แถวอัตราในงวดที่ปิดแล้วถูก lock จากการแก้; การแทรกใหม่ที่ `at_date` อยู่ในงวดที่ปิดถูกปฏิเสธ

## 7. การอ้างอิงข้ามโมดูล

- [[master-data/currency]] — parent แต่ละแถวอัตรา scoped ต่อ `tb_currency` หนึ่งราย
- [[master-data/business-unit]] — `default_currency_id` เป็นด้าน "to" โดยปริยายของทุกอัตรา
- [[purchase-order]], [[good-receive-note]], [[purchase-request]] — เอกสารที่ snapshot อัตรา
- [[vendor-pricelist]] — การเปรียบเทียบ normalise เป็น BU default ผ่านอัตราที่มีวันที่
- [[costing]] — `COST_CALC_005` (FX revaluation ของใบลดหนี้) และการปิดงวดอ่านจากที่นี่

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_exchange_rate` (lines ~744-768)
- **Frontend:** `../carmen-inventory-frontend/app/(root)/config/exchange-rate/`
- **Cron job:** `../micro-cronjobs/` — daily FX feed
