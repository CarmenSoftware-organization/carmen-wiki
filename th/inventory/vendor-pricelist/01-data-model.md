---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Data Model
description: เอนทิตี, ฟิลด์, ความสัมพันธ์ และ enum สำหรับโมดูล vendor-pricelist
published: true
date: 2026-05-19T23:55:00.000Z
tags: vendor-pricelist, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Data Model

> **At a Glance**
> **ตาราง:** Tier 1 — `tb_pricelist_template` / `_detail` &nbsp;·&nbsp; Tier 2 — `tb_request_for_pricing` / `_detail` (vendor invitation + URL token) &nbsp;·&nbsp; Tier 3 — `tb_pricelist` / `_detail` (vendor submission); บวกตาราง `_comment` ต่อระดับ
> **กลุ่มผู้ใช้:** Developer / Auditor (อ้างอิง dev)
> **FK สำคัญ:** request-for-pricing `→ tb_pricelist_template`; invitation `→ tb_vendor` + แบบเลือกได้ `→ tb_pricelist`; pricelist `→ tb_vendor` / `tb_currency`; pricelist-detail `→ tb_product` / `tb_unit` / `tb_tax_profile`; back-relation จาก `tb_purchase_request_detail.pricelist_detail_id` (แหล่งราคา PR)
> **รูปแบบ audit:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; ความ unique รวม `deleted_at`; pricelist-detail unique บน `(pricelist_id, product_id, unit_id, moq_qty)` รองรับการตั้งราคาแบบ multi-MOQ-tier

> **แหล่งความจริง:** Backend Prisma schema อ่านนี่ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
>
> Platform schema ไม่มีโมเดล vendor-pricelist; เอนทิตีทั้งหมดอยู่ใน tenant schema ไฟล์ `generated/client/schema.prisma` เป็นสำเนา auto-generated และไม่ใช่ authoritative

## 1. ภาพรวม

โมดูล vendor-pricelist เป็นเจ้าของเอนทิตีใน tenant-schema สิบตัวที่จัดเป็นสาม tier **Tier 1 — Templates** (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`) กำหนดสิ่งที่ฝ่ายจัดซื้อต้องการให้ผู้ขายเสนอราคา: รายการสินค้า, default unit-of-measure block, รูปแบบ MOQ tier, สกุลเงิน, validity window, schedule การ reminder และคำสั่งที่ผู้ขายต้องเห็น **Tier 2 — Request-for-Pricing** (`tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`) เป็น object "campaign" ที่ตั้งชื่อตามแบบ legacy — ผูก template หนึ่งกับ vendor cohort ที่มีวันที่เริ่ม / สิ้นสุด, ข้อความ custom, การอ้างอิง email template และแถว invitation ต่อผู้ขายที่แต่ละแถว carry `pricelist_url_token` ทาง cryptographic และ FK ไปยัง pricelist ในที่สุดของผู้ขาย **Tier 3 — Pricelist** (`tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) คือ artefact ที่ผู้ขาย submit: header ที่มีการอ้างอิงผู้ขาย, หมายเลข pricelist, สถานะ, validity window, สกุลเงิน, วิธีการ submission และ url token — บวกแถว detail ที่ carry การอ้างอิงสินค้า, หน่วย, MOQ qty, price-without-tax, tax และ lead time

โมดูล pricelist อยู่ **ติดกับ [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order) และ [good-receive-note](/th/inventory/good-receive-note)** ใน chain procure-to-pay แถว PR detail สามารถอ้างอิง `tb_pricelist_detail.id` โดยตรงผ่าน `tb_purchase_request_detail.tb_pricelist_detail` (back-relation ฝั่ง pricelist detail); PO snapshot `price` ของมันจาก pricelist active ที่เวลา PR-to-PO conversion (สำเนา snapshot — ไม่มี FK สด) และ GRN รัน price-variance check ของมันกับ pricelist active เดียวกัน แถว pricelist อ้างอิง [product](/th/inventory/product), `tb_unit`, `tb_tax_profile`, `tb_currency` และ `tb_vendor`; แถว request-for-pricing detail อ้างอิง `tb_vendor` (ผู้ขายที่ถูกเชิญ) และ `tb_pricelist` (pricelist ที่ผู้ขาย submit ในที่สุด, แบบเลือกได้จนกว่าจะมีการ submission ครั้งแรก)

Header ในแต่ละ tier carry enum สถานะของมันเอง — `enum_pricelist_template_status` สำหรับ template (`draft`, `active`, `inactive`) และ `enum_pricelist_status` สำหรับ pricelist (`draft`, `active`, `inactive`, `expired`); request-for-pricing ไม่มี enum สถานะ dedicated และถูกจัดเป็น active ระหว่าง `start_date` และ `end_date` วิธีการ submission ของ pricelist จับใน enum แยก `pricelist_submission_method` (`online`, `email`, `portal`, `manual`) แนวคิด carmen/docs ของ "campaign status" (`draft`, `active`, `paused`, `completed`, `cancelled`) และ "invitation submission status" (`pending`, `in-progress`, `submitted`, `approved`, `expired`) เป็น derivation ระดับแอปจาก `start_date`, `end_date`, `tb_pricelist.status` และ `tb_pricelist.submitted_at` — ไม่มีคอลัมน์ Prisma หรือ enum สำหรับมัน

