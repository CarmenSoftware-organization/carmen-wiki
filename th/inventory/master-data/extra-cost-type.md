---
title: ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type)
description: แคตตาล็อกหมวด landed cost ของ GRN (ค่าขนส่ง อากร handling) พร้อมโหมดการจัดสรรต่อ instance — นับจาก 2026-09-10 ledger ของ GRN กระจายยอดรวมลง extra_cost_amount ของ cost layer จริง
published: true
date: '2026-09-23T01:30:00.000Z'
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

`by_value` และ `by_qty` เป็นสอง label ของโหมดจัดสรรที่ผู้ใช้เลือกได้จริงบนฟอร์ม GRN ปัจจุบัน; `manual` เป็นค่าที่สามที่ enum และ schema อนุญาต แต่ picker ไม่เคยเสนอให้เลือก **บริหารจัดการโดย** Product Admin (catalogue) และผู้ใช้ GRN (instance) **อ่านโดย** ตัวสร้าง ledger ของ GRN ณ เวลา commit

**การจัดสรรทำงานจริงแล้วนับจาก 2026-09-10 (แก้ไขในรอบนี้)** หน้านี้เวอร์ชัน 2026-07 รายงาน — ซึ่งถูกต้อง ณ เวลานั้น — ว่า `allocate_extra_cost_type` เป็นแค่ tag ที่ไม่มีผลต่อการคำนวณ backend commit "GRN FOC to stock + extra cost into landed cost" (2026-09-10) เปลี่ยนเรื่องนั้น: `apps/micro-business/src/inventory/good-received-note/good-received-note.extra-cost.ts` (`allocateExtraCost`) ตอนนี้กระจาย **ผลรวมของทุก `tb_extra_cost_detail.amount` บน GRN** ข้ามบรรทัดรับที่นำสต๊อกเข้า on hand จริง และ `good-received-note.ledger.ts:105-133` เขียนส่วนแบ่งของแต่ละบรรทัด (แปลงเป็นสกุลเงินหลักด้วย `exchange_rate` ของ GRN) ลง `base_extra_cost_amount` ซึ่งไปลงคอลัมน์ใหม่ของ cost layer `tb_inventory_transaction_cost_layer.extra_cost_amount` (`20260910130000_add_cost_layer_extra_cost`) landed unit cost ที่ costing engine นำไปเฉลี่ยคือ `base_net_amount + base_extra_cost_amount` (`inventory-transaction.service.ts:91`) ดังนั้น `amount` ที่พิมพ์บนแต่ละ cost line จึงหมายถึง "ส่วนนี้ของยอดรวม" และโหมดบน header หมายถึง "ยอดรวมถูกแบ่งข้ามบรรทัดสินค้าอย่างไร":

| `allocate_extra_cost_type` | สิ่งที่โค้ดทำ (`allocateExtraCost`) |
| --- | --- |
| `by_qty` | **แบ่งเท่ากันต่อบรรทัดรับ** — ทุกบรรทัดที่ `stock_qty > 0` ได้ `total / n` ไม่ว่าจะรับมาเท่าไร (ชื่อบอกว่าเป็นสัดส่วนตามจำนวน; แต่โค้ดแบ่งเท่ากัน — น้ำหนักเป็น `1` ต่อบรรทัด) |
| `by_value` | **ถ่วงน้ำหนักตามจำนวนหน่วยที่รับ** — น้ำหนักคือ `stock_qty` ของแต่ละบรรทัด (ชื่อบอกว่าเป็นสัดส่วนตามมูลค่า; แต่โค้ดถ่วงน้ำหนักตามจำนวน ไม่ใช่ตามยอดเงิน) |
| `manual` / `null` | ไม่จัดสรรอะไรเลย; `extra_cost_amount` คงเป็น `0` comment ในโค้ดบอกว่า input ส่วนแบ่ง manual ต่อบรรทัด "ยังไม่มี" |

