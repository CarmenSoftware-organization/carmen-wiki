---
title: ปิดงวด (Period End)
description: การปิดสิ้นงวด — checklist review เหนือเอกสารที่ค้างและ physical count และการปิดคลิกเดียว (one-click close) ที่ยกยอด lot balance ไปยังงวดถัดไป
published: true
date: 2026-07-15T10:30:00.000Z
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ปิดงวด (Period End)

> **At a Glance**
> **เจ้าของ:** ผู้ใช้ใดก็ได้ที่ถือสิทธิ์ `inventory_management.period_end.execute` (ดูอย่างเดียว: `.view`) &nbsp;·&nbsp; **กระบวนการ:** review + close เหนือ `tb_period` &nbsp;·&nbsp; **หน้าจอ:** `/inventory-management/period-end` (การ์ดงวดปัจจุบัน + ประวัติงวดที่ปิดแล้ว) และ `/inventory-management/period-end/review` (checklist เอกสารที่ block + **Close period**) &nbsp;·&nbsp; **เขียน:** transaction ยกยอด `close`/`open`, `tb_period.status = closed`, งวดถัดไปถูกสร้างอัตโนมัติ; `tb_period_snapshot` เฉพาะ tenant ที่ใช้ average method &nbsp;·&nbsp; **1-liner:** freeze งวดโดยการ zero ทุก lot ที่ยังเหลือ balance แล้วเปิดใหม่ในงวดถัดไป

![ปิดงวด (Period End) screen](/screenshots/inventory/period-end.png)

## 1. ภาพรวมและผู้ใช้งาน

Period End คือ **พิธีการ run-the-close** — หน้าจอ review แสดงว่าอะไรยัง block การปิดอยู่ และปุ่ม **Close period** (สไตล์ destructive, disabled จนกว่าทุก gate จะเขียว) จะ freeze งวดปัจจุบัน ตัวการปิดเองคือ stock transaction: ทุก lot ที่ยังมี balance คงเหลือถูก zero ในงวดที่ปิด (lot `CLOSE-…`) และถูกสร้างใหม่ในงวดถัดไป (lot `OPEN-…`) ที่ต้นทุนเดิม

- **Period-end operator** — ผู้ใช้ใดก็ได้ที่มี `inventory_management.period_end.execute` เป็นผู้ trigger การปิด; ผู้ใช้ที่มี `*.view` เปิดตรวจดูหน้าจอได้
- **เจ้าของเอกสารต้นน้ำ** — เคลียร์เอกสาร PR / PO / SR / GRN / CN ที่ block การปิด
- **ผู้นับ (Counters)** — ทุก location ที่กำหนดต้องมี physical count สถานะ `completed` ก่อนปิดงวด

## 2. งานที่พบบ่อย

> **Gate เอกสารที่ block — ปุ่ม Close คง disabled จนกว่าทุกข้อจะเขียว** (`validatePeriodEnd`, ตรวจซ้ำฝั่ง server ภายใน row lock ณ เวลาปิด):
> - [ ] ไม่มี **PR** ในช่วงวันที่ของงวดที่ยัง `in_progress` โดย `workflow_next_stage ≠ '-'`
> - [ ] ไม่มี **PO** ในงวดที่ยัง `in_progress` โดย `workflow_next_stage ≠ '-'`
> - [ ] ไม่มี **SR** ในงวดที่ยัง `in_progress` โดย `workflow_next_stage ≠ '-'`
> - [ ] ไม่มี **GRN** ในสถานะกลางทาง — `doc_status` ต้องเป็น `draft`, `committed` หรือ `voided` (**GRN ที่เป็น `draft` *ไม่* block**; block เฉพาะสถานะที่อยู่ระหว่างกลางเท่านั้น)
> - [ ] ไม่มี **CN** ในสถานะกลางทาง — ต้องเป็น `draft`, `completed`, `cancelled` หรือ `voided`
> - [ ] ทุก location ที่กำหนด (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, active) มี **physical count ที่ completed** สำหรับงวดนี้
>
> Spot check **ไม่ใช่** gate ของการปิด — `validatePeriodEnd` ไม่มี validator สำหรับ spot-check

