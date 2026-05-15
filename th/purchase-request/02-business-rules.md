---
title: ใบขอซื้อ — กฎทางธุรกิจ
description: กฎ validation, การคำนวณ, การอนุมัติ, และการ post สำหรับโมดูล purchase-request
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — กฎทางธุรกิจ

## 1. ภาพรวม

หน้านี้รวบรวมกฎที่ครอบคลุมเส้นทางของใบขอซื้อ (Purchase Request — PR) ตั้งแต่ต้นจนจบ ได้แก่ การ validate ฟิลด์ในส่วนหัวและบรรทัด, การคำนวณยอดเงินจากบรรทัดสรุปไปยังเอกสาร, ผู้ที่มีสิทธิ์เดินทาง PR ผ่านห่วงโซ่ workflow, side-effect ที่เกิดขึ้นเมื่อ submit / approve / cancel / convert, และวิธีที่ PR เชื่อมโยงกับโมดูล budget, vendor-pricelist, inventory, และ purchase-order กฎเหล่านี้สังเคราะห์มาจาก `purchase-request-ba.md`, `PR-Technical-Specification.md`, และ `PR-Module-Structure.md` และสอดคล้องกับเอนทิตี Prisma ที่อ้างอิงใน [01-data-model](/purchase-request/01-data-model) — โดยเฉพาะ `tb_purchase_request`, `tb_purchase_request_detail`, `tb_purchase_request_comment`, `tb_purchase_request_detail_comment`, `tb_purchase_request_template`, และ `tb_purchase_request_template_detail`

กฎครอบคลุม 4 ระนาบการกำกับดูแล **Validation rules** ทำงานที่เวลา create / edit / submit เพื่อป้องกันความถูกต้องของฟิลด์ ความสัมพันธ์ FK และ consistency ระหว่างฟิลด์ **Calculation rules** กำหนดสูตรแบบ deterministic สำหรับยอดของบรรทัดและส่วนหัว ภาษี ส่วนลด และการแปลงเป็นสกุลเงินฐาน ทั้งหมดเก็บความละเอียด 5 ตำแหน่งทศนิยมผ่าน Prisma `Decimal(15, 5)` / `Decimal(20, 5)` **Authorization rules** ระบุผู้มีสิทธิ์กระทำกับ PR ในแต่ละ stage ของ workflow และ action ที่ทำได้ (approve, reject, send-back, split-reject) **Posting rules** ระบุการเปลี่ยน status บน `enum_purchase_request_doc_status` และผลกระทบที่ตามมา (soft-commit งบประมาณ, ตารางสะพานสำหรับการแปลงเป็น PO, การเขียน audit comment) กฎข้ามโมดูลเชื่อม PR เข้ากับ budget, inventory, vendor-pricelist, และ purchase-order ตัวอย่างจำนวนเงินในเอกสารใช้สัญลักษณ์ `฿` (บาทไทย)

## 2. กฎ Validation

