---
title: ใบรับสินค้า (Goods Receive Note) — User Flow — Audit & Config
description: เหตุผลที่ไม่พบ GRN configuration console เฉพาะทางหรือเครื่องมือ lot-recall สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้จริง
published: true
date: '2026-09-23T01:30:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, audit-config, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — User Flow — Audit & Config

> **At a Glance**
> **หน้านี้เอกสารอะไร:** เหตุผลที่ flow "Audit / Config" เดิม (GRN configuration console พร้อม panel รูปแบบเลข lot, RBAC, tax/currency/reason-code, integration บวกเครื่องมือ lot-recall ของ Auditor พร้อมการอนุมัติ export แบบ sensitive) ไม่ตรงกับซอร์สปัจจุบัน และสิ่งที่ยืนยันได้จริง

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้บรรยาย "GRN configuration console" (panel ของ Sysadmin สำหรับรูปแบบเลข lot, บทบาท RBAC และเกณฑ์อนุมัติ, รหัสภาษี / สกุลเงิน / เหตุผล, และ endpoint integration ไปยัง PO / Inventory / Finance / Vendor) และเครื่องมือ lot-recall trace ของ Auditor พร้อม workflow การอนุมัติ export แบบ sensitive-field จาก Controller/DPO ไม่พบ route, component ฝั่ง frontend หรือ endpoint ฝั่ง backend ที่ตรงกันใน `carmen-inventory-frontend-react` หรือ `carmen-turborepo-backend-v2` และไม่พบ route ดังกล่าวใน `.specs/resync-2026-07-15-routes-inventory.txt`

## สิ่งที่ยืนยันได้และยังไม่ยืนยัน

| ข้อกล่าวอ้าง | สถานะ |
| --- | --- |
| การสร้างหมายเลข lot | **ยืนยันแล้ว แต่ตั้งค่าไม่ได้** **แก้ไข 2026-09-22:** รูปแบบคือ `<location_code><YYMM><ลำดับ 4 หลัก>` (เช่น `MK-0126070246`) สร้างโดย `buildLotNo()` ใน `apps/micro-business/src/common/helpers/lot-number.helper.ts:27-35`; เลขลำดับคือ `lot_seq_no` ของ cost layer ซึ่งเริ่มนับใหม่ที่ 1 ทุกงวดสินค้าคงคลัง รูปแบบเดิม `RC{YY}{MM}{seq}` ไม่มีอยู่แล้ว ไม่มีตัวแก้ไขรูปแบบเลข lot ใน frontend และไม่มีการเขียนทับด้วยมือบน GRN |
| บทบาท RBAC และเกณฑ์อนุมัติเฉพาะ GRN | **ยังไม่ implement เป็น panel เฉพาะของ GRN** Authorization เป็น RBAC ทั่วไปที่ใช้ร่วมกันข้ามโมดูล (ดู [access-control](/th/inventory/access-control)); ไม่พบแนวคิด "เกณฑ์อนุมัติ" ใดในโมดูลนี้ทั้ง backend (ตรงกับข้อสรุปเดียวกันที่ยืนยันแล้วสำหรับ `PO_AUTH_004` ของโมดูล PO) |
| รหัสภาษี, อัตราแลกเปลี่ยน, รหัสเหตุผลการยกเลิก/ปฏิเสธ | **จริง แต่ทั่วไป — ไม่ใช่ของ GRN** Tax profile, สกุลเงิน และการกำหนดลำดับ running-code ตั้งค่าผ่านหน้าจอ [system-config](/th/inventory/system-config) และ [master-data](/th/inventory/master-data) ข้ามโมดูล ไม่ใช่ console เฉพาะของ GRN |
| Endpoint integration ไปยัง PO / Inventory / Finance / Vendor (พร้อม workflow cutover แบบ dual-write) | **ยังไม่ implement** ไม่พบ UI ตั้งค่า integration-endpoint หรือกลไก dual-write ใดสำหรับโมดูลนี้ |
| Auditor review activity log แบบ read-only | **น่าเป็นไปได้แต่ยังไม่ยืนยันว่าเป็น screen เฉพาะ** `tb_good_received_note.workflow_history` (JSON) เป็นฟิลด์จริงที่มีข้อมูล ซึ่ง screen activity-log / reporting ทั่วไปสามารถอ่านได้; ไม่พบ route "audit module" เฉพาะของ GRN — ดู [reporting-audit](/th/inventory/reporting-audit) สำหรับ equivalent ทั่วไป |
| เครื่องมือ lot-recall trace (forward/backward trace ผ่าน `lot_no`) | **ยังไม่ implement เป็นเครื่องมือเฉพาะ** การเชื่อมโยงข้อมูลพื้นฐานมีจริงและตั้งแต่ 2026-08-10 เป็นแบบตรง: `tb_inventory_transaction_detail.good_received_note_detail_item_id → tb_good_received_note_detail_item` (`@relation` จริง) บวก `GET …/good-received-notes/:id/stock-movements` ซึ่งคืน lot ต่อบรรทัด GRN ไม่มีหน้าจอ recall-trace หรือ workflow export ที่สร้างขึ้นเฉพาะ |
| การ export field แบบ sensitive ที่ต้องการอนุมัติจาก Controller/DPO | **ยังไม่ implement** ไม่พบโค้ด workflow การอนุมัติสำหรับ export ใดๆ ในโมดูลนี้ |
| การ void หลัง commit ที่ต้องการ co-authorisation ระหว่าง Inventory Manager + Finance | **ยังไม่ implement — และตอนนี้การ void หลัง commit ถูกปฏิเสธทันที** `voidGrnById()` (`good-received-note.service.ts:2244-2256`) คืน `GRN_COMMITTED_NOT_VOIDABLE` สำหรับ GRN ที่ `committed`; เส้นทางแก้ไขเดียวคือ credit note หรือ inventory adjustment — ดู [02-business-rules.md](./02-business-rules.md) `GRN_POST_010` |

