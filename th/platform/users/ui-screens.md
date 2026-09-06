---
title: User — UI Screens
description: UserManagement (list พร้อมคอลัมน์ avatar) และ UserEdit (เมทริกซ์ BU assignment, avatar บน header)
published: true
date: 2026-09-05T13:25:00.000Z
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

## 1. At a Glance

- หน้า list: คอลัมน์ avatar/username/name/email เดิมยุบเหลือเซลล์ identity เดียว **User** (บรรทัดชื่อ + บรรทัด username/email ตัดค่าซ้ำ — commit `fd1f6ae`, #219) คอลัมน์ **Status** ไม่สมมาตรแล้ว (`Active` เป็นข้อความจาง ไม่มี badge, `Inactive` เท่านั้นที่ได้ badge) แถบสรุป **Directory** (`UserDirectorySummary`) อ่านจาก endpoint เฉพาะทาง `GET /api-system/user/summary` แล้ว ไม่ใช่การรวมข้อมูลฝั่ง client คอลัมน์ **BU** (จำนวน active/total การ assign BU จาก array ของแถวเอง), filter เหลือเฉพาะ status + show-deleted, คอลัมน์ audit Created/Updated ตอนนี้ render เป็นเวลาสัมพัทธ์พร้อม tooltip เวลาเต็ม (ไม่ใช่สตริงตายตัวแบบเดิม), CSV export เพิ่มเป็น 7 คอลัมน์, เมนู action ของแถวมี 4 รายการ (เพิ่ม **View History** ใหม่), **bulk soft/hard-delete สำหรับ super-admin เท่านั้น** ผ่าน checkbox ของแถวเหมือนเดิม
- Gate: route guard `user.read`/`user.create`/`user.update` + `feature="users"`; Add User, Fetch Keycloak (`user.create`), View History ใหม่ (`activity_log.read` scope ระดับแพลตฟอร์ม), Edit/Delete ของ row และ toggle Edit ห่อด้วย `<Can>` — **Change Password ตอนนี้ก็ gate ด้วย `user.update` แล้ว** เหมือน Edit (เดิมไม่มี gate)
- หน้า edit: การ์ด `UserIdentityHero` (avatar, ชื่อ, chip username/email/alias, badge สถานะ, สรุป access, ตอนนี้มีบรรทัด audit เพิ่มด้วย) แทน header เดิม **ไม่มีการ์ด "User Details" แบบแยกที่แสดงตลอดเวลาอีกต่อไป** — การ์ดฟอร์มทั้งใบถูกครอบด้วยเงื่อนไข `editing` เท่านั้น (แสดงเฉพาะตอนคลิก Edit) โหมด view จึงเห็น identity ผ่าน Hero ล้วน ๆ + การ์ด `UserAccessTree` เดียวที่รวม Clusters/Business Units เข้าด้วยกันเป็นลำดับชั้น cluster → BU (แต่ละแถว BU มีบรรทัด audit แบบย่อเพิ่มด้วย); ปุ่ม Add BU gate ด้วย `canAddBU` (permission จริง) ปุ่ม Remove ต่อแถว gate ด้วย `cluster.update` scope กับ cluster ของ BU เอง; save ใช้ `doc_version` optimistic lock; มี not-found state
- Endpoint: `/api-system/user` (ยังเป็นเอกพจน์) แต่ endpoint join ของ BU เป็นพหูพจน์ (`/api-system/user/business-units`, `/api-system/user/clusters/:clusterId`); แถบสรุปอ่านจาก `/api-system/user/summary`

## 2. References

- ../carmen-platform/src/pages/UserManagement.tsx, userManagement/UserDirectorySummary.tsx
- ../carmen-platform/src/pages/UserEdit.tsx, userEdit/{UserIdentityHero,UserAccessTree}.tsx
- ../carmen-platform/src/utils/audit.ts, src/components/{auditColumns.tsx,AuditMeta.tsx}
- ../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail}.tsx

## 3. TODO

- [ ] เขียนเนื้อหาฉบับเต็มตาม en/platform/users/ui-screens (เลย์เอาต์เปลี่ยนเป็น hero + Access tree แล้ว, ไม่มีการ์ด User Details แยกในโหมด view)
- [ ] Screenshot workflow ของ BU assignment (เลย์เอาต์ใหม่ทั้งหมด)
