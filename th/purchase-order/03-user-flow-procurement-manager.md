---
title: ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)
description: เส้นทางผู้ใช้งานของผู้จัดการฝ่ายจัดซื้อในโมดูล purchase-order — อนุมัติ PO มูลค่าสูง จัดลำดับผู้ขาย และปรับกฎการแปลง/จัดกลุ่ม
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, procurement-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)

## 1. บทบาทในโมดูลนี้

**ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)** เป็นเจ้าของการกำกับดูแลฟังก์ชันการจัดซื้อทั้งระบบ และเข้ามาทำงานในโมดูล PO ผ่าน **สองหน้างานที่แตกต่างกัน** หน้างานแรกคือ **หน้างาน transactional** ซึ่งเป็น gate การอนุมัติมูลค่าสูงที่ stage สุดท้ายของห่วงโซ่ workflow — PO ที่ `tb_purchase_order.total_amount` เกิน threshold ของ tenant (หรือมี pricelist deviation เกิน tolerance ตาม `PO_XMOD_006`) ถูก route เข้ามาที่นี่เพื่อ transition `in_progress → sent` ที่ Purchaser ไม่สามารถ self-approve ได้ตาม `PO_AUTH_004` และ Manager เลือกระหว่างอนุมัติ-และ-ส่ง (`PO_POST_004`), ส่ง PO กลับให้ Purchaser แก้ไข (`PO_POST_005`) หรือ reject เพื่อยุติ workflow ที่ `voided` (`PO_POST_010`) หน้างานที่สองคือ **หน้างาน configurational** ซึ่งเป็น workbench ปรับจูนกฎที่ Manager ดูแล vendor master และ ranking, กฎจัดกลุ่ม `(vendor_id, currency_id)` ที่ Convert-to-PO ใช้, conversion factor ของหน่วยที่ขับ `PO_VAL_009` / `PO_CALC_011`, แถบ tolerance ของ pricelist ที่ gate `PO_XMOD_006` และ threshold มูลค่าสูงเองบน workflow definition ที่ `tb_purchase_order.workflow_id` อ้างถึง นอกจากนี้ Manager ยังถือ **อำนาจ override** ที่ Purchaser ทำไม่ได้: soft-delete-in-draft (`PO_AUTH_005`), void จาก state ที่ไม่ใช่ terminal ใดๆ (`PO_AUTH_007`, `PO_POST_010`), early-close จาก `partial → closed` (`PO_POST_011` ร่วมกับ Inventory Manager ตาม `PO_AUTH_008`) และ override การ send-back ของ Purchaser ในกรณีที่การส่งกลับเป็น draft จะทำให้ PO ที่เร่งด่วนถูกค้าง Manager ทำงานภายใต้ `enum_stage_role = approve` ที่ stage มูลค่าสูง และเพิ่มเติมในฐานะ administrator การกำหนดค่านอกเหนือจาก workflow transactional

## 2. จุดเริ่มต้นและเส้นทางหลัก

Procurement Manager ทำงานสองเส้นทางควบคู่กัน — **เส้นทาง transactional** ที่ trigger เมื่อ PO ที่ escalate มาถึงคิวอนุมัติ และ **เส้นทาง configuration** ที่ขับด้วยจังหวะช้ากว่าเพื่อรักษากฎให้ทันสมัย แต่ละหน้างานมีจุดเริ่มต้นและจังหวะการตัดสินใจของตัวเอง

### เส้นทาง transactional — อนุมัติมูลค่าสูง

**จุดเริ่มต้น:** Notification ใน in-app "Purchase Order [PO-No] Awaiting High-Value Approval" หรือ digest อีเมล deep-link เข้าคิว **Approvals → Pending** ที่กรองด้วย `workflow_current_stage = <stage มูลค่าสูง>` หรือ Sidebar → โมดูล **Purchase Order** → รายการ **My Approvals** เรียงด้วย `total_amount` มากไปน้อย

