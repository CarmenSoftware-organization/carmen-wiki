---
title: ผู้ดูแลคลัสเตอร์ — สิทธิ์ (Permissions)
description: ไม่มี RBAC permission key เลยในโมดูลนี้ — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน isClusterAdminOf แทน ตรวจก่อน feature flag เสมอบนทุก route และ backend ตรวจสมาชิกภาพซ้ำเป็นอิสระในทุกการเขียน
published: true
date: '2026-10-27T15:00:00.000Z'
tags: book/platform, cluster-admin, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ดูแลคลัสเตอร์ — สิทธิ์ (Permissions)

> **At a Glance**
> **ไม่มี RBAC permission key เลยในโมดูลนี้** ทุก route ต่อคลัสเตอร์กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน ตรวจก่อน feature flag เสมอ &nbsp;·&nbsp; **`/cluster-admin` เอง** มีแค่การตรวจล็อกอิน (`AuthedRoute`) — สมาชิกภาพถูกตัดสินทีหลัง ภายใน `ClusterAdminEntry` &nbsp;·&nbsp; **Nav ไม่มีการกรองด้วย permission เลย** — `clusterAdminNav.ts` กรองด้วย feature flag เท่านั้น การมาถึง nav ได้ต้องผ่าน route guard มาแล้ว &nbsp;·&nbsp; **การเขียนในหน้าจอกั้นด้วยวิธีเดียวกัน** — สวิตช์แก้ไขของ `ClusterProfile` และ `canEdit` ของ `BusinessUnitForm` คำนวณจากการเข้าถึง route ได้ล้วน ๆ ไม่มีการตรวจ permission หรือ role ใด ๆ ใน component เลย &nbsp;·&nbsp; **backend ตรวจสมาชิกภาพซ้ำเป็นอิสระทุกครั้งที่เขียน** — `ClusterAdminAuthzService.isClusterAdmin` สะท้อนการตรวจฝั่ง frontend และถูกเรียกก่อนทุกการเขียนที่หน้าจอของโมดูลนี้ทำ &nbsp;·&nbsp; **ไม่ใช่การไม่มีการตรวจ** — สมาชิกภาพเป็น gate จริงที่บังคับใช้อยู่ อย่าเรียกโมดูลนี้ว่า "unguarded" หรือ "ไม่มีการตรวจ permission เลย" &nbsp;·&nbsp; **ไม่มี e2e suite** — ทุกคำกล่าวอ้างด้านล่างมาจากการอ่าน `../carmen-backstage` และสำหรับภาพสะท้อนฝั่ง backend มาจาก `../carmen-turborepo-backend` โดยตรง

## 1. ภาพรวม

โมดูลนี้อยู่นอกโมเดล RBAC permission ที่ [RBAC](/th/platform/rbac) บันทึกไว้สำหรับผลิตภัณฑ์ platform admin ที่เหลือทั้งหมด ไม่มี permission key ใด ๆ (`cluster_admin.*` หรืออื่นใด) ถูกตรวจเลยที่ไหนใน `src/pages/clusterAdmin/` หรือบนทั้งหกของ route ของมัน — ยืนยันแล้วด้วยการ grep ทั้งไดเรกทอรีหา `hasPermission`/`requiredPermission`/`<Can permission=` ซึ่งไม่เจออะไรเลย แกนที่โมดูลนี้ตรวจแทนคือ **สมาชิกภาพของคลัสเตอร์**: แถว `tb_cluster_user` ที่ยัง active ไม่ถูกลบ มี `role: 'admin'` สำหรับคลัสเตอร์ที่ระบุใน URL นั้น

คำอธิบายที่ถูกต้องและแม่นยำ — ใช้เหมือนกันทุกหน้าในโมดูลนี้ ตามคำตัดสินของแผนนี้เอง — คือ: **ไม่มี RBAC permission key — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน** นี่ไม่ใช่คำพูดเดียวกันกับ "ไม่มีการตรวจ permission เลย" "unguarded" หรือ "กั้นด้วยแค่ feature flag" สามวลีนี้เคยปรากฏมาแล้วอย่างผิด ๆ บนหน้าของโมดูลอื่นในแผนนี้ (ล่าสุดที่ [Licenses](/th/platform/licenses/permissions) ซึ่งถูกแก้ไปแล้วในรอบแก้ไข) — แต่ละวลีอ่านเหมือนกับว่าผู้ใช้ที่ล็อกอินอยู่คนไหนก็เปิดหน้าจอของคลัสเตอร์ไหนก็ได้เมื่อ flag เปิดอยู่ ซึ่งไม่จริงเลย สมาชิกภาพคือ gate ที่รับน้ำหนักจริง ตรวจก่อนที่ feature flag จะถูกพิจารณาด้วยซ้ำ (§2)

