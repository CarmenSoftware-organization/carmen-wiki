---
title: Cluster — UI Screens
description: หน้าจอ ClusterManagement (list) และ ClusterEdit (view/edit) — เลย์เอาต์, การ์ด Branding, dialog และ persisted state
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

## 1. At a Glance

- `ClusterManagement` — DataTable พร้อมคอลัมน์ thumbnail ของ logo (fallback เป็น avatar), filter, ส่งออก CSV, คอลัมน์ audit Created/Updated (flatten จาก object `audit` แบบ nested), ปุ่ม Add และ row action Edit/Delete ที่ gate ด้วย `<Can>` (cluster-scoped)
- `ClusterEdit` — โหมด view/edit (toggle Edit ถูก gate ด้วย `cluster.update` + `clusterId`), การ์ด Branding (อัปโหลด logo/avatar ผ่าน `BrandingImageUpload` — บันทึกทันทีเมื่ออัปโหลด ไม่ขึ้นกับปุ่ม Save), การ์ด Business Units และการ์ด assignment ของ user
- Quirk หลัง create: navigate ไป `/clusters/:id` ซึ่งไม่ใช่ route ที่ลงทะเบียนไว้ — catch-all พา operator ไปลงที่ Dashboard
- Endpoint แบบพหูพจน์: `GET/POST /api-system/clusters`, `PUT/DELETE /api-system/clusters/:id`, `GET /api-system/user/clusters/:clusterId`

## 2. References

- ../carmen-platform/src/pages/ClusterManagement.tsx
- ../carmen-platform/src/pages/ClusterEdit.tsx
- ../carmen-platform/src/components/BrandingImageUpload.tsx

## 3. TODO

- [ ] Capture screenshots เข้า assets/screenshots/platform/clusters/
- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/clusters/ui-screens (filter, dialog, persisted state ทั้ง 6 key)
