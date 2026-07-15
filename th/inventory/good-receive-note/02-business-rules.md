---
title: ใบรับสินค้า (Goods Receive Note) — Business Rules
description: การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ และการ posting ของ good-receive-note พร้อมแก้ไขจังหวะการเปลี่ยนแปลงระบบและข้อกล่าวอ้าง three-way match/AP-journal ที่ไม่พบในซอร์สปัจจุบัน
published: true
date: 2026-07-15T00:00:00.000Z
tags: good-receive-note, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# ใบรับสินค้า (Goods Receive Note) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `GRN_VAL_*` validation &nbsp;·&nbsp; `GRN_AUTH_*` permission &nbsp;·&nbsp; `GRN_CALC_*` calc &nbsp;·&nbsp; `GRN_POST_*` posting &nbsp;·&nbsp; `GRN_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 62 กฎ
> **ผู้ใช้:** ผู้เขียน test + developer — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** ส่วน 5.1 (ที่มีอยู่) มี callout ความคลาดเคลื่อนระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้จับกฎทางธุรกิจในการใช้งานที่ครอบคลุมเอกสาร Goods Receive Note (GRN) ตลอดวงจรชีวิต: input validation ตอน create / edit / save / commit, การคำนวณตัวเงิน (บรรทัดและ header รวม tag โหมดการกระจาย extra-cost), ประตู authorization ตามบทบาทและสถานะเอกสาร, ผลของ posting ในการเปลี่ยนแต่ละครั้งของ `enum_good_received_note_status`, และกฎข้ามโมดูลกับ [purchase-order](/th/inventory/purchase-order), [inventory](/th/inventory/inventory), [vendor-pricelist](/th/inventory/vendor-pricelist) และ [costing](/th/inventory/costing)

