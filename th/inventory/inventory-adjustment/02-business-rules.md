---
title: การปรับสต๊อก (Inventory Adjustment) — กติกาทางธุรกิจ
description: กฎการตรวจสอบ การคำนวณ และการ posting สำหรับการปรับสต๊อก
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — กติกาทางธุรกิจ

> **At a Glance**
> **กลุ่มกฎ:** `ADJ_VAL_*` การตรวจสอบ &nbsp;·&nbsp; `ADJ_CALC_*` การคำนวณ &nbsp;·&nbsp; `ADJ_POST_*` การ posting
> **จำนวนกฎ:** 13 ข้อ ทั้งหมด trace ตรงไปยัง `ia-form-schema.ts`, `stock-in.service.ts` / `stock-out.service.ts` และ `inventory-transaction.service.ts`
> **กลุ่มผู้ใช้:** ผู้เขียน test + developer
> **ข้อค้นพบสำคัญที่สุด:** ไม่มีขั้นตอนอนุมัติเลย — `create()` เขียน `doc_status = completed` เสมอ และ post เข้า ledger ในทรานแซกชันเดียวกัน ไม่ว่าต้นทุน, reason หรือปุ่มไหนที่ผู้ใช้กด

## 1. ภาพรวม

หน้านี้รวบรวมกฎที่บังคับใช้จริงโดย **โมดูล inventory-adjustment** — เลเยอร์เอกสารสองตาราง (`tb_stock_in` / `tb_stock_out`) สำหรับการแก้ไขสต๊อกด้วยมือ หน้านี้เวอร์ชันก่อนหน้าบรรยายห่วงอนุมัติที่ gate ด้วย threshold (Store Keeper auto-approve → Inventory Controller → Finance), การลงบัญชี GL, กฎแบ่งแยกหน้าที่ (segregation of duties) และฟอร์มย่อยเลือก lot ไม่มีข้อไหนมีอยู่จริงในซอร์สปัจจุบัน: การค้นหาทั่ว repo `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` ไม่พบคำว่า `threshold` ที่ขอบเขตของโมดูลนี้เลย ไม่พบ `journal`/`ledger` เลย และไม่มี UI สำหรับป้อน lot ที่ไหนใน `ia-item-fields.tsx` / `ia-item-table.tsx` หน้านี้ถูกเขียนใหม่จาก Zod schema จริง (`ia-form-schema.ts`) และ backend service code

**ข้อเท็จจริงที่สำคัญที่สุดเรื่องเดียวของโมดูลนี้:** `StockInService.create()` และ `StockOutService.create()` สร้าง object literal เป็น `{ ...clientData, doc_status: enum_doc_status.completed }` — `doc_status: completed` ที่ระบุชัดเจนเป็น key สุดท้ายใน literal จึงชนะค่าที่ client ส่งมาเสมอ และการเขียน ledger (`executeAdjustmentIn`/`executeAdjustmentOut`) เกิดขึ้นใน `$transaction` block เดียวกัน ปุ่ม Save ของ frontend (ตั้ง `doc_status: "draft"`) และปุ่ม Submit (ตั้ง `doc_status: "completed"`) ต่างก็เรียก mutation `create()` เดียวกันในที่สุด **ปุ่มทั้งสองจึงให้ผลลัพธ์เดียวกัน: เอกสารที่ post แล้วและ immutable ทันที** ไม่มีสถานะ draft ที่เข้าถึงได้จริง ไม่มี approval queue และไม่มีความแตกต่างระหว่าง "การบันทึก draft" กับ "การ submit"

## 2. กฎการตรวจสอบ

Rule IDs ใช้รูปแบบ `ADJ_VAL_NNN` ทั้งหมดถูกบังคับใช้ฝั่ง client (Zod, ใน `ia-form-schema.ts`) หรือในเมธอด `create()`/`update()` ของ backend — ไม่มีขั้นตอนตรวจสอบ "submit" แยกจากการสร้าง เนื่องจากการสร้างและการ post คือเหตุการณ์เดียวกัน

