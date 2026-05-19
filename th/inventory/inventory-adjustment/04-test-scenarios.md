---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios
description: Test cases ตาม persona, scenarios ข้าม persona และการ map E2E สำหรับการปรับสต๊อก
published: true
date: 2026-05-20T00:00:00.000Z
tags: inventory-adjustment, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios

> **At a Glance**
> **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; **Scenarios รวม:** ~22 ข้าม persona + ~130 ต่อ persona &nbsp;·&nbsp; **Personas ที่ครอบคลุม:** Store Keeper, Inventory Controller, Finance, Audit / Config
> **ลำดับการรัน:** Audit / Config setup → happy paths persona หลัก → scenarios ข้าม persona
> **เจาะลึกต่อ persona ใน `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้คือ **จุดเข้าภาพรวม** สำหรับชุด test-scenarios ของโมดูล `inventory-adjustment` Group การครอบคลุมตาม 4 persona groups ที่โต้ตอบกับวงจรชีวิตเอกสาร adjustment (Store Keeper, Inventory Controller, Finance, Audit / Config), inventory ไฟล์เทสต่อ persona, capture handoff scenarios ข้าม persona ที่ stitch เส้นทางส่วนตัวเข้าด้วยกัน และ map ทุก scenario ข้าม persona กลับไปยัง Playwright spec [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) (surface E2E admin adjustment-type / reason-code canonical) บวก specs ที่อยู่ติดกับ adjustment (`720-stock-issue.spec.ts` สำหรับ paths stock-out, `900-period-end.spec.ts` สำหรับ orchestration period-end, `501-grn.spec.ts` สำหรับฝั่ง cost-layer ของการ post การรับที่ adjustments สะท้อน)

Scope กว้างโดยตั้งใจ: แต่ละไฟล์ persona รวม **happy paths เชิงฟังก์ชัน** (auto-approve stock-in / stock-out, การอนุมัติ Controller เหนือ threshold, count-rollup commit, การอนุมัติ Finance, void ผ่าน compensating reversal), **กรณี RBAC / permission-denial** (Store Keeper พยายามอนุมัติ Controller, Controller พยายามอนุมัติ Finance, Sysadmin พยายามสร้าง adjustment), **validation** (เทสลบต่อ `ADJ_VAL_001`–`ADJ_VAL_014` ที่เวลา submit และ edit), **edge cases** (ขอบ threshold, ความแม่นยำทศนิยม, posts พร้อมกัน, lot identity collision, period rollover ระหว่าง draft, new-lot zero-cost, FIFO override สำหรับ expiry write-off) และ **กรณีการกำหนดค่า / audit-trail** (CRUD reason-code, การเปลี่ยน threshold, SoD compliance, lot-recall trace, การตรวจสอบ void-chain)

Scenarios ข้าม persona ใน Section 4 บรรยายเส้นทาง end-to-end ที่ข้ามขอบเขต handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) Section 4 — เช่น *Store Keeper สร้าง stock-in → auto-approve ต่ำกว่า threshold → post ไปยัง inventory*; *Store Keeper สร้าง stock-out เหนือ threshold → Controller อนุมัติ → post*; *Controller commit count variance → auto-rollup สร้างและ post stock-in / stock-out*; *Finance อนุมัติ recall write-off เหนือ Controller-threshold → post*; *Finance review กิจกรรม adjustment ปลายงวด → Finance Manager ปิดงวด* Section 5 map E2E specs ที่เกี่ยวข้องกับ adjustment กลับไปยังเส้นทางเหล่านั้นเพื่อให้ช่องโหว่ในการครอบคลุม automated มองเห็นได้; note ว่า **flow การสร้าง / posting เอกสาร** ครอบคลุมบางส่วน (stock-issue spec ครอบคลุม path stock-out; period-end spec ครอบคลุม review ปลายงวด; adjustment-type spec ครอบคลุม CRUD reason-code ของ Sysadmin) — ข้อกังวลเอกสารฝั่ง adjustment หลายอย่าง validate ผ่าน specs โมดูลต้นน้ำ (count, GRN credit-note) ด้วยไฟล์เทสต่อ persona ที่บันทึก scenarios ที่อาจ manual / planned

## 2. Personas ที่อยู่ใน Scope

- **Store Keeper**: ผู้ปฏิบัติงานระดับพื้นที่ที่ริเริ่ม `tb_stock_in` / `tb_stock_out` สำหรับ adjustments ที่ไม่ใช่ routine GRN / non-SR, แนบหลักฐาน, บันทึก reason, submit สำหรับ auto-approve (ต่ำกว่า threshold) หรือ route ไปยัง Controller (เหนือ threshold หรือ new-lot)
- **Inventory Controller**: อนุมัติ adjustments เหนือ threshold และ new-lot, ติดตามรูปแบบผลต่าง, commit count-variance rollups (ที่ auto-post stock-in / stock-out), forward เอกสารเหนือ Controller-threshold ไปยัง Finance ความรับผิดชอบ review ของ Department Manager พับเข้า
- **Finance**: อนุมัติ adjustments เหนือ Controller-threshold (recall / damage / theft write-offs ขนาดใหญ่), ตรวจสอบ GL-account mapping ต่อ reason code, reconcile inventory sub-ledger กับ GL ที่ปิดงวด, sign-off กิจกรรม adjustment ปลายงวด
- **Audit / Config**: System Administrator ที่กำหนดค่า `tb_adjustment_type` reason codes (รวม `info.glAccount`), tenant thresholds, RBAC, นิยาม workflow; Auditor ที่รัน read-only audit-log queries, การตรวจสอบ SoD compliance, lot-recall traces, การตรวจสอบ void-chain

## 3. ไฟล์เทส Persona

- [Scenarios Store Keeper](./04-test-scenarios-store-keeper.md)
- [Scenarios Inventory Controller](./04-test-scenarios-inventory-controller.md)
- [Scenarios Finance](./04-test-scenarios-finance.md)
- [Scenarios Audit / Config](./04-test-scenarios-audit-config.md)

## 4. Scenarios ข้าม Persona / Handoff

ตารางด้านล่างคือเลเยอร์ integration แต่ละแถว span อย่างน้อยหนึ่ง handoff จาก [03-user-flow.md](./03-user-flow.md) Section 4 และจบด้วยระบบในสถานะปลายทางหรือคงที่ "Personas in order" list actors ในลำดับการ execute; "Pre-condition" capture สถานะระบบที่ต้องการเพื่อเริ่ม; "Expected end state" anchor `doc_status` ของเอกสาร, ผลกระทบ inventory transaction (`tb_inventory_transaction` เขียน, cost-layer rows, GL entry) และผลข้างเคียงข้ามโมดูลใด ๆ

| # | Scenario | Personas ในลำดับ | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Routine stock-in ต่ำกว่า threshold — auto-approve | Store Keeper | Lot ที่มีอยู่ที่ location; total cost < auto-approve threshold; period `open`; reason `FOUND_STOCK` | `tb_stock_in.doc_status = completed`; หนึ่ง `tb_inventory_transaction` (`inventory_doc_type = stock_in`, `enum_transaction_type = adjustment_in`); แถว cost-layer ขาเข้า (`in_qty > 0`); on-hand advance ที่ `(location, product, lot)`; ไม่มี handoff Controller |
| 2 | Stock-out เหนือ threshold สำหรับ breakage — Controller อนุมัติ | Store Keeper → Inventory Controller | Reason `BREAKAGE`; ต้นทุนเหนือ auto-approve threshold แต่ต่ำกว่า Controller threshold; period `open` | หลังการอนุมัติ Controller: `tb_stock_out.doc_status = completed`; `tb_inventory_transaction` ขาออก (`enum_transaction_type = adjustment_out`); cost-layer ขาออก (FIFO หรือ WA ตาม product); on-hand ลด; `workflow_history` บันทึกการอนุมัติ Controller |
| 3 | Recall write-off เหนือ Controller-threshold — Finance อนุมัติ | Store Keeper → Inventory Controller → Finance | Reason `RECALL_WRITE_OFF`; ต้นทุนเหนือ Controller threshold; period `open`; recall notice แนบ | หลังการอนุมัติ Finance: `tb_stock_out.doc_status = completed`; inventory transaction ขาออก; cost-layer rows (FIFO multi-row ถ้า span lots); GL `Dr Product Recall Loss / Cr Inventory` ที่ `info.glAccount` ที่ resolve |
| 4 | New-lot stock-in (ต่ำกว่า threshold) — route ไปยัง Controller | Store Keeper → Inventory Controller | Reason `FOUND_STOCK` หรือ `VENDOR_FREE_REPLACEMENT`; lot ใหม่ (ไม่มีแถว cost-layer ก่อนหน้าที่ `(product, location, lot_no)`); cost ผู้ใช้กรอก; total ต่ำกว่า auto-approve threshold | ตาม `ADJ_AUTH_003`, new-lot route สำหรับ Controller approval ไม่ว่าต้นทุน หลังการอนุมัติ Controller: `tb_stock_in.doc_status = completed`; lot ใหม่สร้างใน cost-layer (`in_qty > 0`, `lot_no` ใหม่, `lot_seq_no` ใหม่ = max+1); on-hand ที่ `(location, product, lot)` initialise เป็น qty ของบรรทัด |
| 5 | Physical count variance commit — auto-rollup post | Inventory Controller | [physical-count](/th/inventory/physical-count) เสร็จด้วยบรรทัดผลต่าง (บาง overage, บาง shortage); Controller commit | สองเอกสาร rollup สร้างและ auto-post: หนึ่ง `tb_stock_in` (บรรทัด overage, reason `COUNT_OVERAGE`); หนึ่ง `tb_stock_out` (บรรทัด shortage, reason `COUNT_SHORTAGE`) ทั้งสอง `doc_status = completed`; `info.countId = <count_uuid>` `tb_count_stock.status = completed_posted` ตาม `ADJ_POST_006` / `ADJ_XMOD_002` |
| 6 | Spot-check variance commit — auto-rollup post | Inventory Controller | [spot-check](/th/inventory/spot-check) เสร็จด้วยบรรทัดผลต่างบน subset; Controller commit | เหมือนกับ Scenario 5 แต่ scope ไปยัง subset ที่ spot-check; เอกสาร rollup อ้างอิง spot-check ผ่าน `info.spotCheckId` ตาม `ADJ_XMOD_003` |
| 7 | FIFO ขาออก span สอง lots | Store Keeper → Inventory Controller | Product ที่ `costing_method = FIFO`; สอง lots ที่ source location ด้วย `lot_seq_no` และ `cost_per_unit` ต่างกัน; stock-out qty ใหญ่กว่ายอดของ lot เก่าที่สุด; ต้นทุนเหนือ auto-approve | `tb_inventory_transaction` ขาออกเดียว; **สอง** แถว cost-layer ขาออก — หนึ่งบริโภค lot เก่าที่สุดเต็มที่ `cost_per_unit` ของมัน, หนึ่งบริโภคที่เหลือจาก next-oldest ที่ `cost_per_unit` ของมัน ตาม `ADJ_CALC_006` / [inventory](/th/inventory/inventory) `INV_CALC_005` |
| 8 | Weighted-average ขาเข้า recompute บน stock-in | Store Keeper | Product ที่ `costing_method = WEIGHTED_AVERAGE`; on-hand ที่มีอยู่ที่ต้นทุนหนึ่ง; stock-in สำหรับ lot ที่มีอยู่ที่ต้นทุนต่างกัน; ต่ำกว่า auto-approve | แถว cost-layer ขาเข้าถือต้นทุนใหม่และ `average_cost_per_unit = (prior_on_hand × prior_average + adj_qty × adj_cost) / (prior_on_hand + adj_qty)` ที่ recompute ตาม `ADJ_CALC_005` ขาออกต่อไปที่ location อ่าน average ใหม่ |
| 9 | ความพยายามยอดติดลบบน stock-out — reject | Store Keeper | Outbound stock-out สำหรับ qty ใหญ่กว่า on-hand ปัจจุบันที่ lot ที่เลือก; tenant policy "ไม่มียอดติดลบ" (default) | Submit reject ก่อน post ตาม `ADJ_VAL_012` / [inventory](/th/inventory/inventory) `INV_VAL_005` ด้วย `"Outbound movement would drive on-hand below zero. Available: X, requested: Y."` เอกสารคงอยู่ `draft` |
| 10 | Post ย้อนหลังเข้างวด closed — reject | Store Keeper / Controller / Finance | เอกสารด้วย `si_date` / `so_date` ภายในงวด `closed` `tb_period` | Submit / approve reject ตาม `ADJ_VAL_011` ด้วย `"Cannot post into period <YYMM>: period is closed."` เอกสารคงอยู่ `draft` Finance Manager re-open path เป็นไปได้ตาม [inventory](/th/inventory/inventory) `INV_AUTH_006` |
| 11 | Adjustment ที่ direct-cost location — reject | Store Keeper | Stock-in หรือ stock-out สร้างต่อ location ที่ `tb_location.location_type = direct` | Reject ที่ submit ตาม `ADJ_VAL_003` / `ADJ_POST_007` ด้วย `"Direct-cost locations cannot be the target of an adjustment."` Picker location filter direct-type ออกบน UI; การ submit API โดยตรง re-check |
| 12 | Stock-in ที่ consignment location — memo-only | Store Keeper | Stock-in ไปยัง `location_type = consignment` (เช่น พบสต๊อกที่ vendor เป็นเจ้าของระหว่างการนับ); ต่ำกว่า auto-approve | `tb_stock_in.doc_status = completed`; `tb_inventory_transaction` เขียน; แถว cost-layer ที่ flag consignment; **ไม่มี Inventory asset debit, ไม่มี AP credit ที่ receipt** ตาม `ADJ_POST_008` / [inventory](/th/inventory/inventory) `INV_POST_004` Per-consumption COGS + AP fire ภายหลังตาม `INV_POST_005` |
| 13 | Void เอกสารที่ post ผ่าน compensating reversal | Inventory Controller / Finance | `tb_stock_in` ที่ `doc_status = completed`; ระบุว่าผิด (เช่น ค้นพบ duplicate-post, ข้อผิดพลาด cost-mapping) | สองขั้น: (a) compensating `tb_stock_out` สร้างด้วย `info.voidsAdjustmentId = <original>`, บรรทัดเดียวกัน reverse; submit และ post ตาม `ADJ_POST_002` (b) ต้นฉบับ `tb_stock_in.doc_status = voided` ตาม `ADJ_POST_004` / [inventory](/th/inventory/inventory) `INV_POST_012` |
| 14 | การละเมิด SoD — Store Keeper write off receipt ของตัวเองเหนือ threshold | Store Keeper | Store Keeper สร้าง `tb_stock_out` ต่อ lot ที่พวกเขารับเองผ่าน GRN; ต้นทุนเหนือ SoD threshold ตาม `ADJ_AUTH_010` | Submit reject ด้วย `"You created the receipt for this lot; an independent adjuster must initiate the write-off (SoD)."` เอกสารคงอยู่ `draft`; SK escalate ไปยัง Controller หรือ SK คนละคนสร้าง |
| 15 | Reason-code direction mismatch — reject | Store Keeper | Reason `BREAKAGE` (`type = stock_out`) ที่เลือกบนเอกสาร `tb_stock_in` — โดยทั่วไป race UI หรือการใช้ API ผิด | Reject ที่ submit ตาม `ADJ_VAL_002` ด้วย `"Adjustment reason is required and must match the document direction."` Picker filter reasons ตามทิศทางบน UI |
| 16 | Attachment ที่ต้องการขาด — reject | Store Keeper | Reason flag `info.requiresDocument = true` (เช่น `THEFT_WRITE_OFF`) แต่ไม่มี attachment upload | Reject ที่ submit ตาม `ADJ_VAL_010` ด้วย `"Supporting document attachment is required for this adjustment reason."` SK เพิ่ม attachment; resubmit |
| 17 | Requires-quality-check bypass auto-approve | Store Keeper → Inventory Controller | Reason flag `info.requiresQualityCheck = true` (เช่น `EXPIRY_WRITE_OFF`); total cost ต่ำกว่า auto-approve threshold | เอกสาร **route ไปยัง Controller** แม้ต่ำกว่า threshold (auto-approve fast path ถูก bypass ตาม [03-user-flow.md](./03-user-flow.md) Section 2.2) Controller อนุมัติ; เอกสาร `doc_status = completed` |
| 18 | Review ปลายงวด: hold ที่ variance-flagged | Inventory Controller → Finance | งวดมี count-variance items ที่เปิดที่ flag "investigate"; Controller ยังไม่ sign-off variance | การ approve ปลายงวด Finance **block** — Controller ยังไม่ sign-off variance Finance communicate hold; Controller resolve การสืบสวน; sign-off; Finance re-run period-end approve และ Finance Manager ปิดตาม [inventory](/th/inventory/inventory) `INV_AUTH_006` |
| 19 | Sysadmin เพิ่ม reason code ใหม่ด้วย GL-account mapping | System Administrator | Business case ใหม่ (เช่น insurance-claimable losses) ต้องการ reason code ใหม่ | แถว `tb_adjustment_type` สร้างด้วย `code = INSURANCE_WRITE_OFF`, `type = stock_out`, `info.glAccount = "6535"`, `info.requiresDocument = true` พร้อมใช้ทันทีใน picker Store Keeper / Controller / Finance Audit-log ตาม `ADJ_AUTH_008` Exercise โดย [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) |
| 20 | Auditor ตรวจสอบ SoD compliance สำหรับงวด | Auditor | `tb_stock_out` posts ทั้งหมดในงวดพร้อมใช้; SoD threshold configure | Audit query join `tb_stock_out.created_by_id` ต่อ `tb_good_received_note.created_by_id` สำหรับ lot เดียวกันเหนือ SoD threshold รายการ findings flag คู่ (ผู้รับ / adjuster) Cross-reference `ADJ_AUTH_010` / [inventory](/th/inventory/inventory) `INV_AUTH_010` |
| 21 | Auditor lot-recall trace | Auditor | Lot ได้รับผลกระทบจาก vendor recall; introduce โดย GRN, ส่วนหนึ่ง issue ผ่าน SR, ส่วนหนึ่ง write off ผ่าน stock-out, ด้วย credit-note amount adjustment | Backward trace return GRN ต้นทาง Forward trace return การเคลื่อนไหวที่บริโภคทั้งหมด (SR issues, stock-out write-offs, แถวปริมาณ credit-note, transfer-outs) รายงาน chain-of-custody render ทั้งสองทิศทาง Read-only; ไม่มีการเปลี่ยนสถานะ |
| 22 | Auditor ตรวจสอบ void chains | Auditor | งวดมีเอกสาร adjustment ที่ `voided` | สำหรับแต่ละเอกสาร `voided` ตรวจสอบว่า compensating `tb_stock_in` หรือ `tb_stock_out` มีอยู่ด้วย `info.voidsAdjustmentId = <original_id>` ตาม `ADJ_POST_004` Orphaned voids (ไม่มี compensating reversal) flag |

## 5. การ Map E2E Test

โมดูล inventory-adjustment **exercise บางส่วน** โดยสาม Playwright spec files; ไม่มี `inventory-adjustment.spec.ts` ที่ครอบคลุมวงจรชีวิตเอกสารเต็ม การครอบคลุมกระจายข้าม specs admin reason-code, stock-issue (ขาออก) และ period-end

| Spec / describe block | Scenarios ข้าม persona ที่ครอบคลุม (Section 4) |
| --------------------- | ------------------------------------------- |
| [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) | 19 (CRUD reason-code Sysadmin); ยัง exercise `ADJ_VAL_001`-equivalent บน uniqueness `tb_adjustment_type.code` และ scope Sysadmin `ADJ_AUTH_008` |
| [`720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) | 2 (stock-out เหนือ threshold — ใช้ stock-issue surface ที่สะท้อน path posting ของ stock-out), 7 (FIFO ขาออก span lots), 9 (negative-balance rejection), 14 (SoD ผ่าน issue path) |
| [`900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) | 10 (backdated-post rejection — ฝั่ง period-status), 18 (period-end variance-flagged hold) |
| [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Stock Movements describe block | 8 (รูปแบบ WA inbound recompute — logic recompute แชร์ระหว่าง GRN inbound และ stock-in inbound), 11 (direct-cost location — ฝั่ง receipt), 12 (consignment location — ฝั่ง receipt) |
| [`601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) | 13 (รูปแบบ compensating-reversal — โมดูล credit-note ใช้ flow void-via-reversal ที่คล้าย) |

