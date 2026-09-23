---
title: ใบสั่งซื้อ (Purchase Order) — Test Scenarios — Vendor
description: Test cases ของ Vendor (happy path, edge cases) สำหรับ purchase-order ฝ่ายภายนอก — ไม่มี in-system permission scenarios; ไม่มีฟีเจอร์ invoice/AP-matching ที่ยืนยันได้
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-order, test-scenarios, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — Test Scenarios — Vendor

> **At a Glance**
> **Persona:** Vendor (ฝ่ายภายนอก — ไม่มี Carmen login) &nbsp;·&nbsp; **Module:** [purchase-order](/th/inventory/purchase-order) &nbsp;·&nbsp; **Scenarios:** ~8
> **Categories:** Happy Path &nbsp;·&nbsp; Permission (N/A) &nbsp;·&nbsp; Edge Case
> **E2E coverage:** ไม่มี vendor spec เฉพาะ (ไม่มี Carmen login); vendor-driven events exercise ทางอ้อมผ่าน `tests/401-po.spec.ts` (TC-PO-030001..030004 send-to-vendor, TC-PO-340001..340003 GRN-sync) ใน `../carmen-inventory-frontend-e2e/`

> **Executable coverage (2026-09-22):** catalog `../carmen-inventory-frontend-e2e/docs/user-stories/401-po.md` (60 case; gap `docs/test-cases/gaps/401-po-create-flows-gap.md`, 29) และ `docs/user-stories/402-po-purchaser-journey.md` TC-PO-060501/060502 ("Send to Vendor" — ตอนนี้คือ **Send Email**, `approved → sent_or_print`) ยังไม่มี spec ใด exercise `POST .../purchase-orders/:id/send-email` หรือ `mark-sent` แบบ end-to-end; เส้นทางอีเมล verify ได้ผ่าน `tb_activity` (`email_sent`) และการ flip status เท่านั้น scenario ด้านล่างแก้ไขให้ตรง source HEAD

> ⚠️ **แก้ไขในรอบนี้** เวอร์ชันก่อนหน้าของหน้านี้มี happy path เรื่อง invoice-issuance (VND-HP-05) และ Validation section เต็มรูปแบบ (VND-VAL-01 ถึง VND-VAL-05) ที่สร้างขึ้นทั้งหมดรอบฟีเจอร์ three-way-match / AP-invoice ไม่พบ invoice-capture screen, AP-posting endpoint, หรือ match algorithm ใด ๆ ในซอร์สโค้ดปัจจุบัน (ดู [03-user-flow-finance.md](./03-user-flow-finance.md) สำหรับการค้นที่รันจริง) — scenarios เหล่านั้นถูกตัดออก edge cases "vendor declines / voids" ก็ถูกแก้ไขด้วยเช่นกัน: ไม่มี path จาก `sent` ไปยัง `voided` ในซอร์สโค้ดปัจจุบัน การจบ `sent` PO ใช้ **Cancel** หรือ **Close** ซึ่งทั้งคู่จบที่ `closed`

หน้านี้ capture test scenarios ที่ exercise การ interact ของ persona **Vendor** กับโมดูล `purchase-order` Vendor เป็น **ฝ่ายภายนอกที่ไม่มี Carmen system login** ([03-user-flow-vendor.md](./03-user-flow-vendor.md) Section 1) — system-side effect ที่ยืนยันได้ของ vendor action คือ GRN posting ของ **Receiver** ซึ่งขับเคลื่อน `PO_POST_006` / `PO_POST_007` ยังไม่ยืนยันว่า vendor acknowledgement ถูกบันทึกไว้ที่ใดในซอร์สโค้ดปัจจุบันหรือไม่ เนื่องจาก vendor ไม่มี in-system role ไฟล์นี้จึงไม่มี Permission / Authorization section ที่มีความหมาย และสั้นกว่าไฟล์ scenario ของ persona อื่น

## 1. Happy Path

