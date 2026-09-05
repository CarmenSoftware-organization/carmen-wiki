---
title: Broadcasts — แบบจำลองข้อมูล (Data Model)
description: ตาราง field ของ tb_broadcast_notification และ tb_user_broadcast_action หลังการปรับใหญ่ระบบ notification — enum scope/doc_type/event แทนที่คอลัมน์ category/type แบบ varchar, doc_version เป็น optimistic lock จริง, end_at บังคับ และทางแยกของการส่งแบบระบุผู้รับลง tb_notification
published: true
date: 2026-09-05T22:00:00.000Z
tags: book/platform, broadcasts, data-model
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# Broadcasts — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_broadcast_notification` (หนึ่ง row ต่อหนึ่ง broadcast แบบ `system_all`/`bu`) + `tb_user_broadcast_action` (read state รายผู้ใช้แบบ lazy, unique ต่อ broadcast×user) &nbsp;·&nbsp; **ทางแยกของการกำหนดเป้าหมาย:** การส่งแบบ `system_users` (`userIds`) ข้ามทั้งสองตารางและ fan out ลง `tb_notification` (row ส่วนบุคคลหนึ่งตัวต่อผู้รับ) — มองไม่เห็นจากหน้า List/Edit ฝั่งแอดมิน &nbsp;·&nbsp; **เป็น enum ไม่ใช่ varchar:** `scope` (`enum_broadcast_scope`), `doc_type`/`event` (`enum_notification_doc_type`/`enum_notification_event`, ใช้ร่วมกับ `tb_notification`) แทนที่คอลัมน์ `category`/`type` แบบ varchar เดิม &nbsp;·&nbsp; **ไม่มีคอลัมน์ severity:** ป้าย Info/Warning/Critical/Maintenance/Other… ของผู้ส่งอยู่ใน `metadata.severity` เท่านั้น; `event` ถูก hardcode เป็น `info` ทุก broadcast &nbsp;·&nbsp; **`end_at` บังคับแล้ว** และเป็นตัวขับ `status` ที่คำนวณได้ (ไม่เคยเป็นคอลัมน์ที่เก็บจริง) &nbsp;·&nbsp; **`doc_version` เป็น optimistic lock จริง** แล้ว ทั้ง `PATCH` และ `DELETE` ตรวจสอบมัน &nbsp;·&nbsp; **Endpoint:** `POST /api/notifications/broadcasts/system` / `/bu` (ส่ง) บวก `GET`/`GET :id`/`PATCH :id`/`DELETE :id` — `/api` **ไม่ใช่** `/api-system`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูลนี้เป็นเจ้าของสองตาราง บวกทางแยกไปยังตารางที่สาม `tb_broadcast_notification` คือหนึ่ง row ต่อหนึ่งข้อความแบบ `system_all`/`bu` ไม่ว่ากลุ่มผู้ชมจะใหญ่แค่ไหน โดยกลุ่มผู้ชมถูก encode เป็น `scope` (`system` หรือ `business_unit`) บวก `scope_id` ส่วน `tb_user_broadcast_action` ถือ state รายผู้ใช้ — ถูกสร้างแบบ **lazy** เฉพาะเมื่อผู้ใช้กระทำ action (mark ว่าอ่านแล้ว) เท่านั้น; การไม่มี row หมายถึง "ยังไม่ได้กระทำ" และ query ของ unread ใช้ LEFT JOIN เพื่อดึง broadcast ที่ไม่มี row ขึ้นมา

