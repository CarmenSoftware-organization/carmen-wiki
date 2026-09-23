---
title: ใบขอซื้อ (Purchase Request) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การให้สิทธิ์ และการ posting ของโมดูล purchase-request
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-request, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `PR_VAL_*` validation &nbsp;·&nbsp; `PR_AUTH_*` permission &nbsp;·&nbsp; `PR_CALC_*` calc &nbsp;·&nbsp; `PR_POST_*` posting
> **จำนวนกฎ:** ประมาณ 40 กฎ &nbsp;·&nbsp; **ตรวจสอบซ้ำ 2026-09-22** กับ `apps/micro-business/src/procurement/purchase-request/logic/purchase-request.validate.ts` (กฎตอน submit), `logic/verify/*` (pre-flight), `purchase-request.service.ts` (การลบ / การเขียนสถานะ) — กฎที่ไม่มี code path ถูกทำเครื่องหมาย **ยังไม่ยืนยัน** แทนที่จะระบุเป็นข้อเท็จจริง
> **กลุ่มผู้ใช้:** ผู้เขียน test + developer — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรสถานะ:** Section 5.1 (เมื่อมี) มี callout ความต่างระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้แจกแจงกฎที่กำกับ Purchase Request (PR) ตั้งแต่ต้นจนจบ: วิธีการ validate ฟิลด์ของ header และบรรทัด, วิธีคำนวณยอดเงินจากบรรทัดไปจนถึง roll-up ระดับเอกสาร, ใครย้าย PR ผ่าน chain ของ workflow ได้, side-effect ใดเกิดขึ้นตอน submit / approve / reject / delete / convert และ PR ทำงานร่วมกับโมดูล vendor-pricelist, inventory และ purchase-order อย่างไร กฎเหล่านี้สังเคราะห์มาจาก `purchase-request-ba.md`, `PR-Technical-Specification.md`, และ `PR-Module-Structure.md` และสอดคล้องกับ entity ของ Prisma ที่บันทึกไว้ใน [01-data-model](/th/inventory/purchase-request/01-data-model) — โดยเฉพาะ `tb_purchase_request`, `tb_purchase_request_detail`, `tb_purchase_request_comment`, `tb_purchase_request_detail_comment`, `tb_purchase_request_template`, และ `tb_purchase_request_template_detail`

กฎครอบคลุมสี่มิติของ governance **Validation rules** ทำงานตอน create / edit / submit เพื่อปกป้องความถูกต้องของฟิลด์, referential integrity, และความสอดคล้องข้ามฟิลด์ **Calculation rules** กำหนดสูตรแบบ deterministic สำหรับยอดบรรทัดและ header, ภาษี, ส่วนลด และการแปลงสกุลเงินฐาน เก็บไว้ที่ 5 ตำแหน่งทศนิยมผ่าน Prisma `Decimal(15, 5)` / `Decimal(20, 5)` **Authorization rules** อธิบายว่าใครลงมือกับ PR ได้ที่ stage ใดของ workflow และ action ใด (approve, reject, send-back, split-reject) ใช้ได้ **Posting rules** อธิบายการ transition สถานะบน `enum_purchase_request_doc_status` และผลปลายน้ำ (bridge การแปลงเป็น PO, การเขียน audit comment) Cross-module rules ผูก PR กับ inventory, vendor-pricelist และ purchase-order *(soft-commitment ของ budget — ที่ระบุในเอกสารรุ่นก่อน — ไม่มี code path ที่ไหนเลยใน backend, frontend หรือ Bruno collection; กฎเรื่องงบประมาณทุกข้อด้านล่างถูกทำเครื่องหมายว่ายังไม่ยืนยัน)* จำนวนเงินที่ระบุในตัวอย่างใช้ `฿` (บาท)

## 2. กฎการตรวจสอบ (Validation Rules)

