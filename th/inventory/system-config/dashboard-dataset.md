---
title: ชุดข้อมูลแดชบอร์ด (Dashboard Dataset)
description: แคตตาล็อก read-only ของ admin สำหรับ data feed ที่ลงทะเบียนไว้ในโค้ด — แหล่งข้อมูลแบบมีชื่อและมี type ที่ widget บนแดชบอร์ดดึงข้อมูลจาก แยกออกจาก widget workspace layout ของผู้ใช้ และจาก view ที่เขียนด้วย SQL ใน query-dataset
published: true
date: 2026-06-09T00:00:00.000Z
tags: system-config, dashboard, dataset, widget, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# ชุดข้อมูลแดชบอร์ด (Dashboard Dataset)

> **At a Glance**
> **เจ้าของ:** Sysadmin (แคตตาล็อก read-only) &nbsp;·&nbsp; **Backing:** ลงทะเบียนไว้ในโค้ดบริการ **micro-data** (`GET /api/dashboard/datasets`) โดย backend-gateway เป็น proxy ผ่าน HTTP — **ไม่มีตาราง tenant เฉพาะ** &nbsp;·&nbsp; **ใช้โดย:** [reporting-audit/widget](/th/inventory/reporting-audit/widget) (widget picker), dashboard tile &nbsp;·&nbsp; **68 feed แบบมี shape** (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`) ครอบคลุม inventory, workflow, procurement, product, vendor, recipe และ equipment

## 1. คืออะไรและใครใช้

Dashboard Dataset คือ **หน้าจอแคตตาล็อก admin แบบ read-only** ที่ `/system-admin/dashboard-dataset` แสดง data feed ทุกตัวที่มีชื่อซึ่ง widget บนแดชบอร์ดสามารถสมัครใช้ได้ แต่ละรายการในแคตตาล็อกคือ **definition ที่ลงทะเบียนไว้ในโค้ด** ใน microservice **micro-data** (Go) ซึ่ง execute กับฐานข้อมูล tenant และส่งผ่าน gateway ผ่าน HTTP — ไม่ใช่ row ในฐานข้อมูลที่ sysadmin แก้ไขได้ แคตตาล็อกถูกกำหนดตายตัวต่อเวอร์ชันของแอปพลิเคชัน; sysadmin เรียกดูและค้นหาเพื่อทำความเข้าใจว่ามี feed ใดบ้างก่อนที่จะวางหรือตั้งค่า widget

**ความแตกต่างจากสองแนวคิดที่เกี่ยวข้อง:**

| แนวคิด | ลักษณะ | แก้ไขได้? | เก็บใน |
|---|---|---|---|
| **Dashboard Dataset** (หน้านี้) | แคตตาล็อก data feed ที่มีชื่อ — query รันกับ tenant DB และคืนข้อมูลแบบ typed | Read-only; อัปเดตโดย code deployment | บริการ **micro-data** (Go) ให้บริการที่ `/api/dashboard/datasets` |
| [system-config/query-dataset](/th/inventory/system-config/query-dataset) | SQL Workbench — admin เขียน tenant view / stored procedure / function | Sysadmin สร้าง/drop catalog object | PostgreSQL catalog (`pg_class`, `pg_proc`) |
| [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) | Layout แดชบอร์ดที่บันทึกต่อผู้ใช้ — dataset ใดแสดง, ขนาดเท่าไร, ลำดับใด | ผู้ใช้แต่ละคนแก้ layout ของตัวเอง | `tb_widget_dashboard` + `tb_widget_dashboard_item`, seed ด้วย `tb_widget_default_layout` (tenant DB) |

**บำรุงรักษาโดย** Engineering (code release) **เรียกดูโดย** Sysadmin เพื่อตรวจสอบ feed ที่มี **บริโภคโดย** widget picker ภายใน dialog "Add widget" ของแดชบอร์ด

dataset แต่ละตัว execute ภายใน **read-only transaction** โดย `SET LOCAL search_path` ถูกตรึงไว้กับ tenant schema ของผู้เรียก ทำให้แคตตาล็อกที่ deploy ชุดเดียวให้บริการ tenant ทุกรายได้อย่างปลอดภัย backend-gateway ทำหน้าที่เป็น thin proxy: `GET /api/dashboard/datasets` รายการแคตตาล็อก (`{items,count}`) และ `GET /api/dashboard/datasets/:id?bu_code=&user_id=` execute feed เดียว (`{meta,data}`)

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เรียกดูแคตตาล็อก dataset ทั้งหมด | System Admin → Dashboard Dataset | แสดงรายการ feed ทั้งหมดจัดกลุ่มตาม category |
| ค้นหา dataset เฉพาะ | Search bar ที่ด้านบนของหน้า | กรองด้วย id, name, description หรือ category |
| ระบุ shape ของ dataset | badge `shape` บนแต่ละ card | ดู §5.1 สำหรับความหมายของ shape |
| เพิ่ม dataset ลงใน widget | Dashboard → Add widget → dataset picker | เปิด popover ที่รองรับโดยแคตตาล็อกนี้ |
| ดูค่า live ของ dataset | Preview widget บนแดชบอร์ด | เรียก `GET /api/:bu_code/datasets/:dataset_id` |
| เพิ่ม data feed ใหม่ | แก้ไขโค้ดในบริการ **micro-data** | งานของ Engineering — ต้องมีการ deploy |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| หน้าแสดง "No datasets available" | ไม่ resolve business unit context หรือ API คืนค่าว่าง | ตรวจสอบ `bu_code` ใน session; ยืนยันว่า microservice กำลังทำงาน |
| Dataset หายจากแคตตาล็อก | ยังไม่ได้ลงทะเบียนในโค้ด registry | Engineering ต้องเพิ่ม entry `DatasetDefinition` และ deploy |
| Widget error ตอน load หลังเลือก dataset | `id` ของ dataset อ้างอิง entry ที่ถูกลบหรือเปลี่ยนชื่อในการ deploy | เลือก dataset ปัจจุบันจากแคตตาล็อกใหม่อีกครั้ง |
| 403 บน route `/system-admin/dashboard-dataset` | ผู้ใช้ขาด role Sysadmin หรือสิทธิ์ App ID | Grant ผ่าน [access-control/application-role](/th/inventory/access-control/application-role) |
| Dataset คืนค่าที่ล้าสมัย | รายการแคตตาล็อก cache ด้วย `CACHE_STATIC`; ค่ารายตัวใช้ `CACHE_DYNAMIC` (TTL 1 นาที) | Hard-refresh หน้าหรือรอ cache หมดอายุ |

## 4. กรณีพิเศษ

- **ไม่มีฐานข้อมูลรองรับแคตตาล็อก** endpoint รายการอ่านจาก registry ที่ compile ตอน build — ไม่มีตาราง `tb_dashboard_dataset` ที่จะ query หรือ migrate การเพิ่ม feed ต้องใช้ code release
- **Shape contract เข้มงวด** dataset แต่ละตัวประกาศหนึ่งใน six shapes (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`) frontend widget renderer narrow ตาม `meta.shape`; ความไม่ตรงกันของ shape ระหว่าง registry กับโค้ด frontend ทำให้เกิด render error
- **การ execute scope ตาม tenant** เมื่อ widget ดึงข้อมูล **micro-data** จะรัน query ภายใน read-only transaction โดย `SET LOCAL search_path` ถูกตรึงไว้กับ tenant schema (`bu_code`) ของผู้เรียก — ทุก query ถูกจำกัดอยู่ใน tenant schema ที่ถูกต้อง; การเข้าถึงข้อมูล cross-tenant เป็นไปไม่ได้
- **Category เป็น soft field** `category` คือ string อิสระบน registry entry (ค่าทั่วไป: `inventory`, `workflow`, `movement`, `spend`, `variance`) UI จัดกลุ่ม card ตามตัวอักษรของ category; category ใหม่ในอนาคตจะปรากฏโดยอัตโนมัติ
- **Cache แยกกัน** รายการแคตตาล็อกใช้ `CACHE_STATIC` (อยู่นาน); payload ของ dataset รายตัวใช้ `CACHE_DYNAMIC` (1 นาที) รายการแคตตาล็อกที่ล้าสมัยจะคงอยู่จนกว่าจะมีการ hard-refresh ครั้งถัดไป
- **`unit` เป็น display เท่านั้น** ฟิลด์ `unit` (เช่น `items`, `฿`, `%`, `วัน`) คือ hint สำหรับ label ของ widget tile — ไม่ส่งผลต่อการคำนวณข้อมูล