**เส้นทางหลัก (happy path):**

1. รับการ escalate Notification จุดติดเมื่อ PO transition `draft → in_progress` (`PO_POST_002`) และ stage cursor ของ workflow ตกลงที่ stage อนุมัติมูลค่าสูง — เพราะ `tb_purchase_order.total_amount` เกิน threshold ของ tenant (`PO_AUTH_004`) หรือเพราะ pricelist deviation เกิน tolerance force-route เข้ามาที่นี่ตาม `PO_XMOD_006` user-id ของ Manager อยู่ใน `user_action.execute` ของ stage ปัจจุบันที่ populate ไว้
2. เปิดหน้า **PO detail** จากคิวอนุมัติ ตรวจส่วนหัว (vendor, currency, exchange rate, credit term, order date, delivery date) ว่าถูกต้องตาม `PO_VAL_002`–`PO_VAL_006` ยืนยันว่าเส้นทาง workflow คือเส้นทางที่คาดหวังสำหรับ tier มูลค่านี้และไม่มี validation flag (deviation, missing pricelist coverage ตาม `PO_XMOD_005`, segregation-of-duties warning ตาม `PO_AUTH_010`) ค้างอยู่
3. ไล่ดูแท็บ **Items** สำหรับแต่ละบรรทัด ตรวจตัวบ่งชี้ pricelist deviation, flag `is_foc`, `cancelled_qty` (ควรเป็นศูนย์ ณ stage นี้), PR ที่ link ผ่าน bridge table สำหรับ PO ที่มาจาก PR (`PO_XMOD_001`) และ `delivery_date` รายบรรทัด Manager ตรวจ roll-up การคำนวณซ้ำ: `total_price`, `total_tax`, `total_amount` ตาม `PO_CALC_008`–`PO_CALC_010`
4. ตรวจแท็บ **Attachments** และ **Comments** Manager มองหา vendor quote, note เหตุผลของผู้ซื้อ, comment ของผู้อนุมัติ stage ก่อนหน้า และ (สำหรับ PO ที่ route ด้วย deviation) เหตุผลที่ระบุชัดเจนใน `tb_purchase_order_detail_comment` คอลัมน์ JSON `history` และ `workflow_history` แสดงห่วงโซ่เต็มของเหตุการณ์ `created → submitted → approved`
5. ตัดสินใจ Manager มีสาม action ที่ stage นี้:
   - **Approve at final stage** — กด **Approve & Transmit** `po_status` เปลี่ยน `in_progress → sent` ผ่าน `PO_POST_004`, `approval_date = now()`, `last_action = approved` และระบบจุดติดตัว transmit handler ภายใต้ `PO_AUTH_006` เพื่อ email / EDI / portal-post PO ให้ผู้ขาย Soft budget commitment กลายเป็น vendor liability
   - **Send back** — กด **Return to Buyer** และใส่เหตุผลที่บังคับ `po_status` เปลี่ยน `in_progress → draft` ผ่าน `PO_POST_005`, `workflow_current_stage` รีเซ็ตเป็นจุดเริ่ม, `last_action = rejected` และเหตุผลถูก append ใน `tb_purchase_order_comment` (type `system`) Purchaser หยิบ PO จากคิว **Returned** ของตัวเอง
   - **Reject / void** — กด **Reject** และใส่เหตุผลที่บังคับ `po_status` เปลี่ยน `in_progress → voided` ผ่าน `PO_POST_010`, `is_active = false`, workflow ยุติ และ soft budget commitment ใดๆ ที่มีอยู่ถูกปลด `voided` เป็น terminal
