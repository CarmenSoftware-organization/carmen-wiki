---
title: ใบขอซื้อ — เส้นทางผู้ใช้งาน — เจ้าหน้าที่จัดซื้อ (Purchaser)
description: เส้นทางผู้ใช้งานของ Purchaser ในโมดูล purchase-request — การจัดสรรผู้ขาย รวมรายการ และแปลงเป็น PO
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, user-flow, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — เส้นทางผู้ใช้งาน — เจ้าหน้าที่จัดซื้อ (Purchaser)

## 1. บทบาทในโมดูลนี้

**เจ้าหน้าที่จัดซื้อ (Purchaser)** (มีอีกชื่อหนึ่งว่า **Procurement Officer**) เป็น persona ที่เป็นสะพานเชื่อมระหว่างฝั่งต้นน้ำ (PR) และฝั่งปลายน้ำ (PO) ของห่วงโซ่ procure-to-pay Purchaser **ไม่** ทำหน้าที่อนุมัติเนื้อหา PR — เมื่อ PR เข้าถึงคิวของ Purchaser แล้วแปลว่าผ่านห่วงโซ่ผู้อนุมัติทั้งหมดและมี `pr_status = approved` (`PR_POST_005`) งานของ Purchaser คือนำสิ่งที่อนุมัติแล้วมาตรวจการจัดสรร vendor รายบรรทัด เปิดดู vendor pricelist ปัจจุบันเพื่อตรวจราคาและ deviation รวมบรรทัดจาก PR หลายฉบับที่มี **vendor + currency** เดียวกันให้ออก PO ใบเดียวกัน แล้วสั่ง Convert to PO การ link จากบรรทัด PR ไปยังบรรทัด PO ถูกบันทึกใน bridge table `tb_purchase_order_detail_tb_purchase_request_detail` ([01-data-model.th.md](./01-data-model.th.md) หัวข้อ 2) — เป็น many-to-many ที่รองรับทั้งการ **consolidation** (หลายบรรทัด PR → บรรทัด PO เดียว) และการแปลง **partial** (บรรทัด PR เดียว → บรรทัด PO หลายใบข้าม vendor หรือวันส่งของ) เมื่อพบประเด็นเกี่ยวกับ vendor หรือ spec ที่ต้องเคลียร์ Purchaser สามารถ route PR กลับไปยังผู้ร้องขอด้วยกลไก send-back มาตรฐานของ PR แทนการ Convert ต่อ Purchaser ทำงานภายใต้ `enum_stage_role = purchase` (`PR_AUTH_008`)

## 2. จุดเริ่มต้นและเส้นทางหลัก

**จุดเริ่มต้น:** Sidebar → โมดูล **Purchase Request** → คิว **Approved PRs** (กรอง `pr_status = approved` ที่ยังไม่ถูก bridge ไปยัง PO ครบทุกบรรทัด) ทางเลือก: workspace ของฝ่ายจัดซื้อ → workbench **Convert to PO** ซึ่งแสดง pool ของบรรทัดที่อนุมัติแล้วโดยจัดกลุ่มตาม vendor + currency Notification ทาง in-app และอีเมล "Purchase Request [PR-ID] Ready for PO Conversion" deep-link เข้าหน้ารายละเอียด PR โดยตรง

**เส้นทางหลัก (happy path):**

