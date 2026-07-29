---
title: User — UI Screens
description: UserManagement (list พร้อมคอลัมน์ avatar) และ UserEdit (เมทริกซ์ BU assignment, avatar บน header)
published: true
date: 2026-07-29T07:06:05.000Z
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

## 1. At a Glance

- หน้า list: แถบสรุป **Directory** ใหม่ (`UserDirectorySummary` — จำนวนรวม/active/inactive/archived + "Recently added" avatar ซ้อนกัน), คอลัมน์ avatar นำหน้า (fallback เป็นอักษรย่อ วางรูป presigned ทับเมื่อมี), คอลัมน์ Name ประกอบด้วย helper `getNameDisplay`, คอลัมน์ **BU** ใหม่ (จำนวน active/total การ assign BU), filter เหลือเฉพาะ status + show-deleted, คอลัมน์ audit Created/Updated, **bulk soft/hard-delete สำหรับ super-admin เท่านั้น** ผ่าน checkbox ของแถว (`enableRowSelection={isSuperAdmin}`)
- Gate: route guard `user.read`/`user.create`/`user.update`; Add User, Fetch Keycloak (ตอนนี้ gate ด้วย `user.create` — แก้ไขจาก sync ก่อนหน้า), Edit/Delete ของ row และ toggle Edit ห่อด้วย `<Can>` (ไม่มี gate ใดส่ง `clusterId` ที่ระดับนี้)
- หน้า edit **เขียนใหม่**: การ์ด `UserIdentityHero` (avatar, ชื่อ, chip username/email/alias, badge สถานะ, สรุป access) แทน header เดิม + การ์ด User Details + การ์ด `UserAccessTree` เดียวที่รวม Clusters/Business Units การ์ดแยกเดิมเข้าด้วยกันเป็นลำดับชั้น cluster → BU; ปุ่ม Add BU gate ด้วย `canAddBU` (permission จริง) ปุ่ม Remove ต่อแถว gate ด้วย `cluster.update` scope กับ cluster ของ BU เอง — ทั้งสองไม่เคยมี gate มาก่อน; save ใช้ `doc_version` optimistic lock; มี not-found state ใหม่
- Endpoint: `/api-system/user` (ยังเป็นเอกพจน์) แต่ endpoint join ของ BU เป็นพหูพจน์ (`/api-system/user/business-units`, `/api-system/user/clusters/:clusterId`)

## 2. References

- ../carmen-platform/src/pages/UserManagement.tsx, userManagement/UserDirectorySummary.tsx
- ../carmen-platform/src/pages/UserEdit.tsx, userEdit/{UserIdentityHero,UserAccessTree}.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/users/ui-screens (เลย์เอาต์เปลี่ยนเป็น hero + Access tree แล้ว)
- [ ] Screenshot workflow ของ BU assignment (เลย์เอาต์ใหม่ทั้งหมด)