6. (หลังจาก approve-and-transmit) ยืนยันผลการส่ง activity log บันทึก channel และ timestamp; การตอบรับของผู้ขาย (ที่ channel รองรับ) feed มุมมอง **Sent POs awaiting acknowledgement** ที่ Manager เฝ้าดูแบบมุมมองเดียว
7. (Optional, เส้นทาง override) เข้าแทรกแซง PO ที่ state สูงกว่า จากหน้า PO detail Manager สามารถ void PO ที่อยู่ `sent` หรือ `partial` (`PO_AUTH_007`, `PO_POST_010`) — ตัวอย่างเช่นเมื่อผู้ขายยกเลิก — หรือปิด PO ที่อยู่ `partial` ก่อนกำหนด (`PO_AUTH_008`, `PO_POST_011`) เมื่อผู้ขายไม่สามารถส่งยอดคงเหลือได้ ทั้งสอง action ต้องการ reason text และถูกบันทึกใน activity log ดูหัวข้อ 3 สำหรับเงื่อนไขการตัดสินใจ

### เส้นทาง configuration — ปรับจูนกฎ

**จุดเริ่มต้น:** Sidebar → **Procurement → Configuration** → เลือกกฎที่จะแก้: **Vendor Ranking & Allocation**, **Convert-to-PO Grouping**, **Unit Conversion**, **Pricelist Tolerance** หรือ **Workflow Threshold** หน้าจอการกำหนดค่าถูก gate ด้วย role Procurement Manager; Purchaser ทั่วไปมี read-only บนหน้าจอเดียวกัน

**เส้นทางหลัก (happy path):**

1. เปิด workbench กฎเป้าหมาย หน้าจอแสดงชุดกฎปัจจุบันพร้อม metadata: rule id, effective-from date, last-updated-by และจำนวน PO ที่ in-flight ที่ถือ snapshot ของเวอร์ชันก่อนหน้า หน้าจอ **Vendor Ranking & Allocation** เรียง vendor ด้วยคะแนน performance (อัตราการส่งตรงเวลา, อัตราสำเร็จ three-way-match, อัตรา deviation); หน้าจอ **Convert-to-PO Grouping** แสดง grouping key `(vendor_id, currency_id)` และ secondary key ที่เลือกได้ (delivery location, payment term) ที่ tenant เปิดใช้; หน้าจอ **Unit Conversion** แสดง factor `order_unit → base_unit` รายสินค้าที่ feed `PO_VAL_009` และ `PO_CALC_011`; หน้าจอ **Pricelist Tolerance** แสดงแถบ `±X%` ที่ gate `PO_XMOD_006`; หน้าจอ **Workflow Threshold** แสดง cutoff มูลค่าสูงที่ trigger `PO_AUTH_004`
2. แก้ไขกฎ ปรับ parameter — ยก vendor ขึ้นหรือลง, เปลี่ยน grouping key, อัปเดต conversion factor, ขยายหรือหด tolerance, เพิ่มหรือลด threshold ระบบ flag PO ที่ in-flight ที่ snapshot ค่าก่อนหน้าและเตือนว่าการเปลี่ยนแปลงจะมีผลต่อ PO **ใหม่** เท่านั้น (ตามหลักการ snapshot ด้านล่าง)
3. บันทึกการเปลี่ยนแปลง ระบบเขียนกฎเวอร์ชันใหม่พร้อม timestamp effective-from, เพิ่มตัวนับเวอร์ชันของกฎ และบันทึกการเปลี่ยนแปลงใน audit log การกำหนดค่าพร้อม user-id ของ Manager, ค่าก่อนหน้า และค่าใหม่ PO ใหม่ที่สร้างจากจุดนี้ไปจะใช้กฎใหม่; draft PO ที่อยู่ใน `in_progress` แล้วและ PO ที่อยู่ `sent` / `partial` แล้วคง snapshot ของตัวเอง
4. แจ้งผู้ใช้ที่ได้รับผลกระทบ ระบบจุดติด notification การเปลี่ยนแปลงการกำหนดค่าไปยัง Purchaser ("Vendor ranking updated", "Convert-to-PO grouping rule updated", "Unit conversion factor changed for product [SKU]") เพื่อให้ทีมผู้ซื้อรับทราบก่อนรอบ Convert-to-PO ครั้งต่อไป
5. (Optional) ทดสอบการเปลี่ยนแปลง สำหรับกฎ grouping และ threshold Manager สามารถรัน dry-run preview กับชุด PR สังเคราะห์เพื่อยืนยันว่ากฎสร้าง pattern grouping หรือ escalation ที่คาดหวังก่อนใช้ใน production
6. (Optional) rollback ถ้ารายงานปลายน้ำหรือ escalation จากผู้ซื้อพบประเด็น Manager เปิด workbench กฎอีกครั้ง, restore เวอร์ชันก่อนหน้า (ที่ audit log เก็บไว้) และเวอร์ชันใหม่จะมีผลกับ PO ที่สร้างหลัง timestamp ของการ rollback

