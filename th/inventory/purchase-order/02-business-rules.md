---
title: ใบสั่งซื้อ (Purchase Order) — Business Rules
description: กฎการ validation การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูลสำหรับ purchase-order
published: true
date: 2026-07-29T05:45:00.000Z
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

หน้านี้ capture กติกาทางธุรกิจเชิงปฏิบัติการที่ควบคุมเอกสาร Purchase Order (PO) ตลอดวงจรชีวิตของมัน: การ validate input ตอน create / edit / submit, การคำนวณเงิน (บรรทัดและส่วนหัว), gate การกำหนดสิทธิ์ตาม workflow stage role, ผล posting บนแต่ละ transition ของ `enum_purchase_order_doc_status`, และกฎข้ามโมดูลกับ [purchase-request](/th/inventory/purchase-request), [good-receive-note](/th/inventory/good-receive-note), [vendor-pricelist](/th/inventory/vendor-pricelist), และ [inventory](/th/inventory/inventory) เอกสารรุ่นก่อนหน้าของหน้านี้เคยอธิบาย amount-threshold approval gate และ three-way-match กับ vendor invoice ด้วย claim three-way-match ไม่พบใน source ปัจจุบัน (§ 5) **ส่วน claim amount-threshold ถูกแก้ไขผิดพลาดโดย resync pass ก่อนหน้า** — pass ติดตามผลยืนยันแล้วว่ากลไกนี้มีจริง: workflow ที่ assign ให้ PO สามารถมี `routing_rules` ที่ route ตาม `total_amount` ได้ (ดู § 4, `PO_AUTH_004`) เพียงแต่ไม่ใช่ field "high-value threshold" เฉพาะของ PO แบบตายตัวตามที่เคยอธิบายไว้เดิม ดู § 4 สำหรับกฎที่แก้ไขแล้ว และดู Discrepancy log สำหรับรายละเอียด

กติกาด้านล่างสังเคราะห์จาก business analysis PO ใน carmen/docs แบบเดิม catalogue กฎทางธุรกิจของ PR ที่ตรงกัน (Section 3 ของ `purchase-request-ba.md` และ `PR-Module-Structure.md` เนื่องจาก PO inherit ปรัชญาการคำนวณ การปัดเศษ และ approval เดียวกัน) และโมเดลข้อมูล canonical ของ Prisma ที่ documented ใน [purchase-order/01-data-model](/th/inventory/purchase-order/01-data-model) เมื่อ carmen/docs แบบเดิมและ Prisma ไม่ตรงกัน Prisma เป็น canonical — โดยเฉพาะสำหรับค่า status (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) และสำหรับ PR↔PO bridge linkage มากกว่า FK เดียวบน PO line

## 2. กฎ Validation

