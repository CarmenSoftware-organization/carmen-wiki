---
title: การนับสต๊อกประจำงวด (Physical Count) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ post และกฎข้ามโมดูลของการนับสต๊อกประจำงวด
published: true
date: 2026-07-15T17:56:09.000Z
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

หน้านี้รวบรวมกฎการดำเนินงานที่บังคับใช้จริงโดย **โมดูล physical-count** — ต้นไม้เอกสารสามระดับ (`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`) และ flow ตระกูลหน้าจอเดียว (list → entry → review → submit) ที่อธิบายใน [physical-count/03-user-flow](/th/inventory/physical-count/03-user-flow) ทุกกฎด้านล่างถูกตรวจสอบเทียบกับ `physical-count.service.ts`, `physical-count-period.service.ts`, `period-end.validate.ts` และ component frontend ใน `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/`; กฎที่ปรากฏใน draft ก่อนหน้าของหน้านี้โดยไม่มีโค้ดรองรับ (recount, tolerance threshold, location transaction-lock, การ post GL, surface ของ Approver/Auditor/Sysadmin แยก) ถูกลบออกแทนที่จะเก็บไว้เป็น scaffolding ที่ยังไม่ยืนยัน เพราะการค้นทั่ว repo ไม่พบโค้ดรองรับใด ๆ เลย Rule ID ใช้ `PHC_VAL_*` (validation), `PHC_CALC_*` (calculation), `PHC_AUTH_*` (authorization), `PHC_POST_*` (posting), `PHC_XMOD_*` (cross-module)

มีข้อสังเกตเชิงโครงสร้างสองข้อที่ผลต่อทุกกฎด้านล่าง **ข้อแรก** variance rollup ตอน Submit สุดท้ายเขียนตรงเข้า `tb_stock_in`/`tb_stock_out` (ตารางที่ [inventory-adjustment](/th/inventory/inventory-adjustment) ก็ใช้เช่นกัน) แต่ข้าม service layer ของโมดูลนั้นไปเลย — ไม่มี row `tb_inventory_transaction`, ไม่มี reason code, และไม่มีฟิลด์เชื่อมโยงถูกสร้าง (ดู [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) § 1/§ 3) **ข้อที่สอง** ไม่มี source ใน carmen/docs สำหรับกฎ `PHC_*` § 5.1 ด้านล่างเปรียบเทียบโค้ดจริงกับเอกสารวางแผนสองฉบับจาก E2E repo ที่อธิบายการออกแบบที่ต่างออกไปอย่างมากและยังไม่ถูกสร้างจริง

## 2. กฎ Validation

