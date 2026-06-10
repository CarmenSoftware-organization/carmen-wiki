---
title: Platform RBAC — สิทธิ์ (Permissions)
description: เมทริกซ์ route-guard ของทั้ง SPA, การประกอบกันของ gate ระดับ route/sidebar/ภายในหน้า, อัลกอริทึมการ resolve permission และกรณีพิเศษสำหรับผู้ทดสอบ
published: true
date: 2026-06-10T15:00:00.000Z
tags: book/platform, rbac, permissions
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# Platform RBAC — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** ทุก route ที่ถูก guard มี `requiredPermission="resource.action"` (หรือ `requireSuperAdmin`) บน `PrivateRoute` &nbsp;·&nbsp; **ลำดับการ resolve:** bootstrap → super-admin → key ระดับแพลตฟอร์ม → key ระดับ cluster &nbsp;·&nbsp; **ข้อยกเว้น bootstrap:** จำนวนผู้ใช้รวม 0 หรือ 1 ⇒ login ข้าม gate ≥1-permission และ `hasPermission` คืน `true` &nbsp;·&nbsp; **เมื่อไม่ผ่าน:** `<AccessDenied>` ภายใน `<Layout>` (sidebar ยังมองเห็นอยู่) &nbsp;·&nbsp; **Gate ภายในหน้า:** `<Can>` ห่อ Add/Edit/Delete บนหน้า list และ edit ของ management ส่วนใหญ่ (key `.create`/`.update`/`.delete` — เฉพาะ Clusters/Business Units เป็นแบบ cluster-scoped); ภายในหน้าจอของโมดูล RBAC เองมีเพียงหน้า detail ของ User Platform ที่ใช้ (`user_platform.manage`)

## 1. ภาพรวม

หน้านี้คือแผนที่ canonical ว่า permission key gate Platform SPA อย่างไร authorization เกิดขึ้นที่สามชั้นซึ่งใช้ resolver เดียวกัน: **route guard** (prop `requiredPermission` / `requireSuperAdmin` ของ `PrivateRoute`), **sidebar filter** (`Layout.tsx` ซ่อน nav item ที่ session ไม่มี `permission` ของมัน) และ **gate ภายในหน้า** (`<Can permission="...">` ห่อปุ่มและฟอร์มรายตัว) ทั้งสามเรียก `AuthContext.hasPermission` ซึ่ง delegate ไปยังฟังก์ชัน pure `checkPermission` เหนือ snapshot `EffectivePermissions` ของ session

มีสอง route ที่เป็น authenticated-only โดยไม่ต้องการ key: `/dashboard` และ `/profile` session ใดที่ผ่าน login เข้าถึงได้ ส่วนที่เหลือทั้งหมดมี key กำกับ — และเนื่องจาก gate ตอน login เองก็กำหนดว่าบัญชีต้องถืออย่างน้อยหนึ่ง permission (หรือ flag super-admin หรือข้อยกเว้น bootstrap) session ที่มี permission เป็นศูนย์จึงเข้าระบบไม่ได้ ณ เวลา login นอกกรณี bootstrap อย่างไรก็ตาม gate ≥1-permission ทำงานเฉพาะภายใน `login()` เท่านั้น: session ที่ถูกถอนสิทธิ์กลางคันยังคง sign in อยู่แม้หลัง refetch snapshot — เพียงแค่จะไม่ผ่านการตรวจสอบ permission ใด ๆ หลังจากนั้น

## 2. เมทริกซ์ของ gate

### 2.1 หน้าจอของโมดูล RBAC

| Route | Component | Guard | Gate ภายในหน้า |
|---|---|---|---|
| `/platform/roles` | `RoleManagement` | `role.read` | ไม่มี — Add/Edit/Delete/Export มองเห็นได้สำหรับทุกผู้ถือ `role.read` |
| `/platform/roles/new` | `RoleEdit` | `role.create` | ไม่มี |
| `/platform/roles/:id/edit` | `RoleEdit` | `role.update` | ไม่มี |
| `/platform/permissions` | `PermissionCatalog` | `role.read` | ไม่มี (หน้าจอ read-only) |
| `/platform/super-admins` | `SuperAdminManagement` | `requireSuperAdmin` | ไม่มี |
| `/platform/user-platform` | `UserPlatformManagement` | `user_platform.read` | ไม่มี |
| `/platform/user-platform/:userId` | `UserPlatformEdit` | `user_platform.read` | `<Can permission="user_platform.manage">` บน Add Role, ฟอร์ม add-role และปุ่ม Remove ของแต่ละ row |

