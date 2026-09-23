---
title: การคำนวณต้นทุน (Costing) — Test Scenarios — Finance (แก้ไข)
description: หน้าแก้ไข — ชุด test ของ Finance ที่เคยเอกสารไว้ที่นี่เล็งไปที่พื้นผิว (valuation-policy console, GL reconciliation, credit-note approval queue, period lock) ที่ไม่มีอยู่จริง
published: true
date: '2026-09-23T01:30:00.000Z'
tags: costing, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios — Finance (แก้ไข)

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-22 — ~34 scenarios ที่เคยอยู่บนหน้านี้ (credit-note approval queue, sub-ledger ↔ GL reconciliation พร้อม tolerance และ compensating journal, period-end orchestration, period lock/re-open เฉพาะ Finance Manager, standard-cost cadence) เล็งไปที่พื้นผิวที่ **ไม่มีที่มาจากซอร์ส** และถูกลบออกแทนการกุขึ้นใหม่

## 1. ทำไม scenarios เหล่านี้ถูกลบ

- **ไม่มี Finance role หรือ permission key อยู่จริง** (`enum_stage_role` ไม่มีสมาชิก `finance`; ไม่มี key เฉพาะ finance ใน `constant/permissions.ts`)
- **ไม่มีโค้ดโพสต์จาก inventory เข้า GL, reconciliation หรือ tolerance อยู่จริง** (ตรวจซ้ำ 2026-09-22) ตอนนี้มีโมดูล GL แล้ว (`apps/micro-business/src/gl/`) แต่ `GlPostingService.post()` โพสต์เฉพาะ journal voucher และไม่มีส่วนใดในโค้ด inventory, GRN หรือ period-end เรียกมัน — เอกสารออกแบบระดับวางแผน (`../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/proc-03-cost-calculation.md`) ยังอธิบายความจริงได้ถูกต้อง: "does not generate GL journal entries"
- **ไม่มี guard "method locked, ต้อง drain ก่อนเปลี่ยน" ที่ code บังคับอยู่จริง** — ดู [02-business-rules](./02-business-rules.md) § 2 (`COST_VAL_009` ถูกลบ)
- **ไม่มี lock/re-open endpoint ในโมดูลนี้** (`period-end.controller.ts`: `find-all` / `find-current` / `close` / `find-review` เท่านั้น)

สอดคล้องกับข้อค้นพบ Finance persona ที่ยืนยันแล้วใน [inventory/04-test-scenarios-finance](/th/inventory/inventory/04-test-scenarios-finance), purchase-order, good-receive-note, และ store-requisition

## 2. พฤติกรรมที่ test ได้จริงอยู่ที่ไหน

| เคย test ที่นี่ | ที่ test จริง |
|---|---|
| Credit-note-amount revaluation happy path | [04-test-scenarios](./04-test-scenarios.md) Scenario 3 |
| Period-end close (FIFO / Average) happy path / blocked | [04-test-scenarios](./04-test-scenarios.md) Scenarios 5, 6; [inventory/04-test-scenarios-inventory-controller](/th/inventory/inventory/04-test-scenarios-inventory-controller) สำหรับ gate ของ review checklist |
| การเปลี่ยนวิธีคำนวณ | [04-test-scenarios](./04-test-scenarios.md) Scenario 7 — ตอนนี้เอกสารไว้ว่า **ไม่มีการป้องกัน** ไม่ใช่ถูกบล็อก |
| Standard-cost update | [04-test-scenarios](./04-test-scenarios.md) Scenario 8 |
| การจัดสรร extra cost (landed cost) เข้า ledger | [04-test-scenarios](./04-test-scenarios.md) Scenario 12 — ใช้งานจริงตั้งแต่ 2026-09-10 |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts`, `.../inventory-transaction/inventory-transaction.service.ts`
- Parent overview: [04-test-scenarios](./04-test-scenarios.md); คู่กัน user-flow: [03-user-flow-finance](./03-user-flow-finance.md)
