---
title: แคตตาล็อกไลเซนส์ — หน้าจอ UI (UI Screens)
description: กลไกแท็บของ shell LicenseCatalog แบบละเอียด, FeatureCatalogPanel (Features), GroupCatalogPanel (Bundles), LicenseFeatureGroupEdit, และส่วนประกอบตัวเลือก feature/แถบสัดส่วนที่ใช้ร่วมกัน
published: true
date: '2026-09-06T09:00:00.000Z'
tags: book/platform, license-catalog, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# แคตตาล็อกไลเซนส์ — หน้าจอ UI (UI Screens)

> **At a Glance**
> **Shell:** `LicenseCatalog` (`/license-features`, `/license-feature-groups`) — component เดียว, prop `tab`, แท็บคือ route ไม่ใช่ state &nbsp;·&nbsp; **แท็บ Features:** `FeatureCatalogPanel` — เน้นอ่าน มีแค่สวิตช์ `state` ต่อแถว ไม่มี create/delete &nbsp;·&nbsp; **แท็บ Bundles:** `GroupCatalogPanel` — รายการ CRUD เต็มรูปแบบของ `tb_license_feature_group` &nbsp;·&nbsp; **ตัวแก้ไข:** `LicenseFeatureGroupEdit` (`/license-feature-groups/{new,:id/edit}`) — component เดียว สองโหมด &nbsp;·&nbsp; **ตัวเลือก feature ที่ใช้ร่วมกัน:** `FeatureSelectionCard` — ตอนนี้มีผู้เรียกใช้**เฉพาะ**ตัวแก้ไขนี้เท่านั้น ไม่ใช่หน้าจอขายใด ๆ &nbsp;·&nbsp; **ไม่มี View History / Activity Trail** — grep `src/pages/licenseCatalog/`, `src/pages/licenseFeatures/`, `LicenseCatalog.tsx`, และ `LicenseFeatureGroupEdit.tsx` หา `activity_log.read`/`ActivityTrail`/`PLATFORM_SCOPED_RECORD` ไม่พบเลย &nbsp;·&nbsp; **ไม่มี e2e suite** — ทุกคำกล่าวอ้างด้านล่างมาจาก implementation ไม่ใช่จาก test spec

## 1. ภาพรวม

สาม component render อยู่บนสี่ route `FeatureCatalogPanel` และ `GroupCatalogPanel` เป็น**panel ไม่ใช่หน้าจอ** — `Layout` กับ `PageHeader` เป็นของ shell `LicenseCatalog` ที่ครอบอยู่ นี่คือเหตุผลที่แถบเครื่องมือของแต่ละ panel ถือปุ่ม Export ของตัวเอง (และของ Bundles คือปุ่ม New group ด้วย) แทนที่จะดันขึ้นไปไว้บนหัวหน้าที่อีกแท็บก็ใช้ร่วมกัน: ปุ่ม primary ที่สลับตัวเองตามแท็บจะอ่านสะดุดในงานที่ผู้ดูแลทำซ้ำทุกวัน `LicenseFeatureGroupEdit` เป็นหน้าเต็มรูปแบบแยกต่างหาก มี `Layout`/`PageHeader` ของตัวเอง เข้าถึงได้จากลิงก์แถวและปุ่ม New-group บนแท็บ Bundles เท่านั้น ไม่เคยซ้อนอยู่ใน shell

## 2. Shell `LicenseCatalog` (`/license-features`, `/license-feature-groups`)

### 2.1 แท็บคือ route ไม่ใช่ state ฝั่ง client

