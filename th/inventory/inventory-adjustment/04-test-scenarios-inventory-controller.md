---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Inventory Controller
description: Test cases สำหรับ view ประวัติแบบอ่านอย่างเดียว และ void endpoint ที่เข้าถึงได้เฉพาะผ่าน API โดยตรง — ไม่มี approval queue ให้ทดสอบ
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (permission/หน้าจอเดียวกับ Store Keeper) &nbsp;·&nbsp; **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment)
> **หมวดหมู่:** Happy Path (อ่านอย่างเดียว + void ผ่าน API โดยตรง) &nbsp;·&nbsp; Edge Case
> **E2E coverage:** ไม่มี — ดู [04-test-scenarios.md](./04-test-scenarios.md) § 5

หน้านี้เคยรวบรวม scenario การอนุมัติ/threshold/count-rollup ประมาณ 30 รายการสำหรับ queue review ของ Controller ที่ไม่มีอยู่จริง (ดู [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md)) สิ่งที่ยังทดสอบได้จริงสำหรับ persona นี้คือ: (a) flow สร้างเดียวกันที่ครอบคลุมแล้วใน [04-test-scenarios-store-keeper.md](./04-test-scenarios-store-keeper.md), (b) หน้ารายการ/รายละเอียด/พิมพ์แบบอ่านอย่างเดียว และ (c) void endpoint จริง ซึ่งเข้าถึงได้เฉพาะผ่านการเรียก API โดยตรง เนื่องจากตัวกระตุ้น UI ของมันไม่เคยแสดงผล

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | -------------- | ------- | -------- |
| IC-HP-01 | อ่านหน้ารายการเอกสารที่ post แล้ว | มี Stock-In และ Stock-Out อย่างน้อยหนึ่งรายการ | 1. เปิดหน้ารายการ Inventory Adjustment 2. กรองตามประเภท / สถานะ / วันที่ / คำค้น | หน้ารายการแสดงทั้งสองประเภทรวมกัน (ผ่าน endpoint `inventory-adjustments` ของ gateway ซึ่งดึงทุกแถวจาก microservice ทั้ง stock-ins และ stock-outs แล้วรวม/เรียง/แบ่งหน้าในหน่วยความจำ) |
| IC-HP-02 | Void เอกสารผ่านการเรียก API โดยตรง | `tb_stock_in` ที่ `completed` ที่ `LOC-A` สำหรับ `P-1 qty=10`; on-hand พอที่ `(LOC-A, P-1)` สำหรับกลับรายการ | เรียก `PATCH` โดยตรงไปยัง endpoint ของ stock-in ด้วย `doc_status: "voided"`, `void_reason` และ `doc_version` ปัจจุบัน (payload เดียวกับที่ `useVoidInventoryAdjustment` จะส่ง หากตัวกระตุ้น UI เข้าถึงได้) | `voidStockIn()` ทำงาน: ตรวจว่ายังไม่ถูก void, ตรวจว่ามี on-hand พอกลับรายการ, เขียนการเรียก `executeAdjustmentOut` แบบกลับรายการต่อบรรทัด จากนั้นตั้งค่า `doc_status = voided` **พร้อมกับ** `deleted_at` บน header ใน update เดียวกัน เอกสารจึงหายไปจากทั้ง list และ detail endpoint (ทั้งคู่กรอง `deleted_at: null`) |
| IC-HP-03 | พิมพ์เอกสารที่ post แล้ว | เอกสาร `completed` ใด ๆ | เปิดรายละเอียด → คลิก **Print** | ไปยัง FastReport viewer ผ่าน `inventory-adjustments.print-to-report`; ปุ่มแสดงผลเสมอในโหมด view (`canPrint = isView && !!id`) |
| IC-HP-04 | พยายาม void เอกสารที่มี on-hand ไม่พอสำหรับกลับรายการ | `tb_stock_in` ที่ `completed` สำหรับ `P-1 qty=10` ที่ `LOC-A` แต่ on-hand ที่ `(LOC-A, P-1)` ลดลงเหลือ 4 แล้ว (ถูกบริโภคโดยการ post ภายหลัง) | เรียก void โดยตรง | ถูกปฏิเสธ: `"Cannot void: product P-1 has insufficient on-hand qty (4) at this location to reverse 10"` — ยืนยันสำหรับ path void ของ stock-in; guard เทียบเท่าของ path void stock-out ยังไม่ได้ยืนยันแยกต่างหากในรอบนี้ |
| IC-HP-05 | พยายาม void เอกสารที่ void ไปแล้ว | เอกสารมี `doc_status = voided` แล้ว | เรียก void โดยตรงอีกครั้ง | ถูกปฏิเสธ: `"Stock in is already voided"` / `"Stock out is already voided"` |

## 2. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| IC-EDGE-01 | ปุ่ม Void เข้าไม่ถึงใน UI | เปิดหน้ารายละเอียดของเอกสาร `completed` ใด ๆ คลิก **Edit** | ปุ่ม Edit ไม่แสดงผล (`isView && !isReadOnly` เป็น false เนื่องจาก `isReadOnly` เป็น true เสมอสำหรับ `completed`/`voided`) จึงไม่เคยเข้าโหมดแก้ไข และปุ่ม Void (ที่ต้องการ `isEdit`) จึงไม่ปรากฏตามไปด้วย |
| IC-EDGE-02 | Delete ในหน้ารายการบนเอกสารที่ completed แล้ว | คลิก Delete จากเมนูแถว | เหมือนกับ SK-EDGE-04 ใน scenario ของ Store Keeper: แสดงผลเสมอ ล้มเหลวฝั่ง server เสมอด้วย 400 |
| IC-EDGE-03 | เอกสารที่ void แล้วหายจากรายงาน | หลังการ void สำเร็จผ่าน API โดยตรง | เอกสารหายไปจากทั้ง list และ detail endpoint (ทั้งคู่กรอง `deleted_at: null` และ void ตั้งค่านี้) — ไม่มีสถานะ badge "Voided" ที่มองเห็นได้ที่ไหนใน UI ของโมดูลนี้ ต่างจาก GRN/PO/SR ที่การ void ทิ้งแถวที่มองเห็นได้พร้อม badge |

## 3. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md)
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) `ADJ_POST_004` (void), `ADJ_VAL_012` (เงื่อนไขก่อน void)
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — ผลกระทบฝั่ง ledger ของทั้งการ post และ void
