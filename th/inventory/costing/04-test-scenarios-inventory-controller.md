---
title: การคำนวณต้นทุน (Costing) — Test Scenarios — Inventory Controller (แก้ไข)
description: หน้าแก้ไข — ชุด test ของ Inventory Controller ที่เคยเอกสารไว้ที่นี่เล็งไปที่ cost-pick-preview adjustment-approval queue ที่ไม่มีอยู่จริง
published: true
date: '2026-09-23T01:30:00.000Z'
tags: costing, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — Test Scenarios — Inventory Controller (แก้ไข)

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-22 — scenarios ที่เคยอยู่บนหน้านี้ (ทบทวน cost-pick preview ตอนอนุมัติ adjustment, ตรวจ new-lot cost basis เทียบ vendor-pricelist tolerance, ตรวจสอบ variance ที่ Finance escalate, triage cost-anomaly dashboard) เล็งไปที่พื้นผิวที่ **ไม่มีที่มาจากซอร์ส** และถูกลบออกแทนการกุขึ้นใหม่

## 1. ทำไม scenarios เหล่านี้ถูกลบ

- **ไม่มี approval queue สำหรับ `tb_stock_in` / `tb_stock_out`** อัปเดต 2026-09-22: ตอนนี้การสร้างเขียน `doc_status = draft` (`stock-in.service.ts:418`) และการโพสต์เกิดที่ `PATCH …/commit` (`:471-575`) — แต่ผู้ถือ permission เดียวกันเป็นคน commit จึงยังคงไม่มีสถานะที่ทวนได้สำหรับผู้อนุมัติแยกและไม่มี cost-pick preview
- **ไม่มีหน้าจอ "cost-pick preview" อยู่จริง**
- **ไม่มีการแยก Inventory-Controller-vs-Store-Keeper ในโมดูลนี้** — ทั้งคู่ gate ด้วย permission ทั่วไปเดียวคือ `inventory_management.view`
- **ไม่มี Finance persona ให้ escalate variance ไปหา** — ดู [03-user-flow-finance](./03-user-flow-finance.md) (แก้ไข)

สอดคล้องกับข้อค้นพบ approval-queue ที่ยืนยันแล้วในรอบ resync ของโมดูล [inventory-adjustment](/th/inventory/inventory-adjustment) เองและรูปแบบการแก้ไขเดียวกันที่ใช้ในทุกจุดที่โมดูล claim ขั้นตอนทบทวนที่กลายเป็น flow แบบสร้างคือ post

## 2. พฤติกรรมที่ test ได้จริงอยู่ที่ไหน

| เคย test ที่นี่ | ที่ test จริง |
|---|---|
| Cost-pick preview / adjustment approval | ไม่มีขั้นตอนอนุมัติอยู่จริง — draft → commit โดยผู้ใช้คนเดียวกัน; ดู [inventory-adjustment](/th/inventory/inventory-adjustment) § 1 |
| Arithmetic ของ FIFO / Average cost-pick | [04-test-scenarios](./04-test-scenarios.md) Scenarios 1, 2, 9, 10, 11, 12, 13, 14 |
| Period-end review checklist + close | [inventory/04-test-scenarios-inventory-controller](/th/inventory/inventory/04-test-scenarios-inventory-controller) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-in/stock-in.service.ts`, `.../stock-out/stock-out.service.ts`
- Parent overview: [04-test-scenarios](./04-test-scenarios.md); คู่กัน user-flow: [03-user-flow-inventory-controller](./03-user-flow-inventory-controller.md)
