---
title: ใบเบิกของจากสโตร์ — โมเดลข้อมูล — ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลใบเบิกของจากสโตร์ — ข้อความ, JSON ไฟล์แนบ, และ enum ประเภทคอมเมนต์ (user/system)
published: true
date: 2026-05-20T00:00:00.000Z
tags: store-requisition, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# ใบเบิกของจากสโตร์ — โมเดลข้อมูล — ตารางคอมเมนต์

## 1. ภาพรวม

โมดูลใบเบิกของจากสโตร์บันทึก note ที่ผู้ใช้เขียนและที่ระบบสร้างขึ้นเอง รวมถึงไฟล์แนบ ลงในตาราง `*_comment` แยกต่างหากจากตาราง header / detail ที่ถือ lifecycle ของเอกสารซึ่งบันทึกใน [01 — โมเดลข้อมูล](/th/inventory/store-requisition/01-data-model) ทุกแถวคอมเมนต์มีฟิลด์ `message` แบบ free-text, ฟิลด์ `attachments` ที่เป็น JSON array ของ record token จาก S3 (`{originalName, fileToken, contentType}`), และฟิลด์ `type` (`enum_comment_type`) ที่ทำหน้าที่แยกระหว่างคอมเมนต์ที่ผู้ใช้เขียน กับ note transition ที่ระบบสร้างเอง เช่นการตัดสินใจอนุมัติ, note การ fulfill บางส่วน, และ event ของ workflow stage คอมเมนต์ระดับเอกสารผูกกับ header ของ SR (`tb_store_requisition_comment`); คอมเมนต์ระดับบรรทัดผูกกับบรรทัด SR เฉพาะ (`tb_store_requisition_detail_comment`) เพื่อรองรับ note การเปลี่ยนสินค้าและ note การ fulfill เป็นรายบรรทัด

## 2. รูปร่างร่วม

ทุกแถวของ `*_comment` ในโมดูลนี้ใช้ layout คอลัมน์ชุดเดียวกัน:

```
id                  uuid / PK
<parent>_id         uuid / FK ไปยังแถว header หรือ detail
message             text (free-form, nullable)
attachments         json — array ของ `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
created_at          timestamp
created_by_id       uuid / FK ไปยัง tb_user
updated_at          timestamp
updated_by_id       uuid / FK ไปยัง tb_user
```

รูปร่างเดียวกันใช้กับทั้งคอมเมนต์ระดับ header และระดับบรรทัด ต่างกันเฉพาะ FK ของ parent

## 3. ตาราง

### 3.1 tb_store_requisition_comment

รายการ workflow / activity-log ที่ผูกกับส่วนหัว SR ไม่มีตาราง `tb_store_requisition_workflow` เฉพาะ — ตาราง comment นี้ รวมกับคอลัมน์ JSON ของ workflow บนส่วนหัว คือบันทึกถาวรของ timeline ของ workflow แต่ละแถวคือ user comment (`type = user`) หรือ system event (`type = system`) เช่นการเปลี่ยนขั้น

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `store_requisition_id` | `String @db.Uuid` | No | FK ไปยัง `tb_store_requisition.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ entry แบบ `system`) |
| `message` | `String` | Yes | เนื้อหา comment แบบอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp สร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `store_requisition_id → tb_store_requisition.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 3.2 tb_store_requisition_detail_comment

ตาราง counterpart ระดับบรรทัดของ `tb_store_requisition_comment` เก็บ comment และ system events ที่ผูกกับบรรทัด SR เดียว — โดยทั่วไปใช้ระหว่างการอนุมัติเพื่อบันทึกการตัดสินใจต่อบรรทัด (โดย `approved_message` / `review_message` / `reject_message` บรรจุลายเซ็นเป็นทางการบนตัวบรรทัดเอง) และระหว่าง issue เพื่อ log การตัดสินใจ fulfillment

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `store_requisition_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_store_requisition_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ entry แบบ `system`) |
| `message` | `String` | Yes | เนื้อหา comment แบบอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของไฟล์แนบ; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp สร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp อัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `store_requisition_detail_id → tb_store_requisition_detail.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

## 4. การอ้างอิงข้าม

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/store-requisition/01-data-model) — `tb_store_requisition` และ `tb_store_requisition_detail` (ตาราง header / line), นิยาม enum, และคอลัมน์ JSON ของ workflow / history.
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/store-requisition/02-business-rules) — กฎ validation และพฤติกรรมคอมเมนต์ตาม workflow stage ที่บันทึกลง `tb_store_requisition_comment` / `tb_store_requisition_detail_comment`.
- ต้นทาง: [ภาพรวมโมดูลใบเบิกของจากสโตร์](/th/inventory/store-requisition) — หน้า landing ของโมดูล.
