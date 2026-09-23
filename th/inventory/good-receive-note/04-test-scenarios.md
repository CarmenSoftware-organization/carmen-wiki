---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios
description: เคสทดสอบตาม persona scenario ข้าม persona และการ map Playwright ของ good-receive-note
published: true
date: '2026-09-23T01:30:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios

> **At a Glance**
> **โมดูล:** [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Receiver, Purchaser, Finance (หน้าแก้ไข), Audit / Config (หน้าแก้ไข)
> **ลำดับการรัน:** happy path ต่อ persona หลัก → scenario ข้าม persona
> **การเจาะลึกของแต่ละ persona คือ `04-test-scenarios-<role>.md`**
> **ตรวจสอบซ้ำ 2026-09-22:** พฤติกรรมที่คาดหวังด้านล่างตอนนี้เดินตามโมเดลการโพสต์ปัจจุบัน — **commit** โพสต์สต๊อกและเลื่อน PO; **business unit แบบ average** โพสต์สต๊อกตั้งแต่ save; void/reject ถอนการเคลื่อนไหวล่วงหน้านั้นออก; extra cost และ FOC เป็นส่วนหนึ่งของ landed cost ดู [02-business-rules.md](./02-business-rules.md) §1 และ §5

> **ความครอบคลุมที่รันได้ (repo E2E `../carmen-inventory-frontend-e2e/`):** spec `tests/501-grn.spec.ts` — **76 case** (44 High / 24 Medium / 8 Low ตาม `docs/user-stories/501-grn.md`) แต่ `docs/test-cases/SPEC-HEALTH.md` บันทึกว่า **57 จาก 76 ไม่มี `expect()` เลย** ไม่มีหน้า catalog `docs/test-cases/501-grn-core.md`; **gap report** สองฉบับคือรายการทางการของพฤติกรรมที่ยังขาด oracle ที่ fail ได้: `docs/test-cases/gaps/501-grn-core-gap.md` (**62 case**, list · detail · edit · receive · tax/discount · status · permissions) และ `docs/test-cases/gaps/501-grn-from-po-gap.md` (**24 case**, `TC-GRN-040005`–`040028`, wizard `/from-po` — ซึ่ง spec ไม่เคยเปิด) `docs/test-cases/COVERAGE.md` map route `/procurement/goods-receive-note` ไปยัง `002-spa-smoke.spec.ts`, `501-grn.spec.ts`, `710-wastage-reporting.spec.ts` หน้านี้ไม่ได้ mirror case เหล่านั้น

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้าภาพรวม** สำหรับชุด test-scenarios ของโมดูล `good-receive-note` จัดกลุ่มความครอบคลุมของ GRN ตาม persona (Receiver, Purchaser, Finance, Audit / Config) ทำบัญชีไฟล์ test ต่อ persona จับ scenario handoff ข้าม persona ที่ร้อยเส้นทางเดี่ยวเข้าด้วยกัน และ map scenario กลับไปยัง Playwright spec ทางการ [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) "ผลลัพธ์ three-way match" และ trace การตรวจคุณภาพต่อบรรทัดด้วย `accepted_qty` ยังคงอยู่นอกขอบเขต — ไม่มีฟีเจอร์ทั้งสอง (ตรวจซ้ำ 2026-09-22; ดู [01-data-model.md](./01-data-model.md) และ [03-user-flow-finance.md](./03-user-flow-finance.md))

`501-grn.spec.ts` เป็นไฟล์ Playwright E2E **เดียว** สำหรับโมดูล GRN; สามในสี่ของ case เดิน UI โดยไม่ assert อะไรเลย (ดูหมายเหตุความครอบคลุมด้านบน) ดังนั้นให้ถือว่า id `TC-GRN-*` ที่ map ไว้หมายถึง "มี describe block ชื่อนี้อยู่" ไม่ใช่หลักฐานว่าพฤติกรรมที่บรรยายถูก assert แบบ end-to-end ตอนนี้ fixture ของ E2E login เป็นผู้ใช้ `…@carmensoftware.dev` กับ BU `GR2VYNKQ` (`d2b35a1`) ไม่ใช่ `@blueledgers.com`

## 2. Persona ในขอบเขต

- **Receiver**: พนักงานรับของ / คลังสินค้าที่รับของจริง ขึ้น GRN ที่ `draft` save (`draft → saved` — ตรวจสอบ ออกเลข และบน BU แบบ average โพสต์สต๊อก) และ commit (`saved → committed` — โพสต์สต๊อกถ้ายังไม่ เลื่อน PO)
- **Purchaser**: พนักงานจัดซื้อที่เป็นเจ้าของ PO ต้นทางและ review variance การรับ; การประสานฝั่ง vendor เกิดขึ้นนอกเอกสาร
- **Finance**: **หน้าแก้ไข** — ไม่พบฟีเจอร์ three-way match, การ post AP หรือบทบาท Finance สำหรับโมดูลนี้
- **Audit / Config**: **หน้าแก้ไข** — ไม่พบ GRN configuration console เฉพาะทางหรือเครื่องมือ lot-recall สำหรับโมดูลนี้

## 3. ไฟล์ทดสอบต่อ Persona

- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Finance scenarios](./04-test-scenarios-finance.md) — หน้าแก้ไข
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md) — หน้าแก้ไข

