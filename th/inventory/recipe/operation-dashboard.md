---
title: Operation Plan Dashboard
description: หน้าจอ /operation-plan: 10 tile KPI/chart ของ recipe และ equipment จากตาราง widget-template ของ Backstage บวก section widget ของ BU; ไม่ใช่ board ที่ผู้ใช้ปรับแต่งได้
published: true
date: '2026-10-27T15:00:00.000Z'
tags: recipe, operation-plan, dashboard, widget, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:00:00.000Z
---

# Operation Plan Dashboard

> **สรุปโดยย่อ**
> **Route:** `/operation-plan` (index) &nbsp;·&nbsp; **Component:** `operation-dashboard.tsx` &nbsp;·&nbsp; **Data:** `GET /api/{bu_code}/dashboard-widgets/operation-plan/config` (config เท่านั้น ตั้งแต่ 2026-09-07) + `GET /api/{bu_code}/datasets/{dataset_id}` แบบ lazy หนึ่งครั้งต่อ tile &nbsp;·&nbsp; **Tiles:** 10 system template (5 KPI, 5 chart) ครอบคลุม recipe + equipment อ่านจากตาราง dashboard-widget template ของ platform (module `operation-plan`) &nbsp;·&nbsp; **tenant แก้ไข system tile ไม่ได้**; มี **section widget ของ BU** แยกต่อท้ายด้านล่าง (ตั้งแต่ 2026-10)

> **ตรวจสอบซ้ำ 2026-10-27 — แหล่งที่มาของ tile เปลี่ยน** ไฟล์ gateway `system-widgets.config.ts` (`OPERATION_PLAN_WIDGETS`) **ถูกลบแล้ว** (commit `3ea25956f`) ตอนนี้ `DashboardSystemWidgetsController` เรียก `SystemWidgetCache.forBu(bu_code, 'operation-plan')` ซึ่งอ่าน system template ที่ active ผ่าน RPC `DashboardTemplates.findActiveSystem` (ฐานข้อมูล backstage, cache 60 วินาที) และซ่อน template ตาม `allow_business_unit` / `deny_business_unit` ของ BU (deny ชนะ; list ว่าง = ไม่จำกัด) แถวทั้งสิบชุดเดียวกันถูก seed โดย `packages/prisma-shared-schema-backstage/prisma/seed.dashboard-widget-template.data.ts` (`seed_key` `system.operation-plan.*`) การติดตั้ง default จึงยังแสดง tile ใน §5 แต่ operator สามารถแก้ไข จัดเรียง เปลี่ยนชื่อ หรือจำกัดตาม BU ได้ใน dashboard-template admin ของ Backstage ชื่อเป็นสองภาษา: แต่ละแถวมี `title` และ `title_i18n` `{ en, th }` ตอนนี้ class controller ถูก guard ด้วย `BuCodePathQueryMatchGuard` (`bu_code` ใน query ต้องตรงกับ path) บนหน้า `operation-dashboard.tsx` render `<BuWidgetSection module="operation-plan">` หลัง system tile (widget ที่ BU curate จาก `tb_dashboard_bu_widget` ซ่อนเมื่อ backend ไม่มีและผู้ใช้เพิ่มไม่ได้) — ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) ในที่ที่ข้อความเดิมด้านล่างบอกว่า tile ถูก hardcode ใน source ของ gateway ให้อ่านว่า "system template ที่ seed ไว้"

> **ตรวจสอบซ้ำ 2026-09-22** สองการเปลี่ยนแปลงตั้งแต่ 2026-07-29: **(1)** หน้าไม่รอ response รวมชุดเดียวอีกต่อไป — `useOperationPlanWidgets()` → `useDashboardWidgetConfigs("operation-plan")` (`hooks/use-dashboard-widgets.ts`) เรียก route ใหม่ `…/dashboard-widgets/operation-plan/config` (`374aad8e5`; gateway คืน config ที่ hardcode ไว้โดยไม่แตะฐานข้อมูล ถ้า 404 จะถอยไปใช้ route รวมชุดเดิม) ด้วย `CACHE_STATIC` และแต่ละ tile เป็น `LazyWidget` ที่ดึง `GET /api/{bu}/datasets/{dataset_id}` เฉพาะเมื่อเลื่อนเข้ามาในสายตา (`db046517`) dataset ที่พังจึงแสดงเป็น error บน **tile นั้น** ไม่ใช่หายไปเงียบ ๆ **(2)** tile วางบน grid 12 คอลัมน์ / แถวสูง 4 rem ที่ใช้ร่วมกันด้วย `gridClasses(widget_type, display)` และสี่ section แบ่งตามชนิดการ render (KPI + gauge · Trends = line/area · Comparison = bar · Distribution = pie) เรียงตาม `order_index` ภายในแต่ละ section

