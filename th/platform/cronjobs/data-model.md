---
title: งานตามกำหนดเวลา — โมเดลข้อมูล (Data Model)
description: ตารางฟิลด์เต็มของ "CRONJOBS"."Cronjob" (เป็นของ migration SQL ของ micro-cronjobs เอง ไม่ใช่ Prisma) รูปแบบ config ของแต่ละประเภทงาน กลไกของ scheduler และจุดที่จะเห็นว่า run ไหนล้มเหลว
published: true
date: '2026-09-06T22:00:00.000Z'
tags: book/platform, cronjobs, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# งานตามกำหนดเวลา — โมเดลข้อมูล (Data Model)

> **แหล่งความจริง:** อ่านสิ่งเหล่านี้ก่อนแก้ไขหน้านี้
> - `../micro-cronjobs/internal/model/cronjob.go` — struct ของ Go และการ map คอลัมน์แบบ GORM (อ่านแบบเต็ม)
> - `../micro-cronjobs/migrations/*.up.sql` — ทุกการเปลี่ยน DDL ของ `"CRONJOBS"."Cronjob"` ตามลำดับ (อ่านครบทั้งสิบไฟล์)
> - `../micro-cronjobs/internal/executor/{executor.go,report.go,notification.go,cleanup.go,dashboard.go,activity_rollup.go,activity_retention.go}` — เป้าหมาย dispatch ทั้งหก (อ่านแบบเต็ม)
> - `../micro-cronjobs/internal/scheduler/scheduler.go`, `cmd/server/main.go` — polling, retry, timezone (อ่านแบบเต็ม)
> - `../micro-cronjobs/internal/handler/cronjob_handler.go`, `internal/repository/cronjob_repo.go` — REST surface และเส้นทางเขียนระดับแถว (อ่านแบบเต็ม)
> - `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/{platform_cronjobs.controller.ts,platform_cronjobs.service.ts}` — ด่านสิทธิ์เดียวที่อยู่หน้าสิ่งข้างต้น (อ่านแบบเต็ม)
>
> ยืนยันกับ `carmen-platform` HEAD `157a65e` (2026-09-04), `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `micro-cronjobs` HEAD `d17d8eb9bc3` (2026-09-04) แต่ละ hash ยืนยันด้วย `git -C <repo> cat-file -e <hash>`

## 1. ภาพรวม

skeleton ที่ seed ไว้ของหน้านี้ชี้ไปที่ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` เป็นแหล่งข้อมูลของตารางนี้ **นั่นผิด และควรพูดตรง ๆ แทนที่จะแก้เงียบ ๆ:** การ grep หา `Cronjob`/`CRONJOBS` ใน Prisma schema ของแพลตฟอร์มไม่พบอะไรเลย ตารางนี้ไม่ใช่ Prisma model เลยด้วยซ้ำ — เป็นของ `../micro-cronjobs` เองทั้งหมด ผ่าน SQL migration ที่เขียนเอง ใน Postgres schema ของตัวเอง (`"CRONJOBS"`) อ่านและเขียนผ่าน `gorm` ไม่ใช่ Prisma ทุก claim ในหน้านี้อ้างอิงกลับไปที่ migration และซอร์สโค้ด Go ของ repo นั้น ไม่ใช่ shared schema ของแพลตฟอร์ม

`"CRONJOBS"."Cronjob"` ยังเป็นตาราง **ที่ใช้ร่วมกัน** ในอีกความหมายหนึ่งด้วย: แถวถูกเขียนทั้งจากฟอร์มสร้าง/แก้ไขของโมดูลนี้เอง และจาก backend service อื่นที่ทำงานในนามของ business unit หนึ่ง (ที่เด่นชัดที่สุดคือกำหนดการรายงานแบบทำซ้ำ — ดูหน้า landing §2) หนึ่งแถวคือหนึ่งงาน ไม่มีอะไรในตารางนี้ที่ผูกงานเข้ากับ business unit ที่มันน่าจะเป็นของ นอกจาก `bu_codes` ที่บังเอิญอยู่ใน `job_config` ของแถวนั้นเอง

## 2. Entity: `"CRONJOBS"."Cronjob"`

