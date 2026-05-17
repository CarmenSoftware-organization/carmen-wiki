---
title: แดชบอร์ด (Dashboard)
description: หน้าแดชบอร์ดข้ามโมดูล — หน้าแรกหลังเข้าระบบและมุมมอง KPI แยกตามโดเมน (PR, PO, GRN, คลังสินค้า, SR) ที่สรุปจำนวนสด, aging และรายการผิดปกติโดยไม่ต้องเปิดทีละโมดูล
published: true
date: 2026-05-17T07:28:28.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ด (Dashboard)

> **At a Glance**
> **Route:** `/dashboard` (server-redirects ไปยัง `/dashboard/main`) &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **ยังเป็น mock data ในปัจจุบัน**; live hook ถูกนิยามไว้แล้วแต่ยังไม่ถูก mount

![แดชบอร์ด (Dashboard) screen](/assets/screenshots/dashboard/index.png)

## 1. คืออะไรและสำหรับใคร

โมดูลแดชบอร์ดคือหน้าจอแรกที่ผู้ปฏิบัติงานส่วนใหญ่เห็นหลังเข้าระบบ กลุ่มในแถบ sidebar เปิด 6 หน้าพี่น้อง — หนึ่งหน้าต่อโดเมนการทำงาน — แต่ละหน้าเป็นภาพรวมแบบ read-only ของ tile, ตาราง และกราฟ ที่ตอบคำถาม *"วันนี้มีอะไรต้องการความสนใจของฉันบ้าง?"* โดยไม่ต้องเปิดโมดูล transactional ที่อยู่ข้างใต้

ข้อสังเกตด้านการออกแบบ 2 ข้อที่นักพัฒนาและทดสอบควรรู้:

- ทั้ง 6 หน้า **ขับเคลื่อนด้วย mock data** ในปัจจุบันผ่าน `app/(root)/dashboard/mock/*.ts` Live count hooks (`useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`, `useApprovalPending`) มีอยู่แล้วแต่ **ยังไม่ถูก mount**
- แถบสีของ tile ถูก resolve ผ่านการ match prefix ที่ยาวที่สุดใน `constant/module-color-map.ts` (`--sub-pr`, `--sub-po`, `--sub-grn`, `--sub-store-requisition`, `--module-inventory`)

**กลุ่มผู้ใช้**

| Persona | เข้ามาที่ | เพราะอะไร |
|---|---|---|
| Requestor | [[dashboard/sr]], [[dashboard/pr]] | ใบขอของตัวเองที่ยัง pending และรายการที่ถูก send back |
| Approver (HOD, Procurement Manager) | [[dashboard/pr]], [[dashboard/po]] | คิวอนุมัติ + คอขวดของ pipeline |
| Purchaser | [[dashboard/po]] | PO ที่เปิดอยู่, การส่งของล่าช้า, ผลงานของผู้ขาย |
| Receiver | [[dashboard/grn]] | PO ที่รอรับวันนี้/สัปดาห์นี้, การรับของบางส่วน |
| Inventory Controller / Store Manager | [[dashboard/inventory]] | สต๊อกเคลื่อนไหวช้า, การเติมสต๊อก, สถานะ PST |
| Executive | [[dashboard/main]] | ค่าใช้จ่ายข้ามโดเมน, การใช้งบประมาณ, top vendor |

## 2. หน้าในโมดูลนี้

- [[dashboard/main]] — แดชบอร์ดแรกพร้อม KPI ข้ามโมดูล (ค่าใช้จ่าย, PR ค้าง, PO เปิด, งบประมาณ)
- [[dashboard/pr]] — pipeline ของใบขอซื้อ, รายการที่ถูก send-back/reject, คิวอนุมัติ
- [[dashboard/po]] — pipeline ของใบสั่งซื้อ, การส่งของล่าช้า, มาตรวัด on-time / completeness
- [[dashboard/grn]] — KPI ของใบรับสินค้า, PO ค้างตามช่วงวัน, GRN ไม่ครบ / รับเกิน
- [[dashboard/inventory]] — pipeline ของสต๊อก, สต๊อกเคลื่อนไหวช้า, การเติมสต๊อก, สถานะ PST, สินค้าหมดอายุ
- [[dashboard/sr]] — pipeline ใบเบิกสโตร์, รายการ send-back, รออนุมัติ, กราฟการบริโภค

---

## 3. แหล่งข้อมูล (Dev)

เมื่อเปิดการเชื่อมต่อข้อมูลจริง แต่ละ tile จะ resolve ไปยังหนึ่งใน 3 backend surface นี้:

- **My-pending counts** — `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (ดู `constant/api-endpoints.ts`) คืนค่า `{ pending: number }` ต่อประเภทเอกสาร
- **Approval queue** — `GET /api/proxy/api/approval/pending` และ `/summary` คืนค่า `ApprovalItem[]` จัดกลุ่มตาม `doc_type` (`pr` / `po` / `sr`) พร้อม `workflow_current_stage`, `doc_date`, `total_amount`
- **Per-domain aggregates** — ตัวเลข pipeline / KPI (ปัจจุบันเป็น mock) จะ resolve ไปยังรายงาน query-dataset จาก [[reporting-audit]] ไม่ใช่การ scan ทีละ row ของตาราง transactional

ดูหน้าย่อยแต่ละหน้าสำหรับ tile-to-endpoint mapping

## 4. โมดูลที่เกี่ยวข้อง

- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]] — แหล่งข้อมูล transactional ที่อยู่เบื้องหลังทุก tile
- [[reporting-audit]] — query dataset สำหรับ KPI aggregate

## 5. แหล่งข้อมูลอ้างอิง

- `../carmen-inventory-frontend/app/(root)/dashboard/page.tsx` — `/dashboard` redirect ไปยัง `/dashboard/main`
- `../carmen-inventory-frontend/app/(root)/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx` — page shell แยกตามโดเมน
- `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-{main,pr,po,grn,inventory,sr}.tsx` — การวาง tile
- `../carmen-inventory-frontend/app/(root)/dashboard/mock/{main,pr,po,grn,inventory,sr}.ts` — mock data ปัจจุบัน
- `../carmen-inventory-frontend/constant/module-list.ts` — การลงทะเบียน 6 หน้าย่อยใน sidebar
- `../carmen-inventory-frontend/constant/module-color-map.ts` — การกำหนดแถบสีต่อ route
- `../carmen-inventory-frontend/hooks/use-dashboard.ts`, `hooks/use-approval.ts` — hook นับสด + อนุมัติ (ยังไม่ wire)
