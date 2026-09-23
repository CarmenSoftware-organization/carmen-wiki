---
title: คลังสินค้า (Inventory) — Test Scenarios
description: Test cases ตาม persona, scenarios ข้าม persona และการ map E2E สำหรับ inventory
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory, test-scenarios, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — Test Scenarios

> **At a Glance**
> **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **Scenarios ข้าม persona:** 14 &nbsp;·&nbsp; **Personas ครอบคลุม:** Store Keeper (ledger), Inventory Controller (period end); Finance และ Audit / Config เป็นหน้า correction
> **ลำดับการรัน:** post เอกสาร source → ตรวจสอบ ledger → รัน scenarios ปิดงวด
> **Correction (2026-07-15):** ตาราง ~17 scenarios เดิม assert เรื่อง threshold approval chains, GL entries, การ reject post ย้อนหลัง, UI error แบบ negative-balance บนเอกสาร manual, consignment memo receipts, Sysadmin drain-blockers และ period lock/re-open — ทั้งหมดได้รับการยืนยันแล้วว่าไม่มี source รองรับและถูกลบออก ตารางด้านล่างมีเฉพาะพฤติกรรมที่ตรวจสอบกับ source ได้เท่านั้น
> **Executable coverage (2026-09-22):** period end — `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` (describe ของหน้า list และ permission-denial รันได้; describe ของ detail / close-workflow / close-action ยังติด tag "Feature pending"), แคตตาล็อก gap แบบ manual `docs/test-cases/gaps/900-period-end-gap.md` (43 เคส รวมปุ่ม **Start Period Close** / **Close Period** ที่ย้อนกลับไม่ได้), user story ที่ generate `docs/user-stories/900-period-end.md` (35) Transaction log — ไม่มี spec; แคตตาล็อก manual `docs/test-cases/740-stock-transaction.md` (38 เคส) ผลกระทบต้นน้ำ — `tests/501-grn.spec.ts`, `tests/601-cn.spec.ts`, `tests/701-sr.spec.ts`, `tests/720-stock-issue.spec.ts` (issue views ของ SR; gap report `docs/test-cases/gaps/720-stock-issue-gap.md`, 44 เคส)

## 1. ภาพรวม

หน้านี้คือจุดเข้าภาพรวมสำหรับชุด test-scenarios ของโมดูล `inventory` พื้นผิว UI ของตัวโมดูลเองมีขนาดเล็ก (Transaction Log แบบ read-only + Period End) ดังนั้น *ผลกระทบ* ฝั่ง inventory ส่วนใหญ่จึงถูก assert จาก suites ของโมดูลต้นน้ำ: ผลการ post ของ GRN ใน `501-grn.spec.ts`, ผลการ issue ของ SR ใน `701-sr.spec.ts` / `720-stock-issue.spec.ts` (หมายเหตุ: `720-stock-issue.spec.ts` navigate ไปยัง issue views ของ **store-requisition** ไม่ใช่หน้าจอ manual stock-out), ผลของ credit-note ใน `601-cn.spec.ts` และพื้นผิว period-end ใน `900-period-end.spec.ts` (เทสหน้า list รันได้; describe blocks ของ detail/close-workflow ถูกทำเครื่องหมายว่า "Feature pending") พฤติกรรมฝั่ง backend (FIFO consumption, การ recompute average, direct-location auto-issue, carry-over ตอน close) ถูกครอบคลุมเพิ่มเติมโดย unit specs ใน `carmen-turborepo-backend-v2` (`inventory-transaction.service.spec.ts`, `period-end.*.spec.ts`)

## 2. Personas ในขอบเขต

- **Store Keeper**: ตรวจสอบการ posting บน Transaction Log แบบ read-only (`inventory_management.view`); การสร้าง adjustments/counts ทำในโมดูลข้างเคียง
- **Inventory Controller / ผู้ดำเนินการ period-end**: ทำงานกับ review checklist และรันการ close (`inventory_management.period_end.view` / `.execute`)
- **Finance**: หน้า correction — [04-test-scenarios-finance](/th/inventory/inventory/04-test-scenarios-finance); ไม่มีพื้นผิวสำหรับ Finance อยู่จริง
- **Audit / Config**: หน้า correction — [04-test-scenarios-audit-config](/th/inventory/inventory/04-test-scenarios-audit-config); ไม่มีพื้นผิว audit/config อยู่จริง

## 3. ไฟล์เทสต่อ Persona

- [Store Keeper scenarios](/th/inventory/inventory/04-test-scenarios-store-keeper)
- [Inventory Controller scenarios](/th/inventory/inventory/04-test-scenarios-inventory-controller)
- [Finance scenarios](/th/inventory/inventory/04-test-scenarios-finance) (หน้า correction)
- [Audit / Config scenarios](/th/inventory/inventory/04-test-scenarios-audit-config) (หน้า correction)

