---
title: ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type)
description: แคตตาล็อกหมวด landed cost ของ GRN (ค่าขนส่ง อากร handling) พร้อมโหมดการจัดสรรต่อ instance (by value, by qty, manual)
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, extra-cost-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_extra_cost_type` (catalogue) + `tb_extra_cost` (per-GRN instance) &nbsp;·&nbsp; **ใช้โดย:** การจัดสรร landed cost ของ GRN &nbsp;·&nbsp; หมวดเช่น Freight / Duty / Handling พร้อมโหมดจัดสรร `by_value` / `by_qty` / `manual`

![ประเภทค่าใช้จ่ายเพิ่ม (Extra Cost Type) screen](/screenshots/master-data/extra-cost-type.png)

## 1. คืออะไร / ใครใช้

**Extra cost** คือค่าขนส่ง อากร handling และส่วนประกอบ **landed cost** อื่น ๆ ที่จัดสรรลงบนสินค้าที่รับเพื่อให้ **unit cost ใน inventory** สะท้อนต้นทุน *delivered* ไม่ใช่แค่บรรทัด invoice `tb_extra_cost_type` เก็บหมวดมีชื่อ (`Freight`, `Customs Duty`, `Brokerage`); `tb_extra_cost` เป็น instance ต่อ GRN พร้อม **โหมดการจัดสรร** ที่เลือก (`by_value`, `by_qty` หรือ `manual`)

`by_value` กระจายตามสัดส่วน value ของบรรทัด, `by_qty` ตามสัดส่วนปริมาณที่รับ และ `manual` รับยอดต่อบรรทัดโดยตรง **บริหารจัดการโดย** Product Admin (catalogue) และผู้ใช้ GRN (instance) **อ่านโดย** costing engine — extra cost ที่จัดสรรผิดบิดเบือน valuation inventory

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มประเภท cost | Configuration → Master Data → Extra Cost Type → **New** | บังคับ: `name` |
| ยกเลิกการใช้งานประเภท | Toggle `is_active` | ซ่อนจาก GRN ใหม่; GRN ประวัติไม่ได้รับผลกระทบ |
| Attach กับ GRN | หน้าแก้ GRN → **Extra Costs** | สร้าง row `tb_extra_cost`; เลือกโหมดการจัดสรร |
| สลับโหมดการจัดสรรบน GRN draft | หน้าเดียวกัน | Trigger recalc ของยอดต่อบรรทัด |
| การจัดสรรด้วยมือ | ตั้ง `allocate_extra_cost_type = manual` | ทุกบรรทัด GRN ต้องได้รับยอดที่ระบุชัดเจน |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่น |
| "Cannot delete — referenced by GRN extra-cost detail" | มี FK references | ใช้ inactivate แทน |
| "Missing allocation amount on line N" | โหมด `manual` กับบรรทัดว่าง | ใส่ยอดที่ระบุชัดเจนบนทุกบรรทัด |
| "Allocated sum doesn't equal parent" | การปัดเศษของ `by_value` / `by_qty` เกิน tolerance | รัน allocation ใหม่หรือปรับด้วยมือ |
| "Cannot change allocation on posted GRN" | พยายามแก้หลัง posting | Reverse / repost หรือปฏิเสธการเปลี่ยน |

## 4. Edge Cases

- **โหมด `manual`** ต้องการให้ทุกบรรทัด GRN มียอดที่ระบุชัดเจน — การ posting ถูกปฏิเสธถ้าบรรทัดใดว่าง
- **Rounding tolerance** — `by_value` / `by_qty` ต้อง reconcile กับ parent total ภายใน tolerance
- **การ re-allocation บน GRN ที่ posted** ต้องการขั้น recalc หรือถูกปฏิเสธ; อย่า mutate posted cost แบบเงียบ ๆ
- **ประเภท inactive** ยังอ่านได้บน GRN ประวัติ
- **ผลกระทบต่อ costing** — extra cost ไหลเข้า landed unit cost ที่ costing engine บริโภค; allocation ผิดบิดเบือนยอดคงเหลือทุกตัวปลายน้ำ

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_extra_cost_type`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String? @db.VarChar` | Yes | ชื่อแสดงผล (เช่น `Freight`) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `is_active` | `Boolean?` | Yes | Active flag |
| `info`, `dimension`, `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `extra_cost_type_name_u` Index บน `name` Reverse relation ไปยัง `tb_extra_cost_detail`

### 5.2 `tb_extra_cost`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String? @db.VarChar` | Yes | Label แบบ free text |
| `good_received_note_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_good_received_note` |
| `allocate_extra_cost_type` | `enum_allocate_extra_cost_type?` | Yes | `manual`, `by_value` หรือ `by_qty` |
| `description`, `note` | `String?` | Yes | Free text |
| `info`, `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** index บน `name` (`extra_cost_name_idx`) FK ไปยัง `tb_good_received_note` `onDelete: NoAction` Reverse relation ไปยัง `tb_extra_cost_detail` และ `tb_extra_cost_comment` (`tb_extra_cost_detail` บรรจุการแยกย่อยต่อบรรทัดรวมทั้ง FK ไปยัง `tb_extra_cost_type`)

`enum_allocate_extra_cost_type` values: `manual`, `by_value`, `by_qty`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `tb_extra_cost_type.name` unique ในแถว non-deleted
- **Deletion guards** ประเภทที่ถูกอ้างอิงไม่สามารถ hard-delete — ใช้ inactivate
- **Validation** โหมด `manual` ต้องการทุกบรรทัดมียอด; ระบบปฏิเสธการ posting มิฉะนั้น
- **Invariant การจัดสรร** `by_value` และ `by_qty` ต้องบวกกันได้ parent total ภายใน rounding tolerance
- **Lifecycle** ประเภท inactive อ่านได้บน GRN ประวัติ; ซ่อนจาก picker GRN ใหม่
- **การ re-allocation** การเปลี่ยนโหมดบน GRN ที่ posted ต้องการ recalc หรือถูกปฏิเสธ

## 7. การอ้างอิงข้ามโมดูล

- [[good-receive-note]] — ผู้บริโภคแต่เพียงผู้เดียว แต่ละ GRN สามารถ attach หลาย instance `tb_extra_cost`; การจัดสรรรันตอน posting
- [[costing]] — landed unit cost ไหลจากการจัดสรร extra cost; allocation ผิดบิดเบือน valuation

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (lines ~4828-4851), `tb_extra_cost` (lines ~4694-4718), `enum_allocate_extra_cost_type` (lines ~109-113)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/extra-cost-type/`
