---
title: ใบขอซื้อ (Purchase Request) — Test Scenarios — Audit & Config
description: เหตุผลที่ไม่มี audit-workspace หรือ test scenarios การตั้งค่าเฉพาะ PR สำหรับ purchase-request ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: 2026-07-29T04:45:21.000Z
tags: purchase-request, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Audit / Config (Auditor + System Administrator) — **ไม่มี audit-workspace หรือ configuration workbench เฉพาะ PR ที่ยืนยันได้ในซอร์สปัจจุบัน** &nbsp;·&nbsp; **โมดูล:** [purchase-request](/th/inventory/purchase-request)
> **E2E coverage:** ไม่มีที่ยืนยันได้สำหรับ workspace เฉพาะทาง; read path ของ `/system-admin/activity-log` แบบ generic ถูก exercise โดยบังเอิญผ่าน spec ของ persona อื่น ไม่ใช่ผ่าน dedicated audit-config journey spec

> ⚠️ **แก้ไขใหญ่ในรอบนี้** เวอร์ชันก่อนหน้าของหน้านี้ระบุ scenario ประมาณสามสิบตัว (`AUD-HP-01` ถึง `AUD-EDGE-06`) ครอบคลุม audit workspace "PR Activity Queries" (audit template, drill-down trail, export-approval workflow, การ flag case file) และ "Configuration workspace" เฉพาะ PR (workflow-threshold editor พร้อม versioning `effective_from`, PR Type Defaults, Delegation Rules, Tax Codes, Currency Rates) ข้อค้นพบนี้ถูก settle เทียบกับซอร์สปัจจุบันใน `.specs/resync-2026-07-15-progress.md` (commit `df8ab13`) หลังจากอ่านทุก route ใน `router.tsx` และทุก screen component ใต้ `routes/system-admin/` และ `routes/config/` — ไม่มี audit หรือ configuration surface เฉพาะ PR อยู่จริง ดู [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) สำหรับการแก้ไขเต็ม, การ map screen-by-screen ที่แม่นยำ, และ search ที่รัน นี่คือ pattern เดียวกันที่พบและแก้ไขอย่างอิสระในโมดูล `purchase-order` — ดู [purchase-order/04-test-scenarios-audit-config.md](/th/inventory/purchase-order/04-test-scenarios-audit-config)

## สิ่งที่ถูกตัดออกและเหตุผล

| กลุ่ม scenario ที่ถูกตัด | เหตุผล |
|---|---|
| `AUD-HP-01` – `AUD-HP-04` (Auditor query-workspace, drill-down trail, export-approval, การ flag case file) | ไม่พบ route "Audit workspace," "PR Activity Queries," หรือหน้า drill-down ที่ scope เฉพาะ PR อยู่เลยใน `carmen-inventory-frontend-react` |
| `AUD-HP-05` – `AUD-HP-09` (Sysadmin workflow-threshold, delegation, PR-type-default, tax/currency-master config พร้อม preview panel และ versioning `effective_from`) | ไม่พบ configuration workbench เฉพาะ PR การตั้งค่า workflow-stage และ RBAC เป็น screen system-config แบบ generic (`/system-admin/workflow`, `/system-admin/user`, `/system-admin/role`); การตั้งค่า tax และ currency เป็น screen master-data แบบ generic (`/config/tax-profile`, `/config/currency`, `/config/exchange-rate`) — ไม่มีตัวใดเฉพาะ PR และไม่มีตัวใดมี panel preview/forecast หรือ versioning ด้วย `effective_from` Amount-threshold routing และ delegation window **ไม่มี equivalent อยู่เลย** ในซอร์สปัจจุบัน ทั้ง generic และเฉพาะ PR |
| `AUD-PERM-01` – `AUD-PERM-07`, `AUD-VAL-01` – `AUD-VAL-08`, `AUD-EDGE-01` – `AUD-EDGE-06` | ทั้งหมดขึ้นกับ workspace และ configuration surface ที่ไม่มีอยู่จริงข้างต้น |

## สิ่งที่ยืนยันได้แทน

- หน้า **`/system-admin/activity-log`** แบบ generic list event `action` / `entity_type` / `user` ข้ามทุกประเภทเอกสาร filter ได้แต่ไม่ใช่ query-template-driven; filter scope `purchase_request` เป็น equivalent ที่ใกล้ที่สุดของ "PR Activity Queries" ผู้ใช้ที่มีสิทธิ์อ่าน PR ยังเห็น `tb_purchase_request_comment` history ได้โดยตรงบนหน้า detail PR (แถว `type = system` immutable ตาม `PR_POST_008`) ยังไม่ยืนยันว่า role Auditor ที่แยกต่างหาก gate surface ใดต่างจากผู้อ่านคนอื่นหรือไม่
- Workflow-stage definition (`stage_role`, `user_action.execute[]`), tax rate, currency และ exchange-rate master, และ RBAC user/role assignment แต่ละตัวตั้งค่าผ่าน screen generic ของตัวเอง — `/system-admin/workflow`, `/config/tax-profile`, `/config/currency` + `/config/exchange-rate`, `/system-admin/user` + `/system-admin/role` — ใช้ร่วมกันข้าม PR, PO, GRN และประเภทเอกสารอื่น ไม่ใช่ผ่าน screen เฉพาะ PR
- Action เดียวที่เปลี่ยนสถานะ PR ที่ยืนยันได้ในแกน persona นี้คือ **void** ระดับสูงของ System Administrator (`PR_AUTH_007` → `PR_POST_006`): `pr_status` flip เป็น `voided`, budget soft-commitment ปล่อย และ comment เหตุผลบังคับ append สิ่งนี้ถูก exercise โดยบังเอิญในตาราง scenario ของ persona อื่น (เช่น [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) `APP-VAL-10`, [04-test-scenarios-requestor.md](./04-test-scenarios-requestor.md) `REQ-PERM-06`) ไม่ใช่ใน audit-config scenario เฉพาะที่นี่
- การค้นหาทั่ว repo สำหรับ `threshold` และ `delegat` ทั้งฝั่ง frontend และ backend ไม่พบกลไก amount-threshold routing หรือ approval-delegation เลย นี่หมายความว่า `PR_AUTH_005` และ `PR_AUTH_006` ใน [02-business-rules.md](./02-business-rules.md) บรรยาย design intent ที่ยังไม่ยืนยัน flag ไว้ที่นี่สำหรับการแก้ไขระดับ business-rules ใน follow-up นอกขอบเขตของหน้านี้

## แหล่งอ้างอิง

- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — การแก้ไขเต็ม รวมถึง screen ที่อ่านจริงและ search ที่รัน
- Sibling: [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) — ที่ `PR_AUTH_007` void ที่ยืนยันแล้วถูก exercise เป็นเงื่อนไขก่อน แทนที่ scenario configuration ของ Sysadmin ที่ถูกตัดออก
- เกี่ยวข้อง (generic config ไม่ใช่เฉพาะ PR): [system-config/workflow](/th/inventory/system-config/workflow)
- Cross-link: [purchase-order/04-test-scenarios-audit-config.md](/th/inventory/purchase-order/04-test-scenarios-audit-config) — การแก้ไขแบบเดียวกันของโมดูลพี่น้อง พร้อมรายการ search ทั้งหมดที่รัน
