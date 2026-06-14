---
title: การจัดการเอกสาร (Document Management)
description: Registry การจัดเก็บไฟล์ scope ตาม tenant — upload, list, download, presigned URL และ delete สำหรับเอกสารที่แนบกับ record ธุรกรรม
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, document, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# การจัดการเอกสาร (Document Management)

> **At a Glance**
> **เจ้าของ:** Sysadmin (delete); list / download ผ่าน App ID grant &nbsp;·&nbsp; **การจัดเก็บ:** Microservice `FILE_SERVICE` (S3-compatible) + metadata mirror ใน `tb_attachment` &nbsp;·&nbsp; **ใช้โดย:** การแนบไฟล์ PR / PO / GRN / SR / IA / count / pricelist / vendor / product &nbsp;·&nbsp; **จำกัด 10 MB, scope ตาม BU**

![การจัดการเอกสาร (Document Management) screen](/screenshots/system-config/document.png)

## 1. คืออะไรและใครใช้

Document Management คือ **registry surface การจัดเก็บไฟล์** ที่ `/system-admin/document` — index ที่ scope ตาม BU ของทุกไฟล์ที่ upload เข้า Carmen แต่ละ row คือ binary blob หนึ่งใน object storage (S3-compatible) บวกกับ metadata สำหรับแสดงผล ไฟล์เดียวกันนี้ปรากฏที่อื่นในรูปของ attachment บนเอกสาร PR / PO / GRN / SR / IA / pricelist / count โดยแต่ละตารางธุรกรรมจะพกพา `attachments` JSONB ที่อ้างอิง **file token** จาก registry นี้

**กลุ่มเป้าหมาย:** Sysadmin จัดการ upload / delete ที่นี่; role ที่ไม่ใช่ admin โดยทั่วไปมี list / get / download แต่ไม่มี delete File microservice (`FILE_SERVICE`, commands `files.upload` / `files.get` / `files.list` / `files.delete`) เป็นเจ้าของการจัดเก็บ; gateway เปิด REST surface

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Upload ไฟล์ใหม่ | System Admin → Document → **Upload** | Single-file picker; ยอมรับ `.pdf, .docx, .xls/.xlsx, .csv, .txt`; จำกัด 10 MB |
| ตรวจสอบขีดจำกัด upload 10 MB | Frontend reject ก่อน `POST` | `MAX_FILE_SIZE = 10 * 1024 * 1024`; backend re-validate; toast `fileSizeLimit` ตอน reject |
| Filter ตามประเภทไฟล์ | Multi-select ประเภท (PDF, Excel/CSV, Word, Image, Text, Archive, Code) | URL-synced; active-filter badge bar ปรากฏ |
| Download ไฟล์ | Action download ต่อ row | Presigned URL ผ่าน `GET /api/:bu_code/documents/:filetoken/download` |
| แชร์ link แบบจำกัดเวลา | `GET /api/:bu_code/documents/:filetoken/presigned-url?expirySeconds=N` | ห้าม embed credentials การจัดเก็บถาวรใน browser |
| Delete ไฟล์เก่า | Delete ต่อ row (Sysadmin เท่านั้น) | Dialog ยืนยัน; **hard delete** — `fileToken` ที่ค้างจะ render เป็น "missing" บนเอกสารที่ผูก |
| แนบไฟล์กับ PR / PO / GRN | **ไม่ใช่ที่นี่** — ใช้หน้าจอธุรกรรม | หน้านี้คือ registry ไม่ใช่การจัดการ attachment ต่อเอกสาร |

## 3. การตรวจสอบและ Error

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Toast `fileSizeLimit` ตอน upload | File > 10 MB | บีบอัด / แบ่งก่อน upload |
| File ถูก reject โดย picker | MIME ไม่อยู่ใน allow-list (`.pdf, .docx, .xls/.xlsx, .csv, .txt`) | แปลงเป็นรูปแบบที่ยอมรับ; `FILE_SERVICE` ยัง sniff ฝั่ง server |
| Attachment "missing" บน PR/PO/GRN | File ถูก hard-delete จาก registry ขณะที่ยังถูก reference | Upload ใหม่และแนบใหม่; ทำความสะอาด `fileToken` ที่ค้างด้วยมือ |
| 403 ตอน delete | User ไม่มี App ID `documents.delete` | Grant ผ่าน [access-control/application-role](/th/inventory/access-control/application-role) |
| File จาก BU `T01` มองไม่เห็นใน BU `T02` | คาดหวัง — prefix การจัดเก็บ scope ตาม BU | แต่ละ BU มี partition ของตัวเอง; การเข้าถึง cross-BU เป็นไปไม่ได้ |
| Presigned URL หมดอายุ | `expirySeconds` หมดแล้ว | ขอใหม่ |

## 4. กรณีพิเศษ

