---
title: แฟล็กฟีเจอร์ — โมเดลข้อมูล (Data Model)
description: FEATURE_CATALOG (แหล่งความจริงฝั่ง frontend ทั้ง 28 รายการว่ามีอะไร gate ได้บ้าง), แถว feature_flags ที่มันถูกวางทับอยู่ในตาราง tb_platform_config ที่ใช้ร่วมกัน, และคู่ REST เฉพาะทาง — PUT เท่านั้น ไม่มี PATCH — ที่อ่านและเขียนมัน
published: true
date: '2026-09-06T23:30:00.000Z'
tags: book/platform, feature-flags, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แฟล็กฟีเจอร์ — โมเดลข้อมูล (Data Model)

> **At a Glance**
> **ที่เก็บข้อมูล:** หนึ่งแถวของตาราง `tb_platform_config` ที่ใช้ร่วมกัน `key = 'feature_flags'` — ตัว entity เองบันทึกไว้แบบเต็มที่[Platform Config](/th/platform/platform-config/data-model) §2 หน้านี้ครอบคลุมเฉพาะส่วนที่เจาะจงกับคีย์นี้ &nbsp;·&nbsp; **รูปร่าง:** `Record<string, 'active' | 'inactive' | 'hide'>` แบบฟรีฟอร์ม (`FeatureFlagsConfigSchema` เป็น Zod `record` ไม่ใช่ object) — คีย์เดียวใน registry ที่ไม่มีรายชื่อฟิลด์ตายตัว และนั่นคือเหตุผลว่าทำไมมันเป็นคีย์เดียวที่ `PATCH` ไม่ได้เลย (§4) &nbsp;·&nbsp; **แหล่งความจริงว่า *มีอะไรบ้าง*:** `FEATURE_CATALOG` ฝั่ง frontend (`src/constants/featureFlags.ts`) 28 รายการ — backend เก็บแค่สถานะ ไม่เคยตรวจชื่อคีย์กับแค็ตตาล็อกใดเลย &nbsp;·&nbsp; **เข้าถึงได้ผ่านคู่ของตัวเองเท่านั้น:** `GET`/`PUT /api-system/platform/feature-flags` ไม่ใช่ผ่าน `/api-system/platform/configs` ทั่วไป (§4)

> **Source of truth:** แค็ตตาล็อกฝั่ง frontend ที่นิยามว่ามีอะไร gate ได้บ้าง และ schema/controller ฝั่ง backend ที่เก็บและให้บริการมัน อ่านสิ่งเหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-platform/src/constants/featureFlags.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts`
> - `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts`
>
> ยืนยันกับ `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06) และ `carmen-platform` HEAD `157a65e` (2026-09-04)

## 1. ภาพรวม

คีย์นี้มีสองสิ่งรองรับอยู่ เป็นของคนละฝั่งของ stack **รูปร่าง** ของค่าที่ใช้ได้ — แมปจากคีย์สตริงไปยังหนึ่งในสามสถานะ — นิยามไว้ที่เดียว ใน `FeatureFlagsConfigSchema` ฝั่ง backend (§2) และถูกบังคับใช้ในทุกการเขียน **สมาชิก** ของแมปนั้น — คีย์ไหนมีความหมายจริงกับ UI — นิยามไว้ที่เดียว ใน `FEATURE_CATALOG` ฝั่ง frontend (§3) และ backend ไม่เคยตรวจสอบเลย doc-comment ของ schema เองระบุ trade-off นี้ตรง ๆ ว่า "a deliberately free-form map: the feature list lives in the frontend, so adding one is not a backend deploy. The trade-off is that no key-name validation can happen here" (`platform-config.schema.ts`, คอมเมนต์เหนือ `FeatureFlagsConfigSchema`) คีย์ที่ backend ไม่เคยรู้จักกับคีย์ที่แค็ตตาล็อกฝั่ง frontend เอาออกไปแล้ว หน้าตาเหมือนกันเป๊ะสำหรับ backend — ทั้งคู่เป็นแค่ entry ใน JSON object — ซึ่งเป็นเงื่อนไขเดียวกับที่ UI คีย์กำพร้าในหน้า landing (§5) มีไว้เพื่อแสดงให้คนเห็น

## 2. Entity: แถว `feature_flags` บน `tb_platform_config`

