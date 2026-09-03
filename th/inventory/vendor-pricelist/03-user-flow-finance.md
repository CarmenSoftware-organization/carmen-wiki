---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Finance (แก้ไข)
description: หน้าแก้ไข — Finance ไม่ใช่ persona แยกต่างหากในโมดูล vendor-pricelist ไม่มีกลไก co-signoff หรือ variance-audit อยู่ในโมดูลนี้
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, finance, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Finance (แก้ไข)

> **หน้านี้เคยอธิบาย persona Finance Officer / Finance Manager แบบเต็มรูปแบบ** — gate co-signoff ก่อน activate สำหรับ pricelist multi-currency / high-value และ dashboard variance-audit หลังรับสินค้าที่ join แถว pricelist กับบันทึก GRN และ invoice การอ่าน `price-list.service.ts`, `price-list-template.service.ts` และ `request-for-pricing.service.ts` โดยตรงอีกครั้ง (2026-07-16) ไม่พบโค้ดที่ตรงกับสิ่งใดเลย และไม่มี member `enum_stage_role` สำหรับ `finance` อยู่ที่ใดใน schema — สอดคล้องกับข้อค้นพบที่ยืนยันแล้วเช่นเดียวกันสำหรับหน้า Finance-persona ของโมดูล `purchase-order` และ `good-receive-note` เอง

## สิ่งที่เคยอ้างเทียบกับสิ่งที่มีอยู่จริง

| ข้ออ้าง | สถานะ |
| ----- | ------ |
| ต้องการ co-signoff จาก Finance Manager เพื่อ activate pricelist multi-currency หรือ "high-value" | **ไม่ได้ implement** ไม่มี endpoint approve แยกต่างหากบน Price List เลย — `status` ถูกตั้งผ่าน update call ปกติ โดยใครก็ตามที่มีสิทธิ์แก้ record นั้น การค้นหา `threshold` ทั่ว repo ในโมดูลนี้คืนผลเป็นศูนย์ hit ที่เกี่ยวข้อง |
| Dashboard variance-audit ของ Finance Officer ที่ join `tb_pricelist_detail` กับบันทึก GRN / invoice ที่ post แล้ว | **ไม่ได้ implement** ไม่มี dashboard, รายงาน หรือ query surface เช่นนี้อยู่ใน frontend หรือ backend ของโมดูลนี้ |
| `system` comment ฝั่ง Finance ที่บันทึก sign-off / การจัดประเภท variance | **ไม่ได้ implement** ไม่มี service ใดในโมดูลนี้เขียนแถว comment โดยอัตโนมัติภายใต้สถานการณ์ใด ๆ — ดู [01a-data-model-comments](/th/inventory/vendor-pricelist/01a-data-model-comments) |
| การ validate สกุลเงิน / FX ที่ทำโดย Finance ตอน activate pricelist | **ไม่ได้ implement** ไม่มีการ lookup อัตรา FX หรือการเช็ครายการสกุลเงินที่อนุญาตใน `price-list.service.ts` |

## สิ่งที่เป็นจริง

- User ใดก็ตามที่มีสิทธิ์อ่านหน้าจอ Price List สามารถเห็น `currency_id`/`currency_code` ของ pricelist และแถว detail ของมันได้ — ไม่มีอะไรที่ route สิ่งนี้ไปยัง user ที่ tag ว่าเป็น Finance โดยเฉพาะ
- Price variance ฝั่ง GRN ถ้ามีการ implement เป็นเรื่องของโมดูล [good-receive-note](/th/inventory/good-receive-note) — ให้ดูข้อค้นพบ resync ของโมดูลนั้นเองแทนหน้านี้ สำหรับสิ่งที่ GRN เปรียบเทียบจริงกับ pricelist
- ถ้าต้องการ surface variance หรือ currency-governance ที่ Finance ใช้ได้ วันนี้ยังไม่มีอยู่จริง และจะเป็นงาน feature ใหม่ ไม่ใช่ช่องว่างด้านเอกสาร

## แหล่งอ้างอิง

- [vendor-pricelist](/th/inventory/vendor-pricelist) — หน้า landing โมดูล, ตาราง role ที่แก้ไขแล้ว
- [02-business-rules.md](./02-business-rules.md) § 4 — ข้ออ้าง authorization ที่ confirmed-vs-design-target
- [03-user-flow.md](./03-user-flow.md) — ดัชนี persona (Finance ถูกลบออก)
- [good-receive-note](/th/inventory/good-receive-note) — โมดูลที่เป็นเจ้าของพฤติกรรม price-variance ฝั่ง GRN จริง ๆ
