---
title: การสุ่มตรวจ (Spot Check) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ post และกฎข้ามโมดูลของการสุ่มตรวจ
published: true
date: 2026-07-29T04:45:21.000Z
tags: spot-check, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `SPC_VAL_*` validation &nbsp;·&nbsp; `SPC_AUTH_*` permission &nbsp;·&nbsp; `SPC_CALC_*` calc &nbsp;·&nbsp; `SPC_POST_*` posting &nbsp;·&nbsp; `SPC_XMOD_*` cross-module
> **จำนวนกฎ:** 23 กฎ ยืนยันใหม่กับ `spot-check.service.ts` / `spot-check.logic.ts`
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** § 5.1 มีการเปรียบเทียบ Live Code vs เอกสารวางแผนทีละจุด

## 1. ภาพรวม

หน้านี้รวบรวมกฎการดำเนินงานที่บังคับใช้จริงโดย **โมดูล spot-check** — ต้นไม้เอกสารแบนสองระดับ (`tb_spot_check` → `tb_spot_check_detail`) และ flow แบบตระกูลหน้าจอเดียว (list → create → entry → review → submit) ที่บรรยายใน [spot-check/03-user-flow](/th/inventory/spot-check/03-user-flow) ทุกกฎด้านล่างถูกตรวจสอบกับ `spot-check.service.ts`, `spot-check.logic.ts` และ component ฝั่ง frontend ใน `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`; กฎที่เคยปรากฏในดราฟต์ก่อนหน้าของหน้านี้แต่ไม่มีโค้ดรองรับ (recount, variance-tolerance threshold, rollup เข้า `tb_stock_in`/`tb_stock_out`, GL posting, surface Approver/Auditor/Sysadmin แยกต่างหาก) ถูกลบออกแทนที่จะเก็บไว้เป็น scaffolding ที่ยังไม่ยืนยัน เพราะการค้นทั้ง repo ไม่พบโค้ดรองรับสำหรับสิ่งใดเลย Rule ID ใช้ `SPC_VAL_*` (validation), `SPC_CALC_*` (calculation), `SPC_AUTH_*` (authorization), `SPC_POST_*` (posting), `SPC_XMOD_*` (cross-module)

มีข้อสังเกตเชิงโครงสร้างสองข้อที่ผลต่อทุกกฎด้านล่าง **ข้อแรก** ต่างจาก [physical-count](/th/inventory/physical-count) — ซึ่ง rollup ของตัวเองอย่างน้อยยังสร้างแถว `tb_stock_in`/`tb_stock_out` ดิบที่ไม่ post — การ submit ขั้นสุดท้ายของ spot check ไม่เขียนอะไรที่ไหนเลยนอกจาก `doc_status`/`end_date` ของตัวมันเอง **ข้อที่สอง** ไม่มี source ใน `carmen/docs` สำหรับกฎ `SPC_*`; § 5.1 ด้านล่างเปรียบเทียบโค้ดจริงกับเอกสารระดับวางแผนหนึ่งฉบับจาก E2E repo ที่ข้อกล่าวอ้างหลัก "posting is pending" ตรงกับโค้ดจริง แต่รายละเอียด status lifecycle ไม่ตรง

## 2. กฎ Validation