| งาน | ที่ใด | หมายเหตุ |
|---|---|---|
| ดูงวดปัจจุบัน | Period End (`/inventory-management/period-end`) | การ์ดแสดงรหัสงวด (YYMM), fiscal year/month, วันเริ่ม/สิ้นสุด, badge สถานะ, note; "งวดปัจจุบัน" = งวดแรกสุดที่ `status ∈ {open, locked}` |
| ดูประวัติงวดที่ปิดแล้ว | หน้าเดียวกัน, รายการประวัติใต้การ์ด | `GET /period-ends` คืนเฉพาะงวด **closed** เรียงใหม่สุดก่อน |
| เริ่มการปิด | ปุ่ม **Start close** บนการ์ด → `/inventory-management/period-end/review` | หน้า review โหลด `GET /period-ends/review` |
| Review เอกสารที่ block | หน้า review — การ์ดหนึ่งใบต่อโมดูล (PR / PO / GRN / CN / SR) พร้อมจำนวน + badge complete/incomplete | คลิกการ์ดเปิด dialog รายการเอกสารของโมดูลนั้น |
| ติดตามความคืบหน้าการนับ | หน้า review — ส่วน physical-count, หนึ่งแถวต่อ location ที่กำหนด พร้อม progress counted/total | คลิกแถวที่กำลังนับอยู่ deep-link ไป `/inventory-management/physical-count/{id}/entry` |
| ปิดงวด | **Close period** (ปุ่ม destructive, มี dialog ยืนยัน) | ยิง `POST /period-ends`; เมื่อสำเร็จกลับไปหน้า list |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | การกระทำ |
|---|---|---|
| ปุ่ม **Close period** disabled ("not ready to close") | การ์ดโมดูลใดเป็น `incomplete` หรือการนับของ location ที่กำหนดยังไม่ `completed` หมายเหตุ: frontend ถือว่าโมดูลที่มีเอกสาร **ศูนย์** ฉบับในงวดเป็น incomplete ด้วย (`is_complete = count > 0 && …`) ขณะที่ gate ฝั่ง backend นับจำนวนตัว block ซึ่งเป็นศูนย์ — quirk ที่ควรรู้เมื่อทดสอบงวดเปล่า | แก้เอกสาร / การนับตามรายการ แล้ว refresh |
| `Cannot close period: incomplete documents {…}` | การ re-validate ฝั่ง backend ล้มเหลว — มีเอกสารที่ block โผล่ขึ้นระหว่างการโหลด review กับการคลิก | Refresh หน้า review; แก้ไข; ปิดใหม่ |
| `Period already closed` | Race จาก concurrency — session อื่นปิดงวดไปแล้วระหว่างที่ session นี้กำลังปิดอยู่ (re-check `SELECT … FOR UPDATE`) | Refresh; ไม่ต้องทำอะไร |
| Empty state "No current period" | ไม่มี row `tb_period` ที่ `status ∈ {open, locked}` | สร้าง/ตรวจสอบงวดผ่าน [system-config/period](/th/inventory/system-config/period) |
| เอกสาร backdate "ตกไปอยู่ผิดเดือน" | ทำงานตามที่ออกแบบ — movement ถูก stamp เข้างวด **open** ปัจจุบันเสมอโดยไม่สนวันที่เอกสาร (`resolveCurrentPeriod`); งวดที่ปิดแล้วไม่รับ row ใหม่ และการ backdate ไม่เคยถูก reject | ไม่มี |

## 4. กรณีพิเศษ

