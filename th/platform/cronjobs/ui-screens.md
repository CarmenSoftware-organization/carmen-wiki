---
title: งานตามกำหนดเวลา — หน้าจอ UI (UI Screens)
description: หน้ารายการ ตัวกรอง และสถิติสรุปของ CronJobManagement การ์ด basics/schedule/execution/type-config ของ CronJobEdit และตัวสร้างตารางเวลาหกโหมดของ CronScheduleField
published: true
date: '2026-09-06T22:00:00.000Z'
tags: book/platform, cronjobs, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# งานตามกำหนดเวลา — หน้าจอ UI (UI Screens)

> **หน้าจอ:** `CronJobManagement` (รายการ, `/cronjobs`) &nbsp;·&nbsp; `CronJobEdit` — คอมโพเนนต์เดียวใช้ทั้งสร้าง (`/cronjobs/new`) และแก้ไข (`/cronjobs/:id/edit`) &nbsp;·&nbsp; **ไม่มีแท็บ ไม่มี wizard** — การ์ดสี่อันเรียงกันบนฟอร์มแก้ไข &nbsp;·&nbsp; **คอมโพเนนต์ย่อย:** `CronScheduleField` ตัวสร้าง cron หกโหมด บวกคอมโพเนนต์ฟิลด์ config เฉพาะประเภทหกตัว (`jobConfig/`) &nbsp;·&nbsp; **Dialog:** ยืนยันการลบงาน (ข้อความรับรู้ความเป็นเจ้าของ) &nbsp;·&nbsp; **State ที่จำไว้:** `localStorage` key เดียว (`perpage_cronjob`) &nbsp;·&nbsp; **Concurrency:** optimistic lock `doc_version` ส่งเฉพาะเมื่อ GET ที่โหลดฟอร์มคืนค่ามาให้ &nbsp;·&nbsp; **Screenshot:** เลื่อนออกไปตามแผน — ยังไม่มี asset screenshot สำหรับโมดูลนี้

## 1. ภาพรวม

โมดูลนี้มีสองหน้าจอ `CronJobManagement.tsx` (อ่านแบบเต็ม) เป็น `DataTable` แบ่งหน้าฝั่ง server มาตรฐาน พร้อมแถบสรุปหกตัวเลขอยู่ด้านบน `CronJobEdit.tsx` (อ่านแบบเต็ม) คือฟอร์มสร้างและหน้าแก้ไขแถวเดียวรวมอยู่ในคอมโพเนนต์เดียว — ต่างจากรูปแบบสลับ view/edit mode ที่ใช้ในที่อื่นของหนังสือเล่มนี้ ([Database Pools](/th/platform/database-pools/ui-screens) §3–4) หน้านี้ไม่มี mode "view" แยกต่างหากเลย: ฟอร์มของงานที่มีอยู่แล้วแค่ถูกกรอกข้อมูลไว้ล่วงหน้าและแก้ไขได้ตลอด (ขึ้นกับการเช็คสิทธิ์ `cronjob.manage` ที่บันทึกไว้ใน [หน้า landing](/th/platform/cronjobs) §4) ส่วนแบ่งของ UI ที่ใช้ร่วมกันระหว่างสร้างและแก้ไขที่มีความซับซ้อนภายในของตัวเองจริง ๆ คือ `CronScheduleField` (§4) ตัวสร้าง cron expression

## 2. `CronJobManagement` — หน้ารายการ (`/cronjobs`)

### 2.1 แถบสถิติสรุป

หกตัวเลข render เป็น `grid` เหนือตาราง พร้อม caption ด้านล่างที่บอกขอบเขตไว้ชัดเจน:

| สถิติ | แหล่งที่มา | ขอบเขต |
|---|---|---|
| Total | `paginate.total` จาก server | ทั้งตาราง |
| Running | `items.filter(j => j.is_active).length` | **เฉพาะหน้าที่โหลดอยู่** |
| Stopped | `items.filter(j => !j.is_active).length` | **เฉพาะหน้าที่โหลดอยู่** |
| With Errors | `items.filter(j => !!j.last_error).length` | **เฉพาะหน้าที่โหลดอยู่** |
| Foreign-Owned | `items.filter(j => !!j.source_service).length` | **เฉพาะหน้าที่โหลดอยู่** |
| Active in Scheduler | `GET /api/cronjobs/status` → `scheduler.ActiveJobCount()` | สดจากทั้ง scheduler — เป็นอิสระจากตัวเลขอื่นทุกตัวในแถบนี้ |

