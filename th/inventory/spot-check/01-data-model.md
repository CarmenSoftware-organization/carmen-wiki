---
title: การสุ่มตรวจ (Spot Check) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูลการสุ่มตรวจ
published: true
date: 2026-06-09T00:00:00.000Z
tags: spot-check, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Data Model

> **At a Glance**
> **ตาราง:** `tb_spot_check` &nbsp;·&nbsp; `tb_spot_check_detail` &nbsp;·&nbsp; `tb_spot_check_comment` &nbsp;·&nbsp; `tb_spot_check_detail_comment`
> **กลุ่มผู้ใช้:** นักพัฒนา / ผู้ตรวจสอบ (อ้างอิงเชิงพัฒนา)
> **FK สำคัญ:** header `→ tb_location`; detail `→ tb_product` และ `→ tb_unit` (`inventory_unit_id`) การเชื่อม variance rollup ไปยัง [inventory-adjustment](/th/inventory/inventory-adjustment) เป็น JSON เท่านั้น (`tb_stock_in.info.spotCheckId` / `tb_stock_out.info.spotCheckId`) — ไม่มี FK ใน Prisma
> **รูปแบบการตรวจสอบ:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; **ต้นไม้แบนสองระดับ** (ไม่มี period parent — ad-hoc, ไม่ผูกกับงวด ต่างจาก [physical-count](/th/inventory/physical-count)); spot-check เองไม่เขียนลง inventory ledger — การ post adjustment คือจุดเชื่อมต่อ

> **Source of truth:** Prisma schema ฝั่ง backend อ่านนี่ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใน package เป็น copy ที่ auto-generate และไม่ถือเป็น authoritative

## 1. ภาพรวม

โมดูล Spot Check เป็น **ชั้นเอกสาร** สำหรับการนับบางส่วนแบบเจาะจงของสินค้าหรือสถานที่จัดเก็บที่เลือก — ลูกพี่ลูกน้องน้ำหนักเบาของ [physical-count](/th/inventory/physical-count) ที่อธิบายใน [spot-check](/th/inventory/spot-check) § 1 ไม่เหมือนต้นไม้สามระดับ period / document / detail ของ physical-count, spot-check persist เป็น **ต้นไม้เอกสารแบนสองระดับ** ภายใต้ `tb_spot_check` → `tb_spot_check_detail`: header เดียวพกพา location, date window, `method` (random / high_value / manual), `size` (เป้าหมายตัวอย่าง), และ `doc_status`; row detail แต่ละ row เป็นบรรทัดสินค้าหนึ่งบรรทัดพร้อม `on_hand_qty` (book snapshot), `actual_qty` (counted), และ `diff_qty` (variance) **ไม่มี `tb_spot_check_period`** parent — spot check ดำเนินการ ad-hoc ไม่ผูกกับ header ของงวดบัญชี Comment / attachment ห้อยอยู่บนทั้งสองระดับ (`tb_spot_check_comment`, `tb_spot_check_detail_comment`)

โมดูลอยู่ **เหนือ [inventory-adjustment](/th/inventory/inventory-adjustment)** ในแบบเดียวกับที่ physical-count ทำ: เมื่อ spot check ถึง `completed` และบรรทัด variance ได้รับการยอมรับ ชั้น application จะ roll up variance เข้าสู่เอกสาร `tb_stock_in` (overage) และ/หรือ `tb_stock_out` (shortage) ด้วย reason code (โดยทั่วไปคือ `SPOT_CHECK_OVERAGE` / `SPOT_CHECK_SHORTAGE` หรือ alias เข้า reason `COUNT_OVERAGE` / `COUNT_SHORTAGE` ที่ใช้โดย physical-count — รอยืนยัน) การ post adjustment คือสิ่งที่เขียน row `tb_inventory_transaction` ที่ลงจอดบน ledger ของ [inventory](/th/inventory/inventory) ตารางของ spot-check เอง **ไม่** เขียนลง inventory ledger โดยตรง — เอกสาร adjustment คือจุดเชื่อมต่อ

> **TODO:** ยืนยันว่า spot-check ใช้ reason code `SPOT_CHECK_*` เฉพาะหรือใช้ reason `COUNT_*` ของ physical-count ซ้ำ ดึงรายละเอียด UI / interaction จาก `../carmen-inventory-frontend/` และพฤติกรรม end-to-end จาก `../carmen-inventory-frontend-e2e/` เมื่อ spec มี (ยังไม่มี spec `spot-check` — ตรวจสอบโดย `ls .../tests/ | grep -i 'spot\|check'`) ไม่มีโฟลเดอร์ source ใน carmen/docs สำหรับโมดูลนี้ — ดู [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) สำหรับ pattern infrastructure ที่แชร์

