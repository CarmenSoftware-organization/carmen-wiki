---
title: แดชบอร์ด (Dashboard)
description: หน้าแดชบอร์ดข้ามโมดูล — หน้าแรกหลังเข้าระบบและมุมมอง KPI แยกตามโดเมน (PR, PO, GRN, คลังสินค้า, SR) ที่สรุปจำนวนสด, aging และรายการผิดปกติโดยไม่ต้องเปิดทีละโมดูล
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ด (Dashboard)

> **At a Glance**
> **Route:** `/dashboard` (server-redirects ไปยัง `/dashboard/main`) &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **ยังเป็น mock data ในปัจจุบัน**; live hook ถูกนิยามไว้แล้วแต่ยังไม่ถูก mount

![แดชบอร์ด (Dashboard) screen](/screenshots/dashboard/index.png)

## 1. คืออะไรและสำหรับใคร

โมดูลแดชบอร์ดคือหน้าจอแรกที่ผู้ปฏิบัติงานส่วนใหญ่เห็นหลังเข้าระบบ กลุ่มในแถบ sidebar เปิด 6 หน้าพี่น้อง — หนึ่งหน้าต่อโดเมนการทำงาน — แต่ละหน้าเป็นภาพรวมแบบ read-only ของ tile, ตาราง และกราฟ ที่ตอบคำถาม *"วันนี้มีอะไรต้องการความสนใจของฉันบ้าง?"* โดยไม่ต้องเปิดโมดูล transactional ที่อยู่ข้างใต้

**Production vs. mock แดชบอร์ด:** route `/dashboard` หลักโหลด **[widget-workspace](/th/inventory/dashboard/widget-workspace) แบบ live** — กริด widget ส่วนตัวแบบ drag-and-drop ที่ขับเคลื่อนด้วย API จริง หกหน้าย่อยแบบมีชื่อ (`/dashboard/pr`, `/dashboard/po` ฯลฯ) คือ **หน้า mock-data แยกตามโดเมน** ที่ยังคงอยู่สำหรับ developer reference และ QA testing แต่ไม่ใช่แดชบอร์ดหลักสำหรับผู้ปฏิบัติงาน

ข้อสังเกตด้านการออกแบบ 3 ข้อที่นักพัฒนาและทดสอบควรรู้:

- **หกหน้าแบบมีชื่อ** **ขับเคลื่อนด้วย mock data** ในปัจจุบันผ่าน `app/(root)/dashboard/mock/*.ts` Live count hooks (`useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`, `useApprovalPending`) มีอยู่แล้วแต่ **ยังไม่ถูก mount** บนหน้าเหล่านี้
- **widget-workspace** (`/dashboard`) และ section เพิ่มเติม **my-pending** และ **my-approval** เป็น **live** — hook mount แล้วและ endpoint เชื่อมต่อแล้ว
- แถบสีของ tile ถูก resolve ผ่านการ match prefix ที่ยาวที่สุดใน `constant/module-color-map.ts` (`--sub-pr`, `--sub-po`, `--sub-grn`, `--sub-store-requisition`, `--module-inventory`)

**กลุ่มผู้ใช้**

| Persona | เข้ามาที่ | เพราะอะไร |
|---|---|---|
| Requestor | [dashboard/sr](/th/inventory/dashboard/sr), [dashboard/pr](/th/inventory/dashboard/pr) | ใบขอของตัวเองที่ยัง pending และรายการที่ถูก send back |
| Approver (HOD, Procurement Manager) | [dashboard/pr](/th/inventory/dashboard/pr), [dashboard/po](/th/inventory/dashboard/po) | คิวอนุมัติ + คอขวดของ pipeline |
| Purchaser | [dashboard/po](/th/inventory/dashboard/po) | PO ที่เปิดอยู่, การส่งของล่าช้า, ผลงานของผู้ขาย |
| Receiver | [dashboard/grn](/th/inventory/dashboard/grn) | PO ที่รอรับวันนี้/สัปดาห์นี้, การรับของบางส่วน |
| Inventory Controller / Store Manager | [dashboard/inventory](/th/inventory/dashboard/inventory) | สต๊อกเคลื่อนไหวช้า, การเติมสต๊อก, สถานะ PST |
| Executive | [dashboard/main](/th/inventory/dashboard/main) | ค่าใช้จ่ายข้ามโดเมน, การใช้งบประมาณ, top vendor |

