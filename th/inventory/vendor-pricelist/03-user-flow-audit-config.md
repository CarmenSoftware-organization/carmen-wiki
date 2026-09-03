---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Audit & Config (แก้ไข)
description: หน้าแก้ไข — ไม่มี Audit workspace หรือ Configuration console เฉพาะทางอยู่ในโมดูล vendor-pricelist
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, audit-config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Audit & Config (แก้ไข)

> **หน้านี้เคยอธิบาย persona Auditor** (workspace query-builder เหนือ template/campaign/invitation/pricelist พร้อมการเช็ค segregation-of-duties และ quality-score) **และ persona System Administrator** (การกำหนดเลข, RBAC, นโยบาย portal-token, การเชื่อม email, registry กติกา validation, การตั้งค่าแหล่ง FX และการ revoke token ต่อ invitation แต่ละหน้าการตั้งค่าของตัวเอง) การอ่าน service ทั้งสี่ของโมดูลโดยตรงอีกครั้ง (2026-07-16) ไม่พบโค้ดที่ตรงกับสิ่งใดเลย — สอดคล้องกับ pattern ที่ยืนยันว่าไม่มีอยู่จริงซึ่งมีเอกสารไว้แล้วสำหรับหน้า "Audit / Config" ที่เทียบเท่ากันในโมดูล `purchase-order`, `good-receive-note`, `store-requisition`, `inventory`, `inventory-adjustment`, `physical-count` และ `spot-check`

## สิ่งที่เคยอ้างเทียบกับสิ่งที่มีอยู่จริง

| ข้ออ้าง | สถานะ |
| ----- | ------ |
| Workspace audit "Pricelist Activity Queries" เฉพาะทางพร้อม saved query template | **ไม่ได้ implement** ไม่มี route หรือ component เช่นนี้อยู่จริง |
| การตรวจสอบ segregation-of-duties (ผู้ถือ vendor-token ≠ ผู้ approve; ผู้แก้ high-value ≠ ผู้ approve) | **ไม่ได้ implement** ไม่มี cross-check เช่นนี้อยู่ใน service ใดของโมดูลนี้ |
| การตั้งค่านโยบาย portal-token (expiration, IP allowlist, ขีดจำกัด concurrent-session, การตรวจจับ suspicious-activity) | **ไม่ได้ implement** `checkPricelist()` ของ `check-price-list.service.ts` ไม่เคยเช็ควันหมดอายุ, IP address หรือจำนวน session เลย |
| Action "Revoke Token" ต่อ invitation | **ไม่ได้ implement** ไม่มี endpoint ใดตั้ง `pricelist_url_token` กลับเป็น `NULL` ที่ใดใน backend; token ถูกเขียนครั้งเดียวตอน RFQ-create |
| Console การตั้งค่า pricelist-numbering / RBAC / email-integration / validation-rule-registry / FX-source เฉพาะทาง | **ไม่ได้ implement ในฐานะหน้าจอเฉพาะของ VPL** การกำหนดเลข generic (`tb_config_running_code` ที่ใช้โดย `generatePLNo()`), RBAC และ currency master data มีอยู่ที่อื่นในผลิตภัณฑ์ (ดู book/โมดูล `system-config` และ `master-data`) แต่ไม่มีหน้าการตั้งค่าเฉพาะ pricelist ที่ซ้อนทับบนสิ่งเหล่านั้น |
| การเปลี่ยนการตั้งค่า snapshot อย่างสะอาดสำหรับเอกสารที่อยู่ในการบิน พร้อม log audit การตั้งค่าที่ rollback ได้ | **ไม่ได้ implement** ไม่มีกลไก configuration-versioning ในโมดูลนี้ที่จะ snapshot หรือ rollback ได้ตั้งแต่แรก |

## สิ่งที่เป็นจริง

- Pattern running-code generic (`tb_config_running_code`, type `PRICE-LIST`) ขับการสร้าง `pricelist_no` — นี่คือกลไกการกำหนดเลข generic เดียวกับที่ใช้ทั่วผลิตภัณฑ์ ไม่ใช่ console การกำหนดเลขเฉพาะ pricelist
- ตาราง comment มีอยู่จริงและมี manual CRUD endpoint ของตัวเองต่อ entity family ใช้ได้โดย user ที่ authorized คนใดก็ได้สำหรับโน้ต free-text — แต่การเขียนหนึ่งครั้งเป็น action แบบ manual เสมอ ไม่เคยเป็น audit-trail entry อัตโนมัติ (ดู [01a-data-model-comments](/th/inventory/vendor-pricelist/01a-data-model-comments))
- ถ้าต้องการ audit query surface เฉพาะทางหรือ action token-revocation วันนี้ยังไม่มีอยู่จริง และจะเป็นงาน feature ใหม่ ไม่ใช่ช่องว่างด้านเอกสาร

## แหล่งอ้างอิง

- [vendor-pricelist](/th/inventory/vendor-pricelist) — หน้า landing โมดูล, ตาราง role ที่แก้ไขแล้ว
- [02-business-rules.md](./02-business-rules.md) § 4, § 5.4 — ข้ออ้าง authorization และสถานะที่ confirmed-vs-design-target รวมถึง confirmed gap ของ portal-token
- [03-user-flow.md](./03-user-flow.md) — ดัชนี persona (Audit/Config ถูกลบออก)
- [system-config](/th/inventory/system-config), [master-data](/th/inventory/master-data), [access-control](/th/inventory/access-control) — ที่ซึ่งหน้าจอการตั้งค่าการกำหนดเลข / currency / RBAC generic ที่แท้จริงอยู่
