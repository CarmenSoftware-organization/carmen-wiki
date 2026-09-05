---
title: แอปพลิเคชัน (Applications)
description: ภาพรวมโมดูล Applications — API client ที่ลงทะเบียนของแพลตฟอร์ม, identity แบบ x-app-id และการมอบสิทธิ์เข้าถึงแบบ allow-all เทียบกับรายการ api_name แบบระบุชัด
published: true
date: 2026-09-05T00:00:00.000Z
tags: platform/applications, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:15:00.000Z
---

# แอปพลิเคชัน (Applications)

โมดูล **Applications** จัดการ **API client** ที่ลงทะเบียนของแพลตฟอร์ม — caller ที่เป็น machine ของ backend gateway เรคคอร์ดของ application คือ identity บวกการมอบสิทธิ์เข้าถึง: UUID ของเรคคอร์ดคือค่า header `x-app-id` ที่ client ส่งมากับทุก request และ grant ของมันคือ "allow all APIs" หรือรายการ key `api_name` แบบระบุชัดที่เลือกจาก catalog ที่ backend generate ขึ้น ขณะที่ [Platform RBAC](/th/platform/rbac) ตอบคำถามว่า "*คน* คนนี้ทำอะไรได้บ้าง" Applications ตอบว่า "*โปรแกรม* ตัวนี้เรียกอะไรได้บ้าง"

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ลงทะเบียน machine client และมอบสิทธิ์เข้าถึง API ให้พวกมัน — `allow_all` หรือรายการ `api_names` แบบระบุชัดที่เลือกจาก catalog ที่จัดกลุ่มตามโมดูล &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA และการบังคับใช้ `AppIdGuard` ของ backend gateway &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_application` (ตัว client: `name`, `is_active`, `allow_all`), `tb_application_api` (grant row แบบ 1:N หนึ่ง `api_name` ต่อ row) &nbsp;·&nbsp; **Identity:** `id` ของเรคคอร์ด (UUID) **คือ** ค่า `x-app-id` — ไม่มี field app-id แยกต่างหาก &nbsp;·&nbsp; **Permission key** (`../carmen-platform/src/components/nav/platformNav.ts`): `application.read` (list/nav) + `application.create`/`application.update`/`application.delete` &nbsp;·&nbsp; **Feature-flag key:** `applications` (ตรวจหลัง permission gate บนทั้งสาม route และ sidebar entry) &nbsp;·&nbsp; **superAdminOnly:** ไม่ใช่ &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูลนี้ทำตามรูปแบบสองหน้าจอมาตรฐานของ SPA:

- **`/applications` → `ApplicationManagement`** — `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce (name/description), filter Active/Inactive + Device แบบ Sheet, ส่งออก CSV, แถบสรุป **Registry** (`ApplicationRegistrySummary` — ตั้งแต่ 2026-08-24 อ่านจาก endpoint `GET /api-system/applications/summary` โดยเฉพาะ ไม่กวาดทั้งตารางฝั่ง client แล้ว — จำนวนรวม/active/inactive, แถบสัดส่วน full-access เทียบกับ scoped และสรุปตามอุปกรณ์) และจดจำสถานะ UI ใน `localStorage` App ID และ Description ไม่มีคอลัมน์แยกของตัวเองอีกต่อไป: เซลล์ Name ซ้อนลิงก์ชื่อ (พร้อม badge **Inactive** ข้างๆ เฉพาะเมื่อ application ปิดใช้งาน — วาดเฉพาะข้อยกเว้น ไม่ใช่ทาสีเขียวทุกแถวเหมือนเดิม), UUID ของเรคคอร์ดแบบ monospace พร้อมปุ่ม copy inline และคำอธิบายไว้ข้างล่าง **คอลัมน์ Access ไม่ใช่ badge ธรรมดาอีกต่อไป** ตั้งแต่ commit `89ba8a8` (2026-09-02, `#254`) มันเรนเดอร์ `ApplicationReachCell`: บาร์บวกเศษส่วน `granted/catalogSize` (เช่น `207/900`) เทียบกับ catalog จริง เปลี่ยนเป็นโทนเตือนพร้อมไอคอนสามเหลี่ยมเมื่อ reach เท่ากับทั้ง catalog (`allow_all` วาดเป็น `n/n` บนไม้บรรทัดเดียวกัน ไม่ใช่คำว่า "All APIs") พร้อมบรรทัดรองบอกจำนวนโมดูลที่เข้าถึง บาร์และตัวหารจะหายไปแทนที่ด้วยตัวเลขเปล่าถ้า catalog fetch ล้มเหลว คอลัมน์ **Device** ตอนนี้เป็นข้อความเงียบ (`formatDevice()`) ไม่ใช่ badge — แถบทะเบียนบอก histogram อุปกรณ์ไปแล้ว **ไม่มีคอลัมน์ Status แยกอีกต่อไป**
- **`/applications/new` และ `/applications/:id/edit` → `ApplicationEdit`** — การ์ด **`ApplicationIdentityHero`** (ไอคอน, ชื่อ, badge device/สถานะ, chip App ID พร้อมปุ่ม copy, บรรทัด audit) บวก layout สองคอลัมน์: การ์ด **"API access"** ทางซ้าย ที่ถือ accordion selector (เป็นองค์ประกอบหลักทางสายตา แสดงเสมอ) และการ์ด **"Settings"** แบบ sticky ทางขวา (Name, Description, Device, Status — Device และ Status วาดเป็นข้อความอ่านอย่างเดียวเงียบๆ ในโหมด view ไม่ใช่ badge แล้ว: commit `1c2894d`, 2026-09-02, `#255` ถอด badge ซ้ำที่ห่างจาก badge ของ hero เอง 60px ออก) route edit ยังคงเริ่มต้นแบบ read-only อยู่หลัง toggle Edit (ต่างจาก clusters/business-units ที่ย้ายไปเป็นหน้า one-document แก้ไขได้ตลอด); แถบ sticky ด้านล่างแสดง Save/Cancel ขณะแก้ไข **ตั้งแต่ `#255` hero กับการ์ด API access ใช้ไม้บรรทัดวัดรัศมีร่วมกับหน้ารายการ** (`reachOf()` ใน `utils/apiReach.ts`): hero แสดงบาร์ + เศษส่วน `granted/catalogSize` และบรรทัด "`N` จาก `M` โมดูล" เหมือนที่หน้ารายการใช้ บวกจำนวน **authority actions** ที่ถือครอง — กริยาที่ลบข้อมูลหรือเลื่อนสถานะ workflow ในนามแอป (`delete`, `approve`, `submit`, `revoke` และใกล้เคียง จาก `AUTHORITY_VERBS` ใน `utils/apiCatalog.ts`) ตัว API Names selector ทั้งโหมดอ่านและแก้ไข ย้อมสีเฉพาะชิปกริยา authority และเรียงมันไว้ก่อนในแต่ละโมดูล แสดงเศษส่วน `known/total` อิง catalog ต่อโมดูล (พร้อมตัวนับ `+N` แยกสำหรับ grant ที่ชี้ไป api_name ที่ catalog เลิกมีแล้ว) และเพิ่มบรรทัด "อีก `N` โมดูลที่ไม่เคยแตะ" — กติกาเดียวกับที่ `#252` วางไว้ให้ permission grid ของ RBAC ว่าต้องบอกสิ่งที่เอื้อมไม่ถึงด้วย การเปิด `allow_all` ยังคงเก็บ `api_names` เดิมไว้ในเรคคอร์ด และตอนนี้บอกตรงๆ ด้วย ("ยังเก็บ `N` endpoint ที่จำกัดขอบเขตไว้ข้างใต้ — จะกลับมามีผลถ้าปิด full access") สถานะ not-found ยัง gate ทั้ง shell เมื่อ id หาไม่เจอ องค์ประกอบที่เป็นเอกลักษณ์ยังคงเป็น **API Names selector**: accordion แบบพับเก็บได้ของ key `api_name` จัดกลุ่มตามโมดูล พร้อมช่อง filter, select-all ต่อโมดูล และ — แทนที่บรรทัด "N selected" เปล่าๆ — มิเตอร์บาร์+เศษส่วน+จำนวน authority — render เฉพาะเมื่อ `allow_all` ปิดอยู่ โดยมี banner เตือนแสดงแทนเมื่อ `allow_all` เปิดอยู่ (ทั้งในโหมด view และ edit)

