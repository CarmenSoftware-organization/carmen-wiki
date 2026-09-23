---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Audit & Config
description: เหตุผลที่ไม่มี test scenario สำหรับ GRN configuration console หรือเครื่องมือ lot-recall สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: '2026-09-23T01:30:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
---

# ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Audit & Config

> **At a Glance**
> **สถานะ:** หน้าแก้ไข — ไม่พบ GRN configuration console เฉพาะทาง, panel RBAC, หรือเครื่องมือ lot-recall สำหรับ good-receive-note ในซอร์สปัจจุบัน

> ⚠️ **แก้ไขใหญ่ในรอบนี้ (2026-07-15)** เวอร์ชันก่อนหน้าของหน้านี้ list scenario ประมาณ 29 รายการ ครอบคลุม "GRN configuration console" ของ Sysadmin (ตัวแก้ไขรูปแบบเลข lot, panel บทบาท RBAC/เกณฑ์อนุมัติ, การดูแลรหัสภาษี/สกุลเงิน/เหตุผล, การ cutover integration ไปยัง PO/Inventory/Finance/Vendor) และเครื่องมือ lot-recall trace ของ Auditor พร้อมการอนุมัติ export แบบ sensitive-field จาก Controller/DPO ไม่พบ route, component ฝั่ง frontend หรือ endpoint ฝั่ง backend ที่ตรงกันใน `carmen-inventory-frontend-react` หรือ `carmen-turborepo-backend-v2` และไม่พบ route ดังกล่าวใน `.specs/resync-2026-07-15-routes-inventory.txt`

| กลุ่ม scenario ที่เคยกล่าวอ้าง | ข้อสรุป |
| --- | --- |
| AUD-HP-01..04 (การ query activity log ของ Auditor, การเจาะลึก GRN, lot-recall trace, การ export sensitive-field พร้อมการอนุมัติรอง) | ไม่พบ route audit-module เฉพาะทางหรือ workflow การอนุมัติ export ข้อมูลที่รองรับ (`workflow_history` JSON, linkage ผ่าน `inventory_transaction_id`) เป็นจริง แต่ไม่พบ screen ที่สร้างขึ้นมาเฉพาะเพื่ออ่านมัน |
| AUD-HP-05..08 (การเปลี่ยนรูปแบบ lot ของ Sysadmin, การปรับ RBAC, การดูแลรหัสภาษี/เหตุผล, การ cutover integration) | การสร้างหมายเลข lot มีจริงแต่ hardcode — **แก้ไข 2026-09-22:** `<location_code><YYMM><ลำดับ 4 หลัก>` จาก `buildLotNo()` (`common/helpers/lot-number.helper.ts`) เลขลำดับ = `lot_seq_no` ที่นับตามงวด; ตั้งค่าผ่าน panel ใดไม่ได้ การตั้งค่าภาษี/สกุลเงิน/running-code มีจริงแต่อยู่ในโมดูลทั่วไป [system-config](/th/inventory/system-config) / [master-data](/th/inventory/master-data) ไม่ใช่ console เฉพาะ GRN ไม่พบ panel RBAC-threshold หรือ integration-endpoint |
| AUD-PERM-01..07, AUD-VAL-01..08, AUD-EDGE-01..06 | ทั้งหมดสร้างขึ้นบนพื้นฐาน configuration console / เครื่องมือ lot-recall ที่ยังไม่ยืนยันเดียวกัน; ไม่ได้สร้างใหม่ |
| การ co-authorisation post-commit void ของ `GRN_POST_010` (Inventory Manager + Finance) ที่อ้างตลอดทั้งหน้า | **ยังไม่ implement — การ void หลัง commit ถูกปฏิเสธทันที** (`GRN_COMMITTED_NOT_VOIDABLE`, `good-received-note.service.ts:2254-2256`); ดู [02-business-rules.md](./02-business-rules.md) `GRN_POST_010` และ [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) |

> **ความครอบคลุมที่รันได้:** block permission-denial ใน `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (fixture บทบาท Requestor, ผู้ใช้ `carmensoftware.dev`, BU `GR2VYNKQ`); ส่วนสถานะ / สิทธิ์ของ `docs/test-cases/gaps/501-grn-core-gap.md`

## สิ่งที่ควรทดสอบแทน

- การสร้างหมายเลข lot (`<location_code><YYMM><run>` เริ่มนับใหม่ทุกงวด) และ link ledger → เหตุการณ์ GRN (`tb_inventory_transaction_detail.good_received_note_detail_item_id`) สังเกตได้บนแท็บ Stock Movement หลัง commit — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) RCV-HP-06
- ความครอบคลุม RBAC / permission-denial ทั่วไป — pattern fixture Requestor เทียบ Purchase ที่ใช้ตลอด describe block permission-denial ของ `501-grn.spec.ts`; หมายเหตุว่า save และ commit ใช้ permission key เดียวกัน (`procurement.goods_received_note.commit`)
- การปฏิเสธ void สำหรับ GRN ที่ `committed` และการปฏิเสธ 409 เมื่อ lot ที่รับถูกใช้ไปแล้ว — RCV-PERM-06, RCV-VAL-08
- การตั้งค่ารหัสภาษี, สกุลเงิน, และ running-code (การกำหนดลำดับเลข GRN) — ดู [system-config](/th/inventory/system-config) และ [master-data](/th/inventory/master-data) สำหรับหน้า test-scenario จริงของตัวเอง

## แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — ตาราง scenario ข้าม persona ที่แก้ไขแล้ว
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — การแก้ไขฉบับเต็มและการค้นหาที่ดำเนินการ
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — การสร้าง lot ในฐานะส่วนหนึ่งของ flow commit ของ Receiver
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — pattern permission-denial (fixture บทบาท Requestor) คือความครอบคลุมจริงที่ใกล้เคียงขอบเขต "Auditor read-only" ที่สุด; ไม่มี describe block สำหรับ lot-recall หรือ configuration console ในไฟล์นี้
