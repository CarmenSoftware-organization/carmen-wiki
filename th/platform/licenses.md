---
title: ไลเซนส์ (Licenses)
description: License centre — บัญชีโควตา BU ต่อ cluster, บัญชีที่นั่งต่อ BU, และสัญญา subscription ที่พก feature-group entitlement พร้อมเกณฑ์ใกล้หมดอายุและ redirect เก่าจาก /subscriptions
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ไลเซนส์ (Licenses)

โมดูล **Licenses** คือบัญชีเชิงพาณิชย์ของแพลตฟอร์มที่บอกว่า cluster และ business unit ของมันซื้ออะไรไว้จริง ๆ: cluster หนึ่งมีสิทธิ์สร้าง **business unit** ได้กี่หน่วยตามสัญญา (BU-quota), business unit หนึ่งมีสิทธิ์เติม **ที่นั่งผู้ใช้** ได้กี่ที่ตามสัญญาของมันเอง (seats), และตัวสัญญา **subscription** เอง — เรคคอร์ดความสัมพันธ์เชิงพาณิชย์ต่อ BU หนึ่งหน่วยของ cluster ที่พก feature group ซึ่งสัญญานั้นให้สิทธิ์ใช้งาน สามประเภทการซื้อ สามบัญชี หนึ่งโมดูล `src/pages/licenses/` คือไดเรกทอรีที่เปลี่ยนมากที่สุดใน SPA ตลอดช่วงที่แผนนี้ไล่ตรวจ (228 commits) — แทบทุกหน้าจอที่เอกสารหน้านี้อธิบายถูกสร้างใหม่อย่างน้อยหนึ่งรอบนับตั้งแต่ baseline ที่เคยบันทึกไว้ล่าสุดของโมดูลนี้

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** บัญชีซื้อสำหรับ BU-quota ระดับ cluster (`tb_cluster_license`) และที่นั่งระดับ BU (`tb_business_unit_license`) บวกสัญญา subscription (`tb_subscription`) ที่พก feature-group entitlement &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับด้านการค้า/licensing ของ Platform admin SPA &nbsp;·&nbsp; **Route:** `/licenses` (`LicenseCenter`), `/licenses/:clusterId` (`ClusterLicenseDetail`), `/licenses/subscriptions/{new,:id/edit}` (`SubscriptionForm`), `/licenses/seats/{new,:id/edit}` และ `/licenses/bu-quota/{new,:id/edit}` (ทั้งคู่ render **component เดียวกัน** คือ `LicensePurchaseForm` สลับด้วย prop `config`) &nbsp;·&nbsp; **Route เก่า:** `/subscriptions`, `/subscriptions/new`, `/subscriptions/:id/edit` ทุกตัว redirect เข้า `/licenses/...` — ลิงก์เก่ายังใช้ได้ &nbsp;·&nbsp; **Permission key:** `subscription.read` (nav + view) และ `subscription.manage` (create/edit/cancel) — **ไม่ใช่** `license.manage` ซึ่งเป็นของอีกโมดูลหนึ่ง (ดู §3) &nbsp;·&nbsp; **Feature-flag key:** `licenses` (ตรวจหลัง permission gate บนทุก route) &nbsp;·&nbsp; **Nav group:** `navGroup.licenseManagement` ("License Management") &nbsp;·&nbsp; **superAdminOnly:** ไม่ใช่ &nbsp;·&nbsp; **e2e suite:** **ไม่มี** — `../carmen-platform-e2e/tests/` ไม่มีไดเรกทอรี `licenses` เลย ทุกคำกล่าวอ้างในหน้าของโมดูลนี้มาจากการอ่าน implementation ล้วน &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูลนี้มีสี่หน้าจอ อยู่บนห้า component ที่แยกกัน:

