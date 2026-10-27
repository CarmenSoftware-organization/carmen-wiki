---
title: ประเภทการปรับสต๊อก (Adjustment Type)
description: รหัสเหตุผลสำหรับการปรับสต๊อก stock-in / stock-out — ใช้โดยการ posting แบบ manual ของโมดูล inventory-adjustment เท่านั้น; physical count และ spot check ไม่ได้ตั้งค่านี้
published: true
date: '2026-10-27T15:00:00.000Z'
tags: master-data, adjustment-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ประเภทการปรับสต๊อก (Adjustment Type)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_adjustment_type` &nbsp;·&nbsp; **ใช้โดย:** เฉพาะฟอร์ม Stock-In / Stock-Out แบบ manual ของโมดูล inventory-adjustment — เป็น FK ที่ nullable ถูกปล่อย `null` โดย physical count และไม่เคยถูกแตะโดย spot check &nbsp;·&nbsp; รหัสเหตุผลสำหรับการเคลื่อนไหว stock-in / stock-out ที่กรอกด้วยมือ

![ประเภทการปรับสต๊อก (Adjustment Type) screen](/screenshots/master-data/adjustment-type.png)

## 1. คืออะไร / ใครใช้

ประเภทการปรับสต๊อกจำแนก *ทำไม* ยอดสต๊อกจึงขึ้นหรือลง — write-off, write-on, spoilage, theft, transfer error ฯลฯ `adjustment_type_id` บน `tb_stock_in` / `tb_stock_out` เป็น **nullable** และในทางปฏิบัติจะถูกกรอกโดยฟอร์ม Stock-In / Stock-Out แบบ manual ของโมดูล [inventory-adjustment](/th/inventory/inventory-adjustment) เท่านั้น ซึ่งบังคับให้เลือกเหตุผล ตัว discriminator `type` (`stock_in` / `stock_out`) ทำให้ catalogue ถูก filter ตามทิศทางได้ที่นั่น

**ไม่ใช่เหตุผลการ posting แบบสากล (ยืนยันในรอบนี้)** variance rollup ของ [physical-count](/th/inventory/physical-count) สร้างแถว `tb_stock_in`/`tb_stock_out` โดยตรงตอน submit แต่ไม่เคยตั้ง `adjustment_type_id` — ค่ายังเป็น `null` ในทุกแถวที่โมดูลนั้นสร้าง [spot-check](/th/inventory/spot-check) ยิ่งง่ายกว่านั้นอีก: `submit()` ของมันไม่สร้างแถว `tb_stock_in`/`tb_stock_out` เลย จึงไม่แตะตารางนี้เลยไม่ว่าทางใด มีเพียงการ posting ของโมดูล inventory-adjustment เองเท่านั้นที่มีรหัสเหตุผลจริง

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
| `ADJUSTMENT_TYPE_ALREADY_EXISTS` (catalog; dialog แสดงใต้ **Code**) | `code` ซ้ำบนแถว non-deleted | เลือก code อื่นหรือ reactivate แถวที่มี |
| "Type required" | Form ส่งโดยไม่มี `stock_in` / `stock_out` | เลือกทิศทาง — UI filter ตามมัน |
| **ยังไม่ยืนยัน** — ไม่พบ guard สำหรับการลบหรือการเปลี่ยน type | อ่านโค้ด `adjustment-type.service.ts`'s `delete()` และ `update()` โดยตรงในรอบนี้ พบว่า**ไม่มี**การเช็ค stock-in/out ที่อ้างอิงอยู่ก่อน soft-delete และ**ไม่มี**การเช็คที่กัน `type` ไม่ให้เปลี่ยนตอน `update()` — `...data` ถูก spread ตรงเข้า Prisma update โดยมีแค่การเช็ค code-uniqueness เท่านั้น | ถือว่า "cannot delete — referenced by postings" และ "type cannot be changed" **ยังไม่ถูกบังคับใช้** จนกว่าจะตรวจสอบซ้ำ — การ inactivate หรือเปลี่ยนทิศทางของเหตุผลที่ใช้อยู่แล้วจะสำเร็จในปัจจุบัน |

## 4. Edge Cases

- **การพลิกทิศทางหลังใช้ทำได้ในปัจจุบัน** ไม่มีโค้ดใดบล็อกไว้ — `update()` ยอมรับ `type` ใหม่บนแถวที่ถูกอ้างอิงอยู่แล้ว การทำเช่นนี้จะทำลายรายงานที่อิงทิศทางของ posting เดิม; ถือว่าข้ออ้างเดิม "ระบบปฏิเสธ" ยังไม่ยืนยัน
- **การลบเหตุผลที่ถูกอ้างอิงสำเร็จในปัจจุบัน** `delete()` เป็น soft-delete แบบไม่มีเงื่อนไข (`is_active: false` + `deleted_at`) โดยไม่มีการเช็ค FK — แถวประวัติยัง resolve ชื่อผ่าน FK (ที่ soft-deleted) ได้เหมือนเดิม
- **บัญชี GL ต่อ adjustment type อยู่ที่อื่น** บัญชีที่การปรับสต๊อกไป post กำหนดต่อ location x item group x adjustment type ใน [chart-of-account-mapping](/th/inventory/master-data/chart-of-account-mapping) (แท็บ GL, `movement = adjustment`) ไม่ได้อยู่บนระเบียนนี้
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
| `chart_of_accounts_id` | `String? @db.Uuid` | Yes | hint บัญชีฝั่งตรงข้ามที่เพิ่มโดย `20261016140000_account_mapping_contra_defaults`; **ไม่มี FK** รับตอน create/update และ validate ว่าเป็นแถว [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) ที่ active และ postable (มิฉะนั้น `422 GL_ACCOUNT_NOT_POSTABLE`) **ไม่มีอะไรอ่านมัน:** resolver ของ account-mapping ตัด fallback ตาม adjustment-type ออก (commit `db3544c76`) และ frontend ถอด picker ออกอีกครั้ง (`bd572120`, "nothing reads it") ถือว่าเป็นซาก
| `is_active` | `Boolean?` | Yes | Active flag |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])` map `AT1_code_u` Index บน `code` Reverse relations ไปยัง `tb_stock_in` และ `tb_stock_out`

