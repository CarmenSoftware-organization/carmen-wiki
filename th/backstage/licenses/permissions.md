---
title: ไลเซนส์ — สิทธิ์ (Permissions)
description: subscription.read กั้นการดู (รวมถึงเปิดหน้าแก้ไขแบบอ่านอย่างเดียว); subscription.manage เพียงตัวเดียวกั้นทุกการแก้ไข license.manage เป็นคีย์ของอีกโมดูลหนึ่ง ไม่ใช่ของโมดูลนี้
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, licenses, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ไลเซนส์ — สิทธิ์ (Permissions)

> **At a Glance**
> **มีแค่สองคีย์:** `subscription.read` (nav, ทุก route ของ list/detail และ — โดยตั้งใจ — route แก้ไขของฟอร์มซื้อทั้งสามและ route แก้ไข subscription ด้วย) และ `subscription.manage` (ทุก route create/update/delete/cancel และ action save/cancel-licence ในหน้า — route ของ interface licence ที่เพิ่มใน PR #287 ใช้สองคีย์นี้เป๊ะ ไม่มีการสร้างคีย์ใหม่) &nbsp;·&nbsp; **`license.manage` ไม่ใช่คีย์ของโมดูลนี้** — คำอธิบายเดิมของหน้านี้เคยระบุว่ามันเป็นตัวกั้น CRUD ที่นี่; จริง ๆ แล้วมันกั้นสวิตช์ License Enforcement ที่ไม่เกี่ยวข้องกันบนหน้าจอ [Platform Config](/th/backstage/platform-config) (แก้ไขแล้วด้านล่าง §1) &nbsp;·&nbsp; **Feature flag:** `licenses` ตรวจโดย `PrivateRoute` หลังด่าน permission &nbsp;·&nbsp; **การอ่านฝั่ง backend ไม่ถูกกั้นโดยตั้งใจ** — ทุก `GET` บน controller บัญชีซื้อ/สัญญาทั้งสี่ของโมดูลนี้ (ยกเว้นของ subscription และรายการ `deleted` ที่เป็นของ super admin เท่านั้น) ไม่มี `@RequireBackstagePermission` เลย ตรวจสอบด้วย scope ของ cluster ภายใน `micro-cluster` แทน &nbsp;·&nbsp; **cluster admin ไม่มีวันมาถึงโมดูลนี้เลย** — `subscription.read`/`subscription.manage` มาจาก `tb_user_tb_backstage_role` เท่านั้น cluster admin แบบสมาชิกภาพไม่มีทั้งคู่ และใช้หน้าจอแบบอ่านอย่างเดียวแยกต่างหากแทน กั้นด้วยสมาชิกภาพของ cluster (`ClusterAdminRoute` ตรวจ `isClusterAdminOf(clusterId)`) ไม่ใช่คีย์ RBAC (กรณีพิเศษ 5, §4) &nbsp;·&nbsp; **e2e: smoke เท่านั้น** (`licenses-smoke.spec.ts` — render + sidebar, session ของ super admin, ยกเลิก mutation) — ทุกคำกล่าวอ้างด้านล่างมาจากการอ่าน implementation ของ `../carmen-backstage` และ `../carmen-turborepo-backend` โดยตรง

## 1. ภาพรวม

**คำแก้ไขต่อคำอธิบายเดิมของหน้านี้** ก่อนงานนี้ คำอธิบายใน frontmatter ของหน้านี้ระบุตัวกั้น CRUD ของโมดูลว่าเป็น "`subscription.manage` และ `license.manage`" นั่นผิด — การ grep ทั่ว `../carmen-backstage/src` หา `license.manage` เจอแค่ที่เดียว คือ `BackstageConfigManagement.tsx:75` (`hasPermission('license.manage')`) และไฟล์ลูก `backstageConfig/LicenseEnforcementCard.tsx` ทั้งคู่เป็นส่วนหนึ่งของโมดูล **[Platform Config](/th/backstage/platform-config)** — กั้นสวิตช์ "บังคับใช้ขีดจำกัดใบอนุญาต" ซึ่งเป็นการตั้งค่าระดับแพลตฟอร์ม ไม่เกี่ยวข้องกับการซื้อหรือแก้ไขใบอนุญาต, subscription, หรือที่นั่งใด ๆ เลย ไม่มีที่ไหนใต้ `src/pages/licenses/` อ้างถึง `license.manage` เลยสักที่ โมดูลนี้มี permission key แค่สองตัว ทั้งคู่อยู่ใต้ resource `subscription.*` และหน้านี้เอกสารเฉพาะสองตัวนั้น

รูปแบบที่เป็นเอกลักษณ์ของโมดูลนี้จริง ๆ คือ **`subscription.read` เพียงอย่างเดียวก็เปิดหน้าแก้ไขได้** — `/licenses/subscriptions/:id/edit`, `/licenses/seats/:id/edit`, `/licenses/bu-quota/:id/edit` และ `/licenses/interface/:id/edit` ทั้งหมดต้องการ `subscription.read` ที่ระดับ route คีย์เดียวกับที่ list/detail แบบอ่านอย่างเดียวของมันต้องการ ขณะที่ route `/new` ทั้งสี่พี่น้องต้องการ `subscription.manage` นี่ไม่ใช่ความไม่สอดคล้องของ route guard — ทุกฟิลด์บนทุกฟอร์มแก้ไขถูกกั้นแยกต่างหากภายใน component เอง (§3) session ที่มีแค่ `subscription.read` จึงเห็นเรคคอร์ดแต่แก้ไขไม่ได้

## 2. เมทริกซ์ของ gate

ทุก route ตรวจผ่าน `PrivateRoute` ซึ่งตรวจ `requiredPermission` ก่อน (ล้มเหลว → `<Forbidden>` ในที่, URL ไม่เปลี่ยน) แล้วตรวจ feature flag `feature` หลังเสมอ (ล้มเหลว → `NotFound` เมื่อ `hide`, `ComingSoon` เมื่อ `inactive`) — ดู [Backstage RBAC — Permissions](/th/backstage/rbac/permissions) สำหรับ resolver ที่ใช้ร่วมกัน

| Route | Permission | Feature | แหล่งที่มา |
|---|---|---|---|
| `/licenses` | `subscription.read` | `licenses` | `../carmen-backstage/src/App.tsx:187-194` |
| `/licenses/:clusterId` | `subscription.read` | `licenses` | `App.tsx:195-202` |
| `/licenses/subscriptions/new` | `subscription.manage` | `licenses` | `App.tsx:203-210` |
| `/licenses/subscriptions/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:211-218` |
| `/licenses/seats/new` | `subscription.manage` | `licenses` | `App.tsx:219-226` |
| `/licenses/seats/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:227-234` |
| `/licenses/bu-quota/new` | `subscription.manage` | `licenses` | `App.tsx:235-242` |
| `/licenses/bu-quota/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:243-250` |
| `/licenses/interface/new` | `subscription.manage` | `licenses` | `App.tsx:251-258` (PR #287) |
| `/licenses/interface/:id/edit` | **`subscription.read`** | `licenses` | `App.tsx:259-266` (PR #287) |
| `/subscriptions`, `/subscriptions/new`, `/subscriptions/:id/edit` | (ไม่มี — redirect ล้วน) | ไม่มี | `App.tsx:268-270` |
| Sidebar "Licenses" (กลุ่ม License Management) | `subscription.read` | `licenses` | `../carmen-backstage/src/components/nav/backstageNav.ts:24` |

Gate แบบ `<Can>`/`hasPermission` ในหน้า ทั้งหมดอยู่บน `subscription.manage`:

| จุด | Component |
|---|---|
| Save Changes (แก้ไข subscription, แถบ sticky) | `SubscriptionForm.tsx:591` |
| ปุ่ม Submit ของฟอร์มสร้างและทุกฟิลด์ที่แก้ได้ (`editing={canEdit}`) | `SubscriptionCreateForm.tsx:254`, `SubscriptionForm.tsx:96` |
| checkbox ของตัวเลือกกลุ่ม (`readOnly={!canEdit}`) | `GroupSelectionCard` ผ่าน `SubscriptionForm.tsx:569` |
| Save Changes / Create License (ฟอร์มซื้อ seat, BU-quota หรือ interface) | `LicensePurchaseForm.tsx` (`canEdit`, `<Can permission="subscription.manage">` บนทั้งสองปุ่ม) |
| ลิงก์ "Add interface license" / "New subscription" บนแท็บ Licenses ของหน้าแก้ไข BU | `BusinessUnitEdit.tsx:793,810` — `createHref` ถูกส่งมาเฉพาะเมื่อ `canCreateSubscription` (= `hasPermission('subscription.manage')`) คีย์เดียวกับที่ route ปลายทางตรวจ ลิงก์จึงไม่มีวันพาไป `<Forbidden>` |
| Cancel this license (เฉพาะฟอร์มซื้อ BU-quota — `config.cancel` ไม่ใช่ null) | `LicensePurchaseForm.tsx:975` |
| Add Subscription (header + empty state, `SubscriptionTable`) | `SubscriptionTable.tsx:467,650` |
| การ์ด **Deleted** ใน summary ของ License Center และมุมมอง licence ที่ถูกลบ (`?deleted=1`) | `LicenseCenter.tsx` ส่ง control `deletedView` ก็ต่อเมื่อ `isSuperAdmin` และแท็บไม่ใช่ "By cluster"; สำหรับคนอื่นการ์ดเป็นตัวเลขอ่านอย่างเดียว (ลิงก์ `?deleted=1` ที่แปะมายังแสดงตารางปกติ) |
| Restore (action ของแถวในมุมมองที่ถูกลบ) | `<Can permission="subscription.manage">` ใน `DeletedLicenseTable.tsx`; **Delete permanently** แสดงเฉพาะเมื่อ `isSuperAdmin` และให้ผู้ปฏิบัติงานพิมพ์เลข licence ยืนยัน (`TypeToConfirmDialog`) |
| ปุ่ม soft-delete ท้ายหน้าแก้ไข **subscription** และหน้าแก้ไข **interface-licence** (ไม่มีในที่นั่ง ไม่มีใน BU quota) | `<Can permission="subscription.manage">` ใน `SubscriptionForm.tsx` / `LicensePurchaseForm.tsx` (`config.kind === 'interface'`); อยู่หลัง `ConfirmDialog` แล้ว redirect กลับรายการ |
| action ต่อแถว Add/Edit/Cancel/Remove ของ `BuQuotaSection`/`SeatSection` | prop `canManage` คำนวณครั้งเดียวโดย `ClusterLicenseDetail.tsx:59` จาก `hasPermission('subscription.manage')` แล้วส่งลง — **ไม่** ถูกตรวจซ้ำต่อ section |

การบังคับใช้ฝั่ง backend พิสูจน์โดยตรงกับ controller source (ทุก route เขียนต้องการ `subscription.manage`; ทุก route อ่านไม่มี `@RequireBackstagePermission` เลย):

| Endpoint | Guard | แหล่งที่มา |
|---|---|---|
| `GET /api-system/clusters/:clusterId/licenses` | `AppIdGuard` เท่านั้น | `backstage_cluster-licenses.controller.ts:104-105` |
| `POST /api-system/clusters/:clusterId/licenses` | `AppIdGuard` + `BackstagePermissionGuard`, `subscription.manage` | `backstage_cluster-licenses.controller.ts:144-146` |
| `PATCH /api-system/clusters/:clusterId/licenses/:id` | เหมือนกัน, `subscription.manage` | `backstage_cluster-licenses.controller.ts:189-191` |
| `DELETE /api-system/clusters/:clusterId/licenses/:id` | เหมือนกัน, `subscription.manage` | `backstage_cluster-licenses.controller.ts:237-239` |
| `POST /api-system/clusters/:clusterId/licenses/:id/cancel` | เหมือนกัน, `subscription.manage` | `backstage_cluster-licenses.controller.ts:277-279` |
| `GET /api-system/backstage/cluster-licenses[/:id]` | `AppIdGuard` เท่านั้น | `backstage_cluster-licenses.controller.ts:370-371,500-501` (fleet controller) |
| `GET /api-system/business-units/:buId/licenses` | `AppIdGuard` เท่านั้น | `backstage_business-unit-licenses.controller.ts:99-100` |
| `POST /api-system/business-units/:buId/licenses` | `subscription.manage` | `backstage_business-unit-licenses.controller.ts:139-141` |
| `PATCH /api-system/business-units/:buId/licenses/:id` | `subscription.manage` | `backstage_business-unit-licenses.controller.ts:184-186` |
| `DELETE /api-system/business-units/:buId/licenses/:id` | `subscription.manage` | `backstage_business-unit-licenses.controller.ts:232-234` |
| `GET /api-system/backstage/business-unit-licenses[/:id]` | `AppIdGuard` เท่านั้น | `backstage_business-unit-licenses.controller.ts:316-317,436-437` |
| `GET /api-system/business-units/:buId/interface-licenses` | `AppIdGuard('businessUnitInterfaceLicense.findAll')` เท่านั้น | `backstage_business-unit-interface-licenses.controller.ts:105-106` |
| `POST /api-system/business-units/:buId/interface-licenses` | `AppIdGuard` + `BackstagePermissionGuard`, `subscription.manage` | `backstage_business-unit-interface-licenses.controller.ts:148-150` |
| `PATCH /api-system/business-units/:buId/interface-licenses/:id` | เหมือนกัน, `subscription.manage` | `backstage_business-unit-interface-licenses.controller.ts:194-196` |
| `DELETE /api-system/business-units/:buId/interface-licenses/:id` | เหมือนกัน, `subscription.manage` | `backstage_business-unit-interface-licenses.controller.ts:241-243` |
| `GET /api-system/backstage/interface-licenses[/:id]` | `AppIdGuard` เท่านั้น | `backstage_business-unit-interface-licenses.controller.ts:328-329,458-459` (fleet controller, ไฟล์เดียวกัน) |
| `GET .../subscriptions`, `.../subscriptions/summary`, `.../subscriptions/:id`, `.../license-features` | `subscription.read` | `backstage_subscriptions.controller.ts:90-92,145-147,215-217,251-253` |
| `POST .../subscriptions` | `subscription.manage` | `backstage_subscriptions.controller.ts:282-284` |
| `PATCH .../subscriptions/:id` | `subscription.manage` | `backstage_subscriptions.controller.ts:322-324` |
| `PUT .../subscriptions/:id/groups` | `subscription.manage` | `backstage_subscriptions.controller.ts:369-371` |
| `DELETE .../subscriptions/:id` | `subscription.manage` | `backstage_subscriptions.controller.ts:421-423` |
| `GET .../{cluster-licenses,business-unit-licenses,interface-licenses}/summary` (fleet controllers) | `AppIdGuard` เท่านั้น กรองตาม scope | `backstage_cluster-licenses.controller.ts:430-431`, `backstage_business-unit-licenses.controller.ts:366-367`, `backstage_business-unit-interface-licenses.controller.ts:388-389` |
| `GET .../{cluster-licenses,business-unit-licenses,interface-licenses}/deleted`, `GET .../subscriptions/deleted` | `AppIdGuard` + **`BackstageSuperAdminGuard`** — ไม่มี permission key เลย | `…cluster-licenses.controller.ts:460-461`, `…business-unit-licenses.controller.ts:396-397`, `…interface-licenses.controller.ts:418-419`, `backstage_subscriptions.controller.ts:178-179` |
| `POST .../{cluster-licenses,business-unit-licenses,interface-licenses}/:id/restore`, `POST .../subscriptions/:id/restore` | `subscription.manage` | `…cluster-licenses.controller.ts:539-541`, `…business-unit-licenses.controller.ts:475-477`, `…interface-licenses.controller.ts:499-501`, `backstage_subscriptions.controller.ts:459-461` |
| `DELETE .../{cluster-licenses,business-unit-licenses,interface-licenses}/:id/hard`, `DELETE .../subscriptions/:id/hard` | **`BackstageSuperAdminGuard`** เท่านั้น | `…cluster-licenses.controller.ts:573-574`, `…business-unit-licenses.controller.ts:512-513`, `…interface-licenses.controller.ts:536-537`, `backstage_subscriptions.controller.ts:498-499` |

path ฝั่ง backend ทั้งหมดข้างบนคือ `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/{backstage_cluster-licenses,backstage_business-unit-licenses,backstage_business-unit-interface-licenses,backstage_subscriptions}/*.controller.ts` คอมเมนต์หัวไฟล์ของ controller interface licence ให้เหตุผลเดียวกับอีกสองตัวในการปล่อยการอ่านไม่กั้น: `BackstagePermissionGuard` สร้างชุด permission จาก `tb_user_tb_backstage_role` เท่านั้น คีย์ RBAC บน path อ่านจึงจะ 403 cluster admin แบบสมาชิกภาพที่ดูคลัสเตอร์ของตัวเอง

## 3. ทำไม route `:id/edit` ของฟอร์มซื้อทั้งสองแบบต้องการแค่ `subscription.read`

นี่เป็นความตั้งใจ พิสูจน์ได้สามทางแยกกัน ไม่ใช่ความไม่สอดคล้องที่ต้องปักธงว่าเป็นบั๊ก:

1. **Route guard เอง** `App.tsx` ต้องการ `subscription.read` บน route `:id/edit` และ `subscription.manage` เฉพาะบน route `new` พี่น้อง (§2) session ที่มีแค่ `subscription.read` จึงเข้า URL แก้ไขของ subscription หรือใบอนุญาตที่มีอยู่แล้วตัวไหนก็ได้
2. **Gate ของ component เอง** ทั้ง `SubscriptionForm.tsx:96` และ `LicensePurchaseForm.tsx:461` คำนวณ `canEdit = hasPermission('subscription.manage')` เป็นอิสระจาก route แล้วใช้มันตัดสินว่าฟิลด์ของฟอร์มจะ render เป็น input ที่แก้ได้หรือเป็นข้อความ `ReadOnlyField` — คอมเมนต์ของ `LicenseFieldsCard` เองระบุตรง ๆ ว่า "`editing` เป็น `false` เฉพาะตอนดูอย่างเดียว (ไม่มี `subscription.manage`) — โหมดสร้างเป็น `true` เสมอ (route คุมสิทธิ์ไว้แล้ว)" ทุกปุ่ม Save/Create/Cancel-licence ถูกห่อแยกต่างหากด้วย `<Can permission="subscription.manage">`
3. **backend เห็นด้วย** `ClusterLicenseDetail.tsx:46-48` ระบุเรื่องนี้ไว้ตรง ๆ: `canManage` คำนวณจาก `subscription.manage` "**ไม่ใช่** `cluster.update`" เพราะ backend บังคับ `subscription.manage` บนทั้งสอง endpoint เขียนของใบอนุญาตไม่ว่า frontend จะทำอะไร session ที่ไปถึงปุ่ม Save ได้โดยไม่มีคีย์นี้ (ด้วยเหตุผลใดก็ตาม) ก็จะโดน 403 จาก server อยู่ดี

**เหตุผลที่รูปแบบนี้มีอยู่** จากคอมเมนต์ source เดียวกัน: สิทธิ์อ่านของใบอนุญาตของ cluster หรือ BU ตัวเองจงใจ **ไม่** ผูกกับคีย์ RBAC บนเส้นทางอ่าน — route `GET` ไม่มี `@RequireBackstagePermission` เพราะ guard นั้นอ่านสิทธิ์จาก `tb_user_tb_backstage_role` เท่านั้น ซึ่งไม่มีทางแสดง "ผู้ใช้คนนี้ดูแล cluster นี้ผ่าน `tb_cluster_user`" ได้เลย การกั้นการอ่านด้วย `subscription.read` ที่ backend จะไม่มีผลเสียกับ platform admin ที่ถือคีย์นั้นอยู่แล้ว แต่ route guard ฝั่ง frontend ก็ยังตั้งใจใช้คีย์เดียวกันสะท้อนไว้ เพื่อให้ประสบการณ์ฝั่งเบราว์เซอร์ของ platform admin ว่า "ดูได้ไหม" กับ "แก้ได้ไหม" ยังคงแยกกันชัดเจนให้เห็น แม้ว่าการตรวจสอบสิทธิ์อ่านข้อมูล scoped จริง ๆ ของ backend จะเดินผ่านสมาชิกภาพของ cluster ไม่ใช่คีย์นี้เลยก็ตาม

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | session มีแค่ `subscription.read` | เปิด `/licenses`, `/licenses/:clusterId`, และ URL `:id/edit` ใดก็ได้; เห็นทุกฟิลด์เป็นข้อความอ่านอย่างเดียว ไม่มีปุ่ม Save/Cancel-licence/Create ไม่มีปุ่ม Add-subscription บนหน้ารายการ | ทำซ้ำได้โดยเปิด URL แก้ไขของใบอนุญาตใบหนึ่งตรง ๆ — หน้า render เต็ม แค่ไม่ทำอะไรได้เลย `SubscriptionForm.test.tsx` และ `SubscriptionTable.test.tsx` ทั้งคู่ pin เคสนี้ไว้เป๊ะ |
| 2 | session มี `subscription.manage` แต่ไม่มี `subscription.read` | เข้า `/licenses` หรือ `/licenses/:clusterId` ไม่ได้เลย (`<Forbidden>`) — แต่**เข้าได้**ที่ `/licenses/subscriptions/new`, `/licenses/seats/new`, `/licenses/bu-quota/new` ตรง ๆ ผ่าน URL เพราะ route เหล่านั้นตรวจแค่ `subscription.manage` | รูปแบบ grant ที่ไม่ปกติ (manage โดยไม่มี read) เป็นไปได้ในหลักการเพราะสองคีย์เป็นแถว RBAC ที่เป็นอิสระต่อกัน ตัดสินตามแผนทดสอบว่าเป็น role จริงหรือความผิดพลาดในการตั้งค่า |
| 3 | ใบที่นั่งหรือ interface licence — พยายามยกเลิก | ไม่มีปุ่ม Cancel เลยไม่ว่าจากแถวในลิสต์หรือหน้าแก้ไขเฉพาะใบ — `config.cancel` เป็น `null` สำหรับ `SEAT_CONFIG` และ `INTERFACE_CONFIG` และไม่มี endpoint แบบนี้บน backend สำหรับทั้งสองตารางเลย | อย่ามองปุ่มที่หายไปว่าเป็นปัญหาสิทธิ์ที่ต้อง escalate — มันเป็นความสามารถที่ไม่มีอยู่สำหรับประเภทการซื้อเหล่านี้ ยืนยันได้ทั้งระดับ schema (ไม่มีคอลัมน์ `cancelled_at`) และระดับ config |
| 3a | session ที่มี `subscription.manage` ผูกกลุ่มชนิด `interface` เข้ากับ subscription (`PUT .../subscriptions/:id/groups`) หรือกลุ่ม `standard` เข้ากับ interface licence (`POST .../interface-licenses`) | **400 จาก backend** ไม่ใช่การกรองเงียบ ๆ และไม่ใช่ 403 — permission ผ่าน แต่ payload ไม่ผ่าน SPA ไม่เคยเสนอทั้งสองแบบ (`GroupSelectionCard` ของฟอร์ม subscription ซ่อนกลุ่ม `interface`; ตัวเลือกของฟอร์มซื้อแสดงเฉพาะกลุ่ม `interface`) จึงเข้าถึงได้ผ่านการเรียก API ตรงเท่านั้น | 400 ตรงนี้คือกฎ kind ของกลุ่ม (`enum_license_feature_group_kind`, [Data Model](/th/backstage/licenses/data-model) §5) ไม่ใช่ข้อบกพร่องของ gate; อย่ายื่นเป็นบั๊กของ RBAC |
| 4 | ใบ BU-quota ที่ถูกยกเลิกแล้ว | ฟิลด์กลายเป็นอ่านอย่างเดียวถาวรบนหน้าแก้ไขของมัน (มี banner อธิบาย) แม้สำหรับ session ที่มี `subscription.manage`; ไม่มีทางย้อนกลับ — คืนความคุ้มครองต้องสร้างใบใหม่ | สถานะอ่านอย่างเดียวตรงนี้เป็นกฎธุรกิจ (§2 ของ [Data Model](/th/backstage/licenses/data-model)) ไม่ใช่ permission gate — ยืนยันว่าปุ่ม Save หายไปเลย ไม่ใช่แค่ disabled พร้อม tooltip |
| 5 | cluster admin (สมาชิกภาพเท่านั้น ไม่มี role RBAC) | เข้า `/licenses/*` route ไหนไม่ได้เลย — `hasPermission('subscription.read')` เป็น `false` เสมอสำหรับ session ที่ไม่มีแถว `tb_user_tb_backstage_role` เลย ไม่ว่าจะมีสถานะ cluster admin หรือไม่ก็ตาม | cluster admin ใช้หน้าจอ `/cluster-admin/:clusterId/licenses` ที่แยกออกไปคนละหน้าแทน `ClusterAdminRoute` ตรวจ scope ก่อน feature flag เสมอ ตามลำดับนี้: authenticated → `adminScope` โหลดเสร็จ → ถ้าไม่มี `clusterId` หรือผู้เรียกไม่ใช่ `isClusterAdminOf` ของ cluster นั้น จะ render `<Forbidden>` — ผู้ที่ไม่ใช่สมาชิกของ cluster นั้นถูกกั้นตรงนี้ ก่อนที่ `feature="cluster_admin_licenses"` จะถูกตรวจด้วยซ้ำ ไม่มี **RBAC permission key** บน route นี้เลย (ต่างจากคีย์ `subscription.*` ของโมดูลนี้เอง) แต่สมาชิกภาพของ cluster เป็น gate จริงที่บังคับใช้อยู่ ไม่ใช่การไม่มี gate เลย — อย่าทดสอบ gate ของโมดูลนี้จาก session ของ cluster admin อยู่ดี มันจะ 403 ตั้งแต่ route `/licenses/*` แรกที่ลองเปิด |
| 6 | Deep link ไปที่ `/licenses/subscriptions/:id/edit` ด้วย id ที่ไม่มีอยู่หรือถูกลบแล้ว | route guard ผ่าน (permission ถูกตรวจก่อนที่ id จะถูกดึงมาด้วยซ้ำ); หน้าจึงโหลด ได้ 404 จาก API แล้ว render `EmptyState` "Subscription not found" ของตัวเอง แทนที่จะเป็น error ดิบ | แยกความต่างระหว่าง permission 403 (ทั้งหน้าถูกแทนที่ด้วย `<Forbidden>`) กับ data-layer not-found (`PageHeader` render ปกติ มีแค่ body เป็น EmptyState) — สองอย่างนี้หน้าตาต่างกันและหมายความต่างกัน |
| 7 | บุ๊กมาร์ก `/subscriptions/:id/edit` แบบเก่า | redirect ผ่าน `SubscriptionEditRedirect` ก่อนที่การตรวจ permission ใด ๆ บน path *เก่า* จะทำงาน — การตรวจ permission ที่มีผลจริงคือตัวที่อยู่บน route ปลายทาง `/licenses/subscriptions/:id/edit` (`subscription.read`) | session ที่ไม่มี `subscription.read` จะเห็น `<Forbidden>` หลังจาก redirect เสร็จแล้วเท่านั้น ที่ URL ใหม่ — address bar จะโชว์ `/licenses/...` ไม่ใช่ path เดิมของบุ๊กมาร์ก ซึ่งเป็นพฤติกรรม `replace: true` ที่คาดหวังไว้อยู่แล้ว ไม่ใช่บั๊ก |
| 8 | Session ของ super-admin หรือ bootstrap | ทุก gate ใน §2 ผ่านหมดไม่ว่าจะมี grant อะไร — [RBAC resolver](/th/backstage/rbac/permissions) short-circuit ก่อนตรวจคีย์ใด ๆ | อย่า QA เมทริกซ์การกั้นสิทธิ์ของโมดูลนี้จาก session super-admin เด็ดขาด มันเผยความจริงเรื่อง grant `subscription.*` ที่ขาดหายไปไม่ได้เลย |
| 9 | ค่าเกณฑ์ใกล้หมดอายุ (`GET /api-system/backstage/expiry-thresholds`) | อ่านได้โดย **session ที่ล็อกอินแล้วทุกตัว** เป็นอิสระจาก `subscription.read` — โดยตั้งใจ เพื่อให้ป้ายเตือนบนหน้าจอของโมดูลนี้สะท้อนการตั้งค่าจริงของผู้ดูแลให้ทุกคนเห็น ไม่ใช่แค่คนที่มี permission licensing เท่านั้น | อย่าคาดหวังว่า endpoint ตัวนี้จะ 403 สำหรับ session ที่เข้า `/licenses` ไม่ได้เลย — มันถูกเรียกจาก `ExpiryThresholdProvider` ที่ root ของแอป ก่อน route-level gate ใด ๆ จะทำงานด้วยซ้ำ |
| 10 | session `subscription.manage` (ไม่ใช่ super admin) ต้องการดู licence ที่ถูกลบ | ไม่มีทางเข้า: การ์ด Deleted ไม่ตอบสนองสำหรับพวกเขา และ endpoint `…/deleted` ตอบ 403 (`BackstageSuperAdminGuard`) พวกเขา *soft-delete* subscription หรือ interface licence จากหน้าแก้ไขได้ และถ้ารู้ id ก็เรียก `restore` ได้ แต่ไม่สามารถแสดงรายการสิ่งที่ตัวเองลบ | ทดสอบ restore ด้วย session ของ super admin; ทดสอบการ์ดที่ไม่ตอบสนองด้วย session `subscription.manage` ธรรมดา |
| 11 | ลบถาวร licence ที่ยัง active | Backend ปฏิเสธด้วย 409 `LICENSE_HARD_DELETE_ACTIVE` — hard delete ทำได้เฉพาะแถวที่ถูก soft-delete แล้ว หรือ (BU quota) แถวที่ถูกยกเลิกแล้ว SPA เสนอให้ในมุมมองที่ถูกลบเท่านั้น บวก action ของแถว BU-quota ที่ถูกยกเลิกในตารางสด (`PurchaseLicenseTable.tsx`, `hardDeleteRow`) | เลขที่ลบถาวรจะถูกเขียนลง `tb_license_number_retired` และไม่ถูกออกซ้ำ ([Data Model](/th/backstage/licenses/data-model) §2.5) |

## 5. คำแนะนำ

- **ทดสอบ read กับ manage เป็นสองแกนที่เป็นอิสระต่อกันจริง ๆ** ไม่ใช่สมมติฐาน read≤manage แบบที่ยกมาจากโมดูลอื่น — session ถือคีย์ใดคีย์หนึ่งเดี่ยว ๆ ได้ และ route แก้ไขของโมดูลนี้พึ่งพาความเป็นอิสระนั้นโดยตรง (§3)
- **อย่าตีความปุ่ม Cancel ที่หายไปของ BU-quota บนประเภทที่นั่งว่าเป็นบั๊กสิทธิ์** ตรวจกับ [Data Model](/th/backstage/licenses/data-model) §2.2 ก่อนเสมอ มันเป็นช่องว่างความสามารถระดับ schema ไม่ใช่ความหละหลวมของการกั้นสิทธิ์
- **ส่งต่อคำแก้ไขเรื่อง `license.manage` ต่อไป** ถ้าพบหน้าอื่นในวิกินี้ (โดยเฉพาะ [Platform Config](/th/backstage/platform-config)) อ้างว่า `license.manage` เป็นคีย์ของโมดูล Licenses ในภายหลัง ให้ยึด §1 ของหน้านี้เป็นหลัก แล้วแก้ที่ต้นทาง ไม่ใช่ที่นี่
- **ทดสอบการเข้าถึงของ cluster-admin แยกเป็นกรณีของตัวเองต่างหาก** มันไม่มีวันมาถึง gate ของโมดูลนี้เลย (กรณีพิเศษ 5) และการที่มัน pass ตรงนั้นไม่ได้พิสูจน์อะไรเลยเกี่ยวกับการบังคับสิทธิ์ RBAC ของโมดูลนี้เอง
- **เมื่อโมดูลนี้มี e2e spec มากกว่า smoke** เคส read/manage-independence ใน §4 (โดยเฉพาะกรณีพิเศษ 1 และ 2) คือเคสที่คุ้มค่าที่สุดที่จะเขียนเป็นชุดแรก เพราะเป็นรูปแบบการกั้นสิทธิ์ที่ไม่ชัดเจนในตัวเองที่สุดของโมดูลนี้

**แหล่งอ้างอิง:** path ทั้งหมดคือ `../carmen-backstage` ยกเว้นที่ระบุไว้ `src/App.tsx:187-270` (route + redirect เก่า) · `src/components/nav/backstageNav.ts:24` (รายการ sidebar) · `src/pages/licenses/{SubscriptionForm,LicensePurchaseForm}.tsx` (การคำนวณ `canEdit`/`canEditFields`, gate `<Can>`) · `src/pages/licenses/ClusterLicenseDetail.tsx:46-59` (`canManage` แหล่งความจริงเดียวที่ส่งลงทั้งสามแท็บ) · `src/pages/BackstageConfigManagement.tsx:74-75`, `src/pages/backstageConfig/LicenseEnforcementCard.tsx:14,109` (`license.manage` — คีย์ของอีกโมดูลหนึ่ง, §1) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/{backstage_cluster-licenses,backstage_business-unit-licenses,backstage_subscriptions}/*.controller.ts` (การบังคับใช้ฝั่ง backend, §2)
**ลิงก์ข้าม:** [หน้าลงจอด Licenses](/th/backstage/licenses) &nbsp;·&nbsp; [Data Model](/th/backstage/licenses/data-model) &nbsp;·&nbsp; [UI Screens](/th/backstage/licenses/ui-screens) &nbsp;·&nbsp; [Backstage RBAC — Permissions](/th/backstage/rbac/permissions) &nbsp;·&nbsp; [cluster-admin](/th/backstage/cluster-admin) &nbsp;·&nbsp; [Platform Config](/th/backstage/platform-config)
