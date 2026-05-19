---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Business Rules
description: การ validate, การคำนวณ, authorization, การเปลี่ยนสถานะ และกติกาข้ามโมดูลสำหรับ vendor-pricelist
published: true
date: 2026-05-17T12:00:00.000Z
tags: vendor-pricelist, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Business Rules

> **At a Glance**
> **กลุ่มกติกา:** `VPL_VAL_*` validation &nbsp;·&nbsp; `VPL_AUTH_*` permission &nbsp;·&nbsp; `VPL_CALC_*` calc &nbsp;·&nbsp; `VPL_POST_*` posting &nbsp;·&nbsp; `VPL_XMOD_*` cross-module
> **จำนวนกติกา:** ประมาณ 81 กติกา
> **กลุ่มผู้ใช้:** Test author + developer — ทุก rule ID anchor จากหน้า `04-test-scenarios*`
> **Status lifecycle:** Section 5.1 (เมื่อมี) carry callout ความแตกต่าง Live UI vs BRD

## 1. ภาพรวม

หน้านี้จับกติกาทางธุรกิจเชิงปฏิบัติการที่กำกับสาม tier ของโมดูล vendor-pricelist — **template** (`tb_pricelist_template`), **request-for-pricing campaign** (`tb_request_for_pricing`) และ **vendor pricelist** (`tb_pricelist`) — ผ่าน lifecycle ของแต่ละ กลุ่มกติกาคือ: การ validate input ที่เวลา create / edit / submit, การ validate MOQ-tier ข้ามหลายแถวต่อสินค้า, การคำนวณเงิน (การแยกราคาระดับบรรทัด; effective unit price ต่อ UoM ฐาน; การแสดงผล multi-currency), authorization gate ตาม role (Purchaser / Manager / Vendor / Finance / Sysadmin / Auditor), การเปลี่ยนสถานะบน `enum_pricelist_template_status` และ `enum_pricelist_status`, นโยบาย portal-token (การหมดอายุ, IP, session), semantic ของ validation-engine (รูปแบบ, ความสมบูรณ์, business rule, quality score) และกติกาข้ามโมดูลกับ [[purchase-request]] (การ default ราคาจาก pricelist ของ preferred vendor), [[purchase-order]] (snapshot ราคา + การติดตาม deviation), [[good-receive-note]] (price-variance check) และ [[product]] (อ้างอิงจากทุกแถว detail)

กติกาด้านล่างสังเคราะห์จากเอกสาร vendor-pricelist ของ carmen/docs (`design.md`, `requirements.md`, `price-assignment-workflow-documentation.md`, `VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md`, `VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md`) และโมเดลข้อมูล Prisma canonical ใน [[vendor-pricelist/01-data-model]] ที่ carmen/docs และ Prisma ไม่ตรงกัน **Prisma เป็น canonical สำหรับเอนทิตี, ฟิลด์ และค่า enum**; carmen/docs เป็น canonical สำหรับ semantic ของ workflow, คำอธิบายกติกา และนโยบายที่ชั้นแอปบังคับใช้บน Prisma schema ที่ slim กว่า — โดยเฉพาะ campaign status (`draft` / `active` / `paused` / `completed` / `cancelled`) และ invitation submission status (`pending` / `in-progress` / `submitted` / `approved` / `expired`) เป็น derivation ระดับแอปเพราะ Prisma ไม่มีคอลัมน์ dedicated สำหรับมัน ([[vendor-pricelist/01-data-model]] § 5 ทำแคตตาล็อก divergence material 12 รายการ)

## 2. กติกาการ Validate

Rule ID ตาม `VPL_VAL_NNN` กติกา template (001–007) รันบนเส้นทาง create / edit / activate template; กติกา campaign (008–013) บน create / send-invitation request-for-pricing; กติกา pricelist (014–025) บน submission ของ vendor / การ approve ของ purchaser ที่ index Prisma `@@unique` เป็น guard สุดท้าย ข้อความ validation ถูกส่งที่ชั้นแอปโดยมี index DB เป็น fallback

