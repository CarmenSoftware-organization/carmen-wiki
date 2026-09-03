---
title: ใบสั่งซื้อ (Purchase Order) — Test Scenarios
description: Test cases แยกตาม persona, scenarios ข้าม persona และ Playwright mapping สำหรับ purchase-order
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — Test Scenarios

> **At a Glance**
> **Module:** [purchase-order](/th/inventory/purchase-order) &nbsp;·&nbsp; **จำนวน scenarios ทั้งหมด:** ~10 ข้าม persona + drill-down ต่อ persona ข้ามทุก personas &nbsp;·&nbsp; **Personas ที่ครอบคลุม:** Purchaser, Procurement Manager, Vendor, Receiver, Finance, Audit / Config
> **ลำดับการรัน:** Audit / Config setup → happy paths persona หลัก → scenarios ข้าม persona
> **Drill-down ของแต่ละ persona คือ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** สำหรับชุด test-scenario ของโมดูล `purchase-order` วงจรชีวิตของ PO ครอบคลุมหก personas — Purchaser, Procurement Manager, Vendor, Receiver, Finance และ Audit / Config — และ test coverage แบ่งตาม: แต่ละ persona มีไฟล์เฉพาะ (link ใน Section 3) ที่ enumerate scenarios functional, authorization, validation, edge และ golden-journey ของ persona นั้น ไฟล์ภาพรวมนี้ให้ภาพ global: ใครอยู่ในขอบเขต, tests ของแต่ละ persona ครอบคลุมอะไรที่ระดับ headline, scenarios cross-persona handoff ที่เย็บ journeys ส่วนตัวเป็น flow end-to-end สมบูรณ์ และ mapping จากแต่ละ scenario กลับไปยังไฟล์ Playwright spec ที่ exercise

ขอบเขตของ testing บนโมดูล PO ครอบคลุมสามพื้นที่กว้าง: **functional coverage** ของทุก action ที่ใช้ได้บน PO list, detail, create wizards (Blank, From Price List, From PR), edit mode, และ post-approval toolbar; **RBAC / authorization** ของใครสามารถ perform แต่ละ action ที่แต่ละ state (Purchaser-only edit บน draft, approver-only stage actions บน `in_progress`, read-only สำหรับ Sent/Completed); และ **edge cases** รอบ ๆ empty data, no-permission users, save-without-items, dynamic skip เมื่อ seed data ไม่มี หน้านี้เวอร์ชันก่อนหน้ายังระบุ "three-way match rules ที่ PO ↔ GRN ↔ invoice handoff" ว่าอยู่ในขอบเขตด้วย แต่ไม่พบฟีเจอร์ invoice/AP-matching ใด ๆ ในซอร์สโค้ดปัจจุบัน (ดู [03-user-flow-finance.md](./03-user-flow-finance.md)) จึงตัดรายการนี้ออกที่นี่

## 2. Personas ในขอบเขต

- **Purchaser** — สร้าง POs (blank, from price list, from PR), edit drafts, submit สำหรับ approval, ส่งให้ vendor, จัดการ amendments และ close-out เป็นเจ้าของ 24+ scenarios ข้าม list, create, detail, edit, post-approval, และ golden journey
- **Procurement Manager** — ทำหน้าที่เป็น FC approver ใน seeded data เป็นเจ้าของ My-Approvals dashboard, item-level mark (Approve / Review / Reject), document-level Approve / Send Back / Reject flows, และ final-stage transmission ไปยัง vendor
- **Vendor** — ฝ่ายภายนอก ไม่มี system login และไม่มี in-system test coverage; documented สำหรับ cross-persona scenarios (transmission, acknowledgement, fulfilment, decline) และเพื่อตั้ง expectations สำหรับ personas ปลายน้ำ
- **Receiver** — Post GRN ทีละบรรทัดเทียบกับ Sent PO ขับเคลื่อน receipt-state transitions `sent → partial → completed` ยังไม่มี E2E spec เฉพาะ — partial / final receipt behaviour exercised ผ่าน cross-persona scenarios ใน Section 4
- **Finance** — ระบุไว้ใน design docs เดิมว่าเป็นเจ้าของ three-way-match / AP; **ยังไม่ยืนยัน** ในซอร์สโค้ดปัจจุบัน ไม่มี invoice-capture screen, AP-posting endpoint, หรือ spec file เฉพาะอยู่เลย — ดูคำแก้ไขที่ [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)
- **Audit / Config** — Auditor (review activity log แบบ read-only) และ System Administrator (workflow-stage / numbering configuration แบบ generic ที่ใช้ร่วมกันข้ามชนิดเอกสาร ไม่ใช่เฉพาะ PO) ไม่พบ audit-workspace เฉพาะหรือ configuration-workbench เฉพาะ PO ที่ยืนยันได้ — ดู [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md)

