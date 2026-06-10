---
title: บรอดแคสต์ (Broadcasts)
description: ภาพรวมโมดูล Broadcasts — หน้าจอเขียน push notification หน้าเดียว พร้อม target mode สามแบบ (ผู้ใช้ทั้งหมด ผู้ใช้ที่ระบุ business unit หนึ่งแห่ง), type preset แบบ SYS_/BU_ และการส่งทันทีหรือตามกำหนดเวลา แบบ fire-and-forget จาก SPA
published: true
date: 2026-06-10T16:00:00.000Z
tags: platform/broadcasts, carmen-software
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# บรอดแคสต์ (Broadcasts)

โมดูล **Broadcasts** push การแจ้งเตือนไปยังผู้ใช้แพลตฟอร์ม: ผู้ใช้ทั้งหมด, รายการที่ระบุชัด หรือสมาชิกทุกคนของ business unit หนึ่งแห่ง — ส่งทันทีหรือกำหนดเวลาไว้ในอนาคต มันคือคู่เทียบแบบ **push** ของ [News](/th/platform/news) ซึ่งเป็นแบบ **pull**: broadcast ตกถึง notification list ของผู้รับแต่ละคน (และแบบ live ผ่าน WebSocket เมื่อพวกเขาออนไลน์อยู่) ขณะที่บทความข่าวนั่งรออยู่ใน `tb_news` ให้ถูก fetch ฝั่ง SPA คือ**หน้าจอเขียน (compose) หน้าเดียว** (`/broadcasts/new`) ไม่มี route ของ list, edit หรือ cancel — เมื่อส่งออกไปแล้ว broadcast เป็นแบบ fire-and-forget จากผลิตภัณฑ์นี้

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เขียนและส่ง push notification — target mode สามแบบ (`system_all` / `system_users` / `bu`), type preset ที่ถูก resolve เป็น `SYS_*`/`BU_*`, ส่งทันทีหรือตามกำหนดเวลา (`datetime-local`, ต้องเป็นอนาคต) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA, โมดูล notification ของ backend-gateway และ micro-notification &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_broadcast_notification` + `tb_user_broadcast_action` (read state แบบ lazy); การส่งแบบกำหนดเป้าหมาย fan out ลง `tb_notification` แทน &nbsp;·&nbsp; **Endpoint:** `POST /api/notifications/broadcasts/system` และ `/bu` — สังเกตว่าเป็น `/api` **ไม่ใช่** `/api-system` &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

Broadcasts เป็นโมดูล Platform ตัวเดียวที่ surface ฝั่ง SPA เป็น**หน้าจอเดียว**: `/broadcasts/new` → `BroadcastCompose`, การ์ด Compose หนึ่งใบ ไม่มี route ของ list `/broadcasts`, ไม่มี route ของ edit, ไม่มี detail view — เป็นการเบี่ยงเบนโดยเจตนาจากรูปแบบสองหน้าจอ Management/Edit มาตรฐานของ SPA เพราะหน้าที่ของโมดูลคือ action แบบ one-shot ไม่ใช่การจัดการเรคคอร์ด อย่างไรก็ตามหน้านี้ยังคงมีองค์ประกอบมาตรฐานครบ: guard `useUnsavedChanges`, คีย์ลัด global (Ctrl/Cmd+S ส่ง, Escape รีเซ็ต), toast feedback และ Debug Sheet เฉพาะ dev ที่แสดง response ล่าสุดของ API

ฟอร์มเป็นการ์ดเดียวจากบนลงล่าง: แถบแท็บ **Target** (All users / Specific users / Business Unit), ตัวเลือกผู้รับแบบมีเงื่อนไข (`UserMultiSelect`) หรือ select ของ BU, **Title** (≤200 ตัวอักษร, ตัวนับแบบ live) และ **Message** (≤2000 ตัวอักษร, ตัวนับแบบ live), select ของ **Type** preset (Info / Warning / Critical / Maintenance / Other…) และแถบแท็บ **Send time** (Send immediately / Schedule for later พร้อม input แบบ `datetime-local`) การส่งต้องผ่าน dialog ยืนยันเสมอ โดยหัวข้อและสไตล์ของ dialog แตกต่างกันตาม target mode ดู [UI Screens](/th/platform/broadcasts/ui-screens) สำหรับ walkthrough ฉบับเต็ม

เบื้องหลัง SPA, controller ของ backend-gateway (`api/notifications/broadcasts/*`) forward ผ่าน TCP (`notifications.create`) ไปยัง **micro-notification** ซึ่งเป็นผู้เขียน row และ push แบบ live ผ่าน Socket.io ไปยังผู้ใช้ in-scope ที่ออนไลน์ การจัดเก็บคือ row ของ `tb_broadcast_notification` หนึ่งตัวต่อการส่งหนึ่งครั้ง พร้อม read state รายผู้ใช้แบบ lazy ใน `tb_user_broadcast_action` — ยกเว้นโหมด *specific users* ซึ่ง fan out เป็น row ของ `tb_notification` หนึ่งตัวต่อผู้รับแทน ดู [Data Model](/th/platform/broadcasts/data-model)

## 2. บริบททางธุรกิจ

News และ Broadcasts แบ่งปัญหาการประกาศกันตามความเร่งด่วน บทความข่าวเป็นเนื้อหาแบบ **pull**: มันนั่งอยู่หลัง public feed จนกว่า client จะ render มัน เหมาะกับเอกสารนโยบายและอัพเดทแบบ long-form และแก้ไขหรือ archive ภายหลังได้ broadcast นั้น**ขัดจังหวะ**: มันปรากฏใน notification bell ของผู้ใช้ in-scope ทุกคน (และเป็น socket event แบบ live สำหรับผู้ใช้ที่ออนไลน์) ทันทีที่ถูกส่ง — และแก้ไขหรือเรียกคืนภายหลังไม่ได้ use case ตามแบบฉบับเป็นเชิงปฏิบัติการ: คำเตือนปิดปรับปรุงตามกำหนด (`SYS_MAINTENANCE`), ประกาศ incident (`SYS_CRITICAL`) และประกาศรายโรงแรมไปยังพนักงานของ business unit หนึ่งแห่ง (`BU_INFO`)

การกำหนดเวลา (scheduling) ให้ operator เตรียมประกาศปิดปรับปรุงไว้ล่วงหน้าได้: row ของ broadcast ที่กำหนดเวลาไว้ถูกสร้างทันทีแต่จะอยู่นอก list ของผู้รับจนกว่า `scheduled_at` จะผ่านไป (เป็นการ filter ตอนอ่าน — **ไม่มี delivery cron** เข้ามาเกี่ยวข้องสำหรับ row ของ broadcast) ข้อพึงระวังสองข้อที่ QA ควรรู้ตั้งแต่ต้น: side-effect ของการ fan-out อีเมล (เมื่อ SMTP ถูกเปิดใช้บน micro-notification) ทำงานตอน **create** แม้กับการส่งแบบกำหนดเวลา และโหมด *specific users* ไม่เคารพการกำหนดเวลาเลยบนเส้นทางอ่าน — รายละเอียดอยู่ใน [Permissions](/th/platform/broadcasts/permissions) §3–§4

## 3. แนวคิดสำคัญ

- **Target mode** — `BroadcastTargetMode = 'system_all' | 'system_users' | 'bu'` สองตัวแรกใช้ `POST .../broadcasts/system` ร่วมกัน (array `userIds` แบบระบุชัดเปลี่ยน "ทุกคน" เป็น "ผู้ใช้เหล่านี้"); `bu` post ไป `.../broadcasts/bu` พร้อม `bu_code` — **code** ของ BU ที่มนุษย์อ่านได้ ไม่ใช่ UUID; micro-notification resolve มันเป็น `tb_business_unit.id` แล้วจัดเก็บค่านั้นเป็น `scope_id`
- **การ resolve type** — SPA resolve ตัว preset ฝั่ง client: `SYS_<PRESET>` สำหรับสองโหมด system, `BU_<PRESET>` สำหรับโหมด BU (เช่น Maintenance → `SYS_MAINTENANCE` หรือ `BU_MAINTENANCE`) การเลือก **Other…** เผย input ของ custom type (`[A-Z0-9_]+`, ≤50 ตัวอักษร, อัพเปอร์เคสอัตโนมัติ) ที่ถูกส่งแบบ verbatim **โดยไม่มี prefix** หาก `type` ถูกละไว้ทั้งหมด (เฉพาะ caller ของ API เท่านั้น — SPA ส่งมันเสมอ) gateway จะ default เป็น `SYS_INFO`/`BU_INFO`
- **หนึ่ง row, read state แบบ lazy** — broadcast แบบ system-wide หรือแบบ BU คือ row ของ `tb_broadcast_notification` ตัวเดียว; ใครอ่านแล้วอยู่ใน `tb_user_broadcast_action` ซึ่งถูกสร้างแบบ lazy ตอน action แรก แบบแผนนี้แทนที่ดีไซน์ fan-out-on-write รุ่นก่อนหน้า (comment ของ schema document การ migrate ไว้) เส้นทาง *specific users* ยังคงใช้ fan-out แบบ legacy: row ของ `tb_notification` หนึ่งตัวต่อผู้รับ
- **การกำหนดเวลา = การมองเห็นตอนอ่าน** — broadcast ที่ `scheduled_at` เป็นอนาคตมีอยู่ทันทีแต่ถูก filter ออกจากทุก list query (`scheduled_at IS NULL OR scheduled_at <= NOW()`) จนกว่าเวลาจะผ่านไป; การ push ผ่าน socket แบบ live ถูกข้ามสำหรับการส่งแบบกำหนดเวลาและไม่มีวันเกิดขึ้นภายหลัง (ผู้รับเห็นมันตอน fetch list ครั้งถัดไป)
- **Fire-and-forget** — ไม่มี API ที่ไหนเลย (gateway หรือ micro-notification) ที่ list, update, cancel หรือ delete broadcast read query เคารพ `deleted_at` แต่ไม่มี code path ใดเคยเขียนมัน — การถอน broadcast ที่ส่งผิดหรือกำหนดเวลาผิดเป็นการดำเนินการบนฐานข้อมูลด้วยมือในวันนี้

## 4. บทบาทและ Persona

permission key ตัวเดียว gate ทุก surface ผ่าน [Platform RBAC](/th/platform/rbac) (`broadcast.send`, seed ใน `seed.platform-permission.ts` คู่กับ `broadcast.read` ที่ SPA ไม่ได้ใช้):

| Surface | Gate | Key |
|---|---|---|
| route `/broadcasts/new` | `PrivateRoute` | `broadcast.send` |
| sidebar "Send Broadcast" (กลุ่ม Content, ไอคอน Megaphone) | nav filter ของ `Layout.tsx` | `broadcast.send` |
| ปุ่ม Send (footer ของฟอร์ม) | `<Can>` | `broadcast.send` |

ต่างจากโมดูลแบบ CRUD ตรงที่ไม่มีการแบ่ง read/create/update/delete — การส่งเป็นการดำเนินการเดียวของโมดูล สังเกตว่า backend บังคับใช้**เฉพาะ authentication** (Keycloak bearer) บนสอง endpoint นี้; key `broadcast.send` ไม่ถูกตรวจสอบที่ไหนเลยฝั่ง server เมทริกซ์ฉบับเต็ม, quirk ของการ gate แท็บภายใน component และ semantics การส่งมอบราย target mode อยู่ใน [Permissions](/th/platform/broadcasts/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [News](/th/platform/news) — sibling ฝั่ง pull: เนื้อหาที่ถูกเขียนพร้อม lifecycle และ public feed เทียบกับ push แบบ one-shot ทันทีของ Broadcasts ใช้ Broadcasts เพื่อขัดจังหวะ ใช้ News เพื่อแจ้งข้อมูล
- [Business Units](/th/platform/business-units) — โหมด BU กำหนดเป้าหมายหนึ่ง unit ด้วย `code`; หน้าจอเขียนโหลดตัวเลือก select ของมันจาก API ของโมดูลนั้น (เฉพาะ BU ที่ active) และ micro-notification resolve ตัว code กับ row ของ `tb_business_unit` ที่ live อยู่ ณ เวลาส่ง
- [Users](/th/platform/users) — โหมด *specific users* ค้นหา user registry ผ่าน `UserMultiSelect`; ผู้รับถูกส่งเป็น UUID ของ `tb_user.id`
- [Platform RBAC](/th/platform/rbac) — กำหนดและ resolve key `broadcast.send` ที่ gate surface ของ SPA

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route guard ของ `/broadcasts/new` (`broadcast.send`)
- `../carmen-platform/src/components/Layout.tsx` — รายการ sidebar "Send Broadcast" (กลุ่ม Content)
- `../carmen-platform/src/pages/BroadcastCompose.tsx` — หน้าจอเขียน: แท็บ, การ validate, ตัวสร้าง payload, dialog ยืนยัน, คีย์ลัด
- `../carmen-platform/src/components/UserMultiSelect.tsx` — การค้นหาผู้ใช้แบบ debounce พร้อมการเลือกแบบ badge
- `../carmen-platform/src/services/broadcastService.ts` — การเรียก POST สองตัว; `src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, payload type สองตัว, `UserOption`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_broadcast_notification` (บรรทัด 357), `tb_user_broadcast_action` (บรรทัด 388), `tb_notification` (บรรทัด 316)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — `pushSystemBroadcast` / `pushBuBroadcast` (KeycloakGuard, การ forward ผ่าน TCP)
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/` — `notification.controller.ts` (dispatch ของ create, live emit), `notification.service.ts` (การเขียน row, การ resolve scope, filter ตอนอ่าน, การ fan-out อีเมล)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/broadcasts/data-model) — ตาราง field ของ `tb_broadcast_notification` และ `tb_user_broadcast_action`, ทางแยกของการส่งแบบกำหนดเป้าหมายลง `tb_notification`, คลังศัพท์ของ type และความแตกต่างจาก payload type ของ SPA
- [UI Screens](/th/platform/broadcasts/ui-screens) — หน้าจอเขียนหน้าเดียว: แท็บ target, ตัวเลือกผู้รับ, ตัวนับ, flow ส่ง/กำหนดเวลา, dialog ยืนยัน และคีย์ลัด
- [Permissions](/th/platform/broadcasts/permissions) — เมทริกซ์ gate แบบ key เดียว, ข้อพึงระวังการบังคับใช้ฝั่ง client เท่านั้น, semantics การส่งมอบราย target mode และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
