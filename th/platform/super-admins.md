---
title: ผู้ดูแลระบบสูงสุด (Super Admins)
description: บัญชีดำ god-mode ของแพลตฟอร์ม — SuperAdminManagement (/backstage/super-admins) กั้นด้วย superAdminOnly โดยไม่มี RBAC permission key เลย พร้อมตาราง tb_backstage_super_admin สามคอลัมน์ที่แท้จริง
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, super-admins
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ดูแลระบบสูงสุด (Super Admins)

> **At a Glance**
> **หน้าจอ:** `SuperAdminManagement` (`/backstage/super-admins`) — ทะเบียนแบบการ์ด (หนึ่ง `<ul>`/`<li>` ต่อคน) ไม่ใช่ `DataTable` &nbsp;·&nbsp; **ตัว gate:** **ไม่มี RBAC permission key เลย** — ทั้งรายการใน nav และ route เป็น `superAdminOnly: true` ตรวจกับ `isSuperAdmin` (มาจาก `effectivePermissions.is_super_admin`) ไม่เคยตรวจกับ permission string เลย &nbsp;·&nbsp; **Nav:** `feature: 'super_admins'`, `dividerBefore: true` — เส้นคั่นบอกจุดที่ sidebar เปลี่ยนจากงานตั้งค่าประจำวันไปเป็น "ใครอีกบ้างที่เข้าถึงงานตั้งค่าได้" &nbsp;·&nbsp; **การบังคับใช้ฝั่ง backend:** ทั้งสาม endpoint (`GET`/`POST`/`DELETE /api-system/backstage/super-admins`) อยู่หลัง `BackstageSuperAdminGuard` ซึ่ง resolve `is_super_admin` จากฐานข้อมูลใหม่ทุกครั้งที่มีคำขอ — ไม่มี cache เลยตลอดสาย &nbsp;·&nbsp; **ตาราง:** `tb_backstage_super_admin` — มีคอลัมน์ที่มีความหมายจริงสามคอลัมน์ (`user_id`, `is_active`, `current_business_unit_id`) นอกเหนือจากคอลัมน์ audit บันทึกไว้ครบใน §5 ด้านล่างแทนที่จะแยกเป็นหน้า `data-model` &nbsp;·&nbsp; **ชุด e2e:** `super-admins` (1 spec, HEAD `bb8f671`, 2026-06-11) — เก่ากว่าการเขียนใหม่เป็นทะเบียนแบบการ์ดเมื่อ 2026-09-02 และพังตั้งแต่ fixture ของชุดทดสอบเอง ไม่ใช่แค่การ assert รายจุด (§6)

![ผู้ดูแลระบบสูงสุด (Super Admins) screen](/screenshots/platform/super-admins/index.png)

## 1. ภาพรวม

Super Admins คือหน้าจอเดียวในผลิตภัณฑ์ Platform admin ที่มีหน้าที่ทั้งหมดคือควบคุมว่าใครเข้าถึงหน้าจออื่นทุกหน้าได้ รายการใน nav (`../carmen-backstage/src/components/nav/backstageNav.ts:51`) เขียนไว้ว่า

```
{ path: '/backstage/super-admins', labelKey: 'nav.superAdmins', icon: ShieldAlert,
  superAdminOnly: true, groupKey: 'navGroup.backstage', feature: 'super_admins', dividerBefore: true }
```

แถวนี้ไม่มีฟิลด์ `permission` เลย ทุกแถวอื่นใน sidebar ถูกกรองด้วย `!item.permission || opts.hasPermission(item.permission)` (`backstageNav.ts:118`) ส่วนแถวนี้ถูกกรองด้วย `!item.superAdminOnly || opts.isSuperAdmin` แทน (`backstageNav.ts:119`) — เป็นค่า boolean ไม่ใช่การค้นหา permission string คอมเมนต์สองบรรทัดเหนือแถวนี้ (`backstageNav.ts:49-50`, ภาษาไทย) บอกเหตุผลของเส้นคั่นไว้ตรง ๆ ว่า *"เส้นคั่นแบ่งสองแถวล่างออกจากงานตั้งค่าประจำวัน — ทั้งคู่เปลี่ยนสิ่งที่คนอื่นเข้าถึงได้ ไม่ตั้งเป็นกลุ่มใหม่เพราะยังเป็นเรื่อง Backstage เหมือนกัน ต่างแค่ระดับความเสี่ยง"* route (`../carmen-backstage/src/App.tsx:489-496`) ก็ห่อในแบบเดียวกัน ด้วย `<PrivateRoute requireSuperAdmin feature="super_admins">`

วิธีอธิบาย gate นี้อย่างตรงไปตรงมา — และเป็นวิธีที่หน้านี้ใช้ตลอดทั้งหน้า — คือ **"ไม่มี RBAC permission key — ทั้งรายการเมนูและ route เป็น `superAdminOnly`"** ไม่ใช่ "ไม่มีการตรวจสิทธิ์เลย" การตรวจนี้มีอยู่จริงและทำงานสองรอบ: รอบแรกใน `PrivateRoute` (`../carmen-backstage/src/components/PrivateRoute.tsx:89-91`, `if (requireSuperAdmin && !isSuperAdmin) return <Forbidden />` ตรวจหลังกิ่งการ resolve platform authority และก่อนการตรวจ feature flag ที่บรรทัด 96-105 — ลำดับ permission-ก่อน-flag แบบเดียวกับทุก route ที่กั้นสิทธิ์ในหนังสือเล่มนี้) และตรวจซ้ำอีกครั้งอย่างเป็นอิสระในทุกคำขอฝั่ง backend สิ่งที่ขาดหายไปจริง ๆ คือ permission *key*: ไม่มีอะไรใน `tb_backstage_permission` ที่ตั้งชื่อความสามารถนี้ไว้ ดังนั้นไม่มี role bundle ใดให้หรือถอดสิทธิ์เข้าถึงหน้านี้ได้ — ทางเดียวที่จะเข้าได้คือต้องถือแถวในบัญชีดำนี้อยู่แล้วเท่านั้น

`isSuperAdmin` เองคือ `!!effectivePermissions?.is_super_admin` (`../carmen-backstage/src/context/AuthContext.tsx:342`) และ `effectivePermissions` ถูกดึงเพียงสามจุด — ครั้งหนึ่งตอนหน้าเว็บ mount และอีกครั้งต่อการล็อกอินแต่ละครั้ง (ล็อกอินด้วยรหัสผ่านหรือ Google sign-in) (`fetchEffectivePermissions()` เรียกที่ `AuthContext.tsx:87`, `:185` และ — สำหรับ Google sign-in — `:289`) — ไม่มีการ poll ซ้ำ §5.4 อธิบายว่าการแคชแบบนี้มีผลอย่างไรกับ session ที่เปิดค้างอยู่ตอนที่แถวของใครสักคนถูกถอดออก