- **`/licenses` → `LicenseCenter`** — หน้าจอลงจอด แถบ Fleet Capacity (`FleetCapacity`, ใช้ร่วมกับโมดูล [Clusters](/th/platform/clusters) อ่าน `GET /api-system/clusters/summary` แบบไม่กรองตัวเดียวกัน) อยู่เหนือ `TabStrip` สี่มุมมองที่มองข้อมูลชุดเดียวกันคนละแบบ: **By cluster** (`ClusterLicenseTable` — หนึ่งแถวต่อ cluster มิเตอร์ความจุ BU-quota และที่นั่ง คำเตือนโควตาใกล้หมดอายุ), **By subscription** (`SubscriptionTable` render แบบ `embedded`), **By seat license** (`PurchaseLicenseTable` ตั้งค่าสำหรับที่นั่ง) และ **By BU quota** (`PurchaseLicenseTable` ตัวเดียวกัน ตั้งค่าสำหรับ BU-quota) มุมมองที่กำลังเปิดอยู่ถูกเขียนลงทั้ง `?tab=` และ `localStorage` (`license_center_view`) โดย `?tab=` ชนะเสมอตอนโหลดหน้า ลิงก์ที่ส่งต่อกันจึงเปิดมุมมองที่ผู้ส่งตั้งใจไว้เสมอ ไม่ว่าผู้รับจะเคยเปิดแท็บไหนค้างไว้ก็ตาม
- **`/licenses/:clusterId` → `ClusterLicenseDetail`** — รายละเอียด licensing ของ cluster หนึ่งตัว: `LicenseHealthStrip` สรุปทั้งสามบัญชีในบรรทัดเดียว (cap/used/เหลืออีกกี่วันของโควตา, ยอดรวมที่นั่ง, จำนวน/หมดอายุ/ใกล้หมดอายุของสัญญา) ตามด้วย `TabStrip` สามแท็บที่ใช้ข้อมูลชุดเดียวกันที่หน้าเพจแม่โหลดไว้ (ไม่ใช่แต่ละแท็บดึงเอง เพื่อไม่ให้แถบสรุปกับแท็บด้านล่างเพี้ยนจากกันได้เลย): **Quota** (`BuQuotaSection`), **Seats** (`SeatSection`), **Subscriptions** (`SubscriptionSection`) แท็บอ่าน/เขียน `?tab=` และยังรับ hash เก่าแบบ `#seats`/`#subscriptions` ที่ลิงก์ "Manage licences" บนหน้าแก้ไขของ [Business Units](/th/platform/business-units) และ [Clusters](/th/platform/clusters) ยังชี้มาอยู่
- **`/licenses/subscriptions/new`, `/licenses/subscriptions/:id/edit` → `SubscriptionForm`** — สร้าง/แก้สัญญา subscription ดู §3.2 และ [UI Screens](/th/platform/licenses/ui-screens) §3
- **`/licenses/seats/{new,:id/edit}` และ `/licenses/bu-quota/{new,:id/edit}` → `LicensePurchaseForm`** — **component เดียวกัน** ให้บริการทั้งสองประเภทการซื้อ สลับทั้งหมดด้วย prop `config: LicenseKindConfig` (`SEAT_CONFIG` หรือ `BU_QUOTA_CONFIG`, `src/pages/licenses/licenseKindConfig.ts`) ดู §3.1 ว่าสองโหมดต่างกันตรงไหนบ้าง

route ของฟอร์มซื้อทั้งสองแบบในรูป `:id/edit` ถูกกั้นด้วย `subscription.read` ไม่ใช่ `subscription.manage` — เช่นเดียวกับ route แก้ไขของ `SubscriptionForm` ดู §4 ว่าทำไมนี่ไม่ใช่ช่องโหว่ของการกั้นสิทธิ์

## 2. บริบททางธุรกิจ

Carmen ขายลูกค้าโรงแรม/ธุรกิจบริการเป็น cluster ของ business unit และความสัมพันธ์เชิงพาณิชย์นั้นมีสามมิติที่ซื้อแยกจากกันได้:

1. **cluster หนึ่งสร้าง business unit ได้กี่หน่วย** — โควตาระดับ cluster ซื้อเป็นแถว `tb_cluster_license` และถูกใช้โดยหน้าสร้าง/แก้ของ [Clusters](/th/platform/clusters)
2. **business unit หนึ่งเติมที่นั่งผู้ใช้ได้กี่ที่** — โควตาระดับ BU ซื้อเป็นแถว `tb_business_unit_license` และถูกใช้โดยแท็บ Users ของ [Business Units](/th/platform/business-units)
3. **สัญญาของ business unit หนึ่งให้สิทธิ์ใช้ feature อะไรบ้าง** — พกด้วยแถว `tb_subscription` (หนึ่ง BU ต่อหนึ่งสัญญา นับตั้งแต่ migration `20260821130000_subscription_one_bu`) และ feature group ที่เลือกไว้ ซึ่งนิยามอยู่ในโมดูล [License Catalog](/th/platform/license-catalog) และถูกใช้จริงตอน runtime โดยทั้ง `carmen-platform` และ `carmen-inventory-frontend-react`

โมดูลนี้คือที่ที่ทั้งสามการซื้อถูกบันทึก เรียกดู และ (สำหรับ quota/seats) ยกเลิกได้ มันไม่ตัดสินว่า feature group *มีอะไรอยู่ข้างใน* — catalog นั้นเป็นของและแก้ไขได้ที่ [License Catalog](/th/platform/license-catalog) เท่านั้น โมดูลนี้แค่ให้ subscription เลือกจากมันได้

## 3. แนวคิดสำคัญ

### 3.1 ฟอร์มเดียว สองประเภทการซื้อ

`LicensePurchaseForm` เป็นหน้าจอแก้ไขเดียวสำหรับทั้ง `tb_cluster_license` (BU-quota) และ `tb_business_unit_license` (seats) ทุกสิ่งที่ต่างกันอยู่ใน `LicenseKindConfig` (`licenseKindConfig.ts`) ไม่เคยกระจายเป็น `if (kind === ...)` ในฟอร์มเอง:

| แง่มุม | Seats (`SEAT_CONFIG`) | BU quota (`BU_QUOTA_CONFIG`) |
|---|---|---|
| เจ้าของ | business unit (`ownerParam: 'bu'`) | cluster (`ownerParam: 'cluster'`) |
| ชื่อฟิลด์จำนวนบนสาย | `licensed_users` | `licensed_bus` |
| สวิตช์ "ไม่มีวันหมดอายุ" | **ไม่มีให้** (`showNoExpiry: false`) | มีให้ — เขียน sentinel `2099-12-31T23:59:59.999Z` |
| ช่อง Note | ไม่แสดง | แสดง (ข้อความอิสระ — เช่น "migrated from `tb_cluster.max_license_bu` (old value: 2)") |
| แสดง Cluster เป็นช่องอ่านอย่างเดียวแยกต่างหาก | ใช่ — ที่นั่งของ BU อยู่ใน cluster ไหนต้องบอกให้ชัด | ไม่ใช่ — เจ้าของ **คือ** cluster อยู่แล้ว |
| กติกาการนับ | **ผลรวม** ของทุกใบที่ active (`sumActiveLicenses`) | **ใบที่ชนะใบเดียว** (`activeLicense` — `start_date` ใหม่ที่สุดชนะ ไม่ใช่ผลรวม) |
| ตัวอ่าน "เจ้าของใช้ไปแล้วเท่าไร" | ไม่มี (`readUsage: null`) — ตัวหารของที่นั่งคือจำนวนผู้ใช้ของ BU ซึ่งเป็นสูตรคนละชุด | `clusterService.getById(clusterId).bu_used` |
| การยกเลิก (cancel) | **ไม่มีให้** (`cancel: null`) — ไม่มี endpoint ยกเลิกสำหรับที่นั่งเลย แก้ไขหรือลบทิ้งได้เท่านั้น | มีให้ (`clusterLicenseService.cancel`) — ใบยังอยู่ในบัญชีแต่หยุดให้โควตา ย้อนกลับไม่ได้ |
| prefix เลขที่ใบ | `SEAT-YYMM-####` | `BUQ-YYMM-####` |
| segment ของ path แก้ไข | `seats` | `bu-quota` |
| ฟิลด์เกณฑ์ใกล้หมดอายุที่อ่าน | `thresholds.seat_days` | `thresholds.bu_quota_days` |

