---
title: การคำนวณต้นทุน (Costing) — User Flow
description: วงจรชีวิต cost-flow และไฟล์ flow ตาม persona สำหรับ costing
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — User Flow

> **At a Glance**
> **Module:** [costing](/th/inventory/costing) &nbsp;·&nbsp; **Personas:** ไม่มีที่แยกจริง — ดูหมายเหตุแก้ไขด้านล่าง โมดูลนี้ไม่มีหน้าจอที่ gate ด้วย persona
> **Workflow lifecycle:** Cost-layer row born (inbound) → picked (FIFO/WA outbound) → revalued (credit-note) → period-close anchor (เฉพาะวิธี average เขียน `tb_period_snapshot`; FIFO นำ lot ไปต่อแทน) → period-open rollforward
> **เจาะลึกหน้า per-persona ด้านล่าง — แต่ละหน้าคือหน้าแก้ไขที่ชี้ไปพฤติกรรมจริง**

> **แก้ไข (ยืนยันแล้ว 2026-07-22):** สามหน้า per-persona ที่ลิงก์จาก Section 3 (Finance, Inventory Controller, Auditor) เคยเอกสารหน้าจอเฉพาะ — valuation-policy console, sub-ledger ↔ GL reconciliation dashboard, adjustment cost-pick-preview approval queue, read-only audit workspace — ไม่มีสิ่งใดมีอยู่จริง Engine **ไม่มี UI ที่ gate ด้วย persona ของตัวเอง**: มันทำงานเป็นผลข้างเคียงของ GRN commit, SR issue, การสร้าง inventory-adjustment, credit-note approval, และ period-end close โดยแต่ละอย่าง gate ด้วย permission ทั่วไปของ source document นั้นเอง `enum_stage_role` (enum role เดียวใน tenant schema) คือ `{create, approve, purchase, issue, view_only}` — ไม่มีสมาชิก `finance` หรือ `auditor` สอดคล้องกับการแก้ไขเดียวกันที่ทำแล้วบน [inventory/03-user-flow](/th/inventory/inventory/03-user-flow) ซึ่งพบว่า "ไม่มี Finance role, GL reconciliation, หรือ period-lock flow" สำหรับ period-end surface เดียวกันที่ engine โมดูลนี้เชื่อมต่อด้วย

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด user-flow ของโมดูล `costing` Costing เป็นโมดูลที่ผิดปกติเมื่อเทียบกับ document module พี่น้อง — ไม่มี workflow document เดียวที่ลำดับ draft → saved → committed lifecycle เล่นออก และไม่มี document tree แยกเลย Costing เป็น **ชั้นพฤติกรรมเหนือ inventory cost-layer ledger** ดังนั้น lifecycle ที่จะอธิบายคือ **lifecycle ของ unit cost** ที่ `(location_id, product_id, lot_no)`: มันถูก **เกิด** บน inbound `tb_inventory_transaction_cost_layer` row (GRN receipt ตั้ง `cost_per_unit`; ภายใต้ Average running average ถูกคำนวณใหม่), ถูก **เลือก** โดยทุก outbound ที่ตามมา (FIFO จาก lot เก่าที่สุด; Average ที่ running average ที่มีอยู่), ถูก **ตีมูลค่าใหม่** โดย credit-note-amount adjustments (`diff_amount`), และ — **เฉพาะ business unit ที่ใช้วิธี average เท่านั้น** — ถูก **roll forward** ที่ period close เข้า opening cost ของงวดถัดไปและล็อกเข้า `tb_period_snapshot` Business unit ที่ใช้วิธี FIFO นำ lot คงเหลือไปต่อเป็นแถว `close_period`/`open_period` บน cost-layer และไม่เขียนแถว snapshot เลย

Section 2 ข้างล่างอธิบาย **cost-flow lifecycle** — ชุด canonical ของ transitions ที่ถูกกฎหมายบน unit cost จากการสร้าง inbound ถึง consumption outbound ถึง period rollforward ไม่มี "เส้นทาง persona ผ่าน state space นี้" ให้เอกสาร เพราะไม่มีหน้าจอเฉพาะ persona อยู่จริง — ผู้ถือ permission ของเอกสารที่เกี่ยวข้อง (GRN commit, SR approve, adjustment create, credit-note approve, หรือ `inventory_management.period_end.execute`) จุดชนวน engine เดียวกันด้วยวิธีเดียวกัน Section 3 ลิงก์ไปสามหน้าแก้ไขที่อธิบายว่าเคย claim อะไรและพฤติกรรมจริงอยู่ที่ไหน Section 4 ถูกลดเหลือ handoff ข้ามโมดูลจริงเพียงหนึ่งเดียวที่โมดูลนี้เกี่ยวข้อง

