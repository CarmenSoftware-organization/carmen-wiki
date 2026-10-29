---
title: Report Templates — แบบจำลองข้อมูล (Data Model)
description: tb_report_template และ tb_report_template_version — XML ของ dialog/content/export ชื่อ EN/TH การผูก source ขอบเขต BU และวิธีคิดต้นทุน สวิตช์ run/export template_type is_default และ doc_version
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, report-templates, data-model
editor: markdown
dateCreated: 2026-06-10T17:00:00.000Z
---

# Report Templates — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_report_template` (หลัก) และ `tb_report_template_version` (snapshot ต่อการเขียน, §2.2) &nbsp;·&nbsp; **ตารางพี่น้องเดิม:** `tb_print_template_mapping` — **ถูก drop เมื่อ 2026-07-23** (migration `20260723120000_print_form_default`) บทบาท `is_default` ของมันถูกดูดซับมาที่ตารางนี้แล้ว โมดูล print-template-mapping ที่เคยเป็นเจ้าของตารางนี้ถูกลบออกจากผลิตภัณฑ์เมื่อ 2026-07-24 (carmen-backstage commit `de11377`; ดู §7 Cross-link) &nbsp;·&nbsp; **Payload JSON/XML:** `dialog` (XML, non-nullable), `content` (XML, non-nullable), `export_xml` (XML, nullable), `name_i18n` / `description_i18n` (`{en?, th?}`), `source_params` (`{ params: [...] }`), `signature_config` (`{ blocks: [...] }`) &nbsp;·&nbsp; **การผูก source:** `source_type` (String ธรรมดา: `view` / `function` / `procedure`) + `source_name` + `source_params` &nbsp;·&nbsp; **ขอบเขต BU:** `allow_business_unit` / `deny_business_unit` เก็บเป็น `Json?`; serialise เป็น string แบบ CSV ในฟอร์มของ SPA &nbsp;·&nbsp; **ขอบเขตต้นทุน:** `calculation_methods` (`enum_calculation_method[]`, ว่าง = ทุกวิธี) &nbsp;·&nbsp; **Flag วงจรชีวิต:** `is_standard`, `is_default` (เฉพาะ form template ใหม่เมื่อ 2026-07-23), `is_active`, `allow_run`, `allow_export`, `doc_version`

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

`tb_report_template` คือรายการใน catalogue สำหรับเอกสารที่พิมพ์หรือส่งออกได้หนึ่งรายการใน Carmen Blue แต่ละ row encode นิยามที่สมบูรณ์ของรายงานหนึ่งฉบับ: identity ของมัน (`name`, `report_group`, `template_type`), คอลัมน์ payload XML สองคอลัมน์ (`dialog` และ `content`) ที่ report runtime นำไปใช้, การผูก source ตอน runtime (`source_type`, `source_name`, `source_params`), ฟิลด์ print-layout (`orientation`, `signature_config`), คู่ allow/deny สำหรับขอบเขต BU และ flag วงจรชีวิตมาตรฐานพร้อม audit trio (รวมถึง `doc_version` คอลัมน์ optimistic-lock ทั้งแพลตฟอร์มที่เพิ่มเมื่อ 2026-06-12 — **แก้ไขแล้ว** sync ครั้งก่อนระบุวันที่ผิดเป็น 2026-07-16)

เทมเพลตรายงานเป็น tenant-global — ไม่ scope ต่อ cluster และไม่มี FK ไป `tb_cluster` คอลัมน์ขอบเขต BU (`allow_business_unit`, `deny_business_unit`) เป็นรายการกรองแบบ opt-in ที่จำกัดว่า business unit ใดมองเห็นเทมเพลตได้; มันไม่ได้ผูก row เข้ากับ cluster ใดเป็นการเฉพาะ จุดนี้ทำให้ surface ของ report-templates ต่างจากหน้า [clusters](/th/backstage/clusters) และ [business-units](/th/backstage/business-units) ซึ่ง document ลำดับชั้น cluster/BU ไว้ BU code ที่อ้างอิงใน chip list ตรงกับค่า `tb_business_unit.code` แต่ไม่มี FK constraint — การอ้างอิงเป็น convention ระดับ application

