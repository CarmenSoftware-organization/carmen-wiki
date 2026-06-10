---
title: News — สิทธิ์ (Permissions)
description: เมทริกซ์ gate ของ news.* สำหรับผู้เขียน, กฎการมองเห็นฝั่งผู้อ่านบน public endpoint แบบ anonymous (สถานะ, cutoff ของ published_at, global เทียบกับการกำหนดเป้าหมาย BU) และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
published: true
date: 2026-06-10T15:45:00.000Z
tags: book/platform, news, permissions
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# News — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route ถือ `news.read` / `.create` / `.update` บน `PrivateRoute`; รายการ sidebar บน `.read` &nbsp;·&nbsp; **Gate `<Can>` ภายในหน้า:** Add News (`.create`), Edit ของ row (`.update`), Delete ของ row (`.delete` — ภายในหน้าเท่านั้น ไม่มี route), toggle Edit (`.update`) &nbsp;·&nbsp; **ช่องว่างที่ทราบ:** CTA "Add News" ของ empty-state ไม่ถูก gate &nbsp;·&nbsp; **ฝั่งผู้อ่าน:** `/api/public/news` เป็น **anonymous** — การมองเห็นถูกตัดสินโดย `status = published` + `published_at <= now()` + การกำหนดเป้าหมาย ไม่ใช่โดย permission key ใด ๆ

## 1. ภาพรวม

สองเรื่องราว authorization ที่เป็นอิสระต่อกันมาบรรจบกันในโมดูลนี้ เรื่องแรกคือ [Platform RBAC](/th/platform/rbac) แบบธรรมดา: key `news.*` ทั้งสี่ (seed ใน `seed.platform-permission.ts`) ที่ตัดสินว่า*ผู้เขียน*คนใดมองเห็นและแก้ไขบทความใน admin SPA ได้ (§2) เรื่องที่สองคือสิ่งที่ตัว row เอง encode ไว้: **กฎการมองเห็นฝั่งผู้อ่าน** — บทความตัวไหนที่ public endpoint แบบ anonymous เสิร์ฟให้ผู้ชมกลุ่มไหน ควบคุมโดย `status`, `published_at`, soft delete และรายการกำหนดเป้าหมาย `business_unit_ids` (§3) ไม่มี RBAC key ใดมีบทบาทในการส่งมอบ และไม่มี bearer token หรือ `x-app-id` ถูกตรวจสอบบน public controller — ผู้เขียนที่มี key `news.*` เป็นศูนย์ยังคงอ่านทุกบทความที่ published ผ่าน `/api/public/news` ได้ เหมือนกับใครก็ตาม

