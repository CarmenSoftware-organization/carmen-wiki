---
title: กิจกรรมผู้ใช้ (User Activity)
description: Timeline login/logout ที่เน้น actor สร้างขึ้นทั้งหมดจากแถว tb_activity tb_user_login_session (ที่เคยบันทึกไว้ว่าเป็นครึ่งหนึ่งของโมเดลข้อมูล) เป็นตารางที่ตายแล้ว ไม่มีการอ้างอิงจากโค้ดนอกเหนือจาก schema เลย — JWT ที่ Keycloak ออกให้คือ mechanism session ที่แท้จริง ไม่มีตาราง session ในเครื่องรองรับ
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, activity, security, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# กิจกรรมผู้ใช้ (User Activity)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Auditor (อ่านอย่างเดียว) &nbsp;·&nbsp; **ตาราง:** `tb_activity` กรองที่ `action IN ('login','logout')` — **ไม่ใช่** `tb_user_login_session` ซึ่งตายแล้ว &nbsp;·&nbsp; **ผู้เขียนที่ยืนยันแล้ว:** `AuthService.logAuthActivity()` ของ `micro-business` scope เฉพาะ business unit เริ่มต้นของผู้ใช้เท่านั้น &nbsp;·&nbsp; **ใช้โดย:** `/system-admin/user-activity` &nbsp;·&nbsp; **มีเฉพาะ login/logout — ไม่มีการ log page-view หรือ failed-login ที่ยืนยันแล้ว**

![กิจกรรมผู้ใช้ (User Activity) screen](/screenshots/reporting-audit/user-activity.png)

## สถานะการทำงานจริง (ตรวจสอบเมื่อ 2026-07-22)

หน้านี้ฉบับก่อนหน้าบันทึก `tb_user_login_session` (platform schema) ว่าเป็นหนึ่งในสองตารางที่ประกอบ surface นี้ พร้อมตาราง field แบบละเอียดและ semantic "การ insert แถว = session เปิด... การลบ/หมดอายุ = session ปิด" การค้นหาโค้ดทั่ว `carmen-turborepo-backend-v2/apps` พบว่า **ไม่มีการอ้างอิง `tb_user_login_session` เลย** นอกเหนือจากการประกาศ Prisma model ของมันเอง — ตายแล้ว รูปแบบเดียวกับที่ยืนยันแล้วสำหรับ `tb_attachment`, `tb_report_schedule` และตระกูล `tb_widget_*` เดิม ระบบนี้ authenticate ผ่าน **Keycloak** (`KEYCLOAK_SERVICE` client proxy ใน `AuthService` ของ `micro-business`) และออก JWT access/refresh token โดยตรง — ไม่มีตาราง session ในเครื่องรองรับการ login เลย

สิ่งที่**ยืนยันแล้วว่ามีอยู่จริง**: `AuthService.login()` เรียก `logAuthActivity('login', ...)` เมื่อ authenticate สำเร็จ และ `AuthService.logout()` เรียก `logAuthActivity('logout', ...)` — ทั้งคู่เขียนแถว `tb_activity` (`entity_type: 'auth'`) ไปยัง business unit **เริ่มต้น**ของผู้ใช้เท่านั้น (แถว `tb_user_tb_business_unit` ที่ `is_default: true`; ถ้าผู้ใช้ไม่มี BU เริ่มต้น การเขียนจะถูกข้ามไปทั้งหมด และ log เป็นระดับ debug ไม่ใช่ error) ทั้งสองการเรียกถูกห่อด้วย try/catch ของตัวเองที่ log ความล้มเหลวโดยไม่ทำให้ request login/logout ล้มเหลวตาม

**ยังไม่ยืนยันในรอบนี้:** การจับ failed-login (สาขาความล้มเหลวของ `login()` — rate-limited, user not found — return ก่อนเรียก `logAuthActivity` เลย ไม่มีแถว `tb_activity` เขียนสำหรับความพยายามที่ล้มเหลว), การ log "view" หน้าที่ละเอียดอ่อน (การค้นหาผู้เรียก `logTenantEvent`/`logEvents` ทั่ว repo พบเฉพาะ login/logout ของ auth และ event upload-delete รูปสินค้า/สูตรอาหาร — ไม่เคยมี `action: 'view'`), การติดตาม chain การ impersonation และ event MFA/การเปลี่ยน role ทั้งหมดนี้เคยถูกบันทึกไว้ว่ามีอยู่จริง และตอนนี้ถูกทำเครื่องหมายว่ายังไม่ยืนยัน/น่าจะไม่มีจริงด้านล่าง

