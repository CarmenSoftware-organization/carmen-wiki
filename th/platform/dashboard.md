---
title: Dashboard
description: หน้า home hub สำหรับผู้ใช้ที่ signed-in (/dashboard) — activity stream รวมทั่ว 6 โดเมน บวกแถบสรุปจำนวน active/total ต่อโดเมนแบบ sticky ไม่มี requiredPermission ของตัวเอง ทุกโดเมนจะหลุดจากทั้งสองส่วนแบบเงียบ ๆ ถ้า session อ่านไม่ได้
published: true
date: 2026-09-06T00:00:00.000Z
tags: platform/dashboard, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Dashboard

> **At a Glance**
> **หน้าจอ:** `Dashboard` (`/dashboard`) &nbsp;·&nbsp; **การเข้าถึง:** authenticated เท่านั้น — route ไม่มี `requiredPermission` **และไม่มีคีย์ `feature`** (แถว nav เดียวใน `platformNav.ts` ที่ไม่มีทั้งสอง) เหมือนกับ [Profile](/th/platform/profile) จึงเห็นได้/เข้าถึงได้เสมอไม่ว่าจะมีสิทธิ์หรือสถานะ feature-flag อย่างไร &nbsp;·&nbsp; **Sidebar:** รายการ nav บนสุด ไม่ถูก gate อยู่เหนือทุกกลุ่ม `groupKey` (Organization, License Management, Content, Analytics, Scheduling, Platform, Database — ดู §4) &nbsp;·&nbsp; **เนื้อหา:** activity stream รวมทั่ว 6 โดเมน + แถบสรุป active/total แบบ sticky &nbsp;·&nbsp; **เข้าถึงจาก:** redirect หลัง login (จาก [Landing](/th/platform/landing) หรือ Login), สัญลักษณ์แบรนด์ใน sidebar, หรือรายการ nav "Dashboard" เอง — แม้ว่า cluster admin แบบ membership-only ที่มาถึงหน้านี้จะถูกส่งต่อไปที่ `/cluster-admin` ทันที (§5)

## 1. ภาพรวม

Dashboard คือหน้าจอแรกที่ session ที่มี platform authority และ signed-in ไปถึง: ทั้ง [Landing](/th/platform/landing) และหน้า Login จะ redirect session ที่ authenticated อยู่แล้วไปยัง `/dashboard` แบบไม่มีเงื่อนไข และ — สำหรับ session ที่มี platform authority — สัญลักษณ์แบรนด์ของ sidebar (โลโก้ + wordmark "Carmen Platform") ลิงก์กลับมาที่นี่จากทุกที่ในแอป สัญลักษณ์แบรนด์ของ cluster admin แบบ membership-only กลับชี้ไปที่หน้าคลัสเตอร์ของตัวเอง (`/cluster-admin/:clusterId/cluster`) แทน และ `PrivateRoute` จะส่ง session เดียวกันนั้นไปที่ `/cluster-admin` ทันทีถ้ามาถึง `/dashboard` ไม่ว่าจะมาทางไหน (§5) — การ redirect จาก Landing/Login ไม่มีเงื่อนไขก็จริง แต่การมาถึงที่นี่ไม่ใช่จุดจบของเรื่องสำหรับทุก session ต่างจากทุกหน้าจอโมดูลที่บันทึกไว้ในที่อื่นของ book นี้ Dashboard อ่านข้าม module แทนที่จะเป็นเจ้าของ module ใดโมดูลหนึ่ง — หน้าที่ทั้งหมดของมันคือตอบคำถาม "อะไรเปลี่ยนไปบ้าง และ estate ของฉันใหญ่แค่ไหน" โดยไม่ต้อง navigate ไปไหนเลย