## 3. ไฟล์ Test ต่อ Persona

- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Vendor scenarios](./04-test-scenarios-vendor.md)
- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Scenarios Cross-Persona / Handoff

Scenarios ด้านล่าง trace PO ข้าม personas หลายตัว แต่ละ row anchor ลำดับ handoff กับ document state ที่ boundary และ expected end state มาจากตาราง handoff ใน [03-user-flow.md](./03-user-flow.md) Section 4

| # | Scenario | Personas ตามลำดับ | เงื่อนไขก่อน | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-PO-01 | Full happy path (from PR) | Purchaser → Procurement Manager → Vendor → Receiver | PR ที่อนุมัติแล้วมีอยู่; vendor reachable | `completed` (ทุกบรรทัดรับครบ) |
| X-PO-02 | Manual PO (no PR linkage) | Purchaser → Procurement Manager → Vendor → Receiver | Vendor ในแคตตาล็อก; pricelist optional; ไม่มี source PR | `completed` (manual flow; ไม่มี PR consumed) |
| X-PO-03 | Partial receipt แล้ว final balance | Purchaser → Procurement Manager → Vendor → Receiver (partial GRN) → Receiver (second GRN) | PO `sent`; vendor ส่งใน 2 shipments | `completed` ผ่าน `partial` (state ข้าม `sent → partial → completed`) |
| X-PO-04 | ~~Three-way match quantity discrepancy~~ — ตัดออก | — | ไม่พบฟีเจอร์ invoice/AP-matching ใด ๆ ในซอร์สโค้ดปัจจุบัน (ดู [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)) | n/a |
| X-PO-05 | Amendment cycle บน Sent PO | Purchaser → Procurement Manager (approve amendment) → Vendor | PO `sent`; vendor accept amendment | PO `sent` พร้อม revision history (`cancelled_qty` / note เท่านั้น ตาม `PO_VAL_016`) |
| X-PO-06 | การปฏิเสธที่ approval stage | Purchaser → Procurement Manager (reject) | PO `in_progress`; reason optional | `voided` (direct, terminal; workflow terminated) |
| X-PO-07 | Cancel ก่อนมี GRN posted | Purchaser (cancel) | PO `draft`, `in_progress`, หรือ `sent`; ไม่มี GRN เทียบกับบรรทัดใด ๆ | `closed` — แก้ไขจาก framing เดิม "void mid-flight"; ไม่มี action "void" แยกต่างหากจาก reject และ reject ถึง `voided` ได้จาก `in_progress` เท่านั้น |
| X-PO-08 | Vendor ไม่สามารถ fulfil หลัง transmission | Purchaser → Procurement Manager → Vendor (cannot fulfil) | PO `sent` | `closed` ผ่าน **Cancel** หรือ **Close** — ไม่ใช่ `voided` (ไม่มี path จาก `sent` ไปยัง `voided` ในซอร์สโค้ดปัจจุบัน) |
| X-PO-09 | ปิด partial PO (vendor ไม่สามารถ supply remainder) | Purchaser → Procurement Manager → Vendor → Receiver (partial GRN) → Inventory Manager (close) | PO `partial`; outstanding balance treat เป็น cancelled | `closed` (qty ที่เหลือเขียนเป็น `cancelled_qty`) |
| X-PO-10 | Send-back ระหว่าง approval (item-level Review) | Purchaser → Procurement Manager (Send Back) → Purchaser (revise) → Procurement Manager (approve) | PO `in_progress`; รายการสินค้าหนึ่งหรือมากกว่ามาร์ก Review | `sent` (หลัง revise + re-approve); `po_status` ยังคงเป็น `in_progress` ตลอด send-back เอง แก้ไขจาก framing เดิม "returns to draft" |

