---
title: การคำนวณต้นทุน — แบบจำลองข้อมูล (Costing — Data Model)
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum สำหรับโมดูล costing
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน — แบบจำลองข้อมูล

> **At a Glance**
> **ตาราง:** `tb_inventory_transaction_cost_layer` &nbsp;·&nbsp; `tb_inventory_transaction_detail` &nbsp;·&nbsp; `tb_period_snapshot` &nbsp;·&nbsp; `tb_business_unit.calculation_method` &nbsp;·&nbsp; `tb_product.standard_cost`
> **กลุ่มผู้ใช้:** นักพัฒนา / Auditor (เอกสารอ้างอิงนักพัฒนา)
> **FK สำคัญ:** cost-layer `→ tb_inventory_transaction_detail`; cost-layer `→ tb_period`; การเชื่อม cross-schema: tenant cost-layer อ่าน platform `tb_business_unit.calculation_method` ผ่าน JWT `x-app-id` (ไม่มี Prisma `@relation`)
> **รูปแบบ audit:** มาตรฐาน `created_*` / `updated_*` / `deleted_*` บน cost-layer และ snapshot; **`tb_inventory_transaction_detail` ไม่มี soft-delete** — การกลับรายการ post compensating row แทน

> **แหล่งข้อมูลอ้างอิงหลัก:** Prisma schema ฝั่ง backend อ่านไฟล์เหล่านี้ก่อนเสมอเมื่อเขียนหรือปรับปรุงหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ในแต่ละ package เป็นไฟล์ที่ถูกสร้างขึ้นอัตโนมัติ ไม่ใช่แหล่งอ้างอิง

## 1. ภาพรวม

โมดูล Costing **ไม่ใช่ document tree แยกต่างหาก** ในแบบเดียวกับ GRN, PR หรือ SR แต่เป็น **สัญญา read-and-write ที่วางทับ inventory transaction ledger**: เอนจินอ่าน `tb_inventory_transaction_detail` และ `tb_inventory_transaction_cost_layer` เพื่อเลือกต้นทุนสำหรับการเคลื่อนไหวขาออก เขียน `cost_per_unit` / `average_cost_per_unit` ลงบนแถว cost-layer ตอน post และอ่านกลับจากแถวเดียวกันเมื่อผู้บริโภคปลายน้ำ (recipe costing, financial reporting, valuation) ต้องการต้นทุนต่อหน่วย ไม่มี `tb_costing_*` model ใน Prisma schema — ข้อมูล costing อยู่บนเอนทิตี inventory (`tb_inventory_transaction_cost_layer` คือ canonical cost-flow record, `tb_inventory_transaction_detail.cost_per_unit` คือต้นทุนต่อบรรทัด, `tb_period_snapshot.closing_cost_per_unit` คือต้นทุนต่อหน่วยที่ล็อกปลายงวด) และ **การตั้งค่าวิธี costing** อยู่ที่ระดับสูงกว่าหนึ่งระดับที่ **business unit** ใน platform schema ไม่ใช่ที่ product

สมมติฐาน cost-flow — **FIFO** (lot ถูกบริโภคตาม `lot_seq_no` ascending แต่ละ lot มี `cost_per_unit` ของตัวเอง) หรือ **Weighted Average** (moving-average เดียวต่อ `(location_id, product_id)` รีเฟรชทุกการรับเข้า) — ตั้งค่าบน `tb_business_unit.calculation_method` (`enum_calculation_method = average | fifo`, default `average`) ที่ระดับ property ของ tenant schema `enum_business_unit_config_key` เปิดเผย `calculation_method` เป็น runtime config key และ `enum_physical_count_costing_method` (`standard`, `last`, `average`, `last_receiving`) เลือกแหล่งต้นทุนที่ feed count-driven variance posts สินค้าเอง (`tb_product`) มี `standard_cost` (ต้นทุนอ้างอิงที่ใช้โดย `standard` count-costing method และ recipe baselining) และ `price_deviation_limit` / `qty_deviation_limit` (tolerance bands ที่ใช้โดยกฎ procurement / receiving) แต่ **ไม่มี** วิธี costing ต่อสินค้า — นี่เป็นการ simplify ระดับแพลตฟอร์มที่จงใจ ดูเอกสารใน Section 5

