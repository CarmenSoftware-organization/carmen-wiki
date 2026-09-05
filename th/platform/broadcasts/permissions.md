---
title: Broadcasts — สิทธิ์การเข้าถึง (Permissions)
description: สี่ key broadcast.* (read/send/update/delete) gate หน้าจอ List/Compose/Edit ของโมดูลและ REST endpoint ที่ตรงกันฝั่ง server; เนื้อหาถูกล็อกเมื่อ broadcast ออกอากาศไปแล้ว doc_version เป็น optimistic lock จริง และมีแค่การส่งแบบระบุผู้รับ (system_users) เท่านั้นที่ยังคง fire-and-forget
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, broadcasts, permissions
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# Broadcasts — สิทธิ์การเข้าถึง (Permissions)

> **At a Glance**
> **สี่ key ไม่ใช่หนึ่ง:** `broadcast.read` (List + ดูหน้า Edit), `broadcast.send` (Compose + Send), `broadcast.update` (action Edit + Expire Now + `PATCH`), `broadcast.delete` (Delete + `DELETE`) &nbsp;·&nbsp; **ทั้งสี่ถูกบังคับใช้ฝั่ง server** ผ่าน `PlatformPermissionGuard` บนทุกหนึ่งในหกเส้นทางของ broadcast &nbsp;·&nbsp; **ความหยาบที่รู้อยู่แล้ว (ไม่เปลี่ยนตั้งแต่ sync ครั้งก่อน):** guard ผ่านได้ด้วย grant ระดับแพลตฟอร์ม **หรือ** grant ใน cluster เดียวก็ได้ — การจำกัดขอบเขตราย-cluster แบบแท้จริงยังถูกเลื่อนออกไปอย่างชัดเจน &nbsp;·&nbsp; **Content lock:** title/message/metadata แก้ได้เฉพาะตอน broadcast ยัง `scheduled`; ไม่งั้น 400 `content_locked` &nbsp;·&nbsp; **`doc_version` เป็น optimistic lock จริง** ทั้ง `PATCH` และ `DELETE` ตรวจสอบมัน &nbsp;·&nbsp; **การส่งแบบระบุผู้รับ (`system_users`) ยังคง fire-and-forget** — มองไม่เห็นจาก `broadcast.read`/`.update`/`.delete` เลย เพราะไม่เคยแตะ `tb_broadcast_notification`

## 1. ภาพรวม

Broadcasts ย้ายจาก key gate เดียวมาเป็นสี่ key เต็มรูปแบบ สอดคล้องกับการย้ายจากหน้าส่งครั้งเดียวมาเป็นสามหน้าจอ List/Compose/Edit ทั้งสี่ key ถูกลงทะเบียนใน permission catalog ของแพลตฟอร์ม (`seed.platform-permission.data.ts`) พร้อมคำอธิบายจริง — `broadcast.read` **ไม่ใช่ orphan อีกต่อไป**: ตอนนี้มัน gate route ของ List, รายการใน nav และโหมดดูของหน้า Edit ปิดผลตรวจสอบเดิมก่อนปรับใหญ่ที่บอกว่ามัน "ไม่ gate อะไรใน SPA เลย"

