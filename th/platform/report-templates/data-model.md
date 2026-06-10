---
title: Report Templates — แบบจำลองข้อมูล (Data Model)
description: เอนทิตี tb_report_template, payload XML ของ dialog/content, การผูก source และขอบเขต BU
published: true
date: 2026-06-10T17:00:00.000Z
tags: book/platform, report-templates, data-model
editor: markdown
dateCreated: 2026-06-10T17:00:00.000Z
---

# Report Templates — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_report_template` (หลัก) &nbsp;·&nbsp; **ตารางพี่น้อง:** `tb_print_template_mapping` — document ไว้ใน [Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; **Payload JSON:** `dialog` (XML, non-nullable), `content` (XML, non-nullable), `source_params` (`{ params: [...] }`), `signature_config` (`{ blocks: [...] }`) &nbsp;·&nbsp; **การผูก source:** `source_type` (String ธรรมดา: `view` / `function` / `procedure`) + `source_name` + `source_params` &nbsp;·&nbsp; **ขอบเขต BU:** `allow_business_unit` / `deny_business_unit` เก็บเป็น `Json?`; serialise เป็น string แบบ CSV ในฟอร์มของ SPA &nbsp;·&nbsp; **Flag วงจรชีวิต:** `is_standard`, `is_active`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

`tb_report_template` คือรายการใน catalogue สำหรับเอกสารที่พิมพ์หรือส่งออกได้หนึ่งรายการใน Carmen Platform แต่ละ row encode นิยามที่สมบูรณ์ของรายงานหนึ่งฉบับ: identity ของมัน (`name`, `report_group`, `kind`), คอลัมน์ payload XML สองคอลัมน์ (`dialog` และ `content`) ที่ report runtime นำไปใช้, การผูก source ตอน runtime (`source_type`, `source_name`, `source_params`), คู่ allow/deny สำหรับขอบเขต BU และ flag วงจรชีวิตมาตรฐานพร้อม audit trio

เทมเพลตรายงานเป็น tenant-global — ไม่ scope ต่อ cluster และไม่มี FK ไป `tb_cluster` คอลัมน์ขอบเขต BU (`allow_business_unit`, `deny_business_unit`) เป็นรายการกรองแบบ opt-in ที่จำกัดว่า business unit ใดมองเห็นเทมเพลตได้; มันไม่ได้ผูก row เข้ากับ cluster ใดเป็นการเฉพาะ จุดนี้ทำให้ surface ของ report-templates ต่างจากหน้า [clusters](/th/platform/clusters) และ [business-units](/th/platform/business-units) ซึ่ง document ลำดับชั้น cluster/BU ไว้ BU code ที่อ้างอิงใน chip list ตรงกับค่า `tb_business_unit.code` แต่ไม่มี FK constraint — การอ้างอิงเป็น convention ระดับ application

คอลัมน์ `kind` แยกการใช้งานสองแบบของตารางนี้ออกจากกัน: row แบบ `"report"` คือรายงานเชิงวิเคราะห์ที่ผู้ใช้มองเห็น; row แบบ `"print"` คือ layout เอกสารพิมพ์ที่ `tb_print_template_mapping` นำไปใช้ ตาราง join พี่น้องนั้น (Prisma model `tb_print_template_mapping`) map document type (PO, GRN, SR, …) เข้ากับ row ของ `tb_report_template`; ตอนนี้มันมี surface ใน SPA ของตัวเองและ document ไว้ในโมดูล [Print Template Mapping](/th/platform/print-template-mapping) ([Data Model](/th/platform/print-template-mapping/data-model)) — หน้านี้ครอบคลุมเฉพาะ `tb_report_template`

## 2. เอนทิตี

### 2.1 `tb_report_template`

หนึ่ง row ต่อหนึ่งเทมเพลตรายงานหรือเทมเพลตพิมพ์ ตารางฟิลด์ด้านล่างเรียงตามลำดับการประกาศใน Prisma จัดกลุ่มตามวัตถุประสงค์ ตารางนี้มีฟิลด์มากกว่า 15 ฟิลด์ จึงใช้ row คั่นตัวหนาเพื่อจัดกลุ่มคอลัมน์ที่เกี่ยวข้องกัน

