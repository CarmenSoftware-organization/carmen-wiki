---
title: โปรไฟล์ (Profile)
description: หน้าจัดการตนเองสำหรับผู้ใช้ที่ล็อกอินอยู่ ดูและแก้ไขข้อมูลตัวตนของตน รวมถึงเปลี่ยนรหัสผ่าน mount อยู่สอง route ที่ใช้ component เดียวกัน
published: true
date: 2026-09-06T23:45:00.000Z
tags: platform/profile, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# โปรไฟล์ (Profile)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจัดการตนเองสำหรับผู้ใช้ที่ล็อกอินอยู่ใช้ดูและแก้ไขข้อมูลตัวตนของตน รวมถึงเปลี่ยนรหัสผ่าน &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ใช้ที่ล็อกอินอยู่ (เจ้าของบัญชีเอง) &nbsp;·&nbsp; **การเข้าถึง:** authenticated-only — route `/profile` ไม่มี `requiredPermission` และไม่มีคีย์ `feature` &nbsp;·&nbsp; **Mount สองครั้ง:** `/profile` (มุมมอง platform) และ `/cluster-admin/:clusterId/profile` (มุมมอง cluster-admin) ทั้งคู่ render component `Profile` เดียวกันด้วยเนื้อหาและข้อมูลเหมือนกันทุกประการ — ต่างกันแค่ chrome (§1) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `user`, `user_info`, `business_unit` (แสดงแบบอ่านอย่างเดียว) &nbsp;·&nbsp; **หน้าย่อย:** 0

## 1. ภาพรวม

Profile คือหน้าบัญชีส่วนตัวของผลิตภัณฑ์ Carmen Platform admin ผู้ใช้ที่ผ่านการพิสูจน์ตัวตนทุกคนจะเข้าถึงหน้านี้ได้จากเมนู avatar ที่ด้านล่างของแถบเมนูข้าง — ไม่มีรายการนำทางระดับบนสำหรับ `/profile` หน้านี้แสดงข้อมูลตัวตนปัจจุบันของผู้ใช้ (alias name, ชื่อจริง/ชื่อกลาง/นามสกุล, เบอร์โทรศัพท์, อีเมล, รหัสบัญชี, วันที่เป็นสมาชิก) และในการ์ดแบบอ่านอย่างเดียวอีกใบหนึ่ง แสดงรายการ business unit ที่ถูกกำหนดให้บัญชีนั้น การ์ด Profile Overview จะ render badge ของ role เล็ก ๆ เฉพาะเมื่อ API response มี string `role` เท่านั้น; การแสดง `platform_role` รุ่นเก่าถูกถอดออกเมื่อ SPA ย้ายไปใช้ RBAC แบบ permission-based ([rbac](/th/platform/rbac))

รองรับการเขียนข้อมูลสองรูปแบบ ทั้งคู่ส่งเป็น `PATCH /api/user/profile` แบบแรกคือการแก้ไขฟิลด์ตัวตน — alias name, ชื่อจริง, ชื่อกลาง, นามสกุล, เบอร์โทรศัพท์; การ์ด Profile Information เปิดมาแบบอ่านอย่างเดียว และปุ่ม **Edit** สลับเข้าโหมดแก้ไข (พร้อมปุ่มคู่ Save Changes / Cancel และ guard การเปลี่ยนแปลงที่ยังไม่ได้บันทึก) อีเมลไม่สามารถแก้ไขจากหน้านี้ได้ แบบที่สองคือการเปลี่ยนรหัสผ่านบัญชีผ่าน modal dialog **Change Password** ที่ต้องกรอกรหัสผ่านปัจจุบันพร้อมรหัสผ่านใหม่ความยาวอย่างน้อยหกตัวอักษรและค่ายืนยันที่ตรงกัน การบันทึก identity edit จะ re-fetch ข้อมูลโปรไฟล์และ refresh local auth context ทำให้ avatar และชื่อที่แสดงในแถบเมนูข้างอัปเดตทันที การเปลี่ยน password ไม่ได้ refresh auth context — dialog เพียงแค่ปิดลงเมื่อสำเร็จ

หน้านี้มีขอบเขตที่แคบโดยตั้งใจ ไม่กำหนดหรือยกเลิกการเป็นสมาชิก business unit ไม่มอบ permission และไม่จัดการผู้ใช้คนอื่น — flow เหล่านั้นเป็นของโมดูล [users](/th/platform/users) และ [rbac](/th/platform/rbac) ซึ่งต้องการ grant permission ที่ตรงกัน route `/profile` ถูกห่อด้วย `<PrivateRoute>` เปล่า ๆ โดยไม่มี `requiredPermission` — เช่นเดียวกับ Dashboard มันเข้าถึงได้โดย session ที่ผ่านการพิสูจน์ตัวตนทุกตัวโดยไม่คำนึงถึง grant permission

### 1.1 Mount อยู่สอง route: Profile ฝั่ง platform และ Profile ฝั่ง cluster-admin

`Profile.tsx` เป็น component เดียวที่ render อยู่สอง route ที่ต่างกัน — `App.tsx` ผูก element `<Profile />` ตัวเดียวกันเข้ากับทั้ง `/profile` และ `/cluster-admin/:clusterId/profile` comment ของ component เองระบุการออกแบบนี้ตรง ๆ ว่า: "Rendered at two routes: `/profile` in the platform view, and `/cluster-admin/:clusterId/profile` inside the cluster-admin view. The param is the only difference — the page's content and data source are identical — so the shell follows it." พูดให้เป็นรูปธรรม: `const { clusterId } = useParams<{ clusterId: string }>(); const Shell = clusterId ? ClusterAdminLayout : Layout;` — การมี route param `clusterId` เป็น branch เดียวในทั้ง component และมันตัดสินใจแค่ว่า layout ไหนจะห่อหน้านี้เท่านั้น

ทุกอย่างที่เหลือเหมือนกันทุกประการระหว่างสอง mount นี้: การเรียก `GET`/`PATCH /api/user/profile` เดียวกัน, ฟิลด์ตัวตนเดียวกัน, dialog Change Password เดียวกัน, การ์ด business unit เดียวกัน, กฎ validate เดียวกัน cluster admin ที่แก้ไข alias name ของตัวเองที่ `/cluster-admin/:clusterId/profile` กำลังแก้ไข record บัญชีตัวเดียวกันเป๊ะกับที่ผู้ใช้ platform แก้ไขที่ `/profile` — ไม่มีข้อมูล profile ที่ scope ตามคลัสเตอร์ เพราะบัญชีผู้ใช้ไม่ได้ scope ตามคลัสเตอร์

สิ่งที่ *ต่างกัน* จริง ๆ คือ chrome ที่ `Shell` แต่ละตัวจัดให้:

| | `/profile` (`Layout`) | `/cluster-admin/:clusterId/profile` (`ClusterAdminLayout`) |
|---|---|---|
| Route guard | `<PrivateRoute>` เปล่า ๆ — ไม่มี `requiredPermission`, ไม่มี `feature` (§4) | `<ClusterAdminRoute>` — ไม่ส่ง prop `feature` จึงไม่มี feature gate เช่นกัน; ต้องการ `isClusterAdminOf(clusterId)` (§4) |
| Nav ของ sidebar | platform nav เต็มรูปแบบ (`buildPlatformNav()`) ถ้า session มี platform authority | cluster-admin nav (`buildClusterAdminNav()`) จำกัดเฉพาะคลัสเตอร์เดียวนั้น |
| ตัวตนของแบรนด์ | แบรนด์ผลิตภัณฑ์ "Carmen Platform" | ชื่อ/code/โลโก้ของคลัสเตอร์ที่ดูแลอยู่ |
| ปลายทางของสัญลักษณ์แบรนด์ | `/dashboard` | `/cluster-admin/:clusterId/cluster` |
| ส่วนเสริมของ header | ไม่มี | `ClusterSwitcher` สำหรับสลับไปคลัสเตอร์อื่นที่ดูแลอยู่ |

session ที่มี platform authority และ*ยังเป็น*cluster admin ด้วย จึงเข้าถึงเนื้อหา Profile เดียวกันได้จากทั้งสอง shell ขึ้นอยู่กับว่ากำลังทำงานในมุมมองไหนอยู่ — บัญชีที่เห็นและแก้ไขไม่เปลี่ยนแปลง

## 2. บริบททางธุรกิจ

Profile เป็นหน้าจัดการตนเองแบบ self-service ไม่มีปัจจัยทางธุรกิจภายนอกที่ขับเคลื่อนนอกเหนือจากการรักษาให้ข้อมูลตัวตนของผู้ใช้แต่ละคนเป็นปัจจุบัน เพื่อให้ audit log การแจ้งเตือน และรายชื่อสมาชิก BU อ้างอิงชื่อและข้อมูลติดต่อที่ถูกต้อง

## 3. แนวคิดสำคัญ

- **Profile**: ชุดของฟิลด์ตัวตนที่เป็นของบัญชีผู้ใช้แต่ละคน — alias name, ชื่อจริง/ชื่อกลาง/นามสกุล, เบอร์โทรศัพท์, อีเมล ทั้งหมดแก้ไขได้จากหน้านี้ยกเว้นอีเมล
- **Alias name**: ป้ายชื่อสั้น ๆ ที่ใส่ได้หรือไม่ใส่ก็ได้ ใช้สำหรับแสดงตัวอักษรย่อบน avatar และเป็นชื่อย่อในที่ที่พื้นที่จำกัด
- **Email (เปลี่ยนไม่ได้)**: รหัสประจำตัวสำหรับล็อกอินของผู้ใช้ แสดงในหน้า Profile แบบอ่านอย่างเดียว การเปลี่ยนค่านี้เป็นการดำเนินการระดับ administrative ที่จัดการนอกโมดูลนี้
- **Toggle view/edit**: การ์ด Profile Information เปิดมาแบบอ่านอย่างเดียว; ปุ่ม **Edit** (มองเห็นคู่กับ **Change Password** เมื่อไม่ได้แก้ไขอยู่) สลับฟิลด์ตัวตนเข้าโหมดแก้ไข Cancel คืนค่าที่บันทึกไว้โดยไม่เรียก API; hook `useUnsavedChanges` จะเตือนผ่าน browser เมื่อ navigate ออกทั้งที่มีการแก้ไขค้างอยู่ Ctrl/Cmd+S submit, Escape ยกเลิก
- **การเปลี่ยนรหัสผ่าน**: flow แบบ modal เฉพาะที่ต้องการรหัสผ่านปัจจุบัน รหัสผ่านใหม่ (อย่างน้อยหกตัวอักษร) และค่ายืนยันที่ตรงกัน ส่งผ่าน endpoint `PATCH /api/user/profile` เดียวกันกับการแก้ไขข้อมูลตัวตน แต่ใส่ `currentPassword` / `newPassword` แทน
- **Business unit ที่ถูกกำหนด**: รายการ BU ที่ผู้ใช้สังกัด แสดงเป็นการ์ดแบบอ่านอย่างเดียว การเป็นสมาชิกจัดการในโมดูล [users](/th/platform/users) โดยผู้ดูแลระบบ หน้า Profile เพียงแสดงข้อมูลเท่านั้น บัญชีที่ไม่มี BU เลย render component `EmptyState` ที่ใช้ร่วมกัน ("No business units", ไอคอน Building2) แทนที่จะเป็นประโยคธรรมดา
- **รหัสบัญชีและวันที่เป็นสมาชิก**: ข้อมูล metadata แบบอ่านอย่างเดียวที่ประทับเวลาตอนสร้างบัญชี render ผ่าน component `AuditMeta` ที่ใช้ร่วมกัน (`variant="compact"` รับค่าจาก `normalizeAudit(profile).created`) เป็นเวลาแบบสัมพัทธ์พร้อม timestamp แบบเต็มใน tooltip เมื่อ hover — ไม่ใช่ string วันที่ตายตัว มีประโยชน์สำหรับการสนทนากับ support และ audit แต่แก้ไขจากหน้านี้ไม่ได้ ไม่มีค่า "updated" คู่กันแสดงบน Profile เลย — มีแค่วันที่สร้างบัญชีเท่านั้นที่แสดง
- **การ validate field แบบ inline**: Alias Name และ Telephone validate ตอน blur ผ่าน helper `validateField` ที่ใช้ร่วมกัน — Alias Name เทียบกับ `^[a-zA-Z0-9]{0,3}$` ("Alias must be 1-3 alphanumeric characters"), Telephone เทียบกับ `^\+?[\d\s\-()]{8,20}$` ("Invalid phone number format") error แสดงแบบ inline เฉพาะในโหมดแก้ไขและเคลียร์ทันทีที่ field เปลี่ยน ทั้งสองการตรวจสอบผ่านแบบเงียบ ๆ เมื่อค่าว่าง (ไม่มี field ใดจำเป็น)
- **การมองเห็นเมื่อ fetch ล้มเหลว**: การ `GET /api/user/profile` เริ่มต้นที่ล้มเหลวตอนนี้แสดง error banner ที่มองเห็นได้ ("Failed to load profile: …") เพิ่มเติมจาก dev-console log เดิม — ก่อนหน้านี้ fetch ที่ล้มเหลวจะทำให้หน้าค้างอยู่แบบเงียบ ๆ โดยไม่มีข้อมูลและไม่มีคำอธิบายบนหน้าจอ

