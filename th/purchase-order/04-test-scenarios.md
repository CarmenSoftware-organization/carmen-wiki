---
title: ใบสั่งซื้อ — กรณีทดสอบ
description: กรณีทดสอบแยกตาม persona, กรณีข้าม persona, และการเชื่อมโยงกับ Playwright สำหรับโมดูล purchase-order
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ — กรณีทดสอบ

## 1. ภาพรวม

หน้านี้คือ **จุดเริ่มต้นภาพรวม** ของชุดเอกสารกรณีทดสอบสำหรับโมดูล `purchase-order` วงจรชีวิตของ PO ครอบคลุม persona หกราย ได้แก่ Purchaser, Procurement Manager, Vendor, Receiver, Finance, และ Audit / Config และความครอบคลุมของการทดสอบถูกแบ่งตาม persona เหล่านี้ โดยแต่ละ persona มีไฟล์ของตัวเอง (ลิงก์ใน Section 3) ที่ระบุกรณีทดสอบเชิง functional, authorization, validation, edge และ golden journey ของ persona นั้น ๆ หน้าภาพรวมนี้ให้มุมมองโดยรวม คือ ใครอยู่ใน scope, แต่ละ persona ครอบคลุมอะไรในระดับหัวข้อ, กรณีส่งต่อข้าม persona ที่เชื่อมโยงเส้นทางแต่ละสาย ให้กลายเป็น flow ปลายทางถึงปลายทาง และการเชื่อมโยงแต่ละ scenario กลับไปยังไฟล์ Playwright spec ที่ใช้ทดสอบ

ขอบเขตการทดสอบของโมดูล PO ครอบคลุมสี่ด้านหลัก ได้แก่ **functional coverage** ของทุก action ที่อยู่ในหน้า list, detail, create wizards (Blank, From Price List, From PR), edit mode, และ post-approval toolbar; **RBAC / authorization** ของผู้ที่ทำ action ได้ในแต่ละ state (Purchaser แก้ไขได้เฉพาะ draft, FC อนุมัติได้เฉพาะ `in_progress`, read-only สำหรับ Sent/Completed); **edge cases** เกี่ยวกับข้อมูลว่างเปล่า ผู้ใช้ไม่มีสิทธิ์ การ save โดยไม่มี item การ skip แบบ dynamic เมื่อไม่มี seed data; และ **three-way match** ที่จุดส่งต่อ PO ↔ GRN ↔ invoice ซึ่งครอบคลุม persona Receiver และ Finance และส่วนใหญ่ถูกทดสอบผ่านกรณีข้าม persona ใน Section 4

## 2. Personas ใน Scope

- **Purchaser** — สร้าง PO (blank, จาก price list, จาก PR), แก้ไข draft, submit เพื่อขออนุมัติ, ส่งให้ vendor, จัดการการแก้ไขและการปิดเอกสาร เป็นเจ้าของกรณีทดสอบ 24+ ครอบคลุม list, create, detail, edit, post-approval, และ golden journey
- **Procurement Manager** — ทำหน้าที่เป็น FC approver ใน seed data เป็นเจ้าของ dashboard My-Approvals, การทำเครื่องหมายระดับ item (Approve / Review / Reject), การ Approve / Send Back / Reject ระดับเอกสาร, และการส่งให้ vendor ใน stage สุดท้าย
- **Vendor** — บุคคลภายนอก ไม่มี login ในระบบและไม่มี coverage ใน E2E ระบุไว้สำหรับกรณีข้าม persona (การส่ง, การตอบรับ, การจัดส่ง, การปฏิเสธ) และเพื่อกำหนดความคาดหวังสำหรับ persona ปลายน้ำ
- **Receiver** — Post GRN ทีละรายการเทียบกับ PO ที่ Sent ขับเคลื่อน state transition `sent → partial → completed` ยังไม่มี E2E spec เฉพาะ — การรับแบบ partial / final ถูกทดสอบผ่านกรณีข้าม persona ใน Section 4
- **Finance** — รัน three-way match (PO ↔ GRN ↔ invoice), จัดการ currency / FX, และ post AP ยังไม่มี E2E spec เฉพาะ — coverage ฝั่ง invoice อยู่ใน spec ของโมดูล AP และอ้างอิงผ่าน handoff scenario
- **Audit / Config** — Auditor (อ่านเท่านั้นสำหรับ activity log) และ System Administrator (workflow stage, RBAC, การ numbering) พฤติกรรมส่วนใหญ่เกิดที่ระยะ configuration ไม่ได้ถูกขับผ่าน UI ของโมดูล PO ระบุไว้ใน Section 3 เพื่อความครบถ้วน และอ้างอิงข้ามจากกรณีข้าม persona เกี่ยวกับ void / amendment

