---
title: การปรับสต๊อก (Inventory Adjustment) — กติกาทางธุรกิจ
description: กฎการตรวจสอบ การคำนวณ การกำหนดสิทธิ์ และการ posting สำหรับ stock-in / stock-out ด้วยมือ — draft ตอนสร้าง, เขียน ledger ตอน commit, กลับรายการตอน void
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — กติกาทางธุรกิจ

> **At a Glance**
> **กลุ่มกฎ:** `ADJ_VAL_*` การตรวจสอบ &nbsp;·&nbsp; `ADJ_CALC_*` การคำนวณ &nbsp;·&nbsp; `ADJ_POST_*` การ posting
> **จำนวนกฎ:** 27 ข้อ trace ไปยัง `ia-form-schema.ts`, `stock-in.service.ts` / `stock-out.service.ts`, `inventory-period.helper.ts`, `inventory-transaction.service.ts` และ `packages/error-catalog/src/catalog.ts`
> **กลุ่มผู้ใช้:** ผู้เขียน test + developer
> **ข้อค้นพบสำคัญ (ตรวจซ้ำ 2026-09-22):** `create()` เขียน `doc_status = draft` และไม่ทำอย่างอื่น; `commit()` คือ posting event; ยังคงไม่มีขั้นตอนอนุมัติ, threshold หรือ GL entry

## 1. ภาพรวม

หน้านี้รวบรวมกฎที่บังคับใช้จริงโดย **โมดูล inventory-adjustment** — เลเยอร์เอกสารสองตาราง (`tb_stock_in` / `tb_stock_out`) สำหรับการแก้ไขสต๊อกด้วยมือ ฉบับ 2026-07-15 ถูกเขียนเทียบกับโค้ดที่การสร้าง*คือ*การ post; commit ของ backend `281a16399` (2026-07-30) แยกสิ่งนั้นเป็น **create → draft** และ **commit → post** และชุดการเปลี่ยนแปลงในเดือน 2026-08 เพิ่ม guard วันที่ในงวดฝั่ง server (`4898ec8d3`, `3ff5e05dc`, `6ca3266e1`), การออกเลข stock-out ตามวันที่เอกสาร (`5d878a6c8`) และการตรวจ on-hand ล่วงหน้าของ stock-out ทุกกฎด้านล่างถูกอ่านซ้ำจาก HEAD สิ่งที่**ไม่**เปลี่ยน: ไม่มีห่วงอนุมัติที่ gate ด้วย threshold, ไม่มีการลงบัญชี GL/journal, ไม่มี UI ป้อน lot, ไม่มีการตรวจแบ่งแยกหน้าที่

## 2. กฎการตรวจสอบ

Rule IDs ใช้รูปแบบ `ADJ_VAL_NNN` "Client" = Zod ใน `ia-form-schema.ts` (รันตอน Save และก่อน confirm dialog ของ Commit); "Server" = `StockInService` / `StockOutService` และ error catalog

