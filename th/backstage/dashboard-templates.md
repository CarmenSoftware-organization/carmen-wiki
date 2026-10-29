---
title: Dashboard Templates (เทมเพลตแดชบอร์ด)
description: เทมเพลต widget แดชบอร์ดที่แพลตฟอร์มจัดการ — widget "system" แบบอ่านอย่างเดียวที่แสดงบนแดชบอร์ดโมดูลของทุก BU และชุด "BU default" ที่มีเวอร์ชันซึ่งเจ้าหน้าที่ deploy เข้าแดชบอร์ดของแต่ละ business unit
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, dashboard-templates
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates (เทมเพลตแดชบอร์ด)

โมดูล **Dashboard Templates** ให้เจ้าหน้าที่แพลตฟอร์มตัดสินใจได้ว่า widget แดชบอร์ดตัวไหนที่ทุก business unit จะเห็น โดยไม่ต้องมีใครตั้งค่าทีละ BU เทมเพลตหนึ่งตัวคือคำนิยาม widget หนึ่งอัน: **dataset** จากแค็ตตาล็อกของ micro-data, **render type** (KPI, line, bar, ...), ชื่อสองภาษา, พารามิเตอร์ของ dataset (ถ้ามี) และตำแหน่ง เทมเพลตมีสองชนิดที่ทำงานต่างกันมาก:

| ชนิด | ปรากฏที่ไหน | ไปถึง BU อย่างไร |
|---|---|---|
| **System** (`system`) | หน้าแดชบอร์ดรายโมดูล (procurement, inventory, product, config, vendor-management, operation-plan, store-operation) ของ**ทุก** BU แบบอ่านอย่างเดียว | gateway อ่านสดตอนมี request ผ่าน cache 60 วินาที; จำกัดรายBU ได้ด้วยรายการ code แบบ allow/deny |
| **BU default** (`bu_default`) | board widget ของ BU เองที่แก้ไขได้ (`tb_dashboard_bu_widget`) รวมถึงหน้า `/dashboard` หลัก | ถูก**คัดลอก**เข้าฐานข้อมูล tenant ของ BU ด้วย action **Deploy** ที่สั่งชัดเจน และติดตามเทียบกับหมายเลขเวอร์ชันส่วนกลางหนึ่งค่า |

> **At a Glance**
> **หน้าจอ:** `DashboardTemplateManagement` พร้อมแท็บ System / BU default / Deploy &nbsp;·&nbsp; **Route:** `/dashboard-templates` (`?tab=system|bu_default|deploy`) &nbsp;·&nbsp; **Nav:** กลุ่ม `navGroup.content`, `permission: 'dashboard_template.read'`, `feature: 'dashboard_templates'` (`backstageNav.ts:30`) &nbsp;·&nbsp; **Permission key:** `dashboard_template.read` / `.create` / `.update` / `.delete` / `.deploy` &nbsp;·&nbsp; **API:** `/api-system/dashboard-templates[/...]` &nbsp;·&nbsp; **ตาราง:** `tb_dashboard_widget_template`, `tb_dashboard_bu_default_version` &nbsp;·&nbsp; **หน้าย่อย:** 3 &nbsp;·&nbsp; **e2e suite:** ไม่มี

## 1. ภาพรวม

หน้านี้คือ route เดียวที่มี `TabStrip` แท็บ **System** และ **BU default** ใช้ `TemplateListPanel` ร่วมกัน (ตัวเลือกโมดูล, ตาราง widget, ลูกศรจัดลำดับ และ dialog เพิ่ม/แก้ไข); **Deploy** เป็น `DeployPanel` แยกต่างหากที่แสดง business unit ทุกแห่งพร้อมสถานะ deploy แท็บ Deploy ถูกซ่อนเว้นแต่ผู้ดูจะมี `dashboard_template.deploy`; URL `?tab=deploy` โดยไม่มี permission นั้นจะ fallback ไปที่ System (`DashboardTemplateManagement.tsx`)

