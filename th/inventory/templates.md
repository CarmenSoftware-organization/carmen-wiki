---
title: เทมเพลต (Templates)
description: นิยาม scaffold ที่ใช้ซ้ำได้สำหรับ PR และ Vendor Pricelist — กลไกร่วมของเอกสาร seed-only ที่ pre-fill record transactional ใหม่ตอน instantiate
published: true
date: 2026-06-09T16:28:56.000Z
tags: templates, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T16:00:00.000Z
---

# เทมเพลต (Templates)

> **At a Glance**
> **จุดประสงค์ของโมดูล:** scaffold แบบ seed-only (PR draft, รอบ RFQ / pricelist) ที่ deep-copy header และ detail row ลงใน record transactional ใหม่ตอน instantiate &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Requestor (PR), Purchaser (pricelist), Sysadmin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_purchase_request_template`, `tb_pricelist_template` &nbsp;·&nbsp; **หน้าย่อย:** 2

![เทมเพลต (Templates) screen](/screenshots/templates/purchase-request.png)

![เทมเพลต (Templates) detail screen](/screenshots/templates/purchase-request-detail.png)

## 1. ภาพรวม

เทมเพลตใน Carmen เป็นเอกสาร *seed-only* — ตัวเองไม่เคยเข้า workflow หรือ post ไปยัง ledger ใด ๆ จุดประสงค์คือ pre-fill record transactional ใหม่ (PR draft, รอบ RFQ pricelist) ด้วยค่า header และ detail row ที่ผู้ปฏิบัติงานต้องกรอกใหม่ทุกครั้ง เมื่อผู้ใช้เลือก **Create from Template** ฟิลด์ที่เกี่ยวข้องจะถูก clone ไปยัง record draft ใหม่ จากจุดนั้นเป็นต้นไป record ใหม่จะเป็นอิสระและเทมเพลตไม่ถูกเปลี่ยน

## 2. กลไกที่ใช้ร่วมกัน

พฤติกรรมด้านล่างใช้กับเทมเพลตทุกตัวแปรในระบบ:

- **การคงอยู่แบบ Seed-only** ตาราง template (`tb_purchase_request_template`, `tb_pricelist_template`) มี primary key และ audit column ของตัวเอง แต่ไม่เคยถูกอ้างเป็น parent โดย record transactional
- **Clone semantics** การ instantiate deep-copy header และ detail row ลงใน record transactional ใหม่ การแก้ template ภายหลัง **ไม่** propagate ไปยัง record ที่สร้างไปแล้ว
- **Lifecycle** `draft` (แก้ได้ ยังไม่เลือกได้ใน picker) → `active` (เลือกได้ตอนสร้าง record ใหม่) → `inactive` (ถูกถอนจาก picker ใหม่ ยังอ่านได้บน record เก่า)
- **Soft-delete + audit column** ใช้ convention เดียวกับตาราง config อื่น — `created_*`, `updated_*`, `deleted_*` มีอยู่ และ hard-delete ถูกบล็อกเมื่อ template ถูกใช้อย่างน้อย 1 ครั้ง
- **Currency / workflow snapshot** เมื่อ template มีการอ้าง currency, workflow หรือ tax profile ค่าเหล่านั้น resolve เป็น config *ปัจจุบัน* ตอน clone การเปลี่ยนบน template ภายหลังกระทบเฉพาะ clone ในอนาคต

## 3. หน้าในโมดูลนี้

- [templates/purchase-request](/th/inventory/templates/purchase-request) — scaffold PR ที่ clone ผ่าน "Create PR from Template" ใน UI procurement
- [templates/price-list](/th/inventory/templates/price-list) — scaffold RFQ / pricelist ที่นิยาม currency, validity, ตารางการเตือน และกฎการ escalate

## 4. โมดูลที่เกี่ยวข้อง

- [purchase-request](/th/inventory/purchase-request) — ผู้บริโภคหลักของ PR template (Requestor persona, scenario REQ-HP-06)
- [vendor-pricelist](/th/inventory/vendor-pricelist) — ผู้บริโภคหลักของ pricelist template (Purchaser เริ่มรอบ RFQ)
- [system-config/workflow](/th/inventory/system-config/workflow) — การ assign workflow ที่ติดมากับ PR template
- [master-data/currency](/th/inventory/master-data/currency) — currency ที่ resolve บน pricelist template

## 5. แหล่งข้อมูลอ้างอิง

- `../carmen-inventory-frontend-react/routes/procurement/purchase-request-template/` — หน้า frontend ของ PR template
- `../carmen-inventory-frontend-react/routes/vendor-management/price-list-template/` — หน้า frontend ของ Pricelist template
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — flow การสร้าง PR จาก template
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template`, `tb_pricelist_template`
