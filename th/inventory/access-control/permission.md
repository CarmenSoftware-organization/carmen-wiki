---
title: สิทธิ์ (Permission)
description: คู่ resource + action แบบ atomic ที่รวมเข้าใน application role เพื่อ RBAC; App ID allowlist และ licence feature ต่อ BU เป็นเลเยอร์แยก การเปลี่ยนแคตตาล็อกตั้งแต่ 2026-07-29: เปลี่ยนชื่อ inventory_period, ลบ query_dataset
published: true
date: '2026-09-23T01:30:00.000Z'
tags: access-control, permission, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# สิทธิ์ (Permission)

> **At a Glance**
> **เจ้าของ:** จัดการโดย seed (release-time) &nbsp;·&nbsp; **ตาราง:** `tb_permission` &nbsp;·&nbsp; **ใช้โดย:** [access-control/application-role](/th/inventory/access-control/application-role) (consumer เดียว) &nbsp;·&nbsp; **Endpoint:** `GET api/config/:bu_code/permissions` (แคตตาล็อก, `KeycloakGuard` เท่านั้น), `GET /api/user/permission` (+ `/mobile`, `/platform`) &nbsp;·&nbsp; คู่ `(resource, action)` แบบ atomic — หน่วยเล็กที่สุดของการอนุญาต **มีเลเยอร์การอนุญาตสามชั้นอยู่ร่วมกันที่ HEAD:** RBAC (`@Permission` + `PermissionGuard` บน route decoration 38 จุด), App-ID client allowlist (`AppIdGuard` route ส่วนใหญ่) และ **licence** feature ต่อ BU (`LicenseInterceptor` ทุก route ที่ map ไว้)

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

