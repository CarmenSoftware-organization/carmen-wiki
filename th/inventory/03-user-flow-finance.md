---
title: คลังสินค้า (Inventory) — User Flow — Finance
description: Flow ของ Finance ในโมดูล inventory — การตรวจสอบการตีมูลค่า การกระทบยอด inventory-to-GL การปิดและล็อกงวด
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Finance

> **At a Glance**
> **Persona:** Finance (Officer / Accountant + Manager / Controller) &nbsp;·&nbsp; **โมดูล:** [[inventory]] &nbsp;·&nbsp; **ขั้นตอน workflow:** อนุมัติ adjustment ผลกระทบต้นทุนเหนือ threshold ของ Controller &nbsp;·&nbsp; sub-ledger ↔ GL reconciliation &nbsp;·&nbsp; run ปิดงวด (close + open next) &nbsp;·&nbsp; period-lock (`closed → locked`) &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อนุมัติเหนือ threshold ของ Controller (`INV_AUTH_005`); advance `tb_period.status` (`INV_AUTH_006`); fire `INV_POST_009 / INV_POST_010 / INV_POST_011`
> **สิ่งที่ persona นี้ทำ:** เป็นเจ้าของการตีมูลค่าและ GL reconciliation; เซ็นรับรอง run ปิดงวดและ advance `tb_period.status` ไปยัง lock

## 1. บทบาทในโมดูลนี้

Persona **Finance** ครอบคลุม **Finance Officer / Inventory Accountant** ที่โต๊ะ reconciliation ประจำวันบวก **Finance Manager / Controller** ที่ขอบเขตการปิดและล็อกงวด Finance คือ **สิทธิ์การตีมูลค่า** บนโมดูล inventory — role ที่เป็นเจ้าของสะพานระหว่าง sub-ledger สต๊อกจริง (`tb_inventory_transaction_cost_layer`) และบัญชีควบคุม GL Inventory และ role ที่เซ็นรับรอง run ปิดงวดที่ล็อก sub-ledger ไปยัง snapshot ภายในโมดูล inventory งานของ Finance ครอบคลุมสี่สาย: (1) **อนุมัติ adjustment ผลกระทบต้นทุนเหนือ threshold ของ Inventory Controller** ตาม `INV_AUTH_005` — โดยทั่วไป write-off recall ขนาดใหญ่, write-off สต๊อกเสียหายขนาดใหญ่, adjustment ที่ flag โดย audit ที่ผลกระทบต้นทุนสมควรการ review ของ Finance; (2) **inventory-to-GL reconciliation** — การ reconciliation เป็นระยะ (โดยทั่วไปรายสัปดาห์หรือรายเดือน) ของผลรวม sub-ledger ของกิจกรรม cost-layer กับการเปลี่ยนแปลง net ของบัญชีควบคุม GL Inventory ตาม `INV_XMOD_008`; (3) **run ปิดงวด** — orchestrate checklist ปิดงวดหลังจากการเซ็นรับรองของ Inventory Controller, post journal entry การกระทบยอด inventory-to-GL ของงวด, fire `INV_POST_009` (close) และ `INV_POST_010` (open next) ผ่าน job ปิดงวด และตรวจสอบว่า rows `tb_period_snapshot` ที่เกิด balance ไปยัง GL; (4) **ความก้าวหน้าของ period-lock** ที่ระดับ Finance Manager — advance `tb_period.status` จาก `closed` ไปยัง `locked` ตาม `INV_AUTH_006` / `INV_POST_011` หลังจาก audit window ผ่าน สำคัญ Finance **ไม่** สร้างหรือแก้ไข rows `tb_inventory_transaction` ตรง ๆ — การแก้ไขเสมอผ่านเอกสาร stock-in / stock-out / credit-note ที่ Finance อนุมัติ; Finance คือสิทธิ์การอนุมัติ ไม่ใช่มือป้อนข้อมูล

## 2. จุดเข้าและ Flow หลัก

**จุดเข้า:** สี่เส้นทาง แต่ละ anchor ไปยังกิจกรรม Finance ที่ต่างกัน

