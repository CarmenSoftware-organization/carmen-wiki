---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Audit & Config (Correction)
description: หน้า correction — ไม่มี Audit workspace หรือ Configuration console แยกต่างหากในโมดูล vendor-pricelist; ไม่มี test scenario ใดที่เกี่ยวข้อง
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, test-scenarios, audit-config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Audit & Config (Correction)

> หน้านี้เคยทำแคตตาล็อก scenario สำหรับ workspace query-builder ของ Auditor และ configuration console ของ System Administrator (การกำหนดเลข, RBAC, นโยบาย portal-token, การเชื่อม email, registry กติกา validation, การตั้งค่าแหล่ง FX, การ revoke token) ดู [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) สำหรับ correction ฉบับเต็ม — ไม่มีอะไรในนี้ที่มี code ตรงกัน

ไม่มี test scenario เฉพาะ Audit/Config ใดที่เกี่ยวข้องกับโมดูลนี้ หน้าจอการกำหนดเลข, RBAC และ currency-master ทั่วไปถูก test อยู่ใน [system-config](/th/inventory/system-config), [access-control](/th/inventory/access-control) และ [master-data](/th/inventory/master-data) แทน

## แหล่งอ้างอิง

- [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — รายละเอียด correction ฉบับเต็ม
- [02-business-rules.md](./02-business-rules.md) § 4, § 5.4
- [04-test-scenarios.md](./04-test-scenarios.md) — ดัชนี persona (Audit/Config ถูกลบออก)
