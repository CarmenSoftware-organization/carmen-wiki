---
title: การนับสต๊อกประจำงวด (Physical Count) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-06-17T08:00:00.000Z
tags: physical-count, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Data Model

> **At a Glance**
> **ตาราง:** `tb_physical_count_period` &nbsp;·&nbsp; `tb_physical_count` &nbsp;·&nbsp; `tb_physical_count_detail` &nbsp;·&nbsp; ตาราง `_comment` ต่อระดับ (สามตาราง)
> **กลุ่มผู้ใช้:** นักพัฒนา / ผู้ตรวจสอบ (อ้างอิงเชิงพัฒนา)
> **FK สำคัญ:** period `→ tb_period`; count `→ tb_location` และ `→ tb_physical_count_period`; detail `→ tb_product` และ `→ tb_unit` (`inventory_unit_id`) การเชื่อม variance rollup ไปยัง [inventory-adjustment](/th/inventory/inventory-adjustment) เป็น JSON เท่านั้น (`tb_stock_in.info.countId` / `tb_stock_out.info.countId`) — ไม่มี FK ใน Prisma
> **รูปแบบการตรวจสอบ:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; ลำดับชั้นสามระดับ (period → document → detail) — การนับเองไม่เขียนลง inventory ledger; การ post adjustment คือจุดเชื่อมต่อเข้ากับ ledger

> **Source of truth:** Prisma schema ฝั่ง backend อ่านนี่ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใน package เป็น copy ที่ auto-generate และไม่ถือเป็น authoritative

## 1. ภาพรวม

โมดูล Physical Count เป็น **ชั้นเอกสาร** สำหรับการนับ end-to-end ทุกรายการที่สถานที่หนึ่ง — การดำเนินการตามรอบที่เป็น baseline ทางกฎระเบียบที่อธิบายใน [physical-count](/th/inventory/physical-count) § 1 ฝั่ง Prisma persist ต้นไม้เอกสารสามระดับภายใต้ลำดับชั้น **`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`**: period header รวบรวมเอกสารการนับทุกฉบับที่เปิดในงวดบัญชีเดียวกัน (`tb_period`) แต่ละเอกสาร count แทนการจับคู่หนึ่ง (period, location) และพกพาสถานะการนับ / ประเภท / ความคืบหน้าของ counter และแต่ละ row ของ detail คือหนึ่งบรรทัดสินค้าบนการนับนั้น โดยมี `on_hand_qty` (book), `actual_qty` (counted) และ `diff_qty` (variance) Comment และ attachment ห้อยอยู่บนทั้งสามระดับ (`tb_physical_count_period_comment`, `tb_physical_count_comment`, `tb_physical_count_detail_comment`)

โมดูลอยู่ **เหนือ [inventory-adjustment](/th/inventory/inventory-adjustment)**: เมื่อเอกสารการนับถึง `completed` และบรรทัดผลต่างได้รับการยอมรับ ชั้น application จะ roll up ผลต่างเข้าสู่เอกสาร `tb_stock_in` (overage) และ/หรือ `tb_stock_out` (shortage) ด้วย reason code `COUNT_OVERAGE` / `COUNT_SHORTAGE` ซึ่งการ post ของเอกสารนั้นจะเขียน row `tb_inventory_transaction` ที่ลงจอดบน ledger ของ [inventory](/th/inventory/inventory) ตารางของ physical-count เอง **ไม่** เขียนลง inventory ledger โดยตรง — เอกสาร adjustment คือจุดเชื่อมต่อ ข้อมูล lot บน count detail บางเบา — `tb_physical_count_detail` พกพาเพียง `on_hand_qty` / `actual_qty` ต่อสินค้าต่อสถานที่ (ไม่มีคอลัมน์ `lot_no`); การ recount ระดับ lot จัดการที่ฝั่ง adjustment ผ่านการเลือก cost-layer ตอน post ตาม [inventory](/th/inventory/inventory) `INV_CALC_005` / `INV_CALC_006`

> **TODO:** ดึงรายละเอียด UI / interaction จาก `../carmen-inventory-frontend-react/` และพฤติกรรม end-to-end จาก `../carmen-inventory-frontend-e2e/` เมื่อ spec มี ไม่มีโฟลเดอร์ source ใน carmen/docs สำหรับโมดูลนี้ — divergence (หัวข้อ 5) จะเขียนไม่ได้จนกว่าจะมีเอกสารเพิ่มหรือยืนยันว่าฟิลด์เป็น source-of-truth-only

## 2. เอนทิตี

Prisma schema canonical กำหนดหกตาราง (ตรวจสอบกับ `prisma-shared-schema-tenant/prisma/schema.prisma` บรรทัด 5002–5152):

