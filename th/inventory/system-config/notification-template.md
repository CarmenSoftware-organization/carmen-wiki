---
title: Notification Template
description: Template ข้อความที่ใช้ซ้ำได้ (tb_notification_template) ที่ถูกเลือกต่อ workflow stage/action/recipient/channel เพื่อ render เป็นการแจ้งเตือนในแอป มีแค่ channel "app" เท่านั้นที่ถูก dispatch จริง — email เลือกได้ใน workflow editor แต่ dispatcher เพิกเฉยเงียบ ๆ; template sms และ line สร้างได้แต่ไม่มีผู้บริโภคที่ใดเลย
published: true
date: 2026-07-29T10:45:00.000Z
tags: system-config, notification-template, workflow, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:45:00.000Z
---

# Notification Template

> **สรุปโดยย่อ**
> **Routes:** `/system-admin/notification-template` (+ `/new`, `/:id`) &nbsp;·&nbsp; **ตาราง:** `tb_notification_template` (tenant schema — คนละตัวกับ `tb_message_format` ที่ platform schema ที่ [reporting-audit/notification](/th/inventory/reporting-audit/notification) บันทึกไว้) &nbsp;·&nbsp; **Endpoint:** `api/config/{bu_code}/notification-templates` &nbsp;·&nbsp; **ถูกใช้โดย:** config การแจ้งเตือนต่อ stage ของ [system-config/workflow](/th/inventory/system-config/workflow) dispatch โดย `WorkflowNotificationDispatcher` &nbsp;·&nbsp; **ช่องว่างที่ยืนยันแล้ว:** `type` รองรับ `app`/`email`/`sms`/`line` แต่ dispatcher ส่งแค่ `app` เท่านั้น — `email` เลือกได้ใน workflow editor และถูกบันทึกลง `tb_workflow.data` แต่ไม่เคยถูกส่งจริง; `sms`/`line` ไม่มี picker ที่ใดเลย

![Notification Template list](/screenshots/notification-template/index.png)

![Notification Template detail](/screenshots/notification-template/detail.png)

![Notification Template create form](/screenshots/notification-template/new.png)

## 1. คืออะไรและใครใช้

Notification Template คือหน้าจอ CRUD ธรรมดาสำหรับแถว **`tb_notification_template`** — ข้อความที่ใช้ซ้ำได้พร้อม `name`, `type` (channel: `app`/`email`/`sms`/`line`), `subject` (optional), `body` (required), `description` (optional), และ flag `is_active` คำอธิบายที่แปลไว้ของหน้าจอเองบอกจุดประสงค์ตรง ๆ: *"Manage reusable notification templates for workflow events."*

Template ไม่ใช่เนื้อหาลอย ๆ — มันมีอยู่เพื่อให้**ถูกเลือกโดย config การแจ้งเตือนของ workflow stage** บน stage editor ของ [system-config/workflow](/th/inventory/system-config/workflow) แต่ละ entry ของ `available_actions[<action>].recipients[<slot>].notification_channel[<channel>]` มี `notification_template_id` ของตัวเอง กรองเฉพาะ template ที่ active และมี `type` ตรงกับ channel นั้น (prop `channelType` ของ `LookupNotificationTemplate`) ตอน runtime `WorkflowNotificationDispatcher.dispatch()` อ่าน `notification_template_id` นั้นกลับจาก `tb_workflow.data` โหลดแถว `tb_notification_template` ที่อ้างถึง และ render `subject`/`body` ของมันผ่าน engine แทนที่ `{{placeholder}}` เล็ก ๆ ก่อน dispatch เป็นการแจ้งเตือนในแอป ดู §6 สำหรับ chain เต็มจาก trigger ถึง delivery

