---
title: คำขอใบเสนอราคา (Request for Quotation)
description: เอกสารคำขอราคา outbound (RFQ) ส่ง email ไปยังผู้ขายหนึ่งรายหรือมากกว่า — แต่ละรายได้ลิงก์ portal ที่หมดอายุได้; submission ลงเป็น pricelist ที่ submitted
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# คำขอใบเสนอราคา (Request for Quotation)

> **At a Glance**
> **เจ้าของ:** Purchaser / Procurement Manager &nbsp;·&nbsp; **ตาราง:** `tb_request_for_pricing` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** ไม่มี (ขับด้วย date-window) &nbsp;·&nbsp; **ต้นน้ำ:** [templates/price-list](/th/inventory/templates/price-list) &nbsp;·&nbsp; ขอใบเสนอราคาจากผู้ขายก่อนได้รับการมอบ `tb_pricelist`
> **Re-sync 2026-09-22:** action **Send email** ต่อผู้ขาย (`POST …/request-for-pricings/:id/send-email`, 2026-09-16); ลิงก์ portal ตอนนี้หมดอายุที่ `end_date` ของ RFQ (`UrlTokenGuard`); Save/Submit ของ portal ทำงานได้และผลิต pricelist `submitted`; detail response expand `vendor`, `pricelist { id, no, name, status }` และ `pricelist_template { …, currency }` เป็น object

![คำขอใบเสนอราคา (Request for Quotation) screen](/screenshots/vendor-pricelist/request-price-list.png)

![คำขอใบเสนอราคา (Request for Quotation) detail screen](/screenshots/vendor-pricelist/request-price-list-detail.png)

## 1. ภาพรวมและผู้ใช้งาน

**Request for Pricing (RFQ)** คือเอกสาร outbound ที่ procurement-initiate ขอใบเสนอราคาจากผู้ขายหนึ่งรายหรือมากกว่าก่อน [vendor-pricelist](/th/inventory/vendor-pricelist) ได้รับการมอบ ผู้ซื้อหยิบ [templates/price-list](/th/inventory/templates/price-list) (ซึ่ง carry สกุลเงิน, validity window, schedule reminder และแคตตาล็อกสินค้าที่อยู่ใต้การ quote), ตั้งชื่อผู้ขาย candidate และ dispatch คำขอ ผู้ขายที่เชิญแต่ละรายได้ **link ที่ tokenise** (ส่ง email จากแถว vendor ของ RFQ) ไปยัง portal ที่พวกเขาตั้งราคาสินค้าของ template บันทึก draft และ submit; submission คือ `tb_pricelist` ที่ `status = submitted` keyed กลับไปยังแถว RFQ หลัง deadline ลิงก์หยุดทำงาน; ผู้ซื้อ review pricelist ที่ submit แล้วบนหน้าจอ Price List และ *มอบ* หนึ่ง (หรือหลาย) โดย flip สถานะของมันเป็น `active`

