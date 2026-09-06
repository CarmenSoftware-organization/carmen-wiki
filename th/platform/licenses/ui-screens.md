---
title: ไลเซนส์ — หน้าจอ UI (UI Screens)
description: สี่แท็บของ LicenseCenter, สามส่วนของ ClusterLicenseDetail, SubscriptionForm และ LicensePurchaseForm ที่ใช้ร่วมกัน, และพฤติกรรมของ redirect เก่าจาก /subscriptions
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, licenses, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# ไลเซนส์ — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `LicenseCenter` (`/licenses`, 4 แท็บ) &nbsp;·&nbsp; `ClusterLicenseDetail` (`/licenses/:clusterId`, 3 แท็บ) &nbsp;·&nbsp; `SubscriptionForm` (`/licenses/subscriptions/{new,:id/edit}`) &nbsp;·&nbsp; `LicensePurchaseForm` — **component เดียว สองโหมด** สลับด้วย prop `config` (`/licenses/seats/*`, `/licenses/bu-quota/*`) &nbsp;·&nbsp; **Route เก่า:** `/subscriptions*` redirect เข้า `/licenses/...` &nbsp;·&nbsp; **ภาพร่วม:** `LicenseCoverageBar` — เส้นเวลาแนวนอนแบบ div ล้วน (ไม่มี chart library) ของช่วงความคุ้มครอง ใช้ในทั้งสามแท็บของ `ClusterLicenseDetail` &nbsp;·&nbsp; **ไม่มี View History / Activity Trail** — ต่างจากโมดูลอื่นส่วนใหญ่ในแผนนี้ โมดูลนี้ไม่มี action "ดูประวัติ" ที่กั้นด้วย `activity_log.read` อยู่บนหน้าจอไหนเลย &nbsp;·&nbsp; **ไม่มี e2e suite** — ทุกคำกล่าวอ้างด้านล่างมาจาก implementation ไม่ใช่จาก test spec

## 1. ภาพรวม

สี่ route ของโมดูลนี้ render ห้า component โดยสามตัวใช้ข้อมูลที่โหลดมาชุดเดียวกันร่วมกันข้ามแท็บ แทนที่แต่ละแท็บจะดึงสำเนาของตัวเอง — เป็นความตั้งใจ เพื่อไม่ให้แถบสรุปกับแท็บด้านล่างเพี้ยนจากกันได้เลย สองประเภทการซื้อ (seats, BU quota) ใช้ฟอร์มแก้ไข**เดียวกัน** (`LicensePurchaseForm`) สลับทั้งหมดด้วย `LicenseKindConfig` ที่ route ส่งเข้ามา (ดู [Data Model](/th/platform/licenses/data-model) §2.1–2.2 และ [หน้าลงจอด](/th/platform/licenses) §3.1 ว่า config เปลี่ยนอะไรบ้าง) ทุกหน้าจออ่านเกณฑ์ "ใกล้หมดอายุ" จาก `useExpiryThresholds()` ไม่เคยเป็นตัวเลขตายตัว (ดู [Data Model](/th/platform/licenses/data-model) §6)

ทั้งสี่หน้าจอมีของมาตรฐานของ SPA เหมือนกัน — `TableSkeleton` ตอนโหลดครั้งแรก, `EmptyState` เมื่อผลลัพธ์ว่างเปล่า, toast แจ้งผลตอนแก้ไข, การบันทึกแบบ optimistic-lock ด้วย `doc_version` (toast แจ้งขัดแย้ง + reload ตอน `409`), การ์ด `useUnsavedChanges` กันออกจากหน้าตอนฟอร์มมีการแก้ไขค้างอยู่, `useGlobalShortcuts` (⌘/Ctrl+S บันทึก, Escape ยกเลิก), และ `DevDebugSheet` เฉพาะ dev ที่โชว์ raw response ของแต่ละหน้าจอ **โมดูลนี้ไม่มี View History / Activity Trail เลยสักหน้า** — งานของโมดูลอื่นในแผนนี้ส่วนใหญ่บันทึกไว้ว่ามี action "View History" ที่กั้นด้วย `activity_log.read` ข้าม-โมดูลอยู่บนแถวของ list และหัวของหน้าแก้ไข การ grep `src/pages/licenses/` และ `LicenseCenter.tsx` โดยตรงหา `activity_log.read`/`ActivityTrailSheet`/`PLATFORM_SCOPED_RECORD` ไม่เจออะไรเลย โมดูลนี้ไม่เคยได้รับ feature นั้นมา

## 2. `LicenseCenter` (`/licenses`)

