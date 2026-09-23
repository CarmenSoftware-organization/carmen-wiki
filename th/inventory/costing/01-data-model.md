---
title: การคำนวณต้นทุน (Costing) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum สำหรับโมดูล costing — ตรวจสอบซ้ำ 2026-09-22 (extra_cost_amount, tb_inventory_period_snapshot, average ต่อสินค้า, ปัด 2 ตำแหน่ง)
published: true
date: '2026-09-23T01:30:00.000Z'
tags: costing, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Data Model

> **At a Glance**
> **ตาราง:** `tb_inventory_transaction_cost_layer` &nbsp;·&nbsp; `tb_inventory_transaction_detail` &nbsp;·&nbsp; `tb_inventory_period_snapshot` (เปลี่ยนชื่อจาก `tb_period_snapshot`, `20260916141000_rename_tb_period_to_tb_inventory_period`) &nbsp;·&nbsp; `tb_business_unit.calculation_method` &nbsp;·&nbsp; `tb_product.standard_cost`
> **กลุ่มผู้ใช้:** นักพัฒนา / Auditor (เอกสารอ้างอิงนักพัฒนา)
> **FK สำคัญ:** cost-layer `→ tb_inventory_transaction_detail`; cost-layer `→ tb_inventory_period` (`period_id`, `schema.prisma:1217`); detail `→ tb_good_received_note_detail_item` (`good_received_note_detail_item_id`, ตั้งแต่ 2026-08-10); การเชื่อม cross-schema: tenant cost-layer อ่าน platform `tb_business_unit.calculation_method` ผ่าน `bu_code` ของ request (ไม่มี Prisma `@relation`)
> **ตรวจสอบซ้ำ 2026-09-22:** คอลัมน์ใหม่ `tb_inventory_transaction_cost_layer.extra_cost_amount` (`20260910130000_add_cost_layer_extra_cost`); `tb_period*` → `tb_inventory_period*`; ค่าเฉลี่ยเป็นต่อ **สินค้า** ไม่ใช่ต่อ `(location, product)`; `cost_per_unit` บน ledger ปัดเป็น **2 ตำแหน่ง**; หมายเลข lot เป็น `<location_code><YYMM><run>`
> **รูปแบบ audit:** มาตรฐาน `created_*` / `updated_*` / `deleted_*` บน cost-layer และ snapshot; **`tb_inventory_transaction_detail` ไม่มี soft-delete** — การกลับรายการ post compensating row แทน

> **แหล่งข้อมูลอ้างอิงหลัก:** Prisma schema ฝั่ง backend อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อเขียนหรือปรับปรุงหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ในแต่ละ package เป็นไฟล์ที่ถูกสร้างขึ้นอัตโนมัติ ไม่ใช่แหล่งอ้างอิง

## 1. ภาพรวม

โมดูล Costing **ไม่ใช่ document tree แยกต่างหาก** ในแบบเดียวกับ GRN, PR หรือ SR แต่เป็น **สัญญา read-and-write ที่วางทับ inventory transaction ledger**: เอนจินอ่าน `tb_inventory_transaction_detail` และ `tb_inventory_transaction_cost_layer` เพื่อเลือกต้นทุนสำหรับการเคลื่อนไหวขาออก เขียน `cost_per_unit` / `average_cost_per_unit` / `extra_cost_amount` ลงบนแถว cost-layer ตอน post และอ่านกลับจากแถวเดียวกันเมื่อผู้บริโภคปลายน้ำ (recipe costing, financial reporting, valuation, endpoint `GET …/cost/products/:id/*`) ต้องการต้นทุนต่อหน่วย ไม่มี `tb_costing_*` model ใน Prisma schema — ข้อมูล costing อยู่บนเอนทิตี inventory (`tb_inventory_transaction_cost_layer` คือ canonical cost-flow record, `tb_inventory_transaction_detail.cost_per_unit` คือต้นทุนต่อบรรทัด, `tb_inventory_period_snapshot.closing_cost_per_unit` คือต้นทุนต่อหน่วยที่ล็อกปลายงวด) และ **การตั้งค่าวิธี costing** อยู่ที่ระดับสูงกว่าหนึ่งระดับที่ **business unit** ใน platform schema ไม่ใช่ที่ product

สมมติฐาน cost-flow — **FIFO** (lot ถูกบริโภคตาม `lot_seq_no` ascending แต่ละ lot มี `cost_per_unit` ของตัวเอง) หรือ **Weighted Average** (moving average เดียว **ต่อสินค้า** รีเฟรชทุกการรับเข้าและประทับซ้ำลงทุก layer ที่ยังมีชีวิตของสินค้านั้น — **แก้ไข 2026-09-22** ค่าเฉลี่ยไม่ใช่ต่อ `(location_id, product_id)`: `getNetTotals(tx, productId)` ใน `inventory-transaction.service.ts:1487-1509` ไม่สน location) — ตั้งค่าบน `tb_business_unit.calculation_method` (platform `enum_calculation_method = average | fifo`, default `average`) ที่ระดับ property หมายเหตุว่า **tenant** schema ก็ประกาศ `enum_calculation_method { FIFO, AVG }` (`schema.prisma:39-42`) ด้วย ซึ่งเอนจินไม่ได้ใช้ — โค้ด import enum ของ platform (`inventory-transaction.service.ts:2`) ของ tenant schema `enum_business_unit_config_key` เปิดเผย `calculation_method` เป็น runtime config key และ `enum_physical_count_costing_method` (`standard`, `last`, `average`, `last_receiving`) เลือกแหล่งต้นทุนที่ feed count-driven variance posts สินค้าเอง (`tb_product`) มี `standard_cost` (ต้นทุนอ้างอิงที่ใช้โดย `standard` count-costing method และ recipe baselining) และ `price_deviation_limit` / `qty_deviation_limit` (เพดานเป็นเปอร์เซ็นต์ที่ checklist การ **save** ของ GRN บังคับใช้เทียบกับบรรทัด PO — [good-receive-note/02-business-rules](/th/inventory/good-receive-note/02-business-rules) `GRN_VAL_006`/`007`) แต่ **ไม่มี** วิธี costing ต่อสินค้า — นี่เป็นการ simplify ระดับแพลตฟอร์มที่จงใจ ดูเอกสารใน Section 5