- **Queue อนุมัติผลกระทบต้นทุน** — เอกสาร `tb_stock_in` / `tb_stock_out` ที่ flag สำหรับการอนุมัติของ Finance หลังจากการอนุมัติของ Inventory Controller ตาม chain threshold ใน `INV_AUTH_005` ขับ Section 2.1
- **Dashboard inventory-to-GL reconciliation** — run เป็นระยะ (เช่นรายสัปดาห์) เปรียบเทียบ `Σ tb_inventory_transaction_cost_layer.total_cost + Σ diff_amount` สำหรับงวดกับการเปลี่ยนแปลง net ของบัญชีควบคุม GL Inventory ขับ Section 2.2
- **Dashboard orchestration ปิดงวด** — run ปิดงวดหลังจากการเซ็นรับรอง variance ของ Inventory Controller; แสดงรายการ pre-close checklist, สถานะการกระทบยอด และ trigger close ขับ Section 2.3
- **Dashboard period-lock** (Finance Manager) — มุมมองของงวด `closed` หลังจาก audit window รอ advance `closed → locked`

### 2.1 Flow อนุมัติผลกระทบต้นทุน (Controller-escalated, 5 ขั้นตอน)

1. **เปิด queue อนุมัติผลกระทบต้นทุน** แสดงเอกสารที่ sub-state Finance-pending — rows `tb_stock_in` / `tb_stock_out` ที่ Inventory Controller อนุมัติแต่ผลกระทบต้นทุนเกิน threshold ของ Controller และ route ไปยัง Finance ตาม `INV_AUTH_005` เรียงตาม submitted-at ขึ้น พร้อมผลกระทบต้นทุนและ reason code มองเห็น
2. **เปิดเอกสารเฉพาะ** Review การประเมินของ Controller: evidence ที่มาจาก (count sheet, ภาพถ่าย, vendor RMA), reason code (`adjustment_type_id`), รายละเอียดระดับ line และ preview cost-pick สำหรับ outbound Cross-check กับนัยทางการเงิน — write-off กระทบบัญชี GL ที่ถูกต้องตาม reason code หรือไม่? cost-per-unit สามารถปกป้องได้ต่อต้นทุนที่บันทึกของ lot หรือไม่?
3. **ตัดสินใจผลลัพธ์** **Approve** สำหรับ adjustment ที่ใหญ่จริงแต่สามารถปกป้องได้ (write-off recall ขนาดใหญ่กับข้อตกลง vendor, write-off expiry มวลที่บันทึกโดยการตรวจสอบ QA) **Reject** พร้อม comment สำหรับ adjustment ที่นัยทางการเงินต้องการการสนับสนุนเพิ่มเติม (ขอ engagement-letter evidence บนการเรียกร้องความเสียหายขนาดใหญ่, ขอ count ที่สองบน shortage ใหญ่ที่ไม่ได้อธิบาย) **Investigate** สำหรับ adjustment ที่รูปแบบแนะนำปัญหาเชิงระบบ (write-off concentrate บนสินค้า / vendor / lot เดียว) — route ไปยัง chain escalation Audit / Controller นอก workflow เอกสาร
4. **Approve fire การ post** บนการอนุมัติของ Finance: `tb_stock_in.doc_status = completed` (หรือ `tb_stock_out.doc_status = completed`); inventory transaction เขียนตาม `INV_POST_001` / `INV_POST_002`; GL journal entry post ไปยังบัญชีที่เหมาะสม (Dr Department Expense / Cr Inventory สำหรับ write-off ฯลฯ); activity log บันทึก `{ action: 'approved', actor_id: finance, threshold: above_controller }` Inventory Controller เห็นเอกสารที่ `completed`
5. **Reject กลับไปยัง Controller** บนการ reject ของ Finance: เอกสารกลับไปยัง queue ของ Controller พร้อม comment ของ Finance; Controller resubmit พร้อม evidence เพิ่มเติม กลับไปยัง Store Keeper เพื่อประเมินใหม่ หรือ void เอกสาร

### 2.2 Flow inventory-to-GL reconciliation (เป็นระยะ, 6 ขั้นตอน)

