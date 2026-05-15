---
title: ใบขอซื้อ — เส้นทางผู้ใช้งาน — ผู้อนุมัติ (Approver)
description: เส้นทางผู้ใช้งานของ Approver (Department Head, Budget Controller, Finance) ในโมดูล purchase-request
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, user-flow, approver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — เส้นทางผู้ใช้งาน — ผู้อนุมัติ (Approver)

## 1. บทบาทในโมดูลนี้

**ผู้อนุมัติ (Approver)** เป็น persona แบบรวมที่ครอบคลุมผู้ตัดสินใจสามตำแหน่งในห่วงโซ่อนุมัติของ PR — **Department Head** (Stage 1 approve), **Budget Controller** (Stage 2) และ **Finance Officer / Manager** (Stage 3) — ซึ่งทั้งสามใช้หน้าจอ review-and-decide เดียวกัน แต่ตรวจประเด็นต่างกัน (ความสมเหตุสมผลของแผนก, ความพร้อมของงบประมาณ และความถูกต้องของผลกระทบทางการเงินตามลำดับ) ในแต่ละ stage ผู้อนุมัติเปิด PR ที่ submit แล้ว ตรวจส่วนหัวและบรรทัด ปรับ `approved_qty` รายบรรทัดได้ถ้าจำเป็น แล้วเลือกการกระทำหนึ่งในสี่: **Approve** (เลื่อนไป stage ถัดไป), **Send Back** (ส่งกลับไปยังผู้ร้องขอที่สถานะ `draft`), **Reject** (ยุติเอกสาร) หรือ **Split-Reject** (อนุมัติ / ปฏิเสธรายบรรทัด — บรรทัดที่อนุมัติเดินต่อ ส่วนบรรทัดที่ถูกปฏิเสธคงอยู่ในเอกสารโดยมี `current_stage_status = rejected`) สถานะเอกสารยังคงเป็น `in_progress` ตลอดทุก stage อนุมัติระหว่างทาง — `pr_status` จะเปลี่ยนเป็น `approved` ก็ต่อเมื่อ stage อนุมัติ **สุดท้าย** ผ่าน (ดู `PR_POST_004` / `PR_POST_005` ใน [02-business-rules.th.md](./02-business-rules.th.md)) ผู้อนุมัติไม่มีบทบาทใน vendor allocation หรือการแปลงเป็น PO — สิทธิ์นั้นเป็นของ Procurement Manager / Purchaser ภายใต้ `enum_stage_role = purchase` (`PR_AUTH_008`)

## 2. จุดเริ่มต้นและเส้นทางหลัก

**จุดเริ่มต้น:** Notification ทาง email / in-app "Purchase Request [PR-ID] Awaiting Your Approval" → กด deep link ซึ่งพาเข้าหน้ารายละเอียด PR โดยตรง ทางเลือก: Sidebar → โมดูล **Purchase Request** → คิว **My Approvals** (กรอง PR ที่ผู้ใช้ปัจจุบันอยู่ใน `tb_purchase_request.user_action.execute[]` ของ stage ปัจจุบัน)

**เส้นทางหลัก (happy path) — มุมมอง stage เดียว:**