| Rule ID | เงื่อนไข | บังคับใช้โดย | พฤติกรรม |
| ------- | -------- | ------------ | -------- |
| `ADJ_VAL_001` | `location_id` บังคับ | Client (Zod `.min(1)`) และ server ตอน create **และ** commit (`STOCK_IN_LOCATION_REQUIRED` / `STOCK_OUT_LOCATION_REQUIRED`) | 400 `Location is required for stock in` / `…stock out` |
| `ADJ_VAL_002` | `adjustment_type_id` บังคับและควรตรงกับทิศทางของเอกสาร | Client เท่านั้น (Zod `.refine`; picker กรอง `tb_adjustment_type` ด้วย `type`) Server enrich header จากแถวที่อ้างอิง (`enrichment.enrich('tb_stock_in', …)`) และไม่ตรวจซ้ำ `type` | การเรียก API โดยตรงด้วย reason ผิดทิศทางไม่ถูกปฏิเสธฝั่ง server |
| `ADJ_VAL_003` | วันที่เอกสารต้องอยู่ในงวด | Client (Zod `.refine` เทียบกับช่วงงวดปัจจุบัน) **และ server** — stock-in: `assertDateInOpenPeriod(si_date)` ตอน create และ commit; stock-out: `assertDateInCurrentPeriod(so_date)` ตอน create และ commit (`inventory-period.helper.ts`) | 422 `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD` ("The stock-in date does not fall inside any open period"); 422 `STOCK_OUT_DATE_NOT_CURRENT_PERIOD` ("Stock-outs can only be dated inside the current period ({period}: {start} to {end})"); 422 `STOCK_OUT_NO_OPEN_PERIOD` เมื่อไม่มีงวดเปิดเลย สังเกตความไม่สมมาตร: stock-in ลงวันที่ในงวด `open`/`locked` ใดก็ได้ stock-out ลงได้เฉพาะงวดปัจจุบัน (open ที่เร็วสุด) |
| `ADJ_VAL_004` | ต้องมีอย่างน้อยหนึ่งบรรทัด | Client (Zod `items.min(1)`) และ server ตอน create (`stock_in_detail.add` ไม่ว่าง) และ commit (`STOCK_IN_DETAIL_ITEMS_REQUIRED` / `STOCK_OUT_DETAIL_ITEMS_REQUIRED`) | 400 `Stock in detail items are required` / `…out…` |
| `ADJ_VAL_005` | `product_id` ของแต่ละบรรทัดต้องมีแถว `tb_product` จริง | Client (`.min(1)`) และ enrichment ฝั่ง server (`enrich('tb_stock_in_detail', …)`; endpoint ของ detail คืน `PRODUCT_NOT_FOUND`) | ปฏิเสธต่อเอกสาร / ต่อบรรทัด |
| `ADJ_VAL_006` | `qty ≥ 0` ของแต่ละบรรทัด | Client เท่านั้น (Zod `.min(0)` — ผ่อนจาก `≥ 1` เดิม; `e9d7fd35c` "xxx_qty can accept float") | รับปริมาณเศษส่วน; บรรทัดที่เป็นศูนย์ผ่าน validation แต่ post ไม่ได้อะไรที่มีประโยชน์ |
| `ADJ_VAL_007` | `cost_per_unit ≥ 0` ของแต่ละบรรทัด | Client เท่านั้น (Zod `.min(0)`) มีความหมายเฉพาะ Stock-In — grid ของ Stock-Out ซ่อนคอลัมน์นี้และ server ไม่เคย persist สำหรับบรรทัด stock-out | ปฏิเสธด้วยข้อความ non-negative-cost บน Stock-In |
| `ADJ_VAL_008` | `description` (header และบรรทัด) ≤ 256 ตัวอักษร; ไม่บังคับ | Client เท่านั้น | คำอธิบายว่างเปล่า save และ commit ได้ |
| `ADJ_VAL_009` | ประเภทตำแหน่งถูกจำกัดเป็น Inventory / Consignment | Client เท่านั้น (`locationTypes` ของ `LookupUserLocation`) Server ต้องการเพียง id | การเรียก API โดยตรงด้วย location ประเภท `direct` ไม่ถูกปฏิเสธ |
| `ADJ_VAL_010` | การตรวจ on-hand ล่วงหน้าของ Stock-Out ตอน commit: Σ ที่ขอต่อสินค้า ≤ `getOnHandQty(product, location)` | Server (`StockOutService.commit` → `findStockShortage` ก่อนเปิดทรานแซกชัน) | 400 `STOCK_OUT_INSUFFICIENT_STOCK`: `Insufficient stock for {product} at {location}: on hand {x}, requested {y}`; ไม่มีอะไรถูกเขียน draft ยังอยู่ `Insufficient stock. Requested: …, Available: …` ของ ledger เอง (Error → 500) ยังคงเป็น guard ที่สองภายใน `createAverageConsumption` / `createFifoConsumption` |
| `ADJ_VAL_011` | Optimistic concurrency: ต้องส่ง `doc_version` ตอน save และ commit และตรงกับค่าที่เก็บไว้ | Server (`COMMON_DOC_VERSION_REQUIRED`; Prisma `where: { id, doc_version }`) | version ที่ล้าสมัยไม่ match แถวใด → update/commit ล้มเหลว; frontend อ่าน `doc_version` ที่เพิ่มขึ้นใหม่หลังทุก save (`useUpdateInventoryAdjustment`) |
| `ADJ_VAL_012` | เงื่อนไขก่อน void: ยังไม่ `voided`; สำหรับ stock-in ที่ post แล้ว on-hand ที่ตำแหน่งต้องรองรับการกลับรายการของทุกบรรทัดที่ post แล้ว | Server (`STOCK_IN_ALREADY_VOIDED` / `STOCK_OUT_ALREADY_VOIDED`; loop ตรวจ on-hand ของ `voidStockIn`) | 400 `Stock in is already voided`; `Cannot void: product <code> has insufficient on-hand qty (<X>) at this location to reverse <Y>` (INVALID_ARGUMENT) `voidStockOut` กลับรายการด้วย `executeAdjustmentIn` และไม่มีเงื่อนไข on-hand |
| `ADJ_VAL_013` | Reason-direction ต้องตรงกัน (`tb_adjustment_type.type` เทียบกับต้นเอกสาร) | Client เท่านั้น | ไม่สามารถบังคับใช้นอกเหนือจาก picker UI |
| `ADJ_VAL_014` | มีเพียง `draft` ที่ commit, save หรือเพิ่ม/แก้/ลบบรรทัดได้; มีเพียง `draft` ที่ลบได้ | Server (`STOCK_IN_ONLY_DRAFT_COMMITTABLE`, `STOCK_IN_COMPLETED_NO_UPDATE`, `STOCK_IN_NON_DRAFT_NO_ADD/UPDATE/DELETE_DETAIL`, `STOCK_IN_COMPLETED_NO_DELETE` และคู่แฝด `STOCK_OUT_*`) | 400 `Only a draft Stock In can be committed`; `Cannot update a completed Stock In — inventory has already been adjusted`; `Cannot delete a completed Stock In — …` |
| `ADJ_VAL_015` | `doc_status` เปลี่ยนผ่าน save ไม่ได้ | Server (`STOCK_IN_STATUS_CHANGE_NOT_ALLOWED` / `STOCK_OUT_STATUS_CHANGE_NOT_ALLOWED` เมื่อ `doc_status ≠ draft` ใน payload) | 400 `doc_status cannot be changed on save — use the commit or void endpoint` |

