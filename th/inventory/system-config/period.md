---
title: ช่วงงวด (Period)
description: นิยามช่วงงวดบัญชีและ snapshot ต้นทุนสต๊อกต่องวด — หน้าจอ admin จริงคือรายการ CRUD ธรรมดาที่สถานะเป็นแค่ฟิลด์แก้ไขได้หนึ่งฟิลด์ ไม่ใช่ workflow Close/Lock/Reopen เฉพาะที่มี snapshot viewer
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, period, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ช่วงงวด (Period)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance Manager &nbsp;·&nbsp; **ตาราง:** `tb_period` (+ `tb_period_snapshot`) &nbsp;·&nbsp; **ใช้โดย:** GRN, IA, count, spot-check, engine ต้นทุน &nbsp;·&nbsp; ปฏิทินบัญชี — ควบคุมการ back-date และขับเคลื่อนการปิดต้นทุน &nbsp;·&nbsp; **หน้าจอ admin คือรายการธรรมดา + dialog สร้าง/แก้ไข — ไม่มี action Close/Lock/Reopen เฉพาะ หรือ tab Snapshot เลย**

![ช่วงงวด (Period) screen](/screenshots/system-config/period.png)

## สถานะการ implement (ตรวจสอบ 2026-07-16)

หน้าจอ `/system-admin/period` (`period-component.tsx` + `period-dialog.tsx`) คือ **รายการ CRUD ทั่วไป**: ค้นหา, filter สถานะ, Add/Export/Print และ dialog แก้ไข row ที่มีฟิลด์ธรรมดา — `fiscal_year`, `fiscal_month`, `start_at`, `end_at` และ **`<Select>` สถานะ** ที่เสนอ `open`/`closed`/`locked` ตรงๆ ส่งด้วยวิธีเดียวกับฟิลด์อื่นผ่าน `PATCH` ไม่มี button "Close" เฉพาะ, button "Lock" เฉพาะ, button "Reopen" เฉพาะ, prompt ยืนยัน/เหตุผล audit หรือ tab "Snapshot" เลยที่ไหนในโครงสร้าง component (ไม่มี component period-detail อยู่เลยใน directory — มีแค่ card, list และ dialog) การเปลี่ยนสถานะทำง่ายพอๆ กัน และเป็น UI action เดียวกันเป๊ะ กับการเปลี่ยน `fiscal_month` ตาราง "งานทั่วไป" ด้านล่างถูกแก้ไขให้สะท้อนสิ่งนี้; ค่า enum และความหมายของการ์ด posting เอง (§5, §6) ไม่ได้รับผลกระทบและยังคงถูกต้อง

## 1. คืออะไรและใครใช้

Period นิยามปฏิทินบัญชีที่ Carmen ดำเนินงานบน — หนึ่ง row ต่อเดือนการเงิน ระบุโดย `YYMM` บวก integer `fiscal_year` / `fiscal_month` และช่วง `[start_at, end_at)` ทุกงวดมีสถานะ (`open`, `closed`, `locked`) ที่ควบคุมว่าเอกสารที่มีวันที่ใดสามารถ post ได้ Period คือหน่วยที่ปิดต้นทุนสต๊อกและทำ snapshot: เมื่อ finance ปิดมกราคม จะไม่มี GRN / การออก / การปรับของเดือนมกราคมเพิ่มเติมที่จะ post และยอดปิดกลายเป็นยอดเปิดของเดือนกุมภาพันธ์

`tb_period_snapshot` เก็บ snapshot สต๊อกต่อ location / ต่อ product / ต่อ lot ณ เวลาหนึ่ง — สร้างโดย engine ต้นทุนและใช้สำหรับ trial balance, การ post GL และ roll-forward ไม่มีหน้าจอใดในโมดูลนี้ render มัน (ดูสถานะการ implement) — มันถูกเขียนและอ่านโดย engine ต้นทุนเท่านั้น

