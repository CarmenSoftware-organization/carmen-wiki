---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios — Counter
description: Test case ของ Counter สำหรับโมดูลการสุ่มตรวจ
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios — Counter

> **At a Glance**
> **Persona:** Counter (การป้อนข้อมูลพื้นที่) &nbsp;·&nbsp; **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **Scenario:** ~26
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี — ยังไม่มี Playwright spec ของ spot-check ที่ `../carmen-inventory-frontend-e2e/tests/`

## 1. ขอบเขต Persona

**Counter** — พนักงานพื้นที่ที่ป้อน `actual_qty` ต่อบรรทัดบน spot check ที่ได้รับมอบหมาย flag รายการเสียหาย / ไม่มีป้าย และเซ็นปิด sheet ที่เสร็จ Scenario ด้านล่างใช้ action ที่ catalogue ใน [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter) หัวข้อ 3 — การเปิด sheet ที่ได้รับมอบหมาย, การป้อนการนับ, การ flag รายการ, การเพิ่ม comment, การเซ็นปิด completion Authority anchor `SPC_AUTH_002`

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| C-F-01 | เปิด spot-check sheet ที่ได้รับมอบหมาย | Counter มี location-grant; spot check อยู่ `pending` | บรรทัด detail มองเห็น; `on_hand_qty` (book) ซ่อนถ้านโยบาย blind-count ของ tenant เปิด (TODO ยืนยัน) |
| C-F-02 | ป้อน `actual_qty` แรกบนบรรทัด | Spot check อยู่ `pending`; counter มี location-grant | Spot check เลื่อนไป `in_progress` |
| C-F-03 | ป้อน `actual_qty` ตรงกับ `on_hand_qty` | บรรทัดบน spot check ที่ได้รับมอบหมาย | `actual_qty` บันทึก; `diff_qty = 0`; stamp `counted_at` / `counted_by_id` บน `tb_spot_check_detail` |
| C-F-04 | ป้อน `actual_qty` > `on_hand_qty` (overage) | บรรทัดบน spot check ที่ได้รับมอบหมาย | `actual_qty` บันทึก; `diff_qty > 0`; บรรทัดภายใน tolerance band ถ้ามี |
| C-F-05 | ป้อน `actual_qty` < `on_hand_qty` (shortage) | บรรทัดบน spot check ที่ได้รับมอบหมาย | `actual_qty` บันทึก; `diff_qty < 0`; บรรทัด eligible สำหรับการตรวจ tolerance ระดับ controller |
| C-F-06 | ป้อน `actual_qty = 0` (ศูนย์บนชั้น) | บรรทัดที่ `on_hand_qty > 0` | `actual_qty = 0` บันทึก; `diff_qty = -on_hand_qty` (shortage เต็ม); บรรทัด flag ระดับ controller ถ้าเกิน threshold |
| C-F-07 | Flag รายการเสียหาย / ไม่มีป้าย / ไม่คุ้นเคย | บรรทัดบน spot check ที่ได้รับมอบหมาย | สร้าง `tb_spot_check_detail_comment` row พร้อม attachment photo; แจ้ง Inventory Controller |
| C-F-08 | เพิ่ม comment ระดับ spot-check | Spot check อยู่ `in_progress` | สร้าง `tb_spot_check_comment` row (เช่น `"shelf restock กำลังดำเนิน แนะนำให้ recount บรรทัด 4"`) |
| C-F-09 | แก้ไขบรรทัดของตนก่อน submit | Counter ป้อน `actual_qty` ไว้ก่อนหน้า | `actual_qty` อัปเดต; `counted_at` re-stamp; audit log เก็บค่าก่อนหน้าผ่าน thread comment |
| C-F-10 | เซ็นปิด sheet ที่เสร็จ | ทุกบรรทัดมี `actual_qty` ไม่เป็น null | Notification ยิงไปยัง Inventory Controller; counter submit เอกสารไม่ได้ |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| C-R-01 | Counter พยายามป้อนบรรทัดนอก location | Counter มี location-grant สำหรับ Location A; พยายามแก้ไข spot check ของ Location B | Reject ตาม `SPC_AUTH_004` พร้อม error location-scope |
| C-R-02 | Counter พยายาม submit spot check | ทุกบรรทัดนับแล้ว; Counter คลิก submit | Action submit ไม่มีให้ Counter ตาม `SPC_AUTH_002`; UI ชี้แนะ counter ให้ "เซ็นปิด sheet" เท่านั้น |
| C-R-03 | Counter พยายามแก้ไข spot check ที่ `completed` | Spot check อยู่ `completed` | แก้ไข reject ตาม `SPC_VAL_007` (immutable) |
| C-R-04 | Counter ไม่มี location-grant พยายามดู sheet | Counter มี role Counter แต่ไม่มี location-grant | เอกสารไม่มองเห็นใน "การมอบหมาย spot-check ของฉัน"; การเข้าถึง URL ตรงถูก reject |
| C-R-05 | Counter พยายาม void spot check | Counter คลิก void | Action ไม่มี; เฉพาะ Inventory Controller ที่ void ได้ ตาม `SPC_AUTH_001` |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| C-V-01 | `SPC_VAL_005` | Counter ป้อน `actual_qty` ติดลบ | `"Counted quantity must be zero or positive."` |
| C-V-02 | `SPC_VAL_005` | Counter ป้อน `actual_qty` ไม่ใช่ตัวเลข | Input ถูก reject ที่ระดับ form ด้วย type error |
| C-V-03 | `SPC_VAL_004` (controller-facing) | Counter ปล่อยบรรทัดว่าง (ไม่ป้อน `actual_qty` เลย) | ตอน Inventory Controller submit เอกสารบล็อกด้วย `"Cannot submit spot check — <N> of <M> lines remain uncounted."` Counter ต้องป้อนค่า |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| C-E-01 | Recount บรรทัดของตน — ไม่แนะนำ | Counter A ต้นฉบับพยายามป้อน recount บนบรรทัดที่ flag | Convention: recount โดย counter คนละคน; UI อาจเตือนแต่ไม่ hard-block (TODO ยืนยัน) |
| C-E-02 | Mobile / handheld scanner barcode ไม่ตรง | Counter scan barcode ที่ไม่ตรงกับ `product_code` ของบรรทัด | Scanner UI reject; counter ต้องหาบรรทัดที่ถูกหรือ flag เป็นไม่คุ้นเคย |
| C-E-03 | เครือข่ายหลุดระหว่างการนับ | Counter เสียการเชื่อมต่อขณะป้อน `actual_qty` | Local cache เก็บการป้อน; sync resume เมื่อ reconnect; idempotent retry |
| C-E-04 | Counter สองคนบน spot check เดียวกัน (ขนาน) | Counter สองคนแชร์ location-grant บน `tb_spot_check` เดียวกัน | Last-write-wins ต่อบรรทัด; thread comment แสดง action ของ counter ทั้งสองคนใน audit log |
| C-E-05 | Spot check ถูก void ขณะ counter กำลังป้อน | Inventory Controller void; counter มีการป้อนที่ยังไม่บันทึก | การบันทึกต่อมา reject ด้วย `"Spot check is voided."`; การป้อนบางส่วนของ counter เก็บไว้จนถึงเวลา void |

