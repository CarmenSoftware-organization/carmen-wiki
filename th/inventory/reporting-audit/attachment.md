---
title: ไฟล์แนบ (Attachment)
description: registry ของ metadata ไฟล์ที่ใช้โดยทุกโมดูลที่มีการอัปโหลดไฟล์ — tb_file_tag เก็บบน MinIO อยู่ในฐานข้อมูล file-service แยกต่างหาก ให้บริการโดย microservice micro-file ตาราง tb_attachment ใน tenant schema ไม่มีการอ้างอิงจากโค้ดเลยและถือว่าตายแล้ว
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ไฟล์แนบ (Attachment)

> **At a Glance**
> **เจ้าของ:** flow การอัปโหลดของโมดูลเจ้าของ &nbsp;·&nbsp; **ตาราง:** `tb_file_tag` — อยู่ใน **ฐานข้อมูล `prisma-shared-schema-file` (`CARMEN_FILE`) แยกต่างหาก** ไม่ใช่ tenant schema &nbsp;·&nbsp; **การจัดเก็บ:** MinIO &nbsp;·&nbsp; **ใช้โดย:** ทุกโมดูลที่มีการอัปโหลดไฟล์ &nbsp;·&nbsp; ตาราง `tb_attachment` ใน tenant schema ตายแล้ว — ไม่มีการอ้างอิงจากโค้ดนอกเหนือจาก schema เลย

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

หน้านี้ฉบับก่อนหน้าบันทึก `tb_attachment` (tenant schema) ว่าเป็นแคตตาล็อกไฟล์-metadata ที่ใช้ร่วมกันและใช้งานจริง เก็บบน S3 ด้วยรูปแบบ `s3_token`/`s3_folder` และมี `doc_version` เป็น "ตัวนับการ re-render... เพิ่มเมื่อ re-render; เวอร์ชันเก่าคงไว้สำหรับ audit" การค้นหาทั่ว `carmen-turborepo-backend-v2/apps` พบว่า **ไม่มีการอ้างอิง `tb_attachment` เลยนอกเหนือจากการประกาศ Prisma model ของมันเอง** — ไม่มี service, controller, repository หรือ DTO ใดอ่านหรือเขียนตารางนี้เลย `tb_attachment.doc_version` เองก็ไม่เคยถูกเพิ่มค่าหรืออ่านโดยโค้ดใด ๆ เช่นกัน — เป็น schema เฉย ๆ ไม่ใช่ตัวนับการ re-render ที่ทำงานจริง ผลนี้สอดคล้องกับสิ่งที่ยืนยันไว้แล้วใน [system-config/document](/th/inventory/system-config/document)

เส้นทางการจัดเก็บไฟล์ที่แท้จริงคือ microservice **`micro-file`** (`micro-file/src/files/files.service.ts`) ซึ่งเขียนไปที่ **MinIO** object storage และไปที่ **`tb_file_tag`** — ตารางในฐานข้อมูล `@repo/prisma-shared-schema-file` แยกต่างหากทั้งหมด (schema `CARMEN_FILE`) ไม่ใช่ tenant หรือ platform schema หน้านี้ถูกแก้ไขให้อธิบาย mechanism นี้ ดู [system-config/document](/th/inventory/system-config/document) สำหรับ UI walkthrough แบบเต็มของหน้าจอ admin (`/system-admin/document`) — หน้านี้เน้นที่เอนทิตีในแง่ที่ถูกโมดูลอื่นใช้งาน

## 1. ภาพรวมและผู้ใช้งาน

Registry ไฟล์ที่แท้จริงคือ `tb_file_tag` หนึ่งแถวต่อหนึ่ง MinIO object ที่อัปโหลด เชื่อมกลับไปยังเอกสารเจ้าของผ่าน **JSONB array ต่อเอกสาร** แทนที่จะเป็น FK ใน schema ใบเสนอราคาบน PR, การยืนยันจากผู้ขายบน PO, docket การส่งของที่เซ็นแล้วบน GRN, ใบนับสินค้าบน physical count, รูปภาพบน spot check — ทุกตารางธุรกรรมที่รองรับ attachment (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) มีคอลัมน์ JSONB `attachments` ที่แต่ละรายการอ้างอิง `fileToken` — ไม่ใช่ `tb_attachment.s3_token`