**ดูแลโดย** Sysadmin (เนื้อหา template), Workflow Administrator (template ไหนถูกผูกกับ stage/action/recipient/channel ไหน — ทำที่หน้าจอ Workflow ไม่ใช่ที่นี่) **อ่านโดย** workflow notification dispatcher ตอน submit/approve/reject/sendback

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง template | Notification Template → **Add** → กรอก Name, Channel, Subject (optional), Body | `name` + `type` ต้อง unique คู่กัน — ซ้ำแล้วถูก reject ฝั่ง server (`ALREADY_EXISTS`) |
| แก้ template | Detail ของ template → **Edit** | `PUT`, guard ด้วย `doc_version` (optimistic lock) |
| ปิดใช้งานโดยไม่ลบ | Detail → **Edit** → toggle **Active** ปิด | `is_active = false`; template ที่ปิดใช้งานจะหายไปจาก picker ของ workflow editor เท่านั้น (`filter: tpl.is_active && tpl.type === channelType`) — ไม่ได้ถูกลบ |
| ลบ template | Detail → โหมด **Edit** → **Delete** | Soft delete (`deleted_at` + บังคับ `is_active = false`) — **ไม่มีการเช็คว่า workflow ยังอ้างอิง id ของ template นี้อยู่หรือไม่** (ดู §4) |
| ผูก template เข้ากับ workflow stage | [system-config/workflow](/th/inventory/system-config/workflow) → stage → tab Notifications → เลือก channel toggle → เลือก template | ไม่ได้ทำจากหน้าจอนี้เลย — หน้านี้แค่สร้างเนื้อหา |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| `Notification template "<name>" already exists for channel <type>` | `(name, type)` ซ้ำตอน create หรือตอน rename/เปลี่ยน channel ระหว่าง update | **ยืนยันแล้ว** — `notification-template.service.ts` ทั้ง `create()`/`update()` เช็ค `findFirst` อย่างชัดเจนก่อนเขียน ตรงกับ `@@unique([name, type, deleted_at])` ของ schema |
| Update ถูก reject เพราะไม่มี `doc_version` | `update()` ต้องการ `doc_version` เป็นตัวเลขใน payload | **ยืนยันแล้ว** — error `COMMON_DOC_VERSION_REQUIRED` ถ้าไม่มี |
| `body` required, `subject` optional | Validation ระดับฟอร์มด้วย Zod (`noti-tmpl-form-schema.ts`) สะท้อน DB (`body String?` แต่ส่งเสมอ; `subject String?` optional จริง) | **ยืนยันแล้ว** |
| เลือก "Email" ใน workflow stage editor ดูเหมือนใช้ได้แต่ข้อความไม่เคยมาถึง | Dispatcher รู้จักเฉพาะ `channelName === "app"` — channel อื่นถูกข้ามด้วยเหตุผล `channel_not_supported` | **ยืนยันแล้ว** — ดู §6; นี่เป็นช่องว่างที่จริงและยังมีอยู่ในปัจจุบัน ไม่ใช่ข้อผิดพลาดในการบันทึกเอกสาร |
| Workflow stage ยังแสดง notification_template_id หลังจาก template นั้นถูกลบ | ไม่มีการเช็คการอ้างอิงตอนลบ | **ยืนยันแล้ว** — id ที่ค้างอยู่ resolve เป็น `template_not_found` ตอน dispatch และ slot/channel นั้นถูกข้ามเงียบ ๆ (ดู §4) |

## 4. กรณีพิเศษ