| รหัสกฎ | เงื่อนไข | บังคับใช้เมื่อ | ข้อผิดพลาด / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `PR_VAL_001` | `tb_purchase_request.pr_no` ต้องมีค่าและไม่ซ้ำในชุดที่ยัง active (`deleted_at IS NULL`) สร้างฝั่ง server; รูปแบบเป็นนโยบายของแอป (เช่น `PR-YYYYMM-NNNN`) | เมื่อสร้าง (insert ส่วนหัว) | ปฏิเสธด้วย `"PR reference number is required and must be unique"` บังคับด้วย unique index `PR0_pr_no_u` ที่ `(pr_no, deleted_at)` |
| `PR_VAL_002` | `requestor_id` ต้องอ้างอิงผู้ใช้ที่ active และต้องตั้ง snapshot `requestor_name` คู่กัน | เมื่อสร้าง / เมื่อ submit | ปฏิเสธด้วย `"Requestor is required"` |
| `PR_VAL_003` | ต้องตั้ง `department_id` และผู้ขอต้องสังกัดแผนกนั้น (หรือได้รับมอบหมายอำนาจสำหรับแผนกนั้น) | เมื่อสร้าง / เมื่อ submit | ปฏิเสธด้วย `"Department is required and must match requestor membership"` |
| `PR_VAL_004` | `workflow_id` ต้องอ้างอิงแถวที่ active ใน `tb_workflow` ที่ scope เอกสารเป็น `purchase-request` | เมื่อ submit | ปฏิเสธด้วย `"A valid PR workflow must be selected"` ค่า `workflow_name` ที่เลือกจะถูก snapshot ลงส่วนหัว |
| `PR_VAL_005` | `pr_date` ต้องมีค่า อยู่ในรูปแบบ ISO-8601 และไม่เกินวันปัจจุบัน (ห้ามวันที่ในอนาคต) | เมื่อ submit | ปฏิเสธด้วย `"PR date cannot be in the future"` |
| `PR_VAL_006` | ต้องมีแถว `tb_purchase_request_detail` อย่างน้อย 1 รายการที่ยังไม่ถูกลบ | เมื่อ submit | ปฏิเสธด้วย `"A PR must contain at least one line item"` |
| `PR_VAL_007` | ทุกบรรทัดต้องมี `product_id` ที่ไม่ null และอ้างอิง `tb_product` ที่ active บรรทัด service / free-text ก็ต้องเลือก product placeholder | เมื่อบันทึกบรรทัด / เมื่อ submit | ปฏิเสธด้วย `"Product is required on every line"` ฐานข้อมูลบังคับ NOT NULL บน `product_id` |
| `PR_VAL_008` | ทุกบรรทัดต้องมี `requested_qty > 0` พร้อม `requested_unit_id` และ `requested_unit_conversion_factor` ที่ไม่ null | เมื่อบันทึกบรรทัด / เมื่อ submit | ปฏิเสธด้วย `"Requested quantity must be greater than zero and have a unit"` |
| `PR_VAL_009` | `delivery_date` ของบรรทัด (ถ้าระบุ) ต้องไม่เร็วกว่า `pr_date` | เมื่อบันทึกบรรทัด / เมื่อ submit | ปฏิเสธด้วย `"Delivery date cannot be earlier than the PR date"` |
| `PR_VAL_010` | `location_id` ของบรรทัดต้องอ้างอิง `tb_location` ที่ active และเป็นชนิดที่ขอสต๊อกได้ ตาม unique index `PR1_purchase_request_product_location_dimension_u` คู่ผสม `(purchase_request_id, product_id, location_id, dimension)` ต้องไม่ซ้ำใน PR เดียวกัน | เมื่อบันทึกบรรทัด | ปฏิเสธรายการซ้ำด้วย `"Same product cannot be requested twice for the same location and dimension"` |
| `PR_VAL_011` | `currency_id` ของบรรทัดต้องอ้างอิง `tb_currency` ที่ active; `exchange_rate` ต้อง > 0 (ค่าเริ่มต้น `1`); `exchange_rate_date` ต้องไม่หลัง `pr_date` | เมื่อบันทึกบรรทัด / เมื่อ submit | ปฏิเสธด้วย `"Currency and exchange rate are required and must be effective on or before the PR date"` |
| `PR_VAL_012` | `tax_rate` และ `discount_rate` ต้องอยู่ระหว่าง `0` ถึง `100` (เปอร์เซ็นต์) `tax_amount` / `discount_amount` ต้อง ≥ `0` การ override ด้วยมือจะตั้ง `is_tax_adjustment` / `is_discount_adjustment` เป็น `true` | เมื่อบันทึกบรรทัด | ปฏิเสธด้วย `"Tax and discount rates must be between 0 and 100"` |
| `PR_VAL_013` | เมื่อระบุ `approved_qty` ค่าต้อง > 0 และ ≤ `requested_qty` (หลังแปลงเป็น UoM ฐานเดียวกัน) ต้องส่ง `approved_unit_id` และ `approved_unit_conversion_factor` พร้อมกัน | เมื่อทำ action อนุมัติ | ปฏิเสธด้วย `"Approved quantity must be positive and may not exceed requested quantity"` |
| `PR_VAL_014` | ผู้ใช้ที่ submit PR ต้องมีสิทธิ์ทำงานใน stage แรกของ workflow ที่ `enum_stage_role = create` | เมื่อ submit | ปฏิเสธด้วย `"You are not authorised to submit purchase requests"` |
| `PR_VAL_015` | ต้องตรวจสอบงบประมาณตอน submit ผลรวมของ `base_total_amount` บวกกับ soft-commitment ที่มีอยู่สำหรับ `(department, budget_category, period)` ต้องไม่เกินงบที่ใช้ได้ในรอบนั้น | เมื่อ submit | ปฏิเสธด้วย `"Budget unavailable for this department / category"` การ override ต้องมีธงจาก budget controller (ดู `PR_AUTH_005`) |
| `PR_VAL_016` | Optimistic concurrency: `doc_version` ของแถวที่กำลังอัปเดตต้องตรงกับค่าที่ client อ่านมา | ทุกการอัปเดต | ปฏิเสธด้วย `"Document was modified by another user; reload and retry"` และเพิ่ม `doc_version` 1 เมื่อเขียนสำเร็จ |

