---
title: คลังสินค้า — User Flow (Inventory — User Flow)
description: วงจรชีวิตของ movement และไฟล์ flow เฉพาะ persona สำหรับ inventory
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า — User Flow (Inventory — User Flow)

> **At a Glance**
> **โมดูล:** [[inventory]] &nbsp;·&nbsp; **Personas:** Store Keeper &nbsp;·&nbsp; Inventory Controller &nbsp;·&nbsp; Finance &nbsp;·&nbsp; Audit / Config (Auditor + Sysadmin)
> **วงจรชีวิต workflow:** ขับเคลื่อนด้วย movement — แต่ละ `tb_inventory_transaction` คือ posting event ตัวเอง (ไม่มี draft → committed บน movement) วงจรชีวิตต่องวดบน `tb_period.status`: `open` → `closed` → `locked` การกลับรายการแบบ compensating เขียน transaction ใหม่; row ดั้งเดิมไม่เคยถูกแก้ไข
> **ดู per-persona views ด้านล่างสำหรับรายละเอียดระดับ action**

## 1. ภาพรวม

หน้านี้คือ **จุดเข้าภาพรวม** สำหรับชุด user-flow ของโมดูล `inventory` Inventory ไม่ปกติเมื่อเทียบกับโมดูลเอกสารพี่น้อง — ไม่มีเอกสาร workflow เดียวที่วงจรชีวิต draft → saved → committed เล่นบน แต่โมดูลเป็น **movement-driven**: แต่ละ row `tb_inventory_transaction` เป็น **posting event ตัวเอง** เขียนโดยโมดูล source ต้นน้ำ (GRN commit, SR approve, count complete, credit-note approve, manual stock-in / stock-out approve) "วงจรชีวิต" ที่ persona เดินผ่านคือ **วงจรชีวิตของยอด stock balance ที่ `(location_id, product_id, lot_no)`**: เปิดด้วย period-open rollforward (หรือ inbound แรกเมื่อ location ใหม่) สะสม inbound / outbound movements ผ่านงวด ถูกกระทบยอดกับ physical หรือ spot count ปรับสำหรับ variance และปิดเข้า row `tb_period_snapshot` ณ สิ้นงวด แต่ละ persona เป็นเจ้าของ slice ที่แตกต่างของวงจรชีวิตนั้น

Section 2 ด้านล่างอธิบาย **state machine ของ movement-and-period** — ชุด canonical ของ transitions ที่ legal ที่ระดับ movement และ period อิสระจากผู้ที่ทำ ไฟล์ per-persona แต่ละไฟล์ (link จาก Section 3) อธิบาย *เส้นทางผ่าน* state space นี้ของ persona — จุดเข้า การกระทำที่มี การตัดสินใจที่เผชิญ และการส่งต่อที่จบการมีส่วนร่วม Section 4 จากนั้นสรุปการส่งต่อข้าม persona ที่เย็บ paths แต่ละอันเข้าด้วยกัน (Store Keeper → Inventory Controller สำหรับ variance review, Inventory Controller → Finance สำหรับการเซ็นรับรองการตีมูลค่า, Finance Manager → Audit ที่ period lock) อ่านภาพรวมนี้ก่อนเพื่อ anchor วงจรชีวิต จากนั้น drill เข้าไฟล์ persona ที่ตรงกับ role ของคุณ

## 2. วงจรชีวิตของ Movement และ Period

state machines สองอันที่แยกจากกันอยู่ร่วมในโมดูลนี้: วงจรชีวิต **ต่อ-movement** (degenerate — แต่ละ transaction เขียน posted, อาจ compensate, อาจซ่อนผ่าน `deleted_at`) และวงจรชีวิต **ต่อ-period** บน `tb_period.status` (วงจรชีวิตเชิงสาระ: `open` → `closed` → `locked`) Transitions ด้านล่างครอบคลุมทั้งสอง

### 2.1 Transitions ระดับ Movement

