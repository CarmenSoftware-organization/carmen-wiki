---
title: Activity Log (หน้าจอ)
description: หน้าจอ /system-admin/activity-log — list/grid view เหนือ tb_activity พร้อม filter action/entity-type/actor, export XLSX, print, และ detail sheet JSON before/after ดิบ ๆ โมเดลข้อมูลอยู่ที่ reporting-audit/activity — หน้านี้บันทึกเฉพาะหน้าจอ
published: true
date: 2026-07-29T11:00:00.000Z
tags: system-config, activity-log, audit, carmen-software
editor: markdown
dateCreated: 2026-07-29T11:00:00.000Z
---

# Activity Log (หน้าจอ)

> **สรุปโดยย่อ**
> **Route:** `/system-admin/activity-log` &nbsp;·&nbsp; **ชื่อบน sidebar:** "Activity Monitor" (`modules.activityLog`) ต่างจาก path segment ของ route เอง &nbsp;·&nbsp; **ตาราง:** `tb_activity` — โมเดลข้อมูลเต็มที่ [reporting-audit/activity](/th/inventory/reporting-audit/activity) &nbsp;·&nbsp; **Permission:** `system_configuration.view` &nbsp;·&nbsp; **หน้านี้บันทึกกลไกของหน้าจอเอง** (view mode, filter, export, detail sheet) — ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity) สำหรับตาราง/enum/กติกาทางธุรกิจ และการยืนยันว่านี่คือ activity UI เดียวที่มีอยู่

![Activity Log screen](/screenshots/activity-log/index.png)

## 1. คืออะไรและใครใช้

นี่คือ**หน้าจอเดียว**ที่อ่าน `tb_activity` — ยืนยันแล้วที่ [reporting-audit/activity](/th/inventory/reporting-audit/activity) ("Read by exactly one screen — `/system-admin/activity-log`. No embedded per-document 'Activity drawer' was found anywhere") ถูกจัดไว้ในที่นี้ภายใต้ System Configuration เพราะเป็นหนึ่งในหน้าจอที่ route ไว้ภายใต้ `/system-admin/*` (ข้าง [workflow](/th/inventory/system-config/workflow), [period](/th/inventory/system-config/period) ฯลฯ) — หน้านี้จำกัดขอบเขตไว้ที่**พฤติกรรมของหน้าจอเอง**; entity ที่อยู่เบื้องหลัง, enum ของมัน, และกติกาทางธุรกิจของมัน ถูกบันทึกไว้ครั้งเดียวที่ [reporting-audit/activity](/th/inventory/reporting-audit/activity) และไม่ทำซ้ำที่นี่

หน้าจอนี้มี rendering mode สองแบบ (list และ card/grid), filter สามแกน (action, entity type, actor), free-text search, export XLSX, browser print, และ detail sheet แบบเลื่อนเข้ามาแสดง JSON ดิบของ `old_data`/`new_data` สำหรับแถวที่เลือก

