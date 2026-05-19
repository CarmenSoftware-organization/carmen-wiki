---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Finance
description: Test cases ของ Finance (happy path, permission, validation, edge cases) สำหรับการปรับสต๊อก
published: true
date: 2026-05-19T23:55:00.000Z
tags: inventory-adjustment, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Finance

> **At a Glance**
> **Persona:** Finance &nbsp;·&nbsp; **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; **Scenarios:** ~26
> **ประเภท:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** map ไปยัง `900-period-end.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้ capture test scenarios ที่ persona Finance ขับเคลื่อนโดยตรงในโมดูล `inventory-adjustment` Finance เป็นเจ้าของ **การตรวจสอบผลกระทบต้นทุนและ GL-mapping**: อนุมัติ adjustments เหนือ Controller-threshold (recall / damage / theft write-offs ขนาดใหญ่), ตรวจสอบว่า `info.glAccount` ที่ resolve ตรงกับ chart of accounts, reconcile inventory sub-ledger กับ GL ที่ปิดงวด และ sign-off กิจกรรม adjustment ปลายงวดก่อน period close ของ Finance Manager `tb_period.status` ตาม [inventory](/th/inventory/inventory) `INV_AUTH_006` Scenarios group เป็น **happy paths** (อนุมัติต้นทุนขนาดใหญ่, การตรวจสอบ GL-mapping, review และ sign-off ปลายงวด, การริเริ่ม void), **RBAC** (scope Finance vs scope Controller / Finance-Manager), **validation** (กฎที่ re-check ที่อนุมัติ) และ **edge cases** รอบ routing การ recovery, scenarios period-reopen, การสืบสวน cost-anomaly

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | ------------- | ----- | -------- |
| FN-HP-01 | อนุมัติ recall write-off ที่ Controller forward (ต้นทุนขนาดใหญ่) | Finance `finance@blueledgers.com` login; `tb_stock_out` ที่ Controller forward ที่ `doc_status = in_progress`, reason `RECALL_WRITE_OFF`, total `฿85,000` (เหนือ Controller threshold `฿10,000`); recall notice แนบ; lots ตรง notice | 1. เปิด Finance Approval queue 2. เปิดเอกสาร 3. ตรวจสอบบริบท recall: vendor notice, หมายเลข lot, ขอบเขต geographic ตรง 4. ตรวจสอบ FIFO cost-pick `฿42.50` จาก `LOT-2023-Q4` กับประวัติต้นทุน GRN และ [vendor-pricelist](/th/inventory/vendor-pricelist) — อยู่ในช่วง 5. ตรวจสอบ `info.glAccount` resolve ไปยัง `6540 — Product Recall Loss` (active ในงวดปัจจุบัน) 6. ตรวจสอบ `dimension.department` ตรงกับ cost-centre ที่รับผิดชอบ 7. คลิก **Approve** | `tb_stock_out.doc_status = in_progress → completed` ตาม `ADJ_POST_002` `tb_inventory_transaction` ขาออก; cost-layer rows (FIFO, multi-row ถ้า span lots); GL `Dr 6540 Product Recall Loss ฿85,000 / Cr Inventory ฿85,000` `workflow_history` บันทึก `finance_approved` Map ไปยัง parent Scenario 3 |
| FN-HP-02 | Reject เนื่องจากปัญหา GL-mapping | `tb_stock_out` ที่ Controller forward reason `BREAKAGE` (`info.glAccount = "6510"`) แต่เอกสารเกี่ยวกับ scenario vendor-recall ที่ reason ที่ถูกต้องคือ `RECALL_WRITE_OFF` (`6540`) | 1. เปิดเอกสาร 2. สังเกต reason / scenario mismatch 3. คลิก **Reject** ด้วย comment "Reason should be `RECALL_WRITE_OFF`, not `BREAKAGE` — different GL account" | เอกสาร return ไปยัง `draft` สำหรับการแก้ไข Store-Keeper + Controller re-forward ด้วย reason ที่ถูกต้อง Finance ไม่ override reason โดยตรง; เอกสาร re-cycle ผ่าน threshold ladder ด้วยการจัดประเภทที่ถูกต้อง |
| FN-HP-03 | Send-back ไปยัง Controller สำหรับหลักฐานเพิ่มเติม | `tb_stock_out` ที่ Controller forward ขาด insurance-claim reference; reason เป็น `THEFT_WRITE_OFF` (ต้นทุนขนาดใหญ่) | 1. เปิดเอกสาร 2. Comment "Insurance claim reference required before approval; confirm with security incident report." 3. คลิก **Send back to Controller** | เอกสารคงอยู่ `in_progress`; Controller re-engage, ขอ Store Keeper แนบ insurance reference, Controller re-forward |
| FN-HP-04 | อนุมัติด้วย flow credit-note คู่ขนาน | Recall write-off ด้วย vendor-credit recovery คู่ขนานอยู่ใน flight ผ่านโมดูล credit-note ของ [good-receive-note](/th/inventory/good-receive-note) | 1. เปิดเอกสาร 2. ตรวจสอบว่า `tb_credit_note` คู่ขนานมีอยู่และอนุมัติแล้ว 3. อนุมัติ adjustment write-off ที่ต้นทุนเต็ม (credit-note recover ต้นทุนแยกเป็นการลด AP) 4. Optional: comment cross-link credit-note สำหรับ audit | `tb_stock_out.doc_status = completed`; ผลกระทบ inventory apply Credit-note แยก post `Dr AP / Cr <vendor-recovery account>` Net P&L impact = write-off ลบ recovery |
| FN-HP-05 | Review และ sign-off ปลายงวด (happy path) | Adjustments `completed` ทั้งหมดในงวด `2026-04`; aggregate variance vs GL Inventory control = `฿0` (ภายใน tolerance); ไม่มี anomalies ที่ flag | 1. เปิด Period-end Review สำหรับ `2026-04` 2. Review aggregate ผลกระทบต้นทุนต่อ reason (totals ตรงช่วง operational ที่คาดหวัง) 3. ตรวจสอบ reconciliation ผ่าน (variance ≤ tolerance) 4. ไม่มี outliers ที่ flag 5. คลิก **Period Approve** | กิจกรรม adjustment ของงวดอนุมัติโดย Finance Finance Manager (ผู้ใช้คนเดียวกันหรือคนละคน) ทำ `tb_period.status = open → closed` ตาม [inventory](/th/inventory/inventory) `INV_AUTH_006` Period close cascade ฝั่ง inventory `INV_POST_009` / `INV_POST_010` ตาม [inventory](/th/inventory/inventory) |
| FN-HP-06 | ริเริ่ม void บน adjustment ที่ post ก่อนหน้านี้ | `tb_stock_in` ที่ `completed` จากสัปดาห์ก่อน ระบุ post-fact ว่าเป็น duplicate (เหตุการณ์ vendor-replacement เดียวกันรายงานสองครั้งโดยสอง SKs) | 1. Finance เปิด duplicate 2. คลิก **Void** → Create compensating reversal 3. Form compensating `tb_stock_out` pre-fill ด้วย `info.voidsAdjustmentId = <original_id>` 4. Finance อนุมัติโดยตรง (อำนาจ Finance ครอบคลุม compensating reversal) 5. Compensating post; ต้นฉบับ `doc_status = voided` | ตาม `ADJ_POST_004` สองขั้น On-hand restore ไปยังสถานะก่อน duplicate Inventory transaction ต้นฉบับ NOT edit ตาม [inventory](/th/inventory/inventory) `INV_POST_012` Auditor inspect void-chain ตาม `ADJ_AUTH_009` (และ FN-HP-08-equivalent ใน audit-config) |
| FN-HP-07 | อนุมัติ adjustment ที่ flag direct-cost-impact | Anomaly alert fire บน adjustment ที่ post (cost-per-unit > 3× ของค่าเฉลี่ย vendor 90 วัน); จุดเข้า review reactive | 1. เปิด detail alert / adjustment 2. สืบสวนประวัติ cost-layer: การรับก่อนหน้าที่ราคาสูงระหว่าง supply shock; ต้นทุน defensible 3. Annotate finding ใน comment; ปิด anomaly flag | ไม่มีการเปลี่ยนสถานะบน adjustment เอง (`completed` แล้ว); review Finance บันทึกใน comment Anomaly resolve ด้วย annotation |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| FN-PERM-01 | อนุมัติเอกสาร `in_progress` เหนือ Controller-threshold | **Allow ตาม `ADJ_AUTH_005`** Finance เป็น third signature ใน threshold ladder; ครอบคลุม adjustments เหนือ Controller-threshold |
| FN-PERM-02 | อนุมัติเอกสารต่ำกว่า Controller-threshold โดยตรง | **Allow (over-approval)** Finance สามารถอนุมัติ tier threshold ใด ๆ (ทำหน้าที่เป็นอำนาจที่สูงกว่า) Flow ทั่วไปมี Controller อนุมัติต่ำกว่า Controller-threshold; Finance อนุมัติต่ำกว่า Controller-threshold หายากแต่อนุญาต (เช่น Controller ไม่อยู่) |
| FN-PERM-03 | Finance พยายามแก้ไขเอกสาร `completed` | **Deny ตาม `ADJ_VAL_013`** ต้องใช้ void + compensating reversal |
| FN-PERM-04 | Finance กำหนดค่า `tb_adjustment_type` หรือ thresholds | **Deny — Sysadmin required** ตาม `ADJ_AUTH_008` Finance ขอการเปลี่ยนการกำหนดค่าแต่ไม่ execute |
| FN-PERM-05 | Finance ทำ `tb_period.status = closed → locked` | **Deny — Finance Manager required** ตาม [inventory](/th/inventory/inventory) `INV_AUTH_006`, period close / lock ต้องการ Finance Manager (บทบาท elevated ที่ distinct; tenants บางตัวมอบหมายให้ผู้ใช้คนเดียวกัน) Finance role ของโมดูล adjustment sign-off ฝั่ง adjustment ของ period end; Finance Manager fire การเปลี่ยน period-status |
| FN-PERM-06 | Finance void ริเริ่ม compensating reversal | **Allow ตาม `ADJ_AUTH_007` / `ADJ_POST_004`** Finance สามารถริเริ่ม void บนเอกสาร `completed` ใด ๆ (เหมือนกับ Inventory Controller) |
| FN-PERM-07 | Finance สร้าง adjustment ใหม่โดยตรง | **Allow** Finance มีอำนาจสร้าง (บทบาทใด ๆ เหนือ Store Keeper สามารถสร้าง); การใช้ทั่วไปคือ reason `DATA_FIX` สำหรับการแก้ไข sub-ledger / GL reconciliation |
| FN-PERM-08 | Finance พยายาม back-post เข้างวด `closed` | **Deny ตาม `ADJ_VAL_011` / [inventory](/th/inventory/inventory) `INV_VAL_008`** Re-open เป็น scope Finance Manager ตาม [inventory](/th/inventory/inventory) `INV_AUTH_006` Finance ขอ re-open; Finance Manager grant ถ้าพิเศษ |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| FN-VAL-01 | Approve fail บน stale on-hand (`ADJ_VAL_012`) | เอกสารที่ Finance approval; posting อื่นบริโภคจาก lot เหลือ on-hand ไม่เพียงพอ | เหมือนกับ IC-VAL-01: live recheck reject approval; เอกสาร return ไปยัง `draft`; Store Keeper re-pick |
| FN-VAL-02 | Approve fail บน closed period (`ADJ_VAL_011`) | งวดปิดระหว่าง Controller forward และ Finance approval | Rejection ตาม [inventory](/th/inventory/inventory) `INV_VAL_008`; Finance ขอ Finance Manager re-open หรือประสาน current-period restatement |
| FN-VAL-03 | Approve fail บนบัญชี GL inactive | `info.glAccount` ที่ resolve อ้างอิงบัญชี GL ที่ lock สำหรับวันที่เอกสาร (เช่น retire ระหว่างการ restructure chart-of-accounts) | Rejection ที่ approval ด้วย `"GL account <code> is not active for the document date."` Finance ประสานกับ Sysadmin เพื่ออัปเดต GL mapping ของ reason-code; เอกสาร return ไปยัง `draft` (หรือ re-cycle หลัง Sysadmin fix) |
| FN-VAL-04 | Period-end approve fail บน sub-ledger / GL variance | Reconciliation variance > tolerance | Sign-off block ด้วย `"Inventory sub-ledger and GL Inventory control account differ by ฿<X>; investigate before sign-off."` Finance สืบสวน, post adjustment `DATA_FIX` แก้ไข, re-run reconciliation |
| FN-VAL-05 | Period-end approve fail บน count-variance hold ที่เปิด | Controller ยังไม่ sign-off count-variance items ที่เปิดตาม parent Scenario 18 | Sign-off block ด้วย `"Inventory Controller has not signed off variances for the period."` Finance communicate hold; Controller resolve; Finance re-run Map ไปยัง parent Scenario 18 |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | --------- | -------- |
| FN-EDGE-01 | Finance อนุมัติที่ขอบ Controller threshold พอดี | ต้นทุนเอกสาร `฿10,000.00` พอดี | **Controller สามารถอนุมัติได้; Finance ก็สามารถ (over-approval)** Activity log แสดง Finance เป็นผู้อนุมัติ |
| FN-EDGE-02 | เอกสาร multi-reason ที่ Controller forward | เอกสาร multi-line เดียวด้วย reasons ผสม (`BREAKAGE` × 2 บรรทัด, `EXPIRY_WRITE_OFF` × 1 บรรทัด) | Finance ตรวจสอบ GL mapping ต่อบรรทัด — แต่ละบรรทัดของ reason resolve ไปยัง `info.glAccount` ของตัวเอง การอนุมัติ post inventory transaction เดียวด้วย details หลายตัว; cost-layer rows หลายแถว; GL credit / debit lines หลายตัว |
| FN-EDGE-03 | Period reconciliation tolerance apply | Tenant มี ±`฿1.00` rounding tolerance configure; variance = `฿0.75` | Reconciliation ผ่าน (ภายใน tolerance); sign-off ดำเนินการ Variance > `฿1.00` จุดชนวน FN-VAL-04 block |
| FN-EDGE-04 | Period re-open หลังปิด (scope Finance Manager) | External audit ระบุ adjustment ที่ขาดใน `2026-03` (closed); Finance Manager re-open | Finance Manager fire `tb_period.status = closed → open` ตาม [inventory](/th/inventory/inventory) `INV_AUTH_006` การพิสูจน์ระดับ audit log Finance สร้าง adjustment แก้ไขใน period ที่ re-open; submit / approve Finance Manager re-close ก่อน period close ปกติถัดไป Map ไปยัง parent Scenario ที่ครอบคลุมโดยอ้อม |
| FN-EDGE-05 | Currency rounding outlier บน FIFO multi-row | Stock-out สำหรับ qty 7 span 3 lots ที่ต้นทุนต่างกัน; total คำนวณที่ 5dp เต็ม; sum ของ totals บรรทัดที่ปัดเศษ 2dp ต่างจาก grand total ที่ปัดเศษ 2dp `฿0.01` | Finance ยอมรับ residual การปัดเศษภายใน `ADJ_CALC_011` tolerance; ledger เก็บ 5dp บนแต่ละแถวเพื่อให้ audit trail แม่นยำ; การแสดง 2dp อาจแสดง residual cent บน view ที่ roll up |
| FN-EDGE-06 | Cost anomaly alert บนผู้สมัคร duplicate-post | Adjustment ที่ post ด้วยต้นทุนนอกช่วงประวัติ; Finance สืบสวนและระบุว่าเป็น duplicate-post (ครอบคลุมโดย adjustment อื่นแล้วสำหรับเหตุการณ์เดียวกัน) | Finance ริเริ่ม void ผ่าน compensating reversal ตาม FN-HP-06; ต้นฉบับเคลื่อนไปยัง `voided` Anomaly resolve |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — handoff scenarios ที่ Finance เป็น protagonist: 3 (อนุมัติเหนือ Controller-threshold), 13 (การริเริ่ม void โดย Finance), 18 (period-end variance hold)
- User flow: [03-user-flow-finance.md](./03-user-flow-finance.md) — primary 10 ขั้น approval flow; flow review ปลายงวด; decision branches (cost-anomaly approve/reject/send-back, routing การ recovery, period close tolerance, scope re-open)
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) — `ADJ_AUTH_005` (อนุมัติ Finance), `ADJ_AUTH_007` (Finance void), `ADJ_POST_002` (post fan-out), `ADJ_POST_004` (void), `ADJ_XMOD_007` (การ reconcile Finance / GL)
- E2E specs: [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — approval gate ปลายงวด, variance hold, scenarios re-open ผู้ใช้ Finance fixture `finance@blueledgers.com`
- Cross-link: [inventory](/th/inventory/inventory) — `INV_AUTH_005` (scope การอนุมัติ Finance), `INV_AUTH_006` (Finance Manager period transitions), `INV_XMOD_008` (การ reconcile inventory-to-GL)
- Cross-link: [good-receive-note](/th/inventory/good-receive-note) — Finance อาจ chain flow credit-note สำหรับ vendor-recall recovery ต่อ GRN ต้นทาง
- Cross-link: [vendor-pricelist](/th/inventory/vendor-pricelist) — reference cost-anomaly ประวัติ
- Cross-link: [costing](/th/inventory/costing) — FIFO / WA cost picks ที่ Finance ตรวจสอบบน adjustments ขาออก
