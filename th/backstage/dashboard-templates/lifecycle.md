---
title: Dashboard Templates — Lifecycle
description: การทำงานกับเทมเพลตแดชบอร์ด — create, edit, reorder, delete พร้อมผลข้างเคียงด้านเวอร์ชันและ cache รวมถึงการตรวจสถานะ BU-default และ flow การ deploy ที่รวมการจัดการ 409/422
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, dashboard-templates, lifecycle
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates — Lifecycle

> **At a Glance**
> **Operation:** create · edit · reorder · delete · deploy-status · deploy &nbsp;·&nbsp; **ไม่มีในโมดูลนี้:** hard delete, restore, เวอร์ชันรายโมดูล, การย้อนกลับ deploy, deploy ตามเวลา &nbsp;·&nbsp; **Endpoint:** `/api-system/dashboard-templates` และ `/deploy/:target_bu_code` &nbsp;·&nbsp; **ผลข้ามเอนทิตี:** ตัวนับเวอร์ชัน, cache ของ gateway, `tb_dashboard_bu_widget` ฝั่ง tenant

## 1. ภาพรวม

CRUD ของเทมเพลตเป็นแบบเรียบง่าย พร้อมผลข้างเคียงที่ซ่อนอยู่สองอย่างซึ่งผูกกับ `kind` การ deploy เป็นการทำงานเดียวที่ข้ามฐานข้อมูล: อ่านชุด BU-default จากฐานข้อมูล backstage ผ่าน micro-cluster และเขียนลง tenant ทีละหนึ่งผ่าน micro-data ไม่มี endpoint สำหรับ deploy หลาย BU พร้อมกัน; "deploy ไป N BU" คือ SPA วนเรียก endpoint ของ BU เดียว

## 2. Flow การสร้าง

`POST /api-system/dashboard-templates` (`dashboard_template.create`, backstage-wide) gateway ตรวจ `dataset_id` และ `widget_type` กับแค็ตตาล็อก micro-data ก่อน (422 ถ้า dataset ไม่รู้จักหรือ render ไม่รองรับ) แล้วส่งการเขียนไป micro-cluster micro-cluster เก็บเฉพาะฟิลด์ที่อยู่ใน whitelist (`kind`, `module`, `dataset_id`, `widget_type`, `order_index`, `params`, `display`, รายการ allow/deny, `is_active`) บวกคอลัมน์ title ที่ resolve จาก `title_i18n`/`title` Response: `{ id, doc_version }`

ผลข้างเคียง: `kind = bu_default` เพิ่มเวอร์ชันใน transaction เดียวกัน; `kind = system` ล้าง cache ของ gateway หลัง RPC คืนค่า

## 3. Flow การแก้ไข

`PATCH /:id` (`dashboard_template.update`) gateway อ่าน row ที่เก็บไว้ก่อน แล้วใช้กฎที่ต้องใช้มัน: `allow/deny` บน row `bu_default` และ `module: null` บน row `system` ถูกปฏิเสธด้วย 422; การตรวจ dataset/render ทำเฉพาะเมื่อมีอย่างใดอย่างหนึ่งเปลี่ยน (ใช้ค่าที่ merge แล้ว) จากนั้น micro-cluster update ภายใต้ optimistic locking: `doc_version` เป็นส่วนของ `UPDATE ... WHERE`, ถ้าไม่ตรงจะไม่เขียนอะไรและคืน `ALREADY_EXISTS` ("Dashboard template was modified", 409) ถ้า client ไม่ส่ง `doc_version` การเขียนจะไม่ถูกป้องกัน; SPA ของ backstage ส่งเสมอเมื่อ row มีค่านี้

ฟิลด์ที่เปลี่ยนไม่ได้หลังสร้าง: `kind` (ไม่อยู่ใน whitelist ของ update) `module` อยู่ใน whitelist ของ update ที่ระดับ API แต่ SPA ไม่เคยส่ง

กฎ title ตอน update: ถ้ามี `title_i18n` ตัวนั้นชนะ; `title` แบบเดิมอย่างเดียวจะถูก merge เข้า `title_i18n` ที่เก็บไว้ เพื่อให้ข้อความภาษาไทยไม่หายเมื่อ client เก่าแก้ไข

## 4. Reorder

`PATCH /api-system/dashboard-templates/reorder` พร้อม `{ kind, module, items: [{ id, order_index }] }` (`dashboard_template.update`) micro-cluster นับว่าทุก id เป็น row ที่ยังไม่ถูกลบของ kind และ module นั้น; ถ้ามี id ใดไม่ใช่ ทั้งคำขอจะเป็น `NOT_FOUND` และไม่มีอะไรเปลี่ยน ไม่งั้นจะเขียน `order_index` ทีละตัว และสำหรับ `bu_default` จะเพิ่มเวอร์ชัน SPA กำหนดเลขลำดับใหม่ทั้งรายการของโมดูลเป็น 10, 20, 30... ดังนั้นการคลิกลูกศรหนึ่งครั้งแตะ `order_index` และ `updated_at` ของทุก row

## 5. Delete

`DELETE /:id` (`dashboard_template.delete`) Soft delete: ตั้ง `deleted_at`/`deleted_by_id` การลบ `bu_default` เพิ่มเวอร์ชัน gateway ล้าง cache system-widget ใน**ทุก**การลบไม่ว่า kind ใด (การ invalidate เกินมาแต่ไม่เป็นอันตราย)

## 6. สถานะและ Deploy

### 6.1 การตรวจสถานะ

