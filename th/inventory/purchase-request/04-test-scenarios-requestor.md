---
title: ใบขอซื้อ (Purchase Request) — Test Scenarios — Requestor
description: Test case ของ Requestor (happy path, permission, validation, edge case) สำหรับโมดูล purchase-request
published: true
date: 2026-05-17T12:00:00.000Z
tags: purchase-request, test-scenarios, requestor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Test Scenarios — Requestor

> **At a Glance**
> **Persona:** Requestor &nbsp;·&nbsp; **โมดูล:** [[purchase-request]] &nbsp;·&nbsp; **Scenario:** ~36
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** map ไปยัง `tests/302-pr-creator-journey.spec.ts`, `tests/311-pr-returned-flow.spec.ts` และ `tests/301-pr.spec.ts` (fixture requestorTest / noAuthTest) ใน `../carmen-inventory-frontend-e2e/`

หน้านี้จับ test scenario ที่ persona Requestor ขับโดยตรงในโมดูล `purchase-request` ครอบคลุม happy path ที่อธิบายใน [03-user-flow-requestor.md](./03-user-flow-requestor.md) Section 2, ขอบเขต RBAC ที่ implied โดย `PR_AUTH_001` และกฎ draft-only edit ใน [02-business-rules.md](./02-business-rules.md), กฎ validation ตอน submit `PR_VAL_001`..`PR_VAL_012` ที่ Requestor สามารถ trigger ได้โดยตรง และชุดเล็กของ case boundary / concurrency ที่ตกจากความแม่นยำ `Decimal(15, 5)` / `Decimal(20, 5)` และ loop send-back Handoff ข้าม persona (`X-PR-02`, `X-PR-10`) ที่เริ่มที่ Requestor และ bounce off Approver อยู่ในภาพรวมหลัก ไม่ใช่ที่นี่

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| REQ-HP-01 | สร้างและ submit PR ขั้นต่ำ (บรรทัดเดียว สกุลเงินฐาน) | Requestor `requestor@blueledgers.com` ล็อกอินอยู่; `tb_workflow` active สำหรับ scope `purchase-request`; มี `tb_product` active อย่างน้อยหนึ่งใน catalog; สกุลเงินฐาน THB | 1. จาก PR list view คลิก **Create New PR** 2. กรอก header: เลือก `department_id`, ตั้ง `delivery_date` ≥ `pr_date`, ทิ้ง `currency_id` เป็น default ฐาน, เลือก `workflow_id`, ใส่ description 3. เพิ่ม 1 บรรทัดด้วย `requested_qty > 0`, `requested_unit_id` valid, `pricelist_price` และ `delivery_date` ในอนาคต 4. Save header (auto-save ก็ทำงานเมื่อขาดการเชื่อมต่อ) 5. เปิดแท็บ **Review** ยืนยัน subtotal / discount / tax / grand total 6. คลิก **Submit** | แถวใหม่ใน `tb_purchase_request` ด้วย `pr_status = draft → in_progress`; `pr_no` สร้างอัตโนมัติและไม่ซ้ำ; `last_action = submitted`; `workflow_current_stage` = stage อนุมัติแรก; soft budget commitment ลงทะเบียน; ผู้อนุมัติ stage แรกได้รับแจ้ง; Requestor เห็น PR บน dashboard **My PRs** |
| REQ-HP-02 | สร้างและ submit PR หลายบรรทัดพร้อม attachment | เหมือน REQ-HP-01; ใบเสนอราคา vendor PDF พร้อมอัปโหลด; สินค้า active สองตัวใน catalog | 1. **Create New PR**, กรอก header 2. เพิ่มบรรทัด 1 (Product A, qty, UoM, ส่วนลดบรรทัด 5 %, ภาษี 7 %) 3. เพิ่มบรรทัด 2 (Product B, store location ต่างกัน, FOC qty > 0, ส่วนลด 0) 4. เปิดแท็บ **Attachments** → อัปโหลด PDF ใบเสนอราคา, ตั้ง description และ visibility 5. Review ยอด header (`PR_CALC_007` roll-up) 6. Submit | สองแถวที่ไม่ลบใน `tb_purchase_request_detail` (`PR_VAL_006` ผ่าน); แถว attachment persist พร้อม description / visibility; header `base_net_amount` / `base_total_amount` เท่ากับ roll-up บรรทัดที่ 5 dp; PR transition ไป `in_progress` และผู้อนุมัติคนแรกรับ notification |
| REQ-HP-03 | Save draft วันนี้, กลับมาแก้วันถัดไป, แล้ว submit | Requestor ล็อกอินอยู่; ยังไม่ submit | 1. **Create New PR**, กรอก header, เพิ่ม 1 บรรทัด 2. คลิก **Save** (ไม่ submit) → PR persist ด้วย `pr_status = draft` 3. Logout / ปิด tab 4. วันถัดไป login ใหม่, เปิด PR จาก **My PRs** 5. แก้ description และ qty บนบรรทัด 1 (`PR_AUTH_001` อนุญาตเพราะยัง `draft` และ Requestor เป็นเจ้าของ) 6. Submit | Draft เห็นได้ตอน login ครั้งถัดไปด้วยสถานะที่ save ล่าสุด; edit อนุญาตเพราะ `pr_status = draft` และ `requestor_id == auth.user.id`; ตอน submit `doc_version` increment ตาม `PR_VAL_016`; สถานะ transition `draft → in_progress` |
| REQ-HP-04 | ตอบสนอง send-back และ resubmit | PR ถูก submit โดย Requestor นี้และผู้อนุมัติ stage แรกคลิก **Send Back** พร้อมเหตุผล; PR กลับเป็น `pr_status = in_progress` ด้วย `workflow_current_stage` ที่ stage `create` ก่อนหน้าและ edit unlock สำหรับ Requestor | 1. เปิด PR จาก dashboard หรือ in-app notification 2. อ่าน comment ของผู้อนุมัติใน workflow history 3. แก้ฟิลด์ที่มีปัญหา (เช่นอัปเดต `requested_qty` หรือแก้ description) 4. คลิก **Submit** อีกครั้ง | Edit สำเร็จเพราะ Requestor กลับมาอยู่ใน role stage `create` สำหรับ PR นี้; `last_action = submitted` ประทับใหม่, `workflow_current_stage` เลื่อนไป stage อนุมัติแรกอีกครั้ง; soft budget commitment ถูก re-evaluate; ประวัติการแก้ไขเก็บ submit + send-back comment ก่อนหน้า (`PR_POST_008` ทำให้ system comment immutable) |
| REQ-HP-05 | ยกเลิก draft ของตัวเองจากหน้า detail | PR มีอยู่ใน `pr_status = draft`; Requestor เป็นเจ้าของ; ไม่เคย submit | 1. เปิดหน้า PR detail 2. คลิก **Delete** / **Cancel** 3. ยืนยันใน modal | `pr_status` พลิกเป็น `cancelled`; ไม่มี stage workflow ที่ถูกเลื่อน; ไม่มี soft budget commitment ที่เคยสร้าง (เพราะไม่เคยถึง submit); audit log จับ cancel event; PR ไม่ปรากฏใน list active และปุ่ม edit ถูกถอด |
| REQ-HP-06 | สร้าง PR จาก template, แก้ไข, submit | มี `tb_purchase_request_template` active อย่างน้อยหนึ่งที่มีแถว detail ที่ Requestor เห็น; template มี `workflow_id` สำหรับ scope `purchase-request` | 1. **Create from Template**, เลือก template แรกใน picker 2. PR ใหม่ pre-fill header (currency, workflow) และ clone แถว detail ของ template เข้า `tb_purchase_request_detail` 3. ปรับ `requested_qty` และ `delivery_date` บนบรรทัดหนึ่ง 4. Submit | PR ใหม่อิสระจาก template; แถว `tb_purchase_request_template_detail` ไม่ถูก mutate; PR transition `draft → in_progress`; workflow ตาม `workflow_id` ของ template |
| REQ-HP-07 | Submit PR ด้วยการปรับส่วนลดและภาษีระดับบรรทัด | เหมือน REQ-HP-01; tax profile และ input discount เปิด | 1. เพิ่มบรรทัดด้วย `pricelist_price = 185.00000`, `discount_rate = 5`, `tax_rate = 7`, `is_discount_adjustment = false`, `is_tax_adjustment = false` 2. Verify preview live แสดง `sub_total_price = 2,220.00000`, `discount_amount = 111.00000`, `net_amount = 2,109.00000`, `tax_amount = 147.63000`, `total_price = 2,256.63000` สำหรับ `requested_qty = 12` 3. Submit | บรรทัด persist ด้วยค่าจาก rule engine จาก `PR_CALC_001`..`PR_CALC_005`; header roll-up `base_total_amount` = 2,256.63000 ฿ (THB ฐาน, exchange_rate = 1.00000); display layer อาจตัดเป็น 2 dp แต่ค่า persist เก็บ 5 dp |
| REQ-HP-08 | Submit PR สกุลต่างประเทศ (บรรทัด USD, ฐาน = THB) | เหมือน REQ-HP-01; `tb_currency` สำหรับ USD active; `exchange_rate` ที่มีผลพร้อมในหรือก่อน `pr_date` | 1. เพิ่มบรรทัด USD ด้วย `pricelist_price = 5.20000`, `requested_qty = 12`, `discount_rate = 5`, `tax_rate = 7`, `exchange_rate = 35.50000` 2. Verify preview ฐาน ≈ `base_total_price = 2,251.74180 ฿` 3. Submit | `exchange_rate` ถูก snapshot บนบรรทัดตอน submit และ freeze ตลอดอายุของเอกสาร (re-approve ไม่ re-fetch); คอลัมน์ `base_*` คำนวณตาม `PR_CALC_006`; soft budget commitment ลงทะเบียนในสกุลฐาน |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| REQ-PERM-01 | Requestor เปิด PR ที่ตนเป็นเจ้าของ (`requestor_id == auth.user.id`) ใน `pr_status = draft` | **Allow** read และ edit `PR_AUTH_001` ให้สิทธิ์ edit exclusive แก่เจ้าของขณะที่ PR เป็น `draft` |
| REQ-PERM-02 | Requestor เปิด PR ที่ผู้ใช้อื่นเป็นเจ้าของใน `pr_status = draft` | **Deny edit, read-only** (ไม่มี toolbar Edit / Delete / Submit) `PR_AUTH_001` สงวน edit ให้เจ้าของหรือ delegate ที่ระบุ Visibility list เองขึ้นกับ grant **All Documents** / department-wide; ถ้า PR นอกแผนกของ Requestor มันไม่ปรากฏใน list เลย |
| REQ-PERM-03 | Requestor edit draft ของตนเอง (description header และ qty บรรทัดหนึ่ง) | **Allow.** `PR_AUTH_001` ผ่าน; `doc_version` increment ตอน save ตาม `PR_VAL_016` |
| REQ-PERM-04 | Requestor พยายามแก้ PR ของตนเองหลัง submit (`pr_status = in_progress`) | **Deny.** Lock ของ state-machine — ปุ่ม edit เป็น read-only วิธีเดียวกลับไปแก้คือให้ผู้อนุมัติ **Send Back** PR เป็น `draft` |
| REQ-PERM-05 | Requestor cancel / delete PR ของตนเองที่ `draft` | **Allow.** Action เฉพาะเจ้าของบนเอกสารที่ยังไม่ submit; ไม่มี stage workflow ที่เลื่อน, ไม่มี soft commitment ที่ต้องปล่อย |
| REQ-PERM-06 | Requestor พยายาม cancel PR ของตนเองหลัง submit (`in_progress` หรือ `approved`) | **Deny.** PR ที่ submit แล้วกลับเข้า chain ผ่าน **Send Back** ของผู้อนุมัติเท่านั้น, ถูก reject โดยผู้อนุมัติ (`PR_AUTH_004` → `cancelled`) หรือ **void** โดย Finance / sys-admin (`PR_AUTH_007` → `voided`) Requestor ไม่เคยเห็น Cancel control สำหรับ PR ที่ submit แล้ว |
| REQ-PERM-07 | Requestor พยายาม approve PR ของตนเอง | **Deny.** Segregation of duties — role stage `create` และ role stage `approve` ปลายน้ำ disjoint ตามนิยาม workflow (ดู [02-business-rules.md](./02-business-rules.md) Section 4 chain default) แม้ Requestor ถูกตั้งชื่อบน approver stage โดย misconfig `user_action.execute[]` ถูกคำนวณใหม่ต่อ stage และเจ้าของ create-stage ถูก filter ออก |
| REQ-PERM-08 | Requestor ด้วย fixture `noAuth` / session หมดอายุเปิด URL PR ใด ๆ | **Deny — redirect ไป login.** นอก auth context ไม่มี `auth.user.id` ที่จะ match กับ `requestor_id`; `PR_AUTH_001` ใช้ไม่ได้ Covered โดย fixture `noAuthTest` ใน `301-pr.spec.ts` |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาด |
| - | -------- | ------- | -------------- |
| REQ-VAL-01 | Submit โดยไม่มี `pr_no` (หรือ `pr_no` duplicate) | Header insert race สอง client; หรือ seed test สร้างแถวด้วย `pr_no` ที่ชนกับแถวที่ไม่ลบ | `PR_VAL_001` — reject ด้วย `"PR reference number is required and must be unique"` Unique index `PR0_pr_no_u` บน `(pr_no, deleted_at)` บังคับ |
| REQ-VAL-02 | Submit โดยไม่มี snapshot `requestor_id` / `requestor_name` valid | บัญชี Requestor ถูก deactivate กลางการแก้ หรือ snapshot สูญหาย | `PR_VAL_002` — reject ด้วย `"Requestor is required"` |
| REQ-VAL-03 | Submit ด้วย `department_id` ว่างหรือชี้ไปแผนกที่ Requestor ไม่สังกัด | Header `department_id` ถูกล้าง หรือ set เป็นค่านอก `user.memberships` | `PR_VAL_003` — reject ด้วย `"Department is required and must match requestor membership"` |
| REQ-VAL-04 | Submit โดยไม่มี `workflow_id` (หรือชี้ไป workflow ที่ scope ≠ `purchase-request`) | Header `workflow_id` ถูกล้าง | `PR_VAL_004` — reject ด้วย `"A valid PR workflow must be selected"` |
| REQ-VAL-05 | Submit ด้วย `pr_date` ในอนาคต | ตั้ง `pr_date` เป็นพรุ่งนี้ | `PR_VAL_005` — reject ด้วย `"PR date cannot be in the future"` |
| REQ-VAL-06 | Submit PR ที่มีบรรทัดที่ไม่ลบเป็น 0 | Save header เท่านั้น, แล้วคลิก Submit | `PR_VAL_006` — reject ด้วย `"A PR must contain at least one line item"` ปุ่ม Submit ก็ถูก disable ใน UI ตาม `TC-PR-050604` |
| REQ-VAL-07 | Save บรรทัดโดยไม่มี `product_id` (หรือสินค้า inactive) | คำอธิบาย free-text เท่านั้น ไม่เลือกสินค้า; หรือสินค้าถูก soft-delete ใน catalog | `PR_VAL_007` — reject ด้วย `"Product is required on every line"` NOT NULL บังคับที่ DB layer ด้วย |
| REQ-VAL-08 | Save บรรทัดด้วย `requested_qty = 0` (หรือลบ หรือขาด `requested_unit_id`) | ใส่ `0` ใน input qty บนบรรทัดใหม่ | `PR_VAL_008` — reject ด้วย `"Requested quantity must be greater than zero and have a unit"` |
| REQ-VAL-09 | Save บรรทัดด้วย `delivery_date` ก่อน `pr_date` | ตั้ง `delivery_date` ของบรรทัดเป็นวันที่ในอดีตเทียบกับ `pr_date` (covered โดย `TC-PR-050211`) | `PR_VAL_009` — reject ด้วย `"Delivery date cannot be earlier than the PR date"` |
| REQ-VAL-10 | เพิ่มบรรทัดที่สองสำหรับ `(product_id, location_id, dimension)` เดียวกันที่อยู่บน PR แล้ว | บรรทัด duplicate ใน PR เดียวกัน | `PR_VAL_010` — reject ด้วย `"Same product cannot be requested twice for the same location and dimension"` Unique index `PR1_purchase_request_product_location_dimension_u` บังคับ |
| REQ-VAL-11 | Save บรรทัดด้วย `currency_id` ขาด หรือ `exchange_rate ≤ 0` หรือ `exchange_rate_date` หลัง `pr_date` | Force-clear `exchange_rate` เป็น `0` หรือ ตั้ง `exchange_rate_date` เป็นพรุ่งนี้ | `PR_VAL_011` — reject ด้วย `"Currency and exchange rate are required and must be effective on or before the PR date"` |
| REQ-VAL-12 | Save บรรทัดด้วย `tax_rate = 110` (หรือ `discount_rate = -5`) | พิมพ์อัตรานอกช่วงด้วยมือ | `PR_VAL_012` — reject ด้วย `"Tax and discount rates must be between 0 and 100"` |
| REQ-VAL-13 | สอง browser tab edit draft เดียวกันและ tab ที่สองพยายาม save | Tab A save description; Tab B (ยังถือ `doc_version` เก่ากว่า) คลิก Save | `PR_VAL_016` — reject ด้วย `"Document was modified by another user; reload and retry"` Save สำเร็จ bump `doc_version` ขึ้น 1 |

