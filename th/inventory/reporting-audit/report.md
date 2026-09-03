---
title: รายงาน (Report)
description: pipeline การสร้างรายงาน — แคตตาล็อก report-template และ print-type mapping (platform), การ render ผ่าน viewer แบบ on-demand และตาราง job/history ที่มีอยู่จริงแต่ปัจจุบันไม่มีข้อมูล (ไม่มีเส้นทาง UI ใดเขียนเข้าไปเลย)
published: true
date: 2026-07-22T03:05:28.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# รายงาน (Report)

> **At a Glance**
> **เจ้าของ:** Platform Admin (template, mapping) &nbsp;·&nbsp; **ตาราง:** `tb_report_job` (tenant — มีอยู่จริงแต่ปัจจุบันไม่มีข้อมูล) — schedule **ไม่ได้** อยู่ใน `tb_report_schedule` (ตายแล้ว ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)), `tb_report_template` + `tb_print_template_mapping` (platform, มีอยู่จริง) &nbsp;·&nbsp; **ใช้โดย:** รายการรายงาน ("Run"), ทุกปุ่ม "Print" และการ fire ตามเวลา — ทั้งสามเส้นทาง render ผ่าน viewer endpoint ไม่มีเส้นทางใดเขียนแถว job เลย

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

flow "Run" แบบ on-demand บนรายการรายงาน (`report-component.tsx` → `useRunReportMutation` → `POST .../reports/viewer`) และปุ่ม "Print" ของทุกโมดูล (`lib/print-document.ts`) ทั้งคู่ resolve ตรงไปยัง viewer URL ที่ render แล้ว — ไม่มีเส้นทางใดเรียก async job endpoint (`generate-async`) เลย จึงไม่มีเส้นทางใดเขียนแถว `tb_report_job` การค้นหาทั่ว frontend พบว่าไม่มีผู้เรียก `generate-async`/`job-status` เลยแม้แต่ที่เดียว ดู [reporting-audit/history](/th/inventory/reporting-audit/history) สำหรับข้อค้นพบแบบเต็มและผลกระทบต่อหน้าจอ history และ [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) สำหรับตาราง `tb_report_schedule` ที่ยืนยันแล้วว่าตายแล้ว (ที่เก็บ schedule จริงคือตาราง `Cronjob` แบบ generic ใน service micro-cronjobs แยกต่างหาก)

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี report คือ **pipeline การสร้างรายงาน** — การ render แบบ ad-hoc on-demand, print layout เบื้องหลังทุกปุ่ม "Print" และ (ในเชิงโครงสร้าง แม้จะยังไม่มีข้อมูลจริง) การ export แบบเกิดซ้ำตามเวลา มีสามตารางที่เกี่ยวข้อง กระจายอยู่ในสอง schema บวกฐานข้อมูล scheduler ภายนอกอีกหนึ่งแห่ง:

- `tb_report_template` (platform) — แคตตาล็อก template (`report` แบบ analytical หรือ `print` layout); เก็บ layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`), orientation, signatures อ่านอย่างเดียวจากรายการรายงานของ `carmen-inventory-frontend-react` — ไม่พบ UI สำหรับสร้าง/แก้ template ใน repo นี้ (`POST`/`PUT`/`DELETE` ของ template มีอยู่บน backend แต่เปิดผ่าน gateway module ใน `platform/` ซึ่งอยู่นอกขอบเขตของ repo นี้)
- `tb_print_template_mapping` (platform) — map `document_type` (`PO`, `PR`, `SR`, `GRN`, `CN`, `IA`, …) ไปยังหนึ่งหรือหลาย template; `is_default = true` หนึ่งตัวต่อประเภท มีอยู่จริงและถูก resolve ใช้งานจริงโดยทุกปุ่ม "Print" ผ่าน `GET .../report/print-template?document_type=`
- `tb_report_job` (tenant) — ตาราง job/history มีอยู่จริงและเชื่อมกับ `/report/history` ถูกต้อง แต่ยืนยันแล้วว่าไม่มีการเขียนจากเส้นทาง UI ที่เข้าถึงได้เลยในปัจจุบัน — ดูสถานะการทำงานจริงด้านบน

**Schedule** ของรายงานไม่ใช่ตาราง tenant ตัวที่สี่ในที่นี้ — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) สำหรับโมเดลที่แก้ไขแล้ว (แถว `Cronjob` แบบ generic ใน service micro-cronjobs แยกต่างหาก)

**ดูแลโดย** Platform Admin (template, mapping) — schedule ไม่ใช่เรื่องที่ Sysadmin เป็น gate ในที่นี้; ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) (ผู้ใช้ที่ authenticate แล้วและมี BU context คนใดก็ได้ ไม่พบ gate schedule-admin) **อ่านโดย** รายการรายงาน, เมนู "Print as…", widget บน dashboard

### 1.1 Dataset เทียบกับการ render — การแยก micro-data

การสร้างรายงานแบ่งออกเป็นสอง Go service โดยมีออบเจกต์ **`Dataset`** (columns + rows + totals + summary) เป็นสัญญาขอบเขต:

| ความรับผิดชอบ | Columns บน `tb_report_template` | เจ้าของ | หน้าที่ |
|---|---|---|---|
| **Dataset** | `source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key` | **micro-data** | แก้ไข view / function / procedure, ประกอบ WHERE clause จาก filter, กระจายไปยัง BU ของ tenant, คืน `Dataset` ไม่ render อะไรทั้งนั้น |
| **Report** | `content`, `kind`, `report_group`, format / orientation / signatures | **micro-report** | รับผิดชอบรูปแบบ output (PDF / Excel / CSV / JSON), layout ของ template, `kind`, print mapping และการติดตาม job |

micro-report ไม่รันคำสั่ง query ใน process ของตัวเองอีกต่อไป — แต่เรียก `POST /api/datasets/execute` ของ micro-data (ส่ง `builder_key` หรือ `name`, `bu_codes`, และ `filters` ของ source) แล้ว render `Dataset` ที่ได้รับกลับมา แถว `tb_report_template` ยังคงเก็บทั้งสองชุด column ไว้จริง; micro-data อ่านเฉพาะ dataset columns (map ไปยัง `model.DatasetSource`) การแยก column เหล่านั้นออกเป็นตาราง `tb_dataset_source` เป็น future migration ที่กล่าวถึงไว้ แต่ยังไม่ได้ดำเนินการ

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| รันรายงาน on demand | รายการรายงาน → เลือกรายงาน → Run | `POST .../reports/viewer` — render viewer URL โดยตรง; **ไม่มีการเขียนแถว `tb_report_job`** |
| Print เอกสาร | action Print ของเอกสารใดก็ได้ | resolve `tb_print_template_mapping` แล้วใช้ viewer endpoint เดียวกัน — พฤติกรรม "ไม่มีแถว job" เหมือนกัน |
| กรองรายการรายงาน | ช่องค้นหา + filter กลุ่มรายงาน | ค้นหาแบบ server-side; filter กลุ่มเป็น client-side บนหน้าปัจจุบัน |
| เพิ่ม print layout สำหรับประเภทเอกสาร | Platform Admin (นอก UI ของ repo นี้ — ดูด้านล่าง) | toggle `is_default` เพื่อสลับ default; endpoint backend มีอยู่จริง แต่ไม่พบหน้าจอแก้ไขใน `carmen-inventory-frontend-react` |
| BU-scope template | แก้ `allow_business_unit` / `deny_business_unit` ของ template | Null allow-list = ทุก BU |
| ตั้งเวลา export เกิดซ้ำ | ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) | ไม่ได้เก็บในตาราง tenant ของโมดูลนี้ — ที่เก็บจริงคือ service scheduler แยกต่างหาก |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| หน้าจอ history ไม่แสดงอะไรเลยสำหรับ run ที่เพิ่งทำ | ตามที่คาดไว้ — ดูสถานะการทำงานจริงด้านบน; ไม่มีเส้นทางที่เข้าถึงได้เขียน `tb_report_job` | ไม่ใช่ bug ในเส้นทางการอ่าน |
| Job ล้มเหลวด้วย "view not found" (เมื่อเส้นทาง async *ถูกใช้งานจริง*) | `source_type` / `source_name` drift | จัด template binding ให้ตรงกับ DB object |
| มี default หลายตัวต่อประเภทเอกสาร | invariant ของแอปถูกละเมิด | ซ่อม: ให้มี `is_default = true` หนึ่งตัว; ที่เหลือเป็น false |
| Template ไม่เห็นใน BU | `allow_business_unit` exclude; หรือ `deny_business_unit` include | แก้ BU scoping |

## 4. กรณีพิเศษ

- **การรัน on-demand และ Print เป็นการ render แบบ synchronous ผ่าน viewer ไม่ใช่ job แบบ queue** ไม่มีแถว `tb_report_job`, ไม่มี entry ใน history, ไม่มี retention `expires_at` ใด ๆ ใช้กับทั้งสอง
- **Source binding drift** เป็นสาเหตุที่เป็นไปได้มากที่สุดของความล้มเหลวบนเส้นทาง viewer (ความไม่ตรงกันของ `source_type`/`source_name`) — รักษา template binding ให้สอดคล้องกับ DB object จริง
- **Template มาตรฐาน vs ที่ผู้ใช้กำหนด** `is_standard = true` มีการจัดการพิเศษโดย handler `delete`/`update` ของ backend (ยังไม่ยืนยันพฤติกรรม UI ที่แน่ชัดในรอบนี้ — ไม่มีหน้าจอแก้ไข template ใน `carmen-inventory-frontend-react`)
- **Lifecycle ของ job แบบ async มีอยู่จริงแต่ไม่ถูกใช้งาน** `queued → processing → (completed | failed | cancelled)` ยังเป็นสัญญาของโมเดล; executor เดินหน้าผ่าน `generate-async` เท่านั้น ซึ่งไม่มี frontend ปัจจุบันเรียกใช้เลย

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: **ผสม** — tenant สำหรับตาราง job/history, platform สำหรับ templates/mappings Schedule **ไม่ใช่** ตาราง tenant ในที่นี้ — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) §5 สำหรับโมเดล `Cronjob` จริงใน service micro-cronjobs แยกต่างหาก

### 5.1 `tb_report_job` (tenant — มีอยู่จริง ปัจจุบันไม่มีข้อมูล; ดู [reporting-audit/history](/th/inventory/reporting-audit/history))

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `report_type` | `String @db.VarChar(100)` | No | identifier เชิง logical |
| `report_category` | `enum_report_category` | No | `inventory`, `procurement`, `recipe`, `vendor`, `financial`, `operational` |
| `format` | `enum_report_format` | No | `pdf`, `excel`, `csv`, `json` |
| `status` | `enum_report_job_status` | No | Default `queued` |
| `filters` / `options` | `Json? @db.JsonB` | Yes | Default `{}` |
| `file_url` / `file_name` / `file_size` / `row_count` | — | Yes | metadata output |
| `error_message` | `String?` | Yes | populate เมื่อ `failed` |
| `started_at` / `completed_at` / `expires_at` | `DateTime?` | Yes | เวลา |
| `duration_ms` | `Int?` | Yes | cached duration |
| `requested_by_id` | `String @db.Uuid` | No | ผู้ใช้ที่ขอ |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `status`, `report_type`, `requested_by_id`, `created_at DESC`

### 5.2 Schedule — ไม่ใช่ตาราง tenant (แก้ไขแล้ว)

tenant schema ประกาศ model `tb_report_schedule` ไว้จริง แต่การค้นหาโค้ดทั่ว repo พบว่า **ไม่มีการอ้างอิงถึงมันเลย** นอกเหนือจากการประกาศ Prisma ของมันเอง — ตายแล้ว รูปแบบเดียวกับที่ยืนยันแล้วสำหรับ `tb_attachment` และตระกูล `tb_widget_*` เดิม ที่เก็บ schedule จริงคือตาราง `Cronjob` แบบ generic (แถว `job_type = "report"`) ใน Postgres schema ของ service micro-cronjobs เอง ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) §5 สำหรับโมเดลที่แก้ไขแบบเต็ม

### 5.3 `tb_report_template` (platform)

Carry `name`, `description`, `report_group`, `kind` (`report` / `print`), `dialog`, `content`, `builder_key` แบบเลือกได้, `source_type` (`view` / `function` / `procedure`), `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `allow_business_unit` / `deny_business_unit`, `is_active` `@@unique([name, deleted_at])`