| Rule ID | Tier | เงื่อนไข | บังคับใช้เมื่อ | Error / behavior |
| ------- | ---- | --------- | ------------- | ----------------- |
| `VPL_VAL_001` | Template | `tb_pricelist_template.name` ไม่ว่างและ unique ในแถวที่ไม่ถูก soft-delete (`@@unique([name, deleted_at])`) | Create, edit, activate | Reject ด้วย "Template name is required and must be unique." Fallback ระดับ DB ผ่าน unique index `pricelist_template_name_deletedat_u` |
| `VPL_VAL_002` | Template | `tb_pricelist_template.status ∈ enum_pricelist_template_status (draft, active, inactive)` Activate transition (`draft → active`) ต้องมีแถว `tb_pricelist_template_detail` อย่างน้อยหนึ่ง | Activate | Reject ด้วย "Template must contain at least one product before it can be activated." |
| `VPL_VAL_003` | Template | `tb_pricelist_template.currency_id` อ้างอิงแถว `tb_currency` ที่ไม่ถูก soft-delete เมื่อตั้งค่า | Save | Reject ด้วย "Default currency must be a valid, active currency." Currency บน template เป็น default — ผู้ขายอาจเลือกสกุลเงิน submission อื่นบน pricelist เอง |
| `VPL_VAL_004` | Template | `tb_pricelist_template.validity_period > 0` เมื่อตั้ง; ค่า days-to-deadline ใน `reminder_days` เป็นบวกและลดลงอย่างเข้มงวด (เช่น `[14, 7, 3, 1]`) | Save | Reject ด้วย "Validity period must be positive and reminder schedule must be strictly decreasing." |
| `VPL_VAL_005` | Template | `tb_pricelist_template_detail.product_id` แต่ละตัวอ้างอิง `tb_product` ที่ active และไม่ถูก soft-delete; `@@unique([pricelist_template_id, product_id, deleted_at])` ป้องกันสินค้าซ้ำบน template เดียวกัน | Save line | Reject ด้วย "Product is required and may only appear once per template." Fallback DB ผ่าน unique index |
| `VPL_VAL_006` | Template | `tb_pricelist_template_detail.order_unit_obj` carry object `default_order` และ MOQ tier อย่างน้อยหนึ่ง; แต่ละ MOQ tier มี `unit_id`, `unit_name` และ `qty > 0`; ค่า MOQ `qty` เพิ่มขึ้นอย่างเข้มงวดข้าม tier (auto-sort ตอน save) | Save line | Reject ด้วย "Order unit and at least one MOQ tier with positive quantity are required; MOQ quantities must be strictly increasing." |
| `VPL_VAL_007` | Template | `tb_pricelist_template.escalation_after_days >= 0` ไม่สามารถ escalate ก่อน deadline | Save | Reject ด้วย "Escalation days must be non-negative." |
| `VPL_VAL_008` | Campaign | `tb_request_for_pricing.name` ไม่ว่างและ unique ในแถวที่ไม่ถูก soft-delete (`@@unique([name, deleted_at])`) | Create, edit | Reject ด้วย "Campaign name is required and must be unique." |
| `VPL_VAL_009` | Campaign | `tb_request_for_pricing.pricelist_template_id` อ้างอิง `tb_pricelist_template` ที่ `status = active` | Create | Reject ด้วย "Campaign must reference an active template — draft or inactive templates cannot drive campaigns." |
| `VPL_VAL_010` | Campaign | `tb_request_for_pricing.start_date < end_date`; `end_date > now()` ที่ launch campaign; `start_date` และ `end_date` ครอบคลุมอย่างน้อย response window ขั้นต่ำของ tenant (default 3 วัน, ตั้งค่าได้) | Create, launch | Reject ด้วย "Campaign window must run for at least the tenant minimum (default 3 days) and end strictly after start; end_date must be in the future at launch." |
| `VPL_VAL_011` | Campaign | มีแถว `tb_request_for_pricing_detail` อย่างน้อยหนึ่งก่อน launch campaign; แต่ละแถว detail มี `vendor_id` ที่ไม่ null และ `contact_email` (snapshot-or-master) ที่เป็น email ที่ถูก syntactic | Launch | Reject ด้วย "Campaign must invite at least one vendor and every invited vendor must have a contact email." |
| `VPL_VAL_012` | Campaign | `tb_request_for_pricing_detail.@@unique([request_for_pricing_id, vendor_id, deleted_at])` ป้องกันการเชิญผู้ขายเดียวกันสองครั้ง | Add vendor | Reject ด้วย "Vendor has already been invited to this campaign." Fallback ระดับ DB |
| `VPL_VAL_013` | Campaign | Email-template ที่อ้างอิงโดย `email_template_id` มีอยู่ใน tenant email-template registry และไม่ archive | Launch | Reject ด้วย "Email template not found or archived — pick a valid template before launch." |
| `VPL_VAL_014` | Pricelist | `tb_pricelist.pricelist_no` ไม่ว่างและ unique ในแถวที่ไม่ถูก soft-delete (`@@unique([pricelist_no, deleted_at])`) | Create | Reject ด้วย "Pricelist reference number is required and must be unique." Fallback DB ผ่าน index `pricelist_pricelist_no_u` |
| `VPL_VAL_015` | Pricelist | `tb_pricelist.vendor_id` อ้างอิง `tb_vendor` ที่ active และไม่ถูก soft-delete; `tb_pricelist.currency_id` อ้างอิง `tb_currency` ที่ไม่ถูก soft-delete | Save | Reject ด้วย "Vendor and currency are required and must reference active master-data records." |
| `VPL_VAL_016` | Pricelist | `tb_pricelist.effective_from_date < effective_to_date`; `effective_from_date >= submitted_at` (effective date ไม่สามารถอยู่ในอดีตเทียบกับ submission ยกเว้น template อนุญาตการ back-date อย่างชัดเจน) | Save, submit | Reject ด้วย "Effective-from date must precede effective-to date; effective-from cannot precede submission." |
| `VPL_VAL_017` | Pricelist | `tb_pricelist.submission_method ∈ pricelist_submission_method (online, email, portal, manual)` | Save | Reject ด้วย "Submission method must be one of online, email, portal, or manual." |
| `VPL_VAL_018` | Pricelist | `tb_pricelist_detail.product_id` แต่ละตัวอ้างอิง `tb_product` ที่ active และไม่ถูก soft-delete; สินค้าต้องมีอยู่บน template ที่อ้างอิงโดย campaign ที่ออก invitation (ผู้ขายไม่สามารถเสนอราคาสินค้าที่ไม่ได้ถาม) | Save line | Reject ด้วย "Product is required and must appear on the issuing template." |
| `VPL_VAL_019` | Pricelist | `tb_pricelist_detail.@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])` อนุญาตหลายแถวต่อ `(pricelist, product, unit)` แยกโดย `moq_qty` `moq_qty` ของแต่ละแถว `>= 0` | Save line | Reject ด้วย "MOQ quantity is required and must be non-negative; duplicate (product, unit, MOQ) rows are not permitted." |
| `VPL_VAL_020` | Pricelist | เมื่อสินค้ามีหลายแถว MOQ-tier บน pricelist เดียวกัน (`product_id` + `unit_id` เดียวกัน) แถวถูก auto-sort ตาม `moq_qty` จากน้อยไปมาก และ **ปริมาณที่สูงกว่าต้อง carry ราคาต่อหน่วยที่เท่าหรือต่ำกว่า** (`price` non-increasing เมื่อ `moq_qty` เพิ่มขึ้น) | Save, submit | Warn ที่ save ด้วย "Tier MOQ 50 (฿10.50) is cheaper than MOQ 100 (฿11.00) — please review."; reject ที่ submit ด้วย "MOQ-tier pricing must be non-increasing as MOQ quantity increases." |
| `VPL_VAL_021` | Pricelist | `tb_pricelist_detail.price_without_tax >= 0` (อนุญาต zero แต่ flag สำหรับ review); `tax_rate >= 0`; `tax_amt = Round(price_without_tax × tax_rate, 5)`; `price = Round(price_without_tax + tax_amt, 5)` | Save line | Reject ด้วย "Price-without-tax must be non-negative; tax_amt and price must reconcile to the configured rounding rule (5 dp internal, 2 dp display)." |
| `VPL_VAL_022` | Pricelist | `tb_pricelist_detail.lead_time_days >= 0`; `tb_pricelist_detail.rating ∈ [0, 5]` (ขอบบนตั้งค่าได้ตาม tenant) | Save line | Reject ด้วย "Lead time must be non-negative; rating must be within 0–5." |
| `VPL_VAL_023` | Pricelist | ตอน submit (ผู้ขายคลิก Submit) pricelist มีแถว detail ที่ไม่ถูก soft-delete อย่างน้อยหนึ่ง; ทุกแถว detail ผ่าน `VPL_VAL_018`–`VPL_VAL_022` | Submit | Reject ด้วย "Pricelist must contain at least one valid line item to submit." |
| `VPL_VAL_024` | Pricelist | การเปลี่ยนสถานะตาม state machine ใน § 5; การเปลี่ยน out-of-order ถูกบล็อก | On status change | Reject ด้วย "Invalid status transition from `<from>` to `<to>`." |
| `VPL_VAL_025` | Pricelist | หลัง `tb_pricelist.status = active` header ของ pricelist เป็น immutable ยกเว้น `status` (admin สามารถย้ายไป `inactive`) และ surface comment / activity-log; การแก้ detail row ต้องมี administrative override หรือ pricelist ใหม่ (ออกภายใต้ campaign ใหม่) | Edit on active | Reject ด้วย "Active pricelist is immutable — open a new pricelist via a fresh campaign, or move this pricelist to inactive first." |