---

## 5. รูปแบบข้อมูล (Dev)

**ไม่มีตาราง tenant เฉพาะ** แคตตาล็อกลงทะเบียนไว้ในโค้ดของ micro-data (Go); ตารางฟิลด์ด้านล่างอธิบาย wire contract ที่ส่งคืนไปยัง gateway และ frontend

### 5.1 `DatasetMeta` — shape ของรายการแคตตาล็อก

| ฟิลด์ | Type | คำอธิบาย |
|---|---|---|
| `id` | `string` | ตัวระบุแบบ dot-namespaced เช่น `inventory.low-stock-count` ใช้เป็น reference `dataset_id` ของ widget |
| `name` | `string` | Label แบบอ่านได้ที่แสดงบน catalog card |
| `description` | `string?` | คำอธิบายแบบยาวแบบ optional |
| `shape` | `enum_dataset_shape` | หนึ่งใน: `scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix` กำหนดโครงสร้าง payload ที่ widget renderer คาดหวัง |
| `category` | `string` | การจัดกลุ่มเชิงฟังก์ชัน ค่าปัจจุบัน: `inventory`, `workflow`, `movement`, `spend`, `variance` |
| `unit` | `string?` | Hint แบบ display เท่านั้น เช่น `items`, `฿`, `%` |