แถวกติกาการนับเป็นเรื่องตั้งใจ ไม่ใช่ความพลาด: ที่นั่งเป็นผลรวมเพราะ BU หนึ่งถือใบซื้อที่นั่งพร้อมกันได้หลายใบและทุกใบนับรวมกันจริง ส่วน BU-quota เป็นแบบชนะใบเดียวเพราะเคสที่ตั้งใจรองรับคือ "ซื้อโควตาใหม่ที่ใหญ่กว่ากลางสัญญา" — ใบใหม่ต้องแทนที่เพดานของใบเก่าทันทีที่ถึงวันเริ่ม ไม่ใช่บวกเพิ่มเข้าไป สองสูตรนี้อยู่คนละไฟล์ (`utils/buLicense.ts` เทียบ `utils/clusterLicense.ts`) โดยตั้งใจ เพื่อไม่ให้ใครหยิบสูตรหนึ่งไปใช้ผิดที่

### 3.2 Subscription พก feature-group entitlement ไม่ใช่ feature รายตัว

แถว `tb_subscription` (หนึ่งแถวต่อคู่ cluster+BU วันที่ของสัญญา `status`) มีอยู่เพื่อผูก entitlement ระดับ **feature-group** (`tb_subscription_bu_group` ต่อผ่าน `tb_subscription_bu`) เข้ากับ business unit — แทนที่ทั้งชุดทุกครั้งที่บันทึก (`PUT .../groups` ส่งชุดที่ต้องการทั้งหมด ไม่ใช่ diff) การ์ด "Purchased Groups" ของ `SubscriptionForm` (`GroupSelectionCard`) ให้ผู้แก้ไขเลือกจากกลุ่มที่ [License Catalog](/th/platform/license-catalog) นิยามไว้ และกางดูแต่ละกลุ่มแบบอ่านอย่างเดียวว่ามันให้ feature อะไรบ้าง — หน้าจอนี้ไม่มี checkbox รายฟีเจอร์อีกต่อไปแล้ว (UI นั้น `FeatureSelectionCard` มีอยู่เฉพาะในหน้าจอแก้ไขกลุ่มของ License Catalog เอง) สัญญายังโชว์ `feature_keys` (ชุดที่ backend คำนวณจริงให้ BU นั้น) คู่กับ `group_ids` ของมัน สัญญาที่ย้ายมาก่อนระบบกลุ่มจะมีอยู่ — ใบที่มี feature แต่ไม่มีกลุ่ม — จึงถูกเห็นได้ชัดแทนที่จะถูกแสดงผิด ๆ อย่างเงียบ ๆ

### 3.3 Route เก่า `/subscriptions*` ยังใช้ได้

