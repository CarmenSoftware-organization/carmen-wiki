---
title: Widget Workspace แดชบอร์ด (Widget Workspace Dashboard)
description: แดชบอร์ด production จริงที่ /dashboard — workspace แบบ drag-and-drop ส่วนตัว ที่ผู้ใช้แต่ละคนปักหมุด widget KPI, pie และ bar จาก dataset catalog ของระบบ
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, widget-workspace, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget Workspace แดชบอร์ด (Widget Workspace Dashboard)

> **At a Glance**
> **Route:** `/dashboard` &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **Live** — ขับเคลื่อนด้วย API จริง; เนื้อหา dataset ขึ้นอยู่กับการ seed ฝั่ง backend &nbsp;·&nbsp; **ขอบเขต:** ส่วนบุคคล — layout widget ที่ user แต่ละคนบันทึกไว้

## 1. คืออะไรและสำหรับใคร

Widget Workspace คือ **หน้าเดียวเท่านั้นบน route `/dashboard`** — ไม่มีชุดหน้าย่อยแบบมีชื่อของโดเมนต่างๆ อยู่เบื้องหลังมันแต่อย่างใด (เอกสารฉบับก่อนหน้าของ wiki นี้เคยอ้างว่ามัน "แทนที่" หน้า mock 6 หน้าที่ `/dashboard/pr`, `/dashboard/po` ฯลฯ — หน้าเหล่านั้นไม่เคยมีอยู่จริงในฐานะ route เลย ดูหน้าพี่น้อง [dashboard/main](/th/inventory/dashboard/main), [pr](/th/inventory/dashboard/pr) ฯลฯ ซึ่งตอนนี้ถูก flag ว่าเป็นข้อมูลเชิงประวัติศาสตร์เท่านั้น) หน้านี้ render กริด widget แบบ drag-and-drop ส่วนตัว โดยแต่ละ widget ผูกกับ dataset จาก system catalog

> **หมายเหตุเรื่องชื่อ (แก้ไขเมื่อ 2026-07-16):** ตาราง backend จริงคือ `tb_dashboard_personal_widget` (ข้อมูลของหน้านี้ — tenant schema, `packages/prisma-shared-schema-tenant/prisma/schema.prisma` บรรทัด ~6205: `dataset_id`, `widget_type`, `order_index`, `params`, scope ด้วย `user_id`) และตารางพี่น้อง `tb_dashboard_bu_widget` (บรรทัด ~6185, scope ระดับ BU, widget ที่ admin curate ไว้ให้สมาชิกทุกคนใน business unit เห็น — เป็นฟีเจอร์**คนละตัว นอก scope ของหน้านี้** ที่ขับเคลื่อนแดชบอร์ด landing ระดับโมดูลใน Procurement/Inventory-management ฯลฯ ไม่ใช่หน้านี้) หมายเหตุฉบับก่อนหน้าอ้างถึง `tb_widget_dashboard`, `tb_widget_dashboard_item`, และ `tb_widget_default_layout` — **ตารางเหล่านี้ไม่มีอยู่จริง** ในทุก Prisma schema (tenant, platform หรือ file) หรือใน micro-data/micro-report ส่วน `tb_widget_workspace` ที่ชื่อคล้ายกันก็เป็นแนวคิดที่แยกต่างหากเช่นกัน (query ที่บันทึกไว้ใน data explorer ต่อผู้ใช้) — ดู [reporting-audit/widget](/th/inventory/reporting-audit/widget) สำหรับ data model นั้น

