---
title: แดชบอร์ดใบรับสินค้า (GRN Dashboard)
description: KPI ของใบรับสินค้า — จำนวน receiving-now / received-today / MTD / YTD, PO ค้างตามช่วงวันแบบ tab, PO ล่าช้าพร้อมไฮไลต์วิกฤต, ตาราง GRN ไม่ครบและรับเกิน รวมถึง top vendor และค่าใช้จ่ายตามหมวด
published: true
date: 2026-05-19T23:55:00.000Z
tags: dashboard, good-receive-note, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ดใบรับสินค้า (GRN Dashboard)

> **At a Glance**
> **Route:** `/dashboard/grn` &nbsp;·&nbsp; **สำหรับ:** Receiver &nbsp;·&nbsp; Inventory Controller &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; **สถานะ:** **ยังเป็น mock data ในปัจจุบัน**; การ wire จริงรอ

![แดชบอร์ดใบรับสินค้า (GRN Dashboard) screen](/screenshots/dashboard/grn.png)

## 1. คืออะไรและสำหรับใคร

บอร์ดปฏิบัติการของ Receiver ตอบคำถาม *"วันนี้มีอะไรเข้า dock บ้าง, อะไรที่ช้า, และการรับของไม่ตรงกับใบสั่งซื้อตรงไหน?"*

**Layout:** การ์ด KPI 4 ใบ (ด้านบน: Receiving Now / Received Today / MTD / YTD) → กริด 2×2 ของตาราง (PO ค้างตามช่วงวัน, PO ล่าช้า, GRN ไม่ครบ, GRN รับเกิน) → กราฟค่าใช้จ่าย YTD 2 อัน (ด้านล่าง)

บล็อก Pending PO เป็น interactive — แถบ tab 3 ปุ่ม (TODAY / THIS WEEK / NEXT WEEK) สลับตารางฝั่ง client โดยไม่ navigate

**กลุ่มผู้ใช้**

- **Receiver / Dock Operator** — หลัก เฝ้าดู tab Pending PO เพื่อเตรียมตัวประจำวัน, Overdue PO เพื่อ escalate, Receiving Now เพื่อรู้ว่าใครอยู่ที่ dock
- **Inventory Controller** — ใช้ตาราง Incomplete และ Over-Received สำหรับสืบสวน variance ก่อน commit
- **Procurement Manager** — review Top Vendors YTD และ Spend by Category สำหรับ supplier performance

## 2. Tile และการ Drill-down

| Tile | แสดงอะไร | Drill-down (เมื่อ live) |
|---|---|---|
| **Receiving Now** | จำนวน, ไอคอนลูกศร (สี primary) | → [good-receive-note](/th/inventory/good-receive-note) in-progress |
| **Received Today** | จำนวน, ไอคอน check (สี success) | → [good-receive-note](/th/inventory/good-receive-note) วันนี้ |
| **GRN รวม (MTD)** | จำนวน, ไอคอนปฏิทิน | → [good-receive-note](/th/inventory/good-receive-note) month-to-date |
| **GRN รวม (YTD)** | ตัวเลข format, ไอคอนกล่อง | → [good-receive-note](/th/inventory/good-receive-note) year-to-date |
| **ใบสั่งซื้อค้าง** | tab วันนี้ / สัปดาห์นี้ / สัปดาห์หน้า — PO, Supplier, Expected Date, Items, Total, Priority (`High` / `Medium` / `Low`) | → [purchase-order](/th/inventory/purchase-order) |
| **ใบสั่งซื้อล่าช้า** | PO, Supplier, Original Due Date, Days Overdue (badge แดง `OVERDUE` ถ้า ≥ 10 วัน), Items | → [purchase-order](/th/inventory/purchase-order) |
| **GRN ไม่ครบ (รับบางส่วน)** | GRN, PO, Supplier, Qty Ordered, Qty Received, Variance %, badge "Partially Received" | → [good-receive-note](/th/inventory/good-receive-note) |
| **GRN รับเกิน** | GRN (AlertTriangle), PO, Supplier, PO Amount, GRN Amount, Excess, Variance % | → [good-receive-note](/th/inventory/good-receive-note) |
| **5 ผู้ขายสูงสุดตามยอดซื้อ YTD** | bar แนวนอนพร้อม label มูลค่า `$NM` | → [vendor-pricelist](/th/inventory/vendor-pricelist) |
| **ค่าใช้จ่ายในการซื้อตามหมวด** | bar แนวตั้งจัดกลุ่ม: เดือนปัจจุบัน vs YTD ต่อหมวด | — |

