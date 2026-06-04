---
title: Widget Workspace แดชบอร์ด (Widget Workspace Dashboard)
description: แดชบอร์ด production จริงที่ /dashboard — workspace แบบ drag-and-drop ส่วนตัว ที่ผู้ใช้แต่ละคนปักหมุด widget KPI, pie และ bar จาก dataset catalog ของระบบ
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, widget-workspace, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget Workspace แดชบอร์ด (Widget Workspace Dashboard)

> **At a Glance**
> **Route:** `/dashboard` &nbsp;·&nbsp; **สำหรับ:** ทุก role ของผู้ปฏิบัติงานหลังเข้าระบบ &nbsp;·&nbsp; **สถานะ:** **Live** — ขับเคลื่อนด้วย API จริง; เนื้อหา dataset ขึ้นอยู่กับการ seed ฝั่ง backend &nbsp;·&nbsp; **ขอบเขต:** ส่วนบุคคล — layout widget ที่ user แต่ละคนบันทึกไว้

## 1. คืออะไรและสำหรับใคร

Widget Workspace คือ **แดชบอร์ด production จริง** ที่โหลดขึ้นมาเมื่อผู้ใช้ navigate ไปยัง `/dashboard` เป็นตัวแทนของหน้า mock-data แบบ static (เช่น `/dashboard/pr`, `/dashboard/po` ฯลฯ ซึ่งยังคงอยู่เป็น domain view แยกต่างหาก) หน้านี้ render กริด widget แบบ drag-and-drop ส่วนตัว โดยแต่ละ widget ผูกกับ dataset จาก system catalog

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
| `categorical` | Pie / bar chart card |

**กลุ่มผู้ใช้**

- **ผู้ใช้ที่เข้าระบบทุกคน** — ทุก operator สร้าง workspace ของตัวเอง ไม่มี layout ตายตัว workspace เริ่มว่างเปล่าและเติบโตเมื่อผู้ใช้ปักหมุด widget
- **นักพัฒนา** — compositing layer คือ `dashboard-component.tsx`; การ render widget จัดการโดย `AppTile` / `SortableWidgetItem`

## 2. Tile และการ Drill-down

ต่างจากแดชบอร์ดโดเมนแบบมีชื่อ (pr, po, grn…) Widget Workspace ไม่มีชุด tile ตายตัว กริดเป็น dynamic ทั้งหมด:

| Widget Card | แหล่งข้อมูล | เพิ่มผ่าน |
|---|---|---|
| Dataset `scalar` / `scalar_delta` ใดก็ได้ | `GET /api/proxy/api/me/dashboard-widgets` คืนรายการที่บันทึกไว้; ข้อมูลแต่ละรายการ fetch ด้วย `dataset_id` | picker "+ Add widget" |
| Dataset `categorical` ใดก็ได้ | endpoint เดียวกัน, render เป็น pie/bar | picker "+ Add widget" |

Drill-down จาก widget card ขึ้นอยู่กับ dataset definition และไม่ได้ถูกกำหนดตายตัวโดย workspace เอง สีของ tile ตาม dataset category และ module-color-map convention

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไมหน้าแสดง greeting แทนที่จะเป็น tile? | Workspace โหลดรายการ widget ที่บันทึกไว้ของผู้ใช้ — ถ้าว่างจะแสดง empty-state เพิ่ม widget อย่างน้อยหนึ่งรายการผ่าน picker "+ Add widget" |
| dataset ที่ใช้ได้มาจากไหน? | picker "Add widget" เรียก `LookupDataset` ซึ่ง query dataset catalog dataset ถูกนิยามและ seed โดย backend ดู [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) |
| นี่คือสิ่งเดียวกับแดชบอร์ด PR / PO / GRN ใน sidebar หรือเปล่า? | ไม่ใช่ หกหน้านั้น (`/dashboard/pr` ฯลฯ) คือ **หน้า mock แยกตามโดเมน** (pipeline + ตาราง) workspace นี้คือ **กริด widget ส่วนตัว live** บน route `/dashboard` |
| ฉันสามารถ reset layout ไปยังค่าเริ่มต้นได้ไหม? | ยังไม่เปิดให้ใช้ใน UI Backend เก็บตาราง `tb_widget_default_layout` พร้อม seed item ต่อ scope; action reset-to-default สามารถเพิ่มเป็น endpoint ในอนาคต |
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
- **ตาราง backend:** `tb_widget_dashboard` (dashboard container), `tb_widget_dashboard_item` (per-slot item พร้อม `sort_order`, `type`, `config`) Personal scope: `created_by_id = current_user` Default seed layout: `tb_widget_default_layout` (scope = `personal`)

## 6. จังหวะการ Refresh

- **รายการ widget** — `CACHE_DYNAMIC` (TanStack Query, staleTime 1 min) Refetch on focus; ไม่ poll
- **ข้อมูล widget** — fetch ต่อ `dataset_id` เมื่อ card mount; cadence ขึ้นอยู่กับ dataset definition
- **เรียงใหม่** — optimistic cache update เมื่อ drag-end จากนั้น PATCH ทำงาน; ไม่ต้อง refresh อย่างชัดเจน

## 7. โมดูลที่เกี่ยวข้อง

- [reporting-audit/widget](/th/inventory/reporting-audit/widget) — เอกสาร data-model สำหรับระบบ widget (dataset shape, widget type, DB schema)
- [system-config/dashboard-dataset](/th/inventory/system-config/dashboard-dataset) — admin UI สำหรับ curate dataset catalog ที่ใช้ใน picker
- [dashboard/my-pending](/th/inventory/dashboard/my-pending) — section เพิ่มเติมบน `/dashboard` แสดงจำนวน pending ส่วนตัว
- [dashboard/my-approval](/th/inventory/dashboard/my-approval) — section เพิ่มเติมบน `/dashboard` แสดงคิวงานอนุมัติส่วนตัว
- [dashboard/pr](/th/inventory/dashboard/pr) — แดชบอร์ด PR แบบ mock แยกตามโดเมน (route แยก)
- [dashboard/main](/th/inventory/dashboard/main) — แดชบอร์ด landing ข้ามโดเมน

## 8. แหล่งข้อมูลอ้างอิง

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-component.tsx`
- **Sortable item:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/sortable-widget-item.tsx`
- **Hooks:** `../carmen-inventory-frontend/hooks/use-my-dashboard-widgets.ts` — `useMyDashboardWidgets`, `useCreateMyDashboardWidget`, `useUpdateMyDashboardWidget`, `useDeleteMyDashboardWidget`
- **Types:** `../carmen-inventory-frontend/types/dashboard-widget.ts` — `WidgetConfig`, `WidgetConfigListResponse`, `DatasetShape`, `WidgetType`
- **API constants:** `../carmen-inventory-frontend/constant/api-endpoints.ts` → `MY_DASHBOARD_WIDGETS`, `MY_DASHBOARD_WIDGET_BY_ID`
- **Backend design:** `../carmen-turborepo-backend-v2/docs/superpowers/archive/widget/2026-05-12-widget-backend-design.md`
- **Widget rewrite spec:** `../carmen-inventory-frontend/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md`
