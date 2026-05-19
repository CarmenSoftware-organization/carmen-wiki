---
title: รายงานของเสีย (Wastage Reporting)
description: Variant เฉพาะของ stock-out สำหรับ spoilage, breakage, expiry และ theft — จัดประเภทเพื่อให้ finance วิเคราะห์รูปแบบการสูญเสียตาม reason, outlet และงวด
published: true
date: 2026-05-17T07:00:36.000Z
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# รายงานของเสีย (Wastage Reporting)

> **At a Glance**
> **เจ้าของ:** Store Keeper (submit) &nbsp;·&nbsp; Inventory Controller (approve) &nbsp;·&nbsp; **ตาราง:** `tb_stock_out` ด้วย flavour `adjustment_type = 'wastage'` (ไม่ใช่ตารางแยก) &nbsp;·&nbsp; **Trigger:** spoilage / breakage / expiry / theft / sample &nbsp;·&nbsp; **เขียนไปยัง:** ledger เป็น `stock_out` / `adjustment_out` &nbsp;·&nbsp; **สรุปบรรทัดเดียว:** variant OUT-only ของ [[inventory-adjustment]] ด้วย reason บังคับและบัญชี GL wastage

![รายงานของเสีย (Wastage Reporting) screen](/screenshots/inventory-adjustment/wastage-reporting.png)

## 1. อะไร & ใคร

Wastage Reporting คือ **variant ของ [[inventory-adjustment]]** สำหรับสต๊อกที่หายไปโดยไม่มีการขาย: spoilage, breakage, expiry, theft, sample / staff consumption, other-loss **ไม่ใช่ document type แยก** — ทุก entry wastage เป็นแถว `tb_stock_out` ที่ `adjustment_type_id` resolve ไปยัง reason flavour wastage Variant นี้มีอยู่เพื่อให้ finance แยกการสูญเสียตาม reason สำหรับการรายงาน cost-control

มันต่างจาก adjustment ทั่วไปอย่างไร:

- **OUT only** — ไม่มี counterpart return-to-stock
- **Reason บังคับ** — submit reject โดยไม่มี wastage reason ที่รู้จัก
- **GL Loss / expense** — credit side map ไปยังบัญชี wastage expense ไม่ใช่ adjustment ทั่วไป

## 2. งานทั่วไป

| งาน | ที่ไหน | Notes |
|---|---|---|
| บันทึก entry wastage | Store Operation → Wastage Reporting → **New** | เลือก location, reason, product, qty, lot |
| เลือก reason code | ฟิลด์ Reason บน header | Filter `tb_adjustment_type` ไปยังแถว flavour wastage `STOCK_OUT`: `SPOIL`, `BREAK`, `EXPIRY`, `THEFT`, `SAMPLE`, `OTHER` |
| แนบหลักฐาน | Tab Comments บนเอกสาร | รูปขวดแตก / ป้ายหมดอายุ (บังคับสำหรับ reason codes high-loss) |
| Submit เพื่ออนุมัติ | Action **Submit** | Flip `draft → in_progress`, route ไปยัง Inventory Controller |
| อนุมัติและ post | Inventory Controller → **Approve** | Post `tb_inventory_transaction` (stock_out / adjustment_out), debit Wastage Expense, credit Inventory |
| Reverse entry wastage | Wastage ใหม่ด้วย qty ลบ | Path correction เท่านั้น — ไม่แก้ไขต้นฉบับเลย; อ้างอิงต้นฉบับใน `note` |
| รัน report loss-by-reason | [[reporting-audit]] | Aggregation ต่อ outlet, ต่องวด, ต่อ reason |

## 3. Validation & Errors

| อาการ / Message | สาเหตุ | Action |
|---|---|---|
| "Reason required" | `adjustment_type_id` null ที่ submit | เลือก wastage reason จาก catalogue |
| "Invalid reason for this surface" | Reason `STOCK_IN` หรือ `STOCK_OUT` ที่ไม่ใช่ wastage ถูกเลือก | เลือก reason `STOCK_OUT` flavour wastage เท่านั้น |
| "Evidence required for THEFT / EXPIRY" | High-loss reason โดยไม่มี attachment | Upload รูปถ่าย / รายงานความเสียหายไปยัง `tb_stock_out_comment` |
| "Lot has zero balance" | Lot-tracked product ที่ source location ว่าง | เลือก lot อื่นหรือแก้ไข on-hand ก่อน |
| "Period is closed" | `so_date` ภายในงวดที่ปิด | ใช้วันที่วันนี้ หรือสร้าง JV ด้วยมือ |
| "Submit and approve must be different users" | ผู้ใช้คนเดียวกันพยายามทั้งสอง actions | Route ไปยังผู้อนุมัติคนละคน (segregation of duties) |
| ไม่สามารถแก้ไขเอกสารที่ completed | `doc_status = completed` เป็น immutable | ออก reversal (wastage qty ลบ) |

## 4. Edge Cases

