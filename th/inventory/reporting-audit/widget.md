---
title: Widget
description: เอนทิตี widget ของ dashboard — tile แบบ BU-scoped และต่อผู้ใช้ที่ผูกกับแคตตาล็อก dataset ที่ลงทะเบียนในโค้ด ให้บริการโดย micro-data service (Go) ตระกูลตาราง tb_widget_workspace / tb_widget_dashboard / tb_widget_dashboard_item / tb_widget_default_layout ที่หน้านี้เคยบันทึกไว้ไม่มีอยู่จริง
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

> **At a Glance**
> **เจ้าของ:** ผู้ใช้ปลายทาง (widget ส่วนตัว) + สมาชิก BU โดยนัย (ไม่พบ gate ที่แยก "BU admin" ในการแก้ไข) &nbsp;·&nbsp; **ตาราง:** `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` (tenant schema) &nbsp;·&nbsp; **ใช้โดย:** หน้าจอ [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) ที่ `/dashboard` (ส่วนตัว) และ dashboard หน้าแรกของแต่ละโมดูลใต้ Procurement / Inventory-management / Vendor-management / Product-management / Operation-plan / Config (BU) &nbsp;·&nbsp; **ให้บริการโดย:** micro-data (Go)

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

หน้านี้ฉบับก่อนหน้าบันทึกตระกูลตาราง `tb_widget_dashboard` / `tb_widget_dashboard_item` / `tb_widget_default_layout` / `tb_widget_workspace` ว่าเป็นระบบ widget ที่ใช้งานจริง การค้นหาทั่ว Prisma schema ทุกตัว (tenant, platform, file) พบว่า **ไม่มี `model tb_widget_*` ประกาศอยู่เลยแม้แต่ตัวเดียว** — `tb_widget_dashboard`, `tb_widget_dashboard_item` และ `tb_widget_default_layout` ไม่เคยมีอยู่จริง ส่วน `tb_widget_workspace` *เคย* มีอยู่จริงในช่วงสั้น ๆ — สร้างโดย migration `20260512180928_widget_system_replace_dashboard` (tenant schema) — แต่ถูกลบไปเก้าวันให้หลังโดย migration `20260521040013_remove_widget_system` (`DROP TABLE IF EXISTS "tb_widget_workspace" CASCADE`, พร้อมกับ `tb_widget_dashboard`, `tb_widget_dashboard_item`, `tb_widget_default_layout` และ `tb_widget_comment` ใน migration เดียวกัน) ไม่มีฟีเจอร์ data-explorer/saved-query ใด ๆ อยู่ใน frontend หรือ backend ปัจจุบันที่เคยใช้ตารางนี้

ตาราง widget ที่มีอยู่จริงและใช้งานอยู่ในปัจจุบันคือ `tb_dashboard_bu_widget` และ `tb_dashboard_personal_widget` — อธิบายไว้ด้านล่าง หน้านี้ถูกเขียนใหม่เพื่ออธิบายตารางทั้งสองนี้

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี widget คือ **ชั้น tile ของ dashboard** — การวาง feed [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) ที่ลงทะเบียนในโค้ด (`dataset_id`) แสดงเป็นกราฟ (`widget_type`) บน dashboard ของ business unit ที่แชร์กัน หรือ dashboard ส่วนตัวของผู้ใช้คนเดียว มีตารางอยู่เพียงสองตาราง ทั้งคู่เป็น **tenant-scoped** (resolve ด้วย `bu_code` — tenant schema เองคือ BU ดังนั้นทั้งสองตารางไม่มีคอลัมน์ `business_unit_id`):

- `tb_dashboard_bu_widget` — widget บน dashboard ที่แชร์กันของ business unit ขับเคลื่อน dashboard หน้าแรกของแต่ละโมดูล (เช่น `procurement-dashboard.tsx` → `useProcurementWidgets` → `GET api/:bu_code/dashboard-widgets/bu`) **ไม่ใช่** หน้าจอของโมดูล reporting-audit นี้เอง
- `tb_dashboard_personal_widget` — widget บน dashboard ส่วนตัวของผู้ใช้หนึ่งคน scope ด้วย `user_id` ขับเคลื่อน Widget Workspace ที่ route `/dashboard` — ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) สำหรับ UI แบบเต็ม (เพิ่ม/จัดเรียง/ลบ, drag-and-drop, empty state)

