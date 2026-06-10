---
title: Print Template Mapping — แบบจำลองข้อมูล (Data Model)
description: ตาราง tb_print_template_mapping (ไม่มี unique constraint, ไม่มี FK ระดับ DB), tb_report_template ที่ถูกอ้างอิง, shape การอ่านแบบ denormalize ของ Go และ quirk ของ JSONB ในการ update แบบ merge
published: true
date: 2026-06-10T15:30:00.000Z
tags: book/platform, print-template-mapping, data-model
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# Print Template Mapping — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_print_template_mapping` (เป็นเจ้าของ) &nbsp;·&nbsp; `tb_report_template` (ถูกอ้างอิง — doc ฉบับเต็มอยู่ใน Report Templates) &nbsp;·&nbsp; **Enum:** ไม่มี — `document_type` เป็น VarChar ที่ validate กับรายการ Go แบบ hard-code จำนวน 10 code &nbsp;·&nbsp; **Constraint:** มีเพียง `@id` — **ไม่มี `@@unique`, ไม่มี `@relation` ของ Prisma/FK ของ DB**; การเชื่อมโยงเทมเพลตและกฎ single-default อยู่ที่ชั้น application &nbsp;·&nbsp; **Shape การอ่าน:** LEFT JOIN ของ Go ทำการ denormalize `template_name` / `template_group` / ชื่อ audit ลงบนแต่ละ row &nbsp;·&nbsp; **Quirk การเขียน:** `PUT` เป็น partial merge และ JSON `null` หมายถึง "คงเดิมไม่เปลี่ยน" — SPA เคลียร์รายการ BU ไม่ได้

> **Source of truth:** Prisma platform schema ฝั่ง backend — อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูลนี้เป็นเจ้าของตารางเดียว `tb_print_template_mapping` คือ row สำหรับ routing: code `document_type` หนึ่งตัว, pointer ไปยัง `tb_report_template` ที่ render มัน, field การนำเสนอสำหรับเมนูพิมพ์ (`is_default`, `display_label`, `display_order`), คู่ allow/deny ของ BU, `is_active` และ audit trio มาตรฐานของแพลตฟอร์ม comment ใน schema ระบุสัญญาไว้: หลาย row อาจใช้ `document_type` ร่วมกันได้; *ควร* มีเพียงหนึ่งเดียวที่ติด flag `is_default` สำหรับปุ่ม Print แบบ legacy ส่วนที่เหลือปรากฏในเมนู "Print as…"

ผิดปกติสำหรับ platform schema ตารางนี้**ไม่มี unique constraint และไม่มี relation ของ Prisma เลยแม้แต่ตัวเดียว** — ฐานข้อมูลยอมเก็บคู่ `(document_type, report_template_id)` ที่ซ้ำกัน, ค่า `report_template_id` ที่ค้างลอย (dangling) และ default หลายตัวอย่างหน้าตาเฉย กฎ integrity ทุกข้ออยู่ที่ชั้น application: Go service ของ micro-report ทำการ validate `document_type` กับรายการ hard-code ของมัน, ลดสถานะ default ที่แข่งกันแบบ best-effort หลังการ save แต่ละครั้ง และ join เทมเพลตด้วย id ตอนอ่าน ผู้ทดสอบควรปฏิบัติกับ DB ว่าเป็นแบบ permissive และ probe กฎที่ชั้น service แทน

แม้ตารางจะอยู่ใน Prisma schema ของแพลตฟอร์ม แต่**เจ้าของ CRUD คือ Go service ของ micro-report** (GORM, `db/print_template_mapping_repo.go`); controller ของ backend-gateway เป็น proxy แบบ pass-through และ Prisma แตะตารางนี้เฉพาะใน seed และใน query แบบ inline ของเส้นทางพิมพ์ของ micro-business (§5)

## 2. เอนทิตี

### 2.1 `tb_print_template_mapping`

