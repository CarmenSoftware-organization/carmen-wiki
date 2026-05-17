---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Inventory Controller
description: Test cases ของ Inventory Controller (happy path, permission, validation, edge cases) สำหรับการปรับสต๊อก
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory-adjustment, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (+ Department Manager review) &nbsp;·&nbsp; **โมดูล:** [[inventory-adjustment]] &nbsp;·&nbsp; **Scenarios:** ~30
> **ประเภท:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **การครอบคลุม E2E:** map ไปยัง `720-stock-issue.spec.ts`, `900-period-end.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้ capture test scenarios ที่ persona Inventory Controller ขับเคลื่อนโดยตรงในโมดูล `inventory-adjustment` Controller คือ **อำนาจการกำกับเหนือ threshold auto-approve และเจ้าของความถูกต้องของยอด**: review และอนุมัติเอกสาร `in_progress` ในแบนด์ Controller threshold, validate new-lot stock-ins ไม่ว่าต้นทุน, commit บรรทัด count-variance (ที่ auto-create และ post เอกสาร rollup), forward เอกสารเหนือ Controller-threshold ไปยัง Finance, cancel ก่อน post หรือ void หลังการกระทำ และติดตามรูปแบบผลต่าง ความรับผิดชอบ review ของ Department Manager (การกำกับ cost-centre read-only) พับเข้ากับ persona group นี้ Scenarios group เป็น **happy paths** (review-and-approve เหนือ threshold, new-lot approval, count-variance commit, reject / cancel, forward ไปยัง Finance), **RBAC** (scope Controller vs scope Store Keeper / Finance, void authority), **validation** (กฎที่ re-check ตอนอนุมัติ) และ **edge cases** รอบ threshold borderline, count-rollup ด้วยผลผสม, flags การสืบสวน variance ขนาดใหญ่

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | อนุมัติ stock-out เหนือ threshold ที่ Store-Keeper submit | Inventory Controller `ic@blueledgers.com` login; `tb_stock_out` ที่ Store-Keeper submit ที่ `doc_status = in_progress`, reason `BREAKAGE`, total `฿2,500` (เหนือ auto-approve `฿500`, ต่ำกว่า Controller threshold `฿10,000`), หลักฐานแนบ | 1. เปิดโมดูล Inventory Adjustment → Pending Approvals 2. คลิกเข้าไปในเอกสาร 3. ตรวจสอบ reason ตรงกับหลักฐาน (`BREAKAGE` + รูปความเสียหาย) 4. ตรวจสอบบริบท: `BREAKAGE` ก่อนหน้าสำหรับ product / location นี้ 5. Review preview ต้นทุน: FIFO pick `LOT-1` ที่ `฿10.00` 6. คลิก **Approve** | `tb_stock_out.doc_status = in_progress → completed` ตาม `ADJ_POST_002` `tb_inventory_transaction` ขาออก; FIFO cost-layer rows; GL `Dr Breakage Expense ฿2,500 / Cr Inventory ฿2,500` `workflow_history` บันทึก `{stage: 'completed', action: 'approved', by: ic@blueledgers.com}` Map ไปยัง parent Scenario 2 |
| IC-HP-02 | อนุมัติ new-lot stock-in (defensibility ของต้นทุน) | `tb_stock_in` ที่ Store-Keeper submit ที่ `in_progress`; reason `VENDOR_FREE_REPLACEMENT`; new `lot_no = LOT-FOC`; `cost_per_unit = 0`; total `฿0` (FOC zero-cost) | 1. เปิดเอกสาร 2. ตรวจสอบ identity ของ new-lot well-formed ตาม `ADJ_VAL_009` 3. ตรวจสอบ defensibility ต้นทุน: zero-cost สอดคล้องกับ reason `VENDOR_FREE_REPLACEMENT`; vendor RMA แนบ 4. ตรวจสอบป้าย lot / expiry 5. Approve | ตาม `ADJ_AUTH_003`, Controller เป็น gate อนุมัติที่ระบุชัดเจนสำหรับ new-lot stock-ins เอกสาร `doc_status = completed` New `lot_no = LOT-FOC` สร้างด้วย `cost_per_unit = 0`, `lot_seq_no = max+1` WA recompute dilute average ตาม `ADJ_CALC_005` Map ไปยัง parent Scenario 4 |
| IC-HP-03 | Reject stock-out ที่มี reason / หลักฐาน mismatched | `tb_stock_out` ที่ Store-Keeper submit ที่ `in_progress`; reason `EXPIRY_WRITE_OFF` แต่ lot ไม่หมดอายุ (วันที่ expiry บนป้าย lot คือ 6 เดือนข้างหน้า) | 1. เปิดเอกสาร 2. สังเกต expiry mismatch บน lot 3. คลิก **Reject** 4. กรอกเหตุผล rejection: "Lot not expired; use correct reason code (e.g. `BREAKAGE` or `DATA_FIX`) and resubmit" | `doc_status = in_progress → draft`; เหตุผล rejection ใน `workflow_history` Store Keeper เห็น rejection; แก้ไข reason code หรือ cancel ไม่มีผลกระทบ inventory |
| IC-HP-04 | Commit count-variance — auto-rollup | [[physical-count]] เสร็จที่ `LOC-A`; บรรทัดผลต่าง: `P-1 เกิน 2 (cost ฿20)`, `P-2 ขาด 1 (cost ฿15)`, `P-3 ขาด 0.5 (cost ฿8.50)` | 1. เปิดเอกสารนับที่เสร็จ 2. Review บรรทัดผลต่าง; ยืนยันจริง (ไม่ใช่ข้อผิดพลาดการนับ) 3. คลิก **Commit Variances** | ตาม `ADJ_POST_006`: (a) หนึ่ง `tb_stock_in` ด้วยเหตุผล `COUNT_OVERAGE`, หนึ่งบรรทัดสำหรับ `P-1 qty=2`; (b) หนึ่ง `tb_stock_out` ด้วยเหตุผล `COUNT_SHORTAGE`, สองบรรทัดสำหรับ `P-2 qty=1`, `P-3 qty=0.5` ทั้งสอง auto-advance ไปยัง `completed` ภายใต้อำนาจ Controller `info.countId = <count_uuid>` `tb_count_stock.status = completed_posted` Map ไปยัง parent Scenario 5 |
| IC-HP-05 | Forward เอกสารเหนือ Controller-threshold ไปยัง Finance | `tb_stock_out` ที่ Store-Keeper submit ที่ `in_progress`; reason `RECALL_WRITE_OFF`; total `฿85,000` (เหนือ Controller threshold) | 1. เปิดเอกสาร 2. ตรวจสอบบริบท recall (recall notice แนบ) 3. ตรวจสอบว่า lots อยู่ใน recall notice 4. คลิก **Forward to Finance** ด้วย comment "Controller-verified; ready for Finance approval" | `workflow_current_stage` advance ไปยัง "finance-review"; เอกสารคงอยู่ `in_progress`; ปรากฏใน queue Finance Approvals ตาม [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) FN-HP-* Map ไปยัง parent Scenario 3 |
| IC-HP-06 | Void เอกสารที่ post ผ่าน compensating reversal | `tb_stock_in` ที่ `completed` ที่ `LOC-A` สำหรับ `P-1` qty 10, ระบุว่าเป็น duplicate-post (found stock เดียวกันรายงานสองครั้งโดยสอง SKs) | 1. เปิด `tb_stock_in` duplicate 2. คลิก **Void** → "Create compensating reversal" 3. Form pre-fill `tb_stock_out` ด้วยบรรทัดเดียวกัน, reason `DATA_FIX`, `info.voidsAdjustmentId = <original_stock_in.id>` 4. Submit (อำนาจ Controller — auto-approve ไม่ว่า threshold ภายใต้ void-compensation) 5. หลังการ post ชดเชย: ต้นฉบับ `tb_stock_in.doc_status = voided` | Compensating `tb_stock_out.doc_status = completed` ด้วย `info.voidsAdjustmentId` ผลกระทบ inventory: on-hand ที่ `(LOC-A, P-1, LOT-1)` ลด 10 (reverse duplicate ต้นฉบับ) ต้นฉบับ `tb_stock_in.doc_status = voided`; inventory transaction ต้นฉบับ NOT edit ตาม [[inventory]] `INV_POST_012` Map ไปยัง parent Scenario 13 |
| IC-HP-07 | Direct create — Controller สร้าง stock-out สำหรับ write-off ต่ำกว่า SoD threshold สำหรับ SK | SoD block Store Keeper จากการสร้าง write-off ต่อ lot ที่พวกเขารับเอง (parent Scenario 14) Controller สร้างโดยตรงภายใน scope Controller | 1. Controller เปิด New Stock-Out 2. Reason `EXPIRY_WRITE_OFF` 3. Lines ตามความต้องการต้นฉบับ 4. Submit | เอกสารที่ Controller สร้างโดยตรงดำเนินตาม flow มาตรฐาน; ต่ำกว่า Controller threshold auto-approve (Controller อยู่เหนือ SK auto-approve และต่ำกว่า Finance threshold); เหนือ Controller threshold forward ไปยัง Finance `doc_status = completed`; ผลกระทบ inventory apply |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| IC-PERM-01 | Approve / reject เอกสาร `in_progress` ภายในแบนด์ Controller threshold | **Allow ตาม `ADJ_AUTH_004`** ต่ำกว่า auto-approve threshold: Controller ไม่เห็น (auto-approved) เหนือ Controller threshold: Controller forward ไปยัง Finance แทนการอนุมัติ |
| IC-PERM-02 | Controller อนุมัติเอกสารเหนือ Controller threshold โดยตรง | **Deny — Finance required** ตาม `ADJ_AUTH_005`, เหนือ Controller-threshold ต้องการ Finance API call return `"Approval above the Controller threshold requires the Finance role; please forward to Finance instead."` เอกสารคงอยู่ `in_progress` |
| IC-PERM-03 | Controller อนุมัติ new-lot stock-in ไม่ว่าต้นทุน | **Allow ตาม `ADJ_AUTH_003`** Controller เป็น gate ที่ระบุชัดเจนสำหรับ new-lot stock-in; below-threshold auto-approve ไม่ใช้ |
| IC-PERM-04 | Controller commit count variances | **Allow ตาม `ADJ_POST_006` / `ADJ_XMOD_002`** จุดชนวน auto-rollup `tb_stock_in` / `tb_stock_out` ที่ `completed` ภายใต้ลายเซ็น Controller |
| IC-PERM-05 | Controller void เอกสาร `completed` | **Allow ตาม `ADJ_AUTH_007` / `ADJ_POST_004`** สองขั้น: สร้าง compensating reversal ก่อน; ต้นฉบับเคลื่อนไปยัง `voided` หลังการ post ชดเชย |
| IC-PERM-06 | Controller cancel เอกสาร `in_progress` | **Allow ตาม `ADJ_AUTH_007`** `doc_status = cancelled` ด้วยเหตุผล; ปลายทาง; ไม่มีผลกระทบ inventory |
| IC-PERM-07 | Controller พยายามกำหนดค่า `tb_adjustment_type` | **Deny — Sysadmin required** ตาม `ADJ_AUTH_008`, master-data CRUD เป็น scope Sysadmin Controller ขอการเปลี่ยนการกำหนดค่าผ่านกระบวนการภายในแต่ไม่ execute |
| IC-PERM-08 | Controller พยายามแก้ไขเอกสาร `completed` โดยตรง | **Deny ตาม `ADJ_VAL_013`** ต้องใช้รูปแบบ void + compensating reversal |
| IC-PERM-09 | Department Manager (persona พับ) พยายามอนุมัติเอกสาร | **Deny — read-only** ความรับผิดชอบ review ของ Department-Manager ภายใน persona group นี้คือ **การกำกับ read-only**; การอนุมัติต้องการบทบาท Controller โดยเฉพาะ การแจ้งเตือนและ comment / flag-for-escalation อนุญาต; การอนุมัติไม่ |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| IC-VAL-01 | Approve fail บน stale on-hand check (`ADJ_VAL_012`) | ที่เวลาอนุมัติ Controller, posting อื่นบริโภคจาก lot ตั้งแต่ SK submit, เหลือ on-hand ไม่เพียงพอ | Approval reject ด้วย live recheck ตาม [[inventory]] `INV_VAL_005` ("Outbound movement would drive on-hand at (..., lot) below zero. Available: <X>, requested: <Y>.") เอกสาร return ไปยัง `draft` ด้วย system note; SK re-pick lot หรือลด qty |
| IC-VAL-02 | Approve fail บน closed period (`ADJ_VAL_011`) | งวดที่มี `si_date` / `so_date` ปิดระหว่าง SK submit และ Controller approval | Approval reject ด้วย `"Cannot post into period <YYMM>: period is closed."` ตาม [[inventory]] `INV_VAL_008` Controller ขอ Finance Manager re-open หรือประสาน current-period restatement |
| IC-VAL-03 | Approve fail เมื่อ reason ไม่ตรงทิศทางอีกต่อไป (`ADJ_VAL_002`) | Sysadmin deactivate / soft-delete reason ระหว่าง SK submit และ Controller approval | Approval reject ด้วย `"Adjustment reason is no longer valid; please pick an active reason matching the document direction."` เอกสาร return ไปยัง `draft` |
| IC-VAL-04 | Approve fail เมื่อ location กลายเป็น inactive (`ADJ_VAL_003`) | Sysadmin deactivate location ระหว่าง SK submit และ Controller approval (หายาก) | Approval reject ด้วย `"Cannot post to an inactive or soft-deleted location."` เอกสาร return ไปยัง `draft` |
| IC-VAL-05 | Commit count variance fail เมื่อเอกสาร count ไม่ที่ `completed` | พยายาม commit variances บน count ยังอยู่ที่ `in_progress` | Reject ด้วย `"Count must be at completed status before variances can be committed."` (Validation ใน [[physical-count]] / [[spot-check]] module, called จาก adjustment commit path) |
| IC-VAL-06 | Void โดยไม่มี compensating reversal (`ADJ_VAL_014`) | การ call API โดยตรง set `tb_stock_in.doc_status = voided` โดยไม่สร้าง compensating reversal | Reject ด้วย `"Cannot soft-delete or directly void a posted adjustment without a compensating reversal."` ตาม [[inventory]] `INV_VAL_013` |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | --------- | -------- |
| IC-EDGE-01 | ขอบ threshold ที่ขอบบน (Controller → Finance) | ต้นทุนเอกสาร `฿10,000` พอดี (Controller threshold) | **ขอบ inclusive — Controller สามารถอนุมัติ** `฿10,000.01` เกินและต้องการ Finance |
| IC-EDGE-02 | Count-rollup ด้วยผลผสม (overage AND shortage บน product เดียวกันข้าม lots) | Count: `P-1 LOT-1 ขาด 1`; `P-1 LOT-2 เกิน 2` | **สองเอกสาร rollup, ไม่ net** Auto-rollup สร้างหนึ่ง `tb_stock_in` (`LOT-2` overage qty 2) และหนึ่ง `tb_stock_out` (`LOT-1` shortage qty 1); ไม่ใช่ `tb_stock_in` qty 1 ที่ net เดียว Preserve audit trail ต่อ lot ทั้งสอง auto-advance ไปยัง `completed` |
| IC-EDGE-03 | การ flag สืบสวน variance ขนาดใหญ่ | บรรทัด count-variance เหนือ `ADJ_CALC_008` variance threshold (เช่น > 10% net cost impact) | Controller อาจ **reject the count** (ขอ recount) ก่อน commit, ป้องกัน auto-rollup จากการ post หรือ commit ด้วย comment flag สำหรับการสืบสวน Finance; rollup ยัง auto-post แต่เอกสารถือ flag |
| IC-EDGE-04 | ความพยายามอนุมัติพร้อมกัน (สอง Controllers) | สอง Controllers เปิดเอกสาร `in_progress` เดียวกันพร้อมกัน; ทั้งคู่คลิก Approve | First commit ชนะ; ที่สองเห็น `"Document already approved — refresh"` (optimistic-concurrency บน `doc_version` ตาม `tb_stock_in.doc_version` / `tb_stock_out.doc_version`) ไม่มี double-post |
| IC-EDGE-05 | Forwarding ไปยัง Finance ผ่าน API โดยตรง bypass UI | API call ขยับ `workflow_current_stage` ไปยัง "finance-review" โดยไม่มี comment | **Reject** — Forward action ต้องการ comment ตามกฎ workflow (นิยาม `tb_workflow`) Return `"Forward action requires a comment."` |
| IC-EDGE-06 | New-lot approval ด้วย cost outlier | SK-submitted new-lot stock-in `cost_per_unit = ฿100.00` สำหรับ product ที่ `[[vendor-pricelist]]` last-price `฿10.00` | Controller เห็น 10× outlier flag; **คาดหวัง** reject ระหว่างรอ defensibility (vendor-RMA reference, invoice ที่แนบ) ถ้าอนุมัติโดยไม่มีการพิสูจน์ audit-trail flag จุดชนวน Auditor review ตาม `ADJ_AUTH_009` |
| IC-EDGE-07 | Compensating-reversal ของ compensating-reversal | หลัง void ผ่าน compensating reversal, ระบุว่า void ต้นฉบับผิดและ re-void compensating | อนุญาต — เอกสาร compensating เป็น `tb_stock_in` / `tb_stock_out` ปกติและสามารถ void เองตาม `ADJ_POST_004` Void chain ลึกสองชั้น (original → comp → comp-of-comp); Auditor inspect ตาม `ADJ_AUTH_009` ผลกระทบ on-hand net ไปยังสถานะต้นฉบับ |
| IC-EDGE-08 | Department Manager flag-for-escalation | DM (read-only sub-persona) flag adjustment ที่ post เป็น anomalous ผ่าน comment | Comment บันทึกบน `tb_stock_in_comment` / `tb_stock_out_comment`; การแจ้งเตือน fire ไปยัง Finance และ Auditor ไม่มีการเปลี่ยนสถานะ; Finance / Auditor follow-up |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — handoff scenarios ที่ Controller เป็น protagonist: 2 (อนุมัติ stock-out เหนือ threshold), 3 (forward ไปยัง Finance), 4 (อนุมัติ new-lot), 5 (commit count variance), 6 (commit spot-check variance), 7 (FIFO ขาออก, อนุมัติ Controller), 13 (void ผ่าน compensating reversal), 18 (period-end variance hold)
- User flow: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md) — primary 9 ขั้น approval flow, count-rollup commit flow, direct-create flow, decision branches, exit handoffs
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) — `ADJ_AUTH_003` (new-lot gate), `ADJ_AUTH_004` (อนุมัติ Controller), `ADJ_AUTH_007` (cancel / void), `ADJ_POST_002` (post fan-out), `ADJ_POST_004` (void ผ่าน compensating), `ADJ_POST_006` (count-rollup), `ADJ_CALC_008` (variance %), validations re-check ที่ approval (`ADJ_VAL_002`, `ADJ_VAL_003`, `ADJ_VAL_009`, `ADJ_VAL_011`, `ADJ_VAL_012`)
- E2E specs: [`../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) — รูปแบบการอนุมัติขาออกแชร์กับ stock-out adjustment; [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — รูปแบบ variance-hold และ approval-gate ปลายงวด ผู้ใช้ Controller-fixture `inventory@blueledgers.com` (ทั่วไป multi-role)
- Cross-link: [[inventory]] — `INV_AUTH_003` (Controller เป็น second signature ในลำดับชั้น inventory), `INV_POST_001` / `INV_POST_002` (post effects), `INV_VAL_005` / `INV_VAL_008` (กฎ re-check)
- Cross-link: [[physical-count]] / [[spot-check]] — count variance commit จุดชนวน adjustment auto-rollup
- Cross-link: [[good-receive-note]] — Controller อาจ inspect GRN ต้นทางเมื่อ review recall write-off หรือ vendor-replacement
- Cross-link: [[vendor-pricelist]] — reference cost-outlier สำหรับ defensibility ของ new-lot stock-in