Rule ID ใช้รูปแบบ `SPC_VAL_NNN`

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `SPC_VAL_001` | `location_id` ต้องอ้างอิง `tb_location` ที่มีอยู่จริงและไม่ถูกลบ | สร้าง (`POST /spot-checks`) | Reject ด้วย `COMMON_LOCATION_NOT_FOUND` ไม่มีการตรวจ `location_type` หรือ `is_active` แยกภายใน `create()` เอง — หน้ารายการเสนอเฉพาะ location ที่กรองแล้วโดย `findCurrentByLocation()` (`location_type ∈ {inventory, consignment}`, `is_active = true`, และ — เว้นแต่ติ๊ก "Include Not Count" — `physical_count_type = yes`) |
| `SPC_VAL_002` | eligible product pool (union ของ `tb_product_location` assignment กับสินค้าใดที่มีสต๊อกสุทธิไม่เป็นศูนย์ที่ location) ต้องไม่ว่างเปล่า | สร้าง | Reject ด้วย `"No products found at this location"` |
| `SPC_VAL_003` | `method = manual` ต้องมี array `product_id[]` ไม่ว่างเปล่า หลังกรองให้เหลือเฉพาะสินค้าใน eligible pool จริง ต้องเหลืออย่างน้อยหนึ่งตัว | สร้าง | Reject ด้วย `"product_id is required for manual selection"` (array ว่าง/ไม่มี) หรือ `"None of the selected products were found at this location"` (กรองแล้วเหลือศูนย์) |
| `SPC_VAL_004` | `method = high_value` ต้องมี `tb_period` อย่างน้อยหนึ่งแถวที่ `status ∈ {open, locked}` | สร้าง | Reject ด้วย `SPOT_CHECK_NO_ACTIVE_PERIOD` ("No active period found") ถ้าไม่มี |
| `SPC_VAL_005` | เอกสารที่ `doc_status = pending` เท่านั้นที่ update ได้ (`description`/`note` เท่านั้น — ไม่มีฟิลด์อื่นแก้ไขได้ผ่าน `update()`) | Update | Reject ด้วย `"Only pending spot checks can be updated"` **ไม่สามารถเข้าถึงได้ผ่านหน้าจอที่ shipped ใด ๆ** — ดู [spot-check](/th/inventory/spot-check) § 1; มีแค่การเรียก Bruno/API โดยตรงเท่านั้นที่ใช้ path นี้ |
| `SPC_VAL_006` | `doc_status = void` หรือ `= completed` บล็อก Reset (`"Spot check is already void"` / `"Completed spot check cannot be reset"`) `pending`/`in_progress` เป็นสถานะเดียวที่ reset ได้ | Reset | Reject ด้วยข้อความที่ยกมาบน `void`/`completed`; อนุญาตนอกเหนือจากนั้น |
| `SPC_VAL_007` | Save (`saveItems()`) ต้องมี array `items[]` ไม่ว่างเปล่า และเอกสารต้องเป็น `pending` หรือ `in_progress` | Save | Reject ด้วย `SPOT_CHECK_NO_ITEMS` ("No items to save") บน array ว่าง หรือ `"Cannot save items when spot check is <status>"` นอก `{pending, in_progress}` |
| `SPC_VAL_008` | `submit()` (ขั้นสุดท้าย) reject เฉพาะเมื่อ `doc_status = completed` หรือ `= void` **ไม่มีการตรวจความครบถ้วน** — เอกสารที่บางบรรทัดยังคง `actual_qty = 0` ที่ seed ไว้สามารถ submit ไปเป็น `completed` ได้โดยไม่ error | Submit | Reject ด้วย `"Spot check is already completed"` / `"Void spot check cannot be submitted"`; นอกเหนือจากนั้นสำเร็จเสมอ |

> **ไม่พบในโค้ด (ลบออกจาก catalogue นี้):** การตรวจ tolerance-threshold แบบเปอร์เซ็นต์หรือปริมาณสัมบูรณ์ที่ขับเคลื่อนสถานะ "flag for recount"; action recount แยกต่างหากที่ทำโดย counter คนละคน; location-level transaction lock ที่บล็อก GRN/SR/posting อื่นระหว่าง spot check เปิดอยู่; toggle "blind count" (หน้า entry เพียงแค่ไม่ render `on_hand_qty` ให้ counter เห็นเลย โดยการออกแบบหน้า ไม่ใช่ toggle ที่ config ได้); gate ความครบถ้วนที่ API layer (มีแค่ button visibility ฝั่ง client เท่านั้นที่บังคับ "นับครบทุกบรรทัด")

## 3. กฎการคำนวณ

Rule ID ใช้รูปแบบ `SPC_CALC_NNN` ฟิลด์ปริมาณเป็น `Decimal(20, 5)` บน `tb_spot_check_detail.on_hand_qty` / `actual_qty` / `diff_qty`