**สร้างโดย** Purchaser &nbsp;·&nbsp; **ตอบกลับโดย** ผู้ขายที่เชิญ (ไม่มี login — portal scope ด้วย token ที่ save และ submit ได้; ดู [03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor)) &nbsp;·&nbsp; **ไม่ผลิตผลกระทบ inventory หรือ AP**

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง RFQ จาก template | Vendor Management → Request Price List → **New** | Template ผูกสกุลเงิน + แคตตาล็อกสินค้า |
| เชิญผู้ขาย | ฟอร์ม create เดียวกัน → dialog **Add vendors** (multi-select, 2026-08-06) | แถว invitation ทั้งหมด (พร้อม `pricelist_url_token`, JWT และแถว `tb_shot_url` ที่ `expired_at = end_date` ของแต่ละแถว) ถูกสร้างใน `POST` call เดียวกันกับ header ของ RFQ — ไม่มีขั้นตอน "launch" แยกต่างหาก |
| ส่ง email ลิงก์ให้ผู้ขาย | Detail → แถว vendor → **Send email** (คอลัมน์ action, 2026-09-10) | เปิด dialog เดียวกับ email ของ PO: เลือก email profile (`profile_id`), ป้อน `to` / `cc` optional และ `subject` / HTML `body` ที่เติมไว้ล่วงหน้าจาก email template ที่มี placeholder `rfp` (ลิงก์ portal `/pl/:url_token` ประกอบฝั่ง client); `POST …/request-for-pricings/:id/send-email` (`vendor_id` optional) → activity `email_sent` ส่งทีละผู้ขาย; ไม่มีปุ่ม "send to all" |
| เพิ่มผู้ขายลงใน RFQ ที่มีอยู่ | Detail → edit → เพิ่มแถว vendor | `PATCH` รองรับ `vendors.add`/`vendors.remove`/`vendors.update`; unique constraint บน `(request_for_pricing_id, vendor_id)` บังคับไม่ให้เชิญซ้ำ |
| ติดตามการตอบกลับ | RFQ detail → แถว vendor | `has_submitted` และ `pricelist { no, status }` ที่ลิงก์ต่อผู้ขาย (`submitted` เมื่อผู้ขายคลิก Submit; ยังคง `draft` ถ้าแค่เปิด/save) |
| เปรียบเทียบ / มอบ | Purchaser เปิด pricelist `submitted` ของ vendor บนหน้าจอ **Price List** | การมอบ = การตั้ง `tb_pricelist.status = active` ของผู้ชนะจากฟอร์ม edit ของ Price List — ไม่มีปุ่ม "Compare" หรือ "Activate" บนหน้าจอ RFQ เอง และไม่พบ UI เปรียบเทียบการเสนอราคาใด ๆ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| "Vendor already invited" | มีแถว detail ที่ไม่ถูกลบสำหรับ (RFQ, vendor) | **ยืนยันแล้ว** — `@@unique([request_for_pricing_id, vendor_id, deleted_at])` |
| การสร้าง RFQ ถูก reject เพราะช่วงวันที่ไม่ถูกต้อง | `start_date > end_date` | **ยืนยันแล้ว** — `request-for-pricing.service.ts` `create()` เช็คสิ่งนี้อย่างชัดเจน (`RFP_INVALID_DATE_RANGE`) |
| "Cannot change template — invitations sent" | `pricelist_template_id` immutable หลัง dispatch | **ไม่ยืนยัน** `update()` รับ `pricelist_template_id` ใหม่โดยไม่มีการเช็ค immutability เลย แม้จะมีแถว vendor อยู่แล้วก็ตาม |
| การ submission สายถูก reject หลัง `end_date` | ลิงก์ portal หมดอายุ | **Confirmed (2026-09-22) — ที่ guard ไม่ใช่ใน service** `UrlTokenGuard` คืน 401 `url_token has expired` เมื่อ `tb_shot_url.expired_at` (ตั้งเป็น `end_date` ของ RFQ ตอนออก token) ผ่านไปแล้ว; ทุก call ของ portal รวมถึงการเปิดครั้งแรกถูก block และ portal React แสดง *This link has expired* การขยาย `end_date` ภายหลัง **ไม่** refresh token ที่มีอยู่ |
| "Vendor must be active" | `tb_vendor.is_active = false` บล็อกการเชิญ | **ไม่ยืนยัน** ไม่พบการเช็ค `is_active` บน vendor ใน `create()` หรือ `update()` |
| Invitation link คืน 401 | token ไม่รู้จัก หรือ `expired_at` ผ่านไปแล้ว | `UrlTokenGuard`; แถว detail ของ RFQ ที่ถูก soft-delete ถูกรายงานโดย `checkPriceList()` เป็น `Request for pricing detail not found` (404) ไม่มีโค้ด token-rotation หรือ revoke |
| Send email ล้มเหลวด้วย permission/login bounce | app-id `requestForPricing.sendEmail` หายไปจาก app-id allow-list ของ tenant | เพิ่มใน platform app catalog ก่อนใช้ (ระบุใน commit `2b750267e`) |