Rule IDs ตามรูปแบบ `PO_VAL_NNN` Header rules (001–006) ทำงานทุก save และตอน submit; line rules (007–011) ทำงานต่อบรรทัดตอน save และตอน submit; aggregate rules (012–016) ทำงานเฉพาะตอน submit เท่านั้น

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PO_VAL_001` | `tb_purchase_order.po_no` ไม่ว่างและไม่ซ้ำในหมู่ rows ที่ไม่ soft-delete (`@@unique([po_no, deleted_at])`) | Create, edit, submit | Reject ด้วย "PO reference number is required and must be unique." DB-level fallback ผ่าน unique index |
| `PO_VAL_002` | `vendor_id` อ้างอิง row `tb_vendor` ที่ active และไม่ soft-deleted | Create, edit, submit | Reject ด้วย "Vendor is required and must be from the approved vendor list." |
| `PO_VAL_003` | `currency_id` อ้างอิง row `tb_currency` ที่ไม่ soft-deleted; `exchange_rate > 0` | Create, edit, submit | Reject ด้วย "Transaction currency and a positive exchange rate are required." |
| `PO_VAL_004` | `po_type` เป็นหนึ่งใน `enum_purchase_order_type` (`manual`, `purchase_request`, `pricelist`); default `purchase_request` | Create | Reject ด้วย "PO type must be `manual`, `purchase_request`, or `pricelist`." |
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

Rule IDs ตามรูปแบบ `PO_AUTH_NNN` Authorization บังคับใช้โดย RBAC ที่ชั้น API; กฎด้านล่างระบุนโยบาย ไม่ใช่ implementation ชื่อ role mirror ตาราง RBAC ของ carmen/docs

> ⚠️ **การแก้ไข (รอบนี้ ตรวจสอบกับ source ปัจจุบันแล้ว):** ตารางรุ่นก่อนหน้าเคยอธิบาย "high-value threshold" ที่ตั้งค่าได้ระดับ tenant ซึ่ง route การอนุมัติไปยัง Procurement Manager, action "Void" ที่เฉพาะ Procurement Manager เข้าถึงได้จาก status ที่ไม่ terminal ใด ๆ, และการตรวจสอบ segregation-of-duties (buyer ≠ ผู้ post GRN) ที่บังคับใช้ตอนสร้าง GRN claim Void และ segregation-of-duties ไม่พบใน source ปัจจุบัน: การค้นหาทั่ว `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `segregation` และ `SoD` ไม่พบผลลัพธ์ที่เกี่ยวข้องเลย และ `enum_stage_role` (`create`, `approve`, `purchase`, `issue`, `view_only`) ไม่มี member ใดที่รับรู้ deviation `PO_AUTH_007` และ `PO_AUTH_010` ด้านล่างถูกแก้ไขตามนี้
>
> **claim amount-threshold ถูกตัดทิ้งผิดพลาดใน pass เดียวกันนั้น** — การค้นหาคำตรงตัว `threshold` ครั้งแรกไม่พบอะไรเพราะกลไกที่ใช้งานจริงใช้คำศัพท์คนละชุด `tb_workflow.data.routing_rules` ซึ่งถูกประเมินโดย `evaluateCondition`/`findNextStep` ใน `workflows.navagation.service.ts` ทุกครั้งที่ submit และทุกครั้งที่ approve สามารถ route stage ถัดไปของ PO ตาม condition field (`total_amount` — ผลรวม `total_price` ของแต่ละบรรทัด map โดย `po-workflow.mapper.ts`; หรือ `department`, `category`) เทียบกับค่าที่ตั้งไว้ด้วย operator (`eq`, `gt`, `lt`, `gte`, `lte`, `between`) แล้ว `SKIP_STAGE` หรือกระโดดไปยัง `NEXT_STAGE` ที่ระบุชื่อไว้ ตั้งค่าได้จากแท็บ **Routing** ทั่วไปใน `/system-admin/workflow` (`wf-routing.tsx` + `wf-routing-constants.ts`) — ใช้ร่วมกันระหว่าง PR, PO, และ SR workflow (docstring ของ orchestrator เองระบุ "used across PR, PO, and SR") ไม่ใช่หน้าจอเฉพาะของ PO และเป็นทางเลือกการตั้งค่าต่อ workflow ไม่ใช่กฎแพลตฟอร์มตายตัว `PO_AUTH_004` ด้านล่างถูกแก้ไขตามนี้

