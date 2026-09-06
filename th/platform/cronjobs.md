---
title: งานตามกำหนดเวลา (Cronjobs)
description: คอนโซลจัดตารางเวลาของแพลตฟอร์มบนตารางที่ใช้ร่วมกัน "CRONJOBS"."Cronjob" — งานหกประเภท ใครเป็นคนรัน (../micro-cronjobs) และจุดที่จะเห็นว่า run ไหนล้มเหลว
published: true
date: '2026-09-06T22:00:00.000Z'
tags: book/platform, cronjobs
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# งานตามกำหนดเวลา (Cronjobs)

> **At a Glance**
> **จุดประสงค์โมดูล:** คอนโซลดูแลระดับแพลตฟอร์มบนตารางเดียวที่ใช้ร่วมกัน `"CRONJOBS"."Cronjob"` ซึ่งทั้งโมดูลนี้และ service อื่นเขียนงานตามกำหนดเวลาลงไปด้วยกัน &nbsp;·&nbsp; **หน้าจอ:** `CronJobManagement` (รายการ, `/cronjobs`) และ `CronJobEdit` ใช้ทั้งสร้าง (`/cronjobs/new`) และแก้ไข (`/cronjobs/:id/edit`) &nbsp;·&nbsp; **Service เบื้องหลัง:** [`../micro-cronjobs`](#6-แหล่งอ้างอิง) (Go) — โปรเซส scheduler/worker แยกต่างหาก **ไม่มีการยืนยันตัวตนของตัวเอง** &nbsp;·&nbsp; **Sidebar:** `permission: 'cronjob.read'` อยู่กลุ่มของตัวเอง `navGroup.scheduling` — ไม่ถูกรวมเข้ากับ `navGroup.platform` &nbsp;·&nbsp; **Feature flag:** `cronjobs` &nbsp;·&nbsp; **โมเดลสอง permission:** `cronjob.read` (permission **เดียว** ที่ frontend route guard เช็คบนทั้งสามเส้นทาง รวมถึง `/new` และ `/:id/edit`) กับ `cronjob.manage` (ทุกการกระทำที่เขียนข้อมูล — start/stop/run-now/edit/delete/create — บังคับด้วย `<Can>` **และ** เช็คซ้ำใน submit handler) &nbsp;·&nbsp; **การกำหนด role:** มีเฉพาะ role **Platform Admin** เท่านั้นที่ถือ permission `cronjob.*` ใด ๆ &nbsp;·&nbsp; **ประเภทงาน:** 6 ประเภท — `report`, `notification`, `cleanup`, `dashboard_refresh`, `activity_rollup`, `activity_retention` &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — `../carmen-platform-e2e/tests/` ไม่มีโฟลเดอร์ `cronjobs` &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

**Cronjobs** คือหน้าต่างของแพลตฟอร์มที่มองเห็นงานเบื้องหลังที่ตั้งเวลาไว้ทุกงานใน Carmen — หนึ่งหน้ารายการ (`CronJobManagement.tsx` อ่านแบบเต็ม) และหนึ่งฟอร์มสร้าง/แก้ไข (`CronJobEdit.tsx` อ่านแบบเต็ม) ทั้งคู่เข้าถึงได้ที่ `/cronjobs` ตัวหน้าจอเองไม่ทำอะไรนอกจากอ่าน/เขียนแถวข้อมูล — งานจริงที่แต่ละแถวอธิบายไว้ ไม่ว่าจะเป็นส่งรายงาน รีเฟรชแดชบอร์ด หรือลบ telemetry เก่า ล้วนถูกทำโดย Go service แยกต่างหาก คือ **`../micro-cronjobs`** ซึ่ง poll ตารางฐานข้อมูลเดียวกับที่คอนโซลนี้แก้ไข การเข้าใจโมดูลนี้จึงต้องเข้าใจทั้งสองฝั่ง คือคอนโซลให้ตั้งค่าอะไรได้บ้าง และ worker ทำอะไรกับค่านั้นจริง ๆ เมื่อบันทึกแล้ว — รวมถึงจุดสำคัญคือ run ที่ล้มเหลวจะไปโผล่ให้เห็นที่ไหน

คอนโซลนี้ส่งต่อผ่าน `PlatformCronjobsController` / `PlatformCronjobsService` ของ `backend-gateway` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/`) ซึ่งเรียก REST API ของ `micro-cronjobs` เอง (`CRONJOB_SERVICE_URL`) ผ่าน HTTP ธรรมดา `micro-cronjobs` ไม่มีการ login, session หรือ API key ของตัวเองเลย — comment ของ gateway controller เองระบุตรง ๆ ว่ามันคือ "ด่านเดียวระหว่างเบราว์เซอร์กับ service ที่ลบ job ให้ใครก็ได้" และ `CRONJOB_SERVICE_URL` ต้องไม่ถูกเปิดเผยให้ frontend เห็นเด็ดขาด การตรวจสิทธิ์ทุกจุดที่ tester สังเกตเห็นได้จากเบราว์เซอร์เกิดขึ้นที่ gateway เท่านั้น ไม่ใช่ที่ worker

## 2. บริบททางธุรกิจ

`"CRONJOBS"."Cronjob"` ไม่ได้เป็นของโมดูลนี้แต่เพียงผู้เดียว — มันคือ **ตารางที่ใช้ร่วมกัน** บางแถวถูกสร้างที่นี่ โดยผู้ปฏิบัติงาน ผ่านคอนโซลนี้ (`source_service` ว่างเปล่า แสดงเป็น "Platform" ในคอลัมน์ Owner) บางแถวถูกสร้างโดย service อื่นในนามของ business unit — ที่เด่นชัดที่สุดคือ `reports.service.ts` ใน `backend-gateway` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.service.ts`) ซึ่งเรียก endpoint `by-source` ของ `micro-cronjobs` โดยตรง (client `cronjobHttp` ของตัวเองเรียก `CRONJOB_SERVICE_URL` ตรง ๆ ข้าม gateway controller ของโมดูลนี้ไปเลย) ทุกครั้งที่ business unit ตั้งกำหนดการรายงานแบบทำซ้ำจากอีกส่วนของผลิตภัณฑ์ แถว "foreign-owned" เหล่านั้นยังคงมองเห็น แก้ไข และลบได้เต็มที่จากคอนโซลนี้ — ดู §3 ว่าสิ่งนี้หมายความว่าอะไร และไม่ได้หมายความว่าอะไร