1. จากคิว **Approved PRs** ใช้ filter — vendor, currency, ช่วงวันส่งที่ต้องการ, แผนก, store location — เพื่อจำกัด working set คิวแสดง `pr_no`, ผู้ร้องขอ, แผนก, จำนวนบรรทัด, `base_total_amount`, vendor (ถ้า vendor เดียวครอบคลุมทุกบรรทัด) หรือ "multi-vendor", สกุลเงิน และเวลาที่ PR ค้างอยู่ใน `approved` จำนวนบรรทัดที่ยังไม่ถูก bridge เทียบกับจำนวนบรรทัดทั้งหมดของแต่ละ PR ปรากฏในแต่ละแถว ทำให้ PR ที่แปลงเพียงบางส่วนสังเกตเห็นได้ทันที
2. เปิด PR โดยคลิกเข้าไป หน้ารายละเอียดเป็น **read-mostly** สำหรับ Purchaser: ส่วนหัว (PR type, ผู้ร้องขอ, แผนก, `pr_date`, วันส่งของที่ต้องการ, สกุลเงิน, `exchange_rate`, เหตุผล, ไฟล์แนบ) แก้ไม่ได้; สิ่งที่ interact ได้คือ vendor allocation, การเลือก pricelist และ checkbox conversion รายบรรทัดเท่านั้น
3. ไล่ดู **บรรทัดที่อนุมัติแล้ว** แต่ละบรรทัด ตรวจค่า `vendor_id` / `vendor_name` ที่ snapshot ไว้ ถ้าผู้ร้องขอหรือระบบ allocate vendor ไว้ล่วงหน้า Purchaser ตรวจกับข้อมูล vendor master ปัจจุบัน (สถานะ active, payment terms, credit limit, blacklist flag) ที่ดึงสด ๆ จาก [[vendor-pricelist]] และ [[vendor-pricelist]] ถ้าบรรทัดยังไม่มี vendor allocation Purchaser เปิด dialog Allocate Vendor แล้วเลือก — dialog เรียง vendor candidate ตามการ match pricelist กับสินค้า, location และวันที่ต้องการ พร้อมแสดงราคาปัจจุบัน, lead time และประวัติ performance
4. ตรวจ **ราคาและ pricelist deviation** รายบรรทัด ระบบเทียบ `pricelist_price` ที่ snapshot ไว้กับบรรทัด pricelist ที่ **active ปัจจุบัน** (resolve จาก `product_id`, vendor, location และ effective date) ตัวบ่งชี้ deviation highlight บรรทัดที่ราคาปัจจุบันขยับเกิน tolerance ที่ตั้งไว้ (เช่น `±5%`) เมื่อมี deviation Purchaser เลือกได้ว่า (a) ยอมรับราคาที่ snapshot แล้วเดินหน้าต่อ, (b) refresh เป็นราคา pricelist ปัจจุบันก่อนแปลง หรือ (c) ยกประเด็นและส่ง PR กลับไปยังผู้ร้องขอเพื่อทบทวน
5. (ทางเลือก) ปรับ **จำนวนที่จะแปลง** รายบรรทัด ค่าเริ่มต้นคือแปลงเต็มจำนวนที่ยังเปิดอยู่ของบรรทัด (`approved_base_qty` ลบจำนวนที่ถูก bridge แล้วจากการแปลงบางส่วนรอบก่อน) Purchaser อาจแปลงน้อยกว่าจำนวนเปิด คงเหลือไว้สำหรับ PO รอบหน้า — bridge table บันทึกจำนวนที่แปลงจริงต่อ link ของ PO-PR-line
6. สลับไปยังมุมมอง workbench **Convert to PO** workbench รวมบรรทัดที่ติ๊กไว้จาก PR ปัจจุบันและ PR อื่น ๆ ที่ Purchaser เลือก แล้วจัดกลุ่มอัตโนมัติตาม `(vendor_id, currency_id)` แต่ละกลุ่มกลายเป็น draft PO หนึ่งใบ; บรรทัดที่ใช้ vendor และสกุลเงินเดียวกันจะ consolidate ลง PO เดียวกันโดยไม่สนว่ามาจาก PR ฉบับใด preview ของแต่ละกลุ่มแสดง: ชื่อและรหัส vendor, สกุลเงิน, จำนวนบรรทัด, subtotal, total tax, total discount และ grand total ทั้งสกุลเงินที่ทำรายการและสกุลเงินฐาน
7. ตรวจแต่ละกลุ่ม draft PO Purchaser สามารถย้ายบรรทัดออกจากกลุ่ม (เช่น เลื่อนไป PO รอบหลัง), แก้วันส่งฝั่ง PO หรือส่วนลดฝั่ง PO ของบรรทัดได้ในขอบเขตที่ `PR_AUTH_008` และนโยบายโมดูล PO อนุญาต และเพิ่ม note ระดับ PO ได้ บรรทัดที่ vendor หรือ pricelist validation ไม่ผ่านจะถูก flag แดงและไม่อยู่ในการแปลงจนกว่าจะแก้
8. รัน **Convert to PO** ระบบสร้าง `tb_purchase_order` หนึ่งใบต่อหนึ่งกลุ่ม, insert บรรทัด `tb_purchase_order_detail` ที่ตรงกันพร้อม context สินค้า / ราคา / จำนวน / UoM ที่ snapshot แล้ว, snapshot อัตราแลกเปลี่ยนในจังหวะแปลงลงบนบรรทัด PO และเขียน 1 แถวต่อคู่ (บรรทัด PO, บรรทัด PR) ลงใน bridge `tb_purchase_order_detail_tb_purchase_request_detail` พร้อมจำนวนที่แปลง ตาม `PR_POST_007` ถ้าทุกบรรทัดของ PR ต้นทางถูก bridge ครบ (ผลรวมของ quantity ที่ link ใน bridge เท่ากับ `approved_base_qty`) หรือถูก cancel ไปแล้ว `pr_status` จะ flip จาก `approved` เป็น `completed`; บรรทัดที่ยังมีจำนวนเปิดเหลือ จะปล่อย PR ไว้ที่ `approved` เพื่อรอแปลงรอบถัดไป
9. ยืนยันการแปลงใน dialog สรุป (จำนวน PO ที่สร้าง, มูลค่า PO รวมในสกุลเงินฐาน, จำนวน PR ต้นทาง) เมื่อยืนยัน ระบบเขียน audit comment `type = system` ลงในแต่ละ PR ต้นทาง (`PR_POST_008`), ส่ง PO notification ไปยัง contact ของ vendor ที่ระบุ (กรณีเปิดใช้งาน vendor portal integration) และแจ้งผู้ร้องขอว่า PR ของเขาถูก link กับ PO แล้ว
10. Purchaser กลับมาที่คิว **Approved PRs** PR ที่ bridge ครบจะหลุดออกจากคิว; PR ที่ bridge บางส่วนยังอยู่ในคิวโดยจำนวนบรรทัดที่ยังไม่ถูก bridge อัปเดตให้ใหม่ PO ที่สร้างใหม่ปรากฏในโมดูล [[purchase-order]] ให้ Purchaser ติดตามต่อจนถึงการรับของ

