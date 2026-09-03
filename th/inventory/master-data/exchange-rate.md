---
title: อัตราแลกเปลี่ยน (Exchange Rate)
description: ประวัติอัตราแปลงสกุลเงินไปยังสกุลเงินฐานแบบมีวันที่ — เอกสารธุรกรรมทุกใบ snapshot อัตราที่มีผลในวันที่ของเอกสาร
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, exchange-rate, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# อัตราแลกเปลี่ยน (Exchange Rate)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_exchange_rate` &nbsp;·&nbsp; **ใช้โดย:** PR / PO / GRN / pricelist / costing &nbsp;·&nbsp; **Feed:** ใส่ด้วยมือ หรือ sync แบบ bulk จาก external FX API (ปัจจุบันเสีย — ดู Edge Cases) ไม่มี cron job

![อัตราแลกเปลี่ยน (Exchange Rate) screen](/screenshots/master-data/exchange-rate.png)

## 1. คืออะไร / ใครใช้

Exchange Rate เก็บ **ประวัติอัตราแบบมีวันที่** ของอัตราแปลงสกุลเงินไปยังสกุลเงินฐาน เอกสารที่มีราคาทุกใบ (PR / PO / GRN / pricelist) จะ **snapshot อัตรา** ที่มีผลในวันที่นั้น ๆ ตอน submit และ **freeze ไว้** ตลอดอายุของเอกสาร — การ re-approval จะไม่ดึงค่าใหม่

**บริหารจัดการโดย** Product Admin (โดยทั่วไปทุกเช้า ด้วยการใส่ด้วยมือ — ปุ่ม bulk-sync จาก external ยืนยันว่าเสียในเวอร์ชันปัจจุบัน ดู Edge Cases) **อ่านโดย** costing engine สำหรับ FX revaluation ของใบลดหนี้ (`COST_CALC_005`) และการปิดงวด

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ใส่หนึ่งอัตรา (สกุลเงินเดียว) | Configuration → Exchange Rate → **Add Manual** | เลือกสกุลเงิน เลือกวัน ใส่อัตรา; backend ปฏิเสธเฉพาะแถว `(currency, at_date)` ที่ซ้ำเป๊ะเท่านั้น |
| Sync สกุลเงินที่เปิดใช้งานทั้งหมดจาก external rate feed | Configuration → Exchange Rate → **Update** | ดึงอัตราสดจาก external FX API (`/api/exchange-rate?base=<code>`) เทียบกับ cache อัตราของแต่ละสกุลเงิน แล้ว bulk-submit ตัวที่เปลี่ยนโดย stamp วันนี้ผ่าน endpoint `createBulk` จริง — **แต่ดู Edge Cases: การดึงข้อมูลนี้ยืนยันว่าเสียในเวอร์ชันปัจจุบัน** |
| ตรวจสอบว่าเอกสารใช้อัตราเท่าใด | เปิด PR/PO/GRN ดูฟิลด์ FX บนบรรทัด | เอกสาร freeze อัตราตอน submit |
| เปลี่ยนอัตราบน PR/PO/GRN ที่เป็น draft | Header เอกสาร → picker สกุลเงิน | การเลือกสกุลเงินใหม่จะเติมฟิลด์ใหม่จาก `tb_currency.exchange_rate`; ฟิลด์นี้แก้ไขได้โดยตรงด้วย ไม่มี action "Refresh FX" แยกต่างหากอยู่ที่ไหนในโค้ดเบสเลย — PR, PO และ GRN ทำงานเหมือนกันทุกที่ |
| แก้อัตราผิดบนเอกสารที่ *posted* แล้ว | ไม่สามารถแก้ในที่ได้ | ออก manual journal voucher ตามนโยบาย finance |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Must be at least 0" | ใส่อัตราติดลบใน dialog Add Manual / Edit (Zod `min(0)` ฝั่ง client) | ใส่ศูนย์หรือค่าบวก |
| Duplicate rate for the same date | มีแถวสำหรับ `(currency, at_date)` อยู่แล้ว — `create()` ปฏิเสธด้วย "Exchange rate already exists"; `createBulk()` ข้ามแถวนั้นเงียบ ๆ แทน | แก้แถวที่มีอยู่; อย่าแทรกแถวที่สอง |
| เอกสารแสดง warning **"rate not in history"** | ไม่มี `tb_exchange_rate` row ที่หรือก่อนวันที่เอกสารสำหรับสกุลเงินนั้น | เพิ่ม backdated rate แล้วเปิดเอกสารใหม่ให้ resolution ทำงาน |
| **ยังไม่ยืนยัน** — backend ไม่มี validation อะไรนอกจาก "สกุลเงินมีอยู่จริง" | `ExchangeRateCreateSchema`/`ExchangeRateUpdateSchema` (`exchange-rate.dto.ts`) เช็คแค่ว่า `currency_id` resolve ไปยังแถวจริงได้ — ไม่มีการเช็คอัตราเป็นบวก ไม่มี future-date horizon ไม่มีการเช็คสกุลเงิน active และไม่มีการเช็คงวดปิด ที่ไหนใน `exchange-rate.service.ts` เลย | เดิมหน้านี้ระบุว่า "rate must be > 0", "date too far in future", "currency must be active" และ "period is closed" เป็น error ที่บังคับใช้จริงฝั่ง server — ไม่พบทั้งสี่ในรอบนี้; ให้ถือว่าเป็น**เฉพาะฝั่ง client หรือไม่มีเลย** ไม่ใช่การรับประกันจาก server จนกว่าจะตรวจสอบซ้ำ |