| Rule ID | เงื่อนไข | บังคับใช้โดย | พฤติกรรม |
| ------- | -------- | ------------ | -------- |
| `ADJ_VAL_001` | `location_id` บังคับ (ไม่ว่าง) | Client (Zod `.min(1)`) และ server (`STOCK_IN_LOCATION_REQUIRED` / `STOCK_OUT_LOCATION_REQUIRED` ถ้าไม่มีตอน `create()`) | ปฏิเสธด้วย `"Location is required for stock in"` / `"...stock out"` |
| `ADJ_VAL_002` | `adjustment_type_id` บังคับ (ไม่เป็น null) | Client เท่านั้น (Zod `.refine((v) => !!v, ...)`) การตรวจสอบ header ของ backend (`validateAndEnrichHeader`) ตรวจเพียงว่าแถว `tb_adjustment_type` ที่อ้างอิงมีอยู่จริง — ไม่บังคับให้ต้องมีฟิลด์นี้ และไม่ตรวจว่า `type` ตรงกับทิศทางของเอกสาร | Client ปฏิเสธด้วยข้อความ "required" ก่อนจะ submit ได้; การเรียก API โดยตรงที่มี reason ผิดทิศทางหรือไม่ระบุเลยไม่ถูกตรวจซ้ำฝั่ง server เกินกว่าการตรวจว่ามีอยู่จริง |
| `ADJ_VAL_003` | `date` บังคับและต้องอยู่ในช่วง `start_at`–`end_at` ของงวดปัจจุบัน | **Client เท่านั้น** (Zod `.refine`, ใช้ `useProfile().currentPeriod`) ไม่พบการตรวจสอบเทียบเท่าใน `StockInService.create()`/`update()` หรือ `StockOutService.create()`/`update()` | Client ปฏิเสธด้วยข้อความวันที่นอกงวด; การเรียก API โดยตรงด้วยวันที่นอกงวดไม่พบว่าถูกปฏิเสธฝั่ง server |
| `ADJ_VAL_004` | ต้องมีอย่างน้อยหนึ่งบรรทัด (`items.min(1)`) | Client (Zod) และ server (`STOCK_IN_DETAIL_ITEMS_REQUIRED` / `STOCK_OUT_DETAIL_ITEMS_REQUIRED` ถ้า `stock_in_detail.add` / `stock_out_detail.add` ว่างตอนสร้าง) | ปฏิเสธด้วย `"Stock in detail items are required"` / `"...out..."` |
| `ADJ_VAL_005` | `product_id` ของแต่ละบรรทัดบังคับและต้องมีแถว `tb_product` จริง | Client (Zod `.min(1)`) และ server (`validateAndEnrichDetailItems` — รวบรวมทุก id ที่ไม่เจอและปฏิเสธด้วย `"Product not found: <ids>"`) | ปฏิเสธทั้งเอกสารพร้อม list product id ที่ไม่เจอทั้งหมด |
| `ADJ_VAL_006` | `qty` ของแต่ละบรรทัดต้อง `>= 1` (ไม่ใช่แค่ `> 0`) | Client เท่านั้น (Zod `.min(1, ...)`) | ปริมาณเศษส่วนต่ำกว่า 1 (เช่น `0.5`) ถูกปฏิเสธโดยฟอร์ม แม้คอลัมน์จะเป็น `Decimal(20,5)` ที่เก็บได้ |
| `ADJ_VAL_007` | `cost_per_unit` ของแต่ละบรรทัดต้อง `>= 0` | Client เท่านั้น (Zod `.min(0, ...)`) มีความหมายเฉพาะ Stock-In — grid ของ Stock-Out ซ่อนคอลัมน์นี้และ backend ไม่เคย persist สำหรับบรรทัด stock-out (ดู [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) § 2.5) | ปฏิเสธด้วยข้อความ non-negative-cost บน Stock-In |
| `ADJ_VAL_008` | `description` (header และบรรทัด) จำกัด 256 ตัวอักษร; **ไม่บังคับ** — ไม่มี `.min()` บนฟิลด์ใดเลย | Client เท่านั้น (Zod `.max(256, ...)`) | Adjustment ที่ไม่มีคำอธิบายเลยบันทึกและ post สำเร็จ — ขัดแย้งกับข้อกล่าวอ้างก่อนหน้าที่ว่า reason narrative เป็นบังคับ |
| `ADJ_VAL_009` | ประเภทตำแหน่งถูกจำกัดเป็น Inventory / Consignment (`locationTypes={[INVENTORY_TYPE.INVENTORY, INVENTORY_TYPE.CONSIGNMENT]}` บน picker `LookupUserLocation`) | **Client เท่านั้น** `validateAndEnrichHeader` ทั้งใน `stock-in.logic.ts` และ `stock-out.logic.ts` ตรวจเพียงว่า location มีอยู่จริง — ไม่ตรวจ `location_type` | Picker จะไม่เสนอ location ประเภท Direct-cost แต่การเรียก API โดยตรงด้วย location ประเภทนี้ไม่พบว่าถูกปฏิเสธฝั่ง server |
| `ADJ_VAL_010` | สต๊อกไม่พอบน Stock-Out (สินค้าที่ใช้ Average costing): `balance < qty ที่ขอ` | Server ภายใน `InventoryTransactionService.createAverageConsumption()` — throw `Error("Insufficient stock. Requested: <qty>, Available: <balance>")` ซึ่งปรากฏเป็น HTTP 500 ที่ frontend's `handleMutationError` จัดการพิเศษให้แสดงข้อความดิบแทน error ทั่วไป | ทรานแซกชันสร้าง/void ทั้งหมด rollback; ไม่สร้างเอกสาร / การ void ไม่ดำเนินต่อ **ยังไม่ยืนยันสำหรับสินค้าที่ใช้ FIFO** ในรอบนี้ — การจัดการ balance ของ `createFifoConsumption()` ยังไม่ได้ตรวจสอบครบถ้วน ถือว่ายังไม่ยืนยันสำหรับ FIFO |
| `ADJ_VAL_011` | Optimistic concurrency ตอน update: `doc_version` ที่ client ส่งต้องตรงกับค่าที่เก็บปัจจุบัน | Server — clause `where` ของ Prisma `update()` รวม `doc_version` ไว้กับ `id`; ค่าที่ล้าสมัยจะไม่ match แถวใดเลย | เนื่องจาก `update()` (และ `createDetail`/`updateDetail`/`deleteDetail`) ต้องการ `doc_status === draft` ก่อนด้วย และไม่มีเอกสารใดถูกสร้างที่ `draft` เลย (§ 1) path นี้จึงเข้าไม่ถึงผ่าน UI ปกติสำหรับเอกสารจริงใด ๆ — ดู `ADJ_POST_003` ด้านล่าง |
| `ADJ_VAL_012` | เงื่อนไขก่อน void: เอกสารต้องไม่ถูก void แล้ว | Server (`STOCK_IN_ALREADY_VOIDED` / `STOCK_OUT_ALREADY_VOIDED`) การ void ยังตรวจซ้ำว่ามี on-hand พอสำหรับกลับรายการของแต่ละบรรทัดที่ location ของเอกสาร (loop ตรวจสอบผลรวม cost-layer ของ `voidStockIn` ที่ระบุชัดเจน; การกลับรายการของ `voidStockOut` ไม่มี check เทียบเท่าที่ระบุชัดเจนในโค้ดที่อ่านรอบนี้) | `"Cannot void: product <code> has insufficient on-hand qty (<X>) at this location to reverse <Y>"` สำหรับ void ของ stock-in; guard ของ void stock-out ยังไม่ได้ยืนยันแยกต่างหาก |
| `ADJ_VAL_013` | Reason-direction ต้องตรงกัน (`tb_adjustment_type.type` เทียบกับต้นเอกสาร) | **Client เท่านั้น** — reason picker กรอง `adjTypeData` ด้วย `at.type === (adjustmentType === "stock-in" ? ADJUSTMENT_TYPE.STOCK_IN : ADJUSTMENT_TYPE.STOCK_OUT)` ไม่พบการตรวจสอบฝั่ง server (ดู `ADJ_VAL_002`) | ไม่สามารถบังคับใช้นอกเหนือจาก picker UI |

