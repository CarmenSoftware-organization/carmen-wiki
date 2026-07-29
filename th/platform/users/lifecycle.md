---
title: User — Lifecycle
description: Create, gate ตอน sign-in ด้วย effective permissions, disable, hard/soft delete และ password reset
published: true
date: 2026-07-29T07:06:05.000Z
tags: book/platform, users, lifecycle
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Lifecycle

## 1. At a Glance

- Flow การ create (7 ฟิลด์ — การสร้างบัญชีไม่มอบสิทธิ์ Platform admin ใด ๆ ในตัวเอง; ต้อง assign role บน `/platform/user-platform` ก่อน) — การ์ดสร้างชื่อ "Account details" (ไม่ใช่ "User Details")
- Gate ตอน sign-in: `login()` ตรวจ effective permissions (`GET /api/user/permission/platform`) — รับ session เฉพาะเมื่อถือ permission อย่างน้อยหนึ่งตัว, มี flag super-admin หรือเข้าข้อยกเว้น bootstrap (user รวม 0–1 คน)
- Save ใช้ `doc_version` optimistic lock — `PUT /api-system/user/:id` ส่งค่ากลับไปด้วย conflict (`409`) แสดง toast + โหลดใหม่
- Disable vs delete (soft vs hard) — ทั้ง Delete และ Hard Delete ห่อด้วย `<Can permission="user.delete">`; **ใหม่:** bulk soft/hard delete สำหรับ super-admin เท่านั้น (`isSuperAdmin`) — bulk hard delete ใช้รหัสยืนยัน 6 ตัวอักษรแบบสุ่ม ต่างจาก flow เดี่ยวที่พิมพ์ username ตรง ๆ; dialog hard-delete เดี่ยวมีปุ่ม copy-username สำหรับ super-admin
- Password reset (admin เป็นผู้ทำ — ปุ่ม Change Password ย้ายไปอยู่ actions slot ของการ์ด `UserIdentityHero` แล้ว ไม่มี gate `<Can>` ของตัวเอง)
- Keycloak sync (`/api-system/fetch-user`) — **แก้ไขจาก sync ก่อนหน้า:** ตอนนี้ gate ด้วย `<Can permission="user.create">` แล้ว (เดิมไม่มี gate ภายในหน้าเลย)
- Add/Remove BU assignment ใน `UserAccessTree` — **แก้ไข:** ปุ่ม Add BU ตอนนี้ gate ด้วย `canAddBU` (permission check จริงต่อ cluster ไม่ใช่แค่ "มี cluster") และปุ่ม Remove ต่อแถว gate ด้วย `cluster.update` scope กับ cluster ของ BU เอง

## 2. References

- ../carmen-platform/src/pages/UserEdit.tsx, userEdit/{UserIdentityHero,UserAccessTree}.tsx
- ../carmen-platform/src/pages/UserManagement.tsx, userManagement/UserDirectorySummary.tsx
- ../carmen-platform/src/utils/docVersion.ts
- ../carmen-platform/src/context/AuthContext.tsx — gate effective-permissions ใน `login()` และข้อยกเว้น bootstrap

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/users/lifecycle
- [ ] Document flow email ของ password reset ถ้ามี