โมเดล Prisma slim กว่าเอกสาร design ของ carmen/docs อย่างมีนัยสำคัญ ซึ่งอธิบายชั้น analytics campaign/invitation เต็มรูปแบบ (อัตราการตอบสนอง, เวลาตอบสนองเฉลี่ย, คะแนนคุณภาพ, การติดตาม IP-address, จำนวน session, telemetry click-through, PII ที่เข้ารหัสตอน rest) ที่ **ยังไม่มีใน Prisma** Section 5 ทำแคตตาล็อกของ divergence ที่ Prisma และ carmen/docs ไม่ตรงกัน Prisma เป็น canonical สำหรับเอนทิตีและฟิลด์; carmen/docs เป็น canonical สำหรับ semantic ของ workflow และคำอธิบายกติกาที่ชั้นแอปบังคับใช้บน schema ที่ slim กว่า

## 2. เอนทิตี

### 2.1 tb_pricelist_template

นิยามที่ใช้ซ้ำได้ของ "สิ่งที่จะถามผู้ขาย" Carry รายการสินค้า (ผ่าน `tb_pricelist_template_detail`), default currency และ validity period, คำสั่งที่ผู้ขายต้องเห็น และ schedule การ reminder / escalation Template หนึ่งสามารถขับ request-for-pricing ได้หลายแถว

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, สร้างผ่าน `gen_random_uuid()` |
| `name` | `String @db.VarChar` | No | ชื่อ template ที่อ่านได้สำหรับมนุษย์; unique ในแถวที่ไม่ถูก soft-delete |
| `status` | `enum_pricelist_template_status` | No | สถานะ template; default `draft` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระสำหรับการอ้างอิงทีมจัดซื้อ |
| `note` | `String @db.VarChar` | Yes | โน้ตข้อความอิสระแนบกับ template |
| `vendor_instructions` | `String @db.Text` | Yes | คำสั่งที่ผู้ขายต้องเห็นที่ render บน portal และในเนื้อหา email |
| `currency_id` | `String @db.Uuid` | Yes | default currency สำหรับการ submission ของผู้ขาย; FK ไป `tb_currency` |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสกุลเงินตอนสร้าง template |
| `validity_period` | `Int` | Yes | default validity window ในวัน; pricelist `effective_from_date` + `validity_period` ⇒ `effective_to_date` |
| `send_reminders` | `Boolean` | Yes | reminder อัตโนมัติเปิดอยู่ไหม; default `true` |
| `reminder_days` | `Json @db.JsonB` | Yes | array ของ trigger days-before-deadline เช่น `[14, 7, 3, 1]`; default `[]` |
| `escalation_after_days` | `Int` | Yes | วันหลัง deadline ก่อน escalation; default `0` |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension สำหรับ template attribute เฉพาะ tenant; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension / classification; default `[]` |
| `doc_version` | `Int @db.Integer` | No | ตัวนับเวอร์ชัน optimistic-concurrency; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง; default `now()` |
| `created_by_id` | `String @db.Uuid` | Yes | id ของ user ผู้สร้างแถว |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด; default `now()` |
| `updated_by_id` | `String @db.Uuid` | Yes | id ของ user ผู้อัปเดตล่าสุด |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete; non-null หมายถึงถูกลบเชิง logical |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ของ user ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `currency_id → tb_currency.id` (`NoAction`) Back-relation ไป `tb_pricelist_template_detail`, `tb_pricelist_template_comment` และ `tb_request_for_pricing`
**Indexes:** `@@unique([name, deleted_at])` เป็น `pricelist_template_name_deletedat_u`; `@@index([name])` เป็น `pricelist_template_name_idx`

### 2.2 tb_pricelist_template_detail