## 4. Edge Cases

- **การใส่ backdated** อนุญาตให้ทำได้แต่ **ไม่** เปลี่ยนเอกสาร ที่ snapshot ค่าอื่นไปแล้วย้อนหลัง การแก้เอกสาร posted ใช้ manual journal voucher
- **การ inactivate สกุลเงินไม่ลบประวัติอัตรา** — เอกสารย้อนหลังยังคง render ถูกต้อง
- **Precision** อัตราเก็บที่ `Decimal(15, 5)`; ยอดรวมบรรทัดเอกสารปัดเศษเป็น 2 ทศนิยม (เงิน) ตามกติกาการปัดเศษ
- **"Current" cache vs. history** `tb_currency.exchange_rate` เป็น *cache* ของ `tb_exchange_rate` ล่าสุด เอกสารใหม่ resolve ผ่านประวัติที่มีวันที่ก่อน; ถ้าไม่มีแถวที่ตรงวันเท่านั้น cache จึงทำหน้าที่เป็น fallback (พร้อม warning บนเอกสาร)
- **ฟีเจอร์ที่ยืนยันว่าค้างครึ่งทาง — ปุ่ม "Update" แบบ bulk-sync** hook `useExternalExchangeRates` ของ `ExchangeRateComponent` เรียก `GET /api/exchange-rate?base=<รหัสสกุลเงิน>` ซึ่งเป็น route แบบ Next.js API จาก stack เดิม ค้นหาทั่ว repo ใน NestJS gateway ปัจจุบัน (`carmen-turborepo-backend-v2/apps/backend-gateway`) ไม่พบ route ที่ตรงกันเลย — มีแค่ controller CRUD `api/config/:bu_code/exchange-rates` เท่านั้น comment ในโค้ดของ hook เองยืนยันเรื่องนี้ตรง ๆ: `// TODO(phase-config): /api/exchange-rate was a Next route — move to backend or client-side fetch when the config module migrates` และอีก comment บอกว่าบน static hosting SPA fallback จะคืน `index.html` พร้อม status `200` ทำให้ endpoint นี้ตกไปเป็น error "Exchange rate endpoint is not available" แทนที่จะ crash เส้นทาง **Add Manual** แบบทีละแถวไม่ได้รับผลกระทบ — มัน POST ตรงไปยัง endpoint จริง `POST /exchange-rates`
- **ไม่มี feed แบบ cron** ค้นหาทั่ว repo ใน `../micro-cronjobs` หา `exchange`/`fx`/`currency` ไม่พบเลย ไม่มี scheduled job ที่ refresh อัตรา วิธีเดียวที่แถวอัตราจะถูกสร้างคือปุ่ม external-sync (ที่เสียอยู่ตอนนี้) และ dialog แบบ manual ทีละแถว

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
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`); DTO ของการอัปเดตบังคับต้องส่งมา และปฏิเสธถ้าไม่ตรงกัน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([at_date, currency_id, deleted_at])` map `exchangerate_at_date_currency_u` — หนึ่งอัตราต่อ `(currency, date)` Index บน `(at_date, currency_id)` FK บน `currency_id` `onDelete: NoAction` เพื่อให้ประวัติอัตรารอดจากการ soft-delete สกุลเงิน

## 6. กติกาทางธุรกิจ

