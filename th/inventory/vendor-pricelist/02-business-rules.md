---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Business Rules
description: กติกา validation, การคำนวณ, authorization, การเปลี่ยนสถานะ และกติกาข้ามโมดูลสำหรับ vendor-pricelist
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Business Rules

> **At a Glance**
> **กลุ่มกติกา:** `VPL_VAL_*` validation &nbsp;·&nbsp; `VPL_CALC_*` calc &nbsp;·&nbsp; `VPL_XMOD_*` cross-module
> **กลุ่มผู้ใช้:** Test author + developer — ทุก rule ID anchor จากหน้า `04-test-scenarios*`
> **สถานะการ implement (ตรวจสอบเมื่อ 2026-07-16):** แถวส่วนใหญ่ด้านล่างถูก mark เป็น **Confirmed** (มีโค้ดจริง: Zod check, Prisma constraint หรือ `if` ที่ชัดเจนใน service method) หรือ **Design-target** (มีอยู่ใน `../carmen/docs/vendor-pricelist-management/` แต่ไม่มีโค้ดที่ตรงกันเลยใน `carmen-inventory-frontend-react` หรือ `carmen-turborepo-backend-v2`) โมดูลนี้ **ไม่มี workflow engine**, **ไม่มี endpoint แยกสำหรับ approve/reject/submit**, **ไม่มี quality score**, **ไม่มี validation engine เกินกว่าการตรวจสอบระดับฟิลด์** และ **ไม่มีการเขียน comment/activity-log อัตโนมัติ** — ดู [01-data-model](/th/inventory/vendor-pricelist/01-data-model) § 5 และ [01a-data-model-comments](/th/inventory/vendor-pricelist/01a-data-model-comments) สำหรับหลักฐานที่มา

## 1. ภาพรวม

หน้านี้จับกติกาเชิงปฏิบัติการของสี่หน้าจอจริงในโมดูล — **Vendor**, **Price List** (`tb_pricelist`), **Price List Template** (`tb_pricelist_template`) และ **Request for Pricing** (`tb_request_for_pricing`, มีรายละเอียดที่ [request-price-list](/th/inventory/vendor-pricelist/request-price-list)) — บวก external vendor portal แต่ละตัวใน Price List, Price List Template และ Request for Pricing เป็น plain CRUD resource: create / find / update / soft-delete พร้อม `doc_version` optimistic-concurrency locking บนทุกแถว Price List Template มี endpoint เฉพาะเพิ่มเติมหนึ่งตัวคือ `PATCH :id/status` แต่มันทำเพียงเขียนค่า status เปล่า ๆ โดยไม่มีการ validate ใด ๆ ไม่มี action แยกสำหรับ "submit," "approve," หรือ "reject" บน resource เหล่านี้เลย — `status` เป็นเพียงฟิลด์ที่ฟอร์มแก้ไขสามารถตั้งค่าได้ กำกับด้วย permission เดียวกันกับที่กำกับส่วนที่เหลือของ record

หน้าเวอร์ชันก่อนหน้าสังเคราะห์กติกาส่วนใหญ่จาก `../carmen/docs/vendor-pricelist-management/` (`design.md`, `requirements.md`, `price-assignment-workflow-documentation.md`) และถือว่ากลไก 6-phase campaign/quality-score/threshold/RBAC ส่วนใหญ่ของเอกสารออกแบบนั้นถูก implement แล้ว การอ่าน `price-list.service.ts`, `price-list-template.service.ts`, `request-for-pricing.service.ts` และ `check-price-list.service.ts` โดยตรงอีกครั้ง (รอบนี้) แสดงว่ากลไกเหล่านั้นไม่มีอยู่จริง กติกาด้านล่างถูก re-anchor ให้ตรงกับสิ่งที่โค้ดทำจริง; การอ้างอิง carmen/docs ถูกเก็บไว้เฉพาะที่อธิบายสิ่งที่ยังไม่ถูก implement และถูก label เป็น **Design-target** ตามนั้น

## 2. กติกาการ Validate