## 1. ภาพรวมและผู้ใช้งาน

User Activity คือ **timeline login/logout ต่อผู้ใช้** — ยืนยันแล้วว่าครอบคลุมเพียงสอง event (`login`, `logout`) แต่ละอันเขียนหนึ่งครั้งต่อการ authenticate สำเร็จหรือการเรียก logout หนึ่งครั้ง scope ด้วย business unit เริ่มต้นของผู้ใช้ แตกต่างจาก [reporting-audit/activity](/th/inventory/reporting-audit/activity) เพียงตรงที่หน้านี้กรองล่วงหน้าไปที่สองค่า `action` นั้นและ group โดย `actor_id` เท่านั้น — ไม่ใช่ตารางแยกหรือเส้นทางการเขียนแยก

**กลุ่มผู้ใช้:** Sysadmin / Auditor ผ่าน `/system-admin/user-activity` — ไม่พบ role "Security Officer" ที่แยกออกมาหรือ gate ใด ๆ ทั้งใน frontend หรือ permission decorator ของ backend-gateway สำหรับหน้าจอนี้ — ถือว่า persona label นั้นยังไม่ยืนยัน

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดูประวัติ login/logout | `/system-admin/user-activity` | ใช้ list component เดียวกับ [reporting-audit/activity](/th/inventory/reporting-audit/activity) กรองล่วงหน้าด้วย `entity_type = "auth"` ที่ client — เรียก endpoint `ACTIVITY_LOGS` เดียวกัน ไม่ใช่ API แยก |
| กรองเฉพาะ login หรือ logout | Filter **Action** (Login / Logout เท่านั้น — 2 ตัวเลือก) | query param `action` ที่ server-side |
| กรองตามผู้ใช้ | Filter **User** (actor) | multi-select บน `useAllUsers()` |
| Export สำหรับ compliance | ปุ่ม **Export** | export XLSX แบบ client-side, query params เดียวกัน |
| ตรวจดูหนึ่งแถว | คลิกแถว | เปิด `UserActivityDetailSheet` (render `meta_data`/`old_data`/`new_data` เหมือน detail sheet ของ activity ทั่วไป) |
| **ไม่มี / ยังไม่ยืนยัน** | — | การ drill-down timeline ของ session, การสืบสวน failed-login, การตรวจสอบ chain การ impersonation, tab "activity ของตัวเอง" บน profile, การกรอง session reap ที่หมดอายุ — ไม่มีสิ่งใดมี mechanism เบื้องหลังที่ยืนยันแล้ว (ดูสถานะการทำงานจริงด้านบน) |

## 3. คำถามที่พบบ่อย

