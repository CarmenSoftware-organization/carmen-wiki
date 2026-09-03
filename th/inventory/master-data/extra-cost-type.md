---
title: ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type)
description: แคตตาล็อกหมวด landed cost ของ GRN (ค่าขนส่ง อากร handling) พร้อมโหมดการจัดสรรต่อ instance (by value, by qty, manual)
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, extra-cost-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_extra_cost_type` (catalogue) + `tb_extra_cost` (per-GRN instance) &nbsp;·&nbsp; **ใช้โดย:** การจัดสรร landed cost ของ GRN &nbsp;·&nbsp; หมวดเช่น Freight / Duty / Handling พร้อมโหมดจัดสรร `by_value` / `by_qty` / `manual`

![ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type) screen](/screenshots/master-data/extra-cost-type.png)

## 1. คืออะไร / ใครใช้

**Extra cost** คือค่าขนส่ง อากร handling และส่วนประกอบ **landed cost** อื่น ๆ ที่จัดสรรลงบนสินค้าที่รับเพื่อให้ **unit cost ใน inventory** สะท้อนต้นทุน *delivered* ไม่ใช่แค่บรรทัด invoice `tb_extra_cost_type` เก็บหมวดมีชื่อ (`Freight`, `Customs Duty`, `Brokerage`); `tb_extra_cost` เป็น instance ต่อ GRN พร้อม **โหมดการจัดสรร** ที่เลือก (`by_value`, `by_qty` หรือ `manual`)

`by_value` และ `by_qty` เป็นสอง label ของโหมดจัดสรรที่ผู้ใช้เลือกได้จริงบนฟอร์ม GRN ปัจจุบัน; `manual` เป็นค่าที่สามที่ enum และ schema อนุญาต แต่ picker ไม่เคยเสนอให้เลือก **บริหารจัดการโดย** Product Admin (catalogue) และผู้ใช้ GRN (instance) **อ่านโดย** costing engine ในหลักการ — ดู gap ที่ยืนยันแล้วด้านล่าง

**Gap ที่ยืนยันแล้ว (ตรวจสอบกับ `grn-extra-cost-fields.tsx` และ `good-received-note.service.ts` ในรอบนี้):** ไม่ว่าจะเลือกโหมดใด ทุกบรรทัด `tb_extra_cost_detail` มีฟิลด์ `amount` ที่พิมพ์ด้วยมือของตัวเอง — ไม่มีโค้ดที่ไหนใน GRN service ที่คำนวณหรือแบ่งยอด extra-cost รวมข้ามบรรทัดตามสัดส่วน value หรือ qty เลย ฟิลด์ `allocate_extra_cost_type` ถูกเก็บเป็นแค่ tag การจำแนกประเภท ไม่มีผลต่อการคำนวณที่พบในรอบนี้ ถือว่าสูตรการจัดสรร `by_value` / `by_qty` ด้านล่างเป็น **design intent** ไม่ใช่พฤติกรรมจริงที่ยืนยันแล้ว (ตรงกับ gap เดียวกันที่รอบ resync ของโมดูล good-receive-note เองยกธงไว้และปล่อยเป็นยังไม่ยืนยัน)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มประเภท cost | Configuration → Master Data → Extra Cost Type → **New** | บังคับ: `name` |
| ยกเลิกการใช้งานประเภท | Toggle `is_active` | ซ่อนจาก GRN ใหม่; GRN ประวัติไม่ได้รับผลกระทบ |
| Attach กับ GRN | หน้าแก้ GRN → ส่วน **Extra Costs** | สร้าง header `tb_extra_cost` หนึ่งอัน (ต่อ GRN หนึ่งใบ) บวกแถว `tb_extra_cost_detail` หนึ่งแถวต่อ cost line ที่เพิ่ม |
| เลือก label โหมดการจัดสรร | หน้าเดียวกัน → dropdown โหมด | มีแค่ `by_qty` / `by_value` เท่านั้นที่เสนอ (`by_qty` เป็น default ของฟอร์ม); `manual` มีอยู่ใน schema แต่ไม่ใช่ตัวเลือกใน picker |
| ใส่ยอดต่อ cost line | หน้าเดียวกัน → **Add Cost** → ฟิลด์ `amount` ต่อแถว | เป็นตัวเลขที่พิมพ์ด้วยมือเสมอ ไม่ว่าจะเลือก label โหมดใด — ไม่พบการแบ่งยอดอัตโนมัติ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่น |
| **ยังไม่ยืนยัน** — ไม่พบ delete guard | `extra_cost_type.service.ts`'s `delete()` เป็น soft-delete แบบไม่มีเงื่อนไข ไม่มีการเช็คแถว `tb_extra_cost_detail` ที่อ้างอิงอยู่ | เดิมหน้านี้ระบุว่า "cannot delete — referenced by GRN extra-cost detail" เป็น error ที่บังคับใช้จริง; ให้ถือว่า**ยังไม่ถูกบังคับใช้**จนกว่าจะตรวจสอบซ้ำ |
| **ยังไม่ยืนยัน** — ไม่พบการ reconcile หรือ lock บน GRN ที่ posted | เดิมหน้านี้ระบุว่า "missing allocation amount," "allocated sum doesn't equal parent" และ "cannot change allocation on a posted GRN" เป็น error ที่บังคับใช้จริง อ่านโค้ด `good-received-note.service.ts`'s extra-cost create/update path โดยตรงไม่พบการเช็ค sum-reconciliation และไม่พบ lock เฉพาะของ extra cost — การจำกัดการแก้ทั่วไปมาจาก `doc_status`/`isReadOnly` gate ของ GRN เอง (ดู [good-receive-note](/th/inventory/good-receive-note)) ไม่ใช่จาก extra cost โดยเฉพาะ | ถือว่าทั้งสามข้อความนี้ยังไม่ยืนยันจนกว่าจะตรวจสอบซ้ำ |

## 4. Edge Cases

- **ไม่พบการคำนวณการจัดสรร** `amount` บนแต่ละแถว `tb_extra_cost_detail` เป็นค่าที่ผู้ใช้กรอกเองเสมอ; การเปลี่ยน label `allocate_extra_cost_type` ของ header ไม่ recalculate บรรทัดใดเลย (ยืนยันจากการอ่าน `grn-extra-cost-fields.tsx` — `Select` ของโหมด และ `Input` ของ `amount` ต่อแถว เป็น field ของฟอร์มที่แยกอิสระจากกัน ไม่มีการเชื่อมโยงแบบ derived-value)
- **`manual` มีแค่ใน schema** Prisma enum และ DTO ยอมรับ `manual` เป็นค่าที่สามของ `allocate_extra_cost_type` แต่ dropdown ของฟอร์ม GRN hard-code แค่ `by_qty` และ `by_value` เป็นตัวเลือก — `manual` เข้าไม่ถึงผ่าน UI
- **ประเภท inactive** ยังอ่านได้บน GRN ประวัติ
- **ผลกระทบต่อ costing — ยังไม่ยืนยัน** เจตนาคือให้ extra cost ไหลเข้า landed unit cost ที่ costing engine บริโภค; ยังไม่ยืนยันในรอบนี้ว่ามีโค้ด costing ใดอ่านยอด `tb_extra_cost_detail` จริงหรือไม่ (ตรงกับ flag ที่ยังไม่ยืนยันของโมดูล good-receive-note เองในประเด็นนี้)

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_extra_cost_type`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String? @db.VarChar` | Yes | ชื่อแสดงผล (เช่น `Freight`) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `is_active` | `Boolean?` | Yes | Active flag |
| `info`, `dimension`, `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `extra_cost_type_name_u` Index บน `name` Reverse relation ไปยัง `tb_extra_cost_detail`

