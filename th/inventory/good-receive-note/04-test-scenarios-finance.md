---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Finance
description: test scenario ของ Finance อยู่ที่ใดนอกโมดูล GRN, สิ่งที่โมดูล AP Invoice ใน backend ครอบคลุมแล้ว และสิ่งที่ควรทดสอบฝั่ง GRN ของลิงก์
published: true
date: '2026-10-27T15:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, finance, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Finance

> **At a Glance**
> **สถานะ:** หน้าสถานะ — โมดูล GRN ไม่มี persona หรือหน้าจอ Finance โดยเฉพาะ ตั้งแต่ 2026-10 โมดูล AP Invoice ใน backend จับคู่บรรทัด GRN ที่ committed และโพสต์เข้า GL ([AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn)); การทดสอบของมันอยู่กับโมดูลนั้น ผลฝั่ง GRN ที่ควรทดสอบแสดงไว้ด้านล่าง

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้ list scenario ราว 30 รายการ (FIN-HP-01 ถึง FIN-EDGE-06) ครอบคลุมการปรับการจัดสรร extra-cost ก่อน AP, three-way match กับใบกำกับผู้ขาย, การ post journal ฝั่ง AP (`Dr GRN Clearing / Cr AP-Trade`), การ post ปรับ FX และการกระทบยอดปิดงวด ไม่มีสิ่งใดในนี้ map กับซอร์สปัจจุบัน:

- **ตรวจซ้ำ 2026-10-27:** ตอนนี้ backend มีโมดูล AP Invoice (`apps/micro-business/src/ap/ap-invoice`, `ap-payment`); การโพสต์ AP เขียน GL journal ด้วย `source = ap` (`ap-invoice.posting.ts:291`) ไม่มีโค้ด GRN, inventory-transaction หรือ period-end ใดเรียกโมดูล GL และ `enum_gl_jv_source.inventory` ไม่มีผู้เขียน หน้าจอ `routes/accounting` ของ frontend (AP invoice / payment, AR, JV) ทำงานบน mock ในเบราว์เซอร์ (`ap-mock-repository.ts`, `documentsFor()`) และไม่เรียก API จึงไม่มีเส้นทาง UI ให้ทดสอบ
- โมดูล backend ของ good-received-note มี lifecycle operation ห้าตัว (`save`, `commit`, `approve`, `reject`, `voidGrnById`) — ไม่มีตัวใดแตะ journal, ledger หรือ AP entity
- `enum_stage_role` ไม่มีสมาชิก `finance`
- spec E2E `501-grn.spec.ts` ไม่มี describe block สำหรับการจับคู่ใบกำกับ การโพสต์ AP หรือการปิดงวด (และไม่มี AP spec ใน `../carmen-frontend-e2e/tests`); กลุ่ม "Financial Summary" (`TC-GRN-1300xx`) ทดสอบเพียงแท็บยอดรวมแบบอ่านอย่างเดียวบนหน้ารายละเอียด GRN โดยไม่มี assertion ที่ผูกกับ three-way match หรือ journal entry

> **ความครอบคลุมที่รันได้:** `../carmen-frontend-e2e/tests/501-grn.spec.ts` กลุ่ม `GRN — Extra Costs` (`TC-GRN-1000xx`) และ `GRN — Financial Summary` (`TC-GRN-1300xx`); gap report `docs/test-cases/gaps/501-grn-core-gap.md` (ส่วน tax / discount) ไม่มี AP หรือ GL spec; `502-grn-doc-flow.spec.ts` แบบ opt-in ใหม่ครอบคลุมเพียง draft/edit/delete ของ GRN แบบ manual และ saved-on-AVG

| กลุ่ม scenario ที่เคยอ้าง | ข้อค้นพบ |
| --- | --- |
| FIN-HP-01..03 (สลับการจัดสรร extra-cost ก่อน AP, คำนวณใหม่แบบ `manual` / `by_value` / `by_qty` พร้อมโพสต์ delta ลง GL) | ตอนนี้ **การจัดสรร extra-cost ทำงานจริง** (2026-09-10): `allocateExtraCost()` แบ่งยอดรวมตอนโพสต์ — `by_qty` ส่วนเท่ากัน, `by_value` ถ่วงตามปริมาณสต๊อก, `manual` ไม่แบ่ง — เข้า landed cost และ `tb_inventory_transaction_cost_layer.extra_cost_amount` ยังไม่มี GL delta, ไม่มีการจัดสรรใหม่หลังโพสต์ (GRN ที่ committed ไม่ถูกโพสต์ซ้ำ) และไม่มีการกรอก manual ต่อบรรทัด ให้ทดสอบจากฝั่ง Receiver: [04-test-scenarios](./04-test-scenarios.md) Scenario 5, [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) RCV-EDGE-02 |
| FIN-HP-04..06 (จับคู่สะอาด, จับคู่บางส่วน, ราคาอยู่ในช่วง tolerance ผ่านอัตโนมัติ) | **เฉพาะ backend ขอบเขตโมดูล AP** มีการจับคู่ปริมาณ (`matched_qty` ≤ `received_qty`, `AP_GRN_OVER_MATCHED`; `variance_amount` เก็บต่อ source) แต่ไม่มี price-tolerance auto-pass ให้ทดสอบ API จากฝั่ง AP; การตรวจฝั่ง GRN อยู่ในตารางด้านล่าง |
| FIN-HP-07 (ปรับ FX เมื่ออัตราเคลื่อนระหว่าง snapshot ของ GRN กับวันโพสต์ AP) | AP invoice มี `exchange_rate` และคอลัมน์ realized-FX ของตัวเอง (`tb_ap_invoice_reference.realized_fx_amount`); ขอบเขตโมดูล AP ไม่ใช่ scenario ของ GRN |
| FIN-HP-08 (กระทบยอดปิดงวดและเซ็นรับรอง) | ไม่พบฟีเจอร์ปิดงวดเฉพาะโมดูลนี้ |
| FIN-PERM-01..07, FIN-VAL-01..09, FIN-EDGE-01..06 | สร้างบนดีไซน์ three-way-match เดิม; ไม่ได้สร้างใหม่ scenario ฝั่ง GRN ใหม่แสดงไว้ด้านล่าง |

