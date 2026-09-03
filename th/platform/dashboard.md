---
title: Dashboard
description: หน้า home hub สำหรับผู้ใช้ที่ signed-in (/dashboard) — activity stream รวมทั่ว 6 โดเมน บวกแถบสรุปจำนวน active/total ต่อโดเมนแบบ sticky ไม่มี requiredPermission ของตัวเอง ทุกโดเมนจะหลุดจากทั้งสองส่วนแบบเงียบ ๆ ถ้า session อ่านไม่ได้
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/dashboard, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Dashboard

> **At a Glance**
> **หน้าจอ:** `Dashboard` (`/dashboard`) &nbsp;·&nbsp; **การเข้าถึง:** authenticated เท่านั้น — route ไม่มี `requiredPermission` เหมือนกับ [Profile](/th/platform/profile) &nbsp;·&nbsp; **Sidebar:** รายการ nav บนสุด (ไม่ถูก gate อยู่เหนือกลุ่ม Organization/Content/Platform) &nbsp;·&nbsp; **เนื้อหา:** activity stream รวมทั่ว 6 โดเมน + แถบสรุป active/total แบบ sticky &nbsp;·&nbsp; **เข้าถึงจาก:** redirect หลัง login (จาก [Landing](/th/platform/landing) หรือ Login), สัญลักษณ์แบรนด์ใน sidebar, หรือรายการ nav "Dashboard" เอง

## 1. ภาพรวม

Dashboard คือหน้าจอแรกที่ session ที่ signed-in ไปถึง: ทั้ง [Landing](/th/platform/landing) และหน้า Login จะ redirect session ที่ authenticated อยู่แล้วไปยัง `/dashboard` ทันที และสัญลักษณ์แบรนด์ของ sidebar (โลโก้ + wordmark "Carmen Platform") ลิงก์มาที่นี่จากทุกที่ในแอป ต่างจากทุกหน้าจอโมดูลที่บันทึกไว้ในที่อื่นของ book นี้ Dashboard อ่านข้าม module แทนที่จะเป็นเจ้าของ module ใดโมดูลหนึ่ง — หน้าที่ทั้งหมดของมันคือตอบคำถาม "อะไรเปลี่ยนไปบ้าง และ estate ของฉันใหญ่แค่ไหน" โดยไม่ต้อง navigate ไปไหนเลย

หน้านี้มีสองส่วนที่เป็นอิสระจากกัน: **Activity Stream** ทางซ้าย (timeline รวม, filter ได้, จัดกลุ่มตามวัน ของ event ล่าสุด create/update/publish ทั่ว 6 โดเมน) และ **Counts Rail** ทางขวา (การ์ดสรุปแบบ sticky แสดงยอดรวม "Estate" บวกจำนวน active/total ของแต่ละโดเมน แต่ละแถวลิงก์ตรงไปหน้ารายการของโดเมนนั้น) ทั้งสองส่วนโหลดอิสระต่อกันและ fail อิสระต่อกัน — โดเมนที่ช้าหรือ error ไม่บล็อกอีกส่วนหรือโดเมนอื่นภายในส่วนของตัวเอง

## 2. Activity Stream

หกโดเมนป้อนเข้า stream ตามลำดับตายตัวนี้: **Clusters, Business Units, Users, Applications, News, Report Templates** สำหรับแต่ละโดเมน หน้านี้ fetch 8 record ที่ update ล่าสุดที่ไม่ถูกลบ (`sort: 'updated_at:desc'`, `perpage: 8`) ผ่านการเรียก service `getAll` ของโดเมนนั้นเอง — การเรียกเดียวกับที่หน้ารายการของโดเมนนั้นใช้ ไม่ใช่ endpoint activity เฉพาะ ทั้งหกการเรียกทำงานพร้อมกันผ่าน `Promise.allSettled`; **โดเมนที่ fetch ล้มเหลวจะถูกตัดออกจาก stream แบบเงียบ ๆ** แทนที่จะแสดง error สำหรับโดเมนนั้น (ดู §4 ว่านี่หมายถึงอะไรสำหรับ session สิทธิ์ต่ำ) ทุก record ที่ได้กลับมาจะถูก normalize (รองรับทั้งรูปแบบ flat `updated_at`/`updated_by_name` และรูปแบบ nested `audit.updated.{at,name}` ของ API), จัดประเภทเป็น **created** (`created_at` กับ timestamp "at" ที่ได้ผลเท่ากัน), **updated** (ต่างกัน), หรือ **published** (เฉพาะโดเมน News เมื่อ `status === 'published'` แทนที่การอนุมาน created/updated) — จากนั้น item ของทุกโดเมนจะถูก merge เรียงจากใหม่ไปเก่า และ cap ที่ 15 รายการรวม

