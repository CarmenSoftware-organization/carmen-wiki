---
title: รายการราคาผู้ขาย (Vendor Pricelist)
description: แคตตาล็อกของผู้ขายที่เก็บสินค้าพร้อมราคาที่ตกลง, หน่วย และช่วงเวลาที่มีผลใช้ — แหล่งอ้างอิงราคาของ PR/PO
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกราคาแบบเฉพาะผู้ขายและมีกำหนดเวลา พร้อม MOQ tier — Vendor master data, Certification, Price List, Price List Template และ Request-for-Pricing (RFQ) เป็นห้าหน้าจอ CRUD อิสระภายใต้ Vendor Management บวก external vendor portal ที่ gate ด้วย token — แหล่งอ้างอิงสำหรับราคา PR / PO และ variance ของ GRN &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Purchaser, Vendor (portal ภายนอก) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_vendor`, `tb_certificate`, `tb_pricelist`, `tb_pricelist_detail`, `tb_request_for_pricing`, `tb_pricelist_template`, [vendor-pricelist/request-price-list](/th/inventory/vendor-pricelist/request-price-list) &nbsp;·&nbsp; **หน้าย่อย:** 15
> **Re-sync 2026-09-22 เทียบกับ backend HEAD `180bd19c3` / frontend HEAD `7b3a943c`:** route Save และ Submit ของ vendor portal **มีอยู่แล้ว** (`pricelist-external.controller.ts` guard ด้วย `UrlTokenGuard` ที่มีวันหมดอายุจริง), `enum_pricelist_status` เพิ่ม `submitted` (migration `20260721105944`), RFQ สามารถ **ส่ง email** ให้ vendor ได้ (`POST …/request-for-pricings/:id/send-email`, 2026-09-16), `tb_vendor` เพิ่ม `tax_no` / `branch_no` / `rating` (`20260909203000`), `tb_vendor_master_certificate` ถูกเปลี่ยนชื่อเป็น `tb_certificate` (`20260904133000`) และหน้าจอ Certification ย้ายมาอยู่ใต้ Vendor Management, `price-compare` รับ `qty` เพื่อเลือก MOQ tier, การ lookup active-pricelist คืน flag `can_use` ต่อบรรทัดสำหรับ workflow, action ของ portal ถูก log ลง `tb_activity` และ detail response มี nested entity objects (`vendor`, `currency`, `product`, `unit`, `tax_profile` — `@ExpandRefs`, 2026-09-17)
>
> **ยังคงเป็นจริงที่ HEAD:** โมดูลนี้**ไม่มี workflow engine** (ไม่มีคอลัมน์ `workflow_*` ต่างจาก PR/PO/GRN/SR) และ**ไม่มี endpoint approve/reject แยกต่างหาก** — `tb_pricelist.status` และ `tb_pricelist_template.status` เป็นฟิลด์ enum ธรรมดาที่ใครก็ตามที่มีสิทธิ์แก้ไขสามารถเปลี่ยนได้ผ่าน update call ปกติ (side-effect เดียวของวงจรชีวิต: `draft → submitted` stamp `submitted_at` และลบแถวที่ไม่มีราคา) ไม่มีคะแนนคุณภาพ (quality score), ไม่มี validation engine เกินกว่าการตรวจสอบระดับฟิลด์, ไม่มีเกณฑ์อนุมัติ Manager สำหรับมูลค่าสูง/multi-currency, ไม่มี IP allowlist หรือ session limit, ไม่มี action การ revoke token และไม่มีแถวคอมเมนต์ "system" อัตโนมัติ (event ของ portal ไปที่ `tb_activity` ไม่ใช่ตาราง comment) Finance และ Audit/Config **ไม่ใช่** persona ที่แยกต่างหากในโมดูลนี้ ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules), [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) และ [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) สำหรับรายละเอียดที่แก้ไขแล้ว

![รายการราคาผู้ขาย (Vendor Pricelist) screen](/screenshots/vendor-pricelist/index.png)

## 1. ภาพรวม

**Vendor Pricelist** (`tb_pricelist`) คือบันทึกราคาที่ผู้ขายรายหนึ่งเสนอสำหรับสินค้าชุดหนึ่ง แสดงเป็นสกุลเงินของผู้ขาย ผูกกับช่วงเวลาที่มีผลใช้ และจัดโครงสร้างรอบหน่วยและ tier ของปริมาณการสั่งซื้อขั้นต่ำ (MOQ) ที่ผู้ขายจะยึดถือ แต่ละ pricelist มีส่วนหัว — ผู้ขาย, หมายเลข pricelist, สกุลเงิน, วันที่มีผลใช้ตั้งแต่-ถึง, วิธีการ submission และสถานะ — และแถว detail หนึ่งแถวหรือมากกว่าที่ carry การอ้างอิงสินค้า, ราคาตาม MOQ tier (หน่วย, ราคาต่อหน่วย, ภาษี, lead time, flag `is_preferred`) และโน้ต สินค้าเดียวกันบน pricelist ของผู้ขายรายเดียวกันสามารถมีหลายแถว MOQ (เช่น MOQ 1 ที่ ฿12.50/Each, MOQ 50 ที่ ฿10.50/Each, MOQ 100 ที่ ฿9.75/Each) เพราะ `moq_qty` เป็นส่วนหนึ่งของ uniqueness key ของแถว

Pricelist เป็นเฉพาะผู้ขายและมีกำหนดเวลา ผู้ขายหลายรายสามารถมีสินค้าเดียวกัน แต่ละรายอยู่บน pricelist ของตนเองที่ราคาและสกุลเงินของตนเอง; checkbox `is_preferred` บนแถว detail ของ pricelist แต่ละใบทำเครื่องหมายว่า Purchaser ต้องการให้แถวไหนถูกใช้เป็นแหล่งข้อมูล default และ endpoint `GET .../pricelists/price-compare` คืนแถวที่ตรงกันข้ามผู้ขายทั้งหมด เรียงตาม `is_preferred desc, price asc` สำหรับสินค้า/สกุลเงิน/วันที่ที่กำหนด — นี่คือกลไกจริง (และง่ายกว่ามาก) เบื้องหลังราคาแบบ "preferred vendor"; ไม่มีหน้าจอเปรียบเทียบข้ามผู้ขายและไม่มี rule engine อัตโนมัติที่ตั้งค่า flag นี้ Multi-currency รองรับที่ระดับการจัดเก็บ — `currency_id` ของ pricelist คือสิ่งที่ผู้สร้างเลือก — แต่ไม่มีโค้ดที่แปลงหรือ reconcile FX ที่จุดใช้งาน; การแปลงสกุลเงิน ถ้าจำเป็น เป็นเรื่องของโมดูลปลายน้ำ

Pricelist สามารถถูกสร้างโดยตรงโดย Purchaser (ป้อนมือ, import CSV หรืออัปโหลด Excel) หรือมาถึงผ่านขั้นตอน **Request for Pricing (RFQ)**: Purchaser สร้าง RFQ จาก [Price List Template](/th/inventory/vendor-pricelist/request-price-list) ที่ระบุผู้ขายที่ถูกเชิญ และ backend สร้าง `pricelist_url_token` ทาง cryptographic หนึ่งตัวต่อผู้ขายที่ถูกเชิญทันที ผู้ขายแต่ละรายสามารถเปิด `/pl/:url_token` (portal ภายนอก) — การเข้าลิงก์จะ auto-create draft pricelist ราคาศูนย์จาก template ให้ **Gap เรื่อง Save/Submit ที่รายงานเมื่อ 2026-07-16 ปิดแล้ว:** `PATCH /api/external/api/pricelist-external/:url_token` บันทึกการแก้ไข draft ของผู้ขาย (`note`, `pricelist_detail.update[]` / `.add[]` สำหรับบรรทัด unit/MOQ ใหม่) และ `POST …/:url_token/submit` พลิก pricelist `draft → submitted` โดย stamp `submitted_at` และลบทุกบรรทัดที่ `price` เป็น null หรือ `≤ 0` (`price-list.zero-price.ts`, 2026-09-10) ทั้งสอง route อยู่หลัง `UrlTokenGuard` ซึ่งปฏิเสธ token ที่ `tb_shot_url.expired_at` (= `end_date` ของ RFQ) ผ่านไปแล้ว จากนั้น Purchaser review pricelist ที่ `submitted` บนหน้าจอ Price List ภายในและตั้ง `status = active`

เมื่อ `status` ของ pricelist ถูกตั้งเป็น `active` (โดยการแก้ไข record — ไม่มีขั้นตอนอนุมัติแยกต่างหาก) มันจะกลาย queryable เป็นแหล่งอ้างอิงสำหรับ procurement ปลายน้ำ: ราคา PR สามารถ default จากแถว preferred (`price-compare` ตอนนี้เคารพ MOQ tier ตามปริมาณสั่งซื้อและรายงานราคาซื้อล่าสุด), PO wizard กรอง active pricelist ตาม workflow ผ่าน flag `can_use` ต่อบรรทัด, การแปลงเป็น PO จะ snapshot ราคา และการ post GRN สามารถเปรียบเทียบกับมันได้ Pricelist ที่ inactive และ expired ยังคง queryable ได้สำหรับประวัติ

## 2. บริบททางธุรกิจ

Vendor pricelist ให้ procurement มี system-of-record สำหรับอัตราที่ต่อรองไว้แทนที่จะพึ่งพาราคาที่ผู้ขายเสนอในวันนั้น ๆ `price-compare` ให้ราคา PR/PO default ไปยังแถวผู้ขายที่ถูกทำเครื่องหมาย preferred (หรือถูกที่สุดถ้าไม่มีการทำเครื่องหมาย) และการตรวจสอบ variance ของ GRN (บันทึกไว้ใน [good-receive-note](/th/inventory/good-receive-note)) สามารถเปรียบเทียบราคาที่รับกับ pricelist active ได้

ในเชิงปฏิบัติการ โมดูลนี้คือหน้าจอ CRUD ตรงไปตรงมาห้าหน้าจอ ไม่ใช่ campaign wizard ที่มีการนำทาง: **Vendor** (master data ผู้ขาย — ผู้ติดต่อ, ที่อยู่, ประเภทธุรกิจ, tax profile, certificate; backend ยังเก็บ `tax_no`, `branch_no` และ `rating` 1–5 ซึ่งฟอร์ม React ยังไม่แสดง), **Certification** (`/vendor-management/certification` master `tb_certificate` ที่ certificate ของผู้ขายอ้างอิง — ย้ายมาจาก Product Management เมื่อ 2026-09-03), **Price List** (ราคาที่ผู้ขายเสนอ), **Price List Template** (สิ่งที่ RFQ ในอนาคตจะถามผู้ขายให้เสนอราคา: สินค้า, สกุลเงิน default, validity window) และ **Request for Pricing** (RFQ ขาออกที่ระบุ template และกลุ่มผู้ขาย พร้อม action **Send email** ต่อผู้ขาย — ดู [request-price-list](/th/inventory/vendor-pricelist/request-price-list)) dashboard `/vendor-management` แสดง KPI widget (จำนวนผู้ขาย active, จำนวน pricelist active, pricelist ที่ใกล้หมดอายุ, RFQ ที่กำลังจะมาถึง) แต่ไม่มี "workspace" แบบ tab รวมที่เชื่อมสี่หน้าจอเข้าด้วยกัน — ดู [vendor-pricelist/vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) สำหรับรายการ tile เต็มและการยืนยันความต่างจากระบบ widget BU/personal จริงที่แก้ไขได้ CSV import (grouped upsert คีย์ด้วย `pricelist_no`) และการอัปโหลด/ดาวน์โหลดแบบ Excel มีไว้สำหรับการดูแล pricelist จำนวนมาก

## 3. แนวคิดสำคัญ

- **Pricelist Header** (`tb_pricelist`): การอ้างอิงผู้ขาย, หมายเลข pricelist, สกุลเงิน, validity-from/-to, `submission_method` (`online`, `email`, `portal`, `manual`), `submitted_at` และ `status` (`draft`, `submitted`, `active`, `inactive`, `expired` — `enum_pricelist_status`; `submitted` เพิ่มโดย migration `20260721105944_add_submitted_pricelist_status`) `submitted` ไปถึงได้ทั้งจาก Submit บน portal ของผู้ขายหรือจาก Purchaser ตั้งสถานะบนฟอร์มภายใน; ทั้งสองทาง stamp `submitted_at` และตัดแถวที่ไม่มีราคาทิ้ง ไม่มีฟิลด์ campaign/quality-score/validation-result บน header
- **Pricelist Detail Row** (`tb_pricelist_detail`): สินค้า, หน่วย, หนึ่งแถว MOQ-tier ต่อ combination `(product, unit, moq_qty)`, `price_without_tax` / `tax_rate` / `tax_amt` / `price` (การแยกภาษีคำนวณฝั่ง client ก่อนบันทึก; backend เก็บค่าที่ได้รับมาโดยไม่คำนวณซ้ำ), `lead_time_days`, `rating` และ `is_preferred` (checkbox ต่อแถวธรรมดา ตั้งค่าแยกอิสระได้บนแต่ละ pricelist — ไม่ใช่หน้าจอ matrix ข้ามผู้ขาย)
- **Price List Template** (`tb_pricelist_template`): นิยามที่ใช้ซ้ำได้ของสิ่งที่ RFQ จะขอ — รายการสินค้า (พร้อม order unit default + รูปแบบ MOQ-tier ต่อสินค้า), สกุลเงิน default, `validity_period` (วัน) และ array reminder-day มี `status` ของตัวเอง (`draft`/`active`/`inactive`) พร้อม endpoint `PATCH :id/status` เฉพาะ แต่ endpoint นั้นไม่ทำการ validate ใด ๆ เลย (ไม่มีเงื่อนไข "ต้องมีสินค้าอย่างน้อยหนึ่งรายการ") — เป็นเพียงการเขียนสถานะเปล่า ๆ
- **Request for Pricing (RFQ)** (`tb_request_for_pricing` + `tb_request_for_pricing_detail`): ผูก template หนึ่งกับรายชื่อผู้ขายที่ระบุ พร้อม window `start_date`/`end_date` token invitation ต่อผู้ขายทั้งหมดถูกสร้างใน create call เดียวกัน — ไม่มีขั้นตอน "launch" แยกต่างหาก, ไม่มี reminder job และไม่มี campaign state `paused`/`cancelled`/`completed` ที่ derive มา การส่งเป็น action manual ต่อผู้ขาย: **Send email** (`POST …/request-for-pricings/:id/send-email` พร้อม `profile_id`, `to[]`, `cc[]`, `subject`, HTML `body`, `vendor_id` optional) ส่งผ่าน email profile ที่ตั้งค่าไว้และ log activity `email_sent` สัญญาณต่อผู้ขายที่ UI แสดง: `has_submitted: !!pricelist_id` บวก `pricelist { id, no, name, status }` ที่ลิงก์
- **Portal Token** (`pricelist_url_token`): สตริงสุ่มต่อผู้ขายที่ถูกเชิญ ฝังใน `/pl/:url_token` map ผ่านตาราง platform `tb_shot_url` ไปยัง JWT (`{ bu, vendor_id, rfp_detail_id }`) และ `expired_at` เท่ากับ `end_date` ของ RFQ `UrlTokenGuard` ปฏิเสธ token ที่หายไป ไม่รู้จัก หรือหมดอายุด้วย 401 (portal จึงแสดงหน้าจอ *This link has expired*) ยังคงไม่มี IP allowlist, session limit หรือ action revoke
- **เลขประจำตัวผู้เสียภาษีและ rating ของผู้ขาย** (`tb_vendor.tax_no`, `branch_no`, `rating`, 2026-09-09): เลขประจำตัวผู้เสียภาษีไทย 13 หลักและเลขสาขาแบบ free-text (`00000` = สำนักงานใหญ่) และ rating 1–5 แบบ manual ที่บังคับโดย DB check `vendor_rating_chk`; `tax_no` มี index ตอนนี้เป็น backend เท่านั้น — ฟอร์มผู้ขายอ่าน `tax_profile` เป็น object แต่ไม่มี input สำหรับสามคอลัมน์ใหม่
- **Preferred Row** (`is_preferred` บน `tb_pricelist_detail`): การเลือกด้วยมือของ Purchaser ว่าแถวของผู้ขายรายไหนที่ `price-compare` ควรแสดงก่อนสำหรับสินค้า/สกุลเงิน/วันที่ที่กำหนด; ไม่มี rule engine อัตโนมัติที่ตั้งค่านี้

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Purchaser | ดูแล master data ของผู้ขายและ certification master, สร้างและแก้ไข price list template และ price list โดยตรง, สร้าง RFQ ที่ระบุ template และกลุ่มผู้ขาย, ส่ง email ลิงก์ portal ให้ผู้ขายแต่ละราย และเมื่อ pricelist ของผู้ขายกลับมาเป็น `submitted` (หรือคีย์ sheet จาก email/CSV เข้า) review แล้วตั้ง `status = active` ไม่มีขั้นตอนอนุมัติแยกต่างหากหรือ gate เฉพาะ Manager — ใครก็ตามที่มีสิทธิ์แก้ไขบนหน้าจอสามารถเปลี่ยน `status` ได้ |
| Vendor | บุคคลภายนอกที่ไม่มี login ของ Carmen เปิด `/pl/:url_token` จาก invitation ทาง email ก่อน `end_date` ของ RFQ; portal จะ auto-create draft pricelist จาก template ให้ ให้ผู้ขายเลือก tax profile และ order unit ต่อสินค้า (`GET …/check-pricelist/:token/tax-profiles`, `…/units`), บันทึก draft (`PATCH …/pricelist-external/:token`), import sheet Excel และ **Submit** (`POST …/submit` → `submitted`) หลัง submit portal เป็นแบบอ่านอย่างเดียว |
| Receiver / Store Keeper | ผู้บริโภคทางอ้อม — การ post GRN สามารถเปรียบเทียบราคาที่รับกับ pricelist active ได้ ([good-receive-note](/th/inventory/good-receive-note)) ไม่มี write surface ที่นี่ |

ไม่มี persona Finance หรือ Audit/Config ที่แยกต่างหากในโมดูลนี้ — ดู [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) และ [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) สำหรับสิ่งที่เคยถูกบันทึกไว้ก่อนหน้านี้และเหตุผลที่มันไม่ตรงกับ source ปัจจุบัน

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [product](/th/inventory/product) — entry ของ pricelist อ้างอิงสินค้า
- [purchase-request](/th/inventory/purchase-request) — PR default จาก pricelist ของ preferred vendor
- [purchase-order](/th/inventory/purchase-order) — PO validate ราคากับ pricelist active
- [good-receive-note](/th/inventory/good-receive-note) — variance ราคา GRN คำนวณกับ pricelist

**Master configuration:**
- [master-data/vendor](/th/inventory/master-data/vendor) — master ของผู้ขายที่ pricelist แต่ละใบ scope ไป (`tb_vendor` — ตอนนี้มี `tax_no` / `branch_no` / `rating` และ FK `tb_tax_profile`)
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — tax profile ของ BU ที่ portal เสนอให้ผู้ขายต่อบรรทัด
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินที่ผู้ขายเลือกตอน submission
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — รหัสภาษีบนแต่ละบรรทัดของ pricelist
- [templates/price-list](/th/inventory/templates/price-list) — template ที่ใช้ซ้ำได้ที่กำหนดสินค้า/สกุลเงิน/validity ที่ RFQ ถามผู้ขาย
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยการตั้งราคา (Box / Carton / Pack) ที่แถว pricelist detail อ้างอิง

หมายเหตุ: โมดูลนี้**ไม่มี workflow engine** — `status` บน `tb_pricelist` / `tb_pricelist_template` เป็นฟิลด์ธรรมดา ไม่ใช่ stage chain แบบ [system-config/workflow](/th/inventory/system-config/workflow) — และไม่มีการเขียน activity-log อัตโนมัติ; ตาราง `*_comment` มีอยู่จริงแต่ถูก populate โดยคอมเมนต์ของผู้ใช้ที่ชัดเจนเท่านั้น ไม่ใช่จาก transition

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/vendor-pricelist-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [vendor-pricelist/01-data-model](/th/inventory/vendor-pricelist/01-data-model) — เอนทิตี, ฟิลด์, ความสัมพันธ์, enum สำหรับ tenant-schema model ตระกูล pricelist สิบตัว (บวกตาราง vendor / certificate ที่ถูกแตะในรอบนี้) (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`, `tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`, `tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) และ enum module-local สามตัว (`enum_pricelist_template_status`, `enum_pricelist_status` — ตอนนี้ห้าค่า, `pricelist_submission_method`) บวกตาราง divergence
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/vendor-pricelist/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด ครอบคลุมทั้งสาม sub-entity families ของ pricelist template, request-for-pricing และ pricelist
- [vendor-pricelist/02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) — การ validate (`VPL_VAL_001`–`VPL_VAL_025`, ยืนยันเป็น subset), การคำนวณ (`VPL_CALC_001`–`VPL_CALC_003`) และกติกาข้ามโมดูล — เขียนใหม่ 2026-07-16 เพื่อตัดเกณฑ์อนุมัติที่ไม่ยืนยัน, rule ID ของ posting-workflow และ state machine ของ campaign/invitation ที่ไม่มีโค้ดรองรับออก
- [vendor-pricelist/03-user-flow](/th/inventory/vendor-pricelist/03-user-flow) — ภาพรวม document-lifecycle + index persona
  - [vendor-pricelist/03-user-flow-purchaser](/th/inventory/vendor-pricelist/03-user-flow-purchaser) — เส้นทาง Purchaser ข้ามสี่หน้าจอ CRUD จริง (Vendor, Price List, Price List Template, Request for Pricing)
  - [vendor-pricelist/03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor) — เส้นทาง Vendor (portal ภายนอกที่ authenticate ด้วย token): เปิด → ตั้งราคา → save → submit และสิ่งที่เกิดขึ้นหลังลิงก์หมดอายุ
  - [vendor-pricelist/03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) — หน้า correction: ไม่มี persona Finance แยกต่างหากหรือกลไก co-signoff ในโมดูลนี้
  - [vendor-pricelist/03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) — หน้า correction: ไม่มี workspace Audit เฉพาะหรือ console Configuration เฉพาะในโมดูลนี้
- [vendor-pricelist/04-test-scenarios](/th/inventory/vendor-pricelist/04-test-scenarios) — ภาพรวม test-scenario + scenario ข้าม persona ที่ยึดกับหน้าจอ CRUD จริง + coverage E2E จริง
  - [vendor-pricelist/04-test-scenarios-purchaser](/th/inventory/vendor-pricelist/04-test-scenarios-purchaser) — scenario Purchaser
  - [vendor-pricelist/04-test-scenarios-vendor](/th/inventory/vendor-pricelist/04-test-scenarios-vendor) — scenario Vendor (portal save / submit / หมดอายุ); section Permission เป็น N/A เพราะ vendor ไม่มี Carmen RBAC matrix
  - [vendor-pricelist/04-test-scenarios-finance](/th/inventory/vendor-pricelist/04-test-scenarios-finance) — หน้า correction
  - [vendor-pricelist/04-test-scenarios-audit-config](/th/inventory/vendor-pricelist/04-test-scenarios-audit-config) — หน้า correction
- [Request Price List](/th/inventory/vendor-pricelist/request-price-list) — เอกสาร RFQ ขาออก (`tb_request_for_pricing` + แถว invitation ต่อผู้ขายพร้อม `pricelist_url_token`) action Send-email ต่อผู้ขาย, การหมดอายุของลิงก์ และข้อค้นพบที่ยังคงเป็นจริงเรื่องไม่มีสถานะ/ไม่มี reminder
- [Vendor Dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) — 10 tile KPI/chart ที่ hardcode ไว้ (vendor + pricelist + RFP) ของหน้าจอ landing `/vendor-management` — ไม่ใช่ widget board ที่ผู้ใช้ปรับแต่งได้

> **สถานะ (ตรวจสอบซ้ำ 2026-09-22):** การเขียนใหม่รอบ 2026-07-16 ที่ตัด workflow campaign, quality scoring, validation engine, threshold Manager/Finance และการ revoke token ออกยังคงใช้ได้ "gap ที่ยืนยันแล้ว" สองข้อของรอบนั้นถูกปิดโดยโค้ดแล้วและแก้ไขทั่วหน้าย่อย: route Save/Submit ของ portal (`pricelist-external.controller.ts`, 2026-08/09) และการหมดอายุของ token (`UrlTokenGuard` + `tb_shot_url.expired_at`) ใหม่ตั้งแต่นั้น: สถานะ `submitted`, RFQ send-email, คอลัมน์ tax/rating ของผู้ขาย, การเปลี่ยนชื่อ `tb_certificate`, `can_use`, `price-compare` `qty`, event ของ portal ใน `tb_activity` **E2E coverage:** `150-vendor.spec.ts` (31 case), `159-pl.spec.ts` (28), `160-pl-template.spec.ts` (33), `043-certification.spec.ts` (6) ใน `../carmen-inventory-frontend-e2e/tests/` พร้อมรายงาน gap ใต้ `docs/test-cases/gaps/` (54 / 65 / 58 / 29 case); portal ภายนอกมี catalog แบบเอกสารเท่านั้น `docs/test-cases/1002-external-price-list.md` (42 case ไม่มี spec); ยังไม่มี spec สำหรับ Request for Pricing
