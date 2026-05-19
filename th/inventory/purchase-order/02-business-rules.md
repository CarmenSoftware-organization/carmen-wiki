---
title: ใบสั่งซื้อ (Purchase Order) — Business Rules
description: กฎการ validation การคำนวณ การกำหนดสิทธิ์ การ posting การ three-way-match และกฎข้ามโมดูลสำหรับ purchase-order
published: true
date: 2026-05-19T23:55:00.000Z
tags: purchase-order, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — Business Rules

> **At a Glance**
> **กลุ่ม rule:** `PO_VAL_*` validation &nbsp;·&nbsp; `PO_AUTH_*` permission &nbsp;·&nbsp; `PO_CALC_*` calc &nbsp;·&nbsp; `PO_POST_*` posting &nbsp;·&nbsp; `PO_XMOD_*` cross-module
> **จำนวน rule:** ประมาณ 60 rules
> **กลุ่มผู้ใช้:** ผู้เขียน test + developer — ทุก rule ID anchor จากหน้า `04-test-scenarios*`
> **Status lifecycle:** Section 5.1 (ที่มี) carry callout ความแตกต่างของ Live UI กับ BRD

## 1. ภาพรวม

หน้านี้ capture กติกาทางธุรกิจเชิงปฏิบัติการที่ควบคุมเอกสาร Purchase Order (PO) ตลอดวงจรชีวิตของมัน: การ validate input ตอน create / edit / submit, การคำนวณเงิน (บรรทัดและส่วนหัว), gate การกำหนดสิทธิ์ตาม role และเกณฑ์มูลค่า, ผล posting บนแต่ละ transition ของ `enum_purchase_order_doc_status`, three-way-match กับ GRN และ vendor invoice และกฎข้ามโมดูลกับ [purchase-request](/th/inventory/purchase-request), [good-receive-note](/th/inventory/good-receive-note), [vendor-pricelist](/th/inventory/vendor-pricelist), และ [inventory](/th/inventory/inventory)

กติกาด้านล่างสังเคราะห์จาก business analysis PO ใน carmen/docs แบบเดิม catalogue กฎทางธุรกิจของ PR ที่ตรงกัน (Section 3 ของ `purchase-request-ba.md` และ `PR-Module-Structure.md` เนื่องจาก PO inherit ปรัชญาการคำนวณ การปัดเศษ และ approval เดียวกัน) และโมเดลข้อมูล canonical ของ Prisma ที่ documented ใน [purchase-order/01-data-model](/th/inventory/purchase-order/01-data-model) เมื่อ carmen/docs แบบเดิมและ Prisma ไม่ตรงกัน Prisma เป็น canonical — โดยเฉพาะสำหรับค่า status (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) และสำหรับ PR↔PO bridge linkage มากกว่า FK เดียวบน PO line

## 2. กฎ Validation

