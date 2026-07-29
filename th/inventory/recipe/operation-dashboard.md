---
title: Operation Plan Dashboard
description: หน้าจอ /operation-plan — 10 tile KPI/chart ที่ hardcode ไว้ (recipe + equipment) มาจาก dataset catalog ที่ลงทะเบียนในโค้ด ไม่ใช่ widget board ที่ผู้ใช้ปรับแต่งได้
published: true
date: 2026-07-29T10:00:00.000Z
tags: recipe, operation-plan, dashboard, widget, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:00:00.000Z
---

# Operation Plan Dashboard

> **สรุปโดยย่อ**
> **Route:** `/operation-plan` (index) &nbsp;·&nbsp; **Component:** `operation-dashboard.tsx` &nbsp;·&nbsp; **Data:** `GET /api/{bu_code}/dashboard-widgets/operation-plan` &nbsp;·&nbsp; **Tiles:** 10 tile hardcode (5 KPI, 5 chart) ครอบคลุม recipe + equipment &nbsp;·&nbsp; **แก้ไขไม่ได้** — ไม่มี UI add/remove/reorder ไม่มีการปรับแต่งตาม tenant

![Operation Plan dashboard](/screenshots/operation-plan/index.png)

## 1. คืออะไรและใครใช้

Operation Plan Dashboard คือหน้าจอ landing ที่แสดงที่ `/operation-plan` ก่อนที่ผู้ใช้จะเลือก sub-module ([Recipe](/th/inventory/recipe), [Recipe Category](/th/inventory/recipe/category), [Cuisine](/th/inventory/recipe/cuisine), [Equipment](/th/inventory/recipe/equipment), [Equipment Category](/th/inventory/recipe/equipment-category)) มันแสดงชุด tile คงที่ **10 ชิ้น** — KPI card 5 ชิ้น และ chart 5 ชิ้น — สร้างจาก entry `recipe.*` และ `equipment.*` ใน catalog ของ [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) i18n key ที่ตั้งชื่อมันคือ `operationPlan.dashboard` (`title: "Operations Overview"`, `description: "Recipe, cuisine, and equipment status across the operation plan"`)

**นี่ไม่ใช่กลไกเดียวกับ [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) หรือ [reporting-audit/widget](/th/inventory/reporting-audit/widget)** หน้าเหล่านั้นบันทึก `tb_dashboard_bu_widget` (BU-curate, เพิ่ม/ลบได้) และ `tb_dashboard_personal_widget` (ต่อผู้ใช้ เพิ่ม/ลบได้) — ทั้งคู่เป็นตาราง widget จริงที่แก้ไขได้ ให้บริการโดย **micro-data** (Go) หน้าจอนี้ ทั้ง 10 tile เป็น **กลไกที่สาม แยกต่างหาก**: array TypeScript hardcode (`SystemWidgetConfig[]`) ฝังอยู่ใน backend-gateway ไม่มีแถวฐานข้อมูลใดรองรับ tile แต่ละชิ้นเลย ดู §6 สำหรับความแตกต่างระดับโค้ดและการอ้างอิงหน้าก่อนหน้าที่หน้านี้แก้ไข