ทั้งสองหน้าจอยังมีฟีเจอร์ **Activity Trail** ที่เพิ่มทั่วทั้ง Platform SPA: ปุ่ม **View History** (dropdown action ของแถวในหน้า list; actions slot ของ hero ในหน้า edit) gate ด้วย `activity_log.read` ผ่าน sentinel `clusterId={PLATFORM_SCOPED_RECORD}` เนื่องจาก application ไม่มี cluster ของตัวเอง (ดู [Permissions](/th/platform/applications/permissions)) การบันทึกเริ่มตั้งแต่ 2026-08-31 (`AUDIT_RECORDING_STARTED_ON_PHASE_2`) application ที่สร้างก่อนหน้านั้นจึงมี timeline ว่างเปล่า ไม่ใช่ว่าไม่เคยถูกแก้ไข

ตัวเลือกของ selector มาจาก `GET /api-system/applications/api-catalog` SPA เพิ่มหรือแก้ไขรายการใน catalog ไม่ได้ — catalog ถูก generate ฝั่ง backend (§2) และ SPA ทำได้เพียงเลือกจากมัน ดู [UI Screens](/th/platform/applications/ui-screens) สำหรับ walkthrough ฉบับเต็ม

ส่วนที่เหลือทั้งหมดเป็นองค์ประกอบมาตรฐานของหน้า Management ใน SPA: `TableSkeleton` ตอนโหลดครั้งแรก, `EmptyState` เมื่อ list ว่าง (CTA "Add Application" ของมันถูก gate ด้วย `<Can>` — ดู §4), toast feedback ตอน mutation, สถานะ not-found ที่ gate ทั้ง shell ของหน้า edit เมื่อ id หาไม่เจอ, การบันทึกแบบ optimistic-lock ด้วย `doc_version`, navigation guard `useUnsavedChanges` ระหว่างแก้ไข และ Debug Sheet เฉพาะ dev ที่เปิดเผย raw API response ของแต่ละหน้าจอ ทั้งสาม route ของ `application.*` และ sidebar entry ยังถือ flag `feature="applications"` บน `PrivateRoute` ตรวจ**หลัง**ผ่าน permission gate: session ที่ไม่มี `application.*` ยังเห็น `<Forbidden>` เหมือนเดิม แต่ session ที่มีสิทธิ์จะเห็น `NotFound` หรือหน้า "Coming Soon" แทนถ้า feature flag ถูกตั้งเป็น `hide`/`inactive`

