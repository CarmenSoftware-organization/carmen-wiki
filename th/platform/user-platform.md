---
title: ผู้ใช้แพลตฟอร์ม (User Platform)
description: มอบ role แบบ RBAC — ทั้งแพลตฟอร์มหรือเฉพาะ cluster — ให้บัญชี tb_user ที่มีอยู่แล้ว หน้าจอ "ทะเบียนสิทธิ์" ที่แยกออกมาจาก RBAC และ Users เส้นทาง detail คือ /platform/user-platform/:userId ไม่มี /edit ต่อท้าย และ workflow จริงส่วนใหญ่ยังต้องมี user.read จากโมดูล Users เพิ่มด้วย ซึ่งด่าน nav ของโมดูลนี้เองไม่ครอบคลุม
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, user-platform
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ใช้แพลตฟอร์ม (User Platform)

> **At a Glance**
> **Component:** `UserPlatformManagement` (รายการ) &nbsp;·&nbsp; `UserPlatformEdit` (detail รายบุคคล) &nbsp;·&nbsp; **Route:** `/platform/user-platform` &nbsp;·&nbsp; `/platform/user-platform/:userId` — **สังเกตว่าพารามิเตอร์คือ `:userId` และไม่มี `/edit` ต่อท้าย** ต่างจาก edit route แทบทุกตัวในหนังสือเล่มนี้ &nbsp;·&nbsp; **Nav:** `permission: 'user_platform.read'`, `feature: 'user_platform'`, `groupKey: 'navGroup.platform'` (`platformNav.ts:43`) — **ไม่ใช่** `superAdminOnly` &nbsp;·&nbsp; **Permission key:** `user_platform.read` (ทั้งสอง route) + `user_platform.manage` (ทุกจุดที่เขียนได้บนทั้งสองหน้าจอ) &nbsp;·&nbsp; **ข้อพึ่งพาที่สองที่ไม่ได้ประกาศไว้:** ส่วนใหญ่ที่หน้า detail แสดงยังต้องการ `user.read` ด้วย ซึ่งเป็นคีย์ของโมดูล [Users](/th/platform/users) ที่ route guard ของโมดูลนี้เองไม่เคยตรวจ — ดู §4 และ [Permissions](/th/platform/user-platform/permissions) §3 สำหรับการไล่รอยแบบเต็ม &nbsp;·&nbsp; **e2e suite:** `user-platform` (2 specs) — มี coverage ต่างจากโมดูลส่วนใหญ่ในชุดนี้ แต่ทั้งสอง spec เล็งไปที่ UI ที่หน้าจอนี้ไม่มีแล้ว — ดู [UI Screens](/th/platform/user-platform/ui-screens) §4 &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

