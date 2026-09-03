---
title: บันทึกธุรกรรมคลังสินค้า (Inventory Transaction Log)
description: Ledger append-only ของทุก event ที่กระทบ inventory — GRN, SR, adjustment, wastage, count variance, period flip — และเป็น source of truth สำหรับการคำนวณ balance
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, transaction, audit, ledger, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# บันทึกธุรกรรมคลังสินค้า (Inventory Transaction Log)

> **At a Glance**
> **เจ้าของ:** System (read-only สำหรับ users) &nbsp;·&nbsp; **Tables:** `tb_inventory_transaction` (header) + `_detail` + `_cost_layer` &nbsp;·&nbsp; **Trigger:** ทุก source-document posting (`good_received_note` / `store_requisition` / `stock_in` / `stock_out` / `credit_note` / `close` / `open` — count variance เข้ามาเป็น stock-in/stock-out) &nbsp;·&nbsp; **ใช้โดย:** การคำนวณ balance + audit trace &nbsp;·&nbsp; **1-liner:** event tape ที่ immutable; **append-only, ไม่เคย update, ไม่เคย delete**

![บันทึกธุรกรรมคลังสินค้า (Inventory Transaction Log) screen](/screenshots/inventory/transaction.png)

## 1. ภาพรวมและผู้ใช้งาน

Inventory Transaction Log คือ **event tape ที่ immutable** ของทุกการเคลื่อนไหวปริมาณที่ทุก location แต่ละ row คือหนึ่ง event ร่วมกับ `(product, location, lot, qty, unit-cost)` ที่กระทบที่ pick ที่ posting time **Rows ไม่เคย UPDATE และไม่เคย DELETE** — การแก้ไขคือ row ตรงข้าม-sign ใหม่ ไม่เคยเป็น mutation ของ row เก่า

- **Testers / Support / Finance** — อ่าน timeline ที่ `/inventory-management/transaction` เพื่อ trace balance ใด ๆ กลับไปยังเอกสาร source
- **Cost Engine** — ใช้ rows `_cost_layer` สำหรับ AVCO / FIFO consumption
- **Period Close** — `GROUP BY` เหนือ cost layers กลายเป็น `tb_period_snapshot`

## 2. งานที่พบบ่อย

| งาน | ที่ใด | หมายเหตุ |
|---|---|---|
| Find movement โดย source-document reference | Transaction Log → filter โดย `inventory_doc_no` | Composite index `(inventory_doc_type, inventory_doc_no)` ทำให้นี่เป็น one-query |
| ดู cost-layer impact ของ posting | เปิด detail → tab Cost Layer | แสดง `lot_no`, `lot_index`, `in_qty` / `out_qty`, `cost_per_unit`, `average_cost_per_unit` |
| Verify ว่า GRN posting เขียนไปยัง ledger | Filter `inventory_doc_type = 'good_received_note'` และ GRN id | หนึ่ง header row + หนึ่ง detail row ต่อ GRN line + หนึ่ง cost-layer row ต่อ lot |
| Trace SR transfer (สองด้าน) | Filter โดย SR id | คู่ของ OUT @ source (`transfer_out`) และ IN @ destination (`transfer_in`) |
| Audit period close | Filter `inventory_doc_type IN ('close', 'open')` | Close เองปรากฏบน ledger |
| Diagnose balance mismatch | Sum cost-layer `in_qty − out_qty` สำหรับ `(location, product)` key | ผลรวมนี้**คือ** balance เอง — ไม่มี balance row ที่ cache แยกต่างหาก; ตัวเลข on-hand ทุกจุดในผลิตภัณฑ์ (dialog on-hand ของ PR, system qty ของ spot-check) derive จาก sum เดียวกันนี้ |
| Filter รายการ | ช่องค้นหา + date-range presets (Today / 7d / 30d / This month / custom), ทิศทาง Inbound/Outbound, Location, Category, และ ref-type pills (GRN / SR / SI / SO / PC) | Filters เป็นแบบ URL-backed; convention ของ backend filter คือ `field:value;field\|op:v1,v2` |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | การกระทำ |
|---|---|---|
| "Cannot edit transaction" ใน UI | Ledger คือ read-only โดยการออกแบบ — หน้าจอไม่มี affordance ให้ create/edit เลย | แก้ไขผ่านเอกสาร source ทิศทางตรงข้าม (credit note, stock-in/stock-out) |
| Balance ดูผิด | เอกสาร source post โดยไม่คาดคิด (เช่น GRN **save** ก็ post แล้ว — commit ไม่ได้ post) | Re-derive จาก ledger; ผลรวม cost-layer คือ balance เดียวที่มี |
| Movement ที่ลงวันที่เดือนก่อนไปปรากฏในงวดเดือนนี้ | โดยการออกแบบ: `resolveCurrentPeriod` stamp ทุก movement ใหม่เข้า**งวดเปิดปัจจุบัน**เสมอโดยไม่สน document date — row ที่ backdate ไม่เคยถูกจัดเข้างวด closed (และไม่เคยถูก reject เพราะ backdate เช่นกัน) | ไม่มีอะไรต้องแก้; *มูลค่า* ของงวด closed ถูกป้องกันด้วย guard การ reprice ของ credit-note ไม่ใช่ด้วยการ block posting |
| Filter ref-type PC ไม่คืนผลลัพธ์ | Frontend มี pill `PC (physical_count)` แต่ `enum_inventory_doc_type` ไม่มีค่า `physical_count` — การแก้ไขจาก count เข้ามาเป็นเอกสาร `stock_in` / `stock_out` | Filter ด้วย SI / SO แทน |
| Cost ต่างจาก current product cost | `cost_per_unit` snapshot ที่ posting; ไม่ re-fetch | ถูกต้องโดยการออกแบบ — ยกเว้น Credit Note Amount กับ lot ในงวดเปิด ซึ่ง**จะ** re-price lot จริง (lot ในงวด closed จะบันทึกเป็น `diff_amount` แทน) |

