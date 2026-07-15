---
title: คลังสินค้า (Inventory) — Test Scenarios — Finance
description: หน้าแก้ไข — test suite ของ Finance ที่เคยบันทึกไว้บนหน้านี้อ้างถึง surfaces (approval queue, GL reconciliation, period lock) ที่ไม่มีอยู่จริง
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — Test Scenarios — Finance

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-15 — scenario ~28 รายการที่เคยอยู่บนหน้านี้ (cost-impact approval queue, inventory-to-GL reconciliation พร้อม tolerances และ compensating journals, การ orchestrate ปิดงวดพร้อม sign-off gates, period lock / re-open, FX revaluation journals) อ้างถึง surfaces ที่**ไม่มี source รองรับ** และถูกตัดออกแทนที่จะสร้างขึ้นใหม่

## 1. เหตุผลที่ scenarios เหล่านี้ถูกตัดออก

- **ไม่มี Finance role หรือ permission key อยู่จริง** (`enum_stage_role` ไม่มีสมาชิก `finance`; ไม่มี key ที่ scope เป็น finance ใน `constant/permissions.ts`)
- **ไม่มีโค้ด GL/journal, reconciliation, หรือ tolerance** ที่ใดเลยใน `carmen-turborepo-backend-v2` (ดู [01-data-model](/th/inventory/inventory/01-data-model) § 1)
- **ไม่มี approval chain แบบอิง threshold** ([02-business-rules](/th/inventory/inventory/02-business-rules) § 4 คำแก้ไข)
- **ไม่มี endpoint lock/re-open ในโมดูลนี้** (`period-end.controller.ts`: มีเพียง `find-all` / `find-current` / `close` / `find-review`) กฎ block การปิดงวดที่เคยอ้างถึง ("Controller sign-off", "reconciliation clean") ถูกแทนด้วย gates จริงใน `validatePeriodEnd` — ดู [period-end](/th/inventory/inventory/period-end) § 2

สิ่งนี้สอดคล้องกับข้อค้นพบ persona Finance ที่ยืนยันแล้วว่าถูกสร้างขึ้นเองในโมดูล purchase-order, good-receive-note และ store-requisition

## 2. พฤติกรรมที่ test ได้จริงตอนนี้อยู่ที่ไหน

| เคย test ที่นี่ | ที่ test จริง |
|---|---|
| Period close happy path / blocked / race | [04-test-scenarios-inventory-controller](/th/inventory/inventory/04-test-scenarios-inventory-controller) IC-HP-05/06, IC-VAL-01–03 |
| Credit-note amount repricing (งวดเปิด vs งวดปิด) | [04-test-scenarios](/th/inventory/inventory/04-test-scenarios) scenarios 5, 6, 12 |
| พฤติกรรม backdating | [04-test-scenarios](/th/inventory/inventory/04-test-scenarios) scenario 7 (re-date ไม่ใช่ reject) |
| Adjustment approval | ไม่มี approval tier อยู่จริง; test ของเอกสาร adjustment เป็นของ [inventory-adjustment](/th/inventory/inventory-adjustment) |

## 3. แหล่งอ้างอิง

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts`, `.../inventory-transaction/inventory-transaction.service.ts`
- ภาพรวม parent: [04-test-scenarios](/th/inventory/inventory/04-test-scenarios); คู่ user-flow: [03-user-flow-finance](/th/inventory/inventory/03-user-flow-finance)
