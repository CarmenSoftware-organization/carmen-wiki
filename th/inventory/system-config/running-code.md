---
title: Running Code
description: pattern เลขที่เอกสาร — prefix, date token, running counter ต่อประเภทเอกสาร (PR, PO, GRN, SR, GL-JV, …) ตั้งแต่ 2026-08-27 dialog ของ admin เป็น editor แบบทีละส่วนพร้อม preview สด; JSON ดิบเป็น fallback ที่พับไว้
published: true
date: '2026-09-23T01:30:00.000Z'
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **เจ้าของ:** Sysadmin &nbsp;·&nbsp; **ตาราง:** `tb_config_running_code` &nbsp;·&nbsp; **Route:** `/system-admin/running-code` &nbsp;·&nbsp; **Permission / licence:** `system_admin.running_code` &nbsp;·&nbsp; **ใช้โดย:** บริการ numbering ตอน document create ทุกครั้ง &nbsp;·&nbsp; กฎ document-numbering — `PR202605-00001` ฯลฯ &nbsp;·&nbsp; **dialog ของ admin เป็น editor แบบทีละส่วน (text / date / running / token) พร้อม preview สดตั้งแต่ 2026-08-27; JSON `config` ดิบยังคงไว้เป็น fallback "Advanced" ที่พับอยู่**

![Running Code screen](/screenshots/system-config/running-code.png)

## สถานะการ implement (ตรวจสอบ 2026-07-16; ตรวจสอบซ้ำ 2026-09-22)

**ข้อค้นพบเมื่อ 2026-07-16 ถูกแทนที่แล้ว** FE commit `704f1f9f` (2026-08-27, *"edit the document-number format part by part instead of typing JSON"*) แทนที่ textarea ดิบด้วย editor แบบมีโครงสร้าง:

- `running-code-config.ts` parse JSON `{ A, B, C, …, format }` ของ backend เป็นรายการ **part** ที่มีลำดับ — `text` (literal), `date` (`date('<pattern>')`), `running` (`running(<digits>, '<pad>')`), `token` (`{name}`) — และ serialise กลับ โดยตั้งตัวอักษร slot `A`, `B`, `C`… ใหม่ (`slotName()`) ทุกครั้งที่บันทึก admin ไม่เห็นตัวอักษรหรือคำว่า `format` เลย
- `running-code-config-fields.tsx` render part พร้อม control เพิ่ม/ลบ/จัดเรียง และ **preview สด** (`previewCode(parts, now)`) ของเลขถัดไป
- key ที่มีใน `config` แต่ไม่ถูกอ้างโดย `format` ถูกเก็บไว้ใน `extra` และเขียนกลับโดยไม่แตะต้อง การแก้ prefix จึงไม่ทำให้ key ที่ไม่รู้จักหายไปเงียบ ๆ
- textarea JSON ดิบยังมีอยู่ พับอยู่ใต้ **Advanced config** (`running-code-dialog.tsx:185-245`) พร้อม button pretty-print; เมื่อ `parseConfig()` คืน `null` (ไม่มี `format` หรือ `format` อ้าง slot ที่หายไป) editor แบบมีโครงสร้างจะถูกปิดพร้อมข้อความ `configUnreadable` และ textarea JSON เปิดขึ้นเพื่อซ่อมด้วยมือ
- `type` ยังเป็น input free-text ที่กลายเป็น read-only ทันทีที่มี row อยู่แล้ว (`disabled={isPending || isEdit}`, `:172`)

ภาษา pattern ที่อยู่เบื้องหลัง (`date('yyyyMM')`, `running(5,'0')`, template `format`) ไม่เปลี่ยนและยังถูก consume โดย `GenerateCode`/`getPattern` ใน `common/helpers/running-code.helper.ts` fallback ของ backend: เมื่อ BU ไม่มี row สำหรับ type หนึ่ง `getRunningPattern()` อ่าน `RUNNING_CODE_PRESET[type].config` (`apps/micro-business/src/master/running-code/const/running-code.const.ts`) — มี preset สำหรับ `PURCHASE-REQUEST`, `PURCHASE-ORDER`, `GOOD-RECEIVED-NOTE`, `CREDIT-NOTE`, `PRICE-LIST`, `STOCK-IN`, `STOCK-OUT`, `STORE-REQUISITION`, `SPOT-CHECK`, `PHYSICAL-COUNT`, `PRODUCT-CAT`, `PRODUCT-SUB-CAT`, `PRODUCT-ITEM-GROUP`, `PRODUCT` และตั้งแต่ 2026-09-15 `GL-JV` (`27f65cba1` — preset ที่ขาดหายทำให้ JV ฉบับแรกของทุก BU ล้มเหลวด้วย 500) **ไม่มี guard** สำหรับ type นอก preset: ประเภทเอกสารที่ไม่มีทั้ง row และ preset ยังคง crash ตอนสร้างเลข

## 1. คืออะไรและใครใช้

Running code คือ **กฎ document-numbering** สำหรับทุกประเภทเอกสารธุรกรรม Row นิยาม prefix, date token แบบ optional และ counter ที่ pad ด้วย zero — ประกอบเป็น `format` string — ซึ่งบริการ numbering consume ตอนสร้างเอกสารเพื่อผลิต reference ที่อ่านได้เช่น `PR202605-00001` ตั้งแต่ 2026-08-27 pattern เขียนผ่าน part editor แบบมีโครงสร้างพร้อม preview สด (ดูสถานะการ implement); JSON เป็นเพียงรายละเอียดการจัดเก็บ

