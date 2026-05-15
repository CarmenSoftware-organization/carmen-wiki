---
title: ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ฝ่ายการเงิน (Finance)
description: เส้นทางของฝ่ายการเงินในโมดูล purchase-order — three-way match (PO ↔ GRN ↔ invoice), การ post AP, การจัดการสกุลเงิน/FX
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — ฝ่ายการเงิน (Finance)

## 1. บทบาทในโมดูลนี้

persona **ฝ่ายการเงิน (Finance)** ครอบคลุมทั้ง **Finance Officer / Accounts Payable** ผู้รัน invoice match รายวันและ post AP liability และ **Finance Manager** ผู้ใช้สิทธิ์ sign-off ทางการเงินก่อนส่ง PO สำหรับ PO ที่มูลค่าสูงหรือมีความอ่อนไหวด้าน FX ฝ่ายการเงินมี **จุดสัมผัสสองจุดที่แตกต่างกัน** ในวงจรชีวิตของ PO และอยู่คนละปลายของเอกสาร: **การ review ก่อนส่ง** ที่ปลายของขั้นอนุมัติ (Finance Manager ตรวจสกุลเงิน อัตราแลกเปลี่ยน รหัสภาษี และยอดรวมรายบรรทัด ขณะที่ PO ยังอยู่ที่ `po_status = in_progress` ก่อน transition ขั้นสุดท้ายไปยัง `sent` ภายใต้ `PO_POST_004`) และ **three-way match หลังการรับสินค้า** หลังการ post GRN (Finance Officer / AP รับใบแจ้งหนี้จากผู้ขาย ค้นหา PO และ GRN ที่ตรงกัน และรันอัลกอริทึม match ภายใต้ `PO_POST_008` / `PO_POST_009`) three-way match คือ **กิจกรรมหลัก** ของฝ่ายการเงินในโมดูล PO — เป็น control ที่แปลง matched-but-unbilled accrual ให้เป็น payable เคลียร์ GRN accrual และ post AP liability บนใบแจ้งหนี้ผู้ขายที่เชื่อมโยง PO เอง **ไม่** ถูก transition โดย three-way match (`PO_POST_008` ระบุชัดในเรื่องนี้); PO คงสถานะการรับสินค้าที่ไปถึง (`partial`, `completed` หรือ `closed`) และผลลัพธ์การ match อยู่บน record ใบแจ้งหนี้ เมื่อ match ล้มเหลว ความไม่ตรงกันถูก flag กลับไปยัง **Purchaser** เพื่อแก้ไขผ่าน amendment, credit note หรือ void และใบแจ้งหนี้ถูก hold ใน dispute จนกว่าจะกระทบยอดได้

## 2. จุดเริ่มต้นและเส้นทางหลัก

ฝ่ายการเงินมีสองเส้นทาง ซึ่งอธิบายแยกกันด้านล่าง

### 2.1. การ review ก่อนส่ง (Finance Manager)

**จุดเริ่มต้น:** Finance Manager ถูกกำหนดเป็น approver บน workflow stage ที่ตั้งค่าไว้สำหรับการ review ทางการเงิน (โดยทั่วไปคือ stage สุดท้ายก่อนการอนุมัติขั้นสุดท้าย หรือเป็น co-approver ที่ gate ของ PO มูลค่าสูง) เข้าสู่ flow ผ่าน **การแจ้งเตือนใน review queue** เมื่อ PO อยู่ที่ `po_status = in_progress` และ workflow stage cursor มาถึง stage ของ Finance

**เส้นทางหลัก (4 ขั้นตอน):**

