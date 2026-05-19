---
title: การยืนยันตัวตนและสิทธิ์ (Authentication & Roles)
description: flow การล็อกอิน โมเดล session แคตตาล็อก role ตัวป้องกัน route และการกรองแถบเมนูข้างตาม role ของผลิตภัณฑ์ Carmen Platform admin
published: true
date: 2026-05-19T12:00:00.000Z
tags: platform/auth-roles, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# การยืนยันตัวตนและสิทธิ์ (Authentication & Roles)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** flow การล็อกอิน โมเดล session แคตตาล็อก role และตัวป้องกัน route + แถบเมนูข้างที่ควบคุมการเข้าถึงทุกหน้าจอของ Platform admin &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ของ Platform admin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `user`, `platform_role`, สถานะ session ใน `AuthContext`, ตัวป้องกัน `PrivateRoute`, `NavItem.roles` ของแถบเมนูข้าง &nbsp;·&nbsp; **หน้าย่อย:** 0

## 1. ภาพรวม

Authentication & Roles คือเอกสารควบคุมการเข้าถึงแบบ cross-cutting ของผลิตภัณฑ์ Carmen Platform admin ครอบคลุมเส้นทางทั้งหมดที่ผู้ใช้ที่ล็อกอินอยู่ต้องผ่าน หน้า `/login` รับ email หรือชื่อผู้ใช้ (email-or-username) และรหัสผ่าน `AuthContext` เก็บ JWT และ `platform_role` ของผู้ใช้ที่ได้กลับมา `PrivateRoute` ควบคุมทุก route ที่ต้องล็อกอิน และแถบเมนูข้างใน `Layout` ซ่อนรายการที่ Role ปัจจุบันเข้าไม่ได้ ไม่มีโมดูลอื่นใน Platform เป็นเจ้าของชิ้นส่วนเหล่านี้ — โมดูลฟีเจอร์อื่นเพียงแค่นำไปใช้

หน้าล็อกอินเอง (`src/pages/Login.tsx`) เป็น form email-or-username และรหัสผ่านอย่างเดียว ไม่มี SSO, MFA หรือ flow การรีเซ็ตรหัสผ่าน เมื่อ submit จะเรียก `POST /api/auth/login` คาดหวัง `access_token` และ `platform_role` ใน response แล้วเก็บทั้งสองค่าใน `localStorage` (`token`, `user`, `loginResponse`) token จะถูกแนบเป็น `Authorization: Bearer ...` ในทุกการเรียก API หลังจากนั้น ผ่าน axios instance ส่วนกลาง หาก `platform_role` ไม่อยู่ใน allow-list การล็อกอินจะถูกปฏิเสธพร้อมข้อความ "Access Denied" ก่อนที่ session จะถูกสร้าง

หลังจากล็อกอิน `PrivateRoute` จะห่อทุก route ที่ต้องการการป้องกัน หากไม่ส่ง prop `allowedRoles` จะอนุญาตให้ผู้ใช้ที่ล็อกอินแล้วทุกคนผ่าน หากส่ง prop จะตรวจสอบ `hasRole(allowedRoles)` และแสดง `<AccessDenied>` ภายใน `<Layout>` ปกติเมื่อการตรวจล้มเหลว function `hasRole()` ตัวเดียวกันนี้ยังขับเคลื่อนแถบเมนูข้าง — `Layout` กรอง `NavItem[]` ตาม Role ปัจจุบัน เพื่อให้ผู้ใช้เห็นเฉพาะรายการที่เข้าถึงได้จริง มีข้อยกเว้นเริ่มต้นใช้งานหนึ่งกรณี: เมื่อ `userCount` resolve แล้วและได้ค่าเป็น `0` หรือ `1` (สถานะ bootstrap ของผู้ดูแลคนแรก) `hasRole()` จะคืน `true` สำหรับ Role array ใด ๆ เพื่อให้ผู้ดูแลคนแรกตั้งค่าระบบได้ แต่เมื่อ `userCount` ยังเป็น `null` (API call ยังไม่ resolve หรือล้มเหลว) ข้อยกเว้น bootstrap จะ**ไม่**ทำงาน และการตรวจสอบ Role ปกติจะมีผลแทน

