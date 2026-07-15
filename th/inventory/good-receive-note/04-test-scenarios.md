---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios
description: เคสทดสอบตาม persona scenario ข้าม persona และการ map Playwright ของ good-receive-note
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios

> **At a Glance**
> **โมดูล:** [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Receiver, Purchaser, Finance (หน้าแก้ไข), Audit / Config (หน้าแก้ไข)
> **ลำดับการรัน:** happy path ต่อ persona หลัก → scenario ข้าม persona
> **การเจาะลึกของแต่ละ persona คือ `04-test-scenarios-<role>.md`**
> **แก้ไขในรอบนี้ (2026-07-15):** เวอร์ชันก่อนหน้าของหน้านี้บรรยาย commit เป็นเหตุการณ์ posting, ชั้น integration แบบ three-way-match / AP-posting, และกลไก batch-commit / scheduled-auto-commit ทั้งหมดนี้ไม่ตรงกับซอร์สปัจจุบัน — ดู [02-business-rules.md](./02-business-rules.md) §1 และการแก้ไขในเนื้อหาด้านล่าง

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้าภาพรวม** สำหรับชุด test-scenarios ของโมดูล `good-receive-note` จัดกลุ่มความครอบคลุมของ GRN ตาม persona (Receiver, Purchaser, Finance, Audit / Config) เก็บรายการไฟล์ทดสอบต่อ persona จับ scenario handoff ข้าม persona ที่เย็บแต่ละเส้นทางเข้าด้วยกัน และ map scenario กลับไปยัง Playwright spec ทางการ [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) **ยังไม่ยืนยัน / ตัดออกในรอบนี้:** "three-way-match outcomes" และ trace `accepted_qty` แบบ quality-inspection ต่อบรรทัด เคยอยู่ในรายการขอบเขตความครอบคลุมในเวอร์ชันก่อนหน้าของหน้านี้ — ไม่พบทั้งสองฟีเจอร์ในซอร์สปัจจุบัน (ดู [01-data-model.md](./01-data-model.md) และ [03-user-flow-finance.md](./03-user-flow-finance.md))

`501-grn.spec.ts` เป็นไฟล์ Playwright E2E **เดียว** สำหรับโมดูล GRN; test body แต่ละตัวส่วนใหญ่เป็น best-effort (`.catch(() => {})` เมื่อ UI ไม่มี, มี hard assertion น้อย) ดังนั้นให้ถือว่า `TC-GRN-*` id ที่ map ไว้เป็นเพียง "มี describe block ชื่อนี้อยู่" ไม่ใช่หลักฐานว่าพฤติกรรมที่บรรยายถูก assert แบบ end-to-end

## 2. Persona ในขอบเขต

- **Receiver**: พนักงานรับของ / คลังสินค้าที่รับของจริง ขึ้น GRN ที่ `draft` และบันทึกเพื่อ review (`draft → saved`) — ขั้นตอนที่ post inventory และเลื่อน PO
- **Purchaser**: พนักงานจัดซื้อที่เป็นเจ้าของ PO ต้นทางและ review variance การรับ; การประสานฝั่ง vendor เกิดขึ้นนอกเอกสาร
- **Finance**: **หน้าแก้ไข** — ไม่พบฟีเจอร์ three-way match, การ post AP หรือบทบาท Finance สำหรับโมดูลนี้
- **Audit / Config**: **หน้าแก้ไข** — ไม่พบ GRN configuration console เฉพาะทางหรือเครื่องมือ lot-recall สำหรับโมดูลนี้

## 3. ไฟล์ทดสอบต่อ Persona

- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Finance scenarios](./04-test-scenarios-finance.md) — หน้าแก้ไข
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md) — หน้าแก้ไข

## 4. Scenario ข้าม Persona / Handoff

ตารางด้านล่าง span handoff ที่บันทึกไว้ใน [03-user-flow.md](./03-user-flow.md) ส่วน 4 **แก้ไขในรอบนี้:** แถวสำหรับ "การ review extra-cost allocation โดย Finance", "batch commit", "post-commit void พร้อม elevated co-auth" และ "scheduled auto-commit sweep" ถูกตัดออก — ไม่มีอันไหนตรงกับซอร์สปัจจุบัน (ไม่มี batch-commit endpoint ไม่มี scheduled job ไม่มีโค้ดบทบาท Finance และ endpoint `/void` ไม่มีเงื่อนไข `doc_status` นอกจาก "ยังไม่ voided" จึงไม่มีเส้นทาง reversal ที่ยกระดับให้ทดสอบ)

