---
title: มิติ (Dimension)
description: Custom field ที่ผู้ใช้นิยามได้ (cost centre, project code ฯลฯ) ที่แนบไปกับเอกสารหรือ master record ใดก็ได้ พร้อมกฎการแสดงผลต่อเอนทิตี
published: true
date: 2026-05-17T12:00:00.000Z
tags: system-config, dimension, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# มิติ (Dimension)

> **At a Glance**
> **เจ้าของ:** Sysadmin &nbsp;·&nbsp; **ตาราง:** `tb_dimension` (+ `tb_dimension_display_in`) &nbsp;·&nbsp; **ใช้โดย:** PR / PO / GRN / SR / IA / inventory / master records &nbsp;·&nbsp; ระบบ custom field ที่ผู้ใช้ขยายได้ — cost-centre, project code, GL override

## 1. คืออะไรและใครใช้

Dimension คือ **ระบบ custom field ที่ผู้ใช้ขยายได้** มิติหนึ่งนิยาม tag ที่มีชื่อ (`cost_centre`, `project_code`, `gl_account_override`, `event_name`, …) พร้อม value space แบบ typed, default value และรายการของ *สถานที่ที่ควรปรากฏ* — header ของ PR, detail ของ GRN, master ของ vendor ฯลฯ ค่าของผู้ใช้ปลายทางถูกเก็บในคอลัมน์ `dimension` JSONB ที่ทุกตารางธุรกรรมและ master record ส่วนใหญ่พกพา

การแยกเป็นสองตารางทำให้แคตตาล็อกสะอาด `tb_dimension` คือ *นิยาม* `tb_dimension_display_in` คือ *matrix การแสดงผล* — หนึ่ง row ต่อสถานที่ที่ dimension ควรปรากฏ (พร้อม default override ต่อสถานที่) นี่คือวิธีที่ Carmen รองรับการติด tag cost-centre บน PR header และ IA detail line โดยไม่ต้อง hardcode คอลัมน์

**บำรุงรักษาโดย** Sysadmin **อ่านโดย** ทุกฟอร์มที่ render ฟิลด์ dimension และทุกรายงานการจัดสรรต้นทุน

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| นิยาม dimension | System Config → Dimensions → New | ตั้ง key, type, default value แบบ optional |
| เปิดใช้ dimension บนสถานที่ | Dimension edit → display-in matrix | Checkbox grid กับค่า enum 24 ตัว |
| คัดสรรค่าที่อนุญาตของ `lookup` | Dimension edit → editor `value` | จำเป็นสำหรับ `lookup` / `lookup_dataset` |
| Override default ต่อสถานที่ | Display-in row → `default_value` | ชนะ default ระดับบนสุดของ dimension |
| ปลดระวาง dimension | ตั้ง `is_active = false` | ซ่อนจากฟอร์มใหม่; ค่าเดิมคงอยู่ |
| ตรวจสอบการเปลี่ยนแปลง dimension | [[reporting-audit/activity]] log | `entity_type = dimension` |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Key already exists" | ซ้ำในกลุ่มที่ไม่ถูก delete | เลือก key อื่นหรือ reactivate ของเดิม |
| "Value not in catalogue" | ค่า `lookup` ไม่อยู่ใน `value` JSON | เพิ่มในแคตตาล็อกหรือเลือกที่มีอยู่ |
| ไม่สามารถ hard-delete dimension | เอกสารมีค่าที่ไม่ว่างสำหรับ key | ตั้ง `is_active = false` แทน |
| ฟิลด์หายจากฟอร์มใหม่ | Row `display_in` ขาดหายหรือถูกลบ | เพิ่ม row ใน display-in matrix |
| Type mismatch ตอนบันทึก | ค่าเอกสารละเมิด `type` | Validation ฝั่งฟอร์มควร reject ก่อน |

## 4. กรณีพิเศษ