caption ใต้แถบมีอยู่เพราะเหตุผลเฉพาะ: สี่ใน หกตัวเลขนี้อยู่ในขอบเขตของหน้า ไม่ใช่ทั้งตาราง — ดู [Data Model](/th/platform/cronjobs/data-model) §5.2 ว่าทำไม "With Errors" โดยเฉพาะจึงไม่ควรอ่านว่าเป็น "ทุกงานที่กำลังล้มเหลว"

### 2.2 การค้นหาและตัวกรอง

- **การค้นหา** เป็นการค้นแบบ free-text ฝั่ง server แบบ debounce (300ms) กับ `name`, `description`, `job_type`, `cron_expression`, และ `source_service` (`defaultSearchFields` ของ `cronjobService.ts`)
- **ตัวกรอง** เปิด side sheet (`CronJobFilterSheet`) มี Select แบบตายตัวสองตัว: **Job Type** (ทั้งหกประเภทบวก "All") และ **Status** (Running / Stopped / "All") ไม่มีไวยากรณ์ filter แบบขั้นสูงหรือพิมพ์เอง
- เคยมีตัวกรอง **Owner** ("All" กับ "Platform-owned only") อยู่ และถูกเอาออกไป เหตุผลคือข้อจำกัดของ backend ไม่ใช่การเปลี่ยนดีไซน์: ตัว parser query string ที่ gateway ใช้ร่วมกัน (`parseFilterString`, `apps/backend-gateway/src/shared-dto/paginate.dto.ts`) ตัดคู่ `key:value` ที่ค่าเป็น empty string ทิ้งก่อนที่ `platform_cronjobs.service.ts` จะเห็นด้วยซ้ำ — ดังนั้นตัวกรอง "Platform-owned only" ซึ่งต้องส่ง `source_service:` (ว่าง) จึงตรงกับทุกอย่างโดยเงียบ ๆ แทนที่จะกรองงาน foreign-owned ออก comment ของคอมโพเนนต์เองสรุปไว้ตรง ๆ: "Select ที่กรองไม่ได้แย่กว่าการไม่มี Select เลย"

### 2.3 คอลัมน์

| คอลัมน์ | เรียงได้ไหม | หมายเหตุ |
|---|---|---|
| Name | ได้ | แสดง description เป็นบรรทัดสีจางด้านล่างเมื่อมีค่า |
| Type | ได้ | Badge หนึ่งใน label ของ `job_type` ทั้งหก |
| Business Unit | ไม่ได้ (ค่าอยู่ใน JSON ของ `job_config` ไม่ใช่คอลัมน์ที่ server เรียงได้) | แสดงเฉพาะ `report`/`dashboard_refresh` (สองประเภทที่ผูกกับ BU) แสดง `bu_codes` สองตัวแรกบวก overflow `+N`, "All" สำหรับ `dashboard_refresh` ที่ว่าง, หรือขีดกลางสำหรับประเภทอื่น/`report` ที่ `bu_codes` ว่าง (`bu_codes` ว่างของงาน `report` คือ config ผิดพลาด ไม่ใช่ "ทุกหน่วยธุรกิจ" — คอลัมน์นี้ตั้งใจไม่ปนสองความหมายนี้เข้าด้วยกัน) |
| Schedule | ไม่ได้ | cron expression ดิบบวกคำอธิบายภาษาธรรมดาด้านล่าง (`describeCron`) |
| Status | ได้ | badge Running / Stopped จาก `is_active` |
| Owner | ไม่ได้ | badge `source_service` หรือ "Platform" ถ้าไม่ตั้งค่า |
| Last Run | ได้ | เวลาสัมพัทธ์; ไอคอนสามเหลี่ยมเตือนพร้อม tooltip error ดิบเมื่อ `last_error` มีค่า — ดู [Data Model](/th/platform/cronjobs/data-model) §5.2 |
| Next Run | ได้ | timestamp แบบเต็ม |
| Runs | ได้ | `run_count` ชิดขวาแบบตัวเลข |
| (actions) | — | ถูกซ่อนทั้งหมดถ้า session ไม่มี `cronjob.manage` |

