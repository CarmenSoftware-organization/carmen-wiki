---
title: มิติ (Dimension)
description: ระบบ custom field ที่ provision ไว้ใน schema (tb_dimension, tb_dimension_display_in และคอลัมน์ dimension JSONB บน ~65 ตาราง) แต่ไม่มีหน้าจอ CRUD ไม่มี backend service และไม่มี frontend ที่ใช้งานจริงเลยในโค้ดเบส
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, dimension, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# มิติ (Dimension)

> **At a Glance**
> **เจ้าของ:** ไม่มีใครวันนี้ — **ไม่มี UI หรือ API สำหรับสร้าง/แก้ dimension เลย** &nbsp;·&nbsp; **ตาราง:** `tb_dimension` (+ `tb_dimension_display_in`) &nbsp;·&nbsp; **คอลัมน์ `dimension` JSONB** provision ไว้บน ~65 ตารางในฐาน tenant (ทั้งธุรกรรมและ master) แต่ไม่มีโค้ดใดอ่านหรือเขียนเลย &nbsp;·&nbsp; ระบบ custom field ที่ยังเป็นแค่ design — schema มีอยู่ แต่ไม่มีอะไร implement มัน

## สถานะการ implement (ตรวจสอบ 2026-07-16)

การค้นทั่วทั้ง repo (`carmen-inventory-frontend-react`, `carmen-turborepo-backend-v2`) **ไม่พบ route, component, controller หรือ service ใดเลย** ที่สร้าง แก้ไข แสดงรายการ หรือลบ row ของ `tb_dimension` หรือ `tb_dimension_display_in`:

- **ไม่มี frontend route** `/system-admin` ไม่มี path `dimension` ใน `routes/router.tsx` และไม่มี directory ชื่อ `dimension` ใต้ `routes/system-admin/` หน้า System Admin landing (`landing-types.ts`) ก็ไม่มีโมดูล Dimensions อยู่ในทั้ง 5 chapter
- **ไม่มี backend CRUD** `tb_dimension` ถูกอ้างถึงในไฟล์ non-schema เพียงไฟล์เดียวคือ `dimension-comment.service.ts` — และใช้แค่ตรวจสอบ `findFirst` ว่ามี row อยู่ก่อนสร้าง comment ไม่มี `dimension.service.ts`, `dimension.controller.ts` หรือ Bruno folder `config/dimension/*` (มีแค่ `config/dimension-comment/*` ซึ่งเป็น comment thread บน row ที่ต้องมีอยู่แล้วโดยวิธีอื่น — insert ตรงเข้าฐานข้อมูลหรือ seed data ซึ่งไม่พบที่ไหนเลยในโค้ด)
- **`tb_dimension_display_in` ไม่มีการอ้างอิงนอก schema เลยแม้แต่จุดเดียว** — แม้แต่ฟีเจอร์ comment ก็ไม่แตะตารางนี้
- **คอลัมน์ `dimension` JSONB มีจริงแต่ไม่มีชีวิต** ตาราง tenant 65 ตารางมีคอลัมน์ `dimension Json?` (ยืนยันด้วยการนับ grep กับ Prisma schema) รวมถึง `tb_purchase_request`, `tb_workflow` และตารางธุรกรรม/master ส่วนใหญ่ — แต่การค้นในโมดูล Purchase Request (โมดูลที่ "การอ้างอิงข้าม" ด้านล่างทุกจุดชี้ไปหา) ไม่พบการอ่านหรือเขียน `.dimension` เลยในฟอร์ม hook หรือ service ใดๆ ของมัน คอลัมน์นี้คือ capacity ที่ provision ไว้ใน schema ไม่ใช่ฟีเจอร์ที่ต่อสายไว้แล้ว
- ทุกจุดที่เจอคำว่า `dimension` เปล่าๆ ใน `carmen-inventory-frontend-react` (นอกเหนือจาก dead code path นี้) กลายเป็นฟิลด์ physical-dimension ที่ไม่เกี่ยวข้อง — ความยาว-กว้าง-สูงของ equipment/product/unit ไม่ใช่แนวคิด custom field นี้

เนื้อหาที่เหลือของหน้านี้อธิบาย **เจตนาการออกแบบ** ตามที่ปรากฏใน schema (เก็บไว้เพราะตารางและคอลัมน์มีอยู่จริงและอาจถูกสร้างต่อในอนาคต) ไม่ใช่ฟีเจอร์ที่ ship แล้ว ถือว่าทุก task/workflow ที่กล่าวถึงด้านล่าง **ยังไม่ยืนยัน / ยังไม่ implement** เว้นแต่จะระบุไว้เป็นอย่างอื่น

## 1. คืออะไรและใครใช้