## 4. กรณีพิเศษ

- **Append-only** ไม่มี `UPDATE` หรือ `DELETE` ในการทำงานปกติ `deleted_at` ถูกตั้งเฉพาะสำหรับ soft-purge ไม่เคยสำหรับ "correction"
- **No standalone insert** Rows insert เฉพาะโดย transitions workflow ของเอกสาร source — ไม่เคยโดย user action Frontend คือ read-only
- **Cost snapshot ที่ posting** `cost_per_unit` pick ที่ moment ที่เอกสาร source post AVCO ใช้ snapshot running average; FIFO pick layer lot ที่เก่าที่สุดที่เปิด
- **Lot lineage** `from_lot_no` และ `current_lot_no` จับ splits / merges / consumption FIFO consumption order บังคับใช้ผ่าน `(lot_at_date, lot_seq_no)` บน cost layer
- **Period stamp != document date** ทุก cost-layer row stamp `period_id` และ `at_period` (YYMM) ที่ insert — และ stamp เป็น**งวดเปิดปัจจุบัน**เสมอ (`resolveCurrentPeriod`) ไม่เคยเป็นงวดของ document date การ aggregate ตามงวด group โดย stamp นี้
- **Correction = rows ใหม่ผ่านเอกสาร source** ไม่มี reversal endpoint บน ledger เอง; การแก้ไขเข้ามาเป็นเอกสาร credit-note หรือ stock-in/stock-out ซึ่ง post transaction ใหม่ของตัวเอง `deleted_at` ไม่เคยถูกตั้งโดย code path ใดของ inventory ปัจจุบัน
- **การรับเข้า direct-location มีสองขา** การรับ GRN เข้า location ที่ `location_type = direct` post layer ขาเข้า **บวก** layer `issue` หักล้างอัตโนมัติ (`createDirectExpenseOut`, lot `ISS-…`) ภายใต้ header เดียวกัน — net on-hand เป็นศูนย์

---

## 5. โมเดลข้อมูล (Dev)

Source: tenant schema สองตารางหลัก (header + detail) บวกตาราง cost-layer