## 3. กติกาการคำนวณ

ค่าเงินทั้งหมดเก็บเป็น `Decimal(20, 5)` ที่ระดับแถว; อัตราภาษีใช้ `Decimal(15, 5)` การปัดเศษการแสดงผลเป็น half-up (banker's rounding สำหรับ tie ที่ .5) ไปยัง 2 ทศนิยมสำหรับสกุลเงิน, 3 ทศนิยมสำหรับปริมาณ และ 5 ทศนิยมสำหรับอัตรา การคำนวณ intermediate อ่านค่าที่ปัดเศษของขั้นก่อนหน้าเสมอ

Rule ID ตาม `VPL_CALC_NNN`

| Rule ID | สูตร |
| ------- | ------- |
| `VPL_CALC_001` (จำนวนภาษีบรรทัด) | `tax_amt = Round(price_without_tax × tax_rate, 5)` ต่อ `tb_pricelist_detail` |
| `VPL_CALC_002` (ราคาบรรทัดรวมภาษี) | `price = Round(price_without_tax + tax_amt, 5)` |
| `VPL_CALC_003` (effective unit price ต่อ UoM ฐาน) | สำหรับแถว MOQ-tier ที่ `(unit_id, moq_qty, price)`: `effective_unit_price = Round(price ÷ unit.conversion_factor_to_base, 5)` `conversion_factor_to_base` resolve ที่เวลา lookup จาก `tb_unit` ไม่ได้เก็บบนแถว pricelist การปัดเศษการแสดงผลเป็น 2 dp ตอน render |
| `VPL_CALC_004` (การเปรียบเทียบ tier) | เมื่อสินค้า carry หลายแถว MOQ-tier บน pricelist เดียวกัน แถวถูก sort ตาม `moq_qty` จากน้อยไปมากตอน save; แอป assert `price[i+1] <= price[i]` สำหรับแถวที่ติดกันหลัง sort (`VPL_VAL_020`) สำหรับรายงานเปรียบเทียบข้ามผู้ขาย effective unit price ต่อ UoM ฐาน (`VPL_CALC_003`) เป็นค่าที่เปรียบเทียบได้ |
| `VPL_CALC_005` (การแสดงผล multi-currency) | ค่า pricelist เก็บใน `tb_pricelist.currency_id` (สกุลเงิน submission ที่ vendor เลือก); ไม่มี FX conversion เก็บบนแถว การเปรียบเทียบและรายงานแปลงเป็นสกุลเงินเป้าหมายที่เวลาแสดงผลโดยใช้อัตรา FX ของ tenant ที่ as-of date ของรายงาน — ราคา pricelist ที่เก็บไม่เคย mutate สำหรับ FX |
| `VPL_CALC_006` (quality score — ระดับแอป, เก็บใน `info`) | `quality_score ∈ [0, 100] = w1 × completeness_pct + w2 × business_rule_pass_pct + w3 × format_correctness_pct + w4 × vendor_reliability_score` ด้วย weight ที่ tenant ตั้งได้ (default `0.30 / 0.40 / 0.15 / 0.15`) เก็บเป็น `info.quality_score` บน `tb_pricelist` |
| `VPL_CALC_007` (validity countdown สำหรับการแสดงผล portal) | `days_remaining = floor((effective_to_date − now()) ÷ 1 day)` render บน vendor portal และบน dashboard open-pricelists ของ purchaser |
| `VPL_CALC_008` (โหมดการปัดเศษ) | โหมด Half-up (banker's) สำหรับการปัดเศษทุกเงินและอัตรา; การ format ตัวเลขตามภูมิภาคถูกใช้ที่การ render เท่านั้น ไม่ใช่ที่การเก็บ |

### 3.1 ตัวอย่างที่ทำงาน — การตั้งราคา multi-MOQ บนสินค้าหนึ่ง

Vendor `V1` submit pricelist สำหรับสินค้า `P1` (`unit = Each`, conversion ไปฐาน `Each = 1`) ที่สาม MOQ tier ใน `currency_id = THB`, `tax_rate = 0.07000`:

- Tier 1: `moq_qty = 1`, `unit_id = Each`, `price_without_tax = ฿12.50`
  - `tax_amt = Round(12.50 × 0.07, 5) = ฿0.87500`
  - `price = Round(12.50 + 0.87500, 5) = ฿13.37500`
  - `effective_unit_price_per_base = Round(13.37500 ÷ 1, 5) = ฿13.37500`
- Tier 2: `moq_qty = 50`, `unit_id = Each`, `price_without_tax = ฿10.50`
  - `tax_amt = ฿0.73500`; `price = ฿11.23500`; `effective_unit_price_per_base = ฿11.23500`
- Tier 3: `moq_qty = 100`, `unit_id = Each`, `price_without_tax = ฿9.75`
  - `tax_amt = ฿0.68250`; `price = ฿10.43250`; `effective_unit_price_per_base = ฿10.43250`

Validation `VPL_VAL_020` ผ่าน — `price` ลดลงอย่างเข้มงวดข้ามสาม tier (`13.375 > 11.235 > 10.4325`) ถ้า Tier 3 เสนอราคาที่ `฿11.00` (เหนือ Tier 2) save warn และ submit reject

ถ้า `V1` ยังเสนอสินค้าเดียวกันที่ `unit = Box of 12` (`tb_unit.conversion_factor_to_base = 12`) ที่ `moq_qty = 1`, `price_without_tax = ฿138.00` แล้ว `effective_unit_price_per_base = Round(138.00 ÷ 12, 5) = ฿11.50000` — **เปรียบเทียบได้** กับราคา MOQ-tier `Each` ข้างต้น Schema เก็บแถวในหน่วยที่ vendor เสนอราคา (`Box`); การเปรียบเทียบเกิดผ่าน `VPL_CALC_003`

## 4. กติกา Authorization

Rule ID ตาม `VPL_AUTH_NNN` Authorization บังคับใช้โดย RBAC ที่ชั้น API; กติกาด้านล่างระบุนโยบาย ไม่ใช่การ implement ชื่อ role สะท้อนตาราง RBAC ของ carmen/docs ขีดจำกัด "high-value" หรือ "multi-currency" สำหรับการ approve เฉพาะ Manager ตั้งค่าได้ตาม tenant

| Rule ID | Subject | สิทธิ์ | ข้อจำกัด |
| ------- | ------- | ----- | ---------- |
| `VPL_AUTH_001` | Purchaser / Purchasing Staff | Create / edit / activate / inactivate `tb_pricelist_template` | ทั้ง `status = draft` และ `status = active` สามารถแก้ได้; activate ต้องการ `VPL_VAL_002` |
| `VPL_AUTH_002` | Purchaser | Create / edit / launch `tb_request_for_pricing` (campaign) | Launch ต้องการ `VPL_VAL_009`–`VPL_VAL_013`; เฉพาะผู้สร้าง campaign หรือสมาชิกของ role procurement-team สามารถแก้ campaign mid-flight |
| `VPL_AUTH_003` | Purchaser | Upload manually pricelist ที่ส่งมาทาง email (`tb_pricelist.submission_method = email`) ในนาม vendor | อนุญาต; การ upload เขียน `system` comment บน pricelist บันทึกแหล่ง email, staff ที่ upload และการอ้างอิง email ต้นฉบับ |
| `VPL_AUTH_004` | Purchaser | Review และ approve pricelist ที่ submit (`draft → active`) | ต่ำกว่าขีดจำกัด high-value ของ tenant; pricelist high-value route ไปยัง Purchasing Manager ตาม `VPL_AUTH_005` |
| `VPL_AUTH_005` | Purchasing Manager | Approve pricelist high-value หรือ multi-currency; ตั้งค่า business rule สำหรับ logic preferred-vendor และ price-assignment | ต้องการสำหรับ pricelist ที่เกินขีดจำกัด high-value ของ tenant หรือครอบคลุมข้อตกลงข้ามพรมแดน multi-currency ยังถือ sign-off บนการ toggle preferred-vendor flag (`tb_pricelist_detail.is_preferred`) |
| `VPL_AUTH_006` | Purchasing Manager | Reject pricelist ที่ submit พร้อมเหตุผล | ส่ง pricelist กลับไปยัง vendor (สถานะยังเป็น `draft` พร้อม `system` rejection comment ใน `tb_pricelist_comment`); vendor ได้รับ email พร้อมเหตุผลการ reject และอาจ resubmit ผ่าน portal token เดียวกัน (ถ้ายังไม่หมดอายุ) |
| `VPL_AUTH_007` | Vendor (external) | เข้าถึง portal ผ่าน `pricelist_url_token`; draft, save, resubmit pricelist | Token ต้องไม่หมดอายุ (ไม่เลย `tb_request_for_pricing.end_date` และไม่ถูก revoke); IP ต้องตรงกับ allowlist ที่ตั้งค่าไว้ถ้ามี; บังคับ session limit (default 5 session พร้อมกันต่อ token) |
| `VPL_AUTH_008` | Vendor | เลือกสกุลเงิน submission; จัด MOQ tier พร้อมหน่วยและ conversion factor | สกุลเงินต้องอยู่ในรายการสกุลเงินที่ tenant อนุญาต; conversion factor อ่านจาก master data ของ `tb_unit` ไม่ใช่ vendor-supplied เป็นค่าอิสระ |
| `VPL_AUTH_009` | Finance Officer / Accounts Payable | อ่าน pricelist สำหรับการ audit variance | อ่านอย่างเดียวข้าม pricelist, campaign และ invitation ทั้งหมด; ไม่สามารถแก้หรือเปลี่ยนสถานะ |
| `VPL_AUTH_010` | Finance Manager | Sign off บน pricelist multi-currency หรือ high-value | สิทธิ์ co-approval ข้าง Purchasing Manager เมื่อตั้งค่า; gate การเปลี่ยน `draft → active` สำหรับกรณี multi-currency |
| `VPL_AUTH_011` | Receiver / Store Keeper | ผู้บริโภคทางอ้อม — ไม่มีสิทธิ์เขียนโมดูล | การเข้าถึงอ่านผ่าน variance check ของ [[good-receive-note]]; ไม่สามารถแก้ pricelist |
| `VPL_AUTH_012` | System Administrator | ตั้งค่า scheme การกำหนดเลข pricelist, RBAC, การตั้งค่า template / campaign, นโยบาย portal token (การหมดอายุ, IP restriction, session limit), การเชื่อม email, กติกา validation | ไม่สามารถสร้างหรือ approve pricelist; ไม่สามารถ transact ในโมดูล สามารถ revoke portal token โดยตั้ง `tb_request_for_pricing_detail.pricelist_url_token = NULL` และเขียน `system` comment ซึ่ง invalidate การเข้าถึง portal ของ vendor ทันที |
| `VPL_AUTH_013` | Auditor | อ่านอย่างเดียวข้าม pricelist, campaign, invitation, ประวัติการ submission, ผลการ validate และ activity log | ไม่มี surface เขียน; ไม่สามารถ approve, reject, void หรือ amend การ export ฟิลด์ละเอียดอ่อน (vendor identity เต็ม, pricing snapshot, portal-token telemetry) ต้องการการ approve การ export ทุติยภูมิตามนโยบายการ export ของ tenant |
| `VPL_AUTH_014` | การแยกหน้าที่ | Vendor ≠ Purchaser; Purchaser ≠ Approver (สำหรับ high-value) | user ที่ถือ portal token ของ vendor ไม่สามารถ approve pricelist; user ที่สร้างหรือแก้ pricelist high-value's detail rows อย่างมีนัยสำคัญต้องไม่เป็น user เดียวกันที่ approve มัน บังคับใช้ที่การเปลี่ยนสถานะ |
| `VPL_AUTH_015` | การ revoke token | System Administrator หรือ Purchasing Manager อาจ revoke `pricelist_url_token` | การ revoke เป็นทันที; การเข้า portal ตามมาด้วย token ที่ revoke return `401 — token revoked` การออกใหม่ต้องส่ง invitation ใหม่พร้อม token ใหม่; แถว invitation ต้นฉบับคงไว้สำหรับ audit |

## 5. กติกา Status / Posting

โมดูลมีสาม enum สถานะที่มี lifecycle แยกกัน บวก campaign และ invitation status ที่ derive ระดับแอป

### 5.1 Template lifecycle (`enum_pricelist_template_status`)

State: `draft`, `active`, `inactive` Rule ID `VPL_POST_001`–`VPL_POST_004`

| Rule ID | Transition | ผลกระทบ |
| ------- | ---------- | ------- |
| `VPL_POST_001` | Create (→ `draft`) | Insert `tb_pricelist_template` ด้วย `status = draft`, `doc_version = 0` แถว detail สามารถเพิ่ม / แก้ได้อย่างอิสระ ไม่สามารถขับ campaign ขณะ `draft` |
| `VPL_POST_002` | Activate (`draft → active`) | ต้องการ `VPL_VAL_002`–`VPL_VAL_007` ตั้ง `status = active`; template ตอนนี้เลือกได้เป็นแหล่งสำหรับแถว `tb_request_for_pricing` ใหม่ `system` comment append ใน `tb_pricelist_template_comment` บันทึกการ activate |
| `VPL_POST_003` | Inactivate (`active → inactive`) | ตั้ง `status = inactive` Template ไม่สามารถขับ campaign ใหม่; campaign ที่มีอยู่ดำเนินต่อภายใต้การอ้างอิงที่ snapshot |
| `VPL_POST_004` | Re-activate (`inactive → active`) | อนุญาตเมื่อสินค้าและสกุลเงินที่อ้างอิงของ template ยังถูกต้อง; ถ้าสินค้าใดถูก soft-delete แล้ว activate ถูก reject พร้อมรายการสินค้าที่ได้รับผลกระทบ |

### 5.2 Campaign lifecycle (แอป derive จาก `start_date`, `end_date` และ count pricelist ฝั่ง detail)

ตาม [[vendor-pricelist/01-data-model]] § 5 item 2 มี **คอลัมน์ Prisma ที่ไม่มีสำหรับ campaign status** แอป derive สถานะดังนี้ Rule ID `VPL_POST_005`–`VPL_POST_009`

| Rule ID | State ที่ derive | เงื่อนไข | ผลกระทบ |
| ------- | ------------- | --------- | ------- |
| `VPL_POST_005` | `draft` | `tb_request_for_pricing` มีอยู่ที่ `start_date IS NULL` OR `start_date > now()` และไม่มีแถว detail ที่ dispatch invitation email | Campaign กำลังเตรียม; vendor ยังไม่ถูกติดต่อ; แก้ได้อย่างอิสระ |
| `VPL_POST_006` | `active` | `start_date <= now() < end_date` AND มีแถว detail อย่างน้อยหนึ่งที่ dispatch invitation | Campaign live; vendor สามารถเข้า portal ผ่าน token; reminder fire ตาม schedule ของ template |
| `VPL_POST_007` | `paused` | Flag ที่แอปตั้ง (ใน JSON `info` บน `tb_request_for_pricing`) ระงับ reminder และล็อก invitation ใหม่; portal token ที่มีอยู่ยังถูกต้อง | ใช้เมื่อฝ่ายจัดซื้อระงับ campaign ชั่วคราว (เช่น พบ error ของ template) แถว detail คง `pricelist_url_token` ของมัน; vendor ยัง submit ได้ถ้าต้องการ |
| `VPL_POST_008` | `completed` | `now() >= end_date` OR ทุกแถว detail มี `tb_pricelist.status = active` ที่ link | Window campaign ปิด; reminder ถูกระงับ; portal token อาจถูก revoke โดย `VPL_AUTH_015` |
| `VPL_POST_009` | `cancelled` | Flag ที่แอปตั้ง (ใน JSON `info`) บันทึกการ cancel ด้วย `system` comment ใน `tb_request_for_pricing_comment` | ใช้เมื่อ campaign ถูกละทิ้งก่อน complete portal token ทั้งหมดถูก revoke; vendor ได้รับแจ้งทาง email |

### 5.3 Invitation lifecycle (แอป derive จาก `tb_pricelist.status` และ `submitted_at`)

ตาม [[vendor-pricelist/01-data-model]] § 5 item 4 Rule ID `VPL_POST_010`–`VPL_POST_014`

| Rule ID | State ที่ derive | เงื่อนไข |
| ------- | ------------- | --------- |
| `VPL_POST_010` | `pending` | `tb_request_for_pricing_detail.pricelist_id IS NULL` AND ไม่มีการเข้า portal ที่บันทึก |
| `VPL_POST_011` | `in-progress` | บันทึกการเข้า portal แล้ว (`system` comment first-access มีอยู่) OR `tb_pricelist` ที่ link มี `status = draft` และ `submitted_at IS NULL` |
| `VPL_POST_012` | `submitted` | `tb_pricelist.submitted_at IS NOT NULL` ที่ link AND `tb_pricelist.status = draft` (รอการ approve ของ purchaser) |
| `VPL_POST_013` | `approved` | `tb_pricelist.status = active` ที่ link |
| `VPL_POST_014` | `expired` | Campaign `end_date < now()` AND `tb_pricelist.submitted_at IS NULL` ที่ link Portal token ถูก revoke อัตโนมัติโดย cron job |

### 5.4 Pricelist lifecycle (`enum_pricelist_status`)

State: `draft`, `active`, `inactive`, `expired` Rule ID `VPL_POST_015`–`VPL_POST_022`

| Rule ID | Transition / Event | ผลกระทบ |
| ------- | ------------------ | ------- |
| `VPL_POST_015` | Create (→ `draft`) | Vendor บันทึกครั้งแรกที่ portal: insert `tb_pricelist` ด้วย `status = draft`, `doc_version = 0`, snapshot `vendor_id` / `currency_id` จาก invitation; FK `tb_request_for_pricing_detail.pricelist_id` ถูก populate Auto-save fire ทุก 30 วินาทีหลังจากนั้น |
| `VPL_POST_016` | Submit (`draft → draft` พร้อม `submitted_at` ถูกเขียน) | Vendor คลิก Submit ที่ portal: validator รัน (`VPL_VAL_018`–`VPL_VAL_023`); ผ่าน `submitted_at = now()`, `system` comment append บน `tb_pricelist_comment` บันทึก submission, quality score คำนวณ (`VPL_CALC_006`) และเขียนไป `info` และ purchaser ถูกแจ้งสำหรับ review สถานะคง `draft` จนกว่าจะมีการ approve ของ purchaser — state `submitted` / `under-review` ของ carmen/docs คือ window `draft + submitted_at IS NOT NULL` นี้ |
| `VPL_POST_017` | Approve (`draft → active`) | Purchaser approve: ต้องการ `VPL_AUTH_004` (หรือ `VPL_AUTH_005` สำหรับ high-value, บวก `VPL_AUTH_010` สำหรับ multi-currency) ตั้ง `status = active`; pricelist ตอนนี้เป็นการอ้างอิงสดสำหรับ PR / PO / GRN ปลายน้ำภายใน validity window `system` comment การ approve append |
| `VPL_POST_018` | Reject (`draft → draft` พร้อม `system` rejection comment) | Purchaser reject ผ่าน `VPL_AUTH_006` พร้อมเหตุผล: pricelist อยู่ที่ `draft`, `submitted_at` reset เป็น `NULL`, `system` comment จับเหตุผล และ vendor email สำหรับ resubmission Vendor สามารถ resubmit ผ่าน portal token เดียวกันจนกว่าจะหมดอายุ |
| `VPL_POST_019` | Inactivate (`active → inactive`) | Purchaser หรือ Sysadmin ย้าย pricelist active ไป `inactive` (เช่น vendor flag สำหรับ compliance review) PR / PO / GRN ปลายน้ำปฏิบัติกับ pricelist เป็น historical-only จากจุดนี้ `system` comment Inactivation append |
| `VPL_POST_020` | Re-activate (`inactive → active`) | อนุญาตภายใน validity window เท่านั้น นอก window ระบบ reject การ re-activate และต้องการ pricelist ใหม่ (ผ่าน campaign ใหม่) |
| `VPL_POST_021` | Auto-expire (`active → expired`) | Cron background: เมื่อ `now() > effective_to_date` AND `status = active` ตั้ง `status = expired` Auto-expiry `system` comment append Pricelist ยัง queryable สำหรับรายงานประวัติ; PR / PO / GRN ปลายน้ำไม่ปฏิบัติกับมันเป็น live |
| `VPL_POST_022` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `draft` (ก่อน approve); pricelist active ไม่สามารถ soft-delete ได้เพราะ PR / PO / GRN ปลายน้ำอาจอ้างอิง unique index ทั้งหมดรวม `deleted_at` ดังนั้น pricelist ใหม่สามารถใช้ `pricelist_no` เดิม |

State diagram (Prisma-canonical):

```
[*] → draft → (submitted_at เขียน) → draft → active → inactive → active (ภายใน window)
                                          ↓        ↓
                                       (reject)  expired (auto, เมื่อ now > effective_to_date)
                                          ↓
                                        draft
```

`expired` และ `inactive` กู้คืนเป็น `active` ได้ (`expired` ต้องการ validity date ใหม่ผ่าน pricelist ใหม่; `inactive` re-activate ภายใน window) `draft` รับ soft-delete; `active` / `inactive` / `expired` คง audit history

## 6. กติกาข้ามโมดูล

Rule ID ตาม `VPL_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กติกา |
| ------- | -------------- | ---- |
| `VPL_XMOD_001` | [[purchase-request]] | การสร้างบรรทัด PR default ราคาต่อหน่วยจาก **pricelist active ของ preferred vendor** สำหรับ tuple `(product_id, currency_id)`, ปรับขนาดเป็น MOQ ของบรรทัด PR ผ่าน `VPL_CALC_004` Preferred vendor resolve ต่อ `is_preferred = true` บน `tb_pricelist_detail` (หรือผ่าน business-rule engine ที่บันทึกใน carmen/docs `price-assignment-workflow-documentation.md`) บรรทัด PR เก็บ `pricelist_detail_id` เป็น back-reference และ `pricelist_type ∈ enum_pricelist_compare_type (automatic, manual_select, manual_input)` เพื่อบันทึกว่าราคาได้รับมาอย่างไร |
| `VPL_XMOD_002` | [[purchase-request]] | เมื่อไม่มี pricelist active สำหรับสินค้า บรรทัด PR ถูกสร้างด้วย `pricelist_type = manual_input` ราคาจับแบบอิสระ และ `system` comment append บน PR flag การขาด pricelist coverage Purchaser คาดว่าจะ raise campaign เพื่อเก็บ coverage หรือ override ราคา manual ระหว่างการ approve |
| `VPL_XMOD_003` | [[purchase-order]] | ที่การ conversion PR-to-PO บรรทัด PO snapshot `price` จาก `pricelist_detail_id` ของบรรทัด PR (ราคามีผลที่การสร้าง PR) ถ้า pricelist active เปลี่ยนระหว่างการสร้าง PR และการ conversion PO ระบบ surface deviation เทียบกับราคา pricelist **ปัจจุบัน** สำหรับ Purchaser review บรรทัด PO เก็บราคาที่ snapshot ไม่ใช่ FK สด — pricelist อาจเปลี่ยนโดยไม่ส่งผลต่อ PO อ้างอิง: `PO_XMOD_005` ใน [[purchase-order/02-business-rules]] § 6 |
| `VPL_XMOD_004` | [[purchase-order]] | เมื่อราคาบรรทัด PO เบี่ยงเบนจาก pricelist active เกินขีดจำกัด tenant (default ±5%) PO ถูก route ไปยัง stage approve high-value แม้ว่า `total_amount` จะต่ำกว่าขีดจำกัด Deviation ถูก log ใน `tb_purchase_order_detail_comment` และ surface เป็น entry vendor-pricelist deviation อ้างอิง: `PO_XMOD_006` |
| `VPL_XMOD_005` | [[good-receive-note]] | ที่การ post GRN ราคาต่อหน่วยบนบรรทัด GRN ถูกเปรียบเทียบกับราคา pricelist active สำหรับ tuple `(vendor_id, product_id, unit_id, qty bracket)` Variance เกินขีดจำกัด tenant ถูก flag เป็น variance comment บน GRN และสร้าง entry deviation บนฝั่ง vendor / vendor-pricelist ป้อน analytics pricelist-deviation |
| `VPL_XMOD_006` | [[product]] | ทุก `tb_pricelist_detail.product_id` อ้างอิง `tb_product` ถ้าสินค้าถูก soft-delete ขณะมีแถว pricelist active แถวยัง queryable แต่ product picker กรองสินค้าออกสำหรับ pricelist ใหม่ แอป surface แถว pricelist ที่กลายเป็น orphan ในรายงาน data-hygiene สำหรับ Purchasing review |
| `VPL_XMOD_007` | Vendor master (`tb_vendor`) | Vendor ที่ flag เป็น inactive (`tb_vendor.is_active = false`) หรือ soft-delete ไม่สามารถถูกเชิญไปยัง campaign ใหม่และไม่สามารถสร้าง pricelist ใหม่ pricelist active ที่มีอยู่ยัง queryable แต่ surface สำหรับ review; แอปอาจ auto-inactivate (`VPL_POST_019`) ตอน vendor inactivation ตามนโยบาย tenant |
| `VPL_XMOD_008` | Currency master (`tb_currency`) | ค่า Pricelist เก็บใน `currency_id` ที่ vendor เลือก และ **ไม่** mutate โดย FX move การเปรียบเทียบข้าม vendor และข้ามสกุลเงินใช้อัตรา FX ของ tenant ที่ as-of date ของรายงาน (`VPL_CALC_005`) แหล่ง FX rate เป็นข้อกังวลการตั้งค่าของ System Administrator |
| `VPL_XMOD_009` | Validation engine (ระดับแอป) | ทุก pricelist ที่ submit ถูก validate โดย validation engine รัน format check (รูปแบบราคา, ความสม่ำเสมอสกุลเงิน), business-rule check (MOQ-tier non-increasing, lead-time bound, dedupe สินค้า+หน่วย+MOQ), completeness check (ฟิลด์ที่ต้องการ populate, ครอบคลุมสินค้า template ทั้งหมด) และ quality scoring (`VPL_CALC_006`) Output เขียนไป `tb_pricelist.info` เป็น `validation_results` (structured object) และ `quality_score` (numeric) Quality score ต่ำกว่าขีดจำกัด tenant (default 70) route pricelist ไป Purchasing Manager review แทนที่จะ auto-approve |

## 7. แหล่งอ้างอิง

- `../carmen/docs/vendor-pricelist-management/design.md` — สถาปัตยกรรม 6-phase, component breakdown และ TypeScript interface ใช้เป็น carmen/docs basis สำหรับการ cross-check แต่ละกลุ่มกติกาข้างต้น
- `../carmen/docs/vendor-pricelist-management/requirements.md` — 30+ functional requirement; map ไปยังกติกา validation ใน Section 2, กติกา authorization ใน Section 4 และกติกาข้ามโมดูลใน Section 6
- `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md` — business-rule-engine specification: rule category, condition, action และ real-time assignment logic ที่ขับ `VPL_XMOD_001`–`VPL_XMOD_004` ฝั่งโมดูลที่บริโภค
- `../carmen/docs/vendor-pricelist-management/VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — feature vendor portal ที่ใช้ใน `VPL_AUTH_007`–`VPL_AUTH_008` และ `VPL_POST_015`–`VPL_POST_016`
- `../carmen/docs/vendor-pricelist-management/VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md` — RBAC matrix ใช้ใน Section 4
- Sibling: [01-data-model.md](./01-data-model.md) — โมเดล Prisma canonical, ค่า enum, unique key multi-MOQ-per-product บน `tb_pricelist_detail` และตาราง divergence ที่ derivation Section 5 พึ่งพา
- Backend rule implementation (เมื่อเพิ่ม): `../carmen-turborepo-backend-v2/apps/` — vendor-pricelist service module เป็นจุดเชื่อมการ implement สำหรับกติกาเหล่านี้ (validation engine, quality scorer, การ derive campaign-status, token middleware, cron jobs สำหรับ auto-expire)
- โมดูลที่เกี่ยวข้อง: [[purchase-request]] (`VPL_XMOD_001`–`VPL_XMOD_002`), [[purchase-order]] (`VPL_XMOD_003`–`VPL_XMOD_004`), [[good-receive-note]] (`VPL_XMOD_005`), [[product]] (`VPL_XMOD_006`)