## 3. ไฟล์กรณีทดสอบรายตาม Persona

- [กรณีทดสอบ Purchaser](./04-test-scenarios-purchaser.md)
- [กรณีทดสอบ Procurement Manager](./04-test-scenarios-procurement-manager.md)
- [กรณีทดสอบ Vendor](./04-test-scenarios-vendor.md)
- [กรณีทดสอบ Receiver](./04-test-scenarios-receiver.md)
- [กรณีทดสอบ Finance](./04-test-scenarios-finance.md)
- [กรณีทดสอบ Audit / Config](./04-test-scenarios-audit-config.md)

## 4. กรณีข้าม Persona / Handoff

ตารางด้านล่างไล่ตาม PO ที่ข้ามผ่านหลาย persona แต่ละแถวยึด sequence ของ handoff ไว้กับ state ของเอกสาร ณ จุดเปลี่ยน และ state สุดท้ายที่คาดหวัง ข้อมูลถูก derive มาจากตาราง handoff ใน [03-user-flow.md](./03-user-flow.md) Section 4

| # | Scenario | Personas เรียงลำดับ | เงื่อนไขก่อนหน้า | State สุดท้ายที่คาดหวัง |
| - | -------- | ------------------- | ----------------- | ----------------------- |
| X-PO-01 | Happy path เต็มรูปแบบ (มูลค่าสูง, จาก PR) | Purchaser → Procurement Manager → Vendor → Receiver → Finance | มี PR ที่ approved; มูลค่าเข้าเกณฑ์มูลค่าสูง; vendor ติดต่อได้ | `completed` (ทุก line รับครบ; three-way match post แล้ว) |
| X-PO-02 | Manual PO (ไม่มี PR linkage) | Purchaser → Procurement Manager → Vendor → Receiver → Finance | Vendor อยู่ใน catalogue; pricelist optional; ไม่มี PR ต้นทาง | `completed` (สาย manual; ไม่มี PR ถูกใช้) |
| X-PO-03 | รับแบบ partial แล้วตามด้วยยอดที่เหลือ | Purchaser → Procurement Manager → Vendor → Receiver (GRN partial) → Receiver (GRN ครั้งที่สอง) → Finance | PO `sent`; vendor ส่งของสองเที่ยว | `completed` ผ่าน `partial` (state ข้าม `sent → partial → completed`) |
| X-PO-04 | Three-way match จำนวนไม่ตรง | Purchaser → Procurement Manager → Vendor → Receiver → Finance (flag) → Purchaser (แก้ไข) | จำนวนใน invoice ≠ จำนวนใน GRN อย่างน้อยหนึ่ง line | Bounce-back ไป Purchaser; PO ยังคง `partial` หรือ `completed` จนกว่าจะถูก reconcile |
| X-PO-05 | Amendment cycle บน PO ที่ Sent | Purchaser → Procurement Manager (อนุมัติ amendment) → Vendor (re-transmit) | PO `sent`; vendor ยอมรับ amendment | PO `sent` พร้อม revision history; vendor ตอบรับใหม่ |
| X-PO-06 | ปฏิเสธมูลค่าสูงใน stage สุดท้าย | Purchaser → Procurement Manager (reject) | PO `in_progress` ที่ stage สุดท้าย; ระบุเหตุผล | `voided` (workflow ยุติ; เหตุผลถูกบันทึก) |
| X-PO-07 | Void กลางทาง (ยังไม่มี GRN) | Purchaser → Procurement Manager (void) | PO `in_progress` หรือ `sent`; ยังไม่มี GRN บน line ใด ๆ; ระบุเหตุผล | `voided` |
| X-PO-08 | Vendor ปฏิเสธหลังตอบรับแล้ว | Purchaser → Procurement Manager → Vendor (ปฏิเสธ) | PO `sent`; vendor ไม่สามารถจัดส่งได้ | Bounce-back ไป Purchaser (amend) หรือ `voided` (cancel) |
| X-PO-09 | ปิด PO บางส่วน (vendor ส่งของที่เหลือไม่ได้) | Purchaser → Procurement Manager → Vendor → Receiver (GRN partial) → Inventory Manager (ปิด) | PO `partial`; ยอดคงค้างถูกถือเป็น cancel | `closed` (ยอดที่เหลือถูกเขียนเป็น `cancelled_qty`) |
| X-PO-10 | Send-back ระหว่างอนุมัติ (Review ระดับ item) | Purchaser → Procurement Manager (Send Back) → Purchaser (แก้ไข) → Procurement Manager (อนุมัติ) | PO `in_progress`; รายการ line อย่างน้อยหนึ่งรายการถูกทำเครื่องหมาย Review | `sent` (หลังแก้ไข + re-approve) |

