---
title: ประวัติรายงาน (Report History)
description: รายการอ่านอย่างเดียวของแถว tb_report_job — ยืนยันแล้วว่าไม่มีข้อมูลในเชิงโครงสร้างในระบบปัจจุบัน เพราะทั้งการรันรายงานแบบ on-demand, Print และการ fire ตามเวลาต่างไม่มีเส้นทางโค้ดที่เข้าถึงได้เขียนแถว job เลย
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, history, archive, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ประวัติรายงาน (Report History)

> **At a Glance**
> **Route:** `/report/history` &nbsp;·&nbsp; **ตาราง:** `tb_report_job` (tenant schema — มีอยู่จริง ไม่ตาย) &nbsp;·&nbsp; **หน้าจอ:** รายการอ่านอย่างเดียว — ไม่มี re-run, ไม่มีคอลัมน์ requester, ไม่มี filter ตามวันที่, ไม่มี drawer Print History &nbsp;·&nbsp; **ช่องว่างที่ยืนยันแล้ว:** ไม่มีเส้นทางที่เข้าถึงได้ใน frontend ปัจจุบันเขียนแถวเข้าตารางนี้เลย

![ประวัติรายงาน (Report History) screen](/screenshots/reporting-audit/history.png)

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

`tb_report_job` เองมีอยู่จริง — ต่างจาก `tb_report_schedule` (ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)) มันถูกอ่านและเขียนใช้งานจริงโดย `ReportJobRepo` (Go) ของ `micro-report` ปัญหาอยู่ที่เส้นทางไหนเขียนเข้าตารางนี้:

- **"Run รายงาน" บนรายการรายงาน** (`report-component.tsx` → `useRunReportMutation` → `POST /reports/viewer`) เรียก handler `viewReport` ซึ่งสร้าง viewer URL โดยตรงและคืนกลับมา — ไม่เคยเรียก `ReportJobRepo.Create` เลย
- **ปุ่ม "Print" ทุกตัว** (`printDocument()` ของ `lib/print-document.ts`) resolve print-template mapping แล้วเรียก endpoint `POST .../report/viewer` ตัวเดียวกัน — ก็ไม่มีแถว job เช่นกัน
- **การ fire ของ schedule ตามเวลา** (ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)) ส่งมอบผ่าน `format: "viewer_url"` เสมอจาก UI สร้าง schedule ปัจจุบัน ซึ่ง executor dispatch ผ่าน `executeViewerURL()` — ก็ไม่มีแถว job อีกเช่นกัน มีเพียงสาขา `executeFile()` แบบ legacy ของ executor (ซึ่ง UI ปัจจุบันเข้าไม่ถึง) เท่านั้นที่เรียก `POST .../report/generate-async` ซึ่งเป็น endpoint เดียวที่เขียน `tb_report_job`
- การค้นหาทั่ว frontend ยืนยันว่า **ไม่มีผู้เรียก `generate-async`, `generateAsync` หรือ `job-status`/`jobStatus`** เลยแม้แต่ที่เดียวใน `carmen-inventory-frontend-react`

**ผลสุทธิ:** ภายใต้ UI ที่เข้าถึงได้ในปัจจุบัน ไม่มีอะไรเติมข้อมูลให้ `tb_report_job` เลย หน้าจอ `/report/history` มีอยู่จริง เชื่อมต่อถูกต้องกับตารางจริงและ backend endpoint จริง แต่คาดว่าจะ **ว่างเปล่าในทางปฏิบัติ** เว้นแต่จะมีผู้เรียกอื่น (การเชื่อมต่อ API โดยตรง, การเปลี่ยนแปลง UI ในอนาคต หรือ schedule ที่ `delivery.type` ถูกตั้งเป็น `"file"` นอกเหนือจาก create-dialog ปกติ) ใช้เส้นทาง async-job หน้านี้ถูกแก้ไขให้อธิบายหน้าจอจริงและช่องว่างที่พบ; ข้อกล่าวอ้างในฉบับก่อนหน้าเกี่ยวกับ "ทุกการรันรายงาน" ที่มาลงที่นี่, action "Re-run" และ drawer "Print History" ต่อเอกสารถูกลบออกในฐานะที่ยังไม่ยืนยัน/ไม่มีอยู่จริง

