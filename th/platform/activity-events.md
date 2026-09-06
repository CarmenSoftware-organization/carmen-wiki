---
title: บันทึกกิจกรรม (Activity Events)
description: หน้า explorer ของ UI telemetry แบบรายอีเวนต์ที่ /activity-events — ทุกตัวกรองและคอลัมน์ สิทธิ์ activity_event.detail ที่ใช้ร่วมกัน (แต่ไม่ซ้ำกัน) กับ Usage Analytics และเหตุผลที่หน้านี้ไม่ใช่ audit trail ของ activity_log
published: true
date: '2026-09-06T02:14:23.000Z'
tags: book/platform, activity-events
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# บันทึกกิจกรรม (Activity Events)

**Activity Events** คือหน้าเดียว `ActivityEventManagement` ที่เข้าถึงได้ที่ route **`/activity-events`** — route กับ slug ของโมดูลนี้ตรงกัน ต่างจากโมดูลพี่น้อง มันคือคู่แบบรายแถวของ [Usage Analytics](/th/platform/usage-analytics) — ในขณะที่แดชบอร์ดนั้นแสดงตัวเลขสรุป หน้านี้แสดงรายการ UI telemetry แบบรายแถว (หนึ่งแถวต่อหนึ่งการคลิกหรือการเปิดหน้า) จากตารางเดียวกัน คือ `tb_activity_event` พร้อมตัวกรอง การเรียงลำดับ การ export CSV และมุมมองรายละเอียดเต็มต่อแถว

**นี่ไม่ใช่ audit trail** หน้าจอที่มีชื่อคล้ายกัน — ปุ่ม "View History" บน Clusters, Business Units, Users และ Report Templates — อ่านจากตารางที่ต่างกันโดยสิ้นเชิง (`tb_activity`, resource key `activity_log`) ซึ่งบันทึกว่าใครเปลี่ยนฟิลด์ไหนของเรคคอร์ดระดับแพลตฟอร์ม พร้อมค่าก่อน/หลัง หน้านี้ไม่มีความเกี่ยวข้องกับฟีเจอร์นั้นเลย ดูรายละเอียดเต็มที่ §2 (draft ก่อนหน้าของหน้านี้เคยปนสองระบบนี้เข้าด้วยกัน — แก้ไขแล้วในเวอร์ชันนี้)

## 1. ภาพรวม

หน้านี้ (`ActivityEventManagement.tsx` 434 บรรทัด อ่านแบบเต็ม) render จากบนลงล่างดังนี้:

1. page header พร้อม subtitle "Per-event UI telemetry — who clicked what, on which page, and when" (`pages.activityEvents.subtitle`, `src/i18n/en.ts:4143`) และปุ่ม **Export CSV** (ปิดใช้งานระหว่างโหลด)
2. แถบตัวกรอง: ช่องค้นหาแบบ free-text (debounce 400ms), ตัวเลือกช่วงวันที่ใช้ร่วมกับ Usage Analytics (`DateRangeFilter`, ค่าเริ่มต้น 7 วันล่าสุดผ่าน `presetRange(7)`) และปุ่ม **Filters** ที่เปิด side sheet
3. sheet ตัวกรอง: Event type (`click`/`page_view`, dropdown — ไม่ใช่พิมพ์เอง เพื่อกันพิมพ์ผิดแล้วไม่พบ event โดยไม่รู้สาเหตุ), dropdown Business Unit, dropdown Application, ช่อง free-text User (User ID), ช่อง free-text Page path, และช่อง free-text Session ID
4. chip ตัวกรองที่ใช้งานอยู่ใต้แถบ หนึ่งอันต่อตัวกรองที่ไม่ว่าง แต่ละอันเคลียร์ได้แยกกัน
5. banner error ที่แสดงเฉพาะตอน fetch ล้มเหลวเท่านั้น
6. ตารางข้อมูล (คอลัมน์ดูที่ §3.1) พร้อมการแบ่งหน้าและเรียงลำดับฝั่ง server หรือ `TableSkeleton`/`EmptyState` แทนที่ระหว่างโหลดหรือเมื่อไม่มีแถวที่ตรงเงื่อนไข
7. เฉพาะ build แบบ development (`process.env.NODE_ENV === 'development'`) จะมี `DevDebugSheet` แสดง response ดิบของ `GET /api-system/platform/analytics/records` (`ActivityEventManagement.tsx:423-428`)

ทุกแถวบนหน้านี้คือ `ActivityEvent` หนึ่งตัว (`src/types/index.ts:1367-1386`) — รายการฟิลด์ครบทั้งหมด ใครเป็นคนเขียนแต่ละฟิลด์ และเก็บไว้นานแค่ไหน อยู่ในหน้าย่อย [Data Model](/th/platform/activity-events/data-model) ไม่ขอพูดซ้ำที่นี่

## 2. บริบททางธุรกิจ — โมดูลนี้คืออะไร และไม่ใช่อะไร

หน้าจอนี้มีอยู่เพื่อให้ operator ที่ถือสิทธิ์แคบกว่าในสองสิทธิ์ analytics ตรวจดูแถว telemetry แบบ *รายบุคคล* ได้ — session ไหนคลิก element ไหน บนหน้าไหน เวลาใด — ไม่ใช่แค่ยอดรวมที่ `/analytics` แสดง มันถูก gate ด้วยสิทธิ์อีกคีย์หนึ่งที่เข้มกว่าโดยตั้งใจ (§4) เพราะแถวดิบสามารถระบุตัวตนการกระทำของผู้ใช้คนใดคนหนึ่งได้ ซึ่งตัวเลขสรุปทำไม่ได้

**resource สองตัวที่ไม่เกี่ยวข้องกันแชร์คำว่า "activity"** ยืนยันตรงจาก source ไม่ใช่จากคอมเมนต์เพียงอย่างเดียว:

| | `activity_event` (โมดูลนี้) | `activity_log` (View History, ที่อื่น) |
| --- | --- | --- |
| ตาราง | `tb_activity_event` (`schema.prisma:1489-1509`) | `tb_activity` (`schema.prisma:907-929`) |
| รูปร่าง | `session_id`, `event_type` (`click`/`page_view`), `page_path`, `element_id`/`element_text`, `props`, `client_ts`/`server_ts` — UI telemetry | `action`, `entity_type`/`entity_id`, `actor_id`, `old_data`/`new_data` แบบ JSON — เรคคอร์ดประวัติการเปลี่ยนแปลง |
| ใครเขียน | client ส่ง batch telemetry เข้ามาเอง (§3.4) | จุดเรียก audit-logging แบบระบุเอง (login/logout, เปลี่ยน avatar, และ handler CRUD ของแต่ละโมดูล) |
| คีย์สิทธิ์ | `activity_event.read` (แดชบอร์ดสรุป), `activity_event.detail` (หน้านี้) | `activity_log.read` (timeline), `activity_log.detail` (ค่าฟิลด์ก่อน/หลัง) |
| หน้าจอ | `/analytics`, `/activity-events` | "View History" บน `BusinessUnitManagement`, `ClusterManagement`, `UserManagement`, `ReportTemplateEdit` และอื่น ๆ |

permission catalog ระบุความแตกต่างนี้ไว้ตรง ๆ ในสี่แถวติดกัน (`seed.platform-permission.data.ts:95-100`, `../carmen-turborepo-backend-v2`):

| Resource | Action | คำอธิบายใน catalog |
| --- | --- | --- |
| `activity_event` | `read` | "View the Usage Analytics dashboard (aggregate figures only)" |
| `activity_event` | `detail` | "View raw UI telemetry events, including which user clicked what" |
| `activity_log` | `read` | "View the change history timeline of a platform record (who changed it, when)" |
| `activity_log` | `detail` | "View the old and new value of each changed field on a platform record" |

