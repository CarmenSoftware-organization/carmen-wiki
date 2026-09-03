---
title: แดชบอร์ด (Dashboard)
description: หน้า /dashboard เพียงหน้าเดียว — header ทักทายพร้อมกริด "Saved Widgets" แบบ drag-and-drop ส่วนตัว ประกอบด้วย card KPI/pie ที่ขับเคลื่อนด้วย dataset ซึ่งผู้ใช้แต่ละคนสร้างขึ้นเอง
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ด (Dashboard)

> **At a Glance**
> **Route:** `/dashboard` (root `/` redirect มาที่นี่) &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **Live** — หน้าเดียว: header ทักทาย + กริด "Saved Widgets" ส่วนตัว ขับเคลื่อนด้วย API จริง

![แดชบอร์ด (Dashboard) screen](/screenshots/dashboard/index.png)

## สถานะการ implement (ตรวจสอบเมื่อ 2026-07-16)

โมดูล Dashboard คือ **หนึ่ง route หนึ่ง component** ไม่ใช่กลุ่ม sidebar ของหกหน้าโดเมน `constant/module-list.ts` ลงทะเบียน entry ระดับบนสุดเพียงหนึ่งรายการ คือ `{ name: "dashboard", path: "/dashboard" }` ไม่มี sub-module ใดๆ; `routes/router.tsx` มี nested route เพียงหนึ่งเดียว คือ `{ path: "dashboard", lazy: () => import("./dashboard/dashboard.route") }` ซึ่ง resolve ไปยัง `DashboardComponent` (header ทักทาย + กริด "Saved Widgets", `routes/dashboard/dashboard-component.tsx`)

หน้าย่อยทั้งแปดหน้าภายใต้โมดูล wiki นี้ (`dashboard/main`, `pr`, `po`, `grn`, `inventory`, `sr`, `my-pending`, `my-approval`) แต่ละหน้า document หน้าย่อยโดเมนที่มีชื่อ (`/dashboard/pr`, `/dashboard/po`, …) หรือ section "companion widget" บน `/dashboard` **ไม่มีหน้าใดเลยที่เคยมี route จริง** เมื่อตรวจสอบประวัติ router: แม้ก่อนการ cleanup ล่าสุด `dashboard/page.tsx` ก็ render component เดียวกันกับที่เห็นทุกวันนี้เสมอมา คือ header ทักทาย + กริด saved-widgets ไฟล์แยกตามโดเมน (`dashboard-main.tsx`, `dashboard-pr.tsx`, `dashboard-po.tsx`, `dashboard-grn.tsx`, `dashboard-inventory.tsx`, `dashboard-sr.tsx`) และไฟล์ companion-widget สองไฟล์ (`dashboard-my-pending.tsx`, `dashboard-my-approval.tsx`) นั่งอยู่ใน `_components/` โดยไม่เคยถูก route commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) ลบทั้งแปดไฟล์นี้พร้อมโฟลเดอร์ `mock/` โดยระบุไว้ตรงๆ ว่า *"The mock-fed widgets and the my-pending/my-approval widgets were dead code carried over from the source app — no importers anywhere."*

ผลกระทบเชิงปฏิบัติต่อ wiki นี้: หน้าย่อยด้านล่าง (จำนวนไฟล์ไม่เปลี่ยนแปลง) ถูกเก็บไว้เป็น **ข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น** สำหรับหน้าจอ demo ที่ไม่เคยเข้าถึงได้จริงและไม่มีอยู่บนดิสก์อีกต่อไป ถือว่าทุกการอ้าง route, "ยังเป็น mock data ในปัจจุบัน" และ "การ wire จริงรอ" ในหน้าเหล่านั้นเป็นโมฆะ — จะไม่มีวัน live เพราะ component ถูกลบไปแล้ว

## 1. คืออะไรและสำหรับใคร

Dashboard คือหน้าจอแรกที่ผู้ปฏิบัติงานทุกคนเห็นหลังเข้าระบบ (root `/` redirect ไปยัง `/dashboard`) มันแสดง:

- **Header ทักทาย** — "Good Morning/Afternoon/Evening, {ชื่อเต็ม}" พร้อมวันที่ปัจจุบันแบบ localized มาจากโปรไฟล์ผู้ใช้
- **Section "Saved Widgets"** — กริด drag-and-drop ส่วนตัวของ card ที่ขับเคลื่อนด้วย dataset ผู้ใช้แต่ละคนสร้าง layout ของตัวเองตั้งแต่ต้น ไม่มี layout ที่กำหนดไว้ล่วงหน้าหรือ curate โดย admin บนหน้านี้

ดูหน้า [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) สำหรับเอกสารอ้างอิงเต็มรูปแบบ (layout, การเรียก API, การแก้ปัญหา)

**กลุ่มผู้ใช้:** ผู้ปฏิบัติงานที่ล็อกอินทุกคน — ไม่มีการ route ตาม persona บนหน้านี้ ชุด widget ที่บันทึกไว้ของผู้ใช้แต่ละคนเป็นของตนเองทั้งหมด (scope ด้วย `user_id`) ดังนั้นสิ่งที่ Requestor, Approver หรือ Purchaser เห็นบนหน้านี้ขึ้นอยู่กับ dataset ที่พวกเขาปักหมุดไว้เองเท่านั้น ไม่ใช่ตาม role