ตารางนี้ยังเติบโตในรอบ 2026-08 ถึง 2026-10: ชื่อ EN/TH (`name_i18n`, `description_i18n`), คอลัมน์ Export XML, สวิตช์ run/export, ขอบเขตวิธีคิดต้นทุน และตารางพี่น้อง `tb_report_template_version` ที่บันทึกทุกการเขียน (§2.2) คอลัมน์ `template_type` (เปลี่ยนชื่อจาก `kind` โดย migration `20260723120000_print_form_default`, 2026-07-23) แยกการใช้งานสองแบบของตารางนี้ออกจากกัน: row แบบ `"list"` (เดิม `"report"`) คือรายงานเชิงวิเคราะห์แบบตารางที่ผู้ใช้มองเห็น; row แบบ `"form"` (เดิม `"print"`) คือ layout เอกสารเดี่ยว จนถึง 2026-07-23 ตาราง `tb_print_template_mapping` แยกต่างหากเคย map document type (PO, GRN, SR, …) เข้ากับ row แบบ `kind="print"` ที่นี่; ตอนนี้ตารางนั้น **ถูก drop แล้ว** หน้าที่ของมัน — การเลือก template default หนึ่งตัวที่ business unit จะได้สำหรับกลุ่มหนึ่ง ๆ — ตอนนี้ทำโดยคอลัมน์ `is_default` ของตารางนี้เอง กำหนดขอบเขตด้วย `report_group` และบังคับด้วย partial unique index (§2.1) โมดูล print-template-mapping ที่เคยเป็นเจ้าของตารางนี้ถูกลบออกจากผลิตภัณฑ์เมื่อ 2026-07-24 เช่นกัน (carmen-backstage commit `de11377`) — ดู §7 Cross-link สำหรับ timeline การถูกลบฉบับเต็ม หน้านี้ครอบคลุมเฉพาะ `tb_report_template`

## 2. เอนทิตี

### 2.1 `tb_report_template`

หนึ่ง row ต่อหนึ่งเทมเพลตรายงานหรือเทมเพลตพิมพ์ ตารางฟิลด์ด้านล่างเรียงตามลำดับการประกาศใน Prisma จัดกลุ่มตามวัตถุประสงค์ ตารางนี้มีฟิลด์มากกว่า 15 ฟิลด์ จึงใช้ row คั่นตัวหนาเพื่อจัดกลุ่มคอลัมน์ที่เกี่ยวข้องกัน