| คอลัมน์ (Postgres) | ฟิลด์ Go | ชนิด | ใครเขียน |
| --- | --- | --- | --- |
| `id` | `ID` | `UUID`, `default gen_random_uuid()` | DB ตอน insert |
| `name` | `Name` | `VARCHAR(255) NOT NULL` | ผู้ปฏิบัติงาน (ฟอร์มสร้าง/แก้ไข) หรือ service ที่สร้างงานนั้น |
| `description` | `Description` | `TEXT` nullable | ผู้ปฏิบัติงานหรือ service ที่สร้างงานนั้น |
| `"jobType"` | `JobType` | `VARCHAR(50) NOT NULL` | ตั้งครั้งเดียวตอนสร้าง; update DTO ไม่รับฟิลด์นี้ |
| `"cronExpression"` | `CronExpression` | `VARCHAR(100) NOT NULL` | ผู้ปฏิบัติงาน ผ่านตัวสร้างตารางเวลาหรือช่อง expression ดิบ |
| `"jobData"` | `JobConfig` | `JSONB` serialize เป็น `any` | ผู้ปฏิบัติงาน ผ่านฟิลด์ config เฉพาะประเภท (§3) |
| `"sourceService"` / `"sourceID"` | `SourceService` / `SourceID` | `VARCHAR(100)` / `VARCHAR(255)` nullable | เฉพาะ service ที่สร้างงานเท่านั้น — ถูกตัดออกจากทุก payload ที่การสร้าง/อัปเดตของคอนโซลนี้ส่งไป ดังนั้นการแก้ไขผ่านคอนโซลนี้จึงตั้งหรือล้างค่าไม่ได้เลย |
| `"isActive"` | `IsActive` | `BOOLEAN DEFAULT true` | ผู้ปฏิบัติงาน (ปุ่ม Start/Stop หรือ checkbox Active บนฟอร์ม) |
| `"lastRunAt"` / `"nextRunAt"` | `LastRunAt` / `NextRunAt` | `TIMESTAMPTZ` nullable | **scheduler เท่านั้น** หลังทุก run ตามกำหนดหรือสั่งรันเอง |
| `"lastError"` | `LastError` | `TEXT` nullable | scheduler เท่านั้น — ข้อความ `err.Error()` ของ run ที่ล้มเหลว หรือ `NULL` ที่ถูกล้างเมื่อ run ถัดไปสำเร็จ |
| `"runCount"` | `RunCount` | `INTEGER DEFAULT 0` | scheduler เท่านั้น เพิ่มขึ้นทุกครั้งที่พยายามรัน (สำเร็จหรือล้มเหลว) |
| `"notifyAt"` | `NotifyAt` | `VARCHAR(5)` nullable, `CHECK` บังคับรูปแบบ `HH:mm` | ผู้ปฏิบัติงาน — **เฉพาะ job type `report`**; executor อื่นไม่มีตัวไหนอ่านมันเลย |
| `"notifyDayOffset"` | `NotifyDayOffset` | `SMALLINT DEFAULT 0`, `CHECK` ระหว่าง 0 ถึง 7 | **ตั้งจาก UI ของคอนโซลนี้ไม่ได้เลย** — ดู §4.4 |
| `"maxRetries"` | `MaxRetries` | `INTEGER DEFAULT 0` | ผู้ปฏิบัติงาน (การ์ด Execution) |
| `"retryCount"` | `RetryCount` | `INTEGER DEFAULT 0` | scheduler เท่านั้น — เพิ่มขึ้นทุกครั้งที่ retry ล้มเหลว รีเซ็ตเป็น 0 เมื่อ run ถัดไปสำเร็จ |
| `"timeoutSeconds"` | `TimeoutSeconds` | `INTEGER DEFAULT 300` | ผู้ปฏิบัติงาน (การ์ด Execution) |
| `"docVersion"` | `DocVersion` | `INT NOT NULL DEFAULT 1` | เพิ่มขึ้นทุกครั้งที่มนุษย์แก้ไขผ่านเส้นทาง update; **ตั้งใจไม่เพิ่ม** จากการเขียนของ `UpdateLastRun` ของ scheduler เอง |
| `"createdAt"` / `"createdByID"` / `"updatedAt"` / `"updatedByID"` | — | `TIMESTAMPTZ` / `UUID` | คอลัมน์ audit มาตรฐาน |
| `"deletedAt"` | — | `TIMESTAMPTZ` nullable | soft delete — ทุก path การอ่านกรอง `"deletedAt" IS NULL` |

**ไม่มี unique constraint บน `name`** งาน active สองตัวใช้ชื่อซ้ำกันได้ ไม่มีอะไรในสคีมาหรือชั้น service ป้องกันไว้ (ต่างจาก [Database Pools](/th/platform/database-pools/data-model) §2 ที่บังคับความไม่ซ้ำของชื่อในระดับ application layer)

### 2.1 ประวัติสคีมา

ตารางนี้ถูกเปลี่ยนชื่อและปรับโครงสร้างมาสองครั้งตั้งแต่ migration แรก ทั้งหมดอยู่ในสาย migration ของ `micro-cronjobs` เอง:

1. `20260405120000_create_cronjob.up.sql` — รูปแบบแรก คอลัมน์เป็น `snake_case` อยู่ใน schema ใดก็ตามที่ `search_path` ชี้ไปตอนนั้น
2. `20260406010000_move_to_cronjobs_schema.up.sql` — ลบตารางนั้นและตาราง Prisma เดิมที่มีอยู่ก่อน สร้างใหม่ตรง ๆ ใน `"CRONJOBS"` และเพิ่ม `source_service`/`source_id` เพื่อรองรับความเป็นเจ้าของหลาย service
3. `20260406135707_update_field.up.sql` — เปลี่ยนชื่อตาราง `tb_cronjob` → `"Cronjob"` และทุกคอลัมน์จาก `snake_case` เป็น `camelCase` (รูปแบบในตารางด้านบน)
4. `20260610120000_seed_dashboard_refresh_jobs.up.sql` — seed แถว `dashboard_refresh` สามแถว (หน้า landing §3.2); ไม่มีการเปลี่ยนสคีมา
5. `20260730092930_seed_activity_rollup_job.up.sql` / `20260730093731_seed_activity_retention_job.up.sql` — seed สองงานของ Activity Events; ไม่มีการเปลี่ยนสคีมา
6. `20260824100000_add_notify_at_column.up.sql` — เพิ่ม `"notifyAt"` ย้ายค่าเดิม (ถ้ามี) ออกจาก `jobData->schedule_config->notify_time` (backfill เฉพาะที่ตรงรูปแบบ `HH:mm` อยู่แล้ว) แล้วลบ key นั้นออกจาก `jobData`
7. `20260902104533_add_doc_version.up.sql` — เพิ่ม `"docVersion"` (default 1) สำหรับ optimistic locking บนการแก้ไขของมนุษย์
8. `20260903100000_add_notify_day_offset.up.sql` — เพิ่ม `"notifyDayOffset"` (default 0, `CHECK 0..7`) ซึ่ง comment ของ migration เองระบุตรง ๆ ว่าเป็นข้อเท็จจริงของตารางเวลา ไม่ใช่ค่าที่เดาเอาตอนรัน — ดู §4.4

## 3. ประเภทงานและ Config ของแต่ละแบบ

`job_config` คือ JSON blob ที่แยกตาม `job_type` โดยไม่มีรูปร่างร่วมกันเลยระหว่างหกประเภท (union `CronJobConfig` ฝั่ง frontend เองแทบไม่มีชื่อฟิลด์ซ้ำกัน — `../carmen-platform/src/types/index.ts:1691-1697`) ทุกฟิลด์ด้านล่างเป็น optional ในระดับ struct ของ Go; executor ต่างหากที่บังคับว่าฟิลด์ไหนจำเป็นจริง ๆ ตอนรัน

### 3.1 `report`

| ฟิลด์ | จำเป็นตอนรันไหม? | หมายเหตุ |
|---|---|---|
| `template_id` | ไม่ | เทมเพลตรายงานที่จะ render |
| `bu_codes` | **ใช่** — `ReportExecutor.Execute()` คืน `"report job config missing bu_codes"` ถ้าว่าง | hint เดิมของคอนโซลเคยบอกว่า "เว้นว่างเพื่อทุก business unit" คัดลอกมาจากฟิลด์ของ `dashboard_refresh` — แก้แล้วใน UI ปัจจุบันให้บอกว่าจำเป็น |
| `format` | ไม่ | `pdf` / `excel` / `csv` / `json`; ยังเลือก path การส่งแบบเดิมด้วยเมื่อ `delivery.type` ไม่ถูกตั้ง |
| `filters` | ไม่ | คู่ key/value แบบอิสระ แก้ไขเป็นแถวในฟอร์มได้ |
| `recipients` | ไม่ (แต่ถ้าว่างจะไม่มีใครได้รับแจ้ง) | **user ID ไม่ใช่ email address** — ส่งตรงเป็น `audience.user_ids` ของ notification envelope; เวอร์ชันก่อนหน้าของฟิลด์นี้รับ email แบบพิมพ์เอง ซึ่งไม่เคย resolve ไปหาใครได้เลย |
| `delivery.type` | ไม่ | `file` (แบบเดิม — micro-report render และแจ้งเองทั้งหมด) หรือ `viewer_url` (สร้างลิงก์ที่แชร์ได้ executor ตัวนี้เป็นคนแจ้ง) |
| `delivery.viewer_endpoint` | ไม่ และ **ตั้งใจไม่มีให้แก้จากฟอร์ม** | Go executor เพิกเฉยต่อ URL แบบ relative (สิ่งที่ SPA จะเก็บไว้แทน — path proxy ของ Next.js ที่ backend นี้เข้าไม่ถึง) แล้วประกอบ URL ของตัวเองจาก `REPORT_SERVICE_URL` + `bu_code` ตัวแรก; ฟอร์มไม่มีช่องให้กรอกฟิลด์นี้เลย เพราะค่าที่แก้ได้จากเบราว์เซอร์ที่ควบคุม POST ฝั่ง server จะกลายเป็นช่องโหว่ SSRF ที่มีสิทธิ์แค่ `cronjob.manage` เป็นด่านเดียว |
| `notifications.{web,email,mail_source}` | ไม่ | `mail_source: "external"` สลับการส่งไปใช้ config SMTP `report_email` ของ business unit เองใน `tb_application_config`; ค่า default คือ `"internal"` (SMTP env ของ notification service เอง) |

นี่คือประเภทงาน**เดียว**ที่อ่านคอลัมน์ระดับแถว `notify_at`/`notify_day_offset` — executor อื่นไม่มีตัวไหนแม้แต่จะดูมัน `notify_at` (`HH:mm`) บวกกับ `notify_day_offset` (จำนวนวันที่บวกก่อน) รวมกันได้เป็นเวลาที่บอกผู้รับว่ารายงานพร้อมแล้ว ถ้าเวลาที่คำนวณได้นั้นผ่านไปแล้วตอนที่ run เสร็จ การแจ้งเตือนจะส่งทันทีแทนที่จะรอเต็มวัน (`scheduledNotifyAt()`, `report.go`)