ฝั่ง backend `BackstageSuperAdminsController` (`../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-super-admins/backstage-super-admins.controller.ts:63-65`) ใส่ `@UseGuards(KeycloakGuard, BackstageSuperAdminGuard)` ไว้ที่ระดับ controller ดังนั้น `list`, `add`, และ `remove` ถูกกั้นเหมือนกันทั้งหมด `BackstageSuperAdminGuard.canActivate` (`../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-super-admin.guard.ts:44-76`) ยิง TCP call ใหม่ไปหา `BackstagePermissions.effective` ทุกครั้งที่ถูกเรียก และ fail-closed — error ที่โยนออกมาหรือ response ที่ไม่ใช่ OK จะปฏิเสธคำขอทันที (บรรทัด 55-68) — ไม่มีการตกกลับไปใช้ค่าที่แคชไว้หรือค่า default เลย นี่หมายความว่า **ตัว API เองต้องการให้ผู้เรียกเป็น super admin อยู่แล้วถึงจะจัดการบัญชีดำนี้ได้** ซึ่งเป็นผลที่ตามมาเรื่องการ bootstrap ที่ครอบคลุมใน §5.2

## 2. บริบททางธุรกิจ

แถวใน `tb_backstage_super_admin` คือการ bypass ไม่ใช่ชุดของสิทธิ์ มี short-circuit อิสระสองจุดที่ยึดค่านี้:

- **Frontend:** `checkPermission()` (`../carmen-backstage/src/utils/permissions.ts:56`) — `if (eff?.is_super_admin) return true;` — ก่อนที่จะไปดู `eff.platform` หรือ `eff.clusters` เลยด้วยซ้ำ ทุกการตรวจ `hasPermission()`/`<Can>` ในแอปนี้ผ่านฟังก์ชันนี้ทั้งหมด
- **Backend:** `BackstagePermissionGuard.canActivate` (`../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-permission.guard.ts:110`) — `if (eff?.is_super_admin === true) return true;` — เทียบแบบ strict-equality ซึ่งคอมเมนต์ของ guard เองบอกว่าต้องตรงกับตัวกรองขอบเขตฝั่ง analytics เป๊ะ ๆ "ไม่งั้นค่าเพี้ยน ๆ อย่าง `\"false\"` หรือ `1` อาจให้ผลต่างกันระหว่าง guard กับตัวกรองข้อมูล" นี่คือ guard ตัวเดียวกับที่อยู่หลัง `@RequireBackstagePermission` decorator ทุกตัวใน backend gateway — พูดง่าย ๆ คืออยู่หลัง route ที่กั้นด้วย RBAC เกือบทุกเส้นในผลิตภัณฑ์นี้

นี่คือสิ่งเดียวกับที่ subtitle ของหน้าจอเองบอกไว้: *"Backstage users who bypass all permission checks"* (`pages.superAdmins.subtitle`, `../carmen-backstage/src/i18n/en.ts:4091`) หน้าจอนี้มีไว้เพื่อให้บัญชีดำเล็ก ๆ ที่ตรวจสอบย้อนกลับได้ — ไม่ใช่ role ไม่ใช่ชุด permission — เป็นจุดเดียวที่ตอบคำถามว่า "ตอนนี้ใครถือ god mode อยู่บ้าง" การให้สิทธิ์นี้เหมาะกับทีมวิศวกรรม/ซัพพอร์ตของแพลตฟอร์มที่ต้องเข้าถึงได้แบบไม่มีเงื่อนไขข้ามทุกคลัสเตอร์และทุก business unit ไม่ใช่ตัวแทนของ RBAC role bundle สำหรับใครก็ตามที่งานจำกัดอยู่แค่ resource บางส่วน

## 3. แนวคิดสำคัญ

### 3.1 หน้าจอทะเบียนรายชื่อ

`SuperAdminManagement` (`../carmen-backstage/src/pages/SuperAdminManagement.tsx`) ดึง `GET /api-system/backstage/super-admins` ตอน mount (`fetchData`, บรรทัด 90-105) แล้วเรนเดอร์ `<Card>` เดียวที่บรรจุ `<ul className="divide-y">` ของแถว `<li>` (บรรทัด 284-293) — ไม่ใช่ `DataTable` แต่ละแถว (`RosterRow`, บรรทัด 391-466) แสดง avatar พร้อมอักษรย่อไม่เกินสองตัว ชื่อหรืออีเมลของคนนั้น (ตกกลับไปเป็นขีดกลาง (em dash) โดยเจตนา ไม่ใช้คำอย่าง "Unknown user" — คอมเมนต์ของ component เองอธิบายเหตุผล: frontend ที่ deploy ไปก่อน backend ที่ยัง join ฟิลด์เหล่านี้ไม่ได้ จะทำให้ทุกแถวอ่านราวกับว่าผู้ใช้ถูกลบไปแล้ว, บรรทัด 28-32) UUID ของ `user_id` แบบดิบ ป้าย Active/Inactive และบรรทัด "Granted `<เวลาแบบสัมพัทธ์>`"

ช่องค้นหา (`SearchInput`) จะปรากฏก็ต่อเมื่อทะเบียนมีมากกว่า `SEARCH_THRESHOLD = 8` แถว (บรรทัด 57) — คอมเมนต์ของ component เองให้เหตุผลไว้ว่า "ทะเบียนที่สั้นขนาดนี้มีไว้อ่าน ไม่ใช่ค้นหา... ต่ำกว่านั้นมันคือ control ที่ไม่มีใครใช้เลย" (บรรทัด 54-56) subtitle ของหัวเพจบอกผลลัพธ์แทนที่จะบรรยายตัวหน้าจอ: ระหว่างโหลดข้อมูลและยังไม่มีอะไรขึ้นจอเลยจะโชว์ subtitle ทั่วไป นอกนั้นจะบอกจำนวนคนตรง ๆ ("One person on this platform bypasses every permission check" / "`{count}` people... bypass every permission check", บรรทัด 201-207) — ข้อเท็จจริงข้อเดียวที่ operator มาที่หน้านี้เพื่อเช็ก

