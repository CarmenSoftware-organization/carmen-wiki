---
title: ปิดงวด (Period End)
description: การปิดสิ้นงวด — เริ่มรอบการนับ, review เอกสารที่ค้างและ physical count แล้วปิดคลิกเดียว (one-click close) ที่ยกยอด lot balance ไปยังงวดถัดไป
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ปิดงวด (Period End)

> **At a Glance**
> **เจ้าของ:** ผู้ใช้ใดก็ได้ที่ถือสิทธิ์ `inventory_management.period_end.execute` (ดูอย่างเดียว: `.view`) &nbsp;·&nbsp; **กระบวนการ:** เริ่มนับ → review → close เหนือ `tb_inventory_period` (เปลี่ยนชื่อจาก `tb_period` โดย migration `20260916141000_rename_tb_period_to_tb_inventory_period`) &nbsp;·&nbsp; **หน้าจอ:** `/inventory-management/period-end` (การ์ดงวดปัจจุบัน + ประวัติงวดที่ปิดแล้ว, ปุ่ม **Start Period Close** / **Continue Counting**) และ `/inventory-management/period-end/review` (การ์ดเอกสารเจ็ดใบ + ความคืบหน้า physical-count + **Close Period**) &nbsp;·&nbsp; **เขียน:** `tb_physical_count_period.status = counting` (ตอนเริ่ม), transaction ยกยอด `close`/`open`, `tb_inventory_period.status = closed`, งวดถัดไปถูกสร้างอัตโนมัติ; `tb_inventory_period_snapshot` เฉพาะ tenant ที่ใช้ average method &nbsp;·&nbsp; **1-liner:** เปิดรอบการนับ แล้ว freeze งวดโดยการ zero ทุก lot ที่ยังเหลือ balance แล้วเปิดใหม่ในงวดถัดไป

![ปิดงวด (Period End) screen](/screenshots/inventory/period-end.png)

## 1. ภาพรวมและผู้ใช้งาน

Period End คือ **พิธีการ run-the-close** ในสองขั้นที่ย้อนกลับไม่ได้ **Start Period Close** (เพิ่ม 2026-08-27, `POST /period-ends/start-counting`) เปิดรอบการนับ — มันย้าย `tb_physical_count_period` ของงวดจาก `draft` เป็น `counting` ซึ่งเป็นสิ่งเดียวที่ปลดล็อกปุ่ม **Start** ใน [physical-count](/th/inventory/physical-count) จากนั้น **Close Period** (`POST /period-ends`) freeze งวดเมื่อทุก gate เขียว ตัวการปิดเองคือ stock transaction: ทุก lot ที่ยังมี balance คงเหลือถูก zero ในงวดที่ปิดและถูกสร้างใหม่ในงวดถัดไปที่ต้นทุนเดิม

- **Period-end operator** — ผู้ใช้ใดก็ได้ที่มี `inventory_management.period_end.execute` เป็นผู้กดทั้งสองปุ่ม; ผู้ใช้ที่มี `*.view` เปิดตรวจดูหน้าจอได้
- **เจ้าของเอกสารต้นน้ำ** — เคลียร์เอกสาร GRN / SI / SO / SR / CN ที่ block การเริ่มหรือการปิด
- **ผู้นับ (Counters)** — ทุก location ที่กำหนดต้องมี physical count สถานะ `completed` ก่อนปิดงวด

## 2. งานที่พบบ่อย

