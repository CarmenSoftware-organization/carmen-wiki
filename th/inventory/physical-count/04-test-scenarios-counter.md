---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Counter
description: Test case ของ Counter / Store Keeper สำหรับโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-05-19T23:55:00.000Z
tags: physical-count, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Counter

> **At a Glance**
> **Persona:** Counter (Counter / Store Keeper) &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **Scenario:** ~30 (skeleton)
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `physical-count` ที่ `../carmen-inventory-frontend-e2e/`; scenario เป็น manual / planned

## 1. ขอบเขต Persona

**Counter** = Counter / Store Keeper พนักงานพื้นที่ที่ป้อน `actual_qty` ต่อบรรทัดใน zone ที่ได้รับมอบหมาย flag รายการเสียหาย / ไม่มีป้าย และเซ็นปิด zone ที่เสร็จ Scenario ด้านล่างใช้ action ที่ catalogue ใน [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter) หัวข้อ 3 — การเปิด sheet ที่ได้รับมอบหมาย, การป้อนการนับ, การ flag รายการ, การเพิ่ม comment, การเซ็นปิด zone Authority anchor `PHC_AUTH_002`

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| C-F-01 | เปิด count sheet ที่ได้รับมอบหมาย | Counter มี zone-grant; เอกสาร count อยู่ `pending` | บรรทัด zone-scoped มองเห็น; `on_hand_qty` (book) ซ่อนถ้านโยบาย blind-count ของ tenant เปิด |
| C-F-02 | ป้อน `actual_qty` แรกบนบรรทัด | เอกสาร count อยู่ `pending`; counter มี zone-grant | เอกสาร count เลื่อนไป `in_progress`; stamp `start_counting_at` / `start_counting_by_id` บน `tb_physical_count` |
| C-F-03 | ป้อน `actual_qty` ตรงกับ `on_hand_qty` | บรรทัดใน zone ของ counter | `actual_qty` บันทึก; `diff_qty = 0`; stamp `counted_at` / `counted_by_id` บน `tb_physical_count_detail` |
| C-F-04 | ป้อน `actual_qty` > `on_hand_qty` (overage) | บรรทัดใน zone ของ counter | `actual_qty` บันทึก; `diff_qty > 0`; บรรทัดภายใน tolerance band ถ้ามี |
| C-F-05 | ป้อน `actual_qty` < `on_hand_qty` (shortage) | บรรทัดใน zone ของ counter | `actual_qty` บันทึก; `diff_qty < 0`; บรรทัด eligible สำหรับการตรวจ tolerance ระดับ Count Lead |
| C-F-06 | ป้อน `actual_qty = 0` (ศูนย์บนชั้น) | บรรทัดที่ `on_hand_qty > 0` | `actual_qty = 0` บันทึก; `diff_qty = -on_hand_qty` (shortage เต็ม); บรรทัด flag ระดับ Count Lead ถ้าเกิน threshold |
| C-F-07 | Flag รายการเสียหาย / ไม่มีป้าย / ไม่คุ้นเคย | บรรทัดใน zone ของ counter | สร้าง `tb_physical_count_detail_comment` row พร้อม attachment photo; แจ้ง Count Lead |
| C-F-08 | เพิ่ม comment ระดับ count | เอกสารอยู่ `in_progress` | สร้าง `tb_physical_count_comment` row (เช่น `"zone B นับครบ รอตรวจสอบ bin re-stock"`) |
| C-F-09 | แก้ไขบรรทัดของตนก่อน submit | Counter ป้อน `actual_qty` ไว้ก่อนหน้า | `actual_qty` อัปเดต; `counted_at` re-stamp; audit log เก็บค่าก่อนหน้าผ่าน thread comment |
| C-F-10 | เซ็นปิด zone ที่เสร็จ | ทุกบรรทัด zone มี `actual_qty` ไม่เป็น null | Notification ยิงไปยัง Count Lead; counter submit เอกสารไม่ได้ |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| C-R-01 | Counter พยายามป้อนบรรทัดนอก zone | Counter มี zone-grant สำหรับ zone A; พยายามแก้ไขบรรทัด zone B | Reject ตาม `PHC_AUTH_004` พร้อม error zone-scope |
| C-R-02 | Counter พยายาม submit เอกสาร count | ทุกบรรทัด zone นับแล้ว; Counter คลิก submit | Action submit ไม่มีให้ Counter ตาม `PHC_AUTH_002`; UI ชี้แนะ counter ให้ "เซ็นปิด zone" เท่านั้น |
| C-R-03 | Counter พยายามแก้ไขเอกสาร `completed` | เอกสารอยู่ `completed` | แก้ไข reject ตาม `PHC_VAL_008` (immutable) |
| C-R-04 | Counter ไม่มี zone-grant พยายามดู sheet | Counter มี role Counter แต่ไม่มี zone-grant ที่ location | เอกสารไม่มองเห็นใน "การมอบหมายการนับของฉัน"; การเข้าถึง URL ตรงถูก reject |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| C-V-01 | `PHC_VAL_005` | Counter ป้อน `actual_qty` ติดลบ | `"Counted quantity must be zero or positive."` |
| C-V-02 | `PHC_VAL_005` | Counter ป้อน `actual_qty` ไม่ใช่ตัวเลข | Input ถูก reject ที่ระดับ form ด้วย type error |
| C-V-03 | `PHC_VAL_004` (Count Lead facing) | Counter ปล่อยบรรทัดว่าง (ไม่ป้อน `actual_qty` เลย) | ตอน Count Lead submit เอกสารบล็อกด้วย `"Cannot submit count — <N> of <M> lines remain uncounted."` Counter ต้องป้อนค่า |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| C-E-01 | Recount บรรทัดของตน — reject | Counter A ต้นฉบับพยายามป้อน recount บนบรรทัดที่ flag | Recount ต้องทำโดย counter คนละคน; UI ป้องกันการ re-entry โดย `counted_by_id` เดียวกัน |
| C-E-02 | Mobile / handheld scanner barcode ไม่ตรง | Counter scan barcode ที่ไม่ตรงกับ `product_code` ของบรรทัด | Scanner UI reject; counter ต้องหาบรรทัดที่ถูกหรือ flag เป็นไม่คุ้นเคย |
| C-E-03 | เครือข่ายหลุดระหว่างการนับ | Counter เสียการเชื่อมต่อขณะป้อน `actual_qty` | Local cache เก็บการป้อน; sync resume เมื่อ reconnect; idempotent retry |
| C-E-04 | Counter สองคนบน zone เดียวกัน (ขนาน) | Counter สองคนแชร์ zone-grant บน `tb_physical_count` เดียวกัน | Last-write-wins ต่อบรรทัด; thread comment แสดง action ของ counter ทั้งสองคนใน audit log |
| C-E-05 | Counter มอบหมายให้หลาย zone | Counter เดียวกัน, สอง zone-grant บนเอกสารเดียวกัน | Counter เห็นทั้งสอง zone; ป้อนได้อิสระข้าม zone |
| C-E-06 | การนับโหมด frozen — counter เห็นธุรกรรมที่ถูกบล็อก | การพยายามรับสดที่ location ที่นับถูกบล็อกตาม `PHC_VAL_006`; counter ทราบแต่ไม่ถูกบล็อกจากการนับต่อ | Counter ทำการนับต่อปกติ; พื้นที่รับแสดง lock จนการนับ complete |

