---
title: Dashboard Templates — UI Screens
description: หน้า Dashboard Templates ทีละแท็บ — รายการ widget ของ System และ BU default, dialog เพิ่ม/แก้ไข widget, ลูกศรจัดลำดับ และแท็บ Deploy พร้อมการยืนยัน overwrite
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, dashboard-templates, ui-screens
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates — UI Screens

> **At a Glance**
> **หน้าจอ:** 1 หน้า 3 แท็บ (System, BU default, Deploy) &nbsp;·&nbsp; **Layout การแก้ไข:** modal dialog ไม่มี route แก้ไข &nbsp;·&nbsp; **Dialogs:** `TemplateEditDialog`, `ConfirmDialog` สำหรับลบ, `OverwriteConfirmDialog` &nbsp;·&nbsp; **การเข้าถึง:** `dashboard_template.read`; แท็บ Deploy ต้องมี `.deploy` &nbsp;·&nbsp; **UI state ที่เก็บถาวร:** แท็บที่เลือกใน URL เท่านั้น

## 1. ภาพรวม

`DashboardTemplateManagement` ที่ `/dashboard-templates` render `PageHeader` และ `TabStrip` แท็บที่เลือกเก็บใน query string (`?tab=`) เขียนด้วย `replace` เพื่อให้การสลับแท็บไม่เพิ่ม history entry System และ BU default render คอมโพเนนต์เดียวกันโดยส่ง prop `kind`; `key={tab}` ทำให้ remount เมื่อสลับ ดังนั้นการเลือกโมดูลจึงรีเซ็ต ไม่มีการค้นหา, pagination หรือตัวควบคุมการเรียง: โมดูลหนึ่งมี widget ไม่กี่ตัว และการจัดลำดับคือตัวฟีเจอร์เอง

## 2. `TemplateListPanel` (แท็บ System และ BU default)

### 2.1 Layout

การ์ดที่มี toolbar และตาราง Toolbar จากซ้ายไปขวา: select **Module** (System: เจ็ดโมดูล, ค่าเริ่มต้น Procurement; BU default: **Main** บวกเจ็ดโมดูล, ค่าเริ่มต้น Main), **version badge** (เฉพาะแท็บ BU default, "Version N" อ่านจาก `GET /bu-default/version` หลังโหลดทุกครั้ง) และ badge **ความครอบคลุมภาษาไทย** ("Thai titles done/total" นับ row ที่มี title และมี title ภาษาไทยด้วย; สีเหลืองอำพันจนกว่าจะครบ) ปุ่ม **Add widget** อยู่ทางขวา

ตาราง:

| คอลัมน์ | หมายเหตุ |
|---|---|
| Title | title ในภาษาของ UI (fallback ไปภาษาอื่น แล้วไปชื่อ dataset พร้อมป้าย "(Dataset name)") บรรทัดที่สองแสดงอีกภาษาพร้อมแท็ก `en`/`th` หรือ hint ตัวเอียง "No Thai title" |
| Dataset | ชื่อ dataset (จากแค็ตตาล็อก) เหนือ `dataset_id` แบบ monospace; badge แดง "Dataset no longer exists" เมื่อโหลดแค็ตตาล็อกแล้วไม่พบ |
| Type | ไอคอนพร้อม `widget_type` |
| Scope | **เฉพาะแท็บ System** "All business units" หรือ "Only N business unit(s)" / "Hidden from N" พร้อม BU code ใน tooltip |
| Status | badge Active / Inactive; row ที่ inactive เป็นสีเทา |
| (actions) | เลื่อนขึ้น, เลื่อนลง, แก้ไข, ลบ |

ระหว่างโหลดใช้ `TableSkeleton`; เมื่อว่างใช้ `ListEmptyState` มีเพียง request ล่าสุดเท่านั้นที่เขียน state ดังนั้นการสลับโมดูลเร็ว ๆ จะไม่แสดงคำตอบที่ล้าสมัย

### 2.2 Row actions

| Action | Permission | พฤติกรรม |
|---|---|---|
| Move up / down | `dashboard_template.update` | `PATCH /reorder` โดยกำหนดเลขลำดับใหม่ทั้งโมดูลเป็น 10, 20, 30...; disable ที่ row แรก/สุดท้ายและขณะ busy |
| Edit | `dashboard_template.update` | เปิด `TemplateEditDialog` |
| Delete | `dashboard_template.delete` | dialog ยืนยัน แล้ว `DELETE /:id` |

dialog ยืนยันการลบมีหัวข้อ "Delete widget" และบอกว่า business unit ที่ได้รับเทมเพลตไปแล้วจะยังเก็บสำเนาไว้จนกว่าจะ deploy ครั้งถัดไป

## 3. `TemplateEditDialog`: โหมดสร้าง

เปิดจาก Add widget บริบท (kind, module) มาจาก panel จึงแก้ไขที่นี่ไม่ได้ widget ใหม่ได้ `order_index` = ค่าสูงสุดปัจจุบัน + 10 ฟิลด์:

| ฟิลด์ | Control | หมายเหตุ |
|---|---|---|
| Dataset | select เรียงตามหมวดหมู่แล้วตามชื่อ ป้ายเป็น `name · shape` | จำเป็น; การเปลี่ยนจะรีเซ็ต widget type และ params |
| Widget type | select ของ `supported_renders` ของ dataset | disable จนกว่าจะเลือก dataset; จำเป็น |
| Title (EN) / Title (TH) | text, สูงสุด 255 | TH โดยไม่มี EN ถูกบล็อกฝั่ง client |
| Dataset parameters | `DatasetParamFields`: select เมื่อ param มี `options`, ช่องตัวเลขเมื่อ `type = number`, ไม่งั้นเป็น text; ฟิลด์จำเป็นมี `*` | ค่าที่ว่างจะถูกทิ้งแทนที่จะส่งเป็น `''` |
| Allow BUs / Deny BUs | `BusinessUnitMultiSelect` ใช้ BU **code** เป็น key | เฉพาะ kind แบบ System |
| Active | checkbox | เปิดเป็นค่าเริ่มต้น |

Save ต้องมี dataset และ widget type `POST /api-system/dashboard-templates` พร้อม `kind`, `module` ใน wire format (`main` กลายเป็น `null`) และ `order_index`

## 4. `TemplateEditDialog`: โหมดแก้ไข

dialog เดียวกันที่โหลดค่าจาก row `kind` และ `module` แก้ไม่ได้ (dialog ไม่ส่งทั้งสอง) `PATCH /:id` ส่ง `doc_version` เมื่อ row มีค่านี้; version conflict แสดง toast ที่ใช้ร่วมกัน ปิด dialog และโหลดใหม่ error อื่นแสดงแบบ inline ("Could not save: ...") รวมถึงข้อความ 422 ของ backend สำหรับ dataset ที่ไม่รู้จักหรือ widget type ที่เข้ากันไม่ได้ Title ถูกส่งทั้งเป็น `title` และ `title_i18n` `display` ไม่เคยถูกส่ง

## 5. `DeployPanel` (แท็บ Deploy)

ซ่อนและ render ไม่ได้หากไม่มี `dashboard_template.deploy` (คอมโพเนนต์คืน `null` ถ้าการตรวจล้มเหลว)

### 5.1 Layout

ข้อความ hint พร้อมเวอร์ชันปัจจุบัน, alert เมื่อชุด BU-default ที่ active ว่างเปล่า แล้วจึงเป็น toolbar: **Refresh status**, **Select outdated** (เลือก BU ที่สถานะเป็น `outdated` หรือ `never`), radio คู่ **mode** (Skip customized / Overwrite) และ **Deploy (N)** ซึ่งกลายเป็น **Stop** สีแดงขณะรัน ด้านล่างเป็นตารางของ business unit ทุกแห่งเรียงตาม code

| คอลัมน์ | เนื้อหา |
|---|---|
| (checkbox) | ราย row และเลือกทั้งหมด |
| Business unit | `code - name` |
| Deploy status | Badge: `current` (เขียว), `outdated` (เหลืองอำพัน), `customized` (เทา), `never` (outline), `unknown` ก่อนการตรวจครั้งแรก (outline), `error` (แดง); spinner ขณะตรวจ/deploy; บรรทัดผลลัพธ์ราย row ("Deployed N widget(s)", หมายเหตุว่าข้าม หรือ error) |
| Deployed version | `deployed_version` หรือขีดกลาง |
| Deployed at / Customized at | วันที่-เวลาจัดรูปแบบตาม locale, ขีดกลางเมื่อเป็น null |

ตอน mount panel โหลด BU ทั้งหมด (`fetchAllBusinessUnits`) จากนั้นโหลดเวอร์ชันและจำนวน widget ที่ active แล้วตรวจสถานะของทุก BU ด้วย concurrency 4

### 5.2 การยืนยัน Overwrite

เมื่อเลือก Overwrite แล้วกด Deploy จะเปิด `OverwriteConfirmDialog`: หัวข้อสีแดง, บรรทัดที่บอกว่า BU ที่เลือกกี่แห่งเคยแก้แดชบอร์ดด้วยมือ (การเปลี่ยนแปลงของพวกเขาจะถูกแทนที่) และช่อง input ที่ต้องพิมพ์ `OVERWRITE` (ตัวพิมพ์ถูกแปลงเป็นตัวใหญ่) ปุ่มยืนยันแสดง "Deploy (N)" ซ้ำ โหมด Skip customized deploy โดยไม่ต้องยืนยัน

## 6. UI state ที่เก็บถาวร

| ที่ไหน | อะไร | คงอยู่ |
|---|---|---|
| URL query | `tab` (`system`, `bu_default`, `deploy`) | จนกว่าจะ navigate |
| `localStorage` | หน้านี้ไม่เขียนอะไร | n/a |

การเลือกโมดูล, checkbox ที่เลือก และโหมด deploy รีเซ็ตเมื่อสลับแท็บหรือโหลดซ้ำ

## 7. Screenshots

> **TODO:** Screenshots เลื่อนไปทำในชุด screenshot ของ Platform ที่จะมาถึง ดู `.specs/2026-05-17-screenshots-coverage-checklist.md` สำหรับแผนครอบคลุมข้ามโมดูล

## 8. แหล่งอ้างอิง

- `../carmen-backstage/src/pages/DashboardTemplateManagement.tsx`, `src/pages/dashboardTemplates/{TemplateListPanel,TemplateEditDialog,DeployPanel,OverwriteConfirmDialog,DatasetParamFields}.tsx`, `modules.ts`, `reorderItems.ts`, `deployRowState.ts`
- i18n: `pages.dashboardTemplates.*`
- หน้าข้างเคียง: [Dashboard Templates](/th/backstage/dashboard-templates), [Lifecycle](/th/backstage/dashboard-templates/lifecycle)
