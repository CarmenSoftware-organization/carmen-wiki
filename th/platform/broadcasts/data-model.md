---
title: Broadcasts — แบบจำลองข้อมูล (Data Model)
description: ตาราง field ของ tb_broadcast_notification และ tb_user_broadcast_action, ทางแยกของการส่งแบบกำหนดเป้าหมายลง tb_notification, การ resolve scope_id จาก bu_code และความแตกต่างจาก payload type แบบ write-only ของ SPA
published: true
date: 2026-06-10T16:00:00.000Z
tags: book/platform, broadcasts, data-model
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# Broadcasts — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_broadcast_notification` (หนึ่ง row ต่อหนึ่ง broadcast) + `tb_user_broadcast_action` (read state รายผู้ใช้แบบ lazy, unique ต่อ broadcast×user) &nbsp;·&nbsp; **ทางแยกของการกำหนดเป้าหมาย:** การส่งแบบ `userIds` ข้ามทั้งสองตารางและ fan out ลง `tb_notification` (row ส่วนบุคคลหนึ่งตัวต่อผู้รับ) &nbsp;·&nbsp; **Scope:** `scope_id` = UUID ของ `tb_business_unit.id` สำหรับ `bu-to-user`, null สำหรับ `system-to-user` — API รับ **code** ของ BU แล้ว resolve มัน &nbsp;·&nbsp; **ไม่มี enum:** `category` และ `type` เป็น varchar ธรรมดา &nbsp;·&nbsp; **Endpoint:** `POST /api/notifications/broadcasts/system` / `/bu` — `/api` **ไม่ใช่** `/api-system`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูลนี้เป็นเจ้าของสองตาราง `tb_broadcast_notification` คือ "single source of truth for a broadcast" ตาม comment ของ schema: หนึ่ง row ต่อหนึ่งข้อความไม่ว่ากลุ่มผู้ชมจะใหญ่แค่ไหน โดยกลุ่มผู้ชมถูก encode เป็น `category` (`'system-to-user'` หรือ `'bu-to-user'`) บวก `scope_id` ส่วน `tb_user_broadcast_action` ถือ state รายผู้ใช้ — ถูกสร้างแบบ **lazy** เฉพาะเมื่อผู้ใช้กระทำ action (mark ว่าอ่านแล้ว) เท่านั้น; การไม่มี row หมายถึง "ยังไม่ได้กระทำ" และ query ของ unread ใช้ LEFT JOIN เพื่อดึง broadcast ที่ไม่มี row ขึ้นมา comment ของ schema บันทึกไว้ว่าคู่ตารางนี้แทนที่รูปแบบ fan-out-on-write รุ่นก่อนที่ insert row ของ `tb_notification` หนึ่งตัวต่อผู้รับ

รูปแบบ legacy นั้นยัง live อยู่บนเส้นทางเดียว: การส่งแบบ system ที่มีรายการ `userIds` แบบระบุชัดจะข้ามตาราง broadcast ทั้งสองและ fan out ลง `tb_notification` (§2.3) — code ของ micro-notification เรียกสิ่งนี้ว่า "legacy behavior — small N, fanout is fine"

เส้นทาง persistence คือ backend-gateway (`api/notifications/broadcasts/*`, KeycloakGuard) → TCP `notifications.create` → micro-notification ซึ่งเป็นเจ้าของการเขียนทั้งหมด, การ resolve `bu_code → scope_id`, การ emit แบบ live ผ่าน Socket.io สำหรับการส่งที่ไม่กำหนดเวลา และ side-effect ของการ fan-out อีเมลเมื่อ SMTP ถูก config ไว้ ไม่มี endpoint แบบ read/update/delete ฝั่ง admin — ผู้อ่านมีเพียง endpoint ฝั่งผู้รับ เช่น ชุด list/unread/mark-read ที่ document ไว้ใน §6 (บวก `GET /api/notifications/:notification_id` และ `PUT /api/notifications/mark-all-read` ซึ่ง apply filter ของ scope และ `scheduled_at` ชุดเดียวกัน)