![Operation Plan dashboard](/screenshots/operation-plan/index.png)

## 1. คืออะไรและใครใช้

Operation Plan Dashboard คือหน้าจอ landing ที่แสดงที่ `/operation-plan` ก่อนที่ผู้ใช้จะเลือก sub-module ([Recipe](/th/inventory/recipe), [Recipe Category](/th/inventory/recipe/category), [Cuisine](/th/inventory/recipe/cuisine), [Equipment](/th/inventory/recipe/equipment), [Equipment Category](/th/inventory/recipe/equipment-category)) มันแสดงชุด tile คงที่ **10 ชิ้น** — KPI card 5 ชิ้น และ chart 5 ชิ้น — สร้างจาก entry `recipe.*` และ `equipment.*` ใน catalog ของ [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) i18n key ที่ตั้งชื่อมันคือ `operationPlan.dashboard` (`title: "Operations Overview"`, `description: "Recipe, cuisine, and equipment status across the operation plan"`)

**นี่ไม่ใช่กลไกเดียวกับ [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) หรือ [reporting-audit/widget](/th/inventory/reporting-audit/widget)** หน้าเหล่านั้นบันทึก `tb_dashboard_bu_widget` (BU-curate, เพิ่ม/ลบได้) และ `tb_dashboard_personal_widget` (ต่อผู้ใช้ เพิ่ม/ลบได้) — ทั้งคู่เป็นตาราง widget จริงที่แก้ไขได้ ให้บริการโดย **micro-data** (Go) หน้าจอนี้ ทั้ง 10 tile เป็น **กลไกที่สาม แยกต่างหาก**: widget template ของ *system* (แถวในฐานข้อมูล backstage, cache ใน gateway) — tenant แก้ไขไม่ได้ ต่างจาก widget ของ BU / personal (ณ 2026-10-27; ก่อนหน้านั้นเป็น array TypeScript ที่ hardcode) ดู §6 สำหรับความแตกต่างระดับโค้ดและการอ้างอิงหน้าก่อนหน้าที่หน้านี้แก้ไข

**ดูแลโดย** Engineering / operator ของ platform (system template แก้ใน dashboard-template admin ของ Backstage หรือไฟล์ seed; ไม่มีหน้าจอฝั่ง tenant) **อ่านโดย** ผู้ใช้ที่ authenticate แล้วคนใดก็ตามที่โหลด `/operation-plan` ได้ — ไม่พบการเช็ค permission ที่ gate ตัว data endpoint เอง (ดู §4)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู KPI ของ operation-plan | ไปที่ `/operation-plan` | โหลดอัตโนมัติ; ไม่มี filter/date-range control |
| ดูรายละเอียดของ metric | คลิก tile (แสดงผลอย่างเดียว) | tile ไม่ใช่ link — `KpiCard`/`BarCard`/`PieCard` render แบบ read-only; หากต้องการดูข้อมูลจริง ต้องไปที่หน้าจอ sub-module เอง |
| เพิ่ม/ลบ/จัดเรียง tile | **ทำจาก UI ฝั่ง tenant ไม่ได้** | operator แก้ system template ใน dashboard-template admin ของ Backstage (หรือไฟล์ seed) — ดู §6 |
| ลองใหม่หลัง load error | รีโหลดหน้า | หน้าจอแสดง banner error เดียวสำหรับทั้งชุด tile (`dashboardWidget.loadError`) — ไม่มีการ retry รายชิ้น |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| Dashboard ทั้งหมดแสดง banner error | `GET .../dashboard-widgets/operation-plan` ล้มเหลว (network, auth, หรือ micro-data มีปัญหา) | **ยืนยันแล้ว** — `operation-dashboard.tsx` render banner `role="alert"` เดียว ผูกกับ `isError` |
| Tile ชิ้นเดียวแสดง error / skeleton | `GET /api/{bu}/datasets/{dataset_id}` แบบ lazy ของมันล้มเหลว หรือยังไม่ยิง (tile ยังไม่เข้ามาในสายตา) | **ยืนยันแล้ว (2026-09-22)** — query ต่อ tile ใน `LazyWidget`; grid ที่เหลือไม่กระทบ (แทนที่พฤติกรรม "หายไปเงียบ ๆ" ก่อน 2026-09) |
| ข้อความ empty-state ("No widget data") | route config คืนรายการว่าง (หรือทั้งหมดอยู่ใน `HIDDEN_DATASETS` ซึ่งปัจจุบันว่าง) | **ยืนยันแล้ว** — `hasAny` เช็คกับ list ของ config ไม่ใช่ผลของ dataset |
| Skeleton grid แสดง placeholder card 4 ชิ้นพอดีตอนโหลด | `Array.from({ length: 4 })` hardcode ไว้ใน loading state | **ยืนยันแล้ว** — เป็นเรื่อง cosmetic เท่านั้น; ชุดจริงที่ resolve คือ 10 tile ไม่ใช่ 4 |

