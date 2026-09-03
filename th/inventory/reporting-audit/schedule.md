---
title: กำหนดการรายงาน (Report Schedule)
description: กำหนดการรายงานเกิดซ้ำ — หน้าจอที่ทำได้เพียง สร้าง/รายการ/ลบ เท่านั้น อยู่เบื้องหลังด้วยตาราง cron-job แบบ generic ใน service micro-cronjobs แยกต่างหาก ไม่ใช่ tb_report_schedule ของ tenant schema (ซึ่งไม่มีการอ้างอิงจากโค้ดเลย)
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, schedule, automation, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# กำหนดการรายงาน (Report Schedule)

> **At a Glance**
> **Route:** `/report/schedules` &nbsp;·&nbsp; **เจ้าของ:** ผู้ใช้ที่ authenticate แล้วคนใดก็ได้ที่มี BU context — ไม่พบ gate เฉพาะ schedule-admin &nbsp;·&nbsp; **ที่เก็บจริง:** ตาราง `"CRONJOBS"."Cronjob"` ใน service **micro-cronjobs** แยกต่างหาก, `job_type = "report"` &nbsp;·&nbsp; **หน้าจอ:** รายการ + dialog สร้าง + ลบ เท่านั้น — ไม่มีหน้ารายละเอียด, ไม่มีการแก้ไข, ไม่มี pause toggle, ไม่มี test-run &nbsp;·&nbsp; `tb_report_schedule` ของ tenant schema มี **การอ้างอิงจากโค้ดเป็นศูนย์**

![กำหนดการรายงาน (Report Schedule) screen](/screenshots/reporting-audit/schedule.png)

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

หน้านี้ฉบับก่อนหน้าบันทึก `tb_report_schedule` (tenant schema) ว่าเป็นตารางที่เก็บ schedule จริง พร้อมหน้ารายละเอียดที่มี cron-expression builder, Active toggle, action Test Run และ recipients picker แบบมี type (`email`/`user`/`sftp`) การค้นหาโค้ดทั่ว `carmen-turborepo-backend-v2/apps` พบว่า **ไม่มีการอ้างอิง `tb_report_schedule` เลย** นอกเหนือจากการประกาศ Prisma model ของมันเอง — เป็นตารางที่ตายแล้ว รูปแบบเดียวกับที่ยืนยันแล้วสำหรับ `tb_attachment` และตระกูล `tb_widget_*` เดิม

ที่เก็บจริงคือคอมเมนต์ในโค้ดของ `reports.service.ts` เอง: *"micro-report no longer owns schedules; they live in micro-cronjob as rows in the Cronjob table with `job_type="report"` and `source_service="micro-report"`."* `Cronjob` เป็นตาราง scheduler แบบ **generic** (ใช้ร่วมกับ `job_type = "notification"`, `"cleanup"`, `"dashboard_refresh"` ด้วย) อยู่ใน Postgres schema/database ของตัวเองแยกต่างหากทั้งหมดจาก tenant และ platform Prisma schema ทุกข้อกล่าวอ้างระดับ UI ด้านล่างถูกตรวจสอบเทียบกับ `schedule-component.tsx`, `create-schedule-dialog.tsx` และ hook `hooks/use-report-schedule.ts` — frontend **ไม่มีหน้ารายละเอียด, ไม่มี endpoint แก้ไข/อัปเดต, ไม่มี pause toggle และไม่มี test-run** เลย

## 1. ภาพรวมและผู้ใช้งาน

Report Schedule กำหนด **เวลาที่รายงานจะรันและใครได้รับแจ้งเตือน** หน้าจอที่ `/report/schedules` เป็นรายการแบบแบน (ชื่อ, ประเภทรายงาน, รูปแบบ, ความถี่, badge active, next/last run, ลบ) บวก dialog **Create Schedule** เดียว ไม่มีหน้ารายละเอียดจากการคลิกแถวและไม่มี update mutation ใน frontend — `useReportSchedules` (รายการ), `useCreateReportSchedule` (สร้าง) และ `useDeleteReportSchedule` (ลบ) คือสามการทำงานเดียวที่เชื่อมไว้