- **การเปลี่ยนแคตตาล็อกตั้งแต่ 2026-07-29** (`packages/prisma-shared-schema-platform/prisma/seed.permission.data.ts`): `system_admin.period` → **`system_admin.inventory_period`** (migration `20260916140000_rename_period_to_inventory_period` ทั้งสี่ action grant ของ role ถูกย้ายตาม); **`system_admin.query_dataset` ถูกลบ** (`7bebddaa7`, 2026-09-21 — SQL Workbench gate ด้วย platform permission เท่านั้น); เพิ่ม `configuration.chart_of_accounts` (เปลี่ยนชื่อจาก account code, 2026-08-27), `configuration.cost_center`, `configuration.cost_center_group`, `configuration.location_shelf`, resource `accounting.gl.*` (โมดูล GL), `system_admin.workflow.{purchase_request,purchase_order,store_requisition}` (grant workflow ต่อประเภท, 2026-09-03), `configuration.app_config`, `configuration.dimension`, `configuration.notification_template`, `system_admin.business_unit`, `system_admin.config_email`, `system_admin.user_activity` ตั้งใจ**ไม่มี resource `interface`** — หน้าจอ interface เป็น licence-only (`LICENSE_ONLY_RESOURCES`)
- **Key ผีฝั่ง frontend ถูกลบ** (FE `b9e2de5f`, `91b2b274`, 2026-09-21): `constant/permissions.ts` เคยประกาศบล็อก `system_configuration.*` และ key อื่นที่ไม่เคยมีอยู่ใน `tb_permission`; ทุกรายการ `/system-admin/*` ตอนนี้ gate ด้วย resource จริง (`system_admin.business_unit`, `.inventory_period`, `.workflow[.<type>]`, `.role`, `.user`, `.running_code`, `.document`, `.user_activity`, `.activity_log`, `.config_email`, `dashboard.dataset`, `configuration.notification_template`) comment บนสุดของ `permissions.ts` ยังบอกว่ามัน mirror endpoint BE `/permissions` — ตอนนี้จริงแล้ว
- **แก้ role picker** (FE `bad71662`, 2026-08-31): resource ระดับโมดูล (ไม่มีจุด — `procurement`, `configuration`, `inventory_management`, `dashboard`, `report`, `system_admin`, …) grant ได้แล้ว และ row ที่มี `audit.deleted` ถูกซ่อน query แคตตาล็อกเองกรอง `deleted_at: null` (`role_permission.service.ts:68-70`)
- **Licence เป็นเลเยอร์ที่สาม ไม่ใช่ RBAC** ตั้งแต่ 2026-08 ทุก URL ของ request ถูก resolve เป็น licence feature (map `ROUTE_*` ใน `permission.route-map.ts` + `LICENSE_ROUTE_OVERRIDES`) และตรวจกับสัญญาของ BU โดย `LicenseInterceptor`; ไม่ผ่านจะได้ `403 LICENSE_REQUIRED` / `LICENSE_EXPIRED` (เฉพาะ write เมื่อหมดอายุ) พร้อม `bu_codes` / `bu_names` key ของ feature ใช้ชื่อ resource ของ permission ซ้ำ (`system_admin.workflow`, `configuration.location`, …) แต่อาจ*ละเอียดกว่า* RBAC — `configuration.email_profile` / `configuration.email_template` มีอยู่เป็น licence feature ขณะที่ RBAC ยังเห็นเป็น `configuration.app_config` / `system_admin.config_email` มุมมอง licence ของผู้ใช้คือ `GET /api/license` (`features[]`, `hidden_features[]`, `expired_features[]` ต่อ BU + union); `BU role = admin` **ไม่** bypass การตรวจ licence
- **ความครอบคลุมของ `PermissionGuard` ยังบางส่วน** `@Permission(...)` ปรากฏบน route decoration 38 จุดที่ HEAD (เช่น `config_vendor-master-certificates.controller.ts:89-200`); ไม่ได้ลงทะเบียนเป็น `APP_GUARD` ระดับ global (`APP_GUARD` ตัวเดียวคือ `ThrottlerGuard`, `app.module.ts:227-228`) route ที่ไม่มี decorator — รวมทั้ง controller `config_application-roles`, `config_user-application-roles`, `config_permissions` และ `config_app-config` ทั้งชุด — **ไม่มีการตรวจ RBAC ต่อผู้ใช้**; ดู [access-control/application-role](/th/inventory/access-control/application-role) หัวข้อ 4

## 1. คืออะไรและใครใช้

Permission คือ **หน่วยเล็กที่สุดของการอนุญาต**: คู่ `(resource, action)` เช่น `resource = "procurement.purchase_request"`, `action = "view"` (คอลัมน์ `resource` เองเป็น string แบบ dot-namespaced เช่น `procurement.purchase_request` หรือ `inventory_management.stock_in` — ไม่ใช่คำนามเปล่า) Permission ถูก catalog ส่วนกลาง (seed script `packages/prisma-shared-schema-platform/prisma/seed.permission.data.ts`) และ **ไม่เคยมอบโดยตรง** ให้ผู้ใช้ — รวบรวมเข้าใน row [access-control/application-role](/th/inventory/access-control/application-role) ผ่าน `tb_application_role_tb_permission` และผู้ใช้ได้รับมันโดยอ้อมจากการได้รับ role

การตรวจสอบ runtime ถูกบังคับโดย backend guard ที่เป็นรูปธรรม ไม่ใช่แค่ join เชิงนามธรรม: route ประกาศ `@Permission({ 'procurement.purchase_request': ['view'] })` (`apps/backend-gateway/src/auth/decorators/permission.decorator.ts`) และ `PermissionGuard` (`apps/backend-gateway/src/auth/guards/permission.guard.ts`) อ่าน grant ที่ resolve แล้วของผู้เรียกจาก header `x-bu-datas` (คำนวณตอน login/BU-switch จาก join `tb_user_tb_application_role` → `tb_application_role` → `tb_application_role_tb_permission`) และตรวจสอบ `hasAllPermissions` User ที่มี `tb_user_tb_business_unit.role = admin` สำหรับ BU นั้น bypass การตรวจสอบทั้งหมด ("god-mode" — ตรงกับ bypass ของ BU-admin ที่ documented ใน [access-control/business-unit-user](/th/inventory/access-control/business-unit-user)) ไม่ใช่ทุก route ที่มี decorator `@Permission` — ถ้าไม่มี `PermissionGuard` จะปล่อยให้ request ผ่านโดยไม่มีเงื่อนไข ดังนั้น endpoint บางตัวไม่มีการตรวจสอบ RBAC เลย (ยืนยันกับ Bruno collection หลายรายการที่ documented ว่า "Permissions: None")

