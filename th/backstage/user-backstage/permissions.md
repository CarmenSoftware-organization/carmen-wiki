---
title: ผู้ใช้แพลตฟอร์ม — สิทธิ์ (Permissions)
description: user_backstage.read กั้นทั้งสอง route; user_backstage.manage กั้นทุกจุดที่เขียนได้ — แต่หน้า detail ส่วนใหญ่ยังต้องมี user.read ของโมดูล Users ด้วย
published: true
date: 2026-10-29T05:00:00.000Z
tags: book/backstage, user-backstage, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ใช้แพลตฟอร์ม — สิทธิ์ (Permissions)

> **At a Glance**
> **มีสองคีย์เท่านั้น:** `user_backstage.read` (ด่าน nav/route ของทั้งสอง route) และ `user_backstage.manage` (ทุกจุดที่เขียนได้บนทั้งสองหน้าจอ) — grep ทั้ง repo หา `user_backstage\.` ไม่พบ literal ตัวที่สาม &nbsp;·&nbsp; **frontend กับ backend ตรงกันเป๊ะ**ในทั้งสี่ action ที่เขียนได้ — resource เดียวกัน action เดียวกัน ไม่มีความไม่ตรงกันข้ามคีย์แบบที่พบใน [Backstage Config](/th/backstage/backstage-config) §4.3 หรือ [Email Settings](/th/backstage/email-settings) §4.2 &nbsp;·&nbsp; **ช่องว่างจริงอยู่ที่การอ่าน ไม่ใช่การเขียน:** identity บัญชีและรายการ role บนหน้า detail ต้องมี `user.read` ด้วย ซึ่งเป็นคีย์ของโมดูล [Users](/th/backstage/users) ที่ `user_backstage.read` เพียงอย่างเดียวไม่ได้ให้มา และ route guard ก็ไม่เคยตรวจ &nbsp;·&nbsp; **ไม่เงียบ** — ความล้มเหลวแสดงเป็นแถบ error ชัดเจน แต่หน้าที่เหลือใต้แถบนั้นยังอ่านเหมือน "ผู้ถือสิทธิ์คนนี้ไม่มี role เลย" ซึ่งไม่จริงเสมอไป &nbsp;·&nbsp; **ไม่มี e2e ครอบคลุมการไล่รอยนี้** — สอง spec ของ suite `user-platform` ไม่เคยทดสอบ session ที่ลดสิทธิ์เลย (ดู [UI Screens](/th/backstage/user-backstage/ui-screens) §4)

## 1. ภาพรวม

พื้นผิว permission ของโมดูลนี้เล็กและฝั่งเขียนสะอาด: สองคีย์ ตรวจเหมือนกันทั้งฝั่ง frontend และ backend ไม่มีคีย์ไหนถูกเปลี่ยนชื่อหรือยกเลิกตั้งแต่แยกออกมาจาก RBAC พฤติกรรมที่น่าสนใจไม่ใช่ความไม่ตรงกันภายในโมดูลนี้เอง — แต่คือการที่หน้าจอของโมดูลนี้ต้องพึ่งคีย์ของโมดูลอื่นซึ่ง route guard ไม่เคยถูกเขียนให้ต้องมี

## 2. เมทริกซ์ของ gate

| จุด | Guard | คีย์ | ที่มา |
| --- | --- | --- | --- |
| route `/backstage/user-backstage` | `PrivateRoute` | `user_backstage.read`, `feature: 'user_backstage'` | `App.tsx:497-504` |
| route `/backstage/user-backstage/:userId` | `PrivateRoute` | `user_backstage.read`, `feature: 'user_backstage'` | `App.tsx:505-512` |
| รายการ sidebar | nav filter | `permission: 'user_backstage.read'`, `feature: 'user_backstage'`, `groupKey: 'navGroup.backstage'` — ไม่ใช่ `superAdminOnly` | `backstageNav.ts:48` |
| ปุ่ม Grant Access (header รายการ, empty state) | `<Can>` | `user_backstage.manage` | `UserBackstageManagement.tsx:417,586` |
| Revoke all access (row menu รายการ) | `<Can>` | `user_backstage.manage` | `UserBackstageManagement.tsx:390` |
| sheet Add Role (หน้า detail) | `<Can>` | `user_backstage.manage` | `UserBackstageEdit.tsx:302` |
| Remove role (หน้า detail, ต่อแถว) | `<Can>` | `user_backstage.manage` | `RoleGrantList.tsx:126` |
| Manage roles (row menu รายการ → นำทางไป detail) | ไม่มี permission key ของตัวเอง — กั้นด้วยด่าน `user_backstage.read` ของ route detail เองแทน | — | `UserBackstageManagement.tsx:383-389` |

