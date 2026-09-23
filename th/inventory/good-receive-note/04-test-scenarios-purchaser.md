---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Purchaser
description: เคสทดสอบของ Purchaser (happy path, permission, validation, edge case) สำหรับ good-receive-note
published: true
date: '2026-09-23T01:30:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser (Procurement Officer + Department Manager) &nbsp;·&nbsp; **โมดูล:** [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; **จำนวน scenario:** ~12
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** map ไปยัง `501-grn.spec.ts` ใน `../carmen-inventory-frontend-e2e/`
> **ตรวจสอบซ้ำ 2026-09-22:** PO เลื่อนตอน **commit** ไม่ใช่ตอน save; สถานะ PO คือ `approved` / `sent_or_print` / `partial` / `completed`; ตอนนี้มีการตรวจ price-deviation เทียบ **ราคา PO** ตอน save (`GRN_VAL_007`) — ยังไม่มีการตรวจ pricelist ไม่มี `accepted_qty` ไม่มี three-way match และไม่มี segregation of duties

> **ความครอบคลุมที่รันได้:** `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (76 case; กลุ่มที่เกี่ยวกับ Purchaser list ใน §5) และ `docs/test-cases/gaps/501-grn-core-gap.md` (62) — case permission-denial ใช้ fixture บทบาท Requestor

หน้านี้จับ test scenario ที่ persona Purchaser (**Purchaser / Procurement Officer** ที่ออก PO ต้นทาง บวก subset **Department Manager**) ขับโดยตรงในโมดูล `good-receive-note` Purchaser เป็นผู้มีส่วนร่วมแบบ **review-only** บน GRN — **ไม่** สร้าง GRN ที่ dock, **ไม่** save และ **ไม่** commit (commit คือสิ่งที่โพสต์ inventory และเลื่อน PO — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)) การ scope "PO ของตัวเอง" ด้านล่างเป็นธรรมเนียมการทำงาน — backend ไม่ได้กรอง list GRN ตาม `buyer_id`

## 1. Happy Path

| # | Scenario | เงื่อนไขก่อน | ขั้นตอน | ผลที่คาด |
| - | -------- | ------------- | ----- | -------- |
| PUR-HP-01 | เปิด GRN ที่ `saved` / `committed` บน PO ของตัวเองในโหมด read | Purchaser เป็น `buyer_id` ของ PO `PO-X` ที่ `po_status ∈ {sent_or_print, partial}`; Receiver ขับ GRN บน `PO-X` ไปถึง `committed` (โพสต์ inventory เลื่อน PO แล้ว) | 1. เปิด Receiving History tab ของโมดูล PO สำหรับ `PO-X` (หรือ list **Reference documents** ของ GRN, `GET …/ref`) 2. คลิกเข้าแถว GRN | GRN read view เปิด; header แสดง `doc_status`, vendor, `grn_date`, สกุลเงิน อัตราแลกเปลี่ยน; แถวบรรทัดแสดง `order_qty` / `order_price`, `received_qty` / `received_price`, `foc_qty`, `expired_at`; คอลัมน์ action แสดง link เอกสารต้นทาง; แท็บ Stock Movement list lot; ไม่มี affordance edit, save, commit หรือ void แสดงสำหรับผู้ใช้ที่ไม่มี permission key ที่เกี่ยวข้อง Maps to TC-GRN-010001 |
| PUR-HP-02 | Review การรับของสะอาด — ไม่ต้องติดต่อ vendor | GRN ที่ committed บน PO ของตัวเอง `PO-X` ที่ทุกบรรทัด `received_qty = order_qty` | 1. เปิด GRN 2. เทียบคอลัมน์ที่สั่ง / ที่รับระดับบรรทัด | ไม่มี action ฝั่ง vendor; ไม่มีการแก้ไข PO; เอกสาร GRN เอง **ไม่** ถูกแก้ไข; บรรทัด PO เปลี่ยนสถานะตอน commit ของ Receiver (`sent_or_print → completed`) |
| PUR-HP-03 | Review การรับของขาดและตาม vendor | GRN ที่ committed บน PO ของตัวเอง `PO-Y` (`order_qty = 10`) มี `received_qty = 6`; Receiver เขียน comment variance; `po_status = partial` | 1. เปิด GRN 2. ยืนยัน `received_qty (6) < order_qty (10)` 3. อ่าน comment ของ Receiver 4. ติดต่อ vendor นอกเอกสาร GRN 5. เขียน comment บันทึกคำตอบของ vendor | การตาม vendor เกิดนอกเอกสาร; GRN เองไม่เปลี่ยน; PO ต้นทางคงอยู่ที่ `po_status = partial` โดย pending = 4; เมื่อของรอบตามมาถึง Receiver commit GRN ใบที่สองซึ่งเลื่อน `received_qty` เป็น 10 และเปลี่ยน `po_status → completed` |
| PUR-HP-04 | การป้องกัน price-deviation ก่อนเอกสารมาถึงการ review | สินค้า `price_deviation_limit = 10`; บรรทัด PO `order_price = ฿100`; Receiver กรอก `received_price = ฿120` | 1. Receiver คลิก **Save** | เอกสารไม่มีวันถึง `saved` — `GRN_DEVIATION_LIMIT_EXCEEDED` (`kind = price`) ถูกคืนตอน save ดังนั้น Purchaser ไม่ถูกขอให้ review การรับของที่ราคาเกิน ด้วย `received_price = ฿108` จะ save ได้และ Purchaser เห็น variance 8 % บนบรรทัด |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| PUR-PERM-01 | Purchaser เปิด GRN ในโหมด read | **Allow** ด้วย `procurement.goods_received_note.view` (`GET …/:id`, guard `goodReceivedNote.findOne`) header, บรรทัด, Stock Movement (เมื่อ committed แล้ว), ไฟล์แนบ และ activity log มองเห็นได้; ปุ่ม edit / save / commit / void ถูกซ่อนเมื่อผู้ใช้ไม่มี `.update` / `.commit` / `.delete` Maps to TC-GRN-010001 |
| PUR-PERM-02 | Purchaser พยายามเปิด GRN ที่ PO ต้นทางตนเอง**ไม่ได้**เป็นเจ้าของ | **backend อนุญาต** — ไม่มี scope `buyer_id` บน `findAll` / `findOne` (ตรวจซ้ำ 2026-09-22) ผู้ใช้ที่**ไม่มี** `procurement.goods_received_note.view` ได้ `403` จาก gateway guard และ route list redirect Maps to TC-GRN-010003 (permission denial ไม่ใช่ ownership) |
| PUR-PERM-03 | Purchaser พยายามแก้ไข header / บรรทัดของ GRN | **Deny ด้วย permission key เท่านั้น** หากไม่มี `.update` `PATCH …/:id` และ endpoint detail คืน `403`; ไม่มีข้อความตามชื่อ role และไม่มีกฎ segregation-of-duties — Purchaser ที่ถือ `.update` ด้วยสามารถแก้ `draft` ได้ Maps to TC-GRN-080005 |
| PUR-PERM-04 | Purchaser พยายามสร้าง GRN | **Deny ด้วย permission key** (`goodReceivedNote.create` → `403`); ปุ่ม **New** ถูกซ่อนหากไม่มี `.create` |
| PUR-PERM-05 | Purchaser พยายาม save หรือ commit GRN ที่ `saved` | **Deny ด้วย permission key** — ทั้ง `PATCH …/save` และ `PATCH …/commit` อยู่หลัง `goodReceivedNote.commit` (`403` หากไม่มี) ไม่มีข้อความ "Inventory Manager role" Maps to TC-GRN-110002 |

## 3. Validation / Error

| # | Scenario | Trigger | ข้อผิดพลาดที่คาด |
| - | -------- | ------- | -------------- |
| PUR-VAL-01 | Purchaser ที่ไม่มี commit key เรียก endpoint commit โดยตรง | GRN ที่ `saved` อยู่บน PO ของตัวเอง `PO-X`; Purchaser (ไม่มี `procurement.goods_received_note.commit`) เรียก `PATCH …/commit` | **Reject 403** จาก `AppIdGuard('goodReceivedNote.commit')`; `doc_status` คงเป็น `saved` Maps to TC-GRN-110002 |
| PUR-VAL-02 | Purchaser พยายามแก้บรรทัดบน GRN ที่ `saved` | GRN ที่ `saved` มี `received_qty = 10`; Purchaser เรียก `PATCH …/:id/details/:detail_id` (หรือ delete detail) | **Reject** — `GRN_NON_DRAFT_NO_UPDATE_DETAIL` / `_DELETE_DETAIL` (400) ไม่ว่าจะมีสิทธิ์หรือไม่ เพราะ endpoint detail เป็น `draft`-only; เส้นทางที่ถูกต้องคือ comment และขอให้ Receiver void แล้วออกใหม่ (หรือหลัง commit ให้ออก credit note) |

## 4. Edge Case

| # | Scenario | เงื่อนไข | ผลที่คาด |
| - | -------- | --------- | -------- |
| PUR-EDGE-01 | การ review การรวมหลาย PO — GRN เดียว span สอง PO ของ Purchaser | vendor เดียวกันส่งของในรถคันเดียวครอบคลุม `PO-A` (หนึ่งบรรทัด pending 4) และ `PO-B` (สองบรรทัด pending 6 แต่ละบรรทัด); Receiver รวมเป็น GRN เดียวสามบรรทัดตาม RCV-EDGE-04 (ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)) และ commit | การเปิด GRN แสดงทั้งสามบรรทัด; list **Reference documents** (`GET …/ref`) แสดงทั้งสอง PO; variance ของบรรทัดที่ขาดถูก scope ไปยังบรรทัด PO ที่มันอยู่ `received_qty` ของทั้งสอง PO เลื่อนในธุรกรรม commit เดียวกัน Maps to TC-GRN-040002, TC-GRN-040004 (stub) และ gap `501-grn-from-po-gap.md` |
| PUR-EDGE-02 | Credit note หลัง commit — หนึ่งสินค้าต่อ GRN เพียงครั้งเดียว | GRN ที่ committed มีสินค้า P1 และ P2; มี credit note สำหรับ P1 อยู่แล้ว | `GET …/good-received-notes/vendor/:vendor_id/cn` ยัง list GRN นี้ (P2 ยังไม่ถูก credit); หลังจาก P2 ถูก credit ด้วย GRN หลุดจาก list (`findFullyCreditedGrnIds`, `good-received-note.service.ts:494-552`); credit note ใบที่สองสำหรับ P1 บน GRN เดียวกันถูกปฏิเสธโดยโมดูล credit-note |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona ที่ pivot บน Purchaser
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — แหล่ง happy-path สำหรับส่วน 1 ข้างต้น
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — ชุด test ต้นทางที่สร้าง save และ commit (โพสต์) GRN
- Sibling: [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) — หน้าแก้ไข: เหตุผลที่ไม่มี test scenario สำหรับ handoff credit-note / three-way-match
- กฎธุรกิจที่ตรวจสอบ: [02-business-rules.md](./02-business-rules.md) — การแยกหน้าที่ (`GRN_AUTH_010` ทำเครื่องหมายว่ายังไม่ยืนยันในรอบนี้) อ้างใน PUR-PERM-03, PUR-VAL-01, PUR-VAL-02
- Cross-link: [purchase-order](/th/inventory/purchase-order) — โมดูลต้นทางที่ persona นี้เป็นเจ้าของ; แหล่งของ `order_price`, `po_status` (`approved` / `sent_or_print` / `partial` / `completed`) และ activity log
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (76 case) กลุ่มที่เกี่ยวกับ Purchaser: **TC-GRN-010001** (View GRN List), **TC-GRN-010003** (Insufficient Permissions), **TC-GRN-080005** (Edit Line Item — denial), **TC-GRN-110002** (No Permission to Commit), **TC-GRN-040002 / 040004** (Create from Multiple POs — stub; case จริงของ wizard อยู่ใน `docs/test-cases/gaps/501-grn-from-po-gap.md`)
