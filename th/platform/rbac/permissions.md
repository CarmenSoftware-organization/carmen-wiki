---
title: Platform RBAC — สิทธิ์ (Permissions)
description: เมทริกซ์ route-guard ของทั้ง SPA, การประกอบกันของ gate ระดับ route/sidebar/ภายในหน้า, อัลกอริทึมการ resolve permission และกรณีพิเศษสำหรับผู้ทดสอบ อัพเดทสำหรับการเปลี่ยนคีย์เป็น platform_role.*, การย้าย route ไป category-permissions และข้อยกเว้น login ของ cluster-admin
published: true
date: 2026-09-06T01:00:00.000Z
tags: book/platform, rbac, permissions
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# Platform RBAC — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** ทุก route ที่ถูก guard มี `requiredPermission="resource.action"` (หรือ `requireSuperAdmin`) บวก prop `feature="<key>"` แบบ optional ตั้งแต่ sync ครั้งก่อนบน `PrivateRoute` &nbsp;·&nbsp; **ลำดับการ resolve (`hasPermission` ที่ gate ทุกตัวใช้):** bootstrap → super-admin → key ระดับแพลตฟอร์ม → key ระดับ cluster — ไม่เปลี่ยนแปลงตั้งแต่ sync ครั้งก่อน &nbsp;·&nbsp; **ข้อยกเว้น bootstrap:** จำนวนผู้ใช้รวม 0 หรือ 1 ⇒ login ข้าม gate ≥1-permission และ `hasPermission` คืน `true` &nbsp;·&nbsp; **login ยังรับ session แบบ cluster-admin เท่านั้นด้วย** (ไม่มี permission ระดับแพลตฟอร์มเลย) นอกกรณี bootstrap — เป็น OR-branch แยกต่างหากตอน `login()` ไม่ใช่ `hasPermission` (ดู §4) &nbsp;·&nbsp; **เมื่อไม่ผ่าน:** หน้า `Forbidden` (`src/pages/Forbidden.tsx`) render ในตำแหน่งเดิมภายใน `<Layout>` (sidebar ยังมองเห็นอยู่, URL ไม่เปลี่ยน); route `/403` โดยตรงก็ render หน้าเดียวกันนี้ &nbsp;·&nbsp; **Gate ภายในหน้า:** `<Can>` ห่อ Add/Edit/Delete บนหน้า list และ edit ของ management ส่วนใหญ่ (key `.create`/`.update`/`.delete` — เฉพาะ Clusters/Business Units เป็นแบบ cluster-scoped); list/edit ของ Roles gate Add/Edit/Delete ด้วย key `platform_role.*` (เปลี่ยนชื่อจาก `role.*` เมื่อ 2026-08-20) และหน้า detail ของ User Platform ใช้ (`user_platform.manage`) &nbsp;·&nbsp; **route ของ Permission Catalog ไม่มี key เลย** — ดู §2.1

## 1. ภาพรวม

หน้านี้คือแผนที่ canonical ว่า permission key gate Platform SPA อย่างไร authorization เกิดขึ้นที่สามชั้นซึ่งใช้ resolver เดียวกัน: **route guard** (prop `requiredPermission` / `requireSuperAdmin` ของ `PrivateRoute` บวก prop `feature` แบบ optional ที่ตรวจสอบเป็นลำดับสุดท้าย — ดู §3), **sidebar filter** (`buildPlatformNav()` ใน `src/components/nav/platformNav.ts` ซ่อน nav item ที่ session ไม่มี `permission` ของมัน — `Layout.tsx` เองเรียกฟังก์ชันนี้อย่างเดียว ไม่ได้นิยาม array ของ nav เองอีกต่อไป) และ **gate ภายในหน้า** (`<Can permission="...">` ห่อปุ่มและฟอร์มรายตัว) ทั้งสามเรียก `AuthContext.hasPermission` ซึ่ง delegate ไปยังฟังก์ชัน pure `checkPermission` เหนือ snapshot `EffectivePermissions` ของ session

