---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Audit & Config (Correction)
description: บันทึก correction — ไม่มี surface ของ Approver/Finance, Auditor หรือ Sysadmin สำหรับการนับสต๊อกประจำงวด
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — Audit & Config (Correction)

> **At a Glance**
> **Status:** กลุ่ม persona ที่ยืนยันแล้วว่าไม่มีอยู่จริง &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **สิ่งที่แทนที่หน้านี้:** [04-test-scenarios-count-lead](/th/inventory/physical-count/04-test-scenarios-count-lead) และ [04-test-scenarios-counter](/th/inventory/physical-count/04-test-scenarios-counter)

## 1. สิ่งที่หน้านี้เคยอ้าง

Draft ก่อนหน้าของโมดูลวิกินี้ catalogue scenario ของ Approver/Finance, Auditor และ Sysadmin ไว้ประมาณสามสิบข้อสำหรับการนับสต๊อกประจำงวด — การ review และอนุมัติ variance-rollup adjustment, การสังเกตการนับขณะ in-progress, การตรวจ audit chain เต็ม, และการตั้งค่า tolerance threshold, default costing method และการ map reason-code

## 2. เหตุผลที่ถูกลบออก

ดู [03-user-flow-audit-config.md](/th/inventory/physical-count/03-user-flow-audit-config) สำหรับการแจกแจงทีละ source โดยละเอียด สรุปคือ: โมดูลนี้มี permission key เดียวเท่านั้น (`inventory_management.physical_count`) เอกสาร rollup ถูก insert ที่ `doc_status = completed` ทันทีโดยไม่มี stage ให้อนุมัติ ไม่มีกลไก tolerance หรือ recount ใด ๆ ให้ config และไม่มี reason-code mapping ใด ๆ ถูกอ่านโดย rollup เลย (`adjustment_type_id` คงเป็น `null`) ไม่มีอะไรเหลือให้เขียน scenario เทียบสำหรับกลุ่ม persona นี้

## 3. ควรอ่านอะไรแทน

- [physical-count/04-test-scenarios-count-lead](/th/inventory/physical-count/04-test-scenarios-count-lead) — scenario ของหน้ารายการ
- [physical-count/04-test-scenarios-counter](/th/inventory/physical-count/04-test-scenarios-counter) — scenario ของหน้า entry/review รวมถึงกฎ validation และ posting จริงเพียงชุดเดียวของโมดูล
- [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) § 4 — scenario end-to-end ที่ครอบคลุมทั้งสองหน้าจอ

## 4. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`
- ที่เกี่ยวข้อง: [physical-count/03-user-flow-audit-config](/th/inventory/physical-count/03-user-flow-audit-config) (หน้า correction คู่ขนานฝั่ง user-flow)