## 4. Edge Case

| # | Scenario | เงื่อนไข | คาดหวัง |
| - | -------- | --------- | -------- |
| REQ-EDGE-01 | Boundary จำนวนศูนย์ | Save บรรทัดด้วย `requested_qty = 0.00000` | Reject ตาม `PR_VAL_008` — กฎเข้มเป็น `> 0` ไม่ใช่ `≥ 0`; เดียวกันใช้กับค่าลบที่ input ควร reject ที่ form layer ด้วย |
| REQ-EDGE-02 | ความแม่นยำทศนิยมสูงสุด | บรรทัดใส่ด้วย `requested_qty = 1.99999`, `pricelist_price = 0.00001`, `discount_rate = 99.99999`, `tax_rate = 99.99999`, `exchange_rate = 35.12345` | Persist ตรงที่ 5 ทศนิยมบนคอลัมน์ `Decimal(15, 5)` / `Decimal(20, 5)`; ทศนิยมที่ 6 ถูก round half-up ก่อน step ถัดไปตามนโยบายการ round ใน [02-business-rules.md](./02-business-rules.md) Section 3 Display อาจตัดเป็น 2 dp แต่ค่า persist เก็บ 5 dp |
| REQ-EDGE-03 | `requested_date` ย้อนหลัง (บรรทัด `delivery_date` = `pr_date`) | `delivery_date == pr_date` (วันเดียวกัน) | ยอมรับ — `PR_VAL_009` เป็น "ในหรือหลัง `pr_date`" ดังนั้นเท่ากันถูกต้อง |
| REQ-EDGE-04 | `requested_date` ในอนาคตไกล | บรรทัด `delivery_date` = `2099-12-31` | ยอมรับโดย `PR_VAL_009`; stage ปลายน้ำ (Approver, Purchaser) อาจ flag ระหว่าง validation ของตนเองแต่ submit ของ Requestor ไม่บล็อก |
| REQ-EDGE-05 | สกุลเงินบรรทัดต่างจากสกุลเงิน default ของแผนก | Header `currency_id = USD` แต่ default แผนกของ Requestor คือ THB | อนุญาตที่ stage Requestor — การแปลงสกุลฐานเกิดผ่าน `PR_CALC_006` โดยใช้ `exchange_rate` ที่ snapshot; soft budget commitment ลงทะเบียนในสกุลฐาน (THB) Chain Approver ยังสามารถ send back ด้วยเหตุผล "ใช้สกุลแผนก" แต่นั่นเป็นปลายน้ำ |
| REQ-EDGE-06 | Edit พร้อมกันบน draft เดียวกัน | Draft เดียวเปิดในสอง tab; ทั้งคู่ edit ฟิลด์ต่างกันและคลิก Save อย่างรวดเร็ว | Save แรกชนะและ bump `doc_version`; save ที่สองถูก reject โดย `PR_VAL_016` และ UI prompt reload Last-write-wins **ไม่ใช่** นโยบาย |
| REQ-EDGE-07 | Send-back ได้รับขณะ Requestor ยัง edit อยู่ | ผู้อนุมัติคลิก **Send Back** บน PR ที่อยู่ใน `in_progress`; Requestor มี PR เปิดใน view `draft` (หรือดูหน้า detail) | ตอน refresh / save ถัดไป client เห็น `pr_status` กลับเป็น `in_progress` แล้วด้วย `workflow_current_stage` ที่ rolled back; edit กลับมาใช้ได้ (lock `in_progress` ก่อนหน้าถูกปล่อย) การเปลี่ยน local ที่ยังไม่ save ตั้งแต่ send-back ถูก merge เข้า draft ที่ edit ได้ (`PR_VAL_016` ยังคุ้มกันแต่ละ save) |

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona (`X-PR-02`, `X-PR-09`, `X-PR-10` แตะ Requestor)
- User flow: [03-user-flow-requestor.md](./03-user-flow-requestor.md) — แหล่ง happy-path สำหรับ Section 1 ด้านบน
- กฎทางธุรกิจที่ verify: [02-business-rules.md](./02-business-rules.md) Section 2 (`PR_VAL_001`..`PR_VAL_012`, `PR_VAL_016`) และ Section 4 (`PR_AUTH_001`, `PR_AUTH_004`, `PR_AUTH_007`)
- E2E: `../carmen-inventory-frontend-e2e/tests/302-pr-creator-journey.spec.ts` (block `TC-PR-0501NN`..`TC-PR-0509NN` — list, create, template, draft, edit, submit, delete, golden flow) Loop Returned-PR อยู่ใน `../carmen-inventory-frontend-e2e/tests/311-pr-returned-flow.spec.ts` Coverage permission ต่อ action × ต่อ role อยู่ใน `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` (fixture `requestorTest`, `noAuthTest`)
- ที่มา: `../carmen/docs/purchase-request-management/testing.md` (level testing, test ตัวอย่าง), `../carmen/docs/purchase-request-management/troubleshooting.md` (Section 1.1, 2.1, 3.1, 6.2 — mode failure ที่รู้สำหรับ form submission, workflow / approval, calculation และ permission)
