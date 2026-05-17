---
title: ใบขอซื้อ (Purchase Request) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การให้สิทธิ์ และการ posting ของโมดูล purchase-request
published: true
date: 2026-05-17T12:00:00.000Z
tags: purchase-request, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `PR_VAL_*` validation &nbsp;·&nbsp; `PR_AUTH_*` permission &nbsp;·&nbsp; `PR_CALC_*` calc &nbsp;·&nbsp; `PR_POST_*` posting
> **จำนวนกฎ:** ประมาณ 40 กฎ
> **กลุ่มผู้ใช้:** ผู้เขียน test + developer — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรสถานะ:** Section 5.1 (เมื่อมี) มี callout ความต่างระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้แจกแจงกฎที่กำกับ Purchase Request (PR) ตั้งแต่ต้นจนจบ: วิธีการ validate ฟิลด์ของ header และบรรทัด, วิธีคำนวณยอดเงินจากบรรทัดไปจนถึง roll-up ระดับเอกสาร, ใครย้าย PR ผ่าน chain ของ workflow ได้, side-effect ใดเกิดขึ้นตอน submit / approve / cancel / convert และ PR ทำงานร่วมกับโมดูล budget, vendor-pricelist, inventory และ purchase-order อย่างไร กฎเหล่านี้สังเคราะห์มาจาก `purchase-request-ba.md`, `PR-Technical-Specification.md`, และ `PR-Module-Structure.md` และสอดคล้องกับ entity ของ Prisma ที่บันทึกไว้ใน [01-data-model](/purchase-request/01-data-model) — โดยเฉพาะ `tb_purchase_request`, `tb_purchase_request_detail`, `tb_purchase_request_comment`, `tb_purchase_request_detail_comment`, `tb_purchase_request_template`, และ `tb_purchase_request_template_detail`

กฎครอบคลุมสี่มิติของ governance **Validation rules** ทำงานตอน create / edit / submit เพื่อปกป้องความถูกต้องของฟิลด์, referential integrity, และความสอดคล้องข้ามฟิลด์ **Calculation rules** กำหนดสูตรแบบ deterministic สำหรับยอดบรรทัดและ header, ภาษี, ส่วนลด และการแปลงสกุลเงินฐาน เก็บไว้ที่ 5 ตำแหน่งทศนิยมผ่าน Prisma `Decimal(15, 5)` / `Decimal(20, 5)` **Authorization rules** อธิบายว่าใครลงมือกับ PR ได้ที่ stage ใดของ workflow และ action ใด (approve, reject, send-back, split-reject) ใช้ได้ **Posting rules** อธิบายการ transition สถานะบน `enum_purchase_request_doc_status` และผลปลายน้ำ (soft-commit budget, bridge การแปลงเป็น PO, การเขียน audit comment) Cross-module rules ผูก PR กับ budget, inventory, vendor-pricelist และ purchase-order จำนวนเงินที่ระบุในตัวอย่างใช้ `฿` (บาท)

## 2. กฎการตรวจสอบ (Validation Rules)

