---
title: แดชบอร์ดหลัก (Main Dashboard)
description: หน้าแดชบอร์ดแรกที่แสดง KPI ระดับบนของ PR, PO, GRN, คลังสินค้า และ SR — หน้าเดียวที่แสดงทันทีหลังเข้าระบบ
published: true
date: 2026-05-19T23:55:00.000Z
tags: dashboard, landing, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ดหลัก (Main Dashboard)

> **At a Glance**
> **Route:** `/dashboard/main` (เข้าจาก `/dashboard` ผ่าน redirect ก็ได้) &nbsp;·&nbsp; **สำหรับ:** Executive / Controller / HOD หลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** Mock data ในปัจจุบัน; การเชื่อมต่อข้อมูลจริงรอ wire

![แดชบอร์ดหลัก (Main Dashboard) screen](/screenshots/dashboard/main.png)

## 1. คืออะไรและสำหรับใคร

หน้าหลังเข้าระบบ ตอบคำถาม *"สาย procure-to-pay ทั้งสายเดือนนี้เป็นอย่างไร?"* — เพจเดียวที่แสดง KPI ข้ามโดเมน เหมาะกับคนที่ต้องการภาพรวมก่อนเจาะลงไปที่โมดูลใดโมดูลหนึ่ง

**Layout:** การ์ด KPI 4 ใบ (ด้านบน) → กราฟ 2 อัน (กลาง: donut + bar) → บล็อกวิเคราะห์ 2 บล็อก (คอขวด PR pipeline + top vendor)

**กลุ่มผู้ใช้**

- **Executive / GM** — การ์ด KPI 4 ใบ + กราฟแท่งค่าใช้จ่ายตามแผนก
- **Procurement Manager** — คอขวด PR Pipeline + Top Vendors
- **Finance Controller** — Budget Utilisation + donut สัดส่วนค่าใช้จ่าย

## 2. Tile และการ Drill-down

| Tile | แสดงอะไร | Drill-down (เมื่อ live) |
|---|---|---|
| **ค่าใช้จ่ายรวมเดือนนี้ (Total Spend This Month)** | จำนวน `฿`, ↑/↓ เทียบเดือนก่อน, % เปลี่ยนแปลง | (Inferred — ต้องยืนยัน) |
| **จำนวน PR ค้าง (Pending PRs Count)** | จำนวน + "HOD Approved, Awaiting Purchase" | → [purchase-request](/th/inventory/purchase-request) |
| **จำนวน PO เปิด (Open POs Count)** | จำนวน + "Waiting for Delivery" | → [purchase-order](/th/inventory/purchase-order) |
| **ค่าใช้จ่ายจริงเทียบงบประมาณ (Actual Spend vs Budget)** | progress bar 0–100% | (Inferred) |
| **ค่าใช้จ่ายตาม Material Group** | Donut: Food / Beverage / Supplies / Chemicals / Others | — |
| **ค่าใช้จ่ายตามแผนก** | Bar: 5 แผนก, จำนวน `฿` | — |
| **PR Pipeline — คอขวด** | 6 stage (Saved / Committed / Awaiting HOD / Awaiting Purchase / Approved / Rejected) พร้อมจำนวน, `฿`, badge คอขวด | → [purchase-request](/th/inventory/purchase-request) |
| **5 ผู้ขายสูงสุดตามค่าใช้จ่าย** | Vendor, ค่าใช้จ่ายรวม, จำนวน PO, จำนวนวันส่งของเฉลี่ย | → [vendor-pricelist](/th/inventory/vendor-pricelist) |