แถวต่อสินค้าภายใน template Carry การอ้างอิงสินค้า, inventory unit (UoM canonical ที่สินค้า convert ไป) และ JSON `order_unit_obj` ที่จับ default order unit บวกนิยาม MOQ tier (qty + unit ต่อ tier) ที่ผู้ขายจะถูกถามให้เสนอราคา

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_template_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist_template.id` |
| `sequence_no` | `Int` | Yes | ลำดับแถวภายใน template; default `1` |
| `comment` | `String @db.VarChar` | Yes | comment ต่อแถว |
| `product_id` | `String @db.Uuid` | No | FK ไป `tb_product.id`; required |
| `product_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot ชื่อสินค้าแปลภาษา |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `inventory_unit_id` | `String @db.Uuid` | Yes | UoM ฐาน inventory ตอนสร้าง template |
| `inventory_unit_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ inventory unit |
| `order_unit_obj` | `Json @db.JsonB` | Yes | default order unit + นิยาม MOQ tier; structure `{ default_order: { unit_id, unit_name }, moq: [ { unit_id, unit_name, note, qty }, ... ] }`; default `{}` |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | cost dimension ต่อแถว; default `[]` |
| `doc_version` | `Int @db.Integer` | No | optimistic-concurrency version; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK: `pricelist_template_id → tb_pricelist_template.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`, required) Back-relation ไป `tb_pricelist_template_detail_comment`
**Indexes:** `@@unique([pricelist_template_id, product_id, deleted_at])` เป็น `pricelist_template_detail_pricelist_template_id_product_id_u`; `@@index([pricelist_template_id, product_id])` และ `@@index([product_id])`

### 2.3 tb_pricelist_template_comment

Entry activity-log แนบกับ header ของ template ถือ comment ของ user และ event `system` (การเปลี่ยนสถานะ, การแก้ vendor-instruction)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_template_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist_template.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | id user ผู้เขียน (null สำหรับ `system`) |
| `message` | `String` | Yes | body comment ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `pricelist_template_id → tb_pricelist_template.id` (`NoAction`)
**Indexes:** ไม่ได้ประกาศนอกจาก primary key

### 2.4 tb_pricelist_template_detail_comment

คู่ของ `tb_pricelist_template_comment` ในระดับแถว จับ comment และ event ของระบบที่แนบกับแถว template detail เดียว

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_template_detail_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist_template_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | id user ผู้เขียน (null สำหรับ `system`) |
| `message` | `String` | Yes | body ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | array ของ attachment; default `[]` |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (audit มาตรฐาน) | Yes | คอลัมน์ audit มาตรฐาน |

**Constraints:** `@id` บน `id` FK `pricelist_template_detail_id → tb_pricelist_template_detail.id` (`NoAction`)

### 2.5 tb_request_for_pricing

object "campaign" ในภาษา carmen/docs ผูก template หนึ่งกับ vendor cohort ที่มีวันที่เริ่ม / สิ้นสุด, ข้อความ custom และการอ้างอิง email-template; invitation ต่อผู้ขายถูกเขียนไปยัง `tb_request_for_pricing_detail` มี **คอลัมน์สถานะ Prisma ที่ไม่มี** — แอป derive `draft` / `active` / `paused` / `completed` / `cancelled` จาก `start_date`, `end_date` และจำนวน pricelist ที่ submit บนแถว detail ของมัน

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ campaign; unique ในแถวที่ไม่ถูก soft-delete |
| `pricelist_template_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist_template.id`; template ที่ campaign ออก |
| `start_date` | `DateTime @db.Timestamptz(6)` | Yes | Vendor portal เปิดที่วันนี้ |
| `end_date` | `DateTime @db.Timestamptz(6)` | Yes | Deadline การ submission |
| `custom_message` | `String @db.Text` | Yes | ข้อความอิสระที่ render ในเนื้อหา email และบน portal |
| `email_template_id` | `String @db.VarChar` | Yes | การอ้างอิงชื่อหรือ id ของ tenant email template |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension / classification; default `[]` |
| `doc_version` | `Int @db.Integer` | No | optimistic-concurrency version; default `0` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `pricelist_template_id → tb_pricelist_template.id` (`NoAction`) Back-relation ไป `tb_request_for_pricing_detail` และ `tb_request_for_pricing_comment`
**Indexes:** `@@unique([name, deleted_at])` เป็น `request_for_pricing_name_u`; `@@index([pricelist_template_id])`; `@@index([name])`

### 2.6 tb_request_for_pricing_detail

แถว invitation ต่อผู้ขาย Carry การอ้างอิงผู้ขายที่เชิญ, contact triplet (ผู้ติดต่อ / โทร / อีเมล), link pricelist แบบเลือกได้ (populate เมื่อผู้ขายบันทึก draft ครั้งแรก) และ — สำคัญที่สุด — `pricelist_url_token` ที่ให้สิทธิ์การเข้า portal ของผู้ขาย ไม่มีคอลัมน์ "invitation status" แยก: แอป infer `pending` / `in-progress` / `submitted` / `approved` / `expired` จาก `tb_pricelist.status`, `tb_pricelist.submitted_at` ที่ link และ `end_date` ของ campaign

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `request_for_pricing_id` | `String @db.Uuid` | No | FK ไป `tb_request_for_pricing.id` |
| `sequence_no` | `Int` | Yes | ลำดับแถวภายใน campaign; default `1` |
| `comment` | `String @db.VarChar` | Yes | comment ต่อแถว (เช่น language preference, escalation note) |
| `vendor_id` | `String @db.Uuid` | No | FK ไป `tb_vendor.id`; ผู้ขายที่เชิญ |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้ขาย |
| `contact_person` | `String @db.VarChar` | Yes | ชื่อผู้ติดต่อฝั่งผู้ขาย |
| `contact_phone` | `String @db.VarChar` | Yes | โทรผู้ติดต่อฝั่งผู้ขาย |
| `contact_email` | `String @db.VarChar` | Yes | อีเมลผู้ติดต่อฝั่งผู้ขาย (ใช้สำหรับอีเมล invitation) |
| `pricelist_id` | `String @db.Uuid` | Yes | FK ไป `tb_pricelist.id`; populate ตอนบันทึกครั้งแรก |
| `pricelist_no` | `String @db.VarChar` | Yes | Snapshot ของหมายเลขอ้างอิง pricelist |
| `pricelist_url_token` | `String @db.VarChar` | Yes | Token cryptographic ต่อ invitation อนุญาตการเข้า portal |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension; default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension; default `[]` |
| `doc_version` | `Int @db.Integer` | No | optimistic-concurrency version; default `0` |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (audit มาตรฐาน) | Yes | คอลัมน์ audit มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `request_for_pricing_id → tb_request_for_pricing.id` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`, required); `pricelist_id → tb_pricelist.id` (`NoAction`, optional) Back-relation ไป `tb_request_for_pricing_detail_comment`
**Indexes:** `@@unique([request_for_pricing_id, vendor_id, deleted_at])` เป็น `request_for_pricing_detail_request_for_pricing_id_vendor_id_u`; `@@index([request_for_pricing_id, vendor_id])`