| Field | Prisma Type | Nullable | Default | คำอธิบาย |
| ----- | ----------- | -------- | ------- | ----------- |
| **— Identity —** | | | | |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `name` | `String @db.VarChar(255)` | No | — | ชื่อเทมเพลตที่อ่านเข้าใจได้; unique ในหมู่ live row (ร่วมกับ `deleted_at`) |
| `description` | `String?` | Yes | — | คำอธิบาย free-text แบบ optional ของวัตถุประสงค์ของเทมเพลต |
| `name_i18n` | `Json? @db.JsonB` | Yes | — | ชื่อที่แปลแล้ว `{ en?, th? }` `name` ยังเป็น unique key และถูกเขียนคู่ให้เท่ากับ `name_i18n.en`; service ปฏิเสธชื่อว่างตอน create และ update และ SPA ส่งทั้งสองทุกครั้งที่บันทึก |
| `description_i18n` | `Json? @db.JsonB` | Yes | — | คำอธิบายที่แปลแล้ว `{ en?, th? }`; `description` ยังเป็นค่า EN ที่เป็นบันทึกหลัก |
| `report_group` | `String @db.VarChar(100)` | No | — | key สำหรับจัดกลุ่ม ใช้จัดระเบียบเทมเพลตในหน้า list ของการจัดการ (เช่น `"Receiving"`, `"Inventory"`) |
| `template_type` | `String @default("list") @db.Text` | No | `"list"` | หมวดของเทมเพลต: `"list"` (รายงานเชิงวิเคราะห์แบบตาราง เดิม `"report"`) หรือ `"form"` (layout เอกสารเดี่ยว เดิม `"print"`) เปลี่ยนชื่อจาก `kind` โดย migration `20260723120000_print_form_default` (2026-07-23); ค่าก็เปลี่ยนพร้อมกัน |
| **— XML Payloads —** | | | | |
| `dialog` | `String @db.Text` | No | — | string XML ที่นิยามฟอร์ม parameter ซึ่ง report runtime render ไม่เป็น nullable — string ว่าง `""` คือค่า "ไม่มี dialog" ที่ valid โครงสร้าง XML โดยละเอียด document ไว้ใน [XML Spec §2](/th/backstage/report-templates/xml-spec) |
| `content` | `String @db.Text` | No | — | string XML ที่นิยาม layout ผลลัพธ์ของรายงานซึ่ง report runtime render ไม่เป็น nullable — `""` valid สำหรับเทมเพลตที่สร้างใหม่ แท็บ Content ใน editor ยังรับการอัพโหลดไฟล์ `.frx` / `.xml` / `.txt` ด้วย (การ migrate ไฟล์ FastReport รุ่นเก่า) โครงสร้างโดยละเอียดอยู่ใน [XML Spec §3](/th/backstage/report-templates/xml-spec) |
| `export_xml` | `String? @db.Text` | Yes | — | เอกสาร `<Export>` ที่ map dataset ของรายงานเป็นคอลัมน์ CSV สำหรับ action "Export data" `NULL` = ไม่มีการ map export; service เก็บ string ว่าง/ช่องว่างล้วนเป็น `NULL` รูปแบบ: [XML Spec §4](/th/backstage/report-templates/xml-spec) |
| **— Go Builder —** | | | | |
| `builder_key` | `String @db.VarChar(100)` | No | `""` | **แก้ไขเมื่อ 2026-10-27 — ไม่เป็น nullable อีกต่อไป** (string ว่าง = ไม่ได้ผูก) ผูก row ของเทมเพลตเข้ากับ key ใน registry ของ Go report.Definition เมื่อถูกตั้งค่า runtime ฝั่ง Go ใช้ key นี้ resolve นิยามรายงานแทนการ execute `source_type`/`source_name` โดยตรง |
| **— Source Binding (legacy) —** | | | | |
| `view_name` | `String? @db.VarChar` | Yes | — | คอลัมน์ legacy ที่คงไว้เพื่อ backward compatibility ให้ใช้ `source_type` + `source_name` แทน registry ฝั่ง Go fallback ไปใช้ `view_name` เมื่อ `source_name` ว่าง SPA โหลด `source_name` เป็น `template.source_name \|\| template.view_name` |
| **— Source Binding —** | | | | |
| `source_type` | `String @db.VarChar(20)` | No | `"view"` | บอก report executor ว่าจะอ่านข้อมูลอย่างไร เป็น String ธรรมดา — ไม่ใช่ Prisma enum; SPA validate ค่าที่ฝั่ง client ค่าที่ valid: `"view"`, `"function"`, `"procedure"` (ดู §4) |
| `source_name` | `String? @db.VarChar` | Yes | — | identifier เปล่าของ view, function หรือ procedure (ไม่มี schema prefix; resolve เทียบกับ `current_schema()` ของ tenant) จำเป็นเมื่อ `source_type` เป็น `"function"` หรือ `"procedure"` — SPA บังคับใช้ด้วย validation error ระดับฟิลด์ |
| `source_params` | `Json @db.JsonB` | No | `{"params":[]}` | การ map argument แบบ positional สำหรับการเรียก function/procedure Shape: `{ "params": [{ "filter": "DateFrom", "type": "date", "nullable": false }, ...] }` ค่า default คือ params array ว่าง; ดู §5.3 |
| **— Print Layout —** | | | | |
| `orientation` | `String @db.VarChar(20)` | No | `"portrait"` | การวางแนวหน้ากระดาษสำหรับเทมเพลตแบบ print: `"portrait"` หรือ `"landscape"` แทนที่ convention เดิมที่ใช้ suffix ของชื่อแบบ `"Document Landscape"` |
| `signature_config` | `Json @db.JsonB` | No | `{"blocks":[]}` | นิยาม block ลายเซ็นที่ render บน layout การพิมพ์ Shape: `{ "blocks": [{ "key": "Sig1Name", "label": "Requestor", "required": true }, ...] }` แทนที่พฤติกรรมเดิมที่ดึง `Sig1Name`…`Sig5Name` จาก workflow stage ที่ active |
| **— Costing scope —** | | | | |
| `calculation_methods` | `enum_calculation_method[]` | No | `[]` | วิธีคิดต้นทุนที่เทมเพลตรองรับ: `average`, `fifo`, `average_per_location` ว่าง = รองรับทุกวิธี micro-report ปฏิเสธการรันสำหรับ business unit ที่วิธีของมันไม่อยู่ในรายการ (`calculation_method_unsupported`); form template ได้รับการยกเว้น SPA ล้างค่านี้สำหรับ `template_type = "form"` |
| **— Run / export switches —** | | | | |
| `allow_run` | `Boolean` | No | `true` | แสดงปุ่ม Run Report การรันแบบโต้ตอบของ `list` template ถูกปฏิเสธเมื่อเป็น `false` (micro-report `run_disabled`); schedule ไม่ได้รับผลกระทบ (ตรวจเฉพาะผู้เรียกจากเว็บ) ไม่ส่งสำหรับ form template |
| `allow_export` | `Boolean` | No | `false` | แสดงปุ่ม Export data; micro-report ปฏิเสธ endpoint export เมื่อเป็น `false` (`export_disabled`) `has_export` ในรายการเทมเพลตของ BU เป็น true เฉพาะเมื่อ `allow_export` เปิด **และ** `export_xml` ไม่ว่าง |
| **— Lifecycle —** | | | | |
| `is_standard` | `Boolean` | No | `true` | ทำเครื่องหมายว่าเทมเพลตเป็นเทมเพลตมาตรฐาน (system-provided) โดยปกติเทมเพลตมาตรฐานเป็น read-only สำหรับ operator ปลายทาง |
| `is_default` | `Boolean` | No | `false` | **ใหม่เมื่อ 2026-07-23** มีความหมายเฉพาะเมื่อ `template_type = "form"`: เทมเพลตตัวเดียวที่ live ต่อ `report_group` ที่ใช้เมื่อ business unit ยังไม่ได้เลือกเอง บังคับด้วย partial unique index ด้านล่าง ไม่ใช่แค่ logic ฝั่ง application — นี่คือคอลัมน์ที่ดูดซับ `tb_print_template_mapping.is_default` เมื่อตารางนั้นถูก drop |
| **— BU Scope —** | | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | — | รายการ optional ของ BU code ที่มองเห็นเทมเพลตนี้ได้ `NULL` หรือว่าง = มองเห็นได้ทุก BU **เก็บตามที่ได้รับ:** SPA ส่ง string คั่นด้วย comma (row ที่บันทึกจากหน้า Edit จึงเก็บเป็น JSON string) ขณะที่ seed และผู้เขียนผ่าน API อาจเก็บเป็น array; SPA อ่านได้ทั้งสองแบบ (array หรือ scalar) แล้ว normalise เป็น string CSV ผ่าน `toCsv()` และ `ParseBuList` ของ micro-report รับได้ทั้งสองรูป (เทียบแบบไม่สนตัวพิมพ์) ถูกละเว้นสำหรับ `form` template |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | — | รายการ optional ของ BU code ที่ถูกตัดออกจากการมองเห็นเทมเพลตนี้อย่างชัดเจน `NULL` = ไม่มีการ deny การ normalise ด้วย `toCsv()` แบบเดียวกับ `allow_business_unit` |
| `is_active` | `Boolean` | No | `true` | เมื่อเป็น `false` เทมเพลต inactive และถูกซ่อนจาก list การเลือก |
| **— Audit —** | | | | |
| `doc_version` | `Int @default(0) @db.Integer` | No | `0` | Token สำหรับ optimistic-lock ส่วนหนึ่งของการ rollout `doc_version` ทั้งแพลตฟอร์ม (**2026-06-12**, migration `20260612000000_add_doc_version`, 35 ตาราง — แก้จาก "2026-07-16" ของ sync ครั้งก่อน) SPA ส่งค่านี้ทุกครั้งที่ `PUT` และแสดง toast conflict + reload เมื่อไม่ตรงกัน |
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
- **ใหม่เมื่อ 2026-07-23:** partial unique index `idx_report_template_default_per_group` บน `(report_group)` `WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` — บังคับ "default form template ที่ live ได้ไม่เกินหนึ่งตัวต่อกลุ่ม" ระดับฐานข้อมูล index นี้เป็น SQL ล้วน (เพิ่มตรงใน migration ไม่สามารถแสดงใน Prisma schema DSL ได้) — `prisma migrate diff` จะมองไม่เห็นมัน ดังนั้นต้องระวังไม่ให้ migration ที่ generate อัตโนมัติในอนาคต drop มันทิ้ง

