---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Purchaser
description: เคสทดสอบของ Purchaser (happy path, permission, validation, edge case) สำหรับ good-receive-note
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-19T23:55:00.000Z
tags: good-receive-note, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser (Procurement Officer + Department Manager) &nbsp;·&nbsp; **โมดูล:** [good-receive-note](/th/inventory/good-receive-note) &nbsp;·&nbsp; **จำนวน scenario:** ~12
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** map ไปยัง `501-grn.spec.ts` ใน `../carmen-inventory-frontend-e2e/`
> **แก้ไขในรอบนี้ (2026-07-15):** ตัดการอ้างอิง `accepted_qty` ออก (ไม่มีฟิลด์นี้อยู่), scenario ตรวจ pricelist-deviation (ไม่พบโค้ดที่ตรงกันในโมดูล GRN), scenario handoff Finance/credit note (ไม่พบฟีเจอร์ three-way-match — ดู [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)) และเปลี่ยน label การแยกหน้าที่เป็น "ยังไม่ยืนยัน" แทน "บังคับใช้แล้ว"

หน้านี้จับ test scenario ที่ persona Purchaser (**Purchaser / Procurement Officer** ที่ออก PO ต้นทาง บวก subset **Department Manager**) ขับเคลื่อนโดยตรงในโมดูล `good-receive-note` Purchaser เป็นผู้เข้าร่วมแบบ **review-only** บน GRN — พวกเขา **ไม่** สร้าง GRN ที่ dock, **ไม่** บันทึกรายการบรรทัด (การ save คือสิ่งที่ post inventory และเลื่อน PO — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)) และ **ไม่** commit หรือแก้ไขเอกสาร GRN ในสถานะใด

## 1. Happy Path

| # | Scenario | เงื่อนไขก่อน | ขั้นตอน | ผลที่คาด |
| - | -------- | ------------- | ----- | -------- |
| PUR-HP-01 | เปิด GRN ที่ `saved` / `committed` บน PO ของตัวเองในโหมด read | Purchaser `purchase@blueledgers.com` เป็น `buyer_id` ของ PO `PO-X` ที่ `po_status ∈ {sent, partial}`; Receiver save GRN กับ `PO-X` ไปที่ `saved` แล้ว (ซึ่ง post inventory และเลื่อน PO ไปแล้ว) | 1. เปิด Receiving History tab ของโมดูล PO สำหรับ `PO-X` 2. คลิกเข้าแถว GRN | GRN read view เปิด; header แสดง `doc_status`, `vendor_id`, `receipt_date`, currency; บรรทัดแสดง `order_qty`, `received_qty` และยอด pending คงเหลือบน PO ต้นทาง; ไม่มีการ edit, save, commit หรือ void affordance ปรากฏ Map ไปยัง TC-GRN-010001 |
| PUR-HP-02 | Review การรับของสะอาด — ไม่ต้องติดต่อ vendor | GRN บน PO ของตัวเอง `PO-X` ที่ทุกบรรทัดเข้าเงื่อนไข `received_qty = pending_qty` | 1. เปิด GRN จาก Receiving History tab 2. เทียบคอลัมน์ `received_qty` / `pending_qty` ระดับบรรทัด | ไม่มี action ฝั่ง vendor fire; ไม่มี PO amendment ขึ้น; เอกสาร GRN เอง **ไม่** ถูกแก้ไข; บรรทัด PO เลื่อนโดยธรรมชาติตอน Receiver save (`sent → partial → completed`) |
| PUR-HP-03 | Review การรับของขาดและตาม vendor | GRN บน PO ของตัวเอง `PO-Y` (`order_qty = 10`) ด้วย `received_qty = 6` บนบรรทัด; Receiver เขียน variance comment; `po_status = sent → partial` | 1. เปิด GRN 2. ยืนยัน `received_qty (6) < pending_qty (10)` 3. อ่าน comment ของ Receiver 4. ติดต่อ vendor นอกเอกสาร GRN (อีเมล / vendor portal) 5. เขียน comment บันทึกการตอบสนองของ vendor | การตาม vendor fire นอกเอกสาร; GRN เองไม่เปลี่ยน — ไม่มีการแก้ไข header / บรรทัดโดย Purchaser; PO source ยังที่ `po_status = partial` พร้อม pending = 4; เมื่อ shipment ตามมาถึง Receiver สร้าง GRN ที่สองซึ่งเลื่อน `received_qty` เป็น 10 และพลิก `po_status → completed` |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| PUR-PERM-01 | Purchaser เปิด GRN ในโหมด read ที่ตนเป็นเจ้าของ PO ต้นทาง | **Allow** endpoint read ของ GRN เปิดให้ผู้ใช้ที่ระบุด้วย `tb_purchase_order.buyer_id` สำหรับทุกบรรทัดบน GRN ที่บรรจุ `purchase_order_detail_id` ชี้ไปยัง PO ที่ตนเป็นเจ้าของ Header, บรรทัด, lot, attachment และ activity log ทั้งหมดมองเห็นได้; **ไม่มี** edit, save, commit, หรือ void affordance ปรากฏ Map ไปยัง TC-GRN-010001 |
| PUR-PERM-02 | Purchaser พยายามเปิด GRN ที่ PO ต้นทางตนเอง**ไม่ได้**เป็นเจ้าของ | **Deny — ขอบเขต** deep-link โดยตรงไปยัง GRN detail return `403` / redirect กลับ list GRN โดยแถวถูกกรองออก Map ไปยัง TC-GRN-010003 |
| PUR-PERM-03 | Purchaser พยายามแก้ไข header / บรรทัดของ GRN | **Deny — Receiver เท่านั้น** endpoint แก้ไข header และเพิ่ม / แก้ / ลบบรรทัด return `"This action requires the Receiver / Store Keeper role."` UI ซ่อน edit affordance ทั้งหมดสำหรับบทบาท Purchaser **ยังไม่ยืนยัน** ว่าถูกบังคับใช้โดยกฎการแยกหน้าที่โดยเฉพาะ หรือเพียงเพราะบทบาท Purchaser ไม่เคยถือสิทธิ์แก้ไขในโมดูลนี้เลย — ไม่พบการตรวจ `buyer_id` cross-check ใน `good-received-note.service.ts` ในรอบนี้ Map ไปยัง TC-GRN-080005 |
| PUR-PERM-04 | Purchaser พยายามสร้าง GRN (ปุ่ม New GRN) | **Deny — Receiver / Inventory Manager เท่านั้น** ปุ่ม **New GRN** ถูกซ่อน / ปิดสำหรับบทบาท Purchaser; เรียก API โดยตรง return `"GRN creation requires the Receiver (Store Keeper) or Inventory Manager role."` |
| PUR-PERM-05 | Purchaser พยายาม commit GRN ที่ `saved` | **Deny — Inventory Manager เท่านั้น** ปุ่ม **Commit** ถูกซ่อน / ปิดสำหรับบทบาท Purchaser; เรียก API โดยตรง return `"Commit from status saved requires the Inventory Manager role."` Map ไปยัง TC-GRN-110002 |