## 4. กรณีพิเศษ

- **ความปลอดภัย Token** `pricelist_url_token` เป็น string สุ่มต่อ invitation ถูกสร้างครั้งเดียวตอน RFQ-create และ map ในตาราง platform `tb_shot_url` ไปยัง JWT (`{ bu, vendor_id, rfp_detail_id }`, `JWT_EXPIRES_IN`) และ `expired_at = end_date`; การเข้า portal scope โดย token เพียงผู้เดียว (vendor ไม่ authenticate) การหมดอายุถูกบังคับใช้โดย `UrlTokenGuard`; ไม่มีการจำกัด IP และไม่มีโค้ด revocation/rotation
- **การ submit สายถูก block ด้วยการหมดอายุ ไม่ใช่ business rule** ไม่มีสิ่งใดใน `check-price-list.service.ts` อ่าน `start_date`/`end_date` นอกจากเพื่อลงวันที่ pricelist ที่สร้างอัตโนมัติ (`effective_from/to`); deadline มีผลเพียงเพราะลิงก์ตายที่ `end_date` RFQ ที่สร้างโดยไม่มี `end_date` ได้ token ที่การหมดอายุขับด้วย `null` — ให้ถือเป็นคำถามที่ยังเปิดอยู่
- **การมอบเป็นการ flip ระดับ pricelist ไม่ใช่ระดับ RFQ** RFQ ไม่มีคอลัมน์สถานะของตัวเอง — "การมอบ" คือการที่ Purchaser ตั้ง `tb_pricelist.status = active` ที่เลือกโดยตรงบนหน้าจอ Price List
- **Cascade สกุลเงิน** Template ให้สกุลเงิน default แก่ draft pricelist ที่สร้างอัตโนมัติ; ไม่พบสิ่งใดที่ป้องกัน Purchaser จากการเปลี่ยน `currency_id` ภายหลังบนฟอร์ม edit ของ Price List
- **ไม่พบ reminder job** การค้นหาทั่ว repo ของโมดูลนี้และ `micro-cronjobs` ไม่พบ scheduled job ที่อ่าน `reminder_days`/`escalation_after_days` — ฟิลด์ template เหล่านั้นถูกเก็บไว้แต่ปัจจุบันไม่มีผลใด ๆ การสื่อสารขาออกเดียวคือ **Send email** แบบ manual ต่อผู้ขาย
- **activity ของ portal ถูก log** การเปิดครั้งแรก (`create`), การ save draft แต่ละครั้ง (`vendor.pricelist.draft_saved`) และการ submit ถูกเขียนลง `tb_activity` พร้อม snapshot ก่อน/หลัง (2026-09-11/12); action send-email เขียน `email_sent` สิ่งเหล่านี้ปรากฏใน Activity panel ของ RFQ / pricelist
- **ไม่มี workflow engine** RFQ ไม่มีคอลัมน์ `workflow_*` และไม่มีคอลัมน์สถานะเลย; สัญญาณที่ใกล้เคียงที่สุดต่อ vendor คือ `has_submitted: !!pricelist_id`

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_request_for_pricing`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดง RFQ (เช่น "Q2-2026 Beverage RFQ") |
| `pricelist_template_id` | `String @db.Uuid` | No | FK ไป [templates/price-list](/th/inventory/templates/price-list) Carry สกุลเงิน, validity, reminder, แคตตาล็อก |
| `start_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่ vendor อาจเริ่ม submit |
| `end_date` | `DateTime? @db.Timestamptz(6)` | Yes | Deadline การ submission; ขับ reminder |
| `custom_message` | `String? @db.Text` | Yes | ข้อความอิสระ render ในอีเมล invitation |
| `email_template_id` | `String? @db.VarChar` | Yes | Identifier สำหรับ invitation / reminder mail |
| `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `request_for_pricing_name_u`; `@@index([pricelist_template_id])`; `@@index([name])` FK ไป `tb_pricelist_template` `onDelete: NoAction`

### 5.2 `tb_request_for_pricing_detail`

หนึ่งแถวต่อ vendor ที่เชิญ

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `request_for_pricing_id`, `sequence_no` | mixed | No / No / Yes | PK, FK parent, ordinal |
| `vendor_id`, `vendor_name` | `String @db.Uuid` / `VarChar` | No / Yes | Vendor ที่เชิญ + snapshot |
| `contact_person`, `contact_phone`, `contact_email` | `String? @db.VarChar` | Yes | Contact ฝั่ง vendor สำหรับรอบนี้ |
| `pricelist_id`, `pricelist_no` | `String? @db.Uuid` / `VarChar` | Yes | FK ไป `tb_pricelist` ที่สร้างตอน submission — null จนกว่า |
| `pricelist_url_token` | `String? @db.VarChar` | Yes | Fragment URL ที่ tokenise สำหรับ portal invitation |
| `comment`, `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([request_for_pricing_id, vendor_id, deleted_at])` — หนึ่ง invitation ต่อ (RFQ, vendor); `@@index([request_for_pricing_id, vendor_id])` FK ไป `tb_request_for_pricing`, `tb_vendor`, `tb_pricelist` — ทั้งหมด `onDelete: NoAction`

### 5.3 ตาราง Comment

`tb_request_for_pricing_comment` และ `tb_request_for_pricing_detail_comment` ตามรูปร่าง comment canonical

## 6. Workflow / กติกาทางธุรกิจ

RFQ **ไม่มีคอลัมน์สถานะและไม่มี workflow engine** — `tb_request_for_pricing` carry เพียง `start_date`/`end_date` เป็นฟิลด์เชิงพรรณนา; ไม่มีอะไรในโค้ดที่อ่านมันเพื่อ gate หรือ derive lifecycle state สิ่งที่เกิดขึ้นจริง ยืนยันเทียบกับ `request-for-pricing.service.ts` และ `check-price-list.service.ts`:

- **Create** — header ของ RFQ พร้อมแถว vendor detail ทั้งหมด (พร้อม `pricelist_url_token` ของแต่ละแถว) ถูก insert ใน `create()` call เดียว ไม่มีขั้นตอน "invitation sent" แยกต่างหากหรือโค้ด dispatch — token มีอยู่ตั้งแต่ขณะสร้าง ไม่ว่าจะมีอะไรสื่อสารไปยัง vendor หรือไม่ก็ตาม
- **การเข้า Portal** — `POST /api/check-pricelist/:url_token` ครั้งแรกของ vendor สร้าง draft `tb_pricelist` ราคาศูนย์จาก template โดยอัตโนมัติ ลงวันที่ `effective_from/to = start_date/end_date` เมื่อ RFQ มีค่าเหล่านั้น ถูก gate เพียงโดย `expired_at` ของ token (= `end_date`) ใน `UrlTokenGuard` ไม่ใช่โดย `start_date`
- **Save / submit บน Portal** — `PATCH …/pricelist-external/:url_token` คง pricelist เป็น `draft`; `POST …/submit` ตั้ง `submitted` + `submitted_at` และลบแถวที่ไม่มีราคา ทั้งสองต้องการให้ pricelist ยังเป็น `draft`
- **Send email** — `POST …/request-for-pricings/:id/send-email` ผ่าน email profile ที่ตั้งค่าไว้; HTML ของ body ถูก sanitise ด้วย allow-list (`common/email-body.ts`); ผลลัพธ์ log เป็น `email_sent`
- **ไม่มี reminder, ไม่มี escalation, ไม่มีการบังคับใช้ deadline** — `reminder_days[]` และ `escalation_after_days` ถูกเก็บไว้บน template แต่ไม่มีอะไรอ่านมัน; ไม่พบ scheduled job ใน repo นี้หรือใน `micro-cronjobs`
- **การมอบ** — Purchaser ตั้ง `tb_pricelist.status = active` ที่เลือกโดยตรงบนหน้าจอ Price List; โค้ดของโมดูลนี้เองไม่แตะฟิลด์นั้น

**การ validate วันที่:** `start_date <= end_date` ถูกเช็คตอน RFQ create (`RFP_INVALID_DATE_RANGE`); ไม่พบกติกาวันที่อื่น **การผูก Template:** `pricelist_template_id` สามารถเปลี่ยนได้บน `update()` โดยไม่มี immutability guard ใด ๆ ขัดแย้งกับข้ออ้างที่เคยมีเอกสารไว้ว่า "immutable หลัง invitation แรก" **สกุลเงิน:** draft ที่สร้างอัตโนมัติ inherit `currency_id` จาก template แต่ไม่มีอะไรป้องกันการเปลี่ยนมันภายหลังบนฟอร์ม edit ของ Price List

## 7. ความเชื่อมโยงข้ามโมดูล

- [vendor-pricelist](/th/inventory/vendor-pricelist) — การตอบสนองของ vendor materialise เป็นแถว `tb_pricelist`; ตัวที่ได้รับมอบกลายเป็นแคตตาล็อก active
- [templates/price-list](/th/inventory/templates/price-list) — RFQ ต้องการ template (สกุลเงิน, validity, reminder, แคตตาล็อกสินค้า)
- [master-data/vendor](/th/inventory/master-data/vendor) — vendor ที่เชิญอ้างอิง `tb_vendor`; ไม่พบการเช็ค `is_active` ตอนเชิญ
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงิน default จาก template
- [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) — ผู้บริโภคปลายน้ำของ pricelist ที่ได้รับมอบ
- [system-config/workflow](/th/inventory/system-config/workflow) — *ไม่ใช้* โดย RFQ; กล่าวเพื่อความตรงข้าม
- [03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor) — confirmed gap ใน backend route ของ Save/Submit ของ portal

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_request_for_pricing` (บรรทัด 4405), `tb_request_for_pricing_comment` (บรรทัด 4438), `tb_request_for_pricing_detail` (บรรทัด 4473), `tb_request_for_pricing_detail_comment` (บรรทัด 4511) *(แก้ไข 2026-07-16 — การอ้างอิงก่อนหน้าที่บรรทัด 4039-4176 ไม่ตรงกับไฟล์ schema ปัจจุบันอีกต่อไป)*
- **Frontend route:** `../carmen-inventory-frontend-react/routes/vendor-management/request-price-list/`; external portal: `routes/external/pl/`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/request-for-pricing/request-for-pricing.service.ts` (`create`, `createVendorDetailWithToken`, `generateVendorToken`, `insertVendorPricelist`, `sendEmail`), `.../check-price-list/check-price-list.service.ts`; gateway `apps/backend-gateway/src/application/request-for-pricings/request-for-pricings.controller.ts` (`POST :id/send-email`, app-id `requestForPricing.sendEmail`; `GET :id/print-viewer`), `apps/backend-gateway/src/auth/guards/url-token.guard.ts`; platform schema `tb_shot_url`
- **Frontend:** `routes/vendor-management/request-price-list/` — `rfp-send-email-dialog.tsx`, `use-rfp-send-email.ts`, `rfp-vendor-add-dialog.tsx`, `rfp-vendor-cells.tsx`; `types/request-price-list.ts`
- **E2E:** ไม่มี spec สำหรับหน้าจอ RFQ; portal มี catalog แบบเอกสารเท่านั้น `../carmen-inventory-frontend-e2e/docs/test-cases/1002-external-price-list.md` (42 case, `TC-EPL-*`)
- **Carmen docs:** `../carmen/docs/business-analysis/price-list-ba.md`; `../carmen/docs/business-analysis/procurement-ba.md` (ส่วน RFQ) — ถือเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว ตาม Section 6 ข้างต้น