นี่คือเหตุผลที่โมดูลนี้อยู่ในกลุ่ม nav **ของตัวเอง** แทนที่จะอยู่ใน `navGroup.platform` comment เหนือรายการ nav (`platformNav.ts:34-35`) เขียนว่า "Scheduling — งานตามเวลา ไม่ใช่การตั้งค่าระบบ จึงเป็นกลุ่มของตัวเอง" ตรวจสอบแล้วในเชิงโครงสร้าง ไม่ใช่เชื่อตาม comment เฉย ๆ: `navGroup.scheduling` มีแค่แถวเดียว (`/cronjobs` grep ทั่วทั้งไฟล์ nav) อยู่ระหว่างกลุ่ม Analytics (Usage Analytics, Activity Events) กับกลุ่ม Platform (Platform Config, Email Settings, Applications, Roles, User Platform, Super Admins, Feature Flags) — แยกตัวจากทั้งสองข้างจริง ไม่ได้ถูกรวมกับฝั่งไหนเลย เหตุผลนี้ยืนได้: ทุกอย่างใน `navGroup.platform` ตัดสินว่า *ใครทำอะไรได้* หรือ *ตั้งค่าแพลตฟอร์มอย่างไร* ส่วน Cronjobs ตัดสินว่า *งานเบื้องหลังจะรันเมื่อไร* ซึ่งเป็นการตั้งค่าคนละประเภทกันจริง ๆ

## 3. แนวคิดสำคัญ

