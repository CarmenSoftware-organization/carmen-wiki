---
title: แดชบอร์ดคลังสินค้า (Inventory Dashboard)
description: ห้องนักบินของฝ่ายปฏิบัติการคลังสินค้า — pipeline สถานะ, ตารางสต๊อกเคลื่อนไหวช้า / เติมสต๊อก / PST กรองตาม location, มูลค่าตาม material group, การแจ้งเตือนของหมดอายุ และกราฟการบริโภคตาม location และหมวด
published: true
date: 2026-05-17T07:00:36.000Z
tags: dashboard, inventory, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ดคลังสินค้า (Inventory Dashboard)

> **At a Glance**
> **Route:** `/dashboard/inventory` &nbsp;·&nbsp; **สำหรับ:** Inventory Controller &nbsp;·&nbsp; Store Manager &nbsp;·&nbsp; Finance &nbsp;·&nbsp; QA &nbsp;·&nbsp; **สถานะ:** **ยังเป็น mock data ในปัจจุบัน**; การ wire จริงรอ

![แดชบอร์ดคลังสินค้า (Inventory Dashboard) screen](/screenshots/dashboard/inventory.png)

## 1. คืออะไรและสำหรับใคร

บอร์ดประจำวันของ Inventory Controller ตอบคำถาม *"สต๊อกล็อคที่ไหน, อะไรไม่เคลื่อนไหว, อะไรต้องสั่งเติม, และการบริโภคไหลที่ไหน?"*

**Layout:** pipeline สถานะ 5 ขั้น (ด้านบน) → คอลัมน์ซ้ายซ้อน 3 ตารางที่กรองตาม location (Slow-Moving / Replenishment / PST) → กริดขวาสำหรับ analytics (มูลค่าตาม Material Group / สินค้าหมดอายุ / การบริโภคตาม Location / การบริโภคตามหมวด)

2 ตารางเปิด Location tab picker (`Main Store`, `Bar`, `Restaurant` ฯลฯ — ดู `INVENTORY_LOCATIONS`) ให้ widget เดียวกัน retarget โดยไม่ navigate

**กลุ่มผู้ใช้**

- **Inventory Controller** — หลัก เฝ้าดู Slow-Moving / Dead Stock, Replenishment และ PST Status
- **Store Manager** — ใช้ Location tab picker สำหรับ scope ทุกตาราง; ใช้ "CREATE PR" ใน Replenishment
- **Finance Controller** — เฝ้าดู Inventory Value by Material Group เป็น exposure ทางการเงินของ on-hand
- **Compliance / QA** — เฝ้าดู Expired Items Alert

## 2. Tile และการ Drill-down

| Tile | แสดงอะไร | Drill-down (เมื่อ live) |
|---|---|---|
| **Pipeline สถานะ** | 5 การ์ด: Stock-Take Not Complete (จำนวน Loc) / Stock-Take Complete (จำนวน Loc) / Uncommitted Docs เดือนปัจจุบัน (จำนวน Doc) / Expiring Items เดือนปัจจุบัน (จำนวน Item) / มูลค่า Inventory (เดือนปัจจุบัน) | → [[physical-count]] / [[inventory]] |
| **Slow-Moving / Dead Stock** | Item, SKU, Location, Days No Movement, Est. Value (พร้อม Location tab) | → [[inventory]] item detail |
| **การเติมสต๊อก (ต่ำกว่า Par)** | Item, SKU, Location, On Hand, Par, Max, Order Qty + ปุ่ม "CREATE PR" 2 ปุ่ม (Location tab) | → [[purchase-request]] ใหม่ที่ pre-fill items |
| **สถานะ Physical Stock Take** | Location, Dept, Last Count Date, badge สถานะ PST (`Completed` / `Awaiting Approval` / `In Progress`), SVF Name | → [[physical-count]] |
| **มูลค่า Inventory ตาม Material Group** | Donut + bar + legend: Food / Beverage / Supplies พร้อม % + `$K` | — |
| **การแจ้งเตือนสินค้าหมดอายุ** | Item (XCircle), Expiry Date | → [[inventory]] lot/expiry |
| **การบริโภครวมตาม Location** | bar แนวนอนพร้อมจำนวนเดือนปัจจุบัน vs YTD | — |
| **การบริโภครวมตามหมวด** | bar แนวนอน + callout SR Awaiting Receipt ที่ list SR# พร้อมลิงก์ "Details" | → [[store-requisition]] สำหรับแถว SR# |