## 1. ภาพรวมและผู้ใช้งาน

Report History คือ log การ execute ของ `tb_report_job` — เมื่อมีข้อมูล จะเป็นหนึ่งแถวต่อ job แบบ **async** หนึ่งตัว (`queued → processing → completed | failed | cancelled`) แต่ละแถวเก็บ identifier ของรายงาน, ชุด filter จริง, ผู้ใช้ที่ขอ, สถานะ lifecycle และตัวชี้ไปยัง artefact ที่ผลิต หน้าจอ `/report/history` (`history-component.tsx`) แสดงเป็นรายการแบ่งหน้าธรรมดา

**กลุ่มผู้ใช้:** ผู้ใช้ที่ authenticate แล้วและมีสิทธิ์อ่านรายงานคนใดก็สามารถดูหน้าจอนี้ได้ — ไม่พบ gate เฉพาะ Auditor/Sysadmin บน endpoint `GET .../history` นอกเหนือจาก `KeycloakGuard` + header `X-App-Id` มาตรฐาน

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดูประวัติ job | `/report/history` | สลับมุมมองรายการ/grid ได้; ช่องค้นหา (server-side, ตรงกับข้อความ `job_id`/`report_type`/`format`/`status`/`file_url`/`file_name`/`filters`) |
| เปิดไฟล์ของ job ที่เสร็จแล้ว | คลิกลิงก์ชื่อรายงานในแถว | render เป็นลิงก์เฉพาะเมื่อมี `file_url` เท่านั้น |
| **ไม่มีในหน้าจอปัจจุบัน** | — | Re-run, คอลัมน์ Requester ที่แยกออกมา, filter ตามช่วงวันที่, การดูรายละเอียด "View Details" ของ JSON `filters`/`options` ที่เก็บไว้ และ drawer "Print History" ต่อเอกสาร — ไม่พบสิ่งเหล่านี้เลยใน `history-component.tsx`, `history-card.tsx` หรือ `use-history-table.tsx` |

## 3. คำถามที่พบบ่อย

| อาการ / คำถาม | สาเหตุ / คำตอบ | การจัดการ |
|---|---|---|
| ทำไมรายการ history ของฉันว่างเปล่าเสมอ? | ตามที่คาดไว้ในระบบปัจจุบัน — ดูสถานะการทำงานจริงด้านบน; ไม่มีเส้นทาง UI ใดเขียน `tb_report_job` | ไม่ใช่ bug โดยตัวมันเอง; แจ้งถ้าเจตนาของ product คือให้ on-demand run และ Print ถูก log ที่นี่ |
| รายงานที่ฉัน "Run" ไปแล้วหายไปไหน? | ถูก render ตรงผ่าน viewer endpoint — ไม่มีแถว job, ไม่มี history entry, ไม่สามารถดาวน์โหลดภายหลังได้ | เปิดใหม่ด้วย combination ของรายงาน/filter เดียวกันในรายการรายงาน |
| แก้ไขแถวได้ไหม? | ไม่ได้ — ไม่มี endpoint CRUD/update สำหรับ `tb_report_job` นอกเหนือจากการเปลี่ยนสถานะภายในของ executor เอง | — |
| คอลัมน์ไหนที่ตารางแสดงจริง? | `#`, ชื่อรายงาน (เป็นลิงก์เมื่อมี `file_url`), ประเภทรายงาน, รูปแบบ, badge สถานะ, จำนวนแถว | ยืนยันผ่าน `use-history-table.tsx` — ไม่มีคอลัมน์ requester หรือวันที่ |

## 4. กรณีพิเศษ