### 5.2 `enum_dataset_shape` — payload contract

| Shape | โครงสร้าง payload | Widget ทั่วไป |
|---|---|---|
| `scalar` | `{ value: number }` | KPI tile |
| `scalar_delta` | `{ value: number; prev: number; change?: string }` | KPI tile พร้อมลูกศรแนวโน้ม |
| `time_series` | `Array<{ date: string; value: number }>` | Line / area / sparkline chart |
| `categorical` | `Array<{ label: string; value: number; color?: string }>` | Bar / pie / donut chart |
| `ranked` | `Array<{ rank: number; label: string; value: number; extras?: … }>` | Ranked bar / data table |
| `matrix` | `{ rows: string[]; cols: string[]; values: number[][] }` | Heatmap / cross-tab table |

### 5.3 API endpoints

```
GET  /api/:bu_code/datasets              → { items: DatasetMeta[], count: number }
GET  /api/:bu_code/datasets/:dataset_id  → { meta: DatasetMeta, data: DatasetData<shape> }
```

ทั้งคู่ต้องการ `Authorization: Bearer <token>` และ header `X-App-Id` response รายการใช้สำหรับ widget picker; response รายตัวป้อน widget tile ที่ live ภายในนั้น gateway ไม่ได้รัน query เอง — มันส่งต่อผ่าน HTTP ไปยังบริการ micro-data (`GET /api/dashboard/datasets` และ `GET /api/dashboard/datasets/:id?bu_code=&user_id=`) ซึ่งจะ execute dataset และส่งคืนผลลัพธ์

### 5.4 ที่ตั้งของ registry

แคตตาล็อก dataset ลงทะเบียนไว้ในโค้ดของบริการ **micro-data** (Go): handler อยู่ใน `../micro-data/controller/dashboard_controller.go`, logic ของ dataset/widget อยู่ใน `../micro-data/service/dashboard/` และ `../micro-data/service/widget_service.go`, และ model อยู่ใน `../micro-data/model/dashboard.go` ณ เวลาที่เขียนนี้ แคตตาล็อกมี **68** dataset แบบมี shape ครอบคลุม inventory, procurement, product, vendor, recipe, equipment และ config

## 6. กฎทางธุรกิจ