โมดูลนี้ไม่มี *ตัวออกแบบ* widget ทุกอย่างที่เทมเพลต render ได้มาจากแค็ตตาล็อก dataset ที่ micro-data เป็นเจ้าของ (`GET /api/dashboard-lab/datasets` ซึ่งเข้าถึงผ่าน `GET /api-system/dashboard-templates/datasets`): แต่ละ dataset ประกาศรูปร่าง พารามิเตอร์ และ render type ที่รองรับ และ dialog เสนอเฉพาะชุดที่ใช้ได้ นี่คือ registry เดียวกับที่แดชบอร์ดของ inventory ใช้ ดู §6

## 2. บริบททางธุรกิจ

โรงแรมใน cluster ควรเปิด Carmen แล้วเจอแดชบอร์ดที่สมเหตุสมผลตั้งแต่วันแรก และเจ้าหน้าที่แพลตฟอร์มควรปล่อย KPI ใหม่ให้ทุกพร็อพเพอร์ตี้ได้ มีสองกลไกรองรับสองความต้องการนี้:

- **System widget** คือไทล์ "ที่มีอยู่เสมอ" เพราะอ่านสด การเปลี่ยนตัวหนึ่ง (หรือสลับเป็น inactive) จึงปรากฏกับทุก BU โดยไม่ต้องทำอะไรรายBU: gateway ล้าง cache ทุกครั้งที่มีการเขียน system และ cache TTL คือ 60 วินาที (`TTL_MS`, `system-widget-cache.service.ts`) cache อยู่ใน process เดียว ดังนั้นเมื่อมี gateway หลาย instance ตัวอื่น ๆ จะตามทันก็ต่อเมื่อ TTL ของตัวเองหมด
- **BU default widget** คือ board เริ่มต้น เมื่อ deploy แล้ว BU เป็นเจ้าของสำเนา และแก้ไขได้ จากนั้นเจ้าหน้าที่ตัดสินใจรายBU ว่าการ redeploy ภายหลังจะเขียนทับการแก้ไขเหล่านั้นได้หรือไม่ (§4)

## 3. แนวคิดสำคัญ

### 3.1 โมดูล

`module` เป็นหนึ่งใน `procurement`, `inventory`, `product`, `config`, `vendor-management`, `operation-plan`, `store-operation` (`DASHBOARD_MODULES`, `dashboardTemplates/modules.ts`) สำหรับเทมเพลต `bu_default` ตัวเลือกจะเพิ่ม **Main** ซึ่งใน wire format ส่งเป็น `module: null` และหมายถึงหน้า `/dashboard` หลักของ BU กฎที่ API และ CHECK ของฐานข้อมูลบังคับ: **`module = null` อนุญาตเฉพาะ `bu_default`**; เทมเพลต system ต้องระบุโมดูล

### 3.2 กฎ System vs BU default

| กฎ | แหล่งที่มา |
|---|---|
| `allow_business_unit` / `deny_business_unit` ใช้กับ `system` เท่านั้น; การเขียน `bu_default` ที่มีรายการไม่ว่างจะถูกปฏิเสธ | create: DTO refine (`dashboard-template.dto`); edit: `validateUpdate`, 422 |
| การมองเห็น widget system สำหรับ BU code `X`: deny list ชนะ; allow list ที่ว่าง/null หมายถึงทุกคน ไม่งั้น `X` ต้องอยู่ในนั้น | `visibleToBu` (`dashboard-widgets/visible-to-bu.ts`) |
| `dataset_id` ต้องมีอยู่ในแค็ตตาล็อก micro-data และ `widget_type` ต้องอยู่ใน `supported_renders` ของ dataset นั้น ไม่งั้น 422 ("Unknown dataset", "cannot render as ...") | `validateAgainstCatalog` |
| ต้องมี title `en` เสมอเมื่อมี title `th` | dialog guard + `normalizeTitleI18n` |
| JSON `display` ต้อง serialize แล้วไม่เกิน 8 KB | zod refine ตอน create/update |
| การ create/update/delete/reorder ใด ๆ ของ row `bu_default` จะเพิ่มเวอร์ชัน BU-default ส่วนกลางขึ้น 1 | `bumpBuDefaultVersion`, ใน transaction เดียวกับการเขียน |
| การเขียน row `system` ล้าง cache system-widget ของ gateway ทันที | `systemWidgetCache.invalidate()` |