เกณฑ์ 10 วัน (`OVERDUE_THRESHOLD`) ถูก hard-code ใน `dashboard-grn.tsx` — production ควรดึงจากการตั้งค่า SLA ที่ปรับได้

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไม "Received Today" ไม่เพิ่มขึ้นหลัง commit GRN? | **ยังเป็น mock data** — ตัวเลขมาจาก `mock/grn.ts` wire จริงใช้ `CACHE_DYNAMIC` (1-min stale) พร้อม refetch-on-focus |
| อะไรจัด PO เป็น "Overdue" vs "Critical OVERDUE"? | Overdue = `expected_delivery_date < CURRENT_DATE` AND ยังรับไม่ครบ Critical badge เด้งเมื่อ days-overdue ≥ `OVERDUE_THRESHOLD = 10` (ปัจจุบัน hard-code) |
| Variance % คำนวณอย่างไรสำหรับรับบางส่วน / รับเกิน? | Frontend คำนวณจาก `received_qty` vs `ordered_qty` ของแต่ละแถว join กลับไป [purchase-order](/th/inventory/purchase-order) line |
| tab ช่วงวัน (วันนี้ / สัปดาห์นี้ / สัปดาห์หน้า) ดึงรายการจากไหน? | [purchase-order](/th/inventory/purchase-order) line จัดกลุ่มตาม bucket ของ `expected_delivery_date` ที่ยังไม่มี [good-receive-note](/th/inventory/good-receive-note) line ถูก commit |
| ทำไม YTD total แสดงเป็น USD ล้าน? | Mock fixture ใช้ `$M`; production localise ไปยังสกุลเงินฐานของ BU จาก [master-data/exchange-rate](/th/inventory/master-data/exchange-rate) |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| badge Receiving Now ค้างเลขเดิมทั้งวัน | mock ไม่มี real-time tick | wire จริงควร refetch on focus และ on commit-event hook |
| เกณฑ์ Overdue ไม่ตรงกับนโยบาย SLA | `OVERDUE_THRESHOLD = 10` hard-code ใน component | เปิด ticket enhancement ดึงจาก config [system-config/workflow](/th/inventory/system-config/workflow) |
| GRN ไม่ครบ vs รับเกิน แสดงแถวเดียวกัน | Mock fixture seed ไม่ consistent | live query เป็น mutually exclusive: `received_qty < ordered_qty` vs `received_qty > ordered_qty` |
| สลับ tab (วันนี้/สัปดาห์นี้/สัปดาห์หน้า) ไม่เปลี่ยนข้อมูล | array mock ต่างกัน แต่ state binding อาจ regress | ตรวจสอบ `pendingPoToday` / `pendingPoThisWeek` / `pendingPoNextWeek` |

---

## 5. แหล่งข้อมูล (Dev)

- **การ์ด KPI** — count query บน [good-receive-note](/th/inventory/good-receive-note) กรองตาม `status` (`in progress` สำหรับ Receiving Now, `commit_date = today` สำหรับ Received Today ฯลฯ)
- **tab Pending PO** — [purchase-order](/th/inventory/purchase-order) line จัดกลุ่มตาม bucket ของ `expected_delivery_date` ที่ยังไม่มี [good-receive-note](/th/inventory/good-receive-note) line ถูก commit
- **Overdue PO** — [purchase-order](/th/inventory/purchase-order) ที่ `expected_delivery_date < CURRENT_DATE` AND ยังรับไม่ครบ; days overdue = `CURRENT_DATE - expected_delivery_date`
- **GRN ไม่ครบ / รับเกิน** — join [good-receive-note](/th/inventory/good-receive-note) line ที่ commit กับ PO line; ไม่ครบ `received_qty < ordered_qty`, เกิน `received_qty > ordered_qty`; Variance % คำนวณ frontend
- **Top Vendors YTD** — sum จำนวน GRN line จัดกลุ่มตาม `vendor_id` เลือก 5 อันดับแรก
- **ค่าใช้จ่ายตามหมวด** — sum จำนวน GRN line จัดกลุ่มตาม [product/category](/th/inventory/product/category) แยกเดือนปัจจุบัน vs YTD

## 6. จังหวะการ Refresh

mock แบบ static ในปัจจุบัน เมื่อ wire แล้ว: การ์ด KPI และ Receiving Now ควร refetch บ่อย (กิจกรรม dock เป็น real-time-ish) — `CACHE_DYNAMIC` (1-min stale) เป็นอย่างน้อย Top Vendors YTD ใช้ `CACHE_NORMAL` (5-min) ได้ เพราะ YTD total เปลี่ยนช้า

## 7. โมดูลที่เกี่ยวข้อง

- [good-receive-note](/th/inventory/good-receive-note) — ระบบบันทึก transactional
- [purchase-order](/th/inventory/purchase-order) — การผูกพันต้นน้ำเบื้องหลังทุกแถว pending / overdue
- [inventory](/th/inventory/inventory) — ผลกระทบ stock ปลายน้ำเมื่อ GRN commit
- [vendor-pricelist](/th/inventory/vendor-pricelist) — vendor master สำหรับกราฟ Top Vendors
- [costing](/th/inventory/costing) — การจัดการ variance สำหรับจำนวนรับเกินตอน commit-time costing

## 8. แหล่งข้อมูลอ้างอิง

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/grn/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-grn.tsx`
- **Mock data:** `../carmen-inventory-frontend/app/(root)/dashboard/mock/grn.ts`
- **i18n:** `messages/en.json` → `dashboard.grn.title` = "Goods Receive Note Dashboard"