ตัว `tb_platform_config` เอง — ทุกคอลัมน์, unique index บน `key`+`deleted_at` ที่ไม่บังคับใช้จริง, และการแข่งกันของแถวซ้ำที่ยังไม่ถูกลบซึ่ง index นั้นไม่กัน — บันทึกไว้แบบเต็มที่[Platform Config — Data Model](/th/platform/platform-config/data-model) §2 ด้านล่างนี้ไม่พูดซ้ำ สิ่งที่เจาะจงกับคีย์นี้:

- **`key = 'feature_flags'`** หนึ่งแถวที่ยังไม่ถูกลบ (หรือศูนย์แถว ก่อนการ save ครั้งแรก)
- **`value`** คือตัวแมปเอง — `Record<string, 'active' | 'inactive' | 'hide'>` — ไม่ใช่ object รูปร่างตายตัวแบบที่ registry key อื่นทุกตัวเป็น (`invitation`, `license` ฯลฯ ทุกตัวมีรายชื่อฟิลด์ที่กำหนดไว้ ตัวนี้ไม่มี)
- **default ของ registry คือ `{}`** (`platform-config.schema.ts`, entry `feature_flags`, `default: {}`) — แมปว่างเปล่า ไม่ใช่แมปที่เติมทุกคีย์ในแค็ตตาล็อกเป็น `active` ไว้ล่วงหน้า deployment ที่ไม่เคย save เลยจึง**ไม่มีแถวเลย** และทุก consumer จะ fallback ไปใช้ default ในโค้ดของตัวเอง (§5) แทนที่จะอ่านอะไรจากตารางนี้เลย
- **สัญญาการตั้งชื่อร่วมกันของสองโปรเซส** คอมเมนต์เหนือ controller เฉพาะทางระบุว่าแถวนี้คือ "the same row `PLATFORM_CONFIG_REGISTRY` of micro-cluster calls `feature_flags`. Two processes, one row" (`feature_flags.controller.ts:29-31`) — ค่าคงที่ `FEATURE_FLAGS_KEY = 'feature_flags'` ใน backend-gateway กับคีย์ registry ชื่อเดียวกันใน micro-cluster เป็น string literal อิสระสองตัวในสอง service ที่ต้องคอยรักษาให้ตรงกันด้วยมือ ไม่มีอะไรบังคับให้มันตรงกันนอกจากคอมเมนต์นี้

## 3. `FEATURE_CATALOG` — ทุกคีย์ แบบเต็ม

นิยามไว้ที่เดียว `../carmen-platform/src/constants/featureFlags.ts:47-84` มี 28 รายการ — ยืนยันโดยนับจากอาร์เรย์จริง และตรวจไขว้กับ union ของทุกค่า `feature:` ที่ใช้ทั้งใน `platformNav.ts` (24 คีย์) และ `clusterAdminNav.ts` (4 คีย์): ทั้งสองชุดตรงกันเป๊ะ จึงไม่มีอะไรในไฟล์ nav ทั้งสองที่อ้างคีย์ที่แค็ตตาล็อกไม่นิยาม และแค็ตตาล็อกก็ไม่มีคีย์ที่ไม่มีแถวเมนูจริงใช้เลย ทั้ง 28 คีย์ default เป็น `active` — คอมเมนต์ของไฟล์เองระบุว่านี่เป็นความตั้งใจ: "a deploy must never hide anything on its own" (บรรทัด 36-37)

