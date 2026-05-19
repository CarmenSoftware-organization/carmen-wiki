---
title: ใบเบิกของสโตร์ (Store Requisition) — Business Rules
description: กฎ validation, calculation, authorization, posting และข้ามโมดูลของ store-requisition
published: true
date: 2026-05-19T23:55:00.000Z
tags: store-requisition, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — Business Rules

> **At a Glance**
> **กลุ่มของกฎ:** `SR_VAL_*` validation &nbsp;·&nbsp; `SR_AUTH_*` permission &nbsp;·&nbsp; `SR_CALC_*` calc &nbsp;·&nbsp; `SR_POST_*` posting &nbsp;·&nbsp; `SR_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 60 กฎ
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา — ทุก rule ID ถูกอ้างจากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** หัวข้อ 5.1 (ในที่ที่มี) บรรจุ callout ความไม่ตรงกันระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้รวบรวมกฎทางธุรกิจเชิงปฏิบัติการที่กำกับเอกสาร Store Requisition (SR) ตลอดวงจรชีวิต: input validation ตอน create / edit / submit / approve / issue, ชุดกฎการคำนวณเล็ก ๆ (quantity invariants และการ feed unit cost จากต้นทาง; SR เป็น **เอกสารเชิงปริมาณ** ไม่ใช่เอกสารเชิงราคา — ดู [store-requisition/01-data-model](/th/inventory/store-requisition/01-data-model) § 5 ข้อ 3 และ 4), การกำหนดสิทธิ์ตาม role และสถานะเอกสาร, ผลกระทบของการ posting ในแต่ละ transition ของ `enum_doc_status` และกฎข้ามโมดูลกับ [inventory](/th/inventory/inventory), [costing](/th/inventory/costing), [recipe](/th/inventory/recipe) และ [good-receive-note](/th/inventory/good-receive-note) SR คือ system of record สำหรับ **การเคลื่อนย้ายสต๊อกภายในระหว่างสถานที่**: จนกว่าจะ commit (`in_progress → completed`) ไม่มีการลด inventory ที่ต้นทางและไม่มี expense / inventory entry ที่ปลายทาง; เมื่อ commit แล้ว on-hand ของสถานที่ต้นทางลดลงตาม `issued_qty` ต่อบรรทัด, ปลายทางได้รับปริมาณเดียวกัน (`sr_type = transfer`) หรือดูดต้นทุนเข้า cost-centre ของตน (`sr_type = issue`) และ journal entries ถูกเขียนผ่าน `tb_inventory_transaction` ที่ลิงก์

จุดทางโครงสร้างสองจุดที่กระทบทุกกฎด้านล่างนี้และคุ้มค่าที่จะเน้นไว้ก่อน **ประการแรก** ปริมาณสามค่าบน `tb_store_requisition_detail` — `requested_qty`, `approved_qty`, `issued_qty` — ร่วมกันบรรจุเรื่องราวทั้งหมดข้ามวงจรชีวิต พร้อม invariant เข้มงวด `0 ≤ issued_qty ≤ approved_qty ≤ requested_qty` ถูกบังคับใช้ที่ระดับค่าทุก save และ transition; นี่คือ analogue ระดับบรรทัดของ `received_qty / accepted_qty` ของ GRN **ประการที่สอง** ต่างจาก GRN ที่ `approved` / `rejected` / `committed` เป็นสถานะส่วนหัวแยก SR ยุบทั้งการอนุมัติและ fulfillment ภายใต้สถานะ `in_progress` เดียว — ฟิลด์ `workflow_current_stage` คือสิ่งที่แยก "รอผู้อนุมัติ" กับ "รอ store keeper" ดังนั้นกฎที่อ้าง "ช่วงอนุมัติ" หรือ "ช่วง issue" gate บน `(doc_status = 'in_progress', workflow_current_stage = <approval-stage-slug>)` แทนที่จะอยู่บนสถานะระดับบนเพียงอย่างเดียว

## 2. กฎ Validation

Rule ID ใช้ `SR_VAL_NNN` กฎส่วนหัว (001–005) ทำงานทุก save และตอน submit; กฎบรรทัด (006–010) ทำงานต่อบรรทัดตอน save, submit และทุก action approval / issue; กฎ aggregate / at-commit (011–014) ทำงานเฉพาะที่ transition `in_progress → completed` (posting event ครั้งเดียว)

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | -------- | -------------- | ---------------- |
| `SR_VAL_001` | `tb_store_requisition.sr_no` เป็น non-null และถูกถือ unique เทียบกับ SR ที่ยังไม่ถูก soft-delete (`@@unique([sr_no, deleted_at])`) ต่างจาก `grn_no` ของ GRN ที่ยอม null, SR ต้องการเลขอ้างอิงตั้งแต่ `draft` เป็นต้นไป | Create, save, submit, commit | Reject ด้วย "SR reference number is required and must be unique." |
| `SR_VAL_002` | `tb_store_requisition.from_location_id` และ `to_location_id` ทั้งคู่ non-null ตอน submit, อ้างอิงแถว `tb_location` ที่ยังไม่ถูก soft-delete และ **ต่างกัน** (`from_location_id ≠ to_location_id` — ไม่มี SR จากสถานที่ไปสถานที่ตัวเอง) | Save (warn สำหรับ null), submit (block) | Reject ด้วย "Source and destination locations are required and must differ." |
| `SR_VAL_003` | ความเข้ากันได้ของประเภทการเคลื่อนย้าย ↔ ประเภทปลายทาง: เมื่อ `sr_type = 'issue'`, `tb_location[to_location_id].location_type = 'direct'`; เมื่อ `sr_type = 'transfer'`, `tb_location[to_location_id].location_type = 'inventory'` ต้นทางต้องเป็น `inventory` ทั้งสองกรณี | Save line, submit, commit | Reject ด้วย "Movement type `<sr_type>` requires a `<expected>` destination; selected destination is `<actual>`." Map ไปยังการจับคู่ `enum_location_type` / `enum_sr_type` |
| `SR_VAL_004` | `sr_date` เป็น non-null และไม่อยู่ในอนาคตเกิน tolerance ของ tenant; `expected_date` (ถ้าตั้ง) อยู่ในวันเดียวกันหรือหลัง `sr_date` | Save, submit | Reject ด้วย "Requisition date is required; expected date must be on or after requisition date." |
| `SR_VAL_005` | `tb_store_requisition.requestor_id` และ `department_id` non-null ตอน submit, อ้างอิงผู้ใช้และแผนกที่ active และผู้ขอเป็นสมาชิกของแผนกที่ระบุ (RBAC join) | Submit | Reject ด้วย "Requester and requesting department are required and the requester must belong to that department." |
| `SR_VAL_006` | ทุกแถว `tb_store_requisition_detail` มี `product_id` non-null อ้างอิง `tb_product` ที่ active และยังไม่ถูก soft-delete ซึ่งสถานะอนุญาตให้ issue (ไม่ discontinued / inactive ที่สถานที่ต้นทาง) | Save line, submit | Reject บรรทัดด้วย "Product is required and must be active for issue from the source location." |
| `SR_VAL_007` | triple `(store_requisition_id, product_id, dimension)` unique ข้ามแถว detail ที่ยังไม่ถูก soft-delete บน SR เดียวกัน (ตาม index `SRT1_*`) สินค้าเดียวกันบน SR เดียวกันที่ `dimension` ต่างกัน (split cost-centre allocation) อนุญาตเป็นสองแถว; product+dimension เหมือนกันเป็น duplicate | Save line, submit | Reject บรรทัดด้วย "This product is already on the SR with the same cost-dimension allocation; edit the existing line or use a different dimension to split." |
| `SR_VAL_008` | Quantity invariant ทุกบรรทัด: `requested_qty ≥ 0` เสมอ; เมื่อ submit แล้ว, `0 ≤ approved_qty ≤ requested_qty`; เมื่อ issue แล้ว, `0 ≤ issued_qty ≤ approved_qty` ปริมาณติดลบถูก reject ทุกขั้น; `requested_qty = 0` ถูก reject ตอน submit (บรรทัดศูนย์ไม่ใช่คำขอ) | Save line (warn สำหรับ 0 / null), submit (block), approve, issue | Reject บรรทัดด้วย "Quantities must satisfy `0 ≤ issued_qty ≤ approved_qty ≤ requested_qty`; requested quantity must be greater than zero at submit." |
| `SR_VAL_009` | ความพร้อมที่ต้นทางตอน submit: `requested_qty ≤ tb_inventory_status[from_location_id, product_id].quantity_on_hand` หักการจองจาก SR เปิดอื่น tenant config ควบคุมว่าจะบังคับเป็น hard block หรือ soft warning ("BR-Stock-01" ใน PRD) | Submit, commit | เมื่อ hard: reject บรรทัดด้วย "Requested quantity `<requested_qty>` exceeds available stock `<on_hand − reserved>` at source location `<from_location_name>`." เมื่อ soft: warn และอนุญาต |
| `SR_VAL_010` | Approval invariant: `approved_qty ≤ requested_qty` เป็น cap ของค่า; เพิ่มเติม ผู้อนุมัติต้อง **ไม่** เพิ่ม `approved_qty` เกิน `requested_qty` (อนุญาตเฉพาะตัดลงหรือศูนย์) Rejection ตั้ง `approved_qty = 0` และต้องการ `reject_message` ไม่ว่าง | Approve action | Reject การอนุมัติด้วย "Approved quantity cannot exceed requested quantity; to grant more, the requester must amend and resubmit." Reject การ reject บรรทัดถ้า `reject_message` ว่าง |
| `SR_VAL_011` | ตอน commit SR มีแถว `tb_store_requisition_detail` ที่ไม่ถูก soft-delete อย่างน้อยหนึ่งแถวที่ `approved_qty > 0` เอกสารที่ไม่มีบรรทัดอนุมัติไม่สามารถ commit ได้ | Commit | Reject ด้วย "SR must contain at least one approved line (approved quantity > 0) before it can be committed." |
| `SR_VAL_012` | ตอน commit ทุกบรรทัดที่ `issued_qty > 0` และ `product.product_type = 'inventory'` ต้องมี `inventory_transaction_id` บรรจุค่า และ `tb_inventory_transaction_detail` ที่ลิงก์บรรจุ `lot_no` (สร้างโดยระบบหรือ store-keeper เลือกสำหรับสินค้าที่ควบคุม lot) และ `cost_per_unit` (ดึงจากวิธี costing ของสถานที่ต้นทางตาม `[costing](/th/inventory/costing)`) ข้อมูล lot บังคับสำหรับสินค้าที่ควบคุม lot / เน่าเสีย; `cost_per_unit` บังคับทุกสินค้า inventory | Commit | Reject ด้วย "Issue posting requires lot information for lot-controlled items and a valid unit cost on every issued line; line `<seq>` is missing data on the linked inventory transaction." |
| `SR_VAL_013` | ตอน commit สถานที่ต้นทางมี on-hand เพียงพอครอบคลุมทุก `issued_qty` การตรวจสอบ run ใหม่เทียบกับ `tb_inventory_status` ที่ live ตอน issue (ไม่ใช่กับ snapshot ตอน submit) เพื่อป้องกันการ post negative stock | Commit | Reject ด้วย "Source stock-out at issue: line `<seq>` requires `<issued_qty>` but only `<on_hand>` is available at `<from_location_name>`. Reduce `issued_qty` to the available quantity or cancel the line." |
| `SR_VAL_014` | ตอน commit วันที่ post อยู่ในงวดบัญชีเปิด (ตาราง period ของ `[costing](/th/inventory/costing)` / finance ไม่ถูกปิด) commit ในงวดปิดถูก reject; SR ยังคงอยู่ที่ `in_progress` เพื่อพยายามใหม่หลังเปิดงวดหรือด้วยวันที่ post อื่น | Commit | Reject ด้วย "Cannot commit SR `<sr_no>`: posting date falls in a closed accounting period." |

## 3. กฎการคำนวณ

SR เป็น **เอกสารเชิงปริมาณ** ไม่ใช่เอกสารเชิงราคา ดังนั้น surface การคำนวณจึงเล็ก ปริมาณทั้งหมดถูกเก็บเป็น `Decimal(20, 5)` ที่ระดับแถว; การปัดเศษเพื่อแสดงผลใช้ half-up 3 ทศนิยมสำหรับปริมาณ **ไม่มีคอลัมน์เงินบน `tb_store_requisition` หรือ `tb_store_requisition_detail`** — unit cost และ line total ถูกอ่านจาก inventory transaction ที่ลิงก์ตอนแสดงผล (ดู [store-requisition/01-data-model](/th/inventory/store-requisition/01-data-model) § 5 ข้อ 3 และ 4)

Rule ID ใช้ `SR_CALC_NNN`

| Rule ID | สูตร |
| ------- | ---- |
| `SR_CALC_001` (quantity invariant) | `0 ≤ issued_qty ≤ approved_qty ≤ requested_qty` บนทุกแถว detail ที่ active (`deleted_at IS NULL`) Invariant บังคับใช้ตอนเขียนตาม `SR_VAL_008`; ยังเป็น integrity check ตอนอ่านที่ใช้โดย costing roll-up และ variance dashboards |
| `SR_CALC_002` (variance — requested vs issued) | `variance_qty = requested_qty − issued_qty` ต่อบรรทัด; variance บวกคือ fulfillment ขาด (approver trim, source stock-out หรือ partial issue) variance ไม่ writeback ลงบรรทัด — คำนวณสำหรับ variance dashboard ([inventory](/th/inventory/inventory) / outlet variance reporting) |
| `SR_CALC_003` (variance — approved vs issued) | `fulfilment_gap = approved_qty − issued_qty` ต่อบรรทัด; gap บวกคือ shortfall ตอน issue (store keeper ไม่สามารถปล่อยจำนวนที่อนุมัติเต็ม) นี่คือ metric ที่ store keeper ปิด (fulfillment เต็มเมื่อ `fulfilment_gap = 0`) |
| `SR_CALC_004` (unit cost feed จากต้นทาง) | `unit_cost = tb_inventory_transaction_cost_layer.cost_per_unit` ตอน issue เลือกตามวิธี costing ของสถานที่ต้นทาง (FIFO หรือ moving-average ตาม [costing](/th/inventory/costing)) SR **ไม่** คำนวณหรือเก็บ unit cost เอง — cost เป็นเจ้าของโดยโมดูล costing ฝั่ง inventory-transaction; บรรทัด SR เข้าถึงผ่าน `inventory_transaction_id` |
| `SR_CALC_005` (line total — แสดงผลเท่านั้น) | `line_total = issued_qty × unit_cost` — คำนวณเพื่อแสดงผลใน detail view และสำหรับการ post journal entry ตอน commit แต่ **ไม่ persist บน `tb_store_requisition_detail`** |
| `SR_CALC_006` (header total — แสดงผลเท่านั้น) | `header_total = Σ (issued_qty × unit_cost)` ข้ามบรรทัดที่ issue และ active — คำนวณเพื่อแสดงผลและสำหรับยอด journal-entry แต่ **ไม่ persist บน `tb_store_requisition`** |
| `SR_CALC_007` (โหมดปัดเศษ) | Half-up 3 ทศนิยมสำหรับปริมาณ (เก็บ `Decimal(20, 5)`) สำหรับฟิลด์เงินที่แสดงผลเท่านั้น half-up ถึงความแม่นยำของสกุลเงินของสถานที่ต้นทาง (โดยทั่วไป 2 dp) inventory transaction รับผิดชอบการเก็บค่าเงินที่ปัดเศษแล้ว |

### 3.1 ตัวอย่างการคำนวณ (1 SR, 3 บรรทัด, ผลลัพธ์ผสม)

เอาท์เลต *Main Kitchen* (`tb_location.location_type = 'direct'`) ตั้ง SR กับ *Central Store* (`tb_location.location_type = 'inventory'`); `sr_type = issue` สามบรรทัด

- **บรรทัด 1** (ข้าว): `requested_qty = 25.000`, on-hand ต้นทาง = 100.000
  - ผู้อนุมัติอนุมัติเต็ม: `approved_qty = 25.000`
  - Store keeper issue เต็ม: `issued_qty = 25.000`
  - Cost-layer ต้นทาง (moving-average): `cost_per_unit = ฿42.50` ต่อ kg
  - Line variance: `requested − issued = 0`; fulfilment gap = 0
  - Total ที่แสดง: `25.000 × ฿42.50 = ฿1,062.50`
- **บรรทัด 2** (แป้ง): `requested_qty = 15.000`, on-hand ต้นทาง = 12.000
  - ผู้อนุมัติตัดลงตามความพร้อมต้นทาง: `approved_qty = 12.000`; `approved_message = "trimmed to source on-hand"`
  - Store keeper issue ตามที่อนุมัติ: `issued_qty = 12.000`
  - Cost-layer ต้นทาง (FIFO): `cost_per_unit = ฿28.00` ต่อ kg
  - Line variance: `requested − issued = 3.000` (ขาด 3; เอาท์เลตขอ 15 ได้ 12)
  - Total ที่แสดง: `12.000 × ฿28.00 = ฿336.00`
- **บรรทัด 3** (น้ำตาล): `requested_qty = 10.000`, on-hand ต้นทางตอน submit = 10.000 แต่ตอน issue = 6.000 (SR อื่นใช้ไป 4)
  - ผู้อนุมัติอนุมัติเต็ม: `approved_qty = 10.000`
  - Store keeper เจอ stock-out ตอน issue (`SR_VAL_013`): ปล่อยได้แค่ 6; บันทึก `issued_qty = 6.000`; เขียน system comment "issued 6 of 10; 4 short due to concurrent consumption"
  - Cost-layer ต้นทาง (moving-average): `cost_per_unit = ฿31.50` ต่อ kg
  - Line variance: `requested − issued = 4.000`; fulfilment gap = 4.000
  - Total ที่แสดง: `6.000 × ฿31.50 = ฿189.00`

Roll-up ส่วนหัว (แสดงผลเท่านั้น):
- `Σ line_total = 1,062.50 + 336.00 + 189.00 = ฿1,587.50` — นี่คือต้นทุนที่ย้ายออกจาก inventory ต้นทางและตกที่ค่าใช้จ่าย cost-centre ของ Main Kitchen (`sr_type = issue` ในที่นี้) หรือเข้าบัญชี inventory ของ Main Kitchen (ถ้าเป็น `sr_type = transfer`)
- inventory transaction สามใบถูกเขียน ทั้งหมด stamp `inventory_doc_type = store_requisition`, ทั้งหมดเป็นแถว `outQty` ที่ต้นทาง สำหรับ `sr_type = transfer` (ไม่ใช่กรณีนี้) แถว `inQty` คู่กันสามแถวจะลงที่ปลายทางด้วย

## 4. กฎ Authorization

Rule ID ใช้ `SR_AUTH_NNN` Authorization บังคับโดย RBAC ที่ชั้น API บวกการ gate ขั้น workflow ผ่าน `tb_store_requisition.user_action.execute` ชื่อ role สะท้อนตาราง RBAC ของ carmen/docs (Requester / Approver / Fulfiller / Receiver / Inventory Controller / Finance Manager / System Administrator) Segregation-of-duties บังคับระหว่าง Requester กับ Approver และระหว่าง Approver กับ Fulfiller; กฎ Requester ≠ Approver คือ SoD gate อย่างเป็นทางการ

| Rule ID | ผู้กระทำ | สิทธิ์ | ข้อจำกัด |
| ------- | -------- | ------ | --------- |
| `SR_AUTH_001` | Requester (Outlet Manager) | สร้าง SR (`doc_status = draft`) | Requester ต้องเป็นสมาชิก `department_id`; `from_location_id` และ `to_location_id` ต้องเป็นสถานที่ที่ requester อนุญาตให้ทำธุรกรรมระหว่างกันได้ |
| `SR_AUTH_002` | Requester | แก้ SR, เพิ่ม / แก้ / ลบบรรทัด | ขณะ `doc_status = draft` และยังไม่ submit เท่านั้น เมื่อถึง `in_progress` แล้ว เอกสารไม่อยู่ในมือ requester อีกต่อไป |
| `SR_AUTH_003` | Requester | Submit (`draft → in_progress`) | ผ่าน validation ในส่วนที่ 2 ตั้งแต่ `SR_VAL_001`–`SR_VAL_009` ตอน submit workflow engine จัดเส้นทางเอกสารไปยังขั้นอนุมัติแรกและบรรจุ `user_action.execute` จาก permitted users ของขั้นนั้น |
| `SR_AUTH_004` | Requester | ถอน / ยกเลิก draft ของตน | `draft → cancelled` อนุญาตสำหรับ requester บน draft ของตนพร้อมเหตุผล `in_progress → cancelled` อนุญาตสำหรับ requester เฉพาะเมื่อ workflow ยังอยู่ที่ขั้นอนุมัติแรก (ยังไม่มีผู้อนุมัติกระทำ); เกินจุดนั้น เฉพาะผู้อนุมัติเท่านั้นที่ reject SR ได้ |
| `SR_AUTH_005` | Approver (Department Head) | อนุมัติ / ตัด / reject บรรทัด, ส่งกลับเพื่อแก้ไข | ขณะ `doc_status = in_progress` และ `workflow_current_stage` เป็นขั้นอนุมัติที่ approver อยู่ใน `user_action.execute` เท่านั้น อาจตั้ง `approved_qty ∈ [0, requested_qty]` (ตาม `SR_VAL_010`), ตั้ง `reject_message` บนบรรทัดที่ทำเป็นศูนย์ หรือ `review_message` เพื่อส่งกลับแก้ไข (ส่งเอกสารกลับขั้นก่อนหน้า โดยทั่วไปคือ requester) Approver ต้องไม่ใช่ผู้ใช้คนเดียวกับ requester (`SR_AUTH_011`) |
| `SR_AUTH_006` | Approver | Split & reject (อนุมัติบางส่วนที่ระดับ SR) | บางบรรทัดอนุมัติ บางบรรทัด reject — เกิดในการกระทำ approve เดียวกัน; workflow ดำเนินต่อถ้ามีบรรทัดอย่างน้อยหนึ่งที่ `approved_qty > 0` มิเช่นนั้นเอกสารย้ายไป `cancelled` ผ่านเส้นทาง all-lines-rejected |
| `SR_AUTH_007` | Fulfiller (Store Keeper) | หยิบ, บันทึก `issued_qty`, เลือก lot, commit (`in_progress → completed`) | ขณะ `doc_status = in_progress` และ `workflow_current_stage` เป็นขั้น fulfillment ที่ fulfiller อยู่ใน `user_action.execute` เท่านั้น `issued_qty ≤ approved_qty` ต่อบรรทัด (`SR_VAL_008`) การเลือก lot เขียนลง `tb_inventory_transaction_detail` ที่ลิงก์ ตอน commit cross-module fan-out fire ตามส่วนที่ 5 Fulfiller ต้องไม่ใช่ผู้ใช้คนเดียวกับ approver บน SR เดียวกัน (`SR_AUTH_012`) |
| `SR_AUTH_008` | Receiver (ผู้แทนเอาท์เลตปลายทาง) | ยืนยันการรับจริง, flag ความคลาดเคลื่อน, ปิด | พร้อมใช้เมื่อ SR เป็น `completed` (หรือที่ขั้น destination-acknowledgement workflow ถ้า tenant มีก่อน `completed`) Receiver ไม่เปลี่ยน `doc_status` แต่สามารถเพิ่ม `user` / `system` comments บนส่วนหัว / บรรทัด และยก discrepancy event ที่ escalate ไปยัง Inventory Controller |
| `SR_AUTH_009` | Inventory Controller | Variance review, period-end signoff, void เชิงบริหาร | อ่านได้ทุกสถานะ; อาจ void SR ที่ `draft` หรือ `in_progress` พร้อมเหตุผล (`* → voided`) ด้วยเหตุผล audit (`SR_AUTH_013`) ไม่อาจแก้บรรทัดหรือเปลี่ยนปริมาณโดยตรง; การแก้ไขผ่าน `[inventory-adjustment](/th/inventory/inventory-adjustment)` |
| `SR_AUTH_010` | Finance Manager | ตรวจสอบการ map cost-centre / journal-entry, period close | อ่านได้ทุกสถานะ อาจ reject การ commit ที่ `SR_VAL_014` (block งวดปิด) หรือโต้แย้ง post ภายหลังผ่านเส้นทาง inventory-adjustment Period-end signoff ยืนยันว่า SR `completed` ทั้งหมดในงวดมี journal entries ที่ถูกต้อง |
| `SR_AUTH_011` | Segregation of duties — **Requester ≠ Approver** | ผู้ใช้ที่อนุมัติ SR (`approved_by_id` บนบรรทัดใด ๆ ตอน approve action) ต้อง **ไม่** เป็นผู้ใช้เดียวกับ `tb_store_requisition.requestor_id` | บังคับใช้ตอน approve action ระบบ reject action ด้วย `"You raised this requisition; another user must approve it."`; ไม่เขียน `approved_qty`, ไม่เดิน workflow |
| `SR_AUTH_012` | Segregation of duties — **Approver ≠ Fulfiller** | ผู้ใช้ที่ commit SR (`last_action_by_id` บน transition `in_progress → completed`) ต้อง **ไม่** เป็นผู้ใช้เดียวกับ `approved_by_id` ของบรรทัดใด | บังคับใช้ตอน commit ระบบ reject ด้วย `"You approved a line on this requisition; another user must issue the goods."` tenant config อาจผ่อนคลายสำหรับ SR มูลค่าต่ำกว่า threshold |
| `SR_AUTH_013` | Inventory Controller / System Administrator | Void SR (`draft → voided` หรือ `in_progress → voided`) | อนุญาตเฉพาะก่อน commit SR ที่ `completed` ไม่สามารถ void ได้ — การแก้ไขหลัง commit ผ่าน `[inventory-adjustment](/th/inventory/inventory-adjustment)` `voided` เป็นจุดสิ้นสุด; `cancelled` ก็เป็นจุดสิ้นสุดแต่สงวนสำหรับเส้นทาง retraction ที่ผู้ใช้เริ่ม (requester ถอนหรือ approver full-reject) |
| `SR_AUTH_014` | Authorization derive จาก workflow | Action ที่ gate ตามขั้น | ชุดผู้ใช้ใน `tb_store_requisition.user_action.execute` ที่ `workflow_current_stage` ปัจจุบันคือชุดเดียวที่อนุญาตให้เดินเอกสารต่อ; การพยายาม action อื่นถูก reject ด้วย `"You are not assigned to act on this requisition at the current stage."` |

## 5. กฎ Posting

ค่าสถานะคือสมาชิก literal ของ `enum_doc_status` ที่ใช้ร่วมตามที่ระบุใน [store-requisition/01-data-model](/th/inventory/store-requisition/01-data-model) § 4: **`draft`**, **`in_progress`**, **`completed`**, **`cancelled`**, **`voided`** วงจรชีวิตเต็มจึงเป็น `draft → in_progress → completed` พร้อม `cancelled` และ `voided` เป็นเส้นทางยกเลิกที่จุดสิ้นสุดสองทางจากสถานะใด ๆ ก่อน commit Posting event ครั้งเดียวคือ transition `in_progress → completed`; ไม่มีอะไร post ที่ `draft` หรือขณะที่ workflow ยังอยู่ในขั้นอนุมัติ / pre-fulfilment ของ `in_progress` ไม่มีค่า `submitted`, `approved`, `partially_approved`, `fulfilled` หรือ `rejected` ที่ระดับ Prisma — สิ่งเหล่านั้นคือ label ของขั้น workflow ภายใต้ `in_progress` ไม่ใช่สถานะส่วนหัว (โมเดล 6 สถานะแบบเก่าของ carmen/docs ต่างออกไป — ดู [store-requisition/01-data-model](/th/inventory/store-requisition/01-data-model) § 5 ข้อ 1)

Rule ID ใช้ `SR_POST_NNN`

| Rule ID | Transition / Event | ผลกระทบ |
| ------- | ------------------ | ------- |
| `SR_POST_001` | Create (→ `draft`) | Insert `tb_store_requisition` ด้วย `doc_status = draft`, `doc_version = 0`, `sr_no` กำหนดตามนโยบายเลขของ tenant Append `workflow_history`: `{ stage: 'draft', action: 'created', by, at }` ไม่กระทบ inventory, GL, reservation |
| `SR_POST_002` | Submit (`draft → in_progress`) | ตั้ง `doc_status = in_progress`, `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user` Initialize `workflow_current_stage` เป็นขั้นอนุมัติแรก; บรรจุ `user_action.execute` จากขั้นนั้น Append `workflow_history` Append `history` ต่อบรรทัด: `{ seq: N, name: '<stage>', status: 'submit', by_id, by_name, at_date }` อาจยก soft reservation เทียบ on-hand ต้นทาง (configurable ของ tenant); ยังไม่ hard inventory write |
| `SR_POST_003` | Approve บรรทัด (ภายใน `in_progress`) | ใน approve action ต่อบรรทัด: ตั้ง `approved_qty`, `approved_by_id`, `approved_by_name`, `approved_date_at`, `approved_message` Append `history` ต่อบรรทัด เมื่อบรรทัดทั้งหมดบนขั้นปัจจุบันถูก action แล้ว เดิน `workflow_current_stage` ไปขั้นถัดไป (ระดับอนุมัติถัดไป หรือขั้น fulfilment ถ้าอนุมัติครบ); refresh `user_action.execute` `doc_status` ส่วนหัวยังคงเป็น `in_progress` ตลอด |
| `SR_POST_004` | Reject บรรทัด / send back (ภายใน `in_progress`) | Reject ต่อบรรทัด: ตั้ง `approved_qty = 0`, `reject_by_id`, `reject_by_name`, `reject_date_at`, `reject_message` (บังคับ) Send-back: ตั้ง `review_by_id`, `review_by_name`, `review_date_at`, `review_message`; workflow ส่ง SR กลับไปขั้นก่อนหน้า (โดยทั่วไปคือ requester) และเอกสารยังคงเป็น `in_progress` ถ้า **ทุก** บรรทัด active ถูก reject (`Σ approved_qty = 0` ข้ามบรรทัด active) เอกสารย้าย `in_progress → cancelled` อัตโนมัติ (`SR_POST_009`) |
| `SR_POST_005` | Commit (`in_progress → completed`) — **posting event** | ตั้ง `doc_status = completed`, `last_action = approved` (หรือ `submitted` ตาม workflow), `last_action_at_date = now()` Append `workflow_history` จากนั้น cross-module fan-out fire เชิง atomic: ดู `SR_POST_006`–`SR_POST_008` |
| `SR_POST_006` | Commit — ฝั่ง inventory (cross-ref [inventory](/th/inventory/inventory)) | สำหรับแต่ละบรรทัดที่ `issued_qty > 0` และสินค้าประเภท inventory, insert แถว `tb_inventory_transaction` (`inventory_doc_type = store_requisition`) บวก children `tb_inventory_transaction_detail` ที่บรรจุ `lot_no`, `expiry_date`, `cost_per_unit` Stamp id ที่ insert บน `tb_store_requisition_detail.inventory_transaction_id` **สำหรับ `sr_type = issue`**: เขียนแถว OUT เดียวที่ `from_location_id`; on-hand ต้นทางที่ `(from_location_id, product_id)` ลดลงตาม `issued_qty` (และ `issued_base_qty` ถ้า UoM ต่างกัน) **สำหรับ `sr_type = transfer`**: เขียน OUT ที่ต้นทาง + IN ที่ปลายทางคู่กัน; on-hand ต้นทางลด on-hand ปลายทางเพิ่มในปริมาณเดียวกัน Cost-layer rows ที่ต้นทางถูก consume ตามวิธี costing ของสถานที่ต้นทาง ([costing](/th/inventory/costing) FIFO consume layer เก่าสุดก่อน; moving-average ทิ้ง per-unit cost ไม่เปลี่ยนแต่ลดปริมาณ) การเลือก lot ถูกรักษาบน transaction detail สำหรับ traceability |
| `SR_POST_007` | Commit — ฝั่ง GL (cross-ref Finance) | Post journal entries ผ่าน inventory transactions ที่ลิงก์ **สำหรับ `sr_type = issue`**: **Dr** บัญชีค่าใช้จ่ายการบริโภคของปลายทางบน cost-centre (ตาม `tb_store_requisition.dimension` / `to_location.cost_centre`) ที่ `Σ issued_qty × cost_per_unit`; **Cr** บัญชี inventory ของสถานที่ต้นทางในจำนวนเท่ากัน **สำหรับ `sr_type = transfer`**: **Dr** บัญชี inventory ของสถานที่ปลายทาง; **Cr** บัญชี inventory ของสถานที่ต้นทาง ทั้งสองขา stamp ด้วย `sr_no` ของ SR สำหรับ traceability Entries ต้องบาลานซ์ (`Σ Dr = Σ Cr`); การ post ที่ไม่บาลานซ์ถูก block โดยโมดูล finance |
| `SR_POST_008` | Commit — feed variance / vendor performance | `requested_qty − issued_qty` และ `approved_qty − issued_qty` ต่อบรรทัดถูก emit เป็น variance events ที่ feed outlet variance reporting และ supply-planning โมดูล SR เองไม่เก็บ variance — surface จาก join ข้ามสามคอลัมน์บนแถว detail |
| `SR_POST_009` | Cancel (`draft → cancelled` หรือ `in_progress → cancelled`) | ตั้ง `doc_status = cancelled`, `last_action_at_date = now()` Trigger โดย: (a) requester ถอน draft ของตน / SR ของตนที่ขั้นอนุมัติแรก (`SR_AUTH_004`); (b) อัตโนมัติเมื่อบรรทัดทั้งหมดถูก reject โดยผู้อนุมัติ (`SR_POST_004` tail); (c) "reject SR" โดย approver ที่ได้รับอนุญาตที่ขั้นอนุมัติใด ๆ ไม่กระทบ inventory หรือ GL (SR ไม่เคย post) บรรทัดและลายเซ็นต่อบรรทัดยังอ่านได้สำหรับ audit จุดสิ้นสุด |
| `SR_POST_010` | Void (`draft → voided` หรือ `in_progress → voided`) | ตั้ง `doc_status = voided`, `last_action_at_date = now()` เส้นทางเชิงบริหาร — Inventory Controller หรือ System Administrator เท่านั้น (`SR_AUTH_013`) อนุญาตเฉพาะก่อน commit ไม่กระทบ inventory หรือ GL บรรทัดยังอ่านได้สำหรับ audit จุดสิ้นสุด **การ void SR ที่ `completed` ไม่อนุญาต**; การแก้ไขหลัง commit ใช้ `[inventory-adjustment](/th/inventory/inventory-adjustment)` |
| `SR_POST_011` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `draft` (ตามจิตวิญญาณของ `SR_AUTH_013`) แถวยังคงในฐานข้อมูล; index `@@unique([sr_no, deleted_at])` ให้ SR ใหม่ reuse `sr_no` เดียวกันได้ |
| `SR_POST_012` | Short fulfillment ตอน stock-out ที่ issue | เมื่อ `SR_VAL_013` ล้มเหลวเพราะ on-hand live ตอน issue น้อยกว่า `approved_qty` fulfiller อาจ (a) ลด `issued_qty` เป็น `min(approved_qty, on_hand)`, ทิ้ง system comment ต่อบรรทัด และ commit แบบบางส่วน — ทิ้ง `fulfilment_gap = approved_qty − issued_qty > 0` ที่บันทึกกับ SR ที่ปิด; หรือ (b) ยกเลิกบรรทัด (`approved_qty → 0` ไม่อนุญาตหลังอนุมัติ ดังนั้นบรรทัดอยู่กับปริมาณที่อนุมัติแต่ `issued_qty = 0` และ system comment "could not fulfil — source stock-out") SR ยังย้ายไป `completed` พร้อม partial fulfillment ที่บันทึกไว้ |
| `SR_POST_013` | Receiver flag ความคลาดเคลื่อน | หลัง commit Receiver ปลายทางอาจ flag discrepancy ("received less than issued" หรือ "wrong lot"); flag เขียน system comment บน SR แต่ **ไม่** ย้ายสถานะ การ resolution ผ่าน `[inventory-adjustment](/th/inventory/inventory-adjustment)` ระหว่างสองสถานที่; SR เองยังคงเป็น `completed` |

State diagram (Prisma-canonical):

```
[*] → draft → in_progress → completed
        ↓        ↓
     cancelled / voided                (completed เป็นจุดสิ้นสุด ต้องผ่านเส้นทาง inventory-adjustment)
