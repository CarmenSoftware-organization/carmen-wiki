---
title: คลังสินค้า (Inventory) — Test Scenarios — Inventory Controller
description: Test cases ของ Inventory Controller สำหรับการ review และการ close ปิดงวด
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (ผู้ดำเนินการ period-end) &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **พื้นผิว:** `/inventory-management/period-end` + `/review`
> **E2E:** `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` — เทสหน้า list รันได้; describes ของ close-workflow ถูกทำเครื่องหมายว่า "Feature pending" แคตตาล็อก gap แบบ manual `docs/test-cases/gaps/900-period-end-gap.md` (43 เคส: TC-PE-01 list, TC-PE-02 review, TC-PE-03 start counting, TC-PE-04 close, TC-PE-31 physical-count unlock, TC-PE-32 document links)
> **Correction (2026-07-15):** ~26 scenarios เดิม (queue อนุมัติ adjustment, การ commit count-variance, editor ของ stock-policy, การเซ็นรับรอง variance) อธิบายพื้นผิวที่ไม่มีอยู่ในโมดูลนี้; scenarios ด้านล่างครอบคลุม flow review/close ที่มีอยู่จริง

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | ดูงวดปัจจุบัน | มี row `tb_inventory_period` ที่ `status ∈ {open, locked}` | 1. เปิด `/inventory-management/period-end` | Card แสดง period code (YYMM), fiscal year/month, วันที่เริ่ม/สิ้นสุด, status badge, note (ถ้ามี); ประวัติงวดที่ปิดแล้ว render ด้านล่าง (map ไปยัง `TC-PE-010001`) |
| IC-HP-02 | เริ่มรอบการนับ | งวดปัจจุบัน `open`; ไม่มีเอกสารเคลื่อนไหวสต๊อกที่ยังเปิด | 1. คลิก **Start Period Close** 2. ยืนยัน dialog | `POST /period-ends/start-counting` → 200 `{ physical_count_period: { status: counting }, created }`; toast "Counting started."; navigate ไปยัง `/inventory-management/period-end/review`; `GET /period-ends/review` return `can_start_counting`, `start_blocking`, `can_close`, `close_blocking` และสถิติต่อโมดูลสำหรับ pr/po/grn/cn/sr/si/so บวกความคืบหน้าการนับต่อ location (map ไปยัง `TC-PE-030106`) |
| IC-HP-03 | Drill เข้า card ของโมดูล | มี PRs บางส่วนในงวด | 1. คลิก card PR | Dialog แสดงรายการเอกสาร PR ของงวด (`no`, `status`, `date`) แต่ละรายการลิงก์ไป `/procurement/purchase-request/{id}`; rows ของ SI/SO ลิงก์ไป `/inventory-management/inventory-adjustment/{id}?type=stock-in|stock-out` (`TC-PE-020104`, `TC-PE-320102`) |
| IC-HP-04 | เปิดหรือสร้าง count ของ location | รอบเป็น `counting`; required location ยังไม่มี count | 1. คลิกการ์ดของ location | `POST /physical-counts` สร้าง count สำหรับ location และงวดนั้น แล้ว deep-link ไปยัง `/inventory-management/physical-count/{physical_count_id}/entry`; count ที่มีอยู่แล้วเปิดโดยตรง ก่อนรอบเป็น `counting` การ์ดถูก disable พร้อมข้อความ "Counting has not started for this period yet." (`TC-PE-020113`) |
| IC-HP-05 | ปิดงวด (FIFO tenant) | ทุก gate เขียว (`can_close: true`); BU `calculation_method = fifo` | 1. คลิก **Close Period** 2. ยืนยัน | `POST /period-ends`; toast สำเร็จ; กลับไปยัง list DB: carry-over transactions `close`/`open` (lots ใหม่ `{location_code}{YYMM}{seq4}`, `parent_lot_no` = lot เดิม), `tb_inventory_period.status = closed`, งวดถัดไปเปิด, rows `tb_physical_count_period` เป็น completed, **ไม่มี** snapshot rows (`TC-PE-040104`) |
| IC-HP-06 | ปิดงวด (average tenant) | เหมือน IC-HP-05 แต่ `calculation_method = average` | ขั้นตอนเดียวกัน | เหมือน IC-HP-05 บวกการ restate issue-layer ที่ average สุดท้าย และหนึ่ง row `tb_inventory_period_snapshot` ต่อ bucket `(product, location)` |
| IC-HP-07 | ตรวจสอบการ close บน ledger | งวดเพิ่งปิด | 1. เปิด Transaction Log 2. Filter `close`/`open` | คู่ close/open ปรากฏโดยมี period code เป็น `parent_document_no` |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง |
| - | -------- | ------------------ |
| IC-PERM-01 | User ที่มี `inventory_management.period_end.view` เปิดหน้าเหล่านี้ | **Allow** (อ่าน) |
| IC-PERM-02 | User ที่มี `.execute` คลิก **Start Period Close** / **Close Period** | **Allow** — สอง mutation ในโมดูล (guard key ของ gateway `period_end.startCounting` / `period_end.close`; map ไปยัง `TC-PE-010109` ซึ่งเป็นคู่ denial) |
| IC-PERM-03 | User ที่ไม่มี period-end keys navigate ไปยัง `/period-end` | **Deny** — route guard redirect/block ตาม permission catalogue (describes เรื่อง permission-denial ใน `900-period-end.spec.ts`) |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| IC-VAL-01 | Close ถูก block โดยเอกสาร | SR ที่มีเลขที่ใด ๆ ที่ `in_progress` กลาง workflow, GRN/CN ในสถานะกลางทาง หรือ required location ที่ยังไม่ได้นับ | ปุ่ม disabled พร้อม tooltip "All transactions must be complete and all physical counts must be completed before closing."; ถ้า force เรียก API จะ return `` `Cannot close period: {total} document(s) are incomplete` `` (422) พร้อมจำนวนต่อประเภทใน `close_blocking` PR/PO ที่ in progress ไม่ถูกนับ |
| IC-VAL-02 | Race ของ concurrency | สอง sessions close พร้อมกัน | ผู้เรียกคนที่สองได้ `` `Counting cannot be started for this period` `` (`PERIOD_END_COUNTING_NOT_ALLOWED`, 409 — re-check ด้วย `FOR UPDATE`) |
| IC-VAL-03 | Blocker ที่มาช้า | เอกสารที่ block ถูกสร้างหลังหน้า review โหลดแต่ก่อนการคลิก | การ re-validate ภายใน transaction reject ด้วย error incomplete-documents — หน้าจอเขียวที่ stale ไม่ชนะ |
| IC-VAL-04 | ไม่มีงวดปัจจุบัน | ไม่มีงวด `open`/`locked` อยู่ | หน้า list แสดง empty state แบบ no-current-period (`TC-PE-010103`); review/close ใช้ไม่ได้ (`PERIOD_END_NO_CURRENT_PERIOD`, 404) |
| IC-VAL-05 | การเริ่มนับถูก block | GRN ที่ `draft`, SI/SO ที่ `draft` หรือ SR ที่มีเลขที่ที่ `draft`/`in_progress` ลงวันที่ในงวด | `POST /period-ends/start-counting` → 422 `` `Cannot start counting: {total} document(s) in this period are still open` ``; dialog "Finish these documents first" list เอกสารเหล่านั้นจัดกลุ่มตามประเภทพร้อม status badge และลิงก์ (`TC-PE-030103`/`030104`); รอบคง `draft` |
| IC-VAL-06 | เริ่มนับบนงวดที่ไม่ใช่ open | งวดเป็น `locked` หรือรอบของมัน `completed` ไปแล้ว | 409 `` `Counting cannot be started for this period` `` |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| IC-EDGE-01 | Card ของโมดูลว่าง | ไม่มีเอกสารของประเภทหนึ่ง ๆ ในงวดเลย | Card ยัง render ด้วย count 0 และ badge Incomplete (`is_complete = count > 0 && …`) แต่ปุ่ม **Close Period** ตาม `can_close` ของ backend ดังนั้นโมดูลว่างไม่ block (`TC-PE-900201`) |
| IC-EDGE-02 | GRN draft ในงวด | GRN ยังอยู่ที่ `draft` | Block **Start Period Close** (`listStartCountingBlockers` ต้องการ `committed`/`voided`) แต่**ไม่** block การ close (`draft ∈` pass-list ของการ close); review card นับมันเป็น incomplete |
| IC-EDGE-03 | Spot checks ยังค้างอยู่ | Spot checks ยังไม่เสร็จตอนสิ้นเดือน | Close ดำเนินต่อ — spot check ไม่ใช่ gate (`validatePeriodEnd` ไม่มี validator ของ spot-check) |
| IC-EDGE-04 | งวดปัจจุบัน locked | Period service ตั้ง `status = locked` | `findCurrent` ยัง return งวดนั้น (`status ∈ {open, locked}`); card render งวดนั้นและการ close รันต่อมันได้ |
| IC-EDGE-05 | การข้ามปี | ปิด fiscal month 12 | `ensureNextPeriod` สร้าง month 1 ของ fiscal year ถัดไป (`period` = `YYMM` ถัดไป) |
| IC-EDGE-06 | Continue Counting | รอบเป็น `counting` อยู่แล้ว | ปุ่มบนการ์ดอ่านว่า **Continue Counting** และ navigate ไป `/review` โดยไม่มี POST ครั้งที่สองหรือ confirm dialog (`TC-PE-010106`); ถ้าเรียก API อีกครั้งอยู่ดีจะคืน `already_counting: true` |
| IC-EDGE-07 | Lots ที่รับเข้างวดถัดไปก่อนการ close | GRN ที่ลงวันที่ในงวดถัดไป (ซึ่งเปิดอยู่แล้ว) ถูก commit ก่อนงวดนี้ปิด | Layers ของมันมี `at_period` ของงวดถัดไปและ**ไม่**ถูกกวาดโดยการ close (`findAllRemainingLots` กรองด้วย `end_at ≤` ของงวดที่กำลังปิด) |

## 5. แหล่งอ้างอิง

- User flow: [03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller); screen reference: [period-end](/th/inventory/inventory/period-end)
- Business rules: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_POST_009`/`INV_POST_010`, `INV_CALC_008`/`INV_CALC_009`, `INV_AUTH_008`
- E2E: `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` (TC-PE-01xxxx รันได้; TC-PE-02/03/04xxxx "Feature pending"); แคตตาล็อก gap แบบ manual `docs/test-cases/gaps/900-period-end-gap.md`; user stories `docs/user-stories/900-period-end.md`
- Backend specs: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/*.spec.ts`
