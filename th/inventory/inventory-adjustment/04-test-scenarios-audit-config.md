---
title: การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Audit & Config
description: ประกาศแก้ไข — ไม่มี surface เฉพาะของ Auditor หรือ threshold config สำหรับโมดูลนี้; ดู E2E spec ของ master reason code แทน
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, audit, sysadmin, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — Test Scenarios — Audit & Config

> **ประกาศแก้ไข** หน้านี้เคยรวบรวม test scenario ประมาณ 38 รายการสำหรับ console threshold/GL/RBAC ของ System Administrator และ workspace SoD/lot-recall/void-chain ของ Auditor เฉพาะโมดูลนี้ ไม่มีข้อไหนมีอยู่จริง — ดู [03 — User Flow — Audit / Config](./03-user-flow-audit-config.md) สำหรับประกาศแก้ไขแบบเต็มและสิ่งที่ตรวจสอบแล้ว

Surface การกำหนดค่าจริงเพียงอย่างเดียวที่ทดสอบได้สำหรับโมดูลนี้คือ master ของ reason code (`tb_adjustment_type`) ซึ่งครอบคลุมแล้วโดย [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — CRUD ปกติ, code ไม่ซ้ำ และ toggle active/inactive ไม่มี threshold, การ map GL หรือการกำหนดค่าบังคับแนบเอกสารให้ทดสอบ และไม่มีหน้าจอ Auditor เฉพาะสำหรับโมดูลนี้

## แหล่งอ้างอิง

- [03 — User Flow — Audit / Config](./03-user-flow-audit-config.md) — ประกาศแก้ไขและสิ่งที่ตรวจสอบแล้ว
- [04 — Test Scenarios](./04-test-scenarios.md) — test scenario จริงของโมดูล
- [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — spec CRUD reason code จริง
