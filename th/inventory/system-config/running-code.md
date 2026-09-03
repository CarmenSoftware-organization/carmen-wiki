---
title: Running Code
description: การตั้งค่า generator เลขที่เอกสาร — prefix, date token และรูปแบบ running counter ต่อประเภทเอกสาร (PR, PO, GRN, SR ฯลฯ) หน้าจอ admin จริงคือ dialog ที่มีฟิลด์ type + textarea JSON ดิบ ไม่ใช่ segment editor พร้อม preview สด
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **เจ้าของ:** Sysadmin &nbsp;·&nbsp; **ตาราง:** `tb_config_running_code` &nbsp;·&nbsp; **ใช้โดย:** บริการ numbering ตอน document create ทุกครั้ง &nbsp;·&nbsp; กฎ document-numbering — `PR202605-00001` ฯลฯ &nbsp;·&nbsp; **หน้าจอ admin แก้ `config` JSONB เป็น raw text — ไม่มี editor ต่อ segment (prefix/date/counter) หรือ preview เลขแบบ live เลย**

![Running Code screen](/screenshots/system-config/running-code.png)

## สถานะการ implement (ตรวจสอบ 2026-07-16)

Dialog แก้ไข `/system-admin/running-code` (`running-code-dialog.tsx` + `running-code-form-schema.ts`) คือ **ฟิลด์ text ธรรมดาสำหรับ type + textarea JSON ดิบ** สำหรับ `config` (สูงสุด 256 ตัวอักษร) พร้อม button "Format" ตัวเดียวที่แค่ pretty-print JSON (`JSON.stringify(parsed, null, 2)`) — ไม่ validate รูปร่างของ pattern เกินกว่า "นี่คือ JSON ที่ valid หรือไม่" ไม่มี editor ความกว้างต่อ segment (`A`/`B`/`C`) ไม่มีการลากจัดเรียง และไม่มีฟิลด์ "preview เลขถัดไป 3 ตัว" แบบ live ที่ไหนใน component เลย `type` เป็นฟิลด์ free-text (ไม่ใช่ picker ที่จำกัดตาม enum คงที่) และกลายเป็น read-only ทันทีที่มี row อยู่แล้ว (`disabled={isPending || isEdit}`) ภาษา pattern ของ `config` JSONB ที่อยู่เบื้องหลัง (`date('yyyyMM')`, `running(5,'0')`, template `format`) **มีจริงและถูก consume ใช้งานอยู่จริง** โดย `GenerateCode`/`getPattern` ใน `common/helpers/running-code.helper.ts` (ยืนยันผ่าน unit test ของไฟล์นั้นเอง) — มีแค่คำอธิบาย UX ของหน้าจอ admin ด้านล่างที่ถูกแก้ไข; เอกสารแบบจำลองข้อมูลของ pattern ใน §5 ไม่เปลี่ยนแปลงและถูกต้อง

## 1. คืออะไรและใครใช้

Running code คือ **กฎ document-numbering** สำหรับทุกประเภทเอกสารธุรกรรม Row นิยาม prefix, date token แบบ optional และ counter ที่ pad ด้วย zero — ประกอบเป็น `format` string — ซึ่งบริการ numbering consume ตอนสร้างเอกสารเพื่อผลิต reference ที่อ่านได้เช่น `PR202605-00001` Pattern นี้เขียนเป็น JSON text ดิบ ไม่ใช่ผ่าน segment builder แบบมีโครงสร้าง (ดูสถานะการ implement)

ระบบ key ด้วย `type` (หนึ่ง row ต่อประเภทเอกสาร — `PR`, `PO`, `GRN`, `SR`, `IA` ฯลฯ) โดย pattern ทั้งหมดถูกจับใน คอลัมน์ `config` JSONB การเก็บ pattern เป็นข้อมูลทำให้ property เปลี่ยน `PR-YYYYMM-NNNN` เป็น `REQ-2026-NNNNN` โดยไม่ต้อง deploy code — แต่การทำวันนี้หมายถึงการแก้ JSON ด้วยมือ ไม่ใช่กรอกฟอร์ม segment