บรรทัดที่ไม่ได้รับอะไรเลย (`stock_qty = 0`) ไม่มีวันได้ส่วนแบ่ง ดังนั้นบรรทัดที่เป็น FOC ทั้งหมดหรือ qty เป็นศูนย์จะไม่ทำให้เงินค้างหรือหารด้วยศูนย์ เมื่อข้อมูลประวัติมี header `tb_extra_cost` มากกว่าหนึ่งอันบน GRN ยอด detail ทั้งหมดจะถูกรวมและกระจายภายใต้โหมดของ header ที่**เก่าที่สุด** (อันที่ `findOne` แสดง)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มประเภท cost | Configuration → Master Data → Extra Cost Type → **New** | บังคับ: `name` |
| ยกเลิกการใช้งานประเภท | Toggle `is_active` | ซ่อนจาก GRN ใหม่; GRN ประวัติไม่ได้รับผลกระทบ |
| Attach กับ GRN | หน้าแก้ GRN → ส่วน **Extra Costs** | สร้าง header `tb_extra_cost` หนึ่งอัน (ต่อ GRN หนึ่งใบ) บวกแถว `tb_extra_cost_detail` หนึ่งแถวต่อ cost line ที่เพิ่ม |
| เลือก label โหมดการจัดสรร | หน้าเดียวกัน → dropdown โหมด | มีแค่ `by_qty` / `by_value` เท่านั้นที่เสนอ (`by_qty` เป็น default ของฟอร์ม); `manual` มีอยู่ใน schema แต่ไม่ใช่ตัวเลือกใน picker |
| ใส่ยอดต่อ cost line | หน้าเดียวกัน → **Add Cost** → ฟิลด์ `amount` ต่อแถว | ตัวเลขที่พิมพ์ด้วยมือต่อ cost line (ค่าขนส่ง ฿1,200, อากร ฿300, …) *ผลรวม* ของบรรทัดเหล่านี้คือสิ่งที่โหมดบน header กระจายข้ามบรรทัดสินค้าตอนสร้าง ledger — ตัวการแบ่งเองไม่เคยถูกแสดงหรือแก้ไขบนฟอร์ม |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่น |
| **ยังไม่ยืนยัน** — ไม่พบ delete guard | `extra_cost_type.service.ts`'s `delete()` เป็น soft-delete แบบไม่มีเงื่อนไข ไม่มีการเช็คแถว `tb_extra_cost_detail` ที่อ้างอิงอยู่ | เดิมหน้านี้ระบุว่า "cannot delete — referenced by GRN extra-cost detail" เป็น error ที่บังคับใช้จริง; ให้ถือว่า**ยังไม่ถูกบังคับใช้**จนกว่าจะตรวจสอบซ้ำ |
| **ยังไม่ยืนยัน** — ไม่พบการ reconcile หรือ lock บน GRN ที่ posted | เดิมหน้านี้ระบุว่า "missing allocation amount," "allocated sum doesn't equal parent" และ "cannot change allocation on a posted GRN" เป็น error ที่บังคับใช้จริง ไม่มีการเช็ค sum-reconciliation เพราะไม่มีอะไรให้ reconcile — การแบ่งถูกคำนวณ ไม่ใช่กรอก (`splitByWeight` กระจายเศษปัดให้ส่วนแบ่งรวมกันได้ยอดรวมเสมอ) ข้อจำกัดการแก้ใด ๆ มาจาก `doc_status` gate ของ GRN เอง (saved / committed — ดู [good-receive-note](/th/inventory/good-receive-note)) ไม่ใช่จาก extra cost โดยเฉพาะ | ถือว่าทั้งสามข้อความนี้ไม่เกี่ยวข้อง / ไม่ถูกบังคับใช้ |

## 4. Edge Cases

