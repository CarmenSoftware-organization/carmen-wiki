---
title: ไฟล์แนบ (Attachment)
description: เอนทิตีจัดเก็บไฟล์แบบ generic — metadata ของไบนารีที่อยู่บน S3 พร้อมการเชื่อมโยงแบบ polymorphic ไปยังเอกสารธุรกรรมใด ๆ
published: true
date: 2026-05-19T23:55:00.000Z
tags: reporting-audit, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ไฟล์แนบ (Attachment)

> **At a Glance**
> **เจ้าของ:** โมดูลเจ้าของ (PR, PO, GRN, …) &nbsp;·&nbsp; **ตาราง:** `tb_attachment` &nbsp;·&nbsp; **ใช้โดย:** ทุกโมดูลที่มีการอัปโหลดไฟล์ &nbsp;·&nbsp; แคตตาล็อก metadata ของไฟล์แบบ generic — เก็บบน S3 เชื่อมโยงแบบ polymorphic จากโมดูลเจ้าของ

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี attachment คือ **แคตตาล็อก metadata ของไบนารีที่ใช้ร่วมกัน** สำหรับทุกโมดูลที่จัดเก็บไฟล์ ใบเสนอราคาบน PR, การยืนยันจากผู้ขายบน PO, docket การส่งของที่เซ็นแล้วบน GRN, ใบนับสินค้าบน physical count, รูปภาพบน spot check — ทั้งหมดมาเก็บที่ `tb_attachment` และเชื่อมกลับผ่าน polymorphism ฝั่งแอปพลิเคชัน (ไม่มี FK ใน schema จากตารางนี้) แต่ละแถว carry token + folder ของ S3, metadata ไฟล์ต้นฉบับ (ชื่อ, นามสกุล, ประเภท, ขนาด), URL สาธารณะ/มีลายเซ็น, `info` แบบอิสระ และ `doc_version` แบบ integer สำหรับเอกสารที่ render ใหม่ (เช่น re-render PDF)

เอนทิตีนี้เป็น generic โดยตั้งใจ — ไม่มี discriminator `document_type` ข้อตกลงคือตาราง **เจ้าของ** เก็บคอลัมน์ FK ไปยังแถว attachment

**ดูแลโดย** flow การอัปโหลดของโมดูลเจ้าของ **อ่านโดย** หน้ารายละเอียดของโมดูลเจ้าของ

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| แนบไฟล์กับเอกสาร | รายละเอียดเอกสาร → tab **Attachments** → Upload | เขียนแถว `tb_attachment` + FK บนตารางเจ้าของ |
| ดาวน์โหลด attachment | คลิกชื่อไฟล์ | resolve ผ่าน S3 service อีกครั้ง (URL อาจเป็นแบบ signed/อายุสั้น) |
| ลบ attachment | tab Attachments → Delete | soft-delete แถว; S3 blob ถูก GC เก็บไป |
| Re-render PDF เอกสาร | action print ของโมดูลเจ้าของ | เพิ่ม `doc_version`; เวอร์ชันเก่าคงไว้สำหรับ audit |
| แทนที่ไฟล์ที่อัปโหลด | soft-delete เก่า + อัปโหลดใหม่ | `s3_token` unique ในแถวที่ไม่ถูกลบ |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| "Duplicate s3_token" | มีแถวที่ไม่ถูกลบอยู่แล้ว | soft-delete หรือใช้ token อื่น |
| file_url เสีย | URL signed หมดอายุ | resolve ผ่าน S3 service อีกครั้งแทนการ cache |
| ไฟล์หายใน S3 แต่แถวยังอยู่ | GC ไม่ตรงกัน / ถูกลบจากภายนอก | orphan; ถูก reap โดย retention job |
| MIME ไม่ตรง | `file_type` มาจาก client ไม่ได้ตรวจสอบใหม่ | อย่าพึ่งพา `file_type`/`file_ext` เพื่อความปลอดภัย |

## 4. กรณีพิเศษ

- **Semantic ของ soft-delete** `deleted_at` ซ่อนจาก UI แต่ไม่ลบ object ของ S3 — GC เก็บไปหลัง retention
- **ไม่มี polymorphic FK ที่บังคับใช้** การลบแถวเจ้าของอาจทำให้แถว attachment กลายเป็น orphan; GC เดียวกันจัดการ cleanup
- **การเพิ่ม `doc_version`** โมดูลเจ้าของเพิ่มเมื่อ re-render (เช่น PDF ของ PR หลัง stage advance); เวอร์ชันเก่ายังดาวน์โหลดได้จาก activity history
- **ความน่าเชื่อถือของ MIME / extension** ทั้งสองมาจาก client; โค้ดที่อยู่ปลายน้ำต้องไม่พึ่งพาเพื่อความปลอดภัย

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_attachment`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `s3_token` | `String? @db.VarChar(255)` | Yes | S3 object key แบบ opaque Unique ในแถวที่ไม่ถูกลบ |
| `s3_folder` | `String? @db.VarChar(255)` | Yes | logical folder / bucket prefix |
| `file_name` | `String? @db.VarChar(255)` | Yes | ชื่อไฟล์ต้นฉบับ |
| `file_ext` | `String? @db.VarChar(255)` | Yes | นามสกุล (`pdf`, `xlsx`, `jpg`, …) |
| `file_type` | `String? @db.VarChar(255)` | Yes | MIME type |
| `file_size` | `BigInt? @db.BigInt` | Yes | ไบต์ |
| `file_url` | `String? @db.VarChar(255)` | Yes | URL ที่ resolve แล้ว (signed หรือ public) |
| `info` | `Json? @db.Json` | Yes | metadata แบบอิสระ |
| `doc_version` | `Int @db.Integer` | No | Default `0` เพิ่มเมื่อ re-render |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([s3_token, deleted_at])` map `attachment_s3_token_u` `@@index([s3_token])` ไม่มีคอลัมน์ FK — เชื่อมโยงที่ตารางเจ้าของ

## 6. กติกาทางธุรกิจ

- **ความ unique** `s3_token` unique ในแถวที่ไม่ถูกลบ; constraint รวม `deleted_at` ทำให้สามารถ re-upload หลัง soft-delete ได้
- **Semantic ของ soft-delete** แถวถูกซ่อน; S3 blob ถูก reap โดย retention GC
- **การเพิ่ม `doc_version`** โมดูลเจ้าของเพิ่มเมื่อ re-render; เวอร์ชันเก่าคงไว้
- **ไม่บังคับ FK** orphan จัดการโดย retention job
- **Lifecycle ของ URL** resolve ผ่าน S3 service อีกครั้ง; อย่า cache `file_url` ข้าม session
- **ความน่าเชื่อถือของ MIME / extension** มาจาก client ไม่ได้ verify ที่ server — อย่าใช้สำหรับการตัดสินใจด้านความปลอดภัย

## 7. ความเชื่อมโยงข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note) — ใบเสนอราคา, การยืนยัน, docket
- [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) — เอกสารประกอบและหลักฐาน
- [store-requisition](/th/inventory/store-requisition), [vendor-pricelist](/th/inventory/vendor-pricelist), [recipe](/th/inventory/recipe), [product](/th/inventory/product) — attachment เฉพาะโมดูล
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — `upload` / `download` ถูก log ด้วย `entity_type = 'attachment'`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4427-4449)
- **Frontend:** ฝังในหน้ารายละเอียดของแต่ละโมดูล (เช่น `.../purchase-request/[id]/`) shared `attachment` service จัดการการอัปโหลด blob