route เดียวที่เป็นข้อยกเว้นจริง ๆ ของ "กั้นด้วยสมาชิกภาพ" คือจุดเข้าเอง: `/cluster-admin` ห่อด้วย `AuthedRoute` ซึ่งตรวจแค่การล็อกอิน (§2) สมาชิกภาพยังไม่เข้ามาในภาพตรงนั้น — `ClusterAdminEntry` อ่าน `adminScope` ของผู้เรียกเองแล้วโชว์ picker, auto-redirect, หรือ empty state ตามนั้น ซึ่งไม่ใช่การตัดสินขอบเขตแบบเดียวกับ `<Forbidden />` ของ `ClusterAdminRoute`

## 2. เมทริกซ์ของ gate

ทั้งห้า route ต่อคลัสเตอร์ตรวจผ่าน `ClusterAdminRoute` ซึ่งตรวจสมาชิกภาพก่อน (ล้มเหลว → `<Forbidden>` ในที่ URL ไม่เปลี่ยน) แล้วตรวจ feature flag `feature` หลังเสมอ (ล้มเหลว → `NotFound` เมื่อ `hide`, `ComingSoon` เมื่อ `inactive`) — ลำดับเดียวกันเป๊ะกับที่ [RBAC — Permissions](/th/platform/rbac/permissions) บันทึกไว้สำหรับ `PrivateRoute` ฝั่ง platform เพียงแต่พูดซ้ำสำหรับ guard ของโมดูลนี้เอง

