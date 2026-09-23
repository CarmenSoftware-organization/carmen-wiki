---
title: Widget
description: เอนทิตี widget ของ dashboard — tile ต่อผู้ใช้ (และแบบ BU-scoped ที่มีเฉพาะ backend) ผูกกับแคตตาล็อก dataset ที่ลงทะเบียนในโค้ด ให้บริการโดย micro-data ผ่าน HTTP หลัง gateway; คอลัมน์ display, สลับ render, route config ของโมดูล (2026-09)
published: true
date: 2026-09-23T10:06:26.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

> **At a Glance**
> **เจ้าของ:** ผู้ใช้ปลายทาง (widget ส่วนตัว) &nbsp;·&nbsp; **ตาราง:** `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` (tenant schema) &nbsp;·&nbsp; **ใช้โดย:** หน้าจอ [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) ที่ `/dashboard` (ส่วนตัว) ตาราง BU มี CRUD ครบใน micro-data + gateway แต่ **ไม่มีผู้เรียกจาก frontend**; dashboard หน้าแรกของแต่ละโมดูลใช้ **system widget** แบบ hardcode ไม่ใช่แถว BU &nbsp;·&nbsp; **ให้บริการโดย:** micro-data (Go, HTTP + `x-internal-token`)

![Widget screen](/screenshots/reporting-audit/widget.png)

## สถานะการทำงานจริง (ตรวจสอบซ้ำเมื่อ 2026-09-22)

การแก้ไขและส่วนเพิ่มจากฉบับ 2026-07-22:

1. **BU widget ไม่ได้ขับเคลื่อน dashboard ของโมดูล** `useProcurementWidgets` / `useInventoryWidgets` / `useOperationPlanWidgets` … เรียก `GET /api/{bu}/dashboard-widgets/{module}/config` (ใหม่เมื่อ 2026-09-07, `374aad8e5` — คืนรายการ `system-widgets.config.ts` แบบ hardcode โดยไม่ execute dataset ใดเลย; ถ้า 404 จะ fallback ไปที่ `GET .../dashboard-widgets/{module}` แบบ bundled ที่เก่ากว่า) แล้วแต่ละ tile lazy-load `GET /api/{bu}/datasets/{dataset_id}` เมื่อเลื่อนมาถึง `GET /api/{bu}/dashboard-widgets/bu` และ `DASHBOARD_BU_WIDGET*` มี **การอ้างอิงเป็นศูนย์** ใน `carmen-inventory-frontend-react` ตัวอย่าง `procurement-dashboard.tsx → …/dashboard-widgets/bu` บนหน้าฉบับก่อนผิด (ถูก flag ไว้แล้วโดย [recipe/operation-dashboard](/th/inventory/recipe/operation-dashboard) §6)
2. **คอลัมน์ JSONB `display` ใหม่บนทั้งสองตาราง** (tenant migration `20260907143700_add_dashboard_widget_display`; micro-data `130_dash_widget_display`) — การแสดงผลต่อ widget (grid `width`/`height`, `decimals`, gauge `min`/`max`/`thresholds`) micro-data เก็บแบบ opaque เช็คเพียงว่าเป็น JSON object ≤ 8 KB (`service/widget_service.go` `maxDisplayBytes`)
3. **`widget_type` แก้ไขได้บน `PATCH` แล้ว** และถูก validate กับ shape ของ dataset (`validateRender()` → 400 พร้อมรายการที่อนุญาต); แคตตาล็อกประกาศชุดที่เข้ากันได้เป็น `supported_renders` ต่อ dataset (`SupportedRenders()` ใน `service/dashboard/dashboard.go`)
4. **ทุกการเรียก gateway → micro-data ต้องแนบ `x-internal-token`** (`INTERNAL_RPC_SECRET`); micro-data ป้องกันทุก route ยกเว้น `/health`, `/`, `/swagger` (`6d86790`, แก้ฝั่ง gateway `c94a625ed` 2026-09-21)
5. picker ของ `/dashboard` ตอนนี้มีหก shape (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `table`) — ไม่ใช่สาม — และสร้างด้วย render แรกที่อนุญาตโดย `supported_renders` ∩ card ของ frontend

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี widget คือ **ชั้น tile ของ dashboard** — การวาง feed [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) ที่ลงทะเบียนในโค้ด (`dataset_id`) แสดงเป็นกราฟ (`widget_type`) พร้อมพารามิเตอร์ของ dataset (`params`) และการตั้งค่าการแสดงผล (`display`) บน dashboard ของ business unit ที่แชร์กัน หรือ dashboard ส่วนตัวของผู้ใช้คนเดียว มีตารางอยู่เพียงสองตาราง ทั้งคู่เป็น **tenant-scoped** (tenant schema เองคือ BU ดังนั้นทั้งสองตารางไม่มี `business_unit_id`):

