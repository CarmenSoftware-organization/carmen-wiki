---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios
description: Test cases สำหรับวงจรชีวิตจริง (เป็น completed เสมอ) ของการปรับสต๊อก บวกช่องว่างของ E2E coverage
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios

> **At a Glance**
> **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Store Keeper, Inventory Controller (หน้าจอเดียวกันที่ไม่แตกต่างกัน); Finance และ Audit/Config ไม่มี surface ที่ตรงกัน — ดูหน้าของแต่ละตัว
> **ข้อเท็จจริงหลักที่กำหนดทุก scenario ด้านล่าง:** การสร้าง post ทันทีเสมอ — ไม่มีสถานะรอ/อนุมัติให้ทดสอบ และ Edit/Void เข้าไม่ถึงผ่าน UI สำหรับเอกสารที่ persist แล้ว
> **หน้าย่อยของแต่ละ persona คือ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เวอร์ชันก่อนหน้าจัดระเบียบ scenario ประมาณ 150 รายการรอบห่วงอนุมัติหลายบทบาทที่ gate ด้วย threshold ซึ่งไม่มีอยู่จริงใน implementation ปัจจุบัน (ดู [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) § 1 และ § 4) การเขียนใหม่นี้คงรูปทรงเดียวกัน — happy path, permission, validation, edge case — แต่จำกัดขอบเขตทุก scenario ให้ตรงกับสิ่งที่ `create()`, `update()`, `delete()`, `voidStockIn()`/`voidStockOut()` และ Zod schema ทำจริง ไม่มี `inventory-adjustment.spec.ts` E2E เฉพาะ; spec เดียวที่แตะ surface ของโมดูลนี้เองคือ `031-adjustment-type.spec.ts` ซึ่งครอบคลุม master ของ reason code ไม่ใช่หน้าจอ Stock-In/Stock-Out เอง

## 2. Persona ในขอบเขต

- **Store Keeper**: กรอกเอกสาร Stock-In/Stock-Out; ทุกเอกสารที่สร้าง post ทันทีไม่ว่าจะกดปุ่มไหน
- **Inventory Controller**: ใช้หน้าจอสร้างเดียวกัน นอกเหนือจากนั้นก็อ่านผล list/detail/print เนื่องจากไม่มีอะไรถูกทิ้งไว้ให้อนุมัติ
- **Finance**: ไม่มี surface ที่ตรงกัน — ดูประกาศแก้ไขใน [04 — Test Scenarios — Finance](./04-test-scenarios-finance.md)
- **Audit / Config**: ไม่มี surface ที่ตรงกัน นอกเหนือจาก master ของ reason code ทั่วไป — ดูประกาศแก้ไขใน [04 — Test Scenarios — Audit / Config](./04-test-scenarios-audit-config.md)

## 3. ไฟล์ Test ตาม Persona

- [Store Keeper scenarios](./04-test-scenarios-store-keeper.md)
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้ามขอบเขต

| # | Scenario | Pre-condition | Expected end state |
| - | -------- | -------------- | ------------------- |
| 1 | Save และ Submit ให้ผลลัพธ์เดียวกันทุกประการ | ฟอร์ม Stock-In/Stock-Out ที่ valid ใด ๆ | ทั้งสองปุ่มเรียก `create()`; backend เขียน `doc_status = completed` และ post ledger ไม่ว่าทางไหน — ไม่มีความแตกต่างที่สังเกตได้ระหว่างสอง path |
| 2 | Edit เข้าไม่ถึงบนเอกสารจริง | เอกสาร `completed` ใด ๆ เปิดในโหมด view | `isReadOnly = true` (เนื่องจาก `doc_status === 'completed'`); ปุ่ม Edit (`isView && !isReadOnly`) ไม่แสดงผล |
| 3 | Void เข้าไม่ถึงผ่าน UI | เอกสาร `completed` ใด ๆ | ปุ่ม Void ต้องการ `isEdit` ซึ่งเข้าถึงได้เฉพาะผ่านปุ่ม Edit (ที่เข้าไม่ถึง) — Void ไม่เคยแสดงผล การ `PATCH` โดยตรงด้วย `doc_status: "voided"` ทำงานได้จริงฝั่ง server (ดู `04-test-scenarios-inventory-controller.md` IC-HP-02) |
| 4 | Delete ในหน้ารายการล้มเหลวเสมอ | เอกสาร `completed` ใด ๆ จากเมนูแถวของหน้ารายการ | การคลิก Delete → Confirm เรียก mutation delete ซึ่งคืนค่า `"Cannot delete a completed Stock In — inventory has already been adjusted"` (หรือเทียบเท่าของ Stock-Out) — 400 แสดงเป็น error toast |
| 5 | การ void เอกสารทำให้หายจากหน้ารายการ | เอกสารที่ void ผ่านการเรียก API โดยตรง | `voidStockIn`/`voidStockOut` ตั้งค่า `deleted_at` พร้อมกับ `doc_status = voided`; endpoint ของ list และ detail ทั้งคู่กรอง `deleted_at: null` เอกสารจึงหายไปจากทั้งคู่ แทนที่จะแสดง badge "Voided" |

## 5. การ Map E2E Test

| Spec | Coverage |
| ---- | -------- |
| [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) | CRUD master data ของ reason code (`tb_adjustment_type`) — code ไม่ซ้ำ, toggle active/inactive, list/search ไม่ครอบคลุมหน้าจอ Stock-In/Stock-Out เอง |

ไม่พบ spec ที่ทดสอบการสร้าง Stock-In/Stock-Out, cost-suggestion probe, การปฏิเสธเมื่อสต๊อกไม่พอ หรือ void endpoint สิ่งเหล่านี้เป็นช่องว่าง ไม่ใช่ coverage "manual/planned" ตามที่หน้านี้เวอร์ชันก่อนหน้ากล่าวอ้าง — ไม่พบ test-plan annotation ที่อ้างอิงถึงสิ่งเหล่านี้เช่นกัน

## 6. แหล่งอ้างอิง

- ส่วนคู่ขนาน: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิตแบบเป็น completed เสมอที่ทุก scenario ด้านบนอิงตาม
- ส่วนคู่ขนาน: [02-business-rules.md](./02-business-rules.md) — rule ID ที่อ้างอิงข้างต้น
- รายละเอียดตาม persona: [Store Keeper](./04-test-scenarios-store-keeper.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md)