- **Uniqueness** หนึ่งแถว non-deleted ต่อ `(at_date, currency_id)`, บังคับระดับ DB `create()` ปฏิเสธแถวที่ซ้ำเป๊ะด้วย "Exchange rate already exists" แทนที่จะอัปเดตให้; `createBulk()` ข้ามแถวซ้ำเงียบ ๆ แทนที่จะ error การแก้แถวที่มีอยู่ต้องเปิดแถวนั้นตรง ๆ (เรียก `update()` แยกต่างหากพร้อม `doc_version`)
- **Validation (ยืนยัน)** `ExchangeRateCreateSchema`/`ExchangeRateUpdateSchema` (`exchange-rate.dto.ts`) บังคับแค่ให้ `currency_id` resolve ไปยังแถว `tb_currency` ที่มีอยู่ (`validateCurrencyIdExists` — ไม่กรอง `is_active` ดังนั้นแม้สกุลเงินที่ inactive หรือ soft-deleted ก็ผ่านได้) ไม่มีการเช็คฝั่ง server ว่า `exchange_rate` เป็นบวก ไม่มี future-date horizon และไม่มีการเช็คงวดปิดที่ไหนใน `exchange-rate.service.ts` เลย dialog Add Manual / Edit ฝั่ง frontend บังคับ `exchange_rate >= 0` เอง (Zod `min(0)`, ดังนั้น `0` เองก็ผ่าน) และ `currency_id`/`at_date` ต้องไม่ว่างบนฟอร์ม manual — เป็นแค่ฝั่ง client เท่านั้น
- **Optimistic lock** การอัปเดตต้องส่ง `doc_version` มา; ค่าที่ล้าสมัยจะถูกปฏิเสธ การสร้างใหม่ไม่ต้องใช้
- **Precision** เก็บที่ `Decimal(15, 5)`; ยอดรวมบรรทัดปัดเศษเป็น money precision (2 dp) ตามกติกาการปัดเศษ
- **Rate resolution** Engine เลือกแถวที่ `at_date <= document_date` ที่ใหญ่ที่สุดสำหรับสกุลเงินเอกสาร ถ้าไม่มีแถว ให้ fall back ไปที่ `tb_currency.exchange_rate` และ flag เอกสาร
- **Snapshot semantics** เมื่อเอกสารบันทึกอัตราที่ resolve ได้แล้ว มันจะ frozen การ re-approving / re-routing / re-posting จะไม่ดึงค่าใหม่โดยอัตโนมัติ; ฟิลด์ยังแก้ไขได้โดยผู้ใช้ และการเลือกสกุลเงินใหม่บน header เอกสารจะเติมค่าใหม่จาก cache `tb_currency.exchange_rate` ปัจจุบัน — ไม่มี action "Refresh FX" แยกเฉพาะอยู่ที่ไหนในโค้ดเบสเลย
- **Currency inactivation** ไม่ลบประวัติอัตรา การ soft-delete แถวอัตราจะลบออกจาก resolution ใหม่เท่านั้น
- **Backdated entry** อนุญาต; ไม่อัปเดตเอกสารที่ posted ย้อนหลัง

## 7. การอ้างอิงข้ามโมดูล

- [master-data/currency](/th/inventory/master-data/currency) — parent แต่ละแถวอัตรา scoped ต่อ `tb_currency` หนึ่งราย
- [master-data/business-unit](/th/inventory/master-data/business-unit) — `default_currency_id` เป็นด้าน "to" โดยปริยายของทุกอัตรา
- [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [purchase-request](/th/inventory/purchase-request) — เอกสารที่ snapshot อัตรา
- [vendor-pricelist](/th/inventory/vendor-pricelist) — การเปรียบเทียบ normalise เป็น BU default ผ่านอัตราที่มีวันที่
- [costing](/th/inventory/costing) — `COST_CALC_005` (FX revaluation ของใบลดหนี้) และการปิดงวดอ่านจากที่นี่

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_exchange_rate` (lines ~760-785)
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/exchange-rate/` — hook `useExternalExchangeRates` ใน `use-exchange-rate.ts` คือจุดที่ external-sync ยืนยันว่าเสีย
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_exchange-rates/` (CRUD รวม `createBulk`) และ `apps/micro-business/src/master/exchange-rate/exchange-rate.service.ts`
- **Cron job:** ไม่พบ `../micro-cronjobs/` ค้นหา `exchange`/`fx`/`currency` ไม่พบเลย ไม่มี FX feed แบบ scheduled