**Index:**
- `@@index([report_group])` — map `"idx_report_template_report_group"` — รองรับการ list เทมเพลตแบบกรองหรือเรียงตามกลุ่ม

### 2.2 `tb_report_template_version`

หนึ่ง snapshot ที่แก้ไม่ได้ต่อการเขียนหนึ่งครั้งของเทมเพลต เพิ่มในรอบ 2026-10 (carmen-turborepo-backend commit `0aba9ec75` ตาราง + snapshot ตอน create/update, `3468a5bc7` endpoint list/get/restore) เขียนใน transaction เดียวกับการเขียนนั้น (`writeVersion`, `report-template-version.ts`); การ delete **ไม่**เขียน version

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`) |
| `report_template_id` | `String @db.Uuid` | No | FK ไป `tb_report_template.id` |
| `version` | `Int` | No | `doc_version` ของเทมเพลต **หลัง**การเขียน; unique ต่อเทมเพลต (`report_template_version_template_version_u`) |
| `snapshot` | `Json @db.JsonB` | No | ฟิลด์ที่แก้ไขได้ (`SNAPSHOT_FIELDS`): `name`, `name_i18n`, `description`, `description_i18n`, `report_group`, `template_type`, `dialog`, `content`, `export_xml`, `allow_run`, `allow_export`, `builder_key`, `view_name`, `source_type`, `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `is_default`, `is_active`, `allow_business_unit`, `deny_business_unit`, `calculation_methods` |
| `change_type` | `String @db.VarChar(20)` | No | `create` \| `update` \| `restore` \| `import` (`import` ถูกตั้งเมื่อ payload มี `change_type: "import"` ซึ่ง dialog Import ของ SPA ส่งมา) |
| `restored_from_version` | `Int?` | Yes | เวอร์ชันต้นทางเมื่อ `change_type = "restore"` |
| `note` | `String?` | Yes | ข้อความอิสระ; ไม่มี code path ปัจจุบันใดเขียน |
| `created_at` / `created_by_id` | `DateTime` / `String? @db.Uuid` | No / Yes | เมื่อไรและโดยใคร |