**ดูแลโดย** audit service แบบ append-only (ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity)) **อ่านโดย** Sysadmin / auditor ที่เข้าดูหน้าจอนี้

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สลับระหว่าง list กับ grid view | Toolbar → toggle icon list/grid | Desktop เท่านั้น — บนมือถือหน้าจอใช้ layout grid/card เสมอไม่ว่า toggle นี้จะเป็นอะไร |
| กรองตาม action | Multi-select Action | 5 option ที่ curate ไว้ (`create`, `update`, `delete`, `login`, `logout`) จาก 20 ค่า enum — ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity) §5.1 สำหรับ enum เต็ม |
| กรองตาม entity type | Multi-select Entity Type (ค้นหาได้) | ~13 ค่าที่ curate ไว้; `entity_type` เองเป็น free-form ดังนั้นค่าอื่นอาจมีอยู่ในข้อมูลโดยไม่มี filter chip ตรงกัน |
| กรองตามผู้ใช้ (actor) | Multi-select User (ค้นหาได้) | มาจาก `useAllUsers()` — ผู้ใช้ทุกคนใน tenant ไม่ใช่แค่คนที่ปรากฏใน log |
| ค้นหา free-text | ช่อง Search | รวมกับ filter สามแกน (query param ทั้งหมด merge เป็น request เดียว) |
| Toggle คอลัมน์ตาราง (list view เท่านั้น) | ไอคอน Columns → popover column-visibility | ไม่มีใน grid view |
| Export view ที่ filter อยู่ | ปุ่ม **Export** | XLSX ฝั่ง client (`useExportActivityLog`) query param เดียวกับ list บนจอ; คอลัมน์: Date, Action, Entity Type, Entity ID, User, IP Address, Description |
| Print | ปุ่ม **Print** | Print ของ browser เอง (`window.print()`) — ไม่ใช่รายงานที่ format ไว้ |
| ดูรายละเอียดของแถว | คลิกแถว / card | เปิด detail sheet — ดู §4 |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ | สาเหตุ | ยืนยันแล้วหรือไม่ |
|---|---|---|
| Grid/card view ใช้ infinite scroll แทน pagination | Desktop โหมด **grid** และ**มือถือทุกกรณี** (ไม่ว่า toggle list/grid จะเป็นอะไร) เปลี่ยนไปใช้ `useGridPagination` (infinite scroll แบบ sentinel); มีแค่ desktop โหมด **list** ที่ใช้ `DataGridPagination` แบบแบ่งหน้าคลาสสิก | **ยืนยันแล้ว** — `useInfiniteScroll = isMobile || displayMode === "grid"` ใน `activity-log-component.tsx` และสอง branch เรียก hook คนละตัว (`useActivityLog` กับ `useGridPagination`) |
| ปุ่ม Export ถูก disable พร้อม spinner | กำลัง export อยู่ (`isExporting`) | **ยืนยันแล้ว** |
| Toast `exportNoData` ตอน Export | Query ที่ filter อยู่คืนแถวว่าง | **ยืนยันแล้ว** |
| จำนวน badge บนไอคอน filter-sheet มือถือ | นับค่าที่เลือกแต่ละตัวจากทั้งสาม filter ไม่ใช่นับ*ประเภท*ของ filter | **ยืนยันแล้ว** — `activeFilters.length` หนึ่งรายการต่อค่าที่เลือกหนึ่งตัว |

## 4. กรณีพิเศษ

- **มี list-rendering path สองแบบที่เป็นอิสระต่อกัน ไม่ใช่ component เดียวที่ใช้ร่วมกันพร้อม flag view-mode** List mode fetch ผ่าน `useActivityLog` (page param แบบคลาสสิก) *เฉพาะเมื่อ* `!useInfiniteScroll`; grid/mobile mode fetch ผ่าน `useGridPagination` (`loadMore` แบบ sentinel-trigger) *เฉพาะเมื่อ* `useInfiniteScroll` เป็นจริง — hook ทั้งสองยิงไปที่ endpoint เดียวกันแต่กลไก pagination ต่างกัน และ component render `<DataGrid>` หนึ่งตัว หรือ card grid หนึ่งตัวแบบมีเงื่อนไข ไม่เคย render ทั้งคู่พร้อมกัน
- **Detail sheet แสดง JSON ดิบสองบล็อก ไม่ใช่ diff ที่คำนวณไว้** Sheet (`activity-log-detail-sheet.tsx`) pretty-print `old_data` และ `new_data` เคียงข้างกันผ่าน `JsonBlock` renderer ธรรมดา — ไม่มีการ highlight ระดับ field (ไม่พบการคำนวณ "ฟิลด์ที่เปลี่ยน" ใด ๆ) [reporting-audit/activity](/th/inventory/reporting-audit/activity) อธิบายสิ่งนี้ว่า "the closest equivalent to a diff old vs new view" — ถูกต้อง แต่ควรระบุให้ชัดว่าเป็นบล็อก JSON ดิบสองบล็อก ไม่ใช่ diff ที่คำนวณไว้
- **Sidebar เรียก module นี้ว่า "Activity Monitor" ไม่ใช่ "Activity Log"** `modules.activityLog` ในไฟล์แปล resolve เป็น `"Activity Monitor"` — path segment ของ route (`/system-admin/activity-log`) และ title บนหน้า (`systemAdmin.activityLog.title` → ก็ `"Activity Monitor"` เช่นกัน) สอดคล้องกันเอง แต่ต่างจาก URL slug และชื่อของหน้า wiki นี้เอง ไม่มีผลต่อการทำงาน แค่บันทึกไว้เพื่อไม่ให้สับสนตอนอ้างอิง screenshot หรือ nav ข้าม
- **ไม่มี permission ที่ละเอียดกว่า `system_configuration.view`** ทุก sidebar entry ของ `/system-admin/*` — รวมถึงตัวนี้ — gate ด้วย permission key เดียวกันตัวเดียว (`constant/module-list.ts`); ไม่มี permission อ่าน/export เฉพาะของ activity-log
- **List filter ของ Actor ไม่ได้จำกัดเฉพาะ actor ที่ปรากฏใน log จริง** `useAllUsers()` คืนผู้ใช้ทุกคนใน tenant ดังนั้น filter Actor อาจแสดงชื่อที่ไม่มีแถว activity ตรงกันเลย

