---
title: การสุ่มตรวจ (Spot Check) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูลการสุ่มตรวจ
published: true
date: 2026-07-29T04:45:21.000Z
tags: spot-check, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Data Model

> **At a Glance**
> **ตาราง:** `tb_spot_check` &nbsp;·&nbsp; `tb_spot_check_detail` &nbsp;·&nbsp; `tb_spot_check_comment` (มีแค่ schema — frontend ไม่ใช้) &nbsp;·&nbsp; `tb_spot_check_detail_comment` (ใช้งานจริง — dialog note/รูปต่อบรรทัด)
> **กลุ่มผู้ใช้:** นักพัฒนา / ผู้ตรวจสอบ (อ้างอิงเชิงพัฒนา)
> **FK สำคัญ:** header `→ tb_location`; detail `→ tb_product` และ `→ tb_unit` (`inventory_unit_id`) **ไม่มีการเชื่อมโยงใด ๆ เลย** — ไม่มี FK ไม่มี convention JSON แม้แต่ description string ที่แชร์กัน — จาก spot check ไปยัง [inventory-adjustment](/th/inventory/inventory-adjustment) หรือ ledger inventory ใด ๆ
> **รูปแบบการตรวจสอบ:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; ต้นไม้แบนสองระดับ (ไม่มี period parent — ad-hoc ไม่ผูกงวด ต่างจาก [physical-count](/th/inventory/physical-count)); spot-check ไม่เขียนลง inventory ledger และ `submit()` ของตัวเองก็ไม่สร้างเอกสารอื่นใดด้วย