- **หนึ่งแถวคือหนึ่งงานตามกำหนดเวลา** ทุกแถวมี `job_type` (หนึ่งในหกประเภท — §3.1) cron expression 5 ช่อง job_config แบบ JSON เฉพาะประเภท flag active/inactive และผลลัพธ์ของ run ล่าสุดของตัวเอง (`last_run_at`, `next_run_at`, `last_error`, `run_count`) ตารางฟิลด์เต็ม: [Data Model](/th/platform/cronjobs/data-model) §2
- **scheduler ไม่ใช่คอนโซล เป็นผู้ตัดสินว่างานจะรันเมื่อไร** `micro-cronjobs` poll ฐานข้อมูลทุกหนึ่งนาที เก็บทุกงาน active ไว้ใน scheduler `go-cron` แบบ in-memory แล้วรันมันเมื่อถึงเวลาตาม cron expression — ในโซนเวลาที่ process resolve ไว้ (ปกติคือ `Asia/Bangkok` ดู [Data Model](/th/platform/cronjobs/data-model) §4) การบันทึกการแก้ไขที่นี่ไม่ได้ทำให้งานรันทันที มันแค่เปลี่ยนว่า run ครั้งถัดไป (หรือที่สั่งรันเอง) จะทำอะไร
- **"Run Now" คือการส่งงานออกไป ไม่ใช่การยืนยันผล** ปุ่ม execute (`POST /:id/execute`) ส่งงานให้ background goroutine แล้วคืนค่าทันที — toast ของคอนโซลเองบอกว่า "dispatched" (`toast.info`) ไม่ใช่ "succeeded" โดยตั้งใจ เพราะยังไม่รู้ผลลัพธ์ตอนที่ HTTP response กลับมา ดู §3.5 และ [Data Model](/th/platform/cronjobs/data-model) §5 ว่าผลลัพธ์นั้นไปโผล่ที่ไหนในที่สุด
- **ความเป็นเจ้าของมองเห็นได้ แต่ไม่ใช่การล็อก** งานที่ service อื่นสร้าง (มี `source_service`) สั่ง start, stop, run, แก้ไข หรือลบได้จากคอนโซลนี้เหมือนกับงานที่ platform สร้างเองทุกประการ — เมธอด `update()`/`remove()`/`control()` ของ gateway ไม่มีการตรวจความเป็นเจ้าของเลย (ยืนยันจากการอ่าน `platform_cronjobs.service.ts` — แต่ละเมธอดมี comment บอกไว้เอง) สิ่งเดียวที่คอนโซลทำเกี่ยวกับความเป็นเจ้าของคือให้ข้อมูล: คอลัมน์/badge Owner บนหน้ารายการ banner เตือนบนหน้าแก้ไข และข้อความยืนยันก่อนลบที่ต่างออกไป ("นี่คือการลบกำหนดการรายงานของ business unit นั้นถาวร" ไม่ใช่ "ลบ job นี้หรือไม่?" แบบทั่วไป)
- **`cronjob.manage` คุมทุกการเขียนข้อมูล ส่วน `cronjob.read` คุมตัวหน้าเอง — รวมถึง route สร้าง/แก้ไขด้วย** `App.tsx:531-551` ใส่ `requiredPermission="cronjob.read"` บน**ทั้งสามเส้นทาง** (`/cronjobs`, `/cronjobs/new`, `/cronjobs/:id/edit`); `cronjob.manage` ถูกเช็คเฉพาะภายในหน้าเท่านั้น ผ่าน `<Can>` รอบทุกปุ่มที่เขียนข้อมูล และเช็คซ้ำใน `handleSave()` session ที่มีแค่สิทธิ์อ่านเปิดฟอร์มสร้างและกรอกข้อมูลได้ แต่ปุ่ม Save ไม่ถูก render และ submit handler จะ return ก่อนเรียก API ตารางสิทธิ์เต็ม: §4
- **มีแค่ Platform Admin เท่านั้นที่เข้าถึงโมดูลนี้ได้เลย** `seed.platform-role-permission.data.ts:15` ให้ `cronjob.*` แก่ Platform Admin คนเดียว; Support Manager, Support Staff และ Security Officer ไม่มีทั้งสอง key เลย ทั้งรายการ nav, route guard และ backend จึงสอดคล้องกัน: ไม่มีใครอื่นเห็น Cronjobs

