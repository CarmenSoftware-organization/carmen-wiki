---
title: ราคาสินค้าจากผู้ขาย — โมเดลข้อมูล — ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลราคาสินค้าจากผู้ขาย ครอบคลุม sub-entity families: pricelist template, request-for-pricing, pricelist
published: true
date: '2026-10-27T15:00:00.000Z'
tags: vendor-pricelist, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# ราคาสินค้าจากผู้ขาย — โมเดลข้อมูล — ตารางคอมเมนต์

## 1. ภาพรวม

โมดูล Vendor Price List เก็บโน้ตพร้อมไฟล์แนบลงในตาราง `*_comment` ที่แยกออกมาเฉพาะ ครอบคลุม sub-entity families สามกลุ่ม — pricelist template, request-for-pricing และ pricelist — โดยแยกจากตาราง header / detail ที่ถือ lifecycle ซึ่งบันทึกไว้ใน [01 — โมเดลข้อมูล](/th/inventory/vendor-pricelist/01-data-model) แถวคอมเมนต์ทุกแถวมีฟิลด์ `message` แบบข้อความอิสระ, ฟิลด์ `attachments` ที่เป็น JSON array ของ S3-token records (`{originalName, fileToken, contentType}`) และฟิลด์ `type` ที่แยก discriminator (`enum_comment_type`, default `user` | `system`) ที่ใช้ร่วมกับทุกตาราง comment อื่นในผลิตภัณฑ์ แต่ละ sub-entity family มีตารางคอมเมนต์ระดับ header และตารางคอมเมนต์ระดับ detail (ระดับบรรทัด) เป็นของตัวเอง พร้อม manual CRUD controller ของตัวเอง

> **ยืนยันแล้ว (ตรวจสอบเมื่อ 2026-07-16):** ค่า `system` บน `enum_comment_type` มีอยู่จริงใน schema แต่ไม่มี service ใดในโมดูลนี้ (`price-list`, `price-list-template`, `request-for-pricing`, `check-price-list`) ที่สร้างแถวคอมเมนต์โดยอัตโนมัติ — `create()`/`update()`/`updateStatus()` ของทั้งสี่ตัวไม่แตะตาราง `*_comment` เลย ทุกแถวคอมเมนต์ที่มีอยู่วันนี้ถูกเขียนโดย call ของผู้ใช้ที่ชัดเจนไปยัง CRUD endpoint ของคอมเมนต์นั้นเอง ให้ถือว่าทุกคำกล่าวแบบ "system comment records..." ด้านล่างและใน [02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) / หน้า user-flow เป็น design-target ไม่ใช่พฤติกรรมปัจจุบัน

> **Re-sync 2026-10-27:** (a) master ผู้ขายมีคู่ comment เดียวกัน — `tb_vendor_comment` และ `tb_vendor_business_type_comment` — และหน้า vendor ตอนนี้เปิด sheet comment + attachment บน `/api/config/{bu}/vendor-comments` (`vendor-form.tsx` → `EntityCommentSheet`, `use-vendor-comments.ts`); (b) comment controller ทุกตัวในโมดูลนี้ (template, RFQ, pricelist, vendor — ทั้ง header และ detail) ตอนนี้ตรวจการอัปโหลดผ่าน `AttachmentPolicyService` / `CommentFilesInterceptor` แทนการตรวจ 10 MB + JPEG/PNG/WebP/GIF/PDF ที่ hard-code: กลุ่มไฟล์ที่อนุญาต (`image`, `pdf`, `excel`, `word`, `csv`, `text`) และเพดานขนาดมาจาก key `config` ของ business unit คือ `attachment.allowed_types` / `attachment.max_size_mb` (ค่า default: image + pdf, 10 MB; เพดานสูงสุด 25 MB; policy ถูก cache 60 วินาทีต่อ BU); (c) DTO ของ micro-service รับ `attachments` ได้ทั้งแบบ array เต็ม (แทนที่) หรือแบบ delta `{ add, remove }` — ก่อนหน้านี้ delta shape จาก gateway ทำให้ PATCH ที่แนบหรือลบไฟล์ล้มเหลวใน validation; (d) ตอน PATCH gateway ลบเฉพาะไฟล์ใน storage ที่ `fileToken` เป็นของ comment นั้นจริง และลบหลังจากเขียน DB สำเร็จแล้วเท่านั้น ยังเป็นจริงอยู่: ไม่มีสิ่งใดในโมดูลนี้เขียน comment แบบ `system` โดยอัตโนมัติ — การ void หรือ restore price list ไม่ทิ้งแถว comment

## 2. โครงสร้างร่วม

แถว `*_comment` ทุกแถวในโมดูลนี้ใช้โครงคอลัมน์เดียวกัน:

