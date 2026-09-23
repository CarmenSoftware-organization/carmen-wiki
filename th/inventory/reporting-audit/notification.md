---
title: การแจ้งเตือน (Notification)
description: Fan-out การแจ้งเตือนหลัง redesign 2026-08 — แถวส่วนตัว (doc_type + event), broadcast ของระบบ/BU พร้อมสถานะอ่านต่อผู้ใช้แบบ lazy, bridge ภายใน NotifyInput และข่าวแพลตฟอร์มที่ scope ตาม BU พร้อม lifecycle การ publish
published: true
date: 2026-09-23T10:06:26.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# การแจ้งเตือน (Notification)

> **At a Glance**
> **เจ้าของ:** Workflow runtime + micro-cronjobs/micro-report (เขียน) · Platform Admin (broadcast `broadcast.send`, ข่าว) · BU admin (`tb_notification_template` ต่อ BU สำหรับข้อความอีเมล/in-app) &nbsp;·&nbsp; **ตาราง (platform):** `tb_notification` (ส่วนตัว) + `tb_broadcast_notification` / `tb_user_broadcast_action` (broadcast) + `tb_news` &nbsp;·&nbsp; **หายไปแล้ว:** `tb_message_format` (ลบเมื่อ 2026-08-11) &nbsp;·&nbsp; **ใช้โดย:** ทุกการเปลี่ยน stage ของ workflow, comment, การส่งมอบรายงานตามเวลา, ข่าวประกาศแพลตฟอร์ม

![การแจ้งเตือน (Notification) screen](/screenshots/reporting-audit/notification.png)

## สถานะการทำงานจริง (ตรวจสอบซ้ำเมื่อ 2026-09-22)

ตาราง notification ถูก **redesign ในเดือนสิงหาคม 2026** (platform migration `20260810000000_notification_redesign_additive` และ `20260811000000_notification_redesign_drop_legacy`; contract ฝั่ง frontend `ac44c550`) การแก้ไขจากหน้านี้ฉบับ 2026-07-22:

1. `tb_notification` เสีย `type`, `category` และ `is_sent` ไป; ตอนนี้มี `doc_type enum_notification_doc_type` (`system`, `business_unit`, `purchase_request`, `store_requisition`, `purchase_order`, `good_received_note`, `credit_note`), `event enum_notification_event` (`info`, `workflow`, `comment`) และ `pushed_at` string discriminator `SYS_INFO` / `BU_INFO` / `PR_COMMENT` และ category `system` / `user-to-user` หายไปแล้ว
2. `tb_broadcast_notification` เสีย `category` และ `type` ไป; ตอนนี้มี `scope enum_broadcast_scope` (`system` | `business_unit`) + `scope_id` บวกคู่ `doc_type` / `event` แบบเดียวกัน string `'system-to-user'` / `'bu-to-user'` บนหน้านี้คือ contract ก่อน redesign
3. **`tb_message_format` หายไปแล้ว** (ถูกลบโดย migration drop-legacy) พร้อมกับ flag channel `is_email` / `is_sms` / `is_in_app` หน้าจอ **notification template** ต่อ BU ([system-config/notification-template](/th/inventory/system-config/notification-template), ตาราง tenant `tb_notification_template`: `name`, `type enum_notification_channel`, `subject`, `body`, `description`, `is_active`; gateway `api/config/:bu_code/notification-templates`) เป็นฟีเจอร์คนละตัวที่ scope ตาม tenant — ไม่ใช่การเปลี่ยนชื่อ `tb_message_format` `tb_user.is_online` ถูกลบใน migration เดียวกัน
4. เส้นทางการเขียนตอนนี้เป็น envelope ที่ validate แล้วตัวเดียว **`NotifyInput`** (`packages/notification-contract`) ซึ่งเปิดเป็น HTTP bridge ภายใน `POST /api/internal/notifications` ที่ micro-cronjobs และ micro-report ใช้ด้วย (§5.6)
5. inbox แบบรวมได้ `GET /api/notifications/unread` (paginated) และ `GET /api/notifications/recent` (30 วันล่าสุด) เพิ่มมา; response ของรายการมี `source` (`personal` | `broadcast`) ต่อแถว และ `summary { unread, read }` แบบเลือกได้ (ถ้าไม่มีหมายถึง "คำนวณไม่ได้" ไม่ใช่ศูนย์)

