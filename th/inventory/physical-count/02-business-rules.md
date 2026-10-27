---
title: การนับสต๊อกประจำงวด (Physical Count) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ post และกฎข้ามโมดูลของการนับสต๊อกประจำงวด
published: true
date: '2026-10-27T15:00:00.000Z'
tags: physical-count, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `PHC_VAL_*` validation &nbsp;·&nbsp; `PHC_AUTH_*` permission &nbsp;·&nbsp; `PHC_CALC_*` calc &nbsp;·&nbsp; `PHC_POST_*` posting &nbsp;·&nbsp; `PHC_XMOD_*` cross-module
> **จำนวนกฎ:** 16 กฎ ยืนยันใหม่เทียบกับ `physical-count.service.ts` / `physical-count-period.service.ts` / `period-end.validate.ts`
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** § 5.1 มีตารางเปรียบเทียบ Live Code กับเอกสารวางแผนทีละจุด

## 1. ภาพรวม

หน้านี้รวบรวมกฎการดำเนินงานที่บังคับใช้จริงโดย **โมดูล physical-count** — ต้นไม้เอกสารสามระดับ (`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`) และ flow ตระกูลหน้าจอเดียว (list → entry → review → submit) ที่อธิบายใน [physical-count/03-user-flow](/th/inventory/physical-count/03-user-flow) ทุกกฎด้านล่างถูกตรวจสอบเทียบกับ `physical-count.service.ts`, `physical-count-period.service.ts`, `period-end.validate.ts` และ component frontend ใน `../carmen-frontend/routes/inventory-management/physical-count/`; กฎที่ปรากฏใน draft ก่อนหน้าของหน้านี้โดยไม่มีโค้ดรองรับ (recount, tolerance threshold, location transaction-lock, การ post GL, surface ของ Approver/Auditor/Sysadmin แยก) ถูกลบออกแทนที่จะเก็บไว้เป็น scaffolding ที่ยังไม่ยืนยัน เพราะการค้นทั่ว repo ไม่พบโค้ดรองรับใด ๆ เลย Rule ID ใช้ `PHC_VAL_*` (validation), `PHC_CALC_*` (calculation), `PHC_AUTH_*` (authorization), `PHC_POST_*` (posting), `PHC_XMOD_*` (cross-module)

มีข้อสังเกตเชิงโครงสร้างสองข้อที่ผลต่อทุกกฎด้านล่าง **ข้อแรก** variance rollup ตอน Submit สุดท้ายเขียนตรงเข้า `tb_stock_in`/`tb_stock_out` (ตารางที่ [inventory-adjustment](/th/inventory/inventory-adjustment) ใช้ด้วย) ที่สถานะ `completed` โดยข้ามเส้นทาง Save/Commit ของโมดูลนั้น — แต่ตั้งแต่โค้ดรอบ 2026-10 มัน **post แต่ละบรรทัดเอง** ผ่าน `executeAdjustmentIn` / `executeAdjustmentOut` จึงมี row `tb_inventory_transaction` ต่อบรรทัด; เอกสารมี adjustment type `eop_in` / `eop_out` ของ BU และไม่มีฟิลด์เชื่อมกลับไปยังการนับ (ดู [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) § 1/§ 3) **ข้อสอง** ไม่มี source ใน `carmen/docs` สำหรับกฎ `PHC_*`; § 5.1 ด้านล่างจึงเทียบโค้ดจริงกับเอกสารวางแผนเชิงความปรารถนาสองฉบับจาก E2E repo ที่อธิบายการออกแบบที่ต่างอย่างมีนัยสำคัญและยังไม่ถูกสร้าง

## 2. กฎ Validation