## 3. Validation / Error

| # | Scenario | Trigger | ข้อผิดพลาดที่คาด |
| - | -------- | ------- | -------------- |
| PUR-VAL-01 | Purchaser ไม่สามารถ trigger commit บน GRN ที่ `saved` ที่ตนเป็นเจ้าของ PO ต้นทาง | GRN ที่ `saved` บน PO ของตัวเอง `PO-X`; Purchaser พยายามเรียก commit endpoint โดยตรง | **Reject** — ตรวจตามบทบาท Server return `"Commit from status saved requires the Inventory Manager role."` `doc_status` ยังที่ `saved` Map ไปยัง TC-GRN-110002 |
| PUR-VAL-02 | Purchaser พยายามแก้ `received_qty` ของบรรทัดบน GRN ที่ตนเป็นเจ้าของ PO ต้นทาง | GRN ที่ `saved` บน PO ของตัวเองด้วย `received_qty = 10`; Purchaser พยายาม PATCH บรรทัด | **Reject** — ตรวจตามบทบาท Server return `"Line quantities are editable only by the Receiver / Store Keeper role."` บรรทัดไม่เปลี่ยน; เส้นทางที่ถูกต้องของ Purchaser คือ comment บน GRN และขอให้ Receiver ประเมินใหม่ขณะที่ GRN ยัง `saved` |

## 4. Edge Case

| # | Scenario | เงื่อนไข | ผลที่คาด |
| - | -------- | --------- | -------- |
| PUR-EDGE-01 | การ review การรวมหลาย PO — GRN เดียว span สอง PO ของ Purchaser | ผู้ขายเดียวกันส่งของด้วยรถเดียวครอบคลุม `PO-A` (หนึ่งบรรทัด pending 4) และ `PO-B` (สองบรรทัด pending 6 แต่ละ); Receiver รวมเข้า GRN เดียวพร้อมสามบรรทัดตาม RCV-EDGE-04 (ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)); ทั้งสอง PO เป็นเจ้าของโดย Purchaser คนเดียวกัน | การเปิด GRN แสดงทั้งสามบรรทัด (ขอบเขตความเป็นเจ้าของข้าม PO รวมเป็นหนึ่งสำหรับ read view เนื่องจาก Purchaser เป็นเจ้าของทั้งสอง PO); variance ของบรรทัดที่ขาดถูก scope ไปยัง PO ที่มันสังกัด (`PO-A` บรรทัด `L1`, หรือ `PO-B` บรรทัด `L1` / `L2`) Map ไปยัง TC-GRN-040002, TC-GRN-040004 |

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona ที่ pivot บน Purchaser
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — แหล่ง happy-path สำหรับส่วน 1 ข้างต้น
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — test set ต้นทางที่สร้างและ save (post) GRN
- Sibling: [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) — หน้าแก้ไข: เหตุผลที่ไม่มี test scenario สำหรับ handoff credit-note / three-way-match
- กฎธุรกิจที่ตรวจสอบ: [02-business-rules.md](./02-business-rules.md) — การแยกหน้าที่ (`GRN_AUTH_010` ทำเครื่องหมายว่ายังไม่ยืนยันในรอบนี้) อ้างใน PUR-PERM-03, PUR-VAL-01, PUR-VAL-02
- Cross-link: [purchase-order](/th/inventory/purchase-order) — โมดูลต้นทางที่ persona นี้เป็นเจ้าของ; ต้นทางของ `pending_qty`, `po_status` และ activity log
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — Playwright spec ทางการสำหรับโมดูล GRN test group ที่เกี่ยวข้องกับ Purchaser: **TC-GRN-010001** (View GRN List), **TC-GRN-010003** (View GRN List with Insufficient Permissions), **TC-GRN-080005** (Edit Line Item in RECEIVED status — deny ตามบทบาท), **TC-GRN-110002** (No Permission to Commit), **TC-GRN-040002 / 040004** (Create from Multiple POs — การ review การรวมหลาย PO)