`GET /deploy/:target_bu_code/status` (`dashboard_template.deploy`) gateway อ่าน snapshot `{version, widgets}` ปัจจุบันจาก micro-cluster ขอ row deploy ของ BU จาก micro-data (`GET /api/dashboard/bu-widgets/deploy-state?bu_code=`) แล้วคืน:

```
{ version, status, deployed_version, deployed_at, customized_at }

status = never        if no deploy row
       = customized   if row.customized_at is set
       = outdated     if row.deployed_version < version
       = current      otherwise
```

สังเกตลำดับ: `customized` ชนะ `outdated`

### 6.2 Deploy

`POST /deploy/:target_bu_code` พร้อม `{ mode, expected_version }` (`dashboard_template.deploy`):

```
snapshot = micro-cluster.getBuDefault()      # version + active bu_default widgets, one RepeatableRead read
if snapshot.version != expected_version  -> 409 "BU default version changed"
if snapshot.widgets is empty             -> 422 "BU default set is empty"
micro-data POST /api/dashboard/bu-widgets/deploy?bu_code&user_id
   body: { mode, version, widgets[module,dataset_id,widget_type,title,title_i18n,order_index,params,display] }
```

ใน micro-data (`service/bu_widget_deploy.go`) transaction ของ tenant หนึ่งอันจะ lock หรือสร้าง row deploy; ถ้า `mode = skip_customized` และ BU เป็น customized จะคืน `{ result: "skipped" }`; ไม่งั้นจะ**soft-delete BU widget ที่มีอยู่ทุกตัว แล้ว insert widget จากเทมเพลต** และทำเครื่องหมาย row ว่า deploy แล้ว (เวอร์ชัน, เวลา, ผู้ทำ; ล้างฟิลด์ customized) และคืน `{ result: "deployed", count }` ในโหมด overwrite BU widget ที่สร้างด้วยมือจึงหายไปทั้งหมด; ไม่มีการ merge

ความสอดคล้องของ snapshot สำคัญ: เวอร์ชันและ widget ถูกอ่านใน transaction `RepeatableRead` เดียว เพื่อไม่ให้การแก้ไขที่เกิดพร้อมกันจับคู่ widget ใหม่กับเวอร์ชันเก่าแล้วหลุดจากการตรวจ 409 (`getBuDefault`, `dashboard-template.service.ts`)

### 6.3 พฤติกรรม batch ของ SPA

| แง่มุม | พฤติกรรม |
|---|---|
| Concurrency | ตรวจสถานะครั้งละ 4; deploy ครั้งละ 3 (`mapWithConcurrency`) |
| 409 ที่ BU ใดก็ตาม | ตั้ง stop flag; BU ที่ยังรอคิวจะไม่เริ่ม; toast "The BU default changed while deploying. The run was stopped; refresh the status and deploy again." |
| 422 ที่ BU ใดก็ตาม | หยุดเหมือนกัน; แสดงข้อความของ backend ใน toast |
| Error อื่น | นับเป็นล้มเหลว, row แสดงข้อความของมัน, การรันดำเนินต่อ; toast สุดท้ายเป็นสรุปบางส่วน |
| ปุ่ม Stop | ยกเลิกคำขอ deploy ที่กำลังทำ (การตรวจสถานะยังดำเนินต่อ) การยกเลิกแค่หยุดให้เบราว์เซอร์รอ; คำขอที่ไปถึง micro-data แล้วอาจยังทำจนเสร็จ ดังนั้นให้ตรวจสถานะซ้ำภายหลัง |
| หลัง deploy แต่ละครั้ง | ดึงสถานะของ row ใหม่ |
| Refresh status | โหลดเวอร์ชันและจำนวน active ใหม่ ล้างผลลัพธ์รายแถวก่อนหน้า ตรวจทุก BU ใหม่ |

## 7. ผลข้างเคียงข้ามเอนทิตี

| Mutation | ผลที่อื่น |
|---|---|
| การเขียน `bu_default` ใด ๆ | เวอร์ชัน +1 ดังนั้นทุก BU ที่ deploy แล้วจะเป็น `outdated` (หรือยังเป็น `customized`) |
| การเขียน `system` ใด ๆ | ล้าง cache ของ gateway; BU เห็นผลในการเรียก `/dashboard-widgets/<module>` ครั้งถัดไป (gateway instance อื่นภายใน TTL 60 วินาที) |
| Deploy | แทนที่ widget ทั้งหมดของ `tb_dashboard_bu_widget` ของ BU หนึ่ง; รีเซ็ต flag customized |
| BU admin แก้ board ของ BU | row ฝั่ง tenant ได้ `customized_at`; การ deploy แบบ `skip_customized` ภายหลังจะข้าม BU นั้น |

## 8. แหล่งอ้างอิง

- Gateway: `.../backstage/backstage_dashboard-templates/{backstage_dashboard-templates.service.ts,dashboard-template-deploy.service.ts,deploy-status-of.ts,micro-data-template.client.ts}`, deploy controller `api-system/dashboard-templates/deploy` (`:target_bu_code/status` บรรทัด 50, `:target_bu_code` บรรทัด 85)
- Micro-cluster: `.../dashboard-template/{dashboard-template.service.ts,dashboard-template-version.ts,dashboard-template-title.ts}`
- Micro-data: `service/bu_widget_deploy.go`, `db/widget_repo.go`
- SPA: `src/pages/dashboardTemplates/DeployPanel.tsx`
- หน้าข้างเคียง: [Dashboard Templates](/th/backstage/dashboard-templates), [Data Model](/th/backstage/dashboard-templates/data-model), [UI Screens](/th/backstage/dashboard-templates/ui-screens)
