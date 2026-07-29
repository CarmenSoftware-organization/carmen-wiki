---
title: รายการราคาผู้ขาย (Vendor Pricelist)
description: แคตตาล็อกของผู้ขายที่เก็บสินค้าพร้อมราคาที่ตกลง, หน่วย และช่วงเวลาที่มีผลใช้ — แหล่งอ้างอิงราคาของ PR/PO
published: true
date: 2026-07-29T10:15:00.000Z
tags: vendor-pricelist, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกราคาแบบเฉพาะผู้ขายและมีกำหนดเวลา พร้อม MOQ tier — Vendor master data, Price List, Price List Template และ Request-for-Pricing (RFQ) เป็นสี่หน้าจอ CRUD อิสระภายใต้ Vendor Management บวก external vendor portal ที่ไม่ต้อง authenticate — แหล่งอ้างอิงสำหรับราคา PR / PO และ variance ของ GRN &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Purchaser, Vendor (portal ภายนอก) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_pricelist`, `tb_pricelist_detail`, `tb_request_for_pricing`, `tb_pricelist_template`, [vendor-pricelist/request-price-list](/th/inventory/vendor-pricelist/request-price-list) &nbsp;·&nbsp; **หน้าย่อย:** 15
>
> **ตรวจสอบแล้ว 2026-07-16 เทียบกับ source ปัจจุบัน:** โมดูลนี้**ไม่มี workflow engine** (ไม่มีคอลัมน์ `workflow_*` ต่างจาก PR/PO/GRN/SR) และ**ไม่มี endpoint approve/reject แยกต่างหาก** — `tb_pricelist.status` และ `tb_pricelist_template.status` เป็นฟิลด์ enum ธรรมดาที่ใครก็ตามที่มีสิทธิ์แก้ไขสามารถเปลี่ยนได้ผ่าน update call ปกติ ไม่มีคะแนนคุณภาพ (quality score), ไม่มี validation engine เกินกว่าการตรวจสอบระดับฟิลด์, ไม่มีเกณฑ์อนุมัติ Manager สำหรับมูลค่าสูง/multi-currency, ไม่มี IP allowlist หรือ session limit ของ portal token, ไม่มี action การ revoke token และไม่มีการบันทึกคอมเมนต์ "system" อัตโนมัติในทุก transition — ไม่มีข้อใดในรายการนี้ที่มีโค้ดรองรับ Finance และ Audit/Config **ไม่ใช่** persona ที่แยกต่างหากในโมดูลนี้ ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules), [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) และ [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) สำหรับรายละเอียดที่แก้ไขแล้ว

![รายการราคาผู้ขาย (Vendor Pricelist) screen](/screenshots/vendor-pricelist/index.png)

## 1. ภาพรวม

**Vendor Pricelist** (`tb_pricelist`) คือบันทึกราคาที่ผู้ขายรายหนึ่งเสนอสำหรับสินค้าชุดหนึ่ง แสดงเป็นสกุลเงินของผู้ขาย ผูกกับช่วงเวลาที่มีผลใช้ และจัดโครงสร้างรอบหน่วยและ tier ของปริมาณการสั่งซื้อขั้นต่ำ (MOQ) ที่ผู้ขายจะยึดถือ แต่ละ pricelist มีส่วนหัว — ผู้ขาย, หมายเลข pricelist, สกุลเงิน, วันที่มีผลใช้ตั้งแต่-ถึง, วิธีการ submission และสถานะ — และแถว detail หนึ่งแถวหรือมากกว่าที่ carry การอ้างอิงสินค้า, ราคาตาม MOQ tier (หน่วย, ราคาต่อหน่วย, ภาษี, lead time, flag `is_preferred`) และโน้ต สินค้าเดียวกันบน pricelist ของผู้ขายรายเดียวกันสามารถมีหลายแถว MOQ (เช่น MOQ 1 ที่ ฿12.50/Each, MOQ 50 ที่ ฿10.50/Each, MOQ 100 ที่ ฿9.75/Each) เพราะ `moq_qty` เป็นส่วนหนึ่งของ uniqueness key ของแถว

Pricelist เป็นเฉพาะผู้ขายและมีกำหนดเวลา ผู้ขายหลายรายสามารถมีสินค้าเดียวกัน แต่ละรายอยู่บน pricelist ของตนเองที่ราคาและสกุลเงินของตนเอง; checkbox `is_preferred` บนแถว detail ของ pricelist แต่ละใบทำเครื่องหมายว่า Purchaser ต้องการให้แถวไหนถูกใช้เป็นแหล่งข้อมูล default และ endpoint `GET .../pricelists/price-compare` คืนแถวที่ตรงกันข้ามผู้ขายทั้งหมด เรียงตาม `is_preferred desc, price asc` สำหรับสินค้า/สกุลเงิน/วันที่ที่กำหนด — นี่คือกลไกจริง (และง่ายกว่ามาก) เบื้องหลังราคาแบบ "preferred vendor"; ไม่มีหน้าจอเปรียบเทียบข้ามผู้ขายและไม่มี rule engine อัตโนมัติที่ตั้งค่า flag นี้ Multi-currency รองรับที่ระดับการจัดเก็บ — `currency_id` ของ pricelist คือสิ่งที่ผู้สร้างเลือก — แต่ไม่มีโค้ดที่แปลงหรือ reconcile FX ที่จุดใช้งาน; การแปลงสกุลเงิน ถ้าจำเป็น เป็นเรื่องของโมดูลปลายน้ำ

Pricelist สามารถถูกสร้างโดยตรงโดย Purchaser (ป้อนมือ, import CSV หรืออัปโหลด Excel) หรือมาถึงผ่านขั้นตอน **Request for Pricing (RFQ)**: Purchaser สร้าง RFQ จาก [Price List Template](/th/inventory/vendor-pricelist/request-price-list) ที่ระบุผู้ขายที่ถูกเชิญ และ backend สร้าง `pricelist_url_token` ทาง cryptographic หนึ่งตัวต่อผู้ขายที่ถูกเชิญทันที ผู้ขายแต่ละรายสามารถเปิด `/pl/:url_token` (portal ภายนอก) — การเข้าลิงก์จะ auto-create draft pricelist ราคาศูนย์จาก template ให้ **Confirmed gap:** ปุ่ม Save และ Submit ของ portal เรียก backend route (`PATCH`/`POST .../pricelist-external/:token[/submit]`) ที่**ไม่มีอยู่จริง**ใน backend ปัจจุบัน — ดังนั้นวันนี้ผู้ขายสามารถดู draft ที่ auto-create ได้ แต่ไม่สามารถบันทึกการแก้ไขหรือ submit ผ่าน portal นี้ได้จริง Purchaser ยังคงสามารถแก้ไขและ activate draft นั้นได้โดยตรงจากหน้าจอ Price List ภายในเมื่อมันถูกสร้างขึ้นแล้ว

เมื่อ `status` ของ pricelist ถูกตั้งเป็น `active` (โดยการแก้ไข record — ไม่มีขั้นตอนอนุมัติแยกต่างหาก) มันจะกลาย queryable เป็นแหล่งอ้างอิงสำหรับ procurement ปลายน้ำ: ราคา PR สามารถ default จากแถว preferred, การแปลงเป็น PO จะ snapshot ราคา และการ post GRN สามารถเปรียบเทียบกับมันได้ Pricelist ที่ inactive และ expired ยังคง queryable ได้สำหรับประวัติ

## 2. บริบททางธุรกิจ

Vendor pricelist ให้ procurement มี system-of-record สำหรับอัตราที่ต่อรองไว้แทนที่จะพึ่งพาราคาที่ผู้ขายเสนอในวันนั้น ๆ `price-compare` ให้ราคา PR/PO default ไปยังแถวผู้ขายที่ถูกทำเครื่องหมาย preferred (หรือถูกที่สุดถ้าไม่มีการทำเครื่องหมาย) และการตรวจสอบ variance ของ GRN (บันทึกไว้ใน [good-receive-note](/th/inventory/good-receive-note)) สามารถเปรียบเทียบราคาที่รับกับ pricelist active ได้

ในเชิงปฏิบัติการ โมดูลนี้คือหน้าจอ CRUD ตรงไปตรงมาสี่หน้าจอ ไม่ใช่ campaign wizard ที่มีการนำทาง: **Vendor** (master data ผู้ขาย — ผู้ติดต่อ, ที่อยู่, ประเภทธุรกิจ, certificate), **Price List** (ราคาที่ผู้ขายเสนอ), **Price List Template** (สิ่งที่ RFQ ในอนาคตจะถามผู้ขายให้เสนอราคา: สินค้า, สกุลเงิน default, validity window) และ **Request for Pricing** (RFQ ขาออกที่ระบุ template และกลุ่มผู้ขาย — ดู [request-price-list](/th/inventory/vendor-pricelist/request-price-list)) dashboard `/vendor-management` แสดง KPI widget (จำนวนผู้ขาย active, จำนวน pricelist active, pricelist ที่ใกล้หมดอายุ, RFQ ที่กำลังจะมาถึง) แต่ไม่มี "workspace" แบบ tab รวมที่เชื่อมสี่หน้าจอเข้าด้วยกัน — ดู [vendor-pricelist/vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) สำหรับรายการ tile เต็มและการยืนยันความต่างจากระบบ widget BU/personal จริงที่แก้ไขได้ CSV import (grouped upsert คีย์ด้วย `pricelist_no`) และการอัปโหลด/ดาวน์โหลดแบบ Excel มีไว้สำหรับการดูแล pricelist จำนวนมาก

## 3. แนวคิดสำคัญ

- **Pricelist Header** (`tb_pricelist`): การอ้างอิงผู้ขาย, หมายเลข pricelist, สกุลเงิน, validity-from/-to, `submission_method` (`online`, `email`, `portal`, `manual`) และ `status` (`draft`, `active`, `inactive`, `expired` — `enum_pricelist_status`) ไม่มีฟิลด์ campaign/quality-score/validation-result บน header — ฟิลด์เหล่านั้นมีอยู่แค่ในกระเป๋า JSON `info` แบบ schemaless ที่ไม่มี service ใดอ่านหรือเขียนในปัจจุบัน
- **Pricelist Detail Row** (`tb_pricelist_detail`): สินค้า, หน่วย, หนึ่งแถว MOQ-tier ต่อ combination `(product, unit, moq_qty)`, `price_without_tax` / `tax_rate` / `tax_amt` / `price` (การแยกภาษีคำนวณฝั่ง client ก่อนบันทึก; backend เก็บค่าที่ได้รับมาโดยไม่คำนวณซ้ำ), `lead_time_days`, `rating` และ `is_preferred` (checkbox ต่อแถวธรรมดา ตั้งค่าแยกอิสระได้บนแต่ละ pricelist — ไม่ใช่หน้าจอ matrix ข้ามผู้ขาย)
- **Price List Template** (`tb_pricelist_template`): นิยามที่ใช้ซ้ำได้ของสิ่งที่ RFQ จะขอ — รายการสินค้า (พร้อม order unit default + รูปแบบ MOQ-tier ต่อสินค้า), สกุลเงิน default, `validity_period` (วัน) และ array reminder-day มี `status` ของตัวเอง (`draft`/`active`/`inactive`) พร้อม endpoint `PATCH :id/status` เฉพาะ แต่ endpoint นั้นไม่ทำการ validate ใด ๆ เลย (ไม่มีเงื่อนไข "ต้องมีสินค้าอย่างน้อยหนึ่งรายการ") — เป็นเพียงการเขียนสถานะเปล่า ๆ
- **Request for Pricing (RFQ)** (`tb_request_for_pricing` + `tb_request_for_pricing_detail`): ผูก template หนึ่งกับรายชื่อผู้ขายที่ระบุ พร้อม window `start_date`/`end_date` token invitation ต่อผู้ขายทั้งหมดถูกสร้างใน create call เดียวกัน — ไม่มีขั้นตอน "launch" แยกต่างหาก, ไม่มี reminder job และไม่มี campaign state `paused`/`cancelled`/`completed` ที่ derive มา (ไม่มีโค้ดที่อ่านหรือเขียน flag แบบนี้) สัญญาณต่อผู้ขายเดียวที่ UI แสดงคือ `has_submitted: !!pricelist_id`
- **Portal Token** (`pricelist_url_token`): สตริงสุ่มต่อผู้ขายที่ถูกเชิญ ฝังใน `/pl/:url_token` มันเป็นตัวกันสิทธิ์ให้กับ portal call ที่ทำงานได้จริงเพียงตัวเดียว (auto-create/คืน draft pricelist) ไม่มีการตรวจสอบวันหมดอายุ, ไม่มี IP allowlist, ไม่มี session limit และไม่มี action revoke อยู่ในโค้ดที่ไหนเลย — ไม่มีสิ่งเหล่านี้อยู่จริง
- **Preferred Row** (`is_preferred` บน `tb_pricelist_detail`): การเลือกด้วยมือของ Purchaser ว่าแถวของผู้ขายรายไหนที่ `price-compare` ควรแสดงก่อนสำหรับสินค้า/สกุลเงิน/วันที่ที่กำหนด; ไม่มี rule engine อัตโนมัติที่ตั้งค่านี้

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Purchaser | ดูแล master data ของผู้ขาย, สร้างและแก้ไข price list template และ price list โดยตรง, สร้าง RFQ ที่ระบุ template และกลุ่มผู้ขาย และ (เมื่อ draft ที่สร้างผ่าน portal ของผู้ขาย หรือ submission ทาง email/CSV มีอยู่แล้ว) แก้ไขและ activate pricelist ไม่มีขั้นตอนอนุมัติแยกต่างหากหรือ gate เฉพาะ Manager — ใครก็ตามที่มีสิทธิ์แก้ไขบนหน้าจอสามารถเปลี่ยน `status` ได้ |
| Vendor | บุคคลภายนอกที่ไม่มี login ของ Carmen เปิด `/pl/:url_token` จาก invitation; portal จะ auto-create draft pricelist จาก template ให้ **Confirmed gap:** การเรียก Save/Submit ของ portal ไปยัง backend route ที่ไม่มีอยู่จริงในวันนี้ ดังนั้นผู้ขายไม่สามารถบันทึกการแก้ไขหรือ submit ผ่านหน้าจอนี้ได้จริง — Purchaser จะแก้ไข draft ที่ auto-create นั้นโดยตรงบนหน้าจอ Price List ภายในแทน |
| Receiver / Store Keeper | ผู้บริโภคทางอ้อม — การ post GRN สามารถเปรียบเทียบราคาที่รับกับ pricelist active ได้ ([good-receive-note](/th/inventory/good-receive-note)) ไม่มี write surface ที่นี่ |

ไม่มี persona Finance หรือ Audit/Config ที่แยกต่างหากในโมดูลนี้ — ดู [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) และ [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) สำหรับสิ่งที่เคยถูกบันทึกไว้ก่อนหน้านี้และเหตุผลที่มันไม่ตรงกับ source ปัจจุบัน

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [product](/th/inventory/product) — entry ของ pricelist อ้างอิงสินค้า
- [purchase-request](/th/inventory/purchase-request) — PR default จาก pricelist ของ preferred vendor
- [purchase-order](/th/inventory/purchase-order) — PO validate ราคากับ pricelist active
- [good-receive-note](/th/inventory/good-receive-note) — variance ราคา GRN คำนวณกับ pricelist

**Master configuration:**
- [master-data/vendor](/th/inventory/master-data/vendor) — master ของผู้ขายที่ pricelist แต่ละใบ scope ไป
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

- [vendor-pricelist/01-data-model](/th/inventory/vendor-pricelist/01-data-model) — เอนทิตี, ฟิลด์, ความสัมพันธ์, enum สำหรับ tenant-schema model สิบตัว (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`, `tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`, `tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) และ enum module-local สามตัว (`enum_pricelist_template_status`, `enum_pricelist_status`, `pricelist_submission_method`) บวกตาราง divergence สำหรับความแตกต่าง material 12 รายการระหว่าง carmen/docs `design.md` และ Prisma
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/vendor-pricelist/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด ครอบคลุมทั้งสาม sub-entity families ของ pricelist template, request-for-pricing และ pricelist
- [vendor-pricelist/02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) — การ validate (`VPL_VAL_001`–`VPL_VAL_025`, ยืนยันเป็น subset), การคำนวณ (`VPL_CALC_001`–`VPL_CALC_003`) และกติกาข้ามโมดูล — เขียนใหม่ 2026-07-16 เพื่อตัดเกณฑ์อนุมัติที่ไม่ยืนยัน, rule ID ของ posting-workflow และ state machine ของ campaign/invitation ที่ไม่มีโค้ดรองรับออก
- [vendor-pricelist/03-user-flow](/th/inventory/vendor-pricelist/03-user-flow) — ภาพรวม document-lifecycle + index persona
  - [vendor-pricelist/03-user-flow-purchaser](/th/inventory/vendor-pricelist/03-user-flow-purchaser) — เส้นทาง Purchaser ข้ามสี่หน้าจอ CRUD จริง (Vendor, Price List, Price List Template, Request for Pricing)
  - [vendor-pricelist/03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor) — เส้นทาง Vendor (portal ภายนอกที่ authenticate ด้วย token) รวมถึง gap ของ backend Save/Submit ที่ยืนยันแล้ว
  - [vendor-pricelist/03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) — หน้า correction: ไม่มี persona Finance แยกต่างหากหรือกลไก co-signoff ในโมดูลนี้
  - [vendor-pricelist/03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) — หน้า correction: ไม่มี workspace Audit เฉพาะหรือ console Configuration เฉพาะในโมดูลนี้
- [vendor-pricelist/04-test-scenarios](/th/inventory/vendor-pricelist/04-test-scenarios) — ภาพรวม test-scenario + scenario ข้าม persona ที่ยึดกับหน้าจอ CRUD จริง + coverage E2E จริง
  - [vendor-pricelist/04-test-scenarios-purchaser](/th/inventory/vendor-pricelist/04-test-scenarios-purchaser) — scenario Purchaser
  - [vendor-pricelist/04-test-scenarios-vendor](/th/inventory/vendor-pricelist/04-test-scenarios-vendor) — scenario Vendor; section Permission เป็น N/A เพราะ vendor ไม่มี Carmen RBAC matrix
  - [vendor-pricelist/04-test-scenarios-finance](/th/inventory/vendor-pricelist/04-test-scenarios-finance) — หน้า correction
  - [vendor-pricelist/04-test-scenarios-audit-config](/th/inventory/vendor-pricelist/04-test-scenarios-audit-config) — หน้า correction
- [Request Price List](/th/inventory/vendor-pricelist/request-price-list) — เอกสาร RFQ ขาออก (`tb_request_for_pricing` + แถว invitation ต่อผู้ขายพร้อม `pricelist_url_token`) รวมถึง gap ของ Save/Submit บน portal ที่ยืนยันแล้ว และข้อค้นพบที่แก้ไขแล้วเรื่องไม่มีสถานะ/ไม่มี reminder
- [Vendor Dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) — 10 tile KPI/chart ที่ hardcode ไว้ (vendor + pricelist + RFP) ของหน้าจอ landing `/vendor-management` — ไม่ใช่ widget board ที่ผู้ใช้ปรับแต่งได้

> **สถานะ (ตรวจสอบแล้ว 2026-07-16):** ส่วน data-model ยึดกับ Prisma schema canonical (`tb_pricelist*` + `tb_request_for_pricing*` + `tb_pricelist_template*` — สิบเอนทิตี, สาม enum module-local) และยังคงถูกต้อง Business-rules, user-flow และ test-scenarios ถูกเขียนใหม่อย่างมีนัยสำคัญในรอบนี้ — draft ก่อนหน้าอธิบาย workflow campaign แบบ 6-phase, quality scoring, validation engine, เกณฑ์อนุมัติ Manager/Finance-Manager, นโยบาย IP/session ของ portal-token และการ revoke token และการเขียน activity-log อัตโนมัติ ซึ่งไม่มีข้อใดมีโค้ดรองรับ; Finance และ Audit/Config ถูกบันทึกเป็นหน้า correction ตาม pattern ที่ตั้งไว้แล้วสำหรับโมดูล inventory อื่นที่มี persona axis ที่แต่งขึ้น **มี E2E coverage อยู่จริง** — `150-vendor.spec.ts`, `159-pl.spec.ts` และ `160-pl-template.spec.ts` ใน `../carmen-inventory-frontend-e2e/tests/` (คำกล่าวก่อนหน้านี้ที่ว่า "ไม่มี spec dedicated" ผิด); ยังไม่มี spec dedicated สำหรับ Request for Pricing
