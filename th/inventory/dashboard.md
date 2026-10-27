---
title: แดชบอร์ด (Dashboard)
description: หน้า /dashboard: header ทักทาย ส่วน widget ของ Business unit ที่ใช้ร่วมกัน และกริด Saved Widgets 12 คอลัมน์แบบ drag-and-drop ของผู้ใช้แต่ละคน ที่ขับเคลื่อนด้วย dataset
published: true
date: '2026-10-27T15:00:00.000Z'
tags: dashboard, kpi, reporting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ด (Dashboard)

> **At a Glance**
> **Route:** `/dashboard` (root `/` redirect มาที่นี่) &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **Live** — หน้าเดียว: header ทักทาย + กริด "Saved Widgets" ส่วนตัว ขับเคลื่อนด้วย API จริง

![แดชบอร์ด (Dashboard) screen](/screenshots/dashboard/index.png)

## สถานะการ implement (ตรวจสอบเมื่อ 2026-07-16, ตรวจสอบซ้ำ 2026-10-27)

**การตรวจสอบซ้ำ 2026-10-27** ยังคงเป็นหนึ่ง route (`/dashboard`) และหนึ่ง component ระดับบนสุด สิ่งที่เปลี่ยนตั้งแต่ 2026-09-22 (FE `0713cbc9..391062b5`, backend `ef4d6f08f..c9d788829`, micro-data `7f21905..c9aa145`): **(1) ส่วน widget ของ BU ที่ใช้ร่วมกัน** ตอนนี้ render เหนือกริดส่วนตัวบน `/dashboard` และที่ท้ายของทุก dashboard ระดับโมดูล — ตาราง `tb_dashboard_bu_widget` ที่ scope ตาม BU ซึ่งข้อความ 2026-09-22 เรียกว่า "backend เท่านั้น ไม่มี UI" ตอนนี้มีหน้าจอแล้ว (`components/dashboard-widget/bu-widget-section.tsx`, 2026-10-06); **(2) ชื่อ widget เป็นสองภาษา** (`title_i18n` `{ en, th? }`, micro-data migration `132_dash_widget_title_i18n`); **(3) component ของ widget ที่ใช้ร่วมกันถูกย้าย** จาก `routes/dashboard/` ไปที่ `components/dashboard-widget/` (`sortable-widget-item.tsx`, `widget-config-dialog.tsx`, `widget-param-fields.tsx`, `widget-display-fields.tsx`, `widget-shape.ts`) เพื่อให้ส่วน BU และ dashboard ระดับโมดูลใช้ซ้ำ; **(4) widget แบบ table ลิงก์แถวไปยังเอกสารได้** (`TableColumn.link` เช่น เซลล์ Type ของ dataset `inventory.slow-moving` ใหม่); **(5)** empty state ตอนนี้มีปุ่ม "add widget" จริงที่เปิด picker เดียวกับปุ่มบน header รายละเอียดใน [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) § 1.4-1.6

**การตรวจสอบซ้ำ 2026-09-22 (เก็บไว้เป็นประวัติ)** ยังคงเป็นหนึ่ง route หนึ่ง component สิ่งที่เปลี่ยนตั้งแต่ 2026-07-29: entry ใน sidebar ตอนนี้มี `licenseFeature: "dashboard.widget"` (`constant/module-list.ts`; license catalog ฝั่ง backend map `app:dashboard-widgets` → `dashboard.widget`); กริดกลายเป็น layout 12 คอลัมน์พร้อมขนาดต่อ widget, card แบบ gauge, การสลับ render, lazy loading ต่อ widget, dialog parameter/display และ card แบบ status-group (ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) §1); และ `hooks/use-dashboard.ts` ที่ตายแล้ว (`useMyPendingPrCount`/`PoCount`/`SrCount`) ที่อ้างถึงด้านล่างถูก**ลบ**ในที่สุดเมื่อ 2026-08-31 (`02228125`, "ลบโค้ดตาย 17 ไฟล์") `hooks/use-approval.ts` ย้ายไป `routes/procurement/approval/use-approval.ts` (2026-08-28, `0d9757f3`) และ `/procurement/approval` ตอนนี้อ่าน view รวม `GET /api/my-pending` แทนการเรียกสามครั้งต่อประเภท (2026-09-16, `9bd21427`)