> **สอง gate ตรวจฝั่ง server ภายใต้ row lock `SELECT … FOR UPDATE` บน `tb_inventory_period` (`period-end.service.ts` `startCounting` / `closeCurrent` ทั้งคู่รัน validator ของตัวเองซ้ำภายใน transaction):**
>
> **Gate การเริ่มนับ** (`listStartCountingBlockers`, `period-end.validate.ts`) — ทุกเอกสารเคลื่อนไหวสต๊อกที่ลงวันที่ในงวดต้องจบแล้ว มิฉะนั้นการนับจะบันทึกตัวเลข on-hand ที่เก่าไปแล้ว:
> - [ ] ไม่มี **GRN** ที่ `doc_status ∉ {committed, voided}` — GRN ที่เป็น `draft` **block** การเริ่ม
> - [ ] ไม่มี **Stock In** / **Stock Out** ที่ `doc_status ∉ {completed, cancelled, voided}` — SI/SO ที่เป็น `draft` block
> - [ ] ไม่มี **SR** ที่มีเลขที่ (`sr_no` ไม่ใช่ `draft-…`) ที่ยัง `draft` หรือ `in_progress`
> - PR และ PO ไม่เคย block การเริ่ม — ทั้งคู่ไม่เขียนลง ledger
>
> **Gate การปิด** (`validatePeriodEnd`) — หกตัวนับ ต้องเป็นศูนย์ทั้งหมด:
> - [ ] ไม่มี **SR** ที่มีเลขที่ในงวดที่ยัง `in_progress` โดย `workflow_next_stage ≠ '-'`
> - [ ] ไม่มี **GRN** ในสถานะกลางทาง — `doc_status` ต้องเป็น `draft`, `committed` หรือ `voided` (GRN ที่เป็น `draft` *ไม่* block การปิด)
> - [ ] ไม่มี **CN** ในสถานะกลางทาง — ต้องเป็น `draft`, `completed`, `cancelled` หรือ `voided`
> - [ ] ไม่มี **Stock In** / **Stock Out** ที่ `in_progress` (SI/SO ไม่เคยไปถึง `in_progress` ผ่าน service ของตัวเอง — `create` เขียน `draft`, `commit` เขียน `completed` — ตัวนับนี้จึงเป็นศูนย์ในทางปฏิบัติ)
> - [ ] ทุก location ที่กำหนด (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) มี **physical count ที่ completed** สำหรับงวดนี้
>
> **PR และ PO ไม่เป็น gate การปิดอีกต่อไป** (เคยเป็นในโค้ดรอบ 2026-07; `validatePurchaseRequest` / `validatePurchaseOrder` ยังอยู่ใน `period-end.validate.ts` แต่ `validatePeriodEnd` ไม่เรียกแล้ว) ยังปรากฏเป็นการ์ด review เพื่อเป็นข้อมูล Spot check ไม่ใช่ gate ของขั้นใดทั้งสิ้น เอกสารถูกจับคู่ด้วย**วันที่เอกสาร** (`grn_date`, `si_date`, `so_date`, `sr_date`, `cn_date`) ภายใน `[start_at, end_at]` และนับเฉพาะ PR/SR ที่**มีเลขที่** — เลขที่ placeholder `draft-…` ถูกข้าม (`NUMBERED_DOC`, 2026-09-18)

| งาน | ที่ใด | หมายเหตุ |
|---|---|---|
| ดูงวดปัจจุบัน | Period End (`/inventory-management/period-end`) | การ์ดแสดงรหัสงวด (YYMM), fiscal year/month, วันเริ่ม/สิ้นสุด, icon + label สถานะ, note; "งวดปัจจุบัน" = งวดแรกสุดที่ `status ∈ {open, locked}` |
| ดูประวัติงวดที่ปิดแล้ว | หน้าเดียวกัน, รายการประวัติใต้การ์ด | `GET /period-ends` คืนเฉพาะงวด **closed** เรียงค่าเริ่มต้น `fiscal_year desc, fiscal_month desc`, มี `?fiscal_year=YYYY` ให้เลือก |
| เริ่มรอบการนับ | **Start Period Close** บนการ์ด → dialog ยืนยัน ("This cannot be undone — the round stays open until the period is closed") | ยิง `POST /period-ends/start-counting`; เมื่อสำเร็จ navigate ไป `/review` เมื่อรอบเป็น `counting` แล้ว ปุ่มเดียวกันจะอ่านว่า **Continue Counting** และแค่ navigate (ไม่มี POST ครั้งที่สอง) |
| Review เอกสารที่ block | หน้า review — การ์ดหนึ่งใบต่อโมดูล (PR / PO / GRN / CN / SR / SI / SO) พร้อมจำนวน + badge Complete/Incomplete | คลิกการ์ดเปิด dialog รายการเอกสาร; แต่ละแถวลิงก์ไปเอกสารต้นทาง (`pe-document-paths.ts` — แถว SI/SO เปิด `/inventory-management/inventory-adjustment/{id}?type=stock-in|stock-out`) |
| ติดตามความคืบหน้าการนับ | หน้า review — การ์ด location หนึ่งใบต่อ location ที่กำหนด พร้อม progress counted/total | คลิกการ์ดเปิด (หรือ**สร้าง**) count ของ location นั้น — `openPhysicalCount(item, physical_count_period.id)`; การ์ดถูก disable พร้อม tooltip "Counting has not started for this period yet." จนกว่ารอบจะเป็น `counting` |
| ปิดงวด | **Close Period** (ปุ่ม destructive, dialog ยืนยัน "All transactions and physical counts in this period will be locked.") | เปิดใช้งานเฉพาะเมื่อ `can_close` ของ payload review เป็น true; ยิง `POST /period-ends` (ไม่มี body); เมื่อสำเร็จกลับไปหน้า list |

