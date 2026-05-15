---
title: ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ผู้ขาย (Vendor)
description: เส้นทางของผู้ขายในโมดูล purchase-order — บุคคลภายนอก (ไม่มี login เข้าระบบ); รับ PO ตอบรับ ส่งของ และออกใบแจ้งหนี้
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ผู้ขาย (Vendor)

## 1. บทบาทในโมดูลนี้

**ผู้ขาย (Vendor)** เป็น **บุคคลภายนอกที่ไม่มี login เข้าระบบ Carmen** ผู้ขายรับ PO ที่ถูกส่งมา ตอบรับการสั่งซื้อ ส่งของตามที่ตกลง และออกใบแจ้งหนี้สำหรับการทำ three-way match — แต่ผลกระทบทางระบบทุกครั้งของ action เหล่านี้ถูกบันทึกโดย persona ภายในแทนผู้ขาย เมื่อ PO ถูกส่งหลังการอนุมัติขั้นสุดท้าย สถานะระบบจะเปลี่ยนเป็น `sent` (`PO_POST_004`); หลังจากนั้นการตอบรับของผู้ขายจะถูกบันทึกแบบ manual โดย **เจ้าหน้าที่จัดซื้อ (Purchaser)** ใน `tb_purchase_order_comment` (หรือถ้ามี vendor portal ตั้งไว้ จะถูกเขียนผ่าน callback ของ portal โดยตรง), การส่งของจริงไม่มีผลกระทบทางระบบทันที, การ post GRN ของ **Receiver** จะ flip `po_status` ไปเป็น `partial` หรือ `completed` ผ่าน `PO_POST_006` / `PO_POST_007`, และใบแจ้งหนี้ของผู้ขายถูกบันทึกและ three-way-match โดย persona **Finance** ผู้ขายไม่มีสิทธิ์ดำเนินการ `po_status` โดยตรง — action ของผู้ขายขับเคลื่อนสถานะผ่าน persona ภายในที่บันทึกแทนเท่านั้น

## 2. จุดเริ่มต้นและเส้นทางหลัก

**จุดเริ่มต้น:** ผู้ขายรับ PO ที่ถูกส่งผ่าน channel ที่ tenant ตั้งไว้ — email PDF, EDI feed หรือ link ของ vendor portal การส่งจะเขียน `tb_purchase_order.email` และ `approval_date` และ PO อยู่ที่ `po_status = sent`

**เส้นทางหลัก (เชิงแนวคิด — ผลกระทบทางระบบเกิดเฉพาะเมื่อ persona ภายในบันทึก):**

1. **ตอบรับการได้รับ PO** ผู้ขายยืนยันการรับเงื่อนไข (ราคา จำนวน วันส่ง เงื่อนไขการชำระเงิน) **ผลกระทบทางระบบ:** Purchaser บันทึกการตอบรับใน `tb_purchase_order_comment` พร้อมวันที่ยืนยันและเลขอ้างอิง; ถ้ามี vendor portal callback ของ portal จะเขียน comment เดียวกันโดยอัตโนมัติ `po_status` ยังคงเป็น `sent`
2. **เตรียมและจัดส่งสินค้าตามวันส่งที่ตกลง** ผู้ขายจัดเตรียม stock เก็บของ บรรจุ และส่งสินค้าพร้อม delivery note / packing list ที่อ้างถึง `po_no` **ผลกระทบทางระบบ:** ไม่มี — การเคลื่อนย้ายทางกายภาพไม่สะท้อนใน Carmen จนกว่า Receiver จะเปิดรับที่ dock
3. **ส่งสินค้าให้ที่จุดรับ** logistics partner ของผู้ขายส่งของตาม PO และจุดส่งที่ตกลง **ผลกระทบทางระบบ:** ไม่มีโดยตรง — persona **Receiver** สแกน/นับและออก GRN ในโมดูลปลายน้ำ [[good-receive-note]] ซึ่งเป็นสิ่งที่ทำให้ `po_status` เปลี่ยน (`sent → partial` หรือ `sent → completed`)
4. **ออกใบแจ้งหนี้** ผู้ขายส่ง AP invoice (กระดาษ PDF หรือ EDI) อ้างถึง `po_no` และจำนวนที่ส่งแล้ว **ผลกระทบทางระบบ:** persona **Finance** เก็บใบแจ้งหนี้ รัน three-way match (PO ↔ GRN ↔ invoice) และ post AP liability เมื่อ match สำเร็จ; PO เองไม่ถูก update สถานะจากการรับใบแจ้งหนี้ — three-way match ถูกติดตามบน record ใบแจ้งหนี้ที่เชื่อมโยง

## 3. สาขาการตัดสินใจ