```

`completed`, `cancelled` และ `voided` เป็นจุดสิ้นสุด `draft` ยอมรับ soft-delete

### 5.1 วงจรชีวิตสถานะ — การ Map ระหว่าง Live UI กับ BRD

`enum_doc_status` ของ Prisma ที่ระบุข้างบนคือสิ่งที่ live UI ใช้ BRD (`BR-store-requisitions v1.5.0`) และ `SR-User-Experience.md` อธิบายวงจรชีวิตหกสถานะ ตารางด้านล่าง map ทุกสถานะที่สังเกตได้ใน live UI ไปยังคู่ใน BRD เพื่อให้ผู้ทดสอบและนักพัฒนาสามารถ reconcile ทั้งสองได้โดยไม่กำกวม Source: `Test_case/System_Process/tx-03-sr.md` (capture date 2026-04-27)

> Diff legend: ✅ match · 🟡 renamed · 🔵 BRD only

| Live UI status | BRD equivalent | Diff | หมายเหตุ |
|---|---|---|---|
| `draft` | `Draft` | ✅ match | สถานะเริ่มต้นที่แก้ไขได้; requester ป้อนข้อมูลบรรทัด |
| `in_progress` | `Submitted`, `UnderReview`, `Approved`, `PartiallyApproved`, `InProcess`, `Fulfilled` | 🟡 renamed | โมเดล BRD 6 สถานะยุบเป็นสถานะ Prisma เดียว; sub-stage จริงติดตามผ่าน `workflow_current_stage` Stage flow ตาม `BR-SR-014`: Draft → Submit → Approve → Issue → Complete |
| `completed` | `Completed` / `Fulfilled` | 🟡 renamed | Posting event ครั้งเดียว (`in_progress → completed`) On-hand ต้นทางลด; cost-layer consume; inventory transactions เขียน |
| `cancelled` | `Rejected` / `Reject` | 🟡 renamed | Trigger โดย requester ถอน, approver full-rejection หรือเส้นทาง `Σ approved_qty = 0` อัตโนมัติ |
| `voided` | `Voided` / `Void` | 🟡 renamed | เส้นทางเชิงบริหาร; Inventory Controller หรือ Sysadmin เท่านั้น; ก่อน commit เท่านั้น |
| — | `PartiallyApproved` | 🔵 BRD only | ไม่ใช่สถานะ Prisma แยก; แทนด้วยผลการอนุมัติต่อบรรทัดที่ผสมขณะ `doc_status = in_progress` |

> ⚠️ **ความไม่ตรงกัน — ลักษณะ 3 variant ไม่สะท้อนใน `enum_doc_status`:** Live UI รองรับ destination variant สามแบบ (INV → INV / INV → DIR / INV → CONS) ที่ให้ผล GL ต่างกัน แต่ทั้งสามใช้เส้นสถานะ `draft → in_progress → completed` เหมือนกัน enum `sr_type` (`issue` / `transfer`) แยก variant สองแบบใน live (DIR และ CONS ทั้งคู่เป็น `sr_type = issue`; INV → INV เป็น `sr_type = transfer`) BRD `BR-store-requisitions v1.5.0` และ `Test_case/System_Process/tx-03-sr.md` อธิบายสาม variant; ระบบ live ยุบ DIR และ CONS ภายใต้ค่า `sr_type = issue` เดียวโดยแยกด้วย `tb_location.location_type` ของปลายทางเท่านั้น Source: `Test_case/System_Process/tx-03-sr.md` (capture date 2026-04-27)

> ⚠️ **ความไม่ตรงกัน — view Stock Transfer vs transaction code TRF แยก:** BRD `BR-period-end v2.0.0` ระบุ `TRF` เป็น transaction code คู่กันกับ `SR` ใน Stage 1 ของ period-close validation gate การ implement (`BR-stock-transfers.md`) ยืนยันว่า Stock Transfers **ไม่ใช่** เอนทิตีแยก — เป็น SR ที่มีปลายทาง INVENTORY (`sr_type = transfer`) สำหรับ period-close Stage 1 validation, SR records ที่มี INV → INV destinations satisfy ทั้ง bucket `SR` และ `TRF` หน้า Stock Transfer เป็น view กรองอ่านอย่างเดียวของ SR records ไม่ใช่เอกสารแยก Source: `Test_case/System_Process/tx-03-sr.md` (capture date 2026-04-27)

> ℹ️ **หมายเหตุ — Auto-complete ของ Variant A:** สำหรับ `sr_type = transfer` (INV → INV) ขั้น Issue และ Complete ถือเป็นขั้นเดียวกัน — auto-complete โดยไม่มีขั้นยืนยัน receiver แยก สำหรับ Variant B และ C (`sr_type = issue`) Fulfiller ระบุปิดเอกสารหลัง issue อย่างชัดแจ้ง

## 6. กฎข้ามโมดูล

Rule ID ใช้ `SR_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | ------------------ | -- |
| `SR_XMOD_001` | [inventory](/th/inventory/inventory) | On-hand inventory ลดที่ต้นทาง **เฉพาะตอน SR commit** (`SR_POST_006`) — ไม่ใช่ตอน submit ไม่ใช่ตอน approve การลดผ่าน insert ลง `tb_inventory_transaction` / `tb_inventory_transaction_detail` เข้าถึงจากฝั่ง SR ผ่าน `tb_store_requisition_detail.inventory_transaction_id` สำหรับ `sr_type = transfer` on-hand ปลายทางเพิ่มใน atomic transaction เดียวกัน; สำหรับ `sr_type = issue` ไม่มีการเพิ่ม on-hand ปลายทาง (มูลค่าลงเป็นค่าใช้จ่ายการบริโภค ไม่ใช่สต๊อกที่ถือ) |
| `SR_XMOD_002` | [inventory](/th/inventory/inventory) | เลข lot, วันหมดอายุ และปริมาณต่อ lot สำหรับบรรทัดที่ issue อยู่บน `tb_inventory_transaction_detail` (และ `tb_inventory_transaction_cost_layer.lot_no`) **ไม่ใช่** บนบรรทัด SR บรรทัด SR เข้าถึงข้อมูล lot ผ่านลิงก์ `inventory_transaction_id` สำหรับสินค้าที่ควบคุม lot fulfiller เลือก lot ที่จะปล่อยก่อน commit; การเลือกถูกรักษาบน transaction detail เพื่อ traceability เรื่อง recall / expiry / lot-cost ครบ (PRD `BR-Lot-01`) |
| `SR_XMOD_003` | [inventory](/th/inventory/inventory) | ค่า `enum_inventory_doc_type` ที่ stamp บน inventory transaction ที่ลิงก์คือ `store_requisition`; query inventory ปลายน้ำที่ filter ตามประเภทเอกสารดึง movements ที่ขับโดย SR ผ่าน stamp นี้ stamp เดียวกันคือสิ่งที่ `[inventory-adjustment](/th/inventory/inventory-adjustment)` อ่านตอน reverse error หลัง commit |
| `SR_XMOD_004` | [costing](/th/inventory/costing) | Valuation ตอน commit ตามวิธี costing ของ **สถานที่ต้นทาง** (FIFO หรือ moving-average ตาม config ต่อ-สถานที่ของ tenant) — ไม่ใช่ของปลายทาง `SR_CALC_004` อ่าน `cost_per_unit` จากตาราง cost-layer ของต้นทางตอน issue FIFO consumption เลือก layer ที่ active เก่าสุด; moving-average ใช้ weighted-average cost ปัจจุบันของสถานที่ โมดูล costing เป็นเจ้าของการคำนวณ; โมดูล SR รับผิดชอบเฉพาะการ trigger การ consume |
| `SR_XMOD_005` | [costing](/th/inventory/costing) | ที่ปลายทาง value-receipt accounting ขึ้นกับ `sr_type`: `transfer` ลงในบัญชี inventory ปลายทางที่ `cost_per_unit` เดียวกัน (cost ย้ายระหว่างบัญชี inventory แบบครบ); `issue` ลงเป็น expense บน cost-centre ปลายทางที่ `cost_per_unit` เดียวกัน (cost ย้ายจาก inventory ไป expense) Cost-per-unit ที่ปลายทางหลัง `transfer` เข้าสู่ cost layers ของปลายทางตามวิธี costing ของตน — โดยทั่วไป append เป็น FIFO layer ใหม่หรือถูก absorb เข้า moving-average |
| `SR_XMOD_006` | [recipe](/th/inventory/recipe) | ความต้องการ recipe จาก event production / banquet อาจสร้าง SR อัตโนมัติสำหรับการเบิกวัตถุดิบ: โมดูล recipe คำนวณปริมาณวัตถุดิบที่ BoM ของเอาท์เลตปลายทางและ post SR ใน `draft` ให้ requester ของเอาท์เลต review และ submit SR หลังจากนั้นเดินตาม flow ปกติ (`SR_POST_001` ต่อไป) SR ที่กำเนิดจาก recipe มี back-reference ใน `info.recipe_id` สำหรับ traceability |
| `SR_XMOD_007` | [good-receive-note](/th/inventory/good-receive-note) | การโอนระหว่างคลังอาจจับคู่ SR-OUT ที่คลังต้นทางกับ GRN-IN ที่คลังปลายทาง — SR บันทึก issue จากมุมมองต้นทาง GRN บันทึกการรับจากมุมมองปลายทาง ทั้งคู่อ้างอิงตระกูล `tb_inventory_transaction` เดียวกันแต่จากฝั่งตรงข้าม; การ reconcile ระหว่างทั้งสองเป็นความรับผิดชอบของ finance / inventory-controller `transfer` SR ขั้นตอนเดียว (`sr_type = transfer`) บันทึกทั้งสองขาบนเอกสารเดียวและไม่ต้องการ GRN คู่; รูปแบบ paired-GRN สงวนสำหรับกรณีที่ปลายทางต้องการยืนยันการรับด้วยเอกสารของตน (โดยทั่วไปเมื่อปลายทางเป็นนิติบุคคลต่างกันหรือ remote facility) |
| `SR_XMOD_008` | Approval workflow | Approval routing — จำนวนขั้น role / threshold ที่แต่ละขั้น กฎ delegation — เป็นเจ้าของโดย `tb_workflow` (อ้างจากส่วนหัว SR ผ่าน `workflow_id` ด้วย Prisma `@relation` ที่ระบุชัด) โมดูล SR รับผิดชอบการปรึกษา workflow ที่แต่ละ transition และบรรจุ `user_action.execute` จากขั้นปัจจุบัน; ไม่รับผิดชอบกฎ routing เอง การ delegate การอนุมัติ (ผู้ใช้มอบสิทธิ์อนุมัติให้ผู้อื่น) จัดการที่ชั้น workflow |
| `SR_XMOD_009` | [inventory-adjustment](/th/inventory/inventory-adjustment) | การแก้ไขหลัง commit — เลือก lot ผิด, นับ issue ผิด, ปลายทางรับขาด — ไหลผ่าน inventory-adjustment ไม่ใช่ผ่านการแก้ SR Adjustment มี back-reference ไปยัง `tb_store_requisition.id` ต้นกำเนิดสำหรับ audit SR เองยังคงเป็น `completed` |
| `SR_XMOD_010` | Vendor performance / outlet variance | Feedback variance (`SR_POST_008`) feed รายงาน outlet-level food-cost variance และ supply-discipline การขอเกินเรื้อรัง (gap `requested_qty − approved_qty` ใหญ่), shortfall เรื้อรังตอน issue (`approved_qty − issued_qty`) และรูปแบบการขอตามฤดูกาล surface จาก join ข้ามสามคอลัมน์ปริมาณ ชุด metric เป็นเจ้าของโดยชั้น reporting; โมดูล SR รับผิดชอบเฉพาะการ persist คอลัมน์ที่ feed มัน |