- **การลบไม่มี guard การใช้งาน** `delete()` ของ `notification-template.service.ts` soft-delete โดยไม่มีเงื่อนไข — ไม่เช็คว่ามี `tb_workflow.data.stages[].available_actions[].recipients[].notification_channel[].notification_template_id` ใดยังชี้ไปที่แถวที่กำลังจะถูกลบหรือไม่ (ไม่มี FK; `tb_workflow.data` เป็น JSONB) Template ที่ถูกลบแต่ยังถูกอ้างอิงอยู่จะทำให้เกิด `template_not_found` เงียบ ๆ ตอน dispatch แทนที่จะมี error แสดงที่ใดใน UI
- **มีแค่ channel `app` เท่านั้นที่ถูก dispatch จริง — ยืนยันจากการอ่าน dispatcher ไม่ใช่การอนุมาน** `WorkflowNotificationDispatcher.dispatch()` วนลูป `Object.keys(channels)` และข้าม (`reason: 'channel_not_supported'`) อะไรก็ตามที่ไม่ใช่ string ตายตัว `"app"` โดยชัดเจน ตัว type `WfChannel` ของ workflow stage editor เองคือ `"app" | "email"` — ดังนั้น **Email ตั้งค่าได้และถูกบันทึก** แต่ไม่เคยถูกส่งจริง `sms` และ `line` เป็นค่าที่ถูกต้องของ `enum_notification_channel` และเป็น `NotificationTemplateType` ที่ถูกต้องในฟอร์ม create ของหน้าจอ CRUD นี้เอง แต่**ไม่มี lookup ใดใน frontend ที่กรองด้วย `channelType="sms"` หรือ `"line"`** — template ของสองประเภทนี้สร้างได้แต่ไม่มีผู้บริโภคเลยที่พบในโค้ดทั้งหมด
- **การ render เป็นการแทนที่แบบ Mustache แบน ๆ ไม่ใช่ template engine** `render()` ใน `workflow-notification-dispatcher.service.ts` รองรับแค่ `{{varName}}` (ไม่มี nesting, ไม่มี helper, ไม่มี conditional) placeholder ที่มีคือ: `{{recipientName}}`, `{{docNo}}`, `{{department}}`, `{{totalAmount}}`, `{{actorName}}`, `{{currentStage}}`, `{{reason}}`, `{{url}}` — token `{{...}}` อื่นใดใน `subject`/`body` ของ template จะ render เป็น string ว่าง เพราะ code comment ระบุตรง ๆ ว่า "the seeded templates only use flat placeholders"
- **`subject` มี fallback, `body` ไม่มี** ถ้า `subject` ว่าง dispatcher จะ fallback ไปที่ `${docType} update` หรือ `name` ของ template เอง; ถ้า `body` ว่าง ข้อความที่ render จะเป็น string ว่างเปล่า — ไม่มี fallback แบบเดียวกันสำหรับเนื้อหา body
- **การ personalize ชื่อผู้รับเป็นแบบ best-effort** `fetchUserProfiles()` ค้นหาชื่อที่แสดงผ่าน TCP call ไปยัง auth service และกลืน error ใด ๆ ให้เป็น map ว่าง — การค้นหาที่ล้มเหลว render `{{recipientName}}` เป็น `""` แทนที่จะบล็อกการส่ง
- **ปลายทางของการส่งคือ `tb_notification` (platform schema) ไม่ใช่ตารางนี้** TCP call `notifications.create` ของ dispatcher บันทึกไว้เต็มที่ [reporting-audit/notification](/th/inventory/reporting-audit/notification) — ตารางของหน้านี้แค่ให้เนื้อหา `subject`/`body` ที่ render แล้วเท่านั้น ไม่ใช่ที่บันทึกข้อความที่ส่งไปแล้ว

---

## 5. โมเดลข้อมูล (Dev)

Source: tenant schema

