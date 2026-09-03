---
title: คลังสินค้า (Inventory) — User Flow — Finance (แก้ไข/correction)
description: หน้าแก้ไข — ไม่มี Finance role, GL reconciliation หรือ flow การ lock งวดอยู่จริงในโมดูล inventory; หน้านี้บันทึกสิ่งที่มาแทน draft ก่อนหน้า
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Finance (แก้ไข/correction)

> **At a Glance**
> **สถานะ:** แก้ไขเมื่อ 2026-07-15 — flow ของ persona Finance ที่เคยเอกสารไว้ในหน้านี้ (cost-impact approval queue, inventory-to-GL reconciliation dashboard, ความก้าวหน้าของ period-lock) **ไม่มีอยู่จริงในผลิตภัณฑ์**
> **สิ่งที่จริง:** การปิดงวด (period-end close) ซึ่ง execute ได้โดยผู้ใช้ใดก็ตามที่ถือสิทธิ์ `inventory_management.period_end.execute` — เอกสารไว้ที่ [period-end](/th/inventory/inventory/period-end) และ [03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller)

## 1. หน้านี้เคยกล่าวอ้างอะไร และเหตุใดจึงถูกลบ

Draft ก่อนหน้าอธิบาย persona Finance Officer / Finance Manager ที่มีสี่สายงาน: cost-impact approval queue สำหรับ adjustment ที่เกิน threshold, inventory-to-GL reconciliation dashboard รายสัปดาห์, flow การ orchestrate ปิดงวดพร้อม reconciliation journal และความก้าวหน้าของ period-lock แบบ `closed → locked` การตรวจสอบเทียบกับ source ปัจจุบันไม่พบสิ่งใดเลย:

- **ไม่มี Finance role อยู่จริง** `enum_stage_role` (Prisma tenant schema) คือ `{create, approve, purchase, issue, view_only}` — ไม่มี member `finance` และ permission catalogue (`carmen-inventory-frontend-react/constant/permissions.ts`) ไม่มี key ที่ scope ให้ finance
- **ไม่มีโค้ด GL/journal อยู่จริง** การค้นหาทั่ว repo `carmen-turborepo-backend-v2` สำหรับการ post journal/ledger จาก inventory movement ไม่พบสิ่งใด (model Prisma `tb_jv_header`/`tb_jv_detail` ยังไม่ถูก wire — ดู [01-data-model](/th/inventory/inventory/01-data-model) § 1) ไม่มี reconciliation dashboard, tolerance หรือกลไก compensating-journal
- **ไม่มี approval chain แบบอิง threshold อยู่จริง** พบ `threshold` ศูนย์รายการใน service ของ inventory / stock-in / stock-out / period-end (ดูการแก้ไขใน [02-business-rules](/th/inventory/inventory/02-business-rules) § 4)
- **ไม่มี flow lock/reopen ในโมดูลนี้** `period-end.controller.ts` expose เพียง `find-all` / `find-current` / `close` / `find-review`; `enum_period_status.locked` ถูก set โดย period service ที่แยกต่างหากหลัง [system-config/period](/th/inventory/system-config/period)

ข้อสรุปนี้สอดคล้องกับข้อค้นพบ Finance-persona แบบเดียวกันที่ยืนยันไปแล้วใน [purchase-order](/th/inventory/purchase-order/03-user-flow-finance), [good-receive-note](/th/inventory/good-receive-note/03-user-flow-finance) และ [store-requisition](/th/inventory/store-requisition)

## 2. พฤติกรรมจริงอยู่ที่ใด

| สิ่งที่เคยกล่าวอ้างในหน้านี้ | กลไกจริง | หน้า |
|---|---|---|
| Finance เป็นผู้ trigger การปิดงวด | ผู้ใช้ใดก็ตามที่มี `inventory_management.period_end.execute` คลิก **Close period** บน `/inventory-management/period-end/review` | [period-end](/th/inventory/inventory/period-end) |
| Reconciliation เป็น gate ของการปิด | Gate จริงคือเอกสารที่ block (PR/PO/SR ที่ยังไม่จบ, GRN/CN ที่อยู่ mid-state) + physical count ที่เสร็จแล้ว | [02-business-rules](/th/inventory/inventory/02-business-rules) `INV_POST_009` |
| การ lock งวดหลัง audit window | `locked` ถูกจัดการโดย period service ของ system-config ไม่ใช่ที่นี่ | [system-config/period](/th/inventory/system-config/period) |
| การอนุมัติ cost-impact ของ adjustment | เอกสาร stock-in/stock-out อยู่ในโมดูล inventory-adjustment; ไม่มี Finance tier อยู่จริง | [inventory-adjustment](/th/inventory/inventory-adjustment) |

## 3. แหล่งอ้างอิง

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts` (endpoint surface ที่ครบถ้วน), `.../inventory-transaction/inventory-transaction.service.ts` (ไม่มี GL fan-out)
- Frontend: `../carmen-inventory-frontend-react/constant/permissions.ts` (`inventory_management.period_end.view` / `.execute`)
- ภาพรวม parent: [03-user-flow](/th/inventory/inventory/03-user-flow)
