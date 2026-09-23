---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Purchaser
description: Flow ของ Purchaser ภายในโมดูล vendor-pricelist — ห้าหน้าจอ CRUD อิสระ (Vendor, Certification, Price List, Price List Template, Request for Pricing) ไม่มี workspace รวม ไม่มี workflow engine
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, user-flow, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Purchaser

> **At a Glance**
> **Persona:** Purchaser &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist) &nbsp;·&nbsp; **หน้าจอ:** Vendor, Certification, Price List, Price List Template, Request for Pricing — ห้าหน้า top-level แยกกันภายใต้ Vendor Management บวก KPI dashboard ที่ `/vendor-management`
> **ตรวจสอบเมื่อ 2026-07-16 ตรวจซ้ำ 2026-09-22:** ไม่มี gate high-value เฉพาะ Manager, ไม่มี Finance co-signoff, ไม่มี "matrix" preferred-vendor, ไม่มี action reminders/campaign-pause/cancel — ไม่มีตัวใดมีโค้ดตรงกันเลย **ใหม่ตั้งแต่นั้น:** **Send email** ของ RFQ ต่อ vendor, pricelist ของ vendor กลับมาเป็น `submitted` จาก portal, สถานะ `submitted` บนฟอร์ม, หน้าจอ Certification ใต้เมนูนี้, `tax_profile` ของ vendor แสดงเป็น object (`tax_no` / `branch_no` / `rating` ของ backend ยังไม่มี input ในฟอร์ม)

## 1. Role ในโมดูลนี้

**Purchaser** เป็น persona ภายในเดียวที่มี write surface ในโมดูลนี้ หน้าเวอร์ชันก่อนหน้ารวม "Purchaser / Purchasing Staff" และ "Purchasing Manager" เข้าไว้ในไฟล์เดียวบนทฤษฎีที่ว่า Manager ถือสิทธิ์การ approve ที่สูงกว่าและถูก gate ด้วย threshold บนหน้าจอเดียวกัน Threshold นั้นไม่มีอยู่จริง — ไม่มี endpoint approve/reject แยกต่างหากบน Price List หรือ Price List Template เลย ดังนั้นจึงไม่มีอะไรให้ tier ของ Manager ไป gate ไฟล์นี้จึงบันทึก role Purchaser เดียวที่ครอบคลุมทั้งห้าหน้าจอ: **Vendor** (master data — contact, ที่อยู่, ประเภทธุรกิจ, tax profile, certificate), **Certification** (master `tb_certificate` ที่ certificate ของ vendor อ้างอิง — `/vendor-management/certification` ย้ายมาจาก Product Management เมื่อ 2026-09-03), **Price List** (ราคาที่ vendor เสนอ), **Price List Template** (สิ่งที่ RFQ ในอนาคตจะขอให้ vendor เสนอราคา) และ **Request for Pricing** (RFQ ขาออกที่ระบุ template + vendor cohort ส่ง email ทีละ vendor)

## 2. จุดเข้าและ Primary Flow

**จุดเข้า:** Sidebar → **Vendor Management** ตกที่ KPI dashboard (`/vendor-management`) พร้อม widget tile สำหรับจำนวน vendor ที่ active, จำนวน pricelist ที่ active, pricelist ที่ใกล้หมดอายุ และ RFQ ที่กำลังจะถึง/ที่ออกแล้ว — ไม่ใช่ workspace แบบ tab รวม แต่ละหนึ่งในห้าหน้าจอย่อย (Vendor, Certification, Price List, Price List Template, Request Price List) เป็น route list/detail/new top-level ของตัวเองที่เข้าถึงได้จาก sidebar; หน้า list ใช้ `ListToolbar` / filter menu สไตล์ Linear, saved view และ sort ฝั่ง server บนคอลัมน์จริงร่วมกัน (vendor / period / status สำหรับ Price List; currency / validity / status สำหรับ template; period สำหรับ RFQ)

**Primary flow — การสร้าง coverage สำหรับสายผลิตภัณฑ์ใหม่:**

