---
title: คำขอใบเสนอราคา (Request for Quotation)
description: เอกสารคำขอราคา outbound (RFQ) ส่งไปยังผู้ขายหนึ่งรายหรือมากกว่า — เก็บการเสนอราคาก่อนเจรจาต่อรอง pricelist ใหม่
published: true
date: 2026-05-17T07:00:36.000Z
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# คำขอใบเสนอราคา (Request for Quotation)

> **At a Glance**
> **เจ้าของ:** Purchaser / Procurement Manager &nbsp;·&nbsp; **ตาราง:** `tb_request_for_pricing` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** ไม่มี (ขับด้วย date-window) &nbsp;·&nbsp; **ต้นน้ำ:** [[templates/price-list]] &nbsp;·&nbsp; ขอใบเสนอราคาจากผู้ขายก่อนได้รับการมอบ `tb_pricelist`

![คำขอใบเสนอราคา (Request for Quotation) screen](/assets/screenshots/vendor-pricelist/request-price-list.png)

## 1. ภาพรวมและผู้ใช้งาน

**Request for Pricing (RFQ)** คือเอกสาร outbound ที่ procurement-initiate ขอใบเสนอราคาจากผู้ขายหนึ่งรายหรือมากกว่าก่อน [[vendor-pricelist]] ได้รับการมอบ ผู้ซื้อหยิบ [[templates/price-list]] (ซึ่ง carry สกุลเงิน, validity window, schedule reminder และแคตตาล็อกสินค้าที่อยู่ใต้การ quote), ตั้งชื่อผู้ขาย candidate และ dispatch คำขอ ผู้ขายที่เชิญแต่ละรายได้ **link ที่ tokenise** ไปยัง portal ที่พวกเขา submit ราคา; submission ลงเป็นแถว `tb_pricelist` draft keyed กลับไปยัง RFQ หลัง deadline ผู้ซื้อเปรียบเทียบการเสนอราคาและ *มอบ* หนึ่ง (หรือหลาย) โดย flip สถานะของมันเป็น `active`

**สร้างโดย** Purchaser / Procurement Manager &nbsp;·&nbsp; **ตอบกลับโดย** ผู้ขายที่เชิญ (ไม่มี login — portal scope ด้วย token) &nbsp;·&nbsp; **ไม่ผลิตผลกระทบ inventory หรือ AP**

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง RFQ จาก template | Vendor Management → Request Price List → **New** | Template ผูกสกุลเงิน + แคตตาล็อกสินค้า |
| เชิญผู้ขาย | Detail → **Add Vendor** | หนึ่งแถวต่อ (RFQ, vendor); unique constraint บังคับไม่ให้เชิญซ้ำ |
| ส่ง / ส่งซ้ำ invitation email | Detail → **Send** | Idempotent — ใช้ `pricelist_url_token` ที่มีอยู่ซ้ำ |
| ขยาย deadline | Header → แก้ `end_date` | บันทึก audit; ต้องการเพื่อรับการเสนอราคาสาย |
| เปรียบเทียบการเสนอราคา | Detail → **Compare** | Normalise เป็นสกุลเงินฐาน BU ผ่าน [[master-data/exchange-rate]] |
| มอบ pricelist | แถว Pricelist → **Activate** | Flip `enum_pricelist_status` เป็น `active` — RFQ เองไม่มีสถานะ "awarded" |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Vendor already invited" | มีแถว detail ที่ไม่ถูกลบสำหรับ (RFQ, vendor) | แก้ invitation ที่มีอยู่แทน |
| "end_date must be after start_date" | Date window ไม่ถูกต้อง | re-pick deadline |
| "Cannot change template — invitations sent" | `pricelist_template_id` immutable หลัง dispatch | Cancel RFQ และเริ่มใหม่ |
| "Late submission rejected" | Portal POST หลัง `end_date` | ขยาย `end_date` ก่อน (บันทึก audit) ก่อน re-send |
| "Vendor must be active" | `tb_vendor.is_active = false` | Reactivate ภายใต้ [[master-data/vendor]] |
| Invitation link 404 | `pricelist_url_token` rotate หรือแถว soft-delete | Re-issue invitation; token ใหม่ generate |

## 4. กรณีพิเศษ