| อาการ / คำถาม | สาเหตุ / คำตอบ | การจัดการ |
|---|---|---|
| ทำไมไม่มีตาราง `tb_user_activity`? | ไม่เคยมีเป็นแนวคิดแยกเลย — หน้าจอนี้คือตาราง `tb_activity` เดียวกับ [reporting-audit/activity](/th/inventory/reporting-audit/activity) กรองล่วงหน้าเป็น `entity_type = "auth"` | ไม่ใช่ "การ reconstruct จากสองตาราง" — `tb_user_login_session` (ตารางที่สองที่เคยอ้างว่ามี) ตายแล้ว |
| ทำไมความพยายาม login ที่ล้มเหลวไม่ปรากฏที่นี่? | สาขาความล้มเหลวของ `AuthService.login()` (rate-limited, user not found) return ก่อนที่ `logAuthActivity()` จะถูกเรียกเลย | ไม่มีเส้นทางโค้ดที่ยืนยันแล้วบันทึกความพยายามที่ล้มเหลว — ถือว่าข้อกล่าวอ้างก่อนหน้าเรื่องแถว failed-login ที่ `actor_id = NULL` ยังไม่ยืนยัน |
| ทำไมหน้านี้ไม่แสดง page view? | ไม่พบการเขียน `action: 'view'` ที่ไหนใน backend เลย — ผู้เรียก `logTenantEvent`/`logEvents` จำกัดอยู่ที่ login/logout ของ auth และ event รูปสินค้า/สูตรอาหาร | การ log page-view ที่ละเอียดอ่อนไม่มีอยู่ในระบบปัจจุบัน |
| แก้ไขแถวได้ไหม? | ไม่ได้ — `tb_activity` เป็น append-only; มีเพียงฟิลด์สถานะที่เกี่ยวกับ lifecycle บนตารางอื่นเท่านั้นที่ถูกอัปเดต ไม่เคยเป็นตารางนี้ | — |
| Login/logout ครอบคลุมทุก business unit ที่ผู้ใช้เป็นสมาชิกไหม? | ไม่ครอบคลุม — `logAuthActivity()` เขียนเฉพาะไปยัง business unit **เริ่มต้น**ของผู้ใช้เท่านั้น (`is_default: true`); ถ้าไม่มี BU เริ่มต้นตั้งไว้ การเขียนจะถูกข้าม | Login/logout activity ของผู้ใช้จะมองไม่เห็นจากหน้าจอของ BU ที่ไม่ใช่ default เลย |
| ดูข้าม tenant ได้ไหม? | ยังไม่ยืนยันในรอบนี้ — ไม่พบ mechanism cold-storage ข้าม tenant ใด ๆ | ถือว่ายังไม่ยืนยันแทนที่จะเป็นฟีเจอร์ที่บันทึกไว้ |

## 4. กรณีพิเศษ

- **มีเพียงสอง action ที่ยืนยันแล้ว: `login` และ `logout`** ทั้งคู่เขียนแถว `tb_activity` หนึ่งแถวด้วย `entity_type = 'auth'` ห่อด้วย try/catch ของตัวเอง (ความล้มเหลวของการ log ไม่เคยทำให้ request login/logout ล้มเหลวตาม)
- **Scope เฉพาะ BU เริ่มต้นเป็นข้อจำกัดจริง ไม่ใช่การออกแบบที่บันทึกไว้ที่อื่น** ผู้ใช้ที่ทำงานข้ามหลาย BU จะมีแถว login/logout ที่ระบุเฉพาะ tenant schema ของ BU เริ่มต้นเท่านั้น
- **เขตเวลา** `tb_activity.created_at` เป็น `Timestamptz(6)` UTC; UI render ใน timezone ของ profile ผู้ใช้ผ่าน `formatDate()`
- **Retention** ควบคุมโดย retention ตามนโยบาย tenant ของ [reporting-audit/activity](/th/inventory/reporting-audit/activity) — ไม่พบกฎ retention แยกสำหรับแถว entity auth โดยเฉพาะ
- **RBAC** หน้าจอเองต้องการสิทธิ์ navigation มาตรฐานของ Sysadmin; ไม่พบสิทธิ์ "Security Officer" ที่ละเอียดกว่าที่ gate ส่วนไหนของหน้าจอนี้เลย

---

## 5. โมเดลข้อมูล (Dev)

**หนึ่งตาราง ไม่ใช่สอง** Surface นี้คือตาราง `tb_activity` เดียวกับ [reporting-audit/activity](/th/inventory/reporting-audit/activity) กรองด้วย `entity_type = 'auth'` (ซึ่งในทางปฏิบัติหมายถึง `action IN ('login', 'logout')` เพราะสองค่านี้เป็นค่าเดียวที่ผู้เขียนของ entity type นี้เคยสร้าง) `tb_user_login_session` — ที่เคยบันทึกไว้ว่าเป็นครึ่งที่เหลือของโมเดลนี้ — ตายแล้ว

### 5.1 `tb_activity` (tenant) — projection ที่กรอง, `entity_type = 'auth'`

| ฟิลด์ | ใช้เป็น | คำอธิบาย |
| --- | --- | --- |
| `actor_id` | identity ผู้ใช้ | join `tb_user.id` ของแพลตฟอร์ม |
| `action` | ประเภท event | `login` หรือ `logout` — ยืนยันแล้วว่าเป็นสองค่าเดียวที่ผู้เขียนนี้สร้าง |
| `entity_type` | คีย์ filter | เป็น `'auth'` เสมอสำหรับแถวของหน้าจอนี้ |
| `meta_data` | เพิ่มเติม | `{ login_time: ... }` ตอน login ตามจุดเรียกของ `logAuthActivity()` — ยังไม่ยืนยัน payload ที่ละเอียดกว่านี้ (flag MFA, chain การ impersonate) ในโค้ดที่ตรวจสอบ |
| `created_at` | timestamp ของ event | UTC `Timestamptz(6)` |

