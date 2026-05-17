---
title: การนับสต๊อกประจำงวด (Physical Count) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ post และกฎข้ามโมดูลของการนับสต๊อกประจำงวด
published: true
date: 2026-05-17T12:00:00.000Z
tags: physical-count, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `PHC_VAL_*` validation &nbsp;·&nbsp; `PHC_AUTH_*` permission &nbsp;·&nbsp; `PHC_CALC_*` calc &nbsp;·&nbsp; `PHC_POST_*` posting &nbsp;·&nbsp; `PHC_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 28 กฎ
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** หัวข้อ 5.1 (ถ้ามี) มี callout ความแตกต่างระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้รวบรวมกฎการดำเนินงานที่กำกับ **โมดูล physical-count** — ต้นไม้เอกสารสามระดับ (`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`) ที่บันทึกการนับ end-to-end ทุกรายการที่สถานที่หนึ่งตามรอบกำหนด กฎด้านล่างนี้อยู่ **เหนือ** [[inventory-adjustment/02-business-rules]] (variance rollup post ที่นั่น) และ **เหนือ** กฎระดับ ledger ใน [[inventory/02-business-rules]] (ผลกระทบขั้นสุดท้ายต่อ inventory ลงจอดที่นั่น) — กฎเหล่านี้กำกับวงจรชีวิตของ period และเอกสาร (`pending → in_progress → completed`), การเลือกโหมด frozen vs live (`enum_physical_count_type`), การมอบหมาย counter และวินัย zone, การ escalate ไป recount เมื่อ variance ทะลุ tolerance, การเลือกวิธีตีมูลค่า ณ เวลา variance rollup (`enum_physical_count_costing_method`) และจุดเชื่อมต่อข้ามโมดูลเข้า [[inventory-adjustment]] / [[inventory]] / [[costing]] Rule ID ใช้ `PHC_VAL_*` (validation), `PHC_CALC_*` (calculation), `PHC_AUTH_*` (authorization), `PHC_POST_*` (posting), `PHC_XMOD_*` (cross-module)

มีข้อสังเกตเชิงโครงสร้างสองข้อจาก [[physical-count/01-data-model]] ที่ผลต่อทุกกฎด้านล่าง: **ข้อแรก** ตารางของ physical-count **ไม่** เขียนลง inventory ledger โดยตรง — variance rollup เขียน `tb_stock_in` (overage) และ/หรือ `tb_stock_out` (shortage) ไปยัง [[inventory-adjustment]] และการ post adjustment คือสิ่งที่เขียน `tb_inventory_transaction` ดังนั้นกฎ PHC จึงกำกับวงจรชีวิตของเอกสารและการคำนวณ variance ความหมายของ ledger สืบทอดจาก `INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` **ข้อที่สอง** ปัจจุบันยังไม่มี source ใน carmen/docs สำหรับกฎ `PHC_*` — rule ID ด้านล่างเป็น scaffolding ที่เสนอเพื่อยืนยันเมื่อ catalogue ใน carmen/docs ถูกเขียน

## 2. กฎ Validation

Rule ID ใช้รูปแบบ `PHC_VAL_NNN` Validation ทำงานที่สามขอบเขต: **ตอนสร้างเอกสาร count** (สร้าง sheet), **ตอนป้อนบรรทัด** (counter พิมพ์ `actual_qty`) และ **ตอน submit** (`in_progress → completed`)

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `PHC_VAL_001` | row `tb_physical_count_period` มีอยู่ในสถานะ `counting` สำหรับงวดบัญชีเป้าหมายก่อนจะสร้าง `tb_physical_count` ใด ๆ ภายใต้นั้น Period ต้องเปิดตาม [[inventory]] `INV_VAL_008` | สร้างเอกสาร count | Reject ถ้าไม่มี period header หรือ period เป็น `completed` |
| `PHC_VAL_002` | `tb_physical_count.physical_count_type` ตั้งค่า (`yes` สำหรับ frozen, `no` สำหรับ live) ตอนสร้าง sheet; โหมดที่เลือกเปลี่ยนไม่ได้เมื่อ `status = in_progress` | สร้าง / แก้ไขเอกสาร count | Reject การเปลี่ยนโหมดบนการนับที่เริ่มแล้ว |
| `PHC_VAL_003` | `location_id` อ้างอิงสถานที่ประเภท inventory หรือ consignment ที่ active ตาม [[inventory]] `INV_VAL_009` สถานที่ direct-cost นับ physical ไม่ได้ | สร้างเอกสาร count | Reject ด้วย `"Direct-cost locations cannot be physically counted."` |
| `PHC_VAL_004` | ทุก `tb_physical_count_detail` บรรทัดมี `actual_qty` ไม่เป็น null ก่อนเอกสารจะ submit ได้ (`product_counted == product_total`) | Submit | Reject ด้วย `"Cannot submit count — <N> of <M> lines remain uncounted."` |
| `PHC_VAL_005` | `actual_qty ≥ 0` บนทุก detail การนับ physical ติดลบไม่มีความหมาย | ป้อนบรรทัด | Reject ด้วย `"Counted quantity must be zero or positive."` |
| `PHC_VAL_006` | เมื่อ `physical_count_type = yes` (frozen), การเขียน `tb_inventory_transaction` ที่ `(period, location)` ไม่รับระหว่าง `status = in_progress` ถึง `status = completed` Frontend pre-check บนหน้าจอ post GRN / SR / adjustment | เมื่อพยายามเขียน inventory ระหว่างช่วงการนับ | Reject การ submit ด้วย `"Location is locked for physical count — wait for count completion or use the live-count mode."` |
| `PHC_VAL_007` | บรรทัดที่ `|diff_qty| / on_hand_qty` เกิน tolerance threshold ของ tenant (ทั่วไป 5% หรือสัมบูรณ์ 1 หน่วย แล้วแต่ค่าใดสูงกว่า) ถูก flag ให้ recount; เอกสาร submit ไม่ได้จนกว่าบรรทัดจะถูก recount-and-reconcile หรือถูกระบุชัดเจนว่า "accept variance" โดย Inventory Controller | Submit | บล็อก submit จนกว่าบรรทัดที่ flag จะถูกแก้ไข |
| `PHC_VAL_008` | `tb_physical_count` ที่ completed แล้วเปิดใหม่ไม่ได้ — การแก้ไขต้องใช้ period ใหม่หรือ `tb_stock_in` / `tb_stock_out` adjustment แบบ manual เทียบกับสถานที่เดียวกันตาม `PHC_POST_004` | แก้ไข completed | Reject ด้วย `"Cannot edit a completed count. Raise a manual inventory adjustment."` |

> **TODO:** ยืนยันสูตร tolerance threshold และค่า default ที่แน่นอนจาก tenant config เมื่อ catalogue carmen/docs ถูกเขียน Cross-reference กับ E2E spec สำหรับ flow recount เมื่อมี

## 3. กฎการคำนวณ

Rule ID ใช้รูปแบบ `PHC_CALC_NNN` ทุกฟิลด์ปริมาณเป็น `Decimal(20, 5)` ตาม `tb_physical_count_detail.on_hand_qty` / `actual_qty` / `diff_qty`

| Rule ID | สูตร |
| ------- | ------- |
| `PHC_CALC_001` (variance qty) | `diff_qty = actual_qty - on_hand_qty` ต่อบรรทัด บวก = overage (write-on); ลบ = shortage (write-off) เก็บใน `tb_physical_count_detail.diff_qty` |
| `PHC_CALC_002` (variance %) | `variance_% = (diff_qty / on_hand_qty) × 100` เมื่อ `on_hand_qty > 0`; เมื่อ `on_hand_qty = 0` และ `actual_qty > 0` ให้ถือเป็น new-discovery (100% บวก) ขับเคลื่อนการ flag tolerance-breach ตาม `PHC_VAL_007` ไม่ persist; derive ตอนอ่าน |
| `PHC_CALC_003` (variance value) | `variance_value = diff_qty × cost_per_unit` โดย `cost_per_unit` เลือกตาม `enum_physical_count_costing_method` ของ tenant: `standard` (product master), `last` (ต้นทุนรับล่าสุด), `average` (weighted average ปัจจุบัน), `last_receiving` (alias ของ last) |
| `PHC_CALC_004` (progress) | `progress_% = product_counted / product_total × 100` ที่ระดับเอกสาร; ตัวนับอัปเดตอัตโนมัติเมื่อ `actual_qty` ของแต่ละ detail ถูกบันทึก |

> **TODO:** ยืนยันลำดับความสำคัญของค่า `enum_physical_count_costing_method` กับ logic frontend เมื่อ path ของ carmen-inventory-frontend ถูกเขียน Cross-link ไป [[costing]] สำหรับพฤติกรรมการตีมูลค่า WA / FIFO

## 4. กฎ Authorization

Rule ID ใช้รูปแบบ `PHC_AUTH_NNN` Persona ตาม [[physical-count]] § 4 และการจัดกลุ่มสามกลุ่มในหน้าย่อยของโมดูลนี้ (count-lead / counter / audit-config)

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_AUTH_001` | **Count Lead** (Inventory Controller / Manager) สร้างและจัดตารางเอกสาร `tb_physical_count_period` และ `tb_physical_count` มอบหมาย counter ตั้งค่าโหมด (frozen vs live) และอนุมัติผล recount หนึ่งที่นั่งต่อ period ตามนโยบาย tenant |
| `PHC_AUTH_002` | **Counter** (Store Keeper / Counter) ป้อน `actual_qty` บนบรรทัด `tb_physical_count_detail` ที่ได้รับมอบหมายภายใน zone ของตน flag รายการเสียหาย / ไม่มีป้ายผ่าน `tb_physical_count_detail_comment` แต่ submit เอกสารไม่ได้ — เฉพาะ Count Lead เท่านั้นที่ submit ได้ |
| `PHC_AUTH_003` | กลุ่ม **Audit / Config**: Approver / Finance review variance-rollup adjustment (action ลงจอดบน [[inventory-adjustment]] ไม่ใช่ที่นี่); Auditor มีสิทธิ์อ่านอย่างเดียวต่อทั้งสามระดับ (period / document / detail) รวมถึง comment thread และ stamp counted-by; Sysadmin ตั้งค่า tolerance threshold และ default costing-method |
| `PHC_AUTH_004` | การมอบหมาย counter ผูกกับขอบเขต — counter เห็นเฉพาะบรรทัดที่ `(location, zone)` อยู่ใน `tb_user_location` / zone-grant ที่เทียบเท่า การมองเห็นข้าม zone ต้องใช้ role Count Lead |

