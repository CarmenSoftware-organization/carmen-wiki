---
title: ประเภทการปรับสต๊อก (Adjustment Type)
description: รหัสเหตุผลสำหรับการปรับสต๊อก stock-in / stock-out — ใช้โดย inventory adjustment, physical count และ spot check เพื่ออธิบาย variance
published: true
date: 2026-05-20T00:00:00.000Z
tags: master-data, adjustment-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ประเภทการปรับสต๊อก (Adjustment Type)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_adjustment_type` &nbsp;·&nbsp; **ใช้โดย:** inventory adjustment / physical count / spot check &nbsp;·&nbsp; รหัสเหตุผลสำหรับการเคลื่อนไหว stock-in / stock-out ทุกครั้ง

![ประเภทการปรับสต๊อก (Adjustment Type) screen](/screenshots/master-data/adjustment-type.png)

## 1. คืออะไร / ใครใช้

ประเภทการปรับสต๊อกจำแนก *ทำไม* ยอดสต๊อกจึงขึ้นหรือลง — write-off, write-on, spoilage, theft, count variance, transfer error ฯลฯ ทุก record `tb_stock_in` และ `tb_stock_out` บรรจุหนึ่งประเภท และรายงาน variance ปลายน้ำจัดกลุ่มตามเหตุผลเพื่อให้ controller เห็น pattern ตัว discriminator `type` (`stock_in` / `stock_out`) ทำให้ catalogue ถูก filter ตามทิศทางได้

**บริหารจัดการโดย** Product Admin **อ่านโดย** developer หรือ tester ที่ทำงานบน adjustments, physical count หรือเส้นทางการ posting ของ spot check

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มเหตุผลใหม่ | Configuration → Master Data → Adjustment Type → **New** | ตั้ง `code`, `name` และ `type` (`stock_in` หรือ `stock_out`) |
| ยกเลิกการใช้งานเหตุผล | หน้าเดียวกัน → toggle `is_active` | แถวประวัติยัง resolve ชื่อ; ซ่อนจาก picker ใหม่ |
| แก้ description | Edit dialog | `code`, `name`, `type` ไม่ควรเปลี่ยนหลังใช้ครั้งแรก |
| ตรวจสอบว่า posting ใช้เหตุผลใด | เปิด record stock-in/out ดูฟิลด์เหตุผล | Snapshot ผ่าน FK |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code already in use" | `code` ซ้ำบนแถว non-deleted | เลือก code อื่นหรือ reactivate แถวที่มี |
| "Type required" | Form ส่งโดยไม่มี `stock_in` / `stock_out` | เลือกทิศทาง — UI filter ตามมัน |
| "Cannot delete — referenced by postings" | มี record stock-in/out อย่างน้อยหนึ่งชี้ไปยังเหตุผลนี้ | ใช้ inactivate แทน |
| "Type cannot be changed" | พยายามพลิก `stock_in` ↔ `stock_out` หลังใช้ | สร้างเหตุผลใหม่ในทิศทางที่ถูกต้อง |

## 4. Edge Cases

- **การพลิกทิศทางหลังใช้** ทำลายรายงานประวัติ — ระบบปฏิเสธ
- **การลบเหตุผลที่ถูกอ้างอิง** ถูกบล็อก; soft-delete ก็ปล่อยให้แถวประวัติ resolve ได้
- **การ filter ทิศทาง** อยู่ที่ picker — หน้า stock-in ไม่เห็นแถว `stock_out` และในทางกลับกัน

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_adjustment_type`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | รหัสสั้น (เช่น `SPOIL`, `THEFT`, `WO`) |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล |
| `type` | `enum_adjustment_type` | No | `stock_in` หรือ `stock_out` |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `is_active` | `Boolean?` | Yes | Active flag |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])` map `AT1_code_u` Index บน `code` Reverse relations ไปยัง `tb_stock_in` และ `tb_stock_out`

`enum_adjustment_type` values: `stock_in`, `stock_out` (ผู้ใช้เห็น — ปรากฏใน picker นี้) บวก `eop_in`, `eop_out` (system-reserved สำหรับ engine rollforward ของ period-end — ไม่แสดงในที่นี่) ดู [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 4 สำหรับ enum เต็ม

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards** เหตุผลที่ถูกอ้างอิงโดย stock-in/out ที่ posted ไม่สามารถ hard-delete — ใช้ inactivate
- **Validation** `code`, `name`, และ `type` บังคับ `type` ไม่สามารถพลิกหลังใช้ครั้งแรก
- **Lifecycle** เหตุผล inactive ยังอ่านได้บน adjustment ประวัติ; ซ่อนจาก picker adjustment ใหม่
- **การ filter ทิศทาง** UI picker filter ตาม `type` — discriminator ไม่ต้อง re-filter ปลายน้ำ

## 7. การอ้างอิงข้ามโมดูล

- [inventory-adjustment](/th/inventory/inventory-adjustment) — ทุกบรรทัด adjustment บรรจุ FK ของ adjustment type
- [physical-count](/th/inventory/physical-count) — variance write-on / write-off post กับ adjustment type
- [spot-check](/th/inventory/spot-check) — variance ของ spot check ใช้เส้นทาง posting เดียวกัน

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_adjustment_type` (lines ~2569-2594), `enum_adjustment_type` (lines ~2564-2567)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/adjustment-type/`