### 2.7 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment

Activity-log surface บน header ของ campaign และ invitation ต่อผู้ขาย รูปร่างเดียวกันกับตาราง template comment — `id`, FK ไป parent, enum `type` (`user` / `system`), `user_id`, `message`, `attachments` และคอลัมน์ audit มาตรฐาน

| ตาราง | Parent FK | วัตถุประสงค์ |
| ----- | --------- | ------- |
| `tb_request_for_pricing_comment` | `request_for_pricing_id → tb_request_for_pricing.id` | activity log ระดับ campaign: campaign สร้าง, ผู้ขายถูกเลือก, email dispatch, reminder fire, campaign ปิด |
| `tb_request_for_pricing_detail_comment` | `request_for_pricing_detail_id → tb_request_for_pricing_detail.id` | activity log invitation ต่อผู้ขาย: email sent / opened / clicked, portal first-access, draft saved, submission completed Telemetry email และ portal ละเอียด (delivered, opened, clicked, IP, จำนวน session) ที่ carmen/docs อธิบาย อยู่ใน JSON ของ `attachments` / `message` ในชั้นแอป; ไม่มีคอลัมน์ Prisma dedicated สำหรับมัน |

### 2.8 tb_pricelist

Header ของ pricelist ที่ผู้ขาย submit Carry หมายเลขอ้างอิง pricelist, สถานะ, การอ้างอิงผู้ขาย, validity window, สกุลเงิน, วิธีการ submission และ portal `url_token` (สำเนา denormalised ของ invitation token สำหรับการ navigate portal โดยตรงหลังการ rotate token) Header หนึ่งมีแถว `tb_pricelist_detail` หลายแถว; pricelist อาจถูก link กลับไปยังแถว `tb_request_for_pricing_detail` ต้นทาง แต่ FK อยู่ฝั่ง invitation (`tb_request_for_pricing_detail.pricelist_id`)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_no` | `String @db.VarChar` | No | หมายเลขอ้างอิง pricelist; unique ในแถวที่ไม่ถูก soft-delete |
| `name` | `String @db.VarChar` | Yes | ชื่อ pricelist (เช่น "Q2 2026 — Vendor A — Beverages") |
| `status` | `enum_pricelist_status` | No | สถานะเอกสาร; default `draft` |
| `url_token` | `String @db.VarChar` | Yes | Token การเข้า portal สำหรับ navigate ตรง; สำเนา denormalised ของ invitation token |
| `vendor_id` | `String @db.Uuid` | Yes | FK ไป `tb_vendor.id` |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อผู้ขาย |
| `effective_from_date` | `DateTime @db.Timestamptz(6)` | Yes | จุดเริ่ม validity window |
| `effective_to_date` | `DateTime @db.Timestamptz(6)` | Yes | จุดสิ้นสุด validity window |
| `currency_id` | `String @db.Uuid` | Yes | FK ไป `tb_currency.id`; สกุลเงิน submission ที่ vendor เลือก |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสกุลเงิน |
| `submission_method` | `pricelist_submission_method` | Yes | วิธีที่ pricelist ถูกส่งกลับ; default `online` |
| `submitted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ที่ผู้ขายคลิก Submit |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระ |
| `note` | `String @db.VarChar` | Yes | โน้ตข้อความอิสระ |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension สำหรับ attribute header เฉพาะ tenant (คะแนนคุณภาพ, ผล validate, telemetry); default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | array cost-dimension; default `[]` |
| `doc_version` | `Int @db.Integer` | No | optimistic-concurrency version; default `0` |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (audit มาตรฐาน) | Yes | คอลัมน์ audit มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `vendor_id → tb_vendor.id` (`NoAction`); `currency_id → tb_currency.id` (`NoAction`) Back-relation ไป `tb_pricelist_detail`, `tb_pricelist_comment` และ `tb_request_for_pricing_detail`
**Indexes:** `@@unique([pricelist_no, deleted_at])` เป็น `pricelist_pricelist_no_u`; `@@index([name])`; `@@index([pricelist_no])`

### 2.9 tb_pricelist_detail