| Rule ID | สูตร |
| ------- | ------- |
| `SPC_CALC_001` (variance qty) | `diff_qty = actual_qty − on_hand_qty` ต่อบรรทัด คำนวณฝั่ง server โดยทั้ง `saveItems()` (เทียบกับ `on_hand_qty` ที่เก็บอยู่ปัจจุบัน) และ `reviewItems()` (เทียบกับ `on_hand_qty` ที่คำนวณสดใหม่) |
| `SPC_CALC_002` (การคำนวณ on-hand ใหม่ตอน review) | `reviewItems()` คำนวณ `on_hand_qty` ทุกบรรทัดเป็น `Σ tb_inventory_transaction_detail.qty` ที่ `location_id` ของ spot check จัดกลุ่มตาม `product_id` โดยไม่มี date cut-off — ยอด ledger สดตอนกด "Submit for Review" ซึ่งอาจต่างจากยอดที่จับตอนสร้าง |
| `SPC_CALC_003` (สรุป review) | `getReview()`/payload review คำนวณ `matched = count(diff_qty === 0)`, `variant = total − matched`; หน้า review คำนวณเพิ่ม `overages = count(diff_qty > 0)` และ `shortages = count(diff_qty < 0)` ฝั่ง client จาก `diff_qty` เดียวกัน **ไม่มีการคำนวณมูลค่าผลต่างเป็นตัวเงินที่ใดเลย** — `diff_qty × cost_per_unit` ไม่มีอยู่ในโมดูลนี้; cost ปรากฏเฉพาะเป็น *input การจัดอันดับตอนเลือกตัวอย่าง* สำหรับ method `high_value` (§ 4 ด้านล่าง) ไม่เคยเป็นการตีมูลค่าของ variance ที่นับได้ |
| `SPC_CALC_004` (การจัดอันดับ high-value) | สำหรับ `method = high_value`: จัดอันดับสินค้าแต่ละตัวใน pool ด้วย `on_hand_qty × max(cost_per_unit)` โดย max cost อ่านจากแถว `tb_inventory_transaction_cost_layer` ที่ location นั้นด้วย `in_qty > 0` และ `lot_at_date` อยู่ในช่วง `[start_at, end_at]` ของงวดที่ active; สินค้าต่ำกว่า `minimum_cost` floor (ถ้ามี) ถูกคัดออก; สินค้าที่ไม่พบ cost ถูกต่อท้ายกลุ่มที่มี cost (เฉพาะเมื่อไม่ได้ตั้ง `minimum_cost`) เรียงตามที่ถูก assign ให้ location ล่าสุดก่อน; `size` ตัวแรก (หรือน้อยกว่าถ้า pool เล็กกว่า) ถูกเก็บไว้ |

## 4. กฎ Authorization