## 4. Scenarios ข้าม Persona / Integration

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | GRN post ไปยัง ledger | GRN operator → Store Keeper | GRN ที่ `draft` พร้อมจำนวนที่รับ; `grn_date` อยู่ในงวดที่เปิด | BU วิธี average: เมื่อ **save** (`draft → saved`) หนึ่ง `tb_inventory_transaction` (`good_received_note`), หนึ่ง detail ต่อ line (พร้อม `good_received_note_detail_item_id`), inbound cost layers (lots `{location_code}{YYMM}{seq4}`); row ใน Transaction Log แสดงเลข GRN และ Qty In สีเขียว; การแก้จำนวนภายหลังจะ void แล้ว post ใหม่ BU แบบ FIFO: ไม่มีอะไรตอน save — rows เดียวกันปรากฏตอน **commit** |
| 2 | Receipt เข้า direct-location net เป็นศูนย์ | GRN operator → Store Keeper | line ของ GRN ชี้ไปยัง location ที่ `location_type = direct` | สอง legs ภายใต้ transaction เดียว: inbound layer + `issue` layer หักล้างอัตโนมัติที่ต้นทุนเดียวกัน; on-hand สุทธิ 0; ภายใต้ average method receipt นี้ถูกยกเว้นจาก average ของสินค้า |
| 3 | SR issue consume FIFO lots | SR approver → Store Keeper | BU แบบ FIFO; สอง lots ที่ source location ด้วยต้นทุนต่างกัน; SR issue ที่อนุมัติแล้วมีจำนวนใหญ่กว่า lot ที่เก่าที่สุด | outbound layers consume lots จากเก่าไปใหม่ (`lot_at_date`/`lot_seq_no`); consumption ที่ span หลาย lots สร้าง layer rows หลายแถว แต่ละแถวที่ต้นทุนของ lot นั้น พร้อม `parent_lot_no` ถูกตั้งค่า |
| 4 | Outbound ที่เกิน balance ถูก reject | SR / adjustment operator | balance ที่มี < จำนวนที่ขอ ที่ `(product, location)` | **Commit** ของ stock-out: `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`, 400) ก่อนเขียน ledger ใด ๆ; ระดับ ledger (SR): `` `Insufficient stock. Requested: <X>, Available: <Y>` ``; ไม่มี rows ถูกเขียน ข้อยกเว้น: quantity consumption ของ credit-note บันทึก `diff_amount` แทนการโยน error |
| 5 | Credit-note amount ต่อ lot ในงวดที่เปิด re-price lot นั้น | CN operator → Store Keeper | CN แบบ `credit_note_amount` ต่อ lot ของ GRN ที่รับในงวดที่ยังเปิดอยู่ | cost-layer rows บันทึก credit; มูลค่าของ lot ถูก restate (BU แบบ average: คู่ SO-at-old-average / SI-at-new-average); consumption ปลายน้ำใช้ต้นทุนใหม่ |
| 6 | Credit-note amount ต่อ lot ในงวดที่ปิดบันทึกเฉพาะ diff | CN operator | เหมือน 5 แต่งวดที่รับเป็น `closed`/`locked` (`isLotPeriodClosed`) | มูลค่าของ lot **ไม่** ถูก re-price; credit post เป็น `diff_amount` ของงวดปัจจุบัน |
| 7 | เอกสารที่ลงวันที่ในงวดที่ปิดแล้วถูก reject | operator ของ source ใด ๆ | stock-in ลงวันที่ในงวดที่ปิดแล้ว; stock-out ลงวันที่นอกงวดปัจจุบัน | `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD` / `STOCK_OUT_DATE_NOT_CURRENT_PERIOD` (422) ตอน create **และ** ตอน commit; ไม่มีอะไร post เอกสารที่ลงวันที่ในงวด open (หรือ locked) post ด้วย `at_period`/`period_id` ของ**งวดนั้น** (`findOpenPeriodForDate`) ไม่ใช่งวดตามเวลาปัจจุบัน |
| 8 | การปิดงวดถูก block โดยเอกสาร | Inventory Controller | มี SR ที่มีเลขที่ในงวดที่ `in_progress` พร้อม `workflow_next_stage ≠ '-'` หรือ GRN/CN ในสถานะกลางทาง หรือ required location ที่ยังไม่ได้นับ | payload ของ review `can_close = false`; ปุ่ม **Close Period** disabled; ถ้า force เรียก API จะ return `Cannot close period: {total} document(s) are incomplete` (422, `data = close_blocking`) PR หรือ PO ที่ `in_progress` **ไม่** block |
| 9 | Happy path ปิดงวด (FIFO tenant) | Inventory Controller | ทุก gate เขียว; `calculation_method = fifo` | transaction `close` ทำให้แต่ละ lot ที่ยังเหลือซึ่งงวดมี `end_at ≤` งวดนี้เป็นศูนย์ (lot ใหม่ `{location_code}{YYMM}{seq4}`, `parent_lot_no` = lot เดิม); transaction `open` สร้าง lots เหล่านั้นใหม่ในงวดถัดไปที่ auto-provision; `tb_inventory_period.status = closed`; rows `tb_physical_count_period` เป็น completed; **ไม่มี** rows `tb_inventory_period_snapshot` |
| 10 | Happy path ปิดงวด (average tenant) | Inventory Controller | ทุก gate เขียว; `calculation_method = average` | เหมือน 9 บวก issue-layers ถูก restate ที่ average สุดท้าย และหนึ่ง row `tb_inventory_period_snapshot` ต่อ bucket `(product, location)` พร้อมคอลัมน์ opening/receipt/issue/adjustment/closing |
| 11 | Race การ close พร้อมกัน | Inventory Controller ×2 | สอง sessions คลิก **Close Period** เกือบพร้อมกัน | การ close แรกชนะภายใต้ lock `FOR UPDATE`; ตัวที่สองได้ `Counting cannot be started for this period` (`PERIOD_END_COUNTING_NOT_ALLOWED`, 409 — รายการใน catalog ที่ใช้ร่วมกัน); ไม่มี carry-over ซ้ำสอง |
| 12 | มูลค่า carried-in ถูกล็อก | Inventory Controller → CN operator | งวดปิดแล้ว (lots carry ผ่าน `open_period`); CN amount ถูก raise ต่อ lot ที่มีก่อน close | carry-in layers (`open_period`, `eop_in`) ถูกยกเว้นจากการ re-price (`CARRIED_IN_TRANSACTION_TYPES`); credit บันทึกเป็น `diff_amount` ของงวดปัจจุบัน (เหมือน 6) |
| 13 | การเริ่มนับถูก block โดยเอกสารเคลื่อนไหวสต๊อกที่ยังเปิด | Inventory Controller | GRN ที่ `draft`, stock-in / stock-out ที่ `draft` หรือ SR ที่มีเลขที่ที่ `draft`/`in_progress` ลงวันที่ในงวด | `POST /period-ends/start-counting` → 422 `Cannot start counting: {total} document(s) in this period are still open`, `data = { counts, total, documents }`; UI แสดง dialog "Finish these documents first" พร้อมหนึ่งลิงก์ต่อเอกสาร; `tb_physical_count_period` คง `draft`; PR/PO ที่ `in_progress` ไม่ block |
| 14 | Happy path ของการเริ่มนับและ idempotency | Inventory Controller | ไม่มีเอกสารเคลื่อนไหวสต๊อกที่ยังเปิด; งวด `open` | การเรียกครั้งแรกสร้าง (หรือย้าย) `tb_physical_count_period` ของงวดไปเป็น `counting` (`created: true` / `already_counting: false`) และ navigate ไป `/review`; การเรียกครั้งที่สองคืน `already_counting: true` โดยไม่มี error; ปุ่ม **Start** ของ physical-count เปิดใช้งานแล้วสำหรับ required locations |

