---
title: ใบรับสินค้า (Goods Receive Note) — User Flow — Finance
description: เหตุผลที่ไม่พบ persona Finance แบบ three-way-match / AP-posting สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้จริง
published: true
date: '2026-09-23T01:30:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, finance, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — User Flow — Finance

> **At a Glance**
> **หน้านี้เอกสารอะไร:** เหตุผลที่ flow "Finance" เดิม (review การจัดสรร extra-cost, three-way match, AP posting, ปิดงวด) ไม่ตรงกับซอร์สปัจจุบัน และสิ่งที่ยืนยันได้จริง

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้บรรยาย Finance Officer / AP Clerk ที่รัน three-way match (PO ↔ GRN ↔ ใบกำกับผู้ขาย) post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`) และ Finance Manager ที่ปิดงวดพร้อม aging ของ GRN Clearing ไม่มีสิ่งใดในนี้ที่พบในซอร์สปัจจุบัน:
>
> - **ตรวจซ้ำ 2026-09-22** ยังไม่มี vendor-invoice entity, หน้าจอบันทึก, endpoint โพสต์ AP หรือ match algorithm สิ่งที่เปลี่ยนตั้งแต่ 2026-07-15: ตอนนี้มี **โมดูล general ledger** แล้ว (`apps/micro-business/src/gl/` — journal voucher, template, budget, period, การโพสต์ลง `tb_gl_balance`; gateway `application/gl-jv`, `gl-posting`, `gl-reports`) มัน **ไม่ได้เชื่อมกับ GRN**: `GlPostingService.post()` (`gl-posting.service.ts:293`) โพสต์ `tb_gl_jv` ที่สร้างโดยโมดูล JV (`gl-jv.service.ts:214`, source `manual`), การรัน template (`gl-jv-template.service.ts:786`) หรือเส้นทาง reversal / closing ของตัวเอง (`gl-posting.service.ts:571,909,1116`); `enum_gl_jv_source.ap` / `.inventory` ไม่มีผู้เขียน; ไม่มีอะไรนอก `src/gl/` import โมดูลนี้ (มีเพียง `app.module.ts` และ seed ของ tenant) ส่วน `routes/accounting` ของ frontend (JV, AP invoice/payment, AR invoice/receipt) แสดง **แถวที่ปั้นขึ้น** จาก `routes/accounting/accounting-documents.ts` (`documentsFor()`) และไม่เรียก API ใด
> - `enum_stage_role` (enum บทบาท stage ของ workflow ที่ใช้ร่วมกับ PR / PO / GRN) ไม่มีสมาชิก `finance`
> - โมดูล backend ของ good-received-note ตอนนี้มี lifecycle operation ห้าตัว — `save`, `commit`, `approve`, `reject` (`good-received-note.logic.ts`) และ `voidGrnById` (`good-received-note.service.ts`) — ไม่มีตัวใดแตะ journal, ledger หรือ AP entity
> - ฟีเจอร์เดียวที่ **จริง** และเกี่ยวข้องกับ AP ในผลิตภัณฑ์คือ **Credit Note** (`tb_credit_note` ตาราง Prisma จริงที่ยืนยันแล้ว มี FK แท้กลับไปยัง `tb_good_received_note`) — เอกสารที่ post debit memo ฝั่ง AP เทียบกับ GRN ก่อนหน้า (ตั้งแต่ 2026-09-21 หนึ่ง credit ต่อสินค้าต่อ GRN) เป็นเอกสารประเภทแยกต่างหากที่มีจริง; ไม่ใช่ three-way match และไม่เกี่ยวกับการบันทึกใบกำกับผู้ขาย อยู่ภายใต้หน้าของโมดูล `purchase-order` ไม่ใช่หน้านี้

## สิ่งที่ยืนยันได้และยังไม่ยืนยัน

| ข้อกล่าวอ้าง | สถานะ |
| --- | --- |
| Tag โหมดการจัดสรร extra-cost (`manual` / `by_value` / `by_qty`) เก็บบน `tb_extra_cost` | **ยืนยันแล้ว** — Prisma enum จริง `enum_allocate_extra_cost_type` (สามค่าเท่านั้น; ไม่มี `by_weight` / `by_volume`) frontend เสนอ `by_qty` และ `by_value` (`grn-extra-cost-fields.tsx:201-202`) |
| จำนวนเงิน extra-cost ถูกแบ่งข้ามบรรทัด GRN จริงและป้อนเข้าสู่การคำนวณ cost layer แบบ FIFO / average | **ยืนยันแล้วว่าใช้งานจริงตั้งแต่ 2026-09-10** (`f8cd9f0d9`) `allocateExtraCost()` (`good-received-note.extra-cost.ts:40-61`) แบ่ง `Σ tb_extra_cost_detail.amount` ไปยังบรรทัดที่นำสต๊อกเข้าคลัง — `by_qty` = ส่วนเท่ากัน, `by_value` = ถ่วงตาม `received_base_qty + foc_base_qty`, `manual` = ไม่มี — ตอนโพสต์; ส่วนแบ่งถูกบวกเข้า landed cost ของบรรทัดและเก็บต่อ cost layer เป็น `extra_cost_amount` (`20260910130000_add_cost_layer_extra_cost`) ยังไม่มี UI จัดสรรต่อบรรทัดและไม่มีตารางการจัดสรรที่เก็บถาวร |
| Three-way match (PO ↔ GRN ↔ ใบกำกับผู้ขาย) | **ยังไม่ implement** ไม่พบ invoice entity, หน้าจอบันทึก หรือ match algorithm |
| การ post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`) | **ยังไม่ implement** โมดูล GL มีอยู่แต่ไม่มีโค้ด GRN, inventory-transaction หรือ period-end ใดเรียกมัน (ผล grep ด้านบน) |
| ฟิลด์ `post_type` ที่แยก `ap` / `consignment` / `cash` | **ยืนยันแล้วว่าเป็นฟิลด์ schema**; **ยังไม่ยืนยันเป็นพฤติกรรม** — ไม่พบ logic แยกเงื่อนไขตามฟิลด์นี้ใน backend เลย |
| Finance Manager ปิดงวดพร้อม report aging ของ GRN Clearing | **ยังไม่ implement** ไม่พบฟีเจอร์ปิดงวดเฉพาะโมดูลนี้ |
| Finance Officer ในฐานะบทบาท workflow-stage แยกต่างหาก | **ยังไม่ implement** `enum_stage_role` ไม่มีค่า `finance` |

