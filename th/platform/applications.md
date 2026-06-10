---
title: แอปพลิเคชัน (Applications)
description: ภาพรวมโมดูล Applications — API client ที่ลงทะเบียนของแพลตฟอร์ม, identity แบบ x-app-id และการมอบสิทธิ์เข้าถึงแบบ allow-all เทียบกับรายการ api_name แบบระบุชัด
published: true
date: 2026-06-10T15:15:00.000Z
tags: platform/applications, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# แอปพลิเคชัน (Applications)

โมดูล **Applications** จัดการ **API client** ที่ลงทะเบียนของแพลตฟอร์ม — caller ที่เป็น machine ของ backend gateway เรคคอร์ดของ application คือ identity บวกการมอบสิทธิ์เข้าถึง: UUID ของเรคคอร์ดคือค่า header `x-app-id` ที่ client ส่งมากับทุก request และ grant ของมันคือ "allow all APIs" หรือรายการ key `api_name` แบบระบุชัดที่เลือกจาก catalog ที่ backend generate ขึ้น ขณะที่ [Platform RBAC](/th/platform/rbac) ตอบคำถามว่า "*คน* คนนี้ทำอะไรได้บ้าง" Applications ตอบว่า "*โปรแกรม* ตัวนี้เรียกอะไรได้บ้าง"

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ลงทะเบียน machine client และมอบสิทธิ์เข้าถึง API ให้พวกมัน — `allow_all` หรือรายการ `api_names` แบบระบุชัดที่เลือกจาก catalog ที่จัดกลุ่มตามโมดูล &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA และการบังคับใช้ `AppIdGuard` ของ backend gateway &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_application` (ตัว client: `name`, `is_active`, `allow_all`), `tb_application_api` (grant row แบบ 1:N หนึ่ง `api_name` ต่อ row) &nbsp;·&nbsp; **Identity:** `id` ของเรคคอร์ด (UUID) **คือ** ค่า `x-app-id` — ไม่มี field app-id แยกต่างหาก &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูลนี้ทำตามรูปแบบสองหน้าจอมาตรฐานของ SPA:

- **`/applications` → `ApplicationManagement`** — `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce (name/description), filter Active/Inactive แบบ Sheet, ส่งออก CSV และจดจำสถานะ UI ใน `localStorage` คอลัมน์ **App ID** render UUID ของเรคคอร์ดเป็น monospace เพื่อให้ operator คัดลอกค่า `x-app-id` ที่ถูกต้องเป๊ะ ๆ ได้ และคอลัมน์ **Access** สรุป grant เป็น badge "All APIs" หรือ "N APIs"
- **`/applications/new` และ `/applications/:id/edit` → `ApplicationEdit`** — การ์ด "Application Details" การ์ดเดียว (โหมด create แก้ไขได้ทันที; route edit เริ่มต้นแบบ read-only อยู่หลัง toggle Edit) องค์ประกอบที่เป็นเอกลักษณ์ของมันคือ **API Names selector**: accordion แบบพับเก็บได้ของ key `api_name` จัดกลุ่มตามโมดูล พร้อมช่อง filter, select-all ต่อโมดูล และ badge นับจำนวนที่เลือก selector จะ render เฉพาะเมื่อ `allow_all` ปิดอยู่

ตัวเลือกของ selector มาจาก `GET /api-system/applications/api-catalog` SPA เพิ่มหรือแก้ไขรายการใน catalog ไม่ได้ — catalog ถูก generate ฝั่ง backend (§2) และ SPA ทำได้เพียงเลือกจากมัน ดู [UI Screens](/th/platform/applications/ui-screens) สำหรับ walkthrough ฉบับเต็ม

ส่วนที่เหลือทั้งหมดเป็นองค์ประกอบมาตรฐานของหน้า Management ใน SPA: `TableSkeleton` ตอนโหลดครั้งแรก, `EmptyState` เมื่อ list ว่าง, toast feedback ตอน mutation, navigation guard `useUnsavedChanges` ระหว่างแก้ไข และ Debug Sheet เฉพาะ dev ที่เปิดเผย raw API response ของแต่ละหน้าจอ

## 2. บริบททางธุรกิจ

caller ที่เรียก backend ของ Carmen Platform มีสองแบบ: **ผู้ใช้ที่เป็นมนุษย์** ซึ่ง session ถือ bearer token และ resolve ผ่าน permission snapshot ของ RBAC และ **machine client** — service พี่น้อง, integration และตัว SPA เอง — ซึ่งระบุตัวตนด้วย header `x-app-id` ทุก request ที่ **authenticated** ที่ Platform admin SPA ส่งออกถือทั้งสองอย่าง: `Authorization: Bearer <token>` สำหรับผู้ใช้ และ `x-app-id` สำหรับ application (`src/services/api.ts` ตั้ง `x-app-id` เป็น default header จาก build env var `REACT_APP_API_APP_ID`; interceptor ของมันแนบ bearer เฉพาะเมื่อมี token อยู่ ดังนั้น `/auth/login` ถูกส่งออกพร้อม `x-app-id` ตัวเดียว) หมายความว่าตัว SPA เองก็เป็นเรคคอร์ด application ที่ลงทะเบียนไว้ request หนึ่ง ๆ จึงล้มเหลวได้บนแกนใดแกนหนึ่งอย่างอิสระ — ผู้ใช้ผิด หรือ app id ผิด/ไม่ได้รับ grant

