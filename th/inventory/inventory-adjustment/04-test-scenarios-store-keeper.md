---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Store Keeper
description: Test cases สำหรับการกรอกเอกสาร Stock-In / Stock-Out ซึ่ง post ทันทีไม่ว่าจะกดปุ่มไหน
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment)
> **หมวดหมู่:** Happy Path &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** ไม่มีที่เจาะจงหน้าจอนี้ — ดู [04-test-scenarios.md](./04-test-scenarios.md) § 5

หน้านี้รวบรวม test scenario สำหรับการกรอกเอกสาร Stock-In หรือ Stock-Out ไม่มีส่วน permission ที่แตกต่างจากผู้ใช้อื่นของโมดูล (ดู [02-business-rules.md](./02-business-rules.md) § 4) และไม่มีสถานะรอ/อนุมัติให้ทดสอบ — ทุก scenario ด้านล่างจบด้วยเอกสารที่ `completed` แล้วและ post แล้ว หรือการเรียก create/void ถูกปฏิเสธไปเลย

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | -------------- | ------- | -------- |
| SK-HP-01 | Stock-In สำหรับสินค้าที่มีอยู่ใช้ Average costing | สินค้า `P-1` มี on-hand ที่ `LOC-A` ต้นทุนเฉลี่ยปัจจุบัน `฿10.00` | 1. Add Stock-In 2. เลือก reason ทิศทาง `stock_in` 3. เลือก `LOC-A` 4. เพิ่มบรรทัด: `P-1`, `qty = 10`; `cost_per_unit` เติมเริ่มต้น `฿10.00` (แก้ไขได้) 5. กด **Save** | เอกสารถูกสร้างที่ `doc_status = completed`; `tb_inventory_transaction` ถูกเขียน (`inventory_doc_type = stock_in`); ค่าเฉลี่ยใหม่คำนวณผ่าน `calculateNewAverageCost`; on-hand ที่ `(LOC-A, P-1)` เพิ่มขึ้น 10 |
| SK-HP-02 | Stock-In สำหรับสินค้าที่มีอยู่ กด Submit แทน Save | เหมือน SK-HP-01 แต่กด **Submit** แทน **Save** | ผลลัพธ์เหมือนกันทุกประการกับ SK-HP-01 — ทั้งสองปุ่มเรียก `create()` เดียวกัน และ backend ไม่สนใจ `doc_status` ที่ client ส่งมา (ดู [03-user-flow.md](./03-user-flow.md) § 2.1) |
| SK-HP-03 | Stock-Out สำหรับของแตก สินค้าใช้ FIFO | สินค้า FIFO `P-2` มีสอง lot ที่ `LOC-A`: 5 หน่วยที่ `฿10.00` (`lot_seq_no=1`), 3 หน่วยที่ `฿12.00` (`lot_seq_no=2`) | 1. Add Stock-Out 2. เลือก reason ทิศทาง `stock_out` 3. เลือก `LOC-A` 4. เพิ่มบรรทัด: `P-2`, `qty = 6` — ไม่มีฟิลด์ต้นทุนแสดง 5. Save | เอกสาร `completed`; `createFifoConsumption` บริโภค 5 หน่วยจาก lot เก่า และ 1 หน่วยจาก lot ใหม่กว่า เขียนแถว cost-layer ขาออกสองแถว; `tb_stock_out_detail.cost_per_unit`/`total_cost` คงเป็น `0` (ไม่เคยเขียนโดย `create()` สำหรับ stock-out) |
| SK-HP-04 | เอกสารหลายบรรทัด | สองสินค้าที่ location เดียวกัน ต่ำกว่าขีดจำกัด on-hand ใด ๆ | 1. เพิ่มบรรทัดสำหรับทั้งสองสินค้า 2. Save | หนึ่ง header, สองแถว detail, สอง (หรือมากกว่า) แถว `tb_inventory_transaction_detail` ภายใต้ `tb_inventory_transaction` เดียว — หนึ่งทรานแซกชันต่อบรรทัด detail ไม่ใช่หนึ่งต่อเอกสาร |
| SK-HP-05 | ปริมาณเศษส่วนที่เท่ากับหรือมากกว่า 1 | สินค้าที่มีหน่วยแบบเศษส่วน (เช่น กก.) | บรรทัด `qty = 1.5` | ยอมรับ — `qty >= 1` ผ่าน ตรงข้ามกับ SK-VAL-02 ด้านล่าง |

## 2. Validation / Error