Rule IDs ตามรูปแบบ `PO_VAL_NNN` Header rules (001–006) ทำงานทุก save และตอน submit; line rules (007–011) ทำงานต่อบรรทัดตอน save และตอน submit; aggregate rules (012–016) ทำงานเฉพาะตอน submit เท่านั้น

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PO_VAL_001` | `tb_purchase_order.po_no` ไม่ว่างและไม่ซ้ำในหมู่ rows ที่ไม่ soft-delete (`@@unique([po_no, deleted_at])`) | Create, edit, submit | Reject ด้วย "PO reference number is required and must be unique." DB-level fallback ผ่าน unique index |
| `PO_VAL_002` | `vendor_id` อ้างอิง row `tb_vendor` ที่ active และไม่ soft-deleted | Create, edit, submit | Reject ด้วย "Vendor is required and must be from the approved vendor list." |
| `PO_VAL_003` | `currency_id` อ้างอิง row `tb_currency` ที่ไม่ soft-deleted; `exchange_rate > 0` | Create, edit, submit | Reject ด้วย "Transaction currency and a positive exchange rate are required." |
| `PO_VAL_004` | `po_type` เป็นหนึ่งใน `enum_purchase_order_type` (`manual`, `purchase_request`); default `purchase_request` | Create | Reject ด้วย "PO type must be `manual` or `purchase_request`." |
| `PO_VAL_005` | `credit_term_id` อ้างอิง row `tb_credit_term` ที่ไม่ soft-deleted เมื่อ vendor ต้องการ | Submit | Reject ด้วย "Credit term is required for this vendor." |
| `PO_VAL_006` | `order_date` ไม่เป็น null และ `delivery_date >= order_date` | Edit, submit | Reject ด้วย "Delivery date must be on or after the order date." |
| `PO_VAL_007` | แต่ละ `tb_purchase_order_detail` row มี `product_id` ที่ไม่เป็น null อ้างอิง `tb_product` ที่ active และไม่ soft-deleted | Save line, submit | Reject บรรทัดด้วย "Product is required." |
| `PO_VAL_008` | `order_qty > 0` และ `order_unit_id` ไม่เป็น null | Save line, submit | Reject บรรทัดด้วย "Order quantity must be greater than zero and a unit of measure is required." |
| `PO_VAL_009` | `order_unit_conversion_factor > 0`; `base_qty = order_qty × order_unit_conversion_factor` ปัดเศษเป็น 3 ทศนิยม | Save line, submit | Reject บรรทัดด้วย "Order UoM must have a positive conversion factor to base UoM." คำนวณ `base_qty` ใหม่ตอน save |
| `PO_VAL_010` | `price >= 0` (อนุญาตศูนย์เฉพาะเมื่อ `is_foc = true`) | Save line, submit | Reject บรรทัดด้วย "Unit price must be non-negative; price of 0 requires the FOC flag." |
| `PO_VAL_011` | `tax_rate >= 0` และ `discount_rate >= 0`; เมื่อ `is_tax_adjustment = true` หรือ `is_discount_adjustment = true` จำนวน override ต้อง persist โดย application | Save line, submit | Reject บรรทัดด้วย "Tax / discount rate must be non-negative; manual override requires an explicit amount." |
| `PO_VAL_012` | PO มีอย่างน้อย `tb_purchase_order_detail` row ที่ไม่ soft-deleted หนึ่งบรรทัดตอน submit | Submit | Reject ด้วย "PO must contain at least one line item." |
| `PO_VAL_013` | ทุกบรรทัดบน PO ใช้ context `vendor_id` และ `currency_id` ของ header (invariant single-vendor / single-currency) | Submit | Reject ด้วย "All lines on a PO must share the header vendor and currency. Split into separate POs by vendor+currency." |
| `PO_VAL_014` | เมื่อ `po_type = purchase_request` ทุกบรรทัดมีอย่างน้อย bridge row หนึ่ง row ใน `tb_purchase_order_detail_tb_purchase_request_detail` ที่ `pr_detail_qty > 0` | Submit | Reject ด้วย "PR-sourced PO lines must be linked to an originating PR line via the bridge table." |
| `PO_VAL_015` | Status transitions เป็นไปตาม state machine ใน Section 5; transitions นอกลำดับถูก block | On status change | Reject ด้วย "Invalid status transition from `<from>` to `<to>`." |
| `PO_VAL_016` | การ amend vendor, currency, หรือบรรทัดใด ๆ บน PO ที่ `po_status` ไม่ใช่ `draft` หรือ `in_progress` ถูก block หลัง `sent` เฉพาะ `cancelled_qty` และ note ต่อบรรทัดเท่านั้นที่ update ได้ | Edit on non-draft PO | Reject ด้วย "PO can no longer be amended at status `<status>`. Void or close instead." |

## 3. กฎการคำนวณ

ค่าเงินทุกตัวเก็บเป็น `Decimal(20, 5)` ที่ระดับ row; **อัตรา** tax และ discount เก็บเป็น `Decimal(15, 5)`; exchange rate เป็น `Decimal(15, 5)` บนส่วนหัว PO การปัดเศษการแสดงผลเป็น half-up (banker's rounding สำหรับ tie ที่ .5) เป็น 2 ทศนิยมสำหรับจำนวนเงิน 3 ทศนิยมสำหรับปริมาณ และ 5 ทศนิยมสำหรับอัตรา การคำนวณกลางเสมอ re-read ค่าที่ปัดเศษของขั้นตอนก่อน (ตรงกับ `PR_046`–`PR_055` จาก PR BA ที่ PO inherit)

Rule IDs ตามรูปแบบ `PO_CALC_NNN`

| Rule ID | สูตร |
| ------- | ------- |
| `PO_CALC_001` (subtotal บรรทัด) | `sub_total_price = Round(price × order_qty, 2)` |
| `PO_CALC_002` (discount บรรทัด) | `discount_amount = Round(Round(sub_total_price, 2) × discount_rate, 2)` เว้นแต่ `is_discount_adjustment = true` ซึ่งกรณีนั้น override ที่ persist ชนะ |
| `PO_CALC_003` (net บรรทัด) | `net_amount = Round(Round(sub_total_price, 2) − Round(discount_amount, 2), 2)` |
| `PO_CALC_004` (tax บรรทัด) | `tax_amount = Round(Round(net_amount, 2) × tax_rate, 2)` เว้นแต่ `is_tax_adjustment = true` (override) |
| `PO_CALC_005` (total บรรทัด) | `total_price = Round(Round(net_amount, 2) + Round(tax_amount, 2), 2)` |
| `PO_CALC_006` (base conversion) | สำหรับแต่ละ column เงิน `X` ในสกุลเงิน transaction column base `base_X = Round(Round(X, 2) × exchange_rate (5 dp), 2)` โดยเฉพาะ `base_price`, `base_sub_total_price`, `base_discount_amount`, `base_net_amount`, `base_tax_amount`, `base_total_price` |
| `PO_CALC_007` (การจัดการ FOC) | เมื่อ `is_foc = true` บรรทัดมีส่วนร่วม `0` ต่อ `sub_total_price`, `discount_amount`, `tax_amount`, และ `total_price` แต่ `order_qty` และ `base_qty` ยัง roll up ไปยัง `tb_purchase_order.total_qty` |
| `PO_CALC_008` (subtotal header) | `tb_purchase_order.total_price = Round(Σ Round(net_amount, 2), 2)` ข้ามบรรทัด active ที่ไม่ soft-deleted |
| `PO_CALC_009` (tax header) | `tb_purchase_order.total_tax = Round(Σ Round(tax_amount, 2), 2)` |
| `PO_CALC_010` (grand total header) | `tb_purchase_order.total_amount = Round(Round(total_price, 2) + Round(total_tax, 2), 2)` เทียบเท่า `Σ Round(line.total_price, 2)` |
| `PO_CALC_011` (qty header) | `tb_purchase_order.total_qty = Round(Σ Round(base_qty, 3), 3)` — quantity บวกใน base UoM เท่านั้นเพราะบรรทัดอาจใช้ order UoMs ต่างกัน |
| `PO_CALC_012` (โหมดปัดเศษ) | การปัดเศษทั้งหมดใช้โหมด half-up (banker's) ตาม PR_047; การจัดรูปแบบตัวเลขเชิงภูมิภาคใช้ที่ presentation เท่านั้น ไม่ใช่ที่ storage (PR_050) |

### 3.1 ตัวอย่างการคำนวณ (฿ THB สกุลเงิน transaction)

สองบรรทัด vendor ใน THB อัตราแลกเปลี่ยนเป็นฐาน THB = 1.00000 (ไม่มี FX)

- Line 1: `order_qty = 10.000`, `price = ฿125.50`, `discount_rate = 5%`, `tax_rate = 7%`, `is_foc = false`
  - `sub_total_price = Round(125.50 × 10.000, 2) = ฿1,255.00`
  - `discount_amount = Round(1,255.00 × 0.05, 2) = ฿62.75`
  - `net_amount = Round(1,255.00 − 62.75, 2) = ฿1,192.25`
  - `tax_amount = Round(1,192.25 × 0.07, 2) = ฿83.46`
  - `total_price = Round(1,192.25 + 83.46, 2) = ฿1,275.71`
- Line 2: `order_qty = 4.000`, `price = ฿89.00`, `discount_rate = 0%`, `tax_rate = 7%`, `is_foc = false`
  - `sub_total_price = ฿356.00`; `discount_amount = ฿0.00`; `net_amount = ฿356.00`
  - `tax_amount = Round(356.00 × 0.07, 2) = ฿24.92`
  - `total_price = ฿380.92`
- Header roll-up:
  - `total_price = Round(1,192.25 + 356.00, 2) = ฿1,548.25`
  - `total_tax = Round(83.46 + 24.92, 2) = ฿108.38`
  - `total_amount = Round(1,548.25 + 108.38, 2) = ฿1,656.63`

หากเพิ่ม FOC บรรทัดที่สาม (`order_qty = 1.000`, `price = 0`, `is_foc = true`), `total_qty` เพิ่ม 1.000 (ใน base UoM) แต่ `total_amount` ไม่เปลี่ยน

## 4. กฎ Authorization

Rule IDs ตามรูปแบบ `PO_AUTH_NNN` Authorization บังคับใช้โดย RBAC ที่ชั้น API; กฎด้านล่างระบุนโยบาย ไม่ใช่ implementation ชื่อ role mirror ตาราง RBAC ของ carmen/docs; เกณฑ์ "high-value" ตั้งค่าได้ที่ระดับ tenant และ default เป็น escalation level ของ procurement-manager ในนิยาม workflow ที่ `tb_purchase_order.workflow_id` อ้างอิง

| Rule ID | Subject | สิทธิ์ | ข้อจำกัด |
| ------- | ------- | ----- | ---------- |
| `PO_AUTH_001` | Procurement Officer | สร้าง PO (`po_status = draft`) | ทั้ง `manual` และ `purchase_request` `po_type` |
| `PO_AUTH_002` | Procurement Officer | แก้ไข PO | เฉพาะตอน `po_status ∈ {draft, in_progress}` และผู้ใช้คือ buyer ที่ assigned หรือถือ `workflow_current_stage` ปัจจุบัน |
| `PO_AUTH_003` | Procurement Officer | Submit PO (`draft → in_progress`) | อย่างน้อยหนึ่งบรรทัด; ผ่าน validation Section 2 |
| `PO_AUTH_004` | Procurement Manager | อนุมัติ PO ที่ stage high-value (`in_progress → sent` สำหรับมูลค่าเหนือ threshold) | `tb_purchase_order.total_amount` เกิน tenant high-value threshold ที่ define ใน workflow ต่ำกว่า threshold Procurement Officer สามารถ self-approve เป็น `sent` ได้ถ้า workflow อนุญาต |
| `PO_AUTH_005` | Procurement Manager | ลบ PO | เฉพาะตอน `po_status = draft` (soft-delete ผ่าน `deleted_at`) |
| `PO_AUTH_006` | Procurement Officer หรือ Procurement Manager | ส่ง PO ให้ vendor (`sent`) | หลังอนุมัติ; ตั้ง `tb_purchase_order.email` และ `approval_date` |
| `PO_AUTH_007` | Procurement Manager | Void PO (`* → voided`) | อนุญาตจาก status ที่ไม่ terminal ใด ๆ (`draft`, `in_progress`, `sent`, `partial`) เมื่ออยู่ที่ `voided` แล้ว ไม่อนุญาต transition เพิ่ม |
| `PO_AUTH_008` | Inventory Manager (Receiver) | สร้าง GRN เทียบกับ PO; ปิด PO (`partial → closed` early termination) | อนุญาตเฉพาะเมื่อ `po_status ∈ {sent, partial}` |
| `PO_AUTH_009` | Finance Officer | View, export reports | Read-only ข้าม status ทั้งหมด |
| `PO_AUTH_010` | Segregation of duties | Purchaser ≠ Receiver | ผู้ใช้ที่สร้างหรือส่ง PO (`tb_purchase_order.buyer_id` หรือ `last_action_by_id` บน transition `sent`) ต้อง **ไม่** เป็นผู้ใช้คนเดียวกันที่ post GRN เทียบกับ PO นั้น บังคับใช้ตอน GRN creation |
| `PO_AUTH_011` | Workflow-derived authorization | Stage-gated approval | ชุดผู้ใช้ใน `tb_purchase_order.user_action.execute` ที่ `workflow_current_stage` ปัจจุบันคือชุดเดียวที่อนุญาตให้ advance เอกสาร; ความพยายาม approve อื่น ๆ ถูก reject |

## 5. กฎ Posting

ค่า status คือสมาชิก literal ของ `enum_purchase_order_doc_status` ที่ documented ใน [purchase-order/01-data-model](/th/inventory/purchase-order/01-data-model) § 4: `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed` ไม่มี GL "posting" แยกต่างหากสำหรับเอกสาร PO เอง; PO posting คือการ mutate status บันทึก audit trail (`history`, `workflow_history`) และ trigger side effect ปลายน้ำ GL posting จริงเกิดที่ GRN (inventory accrual) และที่ three-way-match สำเร็จ (AP invoice)

Rule IDs ตามรูปแบบ `PO_POST_NNN`

| Rule ID | Transition / Event | ผลกระทบ |
| ------- | ------------------ | ------- |
| `PO_POST_001` | Create (→ `draft`) | Insert `tb_purchase_order` ด้วย `po_status = draft`, `doc_version = 0`, `total_qty = total_price = total_tax = total_amount = 0` Append เข้า `history`: `{ po_status: 'draft', action: 'created', by, at }` |
| `PO_POST_002` | Submit (`draft → in_progress`) | คำนวณ roll-ups ใหม่ทั้งหมด (`PO_CALC_008`–`PO_CALC_011`) ตั้ง `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user` Initialise `workflow_history`, `workflow_current_stage = <first stage>`, `stages_status = [...]`, และ populate `user_action.execute` จาก workflow stage definition Append `history` entry Soft commitment ต่องบประมาณ/inventory สร้างปลายน้ำโดย workflow |
| `PO_POST_003` | Approve (ภายใน `in_progress`) | Append entry `workflow_history`; advance `workflow_current_stage` Update `user_action.execute` สำหรับ stage ถัดไป `last_action = approved` ยังไม่มี status change — PO ยังคงเป็น `in_progress` จนกว่าจะถึง stage approval สุดท้าย |
| `PO_POST_004` | Final approval (`in_progress → sent`) | ตั้ง `po_status = sent`, `approval_date = now()`, `last_action = approved` Append `history` ส่ง PO ให้ vendor ผ่าน email/transmit layer ของ application **บน transition เดียวกัน** — ไม่มี action "Send to Vendor" แยกใน live UI (ขั้นตอน `APPROVED → SENT` เป็น auto) จากจุดนี้ไป PO เป็น vendor-facing commitment |
| `PO_POST_005` | Reject (`in_progress → draft`) | ตั้ง `po_status = draft`, `last_action = rejected`, reset `workflow_current_stage` เป็นจุดเริ่ม Append comment rejection ใน `tb_purchase_order_comment` (type `system`) บรรทัดยังแก้ไขได้ |
| `PO_POST_006` | GRN partial receipt (`sent → partial` หรือ `partial → partial`) | สำหรับแต่ละ PO line ที่ได้รับผลกระทบ การ post GRN เพิ่ม `tb_purchase_order_detail.received_qty` ตามปริมาณ GRN (ใน order UoM) หาก `received_qty < order_qty − cancelled_qty` สำหรับอย่างน้อยหนึ่งบรรทัด ตั้ง `po_status = partial` Bridge rows `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` ถูก update สัดส่วนเพื่อรักษา visibility ของ PR-side allocation |
| `PO_POST_007` | GRN full receipt (`sent → completed` หรือ `partial → completed`) | เมื่อทุกบรรทัด active เป็นไปตาม `received_qty = order_qty − cancelled_qty` ตั้ง `po_status = completed` Append `history` PO ปิดปกติ — ไม่รับ GRN เพิ่ม |
| `PO_POST_008` | Three-way match สำเร็จ | Verify (a) PO line, (b) GRN line, (c) vendor invoice (AP) สำหรับสินค้าเดียวกันว่าตรงกันบน quantity (ภายใน tolerance) และ price (ภายใน tolerance) เมื่อสำเร็จ AP module clear GRN accrual และ post vendor invoice สำหรับชำระเงิน PO เองไม่ transition ด้วย event นี้ — ยังคงอยู่ที่ status ใดก็ตามที่สะท้อน fulfilment (`partial` หรือ `completed`) |
| `PO_POST_009` | Three-way match ล้มเหลว | AP invoice ถูก hold ใน dispute Comment `system` ถูก append บน PO และ deviation record เปิดบนฝั่ง vendor / vendor-pricelist PO ไม่ถูก auto-voided; การแก้ไขทำด้วยมือผ่าน amendment, credit note หรือ void |
| `PO_POST_010` | Void (`* → voided` จาก `draft`, `in_progress`, `sent`, `partial` ใด ๆ) | ตั้ง `po_status = voided`, `is_active = false`, `last_action_at_date = now()` Reverse soft commitments ปลายน้ำใด ๆ (budget, vendor-side notification) หาก void จาก `partial`, GRN ที่ post แล้วยังคงใช้ได้ — เฉพาะส่วนที่ยังไม่ fulfilled เท่านั้นที่ถูก void `voided` เป็น terminal |
| `PO_POST_011` | Close (`partial → closed` early-termination) | ตั้ง `po_status = closed` สำหรับแต่ละบรรทัดที่ยังค้าง fulfilment application เขียน remainder กลับเป็น `cancelled_qty` เพื่อให้ `received_qty + cancelled_qty = order_qty` ใช้เมื่อ vendor ไม่สามารถ supply ปริมาณที่เหลือ แตกต่างจาก `completed` (รับครบ) `closed` เป็น terminal |
| `PO_POST_012` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `draft` ตาม `PO_AUTH_005` Row ยังอยู่ในฐานข้อมูล; unique indexes ทั้งหมดรวม `deleted_at` ดังนั้น PO ใหม่สามารถใช้ `po_no` เดียวกันได้ |

State diagram (Prisma-canonical):

```
[*] → draft → in_progress → sent → partial → completed
                ↑    ↓        ↓       ↓         ↑
              (reject)        ↓       ↓     (full receipt)
                              ↓       └→ closed (early term.)
                              ↓
        any non-terminal → voided  (admin)
