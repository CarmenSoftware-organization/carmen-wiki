---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios — Inventory Controller
description: Test case ของ Inventory Controller สำหรับโมดูลการสุ่มตรวจ
published: true
date: 2026-05-17T12:00:00.000Z
tags: spot-check, test-scenarios, inventory-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (เจ้าของการ spot-check) &nbsp;·&nbsp; **โมดูล:** [[spot-check]] &nbsp;·&nbsp; **Scenario:** ~29
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี — ยังไม่มี Playwright spec ของ spot-check ที่ `../carmen-inventory-frontend-e2e/tests/`

## 1. ขอบเขต Persona

**Inventory Controller** — เจ้าของการ spot-check Scenario ด้านล่างใช้ action ที่ catalogue ใน [[spot-check/03-user-flow-inventory-controller]] หัวข้อ 3 — การสร้าง spot-check ข้ามค่า `method` ทั้งสาม, การมอบหมาย counter, การติดตามความคืบหน้า, การแก้ไข flag recount, การ override / accept variance, submit, void และการ route rollup Authority anchor `SPC_AUTH_001`

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| IC-F-01 | เปิด spot check ด้วย random sampling | Location ประเภท inventory; `size = 10` | `tb_spot_check` ใหม่ใน `pending`; `method = random`; 10 row detail สุ่ม; จับ snapshot `on_hand_qty` ต่อบรรทัด |
| IC-F-02 | เปิด spot check ด้วย high-value sampling | Location ประเภท inventory; `size = 10` | `tb_spot_check` ใหม่ใน `pending`; `method = high_value`; top-10 ตามมูลค่า on-hand สุ่ม |
| IC-F-03 | เปิด spot check ด้วย manual selection | Location ประเภท inventory; controller เลือกสินค้า 3 รายการ | `tb_spot_check` ใหม่ใน `pending`; `method = manual`; 3 row detail เพิ่มชัดเจน |
| IC-F-04 | มอบหมาย counter | Spot check อยู่ `pending`; counter มี location-grant | Counter เห็นการมอบหมายใน "การมอบหมาย spot-check ของฉัน" |
| IC-F-05 | ติดตามความคืบหน้าสด | Spot check อยู่ `in_progress` | บรรทัดที่ `actual_qty` เติม vs รวมมองเห็น; `SPC_CALC_004` ถูกต้อง (derive ไม่ persist) |
| IC-F-06 | Flag บรรทัด variance ให้ recount | บรรทัดที่ `|diff_qty| / on_hand_qty` เกิน threshold ตาม `SPC_VAL_006` | Detail-comment พร้อม tag recount; submit บล็อกจนกว่า flag recount จะถูกแก้ไข |
| IC-F-07 | Override / accept variance พร้อม countersignature | Recount ยืนยันการนับเดิม; ไม่สามารถสืบสวน variance เพิ่ม | Flag เคลียร์; บรรทัด eligible สำหรับ rollup; thread comment พกพา countersignature ของ override stamp ด้วย `created_by_id` |
| IC-F-08 | Submit spot check — ทุกบรรทัดนับ ไม่มี flag เปิด | บรรทัด detail ทั้งหมดมี `actual_qty`; ไม่มี flag `SPC_VAL_006` เปิด | `doc_status = completed`; rollup `tb_stock_in` (overage) และ/หรือ `tb_stock_out` (shortage) สร้างพร้อม `info.spotCheckId` |
| IC-F-09 | Route rollup adjustment ไปอนุมัติ | Rollup adjustment ใน `draft` (หรือ `in_progress` ถ้า auto-approve) | Adjustment มองเห็นในคิว Approver / Finance ตาม `ADJ_AUTH_*` |
| IC-F-10 | Void spot check ก่อนนับ | Spot check อยู่ `pending` | `doc_status = void`; ไม่มี rollup; เก็บไว้สำหรับ audit |
| IC-F-11 | Void spot check ระหว่างการนับ | Spot check อยู่ `in_progress` ด้วยการป้อนบางส่วน | `doc_status = void`; การป้อนบางส่วนเก็บ; ไม่มี rollup |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| IC-R-01 | ผู้ใช้ที่ไม่ใช่ Inventory Controller พยายามเปิด spot check | User ไม่มี role พยายาม create | Reject ตาม `SPC_AUTH_001` |
| IC-R-02 | Inventory Controller ไม่มีขอบเขตที่ location | Role กำหนดแต่ไม่มี `tb_user_location` สำหรับเป้าหมาย | การสร้าง sheet reject พร้อม error ขอบเขต |
| IC-R-03 | พยายามข้าม tenant | Controller จาก tenant A พยายามดำเนินการบน spot check ของ tenant B | Reject ที่ชั้น API auth (multi-tenancy guard) |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| IC-V-01 | `SPC_VAL_001` | สร้าง `tb_spot_check` เทียบกับ location ประเภท direct-cost | `"Direct-cost locations cannot be spot-checked."` |
| IC-V-02 | `SPC_VAL_002` | Submit spot check `method = random` ด้วย `size = 0` | `"Sample size must be greater than zero for random / high_value methods."` |
| IC-V-03 | `SPC_VAL_002` | Submit spot check `method = manual` ด้วย row detail ศูนย์ | `"Manual spot check requires at least one product line before submit."` |
| IC-V-04 | `SPC_VAL_004` | Submit ด้วยบรรทัดที่ยังไม่นับ | `"Cannot submit spot check — <N> of <M> lines remain uncounted."` |
| IC-V-05 | `SPC_VAL_006` | Submit ด้วยบรรทัดที่ flag recount เปิดอยู่ | `"Cannot submit — <K> variance line(s) await recount resolution."` |
| IC-V-06 | `SPC_VAL_007` | พยายามแก้ไข spot check ที่เป็น `completed` | `"Cannot edit a completed spot check. Raise a manual inventory adjustment."` |
| IC-V-07 | `SPC_VAL_008` | พยายาม void spot check ที่เป็น `completed` | `"Cannot void a completed spot check — reverse via inventory adjustment."` |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| IC-E-01 | Sample สุ่ม `size` เกินสินค้าที่แตกต่างที่มีที่ location | Sample ถูกตัดตาม `SPC_VAL_003`; บันทึก log ส่วนต่างบน `tb_spot_check.info`; sheet สร้างด้วยจำนวนสินค้าที่มี |
| IC-E-02 | Tolerance threshold แน่นขึ้นระหว่าง spot-check | spot check ที่กำลังดำเนินใช้ threshold ที่ snapshot ที่ sheet-gen; spot check ใหม่ใช้ threshold ใหม่ |
| IC-E-03 | พยายาม submit ขนาน (Inventory Controller คลิก submit สองครั้ง) | Submit ครั้งที่สอง no-op (idempotent); rollup สร้างครั้งเดียว; audit log แสดง submit ครั้งเดียว |
| IC-E-04 | บรรทัด variance ทั้งหมด reconcile เป็นศูนย์ | ไม่สร้าง rollup adjustment (ทุก `diff_qty = 0`); เอกสาร `completed` ไม่มี downstream effect |
| IC-E-05 | High-value sample พร้อมค่าที่เสมอกัน | ผู้ตัดสิน tie-breaker โดย `product_code` ascending (หรือ tie-breaker ที่ tenant config) รับประกันการเลือกที่ deterministic |