| # | คีย์ | ป้ายชื่อเมนู | Console | `groupKey` |
| - | --- | --- | --- | --- |
| 1 | `clusters` | Clusters | Platform | `navGroup.organization` |
| 2 | `business_units` | Business Units | Platform | `navGroup.organization` |
| 3 | `tenant_migrations` | Tenant Migrations | Platform | `navGroup.organization` |
| 4 | `tenant_imports` | Data Import | Platform | `navGroup.organization` |
| 5 | `users` | Users | Platform | `navGroup.organization` |
| 6 | `licenses` | Licenses | Platform | `navGroup.licenseManagement` |
| 7 | `license_feature_groups` | License Feature Groups | Platform | `navGroup.licenseManagement` |
| 8 | `license_features` | License Features | Platform | `navGroup.licenseManagement` |
| 9 | `report_templates` | Report Templates | Platform | `navGroup.content` |
| 10 | `report_form_groups` | Form Groups | Platform | `navGroup.content` |
| 11 | `news` | News | Platform | `navGroup.content` |
| 12 | `broadcasts` | Broadcasts | Platform | `navGroup.content` |
| 13 | `usage_analytics` | Usage Analytics | Platform | `navGroup.analytics` |
| 14 | `activity_events` | Activity Events | Platform | `navGroup.analytics` |
| 15 | `cronjobs` | Scheduled Jobs | Platform | `navGroup.scheduling` |
| 16 | `applications` | Applications | Platform | `navGroup.platform` |
| 17 | `email_settings` | Email Settings | Platform | `navGroup.platform` |
| 18 | `platform_config` | Platform Config | Platform | `navGroup.platform` |
| 19 | `platform_roles` | Platform Roles | Platform | `navGroup.platform` |
| 20 | `super_admins` | Super Admins | Platform | `navGroup.platform` |
| 21 | `user_platform` | Platform Users | Platform | `navGroup.platform` |
| 22 | `platform_migrations` | Platform Migrations | Platform | `navGroup.database` |
| 23 | `sql_workbench` | SQL Workbench | Platform | `navGroup.database` |
| 24 | `database_pools` | Database Pools | Platform | `navGroup.database` |
| 25 | `cluster_admin_cluster` | Cluster | Cluster admin | `navGroup.clusterAdmin` |
| 26 | `cluster_admin_business_units` | Business Units | Cluster admin | `navGroup.clusterAdmin` |
| 27 | `cluster_admin_licenses` | Licenses | Cluster admin | `navGroup.clusterAdmin` |
| 28 | `cluster_admin_users` | Users | Cluster admin | `navGroup.clusterAdmin` |

แถว 25-28 เป็น **namespace คีย์แยกต่างหากจากฝั่ง platform console** ถึงแม้สามในสี่จะมีป้ายชื่อเมนูตรงกันเป๊ะกับแถวฝั่ง platform (`business_units`/`Business Units`, `licenses`/`Licenses`, `users`/`Users`) — คอมเมนต์ของ `clusterAdminNav.ts` เองระบุตรง ๆ ว่า "คีย์ของฝั่งนี้แยกจากของ platform ที่ชื่อเมนูซ้ำกัน" (บรรทัด 12) การตั้ง `business_units` เป็น `hide` ลบแค่แถว **Business Units** ของ platform console เท่านั้น แถว **Business Units** ของ cluster-admin console ยังคง render อยู่จนกว่า `cluster_admin_business_units` จะถูกตั้งแยกต่างหาก ไม่มีคีย์ไหนคุมทั้งสองพร้อมกัน

**ไม่มีในรายการนี้:** มีแค่ **Feature Flags** เท่านั้นที่ไม่มี feature key เลย จึงเป็นแถวเมนูเดียวที่ไม่มีบรรทัดในตารางนี้ (`/platform/features` gate ด้วย permission เท่านั้น §4 ของหน้า landing) **Super Admins** ไม่ใช่ข้อยกเว้นตัวที่สอง — มันมี feature key ของตัวเอง `feature: 'super_admins'` (แถวที่ 20) และ gate ผ่าน `hide`/`inactive` เหมือนทุกแถวอื่นในตารางนี้เป๊ะ สิ่งที่ทำให้แถวนี้พิเศษคือมันมีด่าน**ที่สองแยกต่างหาก**ซ้อนทับอยู่บนนั้น: `superAdminOnly` ซึ่งตรวจที่ระดับ nav และไม่เกี่ยวกับ feature flag เลย สองกลไกนี้ซ้อนกัน ไม่ใช่แทนที่กัน — session ที่ไม่มีสถานะ super-admin จะไม่เห็นแถวนี้เลยไม่ว่า `super_admins` จะถูกตั้งเป็นอะไร และสำหรับ session ที่มีสถานะ super-admin `super_admins` ก็ยังสั่ง `hide` แถวนี้หรือทำให้เป็น `comingSoon` ได้เหมือนคีย์อื่นทุกตัว

## 4. กลไกฝั่งเขียน — ตรวจสองครั้งอิสระต่อกัน และ PUT เท่านั้น

`GET`/`PUT /api-system/platform/feature-flags` (`feature_flags.controller.ts`) เป็นทางเดียวที่อ่านหรือเขียนแถวนี้ — ไม่เคยผ่าน `/api-system/platform/configs/:key` ทั่วไป ยืนยันโดยคอมเมนต์ระดับ class ของ controller เองที่ให้เหตุผลสองข้อ: `GET` บนทางทั่วไปต้องมี `platform_config.read` ซึ่งผู้ใช้ทั่วไปไม่มี และการตรวจสิทธิ์รายคีย์บนทางทั่วไปเป็นการ "บวกเพิ่ม" จาก `platform_config.manage` ซึ่งจะบังคับให้คนแก้ flag อย่างเดียวต้องถือ `platform_config.manage` ไปด้วย (`feature_flags.controller.ts:54-60`)