Frontend สะท้อน catalogue นี้เป็น object แบบ dot-notation ที่มี type ใน `constant/permissions.ts` (`PERMISSIONS.procurement.purchase_request.view` เป็นต้น) แทนที่จะเป็น raw string เพียงเพื่อให้ component gate menu item และ route ได้โดยไม่พิมพ์ literal string ผิด; comment นำของ object เองระบุว่ามัน "mirrors the BE `/permissions` endpoint"

**บำรุงรักษาโดย** release migration (seed) **อ่านโดย** UI role-edit สำหรับการ bundle และโดย `PermissionGuard` สำหรับทุก API request ที่ guard

### 1.1 Allowlist client-application App ID — กลไกแยกต่างหาก

Comment thread บนเอกสาร, action ส่วนใหญ่ของ approval-workflow (`approve`/`reject`/`review`/`submit`) และ inbox "my approvals" ข้ามโมดูล **ไม่** ถูก gate ด้วย `tb_permission` / `@Permission` เลย พวกมันพก `@UseGuards(new AppIdGuard('<api name>'))` แทน ซึ่งตรวจสอบ header `x-app-id` ของ request เทียบกับ allowlist snapshot ใน memory (`apps/backend-gateway/src/common/guard/app-allowlist.store.ts`) ที่มาจากตาราง `tb_application` + `tb_application_api` ของ platform schema `x-app-id` ระบุว่า **client application ที่ลงทะเบียนไว้** ตัวไหน (เช่น web SPA, mobile client, integration) กำลังเรียก — แต่ละ row `tb_application` มี `allow_all` (wildcard) หรือรายการชื่อ API ที่อนุญาตชัดเจน — และไม่เกี่ยวข้องกับว่า permission ของ **user** ที่เรียกอนุญาตอะไร request สามารถผ่าน `AppIdGuard` ได้ด้วย user ที่มี permission ครบถ้วนแต่ถูกบล็อกถ้า client ที่เรียกไม่อยู่ใน allowlist สำหรับชื่อ API นั้น และในทางกลับกัน; guard ทั้งสองเป็นอิสระจากกันและ route หนึ่งอาจพกอันใดอันหนึ่ง ทั้งคู่ หรือไม่มีเลย

ชื่อ API ของ comment ใช้ชุด verb เดียวกันในแต่ละประเภทเอกสาร:

| ประเภทเอกสาร | Prefix ชื่อ API ของ comment | Actions |
|---|---|---|
| Purchase Request | `purchaseRequestComment` | `findAll`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Purchase Order | `purchaseOrderComment` | `findAll`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Store Requisition | `storeRequisitionComment` | `findAll`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |

ไม่มี `create` แบบเดี่ยวแยกต่างหาก — `createWithFiles` คือ action create เดียว (คำขอ multipart เดียวที่ post comment พร้อม attachment ใด ๆ ไปด้วยกัน; ยืนยันแล้วว่าไม่มี comment controller ตัวไหน expose endpoint `create` เปล่าเพิ่มเติม)

App ID อื่น ๆ ที่พบบน route approval/workflow:

| ชื่อ API | วัตถุประสงค์ |
|---|---|
| `storeRequisition.approve` | อนุมัติ store requisition ในขั้นตอนการอนุมัติ |
| `storeRequisition.reject` | ปฏิเสธ store requisition ในขั้นตอนการอนุมัติ |
| `storeRequisition.review` | ทำเครื่องหมาย store requisition ว่าผ่านการตรวจสอบ (การกระทำเวิร์กโฟลว์ระดับกลาง) |
| `storeRequisition.submit` | Submit store requisition เข้าสู่ approval workflow ของมัน |
| `my-approve.findAll` | แสดงรายการเอกสารทุกชนิดที่รอการอนุมัติ**ของผู้ใช้ปัจจุบัน** ข้ามประเภทเอกสาร — รองรับ approval inbox ข้ามโมดูล ([dashboard/my-approval](/th/inventory/dashboard/my-approval)) |

ชื่อ API เหล่านี้ถูกลงทะเบียนต่อ client application ผ่าน `tb_application_api` ไม่ได้ถูก bundle เข้า `tb_application_role` — ดู [access-control/application-role](/th/inventory/access-control/application-role) สำหรับ RBAC bundle ต่อ user ตัวจริง

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู catalogue permission | มีแค่ภายใน permission picker ของหน้าจอ Role edit (`routes/system-admin/role/permission-picker.tsx` จัดกลุ่มโดย `permission-catalog.ts`; `permission-matrix.tsx` ถูกลบเมื่อ 2026-08-20) | ไม่มีหน้าจอ permission-list แบบ standalone ใน inventory frontend; API `GET api/config/:bu_code/permissions` |
| ดูว่า BU ถือ licence feature ใดบ้าง | `GET /api/license` | ไม่ใช่ permission — แต่ feature ที่ขาดจะบล็อก route ก่อน RBAC ทำงาน |
| Bundle permission เข้า role | หน้าจอ edit [access-control/application-role](/th/inventory/access-control/application-role) | Checkbox grid; นี่คือเส้นทางปกติ |
| เพิ่ม atom permission ใหม่ | Release migration / seed | `tb_permission` จัดการโดย seed ไม่แก้ผ่าน UI |
| Rename / retire permission | Soft-delete + re-create | Constraint รวม `deleted_at` ดังนั้น `(resource, action)` re-use ได้ |
| หา role ใดรวม permission | Query `tb_application_role_tb_permission` โดย `permission_id` | มีประโยชน์ก่อนการปลดระวาง |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Permission not found" ตอน runtime | Code อ้างอิง permission ที่ถูกลบหรือไม่เคย seed | Re-seed หรือ restore ผ่าน migration |
| Duplicate `(resource, action)` insert | Row ที่ไม่ถูก delete มีอยู่แล้ว | ใช้ row ที่มีอยู่แทน |
| Feature เงียบปิดสำหรับทุกคน | Permission ถูก delete ขณะ code ยังอ้างอิง | Operational guard — restore ผ่าน migration |
| Tooltip สับสนใน role editor | `description` ขาดหายหรือสั้น | Update seed; description ควรอธิบาย *สิ่งที่ permission ปลดล็อก* |
| 401 เด้งไปหน้า login หลัง deploy ที่เปลี่ยนชื่อ `api_name` | ชื่อใน gateway `AppIdGuard` ถูกเปลี่ยนก่อน row ใน `tb_application_api` (เช่น `period.*` → `inventoryPeriod.*`) | Apply platform migration ก่อน; ดู [system-config/period](/th/inventory/system-config/period) |
| `403 LICENSE_REQUIRED` ทั้งที่ role grant permission แล้ว | สัญญาของ BU ไม่มี licence feature ของ route นั้น | เลเยอร์ licence ไม่ใช่ RBAC — ซื้อ/ต่ออายุผ่าน Platform |

## 4. กรณีพิเศษ

