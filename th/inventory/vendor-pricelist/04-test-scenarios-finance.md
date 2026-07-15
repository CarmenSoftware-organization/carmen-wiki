---
title: รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Finance (แก้ไข)
description: หน้า correction — Finance ไม่ใช่ persona ที่แยกต่างหากในโมดูล vendor-pricelist; ไม่มี test scenario ใดที่เกี่ยวข้อง
published: true
date: 2026-07-16T02:00:00.000Z
tags: vendor-pricelist, test-scenarios, finance, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — Test Scenarios — Finance (แก้ไข)

> หน้านี้เคยทำแคตตาล็อก scenario สำหรับ persona Finance Officer / Finance Manager: gate co-signoff multi-currency, dashboard audit variance และการบังคับใช้นโยบาย FX ดู [03-user-flow-finance.md](./03-user-flow-finance.md) สำหรับ correction ฉบับเต็ม — ไม่มีอะไรในนี้ที่มี code ตรงกันใน `price-list.service.ts`, `price-list-template.service.ts` หรือ `request-for-pricing.service.ts`

ไม่มี test scenario เฉพาะ Finance ใดที่เกี่ยวข้องกับโมดูลนี้ ถ้าต้องการ test price variance ฝั่ง GRN ให้ดูที่หน้า test-scenario ของโมดูล [good-receive-note](/th/inventory/good-receive-note) แทน

## แหล่งอ้างอิง

- [03-user-flow-finance.md](./03-user-flow-finance.md) — รายละเอียด correction ฉบับเต็ม
- [02-business-rules.md](./02-business-rules.md) § 4
- [04-test-scenarios.md](./04-test-scenarios.md) — ดัชนี persona (Finance ถูกลบออก)