ไฟล์ `platformNav.ts` เดียวกันนี้ยัง derive `NAV_RESOURCE_ORDER` (รายการ permission resource ตามลำดับที่ปรากฏใน menu ครั้งแรก) และ export `resourceRank()` ซึ่งจัดอันดับ resource ตามตำแหน่งในลำดับนั้น — resource ที่ไม่มีแถว menu เป็นของตัวเองจะเรียงหลังสุดตามลำดับ catalog ในกลุ่มของตัวเอง **comment ในซอร์สของ `resourceRank()` เองยังระบุ `rbac` และ `license` เป็นตัวอย่าง — `rbac` ล้าสมัยแล้ว**: resource นั้นถูกถอดออกพร้อมกับการเปลี่ยนชื่อ `role.*`→`platform_role.*` (§1) และ `platform_role` ตอนนี้มีแถว menu **Platform Roles** เป็นของตัวเองแล้ว จึงไม่ได้อยู่ท้ายกลุ่มที่ไม่มี menu — มันเรียงตามตำแหน่งของแถวนั้น (ต่อจาก Applications ทันที) เมื่อตรวจสอบทุกจุดที่เรียก `permission`/`requiredPermission`/`hasPermission()` ในทั้ง SPA เทียบกับรายการของ nav เอง resource ที่ไม่มีแถว menu เป็นของตัวเองในปัจจุบันจริง ๆ คือ **`activity_log`** (gate "View History" แบบข้าม module บน Clusters/Business Units/Users) และ **`license`** (key ภายในหน้าของโมดูล Licenses แยกจาก key ระดับ nav `subscription.*` ของโมดูลนั้น) — ไม่มีตัวใดเป็นของโมดูลนี้ `RoleEdit`'s permission grid (§ [UI Screens](/th/platform/rbac/ui-screens)) เรียงตามอันดับนี้ จึงเป็นเหตุผลที่ permission list ของ role อ่านจากบนลงล่างตามลำดับเดียวกับ sidebar ที่ผู้อ่านเพิ่งผ่านมา

มีสอง route ที่เป็น authenticated-only โดยไม่ต้องการ key: `/dashboard` และ `/profile` session ใดที่ผ่าน login เข้าถึงได้ ส่วนที่เหลือทั้งหมดมี key กำกับ — และเนื่องจาก gate ตอน login เองก็กำหนดว่าบัญชีต้องถืออย่างน้อยหนึ่ง permission (หรือ flag super-admin หรือข้อยกเว้น bootstrap) session ที่มี permission เป็นศูนย์จึงเข้าระบบไม่ได้ ณ เวลา login นอกกรณี bootstrap อย่างไรก็ตาม gate ≥1-permission ทำงานเฉพาะภายใน `login()` เท่านั้น: session ที่ถูกถอนสิทธิ์กลางคันยังคง sign in อยู่แม้หลัง refetch snapshot — เพียงแค่จะไม่ผ่านการตรวจสอบ permission ใด ๆ หลังจากนั้น

## 2. เมทริกซ์ของ gate

### 2.1 หน้าจอของโมดูล RBAC