| Route | Guard | การตรวจสมาชิกภาพ | Feature key | แหล่งที่มา |
|---|---|---|---|---|
| `/cluster-admin` | `AuthedRoute` | ไม่มี — ตัดสินภายใน `ClusterAdminEntry` จาก `adminScope` | — | `../carmen-backstage/src/App.tsx:625-628` |
| `/cluster-admin/:clusterId/cluster` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_cluster` | `App.tsx:629-632` |
| `/cluster-admin/:clusterId/business-units` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | `App.tsx:633-636` |
| `/cluster-admin/:clusterId/business-units/:buId/edit` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | `App.tsx:637-640` |
| `/cluster-admin/:clusterId/users` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_users` | `App.tsx:641-644` |
| `/cluster-admin/:clusterId/licenses` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_licenses` | `App.tsx:645-648` |
| `/cluster-admin/:clusterId/profile` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | **ไม่ส่งเลย** | `App.tsx:649-652` |

Sidebar nav (`buildClusterAdminNav`, `../carmen-backstage/src/components/nav/clusterAdminNav.ts:10-27`): กรองสี่แถวของมันด้วยสถานะ feature flag เท่านั้น (`hide` เอาแถวออกทั้งหมด; `inactive` ทำเครื่องหมาย `comingSoon` แต่ยัง render อยู่) **ไม่มีฟิลด์ `permission` บน `NavItem` ใดเลย** ที่มันคืนกลับมา — คอมเมนต์ของฟังก์ชันเองระบุเหตุผลตรง ๆ ว่า "การมาถึง nav นี้ได้ต้องผ่าน `ClusterAdminRoute` มาแล้ว" แถวที่หายไปจาก sidebar นี้จึงหมายความว่า feature flag เป็น `hide` เสมอ ไม่เคยหมายถึง permission grant ที่ขาดหาย

Action การเขียนในหน้าจอ กั้นด้วยการเข้าถึง route ได้ล้วน ๆ ทั้งหมด — ไม่มี permission หรือ role string ใด ๆ ถูกตรวจใน component เหล่านี้เลย:

| จุด | การเขียน | Gate |
|---|---|---|
| สวิตช์แก้ไขของ `ClusterProfile` (ดินสอ → Save/Cancel) | อัปเดตตัวตน/แบรนด์ของคลัสเตอร์ | `!accessLost` (คือเข้า route ได้แล้ว) |
| `BusinessUnitForm` (ทั้งเอกสาร) | อัปเดตฟิลด์ของ business unit | `canEdit = !accessLost`, `BusinessUnitForm.tsx` — คอมเมนต์ของ component เองระบุว่า "สิทธิ์เท่าเดิมเป๊ะ: ใครเข้า route ได้ก็แก้ได้" โดยการเปลี่ยนขอบเขตที่แคบกว่านี้ถูกเลื่อนออกไปให้เป็นสเปกในอนาคตอย่างชัดเจน |
| แท็บ Users (เดิมชื่อ People) ของ `BusinessUnitForm`, `BusinessUnitUsersCard` | เพิ่ม/แก้/ลบสมาชิกภาพ BU | `canEdit` เดียวกับข้างต้น — ไม่มีคีย์ `subscription.*`/`user.*`/`cluster.*` เข้ามาเกี่ยวข้องเลย ต่างจาก `BusinessUnitEdit` ฝั่ง platform ที่ผูก `canEdit` ของ component ตัวเดียวกันนี้ไว้กับ `cluster.update` |
| `ClusterUsers` — แท็บ Members, เมนูของแถว (ใหม่) | **Release seat** / **Restore seat** | ไม่มีสตริง permission ใน UI; route ฝั่ง backend (`POST /api-system/clusters/:cluster_id/users/:user_id/seat/{release,restore}`) มีแค่ `AppIdGuard` และ authorize ภายใน `micro-cluster` ผ่าน `isClusterAdmin` (`cluster-seat.service.ts:95,156`) — เป็นเส้นทางเขียนเดียวที่สร้างมาเพื่อผู้ดูแลแบบสมาชิกโดยเฉพาะ และตั้งใจไม่ติด decorator permission ของ Backstage |
| `ClusterUsers` — แท็บ Members | เปลี่ยน cluster role, ลบสมาชิก | ไม่มี permission string; `clusterService.updateClusterUser`/`deleteClusterUser` |
| `ClusterUsers` — แท็บ Invitations | สร้าง/ส่งซ้ำ/เพิกถอนคำเชิญ | ไม่มี permission string; `clusterAdminService.createInvitation`/`resendInvitation`/`revokeInvitation` |
| `ClusterAdminLicenses` | — | **ไม่มี UI สำหรับเขียนเลยบนหน้าจอนี้** — ดู [UI Screens](/th/platform/cluster-admin/ui-screens) §7 |
| `Profile` (`/cluster-admin/:clusterId/profile`) | แก้ตัวตนของตัวเอง, เปลี่ยนรหัสผ่านของตัวเอง | เหมือนกับการ mount ฝั่ง platform — แค่ล็อกอินบวกสมาชิกภาพของคลัสเตอร์ใน URL ไม่มี RBAC key (ดู [Profile](/th/platform/profile) §4) |

การบังคับใช้ฝั่ง backend ยืนยันโดยตรงจากซอร์ส (`../carmen-turborepo-backend`, HEAD `c9d788829`): `ClusterAdminAuthzService.isClusterAdmin(userId, clusterId)` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:43-60`) — แถว `tb_cluster_user` ที่ active ไม่ถูกลบ มี `role: enum_cluster_user_role.admin` สำหรับคลัสเตอร์นั้น หรือสถานะ super admin ระดับแพลตฟอร์ม — ถูกเรียกเป็นอิสระก่อนการเขียนเรื่องสมาชิกภาพที่หน้าจอของโมดูลนี้ทำ: list/create/update/delete ของ cluster-user (`apps/micro-cluster/src/cluster/cluster/cluster.service.ts` — `getUserClusterById` บรรทัด 1220, `createUserCluster` 1334, `updateUserCluster` 1458/1463, `deleteUserCluster` 1525), สร้าง/list/เพิกถอน/ส่งซ้ำคำเชิญ (`apps/micro-cluster/src/cluster/user-invitation/user-invitation.service.ts` บรรทัด 383/550/623/686) และ release/restore ที่นั่ง (`cluster-seat.service.ts` 95/156) **การอัปเดต *โปรไฟล์* ของคลัสเตอร์และ BU ใช้การตรวจที่กว้างกว่า** คือ `ClusterAdminAuthzService.canWriteCluster(userId, clusterId, 'cluster.update')` (`cluster.service.ts:371` `updateCluster`; `business-unit.service.ts:753-763` รวมถึงตรวจคลัสเตอร์ปลายทางเมื่อย้าย BU): เป็นจริงสำหรับ super admin, สมาชิก cluster-admin **หรือ** grant ของ role Backstage ที่ให้ `cluster.update` กับคลัสเตอร์นั้น (`authz.service.ts:185-190`) สำหรับผู้ดูแลแบบสมาชิก `updateCluster` ยังตัด `is_active`, `info` และ `max_license_users` ออกเงียบ ๆ ด้วย (การตรวจ `canWriteClusterViaBackstageRole` ที่ `cluster.service.ts:393`) ดังนั้น "สมาชิกภาพคือการบังคับใช้ทั้งหมดของ backend" เป็นจริงเฉพาะเส้นทางสมาชิกภาพ/คำเชิญ/ที่นั่งข้างต้น; การเขียนโปรไฟล์ยังรับผู้ถือ role Backstage ด้วย