## 3. กฎการคำนวณ

| Rule ID | สูตร |
| ------- | ---- |
| `ADJ_CALC_001` (ยอดบรรทัด) | `total_cost = qty × cost_per_unit` คำนวณฝั่ง client (`use-ia-item-table.tsx`) และ persist บน `tb_stock_in_detail`; บน Stock-Out ค่านี้เป็นเพียงการแสดงผลและไม่เคย persist |
| `ADJ_CALC_002` (ข้อเสนอต้นทุน Stock-In) | `cost_per_unit` เติมเริ่มต้นผ่าน `useProductCostByLocationQty(buCode, productId, locationId, qty)` — ต้นทุนปัจจุบันของสินค้าที่ location นั้น — ทันทีที่เลือกสินค้า (`e246abaa`); แก้ไขได้ และค่าที่ commit คือค่าที่ ledger ใช้ |
| `ADJ_CALC_003` (Preview ต้นทุน Stock-Out) | Preview แสดงผลเท่านั้นจาก hook ต้นทุนสินค้า; ไม่มีบทบาทในต้นทุนที่ post จริง |
| `ADJ_CALC_004` (ต้นทุนเฉลี่ยใหม่, BU แบบ Average) | ตอน commit Stock-In `executeAdjustmentIn` เขียน layer ขาเข้าใหม่และ restamp `average_cost_per_unit` ของสินค้า (`restampAverageCostForProducts`) — logic ของ ledger ทั่วไปที่แชร์กับ GRN |
| `ADJ_CALC_005` (การบริโภคแบบ FIFO, Stock-Out) | `createFifoConsumption` บริโภคจาก `getAvailableFifoLots` ตามลำดับ `lot_seq_no` จนกว่าปริมาณที่ขอจะครบ หนึ่ง layer ขาออกต่อ lot ที่บริโภค; write-off ของ wastage ส่ง `target_lot_nos` เพื่อบริโภค lot ที่ระบุชื่อ |
| `ADJ_CALC_006` (การบริโภคแบบ Average, Stock-Out) | `createAverageConsumption` คิดปริมาณขาออกทั้งหมดที่ต้นทุนเฉลี่ยปัจจุบันของ BU |
| `ADJ_CALC_007` (การปัดเศษ) | ค่าเงินปัดเศษเป็น 2 ตำแหน่งทศนิยมทุกครั้งที่เขียน cost layer; คอลัมน์ปริมาณเก็บ 5 ตำแหน่งทศนิยม |
| `ADJ_CALC_008` (period stamp) | layer ของ stock-in: `resolvePeriodForDate(si_date)` (throw `No open period covers …` ถ้าไม่มี — เข้าไม่ถึงในทางปฏิบัติเพราะ `ADJ_VAL_003` รันก่อน) การบริโภคของ stock-out และการกลับรายการของ void ทั้งสองแบบ: `resolveCurrentPeriod` (งวด `open`/`locked` ที่เร็วสุด) |
| `ADJ_CALC_009` (เลขที่เอกสาร) | `si_no` / `so_no` ถูกสร้างโดย running-code service จาก**วันที่เอกสาร** (`generateSINo(si_date)` / `generateSONo(so_date)`, `5d878a6c8`) ไม่ใช่วันที่สร้าง |