## 2. หน้าในโมดูลนี้

**แดชบอร์ด production จริง**

- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — route `/dashboard`; กริด widget ส่วนตัวแบบ drag-and-drop ที่ขับเคลื่อนด้วย dataset จริง; ผู้ใช้แต่ละคนสร้าง layout ของตัวเอง
- [dashboard/my-pending](/th/inventory/dashboard/my-pending) — widget นับ pending ส่วนตัว (PR / PO / SR) แสดงเอกสารที่รอการดำเนินการของผู้ใช้เอง
- [dashboard/my-approval](/th/inventory/dashboard/my-approval) — widget คิวงานอนุมัติส่วนตัว แสดงเอกสารที่รอการอนุมัติของผู้ใช้ จัดกลุ่มตามประเภท

**แดชบอร์ด mock แยกตามโดเมน (สำหรับ dev/QA reference)**

- [dashboard/main](/th/inventory/dashboard/main) — แดชบอร์ดแรกพร้อม KPI ข้ามโมดูล (ค่าใช้จ่าย, PR ค้าง, PO เปิด, งบประมาณ)
- [dashboard/pr](/th/inventory/dashboard/pr) — pipeline ของใบขอซื้อ, รายการที่ถูก send-back/reject, คิวอนุมัติ
- [dashboard/po](/th/inventory/dashboard/po) — pipeline ของใบสั่งซื้อ, การส่งของล่าช้า, มาตรวัด on-time / completeness
- [dashboard/grn](/th/inventory/dashboard/grn) — KPI ของใบรับสินค้า, PO ค้างตามช่วงวัน, GRN ไม่ครบ / รับเกิน
- [dashboard/inventory](/th/inventory/dashboard/inventory) — pipeline ของสต๊อก, สต๊อกเคลื่อนไหวช้า, การเติมสต๊อก, สถานะ PST, สินค้าหมดอายุ
- [dashboard/sr](/th/inventory/dashboard/sr) — pipeline ใบเบิกสโตร์, รายการ send-back, รออนุมัติ, กราฟการบริโภค

---

## 3. แหล่งข้อมูล (Dev)

เมื่อเปิดการเชื่อมต่อข้อมูลจริง แต่ละ tile จะ resolve ไปยังหนึ่งใน 3 backend surface นี้:

- **My-pending counts** — `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (ดู `constant/api-endpoints.ts`) คืนค่า `{ pending: number }` ต่อประเภทเอกสาร
- **Approval queue** — `GET /api/proxy/api/approval/pending` และ `/summary` คืนค่า `ApprovalItem[]` จัดกลุ่มตาม `doc_type` (`pr` / `po` / `sr`) พร้อม `workflow_current_stage`, `doc_date`, `total_amount`
- **Per-domain aggregates** — ตัวเลข pipeline / KPI (ปัจจุบันเป็น mock) จะ resolve ไปยังรายงาน query-dataset จาก [reporting-audit](/th/inventory/reporting-audit) ไม่ใช่การ scan ทีละ row ของตาราง transactional

ดูหน้าย่อยแต่ละหน้าสำหรับ tile-to-endpoint mapping

## 4. โมดูลที่เกี่ยวข้อง

- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory) — แหล่งข้อมูล transactional ที่อยู่เบื้องหลังทุก tile
- [reporting-audit](/th/inventory/reporting-audit) — query dataset สำหรับ KPI aggregate

## 5. แหล่งข้อมูลอ้างอิง

- `../carmen-inventory-frontend/app/(root)/dashboard/page.tsx` — `/dashboard` redirect ไปยัง `/dashboard/main`
- `../carmen-inventory-frontend/app/(root)/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx` — page shell แยกตามโดเมน
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-{main,pr,po,grn,inventory,sr}.tsx` — การวาง tile
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/{main,pr,po,grn,inventory,sr}.ts` — mock data ปัจจุบัน
- `../carmen-inventory-frontend/constant/module-list.ts` — การลงทะเบียน 6 หน้าย่อยใน sidebar
- `../carmen-inventory-frontend/constant/module-color-map.ts` — การกำหนดแถบสีต่อ route
- `../carmen-inventory-frontend/hooks/use-dashboard.ts`, `hooks/use-approval.ts` — hook นับสด + อนุมัติ (ยังไม่ wire)