### 2.4 การกระทำต่อแถว

ไอคอนทั้งสี่ในคอลัมน์ action ถูก disable (ไม่ใช่ซ่อน) เฉพาะแถวที่กำลังทำงานอยู่ ติดตามด้วย state ตัวเดียว `actingJobId` แทนที่จะล็อกทั้งตาราง — comment ของคอมโพเนนต์เองอธิบายว่าทำไมเรื่องนี้สำคัญเป็นพิเศษกับ **Run Now**: ต่างจาก Start/Stop การคลิกซ้ำไม่ใช่แค่การทำซ้ำที่ไม่มีอันตราย มันเริ่ม background run จริงเป็นครั้งที่สองแยกต่างหาก (อีเมลรายงานซ้ำ notification ซ้ำ หรือ — สำหรับงาน `cleanup` เมื่อ implement แล้ว — การลบที่รันซ้ำสองครั้ง)

| ไอคอน | การกระทำ | ผลลัพธ์ |
|---|---|---|
| Play / Pause | Start / Stop | `POST /:id/start` หรือ `/stop`; toast สำเร็จ; รายการ refresh |
| Zap | Run Now | `POST /:id/execute`; **`toast.info` "dispatched" ไม่ใช่ `toast.success`** — endpoint ส่งงานให้ background worker แล้วคืนค่าก่อนจะรู้ผลลัพธ์ |
| Pencil | Edit | ไปที่ `/cronjobs/:id/edit` |
| Trash | Delete | เปิด dialog ยืนยัน (§5) |

### 2.5 Export CSV

export **เฉพาะหน้าที่โหลดอยู่เท่านั้น** — comment ของคอมโพเนนต์เองระบุว่า `perpage: -1` endpoint นี้ไม่รองรับ (คืน 10 แถวเงียบ ๆ เสมอ) จึงไม่เคยเป็นการ export ทั้งตาราง สิบคอลัมน์: ชื่อ, description, label ประเภท, label business unit, cron expression, label สถานะ, label owner, last run, next run, run count

### 2.6 Dev-only debug panel

เฉพาะ build `NODE_ENV === 'development'` เท่านั้น จะมี `DevDebugSheet` ลอยแสดงข้อมูล item ดิบที่โหลดมา query parameter ปัจจุบัน และ `{ total, activeJobs }` — ไม่มีใน production

## 3. `CronJobEdit` — สร้าง (`/cronjobs/new`) และแก้ไข (`/cronjobs/:id/edit`)

การ์ดสี่อันเรียงกันตามลำดับนี้เสมอ บวกอันที่ห้าแบบมีเงื่อนไข:

### 3.1 Basics

- **Name** (บังคับ — ฟิลด์เดียวที่มีการ validate ตอน blur; handler update ฝั่ง backend ไม่มีการเช็คว่าไม่ว่างเลย ดังนั้นชื่อว่างที่พิมพ์แล้วลบทิ้งอาจหลุดไปถึงฐานข้อมูลได้ถ้าไม่ดักไว้ที่นี่)
- **Job Type** — Select ถูก **disable เมื่องานถูกสร้างไปแล้ว** (ล็อกหลังสร้าง; การเปลี่ยนประเภทจะทิ้ง `job_config` เก่าที่มีรูปร่างสำหรับประเภทเดิมไว้ เพราะทั้งหก config แทบไม่มีฟิลด์ร่วมกันเลย)
- **Description** — free text, optional
- **Active** — checkbox; เทียบเท่ากับปุ่ม Start/Stop ของหน้ารายการ

### 3.2 Schedule