## 3. กฎการคำนวณ

ยอดเงินทั้งหมดเก็บเป็น `Decimal(20, 5)` ในคอลัมน์ของบรรทัด และ `Decimal(15, 5)` ในยอด roll-up และอัตราของส่วนหัว ค่า intermediate จะปัดทศนิยมที่ 5 ตำแหน่งก่อนใช้ในขั้นถัดไป (ปัดแบบ half-up) เลเยอร์การแสดงผลอาจ truncate เพิ่มเป็น 2 ตำแหน่งตามกฎ `PR_UI` แต่ค่าที่ persist ยังคงเป็น 5 ตำแหน่ง

### `PR_CALC_001` — Subtotal ของบรรทัด (สกุลเงินธุรกรรม)

```
sub_total_price = pricelist_price × approved_qty
```

ก่อนการอนุมัติถ้า `approved_qty` ยัง null จะใช้ `requested_qty` ของผู้ขอใน preview แบบ live ส่วนบรรทัดที่ persist หลังอนุมัติแล้วจะใช้ `approved_qty`

### `PR_CALC_002` — จำนวนเงินส่วนลดของบรรทัด

```
discount_amount =
  is_discount_adjustment ? <ค่าที่ผู้ใช้ override>
                         : round(sub_total_price × (discount_rate / 100), 5)
```

### `PR_CALC_003` — Net amount ของบรรทัด

```
net_amount = sub_total_price − discount_amount
```

### `PR_CALC_004` — จำนวนเงินภาษีของบรรทัด

```
tax_amount =
  is_tax_adjustment ? <ค่าที่ผู้ใช้ override>
                    : round(net_amount × (tax_rate / 100), 5)
```

### `PR_CALC_005` — ยอดรวมของบรรทัด

```
total_price = net_amount + tax_amount
```

### `PR_CALC_006` — การแปลงเป็นสกุลเงินฐาน

```
base_price             = round(pricelist_price       × exchange_rate, 5)
base_sub_total_price   = round(base_price            × approved_qty, 5)
base_discount_amount   = round(discount_amount       × exchange_rate, 5)
base_net_amount        = base_sub_total_price − base_discount_amount
base_tax_amount        = round(tax_amount            × exchange_rate, 5)
base_total_price       = base_net_amount + base_tax_amount
```

`exchange_rate` ถูก snapshot ลงบรรทัดตอน submit (คอลัมน์ `exchange_rate`, `Decimal(15, 5)`, ค่าเริ่มต้น `1`) ค่านี้จะคงที่ตลอดอายุของเอกสาร — การอนุมัติซ้ำ **ไม่** ดึงอัตราใหม่

### `PR_CALC_007` — Roll-up ของส่วนหัว

```
tb_purchase_request.base_net_amount   = Σ tb_purchase_request_detail.base_net_amount
tb_purchase_request.base_total_amount = Σ tb_purchase_request_detail.base_total_price
```