Rule ID ใช้รูปแบบ `PHC_VAL_NNN`

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `PHC_VAL_001` | `tb_physical_count_period.status` ต้องเป็น `counting` อยู่แล้วสำหรับ period เป้าหมาย | สร้างเอกสาร count (`POST /physical-counts`) | Reject ด้วย `"Physical Count Period is not in counting status"` ไม่พบ code path ที่ยืนยันแล้วซึ่งเปลี่ยน period จาก `draft` เป็น `counting` — ดู [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) § 2 |
| `PHC_VAL_002` | `location_id` ต้องอ้างอิง `tb_location` ที่มีอยู่จริงและไม่ถูกลบ | สร้างเอกสาร count | Reject ด้วย error location-not-found `create()` **ไม่** ตรวจสอบ `location_type` หรือ `is_active`/`physical_count_type` เป็นอิสระ — หน้ารายการเสนอเฉพาะสถานที่ที่ถูกกรองแล้วโดย `findCurrent()` (`location_type ∈ {inventory, consignment}`, `is_active = true`, และ — ถ้าไม่ได้เช็ค "include not-counted" — `physical_count_type = yes`) ดังนั้นข้อจำกัดประเภทสถานที่จึงบังคับโดยสิ่งที่ UI แสดง ไม่ใช่โดย create endpoint เอง |
| `PHC_VAL_003` | ถ้า `tb_physical_count` มีอยู่แล้วสำหรับ `(period, location)` `create()` จะไม่สร้างซ้ำ — มันรัน product union ใหม่และเพิ่มบรรทัดที่เข้าเงื่อนไขใหม่เข้าเอกสารที่มีอยู่ แล้วคืน `id`/`doc_version` ของเอกสารนั้น | สร้างเอกสาร count (path idempotent) | ไม่มี error; ทำหน้าที่เป็น "resume/refresh" โดยปริยาย ไม่ใช่ conflict |
| `PHC_VAL_004` | ทุกบรรทัด `tb_physical_count_detail` ต้องมี `counted_at != null` ก่อนเอกสารจะ submit ได้ | Submit (`PATCH .../submit`) | Reject ด้วย `"<N> products have not been counted yet"` มีเพียง call **Save** (`PATCH .../save`) เท่านั้นที่ stamp `counted_at` — **Submit for Review** (`PATCH .../review`) ไม่ทำ ดู [physical-count](/th/inventory/physical-count) § 3 |
| `PHC_VAL_005` | `actual_qty` ถูก parse ที่ client ด้วย `Math.max(0, Number.parseFloat(raw) || 0)` (`entry-item-row.tsx`) — input ที่ติดลบถูก clamp เป็น `0` ก่อนถึง API เลย ไม่พบการตรวจสอบขั้นต่ำฝั่ง server ที่ตรงกันใน `physical-count.service.ts` | ป้อนบรรทัด (client-side เท่านั้น) | Input ที่ไม่ใช่ตัวเลขหรือติดลบถูก clamp เป็นตัวเลขที่ถูกต้องเงียบ ๆ ใน UI ยังไม่ยืนยันว่าถูกบังคับใช้อิสระโดย backend |
| `PHC_VAL_006` | `tb_physical_count.status === completed` บล็อก **Save**, **Submit for Review**, และ **Submit** (`"Physical Count is already completed"`) และบล็อก **Delete** (`"Cannot delete completed Physical Count"`) | Save / Review / Submit / Delete | Reject ด้วยข้อความที่ยกมา ไม่มี guard ที่เทียบเท่าบน **Update** (`PATCH .../physical-counts/:id`, การแก้ไข `description` เท่านั้นแบบ legacy) — มันยอมรับการเปลี่ยน description บนเอกสาร `completed` ถ้าถูกเรียกโดยตรง แม้ route นี้จะเข้าถึงไม่ได้จาก flow navigation จริง (ดู [physical-count](/th/inventory/physical-count) § 1) |
| `PHC_VAL_007` | ทุก call `save`/`update`/`review`/`submit` ต้องส่ง `doc_version` ปัจจุบัน; ค่าไม่ตรงกับที่เก็บไว้จะถูกแปลงโดย decorator `@TryCatch` ที่ใช้ร่วมกันเป็นผล `ALREADY_EXISTS` แบบ `409` | Save / Update / Review / Submit | Reject เมื่อ `doc_version` ไม่ตรง; เพิ่มขึ้นเมื่อสำเร็จ ดู [system-config/doc-version](/th/inventory/system-config/doc-version) |

> **ไม่พบในโค้ด (ถูกลบออกจาก catalogue นี้):** การตรวจสอบ tolerance-threshold แบบเปอร์เซ็นต์หรือปริมาณสัมบูรณ์ที่ขับเคลื่อนสถานะ "flag for recount"; action recount แยกที่ทำโดย "counter คนละคน"; location-level transaction lock ที่บล็อกการ post GRN/SR/อื่น ๆ ระหว่างที่การนับ `in_progress`; toggle "blind count" ที่ซ่อน book quantity จาก counter (หน้า entry เพียงแค่ไม่ render `on_hand_qty` ให้ counter เห็นเลย โดยการออกแบบของหน้า ไม่ใช่ toggle ที่ตั้งค่าได้)

## 3. กฎการคำนวณ

Rule ID ใช้รูปแบบ `PHC_CALC_NNN` ฟิลด์ปริมาณเป็น `Decimal(20, 5)` บน `tb_physical_count_detail.on_hand_qty` / `actual_qty` / `diff_qty`

