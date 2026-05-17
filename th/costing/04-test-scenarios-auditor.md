---
title: การคำนวณต้นทุน (Costing) — Test Scenarios — Auditor
description: Test cases ของ Auditor (chain-of-custody trace, period-snapshot verification, FIFO-WA shadow drift, configuration history audit) สำหรับ costing
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, test-scenarios, auditor, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios — Auditor

> **At a Glance**
> **Persona:** Auditor &nbsp;·&nbsp; **Module:** [[costing]] &nbsp;·&nbsp; **Scenarios:** ~23
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** map ไปยัง `900-period-end.spec.ts` ใน `../carmen-inventory-frontend-e2e/` (chain-of-custody / shadow-drift / configuration-history audits โดยทั่วไป planned manual coverage)

หน้านี้จับ test scenarios ที่ Auditor persona ขับเคลื่อนในโมดูล `costing` Auditor **read-only แท้ ๆ** ข้าม `tb_inventory_transaction_cost_layer`, `tb_period_snapshot`, `tb_business_unit.calculation_method`, `tb_product.standard_cost`, และ configuration history feed per `COST_AUTH_008` รัน **4 query patterns**:

(1) **cost-flow chain-of-custody trace** — forward + backward walk ของ cost-flow ของ lot ผ่านทุก inbound, revaluation, consumption, transfer, และ period rollforward event
(2) **period-end snapshot verification** — defensive reconciliation ว่า snapshot's `closing_cost_per_unit` / `closing_total_cost` ตรงกับ independent reconstruction
(3) **FIFO-vs-WA shadow drift audit** — Auditor independently recomputes running WA และตรวจสอบว่า shadow consistent
(4) **configuration history audit** — ทุก change ของ `tb_business_unit.calculation_method`, `enum_physical_count_costing_method` config value, และ `tb_product.standard_cost` review ตาม pre-condition compliance