คอลัมน์ subtotal / tax ระดับส่วนหัวไม่ได้ persist แยกใน Prisma แต่ derive ใน response ของ API จาก roll-up บรรทัดเมื่อจำเป็น

### `PR_CALC_008` — การแปลง UoM (qty triples)

```
requested_base_qty = round(requested_qty × requested_unit_conversion_factor, 5)
approved_base_qty  = round(approved_qty  × approved_unit_conversion_factor, 5)
foc_base_qty       = round(foc_qty       × foc_unit_conversion_factor, 5)
```

โดย `*_unit_conversion_factor` คือ multiplier จาก UoM ของบรรทัดไปยัง UoM ฐานของ inventory ของ product (`inventory_unit_id`)

### ตัวอย่างคำนวณ (`฿` สกุลฐาน = THB)

บรรทัด PR: น้ำมันพืช 12 ขวด ราคา pricelist `฿185.00000` ต่อขวด ส่วนลด `5%` ภาษี `7%` สกุลเงินธุรกรรม THB, `exchange_rate = 1.00000`

```
sub_total_price       = 185.00000 × 12         = 2,220.00000
discount_amount       = 2,220.00000 × 0.05     =   111.00000
net_amount            = 2,220.00000 − 111.00000 = 2,109.00000
tax_amount            = 2,109.00000 × 0.07     =   147.63000
total_price           = 2,109.00000 + 147.63000 = 2,256.63000
base_total_price      = 2,256.63000 × 1.00000  = 2,256.63000  ฿
```

ตัวอย่างข้ามสกุล: บรรทัดเดียวกันแต่ราคาเป็น USD ที่ `exchange_rate = 35.50000` (THB ต่อ USD) ราคา pricelist `$5.20000`/ขวด:

```
sub_total_price       = 5.20000 × 12           =     62.40000  USD
total_price (USD)     = 62.40000 × 0.95 × 1.07 =     63.42960  USD
base_price            = 5.20000 × 35.50000     =    184.60000  ฿
base_sub_total_price  = 184.60000 × 12         =  2,215.20000  ฿
base_total_price (THB) ≈ 2,251.74180                          ฿
```

## 4. กฎการอนุมัติ

ป้าย role ของ stage มาจาก `enum_stage_role = { create, approve, purchase, issue, view_only }` ห่วงโซ่อนุมัติ 4 stage แบบเริ่มต้นที่ `purchase-request-ba.md` กำหนดไว้คือ

| Stage | บทบาทเริ่มต้น | `enum_stage_role` ทั่วไป | สิ่งที่ stage นี้ทำได้ |
|-------|--------------|---------------------------|------------------------|
| 1 | ผู้ขอ / Department Head | `create` / `approve` | Submit / ส่งซ้ำ; อนุมัติระดับแผนก; reject; ส่งกลับให้ผู้ร่าง |
| 2 | Budget Controller | `approve` | ยืนยันงบประมาณ; reject พร้อมเหตุผล; ส่งกลับไป Stage 1 |
| 3 | Finance | `approve` | ยืนยันผลกระทบการเงิน; reject; ส่งกลับไป Stage 1 หรือ Stage 2 |
| 4 | Procurement Manager | `purchase` | อนุมัติขั้นสุดท้าย; allocate vendor; แปลงเป็น PO; reject; send-back |

Stage จริงสามารถตั้งค่าได้ต่อองค์กรใน `tb_workflow` ห่วงโซ่ที่ PR หนึ่ง ๆ ใช้ขึ้นกับแถวที่ `tb_purchase_request.workflow_id` อ้างอิง