| Rule ID | สูตร |
| ------- | ------- |
| `PHC_CALC_001` (variance qty) | `diff_qty = actual_qty − on_hand_qty` ต่อบรรทัด คำนวณฝั่ง server ทั้งโดย `save()` (เทียบกับ `on_hand_qty` ที่เก็บอยู่ในขณะนั้น) และโดย `reviewItems()` (เทียบกับ `on_hand_qty` ที่คำนวณสดใหม่) |
| `PHC_CALC_002` (การคำนวณ on-hand ใหม่) | `reviewItems()` คำนวณ `on_hand_qty` ของ **ทุก** บรรทัดเป็น `Σ tb_inventory_transaction_detail.qty` ที่ `location_id` ของการนับ จัดกลุ่มตาม `product_id` โดย **ไม่มี date cut-off** — เป็นยอดคงเหลือ ledger ปัจจุบัน ณ ตอนกด "Submit for Review" ไม่ใช่ค่าที่ frozen ตอนสร้าง sheet |
| `PHC_CALC_003` (progress) | `product_counted` ถูกคำนวณใหม่ทุกครั้งที่เรียก `save()`/`reviewItems()` เป็นจำนวนบรรทัดที่มี `actual_qty` ที่ effective ไม่เป็น null/ไม่เป็นศูนย์; `product_total` คือจำนวนบรรทัดบน sheet (ตั้งตอน create/refresh) ตัวเลขเปอร์เซ็นต์ความคืบหน้าบนหน้า entry คือ `Math.round(counted / total × 100)` คำนวณฝั่ง client จากตัวเลขเดียวกัน |
| `PHC_CALC_004` (ต้นทุน rollup) | ที่ `submit()` สุดท้าย `cost_per_unit` ของแต่ละบรรทัด variance ถูก lookup ครั้งเดียวต่อ submit ผ่าน `CostingService.getCostsPerUnit()` โดยใช้วิธีเดียวระดับ business-unit ที่ resolve จาก `enum_business_unit_config_key.physical_count_costing_method` (default `last_receiving` ถ้าไม่ตั้งค่า/ไม่ถูกต้อง); `total_cost = cost_per_unit × |diff_qty|` ทุกบรรทัดใน submit เดียวกันใช้วิธีเดียวกัน — ไม่มี override ต่อบรรทัดหรือต่อการนับ |

## 4. กฎ Authorization

Rule ID ใช้รูปแบบ `PHC_AUTH_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_AUTH_001` | ทุก action ของ list, create, save, review, submit, refresh, delete และ comment ในโมดูลนี้ถูก gate ด้วย permission key CRUD เดียว: `inventory_management.physical_count` (`constant/permissions.ts`) ไม่พบ permission variant แยกสำหรับ create-only, approve-only หรือ read-only สำหรับโมดูลนี้ |
| `PHC_AUTH_002` | ไม่พบข้อจำกัดแบบ zone, location-scoped-to-user หรือ "assigned counter" ใน `physical-count.service.ts` — ผู้ใช้ใดก็ตามที่ถือ permission ของโมดูลสามารถเปิด ป้อน และ submit เอกสาร count ใดก็ได้ ตาราง `tb_user_location` ทั่วไปมีอยู่ใน schema สำหรับ location-level access grant ที่อื่นในผลิตภัณฑ์ แต่ไม่พบการอ้างอิงถึงมันในโค้ด service ของโมดูลนี้เอง ให้ถือว่า claim "counter ถูกจำกัดขอบเขตเฉพาะสถานที่ที่ได้รับมอบหมาย" ยังไม่ยืนยันสำหรับโมดูลนี้โดยเฉพาะ |
| `PHC_AUTH_003` | ไม่มี permission, route หรือ workflow stage ของ Approver/Finance Reviewer, Auditor หรือ Sysadmin สำหรับโมดูลนี้ — ขั้นตอน "review" และ "submit" สุดท้ายทั้งคู่ทำโดยผู้ใช้ permission-gated คนเดียวกันที่ทำการนับ ในเซสชันเดียวกัน |

## 5. กฎการ Posting

