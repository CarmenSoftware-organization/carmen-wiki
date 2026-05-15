---
title: ใบสั่งซื้อ — เส้นทางผู้ใช้งาน
description: วงจรเอกสารและไฟล์เส้นทางตาม persona สำหรับโมดูล purchase-order
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — เส้นทางผู้ใช้งาน

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่มต้นภาพรวม** ของชุดเอกสารเส้นทางผู้ใช้งานสำหรับโมดูล `purchase-order` ใบสั่งซื้อ (PO) คือเอกสารผูกพันการจัดซื้อ — ส่วนหัว PO (`tb_purchase_order`) พร้อมบรรทัดรายละเอียดอย่างน้อยหนึ่งบรรทัด (`tb_purchase_order_detail`) — ซึ่งนำรายการที่ตกลงแล้วจากใบขอซื้อ (PR) ที่อนุมัติแล้วหนึ่งใบหรือมากกว่ามาผูกพันผู้ซื้อกับผู้ขายในราคา จำนวน และวันส่งมอบที่กำหนด วงจรชีวิตในหัวข้อ 2 ครอบคลุมตั้งแต่การสร้างร่างครั้งแรก ผ่านการอนุมัติภายใน การส่ง PO ให้ผู้ขาย การรับสินค้าบางส่วนหรือเต็มจำนวนตาม PO และการปิด (ปิดปกติเมื่อรับครบหรือปิดก่อนกำหนด) persona ที่เกี่ยวข้องประกอบด้วย **เจ้าหน้าที่จัดซื้อ (Purchaser)** (สร้างและส่ง PO, จัดการการแก้ไข), **ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)** (กำกับดูแล, อนุมัติรายการมูลค่าสูง, จัด vendor ranking, มีอำนาจ override), **ผู้ขาย (Vendor)** (บุคคลภายนอกไม่มี login เข้าระบบ — รับ PO, ตอบรับ, ส่งสินค้า, ออกใบแจ้งหนี้), **ผู้รับสินค้า (Receiver)** (รับสินค้าจริงและสร้าง GRN กับ PO), ทีม **ฝ่ายการเงิน (Finance)** (three-way match และลงบัญชี AP) และบทบาท **Audit / Config** (Auditor สำหรับการตรวจสอบแบบ read-only และ System Administrator สำหรับการตั้งค่า workflow และจุดเชื่อมต่อ) แค็ตตาล็อก role อย่างเป็นทางการอยู่ใน [index.md](./index.md) หัวข้อ 4

หัวข้อ 2 ด้านล่างคือ **state machine แบบ global** — รายการ transition ตามค่ามาตรฐานของ `enum_purchase_order_doc_status` โดยไม่ผูกกับ persona ใด ๆ ส่วนไฟล์ตาม persona (ลิงก์อยู่ในหัวข้อ 3) จะอธิบาย *เส้นทาง* ของ persona นั้นผ่าน state machine — จุดเริ่มต้น, action ที่ใช้ได้, การแยกสาขาในการตัดสินใจ และการ handoff ที่จบบทบาทของ persona นั้น หัวข้อ 4 สรุปการ handoff ข้าม persona ที่เชื่อมเส้นทางแต่ละเส้นเข้าด้วยกัน อ่านภาพรวมนี้ก่อนเพื่อยึดวงจรชีวิตให้แน่น แล้วค่อยเจาะลงไปที่ไฟล์ persona ที่ตรงกับ role ของคุณ

## 2. วงจรเอกสาร

status ของเอกสาร PO เก็บใน `tb_purchase_order.po_status` และจำกัดให้ใช้เฉพาะค่าที่ประกาศใน `enum_purchase_order_doc_status` ได้แก่ `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed` ตารางด้านล่างแสดง transition ที่ได้รับอนุญาตระหว่าง state เหล่านี้ การ transition อื่นนอกตารางจะถูก workflow engine ปฏิเสธ หมายเหตุ: transition ที่เกิดจากการรับสินค้า (`sent → partial → completed`) ถูก trigger โดยการ post GRN ในโมดูลปลายน้ำ [[good-receive-note]] ไม่ใช่จากการกระทำตรงของผู้ใช้บน PO