เอนจินทำงานแบบ **per-transaction ไม่ใช่ periodic batch** เมื่อโมดูล inventory post inbound `tb_inventory_transaction_cost_layer` row เอนจินจะเขียน `cost_per_unit` (layer cost), คำนวณ `average_cost_per_unit` ใหม่สำหรับ weighted-average และกำหนด `lot_seq_no` สำหรับ FIFO ordering เมื่อ outbound movement post เอนจินอ่านวิธีที่ตั้งค่าไว้ เลือกต้นทุน (FIFO บริโภคจาก `lot_seq_no` ascending; WA อ่าน `average_cost_per_unit` ล่าสุด) และเขียนแถว outbound `out_qty × cost_per_unit` ที่สอดคล้อง ที่ปลายงวด เอนจินเขียน `closing_cost_per_unit` บน `tb_period_snapshot` และ cost-layer rows `transaction_type = close_period` / `open_period` ที่ยึดต้นทุนต่อหน่วยตอนข้ามขอบเขตงวด [`calculation-methods.md`](./calculation-methods.md) ที่เป็นเอกสารพี่น้องเจาะลึกอัลกอริทึม FIFO / WA และคำแนะนำการออกแบบ strategy-pattern ของแพลตฟอร์ม; หน้านี้คือสารบัญระดับ schema

## 2. เอนทิตี

### 2.1 tb_inventory_transaction_cost_layer (canonical cost record)

**Cost-flow ledger row** — แหล่งความจริงเดียวสำหรับ "หน่วยนี้ราคาเท่าไหร่?" ณ ทุกจุดเวลา หนึ่งแถวต่อ layer event ต่อ movement: inbound rows สร้าง layer ใหม่ด้วย `in_qty > 0`, `cost_per_unit`, `lot_no`, `lot_index`, `lot_seq_no`; outbound rows บริโภค layer ด้วย `out_qty > 0`, `from_lot_no` resolve โดย FIFO ordering บน `lot_seq_no`, และ `cost_per_unit` เลือกจาก layer ที่บริโภค (FIFO) หรือจาก current moving average (WA) แถวยังเก็บ `average_cost_per_unit` เพื่อให้ผู้บริโภค weighted-average อ่าน post-movement moving average โดยไม่ต้อง re-aggregate ประวัติทั้งหมด `at_period` (`YYMM`) และ `period_id` ผูก layer เข้ากับงวดบัญชีเพื่อให้ period-end rollup สามารถ sum activity ต่องวดได้

เอนทิตีนี้เป็นของโมดูล [[inventory]] — สารบัญฟิลด์เต็มที่ [[inventory/01-data-model]] § 2.3 จากมุมมองของโมดูล costing: นี่คือตารางที่เอนจินอ่านทุก outbound (เพื่อเลือก `cost_per_unit`) และเขียนทุก inbound (เพื่อตั้ง `cost_per_unit` และคำนวณ `average_cost_per_unit` ใหม่)

