---
title: ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ผู้รับสินค้า (Receiver)
description: เส้นทางของผู้รับสินค้าในโมดูล purchase-order — รับสินค้าจริง ออก GRN อ้างอิง PO และขับเคลื่อน transition สถานะการรับสินค้า
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ผู้รับสินค้า (Receiver)

## 1. บทบาทในโมดูลนี้

persona **ผู้รับสินค้า (Receiver)** ครอบคลุมทั้ง **Receiver / Store Keeper** ที่จุดรับและ **Inventory Manager** ที่กำกับดูแลการปิดรับสินค้าของสถานที่ ทั้งสองคนเป็นเจ้าของขั้นตอนการยอมรับทางกายภาพในห่วงโซ่ procure-to-pay: Store Keeper ตรวจรับสินค้าที่ผู้ขายส่งเทียบกับ PO ออก **Good Receive Note** (GRN) ทีละบรรทัด และบันทึก `received_qty` และ `accepted_qty` บนแต่ละบรรทัดของ PO; Inventory Manager กำกับการ post นั้นและปิด PO เมื่อการรับสมบูรณ์หรือยอมรับเป็นยอดสุดท้าย สถานะ PO ตอนเข้าสู่เส้นทางนี้คือ `sent` (หรือ `partial` สำหรับการส่งครั้งถัดไป) การ post GRN เองดำเนินการในโมดูลปลายน้ำ `[[good-receive-note]]` — หน้านี้อธิบายเฉพาะ **ผลกระทบฝั่ง PO**: การ post GRN ของ Receiver flip `tb_purchase_order.po_status` จาก `sent → partial` (`PO_POST_006`) หรือ `sent → completed` / `partial → completed` (`PO_POST_007`) อย่างไร Inventory Manager ปิด PO ที่อยู่ใน `partial` พร้อมเขียนยอดที่เหลือไปที่ `cancelled_qty` (`PO_POST_011`) อย่างไร และตัวนับบนบรรทัด PO (`received_qty`, `cancelled_qty`) เคลื่อนเทียบกับ `order_qty` อย่างไร inventory on-hand เพิ่มโดยโมดูล GRN ไม่ใช่โดย PO การแยกหน้าที่ (segregation of duties) ถูกบังคับโดย `PO_AUTH_010` — ผู้ใช้ที่สร้างหรือส่ง PO ห้ามเป็นคนเดียวกับผู้ที่ post GRN เทียบกับ PO นั้น

## 2. จุดเริ่มต้นและเส้นทางหลัก

**จุดเริ่มต้น:** มีสองเส้นทางที่เทียบเท่าเข้าสู่การ post GRN:

- **จากโมดูล PO** — เปิด PO ที่ `po_status ∈ {sent, partial}` และคลิก **Receive** บน header ของ PO ซึ่ง deep-link เข้าสู่โมดูล GRN พร้อมเลือก PO ไว้ล่วงหน้า
- **จากโมดูล GRN โดยตรง** — เริ่ม GRN ใหม่ เลือกผู้ขาย แล้วเลือก PO จากรายการ PO ที่เปิดอยู่ของผู้ขาย / สถานที่จัดส่งนั้น

ทั้งสองเส้นทางเข้าสู่หน้าจอ posting เดียวกัน; ผลกระทบฝั่ง PO ด้านล่างเหมือนกัน

**เส้นทางหลัก (8 ขั้นตอน):**

