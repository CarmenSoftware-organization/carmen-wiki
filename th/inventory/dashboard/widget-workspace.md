---
title: Widget Workspace แดชบอร์ด (Widget Workspace Dashboard)
description: หน้า /dashboard ที่ live — workspace 12 คอลัมน์แบบ drag-and-drop ส่วนตัว ที่ผู้ใช้แต่ละคนปักหมุด widget ที่ขับเคลื่อนด้วย dataset (KPI, gauge, pie, bar, line, area, table) และ card pipeline สถานะ จาก catalog ของ micro-data
published: true
date: 2026-09-23T10:06:26.000Z
tags: dashboard, widget-workspace, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget Workspace แดชบอร์ด (Widget Workspace Dashboard)

> **At a Glance**
> **Route:** `/dashboard` &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **Live** — ขับเคลื่อนด้วย API จริง; เนื้อหา dataset ขึ้นอยู่กับ dataset registry ของ micro-data &nbsp;·&nbsp; **ขอบเขต:** ส่วนบุคคล — layout widget ที่ user แต่ละคนบันทึกไว้ ต่อ business unit &nbsp;·&nbsp; **License feature:** `dashboard.widget` (`constant/module-list.ts`; license catalog `app:dashboard-widgets`)

![Widget Workspace แดชบอร์ด (Widget Workspace Dashboard) screen](/screenshots/dashboard/widget-workspace.png)

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

ตรวจสอบซ้ำกับ `carmen-inventory-frontend-react`, `carmen-turborepo-backend-v2` และ `micro-data` ที่ HEAD ตั้งแต่รอบ 2026-07 หน้านี้เพิ่มฟีเจอร์สี่อย่าง live ทั้งหมด: **(1)** การสลับ render ต่อ widget (`widget_type` บน `PATCH` ซึ่ง micro-data validate กับ shape ของ dataset, 2026-09-07 `74e3c795`), **(2)** card แบบ gauge บวก **กริด 12 คอลัมน์พร้อมขนาดต่อ widget** เก็บในคอลัมน์ JSONB ใหม่ `display` (2026-09-07 `493c78f0`; tenant migration `20260907143700_add_dashboard_widget_display`, micro-data migration `130_dash_widget_display`), **(3)** lazy loading ต่อ widget — แต่ละ card fetch ค่าของตัวเองเมื่อ scroll เข้ามาในสายตาเท่านั้น (`db046517`) และ **(4)** **dialog parameter/display** ของ widget บวก **card status-group** แบบเต็มความกว้าง (`f72f951c`) แก้ไขหนึ่งจุดจากเวอร์ชันก่อนของหน้านี้: backend ที่ให้บริการหน้านี้คือ **micro-data (Go, HTTP)** ไม่ใช่ `micro-cluster` ผ่าน TCP — ดู §5

## 1. คืออะไรและสำหรับใคร

Widget Workspace คือ **หน้าเดียวเท่านั้นบน route `/dashboard`** — ไม่มีชุดหน้าย่อยแบบมีชื่อของโดเมนต่างๆ อยู่เบื้องหลังมันแต่อย่างใด (เอกสารฉบับก่อนหน้าของ wiki นี้เคยอ้างว่ามัน "แทนที่" หน้า mock 6 หน้าที่ `/dashboard/pr`, `/dashboard/po` ฯลฯ — หน้าเหล่านั้นไม่เคยมีอยู่จริงในฐานะ route เลย ดูหน้าพี่น้อง [dashboard/main](/th/inventory/dashboard/main), [pr](/th/inventory/dashboard/pr) ฯลฯ ซึ่งแต่ละหน้าถูก flag ว่าเป็นข้อมูลเชิงประวัติศาสตร์เท่านั้น) หน้านี้ render กริด widget แบบ drag-and-drop ส่วนตัว โดยแต่ละ widget ผูกกับ dataset จาก catalog ของ micro-data