### 3.1 ประเภทงาน

| `job_type` | ทำอะไร | จุดเด่นของ config | Executor (`../micro-cronjobs`) |
|---|---|---|---|
| `report` | ส่งรายงานตามกำหนดเวลา — สร้าง viewer URL ที่แชร์ได้ หรือคิวการ render ไฟล์แบบเดิม แล้วแจ้งผู้รับ | `template_id`, `bu_codes` (**บังคับ** — executor error ถ้าว่าง), `format`, `filters`, `recipients` (user ID ไม่ใช่ email แบบพิมพ์เอง), `delivery.type` (`file` / `viewer_url`), `notifications.{web,email,mail_source}`; ประเภทเดียวที่อ่านฟิลด์ระดับแถว `notify_at`/`notify_day_offset` | `ReportExecutor` (`report.go`) |
| `notification` | ส่งการแจ้งเตือนแบบ system ไปยังผู้ใช้กลุ่มหนึ่งที่กำหนดไว้ | `title`, `message`, `type`, `category` (default `system`), `user_ids` (**บังคับ**) | `NotificationExecutor` (`notification.go`) |
| `cleanup` | ตั้งเป็นงานได้ ตั้งตารางได้ log ได้ — **แต่ยังไม่ได้ implement** executor แค่ log config แล้วคืนค่าสำเร็จโดยไม่ลบอะไรเลย | `action`, `type`, `older_than` (free text ไม่ validate) | `CleanupExecutor` (`cleanup.go`) — body เป็น `// TODO: implement cleanup logic per type` |
| `dashboard_refresh` | รีเฟรช materialized view ใน `micro-data` | `bu_codes` (optional — ว่างคือทุก business unit ที่ active) `tier` (optional — `operational` / `breakdown` / `matrix` ว่างคือทุก tier) | `DashboardRefreshExecutor` (`dashboard.go`) |
| `activity_rollup` | คำนวณ `tb_activity_event_daily` ใหม่จาก raw UI telemetry ย้อนหลัง N วัน | `days_back` (default 2 — self-heal เหตุการณ์ที่มาช้า) | `ActivityRollupExecutor` (`activity_rollup.go`) — ดู [Activity Events — Data Model](/th/platform/activity-events/data-model) §4.2 |
| `activity_retention` | ลบแถว raw `tb_activity_event` ที่เกินช่วง retention เป็น batch | `retention_days` (default 365), `batch_size` (default 10000) | `ActivityRetentionExecutor` (`activity_retention.go`) — ดู [Activity Events — Data Model](/th/platform/activity-events/data-model) §4.1 |

`job_type` **ถูกล็อกหลังสร้าง** — Select ถูก disable บนฟอร์มแก้ไข และ update DTO ฝั่ง backend ไม่รับฟิลด์นี้เลยด้วยซ้ำ เพราะ `job_config` เป็น union ของหกรูปแบบที่ไม่เกี่ยวข้องกันเชิงโครงสร้าง และไม่มีทาง migrate จากอันหนึ่งไปอีกอันหนึ่งได้

### 3.2 งานที่ seed ไว้แล้ว รันอยู่แล้ว

งานสามประเภทมาพร้อมแถว active ที่ seed ไว้จาก migration ไม่ได้สร้างผ่านคอนโซลนี้ — ผู้ปฏิบัติงานที่เปิด `/cronjobs` บน environment ใหม่จะเห็นแถวเหล่านี้อยู่แล้ว:

| ชื่อ | `job_type` | ตารางเวลา | Config | Migration |
|---|---|---|---|---|
| Dashboard MV refresh - operational | `dashboard_refresh` | `*/5 * * * *` (ทุก 5 นาที) | `{"tier":"operational"}` | `20260610120000_seed_dashboard_refresh_jobs.up.sql` |
| Dashboard MV refresh - breakdown | `dashboard_refresh` | `*/30 * * * *` (ทุก 30 นาที) | `{"tier":"breakdown"}` | เดียวกัน |
| Dashboard MV refresh - matrix | `dashboard_refresh` | `0 */6 * * *` (ทุก 6 ชั่วโมง) | `{"tier":"matrix"}` | เดียวกัน |
| Activity events daily rollup | `activity_rollup` | `30 3 * * *` (03:30) | `{"days_back":2}` | `20260730092930_seed_activity_rollup_job.up.sql` |
| Activity events retention (365d) | `activity_retention` | `0 4 * * *` (04:00) | `{"retention_days":365,"batch_size":10000}` | `20260730093731_seed_activity_retention_job.up.sql` |