1. **เปิด dashboard การกระทบยอด** Dashboard render สำหรับงวด `open` ปัจจุบัน (และงวด open ก่อนหน้าที่ยังไม่เซ็นรับรอง) ผลรวมกิจกรรม cost-layer group ตาม location ประเภท `inventory`: `Σ in_qty × cost_per_unit + Σ diff_amount` (inbound net), `Σ out_qty × cost_per_unit` (outbound), `Σ adjustment_in / adjustment_out / credit_note_*` (variance) และการเปลี่ยนแปลง inventory net ที่เกิด ฝั่งขวา render ตัวเลขเดียวกันสำหรับบัญชีควบคุม GL Inventory
2. **คำนวณ variance** สำหรับแต่ละ cost-centre / location, variance = `sub_ledger_net_change − GL_net_change` Variance ต่ำกว่า tolerance (โดยทั่วไปไม่กี่เซ็นต์ต่อ location เนื่องจาก rounding) คือ **ยอมรับได้**; variance เหนือ tolerance trigger การ investigation
3. **Drill เข้า variances** สำหรับแต่ละ variance เหนือ tolerance drill จาก summary ระดับ location เข้ารายการ cost-layer rows (inventory transactions จริงในงวด) และเข้ารายการ GL journal rows สาเหตุ variance ทั่วไป: GRN ที่ post ไปยัง inventory แต่ AP-clearing journal ยังไม่ post เต็มที่, credit-note ที่ post ไปยัง GL แต่ผล cost-layer ฝั่ง inventory พลาด, stock-out post ด้วยการกำหนดบัญชี GL ผิด
4. **แก้ไข variance** **ถ้า sub-ledger ถูกต้องและ GL มี gap** — post compensating GL journal เพื่อ align (ปกติสำหรับ entry AP-clearing ที่มาสาย) **ถ้า GL ถูกต้องและ sub-ledger มี gap** — investigate การเขียน cost-layer ที่พลาดและ post corrective stock-in / stock-out (หายาก; ปกติบ่งชี้ gap data-migration หรือ bug) **ถ้าทั้งสองมี gaps** — investigate ทั้งสอง route ไปยัง System Administrator ถ้า gap เป็นปัญหา configuration / integration
5. **เอกสารการกระทบยอด** แต่ละ variance ที่แก้ไขถูก log ด้วยจำนวน variance, เส้นทางการแก้ไข (compensating journal / corrective adjustment / investigation) และผู้กระทำ Reconciliation pass เซ็นรับรองบน dashboard
6. **Carry forward ไปยังการปิดงวด** Reconciliation pass สะอาดสำหรับงวด unblock การ run ปิดงวด; variance ที่ไม่ได้แก้ไข hold งวดที่ `open` จนกว่า Finance แก้ไข

### 2.3 Flow orchestration ปิดงวด (close trigger, 7 ขั้นตอน)

1. **รอการเซ็นรับรองของ Inventory Controller** Dashboard แสดงการเซ็นรับรอง variance pre-period-end ของ Controller (จาก `03-user-flow-inventory-controller.md` Section 2 / 3); การปิดงวดเริ่มไม่ได้โดยไม่มีมัน การส่งต่อข้าม persona ตาม `03-user-flow.md` Section 4
2. **ตรวจสอบ pre-close checklist สะอาด** เอกสาร `tb_stock_in` / `tb_stock_out` / `tb_count_stock` ที่เปิดทั้งหมดในงวดที่สถานะ terminal (`completed` หรือ `voided`) เอกสาร GRN ทั้งหมดในงวด `committed` หรือ `voided` เอกสาร SR ทั้งหมดในงวด `completed` หรือ `voided` เอกสารที่เปิดใน period ปิด block การปิด
3. **Run final inventory-to-GL reconciliation** Flow ของ Section 2.2 run เป็น pass สุดท้ายสำหรับงวด; การ reconciliation ต้องผ่าน (variance ต่ำกว่า tolerance ต่อ cost-centre / location)
4. **Post journal กระทบยอดปิดงวด** Finance post **entry การกระทบยอด inventory-to-GL** ที่ absorb rounding variance ที่อนุมัติแล้วและนำบัญชีควบคุม GL Inventory ตรงกับ closing balance ของ sub-ledger Entry ทั่วไป: `Dr Inventory / Cr Inventory Rounding` หรือ `Dr Inventory Variance / Cr Inventory` สำหรับ variance เล็กที่ยอมรับได้; variance ขนาดใหญ่ไม่ absorb และ block การปิด
5. **Fire job ปิดงวด** คลิก **Close period** Job (`INV_POST_009`) sweep งวด: เขียน rows `tb_period_snapshot` ต่อ `(location_id, product_id, lot_no, lot_index)` พร้อม buckets opening / receipt / issue / adjustment / closing ตาม `INV_CALC_008`–`INV_CALC_010`; เขียน rows `close_period` cost-layer ที่ผูก closing balance กับงวด ตั้ง `tb_period.status = closed` Chain: `INV_POST_010` (open next period) เขียน rows `open_period` cost-layer เปิดงวดถัดไปที่ closing balance
6. **ตรวจสอบ snapshot** Dashboard render summary closing snapshot — closing on-hand ต่อ location, closing valuation, กิจกรรมงวด Finance cross-check กับ closing balance ของ GL (ตอนนี้เท่ากับ sub-ledger) และกับชุดรายงานปิดงวด
7. **งวดปิด** `tb_period.status = closed`; การ post ย้อนหลังเข้างวดนี้ตอนนี้ reject ตาม `INV_VAL_008` (เว้นแต่ Finance Manager re-open ตาม `INV_AUTH_006`) งวดถัดไป `open` และยอมรับ movements ตามการส่งต่อข้าม persona ไปยัง Inventory Controller และ Store Keeper