Schedule ทุกตัวที่สร้างผ่าน UI ส่งมอบผ่าน **ลิงก์ viewer ไม่ใช่ไฟล์ที่ render แล้ว**: create dialog ตั้งค่าคงที่ `format: "viewer_url"` และ `delivery: { type: "viewer_url", viewer_endpoint: ... }` ทุกครั้งที่ submit — ไม่มีตัวเลือกรูปแบบไฟล์ เมื่อ schedule fire, `ReportExecutor` ของ `micro-cronjobs` จะสร้าง viewer URL ใหม่ (`POST .../report/viewer`) แล้วส่งไปยังผู้รับที่เลือกเป็นการแจ้งเตือน in-app/email (`POST .../api/internal/notifications`) — **ไม่** render หรือแนบไฟล์ PDF/Excel/CSV เส้นทางการส่งมอบแบบ "file" (legacy) มีอยู่จริงใน executor (เรียก `generate-async` ของ micro-report) แต่ไม่มี UI ปัจจุบันเข้าถึงได้ เพราะไม่มีที่ไหนตั้ง `delivery.type` เป็นอย่างอื่นนอกจาก `"viewer_url"`

**กลุ่มผู้ใช้:** ผู้ใช้ที่ authenticate แล้วและมี BU context คนใดก็ได้สามารถสร้างและลบ schedule ของตนเองผ่านหน้าจอนี้ — ไม่พบสิทธิ์ schedule-admin ที่แยกออกมาบน endpoint schedule ของ `reports.controller.ts` (มี `KeycloakGuard` + header `X-App-Id` เหมือน endpoint report อื่น ๆ ไม่ใช่ role check ที่แคบกว่า)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง schedule | `/report/schedules` → **Create Schedule** | เลือก report template, ความถี่ (รายวัน/รายสัปดาห์/รายเดือน) + เวลา, filter เฉพาะ template แบบเลือกได้, ช่องทางแจ้งเตือน (checkbox web/email) และผู้รับ (multi-select ของผู้ใช้) |
| ตั้งความถี่ | Create dialog → select **Frequency** + ตัวเลือกเวลา | รายสัปดาห์เพิ่ม multi-toggle จันทร์–อาทิตย์; รายเดือนเพิ่ม multi-toggle 1–31 **ไม่มีช่อง cron expression ดิบ** ใน UI — backend derive `cron_expression` จาก `schedule_config` เมื่อไม่ได้ส่งมา |
| เลือกผู้รับ | Create dialog → **Recipients** | checkbox multi-select บน `useAllUsers()` — user ID ธรรมดา ไม่ใช่ entry แบบมี type `email`/`user`/`sftp` |
| ดูการ fire ล่าสุด/ครั้งหน้า | รายการ → คอลัมน์ **Last Run** / **Next Run** | เติมจาก `lastRunAt`/`nextRunAt` ของแถว `Cronjob` |
| ลบ schedule | รายการ → ไอคอน trash บนแถว | dialog ยืนยัน แล้วตามด้วย `DELETE .../schedules/:id` |
| **ไม่มีใน UI เลย** | — | การแก้ไข schedule ที่มีอยู่, pause/reactivate (`is_active` แสดงผลอย่างเดียว), cron-expression builder และการ "run now" แบบ manual |

## 3. คำถามที่พบบ่อย