> **Source of truth:** Prisma schema ฝั่ง backend บวก service method ที่อ่าน/เขียนมัน อ่านทั้งสองก่อนเสมอเมื่ออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (บรรทัด ~3964-4130)
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.logic.ts`
>
> ไฟล์ `generated/client/schema.prisma` ใน package เป็น copy ที่ auto-generate และไม่ถือเป็น authoritative

## 1. ภาพรวม

โมดูล Spot Check persist เป็น **ต้นไม้เอกสารแบนสองระดับ** ภายใต้ `tb_spot_check` → `tb_spot_check_detail`: header เดียวพกพา location, date window, `method` (random / high_value / manual), `size`, และ `doc_status`; row detail แต่ละ row เป็นสินค้าที่สุ่มได้หนึ่งตัวพร้อม `on_hand_qty` (snapshot สต๊อกสด ถ่ายสองครั้ง — ครั้งแรกตอนสร้าง ครั้งที่สองตอน review), `actual_qty` (counted), และ `diff_qty` (variance) **ไม่มี `tb_spot_check_period`** parent — spot check เป็น ad-hoc ไม่ผูกกับ header งวดบัญชี และคำว่า "current" ของ endpoint `current` หมายถึง "เอกสาร pending/in-progress ล่าสุดไม่ว่างวดใด" ไม่ใช่ entity ของงวด Comment ห้อยอยู่บนทั้งสองระดับ แต่มีเพียงตารางระดับ detail เท่านั้นที่ถูก wire เข้า frontend จริง — dialog "Add Notes" ต่อบรรทัดในหน้า entry อ่าน/เขียน `tb_spot_check_detail_comment` ผ่าน `GET`/`POST /spot-check-detail-comment/:detailId`; `tb_spot_check_comment` (ระดับ header) มี Prisma model และ controller ฝั่ง backend แต่ frontend ไม่มี hook ใดเรียกใช้เลย (`use-spot-check-comments.ts` มีแค่ `TODO` placeholder สำหรับ endpoint ระดับ header)

**โมดูลนี้ไม่เขียนลง inventory ledger และ — ต่างจาก [physical-count](/th/inventory/physical-count) — การ submit ขั้นสุดท้ายก็ไม่สร้างเอกสารอื่นใดด้วย** ผลของ `submit()` มีแค่ `doc_status = completed` บวก stamp `end_date` และ doc-comment ของตัวมันเองก็ระบุตรง ๆ ว่า: *"Does not create stock-in/stock-out — any follow-up adjustments are user-driven."* การค้นทั้ง repo ในฝั่ง frontend และ backend ของโมดูลนี้สำหรับ `stock_in`, `stock_out`, `executeAdjustment`, `journal`, และ `ledger` ไม่พบผลลัพธ์ใดเลย spot check เป็นบันทึกอิสระของการนับและผลต่างของมัน การแก้ไขผลต่างนั้นใน ledger เป็นการกระทำที่แยกและไม่เชื่อมโยงกันโดยสิ้นเชิง ที่ผู้ใช้ต้องทำผ่าน [inventory-adjustment](/th/inventory/inventory-adjustment) หากเลือกทำ

## 2. เอนทิตี

Prisma schema canonical กำหนดสี่ตาราง (ตรวจสอบกับ `prisma-shared-schema-tenant/prisma/schema.prisma` บรรทัด 3964-4130):

- **`tb_spot_check`** — header ของ spot-check พกพา `spot_check_no` (หมายเลขเอกสาร รูปแบบ `SC{YY}{MM}{seq}` ผ่าน running-code service ที่แชร์), `start_date` (default `now()`) / `end_date` (nullable — stamp เฉพาะโดย `submit()`), `location_id → tb_location` พร้อม snapshot `location_code` / `location_name`, `doc_status` บน `enum_spot_check_status` (`pending`, `in_progress`, `void`, `completed`; default `pending`), `method` บน `enum_spot_check_method` (`random` / `high_value` / `manual`; default `random`), `size` (จำนวนเป้าหมายตัวอย่าง default `10` — สำหรับ manual คือแค่จำนวนสินค้าที่ผู้ใช้เลือกจริง), `description`, `note`, `doc_version` (`Int @db.Integer`, default `0` — ตัวนับ optimistic-concurrency; ทุกคำเรียก `update`/`save`/`review`/`submit` ต้องส่งค่าปัจจุบันกลับมา ไม่งั้น `where` clause ที่ต้องตรงกันจะไม่ match — ดู [system-config/doc-version](/th/inventory/system-config/doc-version)) และ JSON blob `info` / `dimension` (ทั้งคู่ไม่ถูกใช้โดย logic ปัจจุบันใด ๆ — ไม่พบโค้ดที่อ่านค่ากลับ) Unique ภายใน `(spot_check_no, deleted_at)`
- **`tb_spot_check_comment`** — comment/attachment ระดับ header พกพา `message`, JSON array `attachments`, `enum_comment_type` (`user`/`system`) เป็น Prisma model จริงพร้อม controller ฝั่ง backend จริง (`spot-check-comments.controller.ts`) แต่ **ไม่มี hook หรือหน้าจอใดใน `carmen-inventory-frontend-react` อ่านหรือเขียนมันเลย** — ยืนยันจาก `TODO` comment ของ `use-spot-check-comments.ts` เองที่ list endpoint ระดับ header ว่ายังไม่ implement
- **`tb_spot_check_detail`** — บรรทัด spot-check ต่อสินค้า พกพา `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK ไปยัง `tb_unit`), `on_hand_qty` (`Decimal(20,5)`, default `0` — แต่ทุกแถวที่สร้างผ่าน `create()` จริง ถูก seed ด้วย **ปริมาณสต๊อกสดของ pool ณ เวลาสุ่มตัวอย่าง** ไม่ใช่ `0`; จากนั้น **ถูกเขียนทับใหม่อีกครั้ง** ด้วยยอดสดโดย `reviewItems()` เมื่อผู้ใช้กด Submit for Review), `actual_qty` (`Decimal(20,5)`, nullable, seed เป็น `0` ตอนสร้าง — ไม่ใช่ `null`), `diff_qty` (`actual_qty − on_hand_qty`, `Decimal(20,5)`, default `0`), `counted_at` / `counted_by_id` (stamp โดย **ทั้ง** `saveItems()` และ `reviewItems()` — ต่างจาก physical-count ที่มีเพียงการ Save ระหว่างนับเท่านั้นที่ stamp `counted_at`), และ `sequence_no` สำหรับลำดับ sheet (กำหนด `1..N` ตอนสร้าง) Unique ภายใน `(spot_check_id, product_id, dimension, deleted_at)`
- **`tb_spot_check_detail_comment`** — comment/attachment ระดับบรรทัด ตารางเดียวที่ live UI ใช้จริง: dialog notes ต่อบรรทัดในหน้า entry (`sc-entry-notes-dialog.tsx`) อ่าน/เขียนผ่าน `GET`/`POST /spot-check-detail-comment/:detailId` เก็บข้อความอิสระบวก photo attachment (pattern เดียวกับ dialog notes ของ [physical-count](/th/inventory/physical-count) เอง)

## 3. ความสัมพันธ์