เอนจินทำงานแบบ **per-transaction ไม่ใช่ periodic batch** เมื่อ GRN โพสต์ (commit บน BU แบบ FIFO, save บน BU แบบ average) เอนจินรับหนึ่งรายการต่อเหตุการณ์รับพร้อม `received_base_qty`, `foc_base_qty`, `base_net_amount` และ `base_extra_cost_amount` (`ICreateFromGrnDetailItem`, `inventory-transaction.service.ts:44-56`) เขียน `tb_inventory_transaction_detail` หนึ่งแถว (`qty = received + FOC`, `cost_per_unit = Round2(total / qty)`, `current_lot_no = <location_code><YYMM><run>`, `good_received_note_detail_item_id`) และ cost layer หนึ่งชั้นขึ้นไป (`splitFifoCost(qty, totalCost, 2)` กระทบยอดทศนิยมให้ตรงกับยอดรวมพอดีข้ามแถว `lot_index`; ส่วนแบ่ง extra cost ถูกแบ่งลงแถวเดียวกันเป็น `extra_cost_amount`) กำหนด `lot_seq_no` ที่นับตามงวด และ — เฉพาะ BU แบบ average — คำนวณและประทับ `average_cost_per_unit` ใหม่ เมื่อ outbound movement post เอนจินอ่านวิธีที่ตั้งค่าไว้ เลือกต้นทุน (FIFO บริโภคจาก `lot_seq_no` ascending; WA อ่านค่าเฉลี่ยปัจจุบันของสินค้า) และเขียนแถว outbound `out_qty × cost_per_unit` ที่สอดคล้อง ที่ปลายงวด เอนจินเขียน `closing_cost_per_unit` บน `tb_inventory_period_snapshot` (BU แบบ average) และ cost-layer rows `transaction_type = close_period` / `open_period` ที่ยึดต้นทุนต่อหน่วยตอนข้ามขอบเขตงวด [`calculation-methods.md`](./calculation-methods.md) ที่เป็นเอกสารพี่น้องเจาะลึกอัลกอริทึม FIFO / WA และคำแนะนำการออกแบบ strategy-pattern ของแพลตฟอร์ม; หน้านี้คือสารบัญระดับ schema

## 2. เอนทิตี

### 2.1 tb_inventory_transaction_cost_layer (canonical cost record)

**Cost-flow ledger row** — แหล่งความจริงเดียวสำหรับ "หน่วยนี้ราคาเท่าไหร่?" ณ ทุกจุดเวลา หนึ่งแถวต่อ layer event ต่อ movement: inbound rows สร้าง layer ใหม่ด้วย `in_qty > 0`, `cost_per_unit`, `lot_no`, `lot_index`, `lot_seq_no`; outbound rows บริโภค layer ด้วย `out_qty > 0`, `from_lot_no` resolve โดย FIFO ordering บน `lot_seq_no`, และ `cost_per_unit` เลือกจาก layer ที่บริโภค (FIFO) หรือจาก current moving average (WA) แถวยังเก็บ `average_cost_per_unit` เพื่อให้ผู้บริโภค weighted-average อ่าน post-movement moving average โดยไม่ต้อง re-aggregate ประวัติทั้งหมด `at_period` (`YYMM`) และ `period_id` ผูก layer เข้ากับงวดบัญชีเพื่อให้ period-end rollup สามารถ sum activity ต่องวดได้