| From state | Action | To state | อนุญาตสำหรับ | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | post จากเอกสาร source | `posted` | role เอกสาร source (GRN-Inventory-Manager-on-commit, SR-Approver-on-issue, Counter-on-count-complete, Finance-on-credit-note-approve, Store-Keeper-or-Controller-on-stock-in/out-approve) | เอกสาร source อยู่ในสถานะ posting ปลายทาง; `INV_VAL_001`–`INV_VAL_013` ผ่านทั้งหมด; งวดที่บรรจุวันที่ transaction เป็น `open` ตาม `INV_VAL_008` เขียน `tb_inventory_transaction` header + `tb_inventory_transaction_detail` + (สำหรับ location ประเภท inventory / consignment) `tb_inventory_transaction_cost_layer` |
| `posted` | compensating reversal | `posted` (row ใหม่) | Store Keeper, Inventory Controller, Finance | Tenant policy อนุญาต reversal ที่ role / threshold ของ user **row ใหม่** ของ `tb_inventory_transaction` เขียนด้วย `qty` ที่ negate; row ดั้งเดิม **ไม่** ถูกแก้ไข (inventory transaction เป็น immutable ตอนเขียนตาม `INV_POST_012`) |
| `posted` | soft-delete original (หลังจาก compensating reversal) | `posted` ที่ `deleted_at` set | Store Keeper, Inventory Controller, Finance | Compensating transaction ต้องถูกเขียนก่อนตาม `INV_VAL_013`; tenant policy คือ "ซ่อน transactions ที่ reverse แล้ว" `deleted_at` ของ row ดั้งเดิมถูก set; row ยังอยู่ใน database สำหรับ audit แต่ filter ออกจาก views ปกติ |
| `posted` | (ไม่มี action ตรงต่อไป) | `posted` | — | สถานะปลายทาง Audit อ่านได้; รายงานอ่านได้; period close จะกวาดเข้า `tb_period_snapshot` |

### 2.2 Transitions ระดับ Period

| From state | Action | To state | อนุญาตสำหรับ | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | สร้างงวด (system / scheduled) | `open` | System Administrator | นิยามงวด (`YYMM`, `fiscal_year`, `fiscal_month`, `start_at`, `end_at`) populate แล้ว; ไม่ทับซ้อนกับ period rows ที่มี |
| `open` | รับ movements | `open` | role ที่ทำธุรกรรมทั้งหมด (ผ่านโมดูล source) | งวดรับ inbound / outbound movement ใด ๆ ที่วันที่ transaction ตกใน `[start_at, end_at]` การ post ย้อนหลังก่อน `start_at` ของงวด route ไปยังงวดก่อนหน้า (reject ถ้างวดนั้น `closed` / `locked` ตาม `INV_VAL_008`) |
| `open` | period close (รัน period-end job) | `closed` | Finance พร้อมการเซ็นรับรอง variance-review ของ Inventory Controller เป็น pre-condition | Checklist pre-period-end สมบูรณ์: เอกสาร source `draft` / `saved` ทั้งหมด commit หรือ void; spot checks สมบูรณ์; physical count เต็มถ้ามีกำหนด (`tb_location.physical_count_type = yes`); การ approve count-variance adjustments ทั้งหมดตาม `INV_AUTH_003`; ตรวจสอบการกระทบยอด cost ตาม `INV_AUTH_005` Job (`INV_POST_009`) เขียน `tb_period_snapshot` rows และ `close_period` cost-layer rows |
| `closed` | period open (rollforward — chain กับ close) | `open` (บนงวดถัดไป) | System Administrator (scheduled job) | Chain กับ close; เขียน opening cost-layer rows ของงวดถัดไป (`open_period`) และ opening fields ของ snapshot งวดถัดไปตาม `INV_CALC_008` |
| `closed` | re-open period (พิเศษ) | `open` | Finance Manager (elevated; audit-logged ตาม `INV_AUTH_006`) | ต้องการเหตุผล audit-grade ("จำเป็นต้อง adjustment พิเศษในงวดที่ปิด") Re-open งวดสำหรับ back-posting; การ re-close ตามมาต้องทำก่อน period close ปกติถัดไป |
| `closed` | lock period | `locked` | Finance Manager | รายงานการกระทบยอดผ่าน (ไม่มี variance ระหว่าง inventory sub-ledger และ GL); review รายงาน aging; Finance Manager เซ็นรับรองตาม `INV_POST_011` หลัง lock ไม่มี role สามารถ re-open หรือ post |
| `locked` | (ไม่มี transitions อีก) | `locked` | — | ปลายทาง งวดที่ lock เป็น immutable; การแก้ไข post เข้างวดปัจจุบันที่เปิดเป็น restatement |