แต่ละแถวของ `tb_file_tag` เก็บ MinIO object key (`object_name`), metadata ไฟล์ต้นฉบับ (`original_name`, `content_type`, `size`) และ tag แบบมีโครงสร้าง/อิสระ (`reference_type`/`reference_id`/`reference_no`, `tags` JSONB) สำหรับการค้นหา **ไม่มีคอลัมน์ `doc_version`/versioning สำหรับการ re-render บน `tb_file_tag`** — การอัปโหลด PDF ของเอกสารใหม่คือการอัปโหลดครั้งใหม่ธรรมดา ไม่ใช่ revision ที่มีเวอร์ชันของแถวเดิม

**ดูแลโดย** flow การอัปโหลดของโมดูลเจ้าของ ผ่านคำสั่งของ `micro-file` (`files.upload` / `files.get` / `files.info` / `files.find-all` / `files.delete` / `files.presigned-url` / `files.update-tags`) **อ่านโดย** หน้ารายละเอียดของโมดูลเจ้าของ ซึ่ง resolve แต่ละ `fileToken` กลับเป็น MinIO URL ใหม่ที่มีเวลาจำกัด

### 1.1 การดึงไฟล์ — URL ที่บันทึกไว้ไม่เคยถูกไว้ใจ

**เมื่ออ่านข้อมูล URL จะถูก resolve ใหม่ ไม่ใช่เล่นซ้ำจาก storage** สำหรับ attachment ทุกรายการ gateway จะ resolve **presigned MinIO URL** ใหม่ (TTL 1 ชั่วโมง) จาก `fileToken` ภายใน หากการ resolve ล้มเหลวจะ fallback ไปที่เส้นทาง gateway สัมพัทธ์ `/api/{bu_code}/documents/{fileToken}/download` จากนั้น `fileToken` ภายในจะถูก **ลบออก** จาก response ใน projection บางแบบ (เช่น comment attachment) — ผู้เรียกเห็นเพียง `fileUrl` ที่ resolve แล้วเท่านั้น

รูปร่างของ attachment ที่เปิดเผยใน comment responses (เป็น response DTO ที่แคบกว่าและใช้งานจริง — ต่างจาก projection `DocumentFile` แบบเต็มใน [system-config/document](/th/inventory/system-config/document) §5.4):

| ฟิลด์ | ประเภท | หมายเหตุ |
|---|---|---|
| `fileName` | string | ชื่อไฟล์ต้นฉบับ |
| `fileUrl` | string (optional) | Presigned URL หรือ fallback route สัมพัทธ์; เติมใหม่ทุก request |
| `contentType` | string | MIME type (`image/jpeg`, `image/png`, `image/webp`, `image/gif`, `application/pdf`) |
| `size` | number (optional) | ไบต์ |

Comment responses ยังจะ **ลบฟิลด์ผู้แต่งภายใน** (`user_id`, `username`, `firstname`, `middlename`, `lastname`) ออกด้วย — ผู้แต่งที่ resolve แล้วจะเปิดเผยผ่าน object `audit` ที่มีข้อมูลเพิ่มเติมแทน

