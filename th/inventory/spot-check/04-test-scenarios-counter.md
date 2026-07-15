---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios — หน้า Entry & Review
description: Test case หน้า entry และ review สำหรับโมดูลการสุ่มตรวจ
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios — หน้า Entry & Review

> **At a Glance**
> **หน้าจอ:** `spot-check/:id` (`sc-entry-component.tsx`), `spot-check/:id/review` (`sc-review-component.tsx`) &nbsp;·&nbsp; **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **Role:** role เดียวกับ [04-test-scenarios-inventory-controller.md](/th/inventory/spot-check/04-test-scenarios-inventory-controller)
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `spot-check`; scenario เป็นการครอบคลุม manual/planned cross-reference กับ row `TC-SPC-06*`/`TC-SPC-07*` ของ `docs/test-cases/760-spot-check.md`

## 1. ขอบเขต

Scenario ด้านล่างใช้ action ที่ catalogue ใน [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter) § 3 — การป้อนบรรทัด notes import/export Save For Resume, Submit For Review และ Submit ขั้นสุดท้าย

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| E-F-01 | ป้อน `actual_qty` บนบรรทัด | สถานะใดก็ได้ | ค่า commit เข้า local state; ตัวชี้วัด "counted" ปรากฏ ตรงกับ `TC-SPC-060001` |
| E-F-02 | Filter pill All/Counted/Uncounted | มีบรรทัดที่นับแล้วและยังไม่นับผสมกัน | รายการแคบลงตาม filter ที่เลือก; ตัวนับบน pill ตรงกัน ตรงกับ `TC-SPC-060002` |
| E-F-03 | แนบ note และ photo ให้บรรทัด | เวลาใดก็ได้ | `POST /spot-check-detail-comment/:detailId` สร้าง `tb_spot_check_detail_comment` row พร้อมข้อความและ attachment ตรงกับ `TC-SPC-060003` |
| E-F-04 | ใช้ calculator คำนวณ total | สินค้ามี case/unit conversion | Calculator return total เขียนเข้า `actual_qty` ของบรรทัด ตรงกับ `TC-SPC-060003` |
| E-F-05 | "Set X Empty to Zero" | มีบรรทัดยังไม่นับอยู่ | ทุกบรรทัดที่ยังไม่นับกลายเป็น `0` ในเครื่องและนับเป็น counted; footer สลับเป็น Submit For Review เมื่อ `uncountedCount = 0` ตรงกับ `TC-SPC-060004` |
| E-F-06 | Save For Resume ด้วยการนับบางส่วน | บางบรรทัดมีค่า บางบรรทัดไม่มี | `PATCH .../save` stamp `counted_at`/`counted_by_id` บนบรรทัดที่ส่ง; call แรกยังพลิก `pending → in_progress`; navigate กลับหน้ารายการ ตรงกับ `TC-SPC-060001` |
| E-F-07 | Submit For Review เมื่อทุกบรรทัดมีค่าแล้ว | `uncountedCount === 0` | `PATCH .../review` คำนวณ `on_hand_qty`/`diff_qty` ใหม่ทุกบรรทัดจากยอด ledger สด; navigate ไป `/review` ตรงกับ `TC-SPC-070001` |
| E-F-08 | หน้า review แสดง tile สรุปถูกต้อง | บางบรรทัด match บางบรรทัด overage บางบรรทัด shortage | Tile Matches/Variances/Overages/Shortages ตรงกับ `diff_qty` แต่ละบรรทัด; variance ลบแสดงสีเตือน บวกแสดงสีสำเร็จ ตรงกับ `TC-SPC-070002` |
| E-F-09 | Submit Spot Check (ขั้นสุดท้าย) | อยู่บนหน้า review | `PATCH .../submit` ตั้ง `doc_status = completed`; navigate กลับหน้ารายการ; ไม่มีเอกสารอื่นถูกสร้าง ตรงกับ `TC-SPC-070003` |
| E-F-10 | Export ยอดนับปัจจุบัน | เวลาใดก็ได้ | ไฟล์ `.xlsx` ดาวน์โหลดพร้อม id, รหัส/ชื่อ/ชื่อท้องถิ่น/SKU สินค้า, หน่วย, และ `actual_qty` ปัจจุบันต่อแถว |
| E-F-11 | Import ยอดนับจาก spreadsheet | ไฟล์ที่มี SKU ตรงกัน | แถวที่ match เติมค่าในเครื่องของบรรทัดนั้น; toast รายงานจำนวน matched/total/skipped |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| E-R-01 | ผู้ใช้ที่ไม่มี `inventory_management.spot_check` เปิด `:id` โดยตรง | ไม่มี permission | ถูกปฏิเสธการเข้าถึงตามกลไก permission-gate ทั่วไป; ไม่มีข้อจำกัด location หรือการมอบหมายเฉพาะโมดูลให้ทดสอบเพิ่ม |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| V-01 | `SPC_VAL_007` | พยายาม Save บนเอกสารที่ `completed` หรือ `void` | `"Cannot save items when spot check is <status>"` |
| V-02 | `SPC_VAL_007` | Save ด้วย array `items[]` ว่างเปล่า (เช่น เรียก API ตรงโดยไม่มี payload) | `SPOT_CHECK_NO_ITEMS` ("No items to save") |
| V-03 | `SPC_VAL_008` | คลิก Submit Spot Check สองครั้งติดกัน (ครั้งที่สองหลังครั้งแรกสำเร็จแล้ว) | Call ที่สองถูก reject ด้วย `"Spot check is already completed"` |
| V-04 | (doc_version) | Save/Review ด้วย `doc_version` ที่ stale (เช่น tab ที่สองที่ยังไม่ fetch ใหม่หลัง save อื่น) | Update ไม่ match และถูก reject; client ต้อง reload และ retry |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| E-E-01 | Submit ทั้งที่มีบรรทัดยังไม่นับ | ทั้ง Submit For Review และ Submit ขั้นสุดท้ายสำเร็จเสมอ — ไม่มีการตรวจความครบถ้วนฝั่ง server (`SPC_VAL_008`); บรรทัดที่ยังไม่นับแค่พก `diff_qty` แบบ shortage เต็มเข้าสู่ review |
| E-E-02 | เปิด spot check ที่ `completed` แล้วจาก tab History แล้วกดต่อไป Submit For Review อีกครั้ง | `reviewItems()` ไม่มี guard สถานะและจะเขียนทับ `on_hand_qty`/`actual_qty`/`diff_qty`/`counted_at` บนทุกแถว detail; มีเพียง call Submit ขั้นสุดท้ายถัดไปเท่านั้นที่ถูกบล็อก (`"Spot check is already completed"`) |
| E-E-03 | เปิด spot check ที่ `void` จาก tab History | เหมือนข้างต้น — `reviewItems()` ดำเนินไปโดยไม่มี error แม้เอกสารจะ void แล้ว; Submit ขั้นสุดท้ายถูกบล็อกแยกต่างหากด้วย `"Void spot check cannot be submitted"` |
| E-E-04 | Counter สองคนแก้ไข spot check เดียวกันพร้อมกัน | ผู้ใช้ใดก็ตามที่มี permission ของโมดูลแก้ไขบรรทัดใดบน spot check ใดก็ได้ (ไม่มี location-scoping) — last-write-wins ต่อบรรทัดตอน Save ไม่มี conflict อื่นนอกจาก `doc_version` ที่ stale บนระดับ header |
| E-E-05 | ทุกบรรทัด reconcile เป็น variance ศูนย์ | Submit ขั้นสุดท้ายสำเร็จ; ไม่มีเอกสารใด ๆ ถูกสร้างไม่ว่าผล variance จะเป็นอย่างไร — โมดูลนี้ไม่เคย post ไปที่ไหนเลย ไม่ว่า match หรือไม่ |
| E-E-06 | Import match ได้บางส่วน | Toast รายงานจำนวนที่ skip; บรรทัดที่ไม่ match คงเดิมทุกอย่าง |

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/sc-entry-component.tsx`, `sc-review-component.tsx`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (`saveItems`, `reviewItems`, `getReview`, `submit`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; manual test-case catalog ที่ `docs/test-cases/760-spot-check.md` (`TC-SPC-06*`/`TC-SPC-07*`)
- ที่เกี่ยวข้อง: [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter), [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) (`SPC_VAL_007`–`008`, `SPC_POST_001`–`004`), [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) (scenario end-to-end)