**ดูแลโดย** Engineering (ต้องแก้โค้ด + deploy เพื่อเพิ่ม/ลบ/จัดเรียง tile — ไม่มีหน้าจอ admin) **อ่านโดย** ผู้ใช้ที่ authenticate แล้วคนใดก็ตามที่โหลด `/operation-plan` ได้ — ไม่พบการเช็ค permission ที่ gate ตัว data endpoint เอง (ดู §4)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู KPI ของ operation-plan | ไปที่ `/operation-plan` | โหลดอัตโนมัติ; ไม่มี filter/date-range control |
| ดูรายละเอียดของ metric | คลิก tile (แสดงผลอย่างเดียว) | tile ไม่ใช่ link — `KpiCard`/`BarCard`/`PieCard` render แบบ read-only; หากต้องการดูข้อมูลจริง ต้องไปที่หน้าจอ sub-module เอง |
| เพิ่ม/ลบ/จัดเรียง tile | **ทำจาก UI ไม่ได้** | ต้องแก้โค้ด `system-widgets.config.ts` (backend-gateway) — ดู §6 |
| ลองใหม่หลัง load error | รีโหลดหน้า | หน้าจอแสดง banner error เดียวสำหรับทั้งชุด tile (`dashboardWidget.loadError`) — ไม่มีการ retry รายชิ้น |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| Dashboard ทั้งหมดแสดง banner error | `GET .../dashboard-widgets/operation-plan` ล้มเหลว (network, auth, หรือ micro-data มีปัญหา) | **ยืนยันแล้ว** — `operation-dashboard.tsx` render banner `role="alert"` เดียว ผูกกับ `isError` |
| Tile หายไปจาก grid เฉย ๆ | `dataset_id` ของมัน resolve ไม่สำเร็จ (`meta`/`data` หาย) | **ยืนยันแล้ว** — `isResolved()` กรอง widget ที่ไม่มีทั้ง `meta` และ `data` ออกก่อน render |
| ข้อความ empty-state ("No widget data") | dataset ที่ตั้งค่าไว้ทั้ง 10 ตัว resolve ไม่สำเร็จ หรือ catalog entry ถูกลบ | **ยืนยันแล้ว** — `hasAny` เช็คกับ list ที่ resolve แล้วหลัง filter/sort |
| Skeleton grid แสดง placeholder card 4 ชิ้นพอดีตอนโหลด | `Array.from({ length: 4 })` hardcode ไว้ใน loading state | **ยืนยันแล้ว** — เป็นเรื่อง cosmetic เท่านั้น; ชุดจริงที่ resolve คือ 10 tile ไม่ใช่ 4 |

## 4. กรณีพิเศษ

- **ไม่พบ permission gate บน data endpoint** `DashboardSystemWidgetsController` (`api/:bu_code/dashboard-widgets`) ถูก guard ด้วย `KeycloakGuard` เท่านั้น (ผู้ใช้ authenticate แล้วคนใดก็ได้) — ไม่พบ decorator แบบ `@RequirePermission` บน route handler ของ `operation-plan` ต่างจาก sidebar entry ของหน้าจอย่อย `/operation-plan/*` ที่ gate ด้วย `operation_plan.view` ตัว `operation_plan.view` เองเป็น **placeholder เฉพาะ frontend** ที่ยืนยันแล้ว (ดู [recipe](/th/inventory/recipe) §4 "RBAC reality check") — ไม่ถูกใช้ที่ใดเพื่อ gate route dashboard นี้หรือ data call ของมัน
- **Tile เป็นของ hardcode ไม่ใช่ข้อมูลที่เก็บไว้** ต่างจากแถว `tb_dashboard_bu_widget`/`tb_dashboard_personal_widget` — ไม่มีอะไรเกี่ยวกับการเลือก tile, ลำดับ, หรือ title ที่อยู่ใน tenant database เลย ทั้งหมดของ config ของหน้าจอนี้คือ array `OPERATION_PLAN_WIDGETS` ใน `system-widgets.config.ts` (backend-gateway) ทุก business unit เห็น tile ทั้ง 10 ชิ้นในลำดับเดียวกันเป๊ะ
- **Layout จัดกลุ่มตาม widget type ไม่ใช่ตาม `order_index` ของ config เอง** Frontend จัดกลุ่ม widget ที่ resolve แล้วเป็น 4 section ที่ตั้งชื่อไว้ (KPI, Trends, Comparison, Distribution) แล้วเรียง *ภายใน* แต่ละ section ตาม `order_index` — ไม่ได้ render grid แบนเดียวตามลำดับ `order_index` แบบที่ component `DashboardWidgetGrid` ทั่วไป (ที่ [vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) ใช้) ทำ ดู §6 สำหรับความต่างระดับโค้ดระหว่าง dashboard ทั้งสอง
- **`equipment.by-category` เป็น tile รูปวงกลม (pie) เพียงชิ้นเดียวในชุดนี้** (categorical shape) — ที่เหลือเป็น `kpi` (scalar/scalar_delta) หรือ `bar` (categorical/ranked render เป็น bar) ไม่มี tile line/area/time-series เลย แม้ `recipe.added-daily` (dataset รูปแบบ `time_series`) จะมีอยู่ใน catalog ก็ตาม — มันไม่ใช่หนึ่งใน 10 tile ที่ตั้งค่าไว้สำหรับ dashboard นี้
- **Cache** query ของ widget list ใช้ `CACHE_DYNAMIC` (`useOperationPlanWidgets` → `useDashboardWidgets("operation-plan")`) tier เดียวกับ dashboard module อื่นทุกตัว

