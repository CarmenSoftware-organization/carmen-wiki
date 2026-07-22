---
title: การแจ้งเตือน (Notification)
description: Fan-out การแจ้งเตือนข้าม tenant — แถว notification ส่วนตัว บวก mechanism broadcast แยกต่างหากที่ใหม่กว่า (tb_broadcast_notification + tb_user_broadcast_action), message template ที่ใช้ซ้ำได้ และข่าวประกาศแพลตฟอร์มที่มี BU scoping จริงและ lifecycle draft/published/archived
published: true
date: 2026-07-22T03:05:28.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# การแจ้งเตือน (Notification)

> **At a Glance**
> **เจ้าของ:** Workflow runtime (เขียน) + Sysadmin / Platform Admin (template และข่าว) &nbsp;·&nbsp; **ตาราง:** `tb_notification` (ส่วนตัว) + `tb_broadcast_notification` / `tb_user_broadcast_action` (broadcast — ยังไม่เคยบันทึกไว้ก่อนหน้านี้) + `tb_message_format` + `tb_news` &nbsp;·&nbsp; **ใช้โดย:** ทุกการเปลี่ยน stage ของ workflow + การส่งมอบรายงานตามเวลา &nbsp;·&nbsp; ท่อข้อความขาเข้า — inbox ส่วนตัว, broadcast ของ BU/ระบบ, template, ข่าวประกาศแพลตฟอร์ม

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

หน้านี้ฉบับก่อนหน้ามีสองจุดที่ต้องแก้ไข:

1. **มี mechanism broadcast แยกต่างหากที่ยังไม่เคยบันทึกไว้** `tb_broadcast_notification` (หนึ่งแถวต่อ broadcast, `category` = `'system-to-user'` หรือ `'bu-to-user'`, `scope_id` = `business_unit.id` สำหรับ broadcast ที่ scope ด้วย BU) + `tb_user_broadcast_action` (สถานะอ่าน/dismiss ต่อผู้ใช้ สร้างแบบ lazy ตอน action ครั้งแรก) ยืนยันแล้วว่า **มีอยู่จริงและใช้งานอยู่** — ถูกอ่าน/เขียนใช้งานจริงใน `micro-notification/src/notification/notification.service.ts` และเปิดผ่าน `backend-gateway/src/notification/notification.controller.ts` Prisma doc-comment ของมันเอง (บน `model tb_broadcast_notification`, `prisma-shared-schema-platform/schema.prisma` บรรทัด ~372) ระบุไว้ชัดเจน: *"This replaces the previous fan-out-on-write pattern that inserted one `tb_notification` row per recipient for the same broadcast message."* `tb_notification` ยังคงมีอยู่จริงและใช้งานอยู่สำหรับการแจ้งเตือน**ส่วนตัว**ต่อผู้รับ (event ของ workflow, การส่งมอบรายงานตามเวลา — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)); รายการ inbox แบบรวมจะ merge ทั้งสองแหล่ง (`source: 'personal' | 'broadcast'`) เป็น response shape เดียวสำหรับ frontend
2. **`tb_news` มี BU scoping จริงและมี lifecycle draft/published/archived** — ตรงข้ามกับที่หน้านี้เคยระบุไว้ `business_unit_ids` (JSONB array; ว่าง = global, ไม่ว่าง = scope เฉพาะ BU เหล่านั้น) และ `status enum_news_status` (default `draft`, `published`, `archived`) มีอยู่จริงทั้งคู่และถูกบังคับใช้โดย `news.service.ts`: โพสต์ที่เพิ่งสร้างจะ default เป็น `draft` และมองไม่เห็นจาก `findPublicAll()`/`findPublicOne()` (ทั้งคู่กรอง `status: published` แบบ hard filter) จนกว่าจะ publish อย่างชัดเจน

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี notification คือ **ท่อข้อความขาเข้า** — ทุกการเปลี่ยน stage ของ workflow, การ mention ใน comment, ข่าวประกาศของระบบ และข่าวสารของแพลตฟอร์มถูก materialise ขึ้นมาให้ shell ของแอป render badge + drawer inbox และสามารถ dispatch ผ่านอีเมล, SMS หรือ push ได้

ตารางในระดับ platform schema ห้าตัวทำงานร่วมกัน:

