---
title: คลังสินค้า (Inventory) — User Flow — Store Keeper
description: Flow ของ Store Keeper ในโมดูล inventory — อ่าน transaction ledger เพื่อตรวจสอบว่าการ post จากเอกสาร source ลงอย่างถูกต้อง
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory, user-flow, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **Surface ในโมดูลนี้:** Transaction Log แบบ **read-only** (`/inventory-management/transaction`, `inventory_management.view`) — ตรวจสอบว่าการ post จาก GRN / SR / adjustment ลงแล้ว &nbsp;·&nbsp; **ไม่อยู่ในโมดูลนี้:** การ author adjustment (อยู่ใน [inventory-adjustment](/th/inventory/inventory-adjustment)) และการนับ (อยู่ใน [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check))
> **การแก้ไข (2026-07-15):** flow การ author stock-in/stock-out พร้อม auto-approve ตาม threshold และการ route ไปยัง Controller ที่เคยบันทึกไว้ที่นี่ **ไม่มี source รองรับ** — ไม่มี threshold อยู่ที่ใดใน backend และหน้าจอ adjustment เป็นของโมดูล inventory-adjustment ไม่ใช่ของโมดูลนี้

## 1. บทบาทในโมดูลนี้

Persona **Store Keeper** คือผู้ปฏิบัติงานที่ระดับ floor / location ภายในโมดูล wiki *inventory* (transaction ledger + period-end) surface ของพวกเขาเป็น **read-only**: หลังจาก GRN save, การ issue ของ SR หรือการ complete ของ inventory-adjustment, Store Keeper เปิด Transaction Log เพื่อยืนยันว่า movement ลงแล้ว — สินค้า, location, ทิศทางของจำนวน และต้นทุนถูกต้อง ทุกอย่างที่พวกเขา *author* อยู่ในโมดูลพี่น้อง:

- เอกสาร manual stock-in / stock-out → [inventory-adjustment](/th/inventory/inventory-adjustment) (`/inventory-management/inventory-adjustment`, สิทธิ์ nav `inventory_management.view`) Flow เอกสารที่นั่นคือ **Save = draft, Commit = posted** (`PATCH …/commit`, ตั้งแต่ 2026-07-30) — การ commit post inventory transaction แบบ atomic; แก้ไขได้เฉพาะที่ `draft`; **Void** กลับรายการเอกสารที่ post แล้ว
- Physical count และ spot check → [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check)
- การรับสินค้าที่ dock → [good-receive-note](/th/inventory/good-receive-note) (หมายเหตุ: บน business unit แบบ average ledger rows ปรากฏตอน GRN **save**; บน business unit แบบ FIFO ปรากฏตอน **commit** — `postsInventoryAtSave`)

โค้ดของโมดูลนี้ไม่มี scope การ post ต่อ location, threshold หรือ approval routing ใด ๆ; การเข้าถึง ledger ถูก gate ด้วยสิทธิ์เดียวคือ `inventory_management.view`

## 2. จุดเข้าและ Flow หลัก

**จุดเข้า:** Inventory Management → Transaction (`/inventory-management/transaction`)

**Flow หลัก (ตรวจสอบการ post, 5 ขั้นตอน):**

