---
title: ใบสั่งซื้อ (Purchase Order) — User Flow — Finance
description: เส้นทางผู้ใช้งานของ Finance ภายในโมดูล purchase-order — persona ที่ยังไม่ยืนยัน; บันทึกสิ่งที่ยืนยันแล้วและยังไม่ยืนยันใน source ปัจจุบัน
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, user-flow, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# ใบสั่งซื้อ (Purchase Order) — User Flow — Finance

> **At a Glance**
> **Persona:** Finance — **ยังไม่ยืนยันว่าเป็น persona ที่แยกต่างหากใน source ปัจจุบัน** &nbsp;·&nbsp; **Module:** [purchase-order](/th/inventory/purchase-order)
> **หน้านี้บันทึกอะไร:** เหตุผลที่ flow "Finance" ที่เคยอธิบายไว้ก่อนหน้า (pre-transmission sign-off + three-way match + AP posting) ไม่ตรงกับ source ปัจจุบัน และสิ่งที่ยืนยันแล้วจริง ๆ คืออะไร

> ⚠️ **การแก้ไขครั้งใหญ่ในรอบนี้** เวอร์ชันก่อนหน้าของหน้านี้อธิบาย **Finance Manager** ที่ทำ pre-transmission review stage และ persona **Finance Officer / AP** ที่รัน three-way match (PO ↔ GRN ↔ vendor invoice) พร้อม GL account postings, การจัดการ purchase-price-variance, และ FX-adjustment entries ทั้งหมดนี้ไม่พบใน source ปัจจุบัน:
> - การค้นหาทั่ว repo ใน `carmen-turborepo-backend-v2` และ `carmen-inventory-frontend-react` สำหรับ `three-way`, `threeWay`, `vendor_invoice`, `VendorInvoice`, และ `tb_invoice` คืนผลลัพธ์ **ศูนย์รายการ** ไม่มีหน้า capture vendor invoice ไม่มี AP-posting endpoint และไม่มี match algorithm ใด ๆ ใน codebase ปัจจุบัน
> - `enum_stage_role` (`create`, `approve`, `purchase`, `issue`, `view_only`) ไม่มี member เฉพาะสำหรับ `finance` — "Finance stage" จะเป็นเพียง generic `approve` stage ที่ assign ให้ user ที่ตั้งชื่อว่า Finance เหมือน approver อื่น ๆ
> - หลักฐานประกอบชิ้นเดียวสำหรับ actor ที่เกี่ยวข้องกับ Finance คือ e2e fixture user `fc@blueledgers.com` ซึ่ง `04-test-scenarios.md` บันทึกว่าเป็น persona **Procurement Manager (FC Approver)** — กล่าวคือ test fixtures ปัจจุบันถือว่า "FC" และ "Procurement Manager" เป็น approval-stage actor เดียวกัน ไม่ใช่ Finance persona ที่แยกต่างหาก
> - feature เดียวที่ **จริง** และเกี่ยวข้องกับ AP ในโมดูลนี้คือ [Credit Note](/th/inventory/purchase-order/credit-note) — เอกสารที่ implement จริง (`tb_credit_note`, Prisma line numbers จริง, routes จริง) ที่ post AP debit memo เทียบกับ GRN ก่อนหน้า มันไม่ใช่ three-way match และไม่เกี่ยวข้องกับการ capture vendor invoice
>
> หน้านี้ถูกเก็บไว้ (แทนที่จะลบ) เพราะชุด persona ของโมดูลตั้งชื่อ Finance ไว้ในตาราง legacy role ของหน้า landing; เนื้อหาด้านล่างบันทึกการแก้ไขแทนที่จะทำซ้ำ flow ที่ fabricated ดู module progress-log Discrepancy entry สำหรับ source-check trail เต็ม

## 1. สิ่งที่ยืนยันแล้วและยังไม่ยืนยัน

