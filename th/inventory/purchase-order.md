---
title: ใบสั่งซื้อ (Purchase Order)
description: เอกสารผูกพันอย่างเป็นทางการกับผู้ขายเพื่อจัดซื้อสินค้าตามราคา ปริมาณ และเงื่อนไขการส่งมอบที่ตกลงกัน
published: true
date: 2026-05-20T00:00:00.000Z
tags: purchase-order, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบสั่งซื้อ (Purchase Order)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอกสารผูกพันกับผู้ขายภายนอก (`Draft` → `Sent` → `Partial`/`Fully Received` → `Closed`/`Voided`) ที่ยึดโยง three-way match กับ GRN และใบแจ้งหนี้ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Purchaser, Procurement Manager, Vendor, Receiver, Finance / AP, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_purchase_order`, `tb_purchase_order_detail`, ฟิลด์ trace จาก PR→PO (`prItemId`, `prNumber`), activity log การแก้ไข, [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) &nbsp;·&nbsp; **หน้าย่อย:** 17

![ใบสั่งซื้อ (Purchase Order) screen](/screenshots/purchase-order/index.png)

## 1. ภาพรวม

**ใบสั่งซื้อ (Purchase Order — PO)** คือเอกสารทางการที่มีผลผูกพันภายนอก ซึ่งผู้ซื้อออกให้ผู้ขาย และผูกพันองค์กรให้ซื้อสินค้าหรือบริการตามรายการที่ระบุ ในราคาต่อหน่วย ปริมาณ วันส่งของ และเงื่อนไขการชำระเงินที่ตกลงไว้ PO แต่ละใบมีส่วนหัว — หมายเลขอ้างอิงที่ไม่ซ้ำ ผู้ขาย วันที่สั่งซื้อ วันส่งของที่ต้องการ จุดส่งของ สกุลเงินและอัตราแลกเปลี่ยน เงื่อนไขการชำระเงินและการส่งของ สถานะ ผู้สร้าง และยอดรวมที่ roll-up แล้ว — และรายการสินค้าหนึ่งรายการขึ้นไปที่บรรจุข้อมูลสินค้าจากแคตตาล็อกหรือคำอธิบายอิสระ ปริมาณที่สั่ง หน่วยนับ ราคาต่อหน่วย ส่วนลด การจัดการภาษี ปริมาณ FOC และฟิลด์ traceability ที่ลิงก์กลับไปยังบรรทัดของใบขอซื้อต้นทาง ยอดรวมส่วนหัว (subtotal, total discount, total tax, grand total) คำนวณจากค่าระดับบรรทัดที่ปัดเศษแล้ว และ dual-post ทั้งในสกุลเงินที่ใช้บันทึกธุรกรรมและสกุลเงินฐาน

วงจรชีวิตของ PO ขับเคลื่อนด้วยสถานะ: `Draft` (แก้ไขได้ ยังไม่มีการผูกพัน) → `Sent` (ส่งถึงผู้ขายแล้วและเกิด firm budget commitment) → อาจเป็น `Partially Received` เมื่อมีการ post GRN → `Fully Received` เมื่อทุกบรรทัดถูกจับคู่หมด → `Closed` เมื่อ PO ถูกปิดในเชิงบริหาร (หรือ `Voided` หากถูกยกเลิกก่อนการรับของ) การลบทำได้เฉพาะใน `Draft` เท่านั้น; PO ที่ active ทำได้เพียง void หรือ close เพื่อรักษา audit trail ไว้ การแก้ไข (ราคา ปริมาณ วันส่งของ เงื่อนไขผู้ขาย) บน PO ที่ open จะถูก version พร้อมรายการใน activity log การ short-close PO — ยอมรับการรับของบางส่วนเป็นการสิ้นสุด — เป็นการกระทำโดยจงใจที่ปล่อย commitment ส่วนที่เหลือออก

PO สร้างได้ทั้งด้วยมือ (PO เปล่าที่สร้างจาก scratch) หรือโดยการแปลงใบขอซื้อที่อนุมัติแล้วหนึ่งใบขึ้นไป เมื่อเลือก PR หลายใบเพื่อแปลง ระบบจะ group โดยอัตโนมัติด้วย **vendor + currency** สร้าง PO หนึ่งใบต่อแต่ละ combination ที่ไม่ซ้ำ และรวมบรรทัดของ PR เข้าไป โดยรักษา traceability จาก PR ไปยัง PO บนทุกบรรทัด PO จะเป็นเอกสารที่ผู้ขายส่งของให้ ผู้รับสร้าง Good Receive Note และ three-way match (PO ↔ GRN ↔ ใบแจ้งหนี้ผู้ขาย) ปล่อยสินค้าให้ AP posting ได้

## 2. บริบททางธุรกิจ

PO คือจุดที่คำขอภายในกลายเป็นการผูกพันภายนอก ก่อนหน้านี้การใช้จ่ายเป็นเพียง soft commitment กับงบประมาณ การออก PO เปลี่ยนสิ่งนั้นให้กลายเป็น hard commitment พร้อมภาระผูกพันที่บังคับใช้ได้ตามกฎหมายต่อผู้ขายตามเงื่อนไขที่ตกลง การเปลี่ยนผ่านเพียงครั้งเดียวนี้คือสิ่งที่ทำให้ฝ่ายการเงินและจัดซื้อควบคุมการใช้จ่ายที่ควบคุมไม่ได้ได้: โดยการส่งทุกการผูกพันภายนอกผ่าน PO ที่มีเอกสารกำกับ พร้อมหมายเลขอ้างอิงที่ไม่ซ้ำ ผู้ขายที่อนุมัติแล้ว ราคา pricelist ที่ผ่านการ validate และ budget check องค์กรจึงป้องกันการสั่งซื้อนอกระบบและรับประกันว่าทุก invoice ในอนาคตจะมีการอนุมัติที่ตรงกัน

โมดูลนี้คือกระดูกสันหลังของการ integration ในห่วงโซ่ procure-to-pay PR ป้อนเข้ามาทางต้นน้ำพร้อมการจัดสรรผู้ขายและปริมาณที่อนุมัติ; PO ผูกพันปริมาณและราคาเหล่านั้นกับผู้ขาย; โมดูล GRN รับของกับ PO และตรวจสอบปริมาณที่สั่งเทียบกับที่รับและที่ยอมรับ; โมดูล inventory เพิ่ม on-order ตอน PO ส่ง และเพิ่ม on-hand ตอน GRN post; โมดูล vendor-pricelist จัดหาและ validate ราคาต่อหน่วย; และฝ่ายการเงินรับ firm commitment ไป และเมื่อ invoice เข้ามา ก็รัน three-way match ก่อน post ไปยังบัญชีเจ้าหนี้ Document management (attachments, comments, activity log) ให้ทุก PO มี audit trail ครบถ้วน — ใครสร้าง แก้ไขอะไร ส่งเมื่อไหร่ ใครรับ ปิดเมื่อไหร่

ความถูกต้องทางการเงินถูกบังคับใช้ที่ชั้นการคำนวณ subtotal บรรทัด ส่วนลด net amount ภาษี และยอดรวม ถูกปัดเศษที่ระดับบรรทัดด้วย half-up (banker's) rounding โดยใช้ทศนิยม 3 ตำแหน่งสำหรับปริมาณ 2 ตำแหน่งสำหรับเงิน และ 5 ตำแหน่งสำหรับอัตราแลกเปลี่ยน; ยอดรวมส่วนหัว PO roll up จากค่าบรรทัดที่ปัดเศษแล้ว; PO ข้ามสกุลเงิน dual-post พร้อมการจัดการอัตราแลกเปลี่ยนที่ชัดเจน PO ต้องกระทบยอดกับ PR ต้นทางและ GRN และ invoice ที่เกิดขึ้นได้สะอาด ดังนั้นวินัยการปัดเศษเดียวกันจึงใช้ end-to-end ตลอดการคำนวณ procure-to-pay

## 3. แนวคิดสำคัญ

- **PO Header**: เร็คคอร์ดระดับ transaction ที่บรรจุผู้ขาย หมายเลขอ้างอิง วันที่สั่งและวันส่งของที่ต้องการ สกุลเงินและอัตราแลกเปลี่ยน จุดส่งของ เงื่อนไขการชำระเงินและการส่งของ สถานะ ยอดรวม และฟิลด์ audit ส่วนหัวผูกทุก line item เข้าด้วยกันเป็น commitment เดียวต่อผู้ขายรายเดียวในสกุลเงินเดียว
- **PO Line / PO Item**: บรรทัดบน PO ที่แสดงสินค้าเดี่ยวหรือ free-text item พร้อมปริมาณที่สั่ง หน่วยนับ ราคาต่อหน่วย ส่วนลด อัตราภาษี ปริมาณ FOC ยอดรวมบรรทัดที่คำนวณแล้ว และฟิลด์ traceability (`prItemId`, `prNumber`) เมื่อมีต้นทางจาก PR บรรทัดคือหน่วยของการรับของ three-way match และ AP posting
- **Delivery Terms**: Incoterm หรือ clause ที่เทียบเท่าซึ่งกำหนดว่ากรรมสิทธิ์จะส่งต่อที่ใด ใครจ่ายค่าขนส่งและประกัน และที่ใดที่หน้าที่ส่งของของผู้ขายสิ้นสุด (เช่น จุดส่งของ on-premise unloading) บรรจุบนส่วนหัวและใช้โดย receiving และ finance
- **Payment Terms**: เงื่อนไขเครดิตที่ตกลงกับผู้ขาย (เช่น net 30, 2/10 net 30, COD) มาจาก vendor master คัดลอกลงในส่วนหัว PO ตอนสร้าง และใช้โดย AP คำนวณวันครบกำหนดและช่วงส่วนลดบน invoice ที่เกิดขึ้น
- **Amendment**: การเปลี่ยนแปลงที่ควบคุมต่อ PO ที่ active — ราคา ปริมาณ วันส่งของ เงื่อนไข หรือเพิ่ม/ลบบรรทัด — บันทึกเป็นเหตุการณ์ที่ version แล้วใน activity log การ amendment ปรับ open commitment และ propagate ไปยังงบประมาณและ on-order ของ inventory; การ re-acknowledge ของผู้ขายมักจำเป็นสำหรับการเปลี่ยนแปลงที่สำคัญ
- **Open vs Closed PO**: PO **open** มีปริมาณที่เหลือต้องรับหรือยังไม่ถูกปิดในเชิงบริหาร PO **closed** ถูก finalise — รับครบและปิด หรือ short-close พร้อมปล่อย commitment ที่เหลือ Closed PO ไม่รับ GRN เพิ่มและกลายเป็น read-only ยกเว้นสำหรับ reporting และ audit
- **Three-Way Match**: การควบคุม AP ที่เปรียบเทียบ PO line (สั่งอะไร), GRN line (รับและยอมรับอะไร) และ vendor invoice line (เรียกเก็บเงินอะไร) บนปริมาณและราคาก่อนอนุมัติ invoice สำหรับชำระเงิน ความคลาดเคลื่อน route ไปยัง procurement หรือ finance เพื่อแก้ไข
- **Voided PO**: PO ที่ active ถูกยกเลิกก่อนมีการ post receipt การ void ปล่อย budget commitment ทำให้ PO แก้ไขไม่ได้ และเก็บเร็คคอร์ดไว้สำหรับ audit PO ที่มี GRN อย่างน้อยหนึ่งใบไม่สามารถ void ได้ — ต้อง close แทน
- **Vendor + Currency Grouping**: กฎการแปลงที่แบ่ง PR ที่เลือกชุดหนึ่งเป็น PO หนึ่งใบต่อแต่ละ vendor-and-currency combination ที่ไม่ซ้ำ รับประกันว่า PO แต่ละใบเป็น single-vendor และ single-currency รวมบรรทัด PR ที่มีสิทธิ์ลงใน PO เดียว และรักษาแนวปฏิบัติ procurement ให้สะอาด
- **PR-to-PO Traceability**: ลิงก์ถาวรจาก PO line แต่ละบรรทัดกลับไปยัง PR line ต้นทาง (`prItemId`, `prNumber`) รักษาไว้ผ่าน amendments และ partial receipts เพื่อให้ผู้ตรวจสอบและผู้ปฏิบัติงานสามารถ trace สินค้าที่รับใด ๆ กลับไปยังความต้องการที่ขอได้
- **FOC (Free of Charge)**: ฟิลด์ระดับบรรทัดสำหรับสินค้าที่ผู้ขายให้มาในราคา 0 (ตัวอย่าง, โบนัสส่งเสริมการขาย) ปริมาณ FOC ไม่รวมใน subtotal ของ PO แต่ flow ผ่านไปยัง GRN เพื่อให้ฝั่งรับสินค้าบันทึกเข้าคลัง
- **Exchange Rate**: อัตราแปลงที่ capture บนส่วนหัว PO ตอนสร้าง ใช้ dual-post ยอดรวม PO ในสกุลเงินฐาน Lock ไว้บน PO เพื่อให้ commitment และ receipt และ invoice ที่เกิดขึ้นกระทบยอดกับฐานที่เสถียร

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Procurement Officer / Purchaser | สร้าง PO ด้วยมือหรือโดยแปลง PR ที่อนุมัติแล้ว ตรวจสอบการจัดสรรผู้ขายและราคา pricelist ตั้งเงื่อนไขการส่งของและการชำระเงิน ส่ง PO ให้ผู้ขาย บริหาร amendments และการติดตาม และ void หรือ close PO ตามที่วงจรชีวิตต้องการ |
| Procurement Manager | กำกับฟังก์ชัน procurement อนุมัติ PO มูลค่าสูงและ amendments ที่มีความสำคัญเชิงกลยุทธ์ บริหารความสัมพันธ์และการจัดอันดับผู้ขาย และปรับแต่งกฎ conversion และ grouping ถือ delete-in-draft และอำนาจ override |
| Vendor | ฝ่ายภายนอกที่รับ PO ยืนยันการตอบรับ ส่งของตามเงื่อนไขที่ตกลง และออก invoice ที่จับคู่กับ PO และ GRN ก่อนชำระเงิน |
| Receiver / Store Keeper | บทบาทปลายน้ำที่รับสินค้าจริง สร้าง GRN กับ PO และตรวจสอบปริมาณที่รับและที่ยอมรับทีละบรรทัด เป็นตัว trigger การเพิ่ม on-hand ของ inventory และการเปลี่ยนสถานะ partial-/fully-received บน PO |
| Inventory Manager | บริหารการรับสินค้าสำหรับ location กำกับการสร้าง GRN และปิด PO เมื่อรับครบหรือยอมรับเป็นการสิ้นสุด |
| Finance Officer / Accounts Payable | review เงื่อนไข PO และความถูกต้องทางการเงิน รัน three-way match บน invoice ผู้ขายเทียบกับ PO และ GRN post AP liability เมื่อจับคู่สำเร็จ และ flag ความคลาดเคลื่อนกลับไปให้ procurement |
| Finance Manager | review PO มูลค่าสูงและ amendments ก่อนส่ง ตรวจสอบการจัดการสกุลเงินและอัตราแลกเปลี่ยน และกำกับการควบคุมและ reporting ฝั่ง AP |
| System Administrator | ตั้งค่าการเรียงเลข PO การเปลี่ยนสถานะ RBAC การ integration กับผู้ขายและ pricelist การ integration งบประมาณและ inventory templates เอกสาร และกฎ conversion/grouping |
| Auditor | สิทธิ์ read-only ต่อ PO, amendments และ activity log เพื่อตรวจสอบความสอดคล้องของนโยบาย segregation of duties ความสมบูรณ์ของ three-way-match และ traceability end-to-end จาก PR ผ่าน PO และ GRN ไปยัง invoice |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [purchase-request](/th/inventory/purchase-request) — PO สร้างจาก PR ที่อนุมัติแล้ว
- [good-receive-note](/th/inventory/good-receive-note) — GRN ถูกสร้างกับ PO เมื่อรับของ
- [vendor-pricelist](/th/inventory/vendor-pricelist) — ราคา PO ถูก validate กับ vendor pricelist
- [product](/th/inventory/product) — บรรทัด PO อ้างอิงสินค้าจากแคตตาล็อก

**Master configuration:**
- [master-data/vendor](/th/inventory/master-data/vendor) — vendor master (header + addresses + contacts) ที่ส่วนหัว PO อ้างอิง
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินและอัตราแลกเปลี่ยนสำหรับ PO หลายสกุลเงิน
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — รหัสภาษีที่ใช้กับบรรทัด PO
- [master-data/credit-term](/th/inventory/master-data/credit-term) — เงื่อนไขการชำระเงินที่คัดลอกจาก vendor master ลงในส่วนหัว PO
- [master-data/delivery-point](/th/inventory/master-data/delivery-point) — จุดส่งของที่ตกลงกันสำหรับ commitment
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับปริมาณบรรทัด PO
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow อนุมัติสำหรับการอนุญาต PO และ amendments
- [system-config/running-code](/th/inventory/system-config/running-code) — การเรียงลำดับเลขเอกสาร PO
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log การเปลี่ยนสถานะ PO การ amendment และ three-way-match สำหรับ audit
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — vendor acknowledgements และเอกสาร contract ที่แนบกับ PO

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/purchase-order-management/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/purchase-order/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [01a — โมเดลข้อมูล: ตารางคอมเมนต์](/th/inventory/purchase-order/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
- [02 — กติกาทางธุรกิจ](/th/inventory/purchase-order/02-business-rules) — การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ การ posting และกฎ three-way-match
- [03 — User Flow](/th/inventory/purchase-order/03-user-flow) — วงจรชีวิตของเอกสารและสารบัญ persona
  - [Purchaser](/th/inventory/purchase-order/03-user-flow-purchaser)
  - [Procurement Manager](/th/inventory/purchase-order/03-user-flow-procurement-manager)
  - [Vendor](/th/inventory/purchase-order/03-user-flow-vendor)
  - [Receiver](/th/inventory/purchase-order/03-user-flow-receiver)
  - [Finance](/th/inventory/purchase-order/03-user-flow-finance)
  - [Audit / Config](/th/inventory/purchase-order/03-user-flow-audit-config)
- [04 — Test Scenarios](/th/inventory/purchase-order/04-test-scenarios) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ E2E mapping
  - [Purchaser](/th/inventory/purchase-order/04-test-scenarios-purchaser)
  - [Procurement Manager](/th/inventory/purchase-order/04-test-scenarios-procurement-manager)
  - [Vendor](/th/inventory/purchase-order/04-test-scenarios-vendor)
  - [Receiver](/th/inventory/purchase-order/04-test-scenarios-receiver)
  - [Finance](/th/inventory/purchase-order/04-test-scenarios-finance)
  - [Audit / Config](/th/inventory/purchase-order/04-test-scenarios-audit-config)