**Layout:**
- Header ทักทาย (ตามช่วงเวลาของวัน + ชื่อเต็มของผู้ใช้) render จาก user profile
- Section "Saved Widgets": กริด responsive (1 col → 2 col → 4 col) ของ widget card ที่ผู้ใช้เลือกไว้ เรียงตาม `order_index`
- แต่ละ card ลาก (drag) ได้ผ่าน `@dnd-kit/core` — วาง (drop) เพื่อเรียงใหม่และ PATCH อัปเดต `order_index` แบบ optimistic
- Picker "+ Add widget" กรอง dataset catalog ตาม shape ที่รองรับ (`scalar`, `scalar_delta`, `categorical`) และยกเว้น dataset ที่ปักหมุดไว้แล้ว
- Empty state: placeholder พร้อม chip hints (KPI / Pie / Bar) แนะนำให้ผู้ใช้เพิ่ม widget แรก

**Shape ของ widget และประเภทการ render:**

| Shape | แสดงเป็น |
|---|---|
| `scalar` | KPI number card |
| `scalar_delta` | KPI number card พร้อม delta indicator |
| `categorical` | Pie card |

ระบบ type ของ dataset นิยาม shape ไว้ 6 แบบและ widget type ไว้ 9 แบบทั้งหมด (`enum_dashboard_widget_type`: `kpi`/`line`/`area`/`bar`/`pie`/`heatmap`/`gauge`/`table`/`sparkline`) แต่หน้านี้ให้ผู้ใช้ปักหมุดได้เพียง 3 shape ข้างต้นเท่านั้น (`SUPPORTED_SHAPES` ใน `dashboard-component.tsx`) และ flow การสร้าง (`inferWidgetTypeFromShape`) จะกำหนด `widget_type: "kpi"` (สำหรับ `scalar`/`scalar_delta`) หรือ `"pie"` (สำหรับ `categorical`) เท่านั้น — ไม่เคยสร้าง widget แบบ `"bar"` จาก picker ของหน้านี้เลย แม้ `WidgetRenderer` ของ `SortableWidgetItem` จะ render card แบบ bar ได้ถ้ามีอยู่จริงก็ตาม

**กลุ่มผู้ใช้**

- **ผู้ใช้ที่เข้าระบบทุกคน** — ทุก operator สร้าง workspace ของตัวเอง ไม่มี layout ตายตัว workspace เริ่มว่างเปล่าและเติบโตเมื่อผู้ใช้ปักหมุด widget
- **นักพัฒนา** — compositing layer คือ `dashboard-component.tsx`; การ render widget จัดการโดย `AppTile` / `SortableWidgetItem`

## 2. Tile และการ Drill-down

Widget Workspace ไม่มีชุด tile ตายตัว — กริดเป็น dynamic ทั้งหมดและเป็นส่วนตัวของผู้ใช้แต่ละคน:

| Widget Card | แหล่งข้อมูล | เพิ่มผ่าน |
|---|---|---|
| Dataset `scalar` / `scalar_delta` ใดก็ได้ | `GET /api/proxy/api/me/dashboard-widgets` คืนรายการที่บันทึกไว้; ข้อมูลแต่ละรายการ fetch ด้วย `dataset_id` | picker "+ Add widget" |
| Dataset `categorical` ใดก็ได้ | endpoint เดียวกัน, render เป็น pie | picker "+ Add widget" |