| Rule ID | Tier | เงื่อนไข | Status | หลักฐาน |
| ------- | ---- | --------- | ------ | -------- |
| `VPL_VAL_001` | Template | `tb_pricelist_template.name` ไม่ว่างและ unique ในแถวที่ไม่ถูก soft-delete | **Confirmed** (DB) | `@@unique([name, deleted_at])` (`pricelist_template_name_deletedat_u`); ไม่พบการตรวจสอบล่วงหน้าระดับแอปแยกต่างหาก ดังนั้นสัญญาณแรกที่ผู้เรียกเห็นเมื่อชื่อซ้ำคือการละเมิด constraint ของ DB |
| `VPL_VAL_002` | Template | Activate (`draft → active`) ต้องมีแถว `tb_pricelist_template_detail` อย่างน้อย 1 แถว; re-activate ต้องการให้สินค้าที่อ้างอิงทั้งหมดยัง active | **Design-target** | `pricelist-templates.service.ts` ใน `updateStatus()` ตั้งค่า `status` โดยตรง ไม่มีการตรวจนับแถวหรือตรวจความถูกต้องของสินค้าใด ๆ |
| `VPL_VAL_003` | Template | `currency_id` อ้างอิงแถว `tb_currency` ที่ไม่ถูก soft-delete เมื่อตั้งค่า | **Confirmed (DB FK)** | `currency_id → tb_currency.id`; ไม่มีข้อความระดับแอปที่ชัดเจนนอกเหนือจากการ fail ของ FK |
| `VPL_VAL_004` | Template | `validity_period > 0`; `reminder_days` ลดลงอย่างเข้มงวด | **Design-target** | ไม่มีการตรวจสอบเช่นนี้ในเส้นทาง create/update ของ `price-list-template.service.ts`; `reminder_days` ถูกเก็บเป็น `Json` แบบ opaque |
| `VPL_VAL_005` | Template | `tb_pricelist_template_detail.product_id` อ้างอิงสินค้าที่ active; unique ต่อ `(template, product)` | **Confirmed (uniqueness only)** | `@@unique([pricelist_template_id, product_id, deleted_at])` มีอยู่จริง; "สินค้าต้อง active" ไม่ถูกตรวจสอบแยกต่างหาก |
| `VPL_VAL_006` | Template | `order_unit_obj` carry `default_order` + MOQ tier อย่างน้อย 1 รายการที่ `qty > 0` เพิ่มขึ้นอย่างเข้มงวดข้าม tier | **Design-target** | `order_unit_obj` ถูกเก็บเป็น JSON blob แบบ opaque (`Json? @default("{}")`); ไม่มี service หรือ frontend schema ใด validate โครงสร้างภายในของมัน |
| `VPL_VAL_007` | Template | `escalation_after_days >= 0` | **Design-target** | ไม่พบการตรวจสอบเช่นนี้ |
| `VPL_VAL_008` | RFQ | `tb_request_for_pricing.name` ไม่ว่างและ unique ในแถวที่ไม่ถูก soft-delete | **Confirmed** (DB) | `@@unique([name, deleted_at])` (`request_for_pricing_name_u`) |
| `VPL_VAL_009` | RFQ | `pricelist_template_id` อ้างอิง template ที่ `status = active` | **Design-target (partial)** | `request-for-pricing.service.ts` ใน `create()` ตรวจสอบว่า template **มีอยู่จริง** เท่านั้น ไม่ได้ตรวจว่า `status` เป็น `active` |
| `VPL_VAL_010` | RFQ | `start_date < end_date`; ทั้งสอง window ต้องถูกต้อง; response window ขั้นต่ำของ tenant (design: 3 วัน) | **Confirmed (partial)** | `create()` reject `startDate > endDate` อย่างชัดเจน (`RFP_INVALID_DATE_RANGE`); ไม่มีการตรวจสอบ "window ขั้นต่ำ" แยกต่างหาก |
| `VPL_VAL_011` | RFQ | ต้องมีผู้ขายที่เชิญอย่างน้อย 1 รายพร้อม contact email ที่ถูกต้องก่อน "launch" | **Design-target** | ไม่มีขั้นตอน launch แยกต่างหาก — `create()` รับ array `vendors.add` ที่มีความยาวเท่าใดก็ได้ รวมถึงศูนย์ ในการเรียกเดียวกันกับที่สร้าง RFQ header; ไม่มีสิ่งใดบล็อก RFQ ที่ไม่มี vendor เลย |
| `VPL_VAL_012` | RFQ | Vendor เดียวกันไม่สามารถถูกเชิญสองครั้ง | **Confirmed** (DB) | `@@unique([request_for_pricing_id, vendor_id, deleted_at])` |
| `VPL_VAL_013` | RFQ | `email_template_id` ต้องอ้างอิง email template ของ tenant ที่ถูกต้องและไม่ archive | **Design-target** | `email_template_id` ถูกเก็บเป็น `String?` แบบอิสระ; ไม่พบการ lookup หรือ validate เทียบกับ email-template registry ใด ๆ |
| `VPL_VAL_014` | Pricelist | `pricelist_no` ไม่ว่างและ unique ในแถวที่ไม่ถูก soft-delete | **Confirmed** (DB + app) | `@@unique([pricelist_no, deleted_at])`; `generatePLNo()` derive เลขรันถัดไปจาก running-code pattern ของ tenant |
| `VPL_VAL_015` | Pricelist | `vendor_id` / `currency_id` จำเป็นและอ้างอิงแถว master-data ที่ active | **Confirmed (existence only)** | `create()` lookup vendor/currency ตาม id เพื่อ snapshot ชื่อ/รหัส; ไม่พบ gate "ต้อง active" ที่ชัดเจน |
| `VPL_VAL_016` | Pricelist | `effective_from_date < effective_to_date`; ไม่มีวันใดอยู่ในอดีตตอน create | **Confirmed** | `create()` ตรวจสอบ `effective_from_date < now()`, `effective_to_date < now()` และ `effective_from_date > effective_to_date` อย่างชัดเจน แต่ละตัวมี entry `ERROR_CATALOG` ของตัวเอง |
| `VPL_VAL_017` | Pricelist | `submission_method ∈ {online, email, portal, manual}` | **Confirmed** (Prisma enum) | `pricelist_submission_method` |
| `VPL_VAL_018` | Pricelist | แต่ละแถว detail's `product_id` อ้างอิงสินค้าที่ active ซึ่งปรากฏอยู่บน template ที่ออก | **Design-target** | `create()`/`update()` lookup สินค้าเพียงเพื่อ snapshot ชื่อ/รหัส/SKU เท่านั้น; ไม่มีการตรวจสอบว่าสินค้าเป็นของ template ใด |
| `VPL_VAL_019` | Pricelist | `moq_qty >= 0`; ไม่มี `(product, unit, moq_qty)` ซ้ำต่อ pricelist | **Confirmed (uniqueness only)** | `@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])`; ขอบเขต `>= 0` บังคับใช้ฝั่ง client (Zod `min(0)` ใน `pl-form-schema.ts`) แต่ไม่ถูกตรวจซ้ำฝั่ง server |
| `VPL_VAL_020` | Pricelist | แถว MOQ-tier หลายแถวของสินค้าเดียวกันต้องมีราคาไม่เพิ่มขึ้นเมื่อ `moq_qty` เพิ่มขึ้น | **Design-target** | ไม่มีการ sort-and-compare check อยู่ที่ใดเลย — ทั้งใน `price-list.service.ts` และในฟอร์มฝั่ง frontend Vendor หรือ purchaser สามารถ save การตั้งราคา MOQ แบบเพิ่มขึ้นได้โดยไม่มีคำเตือนหรือการ reject ใด ๆ |
| `VPL_VAL_021` | Pricelist | `tax_amt = Round(price_without_tax × tax_rate, 5)`; `price = Round(price_without_tax + tax_amt, 5)` | **Confirmed (client-side only)** | `pl-form-schema.ts` derive `tax_amt`/`price` จาก `price_without_tax` และ `tax_rate` ก่อน submit; backend persist ค่าใดก็ตามที่ได้รับโดยไม่มีการคำนวณซ้ำหรือตรวจสอบ reconciliation ฝั่ง server |
| `VPL_VAL_022` | Pricelist | `lead_time_days >= 0`; `rating` อยู่ในช่วง 0–5 ที่ตั้งค่าได้ | **Confirmed (client-side only)** | บังคับใช้โดย Zod schema ฝั่ง frontend; ไม่ถูกตรวจซ้ำฝั่ง server |
| `VPL_VAL_023` | Pricelist | Submit ต้องมีแถว detail ที่ถูกต้องอย่างน้อย 1 แถว | **N/A** | ไม่มี action "submit" แยกต่างหากบนหน้าจอ Price List ภายใน; `status` เป็นเพียงค่าที่ฟอร์มแก้ไขส่งมา (การเรียก `submit` ของ external vendor-portal มีอยู่ในฝั่ง frontend แต่ชี้ไปยัง backend route ที่ไม่มีอยู่จริง — ดู [03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor)) |
| `VPL_VAL_024` | Pricelist | การเปลี่ยนสถานะต้องเป็นไปตาม state machine ที่ตายตัว; การเปลี่ยน out-of-order ถูกบล็อก | **Design-target** | ไม่มี transition guard อยู่จริง — `update()` เขียนค่า `status` ใดก็ตามที่ผู้เรียกส่งมา ในทิศทางใดก็ได้ |
| `VPL_VAL_025` | Pricelist | pricelist ที่ `active` ต้อง immutable ยกเว้น `status` | **Design-target** | `update()` ไม่มี branch ตาม status — แถว detail สามารถเพิ่ม/แก้/ลบบน pricelist ที่ `active` ได้เหมือนกับบน `draft` ทุกประการ |

