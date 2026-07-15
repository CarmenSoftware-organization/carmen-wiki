---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Finance
description: ประกาศแก้ไข — ไม่มี persona Finance หรือ surface การอนุมัติสำหรับโมดูลนี้ให้ทดสอบ
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Finance

> **ประกาศแก้ไข** หน้านี้เคยรวบรวม test scenario ประมาณ 26 รายการสำหรับ queue อนุมัติของ Finance, การตรวจสอบการ map GL และการ sign-off ปลายงวด ไม่มีข้อไหนมี route, permission หรือ backend endpoint ที่ตรงกัน — ดู [03 — User Flow — Finance](./03-user-flow-finance.md) สำหรับประกาศแก้ไขแบบเต็มและสิ่งที่ตรวจสอบแล้ว

ไม่มี test scenario เฉพาะของ Finance สำหรับโมดูลนี้ หากมีพฤติกรรมที่เกี่ยวเนื่องกับ Finance ต้องการการทดสอบ พฤติกรรมนั้นเป็นของ feature ปิดงวดจริงของ [inventory](/th/inventory/inventory) ไม่ใช่โมดูลนี้ — ตรวจสอบกับหน้า test-scenario ของโมดูลนั้นเองแทน

## แหล่งอ้างอิง

- [03 — User Flow — Finance](./03-user-flow-finance.md) — ประกาศแก้ไขและสิ่งที่ตรวจสอบแล้ว
- [04 — Test Scenarios](./04-test-scenarios.md) — test scenario จริงของโมดูล (Store Keeper / Inventory Controller หน้าจอเดียวกันที่ไม่แตกต่างกัน)
- [inventory](/th/inventory/inventory) — feature ปิดงวดที่แท้จริง