ยังคงเป็นจริง: `tb_news` มี BU scoping จริงและ lifecycle `draft` / `published` / `archived` ที่บังคับใช้โดย `news.service.ts`

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี notification คือ **ท่อข้อความขาเข้า** — ทุกการเปลี่ยน stage ของ workflow, comment, การส่งมอบรายงานตามเวลา, ข่าวประกาศของระบบ และข่าวสารของแพลตฟอร์มถูก materialise ขึ้นมาให้ shell ของแอป render badge + drawer inbox (และส่งอีเมลผ่าน email profile ของ BU ได้ตามต้องการ)

ตารางในระดับ platform schema สี่ตัวทำงานร่วมกัน:

- `tb_notification` — inbox ส่วนตัวหนึ่งแถวต่อผู้รับหนึ่งคน (event ของ workflow, comment, แจ้งรายงานพร้อมแล้ว)
- `tb_broadcast_notification` + `tb_user_broadcast_action` — mechanism broadcast: หนึ่งแถวต่อ broadcast ไม่ว่าขนาดกลุ่มผู้รับจะเป็นเท่าไร พร้อมสถานะอ่านต่อผู้ใช้ที่สร้างแบบ lazy ตอน action ครั้งแรก (เปิด/dismiss) แทนที่จะ fan-out ตอนเขียน
- `tb_news` — ข่าวประกาศทั่วทั้งแพลตฟอร์มหรือ scope ตาม BU พร้อม lifecycle `draft` / `published` / `archived`

ทั้งหมดอยู่ใน **platform schema** เพราะการแจ้งเตือนข้ามขอบเขต BU และการ broadcast ต้องเข้าถึงทุก tenant

**ดูแลโดย** workflow runtime และ service อื่น ๆ ผ่าน `NotifyInput` (แถวส่วนตัว + broadcast ต่อ event), Platform Admin (broadcast, ข่าว), BU admin (ข้อความใน `tb_notification_template`) **อ่านโดย** inbox ของ shell แอป (รายการรวมของ `notification.controller.ts` ที่ merge ทั้งสองแหล่ง)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู inbox | shell แอป → กระดิ่ง notification | `GET /api/notifications` (ทั้งหมด, paginated) / `recent` (30 วัน) / `unread`; แถวมี `source`, `doc_type`, `event`, `metadata.id` (id ของเอกสาร) |
| Mark การแจ้งเตือนส่วนตัวเป็นอ่านแล้ว | คลิกข้อความ | `PUT /api/notifications/{id}/read` พร้อม `{ source: "personal" }` (หรือไม่ส่ง) → `tb_notification.is_read = true` |
| Mark broadcast เป็นอ่านแล้ว | คลิกข้อความ | endpoint เดียวกันพร้อม `{ source: "broadcast" }` → upsert แถว `tb_user_broadcast_action` (สร้างแบบ lazy ตอน action ครั้งแรก) |
| Mark ทั้งหมดเป็นอ่านแล้ว | Inbox → mark all | `PUT /api/notifications/mark-all-read` |
| ส่ง broadcast ทั้งระบบหรือระดับ BU | Platform admin | `POST /api/notifications/broadcasts/system` / `broadcasts/bu` — สิทธิ์ platform `broadcast.send`; รายการ/แก้ไข/ลบฝั่งผู้ส่งที่ `GET/PATCH/DELETE /api/notifications/broadcasts[/:id]` |
| แก้ไขข้อความอีเมล workflow / รายงานของ BU นี้ | `/system-admin/notification-template` | แถว `tb_notification_template` ของ tenant ต่อ channel (`enum_notification_channel`) — ดู [system-config/notification-template](/th/inventory/system-config/notification-template) |
| โพสต์ข่าวประกาศแพลตฟอร์ม | Platform Admin → News | Default เป็น `status = draft` — **ไม่** มองเห็นสาธารณะจนกว่าจะตั้งเป็น `published` อย่างชัดเจน; scope เฉพาะ BU ได้ผ่าน `business_unit_ids` |
| ตั้งเวลาการแจ้งเตือน | ตั้ง `scheduled_at` ใน `NotifyInput` | Dispatcher fire เมื่อเวลาผ่าน; `pushed_at` บันทึกการส่ง |
| แจ้งเตือนจาก service อื่น | `POST /api/internal/notifications` | envelope `NotifyInput` (§5.6); ใช้โดยการ fire รายงานของ micro-cronjobs และ micro-report |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ผู้ใช้ไม่ได้รับการแจ้งเตือนที่คาด | การ resolve ผู้รับขาด (`audience.kind = users` ด้วย id ที่ผิด) หรือ email profile ของ BU ไม่ได้ตั้งค่าสำหรับส่งอีเมล | เช็ค recipient map ของ workflow และ email profile ของ BU |
| `400` จาก `/api/internal/notifications` | payload ไม่ผ่าน `NotifyInputSchema` (`doc_type`/`event` ที่ไม่รู้จัก หรือ key จาก branch `audience` ที่ผิด — เช่น `user_ids` กับ `kind: business_unit`) | แก้ envelope |
| `404` จาก `/api/internal/notifications` | `audience.kind = business_unit` ระบุ `bu_code` ที่ไม่รู้จัก | แก้ code |
| สถานะอ่านของ broadcast ไม่ติด | Client ส่ง `source: personal` (หรือไม่ส่ง) สำหรับแถว broadcast | ส่ง `source` ที่ได้จาก endpoint รายการกลับไปตามเดิม |
| inbox มีแถวซ้ำสำหรับ event เดียว | ชุดผู้รับมีรายการซ้ำ | แอปต้อง dedup ก่อน insert |
| คลิกแล้ว 404 | `metadata.id` อ้างอิง entity ของ tenant ที่ถูกลบ | ไม่บังคับ FK; UI ต้องจัดการอย่างนุ่มนวล |