**บำรุงรักษาโดย** Sysadmin **อ่านโดย** บริการ numbering ทุกครั้งที่มีเอกสารใหม่

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปลี่ยน pattern ของประเภทเอกสาร | System Config → Running Code → แก้ row → textarea **Config** | แก้ JSON ดิบ; ใช้ **Format** เพื่อ pretty-print เท่านั้น ไม่ใช่ validate ความหมายของ pattern |
| เพิ่ม running code สำหรับ doc type ใหม่ | System Config → Running Code → New | ฟิลด์ `type` แบบ free-text (ไม่ใช่ picker) + `config` JSON ดิบ |
| ขยาย counter (เช่น 4→5 หลัก) | แก้ค่า `running(<width>, '0')` ของ segment `C` ด้วยมือใน textarea JSON | มีผลตอน mint ครั้งถัดไป; reference ประวัติศาสตร์ไม่เปลี่ยน |
| Preview เลขถัดไป 3 ตัว | ~~ฟิลด์ preview บน row~~ | **ไม่มีฟิลด์นี้อยู่จริง** — ไม่มี preview แบบ live ที่ไหนใน dialog เลย |
| ปลดระวางประเภทเอกสาร | Soft-delete row | เฉพาะประเภทที่ปลดระวางและไม่อยู่ในการใช้งานปัจจุบัน |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate type" | Row ที่มีอยู่ที่ไม่ถูก delete | แก้ row ที่มีอยู่แทน |
| Textarea reject ค่าตอนบันทึก | `config` ไม่ใช่ JSON ที่ valid | แก้ syntax; ฟอร์มตรวจสอบแค่ `JSON.parse` สำเร็จ ไม่ใช่ว่ารูปร่างเป็น pattern ที่ใช้งานได้ |
| Counter รีเซ็ตโดยไม่คาดคิด | Dated segment เปลี่ยน | Counter scope โดย `type + dated-segment` — การเพิ่ม `yyyyMM` รีเซ็ตรายเดือน |
| Format placeholder ขาดหาย | `format` อ้างอิง segment ที่ไม่มีการนิยาม | เพิ่ม segment หรือลบ placeholder — ฟอร์มไม่จับสิ่งนี้ จะปรากฏก็ต่อเมื่อสร้างเอกสารจริงเท่านั้น |
| Document number collision | Bug การ persist counter หรือการแก้ด้วยมือ | รีเซ็ต counter ของบริการ numbering; ตรวจสอบ |
| ไม่สามารถ delete | ประเภทเอกสารใช้งานอยู่ | Soft-delete เท่านั้นหลังการปลดระวาง |

## 4. กรณีพิเศษ

- **ไม่มี editor แบบมีโครงสร้างหรือ preview** ยืนยันว่า dialog คือ textarea JSON เปล่าพร้อม button "Format" ที่ทำแค่ format; ความหมายของ *pattern* ที่ผิดรูป (เช่น string `format` อ้างอิง segment ที่ไม่ได้นิยาม) ผ่าน validation ฝั่ง client และจะ fail ก็ต่อเมื่อมีการสร้างเอกสารจริงเท่านั้น
- **Counter scope** Implicit — scope โดย `type + dated-segment` หากไม่มี dated segment counter จะ global ต่อ type
- **การ persist counter** เป็น state ของบริการ (advisory lock / sequence) ไม่ใช่ตารางนี้ — เอนทิตีนี้นิยาม *pattern* เท่านั้น
- **การเปลี่ยน pattern กลางงวด** มีผลตอน mint ครั้งถัดไป; reference ที่มีอยู่ render ตามที่เก็บ
- **Format ต้องอ้างอิงอย่างน้อยหนึ่ง segment** — segment ที่ไม่ได้อ้างอิงอนุญาต; ไม่พบ UI warning สำหรับกรณีนี้ (ต่างจากเวอร์ชันก่อนหน้าของหน้านี้)

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
- **Format validation** ต้องอ้างอิงอย่างน้อยหนึ่ง segment เพื่อใช้งานได้ตอน mint; ฟอร์ม admin ไม่ตรวจสอบสิ่งนี้ — ตรวจแค่ `config` parse เป็น JSON ได้
- **การเปลี่ยน pattern** มีผลตอน mint ครั้งถัดไป; reference ประวัติศาสตร์ไม่เปลี่ยน
- **การ์ดการลบ** ประเภทที่ active ไม่สามารถ delete; soft-delete เฉพาะประเภทที่ปลดระวาง

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) — `pr_no`
- [purchase-order](/th/inventory/purchase-order) — `po_no`
- [good-receive-note](/th/inventory/good-receive-note) — เลขที่อ้างอิง GRN
- [store-requisition](/th/inventory/store-requisition) — เลขที่อ้างอิง SR
- [inventory-adjustment](/th/inventory/inventory-adjustment) — เลขที่อ้างอิง IA / SI / SO
- [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) — การกำหนดเลขเอกสาร count
- [vendor-pricelist](/th/inventory/vendor-pricelist) — เลขที่อ้างอิง pricelist

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_config_running_code` (lines ~4864-4883)
- **Backend pattern logic:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/helpers/running-code.helper.ts` — `GenerateCode`, `getPattern` (ยืนยันผ่าน `running-code.helper.spec.ts`, `common.helper.spec.ts`)
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/running-code/` — `running-code-component.tsx` (list), `running-code-dialog.tsx` (สร้าง/แก้ไข JSON ดิบ), `running-code-form-schema.ts`