Rule ID ใช้รูปแบบ `PHC_VAL_NNN`

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `PHC_VAL_001` | `tb_physical_count_period.status` ต้องเป็น `counting` อยู่แล้วสำหรับ period เป้าหมาย | สร้างเอกสาร count (`POST /physical-counts`) | Reject ด้วย `"Physical Count Period is not in counting status"` การเปลี่ยนเป็น `counting` ทำโดย **Start Period Close** (`POST /period-ends/start-counting`, `PeriodEndService.startCounting`, 2026-08-27) ซึ่งตัวมันเองจะปฏิเสธตราบใดที่ยังมี GRN ที่ไม่ใช่ `committed`/`voided`, stock-in / stock-out ที่ไม่ใช่ `completed`/`cancelled`/`voided` หรือ SR ที่มีเลขที่แล้วซึ่งอยู่ที่ `draft`/`in_progress` ลงวันที่ในงวดนั้น (`PERIOD_END_START_COUNTING_BLOCKED`, 422) frontend (`pc-component.tsx`) ไม่ส่ง create เลยขณะที่ `period.status !== "counting"` — แต่แสดง dialog "Counting has not started" พร้อมปุ่ม **Go to Period End** แทน |
| `PHC_VAL_002` | `location_id` ต้องอ้างอิง `tb_location` ที่มีอยู่จริงและไม่ถูกลบ | สร้างเอกสาร count | Reject ด้วย error location-not-found `create()` **ไม่** ตรวจสอบ `location_type` หรือ `is_active`/`physical_count_type` เป็นอิสระ — หน้ารายการเสนอเฉพาะสถานที่ที่ถูกกรองแล้วโดย `findCurrent()` (`location_type ∈ {inventory, consignment}`, `is_active = true`, และ — ถ้าไม่ได้เช็ค "include not-counted" — `physical_count_type = yes`) ดังนั้นข้อจำกัดประเภทสถานที่จึงบังคับโดยสิ่งที่ UI แสดง ไม่ใช่โดย create endpoint เอง |
| `PHC_VAL_003` | ถ้า `tb_physical_count` มีอยู่แล้วสำหรับ `(period, location)` `create()` จะไม่สร้างซ้ำ — มันรัน product union ใหม่และเพิ่มบรรทัดที่เข้าเงื่อนไขใหม่เข้าเอกสารที่มีอยู่ แล้วคืน `id`/`doc_version` ของเอกสารนั้น | สร้างเอกสาร count (path idempotent) | ไม่มี error; ทำหน้าที่เป็น "resume/refresh" โดยปริยาย ไม่ใช่ conflict |
| `PHC_VAL_004` | ทุกบรรทัด `tb_physical_count_detail` ต้องมี `counted_at != null` ก่อนเอกสารจะ submit ได้ | Submit (`PATCH .../submit`) | Reject ด้วย `"<N> products have not been counted yet"` ทั้ง **Save** (`PATCH .../save`) และ **Submit for Review** (`PATCH .../review`, สำหรับบรรทัดที่ได้รับซึ่งไม่เคยถูก stamp) ตั้ง `counted_at`; บรรทัดที่ถูก stamp แล้วคงเวลาเดิม — ดู [physical-count](/th/inventory/physical-count) § 3 |
| `PHC_VAL_005` | `actual_qty` ถูก parse ที่ client ด้วย `Math.max(0, Number.parseFloat(raw) || 0)` (`entry-item-row.tsx`) — input ที่ติดลบถูก clamp เป็น `0` ก่อนถึง API เลย ไม่พบการตรวจสอบขั้นต่ำฝั่ง server ที่ตรงกันใน `physical-count.service.ts` | ป้อนบรรทัด (client-side เท่านั้น) | Input ที่ไม่ใช่ตัวเลขหรือติดลบถูก clamp เป็นตัวเลขที่ถูกต้องเงียบ ๆ ใน UI ยังไม่ยืนยันว่าถูกบังคับใช้อิสระโดย backend |
| `PHC_VAL_006` | `tb_physical_count.status === completed` บล็อก **Save**, **Submit for Review**, และ **Submit** (`"Physical Count is already completed"`) และบล็อก **Delete** (`"Cannot delete completed Physical Count"`) | Save / Review / Submit / Delete | Reject ด้วยข้อความที่ยกมา ไม่มี guard ที่เทียบเท่าบน **Update** (`PATCH .../physical-counts/:id`, การแก้ไข `description` เท่านั้นแบบ legacy) — มันยอมรับการเปลี่ยน description บนเอกสาร `completed` ถ้าถูกเรียกโดยตรง แม้ route นี้จะเข้าถึงไม่ได้จาก flow navigation จริง (ดู [physical-count](/th/inventory/physical-count) § 1) |
| `PHC_VAL_007` | ทุก call `save`/`update`/`review`/`submit` ต้องส่ง `doc_version` ปัจจุบัน; ค่าไม่ตรงกับที่เก็บไว้จะถูกแปลงโดย decorator `@TryCatch` ที่ใช้ร่วมกันเป็นผล `ALREADY_EXISTS` แบบ `409` | Save / Update / Review / Submit | Reject เมื่อ `doc_version` ไม่ตรง; เพิ่มขึ้นเมื่อสำเร็จ ดู [system-config/doc-version](/th/inventory/system-config/doc-version) |