ฝั่ง backend ทั้งหมดอยู่ใน `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/user-backstage-roles/user-backstage-roles.controller.ts` HEAD `937cf5ac4`:

| Route | Guard | ที่มา |
| --- | --- | --- |
| `GET /api-system/backstage/users` | `AppIdGuard` + `BackstagePermissionGuard`, `user_backstage.read` | บรรทัด 88-90 |
| `GET /api-system/backstage/users/:user_id/roles` | เหมือนกัน, **`user.read`** | บรรทัด 135-137 |
| `POST /api-system/backstage/users/:user_id/roles` | เหมือนกัน, `user_backstage.manage` | บรรทัด 180-182 |
| `POST /api-system/backstage/users/:user_id/roles/bulk` | เหมือนกัน, `user_backstage.manage` | บรรทัด 233-235 |
| `DELETE /api-system/backstage/users/:user_id/roles/:assignment_id` | เหมือนกัน, `user_backstage.manage` | บรรทัด 280-282 |

สองคำขอที่หน้า detail เรียก**ไม่**อยู่ในตารางข้างบนเพราะไปเจอ controller คนละตัวเลย: `GET /api-system/user/:user_id` (record ของบัญชีเอง, `userService.getById`) กั้นด้วย `user.read` บน `backstage-user.controller.ts:264-266` และ `GET /api-system/user?...` (การค้นหาที่หนุนหลัง `UserPicker` ของ `GrantAccessDialog` บนหน้ารายการ) กั้นด้วย `user.read` บน controller เดียวกัน บรรทัด 128-130 ทั้งคู่เป็น endpoint ของโมดูล [Users](/th/backstage/users) — โมดูลนี้แค่เรียกใช้ซ้ำ ไม่ได้สร้างวิธีค้นหาคนซ้ำสองแบบ

## 3. ช่องว่าง `user.read` ไล่รอยแบบ end-to-end

**ข้อกล่าวอ้าง พูดให้แม่นยำ:** session ที่ถือ `user_backstage.read` และ `user_backstage.manage` แต่ไม่มี `user.read` สามารถเข้าถึงทั้งสองหน้าจอได้ และในทางเทคนิคยังเรียก action เขียนได้ทุกตัวที่โมดูลนี้มี — แต่ไม่สามารถเห็นได้เลยว่าผู้ถือสิทธิ์คนหนึ่งมี role ที่กำลังจะมอบอยู่แล้วหรือยัง ทั้งสองหน้าจอ และบนหน้า detail โดยเฉพาะจะเห็นหน้าที่ดูเหมือนพังในขณะที่ยังทำได้อยู่ นี่เป็นช่องว่างที่จริงและทำซ้ำได้ ไม่ใช่สมมติฐานลอย ๆ: `user_backstage.read` กับ `user.read` เป็นคนละ resource ตรวจโดยคนละ controller และไม่มีอะไรผูกทั้งสองเข้าด้วยกันเลย

**บนหน้ารายการ** session นี้เห็นตารางทะเบียนโหลดและ filter ได้ปกติ — `GET /api-system/backstage/users` ต้องการแค่ `user_backstage.read` ซึ่งมีอยู่ การเพิกถอนสิทธิ์ของผู้ถือสิทธิ์ที่มีอยู่แล้วก็ทำงานได้เต็มที่ ไม่มีจุดไหนในเส้นทางนั้นแตะ `user.read` เลย จุดที่พังคือการมอบสิทธิ์ให้คนใหม่: `UserPicker` ของ `GrantAccessDialog` ค้นหาผ่าน `GET /api-system/user` ซึ่ง 403 ตามการออกแบบของ component เอง (`useUserSearch.ts`, `UserPicker.tsx`) ความล้มเหลวนั้นแสดง**ในกล่อง dropdown เอง** ไม่เคยเป็น toast — dialog จึงไม่พัง แต่เลือกผู้ใช้ไม่ได้เลยสักคน และ `handleSubmit` ก็ปฏิเสธการ submit ถ้าไม่มีผู้ใช้ (`if (!user) { toast.error(...); return; }`) Grant Access ยังเข้าถึงและกดได้ แต่ทำให้เสร็จไม่ได้

