---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Purchaser
description: Flow ของ Purchaser ภายในโมดูล vendor-pricelist — สี่หน้าจอ CRUD อิสระ (Vendor, Price List, Price List Template, Request for Pricing) ไม่มี workspace รวม ไม่มี workflow engine
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Purchaser

> **At a Glance**
> **Persona:** Purchaser &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist) &nbsp;·&nbsp; **หน้าจอ:** Vendor, Price List, Price List Template, Request for Pricing — สี่หน้า top-level แยกกันภายใต้ Vendor Management บวก KPI dashboard ที่ `/vendor-management`
> **ตรวจสอบเมื่อ 2026-07-16:** ไม่มี gate high-value เฉพาะ Manager, ไม่มี Finance co-signoff, ไม่มี "matrix" preferred-vendor, ไม่มี action reminders/campaign-pause/cancel — ไม่มีตัวใดมีโค้ดตรงกันเลย

## 1. Role ในโมดูลนี้

**Purchaser** เป็น persona ภายในเดียวที่มี write surface ในโมดูลนี้ หน้าเวอร์ชันก่อนหน้ารวม "Purchaser / Purchasing Staff" และ "Purchasing Manager" เข้าไว้ในไฟล์เดียวบนทฤษฎีที่ว่า Manager ถือสิทธิ์การ approve ที่สูงกว่าและถูก gate ด้วย threshold บนหน้าจอเดียวกัน Threshold นั้นไม่มีอยู่จริง — ไม่มี endpoint approve/reject แยกต่างหากบน Price List หรือ Price List Template เลย ดังนั้นจึงไม่มีอะไรให้ tier ของ Manager ไป gate ไฟล์นี้จึงบันทึก role Purchaser เดียวที่ครอบคลุมทั้งสี่หน้าจอ: **Vendor** (master data — contact, ที่อยู่, ประเภทธุรกิจ, certificate), **Price List** (ราคาที่ vendor เสนอ), **Price List Template** (สิ่งที่ RFQ ในอนาคตจะขอให้ vendor เสนอราคา) และ **Request for Pricing** (RFQ ขาออกที่ระบุ template + vendor cohort)

## 2. จุดเข้าและ Primary Flow

**จุดเข้า:** Sidebar → **Vendor Management** ตกที่ KPI dashboard (`/vendor-management`) พร้อม widget tile สำหรับจำนวน vendor ที่ active, จำนวน pricelist ที่ active, pricelist ที่ใกล้หมดอายุ และ RFQ ที่กำลังจะถึง/ที่ออกแล้ว — ไม่ใช่ workspace แบบ tab รวม แต่ละหนึ่งในสี่หน้าจอย่อย (Vendor, Price List, Price List Template, Request Price List) เป็น route list/detail/new top-level ของตัวเองที่เข้าถึงได้จาก sidebar

**Primary flow — การสร้าง coverage สำหรับสายผลิตภัณฑ์ใหม่:**

1. **ดูแล vendor** Sidebar → **Vendor** → **New** (หรือแก้ vendor ที่มีอยู่) กรอกรหัส, ชื่อ, ประเภทธุรกิจ, ที่อยู่, contact และแถวข้อมูล free-form ใด ๆ Save
2. **สร้าง Price List Template** (ทางเลือก — จำเป็นเฉพาะเมื่อจะเก็บราคาผ่าน RFQ แทนการป้อนโดยตรง) Sidebar → **Price List Template** → **New** กรอก `name`, `vendor_instructions`, default `currency_id`, `validity_period` (วัน), `reminder_days` และคำแนะนำสำหรับ vendor เพิ่มสินค้าผ่าน section **Products** — แต่ละสินค้าได้รับ default order unit และ MOQ-tier definition อย่างน้อยหนึ่งรายการ เก็บเป็น JSON (`order_unit_obj`) Save; เลือกได้ว่าจะพลิก `status` เป็น `active` ผ่าน control status ของ template (`PATCH :id/status` — การเขียน status เปล่า ๆ โดยไม่มี gate ใด ๆ ดังนั้นขั้นนี้ไม่มีผลอะไรนอกเหนือจากค่าฟิลด์เอง)
3. **สร้าง Request for Pricing** เพื่อขอราคา Sidebar → **Request Price List** → **New** เลือก template, ตั้ง `name`/`start_date`/`end_date`/`custom_message` และเพิ่มแถว vendor (vendor + ผู้ติดต่อ/เบอร์โทร/email) คลิก Save — การเรียกครั้งเดียวนี้ทั้งสร้าง RFQ header และสำหรับทุกแถว vendor สร้าง `pricelist_url_token` ที่ unique และ sign JWT ที่ token map ไปถึง ไม่มีขั้นตอน "launch" แยกต่างหาก
4. **Vendor เปิด portal** Token ของแต่ละแถว vendor ประกอบเป็น link `/pl/:url_token` การเข้าชมเรียก portal endpoint จริงตัวเดียวซึ่ง auto-create draft `tb_pricelist` ที่ราคาศูนย์จาก template (หรือ return ตัวที่มีอยู่แล้ว) — ดู [03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor) สำหรับ confirmed gap ของสิ่งที่เกิดขึ้นต่อไป
5. **แก้และ activate pricelist โดยตรง** เนื่องจากการเรียก Save/Submit ของ portal เองไม่ไปถึง backend route ที่ใช้งานได้ในปัจจุบัน เส้นทางที่ใช้งานได้จริงสู่ pricelist ที่ใช้ได้คือให้ Purchaser เปิด draft ที่ auto-create บนหน้า **Price List** โดยตรง กรอกราคาจริงต่อสินค้า/MOQ tier และตั้ง `status = active` จากฟอร์มแก้ไข อีกทางหนึ่งคือข้าม RFQ ไปเลย: Sidebar → **Price List** → **New** เลือก vendor และสกุลเงิน เพิ่มแถว detail และ save ที่ `status = active` โดยตรง — นี่เป็นเส้นทางที่พบบ่อยกว่าสำหรับราคาที่เจรจาทางโทรศัพท์/email แทนที่จะขอผ่าน RFQ อย่างเป็นทางการ
6. **Mark แถว preferred ถ้ามีมากกว่าหนึ่ง vendor เสนอราคาสินค้าเดียวกัน** บน grid **Products** ของ pricelist เอง checkbox `is_preferred` (ไอคอน Crown ในโหมด view) เป็น flag ต่อแถว ตั้งค่าอย่างอิสระบน pricelist ของแต่ละ vendor เอง ไม่มีหน้าจอเปรียบเทียบข้าม vendor — ผลของ flag นี้มองเห็นได้เพียงผ่าน endpoint `price-compare` (`is_preferred desc, price asc`) ซึ่งการตั้งราคา PR/PO ปลายน้ำบริโภคใช้