1. **เปิด Transaction Log** รายการ render หนึ่งแถวต่อ transaction พร้อม: วันที่, badge ประเภท (GRN / SR / SI / SO / CN), `parent_document_no`, ชื่อสินค้า, location, Qty In, Qty Out, จำนวน item และต้นทุนรวม การ์ดสรุปสี่ใบอยู่เหนือ grid: จำนวน transaction ทั้งหมด (พร้อมจำนวน adjustment), inbound รวม (หน่วย + ต้นทุน), outbound รวม และ net change แบบมีเครื่องหมาย
2. **Filter ไปยัง movement ที่คาดหวัง** ค้นหาด้วยเลขเอกสาร / สินค้า / ชื่อ location หรือใช้ filter: preset ช่วงวันที่ (Today / 7d / 30d / This month / custom picker), ทิศทาง Inbound–Outbound, Location lookup, Category lookup และ pill ref-type (GRN / SR / SI / SO / PC)
3. **หาแถว** ที่ `parent_document_no` ตรงกับเอกสาร source ที่เพิ่ง post ไป
4. **ตรวจทิศทางและจำนวน** Qty In สีเขียว, Qty Out สีแดง; GRN receipt แบบ direct-location แสดงทั้งสองขา (receipt และ issue หักล้างอัตโนมัติ) ภายใต้ transaction เดียวกัน
5. **Escalate ความไม่ตรงกันผ่านเอกสาร source** Ledger ไม่มีปุ่มแก้ไข — การ post ที่ผิดถูกแก้ด้วย credit note (ต้นทางจาก GRN) หรือ stock-in / stock-out ใน [inventory-adjustment](/th/inventory/inventory-adjustment) ไม่ใช่โดยการแก้ row

## 3. กิ่งการตัดสินใจ

- **แถวหายหลัง action ของ GRN** — ตรวจวิธีคิดต้นทุนของ BU และ action ที่ถูกรัน: BU แบบ average post ตอน **save** (`draft → saved`) และ post ซ้ำเมื่อแก้จำนวน; BU แบบ FIFO post เฉพาะตอน **commit** ไม่ว่ากรณีใด GRN ที่ยังเป็น `draft` ไม่มีตัวตนบน ledger
- **Movement ปรากฏใน "เดือนที่ผิด"** — ตั้งแต่ 2026-08-31 period stamp ตามวันที่เอกสาร (`findOpenPeriodForDate`); stock-in ที่ลงวันที่ในงวดที่ปิดแล้วถูก reject (`The stock-in date does not fall inside any open period`, 422) และ stock-out ต้องลงวันที่ในงวดปัจจุบัน (`Stock-outs can only be dated inside the current period (…)`, 422) เฉพาะ movement ที่ไม่มีวันที่เอกสาร (void reversal, credit note) เท่านั้นที่ fallback ไปงวด open ปัจจุบัน
- **Pill PC ไม่คืนอะไรเลย** — ค่า ref-type `physical_count` ไม่มีสมาชิก `enum_inventory_doc_type` ที่ตรงกัน; การแก้ไขจากการนับมาถึงเป็นเอกสาร SI / SO
- **Error insufficient-stock บนเอกสารขาออก** — การ **Commit** stock-out ตรวจล่วงหน้าทุกบรรทัดและคืน `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`, 400); SR issue ที่ผ่านการตรวจของตัวเองมาได้จะเจอ `Insufficient stock. Requested: <X>, Available: <Y>` ของ ledger; Store Keeper ลดจำนวนหรือสืบสวน balance ใน ledger (หรือ dialog stock panel ของสินค้าบนบรรทัดเอกสาร)

## 4. จุดออก / การส่งต่อ

- **การตรวจสอบสะอาด** — ไม่มี action ต่อ; ledger row เป็น immutable และถาวร
- **พบความไม่ตรงกัน** — ส่งต่อให้โมดูล source เจ้าของ (credit note ของ GRN, การแก้ไขใน inventory-adjustment); การแก้ไข post transaction ใหม่ของตัวเอง และคู่ของ rows คือ audit trail

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow](/th/inventory/inventory/03-user-flow)
- Sibling: [transaction](/th/inventory/inventory/transaction) — data-model และ event matrix ฉบับเต็มของหน้าจอที่ flow นี้ใช้
- Sibling: [02-business-rules](/th/inventory/inventory/02-business-rules) — `INV_VAL_005` (insufficient stock), `INV_VAL_008` (การ stamp งวด), `INV_POST_001`–`INV_POST_003` (แต่ละการ post เขียนอะไรบ้าง)
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/transaction/` (`transaction-component.tsx`, `use-transaction-table.tsx`, `transaction-summary.tsx`)
- ที่เกี่ยวข้อง: [inventory-adjustment](/th/inventory/inventory-adjustment), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check)