`TAB_PATH` แมปแต่ละ tab id ไปยัง URL ของตัวเอง (`bundles` → `/license-feature-groups`, `features` → `/license-features`); `onChange` ของ `TabStrip` เรียก `navigate(TAB_PATH[next])` แทนที่จะตั้ง state ในหน่วยความจำ การสลับแท็บจึง**remount** panel ที่กำลังจะเปิดใหม่และดึงข้อมูลใหม่เสมอ — ไม่มีการแคชร่วมระหว่างสองแท็บเลย คอมเมนต์ของ component เองระบุข้อแลกเปลี่ยนนี้ตรง ๆ: ทั้งสอง panel ดึงครั้งเดียวและมีเพดานเชิงโครงสร้างอยู่แล้ว (แคตตาล็อก feature และรายการ bundle เป็นข้อมูลที่จัดเอง ไม่ได้งอกตามการใช้งาน) การดึงใหม่ทุกครั้งที่สลับจึงไม่มีต้นทุนที่คุ้มจะเลี่ยง และหลีกเลี่ยงการสร้างแคชที่ต้องครอบคลุมสอง route ที่มี permission ต่างกันไปในตัว

### 2.2 ชื่อหัวหน้าคงที่หนึ่งชื่อ subtitle สลับได้หนึ่งอัน

`title` ของ `PageHeader` เป็น `t('pages.licenseCatalog.title')` เสมอ — "License Catalog" ตรงตัว — ไม่ว่าแท็บไหนกำลังเปิดอยู่ มีแค่ `subtitle` ที่เปลี่ยนระหว่าง `pages.licenseFeatureGroups.subtitle` ("Curated bundles of licence features, used when selling a subscription") กับ `pages.licenseFeatures.subtitle` ("Choose which features can still be sold. The catalog itself is generated — only the state is yours to set.") นี่คือการตัดสินใจเรื่องตัวตนโดยตั้งใจ ไม่ใช่ความพลาด: ชื่อที่เปลี่ยนตามแท็บจะทำให้การรวมนี้อ่านเป็นสองหน้าจอที่บังเอิญใช้ URL prefix ร่วมกัน ทำลายเหตุผลทั้งหมดที่ถือว่ามันเป็นโมดูลเดียว

**จุดสังเกตเรื่องชื่อที่ผู้ทดสอบควรรู้:** ป้ายบน sidebar เขียนว่า "License Feature Groups" กับ "License Features" (`platformNav.ts:21-22`) แต่พอเข้ามาในตัว shell แล้ว ป้ายแท็บเองกลับเขียนว่า "Bundles" กับ "Features" (`tabBundles`/`tabFeatures` — ป้ายสั้นกว่าที่ใช้เฉพาะในแถบแท็บ) ผู้ทดสอบที่ตามชื่อบน sidebar เป๊ะ ๆ จะไม่เจอชื่อนั้นซ้ำอีกครั้งบนหน้าจอที่มันพาไป นี่คือพฤติกรรมที่ตั้งใจ ไม่ใช่บั๊กด้านคำ

### 2.3 แถบแท็บหายไปเมื่อเข้าถึงได้แค่แท็บเดียว

`tabs` สร้างโดยกรอง `TAB_ORDER` (`['bundles', 'features']`) ผ่านด่านของแต่ละแท็บเอง (`TAB_GATE`) — `hasPermission(gate.permission) && flagOf(gate.feature) === 'active'` — และ `<TabStrip>` จะ render ก็ต่อเมื่อ `tabs.length > 1` เท่านั้น นี่คือ**การตรวจซ้ำฝั่ง client** ของสิ่งที่ route guard ตรวจไปแล้วก่อนที่ panel จะ mount ได้เลย (ดู §4 ของ[หน้าลงจอด](/th/platform/license-catalog)) — มันมีอยู่เพราะทั้งสองแท็บใช้ shell เดียวกัน shell เองจึงต้องเป็นคนตัดสิน ไม่ใช่ router ว่าจะวาดตัวควบคุมที่ชี้ไปแท็บที่ session ปัจจุบันเข้าไม่ได้หรือไม่ session ที่เข้าถึงได้แค่แท็บเดียวจึงเห็น panel เดียวไม่มีแท็บ ไม่มีแถบเปล่าอยู่ข้างบนบน route ใดก็ตามในสองตัวที่มันเข้าถึงได้