## 3. สาขาการตัดสินใจ

- **ถ้ามี escalation ซับซ้อนที่ PO มูลค่าสูงถูกต้องในเชิงเทคนิคแต่น่ากังขาเชิงพาณิชย์** (เช่น ราคาสูงกว่า benchmark เดิม, vendor ทางเลือกที่รู้ว่าถูกกว่า, บรรทัด FOC ที่ควรจะคิดเงิน): Manager ตรวจ vendor quote ใน **Attachments**, ประวัติ PO ก่อนหน้าใน activity ของ [[vendor-pricelist]] และเหตุผลของ Purchaser ใน **Comments** ถ้าคำตอบคือ "นี่คือ vendor ที่ถูกต้องในราคาที่ถูกต้อง" Manager approve-and-transmit ถ้าคำตอบคือ "ต้องให้ผู้ซื้อเจรจาใหม่หรือเลือก vendor อื่น" Manager ส่งกลับให้ Purchaser พร้อมเหตุผลการเจรจาใหม่ใน comment ถ้าคำตอบคือ "PO นี้ไม่ควรเกิดขึ้น" Manager reject เป็น `voided` (`PO_POST_010`) และแจ้ง Purchaser ผ่าน reason field มาตรฐาน; workflow ยุติและ soft commitment ถูกปลด
- **ถ้า Manager ต้องการเปลี่ยนกฎที่ PO in-flight ได้ snapshot ไว้แล้ว** (เช่น ยก threshold มูลค่าสูงในขณะที่ PO ระดับเส้นแบ่งกำลังนั่งอยู่ที่ `in_progress` ที่ stage มูลค่าสูง): หน้าจอแก้กฎจะเตือนเรื่อง PO in-flight และให้สองเส้นทาง (a) **Save and apply going forward** — threshold ใหม่มีผลต่อ PO ใหม่เท่านั้น; PO in-flight เดินผ่าน stage มูลค่าสูงต่อด้วย threshold เดิม (b) **Save and re-route in-flight** — ใช้ได้เฉพาะเมื่อ workflow definition รองรับการ re-route; PO in-flight ถูกดันกลับเป็น `draft` (พร้อม system comment), threshold ใหม่ถูกประเมินกับ `total_amount` และ PO อาจ skip stage มูลค่าสูงเมื่อ resubmit หรือยังคงอยู่ที่ stage นั้นขึ้นกับค่าใหม่ tenant ส่วนใหญ่ปิด (b) เพื่อความปลอดภัยของ audit และใช้ (a) เท่านั้น ซึ่งเป็นเหตุที่กฎ snapshot-on-submit (เส้นทาง transactional ขั้นตอน 2) ถูกบันทึกเป็น default
- **ถ้าต้อง action กลุ่มกับ PO ที่ค้าง** (เช่น vendor เลิกกิจการและ PO active 12 ใบที่ `sent` / `partial` ต้องถูก void หรือ early-close ในรอบเดียว): จากรายการ PO Manager filter ด้วย vendor และ status, multi-select แถวที่กระทบ และรัน **Bulk Void** (`PO_AUTH_007`, `PO_POST_010`) หรือ **Bulk Close** (`PO_AUTH_008`, `PO_POST_011`) แต่ละ action ต้องการ reason text หนึ่งครั้งที่บันทึกรายใบใน activity log สำหรับ PO ที่อยู่ `partial` เส้นทาง bulk-close เขียนยอดคงเหลือของแต่ละบรรทัดเป็น `cancelled_qty` ให้ `received_qty + cancelled_qty = order_qty` PO ที่อยู่ `completed`, `closed` หรือ `voided` แล้วถูกข้ามจาก bulk action (terminal state เปลี่ยนไม่ได้)
- **ถ้า Manager override การ send-back ของ Purchaser** (ผู้ซื้อส่ง PO กลับเป็น draft ที่ Manager เชื่อว่าควรเดินต่อ — เช่น PO เร่งด่วนที่ประเด็นของผู้ซื้อไม่ blocking): เส้นทาง override คือ re-submit PO จาก `draft` ในนามของผู้ซื้อ (role ของ Manager inherit สิทธิ์ Purchaser ตาม hierarchy ของ role) และอนุมัติที่ stage มูลค่าสูงตามปกติ override ถูกบันทึกเป็นสองเหตุการณ์ที่แตกต่างใน audit log — การ send-back ครั้งแรกจากผู้ซื้อ และการ re-submit ของ Manager พร้อม comment เหตุผล เส้นทางทางเลือก: Manager re-route workflow definition ให้ข้าม stage ของผู้ซื้อทั้งหมดสำหรับ PO นี้และอนุมัติโดยตรง — ใช้ได้เฉพาะเมื่อ workflow ของ tenant อนุญาตการ re-route ด้วยมือ
- **ถ้ามี PO ที่ route ด้วย deviation มาถึงที่ไม่ควรจะถูก route มาที่นี่** (flag deviation ถูกยกโดย `PO_XMOD_006` แต่เมื่อตรวจแล้วราคาถูกต้องและ pricelist เองล้าสมัย): Manager approve-and-transmit ตามปกติและเปิด workbench กฎ **Pricelist Tolerance** เพิ่มเติมเพื่อ refresh แถว pricelist ต้นทางใน [[vendor-pricelist]] หรือปรับ tolerance band ให้ PO คล้ายกันครั้งต่อไปไม่ถูก re-route โดยไม่จำเป็น นี่คือ loop ที่ทำให้หน้างาน transactional และ configurational synchronise กัน
- **ถ้า Manager soft-delete draft PO** (ผู้ซื้อสร้าง PO ผิดและทิ้งไว้ หรือ PO ซ้ำกับ PO active อื่น): จากหน้า draft PO detail Manager รัน **Delete Draft** (`PO_AUTH_005`, `PO_POST_012`); `deleted_at` และ `deleted_by_id` ถูกตั้ง และแถวยังคงอยู่ใน database เพื่อ audit เนื่องจาก unique index บน `po_no` รวม `deleted_at` `po_no` เดียวกันถูกปลดให้ใช้ซ้ำได้ ผู้ซื้อได้รับแจ้งผ่าน notification เหตุการณ์การลบมาตรฐาน

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทของ Procurement Manager ต่อ PO และชุดกฎที่ดูแลสิ้นสุดที่หนึ่งในจุด handoff ต่อไปนี้

