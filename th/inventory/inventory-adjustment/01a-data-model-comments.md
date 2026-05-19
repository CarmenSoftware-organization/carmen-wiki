---
title: การปรับปรุงสต๊อก — โมเดลข้อมูล: ตารางคอมเมนต์
description: ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัดสำหรับโมดูลการปรับปรุงสต๊อก — ข้อความ, JSON ไฟล์แนบ, และ enum ประเภทคอมเมนต์ (user/system)
published: true
date: 2026-05-20T00:00:00.000Z
tags: inventory-adjustment, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# การปรับปรุงสต๊อก — โมเดลข้อมูล: ตารางคอมเมนต์

## 1. ภาพรวม

โมดูลการปรับปรุงสต๊อก persist บันทึกที่ผู้ใช้เขียนและที่ระบบสร้าง รวมถึงไฟล์แนบบนตาราง `*_comment` เฉพาะ แยกจากตาราง header / detail ที่ถือวงจรชีวิตซึ่งบันทึกอยู่ใน [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) แถวคอมเมนต์ทุกแถวถือข้อความอิสระ `message`, array JSON `attachments` ของ S3-token records (`{originalName, fileToken, contentType}`) และ discriminator `type` (`enum_comment_type`) ที่แยกระหว่างเอนทรีที่ผู้ใช้เขียนกับบันทึกการเปลี่ยนสถานะที่ระบบสร้าง ตารางคอมเมนต์ระดับเอกสารผูกกับ header ของเอกสาร (`tb_stock_in_comment`, `tb_stock_out_comment`); ตารางคอมเมนต์ระดับบรรทัดผูกกับบรรทัดเฉพาะ (`tb_stock_in_detail_comment`, `tb_stock_out_detail_comment`) ทำให้สามารถมีหลักฐานต่อบรรทัด เช่น รูปความเสียหายของสินค้านั้น ๆ หรือ references ของ vendor-RMA

## 2. รูปทรงร่วม

แถว `*_comment` ทุกแถวในโมดูลนี้ใช้รูปแบบคอลัมน์เดียวกัน:

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

รูปทรงเดียวกันใช้กับคอมเมนต์ระดับ header และคอมเมนต์ระดับบรรทัด ต่างกันแค่ FK ของ parent เท่านั้น ตาราง stock-in (`tb_stock_in_comment`, `tb_stock_in_detail_comment`) สะท้อนตาราง stock-out (`tb_stock_out_comment`, `tb_stock_out_detail_comment`) ทุกประการในรูปทรงคอลัมน์ ต่างกันแค่ปลายทางของ FK ของ parent เท่านั้น

## 3. ตาราง

### 3.1 tb_stock_in_comment

**Comment / attachment ระดับเอกสาร** บน stock-in ถือ `message` ข้อความอิสระและ array JSON `attachments` ของ S3-token records (รูปความเสียหาย, vendor RMA, สแกน count sheet) ติด tag user-vs-system ผ่าน `enum_comment_type`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `stock_in_id` | `String @db.Uuid` | No | FK ไป `tb_stock_in.id` |
| `type` | `enum_comment_type` | No | `user` (default) หรือ `system` |
| `user_id` | `String @db.Uuid` | Yes | ผู้ใช้ที่เขียน comment |
| `message` | `String` | Yes | เนื้อหา comment ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ `{originalName, fileToken, contentType}`; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `stock_in_id → tb_stock_in.id` (`NoAction`)

### 3.2 tb_stock_in_detail_comment

**Comment / attachment ระดับบรรทัด** บนแถว detail ของ stock-in รูปทรงเดียวกับ `tb_stock_in_comment` แต่ผูกกับบรรทัดเฉพาะ — ใช้สำหรับ "รูปความเสียหายเฉพาะของสินค้านี้" หรือ "vendor RMA สำหรับสินค้านี้"

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | -------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `stock_in_detail_id` | `String @db.Uuid` | No | FK ไป `tb_stock_in_detail.id` |
| `type` | `enum_comment_type` | No | `user` (default) หรือ `system` |
| `user_id` | `String @db.Uuid` | Yes | ผู้ใช้ |
| `message` | `String` | Yes | ข้อความอิสระ |
| `attachments` | `Json @db.JsonB` | Yes | Array ของ attachment records; default `[]` |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String @db.Uuid` | Yes | ID ของผู้สร้าง |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp การอัปเดตล่าสุด |
| `updated_by_id` | `String @db.Uuid` | Yes | ID ของผู้อัปเดต |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String @db.Uuid` | Yes | ID ของผู้ทำ soft-delete |

**Constraints:** `@id` บน `id` FK `stock_in_detail_id → tb_stock_in_detail.id` (`NoAction`)

### 3.3 tb_stock_out_comment, tb_stock_out_detail_comment

ภาพสะท้อนของ `tb_stock_in_comment` / `tb_stock_in_detail_comment` สำหรับเอกสารขาออก รูปทรงคอลัมน์เหมือนกัน; FKs ไปยัง `tb_stock_out.id` / `tb_stock_out_detail.id` ตามลำดับ ใช้สำหรับการแนบรูปความเสียหายบนบรรทัด write-off, references ของ recall-RMA, บันทึก sign-off ของ count-shortage

## 4. ส่วนอ้างอิง

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) — ตาราง header / detail, ตัวจำแนกประเภท `tb_adjustment_type`, นิยาม enum (`enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`), ERD และตารางความต่างจาก design
- ส่วนคู่ขนาน: [02 — กฎเชิงธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) — `ADJ_VAL_010` ใช้ `tb_stock_in_comment.attachments` / `tb_stock_out_comment.attachments` บังคับใช้กฎเรื่องเอกสารแนบสนับสนุนเมื่อ adjustment type มี `info.requiresDocument = true`
- ต้นทาง: [03 — User Flow: Store Keeper](/th/inventory/inventory-adjustment/03-user-flow-store-keeper) — อธิบายการ drag-and-drop ไฟล์แนบลงในแถวคอมเมนต์ระหว่างสร้างเอกสารปรับปรุง
- ต้นทาง: [04 — Test Scenarios: Inventory Controller](/th/inventory/inventory-adjustment/04-test-scenarios-inventory-controller) — IC-EDGE-08 ครอบคลุมการ flag escalation ผ่านคอมเมนต์โดย Department Manager
- ต้นทาง: [ภาพรวมโมดูลการปรับปรุงสต๊อก](/th/inventory/inventory-adjustment) — หน้า landing ของโมดูล
