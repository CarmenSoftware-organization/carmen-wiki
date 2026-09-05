---
title: ผู้ใช้แพลตฟอร์ม — หน้าจอ UI (UI Screens)
description: ทะเบียนของ UserPlatformManagement (PlatformAccessSummary, RoleChips, Grant Access) และแฟ้มรายบุคคลของ UserPlatformEdit (AccessReachBand, RoleGrantList, MembershipCard) พร้อมสองจุดที่ e2e suite ของ user-platform ไม่ตรงกับ UI นี้แล้ว
published: true
date: '2026-09-06T19:00:00.000Z'
tags: book/platform, user-platform, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ใช้แพลตฟอร์ม — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `UserPlatformManagement` (`/platform/user-platform`) &nbsp;·&nbsp; `UserPlatformEdit` (`/platform/user-platform/:userId` ไม่มี `/edit` ต่อท้าย — ดู [Landing](/th/platform/user-platform) §1) &nbsp;·&nbsp; **เปลือกที่ใช้ร่วมกัน:** `Layout`, `PageHeader`, `DevDebugSheet` เฉพาะตอน dev บนทั้งสองหน้าจอ, `useGlobalShortcuts` &nbsp;·&nbsp; **e2e suite:** `user-platform` (2 specs, `../carmen-platform-e2e`, HEAD `a8e3b31`, 2026-08-25) — **ทั้งสอง spec มีมาก่อนการเขียนใหม่เมื่อ 2026-09-02 และไม่ตรงกับ markup ปัจจุบันแล้ว** — ดู §4

## 1. ภาพรวม

ทั้งสองหน้าจอตามรูปแบบ Management/Edit ที่หนังสือเล่มนี้ใช้ทั่วไป แต่ไม่มีหน้าไหนเป็นฟอร์มเลย: `UserPlatformManagement` เป็นรายการทะเบียนที่ไม่มี action สร้าง record ใหม่ (Grant Access มอบ role ให้ผู้ใช้ที่มีอยู่แล้ว ไม่ได้สร้างผู้ใช้ใหม่) และ `UserPlatformEdit` ไม่มีสวิตช์ edit-mode เลย — ทุก action บนหน้านี้ (เพิ่ม role, ลบ role) เขียนทันที ไม่มีอะไรให้ "Save" ทั้งสองหน้าจอใช้การแสดงผลตอนโหลดแบบ `TableSkeleton`/`Skeleton` ร่วมกัน ไม่ใช่ spinner, `DevDebugSheet` เฉพาะ dev ที่แสดง raw API response, และ `useGlobalShortcuts` สำหรับ focus ช่องค้นหา (รายการ) หรือ save/cancel (sheet ของ Add Role)

ทั้งสองหน้าจอใช้คำศัพท์เล็ก ๆ ชุดเดียวกันสำหรับ "สิทธิ์นี้ครอบคลุมแค่ไหน": `ScopeRail` (แท่งสีบาง ๆ ทึบเมื่อเป็นทั้งแพลตฟอร์ม เป็นเส้นขอบเมื่อเฉพาะ cluster) และการจับคู่ label "Platform-wide"/ชื่อ cluster นิยามไว้ที่เดียวใน `userPlatformManagement/roleChips.tsx` แล้ว import ไปใช้ทั้งใน `userPlatformEdit/AccessReachBand.tsx` และ `userPlatformEdit/RoleGrantList.tsx` ผู้ตรวจสอบที่ย้ายจากหน้ารายการไปหน้าของผู้ถือสิทธิ์คนหนึ่งจึงอ่านภาษาภาพเดียวกัน ไม่ใช่สองแบบที่ออกแบบแยกกัน

## 2. `UserPlatformManagement` — ทะเบียน (`/platform/user-platform`)

`DataTable` แบบ server-side (`serverSide`, `tableLayout="auto"`) มีสี่คอลัมน์ตามลำดับ: **User** (ไม่มี avatar — บรรทัดชื่อ/username บวกบรรทัดอีเมลที่ตัดข้อมูลซ้ำออกแล้ว, badge `Inactive` เมื่อเข้าเงื่อนไข), **Roles & scope** (`RoleChips` — จัดกลุ่ม assignment ตาม scope กลุ่มทั้งแพลตฟอร์มขึ้นก่อน แต่ละกลุ่มเขียนชื่อ scope ครั้งเดียวข้าง badge ของ role ไม่เขียนซ้ำต่อ badge), **Granted** (เวลาสัมพัทธ์ + tooltip เวลาแน่นอนของ assignment ที่*สร้างล่าสุด* บวกผู้ให้ grant นั้น — การระบุผู้ให้รายตัวมีเฉพาะบนหน้า detail), และคอลัมน์ row-actions (เมนู kebab: **Manage roles** ไม่นำทางไปหน้า detail; **Revoke all access** กั้นด้วย `<Can permission="user_platform.manage">` เฉพาะผู้ถือสิทธิ์ที่มี role ให้เพิกถอน)