### 3.3 Title

title ถูกเก็บสองครั้ง: `title` แบบเดิม (= ภาษาอังกฤษ) และ `title_i18n` (`{ en, th? }`) SPA เขียนทั้งสอง ในรายการ row ที่ไม่มี title จะ fallback ไปที่ชื่อของ dataset โดยมีป้าย "(Dataset name)" badge ที่หัวแสดงความครอบคลุมภาษาไทย ("Thai titles n/m") และเปลี่ยนเป็นสีเหลืองอำพันเมื่อมี row ที่มี title แต่ไม่มีภาษาไทย

## 4. การ Deploy BU default (สรุป)

Deploy ส่งชุด BU-default ที่ **active** ไปยัง business unit ที่เลือก แต่ละ BU มีสถานะที่ได้จาก row deploy ใน tenant และเวอร์ชันปัจจุบัน:

| สถานะ | ความหมาย |
|---|---|
| `never` | BU ไม่มี row deploy; ไม่เคย deploy อะไรเลย |
| `customized` | BU admin แก้ board หลัง deploy ครั้งล่าสุด (`customized_at` ถูกตั้ง) |
| `outdated` | เคย deploy แล้ว เวอร์ชันที่ deploy ต่ำกว่าเวอร์ชันปัจจุบัน และไม่ได้ customized |
| `current` | deploy ที่เวอร์ชันปัจจุบัน |

สองโหมด: **skip_customized** (ค่าเริ่มต้น; BU ที่ถูกทำเครื่องหมาย customized จะถูกข้าม) และ **overwrite** (แทนที่ widget ของ BU; dialog บังคับให้พิมพ์ `OVERWRITE`) flow เต็ม, concurrency และ failure mode อยู่ใน [Lifecycle](/th/backstage/dashboard-templates/lifecycle)

## 5. Permissions

| Action | Key ที่ต้องมี | หมายเหตุ |
|---|---|---|
| เปิดหน้า, แสดงเทมเพลต, แสดง dataset, อ่านเวอร์ชัน | `dashboard_template.read` | |
| เพิ่ม widget | `dashboard_template.create` | API ต้องการ grant ระดับ backstage ทั้งระบบด้วย |
| แก้ไข, **จัดลำดับ** | `dashboard_template.update` | ลูกศรจัดลำดับอยู่ใน `<Can>` เดียวกับ Edit |
| ลบ | `dashboard_template.delete` | |
| แท็บ Deploy, สถานะ deploy, deploy | `dashboard_template.deploy` | endpoint สถานะ gate ด้วย `deploy` ไม่ใช่ `read` |

endpoint เขียนและ deploy ใช้ `BackstagePermissionGuard` ร่วมกับ `BackstageWidePermissionGuard` ดังนั้น grant ที่จำกัดใน cluster ไม่นับ (super-admin หรือ grant ระดับ backstage ทั้งระบบเท่านั้น) การตรวจฝั่ง SPA ส่ง `BACKSTAGE_SCOPED_RECORD`

**Role เริ่มต้น** (`seed.backstage-role-permission.data.ts`): Backstage Admin ถือ `dashboard_template.*` (รวม `deploy`); Support Manager และ Support Staff ถือแค่ `dashboard_template.read`: เห็นแท็บ System และ BU default โดยไม่มีปุ่ม และไม่เห็นแท็บ Deploy เลย; Security Officer ไม่ถือเลย

## 6. ความสัมพันธ์กับแดชบอร์ดของ Inventory

ตรวจสอบจาก source ไม่ใช่การอนุมาน:

- แค็ตตาล็อก dataset ที่ dialog เทมเพลตเสนอคือตัวที่ micro-data เสิร์ฟที่ `/api/dashboard-lab/datasets` ซึ่งเป็น registry เดียวกับที่ document ใน [Dashboard Dataset](/th/inventory/system-config/dashboard-dataset) และถูกใช้โดยตัวเลือก widget ของ [Dashboard](/th/inventory/dashboard) ของ inventory ([Widget Workspace](/th/inventory/dashboard/widget-workspace))
- เทมเพลต system ถูกเสิร์ฟให้ tenant โดย `GET /api/:bu_code/dashboard-widgets/<module>` (เช่น `/inventory`) โดยแต่ละรายการรวมกับค่า dataset แบบสด (`system-widgets.controller.ts`, `SystemWidgetCache.forBu`)
- BU default ที่ deploy แล้วลงตาราง tenant `tb_dashboard_bu_widget` ซึ่ง document จากฝั่ง tenant ใน [Reporting Audit: Widget](/th/inventory/reporting-audit/widget) หน้านั้นระบุว่าปัจจุบันไม่มีหน้าจอ inventory ใดอ่าน BU widget; pipeline deploy ที่นี่ก็ยังเขียนมันอยู่

## 7. Edge Cases

| กรณี | พฤติกรรม |
|---|---|
| Dataset ถูกลบออกจากแค็ตตาล็อก | row ยังอยู่; รายการแสดง badge แดง "Dataset no longer exists" เมื่อโหลดแค็ตตาล็อกสำเร็จแล้ว (`datasetMissing`) มี migration ชื่อ `20261006120000_dashboard_template_dead_dataset_ids` สำหรับ id ที่ไม่มีในแค็ตตาล็อกอีกต่อไป |
| เปลี่ยน dataset ใน dialog | Widget type รีเซ็ตเป็น render แรกที่ dataset ใหม่รองรับ; params รีเซ็ตเป็นค่าเริ่มต้นของ dataset |
| Reorder | สลับกับตัวข้างเคียงและกำหนดเลขลำดับใหม่ทั้งโมดูลเป็น 10, 20, 30...; ลูกศรถูก disable ที่ปลายทั้งสอง |
| Deploy ขณะที่ชุดว่าง | แท็บ Deploy แสดง alert สีแดงและ disable ปุ่ม; API ตอบ 422 |
| มีคนแก้ BU default ระหว่าง deploy | เวอร์ชันไม่ตรงกับ `expected_version` อีกต่อไป: 409, ทั้งการรันหยุด (ดู Lifecycle) |
| ลบเทมเพลต | Soft delete; การลบ BU-default ก็เพิ่มเวอร์ชันด้วย ดังนั้นทุก BU ที่ deploy แล้วจะกลายเป็น `outdated` |

## 8. หน้าย่อย

- [Data Model](/th/backstage/dashboard-templates/data-model) - ตารางเทมเพลต, ตารางเวอร์ชัน, row deploy ฝั่ง tenant
- [UI Screens](/th/backstage/dashboard-templates/ui-screens) - สามแท็บ, dialog, คอลัมน์
- [Lifecycle](/th/backstage/dashboard-templates/lifecycle) - ผลข้างเคียงของ CRUD, การเพิ่มเวอร์ชัน, สถานะและ flow การ deploy

## 9. แหล่งอ้างอิง

- SPA: `../carmen-backstage/src/pages/DashboardTemplateManagement.tsx`, `src/pages/dashboardTemplates/*`, `src/services/dashboardTemplateService.ts`, `src/types/index.ts` (`DashboardTemplate`, บรรทัด 2010)
- Gateway: `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_dashboard-templates/` (`api-system/dashboard-templates`, deploy ใต้ `api-system/dashboard-templates/deploy`)
- Micro-cluster: `apps/micro-cluster/src/cluster/dashboard-template/` Micro-data: `micro-data/service/bu_widget_deploy.go`
- ที่เกี่ยวข้อง: [Report Templates](/th/backstage/report-templates) (โมดูลอีกตัวในกลุ่ม "Content"), [Feature Flags](/th/backstage/feature-flags)