### 3.2 `notification`

| ฟิลด์ | จำเป็นตอนรันไหม? | หมายเหตุ |
|---|---|---|
| `title` / `message` | ไม่ แต่ title/message ว่างก็ยังส่งอยู่ดี | ส่งตามที่พิมพ์; title ถูกตัดที่ 255 rune |
| `type` / `category` | ไม่ | `category` default เป็น `system` ถ้าไม่ตั้ง |
| `user_ids` | **ใช่** — `NotificationExecutor.Execute()` คืน `"notification job config missing user_ids"` ถ้าว่าง | แก้ hint แบบเดียวกับ `report.bu_codes` (§3.1) ให้ระบุว่าจำเป็น |

### 3.3 `cleanup`

| ฟิลด์ | จำเป็นตอนรันไหม? | หมายเหตุ |
|---|---|---|
| `action` / `type` / `older_than` | ไม่ — ไม่มีการ validate เลย | executor แค่ log ค่าทั้งสามแล้วคืน `nil` |

**ประเภทงานนี้ไม่ทำอะไรเลย** `CleanupExecutor.Execute()` (`cleanup.go` อ่านแบบเต็ม) เป็นฟังก์ชันเก้าบรรทัดที่เนื้อหาทั้งหมดคือ log แบบมีโครงสร้างหนึ่งบรรทัด ตามด้วย `// TODO: implement cleanup logic per type` และ `return nil` งาน `cleanup` ที่ตั้งไว้ผ่านคอนโซลนี้จะรันตามกำหนดเวลา log config ของตัวเอง รายงานว่าสำเร็จ (`last_error` ยังเป็น `NULL`, `run_count` เพิ่มขึ้น) และไม่ลบอะไรเลย ข้อความนี้อ่านตรงจากซอร์สโค้ด executor ไม่ได้เดาจากการไม่พบการเรียกลบที่ไหนอื่น — ฟังก์ชันสั้นพอที่จะอ่านเต็มและยืนยันได้เอง

### 3.4 `dashboard_refresh`

| ฟิลด์ | จำเป็นตอนรันไหม? | หมายเหตุ |
|---|---|---|
| `bu_codes` | ไม่ — ว่างคือทุก business unit ที่ active | ประเภทงานเดียวที่ hint "เว้นว่างคือทุกหน่วย" ของคอนโซลถูกต้องจริง |
| `tier` | ไม่ — ว่างคือทุก tier | `operational` / `breakdown` / `matrix` สอดคล้องกับกลุ่ม materialized view ของ `micro-data` |

HTTP client ของ executor มี timeout 5 นาทีของตัวเอง (แยกจาก `timeout_seconds` ของแถวงาน) อธิบายไว้ใน comment ของตัวเองว่าจำเป็นเพราะ "การกวาดรีเฟรช materialized view ของทุก tenant อาจใช้เวลานาน" error รายตัวของ materialized view ที่ส่งกลับมาใน response body ของ `micro-data` ถูก log เป็น warning เท่านั้น **ไม่** ทำให้งานล้มเหลวหรือถูกตั้งเป็น `last_error` — ดู §5.4

### 3.5 `activity_rollup`

| ฟิลด์ | จำเป็นตอนรันไหม? | หมายเหตุ |
|---|---|---|
| `days_back` | ไม่ — default 2 | จำนวนวัน UTC ย้อนหลังที่จะคำนวณใหม่; ใช้ 2 แทน 1 เพื่อให้ event ที่มาช้าจากเมื่อวานยังถูกรวมเข้า bucket รายวันที่ถูกต้อง |

เส้นทางการเขียนเต็มและจุดบังคับใช้บันทึกไว้ที่ [Activity Events — Data Model](/th/platform/activity-events/data-model) §4.2; หน้านี้เห็นตรงกับข้อมูลนั้น (หน้า landing §3.2)

### 3.6 `activity_retention`

| ฟิลด์ | จำเป็นตอนรันไหม? | หมายเหตุ |
|---|---|---|
| `retention_days` | ไม่ — default 365 | แถวที่เก่ากว่านี้ตาม `server_ts` มีสิทธิ์ถูกลบ |
| `batch_size` | ไม่ — default 10000 | จำนวนแถวที่ลบต่อรอบ `DELETE ... LIMIT` วนจนกว่าจะลบได้ 0 แถวในรอบหนึ่ง |

เส้นทางการเขียนเต็มและจุดบังคับใช้บันทึกไว้ที่ [Activity Events — Data Model](/th/platform/activity-events/data-model) §4.1; หน้านี้เห็นตรงกับข้อมูลนั้น (หน้า landing §3.2)

## 4. พฤติกรรมของ Scheduler

### 4.1 Polling และการ reconcile

