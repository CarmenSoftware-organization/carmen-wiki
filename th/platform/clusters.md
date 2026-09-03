---
title: คลัสเตอร์ (Clusters)
description: ภาพรวมโมดูล Clusters — กลุ่ม tenant ระดับบนสุดที่เป็นเจ้าของ business unit และ user ตามไลเซนส์
published: true
date: 2026-07-29T06:35:38.000Z
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# คลัสเตอร์ (Clusters)

โมดูล **Clusters** เป็นจุดเริ่มต้นของ container ระดับองค์กรที่ใหญ่ที่สุด ใน Carmen Platform โดย cluster หนึ่ง ๆ จะรวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้นเข้าด้วยกัน นอกจากนี้ cluster ยังเป็นที่เก็บข้อมูล **ไลเซนส์** — ทั้งจำนวน BU สูงสุดที่ cluster นี้มีได้ และ (ผ่านการรวมยอด จากทุก BU) จำนวน user ทั้งหมดที่ครอบคลุม route และ action ที่แก้ไขข้อมูลในโมดูลนี้ถูก gate ด้วย permission key `cluster.*` (ดู [Platform RBAC](/th/platform/rbac))

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** container ของ tenant ที่รวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้น และเป็นที่เก็บไลเซนส์ ("จำนวน BU สูงสุดต่อ cluster" และจำนวน user รวมจากทุก BU) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA; การเข้าถึงของ operator ต้องได้รับ grant permission `cluster.*` ([rbac](/th/platform/rbac)) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_cluster` (ฟิลด์: `code`, `name`, `alias_name`, `logo_file_token`, `avatar_file_token`, `max_license_bu`, `is_active`, soft-delete trio), `tb_business_unit` (1:N), `tb_cluster_user` (M:N join ที่ถือ role per-cluster เป็น `admin`/`user`) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูล Clusters เปิดเผย aggregate root ของ cluster ผ่านรูปแบบสองหน้าจอ มาตรฐานที่ใช้ในทุกที่ใน Platform SPA:

- **`/clusters` → `ClusterManagement`** — `DataTable` แบบ server-side พร้อมการค้นหาแบบ debounce, แผง filter แบบ Sheet (active/inactive และ ตัวเลือก "show soft-deleted"), ส่งออก CSV, แถบสรุป **Fleet Capacity** ทั้งฝูง (fleet-wide) เหนือตาราง และจดจำสถานะ UI ใน `localStorage` (search, page, perpage, sort, filters) หน้า list ไม่มีคอลัมน์ thumbnail logo ต่อแถวอีกต่อไป — คอลัมน์นั้นถูกลบออกเมื่อเพิ่มแถบ Fleet Capacity เข้ามา
- **`/clusters/new` → `ClusterEdit` (โหมด create)** — แสดงการ์ด "Cluster details" การ์ดเดียว เมื่อสร้างสำเร็จ ตอนนี้หน้าจะ navigate ตรงไป `/clusters/:id/edit` (ซึ่งเป็น route ที่ลงทะเบียนไว้แล้ว) — การสร้างสำเร็จจะไม่พา operator ไปลงที่ Dashboard อีกต่อไป
- **`/clusters/:id/edit` → `ClusterEdit` (โหมด view/edit)** — เอกสารแบบคอลัมน์เดียว แก้ไข-แบบ-in-place ตามแพทเทิร์น "A4" ทั่วทั้ง platform ไม่ใช่เลย์เอาต์การ์ดสามคอลัมน์แบบเดิม nav แบบ scrollspy ที่ sticky (`ClusterEditNav`, บนเดสก์ท็อป) / แถบ chip แนวนอน (บนมือถือ) จะพาไปยัง 5 ส่วนที่วางซ้อนกันในคอลัมน์เดียว: **Overview** (การ์ด `ClusterHero` แสดงตัวตน + capacity — logo/avatar, code/alias/status และมาตรวัด capacity ของ BU/user), **Details** (field ของตัวตน + license แก้ไขได้แบบ in-place), **Branding** (อัปโหลด logo/avatar), **Business Units** ใน cluster นี้ และ **Users** ใน cluster นี้ ไม่มี toggle Edit ระดับหน้าอีกต่อไป — แต่ละ field หรือแถวในตารางแก้ไขได้เป็นอิสระ (หรือไม่ได้) ตามสิทธิ์ `cluster.update` (`canEdit`) และแถบ "Unsaved changes" แบบ sticky จะปรากฏที่ด้านล่างของหน้าจอพร้อมปุ่ม Save/Cancel เมื่อ field ใด ๆ ต่างจาก snapshot ล่าสุดที่บันทึกไว้ การบันทึกถูกป้องกันด้วย token optimistic-lock `doc_version` (ดู [Data Model](/th/platform/clusters/data-model) §2.1) การบันทึกที่ล้าหลังจะแสดง toast แจ้ง conflict และโหลด record ใหม่ `Ctrl/⌘+S` บันทึกและ `Escape` ยกเลิกได้ขณะมีการเปลี่ยนแปลงค้างอยู่

การ์ด Business Units แสดงรายการ BU ทุกตัวที่ `cluster_id` ตรงกับ cluster ปัจจุบัน (พร้อมช่องค้นหาของตัวเอง, filter Active/Inactive และคอลัมน์ Code/Name ที่ sort ได้) พร้อมปุ่ม **Add** ที่นำทางไป `/business-units/new?cluster_id=<id>` เพื่อให้ BU ใหม่ผูกกับ cluster ตั้งแต่เริ่ม ส่วนส่วน Users แสดงข้อมูล จาก `tb_cluster_user` (กรองตาม cluster_id) พร้อมช่องค้นหา/filter เช่นกัน และรองรับ add ผ่าน dialog บวกกับการแก้ไข role และ parent BU **แบบ inline** ตรงในแถวของตาราง (ไม่มี dialog แก้ไขแยกอีกต่อไป) — พร้อมการเลือกหลายรายการด้วย checkbox และ action แบบกลุ่ม (bulk) **Remove** / **Move to BU**

## 2. บริบททางธุรกิจ

โดยทั่วไป cluster จะแทนองค์กรลูกค้าหนึ่งรายหรือเครือโรงแรมที่ทำสัญญา Carmen Platform หนึ่งฉบับ สัญญานี้กำหนดว่าลูกค้ามีสิทธิ์ใช้ BU ได้กี่ตัว และ (ต่อ BU) มีสิทธิ์มี named user กี่คน ตัว cluster record คือที่เก็บ ค่า cap เหล่านี้ และเป็นที่ที่ทำการคำนวณ "ยังอยู่ใต้ลิมิตหรือไม่"

- ปุ่ม **Add BU** บนหน้า edit cluster จะ disable ตัวเองเมื่อ `business_units.length >= max_license_bu` พร้อม tooltip ("License limit reached (N/M)")
- Dialog **Add User** จะ disable ตัวเลือก BU ที่ `max_license_users` เต็มแล้ว และแสดงยอด "X of Y licensed users" ที่กำลังใช้งานต่อ BU
- เมื่อรวม cluster + BU ภายใต้สังกัด คือกลไกที่ Carmen ใช้กำหนดว่า user คนหนึ่งสลับเข้าใช้ BU ใดได้บ้าง — assignment ถูกเก็บใน `tb_cluster_user` พร้อมตัวชี้ `parent_bu_id`
- **การป้องกันการลบ (deletion guard):** action Delete ของแถวในหน้า list จะถูกบล็อกฝั่ง client (แสดง toast โดยไม่ยิง API) เมื่อ cluster เป้าหมายยังมี `bu_count > 0` — การลบ cluster ไม่ cascade ไปยัง business unit ของมันที่ฝั่ง backend ดังนั้นการลบ cluster ที่ยังมี BU ที่ยังใช้งานอยู่จะทำให้ BU เหล่านั้นกำพร้า operator ต้องย้ายหรือลบ BU ก่อน
- **แถบ Fleet Capacity:** หน้า list จะรวมยอด cluster ที่ยังไม่ถูกลบทั้งหมดเป็นภาพรวมทั้งฝูง — capacity รวมของ BU/user ที่ใช้ไปเทียบกับ cap, จำนวน cluster ที่ไม่มี cap พร้อมยอดที่ใช้อยู่ และจำนวน cluster ทั้งหมด/active/near-limit (≥ 90% ของ cap ที่กำหนดไว้)

## 3. แนวคิดสำคัญ

- **Cluster** — container ที่มีชื่อ ประกอบด้วย `code`, `name`, `alias_name` (ไม่เกิน 3 ตัวอักษร แสดงเฉพาะในฟอร์ม edit และคอลัมน์ Alias ของ CSV export เท่านั้น — ไม่มี UI badge ใด render ค่านี้), flag `is_active` และ cap `max_license_bu` (optional) ส่วน soft-delete ติดตามผ่าน `deleted_at` / `deleted_by_name`
- **Branding (logo + avatar)** — แต่ละ cluster มี **logo** สี่เหลี่ยมผืนผ้าและ **avatar** สี่เหลี่ยมจัตุรัส เก็บใน Prisma เป็น file token (`logo_file_token`, `avatar_file_token`) และ API คืนค่าเป็น presigned object ฝังในตัว (`logo: { url, expires_at }`, `avatar: { url, expires_at }`) การอัปโหลดทำบนส่วน Branding ของหน้า edit ผ่าน multipart endpoint เฉพาะ หน้า list ไม่แสดงคอลัมน์ thumbnail logo อีกต่อไป (ถูกลบเมื่อเพิ่มแถบ Fleet Capacity) — การ์ด `ClusterHero` บนส่วน Overview ของหน้า edit เป็นจุดเดียวตอนนี้ที่เห็น logo/avatar ของ cluster นอกจากส่วน Branding เอง
- **Cluster ↔ Business Unit (1:N)** — BU ทุกตัวถือ `cluster_id` หน้า edit cluster จะกรอง BU list ระดับ global ให้เหลือเฉพาะลูกของ cluster ตัวเอง และนับว่ามีกี่ตัวที่ active
- **Cluster ↔ User (M:N ผ่าน `tb_cluster_user`)** — เพิ่ม user เข้า cluster โดย insert row ที่มี key fields คือ `user_id`, `cluster_id`, `role` (`admin` | `user`), `is_active` และ `parent_bu_id` (optional) ส่วน Users บน `ClusterEdit` อ่าน join นี้ผ่าน `GET /api-system/user/clusters/:clusterId`
- **License caps** — มีสอง limit อิสระต่อกัน: ระดับ cluster `max_license_bu` (จำกัดจำนวน BU ที่ผูกได้) และระดับ BU `max_license_users` (จำกัดจำนวน cluster_user ที่มี BU นี้เป็น parent) หน้า edit cluster รวม cap ของทุก BU เป็นตัวเลข "total licensed users" บนการ์ด `ClusterHero` และแถบ Fleet Capacity/หน้า list ก็รวมยอดแบบเดียวกันในระดับทั้งฝูง
- **Optimistic concurrency (`doc_version`)** — `tb_cluster` (และ `tb_cluster_user`) ตอนนี้มี counter `doc_version` แล้ว หน้า edit จะอ่านค่านี้ตอนโหลดและส่งกลับไปพร้อมทุก `PUT`; การบันทึกที่ล้าหลังจะถูกปฏิเสธด้วย `409` และ SPA จะแสดง toast "ถูกเปลี่ยนโดยคนอื่น" แล้วโหลด record ใหม่แทนที่จะเขียนทับแบบเงียบ ๆ (ดู [Data Model](/th/platform/clusters/data-model) §2.1)
- **คอลัมน์ audit** — หน้า list แสดงคอลัมน์ Created และ Updated (timestamp พร้อมชื่อผู้กระทำ) SPA จะ flatten object `audit` แบบ nested จาก API response (`audit.created.{at,name}`, `audit.updated.{at,name}`) สำหรับคอลัมน์วันที่ โดยยอมรับ shape แบบ flat รุ่นเก่าด้วย ซึ่งชนะเมื่อมีค่า (`item.created_at ?? item.audit?.created?.at`) เซลล์ Updated จะถูกละเมื่อ `updated_at` เท่ากับ `created_at`
- **Soft delete** — หน้า list จะซ่อน row ที่ `deleted_at IS NOT NULL` เว้นแต่จะเปิด filter "Show soft-deleted clusters" row ที่ถูก soft-delete จะมี badge "Deleted" สีแดงกำกับ (tooltip ของ badge ระบุชื่อผู้ลบ) และเมื่อเปิด filter จะมีคอลัมน์ audit "Deleted By" เพิ่มต่อท้าย การลบ cluster ที่ยังเป็นเจ้าของ business unit อยู่จะถูกบล็อกฝั่ง client (§2)

## 4. บทบาทและ Persona

การเข้าถึงเป็นแบบ permission-based ([Platform RBAC](/th/platform/rbac)): แต่ละ route ถือ key `requiredPermission` บน `PrivateRoute` และปุ่มที่แก้ไขข้อมูลยังถูกห่อด้วย gate `<Can>` เพิ่มเติม — บางตัวเป็นแบบ cluster-scoped ผ่าน prop `clusterId`

| Surface | ชนิดของ gate | Key | Scoped? |
|---|---|---|---|
| route `/clusters` | `requiredPermission` | `cluster.read` | ไม่ |
| route `/clusters/new` | `requiredPermission` | `cluster.create` | ไม่ |
| route `/clusters/:id/edit` | `requiredPermission` | `cluster.update` | ไม่ |
| รายการ "Clusters" ใน sidebar | filter `permission` | `cluster.read` | ไม่ |
| List: ปุ่ม Add Cluster | `<Can>` | `cluster.create` | ไม่ |
| List: action Edit ของ row | `<Can>` | `cluster.update` | ใช่ — `clusterId={row.original.id}` |
| List: action Delete ของ row | `<Can>` | `cluster.delete` | ใช่ — `clusterId={row.original.id}` |
| หน้า edit: field Details/Branding/Users, bulk actions | `canEdit = hasPermission('cluster.update', {clusterId})` | `cluster.update` | ใช่ — `clusterId={id}` |

มีสองจุดที่ควรสังเกต ข้อแรก `cluster.delete` มีอยู่ **เฉพาะ** ในรูป gate ภายในหน้าเท่านั้น — ไม่มี route ใดต้องการมัน ดังนั้น session ที่ถือเพียง `cluster.read` จะเห็นหน้า list แต่เมนู action ของ row จะว่างเปล่า ข้อสอง gate แบบ scoped (`clusterId`) จะเข้า branch การ resolve แบบ cluster-specific: role assignment ที่ scope ไว้กับ cluster A จะเปิด Edit/Delete เฉพาะบน row ของ cluster A เท่านั้น ขณะที่ route guard แบบ unscoped จะผ่านด้วย grant แบบ cluster-scoped ของ cluster ใดก็ได้ ไม่มี gate แบบ toggle Edit แยกต่างหากอีกต่อไป — หน้า edit คำนวณ boolean `canEdit` ตัวเดียว (`!isNew && hasPermission('cluster.update', { clusterId: id })`) แล้วส่งลงไปทุกส่วน session ที่ไม่มี grant สามารถเข้าถึง `/clusters/:id/edit` ได้ (route guard เป็นแบบ unscoped) แต่จะเห็นทุก field, control อัปโหลด และ action จัดการ user เป็นแบบอ่านอย่างเดียว/ซ่อนไว้ อัลกอริทึมการ resolve และเมทริกซ์ gate ทั้ง SPA อยู่ใน [rbac permissions](/th/platform/rbac/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [business-units](/th/platform/business-units) — cluster เป็นเจ้าของ BU แบบ 1:N หน้า edit cluster คือจุดมาตรฐานในการสร้าง BU ที่ผูกกับ cluster ตั้งแต่ต้น (เรียก `navigate('/business-units/new?cluster_id=<id>')`) **Gotcha:** route `/business-units*` ใช้ key `cluster.read`/`cluster.create`/`cluster.update` ซ้ำ — ไม่มี key `business_unit.*` ดังนั้นการ grant สิทธิ์เข้าถึง cluster จะมอบ Business Units ไปด้วย
- [users](/th/platform/users) — cluster เพิ่ม user ผ่าน global user list ส่วนหน้า edit user คืออีกฝั่งของ join `tb_cluster_user` ที่ดู assignment เดียวกัน จากมุมของ user
- [rbac](/th/platform/rbac) — กำหนด catalog ของ permission, role และ scoped assignment ที่อยู่เบื้องหลังทุก gate `cluster.*` ใน §4 รวมถึง bypass ของ super-admin และข้อยกเว้น bootstrap ส่วน §5 ของหน้านั้นอธิบายโมเดล role-enum รุ่นเก่าที่เคย gate โมดูลนี้จนถึง 2026-06
- [report-templates](/th/platform/report-templates) — ใช้ pattern route-guard เดียวกันแต่มี key `report_template.*` ของตัวเอง จึงโอนแบบจำลองการ gate ที่อธิบายไว้ที่นี่ไปใช้ได้ 1 ต่อ 1

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การต่อสาย `PrivateRoute` พร้อม key `requiredPermission` (authoritative สำหรับการ gate route; `SITEMAP.md` ยังแสดง role list รุ่นเก่าและ stale ในคอลัมน์ access)
- `../carmen-platform/src/pages/ClusterManagement.tsx` — หน้า list, แถบ Fleet Capacity, filter, ส่งออก CSV, การจัดการ soft-delete, คอลัมน์ audit, การป้องกันการลบ, row action ที่ gate ด้วย `<Can>`
- `../carmen-platform/src/pages/ClusterEdit.tsx` — หน้า orchestrator แบบ create/view/edit: scrollspy nav, hero, ส่วน Details/Branding/Business-Units/Users แบบแก้ไข-in-place, optimistic locking ด้วย `doc_version`, dialog เพิ่ม user, ตรรกะ license-cap
- `../carmen-platform/src/pages/clusterManagement/{ClusterHero,FleetCapacity,CapacityGauge,CapacityMeter}.tsx` และ `../carmen-platform/src/utils/capacity.ts` — สูตรคำนวณและการ render มาตรวัด capacity ที่ใช้ร่วมกันระหว่างหน้า list และหน้า edit
- `../carmen-platform/src/pages/clusterEdit/{ClusterEditNav,useClusterUsers}.ts(x)` และ `sections/{DetailsSection,BrandingSection,BusinessUnitsSection,UsersSection}.tsx` — scrollspy nav ของหน้า edit และ component แต่ละส่วน
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — control อัปโหลด logo/avatar ที่ใช้ร่วมกันบนส่วน Branding
- `../carmen-platform/src/services/clusterService.ts` — REST client (`/api-system/clusters` บวก endpoint อัปโหลด `/logo` และ `/avatar`)
- `../carmen-platform/src/types/` — TypeScript interface `Cluster`, `PresignedImage` และ `BusinessUnit` ที่ทั้งสองหน้าจอใช้

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/clusters/data-model) — field ของ entity cluster, ความสัมพันธ์ 1:N กับ BU, การ join ผ่าน `tb_cluster_user` และสอง field สำหรับ license-cap (stub — ยังไม่สมบูรณ์)
- [Permissions](/th/platform/clusters/permissions) — gate `requiredPermission` ของแต่ละ route, gate `<Can>` ภายในหน้า (รวม variant แบบ cluster-scoped) และสิ่งที่ key `cluster.*` แต่ละตัวเปิดให้ทำ (stub — ยังไม่สมบูรณ์)
- [UI Screens](/th/platform/clusters/ui-screens) — หน้า list `ClusterManagement` (แถบ Fleet Capacity) และเลย์เอาต์แบบ scrollspy ของ `ClusterEdit` (Overview/Details/Branding/Business Units/Users) รวมถึง flow ของ dialog เพิ่ม user และ bulk action (stub — ยังไม่สมบูรณ์)