Timeline ที่ render จัดกลุ่มตามวัน (แถว header วันแบบ sticky) และแต่ละแถวแสดงจุดสีตาม verb (เขียว = created, น้ำเงิน = updated, เหลือง = published), timestamp แบบสัมพัทธ์/นาฬิกา, ชื่อ record (บวก code ถ้าโดเมนมี), label โดเมน, และ — เมื่อทราบ — ใครเป็นคนแก้ไข ทั้งแถวลิงก์ไปหน้า edit ของ record นั้น แถวของ filter chip ("All" บวกหนึ่งอันต่อโดเมน แต่ละอันแสดงจำนวนของโดเมนนั้นภายในหน้าต่าง 15 รายการปัจจุบัน) ให้ผู้ดูจำกัด timeline ให้เหลือโดเมนเดียวได้ฝั่ง client มีสามสถานะนอกเหนือจาก timeline ที่มีข้อมูล: skeleton 5 แถวระหว่างโหลด, `FetchErrorState` พร้อมปุ่ม Retry ถ้าทุกโดเมน fetch ล้มเหลวจริง ๆ (ไม่ใช่แค่ merge ได้ผลว่าง) และข้อความ empty-state ("Nothing changed here yet…") เมื่อ merge ว่างเปล่าแต่ไม่มี error เกิดขึ้น

## 3. Counts Rail

หกโดเมนเดียวกัน (ลำดับเดียวกัน) แต่ละอันมีส่วนร่วมด้วยจำนวน **active** และจำนวน **total** คำนวณจากการเรียก `getAll` สองครั้งต่อโดเมน (`perpage: 1`) พร้อม filter `advance` — หนึ่งแบบไม่ filter (แต่ไม่รวมที่ถูกลบ) หนึ่งแบบ filter เพิ่มด้วย predicate "active" ของโดเมนนั้นเอง: `is_active: true` สำหรับ Clusters/Business Units/Users/Applications/Report Templates, `status: 'published'` สำหรับ News header ของ rail แสดงตัวเลข "Estate" เดียว — ผลรวมของจำนวน **total** ทั้งหกโดเมน (นับเฉพาะโดเมนที่ resolve สำเร็จ) มี label ว่า "records governed" ด้านล่างมีหนึ่งแถวต่อโดเมนแสดง `active / total` แบบ monospace แต่ละแถวลิงก์ไปหน้ารายการของโดเมนนั้น ถ้าโดเมน**ใดก็ตาม**ล้มเหลวในคู่การเรียกนับจำนวน rail ทั้งหมด (ไม่ใช่แค่แถวนั้น) จะเปลี่ยนเป็น `FetchErrorState` พร้อมปุ่ม Retry — โหมดล้มเหลวที่เข้มงวดกว่า Activity Stream ซึ่งตัดออกเฉพาะโดเมนที่ล้มเหลว

## 4. สิ่งที่ไม่มีบน Dashboard