> **หมายเหตุเรื่องชื่อ (แก้ไขเมื่อ 2026-07-16, แก้ไขการระบุ backend เมื่อ 2026-09-22):** ตาราง backend จริงคือ `tb_dashboard_personal_widget` (ข้อมูลของหน้านี้ — tenant schema, `packages/prisma-shared-schema-tenant/prisma/schema.prisma` `model tb_dashboard_personal_widget`: `dataset_id`, `widget_type`, `title`, `order_index`, `params`, `display`, scope ด้วย `user_id`) และตารางพี่น้อง `tb_dashboard_bu_widget` (scope ระดับ BU; CRUD มีใน backend แต่**ไม่มีผู้เรียกฝั่ง frontend** — ดู [reporting-audit/widget](/th/inventory/reporting-audit/widget)) ทั้งสองตารางถูกอ่านและเขียนโดย Go service **micro-data** (`micro-data/controller/dashboard_controller.go`, `/api/dashboard/personal-widgets*`); `DashboardPersonalWidgetsService` ของ NestJS gateway เป็น HTTP proxy บางๆ ที่ตอนนี้ต้องแนบ `x-internal-token` ที่แชร์กัน (`INTERNAL_RPC_SECRET`) ทุกครั้งที่เรียก — micro-data guard ทุก route ยกเว้น `/health`, `/` และ Swagger ด้วย `GinInternalAuth` (`micro-data/routes/routes.go`; gateway fix `c94a625ed`, 2026-09-21 — ถ้าไม่มี header ทั้ง dashboard จะตอบ 401) หมายเหตุฉบับก่อนหน้าอ้างว่าตารางอีกสี่ตารางเป็นของจริง — **ทั้งสี่ตารางไม่มีอยู่แล้วหรือไม่เคยมีอยู่จริง**: `tb_widget_dashboard`, `tb_widget_dashboard_item` และ `tb_widget_default_layout` ไม่ปรากฏใน Prisma schema ใดๆ หรือใน micro-data/micro-report เลย; `tb_widget_workspace` เคยมีอยู่ช่วงสั้นๆ (migration `20260512180928_widget_system_replace_dashboard`) และถูก drop โดย `20260521040013_remove_widget_system`

**Layout (`routes/dashboard/dashboard-component.tsx`, `sortable-widget-item.tsx`):**
- Header ทักทาย (ตามช่วงเวลาของวัน + ชื่อเต็มของผู้ใช้) render จาก user profile
- Section "Saved Widgets" พร้อมจำนวน card ที่ render ได้แบบ live และ picker "+ Add widget" (`LookupDataset`)
- **Card status-group** (ถ้ามี) render ก่อน แบบเต็มความกว้าง นอกกริด drag — ดู §1.2
- กริด widget เป็น CSS grid **12 คอลัมน์บน `lg`, 6 บน `md`, 1 บน mobile** โดยแถวสูงคงที่ **4 rem** (`auto-rows-[4rem]`) แต่ละ card กิน `display.width` คอลัมน์ × `display.height` แถว (`components/dashboard-widget/widget-display.ts` `gridClasses()`); บน `md` ความกว้างถูกหารครึ่ง card เรียงตาม `order_index`
- แต่ละ card ลาก (drag) ได้ผ่าน `@dnd-kit/core` (activation distance 6 px) การตรวจจับการชนใช้ `pointerWithin` โดยมี `closestCorners` เป็น fallback (`bc38a34c`) เพื่อให้ card ขนาดไม่เท่ากันลงตรงที่ pointer อยู่; การ drop เรียง list ใหม่และ PATCH อัปเดต `order_index` แบบ optimistic (`(index + 1) * 10`)
- ข้อมูลของแต่ละ card ถูก fetch **เมื่อ card scroll เข้ามาในสายตาเท่านั้น** (`useInViewport` → `onVisible`) หนึ่ง query ต่อ widget (`useQueries`)
- ปุ่มควบคุมเมื่อ hover ต่อ card: drag handle · **dropdown ประเภทกราฟ** (เฉพาะเมื่อมี render ให้เลือกมากกว่าหนึ่ง) · **gear** (เปิด dialog param/display; แสดงเสมอเมื่อ dataset ยังอยู่ใน catalog) · delete
- Empty state: placeholder ตกแต่งพร้อม chip hints (KPI / Pie / Bar)

### 1.1 Shape ของ widget และประเภทการ render

Dataset เป็นเจ้าของ **shape** (ชนิดข้อมูล); **render** (`widget_type`) เป็นตัวเลือกระดับ widget ที่ผู้ใช้เปลี่ยนได้ micro-data ประกาศชุดที่เข้ากันได้ต่อ dataset เป็น `supported_renders` (`micro-data/service/dashboard/dashboard.go` `SupportedRenders()`) และ frontend intersect กับ card ที่วาดได้จริง (`components/dashboard-widget/render-support.ts` `RENDERERS`):