- **Variant ไม่ใช่ตารางแยก** Schema เดียวกับ stock-out — discriminator คือ `adjustment_type_id` Test plans ที่มองหาตาราง `tb_wastage` จะไม่พบ
- **Snapshot Cost basis ที่ submit** `cost_per_unit` เลือกจาก costing method ที่ active (AVCO snapshot หรือ FIFO layer เก่าที่สุด) และไม่แก้ไขได้
- **ไม่มีการแก้ไขหลัง post** เมื่อ `doc_status = completed` ไม่มีฟิลด์ใดสามารถ mutate การแก้ไขคือ wastage qty ตรงข้ามใหม่อ้างอิงต้นฉบับใน `note`
- **Reversal เป็น append-only** แถวต้นฉบับไม่ `UPDATE` เลย — คู่คือ audit trail (ตรงกับ [[inventory/transaction]] semantics append-only)
- **GL routing** Credit side resolve จาก GL mapping ของ `tb_adjustment_type` — บัญชี wastage expense ไม่ใช่ adjustment expense ทั่วไป
- **Period gate** เหมือนกับเอกสาร inventory ทุกตัว — การ backdate เข้างวดที่ปิด reject

---

## 5. Data Model (Dev)

Wastage แชร์ schema กับ stock-out แหล่ง: tenant schema

### 5.1 `tb_stock_out` (ตาราง host)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key |
| `so_no` | `String? @db.VarChar` | Yes | เลขที่เอกสาร (`WR-2026-0001` เมื่อ issue จากหน้าจอ wastage) |
| `so_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่เอกสาร — gate กับ `tb_period` |
| `adjustment_type_id` | `String? @db.Uuid` | Yes | FK ไป `tb_adjustment_type` — ต้อง resolve ไปยังแถว flavour wastage |
| `adjustment_type_code` | `String? @db.VarChar` | Yes | รหัสที่ denormalise (`SPOIL`, `BREAK` ฯลฯ) |
| `doc_status` | `enum_doc_status` | No | `draft`, `in_progress`, `completed`, `cancelled`, `voided` |
| `location_id` / `location_code` / `location_name` | `String?` | Yes | Location ที่ยอดลด |
| `workflow_*` / `last_action_*` | mixed | Yes | Stage workflow, ประวัติ, audit |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([so_no, deleted_at])` Reverse relations ไปยัง `tb_stock_out_detail`, `tb_stock_out_comment`

### 5.2 `tb_stock_out_detail`

ถือ `product_id`, `qty`, `cost_per_unit`, `total_cost`, lot reference และ back-pointer `inventory_transaction_id` ที่ set ตอน post `@@unique([stock_out_id, product_id, dimension, deleted_at])`

### 5.3 `tb_adjustment_type` (catalogue reason)

| ฟิลด์ | Type | คำอธิบาย |
|---|---|---|
| `code`, `name` | `String` | เช่น `SPOIL` / "Spoilage" |
| `type` | `enum_adjustment_type` | `STOCK_IN` หรือ `STOCK_OUT` — แถว wastage เป็น `STOCK_OUT` เสมอ |
| `is_active` | `Boolean?` | Toggle ความพร้อมใน picker |

ดู [[master-data/adjustment-type]] สำหรับ catalogue reason เต็ม

## 6. Lifecycle / กติกาทางธุรกิจ

```
1. Store Keeper เปิด Wastage Reporting / new, เลือก location และ reason
2. เพิ่ม line items: product, qty, lot (cost_per_unit snapshot ที่ submit)
3. แนบหลักฐาน (reasons high-loss ต้องการ)
4. Submit -> draft -> in_progress, route ไปยัง Inventory Controller
5. Inventory Controller approve -> in_progress -> completed:
   - INSERT tb_inventory_transaction { inventory_doc_type: 'stock_out' }
   - INSERT tb_inventory_transaction_detail per line
   - INSERT tb_inventory_transaction_cost_layer with transaction_type = 'adjustment_out'
   - GL: DR Wastage Expense, CR Inventory
6. Reversal (path correction เท่านั้น): tb_stock_out ใหม่ด้วย qty ลบ, note link ไปยังต้นฉบับ
```

- **Reason บังคับ**, **direction STOCK_OUT เท่านั้น**, **submit ≠ approve** (segregation of duties)
- **ไม่มีการแก้ไขหลัง post** — append-only correction
- **Flag การรายงาน** การ post แต่ละครั้ง contribute ไปยัง aggregation loss ต่อ outlet, ต่องวด, ต่อ reason

## 7. Cross-References

- [[inventory-adjustment]] — โมดูล parent; กฎทางธุรกิจเดียวกัน apply
- [[master-data/adjustment-type]] — catalogue reason
- [[inventory]] &nbsp;·&nbsp; [[inventory/transaction]] &nbsp;·&nbsp; [[costing]] &nbsp;·&nbsp; [[reporting-audit]]

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_stock_out` (~2759-2812), `tb_stock_out_detail` (~2848-2886), `tb_adjustment_type` (~2569-2594), `enum_adjustment_type` (~2564-2567), `enum_doc_status` (~187-193)
- **Frontend:** `../carmen-inventory-frontend/app/(root)/store-operation/wastage-reporting/` — `wr-form.tsx`, `wr-form-schema.ts`, `wr-item-fields.tsx`
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` (wastage เป็น pre-close prerequisite)