- **ถ้าผู้ขายปฏิเสธ PO หลังการส่ง** (ราคาไม่ตกลง, ของหมด, lead-time ไม่ทัน): ผู้ขายแจ้งการปฏิเสธผ่าน channel เดิม **ผลกระทบทางระบบ:** Purchaser บันทึกการปฏิเสธใน `tb_purchase_order_comment` และ re-route ไปยังการแก้ไข (ภายใต้ข้อจำกัด post-`sent` ของ `PO_VAL_016`) หรือ escalate ให้ **Procurement Manager** เพื่อ void จาก `sent` ตาม `PO_AUTH_007` / `PO_POST_010` สถานะปลายทางของ PO คือ `voided`
- **ถ้าผู้ขายส่งบางส่วน** (ส่งเพียงบางจำนวนของที่สั่ง ยอดที่เหลือจะตามมา): ผู้ขายส่งเท่าที่มีพร้อม delivery note ระบุว่าเป็น partial **ผลกระทบทางระบบ:** **Receiver** post GRN แบบ partial — `received_qty < order_qty − cancelled_qty` บนบรรทัดที่ได้รับผลกระทบ — ทำให้ `po_status` เปลี่ยนเป็น `partial` (`PO_POST_006`) การส่งครั้งต่อ ๆ ไปถูกบันทึกผ่าน GRN เพิ่มเติมจนเคลียร์ยอดคงเหลือ (`partial → completed`, `PO_POST_007`) หรือถูกตัดทิ้งเป็น `cancelled_qty` โดย **Procurement Manager** / **Inventory Manager** (`partial → closed`, `PO_POST_011`)
- **ถ้าผู้ขายส่งของผิด เกินจำนวน หรือคุณภาพไม่ได้มาตรฐาน**: ความไม่ตรงกันของผู้ขายถูกตรวจพบที่จุดรับ **ผลกระทบทางระบบ:** **Receiver** บันทึกความไม่ตรงกันบน GRN (จำนวนผันแปร เหตุผล) และ **Purchaser** ได้รับการแจ้งเพื่อเริ่มเส้นทาง return / replacement / credit note กับผู้ขายภายใต้ amendment loop PO ไม่แก้ตัวเองอัตโนมัติ — การแก้ไขถูกบันทึกใน `tb_purchase_order_comment` และยอดที่ตกลงตัดทิ้งจะไปอยู่ที่ `cancelled_qty` บนบรรทัดที่ได้รับผลกระทบ

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทของผู้ขายต่อ PO แต่ละฉบับสิ้นสุดที่ **การออกใบแจ้งหนี้** ตั้งแต่จุดนั้น สถานะเอกสารใน Carmen จะเป็นหนึ่งใน:

- `sent` — PO ถูกส่งแล้วแต่ยังไม่มี GRN post (ผู้ขายยังไม่ส่ง หรืออยู่ระหว่างขนส่ง)
- `partial` — Receiver post GRN อย่างน้อยหนึ่งครั้งแล้วแต่ PO ยังมียอดเปิดในบรรทัดอย่างน้อยหนึ่งบรรทัด
- `completed` — Receiver เคลียร์ทุกบรรทัดผ่าน GRN; PO ถึงสถานะปลายทางของการรับสินค้าแล้ว
- `voided` — PO ถูก void หลังการส่ง (ผู้ขายปฏิเสธ หรือการแก้ไขเชิงเนื้อหาบังคับให้ออกใหม่); ใบแจ้งหนี้ของผู้ขาย (ถ้ามี) ไม่ถูก match

**Three-way match** (PO ↔ GRN ↔ invoice) ดำเนินการโดย persona **Finance** หลังจากทั้ง GRN และใบแจ้งหนี้ถูกบันทึกแล้ว — สถานะของ PO เองไม่ถูกเปลี่ยนจากผลลัพธ์ของการ match แต่ AP liability จะถูก post เทียบกับใบแจ้งหนี้ที่ match สำเร็จ ดูไฟล์ persona Finance สำหรับฝั่งรับของการส่งต่อใบแจ้งหนี้

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.md](./03-user-flow.md) — global state machine ของ PO และตาราง handoff ข้าม persona
- ไฟล์พี่น้อง: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ภายในที่ส่ง PO บันทึกการตอบรับของผู้ขาย และรัน amendment loop แทนผู้ขาย
- ไฟล์พี่น้อง: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — persona ภายในปลายน้ำที่รับของจริงจากผู้ขายและ post GRN ที่ขับเคลื่อน `sent → partial → completed`
- ไฟล์พี่น้อง: [03-user-flow-finance.md](./03-user-flow-finance.md) — persona ภายในที่เก็บใบแจ้งหนี้ของผู้ขายและรัน three-way match
- โมดูลที่เกี่ยวข้อง: [[good-receive-note]] — โมดูลปลายน้ำที่บันทึกการส่งของจริงของผู้ขายและขับเคลื่อน transition สถานะการรับสินค้าของ PO
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่งหลักจาก carmen/docs สำหรับการวิเคราะห์ทางธุรกิจของโมดูล PO การส่ง PO และ flow ของ three-way match