`CronScheduleField` (§4) บวก — **เฉพาะ job type `report`** — ช่องกรอกเวลา `notify_at` พร้อม hint อธิบายว่ามันควบคุมเวลาที่บอกผู้รับว่ารายงานพร้อมแล้ว แยกต่างหากจากเวลาที่ตัวงานรัน ไม่มี job type อื่น render ฟิลด์นี้เลย สอดคล้องกับข้อเท็จจริงฝั่ง backend ที่ไม่มี executor อื่นอ่านมันเลย ([Data Model](/th/platform/cronjobs/data-model) §3.1)

### 3.3 Execution

ช่องตัวเลขสองช่อง: **Max Retries** (default 0) และ **Timeout (seconds)** (default 300) ไม่มีคำอธิบายเพิ่มเติมนอกจาก label ดู [Data Model](/th/platform/cronjobs/data-model) §4.3 ว่าค่าเหล่านี้ควบคุมอะไรจริง ๆ

### 3.4 Type Config

render หนึ่งในหกคอมโพเนนต์ (`jobConfig/`) เลือกตาม `job_type` แต่ละตัวรองรับฟิลด์ใน [Data Model](/th/platform/cronjobs/data-model) §3:

| `job_type` | คอมโพเนนต์ | พฤติกรรม UI ที่น่าสังเกต |
|---|---|---|
| `report` | `ReportConfigFields` | โหลดเทมเพลตรายงานและผู้ใช้แบบสดสำหรับสอง picker (dropdown เทมเพลต, multi-select ค้นหาได้ของผู้รับตามชื่อ/email — ไม่ใช่ช่องพิมพ์เอง); Select **Delivery Type** (`file`/`viewer_url`); **ไม่มีช่องสำหรับ endpoint ของ `viewer_url` เลย** โดยตั้งใจ (ดู SSRF note §3.1) |
| `notification` | `NotificationConfigFields` | รูปแบบ multi-select ค้นหาได้แบบเดียวกันสำหรับ `user_ids`; hint ระบุว่าฟิลด์นี้จำเป็น แก้จาก hint เดิมที่คัดลอกมาจาก `dashboard_refresh` ซึ่งบอกผิด ๆ ว่าว่างคือ "ทุกคน" |
| `cleanup` | `CleanupConfigFields` | ช่องพิมพ์เองสามช่อง (`action`, `type`, `older_than`) ไม่มีการ validate — ตรงกับฝั่ง backend ที่ก็ไม่ validate อะไรเช่นกัน |
| `dashboard_refresh` | `DashboardRefreshConfigFields` | multi-select business unit (ว่างหมายถึง "ทุก BU ที่ active" จริง — ประเภทเดียวที่ hint นี้ถูกต้อง) และ Select Tier (`operational`/`breakdown`/`matrix`/"All") |
| `activity_rollup` | `ActivityRollupConfigFields` | ช่องตัวเลขหนึ่งช่อง `days_back` (default 2) |
| `activity_retention` | `ActivityRetentionConfigFields` | ช่องตัวเลขสองช่อง `retention_days` (default 365) และ `batch_size` (default 10000) |

การเปลี่ยน Job Type บนฟอร์ม**สร้าง**จะรีเซ็ต `job_config` เป็น `{}` ใน state update ก้อนเดียวกันกับการเปลี่ยนประเภทเสมอ — ไม่เคยปล่อยให้ฟิลด์ของประเภทเดิมค้างอยู่ในรูปร่างที่ TypeScript's weak union check จะยอมให้คอมไพล์ผ่านโดยเงียบ ๆ

### 3.5 History (เฉพาะงานที่มีอยู่แล้ว เมื่อมีข้อมูล audit)

render `AuditMeta` — เฉพาะ `created_at`/`created_by_id`/`updated_at`/`updated_by_id` **ไม่แสดง `last_run_at`, `next_run_at`, `last_error`, หรือ `run_count`** — ดู [Data Model](/th/platform/cronjobs/data-model) §5.3 ว่าทำไม tester ไม่ควรคาดหวังหลักฐานความล้มเหลวของ run บนหน้านี้เลย

### 3.6 Banner งาน foreign-owned

