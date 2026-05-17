---
title: การเติมสต๊อก (Stock Replenishment)
description: ข้อเสนอ SR ที่ generate อัตโนมัติขับโดย threshold min / max / par / reorder ที่แต่ละสถานที่ — คู่ขับโดยนโยบายของ flow Store Requisition ที่ทำด้วยมือ
published: true
date: 2026-05-17T12:00:00.000Z
tags: store-requisition, replenishment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# การเติมสต๊อก (Stock Replenishment)

> **At a Glance**
> **เจ้าของ:** Inventory Controller (review / submit) &nbsp;·&nbsp; service account ของ Cron (draft เท่านั้น) &nbsp;·&nbsp; **ตาราง:** ไม่มีเฉพาะ — output เป็น `tb_store_requisition` draft &nbsp;·&nbsp; **Trigger:** cron กลางคืน (หรือ on-demand) &nbsp;·&nbsp; **Inputs:** `tb_product_location` (min/max/par/reorder) + on-hand + on-order &nbsp;·&nbsp; **สรุป 1 บรรทัด:** cron กวาด deficit และ pre-fill SR drafts; มนุษย์อนุมัติ

## 1. ภาพรวมและผู้ใช้งาน

Stock Replenishment คือ **variant ที่ขับโดยนโยบายของ [[store-requisition]]** Job ที่ตั้งเวลากวาดทุกคู่ `(product, location)` ที่มี threshold ตั้งค่าและเสนอ SR draft สำหรับทุก location ใต้ par Inventory Controller review ตัดและ submit — จากจุดนั้นเป็น SR ปกติที่วิ่งผ่าน workflow อนุมัติและ fulfillment มาตรฐาน

- **Inventory Controller** — review draft ที่ generate อัตโนมัติและ submit
- **Cron service account** — insert draft เท่านั้น (ไม่สามารถดันเกิน `draft`)
- **ไม่มีตาราง `tb_replenishment`** การ run อยู่ใน-memory ใน Go cron service; artifact ถาวรเดียวคือ SR draft

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู draft ที่ generate วันนี้ | Store Operation → Stock Replenishment inbox | หนึ่ง draft ต่อกลุ่ม `(source_location, destination_location)` |
| อนุมัติ SR เติมสต๊อก | เปิด draft → ตัดบรรทัดถ้าจำเป็น → **Submit** | พลิก `draft → in_progress` route ผ่าน chain อนุมัติ SR มาตรฐาน |
| Trigger sweep ad-hoc | Inventory Controller → **Run now** | idempotency เดียวกันกับ run กลางคืน; ปลอดภัยที่จะ re-trigger |
| Override par / max สำหรับสินค้า | [[product]] → tab location → แก้ `tb_product_location` | มีผลใน run ถัดไป |
| ตั้งค่าสถานที่ต้นทางสำหรับปลายทาง | การ config ต่อ-BU | ถ้าไม่มีต้นทาง deficit flag สำหรับ SR ด้วยมือแทน |
| สอบสวนการเติมที่ขาด | Check `tb_product_location` มีอยู่และ `min_qty > 0` | คู่ที่ไม่มีนโยบายหรือ `min_qty = 0` ถูกแยก |
| Check log run cron | log service `../micro-cronjobs/` | State run อยู่ใน cron service ไม่ใช่ DB tenant |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / Message | สาเหตุ | Action |
|---|---|---|
| สินค้าไม่ปรากฏใน draft | ไม่มีแถว `tb_product_location` หรือ `min_qty = 0` | เพิ่ม / อัปเดตแถวนโยบายใน [[product]] |
| สถานที่ต้นทาง flag สำหรับ SR ด้วยมือ | ไม่มีต้นทาง config สำหรับปลายทาง | Config ต้นทางต่อ BU หรือตั้ง SR ด้วยมือ |
| Run ข้ามวันนี้ | งวดของวันนี้เป็น `closed` / `locked` | Re-run หลังงวด flip; หรือใช้วันที่งวดปัจจุบัน |
| Draft ดูซ้ำ | ไม่มี — idempotent ต่อ `(from, to, date)` | Re-run อัปเดตบรรทัดตำแหน่ง ไม่ใช่ซ้ำ |
| ปริมาณการเติมสูงเกิน | `on_order` ไม่ถูกนับเข้า check `(on_hand + on_order)` | ยืนยัน PO เปิด / SR transfer-in ที่รอสะท้อน; flag ให้ dev |
| Service account submit ไม่ได้ | ตามการออกแบบ — submit ต้องการ Inventory Controller / Manager | การ review โดยมนุษย์คือ safety gate (`INV_AUTH_004`) |

## 4. กรณีพิเศษ