ไม่มีตาราง default-layout และไม่มี seeding mechanism — dashboard ส่วนตัวของผู้ใช้ใหม่เริ่มต้นว่างเปล่า; dashboard ที่แชร์กันของ BU ใหม่ก็เริ่มต้นว่างเปล่า ไม่มีฟีเจอร์ saved-query / data-explorer ใด ๆ — `dataset_id` อ้างอิงรายการคงที่ในแคตตาล็อก [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) ที่ลงทะเบียนในโค้ดเสมอ ไม่เคยเป็น query ที่ผู้ใช้เขียนเอง

**ดูแลโดย** ผู้ใช้ปลายทาง (widget ส่วนตัวของตนเอง) BU widget ไม่พบ gate "BU admin" ที่แยกออกมาใน controller ของ backend-gateway — endpoint CRUD ด้านล่างไม่มีการตรวจสอบ role เพิ่มเติมนอกจากการยืนยันตัวตนมาตรฐาน ดังนั้นในทางปฏิบัติผู้ใช้ที่ authenticate แล้วและมี `bu_code` context สามารถสร้าง/แก้ไข/ลบ BU widget ได้ **อ่านโดย** [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) (ส่วนตัว) และ component dashboard หน้าแรกของแต่ละโมดูล (BU)

### 1.1 Widget CRUD ทำงานที่ไหน (micro-data)

การสร้าง/อ่าน/แก้ไข/ลบ widget ถูก host โดย service **micro-data** (Go) ไม่ใช่ micro-cluster คอมเมนต์ในโค้ดของ `micro-data/controller/dashboard_controller.go` เองระบุไว้ชัดเจน: *"exposes the dashboard dataset catalogue/execution and the BU + personal widget CRUD over HTTP. The backend-gateway calls these instead of micro-business (datasets) / micro-cluster (widgets)."* `DashboardBuWidgetsService` / `DashboardPersonalWidgetsService` ของ backend-gateway เป็นเพียง HTTP proxy บาง ๆ (`fetch` ไปที่ `DATASET_SERVICE_HOST:DATASET_SERVICE_HTTP_PORT`) — ไม่มี business logic และไม่มีการเชื่อมต่อ DB โดยตรงของตัวเอง

| Scope | Endpoint ของ micro-data (proxy โดย backend-gateway) |
|---|---|
| **BU widgets** | `GET/POST /api/dashboard/bu-widgets?bu_code=` · `GET/PATCH/DELETE /api/dashboard/bu-widgets/:id?bu_code=` |
| **Personal widgets** | `GET/POST /api/dashboard/personal-widgets?user_id=&bu_code=` · `GET/PATCH/DELETE /api/dashboard/personal-widgets/:id?user_id=&bu_code=` · `POST /api/dashboard/personal-widgets/reorder?user_id=&bu_code=` (อัปเดต `order_index` แบบกลุ่มด้วย transaction เดียว) |