## 3. สารบัญ Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down ที่ทุ่มเทอธิบายจุดเข้า primary flow การตัดสินใจ และจุดออก Slugs ตรงกับ role ของ persona; คลิก link เปิด view ต่อ-persona

- [Store Keeper](./03-user-flow-store-keeper.md) — บันทึก stock movements รายวันที่ระดับ location ออกเอกสาร stock-in / stock-out สำหรับ adjustments ประจำ (found-stock, breakage) ดำเนินการ physical counts บน locations ของพวกเขา จับ count-variance lines ที่ route ขึ้นสำหรับ approve และดำเนินการ dock รับสำหรับ inbound ที่ขับเคลื่อนด้วย GRN (ครอบคลุมรายละเอียดใน Receiver flow ของ [[good-receive-note]]) ความเป็นเจ้าของของพวกเขาในโมดูล inventory เริ่มเมื่อ movement ต้องริเริ่มที่ระดับ floor และจบเมื่อเอกสารที่ถือ movement ถูกส่งต่อให้ Inventory Controller สำหรับ approval เกินเกณฑ์
- [Inventory Controller](./03-user-flow-inventory-controller.md) — เป็นเจ้าของ **ความถูกต้องของ balance** review variance จาก physical / spot counts อนุมัติเอกสาร stock-in / stock-out เกินเกณฑ์ Store Keeper ประสานงาน cadence การนับและโปรแกรม spot-check รักษา stock policy ต่อสินค้า / ต่อ location (par / min / max / reorder) บน `tb_product_location` และเป็นลายเซ็นที่สองบน pre-flight period-end (variance อนุมัติก่อน Finance run close)
- [Finance](./03-user-flow-finance.md) — เป็นเจ้าของ **การตีมูลค่าและการกระทบยอด GL** review feed costing (FIFO layer integrity, weighted-average drift) กระทบยอด inventory sub-ledger เทียบกับบัญชี control GL Inventory อนุมัติ adjustments ที่กระทบ cost เกินเกณฑ์ Inventory Controller post รายการกระทบยอด inventory-to-GL period-end และ (เป็น Finance Manager) รัน progression period-close → period-lock บน `tb_period.status`
- [Audit / Config](./03-user-flow-audit-config.md) — System Administrator (กำหนดค่า `tb_location` รวม `location_type` และ `physical_count_type`, reason codes `tb_adjustment_type`, costing method ต่อสินค้า, นิยามงวด, integration endpoints กับโมดูล source, RBAC) และ Auditor (review read-only ของ inventory transactions, cost-layer ledger, period snapshots, configuration history ทั้งหมด; รัน lot-trace และ reconciliation queries ระหว่าง workstream audit และ recall)

## 4. การส่งต่อข้าม Persona

ตารางด้านล่างจับโมเมนต์ที่งาน inventory เคลื่อนจากความรับผิดชอบของ persona หนึ่งไปอีก แต่ละการส่งต่อถูก anchor กับสถานะระบบ ณ จุดถ่ายโอน