มีคอมเมนต์ในซอร์สคั่นอยู่ระหว่างแถวของสอง resource นี้พอดี: "Record audit trail (`tb_activity`) — คนละตารางกับ `activity_event` ข้างบนซึ่งเป็น UI telemetry" (บรรทัด 97) สิ่งนี้ถูกยืนยันอย่างอิสระอีกชั้นด้วยวิธีที่ทั้งสองตารางถูกต่อสายไว้ ไม่ใช่แค่จากคอมเมนต์: `LogEventsModule` ซึ่งเป็นโมดูล audit-logging ทั่วไปที่คอมเมนต์ของตัวเองระบุว่ามีไว้สำหรับ "manual audit logging (login/logout, avatar, etc.)" เขียนลง `tb_activity` นั้น **ยกเว้น** `tb_activity`, `tb_activity_event`, และ `tb_activity_event_daily` ออกจาก list ของโมเดลที่มันติดตามโดยทั่วไปอย่างชัดเจน (`apps/micro-business/src/app.module.ts:211-222`, array `excludeModels`) — สองระบบนี้ถูกกันไม่ให้ป้อนเข้าหากันโดยระบุชื่อตรง ๆ ในโค้ดที่ไม่เกี่ยวอะไรกับสตริงสิทธิ์ของหน้าไหนเลย

ไม่มีเอกสารเชิงแนวคิดของโมดูลนี้ใน `../carmen/docs` มาก่อน (ค้นด้วยคำว่า `activity_event`, `activity event`, `ui telemetry`, `activity-events` — ไม่พบ) ทุกอย่างในหน้านี้และหน้าย่อย data model มาจากการอ่าน implementation ของ `../carmen-platform`, `../carmen-turborepo-backend-v2`, `../carmen-inventory-frontend-react`, และ `../micro-cronjobs` โดยตรง

## 3. หน้าจอ Explorer

### 3.1 คอลัมน์และการเรียงลำดับ

| คอลัมน์ | ฟิลด์ | เรียงได้ | หมายเหตุ |
| --- | --- | --- | --- |
| Time | `server_ts` | ได้ | รูปแบบ `YYYY-MM-DD HH:MM:SS` ตามเวลาของเบราว์เซอร์ |
| User | `user_name` (หรือ 8 ตัวอักษรแรกของ `user_id` ถ้า resolve ชื่อไม่ได้), `user_email` แสดงด้านล่างตัวเล็ก | ไม่ได้ | `user_name`/`user_email` resolve ฝั่ง server ไม่ได้เก็บอยู่ในแถว (ดู data model) |
| BU | `bu_code` | ไม่ได้ | `-` เมื่อไม่มีค่า |
| Type | badge `event_type` | ได้ | |
| Page | `page_path` แบบ monospace ตัดสั้นพร้อม tooltip | ได้ | |
| Element | `element_id` แบบ monospace ตัดสั้น; tooltip แสดง `element_text` หรือ `element_id` | ไม่ได้ | `-` สำหรับแถว `page_view` ซึ่งไม่มี element เลย |
| App | `app_name` | ไม่ได้ | ซ่อนบน layout แบบการ์ด/มือถือ (`meta: { card: 'hidden' }`) |
| (actions) | — | ไม่ได้ | ไอคอนรูปตาเปิด detail sheet ของแถวนั้น |

คอลัมน์ที่เรียงได้สี่ตัวตรงกับ whitelist การเรียงของ backend เป๊ะ (`SORTABLE`, `activity-event.service.ts:25-30`, `../carmen-turborepo-backend-v2`): `server_ts`, `client_ts`, `page_path`, `event_type` — ยกเว้น `client_ts` ไม่มีคอลัมน์ตารางเลยบนหน้านี้ (ปรากฏแค่ใน detail sheet, §3.3) จึงไม่มีทางเรียงผ่าน UI ได้ ทั้งที่ backend รองรับ ค่า `sort` ที่ไม่รู้จักหรือไม่อยู่ใน whitelist จะตกไปใช้ `server_ts:desc` ฝั่ง server เสมอ (`activity-event.service.ts:275-277`); ค่าที่เท่ากันจะตัดสินด้วย `id` ในทิศทางเดียวกันเสมอ (`activity-event.service.ts:284` คอมเมนต์ของตัวเอง: ทุกแถวที่ insert ในหนึ่ง batch มีค่า `server_ts` เท่ากันเป๊ะ เพราะค่า default `now()` ของ Postgres คำนวณที่เวลาเริ่ม transaction ไม่ใช่ต่อแถว จึง `server_ts` เพียงอย่างเดียวรับประกันขอบเขตการแบ่งหน้าที่เสถียรไม่ได้)