เมื่อ `source_service` ของงานที่โหลดมามีค่า จะมี banner เตือนปรากฏเหนือฟอร์ม: "กำลังแก้ไขงานที่ service อื่นเป็นเจ้าของ — การเปลี่ยนแปลงที่นี่มีผลกับกำหนดการของ business unit นั้นโดยตรง" dialog ยืนยันการลบของหน้ารายการมีคำเตือนที่คล้ายกันแต่ระบุ service เจ้าของชัดเจนกว่า (§5)

### 3.7 Save, การ validate, และ version conflict

- **การ validate ฝั่ง client ก่อน submit:** name บังคับ (เช็คซ้ำที่นี่ ไม่ใช่แค่ตอน blur เพราะ `Ctrl/Cmd+S` และ native form submit ข้าม blur handler ได้ทั้งคู่); cron expression บังคับ แล้วถูก validate ว่า parse ได้ (`describeCron(...) === null` ถือว่า "invalid" แยกจากช่องที่ยังไม่ได้แตะ/ว่าง ซึ่งถือว่า "required" แทน)
- **`doc_version`** ถูกใส่ใน payload อัปเดตเฉพาะเมื่อ GET ที่โหลดฟอร์มคืนค่ามาให้ — ถ้าไม่ส่งเท่ากับบอก gateway ให้ข้ามการเช็ค conflict ไปเลย ตรงกับรูปแบบที่ entity แบบ optimistic-lock อื่นใน SPA นี้ใช้
- **Version conflict (`409`, `error_code: VERSION_CONFLICT`)** — เป็น error-code contract ของ `micro-cronjobs` เอง อ่านจากระดับบนสุดของ response body แตกต่างจาก contract `DOC_VERSION_CONFLICT`/message-pattern ที่ helper กลาง `isVersionConflict()` ถูกเขียนไว้สำหรับ resource ฝั่ง Prisma หน้านี้เช็ค code เฉพาะของ Go ก่อน แล้วค่อย fallback ไปที่ helper กลาง และ comment ของคอมโพเนนต์เองเตือนไว้ตรง ๆ ว่าอย่าลบอันใดอันหนึ่งทิ้งเพื่อ "ลดความซ้ำซ้อน" — เพราะเป็นคนละ contract กันจริง ๆ
- **`FOREIGN_OWNED_JOB` (`409`)** — ยังมี branch จัดการอยู่ (เช็คก่อน branch version-conflict เพราะทั้งคู่เป็น 409 มี error code เท่านั้นที่บอกความต่าง) แม้ว่า gateway ปัจจุบันจะไม่ส่ง code นี้แล้วก็ตาม เก็บไว้เผื่อ gateway รุ่นเก่ายังใช้งานอยู่ ดู [หน้า landing](/th/platform/cronjobs) §4

## 4. `CronScheduleField` — ตัวสร้างตารางเวลา

คอมโพเนนต์เดียวใช้ร่วมกันระหว่างสร้างและแก้ไข สร้างขึ้นบนกฎเดียว: **cron expression string คือ state เดียวที่มีอยู่จริง** ทุกครั้งที่ render จะ parse ค่านั้นใหม่ (`parseCron(value)`) เป็นโหมดและค่าฟิลด์ที่ UI แสดง ไม่มี flag "โหมดไหนกำลังใช้งาน" แยกเก็บไว้ที่ไหนเลย ดังนั้นการพิมพ์ตรงในช่อง expression ดิบกับการใช้ปุ่มควบคุมแบบมีไกด์จึงไม่มีทางเพี้ยนออกจากกันได้

