---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Finance
description: เหตุผลที่ไม่มี test scenario แบบ three-way-match / AP-posting สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, finance, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Finance

> **At a Glance**
> **สถานะ:** หน้าแก้ไข — ไม่พบ persona Finance เฉพาะทาง, three-way match, หรือฟีเจอร์ AP-posting สำหรับ good-receive-note ในซอร์สปัจจุบัน

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้ list scenario ประมาณ 30 รายการ (FIN-HP-01 ถึง FIN-EDGE-06) ครอบคลุมการปรับ extra-cost allocation ก่อน AP, three-way match เทียบกับใบกำกับ vendor, การ post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`), การ post FX-adjustment, และการกระทบยอดปิดงวด ไม่มีสิ่งใดในนี้แมพกับซอร์สปัจจุบัน:

- การค้นหาทั่ว repo ของ `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `journal`, `ledger`, `three-way`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` ให้ผลศูนย์รายการ
- โมดูล backend ของ good-received-note มี lifecycle operation เพียงสี่ตัว (`save`, `commit`, `reject`, `voidGrnById`) — ไม่มีตัวใดแตะ journal, ledger หรือ entity ของ AP
- `enum_stage_role` ไม่มีสมาชิก `finance`
- Spec E2E ของ `501-grn.spec.ts` ไม่มี describe block สำหรับการจับคู่ใบกำกับ, การ post AP หรือการปิดงวด; กลุ่ม "Financial Summary" (`TC-GRN-1300xx`) เพียงทดสอบ tab ยอดรวมแบบ read-only บนหน้า detail ของ GRN โดยไม่มี assertion ที่ผูกกับ three-way match หรือ journal entry

| กลุ่ม scenario ที่เคยกล่าวอ้าง | ข้อสรุป |
| --- | --- |
| FIN-HP-01..03 (สลับโหมด extra-cost allocation ก่อน AP, คำนวณใหม่ `manual` / `by_value` / `by_qty` พร้อม post GL delta) | การเก็บ extra-cost เป็นเรื่องจริง (`tb_extra_cost`, enum สามโหมด) แต่ไม่พบโค้ดการแบ่ง allocation หรือ GL delta ใดๆ — ดู [03-user-flow-finance.md](./03-user-flow-finance.md) |
| FIN-HP-04..06 (การจับคู่สะอาด, การจับคู่บางส่วน, price-within-tolerance auto-pass) | ไม่พบโค้ดบันทึกใบกำกับ, การ post AP หรือ match algorithm ใดในซอร์สปัจจุบัน |
| FIN-HP-07 (การปรับ FX บนการเคลื่อนไหวของอัตราระหว่าง snapshot ของ GRN กับวันที่ post AP) | ไม่มีแนวคิดวันที่ post AP อยู่เลย — ไม่มีขั้นตอน post AP เลย |
| FIN-HP-08 (การกระทบยอดปิดงวดและ sign-off) | ไม่พบฟีเจอร์ปิดงวดเฉพาะโมดูลนี้ |
| FIN-PERM-01..07, FIN-VAL-01..09, FIN-EDGE-01..06 | ทั้งหมดสร้างขึ้นบนพื้นฐาน three-way-match / AP-posting ที่ยังไม่ยืนยันเดียวกัน; ไม่ได้สร้างใหม่ |

## สิ่งที่ควรทดสอบแทน

การเก็บ extra-cost (`tb_extra_cost` / `tb_extra_cost_detail`, tag โหมดสามแบบของ `allocate_extra_cost_type`, และ UI กรอกจำนวนเงินรวมต่อประเภทฝั่ง frontend) เป็นเรื่องจริงและทดสอบได้ — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) สำหรับ scenario ที่ทดสอบมันในฐานะส่วนหนึ่งของ flow save ของ Receiver และ describe block `GRN — Extra Costs` (`TC-GRN-1000xx`) ของ `501-grn.spec.ts` สำหรับความครอบคลุม E2E ทางการ

## แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — ตาราง scenario ข้าม persona ที่แก้ไขแล้ว
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — การแก้ไขฉบับเต็มและการค้นหาที่ดำเนินการ
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — การกรอก extra-cost ในฐานะส่วนหนึ่งของ flow save ของ Receiver
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — describe block `GRN — Extra Costs` (`TC-GRN-1000xx`) และ `GRN — Financial Summary` (`TC-GRN-1300xx`) เป็นความครอบคลุมจริงที่ใกล้เคียงที่สุด; ไม่มีตัวใดทดสอบการจับคู่ใบกำกับหรือการ post AP
