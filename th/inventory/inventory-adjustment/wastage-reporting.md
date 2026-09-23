---
title: รายงานของเสีย (Wastage Reporting)
description: รายการ lot ใกล้หมดอายุและ API write-off ภายใต้ Store Operations — backend จริงตั้งแต่ 2026-08-10; write-off สร้าง Stock Out ที่ completed หนึ่งฉบับต่อ location และ post ไป ledger
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# รายงานของเสีย (Wastage Reporting)

> **At a Glance**
> **ตำแหน่ง:** Store Operations → Wastage Reporting (`/store-operation/wastage-reporting`, สิทธิ์ nav `inventory_management.stock_out.view`) — อ้างอิงไขว้จาก Inventory Adjustment เพราะ write-off ของมัน*คือ* `tb_stock_out` &nbsp;·&nbsp; **สถานะ:** **API จริงตั้งแต่ 2026-08-10** (`c9348f667`; frontend เลิกใช้ mock เมื่อ 2026-08-20 `061a0f3f`) &nbsp;·&nbsp; **Endpoints:** `GET /api/{bu}/wastage-reporting` (lot ใกล้หมดอายุ) และ `POST /api/{bu}/wastage-reporting` (write-off) &nbsp;·&nbsp; **Backend:** `apps/micro-business/src/inventory/wastage-reporting/` — ไม่มีตารางของตัวเอง; อ่าน lot ของ GRN และเขียน `tb_stock_out` &nbsp;·&nbsp; **UI วันนี้:** รายการเท่านั้น — endpoint write-off ไม่มีปุ่มใน frontend ที่ ship

![Wastage Reporting screen](/screenshots/inventory-adjustment/wastage-reporting.png)

## 1. คืออะไรและใครใช้

หน้านี้ฉบับ 2026-07-15 บรรยายหน้าจอที่เป็น **mock data เท่านั้น** (`wr-mock-data.ts`, type `WastageReport` ที่มีสถานะ `pending/approved/rejected`, CRUD ปลอม) นั่นไม่เป็นจริงอีกต่อไป — และ feature จริงมีรูปทรงต่างจาก mock ตอนนี้ Wastage Reporting คือ**รายงาน lot ใกล้หมดอายุเหนือ receipt ของ GRN ที่ commit แล้ว** บวก **endpoint write-off** ที่เปลี่ยน lot ที่เลือกให้เป็น Stock Out ที่ completed และ post ไป ledger ยังคงไม่มีตาราง `tb_wastage_report` และไม่มี workflow อนุมัติ

- **พนักงานคลัง / ครัว** (ผู้ใช้ใดก็ตามที่มี `inventory_management.stock_out.view`) — อ่านรายการ: lot ไหนหมดอายุภายใน *n* วัน เหลือกี่หน่วย มีมูลค่าเท่าใด
- **ใครก็ตามที่เรียก `POST /wastage-reporting`** — ปัจจุบันเข้าถึงได้ผ่าน API เท่านั้น (Bruno `_uncategorized/wastage-reporting/POST-write-off-wastage-reporting.bru`); หน้าจอรายการที่ ship ไม่มี action write-off
- **Inventory** — ได้รับ transaction `adjustment_out` หนึ่งรายการต่อบรรทัดที่ write-off

## 2. งานทั่วไป

| งาน | ตำแหน่ง | หมายเหตุ |
|---|---|---|
| ดู lot ที่ใกล้หมดอายุ | Store Operation → Wastage Reporting | `GET /wastage-reporting?days=30` (ช่วงเริ่มต้น `DEFAULT_EXPIRY_WINDOW_DAYS = 30`); optional `include_expired`, `status=expiring|expired`, `location_id`, `product_id`, ค้นหา + แบ่งหน้า แถบสรุป: จำนวน item, จำนวนหมดอายุแล้ว, จำนวนใกล้หมดอายุ, qty ที่เสี่ยง, มูลค่าที่เสี่ยง |
| กระโดดไปยังใบรับ | คลิกเลข GRN | เปิด `/procurement/goods-receive-note/{grn_id}` |
| Write off lot (API) | `POST /wastage-reporting` ด้วย `{ so_date?, adjustment_type_id, description?, note?, items: [{ grn_detail_item_id, qty, note? }] }` | บรรทัดถูกจัดกลุ่มตาม location; สำหรับแต่ละ location สร้าง `tb_stock_out` หนึ่งฉบับที่ `draft`, post ทุกบรรทัดผ่าน `executeAdjustmentOut` แล้วตั้ง header เป็น `completed` — ทั้งหมดในทรานแซกชันเดียว (`wastage-reporting.logic.ts`) `so_date` default เป็นวันนี้และต้องผ่านกฎงวดของ stock-out |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การกระทำ |
|---|---|---|
| รายการว่าง | ไม่มีบรรทัด GRN ที่ commit แล้วมี `expired_at` ในช่วง (`tb_good_received_note_detail_item.expired_at`, migration `20260731120000_add_inflow_price_expiry`) หรือ lot ผู้สมัครทุกตัวมี qty คงเหลือ ≤ 0 | ขยาย `days` หรือตรวจว่าใบรับมีวันหมดอายุ |
| `WASTAGE_ITEMS_REQUIRED` | `items` ว่าง | ส่งอย่างน้อยหนึ่งบรรทัด |
| Write-off ถูกปฏิเสธเรื่องปริมาณ | `qty` เกิน balance คงเหลือของ lot (`remaining_qty` = `in_qty` ของ layer − การบริโภคผ่าน `parent_lot_no`) หรือ on-hand ของ location | ลด `qty` |
| `STOCK_OUT_DATE_NOT_CURRENT_PERIOD` (422) | `so_date` นอกงวด inventory ปัจจุบัน — write-off สืบทอด guard วันที่ของ stock-out | ลงวันที่ใหม่ |