| Field | Prisma Type | Nullable | Default | คำอธิบาย |
| ----- | ----------- | -------- | ------- | ----------- |
| **— Identity —** | | | | |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `name` | `String @db.VarChar(255)` | No | — | ชื่อเทมเพลตที่อ่านเข้าใจได้; unique ในหมู่ live row (ร่วมกับ `deleted_at`) |
| `description` | `String?` | Yes | — | คำอธิบาย free-text แบบ optional ของวัตถุประสงค์ของเทมเพลต |
| `report_group` | `String @db.VarChar(100)` | No | — | key สำหรับจัดกลุ่ม ใช้จัดระเบียบเทมเพลตในหน้า list ของการจัดการ (เช่น `"Receiving"`, `"Inventory"`) |
| `kind` | `String @default("report") @db.Text` | No | `"report"` | หมวดของเทมเพลต: `"report"` (รายงานเชิงวิเคราะห์ที่ผู้ใช้มองเห็น) หรือ `"print"` (layout เอกสารที่ `tb_print_template_mapping` นำไปใช้) |
| **— XML Payloads —** | | | | |
| `dialog` | `String @db.Text` | No | — | string XML ที่นิยามฟอร์ม parameter ซึ่ง report runtime render ไม่เป็น nullable — string ว่าง `""` คือค่า "ไม่มี dialog" ที่ valid โครงสร้าง XML โดยละเอียด document ไว้ใน [XML Spec §2](./xml-spec.md) |
| `content` | `String @db.Text` | No | — | string XML ที่นิยาม layout ผลลัพธ์ของรายงานซึ่ง report runtime render ไม่เป็น nullable — `""` valid สำหรับเทมเพลตที่สร้างใหม่ แท็บ Content ใน editor ยังรับการอัพโหลดไฟล์ `.frx` / `.xml` / `.txt` ด้วย (การ migrate ไฟล์ FastReport รุ่นเก่า) โครงสร้างโดยละเอียดอยู่ใน [XML Spec §3](./xml-spec.md) |
| **— Go Builder —** | | | | |
| `builder_key` | `String? @db.VarChar` | Yes | — | ผูก row ของเทมเพลตเข้ากับ key ใน registry ของ Go report.Definition เมื่อถูกตั้งค่า runtime ฝั่ง Go ใช้ key นี้ resolve นิยามรายงานแทนการ execute `source_type`/`source_name` โดยตรง |
| **— Source Binding (legacy) —** | | | | |
| `view_name` | `String? @db.VarChar` | Yes | — | คอลัมน์ legacy ที่คงไว้เพื่อ backward compatibility ให้ใช้ `source_type` + `source_name` แทน registry ฝั่ง Go fallback ไปใช้ `view_name` เมื่อ `source_name` ว่าง SPA โหลด `source_name` เป็น `template.source_name \|\| template.view_name` |
| **— Source Binding —** | | | | |
| `source_type` | `String @db.VarChar(20)` | No | `"view"` | บอก report executor ว่าจะอ่านข้อมูลอย่างไร เป็น String ธรรมดา — ไม่ใช่ Prisma enum; SPA validate ค่าที่ฝั่ง client ค่าที่ valid: `"view"`, `"function"`, `"procedure"` (ดู §4) |
| `source_name` | `String? @db.VarChar` | Yes | — | identifier เปล่าของ view, function หรือ procedure (ไม่มี schema prefix; resolve เทียบกับ `current_schema()` ของ tenant) จำเป็นเมื่อ `source_type` เป็น `"function"` หรือ `"procedure"` — SPA บังคับใช้ด้วย validation error ระดับฟิลด์ |
| `source_params` | `Json @db.JsonB` | No | `{"params":[]}` | การ map argument แบบ positional สำหรับการเรียก function/procedure Shape: `{ "params": [{ "filter": "DateFrom", "type": "date", "nullable": false }, ...] }` ค่า default คือ params array ว่าง; ดู §5.3 |
| **— Print Layout —** | | | | |
| `orientation` | `String @db.VarChar(20)` | No | `"portrait"` | การวางแนวหน้ากระดาษสำหรับเทมเพลตแบบ print: `"portrait"` หรือ `"landscape"` แทนที่ convention เดิมที่ใช้ suffix ของชื่อแบบ `"Document Landscape"` |
| `signature_config` | `Json @db.JsonB` | No | `{"blocks":[]}` | นิยาม block ลายเซ็นที่ render บน layout การพิมพ์ Shape: `{ "blocks": [{ "key": "Sig1Name", "label": "Requestor", "required": true }, ...] }` แทนที่พฤติกรรมเดิมที่ดึง `Sig1Name`…`Sig5Name` จาก workflow stage ที่ active |
| **— Lifecycle —** | | | | |
| `is_standard` | `Boolean` | No | `true` | ทำเครื่องหมายว่าเทมเพลตเป็นเทมเพลตมาตรฐาน (system-provided) โดยปกติเทมเพลตมาตรฐานเป็น read-only สำหรับ operator ปลายทาง |
| **— BU Scope —** | | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | — | รายการ optional ของ BU code ที่มองเห็นเทมเพลตนี้ได้ `NULL` = มองเห็นได้ทุก BU SPA อ่านค่านี้เป็น array (หรือ scalar) แล้ว normalise เป็น string คั่นด้วย comma สำหรับฟิลด์ chip-input ผ่าน `toCsv()` |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | — | รายการ optional ของ BU code ที่ถูกตัดออกจากการมองเห็นเทมเพลตนี้อย่างชัดเจน `NULL` = ไม่มีการ deny การ normalise ด้วย `toCsv()` แบบเดียวกับ `allow_business_unit` |
| `is_active` | `Boolean` | No | `true` | เมื่อเป็น `false` เทมเพลต inactive และถูกซ่อนจาก list การเลือก |
| **— Audit —** | | | | |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: เวลาสร้าง row |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK ไป `tb_user.id` ของผู้สร้าง (convention ระดับ application; ไม่มี Prisma `@relation` ประกาศไว้) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: เวลาอัพเดทล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK ไป `tb_user.id` ของผู้อัพเดทล่าสุด (convention ระดับ application; ไม่มี Prisma `@relation` ประกาศไว้) |
| **— Soft-delete —** | | | | |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Timestamp ของ soft-delete; `NULL` = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK ไป `tb_user.id` ของผู้ลบ (convention ระดับ application; ไม่มี Prisma `@relation` ประกาศไว้) |

