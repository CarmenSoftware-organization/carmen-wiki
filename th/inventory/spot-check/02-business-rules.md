---
title: การสุ่มตรวจ (Spot Check) — Business Rules
description: กฎการตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ post และกฎข้ามโมดูลของการสุ่มตรวจ
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Business Rules

> **At a Glance**
> **กลุ่มกฎ:** `SPC_VAL_*` validation &nbsp;·&nbsp; `SPC_AUTH_*` permission &nbsp;·&nbsp; `SPC_CALC_*` calc &nbsp;·&nbsp; `SPC_POST_*` posting &nbsp;·&nbsp; `SPC_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 30 กฎ
> **กลุ่มผู้ใช้:** ผู้เขียน test + นักพัฒนา — ทุก rule ID ถูก anchor จากหน้า `04-test-scenarios*`
> **วงจรชีวิตสถานะ:** หัวข้อ 5.1 (ถ้ามี) มี callout ความแตกต่างระหว่าง Live UI กับ BRD

## 1. ภาพรวม

หน้านี้รวบรวมกฎการดำเนินงานที่กำกับ **โมดูล spot-check** — ต้นไม้เอกสารสองระดับ (`tb_spot_check` → `tb_spot_check_detail`) ที่บันทึกการนับบางส่วนแบบเจาะจงของสินค้าหรือสถานที่จัดเก็บที่เลือก กฎด้านล่างนี้อยู่ **เหนือ** [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) (variance rollup post ที่นั่น) และ **เหนือ** กฎระดับ ledger ใน [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) (ผลกระทบขั้นสุดท้ายต่อ inventory ลงจอดที่นั่น) — กฎเหล่านี้กำกับวงจรชีวิตของเอกสาร (`pending → in_progress → completed` บวก path การยกเลิก `void`), การเลือก `method` (random / high_value / manual), `size` ของตัวอย่าง, การมอบหมาย Counter, การ escalate ไป recount เมื่อ variance ทะลุ tolerance และจุดเชื่อมต่อข้ามโมดูลเข้า [inventory-adjustment](/th/inventory/inventory-adjustment) / [inventory](/th/inventory/inventory) / [costing](/th/inventory/costing) Rule ID ใช้ `SPC_VAL_*` (validation), `SPC_CALC_*` (calculation), `SPC_AUTH_*` (authorization), `SPC_POST_*` (posting), `SPC_XMOD_*` (cross-module)

มีข้อสังเกตเชิงโครงสร้างสองข้อจาก [spot-check/01-data-model](/th/inventory/spot-check/01-data-model) ที่ผลต่อทุกกฎด้านล่าง: **ข้อแรก** spot-check **แบน (ไม่มี period parent)** — ไม่เหมือน physical-count ไม่มี `tb_spot_check_period` ดังนั้นกฎระดับ period ของ `PHC_VAL_001` ไม่มี analog; แทนที่ การ containment ของ period บังคับใช้ตอน rollup ฝั่ง [inventory-adjustment](/th/inventory/inventory-adjustment) ตาม `INV_VAL_008` **ข้อที่สอง** ตารางของ spot-check ไม่เขียนลง inventory ledger โดยตรง — variance post ผ่าน rollup `tb_stock_in` / `tb_stock_out` และการ post adjustment เขียน `tb_inventory_transaction` ความหมายของ ledger สืบทอดจาก `INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` **ข้อที่สาม** ปัจจุบันยังไม่มี source ใน carmen/docs สำหรับกฎ `SPC_*` — rule ID ด้านล่างเป็น scaffolding ที่เสนอเพื่อยืนยันเมื่อ catalogue ใน carmen/docs ถูกเขียน

## 2. กฎ Validation

Rule ID ใช้รูปแบบ `SPC_VAL_NNN` Validation ทำงานที่สามขอบเขต: **ตอนสร้าง spot-check** (สร้าง sheet), **ตอนป้อนบรรทัด** (counter พิมพ์ `actual_qty`) และ **ตอน submit** (`in_progress → completed`)

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `SPC_VAL_001` | `location_id` อ้างอิงสถานที่ประเภท inventory หรือ consignment ที่ active ตาม [inventory](/th/inventory/inventory) `INV_VAL_009` สถานที่ direct-cost ไม่สามารถ spot-check ได้ | สร้าง spot check | Reject ด้วย `"Direct-cost locations cannot be spot-checked."` |
| `SPC_VAL_002` | `method` คือ `random` / `high_value` / `manual`; `size > 0` เมื่อ `method ∈ {random, high_value}`; method `manual` ต้องเพิ่มบรรทัด `tb_spot_check_detail` อย่างน้อยหนึ่งบรรทัดอย่างชัดเจนก่อน submit | สร้าง / แก้ไข spot check | Reject ด้วยข้อความ error เฉพาะ method |
| `SPC_VAL_003` | เมื่อ `method = random`, ระบบสุ่ม `size` สินค้าที่แตกต่างจาก inventory ใน scope ที่ `location_id`; เมื่อ `method = high_value`, top-`size` ตามมูลค่า on-hand หรือ velocity (tenant-configurable) ถูกเลือก | สร้าง sheet | ตัวอย่างสร้าง `size` row `tb_spot_check_detail`; ถ้า `size` เกินสินค้าที่แตกต่างที่มี ตัวอย่างถูกตัดและบันทึก log ส่วนต่าง |
| `SPC_VAL_004` | ทุก `tb_spot_check_detail` บรรทัดมี `actual_qty` ไม่เป็น null ก่อนเอกสารจะ submit ได้ | Submit | Reject ด้วย `"Cannot submit spot check — <N> of <M> lines remain uncounted."` |
| `SPC_VAL_005` | `actual_qty ≥ 0` บนทุก detail การนับ physical ติดลบไม่มีความหมาย | ป้อนบรรทัด | Reject ด้วย `"Counted quantity must be zero or positive."` |
| `SPC_VAL_006` | บรรทัดที่ `|diff_qty| / on_hand_qty` เกิน tolerance threshold ของ tenant (ทั่วไป 5% หรือสัมบูรณ์ 1 หน่วย แล้วแต่ค่าใดสูงกว่า) ถูก flag ให้ recount; เอกสาร submit ไม่ได้จนกว่าบรรทัดจะถูก recount-and-reconcile หรือถูกระบุชัดเจนว่า "accept variance" โดย Inventory Controller | Submit | บล็อก submit จนกว่าบรรทัดที่ flag จะถูกแก้ไข |
| `SPC_VAL_007` | `tb_spot_check` ที่ completed แล้วเปิดใหม่ไม่ได้ — การแก้ไขต้องใช้ spot check ใหม่หรือ `tb_stock_in` / `tb_stock_out` adjustment แบบ manual เทียบกับสถานที่เดียวกันตาม `SPC_POST_004` | แก้ไข completed | Reject ด้วย `"Cannot edit a completed spot check. Raise a manual inventory adjustment."` |
| `SPC_VAL_008` | spot check ที่ `pending` หรือ `in_progress` สามารถย้ายไป `void` ได้ (ยกเลิกก่อน completion); spot check ที่ `completed` แล้ว void ไม่ได้ — rollup adjustment (ถ้ามี) คือ path การ reverse ผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) | Void | Reject void บน completed; อนุญาต pending / in_progress |

> **TODO:** ยืนยันสูตร tolerance threshold และค่า default ที่แน่นอนจาก tenant config เมื่อ catalogue carmen/docs ถูกเขียน ยืนยันว่า spot-check มีกฎ frozen-stock window แยกที่ analog กับ `PHC_VAL_006` หรือไม่ — ไม่พบใน schema (ไม่มี `enum_spot_check_type`) Cross-reference กับ E2E spec สำหรับ flow recount เมื่อมี

## 3. กฎการคำนวณ

Rule ID ใช้รูปแบบ `SPC_CALC_NNN` ทุกฟิลด์ปริมาณเป็น `Decimal(20, 5)` ตาม `tb_spot_check_detail.on_hand_qty` / `actual_qty` / `diff_qty`

| Rule ID | สูตร |
| ------- | ------- |
| `SPC_CALC_001` (variance qty) | `diff_qty = actual_qty - on_hand_qty` ต่อบรรทัด บวก = overage (write-on); ลบ = shortage (write-off) เก็บใน `tb_spot_check_detail.diff_qty` |
| `SPC_CALC_002` (variance %) | `variance_% = (diff_qty / on_hand_qty) × 100` เมื่อ `on_hand_qty > 0`; เมื่อ `on_hand_qty = 0` และ `actual_qty > 0` ให้ถือเป็น new-discovery (100% บวก) ขับเคลื่อนการ flag tolerance-breach ตาม `SPC_VAL_006` ไม่ persist; derive ตอนอ่าน |
| `SPC_CALC_003` (variance value) | `variance_value = diff_qty × cost_per_unit` โดย `cost_per_unit` ตาม costing method ฝั่ง adjustment ของ tenant (ไม่มี enum costing-method เฉพาะของ spot-check ใน schema — สืบทอดจาก default `enum_physical_count_costing_method` หรือ basis ต้นทุนที่ configured ของ adjustment-type, รอยืนยันตาม `SPC_XMOD_003`) |
| `SPC_CALC_004` (sample size verification) | `actual_sampled_count == tb_spot_check.size` (หรือถูกตัดพร้อมเหตุผล log ตาม `SPC_VAL_003`) Derive ตอนอ่าน; ไม่ persist บน header (ไม่มีคอลัมน์ `product_counted` / `product_total` บน `tb_spot_check`) |

> **TODO:** ยืนยันลำดับความสำคัญของ costing-method ของ spot-check vs `enum_physical_count_costing_method` ของ physical-count เมื่อ logic frontend ถูกเขียน Cross-link ไป [costing](/th/inventory/costing) สำหรับพฤติกรรมการตีมูลค่า WA / FIFO

## 4. กฎ Authorization

Rule ID ใช้รูปแบบ `SPC_AUTH_NNN` Persona ตาม [spot-check](/th/inventory/spot-check) § 4 และการจัดกลุ่มสามกลุ่มในหน้าย่อยของโมดูลนี้ (inventory-controller / counter / audit-config)

| Rule ID | กฎ |
| ------- | ---- |
| `SPC_AUTH_001` | **Inventory Controller** สร้างและจัดตารางเอกสาร `tb_spot_check` ตั้งค่า `method` (random / high_value / manual) และ `size` มอบหมาย counter review variance อนุมัติหรือ reject คำขอ recount และอนุมัติ adjustment สำหรับการ post หนึ่งที่นั่งต่อ spot check ตามนโยบาย tenant |
| `SPC_AUTH_002` | **Counter** ป้อน `actual_qty` บนบรรทัด `tb_spot_check_detail` ที่ได้รับมอบหมายภายใน location/zone ของตน flag รายการเสียหาย / ไม่มีป้ายผ่าน `tb_spot_check_detail_comment` แต่ submit เอกสารไม่ได้ — เฉพาะ Inventory Controller เท่านั้นที่ submit ได้ |
| `SPC_AUTH_003` | กลุ่ม **Audit / Config**: Auditor มีสิทธิ์อ่านอย่างเดียวต่อทุกระดับ (header / detail) รวมถึง thread comment และ stamp counted-by เพื่อ review ผล spot-check, หลักฐาน recount, และ adjustment ที่ post อย่างเป็นอิสระ — ยืนยันว่าการควบคุมทำงานและการสูญเสียได้รับการสืบสวน Sysadmin (โดยปริยาย) config tolerance threshold, default `size`, default `method` และการ map reason-code |
| `SPC_AUTH_004` | การมอบหมาย counter ผูกกับ location — counter เห็นเฉพาะเอกสาร spot-check สำหรับ location ที่ตนมี `tb_user_location` (หรือ location-grant ที่เทียบเท่า) การมองเห็นข้าม location ต้องใช้ role Inventory Controller |

## 5. กฎการ Posting

Rule ID ใช้รูปแบบ `SPC_POST_NNN` Posting ในโมดูลนี้หมายถึง variance-rollup transition (spot-check-completion → การสร้าง adjustment) ไม่ใช่การเขียน ledger โดยตรง

| Rule ID | กฎ |
| ------- | ---- |
| `SPC_POST_001` | เมื่อ `tb_spot_check.doc_status = completed`, ชั้น application iterate `tb_spot_check_detail` และจัดกลุ่มบรรทัดด้วย `sign(diff_qty)`: บวก → `tb_stock_in` หนึ่งบรรทัดขึ้นไปภายใต้ reason `SPOT_CHECK_OVERAGE` (หรือ `COUNT_OVERAGE` ถ้า alias); ลบ → `tb_stock_out` หนึ่งบรรทัดขึ้นไปภายใต้ reason `SPOT_CHECK_SHORTAGE` (หรือ `COUNT_SHORTAGE`); ศูนย์ → ไม่มี rollup |
| `SPC_POST_002` | Header ของ rollup adjustment พกพา `info.spotCheckId = <tb_spot_check.id>` (และ/หรือ `info.countId` ถ้า reason ถูก alias) สำหรับ join ฝั่ง audit ย้อนกลับไปยังแหล่งที่มาของ spot-check Reason-code บน `tb_adjustment_type` ต้องมีอยู่พร้อมทิศทางที่เหมาะสม (ตาม [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 2.1) |
| `SPC_POST_003` | cost-per-unit บนแต่ละบรรทัด rollup ตั้งตาม `SPC_CALC_003` (costing method ที่สืบทอด) การลงนามรับรองของ Inventory Controller ในการ submit adjustment ตอบสนอง [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) approval ตาม rollup-fast-path (อำนาจ counter pre-approved ที่จุด submit ของ spot check) |
| `SPC_POST_004` | เมื่อ rollup adjustment เป็น `completed` แล้ว เอกสาร spot-check จะ **immutable** — การแก้ไขใด ๆ ในภายหลังที่สถานที่เดียวกันต้องใช้ `tb_stock_in` / `tb_stock_out` ใหม่ที่สร้างเอง (หรือ spot check ใหม่) ไม่ใช่การเปิดใหม่ |

### 5.1 วงจรชีวิตสถานะ — Live UI vs BRD Mapping

Prisma enum `enum_spot_check_status` ที่บันทึกใน [spot-check/01-data-model](/th/inventory/spot-check/01-data-model) § 4 คือสิ่งที่ live schema ใช้ `tx-10-spot-check.md` (BR-spot-check.md v2.2.0) อธิบายชุดสถานะที่ตั้งใจ Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27)

> Diff legend: ✅ ตรงกัน · 🟡 เปลี่ยนชื่อ/เปลี่ยน semantic · 🔴 ใหม่ใน live schema (ไม่มีใน BRD)

| Live schema status (`enum_spot_check_status`) | BRD (`tx-10-spot-check.md`) equivalent | Diff | Notes |
|---|---|---|---|
| `pending` | `draft` / `pending` | 🟡 | BRD ใช้ `draft` (สร้าง ไม่ submit) → `pending` (submit รอเริ่ม) เป็นสองสถานะที่แตกต่าง Live schema ยุบทั้งสองเป็น `pending` Counter ป้อน qty แรก trigger `pending → in_progress` |
| `in_progress` | `in-progress` | ✅ ตรงกัน | ตรงโดยตรง การนับกำลังดำเนิน |
| `completed` | `completed` | ✅ ตรงกัน | ตรงโดยตรง Terminal; ตอบสนอง End Period Close Stage 2 (BR-PE-006) |
| `void` | `cancelled` | 🟡 | BRD ใช้ `cancelled` พร้อม note ว่าข้อมูลที่ป้อนทั้งหมดถูกเก็บไว้และไม่มีการเปลี่ยนแปลง inventory ที่ post (BR-SC-007) Live schema ใช้ `void` |
| — | `on-hold` | 🔴 | BRD กำหนด `on-hold` (พัก; → `in-progress`, `cancelled`) ไม่มีค่า `on_hold` ใน `enum_spot_check_status` ใน Prisma schema — การพัก/resume อาจจัดการผ่าน UI state หรือ migration ในอนาคต |

> ⚠️ **Discrepancy — การยุบ `draft` vs `pending`:** BRD `tx-10-spot-check.md` กำหนดสองสถานะก่อนนับที่แตกต่าง: `draft` (สร้าง ไม่ submit → `pending`) และ `pending` (submit รอเริ่ม → `in-progress`) `enum_spot_check_status` ใน live มีเพียง `pending` — ความแตกต่างระหว่าง create/submit ไม่ persist เป็นค่า enum แยก Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27)

> ⚠️ **Discrepancy — สถานะ `on-hold` ไม่อยู่ใน schema:** BRD กำหนด `on-hold` เป็นสถานะ pause ที่ valid (`in-progress → on-hold → in-progress`) `enum_spot_check_status` ใน live ไม่รวมค่า `on_hold` — พฤติกรรม pause/resume (เช่น "staff unavailable") อาจจัดการที่ชั้น UI โดยไม่ persist สถานะ enum แยก หรืออาจถูกเลื่อนออก Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27)

> ⚠️ **Discrepancy — Gate End Period Close Stage 2 ไม่ได้สร้างใน BRD posting rules:** INDEX ของ test-case ระบุว่า Spot Check ทั้งหมดต้องเป็น `completed` ก่อน End Period Close Stage 2 จะผ่าน (BR-PE-006) BRD (BR-spot-check.md v2.2.0) ไม่รวมกฎที่สอดคล้องใน spot-check posting rules — gate การปิด period กำหนดที่ฝั่ง End Period Close (tx-09) วิกิ cross-reference นี้ใน `SPC_POST_001` ผ่านสถานะ terminal `completed` แต่ live UI บังคับใช้เป็น gate ภายนอก ไม่ใช่ constraint ภายใน spot-check Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27)

> ⚠️ **Discrepancy — การ post variance ไปยัง inventory PENDING:** BRD (BR-spot-check.md v2.2.0) บอกใบ้ว่า variance post ไปยัง QOH / lots / cost เมื่อ completion (pattern rollup เดียวกับ Physical Count) การ implement ที่ live ถึงสถานะ `completed` และตอบสนอง End Period Close Stage 2 แต่ **ไม่** ได้ post variance adjustment ไปยัง inventory, lots หรือ cost ในปัจจุบัน ผลกระทบ lot และผลกระทบต้นทุนทั้งคู่ mark เป็น TBC Source: `Test_case/System_Process/tx-10-spot-check.md` (capture date 2026-04-27)

## 6. กฎข้ามโมดูล

Rule ID ใช้รูปแบบ `SPC_XMOD_NNN`

| Rule ID | กฎ |
| ------- | ---- |
| `SPC_XMOD_001` | **→ [inventory-adjustment](/th/inventory/inventory-adjustment)**: variance ของ spot-check post ผ่านต้นไม้เอกสาร `tb_stock_in` / `tb_stock_out` ด้วย reason code `SPOT_CHECK_OVERAGE` / `SPOT_CHECK_SHORTAGE` (หรือ alias เป็น `COUNT_*`) Rollup เป็น path เดียวจาก spot check ไปยัง ledger |
| `SPC_XMOD_002` | **→ [inventory](/th/inventory/inventory)**: ทุก rollup adjustment เขียน `tb_inventory_transaction` ด้วย `enum_transaction_type = adjustment_in` / `adjustment_out` ไม่มีค่า `spot_check` โดยตรงบน `enum_transaction_type` |
| `SPC_XMOD_003` | **→ [costing](/th/inventory/costing)**: การเลือก costing-method บน rollup สืบทอด default ฝั่ง adjustment (ไม่มี `enum_spot_check_costing_method` เฉพาะใน schema); การบริโภค FIFO (สำหรับ shortage) และการ refresh WA (สำหรับ overage) ตาม `INV_CALC_005` / `INV_CALC_007` เมื่อ adjustment post |
| `SPC_XMOD_004` | **→ [physical-count](/th/inventory/physical-count)**: spot check เป็น **คู่เทียบการนับบางส่วน** ของ [physical-count](/th/inventory/physical-count) — scope แคบกว่า (ตัวอย่าง ไม่ใช่ทุกรายการที่ทุก location), ไม่มี parent งวดบัญชี, cadence ad-hoc ใช้ hook variance-rollup แบบแนวคิดเดียวกันเข้า [inventory-adjustment](/th/inventory/inventory-adjustment); **ไม่ใช่** child ของ `tb_physical_count_period` |

> **TODO:** ตรวจสอบ rule ID ข้างต้นกับ catalogue `SPC-*` ใน carmen/docs เมื่อเขียน ยืนยันค่า default ของ tolerance / threshold จาก tenant config ของ production cross-validate posting fan-out กับการ implement ของ frontend ใน `../carmen-inventory-frontend/`; ยืนยันการตั้งชื่อ reason-code (`SPOT_CHECK_*` vs `COUNT_*` ที่ใช้ซ้ำ)

## 7. แหล่งอ้างอิง

- **Primary (Prisma):** ดู [spot-check/01-data-model](/th/inventory/spot-check/01-data-model) สำหรับ citation ของ entity / enum source
- **Secondary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend/` — การค้นชื่อ hint ไม่พบ route `spot-check` ระดับบนสุด; ตรวจสอบโฟลเดอร์โมดูลย่อยเมื่อเขียน
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; เขียน traceability ของกฎเมื่อมี
- ชุดกฎที่เกี่ยวข้อง: [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_*` — คู่เทียบการนับเต็มที่มีโครงสร้าง period สามระดับ; spot-check เป็นลูกพี่ลูกน้องสองระดับที่เรียบง่ายกว่า), [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) (`ADJ_*` — variance rollup อยู่ที่นั่น), [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) (`INV_VAL_*` / `INV_CALC_*` / `INV_POST_*` — semantics ของ ledger สืบทอดที่ adjustment post), [costing](/th/inventory/costing) (พฤติกรรม FIFO / WA refresh เมื่อ rollup post)
