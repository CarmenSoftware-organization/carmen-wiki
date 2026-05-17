---
title: กำหนดการรายงาน (Report Schedule)
description: ตารางเวลาขับโดย cron สำหรับการสร้างรายงานเกิดซ้ำ — fire การรันตาม cadence และส่ง output ไปยังผู้รับที่ตั้งค่า
published: true
date: 2026-05-17T07:28:28.000Z
tags: reporting-audit, schedule, automation, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# กำหนดการรายงาน (Report Schedule)

> **At a Glance**
> **เจ้าของ:** Sysadmin / schedule-admin &nbsp;·&nbsp; **ตาราง:** `tb_report_schedule` &nbsp;·&nbsp; **Retention:** ไม่จำกัด (soft-delete เท่านั้น); artefact หมดอายุผ่าน [[reporting-audit/history]] &nbsp;·&nbsp; **ใช้โดย:** poller ของ `micro-cronjobs` &nbsp;·&nbsp; **จับคู่ template ของรายงานกับ cron expression, ชุด filter แบบ frozen และรายการการส่ง**

![กำหนดการรายงาน (Report Schedule) screen](/screenshots/reporting-audit/schedule.png)

## 1. ภาพรวมและผู้ใช้งาน

Report Schedule กำหนด **เวลาที่รายงานจะรันและที่ที่ output ไป** แต่ละแถวผูก template ของรายงานกับ cron expression, ชุด filter แบบ frozen และรายการผู้รับ Service ของ cron poll schedule ที่ active, ล็อก slot การ fire ใน Redis และ enqueue job ของ [[reporting-audit/history]] ที่ `micro-report` execute แถว history คือ artefact ของบันทึก; แถว schedule คือคำจำกัดความ

**ผู้ใช้งาน:** **Sysadmin** (สร้าง / แก้ / ปิด), **Operations** (เปลี่ยนผู้รับ, ปรับ cron), **Auditor** (ตรวจสอบว่า daily export ยัง fire)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Pause schedule | Reports → Schedules → แถว → **Active toggle off** | ตั้ง `is_active = false`; แถวคงไว้, การ poll ถูกระงับ |
| เปลี่ยน cron expression | หน้ารายละเอียด → **Cron builder** | คำนวณ `next_run_at` ใหม่จากตอนนี้ |
| อัปเดตผู้รับ | หน้ารายละเอียด → **Recipients picker** | รายการแบบมี type: `email` / `user` / `sftp` |
| ทดสอบ schedule โดยไม่ต้องรอ | หน้ารายละเอียด → **Test Run** | enqueue job ครั้งเดียวด้วย parameter เดียวกัน |
| ดูผลการ fire ล่าสุด | รายการ → คอลัมน์ **Last status** | สะท้อนแถว [[reporting-audit/history]] ล่าสุด |
| ดูเวลา fire ครั้งหน้า | รายการ → **Next-run countdown** | สดจาก `next_run_at` |
| ลบ schedule | หน้ารายละเอียด → **Delete** | soft-delete ผ่าน `deleted_at`; scheduler ละเว้น |
| มี cadence สองชุดจาก template เดียว | สร้าง schedule ที่สองด้วย `report_type` เดียวกัน | ไม่มี uniqueness บน `(report_type, cron_expression)` — โดยตั้งใจ |

## 3. คำถามที่พบบ่อย

| อาการ / คำถาม | สาเหตุ / คำตอบ | การจัดการ |
|---|---|---|
| Schedule ไม่ fire | `is_active = false`, `deleted_at` ถูกตั้ง หรือ cron expression ผิด | toggle active + ตรวจสอบ cron ใน builder |
| มี scheduler สอง replica — จะ fire สองครั้งไหม? | ไม่ — Redis lock บน `(schedule_id, fire_timestamp)` รับประกัน enqueue ครั้งเดียว | — |
| จะเกิดอะไรถ้าเรา down ตอนที่มี slot ขาด? | `schedule_config.misfire_policy`: `fire_once` (default), `skip` หรือ `fire_all` | tenant ที่ down นานควรใช้ `skip` |
| Cron รันใน timezone ไหน? | `schedule_config.timezone` (โดยทั่วไป `Asia/Bangkok`); fall back เป็น UTC ถ้าไม่มี | ตั้งตอนสร้าง |
| Output ไปลงที่ไหน? | `file_url` ของแถว history + ส่งไปยังแต่ละ entry ใน `recipients` | ดู [[reporting-audit/history]] |
| ทำไมผู้รับถูกข้าม? | `type` ไม่รู้จักใน object ของผู้รับ | warning เขียนใน `error_message` ของแถว job |
| ใครสร้าง schedule ได้? | สิทธิ์ schedule-admin (Sysadmin ถือโดยอัตโนมัติ) | grant ผ่าน [[access-control/permission]] |

## 4. กรณีพิเศษ