- **หกโหมด:** ทุก N นาที, รายชั่วโมง, รายวัน, รายสัปดาห์, รายเดือน และ grid custom แบบ 5 ช่องดิบ (minute / hour / day-of-month / month / day-of-week) expression ที่โหมดแบบมีไกด์แสดงไม่ได้ (ช่วงแบบ `1-5` รายการเดือนเจาะจง) จะตกลงโหมด custom โดยอัตโนมัติ — ไม่ถือว่าเป็น error เพราะ expression นั้นถูกต้องสมบูรณ์
- **คำอธิบายแบบสด:** `describeCron()` render ประโยคภาษาธรรมดาใต้ช่อง expression (เช่น "every day at 02:00") แยกความต่างระหว่างช่องที่ยังไม่แตะ/ว่าง (ประโยคว่าง ไม่มี error) กับ expression ที่ผิดรูปจริง ๆ (คืนค่า `null` แสดงเป็น error inline)
- **ตัวอย่าง 3 run ถัดไป:** คำนวณและแสดงใต้คำอธิบาย พร้อม caption ระบุ timezone ท้องถิ่นของ**เบราว์เซอร์**อย่างชัดเจน — ตั้งใจไม่นำเสนอเป็นข้อเท็จจริงเดียวกับ timezone ของ scheduler ฝั่ง server ที่ resolve ไว้ (ปกติ Asia/Bangkok) เพราะสองอย่างนี้ต่างกันได้ และคอมโพเนนต์ไม่มีทางรู้ zone ของ server จากตรงนี้ คำเตือนนี้คือการแก้ไขของคอมโพเนนต์เอง ระบุไว้ใน comment ว่าแก้เวอร์ชันก่อนหน้าที่นำเสนอสองอย่างนี้ราวกับใช้แทนกันได้

## 5. Dialog

### 5.1 ยืนยันการลบงาน (หน้ารายการเท่านั้น)

สองรูปแบบข้อความ เลือกตามว่างานเป้าหมายมี `source_service` หรือไม่:

- **Platform-owned:** ข้อความ "ลบงานนี้หรือไม่?" ธรรมดา ระบุชื่องาน
- **Foreign-owned:** ระบุทั้งชื่องานและ service เจ้าของ วางกรอบว่าเป็นการลบกำหนดการของ business unit นั้นถาวร เพราะสร้างกลับคืนจากหน้าจอนี้ไม่ได้

## 6. State ของ UI ที่จำไว้

`localStorage` key เดียว: `perpage_cronjob` ตัวเลือกจำนวนแถวต่อหน้าของหน้ารายการ การค้นหา ตัวกรอง การเรียงลำดับ และเลขหน้าไม่ถูกจำไว้ข้ามการเข้าชม

## 7. อ้างอิง

- `../carmen-platform/src/pages/cronjobs/CronJobManagement.tsx` — หน้ารายการ อ่านแบบเต็ม
- `../carmen-platform/src/pages/cronjobs/CronJobEdit.tsx` — หน้าสร้าง/แก้ไข อ่านแบบเต็ม
- `../carmen-platform/src/pages/cronjobs/CronJobFilterSheet.tsx`, `CronScheduleField.tsx` — อ่านแบบเต็ม
- `../carmen-platform/src/pages/cronjobs/jobConfig/{index.tsx,ReportConfigFields.tsx,NotificationConfigFields.tsx,CleanupConfigFields.tsx,DashboardRefreshConfigFields.tsx,ActivityRollupConfigFields.tsx,ActivityRetentionConfigFields.tsx}` — คอมโพเนนต์ config เฉพาะทั้งหกตัวบวก dispatcher อ่านแบบเต็ม
- `../carmen-platform/src/services/cronjobService.ts` — REST client, comment เรื่องการ encode filter (§2.2)
- `../carmen-platform/src/utils/cronExpression.ts`, `cronSchedule.ts` — `describeCron`, `nextRuns`, `parseCron`, `buildCron`
- `../carmen-platform/src/components/Can.tsx` — helper render ตามสิทธิ์ที่อ้างถึงตลอดทั้งหน้า
- [Data Model](/th/platform/cronjobs/data-model) — ตารางฟิลด์และกลไก scheduler ที่การพาชมหน้าจอนี้ชี้กลับไปตลอด
- [หน้า landing ของ Cronjobs](/th/platform/cronjobs) §4 — ด่านสิทธิ์เบื้องหลังทุกปุ่มที่อ้างถึงในหน้านี้
- ยืนยันกับ `carmen-platform` HEAD `157a65e` (2026-09-04)