เหนือตาราง **`PlatformAccessSummary`** แสดงค่าสรุปทั้งทะเบียน ([Landing](/th/platform/user-platform) §3.1): จำนวนผู้ถือสิทธิ์ตัวใหญ่, แท่งสัดส่วนทั้งแพลตฟอร์ม/เฉพาะ cluster (เป็นของตกแต่ง — ทุกตัวเลขที่มันสื่อยังเขียนไว้ใน legend ข้างใต้ด้วย) และคำเตือนผู้ถือสิทธิ์ที่ไม่ active ที่กดแล้วใส่ filter ให้ทันที ช่อง legend ของทั้งแพลตฟอร์มก็กดได้เช่นกัน (สลับ filter `cluster_id: null`) ส่วนช่อง cluster-scoped เป็นแค่ตัวเลขนิ่ง ๆ โดยตั้งใจ — คอมเมนต์ในโค้ดอธิบายว่าทำไม: filter แบบ "cluster ไหนก็ได้" ต้องใช้ query `{ not: null }` ที่ backend ไม่เคยรับมาก่อน จึงเลือกให้เป็นตัวเลขที่อ่านตรงไปตรงมา ดีกว่าตัวควบคุมที่อาจกรองไม่ได้อะไรเลยแบบเงียบ ๆ

chrome มาตรฐานด้านล่างนั้น: ช่องค้นหาแบบ debounce (username/email), Filters sheet (สถานะ, role — ปุ่ม multi-select ที่ป้อนจาก `roleService.getAll()` แบบ best-effort ถ้าดึงไม่สำเร็จก็ตกไปใช้ role id ดิบ ๆ — และ scope, `<select>` ของ "Any scope" / "Platform-wide" / หนึ่งตัวเลือกต่อ cluster จาก `clusterService.getAll()`), chip ของ filter ที่ใช้งานอยู่พร้อมลบทีละอันหรือลบทั้งหมด และ CSV export export เป็น**รายแถวต่อ assignment ไม่ใช่ต่อผู้ถือสิทธิ์** — ผู้ใช้ที่มีสาม role จะได้สามแถวใน CSV หนึ่งแถวต่อคู่ role/scope เพราะ "spreadsheet cell กรองหลาย role พร้อมกันไม่ได้" (คอมเมนต์ในโค้ดเอง) คอลัมน์คือ username, email, สถานะ, role, scope, เวลาที่มอบ, ผู้มอบ

**Grant Access** (ปุ่มใน header และปุ่มเรียกร้องใน empty state ทั้งคู่ `<Can permission="user_platform.manage">`) เปิด `GrantAccessDialog`: ช่องค้นหาแบบ typeahead `UserPicker` (ค้นหาผ่าน `GET /api-system/user` กั้นด้วย `user.read` ฝั่ง backend — ดู [Permissions](/th/platform/user-platform/permissions) §3), checkbox list ของ role แพลตฟอร์ม และ scope เดียวที่ใช้ร่วมกัน (ทั้งแพลตฟอร์มหรือ cluster ที่ระบุ) ใช้กับทุก role ที่ติ๊กพร้อมกันผ่าน `POST .../roles/bulk` 409 จาก role ที่มอบไปแล้วจะถูกจับคู่กลับไปยัง checkbox ของมันด้วยการเทียบ substring ง่าย ๆ กับข้อความ error (`roleOptions.filter(r => message.includes(r.name))`) แล้วทำเป็นสีแดง — เป็นความสะดวกด้าน display ไม่ใช่การตรวจสอบที่ backend ทำทีละ role จริง ๆ