Rule ID ใช้รูปแบบ `SPC_AUTH_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `SPC_AUTH_001` | ทุก action list, create, save, review, submit, reset, delete และ comment ในโมดูลนี้ถูกกำหนดสิทธิ์ด้วย permission key CRUD เดียว: `inventory_management.spot_check` (`constant/permissions.ts`) ไม่พบ permission variant แยกสำหรับ create-only, approve-only หรือ read-only |
| `SPC_AUTH_002` | ไม่พบข้อจำกัดแบบ zone-based, location-scoped-to-user หรือ "assigned counter" ใน `spot-check.service.ts` — ผู้ใช้ใดที่มี permission ของโมดูลสามารถเปิด นับ และ submit spot check ที่ location ใดก็ได้ มีตาราง `tb_user_location` ทั่วไปอยู่ที่อื่นใน schema สำหรับ location-level access grant แต่ไม่พบการอ้างอิงถึงมันใน service code ของโมดูลนี้เอง |
| `SPC_AUTH_003` | ไม่มี permission, route หรือ workflow stage ของ Approver/Finance Reviewer, Auditor หรือ Sysadmin สำหรับโมดูลนี้ — ไม่มีอะไรให้ review หรืออนุมัติ เพราะการ submit ขั้นสุดท้ายไม่มีเอกสารหรือผล ledger ปลายทางให้ gate |

## 5. กฎการ Posting

Rule ID ใช้รูปแบบ `SPC_POST_NNN` "Posting" สำหรับโมดูลนี้หมายถึงเฉพาะการเปลี่ยนสถานะที่ทำโดย `submit()` — ไม่มี rollup ไม่มีเอกสาร adjustment ไม่มีการเขียน ledger

| Rule ID | กฎ |
| ------- | ---- |
| `SPC_POST_001` | `submit()` ตั้ง `doc_status = completed` และ stamp `end_date = now()` นั่นคือผลทั้งหมดของการ submit ขั้นสุดท้าย |
| `SPC_POST_002` | ไม่มีเอกสาร `tb_stock_in`/`tb_stock_out` ถูกสร้าง และไม่มี row `tb_inventory_transaction` ถูกเขียน โดย `submit()` — ยืนยันทั้งจากการไม่มี import/call ที่ตรงกันใน `spot-check.service.ts` และ doc-comment ของ method เอง: *"Does not create stock-in/stock-out — any follow-up adjustments are user-driven."* นี่เป็นกลไกที่ง่ายกว่า (และ automate น้อยกว่า) มากกว่าการ submit ขั้นสุดท้ายของ [physical-count](/th/inventory/physical-count) เอง (ซึ่งอย่างน้อยยังสร้างแถว stock-in/out ดิบโดยไม่ post ไปยัง ledger) |
| `SPC_POST_003` | การแก้ไขผลต่างที่ยืนยันแล้วจึงต้องให้ผู้ใช้สร้างเอกสาร Stock In/Out ธรรมดาแยกต่างหากใน [inventory-adjustment](/th/inventory/inventory-adjustment) เอง ไม่มีฟิลด์ convention JSON หรือ description string ใด ๆ เชื่อมเอกสารนั้นย้อนกลับไปยัง spot check ที่พบผลต่าง — audit trail ถ้าจำเป็นต้องสร้างขึ้นมาต้องทำ manual (เช่น จับคู่ location และวันที่) |
| `SPC_POST_004` | เมื่อ `submit()` สำเร็จแล้ว การเรียก Save/Submit-for-Review เพิ่มเติมต่อเอกสารเดียวกันถูก reject โดย `SPC_VAL_007` (guard สถานะของ `saveItems()` เอง) **`reviewItems()` ไม่มี guard ที่เทียบเท่า** — มันจะคำนวณและเขียนทับ `on_hand_qty`/`actual_qty`/`diff_qty`/`counted_at` บนทุกแถว detail ของเอกสารที่ `completed` (หรือ `void`) แล้ว หาก endpoint นั้นถูกเรียกอีก เช่น เปิด spot check ที่ completed แล้วจาก tab History ของหน้ารายการ (ซึ่ง click handler routing ไปหน้า entry เดียวกันไม่ว่างสถานะใด) แล้วกด "Submit for Review" อีกครั้ง มีเพียง call `submit()` ขั้นสุดท้ายเท่านั้นที่ถูก guard (`SPC_VAL_008`) นี่เป็นช่องว่างที่ยืนยันแล้วในโค้ด ไม่ได้ถูกทดสอบด้วย automated test แยกต่างหาก |

## 5.1 การเปรียบเทียบ Live Code vs เอกสารวางแผน

ไม่มี catalogue `SPC-*` ใน `carmen/docs` สำหรับโมดูลนี้ เอกสารอ้างอิงที่ใกล้เคียงที่สุดคือเอกสารระดับวางแผนใน E2E repo, `docs/persona-doc/System Process/tx-10-spot-check.md` (v1.0.0, 2026-04-27) — เอกสารออกแบบสไตล์ BRD ไม่ใช่ automated test หรือพฤติกรรมที่ยืนยันว่า shipped แล้ว

> Diff legend: ✅ ตรงกับโค้ดจริง · 🟡 เปลี่ยนชื่อ/ยุบใน live schema · 🔴 มีแค่ในเอกสารวางแผน (ไม่มีโค้ดรองรับ)

| หัวข้อ | เอกสารวางแผน (`tx-10-spot-check.md`) | Live Code | Diff |
|---|---|---|---|
| การ post variance ไปยัง inventory | "Real-time variance posting to inventory is listed as **Pending** — not yet implemented... does not post variance adjustments to inventory, lots, or cost." | ยืนยันตรงเป๊ะ: `submit()` ไม่มีผลการ posting ใด ๆ เลย และ doc-comment ของตัวมันเองก็ระบุไว้ตรง ๆ | ✅ |
| ชุดสถานะ | หกค่า: `draft`, `pending`, `in-progress`, `on-hold`, `completed`, `cancelled` | `enum_spot_check_status` มีสี่ค่า: `pending`, `in_progress`, `void`, `completed` ความแตกต่างระหว่าง `draft`/`pending` ก่อนนับ และสถานะ pause `on-hold` ของเอกสารไม่มี schema เทียบเท่า; `cancelled` แม็พไปที่ `void` จริง | 🟡 |
| ประเภทการตรวจ | ห้า: `random`, `targeted`, `high-value`, `variance-based`, `cycle-count` | `enum_spot_check_method` มีสาม: `random`, `high_value`, `manual` `targeted`/`variance-based`/`cycle-count` ไม่มี schema เทียบเท่า; analog ที่ใกล้เคียงที่สุดของ "targeted" ในโค้ดคือ `manual` (เลือกสินค้าเอง) | 🟡 |
| รูปแบบหมายเลขอ้างอิง | `SC-YYMMDD-XXXX` | running-code service สร้าง `spot_check_no` จาก pattern วันที่ + ลำดับที่ tenant config ได้ ประเภท `SPOT-CHECK` — รูปแบบที่แท้จริง config โดย tenant ผ่านหน้า running-code ที่แชร์ ไม่ได้ hardcode เป็น `SC-YYMMDD-XXXX` | 🟡 |
| Gate End Period Close | "All Spot Checks must be `completed` before End Period Close Stage 2" | การค้นทั้ง repo ใน `period-end.validate.ts` สำหรับการอ้างอิง `spot` ใด ๆ ไม่พบผลลัพธ์เลย — spot check **ไม่ใช่** period-end gate ชนิดใดเลย สอดคล้องกับข้อค้นพบเดียวกันที่ยืนยันแล้วในการ re-sync ของโมดูล [inventory](/th/inventory/inventory) เอง | 🔴 |
| Pause/resume | `in-progress → on-hold → in-progress` สำหรับ "staff/items unavailable" | ไม่มีสถานะ `on_hold`/pause — ผู้ใช้แค่ออกจากหน้า entry แล้วกลับมาใหม่ทีหลังได้ (เอกสารยังคง `in_progress` หรือ `pending` พร้อมสิ่งที่ยังไม่ได้ save ในเครื่องหายไป — มีเพียง call Save เท่านั้นที่ persist ความคืบหน้า) | 🔴 |

**คำแนะนำสำหรับผู้เขียน test:** ถือกรอบ "posting is pending" ของ `tx-10-spot-check.md` ว่ายืนยันแล้วและยั่งยืน — ไม่มีหลักฐานว่าฟีเจอร์ posting กำลังจะมาในเร็ว ๆ นี้ — แต่เขียน assertion ของ status lifecycle ตาม `enum_spot_check_status` สี่ค่าจริง ไม่ใช่คำบรรยายหกค่าของเอกสารวางแผน

## 6. กฎข้ามโมดูล

Rule ID ใช้รูปแบบ `SPC_XMOD_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `SPC_XMOD_001` | **→ [inventory-adjustment](/th/inventory/inventory-adjustment)**: ไม่มีลิงก์อัตโนมัติใด ๆ ผลต่างที่ยืนยันแล้วถูกแก้ไขได้ก็แต่โดยผู้ใช้สร้างเอกสาร Stock In/Out แยกต่างหากที่นั่นด้วยตัวเอง — ไม่มีสิ่งใดใน spot check เองที่อ้างอิง trigger หรือ pre-fill action นั้น |
| `SPC_XMOD_002` | **→ [inventory](/th/inventory/inventory)**: spot check อ่าน ledger (`tb_inventory_transaction_detail`) สองครั้ง — ครั้งแรกเพื่อสร้าง eligible product pool และ seed `on_hand_qty` ตอนสร้าง อีกครั้งตอน Submit-for-Review เพื่อ refresh `on_hand_qty` — แต่ไม่เคยเขียนลงไป |
| `SPC_XMOD_003` | **→ [master-data/location](/th/inventory/master-data/location)**: filter default ของหน้ารายการ (ซ่อน location ที่ flag `physical_count_type = no` เว้นแต่ติ๊ก "Include Not Count") ใช้ admin flag ระดับ location ตัวเดียวกับที่ [physical-count](/th/inventory/physical-count) ใช้สำหรับ period-end gate ของตัวเอง — แต่ spot check เองไม่ใช่ period-end gate |
| `SPC_XMOD_004` | **→ [physical-count](/th/inventory/physical-count)**: spot check เป็นลูกพี่ลูกน้อง ad-hoc ที่แคบกว่าของการนับบางส่วน — document tree ที่แยกกันโดยสิ้นเชิง (ไม่มีตารางหรือ enum ที่แชร์) ซึ่งบังเอิญใช้ union logic ของ product-pool เดียวกันและ generic notes-dialog UI component เดียวกัน |

## 7. แหล่งอ้างอิง

- **Primary:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (create/update/delete/reset/saveItems/reviewItems/getReview/submit), `spot-check.logic.ts` (sampling strategies)
- **Secondary (ระดับวางแผน ยืนยันบางส่วน):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-10-spot-check.md`
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/` (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`); `constant/permissions.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; manual test-case catalog ที่ `docs/test-cases/760-spot-check.md`
- ชุดกฎที่เกี่ยวข้อง: [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_*` — คู่เทียบการนับเต็มที่อย่างน้อยยังสร้างแถว stock-in/out ที่ไม่ post ตอน submit), [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) (`ADJ_*` — จุดที่ต้อง manual แก้ไขผลต่างที่ยืนยันแล้ว), [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) (semantics ของ ledger — โมดูลนี้ไม่เคยไปถึงเลย)