## 3. กติกาการคำนวณ

ค่าเงินทั้งหมดเก็บเป็น `Decimal(20, 5)` ที่ระดับแถว; อัตราภาษีใช้ `Decimal(15, 5)`

| Rule ID | สูตร | Status |
| ------- | ------- | ------ |
| `VPL_CALC_001` (จำนวนภาษีบรรทัด) | `tax_amt = Round(price_without_tax × tax_rate, 5)` | **Confirmed (client-side)** — คำนวณใน `pl-form-schema.ts` ก่อน submit; backend ไม่คำนวณซ้ำ |
| `VPL_CALC_002` (ราคาบรรทัดรวมภาษี) | `price = Round(price_without_tax + tax_amt, 5)` | **Confirmed (client-side)** — ข้อจำกัดเดียวกัน |
| `VPL_CALC_003` (effective unit price ต่อ UoM ฐาน) | `effective_unit_price = price ÷ unit.conversion_factor_to_base` | **Design-target** — ไม่มีโค้ดใดคำนวณหรือแสดงผลค่านี้; `tb_pricelist_detail` ไม่มีคอลัมน์ conversion-factor และ frontend ไม่เคย resolve ค่านี้ |
| `VPL_CALC_004` (การเลือกแถว preferred) | สำหรับ tuple `(product_id, currency_id, due_date)`, `GET .../pricelists/price-compare` return แถว `tb_pricelist_detail` ที่ตรงกันข้าม vendor ทั้งหมด sorted `is_preferred desc, price asc`; แถวแรกคือ `selected` ที่เหลือคือ `lists` | **Confirmed** — endpoint จริง (`PriceListService.priceCompare`) ใช้โดย dialog การตั้งราคา/เปรียบเทียบปลายน้ำ |
| `VPL_CALC_005` (การแสดงผล multi-currency) | ค่า Pricelist เก็บใน `tb_pricelist.currency_id`; ไม่มี FX conversion ถูกใช้หรือเก็บที่ใดในโมดูลนี้ | **Confirmed (by absence)** — ไม่มีการ lookup FX-rate ใน `price-list.service.ts`; การแปลงข้ามสกุลเงินใด ๆ เป็นเรื่องของโมดูลปลายน้ำ ไม่ใช่สิ่งที่โมดูลนี้ทำ |
| `VPL_CALC_006` (quality score) | *(สูตรที่เคยบันทึกไว้ก่อนหน้า)* | **Removed — no code.** การค้นหาทั้ง repo สำหรับ `quality_score`/`qualityScore` ไม่พบผลลัพธ์ใด ๆ ในโมดูลนี้ |