`micro-cronjobs` เก็บทุกงาน active (`isActive = true AND "deletedAt" IS NULL`) ไว้ใน scheduler `go-cron` (`gocron/v2`) แบบ in-memory loop เบื้องหลังจะโหลดชุดนี้จากฐานข้อมูลใหม่ทุกหนึ่งนาที (`pollInterval = 1 * time.Minute`, `scheduler.go`) และ reconcile สามแบบ:

- งานที่ไม่อยู่ในชุด active แล้วถูกลบออกจาก scheduler ใน memory
- งานที่มีอยู่แต่ยังไม่ถูกตั้งตารางถูกเพิ่มเข้าไป
- งานที่ **cron expression, `job_config`, `notify_at` หรือ `notify_day_offset`** เปลี่ยนไปตั้งแต่ poll ครั้งก่อนจะถูกลบแล้วเพิ่มกลับด้วยค่าใหม่ — `gocron` ไม่มี API "update ตารางเวลาของงานที่กำลังรัน" แบบแก้ในที่ นี่จึงเป็นวิธีเดียวที่การแก้ไขจะมีผล การเปรียบเทียบใช้ fingerprint (`revisionOf()`) สร้างจาก cron string บวก SHA-256 ของ `job_config` ที่ encode เป็น JSON — `encoding/json` เรียง key ของ map ให้เอง ดังนั้น hash จึงคงที่ข้าม poll ไม่ว่าลำดับ key จะเป็นอย่างไร

การเรียก create, update, delete, start หรือ stop ทุกครั้งจาก gateway ยังสั่ง `ForceSync()` — การ reconcile แบบเดียวกันแบบ asynchronous ทันที ดังนั้นในทางปฏิบัติการเปลี่ยนแปลงที่บันทึกแล้วมักถูกนำไปใช้ก่อนรอบ poll ตามกำหนดถัดไปนานมาก มันเป็น fire-and-forget (`go s.syncJobs()`) ดังนั้น HTTP response ที่คอนโซลได้รับจึงไม่มีการยืนยันว่า scheduler ใน memory ได้รับการเปลี่ยนแปลงนั้นแล้วจริง

### 4.2 Timezone

resolve **ครั้งเดียว** ตอน process เริ่มทำงาน (`cmd/server/main.go:142-166`): timezone แบบ IANA ที่ตั้งไว้ของ business unit หลัก (`BusinessUnitRepo.PrimaryTimezone()`) fallback ไปที่ `DEFAULT_TIMEZONE` (env, default `Asia/Bangkok`) ถ้าการค้นหานั้น error หรือคืนค่าว่าง และ fallback ไปที่ UTC ถ้าชื่อที่ resolve ได้โหลดไม่สำเร็จ โซนที่เลือกได้จะกลายเป็นทั้ง `time.Local` ของทั้งโปรเซส และโซนที่ cron expression ทุกตัวถูกตีความ — รวมถึงงานที่ seed ไว้ในหน้า landing §3.2 ที่เวลา "03:30"/"04:00" อยู่ในโซนนี้ ปกติคือ Asia/Bangkok สอดคล้องและยืนยันอย่างเป็นอิสระกับกรอบ "HQ BU timezone" ใน [Activity Events — Data Model](/th/platform/activity-events/data-model) §4.1

### 4.3 Retry, Timeout, ความขนาน

- **Timeout:** `timeout_seconds` (ฟิลด์ของแถว default 300 วินาที) ครอบการรันด้วย `context.WithTimeout` ทั้งการรันตามกำหนดเวลา (task closure ของ `addJob`) และการสั่งรันเอง ("Run Now" — goroutine แยกของ handler ใช้ค่าเดียวกันทุกประการ)
- **Retry:** เมื่อล้มเหลว `retryJob()` จะลองใหม่แบบ synchronous — บล็อก goroutine เดิม ไม่ได้คิวรอบรันใหม่ — สูงสุดตาม `max_retries` ครั้ง โดยรอ `attempt² × 10 วินาที` ระหว่างแต่ละครั้ง (10, 40, 90, 160 วินาที ...) ทุกครั้งที่ลอง ไม่ว่าสำเร็จหรือล้มเหลว จะเขียน `last_run_at`/`last_error`/`retry_count` ลงแถวทันที ดังนั้น `retry_count` ของงานหนึ่งจึงสะท้อนจำนวนครั้งที่ retry ใน run ล่าสุด และถูกรีเซ็ตเป็น 0 ทันทีที่มีครั้งใดครั้งหนึ่ง (ครั้งแรกหรือ retry) สำเร็จ
- **ความขนาน:** `gocron.WithLimitConcurrentJobs(5, gocron.LimitModeWait)` จำกัดทั้งโปรเซสให้รันพร้อมกันได้สูงสุด 5 งาน; งานที่ 6 ที่ถึงกำหนดจะรอคิวแทนที่จะรันพร้อมกับงานอื่น
- **การรันเอง** (`POST /:id/execute`): แยกตัวออกจาก context ของ HTTP request ขาเข้า โดยเจตนา เพื่อไม่ให้การปิดแท็บเบราว์เซอร์หรือ request timeout ไปยกเลิกการ render รายงานหรือส่ง notification ที่กำลังทำอยู่ แล้วรันใน background goroutine และคืน `{"message": "execution triggered"}` ก่อนที่จะรู้ผลลัพธ์