**Concurrency:** การแก้ไขเอกสารนี้ใช้ optimistic locking ผ่าน [system-config/doc-version](/th/inventory/system-config/doc-version) — client ต้องส่ง `doc_version` ปัจจุบันตอนบันทึก ไม่งั้นจะได้ `409 Conflict`

## 2. เอนทิตี

Prisma schema canonical กำหนดสี่ตาราง (ตรวจสอบกับ `prisma-shared-schema-tenant/prisma/schema.prisma` บรรทัด 3615–3765):

- **`tb_spot_check`** — header ของ spot-check พกพา `spot_check_no` (หมายเลขเอกสาร), `start_date` (default `now()`) / `end_date` (nullable), `location_id → tb_location` พร้อม snapshot `location_code` / `location_name`, `doc_status` บน `enum_spot_check_status` (`pending`, `in_progress`, `void`, `completed`), `method` บน `enum_spot_check_method` (`random` / `high_value` / `manual`), `size` (จำนวนเป้าหมายตัวอย่าง default 10), `description`, `note` และ JSON blob `info` / `dimension` Unique ภายใน `(spot_check_no, deleted_at)`
- **`tb_spot_check_comment`** — comment / attachment ระดับ header พกพา `message`, JSON array ของ `attachments` และ `enum_comment_type` (`user` / `system`)
- **`tb_spot_check_detail`** — บรรทัด spot-check ต่อสินค้า พกพา `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK ไปยัง `tb_unit`), `on_hand_qty` (snapshot ของ book ขณะตรวจ, `Decimal(20,5)`), `actual_qty` (ปริมาณ physical ที่ป้อน nullable จนกว่าจะนับ), `diff_qty` (`actual_qty - on_hand_qty`, `Decimal(20,5)`), `counted_at` / `counted_by_id` และ `sequence_no` สำหรับลำดับบน sheet Unique ภายใน `(spot_check_id, product_id, dimension, deleted_at)`
- **`tb_spot_check_detail_comment`** — comment / attachment ระดับบรรทัดบน row ของ spot-check detail

หมายเหตุ: spot-check เป็นโครงสร้าง **เรียบง่ายกว่า** physical-count — ไม่มี `tb_spot_check_period`, ไม่มีตัวนับความคืบหน้า (`product_counted` / `product_total`) บน header, ไม่มี flag `physical_count_type` (frozen vs live) Enum `method` (random / high_value / manual) แทนการ scoping ของ period-and-zone ด้วย strategy การเลือกตัวอย่าง

> **TODO:** ขยายแต่ละเอนทิตีเป็นตารางฟิลด์เต็มเมื่อมี source ใน carmen/docs (หรือ spec authoritative ทางเลือก) cross-reference กับ convention ของรูปทรงตารางใน [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) และ [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) เพื่อความสม่ำเสมอ

## 3. ความสัมพันธ์

```
tb_location
    │
    └─1──*──► tb_spot_check  (doc_status: pending → in_progress → completed / void;
                │              method: random | high_value | manual; size: N)
                │
                ├─1──*──► tb_spot_check_comment
                │
                └─1──*──► tb_spot_check_detail
                            │   (on_hand_qty, actual_qty, diff_qty;
                            │    counted_at / counted_by_id;
                            │    ไม่มีคอลัมน์ lot_no ที่ระดับนี้)
                            │
                            └─1──*──► tb_spot_check_detail_comment


เมื่อ spot-check เสร็จ variance rollup เขียนไปยัง [[inventory-adjustment]]:
    ▼
tb_stock_in  (reason_code = SPOT_CHECK_OVERAGE  หรือ COUNT_OVERAGE)   สำหรับ diff_qty > 0
tb_stock_out (reason_code = SPOT_CHECK_SHORTAGE หรือ COUNT_SHORTAGE)  สำหรับ diff_qty < 0
    │
    └── tb_stock_in_detail / tb_stock_out_detail.info = { spotCheckId: <tb_spot_check.id> }
    │
    └── เมื่อ adjustment post → tb_inventory_transaction พร้อม enum_transaction_type = adjustment_in / adjustment_out
