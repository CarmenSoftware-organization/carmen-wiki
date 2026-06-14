---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Audit & Config
description: Test case ของ Approver / Finance Reviewer, Auditor และ Sysadmin สำหรับโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-05-20T00:00:00.000Z
tags: physical-count, test-scenarios, audit, config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Approver / Finance Reviewer + Auditor + Sysadmin) &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **Scenario:** ~30 (skeleton)
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `physical-count` ที่ `../carmen-inventory-frontend-e2e/`; scenario เป็น manual / planned scenario การอนุมัติ rollup cross-reference [inventory-adjustment](/th/inventory/inventory-adjustment) spec

## 1. ขอบเขต Persona

กลุ่ม persona **Audit / Config** ยุบสาม role ที่การสัมผัสโมดูล physical-count คือการอนุมัติ การสังเกต หรือการ config Scenario ด้านล่างใช้ action ที่ catalogue ใน [physical-count/03-user-flow-audit-config](/th/inventory/physical-count/03-user-flow-audit-config) หัวข้อ 3 — การ review/อนุมัติ/reject rollup adjustment (Approver / Finance), การสังเกต in-progress และการตรวจ chain เต็ม (Auditor), การ config tolerance / costing-method / reason-code (Sysadmin) Authority anchor `PHC_AUTH_003` หมายเหตุ: **action การอนุมัติ rollup ลงจอดบนเอกสาร [inventory-adjustment](/th/inventory/inventory-adjustment) ไม่ใช่บน `tb_physical_count`** — scenario หลายข้อด้านล่าง cross-reference [inventory-adjustment/04-test-scenarios-finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance) และ [inventory-adjustment/04-test-scenarios-audit-config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)

## 2. Functional — Happy Path