หนึ่ง row ของการ route ชนิดเอกสาร → เทมเพลต (schema บรรทัด 776)

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `document_type` | `String @db.VarChar(50)` | No | code ของชนิดเอกสาร (`PR`, `PO`, `GRN`, …); เป็นรูปแบบอิสระใน schema, validate โดย Go service กับ `SupportedDocumentTypes` (§4) |
| `report_template_id` | `String @db.Uuid` | No | Id ของ row `tb_report_template` ที่ทำหน้าที่ render — **ไม่มี `@relation`, ไม่มี FK ของ DB**; resolve ผ่าน LEFT JOIN ตอนอ่าน |
| `is_default` | `Boolean @default(true)` | No | เทมเพลตสำหรับปุ่ม Print แบบ legacy **Default เป็น `true`** — ทุก row ใหม่อ้างสิทธิ์เป็น default เว้นแต่จะถูก untick อย่างชัดเจน |
| `display_label` | `String? @db.VarChar(255)` | Yes | Label ที่แสดงในเมนู "Print as…" (เช่น "Standard PR (A4 Portrait)") |
| `display_order` | `Int @default(0)` | No | ตำแหน่งการเรียงในเมนู "Print as…"; tie-breaker ของ resolve (§5 row 7) |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | Array ของ BU code ที่ได้รับอนุญาตให้ใช้ mapping นี้; `NULL`/ว่าง = ทุก BU (convention เดียวกับ `tb_report_template`) |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | Array ของ BU code ที่ถูก deny; `NULL`/ว่าง = ไม่มี; deny ชนะ allow |
| `is_active` | `Boolean @default(true)` | No | row ที่ inactive ถูกข้ามโดย `resolve` และถูกซ่อนหลัง filter "Active only" ของหน้า list |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้สร้าง — UUID เปล่า ไม่มี FK |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้อัพเดทล่าสุด — UUID เปล่า ไม่มี FK |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: user id ของผู้ลบ — UUID เปล่า ไม่มี FK |

**Constraint:**
- `@id` บน `id` — และไม่มีอะไรอื่นเลย ไม่มี `@@unique` (เทียบกับความ unique ของชื่อแบบรองรับ soft-delete ของ `tb_application`): row `(document_type, report_template_id)` ที่ซ้ำกันและหลาย row ที่ `is_default = true` ต่อชนิดสามารถมีอยู่ได้ที่ระดับ DB
- ไม่มี FK constraint ใด ๆ ทั้งสิ้น — `report_template_id` และ audit id เป็น UUID เปล่า

**Index:**
- `@@index([document_type])` — map `"idx_print_template_mapping_document_type"` — ขับเคลื่อนทั้ง filter ของหน้า list และ `resolve`
- `@@index([report_template_id])` — map `"idx_print_template_mapping_template_id"` — ขับเคลื่อนการ lookup แบบ "เทมเพลตนี้ถูกใช้ที่ไหน"

### 2.2 `tb_report_template` (ถูกอ้างอิง)

เป้าหมายของ mapping เอกสารฉบับเต็มอยู่ใน [Report Templates — Data Model](/th/platform/report-templates/data-model); ที่นี่สนใจเฉพาะมุมมองฝั่ง FK mapping ตั้งใจให้ชี้ไปยัง row ที่ `kind = "print"` (layout เอกสารที่พิมพ์ได้ ตรงข้ามกับรายงานเชิงวิเคราะห์ `kind = "report"`) ซึ่ง `report_group` เท่ากับ `document_type` ของ mapping — select เทมเพลตของ SPA ลอย match เหล่านั้นขึ้นด้านบนเป๊ะ ๆ เส้นทางอ่านของ Go ทำ LEFT JOIN เทมเพลตเพื่อ denormalize `name` (เป็น `template_name`) และ `report_group` (เป็น `template_group`) ลงบนทุก row ของ mapping admin UI จึงไม่ต้อง round-trip ครั้งที่สอง เนื่องจาก join เป็น LEFT JOIN ที่ไม่มี FK อยู่เบื้องหลัง mapping ที่เทมเพลตถูกลบไปแล้วจึงยังโหลดได้ — โดย `template_name` เป็น null — แทนที่จะล้มเหลว

## 3. ความสัมพันธ์

```
tb_report_template  1 ─── M  tb_print_template_mapping
    (เชิง logic เท่านั้น — ไม่มี @relation ของ Prisma, ไม่มี FK ของ DB;
     join ผ่าน report_template_id ใน read SQL ของ micro-report)

tb_print_template_mapping.created_by_id / updated_by_id / deleted_by_id
    ──> tb_user.id  (audit actor ตาม convention — UUID เปล่า ไม่มี FK;
         micro-report join tb_user_profile เฉพาะบน created_by_id และ
         updated_by_id — deleted_by_id ไม่ได้ join ชื่อสำหรับแสดงผล)
```

ไม่มีความสัมพันธ์กับ cluster หรือ business unit: การกำหนดขอบเขต BU ถูกถือเป็น array ของ code แบบ JSONB ไม่ใช่ join row ดังนั้นไม่มีอะไรใน schema ที่ห้ามรายการระบุ BU code ที่ไม่มีอยู่จริง

