---
title: รายงาน (Report)
description: pipeline การสร้างรายงาน — แถว job และ schedule ฝั่ง tenant ที่อยู่เบื้องหลังของ template และ document-type print mapping ฝั่งแพลตฟอร์ม
published: true
date: 2026-05-19T23:55:00.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# รายงาน (Report)

> **At a Glance**
> **เจ้าของ:** Sysadmin (schedule) + Platform Admin (template, mapping) &nbsp;·&nbsp; **ตาราง:** `tb_report_job` + `tb_report_schedule` (tenant), `tb_report_template` + `tb_print_template_mapping` (platform) &nbsp;·&nbsp; **ใช้โดย:** ทุกปุ่ม "Print" + dashboard / scheduled export &nbsp;·&nbsp; Pipeline เต็มของรายงานและ print layout

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี report คือ **pipeline เต็มของการสร้างรายงาน** — การ export แบบ ad-hoc on-demand + การ export แบบเกิดซ้ำตามเวลา + print layout เบื้องหลังทุกปุ่ม "Print" สี่ตารางข้ามสอง schema:

- `tb_report_template` (platform) — แคตตาล็อก template (`report` แบบ analytical หรือ `print` layout); เก็บ layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`), orientation, signatures
- `tb_print_template_mapping` (platform) — map `document_type` (`PO`, `PR`, `SR`, `GRN`, `CN`, `IA`, …) ไปยังหนึ่งหรือหลาย template; `is_default = true` หนึ่งตัวต่อประเภท
- `tb_report_job` (tenant) — ประวัติการ execute (queued / processing / completed / failed / cancelled); filter, รูปแบบ, metadata ของ output
- `tb_report_schedule` (tenant) — การรันแบบเกิดซ้ำขับด้วย cron; enqueue job

Schema ผสมสะท้อนการ deploy: template + mapping ถูก curate รวมศูนย์; job + schedule เป็นข้อมูล tenant

**ดูแลโดย** Platform Admin (template, mapping), Sysadmin (schedule) **อ่านโดย** รายการรายงาน, เมนู "Print as…", widget บน dashboard

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| รันรายงาน on demand | เมนู Reports → เลือกรายงาน → Run | Insert แถว `tb_report_job` |
| ดาวน์โหลด job ที่เสร็จ | Reports → Jobs → คลิกชื่อไฟล์ | resolve `file_url`; เคารพ `expires_at` |
| ตั้งเวลา export เกิดซ้ำ | Reports → Schedules → New | cron expression + filter + ผู้รับ |
| เพิ่ม print layout สำหรับประเภทเอกสาร | Platform Admin → Print Templates | toggle `is_default` เพื่อสลับ default |
| BU-scope template | แก้ `allow_business_unit` / `deny_business_unit` ของ template | Null allow-list = ทุก BU |
| รัน job ที่ล้มเหลวซ้ำ | Reports → Jobs → Re-run | สร้าง `tb_report_job` ใหม่ |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| Job ค้างที่ `queued` | Executor ไม่หยิบ | เช็คสุขภาพ executor และ `idx_report_job_status` |
| Job ล้มเหลวด้วย "view not found" | `source_type` / `source_name` drift | จัด template binding ให้ตรงกับ DB object |
| มี default หลายตัวต่อประเภทเอกสาร | invariant ของแอปถูกละเมิด | ซ่อม: ให้มี `is_default = true` หนึ่งตัว; ที่เหลือเป็น false |
| ดาวน์โหลด 404 | output ถูก reap ตาม `expires_at` | รัน job ซ้ำ |
| Template ไม่เห็นใน BU | `allow_business_unit` exclude; หรือ `deny_business_unit` include | แก้ BU scoping |

## 4. กรณีพิเศษ

- **Source binding drift** เป็นสาเหตุใหญ่สุดของ job ที่ล้มเหลว — รักษา `source_type` / `source_name` ให้สอดคล้องกับ DB object จริง
- **Template มาตรฐาน vs ที่ผู้ใช้กำหนด** UI ของ `is_standard = true` มักป้องกันการลบและเตือนเมื่อแก้
- **Lifecycle ของ job** `queued → processing → (completed | failed | cancelled)` Executor ตั้ง `started_at` / `completed_at` / `duration_ms`
- **Retention ของ output** `expires_at` คือสัญญาของ reaper ของที่จัดเก็บ

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: **ผสม** — tenant สำหรับ jobs/schedules, platform สำหรับ templates/mappings

### 5.1 `tb_report_job` (tenant)

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

### 5.2 `tb_report_schedule` (tenant)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` / `name` | `String` | No | คีย์ |
| `report_type` / `report_template_id` | `String` | Mixed | id เชิง logical + template binding แบบเลือกได้ |
| `format` | `enum_report_format` | No | รูปแบบ output |
| `cron_expression` | `String @db.VarChar(100)` | No | cron มาตรฐาน |
| `schedule_config` / `filters` / `options` / `recipients` | `Json?` | Yes | Scheduler + ตัวเลือกการรัน + email/user IDs |
| `is_active` | `Boolean` | No | Default `true` |
| `last_run_at` / `next_run_at` | `DateTime?` | Yes | bookkeeping ของ scheduler |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.3 `tb_report_template` (platform)

Carry `name`, `description`, `report_group`, `kind` (`report` / `print`), `dialog`, `content`, `builder_key` แบบเลือกได้, `source_type` (`view` / `function` / `procedure`), `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `allow_business_unit` / `deny_business_unit`, `is_active` `@@unique([name, deleted_at])`

### 5.4 `tb_print_template_mapping` (platform)

`document_type` → `report_template_id`; `is_default`, `display_label`, `display_order`, รายการ allow/deny BU, `is_active` ไม่มี uniqueness ใน DB บน `(document_type, is_default)` — แอปบังคับ default เดียว

## 6. กติกาทางธุรกิจ

- **Print template default หนึ่งตัวต่อประเภทเอกสาร** บังคับโดยแอป; การแก้ flip default เดิมเป็น off ใน transaction เดียวกัน
- **BU scoping** กติกาที่ใช้: *อนุญาตถ้าอยู่ใน allow-list AND ไม่อยู่ใน deny-list*; allow-list ว่าง = ทุก BU
- **Kind ของ template** `report` สำหรับเมนู analytical; `print` สำหรับ pipeline print (ซ่อนจากเมนู reports)
- **ความถูกต้องของ source binding** `source_type` ต้องตรงกับธรรมชาติของ DB object; positional args ประกาศใน `source_params`
- **Lifecycle ของ job** `queued → processing → (completed | failed | cancelled)`
- **Retention ของ output** `expires_at` ควบคุม reaper
- **Template มาตรฐาน** UI มักป้องกันการลบ

## 7. ความเชื่อมโยงข้ามโมดูล

- โมดูลธุรกรรมทั้งหมด — ทุกปุ่ม "Print" resolve ผ่าน `tb_print_template_mapping`
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — tile ของ widget สามารถฝัง report ได้
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — การ completion ของ schedule อาจ dispatch notification
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — action `export` / `print` ถูก log
- [access-control/user](/th/inventory/access-control/user) — `requested_by_id` + ผู้รับ
- [master-data/business-unit](/th/inventory/master-data/business-unit) — BU scoping

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (lines ~5652-5683), `tb_report_schedule` (lines ~5685-5709)
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_report_template` (lines ~589-656), `tb_print_template_mapping` (lines ~663-688)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/reporting/` (tenant reports/jobs/schedules); template admin ในแอป platform
- **Microservice:** `../micro-report/` — worker การ execute รายงาน