```
tb_location
    │
    └─1──*──► tb_spot_check  (doc_status: pending → in_progress → completed หรือ → void;
                │              method: random | high_value | manual; size: N)
                │
                ├─1──*──► tb_spot_check_comment  (มีแค่ schema — ไม่มี hook frontend ใช้)
                │
                └─1──*──► tb_spot_check_detail
                            │   (on_hand_qty snapshot ตอนสร้าง ถูกเขียนทับใหม่อีกครั้งตอน review;
                            │    actual_qty / diff_qty; counted_at / counted_by_id stamp โดย
                            │    ทั้ง save และ review; ไม่มีคอลัมน์ lot_no)
                            │
                            └─1──*──► tb_spot_check_detail_comment  (ใช้งานจริง: photo/notes)

ที่ submit(), doc_status กลายเป็น completed และ end_date ถูก stamp นั่นคือผลทั้งหมด
ไม่มีตารางอื่นถูกอ่านหรือเขียนโดย action นี้:
    ▼
(ไม่มีอะไร) — ไม่มี tb_stock_in / tb_stock_out, ไม่มี tb_inventory_transaction, ไม่มีการเชื่อมโยงใด ๆ
การแก้ไข ledger ใด ๆ เป็นเอกสาร inventory-adjustment แยกที่ต้อง manual เริ่มเอง
```

หมายเหตุ:

- **ลำดับชั้นสองระดับ ไม่มี period parent** ต่างจากต้นไม้สามระดับ `tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail` ของ physical-count, spot check เป็นเอกสาร `(location, time-window)` เดี่ยวไม่มี entity จัดกลุ่มระดับ period เลย endpoint `GET /spot-check/current` คำว่า "current" หมายถึง "เอกสาร `pending`/`in_progress` ล่าสุด ไม่ว่างวดใด" — อ่านตรงจาก comment ของโค้ด `findCurrentByLocation()` เอง
- **`on_hand_qty` ถูกจับสองครั้ง ไม่ใช่ครั้งเดียว** `create()` seed มันจากยอดสต๊อกสดของ `SpotCheckLogic.getProductsByLocation()` ณ เวลาสุ่มตัวอย่าง; `saveItems()` (การ Save ระหว่างนับ) ไม่แตะมันอีกเลย — คำนวณแค่ `diff_qty` ใหม่เทียบกับค่าที่เก็บอยู่ปัจจุบัน; `reviewItems()` (Submit for Review) คำนวณมันใหม่รอบสองจาก `groupBy` สดบน `tb_inventory_transaction_detail` ไม่มี date cut-off ถ้ามีการเคลื่อนไหวสต๊อกอื่นที่ตำแหน่งนั้นระหว่างสร้างกับ review สอง snapshot อาจต่างกัน — ยอดตอน review คือสิ่งที่ผู้ใช้เห็นเปรียบเทียบจริง
- **`@relation` FK declaration ที่ระบุชัดเจนทั้งหมดใช้ `onDelete: NoAction`** (หรือ `Cascade` สำหรับ `inventory_unit_id`) — รักษาความหมาย soft-delete (`deleted_at`)

## 4. Enum

