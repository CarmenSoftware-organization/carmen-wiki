---
title: Widget
description: เอนทิตีประกอบ dashboard — dashboard ต่อผู้ใช้ / ต่อ BU, layout default และ workspace ส่วนตัวสำหรับ query ที่บันทึกไว้
published: true
date: 2026-05-17T12:00:00.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

> **At a Glance**
> **เจ้าของ:** ผู้ใช้ปลายทาง (ส่วนตัว) + BU admin (BU) + Sysadmin (default) &nbsp;·&nbsp; **ตาราง:** `tb_widget_dashboard` (+ `tb_widget_default_layout`, `tb_widget_workspace`) &nbsp;·&nbsp; **ใช้โดย:** renderer ของ dashboard + panel data-explorer &nbsp;·&nbsp; Dashboard, seed layout, query ที่บันทึก

## 1. ภาพรวมและผู้ใช้งาน

เอนทิตี widget ขับเคลื่อน **ชั้น dashboard** — multi-table เพราะ dashboard แก้ปัญหาที่เกี่ยวข้องสามอย่าง: ประกอบ dashboard ที่ scope ส่วนตัวหรือ BU ออกจาก tile, seed ผู้ใช้ใหม่ด้วย default ที่สมเหตุสมผล และให้ผู้ใช้บันทึก query ที่ใช้ซ้ำได้

- `tb_widget_dashboard` — header ของ dashboard; `scope` (`personal` หรือ `bu`) ตัดสินการมองเห็น; item อยู่ในตารางพี่น้อง `tb_widget_dashboard_item`
- `tb_widget_default_layout` — หนึ่งแถวต่อ scope; `items` JSON อธิบาย seed layout สำหรับผู้ใช้ใหม่ / dashboard BU ใหม่
- `tb_widget_workspace` — query ที่บันทึกต่อผู้ใช้; surface ใน panel data-explorer และอาจถูกอ้างอิงจาก tile ของ dashboard

**ดูแลโดย** ผู้ใช้ปลายทาง (dashboard ส่วนตัว + workspace), BU admin (dashboard BU), Sysadmin (default) **อ่านโดย** ชั้น dashboard และ data-explorer

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม tile ไป dashboard | Dashboard → Edit → Add tile | เขียนแถว `tb_widget_dashboard_item` พี่น้อง |
| เปลี่ยนขนาด / จัดเรียง tile | drag handle ในโหมด edit | `w`, `h` (grid unit) + `sort_order` |
| บันทึก query data-explorer | data explorer → Save as workspace | แถว `tb_widget_workspace` ต่อผู้ใช้ |
| ตั้ง default layout สำหรับผู้ใช้ใหม่ | Sysadmin → Dashboard Defaults → `personal` | แก้ JSON payload |
| สร้าง dashboard BU | Dashboard → New, scope = `bu` | เห็นได้โดยสมาชิก BU ทุกคน |
| Soft-delete dashboard | เมนู Dashboard → Delete | Item คงไว้; reap โดย GC หลัง retention |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ผู้ใช้ไม่เห็น dashboard ส่วนตัว | `created_by_id` ผิด | dashboard ส่วนตัวกรองตามผู้ใช้ปัจจุบัน |
| Dashboard BU มองไม่เห็นโดยผู้ใช้ | ผู้ใช้ไม่เป็นสมาชิก BU | grant ผ่าน [[access-control/business-unit-user]] |
| Workspace query ถูก reject | รูปแบบผิด (ไม่ใช่ structured filter doc) | ใช้ภาษา structured filter; ไม่รับ raw SQL |
| ผู้ใช้ใหม่เห็น default เก่า | Default layout ถูกแก้หลัง seed | ผู้ใช้ใหม่ได้ default ปัจจุบัน; dashboard ที่ materialise แล้วไม่ถูกแตะ |

## 4. กรณีพิเศษ