## 6. Configuration / Audit-Trail

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| C-C-01 | นโยบาย blind-count ของ tenant | `on_hand_qty` ซ่อนจากมุมมอง counter; แสดงเฉพาะสินค้า UoM และ `actual_qty` ว่าง | Counter ไม่สามารถ bias การป้อนกับ book; มุมมอง Count Lead เก็บ `on_hand_qty` |
| C-C-02 | Audit log per-line counted-by stamp | ทุกบรรทัดป้อน | `tb_physical_count_detail.counted_by_id` และ `counted_at` เติม; audit trail ครบ |
| C-C-03 | Thread comment พร้อม attachment photo | Counter flag รายการเสียหายด้วย photo จากโทรศัพท์ | `tb_physical_count_detail_comment.attachments` พกพา `[{originalName, fileToken, contentType}]` |

> **TODO:** ขยายทุก row ด้วยข้อความ error และ assertion พฤติกรรม UI เมื่อ source frontend / E2E ถูกเขียน Cross-link ไป scenario ฝั่ง cmobile ถ้า PWA เป็นเจ้าของ UI counter

## 7. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — source ของพฤติกรรม UI Counter; ตรวจ `../cmobile/` สำหรับการ implement count sheet ฝั่ง PWA ถ้ามี
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ที่เกี่ยวข้อง: [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_AUTH_002`, `PHC_AUTH_004`, `PHC_VAL_004`–`PHC_VAL_005`), [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) (scenario handoff ข้าม persona)
