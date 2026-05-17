---
title: คลังสินค้า — Test Scenarios (Inventory — Test Scenarios)
description: Test cases ตาม persona, scenarios ข้าม persona และการ map E2E สำหรับ inventory
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า — Test Scenarios (Inventory — Test Scenarios)

> **At a Glance**
> **โมดูล:** [[inventory]] &nbsp;·&nbsp; **Scenarios รวม:** ~17 cross-persona + ~115 per-persona &nbsp;·&nbsp; **Personas ครอบคลุม:** Store Keeper, Inventory Controller, Finance, Audit / Config
> **ลำดับการรัน:** Audit / Config setup → happy paths persona หลัก → scenarios ข้าม persona
> **drill-down ของแต่ละ persona คือ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้คือ **จุดเข้าภาพรวม** สำหรับชุด test-scenarios ของโมดูล `inventory` จัดกลุ่ม coverage ตามสี่ persona ที่โต้ตอบกับ movements inventory และสถานะงวด (Store Keeper, Inventory Controller, Finance, Audit / Config), inventories ไฟล์เทสต่อ persona, จับ scenarios การส่งต่อข้าม persona ที่เย็บเส้นทางแต่ละอันเข้าด้วยกัน และ map ทุก scenario ข้าม persona กลับไปยัง Playwright spec [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) (พื้นผิว E2E ฝั่ง inventory แบบ canonical) บวก specs ที่อยู่ติด inventory `720-stock-issue.spec.ts` (stock-out ผ่านเส้นทาง issue) และ `501-grn.spec.ts` Stock Movements describe block (ฝั่ง inventory ของ GRN commit) ขอบเขตกว้างกว่า functional pass บริสุทธิ์: ไฟล์ persona แต่ละไฟล์รวม **functional happy paths** (movement posts, period transitions, approvals), **กรณี RBAC / permission-denial** (Store Keeper พยายามอนุมัติเหนือ threshold, Controller พยายาม period lock, Sysadmin พยายาม post transaction), **edge cases** (concurrent posts, FIFO consumption spanning lots, weighted-average recompute on inbound, period-boundary movements, locked-period restatement), **count-variance posting** (overage / shortage / lot-mismatch) และ **orchestration ปิดงวด** (close, open-next, lock, re-open ภายใน audit window)

Scenarios ข้าม persona ใน Section 4 คือ integration layer เหนือ suites ต่อ persona พวกเขาอธิบาย end-to-end journeys ที่ข้ามขอบเขตการส่งต่อบันทึกใน [03-user-flow.md](./03-user-flow.md) Section 4 — ตัวอย่างเช่น *Store Keeper raise stock-in → Inventory Controller อนุมัติ → post ไปยัง inventory; Inventory Controller เซ็นรับรอง variance → Finance reconcile → Finance Manager ปิดงวด → ล็อกงวด* Section 5 map describe blocks E2E ที่เกี่ยวข้องกับ inventory กลับไปยัง journeys เหล่านั้นเพื่อให้ gaps ใน automated coverage มองเห็น; โปรดทราบว่าโมดูล inventory ถูกครอบคลุมบางส่วนโดยพื้นผิว E2E แบบ canonical (period-end, stock-issue และ GRN stock-movement) — ความกังวลฝั่ง inventory ละเอียดหลายอย่าง validate ผ่าน specs ของโมดูลต้นน้ำ พร้อมไฟล์เทสต่อ persona catalog scenarios ที่อาจเป็น manual / planned

## 2. Personas ในขอบเขต

- **Store Keeper**: ผู้ปฏิบัติงานระดับ floor ที่เริ่มเอกสาร `tb_stock_in` / `tb_stock_out` สำหรับ adjustments non-GRN / non-SR ปกติ และดำเนินการ physical / spot counts ที่ระดับ location
- **Inventory Controller**: เจ้าของความถูกต้องของยอดที่อนุมัติ adjustments เหนือ threshold, review และ commit count-variance lines, ดูแล policy สต๊อกต่อสินค้า / ต่อ location และเซ็นรับรอง variance ก่อนปิดงวด
- **Finance**: สิทธิ์การตีมูลค่าที่อนุมัติ adjustments เหนือ Controller-threshold, run inventory-to-GL reconciliation, orchestrate run ปิดงวด (close + open-next) และ (เป็น Finance Manager) advance `tb_period.status` จาก `closed` ไปยัง `locked`
- **Audit / Config**: System Administrator ที่เป็นเจ้าของ config `tb_location` / costing-method / `tb_adjustment_type` / period / threshold / RBAC / integration และ Auditor ที่ run audit-log queries อ่านอย่างเดียว, lot-recall traces และ period-snapshot reconciliation queries

## 3. ไฟล์เทสต่อ Persona