ปุ่ม **Export** (ที่หัวเพจ ปิดใช้งานระหว่างโหลดหรือตอนไม่มีข้อมูล) ดาวน์โหลด CSV ของทุกแถวที่มองเห็นอยู่ — user, email, `user_id`, สถานะ, และคอลัมน์ audit สี่ตัว (`created_at`/`created_by`/`updated_at`/`updated_by`) ผ่าน `auditCsvFields(normalizeAudit(r))` (บรรทัด 179-199) `DevDebugSheet` (บรรทัด 377) เปิดดู response ดิบของ `GET` ไว้สำหรับ debug ตอนพัฒนา

**ช่องว่างจริงในระบบ audit trail ที่ตรวจสอบยืนยันแล้ว:** บรรทัด "Granted" ของแต่ละแถว (`AuditMeta` พร้อม `verbKey="pages.superAdmins.grantedVerb"`, บรรทัด 451-455) โชว์ได้แค่เวลาแบบสัมพัทธ์เท่านั้น ไม่เคยโชว์ชื่อคน และนี่ไม่ใช่ข้อจำกัดของการเรนเดอร์ฝั่ง frontend — ชื่อไม่เคยถูกบันทึกไว้ตั้งแต่แรก ทั้ง `add()` ของ `backstage_super_admin.service.ts` เอง (`../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_super_admin/backstage_super_admin.service.ts:133-138`) และการเรียก `create()` ของสคริปต์ seed สำหรับ bootstrap (`../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.backstage-super-admin.ts:29-34`) เขียนแค่ `{ user_id, is_active: true }` — ไม่มีจุดไหนตั้ง `created_by_id` เลย การค้นทั้ง repository หาโค้ดที่เขียนลง `created_by_id` ไม่พบจุดไหนนอกจากช่องว่างในการเขียนจุดนี้ ส่วน Prisma middleware ของ log-events (`../carmen-turborepo-backend/packages/log-events-library/src/middleware/prisma-audit.middleware.ts`) เขียน audit-event เป็นสตรีมแยกต่างหาก ไม่ใช่คอลัมน์นี้ กลไก `@EnrichAuditUsers()` ของ gateway (`../carmen-turborepo-backend/apps/backend-gateway/src/common/enrichment/audit-shape.ts:2,4-7`, `AUDIT_BY_ID_FIELDS = ['created_by_id', ...]`) resolve ชื่อได้ก็ต่อเมื่อมี `created_by_id` ส่งมาให้เท่านั้น ดังนั้น `audit.created` จึงมีแค่ `.at` เสมอ — ตรงกับที่คอมเมนต์ของ type `SuperAdmin` ฝั่ง frontend เองคาดไว้อยู่แล้ว ("gateway's `@EnrichAuditUsers()` nests `created_at` here as `audit.created.at`," `../carmen-backstage/src/types/index.ts:1136`) ในทางกลับกันก็เหมือนกัน: การเรียก `update()` ของ `remove()` (service.ts:163-166) ตั้งแค่ `deleted_at` ไม่เคยตั้ง `deleted_by_id` — ดังนั้นบันทึกว่า *ใคร* เป็นคนถอดสิทธิ์ super admin ก็ไม่ถูกบันทึกไว้เช่นกัน มีแค่ *เมื่อไหร่* เท่านั้น

### 3.2 การเพิ่มผู้ดูแลระบบสูงสุด

ปุ่ม **Add Super Admin** ที่หัวเพจเปิด `Dialog` ที่มี `UserPicker` แบบพิมพ์ค้นหา (ค้นฝั่ง server ผ่าน `useUserSearch`) ไม่ใช่ `<select>` ธรรมดาที่ build ก่อนหน้านี้เคยใช้ ผู้ใช้ที่ถือสิทธิ์นี้อยู่แล้วจะถูกแสดงเป็น disabled ใน picker แทนที่จะปล่อยให้ส่งคำขอไปเจอ 409 ที่รู้ผลอยู่แล้ว (`superAdminUserIds` memo, `SuperAdminManagement.tsx:113-116`) `handleAdd` (บรรทัด 138-164) เรียก `POST /api-system/backstage/super-admins` ด้วย `{ user_id }`; เมื่อเจอ `409` โดยเฉพาะจะล้างค่าที่เลือกไว้ทิ้งแล้วดึงข้อมูลใหม่ ด้วยเหตุผลว่า 409 ตรงนี้แปลว่ามีคนอื่นให้สิทธิ์คนเดียวกันไปก่อนแล้ว ดังนั้นรายการบนจอพิสูจน์ได้ว่าเก่าไปแล้ว (บรรทัด 151-160) — ความล้มเหลวแบบอื่นไม่เปลี่ยนอะไรฝั่ง server เลยจึงปล่อยผ่านไป

### 3.3 การถอดผู้ดูแลระบบสูงสุด — และทำไม guard กันถอดตัวเองถึงมีแค่ฝั่ง UI

ปุ่ม Remove ของแต่ละแถวเปิด `ConfirmDialog` และเมื่อยืนยันจะเรียก `DELETE /api-system/backstage/super-admins/:id` (`handleConfirmRemove`, บรรทัด 166-177) สำหรับแถวที่ตรงกับ `user_id` ของผู้ใช้ที่ล็อกอินอยู่เอง ปุ่ม Remove จะถูกแทนที่ทั้งหมดด้วยข้อความนิ่ง ๆ — *"You cannot revoke your own privileges"* — แทนที่จะแค่ปิดใช้งาน (`RosterRow`, บรรทัด 405-408) คอมเมนต์ของ component เองอธิบายว่าทำไมถึงซ่อนปุ่มไปเลยแทนที่จะปิดใช้งานเฉย ๆ: หน้านี้เข้าถึงได้เฉพาะ super admin เท่านั้น คนที่กำลังอ่านหน้านี้จึงมักจะ *อยู่ใน* รายชื่อนั้นเอง และปุ่ม Remove ที่ยังกดได้อยู่ข้างชื่อตัวเอง "ห่างจากการล็อกตัวเอง — และอาจรวมถึงทุกคน — ออกจากหน้านี้แค่คลิกเดียว" ข้อความแทนบอกเหตุผลตรง ๆ ปุ่มที่หายไปจึงอ่านเหมือนเป็นกฎ ไม่ใช่บั๊กของการเรนเดอร์ (บรรทัด 385-389)