**บนหน้า detail** ลำดับใน `load()` ของ `UserBackstageEdit.tsx` (บรรทัด 134-160) คือ: `userService.getById(userId)` ก่อน แล้วต่อเมื่อสำเร็จเท่านั้นถึงจะไปที่ `loadAssignments()` (เรียก `GET .../roles` ซึ่งใช้ `user.read` เหมือนกัน) และ `loadProvenance()` (เรียก endpoint ทะเบียน `user_backstage.read` — ตัวนี้สำเร็จ) เพราะ `userService.getById` ถูก await ก่อนและทั้งสอง endpoint ที่มันกั้นใช้ permission**เดียวกัน** session นี้จะ throw ที่บรรทัดแรกใน `load()` เลยและไม่ไปถึงตัวอื่นเลย — ไม่มีสถานะแยกที่บัญชีโหลดได้แต่ role โหลดไม่ได้ หรือกลับกัน ทั้งสองล้มเหลวพร้อมกันแน่นอนทุกครั้ง catch block ตั้งค่าแถบ error ให้เห็นชัดเจน (`t('pages.userBackstage.loadUserFailed', { detail: ... })`, render ที่ `UserBackstageEdit.tsx:262-269`) ไม่ใช่พังหรือค้าง

**สิ่งที่หน้าที่เหลือยังแสดงต่อไป เพราะไม่มีอะไรใต้ catch block นั้นถูกผูกกับความสำเร็จของการดึงข้อมูล:** `roleAssignments` ค้างที่ array ว่างตั้งต้น `AccessReachBand` จึงอ่านว่า "No platform privilege" การ์ด "Roles & Scope" อ่านว่า "No roles assigned" และ `MembershipCard` อ่านว่า "Not a member of any cluster or business unit" — สามสถานะว่างที่ฟังดูมั่นใจ อยู่ใต้แถบ error ที่อธิบายอยู่แล้วว่าไม่ควรเชื่อสิ่งไหนเลยในนั้น **และ sheet Add Role ก็ยัง render อยู่** เพราะมันกั้นด้วย `user_backstage.manage` เพียงอย่างเดียว (`UserBackstageEdit.tsx:302`) ซึ่ง session นี้ถือ โดยไม่มีเงื่อนไขผูกกับว่าหน้าโหลดสำเร็จจริงหรือไม่ manager ที่อยู่ในสถานะนี้พอดี — มี `user_backstage.manage` แต่ไม่มี `user.read` — สามารถกดปุ่ม Add Role แล้วมอบ role ทั้งแพลตฟอร์มหรือเฉพาะ cluster ให้ผู้ถือสิทธิ์คนหนึ่งที่ role*เดิม*ของเขาไม่เคยถูกแสดงให้เห็นเลย เสี่ยงมอบซ้ำที่คนละ scope ซึ่งการตรวจซ้ำของ backend เอง (§3.2 ของ [หน้า landing](/th/backstage/user-backstage)) จะจับไม่ได้ เพราะมันปฏิเสธเฉพาะการซ้ำแบบ role+scope*เป๊ะ*เท่านั้น

**ทำไมนี่ไม่ใช่ความผิดพลาดแบบเดียวกับที่หน้าของอีกโมดูลเคยทำ** โมดูลอื่นในแผนนี้เคยยืนยันกับดักฝั่งเขียนสำหรับ session ที่ที่จริงแล้วไปไม่ถึงปุ่มนั้นเลยในทางโครงสร้าง เพราะด่านอ่านที่ล้มเหลวทำให้ปุ่มหายไปก่อนที่ด่านเขียนจะมีความหมาย รูปแบบความล้มเหลวนั้น**ไม่เกิด**ที่นี่: เงื่อนไข render ของ `AddRoleSheet` คือ `<Can permission="user_backstage.manage">` เพียงอย่างเดียว (`UserBackstageEdit.tsx:302`) — ไม่มีเงื่อนไขที่สองผูกกับว่า `userRecord`, `roleAssignments`, หรือ `error` สำเร็จหรือไม่ ปุ่มนี้กดได้จริงแบบไม่มีเงื่อนไขในสถานะนี้ ยืนยันจากการอ่าน JSX ตรง ๆ ไม่ใช่สมมติจากชื่อ permission