Rule ID ใช้รูปแบบ `PHC_POST_NNN` "Posting" ในโมดูลนี้หมายถึง variance-rollup transaction ที่ยิงภายใน `submit()`

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_POST_001` | ที่ `submit()`, service แบ่งบรรทัด detail ที่ `diff_qty ≠ 0` ตามเครื่องหมาย: ทุกบรรทัด variance บวกเข้า `tb_stock_in` ใหม่ **หนึ่งฉบับ**; ทุกบรรทัด variance ลบเข้า `tb_stock_out` ใหม่ **หนึ่งฉบับ** บรรทัดที่ `diff_qty = 0` ไม่สร้าง rollup row ทั้งสอง header ที่สร้างขึ้นถูก insert ด้วย `doc_status: enum_doc_status.completed` โดยตรง — ไม่มี draft หรือ approval stage สะท้อน pattern "create() post completed แบบไม่มีเงื่อนไข" เดียวกับที่ยืนยันแล้วในหน้าจอ Stock In/Out ของโมดูล inventory-adjustment เอง |
| `PHC_POST_002` | ทั้งฟิลด์ `info` JSON ของ header ที่สร้างขึ้นและของบรรทัด detail ใด ๆ ไม่ถูกใส่ค่า — **ไม่มี** การเชื่อมโยงแบบ structured (ไม่มี `info.countId`, ไม่มี reason code บน `adjustment_type_id` ซึ่งถูกปล่อยเป็น `null`) กลับไปยัง `tb_physical_count` ต้นทาง มีเพียงข้อความ `description`/`note` แบบ human-readable ที่ใช้ร่วมกัน ซึ่งบรรจุช่วงวันที่ของ period |
| `PHC_POST_003` | `submit()` **ไม่** เรียก `InventoryTransactionService.executeAdjustmentIn`/`executeAdjustmentOut` — ไม่มี row `tb_inventory_transaction` ถูกเขียนโดย action นี้ เอกสาร `tb_stock_in`/`tb_stock_out` ของ rollup มีอยู่เพียงเป็นบันทึกเท่านั้น มันไม่ได้เคลื่อนย้าย on-hand balance ด้วยตัวเองแบบที่ Stock In/Out create ปกติ (ใน [inventory-adjustment](/th/inventory/inventory-adjustment)) ทำ |
| `PHC_POST_004` | เมื่อ `submit()` สำเร็จ `tb_physical_count.status` จะเป็น `completed` และ `completed_at`/`completed_by_id` ถูก stamp; เอกสารจะถูก reject โดย completed-guard ของตัวมันเอง (`save()`/`reviewItems()`/`submit()`, `PHC_VAL_006`) — การแก้ไขใด ๆ ในภายหลังต้องสร้าง adjustment ใหม่ที่เป็นอิสระผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) ไม่ใช่การเปิด count ใหม่ |

## 5.1 ความแตกต่างระหว่าง Live Code กับเอกสารวางแผน

ไม่มี catalogue ของกฎ `PHC-*` ใน carmen/docs สำหรับโมดูลนี้ อ้างอิงที่ใกล้ที่สุดที่มีคือเอกสารระดับวางแผนใน E2E repo, `docs/persona-doc/System Process/tx-08-physical-stocktake.md` (เวอร์ชัน 1.1.1, 2026-04-27) — เอกสารออกแบบสไตล์ BRD **ไม่ใช่** test อัตโนมัติหรือพฤติกรรมที่ยืนยันว่า ship แล้ว การอ่าน implementation ปัจจุบันโดยตรงแสดงว่ามันต่างจากเอกสารนั้นในเกือบทุกจุดสำคัญ:

> Diff legend: 🔵 เอกสารวางแผนเท่านั้น (ไม่มีโค้ดรองรับ) · 🔴 live code ต่างจากคำอธิบายในเอกสารวางแผน

| หัวข้อ | เอกสารวางแผน (`tx-08-physical-stocktake.md`) | Live code | Diff |
|---|---|---|---|
| ประเภท transaction | "Post เป็น **Physical Stocktake transaction type ของตัวเอง** — **ไม่ใช่** Stock In/Out adjustment" | `submit()` สร้าง row `tb_stock_in`/`tb_stock_out` จริง ๆ — กลไกเดียวกับที่เอกสารวางแผนบอกว่ามันไม่ใช่ ไม่มี physical-count transaction type แยกบน `enum_transaction_type` | 🔴 |
| ผลกระทบต่อ ledger | Variance "เปลี่ยน QOH", "ปรับ lot", trigger "Cost Calculation" (AVCO re-average / เพิ่ม layer FIFO) | ไม่มีสิ่งเหล่านี้เกิดขึ้น: `submit()` ไม่เคยเรียก service ของ inventory-transaction/cost-layer เลย จึงไม่เกิดผลกระทบใด ๆ ต่อ `tb_inventory_transaction`, lot หรือ cost-layer จาก action นี้ (`PHC_POST_003`) | 🔴 |
| วงจรชีวิตสถานะ | สามสถานะ: `IN PROGRESS → COMPLETED → FINALIZED` โดย `FINALIZED` หมายถึง "variance adjustment ถูก post ไปยัง GL" และจำเป็นสำหรับ End Period Close Stage 3 | `enum_physical_count_status` มีสามค่า (`pending`, `in_progress`, `completed`) แต่ไม่มีค่า `finalized` และไม่มีขั้นตอน post GL ใด ๆ ในโค้ดทั้งหมด `completed` เป็นสถานะปลายทาง Gate การปิดงวดจริง (`period-end.validate.ts`'s `validatePhysicalCount`) ตรวจสอบเพียง `status = completed` ที่แต่ละสถานที่จำเป็น — ไม่มี milestone GL-posted แยกที่ต้องผ่าน | 🔴 |
| Transaction lock | "Transaction ที่สถานที่ถูกล็อกขณะ Physical Count เป็น IN PROGRESS" — GRN, CRN, SR, Issues, Sales, Stock In/Out adj ทั้งหมดถูกบล็อก | ไม่พบ guard ที่ตรงกันในทั้ง service ของ GRN, SR หรือ stock-in/out — การค้นแบบตรงเป้าหมายสำหรับการตรวจสอบ physical-count ใน module เหล่านั้นให้ผล 0 hits | 🔵 |
| Tolerance / recount | บอกเป็นนัยโดย draft ก่อนหน้าของหน้าวิกินี้ ไม่ได้ปรากฏจริงใน `tx-08` | ไม่มี tolerance percentage, absolute-quantity threshold หรือ recount flow ใด ๆ ในทั้ง frontend หรือ backend สำหรับโมดูลนี้ | 🔵 |
| การจัดการ lot ของ variance บวก | "New lot created (or existing lot adjusted up — TBC)" | ไม่มีนัยสำคัญ — ไม่มี lot ถูกสร้างหรือปรับโดย rollup ของโมดูลนี้ เนื่องจาก code path ของ inventory-transaction/lot ไม่เคยถูกเข้าถึงเลย | 🔴 |

**คำแนะนำสำหรับ tester:** ถือว่า `tx-08-physical-stocktake.md` เป็นความปรารถนาในการออกแบบ ไม่ใช่ spec ของพฤติกรรมปัจจุบัน Assertion ใน test scenario ควรเขียนตามค่า `enum_physical_count_status` จริงและกลไก rollup ที่ยืนยันแล้วข้างต้น ไม่ใช่ตามภาษา `FINALIZED`/GL posting/location-lock

## 6. กฎข้ามโมดูล

Rule ID ใช้รูปแบบ `PHC_XMOD_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_XMOD_001` | **→ [inventory-adjustment](/th/inventory/inventory-adjustment)**: rollup ตอน Submit เขียนตรงเข้าตาราง `tb_stock_in`/`tb_stock_out` ของโมดูลนั้น แต่ข้าม service layer ของมัน — ดู § 5 ข้างต้น |
| `PHC_XMOD_002` | **→ [inventory](/th/inventory/inventory)**: ไม่มีผลกระทบต่อ ledger เกิดจาก rollup ของโมดูลนี้เอง (`PHC_POST_003`); ผลกระทบต่อ ledger ใด ๆ จาก row stock-in/out ที่ได้จะต้องอาศัย process แยกที่ repo นี้ไม่มี |
| `PHC_XMOD_003` | **→ [system-config/period](/th/inventory/system-config/period)**: `period-end.validate.ts`'s `validatePhysicalCount` บล็อกการปิดงวดจนกว่าทุกสถานที่ที่จำเป็น (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`) จะมี `tb_physical_count` ที่ `completed` ภายใต้ period ที่กำลังปิด นี่คือ gate ข้ามโมดูลจริงที่ยืนยันแล้วเพียงหนึ่งเดียวที่โมดูลนี้มีส่วนร่วม |
| `PHC_XMOD_004` | **→ [spot-check](/th/inventory/spot-check)**: โมดูลและต้นไม้เอกสารแยกสำหรับการนับบางส่วนที่แคบกว่า; ไม่ใช่ child ของ `tb_physical_count_period` และไม่ได้เชื่อมโยงกันใน schema แต่อย่างใด |

## 7. แหล่งอ้างอิง

- **Primary:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (create/refresh/save/reviewItems/submit/delete/update), `.../physical-count-period/physical-count-period.service.ts` (findCurrent/create/update), `.../period-end/period-end.validate.ts` (`validatePhysicalCount`)
- **Secondary (วางแผน ยังไม่ implement):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-08-physical-stocktake.md`
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`, `entry-item-row.tsx`); `constant/permissions.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ชุดกฎที่เกี่ยวข้อง: [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) (ตารางที่ rollup เขียนเข้า), [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) (semantics ของ ledger — ไม่ถูกแตะโดย rollup ของโมดูลนี้), [system-config/period](/th/inventory/system-config/period) (gate ข้ามโมดูลจริง, `PHC_XMOD_003`)