## 2. บริบททางธุรกิจ

caller ที่เรียก backend ของ Carmen Platform มีสองแบบ: **ผู้ใช้ที่เป็นมนุษย์** ซึ่ง session ถือ bearer token และ resolve ผ่าน permission snapshot ของ RBAC และ **machine client** — service พี่น้อง, integration และตัว SPA เอง — ซึ่งระบุตัวตนด้วย header `x-app-id` ทุก request ที่ **authenticated** ที่ Platform admin SPA ส่งออกถือทั้งสองอย่าง: `Authorization: Bearer <token>` สำหรับผู้ใช้ และ `x-app-id` สำหรับ application (`src/services/api.ts` ตั้ง `x-app-id` เป็น default header จาก build env var `REACT_APP_API_APP_ID`; interceptor ของมันแนบ bearer เฉพาะเมื่อมี token อยู่ ดังนั้น `/auth/login` ถูกส่งออกพร้อม `x-app-id` ตัวเดียว) หมายความว่าตัว SPA เองก็เป็นเรคคอร์ด application ที่ลงทะเบียนไว้ request หนึ่ง ๆ จึงล้มเหลวได้บนแกนใดแกนหนึ่งอย่างอิสระ — ผู้ใช้ผิด หรือ app id ผิด/ไม่ได้รับ grant

