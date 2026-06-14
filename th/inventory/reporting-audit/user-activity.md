---
title: กิจกรรมผู้ใช้ (User Activity)
description: Timeline forensic ที่เน้น actor — login, logout, อายุ session, การเปิดหน้าที่ละเอียดอ่อน — แยกจาก activity ระดับ entity
published: true
date: 2026-05-19T23:55:00.000Z
tags: reporting-audit, activity, security, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# กิจกรรมผู้ใช้ (User Activity)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Security Officer / Auditor (อ่านอย่างเดียว) &nbsp;·&nbsp; **ตาราง:** `tb_user_login_session` (platform) + projection ที่กรองจาก `tb_activity` (tenant) &nbsp;·&nbsp; **Retention:** แถว activity ตามนโยบาย tenant; แถว session ลบที่ `expired_on` &nbsp;·&nbsp; **ใช้โดย:** `/system-admin/user-activity`, compliance export &nbsp;·&nbsp; **Timeline forensic ต่อผู้ใช้ของการ login, logout และการเปิดหน้าที่ละเอียดอ่อน**

![กิจกรรมผู้ใช้ (User Activity) screen](/screenshots/reporting-audit/user-activity.png)

> **ไม่มีตาราง `tb_user_activity` แยกในปัจจุบัน** Surface นี้ถูก **reconstruct** โดยการ join `tb_user_login_session` ฝั่งแพลตฟอร์มกับ `tb_activity` ฝั่ง tenant กรองที่ `action IN ('login', 'logout', 'view')` และ group โดย `actor_id` ตารางแยกอยู่ใน roadmap — mark "(Inferred — ต้องตรวจสอบตาราง)" ต่อฟิลด์ที่มองไปข้างหน้า

## 1. ภาพรวมและผู้ใช้งาน

User Activity คือ **timeline forensic ที่เน้น actor** — ทุก login, logout, การ refresh token, การเปลี่ยน password, การเปลี่ยน role และการเปิดหน้าที่ละเอียดอ่อนต่อผู้ใช้ แตกต่างจาก [reporting-audit/activity](/th/inventory/reporting-audit/activity) ซึ่ง **เน้น entity** (หนึ่งแถวต่อการเปลี่ยนแถวธุรกิจ); user-activity เป็นหนึ่งแถวต่อ **event ของ user-action** ไม่ว่าจะมีการเปลี่ยนแถวธุรกิจหรือไม่

**ผู้ใช้งาน:** **Auditor** (compliance trail), **Sysadmin** (ตรวจสอบ account), **Security Officer** (สืบสวน failed login, chain การ impersonation), **Compliance** (export ที่ระวัง PII ไป SIEM)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| หาประวัติ login ของผู้ใช้ | System Admin → **User Activity** → เลือกผู้ใช้ | view default group ตาม user; drill เข้า timeline ของ session |
| สืบสวน failed login | กรอง **event type = login**, **flag failed-login = true** | `actor_id = NULL`, `meta_data.username_attempted` carry identifier ที่เสนอ |
| ดูเอกสารละเอียดอ่อนที่เปิดใน session | drill เข้า session → timeline แสดง `login → views → logout` | เฉพาะหน้าที่มีสิทธิ์ logged-view เท่านั้นจะ emit แถว `view` |
| Export สำหรับ compliance | เส้นทาง query เดียวกัน → snapshot CSV / JSON | โดยทั่วไปส่งไป SIEM รายไตรมาส |
| ตรวจสอบ chain การ impersonation | เปิด event → `meta_data.impersonation_chain` | ต้องมี grant ของ Security Officer |
| เช็ค activity ของตัวเอง | หน้า profile → tab activity | ผู้ใช้อ่าน timeline ของตัวเองได้ |
| หา reap ของ session ที่หมดอายุ | กรอง `meta_data.cause = 'expired'` | แถว logout สังเคราะห์ที่ emit โดย cleanup job |

## 3. คำถามที่พบบ่อย

| อาการ / คำถาม | สาเหตุ / คำตอบ | การจัดการ |
|---|---|---|
| ทำไมไม่มีตาราง `tb_user_activity`? | Surface ถูก **reconstruct** — session + `tb_activity` ที่กรอง | ดู callout ด้านบน; ตารางแยกอยู่ใน roadmap |
| Session เป็น PII ไหม? | ใช่ — `ip_address` และ `user_agent` เป็น PII ในกฎหมายส่วนใหญ่ | `user_agent` redact เป็น family/version บนหน้าจอ ยกเว้นมี grant ของ Security Officer |
| ทำไมหน้านี้ไม่แสดงทุก page view? | เฉพาะหน้าที่ opt-in view-logging (PR/PO detail, costing, financial report) emit แถว `view` | การ navigate อื่นไม่ถูก log |
| แก้ไขแถวได้ไหม? | ไม่ได้ — `tb_activity` เป็น **immutable post-insert**; `tb_user_login_session` เป็น insert / delete อย่างเดียว | — |
| Failed login มี `actor_id = NULL` — บั๊ก? | โดยตั้งใจ — context ที่ไม่ authenticate identifier อยู่ใน `meta_data.username_attempted` | — |
| Logout ของ session ค้างอยู่ที่ไหน? | Cleanup job emit `logout` สังเคราะห์ด้วย `meta_data.cause = 'expired'` หลัง `expired_on` | — |
| ดูข้าม tenant ได้ไหม? | เฉพาะ Platform Admin, เฉพาะกับสำเนา audit ใน cold storage, ไม่เคยกับตาราง tenant สด | — |

## 4. กรณีพิเศษ

