---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios — Audit & Config (Correction)
description: ประกาศแก้ไข — ไม่มี surface ของ Approver/Finance, Auditor หรือ Sysadmin สำหรับการสุ่มตรวจ
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios — Audit & Config (Correction)

> **At a Glance**
> **Status:** กลุ่ม persona ที่ยืนยันแล้วว่าไม่มีอยู่จริง &nbsp;·&nbsp; **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **สิ่งที่แทนที่:** [04-test-scenarios-inventory-controller](/th/inventory/spot-check/04-test-scenarios-inventory-controller) และ [04-test-scenarios-counter](/th/inventory/spot-check/04-test-scenarios-counter)

## 1. สิ่งที่หน้านี้เคยกล่าวอ้าง

ดราฟต์ก่อนหน้าของ wiki module นี้ catalogue scenario ของ Auditor และ Sysadmin ประมาณยี่สิบสามข้อสำหรับ spot check — การตรวจ audit chain เต็มตั้งแต่ spot-check sheet ผ่านการอนุมัติ rollup adjustment ไปจนถึง journal entry, การ verify segregation-of-duties บนการอนุมัตินั้น, และการ config variance-tolerance threshold, default sampling size/method, และ reason-code mapping

## 2. ทำไมถึงถูกลบออก

ดู [03-user-flow-audit-config.md](/th/inventory/spot-check/03-user-flow-audit-config) สำหรับรายละเอียดทีละ source สรุปคือ: โมดูลนี้มี permission key เดียวเท่านั้น (`inventory_management.spot_check`) การ submit ขั้นสุดท้ายไม่สร้างเอกสาร rollup หรือผล ledger ใด ๆ ให้ใครอนุมัติหรือตรวจสอบ ไม่มีกลไก tolerance หรือ recount ให้ config และไม่มีการ map reason-code ใดถูกอ่านเพราะไม่มี rollup ให้ผูกด้วย ไม่มีอะไรเหลือให้เขียน scenario สำหรับกลุ่ม persona นี้

## 3. สิ่งที่ควรอ่านแทน

- [spot-check/04-test-scenarios-inventory-controller](/th/inventory/spot-check/04-test-scenarios-inventory-controller) — scenario หน้ารายการ/สร้าง
- [spot-check/04-test-scenarios-counter](/th/inventory/spot-check/04-test-scenarios-counter) — scenario หน้า entry/review รวมชุดกฎ validation และ completion จริงหนึ่งเดียวของโมดูล
- [spot-check/04-test-scenarios](/th/inventory/spot-check/04-test-scenarios) § 4 — scenario end-to-end ครอบคลุมทั้งสี่หน้าจอ

## 4. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`
- ที่เกี่ยวข้อง: [spot-check/03-user-flow-audit-config](/th/inventory/spot-check/03-user-flow-audit-config) (หน้า correction คู่ขนานฝั่ง user-flow)