### 5.1 `tb_notification_template`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงของ template |
| `type` | `enum_notification_channel` | No | `app` / `email` / `sms` / `line` |
| `subject` | `String? @db.VarChar` | Yes | Render เป็น title ของการแจ้งเตือน; fallback ไปที่ `${docType} update` หรือ `name` ถ้าว่าง |
| `body` | `String? @db.Text` | Yes | Render เป็นข้อความของการแจ้งเตือน; ไม่มี fallback ถ้าว่าง |
| `description` | `String? @db.VarChar` | Yes | หมายเหตุภายใน — ไม่ถูกส่งให้ผู้รับ |
| `is_active` | `Boolean` | No | Default `true` Template ที่ inactive ถูกตัดออกจาก picker ของ workflow editor |
| `doc_version` | `Int @db.Integer` | No | Default `0` กลไก optimistic-concurrency — ดู [system-config/doc-version](/th/inventory/system-config/doc-version) |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, type, deleted_at])` map `notificationtemplate_name_type_deletedat_u`; `@@index([name])`; `@@index([type])`

**`enum_notification_channel`:** `app`, `email`, `sms`, `line` — 4 ค่า มีแค่ `app` เท่านั้นที่มี dispatch path จริง (§4)

## 6. ตั้งแต่ template ถูกใช้ — chain เต็มจาก trigger ถึง delivery

1. **สร้าง** template ที่นี่ (`tb_notification_template`) ตั้งค่า `type` ให้ตรงกับ channel ที่ตั้งใจใช้
2. **ผูก** มันที่ stage editor ของ [system-config/workflow](/th/inventory/system-config/workflow): เลือก recipient slot (`requestor` / `current_approve` / `next_step` บวก slot ที่สี่ `previous_step` ที่ dispatcher รองรับแต่ type ของ editor component ตัวนี้เองไม่ได้เปิดให้ใช้), toggle channel (`app` หรือ `email`), และเลือก template ที่มี `type` ตรงกับ channel นั้นจาก dropdown ที่กรองเฉพาะ template active
3. **บันทึก** — เขียน `notification_template_id` ลง `tb_workflow.data.stages[].available_actions[<action>].recipients[<slot>].notification_channel[<channel>]` ไม่มี FK — เป็นการอ้างอิง JSONB แบบหลวม
4. **Trigger** — ตอนมี action submit/approve/reject/sendback ของ workflow `WorkflowOrchestratorService` (บันทึกไว้ที่ [system-config/workflow](/th/inventory/system-config/workflow)) เรียก `WorkflowNotificationDispatcher.dispatch()` พร้อม action ที่ทำและบริบทของเอกสาร
5. **Resolve ผู้รับ** — dispatcher map แต่ละ slot ที่ตั้งค่าไว้ไปเป็น user id จริง (`requestor` → `requestor_id` ของเอกสาร; `current_approve` → ผู้ที่เพิ่งทำ action; `next_step` → `assigned_users` ของ stage ที่กำลังรอ; `previous_step` → `assigned_users` ของ stage ก่อนหน้า actor)
6. **Resolve channel** — สำหรับแต่ละ slot วนลูป channel ที่ตั้งค่าไว้; **มีแค่ `app` เท่านั้นที่ไปต่อ** (§4); template ที่อ้างอิงถูกโหลดตาม id (`deleted_at: null` — template ที่ soft-delete แล้ว resolve เป็น not-found)
7. **Render** — `subject`/`body` วิ่งผ่านการแทนที่ `{{placeholder}}` แบบแบน (§4) โดยใช้บริบทของ actor, เอกสาร, และผู้รับ
8. **Dispatch** — TCP call `notifications.create` ไปยัง micro-notification service insert แถว `tb_notification` (platform schema), emit ผ่าน Socket.io แล้วพลิก `is_sent = true` ดู [reporting-audit/notification](/th/inventory/reporting-audit/notification) สำหรับรูปร่างเต็มของตารางปลายทางนั้น — หน้านี้ไม่ได้ทำซ้ำเนื้อหานั้น

## 7. ความเชื่อมโยงข้ามโมดูล

- [system-config/workflow](/th/inventory/system-config/workflow) — จุดที่ template ถูกผูกเข้ากับ stage/action/recipient/channel จริง ๆ; เอกสาร `recipients` ของหน้านั้นเองเป็น blob `{ ... }` ที่ opaque ในตอนนี้ — หน้านี้เป็นหน้าแรกที่บันทึกรูปร่างของ `notification_channel`/`notification_template_id` ที่อยู่ข้างในมัน
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — ตารางปลายทาง (`tb_notification`, platform schema) ที่ dispatcher เขียนถึง และ inbox แบบรวมที่อ่านมันกลับ
- [system-config/doc-version](/th/inventory/system-config/doc-version) — กลไก optimistic-lock ที่ `doc_version` ของตารางนี้เข้าร่วม
- [system-config](/th/inventory/system-config) — module แม่

## 8. แหล่งอ้างอิง

- **Frontend routes:** `../carmen-inventory-frontend-react/routes/system-admin/notification-template/notification-template.route.tsx`, `notification-template-new.route.tsx`, `notification-template-edit.route.tsx`, `noti-tmpl.tsx` (list), `noti-tmpl-form.tsx` (create/view/edit), `use-noti-tmpl-table.tsx`
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-notification-template.ts`; `types/noti-tmpl.ts`
- **Frontend lookup (ผู้บริโภค):** `../carmen-inventory-frontend-react/components/lookup/lookup-noti-tmpl.tsx` — `LookupNotificationTemplate` กรองด้วย `channelType`
- **Frontend workflow-editor consumer:** `../carmen-inventory-frontend-react/routes/system-admin/workflow/wf-stage-notifications.tsx` — `WfChannel = "app" | "email"`
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/notification-template/notification-template.service.ts` (CRUD + validate duplicate-name/channel), `.controller.ts`
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_notification-templates/config_notification-templates.controller.ts` — `api/config/:bu_code/notification-templates`
- **Dispatcher:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/workflow/workflow-notification-dispatcher.service.ts` — `WorkflowNotificationDispatcher.dispatch()`, `render()`
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_notification_template` (บรรทัด ~3760), `enum_notification_channel` (บรรทัด ~88)
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `systemAdmin.notificationTemplate.*` (namespace ยืนยัน "Manage reusable notification templates for workflow events")