> ⚠️ **แก้ไขในรอบนี้ (2026-07-15) — เหตุการณ์ที่เปลี่ยนแปลงระบบคือ `draft → saved` ไม่ใช่ commit** `GoodReceivedNoteLogic.save()` (`good-received-note.logic.ts`) คือจุดที่สร้างแถว `tb_inventory_transaction`, เขียน FIFO / average-cost layer และเพิ่ม `received_qty` (พร้อม `po_status`) ของบรรทัด PO ต้นทาง — ทั้งหมดในธุรกรรมเดียว `GoodReceivedNoteLogic.commit()` (`saved → committed`) เพียงอัปเดต `doc_status` และล็อกเอกสาร — ไม่พบผลกระทบต่อ inventory หรือ PO เพิ่มเติมในซอร์สปัจจุบัน ส่วน 5 ด้านล่างถูกแก้ไขให้สะท้อนสิ่งนี้; `GRN_POST_002`/`GRN_POST_003`/`GRN_POST_004` ในเวอร์ชันก่อนหน้าของหน้านี้สลับผลของสองการเปลี่ยนสถานะนี้กลับกัน
>
> ⚠️ **ยังไม่ยืนยัน / ไม่พบในซอร์สปัจจุบัน — three-way match และ AP/GL posting** การค้นหาทั่ว repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `journal`, `ledger`, `accounts_payable`, `three-way`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` ให้ผล **ศูนย์รายการที่ตรงกัน** ไม่มีหน้าจอบันทึกใบกำกับผู้ขาย ไม่มี AP-posting endpoint และไม่มี match algorithm ในซอร์สปัจจุบัน — ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วในโมดูล `purchase-order` กฎด้านล่างที่เคยบรรยายสิ่งนี้ (เดิมคือ `GRN_POST_006`–`GRN_POST_009`, `GRN_XMOD_007`) ถูกทำเครื่องหมายว่า "ยังไม่ implement" แทนที่จะลบทิ้ง เพื่อให้ rule-ID ที่อ้างอิงจากหน้าอื่นยัง resolve ไปยังคำอธิบายได้

มีสองประเด็นเชิงโครงสร้างที่ทาบทาทับทุกกฎด้านล่างและควรย้ำตั้งแต่ต้น **อันแรก** lot number, expiry date และข้อมูล FIFO / average-cost layer **ไม่ได้อยู่บนบรรทัด GRN** — อยู่บน `tb_inventory_transaction_detail` และถึงผ่าน `tb_good_received_note_detail_item.inventory_transaction_id` GRN detail_item คือ cursor เหตุการณ์รับ; inventory transaction คือ lot store (ดู [good-receive-note/01-data-model](/th/inventory/good-receive-note/01-data-model) § 5 รายการ 3) ดังนั้นกฎที่อ้างอิง "lot info" บังคับ linkage กับ inventory transaction ที่ valid ตอน **save** ไม่ใช่การตรวจระดับคอลัมน์บน GRN **อันที่สอง** extra-cost allocation มี tag โหมดการกระจาย **สาม** โหมดใน model Prisma อย่างเป็นทางการ — `manual`, `by_value` และ `by_qty` — ไม่ใช่ห้า (`MANUAL`, `BY_VALUE`, `BY_QUANTITY`, `BY_WEIGHT`, `BY_VOLUME`) ที่ไฟล์ carmen/docs บางส่วนอ้าง; `by_weight` และ `by_volume` ไม่ได้ implement ที่ schema level **ยังไม่ยืนยัน:** ไม่พบโค้ดฝั่ง server ที่แบ่งจำนวนเงิน extra cost ข้ามบรรทัด GRN ตาม `by_value` / `by_qty` จริง หรือป้อนผลลัพธ์เข้าสู่การคำนวณ cost layer — panel extra-cost ฝั่ง frontend รับเพียงจำนวนเงินรวมต่อประเภทโดยมีโหมดเป็นเพียง label และ `createInventoryTransactions` อ่านเฉพาะยอด net ของบรรทัดเอง ให้ถือว่าตัวอย่างการคำนวณ allocation ในส่วน 3.1 เป็นภาพประกอบเจตนาการออกแบบของ enum Prisma ไม่ใช่พฤติกรรมที่ยืนยันแล้ว

## 2. กฎ Validation

Rule ID เป็น `GRN_VAL_NNN` กฎ header (001–005) และกฎ line (006–010) ถูกตรวจตอน save **แก้ไขในรอบนี้:** แถว `GRN_VAL_011`–`GRN_VAL_014` เขียนไว้ด้านล่างเป็นประตู "at commit" (ตรงกับการอ่านกฎก่อนหน้า) แต่ผลข้างเคียงของ posting จริงที่กฎเหล่านี้บรรยาย (การสร้าง inventory transaction, การใช้ po_status) เกิดขึ้นตอนเปลี่ยนสถานะ **`draft → saved`** ใน `GoodReceivedNoteLogic.save()` ไม่ใช่ตอน `commit()` — หน้านี้ยังไม่ได้ตรวจสอบซ้ำอย่างละเอียดในรอบนี้ว่ากฎรวม 4 ข้อไหนถูกบังคับใช้โดยโค้ดตอน save จริง ๆ เทียบกับที่ยังเหลือเป็นประตูตอน commit (ซึ่งตอนนี้แทบไม่มีผลอะไรแล้ว) — ให้ถือว่าคอลัมน์ "บังคับใช้เมื่อ" ด้านล่างยังไม่ยืนยันสำหรับแถว 011–014 จนกว่าจะอ่าน call site ของ validation อย่างละเอียดกว่านี้

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | ข้อผิดพลาด / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `GRN_VAL_001` | `tb_good_received_note.vendor_id` reference แถว `tb_vendor` ที่ไม่ถูก soft-delete จำเป็นภายในเวลา submit; nullable บน draft ต้น ๆ เพื่อรองรับการรวมหลาย PO ที่ resolve vendor ทีหลัง | Save (warn), commit (block) | ปฏิเสธตอน commit ด้วย "Vendor is required and must be from the approved vendor list." |
| `GRN_VAL_002` | `tb_good_received_note.currency_id` reference `tb_currency` ที่ไม่ถูก soft-delete; `exchange_rate > 0` และ `exchange_rate_date` ถูกตั้ง | Create, edit, commit | ปฏิเสธด้วย "Transaction currency and a positive exchange rate are required." |
| `GRN_VAL_003` | `grn_date` (วันที่รับ) ไม่ null และไม่อยู่ในอนาคตเกินกว่า tolerance ของ tenant; เมื่อมีอยู่ `invoice_date <= grn_date + tenant_invoice_grace_days` | Edit, commit | ปฏิเสธด้วย "Receipt date is required and invoice date must be consistent with the receipt." |
| `GRN_VAL_004` | เมื่อ `doc_type = purchase_order` มีอย่างน้อยหนึ่งบรรทัดที่บรรจุ `purchase_order_detail_id` เมื่อ `doc_type = manual` ไม่มีบรรทัดใดมี `purchase_order_detail_id` | Save line, commit | ปฏิเสธด้วย "PO reference is required for PO-sourced GRNs and must be absent for manual GRNs." |
| `GRN_VAL_005` | คู่ `(invoice_no, vendor_id)` ไม่ซ้ำกันระหว่าง GRN ที่ไม่ถูก soft-delete (BR-01 เก่า: invoice-uniqueness สำหรับลำดับธุรกรรม) | Commit | ปฏิเสธด้วย "An invoice with this number has already been received from this vendor." |
| `GRN_VAL_006` | แต่ละแถว `tb_good_received_note_detail` มี `product_id` และ `location_id` ที่ไม่ null อ้างอิงแถวที่ active ไม่ถูก soft-delete ใน `tb_product` / `tb_location` | Save line, commit | ปฏิเสธบรรทัดด้วย "Product and receiving location are required on every GRN line." |
| `GRN_VAL_007` | แต่ละแถว `tb_good_received_note_detail` มีอย่างน้อยหนึ่ง `tb_good_received_note_detail_item` ที่ไม่ถูก soft-delete (แถวเหตุการณ์รับ); บนแต่ละ detail_item, `received_qty > 0` (paid receipt) **หรือ** `foc_qty > 0` (free-of-charge receipt) บรรทัดที่ไม่มีทั้งคู่ไม่ valid | Save line, commit | ปฏิเสธบรรทัดด้วย "Each line must record either a received quantity or a free-of-charge quantity greater than zero." |
| `GRN_VAL_008` | บนทุก detail_item, `received_unit_id` ไม่ null และ `received_unit_conversion_factor > 0`; `received_base_qty = Round(received_qty × received_unit_conversion_factor, 3)` กฎเดียวกันใช้กับ triple `order_*` และ `foc_*` เมื่อ qty ของพวกมันไม่ใช่ศูนย์ | Save line, commit | ปฏิเสธบรรทัดด้วย "Each receipt event must specify a valid receiving UoM with a positive conversion factor." |
| `GRN_VAL_009` | เมื่อบรรทัด detail reference บรรทัด PO (`purchase_order_detail_id` ตั้งไว้) หน่วยรับตรงกับ `order_unit_id` ของบรรทัด PO หรือมี conversion factor ไปยัง `base_unit_id` เดียวกันกับบรรทัด PO; ปริมาณที่รับ (ใน base UoM) ไม่เกิน `(order_qty − received_qty − cancelled_qty)` บนบรรทัด PO (pending qty) tolerance รับเกินของ tenant อาจผ่อนคลาย | Save line, commit | ปฏิเสธบรรทัดด้วย "Receipt quantity exceeds the pending quantity on PO line `<po_no>:<seq>`; over-receipt tolerance not enabled." |
| `GRN_VAL_010` | บนทุก detail_item, ฟิลด์ตัวเงินไม่เป็นลบ: `tax_rate >= 0`, `discount_rate >= 0`, `base_price >= 0` เมื่อ `is_tax_adjustment = true` หรือ `is_discount_adjustment = true` ต้อง persist override amount ชัดเจน | Save line, commit | ปฏิเสธบรรทัดด้วย "Tax / discount rate and unit price must be non-negative; manual override requires an explicit amount." |
| `GRN_VAL_011` | ตอน commit GRN มีอย่างน้อยหนึ่งแถว `tb_good_received_note_detail` ที่ไม่ถูก soft-delete และแถวนั้นมีอย่างน้อยหนึ่ง detail_item ที่ไม่ถูก soft-delete | Commit | ปฏิเสธด้วย "GRN must contain at least one line with a recorded receipt event before it can be committed." |
| `GRN_VAL_012` | ตอน commit ทุก detail_item ที่เพิ่ม inventory (`received_qty > 0` หรือ `foc_qty > 0` และสินค้าเป็นประเภท `inventory` — ไม่ใช่ consignment-only ไม่ใช่ non-inventory expense) ได้สร้างแถว `tb_inventory_transaction` ที่ valid ซึ่งลูก `tb_inventory_transaction_detail` บรรจุ `lot_no` ที่ไม่ null (ระบบสร้างหรือผู้ใช้ใส่) และเมื่อสินค้า flag perishable มี `expiry_date` นี่คือการตรวจ linkage ไม่ใช่การตรวจ column-on-GRN (ดูส่วน 1 จุด 1) | Commit | ปฏิเสธด้วย "Lot information is required for inventory items at commit; line `<seq>` is missing lot data on the linked inventory transaction." |
| `GRN_VAL_013` | ตอน commit สำหรับทุกบรรทัดที่มาจาก PO (`purchase_order_detail_id` ตั้งไว้) PO ที่ reference มี `po_status ∈ {sent, partial}` บรรทัดที่ PO มีสถานะ `voided`, `closed`, `completed`, `draft` หรือ `in_progress` post ไม่ได้ | Commit | ปฏิเสธด้วย "Cannot receive against PO `<po_no>`: PO status `<status>` does not permit receiving. Voided POs are rejected outright." |
| `GRN_VAL_014` | extra-cost allocation เมื่อมี extra cost อยู่ ต้องเสร็จก่อน commit: ทุกแถว `tb_extra_cost` ผูกกับ GRN นี้มี `allocate_extra_cost_type = manual` พร้อม allocation ต่อ item ที่ persist รวมเท่ากับ extra-cost net amount หรือมี `by_value` / `by_qty` และ application คำนวณและ persist allocation ลงใน snapshot การเงินต่อ item แล้ว extra cost ที่ยังไม่ allocate block commit | Commit | ปฏิเสธด้วย "Extra costs must be allocated to lines before commit." (PRD §5.4 / `BR-EC-01`) |

## 3. กฎการคำนวณ

ค่าเงินทั้งหมดเก็บเป็น `Decimal(20, 5)` ที่ระดับแถว; **อัตรา** ภาษีและส่วนลดเก็บเป็น `Decimal(15, 5)`; อัตราแลกเปลี่ยนเป็น `Decimal(15, 5)` บน header GRN การปัดเศษเพื่อแสดงเป็น half-up 2 ทศนิยมสำหรับจำนวนเงิน 3 ทศนิยมสำหรับปริมาณ และ 5 ทศนิยมสำหรับอัตรา การคำนวณกลางมักอ่านค่าที่ปัดของขั้นตอนก่อนหน้าเสมอ (ตรงกับ catalog PR / PO ที่ GRN technical spec สืบทอดเป็น `GRN_041`–`GRN_065`)

Rule ID เป็น `GRN_CALC_NNN`

| Rule ID | สูตร |
| ------- | ------- |
| `GRN_CALC_001` (line subtotal) | `sub_total_price = Round(base_price × received_qty, 2)` ในสกุลธุรกรรม FOC qty ไม่นับใน `sub_total_price` (PRD §3.4.5.5; ส่วน FOC บันทึกเป็นแถว detail_item แยกพร้อม `foc_qty` แต่ไม่มีส่วนช่วยราคา) |
| `GRN_CALC_002` (line discount) | `discount_amount = Round(Round(sub_total_price, 2) × discount_rate, 2)` เว้นแต่ `is_discount_adjustment = true` ในกรณีนั้น override ที่ persist ชนะ |
| `GRN_CALC_003` (line net, tax-exclusive pricing) | `net_amount = Round(Round(sub_total_price, 2) − Round(discount_amount, 2), 2)` ภาษีคือ `tax_amount = Round(Round(net_amount, 2) × tax_rate, 2)` เว้นแต่ `is_tax_adjustment = true` |
| `GRN_CALC_004` (line tax-inclusive variant) | เมื่อราคาต่อหน่วยที่ใส่รวมภาษีอยู่แล้ว: `tax_amount = Round((sub_total_price − discount_amount) × tax_rate / (100 + tax_rate × 100), 2)`; `net_amount = sub_total_price − discount_amount − tax_amount` `total_price` ไม่เปลี่ยน (PRD §3.4.5.5) |
| `GRN_CALC_005` (line total) | `total_price = Round(Round(net_amount, 2) + Round(tax_amount, 2), 2)` Tax-inclusive variant ต้องสอดคล้อง `total_price = sub_total_price − discount_amount` |
| `GRN_CALC_006` (variance) | `variance_qty = received_qty − order_qty` (ต่อ detail_item ใน receiving UoM) variance ลบเป็น partial receipt; บวกเป็น over-receipt (ขึ้นกับ `GRN_VAL_009`) variance ไม่เขียนกลับลงแถว GRN — ปรากฏใน view เปรียบเทียบระหว่าง `order_qty` กับ `received_qty` ของ detail_item |
| `GRN_CALC_007` (header roll-up) | `tb_good_received_note.net_amount = Round(Σ Round(detail_item.net_amount, 2), 2)`; `total_amount = Round(Σ Round(detail_item.total_price, 2), 2)` บวกภาษีของ extra-cost ที่ allocate (ดู `GRN_CALC_010`) Roll-up คำนวณข้าม detail_item ที่ active ไม่ถูก soft-delete ของบรรทัดที่ active |
| `GRN_CALC_008` (base conversion) | สำหรับแต่ละคอลัมน์เงิน `X` ในสกุลธุรกรรม `base_X = Round(Round(X, 2) × exchange_rate (5 dp), 2)` เจาะจง `base_price`, `base_sub_total_price`, `base_discount_amount`, `base_net_amount`, `base_tax_amount`, `base_total_price`; header GRN บรรจุ roll-up `base_net_amount` และ `base_total_amount` |
| `GRN_CALC_009` (extra-cost — `manual`) | ผู้ใช้ใส่จำนวน allocation ต่อบรรทัด ผลรวมของ allocation ข้ามบรรทัดต้องเท่ากับ `tb_extra_cost.net_amount` (tolerance ≤ `0.01` ในสกุลธุรกรรม) แต่ละจำนวนที่ allocate เขียนลงใน snapshot การเงินต่อ item และรวมใน `Last Cost` (PRD §3.4.5.5) |
| `GRN_CALC_010` (extra-cost — `by_value`) | `line_allocation = Round(Round(extra_cost_total, 2) × (line.net_amount / Σ line.net_amount), 2)` บรรทัดสุดท้ายซับเศษปัดเหลือเพื่อให้ `Σ allocations = extra_cost_total` (ภายใน ≤ `0.01`) |
| `GRN_CALC_011` (extra-cost — `by_qty`) | `line_allocation = Round(Round(extra_cost_total, 2) × (line.received_base_qty / Σ line.received_base_qty), 2)` รวม qty ใน base UoM เพราะบรรทัดอาจใช้ receiving UoM ต่างกัน กฎเศษบรรทัดสุดท้ายเหมือน `by_value` |
| `GRN_CALC_012` (Last Cost — feed costing) | `Last Cost per unit = Round((line.net_amount + Σ line.extra_cost_allocations) / (received_qty + foc_qty), 5)` นี่คือสิ่งที่ไหลไปยัง FIFO / average-cost layer ใน [costing](/th/inventory/costing) ผ่าน `tb_inventory_transaction_cost_layer.cost_per_unit` ที่ link หมายเหตุ: FOC qty รวมในตัวหารสำหรับ Last Cost แต่ไม่รวมจาก `Last Price` (ซึ่งคือ `net_amount / received_qty`) |
| `GRN_CALC_013` (rounding mode) | การปัดเศษทั้งหมดเป็น half-up ไปยังความแม่นยำของคอลัมน์ (สกุลเงิน 2dp, ปริมาณ 3dp, อัตรา / FX 5dp) |

### 3.1 ตัวอย่างคำนวณ (สกุลธุรกรรม ฿ THB, tax-exclusive pricing)

สองบรรทัด vendor ใน THB, `exchange_rate = 1.00000` (ไม่มี FX), หนึ่งบรรทัด extra-cost allocate `by_value`

- **บรรทัด 1** (หนึ่ง detail_item): `received_qty = 10.000`, `base_price = ฿125.50`, `discount_rate = 5%`, `tax_rate = 7%`
  - `sub_total_price = Round(125.50 × 10.000, 2) = ฿1,255.00`
  - `discount_amount = Round(1,255.00 × 0.05, 2) = ฿62.75`
  - `net_amount = Round(1,255.00 − 62.75, 2) = ฿1,192.25`
  - `tax_amount = Round(1,192.25 × 0.07, 2) = ฿83.46`
  - `total_price = Round(1,192.25 + 83.46, 2) = ฿1,275.71`
- **บรรทัด 2** (หนึ่ง detail_item): `received_qty = 4.000`, `base_price = ฿89.00`, `discount_rate = 0%`, `tax_rate = 7%`
  - `sub_total_price = ฿356.00`; `discount_amount = ฿0.00`; `net_amount = ฿356.00`
  - `tax_amount = Round(356.00 × 0.07, 2) = ฿24.92`
  - `total_price = ฿380.92`
- **Extra cost** (`tb_extra_cost.net_amount = ฿200.00`, `allocate_extra_cost_type = by_value`):
  - `Σ line.net_amount = 1,192.25 + 356.00 = ฿1,548.25`
  - บรรทัด 1 allocation: `Round(200.00 × (1,192.25 / 1,548.25), 2) = Round(154.01..., 2) = ฿154.01`
  - บรรทัด 2 allocation: เศษ = `200.00 − 154.01 = ฿45.99`
- **Header roll-up**:
  - `net_amount = Round(1,192.25 + 356.00, 2) = ฿1,548.25`
  - `total_amount = Round(1,275.71 + 380.92, 2) = ฿1,656.63` (ไม่รวมภาษี extra-cost; ถ้า extra cost เองมี 7% VAT `฿14.00`, header `total_amount` อ่าน `฿1,670.63`)
- **Last Cost feed สู่ inventory** (บรรทัด 1, สมมติ `foc_qty = 0`): `(1,192.25 + 154.01) / 10.000 = ฿134.626 per base unit` นี่คือสิ่งที่ `tb_inventory_transaction_cost_layer.cost_per_unit` ที่ link รับ; การคำนวณ FIFO และ average-cost ปลายทางบริโภค

ถ้าบรรทัด 1 มี detail_item FOC parallel ด้วย `foc_qty = 1.000` `Last Cost` กลายเป็น `(1,192.25 + 154.01) / (10.000 + 1.000) = ฿122.388` — FOC qty เข้า cost layer ที่ราคาต่อหน่วยที่เจือจาง

## 4. กฎ Authorization

Rule ID เป็น `GRN_AUTH_NNN` Authorization บังคับใช้โดย RBAC ที่ API layer บวก workflow-stage gating ผ่าน `tb_good_received_note.user_action.execute` ชื่อบทบาทสะท้อนตาราง RBAC ของ carmen/docs (Receiving Clerk / Inventory Manager / Finance Officer / Procurement Officer / AP Clerk) กฎ Receiver ≠ Purchaser บังคับใช้ตอน commit ไม่ใช่ตอน create

| Rule ID | Subject | สิทธิ์ | ข้อจำกัด |
| ------- | ------- | ----- | ---------- |
| `GRN_AUTH_001` | Receiving Clerk (Receiver) | สร้าง GRN (`doc_status = draft`) | ทั้ง `purchase_order` และ `manual` `doc_type` สำหรับ `purchase_order` PO ที่ reference ต้องอยู่ที่ `sent` หรือ `partial` (`PO_AUTH_008` ฝั่ง PO; `GRN_VAL_013` ฝั่ง GRN) |
| `GRN_AUTH_002` | Receiving Clerk | แก้ไข GRN เพิ่ม / แก้บรรทัดและ detail_item | เฉพาะขณะ `doc_status ∈ {draft, saved}` เมื่อ `committed` แล้ว GRN ล็อก |
| `GRN_AUTH_003` | Receiving Clerk | Save (`draft → saved`) | ผ่าน validation ส่วน 2 จาก `GRN_VAL_001`–`GRN_VAL_010` **นี่คือเหตุการณ์ posting** (ส่วน 5): inventory transaction, cost layer และการเพิ่ม `received_qty` ของ PO ทั้งหมดถูกเขียนโดย `save()` ไม่ใช่โดย commit |
| `GRN_AUTH_004` | Inventory Manager (Store Manager) | แก้ไข / กระทบยอด GRN ที่ `saved` | Inventory Manager แก้ไขปริมาณ สถานที่ และข้อมูล lot ได้ขณะ `doc_status = saved` **ยังไม่ยืนยัน:** เวอร์ชันก่อนหน้าของแถวนี้ระบุว่าจะกลับ GRN ไปที่ `draft` เมื่อมีการเปลี่ยนแปลง header ที่สำคัญ — ไม่พบโค้ดที่ทำเช่นนั้นในรอบตรวจสอบนี้ |
| `GRN_AUTH_005` | Inventory Manager | Commit (`saved → committed`) | ต้องการ `doc_status = saved`; เมื่อสำเร็จเปลี่ยนเฉพาะ `doc_status` (และ `doc_version`) — ไม่พบ validation at-commit เพิ่มเติมจากส่วน 2, การเขียน inventory หรือผลกระทบฝั่ง PO ใน `GoodReceivedNoteLogic.commit()` **ยังไม่ยืนยัน:** ไม่พบเส้นทาง self-commit สำหรับ Receiving Clerk ที่ GRN ต่ำกว่า threshold ของ tenant — ไม่มีแนวคิด "threshold" ใดในโมดูลนี้ทั้ง backend และ frontend (ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วสำหรับ `PO_AUTH_004` ของ PO) |
| `GRN_AUTH_006` | ~~Inventory Manager — Batch commit~~ | **ยังไม่ implement** | ไม่พบ batch-commit endpoint, controller method หรือ UI เลือก batch ฝั่ง frontend ที่ใดใน `good-received-note.service.ts`, `good-received-note.logic.ts`, `good-received-note.controller.ts` หรือ route ของ GRN ฝั่ง frontend ให้ถือว่าข้อความ "batch commit" ที่ปรากฏในโมดูลนี้เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ implement แล้ว |
| `GRN_AUTH_007` | ~~Finance Officer / AP Clerk — extra-cost allocation ก่อน AP-posting~~ | **ยังไม่ยืนยัน — ไม่พบบทบาท Finance หรือประตู AP-posting** | `enum_stage_role` (enum บทบาท stage ของ workflow ที่ใช้ร่วมกับ PR/PO) ไม่มีสมาชิก `finance` และไม่มีโค้ดที่ gate การแก้ไข extra-cost allocation ตามสถานะ AP-posting (ไม่มีสถานะ AP-posting ให้ gate ด้วยซ้ำ — ดู Discrepancy note ด้านบน) สิ่งที่ยืนยันได้คือ: method `update()` ของ service สามารถเขียนทับแถว `tb_extra_cost` / `tb_extra_cost_detail` ของ GRN ใดก็ได้ที่เรียกใช้ โดยไม่พบ guard ตาม `doc_status` ใน code path นั้นเช่นกัน |
| `GRN_AUTH_008` | Inventory Manager | Void (`draft → voided` หรือ `saved → voided`) | **แก้ไขในรอบนี้** frontend แสดงปุ่ม Void เฉพาะเมื่อ `doc_status ∉ {committed, voided}` (`grn-header.tsx`: `canEdit = !isCommitted && !isVoid`) ซึ่งจำกัดผลให้เหลือ `draft` / `saved` ใน UI แต่ endpoint `/void` ฝั่ง backend (`GoodReceivedNoteService.voidGrnById`) **ไม่มีเงื่อนไข `doc_status` ของตัวเอง** — บล็อกเฉพาะการ void ซ้ำ GRN ที่ `voided` แล้ว จึงเป็น guard ฝั่ง client เท่านั้น ไม่ใช่กฎที่บังคับใช้ที่ server แยกต่างหาก `/reject` (`GoodReceivedNoteLogic.reject`) **บังคับใช้** `doc_status ∈ {draft, saved}` ที่ server จริง endpoint ทั้งสองไม่ reverse ผลกระทบต่อ inventory, cost layer หรือ PO ใดๆ ที่เขียนไปแล้วตอน save |
| `GRN_AUTH_009` | ผู้ใช้ที่ล็อกอินแล้วทุกบทบาท | View, export report | Read-only ข้ามทุกสถานะ |
| `GRN_AUTH_010` | ~~การแยกหน้าที่ — Receiver ≠ Purchaser~~ | **ยังไม่ยืนยัน — ไม่พบโค้ดที่ตรงกัน** | การค้นหาใน `good-received-note.service.ts` และ `good-received-note.logic.ts` สำหรับการตรวจ `buyer_id` cross-check หรือ guard การแยกหน้าที่ตอน save/commit ไม่พบอะไรเลย ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วสำหรับ `PO_AUTH_010` ของโมดูล PO ให้ถือว่านี่เป็นเจตนาควบคุม ไม่ใช่กฎที่บังคับใช้จนกว่าจะพบ guard ที่ตรงกัน |
| `GRN_AUTH_011` | Authorization derive จาก Workflow | Action ที่ stage-gated | ชุดผู้ใช้ใน `tb_good_received_note.user_action.execute` ที่ `workflow_current_stage` ปัจจุบันมีเจตนาเป็นเกทการเลื่อนเอกสาร; หน้านี้ยังไม่ได้ยืนยันอย่างอิสระว่า server บังคับใช้ชุดนั้นสำหรับโมดูล good-received-note ในรอบตรวจสอบนี้ |

## 5. กฎ Posting

ค่าสถานะคือสมาชิกตามตัวอักษรของ `enum_good_received_note_status` ที่เอกสารไว้ใน [good-receive-note/01-data-model](/th/inventory/good-receive-note/01-data-model) § 4: **`draft`**, **`saved`**, **`committed`**, **`voided`** วงจรชีวิตเต็มคือ `draft → saved → committed` พร้อม `voided` เป็นทางออกบริหารจาก `draft` หรือ `saved` **แก้ไขในรอบนี้:** เหตุการณ์ posting เดียวคือการเปลี่ยน **`draft → saved`** — `GoodReceivedNoteLogic.save()` คือจุดที่เขียน inventory transaction, cost layer และการเพิ่ม `received_qty` ของ PO `saved → committed` เพียงอัปเดต `doc_status`/`doc_version` และล็อกเอกสาร — ไม่พบ posting เพิ่มเติมใน transition นั้นในซอร์สปัจจุบัน ไม่มี `pending_approval`, `approved`, `rejected`, `closed` หรือ `cancelled` ที่ระดับ Prisma (enum `GRNStatus` ของ carmen/docs เก่าแตกต่าง — ดู [good-receive-note/01-data-model](/th/inventory/good-receive-note/01-data-model) § 5 รายการ 1)

Rule ID เป็น `GRN_POST_NNN`

| Rule ID | Transition / Event | ผลกระทบ |
| ------- | ------------------ | ------- |
| `GRN_POST_001` | Create (→ `draft`) | Insert `tb_good_received_note` ด้วย `doc_status = draft`, `doc_version = 0`, `net_amount = base_net_amount = total_amount = base_total_amount = 0` ไม่มี inventory, GL, PO ผลกระทบ |
| `GRN_POST_002` | Save (`draft → saved`) — **เหตุการณ์ posting** | `GoodReceivedNoteLogic.save()`: ตั้ง `doc_status = saved` จากนั้นในธุรกรรมเดียวกัน (a) สร้าง inventory transaction ตาม `GRN_POST_004` และ (b) ถ้า `doc_type = purchase_order` เพิ่มฝั่ง PO ตาม `GRN_POST_005` **แก้ไขในรอบนี้:** เวอร์ชันก่อนหน้าของแถวนี้ระบุว่า save "ยังไม่มีผลกระทบ inventory หรือ GL" และ commit คือเหตุการณ์ posting — โค้ดจริงแสดงตรงกันข้าม: `save()` คือจุดที่สต๊อกและ PO เพิ่มเกิดขึ้น; `commit()` (`GRN_POST_003`) ไม่ทำทั้งสองอย่าง |
| `GRN_POST_003` | Commit (`saved → committed`) | `GoodReceivedNoteLogic.commit()`: ต้องการ `doc_status = saved` จากนั้นตั้ง `doc_status = committed` และเพิ่ม `doc_version` **ไม่พบผลกระทบอื่นใด** — ไม่มีการเขียน inventory เพิ่ม ไม่มีการอัปเดตฝั่ง PO ไม่มี journal entry บทบาทของมันคือล็อกเอกสาร (`GRN_AUTH_002`: การแก้ไขอนุญาตเฉพาะขณะ `doc_status ∈ {draft, saved}`) |
| `GRN_POST_004` | Save — ฝั่ง inventory (cross-ref [inventory](/th/inventory/inventory)) | สำหรับแต่ละ detail_item insert `tb_inventory_transaction` (ประเภท `good_received_note` — `enum_transaction_type` ไม่มีสมาชิก "Stock In" / "Consignment In" / "Non-Inventory" แยกต่างหาก) บวกลูก `tb_inventory_transaction_detail` ที่บรรจุ `lot_no`, `expiry_date`, `cost_per_unit` Stamp id ที่ insert บน `tb_good_received_note_detail_item.inventory_transaction_id` On-hand ที่ `(location_id, product_id)` เพิ่มด้วย `received_base_qty` แถว cost-layer ใน `tb_inventory_transaction_cost_layer` ถูกสร้างตามวิธี costing ของ tenant (FIFO หรือ moving-average) **ยังไม่ยืนยัน:** ไม่พบการจัดการแยกตาม `post_type` (`ap` / `consignment` / `cash`) ของ header ใน `inventory-transaction.service.ts` — การรับ GRN ทุกใบดูเหมือนจะ post ผ่านเส้นทางเดียวกันไม่ว่า `post_type` จะเป็นอะไร |
| `GRN_POST_005` | Save — ฝั่ง PO (cross-ref [purchase-order](/th/inventory/purchase-order)) | สำหรับแต่ละบรรทัดที่มี junction reference PO↔PR เพิ่ม `received_qty` ของแถว junction จากนั้น (สำหรับบรรทัดที่ `purchase_order_detail_id` ตั้งไว้) เพิ่ม `tb_purchase_order_detail.received_qty` ด้วย `received_qty` (`GoodReceivedNoteLogic.updatePurchaseOrderReceiving`) ต่อ PO ที่กระทบ ถ้าทุกบรรทัด active เข้าเงื่อนไข `received_qty ≥ order_qty − cancelled_qty` ตั้ง `po_status = completed`; ไม่เช่นนั้น `po_status = partial` |
| `GRN_POST_006` | ~~Commit — GL accrual สำหรับ AP-pending~~ | **ยังไม่ implement** ไม่มีโค้ด journal-entry, ledger หรือ GL-account ใดๆ ใน `good-received-note.service.ts` / `good-received-note.logic.ts` — การค้นหาทั่ว repo สำหรับ `journal`, `ledger`, และ `accounts_payable` ให้ผลศูนย์รายการ ให้ถือว่า "Dr Inventory / Cr GRN Clearing" เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ implement แล้ว |
| `GRN_POST_007` | ~~Commit — anchor three-way-match~~ | **ยังไม่ implement** ไม่พบ vendor-invoice entity, หน้าจอบันทึก หรือ match algorithm ใน `carmen-turborepo-backend-v2` หรือ `carmen-inventory-frontend-react` (คำค้น `three-way`, `vendor_invoice`, `VendorInvoice`, `tb_invoice` — ศูนย์รายการ) ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วในโมดูล `purchase-order` |
| `GRN_POST_008` | ~~Three-way match สำเร็จ~~ | **ยังไม่ implement** ข้อสรุปเดียวกับ `GRN_POST_007` — ไม่มีโมดูล AP ในซอร์สปัจจุบันที่จะรัน match นี้ |
| `GRN_POST_009` | ~~Three-way match ล้มเหลว~~ | **ยังไม่ implement** ข้อสรุปเดียวกับ `GRN_POST_007`/`GRN_POST_008` |
| `GRN_POST_010` | Void (endpoint `/void`, พฤติกรรมจริง) | `GoodReceivedNoteService.voidGrnById()`: ตั้ง `doc_status = voided`; เงื่อนไข**เดียว**ที่ตรวจฝั่ง server คือ GRN ยังไม่ `voided` — **ไม่มี guard `doc_status ∈ {draft, saved}` ฝั่ง server บน endpoint นี้** endpoint `/reject` แยกต่างหาก (`GoodReceivedNoteLogic.reject()`) บังคับใช้ `doc_status ∈ {draft, saved}` จริง endpoint ทั้งสองไม่ reverse inventory transaction, cost layer หรือการเพิ่ม `received_qty` ของ PO ที่เขียนไปแล้วตอน save — การ void ไม่ชดเชยอะไรกลับ **แก้ไขในรอบนี้:** เวอร์ชันก่อนหน้าของแถวนี้ระบุว่า "void GRN ที่ committed ไม่อนุญาต" และสื่อว่ามีการ reverse เกิดขึ้น; frontend ซ่อนปุ่ม Void เมื่อ `doc_status = committed` (`canEdit = !isCommitted && !isVoid` ใน `grn-header.tsx`) แต่นั่นเป็นข้อจำกัดฝั่ง UI เท่านั้น ไม่ใช่กฎที่ endpoint `/void` เองบังคับใช้ |
| `GRN_POST_011` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `draft` (`GoodReceivedNoteService.delete()` ปฏิเสธสถานะอื่นทั้งหมด) แถวยังอยู่ในฐานข้อมูล; index `@@unique([grn_no, deleted_at])` ให้ GRN ใหม่ใช้ `grn_no` เดิมได้ |
| `GRN_POST_012` | ~~End-of-period auto-commit~~ | **ยังไม่ implement** ไม่พบโค้ด batch-commit หรือ scheduled-job ใดใน `carmen-turborepo-backend-v2` สำหรับโมดูลนี้ (ไม่มี cron entry ไม่มี batch endpoint) ให้ถือว่า "scheduled sweep commit GRN ที่ saved ค้างอยู่" เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ implement แล้ว |

State diagram (Prisma-canonical):

```
[*] → draft → saved → committed
        ↓       ↓
       voided  voided
