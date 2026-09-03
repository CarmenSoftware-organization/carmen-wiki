---
title: ใบรับสินค้า (Goods Receive Note)
description: เอกสารรับสินค้าที่บันทึกการรับของจริงตามใบสั่งซื้อและเพิ่มสินค้าเข้าคลัง
published: true
date: 2026-07-15T00:00:00.000Z
tags: good-receive-note, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบรับสินค้า (Goods Receive Note)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** บันทึกการรับสินค้าจริงตามใบ PO โพสต์การเคลื่อนไหวสต๊อกเข้า และอัปเดต costing แบบ FIFO / average (`draft` → `saved` → `committed` หรือ `voided`) &nbsp;·&nbsp; **ผู้ใช้:** Store Keeper / Receiver, Inventory Manager, Purchaser &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_good_received_note`, `tb_good_received_note_detail`, `tb_good_received_note_detail_item`, `tb_inventory_transaction`, FIFO / average-cost layers &nbsp;·&nbsp; **หน้าย่อย:** 13
>
> **แก้ไขในรอบนี้ (2026-07-15):** เวอร์ชันก่อนหน้าของหน้านี้อธิบายวงจรชีวิต 3 สถานะ (`Received`/`Draft → Committed → Voided`) โดยระบุว่า Commit คือ "เหตุการณ์เดียวที่เปลี่ยนแปลงระบบ" และมีการสร้างรายการ AP/journal เป็นส่วนหนึ่งของ **three-way match** (PO↔GRN↔invoice) — ทั้งสองอย่างไม่ตรงกับซอร์สโค้ดปัจจุบัน enum สถานะจริง (`enum_good_received_note_status`) มี **4 ค่า** คือ `draft`, `saved`, `committed`, `voided` และเหตุการณ์ที่เปลี่ยนแปลงระบบจริง ๆ คือ **การเปลี่ยนสถานะ `draft → saved`** (`GoodReceivedNoteLogic.save()` ใน `good-received-note.logic.ts`) — `save()` ไม่ใช่ `commit()` ที่สร้างแถว `tb_inventory_transaction`, เขียน FIFO / average-cost layer และเพิ่ม `received_qty` ของ PO ต้นทาง ส่วน `commit()` (`saved → committed`) เพียงเปลี่ยน `doc_status` และล็อกเอกสาร — ไม่พบผลกระทบต่อ inventory, PO หรือ GL เพิ่มเติมใน backend ปัจจุบัน การค้นหาทั่ว repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `journal`, `ledger`, `three-way`, `vendor_invoice`, และ `tb_invoice` ให้ผล **ศูนย์รายการที่ตรงกัน** — ไม่มีฟีเจอร์การบันทึกใบกำกับผู้ขาย, การโพสต์ journal ฝั่ง AP หรือ three-way match ในซอร์สปัจจุบัน (ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วในโมดูล `purchase-order`) ให้ถือว่าข้อความ "AP accrual", "GRN Clearing" หรือ "three-way match" ที่ปรากฏในหน้านี้หรือหน้าย่อยเป็นข้อมูลที่ยังไม่ยืนยัน / ยังไม่ implement เว้นแต่จะระบุไว้เป็นอย่างอื่น

![ใบรับสินค้า (Goods Receive Note) screen](/screenshots/good-receive-note/index.png)

![ใบรับสินค้า (Goods Receive Note) detail screen](/screenshots/good-receive-note/detail.png)

## 1. ภาพรวม

**ใบรับสินค้า (Goods Receive Note — GRN)** คือเอกสารที่บันทึกการรับสินค้าจริงจากผู้ขายอย่างเป็นทางการและเขียนเข้าคลังสินค้า แต่ละ GRN ประกอบด้วยส่วนหัว — เลข GRN วันที่รับ ผู้ขาย หมายเลขใบกำกับและวันที่ สกุลเงินและอัตราแลกเปลี่ยน snapshot ของเงื่อนไขเครดิต ฟิลด์ `post_type` (`ap` / `consignment` / `cash`) และตัวบ่งชี้ค่าใช้จ่ายเพิ่มเติม — และรายการสินค้าหนึ่งรายการขึ้นไป แต่ละบรรทัดระบุสินค้าและคลังจัดเก็บ ส่วนปริมาณ/ราคา/ภาษีจริงอยู่บนแถวเหตุการณ์รับของลูก (`tb_good_received_note_detail_item`) ทำให้หนึ่งบรรทัดครอบคลุมได้หลายเหตุการณ์การรับ (ส่งแยกรอบ, lot ปน, ของแถม FOC พ่วงกับของที่จ่ายเงิน) แต่ละเหตุการณ์รับมีปริมาณที่สั่ง (เมื่อมาจาก PO) ปริมาณที่รับ ปริมาณ FOC ราคาต่อหน่วย ส่วนลด ภาษี และยอดรวมต่อบรรทัดที่ระบบคำนวณให้; ส่วนหัวจะรวบยอดเป็นยอด net, ภาษี และยอดรวมทั้งในสกุลเงินธุรกรรมและสกุลฐาน หมายเลข lot และวันหมดอายุ **ไม่ได้** เก็บบนบรรทัด GRN เอง — อยู่บนแถว `tb_inventory_transaction_detail` ที่เชื่อมผ่าน `inventory_transaction_id` ของเหตุการณ์รับ (ดู [01-data-model.md](/th/inventory/good-receive-note/01-data-model) §5)

GRN เดินตามวงจรชีวิต 4 สถานะบน `enum_good_received_note_status`: `draft` (แก้ไขได้ ไม่กระทบสต๊อกหรือ GL) → `saved` (บันทึกรายการครบแล้ว) → `committed` (ล็อก) ส่วน `voided` เข้าได้จาก `draft` หรือ `saved` และเป็นการยกเลิกเชิงบริหาร — ไม่มี GRN ที่ `committed` แล้วสามารถ void ผ่านหน้าจอ UI ได้ (ปุ่ม Void จะแสดงเฉพาะเมื่อ GRN ยังไม่ `committed`) **เหตุการณ์ที่เปลี่ยนแปลงระบบคือ `draft → saved`** ไม่ใช่ `saved → committed`: `GoodReceivedNoteLogic.save()` คือจุดที่เขียนแถว `tb_inventory_transaction`, สร้าง FIFO cost layer หรือคำนวณ weighted-average ใหม่ และเพิ่ม `received_qty` (พร้อม `po_status`) ของ PO ต้นทาง — ทั้งหมดในธุรกรรมเดียว การเรียก `commit()` ถัดมา (`saved → committed`) เพียงอัปเดต `doc_status` และล็อกเอกสารไม่ให้แก้ไขต่อ — ไม่พบผลกระทบต่อ inventory, PO หรือ GL เพิ่มเติมสำหรับขั้นตอน commit เองใน backend ปัจจุบัน เมื่อ `committed` แล้วเอกสารจะถูกล็อก — การแก้ไขต้องผ่านการปรับปรุงชดเชยใน [inventory-adjustment](/th/inventory/inventory-adjustment) หรือ `tb_credit_note` กับ GRN

GRN สามารถสร้างได้จาก PO เปิดหนึ่งใบหรือมากกว่า — รองรับการรวมหลาย PO เมื่อ PO ที่เลือกมี **ผู้ขายและสกุลเงินเดียวกัน** (wizard สร้าง GRN จะปฏิเสธการเลือกที่มีสกุลเงินต่างกัน ไม่พบการตรวจสอบเงื่อนไขเครดิตเพิ่มเติม) — หรือสร้างด้วยมือสำหรับการรับของที่ไม่มี PO ต้นทาง (`doc_type = manual`) การรับของบางส่วนถือเป็นเรื่องปกติ — GRN ติดตามปริมาณที่รับเทียบกับที่สั่งต่อบรรทัด และส่ง `received_qty` กลับไปยัง PO ต้นทาง ซึ่งจะเคลื่อนไปทาง `partial` หรือ `completed` ขึ้นอยู่กับว่าทุกบรรทัดรับครบหรือยัง **ยังไม่ยืนยัน:** ไม่พบฟีเจอร์การบันทึกใบกำกับผู้ขาย, การโพสต์ journal ฝั่ง AP หรือ three-way match (PO ↔ GRN ↔ invoice) ใน frontend หรือ backend ปัจจุบันเลย — ให้ถือว่าข้อความลักษณะนี้ที่ปรากฏในโมดูลนี้เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ implement แล้ว

## 2. บริบททางธุรกิจ

GRN คือจุดควบคุมที่โลกของจริงพบกับบัญชี: จนกว่าการเปลี่ยนสถานะ `draft → saved` จะเกิดขึ้น PO ยังเป็นเพียง commitment เมื่อ save แล้ว สต๊อกคงคลังและ cost layer จะถูกอัปเดตและ `received_qty` ของ PO ต้นทางจะเพิ่มขึ้น ธุรกิจโรงแรมมีกำไรขั้นต้นจากต้นทุนอาหารที่บางเฉียบและต้องพึ่งพาจุดตรวจนี้เพื่อจับการส่งของขาด ส่งของเกิน และการคลาดเคลื่อนของราคาก่อนที่จะกลายเป็นความผิดพลาดของคลังสินค้า การบังคับให้หมายเลขใบกำกับ + ผู้ขายเป็น unique (`(invoice_no, vendor_id)` ต้อง unique ต่อ GRN ที่ไม่ได้ void) การแยก `doc_type` PO/manual และสถานะล็อกหลัง commit มีอยู่เพื่อให้ทุกการรับของอธิบายได้

**ยังไม่ยืนยัน / ไม่พบในซอร์สปัจจุบัน:** ไม่พบโค้ด journal entry, ledger หรือ GL-posting ใดๆ ใน backend module ของ good-received-note (`good-received-note.service.ts`, `good-received-note.logic.ts`) — การค้นหาทั่ว repo สำหรับ `journal`, `ledger`, `accounts_payable`, `vendor_invoice`, และ `tb_invoice` ให้ผลศูนย์รายการ ให้ถือว่า "debit inventory / credit accounts payable", "AP entry" และข้อความบัญชีลักษณะเดียวกันเป็นเจตนาการออกแบบจาก `carmen/docs` ไม่ใช่พฤติกรรมที่ยืนยันแล้ว ฟิลด์ boolean `is_consignment` และ `is_cash` ของ Prisma schema ที่เคยอธิบายไว้ในเวอร์ชันก่อนหน้าของหน้านี้ **ไม่มีอยู่แล้ว** — ส่วนหัวปัจจุบันมีเพียง enum `post_type` เดียว (`ap` | `consignment` | `cash`, ค่าเริ่มต้น `ap`) แทน และไม่พบ logic แยกเงื่อนไขตามฟิลด์นี้ใน backend เช่นกัน (ดู [01-data-model.md](/th/inventory/good-receive-note/01-data-model) §4–§5) `enum_transaction_type` (enum ที่ระบุประเภทของแถว ledger สินค้าคงคลัง) ไม่มีสมาชิก "Stock In", "Consignment In", หรือ "Non-Inventory" — การรับ GRN จะ resolve เป็นค่าเดียวคือ `good_received_note` เสมอ; การแยกประเภทการเคลื่อนไหวตาม `post_type` ยังไม่ implement

ความปลอดภัยของอาหารและการควบคุมคุณภาพ: สินค้าที่เน่าเสียง่ายจะมีหมายเลข lot (สร้างอัตโนมัติในรูปแบบตายตัว `RC{YY}{MM}{ลำดับ 4 หลัก}` หรือเขียนทับด้วยมือ) และวันหมดอายุที่เดินทางไปกับ inventory transaction ที่เชื่อมโยง เพื่อให้ FIFO consumption และการสืบย้อน recall สามารถสืบกลับไปยัง GRN ต้นทางได้ **ยังไม่ยืนยัน:** ไม่พบประตู "quality hold" ต่อบรรทัด, ฟิลด์ `accepted_qty` หรือกลไก accept/reject/partially-accept ใดๆ ทั้งใน schema หรือโค้ดแอปพลิเคชัน — ความคลาดเคลื่อนในการรับของถูกจัดการเพียงแค่กรอก `received_qty` ให้น้อยกว่าปริมาณที่สั่ง ไม่ใช่ขั้นตอนการยอมรับแยกต่างหาก ความคลาดเคลื่อนของราคาเทียบกับ vendor pricelist ตอนกรอก GRN มีอธิบายไว้ใน `carmen/docs` แต่ไม่พบโค้ดที่ตรงกันภายในโมดูล GRN เองในรอบตรวจสอบนี้

## 3. แนวคิดสำคัญ

- **Receiving Lot**: หมายเลข lot ที่กำหนดตอนรับของบนแถว inventory transaction ที่เชื่อมโยง (ไม่ใช่บนบรรทัด GRN เอง) ในรูปแบบตายตัวที่ระบบสร้างให้ `RC{YY}{MM}{ลำดับ 4 หลัก}` (`inventory-transaction.service.ts`) พร้อมเขียนทับด้วยมือได้และมีวันหมดอายุ ประวัติ lot ถูกเก็บไว้ตั้งแต่ต้นจนจบ เพื่อให้ FIFO consumption และเหตุการณ์ recall สืบย้อนกลับไปยัง GRN ต้นทางได้ **แก้ไขในรอบนี้:** ไม่พบหลักฐานว่ารูปแบบหมายเลข lot *ตั้งค่าได้* (ส่วนประกอบวันที่ ตัวระบุสินค้า token ที่ tenant กำหนดเอง) — ตัวสร้างปัจจุบันใช้รูปแบบตายตัวเพียงแบบเดียว
- **Partial Receipt**: GRN ที่ทำให้ PO ที่ค้างอยู่สำเร็จเพียงบางส่วน ปริมาณที่รับสามารถน้อยกว่าที่สั่งได้ และ PO ต้นทางจะเคลื่อนไปทางสถานะ `partial` พร้อมปริมาณคงเหลือที่เปิดสำหรับ GRN ในอนาคต สามารถออก GRN หลายใบกับ PO เดียวกันได้จนกว่าทุกบรรทัดจะรับครบ (`po_status = completed`)
- **Over/Under Receipt**: ความคลาดเคลื่อนของปริมาณระหว่าง PO กับ GRN รับขาด (รับน้อยกว่าที่สั่ง) จะปล่อย PO ไว้ที่ `partial` รับเกินถูกจำกัดด้วยการตรวจสอบเทียบ `order_qty − received_qty − cancelled_qty` บนบรรทัด PO ภายใต้ tolerance การรับเกินของ tenant
- **Save (เหตุการณ์ที่เปลี่ยนแปลงระบบ)**: การเปลี่ยนสถานะ `draft → saved` — ไม่ใช่ commit — คือเหตุการณ์เดียวที่อัปเดตสต๊อก ตอน save ระบบจะ: (1) เขียนแถว `tb_inventory_transaction` ต่อเหตุการณ์รับของ (2) สร้าง FIFO cost layer ใหม่หรือคำนวณ weighted-average ใหม่ตามวิธี costing ของสินค้า และ (3) เพิ่ม `received_qty` (พร้อม `po_status`) ของบรรทัด PO ต้นทาง **Commit** (`saved → committed`) เพียงเปลี่ยน `doc_status` และล็อกเอกสาร — ไม่พบผลกระทบต่อ inventory หรือ PO เพิ่มเติมในซอร์สปัจจุบัน **ยังไม่ยืนยัน:** ไม่พบโค้ด journal entry / GL-posting ใดๆ ในโมดูลนี้; batch commit และ auto-commit ที่สิ้นงวดก็ไม่พบในซอร์สปัจจุบันเช่นกัน (ไม่มี batch endpoint ไม่มี scheduled job) — ให้ถือว่าทั้งสองเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ implement แล้ว
- **Extra Cost Allocation**: ส่วนประกอบ landed cost (freight, handling, duties) ถูกบันทึกกับ GRN พร้อม tag โหมดการกระจาย (`manual`, `by_value`, หรือ `by_qty` — `enum_allocate_extra_cost_type`; ไม่มีโหมด `by_weight` / `by_volume`) **ยังไม่ยืนยัน:** ไม่พบโค้ดฝั่ง server ที่แบ่งจำนวนเงิน extra cost ไปยังแต่ละบรรทัด GRN จริง หรือป้อนเข้าสู่การคำนวณ cost layer แบบ FIFO/average — frontend ปัจจุบันรับเพียงจำนวนเงินรวมต่อประเภท extra cost โดยไม่มี UI แจกแจงต่อบรรทัด และการสร้าง cost layer ใน backend อ่านเฉพาะยอด net ของบรรทัดเอง ให้ถือว่า "Last Cost = (Net Amount + Extra Costs) / (Received Qty + FOC Qty)" เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว
- **FOC (Free of Charge)**: เหตุการณ์รับของที่สินค้าจากผู้ขายมาในราคา 0 (ตัวอย่าง โบนัสส่งเสริม การแทนสินค้าที่เสียหาย) บันทึกเป็นแถว `tb_good_received_note_detail_item` คู่ขนานที่มี `foc_qty` บนบรรทัดเดียวกัน ปริมาณ FOC ไม่ถูกรวมในยอด subtotal ของบรรทัดแต่รวมในปริมาณคงคลังและ lot
- **`post_type` (ap / consignment / cash)**: enum ระดับส่วนหัว (`enum_good_received_note_post_type`, ค่าเริ่มต้น `ap`) ที่มาแทน boolean คู่ `is_consignment` / `is_cash` เดิม — สองฟิลด์นั้นไม่มีอยู่ใน schema แล้ว **ยังไม่ยืนยัน:** ไม่พบ logic แยกเงื่อนไขตาม `post_type` ใน backend (ไม่มีการจัดการ GL ที่ต่างกัน ไม่มี inventory-transaction type ที่แยกกัน) — ฟิลด์นี้ถูกเก็บและ expose ผ่าน API แต่ดูเหมือนจะไม่เปลี่ยนพฤติกรรมของระบบ `enum_transaction_type` (enum ประเภทของ ledger คงคลัง) ไม่มีสมาชิก "Stock In" / "Consignment In" / "Non-Inventory" — การรับ GRN จะโพสต์เป็นค่าเดียวคือ `good_received_note` เสมอ

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Store Keeper / Receiving Clerk | รับการส่งของจริงที่ dock นับสินค้าเทียบกับ PO และใบส่งของของผู้ขาย สร้าง GRN ในสถานะ `draft` แนบใบส่งสินค้า บันทึกปริมาณที่รับต่อบรรทัด และบันทึกเพื่อรอตรวจสอบ (`draft → saved` ซึ่งเป็นขั้นตอนที่โพสต์สต๊อก) |
| Store Manager / Inventory Manager | กระทบยอด GRN กับสต๊อกจริงที่รับ ดูแลการติดตาม lot/batch และการกำหนด storage location และ commit (`saved → committed`) เพื่อล็อกเอกสาร |
| Purchaser / Procurement Officer | เป็นเจ้าของ PO ต้นทางที่ GRN ถูกสร้างขึ้นมาเทียบด้วย ตรวจสอบข้อมูลการรับของสำหรับ PO ที่ตนออก และประสานกับผู้ขายเมื่อมีความคลาดเคลื่อน (ส่งขาด ผิดสินค้า) |
| Department Manager | ตรวจสอบ GRN ที่กระทบ cost-centre ของแผนก และยืนยันว่าสินค้าที่รับตรงกับที่สั่งสำหรับแผนก |
| System Administrator | ดูแล RBAC และการกำหนดลำดับ running-code (เลข GRN), รหัสภาษี และอัตราแลกเปลี่ยน; ดูแลการเชื่อมต่อกับโมดูล PO และ Inventory **ยังไม่ยืนยัน:** ไม่พบ "GRN configuration console" เฉพาะทาง (ตัวแก้ไขรูปแบบเลข lot, panel endpoint การเชื่อมต่อ) ในซอร์สปัจจุบัน — หน้าจอตั้งค่าภาษี สกุลเงิน และ running-code เป็นหน้าจอทั่วไปข้ามโมดูล ตามที่บันทึกไว้ใน [system-config](/th/inventory/system-config) และ [master-data](/th/inventory/master-data) ไม่ใช่ workspace เฉพาะของ GRN |

**ตัดออกในรอบนี้ (ไม่พบ route, component หรือ endpoint ที่ตรงกัน):** บทบาท "Finance Team / AP Clerk" ที่อธิบายว่าทำ three-way match ตรวจสอบการจัดสรรค่าใช้จ่ายเพิ่มเติมก่อนโพสต์ AP และเซ็นรับรองกิจกรรมการรับของที่สิ้นงวด การค้นหาทั่ว repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `three-way`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` ให้ผลศูนย์รายการ และ `enum_stage_role` (enum บทบาท stage ของ workflow ที่ใช้ร่วมกับ PR/PO) ไม่มีสมาชิก `finance` — ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วในโมดูล `purchase-order`

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [purchase-order](/th/inventory/purchase-order) — GRN ถูกสร้างจาก PO; การรับของเพิ่ม `received_qty` และ `po_status` ของ PO
- [inventory](/th/inventory/inventory) — การรับ GRN โพสต์การเคลื่อนไหวสต๊อกเข้า
- [costing](/th/inventory/costing) — ราคาต่อหน่วยของ GRN ป้อนเข้า FIFO lot record หรืออัปเดต Weighted Average
- [vendor-pricelist](/th/inventory/vendor-pricelist) — ความคลาดเคลื่อนของราคา GRN ถูกตรวจสอบเทียบกับ vendor pricelist