ช่องโหว่สัมพันธ์กับ Section 4:

- Scenarios 1, 4 (Store Keeper auto-approve และ new-lot stock-in) ไม่ครอบคลุมโดย stock-in spec เฉพาะ; flow transactional ของโมดูล stock-in เป็น surface เทส **manual / planned** การครอบคลุม automated ที่ใกล้ที่สุดอยู่ที่ Stock Movements describe block ของ GRN spec (ที่ครอบคลุมรูปแบบการเขียน `tb_inventory_transaction` เดียวกัน)
- Scenarios 3 (Finance approval) และ 17 (requires-quality-check bypass) ต้องการ Finance approval surface; การครอบคลุม automated ที่ใกล้ที่สุดอยู่ที่ approval gate ของ period-end spec
- Scenarios 5, 6 (count-rollup auto-post) อยู่ใน specs โมดูล count (ยังไม่ลิงก์ที่นี่); การสร้าง rollup ฝั่ง adjustment เป็นเทส **manual / planned** ที่รอ E2E ของโมดูล count
- Scenarios 20, 21, 22 (Auditor SoD / lot-recall / void chains) เป็นรูปแบบ audit-query read-only; โดยทั่วไป **manual / planned** จนกว่า audit module spec จะลง

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — spec CRUD admin adjustment-type / reason-code; surface Sysadmin canonical
- [`../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/720-stock-issue.spec.ts) — path stock-out / stock-issue; surface inventory ขาออกที่ stock-out adjustment แชร์
- [`../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts) — orchestration period-end; cross-link สำหรับ scenarios backdated-post และ variance-hold
- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — ฝั่ง inventory ของ GRN commit; cross-link สำหรับรูปแบบ posting ขาเข้า (WA / FIFO) ที่ stock-in adjustment สะท้อน
- [`../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/601-cn.spec.ts) — ผลกระทบ inventory ของ credit-note; cross-link สำหรับรูปแบบ compensating-reversal ที่ adjustment void ใช้
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — handoffs ข้าม persona ที่ขับเคลื่อน integration scenarios ด้านบน
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation (Section 2), calculation (Section 3), authorization (Section 4), posting (Section 5) และ cross-module (Section 6) ที่ถูกเรียกโดยทุก scenario ด้านบน
- รายละเอียดต่อ persona: [Store Keeper](./04-test-scenarios-store-keeper.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md)