**ความสอดคล้องกับ [Activity Events — Data Model](/th/platform/activity-events/data-model) §4:** หน้านั้นระบุว่า rollup รันเวลา 03:30 และ retention รันเวลา 04:00 ทั้งคู่บน `"CRONJOBS"."Cronjob"` ทั้งคู่ `is_active: true` หน้านี้อ่าน seed migration ทั้งสองไฟล์และตาราง dispatch ของ executor อีกครั้งอย่างเป็นอิสระ และได้ข้อสรุปเดียวกัน — ไม่พบความขัดแย้ง สิ่งเดียวที่เพิ่มเข้ามาในหน้านี้ซึ่งหน้า Activity Events ไม่มีเหตุผลต้องพูดถึงคือ: งานทั้งสองนี้บริหารจัดการได้จาก**คอนโซลนี้**เหมือนแถวอื่น ๆ (ผู้ปฏิบัติงานที่มี `cronjob.manage` สามารถเปลี่ยนตารางเวลา ปิด หรือลบทั้งสองงานนี้ได้ในทางทฤษฎี) ซึ่งเป็นข้อเท็จจริงเชิงโครงสร้างว่างานอยู่ที่ไหน ไม่ใช่การอ้างว่ามีใครทำเช่นนั้นจริงบน environment ที่ใช้งานจริง

### 3.3 รูปแบบตารางเวลา

`cron_expression` ทุกตัวเป็น cron string มาตรฐาน 5 ช่อง (`minute hour day-of-month month day-of-week`) — ไม่มีช่อง seconds ฝั่ง Go scheduler parse มันเพื่อคำนวณ "run ถัดไป" ของตัวเองด้วย `cron.ParseStandard` ของ `robfig/cron` (`scheduler.go`); ตัวสร้างตารางเวลาของคอนโซล (`CronScheduleField` ดู [UI Screens](/th/platform/cronjobs/ui-screens) §4) มีโหมดช่วยเหลือหกโหมด — ทุก N นาที, รายชั่วโมง, รายวัน, รายสัปดาห์, รายเดือน และโหมด custom แบบ 5 ช่องดิบ — สร้างและ parse จาก expression string เดียวกัน ดังนั้นการพิมพ์ตรงในช่อง expression กับการใช้ปุ่มควบคุมของตัวสร้างจึงตรงกันเสมอ ไม่มี state "โหมด" แยกเก็บไว้ที่ไหนเลย

### 3.4 การลองใหม่ timeout และความขนาน

- **Timeout** (`timeout_seconds` default 300): ครอบ run ทั้งหมดด้วย context deadline ทั้งการรันตามกำหนดเวลาและการสั่งรันเอง
- **Retry** (`max_retries` default 0): เมื่อล้มเหลว scheduler จะลองใหม่แบบ synchronous สูงสุดตามจำนวนนั้น ด้วย exponential backoff — 10 วินาที, 40 วินาที, 90 วินาที ไปเรื่อย ๆ (`attempt² × 10 วินาที`) พร้อมอัปเดต `last_run_at`/`last_error`/`retry_count` ของแถวหลังทุกครั้งที่ลอง
- **เพดานความขนาน:** งานรันพร้อมกันได้สูงสุด 5 งานทั่วทั้งโปรเซส `micro-cronjobs` (`gocron.WithLimitConcurrentJobs(5, gocron.LimitModeWait)`); งานที่ 6 ที่ถึงกำหนดจะรอคิวแทนที่จะรันขนาน
- **รอบ poll:** scheduler โหลดงาน active จากฐานข้อมูลใหม่ทุกหนึ่งนาที และสร้างใหม่ (ลบแล้วเพิ่มกลับ) ให้กับงานที่ cron expression, config หรือค่า notify เปลี่ยนไปตั้งแต่ poll ครั้งก่อน — gocron ไม่มี API "update ตารางเวลา" แบบแก้ในที่ การเรียก create/update/delete/start/stop ทุกครั้งจาก gateway ยังสั่ง re-sync แบบ asynchronous ทันที (`ForceSync()`) ด้วย ดังนั้นในทางปฏิบัติการแก้ไขที่บันทึกแล้วมักถูกนำไปใช้ก่อนรอบ poll ถัดไปนานมาก — แต่ re-sync นั้นเป็น fire-and-forget ดังนั้น HTTP response ที่ผู้ปฏิบัติงานได้รับหลังกด Save จึงไม่มีการยืนยันว่า scheduler ได้นำไปใช้แล้วจริง