route ฝั่ง gateway ที่ frontend เรียกจริง ๆ คือ `api/me/dashboard-widgets` (ส่วนตัว, resolve `user_id` จาก auth header) และ controller ของ BU ในลักษณะเดียวกัน — ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) §5 และ §8 สำหรับ hook และ gateway controller ที่แน่ชัด

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม widget ส่วนตัว | `/dashboard` → **+ Add widget** | Picker กรองแคตตาล็อก dataset ตาม shape ที่รองรับ (`scalar`, `scalar_delta`, `categorical`); ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) |
| จัดเรียง widget ส่วนตัว | `/dashboard` → ลาก widget card | อัปเดต `order_index` แบบ optimistic แล้วตามด้วย `POST .../personal-widgets/reorder` |
| ลบ widget ส่วนตัว | `/dashboard` → เมนู widget card | `DELETE .../personal-widgets/:id` — soft delete (`deleted_at`) |
| เพิ่ม/แก้ไข BU widget | dashboard หน้าแรกของแต่ละโมดูล (เช่น `/procurement`) | รูปแบบ CRUD เดียวกับ widget ส่วนตัว scope ด้วย `bu_code` เท่านั้น |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| Widget ส่วนตัวไม่แสดงให้เพื่อนร่วมทีมเห็น | ตามที่ออกแบบไว้ — widget ส่วนตัว scope ด้วย `user_id` เสมอ ไม่เคยแชร์กัน | ใช้ BU widget บน dashboard หน้าแรกของโมดูลแทน |
| Widget card แสดงสถานะ error | ดึง `dataset_id` ไม่สำเร็จ หรือ dataset ถูกลบออกจากแคตตาล็อก | ลบและเพิ่มใหม่จาก picker; ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) |
| 404 ตอนอัปเดต/ลบ widget | `PersonalFindOne`/`BuFindByID` กรอง `deleted_at IS NULL` — id ถูก soft-delete ไปแล้วหรือไม่เคยมีอยู่ | ดึงรายการ widget ใหม่ |
| การจัดเรียงดูเหมือนล้มเหลวแบบเงียบ ๆ | `PersonalReorder` อัปเดตแถวในลูปภายใน DB transaction เดียว — ถ้าล้มเหลวกลางทาง การจัดเรียงทั้งหมดจะ rollback | ลองใหม่; ตรวจ response ของ PATCH สำหรับ id ที่ล้มเหลว |

## 4. กรณีพิเศษ

- **ไม่มี default/seed layout** ต่างจากที่เคยบันทึกไว้ (`tb_widget_default_layout` ซึ่งไม่มีอยู่จริง) ไม่มี seeding mechanism ใด ๆ เลย — grid ของ widget ของผู้ใช้ใหม่และ BU ใหม่ทุกคนเริ่มต้นว่างเปล่า
- **ไม่มีแนวคิด workspace/saved-query** `dataset_id` อ้างอิงรายการคงที่ในแคตตาล็อกเสมอ ไม่มี query ที่ผู้ใช้เขียนเองในระบบนี้เลย
- **ไม่พบ authorization gate สำหรับ BU widget** endpoint ของ BU widget ต้องการ `bu_code` แต่ไม่พบการตรวจสอบ role "BU admin" เพิ่มเติมใน `dashboard-bu-widgets.controller.ts` — ทำเครื่องหมายว่ายังไม่ยืนยันแทนที่จะยืนยันกฎ admin-only เฉพาะเจาะจง
- **Params เป็น config ของ dataset ไม่ใช่ request context** `WidgetCreateInput.Params` (JSONB) เก็บ config ของ filter เฉพาะ dataset (เช่น status filter) ที่ตั้งค่าตอนสร้าง widget — ไม่มี `user_id`/`bu_code` ซึ่งผู้เรียกใส่มาตอน execute เสมอ

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_dashboard_bu_widget`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `dataset_id` | `String @db.VarChar(100)` | No | อ้างอิงรายการในแคตตาล็อก [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) (ไม่มี FK — เป็น code registry ไม่ใช่ตาราง) |
| `widget_type` | `enum_dashboard_widget_type` | No | `kpi` / `line` / `area` / `bar` / `pie` / `heatmap` / `gauge` / `table` / `sparkline` |
| `title` | `String? @db.VarChar(255)` | Yes | ชื่อ override ถ้ามี; ถ้าไม่มีใช้ชื่อแสดงผลของ dataset เอง |
| `order_index` | `Int` | No | ค่า default `0` ตำแหน่งใน grid |
| `params` | `Json? @db.JsonB` | Yes | config ของ filter เฉพาะ dataset |
| `doc_version` | `Int @db.Integer` | No | ค่า default `0` ตัวนับสำหรับ optimistic-concurrency |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Indexes:** `[deleted_at]` (`tenant_dashboard_bu_widget_deleted_idx`) ไม่มีคอลัมน์ `business_unit_id` — tenant schema เองคือขอบเขตของ BU

### 5.2 `tb_dashboard_personal_widget`

รูปแบบเดียวกับ `tb_dashboard_bu_widget` บวกคอลัมน์ scope `user_id String @db.Uuid` **Indexes:** `[user_id, deleted_at]` (`tenant_dashboard_personal_widget_user_deleted_idx`)

### 5.3 `enum_dashboard_widget_type`

`kpi`, `line`, `area`, `bar`, `pie`, `heatmap`, `gauge`, `table`, `sparkline` — 9 ค่า แคตตาล็อก dataset เองมี 6 shape (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`; ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset)) ไม่ใช่ทุกคู่ shape × type ที่ frontend picker ปัจจุบันใช้งาน (picker ของ `/dashboard` สร้างได้เฉพาะ widget `kpi` หรือ `pie` เท่านั้น — ดู [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) §1 สำหรับการจำกัดที่แน่ชัด)