การคลิกหัวคอลัมน์จะวนสถานะ เรียงจากน้อยไปมาก → มากไปน้อย → ไม่เรียง; พอถึง "ไม่เรียง" ระบบจะรีเซ็ต query กลับไปเป็น `server_ts:desc` และ remount ตาราง (bump `sortResetKey`, `ActivityEventManagement.tsx:223-226`) เพื่อให้ลูกศรบนหัวตารางกับลำดับแถวจริงตรงกันเสมอ — `DataTable` เองไม่มีวิธี controlled สำหรับสถานะ "ไม่เรียง" คอมโพเนนต์จึงถูกรีเซ็ตโดยตั้งใจ แทนที่จะปล่อยให้ลูกศรค้างผิดสถานะ

### 3.2 ตัวกรอง การค้นหา และการแบ่งหน้า

- **Search** จับคู่ `page_path`, `element_id`, หรือ `element_text` ผ่าน SQL `ILIKE '%term%'` (`buildWhere()`, `activity-event.query.ts:26-31`) — ยืนยันจากตัวสร้าง query โดยตรง ไม่ใช่แค่จากคอมเมนต์ของ endpoint
- **Event type**, **Business Unit**, และ **Application** เป็น dropdown (ตัวเลือก BU/Application โหลดครั้งเดียว จำกัดที่ 100 แถวเท่ากันทั้งคู่ ใช้ hook `useAnalyticsFilterOptions` ตัวเดียวกับ Usage Analytics)
- **User ID**, **Page path**, และ **Session ID** เป็น free-text; `page_path` และ `session_id` จับคู่แบบ **ตรงตัวเป๊ะ** (`page_path = ...`, `session_id = ...`) ไม่ใช่แบบ substring เหมือนช่อง Search
- ตัวกรองข้อความทั้งสี่ตัว (search, page path, session ID, user ID) debounce 400ms ก่อนยิง fetch และรีเซ็ตกลับหน้า 1 ในจังหวะเดียวกันกับตอนค่า debounce นิ่งจริง เพื่อไม่ให้ยิง fetch ทิ้งหนึ่งครั้งด้วยตัวกรอง/หน้าที่ยังไม่ตรงกัน (`ActivityEventManagement.tsx:92-103`)
- ขนาดหน้าเริ่มต้นที่ 25 และจำค่าไว้ต่อเบราว์เซอร์ผ่าน `localStorage` (`perpage_activity_events`)
- ตัวกรองทุกตัวที่นี่ทำให้ขอบเขตที่ถูกจำกัดฝั่ง server อยู่แล้วแคบลงเท่านั้น (§4.3) — ตัวกรองย่อลงได้อย่างเดียว ไม่ทำให้เห็นกว้างขึ้น

### 3.3 รายละเอียดแถวและการ export CSV

การคลิกไอคอนรูปตาของแถวจะเปิด `EventDetailSheet` (`src/pages/activityEvents/EventDetailSheet.tsx` เต็ม 78 บรรทัด) ซึ่งแสดงทุกฟิลด์ที่ response ของ explorer ดิบมีสำหรับแถวนั้น: เวลาที่ server บันทึก, เวลาที่ client รายงาน, ประเภท, ผู้ใช้ (ชื่อ/id), อีเมล, BU, แอปพลิเคชัน, domain, page path, element id, element text, session id, event id, ออบเจกต์ `props` ดิบ (ผ่าน `JsonViewer`), และสตริง `user_agent` ดิบ — พร้อมปุ่ม **"View this entire session"** ที่เปิดตารางใหม่โดยกรองเฉพาะ `session_id` นั้น (เคลียร์ตัวกรอง page path ก่อน เพราะถ้ายังกรองตาม page อยู่ มุมมองระดับ session จะซ่อนกิจกรรมส่วนใหญ่ของ session นั้นไปแบบเงียบ ๆ)

