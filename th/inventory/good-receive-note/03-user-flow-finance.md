---
title: ใบรับสินค้า (Goods Receive Note) — User Flow — Finance
description: สิ่งที่โมดูล GRN ทำและไม่ทำสำหรับ Finance — โมดูล AP Invoice จับคู่ GRN ที่ commit แล้ว แต่ตัว GRN เองไม่มีหน้าจอ role หรือ journal ของ Finance
published: true
date: '2026-10-27T15:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, finance, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — User Flow — Finance

> **At a Glance**
> **หน้านี้เอกสารอะไร:** จุดที่ผู้ใช้ Finance / AP สัมผัส GRN ณ 2026-10-27 โมดูล GRN เองยังไม่มี persona, role หรือ journal ของ Finance; สิ่งที่เปลี่ยนคือโมดูล **Accounts Payable** แยกต่างหากดึงบรรทัด GRN ที่ `committed` ไปเป็น AP invoice และโพสต์เข้า general ledger ได้แล้ว

> ⚠️ **สถานะเปลี่ยนในรอบนี้ (2026-10-27)** เวอร์ชันก่อนหน้าของหน้านี้ (2026-07-15 ตรวจซ้ำ 2026-09-22) ระบุว่าไม่มี vendor-invoice entity, ไม่มีการโพสต์ AP, ไม่มี match algorithm และพื้นที่ `routes/accounting` ของ frontend แสดงเฉพาะแถวที่ปั้นขึ้น ตรวจซ้ำกับ `carmen-turborepo-backend` `c9d788829` และ `carmen-frontend` `391062b5`:
>
> - **ตอนนี้มี AP Invoice แล้ว** Backend `apps/micro-business/src/ap/ap-invoice` (และ `ap-payment`), gateway `application/ap-invoice`, ตาราง `tb_ap_invoice`, `tb_ap_invoice_detail`, `tb_ap_invoice_detail_source`, สถานะ `enum_ap_invoice_status = draft | in_review | posted | void`, source `enum_ap_invoice_source = manual | grn | copy | excel | ai | interface` **Frontend: ยังไม่มี** — `routes/accounting/accounts-payable` สร้าง hook บน `createApMockRepository` (`shared/use-accounts-payable.ts`, `ap-mock-repository.ts`) และไม่เรียก API และ `routes/accounting/documents` เป็นแถว mock (`documentsFor()`) รายละเอียดเต็มของ flow ฝั่ง backend อยู่ที่ [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn)
> - **ลิงก์ GRN → AP** `GET` GRN candidates (`grnCandidates`, `ap-invoice.service.ts`) คืนรายการของ **GRN ที่ `committed` และ `post_type = ap`** ของ vendor และสกุลเงินเดียว ที่ยังมี `remaining_qty > 0` แต่ละบรรทัด AP เก็บแถว `tb_ap_invoice_detail_source` พร้อม `good_received_note_id`, `good_received_note_detail_item_id`, `matched_qty`, `grn_unit_price`, `matched_amount` และ `variance_amount` ตอน submit/post การตรวจต้องการให้ GRN ยังใช้งานอยู่, `committed` และ `post_type = ap` (`AP_GRN_NOT_COMMITTED`), ทุกบรรทัดใช้ vendor และสกุลเงินเดียวกัน (`AP_VENDOR_CURRENCY_MISMATCH`) และ `Σ matched_qty` ข้ามทุกเอกสาร AP ที่ไม่ void ต้องไม่เกิน `received_qty` ของรายการ (`AP_GRN_OVER_MATCHED`) — `ap-invoice.posting.ts:152-230,1100-1130` นี่คือการจับคู่ปริมาณ GRN ↔ invoice; three-way match ระดับ PO ไม่ใช่ฟีเจอร์แยกต่างหาก
> - **การโพสต์ AP เขียน GL journal** ด้วย `source = ap` (`ap-invoice.posting.ts:291`) ตัว GRN, `inventory-transaction.service.ts` และ `period-end.*` ยังไม่ import อะไรจากโมดูล GL และ `enum_gl_jv_source.inventory` ไม่มีผู้เขียน
> - **ฝั่ง GRN ของลิงก์** response รายละเอียด GRN มี `ap_invoices` (เอกสาร AP ที่ยังใช้งานและไม่ void ที่ดึงบรรทัดใดของมันไป, `findActiveApInvoicesForGrn`, `good-received-note.ap-link.ts:87`); ขณะที่รายการนั้นไม่ว่าง GRN ที่ committed แก้ไขไม่ได้เลย (`GRN_AP_LINKED_NOT_EDITABLE`) และ frontend แสดงปุ่ม *Edit* ที่ปิดพร้อมเลขเอกสาร AP (`grn-header.tsx:60-65,167-175`) — ดังนั้นการล็อกนี้เข้าถึงได้วันนี้เฉพาะผ่าน gateway API หากไม่มี AP GRN ที่ committed ยังรับการแก้ไขส่วนหัวของใบกำกับ (`invoice_no`, `invoice_date`, `invoice_f`, `payment_due_date`, ฟิลด์ credit-term, `post_type`, `description`, `note`)
> - **เส้นทาง Void** ไม่มี AP guard บน `voidGrnById` / `reject` และไม่จำเป็นต้องมี: AP ดึงเฉพาะ GRN ที่ `committed` ซึ่ง void และ reject ปฏิเสธอยู่แล้ว (`GRN_COMMITTED_NOT_VOIDABLE`; reject รับเฉพาะ `draft`/`saved`) GRN ที่ committed ไม่มีวันถูก void ไม่ว่ามี AP หรือไม่
> - **External export** `GET /api/ext/v1/ap-invoices` (API key ของ BU, อ่านอย่างเดียว, `inventory/accounting-export`) เผยแพร่ GRN ที่ `committed` และ credit note เป็นเอกสาร vendor-invoice สำหรับระบบบัญชีภายนอก และข้าม GRN ที่ `post_type = consignment` (`export-core.service.ts:194-228`)
> - `enum_stage_role` (enum บทบาท stage ของ workflow ที่ใช้ร่วมกับ PR / PO / GRN) ยังไม่มีสมาชิก `finance` และโมดูล GRN ไม่มีหน้าจอ Finance, approval stage หรือ action journal lifecycle operation ของมัน (`save`, `commit`, `approve`, `reject` ใน `good-received-note.logic.ts`, `voidGrnById` ใน `good-received-note.service.ts`) ไม่แตะ journal หรือ AP entity ใด
> - **Credit Note** (`tb_credit_note`, FK กลับไปยัง `tb_good_received_note`, หนึ่ง credit ต่อสินค้าต่อ GRN ตั้งแต่ 2026-09-21) ยังคงเป็นเอกสารแยกที่บันทึกไว้ใต้ [purchase-order/credit-note](/th/inventory/purchase-order/credit-note); credit note ที่ยังใช้งานล็อกบรรทัด GRN ที่อ้างถึงไม่ให้แก้ไขและ void (`GRN_LINE_STOCK_LOCKED`)