## 3. ทำไมไม่มี permission key ที่นี่ — เหตุผลเชิงออกแบบ

คอมเมนต์ของ `ClusterAdminRoute` เองบอกตรง ๆ ว่านี่คือ "navigation ไม่ใช่ security" — การตรวจฝั่ง server ยังเกิดขึ้นแบบเป็นอิสระในทุกคำขอต่อไป ซึ่งเป็นเหตุผลที่ทำให้ตัดสินจาก `adminScope` ที่แคชไว้ฝั่ง client ที่ระดับ route ได้อย่างเหมาะสม สองข้อเท็จจริงสนับสนุน ทั้งคู่ยืนยันจากซอร์สจริง ไม่ใช่แค่เชื่อคอมเมนต์เฉย ๆ:

1. **backend ตรวจซ้ำทุกครั้งที่เขียน ไม่ใช่ครั้งเดียวตอนล็อกอิน** `ClusterAdminAuthzService.isClusterAdmin` ถูกเรียกใหม่ ต่อคำขอ ที่จุดเขียนคลัสเตอร์/business-unit/คำเชิญทุกจุดที่ระบุใน §2 — `adminScope` ที่แคชไว้ฝั่ง client ที่อาจล้าสมัย (เช่น จากสมาชิกภาพที่ถูกถอนหลังหน้าโหลดแล้ว) จึงบังคับให้เขียนผ่านไปเองไม่ได้ การตรวจสมาชิกภาพของ server เป็นอิสระและจะปฏิเสธเช่นกัน
2. **การอ่านตัวเดียวที่หน้าจอทางเข้าของโมดูลนี้พึ่งพา ตั้งใจ self-scope ไม่กั้นด้วย permission ฝั่ง backend เช่นกัน** `GET /api-system/me/admin-clusters` ไม่มี decorator `@RequireBackstagePermission` เลย คอมเมนต์ของมันเองระบุเหตุผล — "คำตอบมาจากสมาชิกภาพของผู้เรียกเอง… ซึ่ง fail-closed และคืนรายการว่าง — ไม่ใช่คลัสเตอร์ของผู้อื่น — สำหรับผู้เรียกที่ไม่มีสิทธิ์" (`backstage_me-admin-clusters.controller.ts`) exception list ของการตรวจ permission coverage บน backend เองบันทึกเหตุผลเดียวกันไว้สำหรับ route นี้โดยเฉพาะ: "self-scope: service กรองด้วย `user_id` ของผู้เรียกเอง คืนเฉพาะ cluster ที่ตัวเองดูแล" (`packages/prisma-shared-schema-backstage/prisma/check.api-system-permission-coverage.ts` แถว `admin-clusters`)