| Route | Component | Guard | Gate ภายในหน้า |
|---|---|---|---|
| `/platform/roles` | `RoleManagement` | `platform_role.read` (`feature="platform_roles"`) | Edit ของแถว gate ด้วย `<Can permission="platform_role.update">`, Delete ของแถว gate ด้วย `<Can permission="platform_role.delete">` **Add Role** (ปุ่ม header และ CTA ของ empty-state) gate ด้วย `<Can permission="platform_role.create">` Export ยังไม่ถูก gate |
| `/platform/roles/new` | `RoleEdit` | `platform_role.create` (`feature="platform_roles"`) | ไม่มี |
| `/platform/roles/:id/edit` | `RoleEdit` | `platform_role.update` (`feature="platform_roles"`) | ปุ่ม header **Edit** คือ `<Can permission="platform_role.update">` |
| `/platform/category-permissions` | `PermissionCatalog` | **ไม่มี** — `<PrivateRoute>` เปล่า ๆ ไม่มี `requiredPermission`/`feature`; ผู้ใช้ platform ที่ login แล้วคนใดก็เปิด route นี้ได้ การเรียก `GET /api-system/platform/permissions` ของหน้าเองถูกบังคับที่ฝั่ง backend ด้วย `platform_role.read` (`RequirePlatformPermission`) ดังนั้น session ที่ไม่มี key นี้จะเข้าถึงหน้าได้แต่การ fetch catalog จะ 403 | ไม่มี (หน้าจอ read-only) |
| `/platform/super-admins` | `SuperAdminManagement` | `requireSuperAdmin` (`feature="super_admins"`) | ไม่มี — มีเพียง super admin เท่านั้นที่เข้าถึงหน้านี้ได้ |
| `/platform/user-platform` | `UserPlatformManagement` | `user_platform.read` (`feature="user_platform"`) | ไม่มี |
| `/platform/user-platform/:userId` | `UserPlatformEdit` | `user_platform.read` | `<Can permission="user_platform.manage">` บน Add Role, ฟอร์ม add-role และปุ่ม Remove ของแต่ละ row |

**เปลี่ยนชื่อเมื่อ 2026-08-20** (`carmen-platform` commit `8df0b10`): key ของ Roles ทุกตัวเปลี่ยนจาก `role.*` เป็น `platform_role.*` และ route ของ Permission Catalog ย้ายจาก `/platform/permissions` (ไม่มีอยู่แล้ว) ไปเป็น `/platform/category-permissions` Edit/Delete ของแถวและ Add Role ในหน้า list ของ Roles ถูก gate ด้วย `<Can>` มาตั้งแต่ 2026-06-10 (เดิมเป็น `role.*` ตอนนี้เป็น `platform_role.*`) — *รูปแบบ* การ gate เองไม่เปลี่ยน เปลี่ยนแค่ string ของ key การลบ role จะสำเร็จหรือไม่ยังคงขึ้นกับการบังคับใช้ `platform_role.delete` ของ backend เอง (ดู §5) — gate ภายในหน้าเป็นเพียงคำแนะนำ เหมือนที่อื่นทุกแห่ง

### 2.2 ส่วนที่เหลือของ SPA

| Route prefix | Guard (list / new / edit) | Gotcha |
|---|---|---|
| `/dashboard`, `/profile` | authenticated เท่านั้น — ไม่มี key | |
| `/clusters` | `cluster.read` / `cluster.create` / `cluster.update` | |
| `/business-units` | `cluster.read` / `cluster.create` / `cluster.update` | **Reuse key `cluster.*`** — ไม่มี key `business_unit.*`; การมอบสิทธิ์เข้าถึง cluster มอบ Business Units ไปด้วย และแยกทั้งสองออกจากกันไม่ได้ |
| `/tenant-migrations` | `cluster.read` | หน้าภาพรวม migration ของทั้งฟลีทแบบ standalone; reuse `cluster.*` เช่นกัน (ไม่ใช่ unit ที่ตั้งชื่อไว้ใน book นี้) |
| `/users` | `user.read` / `user.create` / `user.update` | ต่างจาก `user_platform.*` ซึ่ง gate การ assign role ไม่ใช่ CRUD ของผู้ใช้ |
| `/applications` | `application.read` / `application.create` / `application.update` | |
| `/report-templates` | `report_template.read` / `report_template.create` / `report_template.update` | |
| `/report-form-groups` | `report_template.read` (mutation ผ่าน `report_template.update`/`.create`) | ใหม่เมื่อ 2026-07-23; reuse key ของ Report Templates ไม่มี key ใหม่ |
| `/news` | `news.read` / `news.create` / `news.update` | |
| `/broadcasts/new` | `broadcast.send` | Route เดียว; ไม่มีหน้า list |
| `/sql-workbench` | `sql_workbench.read` | ไม่ใช่ unit ที่ตั้งชื่อไว้ใน book นี้; ยังไม่มีหน้า wiki |