| Rule ID | เงื่อนไข | บังคับเมื่อใด | ข้อผิดพลาด / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `PR_VAL_001` | `tb_purchase_request.pr_no` ต้องมีและไม่ซ้ำในเซตที่ active (`deleted_at IS NULL`) สร้างฝั่ง server; format เป็น application-policy (เช่น `PR-YYYYMM-NNNN`) | ตอน create (insert header) | ปฏิเสธด้วย `"PR reference number is required and must be unique"` รองรับโดย unique index `PR0_pr_no_u` บน `(pr_no, deleted_at)` |
| `PR_VAL_002` | `requestor_id` ต้องอ้างถึงผู้ใช้ที่ active; snapshot `requestor_name` ต้องถูก populate ไปด้วยกัน | ตอน create / ตอน submit | ปฏิเสธด้วย `"Requestor is required"` |
| `PR_VAL_003` | `department_id` ต้องถูก set และ requestor ต้องสังกัดแผนกนั้น (หรือมีอำนาจ delegated สำหรับแผนกนั้น) | ตอน create / ตอน submit | ปฏิเสธด้วย `"Department is required and must match requestor membership"` |
| `PR_VAL_004` | `workflow_id` ต้องอ้างถึงแถวที่ active ใน `tb_workflow` ที่ document scope เป็น `purchase-request` | ตอน submit | ปฏิเสธด้วย `"A valid PR workflow must be selected"` `workflow_name` ที่เลือกถูก snapshot ลงบน header |
| `PR_VAL_005` | `pr_date` ต้องมี, อยู่ในรูป ISO-8601 ที่ถูกต้อง และไม่อยู่หลังวันนี้ (ห้ามเอกสารวันในอนาคต) | ตอน submit | ปฏิเสธด้วย `"PR date cannot be in the future"` |
| `PR_VAL_006` | ต้องมีแถว `tb_purchase_request_detail` ที่ไม่ถูกลบอย่างน้อยหนึ่งแถวแนบอยู่ | ตอน submit | ปฏิเสธด้วย `"A PR must contain at least one line item"` |
| `PR_VAL_007` | ทุกบรรทัด detail ต้องอ้างถึง `product_id` ที่ไม่ null และ resolve เป็นแถวที่ active ใน `tb_product` บรรทัด service / free-text ก็ยังต้องเลือก placeholder ของสินค้า | ตอน save บรรทัด / ตอน submit | ปฏิเสธด้วย `"Product is required on every line"` DB บังคับ NOT NULL บน `product_id` ด้วย |
| `PR_VAL_008` | ทุกบรรทัด detail ต้องมี `requested_qty > 0` พร้อม `requested_unit_id` และ `requested_unit_conversion_factor` ที่ไม่ null | ตอน save บรรทัด / ตอน submit | ปฏิเสธด้วย `"Requested quantity must be greater than zero and have a unit"` |
| `PR_VAL_009` | `delivery_date` บนบรรทัด ถ้ามี ต้องเท่ากับหรือหลัง `pr_date` | ตอน save บรรทัด / ตอน submit | ปฏิเสธด้วย `"Delivery date cannot be earlier than the PR date"` |
| `PR_VAL_010` | `location_id` บนบรรทัดต้องอ้างถึง `tb_location` ที่ active ที่เป็นประเภทที่ขอ stock ได้ ตาม unique index `PR1_purchase_request_product_location_dimension_u` คู่ `(purchase_request_id, product_id, location_id, dimension)` ต้องไม่ซ้ำภายใน PR | ตอน save บรรทัด | ปฏิเสธ duplicate ด้วย `"Same product cannot be requested twice for the same location and dimension"` |
| `PR_VAL_011` | `currency_id` บนบรรทัดต้องอ้างถึง `tb_currency` ที่ active; `exchange_rate` ต้อง > 0 (default `1`); `exchange_rate_date` ต้องเท่ากับหรือก่อน `pr_date` | ตอน save บรรทัด / ตอน submit | ปฏิเสธด้วย `"Currency and exchange rate are required and must be effective on or before the PR date"` |
| `PR_VAL_012` | `tax_rate` และ `discount_rate` ต้องอยู่ระหว่าง `0` กับ `100` (เปอร์เซ็นต์) `tax_amount` / `discount_amount` ต้อง ≥ `0` Manual override ทำให้ `is_tax_adjustment` / `is_discount_adjustment` กลายเป็น `true` | ตอน save บรรทัด | ปฏิเสธด้วย `"Tax and discount rates must be between 0 and 100"` |
| `PR_VAL_013` | เมื่อมี `approved_qty` ต้อง > 0 และ ≤ `requested_qty` (หลังแปลงเป็นหน่วยฐาน) ต้องส่ง `approved_unit_id` และ `approved_unit_conversion_factor` มาด้วย | ตอน approve | ปฏิเสธด้วย `"Approved quantity must be positive and may not exceed requested quantity"` |
| `PR_VAL_014` | ผู้ใช้ที่ submit PR ต้องมีสิทธิ์ลงมือกับ stage `create` แรกของ workflow (`enum_stage_role = create`) | ตอน submit | ปฏิเสธด้วย `"You are not authorised to submit purchase requests"` |
| `PR_VAL_015` | ต้องเช็คความพร้อมของ budget ตอน submit ผลรวมของ `base_total_amount` บวก soft-commitment ที่มีอยู่สำหรับสามตัว `(department, budget_category, period)` ต้องไม่เกิน budget ที่ใช้ได้ของงวด | ตอน submit | ปฏิเสธด้วย `"Budget unavailable for this department / category"` Override ต้องมี flag ของ budget-controller (ดู `PR_AUTH_005`) |
| `PR_VAL_016` | Optimistic concurrency: `doc_version` บนแถวที่กำลังอัปเดตต้องเท่ากับค่าที่ client อ่านมา | ตอน update ใด ๆ | ปฏิเสธด้วย `"Document was modified by another user; reload and retry"` และ bump `doc_version` ขึ้น 1 เมื่อ write สำเร็จ |