## 2. วงจรชีวิต Cost-Flow

### 2.0 ลำดับ Transaction → Cost Engine

Costing ไม่มี per-document state machine (ไม่มี `draft → saved → committed` lifecycle) Cost engine ถูก invoke โดย inventory-affecting transactions Diagram ข้างล่างตรวจสอบใหม่โดยตรงกับ `inventory-transaction.service.ts` และ `period-end.close-transaction.helper.ts` / `period-end.close-average.helper.ts`; มัน mirror เจตนาการออกแบบของ Process Execution Swim Lane ที่บันทึกในเอกสารวางแผนจริงที่ `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/INDEX.md` และ `proc-03-cost-calculation.md` (เอกสาร requirements-gathering ไม่ใช่ test spec ที่ยืนยันแล้ว — ฉบับร่างก่อนหน้าอ้างเอกสารชุดเดียวกันนี้ด้วย path ที่ไม่มีอยู่จริง `Test_case/System_Process/` พร้อม capture date ที่กุขึ้นเอง ดู [02-business-rules](/th/inventory/costing/02-business-rules) § 5.1 สำหรับการแก้ไข)

```mermaid
sequenceDiagram
    participant TX as Trigger Transaction
    participant INV as ① Inventory Update
    participant LOT as ② Lot Management
    participant COST as ③ Cost Calculation

    Note over TX,COST: Stock-in — GRN · Stock In (adj)
    TX->>INV: +qty ที่ inventory location
    INV->>LOT: สร้าง lot ใหม่; กำหนด lot_seq_no
    LOT->>COST: AVCO re-average (COST_CALC_003) / FIFO เพิ่ม cost layer (COST_CALC_004)

    Note over TX,COST: Stock-out — CRN · Issues · Sales Consumption · Stock Out (adj) · Wastage Report
    TX->>INV: -qty ที่ inventory location
    INV->>LOT: Consume lot เก่าที่สุด (lot_seq_no ต่ำสุดก่อน)
    LOT->>COST: AVCO cost held ที่ average ที่มีอยู่ (COST_CALC_002) / FIFO consume layer เก่าที่สุด (COST_CALC_001)

    Note over TX,COST: SR — Store Requisition (internal transfer, any variant)
    TX->>INV: -qty inv source / +qty direct or consignment destination
    INV->>LOT: Lot consumed ที่ inv source — ไม่มี lot ที่ destination
    Note over COST: Cost-pick (COST_POST_002): consume existing layer ที่ existing cost ไม่มี AVCO re-average ไม่มี FIFO layer ใหม่ ดู COST_XMOD_003

    Note over TX,COST: Physical Count — variance exists
    TX->>INV: ±qty variance (physical count transaction type)
    INV->>LOT: Lots ปรับขึ้น (overage) หรือ consume ลง (shortage)
    LOT->>COST: Recalc เฉพาะถ้ามี variance — cost source ตาม enum_physical_count_costing_method (COST_CALC_008)

    Note over TX,COST: Physical Count — no variance
    TX->>INV: ยืนยัน count ไม่มี qty change
    Note over LOT,COST: NOT triggered — ไม่มี lot หรือ cost-layer write

    Note over TX,COST: Credit-note-amount revaluation
    TX->>COST: post diff_amount ไป lot ต้นทาง (COST_POST_003 / COST_CALC_005)
    COST->>LOT: lot ต้นทาง cost_per_unit คำนวณใหม่; downstream FIFO เลือก cost ที่ revalued

    Note over TX,COST: End Period Close
    TX->>INV: เขียนแถว cost-layer close_period / open_period สำหรับทุก lot คงเหลือ (ทั้งสองวิธี)
    Note over INV,COST: เฉพาะ business unit ที่ใช้วิธี average: เขียนแถว tb_period_snapshot ด้วย (COST_POST_007) business unit ที่ใช้วิธี FIFO ไม่เขียนแถว snapshot เลย
```

