---
title: การจัดการเอกสาร (Document Management)
description: Registry การจัดเก็บไฟล์ scope ตาม tenant backed ด้วย MinIO และตาราง tb_file_tag ในฐานข้อมูล file-service แยกต่างหาก — ไม่ใช่ tb_attachment ของ tenant schema ซึ่งเป็นตาราง dead ที่ไม่มีการอ้างอิงเลย Upload ไม่มีการ validate ขนาดหรือ MIME ฝั่ง server
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, document, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# การจัดการเอกสาร (Document Management)

> **At a Glance**
> **เจ้าของ:** Sysadmin (delete); list / download ผ่าน App ID grant &nbsp;·&nbsp; **การจัดเก็บ:** Microservice `micro-file` ผ่าน MinIO + ตาราง metadata `tb_file_tag` ใน **ฐานข้อมูล `prisma-shared-schema-file` แยกต่างหาก** — **ไม่ใช่** `tb_attachment` ของ tenant schema ซึ่งไม่มีการอ้างอิงจากโค้ดเลย &nbsp;·&nbsp; **ใช้โดย:** การแนบไฟล์ PR / PO / GRN / SR / IA / count / pricelist / vendor / product &nbsp;·&nbsp; **ขีดจำกัด 10 MB และ MIME allow-list เป็น frontend-only — ไม่ถูก re-validate ฝั่ง server**

![การจัดการเอกสาร (Document Management) screen](/screenshots/system-config/document.png)

## สถานะการ implement (ตรวจสอบ 2026-07-16)

สองข้อแก้ไขสำหรับเวอร์ชันก่อนหน้าของหน้านี้:

1. **ตาราง metadata คือ `tb_file_tag` ไม่ใช่ `tb_attachment`** การค้นทั่ว repo พบว่า **ไม่มีการอ้างอิง `tb_attachment` เลย** ที่ไหนใน `carmen-turborepo-backend-v2/apps` นอกเหนือจากการประกาศ Prisma model ของมันเอง — ไม่มี service, controller หรือ DTO ใดอ่านหรือเขียนมัน เส้นทาง upload ไฟล์จริง (`micro-file/src/files/files.service.ts`) ใช้ `PrismaClient_FILE` จากฐานข้อมูล `@repo/prisma-shared-schema-file` ที่แยกต่างหากทั้งหมด (schema `CARMEN_FILE`) และเขียนหนึ่ง row ต่อการ upload ลงใน **`tb_file_tag`** (`bu_code`, `file_token`, `object_name`, `original_name`, `content_type`, `size`, `reference_type`/`reference_id`/`reference_no`, `tags` JSONB แบบอิสระ) — การจัดเก็บเองคือ **MinIO** ระบุตำแหน่งผ่าน `minioClient.putObject`/`getObject`/`removeObject`/`presignedGetObject` ไม่ใช่ claim "S3-compatible" ทั่วไปที่ผูกกับ `tb_attachment` §5 ด้านล่างแก้ไขให้อธิบาย `tb_file_tag` แล้ว
2. **ไม่มีการ validate ขนาดหรือ MIME ฝั่ง server** `uploadFile()` ของ `files.service.ts` เรียก `minioClient.putObject` ด้วย `mimetype` และ buffer ที่ client ส่งมาตรงๆ — ไม่มีการตรวจสอบขนาดไฟล์และไม่มี MIME/extension allow-list ใดๆ ใน method นั้นเลย ขีดจำกัด 10 MB (`MAX_FILE_SIZE = 10 * 1024 * 1024` ใน `document-component.tsx`) และ attribute `accept` ของ picker เป็น **frontend-only** — ผู้เรียกที่ข้าม browser ไป (เรียก API ตรง) สามารถ upload ไฟล์ที่ใหญ่กว่าหรือประเภทใดก็ได้ ไม่พบ claim "defence-in-depth MIME sniffing ฝั่ง server" ในโค้ดเลย

## 1. คืออะไรและใครใช้

Document Management คือ **registry surface การจัดเก็บไฟล์** ที่ `/system-admin/document` — index ที่ scope ตาม BU ของทุกไฟล์ที่ upload เข้า Carmen แต่ละ row คือ object หนึ่งใน MinIO storage บวกกับ metadata สำหรับแสดงผลใน `tb_file_tag` ไฟล์เดียวกันนี้ปรากฏที่อื่นในรูปของ attachment บนเอกสาร PR / PO / GRN / SR / IA / pricelist / count โดยแต่ละตารางธุรกรรมจะพกพา `attachments` JSONB ที่อ้างอิง **file token** จาก registry นี้

