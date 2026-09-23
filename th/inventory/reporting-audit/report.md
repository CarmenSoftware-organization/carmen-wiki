---
title: รายงาน (Report)
description: pipeline รายงาน — แคตตาล็อก report-template ของ platform (รายงานแบบรายการ + print form พร้อม default ต่อ group), endpoint print-viewer ต่อเอกสาร, export PDF สำหรับอีเมล และตาราง job/history ที่มีอยู่จริงแต่ยังไม่มีข้อมูล
published: true
date: 2026-09-23T10:06:26.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# รายงาน (Report)

> **At a Glance**
> **เจ้าของ:** Platform Admin (template) + BU admin (เลือก print form ใน Default Setting) &nbsp;·&nbsp; **ตาราง:** `tb_report_template` (platform — รายงานแบบรายการ **และ** print form, `template_type` + `is_default`), `tb_report_job` (tenant — มีอยู่จริงแต่ไม่มีข้อมูล) &nbsp;·&nbsp; **หายไปแล้ว:** `tb_print_template_mapping` (ลบเมื่อ 2026-07-23), `tb_report_schedule` (ตายแล้ว) &nbsp;·&nbsp; **ใช้โดย:** รายการรายงาน ("Run"), ทุกปุ่ม "Print" (endpoint `print-viewer` ต่อเอกสาร 11 ตัว), อีเมล PO/RFP พร้อม PDF, การ fire ตามเวลา — ไม่มีเส้นทางใดเขียนแถว job เลย

![รายงาน (Report) screen](/screenshots/reporting-audit/report.png)

## สถานะการทำงานจริง (ตรวจสอบซ้ำเมื่อ 2026-09-22)

หน้านี้ฉบับ 2026-07-22 ยังอธิบายว่า `tb_print_template_mapping` เป็น print mapping ที่ใช้งานอยู่ platform migration `20260723120000_print_form_default` (2026-07-23) **ลบตารางนั้นทิ้งแล้ว**: default ย้ายไปอยู่บน template เอง (`tb_report_template.is_default` หนึ่งตัวต่อ `report_group` ในบรรดาแถว `template_type = 'form'` ที่ยังมีชีวิต บังคับโดย partial unique index `idx_report_template_default_per_group`), `kind` กลายเป็น `template_type` (`form` | `list`) และ group `RFQ` ถูกเปลี่ยนชื่อเป็น `RFP` request print-template-mapping ใน Bruno ถูก archive เมื่อ 2026-07-29 ("endpoint not found in gateway controllers") การ Print ไม่ผ่านคู่ resolve + viewer แบบ generic อีกต่อไป — แต่ละประเภทเอกสารมี `GET /api/{bu}/{documents}/{id}/print-viewer` ของตัวเอง (§1.2)

ไม่เปลี่ยน: flow "Run" แบบ on-demand (`report-component.tsx` → `useRunReportMutation` → `POST /api/{bu}/reports/viewer`) และทุกปุ่ม Print resolve ตรงไปยัง viewer URL; ไม่มีเส้นทางใดเรียก `generate-async` จึงไม่มีเส้นทางใดเขียนแถว `tb_report_job` — การค้นหาทั่ว frontend ที่ HEAD ยังคงไม่พบผู้เรียก `generate-async` / `job-status` เลย ดู [reporting-audit/history](/th/inventory/reporting-audit/history) และ [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)

ใหม่ตั้งแต่ 2026-07-29 (ทั้งหมดอยู่ใน `micro-report` เว้นแต่ระบุไว้): export PDF สำหรับไฟล์แนบอีเมล (§1.3, 2026-09-08), รูปลายเซ็นฝังลงใน form template (2026-08-05), form template Stock In / Stock Out (`145630b`), การ resolve tenant DB ผ่าน `tb_database_pool` (2026-08-18), raw SQL `tb_inventory_period` สำหรับ lookup งวด (2026-09-16) และ internal RPC token ที่ใช้ร่วมกัน — micro-report ป้องกันทุก route ยกเว้น `/health`, `/`, `/swagger` ด้วย `GinInternalAuth` (`ffb1abf`, 2026-09-14) และ gateway/micro-business ต้องส่ง `x-internal-token` (`bb7ea9e61`, "ไม่งั้นพิมพ์เอกสารไม่ได้")

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี report คือ **pipeline การสร้างรายงาน** — การ render แบบ ad-hoc on-demand, print layout เบื้องหลังทุกปุ่ม "Print", export PDF สำหรับอีเมลขาออก และ (ในเชิงโครงสร้าง แม้จะยังไม่มีข้อมูลจริง) การ export แบบเกิดซ้ำตามเวลา มีสองตารางที่เกี่ยวข้อง บวกฐานข้อมูล scheduler ภายนอก:

- `tb_report_template` (platform) — แคตตาล็อกเดียวสำหรับทั้ง **รายงานแบบรายการ** (`template_type = 'list'`, analytical, แสดงบน `/report`) และ **print form** (`template_type = 'form'`, layout เอกสารหนึ่งแบบต่อ `report_group` เช่น `PR`, `PO`, `GRN`, `SR`, `CN`, `SI`, `SO`, `IA`, `PC`, `SC`, `RFP`) เก็บ layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`, `builder_key`), `orientation`, `signature_config`, `is_default`, รายการ allow/deny BU สร้าง/แก้บน platform admin (`api-system/report-templates`, สิทธิ์ platform `report_template.*`); แอป inventory อ่านอย่างเดียว
- `tb_report_job` (tenant) — ตาราง job/history มีอยู่จริงและเชื่อมกับ `/report/history` ถูกต้อง แต่ยืนยันแล้วว่าไม่มีการเขียนจากเส้นทาง UI ที่เข้าถึงได้เลยในปัจจุบัน

**Schedule** ของรายงานอยู่ใน service micro-cronjobs แยกต่างหาก — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)

**ดูแลโดย** Platform Admin (template) BU admin เลือกว่า form ใดจะพิมพ์แต่ละประเภทเอกสารบนหน้าจอ **Default Setting** (`/system-admin/default-setting` ส่วน "Print form" ป้อนจาก `GET /api-system/report-templates/forms?perpage=-1` — เปิดให้ผู้ใช้ BU เมื่อ `685da259b`; เหลือเพียง `AppIdGuard('report-template.findAll')` บน route นั้น) **อ่านโดย** รายการรายงาน, ทุกปุ่ม Print, การส่งอีเมล PO/RFP

### 1.1 Dataset เทียบกับการ render — การแยก micro-data

การสร้างรายงานแบ่งออกเป็นสอง Go service โดยมีออบเจกต์ **`Dataset`** (columns + rows + totals + summary) เป็นสัญญาขอบเขต:

| ความรับผิดชอบ | Columns บน `tb_report_template` | เจ้าของ | หน้าที่ |
|---|---|---|---|
| **Dataset** | `source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key` | **micro-data** | แก้ไข view / function / procedure, ประกอบ WHERE clause จาก filter, กระจายไปยัง BU ของ tenant, คืน `Dataset` ไม่ render อะไรทั้งนั้น |
| **Report** | `content`, `template_type`, `report_group`, `orientation`, `signature_config`, `is_default` | **micro-report** | รับผิดชอบรูปแบบ output (viewer URL / PDF), layout ของ template, default ของ form และการติดตาม job |

micro-report เรียก `POST /api/datasets/execute` ของ micro-data (`micro-report/service/dataset/client.go`) แล้ว render `Dataset` ที่ได้รับกลับมา; แถว `tb_report_template` ยังคงเก็บทั้งสองชุด column ไว้จริง

### 1.2 เส้นทาง Print (ต่อประเภทเอกสาร)

`printDocument()` ของ `lib/print-document.ts` map แต่ละ `PrintDocumentType` ไปยัง gateway endpoint เฉพาะ เช่น `GET /api/{bu}/purchase-orders/{id}/print-viewer?template_id=` — รูปแบบเดียวกันมีสำหรับ PR, GRN, SR, CN, SI (`stock-ins`), SO (`stock-outs`), IA, PC (`physical-counts`), SC (`spot-checks`) และ RFP (`request-for-pricings`); gateway controller 11 ตัวมี route `print-viewer` (Bruno `*/GET-print-to-report-*.bru`) **EOP** ไม่มี form template และไม่มี endpoint — ตั้งค่าได้ แต่พิมพ์ไม่ได้

แต่ละ endpoint รัน `print-report.helper.ts` ของ micro-business: เลือก template — `template_id` ของผู้เรียก (print form ที่ BU เลือก) เมื่อส่งมาและใช้ได้กับ group นั้น มิฉะนั้นใช้ form `is_default` ที่ `report_group` เท่ากับประเภทเอกสาร (error ถ้าไม่มี) — สร้าง payload header/detail, แนบคำบรรยายและรูปลายเซ็นที่ resolve จาก stage ของ workflow (`loadSignatureBlock()`, ผู้ลงนามสูงสุด 5 คน) แล้ว `POST http://micro-report/api/{bu}/report/viewer-with-data` พร้อม `x-internal-token` micro-report ดึงแต่ละ `Sig<N>Image` ออกจาก payload แล้ว **ฝังลงใน `PictureObject` ของ template** ก่อนเรียก FastReport viewer (`9a8e48a`, 2026-08-05 — viewer ไม่เคย hydrate คอลัมน์ `System.Byte[]` จาก JSON การ bind จึง render ว่างเปล่าเงียบ ๆ) viewer URL ถูกเปิดผ่าน `safeNavigationHref` (ปฏิเสธ `javascript:`/`data:`)

