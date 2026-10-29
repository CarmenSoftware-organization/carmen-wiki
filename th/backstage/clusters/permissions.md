---
title: Cluster — Permissions
description: Route guard แบบ permission-key, ชั้น feature-flag, gate <Can> ภายในหน้า, layer resolve platform-authority ใหม่ และสิ่งที่ key cluster.* แต่ละตัวเปิดให้ทำ
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, clusters, permissions
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Permissions

## 1. At a Glance

- Route guard: `/clusters` → `cluster.read`, `/clusters/new` → `cluster.create`, `/clusters/:id/edit` → `cluster.update` (prop `requiredPermission` บน `PrivateRoute`) — **ตอนนี้ทั้งสาม route มี prop `feature="clusters"` เพิ่มด้วย** เช็คหลัง permission (§ ดูรายละเอียดในหน้า en)
- Gate ภายในหน้า: `<Can>` ห่อ Add Cluster (`cluster.create`), Edit ของ row (`cluster.update`), **View History ของ row/หัวหน้า edit (`activity_log.read` — ใหม่)**, Delete ของ row (`cluster.delete`) และทุก field/action บนแผ่นป้าย+แท็บของหน้า edit (`cluster.update`) ผ่าน boolean `canEdit` ตัวเดียว — gate ของ row และหน้า edit เป็นแบบ **cluster-scoped** ผ่าน prop `clusterId`
- `cluster.delete` มีอยู่เฉพาะในรูป gate ภายในหน้า — ไม่มี route ใดต้องการ key นี้
- **ใหม่ — layer resolve platform-authority ก่อน permission:** `PrivateRoute` จะเช็คว่า session นี้มีสิทธิ์ platform-wide หรือ cluster-scoped ใด ๆ เลยหรือไม่ ก่อนที่จะเช็ค `requiredPermission` — session ที่ไม่มีเลยแต่มี scope แบบ cluster-admin จะถูก redirect ไป `/cluster-admin` แทนที่จะเห็น 403
- Gotcha การ reuse key: route `/business-units*` ใช้ key `cluster.*` ชุดเดียวกัน — ไม่มี key `business_unit.*`
- ข้อยกเว้น bootstrap: `hasPermission` คืน `true` โดยไม่มีเงื่อนไขเมื่อ `userCount !== null && userCount <= 1` (ไม่เปลี่ยนแปลง)
- เมื่อไม่ผ่าน permission: `<Forbidden>` (หน้า 403) render ภายใน `<Layout>` (sidebar ยังมองเห็นอยู่) — เมื่อไม่ผ่าน feature flag (`hide`): `NotFound` แทน; (`inactive`): หน้า "Coming Soon"
- **ใหม่ในรอบ 2026-10 (§9 ของหน้า en):** key `cluster_note.view` / `cluster_note.manage` gate แท็บ Notes ภายใน `/clusters/:id/edit` (ไม่ใช่ key ของ route; แท็บไม่มีบน `/clusters/new`; `?tab=notes` โดยไม่มี key จะตกกลับไป Licensing เงียบ ๆ); ปุ่ม **Release / Restore seat** บนแท็บ Users แสดงด้วย `canEdit` ใน UI แต่ endpoint ของ backend (`POST /api-system/clusters/:cluster_id/users/:user_id/seat/{release,restore}`) มีแค่ `AppIdGuard` และ authorize ภายใน `micro-cluster` ด้วย `isClusterAdmin` — ต้องเป็น super admin หรือสมาชิก cluster-admin ของคลัสเตอร์นั้น ไม่งั้น 403 `CLUSTER_USER_NOT_CLUSTER_ADMIN` (ผู้ถือ role Backstage ที่มีแค่ `cluster.update` เห็นปุ่มแต่ได้ 403 เมื่อคลิก); restore ตอบ 403 `SEAT_LIMIT_REACHED` เพิ่มเมื่อสระเต็ม
- เอกสารโมเดล canonical: [rbac permissions](/th/backstage/rbac/permissions)

## 2. References

- ../carmen-backstage/src/App.tsx — route ทั้งสามของ cluster พร้อม prop `requiredPermission` + `feature`
- ../carmen-backstage/src/components/PrivateRoute.tsx — guard แบบเป็นชั้น: auth → resolve platform-authority/cluster-admin (ใหม่) → permission → super-admin → feature flag
- ../carmen-backstage/src/components/Can.tsx, ../carmen-backstage/src/context/AuthContext.tsx, ../carmen-backstage/src/utils/permissions.ts (รวม `checkBackstageAuthority`)
- ../carmen-backstage/src/context/FeatureFlagContext.tsx — `flagOf`/`isReady` ที่ `PrivateRoute` ใช้เช็ค feature flag
- ../carmen-backstage/src/components/nav/backstageNav.ts — รายการ nav ของ Clusters (permission, feature, group)
- ../carmen-backstage/src/pages/Forbidden.tsx, ../carmen-backstage/src/pages/NotFound.tsx, ../carmen-backstage/src/pages/ComingSoon.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/backstage/clusters/permissions (เมทริกซ์ effective access รวม `activity_log.read`, รายละเอียด layer resolve platform-authority ใหม่, พฤติกรรม Forbidden/NotFound/ComingSoon, filter ของ sidebar)
