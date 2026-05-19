---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios — Audit & Config
description: Test case ของ Auditor และ Sysadmin สำหรับโมดูลการสุ่มตรวจ
published: true
date: 2026-05-19T23:55:00.000Z
tags: spot-check, test-scenarios, audit, config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor read-only + Sysadmin config) &nbsp;·&nbsp; **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **Scenario:** ~23
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี — ยังไม่มี Playwright spec ของ spot-check ที่ `../carmen-inventory-frontend-e2e/tests/`

## 1. ขอบเขต Persona

กลุ่ม persona **Audit / Config** ยุบสอง role ที่การสัมผัสโมดูล spot-check คือการสังเกตหรือการ config Scenario ด้านล่างใช้ action ที่ catalogue ใน [spot-check/03-user-flow-audit-config](/th/inventory/spot-check/03-user-flow-audit-config) หัวข้อ 3 — การสังเกต in-progress และการตรวจ chain เต็ม (Auditor), การ config tolerance / default-size / default-method / reason-code (Sysadmin โดยปริยาย) Authority anchor `SPC_AUTH_003` หมายเหตุ: **action การอนุมัติ rollup ลงจอดบนเอกสาร [inventory-adjustment](/th/inventory/inventory-adjustment) ไม่ใช่บน `tb_spot_check`** — scenario หลายข้อด้านล่าง cross-reference [inventory-adjustment/04-test-scenarios-finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance) และ [inventory-adjustment/04-test-scenarios-audit-config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)

## 2. Functional — Happy Path

| # | Scenario | Persona | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------- | ------------- | ---------------- |
| AC-F-01 | Auditor สังเกต spot check ขณะ in-progress | Auditor | Spot check อยู่ `in_progress` | มุมมอง read-only: การป้อน `actual_qty` สด, การมอบหมาย counter, flag recount Auditor อาจแนบ note สังเกตเป็น `tb_spot_check_comment` |
| AC-F-02 | Auditor ตรวจ chain เต็ม | Auditor | Spot check `completed`; rollup adjustment `completed` | Trace read-only: spot-check sheet → บันทึก recount → การอนุมัติ → adjustment ที่ post → inventory transaction → journal entry ไม่มี gap |
| AC-F-03 | Auditor verify SoD บนการอนุมัติ rollup | Auditor | Rollup adjustment `completed` | Auditor query ยืนยัน `tb_stock_in.created_by_id` ≠ approval `last_action_by_id` |
| AC-F-04 | Sysadmin ตั้งค่า tolerance threshold | Sysadmin | นโยบาย tenant ใหม่ | Default tenant อัปเดต; spot check ในอนาคตใช้ threshold ใหม่ตาม `SPC_VAL_006` |
| AC-F-05 | Sysadmin ตั้งค่า default sampling size | Sysadmin | นโยบาย tenant เปลี่ยน | Default tenant อัปเดต; spot check ในอนาคต default เป็น `size` ใหม่ยกเว้น override |
| AC-F-06 | Sysadmin ตั้งค่า default sampling method | Sysadmin | นโยบาย tenant เปลี่ยน (เช่น เปลี่ยนจาก `random` เป็น `high_value`) | Default tenant อัปเดต; spot check ในอนาคต default เป็น `method` ใหม่ |
| AC-F-07 | Sysadmin map reason code สำหรับ rollup | Sysadmin | การ onboard tenant ใหม่ | `tb_adjustment_type` row สำหรับ `SPOT_CHECK_OVERAGE` (`type = STOCK_IN`) และ `SPOT_CHECK_SHORTAGE` (`type = STOCK_OUT`) สร้างพร้อม `info.glAccount` — หรือ alias เป็น `COUNT_*` ที่มีอยู่ตาม convention ของ tenant ตาม [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 2.1 |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| AC-R-01 | Auditor พยายามแก้ไข spot check | Role Auditor เท่านั้น | แก้ไข reject; read-only บังคับสำหรับ Auditor ที่ทั้งสองระดับ (header, detail) |
| AC-R-02 | Auditor พยายาม void spot check | Role Auditor เท่านั้น | Action reject; เฉพาะ Inventory Controller ที่ void ได้ ตาม `SPC_AUTH_001` |
| AC-R-03 | Sysadmin พยายามทำ spot check | Role Sysadmin เท่านั้น | ถ้า Sysadmin ขาด role Inventory Controller, action spot-check ถูก reject Sysadmin config ไม่ดำเนินการ |
| AC-R-04 | Approval — SoD กับ submitter ของ spot-check | User เดียวกันเป็นทั้ง Inventory Controller (spot-check) และ Approver (rollup adjustment) | การตรวจ SoD reject ฝั่ง [inventory-adjustment](/th/inventory/inventory-adjustment): approver ของ rollup ต้องต่างจาก submitter ของ spot-check |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| AC-V-01 | `INV_VAL_008` (inherited) | Rollup adjustment submit เข้า period `closed` | `"Cannot post into period <YYMM>: period is closed."` Finance Manager ต้องเปิดใหม่ |
| AC-V-02 | `ADJ_VAL_002` (downstream) | Sysadmin map `SPOT_CHECK_OVERAGE` ผิดเป็น `type = STOCK_OUT` | บันทึก reason-code reject ที่ form ของ adjustment-type ตามการ validate ทิศทางใน [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) `ADJ_VAL_002` |
| AC-V-03 | `SPC_AUTH_003` | Auditor พยายามอนุมัติ rollup adjustment | Action reject; Auditor เป็น read-only บน path การอนุมัติ rollup |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| AC-E-01 | การอนุมัติ overage และ shortage จาก spot check เดียวกัน (cross-module) | rollup adjustment สองฉบับ approve ฝั่ง [inventory-adjustment](/th/inventory/inventory-adjustment) | ทั้ง `tb_stock_in` และ `tb_stock_out` `completed`; ทั้งสองเขียน `tb_inventory_transaction` ผลสุทธิ = `Σ diff_qty × cost_per_unit` |
| AC-E-02 | วันที่มีผลของการเปลี่ยน tolerance threshold | Threshold แน่นขึ้นจาก 5% เป็น 2% ระหว่างวัน | spot check ที่กำลังดำเนินใช้ 5% (snapshot); spot check ใหม่ใช้ 2% ตรวจสอบผ่านการทดสอบ spot check ขนาน |
| AC-E-03 | การเปลี่ยน default `method` หลัง spot check สร้าง | Sysadmin เปลี่ยน default จาก `random` เป็น `high_value` หลัง spot check `random` กำลัง `in_progress` แล้ว | spot check ที่กำลังดำเนินไม่เปลี่ยน (ใช้ `random` ตามฟิลด์ `method` ของตน); spot check ในอนาคต default เป็น `high_value` |
| AC-E-04 | Query SoD compliance ของ Auditor | Auditor query สำหรับ spot check ที่ submitter = approver ของ rollup | Audit query return คู่ที่ flag; ตรวจสอบว่ากฎ SoD `AC-R-04` บังคับใช้ |
| AC-E-05 | Spot check ถูก void หลัง rollup adjustment อยู่ `in_progress` | Inventory Controller พยายาม void หลัง adjustment ถูก route ไปอนุมัติ | Void reject เพราะ rollup อยู่ downstream แล้ว; การ reverse ต้องผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) |