```

หมายเหตุ:

- **ลำดับชั้นสองระดับ** (เทียบกับสามระดับของ physical-count) Spot check เป็น ad-hoc ไม่ผูกกับ period — ไม่มี `tb_spot_check_period` Header `tb_spot_check` หนึ่งเป็นคู่หนึ่ง (location, time-window); row detail เป็นหนึ่งต่อหนึ่งสินค้า
- **Variance rollup เป็นชั้น application ไม่ใช่ Prisma-FK** เช่นเดียวกับ physical-count ไม่มี FK ใน Prisma จาก `tb_stock_in.info.spotCheckId` ย้อนไปยัง `tb_spot_check.id` — การเชื่อมเป็น convention ใน JSON ห่วงโซ่ audit สร้างใหม่ฝั่งอ่าน
- **ทุก `@relation` FK declaration ที่ระบุชัดเจนใช้ `onDelete: NoAction` (หรือ `Cascade` สำหรับ `inventory_unit_id`)** — รักษาความหมาย soft-delete (`deleted_at`)

## 4. Enum

- **`enum_spot_check_status`** — วงจรชีวิตระดับเอกสาร สี่ค่า: `pending` (สร้างแล้ว sheet สร้างแล้ว counter ยังไม่เริ่ม), `in_progress` (counter เริ่มป้อนปริมาณแล้ว), `void` (ยกเลิกก่อน completion), `completed` (ทุกบรรทัดใน scope นับและเอกสาร submit แล้ว; eligible สำหรับ variance rollup) เทียบกับ enum สามสถานะของ physical-count — spot-check เพิ่ม `void` สำหรับ path การยกเลิกที่เบากว่า
- **`enum_spot_check_method`** — strategy การเลือกตัวอย่างบน `tb_spot_check.method` สามค่า: `random` (ระบบเลือก `size` รายการสุ่ม — หมุนการครอบคลุม), `high_value` (top-N ตามมูลค่าหรือ velocity — risk-based), `manual` (Inventory Controller เลือกรายการเอง — event-driven เช่น หลังมีต้องสงสัยความไม่ตรงหรือเหตุการณ์)
- **`enum_transaction_type`** — ที่ระดับ inventory ledger (บรรทัด schema ~1103) `spot-check` **ไม่ใช่** ค่าตรงบน enum นี้ — variance post เป็น `adjustment_in` / `adjustment_out` ผ่านเอกสาร adjustment ไม่ใช่เป็น transaction type เฉพาะของ spot-check Pattern เดียวกับ physical-count

> **TODO:** ยืนยันว่า spot-check มี enum costing-method เฉพาะของตน (analog กับ `enum_physical_count_costing_method`) หรือสืบทอดจาก default ของ physical-count / adjustment — ไม่พบใน schema ณ ขณะนี้

## 5. ความแตกต่างจาก carmen/docs

> **TODO:** ไม่มีโฟลเดอร์ source ใน carmen/docs สำหรับโมดูล spot-check — divergence เขียนจาก baseline ของ carmen/docs ไม่ได้ ตัวเลือกในการเปรียบเทียบ source: (a) `../carmen-inventory-frontend/` UI flow และ form definition (b) `../carmen-inventory-frontend-e2e/` E2E test spec (ยังไม่มีสำหรับ spot-check — ตรวจสอบโดย `ls .../tests/ | grep -i 'spot\|check'`) (c) interface `SPC-*` ใน carmen/docs ที่อาจมีในอนาคต จนกว่าอย่างน้อยหนึ่งจะมี ให้ถือ Prisma schema เป็น source of truth เดียว

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — เอนทิตีสี่ตัว (`tb_spot_check`, `tb_spot_check_comment`, `tb_spot_check_detail`, `tb_spot_check_detail_comment`); enum สองตัว (`enum_spot_check_status`, `enum_spot_check_method`)
- **Secondary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend/` — ยังไม่เห็น route `spot-check` ที่ระดับบนสุด `app/` ค้นใต้โฟลเดอร์โมดูลย่อยเมื่อเขียน UI flow
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; เขียน scenario เมื่อมี
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ledger ที่ variance adjustment เขียนลง), [inventory-adjustment](/th/inventory/inventory-adjustment) (variance rollup post เป็น `tb_stock_in` / `tb_stock_out`), [physical-count](/th/inventory/physical-count) (คู่เทียบการนับเต็มที่ใช้ pattern การ integrate rollup-to-adjustment เดียวกัน; ดู [physical-count/01-data-model](/th/inventory/physical-count/01-data-model) สำหรับ infrastructure ที่แชร์), [costing](/th/inventory/costing) (default การตีมูลค่า variance สืบทอดจาก costing ฝั่ง adjustment)
