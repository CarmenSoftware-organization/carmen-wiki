---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Count Lead
description: Test case ของ Count Lead (Inventory Controller / Manager) สำหรับโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-05-19T23:55:00.000Z
tags: physical-count, test-scenarios, count-lead, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Count Lead

> **At a Glance**
> **Persona:** Count Lead (Inventory Controller / Inventory Manager) &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **Scenario:** ~30 (skeleton)
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `physical-count` ที่ `../carmen-inventory-frontend-e2e/`; scenario เป็น manual / planned

## 1. ขอบเขต Persona

**Count Lead** = Inventory Controller / Inventory Manager เจ้าของการดำเนินการ scenario ด้านล่างใช้ action ที่ catalogue ใน [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead) หัวข้อ 3 — การสร้าง period และเอกสาร, การเลือกโหมด, การมอบหมาย counter, การติดตามความคืบหน้า, การแก้ไข flag recount, การ override / accept variance, submit และการ route rollup Authority anchor `PHC_AUTH_001`

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| CL-F-01 | เปิด count period | `tb_period` เป็น `open` ตาม `INV_VAL_008`; ไม่มี `tb_physical_count_period` สำหรับ period นี้ | `tb_physical_count_period` ใหม่ใน `draft`; มองเห็นใน period scheduler |
| CL-F-02 | สร้าง count sheet สำหรับ location เดียว (โหมด frozen) | Period อยู่ `draft` หรือ `counting`; location เป้าหมายเป็น inventory-type | `tb_physical_count` ใหม่ใน `pending`; `physical_count_type = yes`; จับ on-hand snapshot ต่อสินค้า; `product_total > 0` |
| CL-F-03 | สร้าง count sheet (โหมด live) | เหมือน CL-F-02 | `tb_physical_count` ที่ `physical_count_type = no`; อนุญาตการเขียน inventory ขนานตาม `PHC_VAL_006` |
| CL-F-04 | มอบหมาย counter ให้ zone | เอกสาร count อยู่ `pending`; counter มีอยู่ | บันทึก counter zone-grant; counter เห็นการมอบหมายใน "การมอบหมายการนับของฉัน" |
| CL-F-05 | ติดตามความคืบหน้าสด | เอกสาร count อยู่ `in_progress` | `product_counted` / `product_total` มองเห็นและอัปเดต; `PHC_CALC_004` ถูกต้อง |
| CL-F-06 | Flag บรรทัด variance ให้ recount | บรรทัดที่ `|diff_qty| / on_hand_qty` เกิน threshold ตาม `PHC_VAL_007` | Detail-comment พร้อม tag recount; submit ถูกบล็อกจนกว่า flag recount จะถูกแก้ไข |
| CL-F-07 | Override / accept variance พร้อม countersignature | Recount ยืนยันการนับเดิม; ไม่สามารถสืบสวน variance เพิ่ม | Flag ถูกเคลียร์; บรรทัด eligible สำหรับ rollup; thread comment พกพา countersignature ของ override stamp ด้วย `created_by_id` |
| CL-F-08 | Submit count — ทุกบรรทัดนับ ไม่มี flag เปิด | `product_counted == product_total`; ไม่มี flag `PHC_VAL_007` เปิด | `tb_physical_count.status = completed`; rollup `tb_stock_in` (overage) และ/หรือ `tb_stock_out` (shortage) สร้างพร้อม `info.countId` |
| CL-F-09 | Route rollup adjustment ไปอนุมัติ | Rollup adjustment ใน `draft` (หรือ `in_progress` ถ้า auto-approve) | Adjustment มองเห็นในคิว Approver / Finance ตาม `ADJ_AUTH_*` |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| CL-R-01 | ผู้ใช้ที่ไม่ใช่ Count Lead พยายามเปิด period | User ไม่มี role Count Lead พยายามสร้าง `tb_physical_count_period` | Reject ตาม `PHC_AUTH_001` |
| CL-R-02 | Count Lead ไม่มีขอบเขตที่ location | Role Count Lead กำหนดแต่ไม่มี `tb_user_location` สำหรับ location เป้าหมาย | การสร้าง sheet ถูก reject พร้อม error ขอบเขต |
| CL-R-03 | พยายามข้าม tenant | Count Lead จาก tenant A พยายามดำเนินการบน period ของ tenant B | Reject ที่ชั้น API auth (multi-tenancy guard) |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| CL-V-01 | `PHC_VAL_001` | สร้าง `tb_physical_count` สำหรับ period ที่เป็น `completed` | `"Cannot add count to a completed period."` |
| CL-V-02 | `PHC_VAL_002` | พยายามเปลี่ยน `physical_count_type` เมื่อเอกสารเป็น `in_progress` | `"Cannot change mode on a started count."` |
| CL-V-03 | `PHC_VAL_003` | เป้าหมาย location ประเภท direct-cost สำหรับการสร้าง count sheet | `"Direct-cost locations cannot be physically counted."` |
| CL-V-04 | `PHC_VAL_004` | Submit ด้วยบรรทัดที่ยังไม่นับ | `"Cannot submit count — <N> of <M> lines remain uncounted."` |
| CL-V-05 | `PHC_VAL_007` | Submit ด้วยบรรทัดที่ flag recount เปิดอยู่ | `"Cannot submit — <K> variance line(s) await recount resolution."` |
| CL-V-06 | `PHC_VAL_008` | พยายามแก้ไขเอกสาร count ที่เป็น `completed` | `"Cannot edit a completed count. Raise a manual inventory adjustment."` |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| CL-E-01 | Counter มอบหมายระหว่างการนับให้ zone ที่นับไปแล้วบางส่วน | Counter เห็นบรรทัดที่นับแล้วของ zone ตน (read-only) บวกบรรทัดที่ยังไม่นับ (editable) |
| CL-E-02 | Tolerance threshold แน่นขึ้นระหว่างการนับ | การนับที่กำลังดำเนินใช้ threshold ที่ snapshot ที่ sheet-gen; การนับใหม่ใช้ threshold ใหม่ |
| CL-E-03 | พยายาม submit ขนาน (Count Lead คลิก submit สองครั้ง) | Submit ครั้งที่สอง no-op (idempotent); rollup สร้างครั้งเดียว; audit log แสดง submit ครั้งเดียว |
| CL-E-04 | บรรทัด variance ทั้งหมด reconcile ภายใน tolerance | ไม่สร้าง rollup adjustment (ทุก `diff_qty = 0` หรือต่ำกว่า tolerance + ภายในศูนย์); เอกสาร `completed` ไม่มี downstream effect |
| CL-E-05 | การนับข้ามเที่ยงคืน / ขอบ period | `start_counting_at` และ `completed_at` คร่อมวันที่; การตรวจ period-containment ใช้วันที่ complete การนับ |