สกุลเงินถูกฟอร์แมตผ่าน `formatCurrency` → `฿` + การจัดกลุ่ม locale ไทย (`th-TH`)

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไม tile ของฉันไม่ refresh? | ทุก tile **เป็น mock data ในปัจจุบัน** Live hook มีอยู่แต่ยังไม่ถูก mount |
| ตัวเลข PR Pipeline มาจากไหน? | จะเป็นการ group-count บน [purchase-request](/th/inventory/purchase-request) โดย `workflow_current_stage` เมื่อ wire แล้ว |
| Live data path อยู่ที่ไหน? | `hooks/use-dashboard.ts` (`useMyPendingPrCount` / `useMyPendingPoCount` / `useMyPendingSrCount`) และ `hooks/use-approval.ts` (`useApprovalPending`) — wire ไปยัง `/api/proxy/api/my-pending/*` และ `/api/proxy/api/approval/pending` แต่ **ยังไม่ถูก mount** บนหน้านี้ |
| badge "Bottleneck" สีส้มหมายความว่าอะไร? | stage หนึ่งถือมูลค่า `฿` มากกว่าสัดส่วนที่คาดหวัง — flag ใน `mock/main.ts` ผ่าน `isBottleneck` ของแต่ละ stage |
| Tile งบประมาณควรสะท้อนแค่เดือนนี้หรือ YTD? | ปัจจุบัน `mock/main.ts` แสดง % เฉพาะเดือน — โหมด production จะดึงจาก query dataset ของ [reporting-audit](/th/inventory/reporting-audit) |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Tile กดไม่ได้ / drill ไม่ไปไหน | drill-down route ยังไม่ wire ในบิลด์ปัจจุบัน | (Inferred — ต้องยืนยันกับ UI จริง) |
| ตัวเลขไม่ตรงกับ sub-dashboard ของ PR/PO | แต่ละแดชบอร์ดอ่าน mock อิสระของตัวเองในปัจจุบัน | จะถูกแก้เมื่อทุก tile อ่าน endpoint จริง |
| สกุลเงินขึ้นเป็น `$` แทน `฿` บางหน้า | Mock fixture quirk บน mock ของ PR / PO / Inventory | wire production ควร localise ไปยังสกุลเงินฐานของ BU จาก [master-data/exchange-rate](/th/inventory/master-data/exchange-rate) |
| Tile แสดงศูนย์หรือว่างเปล่า | Mock fixture seed ค่านี้ไว้โดยตั้งใจ | ตรวจสอบ `app/(root)/dashboard/mock/main.ts` เพื่อยืนยัน |

---

## 5. แหล่งข้อมูล (Dev)

เมื่อมีการ wire ข้อมูลจริง การ mapping ที่คาดหวัง:

- **การ์ด KPI** — query aggregate กับ [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), ตาราง ledger รวมถึงรายงาน budget-vs-actual จาก [reporting-audit](/th/inventory/reporting-audit)
- **ค่าใช้จ่ายตาม Material Group / แผนก** — sum แบบจัดกลุ่มบน PO/GRN line ที่ join กับ product-category และ [master-data/department](/th/inventory/master-data/department)
- **PR Pipeline** — group-count บน [purchase-request](/th/inventory/purchase-request) โดย `workflow_current_stage`
- **Top Vendors** — sum จำนวนรวม PO จัดกลุ่มตาม `vendor_id`, join กับ [vendor-pricelist](/th/inventory/vendor-pricelist)

**จังหวะการ refresh:** mock แบบ static ในปัจจุบัน เมื่อมี hook จริง: `CACHE_DYNAMIC` (1-min stale, 5-min gc), refetch on focus, ไม่ poll

## 6. โมดูลที่เกี่ยวข้อง

- [dashboard](/th/inventory/dashboard) — สารบัญโมดูล + หน้าย่อยพี่น้อง
- [dashboard/pr](/th/inventory/dashboard/pr), [dashboard/po](/th/inventory/dashboard/po) — ปลายทาง drill ของบล็อก PR Pipeline และ Open POs / Top Vendors
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note) — แหล่ง transactional ที่อยู่เบื้องหลังทุก aggregate ค่าใช้จ่าย
- [reporting-audit](/th/inventory/reporting-audit) — query dataset ที่จะรองรับ tile spend-by-group และ budget

## 7. แหล่งข้อมูลอ้างอิง

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/main/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-main.tsx`
- **Mock data:** `../carmen-inventory-frontend/app/(root)/dashboard/mock/main.ts`
- **i18n:** `messages/en.json` → `dashboard.main.title` = "Dashboard"