- `tb_notification` — inbox ส่วนตัวหนึ่งแถวต่อผู้รับหนึ่งคน (event ของ workflow, การส่งมอบรายงานตามเวลา)
- `tb_broadcast_notification` + `tb_user_broadcast_action` — mechanism broadcast จริงและปัจจุบัน: หนึ่งแถวต่อ broadcast ไม่ว่าขนาดกลุ่มผู้รับจะเป็นเท่าไร พร้อมสถานะอ่านต่อผู้ใช้ที่สร้างแบบ lazy ตอน action ครั้งแรก (เปิด/dismiss) แทนที่จะ fan-out ตอนเขียน
- `tb_message_format` — template ที่ใช้ซ้ำได้พร้อม flag channel `is_email` / `is_sms` / `is_in_app`
- `tb_news` — ข่าวประกาศทั่วทั้งแพลตฟอร์มหรือ scope ตาม BU พร้อม lifecycle `draft`/`published`/`archived`

ทั้งหมดอยู่ใน **platform schema** เพราะการแจ้งเตือนข้ามขอบเขต BU และการ broadcast ต้องเข้าถึงทุก tenant

**ดูแลโดย** workflow runtime (เขียนแถวส่วนตัว + broadcast ต่อ event), Sysadmin (template), Platform Admin (ข่าว) **อ่านโดย** inbox ของ shell แอป (รายการรวมของ `notification.controller.ts` ที่ merge `tb_notification` + `tb_broadcast_notification`) และ widget บน dashboard

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู inbox | shell แอป → กระดิ่ง notification | รายการรวมที่ merge `tb_notification` (`source: 'personal'`) และ `tb_broadcast_notification` (`source: 'broadcast'`) |
| Mark การแจ้งเตือนส่วนตัวเป็นอ่านแล้ว | คลิกข้อความ | อัปเดต `tb_notification.is_read = true` |
| Mark broadcast เป็นอ่านแล้ว | คลิกข้อความ | Client ส่ง `category` ที่ได้รับมา (`system-to-user`/`bu-to-user`); backend upsert แถว `tb_user_broadcast_action` (สร้างแบบ lazy ตอน action ครั้งแรก ไม่ได้สร้างล่วงหน้าต่อผู้รับ) |
| แก้ไข message template | Sysadmin → Platform Config → Message Formats | ส่งผลต่อทุก event ที่ใช้ format นั้น |
| โพสต์ข่าวประกาศแพลตฟอร์ม | Platform Admin → News | Default เป็น `status = draft` — **ไม่** มองเห็นสาธารณะจนกว่าจะตั้งเป็น `published` อย่างชัดเจน; scope เฉพาะ BU ได้ผ่าน `business_unit_ids` |
| ตั้งเวลาการแจ้งเตือน | ตั้ง `scheduled_at` | Dispatcher fire เมื่อเวลาผ่าน |
| ส่ง dispatch ซ้ำ | re-process ผ่าน channel ขาออก | `is_sent` ติดตามการส่งต่อ channel (เฉพาะ `tb_notification` ส่วนตัว) |

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
- **Scope ของข่าวเป็นจริง ไม่ใช่ global เท่านั้น** `business_unit_ids` (JSONB array) — array ว่างหมายถึงมองเห็นได้ทุกที่ (global); array ที่ไม่ว่าง scope เฉพาะ BU เหล่านั้น `findPublicAll()` ใช้ `OR: [{business_unit_ids: {equals: []}}, {business_unit_ids: {array_contains: [bu_id]}}]` เมื่อมี `bu_id` ส่งมา
- **ข่าวมี lifecycle draft/published/archived** `status` default เป็น `draft` ตอนสร้าง; `create()`/`update()` ตั้ง `published_at = now()` อัตโนมัติครั้งแรกที่ `status` เปลี่ยนเป็น `published` (เว้นแต่ส่ง `published_at` มาชัดเจน) Query สาธารณะ filter แบบ hard ด้วย `status: published AND published_at <= now()` — โพสต์ draft มองไม่เห็นนอกหน้าจอ admin
- **สถานะการอ่านของ broadcast เป็นแบบ lazy ไม่ fan-out** แถว `tb_user_broadcast_action` ถูกสร้างตอน action อ่าน/dismiss ครั้งแรกต่อผู้ใช้ ไม่ได้ insert ล่วงหน้าให้ผู้รับที่มีสิทธิ์ทุกคนตอนสร้าง broadcast — นี่คือเหตุผลการออกแบบที่ชัดเจนว่าทำไม `tb_broadcast_notification` มาแทนที่ fan-out แบบต่อผู้รับของ `tb_notification` เดิมสำหรับ broadcast
- **ข้อความระบบ** `from_user_id IS NULL` (ส่วนตัว) / broadcast ไม่มีข้อกำหนด `from_user_id` เลย
- **ความเป็นเจ้าของของการอ่าน** `is_read` (ส่วนตัว) / `tb_user_broadcast_action.is_read` (broadcast) ทั้งคู่เป็นของผู้รับ — ผู้เขียนไม่อัปเดต

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
| `doc_version` | `Int @db.Integer` | No | Default `0` เพิ่มเมื่อ 2026-06-12 ทั่ว 103 ตาราง platform/tenant |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.2 `tb_broadcast_notification` (มีอยู่จริง ยังไม่เคยบันทึกไว้ก่อนหน้านี้)