- [Store Keeper scenarios](./04-test-scenarios-store-keeper.md)
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Scenarios ข้าม Persona / การส่งต่อ

ตารางด้านล่างคือ integration layer แต่ละ row span อย่างน้อยหนึ่งการส่งต่อจาก [03-user-flow.md](./03-user-flow.md) Section 4 และจบที่ระบบในสถานะ terminal หรือ steady "Personas in order" รายชื่อ actors ใน execution sequence; "Pre-condition" จับสถานะระบบที่ต้องการเพื่อเริ่ม; "Expected end state" anchor การ post inventory transaction, ผล cost-layer / on-hand และสถานะงวด

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Routine inbound stock-in (ต่ำกว่า threshold, auto-approve) | Store Keeper | Source: found-stock สำหรับ lot ที่มีอยู่; มี scope `tb_user_location`; ผลกระทบต้นทุนรวมต่ำกว่า Store-Keeper auto-approve threshold; งวด `open` | `tb_stock_in.doc_status = completed`; หนึ่ง row `tb_inventory_transaction` (`inventory_doc_type = stock_in`, `enum_transaction_type = adjustment_in`); หนึ่ง inbound cost-layer row (`in_qty > 0`); on-hand ที่ `(location, product, lot)` ก้าวหน้า; ไม่มีการส่งต่อ |
| 2 | Stock-out เหนือ threshold route ไปยัง Inventory Controller | Store Keeper → Inventory Controller | Source: breakage write-off; ผลกระทบต้นทุนรวมเหนือ auto-approve threshold แต่ต่ำกว่า Finance threshold; งวด `open` | หลังจากการอนุมัติ Controller: `tb_stock_out.doc_status = completed`; หนึ่ง outbound `tb_inventory_transaction`; outbound cost-layer (FIFO หรือ WA cost pick ตามสินค้า); on-hand ลด Activity log บันทึก `{ actor: controller, action: 'approve_post' }` |
| 3 | Adjustment ต้นทุนใหญ่ route Controller → Finance | Store Keeper → Inventory Controller → Finance | Source: recall write-off; ผลกระทบต้นทุนรวมเหนือ Controller threshold; งวด `open` | หลังจากการอนุมัติ Finance: `tb_stock_out.doc_status = completed`; outbound inventory transaction; cost-layer rows; on-hand ลด GL entry post ไปยังบัญชี recall-write-off ตาม adjustment reason code |
| 4 | Physical count พร้อม variance — overage และ shortage lines | Store Keeper → Inventory Controller | Scheduled count สำหรับ `tb_location.physical_count_type = yes`; เอกสาร count ที่ `tb_count_stock.status = completed` พร้อม variance lines; บาง overage บาง shortage; รวมต้นทุนต่ำกว่า Controller threshold | บน Controller commit-of-count: rollup `tb_stock_in` (overage) + `tb_stock_out` (shortage) auto-advance ไปที่ `completed`; หนึ่งหรือมากกว่า inventory transactions ต่อ rollup; cost-layer rows; on-hand reconcile ไปยัง counted qty; เอกสาร count ที่ `completed_posted` |
| 5 | Happy path ปิดงวด (ไม่มี variance, ไม่มี holds) | Inventory Controller → Finance → Finance Manager | Adjustments / counts / GRNs / SRs ที่อยู่ระหว่างทางทั้งหมดสำหรับงวดที่สถานะ terminal; เซ็นรับรอง variance ของ Controller เสร็จ; inventory-to-GL reconciliation ผ่าน | Finance run close: `tb_period.status = open → closed`; rows `tb_period_snapshot` เขียนต่อ `(period, location, product, lot)`; rows `close_period` + `open_period` cost-layer เขียน; งวดถัดไป `open` หลังจาก audit window: Finance Manager run lock — `tb_period.status = closed → locked` |
| 6 | Hold flag variance ปิดงวด | Inventory Controller → Finance | Pending count variance line ที่ flag `investigate` จาก count run ก่อนหน้า; Controller ไม่ได้เซ็นรับรองงวด | Finance close run **block** — Controller ไม่ได้เซ็นรับรอง variance Finance สื่อสาร hold; Controller แก้ไข investigation; เซ็นรับรอง; Finance re-run close |
| 7 | FIFO outbound spanning สอง lots | Store Keeper (ผ่าน SR) | สินค้าที่ `costing_method = FIFO`; สอง lots ที่มีอยู่ที่ source location ด้วย `lot_seq_no` ต่างกันและ `cost_per_unit` ต่างกัน; SR-approved issue สำหรับ qty ใหญ่กว่ายอดของ lot ที่เก่าที่สุด | Single outbound `tb_inventory_transaction`; **สอง** outbound cost-layer rows — หนึ่ง consume lot ที่เก่าที่สุดเต็มที่ `cost_per_unit`, หนึ่ง consume ส่วนที่เหลือจาก lot ที่เก่ารองที่ `cost_per_unit` On-hand ลดตามตาม `INV_CALC_005` |
| 8 | Weighted-average inbound recompute | Store Keeper (ผ่าน GRN) | สินค้าที่ `costing_method = WEIGHTED_AVERAGE`; on-hand ที่มีอยู่ที่ต้นทุนหนึ่ง; GRN receipt ใหม่ที่ต้นทุนต่างกัน | GRN commit เขียน inbound inventory transaction; cost-layer row carry `cost_per_unit` ใหม่และ recomputed `average_cost_per_unit = (prior_on_hand × prior_average + in_qty × in_cost) / (prior_on_hand + in_qty)` ตาม `INV_CALC_007` Outbound ต่อมาที่ location นี้อ่าน average ใหม่ |
| 9 | Inbound concurrent ไปยัง location / สินค้า / lot เดียวกัน | Store Keeper (×2) | Sessions / Store Keepers สองคน post inbound ไปยัง `(location, product, lot)` เดียวกันพร้อมกัน (เช่นสอง GRN commits ในนาทีเดียว หรือสอง count-overage stock-ins) | Inventory transactions ทั้งสอง post สำเร็จ (ไม่มี row-level lock conflict เพราะ inserts เป็น append-only); cost-layer rows สำหรับทั้งสอง order ตาม `lot_seq_no`; on-hand ที่ `(location, product, lot)` ก้าวหน้าโดยผลรวม FIFO ordering รักษา; weighted-average recompute ตามลำดับ |
| 10 | ความพยายาม balance ติดลบถูก reject | Store Keeper | Outbound stock-out พยายามสำหรับ qty ใหญ่กว่า on-hand ปัจจุบันที่ `(location, product, lot)`; tenant policy คือ "no negative balance" (default ตาม `INV_VAL_005`) | Submit reject pre-post ด้วย `"Outbound movement would drive on-hand at (location, product, lot) below zero. Available: X, requested: Y."` เอกสารอยู่ที่ `draft`; ไม่มี inventory transaction เขียน; Store Keeper ลด qty, pick lot ต่าง หรือ escalate ไปยัง Controller |
| 11 | Post ย้อนหลังเข้างวดที่ปิดถูก reject | Store Keeper / Inventory Controller / Finance | เอกสาร source ด้วยวันที่ transaction ภายในงวด `closed`; user พยายาม submit / approve | Submit / approve reject ตาม `INV_VAL_008` ด้วย `"Cannot post into period <YYMM>: period is closed. Re-open the period or post a current-period restatement."` ไม่มี inventory transaction เขียน Finance Manager re-open เป็นการกระทำ elevated audit-logged; งวด `locked` re-open ไม่ได้ |
| 12 | Credit-note amount adjustment — การลดราคาหลัง receipt | Finance | GRN `committed` มีอยู่; vendor ยอมลดราคาหลัง receipt; credit-note (`tb_credit_note`) อนุมัติที่ Finance | `tb_inventory_transaction` เขียน (`inventory_doc_type = credit_note`, `enum_transaction_type = credit_note_amount`); cost-layer row ด้วย `in_qty = out_qty = 0`, `diff_amount = signed_amount`; ปรับ `cost_per_unit` ของ lot ต้นทางตาม `INV_CALC_011`; consumption ปลายน้ำจาก lot pick up ต้นทุนที่ revalue |
| 13 | Lot-recall trace — chain-of-custody จาก GRN ไปยัง consumption | Audit / Config (Auditor) | Lot ที่กระทบโดย vendor recall; lot ถูกแนะนำโดย GRN `committed`, issue บางส่วนผ่าน SR, write off บางส่วนผ่าน stock-out พร้อม credit-note amount adjustment | Backward trace return GRN ที่แนะนำ lot Forward trace return ทุก movements ปลายน้ำที่ consume จาก lot: SR issues, stock-out write-offs, credit-note quantity adjustments รายงาน chain-of-custody render ทั้งสองทิศทาง; ไม่มีการเปลี่ยน state transaction |
| 14 | Direct-cost location receipt (ไม่มีผลกระทบ balance) | Store Keeper | GRN receipt ไปยัง location ด้วย `tb_location.location_type = direct` (เช่น kitchen station); qty receipt สินค้าบวก | `tb_inventory_transaction` เขียนสำหรับ audit; **ไม่มี cost-layer row** ตาม `INV_POST_003`; GL: `Dr Department Expense / Cr AP` ตรง ๆ; ไม่มี on-hand ที่ direct location (direct locations ไม่ถือ balance) |
| 15 | Consignment location receipt (memo เท่านั้น) | Store Keeper | GRN receipt ไปยัง `location_type = consignment` location; vendor-owned stock | `tb_inventory_transaction` เขียน; consignment-flagged cost-layer row เขียน (memo register); **ไม่มี Inventory asset debit, ไม่มี AP credit ที่ receipt** ตาม `INV_POST_004` บน consumption (scenario แยก) AP และ COGS post พร้อมกันตาม `INV_POST_005` |
| 16 | Sysadmin location-type change block โดย on-hand ไม่เป็นศูนย์ | Audit / Config (Sysadmin) | Location `inventory`-type ที่มีอยู่ด้วย on-hand ไม่เป็นศูนย์; Sysadmin พยายามเปลี่ยน `location_type` เป็น `direct` | Impact preview reject ตาม `INV_AUTH_008` drain requirement; configuration ไม่ save; Sysadmin ต้อง drain on-hand ก่อน (transfer / write off) ก่อนลองอีกครั้ง |
| 17 | Period re-open (การแก้ไขใน audit-window) | Finance Manager | งวดที่ `tb_period.status = closed`, ภายใน audit window; external auditor ระบุ adjustment ยกเว้นที่ต้องการ | Finance Manager re-open (`closed → open`) ตาม `INV_AUTH_006` พร้อม justification ระดับ audit; corrective adjustment post เป็น movement ใหม่ในงวดที่ re-open; Finance re-close งวดก่อนปิดงวดถัดไป Audit log บันทึก re-open และ re-close |

