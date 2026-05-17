---
title: Running Code
description: การตั้งค่า generator เลขที่เอกสาร — prefix, date token และรูปแบบ running counter ต่อประเภทเอกสาร (PR, PO, GRN, SR ฯลฯ)
published: true
date: 2026-05-17T07:28:28.000Z
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **เจ้าของ:** Sysadmin &nbsp;·&nbsp; **ตาราง:** `tb_config_running_code` &nbsp;·&nbsp; **ใช้โดย:** บริการ numbering ตอน document create ทุกครั้ง &nbsp;·&nbsp; กฎ document-numbering — `PR202605-00001` ฯลฯ

![Running Code screen](/assets/screenshots/system-config/running-code.png)

## 1. คืออะไรและใครใช้

Running code คือ **กฎ document-numbering** สำหรับทุกประเภทเอกสารธุรกรรม Row นิยาม prefix, date token แบบ optional และ counter ที่ pad ด้วย zero — ประกอบเป็น `format` string — ซึ่งบริการ numbering consume ตอนสร้างเอกสารเพื่อผลิต reference ที่อ่านได้เช่น `PR202605-00001`

ระบบ key ด้วย `type` (หนึ่ง row ต่อประเภทเอกสาร — `PR`, `PO`, `GRN`, `SR`, `IA` ฯลฯ) โดย pattern ทั้งหมดถูกจับใน คอลัมน์ `config` JSONB การเก็บ pattern เป็นข้อมูลทำให้ property เปลี่ยน `PR-YYYYMM-NNNN` เป็น `REQ-2026-NNNNN` โดยไม่ต้อง deploy code

**บำรุงรักษาโดย** Sysadmin **อ่านโดย** บริการ numbering ทุกครั้งที่มีเอกสารใหม่

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปลี่ยน pattern ของประเภทเอกสาร | System Config → Running Code → แก้ row | Inline segment editor + preview |
| เพิ่ม running code สำหรับ doc type ใหม่ | System Config → Running Code → New | เลือก `type` (เช่น `IA`), นิยาม segments |
| ขยาย counter (เช่น 4→5 หลัก) | แก้ความกว้าง `C` segment | มีผลตอน mint ครั้งถัดไป; reference ประวัติศาสตร์ไม่เปลี่ยน |
| Preview เลขถัดไป 3 ตัว | ฟิลด์ preview บน row | ตรวจสอบ pattern ก่อนบันทึก |
| ปลดระวางประเภทเอกสาร | Soft-delete row | เฉพาะประเภทที่ปลดระวางและไม่อยู่ในการใช้งานปัจจุบัน |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate type" | Row ที่มีอยู่ที่ไม่ถูก delete | แก้ row ที่มีอยู่แทน |
| Counter รีเซ็ตโดยไม่คาดคิด | Dated segment เปลี่ยน | Counter scope โดย `type + dated-segment` — การเพิ่ม `yyyyMM` รีเซ็ตรายเดือน |
| Format placeholder ขาดหาย | `format` อ้างอิง segment ที่ไม่มีการนิยาม | เพิ่ม segment หรือลบ placeholder |
| Document number collision | Bug การ persist counter หรือการแก้ด้วยมือ | รีเซ็ต counter ของบริการ numbering; ตรวจสอบ |
| ไม่สามารถ delete | ประเภทเอกสารใช้งานอยู่ | Soft-delete เท่านั้นหลังการปลดระวาง |

## 4. กรณีพิเศษ

- **Counter scope** Implicit — scope โดย `type + dated-segment` หากไม่มี dated segment counter จะ global ต่อ type
- **การ persist counter** เป็น state ของบริการ (advisory lock / sequence) ไม่ใช่ตารางนี้ — เอนทิตีนี้นิยาม *pattern* เท่านั้น
- **การเปลี่ยน pattern กลางงวด** มีผลตอน mint ครั้งถัดไป; reference ที่มีอยู่ render ตามที่เก็บ
- **Format ต้องอ้างอิงอย่างน้อยหนึ่ง segment** — segment ที่ไม่ได้อ้างอิงอนุญาต แต่ warn ใน UI

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_config_running_code`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `type` | `String? @db.VarChar(255)` | Yes | ตัวจำแนกประเภทเอกสาร (`PR`, `PO`, `GRN`, `SR`, `IA`, …) จำเป็นโดยพฤตินัยจากความเป็นหนึ่งเดียว |
| `config` | `Json? @db.JsonB` | Yes | นิยาม pattern Default `{}` |
| `note` | `String? @db.VarChar` | Yes | Free-text note |
| `info` | `Json? @db.JsonB` | Yes | Metadata อิสระ |
| `doc_version` | `Int` | No | Optimistic-concurrency token |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([type, deleted_at])` Index บน `[type]` Reverse relation ไปยัง `tb_config_running_code_comment`

### 5.2 Shape `config` JSONB

สังเกตใน seed data:

```
{
  "A": "PR",                  // segment A: static prefix
  "B": "date('yyyyMM')",      // segment B: dated token, evaluate ตอน mint
  "C": "running(5, '0')",     // segment C: running counter, 5 หลัก, zero-padded
  "format": "{A}{B}{C}"       // template assembly
}
```

**Tokens:** `Static` (literal string), `date('<pattern>')` (date-fns-style), `running(<width>, '<pad>')` (sequence zero-padded; scope = ต่อ `type` + dated segment), `format` (template ที่มี placeholder `{A}`, `{B}`, `{C}` + separator)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `type` unique ในกลุ่มที่ไม่ถูก delete — หนึ่ง pattern ต่อ doc type
- **Counter scope** Implicit ต่อ `type + dated-segment`; global ต่อ type หากไม่มี dated segment
- **การ persist counter** State ของบริการ ไม่ใช่ตารางนี้
- **Format validation** ต้องอ้างอิงอย่างน้อยหนึ่ง segment; segment ที่ไม่ได้อ้างอิงอนุญาตแต่ warn
- **การเปลี่ยน pattern** มีผลตอน mint ครั้งถัดไป; reference ประวัติศาสตร์ไม่เปลี่ยน
- **การ์ดการลบ** ประเภทที่ active ไม่สามารถ delete; soft-delete เฉพาะประเภทที่ปลดระวาง

## 7. การอ้างอิงข้าม

- [[purchase-request]] — `pr_no`
- [[purchase-order]] — `po_no`
- [[good-receive-note]] — เลขที่อ้างอิง GRN
- [[store-requisition]] — เลขที่อ้างอิง SR
- [[inventory-adjustment]] — เลขที่อ้างอิง IA / SI / SO
- [[physical-count]], [[spot-check]] — การกำหนดเลขเอกสาร count
- [[vendor-pricelist]] — เลขที่อ้างอิง pricelist

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_config_running_code` (lines ~4493-4512)
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/running-code/`
