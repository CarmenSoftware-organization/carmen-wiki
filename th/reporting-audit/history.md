---
title: ประวัติรายงาน (Report History)
description: คลังเก็บแบบ append-only ของทุกการรันรายงานที่ execute — วันที่, parameter, สถานะ, ลิงก์ไปยัง artefact ที่สร้างขึ้น
published: true
date: 2026-05-17T12:00:00.000Z
tags: reporting-audit, history, archive, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ประวัติรายงาน (Report History)

> **At a Glance**
> **เจ้าของ:** `micro-report` executor (UI อ่านอย่างเดียว) &nbsp;·&nbsp; **ตาราง:** `tb_report_job` &nbsp;·&nbsp; **Retention:** `expires_at` ตามนโยบาย tenant (artefact ถูก reap; แถวคงไว้) &nbsp;·&nbsp; **ใช้โดย:** Reports → History, drawer Print History &nbsp;·&nbsp; **บันทึก audit แบบ append-only ของทุกการรันรายงาน**

## 1. ภาพรวมและผู้ใช้งาน

Report History คือ **บันทึกการ execute แบบ append-only** สำหรับการรันรายงานทุกครั้งบน tenant — การ export แบบ ad-hoc, การเรียก Print และการรันตามเวลาทั้งหมดมาที่นี่ แต่ละแถวเก็บ identifier ของรายงาน, ชุด filter จริง, ผู้ใช้ที่ขอ (หรือ schedule), สถานะ lifecycle และตัวชี้ไปยัง artefact ที่ผลิตใน blob storage

**ผู้ใช้งาน:** **Auditor** (ใครรันอะไร), **Sysadmin** (วิเคราะห์ run ที่ล้มเหลว), **Compliance** (export trail), **Tester** (ตรวจสอบว่า template ที่ถูกต้องทำงาน)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| หาการรันรายงานเมื่อวาน | Reports → **History** | กรองตามช่วงวันที่ + ประเภทรายงาน |
| ดาวน์โหลด output ซ้ำ | แถว History → **Download** | ใช้ได้จนกว่าตัว reap ของ `expires_at` จะลบ artefact |
| ดูว่าใครเป็นผู้กระตุ้นการรัน | แถว History → คอลัมน์ **Requester** | การรันจาก schedule แสดงเจ้าของ schedule ผ่าน `requested_by_id` |
| รันรายงานซ้ำด้วย filter เดิม | แถว History → **Re-run** | enqueue job ใหม่ด้วย `filters` / `options` เดียวกัน |
| ดูชุด filter ที่ใช้แบบเต็ม | แถว History → **View Details** | render JSON ของ `filters` และ `options` |
| ตรวจสอบ run ที่ล้มเหลว | กรอง `status = failed`, เปิด Details | `error_message` carry สาเหตุที่ scrub แล้ว |
| ยืนยันว่า Print ทำงาน | รายละเอียดเอกสาร → drawer **Print History** | แสดง job ล่าสุดต่อเอกสารนั้น |

## 3. คำถามที่พบบ่อย

| อาการ / คำถาม | สาเหตุ / คำตอบ | การจัดการ |
|---|---|---|
| ลิงก์ดาวน์โหลดได้ 404 | `expires_at` ผ่านแล้ว; reaper ลบ artefact | แถวคงไว้สำหรับ audit; **Re-run** เพื่อสร้างใหม่ |
| ทำไมแถวของฉันหาย? | RBAC กรองออก — คุณไม่ได้เป็นผู้ขอและไม่ใช่ category reader | ถาม Sysadmin หรือถือสิทธิ์อ่านของรายงาน |
| แก้ไขแถวได้ไหม? | ไม่ได้ — ตารางเป็นแบบ **append-only**; เฉพาะ executor เท่านั้นที่ mutate `status` / ฟิลด์ terminal | Re-run แทน |
| ทำไม `started_at` เป็น null? | Job ยังอยู่ที่ `queued` (executor ยังไม่หยิบ) | รอ หรือเช็คสุขภาพ executor |
| รูปแบบไฟล์จะได้อะไร? | สิ่งที่ขอตอน enqueue: `pdf` / `excel` / `csv` / `json` | เลือกตอน submit ไม่ใช่ตอน re-download |
| ไฟล์ output อยู่ที่ไหน? | Blob storage; `file_url` คือ URL ดาวน์โหลดที่ resolve แล้ว | อยู่เบื้องหลังโดย config storage ของ tenant |
| Error message ปลอดภัยที่จะแชร์ไหม? | ใช่ — credential, token, ค่า raw SQL ถูก scrub; เหลือเพียงชื่อ bound param | — |

## 4. กรณีพิเศษ