## 5. E2E Test Mapping

มี Playwright specs สามตัวสำหรับโมดูล PO ภายใต้ `../carmen-inventory-frontend-e2e/tests/` เฉพาะ Purchaser และ Procurement Manager (FC Approver) personas เท่านั้นที่มี specs เฉพาะวันนี้ ไฟล์ persona Vendor, Receiver, Finance และ Audit / Config note "ไม่มี E2E spec เฉพาะ — ดู `401-po.spec.ts` ที่ใช้ร่วมกันสำหรับ PO list coverage ทั่วไป" และพึ่งพา cross-persona scenarios ใน Section 4 เพื่อ anchor expected behaviour สำหรับ automation ปลายน้ำ

### 5.1 `401-po.spec.ts` — General / shared coverage

Mixed-persona spec รันทั้ง `purchase@blueledgers.com` (Purchaser) และ `requestor@blueledgers.com` (no-PO-permission negative cases) ครอบคลุม:

- TC-PO-010001 — สร้าง PO จาก PR ที่อนุมัติ (happy path)
- TC-PO-010003 — Edge case เมื่อไม่มี approved PRs
- TC-PO-010004 — Negative: invalid vendor assignment
- List-view fixtures, search, filter, sort scenarios ที่ใช้โดยทุก personas
- Backend / time-based scenarios marked `SKIP_NOTE_BACKEND` / `SKIP_NOTE_TIME` (documented แต่ไม่ executable ผ่าน UI)

Cross-persona coverage: X-PO-02 (manual PO entry point), X-PO-01 (PR-sourced PO entry point), list/search/filter scenarios ทั่วไปที่ใช้โดยทุก persona ปลายน้ำ

### 5.2 `402-po-purchaser-journey.spec.ts` — Purchaser persona

รันเป็น `purchase@blueledgers.com` มาจาก `docs/persona-doc/Purchase Order/Purchaser/INDEX.md` ครอบคลุม Steps 1–5 บวก Golden Journey (TC-PO-060101 ถึง TC-PO-060901):

- Step 1 — PO list (load, tab switch, filter, search, sort)
- Step 2 — Create PO ผ่าน Blank / From Price List / From PR wizards
- Step 3 — PO detail loads (Draft) พร้อม header + items + Item Details panel
- Step 4 — Edit mode (modify qty, add line, cancel edit, submit Draft, delete in-progress)
- Step 5 — Post-approval (Send to Vendor, Close with received items, Close without received items)
- Golden Journey TC-PO-060901 — full create → submit → FC approve (cross-context) → Send to Vendor

Cross-persona coverage: X-PO-01 (happy path PR-sourced), X-PO-02 (manual flow), X-PO-05 (amendment ผ่าน edit mode), X-PO-07 (Close-without-received-items path, landing บน `closed`), X-PO-09 (close partial)

### 5.3 `403-po-approver-journey.spec.ts` — Procurement Manager (FC Approver) persona

รันเป็น `fc@blueledgers.com` มาจาก `docs/persona-doc/Purchase Order/Approver/INDEX.md` ครอบคลุม Steps 1–3 บวก Golden Journey (TC-PO-070101 ถึง TC-PO-070901):

- Step 1 — My Approval dashboard (load, PO filter tab, row click to detail)
- Step 2 — PO detail (FC view) — header read-only, Edit + Comment visible, status badge `IN PROGRESS`
- Step 3 — Approval actions: item-level mark (Approve / Review / Reject) + document-level Approve / Send Back / Reject + edit-mode cancel
- Golden Journey TC-PO-070901 — full open → edit → mark all approved → document approve → hard assertion เป็น badge ที่ match `/approved|sent/i` (สถานะที่ persist จริงคือ `sent`; ไม่มีสถานะ `approved` แยกต่างหากใน `enum_purchase_order_doc_status` — regex ของ test เพียงยอมรับทั้งสองคำ)

Cross-persona coverage: X-PO-01 / X-PO-02 (approval leg), X-PO-06 (rejection), X-PO-10 (Send-Back ระหว่าง approval)

## 6. แหล่งอ้างอิง

- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 (แหล่ง handoff)
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 (posting rules — กฎ three-way-match ที่นั่นระบุว่ายังไม่ implement)
