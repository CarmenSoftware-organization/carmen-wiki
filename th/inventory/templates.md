---
title: เทมเพลต (Templates)
description: นิยาม scaffold ที่ใช้ซ้ำได้สำหรับ PR และ Vendor Pricelist — สองวิธี implement ที่ต่างกันโดยโครงสร้าง ไม่ใช่กลไกร่วมเดียว แม้ทั้งคู่จะ prefill record ใหม่ตอนเลือกใช้
published: true
date: 2026-07-29T04:21:35.000Z
tags: templates, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T16:00:00.000Z
---

# เทมเพลต (Templates)

> **At a Glance**
> **จุดประสงค์ของโมดูล:** scaffold ที่ใช้ซ้ำได้ (PR line-bundle, รอบ RFQ pricelist) ที่ prefill ฟิลด์ของ record ใหม่ตอนเลือกใช้ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Requestor (PR), Product Admin / Procurement Lead (pricelist), Product Admin (ดูแล PR template) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_purchase_request_template` (+ detail, comment), `tb_pricelist_template` (+ detail, comment) &nbsp;·&nbsp; **หน้าย่อย:** 2

![เทมเพลต (Templates) screen](/screenshots/templates/purchase-request.png)

![เทมเพลต (Templates) detail screen](/screenshots/templates/purchase-request-detail.png)

> **สถานะการ implement (ตรวจสอบ 2026-07-29):** เทมเพลตสองตัวในโมดูลนี้ **ไม่ได้** สร้างด้วยวิธีเดียวกัน แม้ผิวเผินจะดูคล้ายกัน ("เลือก template แล้วได้ record ที่ prefill แล้ว") PR template ไม่ deep-clone อะไรเลย — การเลือก template แค่ prefill ฟอร์ม PR ใหม่ฝั่ง client และ PR ที่ได้ไม่มี link กลับไปยัง template Pricelist template เก็บ FK ที่ persist จริง (`tb_request_for_pricing.pricelist_template_id`) จากทุกรอบ RFQ ที่ออกอิงกับมัน กลไก Delete ก็ต่างกันด้วย: PR template delete แบบ hard delete ไม่มีเงื่อนไข; pricelist template delete แบบ soft delete ไม่มีเงื่อนไข ดู callout สถานะการ implement ของแต่ละหน้าย่อยสำหรับรายละเอียดเต็ม — หน้านี้ไม่ยืนยันกลไกเดียวสำหรับทั้งคู่อีกต่อไป

## 1. ภาพรวม

เทมเพลตใน Carmen เป็น configuration ไม่ใช่เอกสาร transactional — ทั้งสองแบบไม่เข้า workflow หรือ post ไปยัง ledger เอง จุดประสงค์คือ prefill record transactional ใหม่ (PR draft, รอบ RFQ pricelist) ด้วยค่าที่ผู้ปฏิบัติงานต้องกรอกใหม่ทุกครั้ง นอกเหนือจากจุดประสงค์ร่วมนี้ ทั้งสอง implementation ต่างกันในแบบที่หน้านี้เอกสารไว้ตรง ๆ แทนที่จะกลบเกลื่อน: record ใหม่เก็บ link กลับไปยัง template หรือไม่, delete เป็น hard หรือ soft, และ "lifecycle" เป็น boolean เดียวหรือ enum status จริง

## 2. กลไกที่ใช้ร่วมกัน

สิ่งที่จริง ๆ ใช้ร่วมกันทั้งสองแบบ:

- **ไม่ post ไปที่ไหนเลย** ไม่มีผลต่อ GL, AP, หรือ inventory จากการสร้าง แก้ไข หรือลบ template ไม่ว่าแบบไหน
- **ไม่มีส่วนใน workflow** ไม่มี `doc_status`, ไม่มี `workflow_current_stage`, ไม่มี approval chain บน row ของ template เอง
- **ทั้งคู่มี audit column มาตรฐาน** (`created_*`, `updated_*`, `deleted_*`) และตัวนับ optimistic-lock `doc_version` บน header
- **ทั้งคู่มี Name-uniqueness และ CRUD ผ่าน route เฉพาะ** (`/procurement/purchase-request-template`, `/vendor-management/price-list-template`) พร้อมหน้า list/detail/new

สิ่งที่ **ไม่** ใช้ร่วมกัน — ดูรายละเอียดในหน้าย่อยทั้งสอง:

| | PR Template | Price List Template |
|---|---|---|
| กลไกการสร้าง instance | prefill ฟอร์มฝั่ง client เท่านั้น (ไม่มี backend clone endpoint) | ไม่มี — template ไม่ถูก "instantiate"; รอบ RFQ อ้างมันผ่าน FK |
| link จาก record ใหม่/ที่สร้างจากมันกลับไปยัง template | ไม่มี — ไม่มีคอลัมน์ `created_from_template_id` หรือเทียบเท่าที่ไหนเลย | มีจริง — `tb_request_for_pricing.pricelist_template_id` persist |
| ฟิลด์ lifecycle | boolean เดียว `is_active` ไม่มี state "draft" | enum 3 ค่าจริง `status` (`draft`/`active`/`inactive`) |
| กลไก Delete | **hard delete** แบบไม่มีเงื่อนไข ไม่มี usage guard | **soft delete** แบบไม่มีเงื่อนไข (`status = inactive` + `deleted_at`) ไม่มี usage guard |
| เนื้อหา line/detail | Location, product, unit, qty, currency เท่านั้น — tax/discount/FOC/dimension เป็น schema-only | MOQ tier ต่อสินค้า (`order_unit_obj` JSON array) — payload จริงของโมดูลนี้ |

## 3. หน้าในโมดูลนี้

- [templates/purchase-request](/th/inventory/templates/purchase-request) — scaffold line-bundle ของ PR ที่ prefill ลงใน PR ใหม่ผ่าน "Create PR from Template" ใน UI procurement
- [templates/price-list](/th/inventory/templates/price-list) — scaffold RFQ / pricelist ที่นิยาม currency, validity, คำแนะนำ vendor, และรายการสินค้า/MOQ; `reminder_days`/`escalation_after_days` มีอยู่บนตารางแต่ไม่มีผลจริง (ไม่มี UI ไม่มี job อ่านมัน)

## 4. โมดูลที่เกี่ยวข้อง

- [purchase-request](/th/inventory/purchase-request) — ผู้บริโภคของ PR template (Requestor persona, scenario REQ-HP-06)
- [vendor-pricelist](/th/inventory/vendor-pricelist) — ผู้บริโภคของ pricelist template; รอบ RFQ (Request for Pricing) เก็บ FK `pricelist_template_id` แบบ persist
- [system-config/workflow](/th/inventory/system-config/workflow) — การ assign workflow ที่ติดมากับ PR template (`workflow_id`)
- [master-data/currency](/th/inventory/master-data/currency) — currency ถูกตรวจแค่ว่ามีอยู่ (ไม่ตรวจ `is_active`) บน pricelist template

## 5. แหล่งข้อมูลอ้างอิง

- `../carmen-inventory-frontend-react/routes/procurement/purchase-request-template/` — frontend ของ PR template (`prt-form.tsx`, `prt-form-schema.ts`, `prt-item-table.tsx`)
- `../carmen-inventory-frontend-react/routes/vendor-management/price-list-template/` — frontend ของ Pricelist template (`plt-form.tsx`, `plt-form-schema.ts`, `plt-form-products-section.tsx`)
- `../carmen-inventory-frontend-react/routes/procurement/purchase-request/new-purchase-request-content.tsx` + `pr-form-schema.ts` — จุดที่ฟิลด์ของ PR template ถูก merge เข้า PR ใหม่จริง ๆ
- `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request-template/purchase-request-template.service.ts` — data layer จริงของ PR-template (Prisma โดยตรง)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/master/price-list-template/price-list-template.service.ts` — data layer จริงของ pricelist-template (Prisma โดยตรง); `apps/backend-gateway/src/application/pricelist-templates/` เป็นแค่ TCP proxy บาง ๆ อยู่หน้ามัน
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (+detail/comment, บรรทัด 2635-2797), `tb_pricelist_template` (+detail/comment, บรรทัด 4222-4360), `tb_request_for_pricing` (บรรทัด 4400-4429)
- `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts`, `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — E2E spec; ทั้งคู่มี `describe` block สำหรับฟีเจอร์ที่ไม่มีในโค้ดปัจจุบัน (PR template "Clone"/"Set as Default"; pricelist template ที่ Clone ถูกถอดออกแล้ว ยืนยันด้วย suite "(removed)" ของมันเอง)