**ตรวจสอบยืนยันแล้ว: guard นี้มีอยู่แค่ฝั่ง SPA เท่านั้น** `remove(id)` ของ `backstage_super_admin.service.ts` (บรรทัด 152-169) ค้นหาแถวด้วย `id` ของมันเองแล้ว soft-delete ให้ — ไม่เคยเทียบ `user_id` ของแถวนั้นกับ `user_id` ของผู้เรียกเลย และทั้ง gateway controller (`backstage-super-admins.controller.ts:148`) และ `BackstageSuperAdminGuard` ก็ไม่มีการตรวจแบบนี้เพิ่มเข้ามาเลย super admin ที่เรียก `DELETE /api-system/backstage/super-admins/:id` ตรง ๆ — ด้วย `id` ของแถวตัวเอง — ถอดสิทธิ์ตัวเองได้ ไม่มีอะไรฝั่ง server ห้ามไว้เลย การไม่มีขอบเขตล่างแบบเดียวกันนี้ยังหมายความว่าผู้เรียกที่มีสิทธิ์พอสามารถถอดทุกแถวที่เหลือได้ รวมถึงแถวสุดท้ายด้วย: service ไม่มีการตรวจ "ต้องเหลือ super admin ที่ active อย่างน้อยหนึ่งคน" อยู่เลยไม่ว่าใน `add`, `remove`, หรือ `list` ทั้งสองข้อนี้ถูกบันทึกเป็น edge case ใน §7 ไม่ใช่การกล่าวอ้างลอย ๆ — มันตามมาโดยตรงจากการอ่านเนื้อหาทั้งหมดของ `remove()` ซึ่งมีแค่การตรวจว่ามีแถวอยู่จริงหรือไม่ (`findFirst` ที่บรรทัด 155-157) ก่อน `update()` เท่านั้น

## 4. บทบาทและ Persona

| พื้นผิว | Guard | การตรวจ | หมายเหตุ |
|---|---|---|---|
| route `/backstage/super-admins` | `PrivateRoute` | `requireSuperAdmin` → `isSuperAdmin` | `../carmen-backstage/src/App.tsx:489-496`; `PrivateRoute.tsx:89-91` |
| รายการ "Super Admins" ใน sidebar | `buildBackstageNav` | `superAdminOnly: true` → `opts.isSuperAdmin` | `backstageNav.ts:51,119`; แถวนี้ไม่มีฟิลด์ `permission` เลย |
| `GET /api-system/backstage/super-admins` | `BackstageSuperAdminGuard` | ตรวจ `is_super_admin` สดใหม่ทุกครั้ง | `backstage-super-admins.controller.ts:78-98` |
| `POST /api-system/backstage/super-admins` | `BackstageSuperAdminGuard` | ตรวจ `is_super_admin` สดใหม่ทุกครั้ง | `backstage-super-admins.controller.ts:107-139`; 409 ถ้า active อยู่แล้ว |
| `DELETE /api-system/backstage/super-admins/:id` | `BackstageSuperAdminGuard` | ตรวจ `is_super_admin` สดใหม่ทุกครั้ง | `backstage-super-admins.controller.ts:148`; ไม่มีการตรวจว่าเป็นแถวตัวเอง ไม่มีการตรวจว่าเป็นแถวสุดท้าย (§3.3) |

ทุกแถวในตารางนี้คือข้อเท็จจริงเดียวกันที่พูดซ้ำ: **ไม่มี RBAC permission key เลยในโมดูลนี้ — ทุก gate คือ `isSuperAdmin` ที่ resolve สดใหม่จาก `tb_backstage_super_admin` ฝั่ง backend และแคชไว้แค่ใน session state ของ SPA เองฝั่ง frontend (§5.4)**

การถือแถวนี้ยังทำให้ผ่านเงื่อนไข authorization อื่นที่ไม่เกี่ยวกับหน้าจอนี้โดยตรงไปด้วยแบบเงียบ ๆ: `resolveProfileMemberships` ใน auth service แสดง business unit ที่ active ทุกตัวเป็นสมาชิกภาพระดับ admin ในโปรไฟล์ของ super admin เอง (`../carmen-turborepo-backend/apps/micro-business/src/authen/auth/auth.service.ts:2796-2824`); `TenantService.isSuperAdmin` ให้สิทธิ์ bypass การเชื่อมต่อฐานข้อมูลแบบ fail-closed (`apps/micro-business/src/tenant/tenant.service.ts:348-358,394-400`); `PermissionService.isSuperAdmin` ของ gateway เอง (`apps/backend-gateway/src/auth/services/permission.service.ts:373-384`) และ `ClusterAdminAuthzService.isBackstageSuperAdmin` ของ `micro-cluster` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:27-34`, ถูกเรียกใช้ที่จุดตรวจสิทธิ์ห้าจุดแยกกันในไฟล์เดียวกันนั้น) ต่างเขียน query `{ user_id, is_active: true, deleted_at: null }` แบบเดียวกันซ้ำเป็นอิสระต่อกัน แทนที่จะใช้ service ร่วมกัน — เพราะแต่ละตัวเป็นคนละ deployable ที่มี Prisma client ของตัวเอง ไม่ใช่เพราะการตรวจต่างกัน

## 5. Entity: `tb_backstage_super_admin`

`tb_backstage_super_admin` ถูกนิยามไว้ที่ `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma:1371` สร้างโดย migration `20260610073505_add_god_mode` และขยายเพิ่มโดย `20260612000000_add_doc_version` นอกเหนือจากคอลัมน์ audit มาตรฐาน ตารางนี้มีฟิลด์ที่มีความหมายจริงสามตัว — เล็กพอที่ตามกฎความลึกของแผนนี้จะบันทึกไว้ตรงนี้แทนที่จะแยกเป็นหน้า `data-model` ของตัวเอง

### 5.1 คอลัมน์

| คอลัมน์ | ชนิด | ความหมาย |
|---|---|---|
| `id` | `uuid`, PK, `gen_random_uuid()` | id ของแถวในบัญชีดำเอง — ตัวนี้ ไม่ใช่ `user_id` ที่ `DELETE .../:id` ใช้ |
| `user_id` | `uuid`, required | ผู้ใช้ระดับแพลตฟอร์มที่แถวนี้ระบุถึง ไม่ใช่ foreign key ตามธรรมเนียมของ schema นี้ (ไม่มีการประกาศ relation) — `list()` ทำการ join กับ `tb_user`/`tb_user_profile` ในโค้ดแอปพลิเคชันเอง (§3.1) ไม่ใช่ที่ระดับฐานข้อมูล |
| `is_active` | `boolean?`, default `true` | เขียนเป็น `true` ตอนสร้างแถว และไม่เคยถูกเขียนเป็น `false` โดยโค้ดจุดไหนเลยที่พบใน repository นี้ (ตรวจสอบยืนยันใน §5.3) — ทุกการอ่านที่มีผลจริงกรอง `is_active: true, deleted_at: null` คู่กันเสมอ ดังนั้นในทางปฏิบัติคอลัมน์นี้เป็นค่าคงที่เมื่อแถวถูกสร้างขึ้นแล้ว |
| `current_business_unit_id` | `uuid?` | business unit ที่ super admin คนนี้สลับไปใช้ล่าสุด (เพิ่ม 2026-10-26, `5d7bab295`) โปรไฟล์ของ super admin แสดงทุก BU ที่ active โดยไม่มีลิงก์สมาชิก (ลิงก์ที่ active จะกินที่นั่งของลูกค้า) ดังนั้น `setDefaultTenant` ใน micro-cluster จึงเก็บตัวเลือกไว้ที่นี่ (`business-unit.service.ts:1355-1366` โดยเขียน `updated_by_id`/`updated_at` ด้วย) และ `resolveProfileMemberships` อ่านมันเพื่อทำเครื่องหมาย `is_default` (`auth.service.ts:2796-2824`); รายการเรียงตามชื่อ BU |
| `doc_version`, `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | คอลัมน์ audit มาตรฐาน | `created_by_id`/`deleted_by_id` มีอยู่ใน schema แต่ไม่เคยถูกเขียนค่าให้ตารางนี้โดยเฉพาะ — ดูข้อสังเกตเรื่อง audit trail ใน §3.1 |