## 3. กฎการคำนวณ

| Rule ID | สูตร |
| ------- | ---- |
| `ADJ_CALC_001` (ยอดบรรทัด) | `total_cost = qty × cost_per_unit` คำนวณฝั่ง client ทุกครั้งที่พิมพ์ใน `recalcTotal()` ของ `ia-item-table.tsx` สำหรับ Stock-In ค่านี้ถูกส่งและ persist บน `tb_stock_in_detail` สำหรับ Stock-Out ค่าที่คำนวณเทียบเท่าเป็นเพียงการแสดงผล — ไม่เคย persist (ดู [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) § 2.5) |
| `ADJ_CALC_002` (ข้อเสนอต้นทุน Stock-In) | `cost_per_unit` ของบรรทัดเติมเริ่มต้นผ่าน `useProductCostByLocationQty(buCode, productId, locationId, qty)` ซึ่งคืนต้นทุนเฉลี่ยปัจจุบันของสินค้าที่ location นั้น — เป็นเพียงข้อเสนอเริ่มต้น; ฟิลด์ยังแก้ไขได้และค่าที่ผู้ใช้ส่งคือค่าที่ ledger ใช้จริง |
| `ADJ_CALC_003` (Preview ต้นทุน Stock-Out) | ยอดรวม (แสดงผลเท่านั้น ไม่ persist) ของบรรทัดเติมเริ่มต้นผ่าน `useProductLastReceiving(buCode, productId)` — ต้นทุนการรับล่าสุดของสินค้า — เป็นข้อมูลอ้างอิงของผู้ใช้ล้วน ๆ; ไม่มีบทบาทในต้นทุนที่ post จริง |
| `ADJ_CALC_004` (ต้นทุนเฉลี่ยใหม่ สินค้าที่ใช้ Average costing) | ตอน post Stock-In: `new_average = (existingInQty × existingInCost + newQty × newTotalCost) / (existingInQty + newQty)` คำนวณโดย helper ที่แชร์ `calculateNewAverageCost()` ใน `inventory-cost.formula.ts` และเขียนลง `average_cost_per_unit` ของแถว cost-layer ใหม่ นี่คือ logic ของ ledger ทั่วไปที่แชร์กับ GRN/SR ไม่เฉพาะเจาะจงกับโมดูลนี้ |
| `ADJ_CALC_005` (การบริโภคแบบ FIFO, Stock-Out) | `createFifoConsumption()` บริโภคจาก `getAvailableFifoLots()` ตามลำดับ `lot_seq_no` จากน้อยไปมากจนกว่าปริมาณที่ขอจะครบ เขียนแถว cost-layer ขาออกหนึ่งแถวต่อ lot ที่บริโภค |
| `ADJ_CALC_006` (การบริโภคแบบ Average, Stock-Out) | `createAverageConsumption()` คิดปริมาณขาออกทั้งหมดที่ต้นทุนเฉลี่ยปัจจุบันของ BU หลังผ่านการตรวจสอบ balance ใน `ADJ_VAL_010` |
| `ADJ_CALC_007` (การปัดเศษ) | ค่าเงินปัดเศษเป็น 2 ตำแหน่งทศนิยม (`Math.round(x * 100) / 100`) ทุกครั้งที่เขียน cost layer; คอลัมน์ปริมาณเก็บ 5 ตำแหน่งทศนิยม (`Decimal(20,5)`) |

