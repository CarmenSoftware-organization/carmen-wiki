---
title: ใบเบิกของสโตร์ (Store Requisition) — User Flow — Audit & Config
description: flow ของ Inventory Controller, Finance, Sysadmin และ Auditor ในโมดูล store-requisition — persona ที่ส่วนใหญ่ยังไม่ยืนยัน; บันทึกสิ่งที่ยืนยันได้และยังไม่ยืนยันใน source ปัจจุบัน
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, user-flow, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# ใบเบิกของสโตร์ (Store Requisition) — User Flow — Audit & Config

> **At a Glance**
> **Persona:** Inventory Controller + Finance + Sysadmin + Auditor — **ส่วนใหญ่ยังไม่ยืนยันว่าเป็น persona แยกของโมดูล SR ใน source ปัจจุบัน** &nbsp;·&nbsp; **โมดูล:** [store-requisition](/th/inventory/store-requisition)
> **หน้านี้บันทึกอะไร:** เหตุใด workspace การกำกับดูแล/config ที่เคยบรรยายไว้ (variance dashboard, admin-void console, GL-verification queue, RBAC/workflow console, threshold การผ่อนคลาย SoD) ไม่ตรงกับ source ปัจจุบัน และสิ่งที่ยืนยันได้จริง

> ⚠️ **แก้ไขครั้งใหญ่รอบนี้.** เวอร์ชันก่อนหน้าของหน้านี้บรรยาย sub-role สี่ตัวพร้อมหน้าจอเฉพาะ: variance dashboard และ admin-void console ก่อน commit ของ Inventory Controller, GL-reconciliation queue และ closed-period gate ของ Finance, workflow/RBAC/SoD-relaxation-threshold config console ของ Sysadmin และเครื่องมือ trace ลายเซ็นแบบอ่านอย่างเดียวของ Auditor การตรวจสอบทั้ง repo เทียบกับ source ปัจจุบันยืนยันแทบไม่มีสิ่งใดเลย:
> - **ไม่มี admin-void console.** `store-requisition.service.ts` ไม่มี method `void`/`admin-void` เลย วิธีเดียวที่ `doc_status` ไปถึง `voided` คือ `StoreRequisitionService.reject()` — action reject ทั้งเอกสารเดียวกับที่ผู้ถือขั้น workflow ปัจจุบันคนใดก็ใช้ได้ ไม่ใช่เส้นทางเฉพาะของ Inventory Controller ดู [03-user-flow-approver.md](./03-user-flow-approver.md) และ [02-business-rules.md](./02-business-rules.md) § 5
> - **ไม่มีโค้ด GL/journal-entry เลย** การค้นทั้ง repo ของ `carmen-turborepo-backend-v2` หาคำว่า `journal` / `ledger` เทียบกับโมดูลนี้และ dependency `inventory-transaction` ให้ผลลัพธ์เป็นศูนย์ ไม่มีอะไรให้ role "Finance" ตรวจสอบหรือ reconcile
> - **ไม่มี closed-period gate** การค้นคำว่า `period` ใน `store-requisition.service.ts`, `store-requisition.logic.ts` และ SR DTOs ให้ผลลัพธ์เป็นศูนย์ ชั้น inventory-transaction resolve งวดปัจจุบันเพื่อ *stamp* `at_period` บนแถวธุรกรรมเท่านั้น (สำหรับการเรียงลำดับ lot) — ไม่ได้ block อะไรเลย
> - **ไม่มี RBAC/workflow console, ตัวแก้ threshold หรือ config การผ่อนคลาย SoD เฉพาะสำหรับ SR** `tb_workflow` เป็นตาราง config จริงที่ใช้ร่วมกัน (ใช้โดย PR/PO/GRN ด้วย) แต่ไม่พบคำว่า `threshold` หรือ `delegat` เลยไม่ว่าในโมดูลนี้หรือ workflow orchestrator และ `enum_stage_role` ไม่มีสมาชิก `finance`
> - **ไม่พบ route หรือ component variance-dashboard** ใน `routes/store-operation/store-requisition/`
> - **ไม่พบ role หรือ route แบบอ่านอย่างเดียวเฉพาะของ Auditor** audit trail ที่มีอยู่คือ `workflow_history` / JSON `history` ต่อบรรทัดเดียวกับที่ผู้ใช้ใดก็ตามที่มีสิทธิ์อ่าน SR เห็นได้อยู่แล้ว
>
> หน้านี้ถูกเก็บไว้ (แทนที่จะลบ) เพราะชุด persona ของโมดูลระบุชื่อ role เหล่านี้ไว้ในตาราง role แบบ legacy บนหน้า landing และตาราง cross-persona ของ [03-user-flow.md](./03-user-flow.md) ที่เป็นแม่ เนื้อหาด้านล่างบันทึกการแก้ไขแทนที่จะพูดซ้ำ workspace ที่แต่งขึ้น

## 1. สิ่งที่ยืนยันได้และยังไม่ยืนยัน

