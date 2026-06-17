---
title: ราคาสินค้าจากผู้ขาย — โมเดลข้อมูล — ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลราคาสินค้าจากผู้ขาย ครอบคลุม sub-entity families: pricelist template, request-for-pricing, pricelist
published: true
date: 2026-06-17T08:00:00.000Z
tags: vendor-pricelist, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# ราคาสินค้าจากผู้ขาย — โมเดลข้อมูล — ตารางคอมเมนต์

## 1. ภาพรวม

โมดูลราคาสินค้าจากผู้ขายจัดเก็บโน้ตที่เขียนโดยผู้ใช้และที่ระบบสร้างให้อัตโนมัติ พร้อมไฟล์แนบ ลงในตาราง `*_comment` ที่แยกออกมาเฉพาะ ครอบคลุม sub-entity families สามกลุ่ม — pricelist template, request-for-pricing และ pricelist — โดยแยกจากตาราง header / detail ที่ถือ lifecycle ซึ่งบันทึกไว้ใน [01 — โมเดลข้อมูล](/th/inventory/vendor-pricelist/01-data-model) แถวคอมเมนต์ทุกแถวมีฟิลด์ `message` แบบข้อความอิสระ, ฟิลด์ `attachments` ที่เป็น JSON array ของ S3-token records (`{originalName, fileToken, contentType}`) และฟิลด์ `type` ที่แยก discriminator (`enum_comment_type`) ซึ่งใช้แยก entry ที่ผู้ใช้เขียนกับ entry ที่ระบบสร้างจาก transition แต่ละ sub-entity family มีตารางคอมเมนต์ระดับ header และตารางคอมเมนต์ระดับ detail (ระดับบรรทัด) เป็นของตัวเอง รองรับการอธิบายเพิ่มเติมต่อบรรทัด การแนบหลักฐาน vendor quotation และการตัดสินใจ approval / rejection ต่อบรรทัด ครอบคลุม lifecycle ของ pricelist request

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

Entry activity-log แนบกับ header ของ template ถือ comment ของ user และ event `system` (การเปลี่ยนสถานะ, การแก้ vendor-instruction)

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
| `tb_request_for_pricing_comment` | `request_for_pricing_id → tb_request_for_pricing.id` | activity log ระดับ campaign: campaign สร้าง, ผู้ขายถูกเลือก, email dispatch, reminder fire, campaign ปิด |
| `tb_request_for_pricing_detail_comment` | `request_for_pricing_detail_id → tb_request_for_pricing_detail.id` | activity log invitation ต่อผู้ขาย: email sent / opened / clicked, portal first-access, draft saved, submission completed Telemetry email และ portal ละเอียด (delivered, opened, clicked, IP, จำนวน session) ที่ carmen/docs อธิบาย อยู่ใน JSON ของ `attachments` / `message` ในชั้นแอป; ไม่มีคอลัมน์ Prisma dedicated สำหรับมัน |

### 3.4 tb_pricelist_comment / tb_pricelist_detail_comment

Activity-log surface บน header ของ pricelist และต่อแถว รูปร่างเดียวกันกับตาราง template comment — `id`, FK ไป parent, enum `type` (`user` / `system`), `user_id`, `message`, `attachments`, `doc_version` และคอลัมน์ audit มาตรฐาน

| ตาราง | Parent FK | วัตถุประสงค์ |
| ----- | --------- | ------- |
| `tb_pricelist_comment` | `pricelist_id → tb_pricelist.id` | activity log header ของ pricelist: created, vendor saved draft, vendor submitted, ผล validate, purchaser approved / rejected, การเปลี่ยนสถานะ |
| `tb_pricelist_detail_comment` | `pricelist_detail_id → tb_pricelist_detail.id` | activity log ต่อแถว: แถวแก้โดย purchaser, validation warning แนบ, flag preferred-vendor toggle, deviation กับราคาประวัติ log |

## 4. แหล่งอ้างอิงข้าม

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/vendor-pricelist/01-data-model) — `tb_pricelist_template`, `tb_request_for_pricing`, `tb_pricelist` (ตาราง header) และ `_detail` siblings, นิยาม enum, และตารางความต่างจาก design.
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/vendor-pricelist/02-business-rules) — กฎ validation และพฤติกรรมคอมเมนต์ตาม workflow stage ครอบคลุมทั้งสาม sub-entity families ที่บันทึกลงตาราง `*_comment` / `*_detail_comment` ของแต่ละกลุ่ม.
- ต้นทาง: [ภาพรวมโมดูลราคาสินค้าจากผู้ขาย](/th/inventory/vendor-pricelist) — หน้า landing ของโมดูล.
