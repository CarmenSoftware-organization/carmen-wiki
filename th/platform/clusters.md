---
title: คลัสเตอร์ (Clusters)
description: ภาพรวมโมดูล Clusters — กลุ่ม tenant ระดับบนสุดที่เป็นเจ้าของ business unit และ user ตามไลเซนส์
published: true
date: 2026-06-10T16:30:00.000Z
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# คลัสเตอร์ (Clusters)

โมดูล **Clusters** เป็นจุดเริ่มต้นของ container ระดับองค์กรที่ใหญ่ที่สุด ใน Carmen Platform โดย cluster หนึ่ง ๆ จะรวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้นเข้าด้วยกัน นอกจากนี้ cluster ยังเป็นที่เก็บข้อมูล **ไลเซนส์** — ทั้งจำนวน BU สูงสุดที่ cluster นี้มีได้ และ (ผ่านการรวมยอด จากทุก BU) จำนวน user ทั้งหมดที่ครอบคลุม route และ action ที่แก้ไขข้อมูลในโมดูลนี้ถูก gate ด้วย permission key `cluster.*` (ดู [Platform RBAC](/th/platform/rbac))

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ตู้คอนเทนเนอร์ของ tenant ที่รวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้น และเป็นที่เก็บไลเซนส์ ("จำนวน BU สูงสุดต่อ cluster" และจำนวน user รวมจากทุก BU) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA; การเข้าถึงของ operator ต้องได้รับ grant permission `cluster.*` ([rbac](/th/platform/rbac)) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_cluster` (ฟิลด์: `code`, `name`, `alias_name`, `logo_file_token`, `avatar_file_token`, `max_license_bu`, `is_active`, soft-delete trio), `tb_business_unit` (1:N), `tb_cluster_user` (M:N join ที่ถือ role per-cluster เป็น `admin`/`user`) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูล Clusters เปิดเผย aggregate root ของ cluster ผ่านรูปแบบสองหน้าจอ มาตรฐานที่ใช้ในทุกที่ใน Platform SPA:

- **`/clusters` → `ClusterManagement`** — `DataTable` แบบ server-side พร้อมการค้นหาแบบ debounce, แผง filter แบบ Sheet (active/inactive และ ตัวเลือก "show soft-deleted"), ส่งออก CSV และจดจำสถานะ UI ใน `localStorage` (search, page, perpage, sort, filters)
- **`/clusters/new` → `ClusterEdit` (โหมด create)** — แสดงการ์ด "Cluster Details" การ์ดเดียว เมื่อสร้างสำเร็จ หน้าจะ navigate ไป `/clusters/:id` ซึ่ง **ไม่ใช่ route ที่ลงทะเบียนไว้** — catch-all ของ SPA จะพา operator ไปลงที่ Dashboard ในปัจจุบัน (ดู [UI Screens](/th/platform/clusters/ui-screens) §3)
- **`/clusters/:id/edit` → `ClusterEdit` (โหมด view/edit)** — เลย์เอาต์ สามคอลัมน์ คอลัมน์ซ้ายคือการ์ด Cluster Details (เริ่มต้นแบบดูอย่างเดียว เปลี่ยนเป็นแก้ไขผ่านปุ่ม Edit — ซึ่ง render เฉพาะภายใน `<Can permission="cluster.update" clusterId={id}>` เท่านั้น) คอลัมน์ขวาขยายกว้าง 2 คอลัมน์ และมี การ์ดวางซ้อนกันสามใบคือ **Branding** (อัปโหลด logo + avatar), **Business Units** ใน cluster นี้ และ **Users** ใน cluster นี้ การ์ดเหล่านี้แสดงเคียงข้างกันใน grid เสมอ ผู้ใช้พับเก็บเองไม่ได้

การ์ด Business Units แสดงรายการ BU ทุกตัวที่ `cluster_id` ตรงกับ cluster ปัจจุบัน พร้อมปุ่ม **Add** ที่นำทางไป `/business-units/new?cluster_id=<id>` เพื่อให้ BU ใหม่ผูกกับ cluster ตั้งแต่เริ่ม ส่วนการ์ด Users แสดงข้อมูล จาก `tb_cluster_user` (กรองตาม cluster_id) และรองรับ add / edit / remove ผ่าน dialog — dialog เพิ่ม user จะค้นหา user จาก pool ทั่วระบบ และให้ ผู้ใช้เลือก cluster role (`admin` หรือ `user`) พร้อม parent BU ของ assignment นั้น

## 2. บริบททางธุรกิจ

โดยทั่วไป cluster จะแทนองค์กรลูกค้าหนึ่งรายหรือเครือโรงแรมที่ทำสัญญา Carmen Platform หนึ่งฉบับ สัญญานี้กำหนดว่าลูกค้ามีสิทธิ์ใช้ BU ได้กี่ตัว และ (ต่อ BU) มีสิทธิ์มี named user กี่คน ตัว cluster record คือที่เก็บ ค่า cap เหล่านี้ และเป็นที่ที่ทำการคำนวณ "ยังอยู่ใต้ลิมิตหรือไม่"

- ปุ่ม **Add BU** บนหน้า edit cluster จะ disable ตัวเองเมื่อ `business_units.length >= max_license_bu` พร้อม tooltip ("License limit reached (N/M)")
- Dialog **Add User** จะ disable ตัวเลือก BU ที่ `max_license_users` เต็มแล้ว และแสดงยอด "X of Y licensed users" ที่กำลังใช้งานต่อ BU
- เมื่อรวม cluster + BU ภายใต้สังกัด คือกลไกที่ Carmen ใช้กำหนดว่า user คนหนึ่งสลับเข้าใช้ BU ใดได้บ้าง — assignment ถูกเก็บใน `tb_cluster_user` พร้อมตัวชี้ `parent_bu_id`

เนื่องจาก cluster ครอบทั้ง **การกำหนดไลเซนส์เชิงพาณิชย์** และ **การกำหนดขอบเขตการเข้าถึง** route และ action ที่แก้ไขข้อมูลทุกตัวของ cluster จึงถูก gate ด้วย permission key `cluster.*` (§4) session ที่ไม่มี key ที่ต้องการจะเจอ `AccessDenied` เมื่อพิมพ์ URL เข้า `/clusters*` โดยตรง และจะไม่เห็นปุ่ม Add/Edit/Delete ที่ grant ของตนไม่ครอบคลุม — โดยมีหนึ่งข้อยกเว้น: ปุ่ม Add Cluster ใน empty state ไม่ถูก gate และถูกจับโดย route guard เท่านั้น (ดู [Permissions](/th/platform/clusters/permissions) §7)

## 3. แนวคิดสำคัญ

- **Cluster** — container ที่มีชื่อ ประกอบด้วย `code`, `name`, `alias_name` (ไม่เกิน 3 ตัวอักษร แสดงเฉพาะในฟอร์ม edit และคอลัมน์ Alias ของ CSV export เท่านั้น — ไม่มี UI badge ใด render ค่านี้), flag `is_active` และ cap `max_license_bu` (optional) ส่วน soft-delete ติดตามผ่าน `deleted_at` / `deleted_by_name`
- **Branding (logo + avatar)** — แต่ละ cluster มี **logo** สี่เหลี่ยมผืนผ้าและ **avatar** สี่เหลี่ยมจัตุรัส เก็บใน Prisma เป็น file token (`logo_file_token`, `avatar_file_token`) และ API คืนค่าเป็น presigned object ฝังในตัว (`logo: { url, expires_at }`, `avatar: { url, expires_at }`) การอัปโหลดทำบนการ์ด Branding ของหน้า edit ผ่าน multipart endpoint เฉพาะ ส่วนหน้า list แสดง thumbnail ของ logo (fallback เป็น avatar)
- **Cluster ↔ Business Unit (1:N)** — BU ทุกตัวถือ `cluster_id` หน้า edit cluster จะกรอง BU list ระดับ global ให้เหลือเฉพาะลูกของ cluster ตัวเอง และนับว่ามีกี่ตัวที่ active
- **Cluster ↔ User (M:N ผ่าน `tb_cluster_user`)** — เพิ่ม user เข้า cluster โดย insert row ที่มี key fields คือ `user_id`, `cluster_id`, `role` (`admin` | `user`), `is_active` และ `parent_bu_id` (optional) การ์ด Users บน `ClusterEdit` อ่าน join นี้ผ่าน `GET /api-system/user/clusters/:clusterId`
- **License caps** — มีสอง limit อิสระต่อกัน: ระดับ cluster `max_license_bu` (จำกัดจำนวน BU ที่ผูกได้) และระดับ BU `max_license_users` (จำกัดจำนวน cluster_user ที่มี BU นี้เป็น parent) หน้า edit cluster รวม cap ของทุก BU เป็น badge "total licensed users"
- **คอลัมน์ audit** — หน้า list แสดงคอลัมน์ Created และ Updated (timestamp พร้อมชื่อผู้กระทำ) SPA จะ flatten object `audit` แบบ nested จาก API response (`audit.created.{at,name}`, `audit.updated.{at,name}`) สำหรับคอลัมน์วันที่ โดยยอมรับ shape แบบ flat รุ่นเก่าด้วย ซึ่งชนะเมื่อมีค่า (`item.created_at ?? item.audit?.created?.at`) เซลล์ Updated จะถูกละเมื่อ `updated_at` เท่ากับ `created_at`
- **Soft delete** — หน้า list จะซ่อน row ที่ `deleted_at IS NOT NULL` เว้นแต่จะเปิด filter "Show soft-deleted clusters" row ที่ถูก soft-delete จะมี badge "Deleted" สีแดงกำกับ (tooltip ของ badge ระบุชื่อผู้ลบ) และเมื่อเปิด filter จะมีคอลัมน์ audit "Deleted By" เพิ่มต่อท้าย

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
| หน้า edit: toggle Edit | `<Can>` | `cluster.update` | ใช่ — `clusterId={id}` |

มีสองจุดที่ควรสังเกต ข้อแรก `cluster.delete` มีอยู่ **เฉพาะ** ในรูป gate ภายในหน้าเท่านั้น — ไม่มี route ใดต้องการมัน ดังนั้น session ที่ถือเพียง `cluster.read` จะเห็นหน้า list แต่เมนู action ของ row จะว่างเปล่า ข้อสอง gate แบบ scoped (`clusterId`) จะเข้า branch การ resolve แบบ cluster-specific: role assignment ที่ scope ไว้กับ cluster A จะเปิด Edit/Delete เฉพาะบน row ของ cluster A เท่านั้น ขณะที่ route guard แบบ unscoped จะผ่านด้วย grant แบบ cluster-scoped ของ cluster ใดก็ได้ ปุ่ม Save ของฟอร์ม edit ไม่ถูกห่อแยกต่างหาก — ถ้าไม่มี toggle Edit ที่ gate ด้วย `<Can>` ฟอร์มจะไม่มีวันออกจากโหมด view ทำให้ไปถึง Save ไม่ได้ อัลกอริทึมการ resolve และเมทริกซ์ gate ทั้ง SPA อยู่ใน [rbac permissions](/th/platform/rbac/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [business-units](/th/platform/business-units) — cluster เป็นเจ้าของ BU แบบ 1:N หน้า edit cluster คือจุดมาตรฐานในการสร้าง BU ที่ผูกกับ cluster ตั้งแต่ต้น (เรียก `navigate('/business-units/new?cluster_id=<id>')`) **Gotcha:** route `/business-units*` ใช้ key `cluster.read`/`cluster.create`/`cluster.update` ซ้ำ — ไม่มี key `business_unit.*` ดังนั้นการ grant สิทธิ์เข้าถึง cluster จะมอบ Business Units ไปด้วย
- [users](/th/platform/users) — cluster เพิ่ม user ผ่าน global user list ส่วนหน้า edit user คืออีกฝั่งของ join `tb_cluster_user` ที่ดู assignment เดียวกัน จากมุมของ user
- [rbac](/th/platform/rbac) — กำหนด catalog ของ permission, role และ scoped assignment ที่อยู่เบื้องหลังทุก gate `cluster.*` ใน §4 รวมถึง bypass ของ super-admin และข้อยกเว้น bootstrap ส่วน §5 ของหน้านั้น documented โมเดล role-enum รุ่นเก่าที่เคย gate โมดูลนี้จนถึง 2026-06
- [report-templates](/th/platform/report-templates) — ใช้ pattern route-guard เดียวกันแต่มี key `report_template.*` ของตัวเอง จึงโอนแบบจำลองการ gate ที่ documented ที่นี่ไปใช้ได้ 1 ต่อ 1

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การต่อสาย `PrivateRoute` พร้อม key `requiredPermission` (authoritative สำหรับการ gate route; `SITEMAP.md` ยังแสดง role list รุ่นเก่าและ stale ในคอลัมน์ access)
- `../carmen-platform/src/pages/ClusterManagement.tsx` — หน้า list, thumbnail ของ logo, filter, ส่งออก CSV, การจัดการ soft-delete, คอลัมน์ audit, row action ที่ gate ด้วย `<Can>`
- `../carmen-platform/src/pages/ClusterEdit.tsx` — หน้า create/view/edit การ์ด Branding, การ์ด Business Units, การ์ด Users, dialog เพิ่ม user, ตรรกะ license-cap
- `../carmen-platform/src/components/BrandingImageUpload.tsx` — control อัปโหลด logo/avatar ที่ใช้ร่วมกันบนการ์ด Branding
- `../carmen-platform/src/services/clusterService.ts` — REST client (`/api-system/clusters` บวก endpoint อัปโหลด `/logo` และ `/avatar`)
- `../carmen-platform/src/types/` — TypeScript interface `Cluster`, `PresignedImage` และ `BusinessUnit` ที่ทั้งสองหน้าจอใช้

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/clusters/data-model) — field ของ entity cluster, ความสัมพันธ์ 1:N กับ BU, การ join ผ่าน `tb_cluster_user` และสอง field สำหรับ license-cap (stub — ยังไม่สมบูรณ์)
- [Permissions](/th/platform/clusters/permissions) — gate `requiredPermission` ของแต่ละ route, gate `<Can>` ภายในหน้า (รวม variant แบบ cluster-scoped) และสิ่งที่ key `cluster.*` แต่ละตัวเปิดให้ทำ (stub — ยังไม่สมบูรณ์)
- [UI Screens](/th/platform/clusters/ui-screens) — หน้า list `ClusterManagement` และเลย์เอาต์ สี่การ์ดของ `ClusterEdit` (Details, Branding, Business Units, Users) รวมถึง flow ของ dialog เพิ่ม user (stub — ยังไม่สมบูรณ์)