| อาการ / คำถาม | สาเหตุ / คำตอบ | การจัดการ |
|---|---|---|
| ทำไมแก้ไข schedule ไม่ได้? | ไม่มี update endpoint เปิดไว้โดย `reports.controller.ts` — มีแค่สร้าง, รายการ และลบ | ลบแล้วสร้างใหม่ |
| ทำไม pause schedule ไม่ได้? | ไม่มี toggle mutation ใน frontend เลย; badge Active เป็นการแสดงผลอย่างเดียว | ลบถ้าไม่ต้องการให้ fire อีก |
| ทำไมรายงานที่ fire มาถึงเป็นลิงก์เสมอ ไม่ใช่ไฟล์? | create dialog ส่ง `format: "viewer_url"` เสมอ — เส้นทางการส่งมอบแบบ "file" (render PDF/Excel/CSV) มีอยู่ใน executor แต่ไม่มีที่ไหนใน UI เลือกได้ | เปิดลิงก์ viewer; ดาวน์โหลดจากที่นั่นถ้า viewer รองรับ |
| ถ้ามี scheduler สองตัวรันพร้อมกันจะเกิดอะไร? | scheduler ของ `micro-cronjobs` ใช้ Redis lock แบบ `SET NX` (key `cronjob:lock:<job-id>`, TTL 5 นาที) ต่อการ execute หนึ่งครั้งผ่าน distributed locker ของ `go-cron` — execute ครั้งเดียวแน่นอนข้าม replica | — |
| Schedule รันใน timezone ไหน? | `time.Location` ของ process scheduler เอง (default `time.Local` ถ้าไม่ตั้ง) — **ไม่มีฟิลด์ timezone ต่อ schedule** บน model `Cronjob` | ยืนยัน timezone ที่ตั้งค่าของ process scheduler กับทีม Ops แทนการสันนิษฐานว่าควบคุมได้ต่อ schedule |
| การ fire ที่พลาด (downtime) ถูกตามให้ทันไหม? | ไม่มีฟิลด์ misfire-policy บน model `Cronjob` — `go-cron` เพียงกลับมา poll ต่อเมื่อ restart; ไม่พบการตั้งค่า catch-up/skip | — |
| ใครสร้าง schedule ได้? | ผู้ใช้ที่ authenticate แล้วใน BU context คนใดก็ได้ — ไม่พบ gate schedule-admin ที่แยกออกมา | — |

## 4. กรณีพิเศษ

- **`is_active` เป็น `true` เสมอตอนสร้างและไม่เคยถูก toggle** `createSchedule()` ของ `reports.service.ts` ตั้ง `is_active: true` แบบ hardcode ในทุก payload ที่ส่งไป `micro-cronjobs`; ไม่มีอะไรใน UI ที่เข้าถึงได้เปลี่ยนค่านี้เลย
- **ผู้รับเป็น user ID ธรรมดา** array `recipients` เก็บ user UUID ที่เลือกจาก user picker มาตรฐาน — ไม่มี recipient type `email`/`sftp` ใน schema หรือ UI ปัจจุบันเลย แม้ type definition ใน `types/report-schedule.ts` จะยอมให้ค่า `ReportFormat` อื่นก็ตาม แต่ create flow ไม่เคยตั้งค่าเหล่านั้น
- **Redis lock เป็นต่อการ execute job ไม่ใช่ต่อ `(schedule_id, fire_timestamp)`** `RedisLocker.Lock()` รับ argument `key` เดียว (identity ของ job ใน gocron) แล้วล็อกด้วย `SET NX` TTL 5 นาที — ไม่มีส่วนประกอบ fire-timestamp ใน lock key
- **Cron expression เป็นค่าที่ derive มา ไม่ใช่เขียนเอง** เมื่อ frontend ไม่ส่ง `cron_expression`, `cronFromConfig()` ของ gateway จะ derive จาก `schedule_config.frequency`/`time`/`days_of_week`/`days_of_month` — เช่น `daily` → `mm hh * * *`
- **Schedule แบบเกิดซ้ำไม่เคยเขียนเข้า `tb_report_job`** เพราะทุก schedule ส่งมอบผ่าน `viewer_url` (ดู §1) เส้นทางการ fire จึงไม่เคยสร้างแถว report-job — ดู [reporting-audit/history](/th/inventory/reporting-audit/history) สำหรับช่องว่างที่เกิดขึ้น

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: **Postgres schema ของ service `micro-cronjobs` เอง** (`"CRONJOBS"."Cronjob"`) — ไม่ใช่ tenant Prisma schema `tb_report_schedule` (tenant schema) แสดงไว้เพื่อเปรียบเทียบเท่านั้น — ตายแล้ว