**การ export CSV** (`handleExport`, `ActivityEventManagement.tsx:228-241`) เขียนเฉพาะคอลัมน์ที่เห็นในตารางบวกอีเมลผู้ใช้ — `server_ts` (ป้าย "Server time"), `user_name`, `user_email`, `bu_code`, `event_type`, `page_path`, `element_id`, `app_name` — **ไม่รวม** `session_id`, `event_id`, `client_ts`, `domain`, `user_agent`, หรือ `props`; หกฟิลด์นี้เห็นได้เฉพาะใน detail sheet เท่านั้น ไม่เคยอยู่ใน export ใช้ helper `generateCSV`/`downloadCSV` ตัวเดียวกับ Usage Analytics รวมถึงการ neutralize ป้องกัน formula-injection แบบเดียวกันทุกเซลล์ (ดู §3.3 ของหน้านั้นสำหรับ regex ที่แน่นอนและกรณีเครื่องหมายลบ ซึ่งใช้ผลเหมือนกันทุกประการที่นี่)

### 3.4 ใครเป็นคนเขียนแถวเหล่านี้

ทั้งหน้านี้และ `carmen-platform` เองไม่ได้เขียนแถว `tb_activity_event` เลย — ยืนยันด้วยการ grep `../carmen-platform/src` หาการเรียก ingestion endpoint หรือ tracking client ใด ๆ ไม่พบเลยสักที่ แถวที่หน้านี้อ่านถูกเขียนโดยแอปพลิเคชัน *อื่น*: `lib/analytics.ts` ของ `../carmen-inventory-frontend-react` (เต็ม) ตัว batcher telemetry คลิก/page-view ที่ทำงานเฉพาะภายใน shell ที่ล็อกอินแล้วของแอปนั้น (`components/analytics-bridge.tsx`, mount ใน `RootLayout`/`ProtectedShell` จึงไม่มีอะไรถูก queue ก่อนล็อกอิน) มันดัก click ทุกครั้งบน `[data-track], button, a, [role="button"]` และทุกการเปลี่ยน route, batch สูงสุด 50 event ต่อ request (คิวจำกัดที่ 500, flush ทุก 10 วินาที, เมื่อคิวถึง 20 รายการ, หรือทันทีด้วย `keepalive` ตอนแท็บถูกซ่อน) แล้ว POST ไปที่ `/api/analytics-events` — ส่งต่อผ่าน `POST api/analytics-events` ของ gateway (`analytics-events.controller.ts`, `../carmen-turborepo-backend-v2`) ที่ guard ด้วย `KeycloakGuard` และ `AppIdGuard('analyticsEvent.create')` เข้าสู่ `ActivityEventService.createBatch()` (`../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts:82-112`) ซึ่ง insert ผ่าน `createMany({ skipDuplicates: true })` โดยใช้ `event_id` ที่ client สร้างเป็น key เพื่อความ idempotent เมื่อ retry รายละเอียดครบทุกฟิลด์ — รวมถึงฟิลด์ไหนที่ client กำหนดได้และฟิลด์ไหนถูกประทับฝั่ง server — อยู่ที่หน้า [Data Model](/th/platform/activity-events/data-model)

## 4. บทบาทและสิทธิ์

### 4.1 คีย์ที่ใช้ gate และความต่างจากแดชบอร์ด

| ชั้น | หน้านี้ (`/activity-events`) |
| --- | --- |
| แถว nav ใน sidebar | `permission: 'activity_event.detail'`, `feature: 'activity_events'`, `groupKey: 'navGroup.analytics'` — ไม่มี `superAdminOnly` (`platformNav.ts:33`) |
| Route (`PrivateRoute`) | `requiredPermission="activity_event.detail"` `feature="activity_events"` (`App.tsx:483-489`) |
| Backend endpoint | `GET /api-system/platform/analytics/records` — `@RequirePlatformPermission('activity_event.detail')` (`platform-analytics.controller.ts:180-182`) |

`activity_event.detail` เป็น **คีย์ที่ต่างกัน** จาก `activity_event.read` ซึ่ง gate แค่แดชบอร์ดสรุป `/analytics` — ผู้เรียกอาจถือคีย์ใดคีย์หนึ่งได้โดยไม่มีอีกคีย์ การเปรียบเทียบสองคีย์แบบเต็ม (แต่ละคีย์ให้สิทธิ์อะไร ตาราง gate สามชั้น การ drill-down ที่ห่อด้วย `<Can>` จาก Top Pages กลไกการจำกัดขอบเขตตาม cluster ฝั่ง backend และการมอบสิทธิ์ตาม role bundle) ถูกบันทึกไว้แบบละเอียดที่ [Usage Analytics §4](/th/platform/usage-analytics) แทนที่จะพูดซ้ำที่นี่ เพราะทั้งสองหน้าจอใช้ guard stack เดียวกันเป๊ะและใช้ฟังก์ชัน `resolveAllowedClusterIds()` ตัวเดียวกัน — ต่างกันแค่คีย์ที่ส่งเข้าไป (`ACTIVITY_EVENT_DETAIL` ที่นี่ เทียบกับ `ACTIVITY_EVENT_READ` ที่หน้านั้น, `analytics-scope.ts:7-13`)