**Constraint:**
- `@id` บน `id`
- `@@unique([name, deleted_at])` — map `"report_template_name_deleted_at_u"` — ชื่อเทมเพลต unique ในหมู่ live row; อนุญาตให้ใช้ชื่อซ้ำได้หลัง soft delete

**Index:**
- `@@index([report_group])` — map `"idx_report_template_report_group"` — รองรับการ list เทมเพลตแบบกรองหรือเรียงตามกลุ่ม

## 3. ความสัมพันธ์

```
tb_report_template  self-FK  created_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  updated_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  deleted_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  1 ─── M  tb_print_template_mapping      (via tb_print_template_mapping.report_template_id; see Print Template Mapping module)
```

สิ่งที่จงใจไม่มี:

- **ไม่มี FK ไป `tb_cluster`** — เทมเพลตรายงานเป็น tenant-global ไม่ scope ต่อ cluster ไม่มีคอลัมน์ cluster บน `tb_report_template`
- **ไม่มี FK ไป `tb_business_unit`** — คอลัมน์ `allow_business_unit` และ `deny_business_unit` อ้างอิง BU code ด้วยค่า (convention ระดับ application) ไม่ใช่ด้วย FK constraint ที่ประกาศไว้ ฐานข้อมูลไม่บังคับ referential integrity ระหว่างคอลัมน์ JSON เหล่านี้กับ `tb_business_unit.code`
- **FK ของ audit เป็นระดับ application เท่านั้น** — `created_by_id`, `updated_by_id` และ `deleted_by_id` ถูกประกาศเป็น `String? @db.Uuid` ใน Prisma แต่ไม่มี directive `@relation` schema ไม่ประกาศ FK constraint สำหรับฟิลด์เหล่านี้ สอดคล้องกับ pattern ที่ใช้ทั่ว platform schema สำหรับ delete path

## 4. Enum

`source_type` ถูกประกาศเป็น `String @db.VarChar(20)` ใน Prisma — มัน**ไม่ใช่** Prisma named enum ฐานข้อมูลไม่บังคับชุดค่าที่อนุญาต SPA (`ReportTemplateEdit.tsx`) บังคับชุดค่าที่ valid ที่ชั้น client ผ่าน typed union: `"view" | "function" | "procedure"` ส่วน `reportTemplateService.ts` re-export union นี้เป็น `ReportSourceType`