1. จากคิว **My Approvals** (หรือ link ใน notification) เลือก PR ที่รอตัดสิน คิวแสดง `pr_no`, ผู้ร้องขอ, แผนก, grand total ทั้งสกุลเงินที่ทำรายการและสกุลเงินฐาน, stage ปัจจุบันใน workflow และเวลาที่รอ คลิกเข้าไปเพื่อเปิดหน้ารายละเอียด PR ในโหมด read-mostly (ส่วนหัวและบรรทัดแก้ไม่ได้สำหรับผู้อนุมัติ ยกเว้น `approved_qty` และ flag การตัดสินรายบรรทัด)
2. ตรวจ **ส่วนหัว**: PR type (`General Purchase` / `Market List` / `Asset`), ผู้ร้องขอและแผนก, `pr_date`, วันส่งของที่ต้องการ, สกุลเงินและ exchange rate, `workflow_name`, คำอธิบาย / เหตุผล และไฟล์แนบ ใช้ panel **Activity Log** อ่านความเห็นก่อนหน้า (note ของผู้ร้องขอ, ความเห็นของผู้อนุมัติ stage ก่อน, system event)
3. เปิดแท็บ **Items** แล้วไล่ดูทุกบรรทัด สำหรับแต่ละบรรทัด ตรวจสินค้า, store location, `requested_qty`, หน่วยนับ, ราคาประมาณการต่อหน่วย, จำนวน FOC, ส่วนลด, การคิดภาษี, วันส่งของบรรทัดและ note ของบรรทัด ผู้อนุมัติจะเห็น context ของสต๊อกด้วย (on-hand, on-order, reorder level, average monthly usage, last purchase price) ดึงสด ๆ จาก [[inventory]] และ context ของ vendor / pricelist ที่ดึงจาก [[vendor-pricelist]]
4. เปิด panel **Budget Impact** ระบบแสดง availability ต่อแผนก / cost-centre / budget category ของงวดที่เกี่ยวข้อง: งบทั้งหมด, soft commitment ปัจจุบันจาก PR ฉบับนี้และ PR / PO เปิดอื่น ๆ, hard commitment และ `availableBudget` ที่ได้ Budget Controller (Stage 2) ใส่ใจ panel นี้มากที่สุด แต่ผู้อนุมัติทุกคนเห็นข้อมูลเดียวกัน
5. ถ้าจำเป็นต้องลดจำนวน (เช่น งบตึง, จำนวนที่ขอเกินนโยบาย, หรือต้องการ fulfil บางส่วน) แก้ **`approved_qty`** บนบรรทัดที่ต้องการ ตาม `PR_VAL_013` ค่าใหม่ต้อง `> 0` และ `≤ requested_qty` หลังแปลง UoM แล้ว และต้องบันทึก `approved_unit_id` กับ `approved_unit_conversion_factor` คู่กัน ยอดรวมของส่วนหัว (`base_sub_total_amount`, `base_total_amount` ฯลฯ) recompute เมื่อบันทึก
6. ตัดสิน **disposition รายบรรทัด** ถ้าต้องทำ split-reject: ทำเครื่องหมายแต่ละบรรทัดเป็น **accept** (ค่าเริ่มต้น) หรือ **reject** บรรทัดที่ปฏิเสธต้องระบุเหตุผล บรรทัดที่ accept ที่เหลือเดินตาม workflow ต่อ ส่วนบรรทัดที่ reject คงอยู่ในเอกสารโดยมี `current_stage_status = rejected` และจะไม่ไปถึงการแปลงเป็น PO (`PR_AUTH_003`)
7. เลือก **header-level action** จากแถบ action: **Approve**, **Send Back**, **Reject** หรือ (เมื่อมีบรรทัดอย่างน้อยหนึ่งถูก mark reject และอื่น ๆ accept) ระบบจะถือว่า action Approve คือการ commit **Split-Reject** สำหรับ Send Back และ Reject ระบบบังคับให้กรอกเหตุผล; สำหรับ Approve ความเห็นเป็น optional
8. ยืนยัน action ใน dialog ระบบรัน authorization check (`PR_AUTH_002` — ผู้ใช้ปัจจุบันต้องอยู่ใน `user_action.execute[]` ของ stage ปัจจุบัน; `PR_VAL_013` กับทุก `approved_qty` ที่แก้)
9. กรณี **Approve** ที่ stage ระหว่างทาง: ระบบ apply `PR_POST_004` — append `workflow_history`, update `workflow_previous_stage` / `workflow_current_stage` / `workflow_next_stage`, ตั้ง `last_action = approved` และ `last_action_by_*` เป็นผู้ใช้ปัจจุบัน, recompute `user_action.execute[]` ของ stage ถัดไปจาก threshold และ routing rule ใน `tb_workflow` แล้วส่ง notification ให้ผู้อนุมัติ stage ถัดไป `pr_status` ยังคงเป็น `in_progress` soft budget commitment ยังอยู่
10. กรณี **Approve** ที่ stage อนุมัติ **สุดท้าย**: `PR_POST_005` flip `pr_status` จาก `in_progress` เป็น `approved`, workflow stepper แสดงว่า chain ครบ, notification ถูกส่งไปยังผู้ร้องขอ ("Approved") และคิวของ Purchaser แล้ว PR พร้อมสำหรับการแปลงเป็น PO soft commitment ยังคงอยู่จนกว่า Purchaser จะสร้าง PO ซึ่งจะแปลงเป็น hard commitment ในจังหวะนั้น (ดู [[purchase-order]])
11. ผู้อนุมัติกลับไปที่คิว **My Approvals** ซึ่ง PR ที่เพิ่งตัดสินถูกตัดออก action และความเห็นที่กรอกถูกบันทึกใน `tb_purchase_request_comment` log แบบ immutable (`PR_POST_008`)

## 3. สาขาการตัดสินใจ