เอนทิตีนี้เป็นของโมดูล [inventory](/th/inventory/inventory) — สารบัญฟิลด์เต็มที่ [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 2.3 จากมุมมองของโมดูล costing: นี่คือตารางที่เอนจินอ่านทุก outbound (เพื่อเลือก `cost_per_unit`) และเขียนทุก inbound (เพื่อตั้ง `cost_per_unit` และคำนวณ `average_cost_per_unit` ใหม่)

**ฟิลด์ที่เกี่ยวข้องกับ costing:**

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยบน layer event นี้; default `0` สำหรับ inbound layer จาก GRN: **landed cost** `Round2((base_net_amount + base_extra_cost_amount) / (received_base_qty + foc_base_qty))` — เก็บที่ 5 ตำแหน่งแต่คำนวณที่ **2 ตำแหน่ง** (`inventory-transaction.service.ts:941,1134`); adjustment-in: ต้นทุนของเอกสาร สำหรับ outbound: ต้นทุนที่กฎ costing เลือก — ภายใต้ FIFO ต้นทุนของ layer ที่บริโภค; ภายใต้ WA ค่าเฉลี่ยของสินค้าตอน post ฟิลด์ canonical "หน่วยนี้ราคาเท่าไหร่" |
| `extra_cost_amount` | `Decimal @db.Decimal(20, 5)` | Yes | **ใหม่ 2026-09-10** (`20260910130000_add_cost_layer_extra_cost`) ส่วนของ `total_cost` ของ layer นี้ที่มาจาก extra cost ของการรับ (ค่าขนส่ง ค่าจัดการ ภาษีศุลกากร) ไม่ใช่จากตัวสินค้า ในสกุลเงินฐาน; default `0` เขียนครั้งเดียวตอนการรับโพสต์ (`splitByWeight(base_extra_cost_amount, layer quantities)`, `:971-974,996`) และไม่แก้ไขอีก — schema comment เรียกว่า "a record of a decision already made" `total_cost − extra_cost_amount` คือมูลค่าเฉพาะตัวสินค้า |
| `average_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Post-movement moving-average unit cost **ของสินค้าข้ามทุก location** (แก้ไข 2026-09-22); default `0` รีเฟรชโดย inbound ทุกครั้งภายใต้ WA และ **ประทับซ้ำลงทุก layer ที่ยังมีชีวิตแบบ non-direct ของสินค้า** (`:1236-1247`, `restampAverageCostForProducts` `:1521-1543`) เพื่อให้รายงานอ่านได้โดยไม่ต้องคำนวณใหม่ Outbound **ไม่** เปลี่ยนค่านี้ **ภายใต้ FIFO การรับ GRN เขียน `0` ที่นี่** (`:998`) — ไม่มี shadow average บน BU แบบ FIFO layer ของ direct location มีค่า `0` เสมอ |
| `lot_seq_no` | `Int` | Yes | เลขลำดับ **ภายในงวดสินค้าคงคลัง** (`getNextLotSeqNo(tx, atPeriod)` ใช้ `max(lot_seq_no) + 1` ในขอบเขต `at_period`, `:1399-1406`) ไม่ใช่ภายใน `(location, product)`; default `1` และเป็นเลขสี่หลักท้ายของ `lot_no` ด้วย `lot_seq_no` ต่ำกว่าถูกบริโภคก่อนภายใต้ FIFO รักษาข้ามขอบเขตงวดโดย `open_period` rollforward เพื่อให้ FIFO sequence รอดจากการ close |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวน variance ใช้สำหรับการปรับ credit-note-amount (vendor ลดราคาหลังรับ — `cost_per_unit` ของ lot ต้นทางคำนวณใหม่ตาม `INV_CALC_011`) และสำหรับ end-of-period price revaluation; default `0` carry cost-only variance ที่ไม่ขึ้นกับ `in_qty` / `out_qty` |
| `in_qty` / `out_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ฝั่งปริมาณของ layer event; `total_cost = (in_qty or out_qty) × cost_per_unit` Mutually exclusive ในแถวเดียวตาม `INV_VAL_007` |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `(in_qty − out_qty) × cost_per_unit` (signed); default `0` จำนวน journal-entry สำหรับ layer event |
| `transaction_type` | `enum_transaction_type` | Yes | Cost-flow classifier — `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period` ขับเคลื่อนกฎ cost-pick ที่เอนจินใช้ |
| `at_period` | `String @db.VarChar` | Yes | งวดในรูป `YYMM` (denormalised จาก `tb_inventory_period.period`) Costing aggregations group ตามคอลัมน์นี้เพื่อสร้าง COGS / valuation totals แบบ period-bounded |
| `period_id` | `String @db.Uuid` | Yes | FK ไป `tb_inventory_period.id` (`@relation`, `schema.prisma:1217`) — งวดสินค้าคงคลังที่บรรจุ layer event นี้ **แก้ไข 2026-09-22:** สำหรับ GRN งวดถูก resolve จาก `grn_date` **ตามช่วงวันที่** (`resolvePeriodForDate` → `findOpenPeriodForDate`, `inventory-period.helper.ts`) ไม่เคยอนุมานชื่อจากวันที่ และการเขียนจะ **throw** เมื่อไม่มีงวด `open`/`locked` ครอบคลุมวันที่นั้น; การ issue / adjustment ยังใช้งวดเปิดปัจจุบัน (`resolveCurrentPeriod`) |
| `lot_no` | `String @db.VarChar` | Yes | `<location_code><YYMM><ลำดับ 4 หลัก>` — เช่น `MK-0126070246` — จาก `buildLotNo()` (`common/helpers/lot-number.helper.ts:27-35`) **แก้ไข 2026-09-22:** ไม่ใช่ `RC{YY}{MM}{seq}`; ไม่มี prefix ตามประเภทเอกสาร; เหมือนกันในทุกประเภทการเคลื่อนไหว |

ฟิลด์อื่น (`lot_index`, `parent_lot_no`, `location_id`, `product_id`, audit columns) แสดงเต็มที่ [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 2.3

**Constraints ที่เกี่ยวข้องกับ costing:** `@@unique([lot_no, lot_index])` บังคับ lot identity; อัลกอริทึม cost-pick อาศัย `lot_seq_no` ordering ภายใน lot ของ location สำหรับ FIFO และ `average_cost_per_unit` ระดับสินค้าสำหรับ WA `cost_per_unit` และ `average_cost_per_unit` ไม่ติดลบตาม `INV_VAL_007`

### 2.2 tb_inventory_transaction_detail (per-line cost ledger)

**Per-product / per-lot ledger line** ภายใต้ movement carry `qty`, `cost_per_unit`, `total_cost`, location, lot-trace fields `from_lot_no` / `current_lot_no` และ — ตั้งแต่ `20260810180000_move_grn_lot_link_to_ledger` — `good_received_note_detail_item_id` คือเหตุการณ์รับที่แถว inbound นี้มาจาก (`NULL` สำหรับ adjustment / transfer / แถว legacy) โมดูล costing อ่าน row นี้เพื่อยืนยัน cost-per-unit ที่ post กับ source-document line เฉพาะ (แถว GRN carry `cost_per_unit` = **landed cost หลังจัดสรร extra cost หารด้วยปริมาณรับ + FOC** — ยืนยันว่าใช้งานจริง 2026-09-22; SR issue line carry `cost_per_unit = picked cost`); เป็นภาพ user-facing ของต้นทุน cost-layer และเป็นสิ่งที่ `GET …/good-received-notes/:id/stock-movements` คืนค่า

**ฟิลด์ที่เกี่ยวข้องกับ costing:**

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยตอน posting; default `0` สำหรับ inbound: layer cost (ขับเคลื่อน cost-layer row's `cost_per_unit`; GRN: `Round2((base_net_amount + ส่วนแบ่ง extra cost) / (received_base_qty + foc_base_qty))`); สำหรับ outbound: engine-picked cost **นี่คือค่าที่ปรากฏบนแท็บ Stock Movement ของ GRN** |
| `good_received_note_detail_item_id` | `String @db.Uuid` | Yes | FK ไป `tb_good_received_note_detail_item.id` (`@relation`, `schema.prisma:1135,1150`; index `inventorytransactiondetail_grndetailitemid_idx`) เหตุการณ์รับที่สร้างแถวนี้; id เดียวกันอาจปรากฏหลายแถวหากเหตุการณ์หนึ่งถูกแยกเป็นหลาย lot `NULL` = ไม่ได้มาจาก GRN |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Signed quantity ในหน่วยฐาน; บวก = inbound (สำหรับ GRN: `received_base_qty + foc_base_qty` — หน่วย FOC อยู่ในคลังที่ต้นทุนเจือจาง), ลบ = outbound คูณ `cost_per_unit` ได้ `total_cost` |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit` (signed); default `0` |
| `from_lot_no` | `String @db.VarChar` | Yes | Source lot consumed (outbound) ตั้งโดย FIFO pick — ชี้ไป lot ที่ `lot_seq_no` ต่ำสุดมี remaining balance |
| `current_lot_no` | `String @db.VarChar` | Yes | Lot ที่สร้างใหม่หรือได้รับผลกระทบ (inbound) Carry lot identity ของ layer ใหม่เข้า `lot_no` ของ cost-layer |

ฟิลด์อื่นและ constraints แสดงเต็มที่ [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 2.2

### 2.3 tb_inventory_period_snapshot (period-locked unit cost)

**เปลี่ยนชื่อ** จาก `tb_period_snapshot` โดย `20260916141000_rename_tb_period_to_tb_inventory_period` (พร้อมกับ `tb_period → tb_inventory_period`, `tb_period_comment → tb_inventory_period_comment`; HTTP path `/inventory-periods`, permission / licence key `system_admin.inventory_period`) **Locked opening / closing balance row** ต่อ `(period_id, location_id, product_id, lot_no, lot_index)` เขียนตอนปลายงวดเป็น audit anchor — **เฉพาะ business unit แบบ average เท่านั้น** (`period-end.close-average.helper.ts:480`) จากมุมมอง costing แถวนี้เป็น **คำตอบ period-end valuation** — carry `closing_qty`, `closing_cost_per_unit`, และ `closing_total_cost` ที่งบดุลและรายงาน food-cost ใช้

**ฟิลด์ที่เกี่ยวข้องกับ costing:**

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `opening_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Opening unit cost สำหรับงวด — โดยปกติคือ `closing_cost_per_unit` ของงวดก่อนหน้า |
| `opening_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `opening_qty × opening_cost_per_unit` Balance-sheet opening valuation |
| `receipt_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Sum ของ inbound `in_qty × cost_per_unit` ระหว่างงวด; default `0` |
| `issue_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Sum ของ outbound `out_qty × cost_per_unit` ระหว่างงวด — **COGS bucket** ที่ grain งวด × location × product × lot |
| `adjustment_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Net adjustment cost (sum ของ `adjustment_in / adjustment_out / credit_note_*` layers รวม `diff_amount`) |
| `closing_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Closing unit cost — สำหรับ WA period-end weighted average; สำหรับ FIFO `cost_per_unit` ของ residual lot (ตาม `INV_CALC_010`) |
| `closing_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `closing_qty × closing_cost_per_unit` Locked balance-sheet valuation; เขียนครั้งเดียวและไม่แก้ |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Variance bucket (โดยทั่วไปจาก physical-count adjustments ใน period); summed เข้า `adjustment_total_cost` |

ฟิลด์อื่นแสดงที่ [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 2.7

### 2.4 tb_business_unit.calculation_method (costing-method configuration — platform)

**การตั้งค่าวิธี costing** อยู่ที่ระดับ business-unit (property / hotel) บน **platform schema** ไม่ใช่บน tenant schema และไม่ใช่บน product ค่าเดียวใช้กับทุก product ที่ business unit นั้น

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `calculation_method` | `enum_calculation_method` | No | วิธี costing สำหรับ business unit ค่า: `average` (Weighted Average — default), `fifo` (First-In-First-Out) อ่านโดย inventory cost-layer post engine ทุก outbound เพื่อตัดสินกฎ cost-pick |

`tb_business_unit` defined ใน `prisma-shared-schema-platform/prisma/schema.prisma:191` (ไม่ใช่ใน tenant schema ที่ `tb_inventory_transaction_cost_layer` อยู่) Cost-layer post engine อ่านค่านี้ด้วย `bu_code` ของ request (`getCalculationMethod(bu_code)`, `inventory-transaction.service.ts:402-408` และ fallback เป็น `fifo` เมื่อแถวไม่มีค่า) และ apply กฎที่เลือกกับ cost-layer write Tenant schema's `enum_business_unit_config_key` enumerate `calculation_method` เป็น config key — surface runtime-config parallel (key/value rows) ที่เอนจิน **ไม่ได้** อ่าน โมดูล GRN ก็อ่านวิธีนี้ด้วย (`postsInventoryAtSave()`) เพื่อตัดสินว่าการรับจะโพสต์ตอน save (average) หรือ commit (FIFO)

### 2.5 tb_product.standard_cost (reference cost on the product)

**Product's reference / standard cost** ใช้โดย `standard` count-costing method (`enum_physical_count_costing_method = standard` — count variance ถูกตีมูลค่าที่ product's `standard_cost` แทนที่จะเป็น cost-layer cost) และโดย recipe baseline costing

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `standard_cost` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนอ้างอิง / standard cost ต่อหน่วยในหน่วยฐาน; default `0` อัปเดตโดย Finance / cost-controller cadence (โดยปกติรายเดือนหรือรายไตรมาส) **ไม่** ใช้โดย FIFO / WA cost-pick engine — engine นั้นอ่าน cost-layer's `cost_per_unit` / `average_cost_per_unit` |
| `price_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | เพดานเป็น **เปอร์เซ็นต์** บังคับใช้ (ตั้งแต่ 2026-08) โดย checklist การ save ของ GRN: ราคารับต่อหน่วยฐานเกิน `order_price` ต่อหน่วยฐานของ PO ได้ไม่เกินเปอร์เซ็นต์นี้ (`good-received-note.deviation.ts:98-116`); `0` / `NULL` = ไม่มีเพดาน ไม่ถูกใช้โดย cost-pick engine เอง |
| `qty_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | เพดานเป็น **เปอร์เซ็นต์** ของ `received_base_qty` ที่เกิน `order_base_qty` บังคับใช้ตอน GRN save (`deviation.ts:125-134`); การรับขาดไม่มีวันละเมิด |

`tb_product` documented เต็มภายใต้โมดูล [product](/th/inventory/product); entry นี้ครอบคลุม subset ที่เกี่ยวข้องกับ costing

### 2.7 endpoint อ่านต้นทุน (gateway `application/cost`)

ไม่ใช่ตาราง แต่เป็น API surface เฉพาะ costing เพียงแห่งเดียว (`apps/backend-gateway/src/application/cost/cost.controller.ts`, micro-business `src/inventory/costing/`; Bruno `_uncategorized/cost/`) ทั้งหมดเป็น read-only, `KeycloakGuard` + `AppIdGuard`:

| Endpoint | Guard key | คืนค่า |
| -------- | --------- | ------- |
| `GET /api/:bu_code/cost/products/:product_id/location/:location_id/qty/:qty` | `product.cost-estimate` | ประมาณการต้นทุนสำหรับการ issue `qty` จาก location นั้นภายใต้วิธีของ BU |
| `GET /api/:bu_code/cost/products/:product_id/last-receiving` | `product.last-receiving` | การรับ GRN ล่าสุดของสินค้า |
| `GET /api/:bu_code/cost/products/:product_id/last-cost` | `product.last-cost` | inbound ล่าสุด (`good_received_note` **หรือ** `stock_in`) — "ต้นทุนล่าสุดไม่ว่าจะมาจากแหล่งรับใด" |
| `GET /api/:bu_code/cost/products/:product_id/last-receiving/unit/:unit_id` | `product.last-receiving-by-unit` | GRN ล่าสุดที่รับในหน่วยนั้น, `cost_per_unit = net_amount / received_qty` (ต่อหน่วยที่รับ, **ก่อน** extra cost); `{}` หากไม่เคยรับในหน่วยนั้น |

**Cost centre (`tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account`, `20260904103000_add_cost_center`)** **ไม่ได้** เชื่อมกับ costing: ไม่มีตาราง inventory หรือ costing ใดพก `cost_center_id` — FK เดียวคือ `tb_gl_jv_detail.cost_center_id` (`schema.prisma:4505`); แถว inventory พกเพียง JSON array `dimension` แบบอิสระเท่านั้น

### 2.6 enum_physical_count_costing_method (count-variance valuation source)

Enum สี่ค่าที่เลือก **แหล่งต้นทุนที่ feed count-driven variance posts** เมื่อ physical-count หรือ spot-check เสร็จด้วย variance นี่เป็น costing-specific concern เพราะ count adjustments (`adjustment_in` / `adjustment_out`) ต้องการ `cost_per_unit` เพื่อคำนวณ `total_cost` และแหล่งของต้นทุนนั้นต่างกันตาม tenant preference

| Value | แหล่งต้นทุน |
| ----- | ----------- |
| `standard` | Product's `tb_product.standard_cost` ใช้โดย tenant ที่ต้องการให้ count variance ถูกตีมูลค่าที่ reference cost โดยไม่คำนึงถึงราคารับล่าสุด |
| `last` | Cost-layer ล่าสุด `cost_per_unit` ที่ `(location_id, product_id)` โดยไม่คำนึงถึงทิศทาง ประมาณ "current market cost" |
| `average` | `average_cost_per_unit` ปัจจุบันของสินค้า สำหรับ BU แบบ WA เท่ากับ running average; บน BU แบบ FIFO การรับ GRN เขียน `0` ลงคอลัมน์นั้น (ไม่มี shadow average — แก้ไข 2026-09-22) ตัวเลือกนี้จึงมีความหมายเฉพาะบน BU แบบ average |
| `last_receiving` | Inbound layer ล่าสุดของ `cost_per_unit` (filtered ไป `transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`) ประมาณ "last price we paid" |

ตั้งค่าต่อ business unit (โดยปกติผ่าน `tb_business_unit_config_key = physical_count_costing_method`) อ่านโดย count-variance posting code ตอนเขียน `tb_stock_in` / `tb_stock_out` document ที่ derived จาก count ที่เสร็จ

## 3. ความสัมพันธ์

```
tb_business_unit (platform schema)
    │  calculation_method ∈ {average, fifo}  ── single costing method per business unit
    │
    │  Read by the cost-layer post engine via the request's bu_code (getCalculationMethod).
    │  No Prisma @relation to tenant entities — cross-schema reference.
    ▼

tb_inventory_transaction  (info JSON on GRN headers: { posted_at_save, po_receiving_applied })
    │ * inventory_transaction_id
    ▼
tb_inventory_transaction_detail
    │  cost_per_unit (landed cost, 2 dp)
    │  qty (signed) ── total_cost = qty × cost_per_unit  (GRN: qty = received + FOC)
    │  good_received_note_detail_item_id ──► tb_good_received_note_detail_item (receipt event)
    │
    │ * inventory_transaction_detail_id
    ▼
tb_inventory_transaction_cost_layer  (canonical cost-flow record)
    │  cost_per_unit            ── layer cost (FIFO: per-lot; WA: per-event)
    │  extra_cost_amount        ── share of total_cost that is freight/duty (GRN only, 2026-09-10)
    │  average_cost_per_unit    ── product-wide moving average (WA units; 0 on FIFO receipts)
    │  lot_no = <location_code><YYMM><lot_seq_no>
    │  lot_seq_no               ── period-scoped run number; FIFO consumes lowest-first
    │  diff_amount              ── credit-note-amount / EOP revaluation variance
    │  in_qty / out_qty         ── direction; mutually exclusive
    │  transaction_type ∈ {good_received_note, transfer_in, transfer_out,
    │                       issue, adjustment_in, adjustment_out,
    │                       credit_note_amount, credit_note_quantity,
    │                       eop_in, eop_out, close_period, open_period}
    │  at_period (YYMM) / period_id ── ties layer to the inventory period
    │
    └──► tb_inventory_period   (period_id → close_period / open_period rollforward anchor)


tb_product
    │  standard_cost           ── reference cost (used by count-costing-method = standard)
    │  price_deviation_limit   ── percent ceiling enforced at GRN save
    │  qty_deviation_limit     ── percent ceiling enforced at GRN save
    │
    │  No per-product costing_method field — single method per business unit.
    │
    │ * product_id (no @relation declared on cost-layer / detail)
    ▼
tb_inventory_transaction_cost_layer / tb_inventory_transaction_detail
    (cost-layer rows reference product_id but no Prisma @relation)


tb_inventory_period ──1──*──► tb_inventory_period_snapshot
                                         (locked period × location × product × lot
                                          opening / receipt / issue / adjustment /
                                          closing cost columns — the period-end
                                          valuation anchor; average units only)
```

หมายเหตุ:

- **Configuration cross-schema gap.** ค่า enum วิธี costing อยู่บน `tb_business_unit.calculation_method` ใน **platform** schema แต่ cost-layer rows ที่บริโภคอยู่ใน **tenant** schema ไม่มี Prisma `@relation` bridging; เอนจิน resolve ด้วย `bu_code` ของ request (`getCalculationMethod(bu_code)`) เส้นทางอ่านของโมดูล costing คือ: `(tenant: inventory transaction post) → (bu_code) → (platform query: tb_business_unit.calculation_method) → apply cost-pick rule`
- **Runtime-config key ไม่ถูกเอนจินอ่าน.** `enum_business_unit_config_key.calculation_method` มีอยู่ แต่ `getCalculationMethod` อ่านเฉพาะคอลัมน์ platform (`inventory-transaction.service.ts:402-408`) ให้ถือว่า config key นี้ไม่ถูกใช้สำหรับ costing จนกว่าจะมีผู้อ่านปรากฏ
- **ค่าเฉลี่ยเป็นระดับสินค้า.** `getNetTotals` / `restampAverageCostForProducts` กรองด้วย `product_id` เท่านั้น; การรับที่ location หนึ่งเปลี่ยนค่าเฉลี่ยที่ใช้สำหรับการ issue ที่ทุก location ของ business unit
- **ไม่มี `tb_costing_*` entity.** โมดูล costing เป็น **ชั้นพฤติกรรมเหนือ inventory entities** ไม่ใช่ document tree ของตัวเอง การเก็บ cost บน row เดียวกับ qty (บน `tb_inventory_transaction_cost_layer`) หมายความว่าไม่สามารถมีการ drift ระหว่าง qty ledger และ cost ledger — เป็น ledger เดียวกัน
- **Cost-pick is movement-time, not query-time.** เมื่อ outbound post engine resolve cost ตอน post และเขียนไป cost-layer's `cost_per_unit` การอ่าน row ในภายหลังคืนค่า historical cost — แม้วิธีที่ตั้งค่าจะเปลี่ยน posted rows คงต้นทุนที่เลือกภายใต้วิธีที่ใช้ ณ ตอน
- **Period-snapshot คือคำตอบที่ล็อก.** เมื่อ `tb_inventory_period_snapshot.closing_cost_per_unit` เขียนโดย `INV_POST_009` (period close, BU แบบ average) valuation ของงวดเป็น immutable; การแก้ไขงวดที่ปิดแล้วในภายหลังโพสต์เป็น restatement ในงวดเปิดถัดไป ไม่ใช่การแก้ snapshot
- **`standard_cost` เป็น reference-only.** **ไม่** ขับเคลื่อน FIFO หรือ WA cost-pick ขับเคลื่อน `standard` count-costing method และ recipe baseline costing

## 4. Enums

- **`enum_calculation_method`** (platform schema, `prisma-shared-schema-platform/prisma/schema.prisma:133-136`): costing-method classifier บน `tb_business_unit.calculation_method` สองค่า default `average`:
  - `average` — Weighted Average Moving average เดียว **ต่อสินค้า** (ทุก location) รีเฟรชทุก inbound ตาม `INV_CALC_007`; outbound บริโภคที่ค่าเฉลี่ยที่มีอยู่ตาม `INV_CALC_006` และทำให้ GRN โพสต์การเคลื่อนไหวสต๊อกตอน **save** ด้วย
  - `fifo` — First-In, First-Out Lot บริโภคตาม `lot_seq_no` ascending ตาม `INV_CALC_005`; แต่ละ lot ที่บริโภคผลิต outbound cost-layer row ของตัวเองที่ `cost_per_unit` GRN โพสต์ตอน **commit**
  - หมายเหตุ: **tenant** schema ประกาศ `enum_calculation_method { FIFO, AVG }` แยกต่างหาก (`prisma-shared-schema-tenant/prisma/schema.prisma:39-42`); เอนจิน import enum ของ platform และไม่เคยอ่านของ tenant
- **`enum_business_unit_config_key`** (tenant schema): enumerate runtime-config keys บน `tb_business_unit_config_key` rows ค่าที่เกี่ยวข้องกับ costing:
  - `calculation_method` — ประกาศไว้ แต่ **เอนจิน costing ไม่ได้อ่าน** (ดูหมายเหตุ § 3)
  - `physical_count_costing_method` — เลือกแหล่งต้นทุนสำหรับ count-driven variance posts
  - `amount`, `quantity`, `recipe` — formatting / precision config keys
- **`enum_physical_count_costing_method`** (tenant schema): แหล่งตีมูลค่า count-variance สี่ค่า ไม่มี schema default declared:
  - `standard` — ตีมูลค่า count variance ที่ `tb_product.standard_cost`
  - `last` — ที่ cost-layer `cost_per_unit` ล่าสุด ที่ key `(location, product)` โดยไม่คำนึงถึงทิศทาง
  - `average` — ที่ `average_cost_per_unit` ล่าสุด (running WA)
  - `last_receiving` — ที่ inbound layer ล่าสุดของ `cost_per_unit`
- **`enum_transaction_type`** (tenant schema): cost-flow effect บน `tb_inventory_transaction_cost_layer.transaction_type` มี 12 ค่าตาม [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 4 subset ที่ engine-relevant:
  - `good_received_note` / `transfer_in` / `adjustment_in` — inbound layer events ที่ engine เขียน `cost_per_unit` สด (และคำนวณ `average_cost_per_unit` ใหม่สำหรับ WA)
  - `issue` / `transfer_out` / `adjustment_out` — outbound events ที่ engine เลือก cost (FIFO หรือ WA)
  - `credit_note_amount` — vendor concession ปรับ `cost_per_unit` บน lot ที่มีอยู่ผ่าน `diff_amount` (ตาม `INV_CALC_011`)
  - `credit_note_quantity` — outbound บริโภคจาก lot ของ receipt ต้นทางที่ `cost_per_unit` ของ lot
  - `eop_in` / `eop_out` — end-of-period rollforward
  - `close_period` / `open_period` — period-anchor rows; cost เก็บรักษาข้ามขอบเขต

## 5. ความแตกต่างจาก carmen/docs

Carmen/docs costing reference (`../carmen/docs/costing/enhanced-costing-engine.md`) และ sibling [`calculation-methods.md`](./calculation-methods.md) อธิบาย model ที่รวยกว่า Prisma reality — โดยเฉพาะ per-product costing-method configuration และ separate `inventory_lot` / `inventory_balance` schema ที่ platform ไม่มี Cross-checking กับ canonical Prisma schemas ให้ความแตกต่างดังนี้:

| # | รายการ | carmen/docs (หรือ sibling calculation-methods.md) ระบุ | Prisma มี | การดำเนินการ |
|---|------|------------------------------------------------------|------------|--------|
| 1 | Costing-method configuration scope | `calculation-methods.md` § 6.1 ระบุการตั้งค่า "ที่ระดับ **organization or product category**" — หมายถึงวิธี costing per-product หรือ per-category พร้อมคอลัมน์ `product_category.costing_method` และ `organization_settings.costing_method` | **Per business unit เท่านั้น** `tb_business_unit.calculation_method ∈ {average, fifo}` (platform schema, default `average`) — ค่าเดียวใช้กับทุก product ที่ business unit นั้น **ไม่มีคอลัมน์ per-product หรือ per-category** บน `tb_product`, `tb_product_category`, `tb_product_sub_category` หรือ `tb_product_item_group` | ถือ Prisma เป็น canonical: platform รองรับ **วิธี costing หนึ่งวิธีต่อ business unit (property / hotel)** ไม่ใช่ต่อ product หรือ category อัปเดต `calculation-methods.md` § 6.1 และ framing per-product ใด ๆ ให้ระบุว่า mixed methods ข้าม products ที่ business unit เดียวกัน **ไม่รองรับ** โดย schema |
| 2 | Separate `inventory_lot` schema | `calculation-methods.md` § 2.3 อธิบายตาราง `inventory_lot` พร้อม `lot_id`, `product_id`, `warehouse_id`, `purchase_date`, `quantity`, `unit_cost` เป็น entity dedicated lot-tracking | **ไม่มี `tb_inventory_lot` model** Lot identity อยู่บน `tb_inventory_transaction_cost_layer.(lot_no, lot_index)` (ด้วย `@@unique([lot_no, lot_index])`) และ lot quantity คือ derived เป็น `Σ (in_qty − out_qty)` สำหรับ lot ตั้งแต่ period snapshot ล่าสุด | อัปเดต `calculation-methods.md` § 2.3 เพื่อสะท้อนว่า lots แสดงเป็น logical grouping ของ cost-layer rows โดย `(lot_no, lot_index)` ไม่ใช่ entity แยก |
| 3 | Separate `inventory_balance` schema (WA path) | `calculation-methods.md` § 3.3 อธิบายตาราง `inventory_balance` พร้อม `product_id`, `warehouse_id`, `quantity`, `average_cost`, `total_value` เป็น per-product / per-location running balance สำหรับ WA | **ไม่มี `tb_inventory_balance` model** Running average อยู่บน `tb_inventory_transaction_cost_layer.average_cost_per_unit` บน layer event **ล่าสุด** ที่ key `(location_id, product_id)` | อัปเดต `calculation-methods.md` § 3.3 ให้ document ว่า WA running state อยู่บน cost-layer ledger |
| 4 | Per-product `costing_method` column on `tb_product` | *(แก้ไขแล้ว 2026-07-22 — รายการประวัติ เก็บไว้เพื่อ audit trail)* ฉบับร่างก่อนหน้าของ `inventory/01-data-model.md` § 5 item 4 เคยระบุ: "Costing method per product อยู่บน model **product** (`tb_product`) — ไม่ใช่ inventory" | **ไม่มีคอลัมน์ `costing_method` บน `tb_product`** Costing method อยู่บน `tb_business_unit.calculation_method` (item 1 ข้างต้น) | แก้ไขแล้ว — [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 5 item 4 ถูกเขียนใหม่ในรอบ resync ของโมดูล inventory เมื่อ 2026-07-15 และตอนนี้ระบุว่า method เป็นระดับ BU ทั้งหมด ไม่มี override ต่อสินค้า ตรงกับหน้านี้แล้ว ไม่ต้องทำอะไรเพิ่ม |
| 5 | Strategy-pattern architecture | `calculation-methods.md` § 6.2 อธิบาย `InventoryCostingStrategy` interface พร้อม `FIFOStrategy` และ `AverageCostStrategy` implementations | สถาปัตยกรรมตรงกับ strategy pattern แต่ **strategy resolve per business unit ไม่ใช่ per product** | อัปเดต `calculation-methods.md` § 6.2 ให้ document resolution scope (business unit ไม่ใช่ product) |
| 6 | `physical_count_costing_method` (count-variance source) | ไม่ระบุใน `calculation-methods.md` หรือ `enhanced-costing-engine.md` | `enum_physical_count_costing_method ∈ {standard, last, average, last_receiving}` เป็น costing-relevant enum (Section 2.6 ข้างต้น) | เพิ่ม §6.x หรือ §7 ใน `calculation-methods.md` covering count-variance valuation source |
| 7 | `diff_amount` (credit-note variance) | ไม่ระบุใน carmen/docs costing reference | `tb_inventory_transaction_cost_layer.diff_amount` carry cost-only variance สำหรับ credit-note-amount adjustments และ end-of-period revaluation | เพิ่มใน `calculation-methods.md` |
| 8 | Enhanced costing engine scope | `../carmen/docs/costing/enhanced-costing-engine.md` อธิบาย **portion-based / recipe-cost / dynamic-pricing** engine | Prisma costing surface ครอบคลุม **inventory valuation เท่านั้น** — FIFO / WA cost-pick บน `tb_inventory_transaction_cost_layer`, period-end snapshot บน `tb_inventory_period_snapshot` | ถือทั้งสองเป็น concerns แยก |
| 9 | "Cost layer" naming vs "lot" naming | `calculation-methods.md` ใช้ "lot" ตลอด Prisma ใช้ "cost layer" (`tb_inventory_transaction_cost_layer`) — broader term | A **lot** ใน carmen/docs ≅ a group of cost-layer rows sharing `(lot_no, lot_index)` | คง "lot" เป็น user-facing term แต่ document ว่า one lot internally คือ collection ของ cost-layer rows |
| 10 | Rounding and precision | `calculation-methods.md` § 6.4 ระบุ "Rounding: Round per lot" (FIFO) และ "Risk of accumulated errors - use high precision" (WA) | คอลัมน์เป็น `Decimal(20, 5)` แต่ **เอนจินปัดต้นทุนต่อหน่วยเป็น 2 ตำแหน่ง** — `cost_per_unit = Math.round(x × 100) / 100` (`inventory-transaction.service.ts:941,1134`), `calculateNewAverageCost` คืน 2 ตำแหน่ง (`inventory-cost.formula.ts:100`), `splitFifoCost(qty, totalCost, 2)` กระทบยอด layer ให้ตรงยอดรวม 2 ตำแหน่งพอดี สาย money chain ของ GRN ต้นน้ำเป็น 5 ตำแหน่ง | Document ความละเอียดจริง: 5 ตำแหน่งบนเอกสาร 2 ตำแหน่งบนต้นทุนต่อหน่วยของ ledger คำแนะนำ "use high precision" ของ `calculation-methods.md` ไม่ใช่สิ่งที่โค้ดทำ |
| 11 | Extra-cost allocation | `calculation-methods.md` / carmen/docs ถือว่า landed cost อยู่นอกขอบเขต; หน้า GRN รอบ 2026-07-15 ระบุการจัดสรรว่า "ยังไม่ยืนยัน" | **ใช้งานจริงตั้งแต่ 2026-09-10:** `allocateExtraCost()` แบ่ง extra cost ของการรับไปยังแต่ละบรรทัด (`by_qty` เท่ากัน, `by_value` ตามปริมาณสต๊อก, `manual` ไม่แบ่ง) และแต่ละ cost layer เก็บ `extra_cost_amount` ของตัวเอง | เพิ่ม landed cost ในคำอธิบายอัลกอริทึม; หมายเหตุว่าชื่อโหมดสวนทางกับพฤติกรรม |
| 12 | ขอบเขตของค่าเฉลี่ย | `calculation-methods.md` § 3 และเวอร์ชันก่อนของหน้านี้: ค่าเฉลี่ยต่อ `(warehouse / location, product)` | **ต่อสินค้าข้ามทุก location** (`getNetTotals(tx, productId)`); location ใช้เฉพาะการตรวจ on-hand | แก้ไขขอบเขตทุกที่ที่ระบุไว้ |
| 13 | ตารางงวด | `tb_period`, `tb_period_snapshot` | เปลี่ยนชื่อเป็น `tb_inventory_period`, `tb_inventory_period_snapshot`, `tb_inventory_period_comment` (`20260916141000`); HTTP `/inventory-periods`; permission `system_admin.inventory_period` | เปลี่ยนชื่อในทุกหน้าที่อ้างชื่อเดิม |

## 6. References

- **Primary (source of truth):**
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — tenant entities (`tb_inventory_transaction_cost_layer` `:1177-1221`, `tb_inventory_transaction_detail` `:1122-1155`, `tb_inventory_period_snapshot` `:1298`, `tb_product`), tenant enums (`enum_business_unit_config_key`, `enum_physical_count_costing_method`, `enum_transaction_type`); migration `20260910130000_add_cost_layer_extra_cost`, `20260810180000_move_grn_lot_link_to_ledger`, `20260916141000_rename_tb_period_to_tb_inventory_period`
  - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (`createFromGoodReceivedNote` `:841`, `createFifoTransaction` `:893`, `createAverageTransaction` `:1051`, `getNetTotals` `:1487`, `restampAverageCostForProducts` `:1521`), `apps/micro-business/src/common/helpers/inventory-cost.formula.ts`, `lot-number.helper.ts`, `fifo-cost-split.helper.ts`
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — platform entity `tb_business_unit.calculation_method` และ platform enum `enum_calculation_method`
- **Secondary (concept cross-check):**
  - `../carmen/docs/costing/enhanced-costing-engine.md`
  - Sibling: [calculation-methods.md](./calculation-methods.md)
- Related modules: [inventory](/th/inventory/inventory) (ledger cost-layer อยู่ในโมดูล inventory; หน้านี้บันทึกมุมมองเอนจิน costing ของแถวเดียวกัน; schema inventory ฉบับเต็มที่ [inventory/01-data-model](/th/inventory/inventory/01-data-model)), [good-receive-note](/th/inventory/good-receive-note) (แหล่ง inbound หลัก — GRN commit หรือ save บน BU แบบ average เขียน inbound cost layer ด้วย landed cost ของการรับ), [store-requisition](/th/inventory/store-requisition) (แหล่ง outbound หลัก — SR issue จุดชนวน cost-pick), [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) (count-variance posts ใช้ `enum_physical_count_costing_method` เลือกแหล่งต้นทุน variance), [inventory-adjustment](/th/inventory/inventory-adjustment) (การปรับ `tb_stock_in` / `tb_stock_out` ด้วยมือ — สร้างเป็น `draft` โพสต์ด้วย `PATCH …/commit`; `adjustment_type_id` เป็นเพียง reason code และไม่ขับ GL routing ใด — โมดูล GL ไม่ถูกเรียกจากโค้ด inventory), [recipe](/th/inventory/recipe) (ผู้บริโภคปลายน้ำ — recipe costing อ่าน cost basis ต่อสินค้าที่เอนจินรักษาไว้), [product](/th/inventory/product) (พก `standard_cost` ต้นทุนอ้างอิงและเพดาน deviation; **ไม่** พกวิธี costing ตาม Section 5 item 4)