| ข้อความจากเวอร์ชันก่อนหน้า | สถานะ |
|---|---|
| Action "Admin Void" เฉพาะทาง จำกัดเฉพาะ Inventory Controller / System Administrator | **ไม่ได้ implement ตามที่บรรยาย** กลไกจริงคือ action `reject` ทั้งเอกสาร ที่ผู้ถือขั้น workflow ปัจจุบันคนใดก็ใช้ได้; ตั้งเป็น `voided` ไม่ใช่ action เชิงบริหารที่ gate แยกต่างหาก |
| Finance GL-reconciliation queue, การตรวจสอบ journal-entry, การ block commit ในงวดปิด | **ไม่ได้ implement** ไม่มีโค้ด journal/ledger และไม่มี check งวดปิดเลยในโมดูลนี้ |
| Sysadmin RBAC / workflow-config console, threshold มูลค่าการอนุมัติ, threshold การผ่อนคลาย SoD | **ยังไม่ยืนยัน / ไม่พบ.** Config ของ `tb_workflow` มีจริงและใช้ร่วมกันข้ามโมดูล แต่ไม่พบ field threshold หรือการผ่อนคลาย SoD เฉพาะสำหรับ SR |
| เครื่องมือ trace ลายเซ็นแบบอ่านอย่างเดียวของ Auditor | **ยังไม่ยืนยันว่าเป็น route แยก** ข้อมูลที่อยู่เบื้องหลัง (`workflow_history`, JSON `history` ต่อบรรทัด, thread comment) มีจริงและอ่านได้โดยผู้ใช้ที่มีสิทธิ์อ่าน SR — ไม่มีหน้าจอที่ยืนยันได้ว่าเฉพาะ Auditor |
| การเชื่อม recipe auto-create ([recipe](/th/inventory/recipe) → SR draft) | **เป็นไปได้แต่ยังไม่ได้ตรวจสอบซ้ำในรอบนี้** — สืบทอดจากเวอร์ชันก่อนหน้าของหน้านี้; ฝั่ง SR ของเรื่องนี้ (SR มาถึงที่ `draft` พร้อม `info.recipe_id` บรรจุแล้ว) สอดคล้องกับ data model แต่ ตัว trigger ของโมดูล recipe เองอยู่ใน resync ของโมดูลนั้นเอง |
| การ reconcile / signoff ปลายงวดเป็น workflow แยก | **ไม่ได้ implement** — ขึ้นกับ closed-period gate และฟีเจอร์ journal-entry ที่ไม่มีอยู่จริงข้างต้น |

## 2. ควรทำอย่างไรกับหน้านี้

จนกว่าจะยืนยันว่ามี endpoint admin-void, ฟีเจอร์ post GL/journal, gate ปิดงวด หรือ console config RBAC/workflow เฉพาะโมดูลนี้ อย่าถือว่าข้อความ "Inventory Controller admin-void", "Finance block การ commit ในงวดปิด", "Sysadmin ตั้งค่า threshold การผ่อนคลาย SoD" หรือ "Auditor trace ลายเซ็น" ที่ปรากฏในหน้าอื่นของโมดูลนี้เป็นพฤติกรรมจริง

สิ่งที่ใกล้เคียงที่สุดที่มีอยู่วันนี้คือ: (a) ผู้ถือขั้น workflow ปัจจุบันคนใดก็สามารถ reject ทั้งเอกสารได้ (`voided` ไม่ใช่เส้นทาง admin แยก); (b) `tb_workflow` config ได้ต่อ tenant ด้วยกลไกทั่วไปเดียวกับที่ PR/PO/GRN ใช้ โดยไม่มี threshold หรือ field SoD เฉพาะ SR ที่ยืนยันได้; (c) `workflow_history` และ JSON `history` ต่อบรรทัดอ่านได้โดยผู้ใช้ที่มีสิทธิ์เข้าถึง SR ซึ่งเป็นสิ่งที่ใกล้เคียง audit trail มากที่สุด การสร้างหน้าจอ variance-dashboard, GL-verification หรือ RBAC-console เฉพาะทางคือฟังก์ชันใหม่ ไม่ใช่ช่องว่างของเอกสาร

## 3. แหล่งอ้างอิง

- ภาพรวมแม่: [03-user-flow.md](./03-user-flow.md) — state machine กลางของ SR; ชุด persona นี้ถูกระบุไว้ที่นั่นว่าส่วนใหญ่ยังไม่ยืนยัน
- Sibling: [03-user-flow-approver.md](./03-user-flow-approver.md) + [03-user-flow-fulfiller.md](./03-user-flow-fulfiller.md) — กลไก `/approve` / `/reject` ทั่วไปจริงที่ผู้ถือขั้น workflow คนใดก็ตาม (รวมถึงคนที่ tenant ตั้งชื่อว่า "Inventory Controller") ใช้อยู่วันนี้
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — เป้าหมาย escalation ความคลาดเคลื่อนที่เวอร์ชันก่อนหน้าของหน้านี้บรรยาย; ตัวมันเองก็ยังไม่ยืนยัน
- Business rules: [02-business-rules.md](./02-business-rules.md) § 2 (`SR_VAL_014`, mark ว่ายังไม่ยืนยัน), § 4 (`SR_AUTH_009`–`SR_AUTH_013`, แก้ไขแล้ว), § 5 (`SR_POST_007`, `SR_POST_009`, `SR_POST_010`, `SR_POST_013`, แก้ไขแล้ว), § 6 (`SR_XMOD_008`, mark ว่ายังไม่ยืนยัน)
- `../carmen/docs/store-requisitions/SR-Overview.md` § User Roles → แถว Manager — แหล่งออกแบบ legacy สำหรับ role "Manager" ที่ยุบ Inventory Controller / Finance Manager / Sysadmin เป็นตัวเดียว; ถือเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมปัจจุบันที่ยืนยันแล้ว
