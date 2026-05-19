---
title: คลัสเตอร์ (Clusters)
description: ภาพรวมโมดูล Clusters — กลุ่ม tenant ระดับบนสุดที่เป็นเจ้าของ business unit และ user ตามไลเซนส์
published: true
date: 2026-05-19T22:00:00.000Z
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# คลัสเตอร์ (Clusters)

โมดูล **Clusters** เป็นจุดเริ่มต้นของ container ระดับองค์กรที่ใหญ่ที่สุด
ใน Carmen Platform โดย cluster หนึ่ง ๆ จะรวม business unit (BU) และ user
ที่ผูกกับ BU เหล่านั้นเข้าด้วยกัน นอกจากนี้ cluster ยังเป็นที่เก็บข้อมูล
**ไลเซนส์** — ทั้งจำนวน BU สูงสุดที่ cluster นี้มีได้ และ (ผ่านการรวมยอด
จากทุก BU) จำนวน user ทั้งหมดที่ครอบคลุม route ในโมดูลนี้จำกัดเฉพาะบทบาท
ระดับ admin ทั้งสามเท่านั้น

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ตู้คอนเทนเนอร์ของ tenant ที่รวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้น และเป็นที่เก็บไลเซนส์ ("จำนวน BU สูงสุดต่อ cluster" และจำนวน user รวมจากทุก BU) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Platform admin และวิศวกร support ของ Carmen (`platform_admin`, `support_manager`, `support_staff`) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `cluster` (ฟิลด์: `code`, `name`, `alias_name`, `logo_url`, `max_license_bu`, `is_active`, soft-delete trio), `business_unit` (1:N), `tb_cluster_user` (M:N join ที่ถือ role per-cluster เป็น `admin`/`user`) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูล Clusters เปิดเผย aggregate root ของ cluster ผ่านรูปแบบสองหน้าจอ
มาตรฐานที่ใช้ในทุกที่ใน Platform SPA:

- **`/clusters` → `ClusterManagement`** — `DataTable` แบบ server-side
  พร้อมการค้นหาแบบ debounce, แผง filter แบบ Sheet (active/inactive และ
  ตัวเลือก "show soft-deleted"), ส่งออก CSV และจดจำสถานะ UI ใน
  `localStorage` (search, page, perpage, sort, filters)
- **`/clusters/new` → `ClusterEdit` (โหมด create)** — แสดงการ์ด
  "Cluster Details" การ์ดเดียว เมื่อสร้างสำเร็จ หน้าจะเปลี่ยน route ไป
  ที่หน้า edit ของ id ที่เพิ่งสร้าง
- **`/clusters/:id/edit` → `ClusterEdit` (โหมด view/edit)** — เลย์เอาต์
  สามคอลัมน์ คอลัมน์ซ้ายคือการ์ด Cluster Details (เริ่มต้นแบบดูอย่างเดียว
  เปลี่ยนเป็นแก้ไขผ่านปุ่ม Edit) คอลัมน์ขวาขยายกว้าง 2 คอลัมน์ และมี
  การ์ดวางซ้อนกันสองใบคือ **Business Units** ใน cluster นี้ และ
  **Users** ใน cluster นี้ การ์ดเหล่านี้แสดงเคียงข้างกันใน grid เสมอ
  ผู้ใช้พับเก็บเองไม่ได้

การ์ด Business Units แสดงรายการ BU ทุกตัวที่ `cluster_id` ตรงกับ cluster
ปัจจุบัน พร้อมปุ่ม **Add** ที่นำทางไป `/business-units/new?cluster_id=<id>`
เพื่อให้ BU ใหม่ผูกกับ cluster ตั้งแต่เริ่ม ส่วนการ์ด Users แสดงข้อมูล
จาก `tb_cluster_user` (กรองตาม cluster_id) และรองรับ add / edit / remove
ผ่าน dialog — dialog เพิ่ม user จะค้นหา user จาก pool ทั่วระบบ และให้
ผู้ใช้เลือก cluster role (`admin` หรือ `user`) พร้อม parent BU ของ
assignment นั้น