## 6. กติกาทางธุรกิจ

- **Tenant-scoped ไม่มี BU FK** ทั้งสองตารางอยู่ใน schema ของแต่ละ tenant เอง; การ resolve `bu_code` เกิดที่ชั้นการเชื่อมต่อ ไม่ใช่ผ่านคอลัมน์ foreign key
- **Widget ส่วนตัวเป็นของผู้ใช้แต่ละคนอย่างเข้มงวด** ไม่มี sharing mechanism ใด ๆ เลย — `PersonalFindOne`/`PersonalFindByID` กรองด้วย `user_id` เสมอ
- **Soft delete เท่านั้น** ทั้งสองตารางใช้ `deleted_at`; ไม่พบ hard delete
- **การจัดเรียงเป็น transactional** `PersonalReorder` ห่อการอัปเดต `order_index` แบบกลุ่มไว้ใน DB transaction เดียว (`tdb.Transaction(...)` ใน `micro-data/db/widget_repo.go`)
- **ไม่มี default/seed layout** รายการ widget ส่วนตัวและ BU ของผู้ใช้ใหม่เริ่มต้นว่างเปล่า — ยืนยันว่าไม่มีจริง ไม่ใช่แค่ไม่ได้บันทึกไว้

## 7. ความเชื่อมโยงข้ามโมดูล

- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — หน้าจอ `/dashboard` ที่ใช้งานจริงซึ่งข้อมูล `tb_dashboard_personal_widget` ของหน้านี้เป็นฐาน; มี UI walkthrough, hook และ gateway controller แบบเต็ม
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — แคตตาล็อกที่ลงทะเบียนในโค้ดซึ่ง `dataset_id` ทุกตัวอ้างอิงถึง
- [access-control/user](/th/inventory/access-control/user) — เจ้าของ widget ส่วนตัว (`user_id`)
- [master-data/business-unit](/th/inventory/master-data/business-unit) — จำกัดการมองเห็น BU widget (tenant = BU)
- โมดูลธุรกรรมทั้งหมด — แหล่งข้อมูล dataset ทั่วไปของ tile (หมวดหมู่ procurement, inventory, vendor, product, recipe ในแคตตาล็อก dataset)

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_dashboard_widget_type` (บรรทัด ~6155), `tb_dashboard_bu_widget` (บรรทัด ~6178), `tb_dashboard_personal_widget` (บรรทัด ~6198)
- **Migration (ประวัติ):** `20260512180928_widget_system_replace_dashboard` (สร้างตระกูล `tb_widget_workspace` ที่ถูกลบไปแล้ว), `20260521040013_remove_widget_system` (ลบทิ้ง, "Drop widget subsystem")
- **micro-data service (Go):** `../micro-data/controller/dashboard_controller.go` (HTTP handler สำหรับทั้งการ execute dataset และ widget CRUD), `../micro-data/service/widget_service.go`, `../micro-data/db/widget_repo.go`, `../micro-data/model/dashboard.go`
- **Backend gateway (ชั้น proxy):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-bu-widgets.controller.ts` + `.service.ts`, `dashboard-personal-widgets.controller.ts` + `.service.ts`
- **Frontend:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx` + `sortable-widget-item.tsx`; `hooks/use-my-dashboard-widgets.ts`