1. **เปิด PO จาก review queue** หน้าจอแสดง tab **Financial Details** (`FinancialDetailsTab`) และ tab **General Info**; สิทธิ์ตรวจสอบคือ `PO_AUTH_003` approver check มาตรฐานเทียบกับ `workflow_current_stage`
2. **ตรวจ header ทางการเงิน** — verify `currency_id` เทียบกับสกุลเงินตามสัญญาของผู้ขาย, `exchange_rate` เทียบกับ FX policy ของ tenant (แหล่งของ rate, รอบ refresh, การปัด), payment terms และ flag prepayment / deposit ใด ๆ ยืนยันว่า `total_amount` ในสกุลเงินธุรกรรมและที่เทียบเท่าใน base currency อยู่ภายในเกณฑ์ high-value ที่ Finance Manager กำลัง sign off
3. **ตรวจ financial รายบรรทัด** — subtotal รายบรรทัดทำตาม chain การคำนวณจาก carmen/docs § 1.4 (`Item Subtotal → Discount → Net Amount → Tax → Item Total`); verify `tax_id` / อัตราภาษีของแต่ละบรรทัดตรงกับ tax profile ของสินค้าและการขึ้นทะเบียนภาษีของผู้ขาย, discount มีเหตุผลที่ถูกบันทึก และไม่มีบรรทัดใดถูกปัดเศษไม่สอดคล้อง รวมยอดรายบรรทัดเทียบกับ header roll-up (`PO_CALC_008`–`PO_CALC_011`)
4. **Sign off หรือ send-back**
   - **Sign off:** post stage approval; workflow ก้าวไปยัง stage ถัดไป (หรือไปยัง final approval ซึ่ง trigger `PO_POST_004`: `in_progress → sent` และส่ง PO ให้ผู้ขาย)
   - **Send-back:** post send-back พร้อมเหตุผลภายใต้ `PO_POST_005`; PO กลับไปเป็น `draft` ให้ Purchaser แก้ไข ความเห็น send-back ถูกเขียนใน `tb_purchase_order_comment` และ workflow cursor ถูก reset

### 2.2. Three-way match (Finance Officer / AP)

**จุดเริ่มต้น:** ใบแจ้งหนี้ผู้ขายมาถึง (กระดาษ, PDF หรือ EDI feed) Finance Officer เปิดหน้าจอ AP capture และทำ index ใบแจ้งหนี้กับ PO ผ่านเลขอ้างอิงของผู้ขายและ `po_no` ที่พิมพ์บนใบแจ้งหนี้

**เส้นทางหลัก (7 ขั้นตอน):**

1. **Capture ใบแจ้งหนี้ผู้ขาย** — บันทึกเลขที่ใบแจ้งหนี้, วันที่, ผู้ขาย, สกุลเงิน, รายการสินค้า (สินค้า, จำนวน, ราคาต่อหน่วย), ภาษี และยอดรวม ใบแจ้งหนี้ถูก hold ในสถานะ **pending match** จนกว่า three-way match จะรัน
2. **ค้นหา PO ตามเลขอ้างอิง** `po_no` ที่ capture จะ resolve ไปยังแถว `tb_purchase_order`; PO ต้องอยู่ที่ `po_status ∈ {partial, completed, closed}` สำหรับการ match (PO ที่อยู่ใน `sent` โดยไม่มี GRN ไม่สามารถ match ได้ — ดู Decision Branches) verify ว่าผู้ขายในใบแจ้งหนี้ตรงกับ `tb_purchase_order.vendor_id` และสกุลเงินในใบแจ้งหนี้ตรงกับ `tb_purchase_order.currency_id`
3. **ค้นหา GRN ที่ตรงกัน** Carmen ดึง GRN ทั้งหมดที่ post กับ PO (การเชื่อมโยง GRN-to-PO อยู่ฝั่ง GRN และมองเห็นได้ที่ `GoodsReceiveNoteTab` ของ PO) สำหรับแต่ละบรรทัดในใบแจ้งหนี้ ระบบระบุบรรทัด GRN ที่ครอบคลุมสินค้าที่ถูก invoice บนบรรทัด PO เดียวกัน
4. **รันอัลกอริทึม three-way match** (`PO_POST_008`) สำหรับแต่ละบรรทัดในใบแจ้งหนี้ การ match เปรียบเทียบ:
   - **จำนวน (Quantity):** invoice qty ↔ GRN `accepted_qty` (หรือ `received_qty` ตามนโยบายของ tenant) — ภายใน qty tolerance ที่ตั้งค่าไว้
   - **ราคา (Price):** invoice unit price ↔ PO `unit_price` — ภายใน price tolerance ที่ตั้งค่าไว้
   - **สินค้า / ตัวตนของบรรทัด:** สินค้าในใบแจ้งหนี้ตรงกับสินค้าใน PO/GRN บนบรรทัด PO เดียวกัน
   การ match เป็นรายบรรทัด; การ match ใบแจ้งหนี้โดยรวมจะ **สำเร็จ** ก็ต่อเมื่อทุกบรรทัด match ได้