- `tb_dashboard_bu_widget` — widget บน dashboard ที่แชร์กันของ business unit backend ครบ; **ไม่มีหน้าจอใดใช้มันในวันนี้** (ดูหมายเหตุสถานะ)
- `tb_dashboard_personal_widget` — widget บน dashboard ส่วนตัวของผู้ใช้หนึ่งคน scope ด้วย `user_id` ขับเคลื่อน route `/dashboard` — ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) สำหรับ UI แบบเต็ม (เพิ่มพร้อม params, สลับ render, ตั้งค่าขนาด/gauge, drag-and-drop, card แบบ status-group, lazy loading)

ไม่มีตาราง default-layout และไม่มี seeding mechanism — dashboard ส่วนตัวของผู้ใช้ใหม่เริ่มต้นว่างเปล่า ไม่มีฟีเจอร์ saved-query / data-explorer — `dataset_id` อ้างอิงรายการคงที่ใน registry ของ micro-data (`service/dashboard/registry.go`) เสมอ ไม่เคยเป็น query ที่ผู้ใช้เขียนเอง frontend ยังเข้ารหัส **status-group card** เป็นแถวส่วนตัวที่มี `dataset_id = "group@document.{pr|po|sr}-count"` เพิ่มด้วย; micro-data ไม่เคย execute id เหล่านั้น

**ดูแลโดย** ผู้ใช้ปลายทาง (widget ส่วนตัวของตนเอง) endpoint ของ BU widget ไม่มีการตรวจสอบ role นอกเหนือจาก `KeycloakGuard` + `x-app-id` **อ่านโดย** [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) (ส่วนตัว)

### 1.1 Widget CRUD ทำงานที่ไหน (micro-data)

การสร้าง/อ่าน/แก้ไข/ลบ widget ถูก host โดย service **micro-data** (Go) ไม่ใช่ micro-cluster `micro-data/controller/dashboard_controller.go` ลงทะเบียน route ด้านล่าง; `DashboardBuWidgetsService` / `DashboardPersonalWidgetsService` ของ backend-gateway เป็นเพียง HTTP proxy บาง ๆ (`fetch` ไปที่ `DATASET_SERVICE_HOST:DATASET_SERVICE_HTTP_PORT` พร้อม header `x-internal-token`) ไม่มี business logic และไม่มีการเชื่อมต่อ DB ของตัวเอง

| Scope | Endpoint ของ micro-data (proxy โดย backend-gateway) |
|---|---|
| **BU widgets** | `GET/POST /api/dashboard/bu-widgets?bu_code=` · `GET/PATCH/DELETE /api/dashboard/bu-widgets/:id?bu_code=` |
| **Personal widgets** | `GET/POST /api/dashboard/personal-widgets?user_id=&bu_code=` · `GET/PATCH/DELETE /api/dashboard/personal-widgets/:id?user_id=&bu_code=` · `POST /api/dashboard/personal-widgets/reorder?user_id=&bu_code=` (อัปเดต `order_index` แบบกลุ่มด้วย transaction เดียว) |
| **ค่าของ widget** | `GET /api/dashboard-lab/widgets/:id/data?scope=bu|personal` — execute `dataset_id` + `params` ที่เก็บไว้ |
| **แคตตาล็อก / preview** | `GET /api/dashboard-lab/datasets` (พร้อม `params[]`, `supported_renders[]`), `POST /api/dashboard-lab/datasets/:id` (`{ params }`), `GET /api/dashboard/datasets[/:id]` (ไม่มีพารามิเตอร์) |