## 4. Scenario ข้าม Persona / Handoff

ตารางด้านล่าง span handoff ที่บันทึกไว้ใน [03-user-flow.md](./03-user-flow.md) ส่วน 4 แถวสำหรับ "การ review การจัดสรร extra-cost โดย Finance", "batch commit", "void หลัง commit พร้อม co-auth ระดับสูง" และ "scheduled auto-commit sweep" ยังคงถูกตัดออก — ไม่มีอยู่จริง (ตรวจซ้ำ 2026-09-22; ตอนนี้ server ปฏิเสธการ void หลัง commit ทันที)

| # | Scenario | Persona ตามลำดับ | เงื่อนไขก่อน | สถานะปลายทางที่คาด |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Happy path เต็มกับ PO (business unit แบบ FIFO) | Receiver → Inventory Manager | PO ต้นทางที่ `po_status ∈ {approved, sent_or_print, partial}` มีอย่างน้อยหนึ่งบรรทัด pending; BU `calculation_method = fifo`; receiver ถือ `procurement.goods_received_note.create` + `.commit` | หลัง **save**: `doc_status = saved` ออก `grn_no` จริง **ไม่มี** แถว ledger PO ไม่ถูกแตะ หลัง **commit**: `tb_inventory_transaction` หนึ่งแถว (`inventory_doc_type = good_received_note`) มี detail + cost layer หนึ่งชุดต่อบรรทัด (`lot_no = <location_code><YYMM><run>`, `cost_per_unit` = landed cost 2 ตำแหน่ง, `extra_cost_amount`), `detail_item.inventory_transaction_id` ถูกตั้ง, junction ของ PO + `tb_purchase_order_detail.received_qty` เลื่อน, `po_status → partial` หรือ `completed`; เอกสารล็อก; แท็บ Stock Movement แสดง |
| 1b | เหมือนกัน บน business unit แบบ **average** | Receiver → Inventory Manager | เหมือน 1 แต่ `calculation_method = average`; `grn_date` อยู่ในงวดเปิด | หลัง **save**: ledger ถูกเขียนแล้ว (`tb_inventory_transaction.info.posted_at_save = true`) `average_cost_per_unit` ของสินค้าถูกประทับซ้ำบนทุก layer ของมัน PO **ไม่ถูกแตะ** หลัง **commit**: ไม่มีการเขียน ledger ครั้งที่สอง; PO เลื่อน; `info.po_receiving_applied = true` |
| 2 | GRN แบบ manual (ไม่มี PO) | Receiver → Inventory Manager | `doc_type = manual`; vendor active; ไม่มี PO ต้นทาง | `saved` โดยไม่มี `purchase_order_detail_id` และ `order_price = NULL` บนทุกเหตุการณ์ (จึงไม่มีการตรวจ price-deviation); commit โพสต์สต๊อก; ไม่มี PO ให้เลื่อน |
| 3 | การรับบางส่วนข้ามสอง GRN | Receiver → Inventory Manager → Receiver → Inventory Manager | บรรทัด PO ต้นทางมี pending qty มากกว่าการส่งครั้งแรก | GRN ใบแรก committed → บรรทัด PO `received_qty < order_qty − cancelled_qty`, `po_status = partial`; GRN ใบที่สอง committed → `po_status = completed` ไม่มีอะไรบน PO เปลี่ยนตอน save ทั้งสองครั้ง |
| 4 | การรับของขาดที่ flag เพื่อตาม vendor | Receiver → Purchaser | การส่งของมีบรรทัดที่ส่งขาด; receiver บันทึก `received_qty < order_qty` พร้อม comment variance บนบรรทัด | save ผ่าน (การขาดไม่มีวันฝ่าเพดาน deviation); commit โพสต์เฉพาะ `received_qty` จริง; Purchaser review และประสานการตาม vendor นอกเอกสาร — ไม่มี workflow แก้ไขในแอป |
| 5 | Extra cost และ FOC ใน landed cost | Receiver → Inventory Manager | header extra-cost ที่ `allocate_extra_cost_type = by_value` และ detail รวมกัน ฿200; สองบรรทัดที่ปริมาณสต๊อก 10 และ 4 (บรรทัดหนึ่งมี `foc_qty = 1` ด้วย) | ตอนโพสต์: ส่วนแบ่ง `฿200 × 11/15` และ `฿200 × 4/15` (`by_value` ถ่วงตาม `received_base + foc_base`); cost layer ของแต่ละบรรทัด `total_cost = base_net_amount + share`, `extra_cost_amount = share`, `in_qty` รวมหน่วย FOC; `cost_per_unit` ปัด 2 ตำแหน่ง ด้วย `by_qty` แต่ละบรรทัดได้ ฿100; ด้วย `manual` ไม่มีการจัดสรร ตัวนับ FOC ที่รับของ junction PO เพิ่ม 1 |
| 6 | การรวมหลาย PO เข้า GRN เดียว | Receiver | vendor และสกุลเงินเดียวกันข้ามสอง PO ที่รับได้; wizard ขั้น 2 เลือกหลายรายการ; การเลือกที่มีสกุลเงินต่างกันถูกปฏิเสธด้วย toast `mixedCurrencyError` (`from-po-content.tsx:93-95`) | GRN เดียวที่บรรทัด span ทั้งสอง PO; commit เลื่อน `received_qty` บนทั้งสอง PO ในธุรกรรมเดียว |
| 7 | Void GRN ที่ saved บน BU แบบ average หลังสต๊อกถูกเบิกแล้ว | Receiver → Store Keeper (เบิก SR) → Receiver | BU แบบ average; GRN `saved` (โพสต์สต๊อกแล้ว); SR / stock-out ใช้ lot ที่รับไปบางส่วน | `DELETE …/void` และ `POST …/reject` ต่างคืน **409 `GRN_RECEIPT_ALREADY_CONSUMED`**; เอกสารคงเป็น `saved` หากไม่มีการเบิก void สำเร็จ การเคลื่อนไหวถูก soft-delete `inventory_transaction_id` ถูกล้าง และ average ของสินค้าถูกประทับใหม่ |
| 8 | วันที่รับอยู่นอกงวดเปิด | Receiver | draft ที่ `grn_date` อยู่ในงวด `closed` (หรือไม่มีงวด) | `POST …/verify` (`verify_state = create`) และ commit / approve (และ save บน BU แบบ average) คืน **422 `GRN_DATE_OUTSIDE_OPEN_PERIOD`**; dialog commit บน UI เสนอ "ย้ายไปงวดเปิด" ซึ่งเขียน `grn_date` ใหม่เป็น `start_at` ของงวดก่อนลูกโซ่ `PATCH → /save → /commit` |