**ฟิลด์ที่เกี่ยวข้องกับ costing:**

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยบน layer event นี้; default `0` สำหรับ inbound layer: ต้นทุน GRN / adjustment-in สำหรับ outbound: ต้นทุนที่กฎ costing เลือก — ภายใต้ FIFO ต้นทุนของ layer ที่บริโภค; ภายใต้ WA moving average ตอน post ฟิลด์ canonical "หน่วยนี้ราคาเท่าไหร่" |
| `average_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Post-movement moving-average unit cost ที่ `(location_id, product_id)`; default `0` รีเฟรชโดย inbound ทุกครั้งภายใต้ WA Outbound **ไม่** เปลี่ยนค่านี้ (บริโภคที่ค่าเฉลี่ยที่มีอยู่แต่ไม่ re-blend) สำหรับ FIFO-only products คอลัมน์นี้เป็นข้อมูล; สำหรับ WA เป็น "current average" canonical ที่ outbound ถัดไปเลือก |
| `lot_seq_no` | `Int` | Yes | FIFO ordering anchor ภายใน `(location_id, product_id)`; default `1` `lot_seq_no` ต่ำกว่าถูกบริโภคก่อนภายใต้ FIFO รักษาข้ามขอบเขตงวดโดย `open_period` rollforward เพื่อให้ FIFO sequence รอดจากการ close ข้อมูลสำหรับ WA-configured products |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | จำนวน variance ใช้สำหรับการปรับ credit-note-amount (vendor ลดราคาหลังรับ — `cost_per_unit` ของ lot ต้นทางคำนวณใหม่ตาม `INV_CALC_011`) และสำหรับ end-of-period price revaluation; default `0` carry cost-only variance ที่ไม่ขึ้นกับ `in_qty` / `out_qty` |
| `in_qty` / `out_qty` | `Decimal @db.Decimal(20, 5)` | Yes | ฝั่งปริมาณของ layer event; `total_cost = (in_qty or out_qty) × cost_per_unit` Mutually exclusive ในแถวเดียวตาม `INV_VAL_007` |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `(in_qty − out_qty) × cost_per_unit` (signed); default `0` จำนวน journal-entry สำหรับ layer event |
| `transaction_type` | `enum_transaction_type` | Yes | Cost-flow classifier — `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period` ขับเคลื่อนกฎ cost-pick ที่เอนจินใช้ |
| `at_period` | `String @db.VarChar` | Yes | งวดในรูป `YYMM` (denormalised จาก `tb_period.period`) Costing aggregations group ตามคอลัมน์นี้เพื่อสร้าง COGS / valuation totals แบบ period-bounded |
| `period_id` | `String @db.Uuid` | Yes | FK ไป `tb_period.id` — งวดบัญชีที่บรรจุ layer event นี้ |

ฟิลด์อื่น (`lot_no`, `lot_index`, `parent_lot_no`, `location_id`, `product_id`, audit columns) แสดงเต็มที่ [[inventory/01-data-model]] § 2.3

**Constraints ที่เกี่ยวข้องกับ costing:** `@@unique([lot_no, lot_index])` บังคับ lot identity; อัลกอริทึม cost-pick อาศัย `(location_id, product_id, lot_seq_no)` ordering สำหรับ FIFO และ row ล่าสุดที่ `(location_id, product_id)` สำหรับ WA current average `cost_per_unit` และ `average_cost_per_unit` ไม่ติดลบตาม `INV_VAL_007`

### 2.2 tb_inventory_transaction_detail (per-line cost ledger)

**Per-product / per-lot ledger line** ภายใต้ movement carry `qty`, `cost_per_unit`, `total_cost`, location และ lot-trace fields `from_lot_no` / `current_lot_no` โมดูล costing อ่าน row นี้เพื่อยืนยัน cost-per-unit ที่ post กับ source-document line เฉพาะ (GRN line carry `cost_per_unit = vendor unit price after extra-cost allocation`; SR issue line carry `cost_per_unit = picked cost`); เป็นภาพ user-facing ของต้นทุน cost-layer

**ฟิลด์ที่เกี่ยวข้องกับ costing:**

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนต่อหน่วยตอน posting; default `0` สำหรับ inbound: layer cost (ขับเคลื่อน cost-layer row's `cost_per_unit`); สำหรับ outbound: engine-picked cost **นี่คือค่าที่ปรากฏบน source document's line** (เช่น GRN detail's unit cost, SR issue's costed unit) |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Signed quantity ในหน่วยฐาน; บวก = inbound, ลบ = outbound คูณ `cost_per_unit` ได้ `total_cost` |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit` (signed); default `0` |
| `from_lot_no` | `String @db.VarChar` | Yes | Source lot consumed (outbound) ตั้งโดย FIFO pick — ชี้ไป lot ที่ `lot_seq_no` ต่ำสุดมี remaining balance |
| `current_lot_no` | `String @db.VarChar` | Yes | Lot ที่สร้างใหม่หรือได้รับผลกระทบ (inbound) Carry lot identity ของ layer ใหม่เข้า `lot_no` ของ cost-layer |

