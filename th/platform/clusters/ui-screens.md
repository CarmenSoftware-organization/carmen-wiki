---
title: Cluster — UI Screens
description: หน้าจอ ClusterManagement (list) และ ClusterEdit (view/edit) — เลย์เอาต์, การ์ด Branding, dialog และ persisted state
published: true
date: 2026-07-29T06:35:38.000Z
tags: book/platform, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

## 1. At a Glance

- `ClusterManagement` — DataTable พร้อมแถบสรุป **Fleet Capacity** ทั้งฝูงเหนือตาราง, filter, ส่งออก CSV, คอลัมน์ audit Created/Updated (flatten จาก object `audit` แบบ nested), ปุ่ม Add และ row action Edit/Delete ที่ gate ด้วย `<Can>` (cluster-scoped) — **ไม่มีคอลัมน์ thumbnail logo ต่อแถวอีกต่อไป** (ถูกลบเมื่อเพิ่มแถบ Fleet Capacity และคอลัมน์ `CapacityMeter`)
- `ClusterEdit` — เขียนใหม่ทั้งหมดเป็นเอกสารแบบ scrollspy คอลัมน์เดียว ("A4" pattern): nav `ClusterEditNav` แบบ sticky พาไปยัง 5 ส่วน (Overview/Details/Branding/Business Units/Users) **ไม่มี toggle Edit ระดับหน้าอีกต่อไป** — field ทุกตัวแก้ไขแบบ in-place ตาม `canEdit = hasPermission('cluster.update', {clusterId})`, มีแถบ "Unsaved changes" แบบ sticky ที่ด้านล่างพร้อมปุ่ม Save/Cancel (`Ctrl/⌘+S` / `Escape`), การบันทึกป้องกันด้วย optimistic lock `doc_version` การ์ด Branding (อัปโหลด logo/avatar ผ่าน `BrandingImageUpload` — บันทึกทันทีเมื่ออัปโหลด ไม่ขึ้นกับปุ่ม Save) ส่วน Business Units และ Users มีช่องค้นหา/filter/sort ของตัวเอง และส่วน Users รองรับแก้ไข role/parent-BU **แบบ inline ในตาราง** (ไม่มี dialog แก้ไขแยกอีกต่อไป) บวก bulk action (Remove, Move to BU)
- Quirk หลัง create ที่เคยพบ **ได้รับการแก้ไขแล้ว**: ตอนนี้ navigate ตรงไป `/clusters/:id/edit` (route ที่ลงทะเบียนไว้แล้ว) แทนที่จะไป `/clusters/:id` ที่ไม่มี route รองรับ
- Endpoint แบบพหูพจน์: `GET/POST /api-system/clusters`, `PUT/DELETE /api-system/clusters/:id`, `GET /api-system/user/clusters/:clusterId`, `POST /api-system/clusters/:id/logo`, `POST /api-system/clusters/:id/avatar`

## 2. References

- ../carmen-platform/src/pages/ClusterManagement.tsx
- ../carmen-platform/src/pages/ClusterEdit.tsx
- ../carmen-platform/src/pages/clusterManagement/{ClusterHero,FleetCapacity,CapacityGauge,CapacityMeter}.tsx, ../carmen-platform/src/utils/capacity.ts
- ../carmen-platform/src/pages/clusterEdit/{ClusterEditNav,useClusterUsers}.ts(x), sections/{DetailsSection,BrandingSection,BusinessUnitsSection,UsersSection}.tsx
- ../carmen-platform/src/components/BrandingImageUpload.tsx

## 3. TODO

- [ ] Capture screenshots เข้า assets/screenshots/platform/clusters/ (เลย์เอาต์เปลี่ยนเป็น scrollspy แล้ว — capture ใหม่ต้องรอเลย์เอาต์นี้)
- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/clusters/ui-screens (filter, dialog, persisted state ทั้ง 6 key, bulk actions)