## 4. Enum

ไม่มี enum ของ Prisma สองคอลัมน์ถือคลังศัพท์ที่ถูกจำกัดซึ่งบังคับใช้นอก schema:

- **`document_type`** — validate ตอน create/update โดย Go service ของ micro-report กับ `model.SupportedDocumentTypes` (slice ของ Go แบบ hard-code ซึ่งถูกเสิร์ฟโดย `GET .../document-types` ด้วย): `PR` Purchase Request · `PO` Purchase Order · `GRN` Good Received Note · `SR` Store Requisition · `CN` Credit Note · `IA` Inventory Adjustment · `PC` Physical Count · `SC` Spot Check · `RFQ` Request For Quotation · `INV` Invoice code ที่ไม่อยู่ในรายการได้ 400 ("unsupported document_type — see GET /document-types"; เส้นทาง update ละ suffix "— see GET /document-types") การขยายรายการเป็นการเปลี่ยนโค้ด Go และ redeploy
- **`allow_business_unit` / `deny_business_unit`** — ตาม convention เป็น JSON array ของ string BU code; ตัวอ่านฝั่ง Go ทนทานต่อ `[]string` หรือ `[]any`-ของ-string และทิ้ง element ที่ไม่ใช่ string เงียบ ๆ

## 5. ความแตกต่างจาก shape ของ carmen-platform SPA

type ของ SPA คือ `PrintTemplateMapping` ใน `src/services/printTemplateMappingService.ts` (ไม่ใช่ `src/types/index.ts`); การ map ของฟอร์มอยู่ใน `PrintTemplateMappingEdit.tsx` ความแตกต่างเทียบกับ Prisma และ Go service ณ 2026-06-10:

| # | ประเด็น | Shape ของ SPA | ความเป็นจริงของ storage / service | หมายเหตุ |
|---|--------|-----------|---------------------------|-------|
| 1 | การกำหนด type ของรายการ BU | `allow_business_unit?: unknown` / `deny_business_unit?: unknown` | array JSONB แบบ `Json?` | จงใจไม่กำหนด type: `rowToForm` ทนทานต่อ `string[]` **หรือ** string แบบ CSV ตอนอ่าน; ตอนเขียน `parseList` ส่ง `string[]` เสมอ (หรือ `null` เมื่อว่าง) |
| 2 | การเคลียร์รายการ BU | ช่องกรอกว่าง → field ใน payload เป็น `null` | Go ปฏิบัติกับ JSON `null` ว่า *ไม่ได้ส่งมา* (การตรวจสอบ nil-interface) และคงรายการที่เก็บไว้; repo ยังข้ามคอลัมน์ JSONB ที่เป็น nil ใน map ของ `Updates` อีกชั้น | **การทำให้รายการ allow/deny ว่างในฟอร์ม edit ของ SPA ไม่ได้เคลียร์มันฝั่ง server** วิธีเดียวที่จะเคลียร์คือ `PUT` ตรง ๆ พร้อม array ว่าง `[]` แบบระบุชัด |
| 3 | `template_name` / `template_group` / `created_by_name` / `updated_by_name` | field สำหรับอ่านแบบ optional | **ไม่ใช่คอลัมน์** — denormalize โดย LEFT JOIN ของ micro-report ไปยัง `tb_report_template` และ `tb_user_profile` | Read-only; ห้าม echo กลับไปในการเขียน `template_name` เป็น null เมื่อเทมเพลตที่ join ถูก soft-delete |
| 4 | semantics ของ `PUT` | ส่งฟอร์มแบบเต็ม | **Partial merge** ไม่ใช่ replace: Go คัดลอกเฉพาะ field ที่ส่งมาลงบน row ที่โหลดไว้; `document_type`/`report_template_id` ที่เป็น string ว่างถูกละเว้น | ตรงข้ามกับการ replace แบบเต็มชุดของโมดูล Applications — อย่า port convention ฝั่งใดไปอีกฝั่ง |
| 5 | Single default | UI ไม่บังคับ; checkbox ติ๊กได้อิสระบน row ใดก็ได้ | Go รัน `EnsureSingleDefault` หลัง create/update เมื่อ `is_default = true` โดยลดสถานะ default ตัวอื่นของชนิดเอกสารนั้น — **best-effort** (ความล้มเหลวเพียงแค่ log warning) | default ที่ซ้ำกันยังคงมีอยู่ได้ (การเขียน DB ตรง, การลดสถานะที่ล้มเหลว); `resolve` ทนทานต่อพวกมันผ่าน tie-break ของ `display_order` |
| 6 | การแบ่งหน้าของ list | SPA ส่งเพียง `document_type`/`active_only` และ render ทุกอย่างที่ได้รับ — ไม่มี UI การแบ่งหน้า | endpoint list ของ Go ใช้การแบ่งหน้ามาตรฐานของ monorepo ที่ **default `perpage = 10`** | เมื่อมี mapping ที่ live มากกว่า 10 ตัว หน้า list ของ SPA แสดงเพียงหน้าแรกเงียบ ๆ — ดู [UI Screens](./ui-screens.md) §2.5 |
| 7 | การ resolve ตอน runtime | `printTemplateMappingService.resolve()` มีอยู่แต่ไม่มีหน้าจอใดใน SPA เรียกมัน | `Resolve` ของ Go เคารพ flag active, รายการ BU และการเรียง `is_default DESC, display_order ASC` | สัญญา runtime ที่ตั้งใจไว้ **อย่างไรก็ตาม** เส้นทางพิมพ์จริงของ micro-business (`print-report.helper.ts`) ทำการ query Prisma โดยตรงด้วยการเรียงเดียวกันและ**ไม่ apply รายการ BU เลย** — ดู [Permissions](./permissions.md) §3 |