ดู [reporting-audit/activity](/th/inventory/reporting-audit/activity) §5.1 สำหรับนิยามตารางเต็ม (รวม `doc_version`, `old_data`/`new_data`, `ip_address`/`user_agent` ที่ผู้เขียนนี้อาจหรืออาจไม่เติมค่า — ยังไม่ได้ตรวจสอบทีละฟิลด์ในรอบนี้)

### 5.2 `tb_user_login_session` (platform schema — ตารางที่ตายแล้ว เก็บไว้เพื่อเปรียบเทียบ)

`id`, `token`, `token_type` (`enum_token_type`: `access_token`/`refresh_token`), `user_id`, `expired_on` (default `now() + 1 day`) มีรูปร่างเหมือนตาราง session แต่ **ไม่พบการอ้างอิงจากโค้ดเลยแม้แต่ตัวเดียว** ทั่ว `carmen-turborepo-backend-v2/apps` ระบบนี้ authenticate ผ่าน JWT ที่ Keycloak ออกให้ — ไม่มีตาราง session ในเครื่องรองรับเลย

## 6. กติกาทางธุรกิจ

- **ผู้เขียนเดียว ตารางเดียว** `AuthService.logAuthActivity()` ใน `micro-business` คือผู้เขียนที่ยืนยันแล้วเพียงตัวเดียว — ถูกเรียกจาก `login()` (เฉพาะสำเร็จ) และ `logout()` ทั้งคู่ scope ด้วย `entity_type = 'auth'`
- **Scope ตาม business unit เริ่มต้น** การเขียน resolve BU เริ่มต้นของผู้ใช้ (`tb_user_tb_business_unit` ที่ `is_default: true, is_active: true`); ถ้าไม่มี การเขียน activity จะถูกข้ามอย่างเงียบ ๆ (log ระดับ debug ไม่ใช่ error)
- **ทนต่อความล้มเหลว ไม่ทำให้ request ล้มเหลว** ทั้งสองจุดเรียกห่อ `logAuthActivity()` ด้วย try/catch — ความล้มเหลวของการ log ไม่เคยทำให้ request login/logout ที่ครอบอยู่ล้มเหลวตาม
- **ไม่มีการยืนยันการจับ failed-login, การ log page-view หรือการติดตาม impersonation** ทั้งสามเคยถูกบันทึกไว้ว่ามีอยู่จริง; ไม่พบสิ่งใดในรอบนี้
- **`tb_user_login_session` ตายแล้ว** ไม่มีเส้นทางโค้ดใดสร้าง, อ่าน, อัปเดต หรือลบแถวในนั้นเลย

## 7. ความเชื่อมโยงข้ามโมดูล

- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — ตารางเบื้องหลัง (และตารางเดียว) หน้านี้เป็นมุมมองที่กรองที่ client เหนือข้อมูลชุดเดียวกันทุกประการ
- [access-control/user](/th/inventory/access-control/user) — `actor_id` resolve ผ่าน `tb_user` ของแพลตฟอร์ม

## 8. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (บรรทัด ~280), `enum_activity_action` (บรรทัด ~56)
- **Prisma platform (ตารางที่ตายแล้ว เพื่อเปรียบเทียบ):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_login_session` (บรรทัด ~567), `enum_token_type` (บรรทัด ~577)
- **ผู้เขียนที่ยืนยันแล้ว:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `logAuthActivity()` (private method) เรียกจาก `login()` และ `logout()`
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/user-activity/user-activity.route.tsx`, `user-activity-component.tsx` (ตั้งค่าคงที่ `entity_type = "auth"` ทุก query), `use-user-activity-table.tsx`
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-user-activity.ts` — เรียก endpoint `API_ENDPOINTS.ACTIVITY_LOGS(buCode)` เดียวกับหน้าจอของ [reporting-audit/activity](/th/inventory/reporting-audit/activity)