route ฝั่ง gateway ที่ frontend เรียก: `api/me/dashboard-widgets[...]` (ส่วนตัว, `user_id` จาก auth header, `?bu_code=`), `api/:bu_code/dashboard-lab/*`, `api/:bu_code/datasets/*`, `api/:bu_code/dashboard-widgets/{module}/config` (system widget) `api/:bu_code/dashboard-widgets/bu[...]` (CRUD ของ BU), `api/:bu_code/dashboard-widgets/me` และ `.../all` (ค่าแบบ bundled) มีอยู่แต่ไม่มีผู้เรียกจาก frontend

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม widget ส่วนตัว | `/dashboard` → **+ Add widget** | Picker แสดงหก shape; dataset ที่มี `params[]` จะเปิด dialog ตั้งค่าก่อน และ pin ได้มากกว่าหนึ่งครั้ง |
| เปลี่ยนวิธีวาด widget | `/dashboard` → card → dropdown ประเภทกราฟ | `PATCH { widget_type }`; 400 เมื่อ shape วาดแบบนั้นไม่ได้ |
| ปรับขนาด / ตั้งทศนิยม / ช่วง gauge | `/dashboard` → card → เฟือง | `PATCH { params, display }` — ทั้งสอง object ถูก **แทนที่** ไม่ใช่ merge |
| จัดเรียง widget ส่วนตัว | `/dashboard` → ลาก widget card | อัปเดต `order_index` แบบ optimistic แล้วตามด้วย `PATCH` หนึ่งครั้งต่อ widget ที่ย้าย (route `reorder` แบบ atomic มีอยู่แต่หน้านี้ไม่ได้ใช้) |
| ลบ widget ส่วนตัว | `/dashboard` → card → ถังขยะ | `DELETE .../personal-widgets/:id` — soft delete (`deleted_at`) |
| เพิ่ม/แก้ไข BU widget | **ไม่มี UI** | มีเฉพาะ backend ในวันนี้ (Bruno `_uncategorized/dashboard-widgets/*-bu.bru`) |
| เพิ่ม tile ให้ dashboard หน้าแรกของโมดูล | แก้โค้ดใน `system-widgets.config.ts` | ไม่ใช่แถวใน DB — ดู [recipe/operation-dashboard](/th/inventory/recipe/operation-dashboard) |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ทุกการเรียก dashboard คืน 401 | Gateway ไม่ได้ส่ง `x-internal-token` หรือ `INTERNAL_RPC_SECRET` ต่างกันระหว่าง service | Ops: จัด secret ให้ตรงกัน |
| Widget ส่วนตัวไม่แสดงให้เพื่อนร่วมทีมเห็น | ตามที่ออกแบบไว้ — widget ส่วนตัว scope ด้วย `user_id` เสมอ ไม่เคยแชร์กัน | ยังไม่มี UI ของ BU widget |
| `PATCH` คืน 400 "cannot render a … dataset (allowed: …)" | `widget_type` ไม่อยู่ใน `SupportedRenders(shape)` | เลือก render จาก `supported_renders` ของ dataset |
| `PATCH`/`POST` คืน 400 ที่ `display` | object เกิน 8 KB (`maxDisplayBytes`) หรือไม่ใช่ JSON object | ตัด display object ให้เล็กลง |
| `PATCH` คืน 400 ด้วย body ว่าง | `validateUpdate` ต้องการอย่างน้อยหนึ่งใน `title`, `order_index`, `params`, `widget_type`, `display`; `order_index` ต้อง ≥ 0 | ส่งฟิลด์มา |
| Widget card แสดง error / หายไป | `dataset_id` resolve ไม่ได้ใน BU นี้อีกต่อไป (id ที่เลิกใช้ หรือ dataset ไม่มีใน schema นี้) — 404 บน `widgets/:id/data` | ลบและเพิ่มใหม่; การเช็ค render ปล่อย dataset ที่ไม่รู้จักผ่านเพื่อให้แถวเก่ายังแก้ไขได้ |
| 404 ตอนอัปเดต/ลบ widget | `PersonalFindOne`/`BuFindByID` กรอง `deleted_at IS NULL` — id ถูก soft-delete ไปแล้วหรือไม่เคยมีอยู่ | ดึงรายการ widget ใหม่ |
| การจัดเรียงดูเหมือนล้มเหลวแบบเงียบ ๆ | `PersonalReorder` อัปเดตแถวใน DB transaction เดียว — ถ้าล้มเหลวกลางทาง การจัดเรียงทั้งหมดจะ rollback | ลองใหม่; ตรวจ response สำหรับ id ที่ล้มเหลว |

## 4. กรณีพิเศษ

