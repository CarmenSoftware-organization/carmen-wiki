---
title: การแจ้งเตือน (Notification)
description: Fan-out การแจ้งเตือนข้าม tenant — แถว notification, message template ที่ใช้ซ้ำได้ และข่าวประกาศของแพลตฟอร์ม
published: true
date: 2026-05-17T12:00:00.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# การแจ้งเตือน (Notification)

> **At a Glance**
> **เจ้าของ:** Workflow runtime (เขียน) + Sysadmin / Platform Admin (template และข่าว) &nbsp;·&nbsp; **ตาราง:** `tb_notification` (+ `tb_message_format`, `tb_news`) &nbsp;·&nbsp; **ใช้โดย:** ทุกการเปลี่ยน stage ของ workflow &nbsp;·&nbsp; ท่อข้อความขาเข้า — inbox, template, ข่าวประกาศแพลตฟอร์ม

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี notification คือ **ท่อข้อความขาเข้า** — ทุกการเปลี่ยน stage ของ workflow, การ mention ใน comment, ข่าวประกาศของระบบ และข่าวสารของแพลตฟอร์มถูก materialise ขึ้นมาให้ shell ของแอป render badge + drawer inbox และสามารถ dispatch ผ่านอีเมล, SMS หรือ push ได้

ตารางในระดับ platform schema สามตัวทำงานร่วมกัน: `tb_notification` (แถว inbox หนึ่งแถวต่อข้อความ), `tb_message_format` (template ที่ใช้ซ้ำได้พร้อม flag channel `is_email` / `is_sms` / `is_in_app`) และ `tb_news` (ข่าวประกาศทั่วทั้งแพลตฟอร์ม) ทั้งหมดอยู่ใน **platform schema** เพราะการแจ้งเตือนข้ามขอบเขต BU และการ broadcast ต้องเข้าถึงทุก tenant

**ดูแลโดย** workflow runtime (เขียนต่อ event), Sysadmin (template), Platform Admin (ข่าว) **อ่านโดย** inbox ของ shell แอปและ widget บน dashboard

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู inbox | shell แอป → กระดิ่ง notification | กรองที่ `to_user_id = me` |
| Mark เป็นอ่านแล้ว | คลิกข้อความ | อัปเดต `is_read = true` |
| แก้ไข message template | Sysadmin → Platform Config → Message Formats | ส่งผลต่อทุก event ที่ใช้ format นั้น |
| โพสต์ข่าวประกาศแพลตฟอร์ม | Platform Admin → News | เห็นได้โดยทุก tenant ทันที |
| ตั้งเวลาการแจ้งเตือน | ตั้ง `scheduled_at` | Dispatcher fire เมื่อเวลาผ่าน |
| ส่ง dispatch ซ้ำ | re-process ผ่าน channel ขาออก | `is_sent` ติดตามการส่งต่อ channel |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ผู้ใช้ไม่ได้รับการแจ้งเตือนที่คาด | การ resolve ผู้รับขาด; หรือ `is_in_app = false` บน format | เช็ค flag channel ของ `tb_message_format` + recipient map ของ workflow |
| inbox มีแถวซ้ำสำหรับ event เดียว | ชุดผู้รับมีรายการซ้ำ | แอปต้อง dedup ก่อน insert |
| ชื่อ template ชนกัน | `tb_message_format.name` มีอยู่แล้วในแถวที่ไม่ถูกลบ | reactivate หรือเลือกชื่ออื่น |
| Email dispatch แต่ in-app ขาด | `is_in_app = false` บน format | เปิดให้ถ้าต้องใช้ทั้งสอง channel |
| คลิกแล้ว 404 | `metadata` อ้างอิง entity ของ tenant ที่ถูกลบ | ไม่บังคับ FK; UI ต้องจัดการอย่างนุ่มนวล |

## 4. กรณีพิเศษ

- **การเชื่อมโยงข้าม schema** `metadata` อาจ carry identifier ของ tenant (เช่น id ของ PR) Platform schema ไม่บังคับ FK เข้าตาราง tenant
- **Scope ของการ broadcast ข่าว** `tb_news` ไม่มี BU scoping — ผู้ใช้ที่ authenticate ทุกคนข้ามทุก tenant เห็นแถว ใช้ in-app แบบ targeted สำหรับเฉพาะ tenant
- **ข้อความระบบ** `from_user_id IS NULL`
- **ความเป็นเจ้าของของการอ่าน** `is_read` เป็นของผู้รับ — ผู้เขียนไม่อัปเดต

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: platform schema

### 5.1 `tb_notification`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `from_user_id` / `to_user_id` | `String? @db.Uuid` | Yes | FK ไป `tb_user` `from = NULL` = ระบบ |
| `type` | `String @db.VarChar(255)` | No | Default `SYS_INFO` discriminator (`SYS_INFO`, `BU_INFO`, `PR`, `PR_COMMENT`, `SR`, `SR_COMMENT`, …) |
| `category` | `String @db.VarChar(255)` | No | Default `system` `system` หรือ `user-to-user` |
| `title` / `message` | `String?` | Yes | ข้อความแสดงผล |
| `metadata` | `Json? @db.JsonB` | Yes | Context ต้นทาง (entity_id, route, event id) |
| `is_read` / `is_sent` | `Boolean?` | Yes | Default `false` |
| `scheduled_at` | `DateTime?` | Yes | timestamp การเลื่อน-จนถึง |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.2 `tb_message_format`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ format (เช่น `pr_stage_advanced`) |
| `message` | `String?` | Yes | template body พร้อม token สำหรับ interpolation |
| `is_email` | `Boolean` | No | Default `false` |
| `is_sms` | `Boolean?` | Yes | Default `false` |
| `is_in_app` | `Boolean?` | Yes | Default `true` materialise แถว inbox |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])`

### 5.3 `tb_news`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `title` | `String @db.VarChar` | No | หัวข้อข่าว |
| `contents` | `String? @db.VarChar` | Yes | เนื้อหา |
| `url` / `image` | `String? @db.VarChar` | Yes | URL อ่านต่อ / banner แบบเลือกได้ |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

## 6. กติกาทางธุรกิจ

- **Fan-out ผู้รับ** Event เดียวอาจสร้างแถว `tb_notification` หลายแถว แอปรับผิดชอบ dedup
- **การ dispatch ตาม channel** Flag ใน `tb_message_format` ตัดสินว่าจะส่งผ่าน channel ใด; `is_sent` บันทึกผลลัพธ์
- **สถานะการอ่าน** เป็นของผู้รับ
- **ความ unique ของ format** `name` unique ในแถวที่ไม่ถูกลบ; กู้คืนผ่านการ reactivate หรือ insert ด้วยชื่อใหม่
- **Scope ของข่าว** Global — ผู้ใช้ที่ authenticate ทุกคนข้ามทุก tenant
- **การตั้งเวลา** Dispatcher flip `is_sent` เฉพาะเมื่อ `scheduled_at` fire

## 7. ความเชื่อมโยงข้ามโมดูล

- ทุกโมดูล workflow — [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]]
- [[access-control/user]] — การ resolve `from_user_id` / `to_user_id`
- [[reporting-audit/activity]] — event ของ workflow โดยปกติเขียนทั้งสองแถว
- [[system-config/workflow]] — การ resolve ผู้รับกับ role type ของ stage

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (lines ~267-301), `tb_message_format` (lines ~226-245), `tb_news` (lines ~690-703)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role type ที่ขับ notification