### 2.1 แถบ Fleet Capacity

`PageHeader` ("Licenses") อยู่เหนือ component `FleetCapacity` ที่ใช้ร่วมกัน — แถบเดียวกับที่ list ของ [Clusters](/th/platform/clusters) เองใช้ อ่าน `GET /api-system/clusters/summary` แบบไม่กรองตัวเดียวกัน สถิติ "BU quota expiring" ของมันคลิกได้และสลับตัวแปร `expiringSoonFilter` ฝั่ง client ที่กรองแค่ตารางในแท็บ **By cluster** เท่านั้น — ยอดรวมของแถบเองไม่เคยถูกกรองด้วยมัน เพราะต้องบอกภาพรวมของทั้ง fleet เสมอไม่ว่าแท็บหรือ filter ไหนกำลังเปิดอยู่ด้านล่าง

### 2.2 สวิตช์สี่แท็บ

`TabStrip` (จอใหญ่) / `<Select>` (มือถือ, `sm:hidden`, เพราะสี่แท็บที่ความกว้าง 386px จะเหลือป้ายของแท็บที่สี่โผล่มาแค่ 4px) สลับระหว่าง:

| แท็บ | Component | เนื้อหา |
|---|---|---|
| By cluster | `ClusterLicenseTable` | หนึ่งแถวต่อ cluster: มิเตอร์ความจุ BU-quota และที่นั่ง, วันที่/ป้ายเตือนโควตาหมดอายุ, สถานะ active/inactive ของ cluster, คอลัมน์ audit Updated |
| By subscription | `SubscriptionTable` (render แบบ `embedded`) | รายการ subscription ทั้ง fleet — ทุกสัญญาข้ามทุก cluster |
| By seat license | `PurchaseLicenseTable` (`config={SEAT_CONFIG}`) | ทุกแถวซื้อที่นั่งข้ามทุก business unit |
| By BU quota | `PurchaseLicenseTable` (`config={BU_QUOTA_CONFIG}`) | ทุกแถวซื้อ BU-quota ข้ามทุก cluster |

แท็บที่กำลังเปิดอยู่ถูกเขียนลงทั้ง URL (`?tab=`) และ `localStorage` (`license_center_view`) ทุกครั้งที่เปลี่ยน และตอนโหลดหน้า URL ชนะค่าที่เก็บไว้ — ลิงก์ deep link ที่ส่งต่อกันไปที่ `?tab=seat` เปิดมุมมองนั้นเสมอ แม้เบราว์เซอร์ของผู้รับจะเปิดแท็บอื่นค้างไว้ล่าสุดก็ตาม ค่า `?tab=` ที่จำไม่ได้หรือเก่าเกินไป (พิมพ์ผิด หรือค่าจากแอปเวอร์ชันที่ใช้ชื่อแท็บต่างออกไป) จะถูกแก้ไขในที่: หน้าจอ render มุมมองสำรองของมัน แล้วเขียนทับ URL ให้ตรง แทนที่จะปล่อยให้ address bar อ้างว่ากำลังแสดงมุมมองที่ไม่ได้แสดงจริง

### 2.3 `ClusterLicenseTable` — By cluster

คอลัมน์: **Cluster** (code, ลิงก์ไปที่ `/licenses/:clusterId`) · **Name** · **BU Quota** (`CapacityMeter` ของ `bu_used`/`bu_cap`; cluster ที่ `bu_cap = 0` โชว์ข้อความ "No licence" แทนมิเตอร์ 0/0 เพราะความจุศูนย์กับ "ไม่มีใบซื้อเลย" อ่านเหมือนกันบนอัตราส่วนล้วน ๆ) · **Seats** (`CapacityMeter` ของยอดรวมการใช้/ความจุที่นั่งของ cluster) · **Quota Expires** (วันที่จาก `cap_end_date` ของ `v_cluster_bu_cap` พร้อมป้ายเตือนเมื่อ `daysLeft <= thresholds.bu_quota_days`; หมดอายุแบบ perpetual หรือไม่มีข้อมูลแสดงเป็นขีดกลางเฉย ๆ ไม่ใช่คำว่า "No expiry" ซ้ำทุกแถว) · **Status** (ธง `is_active` **ของ cluster เอง** — ป้าย Inactive แบบ exception-only ไม่ใช่คอลัมน์สถานะของใบอนุญาต) · **Updated** (`AuditMeta`/`auditColumns()` ที่ใช้ร่วมกัน) เรียงลำดับเริ่มต้น `code:asc`