## สิ่งที่ควรทดสอบแทน

การเก็บ extra-cost (`tb_extra_cost` / `tb_extra_cost_detail`, tag `allocate_extra_cost_type` สามโหมด, UI กรอกจำนวนเงินแบบเหมาต่อประเภทของ frontend ที่เสนอ `by_qty` / `by_value`) **และการจัดสรรเข้า landed cost ตอนโพสต์** ใช้งานจริงและทดสอบได้ — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) และ [04-test-scenarios](./04-test-scenarios.md) Scenario 5 สำหรับ scenario ที่ทดสอบเป็นส่วนหนึ่งของ flow commit ของ Receiver (สังเกตได้บนแท็บ Stock Movement และใน `tb_inventory_transaction_cost_layer.extra_cost_amount`) และ describe block `GRN — Extra Costs` ของ `501-grn.spec.ts` (`TC-GRN-1000xx`) สำหรับ E2E หลัก หมายเหตุว่าความหมายของโหมดสวนทางกับชื่อ (`by_value` ถ่วงตามปริมาณ; `by_qty` แบ่งเท่ากัน) — [02-business-rules.md](./02-business-rules.md) `GRN_CALC_010` / `GRN_CALC_011`

### Scenario ฝั่ง GRN ของลิงก์ AP (เพิ่ม 2026-10-27)

ระดับ API เท่านั้น — ยังไม่มี UI ที่สร้าง AP invoice ไม่มีข้อใดถูกครอบคลุมโดย repo E2E

| ID | Scenario | ผลที่คาดหวัง |
| --- | --- | --- |
| FIN-AP-01 | `PATCH …/good-received-notes/:id` บน GRN ที่ `committed` ที่ไม่มี AP invoice โดยเปลี่ยน `invoice_no` | รับ; การเปลี่ยนถูกเก็บและ `doc_version` เพิ่ม |
| FIN-AP-02 | `PATCH` เดียวกันโดยเปลี่ยนบรรทัดหรือ `grn_date` | `GRN_COMMITTED_HEADER_ONLY` (400) ระบุฟิลด์ที่ถูกปฏิเสธ |
| FIN-AP-03 | สร้างบรรทัด AP invoice ที่มาจาก detail item ของ GRN นั้น แล้วทำซ้ำ FIN-AP-01 | `GRN_AP_LINKED_NOT_EDITABLE` (400) พร้อมเลขเอกสาร AP; `GET …/good-received-notes/:id` แสดงใน `ap_invoices`; การ void AP invoice (`void`) ปลดล็อก |
| FIN-AP-04 | บรรทัด AP ที่มาจาก GRN สถานะ `saved` หรือจาก GRN ที่ `committed` ที่ `post_type = cash` / `consignment` | `AP_GRN_NOT_COMMITTED` ตอน submit/post |
| FIN-AP-05 | เอกสาร AP สองใบแต่ละใบจับคู่ 60% ของ `received_qty` ของรายการ GRN เดียว | ใบที่สองถูกปฏิเสธด้วย `AP_GRN_OVER_MATCHED` |
| FIN-AP-06 | `GET /api/ext/v1/ap-invoices` สำหรับ BU | แสดง GRN ที่ committed (ไม่ใช่ draft/saved); GRN ที่ `post_type = consignment` ไม่ปรากฏ |

## แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — ตาราง scenario ข้าม persona ที่แก้ไขแล้ว
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — คำอธิบายที่ละเอียดกว่าและการค้นหาที่รัน
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — การกรอก extra-cost เป็นส่วนหนึ่งของ flow save ของ Receiver
- E2E spec: `../carmen-frontend-e2e/tests/501-grn.spec.ts` — describe block `GRN — Extra Costs` (`TC-GRN-1000xx`) และ `GRN — Financial Summary` (`TC-GRN-1300xx`) คือความครอบคลุมจริงที่ใกล้ที่สุด; ไม่มีข้อใดทดสอบการจับคู่ใบกำกับหรือการโพสต์ AP