1. **ดูแล vendor** Sidebar → **Vendor** → **New** (หรือแก้ vendor ที่มีอยู่) กรอกรหัส, ชื่อ, ประเภทธุรกิจ, tax profile, ที่อยู่, contact, certificate (จาก Certification master พร้อมเลขที่ / วันออก / วันหมดอายุ / attachment) และแถวข้อมูล free-form ใด ๆ Save (`PUT /api/config/{bu}/vendors/:id`) backend ยังรับ `tax_no`, `branch_no` และ `rating` 1–5 (Bruno / API เท่านั้น — ฟอร์มยังไม่มี input)
2. **สร้าง Price List Template** (ทางเลือก — จำเป็นเฉพาะเมื่อจะเก็บราคาผ่าน RFQ แทนการป้อนโดยตรง) Sidebar → **Price List Template** → **New** กรอก `name`, `vendor_instructions`, default `currency_id`, `validity_period` (วัน), `reminder_days` และคำแนะนำสำหรับ vendor เพิ่มสินค้าผ่าน section **Products** — แต่ละสินค้าได้รับ default order unit และ MOQ-tier definition อย่างน้อยหนึ่งรายการ เก็บเป็น JSON (`order_unit_obj`) Save; เลือกได้ว่าจะพลิก `status` เป็น `active` ผ่าน control status ของ template (`PATCH :id/status` — การเขียน status เปล่า ๆ โดยไม่มี gate ใด ๆ ดังนั้นขั้นนี้ไม่มีผลอะไรนอกเหนือจากค่าฟิลด์เอง)
3. **สร้าง Request for Pricing** เพื่อขอราคา Sidebar → **Request Price List** → **New** เลือก template, ตั้ง `name`/`start_date`/`end_date`/`custom_message` และเพิ่มแถว vendor ผ่าน dialog **Add vendors** แบบ multi-select (ผู้ติดต่อ/เบอร์โทร/email แก้ได้ต่อแถว) คลิก Save — การเรียกครั้งเดียวนี้ทั้งสร้าง RFQ header และสำหรับทุกแถว vendor สร้าง `pricelist_url_token` ที่ unique, sign JWT และเขียนแถว `tb_shot_url` ที่ `expired_at` คือ `end_date` ของ RFQ ไม่มีขั้นตอน "launch" แยกต่างหาก
3a. **ส่ง email ลิงก์ให้ vendor แต่ละราย** บน RFQ ที่บันทึกแล้ว แต่ละแถว vendor มี action **Send email**: เลือก email profile, ป้อน `to` (และ `cc` optional) และปรับ subject / HTML body ที่เติมไว้ล่วงหน้าจาก email template ที่มี placeholder `rfp` — ลิงก์ portal `/pl/:url_token` ถูกแทรกฝั่ง client `POST …/request-for-pricings/:id/send-email` บันทึก activity `email_sent` ทำซ้ำต่อ vendor (ไม่มี bulk send)
4. **Vendor เปิด portal ตั้งราคา และ submit** การเข้า `/pl/:url_token` auto-create draft `tb_pricelist` ที่ราคาศูนย์จาก template (หรือ return ตัวที่มีอยู่แล้ว); vendor บันทึก draft และคลิก **Submit** — pricelist กลายเป็น `submitted` (`submitted_at` ถูก stamp แถวที่ไม่มีราคาถูกลบ) แถว RFQ แสดง `has_submitted` บวกเลขที่และสถานะของ pricelist หลัง `end_date` ลิงก์คืน 401 ดู [03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor)
5. **Review และ activate pricelist** เปิด pricelist ที่ `submitted` บนหน้า **Price List** ตรวจราคา / MOQ tier / ภาษี ปรับถ้าจำเป็น และตั้ง `status = active` จากฟอร์มแก้ไข (`effective_from/to` บังคับบนฟอร์มตั้งแต่ 2026-09-11) ไม่มี endpoint approve/reject — control สถานะคือการมอบ อีกทางหนึ่งคือข้าม RFQ ไปเลย: Sidebar → **Price List** → **New** เลือก vendor และสกุลเงิน เพิ่มแถว detail และ save ที่ `status = active` โดยตรง (หรือที่ `submitted` ซึ่งใช้การตัดทิ้ง/stamp เดียวกับ portal) — เส้นทางที่พบบ่อยสำหรับราคาที่เจรจาทางโทรศัพท์/email
6. **Mark แถว preferred ถ้ามีมากกว่าหนึ่ง vendor เสนอราคาสินค้าเดียวกัน** บน grid **Products** ของ pricelist เอง checkbox `is_preferred` (ไอคอน Crown ในโหมด view) เป็น flag ต่อแถว ตั้งค่าอย่างอิสระบน pricelist ของแต่ละ vendor เอง ไม่มีหน้าจอเปรียบเทียบข้าม vendor — ผลของ flag นี้มองเห็นได้เพียงผ่าน endpoint `price-compare` (`is_preferred desc, price asc` ตอนนี้รู้จัก tier เมื่อผู้เรียกส่ง `qty` และแสดงราคาซื้อล่าสุด) ซึ่งการตั้งราคา PR/PO ปลายน้ำบริโภคใช้; PO wizard ยัง grey out บรรทัดที่สินค้าอยู่นอก workflow ที่เลือก (`can_use`)