## 4. กรณีพิเศษ

- **การเชื่อมโยงข้าม schema** `metadata` อาจ carry identifier ของ tenant (เส้นทางการเขียนใหม่ใส่ id ของเอกสารใน `metadata.id` เสมอ; แถวเก่าอาจยังมี `pr_id` / `po_id` / `sr_id` / `grn_id` / `cn_id` — ไม่มีแถวใหม่ที่สร้างด้วย key เหล่านั้นอีก) Platform schema ไม่บังคับ FK เข้าตาราง tenant
- **Scope ของข่าวเป็นจริง ไม่ใช่ global เท่านั้น** `business_unit_ids` (JSONB array) — array ว่างหมายถึงมองเห็นได้ทุกที่ (global); array ที่ไม่ว่าง scope เฉพาะ BU เหล่านั้น `findPublicAll()` ใช้ `OR: [{business_unit_ids: {equals: []}}, {business_unit_ids: {array_contains: [bu_id]}}]` เมื่อมี `bu_id` ส่งมา
- **ข่าวมี lifecycle draft/published/archived** `status` default เป็น `draft` ตอนสร้าง; `create()`/`update()` ตั้ง `published_at = now()` อัตโนมัติครั้งแรกที่ `status` เปลี่ยนเป็น `published` (เว้นแต่ส่ง `published_at` มาชัดเจน) Query สาธารณะ filter แบบ hard ด้วย `status: published AND published_at <= now()`
- **สถานะการอ่านของ broadcast เป็นแบบ lazy ไม่ fan-out** แถว `tb_user_broadcast_action` ถูกสร้างตอน action อ่าน/dismiss ครั้งแรกต่อผู้ใช้ — นี่คือเหตุผลการออกแบบที่ชัดเจนว่าทำไม `tb_broadcast_notification` มาแทนที่ fan-out แบบต่อผู้รับของ `tb_notification` เดิมสำหรับ broadcast
- **ข้อความระบบ** `from_user_id IS NULL` (ส่วนตัว); broadcast ไม่มี `from_user_id` เลย
- **ความเป็นเจ้าของของการอ่าน** `is_read` (ส่วนตัว) / `tb_user_broadcast_action.is_read` (broadcast) ทั้งคู่เป็นของผู้รับ — ผู้เขียนไม่อัปเดต
- **`summary` เป็นตัวเลือก** endpoint รายการคำนวณ `{ unread, read }` ใน try/catch; ถ้า summary หายไปหมายถึงนับไม่ได้ ไม่ใช่ว่าเป็นศูนย์ (`types/notification.ts`)

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: platform schema (`packages/prisma-shared-schema-platform/prisma/schema.prisma`)

### 5.1 `tb_notification`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `from_user_id` / `to_user_id` | `String? @db.Uuid` | Yes | FK ไป `tb_user` `from = NULL` = ระบบ |
| `doc_type` | `enum_notification_doc_type` | No | `system`, `business_unit`, `purchase_request`, `store_requisition`, `purchase_order`, `good_received_note`, `credit_note` |
| `event` | `enum_notification_event` | No | `info`, `workflow`, `comment` |
| `title` / `message` | `String?` | Yes | ข้อความแสดงผล |
| `metadata` | `Json? @db.JsonB` | Yes | Context ต้นทาง — `id` (id ของเอกสาร), `action`, `current_stage`, `is_fully_approved`, … |
| `is_read` | `Boolean?` | Yes | Default `false` |
| `scheduled_at` / `pushed_at` | `DateTime?` | Yes | เลื่อน-จนถึง / ส่งแล้วเมื่อ |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `[to_user_id, is_read, created_at DESC]`, `[deleted_at]` ลบเมื่อ 2026-08-11: `type`, `category`, `is_sent`