## 3. ข้อผิดพลาดและการตรวจสอบ

error ของ period-end ทั้งหมดมาจาก `packages/error-catalog/src/catalog.ts`:

| อาการ / ข้อความ | Code · HTTP | สาเหตุ | การกระทำ |
|---|---|---|---|
| ปุ่ม **Close Period** disabled, tooltip "All transactions must be complete and all physical counts must be completed before closing." | — | `can_close` ของ payload review เป็น false (`close_blocking` มีตัวนับที่ไม่เป็นศูนย์) ตั้งแต่ 2026-08-27 frontend ไม่คำนวณกฎจากการ์ดเองอีกต่อไป — quirk "โมดูลว่างอ่านเป็น incomplete" เดิมหายไปแล้ว | แก้เอกสาร / การนับตามรายการ แล้วกด **Refresh** |
| `Cannot close period: {total} document(s) are incomplete` | `PERIOD_END_CLOSE_BLOCKED` · 422 | validation ฝั่ง backend ล้มเหลว (ไม่ว่าตอนตรวจครั้งแรกหรือตอน re-check ภายใน row lock); `data` ของ response ถือตัวนับ `close_blocking` ต่อประเภท | Refresh หน้า review; แก้ไข; ปิดใหม่ |
| `Cannot start counting: {total} document(s) in this period are still open` | `PERIOD_END_START_COUNTING_BLOCKED` · 422 | เอกสารเคลื่อนไหวสต๊อกยังเปิดอยู่; `data` ถือ `{ counts, total, documents }` ต่อประเภท (`grn`, `stock_in`, `stock_out`, `sr`) frontend render เป็น dialog **"Finish these documents first"** ที่ list ทุกตัว block พร้อมลิงก์ แทน toast | Commit / void / complete เอกสารที่ list แล้วลองใหม่ |
| `Counting cannot be started for this period` | `PERIOD_END_COUNTING_NOT_ALLOWED` · 409 | ตอนเริ่ม: งวดไม่ `open` อีกต่อไป หรือรอบการนับ `completed` ไปแล้ว ตอนปิด: session อื่นปิดงวดไปแล้วระหว่างที่ session นี้กำลังปิดอยู่ (path ของ race ที่ปิดแล้วใช้รายการ catalog นี้ซ้ำ — string จริง `Period already closed` เดิมไม่มีอีกแล้ว) | Refresh; ไม่ต้องทำอะไร |
| `No current period found` | `PERIOD_END_NO_CURRENT_PERIOD` · 404 | ไม่มี row `tb_inventory_period` ที่ `status ∈ {open, locked}` (start-counting ต้องการ `open` โดยเฉพาะ) | สร้าง/ตรวจสอบงวดผ่าน [system-config/period](/th/inventory/system-config/period) (`/api/{bu}/inventory-periods`) |
| stock-in ที่ลงวันที่เดือนก่อนถูก reject | `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD` · 422 | ตั้งแต่ 2026-08-31 ledger resolve งวดจาก**วันที่เอกสาร** (`findOpenPeriodForDate`); create/commit ของ SI ต้องการ `si_date` ในงวด open/locked, create/commit ของ SO ต้องการ `so_date` ในงวด**ปัจจุบัน** (`STOCK_OUT_DATE_NOT_CURRENT_PERIOD`) ดู [transaction](/th/inventory/inventory/transaction) § 3 | ลงวันที่เอกสารใหม่ให้อยู่ในงวดที่เปิด |