**Revoke all access** ไม่มี bulk-revoke endpoint เฉพาะฝั่ง backend: มันคือ loop ฝั่ง client ที่เรียก `DELETE .../roles/:assignmentId` ทีละครั้ง แล้วรายงานตรง ๆ ว่า role ไหนล้มเหลวบ้าง ไม่ได้อ้างว่าสำเร็จทั้งหมด (`handleRevokeAll`, `UserPlatformManagement.tsx:248-262`) ความล้มเหลวบางส่วนจะเหลือให้ผู้ถือสิทธิ์มี role ที่ลบไม่สำเร็จติดอยู่ — หน้าจอแค่ดึงข้อมูลใหม่แล้วแสดงผลลัพธ์ ไม่ retry และไม่ rollback ตัวที่ลบสำเร็จไปแล้ว

## 3. `UserPlatformEdit` — แฟ้มรายบุคคล (`/platform/user-platform/:userId`)

เข้าถึงพร้อม `backTo="/platform/user-platform"` ใน header page header เองมีบรรทัด audit ของบัญชี (`normalizeAudit(userRecord)` — created/updated บน row `tb_user`) บวก badge `Inactive` เมื่อบัญชีถูกปิดใช้งาน และ badge "Email not verified" เมื่อ `email_verified_at` เป็น falsy ใน action slot ([Landing](/th/platform/user-platform) §3.3) — ทั้งสองเป็นข้อมูลอย่างเดียว ไม่ใช่ตัวควบคุม

ด้านล่าง header ตามลำดับ:

1. **แถบ error กลาง session** แสดงทุกครั้งที่การดึงข้อมูลบัญชี/role ล้มเหลว — ดู [Permissions](/th/platform/user-platform/permissions) §3 ว่าเกิดขึ้นเมื่อไหร่ ทำไม และหน้าที่เหลือหน้าตาเป็นอย่างไรเมื่อเกิดขึ้น
2. **คำเตือนผู้ถือสิทธิ์ที่ไม่ active** (`!isActive && roleAssignments.length > 0`) — เป็นคู่ระดับรายบุคคลของจำนวนที่ไม่ active ในหน้ารายการ มีไว้เฉพาะเพื่อให้ผู้ตรวจสอบที่เปิดหน้าคนนี้ตรง ๆ (ไม่ผ่านลิงก์คำเตือนของหน้ารายการ) ยังไม่พลาดมัน
3. **`AccessReachBand`** — พาดหัวของหน้า: "Reaches the entire platform" / "Reaches N cluster(s)" พร้อมชื่อ cluster / "No platform privilege" บวกจำนวน assignment รวม ใช้คำศัพท์ `ScopeRail` เดียวกับหน้ารายการ
4. **การ์ด "Roles & Scope"** — `RoleGrantList` จัดกลุ่ม assignment ตาม scope (ทั้งแพลตฟอร์มก่อน หัวข้อของกลุ่มทั้งแพลตฟอร์มเดี่ยว ๆ จะถูกซ่อนเพราะ reach band พูดไปแล้ว) แต่ละแถวแสดงชื่อ role, ใครมอบให้และเมื่อไหร่ในกรณีที่หาได้, badge เตือน "Self-granted" เมื่อผู้ให้ grant คือผู้ถือสิทธิ์เอง และปุ่ม **Remove** ต่อแถว (`<Can permission="user_platform.manage">`) ตัวควบคุม **Add Role** บน header การ์ด (`AddRoleSheet` สิทธิ์เดียวกัน) เป็น side sheet ไม่ใช่แผงในหน้า — `<select>` ของ Role, `<select>` ของ Scope (Platform-wide / Specific cluster ตัวหลังจะเปิด `<select>` ของ Cluster เพิ่ม) และปุ่ม Add/Cancel พร้อม `Ctrl/⌘+S`/`Escape` ผ่าน `useGlobalShortcuts` และตัวกันการนำทางออกทั้งที่ยังไม่บันทึก ที่คำนวณจาก "มีฟิลด์ไหนถูกแตะหรือยัง" (ไม่มี baseline ที่บันทึกไว้ให้เทียบ เพราะไม่มีอะไรกำลังถูกแก้ไข — มันคือฟอร์มสร้างครั้งเดียว)
5. **`MembershipCard`** — ผู้ถือสิทธิ์อยู่ตรงไหนใน tenant tree (cluster และ business unit พร้อม badge active/inactive) ระบุชัดเจนว่า "ไม่ใช่สิทธิ์ระดับแพลตฟอร์ม" — มีไว้ให้ผู้ตรวจสอบเช็คได้ว่า grant ที่ scope เป็น cluster ตรงกับที่คนนั้นทำงานจริงหรือไม่ ไม่ได้มีไว้ซ้ำกับ reach band

