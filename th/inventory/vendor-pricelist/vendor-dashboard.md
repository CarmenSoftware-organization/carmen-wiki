---
title: Vendor Management Dashboard
description: หน้าจอ /vendor-management — 10 tile KPI/chart ที่ hardcode ไว้ (vendor + pricelist + RFP) มาจาก dataset catalog ที่ลงทะเบียนในโค้ด ไม่ใช่ widget board ที่ผู้ใช้ปรับแต่งได้
published: true
date: 2026-07-29T10:15:00.000Z
tags: vendor-pricelist, vendor-management, dashboard, widget, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:15:00.000Z
---

# Vendor Management Dashboard

> **สรุปโดยย่อ**
> **Route:** `/vendor-management` (index) &nbsp;·&nbsp; **Component:** `vendor-dashboard.tsx` &nbsp;·&nbsp; **Data:** `GET /api/{bu_code}/dashboard-widgets/vendor-management` &nbsp;·&nbsp; **Tiles:** 10 tile hardcode (7 KPI, 2 chart, 1 line) ครอบคลุม vendor, pricelist, และ RFP &nbsp;·&nbsp; **แก้ไขไม่ได้** — ไม่มี UI add/remove/reorder ไม่มีการปรับแต่งตาม tenant

![Vendor Management dashboard](/screenshots/vendor-management/index.png)

## 1. คืออะไรและใครใช้

Vendor Management Dashboard คือหน้าจอ landing ที่ `/vendor-management` แสดงก่อนที่ผู้ใช้จะเลือก [Vendor](/th/inventory/vendor-pricelist), Price List, Price List Template หรือ [Request for Pricing](/th/inventory/vendor-pricelist/request-price-list) มันแสดงชุด tile คงที่ **10 ชิ้น** สร้างจาก entry `vendor.*`, `pricelist.*`, และ `rfp.*` ใน catalog ของ [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) i18n key คือ `vendorManagement.dashboard` (`title: "Vendor Overview"`, `description: "Vendor, pricelist, and RFP status"`)

ต่างจาก [operation-dashboard](/th/inventory/recipe/operation-dashboard) (ที่มี layout component เฉพาะตัว) หน้าจอนี้เป็น wrapper บาง ๆ รอบ component `DashboardWidgetGrid` ที่ใช้ร่วมกัน — component เดียวกับที่ module dashboard อื่นจะใช้ถ้าเลือกใช้ซ้ำ มัน render เป็น grid แบนเดียวที่ responsive แทนที่จะเป็น section ที่ตั้งชื่อ เรียงตาม render-group ของ widget-type ที่ตายตัว (`kpi`/`gauge` → `sparkline` → `pie` → `bar` → `line`/`area` → `table` → `heatmap`) แล้วเรียงตาม `order_index` ภายในแต่ละกลุ่ม

**นี่เป็นกลไกเดียวกับที่ hardcode และแก้ไขไม่ได้ ที่บันทึกไว้เต็มที่ [recipe/operation-dashboard](/th/inventory/recipe/operation-dashboard) §6** — array TypeScript คงที่ (`VENDOR_MANAGEMENT_WIDGETS` ใน `system-widgets.config.ts`) ไม่มีแถวฐานข้อมูลรองรับ tile ใดเลย ให้บริการโดย endpoint เฉพาะ module บน `DashboardSystemWidgetsController` (`api/:bu_code/dashboard-widgets/vendor-management`) — **ไม่ใช่** `tb_dashboard_bu_widget`/`tb_dashboard_personal_widget` (ตาราง widget จริงที่แก้ไขได้ ที่บันทึกไว้ที่ [reporting-audit/widget](/th/inventory/reporting-audit/widget))