| Rule ID | Subject | สิทธิ์ | ข้อจำกัด |
| ------- | ------- | ----- | ---------- |
| `PO_AUTH_001` | Procurement Officer | สร้าง PO (`po_status = draft`) | ทั้ง `manual`, `purchase_request`, หรือ `pricelist` `po_type` |
| `PO_AUTH_002` | Procurement Officer | แก้ไข PO | เฉพาะตอน `po_status ∈ {draft, in_progress}` และผู้ใช้คือ buyer ที่ assigned หรือถือ `workflow_current_stage` ปัจจุบัน |
| `PO_AUTH_003` | Procurement Officer | Submit PO (`draft → in_progress`) | อย่างน้อยหนึ่งบรรทัด; ผ่าน validation Section 2 |
| `PO_AUTH_004` | ผู้ที่ถือ stage role ที่ถูก assign ให้กับ stage สุดท้ายของ workflow (โดยทั่วไปคือ Procurement Manager แต่เป็นเพียงทางเลือกการตั้งค่า workflow เท่านั้น) | อนุมัติ PO ที่ workflow stage สุดท้าย (`in_progress → sent`) | Transition ไปยัง `sent` เองถูก gate ด้วย `isFinalApproval = (workflow_next_stage === '-')` ใน `purchase-order.logic.ts` เท่านั้น — คือการไปถึง stage สุดท้าย ไม่ใช่การเทียบค่า amount **ยืนยันแล้ว แก้ไขในรอบนี้:** stage ไหนนับเป็น "สุดท้าย" สำหรับ PO ใบหนึ่งอาจขับเคลื่อนด้วย amount ได้เอง — `routing_rules` ของ workflow ที่ assign ให้สามารถประเมิน `total_amount` (ผลรวม `total_price` ของแต่ละบรรทัด, `po-workflow.mapper.ts`) ทุกครั้งที่ submit/approve แล้ว skip หรือกระโดดข้าม stage ตามนั้น (`evaluateCondition`/`findNextStep` ใน `workflows.navagation.service.ts`) ทำให้ PO มูลค่าน้อยไปถึง `sent` ด้วยจำนวน stage น้อยกว่า PO มูลค่าสูงบน workflow เดียวกันได้ นี่เป็นทางเลือกการตั้งค่าต่อ workflow (แท็บ **Routing** ใน `/system-admin/workflow`) — workflow ที่ไม่มี routing rule จะอนุมัติทุก PO ผ่านลำดับ stage เดิมเสมอโดยไม่ขึ้นกับ amount กฎที่อิง `category` จะไม่ match เลยอย่างเงียบ ๆ — ไม่มี mapper ใดส่ง field `category` ระดับเอกสาร (source comment, `workflows.navagation.service.ts` ~บรรทัด 455-456) ไม่มี condition field สำหรับ pricelist-deviation-percentage (รองรับเฉพาะ `total_amount`, `department`, `category`) ดังนั้นการ reroute ตาม deviation จึงยังไม่ยืนยัน (ดู `PO_XMOD_006`) workflow แบบ single-stage ทำให้ผู้ใช้คนเดียวที่ถือ stage นั้นสามารถทั้งสร้างและอนุมัติขั้นสุดท้ายได้ |
| `PO_AUTH_005` | Procurement Manager | ลบ PO | เฉพาะตอน `po_status = draft` (soft-delete ผ่าน `deleted_at`) |
| `PO_AUTH_006` | ผู้ใช้ที่ถือ workflow stage สุดท้าย | ส่ง PO ให้ vendor (`sent`) | รวมอยู่ใน call approve ของ stage สุดท้ายเดียวกัน — ตั้ง `tb_purchase_order.email` และ `approval_date` บน transition เดียวกัน; ไม่มีขั้นตอน "Send to Vendor" แยกด้วยมือใน approval flow เอง |
| `PO_AUTH_007` | ผู้อนุมัติใด ๆ ที่ stage ปัจจุบัน | Reject PO (`in_progress → voided` แบบตรงและสิ้นสุด) | เข้าถึงได้เฉพาะจาก `in_progress` ผ่าน endpoint `/reject` เท่านั้น ไม่มี action "void" แยกต่างหาก และไม่มีเส้นทางไปยัง `voided` จาก `draft`, `sent`, หรือ `partial` — การจบ PO จาก status เหล่านั้นใช้ **Cancel** (`draft`/`in_progress`/`sent → closed`) หรือ **Close** (`sent`/`partial`/`in_progress → closed`) แทน ซึ่งทั้งคู่เขียนส่วนที่เหลือลงใน `cancelled_qty` |
| `PO_AUTH_008` | Inventory Manager (Receiver) | สร้าง GRN เทียบกับ PO; ปิด PO (`{sent, partial, in_progress} → closed` early termination) | การสร้าง GRN ต้องการ `po_status ∈ {sent, partial}` (`findOnePoForGrn`); endpoint Close อนุญาต `in_progress` เพิ่มด้วย (`closePO` ใน `purchase-order.service.ts`) |
| `PO_AUTH_009` | Role read-only ที่มีสิทธิ์ดู/export PO | View, export reports | Read-only ข้าม status ทั้งหมด ไม่พบ role หรือ permission key "Finance Officer" แยกต่างหากที่ยืนยันได้ใน source ปัจจุบัน |
| `PO_AUTH_010` | — | — (ยังไม่ยืนยัน) | **ยังไม่ยืนยัน / น่าจะยังไม่ implement** ไม่มี code path ใดใน GRN หรือ PO service ที่ตรวจสอบ `buyer_id` / `last_action_by_id` เทียบกับผู้ post GRN; การค้นหาทั่ว repo สำหรับ `segregation` ไม่พบผลลัพธ์ ให้ถือว่าข้อความอ้างอิง "Purchaser ≠ Receiver บังคับใช้ตอนสร้าง GRN" ในที่อื่นของโมดูลนี้เป็นเพียงเจตนาการออกแบบ ไม่ใช่พฤติกรรมจริงที่ใช้งานอยู่ |
| `PO_AUTH_011` | Workflow-derived authorization | Stage-gated approval | ชุดผู้ใช้ใน `tb_purchase_order.user_action.execute` ที่ `workflow_current_stage` ปัจจุบันคือชุดเดียวที่อนุญาตให้ advance เอกสาร; ความพยายาม approve อื่น ๆ ถูก reject |