หนึ่งแถวต่อ broadcast ไม่ว่าขนาดกลุ่มผู้รับจะเป็นเท่าไร — มาแทนที่ fan-out แบบต่อผู้รับของ `tb_notification` เดิมสำหรับข้อความระดับระบบและระดับ BU

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `category` | `String @db.VarChar(50)` | No | `'system-to-user'` (ทั้งแพลตฟอร์ม) หรือ `'bu-to-user'` (BU เดียว) |
| `scope_id` | `String? @db.Uuid` | Yes | `business_unit.id` เมื่อ `category = 'bu-to-user'`; `null` สำหรับ `'system-to-user'` |
| `type` | `String @db.VarChar(255)` | No | Default `SYS_INFO` ใช้ discriminator space เดียวกับ `tb_notification.type` |
| `title` / `message` | `String?` | Yes | ข้อความแสดงผล |
| `metadata` | `Json? @db.JsonB` | Yes | context ต้นทาง |
| `scheduled_at` / `end_at` | `DateTime?` | Yes | เลื่อน-จนถึง / หมดอายุ |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `[category, scope_id, created_at DESC]`, `[deleted_at]`

### 5.3 `tb_user_broadcast_action` (มีอยู่จริง ยังไม่เคยบันทึกไว้ก่อนหน้านี้)

สถานะอ่าน/dismiss ต่อผู้ใช้สำหรับ broadcast — สร้างแบบ lazy ตอน action ครั้งแรก ไม่ได้ insert ล่วงหน้าให้ผู้รับที่มีสิทธิ์ทุกคน

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `broadcast_id` | `String @db.Uuid` | No | FK ไป `tb_broadcast_notification`, `onDelete: Cascade` |
| `user_id` | `String @db.Uuid` | No | FK ไป `tb_user`, `onDelete: Cascade` |
| `is_read` | `Boolean?` | Yes | Default `false` |
| `read_at` / `dismissed_at` | `DateTime?` | Yes | timestamp |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| คอลัมน์ audit | — | Yes | `created_at`, `updated_at` เท่านั้น (ไม่มี soft delete) |

**Constraints:** `@@unique([broadcast_id, user_id])`; `@@index([user_id, is_read])`