โมดูล Dashboard คือ **หนึ่ง route หนึ่ง component** ไม่ใช่กลุ่ม sidebar ของหกหน้าโดเมน `constant/module-list.ts` ลงทะเบียน entry ระดับบนสุดเพียงหนึ่งรายการ คือ `{ name: "dashboard", path: "/dashboard" }` ไม่มี sub-module ใดๆ; `routes/router.tsx` มี nested route เพียงหนึ่งเดียว คือ `{ path: "dashboard", lazy: () => import("./dashboard/dashboard.route") }` ซึ่ง resolve ไปยัง `DashboardComponent` (header ทักทาย + กริด "Saved Widgets", `routes/dashboard/dashboard-component.tsx`)

หน้าย่อยทั้งแปดหน้าภายใต้โมดูล wiki นี้ (`dashboard/main`, `pr`, `po`, `grn`, `inventory`, `sr`, `my-pending`, `my-approval`) แต่ละหน้า document หน้าย่อยโดเมนที่มีชื่อ (`/dashboard/pr`, `/dashboard/po`, …) หรือ section "companion widget" บน `/dashboard` **ไม่มีหน้าใดเลยที่เคยมี route จริง** เมื่อตรวจสอบประวัติ router: แม้ก่อนการ cleanup ล่าสุด `dashboard/page.tsx` ก็ render component เดียวกันกับที่เห็นทุกวันนี้เสมอมา คือ header ทักทาย + กริด saved-widgets ไฟล์แยกตามโดเมน (`dashboard-main.tsx`, `dashboard-pr.tsx`, `dashboard-po.tsx`, `dashboard-grn.tsx`, `dashboard-inventory.tsx`, `dashboard-sr.tsx`) และไฟล์ companion-widget สองไฟล์ (`dashboard-my-pending.tsx`, `dashboard-my-approval.tsx`) นั่งอยู่ใน `_components/` โดยไม่เคยถูก route โดยแต่ละไฟล์มี fixture `mock/*.ts` ของตัวเอง commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) ลบทั้งแปดไฟล์นี้พร้อมโฟลเดอร์ `mock/` โดยระบุไว้ตรงๆ ว่า *"The mock-fed widgets and the my-pending/my-approval widgets were dead code carried over from the source app — no importers anywhere."*

ผลกระทบเชิงปฏิบัติต่อ wiki นี้: หน้าย่อยด้านล่าง (จำนวนไฟล์ไม่เปลี่ยนแปลง) ถูกเก็บไว้เป็น **ข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น** สำหรับหน้าจอ demo ที่ไม่เคยเข้าถึงได้จริงและไม่มีอยู่บนดิสก์อีกต่อไป ถือว่าทุกการอ้าง route, "ยังเป็น mock data ในปัจจุบัน" และ "การ wire จริงรอ" ในหน้าเหล่านั้นเป็นโมฆะ — จะไม่มีวัน live เพราะ component ถูกลบไปแล้ว

## 1. คืออะไรและสำหรับใคร

Dashboard คือหน้าจอแรกที่ผู้ปฏิบัติงานทุกคนเห็นหลังเข้าระบบ (root `/` redirect ไปยัง `/dashboard`) มันแสดง:

- **Header ทักทาย** — "Good Morning/Afternoon/Evening, {ชื่อเต็ม}" พร้อมวันที่ปัจจุบันแบบ localized มาจากโปรไฟล์ผู้ใช้
- **Section "Business unit dashboard"** (ใหม่ 2026-10-06) — widget ที่ administrator ปักหมุดไว้สำหรับทั้ง business unit; ทุกคนใน BU เห็นชุดเดียวกัน และผู้ใช้ที่ถือ `dashboard.bu_widget:create/update/delete` เพิ่ม แก้ไข ลบ และจัดลำดับได้ section นี้ซ่อนตัวเองเมื่อ BU ไม่มี widget และผู้ใช้เพิ่มไม่ได้ หรือเมื่อการเรียก backend ล้มเหลว
- **Section "Saved Widgets"** — กริด drag-and-drop 12 คอลัมน์ส่วนตัวของ card ที่ขับเคลื่อนด้วย dataset (KPI, gauge, pie, bar, line, area, table) บวก card pipeline สถานะ PR/PO/SR แบบเต็มความกว้าง แต่ละ card มีขนาด parameter และการตั้งค่า display ของตัวเอง; ผู้ใช้แต่ละคนสร้าง layout ส่วนตัวของตัวเองตั้งแต่ต้น (ส่วนที่ admin curate คือส่วน BU ด้านบน; platform administrator ยัง push ชุด BU เริ่มต้นไปยังหลาย BU ได้ด้วย — ดู § 3)