## 6. Configuration / Audit-Trail

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| IC-C-01 | Inventory Controller เปลี่ยนการมอบหมาย counter ระหว่างการตรวจ | Counter ใหม่เห็น spot check; counter ก่อนสูญสิทธิ์แก้ไข (read-only audit) |
| IC-C-02 | Audit log จับทุก state transition + comment | ประวัติ `tb_spot_check.doc_status` + thread `tb_spot_check_comment` อ่านได้ครบ; `created_by_id` / `counted_by_id` เติม |
| IC-C-03 | การ verify การ link rollup | `tb_stock_in.info.spotCheckId` และ `tb_stock_out.info.spotCheckId` อ้างอิง `tb_spot_check.id` ต้นทาง |

> **TODO:** ขยายทุก row ด้วย assertion ฟิลด์ `tb_*` ชัดเจนและข้อความ error ที่คาดหวังเมื่อ source frontend / E2E ถูกเขียน Cross-link ไป spec E2E เมื่อ `spot-check.spec.ts` ถูกเพิ่มที่ `../carmen-inventory-frontend-e2e/tests/` ตรวจสอบการตั้งชื่อ reason-code (`SPOT_CHECK_*` vs `COUNT_*` ที่ใช้ซ้ำ) เมื่อกำหนด

## 7. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend/` — source ของพฤติกรรม UI Inventory Controller
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check
- ที่เกี่ยวข้อง: [[spot-check/03-user-flow-inventory-controller]], [[spot-check/02-business-rules]] (`SPC_AUTH_001`, `SPC_VAL_*`, `SPC_POST_*`), [[spot-check/04-test-scenarios]] (scenario handoff ข้าม persona), [[physical-count/04-test-scenarios-count-lead]] (scenario คู่เทียบการนับเต็ม)