การค้นหาเป็นช่องข้อความล้วน; sheet Filters มีสองกลุ่มที่เป็นอิสระต่อกัน — กลุ่ม **Status** (Active/Inactive ของ cluster) และกลุ่ม **License** สามคีย์พิเศษที่ backend รู้จัก (`bu_quota_missing`, `bu_over_limit`, `seats_full`) ที่ backend แปลงเป็นลิสต์ id จาก view ชุดเดียวกับที่ตัวเลขในตารางนี้มาจาก filter กับตัวเลขในตารางจึงไม่มีวันขัดแย้งกันว่า cluster ไหนเข้าเงื่อนไข คีย์เหล่านี้ไม่ใช่ชื่อคอลัมน์จริง — การส่งคีย์ที่ backend ยังไม่รู้จักไปจะพังทันที (Prisma error บน `where` key ที่ไม่มีจริง) ซึ่งเป็นเหตุผลที่ frontend ต้อง deploy ตามหลัง backend ที่นิยามมันเสมอ

### 2.4 `SubscriptionTable` — By subscription

รายการสัญญาทั้ง fleet, render แบบ `embedded` อยู่ใน `LicenseCenter` (เส้นทาง render แบบไม่ embedded ของมันเอง — พร้อม `<Layout>`/`<PageHeader>` ของตัวเอง — เป็นโค้ดที่ตายแล้วในการ routing จริงวันนี้: ไม่มี route ไหน mount `<SubscriptionTable>` แบบไม่ใส่ `embedded` อีกต่อไป นับตั้งแต่ `/subscriptions` redirect ไปที่ `/licenses` แทนที่จะเป็นรายการ subscription เปล่า ๆ) คอลัมน์: **Subscription** (เลขที่, ลิงก์ไปฟอร์มแก้ไข) · **Cluster** · **Business Unit** · **State** (`active`/`inactive`/`expired` ที่ backend คำนวณมา บวกป้ายเตือน "Expiring soon" แยกต่างหากที่คำนวณฝั่ง client จาก `thresholds.subscription_days`) · **Features** (จำนวน) · **Period** (`start_date → end_date`) · **Created**/**Updated** (`AuditMeta` ที่ใช้ร่วมกัน) เรียงลำดับเริ่มต้น `end_date:desc` พร้อม tiebreaker `id:asc` ต่อท้ายทุกค่า sort ที่ตารางส่งไป — backend ไม่มี `orderBy` เริ่มต้นเลย และการเรียงคอลัมน์เดียวที่มีค่าซ้ำจะทำให้แถวสลับตำแหน่งข้ามหน้าโดยไม่มีอะไรเตือน

แถบ `SubscriptionSummary` เหนือตาราง (chip filter คลิกได้, `SummaryFilterKey`) และ sheet Filters กรองรายการตาม cluster และ state ปุ่มบน header คือ **Export** (CSV ของหน้าปัจจุบัน) และ **Add Subscription** (`<Can permission="subscription.manage">`, ไปที่ `/licenses/subscriptions/new` โดยไม่มี query param ล่วงหน้า — สร้างจากที่นี่ต้องเลือกทั้ง cluster และ BU เองบนฟอร์มสร้าง ต่างจากการสร้างจากหน้าแก้ไขของ business unit ที่ prefill ทั้งคู่มาให้) **ตารางนี้ไม่มีเมนู action ต่อแถวและไม่มี Delete เลย** — สิ่งเดียวที่ลิงก์ Subscription/Cluster ของแถวทำคือนำทางไปฟอร์มแก้ไข dropdown "Edit" ที่มีรายการเดียวถูกถอดออกเพราะซ้ำกับลิงก์ที่คลิกได้อยู่แล้ว และ Delete เองถูกถอดออกเพราะ subscription ที่ soft-delete แล้วไม่มีวันถูกแสดงกลับมาโดย endpoint ไหนเลย ปุ่มลบที่ไม่มีใครตรวจสอบหรือย้อนกลับได้แย่กว่าไม่มีปุ่มเลย `subscriptionService.delete()` ยังมีอยู่ในฝั่ง client และ route ของ backend ก็ยังบังคับ `subscription.manage` อยู่ แต่ไม่มี UI ไหนในโมดูลนี้เรียกมัน

### 2.5 `PurchaseLicenseTable` — By seat license / By BU quota

Component เดียว สลับด้วย `config` แสดงรายการทุกแถวซื้อของประเภทหนึ่งข้ามทั้ง fleet คอลัมน์: **License Number** (ลิงก์ไปที่ `/licenses/{seats|bu-quota}/:id/edit`) · **Cluster** (เฉพาะประเภทที่นั่ง — `config.showCluster` เพราะเจ้าของของที่นั่งคือ BU และตารางยังบอกด้วยว่า BU นั้นอยู่ cluster ไหน; แถวของ BU-quota ไม่มีคอลัมน์นี้เพราะเจ้าของ**คือ** cluster อยู่แล้ว) · **[Business Unit | Cluster]** (เจ้าของ ป้ายสลับตาม `config.kind`) · **Amount** (`licensed_users`/`licensed_bus`) · **Coverage** (`start_date – end_date` เป็นข้อความล้วน) · **Status** (คำนวณฝั่ง client จากวันที่ — `active`/`scheduled`/`expired` บวก `superseded`/`cancelled` เฉพาะประเภท BU-quota; ไม่ใช่คอลัมน์ที่เรียงได้เพราะไม่ใช่ฟิลด์จริงของ backend) · **Reference No** · **Created** (แถวของตารางนี้ไม่มี `updated_at` บน DTO เลย จึงไม่มีคอลัมน์ Updated เฉพาะที่นี่ ต่างจากตาราง Management-style อื่นในโมดูลนี้) sheet Filters เสนอแค่ `active`/`scheduled`/`expired` ไม่ว่าประเภทไหน — `superseded`/`cancelled` จงใจไม่อยู่ในรายการ filter แม้ตอนเปิดแท็บ BU-quota เพราะปุ่ม filter ที่ไม่คืนอะไรเลยตอนเปิดแท็บ seat จะเป็นปุ่มที่โกหกว่าทำอะไรได้

CSV export (ฝั่ง client เฉพาะหน้าปัจจุบัน) เพิ่มคอลัมน์ audit สี่คอลัมน์ (Created/Updated At/By) นอกเหนือจากคอลัมน์ที่มองเห็นในตาราง

## 3. `ClusterLicenseDetail` (`/licenses/:clusterId`)

### 3.1 หัวเพจและแถบสรุปสุขภาพ

`PageHeader` โชว์ชื่อของ cluster (หรือ "Cluster not found or deleted" เทียบกับข้อความ "unavailable" ทั่วไป แยกความล้มเหลวแบบ 404 จริงออกจากความล้มเหลวอื่น) พร้อม code เป็น subtitle ใต้มันลงมา `LicenseHealthStrip` เป็นบรรทัดสรุปเดียว ไม่ใช่กริดการ์ดแบบแถบ Fleet Capacity ของหน้ารายการ เพราะหน้านี้มี cluster เดียวให้อธิบายอยู่แล้วและไม่มีอะไรให้เทียบด้วย สรุปในภาพเดียว: cap/used/เหลืออีกกี่วันของ BU-quota, ยอดรวมที่นั่ง active และจำนวน BU ที่มีที่นั่งศูนย์, จำนวน/หมดอายุ/ใกล้หมดอายุของ subscription ทุกตัวเลขบนแถบและทุกตัวเลขในสามแท็บด้านล่างมาจาก**การโหลดข้อมูลระดับเพจเดียวกัน** (`useLicenseLedger`, `useClusterSeatLicenses`, `useClusterSubscriptions` ทั้งหมดเป็นของ `ClusterLicenseDetail` เอง ไม่ใช่ของ section) — section ต่าง ๆ รับข้อมูลมาเป็น prop แทนที่จะดึงเอง โดยเฉพาะเพื่อไม่ให้ยอดรวมของแถบกับตัวเลขในแท็บเพี้ยนจากกันเมื่อคำขอหนึ่งสำเร็จแต่อีกคำขอที่ซ้ำกันล้มเหลว

### 3.2 สามแท็บ ภาพเส้นเวลาเดียวกัน

`TabStrip` สลับ **Quota** / **Seats** / **Subscriptions** อ่าน/เขียน `?tab=` — และยังรับ hash เก่าแบบ `#seats`/`#subscriptions` ที่ลิงก์ "Manage licences" บนหน้าแก้ไขของ [Business Units](/th/platform/business-units) และ [Clusters](/th/platform/clusters) เองยังชี้มาอยู่ เพื่อให้ลิงก์ข้ามที่มีอยู่แล้วยังลงจอดที่แท็บที่ถูกต้อง ทั้งสามแท็บวาด `LicenseCoverageBar` ต่อกลุ่มแถว — เส้นเวลาแนวนอนแบบ `<div>` ซ้อนล้วน ๆ (ไม่มี chart library; ทึบ = คุ้มครอง, ช่องว่าง = ไม่คุ้มครอง, เส้นตั้ง = วันนี้) ใช้หน้าต่างเวลาคงที่เดียวกันต่อตาราง (สามเดือนย้อนหลัง สิบสองเดือนไปข้างหน้าจาก "ตอนนี้" ปัดเป็นขอบเดือน) เพื่อให้สองแท่งที่ยาวเท่ากันบนหน้าจอเดียวกันแทนความยาวปฏิทินเท่ากันเสมอ

- **Quota** (`BuQuotaSection`) — สองการ์ด การ์ดแรกโชว์แท่งความคุ้มครองของใบ BU-quota ที่ชนะ, อัตราส่วน `buUsed`/`cap` (อ่านจากฟิลด์ `cluster.bu_used` เดียวกับที่หน้าแก้ไขของ [Clusters](/th/platform/clusters) เองและ `ClusterLicenseTable` อ่าน ไม่เคยนับลิสต์ BU ที่โหลดมาเองฝั่ง client) และตารางบัญชีซื้อ (Quota, Start, End, Status, Reference, Note และ — เมื่อ `canManage` — action ต่อแถว: **Edit**, **Cancel** (แบบ soft, ย้อนกลับไม่ได้, confirm dialog แยกต่างหากที่บอกจำนวน BU ที่คาดการณ์หลังยกเลิก), และ **Remove** (ลบจริงด้วย `DELETE`, confirm dialog อีกอันที่ใช้คำต่างออกไป)) การ์ดที่สองจัดอันดับทุก business unit ในคลัสเตอร์ (HQ ก่อน แล้วสร้างเก่าสุดก่อน ตรงกับ `ORDER BY` ของ `v_cluster_bu_quota` เป๊ะ — ดู [Data Model](/th/platform/licenses/data-model) §3.2) และปักป้าย **Over limit** ให้ BU ที่อันดับเกินเพดาน บวกแท่งความคุ้มครองสัญญาของ BU นั้นที่ใช้ซ้ำจากข้อมูลของแท็บ Subscriptions เพื่อไม่ให้สองแท็บคำนวณคำตอบคนละแบบว่า BU นี้มีสัญญา active ไหม
- **Seats** (`SeatSection`) — ตารางเดียว หนึ่งกลุ่มแถวต่อ business unit (ไม่ใช่หนึ่งการ์ดต่อ BU — layout การ์ดต่อ BU แบบเดิมถูกแทนที่เพราะแต่ละ BU ไม่จำเป็นต้องดึงข้อมูลของตัวเองอีกแล้ว และการ์ด empty-state ขนาด ~360px ต่อ BU ที่ไม่มีใบเลยไม่คุ้มพื้นที่อีกต่อไปเมื่อมี BU สิบหน่วยขึ้นไป) กลุ่มแถวเรียงตาม**ความรุนแรง** ไม่ใช่ตามตัวอักษร — BU ที่โหลดล้มเหลวก่อน แล้ว BU ที่ไม่มีที่นั่งเลย แล้ว BU ที่ใกล้หมดอายุ แล้วค่อยเป็นตัวที่ปกติ เพื่อไม่ให้หน้าที่เปิดมาหาปัญหาต้องไล่หาปัญหาใต้ลำดับตัวอักษร แถวหัวของแต่ละ BU มียอดรวมที่นั่ง active, แท่งความคุ้มครองของมัน, และ (เมื่อ `canManage`) ลิงก์ **Add seat license**; แถวใบแต่ละใบข้างใต้มีแค่ **Edit** และ **Remove** (ลบจริง) — **ไม่มี action Cancel สำหรับที่นั่งเลยบนหน้าจอนี้** ตรงกับข้อเท็จจริงของ schema ที่ `tb_business_unit_license` ไม่มีคอลัมน์ `cancelled_at` เลย (ดู [Data Model](/th/platform/licenses/data-model) §2.2)
- **Subscriptions** (`SubscriptionSection`) — ส่วนที่กรองเฉพาะ cluster ของรายการสัญญาชุดเดียวกับที่ `SubscriptionTable` ทั้ง fleet โชว์ ป้ายสถานะและตรรกะ expiring-soon เหมือนกัน และ (เมื่อ `canManage`) ลิงก์ Add Subscription ที่ prefill id ของ cluster นี้มาให้

`canManage` (`hasPermission('subscription.manage')`) คำนวณ**ครั้งเดียว**ที่ระดับเพจ แล้วส่งลงเป็น prop เดียวให้ทั้งสาม section — ไม่มี section ไหนตรวจสิทธิ์ซ้ำเอง โดยเฉพาะเพื่อให้เพจมีแหล่งความจริงเดียวว่า session นี้แก้ไขอะไรได้บ้าง แทนที่จะมีสามจุดที่ในทางทฤษฎีอาจไม่ตรงกัน

## 4. `SubscriptionForm` (`/licenses/subscriptions/new`, `/licenses/subscriptions/:id/edit`)

**โหมดสร้าง** (`isNew`, ไม่มี `:id`): layout สองคอลัมน์ — ฟอร์มอยู่ซ้าย พรีวิว `SubscriptionDraftPlate` แบบสดอยู่ขวา (sticky บนจอ `lg` ขึ้นไป, ซ้อนอยู่ใต้ฟอร์มบนจอแคบกว่า) โชว์ cluster/BU/วันที่ตามที่พิมพ์ ตัวเลือก cluster (`useAllClusters`, ดึงแบบมีเพดาน 10 หน้า ไม่เคย `perpage: -1`) และตัวเลือก BU ของ cluster นั้น (ดึงเมื่อเลือก cluster แล้วเท่านั้น) บังคับทั้งคู่; ตัวช่วย "Term" เสนอ preset วันสิ้นเดือน 14 ตัว (ทุกเดือนของปีปัจจุบัน บวกมกราคม/กุมภาพันธ์ของปีถัดไป) ที่เติมวันหมดอายุจากวันเริ่มที่เลือกด้วยคลิกเดียว คู่กับช่องกรอกวันที่ปกติ วันเริ่มค่าเริ่มต้นคือวันนี้ ตอน submit มีแค่ห้าฟิลด์ที่ endpoint สร้างยอมรับถูกส่งไป — `subscription_number` ไม่เคยอยู่ใน payload เลย server เป็นคนออกเลขนี้ให้เสมอ

**โหมดดู/แก้** (`:id/edit`): `IssuedSubscriptionPlate` (ตัวตน + วันที่ + บรรทัดคำนวณ "เหลืออีก N วัน"/"หมดอายุมาแล้ว N วัน" ที่ขับด้วย `state` จาก backend ไม่เคยคำนวณเองฝั่ง client) แทนที่ layout scrollspy-nav เก่าไปทั้งหมด — แถบนำทางซ้ายสำหรับสองการ์ดบนหน้าที่เลื่อนแค่ครึ่งจอถูกถอดออกในฐานะต้นทุนที่ไม่ได้ประโยชน์ เหมือนการลดความซับซ้อนแบบเดียวกับที่ฟอร์มซื้อที่ใช้ร่วมกันได้รับ (§5 ด้านล่าง) ใต้แผ่นลงมา: `SubscriptionInfoCard` (วันเริ่ม/สิ้นสุดและ status แก้ได้เฉพาะเมื่อมี `subscription.manage` — `editing={canEdit}` ไม่ใช่ปุ่มสวิตช์แยกต่างหาก) และการ์ด "Purchased Groups" (`GroupSelectionCard`, §3.2 ของ [หน้าลงจอด](/th/platform/licenses)) ให้ผู้แก้ไขเลือก feature group จาก catalog แต่ละกลุ่มกางดูได้แบบอ่านอย่างเดียวว่ามันให้อะไรบ้าง บวกคำเตือนเมื่อสัญญามี `feature_keys` แต่ไม่มี `group_ids` (สัญญาก่อนยุคระบบกลุ่มที่ยังไม่ถูก reconcile) BU ที่เลือกตอนสร้างแก้ไขไม่ได้อีกเลย — ฟอร์มแก้ไขไม่มีช่อง BU เลย มีแค่ตัวตนแบบอ่านอย่างเดียวบนแผ่น

แถบล่างแบบ sticky (โชว์เฉพาะเมื่อมีการแก้ไขค้างอยู่) มี **Save Changes** (`<Can permission="subscription.manage">`) และ **Cancel** (คืนค่าที่โหลดมาล่าสุด) เพราะ `subscription.manage` กั้นแค่ปุ่ม Save กับธง field-editability — ไม่ใช่ตัว route เอง ซึ่งต้องการแค่ `subscription.read` — session ที่มีสิทธิ์อ่านอย่างเดียวจึงเปิด URL นี้เป๊ะ ๆ ได้และเห็นทุกช่อง แค่แก้หรือบันทึกไม่ได้ (ดู [Permissions](/th/platform/licenses/permissions) §3)

## 5. `LicensePurchaseForm` (`/licenses/seats/*`, `/licenses/bu-quota/*`)

**Component และโค้ด route handler ตัวเดียวกัน** ให้บริการสี่ route แยกกันแค่ด้วย prop `config: LicenseKindConfig` และ `mode: 'create' | 'edit'` ที่ `App.tsx` ส่งเข้ามา — ดู [Data Model](/th/platform/licenses/data-model) §2.1–2.2 และ [หน้าลงจอด](/th/platform/licenses) §3.1 สำหรับตารางความต่างเต็มระหว่าง seat กับ BU-quota หน้าจอเองมีหน้าตาแบบนี้:

**โหมดสร้าง** บังคับให้มีเจ้าของมาทาง query parameter เท่านั้น (`?bu=` หรือ `?cluster=` บวก `?ownerLabel=` ที่ไม่บังคับสำหรับชื่ออ่านง่าย) — ฟอร์มนี้ไม่มี owner picker เลย ทุกจุดเข้าถึง (ลิงก์ "Add seat license"/"Add BU-quota license" บน `SeatSection`/`BuQuotaSection`, และบนการ์ด Licenses ของ [Business Units](/th/platform/business-units) เอง) ส่งเจ้าของมาให้ตรง ๆ ถ้าไม่มี owner param หน้าจะ render empty state "ไม่มีเจ้าของ" แยกต่างหากแทนที่จะเป็นฟอร์มที่พัง — เกิดได้เฉพาะจาก URL ที่แก้เองหรือค้างเก่าเท่านั้น

**โหมดดู/แก้** โชว์ `IssuedLicensePlate` — ตัวตนของใบ (เลขที่, เจ้าของ, cluster ถ้ามี), ป้ายสถานะที่คำนวณแล้ว, บรรทัด "เหลืออีก N วัน"/"หมดอายุมาแล้ว N วัน" ระบายสีตามเกณฑ์เฉพาะประเภท และ เฉพาะประเภท BU-quota — การใช้งานปัจจุบันของ cluster เจ้าของ (`bu_used`) อ่านผ่าน `config.readUsage` ใต้แผ่นลงมา การ์ด `LicenseFieldsCard` ตัวเดียว ใช้ร่วมกันทั้งสร้างและแก้ ต่างกันแค่ boolean `editing` มี Amount, Reference No, สวิตช์แบบ segmented "มีวันหมดอายุ / ไม่มีวันหมดอายุ" (**โชว์เฉพาะ BU quota** — `config.showNoExpiry`; ประเภทที่นั่งไม่มีสวิตช์นี้และไม่มีแนวคิด perpetual เลย), วันที่คุ้มครอง, และ — เฉพาะ BU-quota — ช่อง Note ข้อความอิสระ (`config.showNote`) **ฟิลด์ของใบ BU-quota ที่ถูกยกเลิกกลายเป็นอ่านอย่างเดียวถาวร** (`canEditFields = canEdit && !isCancelled`) พร้อม banner อธิบายเหนือการ์ด แทนที่จะยอมรับการแก้ไขเรคคอร์ดที่ไม่ให้อะไรแล้วเงียบ ๆ ใบที่นั่งไม่มีสถานะยกเลิกเลยจึงไม่มีวันเข้าเงื่อนไขนี้

action **Cancel this license** (สไตล์ destructive อยู่ท้ายหน้า หลัง `ConfirmDialog`) โผล่ **เฉพาะเมื่อ `config.cancel` ไม่ใช่ null** — คือเฉพาะประเภท BU-quota เท่านั้น ไม่มีปุ่มแบบนี้เลยบนหน้าแก้ไขใบที่นั่ง ตรงกับข้อเท็จจริงของ schema ที่ไม่มี endpoint cancel สำหรับแถว `tb_business_unit_license` เลย ทั้งสองประเภทการซื้อไม่มี action ลบจริงบนหน้าแก้ไขของมันเอง — สิ่งนั้นมีให้แค่จากเมนูแถวของบัญชีต่อคลัสเตอร์เอง (§3.2 ข้างบน) ไม่ใช่จาก URL ของใบเดี่ยวโดยตรง

## 6. Redirect เก่าของ `/subscriptions*`

| Path เก่า | Render อะไร | ปลายทาง |
|---|---|---|
| `/subscriptions` | `<Navigate to="/licenses" replace>` | License Center, แท็บเริ่มต้น **By cluster** — **ไม่ใช่** แท็บ By subscription |
| `/subscriptions/new` | `<Navigate to="/licenses/subscriptions/new" replace>` | ฟอร์มสร้าง พฤติกรรมไม่เปลี่ยน |
| `/subscriptions/:id/edit` | `SubscriptionEditRedirect` | อ่านพารามิเตอร์ `:id` แล้ว redirect ไปที่ `/licenses/subscriptions/:id/edit` ด้วย id เดิม — บุ๊กมาร์กเก่าไปยังสัญญาใบหนึ่งเปิดสัญญาใบนั้นเป๊ะ |

ทั้งสามตัวใช้ `replace: true` จึงไม่เพิ่ม entry ใน browser history ให้ปุ่ม Back ไปลงจอด `/licenses/subscriptions/...` คือ path หลัก; ผู้ทดสอบควรมองว่า path เก่า "ยังใช้ได้" ไม่ใช่ "path ที่ควรใช้ตอนนี้" — ไม่มีอะไรใน SPA ลิงก์ไปที่ `/subscriptions*` อีกต่อไปแล้ว

## 7. แหล่งข้อมูลอ้างอิง

path ทั้งหมดคือ `../carmen-platform` ยกเว้นที่ระบุไว้เป็นอย่างอื่น

- `src/pages/licenses/LicenseCenter.tsx` — หน้าจอลงจอดสี่แท็บ, แถบ Fleet Capacity, การจำแท็บ
- `src/pages/licenses/ClusterLicenseTable.tsx`, `src/pages/licenses/SubscriptionTable.tsx`, `src/pages/licenses/PurchaseLicenseTable.tsx` — เนื้อหาของสี่แท็บ
- `src/pages/licenses/ClusterLicenseDetail.tsx` — หน้าจอรายละเอียดต่อ cluster และ hook โหลดข้อมูลที่ใช้ร่วมกัน (`useLicenseLedger`, `useClusterSeatLicenses`, `useClusterSubscriptions`)
- `src/pages/licenses/LicenseHealthStrip.tsx`, `src/pages/licenses/LicenseCoverageBar.tsx` — แถบสรุปและภาพเส้นเวลาที่ใช้ร่วมกัน
- `src/pages/licenses/sections/{BuQuotaSection,SeatSection,SubscriptionSection}.tsx` — สามแท็บของ `ClusterLicenseDetail`
- `src/utils/businessUnitRank.ts` — `rankBusinessUnits()`/`countOverLimit()` ตรรกะป้าย Over-limit (§3.2)
- `src/pages/licenses/SubscriptionForm.tsx`, `src/pages/licenses/subscriptionCreate/{SubscriptionCreateForm,SubscriptionDraftPlate,subscriptionTerm}.tsx`, `src/pages/licenses/subscriptionEdit/{IssuedSubscriptionPlate,SubscriptionInfoCard,GroupSelectionCard}.tsx` — ฟอร์ม subscription และ component สนับสนุน
- `src/pages/licenses/LicensePurchaseForm.tsx`, `src/pages/licenses/licenseKindConfig.ts`, `src/pages/licenses/licenseEdit/IssuedLicensePlate.tsx`, `src/pages/licenses/plate/plateParts.tsx` — ฟอร์มซื้อที่ใช้ร่วมกันและ config สลับประเภท
- `src/App.tsx` (บรรทัด 183–249) — ทุก route ที่หน้านี้อธิบาย บวก redirect เก่า (§6)
- `src/hooks/useAllClusters.ts`, `src/hooks/useExpiryThresholds` (`src/context/ExpiryThresholdContext.tsx`) — hook ข้อมูลที่ใช้ร่วมกันข้ามฟอร์ม
- `src/pages/licenses/subscriptionEdit/SeatsCard.tsx` — **ไม่ใช่ส่วนหนึ่งของ UI ที่ใช้งานจริง** การ์ด seat-pool ระดับ cluster ที่มีอยู่ใน source และมี test file ของตัวเอง แต่ไม่ถูก import โดย production page component ตัวไหนเลย (`SubscriptionForm.tsx` ไม่ render การ์ดแบบนี้เลย); คอมเมนต์ใน test file ของมันเองอ้างว่า "ยังใช้ที่ License Center" ซึ่งล้าสมัยเทียบกับ source ปัจจุบัน — ยืนยันด้วยการ grep ทั้ง repo แล้วเจอ import ที่ไม่ใช่ test เป็นศูนย์ ไม่ถูกบันทึกเป็นหน้าจอด้านบนเพราะไม่มี route ไหนพาไปถึงมันได้เลย

**ลิงก์ข้าม:** [หน้าลงจอด Licenses](/th/platform/licenses) &nbsp;·&nbsp; [Data Model](/th/platform/licenses/data-model) &nbsp;·&nbsp; [Permissions](/th/platform/licenses/permissions)