```
id                  uuid / PK
<parent>_id         uuid / FK ไปยังแถว header หรือ detail
message             text (อิสระ, nullable)
attachments         json — array ของ `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
doc_version         int — ตัวนับเวอร์ชันสำหรับ optimistic concurrency (default 0)
created_at          timestamp
created_by_id       uuid / FK ไปยัง tb_user
updated_at          timestamp
updated_by_id       uuid / FK ไปยัง tb_user
```

โครงสร้างเดียวกันนี้ใช้กับคอมเมนต์ระดับ header และคอมเมนต์ระดับ detail ทั่วทั้งสาม sub-entity families (pricelist template, request-for-pricing, pricelist); ต่างกันแค่ปลายทาง FK ของ parent เท่านั้น

## 3. ตาราง

### 3.1 tb_pricelist_template_comment

โน้ตข้อความอิสระที่แนบกับ header ของ template ผ่าน manual CRUD endpoint ของตัวเอง เขียนโดยผู้ใช้เท่านั้น — `updateStatus()` (endpoint เปลี่ยนสถานะของ template) ไม่เคยเขียนที่นี่ ดังนั้นจึงไม่มี entry อัตโนมัติสำหรับการเปลี่ยนสถานะหรือการแก้ vendor-instruction

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_template_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist_template.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | id user ผู้เขียน (null สำหรับ `system`) |
| `message` | `String` | Yes | body comment ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `doc_version` | `Int` | No | ตัวนับเวอร์ชันสำหรับ optimistic concurrency; default 0 |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `pricelist_template_id → tb_pricelist_template.id` (`NoAction`)
**Indexes:** ไม่ได้ประกาศนอกจาก primary key

### 3.2 tb_pricelist_template_detail_comment

คู่ของ `tb_pricelist_template_comment` ในระดับแถว จับ comment และ event ของระบบที่แนบกับแถว template detail เดียว

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `pricelist_template_detail_id` | `String @db.Uuid` | No | FK ไป `tb_pricelist_template_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | id user ผู้เขียน (null สำหรับ `system`) |
| `message` | `String` | Yes | body ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | array ของ attachment; default `[]` |
| `doc_version` | `Int` | No | ตัวนับเวอร์ชันสำหรับ optimistic concurrency; default 0 |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (audit มาตรฐาน) | Yes | คอลัมน์ audit มาตรฐาน |

**Constraints:** `@id` บน `id` FK `pricelist_template_detail_id → tb_pricelist_template_detail.id` (`NoAction`)

### 3.3 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment

Activity-log surface บน header ของ campaign และ invitation ต่อผู้ขาย รูปร่างเดียวกันกับตาราง template comment — `id`, FK ไป parent, enum `type` (`user` / `system`), `user_id`, `message`, `attachments`, `doc_version` และคอลัมน์ audit มาตรฐาน

| ตาราง | Parent FK | วัตถุประสงค์ |
| ----- | --------- | ------- |
| `tb_request_for_pricing_comment` | `request_for_pricing_id → tb_request_for_pricing.id` | โน้ตข้อความอิสระแนบกับ header ของ RFQ — เขียนโดยผู้ใช้เท่านั้น; ไม่มีอะไรใน RFQ create/update service ที่เขียน entry ที่นี่โดยอัตโนมัติ |
| `tb_request_for_pricing_detail_comment` | `request_for_pricing_detail_id → tb_request_for_pricing_detail.id` | โน้ตข้อความอิสระแนบกับแถวผู้ขายที่ถูกเชิญหนึ่งราย — เขียนโดยผู้ใช้เท่านั้น telemetry อีเมล/portal อย่างละเอียด (sent, delivered, opened, clicked, IP addresses, จำนวน session) ที่ carmen/docs อธิบาย ไม่มีโค้ดรองรับที่ไหนเลยในโมดูลนี้ — ไม่มีทั้งคอลัมน์ Prisma dedicated และไม่มีการเขียนอัตโนมัติเข้า JSON `attachments` / `message` ของตารางนี้ |

### 3.4 tb_pricelist_comment / tb_pricelist_detail_comment

Activity-log surface บน header ของ pricelist และต่อแถว รูปร่างเดียวกันกับตาราง template comment — `id`, FK ไป parent, enum `type` (`user` / `system`), `user_id`, `message`, `attachments`, `doc_version` และคอลัมน์ audit มาตรฐาน

| ตาราง | Parent FK | วัตถุประสงค์ |
| ----- | --------- | ------- |
| `tb_pricelist_comment` | `pricelist_id → tb_pricelist.id` | โน้ตข้อความอิสระแนบกับ header ของ pricelist — เขียนโดยผู้ใช้เท่านั้น; `create()`/`update()` ของ `price-list.service.ts` ไม่เคยเขียนที่นี่ ดังนั้นจึงไม่มี entry อัตโนมัติสำหรับการเปลี่ยนสถานะ, การ submit หรือการ approve |
| `tb_pricelist_detail_comment` | `pricelist_detail_id → tb_pricelist_detail.id` | โน้ตข้อความอิสระแนบกับแถวสินค้าหนึ่งแถว — เขียนโดยผู้ใช้เท่านั้น; ไม่มี entry อัตโนมัติสำหรับการ toggle `is_preferred` หรือการแก้ราคา |

### 3.5 tb_vendor_comment / tb_vendor_business_type_comment

รูปร่างเดียวกับ § 2 (`type`, `user_id`, `message`, `attachments`, `doc_version`, คอลัมน์ audit); FK ของ parent คือ `vendor_id → tb_vendor.id` และ `vendor_business_type_id → tb_vendor_business_type.id` Gateway: `GET/POST /api/config/{bu}/vendor-comments/:vendor_id`, `PATCH/DELETE …/:comment_id`, `POST …/:comment_id/attachment`, `DELETE …/:comment_id/attachment/:fileToken` (และคู่แฝด `vendor-business-type-comments`) หน้า vendor ของ React ใช้เฉพาะระดับ vendor

## 4. แหล่งอ้างอิงข้าม

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/vendor-pricelist/01-data-model) — `tb_pricelist_template`, `tb_request_for_pricing`, `tb_pricelist` (ตาราง header) และ `_detail` siblings, นิยาม enum, และตารางความต่างจาก design.
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/vendor-pricelist/02-business-rules) — กฎ validation และพฤติกรรมคอมเมนต์ตาม workflow stage ครอบคลุมทั้งสาม sub-entity families ที่บันทึกลงตาราง `*_comment` / `*_detail_comment` ของแต่ละกลุ่ม.
- ต้นทาง: [ภาพรวมโมดูลราคาสินค้าจากผู้ขาย](/th/inventory/vendor-pricelist) — หน้า landing ของโมดูล.
