---
title: คลังสินค้า (Inventory) — Test Scenarios — Inventory Controller
description: Test cases ของ Inventory Controller สำหรับการ review และการ close ปิดงวด
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (ผู้ดำเนินการ period-end) &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **พื้นผิว:** `/inventory-management/period-end` + `/review`
> **E2E:** `900-period-end.spec.ts` — เทสหน้า list รันได้; describes ของ close-workflow ถูกทำเครื่องหมายว่า "Feature pending"
> **Correction (2026-07-15):** ~26 scenarios เดิม (queue อนุมัติ adjustment, การ commit count-variance, editor ของ stock-policy, การเซ็นรับรอง variance) อธิบายพื้นผิวที่ไม่มีอยู่ในโมดูลนี้; scenarios ด้านล่างครอบคลุม flow review/close ที่มีอยู่จริง

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | ดูงวดปัจจุบัน | มี row `tb_period` ที่ `status ∈ {open, locked}` | 1. เปิด `/inventory-management/period-end` | Card แสดง period code (YYMM), fiscal year/month, วันที่เริ่ม/สิ้นสุด, status badge, note (ถ้ามี); ประวัติงวดที่ปิดแล้ว render ด้านล่าง (map ไปยัง `TC-PE-010001`) |
| IC-HP-02 | เปิดหน้า review | มีงวดปัจจุบัน | 1. คลิกปุ่มเริ่มการ close | Navigate ไปยัง `/inventory-management/period-end/review`; `GET /period-ends/review` return สถิติเอกสารที่ block ต่อโมดูล (pr/po/grn/cn/sr) และความคืบหน้าการนับต่อ location |
| IC-HP-03 | Drill เข้า card ของโมดูล | มี PRs บางส่วนในงวด | 1. คลิก card PR | Dialog แสดงรายการเอกสาร PR ของงวด (`no`, `status`, `date`) เพื่อให้ตามเอกสารที่ block ได้ |
| IC-HP-04 | กระโดดไปยัง count ที่กำลังดำเนินอยู่ | Required location มี count ที่กำลังดำเนินอยู่ | 1. คลิก row ของ location | Deep-link ไปยัง `/inventory-management/physical-count/{physical_count_id}/entry` |
| IC-HP-05 | ปิดงวด (FIFO tenant) | ทุก gate เขียว; BU `calculation_method = fifo` | 1. คลิก **Close period** 2. ยืนยัน | `POST /period-ends`; toast สำเร็จ; กลับไปยัง list DB: carry-over transactions `close`/`open` (lots `CLOSE-…`/`OPEN-…`), `tb_period.status = closed`, งวดถัดไปเปิด, rows `tb_physical_count_period` เป็น completed, **ไม่มี** snapshot rows |
| IC-HP-06 | ปิดงวด (average tenant) | เหมือน IC-HP-05 แต่ `calculation_method = average` | ขั้นตอนเดียวกัน | เหมือน IC-HP-05 บวกการ restate issue-layer ที่ average สุดท้าย และหนึ่ง row `tb_period_snapshot` ต่อ bucket `(product, location)` |
| IC-HP-07 | ตรวจสอบการ close บน ledger | งวดเพิ่งปิด | 1. เปิด Transaction Log 2. Filter `close`/`open` | คู่ close/open ปรากฏโดยมี period code เป็น `parent_document_no` |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง |
| - | -------- | ------------------ |
| IC-PERM-01 | User ที่มี `inventory_management.period_end.view` เปิดหน้าเหล่านี้ | **Allow** (อ่าน) |
| IC-PERM-02 | User ที่มี `.execute` คลิก **Close period** | **Allow** — นี่คือ mutation เดียวในโมดูล (map ไปยัง `TC-PE-010002` / `TC-PE-040003` ซึ่งเป็นคู่ denial สำหรับ users ที่ไม่มี keys) |
| IC-PERM-03 | User ที่ไม่มี period-end keys navigate ไปยัง `/period-end` | **Deny** — route guard redirect/block ตาม permission catalogue (describes เรื่อง permission-denial ใน `900-period-end.spec.ts`) |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| IC-VAL-01 | Close ถูก block โดยเอกสาร | PR/PO/SR ใด ๆ ที่ `in_progress` กลาง workflow, GRN/CN ในสถานะกลางทาง หรือ required location ที่ยังไม่ได้นับ | ปุ่ม disabled; ถ้า force เรียก API จะ return `` `Cannot close period: incomplete documents {"pr":…}` `` พร้อมจำนวนต่อประเภท |
| IC-VAL-02 | Race ของ concurrency | สอง sessions close พร้อมกัน | ผู้เรียกคนที่สองได้ `` `Period already closed` `` (re-check ด้วย `FOR UPDATE`) |
| IC-VAL-03 | Blocker ที่มาช้า | เอกสารที่ block ถูกสร้างหลังหน้า review โหลดแต่ก่อนการคลิก | การ re-validate ภายใน transaction reject ด้วย error incomplete-documents — หน้าจอเขียวที่ stale ไม่ชนะ |
| IC-VAL-04 | ไม่มีงวดปัจจุบัน | ไม่มีงวด `open`/`locked` อยู่ | หน้า list แสดง empty state แบบ no-current-period (`TC-PE-010004`); review/close ใช้ไม่ได้ |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| IC-EDGE-01 | Quirk โมดูลว่าง | ไม่มีเอกสารของประเภทหนึ่ง ๆ ในงวดเลย | Frontend card คำนวณ `is_complete = count > 0 && …` → render เป็น **incomplete** และคง Close disabled แม้ backend gate จะนับ blockers เป็นศูนย์ FE/BE discrepancy ที่ทราบสำหรับงวดว่าง |
| IC-EDGE-02 | GRN draft ในงวด | GRN ยังอยู่ที่ `draft` | **ไม่** block การ close ฝั่ง backend (`draft ∈` pass-list ของ GRN); แต่ review card นับมันเทียบกับ `GRN_COMPLETE = {committed, voided}` — mismatch เรื่องความเข้มงวดระดับ card อีกจุด |
| IC-EDGE-03 | Spot checks ยังค้างอยู่ | Spot checks ยังไม่เสร็จตอนสิ้นเดือน | Close ดำเนินต่อ — spot check ไม่ใช่ gate (`validatePeriodEnd` ไม่มี validator ของ spot-check) |
| IC-EDGE-04 | งวดปัจจุบัน locked | Period service ตั้ง `status = locked` | `findCurrent` ยัง return งวดนั้น (`status ∈ {open, locked}`); card render งวดนั้นและการ close รันต่อมันได้ |
| IC-EDGE-05 | การข้ามปี | ปิด fiscal month 12 | `ensureNextPeriod` สร้าง month 1 ของ fiscal year ถัดไป (`period` = `YYMM` ถัดไป) |

## 5. แหล่งอ้างอิง

- User flow: [03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller); screen reference: [period-end](/th/inventory/inventory/period-end)
- Business rules: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_POST_009`/`INV_POST_010`, `INV_CALC_008`/`INV_CALC_009`, `INV_AUTH_008`
- E2E: `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` (TC-PE-01xxxx รันได้; TC-PE-02/03/04xxxx "Feature pending")
- Backend specs: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/*.spec.ts`