| # | Scenario | เงื่อนไขก่อน | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| VND-HP-01 | ได้รับ PO ทางอีเมล (พร้อม PDF) | PO ที่ `po_status = approved` หลัง final-stage approve call (`approval_date` ตั้งแล้ว); BU email profile ที่ enable; Purchaser เปิด **Send Email** | 1. Purchaser ส่ง `POST .../purchase-orders/:id/send-email` `{ profile_id, to: [vendor@…], subject, body, attach_pdf: true }` (subject / body จาก PO template ที่ seed ไว้) 2. Mailbox ของ vendor ได้รับข้อความพร้อม PDF ที่ micro-report render (FastReport `POST /api/Report/Export/Pdf`) อ้างอิง `po_no`, บรรทัด, qty, ราคา, delivery date, delivery point, และเงื่อนไขการชำระเงิน | `{ sent: true }`; `po_status: approved → sent_or_print` (`markPoAsSent`); `tb_activity` `email_sent` พร้อมผู้รับ **ยังไม่ยืนยัน:** Carmen บันทึก acknowledgement ของการรับหรือไม่ **แก้ไข 2026-09-22:** ไม่มี EDI feed หรือ vendor portal และการส่งไม่ได้เป็นส่วนหนึ่งของ approve call อีกต่อไป |
| VND-HP-01b | ได้รับ PO บนกระดาษ | PO ที่ `po_status = approved`; Purchaser พิมพ์ (`GET .../purchase-orders/:id/print`) และส่งมอบ | 1. Purchaser เรียก `POST .../purchase-orders/:id/mark-sent` (API เท่านั้นในวันนี้) | `po_status: approved → sent_or_print`; `tb_activity` "Marked as sent to vendor" |
| VND-HP-02 | จัดส่งเต็มจำนวนตาม delivery date ที่ตกลงไว้ (Receiver บันทึก GRN ที่ match) | PO ที่ `po_status = sent_or_print` (หรือยัง `approved` — การรับของไม่รออีเมล) พร้อมบรรทัด `L1 : order_qty = 10`, `received_qty = 0`, `cancelled_qty = 0`; vendor จัดส่ง 10 หน่วยตาม `delivery_date` ที่ตกลงไปยัง `delivery_point` ของ header | 1. Logistics partner ของ vendor จัดส่ง 10 หน่วยเต็มไปยัง receiving location พร้อม delivery note ที่อ้างอิง `po_no` 2. Receiver เปิด PO ใน [good-receive-note](/th/inventory/good-receive-note) และ post GRN qty 10 กับ `L1` | GRN posting flip `po_status` เป็น `completed` ตาม `PO_POST_007` เพราะ `received_qty + cancelled_qty = order_qty` บนทุกบรรทัด (`L1`: `10 + 0 = 10`); `tb_purchase_order_detail.received_qty = 10` บน `L1`; inventory on-hand เพิ่มขึ้นในโมดูล [inventory](/th/inventory/inventory) ตาม `PO_XMOD_008`; บรรทัด PO แสดงเลข GRN |
| VND-HP-03 | จัดส่งบางส่วนแล้วส่งครั้งที่สอง (Receiver บันทึก partial แล้ว full) | PO ที่ `po_status = sent_or_print` พร้อม `L1 : order_qty = 10`; vendor สามารถส่งได้ 6 วันนี้และ 4 สัปดาห์หน้า | 1. Vendor ส่ง 6 หน่วยพร้อม delivery note ที่ mark ว่า partial 2. Receiver post GRN #1 qty 6 กับ `L1` 3. Vendor ส่ง 4 หน่วยที่เหลือหนึ่งสัปดาห์ต่อมา 4. Receiver post GRN #2 qty 4 กับ `L1` | หลัง GRN #1: `received_qty = 6`, `po_status` flip `sent_or_print → partial` ตาม `PO_POST_006` เพราะ `received_qty < order_qty − cancelled_qty` บน `L1`; หลัง GRN #2: `received_qty = 10`, `po_status` flip `partial → completed` ตาม `PO_POST_007` เพราะทุกบรรทัดพอใจ `received_qty + cancelled_qty = order_qty` |
| VND-HP-04 | Vendor ส่งของแถมมาด้วย | บรรทัด PO `L1` ที่ bridge `pr_detail_foc_qty = 2`; vendor ส่ง 10 จ่ายเงิน + 2 ฟรี | Receiver post GRN ด้วย `received_qty = 10` และ FOC ที่รับ `2` | bridge `foc_received_qty = 2`; stock ขึ้น 12; บรรทัด PO แสดง `2` ใต้ FOC / GRN |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| VND-PERM-01 | Vendor เป็นฝ่ายภายนอกที่ไม่มี system login; in-system permissions ไม่เกี่ยวข้อง | N/A — ไม่มี Carmen login สำหรับ vendor และไม่มี UI surface ให้ทดสอบ ทุก effect ของ vendor action ที่ไปถึงระบบเกิดผ่าน GRN posting ของ Receiver (`PO_POST_006` / `PO_POST_007`) ในกรณีที่มี vendor portal configure ไว้ มันเป็นเรื่องแยกจาก RBAC matrix ของโมดูล PO (`PO_AUTH_001`–`PO_AUTH_011`) |

## 3. Edge Cases