ที่ขาดหายไปอย่างชัดเจนจากทั้งสองส่วน จากการเทียบตรงกับรายการโมดูลของ sidebar เอง (`Layout.tsx`): **Broadcasts** (ไม่มี endpoint list — เป็นหน้าจอ compose แบบ fire-and-forget ไม่มีอะไรให้นับหรือแสดงเป็น "ล่าสุด"), **Platform RBAC / Roles / Super Admins / User Platform**, **Tenant Migrations**, **SQL Workbench**, และ **Report Form Groups** (มุมมองหนึ่งของ Report Templates ไม่ใช่โดเมนของตัวเอง) ไม่มีข้อใดในหกอย่างนี้ปรากฏที่ Activity Stream หรือ Counts Rail เลย — การเปลี่ยน role, การให้สิทธิ์ super-admin, tenant migration, หรือ default ของ form-group จะไม่ปรากฏบนหน้านี้ไม่ว่าจะเพิ่งเกิดขึ้นแค่ไหนก็ตาม

## 5. บทบาทและ Persona

route `/dashboard` ถูกห่อด้วย `<PrivateRoute>` เปล่า ๆ ไม่มี prop `requiredPermission` — การ authenticate เป็น gate เดียว เหมือนกับ [Profile](/th/platform/profile) ไม่มี gate `<Can>` ใด ๆ ภายในหน้านี้เลย การควบคุมการเข้าถึงที่แท้จริงเป็นแบบทางอ้อม: การเรียก `getAll` ทั้งหกครั้งข้างต้นยังผ่านการตรวจสอบ permission ฝั่ง backend ของโดเมนนั้นเองอยู่ ดังนั้น session ที่ขาด (ตัวอย่างเช่น) `report_template.read` จะทำให้การ fetch Report Templates ล้มเหลวที่ API และโดเมนนั้นก็จะหายไปจากทั้งสองส่วนเฉย ๆ (§2/§3) — Dashboard เองไม่ได้เช็ค `hasPermission` สำหรับโดเมนใดเลย มันสืบทอดสิ่งที่ endpoint list ของโดเมนนั้นบังคับใช้อยู่แล้ว ทีละ request ที่ล้มเหลว

## 6. โมดูลที่เกี่ยวข้อง

- [Landing](/th/platform/landing) — หน้าสาธารณะที่ redirect session ที่ authenticated แล้วมาที่นี่ทันที; ยังเป็นหน้าที่ดัชนี "Inside the console" แบบ hardcode ของตัวเองควรจะแสดงโมดูลเดียวกับที่ sidebar แสดง (ดู Overview ของหน้านั้นสำหรับความคลาดเคลื่อนที่ยืนยันแล้วระหว่างสองสิ่งนี้)
- [Profile](/th/platform/profile) — อีก route หนึ่งที่ gate ด้วย `<PrivateRoute>` เปล่า ๆ ไม่มีข้อกำหนด permission
- [Clusters](/th/platform/clusters), [Business Units](/th/platform/business-units), [Users](/th/platform/users), [Applications](/th/platform/applications), [News](/th/platform/news), [Report Templates](/th/platform/report-templates) — หกโดเมนที่ Activity Stream และ Counts Rail อ่านข้อมูลมา

## 7. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/Dashboard.tsx` — หน้า: การโหลด count และ activity แบบขนาน, layout
- `../carmen-platform/src/pages/dashboard/activity.ts` — `ACTIVITY_SOURCES` (หกโดเมนตามลำดับที่แสดง), `fetchActivity`, `toActivityItem`, `deriveVerb`, `mergeAndSort`
- `../carmen-platform/src/pages/dashboard/ActivityStream.tsx` — filter chip, การจัดกลุ่มตามวัน, การ render timeline, state loading/error/empty
- `../carmen-platform/src/pages/dashboard/CountsRail.tsx` — ยอดรวม Estate และแถว active/total ต่อโดเมน
- `../carmen-platform/src/App.tsx:64` (`<PrivateRoute>` เปล่า ๆ บน `/dashboard`); `src/components/Layout.tsx:51` — รายการ nav บนสุด "Dashboard" ที่ไม่ถูก gate และลิงก์สัญลักษณ์แบรนด์ที่ `Layout.tsx:149`

## 8. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดียว ดู [ดัชนี Platform book](/th/platform)
