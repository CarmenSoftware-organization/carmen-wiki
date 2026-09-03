---
title: Landing
description: หน้าการตลาดสาธารณะที่ / — redirect session ที่ authenticated แล้วไปยัง Dashboard ทันที และแสดงดัชนีโมดูล "Inside the console" แบบ hardcode ที่คลาดเคลื่อนไปจาก sidebar จริง (ยังแสดงโมดูล Print Mapping ที่ถูกลบแล้ว ขาด Form Groups, User Platform, และ SQL Workbench)
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/landing, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Landing

> **At a Glance**
> **หน้าจอ:** `Landing` (`/`) &nbsp;·&nbsp; **การเข้าถึง:** สาธารณะเต็มรูปแบบ — route ไม่มี wrapper `<PrivateRoute>` เลย แม้แต่แบบ authenticated-only เปล่า ๆ ที่ [Dashboard](/th/platform/dashboard) และ [Profile](/th/platform/profile) ใช้ &nbsp;·&nbsp; **พฤติกรรม:** redirect session ที่ authenticated แล้วไปยัง `/dashboard` ทันที &nbsp;·&nbsp; **เนื้อหา:** hero + CTA sign-in + ดัชนีโมดูล "Inside the console" แบบ hardcode สามกลุ่ม + footer version &nbsp;·&nbsp; **ความคลาดเคลื่อนที่ยืนยันแล้ว:** ดัชนีโมดูลยังระบุชื่อโมดูล Print Mapping ที่ถูกลบแล้ว และขาดสามหน้าจอจริง (§4)

## 1. ภาพรวม

Landing คือจุดเริ่มต้นสำหรับผู้ที่ signed-out ที่ `/` — หน้าการตลาดแบบ static หน้าเดียวที่ไม่มีการ fetch ข้อมูลของตัวเอง `<Route path="/" element={<Landing />} />` ใน `App.tsx` ไม่มี wrapper `<PrivateRoute>` เลย ต่างจากทุก route อื่นใน book นี้ route เดียวที่ไม่ถูก guard เท่านี้คือ `/login` และ `/changelog` ผู้เยี่ยมชมที่ authenticated อยู่แล้วจะไม่เห็นเนื้อหาการตลาดจริง ๆ เลย: `useEffect` ตรวจสอบ `isAuthenticated` แล้ว `navigate('/dashboard', { replace: true })` ออกไปทันที — pattern เดียวกับที่ `Login.tsx` ใช้ด้วยเหตุผลเดียวกัน ระหว่างที่ `AuthContext` ยัง resolve ไม่เสร็จ (`loading === true`) หน้านี้จะแสดงสัญลักษณ์ "C" ตรงกลาง, spinner, และ "Loading…" แทน — ดังนั้นผู้เยี่ยมชมที่ signed-in กลับมาโดยทั่วไปจะเห็น loading กระพริบสั้น ๆ แล้วไปที่ Dashboard ไม่เห็น hero ด้านล่างเลย

## 2. เนื้อหาของหน้า

สำหรับผู้เยี่ยมชมที่ signed-out จริง ๆ หน้านี้ render:

- **Header** — สัญลักษณ์ "C" + wordmark "Carmen Platform / Operations console" และปุ่ม **Sign in** ที่ลิงก์ไป `/login`
- **Hero** — หัวข้อชิดซ้าย ("Run the whole operation from one console.") ข้อความวางตำแหน่งหนึ่งประโยค ปุ่ม call-to-action **Sign in** และลิงก์ข้อความ **"See what's new"** ไป `/changelog` (อีก route สาธารณะเต็มรูปแบบเดียว บันทึกไว้ในหน้าของตัวเอง — [Changelog](/th/platform/changelog))
- **ดัชนีโมดูล "Inside the console"** — สามกลุ่มของรายการที่ตั้งชื่อ render เป็น list สามคอลัมน์ธรรมดา (ไม่มีลิงก์ — แต่ละรายการเป็นข้อความเฉย ๆ ไม่ใช่ tile ที่ navigate ได้) ดู §3 สำหรับเนื้อหาที่แน่นอนและ §4 สำหรับการเทียบกับ sidebar จริง
- **Footer** — `VersionBadge` ที่ใช้ร่วมกัน (component เดียวกับที่ footer ของ sidebar ใช้ บันทึกไว้ใน [Changelog](/th/platform/changelog) §3) label environment แบบ optional (`REACT_APP_ENV`) บรรทัด copyright และ build-date stamp แบบ optional (`REACT_APP_BUILD_DATE`)

## 3. ดัชนี "Inside the Console"

ดัชนีนี้เป็น array แบบ hardcode ใน `Landing.tsx` (`groups`) ไม่ได้มาจาก `NavItem[]` ของ sidebar เองหรือการตรวจสอบ permission ใด ๆ — render เหมือนกันทุกครั้งสำหรับผู้เยี่ยมชมทุกคน ไม่ว่าจะเห็นอะไรจริงหลัง sign in ตามที่เขียนไว้ มันแสดง:

| กลุ่ม | รายการ (ตามที่แสดงบน Landing) |
|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations |
| Content | Report Templates, **Print Mapping**, News, Broadcasts |
| Platform | Applications, Roles & Access, Super Admins |

## 4. ความคลาดเคลื่อนที่ยืนยันแล้ว: ดัชนี vs. Sidebar จริง