`/subscriptions` และ `/subscriptions/new` render `<Navigate>` ตรง ๆ ไปที่ `/licenses` และ `/licenses/subscriptions/new` ตามลำดับ; `/subscriptions/:id/edit` render `SubscriptionEditRedirect` ซึ่งอ่านพารามิเตอร์ `:id` แล้ว redirect ไปที่ `/licenses/subscriptions/:id/edit` ด้วย id เดิม — บุ๊กมาร์กเก่าไปยังสัญญาใบหนึ่งยังเปิดสัญญาใบนั้นเป๊ะ **`/licenses/subscriptions/...` คือ path หลัก**; path เก่ามีไว้เพื่อไม่ให้สิ่งที่ลิงก์ไปที่ `/subscriptions*` อยู่แล้วพัง มีจุดหนึ่งที่ผู้ทดสอบควรสังเกต: `/subscriptions` (รายการเปล่า ๆ) ลงจอดที่แท็บ **"By cluster"** ซึ่งเป็นค่าเริ่มต้นของ License Center ไม่ใช่แท็บ "By subscription" — สองแท็บนี้ห่างกันแค่คลิกเดียว แต่บุ๊กมาร์กไปยังรายการ subscription เก่าไม่ได้เปิดมุมมองที่เทียบเท่ากันโดยอัตโนมัติ

### 3.4 เกณฑ์ใกล้หมดอายุตั้งค่าได้ ไม่ใช่ค่าตายตัว

ป้าย "ใกล้หมดอายุ" ทุกป้ายบนทุกหน้าจอของโมดูลนี้อ่านค่าจำนวนวันหนึ่งในสาม — `subscription_days`, `bu_quota_days`, `seat_days` — จาก `useExpiryThresholds()` ไม่ใช่ค่าตายตัว 30 ดู [Data Model](/th/platform/licenses/data-model) §6 สำหรับค่าจริง แหล่งที่มา และผลกระทบต่อแต่ละบัญชี ตัวเกณฑ์เองแก้ได้จากหน้าจอ [Platform Config](/th/platform/platform-config) ไม่ใช่ที่นี่

### 3.5 การกั้นด้วย Nav และ Feature flag

รายการ sidebar "Licenses" (`platformNav.ts:20`) มี `permission: 'subscription.read'`, `groupKey: 'navGroup.licenseManagement'`, `feature: 'licenses'` และ**ไม่มี** `superAdminOnly` ทั้งห้า route ใน §1 มี `feature="licenses"` บน `PrivateRoute` ตรวจ**หลัง**ด่าน permission (permission ไม่ผ่านจะขึ้น `<Forbidden>` เสมอ; permission ผ่านแต่ flag ตั้งเป็น `hide`/`inactive` จะขึ้น `NotFound`/`ComingSoon` แทน — ดู [Permissions](/th/platform/licenses/permissions) §2)

## 4. บทบาทและ Persona

การเข้าถึงถูกกั้นด้วยสิทธิ์ผ่าน [Platform RBAC](/th/platform/rbac) รูปแบบที่เป็นเอกลักษณ์ของโมดูลนี้คือ: **route `:id/edit` ต้องการแค่ `subscription.read` ขณะที่ route `new` และทุกการแก้ไขต้องการ `subscription.manage`** นี่ไม่ใช่ช่องโหว่ — ทั้ง `SubscriptionForm` และ `LicensePurchaseForm` คำนวณ `canEdit = hasPermission('subscription.manage')` เองภายใน และ render ทุกช่องเป็นอ่านอย่างเดียว พร้อมห่อทุกปุ่ม Save/Create/Cancel-licence ด้วย `<Can permission="subscription.manage">` เมื่อไม่มีสิทธิ์นั้น session ที่มีแค่ `subscription.read` จึงเปิด `/licenses/subscriptions/:id/edit` ได้และเห็นสัญญา แต่หน้าจะไม่มีช่องกรอกที่แก้ได้และไม่มีปุ่ม Save เลย backend เองก็บังคับความไม่สมมาตรนี้แยกต่างหากเช่นกัน: `PlatformClusterLicensesController`/`PlatformBusinessUnitLicensesController`/controller ของ subscriptions ทุกตัวต้องการ `subscription.manage` บนทุก route `POST`/`PATCH`/`PUT`/`DELETE`/`cancel` (พิสูจน์ไว้ใน [Permissions](/th/platform/licenses/permissions) §2) ขณะที่ route `GET` ไม่มี `@RequirePlatformPermission` เลย — สิทธิ์อ่านใบของ cluster ตัวเองถูกตรวจสอบภายใน `micro-cluster` ด้วย scope ของ cluster กลไกเดียวกับที่ `GET /api-system/clusters/:id` ใช้ ผู้ดูแล cluster แบบสมาชิกภาพเท่านั้นที่ดู cluster ของตัวเองจึงไม่ถูก 403 ด้วยคีย์ RBAC ที่พวกเขาไม่เคยได้รับ