- **`GET`** (บรรทัด 83-108): guard ด้วย `KeycloakGuard` (ระดับ class) และ `AppIdGuard('feature-flags.get')` เท่านั้น — **ไม่มี** `PlatformPermissionGuard` **ไม่มี** `@RequirePlatformPermission` เลย ยืนยันโดยอ่าน method เต็ม: มันเรียก `platformConfigsService.findOne(FEATURE_FLAGS_KEY, ...)` ตรง ๆ แล้วคืนแมปเปล่า ๆ ไม่มีการตรวจสิทธิ์คั่นกลางเลย เปิดให้ทุกคนที่ยืนยันตัวตนแล้วโดยเจตนา (§4.2 ของหน้า landing มีนัยยะด้านความปลอดภัย)
- **`PUT`** (บรรทัด 118-174): `AppIdGuard('feature-flags.update')` **และ** `PlatformPermissionGuard` **และ** `@RequirePlatformPermission('feature_flag.manage')` (บรรทัด 118-120) — ด่านเขียนเดียวที่มี
- **แทนที่แมปทั้งใบ — ไม่มี `PATCH` สำหรับคีย์นี้ และโดยโครงสร้างแล้วมีไม่ได้ด้วย** ตัวสร้าง `PLATFORM_CONFIG_ENTRIES` ที่ `PlatformConfigService` ใช้ร่วมกันคำนวณรายชื่อ `fields` ที่รู้จักของแต่ละคีย์ไว้สำหรับให้ `PATCH` ปฏิเสธฟิลด์ที่ไม่รู้จัก และสำหรับ schema ที่ไม่ใช่ `z.ZodObject` — ซึ่ง `z.record(...)` ของ `feature_flags` เป็นแบบนั้น — รายการนั้นถูกปล่อยว่างไว้โดยเจตนา (`platform-config.schema.ts:452-456`, คอมเมนต์: "there is no fixed field list, so PATCH is refused outright — such keys are replaced wholesale by PUT") `rejectBadPatchShape()` ปฏิเสธ payload ที่ไม่ว่างเปล่าทุกตัวที่ได้รับเมื่อ `fields` ว่างเปล่า ดังนั้นการเรียก `PATCH` กับ `feature_flags` จะล้มเหลวทุก payload ไม่ใช่แค่ตัวที่ผิดรูปแบบ — นี่เป็นผลลัพธ์เชิงโครงสร้างจาก schema ที่เป็น `record` ไม่ใช่ `object` ไม่ใช่ช่องโหว่ที่ใครลืมปิด
- **ตรวจสอบสองครั้งบน `PUT` เพื่อข้อความ error ที่ดีกว่า** controller ฝั่ง gateway วนดูทุกคีย์ของ body ที่เข้ามาและตรวจค่ากับ `['active', 'inactive', 'hide']` ด้วยตัวเอง (`feature_flags.controller.ts:151-162`) **ก่อน** ส่งต่อไปยัง micro-cluster ซึ่งจะตรวจ body เดิมซ้ำอีกครั้งด้วย `FeatureFlagsConfigSchema` จริง (regex ของคีย์ `^[a-z][a-z0-9_]*$` บวก enum) ภายใน `PlatformConfigService.upsert()` คอมเมนต์อธิบายว่าทำไม gateway ถึงตรวจซ้ำสิ่งที่ backend จะตรวจอีกที: ตรวจตรงนี้ด้วยเพื่อให้ 422 ระบุคีย์ที่ผิดได้ — 422 ที่บอกแค่ "schema ไม่ผ่าน" ทำให้ผู้ดูแลหาไม่เจอว่าแถวไหนพัง (บรรทัด 148-150) การวนตรวจของ gateway เองไม่ได้ตรวจ regex ของชื่อคีย์เลย ตรวจแค่ค่าสถานะ — ชื่อคีย์ที่ผิด (เช่นมีตัวพิมพ์ใหญ่) จะถูกจับได้แค่ในรอบที่สอง ภายใน micro-cluster เท่านั้น
- **คีย์ที่ไม่ได้ส่งไปใน body ของ `PUT` ถือว่าถูกลบ ไม่ใช่ถูกปล่อยไว้เฉย ๆ** ทั้ง service ฝั่ง frontend (`featureFlagService.ts:24`, "แทนที่แมปทั้งใบ — คีย์ที่ไม่ได้ส่งไปถือว่าถูกลบ") และคำอธิบาย Swagger ของ controller เอง ("a key left out is removed") ระบุตรงกัน: แมปที่เก็บไว้ทั้งใบถูกแทนที่ด้วย object ที่ผู้เรียกส่งมา คีย์ต่อคีย์ นี่คือกลไกเบื้องหลังการแข่งกันเขียนทับแมปทั้งใบใน §6
- **ห้ามส่ง `doc_version` เด็ดขาด** `tb_platform_config` มีคอลัมน์นี้อยู่ แต่ไม่มี write path ของคีย์ไหนในตารางนี้อ่านหรือเพิ่มค่ามันเลย (ยืนยันไว้ที่[Platform Config — Data Model](/th/platform/platform-config/data-model) §5) — `feature_flags` ไม่ใช่กรณีพิเศษตรงนี้ มันแค่สืบทอดพฤติกรรมของตารางที่ใช้ร่วมกัน คอมเมนต์ของ service ฝั่ง frontend เองระบุเป็นคำสั่ง ไม่ใช่การค้นพบ: "ห้ามส่ง doc_version: ตาราง tb_platform_config มีคอลัมน์นั้นแต่ backend ยังไม่บังคับ" (`featureFlagService.ts:25`)