State machines สองตัวอยู่ในโมดูลนี้: **per-cost-layer-row** lifecycle (degenerate — แต่ละ cost-layer row เขียน immutable ตอน post, optionally revalued ผ่าน `diff_amount` row, optionally rolled forward ที่ period close) และ **per-period** lifecycle ที่ mirror โมดูล inventory's `tb_period.status` ภายใน route ของโมดูลนี้เอง status นี้เคลื่อนแค่ `open → closed` เท่านั้น — พื้นผิว message-pattern ของ `period-end.controller.ts` มีแค่ `find-all` / `find-current` / `close` / `find-review` ไม่มี action lock/re-open ค่า `locked` มีอยู่บน enum และถูกตั้งโดย period service **แยกต่างหาก** ที่อยู่หลังหน้าจอ [system-config/period](/th/inventory/system-config/period) นอกโมดูลนี้ Transitions ด้านล่างครอบคลุมทั้งสอง lifecycle ตามที่ route ของโมดูลนี้เองรองรับจริง

### 2.1 Transitions ของ Cost-layer

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | inbound cost-layer write (engine เลือก inbound cost) | `posted` | ผู้ถือ permission ของ source document เอง (GRN commit, SR ที่อนุมัติ transfer-in, count overage, การสร้าง stock-in) — ไม่มี gate แยกฝั่ง costing | Source document ถึงจุดใน flow ของตัวเองที่ post เข้า ledger Engine เขียน `cost_per_unit`, `average_cost_per_unit`, `lot_seq_no` ตาม `COST_POST_001` |
| `(none)` | outbound cost-layer write (engine เลือก outbound cost ผ่าน FIFO / Average) | `posted` | ผู้ถือ permission ของ source document เอง (SR issue, การสร้าง stock-out, credit-note-quantity) — ไม่มี gate แยกฝั่ง costing | Source document terminal; `COST_VAL_002` / `COST_VAL_003` ผ่าน; FIFO consume ตาม `lot_seq_no` asc ผลิต 1+ rows; Average consume ที่ current average ผลิต 1 row Engine เขียน outbound rows ตาม `COST_POST_002` |
| `posted` | credit-note-amount revaluation | `posted` (revalued — original row ยังอยู่ + เพิ่ม `diff_amount` row ใหม่) | ผู้ถือ permission อนุมัติ `procurement.credit_note` | Lot ต้นทางระบุ; `COST_VAL_006` ผ่าน Engine เขียน cost-layer row ใหม่พร้อม `in_qty = out_qty = 0, diff_amount = signed_amount` ตาม `COST_POST_003` |
| `posted` | period-close anchor (`close_period`) | `posted` (anchored to period) | ผู้ถือ `inventory_management.period_end.execute` | Period ที่กำลังปิดมี blocking document terminal ทั้งหมด + physical count เสร็จ (ดู [inventory/period-end](/th/inventory/inventory/period-end) § 2) Engine เขียน `close_period` cost-layer rows สำหรับทุก lot คงเหลือ **ทั้งสองวิธี**; **เพิ่มเติม** เขียนแถว `tb_period_snapshot` **เฉพาะ business unit ที่ใช้วิธี average** ตาม `COST_POST_007` |
| `posted` | period-open rollforward (`open_period`) | `posted` (rolled forward to next period) | System-invoked, chain อยู่ใน close transaction เดียวกัน | Engine เขียน `open_period` cost-layer rows สำหรับงวดถัดไป ตาม `COST_POST_008` |
| `posted` | (ไม่มี action โดยตรงต่อไป — terminal ภายใต้ flow ปกติ) | `posted` | — | Cost-layer row เป็น immutable; ไม่มี update/patch endpoint บน cost-layer table |

### 2.2 Per-period transitions (mirror ของ `tb_period.status` ภายใน route ของโมดูลนี้เอง)

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | สร้าง period | `open` | System-provisioned — `ensureNextPeriod` สร้างงวดถัดไปอัตโนมัติเป็นส่วนหนึ่งของทุกการปิดงวด | Fiscal year/month sequencing; ไม่ทับซ้อนกับ period rows ที่มีอยู่ |
| `open` (หรือ `locked`) | accept cost-layer writes | เหมือนเดิม | ผู้ถือ permission ของเอกสารที่ trigger เอง | Engine เขียน cost-layer rows สำหรับ inventory transaction ใด ๆ ที่ถูก stamp เข้างวดที่เปิดอยู่ตอนนั้น ไม่ว่าวันที่บนเอกสารจะเป็นอะไร (`resolveCurrentPeriod` — เอกสารที่ backdate ถูก re-date เข้างวดที่เปิด ไม่ถูกปฏิเสธ) |
| `open` (หรือ `locked`) | close period | `closed` | ผู้ถือ `inventory_management.period_end.execute` | Blocking-document gate ทั้งหมดผ่าน (ดู [inventory/period-end](/th/inventory/inventory/period-end) § 2) รันแบบ atomic ภายใต้ row lock พร้อม re-validation; เขียน lot carry-over; tenant ที่ใช้วิธี average ได้แถว `tb_period_snapshot` ด้วย; สร้างงวดถัดไปแบบ `open` อัตโนมัติ route ของโมดูลนี้เอง (`period-end.controller.ts`) เปิดเผยแค่ `find-all` / `find-current` / `close` / `find-review` — ไม่มี action lock หรือ re-open ที่นี่ |
| `closed` | — | — | — | `locked` เป็นค่า status ที่โมดูลนี้สังเกตได้ (หน้าจอ period-end ปฏิบัติกับงวดที่ `locked` เหมือน `open` สำหรับการค้นหา "งวดปัจจุบัน") แต่ไม่ได้ตั้งค่าเอง — มันถูกเขียนโดย period service **แยกต่างหาก** ที่อยู่หลังหน้าจอ [system-config/period](/th/inventory/system-config/period) นอกขอบเขตของ wiki module นี้ |