## 4. Edge Cases

- **ปริมาณคงเหลือคำนวณจาก ledger ต่อ lot** `resolveLotsByDetailItemIds` เดินจาก `tb_inventory_transaction_detail.good_received_note_detail_item_id` (เพิ่ม 2026-08-10) จากบรรทัด GRN ไปยัง `current_lot_no` ของมัน แล้วรวม `in_qty` และ `out_qty` บน `tb_inventory_transaction_cost_layer` (`parent_lot_no` สำหรับการบริโภค) lot ที่ `remaining_qty ≤ QTY_EPSILON` ถูกตัดออกจากรายการ
- **นับเฉพาะใบรับที่ commit แล้ว** (`doc_status = committed` ทั้งบน GRN และ path ของ detail); GRN ที่เป็น draft หรือ void ไม่เคยปรากฏ
- **`days_to_expiry` เป็นจำนวนเต็มมีเครื่องหมาย** — ติดลบสำหรับ lot ที่หมดอายุแล้ว (`status = expired`); รายการเรียงตาม `expired_at` จากน้อยไปมาก
- **หนึ่ง Stock Out ต่อ location ไม่ใช่ต่อการเรียก** write-off ที่ครอบสาม location สร้างเอกสาร `tb_stock_out` สามฉบับ แต่ละฉบับมี `so_no` ของตัวเอง ทั้งหมด tag ด้วย `adjustment_type_id` และ `description` ของผู้เรียก
- **ไม่มี UI สำหรับ write-off** `routes/store-operation/wastage-reporting/` มีเพียง `use-wastage-report.ts` (GET), `use-wr-table.tsx` และ `wr-component.tsx`; ไฟล์ฟอร์ม / mock ถูกลบเมื่อ 2026-08-20 การ void Stock Out ของ wastage ทำจากหน้าจอ Inventory Adjustment เหมือน stock-out อื่น ๆ
- **Permission เป็นของจริงแต่หยาบ** nav entry ถูก gate ด้วย `inventory_management.stock_out.view` (`constant/module-list.ts`); guard ของ gateway คือ `wastageReporting.findAll` / `wastageReporting.writeOff`

## 5. รูปทรงข้อมูล (API response)

ที่มา: `apps/backend-gateway/src/application/wastage-reporting/swagger` และ `apps/micro-business/src/inventory/wastage-reporting/dto/wastage-reporting.serializer.ts`

| ฟิลด์ | หมายเหตุ |
|---|---|
| `grn_detail_item_id`, `grn_detail_id`, `grn_id`, `grn_no`, `grn_date` | บรรทัดใบรับที่ lot มาจาก — `grn_detail_item_id` คือ key ที่ write-off รับกลับ |
| `product_id`, `product_code`, `product_name`, `product_local_name`, `product_sku` | Snapshot ของสินค้า |
| `location_id`, `location_code`, `location_name` | Location ที่รับ — Stock Out ของ write-off ถูกสร้างที่นี่ |
| `lot_no` | lot ของ ledger (`{location_code}{YYMM}{seq4}`) จาก `tb_inventory_transaction_detail.current_lot_no` ที่ลิงก์ |
| `expired_at`, `days_to_expiry`, `status` (`expiring` / `expired`) | ข้อมูลวันหมดอายุจากบรรทัด GRN |
| `remaining_qty`, `cost_per_unit`, `remaining_value`, หน่วย inventory | Balance และมูลค่าที่เสี่ยงซึ่ง derive จาก ledger |

Response ของ write-off: header `tb_stock_out` ที่สร้าง — `{ id, so_no, doc_status: completed, location_id, location_code, location_name }` ต่อ location

## 6. ส่วนอ้างอิง

- [inventory-adjustment](/th/inventory/inventory-adjustment) — write-off เป็น `tb_stock_out` ธรรมดา (`adjustment_type_id` บังคับ) และปรากฏในรายการ Stock Out ซึ่ง void ได้ที่นั่น
- [inventory/transaction](/th/inventory/inventory/transaction) — แต่ละบรรทัดที่ write-off คือการบริโภค cost-layer `adjustment_out` จาก lot ที่ระบุชื่อ
- [good-receive-note](/th/inventory/good-receive-note) — `expired_at` ถูกเก็บบนบรรทัด GRN; รายการใกล้หมดอายุคือ view เหนือบรรทัดเหล่านั้น
- [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — master ของ reason ที่ write-off อ้างอิง

## 7. แหล่งอ้างอิง

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/wastage-reporting/` (`wastage-reporting.service.ts` — `findNearExpiry`, `resolveLotsByDetailItemIds`; `wastage-reporting.logic.ts` — `WastageReportingLogic.writeOff`, `groupWriteOffByLocation`; `dto/wastage-reporting.dto.ts`, `dto/wastage-reporting.serializer.ts`); gateway `apps/backend-gateway/src/application/wastage-reporting/wastage-reporting.controller.ts` (`@Controller('api/:bu_code/wastage-reporting')`)
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/wastage-reporting/` (`GET-find-near-expiry-wastage-reporting.bru`, `POST-write-off-wastage-reporting.bru`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/store-operation/wastage-reporting/` (`wr-component.tsx`, `use-wr-table.tsx`, `use-wastage-report.ts`); gate ของ nav ใน `constant/module-list.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/710-wastage-reporting.spec.ts` (20 เทส, user story ที่ generate `docs/user-stories/710-wastage-reporting.md`) — พฤติกรรมของรายการ, สรุป และลิงก์ GRN; ไม่มี coverage ของ write-off เพราะ UI ไม่มี