## 4. กรณีพิเศษ

- **ไม่มี permission ต่อ key บน data endpoint** `DashboardSystemWidgetsController` (`api/:bu_code/dashboard-widgets`) ถูก guard ด้วย `BuCodePathQueryMatchGuard` + `KeycloakGuard` (ผู้ใช้ที่ authenticate แล้วของ BU คนใดก็ได้) — ไม่พบ decorator แบบ `@RequirePermission` บน route handler ของ `operation-plan` ต่างจาก sidebar entry ของหน้าจอย่อย `/operation-plan/*` ที่ตอนนี้ gate ด้วย key ระดับ resource เช่น `operation_plan.recipe.view` (placeholder `operation_plan.view` เดิมไม่ถูกใช้โดย menu leaf ใดอีกแล้ว — ดู [recipe](/th/inventory/recipe) §4) ตัว route landing ของ dashboard เองไม่มี permission
- **Tile เป็น template ไม่ใช่แถวของ tenant** ต่างจาก `tb_dashboard_bu_widget`/`tb_dashboard_personal_widget` การเลือก tile, ลำดับ และ title อยู่ในตาราง template ของ **backstage** (ไม่ใช่ tenant database) โดย default ทุก business unit เห็น tile ทั้ง 10 ชิ้นในลำดับเดียวกัน; list allow/deny BU บน template เปลี่ยนสิ่งนี้ตาม BU ได้
- **Layout จัดกลุ่มตาม widget type ไม่ใช่ตาม `order_index` ของ config เอง** Frontend จัดกลุ่ม widget เป็น 4 section ที่ตั้งชื่อไว้ (KPI รวม gauge, Trends = line/area, Comparison = bar, Distribution = pie) แล้วเรียง *ภายใน* แต่ละ section ตาม `order_index` วางแต่ละชิ้นบน grid 12 คอลัมน์ที่ใช้ร่วมกันผ่าน `gridClasses(widget_type, display)` — ไม่ได้ render grid แบนเดียวแบบที่ component `DashboardWidgetGrid` ทั่วไป (ที่ [vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) ใช้) ทำ ดู §6
- **`equipment.by-category` เป็น tile รูปวงกลม (pie) เพียงชิ้นเดียวในชุดนี้** (categorical shape) — ที่เหลือเป็น `kpi` (scalar/scalar_delta) หรือ `bar` (categorical/ranked render เป็น bar) ไม่มี tile line/area/time-series เลย แม้ `recipe.added-daily` (dataset รูปแบบ `time_series`) จะมีอยู่ใน catalog ก็ตาม — มันไม่ใช่หนึ่งใน 10 tile ที่ตั้งค่าไว้สำหรับ dashboard นี้
- **Cache** query ของ config ใช้ `CACHE_STATIC` (`useOperationPlanWidgets` → `useDashboardWidgetConfigs("operation-plan")` — gateway cache template 60 วินาที ชุด tile จึงแทบไม่เปลี่ยนภายใน session); query dataset ของแต่ละ tile ใช้ `CACHE_DYNAMIC` (stale 1 นาที)

---

## 5. Tiles (Dev)

Source (2026-10-27): แถว seed ใน `packages/prisma-shared-schema-backstage/prisma/seed.dashboard-widget-template.data.ts` (`module: 'operation-plan'`, `order_index` 0–9); รอบก่อนหน้าอ่าน list เดียวกันจาก `system-widgets.config.ts` ที่ถูกลบแล้ว

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

