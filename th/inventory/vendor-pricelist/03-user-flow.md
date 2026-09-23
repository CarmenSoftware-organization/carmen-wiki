---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow
description: Lifecycle ของเอกสารและไฟล์ flow ตาม persona สำหรับ vendor-pricelist
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow

> **At a Glance**
> **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist) &nbsp;·&nbsp; **Persona:** Purchaser &nbsp;·&nbsp; Vendor (portal ภายนอก — save และ submit ทำงานได้ตั้งแต่ 2026-08/09)
> **หน้าจอจริง:** Vendor, Certification, Price List, Price List Template, Request for Pricing (RFQ) — ห้าหน้า CRUD อิสระ ไม่มี workspace รวม ไม่มี workflow engine
> **Re-sync 2026-09-22:** route Save/Submit ของ portal มีอยู่และผลิต pricelist `submitted`; ลิงก์หมดอายุที่ `end_date` ของ RFQ; RFQ มี action Send-email ต่อ vendor; Certification ย้ายมาใต้ Vendor Management
> **ตรวจสอบเมื่อ 2026-07-16:** Finance และ Audit/Config ไม่ใช่ persona แยกต่างหากในโมดูลนี้ — ดู [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) และ [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config)

## 1. ภาพรวม

หน้านี้เป็นจุดเข้า overview สำหรับชุด user-flow ของโมดูล `vendor-pricelist` Vendor pricelist (`tb_pricelist` header + แถว `tb_pricelist_detail`) สามารถสร้างได้สองทาง: **โดยตรง** โดย Purchaser (การป้อนด้วยตนเอง, CSV import หรือ Excel upload บนหน้า Price List) หรือ **ผ่าน Request for Pricing (RFQ)** — Purchaser เลือก [Price List Template](/th/inventory/vendor-pricelist/request-price-list) และระบุ vendor cohort ในการเรียก create เดียว ซึ่งสร้าง `pricelist_url_token` cryptographic หนึ่งตัวต่อ vendor ที่เชิญทันที Vendor แต่ละรายสามารถเปิด `/pl/:url_token` ซึ่งเป็น external portal; การเข้าชมจะ auto-create draft pricelist ที่ราคาศูนย์จาก template vendor ตั้งราคาสินค้าของ template บันทึก draft และ submit — pricelist กลายเป็น `submitted` และ Purchaser activate บนหน้าจอ Price List ภายใน นี่คือ "workflow" ทั้งหมดที่โค้ดของโมดูลนี้ implement — ไม่มีขั้นตอน campaign-launch, ไม่มี reminder schedule, ไม่มี quality scoring และไม่มี action approve/reject; การส่งลิงก์เป็น **Send email** แบบ manual ต่อ vendor

Section 2 ด้านล่างระบุฟิลด์ status จริงและสิ่งที่เปลี่ยนค่ามันจริง ๆ Section 3 link ไฟล์ persona สองไฟล์ที่สะท้อนพฤติกรรมจริง (Purchaser, Vendor) Section 4 ระบุ handoff ข้าม persona ที่ยืนยันแล้ว หน้าเวอร์ชันก่อนหน้าอธิบายกระบวนการเก็บข้อมูล 6-phase (vendor setup → template → campaign → invitation → portal submission → validation) ขับเคลื่อนโดย status machine สามตัวที่ derive ระดับแอป (template / campaign / invitation) บวก gate การ approve ของ Manager และ Finance-Manager — ไม่มีกลไก state ใดในนั้นเลยที่มีโค้ดตรงกัน ยกเว้นสอง enum ที่ backed ด้วย Prisma จริงตามที่ระบุด้านล่าง

## 2. ฟิลด์ Status จริง

| Table | Field | ค่า | สิ่งที่เปลี่ยนค่ามัน |
| ----- | ----- | ------ | ---------------- |
| `tb_pricelist_template` | `status` | `draft`, `active`, `inactive` (`enum_pricelist_template_status`) | Control status ของฟอร์มแก้ไข template หรือการเรียก `PATCH :id/status` โดยตรง — ไม่ว่าทางใด เป็นการเขียนฟิลด์เปล่า ๆ โดยไม่มี validation gate (ไม่มีการตรวจ "ต้องมีสินค้า ≥1" ไม่มี re-activation guard) |
| `tb_request_for_pricing` | *(ไม่มี)* | — | ไม่มีคอลัมน์ status และไม่มี state ที่ derive ที่ใดในโค้ด สัญญาณต่อ vendor ที่ใกล้เคียงที่สุดคือ `has_submitted: !!pricelist_id` บนแต่ละแถว invitation |
| `tb_pricelist` | `status` | `draft`, `submitted`, `active`, `inactive`, `expired` (`enum_pricelist_status`) | Control status ของฟอร์มแก้ไข Price List (ผ่านการเรียก update ปกติ — ไม่มี transition guard, ไม่มี action approve/reject, `expired` ไม่เคยถูก assign) **หรือ** Submit บน portal ของ vendor (`draft → submitted`) ขอบ `draft → submitted` stamp `submitted_at` และลบแถวที่ไม่มีราคา |
| External portal | `tb_pricelist.status`, `submitted_at`; event ใน `tb_activity` | `draft` → `submitted` | `POST /api/check-pricelist/:url_token` auto-create หรือ return draft; `PATCH /api/pricelist-external/:url_token` บันทึกการแก้ไข (ยังคง `draft`); `POST …/submit` ตั้ง `submitted` ทั้งสามอยู่หลัง `UrlTokenGuard` (401 หลัง `end_date` ของ RFQ) event `create` / `save` / `submit` ถูก log ลง `tb_activity` |