| Shape (dataset) | `supported_renders` ฝั่ง backend | Card ฝั่ง frontend | ค่าเริ่มต้นตอนเพิ่ม |
|---|---|---|---|
| `scalar`, `scalar_delta` | `kpi`, `gauge` | `kpi`, `gauge` | `kpi` |
| `time_series` | `line`, `area`, `bar`, `sparkline` | `line`, `area`, `bar` | `line` |
| `categorical` | `bar`, `pie`, `table` | `pie`, `bar`, `table` | `pie` |
| `ranked` | `bar`, `table` | `pie`, `bar`, `table` | `bar` |
| `table` | `table` | `table` | `table` |
| `matrix` | `heatmap`, `table` | — (ยังไม่มี converter) | เลือกไม่ได้ |

Picker (`SUPPORTED_SHAPES` ใน `routes/dashboard/widget-shape.ts`) เสนอทั้งหก shape ที่ไม่ใช่ matrix `enum_dashboard_widget_type` ยังมี 9 ค่า (`kpi`/`line`/`area`/`bar`/`pie`/`heatmap`/`gauge`/`table`/`sparkline`); `sparkline` และ `heatmap` ไม่มี card ใน frontend การสลับ render เป็น optimistic ใน cache และ `PATCH` `{ widget_type }`; micro-data ตอบ **400** เมื่อ shape นั้นวาดแบบนั้นไม่ได้ (`micro-data/service/widget_service.go` `validateRender()` — เช่น pie ของ scalar)

### 1.2 Card status-group

Card status-group คือ **การ encode เฉพาะฝั่ง frontend** ที่เก็บเป็น row personal-widget ธรรมดา (`routes/dashboard/status-group.ts`): `dataset_id = "group@document.{pr|po|sr}-count"`, `params.statuses` (list คั่นด้วย comma), `params.time_range` (`@today` / `@3days` / `@7days` / `@1month`) และ `params.owner_visibility` (`@everyone` / `@current_user`) picker แสดงเป็นรายการเพิ่มหกรายการ ("PR/PO/SR summary (status pipeline)" × everyone/mine) micro-data ไม่เคยรัน id `group@` — card เองเรียก `POST /api/{bu}/dashboard-lab/datasets/document.{doc}-by-status` ด้วย params เหล่านั้นแล้ววางจำนวนเป็น pipeline ของ tile สถานะ (อ่านอย่างเดียว — tile ไม่มี navigation handler ที่ HEAD) ชุดสถานะเริ่มต้น: PR `draft, in_progress, approved, completed`; PO `draft, in_progress, approved, sent_or_print, completed` (enum PO เปลี่ยน 2026-09-14); SR `draft, in_progress, completed` card แบบ group ไม่ได้อยู่ในกริด drag

### 1.3 Parameter และการตั้งค่า display

Dataset ที่ประกาศ `params[]` (เฉพาะ endpoint catalog ของ `dashboard-lab` ที่คืน descriptor: `name`, `label`, `type` `text|int`, `required`, `default`, `options`) จะเปิด `WidgetConfigDialog` ก่อนสร้าง widget; dataset ที่มี parameter ปักหมุดได้มากกว่าหนึ่งครั้ง (เช่น trend 30 วันและ 365 วัน) dialog เดียวกันแก้ไขการตั้งค่า **display** ของทุก widget: ขนาด (`width × height` จาก list ต่อประเภท — `widget-display.ts` `SIZE_OPTIONS`), `decimals` (0–4) และสำหรับ gauge `min`, `max` และ `thresholds[0] {value, color}` หนึ่งค่า ค่าเริ่มต้นเมื่อไม่ตั้ง: `kpi` 3×2, `gauge` 3×3, `pie`/`bar`/`line`/`area` 6×3, `table` 12×4; ขนาดที่ต่ำกว่าขั้นต่ำของประเภทถูก clamp ตอน render (เกี่ยวข้องหลังสลับ render) `display` เก็บแบบทึบ — micro-data ตรวจแค่ว่าเป็น JSON object ≤ 8 KB (`maxDisplayBytes`) ดังนั้น frontend เพิ่ม key ได้โดยไม่ต้อง release backend (ข้อความ swagger ของ gateway ยังอธิบาย shape เก่า `width: 1|2|4, height: "sm"|"md"|"lg"` — `WidgetDisplay` ใน `types/dashboard-widget.ts` ของ frontend คือ authority)