## 4. การกำหนดสิทธิ์

ไม่มีการกำหนดสิทธิ์ตาม role หรือ threshold ในโมดูลนี้ nav entry, หน้ารายการ และหน้าจอสร้าง/แก้ไข gate ด้วยสิทธิ์ทั่วไปตัวเดียว `inventory_management.view` (`constant/module-list.ts`) แคตตาล็อกของ frontend ยังนิยาม key CRUD `inventory_management.stock_in.*` / `inventory_management.stock_out.*` (`constant/permissions.ts`) แต่มัน gate nav entry ของ Store Operations สองตัวที่**ต่างกัน** — Stock Replenishment (`.stock_in.view`) และ Wastage Reporting (`.stock_out.view`) — ไม่ใช่หน้าจอของโมดูลนี้ gateway ละเอียดกว่า: `stock-ins.controller.ts` guard `stockIn.findAll / findOne / create / update / commit / delete / print / getStockMovements` (และคู่แฝด `stockOut.*`) ผ่าน `AppIdGuard`; `inventory-adjustments.controller.ts` guard `inventoryAdjustment.findAll / findOne / print`

## 5. กฎการ Posting

Rule IDs ใช้รูปแบบ `ADJ_POST_NNN`

| Rule ID | เหตุการณ์ | ผลกระทบ |
| ------- | -------- | ------- |
| `ADJ_POST_001` | `create()` — `POST /stock-ins` \| `/stock-outs` (**Save** หรือครึ่งแรกของ **Commit** บนฟอร์มใหม่) | ทรานแซกชันเดียว: header ที่ `doc_status = draft`, `doc_version = 0`, `si_no`/`so_no` จากวันที่เอกสาร, snapshot ของ location / reason ที่ enrich แล้ว; สร้างแต่ละบรรทัด detail (บรรทัด stock-in พร้อม `cost_per_unit`, `total_cost`, `expired_at` optional; บรรทัด stock-out ไม่มีต้นทุน) **ไม่มีการเขียน ledger** |
| `ADJ_POST_002` | `update()` — `PATCH /{id}/save` | เฉพาะ draft (`ADJ_VAL_014`) ใช้ฟิลด์ header และ `stock_in_detail.{add, update, remove}`; ตรวจและเพิ่ม `doc_version`; `doc_status` ใน payload ต้องเป็น `draft` (`ADJ_VAL_015`) endpoint ของ detail `POST/PUT/DELETE /{id}/details[/:detail_id]` ใช้กฎ draft-only เดียวกัน |
| `ADJ_POST_003` | `commit()` — `PATCH /{id}/commit` `{ doc_version }` | เฉพาะ draft ตรวจซ้ำ location, บรรทัด, วันที่ (`ADJ_VAL_003`) และสำหรับ stock-out ตรวจ on-hand (`ADJ_VAL_010`); resolve `calculation_method` ของ BU; จากนั้นในทรานแซกชันเดียว ต่อบรรทัด: `executeAdjustmentIn` (stock-in: layer ขาเข้าใหม่ที่ต้นทุนที่กรอก, lot `{location_code}{YYMM}{seq4}`, `at_period` จาก `si_date`) หรือ `executeAdjustmentOut` (stock-out: การบริโภคแบบ FIFO / average), ประทับ `inventory_transaction_id` บนบรรทัด; header → `completed`, `doc_version + 1` |
| `ADJ_POST_004` | `delete()` — `DELETE /{id}` | เฉพาะ draft; soft-delete ของ header และบรรทัด completed → `STOCK_IN_COMPLETED_NO_DELETE` |
| `ADJ_POST_005` | `voidStockIn()` / `voidStockOut()` — `DELETE /{id}/void` `{ void_reason }` | ตรวจว่ายังไม่ void; stock-in ยังตรวจว่า on-hand รองรับการกลับรายการของแต่ละบรรทัดที่ post แล้ว จากนั้นในทรานแซกชันเดียว: สำหรับทุกบรรทัดที่มี `inventory_transaction_id` เขียนขาตรงข้าม (`executeAdjustmentOut` สำหรับ stock-in, `executeAdjustmentIn` สำหรับ stock-out) ที่ต้นทุนที่ ledger แก้ไข ณ เวลา void, `at_period` = งวดปัจจุบัน; header `doc_status = voided`, ตั้ง `deleted_at` / `deleted_by_id`, เก็บ `info.void_reason` `draft` (ไม่มีบรรทัดที่ post แล้ว) เพียงถูก mark เป็น voided และ soft-delete เนื่องจากแถวถูก soft-delete มันจึงหายจาก query ของ list และ detail การเข้าถึงจาก UI: **Void** แสดงเฉพาะในโหมด Edit บน draft; การ void เอกสารที่ post แล้วทำได้ผ่าน API เท่านั้น |
| `ADJ_POST_006` | ผู้ผลิตแถว `tb_stock_in` / `tb_stock_out` รายอื่น | `submit()` ของ [physical-count](/th/inventory/physical-count) เขียนแถวส่วนเกิน/ขาดโดยตรงที่ `completed` โดยไม่มี reason code และ**ไม่เรียก ledger** (ยืนยันแล้ว: ไม่มีการอ้างอิง `inventoryTransactionService` ใน `physical-count/*.ts`) `writeOff()` ของ [wastage-reporting](/th/inventory/inventory-adjustment/wastage-reporting) สร้าง stock-out หนึ่งฉบับต่อ location ที่ `draft`, post แต่ละบรรทัดด้วย `executeAdjustmentOut(target_lot_nos)` และตั้ง `completed` — ทั้งหมดในการเรียกเดียว |