## 2. บริบททางธุรกิจ

Carmen Platform admin ถูกใช้งานโดยกลุ่มธุรกิจโรงแรมที่มักดำเนินงานหลาย property ภายใต้องค์กรแม่หนึ่งราย ระดับสิทธิ์เดียวจึงไม่เพียงพอ — ผู้ดูแลระดับ cluster เจ้าหน้าที่ระดับ business unit และวิศวกร support ภายในของ Carmen ทั้งหมดต้องการหน้าจอที่ต่างกัน ค่า `platform_role` บนบัญชีผู้ใช้แต่ละบัญชีเข้ารหัสว่าผู้ใช้รายนั้นเข้าถึงหน้าจอใดได้บ้าง และทุกอย่างอื่นในโมดูลนี้มีไว้เพื่อบังคับใช้การผูกค่านั้นอย่างสม่ำเสมอตั้งแต่การล็อกอิน ตัว route และแถบเมนูข้าง

## 3. แนวคิดสำคัญ

- **Authentication**: การล็อกอินด้วย email-or-username + รหัสผ่านผ่าน `POST /api/auth/login` คืน `access_token` และ `platform_role` ปัจจุบันยังไม่มี SSO, MFA, OAuth หรือ flow รีเซ็ตรหัสผ่านในผลิตภัณฑ์ Platform admin
- **Session**: object `token`, `user`, และ `loginResponse` ที่เก็บใน `localStorage` และมีสำเนาในสถานะ React ของ `AuthContext` session อยู่รอดเมื่อ reload หน้าได้เพราะ `AuthContext` rehydrate จาก `localStorage` ตอน mount
- **AuthContext**: React context (`src/context/AuthContext.tsx`) ที่เปิดเผย `user`, `login`, `logout`, `isAuthenticated`, `platformRole`, `hasRole`, และ `userCount` ให้กับส่วนอื่นของแอปผ่าน hook `useAuth()`
- **platform_role**: ฟิลด์ string เพียงฟิลด์เดียวบน user ที่ขับเคลื่อนทุกการตัดสินใจด้านสิทธิ์ เก็บใน `loginResponse.platform_role` และเปิดเผยผ่าน `AuthContext.platformRole`
- **ALLOWED_ROLES**: allow-list ที่ hard-code ไว้ภายใน `AuthContext` ที่ login ใช้ตรวจก่อนสร้าง session ปัจจุบันคือ `platform_admin`, `super_admin`, `support_manager`, `support_staff`, `security_officer` ค่า Role อื่นใดจะถูกปฏิเสธตอนล็อกอิน
- **PrivateRoute**: คอมโพเนนต์ตัวป้องกัน route (`src/components/PrivateRoute.tsx`) เปลี่ยนเส้นทางผู้ใช้ที่ยังไม่ล็อกอินไปที่ `/login` หากส่ง prop `allowedRoles` จะรัน `hasRole(allowedRoles)` และแสดง `<AccessDenied>` เมื่อล้มเหลว
- **allowedRoles**: prop ที่ใส่หรือไม่ก็ได้บน `PrivateRoute` ที่ระบุรายการ Role ที่ดู route นั้นได้ Route ที่ไม่มี prop นี้รับผู้ใช้ที่ล็อกอินแล้วทุกคน Route ที่มีจะปฏิเสธ Role ที่ไม่ตรงกัน
- **AccessDenied**: คอมโพเนนต์เต็มหน้าที่แสดงภายใน `<Layout>` เมื่อการตรวจ Role ล้มเหลวบน route แสดง Role ปัจจุบันของผู้ใช้และปุ่ม "Back to Dashboard" นิยามไว้ในไฟล์เดียวกันกับ `PrivateRoute`
- **hasRole(roles)**: method บน `AuthContext` ที่คืน `true` เมื่อ `platformRole` ปัจจุบันอยู่ใน array ที่ส่งเข้ามา นอกจากนี้ยังคืน `true` เมื่อ `userCount !== null` และ `userCount <= 1` (ข้อยกเว้น bootstrap สำหรับการตั้งค่าผู้ดูแลคนแรก) เมื่อ `userCount` เป็น `null` (API call ยังไม่ resolve หรือล้มเหลว) ข้อยกเว้น bootstrap จะ**ไม่**ทำงาน และการตรวจสอบ Role ปกติจะมีผลแทน
- **ตัวกรองแถบเมนูข้างตาม Role**: ใน `Layout.tsx` array `allNavItems` มีฟิลด์ `roles` ที่ใส่หรือไม่ก็ได้บนแต่ละรายการ `Layout` กรองผ่าน `hasRole()` เพื่อให้ผู้ใช้ไม่เห็นรายการเมนูที่เปิดไม่ได้