- **ไม่มีข้อมูลในเชิงโครงสร้าง ไม่ใช่พัง** หน้าจอ, hook และ backend endpoint ทั้งหมดเชื่อมกับตารางจริงถูกต้อง — ช่องว่างคือไม่มีเส้นทางเขียนที่เข้าถึงได้ในปัจจุบัน ไม่ใช่ bug ในเส้นทางการอ่าน
- **Append-only ในจุดที่มีการเขียน** `ReportJobRepo` เขียนเฉพาะตอน `generate-async` และอัปเดตเฉพาะฟิลด์ lifecycle/artefact/error ในภายหลัง — ไม่มีเส้นทางอื่น mutate ตารางนี้
- **เขตเวลา** ทุก timestamp บนโมเดลเบื้องหลังเป็น `Timestamptz(6)` UTC; UI รายการปัจจุบันไม่ render `started_at`/`completed_at`/`expires_at` เลย (แสดงแค่ `row_count` เพิ่มจาก status/format)
- **Retention (ยังไม่ยืนยันด้วยเหตุผลของการเข้าถึงไม่ได้)** `expires_at` มีอยู่บนโมเดลและจะควบคุมการ reap artefact ถ้าเส้นทาง async เคยถูกใช้งาน — ยังไม่ได้ตรวจสอบเทียบกับ reaper job ที่ใช้งานจริงในรอบนี้

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
| `filters` | `Json? @db.JsonB` | Yes | Default `{}` |
| `options` | `Json? @db.JsonB` | Yes | Default `{}` |
| `file_url`, `file_name`, `file_size`, `row_count` | mixed | Yes | metadata ของ artefact |
| `error_message` | `String?` | Yes | populate เมื่อ `status = failed` |
| `started_at`, `completed_at`, `expires_at`, `duration_ms` | mixed | Yes | timestamp การ execute / retention |
| `requested_by_id` | `String @db.Uuid` | No | ผู้ใช้ที่ขอ |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** index บน `status`, `report_type`, `requested_by_id`, `created_at DESC` ไม่มี FK ไป `tb_report_schedule` (ซึ่งตายแล้วเช่นกัน — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule))

## 6. กติกาทางธุรกิจ

- **Lifecycle** `queued → processing → (completed | failed | cancelled)` mutate เฉพาะโดย `ReportJobRepo` ของ `micro-report` (`Create`, `UpdateStatus`, `Complete`, `Fail`)
- **มีเพียง `generate-async` เท่านั้นที่เขียนแถว** เส้นทาง `viewer`, `data` และ `viewer-with-data` (เส้นทางที่ใช้จริงโดยรายการรายงาน, Print และ schedule แบบ viewer-delivery) ไม่เคยแตะตารางนี้
- **ยังไม่ยืนยันข้อกล่าวอ้างเรื่อง scrub PII** ข้อกล่าวอ้างในฉบับก่อนหน้าว่า "credential/token/ค่า raw SQL ถูก scrub ออกจาก `error_message`" ยังไม่ได้ยืนยันเทียบกับ `ReportJobRepo.Fail()` ในรอบนี้ — คงไว้ในฐานะที่ยังไม่ยืนยันแทนที่จะยืนยันเป็นข้อเท็จจริงซ้ำ

## 7. ความเชื่อมโยงข้ามโมดูล

- [reporting-audit/report](/th/inventory/reporting-audit/report) — เส้นทาง "Run" แบบ on-demand และ Print ที่ **ไม่** เติมข้อมูลให้ตารางนี้
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — เส้นทางการ fire แบบเกิดซ้ำ; ก็ไม่เติมข้อมูลให้ตารางนี้เช่นกันภายใต้การส่งมอบ `viewer_url` เท่านั้นในปัจจุบัน
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [vendor-pricelist](/th/inventory/vendor-pricelist) — ปุ่ม Print ที่ resolve ผ่านเส้นทาง viewer ไม่ใช่ตารางนี้
- [access-control/user](/th/inventory/access-control/user) — `requested_by_id`

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (บรรทัด ~6094), `enum_report_job_status` (บรรทัด ~6086), `enum_report_format` (บรรทัด ~6070), `enum_report_category` (บรรทัด ~6077)
- **Backend (มีอยู่จริง แต่เข้าถึงได้เฉพาะผ่านเส้นทาง legacy ที่เข้าไม่ถึง):** `../micro-report/controller/report_controller.go` (handler `generateAsync`, `jobStatus`, `history`), `../micro-report/db/report_job_repo.go`, `../micro-report/model/job.go`
- **Backend (เส้นทางที่ใช้จริง — ไม่มีแถว job):** handler `viewReport` ของ `../micro-report/controller/report_controller.go`
- **Frontend route:** `../carmen-inventory-frontend-react/routes/report/history/report-history.route.tsx`, `history-component.tsx`, `use-history-table.tsx`
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-report-history.ts` — `useReportHistory` (รายการเท่านั้น; ไม่มี hook re-run/detail)