### 3.1 ตัวอย่างที่ทำงาน — การตั้งราคา multi-MOQ บนสินค้าหนึ่ง

Vendor `V1` submit pricelist สำหรับสินค้า `P1` (`unit = Each`) ที่สาม MOQ tier ใน `currency_id = THB`, `tax_rate = 0.07000`:

- Tier 1: `moq_qty = 1`, `price_without_tax = ฿12.50` → `tax_amt = ฿0.87500` → `price = ฿13.37500` (คำนวณฝั่ง client ตาม `VPL_CALC_001`/`VPL_CALC_002`)
- Tier 2: `moq_qty = 50`, `price_without_tax = ฿10.50` → `tax_amt = ฿0.73500` → `price = ฿11.23500`
- Tier 3: `moq_qty = 100`, `price_without_tax = ฿9.75` → `tax_amt = ฿0.68250` → `price = ฿10.43250`

ราคาทั้งสามนี้บังเอิญไม่เพิ่มขึ้นเมื่อ `moq_qty` สูงขึ้น ซึ่งตรงกับเจตนาเบื้องหลัง `VPL_VAL_020` — แต่ไม่มีโค้ดปัจจุบันใดตรวจสอบหรือบังคับใช้ลำดับนั้น Vendor (หรือ purchaser ที่พิมพ์ตรงเข้าไปในฟอร์ม Price List) สามารถ save Tier 3 ที่ `฿15.00` และ record จะถูก save โดยไม่มีคำเตือนใด ๆ

