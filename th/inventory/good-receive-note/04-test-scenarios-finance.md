---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Finance
description: เหตุผลที่ไม่มี test scenario แบบ three-way-match / AP-posting สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: '2026-09-23T01:30:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, finance, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Finance

> **At a Glance**
> **สถานะ:** หน้าแก้ไข — ไม่พบ persona Finance เฉพาะทาง, three-way match, หรือฟีเจอร์ AP-posting สำหรับ good-receive-note ในซอร์สปัจจุบัน

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้ list scenario ประมาณ 30 รายการ (FIN-HP-01 ถึง FIN-EDGE-06) ครอบคลุมการปรับ extra-cost allocation ก่อน AP, three-way match เทียบกับใบกำกับ vendor, การ post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`), การ post FX-adjustment, และการกระทบยอดปิดงวด ไม่มีสิ่งใดในนี้แมพกับซอร์สปัจจุบัน:

- **ตรวจซ้ำ 2026-09-22:** ยังไม่มี vendor-invoice entity, endpoint โพสต์ AP หรือ three-way match ตอนนี้มีโมดูล GL แล้ว (`apps/micro-business/src/gl/`) แต่ไม่มีโค้ด GRN, inventory-transaction หรือ period-end ใดเรียกมัน — `GlPostingService.post()` (`gl-posting.service.ts:293`) โพสต์เฉพาะ journal voucher ที่สร้างด้วยมือ จาก template หรือโดยเส้นทาง reversal / closing ของตัวเอง; `enum_gl_jv_source.ap` / `.inventory` ไม่มีผู้เขียน `routes/accounting` ของ frontend (AP invoice / payment, AR, JV) แสดงแถวที่ปั้นขึ้นจาก `routes/accounting/accounting-documents.ts`
- โมดูล backend ของ good-received-note มี lifecycle operation ห้าตัว (`save`, `commit`, `approve`, `reject`, `voidGrnById`) — ไม่มีตัวใดแตะ journal, ledger หรือ AP entity
- `enum_stage_role` ไม่มีสมาชิก `finance`
- Spec E2E ของ `501-grn.spec.ts` (76 case) ไม่มี describe block สำหรับการจับคู่ใบกำกับ, การ post AP หรือการปิดงวด; กลุ่ม "Financial Summary" (`TC-GRN-1300xx`) ใช้งานเพียงแท็บยอดรวมแบบอ่านอย่างเดียวบนหน้ารายละเอียด GRN โดยไม่มี assertion ที่ผูกกับ three-way match หรือ journal entry

> **ความครอบคลุมที่รันได้:** กลุ่ม `GRN — Extra Costs` (`TC-GRN-1000xx`) และ `GRN — Financial Summary` (`TC-GRN-1300xx`) ใน `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`; gap report `docs/test-cases/gaps/501-grn-core-gap.md` (ส่วน tax / discount) ไม่มี spec AP หรือ GL

| กลุ่ม scenario ที่เคยกล่าวอ้าง | ข้อสรุป |
| --- | --- |
| FIN-HP-01..03 (สลับโหมด extra-cost allocation ก่อน AP, คำนวณใหม่ `manual` / `by_value` / `by_qty` พร้อมโพสต์ GL delta) | **การจัดสรร** extra-cost **มีจริงแล้ว** (2026-09-10): `allocateExtraCost()` แบ่งยอดรวมตอนโพสต์ — `by_qty` ส่วนเท่ากัน, `by_value` ถ่วงตามปริมาณสต๊อก, `manual` ไม่มี — เข้า landed cost และ `tb_inventory_transaction_cost_layer.extra_cost_amount` ยังไม่มี GL delta ไม่มีการจัดสรรใหม่หลังโพสต์ (GRN ที่ committed ไม่ถูกโพสต์ซ้ำเลย) และไม่มีการกรอกด้วยมือต่อบรรทัด ให้ทดสอบจากฝั่ง Receiver: [04-test-scenarios](./04-test-scenarios.md) Scenario 5, [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) RCV-EDGE-02 |
| FIN-HP-04..06 (การจับคู่สะอาด, การจับคู่บางส่วน, price-within-tolerance auto-pass) | ไม่พบโค้ดบันทึกใบกำกับ, การ post AP หรือ match algorithm ใดในซอร์สปัจจุบัน |
| FIN-HP-07 (การปรับ FX บนการเคลื่อนไหวของอัตราระหว่าง snapshot ของ GRN กับวันที่ post AP) | ไม่มีแนวคิดวันที่ post AP อยู่เลย — ไม่มีขั้นตอน post AP เลย |
| FIN-HP-08 (การกระทบยอดปิดงวดและ sign-off) | ไม่พบฟีเจอร์ปิดงวดเฉพาะโมดูลนี้ |
| FIN-PERM-01..07, FIN-VAL-01..09, FIN-EDGE-01..06 | ทั้งหมดสร้างขึ้นบนพื้นฐาน three-way-match / AP-posting ที่ยังไม่ยืนยันเดียวกัน; ไม่ได้สร้างใหม่ |

## สิ่งที่ควรทดสอบแทน

การเก็บ extra-cost (`tb_extra_cost` / `tb_extra_cost_detail`, tag โหมดสามแบบของ `allocate_extra_cost_type`, UI กรอกจำนวนรวมต่อประเภทของ frontend ที่เสนอ `by_qty` / `by_value`) **และการจัดสรรเข้า landed cost ตอนโพสต์** มีจริงและทดสอบได้ — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) และ [04-test-scenarios](./04-test-scenarios.md) Scenario 5 สำหรับ scenario ที่ใช้งานมันในฐานะส่วนหนึ่งของ flow commit ของ Receiver (สังเกตได้บนแท็บ Stock Movement และใน `tb_inventory_transaction_cost_layer.extra_cost_amount`) และ describe block `GRN — Extra Costs` ของ `501-grn.spec.ts` (`TC-GRN-1000xx`) สำหรับความครอบคลุม E2E ทางการ หมายเหตุว่าความหมายของโหมดกลับด้านกับชื่อ (`by_value` ถ่วงตามปริมาณ; `by_qty` แบ่งเท่ากัน) — [02-business-rules.md](./02-business-rules.md) `GRN_CALC_010` / `GRN_CALC_011`

## แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — ตาราง scenario ข้าม persona ที่แก้ไขแล้ว
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — การแก้ไขฉบับเต็มและการค้นหาที่ดำเนินการ
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — การกรอก extra-cost ในฐานะส่วนหนึ่งของ flow save ของ Receiver
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — describe block `GRN — Extra Costs` (`TC-GRN-1000xx`) และ `GRN — Financial Summary` (`TC-GRN-1300xx`) เป็นความครอบคลุมจริงที่ใกล้เคียงที่สุด; ไม่มีตัวใดทดสอบการจับคู่ใบกำกับหรือการ post AP