Index: `(report_template_id, created_at DESC)` (`idx_report_template_version_template_created`) **Restore** (`POST .../versions/:version_no/restore`, body `{ doc_version }`) คัดลอก snapshot กลับไปที่ row ที่ live ภายใต้ optimistic lock ปกติ และเขียน version `restore` ใหม่; มันจงใจไม่แตะ `is_default` (partial unique index อนุญาตหนึ่ง default ต่อกลุ่ม) ตรวจ `source_name` ซ้ำกับ pattern ของ identifier และคง `calculation_methods` ปัจจุบันไว้เมื่อ snapshot เก่ากว่าฟิลด์นั้น version ที่ไม่มีอยู่ตอบ `REPORT_TEMPLATE_VERSION_NOT_FOUND` (`report-template.service.ts` `restoreVersion`)

เพราะ flow set-default บน [Form Groups](/th/backstage/report-form-groups) เป็น `PUT` บางส่วนสองครั้ง การสลับ default แต่ละครั้งจึงเขียน version `update` **สอง**รายการ (หนึ่งต่อเทมเพลตที่ได้รับผล)

การตรวจ `source_name` (ใหม่): service ปฏิเสธด้วย `COMMON_VALIDATION_FAILED` ทุก `source_name` ที่ไม่ใช่ identifier เปล่า (`^[A-Za-z_][A-Za-z0-9_]*$` ยาวไม่เกิน 63 ตัวอักษร) ตอน create, update และ restore เพราะ micro-report ใส่มันลงใน SQL โดยไม่ใส่ quote (`report-template-source-name.ts`, commit `bb2530c12`)