## 3. กฎการคำนวณ (Calculation Rules)

ยอดเงินทั้งหมดเก็บเป็น `Decimal(20, 5)` บนคอลัมน์บรรทัดและ `Decimal(15, 5)` บน roll-up ของ header และอัตรา ค่ากลางถูก round ไปที่ 5 ตำแหน่งทศนิยมก่อนใช้ในขั้นถัดไป (half-up rounding) ชั้น display อาจตัดต่อให้เหลือ 2 ทศนิยมตามกฎ `PR_UI` แต่ค่าที่ persist ยังคงไว้ที่ 5 ทศนิยม

### `PR_CALC_001` — Line subtotal (สกุลเงินธุรกรรม)

```
sub_total_price = pricelist_price × approved_qty
```

ถ้า `approved_qty` เป็น null ก่อนการอนุมัติ `requested_qty` ของ requestor จะถูกใช้ใน live preview; บรรทัดที่ persist หลังอนุมัติใช้ `approved_qty`

### `PR_CALC_002` — Line discount amount

```
discount_amount =
  is_discount_adjustment ? <user override>
                         : round(sub_total_price × (discount_rate / 100), 5)
```

### `PR_CALC_003` — Line net amount

```
net_amount = sub_total_price − discount_amount
```

### `PR_CALC_004` — Line tax amount

```
tax_amount =
  is_tax_adjustment ? <user override>
                    : round(net_amount × (tax_rate / 100), 5)
```

### `PR_CALC_005` — Line total

```
total_price = net_amount + tax_amount
```

### `PR_CALC_006` — Base-currency conversion

```
base_price             = round(pricelist_price       × exchange_rate, 5)
base_sub_total_price   = round(base_price            × approved_qty, 5)
base_discount_amount   = round(discount_amount       × exchange_rate, 5)
base_net_amount        = base_sub_total_price − base_discount_amount
base_tax_amount        = round(tax_amount            × exchange_rate, 5)
base_total_price       = base_net_amount + base_tax_amount
```

`exchange_rate` ถูก snapshot บนบรรทัดตอน submit (คอลัมน์ `exchange_rate`, `Decimal(15, 5)`, default `1`) อัตราถูกตรึงตลอดอายุของเอกสาร — การ re-approve **ไม่** re-fetch อัตรา

### `PR_CALC_007` — Header roll-up

```
tb_purchase_request.base_net_amount   = Σ tb_purchase_request_detail.base_net_amount
tb_purchase_request.base_total_amount = Σ tb_purchase_request_detail.base_total_price
```

คอลัมน์ subtotal / tax ระดับ header ไม่ได้ persist แยกใน Prisma — derive ใน API response จาก roll-up ของบรรทัดเมื่อจำเป็น

### `PR_CALC_008` — UoM conversion (จำนวนสามชุด)

```
requested_base_qty = round(requested_qty × requested_unit_conversion_factor, 5)
approved_base_qty  = round(approved_qty  × approved_unit_conversion_factor, 5)
foc_base_qty       = round(foc_qty       × foc_unit_conversion_factor, 5)
```

โดยที่ `*_unit_conversion_factor` คือ multiplier จาก UoM ของบรรทัดไปยัง UoM ฐานของ inventory ของสินค้า (`inventory_unit_id`)

### ตัวอย่างที่คำนวณเสร็จ (`฿`, ฐาน = THB)

PR line: 12 × ขวดน้ำมันปรุงอาหารราคา pricelist `฿185.00000`/ขวด ส่วนลด `5%` ภาษี `7%` สกุลเงินธุรกรรม THB, `exchange_rate = 1.00000`