## 6. แหล่งข้อมูลอ้างอิง

REST surface (backend-gateway `api-system/print-template-mappings`, proxy 1:1 ไปยัง micro-report `/api/print-template-mappings`):

| Method + Path | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|
| `GET /api-system/print-template-mappings` | List | filter `document_type`, `active_only`; การแบ่งหน้าแบบ monorepo (`page`/`perpage`/`search`/`sort`/`filter`) ถูกส่งต่อ, default `perpage` 10; row มี field จากการ join ที่ denormalize แล้ว |
| `GET /api-system/print-template-mappings/document-types` | รายการชนิดเอกสารแบบ canonical | `{ document_types: [{ code, label }] }` จาก slice ของ Go แบบ hard-code |
| `GET /api-system/print-template-mappings/resolve?document_type=X&bu_code=Y` | การ resolve ตอน runtime | `document_type` จำเป็น (400 ถ้าว่าง); 404 เมื่อไม่มี mapping ที่ active ตัวใดอนุญาต BU |
| `GET /api-system/print-template-mappings/:id` | Detail | gateway validate id ว่าเป็น UUID v4 |
| `POST /api-system/print-template-mappings` | สร้าง | ต้องมี `document_type` + `report_template_id`; `document_type` ถูก validate; `EnsureSingleDefault` รันหลัง save เมื่อ row ที่ save มี `is_default = true` |
| `PUT /api-system/print-template-mappings/:id` | อัพเดท | **Partial merge**; JSON `null` = คงเดิมไม่เปลี่ยน (§5 row 2, 4); `EnsureSingleDefault` รันหลัง save เมื่อ row ที่ save มี `is_default = true` |
| `DELETE /api-system/print-template-mappings/:id` | Soft delete | ตั้ง `deleted_at` / `deleted_by_id` |

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_print_template_mapping` (บรรทัด 776), `tb_report_template` (บรรทัด 701)
- `../micro-report/model/print_template_mapping.go` — model ของ GORM, `SupportedDocumentTypes`, field อ่านจากการ join
- `../micro-report/db/print_template_mapping_repo.go` — การ join ตอนอ่าน, `Resolve`, `EnsureSingleDefault`, เส้นทาง update ที่ข้าม JSONB ที่เป็น nil
- `../micro-report/controller/print_template_mapping_controller.go` — การ validate input และการ update แบบ partial-merge

**รอง (shape ฝั่ง consumer):**
- `../carmen-platform/src/services/printTemplateMappingService.ts` — `PrintTemplateMapping`, `DocumentType`, input ของ create/update
- `../carmen-platform/src/pages/PrintTemplateMappingEdit.tsx` — `rowToForm` (ความทนทานต่อ CSV-หรือ-array), `parseList` (shape การเขียน)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_print-template-mappings/platform_print-template-mappings.service.ts` — DTO ของ proxy
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.print-templates.ts` — mapping default ต่อชนิดที่ seed ไว้

**Cross-link:** [หน้า landing ของ Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — Data Model](../report-templates/data-model.md)