## 4. การกำหนดสิทธิ์

ไม่พบการกำหนดสิทธิ์ตาม role หรือ threshold ที่ไหนในโมดูลนี้เลย nav entry, หน้ารายการ และหน้าจอสร้าง/แก้ไขทั้งหมด gate ด้วยสิทธิ์ทั่วไปตัวเดียว `inventory_management.view` (`constant/module-list.ts`) แคตตาล็อกยังนิยาม permission key รูปแบบ CRUD `inventory_management.stock_in.*` / `inventory_management.stock_out.*` (`constant/permissions.ts`) แต่ถูก wire ไว้ให้ gate nav entry ของ Store Operations สองตัวที่**ต่างกัน** — Stock Replenishment (`.stock_in.view`) และ Wastage Reporting (`.stock_out.view`) — ไม่ใช่หน้าจอของโมดูลนี้เอง ไม่พบการเรียก `hasPermission` ที่อ้างอิงถึง permission เหล่านี้ที่ไหนใต้ `routes/inventory-management/inventory-adjustment/` เลย ไม่มีการกำหนด `enum_stage_role`, ไม่มีการเรียก workflow orchestrator และไม่มีการจำกัด scope ตำแหน่งต่อผู้ใช้ที่มากกว่าที่ component `LookupUserLocation` ทั่วไปใช้กับทุกโมดูลอยู่แล้ว หน้านี้เวอร์ชันก่อนหน้าบรรยายห่วงการกำหนดสิทธิ์ Store-Keeper/Inventory-Controller/Finance/Auditor/System-Administrator พร้อมเกณฑ์เงิน (threshold) และกฎแบ่งแยกหน้าที่ — ไม่มีข้อไหนมี route, permission key หรือ backend guard ที่ตรงกันเลย ดู [03 — User Flow — Finance](/th/inventory/inventory-adjustment/03-user-flow-finance) และ [03 — User Flow — Audit / Config](/th/inventory/inventory-adjustment/03-user-flow-audit-config) สำหรับประกาศแก้ไข