นี่คือรูปแบบเดียวกับ "backend บังคับใช้เป็นอิสระจากคีย์ของ frontend" ที่ [Licenses — Permissions](/th/platform/licenses/permissions) §3 บันทึกไว้สำหรับโมดูลของตัวเอง — ต่างกันตรงที่ UI ของโมดูลนี้ไม่เคยพยายามสร้างเส้นทางเขียนที่ถูกกั้นเลยตั้งแต่แรก (แถว `ClusterAdminLicenses` ของ §2): endpoint การเขียนใบอนุญาตทุกตัวต้องการ `subscription.manage` ซึ่งเป็นคีย์ที่สมาชิกภาพเพียงอย่างเดียวไม่มีวันได้มา ดังนั้น frontend จึงไม่ render ตัวควบคุมที่จะ 403 เลยตั้งแต่ต้น

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | ผู้เรียกที่ล็อกอินอยู่แต่ไม่มีสมาชิกภาพผู้ดูแลคลัสเตอร์เลย deep-link ไป `/cluster-admin/<clusterId ใดก็ได้>/cluster` | `<Forbidden />` render ในที่ ก่อนที่ feature flag `cluster_admin_cluster` จะถูกพิจารณาด้วยซ้ำ | ทำซ้ำได้โดยพิมพ์ URL ตรง ๆ — address bar ยังเป็น path ที่ถูกกั้น ตรงกับธรรมเนียม "Back ต้องไม่ดักผู้ใช้" ของ `PrivateRoute` เอง |
| 2 | ผู้ดูแลคลัสเตอร์ A deep-link ไป URL ของคลัสเตอร์ B | เหมือนกรณีที่ 1 — `isClusterAdminOf` ตรวจต่อคลัสเตอร์ ไม่ใช่ "เป็นผู้ดูแลคลัสเตอร์อะไรสักอันหนึ่ง" | ยืนยันว่าสมาชิกภาพถูกตรวจกับ `:clusterId` ที่เฉพาะเจาะจงใน URL ไม่ใช่ boolean แบบกว้าง ๆ |
| 3 | ผู้เรียกที่ล็อกอินอยู่แต่ไม่ได้ดูแลคลัสเตอร์ใดเลยเข้า `/cluster-admin` เอง | ไม่ใช่ 403 — `ClusterAdminEntry` render `EmptyState` ของตัวเอง ("ไม่มีคลัสเตอร์ให้ดูแล") เพราะ `AuthedRoute` ตรวจแค่ล็อกอิน | ความต่างนี้สำคัญกับผู้ทดสอบ: route ทางเข้าและอีกห้า route ต่อคลัสเตอร์ล้มเหลวต่างกันสำหรับเงื่อนไข "ไม่ได้ดูแลอะไรเลย" แบบเดียวกัน |
| 4 | สมาชิกภาพถูกถอนขณะที่หน้า `ClusterProfile`/`BusinessUnitList`/`BusinessUnitForm`/`ClusterUsers` เปิดอยู่แล้ว | route guard ผ่านไปแล้วตอน mount และไม่ตรวจซ้ำ; คำขอ API ครั้งถัดไปของหน้าจะ 403 และหน้า render `ClusterAccessLost` แทนที่ body ของมัน | ทำซ้ำได้โดยถอนสมาชิกภาพในอีก session/แท็บหนึ่ง แล้วกระตุ้นการดึงข้อมูลใหม่ (เช่น Save หรือ poll ที่พื้นหลัง) บนหน้าที่เปิดค้างไว้ |
| 5 | เหมือนกรณีที่ 4 แต่บน `ClusterAdminLicenses` | **ไม่มีการดัก `ClusterAccessLost` เลยบนหน้าจอนี้** — grep `ClusterAdminLicenses.tsx` เจอแค่สาขา `isNotFoundError` สำหรับคลัสเตอร์ที่หายไป/ถูกลบ ไม่มีการดัก 403 เฉพาะ | เป็นช่องว่างจริงเทียบกับอีกสี่หน้าจอพี่น้อง ไม่ใช่การออกแบบที่ตั้งใจซึ่งระบุไว้ในซอร์สที่ไหน — ควรแจ้งถ้าทำซ้ำได้ เพราะสถานะบนจอที่เกิดขึ้น (การแสดงแบบดึงข้อมูลล้มเหลวดิบ ๆ แทนที่จะเป็น empty state "หมดสิทธิ์เข้าถึง กลับไปคลัสเตอร์ของฉัน" ที่ใช้ร่วมกัน) ยังไม่ได้ถูกอธิบายไว้ที่นี่โดยอิสระ |
| 6 | Super admin (`adminScope.all = true`) เข้า `/cluster-admin/:clusterId/*` route ใดก็ได้ | `isClusterAdminOf` คืน `true` เสมอสำหรับทุก cluster id — ทุก gate ในตารางนี้ผ่านหมด | อย่า QA gate สมาชิกภาพของโมดูลนี้จาก session super-admin เด็ดขาด มันเผยความจริงเรื่องแถว `tb_cluster_user` ที่ขาดหายไปไม่ได้เลยเหมือนกับ session ที่มีแค่สมาชิกภาพจริง ๆ |
| 7 | feature flag `cluster_admin_*` ตัวใดตัวหนึ่งถูกตั้งเป็น `hide` สำหรับ session ที่ผ่านการตรวจสมาชิกภาพแล้ว | route render `NotFound` และแถวของ nav เองก็หายไปจาก sidebar ทั้งหมด (§2) | สมาชิกภาพถูกตรวจก่อนเสมอ — `NotFound` ที่นี่ยังหมายถึง "คุณเป็นสมาชิกแต่ feature นี้ปิดอยู่" ไม่ใช่ "คุณไม่ใช่สมาชิก" — อย่าปนสองเรื่องนี้ตอนวิเคราะห์บั๊กที่รายงานมา |
| 8 | เหมือนกรณีที่ 7 แต่ flag เป็น `inactive` แทน | route render `ComingSoon`; แถวของ nav ยัง render อยู่ ทำเครื่องหมาย `comingSoon` | nav กับ route ตรงกันตรงนี้ — ต่างจาก `hide`, `inactive` ยังโชว์เป็นคำสัญญา ไม่ใช่ถูกซ่อนเงียบ ๆ |
| 9 | session ที่มี platform authority และมี `hasClusterAdminScope` เป็น true แต่ permission ระดับแพลตฟอร์มยังตัดสินไม่ได้ เข้า `/dashboard` หรือ `/profile` ตรง ๆ | สาขา redirect ของ `PrivateRoute` เอง (ไม่ใช่ guard ของโมดูลนี้) ส่งไปที่ `/cluster-admin` ก่อนที่จะตรวจ permission ใด ๆ | บันทึกไว้ที่ [Dashboard](/th/platform/dashboard) §5 และ [Profile](/th/platform/profile) §4 พูดซ้ำที่นี่เพราะเป็นวิธีเดียวที่ session จะมาลงในโมดูลนี้ได้โดยไม่เคยนำทางไป `/cluster-admin` เองเลย |
| 10 | cluster admin เพิ่ม/แก้/ลบสมาชิก BU บนแท็บ Users ของ `BusinessUnitForm` | สำเร็จโดยไม่มีการตรวจ permission ใด ๆ นอกจากเข้าถึง route ได้ — เทียบตรง ๆ กับแท็บ Users ของ `BusinessUnitEdit` ฝั่ง platform ที่ component `BusinessUnitUsersCard` ตัวเดียวกันเป๊ะผูก `canEdit` ไว้กับ `cluster.update` | component ตัวเดียวกัน แต่กติกา gate ต่างกันไปตามว่า shell ไหน render มัน — อย่าสมมติว่าเทสต์ที่เขียนจาก permission ของหน้าฝั่ง platform ยืนยันหน้านี้ได้ด้วย |
| 11 | ผู้ถือ role Backstage ที่มี `cluster.update` ซึ่งไม่ใช่ super admin และไม่ใช่สมาชิกของคลัสเตอร์ เปิดแท็บ Users ฝั่ง platform แล้วคลิก **Release seat** | ปุ่ม render (`canEdit` เป็น true) แต่การเรียกถูกปฏิเสธด้วย 403 `CLUSTER_USER_NOT_CLUSTER_ADMIN` — action ที่นั่งรับเฉพาะสมาชิกภาพ cluster-admin หรือ super admin ไม่รับ grant ของ Backstage | ดูจากอีกฝั่งที่ [Clusters — Permissions](/th/platform/clusters/permissions) §9; ความไม่ตรงกันระหว่าง UI/back-end ที่ควรเปิด ticket |

