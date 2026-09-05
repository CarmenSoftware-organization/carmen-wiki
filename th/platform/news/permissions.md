---
title: News — สิทธิ์ (Permissions)
description: เมทริกซ์ gate ของ news.* สำหรับผู้เขียน (รวม bulk publish/archive/delete), กฎการมองเห็นฝั่งผู้อ่านบน public endpoint แบบ anonymous (สถานะ, cutoff ของ published_at, global เทียบกับการกำหนดเป้าหมาย BU) และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, news, permissions
editor: markdown
dateCreated: 2026-06-10T15:45:00.000Z
---

# News — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** route ถือ `news.read` / `.create` / `.update` บน `PrivateRoute`; รายการ sidebar บน `.read` &nbsp;·&nbsp; **Gate `<Can>`/in-component ภายในหน้า:** Add News (header **และ** CTA ของ empty-state, `.create`), Edit ของ row (`.update`), Delete ของ row (`.delete` — ไม่มี route ของ SPA ต้องการมัน), toggle Edit (`.update`), bulk Publish/Archive Selected (`.update`), bulk Delete Selected (`.delete`), **View History** ของ row/header หน้า edit (`activity_log.read`, `PLATFORM_SCOPED_RECORD` — ไม่ได้อยู่ใน actions slot ของ `NewsMasthead`) &nbsp;·&nbsp; **ฝั่ง server (API):** `POST`/`PUT`/`DELETE` ตรวจสอบ permission `news.*` ของผู้เรียกเอง (`PlatformPermissionGuard` เพิ่มเมื่อ 2026-08-20); route `GET` ทั้งสี่ตรวจสอบเฉพาะ `x-app-id` — ไม่บังคับใช้บนแกน permission ของผู้ใช้โดยตั้งใจ เพื่อให้ผู้ใช้ระดับ tenant ของแอปมือถือยังอ่านข่าวได้ &nbsp;·&nbsp; **ฝั่งผู้อ่าน:** `/api/public/news` เป็น **anonymous** — การมองเห็นถูกตัดสินโดย `status = published` + `published_at <= now()` + การกำหนดเป้าหมาย ไม่ใช่โดย permission key ใด ๆ

## 1. ภาพรวม

สองเรื่องราว authorization ที่เป็นอิสระต่อกันมาบรรจบกันในโมดูลนี้ เรื่องแรกคือ [Platform RBAC](/th/platform/rbac) แบบธรรมดา: key `news.*` ทั้งสี่ (seed ใน `seed.platform-permission.ts`) ที่ตัดสินว่า*ผู้เขียน*คนใดมองเห็นและแก้ไขบทความใน admin SPA ได้ (§2) เรื่องที่สองคือสิ่งที่ตัว row เอง encode ไว้: **กฎการมองเห็นฝั่งผู้อ่าน** — บทความตัวไหนที่ public endpoint แบบ anonymous เสิร์ฟให้ผู้ชมกลุ่มไหน ควบคุมโดย `status`, `published_at`, soft delete และรายการกำหนดเป้าหมาย `business_unit_ids` (§3) ไม่มี RBAC key ใดมีบทบาทในการส่งมอบ และไม่มี bearer token หรือ `x-app-id` ถูกตรวจสอบบน public controller — ผู้เขียนที่มี key `news.*` เป็นศูนย์ยังคงอ่านทุกบทความที่ published ผ่าน `/api/public/news` ได้ เหมือนกับใครก็ตาม

