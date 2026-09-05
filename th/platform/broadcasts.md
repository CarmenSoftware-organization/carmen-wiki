---
title: บรอดแคสต์ (Broadcasts)
description: ภาพรวมโมดูล Broadcasts — สามหน้าจอ (List, Compose, Edit) ครอบคลุม push notification พร้อมวันหมดอายุที่บังคับ และวงจรชีวิตฝั่งผู้ส่งแบบเต็ม (กำหนดเวลา แก้ไขระหว่างที่ยังไม่ส่ง ต่ออายุให้หมดทันที ลบแบบ soft) — ยกเว้นการส่งแบบระบุผู้รับที่ยังคง fire-and-forget
published: true
date: 2026-09-05T00:00:00.000Z
tags: platform/broadcasts, carmen-software
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# บรอดแคสต์ (Broadcasts)

โมดูล **Broadcasts** push การแจ้งเตือนไปยังผู้ใช้แพลตฟอร์ม: ผู้ใช้ทั้งหมด, รายการที่ระบุชัด หรือสมาชิกทุกคนของ business unit หนึ่งแห่ง — ส่งทันทีหรือกำหนดเวลาไว้ในอนาคต พร้อม**วันหมดอายุที่บังคับ** มันคือคู่เทียบแบบ **push** ของ [News](/th/platform/news) ซึ่งเป็นแบบ **pull**: broadcast ตกถึง notification list ของผู้รับแต่ละคน (และแบบ live ผ่าน WebSocket เมื่อพวกเขาออนไลน์อยู่และการส่งนั้นไม่ได้กำหนดเวลาไว้) ขณะที่บทความข่าวนั่งรออยู่ใน `tb_news` ให้ถูก fetch

