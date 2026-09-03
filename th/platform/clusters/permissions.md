---
title: Cluster — Permissions
description: Route guard แบบ permission-key, gate <Can> ภายในหน้า, ข้อยกเว้น bootstrap และ filter ของ sidebar สำหรับทุก operation ของ cluster
published: true
date: 2026-07-29T06:35:38.000Z
tags: book/platform, clusters, permissions
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Permissions

## 1. At a Glance

- Route guard: `/clusters` → `cluster.read`, `/clusters/new` → `cluster.create`, `/clusters/:id/edit` → `cluster.update` (prop `requiredPermission` บน `PrivateRoute`)
- Gate ภายในหน้า: `<Can>` ห่อ Add Cluster (`cluster.create`), Edit ของ row (`cluster.update`), Delete ของ row (`cluster.delete`) และทุก field/action บนหน้า edit (`cluster.update`) ผ่าน boolean `canEdit` ตัวเดียวที่คำนวณครั้งเดียวต่อหน้า — **ไม่มี toggle Edit แยกต่างหากอีกต่อไป** — gate ของ row และหน้า edit เป็นแบบ **cluster-scoped** ผ่าน prop `clusterId`
- `cluster.delete` มีอยู่เฉพาะในรูป gate ภายในหน้า — ไม่มี route ใดต้องการ key นี้ — และการลบยังถูกบล็อกฝั่ง client เพิ่มเติมเมื่อ cluster ยังมี business unit อยู่
- Gotcha การ reuse key: route `/business-units*` ใช้ key `cluster.*` ชุดเดียวกัน — ไม่มี key `business_unit.*`
- ข้อยกเว้น bootstrap: `hasPermission` คืน `true` โดยไม่มีเงื่อนไขเมื่อ `userCount !== null && userCount <= 1` (ตั้งค่า admin คนแรก)
- เมื่อไม่ผ่าน: ตอนนี้เป็น `<Forbidden>` (หน้า 403 แยกต่างหาก แทนที่ `<AccessDenied>` เดิมที่เคย define ในไฟล์เดียวกับ `PrivateRoute`) render ภายใน `<Layout>` (sidebar ยังมองเห็นอยู่) พร้อมปุ่ม "Go Back" และ "Go to Dashboard"
- เอกสารโมเดล canonical: [rbac permissions](/th/platform/rbac/permissions)

## 2. References

- ../carmen-platform/src/App.tsx — route ทั้งสามของ cluster พร้อม prop `requiredPermission` (`SITEMAP.md` ยังแสดง role list รุ่นเก่าและ stale ในคอลัมน์ access)
- ../carmen-platform/src/components/Can.tsx, ../carmen-platform/src/context/AuthContext.tsx, ../carmen-platform/src/utils/permissions.ts
- ../carmen-platform/src/pages/Forbidden.tsx, ../carmen-platform/src/pages/NotFound.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/clusters/permissions (เมทริกซ์ effective access, รายละเอียดข้อยกเว้น bootstrap, พฤติกรรม Forbidden/NotFound, filter ของ sidebar)
