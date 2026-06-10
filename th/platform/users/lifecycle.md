---
title: User — Lifecycle
description: Create, gate ตอน sign-in ด้วย effective permissions, disable, hard/soft delete และ password reset
published: true
date: 2026-06-10T16:30:00.000Z
tags: book/platform, users, lifecycle
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Lifecycle

## 1. At a Glance

- Flow การ create (7 ฟิลด์ — การสร้างบัญชีไม่มอบสิทธิ์ Platform admin ใด ๆ ในตัวเอง; ต้อง assign role บน `/platform/user-platform` ก่อน)
- Gate ตอน sign-in: `login()` ตรวจ effective permissions (`GET /api/user/permission/platform`) — รับ session เฉพาะเมื่อถือ permission อย่างน้อยหนึ่งตัว, มี flag super-admin หรือเข้าข้อยกเว้น bootstrap (user รวม 0–1 คน) (หมายเหตุเชิงประวัติ: จนถึง 2026-06-10 gate นี้เคยเป็น allow-list ของ `platform_role` — `ALLOWED_ROLES` — ถอดออกใน commit `5f629f2` ของ `carmen-platform`)
- Disable vs delete (soft vs hard) — ทั้ง Delete และ Hard Delete ห่อด้วย `<Can permission="user.delete">`
- Password reset (admin เป็นผู้ทำ — ปุ่ม Change Password ไม่มี gate `<Can>` ของตัวเอง)
- Keycloak sync (`/api-system/fetch-user`) — ไม่มี gate ภายในหน้า; backend เป็นขอบเขตจริง

## 2. References

- ../carmen-platform/src/pages/UserEdit.tsx
- ../carmen-platform/src/pages/UserManagement.tsx
- ../carmen-platform/src/context/AuthContext.tsx — gate effective-permissions ใน `login()` และข้อยกเว้น bootstrap

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/users/lifecycle
- [ ] Document flow email ของ password reset ถ้ามี