### 5.1 `Cronjob` (ตารางที่เก็บจริง, แถว `job_type = "report"`)

| ฟิลด์ (Go struct / DB column) | Type | คำอธิบาย |
| --- | --- | --- |
| `ID` / `id` | `uuid` | Primary key |
| `Name` / `name` | `string` | ชื่อแสดงผล — `name` ของ schedule |
| `Description` / `description` | `string?` | ตั้งอัตโนมัติเป็น `"Scheduled report: <report_type>"` |
| `JobType` / `jobType` | `string` | `"report"` สำหรับ schedule ที่สร้างจากหน้าจอนี้; `"notification"` / `"cleanup"` / `"dashboard_refresh"` สำหรับผู้ใช้ cron รายอื่น |
| `CronExpression` / `cronExpression` | `string` | cron มาตรฐาน ส่งมาตรง ๆ หรือ derive จาก `schedule_config` |
| `JobConfig` / `jobData` | `jsonb` | `ReportJobConfig`: `template_id`, `bu_codes`, `format`, `filters`, `recipients`, `user_id`, `options`, `delivery`, `notifications` |
| `SourceService` / `sourceService` | `string?` | `"micro-report"` สำหรับ schedule รายงาน |
| `SourceID` / `sourceID` | `string?` | id ของ report template (หรือ `report_type` เป็น fallback) |
| `IsActive` / `isActive` | `bool` | Default `true` เป็น `true` เสมอตอนสร้าง; ไม่มี UI path ใด toggle |
| `LastRunAt` / `lastRunAt`, `NextRunAt` / `nextRunAt` | `timestamp?` | bookkeeping ของ scheduler |
| `LastError` / `lastError` | `string?` | populate เมื่อ execute ล้มเหลว |
| `RunCount` / `runCount` | `int` | Default `0` |
| `MaxRetries` / `maxRetries`, `RetryCount` / `retryCount` | `int` | Default `0` retry แบบ exponential-backoff (`10s, 40s, 90s, …`) เมื่อ `MaxRetries > 0` |
| `TimeoutSeconds` / `timeoutSeconds` | `int` | Default `300` |
| คอลัมน์ audit | mixed | `createdAt`/`createdByID`, `updatedAt`/`updatedByID`, `deletedAt` (soft delete) |

**ตาราง:** `"CRONJOBS"."Cronjob"` (schema-qualified, ครอบด้วย double-quote เพื่อรักษา case — นี่คือ Postgres schema ที่แยกต่างหาก ไม่ใช่ฐานข้อมูล tenant หรือ platform)

### 5.2 `ReportJobConfig` (รูปร่าง JSONB `jobData`/`JobConfig` สำหรับ `job_type = "report"`)

`template_id`, `bu_codes: string[]`, `format`, `filters: map[string]string`, `recipients: string[]`, `user_id`, `options: map[string]any`, `delivery: { type, viewer_endpoint }`, `notifications: { web, email, mail_source }`

### 5.3 `tb_report_schedule` (tenant schema — ตารางที่ตายแล้ว เก็บไว้เพื่อเปรียบเทียบ)

`id` / `name` / `report_type` / `report_template_id` / `format` / `cron_expression` / `schedule_config` / `filters` / `options` / `recipients` / `is_active` / `last_run_at` / `next_run_at` / คอลัมน์ audit มีรูปร่างใกล้เคียงกับคู่ `Cronjob` + `ReportJobConfig` ที่แท้จริงข้างต้นมาก แต่ **ไม่พบการอ้างอิงจากโค้ดเลย** ทั่วทั้ง `carmen-turborepo-backend-v2/apps` หรือ `micro-report`/`micro-cronjobs`

## 6. กติกาทางธุรกิจ