ฝั่ง backend, endpoint ที่ถูก guard ถูกห่อด้วย `AppIdGuard('module.action')` (backend-gateway) guard จะ validate ตัว header เองก่อน — `x-app-id` ที่หายไปหรือไม่ใช่ UUID เป็น `400` — จากนั้นตรวจสอบมันกับ **allowlist snapshot ใน memory** ไม่ใช่ฐานข้อมูล: `AppAllowlistRefresher` โหลด snapshot จาก micro-cluster ตอน boot (fail-closed — ทุกการเรียกที่ถูก guard ถูกปฏิเสธจนกว่าการโหลดครั้งแรกจะสำเร็จ) และ refresh ตาม interval คงที่ (`APP_ALLOWLIST_TTL_MS` ค่าเริ่มต้น 60 วินาที) request ผ่านเมื่อ entry ใน snapshot ของ app id นั้นมี `allow_all = true` หรือมี `api_name` ของ guard อยู่ เนื่องจากการบังคับใช้อ่านจาก snapshot การเปลี่ยน grant (grant ใหม่, การถอน, การลบ, การ flip `allow_all`) จึงมีผลที่ **การ refresh ครั้งถัดไป** ไม่ใช่ทันที

catalog ที่เลือกได้นั้น **derive มาจาก guard เหล่านั้น ไม่ใช่ดูแลด้วยมือ**: `scripts/generate-app-api-catalog/run.ts` ใน `carmen-turborepo-backend-v2` สแกน source ของ gateway หาการเรียก `new AppIdGuard('...')` และ emit `app-api-catalog.generated.ts` (รายการแบนที่เรียงลำดับแล้วบวกกลุ่มตามโมดูล) endpoint ที่ถูก guard ตัวใหม่จะปรากฏใน selector ของ SPA หลังการ regenerate และ deploy backend — ไม่มี database seed เข้ามาเกี่ยวข้อง ซึ่งเป็นความแตกต่างเชิงปฏิบัติการที่สำคัญจาก permission catalog ของ RBAC (ตาราง Postgres ที่ seed ด้วย migration)

## 3. แนวคิดสำคัญ