**กลุ่มผู้ใช้**

- **ผู้ใช้ที่เข้าระบบทุกคน** — ทุก operator สร้าง workspace ของตัวเองต่อ business unit ไม่มี layout ตายตัว workspace เริ่มว่างเปล่าและเติบโตเมื่อผู้ใช้ปักหมุด widget
- **นักพัฒนา** — compositing layer คือ `dashboard-component.tsx`; การ render card คือ `SortableWidgetItem` → `WidgetRouter` (`components/dashboard-widget/dashboard-widget-grid.tsx`)

## 2. Tile และการ Drill-down

Widget Workspace ไม่มีชุด tile ตายตัว — กริดเป็น dynamic ทั้งหมดและเป็นส่วนตัวของผู้ใช้แต่ละคน:

| Widget Card | แหล่งข้อมูล | เพิ่มผ่าน |
|---|---|---|
| Dataset ที่ปักหมุดใดก็ได้ (6 shape) | `GET /api/{bu}/dashboard-lab/widgets/{widget_id}/data?scope=personal` — micro-data โหลด `dataset_id` + `params` ที่เก็บไว้ของ widget และคืน `{ meta, data }` | picker "+ Add widget" (+ dialog param เมื่อ dataset มี params) |
| Card status-group | `POST /api/{bu}/dashboard-lab/datasets/document.{doc}-by-status` พร้อม `{ params: { time_range, owner_visibility } }` | picker "+ Add widget" → "PR/PO/SR summary (status pipeline)" |
| Dataset shape `table` (เช่น `document.pr-table`) | Row มีคอลัมน์ `id` ที่ซ่อนอยู่ (`TableColumn.type = "id"`, micro-data `dbfde10`) ทำให้คลิก row เปิดเอกสารได้ (`3bd0b68f`) | picker |