User Platform คือจุดที่ role แบบ [RBAC](/th/platform/rbac) — ทั้งแพลตฟอร์ม หรือเฉพาะ cluster เดียว — ถูกผูกเข้ากับบัญชีผู้ใช้ที่มีอยู่แล้ว มันถูกแยกออกจากหน้าจอของโมดูล RBAC เองมาเป็นรายการ nav และ component คู่ของตัวเอง และทั้งคู่ถูกเขียนใหม่ในวันเดียวกัน 2026-09-02 ให้เป็นสิ่งที่ commit message ของมันเองเรียกว่า "ทะเบียนสิทธิ์" (privilege registry) ไม่ใช่ตาราง CRUD ทั่วไป: `UserPlatformManagement` (`../carmen-platform` commit `fc690cb`, PR #250) และ `UserPlatformEdit` (`f6e91c9`, PR #251)

`/platform/user-platform` แสดงรายการผู้ใช้ทุกคนที่ถือ role แพลตฟอร์มอย่างน้อยหนึ่งตัว — คนที่ไม่มีเลยจะถูกกรองออกฝั่ง backend และไม่ปรากฏที่นี่เลย การคลิกชื่อในแถว (เป็น `<a>` ผ่าน react-router `Link` ไม่ใช่ปุ่ม) หรือ action "Manage roles" จะพาไปที่ `/platform/user-platform/:userId` — **id เป็น path segment ธรรมดา ไม่มี `/edit` ต่อท้าย** ผู้อ่านที่จับรูปแบบมาจาก `/users/:id/edit`, `/clusters/:id/edit`, `/applications/:id/edit` และ detail route อื่น ๆ แทบทุกตัวในหนังสือเล่มนี้ อาจพิมพ์ `/platform/user-platform/:userId/edit` แล้วเจอ 404 — route แบบนั้นไม่มีอยู่จริง (`../carmen-platform/src/App.tsx:458-465`) หน้า detail เองก็ไม่มีสวิตช์อ่าน/แก้ด้วย มันเป็นหน้าเดียวที่เพิ่มและลบ role โดยตรง ไม่ใช่ฟอร์มที่มีปุ่ม Save

ทั้งสอง route ถูกกั้นเหมือนกันที่ระดับ route — `requiredPermission="user_platform.read"`, `feature="user_platform"` (`App.tsx:453,461`) — การถือคีย์อ่านอย่างเดียวก็เพียงพอที่จะ*นำทาง*ไปหน้า detail ของผู้ใช้คนไหนก็ได้ ส่วนว่าหน้านั้นจะแสดงอะไรที่เป็นประโยชน์เมื่อไปถึงหรือไม่ เป็นคำถามแยกต่างหาก ตอบไว้ใน §4

## 2. บริบททางธุรกิจ

**ผู้ใช้แพลตฟอร์มไม่ใช่บัญชีชนิดหนึ่ง — มันคือ row ใน `tb_user` ที่บังเอิญมี row อย่างน้อยหนึ่งแถวใน `tb_user_tb_platform_role`** ไม่มีอะไรบนหน้าจอนี้สร้างบัญชีที่อยู่ข้างใต้เลย คนหนึ่งจะมีสิทธิ์ปรากฏที่นี่ได้ด้วยวิธีเดียวกับที่ใครก็ตามกลายเป็น row ใน `tb_user` — สร้างตรงบน [Users](/th/platform/users) (`/users/new`) ผ่านคำเชิญ cluster/BU หรือผ่านการสมัคร self-service — และจะเริ่ม*ปรากฏ*ในทะเบียนนี้ก็ต่อเมื่อมีใครที่ถือ `user_platform.manage` มอบ role แรกให้ ไม่ว่าจะผ่าน **Grant Access** บนหน้ารายการ (ค้นหาผู้ใช้คนไหนก็ได้ด้วยชื่อ) หรือ **Add Role** บนหน้า detail ของผู้ถือสิทธิ์ที่มีอยู่แล้ว

นี่คือความแตกต่างเดียวกับที่ [Users](/th/platform/users) §2 ระบุไว้จากฝั่งของตัวเองแล้ว: "สิ่งที่บัญชีทำได้ใน Platform admin SPA ไม่ได้เก็บอยู่ [บน user row] — นั่นคือ role assignment ของโมดูล RBAC" User Platform คือที่ที่ assignment เหล่านั้นถูกเขียนขึ้นจริง พูดให้เป็นรูปธรรม สิ่งที่แก้ได้ที่นี่และแก้ไม่ได้บน `/users/:id/edit` มีอย่างเดียว — ผู้ใช้ถือ role แพลตฟอร์มตัวไหน ที่ scope ไหนบ้าง — และสิ่งที่แก้ได้บน `/users/:id/edit` แต่แก้ไม่ได้ที่นี่คือทุกอย่างเกี่ยวกับตัวบัญชีเอง: `username`, `email`, ชื่อ, `is_active`, รหัสผ่าน, สมาชิกภาพ cluster/BU การปิดใช้งานหรือลบบัญชีเป็น action ของโมดูล Users ไม่กระทบทะเบียนนี้โดยตรง แม้บัญชีที่ถูกปิดใช้งานจะยังเก็บ role row ไว้ และถูกตั้งค่าสถานะเตือนไว้ที่นี่ (§3.4, [UI Screens](/th/platform/user-platform/ui-screens) §3)

กรอบคิดแบบ "ทะเบียน" ไม่ใช่แค่ความสวยงาม: หน้าจอนี้มีไว้ให้ผู้ตรวจสอบการเข้าถึง (access reviewer) ถามได้ว่า "ใครทำอะไรกับทั้งแพลตฟอร์มได้บ้าง และได้มันมาอย่างไร" โดยไม่ต้องไขว้ทะเบียน Users กับ catalog ของ Roles ด้วยมือ ทุกแถวบอก scope ทุก grant บอกว่าใครเป็นคนให้และเมื่อไหร่ (ในกรณีที่หาได้ — §3.2) และผู้ถือสิทธิ์ที่ไม่ active แต่ยังถือสิทธิ์อยู่จะถูกชี้ให้เห็นชัด ไม่ปล่อยให้กลืนหายไปในรายการที่ดูปกติ

## 3. แนวคิดสำคัญ

### 3.1 ค่าสรุปรวมทั้งทะเบียน (registry-wide summary aggregate)

`GET /api-system/platform/users` (`userPlatformService.getAll()` หนุนหลังโดย `UserPlatformRolesController.listUsers`, `RequirePlatformPermission('user_platform.read')`) คืนไม่ใช่แค่หน้าปัจจุบันของผู้ถือสิทธิ์ แต่มี block `summary` มาด้วย — `holders`, `platform_wide`, `cluster_only`, `assignments`, `inactive` — ที่อธิบายผู้ถือสิทธิ์**ทุกคน**ที่ตรงกับ filter/search ที่ใช้งานอยู่ ไม่ใช่แค่หน้าที่โหลดมา (`user_platform_role.service.ts:541-572`, `buildRegistrySummary`) นี่คือสิ่งที่ทำให้ `PlatformAccessSummary` (แถบเหนือตาราง) แสดงจำนวนผู้ถือสิทธิ์ที่ไม่ active และสัดส่วนทั้งแพลตฟอร์ม/เฉพาะ cluster ได้ถูกต้อง แม้ผู้ถือสิทธิ์ที่ไม่ active คนเดียวจะถูกเรียงไปอยู่หน้า 3

type ฝั่ง frontend ของฟิลด์นี้เป็น optional และคอมเมนต์ของมันเองบอกว่าเป็นสิ่งที่ "จะมาใน backend deploy รอบหลัง" (`types/index.ts:587-590`) และ `PlatformAccessSummary.tsx` ก็ render สถานะ "ยังไม่มี summary" ไว้ถูกต้องสำหรับกรณีนั้น **ณ source HEAD ที่แผนนี้ตรึงไว้ การเปลี่ยนผ่านนั้นเสร็จสมบูรณ์แล้วฝั่ง backend — ทุก response มี `summary` ติดมาเสมอ แต่ไม่ได้มาจากการเรียกแบบไม่มีเงื่อนไขจุดเดียว** `listPlatformUsers()` แยก branch ตามว่ามี assignment ที่ยัง live ตรงกับ filter อยู่หรือไม่: ถ้าไม่มีเลย (`grouped.length === 0`) มันจะคืนค่า `summary` เป็น literal ที่ตั้งเป็นศูนย์ตรง ๆ โดยไม่เรียก `buildRegistrySummary()` เลย (`user_platform_role.service.ts:350-356`) แต่ในกรณีอื่น `buildRegistrySummary(matched)` จะถูกเรียกครั้งเดียวกับชุดผู้ใช้ที่ผ่านการกรองทั้งหมด (บรรทัด 411) แล้วผลลัพธ์ตัวเดียวกันนั้นถูกส่งต่อไปทุก return path ที่เหลือ ไม่ได้คำนวณใหม่ — ทั้ง branch ที่ pagination ไม่เหลือแถวเลย (`pageIds.length === 0`, บรรทัด 432-438) และ response สุดท้าย (บรรทัด 517-521) ใช้ตัวแปร `summary` ตัวเดียวกันนี้ซ้ำ กล่าวคือทั้งสอง branch ต่างกันตรง*วิธี*ที่ได้ summary มา — อันหนึ่งเป็น literal ศูนย์ที่ hardcode ไว้ อีกอันเรียกฟังก์ชัน aggregate จริง — แต่ทั้งคู่ได้ summary เสมอ gateway proxy จะ forward สิ่งที่ได้รับมาทุกครั้ง (`user-platform-roles.service.ts:140-148`) ซึ่งตามข้างต้นคือทุกครั้งที่ response มี `summary` ติดมา branch fallback ฝั่ง frontend ยังเป็นโค้ดป้องกันที่ถูกต้อง เพียงแต่ไม่มีทางถูกเรียกใช้จริงกับ backend ที่แผนนี้บันทึกไว้ อย่าอ่านการที่มันยังอยู่ใน source ว่าค่า aggregate นี้ยังทยอย roll out อยู่

รายละเอียดการคำนวณหนึ่งจุดที่ควรระบุให้แม่นยำ เพราะกลับกันได้ง่าย: `holders` กับ `inactive` นับจากชุดที่**ผ่านการกรองแล้ว** (เคารพ filter role/cluster/status ที่ใช้งานอยู่) แต่ `platform_wide`/`cluster_only` คำนวณจากชุด assignment ที่ยัง live ทั้งหมดของผู้ถือสิทธิ์แต่ละคนที่ผ่านการกรอง โดยตั้งใจไม่จำกัดด้วย filter role/cluster ที่ใช้งานอยู่ — ผู้ถือสิทธิ์ที่ถูกกรองเข้ามาด้วย role หนึ่งจึงยังนับเข้าสัดส่วนทั้งแพลตฟอร์ม/เฉพาะ cluster ตามทุกอย่างที่เขาถือ ไม่ใช่แค่ role ที่ตรงกับ filter (`user_platform_role.service.ts:534-538`, คอมเมนต์ของ method เอง) เหตุผลที่ระบุไว้ตรงนั้นเหมือนกับที่ [UI Screens](/th/platform/user-platform/ui-screens) §2 ให้ไว้สำหรับรายการ assignment รายแถว: การแสดงขอบเขตจริงของผู้ถือสิทธิ์ให้น้อยกว่าความจริงบนหน้าจอ access-review คือ failure mode ที่ผิด

### 3.2 สองทางเข้า endpoint เขียนคู่เดียวกัน — และ race ที่มีบันทึกไว้

การมอบ role เกิดขึ้นได้จากทั้งสองหน้าจอ: **Grant Access** บนหน้ารายการ (`GrantAccessDialog` เลือกผู้ใช้คนไหนก็ได้ผ่านช่องค้นหา, role หนึ่งตัวหรือมากกว่าที่ scope เดียวกัน, `POST .../roles/bulk`) หรือ **Add Role** บนหน้า detail ของผู้ถือสิทธิ์ที่มีอยู่แล้ว (`AddRoleSheet` ทีละ role, `POST .../roles`) ทั้งสองทางสุดท้ายเขียนตารางเดียวกัน `tb_user_tb_platform_role` และทั้งคู่ปฏิเสธการซ้ำแบบเป๊ะ (user + role + scope เดียวกัน, live) ด้วย 409 ก่อนเขียนอะไรเลย — `assign()`/`assignBulk()` ใน `user_platform_role.service.ts:103-141,175-218`

คอมเมนต์ของ `assignBulk()` เองระบุ caveat ที่ใช้กับเส้นทางเพิ่มทีละ role ได้ด้วย แม้จะมีแค่คอมเมนต์นี้ที่พูดถึงตรง ๆ: การตรวจซ้ำเป็นแบบ read-then-write และ unique index ที่อยู่เบื้องหลังรวม `deleted_at` เข้าไปด้วย ซึ่ง Postgres ถือว่า NULL แต่ละตัวแยกจากกันใน unique index โดย default — จึง**ไม่**บล็อกการมอบสิทธิ์แบบเดียวกันสองครั้งที่เกิดพร้อมกันไม่ให้กลายเป็น row live สองแถวแยกกัน (`user_platform_role.service.ts:220-228`) การลบทีหลังทีละแถวยังทำงานปกติ ทะเบียนจะแค่แสดงคู่ role/scope เดียวกันซ้ำสองครั้งในช่วงนั้น ควรรู้ไว้ก่อนที่จะมองว่า row ซ้ำเป็นบั๊กของ UI แทนที่จะเป็น race ที่มีบันทึกไว้แล้ว

### 3.3 คอลัมน์ยืนยันอีเมลสามตัวของ `tb_user` — หน้าจอเดียวที่แสดงมัน

มีสามคอลัมน์ใน `tb_user` ที่ไม่มีหน้าไหนในโมดูล Users อ่านเลย: `email_verified_at`, `email_verification_token_hash`, `email_verification_expires_at` (เพิ่มโดย migration `20260804000000_user_email_verification`, `schema.prisma:485-487`) `UserPlatformEdit.tsx` เป็น SPA surface**เดียว**ของทั้งสามตัว และแม้แต่ตรงนั้นก็ใช้แค่ตัวแรก: `email_verified_at?: string | null` (บรรทัด 43) ป้อนเข้า boolean ที่คำนวณไว้ตัวเดียว `emailVerified = !!userRecord?.email_verified_at` (บรรทัด 195) แสดงเป็น badge แบบ outline "Email not verified" ข้าง page header เมื่อเป็น false คู่ token/expiry ไม่เคยถูกส่งไปหา frontend หรือแสดงที่ไหนเลย

สิ่งที่ตั้งค่าคอลัมน์เหล่านี้ ไม่มีอันไหนอยู่บนหน้าจอนี้: `email_verified_at` ถูกเขียนเป็น `new Date().toISOString()` ตอนสร้างบัญชี — สำหรับบัญชีที่มาจากคำเชิญ ซึ่งอีเมลถูกพิสูจน์แล้วก่อนที่บัญชีจะถูกสร้างด้วยซ้ำ (`createVerifiedUser` ของ `AuthService`, `auth.service.ts:927-931`) — หรือทีหลัง เมื่อ `verifyEmail(token)` ใช้คู่ `email_verification_token_hash`/`email_verification_expires_at` ที่ยังไม่หมดอายุ (`auth.service.ts:1244-1302`) `resendVerificationEmail()` คือสิ่งที่ออก token คู่นั้นใหม่ (หรือครั้งแรก) ให้บัญชีที่ยังไม่ยืนยันอีเมล (`auth.service.ts:1329-1375`) `email_verified_at` ที่เป็น `null` ยังบล็อกการล็อกอินตรง ๆ โดยไม่เกี่ยวกับหน้าจอนี้เลย (`auth.service.ts:498`) — ทุกบัญชีที่มีอยู่ก่อน migration นี้ถูก backfill ให้เป็น "verified" ตอน deploy โดยเฉพาะเพื่อไม่ให้ด่านใหม่นี้ล็อกผู้ใช้ทั้งแพลตฟอร์มที่มีอยู่เดิมออกไป (`20260804000000_user_email_verification/migration.sql`)

ผลในทางปฏิบัติต่อโมดูลนี้: badge "Email not verified" บนผู้ถือ role ไม่ใช่รายละเอียดตกแต่ง มันบอกว่าบัญชีนี้อาจล็อกอินและใช้ role ที่กำลังตรวจสอบอยู่ไม่ได้เลยด้วยซ้ำ หน้าจอนี้แค่แสดงข้อเท็จจริงนั้น การเปลี่ยนมันต้องให้เจ้าของบัญชียืนยันให้เสร็จ (หรือให้ operator เข้าแทรกผ่าน auth flow ด้านบน) ไม่ใช่อะไรบน `/platform/user-platform`

### 3.4 ผู้ถือสิทธิ์ที่ไม่ active และความหมายของ "ขอบเขต" บนหน้า detail

ทั้งสองหน้าจอปฏิบัติกับ "ถือสิทธิ์อยู่ทั้งที่ปิดใช้งานบัญชีแล้ว" เป็นข้อค้นพบ ไม่ใช่สถานะปกติ: แถบสรุปของหน้ารายการแสดงจำนวนผู้ถือสิทธิ์ที่ไม่ active เป็นคำเตือนที่กดได้ และหน้า detail ก็ทวนคำเตือนเดียวกันต่อผู้ถือสิทธิ์แต่ละคน (`!isActive && roleAssignments.length > 0`, `UserPlatformEdit.tsx:277-285`) — เพราะผู้ตรวจสอบที่เปิดหน้าของคนคนเดียวไม่ควรต้องจำจำนวนที่เห็นจากอีกหน้าจอ พาดหัว "ขอบเขต" ของหน้า detail เอง (`AccessReachBand`) คำนวณจาก `roleAssignments` ทั้งหมด ซึ่งเป็นคำขอ*แยก*จาก record ของบัญชีเอง (§4) — ดู [Permissions](/th/platform/user-platform/permissions) §3 ว่าพาดหัวนี้เป็นอย่างไรเมื่อคำขอที่ป้อนมันล้มเหลว

## 4. บทบาทและสิทธิ์

| จุด | Permission | หมายเหตุ |
| --- | --- | --- |
| รายการ sidebar, ทั้งสอง route | `user_platform.read` | `platformNav.ts:43`; `App.tsx:453,461` |
| Grant Access (header รายการ + empty state), Revoke all access (row menu รายการ), Add Role (detail), Remove role (แถวใน detail) | `user_platform.manage` | คีย์**เดียว**อีกตัวที่โมดูลนี้ใช้ — grep ทั้ง repo หา `user_platform\.` ไม่พบ literal ตัวที่สาม decorator ของ backend ทุก write endpoint ตรงกันเป๊ะ: `POST .../roles`, `POST .../roles/bulk`, `DELETE .../roles/:id` ล้วนเป็น `RequirePlatformPermission('user_platform.manage')` |
| การโหลด identity บัญชีและรายการ role บนหน้า detail | **`user.read`** — ไม่ใช่ `user_platform.read` | route guard ของหน้า detail เองไม่เคยตรวจคีย์นี้เลย ดู [Permissions](/th/platform/user-platform/permissions) §3 สำหรับการไล่รอยแบบเต็มว่า session ที่ขาดคีย์นี้เห็นอะไรจริง ๆ |

การกั้นสิทธิ์ฝั่งเขียนของโมดูลนี้สะอาดผิดปกติเมื่อเทียบกับอีกสองโมดูลที่บันทึกไว้แล้วในแผนนี้ ([Platform Config](/th/platform/platform-config) §4.3, [Email Settings](/th/platform/email-settings) §4.2): `<Can>` ฝั่ง frontend กับ decorator `@RequirePlatformPermission` ฝั่ง backend ตรวจ resource กับ action **เดียวกันเป๊ะ** คือ `user_platform.manage` บนทุกจุดที่เขียนได้ทั้งสี่จุดในทั้งสองหน้าจอ ความซับซ้อนที่นี่ไม่ใช่ความไม่ตรงกันระหว่าง frontend/backend — แต่คือการเข้าถึงโมดูลนี้ได้เลย (`user_platform.read`) ไม่ใช่สิ่งเดียวกับการ*เห็น*อะไรเมื่อไปถึงหน้า detail เมทริกซ์ด่านเต็ม ตาราง backend guard และ key combination ที่ทำให้เกิดช่องว่างนี้พอดี: [Permissions](/th/platform/user-platform/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Users](/th/platform/users) — เป็นเจ้าของบัญชี `tb_user` ที่โมดูลนี้ผูก role เข้าไป identity, การเปิด/ปิดใช้งาน และสมาชิกภาพ cluster/BU ล้วนแก้ที่นั่น ไม่ใช่ที่นี่ ดู §2 สำหรับการแบ่งงานที่แน่นอน และ §3.3 สำหรับคอลัมน์ยืนยันอีเมลที่โมดูลนี้แสดงแทนโมดูล Users
- [Platform RBAC](/th/platform/rbac) — เป็นเจ้าของ catalog และตัว role เอง (`tb_platform_role`, `tb_platform_permission`) รวมถึง union `Scope` ที่ type `PlatformUserScope`/`Scope` ของโมดูลนี้สะท้อนตาม และเคยบันทึกโมดูลนี้ไว้ระดับสรุปก่อนหน้านี้จะมีหน้าเป็นของตัวเอง หน้านี้คือเวอร์ชันที่ครบถ้วนกว่า
- [Super Admins](/th/platform/super-admins) — flag ข้ามผ่านแยกต่างหาก กั้นด้วย `superAdminOnly` (`tb_platform_super_admin`) ไม่ใช่ role ใน `tb_platform_role` และไม่ใช่สิ่งที่หน้าจอนี้แสดงหรือมอบให้
- Clusters — `cluster_id` ที่ assignment แบบมี scope อ้างอิงถึง ทั้ง Grant Access และ Add Role อ่านรายการ cluster เพื่อป้อน dropdown scope เท่านั้น (`cluster.read`, best-effort — ถ้าโหลดไม่ได้ dropdown จะลดระดับเหลือแค่ raw id แต่ไม่บล็อกการมอบสิทธิ์)

## 6. แหล่งอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (HEAD `157a65e`, 2026-09-04) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`, 2026-09-06) หรือ `../carmen-platform-e2e` (HEAD `a8e3b31`, 2026-08-25)

- `src/pages/UserPlatformManagement.tsx` — หน้ารายการ/ทะเบียน (commit `fc690cb`, PR #250, 2026-09-02)
- `src/pages/UserPlatformEdit.tsx` — หน้า detail รายบุคคล (commit `f6e91c9`, PR #251, 2026-09-02) รวม field `UserDetailRecord.email_verified_at` (บรรทัด 43) และ badge ที่คำนวณจากมัน (บรรทัด 195)
- `src/pages/userPlatformManagement/{PlatformAccessSummary,roleChips,GrantAccessDialog}.tsx`, `src/pages/userPlatformEdit/{AccessReachBand,MembershipCard,RoleGrantList,AddRoleSheet}.tsx` — component สนับสนุน บันทึกไว้เต็มใน [UI Screens](/th/platform/user-platform/ui-screens)
- `src/services/userPlatformService.ts`, `src/services/userRoleService.ts` — REST client สองตัวที่โมดูลนี้เรียกตรง
- `src/components/nav/platformNav.ts:43`, `src/App.tsx:451-465` — รายการ nav และการลงทะเบียน route
- `src/types/index.ts:544-603` — `Scope`, `PlatformUserScope`, `PlatformUserRoleAssignment`, `PlatformUserRow`, `PlatformUserRegistrySummary`, `PlatformUsersResponse`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/user-platform-roles/user-platform-roles.controller.ts` — พื้นผิว REST และ permission decorator ของทุก route (§4)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/user-platform-roles/user-platform-roles.service.ts:140-148` — ตรรกะ forward `summary` (§3.1)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/user_platform_role/user_platform_role.service.ts` — `assign`/`assignBulk`/`remove`/`listPlatformUsers`/`buildRegistrySummary` (§3.1, §3.2)
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `createVerifiedUser` (บรรทัด 919-933), `verifyEmail` (1244-1302), `resendVerificationEmail` (1329-1375), ด่าน login (บรรทัด 498) (§3.3)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:485-487` — คอลัมน์ยืนยันอีเมลสามตัวของ `tb_user`; migration `20260804000000_user_email_verification`
- `../carmen-platform-e2e/tests/user-platform/{user-platform-list,user-platform-config}.spec.ts` และ `pages/UserPlatform{ManagementPage,EditPage}.ts` — ดู [UI Screens](/th/platform/user-platform/ui-screens) §4 สำหรับจุดที่ suite นี้ไม่ตรงกับ source ปัจจุบันแล้ว

## 7. หน้าในโมดูลนี้

- [UI Screens](/th/platform/user-platform/ui-screens) — พฤติกรรมและ layout เต็มของทั้งสองหน้าจอ และข้อค้นพบเรื่องความล้าสมัยของ e2e suite
- [Permissions](/th/platform/user-platform/permissions) — เมทริกซ์ด่านเต็ม และการไล่รอยช่องว่าง `user.read` แบบ end-to-end