**ถูกลบเมื่อ 2026-07-23/24:** `/print-template-mapping*` และ key `print_template_mapping.*` ไม่มีอยู่แล้ว — โมดูลถูกลบออกจาก carmen-platform เมื่อ 2026-07-24 (commit `de11377`) และแถว permission catalog ที่มันใช้ถูกลบออกจาก seed ของ carmen-turborepo-backend-v2 ก่อนหน้าหนึ่งวัน (commit `c135bb21e`, 2026-07-23); ตอนนี้ `template_type` บวกหน้าจอ [เทมเพลตรายงาน — Form Groups](/th/platform/report-templates/form-groups) ทำหน้าที่แทน

มีสาม route ที่เป็น public เต็มรูปแบบ (ไม่มี `PrivateRoute` เลย): `/` (landing), `/login` และ `/changelog` แหล่งที่มา: `../carmen-platform/src/App.tsx` (block `<Routes>` ฉบับเต็ม) ไม่มี route ใดใน SPA ที่ส่ง key `.delete` เป็น `requiredPermission` — action ของการลบอยู่ภายในหน้า list ซึ่ง management list ทุกหน้า gate ภายในหน้าด้วย `<Can permission="*.delete">` (§3) **รวมถึง Roles ด้วยแล้วตอนนี้** (§2.1) — ข้อความเดิมที่ว่า "มีเพียงหน้า list ของ Roles ที่ยังเปิดเผย Delete" ล้าสมัยแล้ว

## 3. การประกอบกันของ guard

เส้นทางของผู้ใช้ไปสู่ action ใด ๆ ผ่าน gate ได้สูงสุดสามตัว เรียงจากชั้นนอกสุด:

1. **Route guard** — `PrivateRoute` (`src/components/PrivateRoute.tsx` รวม 40 บรรทัด) ถ้า session ไม่ authenticated จะ render `<Navigate to="/login" replace />` ถ้าตั้ง `requiredPermission` และ `hasPermission(requiredPermission)` เป็น false — หรือตั้ง `requireSuperAdmin` และ `isSuperAdmin` เป็น false — จะ render `<Forbidden />` **ในตำแหน่งเดิม** (หน้าเฉพาะ, `src/pages/Forbidden.tsx` — เปลี่ยนชื่อจาก component `AccessDenied` แบบ inline ที่เคยอยู่ในไฟล์เดียวกันนี้) คง URL ไว้เพื่อให้ action "Go Back" ของหน้าไม่เด้งกลับผ่าน guard `Forbidden` render ภายใน shell `<Layout>` ปกติ: ไอคอน `ShieldX`, code "403", หัวข้อ "Access Denied", ข้อความทั่วไป "You don't have permission to access this page." และสอง action — "Go Back" (รู้บริบท fallback ไป `/dashboard` เมื่อไม่มีปลายทางย้อนกลับที่เหมาะสม) และ "Go to Dashboard" route `/403` โดยตรงก็ render หน้าเดียวกันนี้ sidebar ยังมองเห็นอยู่และ session ยังใช้ได้
2. **Sidebar filter** — `ALL_PLATFORM_NAV_ITEMS` ใน `src/components/nav/platformNav.ts` (`Layout.tsx` เรียกแค่ `buildPlatformNav()` ไม่ได้ประกาศ array เองอีกต่อไป) ระบุ `permission: '<key>'` หรือ `superAdminOnly: true` ของแต่ละรายการ แล้ว `buildPlatformNav()` filter: item รอดเฉพาะเมื่อ `(!item.permission || hasPermission(item.permission)) && (!item.superAdminOnly || isSuperAdmin)` และ flag `feature` ของมันไม่ใช่ `hide` item ที่ถูกซ่อนยังเข้าถึงได้โดยตรงผ่าน URL — route guard คือกำแพงจริง sidebar เป็นเพียง UX key ของ sidebar ตรงกับ key ของ route หนึ่งต่อหนึ่งสำหรับ route แบบ list (`platform_role.read`, `user_platform.read`, `cluster.read` ฯลฯ) จึงไม่มีจุดที่รายการที่มองเห็นนำไปสู่ `Forbidden` Permission Catalog ไม่มีรายการ sidebar เลย
3. **Gate ภายในหน้า** — `<Can permission="..." clusterId?>` (`src/components/Can.tsx`) render children ของมันเฉพาะเมื่อ `hasPermission` ผ่าน พร้อม `fallback` แบบ optional (ค่าเริ่มต้น: ไม่มีอะไรเลย) `<Can>` gate Add/Edit/Delete ทั่วหน้า management ส่วนใหญ่ของ SPA: หน้า list (Clusters, Business Units, Users, Applications, Report Templates, News) ห่อปุ่ม Add ด้วย key `.create`, Edit ของ row ด้วย `.update` และ Delete ของ row ด้วย `.delete`; หน้า edit ที่คู่กันห่อ toggle Edit ด้วย `.update` (ถ้าไม่มี มุมมอง detail จะคง read-only ทำให้ไปถึง Save ไม่ได้ — Save เองไม่ถูกห่อ และหน้า edit ไม่มี delete ที่ gate ด้วย `<Can>`); และ BroadcastCompose ห่อ Send ด้วย `broadcast.send` gate ของ Clusters และ Business Units ส่ง `clusterId` (เช่น `<Can permission="cluster.update" clusterId={row.original.id}>`) จึงเข้า branch การ resolve แบบ cluster-specific (§4) — เป็น call site กลุ่มเดียวที่ทำเช่นนั้น ภายในหน้าจอของโมดูล RBAC เอง หน้า list และ editor ของ Roles gate Add/Edit/Delete และ toggle Edit ด้วย key `platform_role.*` (เปลี่ยนชื่อจาก `role.*` เมื่อ 2026-08-20 — รูปแบบการ gate เองไม่เปลี่ยน); หน้า detail ของ User Platform ใช้ `<Can>` สำหรับ `user_platform.manage` (Add Role, ฟอร์ม add-role, Remove ของแต่ละ row); Permission Catalog, Super Admins และหน้า list ของ User Platform ยังคงไม่ถูก gate ภายในหน้า (route guard เป็นกำแพงเดียว — และ route guard ของ Permission Catalog เองก็ไม่มีด้วยซ้ำ ดู §2.1)