## 5. การเชื่อมโยงกับ E2E

มี Playwright spec สามไฟล์สำหรับโมดูล PO ภายใต้ `../carmen-inventory-frontend-e2e/tests/` ปัจจุบันเฉพาะ persona Purchaser และ Procurement Manager (FC Approver) ที่มี spec ของตัวเอง ส่วน persona Vendor, Receiver, Finance, และ Audit / Config จะระบุในไฟล์ของตนว่า "ยังไม่มี E2E spec เฉพาะ — ดู `401-po.spec.ts` ที่ใช้ร่วม" และยึดกรณีข้าม persona ใน Section 4 เป็นจุดตรึงพฤติกรรมที่คาดหวังสำหรับการทำ automation ในอนาคต

### 5.1 `401-po.spec.ts` — Coverage ทั่วไป / ใช้ร่วม

Spec ที่ใช้หลาย persona รันทั้ง `purchase@blueledgers.com` (Purchaser) และ `requestor@blueledgers.com` (ผู้ใช้ที่ไม่มีสิทธิ์ PO — ใช้ทดสอบ negative) ครอบคลุม:

- TC-PO-010001 — Create PO จาก approved PR (happy path)
- TC-PO-010003 — Edge case เมื่อไม่มี approved PR
- TC-PO-010004 — Negative: vendor assignment ไม่ถูกต้อง
- Fixture หน้า list, search, filter, sort ที่ persona ทุกตัวใช้ร่วมกัน
- กรณี backend / time-based ที่ติดป้าย `SKIP_NOTE_BACKEND` / `SKIP_NOTE_TIME` (ระบุไว้แต่ไม่สามารถ run ผ่าน UI ได้)

ครอบคลุมข้าม persona: X-PO-02 (จุดเริ่ม manual), X-PO-01 (จุดเริ่ม PR-sourced), กรณี list/search/filter ที่ persona ปลายน้ำใช้ร่วม

### 5.2 `402-po-purchaser-journey.spec.ts` — Persona Purchaser

รันด้วย `purchase@blueledgers.com` มาจาก `docs/persona-doc/Purchase Order/Purchaser/INDEX.md` ครอบคลุม Step 1–5 บวก Golden Journey (TC-PO-060101 ถึง TC-PO-060901):

- Step 1 — หน้า list ของ PO (โหลด, สลับแท็บ, filter, search, sort)
- Step 2 — สร้าง PO ผ่าน Blank / From Price List / From PR wizard
- Step 3 — หน้า detail ของ PO (Draft) โหลดพร้อม header + items + panel Item Details
- Step 4 — Edit mode (แก้ qty, เพิ่ม line, cancel edit, submit Draft, delete in-progress)
- Step 5 — Post-approval (Send to Vendor, Close ที่มีของรับแล้ว, Close ที่ยังไม่มีของรับ)
- Golden Journey TC-PO-060901 — create → submit → FC อนุมัติ (cross-context) → Send to Vendor ครบถ้วน

ครอบคลุมข้าม persona: X-PO-01 (happy path จาก PR), X-PO-02 (สาย manual), X-PO-05 (amendment ผ่าน edit mode), X-PO-07 (void ผ่านสาย Close-ไม่มีการรับ), X-PO-09 (close partial)

### 5.3 `403-po-approver-journey.spec.ts` — Persona Procurement Manager (FC Approver)

รันด้วย `fc@blueledgers.com` มาจาก `docs/persona-doc/Purchase Order/Approver/INDEX.md` ครอบคลุม Step 1–3 บวก Golden Journey (TC-PO-070101 ถึง TC-PO-070901):

- Step 1 — Dashboard My Approval (โหลด, แท็บ filter PO, คลิก row เข้า detail)
- Step 2 — หน้า detail ของ PO (มุมมอง FC) — header read-only, ปุ่ม Edit + Comment visible, status badge `IN PROGRESS`
- Step 3 — Action การอนุมัติ: mark ระดับ item (Approve / Review / Reject) + Approve / Send Back / Reject ระดับเอกสาร + cancel edit mode
- Golden Journey TC-PO-070901 — open → edit → mark ทั้งหมด approved → document approve → status `APPROVED / SENT` ครบถ้วน

ครอบคลุมข้าม persona: X-PO-01 / X-PO-02 (ขา approval), X-PO-06 (ปฏิเสธมูลค่าสูง), X-PO-07 (void ผ่านสาย reject), X-PO-10 (Send-Back ระหว่างอนุมัติ)

## 6. อ้างอิง

- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`
- ไฟล์พี่น้อง: [03-user-flow.md](./03-user-flow.md) Section 4 (แหล่งของ handoff)
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) Section 5 (กฎ posting + three-way match)