**กลุ่มเป้าหมาย:** Sysadmin จัดการ upload / delete ที่นี่; role ที่ไม่ใช่ admin โดยทั่วไปมี list / get / download แต่ไม่มี delete File microservice (`micro-file`, commands `files.upload` / `files.get` / `files.info` / `files.find-all` (list) / `files.delete` / `files.presigned-url` / `files.update-tags`) เป็นเจ้าของการจัดเก็บและ metadata registry; module `document-management` ของ gateway proxy REST surface ไปให้มันผ่าน TCP

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Upload ไฟล์ใหม่ | System Admin → Document → **Upload** | Single-file picker; picker แนะนำ `.pdf, .docx, .xls/.xlsx, .csv, .txt`; frontend reject ไฟล์เกิน 10 MB — **ทั้งสองอย่างไม่ถูกบังคับฝั่ง server** |
| Filter ตามประเภทไฟล์ | Multi-select ประเภท (PDF, Excel/CSV, Word, Image, Text, Archive, Code) | URL-synced; active-filter badge bar ปรากฏ |
| Download ไฟล์ | Action download ต่อ row | Presigned URL ผ่าน `GET /api/:bu_code/documents/:filetoken/download` |
| แชร์ link แบบจำกัดเวลา | `GET /api/:bu_code/documents/:filetoken/presigned-url?expirySeconds=N` | ห้าม embed credentials การจัดเก็บถาวรใน browser |
| Delete ไฟล์เก่า | Delete ต่อ row (Sysadmin เท่านั้น) | Dialog ยืนยัน; ลบ object ใน MinIO **และ** soft-delete (`deleted_at`) row ของ `tb_file_tag`; `fileToken` ที่ค้างจะ render เป็น "missing" บนเอกสารที่ผูก |
| แนบไฟล์กับ PR / PO / GRN | **ไม่ใช่ที่นี่** — ใช้หน้าจอธุรกรรม | หน้านี้คือ registry ไม่ใช่การจัดการ attachment ต่อเอกสาร |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Toast `fileSizeLimit` ตอน upload | File > 10 MB — **ตรวจสอบฝั่ง frontend เท่านั้น** | บีบอัด / แบ่งก่อน upload; พึงระวังว่าการเรียก API ตรงข้ามการตรวจสอบนี้ได้ทั้งหมด |
| File ถูก reject โดย picker | MIME ไม่อยู่ในรายการแนะนำของ picker — **เป็นแค่คำแนะนำฝั่ง frontend ไม่บังคับฝั่ง server** | แปลงเป็นรูปแบบที่ยอมรับ หรือรู้ไว้ว่า server จะรับไฟล์นั้นจริงๆ ผ่าน API โดยตรง |
| Attachment "missing" บน PR/PO/GRN | File ถูกลบจาก registry ขณะที่ยังถูก reference | Upload ใหม่และแนบใหม่; ทำความสะอาด `fileToken` ที่ค้างด้วยมือ |
| 403 ตอน delete | User ไม่มี App ID `documents.delete` | Grant ผ่าน [access-control/application-role](/th/inventory/access-control/application-role) — ยืนยันจริง: `AppIdGuard('documents.delete')` บน gateway controller |
| File จาก BU `T01` มองไม่เห็นใน BU `T02` | คาดหวัง — prefix การจัดเก็บ scope ตาม BU | แต่ละ BU มี partition ของตัวเอง; การเข้าถึง cross-BU เป็นไปไม่ได้ |
| Presigned URL หมดอายุ | `expirySeconds` หมดแล้ว | ขอใหม่ |

## 4. กรณีพิเศษ