คอมเมนต์ของ component เองอธิบายว่าทำไมการตรวจนี้ไม่ต้องรอ `flagsReady`: route guard ของ URL ที่กำลัง mount อยู่ตอนนี้ตรวจทั้ง permission และ flag เสร็จไปแล้วก่อนที่ `LicenseCatalog` จะ render เลย การตรวจซ้ำที่นี่จึงไม่มีวันเจอสถานะที่ยังโหลดอยู่ — เป็นแค่การคำนวณซ้ำสิ่งที่ตัดสินไปแล้วสำหรับแท็บที่กำลังแสดงอยู่ บวกกับการตรวจด่านของ*อีกแท็บ*แยกต่างหากว่าจะวาดแถบไหม

## 3. `FeatureCatalogPanel` — แท็บ Features

กรองฝั่ง client ไม่ใช่แบ่งหน้าฝั่ง server: `licenseFeatureService.getAll()` (`GET /platform/license-features/all`) ดึงทุกแถวที่ยังไม่ถูกลบ — รวมแถวที่ซ่อนไว้ด้วย เพราะหน้าที่ซ่อน feature ได้ต้องหามันเจอเพื่อเอากลับ — ครั้งเดียว แล้วทุกการค้น/กรองทำงานบนผลลัพธ์ที่อยู่ในหน่วยความจำ ไม่มี debounce บนช่องค้น และไม่มีตัวควบคุมแบ่งหน้า เพราะจำนวนแถวมีเพดานเชิงโครงสร้างจาก generator (89 แถว ณ เวลาที่เขียน ดู [Data Model](/th/platform/license-catalog/data-model) §3) ไม่ได้งอกตามการใช้งาน การหั่นชุดข้อมูลขนาดนี้เป็นหลายหน้าเคยบังคับให้ผู้ดูแลเปิดหลายหน้าเพื่อตอบคำถามที่แถบสรุปตอบได้ในวินาทีเดียว

**พื้นที่แก้ไข:** `state` เท่านั้น ทีละแถว บันทึกทันที (`PATCH` ต่อแถว ไม่มี draft/บันทึกเป็นชุด) แตกต่างจาก `/platform/features` (Feature Flags) โดยตั้งใจ ที่นั่น backend รับ PUT เดียวที่ทับทั้ง map ทีเดียว ส่วนที่นี่แต่ละแถวถือ `doc_version` ของตัวเอง การรวบหลายแถวเป็นชุดเดียวแล้วบันทึกจะบังคับให้ต้องออกแบบ UX ตอนสำเร็จครึ่ง ๆ ("สำเร็จ 18 ล้มเหลว 2 — แต่ 2 อันไหน") ที่การบันทึกทีละแถวไม่ต้องเจอเลย `key`/`label`/`sort_order` เป็นอ่านอย่างเดียวทุกที่บนหน้านี้ — เป็นของ generator

**แถบสรุปสถานะ (`CatalogStateBar`) นับหลังคำค้นแต่ก่อนตัวกรองสถานะ** — พฤติกรรมมาตรฐานของ facet count: ถ้านับหลังตัวกรองสถานะด้วย ทุกช่องที่ไม่ได้เลือกจะขึ้น `0` ทันทีที่มีการกรอง ทำให้แถบทั้งแถบไร้ความหมายพอดีตอนที่กำลังถูกใช้งาน ช่องที่นับได้ `0` ไม่เคย disable — "ยังไม่มีตัวไหนถูกซ่อนเลย" เป็นคำตอบที่มีความหมายและกดเข้าไปยืนยันได้