มี persona ที่สองที่แยกออกไปคนละทางเลย อ่านข้อมูลบางส่วนของโมดูลนี้ได้โดยไม่มี permission key ใดเลย: **cluster admin** (สมาชิกภาพ `tb_cluster_user.role = 'admin'` ไม่ใช่สิทธิ์ RBAC) เห็น `/cluster-admin/:clusterId/licenses` → `ClusterAdminLicenses` — มุมมองความจุแบบอ่านอย่างเดียว สร้างจาก hook/service ชุดเดียวกับที่โมดูลนี้ใช้ (`useLicenseLedger`, `useClusterSeatLicenses`, `clusterLicenseService`) แต่ตอบคำถาม "พอไหม" แทนที่จะเป็น "ออกใบใหม่" หน้านั้นไม่เคยเรียก `GET /platform/subscriptions` เลยด้วยซ้ำ เพราะทุก endpoint เขียนตอบ 403 ให้ cluster admin เสมอ (ไม่มีสิทธิ์ RBAC ใด ๆ อยู่ใน session ของพวกเขาเลย) และหน้านั้นไม่มีอะไรให้ทำกับข้อมูล subscription ที่มันแก้ไขไม่ได้ นี่คือโมดูลแยกต่างหากในวิกินี้ (`cluster-admin`) เอกสารแยกไว้ต่างหาก — ดู [โมดูลที่เกี่ยวข้อง](#5-โมดูลที่เกี่ยวข้อง)

เมทริกซ์การกั้นสิทธิ์แบบเต็ม, การแยก read/manage ที่พิสูจน์กับทั้ง frontend และ backend source, และกรณีพิเศษของโมดูลนี้ อยู่ที่ [Permissions](/th/platform/licenses/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Clusters](/th/platform/clusters) — เป็นเจ้าของฝั่ง *ผู้บริโภค* ของ BU-quota: แท็บ Licensing ของ `ClusterEdit` อ่านบัญชี `tb_cluster_license` เดียวกับที่โมดูลนี้เขียน และแถบ Fleet Capacity ทั้งบน `/clusters` และ `/licenses` อ่าน `GET /api-system/clusters/summary` endpoint เดียวกัน
- [Business Units](/th/platform/business-units) — เป็นเจ้าของฝั่ง *ผู้บริโภค* ของ seats: แท็บ Licenses ของ `BusinessUnitEdit` (`BusinessUnitLicensesCard`) เป็นสรุปแบบอ่านอย่างเดียวของ seat pool ของ BU พร้อมลิงก์ "Manage licences" และ "New subscription" เข้าโมดูลนี้ มันไม่ดึงหรือแก้ข้อมูลที่นั่งเอง เพื่อไม่ให้มีสองแหล่งความจริง
- [License Catalog](/th/platform/license-catalog) — เป็นเจ้าของ catalog ของ feature/feature-group ที่ subscription ของโมดูลนี้เลือกใช้ (§3.2) โมดูลนี้ไม่มีหน้าจอสร้าง/แก้ catalog entry
- [cluster-admin](/th/platform/cluster-admin) — มุมมอง "พอไหม" แบบอ่านอย่างเดียวขอบเขตสมาชิกภาพของบัญชีทั้งสามชุดเดียวกัน ไม่มี permission gate และไม่มีทางเขียน (§4)
- [Platform Config](/th/platform/platform-config) — เป็นเจ้าของค่าเกณฑ์ใกล้หมดอายุที่ป้าย "expiring soon" ของโมดูลนี้อ่าน (§3.4)

## 6. แหล่งข้อมูลอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (Platform admin SPA) ยกเว้นที่ขึ้นต้นด้วย `../carmen-turborepo-backend-v2` (backend monorepo)

- `../carmen-platform/src/App.tsx` (บรรทัด 183–249) — route guard ทั้งห้าของ `/licenses*` บวก redirect เก่าสามตัวของ `/subscriptions*` และ `SubscriptionEditRedirect`
- `../carmen-platform/src/components/nav/platformNav.ts` (บรรทัด 20) — รายการ sidebar "Licenses": `permission: 'subscription.read'`, `groupKey: 'navGroup.licenseManagement'`, `feature: 'licenses'`
- `../carmen-platform/src/pages/licenses/LicenseCenter.tsx` — หน้าจอลงจอดสี่แท็บและแถบ Fleet Capacity
- `../carmen-platform/src/pages/licenses/ClusterLicenseDetail.tsx` — หน้าจอรายละเอียดสามแท็บของแต่ละ cluster และ `LicenseHealthStrip`
- `../carmen-platform/src/pages/licenses/SubscriptionForm.tsx` — ฟอร์มสร้าง/แก้ subscription
- `../carmen-platform/src/pages/licenses/LicensePurchaseForm.tsx` — ฟอร์มซื้อ seat/BU-quota ที่ใช้ร่วมกัน
- `../carmen-platform/src/pages/licenses/licenseKindConfig.ts` — `SEAT_CONFIG`/`BU_QUOTA_CONFIG` ไฟล์เดียวที่เก็บทุกความต่างระหว่างสองประเภทการซื้อ (§3.1)
- `../carmen-platform/src/pages/licenses/sections/{BuQuotaSection,SeatSection,SubscriptionSection}.tsx` — สามแท็บของ `ClusterLicenseDetail`
- `../carmen-platform/src/pages/clusterAdmin/ClusterAdminLicenses.tsx` — คู่หูฝั่ง cluster-admin แบบอ่านอย่างเดียว (§4)
- `../carmen-platform/src/services/{clusterLicenseService,businessUnitLicenseService,subscriptionService,expiryThresholdService}.ts` — REST client
- `../carmen-platform/src/context/ExpiryThresholdContext.tsx` — `useExpiryThresholds()`, `DEFAULT_EXPIRY_THRESHOLDS`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_cluster_license` (บรรทัด 1168), `tb_business_unit_license` (บรรทัด 1133), `tb_subscription` (บรรทัด 452)
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260822000000_add_cluster_license/migration.sql` และ `20260901020000_cluster_license_cancel/migration.sql` — `v_cluster_bu_cap`/`v_cluster_bu_quota` (ดู [Data Model](/th/platform/licenses/data-model) §3)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/{platform_cluster-licenses,platform_business-unit-licenses,platform_subscriptions}/*.controller.ts` — การบังคับใช้สิทธิ์ (ดู [Permissions](/th/platform/licenses/permissions))

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/licenses/data-model) — `tb_cluster_license`, `tb_business_unit_license`, `tb_subscription` และ join table ของกลุ่ม; view `v_cluster_bu_cap`/`v_cluster_bu_quota`/`v_business_unit_seat`; และค่าเกณฑ์ใกล้หมดอายุพร้อมผลกระทบต่อแต่ละบัญชี
- [UI Screens](/th/platform/licenses/ui-screens) — สี่แท็บของ `LicenseCenter`, สามส่วนของ `ClusterLicenseDetail`, ฟอร์มซื้อ/สัญญาทั้งสองแบบ และพฤติกรรมของ redirect เก่า
- [Permissions](/th/platform/licenses/permissions) — เมทริกซ์การกั้นสิทธิ์, การแยก read-vs-manage ที่พิสูจน์กับทั้ง frontend และ backend source, และกรณีพิเศษสำหรับผู้ทดสอบ
