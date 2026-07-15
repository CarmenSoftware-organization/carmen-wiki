---
title: ใบรับสินค้า (Goods Receive Note) — User Flow — Finance
description: เหตุผลที่ไม่พบ persona Finance แบบ three-way-match / AP-posting สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้จริง
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, finance, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — User Flow — Finance

> **At a Glance**
> **หน้านี้เอกสารอะไร:** เหตุผลที่ flow "Finance" เดิม (review การจัดสรร extra-cost, three-way match, AP posting, ปิดงวด) ไม่ตรงกับซอร์สปัจจุบัน และสิ่งที่ยืนยันได้จริง

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้บรรยาย Finance Officer / AP Clerk ที่รัน three-way match (PO ↔ GRN ↔ ใบกำกับผู้ขาย) post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`) และ Finance Manager ที่ปิดงวดพร้อม aging ของ GRN Clearing ไม่มีสิ่งใดในนี้ที่พบในซอร์สปัจจุบัน:
>
> - การค้นหาทั่ว repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `journal`, `ledger`, `accounts_payable`, `three-way`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` ให้ผล **ศูนย์รายการที่ตรงกัน** ไม่มีหน้าจอบันทึกใบกำกับผู้ขาย ไม่มี AP-posting endpoint และไม่มี match algorithm ที่ใดในโค้ดปัจจุบัน
> - `enum_stage_role` (enum บทบาท stage ของ workflow ที่ใช้ร่วมกับ PR / PO / GRN) ไม่มีสมาชิก `finance`
> - โมดูล backend ของ good-received-note (`good-received-note.service.ts`, `good-received-note.logic.ts`) มี lifecycle operation เพียงสี่ตัว — `save`, `commit`, `reject`, `voidGrnById` — ไม่มีตัวใดแตะ journal, ledger หรือ entity ของ AP เลย
> - ฟีเจอร์เดียวที่ **จริง** และเกี่ยวข้องกับ AP ในผลิตภัณฑ์คือ **Credit Note** (`tb_credit_note` ตาราง Prisma จริงที่ยืนยันแล้ว พร้อม FK จริงกลับไปยัง `tb_good_received_note`) — เอกสารที่ post debit memo ฝั่ง AP เทียบกับ GRN ก่อนหน้า เป็นเอกสารจริงและแยกต่างหาก ไม่ใช่ three-way match และไม่เกี่ยวข้องกับการบันทึกใบกำกับผู้ขาย อยู่ในหน้าของโมดูล `purchase-order` ไม่ใช่หน้านี้

## สิ่งที่ยืนยันได้และยังไม่ยืนยัน

| ข้อกล่าวอ้าง | สถานะ |
| --- | --- |
| Tag โหมดการจัดสรร extra-cost (`manual` / `by_value` / `by_qty`) เก็บบน `tb_extra_cost` | **ยืนยันแล้ว** — enum Prisma จริง `enum_allocate_extra_cost_type` (มีเพียงสามค่า; ไม่มี `by_weight` / `by_volume`) |
| จำนวนเงิน extra-cost ถูกแบ่งข้ามบรรทัด GRN จริงและป้อนเข้าสู่การคำนวณ cost layer แบบ FIFO / average | **ยังไม่ยืนยัน** panel extra-cost ฝั่ง frontend (`grn-extra-cost-fields.tsx`) รับเพียงจำนวนเงินรวมต่อประเภท extra cost โดยมีโหมดเป็นเพียง label — ไม่มี UI แจกแจงต่อบรรทัด โค้ดสร้าง cost layer ฝั่ง backend (`inventory-transaction.service.ts`) อ่านเฉพาะ `base_net_amount` ของ detail_item เอง ไม่พบ term extra-cost ในการคำนวณนั้น |
| Three-way match (PO ↔ GRN ↔ ใบกำกับผู้ขาย) | **ยังไม่ implement** ไม่พบ invoice entity, หน้าจอบันทึก หรือ match algorithm |
| การ post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`) | **ยังไม่ implement** ไม่พบโค้ด journal / ledger ใดๆ ในโมดูลนี้ |
| ฟิลด์ `post_type` ที่แยก `ap` / `consignment` / `cash` | **ยืนยันแล้วว่าเป็นฟิลด์ schema**; **ยังไม่ยืนยันเป็นพฤติกรรม** — ไม่พบ logic แยกเงื่อนไขตามฟิลด์นี้ใน backend เลย |
| Finance Manager ปิดงวดพร้อม report aging ของ GRN Clearing | **ยังไม่ implement** ไม่พบฟีเจอร์ปิดงวดเฉพาะโมดูลนี้ |
| Finance Officer ในฐานะบทบาท workflow-stage แยกต่างหาก | **ยังไม่ implement** `enum_stage_role` ไม่มีค่า `finance` |

จนกว่าจะยืนยันฟีเจอร์การบันทึกใบกำกับ/AP ว่ามีอยู่จริง (ใน repo นี้หรือ backend service พี่น้องที่ยังไม่ได้สำรวจ) อย่าถือว่าข้อความ "three-way match", "AP posting", "GRN Clearing" หรือ "period-close sign-off" ที่ปรากฏในหน้าอื่นของโมดูลนี้เป็นพฤติกรรมจริง เมื่อ [02-business-rules.md](./02-business-rules.md) ยังคงรายการ `GRN_POST_006`–`GRN_POST_009` หรือ `GRN_XMOD_007` อยู่ rule ID เหล่านั้นถูกทำเครื่องหมายไว้ว่า **ยังไม่ implement** แทนที่จะบรรยายเป็นกฎที่ใช้งานได้ — เก็บไว้เพียงเพื่อให้ cross-reference จากหน้าอื่นยัง resolve ไปยังคำอธิบายได้

## แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิตทางการ 4 สถานะที่แก้ไขแล้ว; เหตุการณ์ posting คือ `draft → saved` ไม่ใช่ commit
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — persona ที่การ save โพสต์ inventory และเลื่อน PO; ไม่พบ handoff ปลายทางไปยัง persona Finance ที่ยืนยันได้
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — เป็นเจ้าของการแก้ไขฝั่ง vendor สำหรับ variance การรับ; การเจรจา credit note ใดๆ เกิดขึ้นนอกเอกสาร
- Sibling: [02-business-rules.md](./02-business-rules.md) §5 / §6 — ตาราง posting-rule ที่แก้ไขแล้ว (`GRN_POST_006`–`GRN_POST_009`, `GRN_XMOD_007` ทำเครื่องหมายว่ายังไม่ implement)
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — แหล่ง design เก่าสำหรับแนวคิด three-way-match / AP; ถือเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว
- เอกสารที่จริงและยืนยันแล้วที่เกี่ยวข้อง: [purchase-order/credit-note](/th/inventory/purchase-order/credit-note)
