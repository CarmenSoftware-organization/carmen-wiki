---
title: ใบรับสินค้า — โมเดลข้อมูล — ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลใบรับสินค้า — ข้อความ, JSON ไฟล์แนบ, และ enum ประเภทคอมเมนต์ (user/system)
published: true
date: 2026-05-20T00:00:00.000Z
tags: good-receive-note, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# ใบรับสินค้า — โมเดลข้อมูล — ตารางคอมเมนต์

## 1. ภาพรวม

โมดูลใบรับสินค้าเก็บข้อมูลโน้ตที่เขียนโดยผู้ใช้และที่ระบบสร้างขึ้น พร้อมไฟล์แนบ ไว้บนตาราง `*_comment` เฉพาะ แยกจากตาราง header / detail ที่ถือ lifecycle ซึ่งบันทึกไว้ใน [01 — โมเดลข้อมูล](/th/inventory/good-receive-note/01-data-model) ทุกแถวคอมเมนต์บรรจุ `message` แบบ free-text, `attachments` ในรูป JSON array ของ S3-token record (`{originalName, fileToken, contentType}`), และตัวแยกประเภท `type` (`enum_comment_type`) ที่แยกรายการที่ผู้ใช้เขียนออกจาก system-generated transition note ตารางคอมเมนต์ระดับเอกสารผูกกับ header ของเอกสาร; ตารางคอมเมนต์ระดับบรรทัดผูกกับบรรทัดเฉพาะ เพื่อให้บันทึกหลักฐานต่อบรรทัดได้ (เช่น "ภาพถ่ายความเสียหายของสินค้ารายการนี้")

## 2. โครงสร้างร่วม

ทุกแถว `*_comment` ในโมดูลนี้ใช้ column layout เดียวกัน:

```
id                  uuid / PK
<parent>_id         uuid / FK to header or detail row
message             text (free-form, nullable)
attachments         json — array of `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
created_at          timestamp
created_by_id       uuid / FK to tb_user
updated_at          timestamp
updated_by_id       uuid / FK to tb_user
```

โครงสร้างเดียวกันนี้ใช้กับคอมเมนต์ระดับ header และระดับ detail; ต่างกันเฉพาะ FK ของ parent

## 3. ตาราง

### 3.1 tb_good_received_note_comment

รายการ workflow / activity log ที่แนบกับ header GRN ไม่มีตาราง `tb_good_received_note_workflow` เฉพาะ — ตาราง comment นี้บวกกับ JSON workflow columns บน header คือบันทึกถาวรของ timeline workflow แต่ละแถวเป็น user comment (`type = user`) หรือ system event (`type = system`) เช่นการเปลี่ยนขั้น

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `good_received_note_id` | `String @db.Uuid` | No | FK ไปยัง `tb_good_received_note.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system` default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ `system`) |
| `message` | `String` | Yes | เนื้อ comment free-text |
| `attachments` | `Json @db.JsonB` | Yes | array ของ `{ originalName, fileToken, contentType }` default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**ข้อจำกัด:** `@id` บน `id` FK `good_received_note_id → tb_good_received_note.id` (`NoAction` on delete/update)
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key

### 3.2 tb_good_received_note_detail_comment

คู่ขนานระดับบรรทัดของ `tb_good_received_note_comment` จับ comment และ system event ที่แนบกับบรรทัด GRN เดียว — ปกติใช้ในระหว่างการตรวจสอบเพื่อบันทึก note การรับ/ปฏิเสธ และในช่วง commit เพื่อ log การตัดสินใจ posting ต่อบรรทัด

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `good_received_note_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_good_received_note_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system` default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ `system`) |
| `message` | `String` | Yes | เนื้อ comment free-text |
| `attachments` | `Json @db.JsonB` | Yes | array attachment default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดต |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**ข้อจำกัด:** `@id` บน `id` FK `good_received_note_detail_id → tb_good_received_note_detail.id` (`NoAction` on delete/update)
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key

## 4. อ้างอิงข้าม

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/good-receive-note/01-data-model) — ตาราง header และ detail, นิยาม enum, ERD, ตารางความต่างจาก design.
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/good-receive-note/02-business-rules) — กฎ validation ของวงจรชีวิต GRN.
- ต้นทาง: [ภาพรวมโมดูลใบรับสินค้า](/th/inventory/good-receive-note) — หน้า landing ของโมดูล.