- **การ seed default** Materialise เป็น `tb_widget_dashboard` จริงครั้งแรกที่ผู้ใช้แก้ tile ใด ๆ
- **ไม่มี soft-delete บน default layout** — `tb_widget_default_layout` ถูกเขียนทับในที่; เฉพาะฟิลด์ audit `updated_*`
- **ไม่มี surface การแชร์ workspace** ใน schema ปัจจุบัน — workspace เป็นต่อผู้ใช้อย่างเข้มงวด
- **Semantic ของ accent** เป็นเรื่อง cosmetic ล้วน ๆ

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_widget_dashboard`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `label` | `String @db.VarChar(48)` | No | ชื่อแสดงผล |
| `scope` | `enum_widget_dashboard_scope` | No | `personal` หรือ `bu` |
| `accent` | `enum_widget_accent?` | Yes | `muted`, `primary`, `success`, `warning`, `destructive`, `info` |
| `created_*` / `updated_*` / `deleted_*` | — | Mixed | audit มาตรฐาน |

**Relations:** has-many `tb_widget_dashboard_item` (พี่น้อง) **Indexes:** `(scope, deleted_at)`, `(created_by_id, scope)`

### 5.2 `tb_widget_default_layout`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `scope` | `enum_widget_dashboard_scope` | No | Primary key — หนึ่งแถวต่อ scope |
| `items` | `Json @db.JsonB` | No | seed layout (array ของ item descriptor) |
| `created_at` / `updated_at` / `updated_by_id` | — | Mixed | audit จำกัด (ไม่มีผู้สร้าง / ไม่มี soft-delete) |

### 5.3 `tb_widget_workspace`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar(48)` | No | ชื่อแสดงผล |
| `query` | `String @db.Text` | No | query body ที่เก็บ (structured filter doc) |
| คอลัมน์ audit | — | Mixed | มาตรฐาน |

**Indexes:** `(created_by_id, created_at)`, `(created_by_id, deleted_at)`

**Enums:** `enum_widget_dashboard_scope`: `personal`, `bu` `enum_widget_accent`: `muted`, `primary`, `success`, `warning`, `destructive`, `info`

## 6. กติกาทางธุรกิจ

- **การมองเห็นตาม scope** `personal` เห็นได้เฉพาะผู้สร้าง; `bu` เห็นได้โดยสมาชิก BU ทุกคน แอปบังคับทั้งสองการตรวจสอบก่อนแสดงรายการ
- **การ seed default** ผู้ใช้ใหม่ที่ไม่มี dashboard ส่วนตัวเห็น `tb_widget_default_layout[personal]`; materialise ตอนแก้ครั้งแรก
- **Soft-delete บน dashboard/workspace** Item คงในตารางพี่น้อง; reap โดย GC หลัง retention
- **ไม่มี soft-delete บน default layout** เขียนทับในที่; มีสองแถวเสมอ
- **การจัดลำดับ item** ตารางพี่น้อง; `sort_order` + grid 12 คอลัมน์
- **รูปแบบ query ของ workspace** Structured filter doc เท่านั้น; raw SQL ถูก reject ที่ชั้น API
- **Accent เป็น cosmetic**

## 7. ความเชื่อมโยงข้ามโมดูล

- [[access-control/user]] — เจ้าของ dashboard ส่วนตัวและ workspace
- [[master-data/business-unit]] — จำกัดการมองเห็น scope `bu`
- [[reporting-audit/report]] — `config` ของ tile อาจฝัง `report_template_id`
- [[reporting-audit/activity]] — การแก้ dashboard ถูก log
- โมดูลธุรกรรมทั้งหมด — แหล่งข้อมูลทั่วไปของ tile

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_widget_dashboard` (lines ~5727-5744), `tb_widget_workspace` (lines ~5787-5801), `tb_widget_default_layout` (lines ~5803-5809), enums (lines ~5713-5725)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/dashboard/`; panel data-explorer สำหรับ workspace