| # | Scenario | Trigger | Error ที่คาดหวัง |
| - | -------- | ------- | ------------------ |
| SK-VAL-01 | ไม่มีตำแหน่ง | Submit โดย `location_id` ว่าง | Client ปฏิเสธก่อนจะ submit ได้ (Zod `.min(1)`); การเรียก API โดยตรงด้วย `location_id` ว่างคืน `"Location is required for stock in"` / `"...stock out"` |
| SK-VAL-02 | ปริมาณเศษส่วนต่ำกว่า 1 | บรรทัด `qty = 0.5` | Client ปฏิเสธด้วยข้อความ `minNumber` — `qty` ต้อง `>= 1` ไม่ใช่แค่ `> 0` |
| SK-VAL-03 | ไม่มีบรรทัดสินค้า | Submit โดยไม่มีบรรทัดเลย | Client ปฏิเสธ (`atLeastOneItem`); การเรียก API โดยตรงด้วย array `add` ว่างคืน `"Stock in detail items are required"` / `"...out..."` |
| SK-VAL-04 | Product id ที่ไม่รู้จัก | บรรทัดอ้างอิง `product_id` ที่ไม่มีแถว `tb_product` ตรงกัน (เรียก API โดยตรง) | `"Product not found: <id>"` — การสร้างทั้งหมดถูกปฏิเสธ ไม่ใช่แค่บรรทัดที่ผิด |
| SK-VAL-05 | ต้นทุนติดลบบน Stock-In | บรรทัด `cost_per_unit = -1` (bypass การเรียก API โดยตรง) | Client ปฏิเสธด้วยข้อความ `minZero`; ไม่เกี่ยวข้องกับ Stock-Out ซึ่งไม่แสดงฟิลด์ต้นทุนและไม่ persist อยู่แล้ว |
| SK-VAL-06 | สต๊อกไม่พอบน Stock-Out (สินค้า Average) | `qty` ที่ขอเกิน on-hand ปัจจุบันที่ location | การสร้างทั้งหมดล้มเหลวด้วย `"Insufficient stock. Requested: <X>, Available: <Y>"` — แสดงต่อผู้ใช้ผ่าน path error-toast พิเศษ (`handleMutationError`) ที่แสดงข้อความดิบจาก server **ยืนยันเฉพาะสินค้าที่ใช้ Average costing** — พฤติกรรมของ FIFO ภายใต้เงื่อนไขเดียวกันยังไม่ได้ยืนยันแยกต่างหากในรอบนี้ |
| SK-VAL-07 | วันที่นอกงวดปัจจุบัน | เลือกวันที่ก่อน `currentPeriod.start_at` หรือหลัง `currentPeriod.end_at` | Client ปฏิเสธด้วยข้อความ `dateOutsidePeriod` **ฝั่ง client เท่านั้น** — ไม่พบการตรวจสอบเทียบเท่าฝั่ง backend |
| SK-VAL-08 | คำอธิบายว่าง | Submit โดย `description` ว่าง | ยอมรับ — `description` มี `.max(256)` แต่ไม่มี `.min()`; เป็น optional |

## 3. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| SK-EDGE-01 | Reason/ทิศทางไม่ตรงกันผ่าน API โดยตรง | การเรียก create ของ `tb_stock_in` อ้างอิง `adjustment_type_id` ที่มี `type = stock_out` | ยังไม่ยืนยันว่าถูกปฏิเสธฝั่ง server — `validateAndEnrichHeader` ตรวจเพียงว่าแถวมีอยู่จริง ไม่ตรวจ `type` ถือว่ายังไม่ยืนยัน/มีแนวโน้มยอมรับ จนกว่าจะทดสอบตรงกับ backend ที่รันอยู่จริง |
| SK-EDGE-02 | Location ประเภท Direct-cost ผ่าน API โดยตรง | การเรียก create อ้างอิง `location_id` ที่ `location_type` เป็น `direct` (ไม่ใช่ Inventory/Consignment) | ยังไม่ยืนยันว่าถูกปฏิเสธฝั่ง server — มีเพียง picker ที่กรองตามประเภทฝั่ง client |
| SK-EDGE-03 | ข้อเสนอต้นทุน Stock-In สำหรับคู่สินค้า/ตำแหน่งใหม่ทั้งคู่ | `useProductCostByLocationQty` ไม่มีข้อมูลก่อนหน้าสำหรับคู่ `(product, location)` นั้น | พฤติกรรมของ `cost_per_unit` ที่เสนอในกรณีนี้ (ศูนย์ vs ว่าง vs error) ยังไม่ได้ยืนยันแยกต่างหากในรอบนี้ |
| SK-EDGE-04 | Delete จากหน้ารายการบนเอกสารที่ completed แล้ว | คลิก Delete จากเมนูแถว → Confirm | Dialog ลบเปิดขึ้น (ปุ่มแสดงผลเสมอ); mutation คืน `"Cannot delete a completed Stock In — inventory has already been adjusted"` — 400 แสดงเป็น error toast และแถวยังคงอยู่ |
| SK-EDGE-05 | พยายามเข้าถึงปุ่ม Edit หรือ Void | เปิดหน้ารายละเอียดของเอกสาร completed | ไม่มีปุ่มไหนแสดงผล — `isReadOnly` เป็น true เสมอสำหรับเอกสารที่ persist แล้ว ปุ่ม Edit (`isView && !isReadOnly`) จึงไม่ปรากฏ และ Void (ต้องการ `isEdit`) จึงเข้าไม่ถึงตามไปด้วย |

## 4. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios.md](./04-test-scenarios.md) — scenario ข้ามขอบเขต (Save vs Submit, Edit/Void ที่ตายแล้ว, Delete ในหน้ารายการล้มเหลวเสมอ, void-ก็-soft-delete)
- User flow: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md)
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) — `ADJ_VAL_001`–`ADJ_VAL_013`, `ADJ_CALC_001`–`ADJ_CALC_007`, `ADJ_POST_001`
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — ผลกระทบฝั่ง ledger ของทุกการ post
- ที่เกี่ยวข้อง: [costing](/th/inventory/costing) — การแก้ไขต้นทุน FIFO/Average