## 2. บริบททางธุรกิจ

โดยทั่วไป cluster จะแทนองค์กรลูกค้าหนึ่งรายหรือเครือโรงแรมที่ทำสัญญา
Carmen Platform หนึ่งฉบับ สัญญานี้กำหนดว่าลูกค้ามีสิทธิ์ใช้ BU ได้กี่ตัว
และ (ต่อ BU) มีสิทธิ์มี named user กี่คน ตัว cluster record คือที่เก็บ
ค่า cap เหล่านี้ และเป็นที่ที่ทำการคำนวณ "ยังอยู่ใต้ลิมิตหรือไม่"

- ปุ่ม **Add BU** บนหน้า edit cluster จะ disable ตัวเองเมื่อ
  `business_units.length >= max_license_bu` พร้อม tooltip
  ("License limit reached (N/M)")
- Dialog **Add User** จะ disable ตัวเลือก BU ที่ `max_license_users`
  เต็มแล้ว และแสดงยอด "X of Y licensed users" ที่กำลังใช้งานต่อ BU
- เมื่อรวม cluster + BU ภายใต้สังกัด คือกลไกที่ Carmen ใช้กำหนดว่า user
  คนหนึ่งสลับเข้าใช้ BU ใดได้บ้าง — assignment ถูกเก็บใน
  `tb_cluster_user` พร้อมตัวชี้ `parent_bu_id`

เนื่องจาก cluster ครอบทั้ง **การกำหนดไลเซนส์เชิงพาณิชย์** และ
**การกำหนดขอบเขตการเข้าถึง** จึงเปิดให้เฉพาะบทบาทระดับ admin ทั้งสาม
สร้าง แก้ไข หรือลบได้ ผู้ใช้บทบาทอื่นที่เข้า `/clusters*` จะเจอ
`AccessDenied`

## 3. แนวคิดสำคัญ

- **Cluster** — container ที่มีชื่อ ประกอบด้วย `code`, `name`,
  `alias_name` (ไม่เกิน 3 ตัวอักษร ใช้เป็น prefix สั้นใน UI badge),
  `logo_url` (optional), flag `is_active` และ cap `max_license_bu`
  (optional) ส่วน soft-delete ติดตามผ่าน `deleted_at` /
  `deleted_by_name`
- **Cluster ↔ Business Unit (1:N)** — BU ทุกตัวถือ `cluster_id` หน้า
  edit cluster จะกรอง BU list ระดับ global ให้เหลือเฉพาะลูกของ cluster
  ตัวเอง และนับว่ามีกี่ตัวที่ active
- **Cluster ↔ User (M:N ผ่าน `tb_cluster_user`)** — เพิ่ม user เข้า
  cluster โดย insert row ที่มี key fields คือ `user_id`, `cluster_id`,
  `role` (`admin` | `user`), `is_active` และ `parent_bu_id` (optional)
  การ์ด Users บน `ClusterEdit` อ่าน join นี้ผ่าน
  `GET /api-system/user/cluster/:clusterId`
- **License caps** — มีสอง limit อิสระต่อกัน: ระดับ cluster
  `max_license_bu` (จำกัดจำนวน BU ที่ผูกได้) และระดับ BU
  `max_license_users` (จำกัดจำนวน cluster_user ที่มี BU นี้เป็น parent)
  หน้า edit cluster รวม cap ของทุก BU เป็น badge "total licensed users"
- **Soft delete** — หน้า list จะซ่อน row ที่ `deleted_at IS NOT NULL`
  เว้นแต่จะเปิด filter "Show soft-deleted clusters" row ที่ถูก
  soft-delete จะมี badge "Deleted" สีแดงกำกับ

## 4. บทบาทและ Persona