### 1.3 export PDF สำหรับอีเมล

`POST /api/{bu}/report/export-pdf-with-data` (`904a1c6`, 2026-09-08) render เอกสารเดียวกับที่ print จะได้ แต่คืน PDF bytes ผ่าน `/api/Report/Export/Pdf` ของ viewer (`service/render/viewer_client.go` `ExportPDF()`, `ExportReportWithExternalData()`) micro-business ใช้มันเพื่อแนบ PDF เมื่อส่ง PO ให้ vendor ทางอีเมล (`1897b4fc1`) และเมื่อส่ง RFP (`2b750267e`); ทั้งคู่เขียนแถว `email_sent` ลง `tb_activity` ไม่ว่าสำเร็จหรือล้มเหลว — ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| รันรายงาน on demand | `/report` → เลือกรายงาน → Run | `POST /api/{bu}/reports/viewer` — render viewer URL โดยตรง; **ไม่มีการเขียนแถว `tb_report_job`** พารามิเตอร์มาจาก `dialog` ของ template (`report-param-dialog.tsx`); lookup จาก `GET .../reports/lookups` |
| Print เอกสาร | action Print ของเอกสารใดก็ได้ | `GET /api/{bu}/{documents}/{id}/print-viewer?template_id=` → viewer URL — พฤติกรรม "ไม่มีแถว job" เหมือนกัน |
| ส่งอีเมล PO / RFP พร้อมแนบ PDF | หน้า detail ของ PO / RFP → Send email | micro-business → `export-pdf-with-data` → ไฟล์แนบ; activity `email_sent` |
| เลือกว่า form ใดจะพิมพ์แต่ละประเภทเอกสารใน BU นี้ | `/system-admin/default-setting` → Print form | dropdown หนึ่งตัวต่อ `report_group`; ว่าง = default ของ platform (`is_default`) |
| กรองรายการรายงาน | ช่องค้นหา + filter กลุ่มรายงาน, saved view | ค้นหาแบบ server-side; filter กลุ่มบนหน้าปัจจุบัน |
| เพิ่มหรือเปลี่ยน print layout | Platform admin (นอก UI ของ repo นี้) | `POST/PUT api-system/report-templates` (`report_template.create/update`); form `is_default` หนึ่งตัวต่อ group เท่านั้น |
| BU-scope template | แก้ `allow_business_unit` / `deny_business_unit` ของ template | Null allow-list = ทุก BU |
| ตั้งเวลา export เกิดซ้ำ | ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) | service scheduler แยกต่างหาก |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| หน้าจอ history ไม่แสดงอะไรเลยสำหรับ run ที่เพิ่งทำ | ตามที่คาดไว้ — ไม่มีเส้นทางที่เข้าถึงได้เขียน `tb_report_job` | ไม่ใช่ bug ในเส้นทางการอ่าน |
| Print คืน "no default template for this document type" | ไม่มีแถว `template_type = 'form'` ที่ยังมีชีวิตพร้อม `is_default = true` สำหรับ `report_group` นั้น และ BU ยังไม่ได้เลือก | Platform admin ตั้ง default; หรือเลือก form ใน Default Setting |
| Print คืน "template is not a valid form for this type" | `template_id` ที่ส่งมาชี้ไปที่ template ของ `report_group` อื่นหรือ template แบบ `list` | แก้การเลือก print form ของ BU |
| ทุกการ print ล้มเหลวด้วย 401 จาก micro-report | `x-internal-token` (`INTERNAL_RPC_SECRET`) ขาดหรือไม่ตรงกันระหว่าง micro-business/gateway กับ micro-report | Ops: จัด secret ให้ตรงกัน (`bb7ea9e61`) |
| บล็อกลายเซ็นว่างบนงานพิมพ์ | template ไม่มีบล็อก `signature_config` สำหรับ slot นั้น หรือ stage ของ workflow resolve ผู้ลงนามไม่ได้ | เช็ค `signature_config.blocks` บน template และ stage ของ workflow ของเอกสาร |
| ข้อมูลรายงานล้มเหลวด้วย "view not found" | `source_type` / `source_name` drift | จัด template binding ให้ตรงกับ DB object |
| ตัวเลือกงวดว่างใน dialog ของรายงาน | lookup อ่าน `tb_inventory_period` (เปลี่ยนชื่อจาก `tb_period`, `cf4ea57`) — build เก่าของ micro-report ยัง query `tb_period` | deploy micro-report ≥ 2026-09-16 |
| Template ไม่เห็นใน BU | `allow_business_unit` exclude; หรือ `deny_business_unit` include | แก้ BU scoping |