## 5. Consumer — ใครอ่านสถานะบ้าง และแต่ละตัวทำอะไร

ไม่มี consumer ตัวไหน cache ข้อมูลนี้เกินอายุที่ระบุด้านล่าง ทุกการตรวจสถานะคือการค้นในแมปที่ดึงมาไว้ในหน่วยความจำแล้ว ไม่ใช่การเรียก network ใหม่ต่อการตรวจแต่ละครั้ง

| Consumer | โปรเซส | ทำอะไรกับ `hide` / `inactive` / `active` |
| --- | --- | --- |
| `FeatureFlagProvider` (`FeatureFlagContext.tsx`) | Frontend ทั้งแอป | ดึงแมปทั้งใบแค่ **สองครั้ง** ต่อ session ของ browser — ครั้งแรกตอน mount ถ้ามี token อยู่ใน `localStorage` แล้ว (บรรทัด 49-62) และอีกครั้งตอน `login()` — ไม่เคย poll ไม่เคยถูก consumer ตัวไหนด้านล่างดึงซ้ำเอง ทุกตัวอ่านจาก object `states` เดียวกันในหน่วยความจำ การดึงที่ล้มเหลวจะถูกจับแล้วแทนที่ด้วย `DEFAULT_FEATURE_STATES` (ทุกคีย์ในแค็ตตาล็อกเป็น `active`) แบบเงียบ ๆ ไม่มี toast ตั้งใจ: "an ordinary user can do nothing about it... and the app still works" (บรรทัด 23-27) `flagOf(key)` กับคีย์ที่ไม่รู้จักคืน `'active'` (บรรทัด 65) — คีย์ที่พิมพ์ผิดจะไม่มีทางซ่อนแถวเมนูได้ |
| `buildPlatformNav()` (`platformNav.ts:85-103`) | Frontend, sidebar ฝั่ง platform | กรอง `ALL_PLATFORM_NAV_ITEMS`: แถวที่ `feature` resolve เป็น `hide` จะถูกตัดออกจากอาร์เรย์ทั้งหมด (บรรทัด 98); แถวที่ resolve เป็น `inactive` ยังอยู่ตำแหน่งเดิมในอาร์เรย์ แต่ได้ `comingSoon: true` เพิ่มมา (บรรทัด 100-102) แถวที่ไม่มี `feature` key เลย — เช่นแถวของ Feature Flags เอง — ผ่านทั้งสองเงื่อนไขเสมอโดยไม่มีเงื่อนไข |
| `buildClusterAdminNav()` (`clusterAdminNav.ts:22-26`) | Frontend, sidebar ฝั่ง cluster-admin | ตรรกะ hide-แล้ว-map-เป็น-comingSoon **เหมือนกันเป๊ะ** แต่ implement แยกต่างหาก ไม่ได้ใช้ helper ร่วมกับ `buildPlatformNav()` — ยืนยันโดยอ่านทั้งสองฟังก์ชันเต็ม เป็นบล็อกโค้ด 4-6 บรรทัดสองบล็อกที่แยกกัน ไม่ใช่ utility ตัวเดียวที่ใช้ร่วมกัน การเปลี่ยนพฤติกรรมของ filter หนึ่งในอนาคต (เช่นเพิ่มสถานะที่สี่) ต้องไปแก้ทั้งสองด้วยมือ |
| `navGroups` ของ `Sidebar.tsx` (บรรทัด 105-114) | Frontend, ทั้งสอง sidebar | จัดกลุ่มอาร์เรย์ **ที่ผ่านการกรองแล้ว** (หลังตัด `hide` ออก) เป็นหัวข้อตามแถวที่ `groupKey` ซ้ำกันติด ๆ ด้วยลูปแบบ "คีย์เดียวกับ item ก่อนหน้า → กลุ่มเดียวกัน ไม่งั้นเริ่มกลุ่มใหม่" เหมือนกันเป๊ะกับที่ `groups` useMemo ของ `FeatureFlagManagement.tsx` เอง (consumer ของ `featureFlags.ts`, บรรทัด 58-66) ทำสำหรับ layout การ์ดของหน้าตั้งค่าเอง — เป็นการ implement อัลกอริทึมเดียวกันสองครั้งอิสระต่อกัน ยืนยันโดยอ่านทั้งสองไฟล์ แถวที่เป็น `comingSoon` จะ render เป็น `<div>` ที่ไม่ใช่ `<Link>` และมี `aria-disabled="true"` — คอมเมนต์ของ component เองระบุว่านี่ตั้งใจ: `<Link>` ที่ปิด `pointer-events` ยังโฟกัสด้วยแป้นพิมพ์และกด Enter ได้อยู่ ซึ่งการ disable ด้วย CSS เฉย ๆ จะกันไม่ได้ (`Sidebar.tsx`, คอมเมนต์เหนือ branch `comingSoon`) |
| `PrivateRoute` (`PrivateRoute.tsx:84-102`) | Frontend, route guard | ถูกตรวจ **ท้ายสุด** หลังจาก `requiredPermission` และ `requireSuperAdmin` — คอมเมนต์ของ component เองระบุว่าลำดับนี้ตั้งใจ: "permission answers 'can you access this?', the flag answers 'is this ready yet?' — someone without access should still see 403, not a flag-driven 404" (บรรทัด 90-91) `hide` render `<NotFound />` ที่ตำแหน่งเดิม (ไม่ redirect); `inactive` render `<ComingSoon />` ทั้งสองเป็นการแทนที่ระดับ UI เท่านั้น **ไม่มีรหัสสถานะ HTTP เกี่ยวข้องเลย** — คอมเมนต์ของ `ComingSoon.tsx` เองระบุชัดว่าหน้านี้ไม่มีรหัสสถานะ "because the server refused nothing — the UI did" (`ComingSoon.tsx:14-16`) request ไปยัง API เดิมจาก client อื่นใดไม่ได้รับผลกระทบเลย |

