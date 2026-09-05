---
title: ผู้ดูแลคลัสเตอร์ — หน้าจอ UI (UI Screens)
description: ClusterAdminEntry, ClusterProfile, BusinessUnitList/BusinessUnitForm, ClusterUsers และ ClusterAdminLicenses ที่อ่านอย่างเดียว บวกหน้าจอ Profile ที่ใช้ร่วมกัน — ทุกหน้าจำกัดขอบเขตอยู่ที่ :clusterId เดียว และเทียบกับคู่ของมันฝั่ง platform
published: true
date: '2026-09-06T11:00:00.000Z'
tags: book/platform, cluster-admin, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ผู้ดูแลคลัสเตอร์ — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `ClusterAdminEntry` (`/cluster-admin`) &nbsp;·&nbsp; `ClusterProfile` (`/cluster-admin/:clusterId/cluster`) &nbsp;·&nbsp; `BusinessUnitList`/`BusinessUnitForm` (`/cluster-admin/:clusterId/business-units[/:buId/edit]`) &nbsp;·&nbsp; `ClusterUsers` (`/cluster-admin/:clusterId/users`) &nbsp;·&nbsp; `ClusterAdminLicenses` (`/cluster-admin/:clusterId/licenses` อ่านอย่างเดียวทั้งหมด) &nbsp;·&nbsp; `Profile` ที่ใช้ร่วมกัน (`/cluster-admin/:clusterId/profile`) &nbsp;·&nbsp; **Gate บนทุกหน้าจอต่อคลัสเตอร์:** ไม่มี RBAC permission key — กั้นด้วยสมาชิกภาพของคลัสเตอร์ผ่าน `isClusterAdminOf` แทน ตรวจก่อน feature flag เสมอ (ดู [Permissions](/th/platform/cluster-admin/permissions)) &nbsp;·&nbsp; **การเขียนในหน้าจอกั้นด้วยการเข้าถึง route ได้เท่านั้น** — `canEdit` ของ `ClusterProfile` และ `BusinessUnitForm` คำนวณจากการเข้าถึงได้ล้วน ๆ ไม่มีการตรวจ permission หรือ role ใด ๆ ใน component เลย &nbsp;·&nbsp; **ไม่มี e2e suite** — ทุกคำกล่าวอ้างด้านล่างมาจากการอ่าน `../carmen-platform` โดยตรง

## 1. ภาพรวม