## 4. กรณีพิเศษ

- **การรัน on-demand และ Print เป็นการ render แบบ synchronous ผ่าน viewer ไม่ใช่ job แบบ queue** ไม่มีแถว `tb_report_job`, ไม่มี entry ใน history, ไม่มี retention `expires_at` ใด ๆ ใช้กับทั้งสอง
- **default หนึ่งตัวต่อ group ตอนนี้เป็น invariant ของ DB** (partial unique index) ไม่ใช่การเช็คในแอป — migration 2026-07-23 จะล้มเหลวอย่างชัดเจนถ้ามี mapping ที่ active สองตัวสำหรับประเภทเอกสารเดียว
- **connection ของ tenant ประกอบจากสองตาราง platform** micro-report resolve `tb_business_unit.db_schema` + `tb_database_pool` (`host`, `port`, `database`, `username`, `password` เป็น ciphertext `enc:v1`) ผ่าน LEFT JOIN (`micro-report/db/db.go` `resolveTenantDBURL`, platform migration `20260813010000_database_pool_drop_db_connection`); BU ที่ไม่มี pool หรือ schema คือ `ErrTenantNotProvisioned` (ข้ามได้) และ pool password แบบ plaintext เป็น hard error
- **รูปลายเซ็นไม่เดินทางเป็นข้อมูล** ถูกฝังลงใน template XML ต่อการ render; คำบรรยายเป็นคอลัมน์ string ธรรมดา
- **Lifecycle ของ job แบบ async มีอยู่จริงแต่ไม่ถูกใช้งาน** `queued → processing → (completed | failed | cancelled)` ยังเป็นสัญญาของโมเดล; มีเพียง `generate-async` ที่เดินหน้ามัน และไม่มีอะไรใน frontend เรียกใช้เลย

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: **ผสม** — tenant สำหรับตาราง job/history, platform สำหรับ template Schedule **ไม่ใช่** ตาราง tenant — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) §5

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

### 5.2 Schedule — ไม่ใช่ตาราง tenant

tenant schema ยังประกาศ `tb_report_schedule` อยู่ แต่ไม่มีโค้ดอ้างอิงถึงมัน ที่เก็บ schedule จริงคือตาราง `Cronjob` (`job_type = "report"`) ใน micro-cronjobs — [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) §5

### 5.3 `tb_report_template` (platform)