**การตั้งค่า Master:**
- [master-data/vendor](/th/inventory/master-data/vendor) — vendor master ที่อ้างอิงโดยส่วนหัว GRN
- [master-data/currency](/th/inventory/master-data/currency) — สกุลธุรกรรมและอัตราแลกเปลี่ยนสำหรับการรับของที่ dual-post
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — รหัสภาษีที่ใช้กับบรรทัด GRN
- [master-data/credit-term](/th/inventory/master-data/credit-term) — เงื่อนไขการชำระเงินที่ copy จาก vendor master ลง GRN
- [master-data/extra-cost-type](/th/inventory/master-data/extra-cost-type) — ส่วนประกอบ landed cost (freight, duties, handling) ที่จัดสรรข้ามบรรทัด
- [master-data/delivery-point](/th/inventory/master-data/delivery-point) — สถานที่รับของที่สินค้าได้รับการรับจริง
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับปริมาณที่รับ
- [master-data/location](/th/inventory/master-data/location) — สถานที่จัดเก็บที่แต่ละบรรทัดเขียนการเคลื่อนไหวสต๊อกเข้า
- [system-config/workflow](/th/inventory/system-config/workflow) — workflow อนุมัติ / commit สำหรับการอนุญาต GRN
- [system-config/period](/th/inventory/system-config/period) — ประตูงวดบัญชีสำหรับการโพสต์ GRN
- [system-config/running-code](/th/inventory/system-config/running-code) — การกำหนดลำดับหมายเลขเอกสาร GRN
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — บันทึกการเปลี่ยนสถานะและการแก้ไข GRN สำหรับ audit
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — ใบส่งสินค้า ใบส่งของ และหลักฐานคุณภาพที่แนบกับแต่ละ GRN

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/good-recive-note-managment/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — แบบจำลองข้อมูล](/th/inventory/good-receive-note/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/good-receive-note/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
- [02 — กฎทางธุรกิจ](/th/inventory/good-receive-note/02-business-rules) — การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ และการ posting (§6 แก้ไขเรื่องเล่า three-way match / AP-journal เดิมที่ไม่พบในซอร์สปัจจุบัน)
- [03 — User Flow](/th/inventory/good-receive-note/03-user-flow) — วงจรชีวิตของเอกสารและสารบัญ persona
  - [Receiver](/th/inventory/good-receive-note/03-user-flow-receiver)
  - [Purchaser](/th/inventory/good-receive-note/03-user-flow-purchaser)
  - [Finance](/th/inventory/good-receive-note/03-user-flow-finance) — หน้าแก้ไข: เหตุผลที่ไม่พบ persona Finance / three-way match
  - [Audit / Config](/th/inventory/good-receive-note/03-user-flow-audit-config) — หน้าแก้ไข: เหตุผลที่ไม่พบ GRN configuration console เฉพาะทาง
- [04 — Test Scenarios](/th/inventory/good-receive-note/04-test-scenarios) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ mapping ไปยัง E2E
  - [Receiver](/th/inventory/good-receive-note/04-test-scenarios-receiver)
  - [Purchaser](/th/inventory/good-receive-note/04-test-scenarios-purchaser)
  - [Finance](/th/inventory/good-receive-note/04-test-scenarios-finance) — หน้าแก้ไข
  - [Audit / Config](/th/inventory/good-receive-note/04-test-scenarios-audit-config) — หน้าแก้ไข