caller ที่เป็น machine ของ CRUD `/api/news` แบบ authenticated (รวมถึง endpoint รายการ tag และ summary) ถูก gate บนแกนที่สามคู่ขนานกัน: grant ของ `AppIdGuard` (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete`) ที่ถูกตรวจสอบกับ allowlist ของ application ที่เรียก — ดู [Applications](/th/platform/applications)

**แกนที่สามนั้นไม่ใช่เรื่องราวฝั่ง server ทั้งหมด และมันเปลี่ยนกลางโครงการ** จนถึง 2026-08-20 `news.controller.ts` ไม่มี decorator `@RequirePlatformPermission` แม้แต่ตัวเดียว — มีเพียง `KeycloakGuard` (ต้อง login) และ `AppIdGuard` (application ที่เรียกต้องถือ key นั้น) ผู้ใช้ที่ authenticated คนใดก็ตาม จาก application ใดก็ตามที่มี `news.*` อยู่ใน allowlist สามารถสร้าง อัพเดท หรือลบข่าวได้โดยไม่สนใจ RBAC key ของตัวเอง การซ่อนปุ่มใน SPA คือการควบคุมที่แท้จริงเพียงอย่างเดียว การแก้ในวันนั้นเพิ่ม `PlatformPermissionGuard` + `@RequirePlatformPermission('news.create'/'news.update'/'news.delete')` ให้เฉพาะ route **เขียน** สามตัว ปิดช่องว่างนั้น (การตรวจสอบแบบเดียวกันบน route `broadcast.*` มีมาก่อนหน้านั้นนานแล้ว ซึ่งเป็นสิ่งที่ทำให้ `news.controller.ts` ถูกจับได้ว่าเป็นตัวนอกคอก) route **อ่าน** ทั้งสี่ (`findAll`, `findOne`, `tags`, `summary`) ถูกปล่อยไว้แบบไม่มี guard โดยตั้งใจ ไม่ใช่ความผิดพลาด: DB ของ DEV แสดงว่า application `mobile-app` ถือ `news.findAll`/`news.findOne` อยู่ใน allowlist และให้บริการผู้ใช้ระดับ tenant ที่ไม่มี role ระดับแพลตฟอร์มเลย — การเพิ่มการตรวจสอบ `news.read` ที่นั่นจะทำให้ผู้ใช้มือถือทุกคนอ่านข่าวไม่ได้ ดังนั้นวันนี้: request หนึ่ง ๆ ล้มเหลวได้บนแกน application อย่างเดียว (ทุก route) หรือบน**ทั้งสองแกน** (แกน application และแกน permission ของผู้ใช้ — เฉพาะ route เขียน) — แกน permission ของผู้ใช้ไม่มีอยู่เลยสำหรับการอ่าน

## 2. เมทริกซ์ของ gate

gate ทั้งหมดของ SPA resolve ผ่าน permission resolver ตัวเดียวที่ document ไว้ใน [Platform RBAC — Permissions](/th/platform/rbac/permissions); route guard ที่ไม่ผ่านจะ render หน้า `Forbidden` แบบเฉพาะ (เปลี่ยนชื่อจาก `AccessDenied` แบบ inline เดิม ยังคงเป็นหัวข้อ 403 "Access Denied" เหมือนเดิม ตอนนี้มี action Go Back / Go to Dashboard เพิ่มมา) ภายใน shell `Layout` ปกติ

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| `/news` | `PrivateRoute requiredPermission` | `news.read` | `src/App.tsx` |
| `/news/new` | `PrivateRoute requiredPermission` | `news.create` | `src/App.tsx` |
| `/news/:id/edit` | `PrivateRoute requiredPermission` | `news.update` | `src/App.tsx` |
| sidebar "News" (กลุ่ม Content, ไอคอน Newspaper) | nav filter | `news.read` | `src/components/nav/platformNav.ts` (บรรทัด 27 — ไม่ใช่ `Layout.tsx` ซึ่งไม่ได้กำหนดรายการ nav ใด ๆ) |
| Add News (header ของหน้า list) | `<Can>` | `news.create` | `NewsManagement.tsx` |
| Add News (CTA ของ empty-state) | `<Can>` | `news.create` | `NewsManagement.tsx` |
| Edit ของ row (dropdown action) | `<Can>` | `news.update` | `NewsManagement.tsx` |
| Delete ของ row (dropdown action) | `<Can>` | `news.delete` | `NewsManagement.tsx` |
| คอลัมน์ checkbox การเลือก row | in-component (`canSelect = canUpdate \|\| canDelete`) | `news.update` หรือ `news.delete` | `NewsManagement.tsx` |
| Bulk Publish Selected / Archive Selected | in-component (`canUpdate`) | `news.update` | `NewsManagement.tsx` |
| Bulk Delete Selected | in-component (`canDelete`) | `news.delete` | `NewsManagement.tsx` |
| toggle Edit (masthead ของหน้า edit) | `<Can>` | `news.update` | `NewsEdit.tsx` |
| **View History** ของ row (dropdown action) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` | `NewsManagement.tsx` — ฟีเจอร์ Activity Trail ข้ามโมดูล |
| **View History** หน้า edit (แถว header บนสุดข้าง back link — เฉพาะเรคคอร์ดที่มีอยู่แล้ว; ไม่ได้อยู่ใน masthead) | `<Can>` | `activity_log.read`, `clusterId={PLATFORM_SCOPED_RECORD}` | `NewsEdit.tsx` |
| `GET /api/news/tags` | `AppIdGuard` เท่านั้น | `news.findAll` (key เดียวกับ list) | `news.controller.ts` |
| `GET /api/news/summary` | `AppIdGuard` เท่านั้น | `news.findAll` (ใช้ซ้ำ ไม่ใช่ key แยก) | `news.controller.ts` |
| `POST /api/news` | `AppIdGuard` **+ `PlatformPermissionGuard`** (ฝั่ง server, เพิ่มเมื่อ 2026-08-20) | `news.create` (ทั้งสองแกน) | `news.controller.ts` |
| `PUT /api/news/:id` | `AppIdGuard` **+ `PlatformPermissionGuard`** (เพิ่มเมื่อ 2026-08-20) | `news.update` (ทั้งสองแกน) | `news.controller.ts` |
| `DELETE /api/news/:id` | `AppIdGuard` **+ `PlatformPermissionGuard`** (เพิ่มเมื่อ 2026-08-20) | `news.delete` (ทั้งสองแกน) | `news.controller.ts` |
| `GET /api/news`, `GET /api/news/:id` | `AppIdGuard` เท่านั้น — ไม่มีการตรวจสอบ permission ฝั่งแพลตฟอร์ม | `news.findAll` / `news.findOne` | `news.controller.ts` |

ความไม่สมมาตรที่เกี่ยวข้องกับผู้ทดสอบ ซึ่งสะท้อนโมดูล Applications:

- **`.delete` ไม่มี route ของ SPA แต่มีการตรวจสอบฝั่ง server** ไม่มี route ใดต้องการมันและหน้า edit ไม่มี action ลบ — surface ฝั่ง *client* ของ key คือรายการใน dropdown ของ row ในหน้า list บวกปุ่ม Delete Selected แบบ bulk session ที่มีเฉพาะ `.read` เห็น list พร้อม dropdown action ที่ว่างเปล่าและไม่มี checkbox การเลือกเลย (`canSelect` ต้องการ `.update` หรือ `.delete`) นี่เป็นข้อเท็จจริงเรื่อง client-routing เท่านั้น: ตั้งแต่ 2026-08-20 endpoint `DELETE` เองก็ปฏิเสธ caller ที่ไม่มี `news.delete` ด้วยเช่นกัน โดยไม่ขึ้นกับสิ่งที่ SPA แสดง
- **Save ไม่ถูก gate แยกต่างหาก** เฉพาะ *toggle* Edit เท่านั้นที่ถูกห่อด้วย `<Can>`; แถว Save/Cancel render เฉพาะในโหมดแก้ไข ซึ่งไปถึงไม่ได้หากไม่มี toggle (โหมด create อยู่หลัง `.create` ของ route) การบังคับใช้ฝั่ง backend บน `PUT` — ทั้งข้อกำหนด `doc_version` **และ** ตั้งแต่ 2026-08-20 การตรวจสอบ permission `news.update` — คือขอบเขตจริง
- **CTA ของ empty-state ถูก gate เหมือนกับปุ่ม Add ใน header** affordance "Add News" ของ `ListEmptyState` ถูกห่อด้วย `<Can permission="news.create">` ตัวเดียวกับปุ่มใน header (`NewsManagement.tsx:640`) — session ที่ไม่มี `.create` ไม่เห็นทั้งสองอย่าง
- **Export ไม่ถูก gate** session ใดก็ตามที่เข้าถึง list ได้ (`.read`) สามารถส่งออก CSV ของหน้าที่โหลดอยู่ได้ — ปุ่ม Export ไม่มีการห่อ `<Can>` เลย
- **route ที่อ่านไม่มีการบังคับใช้บนแกน permission ของผู้ใช้เลย โดยตั้งใจถาวร** `news.read` gate เฉพาะ route/sidebar ของ SPA; `GET /api/news`, `/:id`, `/tags` และ `/summary` ยอมรับ caller ที่ authenticated จาก application ที่ app-id ผ่านทุกคน โดยไม่มีการตรวจสอบ `news.read` ฝั่ง server — เพราะ route เดียวกันนี้ให้บริการผู้ใช้ระดับ tenant ของแอปมือถือซึ่งไม่มี role ระดับแพลตฟอร์มเลย อย่าคาดหวัง 403 จาก route ทั้งสี่นี้เพราะขาด key `news.*` — คาดหวังได้เฉพาะจาก `x-app-id` ที่ขาดหรือไม่ได้รับอนุญาต
- **Bulk action ใช้ key เดียวกับ single-row** — Publish/Archive Selected gate ด้วย `.update` (key เดียวกับ Edit ของ row และ toggle Edit), Delete Selected ด้วย `.delete` ไม่มี permission "bulk" แยกต่างหาก; session ที่แก้ไขหรือลบได้หนึ่ง row ก็ bulk-edit หรือ bulk-delete ได้หลาย row เช่นกัน โดยยังอยู่ภายใต้การตรวจสอบ `doc_version` ฝั่ง server ต่อ row และ (ตั้งแต่ 2026-08-20) การตรวจสอบ permission ฝั่ง server ต่อ row เช่นกัน
- **Key ของ route เป็นอิสระต่อกัน** `.update` อย่างเดียว deep-link ไป `/news/:id/edit` ได้ขณะที่ `/news` ปฏิเสธ; `.create` อย่างเดียวไปถึง `/news/new` ทาง URL ได้
- **`activity_log.read` เป็น grant ที่แยกจาก key `news.*` ทุกตัวจริง ๆ** — session สามารถถือ View History โดยไม่มี key `news.*` ใดเลย หรือกลับกันก็ได้; ทดสอบทั้งสองอย่างแยกกัน
- **role ที่ seed ไว้ถือ key ทั้งสี่ไม่เท่ากัน** (`seed.platform-role-permission.data.ts`): Platform Admin ถือ `news.*` (ทั้งสี่); Support Manager ถือ `news.read`/`.create`/`.update` แต่**ไม่มี** `.delete`; Support Staff ถือ `news.read` เท่านั้น; Security Officer ไม่มีสักตัวในสี่ตัวนี้ session แบบ Support Manager คือวิธีที่ถูกที่สุดในการจำลอง "`.delete` ถูกปฏิเสธ ที่เหลืออนุญาตหมด" โดยไม่ต้องสร้าง role เอง
- sidebar filter เป็น UX ไม่ใช่ security — session ที่ไม่มี `news.read` ยังพิมพ์ URL ได้และจะชน route guard session แบบ super-admin และ bootstrap ผ่านทุก gate; อย่า QA เมทริกซ์นี้จาก session แบบนั้น

## 3. กฎการกำหนดเป้าหมายและการมองเห็น

ฝั่งเขียน micro-cluster ตรวจสอบการกำหนดเป้าหมายตอน create และตอน update ใด ๆ ที่แตะ field นี้: `business_unit_ids` ต้องเป็น array ของ string และทุก id ที่ unique ต้อง match กับ row ของ `tb_business_unit` ที่ live อยู่ ไม่เช่นนั้นได้ 400 SPA ยังกำหนดเพิ่มว่าต้องมี ≥1 BU เมื่อใดก็ตามที่ checkbox "Visible to all business units" ไม่ถูกติ๊ก — ดังนั้น `[]` ถูกผลิตขึ้นได้โดยจงใจเท่านั้น ด้วยการติ๊กกล่อง

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
| 1 | Archived เทียบกับ soft-deleted | `archived` ยังอยู่ใน admin list (badge, filter ได้) และอยู่นอก public feed; row ที่ถูก soft-delete ตอนนี้ถูก**ตัดออกฝั่ง server** จาก `GET /api/news` แล้ว (ยืนยันว่าแก้แล้วนับจาก sync ครั้งก่อน — query ของ list ใน micro-cluster filter `deleted_at: null`) และ 404 บน `GET :id` | Archive เพื่อปลดระวางเนื้อหาแบบมองเห็นได้; ลบเพื่อเอามันออกจาก admin list ทั้งหมด การซ่อนฝั่ง client แบบเดิมของ SPA (`deleted_at`/`audit.deleted.at`) ตอนนี้เป็นเพียง no-op — raw JSON ของ list ใน Debug Sheet ก็ไม่มี row ที่ถูกลบแล้วเช่นกัน |
| 2 | สถานะถูก flip `published` → `draft` | `published_at` ถูก**คงไว้** ไม่ถูกเคลียร์ (ยืนยันแล้วใน `update` ของ micro-cluster); บทความออกจาก public feed เพราะ filter สถานะอย่างเดียว | list ยังแสดง timestamp ของ Published เดิมบน row ที่เป็น draft — เป็นไปตามที่ออกแบบ ไม่ใช่ bug การ re-publish คงค่าประทับเดิมไว้ |
| 3 | การ re-publish บทความที่ archived | กลับเข้า public feed ภายใต้ `published_at` **เดิม** (server ประทับเฉพาะ row ที่ไม่เคย publish เท่านั้น) | เมื่อเรียงตาม `published_at DESC` ฝั่ง public บทความเก่าที่ re-publish จะ*ไม่*กระโดดขึ้นไปอยู่บนสุด |
| 4 | `published_at` แบบระบุชัด/ลงวันที่อนาคต | ตั้งได้ผ่าน API เท่านั้น (SPA ไม่เคยส่งมัน); วันที่อนาคตกัน row ที่ `published` ไว้นอก feed จนกว่าเวลานั้นจะผ่านไป | เป็นการกำหนดเวลาเผยแพร่โดยพฤตินัย; ทดสอบได้ผ่าน API หรือ Bruno เท่านั้น ไม่ใช่ SPA |
| 5 | field `image` แบบ legacy | SPA อ่าน `image_url \|\| image` ทุกที่; gateway ปัจจุบัน emit `image_url` (presigned, หมดอายุ 1 ชั่วโมง) และตัด token ที่จัดเก็บออก | thumbnail ที่ 404 หลังหน้า list ค้างไว้นานคือ presigned URL ที่หมดอายุ — การ refresh จะ refetch URL ใหม่ |
| 6 | GIF หรือรูปใหญ่เกิน | picker ของ SPA รับ `image/gif` และบังคับเฉพาะ ≤5 MB; backend ปฏิเสธ GIF (`BAD_FILE_TYPE`) และ >2048×2048 px (`BAD_DIMENSIONS`) ตอน save | รายการ accept ของ client/server ต่างกัน — ความล้มเหลวปรากฏเป็น "Failed to save news" ระดับฟอร์ม ไม่ใช่ตอนเลือกไฟล์ |
| 7 | การลบรูปที่ save ไว้ | ทำไม่ได้จาก SPA: update แบบ JSON ไม่แตะรูป และปุ่ม Remove ของ ImageUpload เคลียร์เฉพาะการเลือกที่*ค้างอยู่*เท่านั้น | วิธีเดียวที่จะเอารูปออกคือแทนที่มัน (ไฟล์ MinIO เก่าจะถูกลบฝั่ง server) |
| 8 | BU ถูก soft-delete หลังถูกกำหนดเป้าหมาย | การตรวจสอบรันตอนเขียนเท่านั้น; id ค้างยังอยู่ใน `business_unit_ids` และยัง match กับ `array_contains` ของ public feed | การ save บทความอีกครั้งโดยแตะ field การกำหนดเป้าหมายจะ re-validate แล้ว**ปฏิเสธ** id ค้างนั้น — ผู้แก้ไขต้องเอามันออกจึงจะ save ได้ |
| 9 | sort ของ list ดูเหมือนพัง | server override ทุก sort เป็น `updated_at DESC`; ค่าเริ่มต้น `published_at:desc` ของ SPA และ header ที่คลิกได้ถูกส่งไปแต่ถูกเพิกเฉย | ความแตกต่างที่ทราบกัน ([Data Model](/th/platform/news/data-model) §5) — อย่ายื่น defect ของการ sort รายคอลัมน์จนกว่าการ override จะถูกถอดออก |
| 10 | สองบทความ หัวข้อเดียวกัน | อนุญาต — ไม่มี unique constraint บน `title` | แยกแยะด้วย id (Debug Sheet) เมื่อทดสอบ |
| 11 | `doc_version` ล้าสมัยตอน save หรือ bulk action | `PUT` ที่มี `doc_version` ล้าสมัยคืน 409; SPA แสดง "This record was changed by someone else" ทิ้งรูปที่ค้างอยู่ และ refetch | ทำซ้ำได้โดยเปิดบทความเดียวกันสองแท็บ save ในแท็บหนึ่งแล้ว save (หรือ bulk-publish) ในอีกแท็บ |
| 12 | Bulk action บนการเลือกแบบผสม | แต่ละ row ถูก update/delete แยกอิสระผ่าน `Promise.allSettled`; การล้มเหลวของ row หนึ่ง (เช่น `doc_version` conflict) ไม่บล็อก row อื่น | คาดว่าจะได้ toast "N succeeded, M failed" ไม่ใช่ผลลัพธ์แบบทั้งหมดหรือไม่มีเลย — ไม่มี transaction ครอบการเลือกทั้งหมด |
| 13 | Tag เกินขีดจำกัดของ server | ≤20 tags และ ≤40 ตัวอักษรต่อ tag ถูกบังคับใช้โดย micro-cluster เท่านั้น; `ChipInput` ของ SPA ไม่มีเพดานฝั่ง client | การเพิ่ม tag ตัวที่ 21 หรือ tag ที่ยาวกว่า 40 ตัวอักษรผ่าน UI ได้อย่างเงียบ ๆ และจะล้มเหลวตอน save เท่านั้น (400) |
| 14 | session แบบ Support Staff (หรือ `news.read`-only ใด ๆ) เรียก `POST`/`PUT`/`DELETE /api/news*` โดยตรง | 403 ตั้งแต่ 2026-08-20 (`PlatformPermissionGuard` + `RequirePlatformPermission`) — ก่อนแก้จะสำเร็จโดยไม่สนใจ RBAC key เลย | การ regression ตรงนี้ (การเขียนสำเร็จสำหรับ role ที่อ่านได้อย่างเดียว) คือช่องโหว่ security จริง ไม่ใช่ช่องว่าง UX — ต่างจากพฤติกรรมฝั่งอ่านของกรณีพิเศษ 15 |
| 15 | session ที่ไม่มี key `news.*` **เลย** จาก application ที่ app-id ผ่าน เรียก `GET /api/news` โดยตรง | 200 — สำเร็จ นี่คือความตั้งใจ ไม่ใช่ bug: route อ่านทั้งสี่ตรวจสอบเฉพาะ `x-app-id` ไม่เคยตรวจสอบ permission ของผู้เรียกเอง เพราะผู้ใช้ระดับ tenant ของแอปมือถือใช้ route เดียวกันนี้ร่วมกันและไม่มี role ระดับแพลตฟอร์มเลย | อย่ายื่นเป็น defect แบบ permission-bypass แทนที่ให้ตรวจสอบว่า *SPA* ยังซ่อนรายการ sidebar "News" และปฏิเสธ `/news` สำหรับ session แบบนี้ (ฝั่ง client เท่านั้น) |

## 5. คำแนะนำ

- **ทดสอบสองเรื่องราวแยกจากกัน** ตรวจสอบการ gate ผู้เขียนด้วย session ที่ถือ key `news.*` ทีละหนึ่งตัวเป๊ะ ๆ; ตรวจสอบการส่งมอบด้วยการเรียกแบบ anonymous ดิบ ๆ ไปยัง `/api/public/news` — การ save ใน SPA ที่ผ่านไม่ได้บอกอะไรเลยเกี่ยวกับว่าใครอ่านบทความได้
- **Probe เมทริกซ์ lifecycle × feed** สำหรับบทความหนึ่งตัว เดิน draft → published → archived → published และยืนยันการเป็นสมาชิกของ feed กับ `published_at` ที่คงที่ในแต่ละขั้น (case 2–3 ด้านบน)
- **QA การกำหนดเป้าหมายต้องใช้สามการเรียกต่อบทความ:** public feed โดยไม่มี `bu_id`, ด้วย id ของ BU ที่ถูกกำหนดเป้าหมาย และด้วย id ที่ไม่ถูกกำหนดเป้าหมาย — บวก endpoint แบบรายการเดียวเพื่อยืนยันว่ามันข้ามการตรวจสอบ BU (§3 ข้อ 3)
- **ใช้แกน machine หนึ่งครั้ง** เรียก `/api/news` ด้วย bearer ที่ valid แต่ application ที่ไม่มี grant `news.*` เพื่อยืนยันว่าการปฏิเสธของ `AppIdGuard` เป็นอิสระจาก RBAC key ของผู้ใช้
- **ใช้แกน write-permission แยกต่างหาก** ด้วย session ที่ถือ `news.read` เท่านั้น ยืนยันว่า `POST`/`PUT`/`DELETE /api/news*` คืน 403 แล้ว (แก้เมื่อ 2026-08-20) — และยืนยันว่า route อ่านทั้งสี่ยังคืน 200 สำหรับ session เดียวกัน เพราะครึ่งนั้นเป็นความตั้งใจ ไม่ใช่ช่องว่างที่หลงเหลือ (กรณีพิเศษ 14–15)
- **QA เส้นทางล้มเหลวของ bulk toolbar** ไม่ใช่แค่เส้นทางสำเร็จ: เตรียม row ที่ปกติผสมกับ row ที่เพิ่งถูกคนอื่นแก้ไข bulk-publish ทั้งคู่ แล้วยืนยัน toast แบบสำเร็จบางส่วนและ gate ของรหัสยืนยัน (รหัส 6 ตัวอักษรใหม่ทุกครั้งที่เปิด dialog)
- **ทดสอบ View History แยกจาก key `news.*`** — `activity_log.read` เป็น grant แยกต่างหาก; session อาจถืออย่างใดอย่างหนึ่ง ทั้งคู่ หรือไม่มีเลย
- **ปฏิบัติกับ sort ของ list ที่ถูกเพิกเฉยเป็น issue ที่ทราบกัน** — ตรวจสอบว่าพฤติกรรมตรงกับ [Data Model](/th/platform/news/data-model) §5 แทนที่จะยื่น defect ซ้ำซ้อน; เป็นช่องว่างของ affordance/UX โดยการบังคับใช้ฝั่ง server (การ override เป็น `updated_at DESC`) ยังสมบูรณ์ CTA ของ empty-state **ไม่ใช่** issue ที่ทราบกันอีกต่อไป — มันถูก gate ด้วย `<Can>` เหมือนกับปุ่มใน header

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard ทั้งสาม) · `src/components/nav/platformNav.ts` (รายการ sidebar, บรรทัด 27 — ไม่ใช่ `Layout.tsx` ซึ่งไม่ได้กำหนดรายการ nav ใด ๆ) · `src/pages/NewsManagement.tsx` / `NewsEdit.tsx` (gate `<Can>`, bulk toolbar, View History) · `src/utils/permissions.ts` (`PLATFORM_SCOPED_RECORD`) · `src/components/activityTrail/{ActivityTrailSheet,useRowActivityTrail,constants}.tsx` (View History; `AUDIT_RECORDING_STARTED_ON_PHASE_2` = 2026-08-31) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/news.controller.ts` (KeycloakGuard บนทุก route; `AppIdGuard` ราย route รวมถึง `GET tags`/`summary`; `PlatformPermissionGuard` + `RequirePlatformPermission` เพิ่มบน route เขียนสามตัวเท่านั้น commit `9b474a3fc1c4478ef18d5e5caf9b62d9098f1344`, 2026-08-20) · `public-news.controller.ts` (ไม่มี guard) · `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (การตรวจสอบ BU, การ normalize tag, lock ของ `doc_version`, filter soft-delete, filter ของ `findPublicAll`/`findPublicOne`) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts` (key ทั้งสี่) · `seed.platform-role-permission.data.ts` (Platform Admin ถือทั้งสี่; Support Manager ถือ read/create/update ไม่มี delete; Support Staff ถือ read เท่านั้น; Security Officer ไม่มีเลย)
**Cross-link:** [หน้า landing ของ News](/th/platform/news) &nbsp;·&nbsp; [Data Model](/th/platform/news/data-model) &nbsp;·&nbsp; [UI Screens](/th/platform/news/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/th/platform/rbac/permissions) &nbsp;·&nbsp; [Applications](/th/platform/applications)