### 4.2 ความหมายของ `activity_event.detail` เพียงลำพังสำหรับหน้านี้

การถือ `activity_event.detail` เปิดหน้านี้ได้เลย — ผู้เรียกไม่จำเป็นต้องมี `activity_event.read` ด้วย ตาม role bundle ที่ seed ไว้ (`seed.platform-role-permission.data.ts:11-52`, `../carmen-turborepo-backend-v2`, อ่านซ้ำอย่างอิสระสำหรับหน้านี้ — ดู §6): **Platform Admin** ถือทั้งสองคีย์ผ่าน `activity_event.*` (บรรทัด 14); **Support Manager** ถือแค่ `activity_event.read` (บรรทัด 40) จึงเปิดหน้านี้ไม่ได้เลย (เจอ `<Forbidden />` ที่ route และไม่มีแถว nav ให้เห็นด้วยซ้ำ); **Support Staff** และ **Security Officer** ไม่ถือคีย์ไหนเลย ผลนี้ตรงกับที่ [Usage Analytics §4.4](/th/platform/usage-analytics) บันทึกไว้สำหรับสองคีย์เดียวกันทุกประการ ไม่มีจุดที่ต่างกัน

### 4.3 ชุดทดสอบ e2e: ไม่มี

`../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) ไม่มีโฟลเดอร์ `activity-events` เลย — ยืนยันโดย list โครงสร้าง repository ตรง ๆ ตรงกับ source map ของ Task 1 ที่ระบุว่าโมดูลนี้ไม่มี e2e รองรับ ทุกข้อความเชิงพฤติกรรมบนหน้านี้และหน้าย่อย data model มาจากการอ่าน implementation ของ `../carmen-platform`, `../carmen-turborepo-backend-v2`, `../carmen-inventory-frontend-react`, และ `../micro-cronjobs` ไม่ใช่จาก spec ที่รันได้จริง

## 5. โมดูลที่เกี่ยวข้อง

- [Usage Analytics](/th/platform/usage-analytics) — โมดูลพี่น้องที่เป็นแดชบอร์ดสรุปที่ `/analytics` gate ด้วย `activity_event.read`; เป็นเจ้าของการอธิบายสิทธิ์/guard/การจำกัดขอบเขตตาม cluster แบบเต็มที่ §4 ของหน้านี้อ้างถึง
- [Platform RBAC](/th/platform/rbac) — permission catalog และนิยาม role bundle ที่อ้างถึงใน §2 และ §4
- [Business Units](/th/platform/business-units) และ [Applications](/th/platform/applications) — เป็นแหล่งข้อมูลของ dropdown ตัวกรอง BU และ Application (§3.2) หน้านี้ไม่ได้เป็นเจ้าของ list ทั้งสอง
- [Cronjobs](/th/platform/cronjobs) — หน้าจัดการ scheduled job ของแพลตฟอร์มเอง ซึ่ง (ตามที่ `platform_cronjobs.service.ts` ของ `../carmen-turborepo-backend-v2` อ่านและเขียนตาราง `"CRONJOBS"."Cronjob"` เดียวกัน) เป็น store เดียวกับที่เก็บนิยามงาน retention และ rollup ที่บันทึกไว้ในหน้า [Data Model](/th/platform/activity-events/data-model)

## 6. แหล่งอ้างอิง

path ทั้งหมดด้านล่างเป็น `../carmen-platform` (Platform admin SPA, HEAD `157a65e`, 2026-09-04) เว้นแต่จะระบุเป็นอย่างอื่น

- `../carmen-platform/src/pages/ActivityEventManagement.tsx` (เต็ม 434 บรรทัด) — ตัวหน้า: ตัวกรอง (`fetchEvents`), คอลัมน์, handler การเรียงลำดับ/แบ่งหน้า, การ export CSV, panel debug
- `../carmen-platform/src/pages/activityEvents/EventDetailSheet.tsx` (เต็ม 78 บรรทัด) — detail sheet รายแถวและปุ่ม "View this entire session"
- `../carmen-platform/src/services/analyticsService.ts` — `getEvents()` ใช้ร่วมกับ Usage Analytics
- `../carmen-platform/src/types/index.ts:1367-1386` — type `ActivityEvent` ฝั่ง frontend
- `../carmen-platform/src/App.tsx:483-489` — การลงทะเบียน route `/activity-events`
- `../carmen-platform/src/components/nav/platformNav.ts:32-33` — สองแถว nav ของ Analytics ที่อยู่ติดกัน
- `../carmen-platform/src/i18n/en.ts:4142-4191` และ `src/i18n/th.ts:3151` เป็นต้นไป — ข้อความหน้าที่ยกมาใน §1/§3
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/platform-analytics.controller.ts:147-259` (HEAD `937cf5ac4`, 2026-09-06) — route `GET /records`, guard ของมัน, และคอมเมนต์กับดักตัวบล็อกโฆษณาที่คุม URL (`analytics/records` เท่านั้น ห้ามเป็น `analytics/event*`)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/analytics-scope.ts` (เต็ม) — `ACTIVITY_EVENT_DETAIL`, `resolveAllowedClusterIds()`
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts:82-112,246-347` — `createBatch()` (เส้นทาง insert, §3.4) และ `findEvents()` (คอมเมนต์เรื่องตัดสินความเท่ากันตอนเรียงลำดับ, การ resolve ชื่อผู้ใช้/แอป)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.query.ts` (เต็ม) — เงื่อนไข `ILIKE` ของ `buildWhere()`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.controller.ts` (เต็ม) — `POST api/analytics-events`, guard ของมัน (`KeycloakGuard`, `AppIdGuard('analyticsEvent.create')`), และเพดาน 100 event
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.service.ts` (เต็ม) — ตัว proxy จาก gateway ไป microservice ที่เรียก `ActivityEvents.createBatch`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/activity-event/activity-event.dto.ts` (เต็ม) — schema validate ด้วย Zod (เพดานความยาวแต่ละฟิลด์, เพดาน batch 1–100 event) ที่บันทึกไว้ในหน้า data model
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/extract_client_context.ts` (เต็ม) — วิธีประทับ `app_id`/`domain`/`user_agent` ฝั่ง server จาก header ที่บันทึกไว้ในหน้า data model
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:907-929,1479-1529` — `tb_activity` และ `tb_activity_event`/`tb_activity_event_daily` อ่านคู่กันสำหรับตารางใน §2
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts:93-101` — สี่แถว permission catalog ที่ยกมาใน §2
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-role-permission.data.ts:11-52` (เต็ม) — การมอบสิทธิ์ตาม role bundle ตรวจซ้ำอย่างอิสระสำหรับ §4.2
- `../carmen-turborepo-backend-v2/apps/micro-business/src/app.module.ts:211-222` — `excludeModels` ของ `LogEventsModule` การยืนยันอิสระที่ยกมาใน §2
- `../carmen-inventory-frontend-react/lib/analytics.ts` (เต็ม, HEAD `72d6cd340`, 2026-09-04) — ตัว batcher telemetry: `enqueue`, `deriveElementId`, `collectTrackProps`, `flush`, กฎการ batch/retry/ปิดใช้งาน
- `../carmen-inventory-frontend-react/components/analytics-bridge.tsx` (เต็ม) — จุดและเวลาที่การ tracking เริ่มทำงาน
- `../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) — list ตรง ๆ เพื่อยืนยันว่าไม่มีชุดทดสอบ `activity-events` (§4.3)

## 7. หน้าย่อยของโมดูลนี้

- [Data Model](/th/platform/activity-events/data-model) — ทุกฟิลด์ของเรคคอร์ด `tb_activity_event` ใครเป็นคนเขียน และกลไก retention/rollup ที่คุมว่าแถวถูกเก็บไว้นานแค่ไหน