### Handoff transactional

- **อนุมัติขั้นสุดท้าย → ส่งให้ผู้ขาย** — Manager อนุมัติที่ stage มูลค่าสูงและ `po_status` เปลี่ยน `in_progress → sent` ผ่าน `PO_POST_004` ส่งต่อไปยัง **Vendor**; สถานะเอกสาร ณ จุดส่งต่อคือ `sent` PO กลายเป็น commitment ผูกพัน; **Purchaser** ติดตามการตอบรับของผู้ขายและ transition ที่ขับด้วย GRN ในที่สุดบน dashboard Open POs ดู [03-user-flow-vendor.md](./03-user-flow-vendor.md) สำหรับเส้นทางฝั่งภายนอก
- **Reject → terminal voided** — Manager reject พร้อมเหตุผลและ `po_status` เปลี่ยน `in_progress → voided` ผ่าน `PO_POST_010` ส่งต่อไปยัง **Auditor** สำหรับการตรวจสอบย้อนหลังเท่านั้น; สถานะเอกสาร ณ จุดส่งต่อคือ `voided` (terminal) Soft budget commitment ใดๆ ที่มีอยู่ถูกปลด Purchaser ได้รับแจ้งและสามารถใช้เหตุผลเพื่อบอกผู้ร้องขอหรือออก PO ที่แก้ไขแล้วใหม่ถ้าความต้องการต้นทางยังคงอยู่
- **Send back → ผู้ซื้อแก้ไข** — Manager ส่ง PO กลับเป็น draft พร้อมเหตุผลและ `po_status` เปลี่ยน `in_progress → draft` ผ่าน `PO_POST_005` ส่งต่อไปยัง **Purchaser**; สถานะเอกสาร ณ จุดส่งต่อคือ `draft` Purchaser หยิบ PO จากคิว **Returned** ของตัวเอง, แก้ไขตามเหตุผลของ Manager และ resubmit ผ่านห่วงโซ่ผู้อนุมัติทั้งหมด บทบาทของ Manager กลับมาเล่นต่อถ้า PO ที่ resubmit ตกถึง stage มูลค่าสูงอีกครั้ง
- **Void ที่ non-draft / early-close** — Manager void PO ที่อยู่ `sent` หรือ `partial` (`PO_AUTH_007`, `PO_POST_010`) หรือ early-close PO ที่อยู่ `partial` (`PO_AUTH_008`, `PO_POST_011`) ส่งต่อไปยัง **Finance** (สำหรับ AP close-out review ของ accrual ที่ GRN ได้ post ไว้แล้ว) และไปยัง **Auditor**; สถานะเอกสาร ณ จุดส่งต่อคือ `voided` หรือ `closed` ตามลำดับ (ทั้งสอง terminal) ดู [03-user-flow-finance.md](./03-user-flow-finance.md) สำหรับ close-out ฝั่ง AP