- **`PR_AUTH_001`** — เฉพาะผู้ขอ (`requestor_id == auth.user.id`) หรือผู้ที่ผู้ขอมอบหมายเท่านั้นที่แก้ไข PR ได้ขณะที่ `pr_status = draft` ผู้อื่นเข้าถึงได้แบบอ่านอย่างเดียว
- **`PR_AUTH_002`** — ในแต่ละ stage มีเพียงผู้ใช้ที่อยู่ใน `tb_purchase_request.user_action.execute[]` เท่านั้นที่ทำ action ได้ ระบบจะคำนวณรายชื่อนี้ใหม่ทุกครั้งที่เปลี่ยน stage จากกฎของ role / department / amount-threshold ของ stage นั้น
- **`PR_AUTH_003`** — ผู้อนุมัติแต่ละคนมี action ระดับบรรทัด 3 ตัวคือ **approve**, **reject**, และ **send-back** การ `send-back` ส่ง PR กลับไป stage ก่อนหน้าและตั้ง `last_action = reviewed` ส่วน **split-reject** ให้ผู้อนุมัติ reject บรรทัดเฉพาะแล้วปล่อยส่วนที่เหลือเดินต่อได้ (บรรทัดที่ถูก reject คงอยู่ในเอกสารโดยมี `current_stage_status = rejected`)
- **`PR_AUTH_004`** — การ **reject** ระดับส่วนหัวยุติห่วงโซ่ทันทีและเปลี่ยน `pr_status` เป็น `cancelled` พร้อมปล่อย soft-commitment คืนงบประมาณ (ดู `PR_POST_006`)
- **`PR_AUTH_005`** — Amount threshold เป็นตัวกำหนดว่า stage ใดบ้างจะถูกเรียก (เช่น `Stage 4` อาจถูกข้ามถ้าต่ำกว่า threshold ที่กำหนดได้) ตัวเลข threshold ที่เจาะจงตั้งค่าได้ต่อองค์กร ดูการตั้งค่า workflow ใน `tb_workflow` เอกสารต้นทางไม่ได้กำหนดตัวเลขตายตัว
- **`PR_AUTH_006`** — การมอบอำนาจ (Delegation): ผู้อนุมัติสามารถมอบหมาย stage ของตนให้ผู้อื่นชั่วคราวผ่าน workflow engine ผู้รับมอบหมายจะได้รับสิทธิ์ approve / reject / send-back ในช่วงเวลามอบหมายเท่านั้น ค่า `last_action_by_id` จะสะท้อนผู้รับมอบหมายในขณะที่ audit comment บันทึกที่มาของการมอบหมาย
- **`PR_AUTH_007`** — สิทธิ์ **void** เป็นของ role Finance หรือ system-admin และใช้ได้ทุก stage หลัง submit การ void ตั้ง `pr_status = voided` แช่แข็งเอกสารไม่ให้ทำ action เพิ่ม และปล่อย soft-commitment ที่เปิดอยู่
- **`PR_AUTH_008`** — การแปลงเป็น PO จำกัดเฉพาะ role ที่มี `enum_stage_role = purchase` PR ที่อนุมัติแล้วสามารถคงอยู่ในสถานะ `approved` จนกว่าผู้ใช้ฝั่ง procurement จะสร้าง PO ผ่านตารางสะพาน `tb_purchase_order_detail_tb_purchase_request_detail`

## 5. กฎการ Post

การเปลี่ยน status บันทึกที่ `tb_purchase_request.pr_status` (`enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed, cancelled }`) ทุกการเปลี่ยน status จะเขียนทั้งแถวในไทม์ไลน์ JSON `workflow_history` และแถว `tb_purchase_request_comment` ที่มี `type = system` สำหรับ audit trail

