---
title: ใบสั่งซื้อ — โมเดลข้อมูล — ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลใบสั่งซื้อ — ข้อความ, JSON ไฟล์แนบ, และ enum ประเภทคอมเมนต์ (user/system)
published: true
date: 2026-07-15T13:30:00.000Z
tags: purchase-order, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# ใบสั่งซื้อ — โมเดลข้อมูล — ตารางคอมเมนต์

## 1. ภาพรวม

โมดูลใบสั่งซื้อบันทึก note ที่ผู้ใช้เขียนและที่ระบบสร้าง พร้อมไฟล์แนบ บนตาราง `*_comment` เฉพาะ ซึ่งแยกจากตาราง header / detail ที่เป็นตัวขับเคลื่อนวงจรชีวิตของเอกสาร ดูได้ที่ [01 — โมเดลข้อมูล](/th/inventory/purchase-order/01-data-model) ทุกแถวคอมเมนต์มี `message` แบบ free-text, `attachments` ที่เป็น JSON array ของ S3-token records (`{originalName, fileToken, contentType}`) และ `type` discriminator (`enum_comment_type`) ที่แยก entry ที่ผู้ใช้เขียนออกจากบันทึก transition ที่ระบบสร้าง เช่นเหตุผล send-back, เหตุผล reject, และเหตุผล close-early คอมเมนต์ระดับเอกสารผูกกับ header ของ PO (`tb_purchase_order_comment`); คอมเมนต์ระดับบรรทัดผูกกับ PO line รายการเดียว (`tb_purchase_order_detail_comment`) รองรับ note ต่อบรรทัดระหว่างการอนุมัติและการรับของ (Overview รุ่นก่อนหน้าเคยระบุ "three-way-match exception notes" และ "คอมเมนต์ three-way-match ต่อบรรทัด" เป็นการใช้งานคอมเมนต์ด้วย — ไม่มีฟีเจอร์ three-way-match ใน source ปัจจุบัน ดู [02 — กฎเชิงธุรกิจ](/th/inventory/purchase-order/02-business-rules) § 5)

## 2. รูปแบบที่ใช้ร่วมกัน

ทุกแถว `*_comment` ในโมดูลนี้ใช้ column layout เดียวกัน:

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

รูปแบบเดียวกันใช้กับคอมเมนต์ระดับ header และระดับ detail; ต่างกันแค่ FK ของ parent

## 3. ตาราง

### 3.1 tb_purchase_order_comment

รายการ workflow / activity-log ที่แนบกับ header PO เช่นเดียวกับ PR ไม่มีตาราง `tb_purchase_order_workflow` เฉพาะ — comment table นี้ บวกกับ JSON workflow columns บน header คือบันทึก persistent ของ timeline workflow แต่ละ row เป็นไม่ user comment (`type = user`) ก็เป็น system event (`type = system`) เช่น stage transition

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_order_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_order.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | User id ผู้เขียน (null สำหรับ entry `system`) |
| `message` | `String` | Yes | เนื้อหา comment free-text |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ `{ originalName, fileToken, contentType }`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ผู้ update |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_order_id → tb_purchase_order.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

### 3.2 tb_purchase_order_detail_comment

คู่ระดับบรรทัดของ `tb_purchase_order_comment` Capture comment และ system event ที่แนบกับ PO line เดียว — ใช้ระหว่าง approval เพื่อบันทึกการตัดสินใจระดับ stage และระหว่างการ fulfilment เพื่อ log การแลกเปลี่ยนกับผู้ขายต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `purchase_order_detail_id` | `String @db.Uuid` | No | FK ไปยัง `tb_purchase_order_detail.id` |
| `type` | `enum_comment_type` | No | `user` หรือ `system`; default `user` |
| `user_id` | `String @db.Uuid` | Yes | User id ผู้เขียน (null สำหรับ entry `system`) |
| `message` | `String` | Yes | เนื้อหา comment free-text |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ attachments; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ผู้ update |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `purchase_order_detail_id → tb_purchase_order_detail.id` (`NoAction` on delete/update)
**Indexes:** ไม่มีประกาศนอกเหนือจาก primary key

## 4. การอ้างอิงข้าม

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/purchase-order/01-data-model) — `tb_purchase_order` และ `tb_purchase_order_detail` (ตาราง header / line), นิยาม enum, คอลัมน์ JSON ของ workflow / history, และสะพานข้ามเอกสารกับ PR และ GRN.
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/purchase-order/02-business-rules) — `PO_POST_005` (ข้อความเหตุผล send-back / review แก้ไขในรอบนี้ — เป็นการ reset stage เท่านั้น `po_status` ไม่เปลี่ยน), `PO_POST_010b` (ข้อความเหตุผล reject แก้ไขแล้ว — void แบบตรงและสิ้นสุดจาก `in_progress`), `PO_POST_011` (ข้อความเหตุผล close-early), และ `PO_AUTH_011` (คอมเมนต์อนุมัติตาม workflow stage) ทั้งหมดบันทึกลง `tb_purchase_order_comment` `PO_POST_009` (คอมเมนต์ three-way-match exception) ถูกตัดออก — ไม่พบฟีเจอร์ invoice/AP-matching ใน source ปัจจุบัน.
- ต้นทาง: [03 — User Flow: Procurement Manager](/th/inventory/purchase-order/03-user-flow-procurement-manager) — อธิบายการที่ Manager ตรวจ tab Attachments / Comments และบันทึกการตัดสินใจของผู้อนุมัติ.
- ต้นทาง: [03 — User Flow: Audit & Config](/th/inventory/purchase-order/03-user-flow-audit-config) — อธิบายการที่ Auditor อ่าน `tb_purchase_order_comment` แบบ read-only เพื่อเก็บหลักฐานในแฟ้มกรณี.
- ต้นทาง: [ภาพรวมโมดูลใบสั่งซื้อ](/th/inventory/purchase-order) — หน้า landing ของโมดูล.