| # | Scenario | Persona ตามลำดับ | เงื่อนไขก่อน | สถานะปลายทางที่คาด |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Happy path เต็มกับ PO | Receiver → Inventory Manager | PO ต้นทางที่ `po_status ∈ {sent, partial}` และมีอย่างน้อยหนึ่งบรรทัด pending; vendor / currency / exchange rate พร้อม; receiver มีสิทธิ์สร้าง GRN | GRN `saved` (inventory เพิ่มแล้ว, FIFO / avg-cost layer เขียนแล้ว, `received_qty` ของบรรทัด PO เลื่อนแล้ว — `po_status` ไปทาง `partial` หรือ `completed` — ทั้งหมดตอน save); Inventory Manager commit ตามมา (`saved → committed`) ซึ่งล็อกเอกสารโดยไม่พบผลกระทบเพิ่มเติม |
| 2 | GRN แบบ manual (ไม่มี PO) | Receiver → Inventory Manager | `doc_type = manual` อนุญาตโดย tenant config; vendor active; ไม่มี PO ต้นทาง | GRN `saved` พร้อม `doc_type = manual` และไม่มี `purchase_order_detail_id` บนบรรทัดใด; inventory เพิ่มตอน save; commit ล็อกเอกสาร |
| 3 | การรับบางส่วนข้ามสอง GRN | Receiver → Inventory Manager → Receiver → Inventory Manager | บรรทัด PO ต้นทางมี pending qty มากกว่าการส่งครั้งแรก; tenant อนุญาตการรับบางส่วน | GRN แรก `saved` และบรรทัด PO → `partial` ด้วย `received_qty < ordered_qty`; GRN ที่สอง `saved` ในภายหลังและบรรทัด PO → `completed`; ทั้งสอง GRN ถูก commit แยกกันในภายหลังเพื่อล็อก |
| 4 | การรับของขาดที่ flag เพื่อตาม vendor | Receiver → Purchaser | การส่งของมีบรรทัดที่ขาด; receiver บันทึก `received_qty < order_qty` พร้อม variance comment บนบรรทัด | GRN `saved` (inventory เพิ่มเฉพาะ `received_qty` จริง); Purchaser review และประสานการตามกับ vendor นอกเอกสาร (chase, PO replacement) — ไม่พบ workflow แก้ไขในแอปเฉพาะทาง |
| 5 | การบันทึก extra-cost บน GRN | Receiver | Receiver บันทึก freight / duty / clearance กับ `tb_extra_cost` พร้อม tag โหมดการกระจาย (`manual`, `by_value`, หรือ `by_qty`); GRN ยัง `draft` | แถว extra-cost persist พร้อม tag; **ยังไม่ยืนยัน** ว่าถูกแบ่งข้ามบรรทัดจริงหรือป้อนเข้าสู่การคำนวณ cost layer ตอน save หรือไม่ — ดู [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) |
| 6 | การรวมหลาย PO เข้า GRN เดียว | Receiver | ผู้ขายและสกุลเงินเดียวกันข้ามสอง PO เปิด (wizard รวมหลาย PO ปฏิเสธการเลือกที่มีสกุลเงินต่างกัน) | GRN เดียวพร้อมบรรทัดที่ span ทั้งสอง PO; save เลื่อน `received_qty` บนทั้งสอง PO ในธุรกรรมเดียว |

## 5. E2E Test Mapping

`501-grn.spec.ts` เป็นไฟล์ Playwright E2E **เดียว** สำหรับโมดูล GRN มีโครงสร้างเป็นไฟล์เดียวพร้อมหลาย `describe` block ต่อพื้นที่ฟังก์ชัน; auth เป็น multi-role ผ่าน `createAuthTest` โดย `purchase@blueledgers.com` สำหรับ happy / functional path และ `requestor@blueledgers.com` สำหรับเคส permission-denial