- **`PR_POST_001` — สร้าง.** PR ใหม่ถูก insert ด้วย `pr_status = draft` ยังไม่ตั้ง `last_action = submitted`, `workflow_current_stage` เป็น stage แรกของ workflow และยอดรวม `base_*_amount` เป็นศูนย์จนกว่าจะเพิ่มบรรทัด
- **`PR_POST_002` — Submit.** เปลี่ยน `draft → in_progress` ระบบจะ: (a) ตั้ง `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_*` เป็นผู้ขอ; (b) snapshot `workflow_name` จาก `tb_workflow` ที่เลือก; (c) initialise `stages_status` ต่อ stage; (d) คำนวณ soft-commitment ของงบประมาณ (ดู Section 6) และ insert การกันงบของรอบนั้น; (e) insert `tb_purchase_request_comment` ที่ `type = system` พร้อมข้อความ submit; (f) แจ้งเตือนผู้ใช้ใน `user_action.execute[]` ของ stage แรก
- **`PR_POST_003` — Send-back.** เปลี่ยน `in_progress → in_progress` โดยย้าย `workflow_current_stage` ถอยกลับ 1 stage และตั้ง `last_action = reviewed` ส่งการแจ้งเตือนให้ผู้ใช้ที่ stage ใหม่ (stage ก่อนหน้า) Soft-commitment ยังคงอยู่
- **`PR_POST_004` — Approve (stage กลาง).** อัปเดต `workflow_previous_stage`, `workflow_current_stage`, `workflow_next_stage`, `last_action = approved`, `stages_status` ของ stage ที่เพิ่งผ่าน; append `workflow_history`; คำนวณ `user_action.execute[]` ของ stage ถัดไปใหม่ `pr_status` ยังคงเป็น `in_progress`
- **`PR_POST_005` — Approve ขั้นสุดท้าย.** เมื่อ stage `approve` ตัวสุดท้ายผ่าน `pr_status` เปลี่ยนจาก `in_progress` เป็น `approved` PR พร้อมถูกแปลงเป็น PO; soft-commitment ยังคงอยู่ (จะถูกแปลงเป็น hard commitment เมื่อสร้าง PO — ดู [[purchase-order]])
- **`PR_POST_006` — Reject / Void / Cancel.** การ `reject` ระดับส่วนหัวจากผู้อนุมัติคนใดก็ตามเปลี่ยน `pr_status` เป็น `cancelled` ส่วน `void` จาก Finance / admin เปลี่ยน `pr_status` เป็น `voided` ทั้งสองกรณีปล่อย soft-commitment ของงบประมาณ append `workflow_history` และ insert comment `type = system` พร้อมเหตุผล การ `reject` ระดับบรรทัด (split-reject) ตั้ง `current_stage_status = rejected` ต่อบรรทัดแต่ไม่เปลี่ยน `pr_status`
- **`PR_POST_007` — แปลงเป็น PO.** เมื่อผู้ใช้ procurement สร้าง PO จาก PR ที่อนุมัติแล้วหนึ่งใบหรือหลายใบ แถว `tb_purchase_request_detail` ที่เกี่ยวข้องจะได้แถวในตารางสะพาน `tb_purchase_order_detail_tb_purchase_request_detail` เชื่อมไปยังบรรทัด PO ใหม่ เมื่อ **ทุก** บรรทัดของ PR ถูกแปลงเต็มจำนวน (ผลรวมจำนวนใน PO ที่เชื่อมผ่านสะพานเท่ากับ `approved_base_qty`) หรือถูก cancel อย่างชัดเจน ระบบจะเปลี่ยน `pr_status` จาก `approved` เป็น `completed` การแปลงบางส่วนทำให้ PR อยู่ในสถานะ `approved` พร้อมจำนวนคงเหลือเปิดอยู่จนกว่า PO ถัดไปจะดึงไปใช้
- **`PR_POST_008` — Audit comment เปลี่ยนแปลงไม่ได้.** แถว `tb_purchase_request_comment` ที่มี `type = system` แก้ไขไม่ได้หลัง insert User comment (`type = user`) เจ้าของสามารถ soft-delete (`deleted_at`) ได้ แต่ลบจริงไม่ได้ การ soft-delete จะถูกบันทึกใน audit เช่นกัน

ไม่มีการ post ระดับ stock จาก PR: โมดูล PR เป็นเอกสารแสดงเจตนาในการจัดซื้อและไม่แตะ inventory balance การเคลื่อนไหวสต๊อกเกิดในโมดูล [[purchase-order]] และ Good Receive Note ([[good-receive-note]])

## 6. กฎข้ามโมดูล