## 5. จุดที่จะเห็นว่า run ไหนล้มเหลว

นี่คือคำตอบที่หน้า landing ส่งต่อมาให้ส่วนนี้ (§3.5 ที่นั่น) อ่านจากบนลงล่าง นี่คือทุกที่ที่หลักฐานของ run ที่ล้มเหลวมีอยู่ และแต่ละที่แสดงหรือไม่แสดงอะไร

### 5.1 แถวในฐานข้อมูล (`last_error`, `retry_count`, `run_count`)

`CronJobRepo.UpdateLastRun()` ถูกเรียกหลัง**ทุก**การรัน — ตามกำหนด ลองใหม่ หรือสั่งรันเอง — และตั้งค่า `last_run_at`, `next_run_at`, เพิ่ม `run_count` และตั้ง `last_error` เป็นข้อความ error ที่ล้มเหลว หรือ `NULL` เมื่อสำเร็จ (รีเซ็ต `retry_count` เป็น 0 กรณีสำเร็จ เพิ่มขึ้นกรณีล้มเหลว) การเรียกนี้ตั้งใจไม่แตะ `doc_version` เลย ดังนั้นฟอร์มแก้ไขงานหนึ่งจะไม่ถูกปฏิเสธว่า "มีคนแก้ไปแล้ว" เพียงเพราะ scheduler รันมันอยู่เบื้องหลัง — รายละเอียดเรื่องการควบคุมความขนานนี้ระบุไว้ชัดเจนใน comment ของ repository เอง

### 5.2 หน้ารายการ (`CronJobManagement`, `/cronjobs`)

- **คอลัมน์ Last Run:** เวลาสัมพัทธ์ (เช่น "2 ชั่วโมงที่แล้ว" tooltip แสดง timestamp แบบเต็ม) บวกไอคอนสามเหลี่ยมเตือนเล็ก ๆ ที่ render **เฉพาะเมื่อ `last_error` ไม่ว่าง** ซึ่ง tooltip ของมันเก็บข้อความ error ดิบไว้ตรง ๆ นี่คือที่เดียวในคอนโซลที่มนุษย์อ่านข้อความความล้มเหลวจริงได้
- **สถิติสรุป "With Errors":** ตัวนับเฉพาะในแถบสถิติเหนือตาราง (`items.filter(j => !!j.last_error).length`) นับเฉพาะแถวที่โหลดอยู่บนหน้านั้น — caption ของแถบเองระบุไว้ชัด — ไม่ใช่ทุกงานที่กำลังล้มเหลวทั้งตาราง ไม่มี filter "มี error" ฝั่ง server ให้เห็นทุกความล้มเหลวพร้อมกัน (§6)
- **ไม่มีประวัติ run** แถวหนึ่งเก็บผลลัพธ์ของ run ล่าสุดเพียงครั้งเดียวเท่านั้น งานที่ล้มเหลวสองครั้งแล้วสำเร็จในครั้งที่สาม จะแสดง `last_error` สะอาด (`NULL`) และ `retry_count` เป็น 0 ทันทีที่ครั้งสุดท้ายสำเร็จ — สองความล้มเหลวก่อนหน้าไม่เหลือร่องรอยให้เห็นบนหน้านี้เลยเมื่อ run โดยรวมสำเร็จแล้ว

### 5.3 หน้าแก้ไข (`CronJobEdit`, `/cronjobs/:id/edit`)

**ไม่แสดงเลยแม้แต่น้อย** การ์ด "History" ของหน้านี้แสดงแค่ `created_at`/`created_by_id`/`updated_at`/`updated_by_id` ผ่าน `AuditMeta` — บอกว่าใครแก้ไข *การตั้งค่า* ของแถวล่าสุด ไม่ใช่อะไรเกี่ยวกับ *การรัน* ของมัน `last_run_at`, `next_run_at`, `last_error`, และ `run_count` ล้วนมีอยู่ในเรคคอร์ดที่โหลดมา (`jobRecord` มองเห็นได้ใน dev-only debug panel) แต่ไม่ถูก render ที่ไหนบนหน้านี้เลย tester ที่เปิด Edit เพื่อหวังจะรู้ว่าทำไมงานล้มเหลวจะไม่พบคำตอบตรงนั้น

### 5.4 สิ่งที่ไม่ถูกส่งเป็น `last_error` เลย

executor ของ `dashboard_refresh` ถือว่า HTTP call ไป `micro-data` ที่สำเร็จคือความสำเร็จของงาน แม้ว่า array `errors` ใน response body เองจะไม่ว่างก็ตาม — ความล้มเหลวรายตัวของ materialized view ถูก log เป็น warning (comment ของ `DashboardRefreshExecutor.Execute()` เอง: "the endpoint itself succeeded and the next scheduled run retries naturally") แต่ไม่เคยไปถึง `last_error` เลย ความล้มเหลวบางส่วนแบบนี้จึงมองไม่เห็นในคอนโซลนี้เลย ไม่ใช่ไอคอน Last Run ไม่ใช่สถิติ "With Errors" ตรวจพบได้แค่ใน log ของ Go service เองหรือ OpenTelemetry trace (§5.5)