unique index ชื่อ `backstage_super_admin_user_deleted_at_u` บน `(user_id, deleted_at)` (`schema.prisma:1389`, สร้างโดย migration เดียวกัน) คือสิ่งที่ทำให้การตรวจแถวซ้ำของ `add()` มีความหมายจริงที่ระดับฐานข้อมูลด้วย ไม่ใช่แค่ในโค้ดแอปพลิเคชัน: แถว **active** ที่สองสำหรับ `user_id` เดียวกัน (`deleted_at IS NULL` ทั้งคู่) จะชนกับ index นี้ ถึงแม้การตรวจ `findFirst` ของ `add()` เอง (§5.2) จะเป็นตัวที่สร้าง 409 ให้ผู้ใช้เห็นก่อนที่จะไปถึงจุดนั้นอยู่แล้วก็ตาม

### 5.2 แถวหนึ่งเกิดขึ้นได้อย่างไร

มีทางเดียวที่แน่นอนสองทาง และมันไม่สมมาตรกันโดยเจตนา:

1. **Bootstrap เขียนตรงลงฐานข้อมูล** `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.backstage-super-admin.ts` อ่านตัวแปรสภาพแวดล้อม `SUPER_ADMIN_USER_ID` ตรวจว่ามีแถวที่ยังไม่ถูกลบอยู่แล้วหรือไม่ ถ้าไม่มีจะเรียก `tb_backstage_super_admin.create({ data: { user_id, is_active: true } })` ตรงเข้าฐานข้อมูลเลย — ข้าม `BackstageSuperAdminGuard`, gateway, และทุกช่วง RPC ไปทั้งหมด เส้นทางนี้จำเป็นต้องมี *เพราะ* `BackstageSuperAdminGuard` กั้น `POST /api-system/backstage/super-admins` ด้วยเงื่อนไขว่าผู้เรียกต้องเป็น super admin ที่ active อยู่แล้ว (§1) ดังนั้นก่อนที่จะมีแถวไหนอยู่เลย ไม่มี session ไหนเรียก API เพื่อสร้างแถวแรกได้ สคริปต์ seed คือทางออกเดียวจากวงจรปิดนี้
2. **ในแอป โดย super admin ที่มีอยู่แล้ว** `POST /api-system/backstage/super-admins` → `BackstageSuperAdminService.add(userId)` (`../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_super_admin/backstage_super_admin.service.ts:119-141`) — ตรวจว่ามีแถวที่ active และไม่ถูกลบอยู่แล้วสำหรับ `user_id` นั้นหรือไม่ (บรรทัด 122-124) คืนค่า `ALREADY_EXISTS` (HTTP 409, `packages/error-catalog/src/catalog.ts` → `std-response.ts:143`) ถ้าพบแถวอยู่แล้ว ไม่งั้นสร้างแถวใหม่ด้วย `is_active: true`

### 5.3 แถวหนึ่งถูกถอดสิทธิ์อย่างไร

**มันคือ soft delete ไม่ใช่การพลิกค่า `is_active` และนี่คือข้อเท็จจริงของทั้ง codebase ไม่ใช่ทางเลือกด้านการออกแบบที่เขียนไว้ในคอมเมนต์ที่ไหนเลย — มันตามมาจากการที่มีการเรียก `.update()` ที่เปลี่ยน *วงจรชีวิต* ของแถวอยู่แค่จุดเดียวในทั้ง backend (`.update()` ตัวที่สองใน `setDefaultTenant` ของ micro-cluster เขียนเฉพาะ `current_business_unit_id` กับคู่ audit)** `BackstageSuperAdminService.remove(id)` (service.ts:152-169) ค้นหาแถวด้วย `id` และถ้าพบจะเรียก:

```
await this.prismaSystem.tb_backstage_super_admin.update({
  where: { id },
  data: { deleted_at: new Date().toISOString() },
});
```

— ตั้งแค่ `deleted_at` เท่านั้น การค้นหาทั้ง repository สำหรับทุกจุดที่เขียนลง `tb_backstage_super_admin` พบว่านี่คือ `.update()` จุดเดียวที่แตะ `deleted_at` หรือ `is_active` ในทั้ง `../carmen-turborepo-backend` (`.update()` อีกตัว `setDefaultTenant` ตั้ง `current_business_unit_id`, `updated_by_id`, `updated_at`); `is_active` ถูกเขียนแค่สองครั้งในทั้ง backend ทั้งสองครั้งเป็นค่า `true` เท่ากัน ทั้งคู่เกิดตอนสร้างแถว (สองเส้นทางใน §5.2) ไม่มีจุดไหนในโค้ดตั้ง `is_active: false` เลย พูดให้เป็นรูปธรรม: **การถอดผู้ดูแลระบบสูงสุดผ่านหน้านี้ (หรือเรียก API ตรง) คือ soft delete ที่ยึดกับ `deleted_at` และคอลัมน์ `is_active` — แม้จะถูกกรองในทุกการอ่าน — ไม่เคยเปลี่ยนค่าจริงตลอดอายุของแถวนั้นเลย** แถวที่ขึ้น `Active` บนจอกับแถวที่ "ถูกถอด" ไปแล้วต่างกันแค่ว่า `deleted_at` เป็น null หรือไม่ ส่วน `is_active` อ่านได้เป็น `true` ทั้งคู่ คอมเมนต์ของ `list()` เอง (service.ts:69-73) บอกว่าผู้ใช้ที่ถูกลบหรือปิดใช้งานถูกจงใจไม่กรองออกจากทะเบียน — แถว super-admin ของ `tb_user` ที่ถูก soft-delete ไปแล้วยังมี god-mode อยู่ และต้องแสดงให้เห็นเพื่อให้ operator ถอดสิทธิ์ได้ — แต่นั่นคือคำกล่าวเรื่องแถว `tb_user` ที่ join มา ไม่ใช่เรื่องคอลัมน์ `is_active` ของตารางนี้เอง ซึ่งงานค้นคว้าของหน้านี้พบว่าในทางปฏิบัติเขียนแค่ครั้งเดียวแล้วไม่เปลี่ยนอีกเลย