| ค่า | ความหมาย |
| ----- | ------- |
| `"view"` | executor รัน `SELECT * FROM <source_name>` (default) ไม่ใช้ `source_params`; filter ถูก apply ผ่าน WHERE clause ตอน runtime |
| `"function"` | executor รัน `SELECT * FROM <source_name>($1, $2, …)` โดย function คืน TABLE หรือ SETOF argument เป็น positional, map โดย `source_params.params` ตามลำดับการประกาศ |
| `"procedure"` | executor รัน `CALL <source_name>($1, …, 'rs'::refcursor)` แล้ว fetch จาก cursor ชื่อ `rs` argument เป็น positional จาก `source_params.params`; refcursor ตัวท้ายเป็น convention ของ runtime ที่ไม่ถูกแทนไว้ใน `source_params` |

ในทำนองเดียวกัน `kind` และ `orientation` เป็นคอลัมน์ String ธรรมดา ค่าที่ valid ของมันถูกบังคับใช้ที่ชั้น application เท่านั้น:

- `kind`: `"report"` (default) หรือ `"print"`
- `orientation`: `"portrait"` (default) หรือ `"landscape"`

## 5. คอลัมน์ JSON

คอลัมน์สี่ตัวบน `tb_report_template` ถือ payload แบบมีโครงสร้างที่ฐานข้อมูล validate ภายในไม่ได้ — ชั้น application เป็นเจ้าของ contract เหล่านั้น สองตัว (`source_params`, `signature_config`) เป็นคอลัมน์ `Json @db.JsonB`; อีกสองตัว (`dialog`, `content`) เป็นคอลัมน์ `String @db.Text` ที่เก็บ string XML รายละเอียดต่อ subsection ด้านล่างครอบคลุม shape ของแต่ละคอลัมน์

### 5.1 `dialog` (payload XML)

คอลัมน์ `String @db.Text` แบบ non-nullable (ไม่ใช่ `Json`) ที่เก็บ XML ซึ่ง report runtime render เป็นฟอร์มกรอก parameter ที่แสดงให้ผู้ใช้ก่อนรันรายงาน string ว่าง `""` คือสถานะ "ไม่มี parameter" ที่ valid สำหรับเทมเพลตที่ไม่รับ input จากผู้ใช้

แท็บ Dialog ใน editor ของ SPA รับการกรอก XML อิสระหรือการอัพโหลดไฟล์ เอกสารอ้างอิง element และ attribute ของ XML โดยละเอียดอยู่ใน [XML Spec §2](./xml-spec.md)

### 5.2 `content` (payload XML)

คอลัมน์ `String @db.Text` แบบ non-nullable ที่เก็บ XML ซึ่งนิยาม layout ผลลัพธ์ของรายงาน — คอลัมน์, การจัดกลุ่ม, ยอดรวม, การจัดรูปแบบ ฯลฯ string ว่าง valid สำหรับเทมเพลตที่เพิ่งสร้างก่อนเพิ่ม content

แท็บ Content ใน editor รับการกรอก XML โดยตรงและยังอนุญาตให้อัพโหลดไฟล์ `.frx`, `.xml` หรือ `.txt` ซึ่งรองรับการ migrate ไฟล์เทมเพลต FastReport รุ่นเก่า โครงสร้าง XML โดยละเอียดอยู่ใน [XML Spec §3](./xml-spec.md)

### 5.3 `source_params` (object)

คอลัมน์ `Json @db.JsonB` แบบ non-nullable ที่มี default `{"params":[]}`

Shape:

```
{
  "params": [
    { "filter": "DateFrom",  "type": "date",  "nullable": false },
    { "filter": "DateTo",    "type": "date",  "nullable": false },
    { "filter": "BuCode",    "type": "text",  "nullable": true  }
  ]
}
```

แต่ละ element ใน `params` map ชื่อฟิลด์ filter ของ Dialog หนึ่งชื่อ (key `filter` เช่น `"DateFrom"`) ไปยังชนิด parameter ของ PostgreSQL (key `type` เช่น `"date"`, `"uuid"`, `"text"`) บวก flag boolean `nullable`

พฤติกรรมตาม `source_type`:

- **`"view"`** — `source_params` ถูกละเลยตอน runtime executor apply ค่า filter ผ่าน WHERE clause แทน argument แบบ positional ค่า `{ "params": [] }` ที่ว่าง (default) คือค่าที่ถูกต้อง
- **`"function"`** — array `params` เป็น positional argument ถูกส่งให้ function ตามลำดับที่ปรากฏใน array ให้ตรงกับรายการ parameter ที่ function ประกาศไว้
- **`"procedure"`** — การผูกแบบ positional เดียวกับ `"function"` procedure ถูกเรียกเพิ่มด้วย `INOUT refcursor` ตัวท้ายชื่อ `rs` (executor fetch ด้วย `FETCH ALL FROM "rs"` หลังการเรียก) cursor ตัวท้ายนี้เป็น convention ของ runtime และ**ไม่**ถูกแทนไว้ใน `source_params`

interface `SourceParamRow` ของ SPA (`ReportTemplateEdit.tsx` บรรทัด 30) สะท้อน shape ต่อ element:

```
interface SourceParamRow {
  filter:   string
  type:     string
  nullable: boolean
}
```

ตอน save SPA ประกอบ `{ params: cleanParams }` โดยที่ `cleanParams` คือ array ที่กรอง row ที่ว่างออกแล้ว

### 5.4 `signature_config` (object)

คอลัมน์ `Json @db.JsonB` แบบ non-nullable ที่มี default `{"blocks":[]}`

Shape:

```
{
  "blocks": [
    { "key": "Sig1Name", "label": "Requestor",   "required": true  },
    { "key": "Sig2Name", "label": "Department",  "required": true  },
    { "key": "Sig3Name", "label": "Approver",    "required": false }
  ]
}
```

แต่ละ block นิยามเส้นลายเซ็นหนึ่งเส้นบนเอกสารที่พิมพ์ ฟิลด์ `key` ตรงกับ naming convention แบบ `Sig1Name`…`Sig5Name` รุ่นเก่าที่เคยใช้ในการ lookup ลายเซ็นจาก workflow stage; `label` คือชื่อบทบาทที่อ่านเข้าใจได้ซึ่งพิมพ์เหนือเส้นลายเซ็น สิ่งนี้แทนที่พฤติกรรมเดิมที่ดึงชื่อลายเซ็นจากนิยาม workflow stage ที่ active ณ เวลาพิมพ์

`signature_config` ไม่ปรากฏใน interface `ReportTemplateFormData` ปัจจุบันของ SPA — มันถูกจัดการแยกจากฟอร์ม edit หลัก

## 6. ความแตกต่างจาก shape ของ carmen-platform SPA

interface `ReportTemplate` ใน `../carmen-platform/src/services/reportTemplateService.ts` (บรรทัด 17–37) และ interface `ReportTemplateFormData` ใน `../carmen-platform/src/pages/ReportTemplateEdit.tsx` (บรรทัด 36–50) ถูกเทียบกับ Prisma model `tb_report_template` ที่น่าสังเกตคือ TS interface `ReportTemplate` อยู่ใน `src/services/reportTemplateService.ts` (บรรทัด 17) ไม่ใช่ `src/types/index.ts` ที่ interface ของโมดูล Platform ตัวอื่น (`Cluster`, `BusinessUnit`, `User`) อยู่ — นักพัฒนาที่ค้นหา TS shape ฉบับ canonical ควรดูในไฟล์ service