> **ไม่พบในโค้ด (ถูกลบออกจาก catalogue นี้):** การตรวจสอบ tolerance-threshold แบบเปอร์เซ็นต์หรือปริมาณสัมบูรณ์ที่ขับเคลื่อนสถานะ "flag for recount"; action recount แยกที่ทำโดย "counter คนละคน"; location-level transaction lock ที่บล็อกการ post GRN/SR/อื่น ๆ ระหว่างที่การนับ `in_progress`; toggle "blind count" ที่ซ่อน book quantity จาก counter (หน้า entry เพียงแค่ไม่ render `on_hand_qty` ให้ counter เห็นเลย โดยการออกแบบของหน้า ไม่ใช่ toggle ที่ตั้งค่าได้)

## 3. กฎการคำนวณ

Rule ID ใช้รูปแบบ `PHC_CALC_NNN` ฟิลด์ปริมาณเป็น `Decimal(20, 5)` บน `tb_physical_count_detail.on_hand_qty` / `actual_qty` / `diff_qty`

| Rule ID | สูตร |
| ------- | ------- |
| `PHC_CALC_001` (variance qty) | `diff_qty = actual_qty − on_hand_qty` ต่อบรรทัด คำนวณฝั่ง server ทั้งโดย `save()` (เทียบกับ `on_hand_qty` ที่เก็บอยู่ในขณะนั้น) และโดย `reviewItems()` (เทียบกับ `on_hand_qty` ที่คำนวณสดใหม่) |
| `PHC_CALC_002` (การคำนวณ on-hand ใหม่) | `reviewItems()` คำนวณ `on_hand_qty` ของ **ทุก** บรรทัดเป็นยอด cost-layer ของงวดที่นับที่ `location_id` ของการนับ — `getLocationOnHand` (`location-on-hand.helper.ts`): `Σ in_qty − Σ out_qty` ครอบ row `tb_inventory_transaction_cost_layer` ที่ไม่ถูกลบซึ่ง `at_period` = รหัสของงวดของการนับ (`getCountedPeriod`: count → `physical_count_period_id` → `tb_inventory_period.period`); สินค้าที่ไม่มี layer อ่านเป็น `0` ยอดจึงเป็นสต๊อกยกมาของงวดบวก movement ของงวดเอง โดยไม่รวม movement ที่ post เข้างวดถัดไปแล้วและ row ของเอกสารที่ void (ผลรวมเดิมจาก `tb_inventory_transaction_detail` นับทั้งสองอย่าง) มันถูกคำนวณใหม่ ณ ขณะที่กด "Submit for Review" ไม่ได้ถูกตรึงตอนสร้าง sheet product pool ตอน `create()` / `refresh()` ใช้ helper เดียวกัน `reviewItems()` ยัง stamp `counted_at` / `counted_by_id` บนบรรทัดที่ถูกนับเป็นครั้งแรกด้วย (fix `4eb1abfa5`, 2026-08-27) — ก่อน fix นั้น sheet ที่นับผ่านขั้น review อย่างเดียวถูก `submit()` reject ว่า "not counted" |
| `PHC_CALC_003` (progress) | `product_counted` ถูกคำนวณใหม่ทุกครั้งที่เรียก `save()`/`reviewItems()` เป็นจำนวนบรรทัดที่มี `actual_qty` ที่ effective ไม่เป็น null/ไม่เป็นศูนย์; `product_total` คือจำนวนบรรทัดบน sheet (ตั้งตอน create/refresh) ตัวเลขเปอร์เซ็นต์ความคืบหน้าบนหน้า entry คือ `Math.round(counted / total × 100)` คำนวณฝั่ง client จากตัวเลขเดียวกัน |
| `PHC_CALC_004` (ต้นทุน rollup) | ที่ `submit()` สุดท้าย บรรทัด**ส่วนเกิน**ถูกตั้งราคาหนึ่งครั้งต่อ submit ผ่าน `CostingService.getCostsPerUnit()` ด้วยวิธีที่ BU บันทึกเป็น *Default price for added items* (`si.cost-from`; `getUsableCostingMethod` → ค่าเริ่มต้น `last_cost` และ `average` ใช้ได้เฉพาะบน BU ที่คิดต้นทุนแบบ average ไม่เช่นนั้น fallback พร้อม warning) ตัดที่สิ้นวันธุรกิจสุดท้ายของงวดที่นับและจำกัดขอบเขตที่งวดที่นับ; `total_cost = cost_per_unit × diff_qty` บรรทัด**ส่วนขาด**ไม่ถูกตั้งราคาล่วงหน้า: `executeAdjustmentOut` บริโภค lot (FIFO) หรือใช้ค่าเฉลี่ย ณ ขณะนั้น และ `getPostedCost` คัดลอก `cost_per_unit` / `total_cost` ที่ post แล้วลงบรรทัด stock-out (`note` ของมันลงท้าย `@ <cost> (<ledger method>)`) key `physical_count_costing_method` ต่อ BU แบบเดิมไม่ถูกอ่านอีกต่อไป |