**การสลับกันไม่ใช่ช่องว่าง** session ที่ถือ `user.read` แต่ไม่มี `user_backstage.read` เข้าทั้งสอง route ไม่ได้เลยตั้งแต่แรก (`App.tsx:497-512`) จึงไม่มีอะไรให้ตรวจในทิศทางนั้น เพราะ route guard เองคือข้อจำกัดที่ผูกไว้แล้ว

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
| --- | --- | --- | --- |
| 1 | session มี `user_backstage.read` + `.manage` ไม่มี `user.read`; เปิดหน้า detail ของผู้ถือสิทธิ์ที่มีอยู่แล้ว | แถบ error ("Failed to load user: …"); Access Reach Band อ่านว่า "No platform privilege"; Roles & Scope อ่านว่า "No roles assigned"; sheet Add Role ยัง render และเขียนสำเร็จได้ | คือ combination เดียวที่ควรทดสอบโดยตั้งใจ — ดู §3 ทำซ้ำได้ด้วย role ที่มอบแค่ `user_backstage.*` |
| 2 | session เดียวกัน บนหน้ารายการ ใช้ Grant Access | dropdown ของ `UserPicker` แสดง error การค้นหาในตัวมันเองทุกคำค้น; เลือกผู้ใช้ไม่ได้เลย; Submit ถูกบล็อกฝั่ง client (`if (!user) return`) | dialog ไม่ไปถึง backend เลยในสถานะนี้ — ไม่มีอะไรถูกเขียน ไม่มีอะไร 403 มันแค่ทำให้เสร็จไม่ได้ |
| 3 | session เดียวกัน บนหน้ารายการ ใช้ Revoke all access กับแถวที่มีอยู่แล้ว | สำเร็จเต็มที่ — action นี้ไม่เคยพึ่ง `user.read` เลย | ยืนยันว่าช่องว่างอยู่เฉพาะการ*ค้นหา*ผู้ใช้หรือ role เดิมของผู้ถือสิทธิ์ ไม่ใช่ตัว endpoint เขียนเอง |
| 4 | session มีแค่ `user_backstage.read` (ไม่มี `.manage` ไม่มี `user.read`) | หน้ารายการโหลดแบบอ่านอย่างเดียว; หน้า detail แสดงแถบ error และสถานะว่างแบบเดียวกับกรณีที่ 1 โดยไม่มีปุ่ม Add Role/Remove/Revoke ที่ไหนเลย | ความเสี่ยงในรูปแบบของกรณีที่ 1 ที่ผูกกับ `.manage` ไม่เกิดที่นี่ — ไม่มีอะไรบนหน้าที่เขียนได้ |
| 5 | แอดมินสองคนส่งคำขอ Grant Access ที่เหมือนกันเป๊ะ (ผู้ใช้, role, scope เดียวกัน) พร้อมกันในจังหวะเดียว | ทั้งคู่สำเร็จได้ สร้าง assignment row live ซ้ำสองแถว | มีบันทึกไว้แล้ว ไม่ใช่สมมติฐาน: unique index ที่อยู่เบื้องหลังการตรวจซ้ำเป็น NULL-distinct บน `deleted_at` ใน Postgres การ insert live สองครั้งพร้อมกันจึงไม่ถูกบล็อกด้วยมัน (`user_backstage_role.service.ts:198-216`, [Landing](/th/backstage/user-backstage) §3.2) การลบทีหลังทีละแถวยังทำงานปกติ |
| 6 | บัญชีของผู้ถือสิทธิ์ถูกปิดใช้งานขณะยังถือ role แพลตฟอร์มอยู่ | แสดงสองที่: จำนวนผู้ถือสิทธิ์ที่ไม่ active ในแถบสรุปของหน้ารายการ (กดแล้ว filter ได้) และคำเตือนรายบุคคลซ้ำบนหน้า detail ของเขาเอง | การปิดใช้งานบัญชีเกิดที่ [Users](/th/backstage/users) ไม่ใช่ที่นี่ — โมดูลนี้แค่แสดงผลลัพธ์ |
| 7 | session super admin ทดสอบ gate ใด ๆ บนหน้านี้ | ทุกการตรวจ `<Can>` ผ่านโดยไม่มีเงื่อนไข (ทางลัด `is_super_admin` ของ `checkPermission()`, [UI Screens](/th/backstage/user-backstage/ui-screens) §4) | อย่าทดสอบขอบเขตสิทธิ์ของโมดูลนี้จาก session super admin เด็ดขาด — มันเผยช่องว่าง `user.read` ใน §3 ไม่ได้ เพราะต้องใช้ session ที่ตั้งใจไม่ให้ `user.*` ไว้เฉพาะ `user_backstage.*` |