**ที่มาของ grant เป็น best-effort และระบุไว้ชัดเจนเมื่อหาไม่ได้** endpoint role ต่อผู้ใช้ (`GET .../roles`) ไม่คืนผู้กระทำ/เวลาต่อ assignment เลย สิ่งนั้นมาจาก endpoint รายการทะเบียนที่มี audit enrichment เท่านั้น `UserPlatformEdit` จะ query ทะเบียนซ้ำด้วยอีเมล/username ของผู้ถือสิทธิ์เอง (`loadProvenance` จับคู่ด้วย `user_id` ไม่เคยใช้ตำแหน่งผลการค้นหา) เพื่อเติมข้อมูลนี้เท่านั้น ความล้มเหลวตรงนี้ไม่ร้ายแรงและทุกแถวจะตกไปใช้บรรทัด "Grant history unavailable" ตรง ๆ แทนที่จะเป็นช่องว่าง เพื่อไม่ให้ grant ที่ไม่มีข้อมูล enrichment ถูกเข้าใจผิดว่าระบุแล้วว่าไม่มีใครมอบ

## 4. e2e suite มีมาก่อน UI นี้ — สองจุดไม่ตรงที่ชัดเจน ไม่ใช่คำเตือนลอย ๆ

`../carmen-platform-e2e/tests/user-platform/` มีสอง spec แก้ล่าสุดที่ `a8e3b31` (2026-08-25) — แปดวันก่อนการเขียนใหม่เมื่อ 2026-09-02 (`fc690cb`/`f6e91c9`) ที่หน้านี้บันทึกไว้ ตามกฎยืนของแผนนี้ e2e suite ไม่ใช่หลักฐานโดยอัตโนมัติ การอ่าน page object เทียบกับ source ปัจจุบันยืนยันสองจุดที่ชัดเจนว่าล้าสมัย ไม่ใช่แค่คำเตือนทั่วไปว่า "อาจจะ" ล้าสมัย:

- **`user-platform-list.spec.ts` ระบุเองใน annotation ว่า "no Add button by design"** และ page object ของมัน (`pages/UserPlatformManagementPage.ts`) มีคอมเมนต์: "NO Add button (users are created on /users; this page only assigns roles) The inherited `addButton`/`clickAdd` must never be used" source ปัจจุบันมีปุ่ม **Grant Access** (ไอคอน `<Plus>` ทั้งใน header และ empty state, §2 ด้านบน) กั้นด้วย `<Can permission="user_platform.manage">` suite นี้ล็อกอินเป็น super admin (เงื่อนไขก่อนของมันเอง) และ `hasPermission()` (`AuthContext.tsx:268-272`) ก็ delegate ไปที่ `checkPermission()` ซึ่งตรวจก่อนอันดับแรกว่า `if (eff?.is_super_admin) return true` (`utils/permissions.ts:56`) — session นั้นจึงเห็นปุ่มนี้ render ทดสอบไม่ได้ assert ว่าปุ่มนี้*ไม่มี* จึงไม่ fail ตรงจุดนี้เพียงจุดเดียว — แต่คำอธิบายที่ระบุไว้ไม่ตรงกับ source ปัจจุบันแล้ว
- **page object ตัวเดียวกันให้ `openUser`/`openFirstNonLoginUser` คลิก `row.locator('button').first()` โดยสมมติว่า cell ของ username คือ "a BUTTON... not an `<a>`"** source ปัจจุบัน render username เป็น react-router `<Link>` (แท็ก `<a>`, `UserPlatformManagement.tsx:316-321`) องค์ประกอบ `<button>` จริงตัวเดียวในหนึ่งแถวข้อมูลคือปุ่มเปิดเมนู kebab ของ row-actions (ยืนยันจากการอ่าน `data-table.tsx`: cell แสดงลำดับแถวเป็นข้อความล้วน ไม่มี checkbox เลือกแถวเปิดใช้งานบนตารางนี้ และปุ่ม sort อยู่ใน `<thead>` นอกขอบเขตของแถว) การคลิก `row.locator('button').first()` วันนี้จะเปิด dropdown menu นั้น ไม่ได้พาไปหน้า detail เลย — ทั้ง spec ที่พึ่ง helper ตัวนี้ (การนำทางใน `user-platform-list.spec.ts` และทั้งไฟล์ `user-platform-config.spec.ts` ซึ่งไปหน้า detail ผ่าน helper นี้ทางเดียว) จะ fail ตรงขั้นตอนนี้เลย ไม่ใช่ทีหลัง
- **page object ของ `user-platform-config.spec.ts` (`pages/UserPlatformEditPage.ts`) คาดว่า "Add Role" จะเปิดแผงแบบ inline** `div.rounded-md.border.p-3.space-y-3` ที่มี `<select>` ของ Role/Scope อยู่ข้างในตรง ๆ source ปัจจุบัน `AddRoleSheet` เป็น `Sheet` (`side="right"`, `className="w-full p-4 sm:max-w-sm sm:p-6"`) โดยมี div เนื้อหาข้างในเป็น `mt-6 space-y-4 px-1` — ไม่มี element ที่ตรงกับ `rounded-md border p-3 space-y-3` อยู่เลย locator `addPanel` ของ page object จึงไม่จับอะไรได้กับ markup ปัจจุบัน ทำให้ `roleSelect`/`scopeSelect` (ทั้งคู่อยู่ใต้ `addPanel`) หาไม่เจอ และ `assignFirstAvailableRole()` จะ timeout ไม่ใช่แค่แสดงผลต่างไป