## 4. กฎ Authorization

Rule ID ใช้รูปแบบ `PHC_AUTH_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_AUTH_001` | ทุก action ของ list, create, save, review, submit, refresh, delete และ comment ในโมดูลนี้ถูก gate ด้วย permission key CRUD เดียว: `inventory_management.physical_count` (`constant/permissions.ts`) ไม่พบ permission variant แยกสำหรับ create-only, approve-only หรือ read-only สำหรับโมดูลนี้ |
| `PHC_AUTH_002` | ไม่พบข้อจำกัดแบบ zone, location-scoped-to-user หรือ "assigned counter" ใน `physical-count.service.ts` — ผู้ใช้ใดก็ตามที่ถือ permission ของโมดูลสามารถเปิด ป้อน และ submit เอกสาร count ใดก็ได้ ตาราง `tb_location_user` ทั่วไปมีอยู่ใน schema สำหรับ location-level access grant ที่อื่นในผลิตภัณฑ์ แต่ไม่พบการอ้างอิงถึงมันในโค้ด service ของโมดูลนี้เอง ให้ถือว่า claim "counter ถูกจำกัดขอบเขตเฉพาะสถานที่ที่ได้รับมอบหมาย" ยังไม่ยืนยันสำหรับโมดูลนี้โดยเฉพาะ |
| `PHC_AUTH_003` | ไม่มี permission, route หรือ workflow stage ของ Approver/Finance Reviewer, Auditor หรือ Sysadmin สำหรับโมดูลนี้ — ขั้นตอน "review" และ "submit" สุดท้ายทั้งคู่ทำโดยผู้ใช้ permission-gated คนเดียวกันที่ทำการนับ ในเซสชันเดียวกัน |

## 5. กฎการ Posting