ฟิลด์อื่นและ constraints แสดงเต็มที่ [[inventory/01-data-model]] § 2.2

### 2.3 tb_period_snapshot (period-locked unit cost)

**Locked opening / closing balance row** ต่อ `(period_id, location_id, product_id, lot_no, lot_index)` เขียนตอนปลายงวดเป็น audit anchor จากมุมมอง costing แถวนี้เป็น **คำตอบ period-end valuation** — carry `closing_qty`, `closing_cost_per_unit`, และ `closing_total_cost` ที่งบดุลและรายงาน food-cost ใช้

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

ฟิลด์อื่นแสดงที่ [[inventory/01-data-model]] § 2.7

### 2.4 tb_business_unit.calculation_method (costing-method configuration — platform)

**การตั้งค่าวิธี costing** อยู่ที่ระดับ business-unit (property / hotel) บน **platform schema** ไม่ใช่บน tenant schema และไม่ใช่บน product ค่าเดียวใช้กับทุก product ที่ business unit นั้น

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `calculation_method` | `enum_calculation_method` | No | วิธี costing สำหรับ business unit ค่า: `average` (Weighted Average — default), `fifo` (First-In-First-Out) อ่านโดย inventory cost-layer post engine ทุก outbound เพื่อตัดสินกฎ cost-pick |

`tb_business_unit` definedใน `prisma-shared-schema-platform/prisma/schema.prisma` (ไม่ใช่ใน tenant schema ที่ `tb_inventory_transaction_cost_layer` อยู่) Cost-layer post engine อ่านค่านี้ผ่าน tenant-to-platform JWT context (`x-app-id` resolve ไป business unit) และ apply กฎที่เลือกกับ cost-layer write Tenant schema's `enum_business_unit_config_key` enumerate `calculation_method` เป็น config key — surface runtime-config parallel (key/value rows) ที่อาจ shadow หรือ extend platform default ขึ้นกับ tenant's config-loader convention

### 2.5 tb_product.standard_cost (reference cost on the product)

**Product's reference / standard cost** ใช้โดย `standard` count-costing method (`enum_physical_count_costing_method = standard` — count variance ถูกตีมูลค่าที่ product's `standard_cost` แทนที่จะเป็น cost-layer cost) และโดย recipe baseline costing

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `standard_cost` | `Decimal @db.Decimal(20, 5)` | Yes | ต้นทุนอ้างอิง / standard cost ต่อหน่วยในหน่วยฐาน; default `0` อัปเดตโดย Finance / cost-controller cadence (โดยปกติรายเดือนหรือรายไตรมาส) **ไม่** ใช้โดย FIFO / WA cost-pick engine — engine นั้นอ่าน cost-layer's `cost_per_unit` / `average_cost_per_unit` |
| `price_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | Tolerance band — เปอร์เซ็นต์หรือ absolute — ใช้โดยกฎ procurement / receiving เพื่อ flag ราคา vendor ที่เกิน standard cost ไม่ใช้โดย costing-engine โดยตรง; ข้อมูลสำหรับ variance reporting |
| `qty_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | Tolerance band บนปริมาณรับเทียบกับสั่ง ข้อมูล |

`tb_product` documented เต็มภายใต้โมดูล [[product]]; entry นี้ครอบคลุม subset ที่เกี่ยวข้องกับ costing

### 2.6 enum_physical_count_costing_method (count-variance valuation source)

Enum สี่ค่าที่เลือก **แหล่งต้นทุนที่ feed count-driven variance posts** เมื่อ physical-count หรือ spot-check เสร็จด้วย variance นี่เป็น costing-specific concern เพราะ count adjustments (`adjustment_in` / `adjustment_out`) ต้องการ `cost_per_unit` เพื่อคำนวณ `total_cost` และแหล่งของต้นทุนนั้นต่างกันตาม tenant preference

| Value | แหล่งต้นทุน |
| ----- | ----------- |
| `standard` | Product's `tb_product.standard_cost` ใช้โดย tenant ที่ต้องการให้ count variance ถูกตีมูลค่าที่ reference cost โดยไม่คำนึงถึงราคารับล่าสุด |
| `last` | Cost-layer ล่าสุด `cost_per_unit` ที่ `(location_id, product_id)` โดยไม่คำนึงถึงทิศทาง ประมาณ "current market cost" |
| `average` | `average_cost_per_unit` ล่าสุดที่ `(location_id, product_id)` สำหรับ WA-configured products เท่ากับ running average ปัจจุบัน; สำหรับ FIFO เอนจินคง shadow WA parallel สำหรับวัตถุประสงค์นี้ |
| `last_receiving` | Inbound layer ล่าสุดของ `cost_per_unit` (filtered ไป `transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`) ประมาณ "last price we paid" |

ตั้งค่าต่อ business unit (โดยปกติผ่าน `tb_business_unit_config_key = physical_count_costing_method`) อ่านโดย count-variance posting code ตอนเขียน `tb_stock_in` / `tb_stock_out` document ที่ derived จาก count ที่เสร็จ

## 3. ความสัมพันธ์

```
tb_business_unit (platform schema)
    │  calculation_method ∈ {average, fifo}  ── single costing method per business unit
    │
    │  Read by the cost-layer post engine via the x-app-id / JWT business-unit context.
    │  No Prisma @relation to tenant entities — cross-schema reference.
    ▼

tb_inventory_transaction
    │ * inventory_transaction_id
    ▼
tb_inventory_transaction_detail
    │  cost_per_unit (user-facing per-line cost)
    │  qty (signed) ── total_cost = qty × cost_per_unit
    │
    │ * inventory_transaction_detail_id
    ▼
tb_inventory_transaction_cost_layer  (canonical cost-flow record)
    │  cost_per_unit            ── layer cost (FIFO: per-lot; WA: per-event)
    │  average_cost_per_unit    ── post-movement moving average (WA path)
    │  lot_seq_no               ── FIFO ordering anchor (consumed lowest-first)
    │  diff_amount              ── credit-note-amount / EOP revaluation variance
    │  in_qty / out_qty         ── direction; mutually exclusive
    │  transaction_type ∈ {good_received_note, transfer_in, transfer_out,
    │                       issue, adjustment_in, adjustment_out,
    │                       credit_note_amount, credit_note_quantity,
    │                       eop_in, eop_out, close_period, open_period}
    │  at_period (YYMM) / period_id ── ties layer to accounting period
    │
    └──► tb_period   (period_id → close_period / open_period rollforward anchor)


tb_product
    │  standard_cost           ── reference cost (used by count-costing-method = standard)
    │  price_deviation_limit   ── tolerance band (informational)
    │  qty_deviation_limit     ── tolerance band (informational)
    │
    │  No per-product costing_method field — single method per business unit.
    │
    │ * product_id (no @relation declared on cost-layer / detail)
    ▼
tb_inventory_transaction_cost_layer / tb_inventory_transaction_detail
    (cost-layer rows reference product_id but no Prisma @relation)


tb_period ──1──*──► tb_period_snapshot  (locked period × location × product × lot
                                          opening / receipt / issue / adjustment /
                                          closing cost columns — the period-end
                                          valuation anchor)
```

หมายเหตุ:

- **Configuration cross-schema gap.** ค่า enum วิธี costing อยู่บน `tb_business_unit.calculation_method` ใน **platform** schema แต่ cost-layer rows ที่บริโภคอยู่ใน **tenant** schema ไม่มี Prisma `@relation` bridging; ความสัมพันธ์ resolve ที่ application layer ผ่าน JWT / `x-app-id` business-unit context ที่ tenant API call carry เส้นทางอ่านของโมดูล costing คือ: `(tenant: inventory transaction post) → (jwt: x-app-id) → (platform query: tb_business_unit.calculation_method) → apply cost-pick rule`
- **Per-tenant override via runtime config.** `enum_business_unit_config_key` enumerate `calculation_method` เป็น config key valid บน `tb_business_unit_config_key` Implementation suggest a key/value runtime-config row ที่สามารถ override platform default per business unit โดยไม่ต้อง redeploy
- **ไม่มี `tb_costing_*` entity.** โมดูล costing เป็น **ชั้นพฤติกรรมเหนือ inventory entities** ไม่ใช่ document tree ของตัวเอง การเก็บ cost บน row เดียวกับ qty (บน `tb_inventory_transaction_cost_layer`) หมายความว่าไม่สามารถมีการ drift ระหว่าง qty ledger และ cost ledger — เป็น ledger เดียวกัน
- **Cost-pick is movement-time, not query-time.** เมื่อ outbound post engine resolve cost ตอน post และเขียนไป cost-layer's `cost_per_unit` การอ่าน row ในภายหลังคืนค่า historical cost — แม้วิธีที่ตั้งค่าจะเปลี่ยน posted rows คงต้นทุนที่เลือกภายใต้วิธีที่ใช้ ณ ตอน
- **Period-snapshot คือคำตอบที่ล็อก.** เมื่อ `tb_period_snapshot.closing_cost_per_unit` เขียนโดย `INV_POST_009` (period close) valuation ของงวดเป็น immutable
- **`standard_cost` เป็น reference-only.** **ไม่** ขับเคลื่อน FIFO หรือ WA cost-pick ขับเคลื่อน `standard` count-costing method และ recipe baseline costing

## 4. Enums

- **`enum_calculation_method`** (platform schema, `prisma-shared-schema-platform`): costing-method classifier บน `tb_business_unit.calculation_method` สองค่า default `average`:
  - `average` — Weighted Average Moving average เดียวต่อ `(location_id, product_id)` รีเฟรชทุก inbound ตาม `INV_CALC_007`; outbound บริโภคที่ค่าเฉลี่ยที่มีอยู่ตาม `INV_CALC_006`
  - `fifo` — First-In, First-Out Lot บริโภคตาม `lot_seq_no` ascending ตาม `INV_CALC_005`; แต่ละ lot ที่บริโภคผลิต outbound cost-layer row ของตัวเองที่ `cost_per_unit`
- **`enum_business_unit_config_key`** (tenant schema): enumerate runtime-config keys บน `tb_business_unit_config_key` rows ค่าที่เกี่ยวข้องกับ costing:
  - `calculation_method` — runtime override ของ platform `tb_business_unit.calculation_method` default
  - `physical_count_costing_method` — เลือกแหล่งต้นทุนสำหรับ count-driven variance posts
  - `amount`, `quantity`, `recipe` — formatting / precision config keys
- **`enum_physical_count_costing_method`** (tenant schema): แหล่งตีมูลค่า count-variance สี่ค่า ไม่มี schema default declared:
  - `standard` — ตีมูลค่า count variance ที่ `tb_product.standard_cost`
  - `last` — ที่ cost-layer `cost_per_unit` ล่าสุด ที่ key `(location, product)` โดยไม่คำนึงถึงทิศทาง
  - `average` — ที่ `average_cost_per_unit` ล่าสุด (running WA)
  - `last_receiving` — ที่ inbound layer ล่าสุดของ `cost_per_unit`