- **App ID = UUID ของเรคคอร์ด** primary key `tb_application.id` คือค่า `x-app-id` ไม่มีคอลัมน์หรือ field `app_id` แยกต่างหากที่ใดเลย — SPA เพียงแสดง `id` ภายใต้ label "App ID" (read-only, server เป็นผู้ generate)
- **`allow_all` กับรายการแบบระบุชัด** ทางแยกแบบ boolean: `allow_all = true` มอบทุก endpoint ที่ถูก guard และทำให้ row ใด ๆ ใน `tb_application_api` ไม่มีความหมาย; `allow_all = false` มอบเฉพาะ row `api_name` ที่ live อยู่เท่านั้น SPA ซ่อน API Names selector ทั้งหมดขณะที่ `allow_all` ถูกติ๊ก และ payload ของการเขียนละเว้น names ในกรณีนั้น
- **ไวยากรณ์ของ `api_name`** key เป็น string รูปแบบ `resource.action` — shape เดียวกับ permission key ของ RBAC แต่เป็น **คลังศัพท์แยกต่างหากจากแหล่งที่มาแยกต่างหาก**: `api_name` มาจากการสแกน `AppIdGuard` ส่วน key ของ RBAC มาจาก `tb_platform_permission` segment ฝั่ง action ทำตาม method ของ backend controller ไม่ใช่ชุด verb ของ RBAC — `cluster.findAll`, `cluster.findOne`, `cluster.uploadLogo` แทนที่จะเป็น `cluster.read` — สอง catalog จึงใช้ไวยากรณ์ร่วมกันแต่ key string ไม่เหมือนกัน catalog ที่ generate ขึ้นมี 900 key ใน 148 กลุ่มโมดูล ณ 2026-09-05 (source HEAD `157a65e`, 2026-09-04; เดิม 788/125 ในการตรวจครั้งก่อน — catalog เติบโตขึ้นเรื่อยๆ เมื่อมี endpoint ที่ถูก guard ตัวใหม่) โมดูลของ `api_name` คือ prefix ก่อน `.` ตัวแรก; ชื่อที่ไม่มีจุดเป็นโมดูลของตัวเอง (`src/utils/apiCatalog.ts` สะท้อนกฎการแบ่งของ generator ฝั่ง backend แบบเป๊ะ ๆ)
- **Replace ไม่ใช่ delta** `PUT /api-system/applications/:id` ส่ง **ชุดที่ต้องการแบบเต็ม** เป็น `details: { add: [{ api_name }] }` — semantics แบบ replace ตรงข้ามกับการเขียน role ของ RBAC ซึ่งส่ง delta `{ add, remove }`; นักพัฒนาที่ port โค้ดข้ามไปมาระหว่างสองโมดูลนี้ต้องไม่ assume ว่าใช้ convention เดียวกัน payload ของ `PUT` (และ `POST`) ตอนนี้ถือ `doc_version` มาด้วย (token optimistic-concurrency — ดู [Data Model](/th/platform/applications/data-model) §2.1)
- **`device` จำแนกชนิดของ client** `tb_application.device` (default `"web"`; ชุดค่าของ SPA คือ `mobile` / `web` / `desktop` / `pos`) บันทึกว่า client เป็นชนิดใด backend gateway resolve มันจาก header `x-app-id` (`getDevice(appId)`) เพื่อขับเคลื่อนพฤติกรรมเฉพาะอุปกรณ์ที่ปลายทาง — เช่น application แบบ `mobile` จะเห็นเฉพาะ GRN แบบ `draft` ในมุมมอง list (ดู [good-receive-note/02-business-rules](/th/inventory/good-receive-note/02-business-rules))
- **สุขอนามัยมาตรฐานของแพลตฟอร์ม** `tb_application` มี `is_active`, audit trio และ unique name ที่รองรับ soft-delete (`@@unique([name, deleted_at])`) ชื่อของ application ที่ถูกลบแล้วจึงนำกลับมาใช้ใหม่ได้

## 4. บทบาทและ Persona

การเข้าถึงโมดูลนี้ถูก gate ด้วย permission ผ่าน [Platform RBAC](/th/platform/rbac) ทั้งด้วย route guard และ gate `<Can>` ภายในหน้า:

| Surface | Gate | Key |
|---|---|---|
| route `/applications` + รายการ sidebar "Applications" (กลุ่ม Platform) | `PrivateRoute` / sidebar filter | `application.read` |
| route `/applications/new` | `PrivateRoute` | `application.create` |
| route `/applications/:id/edit` | `PrivateRoute` | `application.update` |
| ปุ่ม Add Application (header ของหน้า list + empty state) | `<Can>` | `application.create` |
| Edit ของ row (dropdown action ในหน้า list) | `<Can>` | `application.update` |
| Delete ของ row (dropdown action ในหน้า list) | `<Can>` | `application.delete` |
| toggle Edit (actions slot ของ hero ในหน้า edit) | `<Can>` | `application.update` |
| action **View History** ของ row (dropdown ในหน้า list) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` (ฟีเจอร์ Activity Trail แบบ cross-cutting — ใหม่) |
| action **View History** ของ hero (หน้า edit) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` |

