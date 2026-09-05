---
title: Cluster — UI Screens
description: หน้าจอ ClusterManagement (list) และ ClusterEdit (create/view/edit) — เลย์เอาต์แผ่นป้าย+แท็บ, แท็บ Licensing, filter, dialog และ persisted state
published: true
date: 2026-09-05T04:19:00.000Z
tags: book/platform, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

## 1. At a Glance

- `ClusterManagement` — DataTable พร้อมแถบสรุป **Fleet Capacity** ทั้งฝูงเหนือตาราง (อ่านจาก endpoint เฉพาะ `GET /api-system/clusters/summary` แล้ว ไม่ผูกกับช่องค้นหา), filter (รวมสถิติ **Quota expiring** ที่คลิกได้ใหม่), ส่งออก CSV (คอลัมน์ `BU Quota`/`Quota Expires` แทน `max_license_bu` เดิม), คอลัมน์ audit Created/Updated, ปุ่ม Add และ row action Edit/**View History (ใหม่, `activity_log.read`)**/Delete ที่ gate ด้วย `<Can>` (cluster-scoped) — Name cell มี `BrandMark` avatar เล็ก ๆ กำกับแล้ว
- `ClusterEdit` — **เขียนใหม่อีกรอบเมื่อ 2026-08-23** (commit `69027b9`) จากเอกสารแบบ scrollspy คอลัมน์เดียว มาเป็นแผ่นป้ายตัวตนที่แสดงตลอด (`ClusterPlate` — branding, ชื่อ, สถานะ, code/alias, มาตรวัดไลเซนส์แบบ tick-strip) พร้อม 3 แท็บด้านล่าง: **Licensing** (ค่าเริ่มต้น — สรุปสัญญาแบบอ่านอย่างเดียว + ปุ่มลิงก์ License Center), **Business Units** (ไม่มีคอลัมน์ Users ต่อแถวแล้ว แต่มีป้าย "Over limit" ตามอันดับแทน), **Users** (ไม่มีคอลัมน์/field Business Unit หรือ bulk action "Move to BU" แล้ว — เหลือ bulk action เดียวคือ Remove) ไม่มี tab/section "Details"/"Branding"/"Overview" แยกอีกต่อไป — field เหล่านั้นย้ายเข้าไปอยู่บนแผ่นป้ายที่แสดงตลอดเวลาแทน
- โหมด create เขียนใหม่ (commit `50386b9`) เป็นสองคอลัมน์: พรีวิว `ClusterDraftPlate` แบบสดข้างฟอร์มสองการ์ด — Identity และการ์ดใหม่ **First Quota Licence** (`licensed_bus`/`license_end_date`/Never-expires ที่จำเป็นต้องกรอก) ซึ่งออกใบโควตา BU แถวแรกให้ cluster ตั้งแต่สร้าง — ไม่มี field `max_license_bu` หรือ checkbox `is_active` บนฟอร์ม create แล้ว
- Endpoint แบบพหูพจน์: `GET/POST /api-system/clusters`, `GET /api-system/clusters/summary` (ใหม่), `PUT/DELETE /api-system/clusters/:id`, `GET /api-system/user/clusters/:clusterId`, `POST /api-system/clusters/:id/logo`, `POST /api-system/clusters/:id/avatar`

## 2. References

- ../carmen-platform/src/pages/ClusterManagement.tsx
- ../carmen-platform/src/pages/ClusterEdit.tsx
- ../carmen-platform/src/pages/clusterEdit/{ClusterPlate,ClusterDraftPlate,PlateField,clusterTabs,useClusterUsers,TableToolbar,BulkActionBar,InlineCell}.ts(x), sections/{BusinessUnitsSection,UsersSection,SubscriptionCard}.tsx — component ปัจจุบัน (`ClusterEditNav`/`useScrollSpy`/`DetailsSection`/`BrandingSection` ยังอยู่ในโค้ดแต่ตอนนี้เป็นของหน้า cluster-admin แล้ว ไม่ใช่หน้านี้)
- ../carmen-platform/src/pages/clusterManagement/{FleetCapacity,CapacityGauge,CapacityMeter,ClusterCreateForm,ClusterIdentityFields}.tsx, ../carmen-platform/src/utils/capacity.ts
- ../carmen-platform/src/utils/businessUnitRank.ts — ตรรกะป้าย "Over limit"
- ../carmen-platform/src/components/BrandingImageUpload.tsx
- ../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail}.tsx — แผ่นประวัติที่ใช้ร่วมกันของทั้งสองหน้าจอ

## 3. TODO

- [ ] Capture screenshots เข้า assets/screenshots/platform/clusters/ (เลย์เอาต์เปลี่ยนเป็นแผ่นป้าย+3 แท็บแล้วตั้งแต่ 2026-08-23 — capture ใหม่ต้องรอเลย์เอาต์นี้ ไม่ใช่ scrollspy เดิม)
- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/clusters/ui-screens (filter, dialog, persisted state ทั้ง 7 key, แท็บ Licensing, ฟอร์ม create แบบสองการ์ด)
- [ ] หมายเหตุ e2e: `../carmen-platform-e2e/tests/clusters/` (แก้ล่าสุด 2026-06-26/2026-08-22) เก่ากว่าการเขียนใหม่วันที่ 2026-08-23 — page object ยังอ้างปุ่ม Edit ระดับหน้าที่ไม่มีอยู่แล้ว และ fillForm() ไม่กรอก `licensed_bus`/`license_end_date` ที่ตอนนี้จำเป็น — ต้องปรับปรุงก่อนใช้เป็นหลักฐานพฤติกรรม