ระบบ key ด้วย `type` (หนึ่ง row ต่อประเภทเอกสาร — key ของ preset ข้างต้น; สังเกตว่าการสะกดใน seed/preset คือ `PURCHASE-REQUEST`, `GOOD-RECEIVED-NOTE`, `GL-JV` ไม่ใช่ `PR`/`GRN`) โดย pattern ทั้งหมดถูกจับใน คอลัมน์ `config` JSONB การเก็บ pattern เป็นข้อมูลทำให้ property เปลี่ยน `PR-YYYYMM-NNNN` เป็น `REQ-2026-NNNNN` โดยไม่ต้อง deploy code

**บำรุงรักษาโดย** Sysadmin **อ่านโดย** บริการ numbering ทุกครั้งที่มีเอกสารใหม่

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปลี่ยน pattern ของประเภทเอกสาร | System Admin → Running Code → แก้ row → เพิ่ม / แก้ / จัดเรียง **part** | Preview อัปเดตสด; **Advanced config** แสดง JSON ที่จะถูกบันทึก |
| เพิ่ม running code สำหรับ doc type ใหม่ | System Admin → Running Code → New | ฟิลด์ `type` แบบ free-text (ไม่ใช่ picker; ใช้การสะกดตาม preset) + part |
| ขยาย counter (เช่น 4→5 หลัก) | แก้จำนวนหลักของ part **Running** | มีผลตอน mint ครั้งถัดไป; reference ประวัติศาสตร์ไม่เปลี่ยน |
| Preview เลขถัดไป | บรรทัด preview ใน dialog (`previewLabel`) | render part ด้วยวันที่วันนี้และ sequence 1 — ไม่ได้อ่าน counter จริง |
| ซ่อม config ที่อ่านไม่ได้ | Dialog แสดง `configUnreadable` และเปิด **Advanced config** | แก้ `format` / การอ้าง slot ใน JSON แล้ว part editor จะเปิดใช้อีกครั้ง |
| ปลดระวางประเภทเอกสาร | Soft-delete row | เฉพาะประเภทที่ปลดระวางและไม่อยู่ในการใช้งานปัจจุบัน |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate type" | Row ที่มีอยู่ที่ไม่ถูก delete | แก้ row ที่มีอยู่แทน |
| Textarea ของ Advanced-config reject ค่าตอนบันทึก | `config` ไม่ใช่ JSON ที่ valid | แก้ syntax |
| Part editor ถูกปิด แสดง `configUnreadable` | `config` ไม่มี `format` หรือ `format` อ้าง slot ที่ไม่มีอยู่ | ซ่อมใน Advanced config; editor ปฏิเสธที่จะเดาและเขียนทับ |
| Counter รีเซ็ตโดยไม่คาดคิด | Dated segment เปลี่ยน | Counter scope โดย `type + dated-segment` — การเพิ่ม `yyyyMM` รีเซ็ตรายเดือน |
| 500 `Cannot read properties of undefined (reading 'config')` ที่เอกสารแรกของ type | BU ไม่มี row สำหรับ type นั้น **และ** ไม่มี preset (`RUNNING_CODE_PRESET`) | เพิ่ม row ที่นี่ หรือเพิ่ม preset ในโค้ด (`GL-JV` ถูกแก้แบบนี้เมื่อ 2026-09-15) |
| Document number collision | Bug การ persist counter หรือการแก้ด้วยมือ | รีเซ็ต counter ของบริการ numbering; ตรวจสอบ |
| ไม่สามารถ delete | ประเภทเอกสารใช้งานอยู่ | Soft-delete เท่านั้นหลังการปลดระวาง |

## 4. กรณีพิเศษ

- **Editor แบบมีโครงสร้างพร้อมทางออก JSON** part editor รับประกัน `format` ที่สอดคล้องกันสำหรับทุกอย่างที่มันบันทึก; มีเพียงเส้นทาง Advanced-config ที่ยังเก็บ `format` ที่อ้าง slot ที่ไม่ได้นิยามได้ ซึ่งจะ fail ตอนสร้างเอกสาร
- **`GL-JV` ไม่มี part prefix แบบ literal โดยตั้งใจ** — prefix อยู่บน `tb_gl_jv_header.prefix_code` และ `jv_no` มีเพียง `date('yyyyMM') + running(5,'0')`; การเพิ่ม literal จะทำให้ lookup แบบ `startsWith` และการรีเซ็ต counter ของโมดูล GL พัง (`running-code.const.ts:119`)
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
- **Format validation** ต้องอ้างอิงอย่างน้อยหนึ่ง segment เพื่อใช้งานได้ตอน mint; part editor emit `format` ที่สอดคล้องกันเสมอ textarea ของ Advanced-config ตรวจแค่ `config` parse เป็น JSON ได้
- **Preset fallback** BU ที่ไม่มี row สำหรับ type ใช้ `RUNNING_CODE_PRESET[type]`; type ที่ไม่มีทั้งสองอย่าง fail อย่างแรง
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
- **Backend pattern logic:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/helpers/running-code.helper.ts` — `GenerateCode`, `getPattern`; preset `apps/micro-business/src/master/running-code/const/running-code.const.ts` (`RUNNING_CODE_PRESET`); service `apps/micro-business/src/master/running-code/running-code.service.ts` (`update` guard ด้วย `doc_version`, `:301`)
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_running-codes/` — `api/config/:bu_code/running-codes`; licence `system_admin.running_code` (`permission.route-map.ts:121`)
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`; `packages/prisma-shared-schema-tenant/src/seed-data/running-code.ts` (รวม `GL-JV`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/running-code/` — `running-code-component.tsx` (list), `running-code-dialog.tsx` (สร้าง/แก้ไข), `running-code-config-fields.tsx` (part editor + preview), `running-code-config.ts` (`parseConfig`, `serializeConfig`, `previewCode`, `slotName`), `running-code-form-schema.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1110-running-code.md` — แคตตาล็อกเท่านั้น