- **ขีดจำกัด 10 MB และ MIME allow-list เป็น frontend-only** ยืนยันว่าไม่มีการบังคับฝั่ง server ใน `uploadFile()` ของ `files.service.ts` ไฟล์ที่ใหญ่กว่าหรือประเภทที่ไม่อยู่ในรายการถูกบล็อกก็ต่อเมื่อ request ผ่านการตรวจสอบฝั่ง client ของ picker เท่านั้น
- **Delete คือ soft-delete บน registry row, hard บน storage** `deleteFile()` ลบ object ใน MinIO (กู้คืนไม่ได้) และตั้ง `tb_file_tag.deleted_at` (best-effort — ถ้าการอัปเดต DB ล้มเหลวหลังจาก object ถูกลบไปแล้ว จะแค่ log warning ไม่ throw error) array `attachments` JSONB ต่อเอกสาร *ไม่* ถูก clean up — token ที่ค้าง render เป็น "missing" ห้าม delete ไฟล์ที่ยังแนบกับเอกสารที่ดำเนินอยู่
- **`tb_attachment` (tenant schema) คือตาราง dead** มีคอลัมน์ `doc_version Int @default(0)` shape เดียวกับที่อธิบายใน [system-config/doc-version](/th/inventory/system-config/doc-version) แต่ **ไม่มีโค้ดใดอ่านหรือเขียนมันเลย** และมันไม่ใช่ตารางเดียวกับ registry จริง (`tb_file_tag` ในฐานข้อมูล file-service แยกต่างหาก) ดู [system-config/doc-version](/th/inventory/system-config/doc-version) §5 สำหรับ framing ที่แก้ไขแล้วของฟิลด์นี้
- **Presigned URL ดีกว่า streaming โดยตรง** สำหรับการแชร์ browser — ห้าม embed credentials การจัดเก็บถาวรในหน้า

---

## 5. แบบจำลองข้อมูล (Dev)

ตาราง `tb_attachment` ของ tenant schema **ไม่ใช่** registry จริง — ยืนยันว่าไม่มีการอ้างอิงจากโค้ดเลยที่ไหนนอกเหนือจากการประกาศ Prisma ของมันเอง File ถูก track จริงในฐานข้อมูล file-service แยกต่างหากบวกกับ array JSONB ต่อเอกสาร