Auditor ไม่ปรากฏใน transactional flow — Auditor ไม่เคยแก้ cost-layer row, ไม่เคยอนุมัติ credit-note, ไม่เคย advance period, ไม่เคย configure method Deliverable ของ Auditor คือ audit report

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| AUD-HP-01 | Chain-of-custody trace — clean forward + backward walk | Auditor logged in; lot `LOT-RECALL-42` introduced by `committed` GRN ที่ `2026-04-10`, partially issued ผ่าน 2 SR transactions, partially written off ผ่าน 1 stock-out, with 1 credit-note-amount revaluation | 1. เปิด chain-of-custody trace tool 2. Enter `lot_no = LOT-RECALL-42` 3. รัน trace 4. Review backward trace (GRN that introduced) 5. Review forward trace (2 SR issues, 1 stock-out, 1 credit-note-quantity ถ้ามี, บวก credit-note-amount revaluation) 6. ยืนยัน consumption cost ของแต่ละ row ตรงกับ engine's cost-pick under then-configured `calculation_method` 7. Export chain-of-custody report | Backward trace returns source GRN with metadata Forward trace returns 2 SR issues, 1 stock-out, 1 credit-note-amount revaluation row Method-consistency annotation: ทุก rows resolved correctly under FIFO method PDF / CSV export ไม่มี transaction state change Map ไปยัง parent Scenario 11 |
| AUD-HP-02 | Period-end snapshot verification — clean reconciliation | Closed period `2026-04`; `tb_period_snapshot` rows written; Auditor runs independent reconstruction query | 1. เปิด period-end verification tool scoped to `2026-04` 2. Read snapshot rows 3. Independently reconstruct จาก `tb_inventory_transaction_cost_layer` per `COST_CALC_006` 4. ยืนยัน rollforward continuity per `COST_CALC_007` 5. Export verification report | ทุก per-key reconciliations clean (snapshot = reconstruction); rollforward continuity confirmed; FIFO `lot_seq_no` preserved บน `open_period` rows Report exports ไม่มี anomalies Map ไปยัง parent Scenario 12 |
| AUD-HP-03 | FIFO-WA shadow drift audit — within tolerance | FIFO business unit `BU-A`; period `2026-04` of normal activity; Auditor runs shadow-drift audit | 1. เปิด shadow-drift tool scoped to `BU-A` และ `2026-04` 2. Read each cost-layer row's `average_cost_per_unit` per `COST_CALC_004` 3. Independently recompute running WA จาก first inbound 4. Compare per row 5. Export drift report | ทุก rows within rounding tolerance (`≤ ฿0.10` per row) Drift report shows zero above-tolerance rows Verification clean Map ไปยัง parent Scenario 13 |
| AUD-HP-04 | Configuration history audit — clean (no anomalies) | ทุก `calculation_method` changes ใน last 12 months pre-conditioned by drain check; ทุก `standard_cost` updates เป็น prospective; ไม่มี mid-period method change | 1. เปิด configuration history feed 2. List ทุก `calculation_method` change 3. Per change: ยืนยัน zero on-hand ที่ save timestamp; ยืนยัน change applied prospectively 4. List ทุก `standard_cost` batch update 5. ยืนยันไม่มี `calculation_method` change cross period boundary mid-period 6. Export consistency report | ทุก checks clean; consistency report exports ไม่มี anomalies flagged |
| AUD-HP-05 | Sensitive-field export with secondary approval | Auditor ต้องการ export cost-flow report รวม unit costs และ vendor terms; tenant policy requires Controller หรือ DPO co-approval | 1. Build filter 2. Tick **Include unit costs** และ **Include vendor terms** 3. คลิก **Request export** 4. System routes to Controller for approval 5. Controller approves with justification 6. System generates watermarked CSV | Export request raised with sensitive flag; Controller approval prompt; watermarked CSV generated; audit-of-audit log entry |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| AUD-PERM-01 | Auditor อ่าน `tb_inventory_transaction_cost_layer`, `tb_period_snapshot`, `tb_business_unit.calculation_method`, `tb_product.standard_cost`, config history | **Allow read-only per `COST_AUTH_008`** Full read across costing entities รวม soft-deleted rows |
| AUD-PERM-02 | Auditor พยายาม edit any costing entity | **Deny — role scope** Direct API write จาก Auditor token returns `403 Forbidden` พร้อม `"Auditor role is read-only on the costing module."` Logged บน audit-of-audit trail |
| AUD-PERM-03 | Auditor พยายามอนุมัติ credit-note-amount revaluation | **Deny — Finance only per `COST_AUTH_005`** Credit-note approval queue ไม่ visible |
| AUD-PERM-04 | Auditor พยายาม lock / re-open period | **Deny — Finance Manager only per `COST_AUTH_006`** Period-lock dashboard ไม่ visible |
| AUD-PERM-05 | Auditor พยายามเปลี่ยน `tb_business_unit.calculation_method` | **Deny — Sysadmin only per `COST_AUTH_001`** |
| AUD-PERM-06 | Sensitive-field export — secondary approval required | **Allow พร้อม secondary approval** Per AUD-HP-05 costing exports รวม unit costs, vendor terms, หรือ PII ต้องการ Controller หรือ DPO co-approval |

## 3. Validation / Anomaly Surfacing