สังเกตว่า action **Delete** ของหน้า list ของ Roles ไม่ถูก gate แยกต่างหาก — `role.read` เพียงพอที่จะเห็นและคลิกมัน ต่างจาก management list อื่น ๆ ที่ห่อ Delete ด้วย `<Can permission="*.delete">` (§3) การลบ role จะสำเร็จหรือไม่ขึ้นกับการบังคับใช้ `role.delete` ของ backend (ดู §5)

### 2.2 ส่วนที่เหลือของ SPA

| Route prefix | Guard (list / new / edit) | Gotcha |
|---|---|---|
| `/dashboard`, `/profile` | authenticated เท่านั้น — ไม่มี key | |
| `/clusters` | `cluster.read` / `cluster.create` / `cluster.update` | |
| `/business-units` | `cluster.read` / `cluster.create` / `cluster.update` | **Reuse key `cluster.*`** — ไม่มี key `business_unit.*`; การมอบสิทธิ์เข้าถึง cluster มอบ Business Units ไปด้วย และแยกทั้งสองออกจากกันไม่ได้ |
| `/users` | `user.read` / `user.create` / `user.update` | ต่างจาก `user_platform.*` ซึ่ง gate การ assign role ไม่ใช่ CRUD ของผู้ใช้ |
| `/applications` | `application.read` / `application.create` / `application.update` | |
| `/report-templates` | `report_template.read` / `report_template.create` / `report_template.update` | |
| `/print-template-mapping` | `print_template_mapping.read` / `print_template_mapping.create` / `print_template_mapping.update` | |
| `/news` | `news.read` / `news.create` / `news.update` | |
| `/broadcasts/new` | `broadcast.send` | Route เดียว; ไม่มีหน้า list |

มีสาม route ที่เป็น public เต็มรูปแบบ (ไม่มี `PrivateRoute` เลย): `/` (landing), `/login` และ `/changelog` แหล่งที่มา: `../carmen-platform/src/App.tsx` (block `<Routes>` ฉบับเต็ม บรรทัด 48–301) ไม่มี route ใดใน SPA ที่ส่ง key `.delete` เป็น `requiredPermission` — action ของการลบอยู่ภายในหน้า list ซึ่ง management list ทุกหน้ายกเว้น Roles gate ภายในหน้าด้วย `<Can permission="*.delete">` (§3) มีเพียงหน้า list ของ Roles ที่ยังเปิดเผย Delete ให้ทุกคนที่ถือ guard `.read` ของมัน (§2.1)

## 3. การประกอบกันของ guard

เส้นทางของผู้ใช้ไปสู่ action ใด ๆ ผ่าน gate ได้สูงสุดสามตัว เรียงจากชั้นนอกสุด:

1. **Route guard** — `PrivateRoute` (`src/components/PrivateRoute.tsx`) ถ้า session ไม่ authenticated จะ render `<Navigate to="/login" replace />` ถ้าตั้ง `requiredPermission` และ `hasPermission(requiredPermission)` เป็น false — หรือตั้ง `requireSuperAdmin` และ `isSuperAdmin` เป็น false — จะ render `<AccessDenied />` ซึ่งเป็นการ์ดภายใน shell `<Layout>` ปกติ (ไอคอนโล่, "Access Denied", "You don't have permission to access this page.", ปุ่ม Back-to-Dashboard) sidebar ยังมองเห็นอยู่และ session ยังใช้ได้
2. **Sidebar filter** — `Layout.tsx` ประกาศ `allNavItems` โดยแต่ละรายการอาจมี `permission: '<key>'` หรือ `superAdminOnly: true` แล้ว filter: item รอดเฉพาะเมื่อ `(!item.permission || hasPermission(item.permission)) && (!item.superAdminOnly || isSuperAdmin)` item ที่ถูกซ่อนยังเข้าถึงได้โดยตรงผ่าน URL — route guard คือกำแพงจริง sidebar เป็นเพียง UX key ของ sidebar ตรงกับ key ของ route หนึ่งต่อหนึ่งสำหรับ route แบบ list (`role.read`, `user_platform.read`, `cluster.read` ฯลฯ) จึงไม่มีจุดที่รายการที่มองเห็นนำไปสู่ `AccessDenied` Permission Catalog ไม่มีรายการ sidebar เลย
3. **Gate ภายในหน้า** — `<Can permission="..." clusterId?>` (`src/components/Can.tsx`) render children ของมันเฉพาะเมื่อ `hasPermission` ผ่าน พร้อม `fallback` แบบ optional (ค่าเริ่มต้น: ไม่มีอะไรเลย) `<Can>` gate Add/Edit/Delete ทั่วหน้า management ส่วนใหญ่ของ SPA: หน้า list (Clusters, Business Units, Users, Applications, Report Templates, Print Template Mapping, News) ห่อปุ่ม Add ด้วย key `.create`, Edit ของ row ด้วย `.update` และ Delete ของ row ด้วย `.delete`; หน้า edit ที่คู่กันห่อ toggle Edit ด้วย `.update` (ถ้าไม่มี มุมมอง detail จะคง read-only ทำให้ไปถึง Save ไม่ได้ — Save เองไม่ถูกห่อ และหน้า edit ไม่มี delete ที่ gate ด้วย `<Can>`); และ BroadcastCompose ห่อ Send ด้วย `broadcast.send` gate ของ Clusters และ Business Units ส่ง `clusterId` (เช่น `<Can permission="cluster.update" clusterId={row.original.id}>`) จึงเข้า branch การ resolve แบบ cluster-specific (§4) — เป็น call site กลุ่มเดียวที่ทำเช่นนั้น ภายในหน้าจอของโมดูล RBAC เอง มีเพียงหน้า detail ของ User Platform ที่ใช้ `<Can>` (`user_platform.manage` บน Add Role, ฟอร์ม add-role และ Remove ของแต่ละ row); หน้า list ของ Roles, editor ของ Role, Permission Catalog, Super Admins และหน้า list ของ User Platform เปิดเผย action ทั้งหมดให้ทุกคนที่ผ่าน route guard

ทั้งสามชั้นเรียก `hasPermission(key, opts?)` เดียวกันจาก `AuthContext` — มีอัลกอริทึมการ resolve เพียงหนึ่งเดียว (§4) ดังนั้นผลลัพธ์ของ route, sidebar และภายในหน้าจะไม่มีวันขัดแย้งกันสำหรับ key เดียวกัน สังเกตว่า route guard ไม่เคยส่ง `clusterId` จึงเข้า branch แบบกว้าง "cluster ใดก็ได้ที่มอบ key นี้ผ่าน": role ที่ scope ไว้กับ cluster เดียวยังคงเปิดหน้าจอที่เกี่ยวข้องได้ทั้งแพลตฟอร์มใน SPA ปัจจุบัน และการจำกัด scope ระดับ cluster มีผลกับ call site ของ `<Can clusterId>` และการบังคับใช้ฝั่ง backend

## 4. การไล่ลำดับการ resolve permission

เส้นทางการ resolve ฉบับเต็ม ตั้งแต่ login จนถึงการตรวจสอบครั้งเดียว (แหล่งที่มา: `AuthContext.tsx` `login`/`hasPermission`, `utils/permissions.ts` `checkPermission`):