ฝั่ง backend, endpoint ที่ถูก guard ถูกห่อด้วย `AppIdGuard('module.action')` (backend-gateway) guard จะ validate ตัว header เองก่อน — `x-app-id` ที่หายไปหรือไม่ใช่ UUID เป็น `400` — จากนั้นตรวจสอบมันกับ **allowlist snapshot ใน memory** ไม่ใช่ฐานข้อมูล: `AppAllowlistRefresher` โหลด snapshot จาก micro-cluster ตอน boot (fail-closed — ทุกการเรียกที่ถูก guard ถูกปฏิเสธจนกว่าการโหลดครั้งแรกจะสำเร็จ) และ refresh ตาม interval คงที่ (`APP_ALLOWLIST_TTL_MS` ค่าเริ่มต้น 60 วินาที) request ผ่านเมื่อ entry ใน snapshot ของ app id นั้นมี `allow_all = true` หรือมี `api_name` ของ guard อยู่ เนื่องจากการบังคับใช้อ่านจาก snapshot การเปลี่ยน grant (grant ใหม่, การถอน, การลบ, การ flip `allow_all`) จึงมีผลที่ **การ refresh ครั้งถัดไป** ไม่ใช่ทันที

catalog ที่เลือกได้นั้น **derive มาจาก guard เหล่านั้น ไม่ใช่ดูแลด้วยมือ**: `scripts/generate-app-api-catalog/run.ts` ใน `carmen-turborepo-backend-v2` สแกน source ของ gateway หาการเรียก `new AppIdGuard('...')` และ emit `app-api-catalog.generated.ts` (รายการแบนที่เรียงลำดับแล้วบวกกลุ่มตามโมดูล) endpoint ที่ถูก guard ตัวใหม่จะปรากฏใน selector ของ SPA หลังการ regenerate และ deploy backend — ไม่มี database seed เข้ามาเกี่ยวข้อง ซึ่งเป็นความแตกต่างเชิงปฏิบัติการที่สำคัญจาก permission catalog ของ RBAC (ตาราง Postgres ที่ seed ด้วย migration)

## 3. แนวคิดสำคัญ

- **App ID = UUID ของเรคคอร์ด** primary key `tb_application.id` คือค่า `x-app-id` ไม่มีคอลัมน์หรือ field `app_id` แยกต่างหากที่ใดเลย — SPA เพียงแสดง `id` ภายใต้ label "App ID" (read-only, server เป็นผู้ generate)
- **`allow_all` กับรายการแบบระบุชัด** ทางแยกแบบ boolean: `allow_all = true` มอบทุก endpoint ที่ถูก guard และทำให้ row ใด ๆ ใน `tb_application_api` ไม่มีความหมาย; `allow_all = false` มอบเฉพาะ row `api_name` ที่ live อยู่เท่านั้น SPA ซ่อน API Names selector ทั้งหมดขณะที่ `allow_all` ถูกติ๊ก และ payload ของการเขียนละเว้น names ในกรณีนั้น
- **ไวยากรณ์ของ `api_name`** key เป็น string รูปแบบ `resource.action` — shape เดียวกับ permission key ของ RBAC แต่เป็น **คลังศัพท์แยกต่างหากจากแหล่งที่มาแยกต่างหาก**: `api_name` มาจากการสแกน `AppIdGuard` ส่วน key ของ RBAC มาจาก `tb_platform_permission` segment ฝั่ง action ทำตาม method ของ backend controller ไม่ใช่ชุด verb ของ RBAC — `cluster.findAll`, `cluster.findOne`, `cluster.uploadLogo` แทนที่จะเป็น `cluster.read` — สอง catalog จึงใช้ไวยากรณ์ร่วมกันแต่ key string ไม่เหมือนกัน catalog ที่ generate ขึ้นมี 777 key ใน 124 กลุ่มโมดูล ณ 2026-06-10 โมดูลของ `api_name` คือ prefix ก่อน `.` ตัวแรก; ชื่อที่ไม่มีจุดเป็นโมดูลของตัวเอง (`src/utils/apiCatalog.ts` สะท้อนกฎการแบ่งของ generator ฝั่ง backend แบบเป๊ะ ๆ)
- **Replace ไม่ใช่ delta** `PUT /api-system/applications/:id` ส่ง **ชุดที่ต้องการแบบเต็ม** เป็น `details: { add: [{ api_name }] }` — semantics แบบ replace ตรงข้ามกับการเขียน role ของ RBAC ซึ่งส่ง delta `{ add, remove }`; นักพัฒนาที่ port โค้ดข้ามไปมาระหว่างสองโมดูลนี้ต้องไม่ assume ว่าใช้ convention เดียวกัน
- **สุขอนามัยมาตรฐานของแพลตฟอร์ม** `tb_application` มี `is_active`, audit trio และ unique name ที่รองรับ soft-delete (`@@unique([name, deleted_at])`) ชื่อของ application ที่ถูกลบแล้วจึงนำกลับมาใช้ใหม่ได้