- **ไม่มี default/seed layout** grid ของ widget ของผู้ใช้ใหม่และ BU ใหม่ทุกคนเริ่มต้นว่างเปล่า
- **ไม่มีแนวคิด workspace/saved-query** `dataset_id` อ้างอิงรายการคงที่ใน registry เสมอ
- **ไม่มี authorization gate สำหรับ BU widget** endpoint ของ BU ต้องการ `bu_code` แต่ไม่มีการตรวจสอบ role เพิ่มเติม — ไม่มีผลในทางปฏิบัติตราบที่ไม่มี UI เรียกใช้
- **`params` เป็น config ของ dataset, `display` เป็นการแสดงผล** `params` (JSONB) เก็บพารามิเตอร์ของ dataset เอง (เช่น `time_range`, `status`, `owner_visibility`) ที่ fix ตอนบันทึก — ไม่มี `user_id`/`bu_code` ซึ่งผู้เรียกใส่มาตอน execute `display` เป็นของ frontend (`types/dashboard-widget.ts` `WidgetDisplay`); swagger ของ gateway ยังอธิบายรูปแบบเก่า `width: 1|2|4, height: "sm"|"md"|"lg"` อยู่
- **Group card อยู่เฉพาะในตารางส่วนตัว** แถว `group@…` ถูก render ทั้งหมดโดย frontend ซึ่งเรียก dataset `document.{doc}-by-status` ที่อยู่เบื้องหลังต่อ card
- **ทั้งสองเส้นทาง migration เพิ่ม `display` ด้วย `IF NOT EXISTS`** ดังนั้น tenant ที่รัน micro-data migration 130 ก่อน Prisma migration (หรือกลับกัน) ก็ไม่มีปัญหา

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_dashboard_bu_widget`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `dataset_id` | `String @db.VarChar(100)` | No | อ้างอิงรายการใน registry [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) (ไม่มี FK — เป็น code registry ไม่ใช่ตาราง) |
| `widget_type` | `enum_dashboard_widget_type` | No | `kpi` / `line` / `area` / `bar` / `pie` / `heatmap` / `gauge` / `table` / `sparkline` |
| `title` | `String? @db.VarChar(255)` | Yes | ชื่อ override ถ้ามี; ถ้าไม่มีใช้ชื่อแสดงผลของ dataset เอง |
| `order_index` | `Int` | No | ค่า default `0` ตำแหน่งใน grid |
| `params` | `Json? @db.JsonB` | Yes | พารามิเตอร์ของ dataset (แทนที่ทั้งก้อนไม่ใช่ merge บน `PATCH`) |
| `display` | `Json? @db.JsonB` | Yes | การตั้งค่าการแสดงผล opaque สำหรับ backend (≤ 8 KB) เพิ่มเมื่อ 2026-09-07 |
| `doc_version` | `Int @db.Integer` | No | ค่า default `0` ตัวนับสำหรับ optimistic-concurrency |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `[deleted_at]` (`tenant_dashboard_bu_widget_deleted_idx`) ไม่มีคอลัมน์ `business_unit_id` — tenant schema เองคือขอบเขตของ BU

### 5.2 `tb_dashboard_personal_widget`

รูปแบบเดียวกับ `tb_dashboard_bu_widget` บวกคอลัมน์ scope `user_id String @db.Uuid` **Indexes:** `[user_id, deleted_at]` (`tenant_dashboard_personal_widget_user_deleted_idx`)

### 5.3 `enum_dashboard_widget_type` และความเข้ากันได้ของ shape

`kpi`, `line`, `area`, `bar`, `pie`, `heatmap`, `gauge`, `table`, `sparkline` — 9 ค่า (`model.WidgetTypes` ใน micro-data เป็นชุดเดียวกัน) registry มี 7 shape; render ที่เข้ากันได้ต่อ shape (`SupportedRenders`) คือ:

| Shape | Render ที่ micro-data ยอมรับ | วาดโดย frontend |
|---|---|---|
| `scalar`, `scalar_delta` | `kpi`, `gauge` | ทั้งคู่ |
| `time_series` | `line`, `area`, `bar`, `sparkline` | `line`, `area`, `bar` |
| `categorical` | `bar`, `pie`, `table` | ทั้งหมด |
| `ranked` | `bar`, `table` | `bar`, `table` (+ `pie`) |
| `matrix` | `heatmap`, `table` | ไม่มี |
| `table` | `table` | `table` |

render นอกชุดของ dataset ถูกปฏิเสธตอนสร้างและตอน `PATCH`; dataset ที่ registry ไม่รู้จักแล้วผ่านเฉพาะการเช็ค canonical ดังนั้นการแก้ไขอื่นของ widget เก่าไม่ถูกบล็อก

### 5.4 payload สำหรับเขียน (micro-data `model/dashboard.go`)

```
WidgetCreateInput { dataset_id, widget_type, title?, order_index?, params?, display? }
WidgetUpdateInput { title?, order_index?, params?, widget_type?, display? }   -- อย่างน้อยหนึ่งฟิลด์
WidgetReorderItem { id, order_index }                                         -- POST .../reorder { items: [...] }
```

## 6. กติกาทางธุรกิจ

- **Tenant-scoped ไม่มี BU FK** ทั้งสองตารางอยู่ใน schema ของแต่ละ tenant เอง; การ resolve `bu_code` เกิดที่ชั้นการเชื่อมต่อ
- **Widget ส่วนตัวเป็นของผู้ใช้แต่ละคนอย่างเข้มงวด** `PersonalFindOne`/`PersonalFindByID` กรองด้วย `user_id` เสมอ
- **Render ต้องเข้ากับ shape** `validateRender()` ตอนสร้างและอัปเดต; `supported_renders` เป็น single source of truth ที่ประกาศบนแคตตาล็อก
- **`params` และ `display` แทนที่ทั้งก้อน** ส่ง object เต็มบน `PATCH`
- **`display` มีขอบเขต ไม่ถูกตีความ** จำกัด 8 KB; client เป็นเจ้าของ schema ดังนั้นตัวเลือกใหม่ไม่ต้อง release backend
- **Soft delete เท่านั้น** ทั้งสองตารางใช้ `deleted_at`; ไม่พบ hard delete
- **การจัดเรียงเป็น transactional** `PersonalReorder` ห่อการอัปเดต `order_index` แบบกลุ่มไว้ใน DB transaction เดียว (`db/widget_repo.go`)
- **ไม่มี default/seed layout** รายการ widget ส่วนตัวและ BU ของผู้ใช้ใหม่เริ่มต้นว่างเปล่า

## 7. ความเชื่อมโยงข้ามโมดูล

- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — หน้าจอ `/dashboard` ที่ใช้งานจริงซึ่งข้อมูล `tb_dashboard_personal_widget` ของหน้านี้เป็นฐาน; มี UI walkthrough, hook และ gateway controller แบบเต็ม
- [recipe/operation-dashboard](/th/inventory/recipe/operation-dashboard) — mechanism ของ system widget แบบ hardcode เบื้องหลัง dashboard หน้าแรกของโมดูล (route config + dataset ต่อ tile แบบ lazy)
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — แคตตาล็อกที่ลงทะเบียนในโค้ดซึ่ง `dataset_id` ทุกตัวอ้างอิงถึง
- [access-control/user](/th/inventory/access-control/user) — เจ้าของ widget ส่วนตัว (`user_id`)
- [master-data/business-unit](/th/inventory/master-data/business-unit) — จำกัดการมองเห็น BU widget (tenant = BU)

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_dashboard_widget_type`, `tb_dashboard_bu_widget`, `tb_dashboard_personal_widget`; migration `20260609190100_add_dashboard_widget_tables`, `20260907143700_add_dashboard_widget_display`; ประวัติ `20260512180928_widget_system_replace_dashboard` / `20260521040013_remove_widget_system` (ตระกูล `tb_widget_*` ที่ถูกลบไปแล้ว)
- **micro-data (Go):** `../micro-data/controller/dashboard_controller.go` (route), `service/widget_service.go` (`validateCreate`/`validateUpdate`, `validateRender`, `validateDisplay`), `db/widget_repo.go` (`PersonalReorder`), `model/dashboard.go` (`WidgetTypes`, input), `service/dashboard/dashboard.go` (`SupportedRenders`), `service/dashboard/lab.go` (แคตตาล็อก), `routes/routes.go` + `middleware` (`GinInternalAuth`), `migrations/tenant/130_dash_widget_display.up.sql`, `api/openapi.yaml`
- **Backend gateway (ชั้น proxy):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-bu-widgets.controller.ts` + `.service.ts`, `dashboard-personal-widgets.controller.ts` + `.service.ts` (`x-internal-token`), `system-widgets.controller.ts` (`GET :module/config`, `GET me`, `GET all`), `system-widgets.config.ts`, `swagger/response.ts`; `dashboard-lab/`, `dashboard-datasets/`
- **Frontend:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx`, `sortable-widget-item.tsx`, `status-group.ts`, `use-my-dashboard-widgets.ts`; `hooks/use-dashboard-widgets.ts` (`useDashboardWidgetConfigs`), `hooks/use-dashboard-dataset.ts`; `components/dashboard-widget/render-support.ts`, `widget-display.ts`; `types/dashboard-widget.ts`, `types/dashboard-dataset.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/dashboard-widgets/*` (BU, personal, module, `GET-module-config`, `GET-me`, `GET-all`), `_uncategorized/dashboard-lab/*`, `_uncategorized/dashboard-datasets/*`