**`ModuleShelf` จัดกลุ่มแถวตาม module ราก** หนึ่งการ์ดต่อหนึ่ง module แทนที่รายการแบน 76-ถึง-89-แถวเดิมที่พิมพ์คอลัมน์ "Module" ซ้ำทุกแถว หัวชั้นสรุปจาก**ลูกทั้งโมดูลเสมอ ไม่ใช่เฉพาะที่ผ่านตัวกรอง** — ตัวเลขที่หดตามตัวกรองจะบอกขนาดโมดูลผิด ระหว่างกรองอยู่หัวชั้นจึงเปลี่ยนไปพูด "แสดง *N* จาก *ทั้งหมด*" แทน ซึ่งพูดถึงมุมมองปัจจุบันตรง ๆ โดยไม่แตะข้อเท็จจริงของโมดูล ลูก (และหลาน เยื้องลึกกว่า — ดู [Data Model](/th/platform/license-catalog/data-model) §3 ว่าทำไมต้นไม้จึงลึกได้ถึงสามชั้นแล้ว) เรียงแบบ depth-first ไม่ใช่ตาม `sort_order` ดิบ หลานจึงอยู่ใต้พ่อของมันเองเสมอ ไม่ไปกองอยู่ในแถบตัวเลขที่ generator กำหนดให้

คำอธิบายต่อแถวแสดง**เฉพาะเมื่อมันพูดสิ่งที่ label ยังไม่ได้พูด** — คำอธิบายส่วนใหญ่ที่ generator เขียนคือ `"View " + label` ตรงตัว ซึ่งถ้าแสดงทุกครั้งจะพูดซ้ำชื่อของแถวเองใน 89 แถวโดยไม่มีข้อมูลใหม่เพิ่มเลย

**การซ่อนคือการกระทำเดียวที่มีกล่องยืนยัน และแค่ตอนที่มันจะทำให้ใครเสียของจริง ๆ** การตั้งเป็น `inactive` ไม่ต้องยืนยัน (หยุดขายเพิ่ม ของเดิมไม่เปลี่ยน) การตั้งเป็น `hide` จะขึ้น `ConfirmDialog` ระบุ `affected_bu_count` — จำนวน business unit ที่จะเสียเมนูนั้นไปทันที — **เฉพาะเมื่อจำนวนนั้นมากกว่าศูนย์**เท่านั้น feature ที่ไม่มีใครถือจะบันทึกทันทีไม่ต้องยืนยัน เมื่อ feature ที่กำลังจะซ่อนมีลูกหลาน (เป็น node ชั้นกลางของต้นไม้) กล่องจะต่อท้ายด้วยจำนวนลูกหลาน เพราะ evaluator สิทธิ์ตอน runtime ตัดคีย์ที่ `hide` ออกจากชุดสิทธิ์ของ business unit ก่อนตรวจสายบรรพบุรุษของลูกหลาน — การซ่อนพ่อจะทำให้สิทธิ์ของลูกทุกตัวพังแบบเงียบ ๆ สำหรับทุกคนที่ถือมันอยู่ แม้ว่าแถวของลูกเองจะไม่เปลี่ยน state เลยก็ตาม (ดู [Data Model](/th/platform/license-catalog/data-model) §3 สำหรับกลไกเต็ม) ข้อความในกล่องยังบอกว่าการกระทำนี้กู้คืนได้ ("ตั้งกลับเป็น active แล้วเมนูจะกลับมาภายในประมาณหนึ่งนาที" — อายุ cache ของ gateway เอง) โดยตั้งใจไม่พูดให้น่ากลัวเกินจริง เพราะคำเตือนที่ฟังดูร้ายแรงกว่าความจริงจะฝึกให้คนเลิกอ่านมัน

`affected_bu_count` เป็น `undefined` ไม่ใช่ `0` เมื่อ gateway ที่ตอบมาเก่าเกินกว่าจะส่งฟิลด์นี้ — แถวนั้นจะ render โดยไม่แสดงจำนวนเลยในกรณีนี้ ไม่ใช่พิมพ์ "0" ซึ่งจะยืนยันผิด ๆ ว่าไม่มีใครถือคีย์นี้

## 4. `GroupCatalogPanel` — แท็บ Bundles

`DataTable` ของทุก bundle ที่ยังไม่ถูกลบ ดึงด้วยขนาดหน้าจำกัด (`perpage: 200` ไม่ใช้ `perpage: -1` เลย) แล้วกรองฝั่ง client ต่อด้วยชื่อ/code และช่อง "active only" — เหตุผล "มีเพดานเชิงโครงสร้าง จึงกรองฝั่ง client ได้" เดียวกับแท็บ Features เพราะ bundle เป็นของที่จัดเอง ไม่ได้งอกตามการใช้งาน