**ดูแลโดย** Engineering (ต้องแก้โค้ด + deploy เพื่อเพิ่ม/ลบ/จัดเรียง tile — ไม่มีหน้าจอ admin) **อ่านโดย** ผู้ใช้ที่ authenticate แล้วคนใดก็ตามที่โหลด `/vendor-management` ได้ — ไม่พบการเช็ค permission ที่ gate ตัว data endpoint เอง

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู KPI ของ vendor-management | ไปที่ `/vendor-management` | โหลดอัตโนมัติ; ไม่มี filter/date-range control |
| ดูรายละเอียดของ metric | คลิก tile (แสดงผลอย่างเดียว) | tile เป็น card แบบ read-only ไม่ใช่ link — ต้องไปที่ Vendor / Price List / Request for Pricing เองเพื่อดูข้อมูลจริง |
| เพิ่ม/ลบ/จัดเรียง tile | **ทำจาก UI ไม่ได้** | ต้องแก้โค้ด `system-widgets.config.ts` (backend-gateway) |
| ลองใหม่หลัง load error | รีโหลดหน้า | banner error เดียว (`dashboardWidget.loadError`) ครอบคลุมทั้งชุด tile — ไม่มีการ retry รายชิ้น |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| Dashboard ทั้งหมดแสดง banner error | `GET .../dashboard-widgets/vendor-management` ล้มเหลว | **ยืนยันแล้ว** — `DashboardWidgetGrid` render banner `role="alert"` เดียว ผูกกับ `isError` ของ query |
| Tile หายไปจาก grid เฉย ๆ | `dataset_id` ของมัน resolve ไม่สำเร็จ (`meta`/`data` หาย) | **ยืนยันแล้ว** — `WidgetRouter` คืน `null` สำหรับ widget ใดที่ไม่มีทั้ง `meta` และ `data` |
| ข้อความ empty-state ("No widget data") | dataset ที่ตั้งค่าไว้ทั้ง 10 ตัว resolve ไม่สำเร็จ | **ยืนยันแล้ว** — เช็คกับ widget list หลัง filter ที่ว่างเปล่า |
| Skeleton grid แสดง placeholder card 6 ชิ้นตอนโหลด | `SKELETON_KEYS` (`a`-`f`) hardcode ไว้ใน Suspense fallback ของ `dashboard-widget-grid-lazy.tsx` | **ยืนยันแล้ว** — เป็นเรื่อง cosmetic เท่านั้น; ชุดจริงที่ resolve คือ 10 tile ไม่ใช่ 6 |
| Chart library (`recharts`) ยังไม่โหลดชั่วขณะตอนเข้าหน้าครั้งแรก | `DashboardWidgetGrid` เป็น lazy-load (`React.lazy` + `Suspense`) เพื่อกัน `recharts` (~100-150KB gzipped) ไม่ให้อยู่ใน first-load JS | **ยืนยันแล้ว** ตามการออกแบบ — code comment ของ `dashboard-widget-grid-lazy.tsx` ระบุไว้ชัดเจน |

## 4. กรณีพิเศษ

- **ไม่พบ permission gate บน data endpoint** `DashboardSystemWidgetsController` ถูก guard ด้วย `KeycloakGuard` เท่านั้น — ไม่พบ permission decorator บน route handler ของ `vendor-management` นี่ต่างจาก sidebar gate ของหน้าจอย่อย `/vendor-management/*` เองที่ใช้ permission key `vendor_management.*` จริง (เช่น `vendor_management.vendor.view`) — key เหล่านี้ยืนยันแล้วว่าจริงใน permission catalog ฝั่ง backend (ต่างจาก placeholder `operation_plan.view` ของ `recipe`) แต่ไม่มี key ใดเลยที่ gate data call ของ dashboard นี้เช่นกัน
- **Tile เป็นของ hardcode ไม่ใช่ข้อมูลที่เก็บไว้** ทุก business unit เห็น tile ทั้ง 10 ชิ้นในลำดับเดียวกันเป๊ะ — ไม่มีอะไรเกี่ยวกับการเลือก tile, ลำดับ, หรือ title ที่ปรับแต่งได้ตาม tenant ผ่านหน้าจอนี้
- **`rfp.issued-daily` เป็น tile time-series เพียงตัวเดียว** — chart แบบ `line` แม้ module นี้จะไม่มี section Trends แยกไว้ชัดเจน (ต่างจาก [operation-dashboard](/th/inventory/recipe/operation-dashboard) ที่จัดกลุ่มเป็น section ชัดเจน grid ที่ใช้ร่วมกันของหน้าจอนี้แค่วางมันต่อจาก tile bar/pie ตามลำดับ render-group ที่ตายตัว)
- **KPI สองตัวเกี่ยวกับ pricelist lifecycle อยู่ข้างกันโดยไม่มีการแยกความเร่งด่วนทางสายตา:** `pricelist.active-count` (scalar ธรรมดา) และ `pricelist.expiring-soon` (scalar ธรรมดาเช่นกัน "≤30d") render เป็น `KpiCard` เหมือนกัน — ไม่มีสี/badge เร่งด่วนบน tile expiring-soon แม้จะมีความสำคัญเชิงปฏิบัติการก็ตาม
- **Cache** query ของ widget list ใช้ `CACHE_DYNAMIC` (`useVendorWidgets` → `useDashboardWidgets("vendor-management")`) tier เดียวกับ dashboard module อื่นทุกตัว

