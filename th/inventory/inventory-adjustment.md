---
title: การปรับสต๊อก (Inventory Adjustment)
description: การแก้ไข stock-in / stock-out ด้วยมือ นอกเหนือจากการจัดซื้อและการเบิกใช้ — draft, commit เพื่อ post, void เพื่อกลับรายการ; บวก write-off ของ wastage ใกล้หมดอายุ
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การแก้ไขสต๊อกด้วยมือ นอกเหนือจากการจัดซื้อ (GRN) และการเบิกใช้ (Store Requisition) — เอกสารสองสายที่เป็นอิสระต่อกัน คือ Stock-In (`tb_stock_in`) และ Stock-Out (`tb_stock_out`) จัดประเภทโดย master ของ reason code ร่วมกัน (`tb_adjustment_type`) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ใช้ใดก็ตามที่มีสิทธิ์ `inventory_management.view` (ไม่มี role อนุมัติแยกต่างหากในโค้ด) &nbsp;·&nbsp; **วงจรชีวิต:** `draft` → **Commit** → `completed` (posted) → **Void** → `voided` &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_stock_in`, `tb_stock_in_detail` (พร้อม `expired_at`), `tb_stock_out`, `tb_stock_out_detail`, `tb_adjustment_type` &nbsp;·&nbsp; **หน้าย่อย:** 14

![การปรับสต๊อก (Inventory Adjustment) screen](/screenshots/inventory-adjustment/index.png)

## 1. ภาพรวม

**Inventory Adjustment** ครอบคลุมเอกสารสองประเภทภายใต้หน้าจอเดียว `/inventory-management/inventory-adjustment` (`?type=stock-in` / `?type=stock-out`, filter ของหน้ารายการ `adj_type`): **Stock-In** (การแก้ไขเพิ่ม — ของพบใหม่ ส่วนเกินจากการนับ) และ **Stock-Out** (การแก้ไขลด — ของเสียหาย หมดอายุ ขาดจากการนับ) ทั้งสองเป็นเอกสารอิสระต่อกัน คือ `tb_stock_in` และ `tb_stock_out` ไม่ใช่ variant ของ entity `tb_inventory_adjustment` ร่วมกันแต่อย่างใด ทั้งคู่มีโครงสร้าง header เหมือนกัน — เลขที่เอกสาร (`si_no` / `so_no`), วันที่, เหตุผล (`adjustment_type_id`, แสดงผลเป็น **Reason**), ตำแหน่ง, คำอธิบาย และบรรทัดสินค้าหนึ่งรายการขึ้นไปพร้อม `qty`, `cost_per_unit`, `total_cost` — และทั้งคู่เชื่อมกับ ledger ของ [inventory](/th/inventory/inventory) ผ่าน `inventory_transaction_id` ที่ nullable ซึ่งถูก stamp บนแต่ละบรรทัด**ตอน commit**

**การสร้างไม่ใช่การ post อีกต่อไป** หน้านี้ฉบับ 2026-07-15 บันทึกว่า `create()` เขียน `doc_status = completed` และ post ledger ทันที ทำให้ Edit / Void เข้าไม่ถึง เมื่อ 2026-07-30 backend (`281a16399`, "si and so endpoint create are no longer mean complete must call /commit") เปลี่ยนเรื่องนั้น: ตอนนี้ `POST /stock-ins` / `POST /stock-outs` สร้าง **`draft`**, `PATCH /{id}/save` แก้ไขมัน และ **`PATCH /{id}/commit`** คือ posting event เพียงจุดเดียว — มัน re-validate วันที่เอกสารเทียบกับงวด inventory, ตรวจบรรทัด stock-out กับ on-hand ล่วงหน้า, เรียก `executeAdjustmentIn` / `executeAdjustmentOut` ต่อบรรทัดใน transaction เดียว และ flip header เป็น `completed` ฟอร์มฝั่ง frontend ถูกออกแบบใหม่ในวันเดียวกัน (`198d83c1`) และตอนนี้มี **Save**, **Commit** (พร้อม confirm dialog), **Void**, **Delete** และ **Print**; Save คงอยู่ที่เอกสาร Commit กลับไปหน้ารายการ (`128380f9`)

กฎ read-only ตามสถานะ: `isReadOnly = doc_status ∈ {completed, voided}` เอกสาร `draft` แสดง **Edit** (`isView && !isReadOnly`) และ **Delete**; ในโหมด Edit ยังแสดง **Void** ด้วย (`canVoid = isEdit && !isReadOnly`) เอกสาร `completed` ใน UI ดูได้ + พิมพ์ได้ + ดู stock movements ได้เท่านั้น — endpoint กลับรายการจริง `DELETE /{id}/void` ทำงานกับเอกสารที่ post แล้ว แต่หน้าจอที่ ship ไม่เคยเสนอปุ่มนี้ให้เอกสารเช่นนั้น (เสนอ Void เฉพาะบน draft ซึ่งพฤติกรรมเหมือน delete พร้อมเหตุผล) การลบเอกสารที่ completed ตอบ `Cannot delete a completed Stock In — inventory has already been adjusted` (400)

## 2. บริบททางธุรกิจ

การดำเนินงานโรงแรมต้องการช่องทางแก้ไขสต๊อกที่เปลี่ยนแปลงนอกเหนือจากการซื้อหรือการเบิก: ของเสียหายที่พบในคลัง ของหมดอายุที่ถูก write-off ของที่พบคืนระหว่างตรวจชั้นวาง หรือบรรทัดส่วนเกิน/ขาดที่เหลือจาก [physical-count](/th/inventory/physical-count) ที่เสร็จสิ้นแล้ว มีผู้ผลิตอีกสองรายเขียนลงตารางเดียวกัน:

- `PhysicalCountService.submit()` สร้างแถว `tb_stock_in` (ส่วนเกิน) / `tb_stock_out` (ขาด) โดยตรงที่ `doc_status = completed` โดยไม่มี `adjustment_type_id` — **และไม่ post ไป ledger** (ยืนยัน 2026-09-22: ไม่มีการอ้างอิง `inventoryTransactionService` ที่ใดใน `physical-count/*.ts`) แถวเหล่านี้เป็นบันทึก audit ของผลต่าง ไม่ใช่ stock movement
- `POST /wastage-reporting` ([wastage-reporting](/th/inventory/inventory-adjustment/wastage-reporting)) สร้าง `tb_stock_out` หนึ่งฉบับต่อ location สำหรับ lot ใกล้หมดอายุที่เลือก และ commit ในการเรียกเดียวกัน — แถวเหล่านี้**ถูก** post (`executeAdjustmentOut` พร้อม `target_lot_nos`)

เนื่องจาก master ของ reason code (`tb_adjustment_type`) มีเพียง `code`, `name`, `type` (ทิศทาง), `description`, `is_active` — ไม่มีฟิลด์บัญชี GL ไม่มี flag บังคับแนบเอกสาร ไม่มี flag ตรวจสอบคุณภาพ — จึงไม่มีการเชื่อมต่อบัญชีในโมดูลนี้: แกน GL ของเดือน 2026-09 (`tb_gl_jv*`, manual journal voucher) ไม่มี hook จากโค้ด stock-in / stock-out ทุก adjustment เป็นการเคลื่อนไหวปริมาณ/มูลค่าสต๊อกล้วน ๆ

## 3. แนวคิดสำคัญ

- **เอกสารสองสายคู่ขนาน จัดประเภทร่วมกันหนึ่งตัว** `tb_stock_in` (ขาเข้า) และ `tb_stock_out` (ขาออก) เป็น Prisma model อิสระต่อกันที่มีโครงสร้าง header/detail เหมือนกัน `tb_adjustment_type.type` (`enum_adjustment_type`: `stock_in` | `stock_out` | `eop_in` | `eop_out`) กำหนดว่า reason ตัวไหนใช้กับสายเอกสารไหน — `eop_in`/`eop_out` สงวนไว้สำหรับ engine ปิดงวด และไม่ปรากฏใน reason picker ตัว picker กรองตามทิศทางฝั่ง client เท่านั้น; backend enrich header จากแถว `tb_adjustment_type` ที่อ้างอิง แต่ไม่ตรวจซ้ำว่า `type` ตรงกับทิศทางของเอกสาร
- **Reason ("Adjustment Type")** ฟิลด์ **Reason** ใน UI คือ foreign key `adjustment_type_id` ที่บันทึกใน [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) แถว reason ถูกดูแลบน `/config/adjustment-type` ซึ่งอยู่นอกขอบเขตของโมดูลนี้
- **การกรอกต้นทุนต่างกันตามทิศทาง** สำหรับ **Stock-In** ฟิลด์ `cost_per_unit` ให้ผู้ใช้แก้ไขได้ในแต่ละบรรทัด (เติมค่าเริ่มต้นจาก `useProductCostByLocationQty` เป็นค่าแนะนำ); ค่าที่ผู้ใช้ commit จะกลายเป็นต้นทุนของ cost layer ใหม่ สำหรับ **Stock-Out** backend ไม่เคยเขียน `cost_per_unit`/`total_cost` ลง `tb_stock_out_detail` (ทั้งสองค่าคงเป็น `0`); ต้นทุนจริงถูกเลือกตอน commit โดย ledger (FIFO: layer เก่าสุดก่อน; Average: ค่าเฉลี่ยปัจจุบันของ BU)
- **วันหมดอายุบนบรรทัด stock-in (API เท่านั้น)** `tb_stock_in_detail.expired_at` (migration `20260731120000_add_inflow_price_expiry`) ถูกรับและ persist โดย `POST /stock-ins`, `PATCH /save` และ endpoint ของ detail (DTO ของ stock-in + swagger ตั้งแต่ 2026-08-03) แต่ฟอร์มที่ ship **ไม่มีช่องกรอกวันหมดอายุ** (`grep expired routes/inventory-management/inventory-adjustment/` → ไม่พบ) และไม่มีอะไรในโมดูลนี้อ่านมัน; `expired_at` ของบรรทัด GRN คือสิ่งที่ป้อน [wastage-reporting](/th/inventory/inventory-adjustment/wastage-reporting)
- **ไม่มี UI สำหรับเลือก lot** ทั้งสองหน้าจอไม่มีฟิลด์เลขที่ lot หรือตัวเลือก lot ใด ๆ identity ของ lot ถูกสร้างโดย ledger (`buildLotNo` → `{location_code}{YYMM}{seq4}`) รูปแบบเดียวกับที่ใช้ในทุกโมดูลที่เขียน inventory-transaction
- **ขอบเขตตำแหน่ง** ตัวเลือกตำแหน่ง (`LookupUserLocation`) กรองฝั่ง client ให้เหลือเฉพาะประเภทตำแหน่ง Inventory / Consignment; backend ต้องการเพียง `location_id` (`STOCK_IN_LOCATION_REQUIRED`) และไม่ตรวจซ้ำประเภท
- **วันที่ต้องอยู่ในงวด — ตอนนี้บังคับฝั่ง server แล้ว** ฟอร์มตรวจสอบวันที่เทียบกับช่วงงวดปัจจุบัน (Zod, `ia-form-schema.ts`) และตั้งแต่ 2026-08-31 backend ตรวจซ้ำตอน create **และ** commit: `si_date` ของ stock-in ต้องอยู่ในงวด open/locked (`STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD`, 422), `so_date` ของ stock-out ต้องอยู่ในงวด**ปัจจุบัน** (`STOCK_OUT_DATE_NOT_CURRENT_PERIOD`, 422; `STOCK_OUT_NO_OPEN_PERIOD` ถ้าไม่มีงวดเปิดเลย) `si_no` / `so_no` ออกเลขจากวันที่เอกสาร ไม่ใช่วันที่คลิก (`5d878a6c8`)
- **สต๊อกไม่พอถูกตรวจก่อน post** `StockOutService.commit` รวมจำนวนที่ขอต่อสินค้าและเทียบกับ `getOnHandQty`; ถ้าขาดจะคืน `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`, 400) และไม่มีอะไรถูกเขียน
- **Optimistic concurrency** `doc_version` เป็นค่าบังคับตอน save และ commit (ตระกูล `COMMON_DOC_VERSION_REQUIRED`); frontend อ่านค่าที่เพิ่มขึ้นใหม่หลัง save เพื่อให้ commit ที่ตามมาไม่ race

## 4. บทบาทและ Persona

โค้ดไม่ได้แยก Store Keeper ออกจาก Inventory Controller สำหรับโมดูลนี้: nav entry, หน้าจอสร้าง/แก้ไข และหน้ารายการทั้งหมด gate ด้วยสิทธิ์ทั่วไปตัวเดียว `inventory_management.view` (`constant/module-list.ts`) และไม่มี workflow stage, approval queue หรือการกำหนด `enum_stage_role` ใน `stock-in.service.ts` / `stock-out.service.ts` (gateway มี guard key ละเอียดกว่า — `stockIn.create / update / commit / delete / print / getStockMovements` — แต่ key `inventory_management.stock_in.*` / `.stock_out.*` ใน catalog ของ frontend gate nav entry สองรายการของ Store Operations ไม่ใช่หน้าจอนี้) wiki ยังคงหน้า persona สองหน้าไว้เพื่อความอ่านง่าย:

| Role | ขอบเขตตามจริง |
|------|----------------|
| Store Keeper / ผู้กรอกเอกสาร | เปิด **Add Stock-In** / **Add Stock-Out** เลือก reason + ตำแหน่ง กรอกบรรทัด **Save** เป็น draft แล้ว **Commit** เมื่อพร้อม |
| Inventory Controller | หน้าจอเดียวกัน: review draft (Edit / Delete / Void), commit มัน, อ่านเอกสารที่ completed, **stock movements** ของมัน และผลพิมพ์; void เอกสารที่ post แล้วผ่าน API ถ้าต้องกลับรายการ |

Persona Finance แบบเจาะจง, workbench การตั้งค่าของ System Administrator และ scope อ่านของ Auditor เคยถูกบันทึกไว้สำหรับโมดูลนี้ — ไม่พบ route, component, permission key หรือ backend endpoint ที่ตรงกันเลยสำหรับทั้งสามบทบาท ดู [03 — User Flow — Finance](/th/inventory/inventory-adjustment/03-user-flow-finance) และ [03 — User Flow — Audit / Config](/th/inventory/inventory-adjustment/03-user-flow-audit-config)

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — ทุก commit เรียก `InventoryTransactionService` ตัวเดียวกัน (`executeAdjustmentIn` / `executeAdjustmentOut`) กับที่ GRN, SR, write-off ของ wastage และ period-end ใช้
- [inventory/period-end](/th/inventory/inventory/period-end) — stock-in / stock-out ที่เป็น `draft` และลงวันที่ในงวด block **Start Period Close**; การ์ด review SI/SO บน `/period-end/review` ลิงก์กลับมาที่นี่
- [physical-count](/th/inventory/physical-count) — เมื่อการนับเสร็จสิ้น สร้างแถว `tb_stock_in` / `tb_stock_out` โดยตรงที่สถานะ `completed` โดยไม่มี reason code และ**ไม่ post ไป ledger**
- [inventory-adjustment/wastage-reporting](/th/inventory/inventory-adjustment/wastage-reporting) — lot ใกล้หมดอายุ; endpoint write-off สร้างและ commit Stock Out หนึ่งฉบับต่อ location
- [costing](/th/inventory/costing) — การสร้าง FIFO layer บน Stock-In, การบริโภค FIFO / คำนวณค่าเฉลี่ยถ่วงน้ำหนักใหม่บน Stock-Out

**การกำหนดค่า master:**
- [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — master ของ reason code (`code`, `name`, ทิศทาง, `is_active`) ที่ `adjustment_type_id` อ้างอิง
- [master-data/location](/th/inventory/master-data/location) — ตำแหน่งที่ adjustment ขยับยอด

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/inventory-adjustment/` (freeze 2026-04-27; ออกแบบเป็น entity เดียว, GL-posting, อนุมัติตาม threshold — ถูกแทนที่โดยโค้ดแล้ว)
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/`
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-in/`, `.../stock-out/`, `.../inventory-transaction/`; gateway `apps/backend-gateway/src/application/stock-ins/`, `stock-outs/`, `inventory-adjustments/`
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/stock-in/`, `inventory/stock-out/` (create, update, **commit**, void, remove, by-id, list, print-viewer, `details/`), `inventory/inventory-adjustment/` (รายการรวม, by-id, print)
- E2E tests: ไม่มี Playwright spec; แคตตาล็อก manual `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (60 เคส, ตรวจซ้ำกับฟอร์มรอบ 2026-09 — Commit, Void ต้องอยู่ในโหมด Edit, Delete ในโหมด view), user story ที่ generate `docs/user-stories/730-inventory-adjustment.md` (32); `tests/031-adjustment-type.spec.ts` ครอบคลุมเฉพาะ master ของ reason code

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/inventory-adjustment/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
- [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) — การตรวจสอบ การคำนวณ และการ posting
- [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) — วงจรชีวิตเอกสาร พร้อมสารบัญ persona
  - [Store Keeper](/th/inventory/inventory-adjustment/03-user-flow-store-keeper)
  - [Inventory Controller](/th/inventory/inventory-adjustment/03-user-flow-inventory-controller)
  - [Finance](/th/inventory/inventory-adjustment/03-user-flow-finance)
  - [Audit / Config](/th/inventory/inventory-adjustment/03-user-flow-audit-config)
- [04 — Test Scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) — ขอบเขต persona, scenario ข้าม persona, การ map E2E
  - [Store Keeper](/th/inventory/inventory-adjustment/04-test-scenarios-store-keeper)
  - [Inventory Controller](/th/inventory/inventory-adjustment/04-test-scenarios-inventory-controller)
  - [Finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance)
  - [Audit / Config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)
- [Wastage Reporting](/th/inventory/inventory-adjustment/wastage-reporting) — รายการ lot ใกล้หมดอายุภายใต้ Store Operations และ API write-off ที่สร้าง Stock Out ที่ commit แล้วหนึ่งฉบับต่อ location