### 5.4 ผลต่อ session ที่เปิดค้างอยู่แล้ว

การถอดสิทธิ์มีผลตั้งแต่คำขอถัดไปฝั่ง backend ทันที สำหรับทุกจุดที่ใช้ flag นี้ เพราะไม่มีจุดไหนแคชค่าไว้เลย: `BackstageSuperAdminGuard` (§1) และ `EffectivePermissionsService.resolve()` (`../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_permission/effective_permissions.service.ts:31-32`, `is_super_admin: isSuperAdmin` คำนวณโดยเรียก `this.superAdmin.isSuperAdmin(userId)` สดใหม่ทุกครั้ง) ต่างก็ query ฐานข้อมูลสด ๆ เช่นเดียวกับการตรวจซ้ำอิสระอีกสี่จุดที่ระบุไว้ใน §4 ไม่มี Redis หรือ cache ในหน่วยความจำอยู่เลยในสายการเรียกนี้ (ตรวจสอบโดยตรงแล้ว — ไม่มีการอ้างถึง cache/Redis อยู่ใน `apps/micro-business/src/authen/backstage_permission` หรือใน guard เอง)

ฝั่ง frontend เป็นอีกเรื่องหนึ่ง และนี่คือส่วนที่ควรทดสอบอย่างตั้งใจ: `AuthContext` ดึง `effectivePermissions` เพียงสามจุด — ครั้งหนึ่งตอน mount จาก token ที่มีอยู่แล้วใน `localStorage` (`AuthContext.tsx:87`), ครั้งหนึ่งตอน `login()` (`AuthContext.tsx:185`) และครั้งหนึ่งตอน `loginWithTokens()` (เส้นทาง Google sign-in, `AuthContext.tsx:289`) — และไม่เคย refetch หรือ poll อีกเลยนอกจากนั้น ดังนั้นแท็บเบราว์เซอร์ที่เปิดค้างและล็อกอินเป็น super admin ที่เพิ่งถูกถอดสิทธิ์ไป จะยังคงเรนเดอร์รายการ "Super Admins" ใน nav และ UI ที่กั้นด้วย `isSuperAdmin` ทุกจุดต่อไป จนกว่าแท็บนั้นจะรีโหลดหรือผู้ใช้ล็อกอินใหม่ — `isSuperAdmin` ใน React state ของแท็บที่ค้างอยู่นั้นยังคงเป็น `true` สิ่งที่แท็บที่ค้างอยู่นั้น **ทำไม่ได้** คือทำการกระทำที่มีสิทธิ์สูงให้สำเร็จจริง: คำขอถัดไปที่มันส่งไปยัง endpoint ใดก็ตามที่กั้นด้วย `BackstageSuperAdminGuard` หรือ `BackstagePermissionGuard` (รวมถึง `GET`/`POST`/`DELETE` ของโมดูลนี้เอง) จะถูกตรวจสดกับฐานข้อมูลและได้รับ 403 ที่ถูกต้องทันที ช่องว่างที่เกิดขึ้นตรงนี้เป็นแค่เรื่องภาพที่เห็น (nav/UI ที่ค้างอยู่) ไม่ใช่ช่องโหว่ authorization ที่ใช้งานได้จริง — สรุปจากการอ่านทั้งจุดที่ frontend ดึงข้อมูลและ guard ฝั่ง backend โดยตรง ไม่ใช่จากการสังเกตขณะระบบทำงานจริง

## 6. ชุดทดสอบ e2e

`../carmen-backstage-e2e/tests/super-admins/super-admin-manage.spec.ts` (spec 1 ไฟล์ 2 test: smoke test ว่าชื่อหน้า ปุ่มเปิด "Add Super Admin" และปุ่ม Remove อย่างน้อยหนึ่งปุ่มถูกเรนเดอร์ กับ test เพิ่ม-แล้ว-ถอดแบบไปกลับที่คืนสภาพเดิมเอง) แก้ไขล่าสุดที่ commit `538632d` (2026-09-18, "follow login and the super-admin picker to their current shapes") ส่วน page object `../carmen-backstage-e2e/pages/SuperAdminManagementPage.ts` แก้ไขล่าสุดที่ `7bc9dc9` (2026-10-26, การเปลี่ยน path เป็น `api-system/backstage`)

หน้านี้ฉบับก่อนหน้าบันทึกว่าชุดทดสอบเก่ากว่าการเขียนทะเบียนแบบการ์ดใหม่ (`28f92eb`, 2026-09-02, `#244`) และล้มที่ fixture **ข้อนั้นไม่เป็นจริงอีกแล้ว**: page object ตรงกับหน้าจอปัจจุบันแล้ว

- `userSelect` คือ `input[aria-label="Select user to add as super admin"]` (`SuperAdminManagementPage.ts:45`) ตรงกับ `<input>` ของ `UserPicker` (`UserPicker.tsx:158`) และเข้าถึงได้หลังจาก `openAddDialog()` คลิกปุ่มเปิด "Add Super Admin" เท่านั้น (`:49`, `:61-64`) เพราะ picker อยู่ใน `Dialog` (`SuperAdminManagement.tsx:301-363`)
- `addButton` จำกัดอยู่ภายใน dialog และ match `/Add Super Admin|Adding/` (`:48`) สอดคล้องกับข้อความปุ่ม submit ของ dialog (`SuperAdminManagement.tsx:359`)
- `goto()` รอ `h1` "Super Admins" และ network นิ่ง แทน `<select>` เดิม (`:52-58`)
- `adminRows` คือ `ul.divide-y > li` (`:67-69`) และ `removeButtons` คือ `button[aria-label^="Remove super admin "]` (`:72-74`) ตรงกับทะเบียน `<ul>`/`<li>` (`SuperAdminManagement.tsx:284,422`) และ `removeAria: 'Remove super admin {{name}}'` (`../carmen-backstage/src/i18n/en.ts:4117`)
- ข้อความ toast สำเร็จที่ page object รอ (`SuperAdminManagementPage.ts:146,169`) ตรงกับ `addSuccess`/`removeSuccess` ใน i18n ปัจจุบัน (`en.ts:4095,4097`)