| From persona | Trigger | To persona | สถานะระบบ ณ การส่งต่อ |
| ------------ | ------- | ---------- | ----------------------- |
| Store Keeper | เอกสาร Stock-in / stock-out ยกเกินเกณฑ์ | Inventory Controller | เอกสาร source ที่ `tb_stock_in.doc_status = in_progress` / `tb_stock_out.doc_status = in_progress`; ยังไม่มี inventory transaction เขียน |
| Store Keeper | Physical / spot count สมบูรณ์พร้อม variance lines | Inventory Controller | เอกสาร count ที่ `tb_count_stock.status = completed`; variance lines staged แต่ยังไม่ post เป็น `tb_stock_in` / `tb_stock_out` |
| Inventory Controller | Stock-in / stock-out อนุมัติ (เกินเกณฑ์ Controller) | Finance | เอกสาร source ยังเป็น `in_progress`; รอ Finance approval (โดยปกติ write-offs มูลค่าใหญ่, recall write-offs, audit-flagged adjustments) |
| Inventory Controller | การเซ็นรับรอง Variance-review สำหรับงวด | Finance | count-variance posts ทั้งหมดสมบูรณ์; งวดยัง `open`; checklist pre-period-end เคลียร์ |
| Finance | Inventory sub-ledger กระทบยอดกับ GL; period-end run | Finance Manager | งวดในสถานะ `open` พร้อม close รายงานการกระทบยอดผ่าน (variance ≤ tolerance) |
| Finance Manager | Period close รัน | Finance, Inventory Controller, Store Keeper | งวดที่ `tb_period.status = closed`; `tb_period_snapshot` rows เขียน; การ post ย้อนหลัง reject ตาม `INV_VAL_008` Personas re-engage ที่งวด (open) ใหม่ |
| Finance Manager | Period lock รัน | Auditor | งวดที่ `tb_period.status = locked`; immutable; พร้อม audit ภายนอก |
| System Administrator | การเปลี่ยน Configuration applied (location type, costing method, รายการ adjustment-type, RBAC, integration endpoint) | Personas ทั้งหมด | ไม่มีการเปลี่ยนสถานะ transaction; กฎใหม่มีผลในอนาคตสำหรับ movements ใหม่; เอกสาร source ที่กำลังดำเนินอาจต้อง re-evaluate ตามกฎ snapshot ใน `[03-user-flow-audit-config.md](./03-user-flow-audit-config.md)` |
| Auditor | Lot-recall trace สมบูรณ์ | Inventory Controller (การประสานงาน write-off) + Finance (การจัด provisioning การเงิน) | ไม่มีการเปลี่ยนสถานะ transaction; การดำเนินการ recall อยู่บนเส้นทาง `[[inventory-adjustment]]` และ `[[good-receive-note]]` credit-note |

## 5. แหล่งอ้างอิง

- `../carmen/docs/Inventory/inventory-management-prd.md` — PRD carmen/docs อธิบาย personas โมดูล inventory และเป้าหมาย (หมายเหตุ: สถานะ workflow `StockMovement` ของ PRD **ไม่ใช่** canonical — Prisma ไม่มี `doc_status` บน `tb_inventory_transaction`; หน้านี้ตาม model ที่ขับเคลื่อนด้วย movement ที่บันทึกใน [[inventory/01-data-model]])
- `../carmen/docs/Inventory/location-type-and-financial-treatment.md` — อ้างอิง carmen/docs สำหรับ variants posting ของ `location_type` ที่เปลี่ยน persona flow สำหรับ locations direct-cost และ consignment
- `../carmen/docs/inventory-management/period-end-process.md` — checklist period-end carmen/docs ฉากหลังเชิงกระบวนการต่อ Section 2.2 (state machine ระดับ period) และการส่งต่อข้าม persona ที่ period close / lock
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_inventory_doc_type`, `enum_transaction_type`, `enum_period_status`, `enum_location_type`, `enum_physical_count_type` (enums ที่ใช้ใน transitions Section 2) และความแตกต่างเทียบกับ carmen/docs ที่หล่อหลอม framing no-`doc_status`
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ posting และ authorization ที่ refer โดยแต่ละ transition row ใน Section 2 (โดยเฉพาะ `INV_POST_001`–`INV_POST_012` สำหรับ fan-out effects, `INV_AUTH_001`–`INV_AUTH_010` สำหรับ role gates, `INV_VAL_008` สำหรับ period-lock guard)
- โมดูลที่เกี่ยวข้อง: [[good-receive-note]] (source ต้นน้ำหลักของ inbound; receipts post ผ่าน `enum_inventory_doc_type = good_received_note`), [[store-requisition]] (source ต้นน้ำหลักของ outbound; issues / transfers), [[physical-count]] (source variance สำหรับ period-end), [[spot-check]] (source variance mid-period), [[inventory-adjustment]] (manual stock-in / stock-out), [[costing]] (ผู้บริโภคปลายน้ำของข้อมูล cost-layer), [[product]] (ถือ configuration costing-method)