- **`enum_spot_check_status`** — วงจรชีวิตระดับเอกสาร สี่ค่า: `pending` (สร้างแล้ว; จับ snapshot `on_hand_qty`; ยังไม่ถูกแตะโดย save/review call ใด), `in_progress` (call Save ระหว่างนับถูกเรียกอย่างน้อยหนึ่งครั้ง), `void` (ยกเลิกผ่าน Reset — เข้าถึงได้จาก `pending` หรือ `in_progress` เท่านั้น), `completed` (submit แล้ว; terminal) **เอกสารสามารถไปถึง `completed` ตรงจาก `pending` ข้าม `in_progress` ไปเลยได้** — precondition เดียวของ `submit()` คือสถานะปัจจุบันต้องไม่ใช่ `completed` หรือ `void`; ผู้ใช้ที่นับทุกบรรทัดแล้วกดตรงไป Submit for Review แล้ว Submit โดยไม่เคย trigger การ Save ระหว่างนับเลย จะไม่เคยเปลี่ยน header เป็น `in_progress` เลย เพราะมีแค่ `saveItems()` เท่านั้นที่ทำ transition นั้น
- **`enum_spot_check_method`** — strategy การเลือกตัวอย่างบน `tb_spot_check.method` สามค่า: `random` (Fisher-Yates shuffle บน eligible product pool เก็บ `size` ตัวแรก), `high_value` (จัดอันดับ pool ตาม `cost_per_unit` สูงสุดที่พบใน cost-layer receipt ภายในงวดบัญชีที่เปิดอยู่หรือล็อกของ tenant ที่ตำแหน่งนั้น เลือกตัดสินค้าต่ำกว่า `minimum_cost` floor ออกได้ — ต้องมี `tb_period` อย่างน้อยหนึ่งที่ `status ∈ {open, locked}` มิเช่นนั้นการสร้างล้มเหลวด้วย `SPOT_CHECK_NO_ACTIVE_PERIOD`), `manual` (ผู้เรียกส่ง `product_id[]` ชัดเจน; สินค้าที่ไม่พบใน eligible pool ถูกทิ้งเงียบ ๆ และ set ที่เหลือว่างเปล่าหลังกรองล้มเหลวด้วย `"None of the selected products were found at this location"`)
- **ค่าสถานะระดับ frontend เท่านั้น ไม่มี schema รองรับ** `SpotCheckStatus` union ของ `types/spot-check.ts` ยัง list `"voided"` และ `"cancelled"` เพิ่มเติมนอกเหนือจากสี่ค่า Prisma จริง — ทั้งสองไม่มีอยู่บน `enum_spot_check_status` จึงไม่มีทางปรากฏใน `doc_status` ของเอกสารจริง น่าจะเป็น union member ที่ตายแล้ว carry มาจาก type ของโมดูลอื่น ไม่ใช่สัญญาณของชุดสถานะที่หลากหลายกว่า
- **`enum_transaction_type`** — ที่ระดับ inventory ledger (บรรทัด schema ~1103) `spot-check` ไม่ใช่ค่าบน enum นี้ และ — เนื่องจาก `submit()` ไม่เขียนอะไรลง ledger เลย — ไม่มี row `adjustment_in`/`adjustment_out` ถูกสร้างโดย action ของโมดูลนี้เองด้วย

## 5. ความแตกต่างจาก carmen/docs

ไม่มีโฟลเดอร์ source ใน `carmen/docs` สำหรับโมดูลนี้ มีเอกสารระดับวางแผนใน E2E repo แทน (`docs/persona-doc/System Process/tx-10-spot-check.md`, v1.0.0, วันที่ 2026-04-27) — ข้อกล่าวอ้างหลักของมัน ที่ว่าการ post variance ไปยัง inventory/lots/cost คือ "Pending — not yet implemented" ตรงกับโค้ดจริงเป๊ะ (ไม่มีกลไก posting ใด ๆ เลย ไม่ว่าจะ pending หรือไม่) ส่วนที่แตกต่างคือ status lifecycle: มันบรรยายหกสถานะ (`draft`, `pending`, `in-progress`, `on-hold`, `completed`, `cancelled`) เทียบกับสี่ค่าของ live schema (`pending`, `in_progress`, `void`, `completed`) — ดู [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) § 5.1 สำหรับการเปรียบเทียบเต็ม

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — เอนทิตีสี่ตัว (`tb_spot_check`, `tb_spot_check_comment`, `tb_spot_check_detail`, `tb_spot_check_detail_comment`); enum สองตัว (`enum_spot_check_status`, `enum_spot_check_method`)
- **Service layer:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (create/update/delete/reset/saveItems/reviewItems/getReview/submit/findCurrentByLocation/getProductsByLocation), `spot-check.logic.ts` (sampling strategies)
- **Secondary (ระดับวางแผน ยืนยันบางส่วน):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-10-spot-check.md`
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/` (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`); `types/spot-check.ts`; `hooks/use-spot-check.ts`, `hooks/use-spot-check-current.ts`, `hooks/use-spot-check-comments.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; มี manual test-case catalog ที่ `docs/test-cases/760-spot-check.md`
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ledger ที่ spot check เปรียบเทียบด้วยแต่ไม่เคยเขียนลงไป), [inventory-adjustment](/th/inventory/inventory-adjustment) (โมดูลที่ผู้ใช้ต้องไปแยกต่างหากเพื่อแก้ไขผลต่างที่ยืนยันแล้ว — ไม่มีลิงก์อัตโนมัติ), [physical-count](/th/inventory/physical-count) (คู่เทียบการนับเต็ม เป็น document tree ที่แยกต่างหากโดยสิ้นเชิง)