## 5. คำแนะนำ

- **อย่าทดสอบการควบคุมการเข้าถึงของโมดูลนี้ด้วยการตรวจ RBAC permission grant** session ทดสอบจริงต้องมีแถว `tb_cluster_user` ที่มี `role: 'admin'` สำหรับคลัสเตอร์เป้าหมาย ไม่ใช่การมอบหมาย `backstage_role` — สองแกนนี้เป็นอิสระต่อกัน (ดู [Landing](/th/platform/cluster-admin) §3.5)
- **ทดสอบการเสียสมาชิกภาพกลางเซสชันบนทั้งห้าหน้าจอต่อคลัสเตอร์** และยืนยันช่องว่างของ `ClusterAdminLicenses` โดยเฉพาะ (กรณีพิเศษที่ 5) ก่อนสมมติว่ามันทำงานเหมือนพี่น้องทั้งสี่ตัว
- **อย่าเรียก gate ของโมดูลนี้ว่าเป็นการไม่มีการตรวจที่ไหนเลย** — "ไม่มี RBAC permission key — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน" คือวลีเดียวที่ควรใช้ ไม่ว่าจะในบรรทัด At-a-Glance ตารางกรณีพิเศษ หรือใน prose — มีสามโมดูลอื่นในแผนนี้ที่เคยพลาดเรื่องนี้มาแล้วครั้งละหนึ่งครั้ง
- **เมื่อโมดูลนี้ได้ e2e suite** (ปัจจุบันมีแค่การ capture screenshot ของ wiki ที่แตะมัน) ลำดับสมาชิกภาพ-ก่อน-flag (§2, กรณีพิเศษที่ 1/2/7) คือเคสที่คุ้มค่าที่สุดที่ควรเขียนไว้ก่อน เพราะเป็นสิ่งเดียวที่ผู้อ่านสรุปเองไม่ได้จากแค่การกรองด้วย feature flag ของ nav
- **การเข้าถึง route ได้ไม่ใช่โมเดล permission ในตัวมันเอง** — `ClusterProfile`/`BusinessUnitForm`'s `canEdit = !accessLost` (§2) หมายความว่าผู้ดูแลทุกคนของคลัสเตอร์หนึ่งเขียนทุกอย่างที่หน้าจอของโมดูลนี้เปิดให้สำหรับคลัสเตอร์นั้นได้ อย่าทดสอบหา permission แบบละเอียดกว่านี้ที่ไม่มีอยู่ในซอร์สวันนี้