## 3. ดัชนี Persona

แต่ละหน้าที่ลิงก์ด้านล่างคือ **หน้าแก้ไข** — อธิบายว่าเคย claim อะไรสำหรับ "persona" นั้น และชี้ไปที่พฤติกรรมจริงที่ยืนยันแล้ว ไม่มีทั้งสามหน้าที่อธิบายหน้าจอที่มีอยู่จริง

- [Finance](./03-user-flow-finance.md) — แก้ไข: ไม่มี Finance role, valuation-policy console, GL reconciliation dashboard, หรือ period-lock flow
- [Inventory Controller](./03-user-flow-inventory-controller.md) — แก้ไข: ไม่มี cost-pick-preview approval queue; [inventory-adjustment](/th/inventory/inventory-adjustment) เอกสารว่า `tb_stock_in`/`tb_stock_out` post ทันทีเมื่อสร้าง ไม่มี pending state ให้ approver ใดทำ
- [Auditor](./03-user-flow-auditor.md) — แก้ไข: ไม่มี read-only audit workspace, chain-of-custody trace tool, หรือ shadow-drift audit screen

## 4. Handoff ข้ามโมดูลจริง

มี handoff ที่คุ้มค่าจะเอกสารเพียงหนึ่งเดียว และไม่ใช่ระหว่าง persona — แต่ระหว่างโมดูล:

| จาก | Trigger | ไป | System state ที่ handoff |
| --- | ------- | -- | ----------------------- |
| Source document ใดก็ตามที่ post stock movement (GRN commit, SR issue, การสร้าง inventory-adjustment, credit-note approval) | เอกสารถึงจุด posting ของตัวเอง | Costing engine (invoke แบบ synchronous ในการเรียกเดียวกัน) | Engine เขียนแถว cost-layer เป็นผลข้างเคียง — ไม่มี queue ไม่มีขั้นตอนอนุมัติแยก และไม่มีการทวนเฉพาะ persona ระหว่างทาง |
| Movement ตกลงในงวดที่เปิดอยู่ตอนนั้น | — | Period-end close (`inventory_management.period_end.execute`) | เมื่อ blocking document ทั้งหมดผ่านและ physical count เสร็จ การปิดงวดจะนำ lot คงเหลือทุกตัวไปต่อ (ทั้งสองวิธี) และเพิ่มเติมทำ snapshot `tb_period_snapshot` (เฉพาะ business unit ที่ใช้วิธี average) ดู [inventory/period-end](/th/inventory/inventory/period-end) § 2 สำหรับตาราง gate เต็ม — costing ไม่มี gate ของตัวเองนอกเหนือจากหน้านั้น |

## 5. References

- `../carmen/docs/costing/enhanced-costing-engine.md`
- Sibling: [calculation-methods.md](./calculation-methods.md)
- Sibling: [01-data-model.md](./01-data-model.md)
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation, calculation, posting, cross-module rules และหมายเหตุแก้ไข Section 4 ว่าทำไมไม่มีชั้น authorization แยก
- Related: [inventory/03-user-flow](/th/inventory/inventory/03-user-flow) และ [inventory/period-end](/th/inventory/inventory/period-end) — lifecycle การเคลื่อนไหวและงวดที่ costing engine เชื่อมต่อด้วย; กลไก period-end close/gate จริงอยู่ที่นั่น ไม่ได้ซ้ำที่นี่
- Related modules: [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) (spot-check ไม่ post variance เลย — ดู [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) § 5.1), [inventory-adjustment](/th/inventory/inventory-adjustment), [recipe](/th/inventory/recipe), [product](/th/inventory/product)