- **`Cronjob` (micro-cronjobs) คือที่เก็บ schedule ที่แท้จริง; `tb_report_schedule` ตายแล้ว** ยืนยันโดยการค้นหาโค้ดทั่ว repo ทั้ง TypeScript และ Go
- **Lifecycle เป็นเพียงสร้าง (create-only) จาก UI** ไม่มี update endpoint เปิดไว้เลยใน route schedule ของ `reports.controller.ts` — มีแค่ `POST /schedules` (สร้าง), `GET /schedules` (รายการ), `DELETE /schedules/:id` (ลบ)
- **การส่งมอบเป็น `viewer_url` เสมอจากหน้าจอนี้** เส้นทางการ render ไฟล์แบบ legacy มีอยู่ใน executor แต่ create dialog ปัจจุบันเข้าไม่ถึง
- **Redis-locked, execute ครั้งเดียวแน่นอน** distributed locker ของ `go-cron` + Redis key `SET NX` (`cronjob:lock:<job-id>`, TTL 5 นาที) ป้องกันการ fire ซ้ำข้าม scheduler replica
- **Poll-based ไม่ใช่ event-driven** scheduler poll แถว `Cronjob` ทุก 1 นาทีและ reconcile job `go-cron` ใน memory กับ DB — การแก้ `cron_expression` ตรง DB (ไม่มี UI path ทำแบบนี้) จะมีผลตอน poll ครั้งถัดไป
- **ไม่มี misfire policy, ไม่มี timezone ต่อ schedule** ทั้งสองฟิลด์ไม่มีอยู่บน model `Cronjob` — ทั้งสองเคยถูกบันทึกไว้ว่าตั้งค่าได้และถูกแก้ไขในที่นี้ว่าไม่มีอยู่จริง

## 7. ความเชื่อมโยงข้ามโมดูล

- [reporting-audit/report](/th/inventory/reporting-audit/report) — โมดูลพ่อ; `report_template_id` resolve แถว `tb_report_template` (platform schema, ยังมีอยู่จริง)
- [reporting-audit/history](/th/inventory/reporting-audit/history) — เพราะ schedule ทุกตัวที่สร้างผ่านหน้าจอนี้ส่งมอบผ่าน `viewer_url` schedule ที่ fire จึง **ไม่** เขียนแถว `tb_report_job` — ดู implementation status ของหน้านั้นสำหรับช่องว่างที่เกิดขึ้น
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — mechanism การส่งมอบที่แท้จริง: เรียก `POST /api/internal/notifications` หนึ่งครั้งต่อผู้รับหนึ่งคนเมื่อ schedule fire
- [access-control/user](/th/inventory/access-control/user) — ผู้รับคือ user ID ธรรมดา

## 8. แหล่งอ้างอิง

- **ที่เก็บจริง (Go, `micro-cronjobs`):** `../micro-cronjobs/internal/model/cronjob.go` (`CronJob`, `ReportJobConfig`, `ReportDelivery`, `ReportNotifications`), `../micro-cronjobs/internal/repository/cronjob_repo.go`, `../micro-cronjobs/internal/scheduler/scheduler.go` (poll loop, retry), `../micro-cronjobs/internal/scheduler/redis_locker.go` (distributed lock), `../micro-cronjobs/internal/executor/report.go` (การ dispatch แบบ `viewer_url` เทียบกับ `file`)
- **Gateway (proxy CRUD schedule → micro-cronjobs):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.controller.ts` (`@Post('schedules')`, `@Get('schedules')`, `@Delete('schedules/:schedule_id')`), `reports.service.ts` (`createSchedule`/`listSchedules`/`deleteSchedule`, `cronFromConfig()`)
- **Prisma tenant (ตารางที่ตายแล้ว เพื่อเปรียบเทียบ):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_schedule` (บรรทัด ~6128)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/report/schedules/report-schedules.route.tsx`, `schedule-component.tsx`, `create-schedule-dialog.tsx`, `schedule-frequency-field.tsx`, `schedule-recipients-field.tsx`, `schedule-notifications-field.tsx`
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-report-schedule.ts` (`useReportSchedules`, `useCreateReportSchedule`, `useDeleteReportSchedule` — ไม่มี update hook), `types/report-schedule.ts`