- **Closed enumeration** ชุดของ permission ปิดต่อ release — permission ใหม่มาพร้อม code ที่ตรวจสอบ
- **ไม่มี link user โดยตรง** ไม่มี join `tb_user_tb_permission` — ทุกเส้นทางไปผ่าน application role
- **Soft-delete + rename** Constraint รวม `deleted_at` ดังนั้น permission ที่ rename สามารถ soft-delete และ `(resource, action)` re-create
- **วินัย Description** `description` สำหรับ tooltip role-edit — ต้องอธิบาย *สิ่งที่ permission ปลดล็อก* ไม่ใช่แค่ restate คู่

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: platform schema

### 5.1 `tb_permission`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `resource` | `String @db.VarChar` | No | Resource string แบบ dot-namespaced เช่น `procurement.purchase_request`, `inventory_management.stock_in`, `configuration.department` — ไม่ใช่คำนามเปล่า |
| `action` | `String @db.VarChar` | No | Verb (เช่น `view`, `view_department`, `view_all`, `create`, `update`, `delete`, `commit`) |
| `description` | `String?` | Yes | Label และเหตุผลที่อ่านได้ |
| `show_in_mobile` | `Boolean` | No | Default `false` ว่า permission นี้ถูก expose ให้ permission surface ของแอป mobile หรือไม่ |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([resource, action, deleted_at])` Back-relation ไปยัง `tb_application_role_tb_permission` Audit FKs `onDelete: NoAction`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(resource, action)` unique ในกลุ่ม permission ที่ไม่ถูก delete; constraint รวม `deleted_at` เพื่อให้ rename ผ่าน soft-delete + re-create
- **Closed enumeration** Permission ใหม่มาพร้อม code ที่ตรวจสอบ; การ delete เป็น guard *operational* (กระบวนการ release) ไม่บังคับโดย DB
- **ไม่มี link user โดยตรง** ทุกเส้นทางการอนุญาตไปผ่าน `tb_application_role` Source of truth เดียวรักษา audit trail ให้เรียบง่าย
- **วินัย Description** จำเป็นสำหรับ tooltip ของ UI role-edit — ต้องอธิบาย consequences ไม่ใช่แค่ restate คู่

## 7. การอ้างอิงข้าม

- [access-control/application-role](/th/inventory/access-control/application-role) — consumer เดียว
- [access-control/user](/th/inventory/access-control/user) — ถือ permission โดยอ้อมผ่าน role
- ทุกโมดูลธุรกรรม — ทุก route ที่พก decorator `@Permission` resolve กับ `(resource, action)` ผ่าน `PermissionGuard`; route ที่ไม่มี decorator ไม่มีการตรวจสอบ RBAC และ route ของ comment/approval-workflow ถูก gate แยกต่างหากโดย `AppIdGuard` (หัวข้อ 1.1)

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_permission` (`model tb_permission`, บรรทัด 425)
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.permission.data.ts`, `seed.permission.ts`
- **Backend guard:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/decorators/permission.decorator.ts`, `.../auth/guards/permission.guard.ts` (RBAC); `.../common/guard/app-id.guard.ts`, `.../common/guard/app-allowlist.store.ts` (App ID client allowlist, หัวข้อ 1.1); `.../license/{license.interceptor,license-route-resolver,license.evaluator}.ts` + `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` (เลเยอร์ licence)
- **Catalog endpoint:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_permissions/config_permissions.controller.ts` (`GET`, `:50`); service `apps/micro-business/src/authen/role_permission/role_permission.service.ts`; `apps/backend-gateway/src/application/user/user.controller.ts:242-322` (`/api/user/permission`, `/mobile`, `/platform`)
- **Migrations:** `20260916140000_rename_period_to_inventory_period` (platform)
- **Frontend:** Surface ภายใน role-edit ที่ `../carmen-inventory-frontend-react/routes/system-admin/role/permission-picker.tsx` + `permission-catalog.ts` ไม่มี CRUD แบบ standalone แคตตาล็อก key ที่มี type สะท้อนที่ `../carmen-inventory-frontend-react/constant/permissions.ts`; licence hook `hooks/use-license.ts`
