---
title: การคำนวณต้นทุน — User Flow (Costing — User Flow)
description: วงจรชีวิต cost-flow และไฟล์ flow ตาม persona สำหรับ costing
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน — User Flow

> **At a Glance**
> **Module:** [[costing]] &nbsp;·&nbsp; **Personas:** Finance &nbsp;·&nbsp; Inventory Controller &nbsp;·&nbsp; Auditor
> **Workflow lifecycle:** Cost-layer row born (inbound) → picked (FIFO/WA outbound) → revalued (credit-note) → period-close anchor → period-open rollforward → period locked. Period valuation: `open` → `closed` → `locked`
> **เจาะลึก per-persona views ด้านล่างเพื่อรายละเอียดระดับ action**

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด user-flow ของโมดูล `costing` Costing เป็นโมดูลที่ผิดปกติเมื่อเทียบกับ document module พี่น้อง — ไม่มี workflow document เดียวที่ลำดับ draft → saved → committed lifecycle เล่นออก และไม่มี document tree แยกเลย Costing เป็น **ชั้นพฤติกรรมเหนือ inventory cost-layer ledger** ดังนั้น lifecycle ที่ personas เดินคือ **lifecycle ของ unit cost** ที่ `(location_id, product_id, lot_no)`: มันถูก **เกิด** บน inbound `tb_inventory_transaction_cost_layer` row (GRN receipt ตั้ง `cost_per_unit`; ภายใต้ WA running average ถูกคำนวณใหม่), ถูก **เลือก** โดยทุก outbound ที่ตามมา (FIFO จาก lot เก่าที่สุด; WA ที่ average ที่มีอยู่), ถูก **ตีมูลค่าใหม่** โดย credit-note-amount adjustments (`diff_amount`), ถูก **roll forward** ที่ period close เข้า opening cost ของงวดถัดไป และถูก **ล็อก** เข้า period snapshot เป็น audit anchor แต่ละ persona เป็นเจ้าของชิ้นที่ต่างกันของ lifecycle นั้น: Finance เป็นเจ้าของนโยบาย valuation และ period-end sign-off, Inventory Controller เป็นเจ้าของความสะอาดของ input ของ engine, และ Auditor ตรวจสอบว่า costed COGS และ ending inventory tie กลับไปยัง source receipts และวิธี costing ถูกใช้อย่างสม่ำเสมอข้ามงวด

Section 2 ข้างล่างอธิบาย **cost-flow lifecycle** — ชุด canonical ของ transitions ที่ถูกกฎหมายบน unit cost จากการสร้าง inbound ถึง consumption outbound ถึง period rollforward, ไม่ขึ้นกับว่าใครทำ ไฟล์ per-persona (ลิงก์จาก Section 3) อธิบาย *เส้นทาง persona นั้นผ่าน* state space นี้ — entry point, actions ที่มี, decision branches, และ handoff ที่จบการเกี่ยวข้อง Section 4 สรุป cross-persona handoffs ที่เย็บเส้นทางบุคคลเข้าด้วยกัน

## 2. วงจรชีวิต Cost-Flow

### 2.0 ลำดับ Transaction → Cost Engine

Costing ไม่มี per-document state machine (ไม่มี `draft → saved → committed` lifecycle) Cost engine ถูก invoke โดย inventory-affecting transactions Diagram ข้างล่าง mirror Process Execution Swim Lane จาก `Test_case/System_Process/INDEX.md` (version 1.3.0, capture date 2026-04-27)

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
    TX->>INV: บันทึก Period snapshot
    INV->>LOT: Anchor lots ที่เปิดสำหรับงวด
    LOT->>COST: Period costs locked — เขียน close_period / open_period cost-layer rows (COST_POST_007 / COST_POST_008)