Dimension คือ **ระบบ custom field ที่ผู้ใช้ขยายได้ตามแผน** ที่ provision ไว้ใน schema แต่ยังไม่ได้สร้างต่อ ตามการออกแบบที่ตั้งใจไว้: มิติหนึ่งนิยาม tag ที่มีชื่อ (`cost_centre`, `project_code`, `gl_account_override`, `event_name`, …) พร้อม value space แบบ typed, default value และรายการของ *สถานที่ที่ควรปรากฏ* — header ของ PR, detail ของ GRN, master ของ vendor ฯลฯ ค่าของผู้ใช้ปลายทางควรถูกเก็บในคอลัมน์ `dimension` JSONB ที่ตารางธุรกรรม/master ส่วนใหญ่พกพา — แต่ไม่มีโค้ดใดเติมหรืออ่านคอลัมน์นั้นในวันนี้

การแยกเป็นสองตารางสะท้อนการออกแบบที่ตั้งใจไว้ `tb_dimension` ควรเป็น *นิยาม* `tb_dimension_display_in` ควรเป็น *matrix การแสดงผล* — หนึ่ง row ต่อสถานที่ที่ dimension ควรปรากฏ (พร้อม default override ต่อสถานที่) นี่คือการออกแบบสำหรับการติด tag cost-centre บน PR header และ IA detail line โดยไม่ต้อง hardcode คอลัมน์ — **ยังไม่เกิดขึ้นจริงในโค้ด**

**บำรุงรักษาโดย** ไม่มีใครในปัจจุบัน — ไม่มีหน้าจอ admin **อ่านโดย** ไม่พบเลย — ไม่มีฟอร์มใด render ฟิลด์ dimension ไม่มีรายงานใดทำการจัดสรรต้นทุนจากตารางนี้

## 2. งานทั่วไป

ไม่มีงานใดในตารางนี้ที่ทำได้จริงวันนี้ — ไม่มีหน้าจอ เก็บไว้เป็น *เจตนาการออกแบบ* ที่บอกใบ้จากรูปร่าง schema เท่านั้น อย่าถือว่าเป็นพฤติกรรมที่ยืนยันแล้ว

| งาน (เจตนาการออกแบบ ยังไม่สร้าง) | ที่ไหน (ไม่มีอยู่จริง) | หมายเหตุ |
|---|---|---|
| นิยาม dimension | ~~System Config → Dimensions → New~~ | ไม่มีหน้าจอนี้ |
| เปิดใช้ dimension บนสถานที่ | ~~Dimension edit → display-in matrix~~ | ไม่มีหน้าจอนี้ |
| คัดสรรค่าที่อนุญาตของ `lookup` | ~~Dimension edit → editor `value`~~ | ไม่มีหน้าจอนี้ |
| Override default ต่อสถานที่ | ~~Display-in row → `default_value`~~ | ไม่มีหน้าจอนี้ |
| ปลดระวาง dimension | ~~ตั้ง `is_active = false`~~ | ต้องมี row อยู่ก่อน — ไม่พบทางสร้าง |
| ตรวจสอบการเปลี่ยนแปลง dimension | ~~[reporting-audit/activity](/th/inventory/reporting-audit/activity) log~~ | ไม่มี service เขียนการเปลี่ยนแปลง dimension; ไม่มีอะไรให้ตรวจสอบ |

## 3. การตรวจสอบและ Error

ยังไม่ยืนยัน — ไม่มี service layer บังคับสิ่งเหล่านี้เลย เก็บไว้เป็นเจตนาการออกแบบเท่านั้น

| อาการ (สมมติฐาน) | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Key already exists" | ซ้ำในกลุ่มที่ไม่ถูก delete | ยังไม่ implement — ไม่มี create endpoint |
| "Value not in catalogue" | ค่า `lookup` ไม่อยู่ใน `value` JSON | ยังไม่ implement |
| ไม่สามารถ hard-delete dimension | เอกสารมีค่าที่ไม่ว่างสำหรับ key | ยังไม่ implement — ไม่มีเอกสารใดเขียนค่าเลย |
| ฟิลด์หายจากฟอร์มใหม่ | Row `display_in` ขาดหายหรือถูกลบ | ไม่เกี่ยวข้อง — ไม่มีฟอร์มใด render ฟิลด์ dimension |
| Type mismatch ตอนบันทึก | ค่าเอกสารละเมิด `type` | ยังไม่ implement |

## 4. กรณีพิเศษ