1. **เปิด PO** ที่จุดรับเทียบกับสินค้าที่ส่งมาจริง หน้าจอแสดง `order_qty` ของแต่ละบรรทัด, `received_qty` และ `cancelled_qty` สะสม และยอดคงเหลือ (`order_qty − received_qty − cancelled_qty`) สิทธิ์ตรวจสอบภายใต้ `PO_AUTH_008` (Inventory Manager / Receiver ดำเนินการได้เมื่อ `po_status ∈ {sent, partial}`) และ `PO_AUTH_010` (ผู้ post GRN ต้องไม่ใช่ buyer / ผู้ส่ง PO)
2. **ตรวจสอบสินค้าที่ส่งจริงเทียบกับ PO** — match delivery note / packing list กับบรรทัด PO นับลังกล่อง และระบุการส่งขาด ส่งเกิน ของผิด หรือปัญหาคุณภาพก่อนเปิด GRN
3. **เริ่ม GRN ใหม่** ที่อ้างอิง PO header ของ GRN inherit `vendor_id`, `currency_id` และสถานที่จัดส่งจาก PO; แถว detail ของ GRN ถูก pre-populate จาก `tb_purchase_order_detail` พร้อม `pending_qty` เป็นจำนวนเริ่มต้นที่แก้ไขได้
4. **ป้อน `received_qty` ในแต่ละบรรทัด** — จำนวนที่ส่งมาจริงในหน่วยตาม PO อาจเท่ากับ น้อยกว่า หรือ (ภายใต้นโยบายส่งเกิน) มากกว่ายอดคงเหลือก็ได้
5. **ป้อน `accepted_qty` ในแต่ละบรรทัด** — จำนวนที่ผ่านการตรวจสอบคุณภาพ / สเปคและยอมรับเข้าสต๊อก `accepted_qty ≤ received_qty`; ส่วนต่าง (`received_qty − accepted_qty`) คือผลต่างจากการปฏิเสธคุณภาพที่ยังคงค้างกับผู้ขายสำหรับการคืนของ / credit note
6. **ตรวจสอบยอดรวมและความไม่ตรงกัน** — หน้าจอ GRN แสดงสรุปผลต่าง (ขาด เกิน คุณภาพปฏิเสธ) และ preview สถานะของบรรทัด PO ที่จะเกิด (บรรทัดนี้จะปิดหรือยังคงเปิด?)
7. **Post GRN** เมื่อ post โมดูล GRN commit transaction: เขียนแถว detail ของ GRN, เพิ่ม `tb_purchase_order_detail.received_qty` ตามจำนวนของบรรทัด GRN, update bridge ฝั่ง PR `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` ตามสัดส่วน และเพิ่ม inventory on-hand ตาม `accepted_qty` (จัดการภายในโมดูล GRN / inventory ไม่ใช่โดย PO)
8. **สถานะ PO update** ถูกคำนวณรายบรรทัดและ apply กับ header:
   - ถ้ามีบรรทัด PO อย่างน้อยหนึ่งบรรทัดที่ยังมี `received_qty < order_qty − cancelled_qty`, `po_status` ถูกตั้งเป็น `partial` (`PO_POST_006`) PO ยังคงเปิดสำหรับการ post GRN ต่อ
   - ถ้า **ทุก** บรรทัด PO ที่ active เป็นไปตาม `received_qty + cancelled_qty ≥ order_qty`, `po_status` ถูกตั้งเป็น `completed` (`PO_POST_007`) PO ถูกปิดตามปกติ; ไม่รับ GRN เพิ่มเติม

## 3. สาขาการตัดสินใจ

- **ส่งขาด** (`received_qty < pending_balance`): post GRN ตามที่ส่งจริง PO เปลี่ยนเป็น `partial` (หรือยังคงเป็น `partial`) ภายใต้ `PO_POST_006`; ยอดที่ยังไม่ได้ส่งคงเป็น pending quantity บนบรรทัดที่ได้รับผลกระทบ พร้อมรองรับการ post GRN ครั้งถัดไป แจ้ง Purchaser ผ่าน activity log เพื่อตามผู้ขายเรื่องยอดคงเหลือ
- **ส่งเกิน** (`received_qty > pending_balance`): โมดูล GRN ตรวจกับ tolerance การส่งเกินของ tenant ถ้ายอมรับ (อยู่ใน tolerance หรือมี override ชัดเจน), GRN post จำนวนที่ส่งเกิน, `tb_purchase_order_detail.received_qty` ขึ้นเหนือ `order_qty − cancelled_qty` และ PO เปลี่ยนเป็น `completed` (`PO_POST_007`) ถ้าปฏิเสธ (เกิน tolerance), Receiver จำกัด `received_qty` ที่ pending balance และปฏิเสธส่วนเกินที่จุดรับ — ไม่มี record ระบบสำหรับส่วนเกินที่ถูกปฏิเสธ; Purchaser บันทึกข้อพิพาทฝั่งผู้ขายบน PO
- **ปัญหาคุณภาพ** (`accepted_qty < received_qty`): post GRN พร้อมทั้งสองค่า pending balance ของบรรทัดลดลงตาม `received_qty` แต่ inventory on-hand เพิ่มเฉพาะตาม `accepted_qty`; ส่วนต่าง (`received_qty − accepted_qty`) คือยอดคืน / credit note ที่ติดตามบน GRN PO ไม่แก้ตัวเองอัตโนมัติ — เส้นทางการแก้ไขคือ amendment, return หรือ credit note ที่ริเริ่มโดย Purchaser
- **ของผิด** (สินค้าที่ส่งไม่ตรงกับสินค้าใน PO): **ห้าม post GRN** ปฏิเสธการรับที่จุดรับและ escalate ให้ Purchaser ผู้บันทึก error ฝั่งผู้ขายใน `tb_purchase_order_comment` PO ยังคงเป็น `sent` (หรือสถานะก่อนหน้า) โดยจำนวนไม่เปลี่ยน
- **GRN partial ตอนนี้ ยอดที่เหลือทีหลัง**: post GRN ตามของที่มาวันนี้; `po_status` เปลี่ยนเป็น `partial` (`PO_POST_006`) และยอดเปิดถูกยกไป เมื่อการส่งครั้งต่อไปมาถึง ทำขั้นตอน 1–7 ซ้ำ; PO อาจคงเป็น `partial` หรือก้าวสู่ `completed` เมื่อยอดสุดท้ายเคลียร์ (`PO_POST_007`)
- **ปิด PO โดยตัดยอดที่เหลือทิ้ง** (เฉพาะ Inventory Manager): เมื่อผู้ขายไม่สามารถส่งยอดที่ค้างได้ Inventory Manager ปิด PO ภายใต้ `PO_AUTH_008` / `PO_POST_011` สำหรับแต่ละบรรทัดที่ยังค้าง application เขียนยอดที่เหลือลงใน `cancelled_qty` ให้ `received_qty + cancelled_qty = order_qty`; `po_status` เปลี่ยนเป็น `closed` (terminal) ต้องระบุเหตุผลและบันทึกใน `tb_purchase_order_comment`

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทของ Receiver บน PO แต่ละฉบับสิ้นสุดที่ **การ post GRN** ตั้งแต่จุดนั้น สถานะเอกสารใน Carmen จะเป็นหนึ่งใน:

- `partial` — มีบรรทัด PO อย่างน้อยหนึ่งบรรทัดที่ยังมียอดเปิด; Receiver อาจกลับเข้าสู่เส้นทางนี้อีกเมื่อการส่งครั้งถัดไปมาถึง
- `completed` — ทุกบรรทัดถูกรับเต็มแล้ว; PO อยู่ที่สถานะปลายทางของการรับและกลายเป็น read-only สำหรับวัตถุประสงค์ inventory ตำแหน่ง matched-but-unbilled ถูกส่งต่อให้ **Finance** เพื่อทำ three-way match (PO ↔ GRN ↔ invoice) เมื่อใบแจ้งหนี้ของผู้ขายมาถึง; AP liability ถูก post ภายใต้ `PO_POST_008`
- `closed` — **Inventory Manager** ปิด PO ที่เป็น `partial` โดยเขียนยอดที่เหลือไปที่ `cancelled_qty` ภายใต้ `PO_POST_011`; การปิด-out ถูก review โดย Finance สำหรับ GRN ที่ post ไปแล้วต่อบรรทัดที่ปิด

ทั้งสามกรณี persona ถัดไปคือ **Finance** สำหรับการ match ใบแจ้งหนี้ (และสำหรับ PO ที่ closed คือการกระทบยอดการปิด) PO เองไม่ถูกเปลี่ยนสถานะจาก three-way match — ผลลัพธ์ของ match อยู่บน record ใบแจ้งหนี้ที่เชื่อมโยงและการ post AP; PO คงสถานะการรับสินค้าที่ไปถึง (`partial`, `completed` หรือ `closed`) ดูไฟล์ persona Finance สำหรับฝั่งรับของการส่งต่อใบแจ้งหนี้

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.md](./03-user-flow.md) — global state machine ของ PO และตาราง handoff ข้าม persona; แถว `sent → partial → completed` และแถว `partial → closed` คือพื้นที่ของ persona นี้
- ไฟล์พี่น้อง: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ภายในต้นน้ำที่ส่ง PO และได้รับการแจ้งเตือนเรื่องความไม่ตรงกันที่จุดรับเพื่อทำ amendment / return / credit note ติดตามผล
- ไฟล์พี่น้อง: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md) — ถือสิทธิ์ override การปิด / void และ review การตัดสินใจ `partial → closed` ร่วมกับ Inventory Manager
- ไฟล์พี่น้อง: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — บุคคลภายนอกที่ persona นี้รับสินค้าจริงที่จุดรับ
- ไฟล์พี่น้อง: [03-user-flow-finance.md](./03-user-flow-finance.md) — persona ปลายน้ำที่รับช่วงตำแหน่ง matched-but-unbilled ไปทำ three-way match หลัง post GRN
- โมดูลที่เกี่ยวข้อง: [[good-receive-note]] — โมดูลปลายน้ำที่ออกและ post GRN จริง; หน้านี้อธิบายเฉพาะผลกระทบฝั่ง PO
- โมดูลที่เกี่ยวข้อง: [[inventory]] — การเพิ่ม on-hand จาก `accepted_qty` เป็นของโมดูล inventory เมื่อ post GRN; PO contribute เฉพาะ on-order pipeline quantity (`order_qty − received_qty − cancelled_qty`) ตาม `PO_XMOD_008`
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) — `PO_POST_006`, `PO_POST_007`, `PO_POST_011`, `PO_AUTH_008` และ `PO_AUTH_010` สำหรับ transition และ authorization ฝั่งการรับสินค้าที่อ้างถึงข้างต้น
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่งหลักจาก carmen/docs สำหรับการวิเคราะห์ทางธุรกิจของโมดูล PO การ integrate GRN และ transition สถานะการรับสินค้า
