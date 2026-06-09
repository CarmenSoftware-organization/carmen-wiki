---
title: ที่ตั้ง / สถานที่ (Location)
description: สถานที่จัดเก็บและบริโภคที่จำแนกเป็น inventory, direct หรือ consignment — ขับเคลื่อนการ post สต๊อกและพฤติกรรมการ physical count
published: true
date: 2026-06-09T16:28:56.000Z
tags: master-data, location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ที่ตั้ง / สถานที่ (Location)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_location` &nbsp;·&nbsp; **ใช้โดย:** inventory, GRN, SR, physical count, spot check, PR/PO &nbsp;·&nbsp; `location_type` (`inventory` / `direct` / `consignment`) ตัดสินพฤติกรรมการ posting

![ที่ตั้ง / สถานที่ (Location) screen](/screenshots/master-data/location.png)

![ที่ตั้ง / สถานที่ (Location) detail screen](/screenshots/master-data/location-detail.png)

## 1. คืออะไร / ใครใช้

**สถานที่** เป็นที่อยู่ทางกายภาพหรือทางตรรกะที่สต๊อกอยู่หรือถูกบริโภค — main warehouse, kitchen pass, bar, housekeeping cart, ชั้น consignment ที่ supplier เป็นเจ้าของ ฟิลด์ `location_type` ตัดสินพฤติกรรมการ posting:

- **`inventory`** — มียอดสต๊อก, post ไป inventory asset GL
- **`direct`** — ข้าม balance, post ตรงไป department expense
- **`consignment`** — ถือสินค้าที่ supplier เป็นเจ้าของ, recognise เมื่อบริโภคเท่านั้น

ระเบียนเดียวกันตั้งค่าพฤติกรรมการนับสิ้นงวด (`physical_count_type` = `yes` / `no`) และจุดส่งของ default ที่ส่งเข้ามายัง location นี้ **บริหารจัดการโดย** Product Admin **อ่านโดย** ทุกเส้นทางการ post inventory

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่ม location | Configuration → Master Data → Location → **New** | บังคับ: `code`, `name`, `location_type` |
| Tag จุดส่งของ default | Location detail | ตั้ง `delivery_point_id` + denormalised `delivery_point_name` |
| ตั้งพฤติกรรมการนับ | Toggle `physical_count_type` | `no` ข้าม period-end count; spot check ยังบังคับใช้ |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker; การ post ประวัติยังเก็บไว้ |
| เปลี่ยน `location_type` | Edit dialog | **บล็อกหลังการเคลื่อนไหวครั้งแรก** — จะทำให้ประวัติ journal เสียหาย |
| กำหนด inventory tree | หน้า location detail | จำกัดว่าสินค้าใดที่มองเห็นได้ที่ location นี้ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code already in use" | `code` ซ้ำในแถว active | เลือก code อื่น |
| "Cannot delete — non-zero balance" | location ยังมีสต๊อก | จ่ายออกหรือโอนก่อน |
| "Cannot delete — referenced by open SR/GRN" | FK references ในเอกสารเปิด | ปิดเอกสารก่อน |
| "Cannot change location_type" | พยายามแก้หลังการเคลื่อนไหวครั้งแรก | สร้าง location ใหม่และย้ายด้วยมือ |
| ชื่อจุดส่งของล้าสมัย | snapshot `delivery_point_name` ไม่ได้ refresh | Save location ใหม่ หรือ run backfill |

## 4. Edge Cases

- **`location_type` ติดเมื่อใช้แล้ว** — การสลับ `inventory` → `direct` ทำให้ journal entry เสียหายย้อนหลัง
- **ยกเว้นการนับ** — `physical_count_type = no` ข้าม period count แต่ **ไม่** ข้าม spot check
- **ยอดคงเหลือ consignment** เป็นของ supplier; recognise ตอนบริโภค ไม่ใช่ตอนรับ
- **การจับคู่กับจุดส่งของ** — `delivery_point_name` เป็น denormalised, ต้อง refresh เมื่อมีการเปลี่ยนชื่อ
- **Code uniqueness บังคับใช้ระดับ app** (ไม่มี DB unique constraint)

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_location`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | รหัสสั้น เช่น `INV1`, `KIT` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `location_type` | `enum_location_type` | No | `inventory` (default), `direct` หรือ `consignment` |
| `description` | `String?` | Yes | Free text |
| `delivery_point_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_delivery_point` (เลือกได้) |
| `delivery_point_name` | `String? @db.VarChar` | Yes | สำเนาแสดงผลแบบ denormalised |
| `physical_count_type` | `enum_physical_count_type` | No | `no` (default) — ข้าม; `yes` — รวม |
| `is_active` | `Boolean?` | Yes | Active flag |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** primary key บน `id` FK บน `delivery_point_id` → `tb_delivery_point` `onDelete: NoAction` Uniqueness บน `code` บังคับใช้ที่ app layer

`enum_location_type` values: `inventory`, `direct`, `consignment`
`enum_physical_count_type` values: `no`, `yes`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว active (app-enforced)
- **Deletion guards** ยอด non-zero หรือการอ้างอิง SR/GRN ที่เปิดอยู่บล็อกการลบ
- **Validation** `location_type` ไม่สามารถเปลี่ยนได้หลังการเคลื่อนไหวครั้งแรก
- **Lifecycle** `is_active = false` ซ่อนจาก picker; รักษาการ post ประวัติ
- **ยกเว้นการนับ** `physical_count_type = no` ข้าม period count ไม่ใช่ spot check
- **การจับคู่กับจุดส่งของ** Refresh snapshot `delivery_point_name` เมื่อมีการเปลี่ยนชื่อ

## 7. การอ้างอิงข้ามโมดูล

- [inventory](/th/inventory/inventory) — ทุกยอดสต๊อก keyed ด้วย location; type ตัดสินว่าจะ track balance หรือไม่
- [good-receive-note](/th/inventory/good-receive-note) — บรรทัด detail ของ GRN เป้าหมาย location ปลายทาง; type ขับเคลื่อน journal entry
- [store-requisition](/th/inventory/store-requisition) — `from_location` / `to_location` ในทุก issue/transfer
- [physical-count](/th/inventory/physical-count) — การนับ scope ไปยัง location ที่ `physical_count_type = yes`
- [spot-check](/th/inventory/spot-check) — เซสชัน enumerate location
- [purchase-request](/th/inventory/purchase-request) และ [purchase-order](/th/inventory/purchase-order) — บรรทัด detail อาจบรรจุ location ปลายทาง

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location` (lines ~1294-1393), `enum_location_type` (lines ~218-222), `enum_physical_count_type` (lines ~62-65)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/location/`
- **carmen/docs:** `../carmen/docs/settings/locations.md` — wireframes
