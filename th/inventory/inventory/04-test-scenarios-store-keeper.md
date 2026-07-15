---
title: คลังสินค้า (Inventory) — Test Scenarios — Store Keeper
description: Test cases ของ Store Keeper สำหรับ Transaction Log แบบ read-only — filters, การตรวจสอบการ posting และ quirks ที่ทราบ
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **พื้นผิว:** Transaction Log แบบ read-only (`/inventory-management/transaction`)
> **Correction (2026-07-15):** ~29 scenarios เดิม (threshold auto-approve, การ route new-lot ไปยัง Controller, lot pickers, การ validate expiry ของ perishable, SoD write-off blocks, submit error แบบ negative-balance บนเอกสาร manual) อธิบาย flow การสร้าง stock-in/stock-out ที่ไม่มีอยู่ในโมดูลนี้ — ไม่มี UI สำหรับ threshold หรือ lot-entry ที่ใดเลย และเลข lot ถูก generate โดยระบบ manual adjustments เป็นของหน้าเทสของ [inventory-adjustment](/th/inventory/inventory-adjustment) เอง

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| SK-HP-01 | ตรวจสอบการ post ของ GRN บน ledger | GRN ถูก **save** แล้ว (`draft → saved`) พร้อม received lines; user ถือ `inventory_management.view` | 1. เปิด `/inventory-management/transaction` 2. ค้นหาเลข GRN | หนึ่ง row: badge ประเภท GRN, `parent_document_no` = เลข GRN, ชื่อสินค้า/location จาก detail rows, ยอด Qty In สีเขียว, จำนวน item, ต้นทุนรวม |
| SK-HP-02 | ตรวจสอบ SR issue | SR ผ่าน approval stage สุดท้ายเสร็จแล้ว | 1. Filter ด้วย ref-type pill **SR** 2. หาเลข SR | Row พร้อม badge SR; Qty Out สีแดง; transfer rows แสดง source/destination locations จาก detail lines |
| SK-HP-03 | ตรวจสอบ receipt เข้า direct-location | line ของ GRN ชี้ไปยัง location ที่ `location_type = direct` | 1. ค้นหาเลข GRN 2. เปิดดูจำนวนของ row | สอง legs ภายใต้ transaction เดียว: Qty In และ Qty Out เท่ากัน (receipt + issue `ISS-…` อัตโนมัติ); ผลสุทธิศูนย์ |
| SK-HP-04 | Summary cards สะท้อนชุดข้อมูลที่ filter | Ledger มี rows inbound/outbound ปนกัน | 1. ใช้ preset ช่วงวันที่ (เช่น 7d) 2. เทียบ cards กับ grid | สี่ cards — จำนวน transactions รวม (+ จำนวน adjustment), units inbound + ต้นทุน, units outbound + ต้นทุน, net change แบบมีเครื่องหมาย — recompute ตาม filter ที่ active (`summary` ฝั่ง server ใน list response) |
| SK-HP-05 | การผสม filter | Rows กระจายหลาย locations/categories | 1. ตั้ง lookups Location + Category + direction Inbound 2. Clear ผ่าน active-filter bar | Grid แคบลงตามแต่ละ filter; chips ของ active-filter render; **Clear all** reset state ที่เก็บใน URL |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาดหวัง |
| - | -------- | ------------------ |
| SK-PERM-01 | User ที่มี `inventory_management.view` เปิด ledger | **Allow** List render แบบ read-only |
| SK-PERM-02 | User ใด ๆ พยายามแก้ไข transaction | **Deny โดยการไม่มีอยู่ (deny by absence)** ไม่มี affordance สำหรับ create/edit/delete ใน UI และไม่มี update endpoint บน API — ledger เป็น append-only โดยโครงสร้าง ไม่ใช่โดยข้อความ guard |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| SK-VAL-01 | เอกสาร source ฝั่ง outbound เกิน balance | SR issue / adjustment-out มากกว่าจำนวนที่มี | โมดูล source แสดง `` `Insufficient stock. Requested: <X>, Available: <Y>` ``; ไม่มี ledger rows ถูกเขียน |
| SK-VAL-02 | เอกสาร source ย้อนหลัง | เอกสารลงวันที่ในงวดที่ปิดแล้ว | **ไม่มี error** — movement post เข้างวดที่เปิดอยู่ปัจจุบัน (`resolveCurrentPeriod`); period stamp ของ ledger row ต่างจากวันที่เอกสาร |
| SK-VAL-03 | Ref-type pill PC | เลือก pill **PC** | ไม่ return rows — `physical_count` ไม่ใช่ค่าใน `enum_inventory_doc_type` (frontend/backing-enum mismatch, quirk ที่ทราบ); การแก้ไขจาก count ปรากฏเป็น SI/SO |

## 4. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | -------- | -------- |
| SK-EDGE-01 | Row ของ transaction แบบหลายสินค้า | GRN เดียวมีหลาย lines | Cell ของ Product และ Location render รายชื่อแบบ comma-joined ที่ de-duplicate แล้ว; คอลัมน์ Items นับจำนวน detail rows |
| SK-EDGE-02 | Sort ข้ามตาราง | Sort ตาม document no / product / location | เป็น sort แบบ post-resolve: backend โหลด rows ที่ตรงทั้งหมด, resolve ชื่อ, sort ใน JS แล้วค่อย slice หน้า (path `POST_SORT` ใน `findAll`) — คาดผลลัพธ์เท่ากันแต่ latency ต่างจาก native sorts (date, type) |
| SK-EDGE-03 | Cost layers ที่ถูก split | Receipt ที่ `total_cost / qty` หารไม่ลงตัวที่ 2dp | `splitFifoCost` เขียนหลาย rows `lot_index` ภายใต้ `lot_no` เดียว เพื่อให้ต้นทุนของ layers reconcile ตรงกับยอดรวมของเอกสารพอดี |

## 5. แหล่งอ้างอิง

- User flow: [03-user-flow-store-keeper](/th/inventory/inventory/03-user-flow-store-keeper)
- Screen reference: [transaction](/th/inventory/inventory/transaction)
- Business rules: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_VAL_005`, `INV_VAL_008`, `INV_POST_001`–`INV_POST_003`
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/transaction/`; ตรรกะ list/search/sort ฝั่ง backend ใน `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (`findAll`)
- E2E: ยังไม่มี spec ที่ exercise หน้าจอนี้โดยตรง (manual/planned); ผลการ posting assert ผ่าน `501-grn.spec.ts` / `701-sr.spec.ts` / `601-cn.spec.ts`
