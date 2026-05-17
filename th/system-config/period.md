---
title: ช่วงงวด (Period)
description: นิยามช่วงงวดบัญชีและ snapshot ต้นทุนสต๊อกต่องวด — สถานะ open/closed/locked ขับเคลื่อนการ์ดการ back-date และการปิดต้นทุน
published: true
date: 2026-05-17T07:28:28.000Z
tags: system-config, period, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ช่วงงวด (Period)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance Manager &nbsp;·&nbsp; **ตาราง:** `tb_period` (+ `tb_period_snapshot`) &nbsp;·&nbsp; **ใช้โดย:** GRN, IA, count, spot-check, engine ต้นทุน &nbsp;·&nbsp; ปฏิทินบัญชี — ควบคุมการ back-date และขับเคลื่อนการปิดต้นทุน

![ช่วงงวด (Period) screen](/assets/screenshots/system-config/period.png)

## 1. คืออะไรและใครใช้

Period นิยามปฏิทินบัญชีที่ Carmen ดำเนินงานบน — หนึ่ง row ต่อเดือนการเงิน ระบุโดย `YYMM` บวก integer `fiscal_year` / `fiscal_month` และช่วง `[start_at, end_at)` ทุกงวดมีสถานะ (`open`, `closed`, `locked`) ที่ควบคุมว่าเอกสารที่มีวันที่ใดสามารถ post ได้ Period คือหน่วยที่ปิดต้นทุนสต๊อกและทำ snapshot: เมื่อ finance ปิดมกราคม จะไม่มี GRN / การออก / การปรับของเดือนมกราคมเพิ่มเติมที่จะ post และยอดปิดกลายเป็นยอดเปิดของเดือนกุมภาพันธ์

`tb_period_snapshot` เก็บ snapshot สต๊อกต่อ location / ต่อ product / ต่อ lot ณ เวลาหนึ่ง — สร้างโดย engine ต้นทุนและใช้สำหรับ trial balance, การ post GL และ roll-forward

**บำรุงรักษาโดย** Sysadmin (โดยทั่วไปคือ Finance Manager) **อ่านโดย** ทุกการ์ด posting และ engine ต้นทุน

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปิดงวดถัดไป | System Config → Period → New / Open | สร้างอัตโนมัติผ่าน roll-forward; status `open` |
| ปิดงวดปัจจุบัน | Row งวด → **Close** | ไม่มี posting ใหม่; การแก้ไขยังอนุญาตโดย Finance |
| Lock งวด | Row งวด → **Lock** | Terminal ภายใต้การดำเนินงานปกติ; การ unlock ต้อง DB override + audit |
| Reopen งวดที่ปิดแล้ว | Row งวด → **Reopen** | ต้องมีเหตุผล audit; เขียน `tb_period_comment` |
| ดู snapshot | Period detail → Snapshot tab | Grid ยอดต่อ location แบบ read-only |
| สร้าง snapshot ปิด | Job engine ต้นทุน | เขียน `tb_period_snapshot` ทุก (location, product, lot) |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Period is closed" | วันที่ posting อยู่ในงวดที่ closed/locked | ใช้งวด open ปัจจุบัน; หรือยก JV |
| "Period date overlap" | งวดสองตัวมีวันที่ทับซ้อน | แก้ช่วง — งวดต้อง contiguous ไม่ทับซ้อน |
| `period` ไม่ตรงกับ fiscal date | `period != fiscal_year-2000 * 100 + fiscal_month` | คำนวณใหม่และแก้ค่าใดค่าหนึ่ง |
| ความไม่ตรงกันของ roll-forward | Closing N ≠ Opening N+1 | ปรากฏใน `diff_amount`; review snapshot |
| ไม่สามารถลบงวด | Snapshot, cost layer หรือ posting อ้างอิงอยู่ | Archive เท่านั้น; soft-delete ทำลายสายโซ่ GL |

## 4. กรณีพิเศษ