การส่งแบบ **`system_users`** (รายการ `userIds` แบบระบุชัด) ข้ามตาราง broadcast ทั้งสองไปเลยและ fan out ลง `tb_notification` — หนึ่ง row **ต่อ id ผู้รับที่มีอยู่จริง** (id ที่ไม่รู้จักถูกทิ้งเงียบ ๆ) นี่ไม่ใช่ของเก่าที่กำลังถูกเลิกใช้ — มันคือวิธีเดียวที่โมดูลนี้รองรับให้แจ้งเตือนรายชื่อที่เลือกเองได้ และมันยังเป็น target mode เดียวที่หน้าแอดมินฝั่งผู้ส่งอย่าง **List** และ **Edit** มองไม่เห็น ค้นหาไม่ได้ แก้ไม่ได้ หรือลบภายหลังไม่ได้เลย — `GET .../broadcasts` (§6) query เฉพาะ `tb_broadcast_notification` เท่านั้น subtitle ของหน้า Compose เองก็บอกไว้ตรง ๆ: *"ประกาศที่ส่งถึงผู้ใช้ที่ระบุเจาะจงจะไม่แสดงที่นี่ — ถูกบันทึกเป็นการแจ้งเตือนรายบุคคล"*

เส้นทาง persistence คือ backend-gateway (`api/notifications/broadcasts/*`, `KeycloakGuard` + `PlatformPermissionGuard`) → RPC → micro-notification ฝั่ง notification แบ่งงานเป็นสอง service: **`BroadcastService`** ดูแลเส้นทางสร้าง (resolve `bu_code`, เขียน row, upsert ของ read-state และตัวช่วย resolve ผู้รับที่ live push ใช้) และ **`BroadcastAdminService`** ดูแล surface list/get/update/delete ฝั่งผู้ส่ง รวมถึงการคำนวณ status **`NotificationWriteService`** คือจุดเข้าเดียวสำหรับเขียนของ `notifications.create`: มันส่งต่อให้ `BroadcastService` สำหรับ audience ที่ไม่ใช่ `users` และเขียน row ของ `tb_notification` โดยตรง ใน transaction เดียว สำหรับ audience แบบ `users`

## 2. เอนทิตี

### 2.1 `tb_broadcast_notification`

ข้อความ broadcast แบบ `system_all`/`bu` หนึ่งข้อความ Schema บรรทัด 369

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, ค่าเริ่มต้น `gen_random_uuid()` |
| `scope_id` | `String? @db.Uuid` | Yes | `tb_business_unit.id` เมื่อ `scope = 'business_unit'`; `null` สำหรับ `'system'` resolve ที่ฝั่ง server จาก `bu_code` ใน payload (เฉพาะ BU ที่ยัง live) — row เก็บ UUID ที่มั่นคง ไม่ใช่ code ที่เปลี่ยนชื่อได้ |
| `title` | `String?` | Yes | หัวข้อการแจ้งเตือน (SPA บังคับ; คอลัมน์ไม่บังคับ) |
| `message` | `String?` | Yes | เนื้อหาการแจ้งเตือน (เหมือนกัน — บังคับแค่ฝั่ง SPA) |
| `metadata` | `Json? @db.JsonB` | Yes | รูปแบบอิสระ เก็บป้าย `severity` ที่เป็นแค่ตกแต่งของผู้ส่ง บวก `bu_code`/`id` ที่ server merge ให้ — ดู §5 |
| `scheduled_at` | `DateTime? @db.Timestamptz(6)` | Yes | จุดตัดการมองเห็น: list query จะซ่อน row จนกว่า `scheduled_at <= NOW()` |
| `end_at` | `DateTime? @db.Timestamptz(6)` | Yes | **บังคับตอนส่ง** (ทั้ง SPA และ Zod request schema บังคับ) — เป็น input หลักของ `deriveStatus()`: `end_at` ที่ผ่านมาแล้วแปลว่า `expired` |
| `doc_type` | `enum_notification_doc_type` | No | `system` สำหรับ `system_all`/`system_users`, `business_unit` สำหรับ `bu` — ตั้งค่าตอนสร้างจาก request path ไม่ใช่ input ของผู้ใช้ |
| `event` | `enum_notification_event` | No | **Hardcode เป็น `info`** ในทุก broadcast ที่สร้างผ่านสอง send endpoint ของโมดูลนี้ — ผู้ส่งไม่มีทางทำให้ broadcast มีค่า event อื่นได้เลย |
| `scope` | `enum_broadcast_scope` | No | `system` หรือ `business_unit` — แทนที่ `category` varchar เดิมก่อนปรับใหญ่ (`'system-to-user'`/`'bu-to-user'`) |
| `doc_version` | `Int @default(0) @db.Integer` | No | **เป็น optimistic lock จริงแล้ว** `BroadcastAdminService.update()`/`.remove()` อ่านค่านี้ เทียบกับค่าที่ผู้เรียกส่งมา (409 ถ้าไม่ตรง) และเขียนแบบมีเงื่อนไข (`updateMany` ใส่ `doc_version` ไว้ใน `where`, `{ increment: 1 }` ใน `data`) เพื่อไม่ให้ PATCH สองอันพร้อมกัน "ชนะ" ทั้งคู่ |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row; เป็น sort key เริ่มต้นของ list ด้วย |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit/ผู้ส่ง: FK → `tb_user` ถูกเติมด้วยผู้ใช้จาก token ในการปรับใหญ่ครั้งนี้ (ทั้งเส้นทาง system และ BU) |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | **เขียนทุกครั้งที่ `PATCH`/`DELETE` สำเร็จ** แล้วตอนนี้ — แต่ API ไม่เคยส่งกลับมา (ดู §5) |
| `updated_by_id` | `String? @db.Uuid` | Yes | **เขียนทุกครั้งที่ `PATCH`/`DELETE` สำเร็จ** — มีข้อจำกัดเรื่องมองไม่เห็นเหมือนกัน |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft delete **`DELETE /api/notifications/broadcasts/:id` เขียนคอลัมน์นี้แล้ว** — มี code path จริงเกิดขึ้นแล้ว แทนที่ผลตรวจสอบเดิมที่บอกว่า "ไม่มี code path ใดเขียนมันเลย" |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: FK → `tb_user` เขียนโดย path การลบเดียวกัน |

