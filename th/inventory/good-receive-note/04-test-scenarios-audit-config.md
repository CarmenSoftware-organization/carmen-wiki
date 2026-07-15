---
title: ใบรับสินค้า (Goods Receive Note) — Test Scenarios — Audit & Config
description: เหตุผลที่ไม่มี test scenario สำหรับ GRN configuration console หรือเครื่องมือ lot-recall สำหรับ good-receive-note ในซอร์สปัจจุบัน และสิ่งที่ยืนยันได้แทน
published: true
date: 2026-07-15T00:00:00.000Z
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
| AUD-HP-05..08 (การเปลี่ยนรูปแบบ lot ของ Sysadmin, การปรับ RBAC, การดูแลรหัสภาษี/เหตุผล, การ cutover integration) | การสร้างหมายเลข lot เป็นจริงแต่ตายตัว (`RC{YY}{MM}{ลำดับ 4 หลัก}` ใน `inventory-transaction.service.ts`) ไม่มี panel ใดตั้งค่าได้ การตั้งค่าภาษี/สกุลเงิน/running-code เป็นจริงแต่อยู่ในโมดูลทั่วไป [system-config](/th/inventory/system-config) / [master-data](/th/inventory/master-data) ไม่ใช่ console เฉพาะของ GRN ไม่พบ panel เกณฑ์ RBAC หรือ integration-endpoint ใด |
| AUD-PERM-01..07, AUD-VAL-01..08, AUD-EDGE-01..06 | ทั้งหมดสร้างขึ้นบนพื้นฐาน configuration console / เครื่องมือ lot-recall ที่ยังไม่ยืนยันเดียวกัน; ไม่ได้สร้างใหม่ |
| การ co-authorisation post-commit void ของ `GRN_POST_010` (Inventory Manager + Finance) ที่อ้างตลอดทั้งไฟล์ | **ยังไม่ implement** endpoint `/void` ไม่มีเงื่อนไข `doc_status` นอกจาก "ยังไม่ voided" และไม่มี gate co-authorisation ใดๆ — ดู [02-business-rules.md](./02-business-rules.md) `GRN_POST_010` และ [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) |

## สิ่งที่ควรทดสอบแทน

- รูปแบบการสร้างหมายเลข lot และการเขียนทับด้วยมือ ในฐานะส่วนหนึ่งของ flow save ของ Receiver — ดู [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)
- ความครอบคลุม RBAC / permission-denial ทั่วไป — pattern fixture `requestor@blueledgers.com` เทียบ `purchase@blueledgers.com` ที่ใช้ตลอด describe block permission-denial ของ `501-grn.spec.ts`
- การตั้งค่ารหัสภาษี, สกุลเงิน, และ running-code (การกำหนดลำดับเลข GRN) — ดู [system-config](/th/inventory/system-config) และ [master-data](/th/inventory/master-data) สำหรับหน้า test-scenario จริงของตัวเอง

## แหล่งอ้างอิง

- ภาพรวม parent: [04-test-scenarios.md](./04-test-scenarios.md) — ตาราง scenario ข้าม persona ที่แก้ไขแล้ว
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — การแก้ไขฉบับเต็มและการค้นหาที่ดำเนินการ
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — การกรอกหมายเลข lot ในฐานะส่วนหนึ่งของ flow save ของ Receiver
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — pattern permission-denial (`requestor@blueledgers.com`) เป็นความครอบคลุมจริงที่ใกล้เคียงที่สุดกับขอบเขต "Auditor read-only"; ไม่มี describe block สำหรับ lot-recall หรือ configuration console ในไฟล์นี้