Drill-down จาก widget card ขึ้นอยู่กับ dataset definition และไม่ได้ถูกกำหนดตายตัวโดย workspace เอง สีของ tile ตาม dataset category และ module-color-map convention

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไมหน้าแสดง greeting แทนที่จะเป็น tile? | Workspace โหลดรายการ widget ที่บันทึกไว้ของผู้ใช้ — ถ้าว่างจะแสดง empty-state เพิ่ม widget อย่างน้อยหนึ่งรายการผ่าน picker "+ Add widget" |
| dataset ที่ใช้ได้มาจากไหน? | picker "Add widget" เรียก `LookupDataset` ซึ่ง query dataset catalog dataset ถูกนิยามและ seed โดย backend ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) |
| นี่คือสิ่งเดียวกับ "แดชบอร์ด PR / PO / GRN" ที่ document ไว้ในหน้าย่อยอื่นของโมดูลนี้หรือเปล่า? | ไม่ใช่ — และหน้าย่อยเหล่านั้นก็ไม่เคยมี route จริงเช่นกัน workspace นี้**คือ**ทั้งหมดของ `/dashboard`; "แดชบอร์ดโดเมน" ที่มีชื่อนั้น document ไฟล์ demo ที่ถูกลบไปเมื่อ 2026-06-27 (commit `03891e3d`) ซึ่งไม่เคยถูก wire เข้า router เลย |
| ฉันสามารถ reset layout ไปยังค่าเริ่มต้นได้ไหม? | ยังไม่เปิดให้ใช้ใน UI ไม่พบตาราง default-layout ใดๆ (`tb_dashboard_personal_widget` ไม่มีแนวคิด seed/default — กริดของผู้ใช้แต่ละคนเริ่มต้นว่างเปล่า); การเพิ่ม action reset จะต้องสร้างฟีเจอร์ backend ใหม่ |
| ทำไม drag-and-drop บางครั้ง revert? | การเรียงใหม่เป็นแบบ optimistic — TanStack Query cache อัปเดตทันที จากนั้น PATCH requests ทำงาน ถ้า PATCH ใดล้มเหลวจะแสดง toast error; cache จะไม่ revert อัตโนมัติในเวอร์ชันนี้ |
| `order_index` เก็บที่ไหน? | ในตาราง backend ที่อยู่เบื้องหลัง `GET /api/proxy/api/me/dashboard-widgets` widget record แต่ละรายการมี field `order_index` ที่เพิ่มทีละ 10 ต่อ slot |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Workspace โหลดแต่ไม่แสดง widget | ผู้ใช้ยังไม่มี widget ที่บันทึกไว้ | คลิก "+ Add widget" เพื่อปักหมุด dataset อย่างน้อยหนึ่งรายการ |
| picker "+ Add widget" แสดงรายการว่าง | ไม่มี dataset ใน catalog หรือ shape ที่รองรับทั้งหมดถูกปักหมุดแล้ว | ตรวจสอบกับ admin ว่า dataset ถูก seed แล้วหรือไม่; ดู `system-config/dashboard-dataset` |
| Widget card แสดง error state | Dataset fetch คืน non-200 หรือ dataset ถูกลบ | ลบ widget แล้วเพิ่มใหม่จาก picker; รายงาน dataset ที่หายไปให้ admin |
| Drag-and-drop ไม่ทำงาน | Pointer เลื่อนน้อยกว่า 6 px ก่อน release (activation constraint) | กด drag อย่างน้อย 6 px ก่อน release เพื่อเริ่ม drag |
| ลำดับ revert หลัง refresh | PATCH request ล้มเหลวเงียบๆ | ตรวจ browser console สำหรับ toast error; backend อาจมี validation error บน `order_index` |

---

## 5. แหล่งข้อมูล (Dev)

- **รายการ widget ที่บันทึกไว้** — `GET /api/proxy/api/me/dashboard-widgets` → `WidgetConfigListResponse { items: WidgetConfig[], count }` Hook: `useMyDashboardWidgets` (`hooks/use-my-dashboard-widgets.ts`)
- **สร้าง widget** — `POST /api/proxy/api/me/dashboard-widgets` พร้อม `{ dataset_id, widget_type, title? }` Hook: `useCreateMyDashboardWidget`
- **อัปเดต widget** — `PATCH /api/proxy/api/me/dashboard-widgets/:id` พร้อม `{ order_index? | title? }` Hook: `useUpdateMyDashboardWidget`
- **ลบ widget** — `DELETE /api/proxy/api/me/dashboard-widgets/:id` Hook: `useDeleteMyDashboardWidget`
- **Dataset catalog** (picker) — component `LookupDataset` query dataset catalog กรองตาม shape
- **ตาราง backend:** `tb_dashboard_personal_widget` (tenant schema, ~บรรทัด 6205) — `id`, `user_id`, `dataset_id`, `widget_type` (`enum_dashboard_widget_type`: `kpi`/`line`/`area`/`bar`/`pie`/`heatmap`/`gauge`/`table`/`sparkline`), `title`, `order_index`, `params` (JSONB), `doc_version`, คอลัมน์ audit มาตรฐาน scope ด้วย `user_id`, soft-delete ผ่าน `deleted_at` ให้บริการโดย `DashboardPersonalWidgetService`/`DashboardPersonalWidgetController` ของ `micro-cluster` (TCP `dashboard-personal-widget.*`) หน้าด่านโดย `DashboardPersonalWidgetsController` ของ `backend-gateway` ที่ `api/me/dashboard-widgets` ไม่มี default/seed layout — ผู้ใช้ใหม่เริ่มต้นด้วยกริดว่างเปล่า

