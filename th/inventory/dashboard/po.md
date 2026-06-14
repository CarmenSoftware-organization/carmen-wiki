---
title: แดชบอร์ดใบสั่งซื้อ (PO Dashboard)
description: tile สรุปใบสั่งซื้อ — pipeline หก stage, PR ค้างและการส่งของล่าช้า, มาตรวัด on-time / completeness, ค่าใช้จ่ายตามหมวด, top vendor และการ flag variance รับเกิน
published: true
date: 2026-05-19T23:55:00.000Z
tags: dashboard, purchase-order, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ดใบสั่งซื้อ (PO Dashboard)

> **At a Glance**
> **Route:** `/dashboard/po` &nbsp;·&nbsp; **สำหรับ:** Purchaser &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; Receiver &nbsp;·&nbsp; **สถานะ:** **ยังเป็น mock data ในปัจจุบัน**; การ wire จริงรอ

![แดชบอร์ดใบสั่งซื้อ (PO Dashboard) screen](/screenshots/dashboard/po.png)

## 1. คืออะไรและสำหรับใคร

ห้องนักบินของ Purchaser ตอบคำถาม *"PO ใดบ้างยังกำลังบินอยู่ ใดบ้างที่กำลังหลุด และฉันมีความเสี่ยงตรงไหน?"*

**Layout:** แถบ pipeline หก tile (ด้านบน) → ตาราง action Pending PRs / Overdue Deliveries (ซ้าย) + มาตรวัด KPI + การแสดงค่าใช้จ่าย (ขวา) → ตาราง Over-Received POs เต็มความกว้าง (ด้านล่าง)

มาตรวัดครึ่งวงกลม 2 อันเน้น 2 ตัวชี้วัดสำคัญในการจัดซื้อ: **% On-Time Delivery** และ **% Order Completeness**

**กลุ่มผู้ใช้**

- **Purchaser** — หลัก คัดกรอง Pending PRs (เพื่อออก PO ใหม่), ติดตาม Overdue Deliveries, เฝ้าดู On-Time %
- **Procurement Manager** — ใช้ Top Vendors และ Category Spend สำหรับ review สัดส่วน supplier; เฝ้าดู variance รับเกิน
- **Receiver** — มอง Delivery Schedule (วันนี้ / สัปดาห์นี้ / สัปดาห์หน้า) เพื่อเตรียมพนักงาน dock

## 2. Tile และการ Drill-down

| Tile | แสดงอะไร | Drill-down (เมื่อ live) |
|---|---|---|
| **PO Pipeline** | 6 stage: Not Sent / Sent / Partial / Closed / Completed / Rejected — จำนวน + progress bar | → [purchase-order](/th/inventory/purchase-order) กรองตาม status |
| **PR ค้างสำหรับการสร้าง PO** | PR ID, Requester, Dept, Date Approved, badge (`Pending PO` / `Hold for Info` / `Overdue Follow-up`) | → [purchase-request](/th/inventory/purchase-request) |
| **การส่งของล่าช้า** | PO ID, Vendor, Dept, Due Date, "ล่าช้า N วัน" (สี destructive) | → [purchase-order](/th/inventory/purchase-order) |
| **On-Time Delivery** | มาตรวัดครึ่งวงกลม, เปอร์เซ็นต์ (สี warning) | — |
| **Order Completeness** | มาตรวัดครึ่งวงกลม, เปอร์เซ็นต์ (สี success) | — |
| **ค่าใช้จ่ายตามหมวด (เดือนปัจจุบัน vs YTD)** | Donut + legend พร้อม 2 จำนวนต่อแถว | — |
| **5 ผู้ขายสูงสุดตามค่าใช้จ่าย** | bar แนวนอน + label จำนวน | → [vendor-pricelist](/th/inventory/vendor-pricelist) |
| **ตารางส่งของ** | 3 stat card: จำนวนวันนี้ / สัปดาห์นี้ / สัปดาห์หน้า | → [good-receive-note](/th/inventory/good-receive-note) expected วันนี้ |
| **PO ที่รับเกิน** | PO #, Material, Code, Vendor, Ordered, Received, Variance `+N`, badge "Variance Flagged" | → [good-receive-note](/th/inventory/good-receive-note) |