- **การปิดเป็น all-or-nothing และกัน race** `closeCurrent` รันในหนึ่ง transaction ด้วย `SELECT … FOR UPDATE` บน row ของงวด และรัน validation เอกสารที่ block ซ้ำภายใต้ lock นั้น ดังนั้นเอกสารที่ถูกสร้างระหว่าง validate กับ commit เล็ดลอดเข้ามาไม่ได้
- **งวดถัดไปถูก provision อัตโนมัติ** `ensureNextPeriod` find-or-create `tb_period` ถัดไป (`fiscal_month + 1`, ข้ามปีได้, `status = open`) — ไม่มีขั้นตอน "เปิดงวดถัดไป" แยกต่างหาก
- **Snapshot ขึ้นกับ costing method** row `tb_period_snapshot` ถูกเขียน **เฉพาะ** เมื่อ `calculation_method = average` ของ business unit (`processAverageClose`); การปิดของ tenant แบบ FIFO เขียนเฉพาะ transaction ยกยอด lot และตาราง snapshot ยังว่างเปล่า
- **มูลค่ายกมา (carried-forward) ถูก lock** layer `open_period` / `eop_in` ถือมูลค่าของงวดที่ปิดเข้าสู่งวดใหม่; ถูกกันออกจากการ re-price ในงวดปัจจุบัน (Credit Note Amount ต่อ lot ของงวดที่ปิดแล้วจะบันทึก `diff_amount` แทนการ re-price)
- **`locked` ไม่ถูกจัดการที่นี่** ไม่มี endpoint lock/reopen ในโมดูลนี้; `enum_period_status.locked` ถูก set โดย period service แยกต่างหากที่อยู่หลัง [system-config/period](/th/inventory/system-config/period) ทั้งนี้ `findCurrent` ถือว่างวด `locked` เป็นงวดปัจจุบัน (`status ∈ {open, locked}`) งวดที่ lock จึงยังแสดง — และปิด — จากหน้าจอนี้ได้
- **งวดของ physical-count ถูกกวาดเมื่อปิด** `closeCurrent` mark row `tb_physical_count_period` ของงวดที่ยังไม่ completed ให้เป็น `completed`
- **ความ unique ของงวด** มีงวดที่ไม่ถูกลบเพียงหนึ่งงวดต่อ YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`)

---

## 5. กระบวนการ (Dev)

Period End **ไม่ใช่ Prisma table เดียว** — เป็นกระบวนการเหนือหลายตาราง:

| ตาราง | บทบาท |
|---|---|
| `tb_period` | Status row (`enum_period_status { open, closed, locked }`) ถือ `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at` โมดูลนี้ flip `open → closed` เท่านั้น |
| `tb_inventory_transaction` (+ `_detail`, `_cost_layer`) | การปิดเขียนหนึ่ง transaction `close` (zero lot, `CLOSE-{YYMM}-{seq}`, `transaction_type = close_period`) และหนึ่ง transaction `open` (สร้าง lot ใหม่ในงวดถัดไป, `OPEN-{YYMM}-{seq}`, `open_period`) |
| `tb_period_snapshot` | หนึ่ง row ต่อ bucket `(product, location)` พร้อม qty+cost แบบ opening / receipt / issue / adjustment / closing — **เขียนเฉพาะบน path การปิดแบบ average method** |
| `tb_physical_count` / `tb_physical_count_period` | Gate การนับต่อ location ที่กำหนด; row ของงวดถูก mark `completed` เมื่อปิด |

**พื้นผิว API** (gateway → message patterns `period-ends`): `GET /period-ends` (ประวัติงวดที่ปิด, paginated), `GET /period-ends/current`, `GET /period-ends/review` (รายละเอียดเอกสารที่ block + การนับ), `POST /period-ends` (ปิด — ไม่มี request body)

## 6. Lifecycle

```
1. Operator เปิด /inventory-management/period-end (การ์ดงวดปัจจุบัน)
2. Start close -> /period-end/review (GET /period-ends/review):
   - การ์ดเอกสารที่ block ต่อโมดูล (pr / po / grn / cn / sr)
   - progress การนับ physical-count ต่อ location
3. Close period (POST /period-ends) -> ภายใน transaction เดียว:
   - SELECT ... FOR UPDATE บน tb_period; re-validate เอกสารที่ block
   - fifo BU:  findAllRemainingLots -> writeCloseTransaction (close)
               -> writeOpenTransaction (open, งวดถัดไป)
     average BU: processAverageClose (restate issues ที่ final average,
               close/open transactions, rows ของ tb_period_snapshot)
   - tb_period.status = closed; rows ของ tb_physical_count_period -> completed
   - งวด tb_period ถัดไปถูก ensure (status = open)
4. Movement ใหม่จากนี้ stamp เข้างวดเปิดใหม่โดยอัตโนมัติ
```

## 7. ความเชื่อมโยงข้ามโมดูล

- [system-config/period](/th/inventory/system-config/period) &nbsp;·&nbsp; [costing](/th/inventory/costing) &nbsp;·&nbsp; [physical-count](/th/inventory/physical-count) (gate ของการปิด) &nbsp;·&nbsp; [spot-check](/th/inventory/spot-check) (ไม่ใช่ gate ของการปิด)
- [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; [inventory-adjustment](/th/inventory/inventory-adjustment) &nbsp;·&nbsp; [store-requisition](/th/inventory/store-requisition) — แหล่งเอกสารที่ block
- [inventory/transaction](/th/inventory/inventory/transaction) — การปิดเขียน ledger row `close` / `open`
- [reporting-audit](/th/inventory/reporting-audit) — รายงาน close-out อ่าน cost layers / snapshot

## 8. แหล่งอ้างอิง

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/` — `period-end.service.ts` (`findAll`, `findCurrent`, `closeCurrent`, `findReview`), `period-end.validate.ts` (gate เอกสารที่ block รวมถึงชุด complete-status ที่แน่นอน), `period-end.close-transaction.helper.ts` (การยกยอด lot แบบ FIFO), `period-end.close-average.helper.ts` (การปิดแบบ average + การเขียน `tb_period_snapshot`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/period-end/` (`pe-component.tsx`, `pe-review.tsx`, `pe-history.tsx`, `pe-documents-dialog.tsx`) และ `hooks/use-period-end.ts` (endpoints)
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period`, `tb_period_snapshot`, `enum_period_status`, `enum_inventory_doc_type`, `tb_inventory_transaction_cost_layer`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` — เทสหน้า list รันได้; describe ของ detail/close-workflow ถูก mark "Feature pending"
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md` (concept; การปิดที่ implement จริงต่างออกไป — ดู § 3–5)
