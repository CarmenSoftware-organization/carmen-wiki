---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios
description: เคสทดสอบตาม persona scenario ข้าม persona และการ map Playwright ของ good-receive-note
published: true
date: 2026-05-19T23:55:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios

> **At a Glance**
> **โมดูล:** [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; **Scenario รวม:** ~10 ข้าม persona + ~110 ต่อ persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Receiver, Purchaser, Finance, Audit / Config
> **ลำดับการรัน:** ตั้งค่า Audit / Config → happy path ของ persona หลัก → scenario ข้าม persona
> **การเจาะลึกของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็น **entry point ภาพรวม** สำหรับชุด test-scenario ของโมดูล `good-receive-note` มันจัดกลุ่ม coverage ของ GRN ตามสี่ persona ที่ interact กับเอกสารตลอด lifecycle (Receiver, Purchaser, Finance, Audit / Config) แสดง inventory ไฟล์ test ต่อ persona จับ scenario การ handoff ข้าม persona ที่เย็บเส้นทางแยกเข้าด้วยกัน และ map ทุก scenario ข้าม persona กลับไปยัง Playwright spec canonical [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) ขอบเขตกว้างกว่าการ pass functional บริสุทธิ์โดยตั้งใจ: ไฟล์แต่ละ persona รวม **happy path functional**, **กรณี RBAC / permission-denial** (ขับเคลื่อนโดย fixture `requestor@blueledgers.com`), **edge case** (input ว่าง / ไม่ถูกต้อง / ใหญ่), **ผลลัพธ์ three-way-match** (การจัดแนว PO ↔ GRN ↔ invoice, รับบางส่วน, คลาดเคลื่อนราคา / qty) และ **lot-tracking trace** (การมีอยู่ของข้อมูล lot ตอน commit และคิวรี recall หลัง commit ผ่าน `tb_inventory_transaction_detail`)

Scenario ข้าม persona ใน Section 4 คือชั้น integration เหนือชุด per-persona บรรยายเส้นทาง end-to-end ที่ข้ามขอบเขต handoff ที่บันทึกใน [03-user-flow.md](./03-user-flow.md) Section 4 — ตัวอย่างเช่น *Receiver save → Inventory Manager commit → Finance match invoice* Section 5 จากนั้น map describe block ของ `501-grn.spec.ts` กับเส้นทางเหล่านั้นเพื่อให้ gap ใน coverage automated มองเห็นได้ในเหลือบเดียว; โปรดทราบว่า `501-grn.spec.ts` เป็นไฟล์ E2E **เพียงไฟล์เดียว** ของ GRN — ไม่มี spec dedicated ต่อ persona ดังนั้นไฟล์ test ต่อ persona ใน Section 3 บรรยาย scenario ที่ครอบคลุมบางส่วนโดย `501-grn.spec.ts` และเอกสารบางส่วนเป็น manual / planned test

## 2. Persona ในขอบเขต

- **Receiver**: พนักงาน Receiving / warehouse ที่รับสินค้าจริง ขึ้น GRN ใน `draft` กรอก header และบรรทัด (กับ PO หรือ manual) และ save เพื่อ review
- **Purchaser**: พนักงาน Procurement ที่เป็นเจ้าของ PO ต้นทางและดูดซับ handoff variance / คุณภาพ / three-way-mismatch กลับจาก Receiver และ Finance
- **Finance**: พนักงาน AP ที่ consume GRN `committed` รัน three-way match กับ invoice vendor และ co-authorise reversal หลัง commit
- **Audit / Config**: System Administrator และ auditor ที่เป็นเจ้าของ RBAC ตั้งค่ารูปแบบ lot / posting / extra-cost, sweep scheduled และ trace audit read-only ข้าม inventory transaction

## 3. ไฟล์ Test ของ Persona

- [Scenario ของ Receiver](./04-test-scenarios-receiver.md)
- [Scenario ของ Purchaser](./04-test-scenarios-purchaser.md)
- [Scenario ของ Finance](./04-test-scenarios-finance.md)
- [Scenario ของ Audit / Config](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้าม Persona / Handoff

ตารางด้านล่างเป็นชั้น integration แต่ละแถว span อย่างน้อยหนึ่ง handoff จาก [03-user-flow.md](./03-user-flow.md) Section 4 และจบด้วยเอกสารใน state terminal หรือ steady "Persona ในลำดับ" lists actor ตามลำดับ execute; "Pre-condition" จับ state ของระบบที่ต้องเริ่ม; "Expected end state" anchor `doc_status` ของ GRN และผลปลายทาง (inventory, PO, AP)

| # | Scenario | Persona ในลำดับ | Pre-condition | Expected end state |
| - | -------- | --------------- | ------------- | ------------------ |
| 1 | Happy path เต็มกับ PO | Receiver → Inventory Manager → Finance | PO ต้นทางที่ `po_status ∈ {sent, partial}` และมีอย่างน้อยหนึ่งบรรทัด pending; vendor / สกุลเงิน / อัตราแลกเปลี่ยนพร้อม; receiver มีสิทธิ์สร้าง GRN | GRN `committed`; inventory เพิ่ม; layer FIFO / avg-cost เขียน; `received_qty` บรรทัด PO เลื่อน (PO → `partial` หรือ `completed`); AP accrual ถูกขึ้น; invoice vendor three-way match และ post โดย Finance |
| 2 | GRN manual (ไม่มี PO) | Receiver → Inventory Manager → Finance | `doc_type = manual` อนุญาตโดย tenant config; vendor active; ไม่มี PO ต้นทาง | GRN `committed` พร้อม `doc_type = manual` และไม่มี `purchase_order_detail_id` บนบรรทัดใด; inventory เพิ่ม; AP accrual ถูกขึ้น; Finance match กับ invoice vendor โดยไม่มี leg PO |
| 3 | รับบางส่วนข้ามสอง GRN | Receiver → Inventory Manager → Receiver → Inventory Manager → Finance | บรรทัด PO ต้นทางมี qty pending ใหญ่กว่าการส่งครั้งแรก; tenant อนุญาตรับบางส่วน | GRN แรก `committed` และบรรทัด PO → `partial` พร้อม `received_qty` < `ordered_qty`; GRN ที่สองภายหลัง `committed` และบรรทัด PO → `completed`; Finance match invoice หนึ่งหรือสอง ขึ้นกับการเก็บเงินของ vendor |
| 4 | ปัญหาคุณภาพตอนรับ | Receiver → Inventory Manager → Purchaser | การส่งของมีสินค้าเสียหาย / qty ขาด; receiver บันทึก `accepted_qty < received_qty` พร้อม comment variance บนบรรทัด | GRN `committed` พร้อม flag คุณภาพบนบรรทัดที่กระทบ; Purchaser ได้รับ variance handoff สำหรับประสาน vendor (credit note หรือ replacement PO); inventory สะท้อนเฉพาะ qty ที่รับ |
| 5 | คลาดเคลื่อน three-way บน invoice | Receiver → Inventory Manager → Finance → Purchaser | GRN `committed` สะอาด; invoice vendor มาถึงพร้อมราคาหรือ qty เบี่ยงเบนเกิน tolerance จาก PO / GRN | GRN ยังคง `committed` ไม่เปลี่ยน; Finance flag ความคลาดเคลื่อน invoice และ bounce กลับ Purchaser; เส้นทางแก้คือ credit note กับ GRN หรือ reversal หลัง commit (Scenario 9) |
| 6 | Review การจัดสรร extra-cost | Receiver → Finance → Inventory Manager | Receiver บันทึก freight / duty / clearance ใน `tb_good_received_note_extra_cost` พร้อมโหมดจัดสรร `manual`, `by_value` หรือ `by_qty`; GRN ยังอยู่ใน `saved` | Finance review / ปรับการจัดสรรก่อน AP; Inventory Manager commit พร้อมบรรทัด extra-cost ที่ reconcile; AP accrual ขึ้นรวมส่วน extra-cost; cost layer carry landed cost |
| 7 | Batch commit สิ้นกะ | Receiver (×N) → Inventory Manager | N GRN นั่งใน `saved` จากกะ; แต่ละใบผ่านกฎระดับบรรทัดอย่างอิสระ | Inventory Manager fire batch commit; แต่ละ GRN ถูกประเมินกับกฎ commit-time; ความล้มเหลวบางส่วนของ batch roll back เฉพาะ GRN ที่ล้มเหลว; GRN สำเร็จ → `committed` ใน transaction window เดียว |
| 8 | Trace lot recall | System Administrator → Auditor | อย่างน้อยหนึ่ง GRN `committed` มีข้อมูล lot เขียนบน `tb_inventory_transaction_detail` ผ่าน `tb_good_received_note_detail_item.inventory_transaction_id` | Sysadmin คิวรีตามหมายเลข lot; Auditor trace จาก inventory transaction กลับไปยัง detail_item ของ GRN และไปข้างหน้าสู่ issue / stock count ปลายทาง; ไม่มีการเปลี่ยน state เอกสาร |
| 9 | Void หลัง commit (co-auth elevated) | Inventory Manager + Finance → Receiver | GRN `committed`; คำขอ reversal ขึ้นพร้อมเหตุผล; co-authorisation elevated พร้อม | GRN → `voided` พร้อม reversal ชดเชยของ inventory transaction, reversal cost-layer, decrement `received_qty` บรรทัด PO และ entry AP reverse; Receiver อาจขึ้น GRN replacement ถ้าจะบันทึกการรับจริงใหม่ |
| 10 | Sweep auto-commit ที่ schedule | System Administrator → Finance, Inventory Manager | GRN `saved` เก่ากว่า grace window ของ tenant มีอยู่; job sweep schedule | GRN ที่ eligible → `committed` โดย sweep ใช้กฎ commit-time เดียวกัน; GRN ที่ล้มเหลวถูก log และ route ไปยัง Inventory Manager สำหรับการแก้ manual; Finance หยิบ GRN ที่ commit ใหม่สำหรับการ match |

## 5. การ Map Test E2E

`501-grn.spec.ts` เป็นไฟล์ Playwright E2E **เพียงไฟล์เดียว** สำหรับโมดูล GRN จัดโครงสร้างเป็นไฟล์เดียวที่มีหลาย `describe` block ต่อพื้นที่ functional; auth เป็น multi-role ผ่าน `createAuthTest` พร้อม `purchase@blueledgers.com` สำหรับเส้นทาง happy / functional (เทียบเท่า Receiver + Purchaser) และ `requestor@blueledgers.com` สำหรับ permission-denial มี **spec dedicated ต่อ persona ศูนย์** — ไฟล์ test ต่อ persona ที่ link ใน Section 3 catalog scenario; บางส่วนครอบคลุมโดย `501-grn.spec.ts` describe block ด้านล่าง อื่น ๆ ยังเป็นเอกสาร / manual

| Describe block ของ `501-grn.spec.ts` (TC group) | Scenario ข้าม persona ที่ครอบคลุม (Section 4) |
| ------------------------------------------- | ------------------------------------------- |
| `GRN — List` (TC-GRN-900001 / 010001–010004) | 1, 8 (entry point สำหรับ list GRN committed ตาม lot / status) |
| `GRN — Filter / Search` (TC-GRN-900002 / 020001–020005) | 8 (คิวรี recall ตาม lot / vendor / invoice number) |
| `GRN — Create from Single PO` (TC-GRN-900003 / 030001–030005) | 1, 3 (leg แรกของ happy path และรับบางส่วน) |
| `GRN — Create from Multiple POs` (TC-GRN-900004 / 040002–040004) | 1, 3 (รวมหลาย PO เป็น GRN ใบเดียว) |
| `GRN — Manual creation` (TC-GRN-900005 / 050001–050005) | 2 (entry point GRN manual end-to-end) |
| `GRN — Edit Header` (TC-GRN-900006 / 060001–060005) | 1, 2 (แก้ header ก่อน save เพื่อ review) |
| `GRN — Add Line Item` (TC-GRN-900007 / 070001–070004) | 1, 2, 3 (กรอกบรรทัดข้ามเส้นทาง PO และ manual) |
| `GRN — Edit Line Item` (TC-GRN-900008 / 080001–080005) | 4 (ปัญหาคุณภาพ: แก้ `accepted_qty` < `received_qty`) |
| `GRN — Delete Line Item` (TC-GRN-900009 / 090001+) | 1, 3 (cleanup บรรทัดก่อน commit) |
| `GRN — Extra Costs` (TC-GRN-900010 / 1059+) | 6 (review การจัดสรร extra-cost) |
| `GRN — Commit` (TC-GRN-900011 / 1150+) | 1, 2, 3, 4, 6, 7 (event posting canonical) |
| `GRN — Void` (TC-GRN-900012 / 1263+) | 9 (void ก่อน commit; reversal หลัง commit ครอบคลุมบางส่วน) |
| `GRN — Financial Summary` (TC-GRN-900013 / 1372+) | 5, 6 (input three-way-match และ landed cost) |
| `GRN — Stock Movements` (TC-GRN-900014 / 1476+) | 1, 8 (inventory transaction เขียนตอน commit; lot trace) |
| `GRN — Comments` (TC-GRN-900015 / 1554+) | 4, 5 (comment variance ที่ handoff ไป Purchaser) |
| `GRN — Attachments` (TC-GRN-900016 / 1692+) | 5 (หลักฐาน invoice / packing-list สำหรับ three-way match) |
| `GRN — Activity Log` (TC-GRN-900017 / 1821+) | 8, 9 (audit trail ข้าม commit / void / reversal) |
| `GRN — Bulk Approval` (TC-GRN-900018 / 1925+) | 7 (batch commit สิ้นกะ) |
| `GRN — * — Permission denial` (block `requestor@blueledgers.com` ทั้งหมด) | ชั้น RBAC ข้ามทุก scenario; ไฟล์ persona สี่ไฟล์ใน Section 3 catalog เส้นทางการ deny เฉพาะ persona |

Gap เทียบกับ Section 4: Scenario 5 (คลาดเคลื่อน three-way end-to-end) และ Scenario 10 (sweep auto-commit schedule) ยังไม่ครอบคลุมโดย `501-grn.spec.ts` และเป็น manual / planned case ในไฟล์ persona

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Playwright E2E spec canonical (auth multi-role, ทุกกลุ่ม TC-GRN-9xxxxx)
- พี่น้อง: [03-user-flow.md](./03-user-flow.md) Section 4 — handoff ข้าม persona ที่ขับเคลื่อน scenario integration ด้านบน
- พี่น้อง: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rule และกฎ three-way-match ที่เรียกที่ transition `saved → committed`
- รายละเอียดต่อ persona: [Receiver](./04-test-scenarios-receiver.md), [Purchaser](./04-test-scenarios-purchaser.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md)