เนื้อหานี้ทับซ้อนกับขอบเขตของโมดูล **system-config** และ **access-control** อย่างมาก — หน้าจอทั่วไปข้ามโมดูล (การตั้งค่า workflow-stage, การกำหนดลำดับ running-code / เลข GRN, tax-profile, สกุลเงิน) มีอยู่จริงในผลิตภัณฑ์ เพียงแต่ไม่ได้อยู่ภายใต้ชื่อ "configuration console" เฉพาะของ GRN แนะนำให้ดูหน้าของโมดูลเหล่านั้นสำหรับสิ่งที่ตั้งค่าได้จริง

## แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิตทางการ 4 สถานะที่แก้ไขแล้ว
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — persona ที่การเปลี่ยนสถานะ save / commit เขียนรายการกิจกรรมที่หน้าจอ activity-log ทั่วไปจะอ่าน
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — หน้าแก้ไขสำหรับการกุขึ้นแบบขนานของ three-way-match / AP
- Sibling: [02-business-rules.md](./02-business-rules.md) §4 / §6 — กฎ authorization และ cross-module หลายรายการทำเครื่องหมายว่ายังไม่ยืนยันหรือยังไม่ implement ในรอบนี้
- โมดูลทั่วไปที่จริงและเกี่ยวข้อง: [system-config](/th/inventory/system-config), [master-data](/th/inventory/master-data), [access-control](/th/inventory/access-control), [reporting-audit](/th/inventory/reporting-audit)
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md` — ภาพรวมโมดูล carmen/docs: คำอธิบายบทบาท System Administrator; ถือเป็นเจตนาการออกแบบ ไม่ใช่พฤติกรรมที่ยืนยันแล้ว สำหรับสิ่งใดที่เกินกว่าหน้าจอทั่วไปข้ามโมดูลข้างต้น