**อ้างอิง:** path ทั้งหมดคือ `../carmen-backstage` (HEAD `8405788f`) เว้นแต่ระบุไว้ `src/App.tsx:625-652` (route) · `src/components/{AuthedRoute,ClusterAdminRoute}.tsx` (guard) · `src/components/nav/clusterAdminNav.ts` (nav) · `src/context/AuthContext.tsx` (`isClusterAdminOf`, `adminScope`, `hasClusterAdminScope`) · `src/pages/clusterAdmin/{ClusterProfile,BusinessUnitForm,ClusterUsers,ClusterAdminLicenses}.tsx` (gate ในหน้าจอ) · `../carmen-turborepo-backend/apps/micro-cluster/src/common/cluster-admin-authz.service.ts` (ภาพสะท้อนฝั่ง backend, HEAD `c9d788829`) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_me-admin-clusters/backstage_me-admin-clusters.controller.ts` และ `packages/prisma-shared-schema-backstage/prisma/check.api-system-permission-coverage.ts` (การอ่านแบบ self-scope ที่ตั้งใจไม่กั้นด้วย permission)
**ลิงก์ที่เกี่ยวข้อง:** [หน้าหลัก Cluster Admin](/th/platform/cluster-admin) &nbsp;·&nbsp; [UI Screens](/th/platform/cluster-admin/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/th/platform/rbac/permissions) &nbsp;·&nbsp; [Licenses — Permissions](/th/platform/licenses/permissions) &nbsp;·&nbsp; [Dashboard](/th/platform/dashboard) &nbsp;·&nbsp; [Profile](/th/platform/profile)