ทุกหน้าจอในโมดูลนี้ใช้ shell เดียวกัน คือ `ClusterAdminLayout` และหลายหน้าใช้ธรรมเนียมเดียวกันที่ควรพูดครั้งเดียวแทนที่จะพูดซ้ำต่อหน้า: `PageHeader`, skeleton placeholder ตอนโหลดครั้งแรก (ไม่ใช่ spinner), `DevDebugSheet` สำหรับ dev เท่านั้นที่โชว์ raw API response แยกตามแท็บ และ — บน `ClusterProfile`/`BusinessUnitForm` — การบันทึกแบบ optimistic-lock ด้วย `doc_version`, guard `useUnsavedChanges` ตอนนำทางออก, และ `Ctrl/⌘+S`/`Escape` ผ่าน hook `useGlobalShortcuts` ที่ใช้ร่วมกัน สี่ในหกหน้าจอ (`ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, `ClusterUsers`) ดัก 403 กลางเซสชันเอง (สมาชิกภาพถูกถอนขณะหน้าเปิดอยู่) แล้ว render `ClusterAccessLost` แทน body — ดู [Landing](/th/platform/cluster-admin) §3.6 `ClusterAdminLicenses` ไม่ทำแบบนี้ (§7)

โมดูลนี้ **ไม่มี View History / Activity Trail แบบ cross-cutting เลย** — grep `src/pages/clusterAdmin/` หา `activity_log.read`/`ActivityTrailSheet`/`PLATFORM_SCOPED_RECORD` ไม่เจอเลยสักที่ ผลลบแบบเดียวกับที่ [Licenses — UI Screens](/th/platform/licenses/ui-screens) บันทึกไว้สำหรับโมดูลของมันเอง

## 2. `ClusterAdminEntry` — หน้าจอลงจอด (`/cluster-admin`)

กั้นด้วย `AuthedRoute` เท่านั้น (แค่ล็อกอิน ยังไม่มีการตรวจสมาชิกภาพ — ดู [Landing](/th/platform/cluster-admin) §1) พฤติกรรมแยกตาม `adminScope` ที่เพิ่งโหลดมา:

- **`adminScope === null`** — ยังตัดสินไม่ได้ แสดงสถานะกำลังโหลด
- **ดูแลอยู่พอดีหนึ่งคลัสเตอร์ และไม่ใช่ super admin** (`!adminScope.all && adminScope.clusters.length === 1`) — `<Navigate replace>` เข้า `/cluster-admin/:id/cluster` ตรง ๆ super admin เห็น picker แม้หน้าของตัวเองมีแค่หนึ่งแถวพอดี เพราะ `adminScope.all` short-circuit สาขานี้ไปเลย — `adminScope.clusters` เป็นแค่หน้าที่ค้นหาได้สำหรับ super admin ไม่ใช่ชุดสมบูรณ์
- **ไม่มีคลัสเตอร์เลย** — `EmptyState` ("ไม่มีคลัสเตอร์ให้ดูแล") ที่คอมเมนต์ของ component เองบรรยายไว้โดยตั้งใจว่าไม่ใช่ 403 โดยเนื้อแท้: ผู้เรียกล็อกอินอยู่ แค่ไม่ได้ดูแลอะไรเลย
- **นอกนั้น (มีหลายคลัสเตอร์ หรือเป็น super admin)** — grid การ์ดแบบ responsive หนึ่งการ์ดต่อหนึ่งคลัสเตอร์ที่ดูแลอยู่ แต่ละการ์ด navigate ไปที่ route `/cluster` ของคลัสเตอร์นั้นเมื่อคลิกหรือกด Enter/Space

`ClusterAdminEntry.tsx` render อยู่ใน `Layout` เปล่า ๆ ที่ `navItems` เป็น array ว่าง — ไม่มี sidebar เลยบนหน้าจอนี้ เพราะยังไม่มีคลัสเตอร์ถูกเลือกให้ `buildClusterAdminNav` เอาไปใช้จำกัดขอบเขต

## 3. `ClusterProfile` — หน้าแรกของคลัสเตอร์ (`/cluster-admin/:clusterId/cluster`)

เป้าหมายลงจอดเมื่อเข้ามาในคลัสเตอร์แล้ว: สำหรับการ redirect ของ `/cluster-admin` ตอนมีคลัสเตอร์เดียว, สำหรับลิงก์แบรนด์, และสำหรับทุกการเลือกจาก `ClusterSwitcher` อ่านเหมือนสถานะใบอนุญาตก่อน แล้วจึงเป็นฟอร์มตัวตน:

1. **`CapacityStrip`** — สองสระว่ายน้ำที่มีจำกัด (โควตา BU, ที่นั่ง) ที่คลัสเตอร์ดึงใช้ วางเคียงกัน แต่ละสระลิงก์ไปที่ `/licenses` (ของโมดูลนี้เอง ที่ `licensesTo`) เมื่อเข้าเขต warn/over หรือไม่มีเงื่อนไขเลยเมื่อโควตา BU เป็น `0` (ยังไม่ได้ซื้ออะไรเลย) ใช้ร่วมกับ `ClusterAdminLicenses` (§7) และแผ่นป้าย `BuPropertyPlate` บน `BusinessUnitForm` (§5)
2. **`ClusterBusinessUnitsCard`** และ **`ClusterPeopleCard`** — สรุปแบบอ่านอย่างเดียว (สูงสุด 8 business unit, สูงสุด 5 ผู้ดูแลก่อนขึ้นบรรทัด "+N เพิ่มเติม") แต่ละการ์ดลิงก์ไปหน้าจอ Business Units หรือ Users เต็ม ทั้งสองการ์ดดึงข้อมูลจากคำเรียก `GET /clusters/:id` เดียวที่หน้านี้เรียกอยู่แล้ว — ไม่มีคำขอที่สอง คอมเมนต์ของ component เองระบุเหตุผลของการออกแบบตรง ๆ ว่า: "สิบเอ็ดชื่อบนหน้า landing คือตารางที่ไม่มีใครขอ — หน้า Users มีให้อยู่แล้ว"
3. **การ์ดตัวตน** (`DetailsSection` ใช้ซ้ำเป๊ะจาก `ClusterEdit.tsx` ฝั่ง platform) — สวิตช์แก้ไข **ดินสอ → Save/Cancel** แก้ได้แค่ `name` กับ `alias_name` `code` ไม่ถูกแสดง (`showCode={false}`) และ `is_active` render เป็น **อ่านอย่างเดียวแม้ตอนแก้ไข** (`canEditPlatformFields={false}`) — คอมเมนต์ของ component เองอธิบายว่าทำไม: backend ตัด `max_license_users`, `is_active`, และ `info` ออกจากการอัปเดตคลัสเตอร์ของผู้ดูแลแบบสมาชิกอย่างเงียบ ๆ เป็นการเขียนที่หายไปโดยไม่มี error ให้เห็น หน้านี้จึงไม่เสนอตัวควบคุมสำหรับฟิลด์ที่ backend จะไม่เปลี่ยนจริง ๆ
4. **การ์ดแบรนด์** — อัปโหลดโลโก้/avatar แก้ไขได้เสมอโดย cluster admin (การอัปโหลดใช้ endpoint แบบ presigned-URL เฉพาะ ไม่ใช่เส้นทางเขียนเดียวกับที่ backend ตัดทิ้งอย่างเงียบ ๆ)

**เทียบกับคู่ฝั่ง platform:** [Clusters — UI Screens](/th/platform/clusters/ui-screens) บันทึก `ClusterEdit` ไว้เป็นแผ่นป้าย `ClusterPlate` บวก body แบบ 3 แท็บ (Licensing/Business Units/Users) `ClusterProfile` ไม่มีโครงแบบนั้นเลย — ไม่มีแท็บ ไม่มี Licensing tab (licensing ที่นี่คือ route `/licenses` แยกออกไปที่อ่านอย่างเดียวทั้งหมด, §7) ไม่มีแท็บแก้ไข Business Units/Users (สองอย่างนั้นคือ route แยก `BusinessUnitList`/`ClusterUsers`, §4/§6) สิ่งที่เหลือรอดมาจากฟอร์มฝั่ง platform มีแค่พื้นผิวแก้ไขตัวตน/แบรนด์ ที่ถูกจำกัดให้เหลือแค่สองฟิลด์ที่ผู้ดูแลแบบสมาชิกเปลี่ยนได้จริง ๆ

403 กลางเซสชัน render `ClusterAccessLost` แทนที่ทุกอย่างใต้หัวเพจ

## 4. `BusinessUnitList` — BU ของคลัสเตอร์ (`/cluster-admin/:clusterId/business-units`)

รายการแบบ `DataTable` ในรูปแบบ Management-page ที่ใช้ร่วมกันเหมือนกับ `BusinessUnitManagement` แต่จำกัดไว้ที่หนึ่งคลัสเตอร์ — พร้อมความต่างสามอย่างจากคู่ฝั่ง platform:

1. **ไม่มีปุ่มสร้างเลยที่ไหนทั้งสิ้น** — ไม่มีปุ่มที่หัวเพจ ไม่มี CTA ที่ empty state คอมเมนต์ของ `BusinessUnitForm.tsx` เองระบุเหตุผล: "การสร้าง BU กิน `max_license_bu` (โควตา BU) ซึ่งเป็นการตัดสินใจระดับแพลตฟอร์ม" — route `/cluster-admin/:clusterId/business-units/new` ไม่มีอยู่เลย route แก้ไขที่อยู่ข้าง ๆ กันต้องมี `:buId` เดิมอยู่แล้วเสมอ
2. **ป้าย "Over limit" ranking** บนคอลัมน์ Name ใช้สูตรเดียวกันเป๊ะกับที่ [Business Units](/th/platform/business-units) บันทึกไว้สำหรับโมดูลของตัวเอง (`rankBusinessUnits()`/`countOverLimit()` ตรงกับ DB view `v_cluster_bu_quota` เป๊ะ) แต่ copy ซ้ำมาไว้ใน i18n namespace ของหน้านี้เอง แทนที่จะ import ข้ามโมดูล ตามธรรมเนียมที่คอมเมนต์ในซอร์สระบุว่า namespace ของแต่ละหน้าเป็นของ slice ตัวเอง
3. **Action ที่หัวเพจมีแค่ Export** ส่วนที่เหลือเป็นรูปแบบเดียวกัน: ช่องค้นหาแบบ debounce, Filters sheet ตามสถานะ, state ที่แคชใน `localStorage` (คีย์ลงท้ายด้วย `_ca_business_units` ของหน้านี้เอง คนละชุดกับรายการฝั่ง platform) และคอลัมน์ audit Created/Updated ผ่าน `auditColumns()` ที่ใช้ร่วมกัน

อันดับ/จำนวน Over-limit มาจากการดึงข้อมูลครั้งที่สองที่ไม่แบ่งหน้า ดึงทุก BU ในคลัสเตอร์ (จำเป็นเพราะการจัดอันดับต้องเห็นทุกแถว ไม่ใช่แค่หน้าปัจจุบัน) และ fail open — ถ้าดึงไม่สำเร็จ cap จะไม่รู้ค่าและป้ายจะไม่ render แทนที่จะโชว์ตัวเลขผิด

403 กลางเซสชัน render `ClusterAccessLost` แทนที่ตาราง

## 5. `BusinessUnitForm` — ตัวแก้ BU ของคลัสเตอร์ (`/cluster-admin/:clusterId/business-units/:buId/edit`)

แก้ไขได้อย่างเดียว — ไม่มี route สร้าง (§4) `canEdit` คำนวณเป็น `!accessLost`: คอมเมนต์ของ component เองระบุตรง ๆ ว่า "สิทธิ์เท่าเดิมเป๊ะ: ใครเข้า route ได้ก็แก้ได้" — การเปลี่ยนขอบเขตสิทธิ์เป็นงานคนละชิ้นที่ถูกเลื่อนออกไปให้ต้องมีสเปกของตัวเองอย่างชัดเจน ไม่ใช่สิ่งที่ทำที่นี่

**โครงหน้า:** แผ่นป้าย `BuPropertyPlate` (โลโก้/avatar, ชื่อที่แก้แบบ inline, สวิตช์ `is_active`/`is_hq`, `code` แบบอ่านอย่างเดียว, และ `SeatMeter` สำหรับสระที่นั่งระดับคลัสเตอร์) อยู่เหนือ **เอกสาร 5 แท็บ** — Overview, People, Hotel, Company, Configuration — แทนที่ฟอร์มต่อเนื่องหน้าเดียวของหน้าแก้ไขฝั่ง platform สำหรับขอบเขตที่แคบกว่านี้

**เทียบกับคู่ฝั่ง platform:** [Business Units — UI Screens](/th/platform/business-units/ui-screens) บันทึกฟอร์มฝั่ง platform ไว้เป็น **6 แท็บ** (General, Location, Formats, Technical, Users, Licenses) การแบ่งแท็บของโมดูลนี้ต่างออกไปโดยตั้งใจ ไม่ใช่แค่จำนวนที่ต่าง:

| แท็บฝั่ง cluster-admin | ส่วนที่เทียบเท่าฝั่ง platform | ต่างกันตรงไหน |
|---|---|---|
| Overview | (ไม่มีส่วนเทียบเท่า) | `TabJumpList` สรุปเนื้อหาของอีกสี่แท็บ — เพิ่มมาเพราะป้ายแท็บเปล่า ๆ บังคับให้คลิกทีละแท็บถึงจะรู้ว่าตั้งค่าอะไรไว้บ้าง |
| People | แท็บ Users (Licenses แยกออกมาจาก General ฝั่ง platform) | รวมแท็บ Users และ Licenses ที่แยกกันของฝั่ง platform เข้าเป็นแท็บเดียว: `BusinessUnitUsersCard` ที่แก้ได้เต็มที่ (เพิ่ม/แก้/ลบสมาชิกภาพ BU) บวก `BusinessUnitLicensesCard` แบบสรุป **อ่านอย่างเดียว** |
| Hotel | Location (รวมกับ Company) | แยกจาก Company โดยตั้งใจ — คอมเมนต์ในซอร์สระบุว่า cluster admin อ่านว่า "โรงแรมคือทรัพย์สินที่ตัวเองบริหาร บริษัทคือผู้ออกใบแจ้งหนี้ให้" เป็นงานคนละงานกันสองวัน ต่างจาก platform admin ที่อ่านทั้งสองอย่างเป็น "ภูมิศาสตร์" เดียวกัน |
| Company | Location (รวมกับ Hotel) | ดูด้านบน คงปุ่ม "คัดลอกจากที่อยู่โรงแรม" แบบทางเดียวไว้ |
| Configuration | Formats + บางส่วนของ Technical | **อ่านอย่างเดียวทั้งหมด** — ไม่มีสาขา `canEdit` เลย timezone, รูปแบบวันที่/เวลา/ตัวเลข, และวิธีคิดต้นทุน แสดงเป็นข้อความล้วน ค่าเหล่านี้ round-trip กลับไปใน save payload โดยไม่เปลี่ยน ดังนั้นการบันทึกจากหน้านี้จึงล้างค่าเหล่านี้ไม่ได้เลยแม้โดยไม่ตั้งใจ |

สองสิ่งที่ฟอร์มฝั่ง platform มีแต่หน้านี้ตัดออกไปเลยทั้งคู่ ตามการออกแบบตามคอมเมนต์ของ component เอง: ตาราง key-value `config[]` (ตั้งค่าไว้ครั้งเดียวตอน provision BU ไม่ใช่งานของ cluster admin — ยังโหลดและ round-trip กลับไปใน save payload อยู่ ดังนั้นรอดจากการบันทึกจากหน้านี้โดยไม่ถูกแตะ) และส่วน database-pool (`database_pool_id`/`db_schema` เป็นฟิลด์ระดับ platform เท่านั้น กั้นด้วย platform role ที่ backend และหน้านี้ไม่อ่านหรือเขียนทั้งคู่)

**ความไม่สมมาตรของการเขียนที่ควรบอกผู้ทดสอบไว้:** แท็บ People ใช้ component ตัวเดียวกันเป๊ะ (`BusinessUnitUsersCard`) กับที่หน้า `BusinessUnitEdit` ฝั่ง platform render แต่สองหน้าคำนวณ `canEdit` ต่างกันเลย — หน้าฝั่ง platform ผูกไว้กับ `cluster.update` ซึ่งเป็น RBAC permission; หน้านี้ผูกไว้กับ `!accessLost` คือแค่การผ่าน `ClusterAdminRoute` มาได้ cluster admin จึงเพิ่ม แก้ และลบผู้ใช้ของ BU ได้โดย **ไม่มี permission key ใด ๆ เข้ามาเกี่ยวข้องเลย** เป็นรูปแบบเดียวกับ "route guard คือด่านทั้งหมด" ของทั้งโมดูลนี้ `BusinessUnitLicensesCard` ที่อยู่ข้าง ๆ กันบนหน้านี้ไม่ได้รับ `createHref` เลย (จึงไม่มีปุ่ม "New subscription" ปรากฏขึ้นเลย) เพราะ cluster admin ไม่มี `subscription.manage` และจะผ่าน `PrivateRoute` ของ `/licenses/subscriptions/new` ไม่ได้ถ้าปุ่มนั้นมีอยู่จริง `manageHref` ของมันชี้ไปที่ route `/licenses` ของโมดูลนี้เอง ไม่ใช่ของ platform เพราะ cluster admin เข้า `/licenses/*` ไม่ได้เช่นกันถ้าไม่มี `subscription.read`

ฟิลด์ที่อยู่ยุบเป็นข้อความล้วนพร้อมปุ่มกางออก (`AddressBlock`) แทนที่จะโชว์ช่องกรอก 10 ช่องต่อที่อยู่ตลอดเวลา — เป็นการลดความซับซ้อนของ UI ไม่มีนัยเรื่องสิทธิ์แต่อย่างใด

403 กลางเซสชัน render `ClusterAccessLost` แทนที่เอกสารทั้งหน้า; BU ที่ `cluster_id` ไม่ตรงกับ `:clusterId` ของ URL อีกต่อไป (บุ๊กมาร์กเก่า หรือ URL ที่ถูกแก้ด้วยมือ) จะได้ URL แก้ไขให้ตรงในที่ผ่าน `navigate(..., { replace: true })` แทนที่จะ render BU นั้นใต้ chrome ของคลัสเตอร์ผิด

## 6. `ClusterUsers` — สมาชิกภาพและคำเชิญของคลัสเตอร์ (`/cluster-admin/:clusterId/users`)

Shell แบบแท็บ (Members / Invitations) ไม่ใช่รายการแบบ Management-page — ชุดข้อมูลคือรายชื่อของหนึ่งคลัสเตอร์ ไม่ใช่แคตตาล็อกที่แบ่งหน้า นี่คือ **data model คนละชุดกันเลย** กับโมดูล [Users](/th/platform/users) ฝั่ง platform: หน้าจอนี้จัดการแถวสมาชิกภาพ `tb_cluster_user` และคำเชิญของคลัสเตอร์ ไม่เคยแตะเรคคอร์ดบัญชี platform `tb_user` ที่แท้จริงเลย ไม่มีทางสร้าง แก้ไขฟิลด์ตัวตน หรือลบ `tb_user` จากหน้านี้ได้เลย — มีแค่การให้ เปลี่ยน หรือถอนสถานะของผู้ใช้นั้นภายในคลัสเตอร์เดียวนี้

- **แท็บ Members** (`MembersTable`) — รายการสมาชิกที่ active ของคลัสเตอร์ ค้นหาได้ action menu ของแต่ละแถวมี **Make Admin**/**Make User** (`clusterService.updateClusterUser`) และ **Remove** (`clusterService.deleteClusterUser`) ทั้งคู่เป็นการเขียนล้วน ๆ ไม่มี permission string ใด ๆ — สมาชิกภาพอย่างเดียว ผ่าน route guard คือด่านทั้งหมด **ไม่มีคอลัมน์ Status และไม่มีปุ่ม Activate/Deactivate โดยตั้งใจ**: endpoint ของ backend ที่ตารางนี้อ่าน (`GET /api-system/user/clusters/:clusterId`) กรองด้วย `is_active: true` แบบ hard-coded และไม่เลือกคอลัมน์นี้เลยด้วยซ้ำ ทุกแถวจึงมี `is_active` เป็น `undefined` เสมอ — คอลัมน์ Status ที่นี่จะโชว์ค่าเดียวได้ตลอด และปุ่ม Deactivate จะเอาแถวออกจากรายการที่ไม่มีทางโชว์กลับมาได้อีกเลย
- **แท็บ Invitations** (`InvitationsTable` + `InviteUserDialog`) — คำเชิญที่ pending/terminal บวก dialog สำหรับสร้างคำเชิญใหม่ (อีเมล, cluster role, และตัวเลือก role/default รายหน่วยธุรกิจที่จำกัดเฉพาะ BU ของคลัสเตอร์นั้น) **Resend**/**Revoke** กั้นด้วยสถานะ *terminal* ของคำเชิญ (`accepted`/`declined`/`revoked`) ไม่ใช่ `status === 'pending'` — `status` ที่แสดงในรายการมีค่าคำนวณ `expired` สำหรับแถว database ที่ยังเป็น `pending` แต่หมดอายุแล้ว และการส่งคำเชิญที่หมดอายุซ้ำก็คือเหตุผลหลักที่ผู้ดูแลเปิดแท็บนี้ ดังนั้นการกั้นด้วยสถานะ working แทนที่จะเป็น terminal จะบล็อกสิ่งที่ต้องทำพอดี `409` ตอนสร้างจะถูกส่งไปยังแท็บที่ตอบคำถามนั้นจริง ๆ — "เป็นสมาชิกอยู่แล้ว" สลับไป Members พร้อม pre-fill อีเมลใน search; "รอดำเนินการอยู่แล้ว" สลับไป Invitations แทนที่จะโชว์ error เปล่า ๆ

การเขียนทั้งสองแบบที่นี่กั้นด้วย route เพียงอย่างเดียว ไม่มี RBAC permission key เข้ามาเกี่ยวข้องเลยที่หน้าจอนี้

## 7. `ClusterAdminLicenses` — มุมมองความจุแบบอ่านอย่างเดียว (`/cluster-admin/:clusterId/licenses`)

หน้าจอเดียวในโมดูลนี้ที่ยืนยันแล้วว่า **ไม่มีทางเขียนเลยที่ไหนทั้งสิ้น** grep หน้าและ component ลูกทั้งสี่ตัว (`CapacityStrip`, `SeatsByBuTable`, `QuotaLedgerCard`, `BuRankingCard`) หา `onClick|<Link to=|<Button|navigate(|Service\.(create|update|delete|cancel)|<form|onSubmit` เจอแค่ปุ่ม "Retry" สองปุ่มตอนดึงข้อมูลไม่สำเร็จ (`QuotaLedgerCard.tsx:75`, `SeatsByBuTable.tsx:58`) — ไม่มีปุ่มสร้าง แก้ ลบ หรือ navigate-ไป-เขียนแบบไหนเลย คอมเมนต์ของหน้าเองอธิบายว่าทำไมนี่ไม่ใช่การตัดสินใจซ่อนปุ่ม แต่เป็นเรื่องเชิงโครงสร้าง: cluster admin ไม่มี RBAC permission ใด ๆ ใน session เลย (สมาชิกภาพมาจาก `tb_cluster_user` ไม่ใช่ `tb_user_tb_platform_role`) endpoint การเขียนใบอนุญาตทุกตัวต้องการ `subscription.manage` ที่ backend และหน้านี้จึงไม่เคยเรียก `GET /platform/subscriptions` เลยด้วยซ้ำ — ไม่มีอะไรให้ทำกับข้อมูล subscription ที่ทำอะไรกับมันไม่ได้อยู่ดี

โครงหน้า:

1. **`CapacityStrip`** — component เดียวกันและสองสระเดียวกันกับ `ClusterProfile` §3 อ่านค่า `bu_used`/`bu_cap`/`users_count`/`total_max_license_users` ของคลัสเตอร์เองตรง ๆ (ไม่ใช่ผลรวมฝั่ง client จากแถวที่โหลดด้านล่าง) แถบนี้กับของ `ClusterProfile` จึงไม่มีทางขัดแย้งกันเลย
2. **`SeatsByBuTable`** — หนึ่งแถวต่อหนึ่ง business unit ในคลัสเตอร์ แต่ละแถวโชว์จำนวนที่นั่ง active รวมของตัวเองและวันหมดอายุที่ใกล้ที่สุด ดึงแบบขนานทีละ BU (`useClusterSeatLicenses`, `Promise.allSettled` เพราะไม่มี endpoint ระดับคลัสเตอร์) และแยกแยะแถวที่โหลดไม่สำเร็จอย่างชัดเจน: จะโชว์ข้อความ "โหลดไม่สำเร็จ" ไม่ใช่ `0` เงียบ ๆ เพราะในระบบนี้ที่นั่งศูนย์แปลว่าเชิญผู้ใช้ใหม่ไม่ได้จริง
3. **`QuotaLedgerCard`** (ยุบไว้เป็นค่าเริ่มต้น) — ทุกแถวการซื้อโควตา BU ของคลัสเตอร์ พร้อมป้าย "In force" บนใบที่ชนะอยู่ในปัจจุบัน (`activeLicense`, `start_date` ใหม่สุดชนะ) — ตอกย้ำกติกานับแบบชนะ-กินรวบที่ [Licenses — Data Model](/th/platform/licenses/data-model) §3 บันทึกไว้ ไม่ใช่การรวมยอด
4. **`BuRankingCard`** (ยุบไว้เป็นค่าเริ่มต้น) — ทุกหน่วยธุรกิจจัดอันดับด้วยสูตร `rankBusinessUnits()` เดียวกับป้าย Over-limit ของ `BusinessUnitList` (§4) ตอบคำถาม "ถ้าคลัสเตอร์เกินโควตา BU ไหนโดนตัดก่อน" — คำถามที่คุ้มค่าให้เห็นก็ต่อเมื่อแถบด้านบนขึ้นสีเตือนไปแล้วเท่านั้น

**นี่คือหน้าจอเดียวที่ไม่ได้ทำแพทเทิร์น `ClusterAccessLost` สำหรับ 403 กลางเซสชัน** ที่อีกสี่หน้าจอของโมดูลใช้ร่วมกัน (§1) — grep `ClusterAdminLicenses.tsx` เจอแค่สาขา `isNotFoundError` สำหรับคลัสเตอร์ที่ถูกลบ/หายไป ไม่มีการดัก 403 เฉพาะเลย ดู [Permissions](/th/platform/cluster-admin/permissions) §4 กรณีพิเศษที่ 9

[Licenses](/th/platform/licenses) §4/§5 บันทึกหน้าจอนี้ไว้จากฝั่งโมดูลของมันเองแล้ว โดยใช้คำอธิบาย gate เดียวกันเป๊ะ

## 8. `Profile` ที่ใช้ร่วมกัน (`/cluster-admin/:clusterId/profile`)

Component `Profile` ตัวเดียวกับที่ platform mount ที่ `/profile` [Profile](/th/platform/profile) §1.1 บันทึกทั้งสอง mounting ไว้เคียงกันเต็มแล้ว (guard, nav, ตัวตนแบรนด์, ปลายทาง brand-mark, ส่วนเพิ่มที่หัวเพจ) หน้านี้เห็นตรงกับเรื่องนั้นแทนที่จะเล่าใหม่ให้ต่างออกไป สิ่งที่ควรพูดซ้ำที่นี่คือ: นี่คือ route ต่อคลัสเตอร์เพียงตัวเดียวที่ `App.tsx` ส่งให้ `ClusterAdminRoute` **โดยไม่มี prop `feature` เลย** (`App.tsx:603-604`) จึงต่างจากอีกห้า route ตรงที่ไม่มี feature-flag gate ใด ๆ ทั้งสิ้น — สมาชิกภาพคือด่านทั้งหมด ไม่มีอะไรตรวจต่อจากนั้นอีกเลย

## 9. Component แสดงผลที่ใช้ร่วมกัน

- **`CapacityStrip`**/**`AllocationTicks`** — ภาพของสระใบอนุญาตที่ `ClusterProfile` และ `ClusterAdminLicenses` ใช้ร่วมกัน `AllocationTicks` วาดหนึ่งขีดต่อหนึ่งใบอนุญาต สูงสุด 40 ขีด เกินจากนั้นจะตกกลับไปเป็น bar เปอร์เซ็นต์ธรรมดา เพราะแต่ละขีดจะเริ่มอ่านไม่ออกเมื่อเกินจำนวนนั้น
- **`SeatMeter`** — มิเตอร์ที่นั่งระดับคลัสเตอร์แบบกะทัดรัดที่แสดงบนแผ่นป้ายของ `BusinessUnitForm` จงใจไม่เคยโชว์ที่นั่งของ BU นั้นเอง (ตัวเลขนั้นอยู่ที่ `BusinessUnitLicensesCard`, §5) เพื่อไม่ให้คำว่า "licensed" มีสองความหมายในบล็อกภาพเดียวกัน
- **`ClusterAccessLost`** — empty state สำหรับ 403 กลางเซสชันที่ใช้ร่วมกัน (§1, §7)
- **`CollapsibleGroupCard`** — แพทเทิร์นการ์ดที่ยุบไว้เป็นค่าเริ่มต้นซึ่ง `QuotaLedgerCard`/`BuRankingCard` ใช้ ต่างจาก `CollapsibleSection` ของฝั่ง platform (ที่ใช้ `CardTitle`/`CardDescription`) เพื่อไม่ให้สองแบบนี้อ่านเหมือนคนละ design system บนหน้าจอเดียวกัน

## 10. แหล่งข้อมูลอ้างอิง

path ทั้งหมดคือ `../carmen-platform` (HEAD `157a65e`)

- `src/pages/clusterAdmin/ClusterAdminEntry.tsx` (§2)
- `src/pages/clusterAdmin/ClusterProfile.tsx`, `src/pages/clusterAdmin/{CapacityStrip,ClusterBusinessUnitsCard,ClusterPeopleCard,SummaryCardHeader}.tsx` (§3)
- `src/pages/clusterAdmin/BusinessUnitList.tsx`, `src/utils/businessUnitRank.ts` (§4)
- `src/pages/clusterAdmin/BusinessUnitForm.tsx`, `src/pages/clusterAdmin/businessUnitForm/{BuPropertyPlate,ClusterBuDocument,ClusterBuTabs,SeatMeter,AddressBlock}.tsx`, `src/pages/businessUnitEdit/{BusinessUnitUsersCard,BusinessUnitLicensesCard,useBusinessUnitUsers}.tsx` (§5)
- `src/pages/clusterAdmin/{ClusterUsers,MembersTable,InvitationsTable,InviteUserDialog}.tsx`, `src/services/clusterAdminService.ts` (§6)
- `src/pages/clusterAdmin/ClusterAdminLicenses.tsx`, `src/pages/clusterAdmin/licenses/{BuRankingCard,CollapsibleGroupCard,QuotaLedgerCard,SeatsByBuTable}.tsx`, `src/pages/licenses/{useLicenseLedger,useClusterSeatLicenses}.ts` (§7)
- `src/pages/Profile.tsx` (§8)
- `src/pages/clusterAdmin/ClusterAccessLost.tsx`, `src/pages/clusterAdmin/AllocationTicks.tsx` (§9)

**ลิงก์ที่เกี่ยวข้อง:** [หน้าหลัก Cluster Admin](/th/platform/cluster-admin) &nbsp;·&nbsp; [Permissions](/th/platform/cluster-admin/permissions) &nbsp;·&nbsp; [Clusters — UI Screens](/th/platform/clusters/ui-screens) &nbsp;·&nbsp; [Business Units — UI Screens](/th/platform/business-units/ui-screens) &nbsp;·&nbsp; [Users — UI Screens](/th/platform/users/ui-screens) &nbsp;·&nbsp; [Licenses](/th/platform/licenses) &nbsp;·&nbsp; [Profile](/th/platform/profile)