**ข้อควรระวัง** ชุดทดสอบถูกอ่านเทียบกับ source ปัจจุบัน ไม่ได้ถูกรันสำหรับหน้านี้ จึงไม่ได้ตรวจยืนยันว่าผ่านจริงตอนรัน ข้อความ `annotation` step ใน spec ยังพูดถึง "select" อยู่บางจุด (เช่น "Assert the 'Select user to add as super admin' select is visible") แต่ตัว test ใช้ flow dialog/picker ความครอบคลุมแคบ: ไม่มีอะไรทดสอบ guard การถอดสิทธิ์ตัวเอง เส้นทาง 409 ซ้ำ หรือพฤติกรรมแท็บค้างใน §5.4 และชุดทดสอบจงใจไม่แตะผู้ใช้ที่ล็อกอิน ทุก claim ในหน้านี้ยังอ้างอิงจาก source ของ `../carmen-backstage`/`../carmen-turborepo-backend` โดยตรง ไม่ใช่จากชุดทดสอบนี้

## 7. กรณีพิเศษ

| สถานการณ์ | พฤติกรรม | แหล่งที่มา |
|---|---|---|
| การถอดสิทธิ์ตัวเองผ่าน UI | ปุ่ม Remove ถูกแทนที่ด้วยข้อความนิ่ง ๆ ไม่มีคำขอถูกส่งออกไปเลย | `SuperAdminManagement.tsx:405-408` |
| การถอดสิทธิ์ตัวเองผ่านการเรียก API ตรง | **ไม่ถูกป้องกัน** `remove(id)` ไม่มีการตรวจเทียบ `user_id` ของแถวกับผู้เรียกเองเลย | `backstage_super_admin.service.ts:152-169` (ยืนยันแล้ว: มีแค่การตรวจว่ามีแถวอยู่จริง ไม่มีการตรวจความเป็นเจ้าของ) |
| การถอดผู้ดูแลระบบสูงสุดที่เหลืออยู่คนสุดท้าย | **ไม่ถูกป้องกันเลยในทุกจุด** — `add`, `remove`, และ `list` ไม่มีการตรวจ "ต้องเหลืออย่างน้อยหนึ่งคน" เลย | อ่านเนื้อหาทั้งหมดของ `backstage_super_admin.service.ts` |
| เพิ่ม `user_id` ที่มีแถว active อยู่แล้ว | `409 ALREADY_EXISTS`; frontend ล้างค่าที่เลือกไว้ทิ้งแล้ว refetch เฉพาะ status code นี้ | `backstage_super_admin.service.ts:122-131`; `SuperAdminManagement.tsx:151-160` |
| แถว `tb_user` ที่เชื่อมกับ super admin ในรายชื่อถูก soft-delete หรือปิดใช้งาน | แถวยัง**คงแสดงอยู่โดยเจตนา** (ไม่ถูกกรองออก) เพื่อให้ยังถอดสิทธิ์ได้ แถวจะเรนเดอร์เป็นขีดกลางแทนชื่อ/อีเมลถ้าทั้งคู่ว่างเปล่า | `backstage_super_admin.service.ts:69-72,98-103`; `SuperAdminManagement.tsx:28-33,433-435` |
| ใครเป็นคนให้สิทธิ์ หลังเกิดเหตุการณ์ไปแล้ว | **ไม่ถูกบันทึกไว้** `created_by_id`/`deleted_by_id` ไม่เคยถูกเขียนสำหรับตารางนี้ ทะเบียนบอกได้แค่ *เมื่อไหร่* ไม่เคยบอก *ใคร* เป็นคนให้/ถอดสิทธิ์ | §3.1, §5.1, §5.3 |
| session ของ super admin เปิดค้างอยู่ในแท็บเบราว์เซอร์ตอนที่แถวของเขาถูกถอด | คำขอฝั่ง backend จากแท็บนั้นถูกตรวจสดและปฏิเสธถูกต้องตั้งแต่คำขอถัดไป; `effectivePermissions` ที่แคชไว้ในแท็บนั้น (ดึงแค่ตอนล็อกอิน/mount) ยังโชว์ UI ของ super admin ต่อไปจนกว่าจะรีโหลดหรือล็อกอินใหม่ | §5.4 |
| ผู้ดูแลระบบสูงสุดคนแรกสุด บน deployment ใหม่เอี่ยม | สร้างผ่าน UI หรือ API ไม่ได้เลย — ทุก endpoint ต้องการให้มี super admin ที่ active อยู่แล้ว ต้องสร้างผ่านสคริปต์ seed `SUPER_ADMIN_USER_ID` ที่เขียนตรงลงฐานข้อมูล | §5.2 |

## 8. คำแนะนำ

ควรมองหน้านี้เป็น break-glass control ไม่ใช่หน้าจอดูแลระบบตามปกติ: ทุกการให้สิทธิ์ที่นี่คือการ bypass RBAC เต็มรูปแบบ ทั้งฝั่ง frontend และ backend ยืนยันได้ตรงจุด short-circuit ที่อ้างอิงไว้ใน §2 เพราะการถอดสิทธิ์เป็น soft delete ที่ไม่มีการตรวจกันถอดตัวเองฝั่ง server และไม่มีการตรวจจำนวนขั้นต่ำ (§3.3, §7) การให้อีกคนช่วยตรวจสอบก่อนถอดสิทธิ์ใครสักคน — โดยเฉพาะตัวเอง หรือแถวสุดท้ายที่เหลืออยู่ — คือขั้นตอนที่หน้าจอนี้ไม่ได้บังคับให้ทำเอง ใครก็ตามที่จะทดสอบโมดูลนี้ด้วย session ที่มีสิทธิ์จำกัดควรรู้ว่าไม่มี session แบบสิทธิ์จำกัดให้ทดสอบสำหรับโมดูล*นี้*โดยเฉพาะเลย — มีแค่สองสถานะคือ "เป็น super admin" กับ "ไม่ใช่" และชุดทดสอบ e2e ที่มีอยู่ (§6) ครอบคลุมเฉพาะสถานะ super admin (ผู้ใช้ที่ล็อกอิน) และ flow เพิ่ม-ถอดแบบไปกลับ session ที่สิทธิ์ลดลงคือสิ่งเดียวที่มันครอบคลุมไม่ได้ การขยายชุดทดสอบควรตรวจ guard การถอดสิทธิ์ตัวเองและเส้นทาง 409 (ข้อควรระวังใน §6) เทียบกับ source ปัจจุบัน