## 3. Index ของ Persona

- [Purchaser](./03-user-flow-purchaser.md) — persona ภายในเดียวที่มี write surface: ดูแล Vendor master data และ Certification master, สร้าง/แก้ Price List Template และ Price List โดยตรง, สร้าง RFQ และส่ง email ลิงก์ให้ vendor แต่ละราย และ activate pricelist `submitted` ที่ vendor ส่งกลับมา (หรือคีย์ sheet จาก email/CSV เข้า)
- [Vendor](./03-user-flow-vendor.md) — บุคคลภายนอกที่ไม่มี Carmen login เปิดลิงก์ portal จาก email ก่อนหมดอายุ ตั้งราคาสินค้า (tax profile และ order unit ต่อบรรทัด) save, import sheet Excel ถ้าต้องการ และ submit

โน้ต: **Finance** และ **Audit / Config** เคยถูกบันทึกเป็น persona แยกต่างหากใน draft ก่อนหน้า ทั้งสองไม่มีโค้ดตรงกันในโมดูลนี้เลย — ดู [03-user-flow-finance.md](./03-user-flow-finance.md) และ [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) ทั้งสองถูกเขียนใหม่เป็นหน้า correction ในรอบนี้

## 4. Handoff ข้าม Persona

| จาก persona | Trigger | ไป persona | ยืนยันแล้วหรือไม่? |
| ------------ | ------- | ---------- | ---------- |
| Purchaser | สร้าง RFQ ที่ระบุ template + vendor cohort | Vendor | **Confirmed** — การเรียก `create()` ครั้งเดียวสร้าง invitation token ทั้งหมด (และแถว `tb_shot_url` ที่หมดอายุที่ `end_date`) พร้อมกัน |
| Purchaser | **Send email** บนแถว vendor | Vendor | **Confirmed** — `POST …/request-for-pricings/:id/send-email` ผ่าน email profile; activity `email_sent` |
| Vendor | เปิด link portal | (auto) | **Confirmed** — `check-pricelists.check` auto-create/return draft pricelist (401 เมื่อลิงก์หมดอายุ) |
| Vendor | Save / Submit บน portal | Purchaser | **Confirmed (gap ปิดแล้ว)** — `saveDraft()` คง `draft`; `submit()` ตั้ง `submitted`, stamp `submitted_at`, ตัดแถวที่ไม่มีราคา; แถว vendor ของ RFQ แสดง `has_submitted = true` และสถานะของ pricelist |
| Purchaser | Review pricelist ที่ `submitted` และตั้ง `status = active` บนหน้า Price List | (terminal — pricelist live) | **Confirmed** — ไม่มี endpoint approve; control สถานะบนฟอร์มแก้ไขคือการมอบ |
| Purchaser | เลือกแถว preferred (checkbox `is_preferred` บนแถว detail ของ pricelist ตัวเอง) | (ป้อนเข้า `price-compare`) | **Confirmed** — ฟิลด์ต่อแถวจริง, endpoint เปรียบเทียบจริง; ไม่ใช่หน้าจอ matrix ข้าม vendor |

ทุก flow ข้าม persona ที่เกี่ยวข้องกับ gate การ approve ของ Manager, co-signoff ของ Finance Manager, การ revoke token ของ Sysadmin, cron auto-expiry หรือ audit query workspace ถูกลบออกจากตารางนี้แล้ว — ไม่มีตัวใดมีโค้ดตรงกันเลย (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) สำหรับหลักฐาน)

## 5. แหล่งอ้างอิง

- Sibling: [01-data-model.md](./01-data-model.md) — การอ้างอิงเอนทิตี / enum canonical
- Sibling: [02-business-rules.md](./02-business-rules.md) — ตาราง confirmed-vs-design-target ที่ข้อกล่าวอ้างของหน้านี้อ้างอิงมา
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`, `routes/external/pl/`
- โมดูลที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [product](/th/inventory/product)
