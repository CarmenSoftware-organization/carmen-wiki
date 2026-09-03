---
title: การปรับสต๊อก (Inventory Adjustment) — User Flow — Audit & Config
description: ประกาศแก้ไข — ไม่มี surface เฉพาะของ Auditor หรือ System Administrator สำหรับโมดูลนี้ นอกเหนือจาก master ของ reason code ทั่วไป
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, user-flow, audit, sysadmin, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment) — User Flow — Audit & Config

> **ประกาศแก้ไข** หน้านี้เคยบรรยาย System Administrator ที่กำหนดค่า GL mapping, threshold ของ tenant และ RBAC ของ reason code บวก Auditor ที่รัน SoD-compliance check, lot-recall trace และการยืนยันห่วง void ไม่มีข้อไหนมีอยู่จริงในซอร์สปัจจุบัน นอกเหนือจาก master ของ reason code ที่แท้จริง (และเล็กกว่ามาก)

## สิ่งที่ตรวจสอบแล้ว

- Surface การกำหนดค่าจริงเพียงอย่างเดียวสำหรับโมดูลนี้คือ master ของ reason code (`/config/adjustment-type`, [master-data/adjustment-type](/th/inventory/master-data/adjustment-type)) ซึ่งเป็นหน้าจอ CRUD ธรรมดาสำหรับ `code`, `name`, `type` (`stock_in`/`stock_out`), `description`, `note`, `is_active` — ไม่มีฟิลด์บัญชี GL, ไม่มี flag บังคับแนบเอกสาร, ไม่มีการกำหนดค่า threshold ใด ๆ
- การค้นหาทั่ว repo สำหรับ `threshold` ที่ขอบเขตของโมดูลนี้และ service ที่แชร์กันไม่พบผลลัพธ์ใด ๆ
- การค้นหาทั่ว repo สำหรับการตรวจสอบแบ่งแยกหน้าที่ (เช่น การเปรียบเทียบ `buyer_id`/`created_by_id` ระหว่างใบรับกับ write-off) ไม่พบโค้ดที่ตรงกันใน `stock-in.service.ts` / `stock-out.service.ts`
- ไม่พบหน้าจอ lot-recall trace, หน้ายืนยันห่วง void หรือ audit-trail workspace เฉพาะของโมดูลนี้ใน route ของ frontend
- E2E spec เดียวที่แตะ config surface ของโมดูลนี้คือ `031-adjustment-type.spec.ts` ซึ่งครอบคลุมเพียง CRUD ของ reason code ปกติ (code ไม่ซ้ำ, toggle active/inactive) — ไม่มีอะไรเกี่ยวกับ threshold หรือ GL

## สถานะข้อกล่าวอ้าง

| ข้อกล่าวอ้างก่อนหน้า | สถานะ | สิ่งที่ซอร์สแสดงจริง |
| ---------------------- | ------ | ----------------------- |
| System Administrator ตั้งค่า `info.glAccount`, `requiresDocument`, `requiresQualityCheck`, thresholds | **แต่งขึ้น** | `tb_adjustment_type` ไม่มีฟิลด์เช่นนี้; หน้าจอ reason code จริงแก้ไขได้เพียง `code`/`name`/`type`/`description`/`note`/`is_active` |
| Auditor รัน SoD-compliance check, lot-recall trace, การยืนยันห่วง void สำหรับโมดูลนี้ | **แต่งขึ้น** | ไม่พบ route, component หรือ query ของ backend ที่ตรงกัน |
| การเปลี่ยนการกำหนดค่าใช้ "ล่วงหน้า" กับ threshold ladder | **แต่งขึ้น** | ไม่มี threshold ladder ให้เปลี่ยน |

## ดูที่ไหนแทน

- [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — หน้าจอ CRUD reason code ที่แท้จริง
- [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) — วงจรชีวิตเอกสารจริงของโมดูลนี้
- [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) — กฎจริงของโมดูล ไม่มีห่วงการกำหนดสิทธิ์
- E2E: `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` — spec CRUD reason code จริง
