---
title: การปรับสต๊อก (Inventory Adjustment) — User Flow — Finance
description: ประกาศแก้ไข — ไม่มี persona Finance, การลงบัญชี GL หรือการอนุมัติแบบ threshold สำหรับโมดูลนี้
published: true
date: '2026-09-23T01:30:00.000Z'
tags: inventory-adjustment, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — User Flow — Finance

> **ประกาศแก้ไข** หน้านี้เคยบรรยาย persona Finance ที่อนุมัติ adjustment เหนือ threshold, ตรวจสอบการ map บัญชี GL และ sign-off การกระทบยอดปลายงวด ไม่มีข้อไหนมีอยู่จริงในซอร์สปัจจุบัน

## สิ่งที่ตรวจสอบแล้ว

- การค้นหาทั่ว repo `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `journal`, `ledger` และโค้ดลงบัญชี GL ในโมดูล stock-in/stock-out ไม่พบผลลัพธ์ใด ๆ (ตรวจซ้ำ 2026-09-22) แกน GL (`tb_gl_jv*`, `apps/micro-business/src/gl/`, manual journal voucher) มาถึงในเดือน 2026-09 แต่ไม่มีอะไรใน `stock-in/` / `stock-out/` อ้างอิงถึงมัน
- `tb_adjustment_type` ไม่มีฟิลด์บัญชี GL, ไม่มี flag บังคับแนบเอกสาร, ไม่มี flag ตรวจสอบคุณภาพ — มีเพียง `code`, `name`, `type`, `description`, `is_active`, `note`
- `enum_stage_role` (enum role ของ workflow ในระดับ platform) คือ `{create, approve, purchase, issue, view_only}` — ไม่มีสมาชิก `finance` และเมธอด `create()`/`update()`/`void*()` ของโมดูลนี้ไม่เคยเรียก workflow orchestrator เลย
- การค้นหาทั่ว repo สำหรับ `threshold` ที่ขอบเขตของโมดูล inventory/stock-in/stock-out ไม่พบผลลัพธ์ที่เกี่ยวข้องเลย
- nav entry และทุก route ใต้ `/inventory-management/inventory-adjustment` gate ด้วยสิทธิ์ทั่วไปตัวเดียว `inventory_management.view` — ไม่มี permission หรือ route guard ที่เจาะจง Finance

## สถานะข้อกล่าวอ้าง

| ข้อกล่าวอ้างก่อนหน้า | สถานะ | สิ่งที่ซอร์สแสดงจริง |
| ---------------------- | ------ | ----------------------- |
| Finance อนุมัติ adjustment เหนือ threshold ของ Controller | **แต่งขึ้น** | ไม่มีขั้นตอนอนุมัติ — ตั้งแต่ 2026-07-30 `create()` เขียน `draft` และใครก็ตามที่ถือ permission ของโมดูลสามารถ **Commit** ได้; ไม่มี threshold ไม่มีชั้น Finance (ดู [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) § 1 / § 4) |
| การ map บัญชี GL ต่อ reason code (`info.glAccount`) | **แต่งขึ้น** | ไม่มีฟิลด์เช่นนี้บน `tb_adjustment_type`; ไม่มีโค้ด journal/ledger ที่ไหนในโมดูลนี้ |
| การ sign-off ปลายงวด / การกระทบยอด inventory-to-GL | **แต่งขึ้น** | ไม่พบ route หรือ backend method ที่ตรงกันสำหรับโมดูลนี้ การปิดงวดเป็น feature จริงของโมดูล [inventory](/th/inventory/inventory) แยกต่างหาก ไม่เกี่ยวกับ sign-off เฉพาะของ Finance ที่นี่ |
| อำนาจ compensating-reversal (void) | **Endpoint จริง แต่เจ้าของผิด** | `voidStockIn`/`voidStockOut` (`DELETE /{id}/void`) เป็นของจริงและไม่ถูก gate ด้วย role ใด; UI มีปุ่ม **Void** เฉพาะบน draft (โหมด Edit) ดังนั้นการกลับรายการเอกสารที่ post แล้วต้องเรียกผ่าน API — โดยใครก็ตามที่ถือ permission ของโมดูล ไม่ใช่ role Finance (ดู [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) § 2.1) |

## ดูที่ไหนแทน

- [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) — วงจรชีวิตเอกสารจริง (เป็น completed เสมอ)
- [03 — User Flow — Store Keeper](/th/inventory/inventory-adjustment/03-user-flow-store-keeper) / [Inventory Controller](/th/inventory/inventory-adjustment/03-user-flow-inventory-controller) — สอง persona จริงที่ไม่แตกต่างกัน
- [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) — กฎการตรวจสอบ การคำนวณ และการ posting จริงของโมดูล