ดูหน้า [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) สำหรับเอกสารอ้างอิงเต็มรูปแบบ (layout, การเรียก API, การแก้ปัญหา)

**กลุ่มผู้ใช้:** ผู้ปฏิบัติงานที่ล็อกอินทุกคน — ไม่มีการ route ตาม persona บนหน้านี้ ชุด widget ที่บันทึกไว้ของผู้ใช้แต่ละคนเป็นของตนเองทั้งหมด (scope ด้วย `user_id`) ดังนั้นสิ่งที่ Requestor, Approver หรือ Purchaser เห็นในกริดส่วนตัวขึ้นอยู่กับ dataset ที่พวกเขาปักหมุดไว้เองเท่านั้น ไม่ใช่ตาม role; ส่วน BU ด้านบนเหมือนกันสำหรับทุกคนใน business unit

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
- [dashboard/my-pending](/th/inventory/dashboard/my-pending) — document widget `dashboard-my-pending.tsx` ที่ถูกลบ (จำนวน pending ส่วนตัว); hook เบื้องหลัง (`useMyPendingPrCount`/`PoCount`/`SrCount`, `hooks/use-dashboard.ts`) ถูกลบเป็น dead code เมื่อ 2026-08-31 (`02228125`); เหลือแค่ค่าคงที่ endpoint `MY_PENDING_*_COUNT` ที่ยังประกาศอยู่
- [dashboard/my-approval](/th/inventory/dashboard/my-approval) — document widget `dashboard-my-approval.tsx` ที่ถูกลบ (คิว approval ส่วนตัว); หน้าจริงที่ live คือหน้า **My Approval** ของโมดูล Procurement — ดู [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) (`/procurement/approval`)

---

## 3. แหล่งข้อมูล (Dev)

- **Saved widgets (ส่วนตัว)** — `GET /api/proxy/api/me/dashboard-widgets?bu_code=` แสดงรายการ widget ที่ผู้ใช้ปักหมุดไว้; `POST`/`PATCH`/`DELETE` บน path เดียวกันใช้สร้าง, อัปเดต (`title`, `order_index`, `params`, `widget_type`, `display`) และลบ ให้บริการโดย **micro-data** (Go) ผ่าน gateway proxy พร้อม header `x-internal-token` ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) §5 สำหรับรูปแบบเต็ม
- **BU widgets (ใช้ร่วมกัน)** — `GET /api/proxy/api/{bu}/dashboard-widgets/bu?module=` (`module=main` สำหรับ `/dashboard` มิฉะนั้นเป็นหนึ่งใน `procurement`, `inventory`, `product`, `config`, `vendor-management`, `operation-plan`, `store-operation`) คืน `{ items[], count, deploy_state }`; `POST`, `PATCH /{id}`, `DELETE /{id}` และ `PATCH .../bu/reorder` ต้องมี `dashboard.bu_widget:create|update|delete` (การอ่านสองตัวไม่มี `@Permission`) ค่ามาจาก `GET .../dashboard-lab/widgets/{id}/data?scope=bu` ให้บริการโดย micro-data (`/api/dashboard/bu-widgets*`) ผ่าน gateway proxy platform administrator push ชุดเริ่มต้นไปยัง BU ได้จากโมดูล dashboard-templates ของ Backstage (gateway `api-system/dashboard-templates` ซึ่งเรียก micro-data `POST /api/dashboard/bu-widgets/deploy` ด้วยโหมด `skip_customized` หรือ `overwrite`; `GET .../deploy-state` รายงาน `deployed_version` / `customized_at`); การแก้ไขด้วยมือครั้งแรกจะประทับ `customized_at` และหน้าจะเตือนหนึ่งครั้งว่า BU ตอนนี้ต่างจากค่าเริ่มต้นของ platform ดู [reporting-audit/widget](/th/inventory/reporting-audit/widget) § 5
- **ค่าของ widget** — `GET /api/proxy/api/{bu}/dashboard-lab/widgets/{widget_id}/data?scope=personal` แบบ lazy หนึ่งครั้งต่อ card (รัน dataset ที่เก็บไว้ + params); card แบบ status-group ใช้ `POST .../dashboard-lab/datasets/document.{doc}-by-status`
- **Dataset catalog** — picker "+ Add Widget" (`LookupDataset`) query `GET /api/proxy/api/{bu}/dashboard-lab/datasets` (พร้อม descriptor `params[]` และ `supported_renders[]`) ซึ่งเป็น registry ที่ code-registered ให้บริการโดย **micro-data** ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset)
- **Endpoint ที่ไม่ได้ใช้แต่ยังประกาศใน `constant/api-endpoints.ts`:** `GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count` (`MY_PENDING_*_COUNT` — hook ของมันถูกลบ 2026-08-31 ไม่มีผู้เรียก) คิว approval ถูก consume โดย `/procurement/approval` (`GET /api/my-pending` + `GET /api/my-approve/pending` ดู [purchase-request/my-approval](/th/inventory/purchase-request/my-approval)) ไม่ใช่ `/dashboard`