### 2.4 Flow period-lock (Finance Manager เท่านั้น, 3 ขั้นตอน)

1. **รอ audit window** หลังจากปิดงวด งวดที่ปิดอยู่ที่ `closed` ตลอด audit window (โดยทั่วไป 30–60 วันหลัง close) เพื่อให้ external auditors review และขอ adjustment Re-open ระหว่าง window นี้อนุญาตตาม `INV_AUTH_006` พร้อม justification ระดับ audit
2. **ตรวจสอบการเซ็นรับรองของ audit ได้รับ** External auditor / internal-audit team เซ็นรับรองงวดที่ปิด; ไม่มีคำขอ audit-correction ที่เปิด; รายงานการกระทบยอดยังคงสะอาด
3. **ล็อกงวด** คลิก **Lock period** Job (`INV_POST_011`) advance `tb_period.status = closed → locked` ไม่มี re-open โดย role ใด; การแก้ไข post เข้างวด open ปัจจุบันเป็น restatement

## 3. กิ่งการตัดสินใจ

- **อนุมัติผลกระทบต้นทุน vs reject** Approve เมื่อต้นทุนปกป้องได้และ GL classification (ขับโดย `adjustment_type_id`) ถูกต้อง Reject สำหรับ evidence ขาดบน adjustment ขนาดใหญ่, GL classification ผิด หรือ cost-per-unit ผิดปกติ **Investigate** เมื่อ adjustment เป็นส่วนของรูปแบบน่าสงสัย — concentrate บนสินค้า / vendor / lot เดียว — โดยไม่ reject เอกสารเฉพาะ
- **Reconciliation variance: ภายใน tolerance vs investigate vs resolve** ภายใน tolerance (โดยทั่วไปไม่กี่เซ็นต์ต่อ location) — ยอมรับและเอกสาร เหนือ tolerance — drill และแก้ไขตาม Section 2.2 step 4 Variance ที่ไม่ได้แก้ไขอย่างต่อเนื่อง — escalate ไปยัง System Administrator (ปัญหา integration / configuration) หรือไปยังทีม Audit (ปัญหา data-integrity ที่อาจเป็น)
- **Gate ปิดงวด vs hold** ปิดเมื่อ (a) Inventory Controller เซ็นรับรอง, (b) เอกสาร source ทั้งหมดในงวดเป็น terminal, (c) การกระทบยอด final ผ่าน Hold เมื่อ gate ใดเปิด — สื่อสาร hold กับ persona ที่ได้รับผลกระทบพร้อมวันที่คาดว่าจะแก้ไข
- **Re-open งวดหลังปิด (ภายใน audit window)** Re-open เมื่อ (a) external audit ระบุ adjustment ที่จำเป็นในงวดที่ปิดและ adjustment ไม่สามารถทำเป็น restatement งวด-ปัจจุบัน, (b) การแก้ไขทางวัตถุดิบถูกค้นพบ (เช่น credit note ที่ควร post ในงวดที่ปิด) Re-open คือ audit-logged; งวดต้อง re-close ก่อนการปิดงวดปกติถัดไป
- **Period lock — ไม่มี re-open path** Lock เฉพาะเมื่อ (a) audit window ผ่านอย่างสะอาดโดยไม่มีคำขอ audit-correction ที่เปิด, (b) external audit เซ็นรับรอง หลังจาก lock ไม่มี role re-open ได้; การแก้ไขใด ๆ post เข้างวด open ปัจจุบันเป็น restatement

## 4. จุดออก / การส่งต่อ

การมีส่วนร่วมของ Finance บนสาย inventory ที่กำหนดจบที่หนึ่งในสี่ขอบเขต:

- **Adjustment ผลกระทบต้นทุนอนุมัติและ post** เอกสาร `tb_stock_in` / `tb_stock_out` ที่ escalate post; inventory transaction และ GL journal เขียน; queue ของ Inventory Controller refresh การมีส่วนร่วมของ Finance บนเอกสารนี้เสร็จ
- **Variance การกระทบยอดแก้ไข** Compensating journal หรือ corrective adjustment post; reconciliation pass สะอาดสำหรับงวด; Finance เซ็นรับรอง การส่งต่อ (โดยปริยาย) ไปยัง persona **Audit / Config** ที่ review กิจกรรมการกระทบยอดใน audit trail
- **งวดปิด** rows `tb_period_snapshot` เขียน; `tb_period.status = closed`; การ post ย้อนหลัง reject ส่งต่อไปยัง **Inventory Controller** และ **Store Keeper** สำหรับการจัดการ variance ของงวดใหม่; ส่งต่อไปยัง **Finance Manager** สำหรับความก้าวหน้า close-to-lock
- **งวดล็อก** `tb_period.status = locked`; immutable ถาวร ส่งต่อไปยัง **Auditor** สำหรับการ review audit-trail ระยะยาว; ไม่มีการกระทำฝั่ง inventory เพิ่มเติมบนงวดนี้

## 5. แหล่งอ้างอิง

- ภาพรวม Parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต movement-and-period แบบ canonical ตารางการส่งต่อข้าม persona ที่ anchor ขอบเขต Inventory Controller → Finance (ผลกระทบต้นทุน, เซ็นรับรองปิดงวด) และ Finance → Finance Manager → Auditor (close, lock)
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — ผู้เริ่ม adjustment ที่ผลกระทบต้นทุนอาจขึ้นถึง threshold ของ Finance
- Sibling: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md) — persona ต้นน้ำที่อนุมัติ adjustment ต่ำกว่า threshold ของ Finance และเซ็นรับรอง variance ก่อนปิดงวด; route adjustment ต้นทุนใหญ่ไปยัง Finance
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Auditor ที่ review กิจกรรมการกระทบยอดของ Finance และ audit trail ปิดงวด; Sysadmin ที่ตั้งค่า map บัญชี GL, costing method ต่อสินค้า, tolerance การกระทบยอด และ period definition
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_inventory_transaction_cost_layer` แบบ canonical (sub-ledger ที่ Finance reconcile กับ GL), `tb_period` / `tb_period_snapshot` (สถานะ close / lock และ rows snapshot ที่ job ปิดงวดเขียน), `enum_period_status` (`open` / `closed` / `locked`), `enum_inventory_doc_type` (`close` / `open` สำหรับ rollforward)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ authorization `INV_AUTH_005` (อนุมัติผลกระทบต้นทุนของ Finance), `INV_AUTH_006` (Finance Manager lock / re-open งวด), `INV_AUTH_007` (system context สำหรับ posting `close` / `open`), บวกกฎ posting `INV_POST_009` (close), `INV_POST_010` (open next), `INV_POST_011` (lock) และกฎข้ามโมดูล `INV_XMOD_008` (inventory-to-GL reconciliation)
- ที่เกี่ยวข้อง: [[costing]] — cost-layer ledger ที่ Finance reconcile คือสิ่งที่ costing อ่านสำหรับ COGS; กิจกรรมการกระทบยอดของ Finance คือ audit anchor สำหรับ outputs ของโมดูล costing
- ที่เกี่ยวข้อง: [[good-receive-note]] — การกระทบยอดของ Finance drill เข้า GRN AP-clearing journal posts เมื่อการ investigation variance พบ gap ฝั่ง GRN `03-user-flow-finance.md` ของโมดูล GRN ครอบคลุมเส้นทาง three-way-match ที่สร้าง entries AP-clearing
- ที่เกี่ยวข้อง: [[inventory-adjustment]] — เส้นทาง corrective stock-in / stock-out ที่ Finance ใช้เมื่อ reconciliation พบ gap ของ sub-ledger ที่ไม่สามารถแก้ไขได้โดย GL journal คนเดียว
- ที่เกี่ยวข้อง: credit note — Finance book credit notes กับ GRNs; ผลฝั่ง inventory ของ credit-note (`credit_note_amount` / `credit_note_quantity`) เป็นส่วนของพื้นผิวการกระทบยอดสำหรับงวดที่ credit-note post