## 4. บทบาทและ Persona

ใช้โดยผู้ใช้ที่ล็อกอินอยู่ (เจ้าของบัญชีเอง) จากทั้งสอง mount (§1.1) ทั้งสอง route ถูก gate ต่างกัน แม้เนื้อหาของหน้าจะเหมือนกันทุกประการ:

- **`/profile` (มุมมอง platform)**: ห่อด้วย `<PrivateRoute>` เปล่า ๆ ไม่มี `requiredPermission` และไม่มี prop `feature` — การพิสูจน์ตัวตนคือ gate เดียว นี่คือการห่อแบบเปล่า ๆ เดียวกับที่ [Dashboard](/th/platform/dashboard) ได้รับ ซึ่งหมายความว่า branch การตัดสินใจ platform-authority/cluster-admin ภายใน `PrivateRoute` ใช้ที่นี่ด้วยเช่นกัน: cluster admin แบบ membership-only ที่มาถึง `/profile` โดยตรงจะถูก redirect ไป `/cluster-admin` โดย guard เอง เหมือนกับที่ `/dashboard` (ดูกลไกเต็มใน [Dashboard](/th/platform/dashboard) §5)
- **`/cluster-admin/:clusterId/profile` (มุมมอง cluster-admin)**: ห่อด้วย `<ClusterAdminRoute>` ไม่มี prop `feature` (จึงไม่มี feature-flag gate เช่นกัน) การตรวจสอบเป็นการเช็คสมาชิกภาพ ไม่ใช่ permission string: `isClusterAdminOf(clusterId)` ต้องเป็นจริงสำหรับผู้เรียก ไม่งั้น route จะ render `<Forbidden>` แทน ไม่มี `requiredPermission` ที่เทียบเท่าตรงนี้ — cluster-admin scope ถูก resolve ครั้งเดียวต่อคลัสเตอร์จาก `adminScope` ไม่ใช่จากคีย์ permission ของ RBAC