## 2. หน้าในโมดูลนี้

**หน้า live จริง**

- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — route `/dashboard` จริง; กริด widget ส่วนตัวแบบ drag-and-drop ที่ขับเคลื่อนด้วย dataset จริง

**ข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น — ถูกลบเมื่อ 2026-06-27 ไม่เคยมี route จริง**

- [dashboard/main](/th/inventory/dashboard/main) — document demo `dashboard-main.tsx` ที่ถูกลบ (tile KPI landing ข้ามโมดูล)
- [dashboard/pr](/th/inventory/dashboard/pr) — document demo `dashboard-pr.tsx` ที่ถูกลบ (pipeline PR, send-back/reject)
- [dashboard/po](/th/inventory/dashboard/po) — document demo `dashboard-po.tsx` ที่ถูกลบ (pipeline PO, การส่งของล่าช้า)
- [dashboard/grn](/th/inventory/dashboard/grn) — document demo `dashboard-grn.tsx` ที่ถูกลบ (KPI GRN, PO ค้างตามช่วงวัน)
- [dashboard/inventory](/th/inventory/dashboard/inventory) — document demo `dashboard-inventory.tsx` ที่ถูกลบ (pipeline สต๊อก, เติมสต๊อก, PST)
- [dashboard/sr](/th/inventory/dashboard/sr) — document demo `dashboard-sr.tsx` ที่ถูกลบ (pipeline SR, กราฟการบริโภค)
- [dashboard/my-pending](/th/inventory/dashboard/my-pending) — document widget `dashboard-my-pending.tsx` ที่ถูกลบ (จำนวน pending ส่วนตัว); hook เบื้องหลัง (`useMyPendingPrCount`/`PoCount`/`SrCount`) ยังอยู่ใน `hooks/use-dashboard.ts` แต่ไม่มี call site เลยในทั้ง frontend
- [dashboard/my-approval](/th/inventory/dashboard/my-approval) — document widget `dashboard-my-approval.tsx` ที่ถูกลบ (คิว approval ส่วนตัว); หน้าจริงที่ live คือหน้า **My Approval** ของโมดูล Procurement — ดู [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) (`/procurement/approval`)

---

## 3. แหล่งข้อมูล (Dev)

- **Saved widgets (ส่วนตัว)** — `GET /api/proxy/api/me/dashboard-widgets?bu_code=` แสดงรายการ widget ที่ผู้ใช้ปักหมุดไว้; `POST`/`PATCH`/`DELETE` บน path เดียวกันใช้สร้าง, เรียงใหม่/เปลี่ยนชื่อ และลบ ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) §5 สำหรับรูปแบบเต็ม
- **Dataset catalog** — picker "+ Add Widget" (`LookupDataset`) query dataset catalog ที่ code-registered ให้บริการโดย **micro-data** ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset)
- **Endpoint ที่พบใน source แต่ไม่ถูกเรียกจากหน้านี้ (dead/unused):** `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (hook มีอยู่ ไม่มี call site) และ endpoint คิว approval ที่ `/procurement/approval` ใช้แทน (ดู [purchase-request/my-approval](/th/inventory/purchase-request/my-approval)) ไม่ใช่ `/dashboard`

## 4. โมดูลที่เกี่ยวข้อง

- [reporting-audit](/th/inventory/reporting-audit), [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — dataset catalog และ data model ของ widget/reporting ที่อยู่เบื้องหลัง saved widget ทุกตัว
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory) — โมดูล transactional ที่ผู้ใช้น่าจะปักหมุด dataset มาจาก แต่ไม่ได้ wire ตรงเข้ากับหน้านี้
- [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) — inbox approval ส่วนตัวที่ live จริง (`/procurement/approval`); ไม่ได้เป็นส่วนหนึ่งของโมดูล Dashboard นี้

## 5. แหล่งข้อมูลอ้างอิง

- `../carmen-inventory-frontend-react/routes/router.tsx` — การลงทะเบียน route เดียว: `{ path: "dashboard", lazy: () => import("./dashboard/dashboard.route") }`
- `../carmen-inventory-frontend-react/routes/dashboard/dashboard.route.tsx`, `dashboard-component.tsx`, `sortable-widget-item.tsx` — หน้า live ทั้งหมด (flatten ออกจาก `_components/` โดย cleanup เมื่อ 2026-06-27)
- `../carmen-inventory-frontend-react/constant/module-list.ts` — การลงทะเบียน sidebar แบบ entry เดียว (ไม่มี sub-module)
- `../carmen-inventory-frontend-react/hooks/use-my-dashboard-widgets.ts` — hook CRUD ของ widget ส่วนตัวที่หน้า live ใช้จริง
- `../carmen-inventory-frontend-react/hooks/use-dashboard.ts` — `useMyPendingPrCount`/`PoCount`/`SrCount`; ยังอยู่ใน source ไม่พบ call site เลยในทั้ง repo
- Commit ที่ลบ: `03891e3d` ใน `../carmen-inventory-frontend-react` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) — ลบ `_components/dashboard-{main,pr,po,grn,sr,inventory,my-pending,my-approval}.tsx` และ `mock/{main,pr,po,grn,sr,inventory}.ts` (19 ไฟล์, เพิ่ม 6 บรรทัด / ลบ 5,468 บรรทัด)