## 5. คำแนะนำ

- **ทดสอบ combination ที่แม่นยำใน §3 โดยตั้งใจ** — role ที่มอบ `user_backstage.read`/`.manage` โดยไม่มี `user.read` — เพราะเป็นสถานการณ์เดียวในโมดูลนี้ที่ให้ผลลัพธ์ที่*ทำให้เข้าใจผิด* ไม่ใช่แค่จำกัดสิทธิ์เฉย ๆ: สถานะว่างที่จริง ๆ คือ "ตรวจไม่ได้" อยู่ข้างตัวควบคุมที่เขียนได้เต็มที่
- **อย่าทดสอบการกั้นสิทธิ์ฝั่งเขียนของโมดูลนี้เพื่อหาความไม่ตรงกันระหว่าง frontend/backend** แบบที่ [Backstage Config](/th/backstage/backstage-config) หรือ [Email Settings](/th/backstage/email-settings) ต้องทำ — ที่นี่ไม่มี: ทั้งสี่ `<Can>` gate และ decorator ของ write endpoint ทั้งสามตัวตรวจคีย์ `user_backstage.manage` เดียวกันเป๊ะ
- **อย่าพึ่ง e2e suite ของ `user-platform` สำหรับการทดสอบขอบเขตสิทธิ์ใด ๆ** — ทั้งสอง spec รันในฐานะ super admin และไม่มี spec ไหนทดสอบ session ที่ลดสิทธิ์เลย ดู [UI Screens](/th/backstage/user-backstage/ui-screens) §4 สำหรับสองจุดที่ suite นี้ล้าสมัยแม้ในแง่ที่ไม่เกี่ยวกับสิทธิ์เลย
- **เมื่อตรวจสอบคำเตือนผู้ถือสิทธิ์ที่ไม่ active หรือ badge "Email not verified" ให้แน่ใจว่ากำลังดูสถานะจริง ไม่ใช่ failure mode ในกรณีที่ 1** — ทั้งคู่เป็นข้อเท็จจริงที่ถูกต้อง (§3.4/§3.3 ของ [หน้า landing](/th/backstage/user-backstage)) เฉพาะเมื่อการดึงข้อมูลบัญชีสำเร็จจริงเท่านั้น

**References:** path ทั้งหมดคือ `../carmen-backstage` (HEAD `157a65e`) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend` (HEAD `937cf5ac4`) `src/App.tsx:497-512` (routes) · `src/components/nav/backstageNav.ts:48` (nav) · `src/pages/UserBackstageManagement.tsx` (gate ของหน้ารายการ, บรรทัด 390,417,586) · `src/pages/UserBackstageEdit.tsx` (gate ของหน้า detail และลำดับการโหลด, บรรทัด 134-160,265-271,302) · `src/pages/userBackstageEdit/RoleGrantList.tsx:126` · `src/components/UserPicker.tsx`, `src/hooks/useUserSearch.ts` (พฤติกรรม error การค้นหาแบบ inline) · `src/context/AuthContext.tsx:354-358`, `src/utils/permissions.ts:56` (ทางลัด super-admin) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/user-backstage-roles/user-backstage-roles.controller.ts` (บรรทัด 88-90,135-137,180-182,233-235,280-282) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-user/backstage-user.controller.ts:128-130,264-266` (`user.read` บน endpoint ของโมดูล Users ที่โมดูลนี้พึ่ง) · `../carmen-turborepo-backend/apps/micro-business/src/authen/user_backstage_role/user_backstage_role.service.ts:198-216` (race ของการมอบสิทธิ์ซ้ำ, กรณีที่ 5)
**Cross-links:** [ผู้ใช้แพลตฟอร์ม (landing)](/th/backstage/user-backstage) &nbsp;·&nbsp; [UI Screens](/th/backstage/user-backstage/ui-screens) &nbsp;·&nbsp; [Users](/th/backstage/users) &nbsp;·&nbsp; [Backstage RBAC — Permissions](/th/backstage/rbac/permissions) &nbsp;·&nbsp; [Backstage Config](/th/backstage/backstage-config) &nbsp;·&nbsp; [Email Settings](/th/backstage/email-settings)