## 3. ความสัมพันธ์

```
tb_report_template  1 ─── M  tb_report_template_version  (report_template_id; Prisma @relation)
tb_report_template  self-FK  created_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  updated_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  deleted_by_id  → tb_user.id  (audit; no Prisma @relation)
```

**ถูกลบเมื่อ 2026-07-23:** `tb_report_template 1 ─── M tb_print_template_mapping` ไม่มีอยู่แล้ว — ตาราง mapping ถูก drop ไปเลย ไม่ใช่แค่ตัดการเชื่อมต่อ (migration `20260723120000_print_form_default`); โมดูล print-template-mapping เองถูกลบออกจากผลิตภัณฑ์วันถัดมาคือ 2026-07-24 (carmen-backstage commit `de11377`) — ดู §7 Cross-link

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

ในทำนองเดียวกัน `template_type` และ `orientation` เป็นคอลัมน์ String ธรรมดา ค่าที่ valid ของมันถูกบังคับใช้ที่ชั้น application เท่านั้น:

- `template_type`: `"list"` (default) หรือ `"form"` — เปลี่ยนชื่อจาก `kind` (`"report"`/`"print"`) โดย migration `20260723120000_print_form_default`
- `orientation`: `"portrait"` (default) หรือ `"landscape"`

## 5. คอลัมน์ JSON

คอลัมน์ห้าตัวบน `tb_report_template` ถือ payload แบบมีโครงสร้างที่ฐานข้อมูล validate ภายในไม่ได้ — ชั้น application เป็นเจ้าของ contract เหล่านั้น สองตัว (`source_params`, `signature_config`) เป็นคอลัมน์ `Json @db.JsonB`; อีกสามตัว (`dialog`, `content` และ `export_xml` แบบ optional) เป็นคอลัมน์ `String @db.Text` ที่เก็บ string XML (`export_xml` บันทึกไว้ที่ [XML Spec §4](/th/backstage/report-templates/xml-spec); `name_i18n` / `description_i18n` และรายการ BU ก็เป็น JsonB เช่นกัน แต่เรียบง่ายพอที่จะครอบคลุมใน §2.1) รายละเอียดต่อ subsection ด้านล่างครอบคลุม shape ของแต่ละคอลัมน์

### 5.1 `dialog` (payload XML)

คอลัมน์ `String @db.Text` แบบ non-nullable (ไม่ใช่ `Json`) ที่เก็บ XML ซึ่ง report runtime render เป็นฟอร์มกรอก parameter ที่แสดงให้ผู้ใช้ก่อนรันรายงาน string ว่าง `""` คือสถานะ "ไม่มี parameter" ที่ valid สำหรับเทมเพลตที่ไม่รับ input จากผู้ใช้

แท็บ Dialog ใน editor ของ SPA รับการกรอก XML อิสระหรือการอัพโหลดไฟล์ เอกสารอ้างอิง element และ attribute ของ XML โดยละเอียดอยู่ใน [XML Spec §2](/th/backstage/report-templates/xml-spec)

### 5.2 `content` (payload XML)

คอลัมน์ `String @db.Text` แบบ non-nullable ที่เก็บ XML ซึ่งนิยาม layout ผลลัพธ์ของรายงาน — คอลัมน์, การจัดกลุ่ม, ยอดรวม, การจัดรูปแบบ ฯลฯ string ว่าง valid สำหรับเทมเพลตที่เพิ่งสร้างก่อนเพิ่ม content

แท็บ Content ใน editor รับการกรอก XML โดยตรงและยังอนุญาตให้อัพโหลดไฟล์ `.frx`, `.xml` หรือ `.txt` ซึ่งรองรับการ migrate ไฟล์เทมเพลต FastReport รุ่นเก่า โครงสร้าง XML โดยละเอียดอยู่ใน [XML Spec §3](/th/backstage/report-templates/xml-spec)

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

`signature_config` ไม่ได้เป็นส่วนหนึ่งของ interface `ReportTemplateFormData` ของ SPA — ฟอร์ม edit ไม่มี control สำหรับมัน การบันทึกจากหน้า edit ปกติจึงไม่ส่งมัน (การ update ของ backend คง `signature_config` ที่ถูกละไว้ตามเดิม) มันเดินทางผ่านการ backup/import แบบ JSON และ snapshot ของเวอร์ชันเท่านั้น