ชื่อ (title) มาจากแถว template (`title` บวก `title_i18n` `{ en, th }` เช่น "Active recipes" / "Recipe ที่ใช้งาน"); ตารางด้านล่างแสดงคอลัมน์ `title` ของ seed — **ไม่ได้** ผ่าน `use-intl`; frontend render สิ่งที่ gateway ส่งกลับมาเป็นชื่อ (`widget-title.ts` resolve `title_i18n`) โดย fallback ไปที่ `meta.name` ของ dataset เองก็ต่อเมื่อ config entry ไม่มี `title` (ไม่มีตัวไหนใน 10 ตัวนี้ที่ขาด) `dataset_id` แต่ละตัว resolve กับ query ที่ลงทะเบียนไว้ใน `micro-data/service/dashboard/registry.go` — ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) §5 สำหรับสัญญา catalog เต็ม

## 6. หน้านี้ต่างจากระบบ widget ของ BU/personal อย่างไร

| | หน้าจอนี้ (`operation-plan`) | [reporting-audit/widget](/th/inventory/reporting-audit/widget) |
|---|---|---|
| Backend route | `GET api/:bu_code/dashboard-widgets/operation-plan/config` (config เท่านั้น; `GET …/operation-plan` แบบรวมชุดยังอยู่เป็น fallback) บน `DashboardSystemWidgetsController` แล้วตามด้วย `GET api/:bu_code/datasets/:dataset_id` ต่อ tile | `GET api/:bu_code/dashboard-widgets/bu` (BU, บน `DashboardBuWidgetsController` ที่แยกต่างหาก — ไม่มีผู้เรียกฝั่ง frontend) หรือ `GET api/me/dashboard-widgets` (personal, บน `DashboardPersonalWidgetsController` ที่แยกต่างหาก — คนละ root path เลย ไม่ได้อยู่ใต้ `:bu_code/dashboard-widgets/`) |
| Storage | แถว template ของ dashboard-widget ใน backstage (system template) cache 60 วินาทีใน gateway | `tb_dashboard_bu_widget` / `tb_dashboard_personal_widget` (แถว tenant DB) |
| เพิ่ม / ลบ / จัดเรียง | operator แก้ template ใน Backstage (ไม่ใช่ tenant) | CRUD จริง (`POST`/`PATCH`/`DELETE`) — BU widget จาก landing dashboard ของแต่ละ module เอง, personal widget จาก `/dashboard` |
| Frontend component | `operation-dashboard.tsx` — layout เฉพาะตัว, 4 section ตั้งชื่อ (Metrics/Trends/Comparison/Distribution) | `DashboardWidgetGrid` (component ที่ใช้ร่วมกัน ใช้โดย [vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) ด้วย) — grid แบนเดียว เรียงตาม render-group ของ widget-type แล้วตาม `order_index` |

**การแก้ไขต่อการอ้างอิงก่อนหน้า (ใส่ลงใน [reporting-audit/widget](/th/inventory/reporting-audit/widget) แล้วเมื่อ 2026-09-22):** หน้านั้นเคยอ้าง `procurement-dashboard.tsx → useProcurementWidgets → GET api/:bu_code/dashboard-widgets/bu` เป็นตัวอย่างผู้บริโภค BU-widget การอ่าน `system-widgets.controller.ts` โดยตรงแสดงว่า route จริงที่ `useProcurementWidgets`/`useOperationPlanWidgets`/`useVendorWidgets`/`useInventoryWidgets`/`useProductWidgets`/`useConfigWidgets` เรียกคือ `api/:bu_code/dashboard-widgets/{module}` บน `DashboardSystemWidgetsController` (กลไกของหน้านี้ ไม่ใช่ของ BU-widget) — route `/bu` จริงของ `DashboardBuWidgetsController` อยู่บน controller ที่แยกต่างหากจริง ๆ และ path การดึง personal widget ที่ frontend เรียกจริง (`api/me/dashboard-widgets` ผ่าน `hooks/use-my-dashboard-widgets.ts` → `MY_DASHBOARD_WIDGETS` ซึ่งบันทึกไว้ถูกต้องแล้วที่ [reporting-audit/widget](/th/inventory/reporting-audit/widget) §1.1) ให้บริการโดย `DashboardPersonalWidgetsController` ที่ root แยกต่างหากนั้น — ไม่ได้อยู่ใต้ `:bu_code/dashboard-widgets/` เลย ตัว `DashboardSystemWidgetsController` เองก็มี handler `@Get('me')` ของตัวเอง (`api/:bu_code/dashboard-widgets/me`) ที่ประกอบ personal-widget list เดียวกันพร้อม live dataset values แต่ไม่พบผู้เรียก frontend ใดสำหรับ composite route ตัวนี้โดยเฉพาะ (`useDashboardWidgets()` ใน `use-dashboard-widgets.ts` ถูกเรียกด้วย `procurement`/`inventory`/`product`/`config`/`vendor-management`/`operation-plan` เท่านั้น ไม่เคยเรียกด้วย `me`) หน้านี้และ [vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) เป็นหน้า wiki สองหน้าแรกที่ตาม trace ความต่างนี้ถึง source แนะนำให้แก้ไข `reporting-audit/widget.md` เองในรอบถัดไป แต่อยู่นอกขอบเขตของงานนี้