5. **กรณี match สำเร็จ (`PO_POST_008`):** โมดูล AP **เคลียร์ GRN accrual** (กลับรายการ accrual ของการรับสินค้า inventory เทียบกับบัญชี goods-received-not-invoiced) และ **post AP liability** เทียบกับผู้ขาย — debit inventory accrual / credit vendor payable ในสกุลเงินธุรกรรม พร้อม FX revaluation เทียบ base currency ที่จับ ณ วันที่ใบแจ้งหนี้ ใบแจ้งหนี้ที่ match แล้วถูกย้ายไปสถานะ **approved for payment** PO **ไม่** ถูกเปลี่ยนสถานะจาก event นี้ (ตาม `PO_POST_008`); PO คงสถานะฝั่งการรับสินค้า PO ก้าวสู่ตำแหน่งปลายทางทางพาณิชย์ — การ commit การจัดซื้อกลายเป็น payable แล้ว
6. **กรณี match ล้มเหลว (`PO_POST_009`):** AP hold ใบแจ้งหนี้ในสถานะ **dispute** ความเห็นแบบ `system` ถูก append ใน `tb_purchase_order_comment` บันทึกความล้มเหลว (บรรทัดใด, มิติใด — qty / price / product) และ record deviation ถูกเปิดฝั่งผู้ขาย / vendor-pricelist เพื่อติดตาม ความไม่ตรงกันถูก **flag กลับไปยัง Purchaser** ผ่านการแจ้งเตือน activity-log มาตรฐาน PO ไม่ถูก auto-void; การแก้ไขทำด้วยตนเอง
7. **กระทบยอดและ re-match (เฉพาะเส้นทางล้มเหลว)** เมื่อ Purchaser แก้ไขความไม่ตรงกัน — amendment, credit note จากผู้ขาย, GRN เพิ่มเติม หรือ write-off ผ่านการปิด PO (`PO_POST_011`) — ใบแจ้งหนี้ถูกนำมาเสนอ match อีกครั้ง เมื่อ re-match สะอาด ขั้นตอนที่ 5 จะ fire

## 3. สาขาการตัดสินใจ