| ฟิลด์ | Type | คำอธิบาย |
| --- | --- | --- |
| `name`, `description` | text | `@@unique([name, deleted_at])` |
| `report_group` | `VarChar(100)` | กลุ่ม analytical สำหรับ list; **ประเภทเอกสาร** สำหรับ form (`PR`, `PO`, `GRN`, `SR`, `CN`, `SI`, `SO`, `IA`, `PC`, `SC`, `RFP`, …) |
| `template_type` | text, default `list` | `form` (layout เอกสารระเบียนเดียว) หรือ `list` (รายงานแบบตาราง) มาแทน `kind` |
| `dialog`, `content` | text | dialog + layout XML ของ FastReport |
| `builder_key` | `VarChar(100)`, default `''` | เชื่อมไปยัง `report.Definition` ของ Go (เช่น `po-document`, `cn-document-landscape`) |
| `view_name` | text? | legacy; ให้ใช้ `source_type` + `source_name` แทน |
| `source_type` / `source_name` / `source_params` | `view`/`function`/`procedure`, ชื่อ, `{ "params": [...] }` | อ่านโดย micro-data |
| `orientation` | `portrait` / `landscape` | มาแทน suffix ชื่อ "Document Landscape" แบบเดิม |
| `signature_config` | JSONB `{ "blocks": [{ "key": "Sig1Name", "label": "Requestor", "required": true }, …] }` | slot ลายเซ็นที่มี label บน print layout |
| `is_standard` | bool, default `true` | template ที่ seed มา (`db/seed/report-templates/*.xml` + `_metadata.json`) |
| `is_default` | bool, default `false` | form ที่ใช้เมื่อ BU ยังไม่ได้เลือกสำหรับ group นี้ partial unique index `idx_report_template_default_per_group` บน `(report_group) WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` — มีเฉพาะใน migration SQL แสดงใน Prisma ไม่ได้ |
| `allow_business_unit` / `deny_business_unit` | JSONB? | BU scoping; allow เป็น null = ทุก BU |
| `is_active`, `doc_version`, คอลัมน์ audit | — | มาตรฐาน |

form ที่ seed ไว้ที่ HEAD รวมเอกสารแนวตั้ง + แนวนอนสำหรับ CN, GRN, IA, Invoice, PC, PO, PR, RFQ/RFP, SC, SI, SO, SR และรายงานแบบรายการ เช่น Inventory Balance, Stock Card, Receiving Detail, Purchase Analysis, Menu Engineering, Recipe Card, EOP Checklist/Adjustment

### 5.4 การ resolve default ของ print form (มาแทน `tb_print_template_mapping`)

```
resolvePrintTemplate(documentType, templateId?):
  if templateId:
    row = tb_report_template where id = templateId and template_type = 'form'
          and report_group = documentType and deleted_at is null
    if none -> error "not a valid form for this type"
  else:
    row = tb_report_template where report_group = documentType
          and template_type = 'form' and is_default and deleted_at is null
    if none -> error "no default form for this type"
  return row
```

`templateId` คือตัวเลือกของ BU จากหน้าจอ Default Setting (ส่งเป็น `?template_id=` โดย `printDocument()`); `is_default` ของ platform เป็น fallback

## 6. กติกาทางธุรกิจ

- **Print form default หนึ่งตัวต่อประเภทเอกสาร** — บังคับโดย DB ด้วย partial unique index บน `tb_report_template` (2026-07-23); ตัวเลือกของ BU ไม่เคยเปลี่ยน `is_default` แค่ override ตอน print
- **BU scoping** กติกาที่ใช้: *อนุญาตถ้าอยู่ใน allow-list AND ไม่อยู่ใน deny-list*; allow-list ว่าง = ทุก BU
- **Type ของ template** `list` สำหรับรายการรายงานแบบ analytical; `form` สำหรับ pipeline print `GET /api/{bu}/reports/templates` คืนเฉพาะ `template_type = 'list'` (`template_controller.go` `listFlat`); `GET /api-system/report-templates/forms` คืน form
- **ความถูกต้องของ source binding** `source_type` ต้องตรงกับธรรมชาติของ DB object; positional args ประกาศใน `source_params`
- **การรัน on-demand และ Print ไม่เคย queue job** ทั้งคู่เรียก viewer endpoint แบบ synchronous — lifecycle ของ `tb_report_job` มีอยู่จริงแต่ไม่มี frontend code path ใดเข้าถึง
- **การเรียกภายในแนบ `x-internal-token`** micro-business → micro-report (print, PDF), gateway → micro-report (report, template), micro-report → micro-notification (`pkg/notify/client.go`, HTTP RPC `POST /rpc` พร้อม body `{pattern, data}`; แก้ pattern พหูพจน์ `0b364cd`)

