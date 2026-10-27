---
title: รายงาน (Report)
description: pipeline รายงาน — แคตตาล็อก report-template ของ Backstage (รายงานแบบรายการ + print form), print-viewer ต่อเอกสาร, export PDF/CSV และตาราง job/history ที่มีอยู่จริงแต่ยังไม่มีข้อมูล
published: true
date: '2026-10-27T15:00:00.000Z'
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# รายงาน (Report)

> **At a Glance**
> **เจ้าของ:** Backstage admin (template) + BU admin (เลือก print form ใน Default Setting) &nbsp;·&nbsp; **ตาราง:** `tb_report_template` (Backstage schema — รายงานแบบรายการ **และ** print form, `template_type` + `is_default`), `tb_report_job` (tenant — มีอยู่จริงแต่ไม่มีข้อมูล) &nbsp;·&nbsp; **หายไปแล้ว:** `tb_print_template_mapping` (ลบเมื่อ 2026-07-23), `tb_report_schedule` (ตายแล้ว) &nbsp;·&nbsp; **ใช้โดย:** รายการรายงาน ("Run"), ทุกปุ่ม "Print" (endpoint `print-viewer` ต่อเอกสาร 11 ตัว), อีเมล PO/RFP พร้อม PDF, การ fire ตามเวลา — ไม่มีเส้นทางใดเขียนแถว job เลย

![รายงาน (Report) screen](/screenshots/reporting-audit/report.png)

## สถานะการทำงานจริง (ตรวจสอบซ้ำเมื่อ 2026-10-27)

การเปลี่ยนแปลงตั้งแต่ 2026-09-22 (micro-report `c9ebf77..origin/main`, FE `0713cbc9..391062b5`, backend `ef4d6f08f..c9d788829`):

1. **Export data (CSV)** action ที่สองถัดจาก Run: `POST /api/{bu}/reports/export { template_id, filters }` → micro-report `POST /api/{bu}/report/export` map dataset ของ template ผ่าน **Export XML** (`tb_report_template.export_xml`) เป็น CSV แบบ UTF-8 with BOM (§ 1.4)
2. **สวิตช์ต่อ template และ availability** `allow_run` (ค่าเริ่มต้นเปิด) และ `allow_export` (ค่าเริ่มต้นปิด) บน template กำหนดว่าปุ่มใดแสดงในรายการรายงาน; template ที่ถูกปฏิเสธสำหรับ BU จะตอบ **403 `REPORT_TEMPLATE_UNAVAILABLE`** พร้อม `reason` (§ 1.5)
3. **Dialog พารามิเตอร์ฉลาดขึ้น** `<Dialog Cols>`, `<Group>`, `Label=` บน control, `<TextBox>`, `<Note>`, ช่อง From-To เป็นคู่ในแถวเดียว, ความจำพารามิเตอร์ล่าสุด 30 นาทีต่อ BU/รายงาน, รายการ picker ดึงใหม่ทุกครั้งที่เปิด dialog และการค้นหา picker ฝั่ง server (§ 1.6)
4. **Template รายงานแบบรายการใหม่** ที่ seed ใน micro-report: Landed Cost Report (เปลี่ยนชื่อจาก Extra Cost Report), Monthly Inventory Movement, Slow Moving, Receiving List, Purchase Request List, Purchase Order List, Product List, Vendor List รวมถึง form Vendor Detail และ Product Category (สองตัวหลังพิมพ์จากหน้า vendor และ category) รายงานเดิมหลายตัวได้ layout ใหม่ (§ 5.3)
5. **เปลี่ยนชื่อ** schema "platform" ตอนนี้คือ "Backstage": package `prisma-shared-schema-backstage`, route ของ gateway `api-system/backstage/*` (API admin ของ report-template ยังคงเป็น `api-system/report-templates`), env `PLATFORM_*` → `BACKSTAGE_*`

**การตรวจสอบ 2026-09-22 (คงไว้)**