## 6. ความแตกต่างจาก shape ของ carmen-backstage SPA

interface `ReportTemplate` ใน `../carmen-backstage/src/services/reportTemplateService.ts` (บรรทัด 21–59) และ interface `ReportTemplateFormData` ใน `../carmen-backstage/src/pages/ReportTemplateEdit.tsx` (บรรทัด 84–106) ถูกเทียบกับ Prisma model `tb_report_template` ที่น่าสังเกตคือ TS interface `ReportTemplate` อยู่ใน `src/services/reportTemplateService.ts` ไม่ใช่ `src/types/index.ts` ที่ interface ของโมดูล Platform ตัวอื่น (`Cluster`, `BusinessUnit`, `User`) อยู่ — นักพัฒนาที่ค้นหา TS shape ฉบับ canonical ควรดูในไฟล์ service

**แก้ไขแล้วเมื่อ 2026-07-23 (ไม่ใช่ความแตกต่างอีกต่อไป):** `kind`/`template_type` และ `is_default` ตอนนี้ตรงกันทั้งสองฝั่ง `ReportTemplateFormData` มี `template_type: '' | 'form' | 'list'` (จำเป็น เปิดเผยเป็น select) และ `is_default: boolean` — รายการที่ 1 ของ sync ครั้งก่อน ("`kind` ไม่มีในฟอร์ม") ล้าสมัยแล้ว ฟิลด์นี้ไม่เพียงมีอยู่แต่ยังจำเป็นตอน submit ด้วย

| # | รายการ | Prisma มี | SPA คาดหวัง | หมายเหตุ |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `orientation` | `String @db.VarChar(20)` | optional บน service type `ReportTemplate`; ไม่อยู่ใน `ReportTemplateFormData` | ยังไม่มี control ในฟอร์ม ณ 2026-10-27 default เป็น `"portrait"` ที่ระดับฐานข้อมูล; เดินทางผ่าน backup, import และ snapshot ของเวอร์ชัน |
| 2 | `signature_config` | `Json @db.JsonB` | optional บน service type `ReportTemplate`; ไม่อยู่ใน `ReportTemplateFormData` | ยังไม่มี control ในฟอร์ม เดินทางผ่าน backup และ import (Import เติม `{ blocks: [] }` เมื่อไฟล์มี `{}` ตามที่ seeder ของ micro-report เขียน) |
| 3 | `view_name` | `String? @db.VarChar` | optional บน service type `ReportTemplate` | คอลัมน์ legacy; load path ของฟอร์ม Edit ถอยกลับไปใช้ (`template.source_name \|\| template.view_name`) dialog Import ตัดมันออกจาก payload (DTO ไม่รับ) แต่ backup และ snapshot ของเวอร์ชันยังพกมัน |
| 4 | `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | `unknown` บน service interface `ReportTemplate`; `string` ใน `ReportTemplateFormData` | ฟอร์ม Edit normalise ค่า JSON (array หรือ scalar) เป็น string คั่นด้วย comma ผ่าน `toCsv()` สำหรับฟิลด์ chip-input ถูก disable และล้างค่าฝั่ง client เมื่อ `template_type = 'form'` — form template ไม่ถูกกำหนดขอบเขต BU แบบนี้ |
| 5 | `created_by_id` / `updated_by_id` | `String? @db.Uuid` (id ดิบ) | `created_by_id?: string` / `updated_by_id?: string` บน `ReportTemplate` | id ดิบมีอยู่ใน service interface SPA ยังอ่าน `created_by_name` / `updated_by_name` จาก API response ด้วย (backend resolve ให้) แต่ค่าเหล่านี้ถูกถือใน state variable `MetadataFields` ที่แยกออกมา ไม่อยู่ใน type `ReportTemplate` |
| 6 | `source_params` | `Json @db.JsonB` (non-nullable) | `source_params?: ReportSourceParams` (optional) บน service interface | service interface ทำเครื่องหมาย optional เพื่อรองรับ API response บางส่วน; default ของ Prisma รับประกันว่าคอลัมน์ใน DB มีค่าเสมอ |

ฟิลด์ identity หลักทั้งหมด (`id`, `name`, `description`, `report_group`, `template_type`), ฟิลด์ payload XML (`dialog`, `content`), ฟิลด์การผูก source (`source_type`, `source_name`), flag วงจรชีวิต (`is_standard`, `is_default`, `is_active`), `doc_version` และ timestamp ของ audit (`created_at`, `updated_at`) สอดคล้องกันระหว่าง Prisma กับ shape ของ SPA ความแตกต่างที่เหลือเป็นคอลัมน์ Prisma ใหม่ที่ยังไม่ปรากฏในฟอร์ม edit (รายการ 1–3) หรือ type coercion ที่ชั้นฟอร์มสำหรับคอลัมน์ JSON (รายการ 4, 6)

## 7. แหล่งข้อมูลอ้างอิง

**หลัก (source of truth):**
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `model tb_report_template` (บรรทัด 1027) และ `model tb_report_template_version` (บรรทัด 1124)
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/migrations/20260723120000_print_form_default/migration.sql` — data migration ที่มากับการเปลี่ยนชื่อ `kind`→`template_type`, การเพิ่ม `is_default`, unique index และการ drop `tb_print_template_mapping`