- **งบประมาณ (Budget)** — เมื่อ submit ค่า `base_total_amount` ของ PR บวกกับการ allocate ระดับบรรทัดต่อหมวดงบจะสร้าง **soft commitment** ในโมดูล budget (`BudgetData.softCommitmentPR`) commitment นี้ลด `availableBudget` ของรอบงบที่เกี่ยวข้อง Soft commitment จะถูกปล่อยเมื่อ `cancelled` / `voided` และจะถูกแปลงเป็น hard commitment เมื่อสร้าง `tb_purchase_order` (ดู `PR_POST_007` และ [[purchase-order]])
- **Inventory** — UI ตอนกรอกบรรทัดอ่านข้อมูลจาก [[inventory]] เพื่อโชว์ qty คงเหลือ qty สั่งซื้อแล้ว reorder level การใช้เฉลี่ยต่อเดือน และราคาซื้อล่าสุดเป็นบริบทเท่านั้น — ค่าเหล่านี้ **ไม่** ถูก persist ลงบรรทัด PR PR **ไม่** จองหรือเคลื่อนย้าย inventory
- **Vendor และ vendor-pricelist** — แต่ละบรรทัดดึง vendor ที่แนะนำ (preferred vendor) ผ่าน [[vendor-pricelist]] โดย match กับ product, location, และวันที่มีผล ค่า `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price`, และ `pricelist_type` (`enum_pricelist_compare_type`) ที่เลือกจะถูก snapshot ลงบรรทัด เพื่อให้ข้อมูล PR ในอดีตคงที่แม้ pricelist จะถูกแก้ ถ้าผู้ขอเลือก vendor ด้วยมือนอก pricelist ระบบจะตั้ง `pricelist_type` ให้เหมาะสมและอาจตั้ง `is_discount_adjustment` / `is_tax_adjustment`
- **Product** — `product_id` เป็น FK บังคับไป [[product]]; master data ของ product (code, name, local name, SKU, UoM ฐาน inventory) ถูก snapshot ลงบรรทัดตอนเขียน ห้ามเพิ่ม product ที่ inactive (`PR_VAL_007`) บรรทัด service ทำได้โดยเลือก product placeholder ประเภท "service"
- **Purchase-order** — PR เป็นเอกสารต้นน้ำของ [[purchase-order]] เชื่อมผ่านตารางสะพาน `tb_purchase_order_detail_tb_purchase_request_detail` (many-to-many) รองรับทั้ง **consolidation** (หลายบรรทัด PR รวมเป็นบรรทัด PO เดียว — มัก group ตาม vendor และ currency) และ **partial conversion** (บรรทัด PR หนึ่งกระจายเป็นหลายบรรทัด PO ตาม delivery date หรือ vendor) `pr_status` ของ PR จะไม่กลายเป็น `completed` จนกว่าทุกบรรทัดจะถูก bridge เต็มหรือถูก cancel (`PR_POST_007`)
- **Template** — `tb_purchase_request_template` / `tb_purchase_request_template_detail` ใช้สำหรับ seed เท่านั้น ไม่เข้า workflow เอง การสร้าง PR จาก template จะ clone บรรทัดของ template เป็น `tb_purchase_request` ใหม่ที่มี status `draft` และคัดลอก `workflow_id` ของ template เป็น default workflow ของ PR ใหม่

## 7. เอกสารอ้างอิง

- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — แหล่งวิเคราะห์ธุรกิจหลัก รหัสกฎ `PR_CRT_*`, `PR_BDG_*`, `PR_WFL_*`, `PR_ITM_*` รวมถึง block การคำนวณ `PR_036`–`PR_055`
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md` — กฎเชิงเทคนิค, Zod validation schema (`PurchaseRequestSchema`, `PurchaseRequestItemSchema`), sequence diagram ของ approval flow และการ routing workflow ตาม threshold
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — การบูรณาการข้ามโมดูล (budget, inventory, workflow, notification), role-based permission, และ state shape
- หน้าพี่น้อง: [01-data-model](/purchase-request/01-data-model) — เอนทิตี Prisma ที่ canonical, enum, และความละเอียดของการปัด (`Decimal(15, 5)` / `Decimal(20, 5)`)
- การ implement กฎฝั่ง backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request/` (service ของส่วนหัว), `purchase-request-comment/`, และ `purchase-request-template/` รวมถึง edge ของ API ที่ `apps/backend-gateway/src/application/purchase-requests/`