---

## 5. Tiles (Dev)

Source: `apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts`, `VENDOR_MANAGEMENT_WIDGETS`

| # | `dataset_id` | Type | ชื่อ (ไทย ตามที่เขียนในโค้ด) |
|---|---|---|---|
| 0 | `vendor.total-active` | kpi | Vendor active |
| 1 | `vendor.added-7d` | kpi | Vendor เพิ่มใน 7 วัน |
| 2 | `vendor.without-products` | kpi | Vendor ไม่มี product |
| 3 | `pricelist.active-count` | kpi | Pricelist active |
| 4 | `pricelist.expiring-soon` | kpi | Pricelist ใกล้หมดอายุ (30d) |
| 5 | `rfp.active` | kpi | RFP เปิดอยู่ |
| 6 | `rfp.upcoming-7d` | kpi | RFP จะเปิดใน 7 วัน |
| 7 | `pricelist.by-status` | pie | Pricelist แยกตามสถานะ |
| 8 | `pricelist.by-vendor-top` | bar | Top 10 vendor ตามจำนวน pricelist |
| 9 | `rfp.issued-daily` | line | RFP สร้างต่อวัน (30d) |

ชื่อ (title) hardcode ไว้บน config entry (เป็นภาษาไทยใน source ปัจจุบัน) ไม่ได้แปลผ่าน `use-intl` `dataset_id` แต่ละตัว resolve กับ section **"Vendor management module"** ของ `micro-data/service/dashboard/registry.go` — ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) §5 สำหรับสัญญา catalog เต็ม รวมถึง category `spend` ที่ทั้ง 10 ตัวนี้ใช้ร่วมกัน

## 6. ความเชื่อมโยงข้ามโมดูล

- [vendor-pricelist](/th/inventory/vendor-pricelist) — module แม่; บันทึกหน้าจอ CRUD จริง 4 หน้า (Vendor, Price List, Price List Template, Request for Pricing) ที่ dashboard นี้สรุปแต่ไม่ได้ link ไป
- [vendor-pricelist/request-price-list](/th/inventory/vendor-pricelist/request-price-list) — แหล่งของ dataset `rfp.*`
- [recipe/operation-dashboard](/th/inventory/recipe/operation-dashboard) — module dashboard คู่กันสำหรับ Operation Plan; §6 มีการเปรียบเทียบเต็มกับระบบ widget BU/personal จริง และการอ้างอิงที่หน้านี้แก้ไข
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — catalog ที่ลงทะเบียนในโค้ดที่ `dataset_id` ทุกตัวในหน้านี้อ้างอิง
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — ระบบ widget BU/personal จริงที่แก้ไขได้ ที่หน้าจอนี้มักถูกเข้าใจผิดว่าเป็นเรื่องเดียวกัน

## 7. แหล่งอ้างอิง

- **Frontend route:** `../carmen-inventory-frontend-react/routes/vendor-management/vendor-management.route.tsx` → `vendor-dashboard.tsx`
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-dashboard-widgets.ts` — `useVendorWidgets()`
- **Frontend shared component:** `../carmen-inventory-frontend-react/components/dashboard-widget/dashboard-widget-grid-lazy.tsx` (lazy wrapper) → `dashboard-widget-grid.tsx` ของ `DashboardWidgetGrid`
- **Gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.controller.ts` — `DashboardSystemWidgetsController`, `@Get('vendor-management')`
- **Gateway config:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts` — `VENDOR_MANAGEMENT_WIDGETS`, `getSystemWidgets()`
- **Dataset registry:** `../micro-data/service/dashboard/registry.go` — entry vendor/pricelist/RFP (บรรทัด ~127-147)
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `vendorManagement.dashboard.title`/`.description`