**คอลัมน์:** ลำดับ (ชิปตัวเลขเล็ก ๆ ขอบสีเตือนเมื่อ bundle อื่นถือเลขเดียวกัน — คำนวณจาก**ชุดที่ไม่ผ่านการกรองทั้งหมด** เพราะ bundle ที่ถูกกรองออกจากมุมมองก็ยังแย่งลำดับเดียวกันบนฟอร์มขายอยู่ดี) · code (ลิงก์เข้า `LicenseFeatureGroupEdit` ตัวพิมพ์ monospace) · ชื่อ + คำอธิบาย (เซลล์เดียวกัน คำอธิบายตัดให้เหลือบรรทัดเดียว) · **Features** (จำนวนบวกแถบสัดส่วนที่ใช้ตัวหารร่วมทั้งหน้าเมื่อรู้ค่าตัวหาร — ดู §6 ว่าตัวหารนั้นพึ่งพาอะไรจริง ๆ) · จำนวนสัญญา (ข้อความสรุปเฉย ๆ บนหน้านี้ ตัวเลขที่จะกลายเป็นคำเตือนก็ต่อเมื่อมีคนพยายามลบหรือปิดการขาย bundle นั้น §4.1) · badge active/inactive · เมนูต่อแถว (Edit / Delete)

**แถบสัดส่วน Features — ตัวหารที่หายไปเงียบ ๆ ได้** ป้ายจำนวน/ทั้งหมดของคอลัมน์นี้และแถบเองพึ่งพา `catalogTotal` ที่ดึงจาก request **แยกต่างหาก** (`subscriptionService.getFeatureCatalog()`) ที่ตั้งใจแยกออกจากการโหลดรายการ bundle เอง — ถ้า catalog total โหลดไม่สำเร็จ แถบจะหายไปเฉย ๆ ไม่ทำให้ทั้งหน้าพัง เพราะ `feature_count` เพียงตัวเดียวโดยไม่มีตัวหารก็ยังเป็นตัวเลขที่อ่านรู้เรื่องได้เอง ดู §4.3 ของ[หน้าลงจอด](/th/platform/license-catalog) ว่า request แยกนั้นต้องการ permission ตัวไหนจริง ๆ ซึ่ง**ไม่ใช่**สองคู่ permission ของโมดูลนี้เอง ตัวหารยังใช้ได้แต่น่าสงสัยได้อีกแบบหนึ่ง: ถ้า `feature_count` ที่บันทึกไว้ของ bundle หนึ่งเกินยอดแคตตาล็อกที่ดึงมา (เกิดได้เฉพาะเมื่อ feature ถูกซ่อนหลังจาก bundle ถือมันไปแล้ว — endpoint แคตตาล็อกทั่วไปตัดแถวที่ซ่อนออก ส่วนแคตตาล็อกฝั่งผู้ดูแลไม่ตัด) คอลัมน์นี้จะถอยไปแสดงตัวเลขเปล่าไม่มีแถบ แทนที่จะวาดเปอร์เซ็นต์เกิน 100%

### 4.1 New group และปุ่มต่อแถว — ถูกกั้นสิทธิ์ แต่กล่องยืนยันการลบไม่ใช่ตัวบล็อกด้วยตัวเอง