จนกว่าฟีเจอร์ใบกำกับ / AP จะถูกเชื่อมเข้ากับ GRN (โมดูล GL น่าจะเป็นจุดลงจอด — จับตาดูผู้เขียน `enum_gl_jv_source.ap` / `.inventory`) อย่าถือว่าข้อความ "three-way match", "AP posting", "GRN Clearing" หรือ "period-close sign-off" ที่ปรากฏในหน้าอื่นของโมดูลนี้เป็นพฤติกรรมจริง ในที่ที่ [02-business-rules.md](./02-business-rules.md) ยัง list `GRN_POST_006`–`GRN_POST_009` หรือ `GRN_XMOD_007` rule ID เหล่านั้นถูกทำเครื่องหมายไว้ที่นั่นว่า **ยังไม่ implement** — คงไว้เพียงเพื่อให้ cross-reference จากหน้าอื่นยัง resolve ไปยังคำอธิบายได้

## แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต 4 สถานะ; เหตุการณ์โพสต์คือ `saved → committed` (BU แบบ average โพสต์สต๊อกตอน save)
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — persona ที่การ commit โพสต์ inventory และเลื่อน PO; ไม่มีการส่งต่อปลายน้ำไปยัง persona Finance
- โมดูล GL (เอกสารบนหน้า wiki ของตัวเอง ไม่ใช่ที่นี่): `../carmen-turborepo-backend-v2/apps/micro-business/src/gl/`, gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports}/`
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — เป็นเจ้าของการแก้ไขฝั่ง vendor สำหรับ variance การรับ; การเจรจา credit note ใดๆ เกิดขึ้นนอกเอกสาร
- Sibling: [02-business-rules.md](./02-business-rules.md) §5 / §6 — ตาราง posting-rule ที่แก้ไขแล้ว (`GRN_POST_006`–`GRN_POST_009`, `GRN_XMOD_007` ทำเครื่องหมายว่ายังไม่ implement)
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — แหล่ง design เก่าสำหรับแนวคิด three-way-match / AP; ถือเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว
- เอกสารที่จริงและยืนยันแล้วที่เกี่ยวข้อง: [purchase-order/credit-note](/th/inventory/purchase-order/credit-note)