---

## 5. โมเดลข้อมูล — ตั้งใจไม่ทำซ้ำ

หน้านี้**ตั้งใจไม่**ทำซ้ำตาราง field ของ `tb_activity`, ค่าของ `enum_activity_action`, หรือกติกาทางธุรกิจ (append-only, ไม่มีการบังคับ FK บน `entity_id`, นโยบาย retention ฯลฯ) — ทั้งหมดนี้เป็นทางการที่ [reporting-audit/activity](/th/inventory/reporting-audit/activity) §5-§6 การทำซ้ำที่นี่จะเสี่ยงให้สองหน้าเพี้ยนออกจากกัน หน้านี้ link ไปแทน

Type เฉพาะของหน้าจอที่ควรพูดถึง: interface `ActivityLog` ของ frontend (`types/activity-log.ts`) แบน field ของ actor จาก response ของ API (`actor_username`, `actor_firstname`, `actor_middlename`, `actor_lastname`) และอ่าน timestamp การสร้างจาก path ที่ nest อยู่ `audit.created.at` แทนที่จะเป็น `created_at` ระดับบนสุด — `getLogCreatedAt()` มีไว้เพื่อดึงค่า nested นั้นออกมาสำหรับทั้งคอลัมน์วันที่บนจอและการ export XLSX

## 6. ความเชื่อมโยงข้ามโมดูล

- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — โมเดลข้อมูล `tb_activity` ที่เป็นทางการ, `enum_activity_action`, กติกาทางธุรกิจ, และการยืนยันว่าหน้าจอนี้เป็น activity UI เดียวในผลิตภัณฑ์
- [reporting-audit/user-activity](/th/inventory/reporting-audit/user-activity) — หน้าจอพี่น้อง `/system-admin/user-activity`: มุมมองที่กรองต่อผู้ใช้ฝั่ง client เหนือตาราง `tb_activity` เดียวกัน (ไม่ใช่ตารางแยกหรือ join สองตาราง)
- [system-config](/th/inventory/system-config) — module แม่; §3 Entity List จัดหน้านี้ไว้ข้างหน้าจอ `/system-admin/*` จริงอื่น ๆ
- [access-control/user](/th/inventory/access-control/user) — แหล่งของ list ผู้ใช้ใน filter Actor

## 7. แหล่งอ้างอิง

- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/activity-log/activity-log.route.tsx`, `activity-log-component.tsx`, `activity-log-card.tsx`, `activity-log-detail-sheet.tsx`, `use-activity-log-table.tsx`
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-activity-log.ts` — `useActivityLog()`, `useExportActivityLog()`; `types/activity-log.ts` — `ActivityLog`, `getLogCreatedAt()`
- **Nav entry:** `../carmen-inventory-frontend-react/constant/module-list.ts` — `activityLog`, `permission: PERMISSIONS.system_configuration.view`
- **Translations:** `../carmen-inventory-frontend-react/messages/en.json` — `systemAdmin.activityLog.*` (`title: "Activity Monitor"`), `modules.activityLog`
- **ตาราง/enum/กติกา (ไม่ทำซ้ำที่นี่):** ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity) §8 สำหรับการอ้างอิง Prisma/frontend/writer ของตัวเอง