```

`committed` และ `voided` เป็น terminal `draft` ยอมรับ soft-delete

### 5.1 วงจรชีวิตสถานะ — การแมพ Live UI กับ BRD

Prisma enum `enum_good_received_note_status` ที่เอกสารไว้ข้างต้นคือสิ่งที่ live UI ใช้ ไม่มี BRD `FR-XXX` identifier ทางการที่กำหนดสำหรับ specification สถานะ GRN ในเอกสาร source ที่มีอยู่ — reference ที่ใกล้ที่สุดคือ model 3 สถานะของ `grn-master-prd.md` และ enum 5 สถานะของ `GRN-Technical-Specification.md` ทั้งสองแตกต่างจาก Prisma (ดู [good-receive-note/01-data-model](/th/inventory/good-receive-note/01-data-model) § 5 รายการ 1) ตารางด้านล่างแมพทุกสถานะ live-UI ที่สังเกตได้กับ PRD / Technical Spec equivalent เพื่อให้ tester และ developer reconcile ทั้งสองโดยไม่กำกวม Source: `Test_case/System_Process/tx-01-grn.md` (วันที่จับ 2026-04-27)

| Live UI status | PRD / Technical Spec equivalent | ต่าง | หมายเหตุ |
|---|---|---|---|
| `draft` | _(ไม่อยู่ใน tx-01-grn.md)_ | 🔴 ใหม่ใน live UI | PRD บรรยาย `Received → Committed`; ไม่มีสถานะ Draft ปรากฏ Prisma default คือ `draft` แก้ไขได้; ไม่มีผลกระทบสต๊อกหรือ GL |
| `saved` | `Received` (model 3 สถานะของ grn-master-prd.md) | 🟡 เปลี่ยนชื่อ | PRD ติด label สถานะนี้เป็น `Received` Live UI เรียกว่า `saved` (review-ready ยังไม่ post) Technical Spec ไม่มี equivalent |
| `committed` | `Committed` | ✅ ตรง | สถานะล็อก terminal **แก้ไขในรอบนี้:** การเพิ่ม inventory, การเขียน cost layer และการเลื่อน PO line ทั้งหมดเกิดขึ้นก่อนหน้านี้แล้วตอนเปลี่ยนสถานะ `draft → saved` (`GRN_POST_002`/`GRN_POST_004`/`GRN_POST_005`) — `committed` เพียงล็อกเอกสาร ไม่พบ GL accrual ใดในซอร์สปัจจุบัน |
| `voided` | _(ไม่อยู่ใน tx-01-grn.md)_ | 🔴 ใหม่ใน live UI | การยกเลิกบริหารก่อน commit ไม่ปรากฏใน status flow string ของ `Test_case/System_Process/tx-01-grn.md` |

> ⚠️ **ความคลาดเคลื่อน — ไม่มีสถานะ Draft ใน Test_case:** `Test_case/System_Process/tx-01-grn.md` บันทึก flow สถานะเป็น `Received → Committed` โดยไม่มีสถานะ `Draft` Live Prisma schema เปิดด้วย `draft` เป็นสถานะสร้างเริ่มต้นก่อน `saved` (≈ `Received`) Tester ควรคาดว่าจะเห็น GRN `draft` ใน UI ที่ tx-01-grn.md ไม่ได้เอกสารชัดเจน Source: `Test_case/System_Process/tx-01-grn.md` (วันที่จับ 2026-04-27)

> ⚠️ **ความคลาดเคลื่อน — สองเส้นทางสร้าง:** `Test_case/System_Process/tx-01-grn.md` BR-01 เอกสารทั้งการสร้าง GRN แบบ PO-linked และแบบ standalone (manual) สอดคล้องกับ `enum_good_received_note_type { purchase_order, manual }` PRD และ Technical Spec บรรยายเฉพาะเส้นทาง PO-sourced Tester ต้องครอบคลุมทั้งสองเส้นทาง; เส้นทาง standalone ตั้ง `doc_type = manual` และไม่เขียน `purchase_order_detail_id` บนบรรทัดใด Source: `Test_case/System_Process/tx-01-grn.md` (วันที่จับ 2026-04-27)

> ℹ️ **หมายเหตุ — ไม่มี BRD FR-XXX identifier:** ต่างจากโมดูล PO (`FR-PO-005`) ไม่มี BRD requirement ID ทางการที่กำหนดสำหรับ specification สถานะ GRN ในเอกสาร source ที่มีอยู่ หัวคอลัมน์ด้านบน reference prose `grn-master-prd.md` แทนที่จะเป็น BRD identifier ที่มี version

> ⚙️ **กฎฝั่ง server — list บน mobile เป็น `draft` เท่านั้น:** Endpoint รายการ GRN ใช้ตัวกรองมุมมองที่ขึ้นกับอุปกรณ์ `applyMobileGrnDocStatusFilter(paginate, appId)` โดยอุปกรณ์ที่เรียกถูก resolve จาก request header `x-app-id` เทียบกับ app allowlist เมื่ออุปกรณ์เป็น `mobile` รายการถูกบังคับให้เป็น `doc_status = draft` เท่านั้น — ตัวกรอง `doc_status` อื่นใดบน request จะถูกถอดออกและแทนที่ด้วย `doc_status|enum = draft` บนอุปกรณ์ที่ไม่ใช่ mobile (desktop) รายการไม่เปลี่ยน: ส่งคืนทุกสถานะ (`draft`, `saved`, `committed`, `voided` ตามที่มี) นี่คือ **การจำกัดมุมมอง (VIEW) ไม่ใช่กฎสถานะเอกสาร** — GRN ที่ไม่ใช่ `draft` ยังคงมีอยู่ในฐานข้อมูลและเข้าถึงได้โดยตรง เพียงแต่ไม่ปรากฏในมุมมอง list บน mobile บังคับใช้ฝั่ง server ที่ backend gateway (`carmen-turborepo-backend-v2`, helper `apps/backend-gateway/src/common/helpers/mobile-grn-doc-status-filter.ts`); **ไม่ปรากฏใน PRD หรือ Technical Spec ดั้งเดิม**

## 6. กฎข้ามโมดูล

Rule ID เป็น `GRN_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | ---- |
| `GRN_XMOD_001` | [purchase-order](/th/inventory/purchase-order) | GRN สามารถสร้างได้เฉพาะกับ PO ที่ `po_status ∈ {sent, partial}` รับจาก PO `voided` ถูกปฏิเสธ outright (`GRN_VAL_013`); รับจาก PO `draft`, `in_progress`, `closed` หรือ `completed` ก็ปฏิเสธเช่นกัน ปริมาณ pending ที่มีคือ `order_qty − received_qty − cancelled_qty` ต่อบรรทัด PO active |
| `GRN_XMOD_002` | [purchase-order](/th/inventory/purchase-order) | **แก้ไขในรอบนี้:** ตอน **save** (`draft → saved` ไม่ใช่ commit) GRN เลื่อน `received_qty` ของบรรทัด PO (`GRN_POST_005`) และอาจย้าย `po_status` จาก `sent → partial` (รับบางส่วน) หรือ `* → completed` (รับเต็ม) การรวมหลาย PO จัดกลุ่มโดย **ผู้ขายและสกุลเงิน** (ยืนยันใน `grn-po-wizard-dialog.tsx` ซึ่งปฏิเสธการเลือกที่มี `currency_id` มากกว่าหนึ่งค่า) ไม่พบการตรวจเงื่อนไขเครดิต |
| `GRN_XMOD_003` | [purchase-order](/th/inventory/purchase-order) | การรับปริมาณเกิน pending qty ถูกปฏิเสธเว้นแต่ tenant config อนุญาต over-receipt tolerance; ไม่เช่นนั้น GRN line ถูก cap ที่ pending qty **ยังไม่ยืนยัน:** วง feedback "การยกเลิกตอนรับเขียนกลับลง `cancelled_qty`" ฝั่ง GRN ยังไม่ได้ตรวจสอบอย่างอิสระเทียบกับ `good-received-note.service.ts` ในรอบนี้ — ให้ถือเป็นเจตนาการออกแบบจนกว่าจะยืนยัน |
| `GRN_XMOD_004` | [inventory](/th/inventory/inventory) | **แก้ไขในรอบนี้:** Inventory on-hand เพิ่มตอน GRN **save** (`GRN_POST_004`) ไม่ใช่ตอน commit การเพิ่มผ่าน insert ลง `tb_inventory_transaction` / `tb_inventory_transaction_detail` ถึงจากฝั่ง GRN ผ่าน `tb_good_received_note_detail_item.inventory_transaction_id` **ยังไม่ยืนยัน / อาจกุขึ้น:** movement type "Consignment In" ที่ผูกกับ `is_consignment` ไม่มีอยู่จริง — boolean นั้นเองไม่มีอยู่บน `tb_good_received_note` แล้ว (ถูกแทนที่ด้วย `post_type`), `enum_transaction_type` ไม่มีสมาชิกที่เกี่ยวกับ consignment และไม่มีโค้ดใดแยกเงื่อนไขการสร้าง inventory transaction ตาม `post_type` การรับ GRN ทุกใบปัจจุบัน post ผ่านเส้นทางเดียวกัน |
| `GRN_XMOD_005` | [inventory](/th/inventory/inventory) | Lot number, expiry date, manufacturing date และ serial number อยู่บน `tb_inventory_transaction_detail` (และ `tb_inventory_transaction_cost_layer.lot_no`) **ไม่ใช่** บน GRN line GRN detail_item คือ cursor เหตุการณ์รับที่ชี้ไปยัง inventory transaction UI เปิดเผยข้อมูล lot ผ่าน linkage นี้; ความแตกต่างจาก PRD §3.5 / Technical Spec `GRNItem.lotNumber` ของ carmen/docs เอกสารใน [good-receive-note/01-data-model](/th/inventory/good-receive-note/01-data-model) § 5 รายการ 3 |
| `GRN_XMOD_006` | [costing](/th/inventory/costing) | Valuation ตอน **save** ตามวิธี costing ของ tenant — FIFO หรือ moving-average (`inventory-transaction.service.ts` แยกตาม `enum_calculation_method`) **ยังไม่ยืนยัน:** สูตร Last Cost "(net + extra costs ที่ allocate) / (received + FOC qty)" ของ `GRN_CALC_012` ยังไม่ยืนยันว่าเป็นตัวเลขที่เขียนลง `tb_inventory_transaction_cost_layer.cost_per_unit` จริง — โค้ดสร้าง cost layer อ่านเฉพาะ `base_net_amount` ของ detail_item เอง ไม่พบ term extra-cost ในการคำนวณนั้น ให้ถือว่าสูตร Last Cost ที่รวม extra-cost เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว |
| `GRN_XMOD_007` | ~~AP / Finance / three-way match~~ | **ยังไม่ implement** ข้อสรุปเดียวกับ `GRN_POST_006`–`GRN_POST_009`: ไม่มีโค้ดใบกำกับ, AP-posting หรือ three-way-match ใน `carmen-turborepo-backend-v2` หรือ `carmen-inventory-frontend-react` ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วสำหรับ `PO_XMOD_007` ของโมดูล `purchase-order` |
| `GRN_XMOD_008` | [vendor-pricelist](/th/inventory/vendor-pricelist) | **ยังไม่ยืนยันภายในโมดูลนี้** ไม่พบโค้ด lookup pricelist หรือ comment price-variance ภายใน `good-received-note.service.ts` หรือ route ของ frontend ในรอบนี้ — การค้นหาทั่วโมดูล GRN สำหรับ `pricelist` / `price-list` ให้ผลศูนย์รายการ ให้ถือว่า "ระบบเปิดเผยคำใบ้ variance ตอนเข้า GRN" เป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้วในโมดูล GRN ปัจจุบัน (ฟีเจอร์ pricelist มีอยู่จริงที่อื่นในผลิตภัณฑ์ — ดู [vendor-pricelist](/th/inventory/vendor-pricelist) — แต่ไม่พบจุดเชื่อมต่อฝั่ง GRN) |
| `GRN_XMOD_009` | Vendor performance | **ยังไม่ยืนยัน** ไม่พบโค้ด vendor-scoring หรือ vendor-performance-feed ภายในโมดูล GRN ในรอบนี้; ให้ถือเป็นเจตนาการออกแบบ |
| `GRN_XMOD_010` | [inventory-adjustment](/th/inventory/inventory-adjustment) | การแก้ไขหลัง commit ที่ไม่ใช่ credit-note-eligible (เช่น lot ที่นับผิด สต๊อกที่เสียหายที่พบหลัง putaway) flow ผ่าน inventory-adjustment ไม่ใช่ผ่านการแก้ไข GRN reference กลับไปยัง `tb_good_received_note.id` ต้นทางถูกบันทึกบน adjustment สำหรับ audit |