สังเกตว่า `application.delete` มีอยู่ **เป็น gate ภายในหน้าเท่านั้น** — ไม่มี route ใดต้องการมัน และหน้า edit ไม่มี action ลบเลย; การลบเกิดขึ้นจาก dropdown ของ row ในหน้า list เท่านั้น **ช่องว่างของ CTA ใน empty-state ที่เคยพบใน sync ก่อนหน้า ตอนนี้ปิดแล้ว** — มันถูกห่อด้วย `<Can permission="application.create">` เหมือนปุ่ม header ยืนยันด้วยการอ่าน source โดยตรง ทั้งสาม route และ sidebar entry ยังต้องการ feature flag `applications` ด้วย (ตรวจหลัง permission gate) เมทริกซ์ฉบับเต็มอยู่ใน [Permissions](/th/platform/applications/permissions)

## 5. โมดูลที่เกี่ยวข้อง

- [Platform RBAC](/th/platform/rbac) — คู่เทียบฝั่งการเข้าถึงของมนุษย์ ใช้ไวยากรณ์ key `resource.action` เดียวกัน แต่ catalog และเส้นทางการบังคับใช้ต่างกัน: key ของ RBAC อยู่ใน `tb_platform_permission` และ gate session ของผู้ใช้; `api_name` มาจากการสแกน `AppIdGuard` และ gate caller ที่ใช้ `x-app-id` key `application.*` ที่ gate *หน้าจอของโมดูลนี้เอง* ก็เป็น key ของ RBAC — มนุษย์ต้องมี grant ของ RBAC เพื่อจัดการ grant ของ machine
- [users](/th/platform/users) — application ไม่มี binding กับผู้ใช้; การอ้างอิง `tb_user` เพียงอย่างเดียวบนตาราง application คือคอลัมน์ audit actor ตระกูล `tb_application_role` ที่มีเฉพาะใน schema (ซึ่ง join กับผู้ใช้จริง) ไม่เกี่ยวข้องกับโมดูลนี้ — ดูส่วนความแตกต่างใน [Data Model](/th/platform/applications/data-model)

## 6. แหล่งข้อมูลอ้างอิง

path ทั้งหมดด้านล่างคือ `../carmen-platform` (Platform admin SPA) เว้นแต่นำหน้าด้วย `../carmen-turborepo-backend-v2` (backend monorepo)