- **Match สะอาด — post AP** (`PO_POST_008`): ทุกบรรทัดผ่าน tolerance qty และ price เทียบกับ GRN และ PO ที่ตรงกัน; โมดูล AP เคลียร์ GRN accrual, post AP liability ในสกุลเงินธุรกรรมพร้อม FX entry เทียบ base currency ณ วันที่ใบแจ้งหนี้ และย้ายใบแจ้งหนี้ไปเป็น approved-for-payment PO ไม่เปลี่ยน; ตำแหน่ง matched-but-unbilled บน PO ตอนนี้เป็นศูนย์
- **ความไม่ตรงกันด้านจำนวน — flag กลับให้ Purchaser** (`PO_POST_009`): invoice qty เกิน GRN `accepted_qty` (หรือต่ำกว่า ขึ้นกับทิศทาง) นอก tolerance ใบแจ้งหนี้ถูก hold ใน dispute; ความเห็นถูกเขียน; Purchaser ได้รับแจ้งเตือนเพื่อตามทั้ง credit note (over-invoicing) หรือ GRN เพิ่มเติมเทียบกับการส่งสินค้าครั้งถัดไปของผู้ขาย (under-receipt) สถานะ PO ไม่เปลี่ยน; ยอดคงค้างรายบรรทัดไม่เปลี่ยน
- **ความไม่ตรงกันด้านราคาภายใน tolerance — auto-pass:** invoice unit price แตกต่างจาก PO `unit_price` แต่ผลต่างสัมบูรณ์ / เปอร์เซ็นต์อยู่ภายใน band ที่ตั้งค่า price-tolerance ของ tenant บรรทัดนั้นผ่าน; AP post ที่ราคาในใบแจ้งหนี้; ผลต่างถูก capture เป็น price-variance entry บนการ post AP (debit / credit ในบัญชี purchase price variance) ราคาบรรทัด PO ยังคงเป็นราคาตามสัญญา
- **ความไม่ตรงกันด้านราคานอก tolerance — flag กลับให้ Purchaser** (`PO_POST_009`): invoice unit price อยู่นอก band ของ price-tolerance ใบแจ้งหนี้ถูก hold ใน dispute; ความเห็นถูกเขียน; Purchaser ตามทั้ง credit note (over-billing) หรือ amendment ราคาบน PO ภายใต้ `PO_VAL_016` (การเปลี่ยนแปลงราคาหลัง `sent` ถูกจำกัดและต้องการสิทธิ์ที่เหมาะสม)
- **ไม่มี GRN ที่ตรง — รอการรับ หรือ bounce-back:** ใบแจ้งหนี้ที่ capture ไม่มี GRN ที่ตรงกันบน PO มีสองสาขาย่อย:
  - **ผู้ขายส่งของแล้วแต่ยังไม่ post GRN:** ใบแจ้งหนี้ถูก park ใน pending-match; ฝ่ายการเงินแจ้ง Receiver / Purchaser ให้ตามการ post GRN เมื่อ post แล้ว match จะ re-run อัตโนมัติ
  - **ผู้ขายออก invoice ก่อนการส่ง (หรือสำหรับสินค้าที่ไม่ได้ส่ง):** ฝ่ายการเงิน bounce ใบแจ้งหนี้กลับไปยังผู้ขายพร้อมหนังสือแจ้งไม่รับ; Purchaser ได้รับแจ้งเตือน สถานะ PO ไม่เปลี่ยน
- **สกุลเงินไม่ตรงกันระหว่าง PO และ invoice — FX adjustment posting:** สกุลเงินในใบแจ้งหนี้แตกต่างจาก `tb_purchase_order.currency_id` ถ้า variance ได้รับอนุญาตตามนโยบายของ tenant (เช่น ผู้ขาย dual-currency ตามสัญญา), AP post ใบแจ้งหนี้ในสกุลเงินของใบแจ้งหนี้และ capture FX adjustment entry เทียบกับสกุลเงินตามสัญญาของ PO ที่ rate ของวันที่ใบแจ้งหนี้ ถ้าไม่ได้รับอนุญาต ใบแจ้งหนี้ถูก bounce กลับเป็น currency-mismatch dispute และ flag ให้ Purchaser แก้ไขกับผู้ขาย

## 4. จุดสิ้นสุด / การส่งต่อ

บทบาทของฝ่ายการเงินบนคู่ PO–invoice แต่ละคู่สิ้นสุดที่ **การ post AP** (สำเร็จ) หรือที่ **การปิดการแก้ไขความไม่ตรงกัน** (ล้มเหลว) ตั้งแต่จุดนั้น สถานะใน Carmen จะเป็นหนึ่งใน:

- **AP post แล้ว, PO ที่ terminal:** ใบแจ้งหนี้ approved for payment; GRN accrual ถูกเคลียร์; PO ไม่เปลี่ยนที่สถานะการรับสินค้า (`partial`, `completed` หรือ `closed`) PO ถึงปลายของวงจรชีวิตทางพาณิชย์ / บัญชีสำหรับส่วนที่ match แล้ว สำหรับ PO ที่ partially-fulfilled ฝ่ายการเงินกลับเข้าสู่เส้นทางนี้อีกสำหรับใบแจ้งหนี้แต่ละใบที่ตามมาเทียบกับ PO เดิม จนกว่าการรับสะสมจะถูก invoice ครบหรือ PO ถูกปิด
- **ความไม่ตรงกันถูก flag, PO hold ที่สถานะปัจจุบัน:** ใบแจ้งหนี้ถูก hold ใน dispute (`PO_POST_009`); PO คง `po_status` ปัจจุบัน; ความเป็นเจ้าของในการแก้ไขอยู่ที่ **Purchaser** (loop amendment / credit-note) หรือเมื่อจำเป็นต้อง void อยู่ที่ **Procurement Manager** ภายใต้ `PO_POST_010` เมื่อแก้ไขเสร็จแล้ว ฝ่ายการเงิน re-run match และเส้นทาง success จะ fire
- **Send-back ก่อนส่ง, PO กลับเป็น draft:** การ send-back ของ Finance Manager ในขั้น review routes PO จาก `in_progress → draft` ภายใต้ `PO_POST_005`; ความเป็นเจ้าของกลับไปที่ **Purchaser** เพื่อแก้ไขประเด็นการเงินที่ถูก flag และ resubmit

การส่งต่อ persona คือ: Finance Manager ↔ Purchaser (loop send-back ก่อนส่ง) และ Finance Officer ↔ Purchaser / Procurement Manager (loop ความไม่ตรงกันหลังการรับ) สถานะปลายทางทางพาณิชย์ของ PO สำหรับ run ที่สะอาดคือ `completed` (หรือ `partial` / `closed` ถ้าฝั่งการรับจบในรูปแบบนั้น) พร้อมใบแจ้งหนี้ที่ match ทั้งหมดถูก post แล้ว

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [03-user-flow.md](./03-user-flow.md) — global state machine ของ PO และตาราง handoff ข้าม persona; แถวของ Finance อยู่ที่ปลายขวา (หลัง `completed`, หลัง `closed`, หลัง `partial`)
- ไฟล์พี่น้อง: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — persona ภายในต้นน้ำที่ post GRN ที่ flow นี้ใช้ match; GRN ขับเคลื่อน `received_qty` และ `accepted_qty` ที่ three-way match consume
- ไฟล์พี่น้อง: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — เป้าหมายของการ bounce-back เมื่อ three-way match ล้มเหลว (qty / price / currency discrepancy); เป็นเจ้าของ loop การแก้ไขด้วย amendment / credit-note
- ไฟล์พี่น้อง: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md) — ถือสิทธิ์ override การ void / close เมื่อความไม่ตรงกันแก้ไขได้เฉพาะผ่าน `PO_POST_010` / `PO_POST_011`
- ไฟล์พี่น้อง: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — บุคคลภายนอกที่ออกใบแจ้งหนี้ที่ flow นี้ capture และ match
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) § 5 (Posting Rules) — `PO_POST_004` (การอนุมัติขั้นสุดท้าย / การส่ง), `PO_POST_005` (send-back), `PO_POST_008` (three-way match สำเร็จ), `PO_POST_009` (three-way match ล้มเหลว) และ `PO_POST_011` (ปิดพร้อมตัดยอดที่เหลือ) สำหรับกฎที่อ้างถึงข้างต้น
- โมดูลที่เกี่ยวข้อง: [[good-receive-note]] — โมดูลต้นน้ำที่การ post สร้าง matched-but-unbilled accrual ที่ AP เคลียร์เมื่อ match สำเร็จ
- โมดูลที่เกี่ยวข้อง: [[inventory]] — inventory accrual ที่ถูกเคลียร์เมื่อ match สำเร็จเป็นของ integration inventory / GL; PO contribute เฉพาะ on-order pipeline quantity จนถึง GRN
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่งหลักจาก carmen/docs สำหรับการวิเคราะห์ทางธุรกิจของโมดูล PO การ integrate ฝ่ายการเงิน และ flow ของ three-way match