ตาราง Replenishment แสดง **ปุ่ม "CREATE PR" 2 ปุ่ม** ข้างกันด้วยสไตล์ต่างกัน — น่าจะเป็น placeholder สำหรับ template PR 2 แบบ (เช่น normal vs urgent) **(Inferred — ต้องยืนยันกับ UI จริง)**

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไม Location tab ไม่ filter ทุกตารางพร้อมกัน? | แต่ละตารางถือ Location state ของตัวเอง tab picker retarget เฉพาะ widget นั้น |
| เกณฑ์ของ "Slow-Moving" คืออะไร? | เกณฑ์ที่ปรับได้เทียบกับวันที่เคลื่อนไหวล่าสุด — ปัจจุบันเป็น mock; ยังไม่มี config กลาง |
| "Order Qty" ใน Replenishment คำนวณอย่างไร? | `max_level - on_hand` (หรือตามนโยบาย [[store-requisition/stock-replenishment]]) |
| "CREATE PR" สร้าง PR จริงหรือไม่? | **Inferred — ต้องยืนยันกับ UI จริง** Mock ไม่มี handler wire จริงควร pre-fill [[purchase-request]] ใหม่ด้วย line items |
| มูลค่า Inventory คำนวณอย่างไร? | `on_hand × unit_cost` จัดกลุ่มตาม root ของ [[product/category]]; `unit_cost` มาจาก [[costing]] |
| อะไรกระตุ้นการแจ้งเตือนสินค้าหมดอายุ? | ตาราง lot ของ [[inventory]] ที่ `expiry_date ≤ CURRENT_DATE + N_days` (N ปรับได้) |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| สลับ Location tab แสดง row เดิม | Mock fixture ไม่ได้ partition ตาม location | live query กรอง `location_id` |
| คลิก "CREATE PR" ไม่มีอะไรเกิดขึ้น | ยังไม่ wire handler ในบิลด์ปัจจุบัน | (Inferred — ต้องยืนยันกับ UI จริง) |
| badge PST Status หายไปสำหรับ count ที่มีจริง | mock มี row จำกัด; ข้อมูลจริงใช้ count ล่าสุดต่อ location | ตรวจสอบกับ header record ของ [[physical-count]] |
| รายการ Expired Items ว่างทั้งที่มีของหมดอายุ | Mock fixture seed row น้อย | live query อ่านตาราง lot ของ [[inventory]] พร้อม filter expiry |
| Inventory Value chart แสดง `$K` ไม่ใช่ `฿K` | Mock fixture currency quirk | production localise ไปยังสกุลเงินฐานของ BU |

---

## 5. แหล่งข้อมูล (Dev)

- **Pipeline สถานะ** — จำนวนจาก [[physical-count]] (location ที่ยังไม่ commit สำหรับงวด), aggregate ของ [[inventory]] (uncommitted docs เดือนนี้), ตาราง lot ของ [[inventory]] (ใกล้หมดอายุภายในเดือน), rollup มูลค่า inventory
- **Slow-Moving / Dead Stock** — ยอด item-location ของ [[inventory]] join กับวันที่เคลื่อนไหวล่าสุด; เกณฑ์ปรับได้
- **Replenishment** — item ที่ `on_hand < par_level`; order qty = `max_level - on_hand` (หรือตาม [[store-requisition/stock-replenishment]])
- **PST Status** — header record ของ [[physical-count]], count ล่าสุดต่อ location; workflow stage project ไปยัง 3 ชนิด badge
- **มูลค่า Inventory ตาม Material Group** — sum `on_hand × unit_cost` จัดกลุ่มตาม root ของ [[product/category]]
- **การแจ้งเตือนสินค้าหมดอายุ** — lot ของ [[inventory]] ที่ `expiry_date ≤ CURRENT_DATE + N_days`
- **การบริโภคตาม Location / หมวด** — sum การเคลื่อนไหวออกที่ commit ของ [[inventory]] (SR-issued, wastage, recipe) จัดกลุ่มตาม location / หมวด
- **SR Awaiting Receipt** — [[store-requisition]] ที่ `status = "issued"` AND location ปลายทางยังไม่ commit รับ

## 6. จังหวะการ Refresh

mock แบบ static ในปัจจุบัน เมื่อ wire แล้ว: Pipeline สถานะ และ rollup มูลค่า → `CACHE_NORMAL` (5-min) Replenishment และ PST Status → `CACHE_DYNAMIC` (1-min ผู้ปฏิบัติงาน act แบบ real-time) กราฟการบริโภค → `CACHE_NORMAL` (aggregate ข้ามเดือน / YTD)

## 7. โมดูลที่เกี่ยวข้อง

- [[inventory]] — ยอดและการเคลื่อนไหว transactional เบื้องหลังทุก tile
- [[inventory-adjustment]] — การ post variance หลัง PST
- [[physical-count]], [[spot-check]] — การ count operation ที่ขับ PST Status
- [[store-requisition]] — การออกของที่ป้อน Consumption + SR Awaiting Receipt
- [[purchase-request]] — เป้าหมายของปุ่ม "CREATE PR" replenishment
- [[costing]] — แหล่ง `unit_cost` สำหรับ donut มูลค่า inventory

## 8. แหล่งข้อมูลอ้างอิง

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/inventory/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-inventory.tsx`
- **Mock data:** `../carmen-inventory-frontend/app/(root)/dashboard/mock/inventory.ts` (รวม `INVENTORY_LOCATIONS`)
- **i18n:** `messages/en.json` → `dashboard.inventory.title` = "Inventory Dashboard"
