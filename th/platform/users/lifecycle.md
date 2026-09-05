---
title: User — Lifecycle
description: Create, gate ตอน sign-in ด้วย effective permissions, disable, hard/soft delete และ password reset
published: true
date: 2026-09-05T13:20:00.000Z
tags: book/platform, users, lifecycle
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Lifecycle

## 1. At a Glance

- Flow การ create — **`firstname`/`lastname` บังคับกรอกแล้ว** เหมือน `username`/`email` (เดิม optional; commit `d21c57c`, #220) ฟอร์ม 7 ฟิลด์จัดเป็น 3 ส่วนมีหัวข้อ (Sign-in details / Display name / Status) การสร้างบัญชีไม่มอบสิทธิ์ Platform admin ใด ๆ ในตัวเอง; ต้อง assign role บน `/platform/user-platform` ก่อน — การ์ดสร้างชื่อ "Account details" (ไม่ใช่ "User Details")
- Gate ตอน sign-in: `login()` ตรวจ effective permissions (`GET /api/user/permission/platform`) — รับ session เฉพาะเมื่อถือ permission อย่างน้อยหนึ่งตัว, มี flag super-admin หรือเข้าข้อยกเว้น bootstrap (user รวม 0–1 คน)
- Save ใช้ `doc_version` optimistic lock — `PUT /api-system/user/:id` ส่งค่ากลับไปด้วย conflict (`409`) แสดง toast + โหลดใหม่; ปุ่ม Save/Cancel ยังผูกกับ shortcut `Ctrl`/`⌘`+`S` และ `Escape` ด้วย
- Disable vs delete (soft vs hard) — ทั้ง Delete และ Hard Delete ห่อด้วย `<Can permission="user.delete">`; bulk soft/hard delete สำหรับ super-admin เท่านั้น (`isSuperAdmin`) — bulk hard delete ใช้รหัสยืนยัน 6 ตัวอักษรแบบสุ่ม ต่างจาก flow เดี่ยวที่พิมพ์ username ตรง ๆ; dialog hard-delete เดี่ยวมีปุ่ม copy-username สำหรับ super-admin
- Password reset (admin เป็นผู้ทำ — ปุ่ม Change Password อยู่ใน actions slot ของการ์ด `UserIdentityHero`; **ตอนนี้ gate ด้วย `<Can permission="user.update">` แล้ว** เหมือนปุ่ม Edit ข้าง ๆ กัน — เดิมไม่มี gate)
- Keycloak sync (`/api-system/fetch-user`) — gate ด้วย `<Can permission="user.create">`
- Add/Remove BU assignment ใน `UserAccessTree` — ปุ่ม Add BU gate ด้วย `canAddBU` (permission check จริงต่อ cluster ไม่ใช่แค่ "มี cluster") และปุ่ม Remove ต่อแถว gate ด้วย `cluster.update` scope กับ cluster ของ BU เอง แต่ละแถว BU ตอนนี้มีบรรทัด audit แบบย่อ (`latestActor()`) ด้วย
- View History ใหม่ (`activity_log.read` scope ระดับแพลตฟอร์ม) — ปุ่มดูประวัติทั้งบน row menu ของ list และ actions slot ของ Hero

## 2. References

- ../carmen-platform/src/pages/UserEdit.tsx, userEdit/{UserIdentityHero,UserAccessTree}.tsx
- ../carmen-platform/src/pages/UserManagement.tsx, userManagement/UserDirectorySummary.tsx
- ../carmen-platform/src/utils/audit.ts — `normalizeAudit()`, `latestActor()`
- ../carmen-platform/src/utils/docVersion.ts
- ../carmen-platform/src/context/AuthContext.tsx — gate effective-permissions ใน `login()` และข้อยกเว้น bootstrap

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/users/lifecycle
- [ ] Document flow email ของ password reset ถ้ามี