| Rule ID | เงื่อนไข | บังคับเมื่อใด | ข้อผิดพลาด / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `PR_VAL_001` | `tb_purchase_request.pr_no` ต้องมีและไม่ซ้ำในเซตที่ active (`deleted_at IS NULL`) สร้างฝั่ง server; format เป็น application-policy (เช่น `PR-YYYYMM-NNNN`) | ตอน create (insert header) | ปฏิเสธด้วย `"PR reference number is required and must be unique"` รองรับโดย unique index `PR0_pr_no_u` บน `(pr_no, deleted_at)` |
| `PR_VAL_002` | `requestor_id` ต้องอ้างถึงผู้ใช้ที่ active; snapshot `requestor_name` ต้องถูก populate ไปด้วยกัน | ตอน create / ตอน submit | ปฏิเสธด้วย `"Requestor is required"` |
| `PR_VAL_003` | `department_id` ต้องถูก set (`purchase-request.validate.ts:26-33`, `PR_ERROR.DEPARTMENT_REQUIRED`) frontend ก็บังคับก่อน Save (`pr-form-schema.ts:129`) *การเช็ค membership ("requestor ต้องสังกัดแผนกนั้น") — ยังไม่ยืนยัน ไม่มี code path; delegation — ยังไม่ยืนยัน ดู `PR_AUTH_006`* | ตอน submit (server) / ตอน save (client) | ปฏิเสธด้วย `"Department is required"` |
| `PR_VAL_004` | `workflow_id` ต้องมี (`validate.ts:10-17`, `PR_ERROR.WORKFLOW_REQUIRED`); client เสนอเฉพาะ workflow ที่ผู้ใช้สร้างภายใต้ได้ (`pr-form-actions.tsx` "noCreatableWorkflow") *การเช็คฝั่ง server ว่าแถว active และ scope เป็น `purchase_request` — ยังไม่ยืนยัน* | ตอน submit | ปฏิเสธด้วย `"Workflow is required before submitting PR"` `workflow_name` ที่เลือกถูก snapshot ลงบน header |
| `PR_VAL_005` | `pr_date` ต้องมี (`validate.ts:34-41`, `PR_ERROR.PR_DATE_REQUIRED`; create ก็ throw `'PR date is required'`, `service.ts:885`) *"ไม่อยู่หลังวันนี้" — ยังไม่ยืนยัน ไม่มี code path* | ตอน create / ตอน submit | ปฏิเสธด้วย `"PR date is required"` |
| `PR_VAL_006` | ต้องมีแถว `tb_purchase_request_detail` ที่ไม่ถูกลบอย่างน้อยหนึ่งแถวแนบอยู่ | ตอน submit | ปฏิเสธด้วย `"A PR must contain at least one line item"` |
| `PR_VAL_007` | ทุกบรรทัด detail ต้องอ้างถึง `product_id` ที่ไม่ null และ resolve เป็นแถวที่ active ใน `tb_product` บรรทัด service / free-text ก็ยังต้องเลือก placeholder ของสินค้า | ตอน save บรรทัด / ตอน submit | ปฏิเสธด้วย `"Product is required on every line"` DB บังคับ NOT NULL บน `product_id` ด้วย |
| `PR_VAL_008` | **เฉพาะตอน submit (2026-09)** draft บันทึกได้ด้วย `requested_qty = 0` (schema ฝั่ง client `pr-form-schema.ts:51-56` เป็น `min(0)`; commit `a848865f` "ปุ่ม Save ของเอกสารร่างไม่บังคับกรอกครบแล้ว") ตอน submit ทุกบรรทัดต้องซื้อ (`requested_qty > 0`) หรือรับของฟรี (`foc_qty > 0`); บรรทัดที่ทั้งสองค่าเป็นศูนย์ไม่ผ่าน `PR_ERROR.LINE_ORDERS_NOTHING`, `requested_qty` ติดลบไม่ผ่าน `REQUESTED_QTY_INVALID`, `requested_unit_id` บังคับเมื่อซื้อ และ `foc_unit_id` เมื่อ `foc_qty > 0` (`validate.ts:105-149`) client เช็คกฎเดียวกันล่วงหน้า (`findRowsMissingQty`, toast "incompleteItems") ก่อนเปิด dialog submit `POST …/verify` ด้วย `verify_state = submit` เช็คเพิ่มว่าแต่ละ requested unit เป็น **order unit** ของสินค้า (`PR_ERROR` `001013`) | ตอน submit | `"Detail line N: needs a requested_qty or a foc_qty"` / `"requested_qty must be positive"` / `"requested_unit_id is required"` |
| `PR_VAL_009` | `delivery_date` **บังคับ** บนทุกบรรทัดโดย schema ฝั่ง client (`pr-form-schema.ts:83`); บรรทัดที่เติมจาก template หรือ duplicate default เป็นพรุ่งนี้ (`freshItem`) *"เท่ากับหรือหลัง `pr_date`" — ยังไม่ยืนยัน ไม่มี code path ทั้งสองฝั่ง* | ตอน save (client) | Client: `"required"` บนช่อง delivery-date |
| `PR_VAL_010` | `location_id` บนบรรทัดต้องอ้างถึง `tb_location` ที่ active ที่เป็นประเภทที่ขอ stock ได้ ตาม unique index `PR1_purchase_request_product_location_dimension_u` คู่ `(purchase_request_id, product_id, location_id, dimension)` ต้องไม่ซ้ำภายใน PR | ตอน save บรรทัด | ปฏิเสธ duplicate ด้วย `"Same product cannot be requested twice for the same location and dimension"` |
| `PR_VAL_011` | `currency_id` บังคับบนทุกบรรทัดโดย schema ฝั่ง client (`pr-form-schema.ts:73`) และที่ stage `purchase` โดยการเช็ค approve ฝั่ง server ร่วมกับ `vendor_id`, `pricelist_price > 0` และ `tax_profile_id` (`pr-form-schema.ts` `superRefine`, `verify-approve.ts` สาขา purchase-role) `exchange_rate` default `1` *`exchange_rate > 0` และ `exchange_rate_date ≤ pr_date` — ยังไม่ยืนยัน ไม่มี code path* | ตอน save (client) / ตอน approve ที่ stage purchase | Client: `"required"` บน currency; server: รายงาน verify list การอ้างอิงที่ขาดแต่ละรายการ |
| `PR_VAL_012` | **เพดานต่อบรรทัด (2026-09-17)** `discount_amount` ของบรรทัดต้องไม่เกิน sub-total และ `tax_amount` ต้องไม่เกิน net amount (`PR_ERROR.DISCOUNT_EXCEEDS_LINE_AMOUNT` / `TAX_EXCEEDS_LINE_AMOUNT`, `common/verify/amount.check.ts` ใช้โดย `findAmountIssues` ในสาขา verify ของ purchase-role) Manual override ทำให้ `is_tax_adjustment` / `is_discount_adjustment` กลายเป็น `true` *การเช็คช่วง `0–100` เปอร์เซ็นต์ — ยังไม่ยืนยัน ไม่มี code path* **ข้อควรระวังเรื่องการบังคับใช้:** เพดานถูกประเมินโดย `POST …/verify`; endpoint `approve` เองไม่เรียก `findPurchaseRequestApproveIssues` (`purchase-request.logic.ts:420` เป็นผู้เรียกเดียว) ดังนั้น client ที่ข้าม verify ยัง post บรรทัดเกินเพดานได้ | ตอน `verify` (`verify_state = approve`, `stage_role = purchase`) | รายงาน verify: `error_code` ต่อบรรทัดที่ผิด |
| `PR_VAL_013` | `approved_qty` เป็น `0` ได้ (schema ฝั่ง client เป็น `min(0)`, `pr-form-schema.ts:67`) แต่**ต้องไม่ติดลบ** และหน่วยที่อนุมัติต้องเป็น order unit ของสินค้า (`verify-approve.ts:172-181`, `PR_APPROVED_UNIT_CHECK`) *"≤ `requested_qty`" — ยังไม่ยืนยัน ไม่มี code path ทั้งสองฝั่ง* ข้อควรระวังเรื่องการบังคับใช้เดียวกับ `PR_VAL_012`: เช็คโดย `verify` ไม่ใช่โดย `approve` เอง | ตอน `verify` (`verify_state = approve`, `stage_role = approve`) | `"Detail line N: approved_qty cannot be negative"` |
| `PR_VAL_014` | ผู้ใช้ที่ submit PR ต้องมีสิทธิ์ลงมือกับ stage `create` แรกของ workflow (`enum_stage_role = create`) | ตอน submit | ปฏิเสธด้วย `"You are not authorised to submit purchase requests"` |
| `PR_VAL_015` | **ยังไม่ยืนยัน — ไม่มี code path** การเช็คความพร้อมของ budget ตอน submit เคยระบุในเอกสารรุ่นก่อน `grep -ri budget` ในโมดูล PR ฝั่ง backend, controller ของ gateway, โมดูล my-pending และ route PR ฝั่ง frontend พบเพียง `budget_code?: string` แบบ optional บน `purchase-request.interface.ts` และข้อความ reject ตัวอย่าง `"Budget exceeded for this period"` | — | — |
| `PR_VAL_016` | Optimistic concurrency: `doc_version` บนแถวที่กำลังอัปเดตต้องเท่ากับค่าที่ client อ่านมา | ตอน update ใด ๆ | ปฏิเสธด้วย `"Document was modified by another user; reload and retry"` และ bump `doc_version` ขึ้น 1 เมื่อ write สำเร็จ |
| `PR_VAL_017` | **Pre-flight verification (2026-08-19)** `POST /:bu_code/purchase-requests/verify` ด้วย `{ verify_state: 'create' \| 'submit' \| 'approve', id?, body? }` ประเมินทุกกฎของ action นั้นโดยไม่เขียนอะไร: `create` resolve ทุก id ใน payload สร้าง; `submit` รัน `findPurchaseRequestSubmitIssues` บวกการเช็ค order-unit บน PR ที่เก็บไว้; `approve` ด้วย `stage_role = purchase` เช็คการอ้างอิง, flag การปรับ และคำนวณทุกยอดใหม่จาก input ส่วน `stage_role = approve` เช็ค `approved_qty` / หน่วยที่อนุมัติ ปัญหาทั้งหมดถูกคืนพร้อมกัน (`{ id, verify_state, is_valid, errors: [{ error_code, message, field, detail }] }`); PR ที่ไม่ผ่านยังตอบ **200** พร้อม `is_valid: false` และ 404 เฉพาะ id ที่ไม่รู้จัก หมายเหตุ endpoint `submit` จริงหยุดที่ปัญหา**แรก** (`purchase-request.logic.ts:982`) | ตามต้องการ | `PurchaseRequestVerifySwaggerDto`; Bruno `POST-verify-procurement-purchase-request.bru` |
| `PR_VAL_018` | **กฎการลบ (2026-07-29)** การลบเดี่ยวและ batch ต้องมี `pr_status = draft` และความเป็นเจ้าของเอกสาร (`created_by_id` หรือ `requestor_id` เท่ากับผู้เรียก) เว้นแต่ผู้เรียกเป็น platform super-admin Batch delete validate ทุก id ก่อนแล้วคืน `{ deleted[], blocked: [{ id, reason: 'not_found' \| 'not_draft' \| 'not_owner' }] }` (`purchase-request.service.ts:1728-1850`) การลบเป็น **soft delete** (`deleted_at`) ไม่ใช่การเปลี่ยนสถานะ | ตอน `DELETE …/:id`, `DELETE …/batch` | `"Only draft purchase requests can be deleted"`, `ERROR_CATALOG.PR_DELETE_FORBIDDEN` |

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