## 4. กติกา Authorization

Authorization ในโมดูลนี้หยาบ (coarse): **Vendor** (หน้าจอ CRUD ซึ่งแยกจาก persona Vendor ของ external portal), **Price List**, **Price List Template** และ **Request for Pricing** แต่ละตัว gate ด้วย permission ระดับโมดูลของตัวเอง — ไม่มีการแยก create-vs-edit-vs-approve, ไม่มี threshold high-value เฉพาะ Manager และไม่มีการตรวจสอบ segregation-of-duties ที่ใดในโค้ดเลย

| ข้อกล่าวอ้างใน draft ก่อนหน้า | Status | หลักฐาน |
| --- | --- | --- |
| Purchasing Manager approve pricelist ที่เกิน "high-value threshold" ของ tenant; Purchaser ถูกจำกัดไว้ต่ำกว่านั้น | **Design-target — removed.** | การค้นหาทั้ง repo สำหรับ `threshold` ในโมดูลนี้ไม่พบผลลัพธ์ที่เกี่ยวข้องเลย (สอดคล้องกับข้อค้นพบที่ยืนยันแล้วในโมดูล `purchase-order`) ไม่มี endpoint approve แยกต่างหากให้ gate ตั้งแต่แรก — `status` ถูกตั้งค่าผ่าน `PATCH` ธรรมดา |
| ต้องมี Finance Manager co-signoff เพื่อ activate pricelist multi-currency | **Design-target — removed.** | ไม่มี persona Finance หรือกลไก co-signoff ใดอยู่จริง — ดู [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) |
| Session ของ vendor portal ถูก gate ด้วยการหมดอายุ token, IP allowlist และขีดจำกัด concurrent-session (default 5) | **Design-target — removed.** | `check-price-list.service.ts` ใน `checkPriceList()` lookup แถว invitation ตาม id แล้ว return/สร้าง pricelist; มันไม่เคยตรวจสอบ `end_date`, IP address หรือจำนวน session เลย |
| การแยกหน้าที่ (segregation of duties): ผู้ถือ vendor-token ≠ user ที่ approve; ผู้แก้ high-value ≠ ผู้ approve | **Design-target — removed.** | ไม่มี cross-check เช่นนี้อยู่ใน service ใดในโมดูลนี้เลย |
| System Administrator สามารถ revoke portal token ของ vendor | **Design-target — removed.** | ไม่มี endpoint ใดตั้งค่า `pricelist_url_token` กลับเป็น `NULL` ที่ใดในฝั่ง backend; token ถูกเขียนเพียงครั้งเดียวตอน RFQ-create และไม่ถูกแตะต้องอีกเลยโดย code path ใดที่พบ |
| Purchaser upload pricelist ที่ส่งทาง email ด้วยตนเองในนามของ vendor | **Confirmed (mechanism), unconfirmed (label)** | `submission_method = email` เป็นฟิลด์จริงที่ตั้งค่าได้บน `tb_pricelist`; Purchaser สามารถสร้าง/แก้ pricelist ด้วยค่านั้นได้โดยตรง ไม่มีหน้าจอ "upload ในนาม vendor" แยกต่างหากจากฟอร์ม create/edit ปกติของ Price List |
| Auditor มีสิทธิ์อ่านอย่างเดียวข้าม pricelist/campaign/invitation/validation results/activity log | **Partially true, overstated** | User ใดก็ตามที่มีสิทธิ์ view สามารถอ่านสี่หน้าจอ list/detail ได้; ไม่มี role Auditor เฉพาะ, ไม่มี query-builder workspace หรือ surface "validation results" (ไม่มีผล validation ให้แสดงตั้งแต่แรก) ดู [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) |

## 5. กติกา Status

### 5.1 Price List Template (`enum_pricelist_template_status`: `draft`, `active`, `inactive`)