- `../carmen-platform/src/App.tsx` — route guard `application.*` ทั้งสาม ทุกตัวมี `feature="applications"` ด้วย (block ของ route บรรทัด 135–155)
- `../carmen-platform/src/components/nav/platformNav.ts` — รายการ sidebar "Applications" (บรรทัด 40: `navGroup.platform`, `permission: 'application.read'`, `feature: 'applications'`, ไม่มี `superAdminOnly`) **แก้ไขการอ้างอิง:** นิยามนี้ไม่ได้อยู่ใน `Layout.tsx` อีกต่อไป — nav row ย้ายมาที่โมดูลนี้แล้ว (เหมือนที่ Task 4/5 พบใน `users`/`rbac`); `Layout.tsx` ไม่มีการอ้างอิง `application` เลยวันนี้
- `../carmen-platform/src/pages/ApplicationManagement.tsx` และ `applicationManagement/{ApplicationRegistrySummary,ApplicationReachCell}.tsx` — หน้า list: แถบสรุป Registry (อ่านจาก endpoint สรุปโดยเฉพาะ), บาร์วัดรัศมีของคอลัมน์ Access (`ApplicationReachCell`, ใหม่ 2026-09-02), การยุบคอลัมน์ App-ID/description และ badge Inactive เข้า Name, filter, ส่งออก CSV, gate `<Can>` รวม action View History ของ row
- `../carmen-platform/src/pages/ApplicationEdit.tsx` และ `applicationEdit/ApplicationIdentityHero.tsx` — หน้า create/view/edit: การ์ด hero (ใช้ไม้บรรทัดวัดรัศมีร่วมกับ list), layout สองคอลัมน์ API-access/Settings, selector แบบ accordion (ย้อมสี authority, นับ stale/untouched module), การเดินสาย `doc_version`, gate not-found, action View History ของ hero
- `../carmen-platform/src/utils/apiReach.ts` — `reachOf()` ฟังก์ชันคำนวณรัศมีตัวเดียวที่ `ApplicationReachCell` และ `ApplicationIdentityHero` ใช้ร่วมกัน
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf`/`actionOf`/`groupApiNames` บวก (ใหม่) `verbOf`/`isAuthorityAction`/`countAuthority` และเซ็ต `AUTHORITY_VERBS`
- `../carmen-platform/src/utils/device.ts` — `formatDevice()` ฟังก์ชัน format label อุปกรณ์ตัวเดียวที่แถบทะเบียน, คอลัมน์ Device ของ list, และ rail Settings ใช้ร่วมกัน
- `../carmen-platform/src/utils/permissions.ts` — `PLATFORM_SCOPED_RECORD` (นามแฝงของ `UNRESOLVED_CLUSTER_ID`) sentinel `clusterId` ที่ gate `activity_log.read` ของโมดูลนี้ใช้ เพราะ application ไม่มี cluster
- `../carmen-platform/src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` — ฟีเจอร์ View History ทั้งใน dropdown ของ row และ hero ของหน้า edit; `AUDIT_RECORDING_STARTED_ON_PHASE_2` (2026-08-31)
- `../carmen-platform/src/utils/docVersion.ts` — helper optimistic-lock
- `../carmen-platform/src/utils/audit.ts` และ `src/components/{AuditMeta,auditColumns}.tsx` — `normalizeAudit()` (ลอง nested ก่อน flat เป็นทางถอย; `updated` แสดงเฉพาะเมื่อ `everEdited`) และคอลัมน์ Created/Updated ที่ list ของโมดูลนี้ใช้ร่วมกับหน้าอื่น
- `../carmen-platform/src/services/applicationService.ts` — REST client และการแปลง read/write (`details.add`, fallback ของ catalog, `doc_version`, `getRegistrySummary()`)
- `../carmen-platform/src/types/index.ts` — type `Application` / `ApplicationWritePayload` / `ApiCatalogGroup` / `ApplicationSummaryData` / `DeviceCount`
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application` (บรรทัด 65), `tb_application_api` (บรรทัด 90); ตรวจซ้ำ 2026-09-05 กับ source HEAD `157a65e` ทั้งสองไม่เปลี่ยนตั้งแต่ sync ก่อนหน้า
- `../carmen-turborepo-backend-v2/scripts/generate-app-api-catalog/run.ts` — generator ของ catalog
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/applications/app-api-catalog.generated.ts` — catalog ที่ generate จริง (900 key / 148 โมดูล ณ source HEAD `157a65e`)
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/` — `app-id.guard.ts` (validate header + ตรวจสอบ allowlist), `app-allowlist.store.ts` (snapshot ใน memory), `app-allowlist.refresher.ts` (โหลดตอน boot + refresh ตาม interval)

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/applications/data-model) — ตาราง field ของ `tb_application` และ `tb_application_api` (รวม `doc_version`), shape read/write ที่ไม่สมมาตร, semantics แบบ replace, endpoint ของ catalog และตระกูล `tb_application_role` ที่มีเฉพาะใน schema
- [UI Screens](/th/platform/applications/ui-screens) — list `ApplicationManagement` และ layout hero + สองคอลัมน์ของ `ApplicationEdit` รวมถึง API Names selector แบบ accordion จัดกลุ่มและ fallback แบบ ChipInput ของมัน
- [Permissions](/th/platform/applications/permissions) — เมทริกซ์ของ gate, การเข้าถึงของ application ต่างจาก RBAC ของผู้ใช้อย่างไร และกรณีพิเศษสำหรับผู้ทดสอบ