- **ไม่มี schema เฉพาะ** ไม่มี `tb_replenishment` หรือ `tb_replenishment_run` ใน schema tenant; artifact ถาวรคือ `tb_store_requisition` เท่านั้น
- **Idempotency** การ re-run cron วันเดียวกัน reuse draft ที่มีต่อ `(from, to)` — ไม่ spawn ซ้ำ
- **`on_order` รวมทั้ง** PO เปิดที่มุ่งหน้าไปปลายทางและ SR transfers-in ที่อยู่ระหว่างดำเนินการ — ป้องกันการเติมซ้ำขณะ SR ก่อนหน้ายังในเที่ยวบิน
- **Gate งวด** ถ้างวดของวันนี้เป็น `closed` / `locked` cron ข้ามการ emit และเขียนเข้า run log
- **ไม่เคย auto-submit** Cron ไม่อาจดันเกิน `draft` การ review โดยมนุษย์ (`INV_AUTH_004`) บังคับ
- **การ resolve ต้นทาง** สถานที่ต้นทางอ่านจาก config ต่อ-BU (โดยทั่วไป "main store"); ปลายทางที่ไม่มีต้นทาง fall back เป็น SR ด้วยมือ

---

## 5. กระบวนการ (Dev)

Stock Replenishment **ไม่ใช่ตาราง Prisma แยก** — เป็นกระบวนการที่ cron ขับเหนือสองตาราง upstream

### 5.1 `tb_product_location` (นโยบาย)

| ฟิลด์ | Type | คำอธิบาย |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key |
| `product_id` | `String @db.Uuid` | FK ไปยัง `tb_product` |
| `location_id` | `String? @db.Uuid` | FK ไปยัง `tb_location` (สถานที่บริโภค) |
| `min_qty` | `Decimal(20,5)?` | Trigger: เติมเมื่อ `on_hand + on_order < min_qty` |
| `max_qty` | `Decimal(20,5)?` | ระดับสต๊อกเป้าหมายหลังการเติม |
| `par_qty` | `Decimal(20,5)?` | par เชิงปฏิบัติการ (โดยทั่วไประหว่าง min และ max) |
| `re_order_qty` | `Decimal(20,5)?` | ปริมาณสั่งแนะนำเมื่อ trigger fire (มัก `max - on_hand`) |
| คอลัมน์ Audit | — | มาตรฐาน |

**Constraints:** `@@unique([product_id, location_id, deleted_at])` หนึ่งแถวนโยบายต่อ `(product, location)`

### 5.2 `tb_store_requisition` (output)

SR ที่ generate มี `sr_type` (`issue` หรือ `transfer`), `from_location_id` (ต้นทาง — โดยทั่วไป main store), `to_location_id` (เอาท์เลตบริโภค), `requestor_id` (service account), `description` (เช่น "Auto-replenishment 2026-05-17"), `doc_status = 'draft'`

## 6. Algorithm / วงจรชีวิต

```
Cron run กลางคืน (หรือ on-demand):

1. SELECT ทุกแถว tb_product_location ที่ min_qty > 0 AND ไม่ถูก delete
2. สำหรับแต่ละ (product, location):
   - on_hand = InventoryStatus.QuantityOnHand ปัจจุบันที่ location
   - on_order = ยอดรวม qty บน PO เปิด + SR transfer-in ที่รอ
   - deficit = max_qty - (on_hand + on_order)     // หรือ re_order_qty ถ้า config
   - if (on_hand + on_order) < min_qty AND deficit > 0:
       emit_line(product, location, deficit)
3. GROUP บรรทัดที่ emit BY (source_location, destination_location)
4. INSERT tb_store_requisition (doc_status = draft, requestor = service account)
   INSERT tb_store_requisition_detail ต่อบรรทัด
   -> ปรากฏใน Stock Replenishment inbox
5. Inventory Controller review ตัด submit:
   - draft -> in_progress; chain อนุมัติ SR มาตรฐานจากที่นี่
```

ถ้า draft มีอยู่แล้วสำหรับ `(from, to, date)` cron อัปเดตบรรทัดตำแหน่ง (idempotency)

## 7. ความเชื่อมโยงข้ามโมดูล

- [[store-requisition]] — ประเภทเอกสารที่ผลิต; วงจรชีวิตปลายน้ำเหมือนกัน
- [[inventory]] — แหล่ง `on_hand` สำหรับการคำนวณ deficit
- [[product]] — นโยบาย `tb_product_location` อยู่ใต้ master สินค้า
- [[master-data/location]] — การตั้งค่า min / max / par / reorder ต่อ-location
- [[purchase-order]] — `on_order` รวม qty PO เปิด
- [[inventory/transaction]] — เมื่อ SR post, ledger เขียน events `store_requisition`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_location` (~4364-4399), `tb_store_requisition` (~2922-2984), `enum_sr_type` (~224-227)
- **Frontend:** `../carmen-inventory-frontend/app/(root)/store-operation/stock-replenishment/`
- **Cron job:** `../micro-cronjobs/` — Go service ที่ host การ sweep กลางคืน State run อยู่ใน cron service (ไม่มีตาราง tenant)
- **Module landing:** [[store-requisition]] § 3 (ประเภทการเคลื่อนย้าย workflow อนุมัติ)