| ข้อกล่าวอ้างจากเวอร์ชันก่อนหน้า | สถานะ |
|---|---|
| workflow stage แบบ pre-transmission review ของ "Finance Manager" ที่แยกต่างหาก | **ยังไม่ยืนยัน** ไม่มี `finance` stage role อยู่จริง; tenant ใด ๆ *สามารถ* ตั้งชื่อ approver ว่า "Finance Manager" ได้ผ่าน workflow configuration ทั่วไปที่ assign user ใดก็ได้ให้ generic `approve` stage แต่ไม่มี code path เฉพาะที่ปฏิบัติต่อ Finance ต่างจาก approver อื่นใด |
| Three-way match (PO ↔ GRN ↔ vendor invoice) | **ไม่ได้ implement** ไม่พบ invoice entity, หน้า capture, หรือ match algorithm ใด ๆ |
| AP liability posting / GL account entries (GRN-accrual, AP-Trade, VAT-input) | **ไม่ได้ implement** ไม่พบโมดูล AP หรือ code สำหรับ GL-posting ใน repo นี้ |
| Purchase-price-variance (PPV) และ FX-adjustment postings บน invoice match | **ไม่ได้ implement** — ขึ้นอยู่กับ feature invoice/match ที่ไม่มีอยู่จริง |
| `PO_AUTH_009` (สิทธิ์อ่าน report แบบ read-only) | เป็นไปได้ในฐานะ generic RBAC read grant แต่ไม่มี permission key เฉพาะของ Finance ที่ยืนยันได้ |
| Credit Note ในฐานะเอกสารแก้ไข post-receipt ที่เกี่ยวข้องกับ AP | **ยืนยันว่ามีจริง** — ดู [Credit Note](/th/inventory/purchase-order/credit-note) |

## 2. จะทำอย่างไรกับหน้านี้

จนกว่า feature Finance/AP-invoicing จะได้รับการยืนยันว่ามีอยู่จริง (ใน repo นี้หรือ backend service พี่น้องที่ยังไม่ได้สำรวจ) อย่าถือว่าข้อกล่าวอ้างเรื่อง "three-way match", "AP posting", หรือ "Finance Manager sign-off" ในหน้าอื่น ๆ ของโมดูลนี้เป็น behavior ที่ใช้งานจริง สำหรับหน้าที่ยังอ้างอิง `PO_POST_008` / `PO_POST_009` (three-way match) หรือ `PO_XMOD_007` (AP/three-way match), [02-business-rules.md](./02-business-rules.md) § 5 / § 6 ตอนนี้ flag rule ID เหล่านั้นว่ายังไม่ได้ implement แทนที่จะอธิบายว่าเป็น rule ที่ใช้งานได้

หากการมีส่วนร่วมของ Finance ในโมดูล PO เป็น product requirement ในระยะใกล้ แนวทางที่ใกล้เคียงที่สุดที่มีอยู่คือ (a) assign user ที่ตั้งชื่อว่า Finance ให้กับ generic `approve` workflow stage (mechanism เดียวกับที่ Procurement Manager ใช้) และ (b) ใช้ [Credit Note](/th/inventory/purchase-order/credit-note) สำหรับการแก้ไข AP หลัง receipt การสร้าง feature invoice-capture / matching จริง ๆ จะเป็น functionality ใหม่ ไม่ใช่ documentation gap

## 3. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — global PO state machine; Finance ถูกระบุไว้ที่นั่นว่ายังไม่ยืนยัน
- Sibling: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md) — mechanism generic approve-stage จริงที่ Finance-titled approver ใด ๆ จะใช้ในปัจจุบัน
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — GRN posting คือ event จริงที่ขับเคลื่อน PO receipt status; ไม่มี invoice-matching event ตามมาใน source ปัจจุบัน
- [Credit Note](/th/inventory/purchase-order/credit-note) — เอกสารที่เกี่ยวข้องกับ AP ที่ implement จริงหนึ่งเดียวในโมดูลนี้
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 5 (`PO_POST_008` / `PO_POST_009`, ทำเครื่องหมายว่ายังไม่ implement), § 6 (`PO_XMOD_007`, ทำเครื่องหมายว่ายังไม่ implement)
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — แหล่ง design ดั้งเดิมสำหรับแนวคิด three-way-match; ถือเป็น design intent ไม่ใช่ verified behavior ปัจจุบัน