## 3. สาขาการตัดสินใจ

- **Bulk-load price sheet ของ vendor** หน้า Price List รองรับ CSV import (grouped upsert keyed บน `pricelist_no` พร้อม validation ต่อแถวของ product/unit/vendor/currency) และ upload/download แบบ Excel นอกเหนือจากการป้อนแถวด้วยตนเอง — มีประโยชน์เมื่อ vendor ส่ง spreadsheet มาแทนการใช้ portal
- **การแก้ไข pricelist ที่ active** ไม่มี immutability guard บน pricelist ที่ `active` — Purchaser สามารถแก้แถว detail บน pricelist ที่ active ได้โดยตรง ไม่มีข้อกำหนดให้ inactivate ก่อน ต่างจากกติกาเดิม (ที่ยังไม่ implement) ของเอกสารออกแบบที่ให้ "เปิด pricelist ใหม่"
- **Vendor ไม่สามารถใช้ portal ได้เลย** ตั้งค่า `submission_method = manual` หรือ `email` ของ pricelist โดยตรงบนฟอร์ม Price List และป้อนราคาที่ Purchaser ได้รับทางโทรศัพท์หรือ email — ไม่มีหน้าจอ "upload ในนาม vendor" แยกต่างหากจากฟอร์ม create/edit ปกติ
- **การตัดสินใจว่า vendor ใด preferred สำหรับสินค้า** Toggle `is_preferred` บนแถว pricelist ของ vendor ที่ชนะ ไม่มีสิ่งใดบังคับ "แถว preferred เดียวต่อสินค้า" โดยอัตโนมัติ — Purchaser อาจปล่อยให้ vendor สองรายถูก mark preferred พร้อมกัน ซึ่งในกรณีนั้นการ sort ของ `price-compare` (`is_preferred desc, price asc`) จะเลือกรายที่ราคาต่ำกว่าเป็น `selected`

## 4. จุดออก / Handoff

- **Pricelist active** เมื่อ `tb_pricelist.status = active` แล้ว มัน queryable ได้โดย pricing logic ของ [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) ผ่าน `price-compare` และ endpoint lookup active-pricelist ไม่ต้องมี action เพิ่มเติมจาก Purchaser
- **RFQ ที่ vendor ไม่เคยตอบกลับ** ไม่มี auto-expiry, ไม่มี reminder และไม่มี state "campaign closed" — แถว RFQ และแถว invitation ที่ยังไม่แก้ไขจะคงอยู่ในรายการเฉย ๆ แยกแยะได้เพียงผ่าน `has_submitted = false`

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — ฟิลด์ status จริงและตาราง handoff ข้าม persona ที่ยืนยันแล้ว
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) — status confirmed-vs-design-target ต่อกติกา
- โมเดลข้อมูล: [01-data-model.md](./01-data-model.md) — เอนทิตี, unique key multi-MOQ-per-product บน `tb_pricelist_detail`
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — คู่กรณีภายนอกที่การเข้าชม portal ผลิต draft ที่ Step 5 ของไฟล์นี้แก้ไข
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) / [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — หน้า correction; ไม่มี persona ใดมีอยู่แยกต่างหากจริงในโมดูลนี้
- Cross-link: [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [product](/th/inventory/product)
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`
