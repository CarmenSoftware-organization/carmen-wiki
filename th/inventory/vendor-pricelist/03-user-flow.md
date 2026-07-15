---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow
description: Lifecycle ของเอกสารและไฟล์ flow ตาม persona สำหรับ vendor-pricelist
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow

> **At a Glance**
> **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist) &nbsp;·&nbsp; **Persona:** Purchaser &nbsp;·&nbsp; Vendor (external, เส้นทาง submit ที่ยืนยันว่าใช้งานไม่ได้)
> **หน้าจอจริง:** Vendor, Price List, Price List Template, Request for Pricing (RFQ) — สี่หน้า CRUD อิสระ ไม่มี workspace รวม ไม่มี workflow engine
> **ตรวจสอบเมื่อ 2026-07-16:** Finance และ Audit/Config ไม่ใช่ persona แยกต่างหากในโมดูลนี้ — ดู [03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) และ [03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config)

## 1. ภาพรวม

หน้านี้เป็นจุดเข้า overview สำหรับชุด user-flow ของโมดูล `vendor-pricelist` Vendor pricelist (`tb_pricelist` header + แถว `tb_pricelist_detail`) สามารถสร้างได้สองทาง: **โดยตรง** โดย Purchaser (การป้อนด้วยตนเอง, CSV import หรือ Excel upload บนหน้า Price List) หรือ **ผ่าน Request for Pricing (RFQ)** — Purchaser เลือก [Price List Template](/th/inventory/vendor-pricelist/request-price-list) และระบุ vendor cohort ในการเรียก create เดียว ซึ่งสร้าง `pricelist_url_token` cryptographic หนึ่งตัวต่อ vendor ที่เชิญทันที Vendor แต่ละรายสามารถเปิด `/pl/:url_token` ซึ่งเป็น external portal; การเข้าชมจะ auto-create draft pricelist ที่ราคาศูนย์จาก template นี่คือ "workflow" ทั้งหมดที่โค้ดของโมดูลนี้ implement จริง — ไม่มีขั้นตอน campaign-launch, ไม่มี reminder schedule, ไม่มี quality scoring และ (ตาม confirmed gap ด้านล่าง) ไม่มีวิธีที่ใช้งานได้จริงให้ vendor save หรือ submit ผ่าน portal นั้นในปัจจุบัน

Section 2 ด้านล่างระบุฟิลด์ status จริงและสิ่งที่เปลี่ยนค่ามันจริง ๆ Section 3 link ไฟล์ persona สองไฟล์ที่สะท้อนพฤติกรรมจริง (Purchaser, Vendor) Section 4 ระบุ handoff ข้าม persona ที่ยืนยันแล้ว หน้าเวอร์ชันก่อนหน้าอธิบายกระบวนการเก็บข้อมูล 6-phase (vendor setup → template → campaign → invitation → portal submission → validation) ขับเคลื่อนโดย status machine สามตัวที่ derive ระดับแอป (template / campaign / invitation) บวก gate การ approve ของ Manager และ Finance-Manager — ไม่มีกลไก state ใดในนั้นเลยที่มีโค้ดตรงกัน ยกเว้นสอง enum ที่ backed ด้วย Prisma จริงตามที่ระบุด้านล่าง

## 2. ฟิลด์ Status จริง

| Table | Field | ค่า | สิ่งที่เปลี่ยนค่ามัน |
| ----- | ----- | ------ | ---------------- |
| `tb_pricelist_template` | `status` | `draft`, `active`, `inactive` (`enum_pricelist_template_status`) | Control status ของฟอร์มแก้ไข template หรือการเรียก `PATCH :id/status` โดยตรง — ไม่ว่าทางใด เป็นการเขียนฟิลด์เปล่า ๆ โดยไม่มี validation gate (ไม่มีการตรวจ "ต้องมีสินค้า ≥1" ไม่มี re-activation guard) |
| `tb_request_for_pricing` | *(ไม่มี)* | — | ไม่มีคอลัมน์ status และไม่มี state ที่ derive ที่ใดในโค้ด สัญญาณต่อ vendor ที่ใกล้เคียงที่สุดคือ `has_submitted: !!pricelist_id` บนแต่ละแถว invitation |
| `tb_pricelist` | `status` | `draft`, `active`, `inactive`, `expired` (`enum_pricelist_status`) | Control status ของฟอร์มแก้ไข Price List ผ่านการเรียก update ปกติ — ข้อจำกัดเดียวกัน: ไม่มี transition guard, ไม่มี action approve/reject/submit แยกต่างหาก, ไม่มี cron auto-expire ใน repo นี้ |
| External portal | *(ไม่มีอะไร persist โดยตัว portal เอง)* | — | `POST /api/check-pricelist/:url_token` auto-create หรือ return draft pricelist ปุ่ม Save/Submit ของ portal เอง เรียก route (`PATCH`/`POST .../pricelist-external/:token[/submit]`) ที่ไม่มีอยู่จริงในฝั่ง backend — ยืนยันโดยการค้นหาทั้ง repo ที่ไม่พบ `pricelist-external` เลยนอกเหนือจากไฟล์ endpoint-constant ของ frontend เอง |