| # | รายการ | Prisma มี | SPA คาดหวัง | หมายเหตุ |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `kind` | `String @default("report") @db.Text` | `kind: 'report' \| 'print'` บน service interface `ReportTemplate` | มีอยู่ใน type ของ service แต่ไม่มีใน `ReportTemplateFormData` — ฟอร์ม edit ของ SPA ไม่เปิดเผยฟิลด์ `kind` สันนิษฐานว่าเทมเพลตถูกกำหนด `kind` ฝั่ง server หรือตอนสร้าง |
| 2 | `orientation` | `String @db.VarChar(20)` | ไม่มีทั้งใน `ReportTemplate` และ `ReportTemplateFormData` | คอลัมน์ Prisma ใหม่ที่ยังไม่ปรากฏใน SPA default เป็น `"portrait"` ที่ระดับฐานข้อมูล |
| 3 | `signature_config` | `Json @db.JsonB` | ไม่มีทั้งใน `ReportTemplate` และ `ReportTemplateFormData` | ยังไม่ปรากฏในฟอร์ม edit ของ SPA |
| 4 | `view_name` | `String? @db.VarChar` | ไม่อยู่ใน service interface `ReportTemplate` | คอลัมน์ legacy; ถูกเข้าถึงโดยนัยเฉพาะใน load path ของฟอร์ม Edit (`template.source_name \|\| template.view_name`) ในฐานะ fallback |
| 5 | `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | `unknown` บน service interface `ReportTemplate`; `string` ใน `ReportTemplateFormData` | ฟอร์ม Edit normalise ค่า JSON (array หรือ scalar) เป็น string คั่นด้วย comma ผ่าน `toCsv()` สำหรับฟิลด์ chip-input service interface type ฟิลด์เหล่านี้เป็น `unknown` เพื่อรองรับทั้ง JSON ดิบจาก API และค่าฟอร์มที่ serialise แล้ว |
| 6 | `created_by_id` / `updated_by_id` | `String? @db.Uuid` (id ดิบ) | `created_by_id?: string` / `updated_by_id?: string` บน `ReportTemplate` | id ดิบมีอยู่ใน service interface SPA ยังอ่าน `created_by_name` / `updated_by_name` จาก API response ด้วย (backend resolve ให้) แต่ค่าเหล่านี้ถูกถือใน state variable `MetadataFields` ที่แยกออกมา ไม่อยู่ใน type `ReportTemplate` |
| 7 | `source_params` | `Json @db.JsonB` (non-nullable) | `source_params?: ReportSourceParams` (optional) บน service interface | service interface ทำเครื่องหมาย optional เพื่อรองรับ API response บางส่วน; default ของ Prisma รับประกันว่าคอลัมน์ใน DB มีค่าเสมอ |

ฟิลด์ identity หลักทั้งหมด (`id`, `name`, `description`, `report_group`), ฟิลด์ payload XML (`dialog`, `content`), ฟิลด์การผูก source (`source_type`, `source_name`), flag วงจรชีวิต (`is_standard`, `is_active`) และ timestamp ของ audit (`created_at`, `updated_at`) สอดคล้องกันระหว่าง Prisma กับ shape ของ SPA ความแตกต่างส่วนใหญ่เป็นคอลัมน์ Prisma ใหม่ที่ยังไม่ปรากฏในฟอร์ม edit (รายการ 2–4) หรือ type coercion ที่ชั้นฟอร์มสำหรับคอลัมน์ JSON (รายการ 5, 7)

## 7. แหล่งข้อมูลอ้างอิง

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `model tb_report_template` (บรรทัด 701); `model tb_print_template_mapping` (บรรทัด 776)

**รอง (shape ฝั่ง consumer):**
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — interface `ReportTemplateFormData` (บรรทัด 36–50); interface `SourceParamRow` (บรรทัด 30–34); helper `toCsv` และ load path (บรรทัด 180–204); การประกอบ `source_params` ใน save path (บรรทัด 278–285)
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` — view list ของเทมเพลตรายงาน
- `../carmen-platform/src/services/reportTemplateService.ts` — interface `ReportTemplate` (บรรทัด 17–37); type `ReportSourceType`, `ReportSourceParam`, `ReportSourceParams` (บรรทัด 5–15)
- `../carmen-platform/src/types/index.ts` — ไม่มี type `ReportTemplate` นิยามไว้ที่นี่; type อยู่ในไฟล์ service

**Cross-link:**
- [report-templates](/th/platform/report-templates) — หน้า landing ของโมดูล
- [print-template-mapping](/th/platform/print-template-mapping) — โมดูลที่เป็นเจ้าของ `tb_print_template_mapping` ตาราง join ที่นำ row `kind="print"` ของตารางนี้ไปใช้ต่อ document type
- [business-units](/th/platform/business-units) — BU code ที่อ้างอิงใน chip list ของ allow/deny ตรงกับ `tb_business_unit.code`
- [clusters](/th/platform/clusters) — surface พี่น้องของ Platform; เทมเพลตรายงานเป็น tenant-global และไม่ scope ต่อ cluster
- [Permissions](./permissions.md) — การควบคุมการเข้าถึงของ surface การจัดการ report-templates
- [UI Screens](./ui-screens.md) — หน้าจอ SPA สำหรับการจัดการและแก้ไขเทมเพลตรายงาน
- [XML Spec](./xml-spec.md) — โครงสร้างโดยละเอียดของ payload XML `dialog` และ `content`