| # | Scenario | Persona | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------- | ------------- | ---------------- |
| AC-F-01 | Review rollup variance adjustment | Approver / Finance | Rollup `tb_stock_in` / `tb_stock_out` ใน `in_progress`; `info.countId` เติม | Reviewer เห็นบรรทัด variance + drill-through ไปยัง `tb_physical_count` ต้นทาง |
| AC-F-02 | อนุมัติ rollup adjustment | Approver / Finance | Variance อยู่ในเกณฑ์ในอดีต; ADJ-side validation ผ่าน | Adjustment `completed`; `tb_inventory_transaction` เขียน; journal entry ของ GL post ตาม path การอนุมัติ [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) |
| AC-F-03 | Reject rollup adjustment | Approver / Finance | Variance ผิดปกติ (เช่น 30% บนหมวดติดตาม) | Adjustment return ไป `draft`; Count Lead รับ notification; การสืบสวนอาจ trigger recount ใหม่ |
| AC-F-04 | Auditor สังเกตการนับขณะ in-progress | Auditor | เอกสาร count อยู่ `in_progress` | มุมมอง read-only: การป้อน `actual_qty` สด, การมอบหมาย zone, flag recount Auditor อาจแนบ note สังเกตเป็น `tb_physical_count_comment` |
| AC-F-05 | Auditor ตรวจ chain เต็ม | Auditor | Period `completed`; rollup adjustment `completed` | Trace read-only: count sheet → บันทึก recount → การอนุมัติ → adjustment ที่ post → inventory transaction → journal entry ไม่มี gap |
| AC-F-06 | Sysadmin ตั้งค่า tolerance threshold | Sysadmin | นโยบาย tenant ใหม่ | Default tenant อัปเดต; การนับในอนาคตใช้ threshold ใหม่ตาม `PHC_VAL_007` |
| AC-F-07 | Sysadmin ตั้งค่า costing-method default | Sysadmin | นโยบาย tenant เปลี่ยน (เช่น เปลี่ยนจาก `last` เป็น `average`) | Default tenant อัปเดต; rollup ในอนาคตตีมูลค่า variance ตาม `PHC_CALC_003` ด้วย method ใหม่ |
| AC-F-08 | Sysadmin map reason code สำหรับ rollup | Sysadmin | การ onboard tenant ใหม่ | `tb_adjustment_type` row สำหรับ `COUNT_OVERAGE` (`type = stock_in`) และ `COUNT_SHORTAGE` (`type = stock_out`) สร้างพร้อม `info.glAccount` ตาม [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 2.1 |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| AC-R-01 | Auditor พยายามแก้ไข count | Role Auditor เท่านั้น | แก้ไข reject; read-only บังคับสำหรับ Auditor ที่ทั้งสามระดับ (period, document, detail) |
| AC-R-02 | Approver / Finance พยายามแก้ไข count detail | Role Approver | แก้ไข reject; action อนุมัติเฉพาะบน rollup `tb_stock_in` / `tb_stock_out` ไม่ใช่บน `tb_physical_count_detail` |
| AC-R-03 | Sysadmin พยายามทำการนับ | Role Sysadmin เท่านั้น | ถ้า Sysadmin ขาด role Count Lead, action การนับถูก reject Sysadmin config ไม่ดำเนินการ |
| AC-R-04 | Approver / Finance approval — SoD กับ Count Lead | User เดียวกันเป็นทั้ง Count Lead และ Approver บนการนับ | การตรวจ SoD reject: approver ต้องต่างจาก submitter ของ count |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| AC-V-01 | `INV_VAL_008` (inherited) | Rollup adjustment submit เข้า period `closed` | `"Cannot post into period <YYMM>: period is closed."` Finance Manager ต้องเปิดใหม่ |
| AC-V-02 | `ADJ_VAL_002` (downstream) | Sysadmin map `COUNT_OVERAGE` ผิดเป็น `type = stock_out` | บันทึก reason-code reject ที่ form ของ adjustment-type ตามการ validate ทิศทางใน [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) `ADJ_VAL_002` |
| AC-V-03 | `PHC_AUTH_003` | Auditor พยายามอนุมัติ rollup adjustment | Action reject; Auditor เป็น read-only บน path การอนุมัติ rollup |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| AC-E-01 | Approver / Finance อนุมัติ overage และ shortage จาก count เดียวกัน | rollup adjustment สองฉบับ approve เป็น session Approver เดียว | ทั้ง `tb_stock_in` และ `tb_stock_out` `completed`; ทั้งสองเขียน `tb_inventory_transaction` ผลสุทธิ = `Σ diff_qty × cost_per_unit` |
| AC-E-02 | วันที่มีผลของการเปลี่ยน tolerance threshold | Threshold แน่นขึ้นจาก 5% เป็น 2% ระหว่าง period | การนับที่กำลังดำเนินใช้ 5% (snapshot); การนับใหม่ใช้ 2% ตรวจสอบผ่าน parallel-count test |
| AC-E-03 | การเปลี่ยน costing-method หลัง rollup post | Sysadmin เปลี่ยนจาก `last` เป็น `average` หลัง rollup เป็น `completed` แล้ว | Rollup ที่ post ไม่เปลี่ยน (immutable); rollup ในอนาคตใช้ `average` |
| AC-E-04 | Query SoD compliance ของ Auditor | Auditor query สำหรับการนับที่ Count Lead = Approver | Audit query return คู่ที่ flag; ตรวจสอบว่ากฎ SoD `AC-R-04` บังคับใช้ |
| AC-E-05 | การอนุมัติบางส่วนของ Approver / Finance | Approver พยายามอนุมัติเฉพาะบางบรรทัดใน rollup adjustment | ไม่รองรับ — rollup adjustment อนุมัติทั้งฉบับ; การอนุมัติบางส่วนต้อง return ไป `draft` และ split ที่ระดับ Count Lead |

## 6. Configuration / Audit-Trail

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| AC-C-01 | Audit log จับทุกการตัดสินใจของ approver | Approver approve หรือ reject | `workflow_history` บน `tb_stock_in` / `tb_stock_out` บันทึก `last_action`, `last_action_by_id`, `last_action_at_date` |
| AC-C-02 | Traceability การเปลี่ยน reason-code ของ Sysadmin | Sysadmin อัปเดต `info.glAccount` บน `COUNT_OVERAGE` | การเปลี่ยน audit-log; rollup-adjustment ที่ post ในประวัติเก็บบัญชี GL ที่ **snapshot** ใน inventory-transaction GL entry ของตนตาม [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 5 item 6 |
| AC-C-03 | Query chain เต็มของ Auditor | Auditor query การนับฉบับเดียว end-to-end | Return `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail` → rollup `tb_stock_in` / `tb_stock_out` (ผ่าน `info.countId`) → `tb_inventory_transaction` → journal entry ของ GL |
| AC-C-04 | การ gate ปิด period บน completion ของการนับ | Finance Manager พยายามปิด period ด้วย `tb_physical_count_period.status != completed` | การปิด period ถูกบล็อก; Count Lead ต้อง complete เอกสาร count ที่เหลือก่อน |

> **TODO:** ขยายทุก row ด้วย assertion ฟิลด์ `tb_*` ชัดเจน, ข้อความ error และ (เมื่อ spec มี) reference บรรทัด spec E2E Validate การพูดของกฎ SoD (`AC-R-04`) กับนโยบาย RBAC ของ carmen-platform

## 7. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — source ของคิวอนุมัติ + UI config admin
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ที่เกี่ยวข้อง: [physical-count/03-user-flow-audit-config](/th/inventory/physical-count/03-user-flow-audit-config), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_AUTH_003`, `PHC_POST_002`), [inventory-adjustment/04-test-scenarios-finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance) (scenario approver ของ rollup), [inventory-adjustment/04-test-scenarios-audit-config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config) (scenario audit / config คู่ขนานฝั่ง adjustment), [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) (scenario handoff ข้าม persona)