| # | Scenario | เงื่อนไข | Expected |
| - | -------- | --------- | -------- |
| VND-EDGE-01 | Vendor ไม่สามารถ fulfil PO ได้อีกต่อไปหลัง transmission | PO ที่ `po_status = sent_or_print`; stock-out / price-disagreement ทำให้ vendor ไม่สามารถส่งได้ | PO จบลงผ่าน **Cancel** (`{draft, in_progress, approved, sent_or_print} → closed`) หรือ **Close** (`{in_progress, approved, sent_or_print, partial} → closed`) — ทั้งคู่เขียนส่วนที่เหลือลง `cancelled_qty` ไม่มี transition จาก `sent_or_print` ไปยัง `voided` ในซอร์สโค้ดปัจจุบัน |
| VND-EDGE-04 | Mailbox ของ vendor ปฏิเสธข้อความ | PO ที่ `po_status = approved`; `send-email` คืน `{ sent: false, rejected: ['vendor@…'] }` | PO ยังคง `approved`; `tb_activity` `email_sent` บันทึกความพยายามที่ล้มเหลว; Purchaser แก้ที่อยู่แล้วส่งใหม่ หรือพิมพ์แล้วใช้ `mark-sent` vendor ยังไม่เห็นใบสั่งจนกว่าอย่างใดอย่างหนึ่งจะสำเร็จ |
| VND-EDGE-02 | Vendor จัดส่งบางส่วนผิดสินค้า (Receiver บันทึก discrepancy) | PO line `L1 : order_qty = 10` (product `P1`); vendor จัดส่ง 8 หน่วยของ `P1` และ 2 หน่วยของ product ที่ไม่เกี่ยวข้อง `P_wrong` (substitution / packing error) | Receiver เปิด GRN กับ `L1` และบันทึก 8 ที่ได้รับกับ `L1` (flip `po_status → partial` ตาม `PO_POST_006`) บวก variance comment ใน `tb_purchase_order_comment` ที่อ้างอิง `P_wrong` การจัดส่งสินค้าผิด **ไม่** post เข้า inventory ภายใต้ `L1`; write-off ที่ตกลงกันของ 2 หน่วยที่เหลือของ `P1` เขียนลง `cancelled_qty` บน `L1` ผ่าน **Close** |
| VND-EDGE-03 | Vendor เลิกกิจการกลางคัน PO | PO ที่ `po_status = partial` พร้อม `received_qty = 6` บน `L1 : order_qty = 10`; vendor หยุดดำเนินธุรกิจก่อนส่งส่วนที่เหลือ 4 หน่วย | **Close** (`partial → closed`, `PO_AUTH_008`, `PO_POST_011`) เขียน 4 หน่วยที่เหลือลง `cancelled_qty`; 6 หน่วยที่รับแล้วยังคงอยู่ใน `tb_purchase_order_detail.received_qty` **แก้ไขในรอบนี้:** เวอร์ชันก่อนหน้าของ scenario นี้ใช้ "Void" (`partial → voided`) ที่สงวนสำหรับ Procurement Manager เท่านั้น; ไม่มี code path ใดไปถึง `voided` จาก `partial` — มีเฉพาะ Close (→ `closed`) เท่านั้นที่ใช้ได้จาก status นี้ |

## 4. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoffs ที่เกี่ยวข้องกับ action ของ vendor แต่ขับเคลื่อนโดย persona ภายใน: `X-PO-01` (happy path เต็มจาก PR ผ่าน transmission ถึง receipt), `X-PO-05` (amendment cycle บน Sent PO)
- User flow: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — แหล่งสำหรับ Section 1 ข้างต้น; documents สิ่งที่ยืนยันได้ vs. ยังไม่ยืนยันเกี่ยวกับ vendor-side events
- Sibling: [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) — persona ภายในที่ transmit PO และรัน amendment loop แทน vendor
- Sibling: [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) — persona ภายในที่มี Close authority ใช้ใน VND-EDGE-01 และ VND-EDGE-03
- Sibling (downstream): test scenarios ของ persona **Receiver** ครอบคลุม GRN postings ที่ flip `po_status` ตาม `PO_POST_006` / `PO_POST_007` ตอบสนองต่อ vendor deliveries
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) / [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) — คำแก้ไขที่อธิบายว่าทำไมไม่มี scenarios invoice / three-way-match ปรากฏบนหน้านี้
- กฎทางธุรกิจที่ verify: [02-business-rules.md](./02-business-rules.md) Section 6 — `PO_XMOD_003` (GRN สร้างได้เฉพาะเมื่อ `po_status ∈ {approved, sent_or_print, partial}`), `PO_XMOD_004` (over-receipt tolerance ที่อ้างอิงใน VND-EDGE-02); Section 5 — `PO_POST_004` (final approval → `approved`), `PO_POST_004b` (send email / mark sent → `sent_or_print`), `PO_POST_006` / `PO_POST_007` (GRN-driven receipt transitions), `PO_POST_010`/`PO_POST_010b` / `PO_POST_011` (cancel / reject / close)
- E2E: `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` — shared / mixed-persona spec; **ไม่มี vendor E2E เฉพาะ** เพราะ vendor ไม่มี Carmen login
- Cross-link: [good-receive-note](/th/inventory/good-receive-note) — โมดูลปลายน้ำที่บันทึกการจัดส่งจริงของ vendor และขับเคลื่อน receipt-state transitions บน PO; surface หลักสำหรับ VND-HP-02, VND-HP-03, และ wrong-item discrepancy ใน VND-EDGE-02