สีของ tile ตาม prefix ของ dataset id (`inventory.*` → Inventory Management ที่เหลือ Procurement) ผ่าน `inferModuleName` / `inferSubTile` ใน `widget-shape.ts`

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไมหน้าแสดง greeting แทนที่จะเป็น tile? | Workspace โหลดรายการ widget ที่บันทึกไว้ของผู้ใช้ — ถ้าว่างจะแสดง empty-state เพิ่ม widget อย่างน้อยหนึ่งรายการผ่าน picker "+ Add widget" |
| dataset ที่ใช้ได้มาจากไหน? | `LookupDataset` query `GET /api/{bu}/dashboard-lab/datasets` (`hooks/use-dashboard-dataset.ts`, `CACHE_STATIC`) — registry ที่ code-registered ใน `micro-data/service/dashboard/registry.go` ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) |
| ทำไมฉันเพิ่ม dataset เดิมได้สองครั้ง? | เฉพาะ dataset ที่**มี** parameter เท่านั้นที่ปักหมุดได้มากกว่าหนึ่งครั้ง; dataset ไม่มี parameter ที่ปักหมุดแล้วถูกยกเว้นจาก picker (`excludeIds`) |
| ทำไมปุ่มประเภทกราฟหายไปบน card? | มี render ให้เลือกแค่ตัวเดียวสำหรับ shape นั้นหลัง intersect `supported_renders` กับ card ฝั่ง frontend (เช่น `table`) |
| ทำไมสลับเป็น gauge/pie แล้วล้มเหลว? | micro-data ปฏิเสธ render สำหรับ shape ของ dataset นั้น (400, `validateRender`); list ถูก fetch ใหม่และ card กลับเป็นเดิม |
| ฉันสามารถ reset layout ไปยังค่าเริ่มต้นได้ไหม? | ยังไม่เปิดให้ใช้ใน UI ไม่มีตาราง default-layout (`tb_dashboard_personal_widget` ไม่มีแนวคิด seed — กริดของผู้ใช้แต่ละคนเริ่มต้นว่างเปล่า) |
| ทำไม drag-and-drop บางครั้ง revert? | การเรียงใหม่เป็นแบบ optimistic — TanStack Query cache อัปเดตทันที จากนั้น PATCH หนึ่งครั้งต่อ widget ที่ย้าย ถ้า PATCH ล้มเหลวจะแสดง toast error; cache ไม่ revert อัตโนมัติสำหรับการเรียงใหม่ (การสลับประเภทและการเปลี่ยน time-range ของ group จะ invalidate เมื่อ error) |
| ทำไม widget ที่ฉันปักหมุดใน BU อื่นไม่แสดงที่นี่? | Widget เก็บใน tenant schema ของ BU และ dataset resolve ต่อ BU; widget ที่ dataset 404 ใน BU ปัจจุบันถูกตัดออกจากกริดเงียบๆ (filter `renderable`) |
| `order_index` เก็บที่ไหน? | บน row `tb_dashboard_personal_widget` เพิ่มทีละ 10 ต่อ slot |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| ทั้งหน้าแสดง load error / dashboard ทุกอัน 401 | การเรียก gateway → micro-data ไม่มี `x-internal-token` (`INTERNAL_RPC_SECRET` ไม่ตรงกันระหว่าง service) | Ops: ทำให้ `INTERNAL_RPC_SECRET` ตรงกันระหว่าง backend-gateway และ micro-data (`c94a625ed`) |
| `GET /api/me/dashboard-widgets?bu_code=` คืน 500 | ฝั่ง backend (ดู `routes/dashboard/CLAUDE.md` ใน repo frontend — reproduce ได้ทั้งตรงและผ่าน proxy) | รายงานทีม backend; หน้า degrade เป็น error banner |
| Workspace โหลดแต่ไม่แสดง widget | ผู้ใช้ยังไม่มี widget ที่บันทึกไว้ | คลิก "+ Add widget" เพื่อปักหมุด dataset อย่างน้อยหนึ่งรายการ |
| picker "+ Add widget" แสดงรายการว่าง | การ fetch catalog ล้มเหลว หรือ dataset ไม่มี parameter ที่รองรับทั้งหมดถูกปักหมุดแล้ว | ตรวจ `GET /api/{bu}/dashboard-lab/datasets`; dataset ที่มี parameter ยังเพิ่มได้ |
| Card ค้างเป็น skeleton | Card ยังไม่เข้า viewport (lazy load) หรือ data query ยัง pending | Scroll ไปหา; ตรวจการเรียก `dashboard-lab/widgets/{id}/data` ต่อ widget |
| Gauge แสดง scale แปลกๆ | ไม่ได้ตั้ง `display.max` — frontend ประมาณค่า max แบบปัดเศษที่สูงกว่าค่าปัจจุบัน (`gaugeRange()`, `isEstimated`) | ตั้ง `max` (และ `min`) ใน dialog gear |
| Save ใน dialog gear ล้มเหลวด้วย 400 | `display` เกิน 8 KB หรือ `params` ไม่ผ่านการ validate param ของ dataset | ลดขนาด display object; ตรวจ `params` กับ descriptor ของ dataset |
| Drag-and-drop ไม่ทำงาน | Pointer เลื่อนน้อยกว่า 6 px ก่อน release (activation constraint) | กดแล้วลากอย่างน้อย 6 px ก่อน release |
| ลำดับ revert หลัง refresh | PATCH request ล้มเหลว | ตรวจ browser console สำหรับ toast error; backend validate `order_index` (ต้อง ≥ 0) |

---

## 5. แหล่งข้อมูล (Dev)

การเรียก personal-widget ทั้งหมดพก `?bu_code=` เพราะ row อยู่ใน tenant schema ของ BU ที่เลือก (`routes/dashboard/use-my-dashboard-widgets.ts`)