## 5. กฎการ Posting

Rule ID ใช้รูปแบบ `PHC_POST_NNN` Posting ในโมดูลนี้หมายถึง variance-rollup transition (count-completion → การสร้าง adjustment) ไม่ใช่การเขียน ledger โดยตรง

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_POST_001` | เมื่อ `tb_physical_count.status = completed`, ชั้น application iterate `tb_physical_count_detail` และจัดกลุ่มบรรทัดด้วย `sign(diff_qty)`: บวก → `tb_stock_in` หนึ่งบรรทัดขึ้นไปภายใต้ reason `COUNT_OVERAGE`; ลบ → `tb_stock_out` หนึ่งบรรทัดขึ้นไปภายใต้ reason `COUNT_SHORTAGE`; ศูนย์ → ไม่มี rollup |
| `PHC_POST_002` | Header ของ rollup adjustment พกพา `info.countId = <tb_physical_count.id>` และ `info.countPeriodId = <tb_physical_count_period.id>` สำหรับ join ฝั่ง audit ย้อนกลับไปยังแหล่งที่มาของ count Reason-code บน `tb_adjustment_type` ต้องมีอยู่พร้อมทิศทางที่เหมาะสม (ตาม [[inventory-adjustment/01-data-model]] § 2.1) |
| `PHC_POST_003` | cost-per-unit บนแต่ละบรรทัด rollup ตั้งตาม `PHC_CALC_003` (`enum_physical_count_costing_method` ที่เลือก) การลงนามรับรองของ Count Lead ในการ submit adjustment ตอบสนอง [[inventory-adjustment/02-business-rules]] approval ตาม rollup-fast-path (อำนาจ counter pre-approved ที่จุด submit ของ count) |
| `PHC_POST_004` | เมื่อ rollup adjustment เป็น `completed` แล้ว เอกสาร count จะ **immutable** — การแก้ไขใด ๆ ในภายหลังที่สถานที่เดียวกันต้องใช้ `tb_stock_in` / `tb_stock_out` ใหม่ที่สร้างเอง ไม่ใช่การเปิด count ใหม่ |

### 5.1 วงจรชีวิตสถานะ — Live UI vs BRD Mapping

มี enum สองชั้นกำกับสถานะของ physical-count `enum_physical_count_period_status` (`draft`, `counting`, `completed`) ติดตาม header ของ period; `enum_physical_count_status` (`pending`, `in_progress`, `completed`) ติดตามเอกสาร count แต่ละฉบับ ไม่มีไฟล์อ้างอิง BRD สำหรับโมดูลนี้ใน carmen/docs — คอลัมน์ "BRD equivalent" ด้านล่างใช้ functional specification ใน `Test_case/System_Process/tx-08-physical-stocktake.md` เป็น BRD proxy ที่ใกล้ที่สุดที่มี และเมื่อ Test_case ใช้ป้ายสถานะแตกต่างกัน diff จะถูกระบุ Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27)

> Diff legend: ✅ ตรงกัน · 🔴 ใหม่ใน live UI (ไม่มีใน Test_case) · 🔵 Test_case เท่านั้น (ไม่มีค่าใน live enum)

**`enum_physical_count_status` (ระดับเอกสาร):**

| Live UI status | Test_case (`tx-08`) equivalent | Diff | Notes |
|---|---|---|---|
| `pending` | — (ไม่มีชื่อ; sheet สร้างแล้วแต่ยังไม่เริ่มนับ) | 🔴 ใหม่ใน live UI | Sheet สร้างโดย Count Lead; snapshot `on_hand_qty` จับ; counter มอบหมายแล้ว Flow ของ Test_case กระโดดตรงจาก "count created" ไป "IN PROGRESS" โดยไม่ตั้งชื่อสถานะ pre-start นี้ |
| `in_progress` | `IN PROGRESS` | ✅ ตรงกัน | Counter กำลังป้อนค่า `actual_qty` Location ถูก **ล็อก** — GRN, SR, Issues, Stock In/Out adj สำหรับ location นั้นทั้งหมดถูกบล็อกตาม `PHC_VAL_006` และ `BR-01` |
| `completed` | `COMPLETED` | ✅ ตรงกัน | ทุกบรรทัดนับ; Count Lead submit; variance บันทึก Rollup adjustment สร้างตาม `PHC_POST_001` ไม่ผ่าน End Period Close Stage 3 เพียงอย่างเดียว — `FINALIZED` (GL posted) ต้องใช้ตาม `BR-02` / `BR-PE-005` |
| — | `FINALIZED` | 🔵 Test_case เท่านั้น | Test_case เพิ่มสถานะ `FINALIZED` (GL posted ไปยัง General Ledger) ที่ต้องใช้สำหรับ End Period Close Stage 3 ตาม `BR-02` / `BR-PE-005` Prisma `enum_physical_count_status` ใน live ไม่มีค่า `finalized` — การ post GL จัดการโดย rollup adjustment (`tb_stock_in` / `tb_stock_out`) ถึง `completed` ใน [[inventory-adjustment]] ไม่ใช่โดยการเปลี่ยนสถานะของ `tb_physical_count` |

**`enum_physical_count_period_status` (ระดับ period):**

| Live UI status | Test_case (`tx-08`) equivalent | Diff | Notes |
|---|---|---|---|
| `draft` | — (วางแผน period, ไม่มีคำใน Test_case) | 🔴 ใหม่ใน live UI | Header ของ period เปิดแล้ว; ยังไม่มีเอกสาร count สร้าง Test_case ไม่ตั้งชื่อสถานะนี้ |
| `counting` | — (การดำเนินงานที่ active, ไม่มีคำใน Test_case) | 🔴 ใหม่ใน live UI | Auto-transition เมื่อเอกสาร `tb_physical_count` แรกถูกสร้าง Test_case อธิบายการดำเนินงานที่ active แต่ใช้คำ `IN PROGRESS` ระดับเอกสาร ไม่ใช่ป้ายระดับ period ที่แยกออก |
| `completed` | — (ทุก location นับเสร็จ, ไม่มีคำใน Test_case) | 🔴 ใหม่ใน live UI | ทุก row `tb_physical_count` ภายใต้ period ถึง `completed` Period ล็อกจาก count ใหม่ Test_case อธิบายสถานะนี้เชิงฟังก์ชัน (ทุก count finalized สำหรับการปิด period) แต่ไม่ใช้ป้ายระดับ period |

> ⚠️ **Discrepancy — ขาดสถานะ `FINALIZED` บน `enum_physical_count_status`:** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) กำหนด flow สามสถานะ `IN PROGRESS → COMPLETED → FINALIZED` โดย `FINALIZED` หมายถึง variance adjustment ของ count ถูก post ไปยัง General Ledger และ count ตอบสนอง End Period Close Stage 3 (ตาม `BR-02` / `BR-PE-005`) Prisma `enum_physical_count_status` ใน live มีเพียง `pending`, `in_progress`, `completed` — ไม่มีค่า `finalized` ในการ implement ที่ live, milestone การ post GL ติดตามผ่านเอกสาร rollup adjustment ใน [[inventory-adjustment]] ที่ถึง `completed` ไม่ใช่โดยการเปลี่ยนสถานะของ `tb_physical_count` เอง Tester ต้องตรวจสอบสถานะของ rollup `tb_stock_in` / `tb_stock_out` — ไม่ใช่แค่ `tb_physical_count.status` — เพื่อยืนยันว่า End Period Close Stage 3 ตอบสนองแล้ว Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27)

> ⚠️ **Discrepancy — Side-effect ของ location lock ไม่ได้สร้างแบบใน Prisma schema:** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) ระบุว่า "transactions at a location are locked while the Physical Count is IN PROGRESS" (`BR-01`): GRN, CRN, SR, Issues, Sales และ Stock In/Out adjustment สำหรับ location นั้นทั้งหมดถูกบล็อก พฤติกรรมนี้กำกับโดย `PHC_VAL_006` ในวิกินี้และบังคับใช้ที่ชั้น application (front-end pre-check บนหน้าจอ post) — ไม่ใช่ constraint ระดับ Prisma บน `tb_physical_count` เอง Tester ที่ตรวจสอบการ lock ต้องพยายาม post GRN หรือ SR เทียบกับ location ที่มี count `in_progress` และยืนยันว่าระบบ reject การพยายามด้วย error ที่คาดหวัง Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27)

> ⚠️ **Discrepancy — Chain prerequisite ของการปิด period (Stage 3 gate):** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) ระบุว่า End Period Close Stage 3 ผ่านไม่ได้จนกว่า Physical Count ทั้งหมดจะถึง `FINALIZED` (GL posted) ตาม `BR-02` / `BR-PE-005` Count ที่เป็น `COMPLETED` แต่ rollup adjustment ยังไม่ post **ไม่** เพียงพอ — จะบล็อกการปิด period Prisma schema ของ live ไม่มีค่า enum `finalized` และไม่มี FK จาก `tb_physical_count` ไปยัง rollup adjustment — logic gate ของการปิด period ต้อง query [[inventory-adjustment]] สำหรับเอกสาร rollup ที่ `info.countPeriodId = <period_id>` และยืนยันว่าทั้งหมดอยู่สถานะ `completed` นี่เป็น dependency ระดับ application ที่ไม่เห็นจาก schema ของ physical-count เพียงอย่างเดียว Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27)

> ⚠️ **Discrepancy — การจัดการ lot ของ variance บวก (TBC):** `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27) mark การสร้าง lot ของ variance บวกว่า "TBC — new lot created or existing lot adjusted up" Prisma schema และ path rollup ปัจจุบัน (`tb_stock_in` พร้อม reason `COUNT_OVERAGE`) สร้าง lot ใหม่สำหรับปริมาณ overage เสมอ path "existing lot adjusted up" ยังไม่ได้รับการยืนยัน Source: `Test_case/System_Process/tx-08-physical-stocktake.md` (capture date 2026-04-27)