> **หมายเหตุ — คอลัมน์ `doc_version` ที่ยืนยันแล้วว่าตายแล้ว** `tb_attachment.doc_version` ใน tenant schema เป็นฟิลด์ legacy ที่ไม่เคยถูกอ้างอิง — ไม่ใช่ตัวนับการ re-render และไม่ใช่แนวคิดเดียวกับ `doc_version` สำหรับ optimistic concurrency ที่เอกสารธุรกรรมใช้ ดู [system-config/doc-version](/th/inventory/system-config/doc-version) สำหรับ framing ที่ถูกต้องของฟิลด์นั้น

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| แนบไฟล์กับเอกสาร | รายละเอียดเอกสาร → tab **Attachments** → Upload | เขียนแถว `tb_file_tag` + เพิ่มเข้า JSONB `attachments` ของตารางเจ้าของ |
| ดาวน์โหลด attachment | คลิกชื่อไฟล์ | Presigned MinIO URL, resolve ใหม่ทุก request (TTL 1 ชั่วโมง) |
| ลบ attachment | tab Attachments → Delete | ลบ MinIO object (กู้คืนไม่ได้) และ soft-delete แถว `tb_file_tag`; รายการใน JSONB `attachments` ของเอกสารเจ้าของ **ไม่ถูก** ทำความสะอาด — ดูกรณีพิเศษ |
| ยืนยันแล้วว่าไม่มีการตรวจสอบขนาด/MIME ที่ server | `uploadFile()` ของ `files.service.ts` | ดู [system-config/document](/th/inventory/system-config/document) §สถานะการทำงานจริง — ขีดจำกัดขนาด/MIME ที่ client ประกาศเป็นเพียงฝั่ง frontend เท่านั้น |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ลิงก์ไฟล์เสีย/หมดอายุ | TTL ของ presigned URL หมด | เปิดเอกสารใหม่ — URL ถูก resolve ใหม่ทุกครั้งที่ดึง ไม่เคยถูก cache ที่ server |
| Attachment "หายไป" บนเอกสาร | แถว `tb_file_tag` ถูกลบออกจาก registry ทั้งที่ `fileToken` ยังถูกอ้างอิงอยู่ | Token ที่ค้างไม่ถูกทำความสะอาดอัตโนมัติ; อัปโหลดและแนบใหม่ |
| MIME ไม่ตรง | `content_type` มาจาก request การอัปโหลดตรง ๆ ไม่ได้ตรวจสอบใหม่ที่ server | อย่าพึ่งพา `content_type` เพื่อการตัดสินใจด้านความปลอดภัย |

## 4. กรณีพิเศษ

- **การลบเป็น hard บน storage, soft บนแถว registry และไม่เคย cascade** `deleteFile()` ลบ MinIO object ทันที (กู้คืนไม่ได้) และตั้ง `tb_file_tag.deleted_at` แบบ best-effort JSONB `attachments` ของเอกสารเจ้าของ **ไม่ถูก** อัปเดต — token ของไฟล์ที่ถูกลบจะแสดงเป็น "missing" บนเอกสารใดก็ตามที่ยังอ้างอิงอยู่
- **ไม่มี FK แบบ polymorphic — โดยการออกแบบ** การเชื่อมโยงเป็นทิศทางเดียว: JSONB `attachments` ของตารางเจ้าของเก็บ `fileToken` ที่ชี้ไปยัง `tb_file_tag`; ไม่มี index ย้อนกลับบน `tb_file_tag` กลับไปยังทุกแถวเจ้าของ
- **ความน่าเชื่อถือของ MIME / ขนาด** ทั้งสองมาจาก request การอัปโหลดและไม่ได้ตรวจสอบใหม่ที่ server — อย่าพึ่งพาเพื่อความปลอดภัย
- **ฐานข้อมูลแยกต่างหาก** `tb_file_tag` อยู่ใน Postgres database/schema ที่แยกต่างหาก (`CARMEN_FILE`) จากทั้ง tenant และ platform schema — join ข้าม schema ที่ระดับ SQL ทำไม่ได้; การ resolve ต้องผ่าน API ของ service `micro-file` เสมอ

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: **ฐานข้อมูล `prisma-shared-schema-file` แยกต่างหาก** — ไม่ใช่ tenant schema

