---
title: Broadcasts — สิทธิ์ (Permissions)
description: gate ตัวเดียว broadcast.send บน route, sidebar และปุ่ม Send — ตอนนี้ยืนยันว่าถูกบังคับใช้ฝั่ง server ด้วยแล้ว (backend PR #239) พร้อมข้อพึงระวังเรื่องความหยาบของ grant ที่ document ไว้ — semantics การส่งมอบราย target mode และเมทริกซ์กรณีพิเศษสำหรับผู้ทดสอบ
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, broadcasts, permissions
editor: markdown
dateCreated: 2026-06-10T16:00:00.000Z
---

# Broadcasts — สิทธิ์ (Permissions)

> **At a Glance**
> **Gate:** key เดียว — `broadcast.send` — บน route, รายการ sidebar และปุ่ม Send &nbsp;·&nbsp; **ฝั่ง server (ยืนยันว่าแก้แล้วนับจาก sync ครั้งก่อน):** ทั้งสอง endpoint ตอนนี้บังคับใช้ `broadcast.send` ผ่าน `PlatformPermissionGuard` (backend PR #239) — ไม่ใช่ฝั่ง client เท่านั้นอีกต่อไป &nbsp;·&nbsp; **ความหยาบที่ทราบ:** guard ผ่านได้ด้วย grant ระดับแพลตฟอร์ม **หรือ** grant ใน cluster ใดก็ได้หนึ่งตัว ดังนั้น grantee ที่ scope ไว้ราย cluster ยังคงเข้าถึงโหมดส่งแบบ system-wide ได้ฝั่ง server — การ scope ราย cluster แบบจริงจังถูกเลื่อนออกไปอย่างชัดเจน ไม่ใช่ bug &nbsp;·&nbsp; **Key กำพร้า:** `broadcast.read` ถูก seed ไว้แต่ไม่ gate อะไรเลยใน SPA &nbsp;·&nbsp; **การส่งมอบ:** กลุ่มผู้ชมถูก resolve จากตัว row (`category` + `scope_id`) ตอนอ่าน; การ push ผ่าน socket แบบ live เฉพาะการส่งที่ไม่กำหนดเวลาเท่านั้น

## 1. ภาพรวม

Broadcasts มีเรื่องราวของ gate ที่เรียบง่ายที่สุดใน book ของ Platform: key ของ [Platform RBAC](/th/platform/rbac) ตัวเดียว `broadcast.send` คุ้มกันทุก surface ของ SPA — ไม่มีการแบ่ง read/create/update/delete เพราะการส่งเป็นการดำเนินการเดียว seed (`seed.platform-permission.ts`) ลงทะเบียนสอง key คือ `broadcast.read` และ `broadcast.send` แต่ `broadcast.read` เป็น**key กำพร้า (orphan)**: ไม่มี route, รายการ sidebar หรือ `<Can>` อ้างอิงมันที่ไหนเลย (ที่ปรากฏใน SPA แห่งเดียวของมันคือ mock permission list เฉพาะ dev ใน `src/utils/permissions.ts`) สันนิษฐานว่าสำรองไว้สำหรับ surface ของ broadcast history ในอนาคต

**ยืนยันว่าแก้แล้วนับจาก sync ครั้งก่อน:** ช่องว่างฝั่ง server ที่เคย document ไว้ — endpoint ทั้งสองของ gateway ตรวจสอบเฉพาะ bearer authentication โดย `broadcast.send` ถูกบังคับใช้ฝั่ง client เท่านั้น — ปิดแล้ว backend commit `1fa15ec02` ("Server-side authz enforcement: guard broadcast sends + close DB-password leak (#239)") เพิ่ม `PlatformPermissionGuard` + `@RequirePlatformPermission('broadcast.send')` ให้กับทั้ง `POST /api/notifications/broadcasts/system` และ `/bu` commit ฝั่ง frontend คู่กัน (`9911b8f`) อัพเดท comment ของ code เองเพื่อบันทึกการแก้ไข และซ่อม bug ของ `parseApiError` ที่เคยกลืน body error แบบ `{ error: { message } }` ซ้อนอยู่อย่างเงียบ ๆ — ดังนั้น 403 จาก guard ที่บังคับใช้ใหม่ตอนนี้แสดงข้อความจริงของมัน ("Missing platform permission: broadcast.send") แทนข้อความทั่วไป

การบังคับใช้จงใจทำแบบ**หยาบ (coarse)** โดยการออกแบบ ไม่ใช่ความพลั้งเผลอ: `PlatformPermissionGuard` resolve permission ที่มีผลของ caller แล้วเรียก `PlatformPermissionService.has()` ซึ่งคืนค่า true หาก key ที่ต้องการอยู่ใน scope **ระดับแพลตฟอร์ม** **หรือ** ใน scope ของ **cluster ใดก็ได้หนึ่งตัว** (ยืนยันด้วยการอ่าน `platform-permission.service.ts` โดยตรง) ผู้ใช้ที่ได้รับ `broadcast.send` บน cluster เดียวจึงยังผ่าน guard สำหรับการส่งแบบ `system_all` ที่เข้าถึงผู้ใช้ทั้งหมดทั่วแพลตฟอร์มได้ — guard ยังไม่ตรวจสอบว่า "action นี้ scope ระดับแพลตฟอร์มหรือเป็นของ cluster ของ caller เอง" comment ของ code เองอธิบายว่าการ scope ราย cluster แบบ**จริงจัง** (system-wide ต้องการ grant ระดับแพลตฟอร์มเท่านั้น; โหมด BU scope ไปที่ cluster ของ BU เป้าหมายเอง) ถูกเลื่อนออกไปอย่างชัดเจน รอโครงสร้างพื้นฐานฝั่ง backend ในการ resolve `bu_code → cluster_id` แล้วตรวจสอบ bucket นั้นโดยเฉพาะ — โครงสร้างพื้นฐานที่ยังไม่มีอยู่ใน repo นี้ การตรวจสอบ `canSendSystem`/`canSend` ของ SPA เองก็ไม่มี scope เช่นกัน ดังนั้น client และ server ตอนนี้**เห็นตรงกัน**ในขอบเขต (แบบหยาบ) เดียวกัน — นี่เป็นข้อพึงระวังที่แคบกว่าและยังคงเป็นจริง ไม่ใช่ข้อค้นพบ "ไม่มีการตรวจสอบฝั่ง server เลย" จาก sync ครั้งก่อน

## 2. เมทริกซ์ของ gate

| Surface | กลไก | Key | แหล่งที่มา |
|---|---|---|---|
| `/broadcasts/new` | `PrivateRoute requiredPermission` | `broadcast.send` | `src/App.tsx` |
| sidebar "Send Broadcast" (กลุ่ม Content, ไอคอน Megaphone) | nav filter ของ `Layout.tsx` | `broadcast.send` | `src/components/Layout.tsx` |
| ปุ่ม Send (sticky action bar ด้านล่าง) | `<Can>` | `broadcast.send` | `BroadcastCompose.tsx` (เพิ่มใน commit `f3f77cf` ของ carmen-platform) |
| แท็บ "All users" + "Specific users" | `hasPermission('broadcast.send')` ภายใน component (`canSendSystem`) | `broadcast.send` | `BroadcastCompose.tsx` |
| `POST /api/notifications/broadcasts/system` / `/bu` | `KeycloakGuard` + `PlatformPermissionGuard` | `broadcast.send` (หยาบ: platform-wide หรือ cluster ใดก็ได้) | `notification.controller.ts` ของ gateway, `platform-permission.guard.ts` |

การอ่านที่เกี่ยวข้องกับผู้ทดสอบ:

- **ทุก gate ของ SPA เป็น key เดียวกัน** ดังนั้นชั้นภายใน component จึงซ้ำซ้อนในวันนี้: session ที่ไม่มี `broadcast.send` ไม่มีวันผ่าน route guard (`Forbidden` ภายใน shell ของ Layout — เปลี่ยนชื่อจาก `AccessDenied` แบบ inline เดิม) การซ่อนแท็บและ `<Can>` รอบปุ่ม Send จึงเป็น defensive code ที่ไปไม่ถึง พวกมันจะสังเกตได้ก็ต่อเมื่อ key ของ route guard เคยแตกต่างจากของ component เท่านั้น
- **ขอบเขตการบังคับใช้จริงตอนนี้คือ authorization ไม่ใช่แค่ authentication แล้ว** — ทั้ง SPA และ API ต้องการ `broadcast.send` และการ POST โดยตรงจาก session ที่ไม่มี `.send` ตอนนี้ล้มเหลวด้วย 403 (ไม่ใช่สำเร็จอย่างเงียบ ๆ) นี่เป็นการพลิกกลับข้อค้นพบของ sync ครั้งก่อน
- **ช่องว่างที่เหลืออยู่คือความละเอียดของ scope ไม่ใช่การมีอยู่ของการตรวจสอบ** ผู้ใช้ที่ได้รับ `broadcast.send` scope ไว้ cluster เดียวยังส่ง broadcast แบบ system-wide (`system_all`) ผ่าน API ได้ (และผ่าน SPA ด้วย เพราะ `canSendSystem` ก็ไม่ scope เช่นกัน) — server และ client สอดคล้องกัน แต่ทั้งคู่ไม่จำกัด grant ที่ scope ราย cluster ให้อยู่แค่กลุ่มผู้ชมของ cluster นั้นเอง ปฏิบัติกับสิ่งนี้เป็นข้อจำกัดที่ทราบและถูกเลื่อนออกไปเมื่อเขียน test case ไม่ใช่ defect ที่ต้องยื่นใหม่
- Reset, แท็บ target และ field ของฟอร์มทั้งหมดไม่ถูก gate — เฉพาะ Send เท่านั้นที่ถูกห่อ
- session แบบ super-admin และ bootstrap ผ่านทุก gate; อย่า QA เมทริกซ์นี้จาก session แบบนั้น

## 3. semantics การส่งมอบราย target mode

ใครได้รับ broadcast จริง ๆ ถูกตัดสินโดย micro-notification รายโหมด:

| Mode | การจัดเก็บ | กลุ่มผู้ชม (เส้นทางอ่าน) | Live push (เฉพาะไม่กำหนดเวลา) | Side-effect ของอีเมล |
|---|---|---|---|---|
| `system_all` | row ของ `tb_broadcast_notification` หนึ่งตัว, `category = 'system-to-user'`, `scope_id = null` | **ผู้ใช้ทุกคน** — list query แบบ scope จะ match row ของ `system-to-user` โดยไม่มีเงื่อนไข | socket emit ไปยังทุก user id ที่ active และไม่ถูกลบ | อีเมลของผู้ใช้ active ทุกคน |
| `system_users` | row ของ `tb_notification` หนึ่งตัว**ต่อ id ผู้รับที่มีอยู่จริง** (id ที่ไม่รู้จักถูกทิ้งอย่างเงียบ ๆ) | เฉพาะผู้ใช้เหล่านั้นเป๊ะ ๆ — row ส่วนบุคคล, match ที่ `to_user_id` | socket emit ราย row แล้วตั้ง `is_sent = true` | อีเมลของผู้ใช้ที่ถูกเลือก |
| `bu` | row ของ `tb_broadcast_notification` หนึ่งตัว, `category = 'bu-to-user'`, `scope_id` = id ของ BU ที่ resolve แล้ว | ผู้ใช้ที่การเป็นสมาชิก `tb_user_tb_business_unit` (row ที่ live) มี BU ของ scope | socket emit ไปยัง id ของสมาชิก BU ปัจจุบัน | อีเมลของสมาชิก BU |

พฤติกรรมสามข้อที่ตามมาจาก "กลุ่มผู้ชมถูก resolve ตอนอ่าน" (เฉพาะ row แบบ broadcast):

1. **การเป็นสมาชิกถูกประเมินราย query ไม่ใช่รายการส่ง** ผู้ใช้ที่ถูกเพิ่มเข้า BU *หลัง*จาก broadcast แบบ BU ถูกส่งไปแล้วยังคงเห็นมัน — ใน list ของ unread อย่างไม่มีกำหนด (ไม่มีกรอบเวลา) และใน list ของ recent เป็นเวลา 30 วัน; ผู้ใช้ที่ถูกถอดออกจะหยุดเห็น ไม่มี snapshot ของผู้รับ
2. **row ที่กำหนดเวลาไว้ส่งมอบแบบ passive** list query ซ่อน row จนกว่า `scheduled_at <= NOW()`; เมื่อถึงกำหนด broadcast ปรากฏตอน fetch ครั้งถัดไป **ไม่มีการ push ผ่าน socket เกิดขึ้นเลยสำหรับ broadcast ที่กำหนดเวลาไว้** — การ emit ตอน create ถูกข้ามและไม่มีอะไร replay มันภายหลัง
3. **read state เป็นแบบ lazy และรายผู้ใช้** (`tb_user_broadcast_action`, unique ต่อ broadcast×user): ไม่มี row ถูกเขียน ณ เวลาส่ง ดังนั้น "ส่งแล้ว" ไม่มีวันยืนยันได้จากฐานข้อมูลนอกเหนือจากการมีอยู่ของ row ของ broadcast เอง

การ fan-out อีเมล (เฉพาะเมื่อ SMTP ถูก config บน micro-notification; ระงับรายการส่งได้ผ่าน `metadata.notify_email = false` ซึ่ง SPA ไม่เคยส่ง) ทำงาน**ตอน create แม้กับการส่งแบบกำหนดเวลา** — การกำหนดเวลาเลื่อนการมองเห็นแบบ in-app ไม่ใช่อีเมล

## 4. กรณีพิเศษ

| # | สถานการณ์ | พฤติกรรม | หมายเหตุสำหรับผู้ทดสอบ |
|---|---|---|---|
| 1 | ผู้รับค้าง (stale recipients) รั่วเข้า "All users" | การเลือกผู้รับใต้ *Specific users* แล้วสลับไป *All users* **ไม่**เคลียร์พวกเขา; `buildSystemPayload` รวม `userIds` เมื่อใดก็ตามที่มีผู้รับอยู่ ดังนั้นการส่งกลายเป็นแบบกำหนดเป้าหมายอย่างเงียบ ๆ — ขณะที่ dialog ยืนยันอ้างว่า "Send to ALL users?" | ยืนยันแล้วใน `BroadcastCompose.tsx` ณ 2026-06-10: การสลับแท็บคง state ของฟอร์มไว้และการ validate ของ `system_all` เพิกเฉยต่อผู้รับ Reset (หรือการลบ badge ออก) เคลียร์พวกเขา ควรค่าแก่การยื่น bug report กับ SPA |
| 2 | การส่งแบบ *Specific users* ที่กำหนดเวลาไว้มองเห็นได้ทันที | list query ของ row ส่วนบุคคล**ไม่** filter `scheduled_at` (เฉพาะ query ของ row แบบ broadcast เท่านั้นที่ filter) ดังนั้น notification แบบกำหนดเป้าหมายที่กำหนดเวลาไว้ปรากฏใน list ของผู้รับทันที; live emit ที่เลื่อนไว้ไม่มีวันเกิดขึ้น — `getScheduledNotifications()` (ครบกำหนด + ยังไม่ส่ง) **ไม่มี caller** ที่ไหนเลย และ NotificationExecutor ของ micro-cronjobs โพสต์เฉพาะ job ที่ config ไว้แบบ recurring เท่านั้น | comment ของ DTO ฝั่ง gateway สัญญาว่า "the live emit is deferred to the scheduled worker" แต่ worker แบบนั้นไม่มีอยู่จริง การกำหนดเวลาถูกเคารพเฉพาะการส่งแบบ `system_all`/`bu` เท่านั้น |
| 3 | ไม่มีวิธีดูหรือยกเลิก broadcast ที่ส่ง/กำหนดเวลาไว้แล้ว | SPA ไม่มี route ของ list และไม่มี endpoint ของ gateway หรือ micro-notification ตัวใด list, update หรือ delete broadcast read query เคารพ `deleted_at` แต่ไม่มีอะไรเขียนมัน | การถอนการส่งผิดเป็นการ soft-delete บน DB ด้วยมือ (`UPDATE tb_broadcast_notification SET deleted_at = NOW() …`) สำหรับ broadcast ที่กำหนดเวลาผิด นี่เป็นเส้นทาง abort เดียว |
| 4 | เวลาที่กำหนดอยู่ในอดีต | การ validate ฝั่ง client ปฏิเสธ ("Scheduled time must be in the future" กับ `Date.now()` ณ เวลา validate); backend ไม่ validate — caller ของ API ที่ส่ง `scheduled_at` ในอดีตสร้าง row ที่มองเห็นได้ทันที (มันผ่าน filter `<= NOW()`) แต่ไม่มีวันถูก live-push | SPA *สามารถ*ปล่อยเวลาในอดีตหลุดผ่านไปได้: การ validate รันตอนคลิก Send แต่การยืนยัน**ไม่** re-validate — dialog ยืนยันที่ถูกเปิดทิ้งไว้จนเลยเวลาที่กำหนดจะ submit `scheduled_at` ที่กลายเป็นอดีตไปแล้ว |
| 5 | custom type ถูกปฏิเสธ | Other… ต้องการ `[A-Z0-9_]+`, ≤50 ตัวอักษร; input อัพเปอร์เคสทั้งข้อความที่พิมพ์และที่ paste โดยอัตโนมัติ ดังนั้นตัวพิมพ์เล็กไม่มีวันไปถึงการ validate — error ของ regex ไปถึงได้เฉพาะด้วยอักขระต้องห้าม เช่น ช่องว่างหรือยัติภังค์ | server รับ varchar(255) ใดก็ได้ — regex เป็นของ SPA เท่านั้น caller ของ API จัดเก็บ string ของ `type` ใดก็ได้ตามอำเภอใจ |
| 6 | รายการ BU โหลดล้มเหลว / มี BU มากกว่า 100 ตัว | การโหลดล้มเหลวแสดง error ที่ parse แล้วพร้อม Retry แบบ inline; fetch มีเพดานที่ `perpage: 100` ดังนั้น BU ที่เกิน 100 ตัวแรกเลือกไม่ได้ | เพดานนี้มองไม่เห็นใน UI — บน cluster ขนาดใหญ่ให้ตรวจสอบว่า BU เป้าหมายปรากฏก่อนยื่น defect "BU หายไป" |
| 7 | code ของ BU ไม่รู้จัก หรือ BU ถูก soft-delete ณ เวลาส่ง | micro-notification resolve `bu_code` กับ BU ที่ live; ความล้มเหลวปรากฏเป็น "Failed to create notification" ใน envelope แบบ 500 พร้อมรายละเอียด `Business unit not found: <code>` | ไปถึงได้จาก SPA เฉพาะใน race เท่านั้น (BU ถูกลบระหว่างการโหลดตัวเลือกกับการส่ง) — ตัว select เสนอเฉพาะ BU ที่ live |
| 8 | การยืนยันแบบ destructive ของ `system_all` | เป็นโหมดเดียวที่มีปุ่มยืนยันสีแดงและคำเตือน "This broadcast will reach every user in the system." | เป็น friction เฉพาะ UX — endpoint เบื้องหลังมันเหมือนกันทุกประการ |
| 9 | การส่งซ้ำ | ไม่มี unique constraint, ไม่มี idempotency key — การยืนยัน compose สองครั้งสร้างสอง row แต่ละตัวถูกส่งมอบ | ปุ่ม Send เป็น disabled ขณะกำลังส่ง ดังนั้นการคลิกครั้งเดียวไม่สามารถ post ซ้ำได้ |
| 10 | session ที่ไม่มี `.send` post โดยตรง | **ยืนยันว่าแก้แล้วนับจาก sync ครั้งก่อน** `PlatformPermissionGuard` ตอนนี้ปฏิเสธด้วย 403 (`Missing platform permission: broadcast.send`) ก่อนที่ request จะไปถึง micro-notification; `parseApiError` ที่แก้แล้วแสดงข้อความนั้นตรง ๆ ใน SPA แทนที่จะถูกกลืนหรือแสดงผิดเพี้ยน | เดิมทีสิ่งนี้เคยสำเร็จ (การบังคับใช้ฝั่ง client เท่านั้น); อย่ายื่นข้อค้นพบเดิมซ้ำ — ตรวจสอบ 403 และข้อความที่ถูกต้องแทน |
| 11 | grant ที่ scope ราย cluster ส่ง broadcast แบบ `system_all` | `PlatformPermissionGuard`/`PlatformPermissionService.has()` ผ่านด้วย grant ของ cluster **ใดก็ได้** ไม่ใช่แค่ระดับแพลตฟอร์ม — ผู้ใช้ที่ได้รับ `broadcast.send` บน cluster เดียวยังเข้าถึงผู้ใช้ทั้งหมดทั่วแพลตฟอร์มผ่าน `system_all` หรือ `system_users` ได้ฝั่ง server | เป็นความหยาบที่จงใจและ document ไว้ (ตาม comment ของ code เอง) ไม่ใช่ bug ที่ต้องยื่น — การ scope ราย cluster แบบจริงจังต้องการโครงสร้างพื้นฐานในการ resolve `bu_code → cluster_id` ที่ยังไม่มีอยู่ |

## 5. คำแนะนำ

- **QA เมทริกซ์ target × timing แบบ end to end** — หกช่อง (`system_all`/`system_users`/`bu` × ทันที/กำหนดเวลา) สำหรับแต่ละช่อง: ถ้อยคำของ dialog ยืนยัน, shape ของ response 201 ใน Debug Sheet, การมองเห็นของผู้รับใน notification list และการมาถึงผ่าน live socket สำหรับผู้รับที่ออนไลน์ คาดหวังว่าสองช่องของ broadcast แบบกำหนดเวลาจะส่งมอบแบบ passive (ไม่มี socket) และช่องของ targeted แบบกำหนดเวลาจะประพฤติผิดตามกรณีพิเศษข้อ 2
- **ตรวจสอบขอบเขตความปลอดภัยใหม่ ไม่ใช่ข้อค้นพบเดิม** ส่ง POST ด้วย bearer ที่ valid จาก session ที่ไม่มี `broadcast.send` แล้วยืนยันว่าตอนนี้ล้มเหลวด้วย 403 พร้อมข้อความ error ที่ถูกต้อง (กรณีพิเศษข้อ 10) — ข้อค้นพบเดิมที่ว่า "มันสำเร็จ" ล้าสมัยแล้ว แยกต่างหาก ยืนยันว่า grant ของ `broadcast.send` ที่ scope ราย cluster ยังเข้าถึง `system_all` ได้ฝั่ง server (กรณีพิเศษข้อ 11) — เป็นสิ่งที่คาดหวัง ไม่ใช่ defect
- **ทดสอบกรณีพิเศษข้อ 1 อย่างชัดแจ้ง** (เลือกผู้รับ → สลับไป All users → dialog ยืนยันเทียบกับ payload จริง); Debug Sheet แสดง response และ request payload มองเห็นได้ใน network tab
- **QA ของ read state ต้องใช้ผู้ใช้สองคน:** ส่ง broadcast, ยืนยันว่าทั้งคู่เห็นมันเป็น unread (ยังไม่มี row ของ `tb_user_broadcast_action`), ให้คนหนึ่ง mark ว่าอ่านแล้ว และยืนยันว่า state แบบ unread ของอีกคนไม่ถูกแตะต้อง
- **ปฏิบัติกับ `broadcast.read`, `end_at`, `dismissed_at` และคอลัมน์ `doc_version` ที่มีเฉพาะใน schema ว่าเป็นของที่หลับใหล (dormant)** — ถูก seed/ประกาศไว้แต่ไม่ถูกใช้; อย่ายื่นการขาดหายของพวกมันจาก UI เป็น defect

**แหล่งข้อมูลอ้างอิง:** `../carmen-platform/src/App.tsx` (route guard) · `src/components/Layout.tsx` (sidebar) · `src/pages/BroadcastCompose.tsx` (`canSendSystem`/`canSend`, `<Can>`, ตัวสร้าง payload, comment ในโค้ดที่บันทึก backend PR #239) · `src/utils/errorParser.ts` (การ parse ข้อความ error แบบซ้อนที่ถูกแก้แล้ว) · `src/utils/permissions.ts` (mock list เฉพาะ dev — ที่ปรากฏแห่งเดียวใน SPA ของ `broadcast.read`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` (`KeycloakGuard` + `PlatformPermissionGuard`; `x-app-id` ยังเป็นเพียง Swagger) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts`, `src/auth/services/platform-permission.service.ts` (การตรวจสอบแบบหยาบ platform-หรือ-cluster-ใดก็ได้) · `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.controller.ts` / `notification.service.ts` (การส่งมอบ, scope query, `getScheduledNotifications` ที่ไม่ถูกเรียก) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.ts` (key ทั้งสอง)
**Cross-link:** [หน้า landing ของ Broadcasts](/th/platform/broadcasts) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md) &nbsp;·&nbsp; [Business Units](/th/platform/business-units)
