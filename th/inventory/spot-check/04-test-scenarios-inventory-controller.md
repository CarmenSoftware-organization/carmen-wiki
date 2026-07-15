---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios — หน้ารายการ & สร้าง
description: Test case หน้ารายการและหน้าสร้างสำหรับโมดูลการสุ่มตรวจ
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, inventory-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios — หน้ารายการ & สร้าง

> **At a Glance**
> **หน้าจอ:** `spot-check` (`sc-component.tsx`), `spot-check/location/:location_id` (`sc-form.tsx`) &nbsp;·&nbsp; **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **Role:** ผู้ใช้ใดก็ตามที่มีสิทธิ์ `inventory_management.spot_check` (role เดียวกับ [04-test-scenarios-counter.md](/th/inventory/spot-check/04-test-scenarios-counter))
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `spot-check`; scenario เป็นการครอบคลุม manual/planned cross-reference กับ row `TC-SPC-01*`/`TC-SPC-03*` ของ `docs/test-cases/760-spot-check.md`

## 1. ขอบเขต

Scenario ด้านล่างใช้ action ที่ catalogue ใน [spot-check/03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller) § 3 — รายการ Locations/History และการสร้าง spot check ผ่านทั้งสาม sampling method

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| L-F-01 | โหลดหน้ารายการ (มุมมอง Locations) | ผู้ใช้ใดก็ได้ที่มี permission ของโมดูล | KPI tiles (All/Resume/Not Started) และ card ตำแหน่ง render ภายในเวลาโหลดหน้าปกติ ตรงกับ `TC-SPC-010001` |
| L-F-02 | สลับไปมุมมอง History | บนหน้ารายการ | มุมมองสลับไปเป็นรายการ spot check ที่เคยสร้างทั้งหมด แบ่งหน้า สถานะใดก็ได้ ตรงกับ `TC-SPC-010002` |
| L-F-03 | Filter ตาม KPI tile | คลิก tile "Resume" | เหลือเฉพาะตำแหน่งที่มี spot check `pending`/`in_progress` ตรงกับ `TC-SPC-010003` |
| L-F-04 | ค้นหาตามชื่อ/รหัสตำแหน่ง | พิมพ์คำที่ตรงบางส่วน | รายการแคบลงฝั่ง client ตรงกับ `TC-SPC-010004` |
| L-F-05 | Include Not Count | ติ๊ก "Include Not Count" | ตำแหน่งที่ flag `physical_count_type = no` ถูกเพิ่มเข้ารายการ ตรงกับ `TC-SPC-010006` |
| L-F-06 | เริ่ม spot check — Random | ตำแหน่งไม่มี spot check ค้าง; `items ≥ 1` | `POST /spot-checks` สำเร็จ; เอกสารสร้างที่ `pending` พร้อม `size` แถวสุ่ม; navigate ไป `/:id` ตรงกับ `TC-SPC-030002` |
| L-F-07 | เริ่ม spot check — High Value | เหมือนกัน บวก `items ≥ 1` และมีงวดบัญชีที่เปิด/ล็อกอยู่ | เอกสารสร้างพร้อมสินค้า top-`items` ตามการจัดอันดับมูลค่า ตรงกับ `TC-SPC-030003` |
| L-F-08 | เริ่ม spot check — Manual | เหมือนกัน บวกเลือกสินค้าอย่างน้อยหนึ่งผ่าน transfer picker | เอกสารสร้างพร้อมสินค้าที่เลือกตรงเป็นแถว detail ตรงกับ `TC-SPC-030004` |
| L-F-09 | Method picker สลับ field ที่แสดง | บนหน้าสร้าง คลิกแต่ละ method card | Random/High Value แสดงช่อง Items (High Value เพิ่ม Min Value); Manual แสดง product transfer picker แทน ตรงกับ `TC-SPC-030005` |
| L-F-10 | Product transfer (Manual) | Method = Manual | สินค้าย้ายระหว่างคอลัมน์ Available/Selected; ตัวนับอัปเดต; select-all และ empty-search state ทำงาน ตรงกับ `TC-SPC-030006` |
| L-F-11 | Resume ตำแหน่งที่กำลังดำเนิน | ตำแหน่งมี spot check `pending`/`in_progress` | Navigate ตรงไปยัง `/:id`; ไม่มีเอกสารใหม่สร้าง ตรงกับ `TC-SPC-060005` |
| L-F-12 | Reset spot check | ตำแหน่งมี spot check `pending`/`in_progress`; คลิก Reset, ยืนยัน | `doc_status → void`; แถว detail ไม่ถูกแตะ; ตำแหน่งกลับไปเป็น Not Started ตรงกับ `TC-SPC-060006` |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| L-R-01 | ผู้ใช้ที่ไม่มี `inventory_management.spot_check` เปิดหน้ารายการ | ไม่มี permission | ถูกปฏิเสธการเข้าถึงตามกลไก permission-gate ทั่วไปที่แชร์ทั้งผลิตภัณฑ์; ไม่มี override เฉพาะโมดูล ตรงกับ `TC-SPC-100001` |
| L-R-02 | ผู้ใช้ที่ไม่ได้ login เปิดหน้ารายการโดยตรง | ไม่มี session | Redirect ไปยัง `/login` ตรงกับ `TC-SPC-100002` |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| L-V-01 | `SPC_VAL_002` | เริ่ม spot check สำหรับตำแหน่งที่ eligible product pool ว่างเปล่า | `"No products found at this location"` |
| L-V-02 | `SPC_VAL_003` | Method = Manual; ปล่อย Products Selected ว่าง; คลิก Create | Error ฝั่ง client ใต้ product transfer ("ต้องเลือกอย่างน้อยหนึ่งสินค้า"); backend จะ reject ด้วย `"product_id is required for manual selection"` เช่นกัน ตรงกับ `TC-SPC-200002` |
| L-V-03 | (client) | Method = Random หรือ High Value; ปล่อย Items ที่ `0`; คลิก Create | Error ฝั่ง client บังคับ `items ≥ 1` ตรงกับ `TC-SPC-200001` |
| L-V-04 | (client) | Method = High Value; กรอก Min Value ติดลบ; คลิก Create | Error ฝั่ง client บังคับ `min_value ≥ 0` ตรงกับ `TC-SPC-200003` |
| L-V-05 | `SPC_VAL_004` | Method = High Value; ไม่มี `tb_period` ที่ `status ∈ {open, locked}` | `SPOT_CHECK_NO_ACTIVE_PERIOD` ("No active period found") |
| L-V-06 | `SPC_VAL_006` | คลิก Reset บน spot check ที่เป็น `void` หรือ `completed` อยู่แล้ว — เข้าถึงไม่ได้ผ่าน UI ที่ shipped (Reset render เฉพาะสำหรับรายการ `pending`/`in_progress`) แต่การ retry API ตรงจะเจอสิ่งนี้ | `"Spot check is already void"` / `"Completed spot check cannot be reset"` |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| L-E-01 | Manual selection รวมสินค้านอก eligible pool ของตำแหน่ง | ถ้าเป็นสินค้าเดียวที่เลือก การสร้างล้มเหลวด้วย `"None of the selected products were found at this location"` (`SPC_VAL_003`); ผสมกับสินค้าที่ valid ก็ถูกทิ้งเงียบ ๆ |
| L-E-02 | เริ่ม spot check สองครั้งติดกันสำหรับตำแหน่งเดียวกัน | สร้างเอกสาร `tb_spot_check` อิสระสองฉบับ (ต่างจาก idempotent resume path ของ physical-count — ไม่มีการตรวจ duplicate เทียบเท่าใน `create()` ของ `spot-check.service.ts`) ทั้งคู่จะแสดงใต้ section Resume ของตำแหน่งนั้น แม้ UI จะโชว์แค่ตัวล่าสุดตัวเดียว |
| L-E-03 | Reset แล้วเริ่มใหม่ทันที | Reset ทำให้เอกสารเก่าเป็น void; Start สร้างฉบับใหม่พร้อมตัวอย่างใหม่ — ทั้งสองเป็นอิสระต่อกันโดยสิ้นเชิง ไม่มีข้อมูลใดถูก carry ต่อ |

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/sc-component.tsx`, `sc-form.tsx`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (`create`, `reset`, `findCurrentByLocation`), `spot-check.logic.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; manual test-case catalog ที่ `docs/test-cases/760-spot-check.md` (`TC-SPC-01*`/`TC-SPC-03*`/`TC-SPC-06*`/`TC-SPC-10*`/`TC-SPC-20*`)
- ที่เกี่ยวข้อง: [spot-check/03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller), [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) (`SPC_VAL_001`–`004`, `SPC_VAL_006`, `SPC_AUTH_001`), [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) (scenario end-to-end)
