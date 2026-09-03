---
title: การคำนวณต้นทุน (Costing) — Test Scenarios — Auditor (แก้ไข)
description: หน้าแก้ไข — ชุด test ของ Auditor ที่เคยเอกสารไว้ที่นี่เล็งไปที่ chain-of-custody trace tool, snapshot verification tool, และ shadow-drift audit ที่ไม่มีอยู่จริง
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, test-scenarios, auditor, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios — Auditor (แก้ไข)

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-22 — scenarios ที่เคยอยู่บนหน้านี้ (lot-level chain-of-custody trace tool, period-end snapshot verification tool, FIFO-vs-Average shadow-drift audit, configuration-history audit) เล็งไปที่พื้นผิวที่ **ไม่มีที่มาจากซอร์ส** และถูกลบออกแทนการกุขึ้นใหม่

## 1. ทำไม scenarios เหล่านี้ถูกลบ

- **ไม่มี Auditor role หรือ permission key อยู่จริง** (`enum_stage_role` ไม่มีสมาชิก `auditor`; ไม่มี key เฉพาะ auditor ใน `constant/permissions.ts`)
- **ไม่มี chain-of-custody trace tool, snapshot-verification tool, หรือ shadow-drift tool อยู่ที่ใดใน frontend เลย** — สอดคล้องกับข้อค้นพบเดียวกันบน [inventory/03-user-flow-audit-config](/th/inventory/inventory/03-user-flow-audit-config): "ไม่พบหน้าจอหรือ permission เฉพาะ audit-only ที่แยกจาก `inventory_management.view`"
- **claim เรื่อง GL และ `COST_VAL_009` ที่ checklist audit พึ่งพาไม่มีอยู่จริง** — ดู [02-business-rules](./02-business-rules.md) §§ 2, 4, 6

## 2. พฤติกรรมที่ test ได้จริงอยู่ที่ไหน

| เคย test ที่นี่ | ที่ test จริง |
|---|---|
| Cost-flow chain-of-custody trace | ไม่มีเครื่องมือในแอป หน้าจอจริงที่ใกล้เคียงที่สุดคือ [inventory/transaction](/th/inventory/inventory/transaction) log แบบ read-only |
| Period-snapshot vs cost-layer reconciliation | จะต้องเป็น query ด้วยมือเทียบกับ [01-data-model](./01-data-model.md) § 2.1 / § 2.3 — ไม่พบเครื่องมือในแอป |
| FIFO-vs-Average shadow-drift audit | คอลัมน์ shadow `average_cost_per_unit` มีอยู่จริง (Section 2.6 ของ [01-data-model](./01-data-model.md)) แต่ไม่มีเครื่องมือ drift-audit ที่อ่านมัน |
| Configuration-history audit | ไม่พบ configuration-history feed สำหรับ `calculation_method` ในรอบนี้ |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` — ไม่พบ controller เฉพาะ audit สำหรับข้อมูล cost-layer
- Parent overview: [04-test-scenarios](./04-test-scenarios.md); คู่กัน user-flow: [03-user-flow-auditor](./03-user-flow-auditor.md)
- Cross-link: [inventory/04-test-scenarios-audit-config](/th/inventory/inventory/04-test-scenarios-audit-config) — การแก้ไขเดียวกันที่ทำแล้วบนโมดูลพี่น้อง