- **Append-only** แถว `tb_activity` เป็น immutable post-insert; `tb_user_login_session` เป็น insert / delete อย่างเดียว ไม่มีเส้นทางแอปอัปเดต event ของ user-activity
- **การจับคู่ Login / logout** Event ของ login และการ insert session เกิดใน transaction เดียวกัน; `entity_id` ตรงกับ `id` ของ session การ logout ลบ session + insert แถว `logout` คู่กัน
- **Session ค้าง** ถูก reap ที่ `expired_on` โดย cleanup job ที่ emit `logout` สังเคราะห์ด้วย `meta_data.cause = 'expired'`
- **เขตเวลา** ทุก timestamp `Timestamptz(6)` UTC; UI render ใน timezone ของ profile ผู้ใช้พร้อม tooltip raw-UTC
- **Retention** `tb_activity` หมดอายุตามนโยบาย tenant (cold storage); แถว session ลบที่ `expired_on` หรือเร็วกว่าตอน logout — ไม่มีการเก็บ session token ระยะยาว
- **RBAC** Timeline ของตัวเองผ่าน profile; หน้าทั่วแพลตฟอร์มจำกัดให้ Sysadmin / Security Officer / Auditor; ข้าม tenant เฉพาะผ่าน cold storage

---

## 5. โมเดลข้อมูล (Dev)

สองตารางประกอบ surface — **ไม่มีตาราง `tb_user_activity` เดียว**

### 5.1 `tb_user_login_session` (platform)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `token` | `String @db.VarChar` | No | session token ที่ออก (หรือ hash reference) |
| `token_type` | `enum_token_type` | No | Default `access_token` `access_token` / `refresh_token` |
| `user_id` | `String @db.Uuid` | No | FK ไป `tb_user.id` |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + 1 day` การหมดอายุของ session |

**Constraints:** unique บน `token` FK ไป `tb_user.id` การ insert แถว = "session เปิด" (login เชิง functional); การลบ / หมดอายุ = "session ปิด" ไม่มี `created_at` / IP / user-agent บนตารางนี้ — อยู่ใน `tb_activity` สำหรับ event login ที่จับคู่กัน

### 5.2 `tb_activity` (tenant) — projection ที่กรอง

กรองที่ `action IN ('login', 'logout', 'view')` และ group โดย `actor_id`

| ฟิลด์ | ใช้เป็น | คำอธิบาย |
| --- | --- | --- |
| `actor_id` | identity ผู้ใช้ | join `tb_user.id` ของแพลตฟอร์ม `NULL` สำหรับ failed login |
| `action` | ประเภท event | `login` / `logout` / `view` สำหรับ user-activity |
| `entity_type`, `entity_id` | เป้าหมาย | สำหรับ `view` คือเอกสารละเอียดอ่อนที่เปิด สำหรับ `login` / `logout` โดยทั่วไป `entity_type = 'session'` กับ `entity_id = tb_user_login_session.id` |
| `ip_address`, `user_agent` | context forensic | แหล่ง canonical สำหรับข้อมูล client (PII — redact ตอนแสดงผล) |
| `meta_data` | เพิ่มเติม | เหตุผล failed login, flag MFA, chain การ impersonate, `cause = 'expired'` สำหรับ logout สังเคราะห์ |
| `created_at` | timestamp ของ event | UTC `Timestamptz(6)` |

ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity) สำหรับนิยามตารางเต็ม

**Inferred — ต้องตรวจสอบ** ตาราง `tb_user_activity` ในอนาคตจะ carry `(user_id, event_type, event_at, ip_address, user_agent, target_type, target_id, meta_data)` พร้อม composite index บน `(user_id, event_at DESC)` และ `(event_type, event_at DESC)`

## 6. กติกาทางธุรกิจ

- **การจับคู่ Login / logout** แถว activity + แถว session insert ใน transaction เดียวกัน; `entity_id` ตรงกับ id ของ session การ logout ลบ session + insert แถว `logout` คู่กัน
- **การจับ Failed login** Insert ด้วย `actor_id = NULL`, `action = 'login'`, `meta_data.success = false`, `meta_data.username_attempted = <offered>` ไม่สร้างแถว session `tb_user.failed_login_count` เพิ่มใน path เดียวกัน
- **การ redact PII** `user_agent` render เป็น family/version ที่ parse แล้วบนหน้าจอ ยกเว้นมี grant ของ Security Officer
- **RBAC** Timeline ของตัวเองผ่าน profile; ทั่วแพลตฟอร์มจำกัดให้ Sysadmin / Security Officer / Auditor; ข้าม tenant เฉพาะผ่าน cold storage
- **Retention** Activity ตามนโยบาย tenant (ย้ายไป cold storage); session ลบที่ `expired_on` หรือเร็วกว่า
- **เขตเวลา** ทุก timestamp UTC; render ใน timezone ของ profile

## 7. ความเชื่อมโยงข้ามโมดูล

- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — ตาราง tenant ที่อยู่เบื้องหลัง; user-activity คือ projection ที่กรอง + join เหนือมันบวก session
- [access-control/user](/th/inventory/access-control/user) — `actor_id` / `user_id` ของ session resolve ผ่าน `tb_user` ของแพลตฟอร์ม
- [access-control/permission](/th/inventory/access-control/permission) — สิทธิ์ view-permission ขับว่าการเปิดหน้าละเอียดอ่อนตัวไหน emit แถว `view`

## 8. แหล่งอ้างอิง

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_login_session` (lines 456-465), `enum_token_type` (577-580), `tb_user` (~360-454)
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (~277-297), `enum_activity_action` (~67-89)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/user-activity/`
- **Authentication middleware:** `../carmen-turborepo-backend-v2/apps/` — handler login / logout เขียนแถว session + activity คู่กัน