- **รายการ widget ที่บันทึกไว้** — `GET /api/me/dashboard-widgets?bu_code=` → `{ items: WidgetConfig[], count }` Hook: `useMyDashboardWidgets` (`CACHE_DYNAMIC`)
- **ค่าของ widget** — `GET /api/{bu}/dashboard-lab/widgets/{widget_id}/data?scope=personal` → `{ meta, data }` (gateway `dashboard-lab.controller.ts` `widgetData`, micro-data `/api/dashboard-lab/widgets/{id}/data`; `scope` default เป็น `bu`) Query options: `myDashboardWidgetDataQueryOptions(buCode, widgetId, enabled)` — `enabled` เปลี่ยนเมื่อ card อยู่ในสายตา Bruno: `_uncategorized/dashboard-lab/GET-widget-data-dashboard-lab.bru`
- **Dataset catalog** — `GET /api/{bu}/dashboard-lab/datasets` → `{ items: DashboardDataset[], count }` พร้อม descriptor `params[]` และ `supported_renders[]` ต่อ dataset (`6dfe58992`) Hook: `useDashboardDatasets` (`CACHE_STATIC`) Bruno: `GET-list-dashboard-lab.bru`
- **Preview / tile ของ group** — `POST /api/{bu}/dashboard-lab/datasets/{dataset_id}` พร้อม `{ params }` → `{ meta, data }` Hook: `useDashboardDatasetPreview` Bruno: `POST-preview-dashboard-lab.bru`
- **สร้าง widget** — `POST /api/me/dashboard-widgets?bu_code=` พร้อม `{ dataset_id, widget_type, title?, order_index?, params?, display? }` → `{ id }` (201) Hook: `useCreateMyDashboardWidget`
- **อัปเดต widget** — `PATCH /api/me/dashboard-widgets/{id}?bu_code=` พร้อมฟิลด์ใดก็ได้ใน `{ title, order_index, params, widget_type, display }` — `params` และ `display` **แทนที่**ทั้ง object (ไม่ merge); `widget_type` ถูก validate กับ shape ของ dataset (400) Hook: `useUpdateMyDashboardWidget` Bruno: `_uncategorized/dashboard-widgets/PATCH-update-dashboard-widgets-dashboard-widgets.bru`
- **เรียงใหม่แบบ bulk** — `PATCH /api/me/dashboard-widgets/reorder?bu_code=` พร้อม `{ items: [{ id, order_index }] }` (atomic, micro-data `PersonalReorder` ใน transaction เดียว) — มีบน gateway และใน Bruno (`PATCH-reorder-dashboard-widgets.bru`) แต่หน้านี้ปัจจุบันยิง `PATCH /{id}` หนึ่งครั้งต่อ widget ที่ย้ายแทน
- **ลบ widget** — `DELETE /api/me/dashboard-widgets/{id}?bu_code=` (soft delete) Hook: `useDeleteMyDashboardWidget`
- **ทางเลือกแบบรวม (หน้านี้ไม่ใช้)** — `GET /api/{bu}/dashboard-widgets/me` คืน list ส่วนตัวเดียวกันพร้อม `{ meta, data }` แนบต่อรายการใน round-trip เดียว (`system-widgets.controller.ts` `@Get('me')`); ไม่มีผู้เรียกฝั่ง frontend
- **ตาราง backend:** `tb_dashboard_personal_widget` (tenant schema) — `id`, `user_id`, `dataset_id` (VarChar 100), `widget_type` (`enum_dashboard_widget_type`), `title`, `order_index` (default 0), `params` (JSONB), `display` (JSONB เพิ่มโดย `20260907143700_add_dashboard_widget_display` / micro-data `130_dash_widget_display.up.sql` ใช้ `IF NOT EXISTS` ทั้งสองฝั่งเพื่อให้ migration ทางไหนรันก่อนก็ได้), `doc_version`, คอลัมน์ audit มาตรฐาน; index `[user_id, deleted_at]` ให้บริการโดย **micro-data** (`controller/dashboard_controller.go` → `service/widget_service.go` → `db/widget_repo.go`) หน้าด่านโดย `DashboardPersonalWidgetsController` ของ `backend-gateway` (`api/me/dashboard-widgets`, `KeycloakGuard` + `x-app-id`) ซึ่ง service `fetch` ไปที่ `http://DATASET_SERVICE_HOST:DATASET_SERVICE_HTTP_PORT/api/dashboard/personal-widgets…` พร้อม header `x-internal-token` ไม่มี default/seed layout

## 6. จังหวะการ Refresh