- **`tb_physical_count_period`** — header ระดับ period จัดกลุ่มเอกสารการนับทั้งหมดสำหรับหนึ่งงวดบัญชี (`period_id → tb_period`) พกพา `status` บน `enum_physical_count_period_status` (`draft`, `counting`, `completed`)
- **`tb_physical_count_period_comment`** — comment / attachment ระดับ period พกพา `message`, JSON array ของ `attachments` และ `enum_comment_type` (`user` / `system`)
- **`tb_physical_count`** — เอกสารการนับสำหรับหนึ่งคู่ `(period, location)` พกพา `location_id → tb_location`, snapshot `location_code` / `location_name`, `physical_count_type` (`yes` / `no` — flag frozen-vs-live ตาม `enum_physical_count_type`), `description`, `status` บน `enum_physical_count_status` (`pending`, `in_progress`, `completed`), `start_counting_at` / `start_counting_by_id`, `completed_at` / `completed_by_id`, ตัวนับความคืบหน้า `product_counted` / `product_total` และ `doc_version` (`Int @db.Integer`, คอลัมน์ nullable = No, default `0`) — ตัวนับเวอร์ชันสำหรับ optimistic-concurrency ที่เพิ่มค่าทุกครั้งที่ save/review/submit; client ต้อง echo ค่านี้กลับตอน update มิฉะนั้นจะได้รับ `409 Conflict` (ดู [system-config/doc-version](/th/inventory/system-config/doc-version)) Unique ภายใน `(period, location, deleted_at)`
- **`tb_physical_count_comment`** — comment / attachment ระดับเอกสารบน count
- **`tb_physical_count_detail`** — บรรทัดการนับต่อสินค้า พกพา `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK ไปยัง `tb_unit`), `on_hand_qty` (snapshot ของ book ขณะนับ), `actual_qty` (ปริมาณ physical ที่ป้อน), `diff_qty` (`actual_qty - on_hand_qty`), `counted_at` / `counted_by_id` และ `sequence_no` สำหรับลำดับบน sheet
- **`tb_physical_count_detail_comment`** — comment / attachment ระดับบรรทัดบน row ของ count detail

> **TODO:** ขยายแต่ละเอนทิตีเป็นตารางฟิลด์เต็มเมื่อมี source ใน carmen/docs (หรือ spec authoritative ทางเลือก) cross-reference กับ convention ของรูปทรงตารางใน [inventory-adjustment/01-data-model](/th/inventory/inventory-adjustment/01-data-model) เพื่อความสม่ำเสมอ

## 3. ความสัมพันธ์

```
tb_period
    │
    └─1──*──► tb_physical_count_period  (status: draft → counting → completed)
                │
                ├─1──*──► tb_physical_count_period_comment
                │
                └─1──*──► tb_physical_count  (หนึ่ง row ต่อ (period, location);
                            │                  status: pending → in_progress → completed;
                            │                  physical_count_type ∈ {yes, no} — frozen vs live)
                            │
                            ├─1──*──► tb_physical_count_comment
                            │
                            └─1──*──► tb_physical_count_detail
                                        │   (on_hand_qty, actual_qty, diff_qty;
                                        │    counted_at / counted_by_id;
                                        │    ไม่มีคอลัมน์ lot_no ที่ระดับนี้)
                                        │
                                        └─1──*──► tb_physical_count_detail_comment


เมื่อ count เสร็จ variance rollup เขียนไปยัง [[inventory-adjustment]]:
    ▼
tb_stock_in  (reason_code = COUNT_OVERAGE)   สำหรับ diff_qty > 0
tb_stock_out (reason_code = COUNT_SHORTAGE)  สำหรับ diff_qty < 0
    │
    └── tb_stock_in_detail / tb_stock_out_detail.info = { countId: <tb_physical_count.id> }
    │
    └── เมื่อ adjustment post → tb_inventory_transaction พร้อม enum_transaction_type = adjustment_in / adjustment_out
