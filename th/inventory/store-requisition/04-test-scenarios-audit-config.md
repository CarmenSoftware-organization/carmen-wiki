---
title: ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios — Audit & Config
description: test case ของ Inventory Controller, Finance, Sysadmin และ Auditor — ส่วนใหญ่เป็น persona ที่ยังไม่ยืนยัน; อธิบายว่าทำไมชุด scenario เดิมไม่ตรงกับ source ปัจจุบัน
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Inventory Controller + Finance + Sysadmin + Auditor — **ส่วนใหญ่ยังไม่ยืนยันว่าเป็น persona แยกของโมดูล SR ใน source ปัจจุบัน** &nbsp;·&nbsp; **โมดูล:** [store-requisition](/th/inventory/store-requisition)
> ⚠️ **แก้ไขครั้งใหญ่รอบนี้** หน้านี้เคยระบุ test scenario ~27 รายการสำหรับ admin-void console, Finance closed-period gate พร้อมการยืนยัน journal-entry, Sysadmin RBAC/workflow/SoD-threshold configuration console และเครื่องมือ Auditor signature-trace [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) บันทึกร่องรอยการตรวจสอบ source เต็ม: ไม่มี admin-void method ใดแยกจาก `reject` ทั้งเอกสารตามปกติ (ซึ่งผู้กระทำขั้นปัจจุบันคนใดก็เรียกได้); ไม่มี code `journal`/`ledger` ใด ๆ ในโมดูลนี้; ไม่มี check `period` ใน `store-requisition.service.ts` หรือ `store-requisition.logic.ts`; และไม่มีผลลัพธ์ `threshold` หรือ `delegat` ใด ๆ ในโมดูลนี้หรือ workflow orchestrator ดังนั้นจึงไม่มีอะไรแยกให้เขียน test scenario ต่อสำหรับ sub-role ทั้งสี่นี้

## 1. สิ่งที่มาแทน Scenario เหล่านี้

สิ่งที่ใกล้เคียงที่สุดกับสิ่งที่หน้านี้เคย test:

| กลุ่ม Scenario เดิม | สิ่งที่ยืนยันได้จริง |
|---|---|
| Admin void บน SR ก่อน commit | action `reject` ทั้งเอกสารตามปกติ (`StoreRequisitionService.reject()`) ใช้ได้โดยผู้ที่ถือขั้น workflow ปัจจุบัน — ดู [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) APR-EDGE-02 และ [04-test-scenarios-fulfiller.md](./04-test-scenarios-fulfiller.md) ไม่ใช่เส้นทาง "admin" แยกต่างหาก |
| Finance closed-period block, การยืนยัน journal-entry, period close | **ยังไม่ implement** ไม่สามารถเขียน test scenario ต่อ feature ที่ไม่พบ code เลยได้ |
| Sysadmin RBAC / workflow / SoD-relaxation-threshold console | `tb_workflow` เป็นตารางจริงที่ tenant config ได้ ใช้ร่วมกับ PR/PO/GRN — การ test การเปลี่ยนจำนวนขั้นหรือ stage-role ที่นั่นเป็น test config workflow ทั่วไป ไม่ใช่เฉพาะ SR ไม่มีฟิลด์ SoD-relaxation หรือ value-threshold ให้ test |
| Auditor read-only signature trace | `workflow_history` และ JSON `history` ต่อบรรทัดอ่านได้โดยผู้ใช้ใดก็ได้ที่มีสิทธิ์อ่าน SR — ไม่มี route เฉพาะ Auditor ให้ test |

Test scenario ขั้นต่ำที่ตรงตามความเป็นจริงกับพื้นผิวจริง:

| # | Scenario | Pre-condition | Steps | คาดหวัง |
| - | -------- | ------------- | ----- | ------- |
| AC-HP-01 | ผู้ที่ถือขั้น workflow ปัจจุบัน reject ทั้งเอกสาร | SR ที่ `doc_status = in_progress` | 1. เปิด SR 2. เรียก action reject ทั้งเอกสาร 3. Confirm | `doc_status = voided` (ไม่ใช่ `cancelled`); ใช้ได้กับผู้ใช้ใดก็ได้ใน `user_action.execute` สำหรับขั้นปัจจุบัน ไม่จำกัดเฉพาะ role "Inventory Controller" หรือ "Sysadmin" ดู `04-test-scenarios-approver.md` APR-EDGE-02 |

## 2. แหล่งอ้างอิง

- ภาพรวมแม่: [04-test-scenarios.md](./04-test-scenarios.md) — Scenarios 9, 10, 11, 13, 14 ถูกลบหรือแคบลงรอบนี้ด้วยเหตุผลเดียวกัน
- User flow: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — ร่องรอย "อะไรยืนยันได้และอะไรยังไม่ยืนยัน" เต็มที่หน้านี้สรุป
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — เป้าหมายการ escalate ความคลาดเคลื่อนที่เวอร์ชันก่อนหน้าของหน้านี้บรรยาย ตัวมันเองก็ยังไม่ยืนยันเช่นกัน
- Business rules: [02-business-rules.md](./02-business-rules.md) § 2 (`SR_VAL_014`, ยังไม่ยืนยัน), § 4 (`SR_AUTH_009`–`SR_AUTH_013`, แก้ไขแล้ว), § 5 (`SR_POST_007`, `SR_POST_009`, `SR_POST_010`, `SR_POST_013`, แก้ไขแล้ว)