## 5. การ Map E2E Test

โมดูล inventory ถูก **exercise บางส่วน** โดย Playwright spec files สามไฟล์; ไม่มี `inventory.spec.ts` เดียวที่ครอบคลุมทุกเส้นทาง inventory เพราะผล inventory ส่วนใหญ่ fan out จาก commits เอกสารต้นน้ำ Coverage จึงกระจาย

| Spec / describe block | Scenarios ข้าม persona ครอบคลุม (Section 4) |
| --------------------- | ------------------------------------------- |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | 5 (happy path ปิดงวด), 6 (hold flag variance), 11 (reject post ย้อนหลัง), 17 (period re-open) |
| [`720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) | 2 (stock-out ที่ Store Keeper เริ่มต่ำกว่า Finance threshold), 7 (FIFO outbound spanning lots), 10 (reject balance ติดลบ) |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Stock Movements describe block (TC-GRN-900014) | 1 (routine inbound จาก GRN commit — ผลฝั่ง inventory ของ GRN), 8 (weighted-average inbound recompute บน GRN commit), 9 (inbound concurrent บน GRN commit), 14 (direct-cost location receipt), 15 (consignment location receipt) |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Commit / Void describe blocks (TC-GRN-900011, TC-GRN-900012) | 1, 14, 15 (ผลฝั่ง inventory ของ commit และ void) |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) (โมดูล credit-note) | 12 (credit-note amount adjustment — ผลฝั่ง inventory) |
| [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) (โมดูล store-requisition) | 2, 7 (SR-driven outbound และ FIFO consumption) |

Gaps relative to Section 4:

- Scenario 3 (chain การอนุมัติต้นทุนใหญ่ Controller → Finance) ไม่ครอบคลุมโดย spec เดียว; ชิ้นส่วน approval-routing อาศัยอยู่ใน specs โมดูล source (flow stock-in, flow stock-out) และผล inventory สังเกตโดยอ้อมผ่าน stock-movement assertions
- Scenario 4 (commit physical-count variance) ครอบคลุมบางส่วนใน specs โมดูล count (ยังไม่ link ที่นี่); rollup posting ฝั่ง inventory คือเทส manual / planned
- Scenario 13 (lot-recall trace) อาศัยอยู่ใน specs โมดูล audit (นอก spec set โมดูล inventory); specs audit-query อ่านอย่างเดียวโดยทั่วไปคือเทส manual planned ในไฟล์ persona Auditor
- Scenario 16 (Sysadmin location-type change) อาศัยอยู่ใน spec admin location-config (`080-location.spec.ts`); blocker ฝั่ง inventory คือ validation manual / planned

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — period-end E2E แบบ canonical
- [`../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) — เส้นทาง stock-out / stock-issue; พื้นผิว outbound inventory
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — ผลฝั่ง inventory ของ GRN commit (Stock Movements describe block)
- [`../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) — ผล inventory ของ credit-note
- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — ผล inventory ของ store-requisition
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — การส่งต่อข้าม persona ที่ขับ scenarios integration ด้านบน
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation (Section 2), calculation (Section 3), authorization (Section 4), posting (Section 5) และ cross-module (Section 6) ที่ทุก scenario ด้านบน invoke
- รายละเอียดต่อ persona: [Store Keeper](./04-test-scenarios-store-keeper.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md)