> **หมายเหตุเจ้าของ service:** dataset columns (`source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key`) ถูกอ่านโดย **micro-data** (map ไปยัง `model.DatasetSource`); columns ที่เหลือถูกอ่านโดย **micro-report** ดู [§1.1](#) สำหรับเหตุผลการแยก

### 5.4 `tb_print_template_mapping` (platform)

`document_type` → `report_template_id`; `is_default`, `display_label`, `display_order`, รายการ allow/deny BU, `is_active` ไม่มี uniqueness ใน DB บน `(document_type, is_default)` — แอปบังคับ default เดียว

## 6. กติกาทางธุรกิจ

- **Print template default หนึ่งตัวต่อประเภทเอกสาร** บังคับโดยแอป; การแก้ flip default เดิมเป็น off ใน transaction เดียวกัน
- **BU scoping** กติกาที่ใช้: *อนุญาตถ้าอยู่ใน allow-list AND ไม่อยู่ใน deny-list*; allow-list ว่าง = ทุก BU
- **Kind ของ template** `report` สำหรับรายการรายงานแบบ analytical; `print` สำหรับ pipeline print
- **ความถูกต้องของ source binding** `source_type` ต้องตรงกับธรรมชาติของ DB object; positional args ประกาศใน `source_params`
- **การรัน on-demand และ Print ไม่เคย queue job** ทั้งคู่เรียก viewer endpoint แบบ synchronous — lifecycle `queued → processing → (completed | failed | cancelled)` ของ `tb_report_job` มีอยู่จริงแต่ไม่มี frontend code path ใดเข้าถึงในปัจจุบัน
- **Template มาตรฐาน** — backend มีการจัดการที่แยกออกมาสำหรับ `is_standard = true` (ตามโค้ด handler ของ Go); ไม่มี UI แก้ไขให้สังเกตพฤติกรรมที่เกิดขึ้นจริงใน repo นี้

## 7. ความเชื่อมโยงข้ามโมดูล

- โมดูลธุรกรรมทั้งหมด — ทุกปุ่ม "Print" resolve ผ่าน `tb_print_template_mapping` แล้ว render ผ่าน viewer endpoint (ไม่มีแถว job)
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — tile ของ dashboard widget ดึงจากแคตตาล็อก [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) ซึ่งเป็นคนละ mechanism กับแคตตาล็อก report-template นี้
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — การ fire แบบเกิดซ้ำ; ไม่ได้อยู่เบื้องหลังด้วยตาราง tenant ในโมดูลนี้
- [reporting-audit/history](/th/inventory/reporting-audit/history) — หน้าจออ่าน `tb_report_job`; ยืนยันแล้วว่าไม่มีข้อมูลในเชิงโครงสร้าง
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — การ fire ของ schedule dispatch notification แบบลิงก์ viewer ต่อผู้รับหนึ่งคน
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — action `export` / `print` ถูก log (ยังไม่ยืนยันเทียบกับเส้นทาง viewer โดยเฉพาะในรอบนี้)
- [access-control/user](/th/inventory/access-control/user) — `requested_by_id` + ผู้รับ
- [master-data/business-unit](/th/inventory/master-data/business-unit) — BU scoping

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (บรรทัด ~6094), `enum_report_job_status` (บรรทัด ~6086), `enum_report_format` (บรรทัด ~6070), `enum_report_category` (บรรทัด ~6077)
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_report_template` (บรรทัด ~731), `tb_print_template_mapping` (บรรทัด ~806)
- **Frontend:** `../carmen-inventory-frontend-react/routes/report/` (`list/`, `schedules/`, `history/`); `lib/print-document.ts` (การเชื่อมต่อ Print ที่ใช้โดยทุกโมดูลธุรกรรม)
- **Microservice:** `../micro-report/` — `controller/report_controller.go` (`viewReport`, `generateAsync`, `history`), `controller/template_controller.go`, `controller/print_template_mapping_controller.go`