## สิ่งที่ยืนยันได้และยังไม่ยืนยัน

| ข้อกล่าวอ้าง | สถานะ |
| --- | --- |
| Tag โหมดการจัดสรร extra-cost (`manual` / `by_value` / `by_qty`) เก็บบน `tb_extra_cost` | **ยืนยันแล้ว** — Prisma enum จริง `enum_allocate_extra_cost_type` (สามค่าเท่านั้น; ไม่มี `by_weight` / `by_volume`) frontend เสนอ `by_qty` และ `by_value` (`grn-extra-cost-fields.tsx:201-202`) |
| จำนวนเงิน extra-cost ที่แบ่งข้ามบรรทัด GRN และป้อนเข้าสู่การคำนวณ cost layer แบบ FIFO / average | **ยืนยันแล้วว่าใช้งานจริงตั้งแต่ 2026-09-10** (`f8cd9f0d9`) `allocateExtraCost()` (`good-received-note.extra-cost.ts:40-61`) แบ่ง `Σ tb_extra_cost_detail.amount` ไปยังบรรทัดที่นำสต๊อกเข้าคลัง — `by_qty` = ส่วนเท่ากัน, `by_value` = ถ่วงตาม `received_base_qty + foc_base_qty`, `manual` = ไม่มี — ตอนโพสต์; ส่วนแบ่งถูกบวกเข้า landed cost ของบรรทัดและเก็บต่อ cost layer เป็น `extra_cost_amount` ตั้งแต่ 2026-10-24 extra cost ของ GRN สถานะ `saved` ยังเปลี่ยนได้จนกว่าบรรทัดใดจะถูก stock-lock (`GRN_COST_STOCK_LOCKED`) และการแก้ไขบน BU แบบ average โพสต์ใหม่เฉพาะบรรทัดที่ได้รับผลกระทบ |
| การจับคู่บรรทัด GRN กับใบกำกับผู้ขาย (ระดับปริมาณ) | **Implement ในโมดูล AP Invoice** (ดูแบนเนอร์); ไม่ใช่หน้าจอของ GRN |
| การโพสต์ AP journal | **Implement ในโมดูล AP** (`source = ap`) ไม่ใช่โดย GRN การ map บัญชี (`Dr` / `Cr`) แน่นอนเป็นการตั้งค่า AP/GL และไม่ได้บันทึกที่นี่ |
| Journal ที่ GRN เป็นต้นทาง (accrual `Dr Inventory / Cr GRN Clearing`) | **ยังไม่ implement** ไม่มีโค้ด GRN, inventory-transaction หรือ period-end ใดเรียกโมดูล GL |
| ฟิลด์ `post_type` ที่แยก `ap` / `consignment` / `cash` | **ยืนยันแล้วว่ามีผู้ใช้สองรายนอก GRN**: AP invoicing รับเฉพาะ `ap`; external export ข้าม `consignment` มันไม่เปลี่ยนอะไรภายในโมดูล GRN และยังแก้ไขได้หลัง commit จนกว่า AP invoice จะดึง GRN ไป |
| Finance Manager ปิดงวดพร้อม report aging ของ GRN Clearing | **ยังไม่ implement** ไม่พบฟีเจอร์ปิดงวดเฉพาะโมดูลนี้ |
| Finance Officer ในฐานะบทบาท workflow-stage แยกต่างหาก | **ยังไม่ implement** `enum_stage_role` ไม่มีค่า `finance`; หน้าจอ AP ถูก gate ด้วย permission key ของตัวเอง |