## 5. กฎการ Posting

Rule IDs ใช้รูปแบบ `ADJ_POST_NNN`

| Rule ID | เหตุการณ์ | ผลกระทบ |
| ------- | -------- | ------- |
| `ADJ_POST_001` | `create()` (ทั้งปุ่ม Save และ Submit เรียก method นี้) | ทรานแซกชันเดียวแบบ atomic: (1) สร้างแถว header ที่ `doc_status = completed`, `doc_version = 0`, สร้าง `si_no`/`so_no` อัตโนมัติผ่าน running-code service; (2) สร้างแต่ละบรรทัด detail; (3) เรียก `executeAdjustmentIn` (Stock-In) / `executeAdjustmentOut` (Stock-Out) ต่อบรรทัด เขียน `tb_inventory_transaction` + `tb_inventory_transaction_detail` + แถว `tb_inventory_transaction_cost_layer` หนึ่งแถวขึ้นไป; (4) ประทับ `inventory_transaction_id` ของ detail ไม่มีขั้นตอน posting แยกต่างหาก — การสร้างคือการ post |
| `ADJ_POST_002` | `update()` | สำเร็จเฉพาะเมื่อ `doc_status === draft` ที่เก็บไว้ — สถานะที่ไม่มีเอกสารใดที่สร้างผ่าน `create()` ของโมดูลนี้เคยมี ฟิลด์ header และการ add/update/remove ของ detail เป็น optimistic-concurrency update ปกติในแบบอื่น (`doc_version` ตรวจสอบต่อแถว) ในทางปฏิบัติเข้าไม่ถึงสำหรับเอกสารที่สร้างผ่าน flow Add Stock-In/Add Stock-Out ปกติ |
| `ADJ_POST_003` | `delete()` | สำเร็จเฉพาะเมื่อ `doc_status === draft` — เข้าไม่ถึงเหมือน `update()` อย่างไรก็ตาม ปุ่ม **Delete** ในเมนูแถวของหน้ารายการแสดงผลโดยไม่มีเงื่อนไขสำหรับทุกแถว (`actionColumn` ถูกเรียกโดยไม่มี `deleteDenied`/`deletePermission`) ดังนั้นการกดปุ่มบนเอกสารจริงใด ๆ จะเปิด dialog ยืนยันแล้วล้มเหลวฝั่ง server ด้วยข้อความ `"Cannot delete a completed Stock In — inventory has already been adjusted"` (400) |
| `ADJ_POST_004` | `voidStockIn()` / `voidStockOut()` | Endpoint ของ backend ที่ใช้งานได้จริง: ตรวจสอบว่ายังไม่ถูก void (`ADJ_VAL_012`), ตรวจซ้ำว่ามี on-hand พอสำหรับกลับรายการแต่ละบรรทัด (ยืนยันเฉพาะ path stock-in) จากนั้นในทรานแซกชันเดียว (a) เขียนการเรียก `executeAdjustmentOut`/`executeAdjustmentIn` แบบกลับรายการต่อบรรทัด (ที่ต้นทุน *ปัจจุบัน* — void ของ stock-out อ่านต้นทุนจากแถว detail ของทรานแซกชันต้นฉบับผ่าน `txDetailMap`; void ของ stock-in ไม่ย้อนดูต้นทุนต้นฉบับ แต่กลับรายการที่ต้นทุนใดก็ตามที่ `executeAdjustmentOut` แก้ไขได้ ณ เวลา void) และ (b) ตั้งค่า `doc_status = voided` **พร้อมกับ** `deleted_at`/`deleted_by_id` บน header ต้นฉบับใน update เดียวกัน เนื่องจาก query ของ list/detail กรอง `deleted_at: null` เอกสารที่ void แล้วจึงหายไปจากทั้งคู่ ไม่ใช่แค่ถูก flag badge **เข้าไม่ถึงจาก UI ปัจจุบัน**: ปุ่ม Void แสดงผลเฉพาะเมื่อ `isEdit && !isReadOnly`, `isEdit` เข้าถึงได้เฉพาะผ่านการคลิก Edit, และ Edit แสดงผลเฉพาะเมื่อ `!isReadOnly` — แต่ `isReadOnly = doc_status === 'voided' \|\| doc_status === 'completed'` ซึ่งเป็น true สำหรับทุกเอกสารที่ persist แล้ว (§ 1) การ Void จึงต้องการการเรียก API โดยตรงในปัจจุบัน |
| `ADJ_POST_005` | Count-variance rollup ([physical-count](/th/inventory/physical-count)) | `PhysicalCountService.submit()` สร้าง `tb_stock_in` (บรรทัดส่วนเกิน) / `tb_stock_out` (บรรทัดขาด) โดยตรงที่ `doc_status = completed` โดย**ไม่ตั้งค่า `adjustment_type_id`** (แถวที่มาจากการนับไม่มี reason code) และข้อความ note บรรยายผลต่างและ costing method ที่ใช้สำหรับต้นทุนบรรทัด รอบนี้ยืนยันเพียงการสร้างแถว แต่ไม่ได้ตรวจสอบว่า `submit()` เรียก `executeAdjustmentIn`/`executeAdjustmentOut` แบบเดียวกับหน้าจอที่สร้างด้วยมือหรือไม่ — ตรวจสอบซ้ำในรอบ resync ของโมดูล `physical-count` เองก่อนถือว่าการเชื่อม ledger ได้รับการยืนยัน |

## 6. แหล่งอ้างอิง

- ส่วนคู่ขนาน: [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) — รูปทรง canonical ของ `tb_stock_in` / `tb_stock_out` / `tb_adjustment_type` และข้อค้นพบ "เป็น completed เสมอ" แบบเต็ม
- ส่วนคู่ขนาน: [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) — กฎเหล่านี้แสดงผลอย่างไรใน (หน้า persona ที่ไม่แตกต่างกัน)
- Frontend: `ia-form-schema.ts` (กฎ Zod ฝั่ง client ทั้งหมด), `ia-item-table.tsx` (`recalcTotal`, cost-probe hooks), `ia-doc-info.tsx` (การกรองประเภทตำแหน่ง)
- Backend: `apps/micro-business/src/inventory/stock-in/{stock-in.service.ts,stock-in.logic.ts}`, `.../stock-out/{stock-out.service.ts,stock-out.logic.ts}`, `.../inventory-transaction/inventory-transaction.service.ts`, `packages/error-catalog/src/catalog.ts` (error code `STOCK_IN_*`/`STOCK_OUT_*` 401xxx/402xxx)
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — ledger ร่วมและกฎ costing method ที่การ post ของโมดูลนี้ป้อนเข้าไป
- ที่เกี่ยวข้อง: [physical-count](/th/inventory/physical-count) — การสร้าง `ADJ_POST_005` count-rollup ที่ต้องตรวจสอบไขว้ในรอบของโมดูลนั้นเอง