- **ขีดจำกัดแข็ง 10 MB** บังคับฝั่ง client *และ* server File ใหญ่กว่านี้ไม่มีทางหลีกใน pipeline ปัจจุบัน
- **MIME allow-list ตอน upload, หมวดกว้างกว่าตอน list** Frontend filter รู้จัก Image / Archive / Code ให้ upload เดิมยังค้นหาได้ แต่ upload ใหม่ต้องอยู่ใน allow-list ของ picker `FILE_SERVICE` ทำ defence-in-depth MIME sniffing ฝั่ง server
- **Hard delete, ไม่มี cascade** `DELETE` ลบ storage และตั้ง `tb_attachment.deleted_at`; array `attachments` JSONB ต่อเอกสาร *ไม่* ถูก clean up — token ที่ค้าง render เป็น "missing" ห้าม delete ไฟล์ที่ยังแนบกับเอกสารที่ดำเนินอยู่
- **ไม่มี versioning แบบ in-place** `tb_attachment.doc_version` default `0` และสงวนไว้; pipeline ปัจจุบัน overwrite ด้วย delete-and-re-upload
- **Presigned URL ดีกว่า streaming โดยตรง** สำหรับการแชร์ browser — ห้าม embed credentials การจัดเก็บถาวรในหน้า

---

## 5. แบบจำลองข้อมูล (Dev)

Tenant schema ไม่มีตาราง `tb_document` File ถูก track ในสองที่: ตาราง metadata mirror และ array JSONB ต่อเอกสาร

### 5.1 `tb_attachment` (file metadata mirror)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `s3_token` | `String? @db.VarChar(255)` | Yes | Storage token ที่ `FILE_SERVICE` ส่งคืน — handle canonical ปลายทาง |
| `s3_folder` | `String? @db.VarChar(255)` | Yes | Storage prefix (โดยทั่วไป `<bu_code>/<yyyy-mm>/`) |
| `file_name` / `file_ext` / `file_type` | `String?` | Yes | ชื่อสำหรับแสดง, นามสกุล, MIME |
| `file_size` | `BigInt? @db.BigInt` | Yes | Bytes |
| `file_url` | `String? @db.VarChar(255)` | Yes | URL ถาวร (presigned URL ออกตามความต้องการ ไม่เก็บ) |
| `doc_version` | `Int` | No | Default `0`; สงวนไว้สำหรับ versioning ในอนาคต |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([s3_token, deleted_at], map: "attachment_s3_token_u")` + index บน `[s3_token]` **ไม่มี FK ออก** — referential integrity ไปยังเอกสารธุรกรรมอยู่ใน `attachments` JSONB ของเอกสาร

### 5.2 `attachments` JSONB ต่อเอกสาร

ทุกตารางธุรกรรมที่รองรับ attachment (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) พกพา:

```jsonc
"attachments": [
  { "fileToken": "S3_UUID", "fileName": "vendor-invoice.pdf",
    "fileSize": 102400, "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z" }
]
```

`fileToken` ตรงกับ `tb_attachment.s3_token` Endpoint list query `FILE_SERVICE` (source of truth) ไม่ใช่ `tb_attachment` โดยตรง

### 5.3 `DocumentFile` API projection

`fileToken` (อาจพา prefix `<buCode>/` — ตัดออกก่อน delete) &nbsp;·&nbsp; `objectName` &nbsp;·&nbsp; `originalName` &nbsp;·&nbsp; `size` &nbsp;·&nbsp; `contentType` (ขับเคลื่อน filter ประเภท) &nbsp;·&nbsp; `lastModified`

## 6. กฎทางธุรกิจ

- **ขีดจำกัด upload 10 MB** บังคับทั้ง client และ server
- **MIME allow-list** บน picker + sniffing ฝั่ง server
- **Scope ตาม BU** ทุก endpoint ภายใต้ `/api/:bu_code/documents/*`; storage partition ตาม `bu_code`
- **Presigned URL** สำหรับ download / share — ห้าม embed credentials ถาวร
- **AppId guards** `documents.upload`, `documents.list`, `documents.get`, `documents.download`, `documents.info`, `documents.presignedUrl`, `documents.delete` Non-admin = list / get / download เท่านั้น
- **Hard delete** Storage ถูกลบ, ตั้ง `tb_attachment.deleted_at`, array ต่อเอกสาร *ไม่* cascade
- **Audit logging** ผ่าน `EnrichAuditUsers` (upload, delete; presigned-URL โดยเฉพาะ *อนุมาน — ต้องตรวจสอบ*)
- **ไม่มี versioning แบบ in-place** — overwrite ผ่าน delete + re-upload

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) / [store-requisition](/th/inventory/store-requisition) / [inventory-adjustment](/th/inventory/inventory-adjustment) / [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) — พกพา `attachments` JSONB
- [master-data/vendor](/th/inventory/master-data/vendor) / [product](/th/inventory/product) — vendor และ product master record พกพา array `attachments` ของตัวเอง
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — นโยบายและกฎการมองเห็น attachment ข้ามโมดูล
- [reporting-audit/report](/th/inventory/reporting-audit/report) — artefact รายงานที่สร้างขึ้นมาที่นี่ผ่านกลไก `fileToken` เดียวกัน
- [system-config/workflow](/th/inventory/system-config/workflow) — comment ของเวิร์กโฟลว์ embed array `attachments` สำหรับไฟล์หลักฐาน
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — entry audit ของ upload / delete / presigned-URL

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4427-4449); คอลัมน์ `attachments` JSONB ต่อเอกสารกระจายอยู่
- **Backend controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts`
- **Backend service:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.service.ts` — forward ไปยัง `FILE_SERVICE` ผ่าน microservice command `files.*`
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/document/page.tsx` และ `_components/document-component.tsx`
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-document.ts` — `useDocument`, `useUploadDocument`, `useDeleteDocument`
- **Frontend type:** `../carmen-inventory-frontend-react/types/document.ts` — `DocumentFile`