การเทียบตรง ๆ ของ array `groups` ใน `Landing.tsx` กับรายการ `allNavItems` ที่ใช้งานจริงใน `Layout.tsx` (แหล่งเดียวกับที่ [Business Units](/th/platform/business-units), [Report Templates](/th/platform/report-templates), และทุกหน้าโมดูลอื่นใน book นี้อ้างอิงสำหรับรายการ sidebar ของตัวเอง) แสดงว่าดัชนีการตลาดนี้ไม่ได้ sync ตามการเปลี่ยนแปลง sidebar สองรอบล่าสุด:

- **Print Mapping ยังอยู่ในรายการ Content** แม้ว่าโมดูล [print-template-mapping](/th/platform/print-template-mapping) — รวมถึงรายการ sidebar ของมัน — ถูกลบออกจาก carmen-platform เมื่อ 2026-07-24 สำเนาของหน้า Landing เองไม่ถูกแตะต้องโดย commit การลบนั้น
- **Form Groups ขาดหายจาก Content** [เทมเพลตรายงาน — Form Groups](/th/platform/report-templates/form-groups) (`/report-form-groups`) ออกมาสัปดาห์เดียวกับการลบ Print Mapping (2026-07-24) และอยู่ในกลุ่ม Content ของ sidebar วันนี้ รายการ Content ของ Landing ยังแสดงแค่ 3 จาก 4 รายการจริงของกลุ่ม
- **User Platform และ SQL Workbench ทั้งคู่ขาดหายจาก Platform** กลุ่ม Platform ของ sidebar มี 5 รายการ (Applications, Roles, Super Admins, User Platform, SQL Workbench); รายการ Platform ของ Landing แสดงแค่ 3 ละเว้นหน้าจอ `UserPlatformManagement` (ส่วนหนึ่งของ [Platform RBAC](/th/platform/rbac)) ไปทั้งหมด และเก่ากว่า [SQL Workbench](/th/platform/sql-workbench) (เพิ่มเมื่อ 2026-07-09) เสียอีก

สิ่งนี้ไม่ส่งผลต่อพฤติกรรมใด ๆ — ดัชนีเป็นข้อความเฉย ๆ ไม่มีลิงก์ อ่านได้เฉพาะผู้เยี่ยมชมที่ signed-out ที่กำลังตัดสินใจว่าจะ sign in หรือไม่ — แต่ผู้อ่านที่ใช้หน้านี้เป็นรายการ feature จะได้ภาพที่ไม่ถูกต้องว่า console ทำอะไรได้บ้างในปัจจุบัน นี่คือความคลาดเคลื่อนเชิงเอกสารในสำเนาการตลาดของผลิตภัณฑ์เอง ไม่ใช่ข้อผิดพลาดของ wiki — ระบุไว้ตรงนี้แทนที่จะแก้ไขแบบเงียบ ๆ เพราะการแก้ `Landing.tsx` เองอยู่นอกขอบเขตของ wiki นี้

## 5. บทบาทและ Persona

ไม่ต้อง authenticate และไม่ต้องมี permission grant ใด ๆ เพื่อดูหน้านี้ — เป็นหน้าจอเดียวในผลิตภัณฑ์ที่ browser แบบ anonymous เข้าถึงได้ องค์ประกอบที่โต้ตอบได้มีแค่สองลิงก์ navigation (Sign in → `/login`, See what's new → `/changelog`) ไม่มีอันไหนถูก gate

## 6. โมดูลที่เกี่ยวข้อง

- [Dashboard](/th/platform/dashboard) — ที่ session ที่ authenticated จะถูก redirect ไป ทั้งจากหน้านี้และจาก Login; พื้นผิวโมดูลจริงที่ filter ด้วย permission (ผ่าน sidebar ที่ `Layout.tsx` render เมื่อ signed in) ที่ดัชนี static ของหน้านี้ตั้งใจจะ preview
- [Changelog](/th/platform/changelog) — อีก route สาธารณะเต็มรูปแบบ ลิงก์จาก "See what's new" ของ hero และใช้ component `VersionBadge` ร่วมกับ footer ของหน้านี้
- [print-template-mapping](/th/platform/print-template-mapping) — โมดูลที่ถูกลบซึ่งดัชนีของหน้านี้เองยังไม่หยุดแสดง (§4)
- [เทมเพลตรายงาน — Form Groups](/th/platform/report-templates/form-groups), [Platform RBAC](/th/platform/rbac), [SQL Workbench](/th/platform/sql-workbench) — สามหน้าจอจริงที่ขาดหายจากดัชนีของหน้านี้ (§4)

## 7. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/pages/Landing.tsx` — หน้า: auth-redirect effect, loading state, hero, array `groups` แบบ hardcode, footer
- `../carmen-platform/src/pages/Login.tsx` — route สาธารณะพี่น้องที่มี pattern redirect เมื่อ authenticated แล้วเหมือนกัน
- `../carmen-platform/src/components/Layout.tsx:50-68` — รายการ `allNavItems` ของ sidebar จริงที่ดัชนีของหน้านี้ถูกเทียบด้วย
- `../carmen-platform/src/App.tsx:61` — `<Route path="/" element={<Landing />} />` ที่ไม่ถูกห่อ (ไม่มี `<PrivateRoute>`)
- `../carmen-platform/src/components/VersionBadge.tsx` — component version-badge ที่ใช้ร่วมกัน บันทึกไว้ครบถ้วนใน [Changelog](/th/platform/changelog) §3

## 8. หน้าในโมดูลนี้

โมดูลนี้เป็นหน้าเดียว ดู [ดัชนี Platform book](/th/platform)