**รอง (shape ฝั่ง consumer):**
- `../carmen-backstage/src/pages/ReportTemplateEdit.tsx` — interface `ReportTemplateFormData` (บรรทัด 84–106); interface `SourceParamRow` (บรรทัด 78–82); load path รวม `toCsv` (`fetchTemplate`, บรรทัด 255–330); save path รวมการประกอบ payload `source_params`/`template_type`/i18n (`handleSubmit`, บรรทัด 384–485)
- `../carmen-backstage/src/pages/ReportTemplateManagement.tsx` — view list ของเทมเพลตรายงาน
- `../carmen-backstage/src/pages/ReportFormGroupManagement.tsx` — หน้าจอ Form Groups ที่แก้ไข `is_default` ต่อ `report_group`
- `../carmen-backstage/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS` รายการ code คงที่ 12 ตัวที่ SPA จำกัด `report_group` ไว้สำหรับ form template
- `../carmen-backstage/src/services/reportTemplateService.ts` — interface `ReportTemplate` (บรรทัด 21–59); type `ReportSourceType`, `CalculationMethod`, `ReportSourceParam`, `ReportSourceParams` (บรรทัด 5–19); `setGroupDefault` (บรรทัด 118–137); `listVersions` / `getVersion` / `restoreVersion` (บรรทัด 139–158)
- `../carmen-backstage/src/types/index.ts` — ไม่มี type `ReportTemplate` นิยามไว้ที่นี่; type อยู่ในไฟล์ service

**Cross-link:**
- [report-templates](/th/backstage/report-templates) — หน้า landing ของโมดูล
- **Print Template Mapping** — ถูกลบออกจากผลิตภัณฑ์เมื่อ 2026-07-24 (carmen-backstage commit `de11377`); เคยเป็นเจ้าของ `tb_print_template_mapping` ที่ถูก drop โดย migration `20260723120000_print_form_default` เดียวกับที่เพิ่ม `is_default` ที่นี่ หน้าที่ของมันตอนนี้ทำโดย `template_type = "form"` + `report_group` + `is_default` บนตารางนี้ แสดงผลผ่านโมดูล [กลุ่มฟอร์ม (Form Groups)](/th/backstage/report-form-groups) แบบ standalone
- [business-units](/th/backstage/business-units) — BU code ที่อ้างอิงใน chip list ของ allow/deny ตรงกับ `tb_business_unit.code`
- [clusters](/th/backstage/clusters) — surface พี่น้องของ Platform; เทมเพลตรายงานเป็น tenant-global และไม่ scope ต่อ cluster
- [Permissions](/th/backstage/report-templates/permissions) — การควบคุมการเข้าถึงของ surface การจัดการ report-templates
- [UI Screens](/th/backstage/report-templates/ui-screens) — หน้าจอ SPA สำหรับการจัดการและแก้ไขเทมเพลตรายงาน
- [XML Spec](/th/backstage/report-templates/xml-spec) — โครงสร้างโดยละเอียดของ payload XML `dialog` และ `content`