## 4. บทบาทและ Persona

การเข้าถึงโมดูลนี้ถูก gate ด้วย permission ผ่าน [Platform RBAC](/th/platform/rbac) ทั้งด้วย route guard และ gate `<Can>` ภายในหน้า:

| Surface | Gate | Key |
|---|---|---|
| route `/applications` + รายการ sidebar "Applications" (กลุ่ม Platform) | `PrivateRoute` / sidebar filter | `application.read` |
| route `/applications/new` | `PrivateRoute` | `application.create` |
| route `/applications/:id/edit` | `PrivateRoute` | `application.update` |
| ปุ่ม Add Application (header ของหน้า list) | `<Can>` | `application.create` |
| Edit ของ row (dropdown action ในหน้า list) | `<Can>` | `application.update` |
| Delete ของ row (dropdown action ในหน้า list) | `<Can>` | `application.delete` |
| toggle Edit (header ของหน้า edit) | `<Can>` | `application.update` |

สังเกตว่า `application.delete` มีอยู่ **เป็น gate ภายในหน้าเท่านั้น** — ไม่มี route ใดต้องการมัน และหน้า edit ไม่มี action ลบเลย; การลบเกิดขึ้นจาก dropdown ของ row ในหน้า list เท่านั้น เมทริกซ์ฉบับเต็ม รวมถึง CTA ของ empty-state ที่ทราบกันว่าไม่ถูก gate อยู่ใน [Permissions](/th/platform/applications/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Platform RBAC](/th/platform/rbac) — คู่เทียบฝั่งการเข้าถึงของมนุษย์ ใช้ไวยากรณ์ key `resource.action` เดียวกัน แต่ catalog และเส้นทางการบังคับใช้ต่างกัน: key ของ RBAC อยู่ใน `tb_platform_permission` และ gate session ของผู้ใช้; `api_name` มาจากการสแกน `AppIdGuard` และ gate caller ที่ใช้ `x-app-id` key `application.*` ที่ gate *หน้าจอของโมดูลนี้เอง* ก็เป็น key ของ RBAC — มนุษย์ต้องมี grant ของ RBAC เพื่อจัดการ grant ของ machine
- [users](/th/platform/users) — application ไม่มี binding กับผู้ใช้; การอ้างอิง `tb_user` เพียงอย่างเดียวบนตาราง application คือคอลัมน์ audit actor ตระกูล `tb_application_role` ที่มีเฉพาะใน schema (ซึ่ง join กับผู้ใช้จริง) ไม่เกี่ยวข้องกับโมดูลนี้ — ดูส่วนความแตกต่างใน [Data Model](/th/platform/applications/data-model)

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — route guard `application.*` ทั้งสาม
- `../carmen-platform/src/components/Layout.tsx` — รายการ sidebar "Applications" (กลุ่ม Platform, `application.read`)
- `../carmen-platform/src/pages/ApplicationManagement.tsx` — หน้า list: คอลัมน์, filter, ส่งออก CSV, gate `<Can>`
- `../carmen-platform/src/pages/ApplicationEdit.tsx` — ฟอร์ม create/view/edit และ API Names selector
- `../carmen-platform/src/services/applicationService.ts` — REST client และการแปลง read/write (`details.add`, fallback ของ catalog)
- `../carmen-platform/src/utils/apiCatalog.ts` + `src/types/index.ts` — helper สำหรับจัดกลุ่ม และ type `Application` / `ApplicationWritePayload` / `ApiCatalogGroup`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application` (บรรทัด 75), `tb_application_api` (บรรทัด 98)
- `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` — generator ของ catalog
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/` — `app-id.guard.ts` (validate header + ตรวจสอบ allowlist), `app-allowlist.store.ts` (snapshot ใน memory), `app-allowlist.refresher.ts` (โหลดตอน boot + refresh ตาม interval)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/applications/data-model) — ตาราง field ของ `tb_application` และ `tb_application_api`, shape read/write ที่ไม่สมมาตร, semantics แบบ replace, endpoint ของ catalog และตระกูล `tb_application_role` ที่มีเฉพาะใน schema
- [UI Screens](/th/platform/applications/ui-screens) — list `ApplicationManagement` และฟอร์ม `ApplicationEdit` รวมถึง API Names selector แบบ accordion จัดกลุ่มและ fallback แบบ ChipInput ของมัน
- [Permissions](/th/platform/applications/permissions) — เมทริกซ์ของ gate, การเข้าถึงของ application ต่างจาก RBAC ของผู้ใช้อย่างไร และกรณีพิเศษสำหรับผู้ทดสอบ