แถวสินค้าบน pricelist ที่ submit Carry การอ้างอิงสินค้า, หน่วย, MOQ qty, price-without-tax / tax / price, lead time, flag `is_preferred` (การกำหนด preferred-vendor ต่อแถว) และฟิลด์ rating Structure MOQ คือ **หนึ่งแถวต่อ MOQ tier** — unique key `(pricelist_id, product_id, unit_id, moq_qty)` อนุญาตหลายแถวต่อสินค้าเพื่อให้ผู้ขายเสนอราคาต่างกันที่ MOQ 1 / 50 / 100

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist.id` |
| `sequence_no` | `Int` | Yes | ลำดับแถวภายใน pricelist; default `1` |
| `product_id` | `String @db.Uuid` | No | FK ไป `tb_product.id`; required |
| `product_code` | `String @db.VarChar` | Yes | Snapshot ของรหัสสินค้า |
| `product_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อสินค้า |
| `product_local_name` | `String @db.VarChar` | Yes | Snapshot ชื่อสินค้าแปลภาษา |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot ของ SKU |
| `unit_id` | `String @db.Uuid` | Yes | FK ไป `tb_unit.id`; หน่วยที่ผู้ขายเสนอราคา |
| `unit_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อหน่วย |
| `is_preferred` | `Boolean` | Yes | `true` เมื่อแถวนี้เป็น preferred-vendor pick สำหรับสินค้า; default `false` |
| `rating` | `Int` | Yes | rating ต่อแถวที่ใช้โดย price-assignment engine; default `0` |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK ไป `tb_tax_profile.id` |
| `tax_profile_name` | `String @db.VarChar` | Yes | Snapshot ของชื่อ tax profile |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | อัตราภาษีที่มีผล; default `0` |
| `moq_qty` | `Decimal @db.Decimal(20, 5)` | Yes | minimum order quantity สำหรับราคาแถวนี้; default `0` หลายแถวต่อ `(pricelist, product, unit)` อนุญาตที่ MOQ ต่างกัน |
| `price_without_tax` | `Decimal @db.Decimal(20, 5)` | Yes | ราคาต่อหน่วยสุทธิภาษี; default `0` |
| `tax_amt` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวนภาษีต่อหน่วยที่ราคานี้; default `0` |
| `price` | `Decimal @db.Decimal(20, 5)` | Yes | ราคาต่อหน่วยรวมภาษี (`price_without_tax + tax_amt`); default `0` |
| `lead_time_days` | `Int @db.Integer` | Yes | lead time ที่ผู้ขายเสนอในวัน; default `0` |
| `is_active` | `Boolean` | Yes | แถว active ไหม; default `true` |
| `description` | `String @db.VarChar` | Yes | คำอธิบายข้อความอิสระ |
| `note` | `String @db.VarChar` | Yes | โน้ตข้อความอิสระ |
| `comment` | `String @db.VarChar` | Yes | comment ต่อแถว |
| `info` | `Json @db.JsonB` | Yes | กระเป๋า extension (ผล validate ต่อแถว, quality flag); default `{}` |
| `dimension` | `Json @db.JsonB` | Yes | cost dimension ต่อแถว; default `[]` |
| `doc_version` | `Int @db.Integer` | No | optimistic-concurrency version; default `0` |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (audit มาตรฐาน) | Yes | คอลัมน์ audit มาตรฐาน |

**Constraints:** `@id` บน `id` FK: `pricelist_id → tb_pricelist.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`, required); `unit_id → tb_unit.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`) Back-relation ไป `tb_purchase_request_detail` (แถว PR detail สามารถอ้างอิงแถว pricelist เฉพาะเป็นแหล่งราคา) และ `tb_pricelist_detail_comment`
**Indexes:** `@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])` เป็น `pricelist_detail_pricelist_id_product_id_unit_id_moqqty_u` — สังเกตว่า `moq_qty` เป็นส่วนหนึ่งของความ unique รองรับรูปแบบ multi-MOQ-tier-per-product; `@@index([pricelist_id, product_id])`

### 2.10 tb_pricelist_comment / tb_pricelist_detail_comment

Activity-log surface บน header ของ pricelist และต่อแถว รูปร่างเดียวกันกับตาราง template comment — `id`, FK ไป parent, enum `type` (`user` / `system`), `user_id`, `message`, `attachments` และคอลัมน์ audit มาตรฐาน

| ตาราง | Parent FK | วัตถุประสงค์ |
| ----- | --------- | ------- |
| `tb_pricelist_comment` | `pricelist_id → tb_pricelist.id` | activity log header ของ pricelist: created, vendor saved draft, vendor submitted, ผล validate, purchaser approved / rejected, การเปลี่ยนสถานะ |
| `tb_pricelist_detail_comment` | `pricelist_detail_id → tb_pricelist_detail.id` | activity log ต่อแถว: แถวแก้โดย purchaser, validation warning แนบ, flag preferred-vendor toggle, deviation กับราคาประวัติ log |

## 3. ความสัมพันธ์

```
tb_pricelist_template ──1──*──► tb_pricelist_template_detail ──1──*──► tb_pricelist_template_detail_comment
        │  1                       │
        │  *  (back-relation)      │
        │                          └──► tb_product            (required, product_id)
        ▼
tb_pricelist_template_comment

tb_pricelist_template ──1──*──► tb_request_for_pricing ──1──*──► tb_request_for_pricing_detail
                                       │  1                            │  *
                                       ▼  *                             ├──► tb_vendor              (required, vendor_id)
                                tb_request_for_pricing_comment          ├──► tb_pricelist           (optional, pricelist_id — populate ตอนบันทึกครั้งแรก)
                                                                        └──► tb_request_for_pricing_detail_comment

tb_pricelist ──1──*──► tb_pricelist_detail ──1──*──► tb_pricelist_detail_comment
    │  1                  │
    ▼  *                  ├──► tb_product             (required, product_id)
tb_pricelist_comment      ├──► tb_unit                (unit_id)
                          ├──► tb_tax_profile         (tax_profile_id)
                          └──► tb_purchase_request_detail   (back-relation — แถว PR detail อ้างอิงแถว pricelist เป็นแหล่งราคา)