**บำรุงรักษาโดย** Sysadmin (โดยทั่วไปคือ Finance Manager) ผ่าน dialog แก้ไขธรรมดา **อ่านโดย** ทุกการ์ด posting และ engine ต้นทุน

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เปิดงวดถัดไป | รายการงวด → **Generate Next** (button `CalendarPlus`) | `POST .../periods/next`; สร้าง batch อัตโนมัติ (เช่น 12 เดือน) ผ่าน roll-forward |
| เปลี่ยนสถานะของงวด | Row งวด → **Edit** → dropdown **Status** → Save | Dialog แก้ไขเดียวกันกับ fiscal year/month/date — การเลือก `closed` หรือ `locked` ที่นี่คือการแก้ฟิลด์ธรรมดา ไม่ใช่ workflow action เฉพาะ |
| ดู snapshot | ~~Period detail → Snapshot tab~~ | **ไม่มีหน้าจอนี้อยู่จริง** — ไม่พบ component period-detail เลย; snapshot เป็นเรื่องภายในของ costing engine |
| สร้าง snapshot ปิด | Job engine ต้นทุน | เขียน `tb_period_snapshot` ทุก (location, product, lot); ไม่ได้ trigger จากหน้าจอนี้ |
| Export รายการงวด | รายการงวด → **Export** | XLSX พร้อมคอลัมน์ period/fiscal year/fiscal month/dates/status |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Period is closed" | วันที่ posting อยู่ในงวดที่ closed/locked | ใช้งวด open ปัจจุบัน; หรือยก JV |
| "Period date overlap" | งวดสองตัวมีวันที่ทับซ้อน | แก้ช่วง — งวดต้อง contiguous ไม่ทับซ้อน |
| `period` ไม่ตรงกับ fiscal date | `period != fiscal_year-2000 * 100 + fiscal_month` | คำนวณใหม่และแก้ค่าใดค่าหนึ่ง |
| ความไม่ตรงกันของ roll-forward | Closing N ≠ Opening N+1 | ปรากฏใน `diff_amount`; review snapshot (ไม่แสดงใน UI ใดเลย — query โดยตรง) |
| ไม่สามารถลบงวด | Snapshot, cost layer หรือ posting อ้างอิงอยู่ | Archive เท่านั้น; soft-delete ทำลายสายโซ่ GL |
| เปลี่ยนสถานะเป็น `closed`/`locked` โดยไม่มีขั้นตอนยืนยัน | คาดหวัง — dialog แก้ไขไม่มี guard เฉพาะสำหรับฟิลด์นี้ | ไม่มีหน้าจอ undo; แก้ row กลับเป็น `open` ถ้านี่คือความผิดพลาด |

## 4. กรณีพิเศษ

- **สถานะคือฟิลด์แก้ไขได้ธรรมดา ไม่ใช่ workflow** ผู้ใช้ใดก็ตามที่เปิด dialog Edit ได้สามารถตั้งค่าสถานะใดก็ได้โดยตรง — ไม่มี prompt เหตุผล audit แยกสำหรับการ reopen งวดที่ปิดแล้ว ต่างจากเวอร์ชันก่อนหน้าของหน้านี้
- **การสร้าง snapshot ใหม่** การรัน close ซ้ำสำหรับงวดเดียวกันจะ overwrite หรือ append ตามนโยบาย Finance; **append ที่ `snapshot_at` ใหม่** คือรูปแบบที่แนะนำเพื่อรักษา audit (พฤติกรรมของ costing engine ยังไม่ยืนยันกับ UI ใดเพราะไม่มี UI)
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
- **สถานะเป็นฟิลด์อิสระใน UI ไม่ใช่ state machine ที่บังคับ** `<Select>` สถานะของ dialog แก้ไขเสนอทั้งสามค่า (`open`/`closed`/`locked`) โดยไม่มีเงื่อนไขไม่ว่าสถานะปัจจุบันของ row จะเป็นอะไร — ไม่พบ backend transition guard ที่ยืนยันได้เช่นกัน (เช่น การบล็อก `locked → open`) ถือว่า progression `open → closed → locked` ที่อธิบายไว้ที่นี่เป็นวินัยการใช้งาน *ตามเจตนา* ไม่ใช่กฎที่ระบบบังคับ
- **การ์ด posting** ทุกเอกสารที่มีวันที่ต้อง resolve ไปยังงวด `open`
- **การสร้าง snapshot** `(period_id, snapshot_at)` ต่อ `(location, product, optional lot)`; append ที่ `snapshot_at` ใหม่รักษา audit
- **Roll-forward integrity** Opening N+1 = Closing N ต่อ tuple
- **การ์ดการลบ** งวดที่มี snapshot / cost layer / posting ไม่สามารถ delete

## 7. การอ้างอิงข้าม

- [inventory](/th/inventory/inventory) — การเขียน current-stock ผ่านการ์ดงวดเปิด
- [costing](/th/inventory/costing) — engine อ่าน movement layer และเขียน snapshot ตอน close
- [good-receive-note](/th/inventory/good-receive-note), [inventory-adjustment](/th/inventory/inventory-adjustment) — การตรวจสอบงวดของวันที่ posting
- [physical-count](/th/inventory/physical-count) — เอกสาร count แช่แข็งกับงวดผ่าน `tb_physical_count_period`
- [spot-check](/th/inventory/spot-check) — การ์ดงวดของการ post variance

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period` (lines ~1203-1240), `tb_period_snapshot` (lines ~1272-1310), `enum_period_status` (line ~1197)
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/period/` — `period-component.tsx` (list), `period-dialog.tsx` (create/edit), `period-card.tsx` (mobile card), `use-period-table.tsx`