## 6. กรณีพิเศษ

| สถานการณ์ | สิ่งที่เกิดขึ้นจริง |
| --- | --- |
| admin สองคนเปิดหน้า Feature Flags พร้อมกัน แต่ละคนแก้คนละคีย์ แล้วทั้งคู่กด Save | `PUT` ที่มาถึงทีหลังชนะเด็ดขาด — มันส่งร่างของตัวเองทั้งใบ (ตั้งต้นจากแมปตอนที่หน้าของ admin คนนั้นโหลด) เขียนทับการเปลี่ยนแปลงที่ admin คนแรก save ไปแล้วอย่างเงียบ ๆ สำหรับคีย์ที่คนที่สองไม่ได้แตะเลย ไม่มีการ merge ไม่มีการตรวจ conflict และไม่มีการตรวจ version (§4) — นี่คือพฤติกรรม last-write-wins-on-the-whole-map ปกติที่ทุกคีย์ของ `tb_platform_config` มี (บันทึกไว้แบบทั่วไปที่[Platform Config — Data Model](/th/platform/platform-config/data-model) §6) เห็นผลชัดกว่าที่นี่เพราะ *ทั้งแมป* คือค่าของคีย์เดียว ไม่ใช่หนึ่งใน namespace หลายตัว |
| คีย์หนึ่งถูกเอาออกจาก `FEATURE_CATALOG` ใน frontend release รุ่นถัดไป แต่สถานะของมันเคยถูก save ไว้ก่อนหน้า | `isFeatureKey()` คืน `false` ให้มัน การคำนวณ `orphans` ของหน้า Feature Flags เอง (`FeatureFlagManagement.tsx:44-47`) จะแสดงมันในการ์ด "Unknown keys" แยกต่างหาก พร้อมปุ่ม Remove การลบแค่แก้ `draft` ในหน่วยความจำ (`setDraft`, บรรทัด 163-168) — แถวจริงยังไม่ถูกลบจาก backend จนกว่าจะ Save ครั้งถัดไป เพราะ `PUT` แทนที่แมปทั้งใบเสมอ (§4) ก่อนหน้านั้น การ refresh หน้าโดยไม่ save จะทำให้คีย์กำพร้ากลับมาทันที |
| request `GET /api-system/platform/feature-flags` ล้มเหลว (network error, backend ล่ม) | ทุก consumer ใน §5 fallback ไปที่ `DEFAULT_FEATURE_STATES` — ทุกคีย์ในแค็ตตาล็อกเป็น `active` — แบบเงียบ ๆ โดย `isReady` ยังคงเปลี่ยนเป็น `true` เพื่อไม่ให้หน้าไหนค้างที่ loader รอ request ที่ล้มเหลวไปแล้ว (`FeatureFlagContext.tsx:41-46`) ผลจริงคือความล้มเหลวในการเข้าถึง endpoint นี้ทำให้ **ทั้งผลิตภัณฑ์ดูเหมือนเปิดใช้งานเต็มที่** ไม่ใช่ซ่อนบางส่วน |
| `PUT` สองตัวแข่งกันบนคีย์ที่ยังไม่เคยบันทึก (ยังไม่มีแถวสำหรับ `feature_flags`) | รูปแบบ `findFirst`-แล้ว-`create`/`update` ของ `PlatformConfigService.upsert()` (บันทึกไว้สำหรับตารางที่ใช้ร่วมกันที่[Platform Config — Data Model](/th/platform/platform-config/data-model) §2) ใช้เหมือนกันที่นี่: ทั้งคู่อาจเห็นว่ายังไม่มีแถวแล้วทั้งคู่ `create()` เหลือแถวที่ยังไม่ถูกลบสองแถวสำหรับ `key = 'feature_flags'` ตัวอ่านทุกตัว (`findOne` และ handler `GET` ของคีย์นี้เอง) จะเอาแถวที่อัปเดตล่าสุด อาการที่เห็นจริงคือแถวที่เก่ากว่าจากสองแถวหายไปเงียบ ๆ ไม่ใช่ error — ไม่ใช่สิ่งที่โค้ดของคีย์นี้เองป้องกันเป็นพิเศษ |
| ค่าที่ไม่ใช่ `'active'`/`'inactive'`/`'hide'` ไปถึงการเรียก `flagOf()` (เช่นแถวที่แก้ในฐานข้อมูลตรง ๆ) | การตรวจของ `PUT` ฝั่ง gateway (§4) กันไม่ให้สิ่งนี้ถูก *save* ผ่าน UI ของผลิตภัณฑ์เองได้ แต่ไม่ได้ย้อนแก้แถวที่ถูกแก้ในฐานข้อมูลตรง ๆ `flagOf()` ไม่มีการตรวจสอบตอน runtime เลยนอกจาก type ของ TypeScript สตริงที่ไม่คาดคิดจะไม่ถูกมองว่าเป็น `'hide'` หรือ `'inactive'` โดยทุกการเปรียบเทียบ `!== 'hide'` / `=== 'inactive'` ใน §5 ซึ่งหมายความว่ามันจะทำงานเหมือน `'active'` ทุกที่โดยไม่เคยถูกตรวจว่าเป็นเช่นนั้นจริง — ไม่ได้ยืนยันกับฐานข้อมูลจริง เป็นการให้เหตุผลจาก operator เปรียบเทียบเท่านั้น |