### 5.1 `tb_inventory_transaction` (header)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_doc_type` | `enum_inventory_doc_type` | No | Discriminator: `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close`, `open` |
| `inventory_doc_no` | `String @db.Uuid` | No | FK-by-id ไปยังเอกสาร source ของ type ที่ตรง |
| `doc_version` | `Int` | No | ตัวนับ optimistic-concurrency; ค่าเริ่มต้น `0` ถูก expose ใน GET responses (findOne + findAll) สำหรับ audit/versioning แต่ไม่ได้ใช้สำหรับ locking — ledger เป็น append-only ไม่มี update endpoint |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` (deleted เฉพาะสำหรับ soft-purge) |

**Indexes:** บน `inventory_doc_no`, บน `inventory_doc_type`, composite `(inventory_doc_type, inventory_doc_no)`

### 5.2 `tb_inventory_transaction_detail` (lines)

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `String @db.Uuid` | No | Primary key |
| `inventory_transaction_id` | `String @db.Uuid` | No | FK ไปยัง header |
| `from_lot_no` / `current_lot_no` | `String?` | Yes | Lot ก่อน / หลัง event นี้ |
| `location_id`, `location_code` | `String?` | Yes | Location ที่ได้รับผลกระทบ |
| `product_id` | `String @db.Uuid` | No | สินค้าที่ได้รับผลกระทบ |
| `qty` | `Decimal(20,5)?` | Yes | Signed; positive = เพิ่ม, negative = ลด |
| `cost_per_unit`, `total_cost` | `Decimal(20,5)?` | Yes | Cost snapshot ที่ posting time |
| Audit columns | — | Yes | `created_*`, `updated_*` **ไม่มี soft-delete บน detail rows** |

### 5.3 `tb_inventory_transaction_cost_layer`

FIFO layer ต่อ lot ด้วย `lot_no`, `lot_index`, `in_qty` / `out_qty`, `cost_per_unit`, `average_cost_per_unit`, `period_id`, `at_period` และ `transaction_type` (`enum_transaction_type`: `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`) `@@unique([lot_no, lot_index])` ขับ FIFO consumption order ที่ issue time

### 5.4 Matrix Event-type

| Source doc | Cost-layer type | Direction |
|---|---|---|
| GRN posting (fire ตอน **save**, `draft → saved`) | `good_received_note` | IN (บวกขา OUT `issue` อัตโนมัติเมื่อ location เป็น `direct`) |
| SR transfer issue | `transfer_in` + `transfer_out` | OUT @ source, IN @ destination |
| SR issue ไปยังปลายทาง direct-cost | `issue` | OUT เท่านั้น |
| Inventory-adjustment IN (`tb_stock_in`) | `adjustment_in` | IN |
| Inventory-adjustment / wastage OUT (`tb_stock_out`) | `adjustment_out` | OUT |
| Credit note | `credit_note_quantity` หรือ `credit_note_amount` | OUT (qty) หรือ value-only (`diff_amount`) |
| Period close | `close_period` (lot `CLOSE-{YYMM}-{seq}`, `out_qty` ล้างแต่ละ lot ที่ยังเหลืออยู่ให้เป็นศูนย์) | OUT, period boundary |
| Period open (next) | `open_period` (lot `OPEN-{YYMM}-{seq}`, `in_qty` สร้างแต่ละ lot ขึ้นใหม่) | IN, period boundary |
| EOP adjustment (`eop_in` / `eop_out`) | `eop_in` / `eop_out` | variant แบบ carry-in/out ที่ expose ผ่าน inventory-adjustment API (`enum_adjustment_type` มีทั้งคู่); layer carry-in ถูก value-lock เหมือน `open_period` |

## 6. Lifecycle / กติกาทางธุรกิจ

```
1. Source-document posting (เช่น GRN save, draft -> saved):
   - INSERT tb_inventory_transaction header
   - INSERT tb_inventory_transaction_detail ต่อ line
   - INSERT tb_inventory_transaction_cost_layer ต่อ lot_index
     (splitFifoCost อาจ split การรับหนึ่งครั้งออกเป็นหลาย layers
      เพื่อ reconcile ทศนิยมให้ตรงเป๊ะ)
2. Correction: เอกสาร source ใหม่ (credit note / stock-in / stock-out)
   post transaction ใหม่ของตัวเอง (ไม่เคย UPDATE ตัวต้นฉบับ)
3. Period close: INSERT headers ด้วย inventory_doc_type = 'close' และ 'open'
```

- **Append-only** การแก้ไขคือ rows ใหม่ผ่านเอกสาร source ใหม่
- **Source linkage** `(inventory_doc_type, inventory_doc_no)` คือ back-pointer; หน้าจอ list resolve มันเป็น `parent_document_no` (เลขที่ GRN/SI/SO/SR/CN หรือ code ของงวดสำหรับ close/open)
- **No backdating เข้างวด closed — ด้วยการ re-date ไม่ใช่การ reject** ทุก row ใหม่ถูก stamp เข้างวดเปิดปัจจุบัน (`resolveCurrentPeriod`); ledger ไม่เคยรับ closed-period row เพราะ stamp ไม่สน document date

## 7. ความเชื่อมโยงข้ามโมดูล

- [inventory](/th/inventory/inventory) — ตัวเลข on-hand ทุกจุดในผลิตภัณฑ์คือ running sum ของ ledger นี้ (ไม่มี balance row ที่ persist)
- [costing](/th/inventory/costing) — กฎ `COST_CALC_*` derive จาก cost-layer rows
- [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; [inventory-adjustment/wastage-reporting](/th/inventory/inventory-adjustment/wastage-reporting) &nbsp;·&nbsp; [store-requisition](/th/inventory/store-requisition) &nbsp;·&nbsp; [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) — เอกสาร source
- [inventory/period-end](/th/inventory/inventory/period-end) — เขียน `close` / `open` rows และ freeze snapshot

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_transaction` (~1048-1073), `tb_inventory_transaction_detail` (~1075-1101), `tb_inventory_transaction_cost_layer` (~1123-1164), `enum_inventory_doc_type` (~208-216), `enum_transaction_type` (~1103-1121)
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/transaction/`
- **Module landing:** [inventory](/th/inventory/inventory) § 3 (แนวคิด Stock Movement)