## 6. Configuration / Audit-Trail

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| AC-C-01 | Audit log จับทุกการตัดสินใจของ approver (downstream) | Approver approve หรือ reject rollup | `workflow_history` บน `tb_stock_in` / `tb_stock_out` บันทึก `last_action`, `last_action_by_id`, `last_action_at_date` |
| AC-C-02 | Traceability การเปลี่ยน reason-code ของ Sysadmin | Sysadmin อัปเดต `info.glAccount` บน `SPOT_CHECK_OVERAGE` | การเปลี่ยน audit-log; rollup-adjustment ที่ post ในประวัติเก็บบัญชี GL ที่ **snapshot** ใน inventory-transaction GL entry ของตนตาม [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 5 item 6 |
| AC-C-03 | Query chain เต็มของ Auditor | Auditor query spot check ฉบับเดียว end-to-end | Return `tb_spot_check` → `tb_spot_check_detail` → rollup `tb_stock_in` / `tb_stock_out` (ผ่าน `info.spotCheckId`) → `tb_inventory_transaction` → journal entry ของ GL |
| AC-C-04 | Auditor list spot check `void` | Auditor query `doc_status = void` | Return spot check ที่ voided พร้อมการป้อนบางส่วนเก็บ; ไม่มี row `tb_inventory_transaction` ที่เกี่ยวข้อง |

> **TODO:** ขยายทุก row ด้วย assertion ฟิลด์ `tb_*` ชัดเจน, ข้อความ error และ (เมื่อ spec มี) reference บรรทัด spec E2E Validate การพูดของกฎ SoD (`AC-R-04`) กับนโยบาย RBAC ของ carmen-platform ยืนยันการตั้งชื่อ reason-code (`SPOT_CHECK_*` vs `COUNT_*` ที่ใช้ซ้ำ) เมื่อ convention ของ tenant ถูกกำหนด

## 7. แหล่งอ้างอิง

- **Primary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend/` — source ของ audit query + UI config admin
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check
- ที่เกี่ยวข้อง: [spot-check/03-user-flow-audit-config](/th/inventory/spot-check/03-user-flow-audit-config), [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) (`SPC_AUTH_003`, `SPC_POST_002`), [inventory-adjustment/04-test-scenarios-finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance) (scenario approver ของ rollup), [inventory-adjustment/04-test-scenarios-audit-config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config) (scenario audit / config คู่ขนานฝั่ง adjustment), [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) (scenario handoff ข้าม persona), [physical-count/04-test-scenarios-audit-config](/th/inventory/physical-count/04-test-scenarios-audit-config) (scenario คู่เทียบการนับเต็มรวม flow Approver/Finance)