```
sub_total_price       = 185.00000 × 12         = 2,220.00000
discount_amount       = 2,220.00000 × 0.05     =   111.00000
net_amount            = 2,220.00000 − 111.00000 = 2,109.00000
tax_amount            = 2,109.00000 × 0.07     =   147.63000
total_price           = 2,109.00000 + 147.63000 = 2,256.63000
base_total_price      = 2,256.63000 × 1.00000  = 2,256.63000  ฿
```

ตัวอย่างข้ามสกุลเงิน: บรรทัดเดียวกันแต่ตั้งราคาเป็น USD ด้วย `exchange_rate = 35.50000` (THB ต่อ USD), pricelist `$5.20000`/ขวด:

```
sub_total_price       = 5.20000 × 12           =     62.40000  USD
total_price (USD)     = 62.40000 × 0.95 × 1.07 =     63.42960  USD
base_price            = 5.20000 × 35.50000     =    184.60000  ฿
base_sub_total_price  = 184.60000 × 12         =  2,215.20000  ฿
base_total_price (THB) ≈ 2,251.74180                          ฿
```

## 4. กฎการให้สิทธิ์ (Authorization Rules)

Label ของ stage role มาจาก `enum_stage_role = { create, approve, purchase, issue, view_only }` Chain อนุมัติ default แบบสี่ stage ที่จับใน `purchase-request-ba.md` คือ:

| Stage | Role default | `enum_stage_role` ที่ใช้ทั่วไป | สิ่งที่ stage นี้ทำได้ |
|-------|--------------|---------------------------|------------------------|
| 1 | Requestor / Department Head | `create` / `approve` | Submit / re-submit; อนุมัติระดับแผนก; reject; ส่งกลับให้ผู้ตั้ง |
| 2 | Budget Controller | `approve` | ยืนยัน budget; reject พร้อมเหตุผล; ส่งกลับไปยัง Stage 1 |
| 3 | Finance | `approve` | ยืนยันผลกระทบทางการเงิน; reject; ส่งกลับไปยัง Stage 1 หรือ Stage 2 |
| 4 | Procurement Manager | `purchase` | อนุมัติสุดท้าย; allocate vendor; แปลงเป็น PO; reject; ส่งกลับ |

Stage จริงตั้งค่าได้ต่อองค์กรใน `tb_workflow`; chain ที่ PR ใบหนึ่งใช้ตัดสินโดยแถวที่อ้างผ่าน `tb_purchase_request.workflow_id`

- **`PR_AUTH_001`** — เฉพาะ requestor (`requestor_id == auth.user.id`) หรือผู้ที่ requestor delegated ให้เท่านั้นที่แก้ไข PR ได้ขณะ `pr_status = draft` ผู้ใช้อื่นมีสิทธิ์อ่านเท่านั้น
- **`PR_AUTH_002`** — ในแต่ละ stage เฉพาะผู้ใช้ที่อยู่ใน `tb_purchase_request.user_action.execute[]` เท่านั้นที่ลงมือทำได้ list จะถูกคำนวณใหม่ทุกการ transition stage จากกฎ role / department / amount-threshold ของ stage
- **`PR_AUTH_003`** — ผู้อนุมัติทุกคนมี action ระดับบรรทัดสามอย่าง: **approve**, **reject**, และ **send-back** `send-back` ส่ง PR กลับไป stage ก่อนหน้าด้วย `last_action = reviewed`; **split-reject** ให้ผู้อนุมัติ reject บรรทัดเฉพาะในขณะที่ส่วนที่เหลือเดินต่อ (บรรทัดที่ถูก reject ยังอยู่บนเอกสารด้วย `current_stage_status = rejected`)
- **`PR_AUTH_004`** — **Reject** ระดับ header ยุติ chain ทันทีและย้าย `pr_status` เป็น `cancelled`; soft-commitment กับ budget ถูกปล่อย (ดู `PR_POST_006`)
- **`PR_AUTH_005`** — Amount threshold ขับว่า stage ใดทำงาน (เช่น `Stage 4` อาจข้ามถ้าต่ำกว่า threshold ที่ตั้งไว้) Threshold ตั้งค่าได้ต่อองค์กร ดูการตั้งค่า workflow ใน `tb_workflow` เอกสารต้นทางไม่ได้กำหนดตัวเลขเฉพาะ
- **`PR_AUTH_006`** — Delegation: ผู้อนุมัติสามารถ delegate stage ของตนให้ผู้ใช้คนอื่นชั่วคราวผ่าน workflow engine ผู้ใช้ที่ได้รับ delegated สืบทอดสิทธิ์ approve / reject / send-back เดียวกันเฉพาะช่วง delegation; `last_action_by_id` สะท้อน delegate ขณะที่ audit comment จับแหล่งที่มาของ delegation
- **`PR_AUTH_007`** — สิทธิ์ **Void** เป็นของ role Finance หรือ system-admin และใช้ได้ทุก stage หลัง submit Void ทำให้ `pr_status = voided`, freeze เอกสารจาก action เพิ่ม และปล่อย soft-commitment ที่เปิดอยู่
- **`PR_AUTH_008`** — การแปลงเป็น PO ถูกจำกัดเฉพาะ role ที่มี `enum_stage_role = purchase` PR ที่ approved อาจค้างที่ status `approved` จนกว่าผู้ใช้ procurement จะสร้าง PO ผ่าน bridge `tb_purchase_order_detail_tb_purchase_request_detail`