```

`completed`, `closed`, และ `voided` เป็น terminal `draft` รับ soft-delete

### 5.1 Status Lifecycle — การ Mapping Live UI กับ BRD

Enum Prisma `enum_purchase_order_doc_status` ที่ documented ข้างต้นคือสิ่งที่ live UI ใช้ BRD `FR-PO-005` อธิบายชุด status ที่ต่างออกไปและบางกว่าเล็กน้อย ตารางด้านล่าง map ทุก live-UI status ที่สังเกตได้กับ BRD equivalent เพื่อให้ tester และ developer reconcile ทั้งสองได้โดยไม่มีความคลุมเครือ Source: `Test_case/Purchase_Order/Purchaser/INDEX.md` § Status Lifecycle (วันที่ capture 2026-04-26)

| Live UI status | BRD `FR-PO-005` equivalent | Diff | Notes |
|---|---|---|---|
| `DRAFT` | `Draft` | ✅ ตรงกัน | — |
| `IN PROGRESS` | _(ไม่อยู่ใน BRD)_ | 🔴 ใหม่ใน live UI | PO submit โดย Purchaser รอ FC อนุมัติ BRD ไม่ได้ model ไว้ |
| `APPROVED` | _(ไม่อยู่ใน BRD)_ | 🔴 ใหม่ใน live UI | FC อนุมัติ; PO auto-sent ไปยัง vendor ทันทีบน transition นี้ |
| `SENT` | `Sent` | ✅ ตรงกัน | Auto-set หลัง FC อนุมัติ ไม่มีขั้นตอน "Send" ด้วยมือใน live UI |
| `PARTIAL` | `Partial Received` | 🟡 เปลี่ยนชื่อ | Label BRD คือ `Partial Received` |
| `COMPLETED` | `Fully Received` | 🟡 เปลี่ยนชื่อ | Label BRD คือ `Fully Received` |
| `CLOSED` | `Closed` | ✅ ตรงกัน | — |
| `VOIDED` | `Cancelled` | 🟡 เปลี่ยนชื่อ | Label BRD คือ `Cancelled`; `VOIDED` ใช้ใน live UI สำหรับ "Close with no items received" |
| `REJECTED` | _(ไม่อยู่ใน BRD)_ | 🔴 ใหม่ใน live UI | FC reject PO โดยตรง PO ส่งกลับไปยัง Purchaser |
| _(ไม่มี)_ | `Acknowledged` | 🔵 BRD เท่านั้น | BRD นิยาม status vendor-confirmation ที่ไม่มีใน live UI |

> ⚠️ **ความแตกต่าง — เฟส FC-approval ไม่อยู่ใน BRD:** BRD `FR-PO-005` นิยาม flow เชิงเส้น `Draft → Sent → Acknowledged → Partial Received → Fully Received → Closed/Cancelled` Live UI แทรกเฟส FC-approval (`DRAFT → IN PROGRESS → APPROVED → SENT`) โดย `APPROVED` status auto-transition ไปยัง `SENT` ทันที `IN PROGRESS`, `APPROVED`, และ `REJECTED` ไม่อยู่ใน BRD

> ⚠️ **ความแตกต่าง — ไม่มี status `ACKNOWLEDGED` ใน live UI:** BRD model vendor confirmation เป็น status แยก Live UI ไม่ capture transition acknowledgement — vendor acknowledgement เมื่อได้รับ log ใน `tb_purchase_order_comment` เท่านั้น `po_status` ยังอยู่ที่ `sent`

> ⚠️ **ความแตกต่าง — semantics ของ `VOIDED`:** BRD `Cancelled` ครอบคลุมการ terminate ของ PO ที่เปิดอยู่ใด ๆ Live UI `VOIDED` แคบกว่า — หมายถึงเฉพาะ "Close approved PO with no items received" การ void จาก `sent` หรือ `partial` หลังจาก GRN ถูก post ทิ้ง GRN ไว้และเฉพาะส่วนที่ยังไม่ fulfilled เท่านั้นที่ถูก void (ตาม `PO_POST_010`)

## 6. กฎ Cross-Module

Rule IDs ตามรูปแบบ `PO_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | ---- |
| `PO_XMOD_001` | [purchase-request](/th/inventory/purchase-request) | เมื่อ `po_type = purchase_request` PO ต้องสร้างผ่าน flow การแปลง PR-to-PO ซึ่ง group PR ที่อนุมัติแล้วที่เลือกด้วย `(vendor_id, currency_id)` และผลิต PO หนึ่งใบต่อกลุ่ม แต่ละ PO line ที่ได้บรรจุ bridge rows หนึ่งหรือมากกว่าหนึ่ง row ใน `tb_purchase_order_detail_tb_purchase_request_detail` ที่ลิงก์กลับไปยัง PR line(s) ต้นทาง (`PO_VAL_014`) |
| `PO_XMOD_002` | [purchase-request](/th/inventory/purchase-request) | Bridge รองรับ consolidation (PR lines หลาย → PO line หนึ่ง) และ partial conversion (PR line หนึ่ง → PO lines หลาย) PR line ถือว่า converted เต็มที่เมื่อ `Σ bridge.pr_detail_qty` สำหรับ `pr_detail_id` นั้นเท่ากับ approved quantity ของ PR line |
| `PO_XMOD_003` | [good-receive-note](/th/inventory/good-receive-note) | GRN สามารถสร้างเทียบกับ PO ที่ `po_status ∈ {sent, partial}` เท่านั้น (`PO_AUTH_008`) GRN detail back-reference `tb_purchase_order_detail.id`; pending quantity ที่ใช้ได้สำหรับ receipt คือ `order_qty − received_qty − cancelled_qty` ตาม `PO_POST_006` |
| `PO_XMOD_004` | [good-receive-note](/th/inventory/good-receive-note) | การรับ quantity ที่จะเกิน pending qty ถูก reject เว้นแต่ tenant configuration อนุญาต over-receipt ภายใน tolerance; มิฉะนั้น GRN line ถูก cap ที่ pending qty |
| `PO_XMOD_005` | [vendor-pricelist](/th/inventory/vendor-pricelist) | ที่ PR-to-PO conversion ระบบ snapshot `price` จาก active vendor pricelist สำหรับ tuple `(vendor, product, currency)` หากไม่มี active pricelist row ราคา last-known ของ PR ถูกใช้และ comment `system` ถูก append flag การ coverage pricelist ที่หายไป |
| `PO_XMOD_006` | [vendor-pricelist](/th/inventory/vendor-pricelist) | เมื่อ buyer override snapshot price delta เทียบกับ pricelist ถูก log ใน `tb_purchase_order_detail_comment` เป็น entry deviation Deviations เหนือ tenant tolerance route PO ไปยัง stage approval high-value แม้ `total_amount` ต่ำกว่า threshold |
| `PO_XMOD_007` | AP / Three-way match | เมื่อ GRN post AP module raise liability inventory-accrual Accrual ถูก clear และ vendor invoice ถูก post เฉพาะเมื่อ three-way-match สำเร็จตาม `PO_POST_008` PO closure (`completed` หรือ `closed`) ไม่ clear accrual โดยตัวเอง — เป็นความรับผิดชอบของ AP เทียบกับ invoice จริง |
| `PO_XMOD_008` | [inventory](/th/inventory/inventory) | Inventory on-hand **ไม่** เพิ่มโดย PO posting — เพิ่มเฉพาะเมื่อ GRN post (ซึ่งอยู่ในขอบเขตของโมดูล GRN) PO มีส่วนร่วมปริมาณ "on-order" pipeline ที่ inventory planning อ่านผ่าน `order_qty − received_qty − cancelled_qty` บน PO lines ที่ active |
| `PO_XMOD_009` | [inventory](/th/inventory/inventory) | `base_qty` ของ PO line (คำนวณใน base UoM ผ่าน `PO_CALC_011`) คือ quantity ที่ inventory reservations และการคำนวณ projected-on-hand อ่าน; order UoM สำหรับการแสดงผลฝั่ง vendor เท่านั้น |

## 7. แหล่งอ้างอิง

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — PO consolidated BA (Section 1.3 Business Rules, Section 1.4 System Calculation Rules, Section 6.1 State Diagram, Section 2.5 RBAC) Labels ของ state ถูก reconcile กับค่า enum ของ Prisma ตาม [purchase-order/01-data-model](/th/inventory/purchase-order/01-data-model) § 5
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — โครงสร้าง validation, error-type, และ workflow-state ที่ PO inherit
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — Section 3 (Business Rules) และ Section 3.6 (System Calculation Rules); กฎการคำนวณของ PO (`PO_CALC_*`) เป็นคู่ของกฎ PR โดยตรง (`PR_036`–`PR_055`)
- Sibling: `en/purchase-order/01-data-model.md` — Prisma model canonical, ค่า enum, และ bridge-table linkage ที่ Section 5 และ Section 6 พึ่งพา
- Backend rule implementation (เมื่อเพิ่ม): `../carmen-turborepo-backend-v2/apps/` — purchase-order service module คือ hook implementation สำหรับกฎเหล่านี้ (status guards, calculation utilities, GRN posting back-references, three-way-match orchestration)