## 7. ความเชื่อมโยงข้ามโมดูล

- โมดูลธุรกรรมทั้งหมด — ทุกปุ่ม "Print" เรียก endpoint `print-viewer` ของตัวเอง; form มาจากตัวเลือกใน Default Setting ของ BU หรือ default ของ group
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — tile ของ dashboard ดึงจากแคตตาล็อก [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) ซึ่งเป็นคนละ mechanism กับแคตตาล็อก template นี้
- [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) — การ fire แบบเกิดซ้ำ; ไม่ได้อยู่เบื้องหลังด้วยตาราง tenant
- [reporting-audit/history](/th/inventory/reporting-audit/history) — หน้าจออ่าน `tb_report_job`; ยืนยันแล้วว่าไม่มีข้อมูลในเชิงโครงสร้าง
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — การ fire ของ schedule dispatch notification แบบลิงก์ viewer ต่อผู้รับหนึ่งคน
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — `email_sent` เมื่อส่งอีเมล PO/RFP; `print` / `export` ยังไม่ยืนยันเทียบกับเส้นทาง viewer
- [system-config/inventory-period](/th/inventory/system-config/period) — lookup งวดอ่าน `tb_inventory_period`
- [master-data/business-unit](/th/inventory/master-data/business-unit) — BU scoping; tenant DB ผ่าน `tb_database_pool`

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job`, `enum_report_job_status`, `enum_report_format`, `enum_report_category`; `tb_report_schedule` (ตายแล้ว)
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_report_template`; migration `20260429110000_add_print_template_mapping` (สร้างตาราง mapping), `20260723120000_print_form_default` (ย้าย default ไปบน template และลบมันทิ้ง), `20260813010000_database_pool_drop_db_connection`
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.controller.ts` (`POST generate`, `GET types`, `GET templates`, `GET templates/:id`, `POST viewer`, `POST data`, `GET lookups`, `POST generate-async`, `GET jobs/:job_id`, `GET history`, schedules), `src/platform/platform_report-templates/platform_report-templates.controller.ts` (`GET forms`, CRUD, `GET db-objects`), route `print-viewer` ของ controller ต่อเอกสาร
- **micro-business:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/print-report.helper.ts` (การ resolve template, payload, ลายเซ็น, การเรียก viewer + PDF), `procurement/purchase-order/purchase-order.service.ts` (`printToReport`, อีเมล + `email_sent`)
- **micro-report:** `../micro-report/controller/report_controller.go` (`viewReport`, `viewReportWithData`, `exportPdfWithData`, `reportData`, `lookups`, `dbObjects`, `dialogParams`, `generateAsync`, `jobStatus`, `history`; SQL `tb_inventory_period`), `controller/template_controller.go` (`listFlat`), `service/render/viewer_client.go` (`View`, `ExportPDF`), `service/report_service.go` (`ExportReportWithExternalData`), `service/dataset/client.go` (`/api/datasets/execute`), `db/db.go` (`resolveTenantDBURL`), `middleware/internal_auth.go`, `pkg/notify/client.go`, `db/seed/report-templates/` (+ `_metadata.json`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/report/` (`list/`, `schedules/`, `history/`, `shared/use-report.ts`), `lib/print-document.ts` (`DEDICATED_PRINT_ENDPOINTS`), `routes/system-admin/default-setting/use-report-form-templates.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/documents-and-reports/report/*`, `platform/report-templates/GET-find-forms-…bru`, `platform/report-template/*`, `*/GET-print-to-report-*.bru`; ที่ archive แล้ว `_archived/2026-07-29/platform/print-template-mapping/*` และ `_archived/2026-07-29/documents-and-reports/report/GET-resolve-print-template-…bru`