`enum_adjustment_type` values: `stock_in`, `stock_out` (ผู้ใช้เห็น — ปรากฏใน picker นี้) บวก `eop_in`, `eop_out` (system-reserved สำหรับ engine rollforward ของ period-end — ไม่แสดงในที่นี่) ดู [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) § 4 สำหรับ enum เต็ม

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards — ยังไม่ยืนยัน** ไม่พบการเช็ค FK ใน `delete()`; soft-delete สำเร็จโดยไม่มีเงื่อนไขแม้มี stock-in/out อ้างอิงอยู่
- **Validation** `code`, `name`, และ `type` บังคับตอนสร้าง `update()` ไม่ได้กันการเปลี่ยน `type` หลังใช้ครั้งแรก — ยืนยันว่า**ไม่มี** ไม่ใช่แค่ยังไม่ยืนยัน
- **Lifecycle** เหตุผล inactive ยังอ่านได้บน adjustment ประวัติ; ซ่อนจาก picker adjustment ใหม่
- **การ filter ทิศทาง** UI picker filter ตาม `type` — discriminator ไม่ต้อง re-filter ปลายน้ำ
- **Default sort** `GET /adjustment-types` ที่ไม่มี `?sort=` คืน `code:asc, name:asc, id:asc` (`adjustment-type.service.ts`, `withDefaultSort`, 2026-09-13)

## 7. การอ้างอิงข้ามโมดูล

- [inventory-adjustment](/th/inventory/inventory-adjustment) — ทุกบรรทัด Stock-In / Stock-Out แบบ manual บรรจุ FK ของ adjustment type; เป็นโมดูลเดียวที่ตั้งค่านี้จริง
- [physical-count](/th/inventory/physical-count) — variance rollup ของมันสร้างแถว `tb_stock_in`/`tb_stock_out` โดยตรง แต่**ไม่**ตั้ง `adjustment_type_id` (ยืนยันว่าเป็น `null` ทุกแถวที่มันสร้าง) — ไม่มีรหัสเหตุผล ไม่มีการเชื่อมกลับมาที่ตารางนี้
- [chart-of-account-mapping](/th/inventory/master-data/chart-of-account-mapping) — หนึ่งแถว GL mapping ต่อ adjustment type ที่ active
- [spot-check](/th/inventory/spot-check) — `submit()` ของมันไม่สร้างแถว `tb_stock_in`/`tb_stock_out` เลย จึงไม่เคยอ้างอิงตารางนี้

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_adjustment_type` (line ~3166), `enum_adjustment_type` (~3159)
- **E2E:** `../carmen-frontend-e2e/tests/031-adjustment-type.spec.ts` + `docs/test-cases/gaps/031-adjustment-type-gap.md`
- **Frontend:** `../carmen-frontend/routes/config/adjustment-type/`