**Constraints:** `@id` บน `id` FK relation: `created_by_id`/`updated_by_id` → `tb_user.id` (`onDelete: NoAction`) ไม่มี unique constraint — ไม่มีอะไรกันการส่งซ้ำที่เหมือนกันเป๊ะ ๆ

**Indexes:** `@@index([scope, scope_id, created_at(sort: Desc)])` (แทนที่ index เดิมก่อนปรับใหญ่ `[category, scope_id, created_at]` — สร้างขึ้น *ก่อน* การ drop คอลัมน์ เพื่อไม่ให้มีช่วงที่ไม่มี index เลย) · `@@index([deleted_at])`

**Status ถูกคำนวณ ไม่เคยถูกเก็บ** `BroadcastAdminService.deriveStatus()` อ่าน `deleted_at`/`scheduled_at`/`end_at` เทียบกับเวลาอ้างอิงเดียวคือ `now`: มี `deleted_at` → `deleted` (ชนะทุกอย่าง); ไม่งั้นถ้า `scheduled_at` ยังเป็นอนาคต → `scheduled`; ไม่งั้นถ้า `end_at` ผ่านมาแล้ว → `expired`; ไม่งั้น → `active`

### 2.2 `tb_user_broadcast_action`

State รายผู้ใช้แบบ lazy สำหรับ broadcast แบบ `system_all`/`bu` หนึ่งตัว Schema บรรทัด 403 **ไม่เปลี่ยนแปลง** จากก่อนปรับใหญ่

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, ค่าเริ่มต้น `gen_random_uuid()` |
| `broadcast_id` | `String @db.Uuid` | No | FK → `tb_broadcast_notification.id`, `onDelete: Cascade` |
| `user_id` | `String @db.Uuid` | No | FK → `tb_user.id`, `onDelete: Cascade` |
| `is_read` | `Boolean? @default(false)` | Yes | Flag การอ่าน; query ของ unread ปฏิบัติต่อ row ที่ไม่มีกับ `is_read = false` เหมือนกัน |
| `read_at` | `DateTime?` | Yes | ประทับเวลาโดย upsert ของ mark-as-read |
| `dismissed_at` | `DateTime?` | Yes | **ประกาศไว้แต่ไม่มีใครใช้** — ไม่มี code เขียนมันเลย |
| `doc_version` | `Int @default(0) @db.Integer` | No | **มีเฉพาะใน schema เท่านั้น** เหมือนเดิม — upsert ของ mark-read (`markBroadcastAsRead`/`markAllBroadcastsAsRead`) ไม่เคยอ่านหรือเพิ่มค่านี้เลย |
| `created_at` / `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | ค่าเริ่มต้น `now()`; `updated_at` ถูกแตะโดย upsert ของ mark-read |

**Constraints:** `@@unique([broadcast_id, user_id])` (`user_broadcast_action_broadcast_user_u`) — path mark-read upsert เทียบกับ key นี้ **Indexes:** `@@index([user_id, is_read])`

Row ถูกเขียนโดยแค่สองเส้นทางใน micro-notification: mark-as-read แบบเดียว (`BroadcastService.markBroadcastAsRead`, Prisma upsert) และ mark-all-as-read (`markAllBroadcastsAsRead`, raw SQL `INSERT … ON CONFLICT … DO UPDATE` เดียวที่ครอบคลุม broadcast ที่ยังไม่อ่านทั้งหมดใน scope) — ทั้งสองไม่เปลี่ยนแปลงจากการปรับใหญ่ครั้งนี้

### 2.3 `tb_notification` (อ้างอิง — ทางแยกของการส่งแบบระบุผู้รับ)

ตารางการแจ้งเตือนส่วนบุคคล (schema บรรทัด 332) **ถูกปรับรูปโดยการปรับใหญ่ครั้งเดียวกัน**: `type` (varchar), `category` (varchar) และ `is_sent` (boolean) ถูก **drop ทั้งหมด**; `doc_type`/`event` (enum สองตัวเดียวกับที่ broadcast ใช้) และ timestamp ใหม่ `pushed_at` ถูกเพิ่มเข้ามา

| Field | Type | หมายเหตุ |
|---|---|---|
| `to_user_id` / `from_user_id` | `String? @db.Uuid` | FK ไปยัง `tb_user`; row ของ broadcast แบบระบุผู้รับพกผู้ส่งไว้ที่ `from_user_id` |
| `doc_type` | `enum_notification_doc_type` | forward มาจาก envelope — `system` สำหรับการส่งแบบระบุผู้รับ |
| `event` | `enum_notification_event` | forward มาจาก envelope — `info` สำหรับ broadcast แบบระบุผู้รับ |
| `pushed_at` | `DateTime? @db.Timestamptz(6)` | **ใหม่** ตั้งค่าเมื่อ row ถูก emit บน WebSocket bus แล้ว — แทนที่ boolean `is_sent` ที่ถูกลบไป ซึ่ง "ถูกตั้งเป็น true ตอน INSERT โดยไม่รอผลการส่งจริง" จึงไม่เคยมีค่าเชิงข้อมูลเลย |
| `scheduled_at` | `DateTime? @db.Timestamptz(6)` | ความหมายจุดตัดการมองเห็นเดียวกับตาราง broadcast |
| `is_read` | `Boolean? @default(false)` | ไม่เปลี่ยนแปลง |

`NotificationWriteService.notify()` เขียนหนึ่ง row ต่อหนึ่ง id ใน `userIds` ภายใน transaction เดียว (ได้ครบหรือไม่ได้เลย — โค้ดเดิมที่วน await ทีละคนเคยทำให้ผู้รับที่เหลือไม่ถูกเขียนเงียบ ๆ เมื่อกลางแบตช์ล้มเหลว) **`ScheduleWorker` cron ใหม่ทุก 30 วินาทีคอย claim row ของ `tb_notification` ที่ถึงเวลาแล้วแต่ยังไม่ push** (`scheduled_at <= NOW()`, `pushed_at IS NULL`, จำกัดหน้าต่างไว้ที่ 7 วัน, `FOR UPDATE SKIP LOCKED`) แล้ว push แต่ละแถวแบบ live ผ่าน helper `emitNotification()` ตัวเดียวกับที่ `emitCreated()` ใช้ จากนั้นประทับ `pushed_at` **worker ตัวนี้ query เฉพาะ `tb_notification` เท่านั้น** — broadcast แบบ `system_all`/`bu` ที่กำหนดเวลาไว้ไม่มีกลไกเทียบเท่าเลย ดู [Permissions](/th/platform/broadcasts/permissions) §3

## 3. ความสัมพันธ์

- `tb_broadcast_notification` 1:M `tb_user_broadcast_action` — `broadcast_id`, `onDelete: Cascade`
- `tb_user` 1:M `tb_user_broadcast_action` — `user_id`, `onDelete: Cascade`
- `tb_user` 1:M `tb_broadcast_notification` ผ่าน `created_by_id` / `updated_by_id` (`NoAction` — การอ้างอิงเพื่อ audit)
- **`scope_id` → `tb_business_unit.id` เป็นข้อตกลง ไม่ใช่ Prisma relation** ตรวจสอบเฉพาะตอนส่งเท่านั้น; BU ที่ถูกลบภายหลังจะทำให้ broadcast row ชี้ไปยัง scope ที่ตายแล้ว

## 4. Enum

**นี่คือ schema ที่ใช้ enum จริงแล้ว — ไม่ใช่ varchar ธรรมดา** คอลัมน์ varchar `category`/`type` ก่อนปรับใหญ่ถูกแทนที่ทั้งหมด:

| Enum | ค่า | ใช้โดย |
|---|---|---|
| `enum_broadcast_scope` | `system`, `business_unit` | `tb_broadcast_notification.scope` |
| `enum_notification_doc_type` | `system`, `business_unit`, `purchase_request`, `store_requisition`, `purchase_order`, `good_received_note`, `credit_note` | `tb_broadcast_notification.doc_type`, `tb_notification.doc_type` (broadcast ใช้แค่สองค่าแรกเท่านั้น) |
| `enum_notification_event` | `info`, `workflow`, `comment` | `tb_broadcast_notification.event` (hardcode เป็น `info`), `tb_notification.event` |

**ไม่มีคอลัมน์ `severity` เลยในตารางไหนทั้งนั้น** ตัวเลือก Info/Warning/Critical/Maintenance/Other… ของผู้ส่งเป็นความสะดวกฝั่ง client เท่านั้น เก็บเป็นสตริงล้วน ๆ ใน `metadata.severity` และถูกส่งกลับโดย `BroadcastAdminService.toRow()` เป็นฟิลด์ `severity` บน wire เพื่อให้ UI ของ list/edit ฝั่งแอดมิน render badge ของตัวเอง มันไม่มีผลใด ๆ ต่อสิ่งที่ผู้รับเห็น: `event` ของทุก broadcast คือ `info` และ preview panel ของฝั่ง client เองก็บอกตรง ๆ ว่า ("สีและป้ายเป็นการจัดหมวดหมู่ภายในเท่านั้น — ผู้รับเห็นแค่การแจ้งเตือนแบบมาตรฐาน") token ของ Other… ที่กำหนดเองถูกตรวจสอบแค่ฝั่ง client (`[A-Z0-9_]+`, ≤50 ตัวอักษร, อัพเปอร์เคสอัตโนมัติ); server รับสตริงอะไรก็ได้ใน `metadata`

## 5. ความแตกต่างจากรูปแบบ SPA ของ carmen-platform

| รูปแบบ SPA | แหล่งที่มาใน SPA | การเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `bu_code: string` | `BroadcastBuPayload` | `scope_id String? @db.Uuid` | API รับ **code** ของ BU ที่เปลี่ยนได้; resolve กับ `tb_business_unit` ที่ live แล้วเก็บเป็น UUID code ที่ไม่รู้จักหรือถูกลบไปแล้ว → การสร้างล้มเหลวด้วย **404** (`COMMON_BUSINESS_UNIT_NOT_FOUND`, `http_status: 404` ใน error catalog กลาง) — แก้ไขคำอธิบายเดิมของ wiki ก่อนปรับใหญ่ที่บอกว่า "500-enveloped" |
| `userIds?: string[]` | `BroadcastSystemPayload` | — (สลับไปที่ `tb_notification`) | มี → หนึ่ง row ต่อ id **ที่มีอยู่จริง** (id ที่ไม่รู้จักถูกทิ้ง); ไม่มี → หนึ่ง row ของ `tb_broadcast_notification` |
| `end_at: string` (**บังคับ**) | ทั้งสอง payload | `DateTime?` (คอลัมน์ nullable แต่ในทางปฏิบัติไม่เป็น null) | คอลัมน์ยัง nullable ใน Prisma แต่ทั้ง SPA และ Zod request schema (`SystemBroadcastCreateSchema`/`BuBroadcastCreateSchema`) บังคับเสมอไม่มีเงื่อนไข — แม้แต่กิ่ง fan-out ของ `userIds` ที่ `audience: { kind: 'users' }` ของ `NotifyInput` ไม่มีฟิลด์ `end_at` ของตัวเองให้พกไปด้วย |
| `metadata.severity?: string` | ทั้งสอง payload (ผ่าน `resolveSeverity()`) | `Json? @db.JsonB` | การจัดหมวดหมู่ฝั่ง client เท่านั้น — ดู §4 **ไม่มี** field `type` ฝั่ง server ให้ resolve อีกต่อไป — ระบบ prefix `SYS_*`/`BU_*` เดิมไม่มีอยู่แล้ว |
| `metadata.bu_code`, `metadata.id` | server merge ให้ | `Json? @db.JsonB` | `buildMetadata()` ของ `NotificationWriteService` จะพับ `bu_code`/`doc_id` เข้าไปใน `metadata` ที่เก็บไว้เสมอ merge (ไม่ใช่แทนที่) ตอน update — client PATCH ไม่สามารถเขียนทับสอง key นี้ได้แม้จะส่งมาตรง ๆ (`BroadcastAdminService.update()` ตัด `bu_code`/`id` ออกจาก `metadata` ของผู้เรียกก่อน merge) |
| `scheduled_at?: string` (ISO) | ทั้งสอง payload | `DateTime?` | ไม่เปลี่ยนแปลง: SPA แปลง input `datetime-local` ผ่าน `new Date(v).toISOString()` |
| — | — | `severity` (field บน wire ไม่มีคอลัมน์ DB) | `BroadcastAdminRow.severity` ถูกสังเคราะห์ต่อแถวจาก `metadata.severity` ไม่ได้อ่านจากฟิลด์ schema — เพราะไม่มีฟิลด์นั้นอยู่ |
| — | — | `updated_at`, `updated_by_id` | **เขียนทุกครั้งที่ `PATCH`/`DELETE` แต่ไม่เคยถูกส่งกลับ** จาก `GET`/`GET :id`/`PATCH`/`DELETE` (`BroadcastAdminRow`/`BroadcastListItem` ไม่มีฟิลด์ `updated_at`/`updated_by` เลย) — CSV export ของหน้า List ยังขอสองคอลัมน์นี้อยู่และมันจะว่างเปล่าตลอด (ดู [UI Screens](/th/platform/broadcasts/ui-screens) §2.1) บรรทัด audit ของ `PageHeader` บนหน้า Edit จึงแสดงแค่ "Created" เสมอ ไม่เคยแสดง "Updated" แม้ broadcast นั้นจะถูกแก้ไขจริงก็ตาม |
| — | — | `end_at`, `dismissed_at` (บน `tb_user_broadcast_action`) | `dismissed_at` ยังคงมีเฉพาะใน schema (§2.2); ส่วน `end_at` ของตาราง broadcast กลับเป็นตรงข้าม — ไม่ตายอีกต่อไป ดูด้านบน |
| `created_by_id` (**ความแตกต่างที่ถูกแก้แล้ว**) | — | `created_by_id` | wiki ก่อนปรับใหญ่เคย document ความไม่สอดคล้องที่มีอยู่จริง: Swagger doc ของ gateway อ้างว่า "ผู้ใช้จาก token จะกลายเป็น `from_user_id`" แต่ code path ของการส่งแบบ system ทิ้งมันไปเงียบ ๆ ทำให้ `created_by_id = null` บนทุก row ของ `system_all` (มีแค่ row ของ BU ที่บันทึกผู้ส่ง) ตอนนี้ `BroadcastService.create()` ตั้ง `created_by_id: input.from_user_id ?? null` สำหรับ audience ที่ไม่ใช่ `users` **ทุกตัว** — ทั้งการส่งแบบ `system_all` และ `bu` บันทึกผู้ส่งสอดคล้องกันแล้ว ความแตกต่างนี้ถูกแก้ไขแล้ว ไม่ใช่แค่ document ซ้ำ |

## 6. แหล่งอ้างอิง

REST surface (backend-gateway) ทั้งหมดอยู่ใต้ `/api/notifications/...` — **ไม่ใช่** `/api-system/...` **ยังไม่มี `AppIdGuard` บนทั้งหกเส้นทางของ broadcast** (ต่างจาก CRUD ที่ยืนยันตัวตนของ News) — ตรวจสอบใหม่กับ controller ปัจจุบันแล้ว: class มี `@ApiHeaderRequiredXAppId()` ซึ่งใช้ document header ให้ Swagger เท่านั้น และไม่มี route decorator ตัวไหนในทั้งหกเส้นทางเพิ่ม `AppIdGuard` ลงใน `@UseGuards(...)` เลย

| Method + Path | Auth | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|---|
| `POST /api/notifications/broadcasts/system` | Bearer + `broadcast.send` (หยาบ: ระดับแพลตฟอร์มหรือ cluster ใดก็ได้) | ส่งแบบ system-wide หรือระบุผู้รับ | Body `{ title, message, end_at, metadata?, scheduled_at?, userIds? }` ไม่มี `userIds`: หนึ่ง broadcast row (`scope: system`) มี `userIds`: fan out เป็น `tb_notification` รายผู้ใช้ 201 |
| `POST /api/notifications/broadcasts/bu` | Bearer + `broadcast.send` (check หยาบเดียวกัน) | ส่งระดับ BU | Body `{ bu_code, title, message, end_at, metadata?, scheduled_at? }` หนึ่ง broadcast row (`scope: business_unit`, `scope_id` = BU id ที่ resolve แล้ว) 201 |
| `GET /api/notifications/broadcasts` | Bearer + `broadcast.read` | List ฝั่งแอดมินผู้ส่ง | ทุก row ไม่ว่าจะกำหนดเวลา/หมดอายุหรือไม่ (ต่างจาก endpoint ฝั่งผู้รับด้านล่าง); `page`/`perpage`/`search`/`sort`/`status`/`scope`/`include_deleted`; คืน `{ data, paginate, summary }` โดย `summary` ตั้งใจไม่สนใจ filter `status` |
| `GET /api/notifications/broadcasts/:id` | Bearer + `broadcast.read` | ดึงรายการเดียวฝั่งผู้ส่ง | คืน row ที่ถูกลบแบบ soft ด้วย (`status: "deleted"`) เพื่อให้รายการที่ถูกลบยังเปิดดูได้ |
| `PATCH /api/notifications/broadcasts/:id` | Bearer + `broadcast.update` | แก้ schedule/วันหมดอายุ/เนื้อหา | ต้องส่ง `doc_version` (409 ถ้าไม่ตรง); `title`/`message`/`metadata` แก้ได้เฉพาะตอน `status === 'scheduled'` (ไม่งั้น 400 `content_locked`); `end_at` ที่เป็นอดีตคือกลไกของ "Expire Now" |
| `DELETE /api/notifications/broadcasts/:id` | Bearer + `broadcast.delete` | ลบแบบ soft | ต้องส่ง `doc_version` เป็น query param (409 ถ้าไม่ตรง) |
| `GET /api/notifications` / `/recent` / `/unread` | Bearer | List ฝั่งผู้รับ | รวม row ส่วนตัว + broadcast ที่อยู่ใน scope; broadcast ถูกกรองด้วย `deleted_at IS NULL` และ `scheduled_at IS NULL OR <= NOW()` |
| `GET /api/notifications/:notification_id` | Bearer | ดึงรายการเดียวฝั่งผู้รับ | คืน row ของ `tb_notification` ถ้าผู้เรียกเป็นผู้รับ หรือ row ของ `tb_broadcast_notification` ถ้าผู้เรียกอยู่ใน scope; ไม่งั้น 404 — ใช้ filter scope/`scheduled_at` ชุดเดียวกับ endpoint list ด้านบน |
| `PUT /api/notifications/:id/read` | Bearer | Mark ว่าอ่านแล้ว | Client ส่ง `source` ของ row นั้น (`'broadcast'` หรือ `'personal'` **ไม่ใช่** `category` ที่เลิกใช้แล้ว) เพื่อ route ไปตารางที่ถูกต้อง |
| `PUT /api/notifications/mark-all-read` | Bearer | Mark ทุกการแจ้งเตือนที่ยังไม่อ่านว่าอ่านแล้ว ทั้งส่วนตัว**และ** broadcast | Mark ทั้งสองอย่างในครั้งเดียว: `tb_notification.updateMany({ to_user_id, is_read: false })` **และ** `BroadcastService.markAllBroadcastsAsRead()` (upsert แบบ raw-SQL ของ §2.2) รันพร้อมกันผ่าน `Promise.all` **คำอธิบาย Swagger ของ gateway เองอธิบายน้อยกว่าที่มันทำจริง** — บอกแค่ "ทุก row ของ `tb_notification` ที่ยังไม่อ่าน" — แต่ comment ของ RPC handler เองและ implementation จริง (`markAllNotificationsAsRead()` ใน `notification.service.ts`) ครอบคลุมทั้งสองตาราง และคืน `{ count, personal_count, broadcast_count }` |

ไม่มี Bruno collection สำหรับ broadcast endpoint เลย (ตรวจสอบแล้วว่ายังไม่มี) — annotation ของ Swagger บน gateway controller คือเอกสาร contract ที่ใกล้เคียงที่สุด

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (บรรทัด 332), `tb_broadcast_notification` (บรรทัด 369), `tb_user_broadcast_action` (บรรทัด 403), enum (บรรทัด 112–131)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260810000000_notification_redesign_additive/`, `20260811000000_notification_redesign_drop_legacy/migration.sql` — การเพิ่ม enum, backfill และการ drop คอลัมน์
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/broadcast.service.ts` (สร้าง, resolve ผู้รับ), `broadcast-admin.service.ts` (list/get/update/delete, `deriveStatus`), `notification-write.service.ts` (จุดเขียนเดียว), `schedule.worker.ts` (push ของ due-notification, เฉพาะ `tb_notification`)

**รอง (รูปร่างฝั่ง gateway + consumer):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — ทั้งหกเส้นทางของ broadcast, payload builder, TCP forwarding
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/notification/notification.dto.ts` — `SystemBroadcastCreateSchema`/`BuBroadcastCreateSchema` (`end_at` บังคับ), `BroadcastListQuerySchema`
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` — `COMMON_BUSINESS_UNIT_NOT_FOUND` (`http_status: 404`)
- `../carmen-platform/src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, `BroadcastListItem`, `BroadcastStatus`, `BroadcastUpdatePayload`, `BroadcastSummary`; `src/services/broadcastService.ts` — ทั้งหกเรียก

**Cross-links:** [หน้าแรก Broadcasts](/th/platform/broadcasts) &nbsp;·&nbsp; [UI Screens](/th/platform/broadcasts/ui-screens) &nbsp;·&nbsp; [Permissions](/th/platform/broadcasts/permissions) &nbsp;·&nbsp; [Business Units — Data Model](/th/platform/business-units/data-model) (เป้าหมายของ `scope_id`) &nbsp;·&nbsp; [Users — Data Model](/th/platform/users/data-model) (ผู้รับและ read-state row)