## 5. กฎ Posting

ค่า status คือสมาชิก literal ของ `enum_purchase_order_doc_status` ที่ documented ใน [purchase-order/01-data-model](/th/inventory/purchase-order/01-data-model) § 4: `draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed` ไม่มี GL "posting" แยกต่างหากสำหรับเอกสาร PO เอง; PO posting คือการ mutate status บันทึก audit trail (`history`, `workflow_history`) และ trigger side effect ปลายน้ำ ผลกระทบฝั่ง inventory เกิดตอน GRN post (เป็นความรับผิดชอบของโมดูล GRN/inventory); ประโยครุ่นก่อนหน้าของย่อหน้านี้เคยยืนยันว่ามี GL posting "ตอน three-way-match สำเร็จ (AP invoice)" ด้วย — ฟีเจอร์นั้นยังไม่ implement (ดู `PO_POST_008`/`PO_POST_009` ด้านล่าง)

Rule IDs ตามรูปแบบ `PO_POST_NNN`

| Rule ID | Transition / Event | ผลกระทบ |
| ------- | ------------------ | ------- |
| `PO_POST_001` | Create (→ `draft`) | Insert `tb_purchase_order` ด้วย `po_status = draft`, `doc_version = 0`, `total_qty = total_price = total_tax = total_amount = 0` Append เข้า `history`: `{ po_status: 'draft', action: 'created', by, at }` |
| `PO_POST_002` | Submit (`draft → in_progress`) | คำนวณ roll-ups ใหม่ทั้งหมด (`PO_CALC_008`–`PO_CALC_011`) ตั้ง `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_id = user` Initialise `workflow_history`, `workflow_current_stage = <first stage>`, `stages_status = [...]`, และ populate `user_action.execute` จาก workflow stage definition Append `history` entry Soft commitment ต่องบประมาณ/inventory สร้างปลายน้ำโดย workflow |
| `PO_POST_003` | Approve (ภายใน `in_progress`) | Append entry `workflow_history`; advance `workflow_current_stage` Update `user_action.execute` สำหรับ stage ถัดไป `last_action = approved` ยังไม่มี status change — PO ยังคงเป็น `in_progress` จนกว่าจะถึง stage approval สุดท้าย |
| `PO_POST_004` | Final approval (`in_progress → sent`) | ตั้ง `po_status = sent`, `approval_date = now()`, `last_action = approved` Append `history` ส่ง PO ให้ vendor ผ่าน email/transmit layer ของ application **บน transition เดียวกัน** — ไม่มี action "Send to Vendor" แยกใน live UI (ขั้นตอน `APPROVED → SENT` เป็น auto) จากจุดนี้ไป PO เป็น vendor-facing commitment |
| `PO_POST_005` | Send-back / Review (`in_progress` ยังคงเป็น `in_progress`) | **แก้ไขในรอบนี้** — endpoint `/review` **ไม่** เปลี่ยน `po_status` มันเพียงรีเซ็ต `workflow_current_stage` / `workflow_previous_stage` กลับไปยัง stage ก่อนหน้า (โดยทั่วไปคือ stage ผู้สร้าง/"purchase" — `buildReviewWorkflow` ใน `workflow-orchestrator.service.ts` navigate กลับผ่าน `workflows.navigate-back-to-stage` และไม่คืนค่า field `po_status` เลย), ตั้ง `last_action = reviewed`, และ append `workflow_history` เมื่อปลายทางคือ stage ที่เฉพาะผู้สร้างเท่านั้น มีเพียง buyer/ผู้สร้างเดิมที่ดำเนินการต่อได้ (คล้ายกับการแก้ไข draft ในทางปฏิบัติ แต่ `po_status` ที่ persist ยังคงเป็น `in_progress` ไม่ใช่ `draft`) ข้อความเหตุผล (ถ้ามี) จะถูก append ลง `tb_purchase_order_comment` |
| `PO_POST_006` | GRN partial receipt (`sent → partial` หรือ `partial → partial`) | สำหรับแต่ละ PO line ที่ได้รับผลกระทบ การ post GRN เพิ่ม `tb_purchase_order_detail.received_qty` ตามปริมาณ GRN (ใน order UoM) หาก `received_qty < order_qty − cancelled_qty` สำหรับอย่างน้อยหนึ่งบรรทัด ตั้ง `po_status = partial` Bridge rows `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` ถูก update สัดส่วนเพื่อรักษา visibility ของ PR-side allocation |
| `PO_POST_007` | GRN full receipt (`sent → completed` หรือ `partial → completed`) | เมื่อทุกบรรทัด active เป็นไปตาม `received_qty = order_qty − cancelled_qty` ตั้ง `po_status = completed` Append `history` PO ปิดปกติ — ไม่รับ GRN เพิ่ม |
| `PO_POST_008` | ~~Three-way match สำเร็จ~~ — **ยังไม่ implement** | **ยังไม่ยืนยัน / น่าจะเป็นข้อมูลที่แต่งขึ้น** การค้นหาทั่ว frontend และ backend สำหรับ `three-way`, `threeWay`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` ไม่พบผลลัพธ์เลย ไม่มีหน้าจอบันทึก vendor-invoice, endpoint AP-posting, หรือ algorithm การจับคู่ใด ๆ อยู่ใน source ปัจจุบัน อย่าถือว่ากฎนี้เป็นพฤติกรรมจริงที่ใช้งานอยู่ — ดู Discrepancy log |
| `PO_POST_009` | ~~Three-way match ล้มเหลว~~ — **ยังไม่ implement** | ข้อค้นพบเดียวกับ `PO_POST_008` — ไม่มีโมดูล invoice/AP ที่จะ hold การจับคู่ที่อยู่ใน dispute |
| `PO_POST_010` | Cancel (`{draft, in_progress, sent} → closed`) | `cancel()` ใน `purchase-order.service.ts`: ตั้ง `po_status = closed`; สำหรับแต่ละบรรทัด เขียน `cancelled_qty = order_qty − received_qty` ไม่แตะ field `is_active` เลย นี่คือ action การถอน commitment ซึ่งต่างจาก Close ด้านล่างเพียงแค่ชุด source-status ที่อนุญาต |
| `PO_POST_010b` | Reject (`in_progress → voided` แบบตรงและสิ้นสุด) | `reject()` ใน `purchase-order.service.ts`: ตั้ง `po_status = voided` โดยตรง (ไม่ตั้ง `is_active = false` — claim นี้ในรุ่นก่อนหน้าของกฎนี้ไม่ได้รับการยืนยันในโค้ด) เข้าถึงได้เฉพาะจาก `in_progress`; ไม่มีเส้นทางไปยัง `voided` จาก `draft`, `sent`, หรือ `partial` `voided` เป็น terminal |
| `PO_POST_011` | Close (`{sent, partial, in_progress} → closed` early-termination) | `closePO()` ใน `purchase-order.service.ts`: ตั้ง `po_status = closed`; สำหรับแต่ละบรรทัดที่ `cancelledQty = orderQty − receivedQty > 0`, เขียนค่าลงใน `cancelled_qty` เพื่อให้ `received_qty + cancelled_qty = order_qty` ใช้เมื่อ vendor ไม่สามารถ supply ปริมาณที่เหลือ แตกต่างจาก `completed` (รับครบ) `closed` เป็น terminal |
| `PO_POST_012` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `draft` ตาม `PO_AUTH_005` Row ยังอยู่ในฐานข้อมูล; unique indexes ทั้งหมดรวม `deleted_at` ดังนั้น PO ใหม่สามารถใช้ `po_no` เดียวกันได้ |

State diagram (Prisma-canonical, แก้ไขในรอบนี้):

```
[*] → draft → in_progress → sent → partial → completed
       ↓ ↑        ↓  ↑        ↓       ↓         ↑
   (soft-  (send-back:      (cancel)  ↓     (full receipt)
    delete) stage resets,     ↓       ↓
             stays              ↓       └→ closed (early term./close/cancel)
             in_progress)        ↓
                          (reject) → voided  (in_progress only, direct & terminal)
