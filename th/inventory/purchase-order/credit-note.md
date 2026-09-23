---
title: ใบลดหนี้ (Credit Note)
description: ใบลดหนี้จากผู้ขายกับ GRN ก่อนหน้า — quantity_return ตัดสต๊อก, amount_discount revalue ต้นทุน; หนึ่งสินค้าต่อ GRN ได้ครั้งเดียว, ส่วนลด/ภาษี cap ตามบรรทัดและสัดส่วน GRN; submit ไป draft → completed ไม่มีการโพสต์ AP/GL
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ใบลดหนี้ (Credit Note)

> **At a Glance**
> **เจ้าของ:** ฝ่ายจัดซื้อ &nbsp;·&nbsp; **ตาราง:** `tb_credit_note` (+ detail, comments) &nbsp;·&nbsp; **วงจร:** `draft` → `completed` เมื่อ **Submit** (transaction เดียวกับ stock ledger); `in_progress` / `cancelled` / `voided` มีอยู่ใน enum แต่ไม่มีอะไรเขียนมัน &nbsp;·&nbsp; **เอกสารต้นทาง:** [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; การปรับยอดหลังรับของกับ GRN เดิม — กลับรายการ cost layer ของสินค้าคงคลัง (คืนสินค้าหรือ revalue ต้นทุน); ไม่มีการโพสต์ AP/GL
> **Re-sync 2026-09-22** กับ `credit-note.{service,logic,validate}.ts` @ ef4d6f08f, `routes/procurement/credit-note/` @ 0713cbc9, Bruno `procurement/credit-note/` (7 ไฟล์), e2e `601-cn` / `602-cn-reason` กฎที่เพิ่มเมื่อ 2026-09-17/21: แต่ละสินค้าบน GRN ลดหนี้ได้ครั้งเดียว; ส่วนลด / ภาษีต่อบรรทัดต้องไม่เกินมูลค่าบรรทัดและไม่เกินสัดส่วนของ GRN; เซิร์ฟเวอร์คำนวณ `return_base_qty` ใหม่; แท็บ Stock Movement เป็น API จริง **แก้ไขแล้ว:** ไม่มี approval workflow ไม่มี action Void ไม่มี gate การปิดงวด

![ใบลดหนี้ (Credit Note) screen](/screenshots/purchase-order/credit-note.png)

![ใบลดหนี้ (Credit Note) detail screen](/screenshots/purchase-order/credit-note-detail.png)

## 1. ภาพรวมและผู้ใช้งาน

**ใบลดหนี้ (Credit Note — CRN)** คือเอกสารสำหรับการแก้ไขหลังการรับสินค้าในห่วงโซ่ procure-to-pay เมื่อผู้ขายเรียกเก็บเกิน, จัดส่งของชำรุดหรือขาด, หรือให้ส่วนลดย้อนหลัง CRN จะเป็นเอกสารที่บันทึกการกลับรายการกับ GRN ต้นทาง และกลับรายการ cost layer ของสินค้าคงคลัง ไม่มีโค้ดโพสต์ AP liability ใดๆ ในระบบหลังบ้านของใบลดหนี้ (ดู § 4) มีสองชนิดคือ **`quantity_return`** ที่คืนสินค้าจริง (ลด stock จาก lot ของ GRN, กลับ cost layer) และ **`amount_discount`** ที่แก้ราคาอย่างเดียว (ไม่กระทบสต๊อก, revalue ต้นทุน lot)

**สร้างโดย** ฝ่ายจัดซื้อเมื่อได้รับ credit invoice จากผู้ขาย (`procurement.credit_note` เป็น permission resource แบบ CRUD ใน SPA, `constant/permissions.ts`; gateway ไม่ประกาศ `@Permission` บน route ของ CN) &nbsp;·&nbsp; **ทำให้เสร็จโดย** ผู้ใช้คนเดียวกันกด **Submit** — **ไม่มีขั้นอนุมัติ**: `submit()` ย้าย `draft → completed` โดยตรงและโพสต์ ledger ใน transaction เดียวกัน (`credit-note.logic.ts` L513-640) `tb_credit_note` มีคอลัมน์ `workflow_*` / `user_action` แต่ไม่มีโค้ดใน `credit-note.service.ts` / `credit-note.logic.ts` อ่านหรือเขียน workflow (ที่ค้นเจอคำว่า `workflow` มีแค่ชื่อ notification event เดียว) **แก้ไข 2026-09-22** — รุ่นก่อนหน้าบอกว่า "อนุมัติโดยผู้อนุมัติใน workflow (ใช้เส้นทางเดียวกับ PO)" &nbsp;·&nbsp; **อ่านโดย** costing engine และการปิดงวด (`period-end.validate.ts` `CN_COMPLETE = {completed, cancelled, voided}`; CN ที่ `draft` นับเป็นเอกสารเปิดที่ block การปิดงวด)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ตั้ง CN กับ GRN | จัดซื้อ → ใบลดหนี้ → **สร้างใหม่** (`/procurement/credit-note/new`) | เลือกผู้ขายและ GRN (`grn_id`); รายการเพิ่มได้ผ่าน **Select from GRN** เท่านั้น (`cn-add-item-dialog.tsx` — หนึ่งแถวต่อ `product × location` ที่รับบน GRN นั้น พร้อม qty, price, discount, tax และ net ของ GRN); ไม่มีแถวเปล่า picker ผู้ขาย / GRN ค้นหาแบบ on demand (`c2ce1271`) |
| เลือก `quantity_return` กับ `amount_discount` | Header field `credit_note_type` | Return จะย้ายสต๊อก; Discount แค่ revalue ต้นทุน ต่อบรรทัดฟอร์ม cap `return_qty ≤ ปริมาณที่รับของ GRN` และสำหรับ `amount_discount` cap `net_amount ≤ net amount ของ GRN` (`cn-form-schema.ts` `maxReturnQty` / `maxCnAmount`, `039e3523`) |
| ลดหนี้สินค้าเดิมซ้ำ | — | **ถูก block** แต่ละสินค้าบน GRN ลดหนี้ได้ครั้งเดียวข้ามทุก CN ที่ไม่ใช่ cancelled / voided (`findAlreadyCreditedIssues`, `credit-note.validate.ts` L105-138; key ตามสินค้า ไม่ใช่ product × location ดังนั้นของชิ้นเดียวกันลดหนี้ครั้งละ location ไม่ได้) |
| ตรวจผลต่อ ledger ก่อน / หลัง submit | Detail → แท็บ **Stock Movement** | API จริงตั้งแต่ 2026-09-21: `GET .../credit-notes/:id/stock-movements` — ก่อน submit เป็น preview ที่สร้างจากรายการ (lot `-`) หลัง submit เป็น movement จริง (lot, in/out qty, cost); แถว `quantity_return` อ่านเป็น issue ส่วนแถว `amount_discount` มีเฉพาะ cost (`cn-stock-table.tsx`, `use-credit-note.ts` L191; gateway `credit-notes.controller.ts` L142 — ยังไม่อยู่ใน Bruno collection) |
| ตั้งค่า return-to-stock vs write-off | (อัตโนมัติ) | Engine จะตัดจาก FIFO lot ของ GRN เดิมก่อน แล้วจึงใช้ lot อื่นที่มีอยู่สำหรับ product+location เดียวกัน; ส่วนต่างระหว่างต้นทุนของ CN กับต้นทุน lot ที่ตัดจะถูกบันทึกเป็น `diff_amount` บน cost-layer row — **ไม่** โพสต์เข้าบัญชี GL/write-off ใดๆ (ไม่มีโค้ดโพสต์ลักษณะนี้อยู่) — ดู [costing](/th/inventory/costing) `COST_XMOD_006` |
| Submit | Detail → summary bar **Submit** (`cn-footer-action.tsx`) | `PATCH .../credit-notes/:id/submit` `{ doc_version }` — `draft → completed` และการโพสต์ inventory เกิดใน transaction **เดียว** (`55bfc6b5b`); บรรทัดที่ลดหนี้มากกว่าที่ location ถืออยู่จะถูกตัดลงถึงศูนย์และส่วนที่เหลือบันทึกเป็น cost variance รายงานกลับเป็น `shortfalls[]` ใน submit response UI ล็อกเอกสาร (`isLocked`) เมื่อ `completed` |
| โพสต์ CN ไปยัง AP | — | **ยังไม่ implement** — ไม่มีโค้ด AP debit memo หรือการโพสต์ AP ใดๆ ในระบบหลังบ้านของใบลดหนี้; `completed` เพียงแค่ trigger การโพสต์ inventory ตาม § 6 |
| ระบุเลขที่ credit invoice ของผู้ขาย | Header `invoice_no` / `tax_invoice_no` | ฟิลด์อ้างอิงฝั่งผู้ขายเท่านั้น; ไม่มีฟีเจอร์ match ปลายน้ำ (ดู [03-user-flow-finance.md](/th/inventory/purchase-order/03-user-flow-finance)) list endpoint ไม่คืนฟิลด์เหล่านี้ (`types/credit-note.ts`) |
| Void / cancel CN ที่ posted แล้ว | — | **ยังไม่ implement** gateway เปิดเฉพาะ `GET`, `GET :id`, `GET :id/stock-movements`, `POST`, `PATCH :id`, `DELETE :id`, `PATCH :id/submit`, `GET :id/print-viewer` (`credit-notes.controller.ts`); ไม่มี endpoint ใดเขียน `cancelled` หรือ `voided` (ทั้ง repo สองค่านี้ปรากฏเฉพาะใน filter `notIn` และชุดของ period-end) **แก้ไข 2026-09-22** — รุ่นก่อนหน้าระบุ action Detail → **Void**; gap report ของ e2e (`601-cn-gap.md`) ยืนยันอิสระว่า "no Commit and no Void button anywhere in this module" |
| ลบ draft | Detail → delete (`cn-header.tsx` แสดงเมื่อ `!isLocked`) | `DELETE .../credit-notes/:id` — "Only draft credit notes can be deleted" (`credit-note.service.ts` L507) |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | วิธีแก้ |
|---|---|---|
| "… returns a product that has already been credited on this receipt. Each product on a goods receipt can be credited once." (`CN_ERROR.GRN_LINE_ALREADY_CREDITED`, field `product_id`) | CN อีกใบ (ที่ไม่ใช่ `cancelled` / `voided`) ลดหนี้สินค้านี้บน `grn_id` เดียวกันไปแล้ว (`findAlreadyCreditedIssues`; `b6772667f`, 2026-09-21) | ลบบรรทัดนี้; ไปแก้ CN ใบก่อนแทน |
| `DISCOUNT_EXCEEDS_LINE_AMOUNT` / `TAX_EXCEEDS_LINE_AMOUNT` | `discount_amount` หรือ `tax_amount` บนบรรทัดเกิน `return_qty × price` — ส่วนลดที่มากกว่าบรรทัดจะดัน `net_amount` ติดลบ (`findCreditNoteAmountIssues`, `credit-note.validate.ts` L40-80; กฎ `findAmountCapIssues` ที่ใช้ร่วมกันก็ใช้กับ PR / PO / GRN ด้วย, `0293a6fa4`) | แก้จำนวนเงิน |
| "Discount on <line> is X, but the receipt only discounted Y …" / เทียบเท่าสำหรับภาษี (field `discount_amount` / `tax_amount`) | ส่วนลด / ภาษีของบรรทัดเกินส่วนลด / ภาษีของ GRN line **ตามสัดส่วนที่คืน** (`findCreditNoteGrnAmountIssues`, L180-250; `1c6dcc262`) — คืนหนึ่งในสิบของการส่งมอบก็ลดหนี้ส่วนลดได้หนึ่งในสิบ บรรทัดที่ GRN ไม่เคยรับ หรือ GRN line ที่ qty เป็นศูนย์ จะไม่ถูกแตะ | ลดจำนวนลงให้เท่ากับสัดส่วนของ GRN |
| ฟอร์ม: `maxReturnQty` / `maxCnAmount` / `net_amount` ต้อง "positive" | cap ฝั่ง client ใน `cn-form-schema.ts`: `return_qty ≤ _grn_received_qty`; สำหรับ `amount_discount` `net_amount ≤ _grn_net_amount` และ `> 0` (`039e3523`) | แก้ก่อน Save; เซิร์ฟเวอร์ validate ซ้ำตอน submit |
| "Cannot submit credit note with status '<status>'. Only draft can be submitted." | Submit บน CN ที่ไม่ใช่ draft (`credit-note.logic.ts` L543) | — |
| "Only draft credit notes can be deleted" | `DELETE` บน CN ที่ completed แล้ว | — |
| `409 Conflict` | `doc_version` ใน body ของ `PATCH` / `submit` เก่าแล้ว (`OptimisticLockError`, `credit-note.service.ts` L418) | โหลดใหม่แล้วทำซ้ำ |
| Submit response `shortfalls[]` ("N line(s) exceeded the stock on hand and were booked as a cost variance, not deducted.") | บรรทัด `quantity_return` ลดหนี้มากกว่าที่ location ถืออยู่; CN ยังคง `completed` | ตรวจสอบสต๊อก; ส่วนต่างคือ `diff_amount` บน cost layer ไม่ใช่ GL entry |
| "GRN required for quantity_return" | **ยังไม่ยืนยัน — ไม่พบเป็นข้อความตรงตัว** `submit()` ยอมรับ `grn_id` ที่หายไป: มัน mark CN เป็น `completed` พร้อมข้อความ "Credit note submitted (no inventory impact — missing GRN or details)" (L570-576) ในทางปฏิบัติฟอร์มบังคับให้มี GRN เพราะรายการเพิ่มได้จาก GRN เท่านั้น | — |
| "Period is closed — cannot void", "Rate not in history", "Tax rate must match GRN snapshot", "User not authorised at this stage" | **ถอดออก 2026-09-22 — ไม่มีข้อความเหล่านี้อยู่จริง** ไม่มี action void ไม่มี period gate ตอน submit CN ไม่มี FX lookup แบบ dynamic ไม่มี stage authorisation (ไม่มี workflow) ในระบบหลังบ้านของใบลดหนี้ | — |

## 4. กรณีพิเศษ

- **การปัดเศษเงิน.** Money fields เก็บที่ `Decimal(20,5)`; ยอดที่คำนวณ round half-up ที่ **2 ตำแหน่ง** ที่ระดับบรรทัด แล้ว sum ขึ้น header (ตรงกับ PO/GRN)
- **FX rate handling.** `exchange_rate` เป็นฟิลด์ snapshot ธรรมดา ที่ auto-populate ครั้งเดียว — จาก rate ของ GRN ที่เลือก หรือจาก currency master (`cn-general-fields.tsx`) — แล้วแก้ไขได้อิสระ **ยังไม่ยืนยัน/แก้ไขแล้ว:** ไม่มีการ resolve rate ใหม่ตาม `cn_date` และไม่มีการคำนวณ FX gain/loss ใดๆ ในระบบหลังบ้านของใบลดหนี้ — ตรงกับข้อค้นพบเดียวกันที่ยืนยันแล้วสำหรับ PO/PR/GRN ใน [master-data/exchange-rate](/th/inventory/master-data/exchange-rate)
- **Return-to-stock vs write-off.** `quantity_return` จะตัดจาก FIFO lot ของ GRN เดิมก่อน แล้วจึงใช้ lot อื่นที่มีอยู่สำหรับ product+location เดียวกัน (ยังคงลำดับ FIFO); ไม่มีการ guard ป้องกัน negative inventory ในเส้นทางนี้ — ถ้าไม่มีสต๊อกเหลือเลย `out_qty = 0` และต้นทุนทั้งหมดของ CN จะถูกบันทึกเป็น `diff_amount` บน cost-layer row **ไม่มีการโพสต์เข้าบัญชี GL/write-off ใดๆ ในระบบหลังบ้าน** — `diff_amount` เป็นเพียง column ธรรมดาบน `tb_inventory_transaction_cost_layer` ไม่ใช่ general-ledger entry (ยืนยันแล้วว่าไม่มีทั้งโมดูล ดู [inventory/02-business-rules](/th/inventory/inventory/02-business-rules))
- **Snapshot semantics.** ชื่อผู้ขาย, สินค้า, currency, FX rate, tax rate, และ pricelist refs ถูก snapshot ตอน draft การแก้ไข master record ไม่มีผลย้อนหลังกับ CRN
- **ไม่มีการ void.** ไม่มี endpoint หรือปุ่มที่ void หรือ cancel CN (`cancelled` / `voided` เป็น enum member ที่ไม่มีตัวเขียน) **แก้ไข 2026-09-22** จาก "void ได้เฉพาะตอนงวดเปิด" — ไม่มี void และไม่มี period gate; ตาราง period ก็ถูกเปลี่ยนชื่อ `tb_period*` → `tb_inventory_period*` แล้วด้วย (2026-09-16) Period-end แค่นับ CN ที่ `draft` เป็นเอกสารเปิด (`CN_COMPLETE` ไม่รวม `draft`)
- **หนึ่งสินค้า หนึ่งการลดหนี้.** กฎครั้งเดียวต่อ GRN key ตาม `product_id` อย่างเดียว (`creditNoteGrnProductKey`) จงใจไม่ใช้ product × location ดังนั้นของที่เก็บสอง location ลดหนี้สองครั้งไม่ได้; การเช็คข้าม CN ที่ `cancelled` / `voided` (`credit-note.logic.ts` L265-290) — ซึ่งวันนี้หมายถึงไม่ข้ามอะไรเลย เพราะไม่มี status ไหนถูกเขียน
- **ปริมาณฐานคำนวณโดยเซิร์ฟเวอร์.** `return_base_qty = return_qty × return_conversion_factor` derive บนเซิร์ฟเวอร์ (`credit-note.logic.ts` L211-220; `55bfc6b5b`) — ค่าที่ client ส่งมาถูกละเลย; ledger ย้าย `return_base_qty`
- **การจัดการ shortfall.** เมื่อบรรทัด `quantity_return` เกินที่ location ถืออยู่ การตัดจะหยุดที่จำนวนที่มี และส่วนที่เหลือบันทึกเป็น cost variance; submit ยังสำเร็จ (`completed`) และคืน `shortfalls[]` เพื่อให้ผู้ปฏิบัติงานรู้ว่าการตัดไม่สะอาด
- **ไม่มีการโพสต์ AP.** ทั้ง `quantity_return` และ `amount_discount` ไม่สร้าง debit memo หรือ record ฝั่ง AP ใดๆ เมื่อ `completed`; ไม่มีโค้ดโพสต์ AP ใดๆ ในระบบหลังบ้านของใบลดหนี้ (`credit-note.logic.ts`, `credit-note.service.ts`, `inventory-transaction.service.ts`)

---

## 5. โมเดลข้อมูล (Dev)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`)

### 5.1 `tb_credit_note`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `cn_no` | `String? @db.VarChar` | Yes | เลขอ้างอิง CRN; unique ในกลุ่ม non-deleted |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | วันที่เอกสาร — ใช้สร้าง `cn_no` (`generateCnNo`, `credit-note.service.ts` L560) ไม่ได้ขับเคลื่อนการ resolve FX rate (ไม่มีโค้ดลักษณะนี้) และไม่ถูกส่งให้การโพสต์ inventory ตอน submit (`executeCreditNoteQty` / `executeCreditNoteAmount` รับเฉพาะ `grn_id`, `credit_note_id`, `detail_items`, `user_id`); movement ที่ได้ถูก assign ให้ `tb_inventory_period` ไหนเป็นเรื่องของ inventory-transaction service — ดู [inventory/transaction](/th/inventory/inventory/transaction) |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `completed` (transition เดียวที่โค้ดทำจริง — `submit()`) `in_progress`, `cancelled`, `voided` ถูกประกาศ (schema.prisma L211-217) และ render โดย `CN_STATUS_CONFIG` แต่ไม่มี service ใดเขียน; enum `CN_STATUS` ของ SPA ไม่มี `in_progress` เลย (`types/credit-note.ts`) |
| `credit_note_type` | `enum_credit_note_type` | No | `quantity_return` หรือ `amount_discount` |
| `vendor_id`, `vendor_name` | `String? @db.Uuid` / `VarChar` | Yes | Snapshot จาก `tb_vendor` ตอน draft |
| `grn_id`, `grn_no`, `grn_date` | mixed | Yes | GRN ต้นทาง — จำเป็นสำหรับ `quantity_return`, optional สำหรับ `amount_discount` |
| `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` | mixed | Yes | อ้างอิง pricelist (ทางเลือก) |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Snapshot currency + rate, auto-populate ครั้งเดียวจาก rate ของ GRN ที่เลือกหรือ currency master ตอนแก้ไข แล้วแก้ไขได้อิสระ **แก้ไขแล้ว:** ไม่ได้ resolve แบบ dynamic ตาม `cn_date` — ไม่มีโค้ดลักษณะนี้ |
| `cn_reason_id`, `cn_reason_name`, `cn_reason_description` | mixed | Yes | FK + snapshot ถึง `tb_credit_note_reason` (หน้าจอ config `/config/credit-note-reason`, e2e `602-cn-reason`) |
| `invoice_no`, `invoice_date`, `tax_invoice_no`, `tax_invoice_date` | mixed | Yes | เลขที่ credit invoice ของผู้ขาย optional ใน payload (`invoice_date` ต้องละไว้ ไม่ใช่ส่ง `""` เมื่อว่าง — ISO-8601 datetime); list endpoint ไม่คืนค่า |
| `workflow_id`, `workflow_*`, `user_action` | mixed | Yes | ประกาศไว้ (รูปแบบเดียวกับ PO; `workflow_history` default `{}`) แต่ **ไม่ใช้งาน** — ไม่มี code path ของ CN อ่านหรือเขียน |
| `last_action`, `last_action_*` | mixed | Yes | การเปลี่ยนสถานะล่าสุด |
| `note`, `description`, `info`, `dimension`, `doc_version` | mixed | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([cn_no, deleted_at])` map `creditnote_cn_no_u`; `@@index([cn_no])`. FKs ไปยัง `tb_vendor`, `tb_currency`, `tb_good_received_note`, `tb_credit_note_reason` — ทั้งหมด `onDelete: NoAction`

### 5.2 `tb_credit_note_detail`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `credit_note_id`, `sequence_no` | mixed | No / No / Yes | PK, parent FK, ลำดับ |
| `inventory_transaction_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_inventory_transaction` ต้นทางสำหรับ `quantity_return`; Null สำหรับ `amount_discount` |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | สถานที่รับเดิม; การคืนใช้ที่เดียวกัน |
| `product_id`, `product_*` | mixed | No / Yes | Snapshot สินค้า |
| `return_qty`, `return_unit_*`, `return_conversion_factor`, `return_base_qty` | `Decimal(20,5)` / mixed | Yes | ปริมาณคืนในหน่วยผู้ใช้ + base; `0` สำหรับ `amount_discount` |
| `price` | `Decimal(20,5)` | Yes | ราคาต่อหน่วย — มักเป็นราคาที่ GRN |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | Snapshot ภาษี + การแปลงเป็น base |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | Snapshot ส่วนลด + base |
| `extra_cost_amount`, `base_extra_cost_amount` | `Decimal(20,5)` | Yes | ค่าใช้จ่ายเพิ่ม (เช่น ค่าขนส่ง) ที่ลด |
| `cn_amount` | `Decimal(20,5)` | Yes | คอลัมน์จำนวนลดหนี้ที่เพิ่มโดย `20260710000000_add_cn_amount_credit_note_detail`; มีใน schema (L448-523) แต่ `credit-note.logic.ts` / `credit-note.service.ts` ที่ HEAD ไม่ได้อ้างถึง — ถือว่าสงวนไว้ |
| `sub_total_price`, `net_amount`, `total_price` | `Decimal(20,5)` | Yes | ยอดบรรทัดใน currency ธุรกรรม; `net_amount` คือค่าที่ฟอร์ม cap เทียบกับ net ของ GRN สำหรับ `amount_discount` |
| `base_*` | `Decimal(20,5)` | Yes | ค่าเดียวกันใน BU base currency |
| `info`, `dimension`, `doc_version`, audit | — | Yes | Metadata มาตรฐาน |

**Constraints:** `@@unique([credit_note_id, sequence_no, deleted_at])`; `@@index([credit_note_id, sequence_no])`. FKs `onDelete: NoAction`

### 5.3 ตาราง Comment

`tb_credit_note_comment` และ `tb_credit_note_detail_comment` ใช้รูปแบบ comment มาตรฐาน — ดู [purchase-request/01-data-model](/th/inventory/purchase-request/01-data-model)

## 6. วงจรการทำงาน / กติกาทางธุรกิจ

`doc_status`: `draft` → `completed` (terminal) เมื่อ **Submit** นั่นคือ state machine ทั้งหมดที่ใช้งานจริง

```
[*] → draft ──(PATCH :id/submit, transaction เดียว: status + ledger)──► completed
        │
        └──(DELETE :id, draft เท่านั้น)──► ถูกลบ (soft delete)

  in_progress / cancelled / voided : ประกาศใน enum_credit_note_doc_status,
                                     render โดย CN_STATUS_CONFIG, ไม่เคยถูกเขียน
```

- **`draft`** — แก้ไขได้; ยังไม่กระทบ AP หรือ inventory Save = `PATCH .../credit-notes/:id` พร้อม `doc_version` และ `credit_note_detail.{add,update,delete}`; `doc_version` ที่เก่าแล้วคืน `409`
- **`completed`** — ตั้งโดย `submit()` พร้อมกับการโพสต์ inventory (`quantity_return`: `executeCreditNoteQty` ตัด `return_base_qty` จาก lot ของ GRN แบบ FIFO หรือ average ตามวิธีคิดต้นทุนของ BU; `amount_discount`: revalue ต้นทุน / variance ผ่าน `diff_amount`) และเขียน back-link `inventory_transaction_id` ลงทุกบรรทัด ไม่มี AP debit memo หรือ GL entry ถูกสร้างสำหรับทั้งสองแบบ
- **`in_progress`**, **`cancelled`**, **`voided`** — **ไม่มีตัวเขียน** รุ่นก่อนหน้าของ section นี้อธิบายขั้นอนุมัติที่ใช้ workflow ของ PO ซ้ำ เส้นทาง cancel และ void ที่จำกัดด้วยงวดซึ่ง "กลับ posting ทุกรายการ"; ไม่มีสิ่งเหล่านั้นในโค้ด (`credit-note.logic.ts`, `credit-note.service.ts`, gateway `credit-notes.controller.ts`) การแก้ CN ที่ `completed` แล้วในวันนี้หมายถึงเอกสารชดเชย ไม่ใช่การกลับรายการ

**GRN anchor:** รายการมาจากแถว `product × location` ที่รับบน GRN ต้นทางเท่านั้น `return_qty` cap ที่ปริมาณที่รับของ GRN ส่วนลด / ภาษี cap ที่มูลค่าบรรทัดและที่สัดส่วนของ GRN และแต่ละสินค้าบน GRN นั้นลดหนี้ได้โดย CN ใบเดียว **Authorisation:** SPA gate route ด้วย `procurement.credit_note` (CRUD); backend ใช้ tenant scoping เท่านั้น — ไม่มีการเช็ค stage หรือ role

## 7. ความเชื่อมโยงข้ามโมดูล

- [purchase-order](/th/inventory/purchase-order) — PO ต้นทางของ GRN เดิม **ยังไม่ยืนยัน:** ยอด CRN ป้อนเข้าตัวเลข open / received ของ PO หรือไม่ — `received_qty` บน `tb_purchase_order_detail` เพิ่มโดยการโพสต์ GRN เท่านั้น และไม่มีโค้ด CN แตะแถว PO
- [good-receive-note](/th/inventory/good-receive-note) — เอกสารต้นทางของทุกบรรทัด `quantity_return`
- [costing](/th/inventory/costing) — `COST_POST_003` (revalue ยอด), `COST_XMOD_006` (กลับต้นทุน lot), `COST_CALC_005` (revalue ต้นทุน lot จาก credit-note-amount — แก้ไขแล้ว ไม่ใช่ FX ตามที่เคยอ้างอิงผิดในหน้านี้)
- [master-data/credit-note-reason](/th/inventory/master-data/credit-note-reason) — taxonomy ของเหตุผล
- [master-data/exchange-rate](/th/inventory/master-data/exchange-rate) — รูปแบบ snapshot rate ที่ใช้ร่วมกับ PO/PR/GRN (auto-populate ครั้งเดียว แก้ไขได้อิสระ; ไม่มีการ resolve แบบ dynamic)
- [master-data/vendor](/th/inventory/master-data/vendor) — Snapshot ผู้ขาย การ route AP debit memo ยังไม่ยืนยัน (ไม่มีโค้ดลักษณะนี้)

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (L335-410), `tb_credit_note_detail` (L448-523), `tb_credit_note_comment` (L412), `tb_credit_note_detail_comment` (L525), `tb_credit_note_reason` (L312), enums `enum_credit_note_type` (L206) และ `enum_credit_note_doc_status` (L211-217)
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/credit-note/` — `credit-note.validate.ts` (ครั้งเดียวต่อ GRN L105-138, cap จำนวนเงินบรรทัด L40-80, สัดส่วน GRN L180-250), `credit-note.logic.ts` (`submit` L513-640, derive ปริมาณฐาน L211, lookup key ที่ลดหนี้แล้ว L265-290), `credit-note.service.ts` (`generateCnNo` L560, guard การลบ L507, optimistic lock L418); gateway `apps/backend-gateway/src/application/credit-notes/credit-notes.controller.ts` (8 route รวม `GET :id/stock-movements` L142)
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/credit-note/` — 7 ไฟล์ (`GET-list`, `GET-by-id`, `POST-create`, `PATCH-update`, `PATCH-submit`, `DELETE-remove`, `GET-print-to-report`); `stock-movements` ยังไม่อยู่ใน collection
- **Frontend route:** `../carmen-inventory-frontend-react/routes/procurement/credit-note/` — `cn-form-schema.ts` (cap), `cn-add-item-dialog.tsx` (Select from GRN), `cn-stock-table.tsx` (แท็บ Stock Movement), `cn-header.tsx` / `cn-footer-action.tsx` (Edit / delete / Submit เท่านั้น); `types/credit-note.ts`; `constant/credit-note.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/docs/user-stories/601-cn.md` (124 case, `tests/601-cn.spec.ts` — skip 82, oracle จริง ~6) และ `docs/test-cases/gaps/601-cn-gap.md` (65 case ที่ยังไม่ cover; note ของ reviewer ในนั้นคือคำอธิบาย UI จริงแบบสั้นที่ดีที่สุด: ไม่มีปุ่ม Commit / Void, status `draft · in_progress · completed · cancelled · voided`, ไม่มีแนวคิด lot, ไม่มี field จำนวนเงินบน header); `docs/user-stories/602-cn-reason.md` (18) / `gaps/602-cn-reason-gap.md` (27)
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram
