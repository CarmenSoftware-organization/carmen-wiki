---
title: ผู้ดูแลคลัสเตอร์ (Cluster Admin)
description: คอนโซลผู้ดูแลคลัสเตอร์ — nav และ persona ที่สองของแอป จำกัดขอบเขตอยู่ที่คลัสเตอร์เดียวต่อครั้ง เข้าที่ /cluster-admin/:clusterId/* ไม่มี RBAC permission key เลยในโมดูลนี้ — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน isClusterAdminOf แทน ตรวจก่อน feature flag เสมอ
published: true
date: '2026-09-06T11:00:00.000Z'
tags: book/platform, cluster-admin
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ดูแลคลัสเตอร์ (Cluster Admin)

> **At a Glance**
> **คืออะไร:** **คอนโซลที่สอง** ไม่ใช่หน้าจอเพิ่มเติมของผลิตภัณฑ์ platform admin — มี nav ของตัวเอง มี shell ของตัวเอง และเป็น persona ของตัวเอง อยู่ทั้งหมดใต้ `/cluster-admin/:clusterId/*` &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับพื้นผิว "ผู้ดูแลคลัสเตอร์" ที่ลูกค้าใช้เอง — บทบาทที่พนักงานของลูกค้าถือได้โดยไม่ต้องมี RBAC grant ใด ๆ ของ platform เลย &nbsp;·&nbsp; **Route ทางเข้า:** `/cluster-admin` → `ClusterAdminEntry` กั้นด้วย `AuthedRoute` ที่ตรวจแค่การล็อกอิน &nbsp;·&nbsp; **Route ต่อคลัสเตอร์:** `/cluster-admin/:clusterId/{cluster,business-units,business-units/:buId/edit,users,licenses,profile}` ทั้งหมดกั้นด้วย `ClusterAdminRoute` &nbsp;·&nbsp; **ตัว gate:** **ไม่มี RBAC permission key — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน** ตรวจก่อน feature flag เสมอ บนทุก route ทั้งห้าที่ผูกกับคลัสเตอร์ &nbsp;·&nbsp; **Nav:** `clusterAdminNav.ts` **ไม่มีการกรองด้วย permission เลย** — การผ่าน route guard มาได้คือด่านทั้งหมดอยู่แล้ว — และ feature key ทั้งสี่ตัว (`cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`, `cluster_admin_users`) เป็น **คนละชุด** จาก nav ฝั่ง platform แม้ป้ายเมนูจะซ้ำกัน &nbsp;·&nbsp; **Key entities/tables:** อ่าน `tb_cluster`, `tb_business_unit`, `tb_cluster_user`, `tb_cluster_license`, `tb_business_unit_license` — ตารางชุดเดียวกับที่โมดูลฝั่ง platform อย่าง [Clusters](/th/platform/clusters), [Business Units](/th/platform/business-units), [Users](/th/platform/users) และ [Licenses](/th/platform/licenses) เป็นเจ้าของ — โมดูลนี้ไม่มี schema ของตัวเองเลย &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — `../carmen-platform-e2e/tests/` ไม่มีไดเรกทอรี `cluster-admin` เลย ทุกคำกล่าวอ้างในหน้าของโมดูลนี้มาจากการอ่าน `../carmen-platform` (และสำหรับภาพสะท้อนฝั่ง backend ของ gate มาจาก `../carmen-turborepo-backend-v2`) โดยตรง &nbsp;·&nbsp; **หน้าย่อย:** 2

## 1. ภาพรวม

Cluster Admin คือประตูหน้าที่สองของ Carmen Platform ทุกโมดูลอื่นในหนังสือเล่มนี้ — Clusters, Business Units, Users, Licenses, RBAC — เข้าถึงผ่าน sidebar ของ platform admin เอง และกั้นด้วย RBAC permission key จาก `tb_user_tb_platform_role` โมดูลนี้เข้าผ่าน sidebar คนละตัวเลย สร้างด้วยฟังก์ชันคนละตัว (`buildClusterAdminNav()`, `../carmen-platform/src/components/nav/clusterAdminNav.ts`) และกั้นด้วยแกนคนละแกนไปเลย: **สมาชิกภาพของคลัสเตอร์** — แถวใน `tb_cluster_user` ที่มี `role: 'admin'` ไม่ใช่ permission grant

จุดเข้าคือ `/cluster-admin` ต่อกับ `ClusterAdminEntry` อยู่ใน `AuthedRoute` (`../carmen-platform/src/App.tsx:578-581`) `AuthedRoute` ตรวจแค่ว่าผู้เรียกล็อกอินอยู่หรือไม่ — ไม่มี permission ไม่มีการตรวจสมาชิกภาพเลยตรงนี้ (`../carmen-platform/src/components/AuthedRoute.tsx:6-27`) คอมเมนต์ของมันเองอธิบายว่าทำไมต้องบางขนาดนี้: `PrivateRoute` ของฝั่ง platform จะ redirect ผู้ดูแลคลัสเตอร์ที่มีแค่สมาชิกภาพ *ไปที่* `/cluster-admin` เมื่อมันตัดสินว่าคนนั้นไม่มีอำนาจระดับแพลตฟอร์ม (`../carmen-platform/src/components/PrivateRoute.tsx:60-81`) ดังนั้นถ้าห่อ `/cluster-admin` เองด้วย `PrivateRoute` ก็จะ redirect วนกลับมาที่ตัวเองไม่มีที่สิ้นสุด `ClusterAdminEntry` (`../carmen-platform/src/pages/clusterAdmin/ClusterAdminEntry.tsx`) จัดการที่เหลือเองจาก `adminScope`: มีคลัสเตอร์ที่ดูแลอยู่พอดีหนึ่งคลัสเตอร์ (และไม่ใช่ super admin) จะ redirect เข้าไปเลยทันที; นอกนั้น — ไม่มีคลัสเตอร์เลย, มีหลายคลัสเตอร์, หรือเป็น super admin ที่ดูแลทุกอย่าง — จะแสดง picker หรือ (กรณีไม่มีคลัสเตอร์เลย) `EmptyState` ที่คอมเมนต์ของ component เองบรรยายไว้ว่า "ไม่ใช่ 403 โดยเนื้อแท้… ผู้ใช้ล็อกอินอยู่ แค่ไม่ได้ดูแลอะไรเลย" (บรรทัด 10-13)

เมื่อเข้ามาในคลัสเตอร์หนึ่งแล้ว route ที่เหลือทั้งห้าตัวจะพก `:clusterId` ไว้ใน path และอยู่หลัง `ClusterAdminRoute` (`../carmen-platform/src/components/ClusterAdminRoute.tsx`) ซึ่งตัดสินคำถามเรื่องสมาชิกภาพครั้งเดียวต่อคลัสเตอร์แล้วให้ทุกหน้าข้างใต้รับคำตอบนั้นไปใช้ต่อ — ดู §3.2 และ [Permissions](/th/platform/cluster-admin/permissions) สำหรับการตรวจตัวจริงและลำดับของมัน เพราะ id ของคลัสเตอร์อยู่ใน URL ไม่ใช่ state ที่เลือกไว้ฝั่ง client sidebar ที่สร้างจากมัน (`buildClusterAdminNav`) จึงสร้างลิงก์ที่หลุดออกจากคลัสเตอร์ที่ URL บอกไม่ได้เลยในทางเทคนิค — ทุก nav item เป็น `${base}/...` โดย `base = /cluster-admin/${clusterId}` (`clusterAdminNav.ts:15`) การสลับคลัสเตอร์เป็น dialog `ClusterSwitcher` ที่หัวเพจ ซึ่ง navigate ไป URL อื่น ไม่ใช่การเปลี่ยน state (`../carmen-platform/src/components/ClusterSwitcher.tsx:20-22`)

Shell เองคือ `ClusterAdminLayout` (`../carmen-platform/src/components/ClusterAdminLayout.tsx`) — ใช้ component `Layout` ที่ใช้ร่วมกันทั้งแอปซ้ำทั้งหมด แล้วเติมแค่สามอย่าง: nav items จาก `buildClusterAdminNav`, `ClusterSwitcher` ที่ header slot, และตัวตนแบรนด์ ซึ่งกลายเป็นชื่อ/รหัส/avatar ของคลัสเตอร์ที่กำลังดูแลอยู่เอง (ตกกลับไปใช้แบรนด์ผลิตภัณฑ์เฉพาะเมื่อคลัสเตอร์นั้นไม่อยู่ใน `adminScope.clusters` ที่แคชไว้ในเครื่องผู้เรียก — กรณี super admin ที่การไปค้นหาชื่อจริงจะเสียคำขอเพิ่มแค่เพื่อป้ายชื่อ) ลิงก์แบรนด์พาไปที่ `/cluster-admin/:clusterId/cluster` ไม่ใช่ `/dashboard`

## 2. บริบททางธุรกิจ

Carmen ขายคลัสเตอร์ของ business unit ให้ลูกค้าโรงแรม/ธุรกิจบริการ และลูกค้ามักมีคนในทีมของตัวเอง — หัวหน้าฝ่าย IT ผู้จัดการฝ่ายปฏิบัติการระดับภูมิภาค — ที่ต้องเห็นและดูแลคลัสเตอร์ของตัวเองเบา ๆ โดยไม่ต้องกลายเป็นผู้ปฏิบัติการของ Carmen เอง การให้ role RBAC (`tb_user_tb_platform_role`) กับคนนั้นจะผิดรูปสองต่อ: ต้องให้ทีมซัพพอร์ตของ Carmen จัดสรรและตรวจสอบ grant ฝั่งแพลตฟอร์มให้ผู้ดูแลของลูกค้าทุกราย และ — เพราะ role ระดับแพลตฟอร์มไม่ได้ผูกขอบเขตกับคลัสเตอร์ในแบบที่ความสัมพันธ์นี้ต้องการ — จะเสี่ยงให้ผู้ดูแลนั้นเข้าถึงคลัสเตอร์ที่ไม่ใช่ของตัวเอง

คำตอบของผลิตภัณฑ์คือแถวสมาชิกภาพแทน: `tb_cluster_user.role = 'admin'` ระบุว่าใครเป็นผู้ดูแลของคลัสเตอร์ที่ระบุหนึ่งตัว เป็นอิสระจาก RBAC grant ใด ๆ แถวเดียวนี้แหละที่ทั้ง `isClusterAdminOf` (ฝั่ง frontend, `AuthContext.tsx`) และ `ClusterAdminAuthzService.isClusterAdmin` (ฝั่ง backend, §3.2) ใช้ตัดสิน คนหนึ่งคนถือสถานะนี้ได้กับศูนย์ หนึ่ง หรือหลายคลัสเตอร์ ถือ RBAC authority ระดับแพลตฟอร์มไปพร้อมกันได้หรือไม่ก็ได้ และสองระบบนี้ไม่เคยถามกันเลย

สิ่งที่ผู้ดูแลของลูกค้าทำได้ในคลัสเตอร์ของตัวเองสะท้อนอยู่ในห้าหน้าจอของโมดูลนี้: ดูตัวตนและแบรนด์ของคลัสเตอร์เอง (§3.3) เห็นและดูแลเบา ๆ business unit กับพนักงานในนั้น เชิญและจัดการผู้ใช้ของคลัสเตอร์ และตรวจ — อ่านอย่างเดียว — ว่าสิ่งที่ซื้อไว้เหลืออยู่เท่าไร มันคือคอนโซลสำหรับดูสถานะใบอนุญาตและดูแลรายชื่อเบา ๆ ไม่ใช่พื้นผิวสำหรับซื้อหรือตั้งค่าแพลตฟอร์ม ไม่มีอะไรในโมดูลนี้สร้าง business unit แก้ไขใบอนุญาต หรือแตะอะไรนอกคลัสเตอร์เดียวที่อยู่ใน URL ได้เลย

## 3. แนวคิดสำคัญ

### 3.1 `adminScope` กับ `isClusterAdminOf` — ตัดสินครั้งเดียว แคชไว้ฝั่ง client

`AuthContext` ดึง `GET /api-system/me/admin-clusters` ครั้งเดียวต่อ session (`fetchAdminScope`, `AuthContext.tsx:98-107`) เก็บเป็น `adminScope: { all: boolean; clusters: AdminCluster[] }` แคชไว้ใน `localStorage` คีย์ `adminScope` ค่า `all` short-circuit การตรวจทุกครั้งถัดไป — ตั้งเป็น true เฉพาะ super admin ระดับแพลตฟอร์ม ตามคอมเมนต์ของ `clusterAdminService.getMyAdminClusters` เอง: "super admin ดูแลทุกอย่างอยู่แล้ว ดังนั้น `clusters` เป็นแค่หน้าสำหรับค้นหาเท่านั้น" (`../carmen-platform/src/services/clusterAdminService.ts:14-17`) `isClusterAdminOf(clusterId)` (`AuthContext.tsx:274-275`) ก็แค่ `adminScope.all || adminScope.clusters.some(c => c.id === clusterId)` — การอ่านค่าที่แคชไว้แบบ synchronous ไม่ใช่การยิงคำขอใหม่ทุกครั้งที่นำทาง

### 3.2 `ClusterAdminRoute` — ตัว gate ตามลำดับที่มันทำงานจริง

`ClusterAdminRoute` (`../carmen-platform/src/components/ClusterAdminRoute.tsx:20-59`) ตรวจตามลำดับนี้เป๊ะ ๆ:

1. **ล็อกอินอยู่** — ผู้ที่ไม่ได้ล็อกอิน redirect ไป `/login`
2. **`adminScope` โหลดเสร็จแล้ว** — scope เป็น `null` (ยังไม่ได้ดึงมา) จะแสดงสถานะกำลังโหลด ไม่ตัดสินก่อนเวลา
3. **`!clusterId || !isClusterAdminOf(clusterId)` → render `<Forbidden />` ในที่** นี่คือการตรวจที่รับน้ำหนักจริง และเป็นการตรวจสมาชิกภาพ ไม่ใช่ permission string
4. **ตรวจ feature flag ทีหลังสุดเท่านั้น** เมื่อมีการส่งมา คอมเมนต์ของ component เองระบุว่าลำดับนี้ตั้งใจ และให้เหตุผลไว้ตรง ๆ: "ด่านฟีเจอร์ท้ายสุด ด้วยเหตุผลเดียวกับใน `PrivateRoute`: ขอบเขตต้องตอบก่อน flag" (บรรทัด 42-43) — ลำดับเดียวกันเป๊ะกับที่ [RBAC — Permissions](/th/platform/rbac/permissions) บันทึกไว้สำหรับ guard ฝั่ง platform

คำอธิบายที่ถูกต้องของข้อ 3 ใช้เหมือนกันทุกหน้าในโมดูลนี้: **ไม่มี RBAC permission key — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน** นี่ไม่ใช่การไม่มีการตรวจ ผู้ที่ไม่ใช่สมาชิกถูกกั้นเด็ดขาด ก่อนที่ feature flag จะถูกตรวจด้วยซ้ำ — ดู [Permissions](/th/platform/cluster-admin/permissions) สำหรับเมทริกซ์ gate เต็มและเหตุผลว่าทำไมเรื่องนี้สำคัญต่อการทดสอบ

คอมเมนต์ของ `ClusterAdminRoute` เองบอกตรง ๆ ว่านี่คือ "navigation ไม่ใช่ security": การบังคับใช้จริงอยู่ฝั่ง server และเกิดขึ้นเป็นอิสระในทุกคำขอ ไม่ใช่แค่ครั้งเดียวตอนเข้า route `../carmen-turborepo-backend-v2`'s `ClusterAdminAuthzService.isClusterAdmin(userId, clusterId)` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:46-63`) สะท้อนการตรวจฝั่ง frontend เป๊ะทุกจุด — แถว `tb_cluster_user` ที่ยัง active ไม่ถูกลบ มี `role: 'admin'` สำหรับคลัสเตอร์นั้น หรือสถานะ super admin ระดับแพลตฟอร์ม — และทุกคำเรียกที่เขียนข้อมูลจากหน้าจอของโมดูลนี้ (แก้คลัสเตอร์ แก้ business unit สร้าง/ส่งซ้ำ/เพิกถอนคำเชิญ) เรียก service นี้เป็นอิสระก่อนเขียนทุกครั้ง `adminScope` ที่แคชไว้ฝั่ง client ที่อาจล้าสมัย (เช่น จากสมาชิกภาพที่ถูกถอนกลางเซสชัน) จึงบังคับให้เขียนผ่านไปเองไม่ได้ — backend ตรวจซ้ำทุกครั้ง แนวคิด "self-scope ไม่มี permission decorator" แบบเดียวกันนี้ยังขยายไปถึงฝั่งอ่านด้วย: exception list ของการตรวจ permission coverage บน backend เองบันทึก `GET api-system/me/admin-clusters` ไว้ว่าตั้งใจไม่กั้นด้วย permission เพราะ "service กรองด้วย `user_id` ของผู้เรียกเอง คืนเฉพาะ cluster ที่ตัวเองดูแล" (`packages/prisma-shared-schema-platform/prisma/check.api-system-permission-coverage.ts` แถว `admin-clusters`) — เหตุผลแบบ self-scope เดียวกันกับ gate ฝั่ง frontend ใช้กับ endpoint เดียวของ backend ที่หน้าจอทางเข้าของโมดูลนี้พึ่งพา

การห่อด้วย Fragment ตัวเดียวยังแก้ปัญหาเฉพาะของ React Router ที่คุ้มค่าต่อการรู้ไว้เวลาทดสอบ: `ClusterAdminRoute` ห่อลูกของมันด้วย `<React.Fragment key={clusterId}>` (บรรทัด 58) โดยตั้งใจ เพื่อบังคับให้ remount ทั้งชุดเมื่อ `clusterId` เปลี่ยน — ถ้าไม่มีตัวนี้ การกระโดดจากหน้าคลัสเตอร์หนึ่งไปอีกคลัสเตอร์หนึ่งตรง ๆ ผ่านเมนู Back/Forward ของเบราว์เซอร์ (กด Back ค้าง) อาจทิ้ง state ของคลัสเตอร์ก่อนหน้าไว้บนจอ เพราะ React Router ใช้ instance ของ component ซ้ำเมื่อมีแค่ route param ที่ต่างกัน

### 3.3 Nav ไม่มีการกรองด้วย permission เลย — การเข้าถึงได้คือด่านทั้งหมด

`buildClusterAdminNav(clusterId, flagOf)` (`clusterAdminNav.ts:10-27`) กรองสี่รายการของมันด้วยสถานะ feature flag เท่านั้น (`hide` เอาแถวออก, `inactive` ทำเครื่องหมาย `comingSoon`) — ไม่มีฟิลด์ `permission` บน `NavItem` ใดเลยที่มันคืนกลับมา และคอมเมนต์ของมันเองระบุเหตุผลตรง ๆ: "ไม่มีการกรองด้วยสิทธิ์: การมาถึง nav นี้ได้ต้องผ่าน `ClusterAdminRoute` มาแล้ว" (บรรทัด 7-8) feature key ทั้งสี่ — `cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`, `cluster_admin_users` — ใช้ป้ายเมนูร่วมกับแถวฝั่ง platform (Cluster, Business Units, Licenses, Users) แต่เป็น **คนละชุดกันเลย** การสลับ feature flag ฝั่ง platform ไม่มีผลอะไรที่นี่ และกลับกันก็เช่นกัน ผู้อ่านที่สมมติว่าคีย์ฝั่ง platform (`clusters`, `business_units`, `licenses`, `users`) ใช้กับคอนโซลนี้ได้จะทดสอบผิด flag

### 3.4 สองสระว่ายน้ำที่มีจำกัด อ่านอย่างเดียวทุกที่ในคอนโซลนี้

ทุกหน้าจอที่แสดงความจุ — `ClusterProfile`, `ClusterAdminLicenses`, และแผ่นป้าย `BuPropertyPlate` บน `BusinessUnitForm` — ดึงตัวเลขสองชุดเดียวกัน: **โควตา BU** ของคลัสเตอร์ (สร้าง business unit ได้กี่หน่วย จาก `bu_cap`/`bu_used` บนเรคคอร์ดคลัสเตอร์ ท้ายที่สุดมาจาก `v_cluster_bu_cap`) และ **สระที่นั่ง** (`total_max_license_users`/`users_count` ระดับคลัสเตอร์ ไม่ใช่รายต่อ BU) ทั้งคู่ใช้สูตรความจุและสเกลสีเดียวกับฝั่ง platform (`utils/capacity`) ระดับ "warn" หรือ "over" จึงมีความหมายเดียวกันกับมิเตอร์ฝั่ง platform ที่ [Licenses — Data Model](/th/platform/licenses/data-model) §3 บันทึกไว้ ไม่มีอะไรในคอนโซลนี้ซื้อ แก้ หรือยกเลิกสระใดสระหนึ่งได้เลย — ดู §4 และ [UI Screens](/th/platform/cluster-admin/ui-screens) §7 สำหรับหน้าจอ `ClusterAdminLicenses` ที่อ่านอย่างเดียว และ [Licenses](/th/platform/licenses) §4 ว่าตัวเลขเหล่านั้นถูกเขียนที่ไหนจริง ๆ

### 3.5 สมาชิกภาพ กับ RBAC — สองแกนที่ไม่เคยตัดกัน

บัญชีผู้ใช้หนึ่งบัญชีเป็นได้อิสระต่อกัน: เป็น platform admin ที่มี RBAC grant (เข้า sidebar ฝั่ง platform ได้ ขึ้นกับ permission key ของ [RBAC](/th/platform/rbac)), เป็น cluster admin ผ่านสมาชิกภาพ `tb_cluster_user` (เข้าคอนโซลนี้ได้สำหรับคลัสเตอร์ที่ดูแลอยู่), เป็นทั้งสองอย่างพร้อมกัน หรือไม่เป็นเลยทั้งคู่ ไม่มีระบบไหนตรวจอีกระบบหนึ่งเลย กรณีจริงที่พบบ่อยที่สุดสำหรับคอนโซลนี้คือแบบที่สองล้วน ๆ — พนักงานของลูกค้าที่ไม่มี role ระดับแพลตฟอร์มของ Carmen เลย

### 3.6 `ClusterAccessLost` — สมาชิกภาพถูกถอนกลางเซสชัน

`ClusterAdminRoute` ตัดสินครั้งเดียวตอน mount ถ้าสมาชิกภาพของ cluster admin ถูกถอนขณะที่หน้าใต้ `/cluster-admin/:clusterId/*` เปิดอยู่แล้ว route guard จับไม่ได้ — คำขอ API ครั้งถัดไปที่หน้าที่เปิดอยู่ยิงออกไปจะโดน 403 ทันที `ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, และ `ClusterUsers` แต่ละหน้าดัก 403 นั้นเองแล้ว render `ClusterAccessLost` (`../carmen-platform/src/pages/clusterAdmin/ClusterAccessLost.tsx`) — `EmptyState` พร้อมปุ่ม "กลับไปคลัสเตอร์ของฉัน" — แทนที่ body ของหน้า แทนที่จะพังหรือโชว์ error ดิบ `ClusterAdminLicenses` **ไม่มี** การดักแบบนี้ (ดู [UI Screens](/th/platform/cluster-admin/ui-screens) §7 และ [Permissions](/th/platform/cluster-admin/permissions) §4 กรณีพิเศษที่ 9)

## 4. บทบาทและ Persona

| Route | Guard | การตรวจสมาชิกภาพ | Feature key | หมายเหตุ |
|---|---|---|---|---|
| `/cluster-admin` | `AuthedRoute` | ยังไม่มี — ตัดสินภายใน `ClusterAdminEntry` จาก `adminScope` | — | ดู §1 |
| `/cluster-admin/:clusterId/cluster` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_cluster` | [UI Screens](/th/platform/cluster-admin/ui-screens) §3 |
| `/cluster-admin/:clusterId/business-units` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | [UI Screens](/th/platform/cluster-admin/ui-screens) §4 |
| `/cluster-admin/:clusterId/business-units/:buId/edit` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | [UI Screens](/th/platform/cluster-admin/ui-screens) §5 |
| `/cluster-admin/:clusterId/users` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_users` | [UI Screens](/th/platform/cluster-admin/ui-screens) §6 |
| `/cluster-admin/:clusterId/licenses` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_licenses` | [UI Screens](/th/platform/cluster-admin/ui-screens) §7 |
| `/cluster-admin/:clusterId/profile` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | **ไม่ส่งเลย** — route นี้ไม่มี feature gate | ดู §4.1 |

ทุกแถวที่กั้นด้วยสมาชิกภาพในตารางนี้คือข้อเท็จจริงเดียวกันที่พูดซ้ำ: **ไม่มี RBAC permission key — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน**

### 4.1 `/cluster-admin/:clusterId/profile` คือหน้า `/profile` ของ platform เอง แค่อยู่คนละ shell

`Profile.tsx` เป็น component เดียวที่ mount ที่สอง route หน้า [Profile](/th/platform/profile) บันทึกทั้งสอง mounting ไว้เต็มแล้ว (ตาราง chrome comparison ที่ §1.1) และหน้านี้เห็นตรงกับเรื่องนั้นแทนที่จะเล่าใหม่ให้ต่างออกไป: ข้อมูลเดียวกัน ฟิลด์เดียวกัน validation เดียวกัน `PATCH /api/user/profile` endpoint เดียวกัน — ต่างกันแค่ `Shell` (`Layout` เทียบกับ `ClusterAdminLayout`), ตัวตนแบรนด์ และ `ClusterSwitcher` ที่หัวเพจ จุดที่ควรพูดซ้ำที่นี่คือ: นี่คือ route ต่อคลัสเตอร์เพียงตัวเดียวที่ส่ง `ClusterAdminRoute` โดยไม่มี prop `feature` เลย (`App.tsx:603-604`) จึงไม่มี feature-flag gate ใด ๆ ทั้งสิ้น — สมาชิกภาพคือด่านทั้งหมด

### 4.2 session หนึ่งถูก redirect มาที่นี่จาก shell ของ platform ได้เลยทั้งชุด

[Dashboard](/th/platform/dashboard) §5 และ [Profile](/th/platform/profile) §4 ทั้งคู่บันทึกไว้ว่า `PrivateRoute` มีสาขาหนึ่งที่ทำงานก่อนการตรวจ permission ใด ๆ: session ที่มี `hasClusterAdminScope` (ดูแลอย่างน้อยหนึ่งคลัสเตอร์) แต่ยังไม่มี platform authority ที่ตัดสินได้ จะถูก redirect ไป `/cluster-admin` แทนที่จะเห็น 403 (`PrivateRoute.tsx:60-81`) นี่คือเหตุผลเดียวกับที่คอมเมนต์ของ `AuthedRoute` เองให้ไว้ว่าทำไม `/cluster-admin` เองใช้ `PrivateRoute` ไม่ได้ (§1) — การ redirect จะวนกลับไปกลับมา ในทางปฏิบัติหมายความว่า cluster admin ที่มีแค่สมาชิกภาพซึ่งพิมพ์ `/dashboard` หรือ `/profile` ตรง ๆ จะมาลงที่นี่แทน โดยไม่เคยเห็นหน้า Forbidden เลย

## 5. โมดูลที่เกี่ยวข้อง

- [Clusters](/th/platform/clusters) — `ClusterProfile` เป็นภาพสะท้อนที่แคบกว่าและอ่านเป็นหลักของ `ClusterEdit` ดูการเทียบที่ [UI Screens](/th/platform/cluster-admin/ui-screens) §3
- [Business Units](/th/platform/business-units) — `BusinessUnitList`/`BusinessUnitForm` เป็นภาพสะท้อนแบบจำกัดคลัสเตอร์และแก้ไขได้อย่างเดียวของ `BusinessUnitManagement`/`BusinessUnitEdit` ดู [UI Screens](/th/platform/cluster-admin/ui-screens) §4–5
- [Users](/th/platform/users) — เป็นคนละ data model กันเลย: หน้าจอ Users ของโมดูลนี้จัดการสมาชิกภาพ `tb_cluster_user` และคำเชิญของคลัสเตอร์ ไม่ใช่เรคคอร์ดบัญชี platform `tb_user` ที่โมดูล Users เป็นเจ้าของ ดู [UI Screens](/th/platform/cluster-admin/ui-screens) §6
- [Licenses](/th/platform/licenses) — บันทึกหน้าจอ licence อ่านอย่างเดียวของโมดูลนี้ไว้จากฝั่งตัวเองแล้ว (§4, §5) และใช้คำอธิบาย gate เดียวกันเป๊ะกับที่นี่ `ClusterAdminLicenses` ใช้ hook (`useLicenseLedger`, `useClusterSeatLicenses`) และ service ของโมดูลนั้นซ้ำ
- [RBAC](/th/platform/rbac) — เป็นเจ้าของแกน permission ที่โมดูลนี้ตั้งใจอยู่นอกเหนือไปเลย (§3.5)
- [Profile](/th/platform/profile) — เป็นเจ้าของบันทึกเต็มของ component `Profile` ที่ใช้ร่วมกันซึ่งโมดูลนี้ mount เป็นครั้งที่สอง (§4.1)
- [Dashboard](/th/platform/dashboard) — บันทึกกลไก redirect ของ `PrivateRoute` ที่พา session มาลงที่นี่ได้โดยไม่เคยเรียก `/cluster-admin` ตรง ๆ เลย (§4.2)

## 6. แหล่งข้อมูลอ้างอิง

path ทั้งหมดคือ `../carmen-platform` (HEAD `157a65e`, 2026-09-04) เว้นแต่จะขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`, 2026-09-06)

- `src/App.tsx:578-605` — หก route `/cluster-admin*` และ guard/feature prop ของแต่ละตัว
- `src/components/AuthedRoute.tsx` — guard ทางเข้าที่ตรวจแค่ล็อกอิน และเหตุผลที่มันมีอยู่
- `src/components/ClusterAdminRoute.tsx` — ตัว gate ต่อคลัสเตอร์ (§3.2)
- `src/components/ClusterAdminLayout.tsx`, `src/components/ClusterSwitcher.tsx` — chrome ของ shell
- `src/components/nav/clusterAdminNav.ts` — nav สี่รายการที่ไม่มี permission (§3.3)
- `src/components/PrivateRoute.tsx:38-104` — guard ฝั่ง platform รวมถึงสาขา redirect ที่บันทึกไว้ที่ §4.2
- `src/context/AuthContext.tsx` — `adminScope`, `fetchAdminScope`, `isClusterAdminOf`, `hasClusterAdminScope`
- `src/services/clusterAdminService.ts` — `getMyAdminClusters`, CRUD ของคำเชิญ
- `src/pages/clusterAdmin/ClusterAdminEntry.tsx` — หน้าจอลงจอด `/cluster-admin`
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/common/cluster-admin-authz.service.ts:46-63` — `ClusterAdminAuthzService.isClusterAdmin` ภาพสะท้อนฝั่ง backend ของ `isClusterAdminOf`
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_me-admin-clusters/platform_me-admin-clusters.controller.ts` และ `packages/prisma-shared-schema-platform/prisma/check.api-system-permission-coverage.ts` — endpoint `GET api-system/me/admin-clusters` ที่ตั้งใจไม่กั้นด้วย permission และข้อยกเว้นที่บันทึกไว้

## 7. หน้าในโมดูลนี้

- [UI Screens](/th/platform/cluster-admin/ui-screens) — ทั้งหกหน้าจอ (`ClusterAdminEntry`, `ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, `ClusterUsers`, `ClusterAdminLicenses`) บวกการ mount ร่วมของ `Profile` แต่ละหน้าเทียบกับคู่ของมันฝั่ง platform
- [Permissions](/th/platform/cluster-admin/permissions) — เมทริกซ์ gate เต็ม เหตุผลเชิงออกแบบว่าทำไมไม่มี RBAC key และกรณีพิเศษสำหรับผู้ทดสอบ