## 6. Configuration / Audit-Trail

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| C-C-01 | นโยบาย blind-count ของ tenant (ถ้ามี) | `on_hand_qty` ซ่อนจากมุมมอง counter; แสดงเฉพาะสินค้า UoM และ `actual_qty` ว่าง | Counter ไม่สามารถ bias การป้อนกับ book; มุมมอง Inventory Controller เก็บ `on_hand_qty` (TODO ยืนยันว่านโยบาย tenant ใช้กับ spot-check) |
| C-C-02 | Audit log per-line counted-by stamp | ทุกบรรทัดป้อน | `tb_spot_check_detail.counted_by_id` และ `counted_at` เติม; audit trail ครบ |
| C-C-03 | Thread comment พร้อม attachment photo | Counter flag รายการเสียหายด้วย photo จากโทรศัพท์ | `tb_spot_check_detail_comment.attachments` พกพา `[{originalName, fileToken, contentType}]` |

> **TODO:** ขยายทุก row ด้วยข้อความ error และ assertion พฤติกรรม UI เมื่อ source frontend / E2E ถูกเขียน Cross-link ไป scenario ฝั่ง cmobile ถ้า PWA เป็นเจ้าของ UI counter ยืนยันการใช้นโยบาย blind-count สำหรับ spot-check

## 7. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — source ของพฤติกรรม UI Counter; ตรวจ `../cmobile/` สำหรับการ implement spot-check sheet ฝั่ง PWA ถ้ามี
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check
- ที่เกี่ยวข้อง: [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter), [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) (`SPC_AUTH_002`, `SPC_AUTH_004`, `SPC_VAL_004`–`SPC_VAL_005`), [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) (scenario handoff ข้าม persona), [physical-count/04-test-scenarios-counter](/th/inventory/physical-count/04-test-scenarios-counter) (scenario คู่เทียบการนับเต็ม)