- **Append-only** Executor เขียนตอน enqueue และอัปเดตเฉพาะฟิลด์ lifecycle / artefact / error ไม่มีเส้นทางอื่น mutate ตารางนี้
- **การแยก retention** Artefact (file_url) หมดอายุที่ `expires_at`; แถวคงไว้เพื่อให้ "ใครรันอะไรกับ filter ไหน" อยู่ตลอดไป (ขึ้นกับนโยบาย tenant)
- **เขตเวลา** ทุก timestamp เป็น `Timestamptz(6)` UTC; UI render ตาม timezone ของ profile การรันตามเวลาเข้ารหัสเวลาที่ตั้งใจ fire ไว้ใน `options.scheduled_fire_at`
- **RBAC ในการอ่าน** มองเห็นโดยผู้ขอ, category reader หรือ Sysadmin / Auditor Frontend กรองที่ฝั่ง server; อย่าเชื่อ client
- **Job ที่ล้มเหลว / ถูก cancel** อาจใช้ขอบเขต retention ที่สั้นกว่าเพราะไม่มี artefact

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_report_job`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `report_type` | `String @db.VarChar(100)` | No | identifier เชิง logical ที่ตรงกับ template |
| `report_category` | `enum_report_category` | No | `inventory` / `procurement` / `recipe` / `vendor` / `financial` / `operational` |
| `format` | `enum_report_format` | No | `pdf` / `excel` / `csv` / `json` |
| `status` | `enum_report_job_status` | No | Default `queued` `queued` / `processing` / `completed` / `failed` / `cancelled` |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}` ค่า filter จริงสำหรับการรันครั้งนี้ |
| `options` | `Json? @db.JsonB` | Yes | Default `{}` ตัวเลือก render + `scheduled_fire_at` สำหรับการรันตามเวลา |
| `file_url`, `file_name`, `file_size`, `row_count` | mixed | Yes | metadata ของ artefact |
| `error_message` | `String?` | Yes | populate เมื่อ `status = failed`; scrub ความลับแล้ว |
| `started_at`, `completed_at`, `expires_at`, `duration_ms` | mixed | Yes | timestamp การ execute / retention |
| `requested_by_id` | `String @db.Uuid` | No | ผู้ใช้ที่ขอ (หรือ `created_by_id` ของ schedule) |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** index บน `status`, `report_type`, `requested_by_id` และ `created_at DESC` (รูปแบบการเข้าถึงหลัก) ไม่มี FK ไป `tb_report_schedule`; การเชื่อมเป็น logical ผ่านการจับคู่ `report_type` + correlation id ใน `options`

## 6. กติกาทางธุรกิจ

- **Lifecycle** `queued → processing → (completed | failed | cancelled)` `started_at` ตั้งเมื่อเข้า `processing`; `completed_at` + `duration_ms` ตั้งเมื่อเข้าสถานะ terminal `cancelled` เข้าถึงได้จาก `queued` หรือ `processing`
- **Retention ของ output** `expires_at` ขับ reaper ของที่จัดเก็บ หลังเวลาผ่านไป artefact หลัง `file_url` ถูกลบ; แถวคงไว้
- **RBAC** แถวมองเห็นโดย (a) ผู้ขอ, (b) ผู้ถือสิทธิ์อ่านของ category หรือ (c) Sysadmin / Auditor
- **เขตเวลาที่บันทึก** timestamp เก็บ UTC การรันตามเวลา persist เวลาที่ตั้งใจ fire ใน `options.scheduled_fire_at` เพื่อให้การ review ไม่กำกวม
- **ไม่มี PII ใน error** Executor scrub credential, token, ค่า raw SQL; เหลือเพียงชื่อ bound param

## 7. ความเชื่อมโยงข้ามโมดูล

- [[reporting-audit/report]] — โมดูลพ่อ; ทุก template `kind = report` ที่ทำงานสร้างแถวที่นี่
- [[reporting-audit/schedule]] — การรันแบบเกิดซ้ำ enqueue job ที่นี่; `last_run_at` derive จาก job ล่าสุดที่ completed
- [[reporting-audit/activity]] — action `export` และ `print` ก็ถูก log ด้วย `entity_type = 'report_job'`
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — การเรียก Print มาที่นี่
- [[access-control/user]] — `requested_by_id` resolve ผ่าน `tb_user` ของแพลตฟอร์ม

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (lines 5652-5683), `enum_report_job_status` (5644-5650), `enum_report_format` (~5628-5633), `enum_report_category` (~5635-5642)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/report/history/`
- **Reports microservice:** `../micro-report/controller/report_controller.go`, `../micro-report/db/report_job_repo.go`