---

## 5. Tiles (Dev)

Source: `apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts`, `OPERATION_PLAN_WIDGETS`

| # | `dataset_id` | Type | ชื่อ (ไทย ตามที่เขียนในโค้ด) | Section ที่ render |
|---|---|---|---|---|
| 0 | `recipe.total-active` | kpi | Recipe active | Metrics |
| 1 | `recipe.added-7d` | kpi | Recipe เพิ่มใน 7 วัน | Metrics |
| 2 | `recipe.average-ingredients` | kpi | Avg ingredients / recipe | Metrics |
| 3 | `recipe.cuisines-total` | kpi | Cuisine types | Metrics |
| 4 | `equipment.total-active` | kpi | Equipment active | Metrics |
| 5 | `recipe.by-cuisine-top` | bar | Top 10 cuisine ตามจำนวน recipe | Comparison |
| 6 | `recipe.by-category-top` | bar | Top 10 recipe category | Comparison |
| 7 | `equipment.by-category` | pie | Equipment แยกตามประเภท | Distribution |
| 8 | `recipe.most-complex` | bar | Recipe ที่ใช้ ingredients มากสุด | Comparison |
| 9 | `recipe.added-daily` | line | Recipe สร้างต่อวัน (30d) | Trends |

ชื่อ (title) เป็น string ที่ hardcode ไว้บน config entry (เป็นภาษาไทยใน source ปัจจุบัน) — **ไม่ได้** ผ่าน `use-intl`; frontend render string ที่ gateway ส่งกลับมาสำหรับ `title` ตรง ๆ โดย fallback ไปที่ `meta.name` ของ dataset เองก็ต่อเมื่อ config entry ไม่มี `title` (ไม่มีตัวไหนใน 10 ตัวนี้ที่ขาด) `dataset_id` แต่ละตัว resolve กับ query ที่ลงทะเบียนไว้ใน `micro-data/service/dashboard/registry.go` — ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) §5 สำหรับสัญญา catalog เต็ม

## 6. หน้านี้ต่างจากระบบ widget ของ BU/personal อย่างไร

| | หน้าจอนี้ (`operation-plan`) | [reporting-audit/widget](/th/inventory/reporting-audit/widget) |
|---|---|---|
| Backend route | `GET api/:bu_code/dashboard-widgets/operation-plan` — endpoint คงที่เฉพาะ module บน `DashboardSystemWidgetsController` | `GET api/:bu_code/dashboard-widgets/bu` (BU) หรือ `api/:bu_code/dashboard-widgets/me` (personal) — ให้บริการโดย `DashboardBuWidgetsController` / `DashboardPersonalWidgetsController` |
| Storage | ไม่มี — array hardcode ใน source ของ gateway (`system-widgets.config.ts`) | `tb_dashboard_bu_widget` / `tb_dashboard_personal_widget` (แถว tenant DB) |
| เพิ่ม / ลบ / จัดเรียง | ต้องแก้โค้ด + deploy เท่านั้น | CRUD จริง (`POST`/`PATCH`/`DELETE`) — BU widget จาก landing dashboard ของแต่ละ module เอง, personal widget จาก `/dashboard` |
| Frontend component | `operation-dashboard.tsx` — layout เฉพาะตัว, 4 section ตั้งชื่อ (Metrics/Trends/Comparison/Distribution) | `DashboardWidgetGrid` (component ที่ใช้ร่วมกัน ใช้โดย [vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) ด้วย) — grid แบนเดียว เรียงตาม render-group ของ widget-type แล้วตาม `order_index` |