- **Progression สถานะ** อนุญาต: `open → closed`, `closed → open` (reopen), `closed → locked` `locked` เป็น terminal ภายใต้การดำเนินงานปกติ
- **การสร้าง snapshot ใหม่** การรัน close ซ้ำสำหรับงวดเดียวกันจะ overwrite หรือ append ตามนโยบาย Finance; **append ที่ `snapshot_at` ใหม่** คือรูปแบบที่แนะนำเพื่อรักษา audit
- **Roll-forward integrity** Opening N+1 ต้องเท่ากับ Closing N สำหรับทุก (location, product, lot); ความไม่ตรงกัน track ใน `diff_amount`
- **การเป็นสมาชิกของช่วงวันที่** resolve งวดตอน post

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_period`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `period` | `String @db.VarChar` | No | `YYMM` (เช่น `2601`) |
| `fiscal_year` / `fiscal_month` | `Int @db.Integer` | No | `YYYY` + `1`-`12` |
| `start_at` / `end_at` | `DateTime @db.Timestamptz(6)` | No | Inclusive / exclusive |
| `status` | `enum_period_status` | No | `open` (default), `closed`, `locked` |
| `note` / `info` / `dimension` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([period, deleted_at])` + `@@unique([fiscal_year, fiscal_month, deleted_at])` Index บน `[fiscal_year, fiscal_month]` และ `[period]` Reverse relations ไปยัง `tb_period_snapshot`, `tb_inventory_transaction_cost_layer`, `tb_period_comment`, `tb_physical_count_period` **`enum_period_status`:** `open`, `closed`, `locked`

### 5.2 `tb_period_snapshot`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` / `period_id` | `String @db.Uuid` | No | Keys |
| `snapshot_at` | `DateTime @db.Timestamptz(6)` | No | เวลา snapshot ที่แน่นอน (โดยทั่วไป close datetime) |
| `location_id` / `product_id` | `String @db.Uuid` | No | Position keys |
| `location_code` / `location_name` / `product_code` / `product_name` / `product_local_name` / `product_sku` | `String?` | Yes | Denormalised แสดงผล |
| `lot_no` / `lot_index` / `lot_at_date` / `lot_seq_no` | — | Yes | การระบุ lot แบบ optional |
| `opening_qty` / `opening_cost_per_unit` / `opening_total_cost` | `Decimal? @db.Decimal(20,5)` | Yes | ยกจากงวดก่อน |
| `receipt_qty` / `receipt_total_cost` | `Decimal?` | Yes | GRN ในงวด |
| `issue_qty` / `issue_total_cost` | `Decimal?` | Yes | SR ในงวด |
| `adjustment_qty` / `adjustment_total_cost` | `Decimal?` | Yes | IA / count / spot-check ในงวด |
| `closing_qty` / `closing_cost_per_unit` / `closing_total_cost` | `Decimal?` | Yes | Position ที่ `snapshot_at` |
| `diff_amount` | `Decimal?` | Yes | Residual จากการปัดเศษ / true-up |
| `note` / `info` / `dimension` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([period_id, snapshot_at, deleted_at])` Index บน `[period_id, snapshot_at]` FK `onDelete: NoAction`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** ทั้ง `period` และ `(fiscal_year, fiscal_month)` unique ในกลุ่มที่ไม่ถูก delete; ควรสอดคล้องกัน (`period == fiscal_year-2000 * 100 + fiscal_month` สำหรับ 2000-2099)
- **Date integrity** `start_at < end_at`; งวด contiguous ไม่ทับซ้อน
- **Progression สถานะ** `open → closed`, `closed → open`, `closed → locked` `locked` terminal ภายใต้การดำเนินงานปกติ
- **การ์ด posting** ทุกเอกสารที่มีวันที่ต้อง resolve ไปยังงวด `open`
- **การสร้าง snapshot** `(period_id, snapshot_at)` ต่อ `(location, product, optional lot)`; append ที่ `snapshot_at` ใหม่รักษา audit
- **Roll-forward integrity** Opening N+1 = Closing N ต่อ tuple
- **การ์ดการลบ** งวดที่มี snapshot / cost layer / posting ไม่สามารถ delete

## 7. การอ้างอิงข้าม

- [[inventory]] — การเขียน current-stock ผ่านการ์ดงวดเปิด
- [[costing]] — engine อ่าน movement layer และเขียน snapshot ตอน close
- [[good-receive-note]], [[inventory-adjustment]] — การตรวจสอบงวดของวันที่ posting
- [[physical-count]] — เอกสาร count แช่แข็งกับงวดผ่าน `tb_physical_count_period`
- [[spot-check]] — การ์ดงวดของการ post variance

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period` (lines ~1172-1203), `tb_period_snapshot` (lines ~1239-1292), `enum_period_status` (lines ~1166-1170)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/period/`