route ทั้งสามของ cluster ห่อด้วย `PrivateRoute` ที่มี `allowedRoles` ชุด
เดียวกัน ไม่มี gate เพิ่มเติมในระดับ action ภายในหน้า — เมื่อ route
resolve แล้ว user สามารถใช้ทุกปุ่มบนหน้าได้ (Add, Edit, Delete, Export,
Add User, Remove User)

| บทบาท | List (`/clusters`) | Create (`/clusters/new`) | Edit / Delete | จัดการ BU และ User |
|---|---|---|---|---|
| `platform_admin` | Full | Full | Full | Full |
| `support_manager` | Full | Full | Full | Full |
| `support_staff` | Full | Full | Full | Full |
| บทบาทอื่นที่ login อยู่ | `AccessDenied` | `AccessDenied` | `AccessDenied` | `AccessDenied` |

string ที่ใช้ gate ใน `src/App.tsx` คือ
`allowedRoles={["platform_admin", "support_manager", "support_staff"]}`
บน route ทั้งสาม รูปแบบนี้เหมือนกับโมดูล Report Templates ทุกประการ

## 5. โมดูลที่เกี่ยวข้อง

- [[business-units]] — cluster เป็นเจ้าของ BU แบบ 1:N หน้า edit cluster
  คือจุดมาตรฐานในการสร้าง BU ที่ผูกกับ cluster ตั้งแต่ต้น (เรียก
  `navigate('/business-units/new?cluster_id=<id>')`)
- [[users]] — cluster เพิ่ม user ผ่าน global user list ส่วนหน้า edit
  user คืออีกฝั่งของ join `tb_cluster_user` ที่ดู assignment เดียวกัน
  จากมุมของ user
- [[auth-roles]] — กำหนดความหมายของ `platform_admin`, `support_manager`
  และ `support_staff` การ gate route ของ cluster เป็นเพียงการนำค่า role
  เหล่านี้ไปใช้ใน `PrivateRoute`
- [[report-templates]] — ใช้รูปแบบ `allowedRoles` เดียวกันทุกประการ
  จึงโอนแบบจำลองสิทธิ์ที่ documented ที่นี่ไปใช้ได้ 1 ต่อ 1

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/SITEMAP.md` — ตาราง route เป็น source of truth
  ของ route cluster ทั้งสามและ access list
- `../carmen-platform/src/App.tsx` — การต่อสาย `PrivateRoute` พร้อม
  `allowedRoles`
- `../carmen-platform/src/pages/ClusterManagement.tsx` — หน้า list,
  filter, ส่งออก CSV, การจัดการ soft-delete, คอลัมน์นับ BU และ user
- `../carmen-platform/src/pages/ClusterEdit.tsx` — หน้า create/view/edit
  การ์ด Business Units, การ์ด Users, dialog เพิ่ม user, ตรรกะ
  license-cap
- `../carmen-platform/src/services/clusterService.ts` — REST client
  (`/api-system/cluster`)
- `../carmen-platform/src/types/` — TypeScript interface `Cluster` และ
  `BusinessUnit` ที่ทั้งสองหน้าจอใช้

## 7. หน้าในโมดูลนี้

- [[clusters/data-model|Data Model]] — field ของ entity cluster, ความสัมพันธ์ 1:N
  กับ BU, การ join ผ่าน `tb_cluster_user` และสอง field สำหรับ
  license-cap (stub — ยังไม่สมบูรณ์)
- [[clusters/permissions|Permissions]] — gate `allowedRoles` แต่ละ route และสิ่งที่
  แต่ละบทบาทระดับ admin ทำได้บนหน้าจอ (stub — ยังไม่สมบูรณ์)
- [[clusters/ui-screens|UI Screens]] — หน้า list `ClusterManagement` และเลย์เอาต์
  สามการ์ดของ `ClusterEdit` รวมถึง flow ของ dialog เพิ่ม user
  (stub — ยังไม่สมบูรณ์)