- **รายการ widget** — `CACHE_DYNAMIC` (TanStack Query, staleTime 1 min) Refetch on focus; ไม่ poll
- **ข้อมูล widget** — หนึ่ง query ต่อ widget, `CACHE_DYNAMIC` เริ่มเมื่อ card เข้า viewport ครั้งแรก; การ save param/display จะ invalidate เฉพาะ data query ของ widget นั้น
- **Catalog** — `CACHE_STATIC` (registry เป็น code เปลี่ยนเฉพาะตอน deploy)
- **เรียงใหม่ / สลับ render / time-range ของ group** — optimistic cache update จากนั้น PATCH; list ถูก invalidate เมื่อ error สำหรับการสลับ render และ time-range ไม่ใช่สำหรับการเรียงใหม่

## 7. โมดูลที่เกี่ยวข้อง

- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — เอกสาร data-model สำหรับตาราง widget (BU + personal), endpoint ของ micro-data, กฎการ validate
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — dataset catalog ที่ code-registered ซึ่งเติมข้อมูลให้ picker
- [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) — approval inbox ที่ live จริง (`/procurement/approval`); preset "mine" ของ status-group คือสิ่งที่ใกล้เคียงที่สุดบน dashboard
- [dashboard/my-pending](/th/inventory/dashboard/my-pending), [dashboard/my-approval](/th/inventory/dashboard/my-approval), [dashboard/pr](/th/inventory/dashboard/pr), [dashboard/main](/th/inventory/dashboard/main) — **ข้อมูลเชิงประวัติศาสตร์เท่านั้น**; ไฟล์ demo ถูกลบเมื่อ 2026-06-27 ไม่เคยถูก route

## 8. แหล่งข้อมูลอ้างอิง

- **Route:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard.route.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx` (กริด, dnd, ชุด lazy visibility, handler add/config/type-switch)
- **Card และ helper:** `routes/dashboard/sortable-widget-item.tsx` (drag handle, dropdown render, gear, delete), `status-group.ts` + `status-group-card.tsx`, `widget-config-dialog.tsx` + `widget-param-fields.tsx` + `widget-display-fields.tsx`, `widget-shape.ts`; `components/dashboard-widget/widget-display.ts` (ขนาดกริด, gauge range, thresholds), `render-support.ts` (shape ↔ render), `dashboard-widget-grid.tsx` (`WidgetRouter`, card, `LazyWidget`)
- **Hooks:** `routes/dashboard/use-my-dashboard-widgets.ts` (ย้ายออกจาก `hooks/` เมื่อ 2026-08-28, `0d9757f3`), `hooks/use-dashboard-dataset.ts`
- **Types:** `types/dashboard-widget.ts` (`WidgetConfig`, `WidgetDisplay`, `DatasetParam`, `TableColumn`, shape guard), `types/dashboard-dataset.ts` (`supported_renders`)
- **API constants:** `constant/api-endpoints.ts` → `MY_DASHBOARD_WIDGETS`, `MY_DASHBOARD_WIDGET_BY_ID`, `DASHBOARD_LAB_DATASETS`, `DASHBOARD_LAB_DATASET_EXEC`, `DASHBOARD_LAB_WIDGET_DATA`
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-personal-widgets.controller.ts` + `.service.ts` (HTTP proxy, `x-internal-token`), `swagger/response.ts` (`WidgetUpdateRequestDto.widget_type`/`display`), `dashboard-lab/dashboard-lab.controller.ts` (`GET widgets/:widget_id/data`)
- **micro-data:** `../micro-data/controller/dashboard_controller.go`, `service/widget_service.go` (`validateRender`, `validateDisplay`, cap 8 KB), `service/dashboard/dashboard.go` (`SupportedRenders`), `service/dashboard/lab.go` (catalog พร้อม `params`/`supported_renders`), `service/dashboard/document.go` (dataset `document.*`, row ตารางพร้อม `id`), `model/dashboard.go`, `migrations/tenant/130_dash_widget_display.up.sql`
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dashboard_personal_widget`, `tb_dashboard_bu_widget`, `enum_dashboard_widget_type`; migration `20260907143700_add_dashboard_widget_display`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/dashboard-lab/*`, `_uncategorized/dashboard-widgets/*` (`GET-me`, `PATCH-reorder`, `PATCH-update`, `POST-create`, `GET-module-config`)
- **Backend design (ประวัติศาสตร์):** `../carmen-turborepo-backend-v2/docs/superpowers/archive/widget/2026-05-12-widget-backend-design.md`
