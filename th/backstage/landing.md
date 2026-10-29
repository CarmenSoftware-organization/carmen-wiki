---
title: Landing
description: หน้าการตลาดสาธารณะที่ / — redirect session ที่ authenticated แล้วไปยัง Dashboard และแสดงดัชนีโมดูล "Inside the console" แบบ hardcode ที่คลาดเคลื่อนจาก sidebar จริง
published: true
date: 2026-10-29T05:30:00.000Z
tags: backstage/landing, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Landing

> **At a Glance**
> **หน้าจอ:** `Landing` (`/`) &nbsp;·&nbsp; **การเข้าถึง:** สาธารณะเต็มรูปแบบ — route ไม่มี wrapper `<PrivateRoute>` เลย แม้แต่แบบ authenticated-only เปล่า ๆ ที่ [Dashboard](/th/backstage/dashboard) และ [Profile](/th/backstage/profile) ใช้ &nbsp;·&nbsp; **พฤติกรรม:** redirect session ที่ authenticated แล้วไปยัง `/dashboard` แบบไม่มีเงื่อนไข — route guard ของ [Dashboard](/th/backstage/dashboard) เองเป็นผู้ตัดสินใจต่อว่า session นั้นควรอยู่ที่นั่นจริงหรือไม่ (§4) &nbsp;·&nbsp; **เนื้อหา:** hero + CTA sign-in + ดัชนีโมดูล "Inside the console" แบบ hardcode สามกลุ่ม + footer version-stamp &nbsp;·&nbsp; **ความคลาดเคลื่อนที่ยืนยันแล้ว:** แถว Print Mapping ที่ตายแล้วถูกถอดออกในที่สุดเมื่อ 2026-09-07 แต่ดัชนีโมดูลยังขาดแถวจริงส่วนใหญ่ของ sidebar อยู่ (§4)

## 1. ภาพรวม

Landing คือจุดเริ่มต้นสำหรับผู้ที่ signed-out ที่ `/` — หน้าการตลาดแบบ static หน้าเดียวที่ไม่มีการ fetch ข้อมูลของตัวเอง `<Route path="/" element={<Landing />} />` ใน `App.tsx` ไม่มี wrapper `<PrivateRoute>` เลย ต่างจากทุก route อื่นใน book นี้ route เดียวที่ไม่ถูก guard เท่านี้คือ `/login` และ `/changelog` ผู้เยี่ยมชมที่ authenticated อยู่แล้วจะไม่เห็นเนื้อหาการตลาดจริง ๆ เลย: `useEffect` ตรวจสอบ `isAuthenticated` แล้ว `navigate('/dashboard', { replace: true })` ออกไปทันที — pattern เดียวกับที่ `Login.tsx` ใช้ด้วยเหตุผลเดียวกัน ระหว่างที่ `AuthContext` ยัง resolve ไม่เสร็จ (`loading === true`) หน้านี้จะแสดงสัญลักษณ์ "C" ตรงกลาง, spinner, และ "Loading…" แทน — ดังนั้นผู้เยี่ยมชมที่ signed-in กลับมาโดยทั่วไปจะเห็น loading กระพริบสั้น ๆ แล้วไปที่ Dashboard ไม่เห็น hero ด้านล่างเลย การ redirect นี้ตั้งใจให้ไม่มีเงื่อนไขและไม่แยกแยะเองว่า session เป็น Backstage authority หรือ cluster admin แบบ membership-only: ตาม doc comment ของ `PrivateRoute` เอง "จุดเข้าอย่าง Login กับ Landing ทำแบบนั้นไม่ได้ — มันอ่านค่า context แบบ snapshot ก่อน login…เลยส่งทุกคนไป `/dashboard` แล้วให้ guard นี้จัดการคนที่ไม่ควรอยู่ตรงนั้น" — cluster admin แบบ membership-only จะถูกส่งต่อจาก `/dashboard` ไป `/cluster-admin` โดย route guard ของ [Dashboard](/th/backstage/dashboard) เองในอีกไม่กี่ขณะถัดมา ไม่ใช่สิ่งที่ Landing ตัดสินใจ

## 2. เนื้อหาของหน้า

สำหรับผู้เยี่ยมชมที่ signed-out จริง ๆ หน้านี้ render:

- **Header** — สัญลักษณ์ "C" + wordmark "Carmen Blue Backstage / Operations console" และปุ่ม **Sign in** ที่ลิงก์ไป `/login`
- **Hero** — หัวข้อชิดซ้าย ("Run the whole operation from one console.") ข้อความวางตำแหน่งหนึ่งประโยค ปุ่ม call-to-action **Sign in** และลิงก์ข้อความ **"See what's new"** ไป `/changelog` (อีก route สาธารณะเต็มรูปแบบเดียว บันทึกไว้ในหน้าของตัวเอง — [Changelog](/th/backstage/changelog))
- **ดัชนีโมดูล "Inside the console"** — สามกลุ่มของรายการที่ตั้งชื่อ render เป็น list สามคอลัมน์ธรรมดา (ไม่มีลิงก์ — แต่ละรายการเป็นข้อความเฉย ๆ ไม่ใช่ tile ที่ navigate ได้) ดู §3 สำหรับเนื้อหาที่แน่นอนและ §4 สำหรับการเทียบกับ sidebar จริง
- **Footer** — `VersionStamp` ที่ใช้ร่วมกัน (component เดียวกับที่ footer ของ sidebar และหน้า Login ใช้ ตั้งแต่ `918a3b8a`, 2026-10-07): เวอร์ชันแอป `v<CURRENT_VERSION>` ที่ลิงก์ไป `/changelog`, commit SHA ของ build เมื่อตั้ง `REACT_APP_BUILD_SHA`, และเวอร์ชัน API (`API v<version>`) ที่ดึงจาก `GET /version` สาธารณะของ backend ด้วย `fetch` ธรรมดา (ไม่ต้องมี session จึงใช้ได้บนหน้า signed-out นี้) และถูกละไว้เงียบ ๆ เมื่อการเรียกล้มเหลว จากนั้นเป็น label environment แบบ optional (`REACT_APP_ENV`) บรรทัด copyright และ build-date stamp แบบ optional (`REACT_APP_BUILD_DATE`) มันไม่ได้ใช้ `VersionBadge` เป็น component อีกต่อไป — ตอนนี้ `VersionBadge.tsx` export เฉพาะค่าคงที่ `CURRENT_VERSION` และ `BUILD_SHA` ที่ `VersionStamp` อ่าน

## 3. ดัชนี "Inside the Console"

ดัชนีนี้เป็น array แบบ hardcode ใน `Landing.tsx` (`groups`) ไม่ได้มาจาก `NavItem[]` ของ sidebar เองหรือการตรวจสอบ permission ใด ๆ — render เหมือนกันทุกครั้งสำหรับผู้เยี่ยมชมทุกคน ไม่ว่าจะเห็นอะไรจริงหลัง sign in ตามที่เขียนไว้ มันแสดง:

| กลุ่ม | รายการ (ตามที่แสดงบน Landing) |
|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations |
| Content | Report Templates, News, Broadcasts |
| Backstage | Applications, Roles & Access, Super Admins |

## 4. ความคลาดเคลื่อนที่ยืนยันแล้ว: ดัชนี vs. Sidebar จริง

การเทียบตรง ๆ ของ array `groups` ใน `Landing.tsx` กับ `ALL_BACKSTAGE_NAV_ITEMS` — รายการ sidebar จริงใน `src/components/nav/backstageNav.ts` (แหล่งเดียวกับที่ [Business Units](/th/backstage/business-units), [Report Templates](/th/backstage/report-templates), และทุกหน้าโมดูลอื่นใน book นี้อ้างอิงสำหรับรายการ sidebar ของตัวเอง; `Layout.tsx` เองไม่ได้กำหนดแถว nav แล้ว มันแค่เรียก `buildBackstageNav()`) — แสดงว่าดัชนีการตลาดนี้คลาดเคลื่อนไปไกลกว่าตอนที่หน้านี้ทบทวนครั้งล่าสุดมาก sidebar จริงวันนี้มีกลุ่ม `groupKey` **แปด**กลุ่ม (Organization, License Management, Content, Analytics, Scheduling, Backstage, AI, Database ตามลำดับ) บวกแถว Dashboard ที่ไม่ถูก gate; ดัชนี hardcode ของ Landing ยังรู้จักแค่สามกลุ่มเท่านั้น (กลุ่มที่สามตอนนี้ใช้ label "Backstage" ผ่าน `navGroup.backstage`):