- **ความปลอดภัย Token** `pricelist_url_token` เป็น string สุ่มยาวต่อ invitation; การเข้า portal scope โดย token **เพียงผู้เดียว** (vendor ไม่ authenticate) การ rotate token invalidate invitation ที่ค้างทั้งหมดสำหรับ vendor นั้น
- **การ submission สาย reject** การ insert `tb_pricelist` หลัง `end_date` ถูก reject ที่ชั้น API ผู้ซื้อต้องขยาย `end_date` อย่างชัดเจนก่อนปิดเพื่อรับการเสนอราคาเพิ่ม
- **การมอบเป็นการ flip ระดับ pricelist ไม่ใช่ระดับ RFQ** RFQ ไม่มีสถานะระบบ "awarded" — การมอบ = การ flip `tb_pricelist` ที่เลือกเป็น `active` Pricelist หลายตัวอาจ active ต่อสินค้า (split award)
- **Cascade สกุลเงิน** RFQ inherit สกุลเงินจาก template; vendor ไม่สามารถ override ต่อบรรทัด RFQ ข้ามสกุลเงินต้องการ **รอบแยกต่อสกุลเงิน**
- **Dispatch Idempotent** การส่ง invitation ซ้ำใช้ token ที่มีอยู่ซ้ำ; ไม่มี `tb_pricelist` ใหม่สร้าง
- **Snapshot semantic** ชื่อ vendor, contact และฟิลด์ template ถูก snapshot ที่เวลา invitation การแก้ master-record ไม่เปลี่ยนแถว RFQ ย้อนหลัง
- **ไม่มี workflow engine** RFQ ไม่มีคอลัมน์ `workflow_*`; lifecycle ขับด้วย date-window + pricelist-status ล้วน ๆ

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_request_for_pricing`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดง RFQ (เช่น "Q2-2026 Beverage RFQ") |
| `pricelist_template_id` | `String @db.Uuid` | No | FK ไป [[templates/price-list]] Carry สกุลเงิน, validity, reminder, แคตตาล็อก |
| `start_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่ vendor อาจเริ่ม submit |
| `end_date` | `DateTime? @db.Timestamptz(6)` | Yes | Deadline การ submission; ขับ reminder |
| `custom_message` | `String? @db.Text` | Yes | ข้อความอิสระ render ในอีเมล invitation |
| `email_template_id` | `String? @db.VarChar` | Yes | Identifier สำหรับ invitation / reminder mail |
| `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `request_for_pricing_name_u`; `@@index([pricelist_template_id])`; `@@index([name])` FK ไป `tb_pricelist_template` `onDelete: NoAction`

### 5.2 `tb_request_for_pricing_detail`

หนึ่งแถวต่อ vendor ที่เชิญ

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `request_for_pricing_id`, `sequence_no` | mixed | No / No / Yes | PK, FK parent, ordinal |
| `vendor_id`, `vendor_name` | `String @db.Uuid` / `VarChar` | No / Yes | Vendor ที่เชิญ + snapshot |
| `contact_person`, `contact_phone`, `contact_email` | `String? @db.VarChar` | Yes | Contact ฝั่ง vendor สำหรับรอบนี้ |
| `pricelist_id`, `pricelist_no` | `String? @db.Uuid` / `VarChar` | Yes | FK ไป `tb_pricelist` ที่สร้างตอน submission — null จนกว่า |
| `pricelist_url_token` | `String? @db.VarChar` | Yes | Fragment URL ที่ tokenise สำหรับ portal invitation |
| `comment`, `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([request_for_pricing_id, vendor_id, deleted_at])` — หนึ่ง invitation ต่อ (RFQ, vendor); `@@index([request_for_pricing_id, vendor_id])` FK ไป `tb_request_for_pricing`, `tb_vendor`, `tb_pricelist` — ทั้งหมด `onDelete: NoAction`

### 5.3 ตาราง Comment

`tb_request_for_pricing_comment` และ `tb_request_for_pricing_detail_comment` ตามรูปร่าง comment canonical

## 6. Workflow / กติกาทางธุรกิจ

RFQ **ไม่** ใช้ generic workflow engine Lifecycle ขับด้วย date window และ state ของ `tb_pricelist` ลูก:

- **Setup** — RFQ สร้างจาก template; เพิ่มแถว vendor detail ยังไม่ส่ง invitation
- **Invitation sent** — แต่ละแถว detail ได้ `pricelist_url_token`; email dispatch ผ่าน `email_template_id`
- **Open for response** (`start_date <= now < end_date`) — vendor submit ผ่าน portal; แต่ละ submission สร้าง `tb_pricelist` ใน `draft`
- **Reminders / escalation** — ตาม [[templates/price-list]] `reminder_days[]` และ `escalation_after_days` job background ไล่ vendor ที่ไม่ตอบสนอง
- **Closed for response** (`now >= end_date`) — portal ล็อก; การ submission สาย reject
- **Award** — ผู้ซื้อ flip `tb_pricelist` ที่เลือกเป็น `active`; ผู้แพ้คงที่ `draft` หรือ flip ไป `inactive`

**Date validation:** `end_date > start_date`; ทั้งคู่ต้องอยู่ในอนาคตเมื่อ invitation ถูกส่ง **Template-bound:** `pricelist_template_id` immutable หลัง invitation ครั้งแรก **สกุลเงิน:** inherit จาก template; การ override ต่อบรรทัดห้าม

## 7. ความเชื่อมโยงข้ามโมดูล

- [[vendor-pricelist]] — การตอบสนองของ vendor materialise เป็นแถว `tb_pricelist`; ตัวที่ได้รับมอบกลายเป็นแคตตาล็อก active
- [[templates/price-list]] — RFQ ต้องการ template (สกุลเงิน, validity, reminder, แคตตาล็อกสินค้า)
- [[master-data/vendor]] — vendor ที่เชิญต้องอ้างอิงบันทึก vendor active
- [[master-data/currency]] — สกุลเงิน cascade จาก template
- [[purchase-request]] / [[purchase-order]] — ผู้บริโภคปลายน้ำของ pricelist ที่ได้รับมอบ
- [[system-config/workflow]] — *ไม่ใช้* โดย RFQ; กล่าวเพื่อความตรงข้าม

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_request_for_pricing` (lines 4039-4070), `tb_request_for_pricing_detail` (lines 4106-4142), `tb_request_for_pricing_comment` (lines 4072-4104), `tb_request_for_pricing_detail_comment` (lines 4144-4176)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/vendor-management/request-price-list/`
- **Carmen docs:** `../carmen/docs/business-analysis/price-list-ba.md`; `../carmen/docs/business-analysis/procurement-ba.md` (section RFQ)