```
on login(credentials):
    token = POST /api/auth/login                       # unwrap { data: { access_token } }
    store token; set Authorization header

    eff   = GET /api/user/permission/platform          # EffectivePermissions
    count = GET /api-system/user?page=1&perpage=1      # อ่าน paginate.total

    hasAnyPermission = eff exists and (
        eff.is_super_admin
        or eff.platform is non-empty
        or eff.clusters has any key
    )
    isBootstrap = count is not null and count <= 1     # ทางหนีสำหรับ admin คนแรก

    if not hasAnyPermission and not isBootstrap:
        tear down the partial session (drop token, permissions, header)
        return "Access Denied. You are not authorized to access this platform."

    persist session; cache eff in localStorage["effectivePermissions"]


function hasPermission(key, opts?):                    # AuthContext — ใช้โดย gate ทุกตัว
    # 1. ทางหนี bootstrap: ผู้ใช้ 0-1 คน => อนุญาตทุกอย่าง
    if userCount is not null and userCount <= 1:
        return true
    return checkPermission(effectivePermissions, key, opts)


function checkPermission(eff, key, opts?):             # pure function, utils/permissions.ts
    if eff is null:
        return false
    # 2. Super-admin bypass — ตรวจสอบก่อน key list ใด ๆ
    if eff.is_super_admin:
        return true
    # 3. สิทธิ์ระดับแพลตฟอร์มใช้ได้ทุกที่
    if key in eff.platform:
        return true
    # 4a. การตรวจสอบแบบ cluster-specific: นับเฉพาะสิทธิ์ของ cluster นั้น
    if opts.clusterId is set:
        return key in eff.clusters[opts.clusterId]
    # 4b. การตรวจสอบแบบกว้าง (ไม่มี clusterId): cluster ใดก็ได้ที่มอบ key นี้ผ่าน
    return any cluster_keys in eff.clusters where key in cluster_keys
```

snapshot `EffectivePermissions` ถูก fetch ตอน login และอีกครั้งทุกครั้งที่ `AuthProvider` mount (refresh หน้า) โดยใช้สำเนาใน `localStorage` เป็นค่าเริ่มต้นระหว่างที่ refetch กำลังทำงาน `userCount` เป็น `null` จนกว่าการ fetch ของมันจะ resolve; branch ของ bootstrap ต้องการ count ที่ไม่เป็น null ดังนั้นในช่วงหน้าต่างการโหลด การตรวจสอบจะถูกบังคับใช้อย่างเข้มงวด

## 5. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | Login ตอน bootstrap — แพลตฟอร์มมีผู้ใช้รวม 0 หรือ 1 คน | `login()` รับ session ที่มี permission เป็นศูนย์; ทุก `hasPermission` คืน `true` ดังนั้นทุก route, รายการ sidebar และ block `<Can>` เปิดหมด | เส้นทางที่ตั้งใจไว้สำหรับ admin คนแรก: sign in, สร้าง role แล้ว assign ให้ผู้ใช้ — ข้อยกเว้นนี้หยุดมีผลทันทีที่มี row ผู้ใช้คนที่สอง; session ที่ค้างอยู่จะไม่ตรวจสอบ count ซ้ำจนกว่าจะ refresh/login |
| 2 | `userCount` ยังเป็น `null` (การ fetch count ค้างอยู่หรือล้มเหลว) | branch ของ bootstrap ไม่ทำงาน; การตรวจสอบทำงานเข้มงวดกับ snapshot ของ permission | การ fetch count ที่ล้มเหลว fail closed ไม่ใช่ open |
| 3 | session ของ super admin | `is_super_admin` short-circuit ก่อน key list ใด ๆ — แม้ `platform`/`clusters` ว่างเปล่าทุกอย่างก็ผ่าน | อย่า QA ความครอบคลุมของ key จาก session ของ super-admin; มันเผยให้เห็น grant ที่ขาดหายไม่ได้ ทดสอบด้วย session ที่สร้างจาก role แทน |
| 4 | `user_platform.read` โดยไม่มี `user_platform.manage` | หน้า list และ detail โหลดได้; การ์ด Roles & Scope เป็น read-only — Add Role, ฟอร์ม add-role และปุ่ม Remove ไม่ render | test case ของ `<Can>` แบบ canonical; ตรวจสอบว่าปุ่มหายไป ไม่ใช่แค่ถูก disable |
| 5 | `role.read` โดยไม่มี `role.delete` | item Delete ใน dropdown ของหน้า list ของ Roles ยังมองเห็นและคลิกได้ — ไม่มี gate `.delete` ฝั่ง client | คาดหวังให้ backend ปฏิเสธและ SPA แสดง error toast; ถ้าการลบสำเร็จ นั่นคือช่องโหว่ authorization ฝั่ง backend ไม่ใช่พฤติกรรมที่ตั้งใจ |
| 6 | Permission ถูกถอนกลาง session | snapshot `effectivePermissions` ที่ cache ไว้ยังคงมอบสิทธิ์จนกว่า login ครั้งถัดไปหรือ `AuthProvider` mount จะ refetch | การบังคับใช้ฝั่ง backend คือขอบเขตจริง; snapshot ของ SPA เป็นเพียงคำแนะนำระหว่าง refresh |
| 7 | ต้องการ permission key ใหม่ | catalog เป็น read-only ใน SPA — row `resource.action` ใหม่มาจาก seed/migration ฝั่ง backend และการ redeploy เท่านั้น | feature branch ที่เพิ่ม route ที่ถูก guard ต้องประสานงานการเปลี่ยน catalog ฝั่ง backend; key จะไม่มีอยู่จนกว่าจะถึงตอนนั้น |
| 8 | role ที่ scope ระดับ cluster กับ route ระดับแพลตฟอร์ม | route guard ตรวจสอบโดยไม่มี `clusterId` ดังนั้น grant ของ cluster เดียวใดก็ได้เปิดหน้าจอที่เกี่ยวข้องแบบ global | การจำกัด scope มีผลกับ call site ของ `<Can clusterId>` และการกรองข้อมูลฝั่ง backend ไม่ใช่การเข้าถึง route ของ SPA |
| 9 | dev build ที่ response ของ permission ว่างเปล่า | `DEV_MOCK_EFFECTIVE_PERMISSIONS` (key ของ platform-management ทั้งหมด, `is_super_admin: false`) ถูกนำมาใช้แทนเฉพาะใน `import.meta.env.DEV` | ไม่เคยทำงานใน production build; อย่าตีความการเข้าถึงในโหมด dev ว่าเป็น grant |
| 10 | การมอบสิทธิ์เข้าถึง cluster | key `cluster.*` เปิด `/business-units*` ด้วย — ไม่มี key `business_unit.*` แยกต่างหาก | รวมหน้าจอ Business Units ไว้ใน test plan ของ cluster-permission ทุกชุด |