- **`enum_transaction_type`** (tenant schema): cost-flow effect บน `tb_inventory_transaction_cost_layer.transaction_type` มี 12 ค่าตาม [[inventory/01-data-model]] § 4 subset ที่ engine-relevant:
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
| 4 | Per-product `costing_method` column on `tb_product` | `inventory/01-data-model.md` § 5 item 4 ระบุ: "Costing method per product อยู่บน model **product** (`tb_product`) — ไม่ใช่ inventory" | **ไม่มีคอลัมน์ `costing_method` บน `tb_product`** Costing method อยู่บน `tb_business_unit.calculation_method` (item 1 ข้างต้น) | อัปเดต [[inventory/01-data-model]] § 5 item 4 เพื่อแก้ไข — costing method เป็น per business unit ไม่ใช่ per product |
| 5 | Strategy-pattern architecture | `calculation-methods.md` § 6.2 อธิบาย `InventoryCostingStrategy` interface พร้อม `FIFOStrategy` และ `AverageCostStrategy` implementations | สถาปัตยกรรมตรงกับ strategy pattern แต่ **strategy resolve per business unit ไม่ใช่ per product** | อัปเดต `calculation-methods.md` § 6.2 ให้ document resolution scope (business unit ไม่ใช่ product) |
| 6 | `physical_count_costing_method` (count-variance source) | ไม่ระบุใน `calculation-methods.md` หรือ `enhanced-costing-engine.md` | `enum_physical_count_costing_method ∈ {standard, last, average, last_receiving}` เป็น costing-relevant enum (Section 2.6 ข้างต้น) | เพิ่ม §6.x หรือ §7 ใน `calculation-methods.md` covering count-variance valuation source |
| 7 | `diff_amount` (credit-note variance) | ไม่ระบุใน carmen/docs costing reference | `tb_inventory_transaction_cost_layer.diff_amount` carry cost-only variance สำหรับ credit-note-amount adjustments และ end-of-period revaluation | เพิ่มใน `calculation-methods.md` |
| 8 | Enhanced costing engine scope | `../carmen/docs/costing/enhanced-costing-engine.md` อธิบาย **portion-based / recipe-cost / dynamic-pricing** engine | Prisma costing surface ครอบคลุม **inventory valuation เท่านั้น** — FIFO / WA cost-pick บน `tb_inventory_transaction_cost_layer`, period-end snapshot บน `tb_period_snapshot` | ถือทั้งสองเป็น concerns แยก |
| 9 | "Cost layer" naming vs "lot" naming | `calculation-methods.md` ใช้ "lot" ตลอด Prisma ใช้ "cost layer" (`tb_inventory_transaction_cost_layer`) — broader term | A **lot** ใน carmen/docs ≅ a group of cost-layer rows sharing `(lot_no, lot_index)` | คง "lot" เป็น user-facing term แต่ document ว่า one lot internally คือ collection ของ cost-layer rows |
| 10 | Rounding and precision | `calculation-methods.md` § 6.4 ระบุ "Rounding: Round per lot" | คอลัมน์การเงินทั้งหมดเป็น `Decimal(20, 5)` ตาม `INV_CALC_012` | ไม่มี divergence ใน policy; document explicit precision |

## 6. References

- **Primary (source of truth):**
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — tenant entities (`tb_inventory_transaction_cost_layer`, `tb_inventory_transaction_detail`, `tb_period_snapshot`, `tb_product`), tenant enums
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — platform entity `tb_business_unit.calculation_method` และ platform enum `enum_calculation_method`
- **Secondary (concept cross-check):**
  - `../carmen/docs/costing/enhanced-costing-engine.md`
  - Sibling: [calculation-methods.md](./calculation-methods.md)
- Related modules: [[inventory]], [[good-receive-note]], [[store-requisition]], [[physical-count]] / [[spot-check]], [[inventory-adjustment]], [[recipe]], [[product]]