ปุ่ม **New group** บนหัวหน้า, ปุ่ม New-group ใน empty state, และรายการ **Edit**/**Delete** ในเมนูต่อแถว ทั้งหมดถูกห่อด้วย `<Can permission="license_feature_group.manage">` — session ที่มีแค่ `.read` เห็นตารางและแถบสัดส่วนได้ แต่ไม่มีทางสร้าง แก้จากรายการ หรือลบ

**การลบ bundle ที่ยังใช้งานอยู่ไม่ถูกบล็อกโดยข้อความในกล่องยืนยัน — มันถูกบล็อกโดย server** `ConfirmDialog` ที่ขึ้นก่อนลบแสดงข้อความรุนแรงกว่าเมื่อ `subscription_count > 0` (ระบุจำนวนสัญญาที่อ้างถึง bundle นั้นตรง ๆ) เทียบกับข้อความ "ลบกลุ่มนี้ไหม" ธรรมดาเมื่อไม่มี — แต่การกดยืนยันทั้งสองแบบยิง `DELETE` เหมือนกันไม่ว่าจำนวนจะเป็นเท่าไร backend ปฏิเสธการลบเมื่อยังมีแถว `tb_subscription_bu_group` ที่ยังไม่ถูกลบอ้างถึง bundle นั้นอยู่ ส่งกลับเป็น error ที่ frontend แปลงเป็น 409 conflict UI แสดงเป็น toast (`getErrorDetail`) และ bundle ยังคงอยู่ในรายการ ไม่ถูกลบ อย่าอ่านข้อความเตือนในกล่องว่าเป็นกลไกการบังคับใช้ — มันเป็นแค่การแจ้งให้รู้ก่อน ตัวล็อกจริงอยู่ฝั่ง server

## 5. `LicenseFeatureGroupEdit` (`/license-feature-groups/new`, `/license-feature-groups/:id/edit`)

component เดียวให้บริการทั้งสร้างและแก้ไข แยกกันแค่ว่ามี `:id` หรือไม่ หน้าเรียงเป็น *ตัวตน → สัดส่วน → ตำแหน่งบนฟอร์มขายและสถานะ → เนื้อหาข้างใน* แทนที่จะเป็นกริดหกช่องที่ให้น้ำหนักเท่ากันหมด: `code` (แก้ได้เฉพาะตอนสร้าง — ในโหมดแก้ไขฟิลด์นี้ไม่ได้ render เป็นช่องกรอกเลยด้วยซ้ำ มีแค่ป้าย monospace คงที่ เพราะ backend ปฏิเสธ `code` ในทุก payload ของ `PATCH`), `name`, `description` แล้วในคอลัมน์ขวาความกว้างคงที่ที่ใช้ความกว้างเดียวกับคอลัมน์แถบสัดส่วนของหน้ารายการ เพื่อไม่ให้สองหน้าพูดความหมายของตัวเลขต่างกัน คือ `GroupCompositionPanel` (§6) ใต้เส้นคั่น: `sort_order` (มีขอบสีเตือนเมื่อชนกับกลุ่มอื่นเหมือนหน้ารายการ คำนวณจากการดึงข้อมูลลำดับของ bundle อื่นทั้งหมดแยกต่างหากที่ล้มแล้วเงียบ ไม่บล็อกหน้าถ้าโหลดไม่สำเร็จ) และปุ่มแบบ segmented "ขายอยู่ / หยุดขาย" สำหรับ `is_active` (แทนที่ checkbox ธรรมดาพร้อมข้อความอธิบายข้าง ๆ เดิม — สองสถานะที่แยกกันชัดเจนอ่านเร็วกว่าเป็นปุ่มสองปุ่มที่สลับที่กัน มากกว่ากล่องเดียวที่ต้องอ่านประโยคข้าง ๆ ถึงจะรู้ความหมาย)

**การบันทึกคือหนึ่งหรือสอง request ขึ้นกับว่ามีอะไรเปลี่ยนจริง** ถ้ามีแค่ metadata เปลี่ยน จะยิง `PATCH` ครั้งเดียว ถ้าการเลือก feature เปลี่ยนด้วย metadata จะบันทึกก่อน (ถ้าเปลี่ยนด้วย) แล้วยิง feature `PUT` ตามหลัง **โดยใช้ `doc_version` ที่การบันทึก metadata เพิ่งคืนมา** ไม่ใช่ค่าที่ถืออยู่ก่อนทั้งสอง request เพราะ `PATCH` เพิ่งเลื่อนเวอร์ชันไปแล้วฝั่ง server การส่งค่าเก่าจะได้ 409 ทันทีทั้งที่ไม่มีใครมาแก้แข่งจริง ๆ ความขัดแย้งของเวอร์ชันจากคำขอไหนก็ตามจะเรียก toast "มีคนอื่นแก้ไปแล้ว" ที่ใช้ร่วมกันและโหลดเรคคอร์ดใหม่ทั้งหมด ทิ้ง draft ที่ค้างอยู่

**feature key ที่ไม่รู้จักถูกแสดงให้เห็น ไม่ถูกถอดทิ้งเงียบ ๆ** bundle หนึ่งอาจถือคีย์ที่ภายหลังถูกถอดออกจากแคตตาล็อกที่ active แล้ว (ถูกปิดหลังจาก bundle เคยถืออยู่แล้ว) `FeatureSelectionCard` แสดงคีย์เหล่านี้ในบล็อกขอบเส้นประแยกต่างหาก แยกจากต้นไม้หลัก พร้อมปุ่มถอดทีละคีย์ในโหมดแก้ไข — ไม่เคยถอดให้อัตโนมัติเลย เพราะการเขียนทับสิ่งที่สัญญาลูกค้าได้รับแบบเงียบ ๆ โดยไม่มีการกระทำที่มองเห็นได้ ไม่ใช่ "ความช่วยเหลือ" แบบที่ควรเป็น

**จำนวนสัญญาของ bundle เองกลายเป็นคำเตือนที่ทำงานจริงที่นี่ ต่างจากหน้ารายการ** `GroupCompositionPanel` แสดงกล่องเตือนแยกต่างหากเมื่อ `subscription_count > 0` และต่อท้ายอีกหนึ่งบรรทัด — ปรากฏก็ต่อเมื่อผู้ใช้กำลังสลับ bundle จาก active ไปเป็น inactive เท่านั้น — ระบุว่ามีสัญญาที่ยังใช้งานอยู่กี่ใบที่จะได้รับผลกระทบ บรรทัดนี้ถูกซ่อนด้วย `invisible` (ไม่ใช่ถอดออกจาก layout) แทนที่จะโผล่มาแค่ตอนคลิกที่จะทำให้มันจริง เพื่อไม่ให้กล่องรอบข้างเปลี่ยนความสูงในจังหวะที่เพิ่งมีคลิกเกิดขึ้น ซึ่งเคยทำให้คลิกครั้งที่สองที่ตั้งใจกดปุ่มอื่นพลาดเป้าไปโดนที่อื่นแทน

## 6. ส่วนประกอบที่ใช้ร่วมกัน

- **`FeatureSelectionCard`** (`src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`) — ตัวเลือก feature แบบหีบเพลง n ชั้นต่อโมดูล ตอนนี้มีผู้เรียกใช้เหลือแค่**ที่เดียวในทั้ง SPA: ตัวแก้ไขนี้เอง** คอมเมนต์ของมันเองระบุว่าเคยชื่อ `FeatureMatrixCard` และเคยใช้บนหน้าจอขาย/subscription ด้วย เฟสของขั้นตอนขายเมื่อ 2026-09 ถอดการเลือก feature รายตัวออกจาก subscription ทั้งหมดแล้วหันไปเลือกทั้ง bundle แทน (`GroupSelectionCard` ของโมดูล [Licenses](/th/platform/licenses) เอง เป็นคนละ component) ทำให้การ์ดนี้เป็นของโมดูลนี้เพียงผู้เดียวตอนนี้ มันวาดแถบขีดต่อโมดูล (`AllocationTicks` component เดียวกับที่หน้าจอโควตาที่นั่งใช้) แทนแถบเปอร์เซ็นต์ เพราะแถบเปอร์เซ็นต์เทียบข้ามแถวไม่ได้เมื่อแต่ละแถวมีตัวหารไม่เท่ากัน ส่วน "หนึ่งขีดต่อหนึ่งช่องที่มีได้" อ่านความหมายเดียวกันไม่ว่าโมดูลไหนจะมีกี่ช่อง
- **`GroupCompositionPanel`** / **`FeatureCompositionBar`** (`src/pages/licenses/{GroupCompositionPanel,FeatureCompositionBar}.tsx`) — แผงสรุปสัดส่วนและแถบของมัน ใช้ร่วมกันตัวต่อตัวระหว่างแถบต่อแถวของหน้ารายการกับแผงบนหัวของตัวแก้ไข เพื่อไม่ให้ข้อเท็จจริง "กินแคตตาล็อกไปเท่าไร" ของ bundle เดียวกันมีคำตอบสองแบบต่างกันแล้วแต่หน้าจอ ตัวหารของแถบมาจากผู้เรียกเสมอ ไม่เคยคำนวณเองจากค่าที่มากที่สุดในหน้า — วินัยเดียวกับที่คอมเมนต์ของ `FeatureCompositionBar` เองย้อนไปถึงบั๊กที่เคยเกิดบนแถบของอีกโมดูลหนึ่ง (`windowStart`/`windowEnd` ของ `LicenseCoverageBar`)
- **`CatalogStateBar`** / **`ModuleShelf`** (`src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx`) — แถบสรุปและชั้นวางต่อโมดูลของแท็บ Features เองที่อธิบายไว้ใน §3 ชุดคีย์ป้าย/คำใบ้สถานะ (`LICENSE_STATE_LABEL`/`LICENSE_STATE_HINT` ใน `FeatureCatalogPanel.tsx`) ตั้งใจ**ไม่**ใช้ร่วมกับหน้า Feature Flags ที่ไม่เกี่ยวข้องกัน — ดู §3.3 ของ[หน้าลงจอด](/th/platform/license-catalog)

## 7. แหล่งข้อมูลอ้างอิง

path ทั้งหมดคือ `../carmen-platform` ยกเว้นที่ระบุไว้เป็นอย่างอื่น

- `src/pages/LicenseCatalog.tsx` — shell, `TAB_PATH`/`TAB_GATE`/`TAB_ORDER`, และสามพฤติกรรมใน §2
- `src/pages/licenseCatalog/FeatureCatalogPanel.tsx` — แท็บ Features (§3)
- `src/pages/licenseFeatures/{CatalogStateBar,ModuleShelf}.tsx` — แถบสรุปและชั้นวางต่อโมดูลของแท็บ Features
- `src/pages/licenseCatalog/GroupCatalogPanel.tsx` — แท็บ Bundles (§4)
- `src/pages/LicenseFeatureGroupEdit.tsx` — ตัวแก้ไข bundle (§5)
- `src/pages/licenses/subscriptionEdit/FeatureSelectionCard.tsx`, `src/pages/licenses/subscriptionEdit/featureSelection.ts` — ตัวเลือก feature ที่ใช้ร่วมกันและตรรกะการเปลี่ยนสถานะล้วน ๆ ของมัน (§6)
- `src/pages/licenses/GroupCompositionPanel.tsx`, `src/pages/licenses/FeatureCompositionBar.tsx` — แผงสรุปสัดส่วนและแถบที่ใช้ร่วมกัน (§6)
- `src/hooks/useFeatureCatalog.ts` — hook แคตตาล็อกที่โหลดครั้งเดียวต่อหน้าของตัวแก้ไข ป้อนทั้งตัวเลือกและแผงสรุปสัดส่วนจาก request เดียวกัน
- `src/services/{licenseFeatureService,licenseFeatureGroupService,subscriptionService}.ts` — REST client; `subscriptionService.getFeatureCatalog()` คือคำเรียกข้ามโมดูลที่เอกสารไว้ใน §4.3 ของ[หน้าลงจอด](/th/platform/license-catalog)
- `src/utils/featureTree.ts` — `ancestorsOf()`, `descendantKeys()`, `flattenDescendants()`, ใช้ตลอดทั้ง §3 และ §5

**Cross-links:** [หน้าลงจอด License Catalog](/th/platform/license-catalog) &nbsp;·&nbsp; [Data Model](/th/platform/license-catalog/data-model) &nbsp;·&nbsp; [Licenses](/th/platform/licenses)