## 7. ความเชื่อมโยงข้ามโมดูล

- [recipe](/th/inventory/recipe) — module แม่; §4 "RBAC reality check" บันทึก key permission `operation_plan.*` ปัจจุบัน (route ของ dashboard เองไม่มี)
- [recipe/category](/th/inventory/recipe/category), [recipe/cuisine](/th/inventory/recipe/cuisine), [recipe/equipment](/th/inventory/recipe/equipment), [recipe/equipment-category](/th/inventory/recipe/equipment-category) — sub-module ที่ dashboard นี้สรุปแต่ไม่ได้ link ไป
- [vendor-pricelist/vendor-dashboard](/th/inventory/vendor-pricelist/vendor-dashboard) — module dashboard คู่กันสำหรับ Vendor Management; กลไก backend เดียวกัน frontend rendering component ต่างกัน
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — catalog ที่ลงทะเบียนในโค้ดที่ `dataset_id` ทุกตัวในหน้านี้อ้างอิง
- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — ระบบ widget BU/personal จริงที่แก้ไขได้ ที่หน้าจอนี้มักถูกเข้าใจผิดว่าเป็นเรื่องเดียวกัน; ดู §6 สำหรับการแก้ไข

## 8. แหล่งอ้างอิง

- **Frontend route:** `../carmen-frontend/routes/operation-plan/operation-plan.route.tsx` → `operation-dashboard.tsx`
- **Frontend hook:** `../carmen-frontend/hooks/use-dashboard-widgets.ts` — `useOperationPlanWidgets()` → `useDashboardWidgetConfigs("operation-plan")`; `dashboardDatasetDataQueryOptions()` ต่อ tile ใน `hooks/use-dashboard-dataset.ts`
- **Frontend shared cards:** `../carmen-frontend/components/dashboard-widget/dashboard-widget-grid.tsx` — `LazyWidget`, `KpiCard`, `BarCard`, `PieCard`, `LineCard`, `WidgetSkeleton` (ใช้ซ้ำโดย layout เฉพาะของหน้าจอนี้ ไม่ใช่ wrapper `DashboardWidgetGrid` ที่ใช้ร่วมกัน); `widget-display.ts` — `gridClasses()`
- **Gateway controller:** `../carmen-turborepo-backend/apps/backend-gateway/src/application/dashboard-widgets/system-widgets.controller.ts` — `DashboardSystemWidgetsController`, `@Get(':module/config')` (2026-09-07) และ `@Get('operation-plan')` แบบรวมชุด Bruno: `_uncategorized/dashboard-widgets/GET-module-config-dashboard-widgets.bru`, `GET-operation-plan-dashboard-widgets.bru`
- **Gateway template cache:** `../carmen-turborepo-backend/apps/backend-gateway/src/application/dashboard-widgets/system-widget-cache.service.ts` — `SystemWidgetCache.forBu()`; `system-widgets.config.ts` (`OPERATION_PLAN_WIDGETS`) เดิมถูกลบใน `3ea25956f`
- **Dataset registry:** `../micro-data/service/dashboard/registry.go` — entry `recipe.*` (บรรทัด ~150-165), `equipment.*` (บรรทัด ~166-169)
- **Translations:** `../carmen-frontend/messages/en.json` — `operationPlan.dashboard.title`/`.description`, `dashboardWidget.section*`