```

State machines สองตัวอยู่ในโมดูลนี้: **per-cost-layer-row** lifecycle (degenerate — แต่ละ cost-layer row เขียน immutable ตอน post, optionally revalued ผ่าน `diff_amount` row, optionally rolled forward ที่ period close) และ **per-period valuation** lifecycle ที่ mirror โมดูล inventory's `tb_period.status` (`open` → `closed` → `locked`)

### 2.1 Transitions ของ Cost-layer

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | inbound cost-layer write (engine เลือก inbound cost) | `posted` | Source-document role ฝั่ง inventory | Source document อยู่ใน terminal posting state; `COST_VAL_001`–`COST_VAL_005` ผ่าน; `calculation_method` ของ business unit resolve Engine เขียน `cost_per_unit`, `average_cost_per_unit`, `lot_seq_no` ตาม `COST_POST_001` |
| `(none)` | outbound cost-layer write (engine เลือก outbound cost ผ่าน FIFO / WA) | `posted` | Source-document role | Source document terminal; `COST_VAL_002` / `COST_VAL_003` ผ่าน; FIFO consume ตาม `lot_seq_no` asc ผลิต 1+ rows; WA consume ที่ current average ผลิต 1 row Engine เขียน outbound rows ตาม `COST_POST_002` |
| `posted` | credit-note-amount revaluation | `posted` (revalued — original row ยังอยู่ + เพิ่ม `diff_amount` row ใหม่) | Finance (ที่ credit-note approve) | Lot ต้นทางระบุ; `COST_VAL_006` ผ่าน Engine เขียน cost-layer row ใหม่พร้อม `in_qty = out_qty = 0, diff_amount = signed_amount` ตาม `COST_POST_003` |
| `posted` | period-close anchor (`close_period`) | `posted` (anchored to period) | System / scheduled job | Period ที่กำลังปิดมี source documents terminal ทั้งหมด; engine เขียน `close_period` cost-layer rows ตาม `COST_POST_007` |
| `posted` | period-open rollforward (`open_period`) | `posted` (rolled forward to next period) | System / scheduled job | Engine เขียน `open_period` cost-layer rows สำหรับงวดถัดไป ตาม `COST_POST_008` |
| `posted` | (ไม่มี action โดยตรงต่อไป — terminal ภายใต้ flow ปกติ) | `posted` | — | Cost-layer row เป็น immutable |

### 2.2 Per-period valuation transitions (mirror ของ `tb_period.status`)

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | สร้าง period (system / scheduled) | `open` | System Administrator | Period definition populate; ไม่ทับซ้อนกับ period rows ที่มีอยู่ |
| `open` | accept cost-layer writes | `open` | All transactional roles | Engine เขียน cost-layer rows สำหรับ inventory transaction ใด ๆ ที่วันที่อยู่ใน `[period.start_at, period.end_at]` |
| `open` | run period-end valuation (close + rollforward) | `closed` | Finance, พร้อม Inventory Controller's variance-review sign-off | Pre-period-end checklist เสร็จ Engine run `COST_POST_007` chained กับ `COST_POST_008` ตั้ง `tb_period.status = closed` |
| `closed` | re-open period (exceptional valuation correction) | `open` | Finance Manager (elevated; audit-logged) | ต้องการ audit-grade justification |
| `closed` | lock period (valuation immutable) | `locked` | Finance Manager | Audit window passed cleanly หลัง lock, `tb_period_snapshot.closing_cost_per_unit` / `closing_total_cost` permanent immutable ตาม `COST_AUTH_006` |
| `locked` | (ไม่มี transitions ต่อไป) | `locked` | — | Terminal |

## 3. ดัชนี Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down dedicated อธิบาย entry point, primary flow, decision branches, และ exit point Slugs ตรงกับ persona role

- [Finance](./03-user-flow-finance.md) — เป็นเจ้าของ **นโยบาย valuation** (FIFO vs WA per business unit, count-costing-method selection, reconciliation tolerance, standard-cost update cadence), รัน **inventory-sub-ledger ↔ GL reconciliation** ที่ period close, **อนุมัติ credit-note-amount adjustments** ที่ revalue lot cost, และ (เป็น Finance Manager) **เซ็นรับรอง period-end valuation** แล้ว advance `tb_period.status = closed → locked`
- [Inventory Controller](./03-user-flow-inventory-controller.md) — มั่นใจว่า **inputs ของ engine สะอาด** เพื่อให้ cost ที่เลือกป้องกันได้: lot dates ตั้งถูกต้องตอนรับ, ต้นทุนรับสมเหตุสมผลเทียบกับ vendor pricelists, adjustment cost bases สมเหตุสมผล, waste write-offs ตรวจสอบ **valuation variances** ที่ Finance surface ระหว่าง reconciliation
- [Auditor](./03-user-flow-auditor.md) — ตรวจสอบว่า **costed COGS และ ending inventory tie กลับไปยัง source receipts** (cost-flow chain: GRN inbound → cost-layer row → SR / write-off outbound consume lot → COGS journal entry) และวิธี costing ถูก apply อย่างสม่ำเสมอข้ามงวด

## 4. Cross-Persona Handoffs

ตารางข้างล่างจับช่วงเวลาที่ costing work ย้ายจากความรับผิดชอบของ persona หนึ่งไปอีก persona

| จาก persona | Trigger | ไป persona | System state ที่ handoff |
| ------------ | ------- | ---------- | ----------------------- |
| Inventory Controller | Cost-pick preview ผิดปกติ surface ที่ stock-out approval (เช่น FIFO consume lot เก่าราคาสูงทำให้ COGS ไม่คาดคิด หรือ WA average drift จาก vendor pricelist เกิน tolerance) | Finance | Stock-out document ที่ `doc_status = in_progress`; Controller flag cost concern แต่ยังไม่อนุมัติ; Finance review cost basis ก่อน document ดำเนินต่อ |
| Inventory Controller | Adjustment cost basis เกิน tenant deviation tolerance (`tb_product.price_deviation_limit`) บน manual stock-in | Finance | Stock-in document ที่ `in_progress`; Controller ปฏิเสธกลับไปยัง Store Keeper หรือ escalate ไป Finance |
| Finance | Credit-note-amount adjustment approved (vendor concession บน lot cost ของ posted GRN) | System / costing engine | Credit-note ที่ `approved`; inventory module fires cost-layer revaluation ผ่าน `INV_POST_007` / `COST_POST_003`; lot ต้นทาง's `cost_per_unit` update |
| Finance | Inventory-sub-ledger ↔ GL reconciliation surface costing-side variance | Inventory Controller (investigation) | Period ยังคง `open`; reconciliation dashboard show variance; Controller investigate offending cost-layer rows |
| Finance | Period-end valuation run complete (sub-ledger closing matches GL closing within tolerance) | Finance Manager | Period ที่ `tb_period.status = closed`; พร้อมให้ Finance Manager advance เป็น `locked` |
| Finance Manager | Period locked | Auditor | Period ที่ `tb_period.status = locked`; valuation immutable |
| Finance Manager | Configuration change ไป `tb_business_unit.calculation_method` proposed (FIFO ↔ average) | System Administrator (config save) + Finance (drain check) | Sysadmin พยายาม save; `COST_VAL_009` block ถ้า product ใด ๆ มี non-zero on-hand |
| Auditor | Cost-flow chain-of-custody trace complete | Finance (cost-impact review) + Inventory Controller (lot-trace operational review) | ไม่มี transaction state change Trace report เป็น deliverable |

## 5. References

- `../carmen/docs/costing/enhanced-costing-engine.md`
- Sibling: [calculation-methods.md](./calculation-methods.md)
- Sibling: [01-data-model.md](./01-data-model.md)
- Sibling: [02-business-rules.md](./02-business-rules.md)
- Related: [[inventory/03-user-flow]]
- Related modules: [[good-receive-note]], [[store-requisition]], [[physical-count]] / [[spot-check]], [[inventory-adjustment]], [[recipe]], [[product]]