`updateStatus()` เป็น endpoint เฉพาะที่มีอยู่จริง (`PATCH :id/status`) แต่ทำ **ไม่มีการ validate ใด ๆ** — ผู้เรียกที่ authenticated แล้วซึ่งมี permission ของ endpoint นี้สามารถย้าย status ไปทิศทางใดก็ได้ เมื่อใดก็ได้ ไม่ว่า template จะมีแถวสินค้าหรือไม่ ไม่มี cron, ไม่มี gate การ re-activation และไม่มี comment ใดถูกเขียนตอนเปลี่ยน transition

### 5.2 Request for Pricing (ไม่มีคอลัมน์ status)

`tb_request_for_pricing` ไม่มีฟิลด์ status และไม่มีโค้ดแอปใด derive ค่านี้ สัญญาณต่อ vendor เดียวที่ UI อ่านคือ `has_submitted: !!pricelist_id` บนแต่ละแถว invitation (`request-for-pricings.service.ts` ใน `findAll()`) ไม่มีการ derive `draft`/`active`/`paused`/`completed`/`cancelled` ที่ใดเลย — ทั้ง section "campaign lifecycle" ใน draft ก่อนหน้าอธิบาย state machine ที่ไม่มีโค้ดรองรับเลยและถูกลบออกแล้ว RFQ ที่ "cancelled" เป็นเพียงแถวที่ soft-delete (`remove()`)

### 5.3 Price List (`enum_pricelist_status`: `draft`, `active`, `inactive`, `expired`)

`create()`/`update()` ตั้งค่า `status` เป็นค่าใดก็ตามที่ผู้เรียกส่งมา; ไม่มี action approve/reject/submit/activate แยกต่างหาก ไม่มี transition guard และไม่มี cron auto-expire ใน repo นี้ (`micro-cronjobs` ไม่มี job ที่ตรงกัน) `remove()` (soft-delete) ยังบังคับ `status = inactive` เพิ่มเติม แถว detail สามารถเพิ่ม แก้ หรือลบได้ไม่ว่า `status` ปัจจุบันของ header จะเป็นอะไร รวมถึง `active`

### 5.4 External vendor portal (ช่องว่างที่ยืนยันแล้ว)

`POST /api/check-pricelist/:url_token` (endpoint backend จริงเดียวสำหรับ portal) auto-create draft pricelist ที่ราคาศูนย์จาก template ของ invitation ในการเยี่ยมชมครั้งแรก หรือ return ตัวที่มีอยู่แล้ว Frontend ยัง wire `PATCH /api/pricelist-external/:token` (save) และ `POST /api/pricelist-external/:token/submit` (submit) ผ่าน `hooks/use-price-list-external.ts` แต่ **ไม่มี backend route ที่ตรงกับ `pricelist-external` อยู่ที่ใดใน `carmen-turborepo-backend-v2` เลย** — ยืนยันโดยการค้นหาทั้ง repo ที่ไม่พบผลลัพธ์ใดนอกเหนือจากไฟล์ endpoint-constant ของ frontend เอง ในโค้ดปัจจุบัน vendor portal ทำได้เพียงดูอย่างเดียว; การแก้ไขและ submission ไม่ persist ผ่านมันได้ ดู [03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor) สำหรับรายละเอียดเต็ม

## 6. กติกาข้ามโมดูล