## 3. สาขาการตัดสินใจ

- **ถ้า pricelist deviation ของบรรทัดเกิน tolerance** (ราคาปัจจุบันเทียบ `pricelist_price` ที่ snapshot อยู่นอกแถบ `±X%`): Purchaser เห็น flag deviation ในขั้นตอน 4 และเลือกหนึ่งในสามเส้นทาง (a) **Accept snapshot** — เดินหน้าด้วย `pricelist_price` ที่ PR freeze ไว้; PO รับราคาเดียวกัน (b) **Refresh to current** — ดึงราคาปัจจุบันจาก `tb_pricelist_detail` ลงบรรทัด PO; snapshot ของ PR ไม่เปลี่ยน แต่ PO บันทึกราคาใหม่ (c) **Raise concern / send back** — ยกเลิกการแปลงบรรทัดนั้นและส่ง PR กลับไปยังผู้ร้องขอด้วยเส้นทาง send-back มาตรฐาน (PR's `workflow_current_stage` กลับไปที่ create stage ของผู้ร้องขอ, `pr_status` กลับเป็น `draft`, soft budget commitment ถูกปลดจนกว่าจะ submit ใหม่ ตาม `PR_POST_003`) เหตุผลของการ bounce-back ถูกบันทึกใน `tb_purchase_request_comment` เพื่อการตรวจสอบ
- **ถ้าบรรทัดไม่มี vendor allocation** (`vendor_id IS NULL`): บรรทัดนั้นแปลงต่อในรูปปัจจุบันไม่ได้ Purchaser เปิด dialog Allocate Vendor เลือก vendor (เรียงตามการ match pricelist, lead time และประวัติ performance) แล้ว snapshot ของ `vendor_id`, `vendor_name`, `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` และ `pricelist_type` บนบรรทัด PR ถูก update PR ยังคงอยู่ใน `approved`; ไม่ต้องผ่านผู้อนุมัติใหม่ เพราะ vendor allocation เป็นสิทธิ์ของ Purchaser ภายใต้ `PR_AUTH_008`
- **ถ้า Purchaser ต้องการแปลงเพียงบางบรรทัดในรอบนี้ (partial conversion)**: ในขั้นตอน 5 ติ๊กเฉพาะบรรทัด (และจำนวน) ที่จะแปลงรอบนี้ ปล่อยที่เหลือไว้แล้วรัน Convert to PO bridge table บันทึกเฉพาะสิ่งที่แปลงต่อบรรทัด; PR ต้นทางยังคงอยู่ใน `approved` พร้อมบรรทัดที่ยังไม่ถูก bridge ให้เห็นต่อ Purchaser (หรือเพื่อนร่วมทีม) สามารถรันการแปลงรอบสองได้ภายหลัง — รอบสาม สี่ก็ได้ ตราบใดที่ยังมีบรรทัดที่มีจำนวนเปิด `pr_status` flip เป็น `completed` เมื่อจำนวนเปิดสุดท้ายถูก bridge หรือถูก cancel เท่านั้น (`PR_POST_007`)
- **ถ้าต้องเคลียร์กับ vendor** (spec กำกวม, MOQ ขัดแย้ง, lead-time ไม่ทันวันที่ขอ): Purchaser **ไม่** แก้เนื้อหา PR เอง — แต่ trigger เส้นทาง send-back ของฝั่ง PR ซึ่งส่ง PR กลับไปยังผู้ร้องขอที่ `draft` พร้อมเหตุผลของการเคลียร์ ผู้ร้องขอแก้บรรทัด (คำอธิบาย, จำนวน, วันส่งของ หรือไฟล์แนบ) แล้ว submit ใหม่ผ่านห่วงโซ่อนุมัติทั้งหมด Purchaser มารับ PR ใหม่อีกครั้งเมื่อกลับมาที่ `approved`
- **ถ้า Purchaser พยายาม consolidate ข้ามสกุลเงินที่ไม่ตรง** (บรรทัดสองบรรทัดของ vendor เดียวกันแต่หนึ่งใน `THB` และอีกหนึ่งใน `USD`): workbench ปฏิเสธการรวมเป็น draft PO เดียว — consolidation ต้องตรงทั้ง `vendor_id` และ `currency_id` Purchaser จะเห็น draft PO สองใบสำหรับ vendor เดียวกัน หนึ่งใบต่อสกุลเงิน
- **ถ้าอัตราแลกเปลี่ยนเปลี่ยนแปลงตั้งแต่ submit PR** (เช่น submit เมื่อสามสัปดาห์ก่อนที่ `35.50000` วันนี้ `36.20000`): `exchange_rate` ของ **PR** เป็น immutable ตาม `PR_CALC_006` — การ re-approve ไม่ดึงอัตราใหม่ ส่วน **PO** จะ snapshot `exchange_rate` ใหม่ในจังหวะแปลง ทำให้ยอดในสกุลเงินฐานของ PO สะท้อนอัตราในจังหวะที่ผูกพันกับ vendor ดังนั้นยอด `base_total_amount` ฝั่ง PR และยอดในสกุลเงินฐานฝั่ง PO อาจไม่เท่ากัน — เป็นสิ่งที่คาดไว้และบันทึกในหน้ารายละเอียด PR เพื่อ traceability
- **ถ้า PR ต้นทางถูก bridge ครบในรอบแปลงเดียว**: `PR_POST_007` flip `pr_status` จาก `approved` เป็น `completed` ทันที; soft budget commitment แปลงเป็น hard commitment บน PO ใหม่; PR หลุดออกจากคิว Approved PRs และถูกเก็บแบบ read-only เพื่อการตรวจสอบ

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทของ Purchaser ต่อ PR แต่ละฉบับสิ้นสุดที่หนึ่งในสามจุดต่อไปนี้:

- **แปลงครบ (Full conversion)** — ทุกบรรทัดที่อนุมัติถูก bridge ครบในรอบเดียว (หรือหลายรอบ โดยรอบนี้ปิดจำนวนเปิดสุดท้าย) `pr_status` flip จาก `approved` เป็น `completed` (`PR_POST_007`); soft budget commitment แปลงเป็น hard commitment บน PO; ส่งต่อไปยัง **โมดูล PO** ([[purchase-order]]) เพื่อผูกพันกับ vendor, ติดตามถึงการรับของ และ match กับ GRN ([[good-receive-note]]) ผู้ร้องขอเห็น PO ที่ link อยู่ในหน้ารายละเอียด PR เพื่อ traceability
- **แปลงบางส่วน (Partial conversion)** — บางบรรทัด (หรือบางจำนวนของบรรทัด) ถูก bridge ส่วนที่เหลือยังเปิดอยู่ `pr_status` ยังคงเป็น `approved`; bridge table บันทึกเฉพาะ link PR-line → PO-line ที่ถูกสร้างพร้อมจำนวนที่แปลง PR ยังอยู่ในคิว Approved PRs โดยจำนวนบรรทัดที่ยังไม่ถูก bridge ปรากฏให้เห็น เพื่อรอการแปลงรอบถัดไป soft commitment ของส่วนที่ยังเปิดยังคงอยู่
- **Bounce-back ไปยังผู้ร้องขอ** — มีประเด็น vendor หรือ spec ที่ Purchaser แก้ไม่ได้ในระดับของตน Purchaser trigger เส้นทาง send-back มาตรฐาน: `pr_status` กลับเป็น `draft` (`PR_POST_003`), `workflow_current_stage` กลับไปที่ create stage ของผู้ร้องขอ, soft budget commitment ถูกปลด และส่งต่อไปยัง **ผู้ร้องขอ** ที่ [03-user-flow-requestor.th.md](./03-user-flow-requestor.th.md) หัวข้อ 2 ขั้นตอน 2 ผู้ร้องขอแก้ไขและ submit ใหม่; PR เข้าห่วงโซ่อนุมัติอีกครั้งและในที่สุดกลับมาที่คิวของ Purchaser

สถานะเอกสารในการเปลี่ยนสถานะเหล่านี้ถูกบันทึกโดย `enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed, cancelled }` Purchaser เห็นเฉพาะ PR ที่อยู่ใน `approved` (candidate สำหรับแปลง) หรือ `completed` (เก็บไว้ดู read-only) การ void (`pr_status → voided`) สงวนไว้ให้ Finance / system-admin ตาม `PR_AUTH_007` และไม่อยู่ใน flow มาตรฐานของ Purchaser

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.th.md](./03-user-flow.th.md)
- Bridge table: [01-data-model.th.md](./01-data-model.th.md) หัวข้อ 2 — `tb_purchase_order_detail_tb_purchase_request_detail` (many-to-many link บรรทัด PR↔PO รองรับทั้ง consolidation และ partial conversion)
- กฎ cross-module: [02-business-rules.th.md](./02-business-rules.th.md) หัวข้อ 6 — bridge สำหรับการแปลง PR → PO, semantics ของ snapshot vendor / pricelist, การส่งต่อ budget จาก soft เป็น hard commitment
- กฎ authorization: [02-business-rules.th.md](./02-business-rules.th.md) หัวข้อ 4 — `PR_AUTH_008` (`enum_stage_role = purchase` เป็นเจ้าของ vendor allocation และการแปลงเป็น PO)
- กฎ posting: [02-business-rules.th.md](./02-business-rules.th.md) หัวข้อ 5 — `PR_POST_005` (final approve → `approved`), `PR_POST_007` (convert to PO → เขียน bridge + `completed`)
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — แหล่งหลักสำหรับ UX การแปลงเป็น PO, dialog Allocate Vendor และ workbench Convert-to-PO
- `../carmen/docs/purchase-request-management/PR-Overview.md` — ภาพรวมโมดูล, นิยามบทบาท Purchaser / Procurement Officer และจุดเชื่อมต่อกับโมดูล PO
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — product requirements ที่ขับเคลื่อนการ consolidate (vendor + currency) และพฤติกรรม partial conversion
- ไฟล์พี่น้อง: [03-user-flow-approver.th.md](./03-user-flow-approver.th.md) — persona ต้นน้ำ; ผู้อนุมัติ stage สุดท้ายส่งต่อไปยัง Purchaser เมื่อ `pr_status` flip เป็น `approved`
- ไฟล์พี่น้อง: [03-user-flow-requestor.th.md](./03-user-flow-requestor.th.md) — ปลายทางของ bounce-back เมื่อต้องเคลียร์ประเด็น vendor / spec
- ไฟล์พี่น้อง: [index.md](./index.md) หัวข้อ 4 — นิยามมาตรฐานของบทบาท Purchaser
- Cross-link: [[purchase-order]] — โมดูลปลายน้ำที่รับ PO ที่แปลงแล้ว
- Cross-link: [[vendor-pricelist]] — อ้างอิงสำหรับ pricelist deviation และเรียงลำดับใน Allocate Vendor