- **ไม่มีอะไรให้ snapshot** ไม่เคยพบเอกสารใดเขียนค่า `dimension` JSON เลย ดังนั้นคำถามเรื่อง "snapshot semantics" (การแก้ catalogue ภายหลัง retro-edit เอกสารประวัติศาสตร์หรือไม่) จึงไม่มีความหมายจนกว่าจะมีตัวเขียน
- **ฟีเจอร์ comment คือ code path เดียวที่มีชีวิต** `dimension-comment` ให้ผู้เรียกแนบ comment แบบอิสระกับ `tb_dimension.id` ที่ *มีอยู่แล้ว* — แต่ไม่มีอะไรในโค้ดเบสสร้าง row นั้น ดังนั้นในทางปฏิบัติ endpoint นี้จึงไม่มีเป้าหมายที่เข้าถึงได้จาก UI ใดเลย
- **การติด tag บน master record** (vendor / location / currency สืบทอด default ของ dimension) เป็นแค่ภาษาการออกแบบ — ไม่พบโค้ด cascade ใดเลย

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_dimension`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `key` | `String @db.VarChar` | No | Key เชิงโปรแกรม (เช่น `cost_centre`) เก็บตามตัวอักษรใน array `dimension` ของเอกสาร |
| `type` | `enum_dimension_type` | No | `string`, `number`, `boolean`, `date`, `datetime`, `json`, `dataset`, `lookup`, `lookup_dataset` |
| `value` | `Json? @db.JsonB` | Yes | รายการ catalogue / ค่าที่อนุญาต |
| `description` / `note` | `String?` | Yes | Free text |
| `default_value` | `Json? @db.JsonB` | Yes | Default ระดับบนสุด |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `info` | `Json? @db.JsonB` | Yes | Metadata อิสระ |
| `doc_version` | `Int` | No | Optimistic-concurrency token |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([key, deleted_at])` Index บน `[key]`

### 5.2 `tb_dimension_display_in`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `dimension_id` | `String @db.Uuid` | No | FK ไปยัง `tb_dimension.id` |
| `display_in` | `enum_dimension_display_in` | No | ที่ที่ dimension จะแสดง |
| `default_value` | `Json? @db.JsonB` | Yes | Override ต่อสถานที่ |
| `note` / `info` / `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([dimension_id, display_in, deleted_at])` Index บน `[dimension_id, display_in]` FK `onDelete: NoAction`

**`enum_dimension_display_in`:** `currency`, `exchange_rate`, `delivery_point`, `department`, `product_category`, `product_sub_category`, `product_item_group`, `product`, `location`, `vendor`, `pricelist`, `unit`, `purchase_request_header`, `purchase_request_detail`, `purchase_order_header`, `purchase_order_detail`, `goods_received_note_header`, `goods_received_note_detail`, `transfer_header`, `transfer_detail`, `stock_in_header`, `stock_in_detail`, `stock_out_header`, `stock_out_detail`

## 6. กฎทางธุรกิจ

กฎด้านล่างไม่มีกฎใดถูกบังคับด้วยโค้ดเลย — อธิบายรูปร่าง constraint ที่ schema บอกใบ้ (unique index, FK, nullable flag) ไม่ใช่พฤติกรรมแอปพลิเคชันที่ยืนยันแล้ว

- **ความเป็นหนึ่งเดียว (ระดับ schema เท่านั้น)** `key` unique ในกลุ่มที่ไม่ถูก delete; แต่ละ `(dimension_id, display_in)` unique — บังคับโดย DB index ไม่ใช่โดย application-layer check ใด (ไม่มี service ให้เรียก)
- **Type validation, cascade ของ default, การ์ดการลบ, การลบสถานที่, snapshot semantics** — ทั้งหมดเป็นเจตนาการออกแบบที่สืบทอดจาก spec เดิม **ไม่มีโค้ดใด implement สิ่งเหล่านี้เลย**

## 7. การอ้างอิงข้าม

โมดูลด้านล่างไม่มีโมดูลใดถูกพบว่าอ้างอิง dimension ในทางใดเลยในโค้ด ลิงก์ข้ามถูกเก็บไว้เพียงเพราะคอลัมน์ `dimension` JSONB ของ schema ปรากฏอยู่บนตารางของมัน ถือว่าทุกบรรทัดเป็น "คอลัมน์มีอยู่ ไม่ได้ใช้" ไม่ใช่ "การเชื่อมต่อยืนยันแล้ว"

- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order) — คอลัมน์ `dimension` มีอยู่บนตาราง header/detail; ไม่พบการอ่าน/เขียนเลย
- [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment), [inventory](/th/inventory/inventory) — เหมือนกัน: คอลัมน์มีอยู่ ไม่ได้ใช้
- [master-data/vendor](/th/inventory/master-data/vendor), [master-data/location](/th/inventory/master-data/location), [master-data/currency](/th/inventory/master-data/currency), [product](/th/inventory/product) — ไม่พบ UI การติด tag dimension หรือโค้ด cascade บน master record ใดเลย

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dimension` (lines ~4981-5006), `tb_dimension_display_in` (lines ~5045-5065), `enum_dimension_display_in` (line ~164)
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/dimension-comment/dimension-comment.service.ts` — โค้ด non-schema เพียงจุดเดียวที่แตะ `tb_dimension` (ตรวจสอบ `findFirst` ก่อนเขียน comment) ไม่มี `dimension.service.ts` / `dimension.controller.ts`
- **Frontend:** ไม่พบเลย ไม่มี path `dimension` ใน `../carmen-inventory-frontend-react/routes/router.tsx` และไม่มี directory ชื่อ `dimension` ใต้ `../carmen-inventory-frontend-react/routes/system-admin/`