### 3.5 จุดที่จะเห็นว่า run ไหนล้มเหลว

นี่คือคำถามที่รายชื่อ job ตอบเองไม่ได้ — ดู [Data Model](/th/platform/cronjobs/data-model) §5 สำหรับคำตอบเต็ม (คอลัมน์ DB ที่เก็บมัน สิ่งที่หน้ารายการแสดงและจุดที่ยังขาด เหตุผลที่หน้าแก้ไขไม่แสดงเลย และ OpenTelemetry trace ที่เป็นที่เดียวที่มี trace แบบเต็ม) สรุปสั้น ๆ: **คอลัมน์ Last Run บนหน้ารายการ** ผ่านไอคอนเตือนที่มี tooltip เก็บข้อความ error ดิบ คือที่เดียวในคอนโซลนี้ที่มนุษย์อ่านได้ว่าเกิดอะไรผิดพลาด

## 4. บทบาทและสิทธิ์

| จุด | การ gate | Key |
|---|---|---|
| route `/cronjobs`, `/cronjobs/new`, `/cronjobs/:id/edit` | `PrivateRoute requiredPermission` + `feature` | `cronjob.read` + `cronjobs` (`App.tsx:531-551` — **permission เดียวกันบนทั้งสามเส้นทาง** `.manage` ไม่เคยถูกเช็คที่ระดับ route) |
| รายการ Sidebar "Cronjobs" | filter ด้วย `permission` + `feature` | `cronjob.read` / `cronjobs` (`platformNav.ts:36` กลุ่ม `navGroup.scheduling` ของตัวเอง) |
| รายการ: ปุ่ม Add Job (header และ empty state) | `<Can>` | `cronjob.manage` |
| รายการ: ไอคอน Start/Stop, Run Now, Edit, Delete ต่อแถว | ทั้ง cell action คืน `null` ถ้าไม่ `canManage` | `cronjob.manage` |
| หน้าแก้ไข: ปุ่ม Save ใน unsaved-changes bar | `<Can>` | `cronjob.manage` |
| หน้าแก้ไข: การเช็คสิทธิ์ของ `handleSave` เอง แยกจากปุ่ม Save | `hasPermission('cronjob.manage')` return ทันทีถ้าไม่ผ่าน | `cronjob.manage` |
| Backend gateway: `GET` (list / status / one) | `AppIdGuard('cronjob.findAll'\|'.status'\|'.findOne')` + `PlatformPermissionGuard` | `cronjob.read` |
| Backend gateway: `POST`/`PATCH`/`DELETE`/start/stop/execute | `AppIdGuard('cronjob.create'\|'.update'\|'.delete'\|'.start'\|'.stop'\|'.execute')` + `PlatformPermissionGuard` | `cronjob.manage` |
| `micro-cronjobs` เอง | **ไม่มี** — ไม่มีการยืนยันตัวตนใด ๆ เลย | ไม่มี |

สองเรื่องที่ควรพูดให้ชัด ทั้งคู่ยืนยันจากการอ่านโค้ดจริง ไม่ใช่เดาจากชื่อ permission:

1. **session ที่มีแค่ `cronjob.read` เปิดฟอร์มสร้างและเห็นทุกฟิลด์ของฟอร์มแก้ไขได้** ด้วยเหตุผลเดียวกับที่บันทึกไว้ใน [Database Pools](/th/platform/database-pools) §4: route guard เช็คแค่ permission read บนทั้งสามเส้นทาง และ `CronJobEdit.tsx` render โดยไม่สนใจ `cronjob.manage` เลย มัน submit ผ่านทางไหนไม่ได้ — ปุ่ม Save อยู่ใน `<Can permission="cronjob.manage">` และ `handleSave()` เช็ค `hasPermission('cronjob.manage')` เองแยกต่างหาก แล้ว return ก่อนจะ validate หรือเรียก API ป้องกันไว้ทั้งกรณี `Ctrl/Cmd+S` และ native form submit ที่ข้ามปุ่มที่ถูกซ่อนไป
2. **ความเป็นเจ้าของไม่ได้ gate อะไรเลย** session ที่มี `cronjob.manage` สั่ง start, stop, run, แก้ไข หรือลบงานที่ service อื่นสร้าง (มี `source_service`) ได้อย่างอิสระเท่ากับงานที่ platform สร้างเอง — ดู §3 frontend ยังคงมี branch รองรับ error code `409 FOREIGN_OWNED_JOB` พร้อม comment อธิบายว่า gateway ปัจจุบันไม่ส่ง code นี้แล้ว (ด่าน `assertPlatformOwned` ถูกถอดออกจาก `update`/`delete`) แต่เก็บ branch นี้ไว้เผื่อ gateway รุ่นเก่ายังทำงานอยู่ที่ไหนสักแห่ง ยืนยันกับ `platform_cronjobs.service.ts`: `update()`, `remove()`, และ `control()` แต่ละตัวมี comment "No ownership check" ชัดเจน

## 5. โมดูลที่เกี่ยวข้อง

- [Activity Events](/th/platform/activity-events) และ [Data Model](/th/platform/activity-events/data-model) §4 — ตารางเวลาและจุดบังคับใช้ของงาน `activity_rollup` และ `activity_retention` ถูกบันทึกไว้ที่นั่นอย่างละเอียด หน้านี้เห็นตรงกับข้อมูลนั้น (§3.2) และเพิ่มเติมแค่ว่าทั้งสองแถวบริหารจัดการได้จากคอนโซลนี้
- [Usage Analytics](/th/platform/usage-analytics) — แดชบอร์ดที่อ่านตารางที่ `activity_rollup` ดูแล ไม่เกี่ยวข้องกับหน้าจอของโมดูลนี้เอง
- [Report Templates](/th/platform/report-templates) — โมดูลที่ใช้ตั้งกำหนดการรายงานแบบทำซ้ำของ business unit หนึ่ง กำหนดการเหล่านั้นลงในตาราง `"CRONJOBS"."Cronjob"` เดียวกับที่คอนโซลนี้บริหาร สร้างผ่าน `reports.service.ts` ของ `backend-gateway` ไม่ใช่ผ่านฟอร์มสร้างของโมดูลนี้เอง
- [Database Pools](/th/platform/database-pools) §4 — โมดูลพี่น้องที่รูปแบบ permission read/manage และพฤติกรรม "session อ่านอย่างเดียวเปิดฟอร์มได้แต่บันทึกไม่ได้" ของหน้านี้เลียนแบบมาโดยตรง
- [Platform RBAC](/th/platform/rbac) — แคตตาล็อกสิทธิ์เบื้องหลัง `cronjob.read`/`cronjob.manage` และเหตุผลที่มีเฉพาะ Platform Admin ที่ถือ key ใดก็ตามในสองตัวนี้

## 6. แหล่งอ้างอิง