- **Idempotency** Redis lock ต่อ `(schedule_id, fire_timestamp)`; scheduler ตัวที่สองที่ race เข้ามาคือ no-op Job ที่ enqueue carry `options.schedule_id` และ `options.scheduled_fire_at` สำหรับ traceability
- **Semantic ของ soft-delete** การ poll ของ scheduler กรอง `is_active = true AND deleted_at IS NULL AND next_run_at <= now()` แถวที่ soft-delete ถูกละเว้นตลอดไป
- **การ reactivate** คำนวณ `next_run_at` ใหม่จาก cron กับเวลาปัจจุบัน — ไม่ back-fill slot ที่ขาด
- **เขตเวลา** Cron ประเมินกับ `schedule_config.timezone` `last_run_at` / `next_run_at` เก็บ UTC
- **RBAC ในการอ่าน** การเข้าถึงอ่านต้องมีสิทธิ์อ่านของ category รายงาน; edit / toggle ต้องมีสิทธิ์ schedule-admin

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_report_schedule`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar(255)` | No | ชื่อแสดงผล |
| `report_type` | `String @db.VarChar(100)` | No | identifier ของรายงานเชิง logical (resolve `tb_report_template`) |
| `report_template_id` | `String? @db.Uuid` | Yes | binding template แบบเลือกได้; มิฉะนั้น resolve ตาม `report_type` |
| `format` | `enum_report_format` | No | `pdf` / `excel` / `csv` / `json` |
| `cron_expression` | `String @db.VarChar(100)` | No | cron 5- หรือ 6-field มาตรฐาน |
| `schedule_config` | `Json? @db.JsonB` | Yes | `{ timezone, jitter_seconds, misfire_policy }` |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}` ชุด filter ที่ใช้แต่ละการรัน |
| `options` | `Json? @db.JsonB` | Yes | Default `{}` ตัวเลือกการ render |
| `recipients` | `Json? @db.JsonB` | Yes | Default `[]` เป้าหมายการส่งแบบ typed |
| `is_active` | `Boolean` | No | Default `true` ปิดโดยไม่ลบ |
| `last_run_at`, `next_run_at` | `DateTime? @db.Timestamptz(6)` | Yes | คอลัมน์ health-check |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** index บน `is_active` (`idx_report_schedule_active`) ไม่มี uniqueness บน `(report_type, cron_expression)` — มีหลาย schedule ต่อ template โดยตั้งใจ

## 6. กติกาทางธุรกิจ

- **รูปแบบ cron** มาตรฐาน `minute hour day-of-month month day-of-week` ตัวอย่าง: `0 6 * * *` (รายวัน 06:00), `0 7 * * 1` (จันทร์ 07:00), `0 0 1 * *` (วันที่ 1 ของเดือน)
- **Idempotency** Redis lock บน `(schedule_id, fire_timestamp)` รับประกัน enqueue ครั้งเดียวข้าม replica
- **นโยบาย missed-fire** `fire_once` (default — fire ที่ poll ครั้งหน้า), `skip` (ทิ้งและขยับ) หรือ `fire_all` (ตามทุก slot ที่ขาด)
- **Active flag** `is_active = false` ระงับการ poll โดยไม่ลบ; toggle on คำนวณ `next_run_at` ใหม่จากตอนนี้
- **การ resolve ผู้รับ** object แบบ typed — `{type:"email",value:...}`, `{type:"user",value:<uuid>}`, `{type:"sftp",value:<config_id>}` Type ที่ไม่รู้จักถูกข้ามพร้อม warning
- **RBAC ในการสร้าง** เฉพาะ grant ของ schedule-admin (Sysadmin โดยอัตโนมัติ) สร้าง / แก้ได้
- **Retention** แถว schedule คงไว้ไม่จำกัด (soft-delete เท่านั้น); artefact หมดอายุตาม retention ของ [[reporting-audit/history]]

## 7. ความเชื่อมโยงข้ามโมดูล

- [[reporting-audit/report]] — โมดูลพ่อ `report_type` / `report_template_id` resolve `tb_report_template`
- [[reporting-audit/history]] — ทุกการ fire เขียนแถว `tb_report_job` หนึ่งแถว; `last_run_at` สะท้อนแถวนั้น
- [[reporting-audit/notification]] — ผู้รับ type `user` ได้รับ in-app notification; `email` ได้รับ artefact ผ่าน mailer ของแพลตฟอร์ม
- [[reporting-audit/activity]] — create / update / delete / enable / disable ถูก log ด้วย `entity_type = 'report_schedule'`
- [[access-control/user]], [[access-control/permission]] — เจ้าของ + grant schedule-admin

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_schedule` (lines 5685-5709), `enum_report_format` (~5628-5633)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/report/schedules/`
- **Cron microservice:** `../micro-cronjobs/internal/scheduler/scheduler.go` (poll + dispatch), `../micro-cronjobs/internal/scheduler/redis_locker.go` (idempotency), `../micro-cronjobs/internal/repository/cronjob_repo.go` (reads)
- **Reports microservice:** `../micro-report/` — บริโภค job ที่ enqueue