ทุก key ถูกบังคับใช้**ทั้งสอง**ฝั่ง — client (`<Can>`, `PrivateRoute`) และ server (`KeycloakGuard` + `PlatformPermissionGuard` + `@RequirePlatformPermission(...)`) บนทั้งหกเส้นทางของ gateway: สอง endpoint สำหรับส่ง (การบังคับใช้แบบหยาบไม่เปลี่ยนตั้งแต่ backend PR #239) บวกสี่ endpoint ฝั่งแอดมิน (list/get/update/delete) ที่ถูกเพิ่มมาในการปรับใหญ่ครั้งเดียวกันที่สร้างหน้า List/Edit การบังคับใช้ตั้งใจให้**หยาบ**ทุกที่ ไม่ใช่แค่ตอนส่ง: `PlatformPermissionService.has()` คืน true ถ้า key ที่ต้องการมีอยู่ใน scope **ระดับแพลตฟอร์ม** ของผู้เรียก **หรือ** ใน scope ของ **cluster เดียวก็ได้** — ผู้ใช้ที่ได้รับ เช่น `broadcast.delete` แค่ cluster เดียว สามารถลบ broadcast row **ไหนก็ได้** ผ่าน API นี้ ไม่ว่าจะเป็น system-wide หรือ scope เป็น BU เพราะไม่มี code path ไหนในโมดูลนี้ที่ resolve ว่า "broadcast รายการนี้เป็นของ cluster ไหน" แล้วเช็ค grant กับมัน นี่คือข้อจำกัดเดียวกับที่ wiki ก่อนปรับใหญ่ document ไว้สำหรับ `broadcast.send` อย่างเดียว ตอนนี้มันใช้กับทั้งสี่ key เหมือนกันหมด

## 2. Gate matrix

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| route `/broadcasts` + รายการใน nav | `PrivateRoute` / nav filter | `broadcast.read` | `src/App.tsx`, `src/components/nav/platformNav.ts` |
| route `/broadcasts/:id/edit` (เปิดในโหมดดู) | `PrivateRoute` | `broadcast.read` | `src/App.tsx` |
| route `/broadcasts/new` | `PrivateRoute requiredPermission` | `broadcast.send` | `src/App.tsx` |
| "New Broadcast" (หัวหน้า List + empty state) | `<Can>` | `broadcast.send` | `BroadcastManagement.tsx` |
| ปุ่ม Send (Compose) | `<Can>` | `broadcast.send` | `BroadcastCompose.tsx` |
| แท็บ audience "All users" + "Specific users" | in-component `hasPermission('broadcast.send')` | `broadcast.send` | `BroadcastCompose.tsx` — code ป้องกันที่ไปไม่ถึงจริง เพราะการเข้าหน้านี้ได้ก็ต้องมี key เดียวกันอยู่แล้ว |
| ปุ่ม Edit (แถวใน List + หน้า Edit) | `<Can>` | `broadcast.update` | `broadcastColumns.tsx`, `BroadcastEdit.tsx` |
| Expire Now (แถวใน List) | `<Can>` | `broadcast.update` | `broadcastColumns.tsx` |
| Delete (แถวใน List) | `<Can>` | `broadcast.delete` | `broadcastColumns.tsx` |
| `POST /api/notifications/broadcasts/system` / `/bu` | `KeycloakGuard` + `PlatformPermissionGuard` | `broadcast.send` (หยาบ) | `notification.controller.ts` |
| `GET /api/notifications/broadcasts` (list) | guard เดียวกัน | `broadcast.read` (หยาบ) | `notification.controller.ts` |
| `GET /api/notifications/broadcasts/:id` | guard เดียวกัน | `broadcast.read` (หยาบ) | `notification.controller.ts` |
| `PATCH /api/notifications/broadcasts/:id` | guard เดียวกัน | `broadcast.update` (หยาบ) | `notification.controller.ts` |
| `DELETE /api/notifications/broadcasts/:id` | guard เดียวกัน | `broadcast.delete` (หยาบ) | `notification.controller.ts` |

### การมอบสิทธิ์ตาม role (จาก `seed.platform-role-permission.data.ts`)

| Role | Key |
|---|---|
| Platform Admin | `broadcast.*` — ครบทั้งสี่ |
| Support Manager | `read`, `send`, `update` — **ไม่มี** `delete` |
| Support Staff | `read` เท่านั้น |
| Security Officer | ไม่มีเลย |

สิ่งที่ผู้ทดสอบควรรู้:

- **Gate ของแท็บ audience ใน Compose ซ้ำซ้อนจริง ไม่ใช่แค่ในทางทฤษฎี** — session ที่ไม่มี `broadcast.send` ไปไม่ถึง `/broadcasts/new` เลย (route guard บล็อกก่อน) ดังนั้น logic ซ่อนแท็บใน `BroadcastCompose` จึงไปไม่ถึงในทางปฏิบัติ มันจะมีความหมายก็ต่อเมื่อ key ของ route guard เกิดต่างจาก check ของคอมโพเนนต์เองในอนาคต
- **แค่ `broadcast.read` ก็เพียงพอที่จะเรียกดูและเปิด broadcast แบบ `system_all`/`bu` ได้ทุกอันรวมถึงเนื้อหาในโหมดดู** — มันไม่ใช่ key แบบ "เห็นว่า list มีอยู่" แต่คือ "เห็นทุกอย่างที่ List และ Edit แสดง" มีแค่ action ที่แก้ไขข้อมูลเท่านั้นที่ต้องใช้อีกสาม key
- **Support Manager แก้และต่ออายุให้หมด broadcast ได้ แต่ลบไม่ได้เลย** — ความไม่สมมาตรที่ตั้งใจและเป็นจริง คุ้มที่จะทดสอบโดยตรง (Edit/Expire Now แสดง, Delete ไม่มี จาก role นี้)
- **ตรวจสอบใหม่โดยตรงกับ `BroadcastCompose.tsx` แล้ว: Reset, แท็บ Business Unit ของ audience และทุกฟิลด์ message/type/delivery ไม่มี `<Can>` ห่ออยู่เลยสักตัว — มีแค่ Send เท่านั้นที่มี** ข้อยกเว้นเดียวคือสองแท็บ audience ของ system: มันไม่มี `<Can>` ห่อเหมือนกัน แต่ *ถูก* render แบบมีเงื่อนไขอยู่หลัง check ดิบ `hasPermission('broadcast.send')` (§2) ซึ่ง — ตามที่กล่าวไว้ข้างต้น — ไม่เคยกันใครออกจริง เพราะการเข้าหน้านี้ได้ก็ต้องมี key เดียวกันอยู่แล้ว

## 3. Delivery, scheduling และ push semantics แต่ละโหมด

Delivery/การมองเห็นยังคงรูปแบบ filter ตอนอ่านเหมือนเดิม แต่**พฤติกรรม live-push ตอนนี้แยกกันตาม target mode**ในแบบที่ไม่เคยเป็นมาก่อน:

| Mode | ที่เก็บ | กลุ่มผู้ชม (เส้นทางอ่าน) | Live push ตอนไม่กำหนดเวลา | Live push เมื่อถึงเวลาที่กำหนดไว้ |
|---|---|---|---|---|
| `system_all` | `tb_broadcast_notification`, `scope = 'system'` | ผู้ใช้ทุกคน | emit socket ไปยัง user id ที่ active และยังไม่ถูกลบทุกคน | **ไม่มีวัน** — ไม่มี worker เฝ้าตารางนี้ |
| `system_users` | `tb_notification`, หนึ่ง row **ต่อ id ผู้รับที่มีอยู่จริง** | ผู้ใช้กลุ่มนั้นเท่านั้น | emit socket ทีละ row | **ตอนนี้ส่งได้แล้ว** — `ScheduleWorker` cron ทุก 30 วินาที claim row ของ `tb_notification` ที่ถึงเวลาแล้วแต่ยังไม่ push แล้ว push แบบ live ประทับ `pushed_at` |
| `bu` | `tb_broadcast_notification`, `scope = 'business_unit'` | ผู้ใช้ที่สมาชิกภาพ `tb_user_tb_business_unit` แบบ live ตรงกับ BU ใน scope | emit socket ไปยัง member id ของ BU ปัจจุบัน | **ไม่มีวัน** — เหมือน `system_all` |

นี่คือทั้งการแก้จริงและช่องว่างจริงที่แยกกันตาม mode ควรบอกผู้ทดสอบให้ชัดเจน:

1. **การกำหนดเวลาแบบระบุผู้รับใช้งานได้ตามที่ผู้ทดสอบคาดหวังแล้ว** wiki ก่อนปรับใหญ่ document `getScheduledNotifications()` ว่าเป็น dead code ไม่มี caller — ฟังก์ชันนั้นและช่องว่างที่มันเป็นตัวแทนไม่มีอยู่แล้ว `ScheduleWorker.releaseDueNotifications()` เข้ามาแทน: ทุก 30 วินาทีมัน claim row ที่ `scheduled_at <= NOW()`, `pushed_at IS NULL` และ `scheduled_at` ไม่เก่าเกิน 7 วัน (กันกรณี cold-start) ภายใต้ `FOR UPDATE SKIP LOCKED`, emit แต่ละแถวแบบ live แล้วประทับ `pushed_at`
2. **broadcast แบบ `system_all`/`bu` ยังไม่มีกลไกเทียบเท่า** query ของ worker แตะแค่ `tb_notification` เท่านั้น — broadcast แบบ system-wide หรือ BU ที่กำหนดเวลาไว้ยังคงปรากฏแบบ passive เท่านั้น ตอนที่ผู้รับ fetch REST ครั้งถัดไป เหมือนก่อนปรับใหญ่ทุกประการ (แค่เหตุผลแคบลง: ไม่ใช่ "ไม่มี worker เลย" แต่เป็น "worker ที่มีอยู่ไม่ได้มองตารางนี้")
3. **สมาชิกภาพยังถูกประเมินต่อ query ไม่ใช่ต่อการส่ง** สำหรับ `system_all`/`bu` — ผู้ใช้ที่ถูกเพิ่มเข้า BU หลัง broadcast ถูกส่งไปแล้วยังเห็นมันอยู่ ไม่มีกำหนดเวลาเลยใน unread list และ 30 วันใน recent list (หน้าต่างตายตัว 30 วันของ `GET /api/notifications/recent`); ผู้ใช้ที่ถูกเอาออกจะไม่เห็นมันอีก ไม่มี snapshot ผู้รับ
4. **Read state ยังคง lazy และรายผู้ใช้** (`tb_user_broadcast_action`)

คำกล่าวอ้างของ wiki ก่อนปรับใหญ่เรื่อง "side-effect การ fan-out อีเมล (เมื่อ SMTP เปิดใช้งาน)" **ไม่จริงอีกต่อไป — พฤติกรรมนี้ถูกถอดออกแล้ว** `NotificationWriteService.notify()`, `BroadcastService.create()` และ `NotificationGateway` ถูกอ่านครบทั้งไฟล์สำหรับงานนี้ — ไม่มีตัวไหนเรียก `EmailService`/`PlatformEmailService` เลย service อีเมลเหล่านั้นยังอยู่ใน micro-notification แต่สำหรับ feature platform-email และ app-config test-send ที่ไม่เกี่ยวข้องกันเท่านั้น — ไม่มีอะไรในเส้นทางสร้าง broadcast/notification เรียกมันอีกแล้ว

## 4. Content lock และ optimistic locking

- **Content lock**: `title`/`message`/`metadata` บน `PATCH` ยอมรับได้ก็ต่อเมื่อ status ที่คำนวณได้*ปัจจุบัน*ของ row เป็น `scheduled` การแตะฟิลด์ใดฟิลด์หนึ่งเหล่านี้เมื่อ broadcast ออกอากาศไปแล้วจะคืน **400 `content_locked`** — เพราะผู้รับอาจอ่านไปแล้ว การเลื่อน schedule กลับไปในอนาคตก่อน (การ "ถอน") จะเปิดให้แก้เนื้อหาได้อีกครั้งอย่างถูกต้อง — เป็นสองขั้นที่ตั้งใจ ไม่ใช่ทางลัด
- **`doc_version` เป็น optimistic lock จริง** ไม่ใช่แค่ตกแต่ง schema: ทั้ง `PATCH` และ `DELETE` ต้องใช้มันและเทียบกับ row ที่เก็บไว้ก่อนเขียน (`updateMany` ใส่ `doc_version` ไว้ใน `where` เพื่อไม่ให้ request สองอันที่ถือ version เดียวกัน "ชนะ" ทั้งคู่ — ตัวที่สองจะได้ 409 ไม่ใช่การเพิ่มค่าซ้ำแบบเงียบ ๆ) นี่แก้ผลตรวจสอบเดิมก่อนปรับใหญ่ที่บอกว่า `doc_version` บนตารางนี้มีเฉพาะใน schema เพราะ "ไม่มี update endpoint... ให้ lock ตั้งแต่แรก"
- การตั้ง `end_at` เป็นอดีตเป็นวิธีที่ถูกต้องในการต่ออายุให้ broadcast ที่ live อยู่หมดทันที (นี่คือสิ่งที่ action "Expire Now" ของหน้า List ทำอยู่เบื้องหลังพอดี) — backend อนุญาตให้ทำแบบนี้ตรง ๆ ต่างจาก check ที่จะบังคับให้วันหมดอายุเป็นอนาคตเท่านั้น

## 5. Edge Case

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | ผู้รับเก่าตกค้างเข้า "All users" | เลือกผู้รับใต้ *Specific users* แล้วสลับไป *All users* ไม่ล้างมัน **เลย**; `buildSystemPayload` ใส่ `userIds` เข้าไปทุกครั้งที่มีผู้รับอยู่ ทำให้การส่งกลายเป็นแบบระบุเป้าหมายอย่างเงียบ ๆ — ขณะที่ confirm dialog ยังบอกว่า "Send to ALL users?" | ตรวจสอบใหม่กับ `BroadcastCompose.tsx` ปัจจุบัน — ไม่เปลี่ยนแปลงจากพฤติกรรมก่อนปรับใหญ่ Reset (หรือลบ badge ออก) จะล้างมัน |
| 2 | การส่งแบบ *Specific users* ที่กำหนดเวลาไว้ | **ตอนนี้ส่ง live push ได้เมื่อถึงเวลาแล้ว** `ScheduleWorker` claim row จาก `tb_notification` แล้ว emit มัน จากนั้นประทับ `pushed_at` | นี่กลับผลตรวจสอบเดิมก่อนปรับใหญ่ ("การ emit แบบ live ที่เลื่อนไว้ไม่เคยเกิดขึ้น — ไม่มี worker แบบนั้นอยู่") ตรวจสอบว่า push มาถึงภายใน ~30 วินาทีหลังเวลาที่กำหนดสำหรับผู้รับที่ออนไลน์ |
| 3 | การส่งแบบ `system_all`/`bu` ที่กำหนดเวลาไว้ | ยังไม่มี live push เลยแม้ถึงเวลาแล้ว — มีแค่การมองเห็นตอนอ่านในการ fetch ครั้งถัดไปของผู้รับ | ต่างจาก edge case 2 อันนี้**ไม่เปลี่ยนแปลง** — ตรวจสอบว่าผู้ทดสอบไม่สับสนสอง target-mode family นี้ |
| 4 | ดู แก้ไข หรือลบ broadcast แบบ `system_all`/`bu` หลังส่งไปแล้ว | **ทำได้เต็มที่แล้ว** — หน้า List และ Edit ถูกสร้างมาเพื่อสิ่งนี้โดยเฉพาะ Edit ได้ตอน `scheduled`; Expire Now ได้ตอน `active`; Delete (soft) ได้ทุกสถานะยกเว้นที่ลบไปแล้ว | แทนที่ผลตรวจสอบเดิมก่อนปรับใหญ่ "ไม่มีทางดูหรือยกเลิก broadcast ที่ส่ง/กำหนดเวลาไว้" ทั้งหมด — อย่า file ซ้ำว่าเป็นช่องว่าง |
| 5 | ดูหรือจัดการการส่งแบบ *ระบุผู้รับเจาะจง* หลังส่งไปแล้ว | **ยังทำไม่ได้เหมือนเดิม** — มันอยู่ใน `tb_notification` ซึ่งทั้ง List และ Edit ไม่เคย query เลย | โหมดเดียวที่เรื่องเดิม "fire-and-forget ไม่มี code path" ยังใช้ได้เต็มที่ |
| 6 | แก้เนื้อหาหลัง broadcast ออกอากาศไปแล้ว | 400 `content_locked` ฝั่ง server; การ์ด Content ของหน้า Edit render แบบอ่านอย่างเดียว (พร้อมคำเตือนชัดเจน) เมื่อ status ไม่ใช่ `scheduled` ทำให้ UI ปกติไม่สามารถทำแบบนี้ได้ | เข้าถึงได้แค่ผ่าน API โดยตรง หรือ race ที่ broadcast ออกอากาศระหว่างโหลดหน้ากับ Save |
| 7 | แก้ไข broadcast เดียวกันพร้อมกัน | `PATCH`/`DELETE` ตัวที่สองที่มี `doc_version` เก่าจะได้ 409; SPA แสดง toast version-conflict ที่ใช้ร่วมกันแล้ว refetch เงียบ ๆ | ตรวจสอบว่า row ที่ refetch มาสะท้อนการเปลี่ยนแปลงของผู้ชนะ ไม่ใช่ของผู้แพ้ |
| 8 | Severity แบบกำหนดเองถูกปฏิเสธ | Other… ต้องเป็น `[A-Z0-9_]+`, ≤50 ตัวอักษร, อัพเปอร์เคสอัตโนมัติตอนพิมพ์ — ตรวจสอบฝั่ง client เท่านั้น เพราะ severity ไม่ใช่ field ที่ผู้รับเห็นเลย | Server รับสตริงอะไรก็ได้ใน `metadata`; regex เป็นแค่การตกแต่งฝั่ง SPA บน field ที่ตัวมันเองก็เป็นแค่การตกแต่ง |
| 9 | List ของ BU โหลดไม่สำเร็จ / มีมากกว่า 100 รายการ | โหลดล้มเหลวแสดง error ที่ parse แล้วพร้อม Retry แบบ inline; fetch จำกัดที่ `perpage: 100` — มีผลทั้ง select BU ของ audience และ select metadata "Related Business Unit" บน Compose | ขีดจำกัดนี้มองไม่เห็นใน UI — บน cluster ขนาดใหญ่ตรวจสอบว่า BU เป้าหมายปรากฏก่อน file defect "missing BU" |
| 10 | BU code ไม่รู้จักหรือถูกลบแบบ soft ตอนส่ง | Resolve กับ BU ที่ live; ความล้มเหลวตอนนี้แสดงเป็น **404** (`COMMON_BUSINESS_UNIT_NOT_FOUND`) | แก้คำอธิบายเดิมก่อนปรับใหญ่ที่บอกว่า "500-enveloped" — ตรวจสอบ status code ใหม่ ไม่ใช่แค่ข้อความ ถ้าเขียน regression test |
| 11 | Confirmation แบบทำลายล้างของ `system_all` | โหมดเดียวที่มีปุ่ม confirm สีแดงและคำเตือน "reach every user" | ไม่เปลี่ยนแปลง |
| 12 | ส่งซ้ำ | ไม่มี unique constraint ไม่มี idempotency key — confirm สองครั้งจากสอง compose สร้างสอง row ปุ่ม Send ยังคง disable ระหว่าง request กำลังทำงาน ทำให้คลิกครั้งเดียว double-post ไม่ได้ | ไม่เปลี่ยนจากเดิม แต่ตอนนี้ลบรายการซ้ำภายหลังได้ผ่าน Delete บนหน้า List ซึ่งทำไม่ได้ก่อนปรับใหญ่ |
| 13 | Session ที่ไม่มี `.send`/`.read`/`.update`/`.delete` เรียก endpoint ที่ตรงกันโดยตรง | `PlatformPermissionGuard` ปฏิเสธด้วย 403 (ข้อความ "Missing platform permission: `<key>`" ตามที่บันทึกไว้ใน comment ของ code `BroadcastCompose.tsx` สำหรับ `broadcast.send`) ก่อนที่ request จะไปถึง micro-notification สำหรับ**ทั้งหกเส้นทาง**แล้ว ไม่ใช่แค่สอง endpoint ส่ง | ตรวจสอบทั้งสี่ key แยกกัน — งานนี้ขยาย coverage เกินกว่าการบังคับใช้แค่ตอนส่งที่ sync ครั้งก่อนตรวจสอบไว้ |
| 14 | Grant แบบ cluster เดียวเข้าถึง broadcast ของทุก cluster | Grant ของ key `broadcast.*` แบบ cluster เดียวผ่าน guard สำหรับ**ทุก**row ไม่ว่า system-wide หรือ BU ไหนก็ตาม — ไม่ใช่แค่ cluster ของผู้ได้รับ grant เอง | ความหยาบที่ตั้งใจและ document ไว้ (§1) ไม่ใช่บั๊กที่ต้อง file — ใช้เหมือนกันหมดกับ read/send/update/delete แล้ว |
| 15 | เปิด broadcast ที่ถูกลบแล้วจากรายการ | `GET .../broadcasts/:id` ยังคืนมันอยู่ (`status: "deleted"`) จึงยังดูได้แบบอ่านอย่างเดียว; ปุ่ม Edit ถูกซ่อน เนื้อหาถูกล็อกโดยธรรมชาติ | ตรวจสอบว่า row ที่ถูกลบไม่มีทาง un-delete ได้จาก UI — ไม่มี action กู้คืนเลยในโมดูลนี้ |
| 16 | ตั้งเวลาที่กำหนดไว้เป็นอดีต | Client validation ปฏิเสธ ("Scheduled time must be in the future" ตรวจกับ `Date.now()` ตอน validate); Zod request schema (`scheduled_at: z.string().datetime().optional()`) **ไม่มี check ว่าเป็นอนาคตฝั่ง server เลย** — API caller สร้าง row ที่มี `scheduled_at` เป็นอดีตได้ ซึ่งจะมองเห็นได้ทันที (ผ่าน filter `<= NOW()` อยู่แล้ว) แต่ไม่เคยถูก push แบบ live | ไม่เปลี่ยนจาก wiki ก่อนปรับใหญ่ SPA เองก็หลุด race ได้เหมือนกัน: validation รันตอนกด Send แต่ confirm dialog ไม่ re-validate จึง dialog ที่ค้างเปิดอยู่เลยเวลาที่กำหนดจะยัง submit `scheduled_at` ที่เป็นอดีตไปแล้ว |

## 6. คำแนะนำ

- **QA ทั้งสี่ key แยกกัน** ไม่ใช่แค่ `broadcast.send` เหมือนเดิม — session ที่มีแค่ `read` ควรเห็นทุกอย่างแต่กระทำไม่ได้; session ที่มี `read`+`update` (ไม่มี `send`, ไม่มี `delete`) ควรแก้/ต่ออายุให้หมดได้แต่ส่งหรือลบไม่ได้; ยืนยัน matrix ใน §2 ใช้ได้กับทุกชุดค่าผสม
- **ตรวจสอบการแยก push ตาม target-mode ใหม่ (edge case 2–3) โดยตรง** — ง่ายที่จะสับสนระหว่าง "ตอนนี้ scheduling ใช้งานได้" กับ "scheduling ใช้งานได้ทุกโหมด" ซึ่งไม่จริง: มีแค่การส่งแบบระบุผู้รับ (`system_users`) เท่านั้นที่ได้ push ที่ขับด้วย worker ใหม่
- **ทดสอบขอบเขต content-lock โดยตรง**: แก้ title ของ broadcast ที่ `scheduled` (ควรสำเร็จ) ปล่อยให้มันกลายเป็น `active` (หรือส่งอันหนึ่งทันที) แล้วลองแก้แบบเดิมอีกครั้ง (ควร 400 `content_locked` ฝั่ง server และ render แบบอ่านอย่างเดียวฝั่ง client)
- **ทดสอบ optimistic lock**: เปิด broadcast เดียวกันในสอง session, save จากอันหนึ่ง แล้วลอง save จากอีกอัน — ควรได้ 409 และ toast version-conflict ไม่ใช่การเขียนทับเงียบ ๆ
- **ทดสอบ edge case 1 โดยตรง** (ผู้รับ → สลับไป All users → confirm dialog เทียบกับ payload จริง) — ไม่เปลี่ยนแปลงจากผลตรวจสอบเดิมและยังคุ้มที่จะ file bug report ต่อ SPA ถ้ายังไม่เคย file
- **ยืนยันว่าการส่งแบบ `system_users` ไม่ปรากฏบน List หรือ Edit เลยจริง ๆ** แม้แต่สำหรับ Platform Admin — เป็นความตั้งใจ ไม่ใช่ filter ที่ต้องหาทางเลี่ยง
- **Read-state QA ต้องใช้สองผู้ใช้**: ส่ง broadcast แบบ `system_all`/`bu`, ยืนยันว่าทั้งคู่เห็นมันยังไม่อ่าน (ยังไม่มี row ของ `tb_user_broadcast_action`), ให้คนหนึ่ง mark ว่าอ่านแล้ว แล้วยืนยันว่าสถานะยังไม่อ่านของอีกคนไม่ถูกแตะ — ไม่เปลี่ยนแปลงจากการปรับใหญ่ครั้งนี้
- **`dismissed_at` และ `tb_user_broadcast_action.doc_version` ยังคงไม่ถูกใช้งานจริง** — ถูก seed/ประกาศไว้แต่ไม่มี code path ไหนใช้; อย่า file การหายไปจาก UI ว่าเป็น defect ข้อนี้แคบกว่าโน้ตเดิมของ wiki ก่อนปรับใหญ่ ที่เคยรวม `broadcast.read`, `end_at` และ `doc_version` ของตาราง broadcast เองไว้ด้วยว่าไม่ถูกใช้งาน — ทั้งสามอย่างนั้นตอนนี้เป็นของจริงและ active แล้ว (§1, §4)

**แหล่งอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard) · `src/components/nav/platformNav.ts` (รายการ nav) · `src/pages/BroadcastManagement.tsx`, `src/pages/broadcastManagement/broadcastColumns.tsx` (gate ของ row action) · `src/pages/BroadcastCompose.tsx` (`canSendSystem`/`canSend`, `<Can>`) · `src/pages/BroadcastEdit.tsx` (`contentEditable`, `<Can permission="broadcast.update">`) · `src/utils/permissions.ts` (`PERMISSIONS.BROADCAST.SEND`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` (ทั้งหก route ที่ถูก guard) · `apps/backend-gateway/src/auth/guards/platform-permission.guard.ts`, `src/auth/services/platform-permission.service.ts` (check แบบหยาบ platform-or-any-cluster ไม่เปลี่ยนตั้งแต่ PR วันที่ 2026-06-10) · `apps/micro-notification/src/notification/broadcast-admin.service.ts` (กฎ `content_locked`/`conflict`) · `apps/micro-notification/src/notification/schedule.worker.ts` (worker push เฉพาะแบบระบุผู้รับ) · `packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts`, `seed.platform-role-permission.data.ts` (สี่ key และการมอบสิทธิ์ตาม role) · `packages/error-catalog/src/catalog.ts` (`COMMON_BUSINESS_UNIT_NOT_FOUND`, 404)

**Cross-links:** [หน้าแรก Broadcasts](/th/platform/broadcasts) &nbsp;·&nbsp; [Data Model](/th/platform/broadcasts/data-model) &nbsp;·&nbsp; [UI Screens](/th/platform/broadcasts/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/th/platform/rbac/permissions) &nbsp;·&nbsp; [Business Units](/th/platform/business-units)