ผลรวม: การทดสอบ smoke "renders title and a non-empty user table" ใน `user-platform-list.spec.ts` น่าจะยังผ่านอยู่ (heading, จำนวนแถว, chrome ของ search/filter/export ไม่เปลี่ยน) แต่ทุก test อื่นในทั้งสองไฟล์พึ่ง helper ที่เสียไปแล้วตัวใดตัวหนึ่งจากสองตัวข้างบน ให้ถือว่า suite นี้**ใช้เป็นหลักฐานปัจจุบันไม่ได้**สำหรับพฤติกรรมเชิงโต้ตอบของทั้งสองหน้าจอ ทุกคำกล่าวอ้างบนหน้านี้และ [Permissions](/th/platform/user-platform/permissions) มาจากการอ่าน implementation ของ `../carmen-platform`/`../carmen-turborepo-backend-v2` โดยตรง ไม่ใช่จาก suite นี้

## 5. แหล่งอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (HEAD `157a65e`) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`) หรือ `../carmen-platform-e2e` (HEAD `a8e3b31`)

- `src/pages/UserPlatformManagement.tsx` (commit `fc690cb`) — หน้ารายการ คอลัมน์ filter export loop revoke-all (บรรทัด 248-262)
- `src/pages/userPlatformManagement/{PlatformAccessSummary,roleChips,GrantAccessDialog}.tsx` — แถบสรุป, `ScopeRail`/`RoleChips`, dialog มอบสิทธิ์
- `src/pages/UserPlatformEdit.tsx` (commit `f6e91c9`) — หน้า detail, badge ใน header, แถบ error/คำเตือน
- `src/pages/userPlatformEdit/{AccessReachBand,RoleGrantList,MembershipCard,AddRoleSheet}.tsx` — reach band, รายการ grant พร้อมที่มา, การ์ด membership, sheet เพิ่ม role
- `src/components/ui/data-table.tsx:181-230,325-395` — โครงสร้างแถว/คอลัมน์ที่ใช้อ้างอิงใน §4 เพื่อยืนยันว่า element ไหนเป็น `<button>` จริง
- `src/components/Can.tsx`, `src/context/AuthContext.tsx:268-272`, `src/utils/permissions.ts:56` — พฤติกรรม render-nothing-on-false ของ `<Can>` และทางลัด super-admin ที่อ้างใน §4
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/user_platform_role/user_platform_role.service.ts` — `assign`/`assignBulk`/`remove` ที่หนุนหลังทุกการเขียนบนทั้งสองหน้าจอ
- `../carmen-platform-e2e/tests/user-platform/{user-platform-list,user-platform-config}.spec.ts`, `pages/UserPlatform{ManagementPage,EditPage}.ts` — suite ที่ล้าสมัยตามที่กล่าวใน §4

**Cross-links:** [ผู้ใช้แพลตฟอร์ม (landing)](/th/platform/user-platform) &nbsp;·&nbsp; [Permissions](/th/platform/user-platform/permissions) &nbsp;·&nbsp; [Users](/th/platform/users) &nbsp;·&nbsp; [Platform RBAC](/th/platform/rbac)