- **Snapshot semantics** Array JSON `dimension` ของเอกสารเก็บค่า ณ เวลาเขียน; การแก้ catalogue ภายหลังไม่ retro-edit เอกสารประวัติศาสตร์
- **การลบสถานที่** ซ่อนฟิลด์จากเอกสารใหม่ แต่ไม่ลบค่าที่ persist
- **Cascade ของ default** การ resolve ตอน render ฟอร์ม: `default_value` ต่อสถานที่ → `default_value` ระดับบนสุด → ว่าง
- **การติด tag บน master record** การติด tag vendor / location / currency ทำให้เอกสารธุรกรรมสืบทอด default ของ dimension

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_dimension`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `key` | `String @db.VarChar` | No | Key เชิงโปรแกรม (เช่น `cost_centre`) เก็บตามตัวอักษรใน array `dimension` ของเอกสาร |
| `type` | `enum_dimension_type` | No | `string`, `number`, `boolean`, `date`, `datetime`, `json`, `dataset`, `lookup`, `lookup_dataset` |
| `value` | `Json? @db.JsonB` | Yes | รายการ catalogue / ค่าที่อนุญาต |
| `description` / `note` | `String?` | Yes | Free text |
| `default_value` | `Json? @db.JsonB` | Yes | Default ระดับบนสุด |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `info` | `Json? @db.JsonB` | Yes | Metadata อิสระ |
| `doc_version` | `Int` | No | Optimistic-concurrency token |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([key, deleted_at])` Index บน `[key]`

### 5.2 `tb_dimension_display_in`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `dimension_id` | `String @db.Uuid` | No | FK ไปยัง `tb_dimension.id` |
| `display_in` | `enum_dimension_display_in` | No | ที่ที่ dimension จะแสดง |
| `default_value` | `Json? @db.JsonB` | Yes | Override ต่อสถานที่ |
| `note` / `info` / `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([dimension_id, display_in, deleted_at])` Index บน `[dimension_id, display_in]` FK `onDelete: NoAction`

**`enum_dimension_display_in`:** `currency`, `exchange_rate`, `delivery_point`, `department`, `product_category`, `product_sub_category`, `product_item_group`, `product`, `location`, `vendor`, `pricelist`, `unit`, `purchase_request_header`, `purchase_request_detail`, `purchase_order_header`, `purchase_order_detail`, `goods_received_note_header`, `goods_received_note_detail`, `transfer_header`, `transfer_detail`, `stock_in_header`, `stock_in_detail`, `stock_out_header`, `stock_out_detail`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `key` unique ในกลุ่มที่ไม่ถูก delete; แต่ละ `(dimension_id, display_in)` unique
- **Type validation** การเขียนเอกสาร validate กับ `type` ของ dimension; `lookup` / `lookup_dataset` ตรวจกับ catalogue `value`
- **Cascade ของ default** ต่อสถานที่ → ระดับบนสุด → ว่าง
- **การ์ดการลบ** Hard-delete ถูกบล็อกถ้าเอกสารใดเก็บค่าไม่ว่างสำหรับ key; inactivate แทน
- **การลบสถานที่** ซ่อนจากฟอร์มใหม่; ค่าที่ persist คงอยู่
- **Snapshot semantics** ค่าเอกสารคือ snapshot ตอนเขียน — ไม่ retro-edit

## 7. การอ้างอิงข้าม

- [[purchase-request]], [[purchase-order]] — การติด tag header + detail
- [[good-receive-note]] — พา cost-centre allocation ไปข้างหน้า
- [[store-requisition]] — issue dimensions ขับเคลื่อนการจัดสรรต้นทุน
- [[inventory-adjustment]] — การติด tag stock-in / stock-out
- [[inventory]] — การติด tag transfer
- [[master-data/vendor]], [[master-data/location]], [[master-data/currency]], [[product]] — การติด tag บน master record cascade defaults ไปยังเอกสารธุรกรรม

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dimension` (lines ~4608-4635), `tb_dimension_display_in` (lines ~4671-4692), enums (lines ~115-185)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/dimension/`