ทั้งสามชั้นเรียก `hasPermission(key, opts?)` เดียวกันจาก `AuthContext` — มีอัลกอริทึมการ resolve เพียงหนึ่งเดียว (§4) ดังนั้นผลลัพธ์ของ route, sidebar และภายในหน้าจะไม่มีวันขัดแย้งกันสำหรับ key เดียวกัน สังเกตว่า route guard ไม่เคยส่ง `clusterId` จึงเข้า branch แบบกว้าง "cluster ใดก็ได้ที่มอบ key นี้ผ่าน": role ที่ scope ไว้กับ cluster เดียวยังคงเปิดหน้าจอที่เกี่ยวข้องได้ทั้งแพลตฟอร์มใน SPA ปัจจุบัน และการจำกัด scope ระดับ cluster มีผลกับ call site ของ `<Can clusterId>` และการบังคับใช้ฝั่ง backend

## 4. การไล่ลำดับการ resolve permission

เส้นทางการ resolve ฉบับเต็ม ตั้งแต่ login จนถึงการตรวจสอบครั้งเดียว (แหล่งที่มา: `AuthContext.tsx` `login`/`hasPermission`, `utils/permissions.ts` `checkPermission`):

```
on login(credentials):
    token = POST /api/auth/login                       # unwrap { data: { access_token } }
    store token; set Authorization header

    # ดึงพร้อมกัน (Promise.all)
    eff   = GET /api/user/permission/platform          # EffectivePermissions
    count = GET /api-system/user?page=1&perpage=1      # อ่าน paginate.total
    scope = fetchAdminScope()                          # membership แบบ cluster-admin (ถ้ามี)

    hasAnyPermission = eff exists and (
        eff.is_super_admin
        or eff.platform is non-empty
        or eff.clusters has any key
    )
    # membership แบบ cluster-admin คือสิทธิ์ในตัวเอง แยกจากการตรวจสอบ permission ระดับ
    # แพลตฟอร์มทั้งหมดข้างบน — เพิ่มเข้ามาหลังจาก persona cluster-admin เปิดตัว ถ้าไม่มี
    # branch นี้ ผู้ใช้ที่มีเพียงสิทธิ์นี้จะ login ไม่ได้เลย
    hasClusterAdmin = scope exists and (scope.all or scope.clusters is non-empty)
    isBootstrap = count is not null and count <= 1     # ทางหนีสำหรับ admin คนแรก

    if not hasAnyPermission and not hasClusterAdmin and not isBootstrap:
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

**branch `hasClusterAdmin` มีผลแค่ว่า `login()` จะรับ session หรือไม่ — ไม่เปลี่ยนแปลงอะไรใน `hasPermission`/`checkPermission` ด้านบนเลย** ซึ่งเป็นสิ่งที่ gate ของ route/sidebar/`<Can>` ทุกตัวเรียกจริง ๆ session แบบ cluster-admin เท่านั้นที่ login ด้วยวิธีนี้จะถือ permission ระดับแพลตฟอร์มเป็นศูนย์ ดังนั้น `hasPermission(key)` ทุกครั้งยังคืน `false` สำหรับ session นั้น (นอกกรณี bootstrap) `PrivateRoute` แยกต่างหาก resolve กรณีนี้*ก่อน*การตรวจสอบ permission ของมันเอง แล้ว redirect session แบบนี้ไปที่ `/cluster-admin` แทนที่จะ render `Forbidden` บนทุก route ของ platform (`src/components/PrivateRoute.tsx`: ถ้า `hasPlatformAuthority` เป็น false และ `hasClusterAdminScope` เป็น true จะ `<Navigate to="/cluster-admin" replace />`) หน้าจอของโมดูลนี้เองไม่ได้รับผลกระทบในทางปฏิบัติ — ไม่มีหน้าไหนของโมดูลนี้เข้าถึงได้ผ่านสิทธิ์ admin แบบ cluster-scoped เลย เข้าถึงได้เฉพาะผ่าน grant ของ `platform_role.*`/`user_platform.*`/super-admin เท่านั้น

## 5. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | Login ตอน bootstrap — แพลตฟอร์มมีผู้ใช้รวม 0 หรือ 1 คน | `login()` รับ session ที่มี permission เป็นศูนย์; ทุก `hasPermission` คืน `true` ดังนั้นทุก route, รายการ sidebar และ block `<Can>` เปิดหมด | เส้นทางที่ตั้งใจไว้สำหรับ admin คนแรก: sign in, สร้าง role แล้ว assign ให้ผู้ใช้ — ข้อยกเว้นนี้หยุดมีผลทันทีที่มี row ผู้ใช้คนที่สอง; session ที่ค้างอยู่จะไม่ตรวจสอบ count ซ้ำจนกว่าจะ refresh/login |
| 2 | `userCount` ยังเป็น `null` (การ fetch count ค้างอยู่หรือล้มเหลว) | branch ของ bootstrap ไม่ทำงาน; การตรวจสอบทำงานเข้มงวดกับ snapshot ของ permission | การ fetch count ที่ล้มเหลว fail closed ไม่ใช่ open |
| 3 | session ของ super admin | `is_super_admin` short-circuit ก่อน key list ใด ๆ — แม้ `platform`/`clusters` ว่างเปล่าทุกอย่างก็ผ่าน | อย่า QA ความครอบคลุมของ key จาก session ของ super-admin; มันเผยให้เห็น grant ที่ขาดหายไม่ได้ ทดสอบด้วย session ที่สร้างจาก role แทน |
| 4 | `user_platform.read` โดยไม่มี `user_platform.manage` | หน้า list และ detail โหลดได้; การ์ด Roles & Scope เป็น read-only — Add Role, ฟอร์ม add-role และปุ่ม Remove ไม่ render | test case ของ `<Can>` แบบ canonical; ตรวจสอบว่าปุ่มหายไป ไม่ใช่แค่ถูก disable |
| 5 | `platform_role.read` โดยไม่มี `platform_role.delete` | item Delete ใน dropdown ของหน้า list ของ Roles gate ด้วย `<Can permission="platform_role.delete">` (เปลี่ยนชื่อจาก `role.delete` เมื่อ 2026-08-20) และไม่ render สำหรับ session ที่ไม่มี key นี้ | ตรวจสอบว่า item Delete หายไป ไม่ใช่แค่ถูก disable — เหมือน test pattern ของกรณีพิเศษข้อ 4 การบังคับใช้ `platform_role.delete` ฝั่ง backend ยังคงเป็นขอบเขตจริงไม่ว่ากรณีใด |
| 6 | Permission ถูกถอนกลาง session | snapshot `effectivePermissions` ที่ cache ไว้ยังคงมอบสิทธิ์จนกว่า login ครั้งถัดไปหรือ `AuthProvider` mount จะ refetch | การบังคับใช้ฝั่ง backend คือขอบเขตจริง; snapshot ของ SPA เป็นเพียงคำแนะนำระหว่าง refresh |
| 7 | ต้องการ permission key ใหม่ | catalog เป็น read-only ใน SPA — row `resource.action` ใหม่มาจาก seed/migration ฝั่ง backend และการ redeploy เท่านั้น | feature branch ที่เพิ่ม route ที่ถูก guard ต้องประสานงานการเปลี่ยน catalog ฝั่ง backend; key จะไม่มีอยู่จนกว่าจะถึงตอนนั้น |
| 8 | role ที่ scope ระดับ cluster กับ route ระดับแพลตฟอร์ม | route guard ตรวจสอบโดยไม่มี `clusterId` ดังนั้น grant ของ cluster เดียวใดก็ได้เปิดหน้าจอที่เกี่ยวข้องแบบ global | การจำกัด scope มีผลกับ call site ของ `<Can clusterId>` และการกรองข้อมูลฝั่ง backend ไม่ใช่การเข้าถึง route ของ SPA |
| 9 | **ถูกลบเมื่อ 2026-08-06** (`carmen-platform` commit `19d90c4`) — dev build ไม่มี mock permission set อีกต่อไป | `DEV_MOCK_EFFECTIVE_PERMISSIONS` (key ของ platform ทั้ง 31 ตัว ถูกนำมาใช้แทนเมื่อ backend คืนค่าว่างเปล่าใน `import.meta.env.DEV`) ถูกลบออกทั้งหมด — มันบังเอิญมี shape ตรงกับ permission ของ cluster-admin ที่มีแค่ membership ทุกประการ ขอบเขตนั้นจึงมองไม่เห็นใน dev local และตรวจสอบในเบราว์เซอร์ไม่ได้ dev instance ที่ชี้ไปที่ backend ที่ยังไม่ seed จะ sign in ไม่ได้เลย; DEV ถูก seed ด้วย permission 31 ตัวและ role 5 ตัวมาสักพักแล้ว | อย่าเขียน test plan หรือเอกสาร setup ที่อ้างถึง dev-mode permission mock — ไม่มีอยู่แล้ว ทางหนี bootstrap (`userCount <= 1`) เป็นทางเดียวสำหรับการติดตั้งใหม่ที่ยังไม่มีข้อมูลจริง |
| 10 | การมอบสิทธิ์เข้าถึง cluster | key `cluster.*` เปิด `/business-units*` ด้วย — ไม่มี key `business_unit.*` แยกต่างหาก | รวมหน้าจอ Business Units ไว้ใน test plan ของ cluster-permission ทุกชุด |

## 6. คำแนะนำ

- **ทดสอบต่อ key ไม่ใช่ต่อ persona** สร้าง QA role หนึ่งตัวต่อ permission key (หรือชุด key เล็ก ๆ) และตรวจสอบว่า route, รายการ sidebar และ affordance ภายในหน้า toggle ไปด้วยกัน — พวกมันใช้ resolver เดียวกัน ดังนั้นความแตกต่างบ่งชี้ว่ามี gate ที่ hardcode ไว้
- **เก็บบัญชี QA ที่ไม่ใช่ super-admin ไว้** กรณีพิเศษข้อ 3 ทำให้ session ของ super-admin ไร้ประโยชน์สำหรับการตรวจสอบ grant; สงวน flag ไว้สำหรับทดสอบตัว bypass เองและหน้าจอ `/platform/super-admins`
- **ปฏิบัติกับ gate ของ SPA เป็นเพียงคำแนะนำ** ทุก mutation ที่ SPA ซ่อนไว้หลัง key (`user_platform.manage`, `platform_role.update`/`.delete` และที่เหลือ) ต้องตรวจสอบซ้ำกับ backend ด้วย token ที่ไม่มี key นั้น — การ gate ฝั่ง client อย่างเดียวไม่ใช่ security boundary
- **เมื่อเพิ่ม feature ที่ถูก guard** ให้ลงทะเบียนทั้งสามชั้นพร้อมกัน: row ใน catalog (backend), `requiredPermission` บน route และ field `permission` ของ sidebar — บวก `<Can>` สำหรับ action ใดที่แคบกว่า key ของ route ปฏิบัติตามการตั้งชื่อ `resource.action` ของ catalog ที่มีอยู่
- **ตัดสินใจเรื่อง `business_unit.*` อย่างจงใจ** ถ้า Business Units ต้องการ gate อิสระเมื่อใด ต้องมี key ใหม่บวกการอัพเดท route/sidebar; จนกว่าจะถึงตอนนั้น ให้ document การ reuse `cluster.*` ใน test plan แทนที่จะปฏิบัติกับมันเหมือน bug

**e2e ล้าสมัย ไม่ใช่หลักฐาน:** `../carmen-platform-e2e/tests/permission-catalog/permission-catalog.spec.ts` ไปที่ route `/platform/permissions` ซึ่งไม่มีอยู่แล้ว (ย้ายเป็น `/platform/category-permissions` เมื่อ 2026-08-20) — ทุกเทสต์ในสเปกนี้พังกับซอร์สปัจจุบัน `../carmen-platform-e2e/tests/roles/role-crud.spec.ts` (และ page object `pages/RoleEditPage.ts`) ควบคุมตัวเลือก permission เป็น **checkbox** ("toggle the `cluster.read` permission checkbox") — `PermissionGrid` ปัจจุบัน (2026-08-20, `carmen-platform` commit `42eeafe`) ใช้ปุ่ม toggle `aria-pressed` ไม่ใช่ checkbox แล้ว selector เดิมจึงไม่ match `pages/RoleManagementPage.ts` เองมี comment ระบุว่า "Name cell เป็น `<button>`... ไม่ใช่ link" ซึ่งขัดกับซอร์สปัจจุบันที่ Name cell เป็น `<Link>` ทั้งสามไฟล์นี้ลงวันที่ `bb8f671` (2026-06-11) ก่อนการเปลี่ยนแปลงทุกอย่างในหน้านี้ ตามหลักการของ resync นี้ implementation ชนะ; สเปกทั้งสามต้องการการดูแลรักษาซึ่งอยู่นอกขอบเขตของ sync ครั้งนี้

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard) · `src/components/PrivateRoute.tsx` (guard) · `src/pages/Forbidden.tsx` (หน้า 403) · `src/components/nav/platformNav.ts` (array ของ sidebar, `buildPlatformNav()`, `NAV_RESOURCE_ORDER`/`resourceRank()`) · `src/components/Can.tsx` · `src/context/AuthContext.tsx` (`login`, `hasPermission`, `hasPlatformAuthority`, `hasClusterAdminScope`) · `src/utils/permissions.ts` (`checkPermission`, `checkPlatformAuthority`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-permissions/platform-permissions.controller.ts` (การบังคับ `platform_role.read` บน endpoint ของ catalog)
**Cross-link:** [หน้า landing ของ Platform RBAC](/th/platform/rbac) &nbsp;·&nbsp; [Data Model](/th/platform/rbac/data-model) &nbsp;·&nbsp; [UI Screens](/th/platform/rbac/ui-screens)