```

`completed`, `closed`, และ `voided` เป็น terminal `draft` รับ soft-delete `closed` เข้าถึงได้จาก `draft`/`in_progress`/`sent` (cancel) หรือ `sent`/`partial`/`in_progress` (close) — ไม่มี action "void" แยกต่างหากนอกเหนือจาก `reject` ภายใน workflow

### 5.1 Status Lifecycle — บันทึกการแก้ไข

> ⚠️ **Section นี้เคยนำเสนอ mapping "Live UI vs BRD" ที่มาจากเอกสาร BA test-case รุ่นเก่า (`Test_case/Purchase_Order/Purchaser/INDEX.md`, capture วันที่ 2026-04-26) ซึ่งอ้างว่ามีสถานะ `APPROVED` แยกต่างหาก และสถานะ `REJECTED` ที่ส่ง PO กลับไปยัง Purchaser ทั้งสองอย่างไม่ใช่ Prisma enum member จริง และเมื่อ re-verify กับ source ปัจจุบันในรอบนี้ พบความจริงที่ต่างออกไปและง่ายกว่า — แก้ไขไว้ด้านล่าง**

Prisma enum `enum_purchase_order_doc_status` (`draft`, `in_progress`, `voided`, `sent`, `partial`, `closed`, `completed`) ครบถ้วนสมบูรณ์ — ไม่มี member `approved` หรือ `rejected` สิ่งที่เคยถูกเรียกว่า "`APPROVED`" ไม่ใช่ status ที่ persist: การอนุมัติ stage สุดท้ายและการส่งเกิดขึ้นใน call `approve()` เดียวกัน และลงเอยที่ `sent` โดยตรง (`PO_POST_004`) สิ่งที่เคยถูกเรียกว่า "`REJECTED`" คือ transition `in_progress → voided` แบบตรงและสิ้นสุด (`PO_POST_010b`) — ไม่มี state ระหว่างทางและไม่มีการกลับไป `draft` UI badge ที่แสดง "Rejected" (พบใน `403-po-approver-journey.spec.ts` `TC-PO-070311`) สอดคล้องกับ PO ที่เป็น `voided` ซึ่งมี `last_action = rejected` ไม่ใช่ status ที่ persist แยกต่างหาก

แยกจากกัน **"send-back"** (action `/review`) ไม่ย้าย `po_status` เลย — ดู `PO_POST_005` ด้านบน เอกสารรุ่นก่อนหน้าของหน้านี้เคยปนกันระหว่าง "send-back" และ "reject" ว่าเป็น transition `in_progress → draft` เดียวกัน ทั้งสองเป็น endpoint คนละตัวที่มีผลต่างกัน และไม่มีอันไหนเลยที่ไปถึง `draft` จริง ๆ จาก `in_progress`

ไม่มี status การรับทราบของ vendor (`ACKNOWLEDGED`) อยู่ใน source ปัจจุบัน; หากมีการบันทึกการตอบรับของ vendor เลย มันจะเป็น entry ใน `tb_purchase_order_comment` ไม่ใช่ค่า status — claim นี้ไม่ได้ถูก verify โดยตรงในรอบนี้ และควรถือว่ายังไม่ยืนยัน ไม่ใช่ถูกแก้ไข

## 6. กฎ Cross-Module

Rule IDs ตามรูปแบบ `PO_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | ---- |
| `PO_XMOD_001` | [purchase-request](/th/inventory/purchase-request) | เมื่อ `po_type = purchase_request` PO ต้องถูกสร้างผ่าน flow การแปลง PR-to-PO (dialog 2 ขั้นตอน, `po-from-pr-dialog.tsx`: เลือก PR ทั้งใบ → ตรวจสอบ PO ที่ group แล้ว) ซึ่ง group บรรทัด PR ที่อนุมัติแล้วที่เลือกด้วย `(vendor_id, delivery_date, currency_id)` — ยืนยันผ่าน `buildPoGroupKey` ใน `purchase-order.service.ts` — และผลิต PO หนึ่งใบต่อกลุ่ม แต่ละ PO line ที่ได้บรรจุ bridge row หนึ่งหรือมากกว่าหนึ่ง row ใน `tb_purchase_order_detail_tb_purchase_request_detail` ที่ลิงก์กลับไปยัง PR line(s) ต้นทาง (`PO_VAL_014`) ทั้งสอง endpoint (`POST .../purchase-orders/group-pr`, `POST .../purchase-orders/confirm-pr`) list `Permissions: None` ใน Bruno; frontend dialog chain ไม่มีการตรวจสอบ `hasPermission` |
| `PO_XMOD_002` | [purchase-request](/th/inventory/purchase-request) | Bridge รองรับ consolidation (PR lines หลาย → PO line หนึ่ง) และ partial conversion (PR line หนึ่ง → PO lines หลาย) PR line ถือว่า converted เต็มที่เมื่อ `Σ bridge.pr_detail_qty` สำหรับ `pr_detail_id` นั้นเท่ากับ approved quantity ของ PR line |
| `PO_XMOD_003` | [good-receive-note](/th/inventory/good-receive-note) | GRN สามารถสร้างเทียบกับ PO ที่ `po_status ∈ {sent, partial}` เท่านั้น (`PO_AUTH_008`) GRN detail back-reference `tb_purchase_order_detail.id`; pending quantity ที่ใช้ได้สำหรับ receipt คือ `order_qty − received_qty − cancelled_qty` ตาม `PO_POST_006` |
| `PO_XMOD_004` | [good-receive-note](/th/inventory/good-receive-note) | การรับ quantity ที่จะเกิน pending qty ถูก reject เว้นแต่ tenant configuration อนุญาต over-receipt ภายใน tolerance; มิฉะนั้น GRN line ถูก cap ที่ pending qty |
| `PO_XMOD_005` | [vendor-pricelist](/th/inventory/vendor-pricelist) | ที่ PR-to-PO conversion ระบบ snapshot `price` จาก active vendor pricelist สำหรับ tuple `(vendor, product, currency)` หากไม่มี active pricelist row ราคา last-known ของ PR ถูกใช้และ comment `system` ถูก append flag การ coverage pricelist ที่หายไป |
| `PO_XMOD_006` | [vendor-pricelist](/th/inventory/vendor-pricelist) | **ยังไม่ยืนยันบางส่วน แก้ไขบางส่วนในรอบนี้** ว่าการ override ราคาของ buyer เทียบกับ snapshot pricelist ถูก log เป็น "deviation entry" แยกต่างหากหรือไม่ ยังไม่ได้รับการยืนยันโดยตรง ส่วนที่สองของ claim เดิม — ว่า deviation ที่เกิน *pricelist-tolerance band โดยเฉพาะ* บังคับ route PO ไปยัง "high-value approval stage" — ยัง **ไม่ implement ในฐานะกลไกที่รับรู้ deviation**: condition field ที่ `tb_workflow.data.routing_rules` รองรับมีเพียง `total_amount`, `department`, และ `category` (`wf-routing-constants.ts`) — ไม่มี field pricelist-deviation-percentage ให้ route ได้ **แต่ amount-threshold routing เองมีจริง** (ดู `PO_AUTH_004`) — workflow สามารถ route ตาม `total_amount` ตรง ๆ ของ PO ได้ ซึ่งเป็น trigger ที่หยาบกว่า deviation percentage (มัน fire ตามขนาดของ PO ไม่ใช่ตามว่าราคาเบี่ยงจาก pricelist ไปเท่าไร) แต่ก็หมายความว่า PO มูลค่าสูงสามารถถูก escalate ไป stage เพิ่มได้ ไม่ว่าบรรทัดใดจะ deviate จากราคา pricelist หรือไม่ จำนวนและการกำหนด approval stage นอกเหนือจากนี้มาจากนิยาม workflow เท่านั้น |
| `PO_XMOD_007` | ~~AP / Three-way match~~ — **ยังไม่ implement** | **ยังไม่ยืนยัน / น่าจะเป็นข้อมูลที่แต่งขึ้น** ข้อค้นพบเดียวกับ `PO_POST_008`/`PO_POST_009`: ไม่มีโค้ด invoice, AP-posting, หรือ three-way-match ใน `carmen-turborepo-backend-v2` หรือ `carmen-inventory-frontend-react` ผล accrual/GL ของการ post GRN (ถ้ามี) อยู่ทั้งหมดในโมดูล GRN/inventory/costing — ไม่ได้ verify เป็นส่วนหนึ่งของ pass โมดูล PO นี้ |
| `PO_XMOD_008` | [inventory](/th/inventory/inventory) | Inventory on-hand **ไม่** เพิ่มโดย PO posting — เพิ่มเฉพาะเมื่อ GRN post (ซึ่งอยู่ในขอบเขตของโมดูล GRN) PO มีส่วนร่วมปริมาณ "on-order" pipeline ที่ inventory planning อ่านผ่าน `order_qty − received_qty − cancelled_qty` บน PO lines ที่ active |
| `PO_XMOD_009` | [inventory](/th/inventory/inventory) | `base_qty` ของ PO line (คำนวณใน base UoM ผ่าน `PO_CALC_011`) คือ quantity ที่ inventory reservations และการคำนวณ projected-on-hand อ่าน; order UoM สำหรับการแสดงผลฝั่ง vendor เท่านั้น |

## 7. แหล่งอ้างอิง

- `../carmen/docs/purchase-order-management/purchase-order-module.md` — PO consolidated BA (Section 1.3 Business Rules, Section 1.4 System Calculation Rules, Section 6.1 State Diagram, Section 2.5 RBAC) Labels ของ state ถูก reconcile กับค่า enum ของ Prisma ตาม [purchase-order/01-data-model](/th/inventory/purchase-order/01-data-model) § 5
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — โครงสร้าง validation, error-type, และ workflow-state ที่ PO inherit
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — Section 3 (Business Rules) และ Section 3.6 (System Calculation Rules); กฎการคำนวณของ PO (`PO_CALC_*`) เป็นคู่ของกฎ PR โดยตรง (`PR_036`–`PR_055`)
- Sibling: `en/purchase-order/01-data-model.md` — Prisma model canonical, ค่า enum, และ bridge-table linkage ที่ Section 5 และ Section 6 พึ่งพา
- Backend rule implementation: `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-order/` — `purchase-order.service.ts` และ `purchase-order.logic.ts` implement status guards, workflow transitions, และ GRN-facing queries ที่ verify แล้วใน pass นี้ ไม่มี three-way-match orchestration อยู่ในนั้น (ดู § 5 / § 6)