- `../carmen-platform/src/App.tsx:531-551` — สามเส้นทาง ทั้งหมด gate ด้วย `cronjob.read` เท่านั้น
- `../carmen-platform/src/components/nav/platformNav.ts:34-36` — รายการ sidebar และ comment ของ `navGroup.scheduling` ยืนยันเชิงโครงสร้างกับ nav array ทั้งไฟล์
- `../carmen-platform/src/constants/featureFlags.ts:67` — รายการ feature flag `cronjobs` กลุ่ม `navGroup.scheduling` เดียวกัน
- `../carmen-platform/src/pages/cronjobs/CronJobManagement.tsx` — หน้ารายการ อ่านแบบเต็ม
- `../carmen-platform/src/pages/cronjobs/CronJobEdit.tsx` — หน้าสร้าง/แก้ไข อ่านแบบเต็ม
- `../carmen-platform/src/pages/cronjobs/CronJobFilterSheet.tsx`, `CronScheduleField.tsx` — อ่านแบบเต็ม
- `../carmen-platform/src/pages/cronjobs/jobConfig/*.tsx` (คอมโพเนนต์ config เฉพาะทั้งหกประเภท) — อ่านแบบเต็ม
- `../carmen-platform/src/services/cronjobService.ts` — REST client และปัญหาการ encode filter ของ gateway ที่ต้องหลบ
- `../carmen-platform/src/types/index.ts:1660-1746` — `CronJob`, `CronJobWriteInput`, `CronJobConfig` และสมาชิกทั้งหก
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/{platform_cronjobs.controller.ts,platform_cronjobs.service.ts,swagger/request.ts}` — REST surface และ HTTP proxy ของ gateway อ่านแบบเต็ม
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.service.ts` — เส้นทางสร้างงานแบบ `by-source` ที่กำหนดการรายงานใช้ (`cronjobHttp`, `CRONJOB_SERVICE_URL`)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts:91-92` — คำอธิบายแคตตาล็อก `cronjob.read`/`cronjob.manage`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-role-permission.data.ts:11-15` — มีแค่ Platform Admin ที่ถือ `cronjob.*`
- `../micro-cronjobs/internal/model/cronjob.go`, `internal/executor/*.go`, `internal/scheduler/scheduler.go`, `internal/handler/cronjob_handler.go`, `internal/repository/cronjob_repo.go`, `cmd/server/main.go` — อ่านแบบเต็มทั้งหมด ดูรายการเต็มพร้อมจำนวนบรรทัดที่ [Data Model](/th/platform/cronjobs/data-model) §8
- `../micro-cronjobs/migrations/20260610120000_seed_dashboard_refresh_jobs.up.sql`, `20260730092930_seed_activity_rollup_job.up.sql`, `20260730093731_seed_activity_retention_job.up.sql` — งานที่ seed ไว้ตาม §3.2
- ยืนยันกับ `carmen-platform` HEAD `157a65e` (2026-09-04), `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `micro-cronjobs` HEAD `d17d8eb9bc3` (2026-09-04)
- `../carmen-platform-e2e/tests/` — ตรวจดูโดยตรง (`applications`, `auth`, `broadcast`, `business-units`, `changelog`, `clusters`, `dashboard`, `journeys`, `landing`, `news`, `permission-catalog`, `print-template-mapping`, `profile`, `report-templates`, `roles`, `super-admins`, `user-platform`, `users`) ไม่มีโฟลเดอร์ `cronjobs` HEAD `a8e3b31`

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/cronjobs/data-model) — ตารางฟิลด์เต็มของ `"CRONJOBS"."Cronjob"` (เป็นของ migration SQL ของ `micro-cronjobs` เองทั้งหมด ไม่ใช่ Prisma schema ของแพลตฟอร์ม) รูปแบบ config ของทุกประเภทงาน กลไก polling/retry/timezone ของ scheduler และคำตอบเต็มของ "run ที่ล้มเหลวจะไปโผล่ให้เห็นที่ไหน"
- [UI Screens](/th/platform/cronjobs/ui-screens) — พาชม `CronJobManagement` (รายการ ตัวกรอง สถิติสรุป export CSV) และ `CronJobEdit` (การ์ด basics/schedule/execution/type-config ตัวสร้างตารางเวลา การจัดการ version conflict) รวมถึงปฏิสัมพันธ์ระหว่างสิทธิ์อ่าน/ฟอร์มสร้างที่บันทึกไว้ใน §4 ข้างต้น