## 5. E2E Test Mapping

`501-grn.spec.ts` เป็นไฟล์ Playwright E2E **เดียว** สำหรับโมดูล GRN มีโครงสร้างเป็นไฟล์เดียวที่มีหลาย `describe` block ต่อพื้นที่ฟังก์ชัน; auth เป็นหลาย role ผ่าน `createAuthTest` โดยผู้ใช้บทบาท Purchase สำหรับ happy / functional path และผู้ใช้บทบาท Requestor สำหรับ case permission-denial (ผู้ใช้ย้ายไปโดเมน `carmensoftware.dev`, BU `GR2VYNKQ`) route ของ wizard `/from-po` **ไม่** ถูกเยี่ยมโดย case ใด — ดู `gaps/501-grn-from-po-gap.md`

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
| `GRN — Extra Costs` (TC-GRN-100001+) | 5 (การบันทึก extra-cost; การจัดสรรเข้า landed cost สังเกตได้เฉพาะบนแท็บ Stock Movement หลัง commit) |
| `GRN — Commit` (TC-GRN-110001+) | 1, 1b, 2, 3 (annotation ของ describe block ที่เรียก commit ว่า "the canonical posting event" **ถูกต้องอีกครั้ง** ตั้งแต่ `c815d67ce`; บน BU แบบ average สต๊อกถูกโพสต์แล้วตอน save) |
| `GRN — Void` (TC-GRN-120001–120004) | 7 — void จาก `draft` / `saved` **หมายเหตุ:** annotation ของ `TC-GRN-120003` บรรยายการ void GRN ที่ `committed` ว่าย้อนกลับเป็น "RECEIVED" พร้อมกลับรายการ stock movement และ Journal Voucher — ตอนนี้ server คืน `GRN_COMMITTED_NOT_VOIDABLE` สำหรับ GRN ที่ committed และไม่มี JV; ตัว test body ไม่ assert อะไร |
| `GRN — Financial Summary` (TC-GRN-130001+) | 5 (มุมมองยอดรวมแบบ read-only; header totals ไม่รวม extra cost) |
| `GRN — Stock Movements` (TC-GRN-140001+) | 1, 1b, 5 (`GET …/stock-movements` เป็น API จริงตั้งแต่ 2026-08; แท็บแสดงเฉพาะ GRN ที่ `committed` — `grnStockVisible()`) |
| `GRN — Comments` (TC-GRN-150001+) | 4 (variance comment) |
| `GRN — Attachments` (TC-GRN-160001+) | 1 (หลักฐาน packing-list) |
| `GRN — Activity Log` (TC-GRN-170001+) | 1 (audit trail ข้าม save / commit / void) |
| `GRN — Bulk Approval` (TC-GRN-180001+) | **ยังไม่ยืนยัน** — annotation ของ describe block นี้บรรยายสถานะ "APPROVED" ต่อบรรทัดที่ไม่มีอยู่ใน schema (`tb_good_received_note_detail_item` ไม่มีคอลัมน์สถานะ); test body ไม่มี assertion ไม่ได้ map ไปยัง scenario ใดข้างต้น |
| `GRN — * — Permission denial` (ทุก block ของ `requestor@blueledgers.com`) | ชั้น RBAC ข้ามทุก scenario; สองไฟล์ persona ในส่วน 3 เก็บ path denial เฉพาะ persona |

## 6. แหล่งอ้างอิง

- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — Playwright E2E spec ทางการ (76 case, auth หลาย role, ทุกกลุ่ม `TC-GRN-*`); catalogue ที่ generate `docs/user-stories/501-grn.md`; gap report `docs/test-cases/gaps/501-grn-core-gap.md` (62) และ `docs/test-cases/gaps/501-grn-from-po-gap.md` (24); สุขภาพ spec `docs/test-cases/SPEC-HEALTH.md`
- Sibling: [03-user-flow.md](./03-user-flow.md) ส่วน 4 — handoff ข้าม persona ที่ขับ integration scenario ข้างต้น
- Sibling: [02-business-rules.md](./02-business-rules.md) ส่วน 5 — กฎ posting (ตรวจสอบซ้ำ 2026-09-22: commit โพสต์; BU แบบ average โพสต์สต๊อกตอน save)
- รายละเอียดต่อ persona: [Receiver](./04-test-scenarios-receiver.md), [Purchaser](./04-test-scenarios-purchaser.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md)