caller ที่เป็น machine ของ CRUD `/api/news` แบบ authenticated ถูก gate บนแกนที่สามคู่ขนานกัน: grant ของ `AppIdGuard` (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete`) ที่ถูกตรวจสอบกับ allowlist ของ application ที่เรียก — ดู [Applications](/th/platform/applications) request หนึ่ง ๆ ล้มเหลวได้บนแกนผู้ใช้ แกน application หรือทั้งสองแกน

## 2. เมทริกซ์ของ gate

gate ทั้งหมดของ SPA resolve ผ่าน permission resolver ตัวเดียวที่ document ไว้ใน [Platform RBAC — Permissions](../rbac/permissions.md); route guard ที่ไม่ผ่านจะ render `AccessDenied` ภายใน shell `Layout` ปกติ

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| `/news` | `PrivateRoute requiredPermission` | `news.read` | `src/App.tsx` |
| `/news/new` | `PrivateRoute requiredPermission` | `news.create` | `src/App.tsx` |
| `/news/:id/edit` | `PrivateRoute requiredPermission` | `news.update` | `src/App.tsx` |
| sidebar "News" (กลุ่ม Content, ไอคอน Newspaper) | nav filter ของ `Layout.tsx` | `news.read` | `src/components/Layout.tsx` |
| Add News (header ของหน้า list) | `<Can>` | `news.create` | `NewsManagement.tsx` |
| Edit ของ row (dropdown action) | `<Can>` | `news.update` | `NewsManagement.tsx` |
| Delete ของ row (dropdown action) | `<Can>` | `news.delete` | `NewsManagement.tsx` |
| toggle Edit (header ของหน้า edit) | `<Can>` | `news.update` | `NewsEdit.tsx` |

ความไม่สมมาตรที่เกี่ยวข้องกับผู้ทดสอบ ซึ่งสะท้อนโมดูล Applications และ Print Template Mapping:

- **`.delete` มีอยู่ภายในหน้าเท่านั้น** ไม่มี route ใดต้องการมันและหน้า edit ไม่มี action ลบ — surface ทั้งหมดของ key คือรายการใน dropdown ของ row ในหน้า list session ที่มีเฉพาะ `.read` เห็น list พร้อม dropdown action ที่ว่างเปล่า
- **Save ไม่ถูก gate แยกต่างหาก** เฉพาะ *toggle* Edit เท่านั้นที่ถูกห่อด้วย `<Can>`; แถว Save/Cancel render เฉพาะในโหมดแก้ไข ซึ่งไปถึงไม่ได้หากไม่มี toggle (โหมด create อยู่หลัง `.create` ของ route) การบังคับใช้ฝั่ง backend บน `PUT` ยังคงเป็นขอบเขตจริง
- **CTA ของ empty-state ไม่ถูก gate** เมื่อ list ว่างและไม่มีคำค้นหา active, `EmptyState` เสนอปุ่ม "Add News" โดยไม่มีการห่อ `<Can>` — session ที่ไม่มี `.create` เห็น affordance, คลิกมัน และไปเจอ `AccessDenied` ของ route guard `/news/new` เป็นเพียงการรั่วของ affordance ไม่ใช่รูรั่วของการบังคับใช้
- **Export ไม่ถูก gate** session ใดก็ตามที่เข้าถึง list ได้ (`.read`) สามารถส่งออก CSV ของหน้าที่โหลดอยู่ได้
- **Key ของ route เป็นอิสระต่อกัน** `.update` อย่างเดียว deep-link ไป `/news/:id/edit` ได้ขณะที่ `/news` ปฏิเสธ; `.create` อย่างเดียวไปถึง `/news/new` ทาง URL ได้
- sidebar filter เป็น UX ไม่ใช่ security — session ที่ไม่มี `news.read` ยังพิมพ์ URL ได้และจะชน route guard session แบบ super-admin และ bootstrap ผ่านทุก gate; อย่า QA เมทริกซ์นี้จาก session แบบนั้น

## 3. กฎการกำหนดเป้าหมายและการมองเห็น

ฝั่งเขียน micro-cluster ตรวจสอบการกำหนดเป้าหมายตอน create และตอน update ใด ๆ ที่แตะ field นี้: `business_unit_ids` ต้องเป็น array ของ string และทุก id ที่ unique ต้อง match กับ row ของ `tb_business_unit` ที่ live อยู่ ไม่เช่นนั้นได้ 400 SPA ยังกำหนดเพิ่มว่าต้องมี ≥1 BU เมื่อใดก็ตามที่ checkbox "Visible to all business units (global)" ไม่ถูกติ๊ก — ดังนั้น `[]` ถูกผลิตขึ้นได้โดยจงใจเท่านั้น ด้วยการติ๊กกล่อง

ฝั่งอ่าน public feed (`GET /api/public/news`, anonymous) ตัดสินการมองเห็นจากข้อมูลใน row ล้วน ๆ:

```
visible(article, bu_id?):
    if article.deleted_at is not null:        return false
    if article.status != published:           return false   -- draft และ archived เหมือนกัน
    if article.published_at is null
       or article.published_at > now():       return false   -- ลงวันที่อนาคต = กำหนดเวลาเผยแพร่;
                                                             -- ค่าประทับที่ถูกเคลียร์ผ่าน API ก็ซ่อนมันเช่นกัน
    if bu_id is absent:
        return article.business_unit_ids == []               -- global เท่านั้น
    return article.business_unit_ids == []
        or bu_id in article.business_unit_ids                 -- global + ที่กำหนดเป้าหมาย
```

ผลสืบเนื่องสำหรับผู้ทดสอบ:

1. **ผู้อ่านใน BU X เห็น:** บทความ global ทั้งหมดบวกบทความที่รายการมี BU id ของ X — เมื่อ caller ส่ง `bu_id=X` มา endpoint เชื่อใจ parameter นี้; ไม่มี session ให้ derive มันออกมา `bu_id` ที่ไม่รู้จักหรือผิดรูปแบบจะลดระดับเป็น global-only อย่างเงียบ ๆ (ไม่มี error)
2. **การละ `bu_id` ซ่อนทุกบทความที่กำหนดเป้าหมาย** แม้จากผู้ชมที่มันกำหนดเป้าหมายไว้ — ภาระการส่ง id ที่ถูกต้องอยู่ที่ client ฝั่งบริโภค
3. **endpoint แบบรายการเดียว** (`GET /api/public/news/:id`) apply filter ของสถานะ/วันที่/การลบ แต่**ไม่มีการตรวจสอบ BU** — caller ใดก็ตามที่รู้ UUID ของบทความที่กำหนดเป้าหมายสามารถ fetch มันได้ การกำหนดเป้าหมายบน public surface เป็นการ scope ของ feed ไม่ใช่ access control
4. id ที่เป็น draft, archived, ถูก soft-delete, ลงวันที่อนาคต และไม่มีอยู่จริง ทั้งหมดตอบ 404 เหมือนกัน — การมีอยู่ไม่รั่วไหล

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | Archived เทียบกับ soft-deleted | `archived` ยังอยู่ใน admin list (badge, filter ได้) และอยู่นอก public feed; row ที่ถูก soft-delete *ถูกคืนมา*โดย endpoint ของ admin list แต่ถูกซ่อนฝั่ง client และ 404 บน `GET :id` | Archive เพื่อปลดระวางเนื้อหาแบบมองเห็นได้; ลบเพื่อเอามันออกจาก SPA ทั้งหมด ตรวจสอบการลบที่ถูกซ่อนผ่าน Debug Sheet — raw JSON ของ list ยังมีพวกมันอยู่ |
| 2 | สถานะถูก flip `published` → `draft` | `published_at` ถูก**คงไว้** ไม่ถูกเคลียร์ (ยืนยันแล้วใน `update` ของ micro-cluster); บทความออกจาก public feed เพราะ filter สถานะอย่างเดียว | list ยังแสดง timestamp ของ Published เดิมบน row ที่เป็น draft — เป็นไปตามที่ออกแบบ ไม่ใช่ bug การ re-publish คงค่าประทับเดิมไว้ |
| 3 | การ re-publish บทความที่ archived | กลับเข้า public feed ภายใต้ `published_at` **เดิม** (server ประทับเฉพาะ row ที่ไม่เคย publish เท่านั้น) | เมื่อเรียงตาม `published_at DESC` ฝั่ง public บทความเก่าที่ re-publish จะ*ไม่*กระโดดขึ้นไปอยู่บนสุด |
| 4 | `published_at` แบบระบุชัด/ลงวันที่อนาคต | ตั้งได้ผ่าน API เท่านั้น (SPA ไม่เคยส่งมัน); วันที่อนาคตกัน row ที่ `published` ไว้นอก feed จนกว่าเวลานั้นจะผ่านไป | เป็นการกำหนดเวลาเผยแพร่โดยพฤตินัย; ทดสอบได้ผ่าน API หรือ Bruno เท่านั้น ไม่ใช่ SPA |
| 5 | field `image` แบบ legacy | SPA อ่าน `image_url \|\| image` ทุกที่; gateway ปัจจุบัน emit `image_url` (presigned, หมดอายุ 1 ชั่วโมง) และตัด token ที่จัดเก็บออก | thumbnail ที่ 404 หลังหน้า list ค้างไว้นานคือ presigned URL ที่หมดอายุ — การ refresh จะ refetch URL ใหม่ |
| 6 | GIF หรือรูปใหญ่เกิน | picker ของ SPA รับ `image/gif` และบังคับเฉพาะ ≤5 MB; backend ปฏิเสธ GIF (`BAD_FILE_TYPE`) และ >2048×2048 px (`BAD_DIMENSIONS`) ตอน save | รายการ accept ของ client/server ต่างกัน — ความล้มเหลวปรากฏเป็น "Failed to save news" ระดับฟอร์ม ไม่ใช่ตอนเลือกไฟล์ |
| 7 | การลบรูปที่ save ไว้ | ทำไม่ได้จาก SPA: update แบบ JSON ไม่แตะรูป และปุ่ม Remove ของ ImageUpload เคลียร์เฉพาะการเลือกที่*ค้างอยู่*เท่านั้น | วิธีเดียวที่จะเอารูปออกคือแทนที่มัน (ไฟล์ MinIO เก่าจะถูกลบฝั่ง server) |
| 8 | BU ถูก soft-delete หลังถูกกำหนดเป้าหมาย | การตรวจสอบรันตอนเขียนเท่านั้น; id ค้างยังอยู่ใน `business_unit_ids` และยัง match กับ `array_contains` ของ public feed | การ save บทความอีกครั้งโดยแตะ field การกำหนดเป้าหมายจะ re-validate แล้ว**ปฏิเสธ** id ค้างนั้น — ผู้แก้ไขต้องเอามันออกจึงจะ save ได้ |
| 9 | sort ของ list ดูเหมือนพัง | server override ทุก sort เป็น `updated_at DESC`; ค่าเริ่มต้น `published_at:desc` ของ SPA และ header ที่คลิกได้ถูกส่งไปแต่ถูกเพิกเฉย | ความแตกต่างที่ทราบกัน ([Data Model](./data-model.md) §5) — อย่ายื่น defect ของการ sort รายคอลัมน์จนกว่าการ override จะถูกถอดออก |
| 10 | สองบทความ หัวข้อเดียวกัน | อนุญาต — ไม่มี unique constraint บน `title` | แยกแยะด้วย id (Debug Sheet) เมื่อทดสอบ |

## 5. คำแนะนำ

- **ทดสอบสองเรื่องราวแยกจากกัน** ตรวจสอบการ gate ผู้เขียนด้วย session ที่ถือ key `news.*` ทีละหนึ่งตัวเป๊ะ ๆ; ตรวจสอบการส่งมอบด้วยการเรียกแบบ anonymous ดิบ ๆ ไปยัง `/api/public/news` — การ save ใน SPA ที่ผ่านไม่ได้บอกอะไรเลยเกี่ยวกับว่าใครอ่านบทความได้
- **Probe เมทริกซ์ lifecycle × feed** สำหรับบทความหนึ่งตัว เดิน draft → published → archived → published และยืนยันการเป็นสมาชิกของ feed กับ `published_at` ที่คงที่ในแต่ละขั้น (case 2–3 ด้านบน)
- **QA การกำหนดเป้าหมายต้องใช้สามการเรียกต่อบทความ:** public feed โดยไม่มี `bu_id`, ด้วย id ของ BU ที่ถูกกำหนดเป้าหมาย และด้วย id ที่ไม่ถูกกำหนดเป้าหมาย — บวก endpoint แบบรายการเดียวเพื่อยืนยันว่ามันข้ามการตรวจสอบ BU (§3 ข้อ 3)
- **ใช้แกน machine หนึ่งครั้ง** เรียก `/api/news` ด้วย bearer ที่ valid แต่ application ที่ไม่มี grant `news.*` เพื่อยืนยันว่าการปฏิเสธของ `AppIdGuard` เป็นอิสระจาก RBAC key ของผู้ใช้
- **ปฏิบัติกับ CTA ของ empty-state ที่ไม่ถูก gate และ sort ของ list ที่ถูกเพิกเฉยเป็น issue ที่ทราบกัน** — ตรวจสอบว่าพฤติกรรมตรงกับหน้านี้แทนที่จะยื่น defect ซ้ำซ้อน; ทั้งคู่เป็นช่องว่างของ affordance/UX โดยการบังคับใช้ฝั่ง server ยังสมบูรณ์

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard ทั้งสาม) · `src/components/Layout.tsx` (รายการ sidebar) · `src/pages/NewsManagement.tsx` / `NewsEdit.tsx` (gate `<Can>`, CTA ที่ไม่ถูก gate) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/news.controller.ts` (KeycloakGuard + `AppIdGuard` ราย route) · `public-news.controller.ts` (ไม่มี guard) · `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (การตรวจสอบ BU, filter ของ `findPublicAll`/`findPublicOne`) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.ts` (key ทั้งสี่)
**Cross-link:** [หน้า landing ของ News](/th/platform/news) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md) &nbsp;·&nbsp; [Applications](/th/platform/applications)