## 6. Configuration / Audit-Trail

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| CL-C-01 | Count Lead เปลี่ยนการมอบหมาย counter ระหว่างการนับ | Counter ใหม่เห็น zone; counter ก่อนสูญสิทธิ์แก้ไขบน zone (read-only audit) |
| CL-C-02 | Audit log จับทุก state transition + comment | ประวัติ `tb_physical_count.status` + thread `tb_physical_count_comment` อ่านได้ครบ; `created_by_id` / `counted_by_id` เติม |
| CL-C-03 | การ verify การ link rollup | `tb_stock_in.info.countId` และ `tb_stock_out.info.countId` อ้างอิง `tb_physical_count.id` ต้นทาง |

> **TODO:** ขยายทุก row ด้วย assertion ฟิลด์ `tb_*` ชัดเจนและข้อความ error ที่คาดหวังเมื่อ source frontend / E2E ถูกเขียน Cross-link ไป spec E2E เมื่อ `physical-count.spec.ts` ถูกเพิ่มที่ `../carmen-inventory-frontend-e2e/tests/`

## 7. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — source ของพฤติกรรม UI Count Lead
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ที่เกี่ยวข้อง: [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_AUTH_001`, `PHC_VAL_*`, `PHC_POST_*`), [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) (scenario handoff ข้าม persona)