หน้านี้มีสองส่วนที่เป็นอิสระจากกัน: **Activity Stream** ทางซ้าย (timeline รวม, filter ได้, จัดกลุ่มตามวัน ของ event ล่าสุด create/update/publish ทั่ว 6 โดเมน) และ **Counts Rail** ทางขวา (การ์ดสรุปแบบ sticky แสดงยอดรวม "Estate" บวกจำนวน active/total ของแต่ละโดเมน แต่ละแถวลิงก์ตรงไปหน้ารายการของโดเมนนั้น) ทั้งสองส่วนโหลดอิสระต่อกันและ fail อิสระต่อกัน — โดเมนที่ช้าหรือ error ไม่บล็อกอีกส่วนหรือโดเมนอื่นภายในส่วนของตัวเอง

## 2. Activity Stream

หกโดเมนป้อนเข้า stream ตามลำดับตายตัวนี้: **Clusters, Business Units, Users, Applications, News, Report Templates** สำหรับแต่ละโดเมน หน้านี้ fetch 8 record ที่ update ล่าสุดที่ไม่ถูกลบ (`sort: 'updated_at:desc'`, `perpage: 8`) ผ่านการเรียก service `getAll` ของโดเมนนั้นเอง — การเรียกเดียวกับที่หน้ารายการของโดเมนนั้นใช้ ไม่ใช่ endpoint activity เฉพาะ ทั้งหกการเรียกทำงานพร้อมกันผ่าน `Promise.allSettled`; **โดเมนที่ fetch ล้มเหลวจะถูกตัดออกจาก stream แบบเงียบ ๆ** แทนที่จะแสดง error สำหรับโดเมนนั้น (ดู §4 ว่านี่หมายถึงอะไรสำหรับ session สิทธิ์ต่ำ) ทุก record ที่ได้กลับมาจะถูก normalize (รองรับทั้งรูปแบบ flat `updated_at`/`updated_by_name` และรูปแบบ nested `audit.updated.{at,name}` ของ API), จัดประเภทเป็น **created** (`created_at` กับ timestamp "at" ที่ได้ผลเท่ากัน), **updated** (ต่างกัน), หรือ **published** (เฉพาะโดเมน News เมื่อ `status === 'published'` แทนที่การอนุมาน created/updated) — จากนั้น item ของทุกโดเมนจะถูก merge เรียงจากใหม่ไปเก่า และ cap ที่ 15 รายการรวม

Timeline ที่ render จัดกลุ่มตามวัน (แถว header วันแบบ sticky) และแต่ละแถวแสดงจุดสีตาม verb (เขียว = created, น้ำเงิน = updated, เหลือง = published), timestamp แบบสัมพัทธ์/นาฬิกา, ชื่อ record (บวก code ถ้าโดเมนมี), label โดเมน, และ — เมื่อทราบ — ใครเป็นคนแก้ไข ทั้งแถวลิงก์ไปหน้า edit ของ record นั้น แถวของ filter chip ("All" บวกหนึ่งอันต่อโดเมน แต่ละอันแสดงจำนวนของโดเมนนั้นภายในหน้าต่าง 15 รายการปัจจุบัน) ให้ผู้ดูจำกัด timeline ให้เหลือโดเมนเดียวได้ฝั่ง client มีสามสถานะนอกเหนือจาก timeline ที่มีข้อมูล: skeleton 5 แถวระหว่างโหลด, ข้อความ empty-state ("Nothing changed here yet…") เมื่อ merge ว่างเปล่า, และ `FetchErrorState` พร้อมปุ่ม Retry — แต่สถานะ error นี้ไปไม่ถึงได้ด้วยความล้มเหลวระดับโดเมนเดียว `fetchActivity()` fetch ทั้งหกโดเมนผ่าน `Promise.allSettled` ซึ่งไม่มีวัน reject; โดเมนที่ request ล้มเหลวจะถูกตัดออกจาก merge เฉย ๆ (ตามย่อหน้าข้างต้น) ดังนั้น **แม้ทุกโดเมนทั้งหกจะล้มเหลวหมด มันก็ยัง resolve สำเร็จด้วย array ว่าง** และ render empty state "Nothing changed here yet…" เดียวกันกับหกโดเมนที่เงียบจริง ๆ — สองกรณีนี้แยกไม่ออกด้วยตา เส้นทาง `FetchErrorState`/Retry เฉพาะทางมีไว้สำหรับความล้มเหลวใน `fetchActivity()` เอง (สิ่งที่ throw นอกเหนือจากการเรียก `Promise.allSettled` ต่อโดเมน) ไม่ใช่สำหรับโดเมนที่มัน fetch

