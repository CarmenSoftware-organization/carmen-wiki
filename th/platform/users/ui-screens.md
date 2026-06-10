---
title: User — UI Screens
description: UserManagement (list พร้อมคอลัมน์ avatar) และ UserEdit (เมทริกซ์ BU assignment, avatar บน header)
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

## 1. At a Glance

- หน้า list: คอลัมน์ avatar นำหน้า (fallback เป็นอักษรย่อ วางรูป presigned ทับเมื่อมี), คอลัมน์ Name ประกอบด้วย helper `getNameDisplay`, filter เหลือเฉพาะ status + show-deleted (filter ตาม Role หายไปพร้อม role enum), คอลัมน์ audit Created/Updated
- Gate: route guard `user.read`/`user.create`/`user.update`; Add User, Edit/Delete ของ row และ toggle Edit ห่อด้วย `<Can>` (ไม่มี gate ใดส่ง `clusterId`)
- หน้า edit: avatar บน header, การ์ด User Details / Clusters (read-only) / Business Units พร้อม dialog Add BU และ dialog Change Password
- Endpoint: `/api-system/user` (ยังเป็นเอกพจน์) แต่ endpoint join ของ BU เป็นพหูพจน์ (`/api-system/user/business-units`, `/api-system/user/clusters/:clusterId`)

## 2. References

- ../carmen-platform/src/pages/UserManagement.tsx
- ../carmen-platform/src/pages/UserEdit.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/users/ui-screens
- [ ] Screenshot workflow ของ BU assignment