- **แคตตาล็อก read-only** Sysadmin ไม่สามารถสร้าง แก้ไข หรือลบรายการแคตตาล็อกผ่าน UI — แคตตาล็อกถูกจัดการด้วยโค้ด
- **Query scope ตาม tenant** ทุก dataset query รันใน micro-data ภายใน read-only transaction โดย `SET LOCAL search_path` ถูกตรึงไว้กับ schema ของ `bu_code` ของผู้เรียก — ข้อมูลทั้งหมดอ่านจาก schema ของ tenant ที่เรียกใช้
- **Shape contract เข้มงวด** frontend widget renderer switch ตาม `meta.shape`; การเพิ่ม shape ใหม่ต้องมีการเปลี่ยนแปลง frontend และ backend พร้อมกัน
- **ไม่ต้องมีสิทธิ์ CRUD เพื่อเรียกดู** หน้าจอมองเห็นได้สำหรับ Sysadmin โดยการเข้าถึงผ่าน navigation; ไม่มี granularity สิทธิ์ต่อ dataset — dataset ที่ลงทะเบียนทั้งหมดอ่านได้โดยผู้ใช้ที่ยืนยันตัวตนแล้วซึ่งสามารถโหลดแดชบอร์ดได้
- **`id` มีความเสถียร** dot-namespaced id (เช่น `workflow.pr-pending-approval`) ถูกเก็บเป็น `dataset_id` ในการตั้งค่า widget tile ใน `tb_widget_dashboard_item` การเปลี่ยนชื่อหรือลบ registry entry ทำลาย widget config ที่มีอยู่

## 7. การอ้างอิงข้าม

- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — widget บนแดชบอร์ดเลือกแหล่งข้อมูลจากแคตตาล็อกนี้; ฟิลด์ `dataset_id` บนแต่ละ widget row อ้างอิง `id` ในแคตตาล็อก
- [system-config/query-dataset](/th/inventory/system-config/query-dataset) — เครื่องมือ admin เสริม: sysadmin เขียน tenant view / stored procedure / function ด้วย SQL; object เหล่านั้นสามารถรองรับ report template ได้ feed ของ Dashboard Dataset เขียนด้วยโค้ด ไม่ใช่ SQL
- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — layout แดชบอร์ดที่บันทึกต่อผู้ใช้ที่เก็บใน `tb_widget_dashboard` + `tb_widget_dashboard_item`; แต่ละ tile row อ้างอิง `dataset_id` จากแคตตาล็อกนี้ (หมายเหตุ: `tb_widget_workspace` คือตารางแยกต่างหากสำหรับ query ที่บันทึกไว้ใน data explorer ต่อผู้ใช้ — ดู [reporting-audit/widget](/th/inventory/reporting-audit/widget))
- [access-control/application-role](/th/inventory/access-control/application-role) — การเข้าถึง navigation และ route ไปยัง `/system-admin/dashboard-dataset`

## 8. แหล่งข้อมูลอ้างอิง

- **micro-data service (Go):** `../micro-data/` — dashboard datasets + widget CRUD. Handlers: `controller/dashboard_controller.go`; logic: `service/dashboard/`, `service/widget_service.go`; models: `model/dashboard.go`; routes: `routes/routes.go`; overview: `README.md`
- **Gateway proxy:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-datasets/dashboard-datasets.service.ts` — HTTP proxy ไปยัง micro-data; controller `dashboard-datasets.controller.ts` เปิดเผย `GET /api/:bu_code/datasets` และ `GET /api/:bu_code/datasets/:dataset_id`
- **Swagger response DTOs:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-datasets/swagger/response.ts` — `DatasetMetaDto`, `DatasetListResponseDto`, `DatasetResponseDto`
- **Platform enum:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `enum_dataset_shape` (บรรทัด ~815)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/dashboard-dataset/page.tsx` และ `_components/dashboard-dataset-component.tsx`
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-dashboard-dataset.ts` — `useDashboardDatasets()`, `useDashboardDatasetDetail(id)`
- **Frontend type:** `../carmen-inventory-frontend/types/dashboard-dataset.ts` — `DashboardDataset`, `DashboardDatasetShape`, `DashboardDatasetCategory`