สกุลเงินแสดงเป็น `$` ใน mock — production ควร localise ไปยังสกุลเงินฐานของ BU

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไมมาตรวัดถึง static? | **ยังเป็น mock data** — On-Time / Completeness จะ resolve ไปยังรายงาน query dataset จาก [reporting-audit](/th/inventory/reporting-audit) |
| PR ใดบ้างขึ้นใน "Pending PRs for PO Creation"? | [purchase-request](/th/inventory/purchase-request) ที่ `workflow_current_stage = "approved"` AND `po_id IS NULL` เกณฑ์ SLA ขับเคลื่อนชนิด badge |
| อะไร flag PO เป็น "Overdue"? | `expected_delivery_date < CURRENT_DATE` AND ยังรับไม่ครบเทียบ [good-receive-note](/th/inventory/good-receive-note) |
| Over-Received variance reconcile ที่ไหน? | join PO line → committed GRN line ที่ `received_qty > ordered_qty`; ดู [costing](/th/inventory/costing) สำหรับการ post variance |
| ทำไมขึ้น `$` ไม่ใช่ `฿`? | Mock fixture quirk; production จะ localise ไปยังสกุลเงินฐานของ BU |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| มาตรวัดแสดง % เดียวกันทุก BU | Mock fixture seed `poKpi.onTimeDelivery` / `orderCompleteness` เดียวกันทุกที่ | ตรวจสอบ `mock/po.ts` — ค่า static |
| Delivery Schedule "วันนี้" ว่างทั้งที่มีของกำหนดส่งวันนี้ | mock ไม่มี filter ตามวันที่ปัจจุบัน | wire จริง filter `expected_delivery_date` กับ `CURRENT_DATE` |
| แถว Over-Received หายไปหลัง reload | mock array re-import ต่อ render — เสถียรในปัจจุบัน; ไม่เสถียรเมื่อ live | ตรวจสอบกับ commit log ของ [good-receive-note](/th/inventory/good-receive-note) เมื่อ wire แล้ว |
| Top Vendors bar แสดงชื่อ vendor ซ้ำ | Mock fixture quirk — `vendor_id` ไม่ถูก de-dup | live query group ตาม `vendor_id` และ join [vendor-pricelist](/th/inventory/vendor-pricelist) |

---

## 5. แหล่งข้อมูล (Dev)

- **Pipeline bucket** — group-count บน [purchase-order](/th/inventory/purchase-order) โดย `status` → 6 ค่า `PoPipelineKey`
- **Pending PR สำหรับ PO** — [purchase-request](/th/inventory/purchase-request) ที่ `workflow_current_stage = "approved"` AND `po_id IS NULL`; badge ตาม SLA (`Pending PO` < N วัน, `Overdue Follow-up` ≥ N วัน)
- **Overdue Deliveries** — [purchase-order](/th/inventory/purchase-order) line ที่ `expected_delivery_date < CURRENT_DATE` AND ยังรับไม่ครบเทียบ [good-receive-note](/th/inventory/good-receive-note)
- **On-Time Delivery / Order Completeness** — KPI ตามช่วงเวลาจาก [reporting-audit](/th/inventory/reporting-audit) บน GRN ที่ commit เทียบกับวัน/จำนวนคาดหวังของ PO
- **ค่าใช้จ่ายตามหมวด** — sum จำนวน PO line จัดกลุ่มตาม [product/category](/th/inventory/product/category) เดือนปัจจุบัน vs YTD
- **Top Vendors** — sum ยอดรวม PO จัดกลุ่มตาม `vendor_id` เลือก 5 อันดับแรก
- **Delivery Schedule** — count PO line ที่ `expected_delivery_date` ตกใน วันนี้ / สัปดาห์นี้ / สัปดาห์หน้า
- **Over-Received POs** — join [purchase-order](/th/inventory/purchase-order) line กับ [good-receive-note](/th/inventory/good-receive-note) line ที่ commit ซึ่ง `received_qty > ordered_qty`

## 6. จังหวะการ Refresh

mock แบบ static ในปัจจุบัน wire จริงรับ `CACHE_DYNAMIC` (1-min stale) จาก proxy hook Overdue Deliveries และ Over-Received เป็น time-sensitive — ทดสอบควรยืนยันการคำนวณซ้ำเมื่อ focus tab หลัง wire แล้ว

## 7. โมดูลที่เกี่ยวข้อง

- [purchase-order](/th/inventory/purchase-order) — ระบบบันทึก transactional
- [purchase-request](/th/inventory/purchase-request) — แหล่งต้นน้ำสำหรับ Pending PRs for PO Creation
- [good-receive-note](/th/inventory/good-receive-note) — การรับของปลายน้ำที่ขับ On-Time, Completeness, Over-Received
- [vendor-pricelist](/th/inventory/vendor-pricelist) — vendor master เบื้องหลัง Top Vendors bar
- [reporting-audit](/th/inventory/reporting-audit) — query dataset สำหรับมาตรวัด KPI
- [costing](/th/inventory/costing) — การจัดการ variance สำหรับจำนวนรับเกิน

## 8. แหล่งข้อมูลอ้างอิง

- **Page shell:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-po.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-po.tsx`
- **Mock data:** `../carmen-inventory-frontend-react/routes/dashboard/mock/po.ts`
- **i18n:** `messages/en.json` → `dashboard.po.title` = "Purchase Order Dashboard"