### 5.5 Observability (SigNoz ผ่าน OpenTelemetry)

`Execute()` ของ `executor.go` เปิด root span หนึ่งอันต่อการรันหนึ่งครั้ง (`cronjob <job_type>`) และเรียก `span.RecordError(err)` กับ `span.SetStatus(codes.Error, ...)` เมื่อล้มเหลว นี่คือที่เดียวที่มี trace แบบเต็มทั้งเวลาและ stack ของ run ที่ล้มเหลวหนึ่งครั้ง และต้องเข้าถึง SigNoz instance ที่ตั้งค่าไว้ — เกินเอื้อมสำหรับ tester ที่ใช้แค่คอนโซลของแพลตฟอร์ม

### 5.6 สัญญาณความล้มเหลวอีกอย่างที่เป็นอิสระ: scheduler status ไม่ตรงกัน

แถบสรุปของหน้ารายการแสดง **"Active in Scheduler"** จาก `GET /api/cronjobs/status` → `scheduler.ActiveJobCount()` — ตัวนับแบบสดใน memory ที่คำนวณแยกจากตัวเลข "Running"/"Stopped" ที่มาจาก DB บนแถบเดียวกันโดยเจตนา comment ของคอมโพเนนต์เองระบุเหตุผล: ความไม่ตรงกันระหว่างสองค่า (เช่น "Running: 12" จาก DB กับ "Active in Scheduler: 9") คือหลักฐานว่า scheduler process ค้างหรือตามหลังรอบ poll ของมันเอง ไม่ใช่ bug ของการแสดงผลที่ต้องแก้ให้ตรงกัน

## 6. กรณีขอบ

| สถานการณ์ | สิ่งที่เกิดขึ้นจริง | แหล่งที่มา |
|---|---|---|
| งาน `cleanup` ถูกตั้งเวลาและรัน | log config ของตัวเอง รายงานว่าสำเร็จ ไม่ลบอะไรเลย — executor ไม่มีการ implement | `cleanup.go` (เต็ม, `// TODO`) |
| `dashboard_refresh` ล้มเหลวบางส่วน (บาง materialized view error) | งานยังรายงานว่าสำเร็จ; `last_error` ยังเป็น `NULL`; error รายตัวถูก log เท่านั้น ไม่ถูกส่งขึ้นคอนโซล | `dashboard.go` (§5.4) |
| ผู้ปฏิบัติงานต้องการเปลี่ยนวันที่ผู้รับงาน `report` ถูกแจ้งเทียบกับวันที่รัน ให้เป็นคนละวันกับวันรัน | ทำไม่ได้ — ฟอร์มสร้าง/แก้ไขไม่มีช่องให้ตั้ง `notify_day_offset`; ทุกงานที่สร้างผ่านคอนโซลนี้คงค่า default ของคอลัมน์ไว้ (0, แจ้งวันเดียวกับที่รัน) แม้ backend และ executor จะรองรับ 0–7 เต็มที่ | `types/index.ts:1735-1746` (ไม่มีฟิลด์ใน `CronJobWriteInput`), `CronJobEdit.tsx` (ไม่มีช่องกรอกให้) |
| session ที่มีแค่ `cronjob.read` เปิด `/cronjobs/new` | เห็นและกรอกทุกฟิลด์ของฟอร์มสร้างได้; submit ไม่ได้ — Save ไม่ถูก render และ `handleSave()` return ก่อนเรียก API | `CronJobEdit.tsx:171`, `App.tsx:531-551` |
| gateway ตอบ `409 FOREIGN_OWNED_JOB` | frontend ยังมี branch รองรับ code นี้อยู่ แต่ `update()`/`delete()` ของ gateway ปัจจุบันไม่มีการตรวจความเป็นเจ้าของแล้ว จึงสร้าง code นี้ไม่ได้ — เป็นโค้ดตาย เก็บไว้เพื่อรองรับ gateway รุ่นเก่า | `CronJobEdit.tsx` (comment), `platform_cronjobs.service.ts` ("No ownership check") |
| ผู้ปฏิบัติงานต้องการดูทุกงานที่กำลังล้มเหลวทั้งตาราง ไม่ใช่แค่หน้าที่โหลดอยู่ | ไม่มี filter ฝั่ง server สำหรับ "มี `last_error`"; สถิติ "With Errors" และคอลัมน์ที่เรียงได้ไม่มีคอลัมน์นี้เลย | `CronJobManagement.tsx` (§5.2), `platform_cronjobs.service.ts` (`SORTABLE` ไม่มีคอลัมน์ error) |
| ตารางเวลาถูกแก้และบันทึก | ถูกนำไปใช้กับ scheduler ใน memory ตอน `ForceSync()` ถัดไป (มักเกือบทันที) หรือถ้าไม่สำเร็จก็รอบ poll ถัดไป (นานสุดประมาณ 1 นาที) — ไม่มีการยืนยันทั้งสองแบบส่งกลับมาที่เบราว์เซอร์ | `scheduler.go` (`ForceSync`, `syncJobs`) |
| ผู้เรียกเข้าถึง `micro-cronjobs` โดยตรง ข้าม gateway | ทุก operation สำเร็จหมด — service นี้ไม่มีการยืนยันตัวตนของตัวเองเลย | `platform_cronjobs.controller.ts` (comment), `platform_cronjobs.service.ts` (comment) |