## 9. โมดูลที่เกี่ยวข้อง

- [RBAC](/th/platform/rbac) — เป็นเจ้าของแกน permission-key/role-bundle ที่โมดูลนี้จงใจอยู่นอกเหนือไป §2 ด้านบนแสดงจุดที่ `is_super_admin` short-circuit ระบบนั้นทั้งสองฝั่งไว้ชัดเจน
- [User Platform](/th/platform/user-platform) — วิธีปกติที่ให้สิทธิ์ระดับแพลตฟอร์มแบบผูกกับ RBAC เทียบกับการ bypass แบบไม่มีเงื่อนไขของโมดูลนี้
- [Cluster Admin](/th/platform/cluster-admin) — อีกแกนหนึ่งที่ flag ตัวเดียวกันนี้ short-circuit เช่นกัน: `ClusterAdminAuthzService.isBackstageSuperAdmin` ถือว่า super admin ทุกคนเป็นผู้ดูแลของทุกคลัสเตอร์ (§4 ด้านบน)
- [Users](/th/platform/users) — เป็นเจ้าของแถว `tb_user`/`tb_user_profile` ที่ทะเบียนของโมดูลนี้ join มาแค่เพื่อแสดงผลเท่านั้น (§3.1)

## 10. แหล่งอ้างอิง

path ของ `../carmen-backstage` ทั้งหมดคือ HEAD `8405788f` (2026-10-27); path ของ `../carmen-turborepo-backend` ทั้งหมดคือ HEAD `c9d788829` (2026-10-27); `../carmen-backstage-e2e` คือ HEAD `9584887` (2026-10-27) โดย spec `super-admins` เองแก้ไขล่าสุดที่ `538632d` (2026-09-18)

- `src/pages/SuperAdminManagement.tsx` — หน้าจอทั้งหมด (อ่านครบทั้งไฟล์ 484 บรรทัด)
- `src/services/superAdminService.ts` — `list`/`add`/`remove`
- `src/types/index.ts:1129-1137` — interface `SuperAdmin` และคอมเมนต์เรื่อง audit shape
- `src/components/nav/backstageNav.ts:49-51,116-128` — รายการ nav, คอมเมนต์ไทยเรื่องเส้นคั่น, และตัวกรองของ `buildBackstageNav`
- `src/App.tsx:489-496` — route
- `src/components/PrivateRoute.tsx:39-108` — guard ฝั่ง frontend รวมถึงลำดับเทียบกับการตรวจ feature flag
- `src/context/AuthContext.tsx:87,185,289,342` — `isSuperAdmin`, `fetchEffectivePermissions`, และจุดที่แต่ละตัวถูกเรียก
- `src/utils/permissions.ts:50-78` — short-circuit สำหรับ super admin ของ `checkPermission` และ `checkBackstageAuthority`
- `src/components/UserPicker.tsx` — ตัวพิมพ์ค้นหาที่ dialog Add ใช้
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-super-admins/{backstage-super-admins.controller.ts,backstage-super-admins.service.ts}` — พื้นผิว HTTP และ RPC proxy ของมัน
- `../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-super-admin.guard.ts` — การตรวจ `is_super_admin` สดใหม่ไม่มี cache
- `../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-permission.guard.ts:108-110` — จุด bypass ของ super admin ที่ route ฝั่ง backend ที่กั้นด้วย RBAC ทุกเส้นใช้ร่วมกัน
- `../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_super_admin/{backstage_super_admin.service.ts,backstage_super_admin.controller.ts,backstage_super_admin.service.spec.ts}` — จุดเดียวที่อ่าน/เขียนตารางนี้ และชุดทดสอบของมันเองที่ยืนยันพฤติกรรม soft-delete/ไม่มีการตรวจกันถอดตัวเอง/ไม่มีการตรวจแถวสุดท้าย ตามที่บรรยายไว้ใน §3.3, §5.3, §7
- `../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_permission/effective_permissions.service.ts:31-32,77` — จุดที่ `is_super_admin` เข้าสู่ payload ของ effective permissions
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma:1371-1390` — model ของ `tb_backstage_super_admin`
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/migrations/{20260610073505_add_god_mode,20260612000000_add_doc_version}/migration.sql` — การสร้างตารางและคอลัมน์ `doc_version` ที่เพิ่มมาทีหลัง
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.backstage-super-admin.ts` — เส้นทาง bootstrap (§5.2)
- `../carmen-turborepo-backend/packages/error-catalog/src/catalog.ts` (`SUPER_ADMIN_NOT_FOUND`, 404) และ `../carmen-turborepo-backend/packages/nest-result/src/std-response.ts:143` (`ALREADY_EXISTS` → 409)
- `../carmen-turborepo-backend/apps/backend-gateway/src/common/enrichment/audit-shape.ts:1-7` และ `../carmen-turborepo-backend/apps/backend-gateway/src/common/enrichment/enrichment.service.ts` — กลไก `@EnrichAuditUsers()` ที่อ้างอิงในข้อสังเกตเรื่อง audit trail ของ §3.1
- จุดที่ใช้ `is_super_admin` ข้ามโมดูลตามที่อ้างอิงใน §4: `../carmen-turborepo-backend/apps/micro-business/src/authen/auth/auth.service.ts:2796-2824`, `../carmen-turborepo-backend/apps/micro-business/src/tenant/tenant.service.ts:348-358,394-400`, `../carmen-turborepo-backend/apps/backend-gateway/src/auth/services/permission.service.ts:373-384`, `../carmen-turborepo-backend/apps/micro-cluster/src/common/cluster-admin-authz.service.ts:27-34`
- `../carmen-backstage-e2e/tests/super-admins/super-admin-manage.spec.ts` และ `../carmen-backstage-e2e/pages/SuperAdminManagementPage.ts` — อ่านครบทั้งไฟล์สำหรับ §6

## 11. หน้าในโมดูลนี้

โมดูลนี้มีหน้าเดียว `tb_backstage_super_admin` ถูกบันทึกไว้ใน §5 ด้านบนแทนที่จะแยกเป็นหน้า `data-model` ต่างหาก และไม่มีหน้า `permissions` — เมทริกซ์ gate ห้าแถวใน §4 คือพื้นผิว permission ทั้งหมดที่มี และทุกแถวในนั้นก็ resolve ไปที่การตรวจ `isSuperAdmin` ตัวเดียวกัน ดูหน้า [ดัชนีหนังสือ Platform](/th/platform) สำหรับหน้าหลัก