### 5.4 `tb_message_format`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ format (เช่น `pr_stage_advanced`) |
| `message` | `String?` | Yes | template body พร้อม token สำหรับ interpolation |
| `is_email` | `Boolean` | No | Default `false` |
| `is_sms` | `Boolean?` | Yes | Default `false` |
| `is_in_app` | `Boolean?` | Yes | Default `true` materialise แถว inbox |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])`

### 5.5 `tb_news` (แก้ไขแล้ว — มี BU scoping จริงและ lifecycle การ publish)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `title` | `String @db.VarChar` | No | หัวข้อข่าว |
| `contents` | `String? @db.VarChar` | Yes | เนื้อหา |
| `url` | `String? @db.VarChar` | Yes | URL อ่านต่อแบบเลือกได้ |
| `image_file_token` | `String? @db.VarChar` | Yes | รูป banner — เป็น token ของ `tb_file_tag` (ดู [reporting-audit/attachment](/th/inventory/reporting-audit/attachment)) **ไม่ใช่** `image` URL ดิบตามที่เคยบันทึกไว้ |
| `business_unit_ids` | `Json @db.JsonB` | No | Default `[]` ว่าง = ทุก BU (global); ไม่ว่าง = scope เฉพาะ BU id เหล่านั้น |
| `tags` | `Json @db.JsonB` | No | Default `[]` normalize เป็นตัวพิมพ์เล็ก, ไม่ซ้ำ, สูงสุด 20 tag ยาวไม่เกิน 40 ตัวอักษรต่อ tag |
| `status` | `enum_news_status` | No | Default `draft` `draft` / `published` / `archived` |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | ตั้งอัตโนมัติเมื่อเปลี่ยนเป็น `published` ครั้งแรก เว้นแต่ส่งมาชัดเจน |
| `doc_version` | `Int @db.Integer` | No | Default `0` ต้องระบุทุกครั้งที่ update (มิฉะนั้น error `COMMON_DOC_VERSION_REQUIRED`) |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `[status, published_at]` (`tb_news_status_published_at_idx`)

## 6. กติกาทางธุรกิจ

- **Mechanism การส่งมอบสองแบบที่แยกอิสระต่อกัน** Event ส่วนตัวต่อผู้รับใช้ `tb_notification` (หนึ่งแถวต่อผู้รับ แอปรับผิดชอบ dedup) Broadcast ของ BU/ระบบใช้ `tb_broadcast_notification` (หนึ่งแถวไม่ว่าขนาดกลุ่มผู้รับ) + แถว `tb_user_broadcast_action` ที่สร้างแบบ lazy
- **การ dispatch ตาม channel** Flag ใน `tb_message_format` ตัดสินว่าจะส่งผ่าน channel ใด; `is_sent` บันทึกผลลัพธ์ — ใช้กับ `tb_notification` เท่านั้น (ไม่พบ flag การ dispatch ต่อ channel บนตาราง broadcast)
- **สถานะการอ่าน** เป็นของผู้รับในทั้งสอง mechanism — `tb_notification.is_read` เทียบกับ `tb_user_broadcast_action.is_read`/`read_at`/`dismissed_at`
- **ความ unique ของ format** `tb_message_format.name` unique ในแถวที่ไม่ถูกลบ; กู้คืนผ่านการ reactivate หรือ insert ด้วยชื่อใหม่
- **ข่าว scope ตาม BU ได้และถูกจำกัดด้วยสถานะ publish** `business_unit_ids` (ว่าง = global) และ `status` (default `draft`; มีเฉพาะแถว `published` + `published_at <= now()` เท่านั้นที่มองเห็นสาธารณะ) ทั้งคู่บังคับใช้ที่ server ใน `news.service.ts`
- **การตั้งเวลา** Dispatcher flip `is_sent` เฉพาะเมื่อ `scheduled_at` fire (`tb_notification` ส่วนตัว); `tb_broadcast_notification` ก็มี `scheduled_at`/`end_at` แต่ mechanism การจับเวลา dispatch ของ broadcast ยังไม่ได้ตรวจสอบแยกในรอบนี้

## 7. ความเชื่อมโยงข้ามโมดูล

- ทุกโมดูล workflow — [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [vendor-pricelist](/th/inventory/vendor-pricelist)
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — schedule รายงานที่ fire dispatch `POST /api/internal/notifications` หนึ่งครั้งต่อผู้รับ (ส่วนตัว, `type: REPORT_READY`) ไม่ใช่ broadcast
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — `tb_news.image_file_token` อ้างอิง registry `tb_file_tag` เดียวกัน
- [access-control/user](/th/inventory/access-control/user) — การ resolve `from_user_id` / `to_user_id` / `user_id`
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — event ของ workflow โดยปกติเขียนทั้งแถว activity และ notification
- [system-config/workflow](/th/inventory/system-config/workflow) — การ resolve ผู้รับกับ role type ของ stage

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_message_format` (บรรทัด ~289), `tb_notification` (บรรทัด ~332), `tb_broadcast_notification` (ใกล้ `tb_news`), `tb_user_broadcast_action` (บรรทัด ~406), `tb_news` (บรรทัด ~834), `enum_news_status` (บรรทัด ~723)
- **Backend (อ่าน/เขียนแบบรวมของส่วนตัว + broadcast):** `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.service.ts`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts`
- **Backend (ข่าว):** `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (CRUD ของ admin), `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/public-news.service.ts` (อ่านสาธารณะ)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role type ที่ขับ notification