tb_pricelist  (FK ระดับ header)
    ├──► tb_vendor              (vendor_id)
    └──► tb_currency            (currency_id)

tb_pricelist_template (FK ระดับ header)
    └──► tb_currency            (currency_id)
```

โน้ต:

- **Template → request-for-pricing** เป็น 1-to-many template เดียวสามารถขับ campaign หลายตัวข้ามเวลา (รอบรายไตรมาส, การสำรวจ ad-hoc, การเก็บ event-based) Campaign carry cohort, schedule และ email-template; template carry รายการสินค้าและรูปร่าง unit/MOQ
- **Request-for-pricing → detail** เป็น 1-to-many แต่ละแถว detail เป็น invitation ของผู้ขายหนึ่งราย — unique โดย `(request_for_pricing_id, vendor_id, deleted_at)` แถว detail carry `pricelist_url_token` cryptographic และ FK ไป `tb_pricelist` (nullable จนกว่าผู้ขายจะบันทึกครั้งแรก)
- **Request-for-pricing-detail → pricelist** เป็น 1-to-1 ในเชิงปฏิบัติ: แต่ละ invitation ผลิต vendor pricelist อย่างมากที่สุดหนึ่งใบ; FK อยู่ฝั่ง invitation และ populate โดยแอปตอนบันทึกครั้งแรก
- **Pricelist → detail** เป็น 1-to-many แถว detail รองรับหลาย MOQ tier ต่อ `(pricelist, product, unit)` เพราะ `moq_qty` เป็นส่วนหนึ่งของ uniqueness key — นี่คือกลไกของ schema สำหรับ pattern การตั้งราคา "MOQ 1 / 50 / 100"
- **Pricelist-detail → PR detail** เป็น 1-to-many (back-relation): แถว pricelist เดียวสามารถเป็นแหล่งราคาสำหรับแถว PR detail หลายแถว ฝั่ง PR carry FK `tb_purchase_request_detail.pricelist_detail_id`; snapshot ของราคาตอนสร้าง PR อยู่บนแถว PR
- **Header → comment** และ **detail → comment** ทั้งคู่เป็น 1-to-many ในทุก tier ตาราง Comment เป็นบันทึก persistent ของ activity; structure "campaign analytics" / "invitation tracking" ของ carmen/docs (อัตราการตอบสนอง, อัตราการเปิด, audit IP) เป็น rollup ระดับแอปของ comment เหล่านี้บวก JSON `info`
- **ไม่มีตาราง campaign-status** enum `CollectionCampaign.status` ของ carmen/docs (`draft`, `active`, `paused`, `completed`, `cancelled`) **ไม่ใช่** คอลัมน์ Prisma บน `tb_request_for_pricing`; แอป derive จาก `start_date`, `end_date` และ count `pricelist.status` ฝั่ง detail Section 5 ทำแคตตาล็อก divergence นี้
- การประกาศ `@relation` FK ทั้งหมดใช้ `onDelete: NoAction, onUpdate: NoAction` ดังนั้นความถูกต้องของ referential รักษาโดย soft-delete ระดับแอป (`deleted_at`) แทน cascade

## 4. Enums

- **`enum_pricelist_template_status`** (`tb_pricelist_template.status`): `draft`, `active`, `inactive` `draft` คือ state ทำงานที่แก้ได้; `active` คือ state ปฏิบัติการที่ template สามารถขับ request-for-pricing campaign ใหม่ได้; `inactive` คือ state ที่ archive (template ยัง queryable ได้ แต่ไม่เลือกได้สำหรับ campaign ใหม่)
- **`enum_pricelist_status`** (`tb_pricelist.status`): `draft`, `active`, `inactive`, `expired` `draft` ครอบคลุม window ผู้ขายแก้ (auto-save) ก่อนผู้ขายคลิก Submit; `active` คือ state หลัง approve ที่ pricelist เป็นการอ้างอิงสำหรับ PR / PO / GRN; `inactive` คือ state ระงับหลัง approve (admin สามารถ re-activate); `expired` คือ auto-transition เมื่อ `effective_to_date` ผ่านไปแล้ว state เพิ่มเติม `submitted` / `under-review` / `approved` / `rejected` ของ carmen/docs **ไม่ใช่** ค่า enum Prisma — แอป infer จาก `status`, `submitted_at` และ entry audit ตาราง comment
- **`pricelist_submission_method`** (`tb_pricelist.submission_method`): `online`, `email`, `portal`, `manual` `online` คือการป้อนตรงใน portal; `email` ครอบคลุม Excel template ที่ email ไปฝ่ายจัดซื้อและอัปโหลดโดย staff; `portal` ครอบคลุม Excel template ที่ drag-and-drop บน portal; `manual` ครอบคลุมการป้อนข้อมูลตรงฝั่ง purchaser โดยไม่มี round-trip vendor portal ใด ๆ (เช่น สำหรับผู้ขายที่ปฏิเสธการใช้ portal)
- **`enum_pricelist_compare_type`** (ประกาศใน schema และอ้างอิงที่อื่น — เช่น PR line `pricelist_type`): `automatic`, `manual_select`, `manual_input` แยกแยะว่าบรรทัด PR ได้รับการอ้างอิง pricelist อย่างไร — auto-resolution จากกติกา preferred-vendor, การเลือก manual จาก candidate list หรือการป้อน manual อิสระ
- **`enum_comment_type`** (ใช้ร่วมในโมดูล): `user` (comment เขียนโดยมนุษย์), `system` (entry activity-log auto-generate โดยชั้น workflow / portal) ใช้โดยทุกตาราง comment ในโมดูลนี้

## 5. ความเบี่ยงเบนจาก carmen/docs

design ของ carmen/docs ภายใต้ `vendor-pricelist-management/` (`design.md`, `requirements.md`, `VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md`, `price-assignment-workflow-documentation.md`) อธิบายชุดเอนทิตีที่รุ่มรวยกว่าที่ Prisma carry จริงในวันนี้มาก ตารางด้านล่างจับความแตกต่างเชิง material ที่เอกสารปลายน้ำต้อง reconcile; ปฏิบัติกับ Prisma เป็น canonical สำหรับเอนทิตีและฟิลด์ และ carmen/docs เป็น canonical สำหรับ workflow / rule semantic ที่ชั้นแอปบังคับใช้บน schema ที่ slim กว่า

| # | รายการ | carmen/docs พูด | Prisma มี | การจัดการ |
|---|------|------------------|------------|--------|
| 1 | ชื่อ object "Campaign" | `CollectionCampaign` (TypeScript interface ใน design.md § Data Models) | `tb_request_for_pricing` (ไม่มี "campaign" ที่ไหนใน schema) | บันทึกทั้งสองชื่อ Carmen-wiki ใช้ "Request-for-Pricing" สำหรับชื่อเอนทิตีและ "Campaign" เป็นคำพ้องในการเล่าเรื่อง |
| 2 | enum campaign status | `'draft' \| 'active' \| 'paused' \| 'completed' \| 'cancelled'` | ไม่มีคอลัมน์ Prisma หรือ enum สำหรับ campaign status บน `tb_request_for_pricing` | แอป derive สถานะจาก `start_date`, `end_date` และ count / สถานะของ pricelist ที่ submit บนแถว detail บันทึกกติกาการ derive ใน `02-business-rules.md` |
| 3 | ชื่อ object Invitation | `VendorInvitation` (design.md § Data Models) | `tb_request_for_pricing_detail` | เหมือนข้อ 1 — ใช้ชื่อ Prisma ในการอ้างอิงเอนทิตี, "invitation" ในการเล่าเรื่อง |
| 4 | สถานะการ submission invitation | `'pending' \| 'in-progress' \| 'submitted' \| 'approved' \| 'expired'` | ไม่มีคอลัมน์ Prisma Derive จาก `tb_pricelist.status`, `tb_pricelist.submitted_at` และ `end_date` ของ campaign | บันทึกกติกาการ derive การเปลี่ยน `pending → in-progress` fire เมื่อผู้ขายเปิด portal ครั้งแรก (บันทึกเป็น `system` comment); `in-progress → submitted` เมื่อ `tb_pricelist.submitted_at` ถูกเขียน; `submitted → approved` เมื่อ `tb_pricelist.status` กลายเป็น `active`; `* → expired` เมื่อ `end_date` ผ่านไปโดยไม่มี submission |
| 5 | enum pricelist status | `'draft' \| 'submitted' \| 'under-review' \| 'approved' \| 'rejected'` (design.md) | `enum_pricelist_status = { draft, active, inactive, expired }` | mapping สอง-enum: `submitted` และ `under-review` ของ carmen/docs ทั้งคู่เป็น `draft` ใน Prisma (โดย `submitted_at IS NOT NULL` แยก "submit แล้วยังไม่ approve"); `approved` ของ carmen/docs เป็น `active` ใน Prisma; `rejected` ของ carmen/docs เป็น `draft` ใน Prisma + `system` rejection comment ใน `tb_pricelist_comment` บันทึก mapping ใน `02-business-rules.md` |
| 6 | Telemetry การเข้า portal | `portalAccess { firstAccessAt, lastAccessAt, sessionCount, ipAddresses[] }` ต่อ invitation; `emailDetails { sentAt, deliveredAt, openedAt, clickedAt }` ต่อ invitation (design.md) | ไม่มีคอลัมน์ dedicated ข้อมูลถูกเขียนไปยัง `tb_request_for_pricing_detail_comment` เป็น entry `system` กับ JSON `attachments` / `message` และ surface ผ่าน JSON `info` บนแถว parent | บันทึก pattern telemetry-via-comments ใน `02-business-rules.md` ที่ที่ต้องการการรับประกันที่แข็งกว่า (เช่น analytics query) ตาราง dedicated อยู่ใน roadmap |
| 7 | Quality score / ผล validate | `qualityScore` ตัวเลขต่อ pricelist, `validationResults` object structured (design.md § Data Models) | ไม่มีคอลัมน์ dedicated บน `tb_pricelist`; ค่าอยู่ใน JSON `info` | บันทึกรูปร่าง JSON และสัญญาของ validator สำหรับการเขียนเข้า `info` ใน `02-business-rules.md` โมเดล Prisma เป็น schemaless บนแกนนี้โดยตั้งใจเพื่อให้ validator พัฒนาได้ |
| 8 | Conversion factor ของ MOQ-tier | "Conversion factor (เช่น 1 Box = 50 Each)" ต่อ MOQ tier (design.md) | `tb_pricelist_detail` มี `unit_id` และ `moq_qty` แต่ไม่มีคอลัมน์ `conversion_factor` แยก | Conversion factor resolve ที่เวลา lookup จาก `tb_unit` (factor `conversion_factor` ของหน่วยไปยัง UoM ฐาน) ไม่ได้เก็บบนแถว pricelist สิ่งที่ carmen/docs อ้างว่ามี conversion factor ต่อแถวคือการ render ระดับแอป ไม่ใช่คอลัมน์ schema |
| 9 | Effective unit price ต่อหน่วยฐาน | "Effective unit price ต่อหน่วยฐาน" แสดงบนทุก MOQ tier (design.md) | ไม่ใช่คอลัมน์ที่เก็บ คำนวณ on-the-fly เป็น `price ÷ unit.conversion_factor` | บันทึกสูตรใน `02-business-rules.md` § Calculation Rules |
| 10 | Linkage "Preferred vendor" | ตั้ง "ต่อสินค้า (หรือต่อ category)" ด้วยตาราง preferred-vendor dedicated (design.md § Pre-Assignment Setup) | `is_preferred` boolean หนึ่งตัวบน `tb_pricelist_detail` ต่อแถว; ไม่มีตาราง preferred-vendor แยก | บันทึก pattern ต่อแถว กลไก cross-category และ rule-based ของ carmen/docs เป็น derivation ระดับแอปจาก `is_preferred` + registry `tb_business_rules`; ไม่มีตาราง schema-level "preferred-vendor-per-product" ในปัจจุบัน |
| 11 | นโยบาย token security ของ email / portal | "Token cryptographically secure ที่มีเวลาการหมดอายุที่ตั้งค่าได้และข้อจำกัดการเข้าถึง"; "การติดตาม IP address"; "การควบคุม session timeout, ข้อจำกัด concurrent session, การตรวจจับ activity ที่น่าสงสัย" (requirements.md § Requirement 28) | `tb_request_for_pricing_detail.pricelist_url_token` (หนึ่งคอลัมน์); `tb_pricelist.url_token` (สำเนา denormalised) | Surface นโยบาย token ที่รุ่มรวยกว่า (การหมดอายุ, IP restriction, concurrent session) บังคับใช้โดย middleware ของ portal ในแอป ไม่ใช่โดย schema บันทึกใน `02-business-rules.md` § Authorization Rules |
| 12 | ตาราง audit history | "Complete audit trail with user attribution and timestamps" สื่อให้เป็นตาราง dedicated (requirements.md § Requirement 19) | ไม่มีตาราง audit-trail dedicated สำหรับโมดูลนี้นอกจากตาราง comment และตาราง `tb_activity` audit ข้ามโมดูลที่ใช้ร่วมกัน | pattern เดียวกันกับโมดูลอื่น: ตาราง comment + `tb_activity` เป็น persistence; คำอธิบายเชิงเล่าเรื่องของ carmen/docs สอดคล้องกับนี้เมื่อ `tb_activity` ถูกบันทึก |

## 6. แหล่งอ้างอิง

- **Primary (แหล่งความจริง):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — vendor-pricelist model ทั้งสิบและ enum module-local สามตัว (`enum_pricelist_template_status`, `enum_pricelist_status`, `pricelist_submission_method`) บวก `enum_pricelist_compare_type` และ `enum_comment_type` ที่ใช้ร่วม
- **Secondary (ตรวจสอบแนวคิด):** `../carmen/docs/vendor-pricelist-management/` — เอกสาร design / requirements แปดฉบับ:
  - `design.md` — สถาปัตยกรรม 6-phase, component breakdown, TypeScript data-model interface (ใช้เป็น carmen/docs basis สำหรับตาราง divergence ใน Section 5)
  - `requirements.md` — 30+ functional requirement ครอบคลุม vendor CRUD, template setup, การจัดการ campaign, UX portal, multi-currency, validation, audit
  - `price-assignment-workflow-documentation.md` — business rule engine, rule category, vendor eligibility, real-time assignment logic (foundational สำหรับ `02-business-rules.md` § Cross-Module Rules)
  - `VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md` — technical spec ครอบคลุม vendor CRUD, RBAC, integration architecture
  - `VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — feature ของ vendor portal และ posture ด้านความปลอดภัย
  - `pricelist-management-navigation-summary.md` — tree การ navigate UI สำหรับโมดูล
  - `vendor-product-assignments-summary.md` — pattern การ assignment vendor↔product underpin flag preferred-vendor บน `tb_pricelist_detail`
  - `tasks.md` — รายการงานการ implement
- **Sibling reference:** `en/purchase-request/01-data-model.md` — `tb_purchase_request_detail` carry back-reference `pricelist_detail_id` เข้าโมดูลนี้; บันทึกที่นั่น ไม่ซ้ำที่นี่
- โมดูลที่เกี่ยวข้อง: [product](/th/inventory/product) (ทุกแถว pricelist detail อ้างอิงสินค้า), [purchase-request](/th/inventory/purchase-request) (บรรทัด PR default ราคาจาก pricelist active), [purchase-order](/th/inventory/purchase-order) (PO snapshot ราคา pricelist ตอน PR-to-PO conversion), [good-receive-note](/th/inventory/good-receive-note) (GRN price-variance check รันกับ pricelist active)