### 5.2 `tb_extra_cost`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String? @db.VarChar` | Yes | Label แบบ free text |
| `good_received_note_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_good_received_note` |
| `allocate_extra_cost_type` | `enum_allocate_extra_cost_type?` | Yes | `manual`, `by_value` หรือ `by_qty` |
| `description`, `note` | `String?` | Yes | Free text |
| `info`, `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** index บน `name` (`extra_cost_name_idx`) FK ไปยัง `tb_good_received_note` `onDelete: NoAction` Reverse relation ไปยัง `tb_extra_cost_detail` และ `tb_extra_cost_comment` (`tb_extra_cost_detail` บรรจุการแยกย่อยต่อบรรทัดรวมทั้ง FK ไปยัง `tb_extra_cost_type`)

`enum_allocate_extra_cost_type` values: `manual`, `by_value`, `by_qty`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `tb_extra_cost_type.name` unique ในแถว non-deleted
- **Deletion guards — ยังไม่ยืนยัน** ไม่พบการเช็ค FK ใน `delete()`; soft-delete สำเร็จโดยไม่มีเงื่อนไขแม้มีการอ้างอิงจาก `tb_extra_cost_detail`
- **Validation — ยังไม่ยืนยัน** ไม่พบโค้ดที่บังคับให้ทุกบรรทัดต้องมียอดก่อน posting หรือปฏิเสธการจัดสรรที่ไม่สมดุล ทุกบรรทัดมีฟิลด์ `amount` ที่แก้ไขได้เสมออยู่แล้ว จึงไม่มีอะไรให้เช็คแบบนี้บังคับใช้นอกเหนือจาก required-field validation ปกติ
- **Invariant การจัดสรร — design intent ยังไม่ยืนยัน** ไม่พบโค้ด reconciliation (`by_value` / `by_qty` บวกกันได้ parent total) ใน `good-received-note.service.ts`
- **Lifecycle** ประเภท inactive อ่านได้บน GRN ประวัติ; ซ่อนจาก picker GRN ใหม่
- **การ re-allocation — ยังไม่ยืนยัน** ไม่พบ lock เฉพาะโหมด; ข้อจำกัดใดก็ตามในการแก้ extra cost หลัง posting มาจาก `doc_status` gate ทั่วไปของ GRN ไม่ใช่จากเอนทิตีนี้

## 7. การอ้างอิงข้ามโมดูล

- [good-receive-note](/th/inventory/good-receive-note) — ผู้บริโภคแต่เพียงผู้เดียว แต่ละ GRN มี header `tb_extra_cost` หนึ่งอันที่บรรจุแถว `tb_extra_cost_detail` หลายแถว แต่ละแถว tag ด้วยประเภท extra-cost และยอดที่กรอกด้วยมือ
- [costing](/th/inventory/costing) — landed unit cost *มีเจตนา* ให้ไหลจากการจัดสรร extra cost; ยังไม่ยืนยันว่ามีโค้ด costing ใดอ่านยอด `tb_extra_cost_detail` จริงหรือไม่ (ดู Edge Cases)

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (lines ~5204-5227), `tb_extra_cost` (lines ~5068-5092), `enum_allocate_extra_cost_type` (lines ~105-109)
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/extra-cost-type/` (catalogue); `../carmen-inventory-frontend-react/routes/procurement/goods-receive-note/grn-extra-cost-fields.tsx` (ฟอร์ม instance ของ GRN)