Rule ID ใช้รูปแบบ `PHC_POST_NNN` "Posting" ในโมดูลนี้หมายถึง variance-rollup transaction ที่ยิงภายใน `submit()` — ทั้งการสร้างเอกสาร **และ**การ post เข้า ledger

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_POST_001` | ที่ `submit()`, service แบ่งบรรทัด detail ที่ `diff_qty ≠ 0` ตามเครื่องหมาย: ทุกบรรทัด variance บวกเข้า `tb_stock_in` ใหม่ **หนึ่ง**ฉบับ; ทุกบรรทัด variance ลบเข้า `tb_stock_out` ใหม่ **หนึ่ง**ฉบับ บรรทัดที่ `diff_qty = 0` ไม่สร้าง rollup row ทั้งสอง header ถูก insert ด้วย `doc_status: enum_doc_status.completed` ทันที (ไม่มีขั้น draft หรืออนุมัติ ต่างจากหน้าจอ Stock In/Out แบบ manual ที่สร้าง `draft` และ post เมื่อกด **Commit**) ออกเลขด้วย `reserveStockDocumentNumbers` (`STOCK-IN` / `STOCK-OUT`) จากวันสิ้นงวดที่นับ |
| `PHC_POST_002` | header มี adjustment type **`eop_in`** (stock-in) / **`eop_out`** (stock-out) ที่ active ของ BU ค้นหาด้วย `type` (แถวที่ active และไม่ถูกลบที่เก่าสุดก่อน) ไม่ใช่ด้วย code ถ้า type ที่ต้องการไม่มี submit จะถูกปฏิเสธก่อนเขียนใด ๆ: ``No active adjustment type of type <eop_in\|eop_out> for this business unit`` (`INVALID_ARGUMENT`) ทั้งฟิลด์ `info` JSON ของ header และของบรรทัด detail ใด ๆ ไม่ถูกใส่ค่า — **ไม่มี**ฟิลด์เชื่อมแบบมีโครงสร้างกลับไปยัง `tb_physical_count` ต้นทาง; เนื้อเยื่อเชื่อมต่อเดียวคือสตริง `description` (``Physical Count Adjustment - Period yyyy-MM``) และ `note` ต่อบรรทัด |
| `PHC_POST_003` | `submit()` **เรียก** `InventoryTransactionService.executeAdjustmentIn` (ส่วนเกิน; โดย `doc_date` = สิ้นงวดที่นับเพื่อให้ layer ถูก stamp เข้างวดนั้น) และ `executeAdjustmentOut` (ส่วนขาด) ทีละบรรทัด ภายใน `$transaction` เดียวกับที่สร้างเอกสารและพลิกการนับเป็น `completed`; แต่ละแถว detail ถูกเขียนพร้อม `inventory_transaction_id` ความล้มเหลว — โดยเฉพาะ `Insufficient stock. Requested: …, Available: …` เมื่อ location ไม่มีสต๊อกพอรองรับส่วนขาด — จะยกเลิก submit ทั้งหมด ทิ้งการนับไว้ที่ `in_progress` *(กลับผลสรุป 2026-09-22 ที่ว่า "submit ไม่เคย post เข้า ledger"; ตรวจซ้ำ 2026-10-27 ที่ `physical-count.service.ts` `submit()` / `postAdjustmentIn` / `postAdjustmentOut`)* |
| `PHC_POST_004` | เมื่อ `submit()` สำเร็จ `tb_physical_count.status` จะเป็น `completed` และ `completed_at`/`completed_by_id` ถูก stamp; เอกสารจะถูก reject โดย completed-guard ของตัวมันเอง (`save()`/`reviewItems()`/`submit()`, `PHC_VAL_006`) — การแก้ไขใด ๆ ในภายหลังต้องสร้าง adjustment ใหม่ที่เป็นอิสระผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) ไม่ใช่การเปิด count ใหม่ |

## 5.1 ความแตกต่างระหว่าง Live Code กับเอกสารวางแผน

ไม่มี catalogue ของกฎ `PHC-*` ใน carmen/docs สำหรับโมดูลนี้ อ้างอิงที่ใกล้ที่สุดที่มีคือเอกสารระดับวางแผนใน E2E repo, `docs/persona-doc/System Process/tx-08-physical-stocktake.md` (เวอร์ชัน 1.1.1, 2026-04-27) — เอกสารออกแบบสไตล์ BRD **ไม่ใช่** test อัตโนมัติหรือพฤติกรรมที่ยืนยันว่า ship แล้ว การอ่าน implementation ปัจจุบันโดยตรงแสดงว่ามันต่างจากเอกสารนั้นในเกือบทุกจุดสำคัญ:

> Diff legend: 🔵 เอกสารวางแผนเท่านั้น (ไม่มีโค้ดรองรับ) · 🔴 live code ต่างจากคำอธิบายในเอกสารวางแผน

| หัวข้อ | เอกสารวางแผน (`tx-08-physical-stocktake.md`) | Live code | Diff |
|---|---|---|---|
| ประเภท transaction | "Post เป็น **Physical Stocktake transaction type ของตัวเอง** — **ไม่ใช่** Stock In/Out adjustment" | `submit()` สร้าง row `tb_stock_in`/`tb_stock_out` จริง ๆ ชนิด `eop_in` / `eop_out` — กลไกที่เอกสารวางแผนบอกว่ามันไม่ใช่ ไม่มี physical-count transaction type แยกบน `enum_transaction_type`; ledger rows เป็น `adjustment_in` / `adjustment_out` ปกติ | 🔴 |
| ผลกระทบต่อ ledger | Variance "เปลี่ยน QOH", "ปรับ lot", trigger "Cost Calculation" (AVCO re-average / เพิ่ม layer FIFO) | ส่วนใหญ่ถูก implement แล้วตั้งแต่โค้ดรอบ 2026-10: `submit()` post ผ่าน `executeAdjustmentIn/Out` (§ `PHC_POST_003`) on-hand จึงเปลี่ยน, ส่วนเกินเพิ่ม cost layer, ส่วนขาดบริโภค lot / ใช้ค่าเฉลี่ย ที่ยังไม่มี: transaction type สำหรับ stocktake โดยเฉพาะ, การ post GL และขั้น `FINALIZED` | 🔴 |
| วงจรชีวิตสถานะ | สามสถานะ: `IN PROGRESS → COMPLETED → FINALIZED` โดย `FINALIZED` หมายถึง "variance adjustment ถูก post ไปยัง GL" และจำเป็นสำหรับ End Period Close Stage 3 | `enum_physical_count_status` มีสามค่า (`pending`, `in_progress`, `completed`) แต่ไม่มีค่า `finalized` และไม่มีขั้นตอน post GL ใด ๆ ในโค้ดทั้งหมด `completed` เป็นสถานะปลายทาง Gate การปิดงวดจริง (`period-end.validate.ts`'s `validatePhysicalCount`) ตรวจสอบเพียง `status = completed` ที่แต่ละสถานที่จำเป็น — ไม่มี milestone GL-posted แยกที่ต้องผ่าน | 🔴 |
| Transaction lock | "Transaction ที่สถานที่ถูกล็อกขณะ Physical Count เป็น IN PROGRESS" — GRN, CRN, SR, Issues, Sales, Stock In/Out adj ทั้งหมดถูกบล็อก | ไม่พบ guard ที่ตรงกันในทั้ง service ของ GRN, SR หรือ stock-in/out — การค้นแบบตรงเป้าหมายสำหรับการตรวจสอบ physical-count ใน module เหล่านั้นให้ผล 0 hits | 🔵 |
| Tolerance / recount | บอกเป็นนัยโดย draft ก่อนหน้าของหน้าวิกินี้ ไม่ได้ปรากฏจริงใน `tx-08` | ไม่มี tolerance percentage, absolute-quantity threshold หรือ recount flow ใด ๆ ในทั้ง frontend หรือ backend สำหรับโมดูลนี้ | 🔵 |
| การจัดการ lot ของ variance บวก | "New lot created (or existing lot adjusted up — TBC)" | ส่วนเกิน post layer ใหม่ผ่าน `executeAdjustmentIn` ที่ราคา `si.cost-from` (เลข lot จาก `buildLotNo` ในงวดที่นับ); ไม่มี lot เดิมถูกปรับขึ้น | 🔴 |

**คำแนะนำสำหรับ tester:** ถือว่า `tx-08-physical-stocktake.md` เป็นความปรารถนาในการออกแบบ ไม่ใช่ spec ของพฤติกรรมปัจจุบัน Assertion ใน test scenario ควรเขียนตามค่า `enum_physical_count_status` จริงและกลไก rollup ที่ยืนยันแล้วข้างต้น (SI/SO ชนิด EOP บวกการ post เข้า ledger) ไม่ใช่ตามภาษา `FINALIZED`/GL posting/location-lock

## 6. กฎข้ามโมดูล

Rule ID ใช้รูปแบบ `PHC_XMOD_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_XMOD_001` | **→ [inventory-adjustment](/th/inventory/inventory-adjustment)**: rollup ตอน Submit เขียนตรงเข้าตาราง `tb_stock_in`/`tb_stock_out` ของโมดูลนั้น (ชนิด `eop_in` / `eop_out`) โดยข้ามเส้นทาง Save/Commit แต่ post ผ่าน helper ของ ledger ตัวเดียวกัน — ดู § 5 ข้างต้น |
| `PHC_XMOD_002` | **→ [inventory](/th/inventory/inventory)**: rollup post เข้า ledger เอง (`PHC_POST_003`): on-hand ที่ location ของการนับเปลี่ยนตาม variance โดย stamp เข้างวดที่นับ; on-hand ที่ใช้คำนวณ variance ถูกอ่านจาก cost layer ชุดเดียวกัน (`PHC_CALC_002`) จากนั้นการปิดงวด (`closeCurrent`) ยกยอดที่แก้ไขแล้วไปข้างหน้า |
| `PHC_XMOD_003` | **→ [system-config/period](/th/inventory/system-config/period)**: `period-end.validate.ts`'s `validatePhysicalCount` บล็อกการปิดงวดจนกว่าทุกสถานที่ที่จำเป็น (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`) จะมี `tb_physical_count` ที่ `completed` ภายใต้ period ที่กำลังปิด นี่คือ gate ข้ามโมดูลจริงที่ยืนยันแล้วเพียงหนึ่งเดียวที่โมดูลนี้มีส่วนร่วม |
| `PHC_XMOD_004` | **→ [spot-check](/th/inventory/spot-check)**: โมดูลและต้นไม้เอกสารแยกสำหรับการนับบางส่วนที่แคบกว่า; ไม่ใช่ child ของ `tb_physical_count_period` และไม่ได้เชื่อมโยงกันใน schema แต่อย่างใด |

