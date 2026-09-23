---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Audit & Config (แก้ไข)
description: หน้า correction — ไม่มี Audit workspace หรือ Configuration console แยกต่างหากในโมดูล vendor-pricelist; ไม่มี test scenario ใดที่เกี่ยวข้อง
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, test-scenarios, audit-config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Audit & Config (แก้ไข)

> **Executable coverage (2026-09-22):** ไม่มีสิ่งใดมุ่งเป้าไปยัง persona นี้ — ดู [04-test-scenarios](/th/inventory/vendor-pricelist/04-test-scenarios) สำหรับ spec และรายงาน gap ของโมดูล

> หน้านี้เคยทำแคตตาล็อก scenario สำหรับ workspace query-builder ของ Auditor และ configuration console ของ System Administrator (การกำหนดเลข, RBAC, นโยบาย portal-token, การเชื่อม email, registry กติกา validation, การตั้งค่าแหล่ง FX, การ revoke token) ดู [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) สำหรับ correction ฉบับเต็ม — ไม่มีอะไรในนี้ที่มี code ตรงกัน

ไม่มี test scenario เฉพาะ Audit/Config ใดที่เกี่ยวข้องกับโมดูลนี้ รายการนโยบายข้อเดียวที่กลายเป็นของจริงตั้งแต่นั้น (การหมดอายุของลิงก์ portal ที่ `end_date` ของ RFQ) ถูกทดสอบจากหน้า Vendor (`VPL-VND-EDGE-01`) และ action ของ portal / email มองเห็นได้ใน Activity log ที่ใช้ร่วม (`tb_activity`) ซึ่งเป็นของ generic ไม่ใช่ console ของโมดูล หน้าจอการกำหนดเลข, RBAC และ currency-master ทั่วไปถูก test อยู่ใน [system-config](/th/inventory/system-config), [access-control](/th/inventory/access-control) และ [master-data](/th/inventory/master-data) แทน

## แหล่งอ้างอิง

- [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — รายละเอียด correction ฉบับเต็ม
- [02-business-rules.md](./02-business-rules.md) § 4, § 5.4
- [04-test-scenarios.md](./04-test-scenarios.md) — ดัชนี persona (Audit/Config ถูกลบออก)