## 6. กฎข้ามโมดูล

Rule ID ใช้รูปแบบ `PHC_XMOD_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `PHC_XMOD_001` | **→ [[inventory-adjustment]]**: variance ของการนับ post ผ่านต้นไม้เอกสาร `tb_stock_in` / `tb_stock_out` ด้วย reason code `COUNT_OVERAGE` / `COUNT_SHORTAGE` Rollup เป็น path เดียวจาก count ไปยัง ledger |
| `PHC_XMOD_002` | **→ [[inventory]]**: ทุก rollup adjustment เขียน `tb_inventory_transaction` ด้วย `enum_transaction_type = adjustment_in` / `adjustment_out` ไม่มีค่า `physical_count` โดยตรงบน `enum_transaction_type` |
| `PHC_XMOD_003` | **→ [[costing]]**: การเลือกวิธีตีมูลค่าบน rollup ตาม `enum_physical_count_costing_method`; การบริโภค FIFO (สำหรับ shortage) และการ refresh WA (สำหรับ overage) ตาม `INV_CALC_005` / `INV_CALC_007` เมื่อ adjustment post |
| `PHC_XMOD_004` | **→ [[spot-check]]**: spot-check เป็นการนับบางส่วนที่แคบกว่าซึ่งใช้โมเดลแนวคิดเดียวกันและจุดเชื่อมต่อ variance-rollup เดียวกันไปยัง [[inventory-adjustment]]; **ไม่ใช่** child ของ `tb_physical_count_period` |

> **TODO:** ตรวจสอบ rule ID ข้างต้นกับ catalogue `PHC-*` ใน carmen/docs เมื่อเขียน ยืนยันค่า default ของ tolerance / threshold จาก tenant config ของ production cross-validate posting fan-out กับการ implement ของ frontend ใน `../carmen-inventory-frontend/`

## 7. แหล่งอ้างอิง

- **Primary (Prisma):** ดู [[physical-count/01-data-model]] สำหรับ citation ของ entity / enum source
- **Secondary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend/` — การค้นชื่อ hint ไม่พบ route `physical-count` ระดับบนสุด; ตรวจสอบโฟลเดอร์โมดูลย่อยเมื่อเขียน
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count; เขียน traceability ของกฎเมื่อมี
- ชุดกฎที่เกี่ยวข้อง: [[inventory-adjustment/02-business-rules]] (`ADJ_*` — variance rollup อยู่ที่นั่น), [[inventory/02-business-rules]] (`INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` — semantics ของ ledger สืบทอดที่ adjustment post), [[costing]] (พฤติกรรม FIFO / WA refresh เมื่อ rollup post)