สำหรับโมดูล AP และ GL เอง ดู [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn) และหน้า [general-ledger](/th/inventory/general-ledger) กฎ `GRN_POST_006`–`GRN_POST_009` และ `GRN_XMOD_007` ใน [02-business-rules.md](./02-business-rules.md) ถูกเขียนใหม่ให้ชี้ไปที่โมดูล AP

## แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต 4 สถานะ; เหตุการณ์โพสต์คือ `saved → committed` (BU แบบ average โพสต์สต๊อกตอน save)
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — persona ที่การ commit โพสต์ inventory และเลื่อน PO
- โมดูล GL (เอกสารบนหน้า wiki ของตัวเอง ไม่ใช่ที่นี่): `../carmen-turborepo-backend/apps/micro-business/src/gl/`, gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports}/`
- ซอร์สโมดูล AP: `../carmen-turborepo-backend/apps/micro-business/src/ap/`; mock ของ frontend `../carmen-frontend/routes/accounting/accounts-payable/` (ไม่เรียก API)
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — เป็นเจ้าของการแก้ไขฝั่ง vendor สำหรับ variance การรับ
- Sibling: [02-business-rules.md](./02-business-rules.md) §5 / §6 — ตาราง posting-rule และกฎข้ามโมดูล
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — แหล่ง design เก่าสำหรับแนวคิด three-way-match / AP; เจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว
- เอกสารที่เกี่ยวข้อง: [purchase-order/credit-note](/th/inventory/purchase-order/credit-note)