## 2. เอนทิตี

### 2.1 `tb_broadcast_notification`

หนึ่งข้อความ broadcast Schema บรรทัด 357

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `category` | `String @db.VarChar(50)` | No | `'system-to-user'` (ทั้งแพลตฟอร์ม) หรือ `'bu-to-user'` (BU หนึ่งแห่ง) — varchar ธรรมดา ไม่มี enum |
| `scope_id` | `String? @db.Uuid` | Yes | `tb_business_unit.id` เมื่อ `category = 'bu-to-user'`; `null` สำหรับ `'system-to-user'` ถูก resolve ฝั่ง server จาก `bu_code` ของ payload (เฉพาะ BU ที่ live) — row จัดเก็บ UUID ที่เสถียร ไม่ใช่ code ที่เปลี่ยนชื่อได้ |
| `type` | `String @default("SYS_INFO") @db.VarChar(255)` | No | label ของ type — preset แบบ `SYS_*`/`BU_*` หรือ custom token แบบอัพเปอร์เคส (§4) |
| `title` | `String?` | Yes | หัวข้อ notification (SPA บังคับ; ตัวคอลัมน์ไม่บังคับ) |
| `message` | `String?` | Yes | เนื้อหา notification (เช่นเดียวกัน — บังคับโดย SPA เท่านั้น) |
| `metadata` | `Json? @db.JsonB` | Yes | รูปแบบอิสระ SPA ไม่เคยส่งมัน; การส่งแบบ BU ได้ `bu_code` ถูก merge เข้ามาฝั่ง server |
| `scheduled_at` | `DateTime?` | Yes | cutoff การมองเห็น: list query ซ่อน row จนกว่า `scheduled_at <= NOW()` ไม่มี annotation ของ timezone (ต่างจากคอลัมน์ audit) |
| `end_at` | `DateTime?` | Yes | **ประกาศไว้แต่ตาย** — ไม่เคยถูกเขียนหรืออ่านโดย code path ใด ณ 2026-06-10 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: การสร้าง row, default `now()`; เป็น sort key ของ list ด้วย |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit/ผู้ส่ง: FK → `tb_user` ถูกตั้งเป็น user ของ token สำหรับการส่งแบบ **BU**; **ถูกปล่อยเป็น `null` สำหรับการส่งแบบ system** (§5) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: default `now()`; ไม่เคยถูก update (ไม่มี update path อยู่เลย) |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: FK → `tb_user`; ไม่เคยถูกเขียน |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft delete — **ถูกเคารพโดยทุก read query แต่ไม่มี code path ใดเขียนมัน**; การถอน broadcast เป็นการดำเนินการบน DB ด้วยมือ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: UUID เปล่า; ไม่เคยถูกเขียน |

**Constraint:**
- `@id` บน `id` FK relation: `created_by_id` และ `updated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`) ไม่มี unique constraint — ไม่มีอะไรหยุดการส่งซ้ำที่เหมือนกันทุกประการ

**Index:**
- `@@index([category, scope_id, created_at(sort: Desc)])` — ขับเคลื่อน list query แบบ scope (row แบบ system สำหรับทุกคน, row แบบ BU ถูก match กับการเป็นสมาชิก BU ของผู้ใช้, ใหม่สุดก่อน)
- `@@index([deleted_at])`

### 2.2 `tb_user_broadcast_action`

state รายผู้ใช้แบบ lazy สำหรับ broadcast หนึ่งตัว Schema บรรทัด 388

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `broadcast_id` | `String @db.Uuid` | No | FK → `tb_broadcast_notification.id`, **`onDelete: Cascade`** |
| `user_id` | `String @db.Uuid` | No | FK → `tb_user.id`, **`onDelete: Cascade`** |
| `is_read` | `Boolean? @default(false)` | Yes | flag การอ่าน; query ของ unread ปฏิบัติกับ row ที่ไม่มีและ `is_read = false` เหมือนกันทุกประการ (`COALESCE(a.is_read, false)`) |
| `read_at` | `DateTime?` | Yes | ถูกประทับโดย upsert ของ mark-as-read |
| `dismissed_at` | `DateTime?` | Yes | **ประกาศไว้แต่ตาย** — comment ของ schema คาดการณ์ action แบบ dismiss ไว้ แต่ไม่มี code ใดเขียนมัน ณ 2026-06-10 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Default `now()` |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Default `now()`; ถูกแตะโดย upsert ของ mark-read |

**Constraint:**
- `@id` บน `id`; `@@unique([broadcast_id, user_id])` (map `user_broadcast_action_broadcast_user_u`) — state หนึ่ง row ต่อผู้ใช้ต่อ broadcast; เส้นทาง mark-read ทำ upsert กับ key นี้ ไม่มีคอลัมน์ audit actor หรือ soft-delete

**Index:**
- `@@index([user_id, is_read])` — การ lookup ของ unread

row ถูกเขียนโดยเส้นทางใน micro-notification เพียงสองทางเป๊ะ ๆ: mark-as-read แบบรายตัว (Prisma upsert) และ mark-all-as-read (raw SQL `INSERT … ON CONFLICT … DO UPDATE` ครั้งเดียวครอบคลุมทุก broadcast ที่ unread และ in-scope)

### 2.3 `tb_notification` (ถูกอ้างอิง)

ตาราง notification ส่วนบุคคล (schema บรรทัด 316; FK ของ `to_user_id`/`from_user_id`, `type` default `SYS_INFO`, `category` default `'system'`, flag `is_read`/`is_sent`, `scheduled_at` ของตัวเอง, คอลัมน์ audit ครบชุด) Broadcasts แตะมันบนเส้นทางเดียวเท่านั้น: การส่งแบบ system ที่ถือ `userIds` สร้างหนึ่ง row **ต่อ id ผู้รับที่มีอยู่จริง** (`category = 'system'`, `from_user_id = null`) จากนั้น emit แบบ live แล้วประทับ `is_sent = true` เมื่อไม่กำหนดเวลา id ที่ไม่ match กับ row ของ `tb_user` ใดถูกทิ้งอย่างเงียบ ๆ — ไม่มี error, ไม่มีรายงาน partial-failure lifecycle ที่กว้างกว่าของตารางนี้ (ข้อความ user-to-user, workflow notification) เป็นของ feature ด้าน notification โดยรวม ไม่ใช่ของโมดูลนี้

## 3. ความสัมพันธ์

- `tb_broadcast_notification` 1:M `tb_user_broadcast_action` — `broadcast_id`, `onDelete: Cascade` (การลบ broadcast จะ hard-delete row ของ read state ของมัน)
- `tb_user` 1:M `tb_user_broadcast_action` — `user_id`, `onDelete: Cascade` (การลบผู้ใช้จะลบ read state ของพวกเขา)
- `tb_user` 1:M `tb_broadcast_notification` ผ่าน `created_by_id` / `updated_by_id` (`NoAction` — การอ้างอิงแบบ audit)
- **`scope_id` → `tb_business_unit.id` เป็น convention ไม่ใช่ Prisma relation** ถูกตรวจสอบเฉพาะตอนส่งเท่านั้น (`bu_code` ต้อง match กับ BU ที่ live ไม่เช่นนั้นการส่งล้มเหลว); BU ที่ถูกลบภายหลังจะทิ้ง row ของ broadcast ที่ชี้ไปยัง scope ที่ตายแล้ว — สมาชิกของมันก็เพียงหยุด match กับ scope query

## 4. Enum

ไม่มี — `category` และ `type` เป็น varchar ธรรมดา คลังศัพท์ของ `type` ตาม convention ซึ่งถูกประกอบฝั่ง client โดย SPA (ดู [UI Screens](./ui-screens.md) §2.5):

