---
title: การคำนวณต้นทุน (Costing) — User Flow — Inventory Controller (แก้ไข)
description: หน้าแก้ไข — ไม่มี approval queue สำหรับ cost-pick preview ในโมดูล costing; stock-in/stock-out post ทันทีเมื่อสร้าง
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — User Flow — Inventory Controller (แก้ไข)

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-22 — "adjustment approval queue พร้อม cost-pick preview" ที่เคยเอกสารไว้ที่นี่ (Store Keeper สร้าง, Controller ทบทวน FIFO/Average cost preview, อนุมัติหรือปฏิเสธ) **ไม่มีอยู่จริงในผลิตภัณฑ์**
> **สิ่งที่มีจริง:** พื้นผิวเดียวที่ Inventory Controller เกี่ยวข้องกับ engine นี้จริง ๆ คือการทบทวน/ปิดงวด period-end ตามที่เอกสารไว้ที่ [inventory/period-end](/th/inventory/inventory/period-end) และ [inventory/03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller)

## 1. สิ่งที่หน้านี้เคย claim และทำไมถูกลบ

ฉบับร่างก่อนหน้าอธิบาย persona Inventory Controller ที่ทบทวน "cost-pick preview" (FIFO lot walk หรือ running cost แบบ Average) บนทุกเอกสาร `tb_stock_in` / `tb_stock_out` ก่อนอนุมัติ, cross-reference ต้นทุน lot ใหม่กับ tolerance ของ vendor pricelist, และรัน "cost-anomaly dashboard" เชิงรุก การตรวจสอบกับซอร์สปัจจุบันไม่พบสิ่งใดเลย:

- **ไม่มี approval queue สำหรับ stock-in / stock-out เลย** [inventory-adjustment](/th/inventory/inventory-adjustment) § 1 (ยืนยันแล้ว) พบว่า **การสร้างคือการ post**: `StockInService.create()` / `StockOutService.create()` เขียน `doc_status = completed` ทันที ในการเรียกเดียวกันที่ post เข้า ledger — ไม่ว่า client จะส่งปุ่มไหนมา (Save vs Submit) ไม่มี draft state ที่เข้าถึงได้ จึงไม่มีอะไรเหลืออยู่ใน pending state ให้ approver ใดทำ
- **ไม่มีการแยก Store Keeper กับ Inventory Controller ในโมดูลนี้** nav entry, หน้าจอ create/edit, และ list ทั้งหมด gate ด้วย permission ทั่วไปเดียวคือ `inventory_management.view`; ไม่มี workflow stage, approval queue, หรือการกำหนด `enum_stage_role` ที่ใดเลยใน `stock-in.service.ts` / `stock-out.service.ts`
- **ไม่มีหน้าจอ "cost-pick preview" อยู่จริง** ฟอร์ม stock-in/stock-out แสดงฟิลด์ที่ user กรอก (cost แก้ไขได้บน stock-in, ซ่อนทั้งหมดบน stock-out — ledger เลือกเองตอนเขียน) ไม่มีขั้นตอน preview แยกที่แสดงว่า FIFO lot ไหนจะถูก consume ก่อนเอกสาร post
- **ไม่พบการตรวจ adjustment-cost-basis เทียบ vendor-pricelist tolerance ในโค้ดของโมดูลนี้** แม้ `tb_product.price_deviation_limit` จะเป็นฟิลด์ที่มีอยู่จริง (มันถูกอ่านที่อื่น — ดู [product](/th/inventory/product))

สอดคล้องกับข้อค้นพบเดียวกันที่ยืนยันแล้วใน [inventory-adjustment/03-user-flow](/th/inventory/inventory-adjustment/03-user-flow) ("สองหน้าจอที่ไม่แยกแยะ... ไม่มี approval action ให้ persona นี้ทำ เพราะไม่มีอะไรเหลืออยู่ใน pending state ที่ทวนได้")

## 2. พฤติกรรมจริงอยู่ที่ไหน

| เคย claim ที่นี่ | กลไกจริง | หน้า |
|---|---|---|
| Controller ทบทวน cost-pick preview ก่อนอนุมัติ adjustment | Stock-in/stock-out post ทันทีเมื่อสร้าง ไม่มีอะไรให้อนุมัติ | [inventory-adjustment](/th/inventory/inventory-adjustment) § 1 |
| Controller ตรวจต้นทุน lot ใหม่เทียบ vendor pricelist tolerance | ไม่พบการตรวจแบบนี้ในโค้ดของโมดูลนี้ | [inventory-adjustment/02-business-rules](/th/inventory/inventory-adjustment/02-business-rules) |
| Controller ตรวจสอบ valuation variance ที่ Finance escalate มา | ไม่มี Finance persona ให้ escalate จาก — ดู [03-user-flow-finance](./03-user-flow-finance.md) | — |
| Controller เซ็นรับรอง pre-period-end variance review แล้วรันการปิดงวด | จริง: ผู้ถือ `inventory_management.period_end.execute` ทำงาน review checklist แล้วคลิก **Close period** | [inventory/03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-adjustment/` (`stock-in.service.ts`, `stock-out.service.ts` — `create()` post ทันที), `.../period-end/`
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/`, `.../period-end/`
- Parent overview: [03-user-flow](./03-user-flow.md)
- Cross-link: [inventory-adjustment](/th/inventory/inventory-adjustment) — โมดูลที่เป็นเจ้าของ `tb_stock_in`/`tb_stock_out` จริง ๆ ที่ฉบับร่างก่อนหน้าของหน้านี้อธิบายผิด
- Cross-link: [inventory/03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller) — flow การปิดงวด period-end ที่มีอยู่จริง