### 5.1 `tb_file_tag` (registry metadata ที่แท้จริง)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `bu_code` | `String @db.VarChar` | No | Business unit เจ้าของ |
| `file_token` | `String @db.VarChar` (unique) | No | Handle มาตรฐาน รูปแบบ `<bu_code>/<uuid>` — ตรงกับ `attachments[].fileToken` ต่อเอกสาร |
| `object_name` | `String @db.VarChar` | No | MinIO object key |
| `original_name` | `String @db.VarChar` | No | ชื่อไฟล์แสดงผล |
| `content_type` | `String @db.VarChar` | No | MIME type มาจาก request การอัปโหลดตรง ๆ |
| `size` | `Int` | No | ไบต์ |
| `reference_type` / `reference_id` / `reference_no` | `String? @db.VarChar` | Yes | ฟิลด์ tag แบบมีโครงสร้างและ index — เอกสารไหนที่ไฟล์นี้เป็นของ |
| `description` | `String?` | Yes | ข้อความอิสระ |
| `tags` | `Json? @db.JsonB` | Yes | Default `{}`; แบบอิสระ, มี GIN index |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` (ไม่มี `doc_version` บน model นี้) |

**Constraints:** unique บน `file_token`; index บน `[bu_code, deleted_at]`, `[bu_code, reference_type, reference_id]`, `[bu_code, reference_no]` และ GIN index บน `tags`

### 5.2 `tb_attachment` (tenant schema — ตารางที่ตายแล้ว เก็บไว้เพื่อเปรียบเทียบ)

`id` / `s3_token` / `s3_folder` / `file_name` / `file_ext` / `file_type` / `file_size` / `file_url` / `info` / `doc_version Int @default(0)` / คอลัมน์ audit มีรูปร่างเหมือน file registry แต่ **ไม่พบการอ้างอิงจากโค้ดเลยแม้แต่ตัวเดียวทั่วทั้ง backend** อย่าถือว่านี่เป็นตารางเบื้องหลังของ attachment ในโมดูลใด ๆ

### 5.3 JSONB `attachments` ต่อเอกสาร

```jsonc
"attachments": [
  { "fileToken": "T01/019638a6-...", "fileName": "vendor-invoice.pdf",
    "fileSize": 102400, "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z" }
]
```

`fileToken` ตรงกับ `tb_file_tag.file_token` ไม่เคยเป็น `tb_attachment.s3_token`

## 6. กติกาทางธุรกิจ

- **`tb_file_tag` คือ registry ที่แท้จริง; `tb_attachment` ตายแล้ว** ยืนยันโดยการค้นหาโค้ดทั่วทั้ง repo — ไม่มี service ใดอ่านหรือเขียน `tb_attachment` เลย
- **ไม่มีการตรวจสอบขนาดหรือ MIME ที่ server** บนเส้นทางการอัปโหลดที่แท้จริง (`uploadFile()` ของ `files.service.ts`)
- **การลบเป็นการทันทีและกู้คืนไม่ได้บน MinIO** soft-delete แบบ best-effort บน `tb_file_tag` และไม่เคย cascade ไปยัง JSONB `attachments` ของเอกสารเจ้าของ
- **Lifecycle ของ URL** resolve ผ่าน file service เสมอ — อย่า cache `fileUrl` ข้าม session; presigned URL หมดอายุหลัง 1 ชั่วโมง
- **การเชื่อมโยงข้ามฐานข้อมูล** `tb_file_tag` ไม่สามารถ join กับตาราง tenant หรือ platform ได้ที่ระดับ SQL — การ resolve ต้องผ่าน API ของ service `micro-file` เสมอ

## 7. ความเชื่อมโยงข้ามโมดูล

- [system-config/document](/th/inventory/system-config/document) — หน้าอ้างอิงหลักของ mechanism นี้: หน้าจอ registry `/system-admin/document`, projection `DocumentFile` แบบเต็ม และ AppId guard
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note) — ใบเสนอราคา, การยืนยัน, docket
- [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) — เอกสารประกอบและหลักฐาน
- [store-requisition](/th/inventory/store-requisition), [vendor-pricelist](/th/inventory/vendor-pricelist), [recipe](/th/inventory/recipe), [product](/th/inventory/product) — attachment เฉพาะโมดูล
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — action `upload`/`download` ถูก log ด้วย `entity_type = 'attachment'` (ยังไม่ยืนยันเทียบกับ `tb_file_tag` โดยเฉพาะ — เส้นทางการเขียน activity ยังไม่ได้ตรวจสอบเทียบกับ file service ในรอบนี้)

## 8. แหล่งอ้างอิง

- **Prisma (file schema — registry ที่แท้จริง):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-file/prisma/schema.prisma` — `tb_file_tag` (บรรทัด ~19-49)
- **Prisma (tenant schema — ตารางที่ตายแล้ว เพื่อเปรียบเทียบ):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (บรรทัด ~4790)
- **Backend gateway (ชั้น proxy):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts` + `.service.ts` — forward ไปยัง microservice `FILE_SERVICE` ผ่านคำสั่ง TCP `files.*`
- **Backend file microservice (การจัดเก็บและ registry ที่แท้จริง):** `../carmen-turborepo-backend-v2/apps/micro-file/src/files/files.controller.ts` + `files.service.ts` — MinIO client, CRUD ของ `tb_file_tag`