| Preset | โหมด system ส่ง | โหมด BU ส่ง |
|---|---|---|
| Info | `SYS_INFO` | `BU_INFO` |
| Warning | `SYS_WARNING` | `BU_WARNING` |
| Critical | `SYS_CRITICAL` | `BU_CRITICAL` |
| Maintenance | `SYS_MAINTENANCE` | `BU_MAINTENANCE` |
| Other… | custom token แบบ verbatim — **ไม่มี prefix** | custom token แบบ verbatim — **ไม่มี prefix** |

custom token คือ `[A-Z0-9_]+`, ≤50 ตัวอักษร (เป็นการ validate ของ SPA; ตัวคอลัมน์รับ varchar(255) ใดก็ได้) caller ของ API ที่ละ `type` ได้ค่า default ของ gateway คือ `SYS_INFO` / `BU_INFO` doc comment ของ `tb_notification` แสดงคลังศัพท์ที่กว้างกว่าซึ่งใช้ที่อื่น (`PR`, `PR_COMMENT`, `SR`, `SR_COMMENT`)

## 5. ความแตกต่างจาก shape ของ carmen-platform SPA

type ของ SPA (`src/types/index.ts`) เป็น **DTO แบบ write-only** — `BroadcastSystemPayload` และ `BroadcastBuPayload` อธิบาย request; ไม่มี read type ฝั่ง SPA เพราะ SPA ไม่เคยอ่าน broadcast กลับมา

| Shape ของ SPA | แหล่งที่มาใน SPA | การจัดเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `bu_code: string` | `BroadcastBuPayload` | `scope_id String? @db.Uuid` | API รับ **code** ของ BU ซึ่งเปลี่ยนได้; micro-notification resolve มันกับ row ของ `tb_business_unit` ที่ live แล้วจัดเก็บ UUID code ที่ไม่รู้จัก/ถูกลบ → การ create ล้มเหลว (envelope แบบ 500, `Business unit not found: <code>`) code ดั้งเดิมถูกเก็บรักษาไว้ใน `metadata.bu_code` |
| `userIds?: string[]` | `BroadcastSystemPayload` | — (สลับตาราง) | มี → row ของ `tb_notification` หนึ่งตัวต่อ id **ที่มีอยู่จริง** (id ที่ไม่รู้จักถูกทิ้งอย่างเงียบ ๆ); ไม่มี → row ของ `tb_broadcast_notification` หนึ่งตัว endpoint เดียวกันเขียนลงสองตารางต่างกันขึ้นกับ field นี้ |
| `type?: string` (optional) | payload ทั้งสอง | `@default("SYS_INFO")` | การ resolve type (การเติม prefix `SYS_`/`BU_`) เกิด**ฝั่ง client** ใน `BroadcastCompose.resolveType`; SPA ส่งค่าที่ resolve แล้วเสมอ ค่า default ของ server ปกป้องเฉพาะ caller ที่ไม่ใช่ SPA |
| `metadata?: Record<string, unknown>` | payload ทั้งสอง | `Json? @db.JsonB` | SPA ไม่เคยตั้งมัน การส่งแบบ BU มาถึงพร้อม `bu_code` ที่ถูก merge เข้ามาฝั่ง server ดังนั้น metadata ของ row แบบ BU ที่จัดเก็บไว้จึงไม่มีวันเป็น null เทียบเท่ากับสิ่งที่ caller ส่งมา |
| `scheduled_at?: string` (ISO) | payload ทั้งสอง | `DateTime?` | SPA แปลง input แบบ `datetime-local` ของมันผ่าน `new Date(v).toISOString()` — เวลาท้องถิ่นของเบราว์เซอร์ ถูกส่งเป็น UTC |
| — | — | `created_by_id` | gateway forward ตัว user ของ token เป็น `from_user_id` และ Swagger doc ของมันอ้างว่า "the token user becomes `from_user_id`" — แต่เส้นทาง **system** ของ micro-notification ทิ้งมัน (`CreateSystemNotificationData` ไม่มี field แบบนั้น): row ของ broadcast แบบ system จัดเก็บ `created_by_id = null` เฉพาะ row แบบ **BU** เท่านั้นที่บันทึกผู้ส่ง row ของ fan-out แบบกำหนดเป้าหมายก็จัดเก็บ `from_user_id = null` เช่นกัน |
| — | — | `end_at`, `dismissed_at` | field ที่มีเฉพาะใน schema โดยไม่มี reader หรือ writer ที่ไหนเลย (§2.1, §2.2) |

