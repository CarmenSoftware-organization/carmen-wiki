---
title: การคำนวณต้นทุน (Costing) — User Flow — Finance (แก้ไข)
description: หน้าแก้ไข — ไม่มี Finance role, valuation-policy console, GL reconciliation dashboard, หรือ period-lock flow ในโมดูล costing
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — User Flow — Finance (แก้ไข)

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-22 — flow ของ persona Finance ที่เคยเอกสารไว้ที่นี่ (valuation-policy console, sub-ledger ↔ GL reconciliation dashboard, credit-note revaluation approval queue, period-end valuation orchestration dashboard, และ period-lock dashboard เฉพาะ Finance Manager) **ไม่มีอยู่จริงในผลิตภัณฑ์**
> **สิ่งที่มีจริง:** ผู้ถือ `inventory_management.period_end.execute` รันการปิดงวด (เอกสารไว้ที่ [inventory/period-end](/th/inventory/inventory/period-end) และ [inventory/03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller)); credit-note อนุมัติภายใต้ permission ทั่วไป `procurement.credit_note` ไม่มี gate เฉพาะ finance

## 1. สิ่งที่หน้านี้เคย claim และทำไมถูกลบ

ฉบับร่างก่อนหน้าอธิบาย persona Finance Officer / Cost Controller / Finance Manager ครอบคลุมห้าเธรด: เป็นเจ้าของนโยบาย valuation แบบ FIFO-vs-Average per business unit, รัน inventory-sub-ledger ↔ GL reconciliation เป็นระยะพร้อม tolerance ที่ตั้งค่าได้, อนุมัติ credit-note-amount revaluation พร้อม GL posting แบบ `Dr AP / Cr Inventory`, orchestrate period-end close, และ — เป็น Finance Manager — advance งวดจาก `closed` ไปเป็นสถานะ `locked` ถาวร การตรวจสอบกับซอร์สปัจจุบันไม่พบสิ่งใดเลย:

- **ไม่มี Finance role หรือ permission key อยู่จริง** `enum_stage_role` (enum role เดียวใน tenant schema) คือ `{create, approve, purchase, issue, view_only}` — ไม่มีสมาชิก `finance` `constant/permissions.ts` ใน frontend ไม่มี key เฉพาะ finance เลยใกล้ ๆ period-end หรือ credit-note
- **ไม่มีโค้ด GL/journal อยู่ที่ใดใน backend เลย** การค้นหาทั้ง repo ของ `carmen-turborepo-backend-v2` สำหรับ journal/ledger posting จาก cost-layer write ไม่พบสิ่งใด เอกสารออกแบบระดับวางแผนที่กฎของโมดูลนี้อ้างถึง (`../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/proc-03-cost-calculation.md`) ระบุตรงนี้ในเนื้อหาของตัวเองว่า **"Does not generate GL journal entries (separate accounting integration — TBC)."**
- **ไม่มี reconciliation dashboard, tolerance, หรือกลไก compensating-journal อยู่จริง** ไม่มีอะไรใน `inventory-transaction.service.ts` หรือ `period-end.service.ts` เทียบ cost-layer activity กับ ledger ภายนอกใด ๆ
- **ไม่มี guard "method locked, ต้อง drain ก่อนเปลี่ยน" อยู่จริง** เอกสารวางแผนบันทึกนี้เป็น *เจตนาการออกแบบ* ที่ stakeholder ยืนยัน (P4 Q1) แต่ write path ของ `tb_business_unit.calculation_method` (`platform_business-units.controller.ts` หน้าจอ platform/cluster-admin) ไม่มีการตรวจ on-hand เลย
- **ไม่มี lock/reopen flow ในโมดูลนี้** `period-end.controller.ts` เปิดเผยแค่ `find-all` / `find-current` / `close` / `find-review` `enum_period_status.locked` ถูกตั้งโดย period service แยกต่างหากที่อยู่หลังหน้าจอ [system-config/period](/th/inventory/system-config/period)

สอดคล้องกับข้อค้นพบ Finance-persona เดียวกันที่ยืนยันแล้วใน [inventory/03-user-flow-finance](/th/inventory/inventory/03-user-flow-finance), [purchase-order](/th/inventory/purchase-order/03-user-flow-finance), [good-receive-note](/th/inventory/good-receive-note/03-user-flow-finance), และ [store-requisition](/th/inventory/store-requisition)

## 2. พฤติกรรมจริงอยู่ที่ไหน

| เคย claim ที่นี่ | กลไกจริง | หน้า |
|---|---|---|
| Finance เป็นเจ้าของนโยบาย valuation FIFO/Average | ตั้งค่าครั้งเดียวบน `tb_business_unit.calculation_method` โดย platform/cluster admin ตอนสร้าง business unit — ค่าเดียวสำหรับทั้ง business unit ไม่มี override ต่อสินค้า | [costing/01-data-model](/th/inventory/costing/01-data-model) § 2.4 |
| Finance รัน sub-ledger ↔ GL reconciliation | ไม่มี GL ให้ reconcile ด้วย | [costing/02-business-rules](/th/inventory/costing/02-business-rules) § 6 (`COST_XMOD_009` ถูกลบ) |
| Finance อนุมัติ credit-note-amount revaluation | อนุมัติภายใต้ `procurement.credit_note` เหมือน credit-note ทั่วไป cost-layer revaluation (`diff_amount`) เป็นผลข้างเคียงของการอนุมัตินั้น ไม่ใช่ action เฉพาะ finance แยก | [costing/02-business-rules](/th/inventory/costing/02-business-rules) § 3 `COST_CALC_005` |
| Finance orchestrate period-end close | ใครก็ได้ที่มี `inventory_management.period_end.execute` คลิก **Close period** บน `/inventory-management/period-end/review` | [inventory/period-end](/th/inventory/inventory/period-end) |
| Finance Manager ล็อกงวดหลัง audit window | `locked` จัดการโดย system-config period service ไม่ใช่ที่นี่ | [system-config/period](/th/inventory/system-config/period) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts` (พื้นผิว endpoint ครบถ้วน), `.../inventory-transaction/inventory-transaction.service.ts` (ไม่มี GL fan-out)
- เอกสารวางแผน (เจตนาการออกแบบ ไม่ใช่ยืนยันจาก code): `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/proc-03-cost-calculation.md`
- Parent overview: [03-user-flow](./03-user-flow.md)
- Cross-link: [inventory/03-user-flow-finance](/th/inventory/inventory/03-user-flow-finance) — การแก้ไขเดียวกันบนโมดูลพี่น้องที่ engine นี้เชื่อมต่อด้วย