## 6. แหล่งอ้างอิง

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) — รูปทรง canonical ของ `tb_stock_in` / `tb_stock_out` / `tb_adjustment_type`
- ส่วนคู่ขนาน: [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) — กฎเหล่านี้แสดงผลอย่างไรในหน้า persona
- Frontend: `ia-form-schema.ts` (กฎ Zod), `use-ia-item-table.tsx` (`recalcTotal`, การเติมต้นทุนล่วงหน้า), `ia-form.tsx` (`confirmCommit`, `isReadOnly`), `ia-form-hero.tsx` (การ gate ปุ่ม), `use-inventory-adjustment.ts` (endpoints)
- Backend: `apps/micro-business/src/inventory/stock-in/stock-in.service.ts`, `.../stock-out/stock-out.service.ts`, `.../inventory-period.helper.ts` (`assertDateInOpenPeriod`, `assertDateInCurrentPeriod`), `.../inventory-transaction/inventory-transaction.service.ts` (`executeAdjustmentIn` / `executeAdjustmentOut`), `packages/error-catalog/src/catalog.ts` (`STOCK_IN_*` / `STOCK_OUT_*` รวมถึง `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD`, `STOCK_OUT_DATE_NOT_CURRENT_PERIOD`, `STOCK_OUT_NO_OPEN_PERIOD`, `STOCK_OUT_INSUFFICIENT_STOCK`, `*_ONLY_DRAFT_COMMITTABLE`, `*_STATUS_CHANGE_NOT_ALLOWED`)
- Bruno: `collections/carmen-inventory/inventory/stock-in/`, `inventory/stock-out/` (`POST-create`, `PATCH-update`, `PATCH-commit`, `DELETE-void-*`, `DELETE-remove`, `GET-print-to-report`, `details/`)
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — ledger ร่วมและกฎ costing method ที่การ post ของโมดูลนี้ป้อนเข้าไป; [inventory/period-end](/th/inventory/inventory/period-end) — draft block Start Period Close
