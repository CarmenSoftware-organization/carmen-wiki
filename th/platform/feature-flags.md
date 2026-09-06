---
title: แฟล็กฟีเจอร์ (Feature Flags)
description: หน้าเดียวที่ตั้งค่าการมองเห็นของทุกฟีเจอร์ (active/inactive/hide) ทั้งฝั่ง Platform admin และ Cluster-admin — ตั้งใจให้ไม่มี feature key ของตัวเอง เพราะสวิตช์ที่ปิดตัวเองได้จะเปิดกลับไม่ได้อีกจากหน้าจอ
published: true
date: '2026-09-06T23:30:00.000Z'
tags: book/platform, feature-flags
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แฟล็กฟีเจอร์ (Feature Flags)

โมดูล **Feature Flags** คือหน้าเดียว `FeatureFlagManagement` ที่ `/platform/features` ซึ่งตั้งสวิตช์การมองเห็นสามสถานะ — `active`, `inactive`, หรือ `hide` — ให้กับทุกแถวเมนูที่ถูก gate ไว้ ทั้งใน sidebar ของ Platform admin และ sidebar ของ Cluster-admin ที่แยกต่างหาก มันคือกลไกที่ทุกโมดูลอื่นในวิกินี้ระบุ feature key ไว้ และเป็นโมดูลเดียวที่แถวเมนูของตัวเองตั้งใจไม่มี feature key เลย (§2) ไม่มีหน้าจอไหนในผลิตภัณฑ์คล้ายหน้านี้: ไม่มีตาราง ไม่มีการค้นหา ไม่มีการแบ่งหน้า และไม่ได้แก้ไขอะไรที่คนสร้างขึ้น — มันแก้ไขแค็ตตาล็อกคงที่ที่ฝังไว้ในตัว build ของ frontend (§3.3)