## 7. คำแนะนำ

- **อย่าทดสอบการสลับ flag โดยแก้ `tb_platform_config` ตรง ๆ แล้วคาดหวังความหมายแบบ `PATCH`** — `feature_flags` ปฏิเสธ `PATCH` ทุกครั้งโดยโครงสร้าง ไม่ว่า payload จะถูกต้องหรือไม่ (§4) ทางเขียนเดียวที่รองรับคือ `PUT` แมปทั้งใบผ่าน endpoint เฉพาะทาง
- **แผนทดสอบการแก้พร้อมกันควรคาดหวัง last-write-wins บนแมปทั้งใบ ไม่ใช่รายคีย์** — ดูแถวแรกใน §6 อย่าแจ้ง bug สำหรับการเปลี่ยนแปลงที่ "หายไป" เมื่อ admin อีกคน save ไม่กี่วินาทีต่อมา นี่คือพฤติกรรมปัจจุบันของ write path ที่ใช้ร่วมกันของ `tb_platform_config` ไม่ใช่เฉพาะคีย์นี้
- **อย่าคิดว่า backend จับชื่อคีย์ที่พิมพ์ผิดได้** — นอกเหนือจาก loop ตรวจค่าของ `PUT` (§4) ไม่มีอะไรฝั่ง backend ตรวจคีย์กับ `FEATURE_CATALOG` เลย คีย์ที่พิมพ์ผิดที่ save ผ่านการเรียก API ตรง ๆ จะอยู่ในแมปแบบมองไม่เห็น ไม่ตรงกับแถวเมนูไหนเลย จนกว่าจะมีใครสังเกตเห็นในหน้า "unknown key" ของหน้านั้นเอง
- **ถือว่า fallback-เป็น-`'active'` ของ `flagOf()` เป็นสมมติฐานเริ่มต้นสำหรับคีย์ไหนก็ตามที่ไม่มีในเอกสารนี้** — รวมถึงคีย์ใหม่ที่ถูกเพิ่มเข้า `FEATURE_CATALOG` หลังจากหน้านี้ถูกเขียน ตรวจกับ `featureFlags.ts` ตรง ๆ แทนที่จะสมมติว่าตารางนี้ (§3) ครบถ้วนตลอดไป