### 5.1 `tb_file_tag` (registry metadata จริง — ฐานข้อมูล `prisma-shared-schema-file` แยกต่างหาก)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `bu_code` | `String @db.VarChar` | No | Business unit เจ้าของ |
| `file_token` | `String @db.VarChar` (unique) | No | Handle canonical รูปแบบ `<bu_code>/<uuid>` — ตรงกับ `attachments[].fileToken` ต่อเอกสาร |
| `object_name` | `String @db.VarChar` | No | MinIO object key (`<file_token>.<ext>`) |
| `original_name` | `String @db.VarChar` | No | ชื่อไฟล์สำหรับแสดง |
| `content_type` | `String @db.VarChar` | No | ประเภท MIME ตามที่ request upload ส่งมาตรงๆ |
| `size` | `Int` | No | Bytes |
| `reference_type` / `reference_id` / `reference_no` | `String? @db.VarChar` | Yes | ฟิลด์ tag แบบมีโครงสร้าง (indexed) — ไฟล์นี้เป็นของเอกสารไหน |
| `description` | `String?` | Yes | Free text |
| `tags` | `Json? @db.JsonB` | Yes | ถุง tag แบบอิสระ, default `{}`; GIN-indexed |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` (model นี้ไม่มี `doc_version`) |

**Constraints:** unique บน `file_token`; index บน `[bu_code, deleted_at]`, `[bu_code, reference_type, reference_id]`, `[bu_code, reference_no]` และ GIN index บน `tags` การจัดเก็บเองคือ bucket **MinIO** (`envConfig.MINIO_BUCKET_NAME`) ระบุตำแหน่งด้วย `object_name` — ไม่ใช่บัญชี S3 ของบุคคลที่สามทั่วไป

### 5.2 `tb_attachment` (tenant schema — ตาราง dead เก็บไว้เพื่อเปรียบเทียบ)

`id` / `s3_token` / `s3_folder` / `file_name` / `file_ext` / `file_type` / `file_size` / `file_url` / `doc_version Int @default(0)` / audit columns — มีรูปร่างเหมือน file registry แต่ **ไม่พบการอ้างอิงจากโค้ด non-schema เลย** อย่าถือว่าเป็นตาราง backing ของ Document Management

### 5.3 `attachments` JSONB ต่อเอกสาร

ทุกตารางธุรกรรมที่รองรับ attachment (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) พกพา:

```jsonc
"attachments": [
  { "fileToken": "T01/019638a6-...", "fileName": "vendor-invoice.pdf",
    "fileSize": 102400, "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z" }
]
```

`fileToken` ตรงกับ `tb_file_tag.file_token` (**ไม่ใช่** `tb_attachment.s3_token`) Endpoint list query `micro-file`/`tb_file_tag` (source of truth) ไม่ใช่ tenant schema

### 5.4 `DocumentFile` API projection

`fileToken` (อาจพา prefix `<buCode>/` — ตัดออกก่อน delete) &nbsp;·&nbsp; `objectName` &nbsp;·&nbsp; `originalName` &nbsp;·&nbsp; `size` &nbsp;·&nbsp; `contentType` (ขับเคลื่อน filter ประเภท) &nbsp;·&nbsp; `lastModified`

## 6. กฎทางธุรกิจ

- **ขีดจำกัด upload 10 MB และ MIME allow-list เป็น frontend-only** ยืนยันว่าไม่มีการตรวจสอบฝั่ง server ใน `uploadFile()` ของ `files.service.ts`
- **Scope ตาม BU** ทุก endpoint ภายใต้ `/api/:bu_code/documents/*`; object ใน MinIO และ row ของ `tb_file_tag` ทั้งคู่ partition ตาม `bu_code`
- **Presigned URL** สำหรับ download / share — ห้าม embed credentials ถาวร
- **AppId guards (ยืนยันจริง)** `documents.upload`, `documents.list`, `documents.get`, `documents.download`, `documents.info`, `documents.presignedUrl`, `documents.delete` — แต่ละอันคือ decorator `AppIdGuard(...)` ที่แยกกันบน `document-management.controller.ts` Non-admin = list / get / download เท่านั้น
- **Delete** การลบ object ใน MinIO ทันทีและกู้คืนไม่ได้; row ของ `tb_file_tag` ถูก soft-delete (`deleted_at`) แบบ best-effort (ถ้า DB ล้มเหลวจะแค่ log ไม่ throw) array `attachments` ต่อเอกสาร *ไม่* cascade
- **Audit logging** ผ่าน `runWithAuditContext`/`AuditContext` ใน controller ของ `micro-file` (upload, delete, presigned-URL, tag update)
- **ไม่มี versioning แบบ in-place** — overwrite ผ่าน delete + re-upload

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) / [store-requisition](/th/inventory/store-requisition) / [inventory-adjustment](/th/inventory/inventory-adjustment) / [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) — พกพา `attachments` JSONB
- [master-data/vendor](/th/inventory/master-data/vendor) / [product](/th/inventory/product) — vendor และ product master record พกพา array `attachments` ของตัวเอง
- [system-config/doc-version](/th/inventory/system-config/doc-version) — `tb_attachment.doc_version` คือคอลัมน์ที่ไม่มีชีวิตบนตาราง dead นี้ ไม่ใช่ concurrency guard หรือ re-render counter ที่ใช้งานจริง
- [reporting-audit/report](/th/inventory/reporting-audit/report) — artefact รายงานที่สร้างขึ้นมามีเจตนาให้ลงที่นี่ผ่านกลไก `fileToken` เดียวกัน (ยังไม่ยืนยันในรอบนี้)
- [system-config/workflow](/th/inventory/system-config/workflow) — comment ของเวิร์กโฟลว์ embed array `attachments` สำหรับไฟล์หลักฐาน

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma (file schema — registry จริง):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-file/prisma/schema.prisma` — `tb_file_tag` (lines ~19-49)
- **Prisma (tenant schema — ตาราง dead เพื่อเปรียบเทียบ):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4797-4819); คอลัมน์ `attachments` JSONB ต่อเอกสารกระจายอยู่
- **Backend gateway (ชั้น proxy):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts` + `document-management.service.ts` — forward ไปยัง microservice `FILE_SERVICE` ผ่าน TCP command `files.*`
- **Backend file microservice (การจัดเก็บ + registry จริง):** `../carmen-turborepo-backend-v2/apps/micro-file/src/files/files.controller.ts` + `files.service.ts` — MinIO client, `tb_file_tag` CRUD
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/document/document.route.tsx` + `document-component.tsx`
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-document.ts` — `useDocument`, `useUploadDocument`, `useDeleteDocument`
- **Frontend type:** `../carmen-inventory-frontend-react/types/document.ts` — `DocumentFile`