### 5.2 `tb_broadcast_notification`

หนึ่งแถวต่อ broadcast ไม่ว่าขนาดกลุ่มผู้รับจะเป็นเท่าไร

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `scope` | `enum_broadcast_scope` | No | `system` (ทั้งแพลตฟอร์ม) หรือ `business_unit` |
| `scope_id` | `String? @db.Uuid` | Yes | `business_unit.id` เมื่อ `scope = business_unit`; `null` สำหรับ `system` |
| `doc_type` / `event` | enum ตามข้างต้น | No | discriminator เดียวกับ `tb_notification` |
| `title` / `message` | `String?` | Yes | ข้อความแสดงผล |
| `metadata` | `Json? @db.JsonB` | Yes | context ต้นทาง |
| `scheduled_at` / `end_at` | `DateTime?` | Yes | เลื่อน-จนถึง / หมดอายุ |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

ลบเมื่อ 2026-08-11: `category`, `type`

### 5.3 `tb_user_broadcast_action`

สถานะอ่าน/dismiss ต่อผู้ใช้สำหรับ broadcast — สร้างแบบ lazy ตอน action ครั้งแรก

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `broadcast_id` | `String @db.Uuid` | No | FK ไป `tb_broadcast_notification`, `onDelete: Cascade` |
| `user_id` | `String @db.Uuid` | No | FK ไป `tb_user` |
| `is_read` | `Boolean?` | Yes | Default `false` |
| `read_at` / `dismissed_at` | `DateTime?` | Yes | timestamp |
| `doc_version` | `Int @db.Integer` | No | Default `0` |
| คอลัมน์ audit | — | Yes | `created_at`, `updated_at` เท่านั้น (ไม่มี soft delete) |

**Constraints:** `@@unique([broadcast_id, user_id])`; `@@index([user_id, is_read])`

### 5.4 `tb_message_format` — ถูกลบแล้ว

ถูกลบโดย `20260811000000_notification_redesign_drop_legacy` ไม่มีอะไรมาแทน flag channel ระดับแพลตฟอร์มของมัน; ข้อความต่อ BU อยู่ใน `tb_notification_template` ของ tenant ([system-config/notification-template](/th/inventory/system-config/notification-template)) และการส่งตาม channel (web / email) ถูกตัดสินต่อการเรียกโดยผู้เขียน (เช่น `notifications { web, email }` ของ report schedule)

### 5.5 `tb_news`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `title` | `String @db.VarChar` | No | หัวข้อข่าว |
| `contents` | `String? @db.VarChar` | Yes | เนื้อหา |
| `url` | `String? @db.VarChar` | Yes | URL อ่านต่อแบบเลือกได้ |
| `image_file_token` | `String? @db.VarChar` | Yes | รูป banner — เป็น token ของ `tb_file_tag` (ดู [reporting-audit/attachment](/th/inventory/reporting-audit/attachment)) |
| `business_unit_ids` | `Json @db.JsonB` | No | Default `[]` ว่าง = ทุก BU (global); ไม่ว่าง = scope เฉพาะ BU id เหล่านั้น |
| `tags` | `Json @db.JsonB` | No | Default `[]` normalize เป็นตัวพิมพ์เล็ก, ไม่ซ้ำ, สูงสุด 20 tag ยาวไม่เกิน 40 ตัวอักษรต่อ tag |
| `status` | `enum_news_status` | No | Default `draft` `draft` / `published` / `archived` |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | ตั้งอัตโนมัติเมื่อเปลี่ยนเป็น `published` ครั้งแรก เว้นแต่ส่งมาชัดเจน |
| `doc_version` | `Int @db.Integer` | No | Default `0` ต้องระบุทุกครั้งที่ update (มิฉะนั้น `COMMON_DOC_VERSION_REQUIRED`) |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `[status, published_at]` (`tb_news_status_published_at_idx`)

### 5.6 envelope `NotifyInput` (`packages/notification-contract`)

```
NotifyInput {
  doc_type:  enum_notification_doc_type
  event:     enum_notification_event
  title, message: string
  audience:  { kind: "users", user_ids: uuid[] }
           | { kind: "business_unit", bu_code: string }
           | { kind: "all_users" }
  from_user_id?, doc_id?, bu_code?, scheduled_at?, metadata?
}
```