ไม่มี gate `<Can>` ใด ๆ ปรากฏภายใน component `Profile` เองที่ mount ไหนเลย และไม่มี grant permission ของ RBAC ถูกตรวจสอบเลยสำหรับการดูหรือแก้ไขโปรไฟล์ของตัวเอง — มีแค่การพิสูจน์ตัวตน (`/profile`) หรือสมาชิกภาพ cluster-admin ของคลัสเตอร์เฉพาะใน URL (`/cluster-admin/:clusterId/profile`)

## 5. โมดูลที่เกี่ยวข้อง

- [users](/th/platform/users) — โมดูลฝั่ง administrative ที่สร้างบัญชีและกำหนด business unit; Profile เพียงอ่านสิ่งที่ Users เขียนเท่านั้น
- [rbac](/th/platform/rbac) — เป็นเจ้าของโมเดล permission ที่ gate ทุก surface อื่น; ตัว Profile เองต้องการเพียง session ที่ผ่านการพิสูจน์ตัวตน และการ assign role/permission ทำบนหน้าจอ User Platform ของโมดูล RBAC
- [business-units](/th/platform/business-units) — แหล่งของรายการ BU ที่แสดงแบบอ่านอย่างเดียวบนหน้า Profile
- [Dashboard](/th/platform/dashboard) — อีก route ที่ได้รับการห่อ `<PrivateRoute>` เปล่า ๆ เหมือน `/profile` ทุกประการ รวมถึงการ redirect platform-authority/cluster-admin ที่อธิบายใน §4
- [ผู้ดูแลคลัสเตอร์ (Cluster Admin)](/th/platform/cluster-admin) — persona ที่สองที่ component `Profile` เดียวกันนี้ให้บริการที่ `/cluster-admin/:clusterId/profile` (§1.1) [UI Screens](/th/platform/cluster-admin/ui-screens) §8 ของโมดูลนั้นเห็นตรงกับเรื่องนี้ตามที่หน้านี้บันทึกไว้ แทนที่จะเล่าใหม่ให้ต่างออกไป

## 6. แหล่งข้อมูลอ้างอิง

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/Profile.tsx` (เรียก `GET` / `PATCH /api/user/profile` ตรง ๆ ผ่าน axios instance ที่ใช้ร่วมกันใน `src/services/api.ts` — ไม่มีไฟล์ profile service แยก; บรรทัด 53-57 คือ branch `clusterId`/`Shell` ที่อธิบายใน §1.1), `../carmen-platform/src/App.tsx:563-568` (`<PrivateRoute>` เปล่า ๆ บน `/profile`) และ `:603-604` (`<ClusterAdminRoute><Profile /></ClusterAdminRoute>` บน `/cluster-admin/:clusterId/profile`), `../carmen-platform/src/components/ClusterAdminRoute.tsx` (การตรวจสอบสมาชิกภาพ `isClusterAdminOf(clusterId)` ที่อธิบายใน §4), `../carmen-platform/src/components/ClusterAdminLayout.tsx` (ตัวตนแบรนด์ของคลัสเตอร์, header slot ของ `ClusterSwitcher`, และ nav `buildClusterAdminNav()` ในตารางเปรียบเทียบของ §1.1), `../carmen-platform/src/utils/validation.ts` (`validateField`, regex ของ Alias Name / Telephone), `../carmen-platform/src/components/PageHeader.tsx` และ `EmptyState.tsx` (component header และ empty-state ที่ใช้ร่วมกันซึ่งถูกนำมาใช้ในหน้านี้), `../carmen-platform/src/components/AuditMeta.tsx` และ `src/utils/audit.ts` (`normalizeAudit` ที่ป้อนวันที่เป็นสมาชิกใน §3)

## 7. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดี่ยว ดู [สารบัญหนังสือ Platform](/th/platform)