Stage จริงตั้งค่าได้ต่อองค์กรใน `tb_workflow`; chain ที่ PR ใบหนึ่งใช้ตัดสินโดยแถวที่อ้างผ่าน `tb_purchase_request.workflow_id` สี่แถวด้านบนเป็นค่าเริ่มต้นจาก concept doc **ไม่ใช่** role ที่ code รู้จัก: คำศัพท์ stage เดียวที่มีคือ `enum_stage_role` และไม่มี stage ใดพก logic เฉพาะ budget หรือ finance (ดู `PR_VAL_015`)

- **`PR_AUTH_001`** — เฉพาะ requestor (`requestor_id == auth.user.id`) เท่านั้นที่แก้ไข PR ได้ขณะ `pr_status = draft` ผู้ใช้อื่นมีสิทธิ์อ่านเท่านั้น *(เอกสารรุ่นก่อนหน้าให้สิทธิ์แก้ไขแก่ "ผู้ที่ requestor delegated ให้" ด้วย — ยังไม่ยืนยัน ดู `PR_AUTH_006`)*
- **`PR_AUTH_002`** — ในแต่ละ stage เฉพาะผู้ใช้ที่อยู่ใน `tb_purchase_request.user_action.execute[]` เท่านั้นที่ลงมือทำได้ list จะถูกคำนวณใหม่ทุกการ transition stage จากกฎ role / department / amount-threshold ของ stage
- **`PR_AUTH_003`** — ผู้อนุมัติทุกคนมี bulk action **Approve**, **Reject**, **Send for Review** (send-back, `last_action = reviewed`, stage เป้าหมายเลือกจาก `GET …/:pr_id/previous-stages`) และ **Split** (`POST …/:id/split` ย้ายบรรทัดที่เลือกเข้า PR ใหม่); บรรทัดเดี่ยวก็ reject ได้เพื่อให้คงอยู่บนเอกสารด้วย `current_stage_status = rejected` และไม่มีวันไปถึงการแปลงเป็น PO
- **`PR_AUTH_004`** — **Reject** ระดับ header ยุติ chain ทันทีและย้าย `pr_status` เป็น `voided` (`purchase-request.service.ts:2201` — การเขียนค่านั้นเพียงจุดเดียว) *(การปล่อย soft-commitment ของ budget — ยังไม่ยืนยัน ดู `PR_VAL_015`)*
- **`PR_AUTH_005`** — **ยืนยันแล้ว** Amount threshold ขับว่า stage ใดทำงาน Workflow ที่ผูกกับ PR (`tb_workflow.data.routing_rules`) สามารถมีกฎ routing ต่อ stage ที่เทียบ condition field (`total_amount` — ผลรวม `total_price` ของบรรทัด PR; หรือ `department` หรือ `category`) กับค่าที่ตั้งไว้ด้วย operator (`eq`, `gt`, `lt`, `gte`, `lte`, `between`) แล้วเมื่อตรงเงื่อนไข จะข้ามหรือกระโดดไป stage เป้าหมายที่ระบุ — ประเมินโดย workflow engine ทั้งตอน submit และทุกครั้งที่ approve ดังนั้นถ้าการแก้ `approved_qty` กลาง review ทำให้ข้าม threshold routing ของ stage *ถัดไป* จะเปลี่ยนก่อนถึง stage นั้น ตั้งค่าได้จาก panel **Routing** ของ workflow ใน `/system-admin/workflow` (แบบ generic — ใช้ร่วมกันระหว่าง workflow ของ PR, PO, และ SR ไม่ใช่หน้าจอเฉพาะ PR) Threshold และ stage เป้าหมายเฉพาะตั้งค่าได้ต่อองค์กร/workflow เอกสารต้นทางไม่ได้กำหนดตัวเลขเฉพาะ **ข้อสังเกตที่ยืนยันในรอบนี้:** กฎ routing ที่อิง `category` จะไม่ match เลยอย่างเงียบ ๆ — ไม่มี mapper ของ PR/PO/SR ตัวใดส่ง field `category` ระดับเอกสารเข้าไปใน `navigation_request_data` และ `evaluateCondition` ใน `workflows.navagation.service.ts` คืนค่า `false` (ไม่ error) เมื่อ field หายไป engine ยังรองรับ operator `in`/`not_eq` เพิ่มเติมนอกเหนือจากชุด `eq`/`gt`/`lt`/`gte`/`lte`/`between` ที่ UI (`wf-routing-constants.ts`) รองรับ ดังนั้น rule ที่สร้างผ่าน direct API call (ไม่ผ่าน panel Routing) อาจใช้ operator เหล่านี้ได้แม้ UI จะตั้งค่าไม่ได้ แหล่งที่มา: `workflows.navagation.service.ts` ~บรรทัด 455-456 (comment เรื่อง field หาย) และ ~บรรทัด 498-500 (case `in`/`not_eq`)
- **`PR_AUTH_006`** — **(ยังไม่ยืนยัน — ไม่พบโค้ด delegation)** กฎนี้เคยระบุว่าผู้อนุมัติสามารถ delegate stage ของตนให้ผู้ใช้คนอื่นชั่วคราวผ่าน workflow engine โดย delegate สืบทอดสิทธิ์ approve / reject / send-back เฉพาะช่วง delegation window, `last_action_by_id` สะท้อน delegate, และ audit comment จับแหล่งที่มาของ delegation การค้นหาทั่ว repo ทั้งฝั่ง frontend (รวมถึง panel **Routing** ของ workflow ที่ยืนยัน `PR_AUTH_005` ตัวเดียวกัน) และฝั่ง backend workflow orchestrator ไม่พบกลไก delegation, reassignment, proxy, หรือ substitute-approver เลย ทั้ง generic และเฉพาะ PR — `routing_rules` ทำหน้าที่ route ตัว *เอกสาร* ระหว่าง stage ตาม amount/department/category เท่านั้น ไม่ได้ส่งต่อ stage ให้ *ผู้ใช้* คนอื่น ถือว่า delegation เป็น design intent ที่ยังไม่ยืนยัน ไม่ใช่ live behavior ที่ verified
- **`PR_AUTH_007`** — **(ยังไม่ยืนยัน — ไม่มี endpoint void)** เอกสารรุ่นก่อนระบุว่า Finance / system-admin **Void** ได้ทุก stage หลัง submit `purchase-requests.controller.ts` ไม่ expose route void, `enum_purchase_request_doc_status.voided` ถูกเขียนโดย `reject` เท่านั้น และฟอร์ม PR ฝั่ง frontend มีแค่ Edit / Save / Delete / Submit / Approve / Reject / Send Back (`pr-form-actions.tsx`, `workflow/pr-footer-action.tsx`) `draft` ถูกเอาออกด้วย **Delete** (soft delete โดยเจ้าของหรือ super-admin — `PR_VAL_018`); PR ที่ submit แล้วยุติได้เฉพาะโดย Reject ของผู้อนุมัติ
- **`PR_AUTH_008`** — การแปลงเป็น PO *ตั้งใจ*ให้เป็นของ role `purchase` แต่ไม่มีการบังคับ permission บน `group-pr` / `confirm-pr` หรือ dialog Convert-to-PO (ดู [03-user-flow-purchaser](./03-user-flow-purchaser.md)) PR ที่ approved ค้างที่ `approved` จนกว่าผู้ใช้จะสร้าง PO ผ่าน bridge `tb_purchase_order_detail_tb_purchase_request_detail` **การมองเห็น list** คือสิ่งที่แคตตาล็อก permission gate จริง: `procurement.purchase_request.view` / `view_department` / `view_all` (`constant/permissions.ts:61-65`; backend `@Permission({ 'procurement.purchase_request': ['view'] })` บน endpoint แบบ list)