> ⚠️ **ความต่าง — bulk-toolbar กับ action ระดับแถว (BRD FR-PR-005A):** BRD ระบุปุ่ม **Approve / Reject / Send for Review** แบบ standalone ต่อแถวบน list / header ของ PR detail UI ปัจจุบันที่ live เปิด action เหล่านี้เป็น **bulk toolbar action** ใน Edit Mode เท่านั้น (ผ่าน dropdown Select All → bulk action toolbar) Bulk action ที่ยืนยันแล้ว: Approve, Reject, Send for Review (BRD "Return Selected"), Split ปุ่มระดับแถวแบบ standalone ยังไม่มี ที่มา: `Test_case/Purchase_Request/Approver/INDEX.md` (วันที่จับภาพ 2026-04-19) สถานะการตรวจสอบ: ยืนยันแล้วสำหรับ HOD; assumed สำหรับ FC / GM / Owner

> ⚠️ **ความต่าง — tooltip ของปุ่ม Send-back ที่ disabled:** ปุ่ม Submit / Send-back ถูก disable เมื่อ pre-condition ไม่ผ่าน (`PR_VAL_004`–`PR_VAL_006`) แต่ live UI ไม่มี tooltip อธิบายเหตุผลที่ disable ช่องว่างด้าน usability ที่จับไว้ใน `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § 6.4

## 5. กฎการ Posting

การ transition สถานะถูกบันทึกบน `tb_purchase_request.pr_status` (`enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed, cancelled }`) ทุกการ transition เขียนทั้งแถว header ใน `workflow_history` (timeline JSON) และแถว `tb_purchase_request_comment` ด้วย `type = system` สำหรับ audit trail

- **`PR_POST_001` — Create.** PR ใหม่ถูก insert ด้วย `pr_status = draft`, `last_action = submitted` ยัง **ไม่** ถูก set, `workflow_current_stage` เป็น entry stage ของ workflow และยอด `base_*_amount` เป็นศูนย์จนกว่าจะเพิ่มบรรทัด
- **`PR_POST_002` — Submit.** Transition `draft → in_progress` ระบบ: (a) ตั้ง `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_*` เป็น requestor; (b) snapshot `workflow_name` จาก `tb_workflow` ที่เลือก; (c) initialise `stages_status` ตาม stage; (d) คำนวณ soft-commitment ของ budget (ดู Section 6) และ insert period reservation; (e) insert `tb_purchase_request_comment` ด้วย `type = system` และข้อความ submit; (f) แจ้งผู้ใช้ใน `user_action.execute[]` ของ stage อนุมัติแรก BRD `FR-PR-005` ตั้ง SLA การแจ้งผู้อนุมัติคนแรกที่ **5 นาที** จากตอน submit; SLA ยังไม่ได้ตรวจสอบกับ notification service จริง

> ⚠️ **ความต่าง — SLA การแจ้งยังไม่ได้ตรวจสอบ:** BRD `FR-PR-005` ระบุ SLA อีเมล 5 นาทีสำหรับผู้อนุมัติคนแรกตอน submit ยังไม่ได้ตรวจสอบใน test environment เพราะการส่งขึ้นกับ availability ของ notification service ที่มา: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-06

> ⚠️ **ความต่าง — budget check `warn` vs `block`:** BRD `FR-PR-004` ทำให้ budget check ตั้งค่าได้ตามนโยบายขององค์กร — *warn* (อนุญาตให้ submit พร้อม warning) หรือ *block* (กัน submit เมื่อเกิน budget) บัญชี test ปัจจุบันมีราคาต่อหน่วยเป็นศูนย์บนสินค้า (commitment = `฿0.00`) ทำให้พฤติกรรม live สำหรับการ submit ที่เกิน budget ยังสังเกตไม่ได้ ที่มา: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-09
- **`PR_POST_003` — Send-back.** Transition `in_progress → in_progress` โดย `workflow_current_stage` ย้ายไปก่อนหน้าหนึ่ง stage และ `last_action = reviewed` แจ้งผู้ใช้ที่ stage ใหม่ (ก่อนหน้า) Soft-commitment ยังอยู่
- **`PR_POST_004` — Approve (intermediate stage).** อัปเดต `workflow_previous_stage`, `workflow_current_stage`, `workflow_next_stage`, `last_action = approved`, `stages_status` สำหรับ stage ที่เพิ่งเสร็จ; append `workflow_history`; คำนวณ `user_action.execute[]` ใหม่สำหรับ stage ถัดไป `pr_status` ยังคง `in_progress`
- **`PR_POST_005` — Final approve.** เมื่อ stage `approve` สุดท้ายผ่าน `pr_status` พลิกจาก `in_progress` เป็น `approved` PR พร้อมแปลงเป็น PO แล้ว; soft-commitment ยังอยู่ (จะแปลงเป็น hard commitment เมื่อสร้าง PO — ดู [[purchase-order]])
- **`PR_POST_006` — Reject / Void / Cancel.** `reject` ระดับ header จากผู้อนุมัติคนใดย้าย `pr_status` เป็น `cancelled` Finance / admin `void` ย้าย `pr_status` เป็น `voided` ทั้งสอง transition ปล่อย soft-commitment ของ budget, append `workflow_history` และ insert comment `type = system` พร้อมเหตุผล `reject` ระดับบรรทัด (split-reject) ตั้ง `current_stage_status = rejected` ต่อบรรทัดแต่ไม่เปลี่ยน `pr_status`
- **`PR_POST_007` — Convert to PO.** เมื่อผู้ใช้ procurement สร้าง PO จาก PR ที่ approved หนึ่งใบหรือมากกว่า แถว `tb_purchase_request_detail` แต่ละแถวที่ได้รับผลกระทบจะได้แถวใน bridge `tb_purchase_order_detail_tb_purchase_request_detail` ที่ link ไปยังบรรทัด PO ใหม่ เมื่อ **ทุก** บรรทัดของ PR ถูกแปลงเต็ม (ผลรวมของจำนวน PO ที่ link ผ่าน bridge เท่ากับ `approved_base_qty`) หรือถูกยกเลิกชัดเจน ระบบพลิก `pr_status` จาก `approved` เป็น `completed` การแปลงบางส่วนทำให้ PR คงอยู่ที่ `approved` พร้อมจำนวนที่เหลือเปิดไว้จนกว่า PO ถัดไปจะมารับ
- **`PR_POST_008` — Audit comment เป็น immutable.** แถว `tb_purchase_request_comment` ที่ `type = system` ไม่สามารถแก้ไขได้หลัง insert User comment (`type = user`) สามารถ soft-delete (`deleted_at`) โดยผู้เขียนได้แต่ไม่มีการ hard-delete; การ soft-delete เองถูกจับโดย audit

ไม่มี posting ระดับ stock จาก PR: โมดูล PR เป็นเอกสารแสดงเจตนา procurement และไม่กระทบยอด inventory การเคลื่อนไหวของ stock เกิดปลายน้ำใน [[purchase-order]] และ Good Receive Note ([[good-receive-note]])

## 6. กฎข้ามโมดูล

- **Budget** — ตอน submit, `base_total_amount` ของ PR บวกการ allocate ต่อบรรทัดเข้ากับ budget category สร้าง **soft commitment** ในโมดูล budget (`BudgetData.softCommitmentPR`) Commitment ลด `availableBudget` ของงวดที่เกี่ยวข้อง Soft commitment ถูกปล่อยตอน `cancelled` / `voided` และแปลงเป็น hard commitment ตอนสร้าง `tb_purchase_order` (ดู `PR_POST_007` และ [[purchase-order]])
- **Inventory** — UI ที่จับบรรทัดอ่านจาก [[inventory]] เพื่อแสดงจำนวน on-hand, on-order qty, reorder level, average monthly usage และราคาซื้อล่าสุดเป็นบริบทเท่านั้น — ค่าเหล่านี้ไม่ persist บน PR detail PR **ไม่** จองหรือย้าย inventory
- **Vendor & vendor-pricelist** — แต่ละบรรทัด detail resolve preferred vendor (optional) ผ่าน lookup [[vendor-pricelist]] ตาม product, location และ effective date ที่ขอ `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price`, และ `pricelist_type` (`enum_pricelist_compare_type`) ที่เลือกถูก snapshot ลงบนบรรทัดเพื่อให้ข้อมูล PR ในอดีตคงที่แม้ pricelist จะเปลี่ยน ถ้า requestor เลือก vendor นอก pricelist ด้วยมือ `pricelist_type` จะถูกตั้งให้สอดคล้องและ `is_discount_adjustment` / `is_tax_adjustment` อาจถูก flag
- **Product** — `product_id` เป็น FK required ไปยัง [[product]]; master data สินค้า (code, name, local name, SKU, UoM ฐานของ inventory) ถูก snapshot ลงบนบรรทัดตอน write สินค้า inactive ไม่สามารถเพิ่มได้ (`PR_VAL_007`) พฤติกรรม service-line ทำได้โดยเลือก placeholder สินค้า "service"
- **Purchase-order** — PR เป็นเอกสารต้นน้ำสำหรับ [[purchase-order]] link คือตาราง bridge `tb_purchase_order_detail_tb_purchase_request_detail` (many-to-many) รองรับทั้ง **consolidation** (หลายบรรทัด PR feed หนึ่งบรรทัด PO — มัก group ตาม vendor และ currency) และ **partial conversion** (หนึ่งบรรทัด PR แตกเป็นหลายบรรทัด PO ข้ามวันส่งของหรือ vendor) `pr_status` ของ PR ไม่พลิกเป็น `completed` จนกว่าทุกบรรทัดจะถูก bridge เต็มหรือยกเลิก (`PR_POST_007`)
- **Templates** — `tb_purchase_request_template` / `tb_purchase_request_template_detail` ใช้ seed เท่านั้น มันไม่เข้าสู่ workflow ของตัวเอง; การสร้าง PR จาก template clone บรรทัดของ template เข้าสู่ `tb_purchase_request` ใหม่ด้วยสถานะ `draft` `workflow_id` ของ template ถูก copy เป็น workflow default ของ PR ใหม่

## 7. แหล่งอ้างอิง

- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — แหล่ง business-analysis หลัก; rule ID `PR_CRT_*`, `PR_BDG_*`, `PR_WFL_*`, `PR_ITM_*`, บวก block การคำนวณ `PR_036`–`PR_055`
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md` — กฎเชิงเทคนิค, schema validation Zod (`PurchaseRequestSchema`, `PurchaseRequestItemSchema`), sequence diagram ของ approval flow, และการ routing workflow ตาม threshold
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — integration ข้ามโมดูล (budget, inventory, workflow, notification), permission ตาม role, และ state shape
- หน้าพี่น้อง: [01-data-model](/purchase-request/01-data-model) — entity Prisma ตามมาตรฐาน, enum และความแม่นยำในการ round (`Decimal(15, 5)` / `Decimal(20, 5)`)
- การ implement กฎฝั่ง backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request/` (header service), `purchase-request-comment/`, และ `purchase-request-template/` บวก API edge ใน `apps/backend-gateway/src/application/purchase-requests/`