## 3. Counts Rail

หกโดเมนเดียวกัน (ลำดับเดียวกัน) แต่ละอันมีส่วนร่วมด้วยจำนวน **active** และจำนวน **total** คำนวณจากการเรียก `getAll` สองครั้งต่อโดเมน (`perpage: 1`) พร้อม filter `advance` — หนึ่งแบบไม่ filter (แต่ไม่รวมที่ถูกลบ) หนึ่งแบบ filter เพิ่มด้วย predicate "active" ของโดเมนนั้นเอง: `is_active: true` สำหรับ Clusters/Business Units/Users/Applications/Report Templates, `status: 'published'` สำหรับ News header ของ rail แสดงตัวเลข "Estate" เดียว — ผลรวมของจำนวน **total** ทั้งหกโดเมน (นับเฉพาะโดเมนที่ resolve สำเร็จ) มี label ว่า "records governed" ด้านล่างมีหนึ่งแถวต่อโดเมนแสดง `active / total` แบบ monospace แต่ละแถวลิงก์ไปหน้ารายการของโดเมนนั้น ถ้าโดเมน**ใดก็ตาม**ล้มเหลวในคู่การเรียกนับจำนวน rail ทั้งหมด (ไม่ใช่แค่แถวนั้น) จะเปลี่ยนเป็น `FetchErrorState` พร้อมปุ่ม Retry — โหมดล้มเหลวที่เข้มงวดกว่า Activity Stream ซึ่งตัดออกเฉพาะโดเมนที่ล้มเหลว

## 4. สิ่งที่ไม่มีบน Dashboard

`ACTIVITY_SOURCES` (หกโดเมนที่ระบุใน §2) ไม่ได้เพิ่มขึ้นเลยตั้งแต่โมดูลนี้ถูกสร้าง — ทุกแถวอื่นในรายการ navigation จริงของ sidebar คือ `ALL_PLATFORM_NAV_ITEMS` ใน `platformNav.ts` ขาดหายจากทั้งสองส่วนหมด รายการนั้นเติบโตขึ้นมากตั้งแต่หน้านี้ sync ครั้งล่าสุด (หลายแถวด้านล่างเป็นโมดูลที่เพิ่มหลัง 2026-07-29) ช่องว่างจึงกว้างกว่าที่อ่านจากหน้านี้ครั้งแรก:

| `groupKey` | รายการ sidebar ที่ไม่มีบน Dashboard |
|---|---|
| `navGroup.organization` | Tenant Migrations, Tenant Imports (อีกสามแถวในกลุ่มนี้ — Clusters, Business Units, Users — *มี* ครอบคลุมแล้ว) |
| `navGroup.licenseManagement` | Licenses, License Feature Groups, License Features — ทั้งกลุ่ม |
| `navGroup.content` | Report Form Groups, Broadcasts (Report Templates และ News อีกสองแถวของกลุ่ม *มี* ครอบคลุมแล้ว) |
| `navGroup.analytics` | Usage Analytics, Activity Events — ทั้งกลุ่ม |
| `navGroup.scheduling` | Cronjobs — ทั้งกลุ่ม |
| `navGroup.platform` | Platform Config, Email Settings, Platform Roles, User Platform, Super Admins, Feature Flags (Applications อีกแถวของกลุ่ม *มี* ครอบคลุมแล้ว) |
| `navGroup.database` | Platform Migrations, SQL Workbench, Database Pools — ทั้งกลุ่ม |

นอกเหนือจากนี้ยังมี persona **cluster-admin** (`/cluster-admin/...`) ที่ Dashboard เข้าไม่ถึงเลย เพราะไม่ได้อยู่ใน `ALL_PLATFORM_NAV_ITEMS` เลยด้วยซ้ำ และไม่มีหน้า landing แบบ Dashboard เป็นของตัวเอง

Broadcasts เป็นกรณีพิเศษแม้ในบรรดารายการที่ขาดหายไป: มันไม่มี endpoint list เลย (เป็นหน้าจอ compose แบบ fire-and-forget ที่มีพื้นผิว list/edit สำหรับแอดมินแยกต่างหากซึ่งเพิ่มเข้ามาหลังจากหน้านี้ sync ครั้งล่าสุด — ดู [Broadcasts](/th/platform/broadcasts)) จึงไม่สามารถเพิ่มเข้า `ACTIVITY_SOURCES` ได้โดยไม่มี schema ที่โดเมนนี้ไม่ได้ expose ออกมา Report Form Groups เป็นมุมมองหนึ่งของทรัพยากร Report Templates มาตั้งแต่แรก ไม่ใช่โดเมนของตัวเอง การขาดหายจึงเป็นการออกแบบ ไม่ใช่ช่องว่าง ไม่มีข้อใดในรายการเหล่านี้ปรากฏที่ Activity Stream หรือ Counts Rail เลย — การเปลี่ยน role, การให้สิทธิ์ super-admin, tenant migration, cronjob หรือ default ของ form-group จะไม่ปรากฏบนหน้านี้ไม่ว่าจะเพิ่งเกิดขึ้นแค่ไหนก็ตาม

## 5. บทบาทและ Persona

route `/dashboard` ถูกห่อด้วย `<PrivateRoute>` เปล่า ๆ ไม่มี prop `requiredPermission` และไม่มี prop `feature` — การห่อแบบเปล่า ๆ เดียวกับที่ route `/profile` ฝั่ง platform ของ [Profile](/th/platform/profile) ได้รับ "การ authenticate เป็น gate เดียว" ไม่ใช่เรื่องทั้งหมด: `PrivateRoute` (`src/components/PrivateRoute.tsx`) มี branch การตัดสินใจ platform-authority/cluster-admin ที่ทำงานทุก route ที่มันคุม ไม่ว่าจะ gate หรือไม่ก็ตาม เมื่อ `effectivePermissions` resolve แล้ว session ที่ไม่มี platform authority จะไม่ถูก render ที่นี่เลย — ถ้ามี cluster-admin scope อย่างน้อยหนึ่งคลัสเตอร์ (`hasClusterAdminScope`) จะถูก redirect ไป `/cluster-admin` แทน (`PrivateRoute.tsx:72-73`); session ที่ไม่มีทั้ง platform authority และ cluster-admin scope จะ fall through และยัง render หน้านี้อยู่ดี ซึ่งเป็นข้อยกเว้นที่ตั้งใจไว้เพื่อไม่ให้แอดมินคนแรก (bootstrap) ของการติดตั้งใหม่ถูกล็อกออกจาก `/dashboard` ระหว่างที่การตรวจนับ super-admin ของตัวเองยังทำงานไม่เสร็จ กล่าวอีกอย่างคือ: การมาถึง `/dashboard` ได้เลยก็หมายความแล้วว่ามี platform authority (หรืออยู่ในช่วง bootstrap แคบ ๆ นั้น) — cluster admin แบบ membership-only จะไม่มีวันเห็นหน้านี้เลย เพราะถูก guard ส่งออกไปเอง ไม่ใช่เพราะ Dashboard เช็คอะไร ไม่มี gate `<Can>` ใด ๆ ภายในหน้านี้เลย นอกเหนือจาก guard นั้น การเข้าถึงเนื้อหาของแต่ละส่วนเป็นแบบทางอ้อม: การเรียก `getAll` ทั้งหกครั้งข้างต้นยังผ่านการตรวจสอบ permission ฝั่ง backend ของโดเมนนั้นเองอยู่ ดังนั้น session ที่ขาด (ตัวอย่างเช่น) `report_template.read` จะทำให้การ fetch Report Templates ล้มเหลวที่ API และโดเมนนั้นก็จะหายไปจากทั้งสองส่วนเฉย ๆ (§2/§3) — Dashboard เองไม่ได้เช็ค `hasPermission` สำหรับโดเมนใดเลย มันสืบทอดสิ่งที่ endpoint list ของโดเมนนั้นบังคับใช้อยู่แล้ว ทีละ request ที่ล้มเหลว