**การแก้ไขต่อการอ้างอิงก่อนหน้า:** [reporting-audit/widget](/th/inventory/reporting-audit/widget) §1 อ้าง `procurement-dashboard.tsx → useProcurementWidgets → GET api/:bu_code/dashboard-widgets/bu` เป็นตัวอย่างผู้บริโภค BU-widget การอ่าน `system-widgets.controller.ts` โดยตรงแสดงว่า route จริงที่ `useProcurementWidgets`/`useOperationPlanWidgets`/`useVendorWidgets`/`useInventoryWidgets`/`useProductWidgets`/`useConfigWidgets` เรียกคือ `api/:bu_code/dashboard-widgets/{module}` บน `DashboardSystemWidgetsController` (กลไกของหน้านี้ ไม่ใช่ของ BU-widget) — route `/bu` และ `/me` อยู่บน controller แยกต่างหากและไม่เคยถูกเรียกโดย per-module dashboard component ตัวใดเลย หน้านี้และ [vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) เป็นหน้า wiki สองหน้าแรกที่ตาม trace ความต่างนี้ถึง source แนะนำให้แก้ไข `reporting-audit/widget.md` เองในรอบถัดไป แต่อยู่นอกขอบเขตของงานนี้

## 7. ความเชื่อมโยงข้ามโมดูล

- [recipe](/th/inventory/recipe) — module แม่; §4 "RBAC reality check" บันทึก permission placeholder `operation_plan.view` ที่ route ของ dashboard นี้ก็ไม่มี gate จริงเช่นกัน
- [recipe/category](/th/inventory/recipe/category), [recipe/cuisine](/th/inventory/recipe/cuisine), [recipe/equipment](/th/inventory/recipe/equipment), [recipe/equipment-category](/th/inventory/recipe/equipment-category) — sub-module ที่ dashboard นี้สรุปแต่ไม่ได้ link ไป
- [vendor-pricelist/vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) — module dashboard คู่กันสำหรับ Vendor Management; กลไก backend เดียวกัน frontend rendering component ต่างกัน
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — catalog ที่ลงทะเบียนในโค้ดที่ `dataset_id` ทุกตัวในหน้านี้อ้างอิง
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — ระบบ widget BU/personal จริงที่แก้ไขได้ ที่หน้าจอนี้มักถูกเข้าใจผิดว่าเป็นเรื่องเดียวกัน; ดู §6 สำหรับการแก้ไข

## 8. แหล่งอ้างอิง

- **Frontend route:** `../carmen-inventory-frontend-react/routes/operation-plan/operation-plan.route.tsx` → `operation-dashboard.tsx`
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-dashboard-widgets.ts` — `useOperationPlanWidgets()`
- **Frontend shared cards:** `../carmen-inventory-frontend-react/components/dashboard-widget/dashboard-widget-grid.tsx` — `KpiCard`, `BarCard`, `PieCard`, `LineCard`, `WidgetSkeleton` (ใช้ซ้ำโดย layout เฉพาะของหน้าจอนี้ ไม่ใช่ wrapper `DashboardWidgetGrid` ที่ใช้ร่วมกัน)
- **Gateway controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.controller.ts` — `DashboardSystemWidgetsController`, `@Get('operation-plan')`
- **Gateway config:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.config.ts` — `OPERATION_PLAN_WIDGETS`, `getSystemWidgets()`
- **Dataset registry:** `../micro-data/service/dashboard/registry.go` — entry `recipe.*` (บรรทัด ~150-165), `equipment.*` (บรรทัด ~166-169)
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `operationPlan.dashboard.title`/`.description`, `dashboardWidget.section*`
