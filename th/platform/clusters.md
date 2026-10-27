---
title: คลัสเตอร์ (Clusters)
description: ภาพรวมโมดูล Clusters — กลุ่ม tenant ระดับบนสุดที่เป็นเจ้าของ business unit และ user ตามไลเซนส์ ปัจจุบันอ้างอิงจาก licence ledger แบบมีวันหมดอายุแทน cap แบบ static เดิม
published: true
date: '2026-10-27T15:00:00.000Z'
tags: platform/clusters, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# คลัสเตอร์ (Clusters)

โมดูล **Clusters** เป็นจุดเริ่มต้นของ container ระดับองค์กรที่ใหญ่ที่สุดใน Carmen Blue โดย cluster หนึ่ง ๆ จะรวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้นเข้าด้วยกัน ลิมิตไลเซนส์ — จำนวน BU สูงสุดที่ cluster มีได้ และจำนวน named user ที่ครอบคลุม — แต่เดิมเป็นคอลัมน์ static บน record ของ cluster/BU แต่ตั้งแต่มีการปรับระบบไลเซนส์ระหว่าง 2026-07-29 ถึง 2026-09-04 ค่าเหล่านี้กลายเป็นแถวที่ "ชนะ" ของ ledger การซื้อแบบมีช่วงวันที่แทน (ดู §3) route และ action ที่แก้ไขข้อมูลในโมดูลนี้ถูก gate ด้วย permission key `cluster.*` **และ** feature flag `clusters` (ดู [Platform RBAC](/th/platform/rbac) และ [Permissions](/th/platform/clusters/permissions))

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** container ของ tenant ที่รวม business unit (BU) และ user ที่ผูกกับ BU เหล่านั้น และลิงก์ไปยัง licence ledger ที่ปัจจุบันเป็นที่เก็บ cap ของจำนวน BU และจำนวนที่นั่ง &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA; การเข้าถึงของ operator ต้องได้รับ grant permission `cluster.*` ([rbac](/th/platform/rbac)) และ feature flag `clusters` ต้องเปิดอยู่ &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_cluster` (ฟิลด์: `code`, `name`, `alias_name`, `logo_file_token`, `avatar_file_token`, `is_active`, `doc_version`, soft-delete trio — **ไม่มีคอลัมน์ licence-cap อีกต่อไป**), `tb_business_unit` (1:N), `tb_cluster_user` (M:N join ที่ถือ role per-cluster เป็น `admin`/`user` — **ไม่มี `parent_bu_id` แล้ว**), `tb_cluster_license` (ledger การซื้อโควตา BU ของ cluster) &nbsp;·&nbsp; `tb_cluster_note` (ใหม่ 2026-10-26 — บันทึกภายในและไฟล์ของเจ้าหน้าที่) &nbsp;·&nbsp; **หน้าย่อย:** 3 &nbsp;·&nbsp; **Permission key:** `cluster.read` (list/nav) + `cluster.create`/`cluster.update`/`cluster.delete` บวก `activity_log.read` (View History) และ `cluster_note.view`/`cluster_note.manage` ใหม่ (แท็บ Notes) &nbsp;·&nbsp; **Feature-flag key:** `clusters` &nbsp;·&nbsp; **superAdminOnly:** ไม่ใช่ — gate ด้วย permission ไม่ใช่ flag แบบ super-admin-only (อ้างอิง `../carmen-backstage/src/components/nav/backstageNav.ts`)

![คลัสเตอร์ (Clusters) screen](/screenshots/platform/clusters/index.png)

## 1. ภาพรวม

โมดูล Clusters เปิดเผย aggregate root ของ cluster ผ่านสองหน้าจอ ซึ่งถูกเขียนใหม่สองรอบนับตั้งแต่ sync ฉบับเต็มครั้งล่าสุด (2026-07-29):

- **`/clusters` → `ClusterManagement`** — `DataTable` แบบ server-side พร้อมการค้นหาแบบ debounce, แผง filter แบบ Sheet (active/inactive, "show soft-deleted"), ส่งออก CSV, แถบสรุป **Fleet Capacity** ทั้งฝูงเหนือตาราง (ตอนนี้อ่านจาก endpoint เฉพาะ `GET /api-system/clusters/summary` ไม่ใช่การรวมยอดฝั่ง client แล้ว) และจดจำสถานะ UI ใน `localStorage` แถบ Fleet Capacity เพิ่มสถิติ **Quota expiring** ที่คลิกได้ (cluster ที่ใบโควตา BU ที่ชนะจะหมดอายุใน 30 วัน) นอกเหนือจากสถิติ Near limit เดิม
- **`/clusters/new` → `ClusterEdit` (โหมด create)** — เลย์เอาต์สองคอลัมน์: พรีวิว `ClusterDraftPlate` แบบสดข้างฟอร์มสองการ์ด — Identity และ (ใหม่) **First Quota Licence** ซึ่งออกใบโควตา BU แถวแรก (`tb_cluster_license`) ให้ cluster ตั้งแต่ตอนสร้าง เมื่อสำเร็จจะ navigate ตรงไป `/clusters/:id/edit`
- **`/clusters/:id/edit` → `ClusterEdit` (โหมด view/edit)** — แผ่นป้ายตัวตนที่แสดงตลอดเวลา (`ClusterPlate`: branding, ชื่อ, สถานะ, code/alias, มาตรวัดไลเซนส์สองแถบแบบ tick-strip) พร้อมเนื้อหาแบบหลายแท็บด้านล่าง — **Licensing** (ค่าเริ่มต้น), **Business Units**, **Users** และ **Notes** (ใหม่ใน 2026-10; เฉพาะเจ้าหน้าที่ ต้องมี `cluster_note.view`) — แทนที่เอกสารแบบ scrollspy คอลัมน์เดียว (Overview/Details/Branding/Business Units/Users) ที่หน้านี้เคยอธิบายไว้เมื่อเดือนกรกฎาคม ไม่มี toggle Edit ระดับหน้าอีกต่อไป — ทุก field บนแผ่นป้ายและทุก action ในแท็บแก้ไขได้เป็นอิสระตามสิทธิ์ `cluster.update` (`canEdit`) และแถบ "Unsaved changes" แบบ sticky จะปรากฏเมื่อ field บนแผ่นป้ายต่างจาก snapshot ล่าสุด การบันทึกป้องกันด้วย token optimistic-lock `doc_version` (ดู [Data Model](/th/platform/clusters/data-model) §2.1)

แท็บ **Notes** ใหม่ ([UI Screens](/th/platform/clusters/ui-screens) §4.6) คือ timeline บันทึกภายในที่แนบไฟล์ได้สูงสุดห้าไฟล์ต่อบันทึก (ไฟล์ละ 10 MB) พร้อมแก้ไข, soft delete, restore, แผงไฟล์ และประวัติรายบันทึก; tenant ไม่เห็นเลย

หน้าจอทั้งสองของ cluster ยังมี action **View History** (permission `activity_log.read` ใหม่รอบนี้) เปิดแผ่นประวัติการเปลี่ยนแปลงที่ใช้ร่วมกันสำหรับ record ของ cluster นั้น

แท็บ Business Units แสดงรายการ BU ทุกตัวที่ `cluster_id` ตรงกับ cluster ปัจจุบัน พร้อมช่องค้นหา, filter Active/Inactive และคอลัมน์ Code/Name ที่ sort ได้ของตัวเอง BU ที่มีอันดับ (HQ มาก่อน ตามด้วยตัวที่เก่าที่สุด ตรงกับ database view เป๊ะ) เกินโควตา BU ของ cluster จะถูกติดป้าย "Over limit" ปุ่ม **Add** จะนำทางไป `/business-units/new?cluster_id=<id>` เพื่อให้ BU ใหม่ผูกกับ cluster ตั้งแต่เริ่ม แท็บ Users แสดงรายการจาก `tb_cluster_user` พร้อมการแก้ไข role แบบ inline ตรงในแถวของตาราง, คอลัมน์ **Seat** พร้อม action **Release / Restore seat** ราย member และ banner เกินโควตา (ใหม่ ดู [UI Screens](/th/platform/clusters/ui-screens) §4.4) และเลือกหลายรายการด้วย checkbox สำหรับ action แบบกลุ่ม **Remove** — ส่วน action กลุ่ม **Move to BU** ที่เคยบันทึกไว้ก่อนหน้านี้ไม่มีอยู่แล้ว เพราะ field ที่มันย้าย (`parent_bu_id`) ถูกถอดออกจาก schema ไปแล้ว

## 2. บริบททางธุรกิจ

โดยทั่วไป cluster จะแทนองค์กรลูกค้าหนึ่งรายหรือเครือโรงแรมที่ทำสัญญา Carmen Blue หนึ่งฉบับ สัญญากำหนดว่าลูกค้ามีสิทธิ์ใช้ BU ได้กี่ตัวและมีสิทธิ์มีที่นั่งกี่ที่ — cap เหล่านี้ตอนนี้เป็น **แถวใบซื้อที่มีวันที่** ไม่ใช่ field แบบ static บน record cluster/BU เองแล้ว:

- **โควตา BU** มาจาก `tb_cluster_license` — ledger การซื้อโควตา BU ต่อ cluster โควตาที่มีผลคือ **ใบที่ชนะใบเดียว** (ครอบคลุม "ตอนนี้" และยังไม่ถูกยกเลิก) ไม่ใช่ผลรวมของทุกใบที่เคยซื้อ ไม่มีใบที่ชนะ = โควตา `0` ซึ่งเป็นศูนย์จริง ไม่ใช่ "ไม่จำกัด"
- **ที่นั่ง** มาจาก `tb_business_unit_license` — ledger ต่อ BU ที่รวมยอดจากทุก BU ในคลัสเตอร์ที่ยังคุ้มครองอยู่ เช่นเดียวกับโควตา BU การไม่มีใบคุ้มครองตอนนี้หมายถึงสระ **0 ที่นั่ง** — กฎเดิม "`null` = ไม่จำกัด" สำหรับที่นั่งถูกกลับในรอบ 2026-10 (`toSeatPool()` ของ SPA; `assertSeatAvailable` ของ backend ไม่เคยมีสถานะไม่จำกัด)
- ปุ่ม **Add BU** บนหน้า edit cluster จะ disable ตัวเองเมื่อ `business_units.length >= bu_cap` พร้อม tooltip ("License limit reached (N/M)") การเกินโควตา BU ด้วยวิธีอื่น (เช่นซื้อใบใหม่ที่โควตาน้อยลงกว่าจำนวน BU ปัจจุบัน) จะไม่ลบหรือบล็อก BU ที่มีอยู่ — แต่จะติดป้าย "Over limit" ตามอันดับแทน (ดู [UI Screens](/th/platform/clusters/ui-screens) §4.3)
- Dialog **Add User** ตอนนี้เช็ค cap แบบทั้งคลัสเตอร์ ไม่ใช่ต่อ BU แล้ว — dialog ไม่ถาม BU ของสมาชิกใหม่อีกต่อไป เพราะไม่มี field ที่ผูกกับ BU บน membership ของ cluster-user แล้ว
- เมื่อรวม cluster + BU ภายใต้สังกัด คือกลไกที่ Carmen Blue ใช้กำหนดว่า user คนหนึ่งสลับเข้าใช้ BU ใดได้บ้าง
- **การป้องกันการลบ (deletion guard):** action Delete ของแถวในหน้า list จะถูกบล็อกฝั่ง client เมื่อ cluster เป้าหมายยังมี `bu_count > 0` — การลบ cluster ไม่ cascade ไปยัง business unit ของมันที่ฝั่ง backend
- การซื้อ ต่ออายุ หรือยกเลิกใบโควตา BU/ที่นั่งทำในโมดูล **licenses** (License Center) ทั้งหมด — หน้าของโมดูลนี้ลิงก์ไปที่นั่นแต่ไม่ได้บันทึก CRUD เต็มรูปแบบของ ledger ดู [Data Model](/th/platform/clusters/data-model) §2.4–2.5

## 3. แนวคิดสำคัญ

- **Cluster** — container ที่มีชื่อ ประกอบด้วย `code`, `name`, `alias_name` (ไม่เกิน 3 ตัวอักษร), flag `is_active` ส่วน soft-delete ติดตามผ่าน `deleted_at` / `deleted_by_name` **ไม่มีคอลัมน์ licence-cap อีกต่อไป** — `max_license_bu` ถูกถอดออกทั้งจาก Prisma model และทุก path อ่าน/เขียนฝั่ง SPA (โค้ดฝั่ง SPA ตัวสุดท้ายที่อ่านค่านี้ถูกลบโดย commit `7fda015`)
- **Branding (logo + avatar)** — แต่ละ cluster มี **logo** สี่เหลี่ยมผืนผ้าและ **avatar** สี่เหลี่ยมจัตุรัส เก็บเป็น file token และ API คืนค่าเป็น presigned object ฝังในตัว ปุ่มอัปโหลดตอนนี้อยู่ในส่วนหัว `ClusterPlate` แบบกะทัดรัด ไม่ใช่แท็บ/ส่วน "Branding" แยกต่างหากแล้ว
- **Cluster ↔ Business Unit (1:N)** — BU ทุกตัวถือ `cluster_id`
- **Cluster ↔ User (M:N ผ่าน `tb_cluster_user`)** — เพิ่ม user เข้า cluster โดย insert row ที่มี key fields คือ `user_id`, `cluster_id`, `role` (`admin` | `user`), `is_active` **ไม่มี `parent_bu_id` แล้ว** — คอลัมน์นี้ถูกถอดออกจาก schema และแท็บ Users กับ dialog Add User ไม่มี field ของ Business Unit อีกต่อไป
- **Licence ledger โควตา BU (`tb_cluster_license`, ใหม่)** — หนึ่งแถวต่อการซื้อโควตา BU หนึ่งครั้ง มี `licensed_bus`, `start_date`/`end_date` และ field การยกเลิก ใบที่ชนะจะกำหนด `bu_cap`; `end_date` ของมันกลายเป็น `bu_cap_end_date` (แสดงเป็น "No expiry" เมื่อเป็น sentinel วันหมดอายุตลอดชีพ)
- **สระที่นั่งและผู้ถือที่นั่ง** — ใบซื้อที่นั่งต่อ BU (`tb_business_unit_license`) รวมยอดเป็น `total_max_license_users` ของ cluster; ใครที่*ถือ*ที่นั่งถูกตัดสินด้วยกฎ SQL ร่วมหนึ่งกฎใน backend (`seat.helper.ts`) และแสดงเป็น `users_count` และ object `seat` ราย member **Release seat** ปิดการใช้งาน link ของสมาชิกเข้า BU ของ cluster (ประทับ `tb_user_tb_business_unit.seat_released_at`); **Restore seat** ย้อนเฉพาะ link ที่ถูกประทับ
- **Licence ledger ที่นั่ง (`tb_business_unit_license`)** — ใบซื้อที่นั่งต่อ BU รวมยอดเป็น `total_max_license_users` ของ cluster แทนคอลัมน์ `tb_business_unit.max_license_users` ที่ถูกถอดออก (migration `20260821000000_drop_bu_max_license_users`)
- **Optimistic concurrency (`doc_version`)** — `tb_cluster` และ `tb_cluster_user` ยังมี counter `doc_version` หน้า edit จะส่งค่านี้กลับไปพร้อมทุก `PUT` และการบันทึกที่ล้าหลังจะแสดง toast "ถูกเปลี่ยนโดยคนอื่น" (ดู [Data Model](/th/platform/clusters/data-model) §2.1)
- **คอลัมน์ audit** — หน้า list แสดง Created และ Updated (timestamp + ผู้กระทำ) อ่านผ่าน helper `normalizeAudit()` ที่ยอมรับทั้ง object `audit` แบบ nested และ shape แบบ flat รุ่นเก่า
- **Soft delete** — หน้า list จะซ่อนแถวที่ถูกลบ เว้นแต่เปิด "Show soft-deleted clusters" การลบ cluster ที่ยังมี business unit อยู่จะถูกบล็อกฝั่ง client (§2)
- **Feature flag (`clusters`)** — ทุก route ของ cluster ตอนนี้มี check `feature="clusters"` บน `PrivateRoute` ด้วย ทำงานหลังจาก check permission: session ที่ไม่มีสิทธิ์ `cluster.*` จะยังเห็น 403 (ไม่ใช่ 404 จาก flag) แต่ session ที่มีสิทธิ์อยู่แล้วจะเห็น `NotFound` หรือหน้า "Coming Soon" ถ้า flag ถูกตั้งเป็น `hide`/`inactive` ตามลำดับ
- **View History (`activity_log.read`, ใหม่)** — หน้าจอทั้งสองของ cluster มี action ดูประวัติการเปลี่ยนแปลง; ระบบเริ่มบันทึกตั้งแต่ 2026-08-31 เท่านั้น ดังนั้น cluster ที่สร้างก่อนหน้านั้นจะเห็นไทม์ไลน์ว่างเปล่า ไม่ได้แปลว่าไม่เคยมีการแก้ไข

## 4. บทบาทและ Persona

การเข้าถึงเป็นแบบ permission-based ([Platform RBAC](/th/platform/rbac)): แต่ละ route ถือ key `requiredPermission` บวก key `feature` บน `PrivateRoute` และปุ่มที่แก้ไขข้อมูลยังถูกห่อด้วย gate `<Can>` เพิ่มเติม — บางตัวเป็นแบบ cluster-scoped ผ่าน prop `clusterId`

| Surface | ชนิดของ gate | Key | Scoped? |
|---|---|---|---|
| route `/clusters` | `requiredPermission` + `feature` | `cluster.read` + `clusters` | ไม่ |
| route `/clusters/new` | `requiredPermission` + `feature` | `cluster.create` + `clusters` | ไม่ |
| route `/clusters/:id/edit` | `requiredPermission` + `feature` | `cluster.update` + `clusters` | ไม่ |
| รายการ "Clusters" ใน sidebar | filter `permission` + `feature` | `cluster.read` + `clusters` | ไม่ |
| List: ปุ่ม Add Cluster | `<Can>` | `cluster.create` | ไม่ |
| List: action Edit ของ row | `<Can>` | `cluster.update` | ใช่ — `clusterId={row.original.id}` |
| List: action **View History** ของ row (ใหม่) | `<Can>` | `activity_log.read` | ใช่ — `clusterId={row.original.id}` |
| List: action Delete ของ row | `<Can>` | `cluster.delete` | ใช่ — `clusterId={row.original.id}` |
| หน้า edit: field บนแผ่นป้าย, อัปโหลด Branding, Add User, bulk actions | `canEdit = hasPermission('cluster.update', {clusterId})` | `cluster.update` | ใช่ — `clusterId={id}` |
| หน้า edit: action **View History** ที่หัวหน้า (ใหม่) | `<Can>` | `activity_log.read` | ใช่ — `clusterId={id}` |
| หน้า edit: แท็บ **Notes** (ใหม่ 2026-10) | `hasPermission('cluster_note.view', { clusterId })`; การเขียนต้องมี `cluster_note.manage` ด้วย | `cluster_note.view` / `cluster_note.manage` | ใช่ — `clusterId={id}` |
| แท็บ Users: ปุ่ม **Release / Restore seat** (ใหม่) | `canEdit` ใน UI; backend ต้องการสมาชิกภาพ cluster-admin หรือ super admin (ไม่มี RBAC key) | — | ใช่ |

สามจุดที่ควรสังเกต ข้อแรก session ที่ไม่มี grant ทั้งระดับ platform และ cluster-scoped เลยตอนนี้จะถูก resolve **ก่อน** ที่ check permission จะทำงานเสียอีก — `PrivateRoute` จะ redirect ไป `/cluster-admin` ถ้า session นั้นมี scope นั้น แทนที่จะแสดง 403 ซึ่งเป็น layer ใหม่ที่ยังไม่มีตอน sync ครั้งก่อน (ดู [Permissions](/th/platform/clusters/permissions) §5) ข้อสอง `cluster.delete` มีอยู่ **เฉพาะ** ในรูป gate ภายในหน้าเท่านั้น — ไม่มี route ใดต้องการมัน ข้อสาม gate แบบ scoped (`clusterId`) จะเข้า branch การ resolve แบบ cluster-specific: role assignment ที่ scope ไว้กับ cluster A จะเปิด Edit/Delete/View History เฉพาะบน row ของ cluster A เท่านั้น ขณะที่ route guard แบบ unscoped จะผ่านด้วย grant แบบ cluster-scoped ของ cluster ใดก็ได้ อัลกอริทึมการ resolve และเมทริกซ์ gate ทั้ง SPA อยู่ใน [rbac permissions](/th/platform/rbac/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [business-units](/th/platform/business-units) — cluster เป็นเจ้าของ BU แบบ 1:N แท็บ Business Units คือจุดมาตรฐานในการสร้าง BU ที่ผูกกับ cluster ตั้งแต่ต้น **Gotcha:** route `/business-units*` ใช้ key `cluster.read`/`cluster.create`/`cluster.update` ซ้ำ — ไม่มี key `business_unit.*`
- [users](/th/platform/users) — cluster เพิ่ม user ผ่าน global user list ส่วนหน้า edit user คืออีกฝั่งของ join `tb_cluster_user`
- [rbac](/th/platform/rbac) — กำหนด catalog ของ permission, role และ scoped assignment ที่อยู่เบื้องหลังทุก gate `cluster.*` ใน §4
- [licenses](/th/platform/licenses) — licence ledger เต็มรูปแบบของโควตา BU/ที่นั่งและ UI ซื้อ/ยกเลิก (License Center) ที่ทุกหน้าจอ cluster ลิงก์ไปหาแล้วตอนนี้
- [report-templates](/th/platform/report-templates) — ใช้ pattern route-guard เดียวกันแต่มี key `report_template.*` ของตัวเอง

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-backstage/src/App.tsx` — การต่อสาย `PrivateRoute` พร้อม key `requiredPermission` + `feature` ของทั้งสาม route ของ cluster
- `../carmen-backstage/src/components/PrivateRoute.tsx` — guard แบบเป็นชั้น: auth → resolve platform-authority/cluster-admin → permission → super-admin → feature flag
- `../carmen-backstage/src/components/nav/backstageNav.ts` — รายการ nav ของ Clusters (บรรทัด 14) และ Business Units (บรรทัด 15) บวกรายการลูก Tenant Migrations/Seeds/Data Import (permission, feature, group)
- `../carmen-backstage/src/pages/ClusterManagement.tsx` — หน้า list, แถบ Fleet Capacity (อ่านจาก `GET /clusters/summary` แล้ว), filter รวม Quota-expiring, ส่งออก CSV, การจัดการ soft-delete, row action ที่ gate ด้วย `<Can>` รวม View History
- `../carmen-backstage/src/pages/ClusterEdit.tsx` — หน้า orchestrator แบบ create/view/edit: `ClusterPlate`/`ClusterDraftPlate`, เนื้อหาแบบหลายแท็บ, optimistic locking ด้วย `doc_version`, dialog เพิ่ม user, action View History ที่หัวหน้า
- `../carmen-backstage/src/pages/clusterEdit/{ClusterPlate,ClusterDraftPlate,PlateField,clusterTabs}.ts(x)` และ `sections/{BusinessUnitsSection,UsersSection,SubscriptionCard}.tsx` — แผ่นป้าย, นิยามแท็บ และเนื้อหาแต่ละแท็บปัจจุบัน; `src/components/clusterSeat/*` และ `src/components/notes/*` — การจัดการที่นั่งและแท็บ Notes
- `../carmen-backstage/src/pages/clusterManagement/{FleetCapacity,CapacityGauge,CapacityMeter,ClusterCreateForm,ClusterIdentityFields}.tsx` และ `../carmen-backstage/src/utils/capacity.ts` — สูตรคำนวณ capacity และฟอร์ม create แบบสองการ์ด
- `../carmen-backstage/src/utils/businessUnitRank.ts` — การจัดอันดับ "Over limit" ที่ใช้ร่วมกับหน้า BU list ของฝั่ง cluster-admin
- `../carmen-backstage/src/services/clusterService.ts` — REST client (`/api-system/clusters`, `/api-system/clusters/summary`, endpoint อัปโหลด `/logo` และ `/avatar`)
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — model `tb_cluster`, `tb_cluster_user`, `tb_cluster_note`, `tb_cluster_license`, `tb_business_unit_license` (ดูเลขบรรทัดที่แน่นอนใน [Data Model](/th/platform/clusters/data-model) §6)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/clusters/data-model) — field ของ entity cluster, ความสัมพันธ์ 1:N กับ BU, การ join ผ่าน `tb_cluster_user` ตาราง licence ledger ที่มาแทน cap แบบ static เดิม และ `tb_cluster_note` ใหม่
- [Permissions](/th/platform/clusters/permissions) — gate `requiredPermission`/`feature` ของแต่ละ route, gate `<Can>` ภายในหน้า (รวม variant แบบ cluster-scoped และ gate `activity_log.read`), layer การ resolve platform-authority และ permission ใหม่ของ Notes / action ที่นั่ง (§9)
- [UI Screens](/th/platform/clusters/ui-screens) — หน้า list `ClusterManagement` (แถบ Fleet Capacity) และเลย์เอาต์ `ClusterPlate` + หลายแท็บของ `ClusterEdit` รวมถึงพรีวิวโหมด create, dialog เพิ่ม user, flow ของ bulk action, release/restore ที่นั่ง และแท็บ Notes