| Rule ID | โมดูลที่เกี่ยวข้อง | กติกา | Status |
| ------- | -------------- | ---- | ------ |
| `VPL_XMOD_001` | [purchase-request](/th/inventory/purchase-request) | การตั้งราคาบรรทัด PR สามารถ source จากแถว `selected` ของ `price-compare` สำหรับ product/currency/date ของบรรทัดนั้น | **Confirmed (mechanism)** — ผ่าน endpoint `price-compare` จริง; ส่วนที่ว่า UI ของโมดูล PR เรียกใช้จริงหรือไม่สำหรับทุกบรรทัด ถูกบันทึกไว้ในรอบตรวจสอบของโมดูล `purchase-request` เอง ไม่ได้ตรวจซ้ำที่นี่ |
| `VPL_XMOD_002` | [purchase-request](/th/inventory/purchase-request) | เมื่อไม่มี pricelist active ครอบคลุมสินค้า บรรทัด PR ถูกจับด้วย `pricelist_type = manual_input` (`enum_pricelist_compare_type`) | **Confirmed (schema)** — enum และฟิลด์บรรทัด PR มีอยู่จริง; บันทึกไว้ในโมดูล `purchase-request` |
| `VPL_XMOD_003` | [purchase-order](/th/inventory/purchase-order) | การ convert PO snapshot ราคา ณ จุดที่ convert PR-to-PO แทนที่จะถือ FK สด | **Confirmed** — ตรงกับข้อค้นพบที่บันทึกไว้แล้วของโมดูล PO; ไม่มีการอ่าน pricelist สดซ้ำหลัง conversion |
| `VPL_XMOD_004` | [purchase-order](/th/inventory/purchase-order) | บรรทัด PO ที่เบี่ยงเบนจาก pricelist active เกิน tolerance ของ tenant route ไปยัง stage approve "high-value" | **Design-target — removed.** รอบ resync ของโมดูล PO เองยืนยันแล้วว่าไม่พบ `threshold` สำหรับกลไกนี้เลย (`PO_AUTH_004`/`PO_XMOD_006`) |
| `VPL_XMOD_005` | [good-receive-note](/th/inventory/good-receive-note) | การ post GRN สามารถเปรียบเทียบราคาต่อหน่วยกับ pricelist active และ flag variance | **Unconfirmed here** — อ่านข้อกล่าวอ้างของโมดูลนี้ร่วมกับข้อค้นพบ resync ของโมดูล GRN เอง รอบนี้ไม่ได้ตรวจสอบโค้ดฝั่ง GRN ซ้ำ |
| `VPL_XMOD_006` | [product](/th/inventory/product) | ทุก `tb_pricelist_detail.product_id` อ้างอิง `tb_product`; แถว pricelist ที่มีอยู่ของสินค้าที่ soft-delete แล้วยัง queryable ได้ | **Confirmed (schema)** — `onDelete: NoAction`, รูปแบบ soft-delete สอดคล้องกับส่วนที่เหลือของ schema |
| `VPL_XMOD_007` | Vendor | Vendor ที่ inactive ไม่ควรถูกเชิญไปยัง RFQ ใหม่หรือมี pricelist ใหม่ถูกสร้าง | **Design-target** — ไม่พบการตรวจสอบ `is_active` ของ vendor ใน `request-for-pricing.service.ts` `create()` หรือ `price-list.service.ts` `create()` |
| `VPL_XMOD_008` | Currency master | ค่า Pricelist เก็บในสกุลเงินที่เลือกไว้; การเปรียบเทียบข้ามสกุลเงิน ถ้าจำเป็น เป็นเรื่องของโมดูลปลายน้ำ | **Confirmed (by absence)** — ดู `VPL_CALC_005` |
| `VPL_XMOD_009` | Validation engine | Engine ตรวจสอบรูปแบบ/ความสมบูรณ์/business-rule/quality-scoring validate ทุก submission | **Removed — no code.** ดู § 2 และ § 3 ข้างต้น; สิ่งที่ใกล้เคียงที่สุดที่มีจริงคือ Zod field validation ธรรมดาบนฟอร์มฝั่ง frontend |

## 7. แหล่งอ้างอิง

- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/` (vendor, price-list, price-list-template, request-price-list) และ `routes/external/pl/` (vendor portal)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/master/price-list/price-list.service.ts`, `.../price-list-template/price-list-template.service.ts`, `.../request-for-pricing/request-for-pricing.service.ts`, `.../check-price-list/check-price-list.service.ts`; gateway controller ภายใต้ `apps/backend-gateway/src/application/pricelists/`, `pricelist-templates/`, `request-for-pricings/`
- Prisma: `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`tb_pricelist*`, `tb_pricelist_template*`, `tb_request_for_pricing*`)
- `../carmen/docs/vendor-pricelist-management/` — เก็บไว้เป็นแหล่งที่มาสำหรับทุกกติกาที่ label ว่า **Design-target**; ถือว่าเป็น aspirational spec ไม่ใช่คำอธิบายพฤติกรรมปัจจุบัน
- E2E: `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts`, `159-pl.spec.ts`, `160-pl-template.spec.ts`
- Sibling: [01-data-model.md](./01-data-model.md) — โมเดล Prisma canonical และตาราง divergence § 5 ที่ label สถานะของหน้านี้อ้างอิงมา
- โมดูลที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request) (`VPL_XMOD_001`–`VPL_XMOD_002`), [purchase-order](/th/inventory/purchase-order) (`VPL_XMOD_003`–`VPL_XMOD_004`), [good-receive-note](/th/inventory/good-receive-note) (`VPL_XMOD_005`), [product](/th/inventory/product) (`VPL_XMOD_006`)
