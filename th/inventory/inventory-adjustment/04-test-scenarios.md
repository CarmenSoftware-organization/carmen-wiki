---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios
description: Test cases สำหรับวงจรชีวิต draft → commit → void ของการปรับสต๊อก บวก pointer ไปยัง E2E coverage
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios

> **At a Glance**
> **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Store Keeper, Inventory Controller (หน้าจอเดียวกันที่ไม่แตกต่างกัน); Finance และ Audit/Config ไม่มี surface ที่ตรงกัน — ดูหน้าของแต่ละตัว
> **ข้อเท็จจริงหลักที่กำหนดทุก scenario ด้านล่าง:** การสร้างเขียน `draft`; **Commit** post; **Void** กลับรายการ (UI: เฉพาะ draft; เอกสารที่ post แล้วผ่าน API)
> **Executable coverage (2026-09-22):** ไม่มี Playwright spec ที่ exercise หน้าจอนี้ แคตตาล็อก manual `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (60 เคส, ตรวจซ้ำกับฟอร์มที่ออกแบบใหม่ 2026-09-20 — ครอบคลุม Commit, Void ต้องอยู่ในโหมด Edit, Delete ในโหมด view, filter สถานะ) และ user story ที่ generate `docs/user-stories/730-inventory-adjustment.md` (32) `tests/031-adjustment-type.spec.ts` ครอบคลุมเฉพาะ master ของ reason code

## 1. ภาพรวม

หน้านี้ฉบับ 2026-07-15 จำกัดขอบเขตอยู่ที่เอกสารที่เป็น completed เสมอพร้อมปุ่ม Edit/Void ที่ตายแล้ว ตั้งแต่ backend แยก create/commit เมื่อ 2026-07-30 และการออกแบบฟอร์มใหม่ในวันเดียวกัน โมดูลมีวงจรชีวิตสามสถานะจริง ดังนั้น scenario ด้านล่างจึงถูก re-base บน `create()` (draft), `update()` (save), `commit()`, `delete()`, `voidStockIn()`/`voidStockOut()`, guard วันที่ในงวด และการตรวจ on-hand ล่วงหน้าของ stock-out Rule ID อ้างอิงถึง [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules)

## 2. Persona ในขอบเขต

- **Store Keeper**: กรอกเอกสาร Stock-In/Stock-Out, save draft, commit
- **Inventory Controller**: review draft, commit, ลบ/void, อ่านเอกสารที่ completed และ stock movements ของมัน; void เอกสารที่ post แล้วผ่าน API
- **Finance**: ไม่มี surface ที่ตรงกัน — ดู [04 — Test Scenarios — Finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance)
- **Audit / Config**: ไม่มี surface ที่ตรงกัน นอกเหนือจาก master ของ reason code — ดู [04 — Test Scenarios — Audit / Config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)

## 3. ไฟล์ Test ตาม Persona

- [Store Keeper scenarios](/th/inventory/inventory-adjustment/04-test-scenarios-store-keeper)
- [Inventory Controller scenarios](/th/inventory/inventory-adjustment/04-test-scenarios-inventory-controller)
- [Finance scenarios](/th/inventory/inventory-adjustment/04-test-scenarios-finance)
- [Audit / Config scenarios](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)

## 4. Scenario ข้ามขอบเขต

| # | Scenario | Pre-condition | Expected end state |
| - | -------- | -------------- | ------------------- |
| 1 | Save สร้าง draft ไม่ใช่การ post | ฟอร์ม Stock-In/Stock-Out ที่ valid ใด ๆ; กด **Save** | `POST` คืน `doc_status = draft`; ไม่มี `tb_inventory_transaction`; on-hand ไม่เปลี่ยน; หน้าจอคงอยู่ที่ `/{id}?type=…` ในโหมด view โดยมี **Edit** และ **Delete** แสดง |
| 2 | Commit post และ lock | draft; กด **Commit** → ยืนยัน | `PATCH /{id}/commit` → `completed`; หนึ่ง ledger transaction ต่อบรรทัดพร้อม `inventory_transaction_id` ที่ stamp แล้ว; on-hand ขยับ; Edit / Delete / Void ไม่แสดงอีกต่อไป (`isReadOnly`) แต่ **Print** และ **Stock movements** แสดง (`TC-IADJ-060002`, `TC-IADJ-020005`) |
| 3 | Commit จากฟอร์มใหม่ | ฟอร์มที่ยังไม่ save; กด **Commit** | Frontend `POST` draft ก่อน แล้ว `PATCH /{id}/commit` ด้วย `doc_version` ที่คืนมา — เอกสาร completed หนึ่งฉบับ ไม่มี draft กำพร้า |
| 4 | Gate validation ของ Commit | ฟอร์มไม่ valid (ไม่มีตำแหน่ง / reason / บรรทัด); กด **Commit** | แสดง error ของ Zod; confirm dialog ไม่เปิดเลย; ไม่มี request ถูกส่ง (`TC-IADJ-060003`) |
| 5 | Void บน draft (UI) | เปิด draft → **Edit** → **Void** พร้อมเหตุผล | `DELETE /{id}/void` → `voided` + `deleted_at`; ไม่มีอะไรให้กลับรายการ; เอกสารหายจากหน้ารายการ (`TC-IADJ-060001`) |
| 6 | Void บนเอกสารที่ post แล้ว (API) | stock-in ที่ completed; on-hand พอ | `DELETE /{id}/void` → `adjustment_out` กลับรายการต่อบรรทัด; `voided` + soft-delete; หน้ารายการไม่แสดงอีกต่อไป ไม่มี path ใน UI สำหรับกรณีนี้ |
| 7 | กฎการลบ | Draft: action ลบในโหมด view → หายไป Completed: การเรียกเดียวกัน (API เท่านั้น) → 400 `Cannot delete a completed Stock In — inventory has already been adjusted` |
| 8 | ปฏิสัมพันธ์กับ period-end | stock-in ที่เป็น draft ลงวันที่ในงวดปัจจุบัน | **Start Period Close** ถูก block โดย draft ถูก list ใน "Finish these documents first"; การ commit หรือลบมันปลด block |

## 5. การ Map E2E Test

| Spec / แคตตาล็อก | Coverage |
| ---- | -------- |
| `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (แคตตาล็อก, 60) | หน้ารายการ (คอลัมน์, badge `Type`, filter สถานะรวมถึง `In Progress` ที่ไม่เคย match), ฟอร์มใหม่/แก้ไข, การ gate ของ Commit / Void / Delete, เอกสาร completed แบบ read-only ยังไม่ automate |
| `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` | CRUD master data ของ reason code (`tb_adjustment_type`) เท่านั้น |
| `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` + `docs/test-cases/gaps/900-period-end-gap.md` | การ์ดและลิงก์ SI/SO บน review ของ period-end (`TC-PE-320102`), SI/SO ที่เป็น draft เป็นตัว block การเริ่มนับ |

ช่องว่าง: ไม่มี automated test สำหรับ Save/Commit/Void, guard วันที่, การตรวจ on-hand ล่วงหน้า หรือแผง stock-movements

## 6. แหล่งอ้างอิง

- ส่วนคู่ขนาน: [03-user-flow](/th/inventory/inventory-adjustment/03-user-flow) — วงจรชีวิตที่ทุก scenario ด้านบนอิงตาม
- ส่วนคู่ขนาน: [02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) — rule ID ที่อ้างอิง
- รายละเอียดตาม persona: [Store Keeper](/th/inventory/inventory-adjustment/04-test-scenarios-store-keeper), [Inventory Controller](/th/inventory/inventory-adjustment/04-test-scenarios-inventory-controller), [Finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance), [Audit / Config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)