| # | Scenario | Trigger | Expected error / behaviour |
| - | -------- | ------- | -------------------------- |
| AUD-VAL-01 | Trace surfaces orphan layer (source GRN soft-deleted) | `tb_inventory_transaction_cost_layer.lot_no = LOT-GAP-9` row exists แต่ source GRN ของ inventory transaction soft-deleted | **Surface gap ใน trace report** Forward trace returns downstream consumption successfully; backward trace flags `"Source document for inventory transaction <Y> is soft-deleted or missing; provenance gap. Recommend forensics."` |
| AUD-VAL-02 | Snapshot verification surfaces mismatch | Period `2026-04` `tb_period_snapshot.closing_total_cost = ฿10,000.00`; Auditor's independent reconstruction returns `฿10,156.00` (variance `฿156.00`) | **Surface variance ใน verification report** Drill identifies cause: missed `credit_note_amount` row ใน `2026-04`'s closing post-dated เป็น `2026-05` Report flags row; routes to Finance Manager เพื่อ re-open `2026-04` |
| AUD-VAL-03 | Shadow drift above tolerance | FIFO business unit; cost-layer row ที่ `T` shows `average_cost_per_unit = ฿12.50`; independent WA recompute ที่ `T` yields `฿14.80` (drift `฿2.30`, เหนือ `฿0.10` tolerance) | **Surface ใน drift report** Drill: out-of-order cost-layer write ทำให้ shadow คำนวณเทียบกับ wrong prior state Report routes to Sysadmin และ Finance |
| AUD-VAL-04 | Configuration history surfaces method-change anomaly | Configuration history shows `calculation_method` change บน `BU-A` ที่ `T` ขณะ `BU-A` มี non-zero on-hand | **Surface ใน consistency report** Drill: change slipped through Report flags change เป็น anomalous; routes to Sysadmin + Finance สำหรับ forensic |
| AUD-VAL-05 | Method-change mid-period detected | Configuration history shows `calculation_method` change บน `BU-A` ที่ `2026-04-15 14:00` (mid-period `2026-04`) | **Surface ใน consistency report** Period's COGS / snapshot เป็น method-inconsistent Report flags; routes to Finance Manager + Sysadmin |
| AUD-VAL-06 | Auditor write attempt rejected | Auditor API call `PATCH /cost-layer/{id} {"cost_per_unit": 99}` | **Deny พร้อม audit-of-audit log per AUD-PERM-02** Server returns `403`; audit-of-audit trail records `{ event: 'unauthorised_write_attempt', actor: auditor, target: 'cost_layer', timestamp: T }` |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| AUD-EDGE-01 | Lot revaluation in mid-trace — cost continuity preserved | Lot `LOT-Y` introduced ที่ `cost_per_unit = ฿15`; partially consumed (10 of 20 units at `฿15` — COGS for those 10 = `฿150`); credit-note-amount revaluation `diff_amount = −฿50` brings `LOT-Y` cost to `(20×15 − 50)/20 = ฿12.50`; remaining 10 units consumed at `฿12.50` | **Trace report shows cost-step** Forward trace renders 10-unit consumption ที่ `฿15` (pre-revaluation), `diff_amount = −฿50` revaluation row ที่ `T`, then 10-unit consumption ที่ `฿12.50` (post-revaluation) Cost-step consistent กับ `COST_CALC_005` |
| AUD-EDGE-02 | Locked-period restatement audit | `2026-03` is `locked`; restatement adjustment posted ใน `2026-05` references `2026-03` ผ่าน note field | **Trace surfaces cross-period reference** Forward trace from `2026-03` lot extends into `2026-05` ผ่าน restatement cost-layer row; row's `note` / `info` JSON carry cross-period reference |
| AUD-EDGE-03 | Query timeout on huge dataset | Auditor's chain-of-custody trace filter spans 12 months across all locations + lots; query เกิน tenant compute budget | **Graceful timeout with partial result** Server cancels at configured timeout (e.g. 60s); returns partial result with `truncated = true` flag |
| AUD-EDGE-04 | Mass-trace export for recall investigation | Auditor ต้องการ traces สำหรับ 100+ lots (multi-lot recall) | **Batch export with rate-limit และ progress bar** Auditor enters lot list; system queues batch trace; renders progress; produces consolidated PDF / CSV export |
| AUD-EDGE-05 | Shadow drift exactly at tolerance | Drift `฿0.10` exactly equals tolerance `฿0.10` | **Boundary inclusive — clean** `≤ tolerance` is clean; `> tolerance` flagged |
| AUD-EDGE-06 | Snapshot reconciles after EOP price revaluation | `eop_in / eop_out` cost-layer row at period boundary captures EOP price revaluation. Auditor's snapshot verification accounts for revaluation in `adjustment_total_cost` | **Reconciliation includes EOP revaluation bucket per `COST_CALC_010`** `Σ diff_amount` ใน `adjustment_total_cost` rollup Snapshot verification passes; report annotates EOP revaluation event |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-auditor.md](./03-user-flow-auditor.md)
- Business rules: [02-business-rules.md](./02-business-rules.md)
- Sibling: [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)
- Sibling: [04-test-scenarios-inventory-controller.md](./04-test-scenarios-inventory-controller.md)
- Sibling: [01-data-model.md](./01-data-model.md)
- Sibling: [calculation-methods.md](./calculation-methods.md)
- E2E specs: [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts)
- Cross-link: [[inventory/04-test-scenarios-audit-config]]
- Cross-link: [[good-receive-note]]
- Cross-link: [[store-requisition]]
- Cross-link: credit-note
- Cross-link: [[physical-count]] / [[spot-check]]