> **At a Glance**
> **Component:** `FeatureFlagManagement` &nbsp;·&nbsp; **Route:** `/platform/features` &nbsp;·&nbsp; **Nav:** `permission: 'feature_flag.manage'` **ไม่มี `feature` key** — ตั้งใจไม่ gate ด้วย feature flag (§2) &nbsp;·&nbsp; **ด่านอ่าน:** ไม่มี — `GET` เปิดให้ทุกคนที่ล็อกอินแล้ว (§4.2) &nbsp;·&nbsp; **ด่านเขียน:** `feature_flag.manage` เท่านั้น มีเฉพาะ role bundle `Platform Admin` ในบรรดา role แพลตฟอร์มที่ seed ไว้ทั้งสี่ (§4.1) &nbsp;·&nbsp; **ขอบเขต:** flag key ทั้งหมด 28 ตัว — 24 ตัวสำหรับ Platform console และ 4 ตัวสำหรับ Cluster-admin console ที่แยกต่างหาก (§3.3) &nbsp;·&nbsp; **ชุดทดสอบ e2e:** **ไม่มี** — `../carmen-platform-e2e/tests/` ไม่มีโฟลเดอร์ `feature-flags` เลย ทุกข้อความในหน้านี้มาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` โดยตรง (§4.4) &nbsp;·&nbsp; **หน้าย่อย:** 1

## 1. ภาพรวม

`FeatureFlagManagement.tsx` ดึงแมปสถานะฟีเจอร์ทั้งใบครั้งเดียวผ่าน `FeatureFlagContext` (หน้า data model §5) แล้ว render เป็นการ์ดเรียงต่อกัน — หนึ่งการ์ดต่อหนึ่ง `groupKey` เรียงตามลำดับเดียวกับที่ sidebar จัดกลุ่มเมนูของตัวเอง — พร้อม toggle สามสถานะ (`FeatureStateToggle`) ต่อหนึ่งฟีเจอร์ doc-comment ของหน้าเองระบุประเภทของมันตรง ๆ ว่า "a Config page, not a Management one: the feature set comes from an in-code catalog" (`FeatureFlagManagement.tsx:25-27`) — ยืนยันแล้วโดยอ่าน component ทั้งไฟล์: ไม่มี endpoint แสดงรายการที่กรองได้ ไม่มีการสร้าง/ลบฟีเจอร์เอง มีแค่การ save แมปทั้งใบ (หน้า data model §4) การ์ดสำหรับคีย์ที่แค็ตตาล็อกของ build ปัจจุบันไม่รู้จัก ("Unknown keys") จะปรากฏใต้การ์ดปกติเมื่อแมปที่บันทึกไว้มีคีย์แบบนั้น พร้อมปุ่ม Remove (หน้า data model §6)

## 2. บริบททางธุรกิจ

โมดูลนี้มีอยู่เพราะทุกหน้าจอที่ถูก gate ในผลิตภัณฑ์ต้องการสวิตช์ที่ operator คุมได้เองโดยไม่ต้อง redeploy — `hide` ทำให้ฟีเจอร์ที่ยังไม่เสร็จหรือพังหายไปจากเมนูทั้งหมด และ `inactive` ทำให้มันยังมองเห็นได้แบบ "coming soon" โดยเข้าถึงไม่ได้ ทั้งสองสถานะอ่านจากแถว `tb_platform_config` แถวเดียวกับที่ config key อื่นทุกตัวใช้ร่วมกัน (หน้า data model §2)

**ทำไมแถวของหน้านี้เองถึงไม่มี `feature` key: ไม่มีคอมเมนต์ไหนถูกอ้างเป็นข้อเท็จจริงโดยไม่ตรวจกับโค้ดรอบ ๆ มันก่อน** `platformNav.ts` ระบุเหตุผลไว้เหนือแถวนั้นตรง ๆ ว่า "ไม่มี feature โดยเจตนา — สวิตช์ที่ปิดตัวเองได้จะเปิดกลับไม่ได้อีกจากหน้าจอ" (`platformNav.ts:47-48`) และตัวแถวเองก็ยืนยันเช่นนั้น — มันเป็น entry **เดียว** ในอาร์เรย์ `ALL_PLATFORM_NAV_ITEMS` ทั้ง 26 แถวที่มี `permission` แต่ไม่มี property `feature` เลยจริง ๆ (ยืนยันโดยอ่านทุกแถวในไฟล์ ไม่ใช่เชื่อคอมเมนต์เฉย ๆ) คำอธิบายที่ถูกต้องสำหรับแถวนี้คือ **"ไม่มี feature key โดยเจตนา — gate ด้วย `feature_flag.manage`"** ไม่ใช่ "ไม่มีการตรวจสิทธิ์" หรือ "unguarded" — ด่านสิทธิ์นั้นมีจริงและถูกบังคับใช้แยกต่างหากฝั่ง server (§4.2)

คอมเมนต์ที่กว้างกว่าอีกอันใน `featureFlags.ts` ระบุ route แปดตัวที่ตั้งใจไม่มี feature key เลย: `/dashboard`, `/platform/features`, `/profile`, `/changelog`, `/login`, `/`, `/403`, `/404` (บรรทัด 39-41) การอ่าน `App.tsx` ยืนยันทุกตัว: `/`, `/login`, และ `/changelog` ไม่ได้ห่อด้วย `PrivateRoute` เลย; `/dashboard`, `/profile`, และ `/403` ห่อด้วย `<PrivateRoute>` เปล่า ๆ ไม่มี prop `feature`; และ `/404` คือ route catch-all ที่ไม่ต้องล็อกอิน ตัวคอมเมนต์เองก็แยกเหตุผลออกเป็นสองแบบอยู่แล้ว ไม่ได้ปฏิบัติต่อทั้งแปดตัวเหมือนกันหมด — "closing any of them would lock the app **or the switch itself**" — และมีแค่ครึ่งหลังของประโยคนี้เท่านั้นที่ใช้กับหน้านี้: อีกเจ็ดตัวไม่ถูก gate เพราะเป็นปลายทางที่ไม่ต้องล็อกอิน เป็นของสากล หรือเป็นหน้า error ที่การ gate จะไม่มีความหมาย ไม่ใช่เพราะการ gate มันจะสร้างการล็อกตัวเองแบบเดียวกับที่จะเกิดถ้า gate Feature Flags

## 3. แนวคิดสำคัญ

### 3.1 สามสถานะ สามผลลัพธ์ที่ต่างกัน — ยืนยันกับตัว filter จริง ไม่ใช่คอมเมนต์ข้าง ๆ มัน

filter ของ `buildPlatformNav()` เอง (`platformNav.ts:91-98`) คือความจริงพื้นฐานว่าแต่ละสถานะทำอะไรกับแถวเมนู อ่านตรงจากโค้ด ไม่ใช่จากคอมเมนต์ข้าง ๆ:

| สถานะ | ผลกับแถว sidebar | ผลกับ route |
| --- | --- | --- |
| `active` | render ตามปกติ | render หน้าปกติ |
| `inactive` | **อยู่ตำแหน่งเดิม** render เป็น `comingSoon: true` — แถวที่กดไม่ได้ `aria-disabled` ไม่ใช่แถวที่ซ่อน (หน้า data model §5) | `PrivateRoute` render `<ComingSoon />` ที่ตำแหน่งเดิม ไม่ redirect ไม่มีรหัสสถานะ HTTP (หน้า data model §5) |
| `hide` | ถูกตัดออกจากอาร์เรย์ที่กรองแล้วทั้งหมด | `PrivateRoute` render `<NotFound />` ที่ตำแหน่งเดิม — แยกไม่ออกจาก URL ที่ไม่เคยมีอยู่ |

คีย์ที่ไม่เคยถูกบันทึกสถานะเลย — รวมถึงทุกคีย์บน deployment ที่ไม่เคยเปิดหน้านี้แล้วกด save — ถือเป็น `active` (fallback ของคีย์ที่ไม่รู้จักใน `flagOf()`, หน้า data model §5) ไม่ต้องมีอะไรถูกตั้งเป็น `active` อย่างชัดเจนก็ได้

### 3.2 ทำไม `inactive` ไม่เคยเปลี่ยนตำแหน่งของแถว — ยืนยันกับ `Sidebar.tsx` เอง ไม่ใช่แค่ยกมาจากไฟล์ nav

คอมเมนต์ข้าง filter ของ `buildPlatformNav()` ระบุเหตุผลที่ `inactive` (ต่างจาก `hide`) ไม่เคยลบแถวออก: "Sidebar จัดกลุ่มจากแถวที่ groupKey ซ้ำกันติด ๆ การตัดรายการกลางกลุ่มออกจึงทำให้กลุ่มเดียวแตกเป็นสองหัวข้อได้" (`platformNav.ts:95-97`) นี่ไม่ใช่แค่สิ่งที่ไฟล์ nav อ้างเฉย ๆ — การอ่านฟังก์ชัน `navGroups` ของ `Sidebar.tsx` เองยืนยันว่าพฤติกรรม render จริงตรงกัน: มันไล่อาร์เรย์ (ที่ผ่านการกรอง `hide` มาแล้ว) แล้วเริ่มหัวข้อใหม่ก็ต่อเมื่อ `groupKey` ของ item ปัจจุบันต่างจาก item ก่อนหน้า ตรงกับอัลกอริทึมที่คอมเมนต์อธิบายเป๊ะ (`Sidebar.tsx:105-114`) คอมเมนต์แบบ inline หลายจุดใน `platformNav.ts` เองมีไว้เพื่อรักษากฎนี้ด้วยมือเท่านั้น — เช่นหมายเหตุว่าสองแถวของ Database "ต้องอยู่ท้ายสุด" เพราะการดึงออกมากลางกลุ่มเคยทำให้หัวข้อ Platform แตกเป็นสองครั้งหนึ่งมาแล้ว (`platformNav.ts:50-52`) — เป็นความเสี่ยงด้านการดูแลที่กฎ contiguity นี้สร้างขึ้นเอง ไม่ใช่สิ่งที่ `buildPlatformNav()` ป้องกันให้อัตโนมัติ

### 3.3 รายการ flag key ทั้งหมด — ทั้งสอง console

ทั้ง 28 คีย์ที่ `FEATURE_CATALOG` นิยามไว้ เมนูที่แต่ละตัวควบคุม และ console ที่มันสังกัด (รายละเอียดระดับฟิลด์เต็ม ๆ — `groupKey`, สถานะ default — อยู่ที่[หน้า data model](/th/platform/feature-flags/data-model) §3):

**Platform console (24 คีย์)** — `clusters`, `business_units`, `tenant_migrations`, `tenant_imports`, `users` (Organization); `licenses`, `license_feature_groups`, `license_features` (License Management); `report_templates`, `report_form_groups`, `news`, `broadcasts` (Content); `usage_analytics`, `activity_events` (Analytics); `cronjobs` (Scheduling); `applications`, `email_settings`, `platform_config`, `platform_roles`, `super_admins`, `user_platform` (Platform); `platform_migrations`, `sql_workbench`, `database_pools` (Database)

**Cluster-admin console (4 คีย์ คนละ namespace)** — `cluster_admin_cluster` (Cluster), `cluster_admin_business_units` (Business Units), `cluster_admin_licenses` (Licenses), `cluster_admin_users` (Users) คอมเมนต์ของ `clusterAdminNav.ts` เองระบุว่าคีย์ฝั่งนี้แยกจากฝั่ง platform โดยเจตนา "ที่ชื่อเมนูซ้ำกัน" (บรรทัด 12) — สามในสี่ป้ายชื่อ (Business Units, Licenses, Users) เป็นสตริงเดียวกันเป๊ะกับแถวฝั่ง platform แต่การตั้งคีย์ฝั่ง platform เป็น `hide` ไม่มีผลต่อแถว cluster-admin ที่ชื่อเดียวกันเลย และกลับกันก็เช่นกัน ผู้ที่คิดว่าคีย์เดียวคุมทั้งสอง console จะเข้าใจผิด

**ไม่อยู่ในรายการนี้:** แถว Feature Flags เองไม่มี feature key (§2) เช่นเดียวกับ Dashboard, Landing, Login, Changelog หรือ route หน้า error เพราะไม่มีตัวไหนเป็น *แถวเมนูที่ถูก gate* ตั้งแต่แรก

## 4. บทบาทและสิทธิ์

### 4.1 ด่านฝั่ง frontend และระดับ role

| ส่วนที่เกี่ยวข้อง | ด่าน | ที่มา |
| --- | --- | --- |
| รายการ sidebar "Feature Flags", route `/platform/features` | `permission: 'feature_flag.manage'` — **ไม่มี `feature` key** | `platformNav.ts:49`; `App.tsx:555-561` (`<PrivateRoute requiredPermission="feature_flag.manage">` ไม่มี prop `feature`) |
| toggle ทุกตัวในหน้า | ไม่มีด่าน UI แยกอีกนอกจากการเข้าหน้านี้ได้ — session ที่เปิดหน้าได้ก็สลับ toggle ไหนก็ได้ | `FeatureFlagManagement.tsx` (ไม่มีการเรียก `hasPermission` เลยในตัว component) |

`feature_flag.manage` ถูก seed ไว้ใน role bundle เดียวจากทั้งสี่ role ของแพลตฟอร์ม (`seed.platform-role-permission.data.ts:11-52`): `Platform Admin` (`feature_flag.*` บรรทัด 33) `Support Manager`, `Support Staff`, และ `Security Officer` ไม่มีคีย์นี้หรือ `feature_flag.*` ตัวไหนเลย — ยืนยันโดยอ่านอาร์เรย์ role ทั้งสี่แบบเต็ม ไม่ใช่แค่ตัวที่มี คำอธิบายของ permission catalog เองระบุว่า resource นี้ถูกแยกออกจาก `platform_config` โดยเจตนา แทนที่จะเป็น action ของมัน "so whoever gates unfinished features is not necessarily whoever edits invitation links or SMTP routing" (`seed.platform-permission.data.ts`, คอมเมนต์เหนือ entry `feature_flag.manage`)

### 4.2 การบังคับใช้ฝั่ง backend

`../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts`, HEAD `937cf5ac4` (2026-09-06):

| Route | Guard | ที่มา |
| --- | --- | --- |
| `GET /api-system/platform/feature-flags` | `KeycloakGuard` + `AppIdGuard('feature-flags.get')` **เท่านั้น** — ไม่มี RBAC permission แบบใดเลย | บรรทัด 65-108 |
| `PUT /api-system/platform/feature-flags` | `KeycloakGuard` + `AppIdGuard('feature-flags.update')` + `PlatformPermissionGuard` + `@RequirePlatformPermission('feature_flag.manage')` | บรรทัด 65, 118-120 |

การที่ `GET` เปิดให้ทุกคนที่ยืนยันตัวตนแล้ว ไม่ใช่แค่ Platform Admin เป็นสิ่งที่ Swagger description ของ controller เองระบุว่าตั้งใจ: "the map decides what the UI renders, so a user who cannot read it sees the frontend built-in defaults instead" (`feature_flags.controller.ts:88-89`) การอ่าน `PlatformPermissionGuard.canActivate()` แบบเต็มยืนยันว่า super-admin short-circuit ใช้ที่นี่เหมือนกับทุก route ที่มี `@RequirePlatformPermission`: `is_super_admin === true` คืน `true` ก่อนที่จะตรวจ `feature_flag.manage` เลยด้วยซ้ำ — super admin เขียน endpoint นี้ได้แม้ไม่มี `feature_flag.*` ของตัวเอง

### 4.3 แถวของโมดูลนี้เองเป็น UI-only — ข้อเท็จจริงด้านความปลอดภัย ไม่ใช่การอนุมาน

มีแหล่งข้อมูลอิสระสามที่ระบุสิ่งเดียวกัน จึงรายงานเป็นข้อเท็จจริง ไม่ใช่การอนุมานจากการอ่านกลไกเดียวแล้วขยายความเอง:

1. **คำอธิบายของ permission catalog เอง** ที่ seed ไว้คู่กับทุก permission key อื่น: "Frontend visibility only — it does NOT block the corresponding backend endpoints" (`seed.platform-permission.data.ts`, entry `feature_flag.manage`)
2. **subtitle ของหน้าเอง ที่แสดงให้ admin ทุกคนที่เปิดหน้านี้เห็น**: "Choose what each feature shows on screen. Frontend visibility only — it does not close the matching API" (`en.ts:967-968`, `pages.featureFlags.subtitle`)
3. **คอมเมนต์ออกแบบของ `ComingSoon.tsx` เอง** ว่าการตั้ง flag เป็น `inactive` ทำอะไรจริง ๆ ในระดับ route: ไม่มีรหัสสถานะ HTTP "because the server refused nothing — the UI did" (หน้า data model §5)

ผลจริงสำหรับผู้ทดสอบ: การตั้ง route ให้เป็น `hide` หรือ `inactive` เปลี่ยนแค่สิ่งที่ SPA render สำหรับ path นั้น ไม่มีผลใด ๆ ต่อว่า backend endpoint ที่เกี่ยวข้องจะรับ request ตรงหรือไม่ — เรื่องนั้นถูกตัดสินทั้งหมดโดย RBAC permission ที่ endpoint นั้นเองต้องการ (บันทึกไว้ในหน้าของโมดูลนั้นเอง) ซึ่งยังคงใช้ได้ไม่ว่า frontend จะแสดงรายการเมนูสำหรับมันอยู่หรือไม่

### 4.4 ชุดทดสอบ e2e: ไม่มี

`../carmen-platform-e2e/tests/` ไม่มีโฟลเดอร์ `feature-flags` (หรือชื่อใกล้เคียง) เลย — ยืนยันโดย list โครงสร้าง `tests/` ของ repository นั้นตรง ๆ ทุกข้อความเชิงพฤติกรรมในหน้านี้และหน้า data model ย่อยของมันมาจากการอ่าน implementation ของ `../carmen-platform` และ `../carmen-turborepo-backend-v2` ไม่ใช่จาก spec ที่รันได้จริง

## 5. โมดูลที่เกี่ยวข้อง

- [Platform Config](/th/platform/platform-config) และ[data model](/th/platform/platform-config/data-model) ของมัน — ตาราง `tb_platform_config` ที่ใช้ร่วมกันซึ่งแถวของคีย์นี้อาศัยอยู่ รวมถึงกลไกฝั่งเขียนแบบทั่วไป (การตรวจสอบ, คอลัมน์ `doc_version` ที่ไม่ถูกบังคับใช้, การแข่งกันของแถวซ้ำที่ยังไม่ถูกลบ) ที่โมดูลนี้สืบทอดมาโดยไม่เปลี่ยนแปลง
- [Platform RBAC](/th/platform/rbac) — permission catalog ที่ `feature_flag.manage` และ role bundle ที่ seed ไว้ทั้งสี่ตัวใน §4.1 ถูกนิยามและดูได้แบบเต็ม
- ทุกโมดูลอื่นในวิกินี้ — แต่ละหน้าระบุ feature key ที่ gate แถวเมนูของตัวเอง หน้านี้คือจุดที่ผู้อ่านจะได้เรียนรู้ว่าการตั้งคีย์นั้นเป็น `active`/`inactive`/`hide` ทำอะไรจริง ๆ

## 6. แหล่งอ้างอิง

ทุก path ด้านล่างเป็น `../carmen-platform` (Platform admin SPA, HEAD `157a65e`, 2026-09-04) เว้นแต่จะขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (backend monorepo, HEAD `937cf5ac4`, 2026-09-06)

- `../carmen-platform/src/pages/FeatureFlagManagement.tsx` — ตัว component และ doc-comment "Config page, not Management" ของมันเอง (§1)
- `../carmen-platform/src/constants/featureFlags.ts` — `FEATURE_CATALOG`, คอมเมนต์เรื่อง route ที่ไม่ gate (§2), คอมเมนต์กฎ contiguity
- `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 9-56, 47-49, 91-103) และ `src/components/nav/clusterAdminNav.ts` (บรรทัด 10-26) — แถว nav เอง, `buildPlatformNav()`/`buildClusterAdminNav()` (§2, §3)
- `../carmen-platform/src/components/Sidebar.tsx` (บรรทัด 105-114) — การจัดกลุ่มแบบ consecutive-run ที่ข้อความเรื่อง contiguity ของหน้านี้ถูกตรวจสอบด้วย (§3.2)
- `../carmen-platform/src/App.tsx` (บรรทัด 99-106, 555-561, 563-575, 606) — ทุก route ที่อ้างถึงใน §2 และ §4.1
- `../carmen-platform/src/pages/ComingSoon.tsx` — หมายเหตุออกแบบเรื่องไม่มีรหัสสถานะ (§4.3)
- `../carmen-platform/src/i18n/en.ts` (บรรทัด 15-43, 965-985) — ป้ายชื่อ nav และข้อความของหน้าเอง (§4.3)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts` — คู่ `GET`/`PUT` เฉพาะทางและ guard ของมัน (§4.2)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts` — super-admin short-circuit ที่ทุก route ซึ่งมี `@RequirePlatformPermission` ใช้ร่วมกัน (§4.2)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` และ `seed.platform-role-permission.data.ts` — entry catalog ของ `feature_flag.manage` และการมอบให้ role เดียว (§4.1, §4.3)
- `../carmen-platform-e2e/tests/` — list ตรง ๆ เพื่อยืนยันว่าไม่มีชุดทดสอบ `feature-flags` (§4.4)

## 7. หน้าย่อยของโมดูลนี้

- [Data Model](/th/platform/feature-flags/data-model) — รูปร่างที่แน่นอนของแถว `feature_flags`, ตาราง `FEATURE_CATALOG` เต็มพร้อม `groupKey` และค่า default ของทุกคีย์, write path ที่ทำได้ผ่าน PUT เท่านั้น, และรายละเอียดว่าแต่ละ consumer ทำอะไรกับแต่ละสถานะ