## 8. อ้างอิง

- `../carmen-platform/src/constants/featureFlags.ts` — `FeatureState`, `FeatureDefinition`, `FEATURE_CATALOG` (§3), `isFeatureKey`, `DEFAULT_FEATURE_STATES`
- `../carmen-platform/src/context/FeatureFlagContext.tsx` — จังหวะการดึงข้อมูล, การ fallback เมื่อล้มเหลว, `flagOf` (§5)
- `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 85-103) และ `src/components/nav/clusterAdminNav.ts` (บรรทัด 10-26) — filter `hide`/`inactive` สองตัวที่แยกกัน (§5)
- `../carmen-platform/src/components/Sidebar.tsx` (บรรทัด 105-114 และ branch render ของ `comingSoon`) — การจัดกลุ่มแบบ consecutive-run และแถวที่ปิดใช้งานแบบไม่ใช่ `<Link>` (§5)
- `../carmen-platform/src/components/PrivateRoute.tsx` (บรรทัด 84-102) — ลำดับการบังคับใช้ระดับ route และผลลัพธ์ (§5)
- `../carmen-platform/src/pages/ComingSoon.tsx` — หมายเหตุออกแบบเรื่องไม่มีรหัสสถานะ (§5)
- `../carmen-platform/src/pages/FeatureFlagManagement.tsx` (บรรทัด 44-47, 58-66, 152-169) — การตรวจจับคีย์กำพร้า, การจัดกลุ่มของหน้าตั้งค่า, การลบแบบ draft-only (§6)
- `../carmen-platform/src/services/featureFlagService.ts` — REST client รวมถึงคำเตือนเรื่อง `doc_version` (§4)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/feature_flags/feature_flags.controller.ts` — คู่ `GET`/`PUT` เฉพาะทาง, guard, และการตรวจสองครั้ง (§4)
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/platform-config/platform-config.schema.ts` (บรรทัด 242-246, 360-369, 452-456) — `FeatureFlagsConfigSchema`, entry ใน registry, และกลไก fields-ว่าง-แปลว่า-PATCH-ถูกปฏิเสธ (§4)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (บรรทัด 1462) — `tb_platform_config` บันทึกไว้แบบเต็มที่[Platform Config — Data Model](/th/platform/platform-config/data-model)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` (บรรทัด 43) — entry catalog ของ `feature_flag.manage` อ้างถึงในหน้า landing §4

**Cross-links:** [Feature Flags landing](/th/platform/feature-flags) &nbsp;·&nbsp; [Platform Config — Data Model](/th/platform/platform-config/data-model)