| จากสถานะ | การกระทำ | ไปยังสถานะ | ผู้มีสิทธิ์ | เงื่อนไขก่อนหน้า |
| -------- | -------- | ---------- | ----------- | ---------------- |
| `(none)` | สร้าง | `draft` | เจ้าหน้าที่จัดซื้อ (Purchaser) | validate ฟิลด์ส่วนหัว (`vendor_id`, `currency_id`, `order_date`, `delivery_date`, `workflow_id`); ต้องมีบรรทัดอย่างน้อย 1 รายการก่อน submit เขียน PR linkage ไปยัง bridge table เมื่อสร้างจาก PR |
| `draft` | บันทึก (แก้ไข) | `draft` | เจ้าหน้าที่จัดซื้อ (เจ้าของ PO) | PO ยังแก้ไขได้; stage ใน workflow ยังไม่เดินหน้า ยอดรวมส่วนหัว (`total_qty`, `total_price`, `total_tax`, `total_amount`) ถูกคำนวณใหม่ตอนบันทึก |
| `draft` | ส่งเพื่ออนุมัติ | `in_progress` | เจ้าหน้าที่จัดซื้อ (เจ้าของ PO) | มีบรรทัดที่ยังไม่ถูกลบอย่างน้อย 1 รายการ; ส่วนหัวครบถ้วน; `workflow_id` ที่เลือก active ใน scope `purchase-order` ตั้ง `last_action` เป็น `submitted`; cursor ของ stage เลื่อนไป stage อนุมัติแรก |
| `draft` | ลบ | `(none)` | เจ้าหน้าที่จัดซื้อ, ผู้จัดการฝ่ายจัดซื้อ | soft-delete เท่านั้น (ตั้ง `deleted_at`); อนุญาตเฉพาะตอนที่ PO อยู่ใน `draft` และไม่เคย submit |
| `in_progress` | อนุมัติ (stage นี้ ไม่ใช่ stage สุดท้าย) | `in_progress` | ผู้อนุมัติของ stage ปัจจุบัน | ผู้อนุมัติถูกผูกกับ `workflow_current_stage` ด้วย `stage_role = approve`; `last_action` กลายเป็น `approved`; cursor ของ stage เลื่อน |
| `in_progress` | อนุมัติ (stage สุดท้าย) | `sent` | ผู้อนุมัติของ stage สุดท้าย (โดยทั่วไปคือ Procurement Manager สำหรับมูลค่าสูง) | stage ก่อนหน้าทุกขั้นเซ็นอนุมัติครบ; ผ่านการตรวจ threshold มูลค่าสูงในกรณีที่ต้องตรวจ ส่ง PO ให้ผู้ขายใน transition นี้ (ผ่าน email / EDI / portal ตามที่ตั้งค่า) |
| `in_progress` | ส่งกลับ (send-back) | `draft` | ผู้อนุมัติคนใดในห่วงโซ่ | ต้องระบุเหตุผล; ส่ง PO กลับให้เจ้าหน้าที่จัดซื้อแก้ไข บันทึก audit comment |
| `in_progress` | ปฏิเสธ / void | `voided` | ผู้อนุมัติคนใดในห่วงโซ่, System Administrator | ต้องระบุเหตุผล; workflow ยุติและไม่อนุญาตให้กระทำการใด ๆ ต่อ |
| `sent` | รับสินค้า (บางส่วน) | `partial` | ผู้รับสินค้า (Receiver) ผ่านการ post GRN | บรรทัด PO อย่างน้อย 1 บรรทัดมี `received_qty > 0` แต่ `received_qty < order_qty − cancelled_qty` ใน PO ทั้งใบ การเปลี่ยน state คำนวณจากการ post GRN ระดับบรรทัด |
| `sent` | รับสินค้า (เต็มจำนวน) | `completed` | ผู้รับสินค้า (Receiver) ผ่านการ post GRN | ทุกบรรทัดสอดคล้องกับ `received_qty + cancelled_qty ≥ order_qty`; ทุกบรรทัดปิดผ่าน GRN ใน transaction เดียวกัน |
| `sent` | void (โมฆะ) | `voided` | ผู้จัดการฝ่ายจัดซื้อ, System Administrator | ต้องระบุเหตุผล; อนุญาตเฉพาะเมื่อยังไม่มี GRN post กับบรรทัดใด ๆ |
| `partial` | รับสินค้า (เพิ่มเติม) | `partial` | ผู้รับสินค้า (Receiver) ผ่านการ post GRN | GRN ถัดไป post จำนวนเพิ่ม แต่ PO ยังมีอย่างน้อย 1 บรรทัดที่ยังเปิด; state คงอยู่ที่ `partial` |
| `partial` | รับสินค้า (ยอดสุดท้าย) | `completed` | ผู้รับสินค้า (Receiver) ผ่านการ post GRN | GRN ใบสุดท้ายเคลียร์ยอดคงค้างในทุกบรรทัด; PO เปลี่ยนเป็นสถานะปิดปกติ |
| `partial` | ปิด (ผู้ขายส่งไม่ครบ) | `closed` | ผู้จัดการฝ่ายจัดซื้อ, Inventory Manager | ผู้ขายไม่สามารถส่งจำนวนคงค้างได้; จำนวนที่เปิดค้างถูกถือว่ายกเลิก (เขียนค่า `cancelled_qty` ของบรรทัด) ต้องระบุเหตุผล |
| `completed` | (ไม่มี action ต่อ) | `completed` | — | terminal state ของเส้นทางการรับสินค้า; three-way match ของ Finance ถูกติดตามบน invoice ที่ลิงก์ ไม่ใช่บน status ของ PO |

## 3. ดัชนีตาม Persona

แต่ละ persona ด้านล่างมีไฟล์เจาะลึกแยกที่อธิบายจุดเริ่มต้น, เส้นทางหลัก, สาขาการตัดสินใจ และจุดสิ้นสุด slug ใน URL ตรงกับ role ของ persona; คลิกลิงก์เพื่อเปิดมุมมองตาม persona

- [เจ้าหน้าที่จัดซื้อ (Purchaser)](./03-user-flow-purchaser.md) — สร้าง PO ด้วยตัวเองหรือแปลงจาก PR ที่อนุมัติแล้ว (พร้อมการจัดกลุ่ม vendor+currency), ตรวจสอบราคาตาม pricelist, ส่ง PO, จัดการการแก้ไขและการติดตามผล
- [ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)](./03-user-flow-procurement-manager.md) — กำกับดูแลฝ่ายจัดซื้อ, อนุมัติ PO และการแก้ไขมูลค่าสูง, จัด vendor ranking, มีอำนาจลบในร่าง void และ override การปิดก่อนกำหนด
- [ผู้ขาย (Vendor)](./03-user-flow-vendor.md) — บุคคลภายนอกที่ไม่มี login เข้าระบบ; รับ PO ที่ส่งมา ตอบรับ ส่งสินค้าตามเงื่อนไขที่ตกลง และออกใบแจ้งหนี้สำหรับ three-way match
- [ผู้รับสินค้า (Receiver)](./03-user-flow-receiver.md) — Receiver / Store Keeper + Inventory Manager รับสินค้าจริง, สร้าง GRN กับ PO ทีละบรรทัด, และ trigger transition การรับ `sent → partial → completed`
- [ฝ่ายการเงิน (Finance)](./03-user-flow-finance.md) — Finance Officer / AP + Finance Manager ตรวจความถูกต้องทางการเงินของ PO, ทำ three-way match (PO ↔ GRN ↔ invoice), จัดการสกุลเงิน / FX, และลงบัญชี AP liability
- [ผู้ตรวจสอบและผู้ดูแลระบบ (Audit / Config)](./03-user-flow-audit-config.md) — Auditor (ตรวจสอบ PO, การแก้ไข และ activity log แบบ read-only) และ System Administrator (ตั้งค่า stage ของ workflow, RBAC, numbering, จุดเชื่อมต่อ vendor และ pricelist)