## 3. Index ของ Persona

- [Purchaser](./03-user-flow-purchaser.md) — persona ภายในเดียวที่มี write surface: ดูแล Vendor master data, สร้าง/แก้ Price List Template และ Price List โดยตรง, สร้าง RFQ และแก้/activate draft ใดก็ตามที่การเข้าชม portal ของ vendor (หรือ submission ทาง email/CSV) สร้างขึ้น
- [Vendor](./03-user-flow-vendor.md) — บุคคลภายนอกที่ไม่มี Carmen login เปิด link portal; portal auto-create draft การเรียก Save/Submit ของ portal ยืนยันแล้วว่าเสียกับ backend ปัจจุบัน

โน้ต: **Finance** และ **Audit / Config** เคยถูกบันทึกเป็น persona แยกต่างหากใน draft ก่อนหน้า ทั้งสองไม่มีโค้ดตรงกันในโมดูลนี้เลย — ดู [03-user-flow-finance.md](./03-user-flow-finance.md) และ [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) ทั้งสองถูกเขียนใหม่เป็นหน้า correction ในรอบนี้

## 4. Handoff ข้าม Persona

| จาก persona | Trigger | ไป persona | ยืนยันแล้วหรือไม่? |
| ------------ | ------- | ---------- | ---------- |
| Purchaser | สร้าง RFQ ที่ระบุ template + vendor cohort | Vendor | **Confirmed** — การเรียก `create()` ครั้งเดียวสร้าง invitation token ทั้งหมดพร้อมกัน |
| Vendor | เปิด link portal | (auto) | **Confirmed** — `check-pricelists.check` auto-create/return draft pricelist |
| Vendor | พยายาม Save / Submit บน portal | (ไม่มีใคร — การเรียกล้มเหลว) | **Confirmed gap** — route เป้าหมายไม่มีอยู่จริงในฝั่ง backend |
| Purchaser | แก้และ activate draft ที่ auto-create โดยตรงบนหน้า Price List | (terminal — pricelist live) | **Confirmed** — นี่คือเส้นทางจริงสู่ pricelist ที่ `active` ซึ่ง source มาจาก RFQ ในปัจจุบัน เพราะตัว portal เองไม่สามารถ persist ได้ |
| Purchaser | เลือกแถว preferred (checkbox `is_preferred` บนแถว detail ของ pricelist ตัวเอง) | (ป้อนเข้า `price-compare`) | **Confirmed** — ฟิลด์ต่อแถวจริง, endpoint เปรียบเทียบจริง; ไม่ใช่หน้าจอ matrix ข้าม vendor |

ทุก flow ข้าม persona ที่เกี่ยวข้องกับ gate การ approve ของ Manager, co-signoff ของ Finance Manager, การ revoke token ของ Sysadmin, cron auto-expiry หรือ audit query workspace ถูกลบออกจากตารางนี้แล้ว — ไม่มีตัวใดมีโค้ดตรงกันเลย (ดู [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) สำหรับหลักฐาน)

## 5. แหล่งอ้างอิง

- Sibling: [01-data-model.md](./01-data-model.md) — การอ้างอิงเอนทิตี / enum canonical
- Sibling: [02-business-rules.md](./02-business-rules.md) — ตาราง confirmed-vs-design-target ที่ข้อกล่าวอ้างของหน้านี้อ้างอิงมา
- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/`, `routes/external/pl/`
- โมดูลที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [product](/th/inventory/product)