`kind = users` เขียน `tb_notification` หนึ่งแถวต่อ id; `business_unit` / `all_users` เขียน `tb_broadcast_notification` หนึ่งแถวด้วย `scope = business_unit` / `system` key จาก branch ที่ผิดจะถูกปฏิเสธ เปิดให้ผู้เรียกที่ไม่ใช่ NestJS ผ่าน `POST /api/internal/notifications` (`internal-notification.controller.ts`, 201 เมื่อสำเร็จ) — ใช้โดย micro-cronjobs สำหรับแจ้งรายงานพร้อมแล้ว และโดย micro-report (`pkg/notify/client.go`, HTTP RPC `POST /rpc` `{ pattern, data }` พร้อม `x-internal-token`)

## 6. กติกาทางธุรกิจ

- **Mechanism การส่งมอบสองแบบ envelope เดียว** Event ส่วนตัวต่อผู้รับใช้ `tb_notification`; broadcast ของระบบ/BU ใช้ `tb_broadcast_notification` + แถว `tb_user_broadcast_action` ที่สร้างแบบ lazy ทั้งสองแบบผลิตจาก `NotifyInput.audience.kind`
- **สถานะการอ่าน** เป็นของผู้รับในทั้งสอง mechanism; client ต้องส่ง `source` ของแถวกลับไปตอน mark อ่านแล้ว
- **การส่ง broadcast เป็นสิทธิ์ระดับ platform** (`broadcast.send`) ไม่ใช่สิทธิ์ tenant
- **ข่าว scope ตาม BU ได้และถูกจำกัดด้วยสถานะ publish** `business_unit_ids` (ว่าง = global) และ `status` (default `draft`; มีเฉพาะแถว `published` + `published_at <= now()` เท่านั้นที่มองเห็นสาธารณะ) ทั้งคู่บังคับใช้ที่ server ใน `news.service.ts`
- **การตั้งเวลา** `scheduled_at` เลื่อนการส่ง; `pushed_at` บันทึกการส่ง (ส่วนตัว) `tb_broadcast_notification` มี `scheduled_at` / `end_at`; mechanism การจับเวลา dispatch ของ broadcast ยังไม่ได้ตรวจสอบแยกในรอบนี้

## 7. ความเชื่อมโยงข้ามโมดูล

- ทุกโมดูล workflow — [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [vendor-pricelist](/th/inventory/vendor-pricelist) — แถว `event = workflow` / `comment` ผ่าน `NotifyInput`
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — schedule รายงานที่ fire ส่ง `POST /api/internal/notifications` หนึ่งครั้งต่อผู้รับที่ `notify_at` ไม่ใช่ broadcast
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — `tb_news.image_file_token` อ้างอิง registry `tb_file_tag` เดียวกัน
- [access-control/user](/th/inventory/access-control/user) — การ resolve `from_user_id` / `to_user_id` / `user_id`
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — event ของ workflow โดยปกติเขียนทั้งแถว activity และ notification
- [system-config/workflow](/th/inventory/system-config/workflow) — การ resolve ผู้รับกับ role type ของ stage
- [system-config/notification-template](/th/inventory/system-config/notification-template) — ข้อความต่อ BU

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification`, `tb_broadcast_notification`, `tb_user_broadcast_action`, `tb_news`, `enum_notification_doc_type`, `enum_notification_event`, `enum_broadcast_scope`, `enum_news_status`; migration `20260810000000_notification_redesign_additive`, `20260811000000_notification_redesign_drop_legacy`
- **Contract:** `../carmen-turborepo-backend-v2/packages/notification-contract/src/notify-input.schema.ts`
- **Backend (อ่าน/เขียนแบบรวม):** `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.service.ts`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` (`GET /`, `recent`, `unread`, `broadcasts*`, `:id`, `PUT :id/read`, `PUT mark-all-read`, `POST broadcasts/system|bu`), `internal-notification.controller.ts` (`POST /api/internal/notifications`)
- **Backend (ข่าว):** `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (CRUD ของ admin), `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/public-news.service.ts` (อ่านสาธารณะ)
- **Backend (template ต่อ BU):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_notification-templates/config_notification-templates.controller.ts`; `tb_notification_template` ของ tenant (migration `20260525041511_add_notification_template`)
- **Frontend:** `../carmen-inventory-frontend-react/types/notification.ts` (`Notification`, `NotificationSource`, `NotificationDocType`, `NotificationListResponse.summary`), `constant/api-endpoints.ts` (`NOTIFICATIONS`, `NOTIFICATIONS_UNREAD`, `NOTIFICATIONS_MARK_ALL_READ`, `NOTIFICATION_MARK_READ`, `NOTIFICATION_TEMPLATES`)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role type ที่ขับ notification (freeze เมื่อ 2026-04-27; ก่อน redesign)