## 4. การส่งต่อข้าม Persona

ตารางด้านล่างจับโมเมนต์ที่ PO ย้ายจากความรับผิดชอบของ persona หนึ่งไปยังอีก persona หนึ่ง การ handoff แต่ละครั้งยึดกับสถานะของเอกสาร ณ จุดที่ส่งต่อ

| จาก persona | ตัวกระตุ้น | ไปยัง persona | สถานะเอกสาร ณ จุดส่งต่อ |
| ----------- | ---------- | ------------- | ------------------------- |
| เจ้าหน้าที่จัดซื้อ (Purchaser) | กดส่งเพื่ออนุมัติ | ผู้อนุมัติ stage แรก (โดยทั่วไปคือ Procurement Manager สำหรับมูลค่าสูง) | `in_progress` (cursor ของ stage อยู่ที่ stage อนุมัติแรก) |
| ผู้อนุมัติ (Approver) stage N (ไม่ใช่ stage สุดท้าย) | อนุมัติที่ stage นี้ | ผู้อนุมัติ (Approver) stage N+1 | `in_progress` (cursor ของ stage เลื่อน) |
| ผู้จัดการฝ่ายจัดซื้อ (stage สุดท้าย) | อนุมัติที่ stage สุดท้ายและส่ง PO | ผู้ขาย (Vendor) | `sent` (ส่ง PO แล้ว; รอ GRN ใบแรก) |
| ผู้อนุมัติ (Approver) stage ใด ๆ | ส่งกลับพร้อมเหตุผล | เจ้าหน้าที่จัดซื้อ (Purchaser) | `draft` (เก็บประวัติการแก้ไขและความเห็นของผู้อนุมัติไว้) |
| ผู้ขาย (Vendor) | ส่งสินค้าจริง | ผู้รับสินค้า (Receiver) | `sent` (สถานะในระบบยังไม่เปลี่ยนจนกว่าจะ post GRN) |
| ผู้รับสินค้า (Receiver) | post GRN — รับบางส่วน | เจ้าหน้าที่จัดซื้อ, Inventory Manager | `partial` (ยังมีบรรทัดเปิดค้างอย่างน้อย 1 บรรทัด) |
| ผู้รับสินค้า (Receiver) | post GRN — ยอดสุดท้าย | ฝ่ายการเงิน (เพื่อ match invoice) | `completed` (ทุกบรรทัดรับครบแล้ว) |
| ผู้จัดการฝ่ายจัดซื้อ / Inventory Manager | ปิด PO โดยถือยอดคงค้างเป็น cancelled | ฝ่ายการเงิน (ตรวจการปิด) | `closed` (เขียนยอดคงค้างเป็น `cancelled_qty`) |
| ผู้จัดการฝ่ายจัดซื้อ / System Administrator | void พร้อมเหตุผล | Auditor (เพื่อตรวจสอบย้อนหลังเท่านั้น) | `voided` |
| ฝ่ายการเงิน (Finance) | three-way match สำเร็จและลงบัญชี AP | (terminal) | `completed` (PO ไม่เปลี่ยน; AP liability ลงบัญชีกับ invoice ที่ match แล้ว) |

## 5. แหล่งอ้างอิง

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่งหลักจาก carmen/docs สำหรับการวิเคราะห์ทางธุรกิจ, state diagram และ flow การสร้าง PO
- ไฟล์พี่น้อง: [01-data-model.md](./01-data-model.md) — ค่ามาตรฐานของ `enum_purchase_order_doc_status` ที่ใช้ในหัวข้อ 2 และ bridge table ที่เก็บการเชื่อมโยง PR→PO
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) — กฎ validation, authorization, posting และ transition ที่อ้างโดย transition แต่ละแถวในหัวข้อ 2
- โมดูลที่เกี่ยวข้อง: [[purchase-request]] (แหล่งต้นน้ำผ่าน bridge PR→PO), [[good-receive-note]] (การรับปลายน้ำที่ขับ transition `partial` / `completed`), [[vendor-pricelist]] (snapshot ราคาตอนแปลง PR เป็น PO)