## 7. แหล่งอ้างอิง

- **Primary:** `../carmen-turborepo-backend/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (create/refresh/save/reviewItems/submit/delete/update), `.../physical-count-period/physical-count-period.service.ts` (findCurrent/create/update), `.../location-on-hand.helper.ts` (`getLocationOnHand`), `.../posted-cost.helper.ts` (`getPostedCost`), `.../period-end/period-end.validate.ts` (`validatePhysicalCount`)
- **Secondary (วางแผน ยังไม่ implement):** `../carmen-frontend-e2e/docs/persona-doc/System Process/tx-08-physical-stocktake.md`
- **Frontend:** `../carmen-frontend/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`, `entry-item-row.tsx`); `constant/permissions.ts`
- **E2E:** `../carmen-frontend-e2e/tests/` — ไม่มี spec `750-physical-count` โดยเฉพาะ แต่การนับถูก exercise ผ่านหน้าจอจริงโดย spec period-close แบบ opt-in `921-period-close-count.spec.ts` และ `922-period-close-verify.spec.ts` (TC-PE-51xxxx / 52xxxx: นับทุก location, เอกสารชดเชย EOP-IN / EOP-OUT ลงวันที่วันสุดท้ายของงวด, ต้นทุนเทียบกับ `si.cost-from` ของ BU, system quantity = ยอด ณ สิ้นงวดที่นับ); รันด้วย `bun run test:period-close` (ดู [inventory/period-end](/th/inventory/inventory/period-end) § 8); manual catalog `docs/test-cases/750-physical-count.md` (41 case, ตรวจทานซ้ำเมื่อ 2026-09-20); gap catalog ของ period-end `docs/test-cases/gaps/900-period-end-gap.md` (TC-PE-31xxxx) ครอบคลุมการ unlock ปุ่ม Start
- ชุดกฎที่เกี่ยวข้อง: [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) (ตารางที่ rollup เขียนลง), [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) (ความหมายของ ledger — rollup post เข้าไปที่นั่น), [system-config/period](/th/inventory/system-config/period) (gate ข้ามโมดูลจริง, `PHC_XMOD_003`)