### Handoff configurational

- **บันทึกการเปลี่ยนกฎ → มีผลกับ PO ใหม่** — Manager บันทึกการเปลี่ยน vendor ranking, Convert-to-PO grouping, unit conversion, pricelist tolerance หรือ threshold มูลค่าสูง ส่งต่อไปยัง **Purchaser** ทั้งทีมผ่าน notification การเปลี่ยนแปลงการกำหนดค่า; ผลกระทบอยู่ที่ PO ใหม่เท่านั้น **PO in-flight คง snapshot** ของกฎเวอร์ชันก่อนหน้าไว้ — draft ที่อยู่ `in_progress` แล้วเดินบน stage workflow เดิม, PO ที่อยู่ `sent` แล้วคง `vendor_id`, `currency_id`, `exchange_rate`, `price` รายบรรทัด และ `order_unit_conversion_factor` รายบรรทัดที่ถูกเก็บไว้ โดยไม่สนใจการแก้กฎที่ตามมา หลักการ snapshot นี้คือสิ่งที่ทำให้หน้างาน configurational ปลอดภัยที่จะ operate ในจังหวะที่ต่างจากหน้างาน transactional
- **Rollback กฎ → restore เวอร์ชันก่อนหน้า** — Manager rollback การเปลี่ยนกฎ ส่งต่อไปยัง **Purchaser** ทั้งทีมผ่าน notification อีกครั้ง; กฎเวอร์ชันก่อนหน้าถูก restore สำหรับ PO ที่สร้างจาก timestamp ของการ rollback ไปข้างหน้า หลักการ forward-only-effect ยังคงใช้: PO ที่สร้างระหว่างการ save ครั้งแรกและการ rollback คงกฎเวอร์ชัน (ที่ตอนนี้ superseded แล้ว) ที่ตัวเอง snapshot ไว้