## 6. แหล่งข้อมูลอ้างอิง

REST surface (backend-gateway) **สังเกต prefix: `/api/notifications/...` ไม่ใช่ `/api-system/...`** — เดิม SPA เรียก `/api-system` และถูกแก้ใน commit `579b3f7` ของ carmen-platform ทั้งสอง route ถือ `KeycloakGuard` (bearer auth) เท่านั้น; ไม่มี guard ของ RBAC หรือ app-id — ดู [Permissions](./permissions.md) §2

| Method + Path | Auth | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|---|
| `POST /api/notifications/broadcasts/system` | Bearer | ส่งแบบ system-wide หรือแบบกำหนดเป้าหมาย | Body `{ title, message, type?, metadata?, scheduled_at?, userIds? }` ไม่มี `userIds`: row ของ broadcast หนึ่งตัว (`system-to-user`), live emit ไปยังผู้ใช้ active ทุกคนเมื่อไม่กำหนดเวลา มี `userIds`: fan-out ลง `tb_notification` รายผู้ใช้ 201 `{ notifications, count }` |
| `POST /api/notifications/broadcasts/bu` | Bearer | ส่งแบบ scope ราย BU | Body `{ bu_code, title, message, type?, metadata?, scheduled_at? }` row ของ broadcast หนึ่งตัว (`bu-to-user`, `scope_id` = id ของ BU ที่ resolve แล้ว), live emit ไปยังสมาชิก BU เมื่อไม่กำหนดเวลา 201 เพิ่ม `bu_code` เข้าไปใน response |
| `GET /api/notifications` / `/recent` / `/unread` | Bearer | list ฝั่งผู้รับ | merge row ส่วนบุคคล + row ของ broadcast ที่ in-scope; broadcast ถูก filter ด้วย `deleted_at IS NULL` และ `scheduled_at IS NULL OR <= NOW()` |
| `PUT /api/notifications/:id/read` | Bearer | mark ว่าอ่านแล้ว | FE ส่ง `category` ของ row มาด้วย; `system-to-user`/`bu-to-user` route ไปยัง upsert ของ `tb_user_broadcast_action` ค่าอื่นใดไปยัง `tb_notification` |

ไม่มี Bruno collection สำหรับ endpoint ของ broadcast ณ 2026-06-10; annotation แบบ Swagger บน controller ของ gateway เป็นเอกสารสัญญาที่ใกล้เคียงที่สุด

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_broadcast_notification` (บรรทัด 357), `tb_user_broadcast_action` (บรรทัด 388), `tb_notification` (บรรทัด 316)
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.service.ts` — `createSystemNotification` (ทางแยก fan-out), `createBusinessUnitNotification` (การ resolve `bu_code`), `createBroadcastNotification`, `markBroadcastAsRead`/`markAllBroadcastsAsRead`, list query แบบ scope

**รอง (gateway + shape ฝั่ง consumer):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — route POST สองตัว, interface ของ payload, การ forward ผ่าน TCP, ค่า default ของ type
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.controller.ts` — dispatch ของ create, ตัวจำแนก broadcast-vs-fanout, live emit + การประทับ `is_sent`
- `../carmen-platform/src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, `BroadcastSystemPayload`, `BroadcastBuPayload`; `src/services/broadcastService.ts` — การเรียกสองตัว

**Cross-link:** [หน้า landing ของ Broadcasts](/th/platform/broadcasts) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Business Units data-model](../business-units/data-model.md) (เป้าหมายของ `scope_id`) &nbsp;·&nbsp; [Users data-model](../users/data-model.md) (ผู้รับและ row ของ read state)