## 5. การ Map E2E Test

| Spec / describe block | Scenarios ครอบคลุม (Section 4) |
| --------------------- | ------------------------------ |
| `900-period-end.spec.ts` — "Period End — List page" (รันได้) | การแสดง period card, empty/closed states, การ deny permission สำหรับหน้า list (รองรับพื้นผิวของ 8–11) |
| `900-period-end.spec.ts` — describes ของ Detail / Close-workflow / Close-action (**"Feature pending"** — placeholder tests) | 8, 9, 10, 11, 13, 14 — spec เอง flag ว่า pending; แคตตาล็อก gap แบบ manual `docs/test-cases/gaps/900-period-end-gap.md` (TC-PE-03xxxx start-counting, TC-PE-04xxxx close, TC-PE-31xxxx physical-count unlock) คือแหล่งอ้างอิง executable-intent ปัจจุบัน |
| `501-grn.spec.ts` | 1, 2 (ผลของ GRN save ต่อ ledger) |
| `701-sr.spec.ts` / `720-stock-issue.spec.ts` (SR issue views) | 3, 4 (พื้นผิวฝั่ง issue; assertions ของ FIFO อยู่ระดับ backend-unit) |
| `601-cn.spec.ts` | 5, 6 (พื้นผิวของ credit-note) |
| Backend unit specs (`inventory-transaction.service.spec.ts`, `period-end.close-transaction.helper.spec.ts`, `period-end.close-average.helper.spec.ts`, `period-end.validate.spec.ts`) | 2–7, 9–12 (assertions ที่เป็น authoritative สำหรับคณิตศาสตร์ costing/close) |

Gaps: ไม่มี E2E ที่ exercise หน้าจอ Transaction Log เอง (แคตตาล็อก manual `740-stock-transaction.md`, 38 เคส); E2E ของ close workflow ถูกระบุชัดว่า "Feature pending"

## 6. แหล่งอ้างอิง

- E2E: `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts`, `501-grn.spec.ts`, `701-sr.spec.ts`, `720-stock-issue.spec.ts`, `601-cn.spec.ts`; แคตตาล็อก `docs/test-cases/gaps/900-period-end-gap.md`, `docs/test-cases/740-stock-transaction.md`, `docs/test-cases/gaps/720-stock-issue-gap.md`
- Backend specs: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.spec.ts` และ `.../period-end/*.spec.ts`
- Sibling: [03-user-flow](/th/inventory/inventory/03-user-flow) (lifecycle), [02-business-rules](/th/inventory/inventory/02-business-rules) (rule IDs ที่อ้างอิงด้านบน)