## 6. จังหวะการ Refresh

- **รายการ widget** — `CACHE_DYNAMIC` (TanStack Query, staleTime 1 min) Refetch on focus; ไม่ poll
- **ข้อมูล widget** — fetch ต่อ `dataset_id` เมื่อ card mount; cadence ขึ้นอยู่กับ dataset definition
- **เรียงใหม่** — optimistic cache update เมื่อ drag-end จากนั้น PATCH ทำงาน; ไม่ต้อง refresh อย่างชัดเจน

## 7. โมดูลที่เกี่ยวข้อง

- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — เอกสาร data-model สำหรับระบบ widget (dataset shape, widget type, DB schema)
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — admin UI สำหรับ curate dataset catalog ที่ใช้ใน picker
- [dashboard/my-pending](/th/inventory/dashboard/my-pending), [dashboard/my-approval](/th/inventory/dashboard/my-approval) — **ข้อมูลเชิงประวัติศาสตร์เท่านั้น**; หน้าเหล่านี้ document section widget แยกต่างหากที่ไม่เคยถูก render บนหน้านี้เลย (dead code ถูกลบเมื่อ 2026-06-27) — ดู [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) สำหรับ approval inbox ที่ live จริง
- [dashboard/pr](/th/inventory/dashboard/pr), [dashboard/main](/th/inventory/dashboard/main) — **ข้อมูลเชิงประวัติศาสตร์เท่านั้น**; document ไฟล์ demo ที่ถูกลบเมื่อ 2026-06-27 ไม่เคยถูก route

## 8. แหล่งข้อมูลอ้างอิง

- **Route:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard.route.tsx`
- **Composition:** `../carmen-inventory-frontend-react/routes/dashboard/dashboard-component.tsx` (flatten ออกจาก `_components/` โดย cleanup เมื่อ 2026-06-27, commit `03891e3d`)
- **Sortable item:** `../carmen-inventory-frontend-react/routes/dashboard/sortable-widget-item.tsx`
- **Hooks:** `../carmen-inventory-frontend-react/hooks/use-my-dashboard-widgets.ts` — `useMyDashboardWidgets`, `useCreateMyDashboardWidget`, `useUpdateMyDashboardWidget`, `useDeleteMyDashboardWidget`
- **Types:** `../carmen-inventory-frontend-react/types/dashboard-widget.ts` — `WidgetConfig`, `WidgetConfigListResponse`, `DatasetShape`, `WidgetType`
- **API constants:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` → `MY_DASHBOARD_WIDGETS`, `MY_DASHBOARD_WIDGET_BY_ID`
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/dashboard-widget/dashboard-personal-widget.service.ts` + `.controller.ts`; gateway route ใน `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/dashboard-widgets/dashboard-personal-widgets.controller.ts`
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dashboard_personal_widget` (~บรรทัด 6205), `tb_dashboard_bu_widget` (~บรรทัด 6185), `enum_dashboard_widget_type` (~บรรทัด 6162)
- **Backend design:** `../carmen-turborepo-backend-v2/docs/superpowers/archive/widget/2026-05-12-widget-backend-design.md`
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md` _(historical; this spec lived in the legacy Next.js frontend repo and was not carried over to -react)_
