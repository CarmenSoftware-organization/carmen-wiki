---
title: ใบสั่งซื้อ (Purchase Order) — Test Scenarios — Audit & Config
description: เหตุผลที่ไม่มี audit-workspace เฉพาะหรือ test scenarios ด้าน configuration เฉพาะ PO ในซอร์สโค้ดปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor + System Administrator) — **ไม่พบ audit-workspace เฉพาะหรือ configuration workbench เฉพาะ PO ที่ยืนยันได้ในซอร์สโค้ดปัจจุบัน** &nbsp;·&nbsp; **Module:** [purchase-order](/th/inventory/purchase-order)
> **E2E coverage:** ไม่มีที่ยืนยันได้สำหรับ workspace เฉพาะ; ฟิลด์ activity-log ที่รองรับอยู่ (`workflow_history`, `tb_purchase_order_comment`) ถูก exercise โดยบังเอิญจาก spec ของทุก persona อื่น ๆ

> ⚠️ **แก้ไขครั้งใหญ่ในรอบนี้** เวอร์ชันก่อนหน้าของหน้านี้ระบุ ~30 scenarios (AUD-HP-01 ถึง AUD-EDGE-06) ครอบคลุม workspace "Procurement Activity Queries" (query templates, export-approval workflow, case-file notes) และ "Configuration workspace" เฉพาะ PO (numbering-scheme editor, RBAC editor, PR-to-PO grouping-rule editor, approval-delegation-window manager, deadlock detection) ไม่พบ route, component, หรือ backend endpoint ใดที่ตรงกับ workspace ทั้งสองนี้ในซอร์สโค้ดปัจจุบัน ดู [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) สำหรับคำแก้ไขฉบับเต็มและการค้นที่รันจริง pattern นี้ (เรื่องเล่า audit/config ที่วิจิตรบรรจงแต่ไม่มี route ที่ตรงกัน) เคยถูก flag ว่ายังไม่ยืนยันในรอบ resync ก่อนหน้าของโมดูล `purchase-request` เช่นกัน; การค้นที่กว้างขึ้นในรอบนี้ไม่พบสิ่งใดสนับสนุนมันเลยทั่วทั้งผลิตภัณฑ์ จึงแก้ไขที่นี่แทนที่จะ defer ต่อไปอีก

## สิ่งที่ถูกตัดออกและเหตุผล

| กลุ่ม scenario ที่ถูกตัดออก | เหตุผล |
|---|---|
| AUD-HP-01 ถึง AUD-HP-05 (Auditor query workspace, chain drill-down, export approval) | ไม่พบ route/component "Audit workspace" หรือ "Procurement Activity Queries" ใด ๆ |
| AUD-HP-06 ถึง AUD-HP-09 (Sysadmin numbering/RBAC/grouping-rule/delegation config) | ไม่พบ configuration workbench เฉพาะ PO; การตั้งค่า numbering และ workflow-stage เป็นหน้า system-config แบบ generic (ดู [system-config/workflow](/th/inventory/system-config/workflow), [system-config/running-code](/th/inventory/system-config/running-code)) ไม่ใช่หน้าเฉพาะ PO ที่มี editor ตามที่อธิบายไว้ |
| AUD-PERM-01 ถึง AUD-PERM-07, AUD-VAL-01 ถึง AUD-VAL-08, AUD-EDGE-01 ถึง AUD-EDGE-06 | ทั้งหมดขึ้นอยู่กับ workspace ที่ไม่มีจริงข้างต้น |

## สิ่งที่ยืนยันได้แทน

- User คนใดก็ตามที่มีสิทธิ์อ่าน PO สามารถเห็น `workflow_history` และ `tb_purchase_order_comment` ของ PO นั้นได้บนหน้า detail เอง — นี่คือ "audit trail" ที่ยืนยันได้จริง ยังไม่ยืนยันว่า role Auditor แยกต่างหากจะ gate สิ่งนี้ต่างจาก viewer คนอื่นหรือไม่
- นิยาม workflow-stage (`stage_role`, `user_action.execute[]`) และการตั้งเลขเอกสาร (`po_no` generation) ถูก configure ผ่านโมดูล system-config แบบ generic ที่ใช้ร่วมกันข้าม PR, PO, GRN และเอกสารชนิดอื่น — ไม่ใช่ผ่านหน้าจอเฉพาะ PO ดูหน้าของโมดูล system-config เอง (นอกขอบเขตของรอบนี้) สำหรับสิ่งที่ยืนยันได้จริงที่นั่น
- ไม่พบ RBAC editor, integration-settings screen, หรือ delegation-window manager เฉพาะ PO ใด ๆ

## แหล่งอ้างอิง

- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — คำแก้ไขฉบับเต็ม รวมถึงการค้นที่รันจริงและผลลัพธ์ที่ได้
- Sibling: [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) — เส้นทางแก้ไขที่ยืนยันได้ (cancel / close / reject) สำหรับ PO ที่ค้าง แทนที่ scenarios การ escalate ไปยัง Sysadmin ที่ถูกตัดออก
- Related (config แบบ generic ไม่ใช่เฉพาะ PO): [system-config/workflow](/th/inventory/system-config/workflow), [system-config/running-code](/th/inventory/system-config/running-code)