## 6. คำแนะนำ

- **ทดสอบต่อ key ไม่ใช่ต่อ persona** สร้าง QA role หนึ่งตัวต่อ permission key (หรือชุด key เล็ก ๆ) และตรวจสอบว่า route, รายการ sidebar และ affordance ภายในหน้า toggle ไปด้วยกัน — พวกมันใช้ resolver เดียวกัน ดังนั้นความแตกต่างบ่งชี้ว่ามี gate ที่ hardcode ไว้
- **เก็บบัญชี QA ที่ไม่ใช่ super-admin ไว้** กรณีพิเศษข้อ 3 ทำให้ session ของ super-admin ไร้ประโยชน์สำหรับการตรวจสอบ grant; สงวน flag ไว้สำหรับทดสอบตัว bypass เองและหน้าจอ `/platform/super-admins`
- **ปฏิบัติกับ gate ของ SPA เป็นเพียงคำแนะนำ** ทุก mutation ที่ SPA ซ่อนไว้หลัง key (`user_platform.manage`, Delete ของ role ที่ไม่มี gate) ต้องตรวจสอบซ้ำกับ backend ด้วย token ที่ไม่มี key นั้น — การ gate ฝั่ง client อย่างเดียวไม่ใช่ security boundary
- **เมื่อเพิ่ม feature ที่ถูก guard** ให้ลงทะเบียนทั้งสามชั้นพร้อมกัน: row ใน catalog (backend), `requiredPermission` บน route และ field `permission` ของ sidebar — บวก `<Can>` สำหรับ action ใดที่แคบกว่า key ของ route ปฏิบัติตามการตั้งชื่อ `resource.action` ของ catalog ที่มีอยู่
- **ตัดสินใจเรื่อง `business_unit.*` อย่างจงใจ** ถ้า Business Units ต้องการ gate อิสระเมื่อใด ต้องมี key ใหม่บวกการอัพเดท route/sidebar; จนกว่าจะถึงตอนนั้น ให้ document การ reuse `cluster.*` ใน test plan แทนที่จะปฏิบัติกับมันเหมือน bug

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard) · `src/components/PrivateRoute.tsx` (guard + AccessDenied) · `src/components/Layout.tsx` (sidebar filter บรรทัด 49–71) · `src/components/Can.tsx` · `src/context/AuthContext.tsx` (`login` บรรทัด 115–188, `hasPermission` บรรทัด 210–214) · `src/utils/permissions.ts` (`checkPermission`, dev mock)
**Cross-link:** [หน้า landing ของ Platform RBAC](/th/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md)