```

หมายเหตุ:

- **ลำดับชั้นสามระดับ** Period header รวบรวมการนับหลายสถานที่; เอกสาร count เป็นหนึ่งต่อหนึ่งสถานที่; detail เป็นหนึ่งต่อหนึ่งสินค้า สะท้อนวิธีดำเนิน physical count: หนึ่งการดำเนินการสิ้นงวด หลายสถานที่นับขนานกัน หลายร้อยบรรทัดสินค้าต่อสถานที่
- **Variance rollup เป็นชั้น application ไม่ใช่ Prisma-FK** ไม่มี FK ใน Prisma จาก `tb_stock_in.info.countId` ย้อนไปยัง `tb_physical_count.id` — การเชื่อมเป็น convention ใน JSON ห่วงโซ่ audit สร้างใหม่ฝั่งอ่าน
- **ทุก `@relation` FK declaration ที่ระบุชัดเจนใช้ `onDelete: NoAction` หรือ `onDelete: Cascade`** — รักษาความหมาย soft-delete (`deleted_at`)

## 4. Enum

- **`enum_physical_count_period_status`** — วงจรชีวิตระดับ period สามค่า: `draft` (วางแผน period), `counting` (เอกสารหนึ่งฉบับขึ้นไปภายใต้กำลังดำเนินการ), `completed` (เอกสารทั้งหมดเสร็จ; period ล็อกจากการนับใหม่)
- **`enum_physical_count_status`** — วงจรชีวิตระดับเอกสาร สามค่า: `pending` (สร้างแล้ว sheet สร้างแล้ว counter ยังไม่เริ่ม), `in_progress` (counter เริ่มป้อนปริมาณแล้ว), `completed` (ทุกบรรทัดนับและเอกสาร submit แล้ว; eligible สำหรับ variance rollup)
- **`enum_physical_count_type`** — flag โหมด frozen vs live บน `tb_physical_count.physical_count_type` สองค่า: `yes` (frozen — stock movement ที่สถานที่บล็อกระหว่างช่วงการนับ), `no` (live — การเคลื่อนไหวดำเนินต่อ snapshot ของ book ทำต่อบรรทัด ณ เวลาที่นับ) Default คือ `yes` ตาม Prisma `@default(yes)`
- **`enum_physical_count_costing_method`** — enum แยกที่ด้านบนของ schema (บรรทัด 55) ประกาศวิธีตีมูลค่าสี่วิธีที่ใช้เมื่อ post adjustment ของผลต่างการนับ: `standard`, `last`, `average`, `last_receiving` วิธีที่เลือกขับเคลื่อนต้นทุนต่อบรรทัดบน `tb_stock_in_detail.cost_per_unit` / `tb_stock_out_detail.cost_per_unit` ของ rollup adjustment
- **`enum_transaction_type`** — ที่ระดับ inventory ledger (บรรทัด 1103) `physical-count` **ไม่ใช่** ค่าตรงบน enum นี้ — ผลต่างจากการนับ post เป็น `adjustment_in` / `adjustment_out` ผ่านเอกสาร adjustment ไม่ใช่เป็น transaction type เฉพาะของการนับ

## 5. ความแตกต่างจาก carmen/docs

> **TODO:** ไม่มีโฟลเดอร์ source ใน carmen/docs สำหรับโมดูล physical-count — divergence เขียนจาก baseline ของ carmen/docs ไม่ได้ ตัวเลือกในการเปรียบเทียบ source: (a) `../carmen-inventory-frontend-react/` UI flow และ form definition (b) `../carmen-inventory-frontend-e2e/` E2E test spec (ยังไม่มีสำหรับ physical-count — ตรวจสอบโดย `ls .../tests/ | grep -i 'physical\|count'`) (c) interface `PHC-*` ใน carmen/docs ที่อาจมีในอนาคต จนกว่าอย่างน้อยหนึ่งจะมี ให้ถือ Prisma schema เป็น source of truth เดียว

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — เอนทิตีหกตัว (`tb_physical_count_period`, `tb_physical_count_period_comment`, `tb_physical_count`, `tb_physical_count_comment`, `tb_physical_count_detail`, `tb_physical_count_detail_comment`); enum สี่ตัว (`enum_physical_count_period_status`, `enum_physical_count_status`, `enum_physical_count_type`, `enum_physical_count_costing_method`)
- **Secondary (TODO):** source carmen/docs — ไม่มีสำหรับโมดูลนี้
- **Frontend (TODO):** `../carmen-inventory-frontend-react/` — ยังไม่เห็น route `physical-count` ที่ระดับบนสุด `app/` ค้นใต้โฟลเดอร์โมดูลย่อยเมื่อเขียน UI flow
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count; เขียน scenario เมื่อมี
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ledger ที่ adjustment ของผลต่างเขียนลง), [inventory-adjustment](/th/inventory/inventory-adjustment) (variance rollup post เป็น `tb_stock_in` / `tb_stock_out`), [costing](/th/inventory/costing) (การตีมูลค่าผลต่างผ่าน `enum_physical_count_costing_method`), [spot-check](/th/inventory/spot-check) (ลูกพี่ลูกน้องการนับบางส่วนที่ใช้โมเดลแนวคิดเดียวกัน)
