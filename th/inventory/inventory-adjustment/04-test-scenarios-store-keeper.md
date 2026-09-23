---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Store Keeper
description: Test cases สำหรับการกรอกเอกสาร Stock-In / Stock-Out — save draft, commit เพื่อ post พร้อม guard วันที่ในงวดและ on-hand
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment)
> **หมวดหมู่:** Happy Path &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **Executable coverage:** ไม่มีที่ automate — แคตตาล็อก manual `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (60 เคส; TC-IADJ-03xxxx ฟอร์มใหม่, TC-IADJ-05xxxx items, TC-IADJ-06xxxx commit/void); ดู [04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) § 5

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | -------------- | ------- | -------- |
| SK-HP-01 | Stock-In draft แล้ว commit (BU แบบ Average) | สินค้า `P-1` ที่ `LOC-A` ต้นทุนปัจจุบัน `฿10.00`; `si_date` อยู่ในงวดปัจจุบัน | 1. Add Stock-In 2. Reason (`stock_in`), ตำแหน่ง `LOC-A` 3. เพิ่มบรรทัด `P-1`, `qty = 10`; `cost_per_unit` เติมเริ่มต้น `฿10.00` เปลี่ยนเป็น `฿12.00` 4. **Save** 5. **Commit** → ยืนยัน | ขั้นที่ 4: `POST /stock-ins` → `draft`, `si_no` ออกเลขจาก `si_date`, ไม่มี ledger rows ขั้นที่ 5: `PATCH /stock-ins/{id}/commit` → `completed`; หนึ่ง `tb_inventory_transaction` (`stock_in`), layer ขาเข้า `in_qty 10 @ ฿12.00`, lot `{code ของ LOC-A}{YYMM}{seq4}`, `average_cost_per_unit` ถูก restamp; on-hand +10 |
| SK-HP-02 | Commit ตรงจากฟอร์มใหม่ | เหมือน SK-HP-01 แต่กด **Commit** โดยไม่ save | Frontend `POST` draft แล้ว commit ด้วย `doc_version` ที่คืนมา; สถานะปลายทางเหมือน SK-HP-01 |
| SK-HP-03 | Stock-Out สำหรับของแตก สินค้า FIFO | BU แบบ FIFO; `P-2` ที่ `LOC-A`: 5 @ `฿10.00` (`lot_seq_no 1`), 3 @ `฿12.00` (`lot_seq_no 2`); `so_date` อยู่ในงวดปัจจุบัน | 1. Add Stock-Out, reason (`stock_out`), `LOC-A` 2. บรรทัด `P-2`, `qty = 6` (ไม่มีคอลัมน์ต้นทุน) 3. Save 4. Commit | `createFifoConsumption` บริโภค 5 จาก lot 1 และ 1 จาก lot 2 — layer ขาออกสองแถวที่ต้นทุนของ lot นั้น ๆ; `tb_stock_out_detail.cost_per_unit`/`total_cost` คงเป็น `0`; on-hand 8 → 2 |
| SK-HP-04 | เอกสารหลายบรรทัด | สองสินค้าที่ location เดียวกัน | เพิ่มทั้งสองบรรทัด, Save, Commit | หนึ่ง header, สองแถว detail, หนึ่ง `tb_inventory_transaction` ต่อบรรทัดตอน commit |
| SK-HP-05 | ปริมาณเศษส่วน | สินค้าที่มีหน่วยแบบเศษส่วน (กก.) | บรรทัด `qty = 1.5` | ยอมรับ (`qty ≥ 0`, `Decimal(20,5)`) |
| SK-HP-06 | แก้ไข draft | draft จาก SK-HP-01 ก่อนขั้นที่ 5 | เปิด → **Edit** → เปลี่ยน qty → **Save** | `PATCH /stock-ins/{id}/save`; `doc_version` เพิ่มขึ้น; ยังเป็น `draft`; ไม่มี ledger rows |

## 2. Validation / Error

| # | Scenario | Trigger | Error ที่คาดหวัง |
| - | -------- | ------- | ------------------ |
| SK-VAL-01 | ไม่มีตำแหน่ง | Save โดย `location_id` ว่าง | Zod ฝั่ง client block; API โดยตรง → 400 `Location is required for stock in` / `…stock out` |
| SK-VAL-02 | ปริมาณติดลบ | บรรทัด `qty = -1` | Client ปฏิเสธ (`min 0`) |
| SK-VAL-03 | ไม่มีบรรทัดสินค้า | Save โดยไม่มีบรรทัดเลย | Client (`atLeastOneItem`); API โดยตรง → 400 `Stock in detail items are required` |
| SK-VAL-04 | Product id ที่ไม่รู้จัก | API โดยตรงด้วย `product_id` ที่ไม่รู้จัก | Enrichment ปฏิเสธบรรทัด / `PRODUCT_NOT_FOUND` บน endpoint ของ detail |
| SK-VAL-05 | ต้นทุนติดลบบน Stock-In | `cost_per_unit = -1` | Client ปฏิเสธ (`minZero`) |
| SK-VAL-06 | สต๊อกไม่พอบน Stock-Out | qty ที่ขอ > on-hand ที่ location (วิธีคิดต้นทุนใดก็ตาม) | **Commit** → 400 `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`); draft ยังอยู่ ไม่มีอะไร post |
| SK-VAL-07 | Stock-in ลงวันที่ในงวดที่ปิดแล้ว | `si_date` ก่อนงวดเปิดที่เร็วสุด | Client `dateOutsidePeriod`; API โดยตรง → 422 `The stock-in date does not fall inside any open period` ตอน create **และ** ตอน commit |
| SK-VAL-08 | Stock-out ลงวันที่นอกงวดปัจจุบัน | `so_date` ในงวดก่อนหน้า (แม้ยังเปิดอยู่) | 422 `Stock-outs can only be dated inside the current period ({period}: {start} to {end})` ตอน create และ commit; 422 `No inventory period is open…` เมื่อไม่มีงวดเปิดเลย |
| SK-VAL-09 | คำอธิบายว่าง | Save โดย `description` ว่าง | ยอมรับ — optional |
| SK-VAL-10 | Commit สองครั้ง | Commit เอกสารที่ completed แล้ว (API) | 400 `Only a draft Stock In can be committed` |
| SK-VAL-11 | เปลี่ยนสถานะผ่าน save | `PATCH /save` ด้วย `doc_status: "completed"` | 400 `doc_status cannot be changed on save — use the commit or void endpoint` |

## 3. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| SK-EDGE-01 | Reason/ทิศทางไม่ตรงกันผ่าน API | create ของ stock-in อ้างอิง reason ประเภท `stock_out` | ไม่ถูกปฏิเสธฝั่ง server (enrichment ตรวจเพียงว่าแถวมีอยู่) |
| SK-EDGE-02 | Location ประเภท Direct-cost ผ่าน API | `location_type = direct` | ไม่ถูกปฏิเสธฝั่ง server; มีเพียง picker ที่กรอง |
| SK-EDGE-03 | ข้อเสนอต้นทุนสำหรับคู่สินค้า/ตำแหน่งใหม่ | ไม่มีข้อมูลต้นทุนก่อนหน้า | `useProductCostByLocationQty` ไม่คืนต้นทุน; ฟิลด์คงว่าง/0 และแก้ไขได้ |
| SK-EDGE-04 | `expired_at` บนบรรทัด stock-in | ส่งผ่าน API เท่านั้น | Persist บน `tb_stock_in_detail.expired_at` และคืนโดย `GET /details`; ฟอร์มไม่มีช่องกรอก |
| SK-EDGE-05 | draft ค้างอยู่ตอนปิดงวด | draft ลงวันที่ในงวด | Block **Start Period Close** จนกว่าจะ commit หรือลบ |
| SK-EDGE-06 | Stock movements หลัง commit | เอกสารที่ completed | `GET /stock-ins/{id}/stock-movements` list แต่ละบรรทัดที่ post แล้วพร้อม lot, qty, ต้นทุน และ `transaction_type` |

## 4. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios)
- User flow: [03-user-flow-store-keeper](/th/inventory/inventory-adjustment/03-user-flow-store-keeper)
- กติกาทางธุรกิจ: [02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) — `ADJ_VAL_001`–`ADJ_VAL_015`, `ADJ_CALC_001`–`ADJ_CALC_009`, `ADJ_POST_001`–`ADJ_POST_003`
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — ผลกระทบฝั่ง ledger ของทุก commit; [costing](/th/inventory/costing) — การแก้ไขต้นทุน FIFO/Average