## 7. แหล่งอ้างอิง

- `../carmen/docs/store-requisitions/SR-Technical-Specification.md` — Functional requirements `SR_CRT_001`–`SR_CRT_010` (creation), `SR_APR_001`–`SR_APR_008` (approval), `SR_FUL_001`–`SR_FUL_008` (fulfilment), `SR_RPT_001`–`SR_RPT_005` (reporting) Validation rules feed `SR_VAL_*`; การคำนวณ cost feed `SR_CALC_*` (พร้อมข้อสังเกตว่า SR เป็นเอกสารเชิงปริมาณ — ดู Section 3 intro) หมายเหตุ: enum `RequisitionItem.approvalStatus` และฟิลด์ `Requisition.totalAmount` ของ Tech Spec ต่างจาก Prisma; กฎข้างบนใช้ schema canonical
- `../carmen/docs/store-requisitions/SR-Overview.md` — §Business Rules (Creation Rules, Approval Rules, Movement Rules, Financial Rules) map ข้างบนไปยัง `SR_VAL_*`, `SR_AUTH_*`, `SR_POST_*`, `SR_XMOD_*` หมายเหตุ: ส่วนหัว 5 สถานะของ Overview (`Draft / In Process / Complete / Reject / Void`) ยุบเป็น Prisma 5-state `enum_doc_status` (`draft / in_progress / completed / cancelled / voided`)
- `../carmen/docs/store-requisitions/SR-User-Experience.md` — User journeys (Create / Approve / Process), state diagram (6 สถานะ legacy — ไม่ canonical), คำอธิบาย persona Logic branch ของการอนุมัติและรูปแบบ partial-approval / send-back feed `SR_AUTH_005`–`SR_AUTH_006` และ `SR_POST_003`–`SR_POST_004`
- `../carmen/docs/store-requisitions/Store Requisitions.md` — Use cases UC-64 (Approve), UC-65 (Deny), UC-66 (Modify), UC-67 (Monitor), UC-68 (Create and Manage), UC-69 (Approve and Record Stock as Issued) — รวมกันนิยามรูปแบบ interaction ของผู้อนุมัติและ store-keeper ที่ใช้ในตาราง authorization และ posting ข้างบน
- Sibling: `en/store-requisition/01-data-model.md` — โมเดล Prisma canonical, ค่า enum (โดยเฉพาะ `enum_doc_status` 5 ค่าที่ใช้ร่วม และ `enum_sr_type` 2 ค่า) และ catalogue จุดที่ต่างที่ Section 1, Section 3 และ Section 6 พึ่งพา
- Backend rule implementation (เมื่อเพิ่ม): `../carmen-turborepo-backend-v2/apps/` — โมดูลบริการ store-requisition คือ implementation hook สำหรับกฎเหล่านี้ (status guards, three-quantity invariant check, source-availability check, segregation-of-duties guard, inventory-transaction creation, journal-entry posting)
