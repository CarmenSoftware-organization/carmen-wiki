---
title: ใบขอซื้อ — โมเดลข้อมูล — ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลใบขอซื้อ — ข้อความ, JSON ไฟล์แนบ, และ enum ประเภทคอมเมนต์ (user/system)
published: true
date: '2026-10-27T15:00:00.000Z'
tags: purchase-request, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# ใบขอซื้อ — โมเดลข้อมูล — ตารางคอมเมนต์

## 1. ภาพรวม

โมดูลใบขอซื้อบันทึก note ที่ผู้ใช้เขียนและที่ระบบสร้างขึ้นเอง รวมถึงไฟล์แนบ ลงในตาราง `*_comment` แยกต่างหากจากตาราง header / detail ที่ถือ lifecycle ของเอกสารซึ่งบันทึกใน [01 — โมเดลข้อมูล](/th/inventory/purchase-request/01-data-model) ทุกแถวคอมเมนต์มีฟิลด์ `message` แบบ free-text, ฟิลด์ `attachments` ที่เป็น JSON array ของ record token จาก S3 (`{originalName, fileToken, contentType}`), และฟิลด์ `type` (`enum_comment_type`) ที่ทำหน้าที่แยกระหว่างคอมเมนต์ที่ผู้ใช้เขียน กับ note transition ที่ระบบสร้างเอง เช่นการตัดสินใจอนุมัติ, เหตุผลที่ส่งกลับให้ผู้ขอ, และ note ของ workflow stage คอมเมนต์ระดับเอกสารผูกกับ header ของ PR (`tb_purchase_request_comment`); คอมเมนต์ระดับบรรทัดผูกกับบรรทัด PR เฉพาะ (`tb_purchase_request_detail_comment`) เพื่อรองรับการอธิบายเพิ่มและการตัดสินใจอนุมัติเป็นรายบรรทัด

## 2. รูปร่างร่วม

ทุกแถวของ `*_comment` ในโมดูลนี้ใช้ layout คอลัมน์ชุดเดียวกัน:

```
id                  uuid / PK
<parent>_id         uuid / FK ไปยังแถว header หรือ detail
message             text (free-form, nullable)
attachments         json — array ของ `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
doc_version         Int — ตัวนับเวอร์ชันสำหรับ optimistic-concurrency (default 0)
created_at          timestamp
created_by_id       uuid / FK ไปยัง tb_user
updated_at          timestamp
updated_by_id       uuid / FK ไปยัง tb_user
```

รูปร่างเดียวกันใช้กับทั้งคอมเมนต์ระดับ header และระดับบรรทัด ต่างกันเฉพาะ FK ของ parent

## 3. ตาราง

### 3.1 tb_purchase_request_comment

รายการของ workflow / activity-log ที่ผูกกับ header ของ PR Prisma schema ไม่มีตาราง `tb_purchase_request_workflow` โดยเฉพาะ — ตาราง comment นี้ผสมกับคอลัมน์ JSON ของ workflow บน header คือ record persist ของ timeline ของ workflow แต่ละแถวเป็น user comment (`type = user`) หรือ system event (`type = system`) เช่นการ transition stage

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_request_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_request.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน (null สำหรับ entry แบบ `system`) |
| `message` | `String` | Yes | เนื้อ comment แบบ free-text |
| `attachments` | `Json @db.JsonB` | Yes | array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `doc_version` | `Int @db.Integer` | No | ตัวนับเวอร์ชันสำหรับ optimistic-concurrency; default 0 |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_request_id → tb_purchase_request.id` (`NoAction` ตอน delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 3.2 tb_purchase_request_detail_comment

ตารางคู่ขนานระดับบรรทัดของ `tb_purchase_request_comment` จับ comment และ system event ที่ผูกกับบรรทัด PR เพียงบรรทัดเดียว — โดยทั่วไปใช้ระหว่างการอนุมัติเพื่อบันทึกการตัดสินใจระดับ stage และเหตุผลการ reject ต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_request_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_request_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | user id ผู้เขียน |
| `message` | `String` | Yes | เนื้อ comment แบบ free-text |
| `attachments` | `Json @db.JsonB` | Yes | array ของ attachment; default `[]` |
| `doc_version` | `Int @db.Integer` | No | ตัวนับเวอร์ชันสำหรับ optimistic-concurrency; default 0 |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | id ผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | timestamp การ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_request_detail_id → tb_purchase_request_detail.id`
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

## 4. การจัดการไฟล์แนบ (2026-10)

JSON `attachments` ถูกเขียนผ่าน endpoint คอมเมนต์ของ gateway (`apps/backend-gateway/src/application/purchase-request-comments/`; controller คอมเมนต์ของ header, line และ template ใช้รูปแบบเดียวกัน): `GET :bu_code/purchase-request-comments/:purchase_request_id`, `POST` path เดียวกันเพื่อสร้าง (multipart field `files`), `PATCH …/:comment_id` เพื่อแก้ไข, `DELETE …/:comment_id`, และ `POST` / `DELETE …/:comment_id/attachment[/:fileToken]` เพื่อเพิ่มหรือลบไฟล์

- **นโยบายรายหน่วยธุรกิจ (BU) แทนกฎ 10 MB / image+PDF แบบตายตัว** การอัปโหลดถูกตรวจกับนโยบายไฟล์แนบของ business unit (`AttachmentPolicyService.assertFiles`, `common/attachment-policy/`) อ่านจาก entry `attachment.allowed_types` และ `attachment.max_size_mb` ใน `tb_business_unit.config` ของ Backstage และ cache 60 วินาทีต่อ BU กลุ่มที่อนุญาต: `image`, `pdf`, `excel`, `word`, `csv`, `text`; ค่า default คือ `image` + `pdf`, ขนาด default 10 MB, เพดานสูงสุด 25 MB config ที่ผิดรูปแบบจะถอยไปใช้ค่า default การตรวจชนิดไฟล์เชื่อ MIME type; เฉพาะ MIME ที่ว่างหรือ `application/octet-stream` เท่านั้นที่ถอยไปใช้นามสกุลไฟล์ ความล้มเหลวเป็น `400` พร้อม `ATTACHMENT_TOO_LARGE` (`max_mb`) หรือ `ATTACHMENT_TYPE_NOT_ALLOWED` (`allowed`) key ของนโยบายตั้งได้จาก Backstage เท่านั้น — endpoint ของ BU เขียน key ที่ขึ้นต้นด้วย `attachment.` ไม่ได้
- **การแก้ไขส่ง delta** ตอนนี้ `PATCH` ส่งต่อ `attachments` เป็น `{ add: [...], remove: [fileToken, ...] }` (service ยังรับ array เต็มได้) gateway อ่านคอมเมนต์ซ้ำก่อน และลบเฉพาะ object ใน S3 ที่ token นั้นเป็นของคอมเมนต์นั้นจริง ดังนั้น token `remove` ที่ปลอมจึงลบไฟล์ของคอมเมนต์อื่นไม่ได้; การลบ S3 เป็น best-effort และบันทึก log เมื่อสำเร็จเพียงบางส่วน
- **การแบ่งหน้าใน UI** แผงคอมเมนต์โหลดครั้งละ 20 คอมเมนต์ เรียงใหม่สุดก่อน (`sort=created_at:desc`) และดึงหน้าถัดไปเมื่อท้ายรายการเลื่อนเข้ามาในมุมมอง; จุดคอมเมนต์ที่ header ของเอกสารใช้ `total` ของ backend ไม่ใช่จำนวนที่โหลดแล้ว (commit `61011d0e`)

## 5. การอ้างอิงข้าม

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/purchase-request/01-data-model) — `tb_purchase_request` และ `tb_purchase_request_detail` (ตาราง header / line), นิยาม enum, และคอลัมน์ JSON ของ workflow / history.
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/purchase-request/02-business-rules) — กฎ validation และพฤติกรรมคอมเมนต์ตาม workflow stage ที่บันทึกลง `tb_purchase_request_comment` / `tb_purchase_request_detail_comment`.
- ต้นทาง: [ภาพรวมโมดูลใบขอซื้อ](/th/inventory/purchase-request) — หน้า landing ของโมดูล.