- **ฟอร์มยังไม่แสดงการจัดสรร** `Select` ของโหมดและ `Input` ของ `amount` ต่อแถวใน `grn-extra-cost-fields.tsx` ยังเป็น field ที่แยกอิสระจากกัน; การแบ่งต่อสินค้าถูกคำนวณเฉพาะตอนสร้าง ledger ของ GRN (ดู [good-receive-note](/th/inventory/good-receive-note) สำหรับจังหวะ save / commit) ดังนั้น tester จะมองไม่เห็นส่วนแบ่งบนหน้าจอ GRN — ให้ตรวจ `tb_inventory_transaction_cost_layer.extra_cost_amount` (หรือ unit cost บน stock card) แทน
- **ชื่อโหมดชวนเข้าใจผิด** `by_qty` คือแบ่งเท่ากันต่อบรรทัด และ `by_value` ถ่วงน้ำหนักตาม `stock_qty` — ไม่มีอันไหนใช้มูลค่าบรรทัด ความคาดหวังในการทดสอบต้องตามโค้ด ไม่ใช่ตาม label
- **`manual` มีแค่ใน schema** Prisma enum และ DTO ยอมรับ `manual` เป็นค่าที่สามของ `allocate_extra_cost_type` แต่ dropdown ของฟอร์ม GRN hard-code แค่ `by_qty` และ `by_value` เป็นตัวเลือก — `manual` เข้าไม่ถึงผ่าน UI
- **ประเภท inactive** ยังอ่านได้บน GRN ประวัติ
- **ผลกระทบต่อ costing — ยืนยันแล้ว** `extra_cost_amount` บน inbound cost layer ถูกรวมในต้นทุนของ layer (`base_net_amount + base_extra_cost_amount`) ดังนั้น unit cost ทั้ง AVG และ FIFO มี landed cost ตั้งแต่วินาทีที่แถว ledger ของ GRN ถูกเขียน (จังหวะ save / commit ตามโมดูล GRN) GRN ที่ post ก่อน 2026-09-10 มี `extra_cost_amount = 0` บน layer ของมัน (default ของคอลัมน์) และ **ไม่ถูก** back-fill

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
- **Validation** ไม่มีโค้ดบังคับให้ทุก cost line ต้องมียอด; บรรทัดยอดศูนย์แค่ไม่มีส่วนร่วมในยอดรวม `allocateExtraCost` ข้ามยอดรวมที่อยู่ภายใน `AMOUNT_EPSILON` ของศูนย์
- **Invariant การจัดสรร — ยืนยันแล้ว** ส่วนแบ่งสร้างโดย `splitByWeight(total, weights)` เหนือบรรทัดรับเท่านั้น; ส่วนแบ่งรวมกันได้ยอดรวมโดยโครงสร้าง ความหมายของโหมด: `by_qty` → น้ำหนักเท่ากัน, `by_value` → น้ำหนัก `stock_qty`, `manual` → ไม่จัดสรร (`good-received-note.extra-cost.ts:41-60`)
- **Default sort** `GET /extra-cost-types` ที่ไม่มี `?sort=` คืน `name:asc, id:asc` (`extra_cost_type.service.ts`, `withDefaultSort`, 2026-09-13)
- **Lifecycle** ประเภท inactive อ่านได้บน GRN ประวัติ; ซ่อนจาก picker GRN ใหม่
- **การ re-allocation — ยังไม่ยืนยัน** ไม่พบ lock เฉพาะโหมด; ข้อจำกัดใดก็ตามในการแก้ extra cost หลัง posting มาจาก `doc_status` gate ทั่วไปของ GRN ไม่ใช่จากเอนทิตีนี้

## 7. การอ้างอิงข้ามโมดูล

- [good-receive-note](/th/inventory/good-receive-note) — ผู้บริโภคแต่เพียงผู้เดียว แต่ละ GRN มี header `tb_extra_cost` หนึ่งอันที่บรรจุแถว `tb_extra_cost_detail` หลายแถว แต่ละแถว tag ด้วยประเภท extra-cost และยอดที่กรอกด้วยมือ
- [costing](/th/inventory/costing) — landed unit cost รวม `extra_cost_amount` ของแต่ละ layer (`inventory-transaction.service.ts:91`); ดู [inventory/01-data-model](/th/inventory/inventory/01-data-model) สำหรับคอลัมน์ของ cost layer

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (line ~5811), `tb_extra_cost` (~5675), `enum_allocate_extra_cost_type` (~109)
- **Migration:** `20260910130000_add_cost_layer_extra_cost` (`tb_inventory_transaction_cost_layer.extra_cost_amount DECIMAL(20,5) DEFAULT 0`)
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/good-received-note/good-received-note.extra-cost.ts` (`allocateExtraCost`), `good-received-note.ledger.ts` (`base_extra_cost_amount`), `apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts:91`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/030-extra-cost.spec.ts` + `docs/test-cases/gaps/030-extra-cost-gap.md`
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/extra-cost-type/` (catalogue); `../carmen-inventory-frontend-react/routes/procurement/goods-receive-note/grn-extra-cost-fields.tsx` (ฟอร์ม instance ของ GRN)
