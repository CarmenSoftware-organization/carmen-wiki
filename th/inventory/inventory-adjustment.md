---
title: การปรับสต๊อก (Inventory Adjustment)
description: การแก้ไข stock-in / stock-out ด้วยมือ นอกเหนือจากการจัดซื้อและการเบิกใช้ — write-off, write-on และ count-variance rollup
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การแก้ไขสต๊อกด้วยมือ นอกเหนือจากการจัดซื้อ (GRN) และการเบิกใช้ (Store Requisition) — เอกสารสองสายที่เป็นอิสระต่อกัน คือ Stock-In (`tb_stock_in`) และ Stock-Out (`tb_stock_out`) จัดประเภทโดย master ของ reason code ร่วมกัน (`tb_adjustment_type`) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ใช้ใดก็ตามที่มีสิทธิ์ `inventory_management.view` (ไม่มี role อนุมัติแยกต่างหากในโค้ด) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_stock_in`, `tb_stock_in_detail`, `tb_stock_out`, `tb_stock_out_detail`, `tb_adjustment_type` &nbsp;·&nbsp; **หน้าย่อย:** 14

![การปรับสต๊อก (Inventory Adjustment) screen](/screenshots/inventory-adjustment/index.png)

## 1. ภาพรวม

**Inventory Adjustment** ครอบคลุมสองหน้าจอภายใต้ `/inventory-management/inventory-adjustment`: **Stock-In** (การแก้ไขเพิ่ม — ของพบใหม่ ส่วนเกินจากการนับ) และ **Stock-Out** (การแก้ไขลด — ของเสียหาย หมดอายุ ขาดจากการนับ) ทั้งสองเป็นเอกสารอิสระต่อกัน คือ `tb_stock_in` และ `tb_stock_out` ไม่ใช่ variant ของ entity `tb_inventory_adjustment` ร่วมกันแต่อย่างใด ทั้งคู่มีโครงสร้าง header เหมือนกัน — เลขที่เอกสาร (`si_no` / `so_no`), วันที่, เหตุผล (`adjustment_type_id`, แสดงผลต่อผู้ใช้เป็นฟิลด์ **Reason**), ตำแหน่ง, คำอธิบาย และบรรทัดสินค้าหนึ่งรายการขึ้นไปพร้อม `qty`, `cost_per_unit`, `total_cost` — และทั้งคู่เชื่อมกับ ledger ของ [inventory](/th/inventory/inventory) ผ่าน `inventory_transaction_id` ที่ nullable บนแต่ละบรรทัด

**ตัวเอกสาร *คือ* เหตุการณ์ posting เอง** ต่างจาก GRN หรือ Store Requisition ตรงที่ไม่มีขั้นตอน submit-แล้ว-approve แยกต่างหาก: `StockInService.create()` / `StockOutService.create()` เขียน header ที่ `doc_status = completed` และเรียก ledger ของ [inventory](/th/inventory/inventory) (`executeAdjustmentIn` / `executeAdjustmentOut`) ใน database transaction เดียวกัน โดยไม่มีเงื่อนไข — เกิดขึ้นไม่ว่าผู้ใช้จะกดปุ่มไหนก็ตาม ปุ่ม **Save** ของฟอร์มตั้งค่า `doc_status: "draft"` และ **Submit** ตั้งค่า `doc_status: "completed"` ก่อนเรียก mutation สร้างเอกสารเดียวกัน แต่ backend ไม่สนใจค่าที่ client ส่งมาและเขียน `completed` เสมอ ในทางปฏิบัติจึงไม่มีสถานะ draft ที่เข้าถึงได้จริงสำหรับ adjustment ที่สร้างใหม่ — ทุก stock-in/stock-out ที่มีอยู่ในระบบถูก post เข้า ledger ตั้งแต่วินาทีที่ถูกสร้างขึ้น

ผลที่ตามมาข้อหนึ่งส่งผลต่อทั้งหน้าจอ: `isReadOnly` บนหน้ารายละเอียดคือ `doc_status === 'voided' || doc_status === 'completed'` และเนื่องจากทุกเอกสารที่ persist แล้วเป็น `completed` เสมอ `isReadOnly` จึงเป็น true เสมอ ปุ่ม **Edit** (`isView && !isReadOnly`) จึงไม่แสดงผลสำหรับเอกสารจริงเลย ทำให้โหมดแก้ไขของฟอร์มไม่ถูกเข้าถึง — และปุ่ม **Void** ซึ่งต้องอาศัย `isEdit` จึงเข้าไม่ถึงตามไปด้วย แม้ backend จะมี void endpoint ที่ใช้งานได้จริง (ดู [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) § 5) ปุ่ม **Delete** ในเมนูแถวของหน้ารายการยังคงแสดงผลโดยไม่มีเงื่อนไข แต่ backend จะปฏิเสธด้วยข้อความ `"Cannot delete a completed Stock In — inventory has already been adjusted"` สำหรับทุกแถวที่มีอยู่ เนื่องจาก `delete()` สำเร็จได้เฉพาะเมื่อ `doc_status = draft` เท่านั้น เมื่อสร้างแล้ว เอกสาร Stock-In หรือ Stock-Out จึงเป็น**อ่านอย่างเดียว**ผ่าน UI ปัจจุบัน (ดูได้และพิมพ์ได้เท่านั้น)

## 2. บริบททางธุรกิจ

การดำเนินงานโรงแรมต้องการช่องทางแก้ไขสต๊อกที่เปลี่ยนแปลงนอกเหนือจากการซื้อหรือการเบิก: ของเสียหายที่พบในคลัง ของหมดอายุที่ถูก write-off ของที่พบคืนระหว่างตรวจชั้นวาง หรือบรรทัดส่วนเกิน/ขาดที่เหลือจาก [physical-count](/th/inventory/physical-count) ที่เสร็จสิ้นแล้ว `PhysicalCountService.submit()` สร้างแถว `tb_stock_in` (ส่วนเกิน) / `tb_stock_out` (ขาด) โดยตรง — ที่ `doc_status = completed` โดยไม่ตั้งค่า `adjustment_type_id` เลย (แถวที่มาจากการนับไม่มี reason code) — เป็นบันทึก audit ของผลต่างจากการนับ ส่วนที่ว่าการเขียนนี้ขับเคลื่อน cost layer ของ ledger แบบเดียวกับ Stock-In/Stock-Out ที่สร้างด้วยมือหรือไม่นั้น ยังไม่ได้รับการยืนยันในรอบนี้ และควรตรวจสอบซ้ำในรอบ resync ของโมดูล physical-count เอง

เนื่องจาก master ของ reason code (`tb_adjustment_type`) มีเพียง `code`, `name`, `type` (ทิศทาง), `description`, `is_active` — ไม่มีฟิลด์บัญชี GL ไม่มี flag บังคับแนบเอกสาร ไม่มี flag ตรวจสอบคุณภาพ — จึงไม่มีการเชื่อมต่อบัญชีในโมดูลนี้: การค้นหาทั่วทั้งทั้ง frontend และ backend `carmen-turborepo-backend-v2` ไม่พบการอ้างอิงถึง `journal`, `ledger` หรือ engine การลงบัญชี GL ใด ๆ ใน code path ของ stock-in/stock-out เลย ทุก adjustment เป็นการเคลื่อนไหวปริมาณ/มูลค่าสต๊อกล้วน ๆ ไม่สร้าง journal entry

## 3. แนวคิดสำคัญ

- **เอกสารสองสายคู่ขนาน จัดประเภทร่วมกันหนึ่งตัว** `tb_stock_in` (ขาเข้า) และ `tb_stock_out` (ขาออก) เป็น Prisma model อิสระต่อกันที่มีโครงสร้าง header/detail เหมือนกัน `tb_adjustment_type.type` (`enum_adjustment_type`: `stock_in` | `stock_out` | `eop_in` | `eop_out`) กำหนดว่า reason ตัวไหนใช้กับสายเอกสารไหน — `eop_in`/`eop_out` สงวนไว้สำหรับ engine ปิดงวด และไม่ปรากฏใน reason picker ของ Stock-In/Stock-Out ตัว picker กรองตามทิศทางฝั่ง client เท่านั้น; การตรวจสอบ header ฝั่ง backend ยืนยันเพียงว่าแถว `tb_adjustment_type` ที่อ้างอิงมีอยู่จริง แต่**ไม่**ตรวจซ้ำว่า `type` ตรงกับทิศทางของเอกสาร — การเรียก API โดยตรงจึงอาจแนบ reason ประเภท `stock_out` เข้ากับเอกสาร `tb_stock_in` ได้
- **Reason ("Adjustment Type")** ฟิลด์ **Reason** ใน UI คือ foreign key `adjustment_type_id` ตัวเดียวกับที่บันทึกใน [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) — ไม่มีแนวคิด "reason code" แยกต่างหากซ้อนอยู่ด้านบน แถว reason ถูกดูแลบนหน้าจอ master data แยกต่างหาก (`/config/adjustment-type`) ซึ่งอยู่นอกขอบเขตของโมดูลนี้
- **การกรอกต้นทุนต่างกันตามทิศทาง** สำหรับ **Stock-In** ฟิลด์ `cost_per_unit` ให้ผู้ใช้แก้ไขได้ในแต่ละบรรทัด (เติมค่าเริ่มต้นจาก `useProductCostByLocationQty` ซึ่งเป็นต้นทุนเฉลี่ยปัจจุบันของตำแหน่งนั้น); ค่าที่ผู้ใช้ส่งจะถูก persist บน `tb_stock_in_detail` และส่งตรงไปยัง `executeAdjustmentIn` ของ ledger ซึ่งใช้สร้าง cost layer FIFO ใหม่ หรือคำนวณค่าเฉลี่ยถ่วงน้ำหนักทั้ง BU ใหม่ สำหรับ **Stock-Out** คอลัมน์ `cost_per_unit` ถูกซ่อนออกจาก grid รายการทั้งหมด — `create()` ของ backend ไม่เคยเขียน `cost_per_unit`/`total_cost` ลง `tb_stock_out_detail` เลย (ทั้งสองค่าคงเป็น `0` ตาม default ของ schema); ต้นทุนจริงถูกเลือกอัตโนมัติโดย ledger ในเวลาที่เขียน (FIFO: layer เก่าสุดก่อน; Average: ค่าเฉลี่ยปัจจุบันของ BU) โดยไม่ขึ้นกับค่าใดที่ client ส่งมา
- **ไม่มี UI สำหรับเลือก lot** ทั้งหน้าจอ Stock-In และ Stock-Out ไม่มีฟิลด์เลขที่ lot วันหมดอายุ หรือตัวเลือก lot ใด ๆ ในฟอร์มเลย identity ของ lot ถูกสร้างขึ้นเชิงกลไกโดย ledger — lot ขาเข้าเป็น `ADI-YYYY-MM-NNNN`, lot การบริโภคขาออกเป็น `ADO-YYYY-MM-NNNN` — รูปแบบที่สร้างโดยระบบเดียวกับที่ใช้ในทุกโมดูลที่เขียน inventory-transaction
- **ขอบเขตตำแหน่ง** ตัวเลือกตำแหน่ง (`LookupUserLocation`) กรองฝั่ง client ให้เหลือเฉพาะประเภทตำแหน่ง `INVENTORY_TYPE.INVENTORY` และ `INVENTORY_TYPE.CONSIGNMENT` การตรวจสอบ header ฝั่ง backend (`StockInLogic.validateAndEnrichHeader` / `StockOutLogic.validateAndEnrichHeader`) ยืนยันเพียงว่า `location_id` มีอยู่จริง — ไม่ตรวจซ้ำประเภทของตำแหน่ง — ข้อจำกัดนี้จึงบังคับใช้โดย UI ไม่ใช่ server
- **วันที่ต้องอยู่ในงวด** ฟิลด์วันที่ถูกตรวจสอบฝั่ง client (Zod) เทียบกับช่วง `start_at`/`end_at` ของงวดปัจจุบันจาก `useProfile()` ไม่พบการตรวจสอบเทียบเท่าใน `StockInService.create()` / `update()` ฝั่ง backend ในรอบตรวจสอบนี้
- **Optimistic concurrency** ทั้ง `doc_version` ของ header และของแต่ละบรรทัดถูกตรวจสอบตอน update — clause `where` ของ Prisma รวม `doc_version` ไว้ด้วย จึงทำให้การเขียนที่ล้าสมัย fail แทนที่จะเขียนทับการแก้ไขที่เกิดขึ้นพร้อมกันโดยเงียบ ๆ

## 4. บทบาทและ Persona

โค้ดไม่ได้แยก Store Keeper ออกจาก Inventory Controller สำหรับโมดูลนี้: nav entry, หน้าจอสร้าง/แก้ไข และหน้ารายการทั้งหมด gate ด้วยสิทธิ์ทั่วไปตัวเดียว `inventory_management.view` และไม่มี workflow stage, approval queue หรือการกำหนด `enum_stage_role` ใด ๆ ใน `stock-in.service.ts` / `stock-out.service.ts` เลย wiki ยังคงหน้า persona สองหน้าไว้เพื่อความอ่านง่าย แต่ทั้งคู่บรรยายหน้าจอเดียวกันที่ไม่มีความแตกต่าง:

| Role | ขอบเขตตามจริง |
|------|----------------|
| Store Keeper / ผู้กรอกเอกสาร | เปิด **Add Stock-In** / **Add Stock-Out** เลือก reason + ตำแหน่ง กรอกบรรทัด กด Save หรือ Submit — ปุ่มไหนก็ post เข้า ledger ทันที |
| Inventory Controller | หน้าจอสร้างเดียวกัน บวกหน้าจอย้อนหลังแบบอ่านอย่างเดียว (รายการ, รายละเอียด, พิมพ์) — เนื่องจาก Edit/Void เข้าไม่ถึงใน UI สำหรับเอกสารที่ persist แล้ว (§ 1) การ "review" ประจำวันในที่นี้จึงหมายถึงการอ่านหน้ารายการ/ผลพิมพ์ ไม่ใช่การอนุมัติอะไรใน app |

Persona Finance แบบเจาะจง, workbench การตั้งค่าของ System Administrator และ scope อ่านของ Auditor เคยถูกบันทึกไว้สำหรับโมดูลนี้ — ไม่พบ route, component, permission key หรือ backend endpoint ที่ตรงกันเลยสำหรับทั้งสามบทบาท (`enum_stage_role` = `{create, approve, purchase, issue, view_only}` ไม่มีสมาชิก `finance` และไม่มีการเรียก workflow orchestrator ใด ๆ ใน service code ของโมดูลนี้) ดู [03 — User Flow — Finance](/th/inventory/inventory-adjustment/03-user-flow-finance) และ [03 — User Flow — Audit / Config](/th/inventory/inventory-adjustment/03-user-flow-audit-config) สำหรับประกาศแก้ไข

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — ทุกการเขียน stock-in/stock-out เรียก `InventoryTransactionService` ตัวเดียวกับที่ GRN, SR และ period-end ใช้
- [physical-count](/th/inventory/physical-count) — เมื่อการนับเสร็จสิ้น สร้างแถว `tb_stock_in` (ส่วนเกิน) / `tb_stock_out` (ขาด) โดยตรงที่สถานะ `completed` โดยไม่มี reason code — ตรวจสอบข้อกล่าวอ้างเรื่องการเชื่อม ledger ซ้ำในรอบของโมดูลนั้นเอง
- [costing](/th/inventory/costing) — การสร้าง FIFO layer บน Stock-In, การบริโภค FIFO / คำนวณค่าเฉลี่ยถ่วงน้ำหนักใหม่บน Stock-Out

**การกำหนดค่า master:**
- [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — master ของ reason code (`code`, `name`, ทิศทาง, `is_active`) ที่ `adjustment_type_id` อ้างอิง
- [master-data/location](/th/inventory/master-data/location) — ตำแหน่งที่ adjustment ขยับยอด

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/inventory-adjustment/`
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/`
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-in/`, `.../stock-out/`, `.../inventory-transaction/`
- API contracts: ไม่มี collection `../carmen-turborepo-backend-bruno/` สำหรับ `stock-in`/`stock-out`/`inventory-adjustment` — ตรวจสอบโดยตรงกับ backend controller แทน
- E2E tests: ไม่มี spec `inventory-adjustment` เฉพาะใน `../carmen-inventory-frontend-e2e/`; `031-adjustment-type.spec.ts` ครอบคลุมเฉพาะหน้าจอ master data ของ reason code

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
- [Wastage Reporting](/th/inventory/inventory-adjustment/wastage-reporting) — หน้าจอแยกที่ขับเคลื่อนด้วย mock data เท่านั้น ภายใต้ Store Operations; อ้างอิงไขว้ไว้ที่นี่ ไม่ใช่ variant ของ Stock-Out