| `501-grn.spec.ts` describe block (กลุ่ม TC) | Scenario ข้าม persona ที่ครอบคลุม (ส่วน 4) |
| ------------------------------------------- | ------------------------------------------- |
| `GRN — List` (TC-GRN-010001–010004) | 1 (entry point สำหรับ list GRN) |
| `GRN — Filter / Search` (TC-GRN-020001–020005) | 1 (ค้นหาตาม vendor / invoice number) |
| `GRN — Create from Single PO` (TC-GRN-030001–030005) | 1, 3 (leg แรกของ happy path และการรับบางส่วน) |
| `GRN — Create from Multiple POs` (TC-GRN-040002–040004) | 6 (การรวมหลาย PO) |
| `GRN — Manual creation` (TC-GRN-050001–050005) | 2 (GRN manual แบบ end-to-end) |
| `GRN — Edit Header` (TC-GRN-060001–060005) | 1, 2 (แก้ header ก่อน save-for-review) |
| `GRN — Add Line Item` (TC-GRN-070001–070004) | 1, 2, 3 (การกรอกบรรทัดข้ามเส้นทาง PO และ manual) |
| `GRN — Edit Line Item` (TC-GRN-080001–080005) | 4 (การแก้ `received_qty` บนบรรทัดที่ส่งขาด) |
| `GRN — Delete Line Item` (TC-GRN-090001+) | 1, 3 (การจัดการบรรทัดก่อน save) |
| `GRN — Extra Costs` (TC-GRN-100001+) | 5 (การบันทึก extra-cost) |
| `GRN — Commit` (TC-GRN-110001+) | 1, 2, 3 (เส้นทาง save-แล้ว-commit — หมายเหตุ: annotation ของ describe block เองเรียกสิ่งนี้ว่า "the canonical posting event" ซึ่งรอบนี้แก้ไข: save คือเหตุการณ์ posting, commit เพียงล็อก) |
| `GRN — Void` (TC-GRN-120001–120004) | Void จาก `draft` / `saved` **หมายเหตุ:** annotation ของ `TC-GRN-120003` บรรยายว่าการ void GRN ที่ `committed` จะย้อนกลับเป็น "RECEIVED" พร้อมการเคลื่อนไหวสต๊อกที่กลับด้านและ Journal Voucher ที่กลับด้าน — สิ่งนี้ไม่ตรงกับโค้ดจริงของ `voidGrnById()` (ซึ่งตั้ง `doc_status = voided` โดยไม่มีการกลับด้านใดๆ) และ test body เองไม่ได้ assert อะไรเลย ให้ถือว่า annotation เป็นความปรารถนา ไม่ใช่พฤติกรรมที่ยืนยันแล้ว |
| `GRN — Financial Summary` (TC-GRN-130001+) | 5 (มุมมองยอดรวมแบบ read-only ไม่ใช่ input ของ three-way-match) |
| `GRN — Stock Movements` (TC-GRN-140001+) | 1 (inventory transaction ที่เขียนตอน save) |
| `GRN — Comments` (TC-GRN-150001+) | 4 (variance comment) |
| `GRN — Attachments` (TC-GRN-160001+) | 1 (หลักฐาน packing-list) |
| `GRN — Activity Log` (TC-GRN-170001+) | 1 (audit trail ข้าม save / commit / void) |
| `GRN — Bulk Approval` (TC-GRN-180001+) | **ยังไม่ยืนยัน** — annotation ของ describe block นี้บรรยายสถานะ "APPROVED" ต่อบรรทัดที่ไม่มีอยู่ใน schema (`tb_good_received_note_detail_item` ไม่มีคอลัมน์สถานะ); test body ไม่มี assertion ไม่ได้ map ไปยัง scenario ใดข้างต้น |
| `GRN — * — Permission denial` (ทุก block ของ `requestor@blueledgers.com`) | ชั้น RBAC ข้ามทุก scenario; สองไฟล์ persona ในส่วน 3 เก็บ path denial เฉพาะ persona |

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Playwright E2E spec ทางการ (multi-role auth, ทุกกลุ่ม `TC-GRN-*`)
- Sibling: [03-user-flow.md](./03-user-flow.md) ส่วน 4 — handoff ข้าม persona ที่ขับเคลื่อน scenario integration ข้างต้น แก้ไขในรอบนี้ให้ตัดแถว batch-commit / auto-commit / post-commit-reversal ออก
- Sibling: [02-business-rules.md](./02-business-rules.md) ส่วน 5 — กฎ posting แก้ไขในรอบนี้ให้แสดง save ไม่ใช่ commit เป็นเหตุการณ์ posting
- รายละเอียดต่อ persona: [Receiver](./04-test-scenarios-receiver.md), [Purchaser](./04-test-scenarios-purchaser.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md)
