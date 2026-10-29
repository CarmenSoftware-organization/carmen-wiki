---
title: Cluster — UI Screens
description: หน้าจอ ClusterManagement (list) และ ClusterEdit (create/view/edit) — เลย์เอาต์แผ่นป้าย+แท็บ, แท็บ Licensing, filter, dialog และ persisted state
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

![Cluster — UI Screens screen](/screenshots/platform/clusters/ui-screens.png)

![Cluster — UI Screens form screen](/screenshots/platform/clusters/ui-screens-form.png)

## 1. At a Glance

- `ClusterManagement` — DataTable พร้อมแถบสรุป **Fleet Capacity** ทั้งฝูงเหนือตาราง (อ่านจาก endpoint เฉพาะ `GET /api-system/clusters/summary` แล้ว ไม่ผูกกับช่องค้นหา), filter (รวมสถิติ **Quota expiring** ที่คลิกได้ใหม่), ส่งออก CSV (คอลัมน์ `BU Quota`/`Quota Expires` แทน `max_license_bu` เดิม), คอลัมน์ audit Created/Updated, ปุ่ม Add และ row action Edit/**View History (ใหม่, `activity_log.read`)**/Delete ที่ gate ด้วย `<Can>` (cluster-scoped) — Name cell มี `BrandMark` avatar เล็ก ๆ กำกับแล้ว
- `ClusterEdit` — **เขียนใหม่อีกรอบเมื่อ 2026-08-23** (commit `69027b9`) จากเอกสารแบบ scrollspy คอลัมน์เดียว มาเป็นแผ่นป้ายตัวตนที่แสดงตลอด (`ClusterPlate` — branding, ชื่อ, สถานะ, code/alias, มาตรวัดไลเซนส์แบบ tick-strip) พร้อมแท็บด้านล่าง: **Licensing** (ค่าเริ่มต้น — สรุปสัญญาแบบอ่านอย่างเดียว + ปุ่มลิงก์ License Center), **Business Units** (ไม่มีคอลัมน์ Users ต่อแถวแล้ว แต่มีป้าย "Over limit" ตามอันดับแทน; ตั้งแต่ PR #292 หัวคอลัมน์ Code/Name/Status เป็นปุ่ม `SortableTableHead` ที่วนลำดับ unsorted → asc → desc ผ่าน `cycleSort`/`sortRows` จาก `src/utils/tableSort.ts`), **Users** (ไม่มีคอลัมน์/field Business Unit หรือ bulk action "Move to BU" แล้ว — เหลือ bulk action เดียวคือ Remove; หัวคอลัมน์ Name/Role/Status เรียงใน memory ได้ตั้งแต่ PR #292 เช่นกัน) และ — ตั้งแต่ 2026-10-26 — **Notes** (บันทึกภายในสำหรับเจ้าหน้าที่ แสดงเมื่อมี `cluster_note.view` เท่านั้น ดู §4.6 ของหน้า en) ไม่มี tab/section "Details"/"Branding"/"Overview" แยกอีกต่อไป — field เหล่านั้นย้ายเข้าไปอยู่บนแผ่นป้ายที่แสดงตลอดเวลาแทน
- **การจัดการที่นั่ง (ใหม่ 2026-10-26/27):** แท็บ Users มีคอลัมน์ **Seat**, filter "Seat holders only", ปุ่ม **Release / Restore seat** ราย member (แสดงเมื่อ `canEdit`; backend ต้องการ super admin หรือ cluster admin ของคลัสเตอร์นั้น — ผู้ถือ `cluster.update` อย่างเดียวเห็นปุ่มแต่ได้ 403) และ banner เกินโควตา (`SeatOverQuotaBanner`) เมื่อ `used > cap`; badge ของแท็บ Users ยังนับ**สมาชิกภาพ** ขณะที่ rail Seats บนแผ่นป้ายนับผู้ถือที่นั่ง — สองตัวเลขต่างกันได้โดยออกแบบ
- โหมด create เขียนใหม่ (commit `50386b9`) เป็นสองคอลัมน์: พรีวิว `ClusterDraftPlate` แบบสดข้างฟอร์มสองการ์ด — Identity และการ์ดใหม่ **First Quota Licence** (`licensed_bus`/`license_end_date`/Never-expires ที่จำเป็นต้องกรอก) ซึ่งออกใบโควตา BU แถวแรกให้ cluster ตั้งแต่สร้าง — ไม่มี field `max_license_bu` หรือ checkbox `is_active` บนฟอร์ม create แล้ว
- Endpoint แบบพหูพจน์: `GET/POST /api-system/clusters`, `GET /api-system/clusters/summary` (ใหม่), `PUT/DELETE /api-system/clusters/:id`, `GET /api-system/user/clusters/:clusterId`, `POST /api-system/clusters/:id/users/:userId/seat/{release,restore}` (ใหม่), `POST /api-system/clusters/:id/logo`, `POST /api-system/clusters/:id/avatar`
- การอัปโหลด branding บนแผ่นป้าย (ยังจริงอยู่ ไม่เปลี่ยน): รับเฉพาะ `image/jpeg`/`image/png`/`image/webp` ขนาดไม่เกิน 5 MB — ไฟล์ที่ไม่ผ่านจะขึ้น error toast โดย**ไม่ยิง API เลย**; อัปโหลดสำเร็จแล้ว **ไม่ re-fetch cluster record** (ตั้งใจ กันไม่ให้ field ที่ยังไม่ได้บันทึกบนแผ่นป้ายหาย); โหมดอ่านอย่างเดียว (`!canEdit`) แสดงแค่พรีวิว ไม่มีปุ่มอัปโหลด — logo แสดง placeholder เส้นประ, avatar แสดงอักษรย่อ (`BrandMark`) ไม่มีข้อความ "No logo"/"No avatar" แล้ว

## 2. References

- ../carmen-backstage/src/pages/ClusterManagement.tsx
- ../carmen-backstage/src/pages/ClusterEdit.tsx
- ../carmen-backstage/src/pages/clusterEdit/{ClusterPlate,ClusterDraftPlate,PlateField,clusterTabs,useClusterUsers,TableToolbar,BulkActionBar,InlineCell}.ts(x), sections/{BusinessUnitsSection,UsersSection,SubscriptionCard}.tsx — component ปัจจุบัน (`ClusterEditNav`/`useScrollSpy`/`DetailsSection`/`BrandingSection` ยังอยู่ในโค้ดแต่ตอนนี้เป็นของหน้า cluster-admin แล้ว ไม่ใช่หน้านี้)
- ../carmen-backstage/src/pages/clusterManagement/{FleetCapacity,CapacityGauge,CapacityMeter,ClusterCreateForm,ClusterIdentityFields}.tsx, ../carmen-backstage/src/utils/capacity.ts
- ../carmen-backstage/src/utils/businessUnitRank.ts — ตรรกะป้าย "Over limit"
- ../carmen-backstage/src/components/SortableTableHead.tsx, ../carmen-backstage/src/utils/tableSort.ts — การเรียงหัวคอลัมน์ใน memory ของแท็บ Business Units และ Users (PR #292)
- ../carmen-backstage/src/components/BrandingImageUpload.tsx
- ../carmen-backstage/src/components/clusterSeat/{SeatCell,SeatActions,SeatOverQuotaBanner,useSeatActions}.ts(x), src/components/notes/*, src/services/clusterNoteService.ts, src/utils/{seatPool,fetchAllBusinessUnits,fetchAllPages}.ts — การจัดการที่นั่งและแท็บ Notes (§4.4, §4.6)
- ../carmen-backstage/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail}.tsx — แผ่นประวัติที่ใช้ร่วมกันของทั้งสองหน้าจอ

## 3. TODO

- [ ] Capture screenshots เข้า assets/screenshots/platform/clusters/ (เลย์เอาต์เปลี่ยนเป็นแผ่นป้าย+หลายแท็บแล้วตั้งแต่ 2026-08-23 — capture ใหม่ต้องรอเลย์เอาต์นี้ ไม่ใช่ scrollspy เดิม)
- [ ] เขียนเนื้อหาฉบับเต็มตาม en/backstage/clusters/ui-screens (filter, dialog, persisted state ทั้ง 7 key, แท็บ Licensing, ฟอร์ม create แบบสองการ์ด)
- [ ] หมายเหตุ e2e: `../carmen-backstage-e2e/tests/clusters/` (7 spec ประมาณ 900 บรรทัด) ถูกปรับให้เข้ากับโมเดลแผ่นป้ายโดย commit `a5197f4` (2026-09-18) ซึ่งแก้ `pages/ClusterEditPage.ts` ด้วย — ข้อกล่าวอ้างเดิมว่า page object ยังอ้างปุ่ม Edit ระดับหน้าไม่เป็นจริงแล้ว ข้อควรระวังที่ยังเหลือ: suite เก่ากว่าแท็บ Notes และตัวควบคุมที่นั่ง (ไม่มี spec ครอบคลุม) และ `cluster-create.spec.ts` ยังไม่ได้ตรวจซ้ำกับฟิลด์ First Quota Licence ที่จำเป็น