## 4. โมดูลที่เกี่ยวข้อง

- [reporting-audit](/th/inventory/reporting-audit), [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — dataset catalog และ data model ของ widget/reporting ที่อยู่เบื้องหลัง saved widget ทุกตัว
- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory) — โมดูล transactional ที่ผู้ใช้น่าจะปักหมุด dataset มาจาก แต่ไม่ได้ wire ตรงเข้ากับหน้านี้
- [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) — inbox approval ส่วนตัวที่ live จริง (`/procurement/approval`); ไม่ได้เป็นส่วนหนึ่งของโมดูล Dashboard นี้

## 5. แหล่งข้อมูลอ้างอิง

- `../carmen-frontend/routes/router.tsx` — การลงทะเบียน route เดียว: `{ path: "dashboard", lazy: () => import("./dashboard/dashboard.route") }`
- `../carmen-frontend/routes/dashboard/dashboard.route.tsx`, `dashboard-component.tsx`, `status-group.ts`, `status-group-card.tsx` และ ใช้ร่วมกับ dashboard ระดับโมดูลตั้งแต่ 2026-10-06 `../carmen-frontend/components/dashboard-widget/` (`bu-widget-section.tsx`, `sortable-widget-item.tsx`, `widget-config-dialog.tsx`, `widget-param-fields.tsx`, `widget-display-fields.tsx`, `widget-shape.ts`, `widget-title.ts`, `table-row-link.ts`) — หน้า live ทั้งหมด
- `../carmen-frontend/constant/module-list.ts` — การลงทะเบียน sidebar แบบ entry เดียว (ไม่มี sub-module), `licenseFeature: "dashboard.widget"`
- `../carmen-frontend/docs/dashboard-widgets.md` — แคตตาล็อกที่ generate จาก dataset registry ของ dev (`bun run docs:widgets`, 2026-10-22); เป็น snapshot ให้ generate ใหม่แทนการ copy จากมัน
- `../carmen-frontend/hooks/use-bu-dashboard-widgets.ts` — list/create/update/delete/reorder ของ BU widget + data query; `../carmen-frontend/routes/dashboard/use-my-dashboard-widgets.ts` — hook CRUD ของ widget ส่วนตัว + hook ข้อมูลต่อ widget ที่หน้า live ใช้จริง (ย้ายจาก `hooks/` เมื่อ 2026-08-28)
- `../carmen-frontend/hooks/use-dashboard.ts` — **ถูกลบ 2026-08-31** (`02228125`); ค่าคงที่ `MY_PENDING_*_COUNT` ที่มันใช้ยังอยู่ใน `constant/api-endpoints.ts` โดยไม่มีผู้เรียก
- `../carmen-turborepo-backend/apps/backend-gateway/src/application/dashboard-widgets/`, `dashboard-lab/` และ `../micro-data/` — backend (ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) §8)
- Commit ที่ลบ: `03891e3d` ใน `../carmen-frontend` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) — ลบ `_components/dashboard-{main,pr,po,grn,sr,inventory,my-pending,my-approval}.tsx` และ `mock/{main,pr,po,grn,sr,inventory}.ts` (19 ไฟล์, เพิ่ม 6 บรรทัด / ลบ 5,468 บรรทัด)