## 7. แหล่งอ้างอิง

- `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md` — System Calculation Rules (`GRN_041`–`GRN_065`) สืบทอดเป็น series `GRN_CALC_NNN` ข้างต้น หมายเหตุ: enum `GRNStatus` และ enum `AllocationMethod` 5 โหมดของ Technical Spec แตกต่างจาก Prisma; กฎข้างต้นใช้ค่า Prisma (`draft`/`saved`/`committed`/`voided` และ `manual`/`by_value`/`by_qty`)
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — §5 Business Rules (status transition, inventory update, integration `BR-01`/`BR-02`, validation), §3.7 Commit Process (individual / batch / end-of-period auto-commit), §3.4.5.5 ตรรกะการคำนวณ tax-inclusive vs tax-exclusive
- `../carmen/docs/good-recive-note-managment/grn-create-process-doc.md` — Process flow (PO-based และ manual) และประตู validation ที่แต่ละ screen แมพข้างต้นลงบน `GRN_VAL_*` และ `GRN_AUTH_*`
- Sibling: `en/good-receive-note/01-data-model.md` — model Prisma ทางการ, ค่า enum (เจาะจง enum 4 ค่า `enum_good_received_note_status` และ enum 3 ค่า `enum_allocate_extra_cost_type` บน `tb_extra_cost`) และ catalog ความแตกต่างที่ส่วน 1, ส่วน 3 และส่วน 6 พึ่งพา
- การ implement กฎ backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/good-received-note/` (`good-received-note.service.ts`, `good-received-note.logic.ts`) — status guard, calculation utility, การสร้าง inventory transaction (เกิดตอน save), และการเลื่อนฝั่ง PO ไม่มี three-way-match orchestration หรือ AP-posting ใดๆ อยู่ที่นั่น (ดู § 5 / § 6)