| กลุ่ม | ดัชนีของ Landing (ตามที่แสดง) | Sidebar วันนี้ (`backstageNav.ts`) | ช่องว่าง |
|---|---|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations | + Tenant Seed Data, Data Import (แถว Tenant Migrations, Tenant Seed Data และ Data Import ถูกวาดเป็น sub-row ใต้ Business Units) | ขาด 2 จาก 6 |
| License Management | *(ไม่มีกลุ่มนี้บน Landing)* | Licenses, License Feature Groups, License Features | ขาด 3 จาก 3 — ทั้งกลุ่มหายไป |
| Content | Report Templates, News, Broadcasts | Report Templates, Form Groups, Dashboard Templates, News, Broadcasts | ขาด 2 จาก 5 (Form Groups, Dashboard Templates) — แถว Print Mapping ที่ตายแล้วถูกลบออกในที่สุดเมื่อ 2026-09-07 |
| Analytics | *(ไม่มีกลุ่มนี้บน Landing)* | Usage Analytics, Activity Events | ขาด 2 จาก 2 — ทั้งกลุ่มหายไป |
| Scheduling | *(ไม่มีกลุ่มนี้บน Landing)* | Scheduled Jobs | ขาด 1 จาก 1 — ทั้งกลุ่มหายไป |
| Backstage | Applications, Roles & Access, Super Admins | + Backstage Config, Email Settings, Backstage Users (+ Backstage Roles ใน "Roles & Access"), Feature Flags | ขาด 4 จาก 7 |
| AI | *(ไม่มีกลุ่มนี้บน Landing)* | Purchase Request AI Providers | ขาด 1 จาก 1 — ทั้งกลุ่มหายไป |
| Database | *(ไม่มีกลุ่มนี้บน Landing)* | Backstage Migrations, SQL Workbench, Database Pools | ขาด 3 จาก 3 — ทั้งกลุ่มหายไป |

เป็นข้อความ:

- **Print Mapping ไม่อยู่ในรายการอีกต่อไป** — แถวที่ตายแล้วซึ่งหน้านี้เคยชี้ไว้ในการแก้ไขรอบ 2026-09-06 (โมดูล print-template-mapping ถูกลบเมื่อ 2026-07-24, commit `de11377` แต่สำเนา hardcode ของ Landing ยังเก็บรายการไว้) ถูกลบออกจากกลุ่ม Content ของ `Landing.tsx` เมื่อ 2026-09-07 (commit `344be13`, PR #283 ซึ่งลบคีย์ i18n `pages.landing.itemPrintMapping`/`descPrintMapping` ไปด้วย) ตอนนี้ Content แสดงสามรายการ และทุกรายการมีอยู่จริง
- **Form Groups และ Dashboard Templates ขาดหายจาก Content** — Form Groups ออกมาสัปดาห์เดียวกับการลบ Print Mapping (2026-07-24) แต่ PR #283 ลบเฉพาะแถวที่ตายแล้ว ไม่ได้เพิ่มแถวที่ขาดไป ส่วน Dashboard Templates มาทีหลังและก็ไม่มีเช่นกัน
- **กลุ่ม Backstage ขาดไป 4 จาก 7 แถวปัจจุบัน**: Backstage Users (ส่วนหนึ่งของ [Backstage Roles](/th/backstage/rbac)), และอีกสองแถวที่เพิ่มหลังจากหน้านี้ทบทวนครั้งล่าสุด — Backstage Config กับ Email Settings (ทั้งคู่อยู่ `navGroup.backstage`) — บวก Feature Flags ซึ่งแถว nav ของตัวเองมี permission (`feature_flag.manage`) แต่ตั้งใจไม่มีคีย์ `feature` เป็นของตัวเอง ตาม comment ใน `backstageNav.ts`: "สวิตช์ที่ปิดตัวเองได้จะเปิดกลับไม่ได้อีกจากหน้าจอ" ตอนนี้ Feature Flags มีโมดูล wiki ของตัวเองแล้ว — [Feature Flags](/th/backstage/feature-flags)
- **สี่กลุ่มทั้งหมดที่ sidebar ปัจจุบันใช้จัดงาน — License Management, Analytics, Scheduling และ AI — ไม่มีตัวแทนบน Landing เลย** ทั้งหมดเป็นโมดูลที่เพิ่มหลังจากหน้านี้ทบทวนครั้งล่าสุด: Licenses, License Feature Groups, และ License Features (License Management); Usage Analytics และ Activity Events (Analytics); Scheduled Jobs (Scheduling); Purchase Request AI Providers (AI)
- **กลุ่ม Database ก็ขาดหายไปทั้งหมดเช่นกัน**: SQL Workbench, Backstage Migrations และ Database Pools

สิ่งนี้ไม่ส่งผลต่อพฤติกรรมใด ๆ — ดัชนีเป็นข้อความเฉย ๆ ไม่มีลิงก์ อ่านได้เฉพาะผู้เยี่ยมชมที่ signed-out ที่กำลังตัดสินใจว่าจะ sign in หรือไม่ — แต่ผู้อ่านที่ใช้หน้านี้เป็นรายการ feature จะได้ภาพที่ขาดพื้นผิวงานดูแลระบบปัจจุบันไปเกือบครึ่งหนึ่ง นี่คือความคลาดเคลื่อนเชิงเอกสารในสำเนาการตลาดของผลิตภัณฑ์เอง ไม่ใช่ข้อผิดพลาดของ wiki — ระบุไว้ตรงนี้แทนที่จะแก้ไขแบบเงียบ ๆ เพราะการแก้ `Landing.tsx` เองอยู่นอกขอบเขตของ wiki นี้

## 5. บทบาทและ Persona

ไม่ต้อง authenticate และไม่ต้องมี permission grant ใด ๆ เพื่อดูหน้านี้ — เป็นหน้าจอเดียวในผลิตภัณฑ์ที่ browser แบบ anonymous เข้าถึงได้ องค์ประกอบที่โต้ตอบได้มีแค่สองลิงก์ navigation (Sign in → `/login`, See what's new → `/changelog`) ไม่มีอันไหนถูก gate

## 6. โมดูลที่เกี่ยวข้อง

- [Dashboard](/th/backstage/dashboard) — ที่ session ที่ authenticated จะถูก redirect ไป ทั้งจากหน้านี้และจาก Login และ route guard ของมันเอง (ไม่ใช่ Landing) คือตัวที่แยก session ที่มี platform authority ออกจาก cluster admin แบบ membership-only จริง ๆ (§1); พื้นผิวโมดูลจริงที่ filter ด้วย permission ที่ดัชนี static ของหน้านี้ตั้งใจจะ preview
- [Changelog](/th/backstage/changelog) — อีก route สาธารณะเต็มรูปแบบ ลิงก์จาก "See what's new" ของ hero และใช้ component `VersionStamp` ร่วมกับ footer ของหน้านี้
- [กลุ่มฟอร์ม (Form Groups)](/th/backstage/report-form-groups), [Backstage Roles](/th/backstage/rbac), [SQL Workbench](/th/backstage/sql-workbench) — สามในหลายหน้าจอจริงที่ขาดหายจากดัชนีของหน้านี้ (§4) ดูตารางเต็มใน §4 รวมถึงสี่กลุ่ม (License Management, Analytics, Scheduling, AI) ที่ไม่มีตัวแทนบน Landing เลย

## 7. แหล่งข้อมูลอ้างอิง

- `../carmen-backstage/src/pages/Landing.tsx` — หน้า: auth-redirect effect, loading state, hero, array `groups` แบบ hardcode, footer
- `../carmen-backstage/src/pages/Login.tsx` — route สาธารณะพี่น้องที่มี pattern redirect เมื่อ authenticated แล้วเหมือนกัน
- `../carmen-backstage/src/components/nav/backstageNav.ts` — `ALL_BACKSTAGE_NAV_ITEMS` รายการ sidebar จริงที่ดัชนีของหน้านี้ถูกเทียบด้วยใน §4 `Layout.tsx` เองไม่ได้กำหนดแถว nav แล้ว มันแค่เรียก `buildBackstageNav()`
- `../carmen-backstage/src/components/PrivateRoute.tsx` — branch การตัดสินใจ Backstage-authority/cluster-admin ที่ยกมาใน §1 บันทึกไว้ครบถ้วนใน [Dashboard](/th/backstage/dashboard) §5
- `../carmen-backstage/src/App.tsx:103` — `<Route path="/" element={<Landing />} />` ที่ไม่ถูกห่อ (ไม่มี `<PrivateRoute>`)
- `../carmen-backstage/src/components/VersionStamp.tsx` (พร้อม `src/hooks/useBackendVersion.ts` และ `src/services/versionService.ts`) — version stamp ของ footer; `src/components/VersionBadge.tsx` ตอนนี้ให้เฉพาะค่าคงที่ `CURRENT_VERSION` / `BUILD_SHA` ประวัติ version badge บันทึกไว้ใน [Changelog](/th/backstage/changelog) §3

## 8. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดียว ดู [ดัชนี Backstage book](/th/backstage)