หน้านี้ฉบับ 2026-07-22 ยังอธิบายว่า `tb_print_template_mapping` เป็น print mapping ที่ใช้งานอยู่ platform migration `20260723120000_print_form_default` (2026-07-23) **ลบตารางนั้นทิ้งแล้ว**: default ย้ายไปอยู่บน template เอง (`tb_report_template.is_default` หนึ่งตัวต่อ `report_group` ในบรรดาแถว `template_type = 'form'` ที่ยังมีชีวิต บังคับโดย partial unique index `idx_report_template_default_per_group`), `kind` กลายเป็น `template_type` (`form` | `list`) และ group `RFQ` ถูกเปลี่ยนชื่อเป็น `RFP` request print-template-mapping ใน Bruno ถูก archive เมื่อ 2026-07-29 ("endpoint not found in gateway controllers") การ Print ไม่ผ่านคู่ resolve + viewer แบบ generic อีกต่อไป — แต่ละประเภทเอกสารมี `GET /api/{bu}/{documents}/{id}/print-viewer` ของตัวเอง (§1.2)

ไม่เปลี่ยน: flow "Run" แบบ on-demand (`report-component.tsx` → `useRunReportMutation` → `POST /api/{bu}/reports/viewer`) และทุกปุ่ม Print resolve ตรงไปยัง viewer URL; ไม่มีเส้นทางใดเรียก `generate-async` จึงไม่มีเส้นทางใดเขียนแถว `tb_report_job` — การค้นหาทั่ว frontend ที่ HEAD ยังคงไม่พบผู้เรียก `generate-async` / `job-status` เลย ดู [reporting-audit/history](/th/inventory/reporting-audit/history) และ [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)

ใหม่ตั้งแต่ 2026-07-29 (ทั้งหมดอยู่ใน `micro-report` เว้นแต่ระบุไว้): export PDF สำหรับไฟล์แนบอีเมล (§1.3, 2026-09-08), รูปลายเซ็นฝังลงใน form template (2026-08-05), form template Stock In / Stock Out (`145630b`), การ resolve tenant DB ผ่าน `tb_database_pool` (2026-08-18), raw SQL `tb_inventory_period` สำหรับ lookup งวด (2026-09-16) และ internal RPC token ที่ใช้ร่วมกัน — micro-report ป้องกันทุก route ยกเว้น `/health`, `/`, `/swagger` ด้วย `GinInternalAuth` (`ffb1abf`, 2026-09-14) และ gateway/micro-business ต้องส่ง `x-internal-token` (`bb7ea9e61`, "ไม่งั้นพิมพ์เอกสารไม่ได้")

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี report คือ **pipeline การสร้างรายงาน** — การ render แบบ ad-hoc on-demand, print layout เบื้องหลังทุกปุ่ม "Print", export PDF สำหรับอีเมลขาออก และ (ในเชิงโครงสร้าง แม้จะยังไม่มีข้อมูลจริง) การ export แบบเกิดซ้ำตามเวลา มีสองตารางที่เกี่ยวข้อง บวกฐานข้อมูล scheduler ภายนอก:

- `tb_report_template` (Backstage schema) — แคตตาล็อกเดียวสำหรับทั้ง **รายงานแบบรายการ** (`template_type = 'list'`, analytical, แสดงบน `/report`) และ **print form** (`template_type = 'form'`, layout เอกสารหนึ่งแบบต่อ `report_group` เช่น `PR`, `PO`, `GRN`, `SR`, `CN`, `SI`, `SO`, `IA`, `PC`, `SC`, `RFP`) เก็บ layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`, `builder_key`), `orientation`, `signature_config`, `is_default`, `export_xml`, `allow_run`, `allow_export`, `calculation_methods` ที่รองรับ, รายการ allow/deny BU และ (2026-10-08) `name`/`description` หลายภาษากับตารางประวัติเวอร์ชัน `tb_report_template_version` สร้าง/แก้บน Backstage admin (`api-system/report-templates`, สิทธิ์ Backstage `report_template.*`); แอป inventory อ่านอย่างเดียว
- `tb_report_job` (tenant) — ตาราง job/history มีอยู่จริงและเชื่อมกับ `/report/history` ถูกต้อง แต่ยืนยันแล้วว่าไม่มีการเขียนจากเส้นทาง UI ที่เข้าถึงได้เลยในปัจจุบัน

**Schedule** ของรายงานอยู่ใน service micro-cronjobs แยกต่างหาก — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule)

**ดูแลโดย** Backstage admin (template) BU admin เลือกว่า form ใดจะพิมพ์แต่ละประเภทเอกสารบนหน้าจอ **Default Setting** (`/system-admin/default-setting` ส่วน "Print form" ป้อนจาก `GET /api-system/report-templates/forms?perpage=-1` — เปิดให้ผู้ใช้ BU เมื่อ `685da259b`; เหลือเพียง `AppIdGuard('report-template.findAll')` บน route นั้น) **อ่านโดย** รายการรายงาน, ทุกปุ่ม Print, การส่งอีเมล PO/RFP

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

### 1.4 Export data (CSV ผ่าน Export XML)

| ด้าน | พฤติกรรม |
|---|---|
| ปุ่ม | "Export data" ใน dialog พารามิเตอร์ของรายงาน แสดงเฉพาะเมื่อ template `has_export` (= `allow_export` และ `export_xml` ไม่ว่าง); ป้องกันการดับเบิลคลิกด้วย ref (`d71ef5f0`) hook เดียวกัน (`hooks/use-export-report.ts`) ขับปุ่ม Print/Export บนหน้า product-category (`82e9c12d`, form Product Category Report) |
| Request | `POST /api/{bu}/reports/export` (gateway `reports.controller.ts:398`) พร้อม `{ template_id, filters }`; filter เดียวกับ Run |
| Response | `200 text/csv; charset=utf-8` (BOM), `Content-Disposition: attachment; filename="<slug>_<yyyyMMdd_HHmmss>.csv"` (นาฬิกา Asia/Bangkok), `X-Row-Count`; gateway เพิ่ม `Access-Control-Expose-Headers: Content-Disposition, X-Row-Count` เพื่อให้ SPA อ่านได้ ถ้าไม่มีแถวเลย FE แสดง info toast แทนการดาวน์โหลด |
| Error | `400 export_not_configured` (ไม่มี/ว่าง Export XML) หรือ XML ไม่ถูกต้อง; `403 REPORT_TEMPLATE_UNAVAILABLE` (`export_disabled` หรือ BU/costing-method ปฏิเสธ) |
| Mapping | `<Export FileName GroupBy?>` พร้อม key `<Sort Field Desc?>` เรียงลำดับ และ `<Column Header Field|Value|Expression Format?>`; ลำดับคอลัมน์ = ลำดับ CSV `GroupBy` ตรึงการจัดกลุ่มให้ export เป็นหนึ่งแถวต่อเอกสารไม่ว่า Group By บนหน้าจอจะเป็นอะไร; สตริงตัวเลข (รวม `NUMERIC` ที่คืนเป็นข้อความ) เรียงและพิมพ์เป็นตัวเลข; สตริง `inf`/`NaN` ที่ใช้ format ตัวเลขไม่นับเป็นตัวเลข; เซลล์ที่ขึ้นต้นด้วยอักขระสูตรจะถูกทำให้เป็นกลาง (ป้องกัน CSV formula-injection, `6cbd433`) Parser: `micro-report/service/export_xml.go` |
| ข้อมูล | row builder เดียวกับ viewer (`buildRowsForTemplate`) โดยฉีดคอลัมน์ที่คำนวณ ปล่อยวันที่เป็นค่าดิบเพื่อให้ `Format` parse ได้; เพิ่ม `GroupBy`, `BuName` และ (เมื่อ template ประกาศ) `CalculationMethod` ต่อแถว |

Template ที่ seed พร้อม Export XML ที่ HEAD: Product List, Product Category, Credit Note Detail, Purchase Order List (ไฟล์ `db/seed/report-templates/*.export.xml`); ตัวอื่นตั้งค่าได้ใน Backstage

### 1.5 Availability, `allow_run` และ `allow_export`

`EnsureAvailable` รันก่อนทุก view/export template จะถูกปฏิเสธสำหรับ BU ด้วย `403 { code: "REPORT_TEMPLATE_UNAVAILABLE", reason }`:

| `reason` | สาเหตุ |
|---|---|
| `bu_denied` | BU อยู่ใน `deny_business_unit` |
| `bu_not_allowed` | `allow_business_unit` ไม่ว่างและไม่มี BU นี้ |
| `calculation_method_unsupported` | `calculation_methods` ไม่ว่างและไม่รวม costing method ของ BU (`fifo`, `average`, `average_per_location`) |
| `run_disabled` | `allow_run = false` บน template แบบ `list` สำหรับ **Run** แบบ interactive เท่านั้น (`ViewReportForUser`); form และการรันตาม schedule ไม่สนใจ |
| `export_disabled` | `allow_export = false` |

`GET /api/{bu}/reports/templates?actionable=true` (ใช้เฉพาะ `/report`) ซ่อน template ที่ไม่มีทั้ง Run และ Export; ตัวเลือกรายงานในฟอร์ม schedule เรียกโดยไม่ใส่ `actionable` จึงเห็นทั้งหมด `GET /api/{bu}/reports/templates/:template_id` คืน 200 หรือ 403 เดียวกัน (404 เมื่อไม่พบ/ไม่ active) FE map `run_disabled` / `export_disabled` ไปเป็น toast "action disabled" และ reason อื่นทั้งหมดเป็น "unavailable for this business unit" ดู [schedule](/th/inventory/reporting-audit/schedule) § 1.2 สำหรับวิธีที่การรันตาม schedule จัดการ template ที่ถูกปฏิเสธ

### 1.6 Dialog พารามิเตอร์ (XML `dialog` ของ template)

Parse ในเบราว์เซอร์ (`routes/report/list/parse-report-dialog.ts`; ฟอร์ม schedule มี parser ของตัวเอง `routes/report/schedules/parse-schedule-dialog.ts` ซึ่งทำ `<Group>` ให้แบนและรองรับ `Label=` แต่ไม่สนใจ layout)

| Element / attribute | ผล |
|---|---|
| `<Dialog Cols="n">` | จัด control เป็น `n` คอลัมน์ (สูงสุด 4, `MAX_COLS`); modal กว้างขึ้น (`sm:max-w-3xl` / `sm:max-w-5xl`) `ColSpan` บน control ขยายข้ามคอลัมน์ |
| `<Group Label?>` | กล่องที่ผู้เขียนกำหนด พร้อมหัวข้อได้; ซ้อน group ได้; ไม่มีการจับคู่ From/To อัตโนมัติภายใน |
| `Label="…"` บน control | มีผลเหนือ `<Label>` ก่อนหน้า; ค่าว่างแสดง `Name` ของ control |
| `<Lookup Name DataSource|Items+Values Multi?>` | Picker; `Multi="true"` render เป็น checkbox group และส่งค่าคั่นด้วยจุลภาค รายการตัวเลือกมาจาก `GET /api/{bu}/reports/lookups?types=` และดึงใหม่ทุกครั้งที่เปิด dialog (`staleTime 0`) |
| `<Date Name Value>` | ช่องวันที่ |
| `<TextBox Name Value Type="Number" Min>` | ข้อความอิสระ; `Type="Number"` รับจำนวนเต็ม ≥ `Min` (ค่าเริ่มต้น 1) และจำเป็นต้องกรอก (Slow Moving: `Day`) |
| `<Note Text>` | ข้อความที่ไม่ใช่ filter ใต้ช่อง; `@today` ถูกแทนด้วยวันที่วันนี้ `dd/MM/yyyy` |
| คู่ `…From` / `…To` | render ในแถวเดียวกันและเติมค่าล่วงหน้าเพื่อไม่ให้ช่วงว่าง (`6e1ee12a`) |

การค้นหาใน picker: การพิมพ์ส่ง `GET …/reports/lookups?types=<source>&search=<text>&limit=50` (debounce 150 ms) เพื่อให้เข้าถึงแถวที่เกิน 500 แถวแรกตามรหัสได้; ค่าเริ่มต้นและสูงสุดของ lookup ใน micro-report คือ **500 แถวต่อ type**, `limit` รับ 1-500, `search` เป็นการจับคู่รหัสหรือชื่อแบบไม่สนตัวพิมพ์เล็ก/ใหญ่ (ไม่ใช้กับ `period`) หน่วยความจำพารามิเตอร์: ค่าและป้ายของ picker จาก **Run** ล่าสุดถูกเก็บใน `localStorage` ต่อ BU + รายงาน เป็นเวลา **30 นาที** (`carmen.report-params:<bu>:<report>`, `report-param-memory.ts`); ถ้าหมดอายุหรืออ่าน storage ไม่ได้จะ fallback เป็นค่าเริ่มต้นเงียบ ๆ หัวรายการรายงานแสดงคำอธิบาย template ใต้ชื่อในโหมด list (`bbdfa238`) และล้างเลขหน้าเมื่อค้นหาจากหน้า 2+ (`e76637ce`)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| รันรายงาน on demand | `/report` → เลือกรายงาน → Run | `POST /api/{bu}/reports/viewer` — render viewer URL โดยตรง; **ไม่มีการเขียนแถว `tb_report_job`** พารามิเตอร์มาจาก `dialog` ของ template (§ 1.6, `report-param-dialog.tsx`); lookup จาก `GET .../reports/lookups` ปุ่ม Run ถูกซ่อนเมื่อ template มี `allow_run = false` |
| ดาวน์โหลดข้อมูลของรายงานเป็น CSV | `/report` → เลือกรายงาน → Export data | § 1.4; เฉพาะ template ที่มี Export XML และ `allow_export` |
| Print เอกสาร | action Print ของเอกสารใดก็ได้ | `GET /api/{bu}/{documents}/{id}/print-viewer?template_id=` → viewer URL — พฤติกรรม "ไม่มีแถว job" เหมือนกัน |
| ส่งอีเมล PO / RFP พร้อมแนบ PDF | หน้า detail ของ PO / RFP → Send email | micro-business → `export-pdf-with-data` → ไฟล์แนบ; activity `email_sent` |
| เลือกว่า form ใดจะพิมพ์แต่ละประเภทเอกสารใน BU นี้ | `/system-admin/default-setting` → Print form | dropdown หนึ่งตัวต่อ `report_group`; ว่าง = form `is_default` ของ group |
| กรองรายการรายงาน | ช่องค้นหา + filter กลุ่มรายงาน, saved view | ค้นหาแบบ server-side; filter กลุ่มบนหน้าปัจจุบัน |
| เพิ่มหรือเปลี่ยน print layout | Backstage admin (นอก UI ของ inventory) | `POST/PUT api-system/report-templates` (`report_template.create/update`); form `is_default` หนึ่งตัวต่อ group เท่านั้น |
| BU-scope template | แก้ `allow_business_unit` / `deny_business_unit` ของ template | Null allow-list = ทุก BU |
| ตั้งเวลา export เกิดซ้ำ | ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) | service scheduler แยกต่างหาก |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| หน้าจอ history ไม่แสดงอะไรเลยสำหรับ run ที่เพิ่งทำ | ตามที่คาดไว้ — ไม่มีเส้นทางที่เข้าถึงได้เขียน `tb_report_job` | ไม่ใช่ bug ในเส้นทางการอ่าน |
| Print คืน "no default template for this document type" | ไม่มีแถว `template_type = 'form'` ที่ยังมีชีวิตพร้อม `is_default = true` สำหรับ `report_group` นั้น และ BU ยังไม่ได้เลือก | Backstage admin ตั้ง default; หรือเลือก form ใน Default Setting |
| Print คืน "template is not a valid form for this type" | `template_id` ที่ส่งมาชี้ไปที่ template ของ `report_group` อื่นหรือ template แบบ `list` | แก้การเลือก print form ของ BU |
| ทุกการ print ล้มเหลวด้วย 401 จาก micro-report | `x-internal-token` (`INTERNAL_RPC_SECRET`) ขาดหรือไม่ตรงกันระหว่าง micro-business/gateway กับ micro-report | Ops: จัด secret ให้ตรงกัน (`bb7ea9e61`) |
| บล็อกลายเซ็นว่างบนงานพิมพ์ | template ไม่มีบล็อก `signature_config` สำหรับ slot นั้น หรือ stage ของ workflow resolve ผู้ลงนามไม่ได้ | เช็ค `signature_config.blocks` บน template และ stage ของ workflow ของเอกสาร |
| ข้อมูลรายงานล้มเหลวด้วย "view not found" | `source_type` / `source_name` drift | จัด template binding ให้ตรงกับ DB object |
| ตัวเลือกงวดว่างใน dialog ของรายงาน | lookup อ่าน `tb_inventory_period` (เปลี่ยนชื่อจาก `tb_period`, `cf4ea57`) — build เก่าของ micro-report ยัง query `tb_period` | deploy micro-report ≥ 2026-09-16 |
| Template ไม่เห็นใน BU | `allow_business_unit` exclude; หรือ `deny_business_unit` include; costing method ไม่อยู่ใน `calculation_methods`; หรือทั้ง `allow_run` และ export ปิด (`actionable=true` ซ่อนไว้) | แก้ BU scoping / สวิตช์ใน Backstage |
| Toast "action disabled" / "unavailable for this business unit" | 403 `REPORT_TEMPLATE_UNAVAILABLE` พร้อม `reason` (§ 1.5) | เช็คสวิตช์ของ template, รายการ BU และ costing method |
| Export คืน 400 `export_not_configured` | Template มี `allow_export` แต่ไม่มี `export_xml` หรือ XML parse ไม่ได้ | เพิ่ม/แก้ Export XML ใน Backstage |

## 4. กรณีพิเศษ

- **การรัน on-demand และ Print เป็นการ render แบบ synchronous ผ่าน viewer ไม่ใช่ job แบบ queue** ไม่มีแถว `tb_report_job`, ไม่มี entry ใน history, ไม่มี retention `expires_at` ใด ๆ ใช้กับทั้งสอง
- **default หนึ่งตัวต่อ group ตอนนี้เป็น invariant ของ DB** (partial unique index) ไม่ใช่การเช็คในแอป — migration 2026-07-23 จะล้มเหลวอย่างชัดเจนถ้ามี mapping ที่ active สองตัวสำหรับประเภทเอกสารเดียว
- **connection ของ tenant ประกอบจากสองตาราง Backstage** micro-report resolve `tb_business_unit.db_schema` + `tb_database_pool` (`host`, `port`, `database`, `username`, `password` เป็น ciphertext `enc:v1`) ผ่าน LEFT JOIN (`micro-report/db/db.go` `resolveTenantDBURL`, Backstage migration `20260813010000_database_pool_drop_db_connection`); BU ที่ไม่มี pool หรือ schema คือ `ErrTenantNotProvisioned` (ข้ามได้) และ pool password แบบ plaintext เป็น hard error
- **รูปลายเซ็นไม่เดินทางเป็นข้อมูล** ถูกฝังลงใน template XML ต่อการ render; คำบรรยายเป็นคอลัมน์ string ธรรมดา
- **Lifecycle ของ job แบบ async มีอยู่จริงแต่ไม่ถูกใช้งาน** `queued → processing → (completed | failed | cancelled)` ยังเป็นสัญญาของโมเดล; มีเพียง `generate-async` ที่เดินหน้ามัน และไม่มีอะไรใน frontend เรียกใช้เลย

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: **ผสม** — tenant สำหรับตาราง job/history, Backstage schema สำหรับ template Schedule **ไม่ใช่** ตาราง tenant — ดู [reporting-audit/schedule](/th/inventory/reporting-audit/schedule) §5

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

### 5.3 `tb_report_template` (Backstage)

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
| `export_xml` | text? | Export XML mapping สำหรับการ export CSV (§ 1.4); `NULL` = ไม่มี export Migration `20261019120000_report_template_export_xml` |
| `allow_run`, `allow_export` | bool (ค่าเริ่มต้น `true` / `false`) | สวิตช์ปุ่ม Run และ Export data Migration `20261019180000_report_template_allow_run_export` |
| `calculation_methods` | enum array | Costing method ที่ template รองรับ; ว่าง = ทั้งหมด Migration `20261008130000_report_template_calculation_methods` |
| `allow_business_unit` / `deny_business_unit` | JSONB? | BU scoping; allow เป็น null = ทุก BU |
| `is_active`, `doc_version`, คอลัมน์ audit | — | มาตรฐาน |

form ที่ seed ไว้ที่ HEAD รวมเอกสารแนวตั้ง + แนวนอนสำหรับ CN, GRN, IA, Invoice, PC, PO, PR, RFQ/RFP, SC, SI, SO, SR และ form Vendor Detail กับ Product Category รายงานแบบรายการที่ seed (`db/seed/report-templates/*.content.xml`): Inventory Balance, Stock Card Detailed, Monthly Inventory Movement, Slow Moving, Receiving Detail, Receiving Detail Summary by Product, Receiving List, Purchase Analysis by Item, Purchase Request Detail / List, Purchase Order Detail / List, Credit Note Detail, Stock In / Stock Out Detail, Store Requisition Detail, Deviation by Item, Material Consumption, Menu Engineering, Recipe Card, EOP Checklist / Adjustment, Landed Cost (เดิมคือ Extra Cost Report, `8196f53`), Product List, Vendor List การเปลี่ยนพฤติกรรมที่สำคัญ: Stock Card บน BU แบบ `average` แสดง `-` ใน Lot# และใส่ `*` ที่ Avg Cost จนกว่างวดจะปิด และ AVG Grand Total เป็นผลรวมของ Total Amount ของแต่ละกลุ่ม (`54d7e6c`, `f2c3db1`); seed ของ Stock Card ส่ง `@calculation_method` ของ BU เข้าฟังก์ชัน (`bffff67`); Monthly Inventory Movement แสดง Lot# บน BU แบบ FIFO และมีคอลัมน์ Diff Amount; Store Requisition Detail มีพารามิเตอร์ Movement Type (Issue/Transfer); ช่วงวันที่ของรายงานเทียบทั้งวันตามปฏิทิน Asia/Bangkok (`75b5fcd`); struct `ReportFilters` เพิ่ม `OrderBy`/`Sort`, `MovementType`, `DeliveryDateFrom/To`

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

`templateId` คือตัวเลือกของ BU จากหน้าจอ Default Setting (ส่งเป็น `?template_id=` โดย `printDocument()`); `is_default` ของ form ใน group เป็น fallback

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

- **Prisma tenant:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job`, `enum_report_job_status`, `enum_report_format`, `enum_report_category`; `tb_report_schedule` (ตายแล้ว)
- **Prisma Backstage:** `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `tb_report_template`; migration `20260429110000_add_print_template_mapping` (สร้างตาราง mapping), `20260723120000_print_form_default` (ย้าย default ไปบน template และลบมันทิ้ง), `20260813010000_database_pool_drop_db_connection`
- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/application/reports/reports.controller.ts` (`POST generate`, `GET types`, `GET templates`, `GET templates/:id`, `POST viewer`, `POST data`, `GET lookups`, `POST generate-async`, `GET jobs/:job_id`, `GET history`, schedules), `src/backstage/backstage_report-templates/backstage_report-templates.controller.ts` (`GET forms`, CRUD, `GET db-objects`), route `print-viewer` ของ controller ต่อเอกสาร
- **micro-business:** `../carmen-turborepo-backend/apps/micro-business/src/common/print-report.helper.ts` (การ resolve template, payload, ลายเซ็น, การเรียก viewer + PDF), `procurement/purchase-order/purchase-order.service.ts` (`printToReport`, อีเมล + `email_sent`)
- **micro-report:** `../micro-report/controller/report_controller.go` (`viewReport`, `viewReportWithData`, `exportPdfWithData`, `reportData`, `lookups`, `dbObjects`, `dialogParams`, `generateAsync`, `jobStatus`, `history`; SQL `tb_inventory_period`), `controller/template_controller.go` (`listFlat`), `service/render/viewer_client.go` (`View`, `ExportPDF`), `service/report_service.go` (`ExportReportWithExternalData`), `service/dataset/client.go` (`/api/datasets/execute`), `db/db.go` (`resolveTenantDBURL`), `middleware/internal_auth.go`, `pkg/notify/client.go`, `db/seed/report-templates/` (+ `_metadata.json`)
- **Frontend:** `../carmen-frontend/routes/report/` (`list/`, `schedules/`, `history/`, `shared/use-report.ts`), `lib/print-document.ts` (`DEDICATED_PRINT_ENDPOINTS`), `routes/system-admin/default-setting/use-report-form-templates.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/documents-and-reports/report/*`, `platform/report-templates/GET-find-forms-…bru`, `platform/report-template/*`, `*/GET-print-to-report-*.bru`; ที่ archive แล้ว `_archived/2026-07-29/platform/print-template-mapping/*` และ `_archived/2026-07-29/documents-and-reports/report/GET-resolve-print-template-…bru`