## 7. ข้อเสนอแนะ

- **implement `CleanupExecutor` จริง หรือเอา `cleanup` ออกจากรายการ job-type ของฟอร์มสร้าง** จนกว่ามันจะทำอะไรสักอย่าง — สภาพปัจจุบันผู้ปฏิบัติงานตั้งงานที่รายงานว่าสำเร็จเงียบ ๆ ตลอดโดยไม่ลบอะไรเลยได้
- **ส่ง array error รายตัวของ `dashboard_refresh` ขึ้นคอนโซล** หรืออย่างน้อยตั้ง `last_error` เมื่อ array นั้นไม่ว่าง เพื่อให้ความล้มเหลวบางส่วนของการรีเฟรช materialized view มองเห็นได้โดยไม่ต้องเปิด log หรือ trace
- **เพิ่มช่อง `notify_day_offset` ในส่วนตารางเวลาของงาน report** ควบคู่กับช่อง `notify_at` ที่มีอยู่แล้ว — backend และ executor รองรับช่วง 0–7 เต็มที่อยู่แล้ว มีแค่คอนโซลเท่านั้นที่ตั้งค่านี้ไม่ได้
- **เพิ่ม filter "มี error" ฝั่ง server** (หรืออย่างน้อยเรียงตาม `last_error IS NOT NULL`) เพื่อให้ผู้ปฏิบัติงานหาทุกงานที่กำลังล้มเหลวทั้งตารางได้ ไม่ใช่แค่หน้าที่โหลดอยู่
- **พิจารณาทำตารางประวัติ run** แม้จะเป็นแค่หน้าต่างสั้น ๆ เพราะสคีมาปัจจุบันเก็บผลลัพธ์ของ run ล่าสุดเพียงครั้งเดียวต่องาน — งานที่เคยล้มเหลวก่อนจะสำเร็จล่าสุด ดูไม่ต่างจากงานที่ไม่เคยล้มเหลวเลยในปัจจุบัน

## 8. อ้างอิง

- `../micro-cronjobs/internal/model/cronjob.go` (139 บรรทัด) — struct ของ Go ชื่อตาราง และ config struct ของทุกประเภทงาน
- `../micro-cronjobs/internal/executor/executor.go` (85 บรรทัด), `report.go` (422 บรรทัด), `notification.go` (102 บรรทัด), `cleanup.go` (40 บรรทัด), `dashboard.go` (98 บรรทัด), `activity_rollup.go` (80 บรรทัด), `activity_retention.go` (64 บรรทัด) — อ่านแบบเต็มทั้งหมด
- `../micro-cronjobs/internal/scheduler/scheduler.go` (345 บรรทัด) — polling, reconciliation, retry, `ForceSync`, `ExecuteNow`
- `../micro-cronjobs/internal/handler/cronjob_handler.go` (451 บรรทัด) — REST surface (`list`, `status`, `getByID`, `create`, `update`, `delete`, `start`, `stop`, `execute`, `getBySource`, `updateBySource`, `deleteBySource`)
- `../micro-cronjobs/internal/repository/cronjob_repo.go` (207 บรรทัด) — `UpdateLastRun`, `Update` แบบ optimistic-lock, `FindActive`/`FindBySource`
- `../micro-cronjobs/cmd/server/main.go` (166 บรรทัด) — การประกอบระบบ การ resolve timezone
- `../micro-cronjobs/migrations/{20260405120000,20260406010000,20260406135707,20260610120000,20260730092930,20260730093731,20260824100000,20260902104533,20260903100000}_*.up.sql` — migration ทั้งสิบไฟล์ อ่านแบบเต็ม
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/platform_cronjobs.service.ts` — comment เรื่องการถอดการตรวจความเป็นเจ้าของ (§5, กรณีขอบ)
- `../carmen-platform/src/types/index.ts:1660-1746` — รูปร่างชนิดข้อมูลฝั่ง frontend เทียบกับ struct ของ Go ทีละฟิลด์
- [Activity Events — Data Model](/th/platform/activity-events/data-model) §4 — ข้อมูล `activity_rollup`/`activity_retention` ที่หน้านี้เห็นตรงกัน
- [Database Pools — Data Model](/th/platform/database-pools/data-model) §2 — การบังคับความไม่ซ้ำของชื่อของโมดูลพี่น้อง เทียบกับที่ §2 ด้านบน