Transition ที่ขับโดยการรับสินค้า (`sent → partial → completed` ผ่าน `PO_POST_006`/`PO_POST_007`) ไม่ใช่ action ของ Procurement Manager — ขับโดย **Receiver** ผ่านการ post GRN Manager สังเกตการ transition เหล่านี้บน dashboard และเข้าแทรกแซงผ่านเส้นทาง early-close หรือ void override ที่อธิบายข้างต้นเท่านั้น

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.md](./03-user-flow.md) — global state machine ของ PO และตาราง handoff ข้าม persona
- ไฟล์พี่น้อง: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ต้นน้ำที่ submit PO ที่ escalate มาถึง Manager และเป็นผู้รับ send-back ที่ `draft`
- ไฟล์พี่น้อง: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — บุคคลภายนอกปลายน้ำที่รับ PO ที่ส่งมาที่ `po_status = sent`
- ไฟล์พี่น้อง: [03-user-flow-finance.md](./03-user-flow-finance.md) — close-out ฝั่ง AP ของ accrual ที่ GRN ได้ post ไว้แล้วเมื่อ Manager void หรือ early-close PO ที่อยู่ `partial`
- ไฟล์พี่น้อง: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator ที่กำหนดค่า workflow definition และ RBAC binding ที่การแก้กฎของ Manager พึ่งพา; Auditor ที่ตรวจ activity log ของ action approve / reject / void / config-change ของ Manager
- กฎ authorization: [02-business-rules.md](./02-business-rules.md) หัวข้อ 4 — `PO_AUTH_004` (อนุมัติมูลค่าสูง), `PO_AUTH_005` (delete-in-draft), `PO_AUTH_007` (void จาก non-draft), `PO_AUTH_008` (early-close จาก partial), `PO_AUTH_010` (segregation of duties), `PO_AUTH_011` (gating ของ workflow stage)
- กฎ posting: [02-business-rules.md](./02-business-rules.md) หัวข้อ 5 — `PO_POST_004` (อนุมัติขั้นสุดท้ายและส่ง), `PO_POST_005` (send-back กลับเป็น draft), `PO_POST_010` (void จาก state ใดก็ได้ที่ไม่ใช่ terminal), `PO_POST_011` (early-close จาก partial), `PO_POST_012` (soft-delete ใน draft)
- กฎข้ามโมดูล: [02-business-rules.md](./02-business-rules.md) หัวข้อ 6 — `PO_XMOD_001` / `PO_XMOD_002` (link bridge PR), `PO_XMOD_005` / `PO_XMOD_006` (snapshot vendor-pricelist และ deviation routing), `PO_XMOD_007` (ปฏิสัมพันธ์ของ three-way-match AP กับการ void / close)
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่งหลักจาก carmen/docs สำหรับการวิเคราะห์ทางธุรกิจของโมดูล PO, ตาราง RBAC และ state diagram ที่เส้นทางนี้อ้างถึง
- โมดูลที่เกี่ยวข้อง: [[vendor-pricelist]] — vendor master, pricelist coverage และ tolerance band ที่ Manager ปรับจูนจากหน้างาน configuration
- โมดูลที่เกี่ยวข้อง: [[purchase-request]] — โมดูลต้นน้ำที่การแปลง PR-to-PO ถูก govern ด้วยกฎ grouping ที่ Manager กำหนด
- โมดูลที่เกี่ยวข้อง: [[good-receive-note]] — การรับของปลายน้ำที่ Manager สังเกตการ post receipt; early-close และ void จาก `partial` โต้ตอบกับ accrual ของ GRN ผ่าน `PO_XMOD_007`