**รูปร่างของโมดูลนี้เปลี่ยนไปมากตั้งแต่ถูก document ครั้งล่าสุด** จากเดิมที่เป็นหน้าจอเขียน (compose) หน้าเดียวไม่มี list, edit หรือวงจรชีวิตใด ๆ ตอนนี้มีสามหน้าจอที่แยกกันชัดเจน: **List** (`/broadcasts` → `BroadcastManagement`) แสดง broadcast ทั้งหมดที่เป็น system-wide และ business-unit พร้อมค้นหา, filter ตามสถานะ/scope, สรุปยอด CSV export, ปุ่มลัด "Expire Now" และการลบแบบ soft; **Compose** (`/broadcasts/new` → `BroadcastCompose`) ที่ใช้ส่งอันใหม่; และ **Edit** (`/broadcasts/:id/edit` → `BroadcastEdit`) ที่ดูได้เสมอ และแก้ schedule/วันหมดอายุ/เนื้อหาได้ตราบใดที่ยังอยู่สถานะ `scheduled` **Compose กับ Edit เป็นคอมโพเนนต์คนละตัว ไม่ใช่หน้าจอเดียวที่มีสองโหมด** — มีไฟล์คนละไฟล์ route คนละ route และ permission gate คนละชุด target mode หนึ่งเป็นข้อยกเว้นของทั้งหมดนี้: การส่งแบบระบุ **ผู้ใช้เจาะจง** ยังคง fan out เป็น row ของ `tb_notification` ส่วนตัวและมองไม่เห็นทั้งจาก List และ Edit เลย — โหมดนั้นยังคง fire-and-forget เหมือนที่ทั้งโมดูลเคยเป็นมาก่อน

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แสดงรายการ, เขียน, กำหนดเวลา, แก้ไข (ระหว่างที่ยังกำหนดเวลาไว้), ต่ออายุให้หมด และลบแบบ soft สำหรับ push notification — target mode สามแบบ (`system_all` / `system_users` / `bu`), ป้าย severity ที่เป็นแค่ข้อมูลฝั่งผู้ส่ง และวันหมดอายุที่บังคับ (`end_at`) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA, โมดูล notification ของ backend-gateway และ micro-notification &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_broadcast_notification` (enum scope/doc_type/event, `doc_version` เป็น optimistic lock จริงแล้ว) + `tb_user_broadcast_action` (read state แบบ lazy); **การส่งแบบระบุผู้รับ (`system_users`) fork ไปที่ `tb_notification` แทน และไม่ปรากฏบน List หรือ Edit เลย** &nbsp;·&nbsp; **Endpoint:** `POST /api/notifications/broadcasts/system` และ `/bu` (ส่ง), `GET .../broadcasts` (list ฝั่งแอดมิน), `GET/PATCH/DELETE .../broadcasts/:id` — ทั้งหมดอยู่ใต้ `/api` **ไม่ใช่** `/api-system` &nbsp;·&nbsp; **Permission key:** `broadcast.read` (nav, list, ดูหน้า Edit) · `broadcast.send` (route Compose + ปุ่ม Send) · `broadcast.update` (action Edit + PATCH) · `broadcast.delete` (action Delete + DELETE) — nav `feature: 'broadcasts'`, ไม่มี `superAdminOnly` &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

รายการใน sidebar ("Broadcasts", ไอคอน Megaphone, กลุ่ม Content) ถูกกำหนดไว้ใน `platformNav.ts` ด้วย `permission: 'broadcast.read'` และ `feature: 'broadcasts'` — ไม่มี `superAdminOnly` มันเปิดหน้า **List** ซึ่งคือ `BroadcastManagement`: `PageHeader` (พร้อม subtitle และข้อความบอกชัดเจนว่าการส่งแบบระบุผู้รับไม่แสดงที่นี่), แถบสรุปสถานะที่คลิกได้ (จำนวน All / Active / Scheduled / Expired / Deleted แต่ละอันสลับ filter ที่ตรงกัน), ช่องค้นหา, sheet ของ Filters (สถานะ, scope, "show deleted"), `DataTable` แบบ server-side (Title+message, Scope, Severity, Status, Scheduled Date, Expires, Created), ปุ่ม CSV Export และปุ่ม "New Broadcast" ที่ gate ด้วย `broadcast.send` action menu ของแต่ละแถวมี Edit (`broadcast.update`, ซ่อนเมื่อถูกลบไปแล้ว), Expire Now (`broadcast.update`, เฉพาะแถวที่ active) และ Delete (`broadcast.delete`, ซ่อนเมื่อถูกลบไปแล้ว)

**Compose** (`/broadcasts/new` → `BroadcastCompose`) คือหน้าจอส่ง: แถบแท็บ Target (All users / Specific users / Business Unit), ตัวเลือกผู้รับแบบมีเงื่อนไข (`UserMultiSelect`) หรือ select ของ BU, ป้าย metadata "Related Business Unit" ที่เป็นตัวเลือก (ไม่เกี่ยวกับกลุ่มผู้รับจริง), Title/Message พร้อมตัวนับแบบ live, preset ของ Type (Info / Warning / Critical / Maintenance / Other…) ที่**เป็นป้ายฝั่งผู้ส่งล้วน ๆ** — ผู้รับไม่มีวันเห็นมันเลย — แถบแท็บ Send-time (ทันทีหรือกำหนดเวลา) และวันหมดอายุที่บังคับ (7/30/90 วัน หรือกำหนดเอง) การ์ด `BroadcastPreview` ที่ใช้ร่วมกันจะ render การแจ้งเตือน, การเข้าถึง และเวลาส่ง/หมดอายุแบบ live จาก state ของฟอร์ม การส่งต้องยืนยันเสมอ โดยสไตล์สีแดงสงวนไว้สำหรับการยิงแบบ system-wide เท่านั้น

**Edit** (`/broadcasts/:id/edit` → `BroadcastEdit`) เป็นคอมโพเนนต์แยกที่เข้าถึงได้จากลิงก์หัวข้อของ List หรือเมนูแถว route เองต้องการแค่ `broadcast.read` — ผู้อ่านคนไหนก็เปิดในโหมดดูได้; ปุ่ม Edit (และทุกอย่างที่มันปลดล็อก) ต้องการ `broadcast.update` Scope/กลุ่มผู้รับถูกกำหนดตายตัวตอนส่งและแก้ไขไม่ได้ที่นี่ Schedule กับวันหมดอายุแก้ไขได้เสมอ; **title, message และ severity แก้ได้ก็ต่อเมื่อสถานะปัจจุบันของ broadcast ยังเป็น `scheduled`** — เมื่อออกอากาศไปแล้ว backend จะ 400 ทันทีที่พยายามแตะเนื้อหา (`content_locked`) เพราะผู้รับอาจอ่านไปแล้ว การ์ด `BroadcastPreview` ตัวเดียวกับที่ Compose ใช้ก็ถูกนำมาแสดงผลแบบ live ที่นี่ด้วย

เบื้องหลัง SPA, controller ของ backend-gateway (`api/notifications/broadcasts/*`) forward ผ่าน RPC ไปยัง **micro-notification** — `BroadcastService` (สร้าง) และ `BroadcastAdminService` (list/get/update/delete) ซึ่งเขียน `tb_broadcast_notification` และเติม `tb_user_broadcast_action` แบบ lazy ตอนอ่าน ดู [Data Model](/th/platform/broadcasts/data-model)

## 2. บริบททางธุรกิจ

News และ Broadcasts ยังคงแบ่งปัญหาการประกาศกันตามความเร่งด่วนเหมือนเดิม บทความข่าวเป็นเนื้อหาแบบ **pull**: มันนั่งอยู่หลัง public feed จนกว่า client จะ render มัน broadcast นั้น**ขัดจังหวะ**: มันปรากฏใน notification bell ของผู้ใช้ in-scope ทุกคน — และแบบ live ผ่าน WebSocket สำหรับผู้ใช้ที่ออนไลน์ — ทันทีที่ถูกส่ง สิ่งที่ไม่จริงอีกต่อไปคือ broadcast "แก้ไขหรือเรียกคืนไม่ได้": ตอนนี้ผู้ส่งแก้เนื้อหาของ broadcast ที่ยัง `scheduled` ได้, ปรับเวลากำหนดหรือวันหมดอายุได้ตลอด, ต่ออายุให้หมดทันทีจากรายการได้ หรือลบแบบ soft ได้เลย มีแค่ *เนื้อหา* เท่านั้นที่ล็อกเมื่อออกอากาศไปแล้ว — กลุ่มผู้รับและข้อเท็จจริงว่ามันออกอากาศไปแล้วยกเลิกไม่ได้ use case ตามแบบฉบับไม่เปลี่ยนแปลง: คำเตือนปิดปรับปรุงตามกำหนด, ประกาศ incident และประกาศรายโรงแรมไปยัง business unit หนึ่งแห่ง

การกำหนดเวลา (scheduling) ยังให้ operator เตรียมประกาศไว้ล่วงหน้าได้เหมือนเดิม: row ของ broadcast ที่กำหนดเวลาไว้ถูกสร้างทันทีแต่จะอยู่นอก list ของผู้รับจนกว่า `scheduled_at` จะผ่านไป (เป็นการ filter ตอนอ่าน เหมือนเดิม) สิ่งหนึ่งที่ดีขึ้นเฉพาะเส้นทาง**ระบุผู้รับ**เท่านั้น: การส่งแบบกำหนดเวลาไปยังผู้ใช้ที่ระบุเจาะจงเคยค้างไม่ถูกส่งเลยโดยไม่มี live push; ตอนนี้มี background worker ใหม่ทุก 30 วินาทีที่คอย claim personal notification ที่ถึงเวลาแล้วแต่ยังไม่ push แล้ว push แบบ live ทันทีที่ถึงเวลา **system-wide และ business-unit broadcast ไม่มีกลไกเทียบเท่าเลย** — เมื่อกำหนดเวลาไว้แล้วมันจะปรากฏแบบ passive เท่านั้น ตอนที่ผู้รับ fetch ครั้งถัดไป รายละเอียดอยู่ใน [Permissions](/th/platform/broadcasts/permissions) §3–§4

## 3. แนวคิดสำคัญ

- **Target mode** — ไม่เปลี่ยน: `BroadcastTargetMode = 'system_all' | 'system_users' | 'bu'` สองตัวแรกใช้ `POST .../broadcasts/system` ร่วมกัน (array `userIds` แบบระบุชัดเปลี่ยน "ทุกคน" เป็น "ผู้ใช้เหล่านี้"); `bu` post ไป `.../broadcasts/bu` พร้อม `bu_code` ที่ resolve เป็น `tb_business_unit.id` ที่ฝั่ง server
- **Severity เป็นป้ายฝั่งผู้ส่งเท่านั้น ไม่ใช่ type ที่ผู้รับเห็น** คอลัมน์ `type` แบบเดิมที่มี prefix `SYS_*`/`BU_*` **หายไปแล้ว** — `tb_broadcast_notification` ไม่มีคอลัมน์ `type` หรือ `category` อีกต่อไปเลย สิ่งที่ผู้ส่งเลือก (Info/Warning/Critical/Maintenance/Other…) ถูกเก็บเป็นสตริงธรรมดาใน `metadata.severity` สำหรับ badge ของหน้าแอดมินเท่านั้น; `event` ของ broadcast ทุกตัวถูก hardcode เป็น `info` จริง ๆ และ `doc_type` สะท้อน scope ของมัน (`system` หรือ `business_unit`) UI ของ compose บอกตรง ๆ เลยว่า "สีและป้ายเป็นการจัดหมวดหมู่ภายในเท่านั้น — ผู้รับเห็นแค่การแจ้งเตือนแบบมาตรฐาน"
- **วันหมดอายุ (`end_at`) บังคับแล้ว** ไม่ใช่คอลัมน์ตายอีกต่อไป หน้า Compose ตั้งค่าเริ่มต้นเป็น preset 30 วัน (7/30/90 วัน หรือกำหนดวันที่เอง) โดยอิงจากเวลาที่*กำหนดไว้ส่ง*เมื่อมีการตั้งเวลา ไม่งั้นอิงจากตอนนี้ `end_at` คือสิ่งที่ backend ใช้คำนวณ `status` ของ broadcast
- **`status` คำนวณเสมอ ไม่เคยถูกเก็บ** `active` / `scheduled` / `expired` / `deleted` ถูกคำนวณที่ฝั่ง server จาก `deleted_at`, `scheduled_at` และ `end_at` ทุกครั้งที่อ่าน — ไม่มีคอลัมน์ status
- **`doc_version` เป็น optimistic lock จริงแล้ว** ไม่ใช่แค่ตกแต่ง schema เฉย ๆ ทั้ง endpoint update และ delete ต้องใช้มันและปฏิเสธค่าที่เก่าด้วย 409
- **Content lock** — title, message และ metadata แก้ได้ก็ต่อเมื่อสถานะปัจจุบันของ row เป็น `scheduled` การเลื่อน schedule ของ broadcast ที่ออกอากาศไปแล้วกลับไปในอนาคต (การ "ถอน") จะเปิดให้แก้เนื้อหาได้อีกครั้งอย่างถูกต้อง (เป็นสองขั้นที่ตั้งใจ ไม่ใช่รูรั่ว)
- **หนึ่ง row, read state แบบ lazy** — broadcast แบบ `system_all` หรือ `bu` ยังเป็น row ของ `tb_broadcast_notification` ตัวเดียว; ใครอ่านแล้วอยู่ใน `tb_user_broadcast_action` ที่สร้างแบบ lazy ตอน action แรก
- **การส่งแบบระบุผู้รับยัง fork ออกไปเต็มตัว** การส่งแบบ `system_users` ที่มี `userIds` ไม่แตะ `tb_broadcast_notification` เลย — มัน fan out เป็น row ของ `tb_notification` หนึ่งตัวต่อผู้รับที่มีอยู่จริง เหมือนเดิม นี่ยังเป็น target mode เดียวที่ List/Edit มองไม่เห็น จัดการไม่ได้ หรือลบภายหลังไม่ได้เลย
- **การลบใช้งานได้แล้ว** `DELETE /api/notifications/broadcasts/:id` ลบแบบ soft สำหรับ broadcast แบบ `system_all`/`bu` (`deleted_at`/`deleted_by_id`) ซึ่งแทนที่ผลการตรวจสอบเดิมที่บอกว่า "ไม่มี code path ใดเขียน `deleted_at`"

## 4. บทบาทและ Persona

ตอนนี้มีสี่ permission key ที่ gate โมดูลนี้ ผ่าน [Platform RBAC](/th/platform/rbac) ที่ seed ไว้ตาม role ใน `seed.platform-role-permission.data.ts`:

| Surface | Gate | Key |
|---|---|---|
| route `/broadcasts` + รายการใน nav | `PrivateRoute` / nav filter | `broadcast.read` |
| route `/broadcasts/:id/edit` (เปิดในโหมดดู) | `PrivateRoute` | `broadcast.read` |
| route `/broadcasts/new` | `PrivateRoute` | `broadcast.send` |
| ปุ่ม Send (Compose) | `<Can>` | `broadcast.send` |
| ปุ่ม Edit (แถวใน List + หน้า Edit) | `<Can>` | `broadcast.update` |
| Expire Now (แถวใน List) | `<Can>` | `broadcast.update` |
| Delete (แถวใน List) | `<Can>` | `broadcast.delete` |
| `GET/PATCH/DELETE .../broadcasts*` | `KeycloakGuard` + `PlatformPermissionGuard` | key ที่ตรงกัน ฝั่ง server |

| Role | Key ที่ได้รับ |
|---|---|
| Platform Admin | `broadcast.*` (ครบทั้งสี่) |
| Support Manager | `read`, `send`, `update` — **ไม่มี** `delete` |
| Support Staff | `read` เท่านั้น |
| Security Officer | ไม่มีเลย |

`broadcast.read` **ไม่ใช่ orphan key อีกต่อไป** — ตอนนี้มัน gate route ของ List, รายการใน nav และโหมดดูของหน้า Edit ทุก route ฝั่ง server บังคับใช้ key ที่ตรงกันผ่าน `PlatformPermissionGuard` แบบหยาบ (coarse): grant ระดับแพลตฟอร์ม **หรือ** grant ใน cluster เดียวก็ผ่านได้ ตรงกับ check ฝั่ง SPA เอง; การจำกัดขอบเขตราย-cluster แบบแท้จริงยังเป็นช่องว่างที่รู้และตั้งใจเลื่อนออกไป matrix แบบเต็ม, กฎ content lock และ delivery/scheduling semantics แต่ละโหมดอยู่ใน [Permissions](/th/platform/broadcasts/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [News](/th/platform/news) — คู่เทียบฝั่ง pull: เนื้อหาที่เขียนไว้พร้อมวงจรชีวิตและ public feed เทียบกับ push ของ Broadcasts
- [Business Units](/th/platform/business-units) — โหมด BU กำหนดเป้าหมายหนึ่งหน่วยด้วย `code`; หน้า Compose โหลด option จาก API ของโมดูลนั้น (เฉพาะ BU ที่ active, จำกัด 100 รายการ)
- [Users](/th/platform/users) — โหมด *specific users* ค้นหา user registry ผ่าน `UserMultiSelect`; ผู้รับถูกส่งเป็น UUID ของ `tb_user.id`
- [Platform RBAC](/th/platform/rbac) — กำหนดและ resolve สี่ key `broadcast.*` ที่ gate ทั้ง SPA และ API

## 6. แหล่งอ้างอิง

- `../carmen-platform/src/App.tsx` — สาม route guard (`broadcast.read`, `broadcast.send`, `broadcast.read`) และ `feature="broadcasts"`
- `../carmen-platform/src/components/nav/platformNav.ts` — รายการ nav "Broadcasts" (`permission: 'broadcast.read'`, `feature: 'broadcasts'`, ไม่มี `superAdminOnly`)
- `../carmen-platform/src/pages/BroadcastManagement.tsx`, `src/pages/broadcastManagement/{BroadcastSummary,BroadcastFilters,broadcastColumns}.tsx` — หน้า List
- `../carmen-platform/src/pages/BroadcastCompose.tsx` — หน้า Compose: แท็บ, validation, payload builder, preset วันหมดอายุ, confirm dialog, shortcut
- `../carmen-platform/src/pages/BroadcastEdit.tsx` — หน้า Edit: content lock, การแก้ schedule/วันหมดอายุ, confirm ของ past/reschedule
- `../carmen-platform/src/components/BroadcastPreview.tsx` — preview แบบ live ที่ใช้ร่วมกันระหว่าง Compose และ Edit (`severityStyle`, `reachSummary`)
- `../carmen-platform/src/utils/broadcastExpiry.ts` — `resolveExpiryIso()`, preset 7/30/90 วัน
- `../carmen-platform/src/services/broadcastService.ts` — `sendSystem`/`sendBu`/`getAll`/`getById`/`update`/`remove`; `src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, `BroadcastListItem`, `BroadcastStatus`, `BroadcastUpdatePayload`, `BroadcastSummary`
- `../carmen-platform/src/utils/permissions.ts` — ค่าคงที่ `PERMISSIONS.BROADCAST.SEND`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (บรรทัด 332), `tb_broadcast_notification` (บรรทัด 369), `tb_user_broadcast_action` (บรรทัด 403); enum `enum_broadcast_scope`, `enum_notification_doc_type`, `enum_notification_event` (บรรทัด 112–131)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260810000000_notification_redesign_additive/`, `20260811000000_notification_redesign_drop_legacy/` — การปรับใหญ่ที่ลบ `type`/`category`/`is_sent` และเพิ่ม `scope`/`doc_type`/`event`/`pushed_at`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — ทั้งหกเส้นทางของ broadcast และ guard ของมัน
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/broadcast.service.ts` (เส้นทางสร้าง), `broadcast-admin.service.ts` (list/get/update/delete, การคำนวณ status), `schedule.worker.ts` (worker push ที่ทำงานทุก 30 วินาที เฉพาะ `tb_notification`)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts`, `seed.platform-role-permission.data.ts` — สี่ key `broadcast.*` และการมอบสิทธิ์ตาม role

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/broadcasts/data-model) — ตารางฟิลด์ของ `tb_broadcast_notification` และ `tb_user_broadcast_action`, การปรับปรุง enum, การ fork ของการส่งแบบระบุผู้รับไปยัง `tb_notification`, และความแตกต่างเทียบกับ type ของ SPA
- [UI Screens](/th/platform/broadcasts/ui-screens) — ทั้งสามหน้าจอ: List (คอลัมน์, filter, สรุปยอด, CSV export), Compose (แท็บ target, preset วันหมดอายุ, preview แบบ live) และ Edit (content lock, การแก้ schedule/วันหมดอายุ)
- [Permissions](/th/platform/broadcasts/permissions) — matrix gate สี่ key, delivery/scheduling semantics แต่ละโหมด, กฎ content lock และ optimistic lock, และตาราง edge case สำหรับผู้ทดสอบ