> ⚠️ **ความต่าง — bulk-toolbar กับ action ระดับแถว (BRD FR-PR-005A):** BRD ระบุปุ่ม **Approve / Reject / Send for Review** แบบ standalone ต่อแถวบน list / header ของ PR detail UI ปัจจุบันที่ live เปิด action เหล่านี้เป็น **bulk toolbar action** ใน Edit Mode เท่านั้น (ผ่าน dropdown Select All → bulk action toolbar) Bulk action ที่ยืนยันแล้ว: Approve, Reject, Send for Review (BRD "Return Selected"), Split ปุ่มระดับแถวแบบ standalone ยังไม่มี ที่มา: `Test_case/Purchase_Request/Approver/INDEX.md` (วันที่จับภาพ 2026-04-19) สถานะการตรวจสอบ: ยืนยันแล้วสำหรับ HOD; assumed สำหรับ FC / GM / Owner

> ⚠️ **ความต่าง — tooltip ของปุ่ม Send-back ที่ disabled:** ปุ่ม Submit / Send-back ถูก disable เมื่อ pre-condition ไม่ผ่าน (`PR_VAL_004`–`PR_VAL_006`) แต่ live UI ไม่มี tooltip อธิบายเหตุผลที่ disable ช่องว่างด้าน usability ที่จับไว้ใน `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § 6.4

## 5. กฎการ Posting

การ transition สถานะถูกบันทึกบน `tb_purchase_request.pr_status` (`enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed }`) ทุกการ transition เขียนทั้งแถว header ใน `workflow_history` (timeline JSON) และแถว `tb_purchase_request_comment` ด้วย `type = system` สำหรับ audit trail

- **`PR_POST_001` — Create.** PR ใหม่ถูก insert ด้วย `pr_status = draft`, `last_action = submitted` ยัง **ไม่** ถูก set, `workflow_current_stage` เป็น entry stage ของ workflow และยอด `base_*_amount` เป็นศูนย์จนกว่าจะเพิ่มบรรทัด
- **`PR_POST_002` — Submit.** Transition `draft → in_progress` ระบบ: (a) ตั้ง `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_*` เป็น requestor; (b) snapshot `workflow_name` จาก `tb_workflow` ที่เลือก; (c) initialise `stages_status` ตาม stage; (d) *soft-commitment ของ budget — ยังไม่ยืนยัน ไม่มี code path (`PR_VAL_015`)*; (e) insert `tb_purchase_request_comment` ด้วย `type = system` และข้อความ submit; (f) แจ้งผู้ใช้ใน `user_action.execute[]` ของ stage อนุมัติแรก BRD `FR-PR-005` ตั้ง SLA การแจ้งผู้อนุมัติคนแรกที่ **5 นาที** จากตอน submit; SLA ยังไม่ได้ตรวจสอบกับ notification service จริง

> ⚠️ **ความต่าง — SLA การแจ้งยังไม่ได้ตรวจสอบ:** BRD `FR-PR-005` ระบุ SLA อีเมล 5 นาทีสำหรับผู้อนุมัติคนแรกตอน submit ยังไม่ได้ตรวจสอบใน test environment เพราะการส่งขึ้นกับ availability ของ notification service ที่มา: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-06

> ⚠️ **ความต่าง — budget check `warn` vs `block`:** BRD `FR-PR-004` ทำให้ budget check ตั้งค่าได้ตามนโยบายขององค์กร — *warn* (อนุญาตให้ submit พร้อม warning) หรือ *block* (กัน submit เมื่อเกิน budget) บัญชี test ปัจจุบันมีราคาต่อหน่วยเป็นศูนย์บนสินค้า (commitment = `฿0.00`) ทำให้พฤติกรรม live สำหรับการ submit ที่เกิน budget ยังสังเกตไม่ได้ ที่มา: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-09
- **`PR_POST_003` — Send-back.** Transition `in_progress → in_progress` โดย `workflow_current_stage` ย้ายกลับไป stage เป้าหมายที่เลือกและ `last_action = reviewed` (`purchase-request.service.ts:2032-2060` เขียน `pr_status = in_progress` โดยไม่มีเงื่อนไข — แม้เป้าหมายเป็น stage `create` ของ requestor PR ก็**ไม่**กลับไป `draft`; requestor แก้ไขมันในฐานะเอกสาร `in_progress` ที่ stage นั้น) แจ้งผู้ใช้ที่ stage ใหม่
- **`PR_POST_004` — Approve (intermediate stage).** อัปเดต `workflow_previous_stage`, `workflow_current_stage`, `workflow_next_stage`, `last_action = approved`, `stages_status` สำหรับ stage ที่เพิ่งเสร็จ; append `workflow_history`; คำนวณ `user_action.execute[]` ใหม่สำหรับ stage ถัดไป `pr_status` ยังคง `in_progress`
- **`PR_POST_005` — Final approve.** เมื่อ stage สุดท้ายผ่าน `pr_status` พลิกจาก `in_progress` เป็น `approved` (`purchase-request.service.ts:1913`) PR พร้อมแปลงเป็น PO แล้ว (ดู [purchase-order](/th/inventory/purchase-order)) *(การแปลง soft เป็น hard commitment ของ budget — ยังไม่ยืนยัน `PR_VAL_015`)*
- **`PR_POST_006` — Reject.** `reject` ระดับ header จากผู้อนุมัติคนใดย้าย `pr_status` เป็น `voided`, append `workflow_history`, อัปเดต `stages_status` / `history` / `current_stage_status` ของแต่ละบรรทัด และ insert comment `type = system` พร้อมเหตุผล (`purchase-request.service.ts:2138-2210`) reject ระดับบรรทัด (split) ตั้ง `current_stage_status = rejected` ต่อบรรทัดแต่ไม่เปลี่ยน `pr_status` *void โดยผู้ดูแลระบบและ "cancel เป็น `voided`" โดย requestor — ยังไม่ยืนยัน; draft ถูก soft-delete (`PR_POST_009`) และ `voided` ไม่มีผู้เขียนอื่น*
- **`PR_POST_007` — Convert to PO.** เมื่อผู้ใช้ procurement สร้าง PO จาก PR ที่ approved หนึ่งใบหรือมากกว่า แถว `tb_purchase_request_detail` แต่ละแถวที่ได้รับผลกระทบจะได้แถวใน bridge `tb_purchase_order_detail_tb_purchase_request_detail` ที่ link ไปยังบรรทัด PO ใหม่ เมื่อ **ทุก** บรรทัดของ PR ถูกแปลงเต็ม (ผลรวมของจำนวน PO ที่ link ผ่าน bridge เท่ากับ `approved_base_qty`) หรือถูกยกเลิกชัดเจน ระบบพลิก `pr_status` จาก `approved` เป็น `completed` การแปลงบางส่วนทำให้ PR คงอยู่ที่ `approved` พร้อมจำนวนที่เหลือเปิดไว้จนกว่า PO ถัดไปจะมารับ
- **`PR_POST_009` — Delete (เฉพาะ draft).** `DELETE …/:id` และ `DELETE …/batch` ประทับ `deleted_at` บน header และทุก detail row และตั้งยอดรวมของ header เป็นศูนย์ตอน batch delete (`purchase-request.service.ts:1791`); `pr_status` ไม่ถูกแตะ และ row หายจากทุก list และจาก `sys_v_my_pending` ดู `PR_VAL_018` ว่าใครลบได้
- **`PR_POST_008` — Audit comment เป็น immutable.** แถว `tb_purchase_request_comment` ที่ `type = system` ไม่สามารถแก้ไขได้หลัง insert User comment (`type = user`) สามารถ soft-delete (`deleted_at`) โดยผู้เขียนได้แต่ไม่มีการ hard-delete; การ soft-delete เองถูกจับโดย audit

ไม่มี posting ระดับ stock จาก PR: โมดูล PR เป็นเอกสารแสดงเจตนา procurement และไม่กระทบยอด inventory การเคลื่อนไหวของ stock เกิดปลายน้ำใน [purchase-order](/th/inventory/purchase-order) และ Good Receive Note ([good-receive-note](/th/inventory/good-receive-note))

## 6. กฎข้ามโมดูล

- **Budget** — **ยังไม่ยืนยัน — ไม่มี code path** `BudgetData.softCommitmentPR`, `availableBudget` และ symbol เรื่องงบประมาณอื่นทุกตัวที่ระบุในเอกสารรุ่นก่อนมาจาก `../carmen/docs/` เท่านั้น; ไม่มีอะไรใน `carmen-turborepo-backend-v2`, `carmen-inventory-frontend-react` หรือ Bruno collection ที่ implement โมดูล budget (`PR_VAL_015`)
- **Inventory** — UI ที่จับบรรทัดอ่านจาก [inventory](/th/inventory/inventory) เพื่อแสดงจำนวน on-hand และ on-order (`pr-inventory-row.tsx` fetch แบบ live ไม่ cache — commit `4077b4ea`) และข้อมูลการรับของล่าสุด (`pr-last-receiving-info.tsx`); ตั้งแต่ 2026-09-17 response ของ PR detail เองมี `last_price` ต่อบรรทัด (`purchase-request.serializer.ts:106`) และ response ของ price-compare มี `last_price` ของสินค้า ค่าเหล่านี้ไม่ persist บน `tb_purchase_request_detail` PR **ไม่** จองหรือย้าย inventory *(reorder level / average monthly usage ใน grid ของ PR — ยังไม่ยืนยัน)*
- **Vendor & vendor-pricelist** — แต่ละบรรทัด detail resolve preferred vendor (optional) ผ่าน endpoint price-compare ([vendor-pricelist](/th/inventory/vendor-pricelist)) ตาม product, หน่วยที่ขอ, currency, วันที่ และ — ตั้งแต่ 2026-09-16 — `qty` ที่ขอ ดังนั้น MOQ tier ที่ปริมาณไปถึงคือ tier ที่เสนอ แถวเรียงแบบ preferred ก่อน แล้วถูกที่สุด (`price-list.service.ts:715`); แถวที่ราคา `0` ถูกตัดออก `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price`, และ `pricelist_type` (`enum_pricelist_compare_type`) ที่เลือกถูก snapshot ลงบนบรรทัดเพื่อให้ข้อมูล PR ในอดีตคงที่แม้ pricelist จะเปลี่ยน ถ้า requestor เลือก vendor นอก pricelist ด้วยมือ `pricelist_type` จะถูกตั้งให้สอดคล้องและ `is_discount_adjustment` / `is_tax_adjustment` อาจถูก flag
- **Product** — `product_id` เป็น FK required ไปยัง [product](/th/inventory/product); master data สินค้า (code, name, local name, SKU, UoM ฐานของ inventory) ถูก snapshot ลงบนบรรทัดตอน write สินค้า inactive ไม่สามารถเพิ่มได้ (`PR_VAL_007`) พฤติกรรม service-line ทำได้โดยเลือก placeholder สินค้า "service"
- **Purchase-order** — PR เป็นเอกสารต้นน้ำสำหรับ [purchase-order](/th/inventory/purchase-order) link คือตาราง bridge `tb_purchase_order_detail_tb_purchase_request_detail` (many-to-many) รองรับทั้ง **consolidation** (หลายบรรทัด PR feed หนึ่งบรรทัด PO — มัก group ตาม vendor และ currency) และ **partial conversion** (หนึ่งบรรทัด PR แตกเป็นหลายบรรทัด PO ข้ามวันส่งของหรือ vendor) `pr_status` ของ PR ไม่พลิกเป็น `completed` จนกว่าทุกบรรทัดจะถูก bridge เต็มหรือยกเลิก (`PR_POST_007`)
- **Templates** — `tb_purchase_request_template` / `tb_purchase_request_template_detail` ใช้ seed เท่านั้น มันไม่เข้าสู่ workflow ของตัวเอง; **Create from Template** เป็นการเติมข้อมูลล่วงหน้าฝั่ง client (`/procurement/purchase-request/from-template` → ขั้นระบุปริมาณ → ฟอร์ม PR ใหม่ปกติโดยส่ง template ผ่าน router state) — ไม่มีอะไรถูกเขียนจนกว่าผู้ใช้จะ save และ PR ที่ได้ไม่เก็บ link ไปยัง template `workflow_id` ของ template ถูก copy เป็น workflow ของ PR ใหม่; ดู [templates/purchase-request](/th/inventory/templates/purchase-request)

## 7. แหล่งอ้างอิง

- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — แหล่ง business-analysis หลัก; rule ID `PR_CRT_*`, `PR_BDG_*`, `PR_WFL_*`, `PR_ITM_*`, บวก block การคำนวณ `PR_036`–`PR_055`
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md` — กฎเชิงเทคนิค, schema validation Zod (`PurchaseRequestSchema`, `PurchaseRequestItemSchema`), sequence diagram ของ approval flow, และการ routing workflow ตาม threshold
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — integration ข้ามโมดูล (budget, inventory, workflow, notification), permission ตาม role, และ state shape
- หน้าพี่น้อง: [01-data-model](/th/inventory/purchase-request/01-data-model) — entity Prisma ตามมาตรฐาน, enum และความแม่นยำในการ round (`Decimal(15, 5)` / `Decimal(20, 5)`)
- การ implement กฎฝั่ง backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request/` — `logic/purchase-request.validate.ts` (กฎตอน submit), `logic/verify/purchase-request.verify-create.ts` / `verify-approve.ts` (pre-flight), `logic/purchase-request.logic.ts` (`verify`, `submit`, `approve`, `reject`, `review`), `purchase-request.service.ts` (`delete`, `deleteBatch`, การเขียนสถานะ) — บวก `purchase-request-comment/`, `purchase-request-template/` และ API edge ใน `apps/backend-gateway/src/application/purchase-requests/` (`purchase-requests.controller.ts`, `swagger/request.ts` `PurchaseRequestVerifySwaggerDto`)
- การ implement กฎฝั่ง frontend: `../carmen-inventory-frontend-react/routes/procurement/purchase-request/pr-form-schema.ts` (Zod schema, `findRowsMissingQty`), `use-pr-form-actions.ts` (`handleSubmitPr`), `workflow/pr-footer-action.tsx`