## 6. โมดูลที่เกี่ยวข้อง

- [Landing](/th/platform/landing) — หน้าสาธารณะที่ redirect session ที่ authenticated แล้วมาที่นี่ทันที; ยังเป็นหน้าที่ดัชนี "Inside the console" แบบ hardcode ของตัวเองควรจะแสดงโมดูลเดียวกับที่ sidebar แสดง (ดู Overview ของหน้านั้นสำหรับความคลาดเคลื่อนที่ยืนยันแล้วระหว่างสองสิ่งนี้)
- [Profile](/th/platform/profile) — อีก route หนึ่งที่ gate ด้วย `<PrivateRoute>` เปล่า ๆ ไม่มีข้อกำหนด permission และ component เดียวที่เข้าถึงได้ทั้งจากฝั่ง platform และ persona cluster-admin แยกต่างหากที่อธิบายด้านล่าง
- [Clusters](/th/platform/clusters), [Business Units](/th/platform/business-units), [Users](/th/platform/users), [Applications](/th/platform/applications), [News](/th/platform/news), [Report Templates](/th/platform/report-templates) — หกโดเมนที่ Activity Stream และ Counts Rail อ่านข้อมูลมา
- Cluster Admin (`/cluster-admin/...`) — persona แยกต่างหากที่ไม่มี dashboard ของตัวเอง ซึ่ง cluster admin แบบ membership-only ถูก redirect เข้าไปแทนหน้านี้ (§5) ยังไม่เป็นโมดูล wiki ของตัวเอง ณ รอบนี้

## 7. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/Dashboard.tsx` — หน้า: การโหลด count และ activity แบบขนาน, layout
- `../carmen-platform/src/pages/dashboard/activity.ts` — `ACTIVITY_SOURCES` (หกโดเมนตามลำดับที่แสดง), `fetchActivity`, `toActivityItem`, `deriveVerb`, `mergeAndSort`
- `../carmen-platform/src/pages/dashboard/ActivityStream.tsx` — filter chip, การจัดกลุ่มตามวัน, การ render timeline, state loading/error/empty
- `../carmen-platform/src/pages/dashboard/CountsRail.tsx` — ยอดรวม Estate และแถว active/total ต่อโดเมน
- `../carmen-platform/src/App.tsx:103-109` — `<PrivateRoute>` เปล่า ๆ (ไม่มี `requiredPermission`, ไม่มี `feature`) บน `/dashboard`
- `../carmen-platform/src/components/PrivateRoute.tsx:66-84` — branch การตัดสินใจ platform-authority/cluster-admin ที่อธิบายใน §5 (`effectivePermissions`, `hasClusterAdminScope`, การ redirect ไป `/cluster-admin`, และ fall-through ของแอดมิน bootstrap)
- `../carmen-platform/src/components/nav/platformNav.ts` — `ALL_PLATFORM_NAV_ITEMS` รายการ sidebar จริงที่ §4 ใช้เทียบ แถว `/dashboard` ที่ไม่ถูก gate และไม่มี feature อยู่นอกทุกกลุ่ม `groupKey` `Layout.tsx` เองไม่ได้กำหนดแถว nav แล้ว — มันแค่เรียก `buildPlatformNav()` (`Layout.tsx:107`) และคำนวณปลายทางของสัญลักษณ์แบรนด์ (`Layout.tsx:111`, `hasPlatformAuthority ? '/dashboard' : '/cluster-admin'` — ดังนั้นกรอบ "เข้าถึงได้จากทุกที่" ใน §1 จะเป็นจริงเฉพาะ session ที่มี platform authority)

## 8. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดียว ดู [ดัชนี Platform book](/th/platform)