## 4. กรณีพิเศษ

- **การเริ่มเป็น idempotent; การปิดไม่ใช่** การเรียก `start-counting` บนรอบที่ `counting` อยู่แล้วคืน `{ already_counting: true }` แทนที่จะ conflict; รอบที่ `completed` คืน 409 การปิดเมื่อ commit แล้วไม่มี endpoint reopen ในโมดูลนี้
- **ทั้งสองขั้นเป็น all-or-nothing และกัน race** `startCounting` และ `closeCurrent` แต่ละตัวรันในหนึ่ง transaction ด้วย `SELECT … FOR UPDATE` บน row ของงวด และรัน validator ของตัวเองซ้ำภายใต้ lock นั้น ดังนั้นเอกสารที่ถูกสร้างระหว่าง validate กับ commit เล็ดลอดเข้ามาไม่ได้
- **lot ใดยกไปข้างหน้าตัดสินด้วย `end_at` ไม่ใช่ "อะไรก็ตามที่เหลือตอนคลิก"** `findAllRemainingLots` พิจารณาเฉพาะ cost layer ที่ `at_period` เป็นของงวดที่มี `end_at ≤ end_at ของงวดที่กำลังปิด` (fix 2026-08-31 `0a2379ebe` / `772e87ea1`) — receipt ที่ post เข้างวดถัดไปที่เปิดอยู่แล้วจะไม่ถูกกวาดเข้าการปิด
- **งวดถัดไปถูก provision อัตโนมัติ** `ensureNextPeriod` (`period-end.close-transaction.helper.ts`) find-or-create `tb_inventory_period` ถัดไป (`fiscal_month + 1`, ข้ามปีได้, `status = open`, UTC วันแรกถึงวันสุดท้าย) — ไม่มีขั้นตอน "เปิดงวดถัดไป" แยกต่างหาก
- **Snapshot ขึ้นกับ costing method** row `tb_inventory_period_snapshot` ถูกเขียน **เฉพาะ** เมื่อ `calculation_method = average` ของ business unit (`processAverageClose`); การปิดของ tenant แบบ FIFO เขียนเฉพาะ transaction ยกยอด lot `resolveCalculationMethod` อ่าน `tb_business_unit.calculation_method` (platform schema, column default `average`) และ fallback ไป `fifo` ถ้าไม่มี row ของ BU
- **lot ยกยอดใช้รูปแบบ lot เดียวกับ layer อื่นทุกตัว** `buildLotNo({ locationCode, atPeriod, seqNo })` → `{location_code}{YYMM}{seq4}` (เช่น `MK26100001`); `parent_lot_no` เชื่อม lot ใหม่กลับไปยัง lot ที่ปิด prefix `CLOSE-…` / `OPEN-…` เดิมหายไปแล้ว
- **มูลค่ายกมา (carried-forward) ถูก lock** layer `open_period` / `eop_in` (`CARRIED_IN_TRANSACTION_TYPES`) ถือมูลค่าของงวดที่ปิดเข้าสู่งวดใหม่; ถูกกันออกจากการ re-price ในงวดปัจจุบัน (Credit Note Amount ต่อ lot ของงวดที่ปิดแล้วจะบันทึก `diff_amount` แทน)
- **`locked` ไม่ถูกจัดการที่นี่** ไม่มี endpoint lock/reopen ในโมดูลนี้; `enum_period_status.locked` ถูก set โดย inventory-period service ที่อยู่หลัง [system-config/period](/th/inventory/system-config/period) (`/api/{bu}/inventory-periods`, permission key `system_admin.inventory_period`) ทั้งนี้ `findCurrent` / `findReview` / `closeCurrent` ถือว่างวด `locked` เป็นงวดปัจจุบัน งวดที่ lock จึงยังแสดง — และปิด — จากหน้าจอนี้ได้; `startCounting` ต้องการ `open`
- **งวดของ physical-count ถูกกวาดเมื่อปิด** `closeCurrent` mark row `tb_physical_count_period` ของงวดที่ยังไม่ completed ให้เป็น `completed` (`physical_count_period_closed` ใน response)
- **ความ unique ของงวด** มีงวดที่ไม่ถูกลบเพียงหนึ่งงวดต่อ YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`)

---

## 5. กระบวนการ (Dev)

Period End **ไม่ใช่ Prisma table เดียว** — เป็นกระบวนการเหนือหลายตาราง:

| ตาราง | บทบาท |
|---|---|
| `tb_inventory_period` | Status row (`enum_period_status { open, closed, locked }`) ถือ `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at` โมดูลนี้ flip `open → closed` เท่านั้น |
| `tb_physical_count_period` | หนึ่ง row ต่องวด (`@@unique([period_id, deleted_at])`), `enum_physical_count_period_status { draft, counting, completed }` `startCounting` สร้างมันที่ `counting` (หรือย้าย row `draft` ที่มีอยู่ไป `counting`); `closeCurrent` mark เป็น `completed` |
| `tb_inventory_transaction` (+ `_detail`, `_cost_layer`) | การปิดเขียนหนึ่ง transaction `close` (zero lot, `transaction_type = close_period`, `out_qty = remaining`) และหนึ่ง transaction `open` (สร้าง lot ใหม่ในงวดถัดไป, `open_period`, `in_qty = remaining`); `inventory_doc_no` = id ของงวด, `note = "Close period YYMM"` / `"Open period YYMM"` |
| `tb_inventory_period_snapshot` | หนึ่ง row ต่อ bucket `(product, location)` พร้อม qty+cost แบบ opening / receipt / issue / adjustment / closing — **เขียนเฉพาะบน path การปิดแบบ average method** |
| `tb_physical_count` | Gate การนับต่อ location ที่กำหนด (`validatePhysicalCount`) |

**พื้นผิว API** (`apps/backend-gateway/src/application/period-end/period-end.controller.ts` ทั้งหมดอยู่ใต้ `/api/{bu_code}/period-ends` guard ด้วย `AppIdGuard('period_end.*')`):

| Endpoint | Guard key | คืนค่า |
|---|---|---|
| `GET /period-ends?fiscal_year=` | `period_end.findAll` | งวดที่ปิดแล้ว, paginated, ใหม่สุดก่อน |
| `GET /period-ends/current` | `period_end.findOne` | งวด `open`/`locked` ที่เร็วสุด |
| `GET /period-ends/review` | `period_end.findReview` | `{ id, start_date, end_date, status, physical_count_period, can_start_counting, start_blocking: { counts, total }, can_close, close_blocking: { sr, grn, cn, stock_in, stock_out, physical_count }, details: { transaction: { pr, po, grn, cn, sr, si, so }, physical_count[] } }` — แต่ละ transaction item คือ `{ count, complete_count, incomplete_count, is_complete, documents[] }` (`is_complete` คือ `count > 0 && complete_count === count`; frontend ไม่ derive ความปิดได้จากมันอีกต่อไป) |
| `POST /period-ends/start-counting` | `period_end.startCounting` | `{ period, physical_count_period: { id, status }, created, already_counting }` |
| `POST /period-ends` | `period_end.close` | row งวดที่ปิดแล้ว + `carry_over: { calculation_method, next_period_id, close_transaction_id, open_transaction_id, carried_lot_count, average_close? }` + `physical_count_period_closed` |

Bruno: `inventory/period-end/*` (list, current, review, close) และ `_uncategorized/period-end/POST-start-counting-period-end.bru`

## 6. Lifecycle

```
1. Operator เปิด /inventory-management/period-end (การ์ดงวดปัจจุบัน)
2. Start Period Close (POST /period-ends/start-counting) -> ภายใน transaction เดียว:
   - SELECT ... FOR UPDATE บน tb_inventory_period; ต้องการ status = open
   - listStartCountingBlockers (GRN ที่ไม่ committed/voided, SI/SO ที่ไม่ terminal,
     SR ที่มีเลขที่ draft/in_progress) -> 422 พร้อมรายการเอกสารถ้ามี
   - tb_physical_count_period: สร้างที่ counting หรือ draft -> counting
   -> navigate ไป /period-end/review (GET /period-ends/review)
3. ผู้นับสร้าง/complete tb_physical_count ต่อ location ที่กำหนด
   (ปุ่ม Start ของ physical-count ปลดล็อกเฉพาะขณะรอบเป็น counting)
4. Close Period (POST /period-ends) -> ภายใน transaction เดียว:
   - SELECT ... FOR UPDATE; รัน validatePeriodEnd ซ้ำ (SR / GRN / CN / SI / SO / counts)
   - ensureNextPeriod (find-or-create tb_inventory_period ถัดไป, status = open)
   - fifo BU:  findAllRemainingLots (layers ที่งวดมี end_at <= end_at นี้)
               -> writeCloseTransaction (close) -> writeOpenTransaction (open)
     average BU: processAverageClose (restate issues ที่ final average,
               rows close/open, rows ของ tb_inventory_period_snapshot)
   - tb_inventory_period.status = closed; tb_physical_count_period -> completed
5. เอกสารใหม่ที่ลงวันที่ในงวดถัดไป post เข้างวดนั้น; เอกสารที่ลงวันที่ในงวดที่ปิดแล้ว
   ถูก reject ตอน create/commit ของ SI/SO (ดู § 3)
```

## 7. ความเชื่อมโยงข้ามโมดูล

- [system-config/period](/th/inventory/system-config/period) &nbsp;·&nbsp; [costing](/th/inventory/costing) &nbsp;·&nbsp; [physical-count](/th/inventory/physical-count) (gate ของการปิด; ปุ่ม Start ของมันรอขั้นที่ 2) &nbsp;·&nbsp; [spot-check](/th/inventory/spot-check) (ไม่ใช่ gate)
- [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; [store-requisition](/th/inventory/store-requisition) &nbsp;·&nbsp; [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) — แหล่งเอกสารที่ block
- [inventory/transaction](/th/inventory/inventory/transaction) — การปิดเขียน ledger row `close` / `open`
- [reporting-audit](/th/inventory/reporting-audit) — รายงาน close-out อ่าน cost layers / snapshot

## 8. แหล่งอ้างอิง

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/` — `period-end.service.ts` (`findAll`, `findCurrent`, `startCounting`, `closeCurrent`, `findReview`), `period-end.validate.ts` (`listStartCountingBlockers`, `validatePeriodEnd`, ชุดสถานะ `*_COMPLETE`, `NUMBERED_DOC`), `period-end.close-transaction.helper.ts` (`findAllRemainingLots`, `ensureNextPeriod`, การยกยอดแบบ FIFO), `period-end.close-average.helper.ts` (การปิดแบบ average + `tb_inventory_period_snapshot`); gateway `apps/backend-gateway/src/application/period-end/period-end.controller.ts`; `apps/micro-business/src/inventory/inventory-period.helper.ts` (การ resolve วันที่เอกสาร → งวดที่ SI/SO/GRN ใช้)
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-history.tsx`, `pe-documents-dialog.tsx`, `pe-start-blocked-dialog.tsx`, `pe-document-paths.ts`, `use-period-end.ts`), `types/period-end.ts`, label ใต้ `inventoryManagement.periodEnd` ใน `messages/en.json`
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_inventory_period`, `tb_inventory_period_snapshot`, `tb_physical_count_period`, `enum_period_status`, `enum_physical_count_period_status`, `enum_inventory_doc_type`, `tb_inventory_transaction_cost_layer`; migration `20260916141000_rename_tb_period_to_tb_inventory_period`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` — describe ของหน้า list รันได้; describe ของ detail / close-workflow / close-action ยังถูก mark "Feature pending" แคตตาล็อก manual: `docs/test-cases/gaps/900-period-end-gap.md` (43 เคส รวมปุ่มที่ย้อนกลับไม่ได้สองปุ่มและ dialog "Counting has not started" ของ physical-count), user story ที่ generate `docs/user-stories/900-period-end.md` (35)
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` (concept, freeze 2026-04-27; การ start/close สองขั้นที่ implement จริงต่างออกไป — ดู § 2–5)