- **ถ้าผู้อนุมัติเลือก Send Back** แทน Approve: dialog บังคับให้กรอกเหตุผล เมื่อยืนยัน ระบบ apply `PR_POST_003` แล้วเลื่อน `workflow_current_stage` ย้อนกลับหนึ่งก้าว เนื่องจาก Stage 1 เป็น stage create ของผู้ร้องขอ การ send-back จาก Stage 1 จึงเป็นการส่ง PR กลับไปยัง `draft` ให้ผู้ร้องขอแก้ไขและ submit ใหม่ พร้อมปลด soft budget commitment การ send-back จาก Stage 2 หรือ Stage 3 อาจส่ง PR กลับไปยัง stage อนุมัติก่อนหน้า หรือกลับไปถึงผู้ร้องขอเลย ขึ้นกับการตั้งค่า workflow notification ยิงไปยังผู้ใช้ใน stage ใหม่ (ก่อนหน้า) บทบาทของผู้อนุมัติจบที่นี่
- **ถ้าผู้อนุมัติเลือก Reject ที่ระดับ header** (PR ไม่มีเหตุผลรองรับ, ซ้ำ หรือไม่ยอมรับด้วยเหตุอื่น): dialog บังคับให้กรอกเหตุผล เมื่อยืนยัน `PR_AUTH_004` + `PR_POST_006` มีผล: `pr_status` เปลี่ยนเป็น `cancelled` (terminal), soft budget commitment ถูกปลด, `workflow_history` ถูก append และ comment `type = system` บันทึกการ reject ผู้ร้องขอจะได้รับ notification และ chain จบ — ไม่มี stage ถัดไปรัน
- **ถ้าผู้อนุมัติต้องการ accept บางบรรทัดและ reject บางบรรทัด (Split-Reject)**: แก้ disposition รายบรรทัดในขั้นตอน 6 ข้างต้น mark บรรทัดที่เกี่ยวเป็น reject พร้อมเหตุผล แล้ว commit Approve ที่ header ระบบบันทึก `current_stage_status = rejected` ในแต่ละบรรทัดที่ปฏิเสธ (`PR_AUTH_003`) และเลื่อน PR ไป stage ถัดไป โดยมีเพียงบรรทัดที่ accept ที่นับรวมในงบประมาณและยอดรวมของ stage ถัดไป บรรทัดที่ปฏิเสธยังมองเห็นได้บนเอกสารเพื่อการตรวจสอบ และไม่ไปแปลงเป็น PO
- **ถ้าผู้อนุมัติปรับ `approved_qty` ลง**: ยอดรวมของส่วนหัว recompute, `base_total_amount` ใหม่คือสิ่งที่ stage ถัดไปและการเช็คงบประมาณเห็น และ soft budget commitment ถูก rebalance ถ้ายอดใหม่ข้าม threshold ที่ตั้งไว้ใน `tb_workflow` routing ของ stage *ถัดไป* อาจเปลี่ยน (เช่น PR ยอดเล็กอาจข้าม Stage 4 ตาม `PR_AUTH_005`)
- **ถ้า `base_total_amount` ของ PR เกิน threshold ที่ตั้งไว้สำหรับการ escalate**: ตาม `PR_AUTH_005` ระบบอาจแทรก stage เพิ่มหรือเส้นทาง escalate ไปยัง **Procurement Manager** ผู้อนุมัติยังทำ stage ของตนตามปกติ; logic threshold รันอัตโนมัติในจังหวะเปลี่ยน stage แล้ว reroute notification ถัดไป ผู้อนุมัติไม่เห็น threshold breach เป็น error — workflow engine จัดการให้
- **ถ้าผู้อนุมัติไม่อยู่ชั่วคราว** และมอบหมาย stage ของตนไว้: ตาม `PR_AUTH_006` ผู้ที่ได้รับมอบหมายได้สิทธิ์ approve / send-back / reject / split-reject เหมือนเดิมในช่วงที่มอบหมาย `last_action_by_id` สะท้อน delegate ในขณะที่ audit comment เก็บแหล่งของการมอบหมาย จากมุมมองของ delegate UI flow เหมือนหัวข้อ 2 ทุกประการ
- **ถ้าผู้อนุมัติพยายาม act บน PR ที่ไม่ได้รับสิทธิ์** (ไม่อยู่ใน `user_action.execute[]` ของ stage ปัจจุบัน หรือ PR เลย stage ไปแล้ว): ปุ่ม action ถูก disable และมีข้อความ inline อธิบาย `PR_AUTH_002` บังคับใช้ในฝั่ง server เช่นกัน

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทของผู้อนุมัติสิ้นสุดในจังหวะที่ commit การตัดสินระดับ header ในขั้นตอน 8 ของหัวข้อ 2 ปลายทางของเอกสารหลังจากนั้นขึ้นกับการตัดสินที่เลือก:

- **Approve stage ระหว่างทาง** (Stage 1 หรือ Stage 2 หรือ Stage 3 เมื่อยังมี Stage 4): `pr_status` ยังคงเป็น `in_progress`; `workflow_current_stage` เลื่อนไป; ส่งต่อไปยัง **ผู้อนุมัติ stage ถัดไป** (Budget Controller, Finance หรือ Procurement Manager ตามลำดับ) soft budget commitment ยังอยู่
- **Approve stage สุดท้าย** (stage `approve` สุดท้ายผ่าน ก่อน stage `purchase`): `pr_status` เปลี่ยนเป็น `approved` (`PR_POST_005`); ส่งต่อไปยังคิวของ **Purchaser / Procurement Manager** เพื่อทำ vendor allocation และแปลงเป็น PO PR คงอยู่ในสถานะ `approved` จนกว่าทุกบรรทัดจะถูกแปลงไปยัง PO ครบหรือถูกยกเลิก ซึ่งตอนนั้น `pr_status` จะเปลี่ยนเป็น `completed` (`PR_POST_007`) soft commitment คงอยู่จนกว่า PO ถูกสร้างซึ่งแปลงเป็น hard commitment
- **Send Back** (stage ใดก็ตาม): `pr_status` ยังคงเป็น `in_progress` แต่ `workflow_current_stage` เลื่อนย้อนหนึ่งก้าว; ถ้าก้าวนั้นเป็น create stage ของผู้ร้องขอ เอกสารจะกลับสู่ `draft` และ **ผู้ร้องขอ** มารับช่วงต่อที่ [03-user-flow-requestor.th.md](./03-user-flow-requestor.th.md) หัวข้อ 2 ขั้นตอน 2 soft budget commitment ถูกปลดจนกว่าจะ submit ใหม่
- **Header Reject** (stage ใดก็ตาม): `pr_status` เปลี่ยนเป็น `cancelled` (terminal, `PR_POST_006`); soft budget commitment ถูกปลด; **Auditor** ตรวจสอบย้อนหลังแต่ไม่มี user action เพิ่มเติม ผู้ร้องขอเห็นการยกเลิกใน dashboard **My PRs**
- **Escalate ด้วย threshold**: `pr_status` ยังคงเป็น `in_progress`; workflow engine แทรก (หรือ re-route ไปยัง) stage เพิ่มที่เป็นของ **Procurement Manager** ผู้อนุมัติคนปัจจุบันได้ออกจากเส้นทางไปแล้ว; Procurement Manager รับช่วงต่อจากคิว My Approvals ของตน โดยใช้ flow เดียวกับหัวข้อ 2

สถานะเอกสารในทุกการเปลี่ยนสถานะถูกบันทึกโดย `enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed, cancelled }` และ timeline ของ workflow ใน `workflow_history` การ void (`pr_status → voided`) สงวนไว้ให้ Finance หรือ system-admin ตาม `PR_AUTH_007` และไม่อยู่ใน flow มาตรฐานของผู้อนุมัติ

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.th.md](./03-user-flow.th.md)
- กฎ authorization: [02-business-rules.th.md](./02-business-rules.th.md) หัวข้อ 4 — `PR_AUTH_001`–`PR_AUTH_008`, ห่วงโซ่ stage, การ delegate, การ route ด้วย threshold
- กฎ posting: [02-business-rules.th.md](./02-business-rules.th.md) หัวข้อ 5 — `PR_POST_003` (send-back), `PR_POST_004` (intermediate approve), `PR_POST_005` (final approve), `PR_POST_006` (reject / void / cancel)
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — แหล่งหลักสำหรับ sequence ของกระบวนการอนุมัติ, UI flow ของผู้อนุมัติ และตารางสิทธิ์รายบทบาทต่อ stage
- `../carmen/docs/purchase-request-management/PR-Overview.md` — ภาพรวมโมดูล, นิยามบทบาทผู้อนุมัติ (Department Head, Budget Controller, Finance) และจุดเชื่อมต่อ
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — product requirements ที่ขับเคลื่อนห่วงโซ่อนุมัติหลาย stage และการ route ด้วย threshold
- ไฟล์พี่น้อง: [01-data-model.th.md](./01-data-model.th.md) — `tb_purchase_request.workflow_current_stage`, `stages_status`, `user_action`, `workflow_history`, `enum_purchase_request_doc_status`
- ไฟล์พี่น้อง: [03-user-flow-requestor.th.md](./03-user-flow-requestor.th.md) — persona ต้นน้ำ; รับ PR ที่ถูกส่งกลับด้วย Send Back
- ไฟล์พี่น้อง: [index.md](./index.md) หัวข้อ 4 — นิยามมาตรฐานของบทบาทผู้อนุมัติและห่วงโซ่ stage
