---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Inventory Controller
description: Test cases สำหรับการ review draft, commit, ลบ/void และการอ่านเอกสารที่ completed — ไม่มี approval queue
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (permission/หน้าจอเดียวกับ Store Keeper) &nbsp;·&nbsp; **โมดูล:** [inventory-adjustment](/th/inventory/inventory-adjustment)
> **หมวดหมู่:** Happy Path (review, commit, void) &nbsp;·&nbsp; Edge Case
> **Executable coverage:** ไม่มีที่ automate — แคตตาล็อก manual `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (TC-IADJ-01xxxx หน้ารายการ, TC-IADJ-02xxxx รายละเอียด/read-only, TC-IADJ-06xxxx void/commit)

## 1. Happy Path

| # | Scenario | Pre-condition | ขั้นตอน | Expected |
| - | -------- | -------------- | ------- | -------- |
| IC-HP-01 | อ่านหน้ารายการรวม | มี Stock-In และ Stock-Out ทั้งที่เป็น draft และ completed | 1. เปิดหน้ารายการ 2. กรอง `adj_type` / สถานะ / วันที่ / คำค้น | ทั้งสองประเภทรวมกันโดย service `inventory-adjustments` ของ gateway (ดึงทั้งหมดจากทั้งสอง upstream, เรียง, แบ่งหน้าในหน่วยความจำ); สถานะแสดงเป็น icon + label (`draft` / `completed`; แถว `voided` ถูก soft-delete และไม่ปรากฏ) |
| IC-HP-02 | Commit draft ของ Store Keeper | Stock-Out ที่เป็น draft; on-hand พอ | 1. เปิด draft 2. **Commit** → ยืนยัน | `PATCH /stock-outs/{id}/commit` → `completed`; ledger rows ถูกเขียน; กลับไปหน้ารายการ |
| IC-HP-03 | Void เอกสารที่ post แล้วผ่าน API | Stock-In ที่ completed `P-1 qty 10` ที่ `LOC-A`; on-hand ≥ 10 | `DELETE /{bu}/stock-ins/{id}/void` `{ void_reason }` พร้อม token ที่ valid | `voidStockIn`: ตรวจว่ายัง void ไม่ได้ทำ, ตรวจ on-hand, `executeAdjustmentOut` กลับรายการต่อบรรทัดที่ post แล้ว, `doc_status = voided`, ตั้ง `deleted_at`, เก็บ `info.void_reason`; เอกสารออกจาก list/detail |
| IC-HP-04 | พิมพ์เอกสารที่ post แล้ว | เอกสาร `completed` ใด ๆ | รายละเอียด → **Print** | `GET /stock-ins/{id}/print-viewer` (FastReport); ปุ่มแสดงในโหมด view (`canPrint = isView && !!id`) |
| IC-HP-05 | อ่าน stock movements | เอกสาร `completed` ใด ๆ | รายละเอียด → แผง stock-movements | `GET /{id}/stock-movements` คืนหนึ่งบรรทัดต่อ detail ที่ post แล้ว พร้อม lot, qty, ต้นทุน และ `transaction_type` (`adjustment_in` / `adjustment_out`) |
| IC-HP-06 | Void โดย on-hand ไม่พอ | Stock-In ที่ completed `qty 10`; on-hand ลดลงเหลือ 4 แล้ว | เรียก void โดยตรง | ถูกปฏิเสธ: `Cannot void: product P-1 has insufficient on-hand qty (4) at this location to reverse 10` |
| IC-HP-07 | Void เอกสารที่ void ไปแล้ว | `doc_status = voided` | เรียก void โดยตรง | 400 `Stock in is already voided` / `Stock out is already voided` |

## 2. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| IC-EDGE-01 | ปุ่ม Void บนเอกสารที่ completed | เปิดเอกสารที่ completed | ไม่มี **Edit** (`isView && !isReadOnly` เป็น false) จึงไม่มี **Void** (`canVoid = isEdit && …`); การกลับรายการทำได้ผ่าน API เท่านั้น |
| IC-EDGE-02 | ลบเอกสารที่ completed | เรียกลบผ่าน API (หน้ารายละเอียดซ่อนปุ่มเมื่อ `isReadOnly`) | 400 `Cannot delete a completed Stock In — inventory has already been adjusted` |
| IC-EDGE-03 | filter สถานะ `In Progress` | เลือก `In Progress` ใน filter ของหน้ารายการ | ไม่คืนอะไร — ไม่มี code path ใดตั้ง `in_progress` บน `tb_stock_in`/`tb_stock_out` |
| IC-EDGE-04 | แถวจาก physical-count ในหน้ารายการ | physical count ถูก submit พร้อม variance | แถว `tb_stock_in`/`tb_stock_out` ของมันปรากฏเป็น `completed` โดยไม่มี reason และ**ไม่มี stock movements** (ไม่เคย post) |
| IC-EDGE-05 | แถวจาก write-off ของ wastage ในหน้ารายการ | `POST /wastage-reporting` ถูกเรียก | Stock-Out ที่ `completed` หนึ่งฉบับต่อ location พร้อม reason ของผู้เรียก; stock movements แสดง `adjustment_out` จาก lot ที่ระบุชื่อ |
| IC-EDGE-06 | `doc_version` ล้าสมัย | สอง session แก้ไข draft เดียวกัน | save/commit ครั้งที่สองล้มเหลวเพราะ `doc_version` ไม่ตรง; reload แล้วลองใหม่ |

## 3. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios)
- User flow: [03-user-flow-inventory-controller](/th/inventory/inventory-adjustment/03-user-flow-inventory-controller)
- กติกาทางธุรกิจ: [02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) `ADJ_POST_002`–`ADJ_POST_006`, `ADJ_VAL_010`–`ADJ_VAL_015`
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — ผลกระทบฝั่ง ledger ของทั้ง commit และ void; [inventory/period-end](/th/inventory/inventory/period-end) — draft block Start Period Close