## 4. บทบาทและ Persona

ค่า Role ห้าค่าใน `ALLOWED_ROLES` (`src/context/AuthContext.tsx`) เป็น Role เพียงค่าเดียวที่ล็อกอินเข้าผลิตภัณฑ์ Platform admin ได้

| Role | เข้าถึงได้ |
|---|---|
| `platform_admin` | ผู้ดูแลแพลตฟอร์มเต็มรูปแบบ เข้าถึงได้ทุก route รวมถึง `Clusters`, `Report Templates`, และ `Print Template Mapping` |
| `super_admin` | ผู้ดูแลระดับสูงสุด ผ่านการตรวจ `ALLOWED_ROLES` ตอนล็อกอิน แต่ปัจจุบันไม่ได้ระบุไว้ใน array `allowedRoles` ของ route ใด ๆ — เข้าถึงได้เฉพาะ route ที่ต้องล็อกอินเท่านั้น ไม่ใช่หน้า cluster/report-template |
| `support_manager` | ผู้จัดการ support ของ Carmen สิทธิ์เข้าถึง route เหมือนกับ `platform_admin` — ถูกระบุในทุก array `allowedRoles` ที่ควบคุมหน้า admin |
| `support_staff` | วิศวกร support ของ Carmen สิทธิ์เข้าถึง route เหมือนกับ `support_manager` |
| `security_officer` | Role ด้านความปลอดภัย/audit ผ่านการตรวจ `ALLOWED_ROLES` ตอนล็อกอิน แต่ปัจจุบันไม่ได้ระบุไว้ใน array `allowedRoles` ของ route ใด ๆ — เข้าถึงได้เฉพาะ route ที่ต้องล็อกอินเท่านั้น |

Role ทั้งห้าเข้าถึง `Dashboard`, `Business Units`, `Users`, และ `Profile` ได้ เพราะ route เหล่านั้นใช้ `PrivateRoute` โดยไม่มี prop `allowedRoles`

## 5. โมดูลที่เกี่ยวข้อง

- [[users]] — จัดการฟิลด์ `platform_role` ที่โมดูลนี้อ่าน การสร้างหรือแก้ไขผู้ใช้คือจุดที่ Role ถูกกำหนดจริง
- [[clusters]] — หน้าจอที่ถูก gate ด้วย Role ที่ส่งผลกระทบสูงสุด array `allowedRoles` ของมันคือตัวอย่างมาตรฐานของวิธีที่ฟีเจอร์ใช้ `hasRole()`
- [[report-templates]] — ตัวอย่างที่สองของหน้าจอที่ถูก gate ด้วย Role โดยใช้ list Role ระดับ admin เดียวกัน
- [[profile]] — หน้าที่ต้องล็อกอินเพียงหน้าเดียวที่เข้าถึงได้จากเมนู avatar แทนที่จะเป็นแถบเมนูข้าง พึ่งพาโมเดล session ของโมดูลนี้
- [[business-units]] — เข้าถึงได้โดยทุก Role ที่ล็อกอินแล้ว เป็นตัวอย่างตรงข้ามที่มีประโยชน์ ให้เห็นว่า "ไม่มี `allowedRoles`" หน้าตาเป็นอย่างไรในทางปฏิบัติ

## 6. แหล่งข้อมูลอ้างอิง

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/Login.tsx`, `../carmen-platform/src/context/AuthContext.tsx`, `../carmen-platform/src/components/PrivateRoute.tsx`, `../carmen-platform/src/components/Layout.tsx`

## 7. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดี่ยว ดู [สารบัญหนังสือ Platform](../index.md)
