---
title: จุดส่งของ (Delivery Point)
description: จุดส่งของทางกายภาพสำหรับการจัดส่งของผู้ขาย — ถูกอ้างอิงโดย PO และ GRN และเชื่อมโยงกับ inventory location
published: true
date: 2026-05-17T12:00:00.000Z
tags: master-data, delivery-point, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# จุดส่งของ (Delivery Point)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_delivery_point` &nbsp;·&nbsp; **ใช้โดย:** PO, GRN, locations &nbsp;·&nbsp; ที่อยู่ทางกายภาพสำหรับ drop-off ของผู้ขาย

## 1. คืออะไร / ใครใช้

**จุดส่งของ** คือที่อยู่ทางกายภาพที่ผู้ขายส่งสินค้ามา — loading dock, ทางเข้าหลังครัว, ช่องรับของของไซต์ระยะไกล PO บรรจุจุดส่งของเพื่อให้ผู้ขายรู้ว่าจะ drop ที่ไหน; GRN บันทึกจุดรับจริง; และ inventory **location** สามารถ tag จุดส่งของ default เพื่อให้ GRN routing มีปลายทางที่สมเหตุสมผล

โดยทั่วไป property จะมีจุดส่งของไม่กี่จุด (Main Dock, Banquet Dock, Spa Receiving) ไม่ว่าจะมี inventory location ปลายน้ำกี่แห่งก็ตาม **บริหารจัดการโดย** Product Admin; **อ่านโดย** developer และ tester ใน PO / GRN routing

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มจุดส่งของ | Configuration → Master Data → Delivery Point → **New** | บังคับ: `name` |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker PO/GRN; เอกสารย้อนหลังยัง resolve ได้ |
| Tag default ของ location | รายละเอียดของ [[master-data/location]] | ตั้ง `tb_location.delivery_point_id` |
| Override บน GRN | ฟิลด์ header ของ GRN | GRN inherit จาก PO แต่อาจ override ตอนรับ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่น |
| "Name required" | `name` ว่าง | เพิ่มชื่อแสดงผล |
| "Cannot delete — referenced by POs / GRNs / locations" | มี FK references | ใช้ inactivate แทน |
| Location แสดงชื่อจุดส่งของล้าสมัย | snapshot `tb_location.delivery_point_name` ไม่ได้ refresh หลังเปลี่ยนชื่อ | Backfill ผ่าน maintenance job |

## 4. Edge Cases

- **การ propagate การเปลี่ยนชื่อ** เอกสารเก็บ FK ดังนั้นการแสดงผล refresh อัตโนมัติ Location ที่ **snapshot ชื่อ** (`tb_location.delivery_point_name`) ต้อง backfill ถ้าต้องการให้การเปลี่ยนชื่อแสดงบน legacy lookup
- **การ inactivate** ซ่อนจาก picker แต่ปล่อยให้การอ้างอิงประวัติ resolve ได้
- **ไม่มีฟิลด์ code** — มีเพียง `name` ที่เป็น identity ที่นี่

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_delivery_point`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `Main Dock`) |
| `is_active` | `Boolean?` | Yes | Active flag, default `true` |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `deliverypoint_name_u` Index บน `name` Reverse relations ไปยัง `tb_location`, `tb_purchase_request_detail` และตาราง PO-PR linkage

## 6. กติกาทางธุรกิจ

- **Uniqueness** `name` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards** การอ้างอิงจาก PO, GRN ที่เปิดอยู่ หรือ location ที่ active บล็อก hard-delete
- **Validation** `name` บังคับ
- **Lifecycle** จุดส่งของ inactive ยังอ่านได้บนเอกสารย้อนหลัง; ซ่อนจาก picker
- **การ propagate การเปลี่ยนชื่อ** เอกสาร resolve ผ่าน FK; snapshot ชื่อบน `tb_location` ต้อง backfill

## 7. การอ้างอิงข้ามโมดูล

- [[purchase-order]] — PO header บรรจุการอ้างอิงจุดส่งของ
- [[good-receive-note]] — GRN inherit จาก PO, อาจ override
- [[master-data/location]] — แต่ละ location tag จุดส่งของ default ได้
- [[purchase-request]] — PR detail อาจมี hint จุดส่งของที่ propagate ไปยัง PO

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_delivery_point` (lines ~623-646)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/delivery-point/`