## 3. สาขาการตัดสินใจ

- **Bulk-load price sheet ของ vendor** หน้า Price List รองรับ CSV import (grouped upsert keyed บน `pricelist_no` พร้อม validation ต่อแถวของ product/unit/vendor/currency) และ upload/download แบบ Excel นอกเหนือจากการป้อนแถวด้วยตนเอง — มีประโยชน์เมื่อ vendor ส่ง spreadsheet มาแทนการใช้ portal
- **การแก้ไข pricelist ที่ active** ไม่มี immutability guard บน pricelist ที่ `active` — Purchaser สามารถแก้แถว detail บน pricelist ที่ active ได้โดยตรง ไม่มีข้อกำหนดให้ inactivate ก่อน ต่างจากกติกาเดิม (ที่ยังไม่ implement) ของเอกสารออกแบบที่ให้ "เปิด pricelist ใหม่"
- **Vendor ไม่สามารถใช้ portal ได้เลย** ตั้งค่า `submission_method = manual` หรือ `email` ของ pricelist โดยตรงบนฟอร์ม Price List และป้อนราคาที่ Purchaser ได้รับทางโทรศัพท์หรือ email — ไม่มีหน้าจอ "upload ในนาม vendor" แยกต่างหากจากฟอร์ม create/edit ปกติ
- **การตัดสินใจว่า vendor ใด preferred สำหรับสินค้า** Toggle `is_preferred` บนแถว pricelist ของ vendor ที่ชนะ ไม่มีสิ่งใดบังคับ "แถว preferred เดียวต่อสินค้า" โดยอัตโนมัติ — Purchaser อาจปล่อยให้ vendor สองรายถูก mark preferred พร้อมกัน ซึ่งในกรณีนั้นการ sort ของ `price-compare` (`is_preferred desc, price asc`) จะเลือกรายที่ราคาต่ำกว่าเป็น `selected`
- **ลิงก์ของ vendor หมดอายุก่อนที่จะ submit** token ตายที่ `end_date` และไม่มีอะไรออกใหม่ให้; สร้าง RFQ ใหม่ (หรือเพิ่ม vendor อีกครั้งหลังลบแถว — unique key ว่างเมื่อ soft-delete) เพื่อออก token ใหม่ แล้ว Send email อีกครั้ง
- **ดูแล certification master** Sidebar → **Certification** → create/edit แบบ dialog (`code`, `name`, `description`, `is_active`); section Certificates ของฟอร์ม vendor เลือกจากรายการนี้ (`GET /api/config/{bu}/vendor-master-certificates`)

## 4. จุดออก / Handoff

- **Pricelist active** เมื่อ `tb_pricelist.status = active` แล้ว มัน queryable ได้โดย pricing logic ของ [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) ผ่าน `price-compare` และ endpoint lookup active-pricelist ไม่ต้องมี action เพิ่มเติมจาก Purchaser
- **RFQ ที่ vendor ไม่เคยตอบกลับ** ไม่มี reminder และไม่มี state "campaign closed" — แถว RFQ และแถว invitation ที่ยังไม่แก้ไขจะคงอยู่ในรายการเฉย ๆ แยกแยะได้ผ่าน `has_submitted = false` (และ pricelist ที่ลิงก์ยังเป็น `draft` ถ้า vendor อย่างน้อยเปิดลิงก์) ตัวลิงก์เองหยุดทำงานที่ `end_date`

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — ฟิลด์ status จริงและตาราง handoff ข้าม persona ที่ยืนยันแล้ว
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) — status confirmed-vs-design-target ต่อกติกา
- โมเดลข้อมูล: [01-data-model.md](./01-data-model.md) — เอนทิตี, unique key multi-MOQ-per-product บน `tb_pricelist_detail`
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — คู่กรณีภายนอกที่การ submit บน portal ผลิต pricelist `submitted` ที่ Step 5 ของไฟล์นี้ activate
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) / [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — หน้า correction; ไม่มี persona ใดมีอยู่แยกต่างหากจริงในโมดูลนี้
- Cross-link: [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [product](/th/inventory/product)
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`
