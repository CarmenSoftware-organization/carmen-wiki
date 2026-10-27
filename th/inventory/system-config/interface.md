---
title: Interface (External API และ POS)
description: หน้าจอ /system-admin/interface: การเชื่อมต่อภายนอกต่อ BU — BU API key ขาเข้า, API docs, endpoint api/ext/v1 ap-invoices และ gl-journals และสรุปการตั้งค่า POS (Simphony / Micros 3700)
published: true
date: '2026-10-27T15:00:00.000Z'
tags: system-config, interface, external-api, api-key, pos, accounting-export, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Interface (External API และ POS)

> **At a Glance**
> **Route:** `/system-admin/interface` (รายการ) และ `/system-admin/interface/:category/:brand` (รายละเอียด); External อยู่ที่ `/system-admin/interface/export/external` (`/interface/accounting/external` เดิม redirect มาที่นี่, `router.tsx:833-841`) &nbsp;·&nbsp; **หมวด:** Accounting (Carmen GL, BlueLedgers), POS (Simphony, Micros 3700, Infrasys, Square), PMS (Opera, Protel), **Export tools** (External) &nbsp;·&nbsp; **การ gate:** licence เท่านั้นบนหน้า (`licenseFeature: "interface"`, ไม่มี key `permission` — `module-list.ts:856-866`); ตัว BU API key เองต้องมี `system_admin.bu_api_key.view|update` **และ** licence `interface.export.external` &nbsp;·&nbsp; **Endpoint หลัก:** `api/config/:bu_code/bu-api-key` (จัดการ) และ `GET api/ext/v1/ap-invoices`, `GET api/ext/v1/gl-journals` (ใช้งาน) &nbsp;·&nbsp; **การจัดเก็บ:** key อยู่ใน backstage schema (`tb_bu_api_key`, allowlist `tb_external_api`); brand อื่นเป็นแถว `tb_application_config` `interface_<category>_<brand>` &nbsp;·&nbsp; **เก็บ config เท่านั้น** — ไม่มีปุ่ม sync หรือ test-connection

## 1. คืออะไรและใครใช้

หน้า Interface แสดงหนึ่งแถวต่อการเชื่อมต่อระบบภายนอกที่ business unit ใช้ได้ การมองเห็นถูกตัดสินโดยสายโซ่ licence ของ BU (`interface` → `interface.<category>` → `interface.<category>.<brand>`; `interface-registry.ts`, `use-interface-entitlement.ts`): brand ที่ไม่อยู่ในสายโซ่จะถูกซ่อน, brand ที่อยู่เฉพาะใน `expired_features` อ่านได้แต่ล็อก และรายการไม่เคยอ่าน config ของ brand ที่ BU ไม่ได้ถือ (backend จะตอบ 403 และทำให้หน้าพัง — FE `c70d9ebc`, `08e827ce`)

| หมวด | Brand | หน้าจอทำอะไร | ความเกี่ยวข้องกับ inventory |
|---|---|---|---|
| Export tools | External | **API Access** (BU API key) + **API documentation** — ไม่มีฟอร์ม ไม่มี Save และไม่เขียนแถว `interface_export_external` อีกแล้ว | ระบบบัญชีภายนอกดึง GRN / CN / SR / SI / SO เป็นข้อมูล Dr/Cr |
| POS | Simphony, Micros 3700 | สวิตช์เชื่อมต่อ / เปิดใช้งาน; ดู §6 | เปิดใช้ Import POS และ Sales Consumption |
| Accounting, PMS | Carmen GL, BlueLedgers, Opera, Protel, Infrasys, Square | ฟอร์ม config ธรรมดาที่เก็บใน `tb_application_config` | เก็บ config เท่านั้น; ค่าเริ่มต้นของบัญชี GL ย้ายไปหน้า Accounting settings |

**ใช้โดย** นักพัฒนาที่เชื่อมระบบบัญชีภายนอกและ QA ที่ตรวจวงจรชีวิตของ key และสัญญา export **ดูแลโดย** sysadmin ที่ถือ `system_admin.bu_api_key.update`

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง key ของ BU | External → API Access → **Create key** | `POST api/config/:bu_code/bu-api-key`; หนึ่ง key ที่ใช้งานอยู่ต่อ BU (สร้างครั้งที่สอง = 409) secret ดิบแสดง **ครั้งเดียว** ใน dialog |
| ดู key | card เดียวกัน | แสดง base URL, Client ID, secret เป็น `••••••••` + 4 ตัวท้าย, ผู้สร้าง, ใช้ล่าสุด, สวิตช์ Active/Inactive `GET` ไม่เคยคืน secret; `exists: false` ก่อนสร้างครั้งแรก |
| เปิดดู secret | ปุ่ม **View** | `POST …/reveal`; นับเป็นสิทธิ์ **update** และเขียน activity `view` (`event_type: bu_api_key.reveal`) ลง activity log ของ BU ทุกครั้ง |
| หมุน secret | **Regenerate** (dialog ยืนยัน) | `POST …/regenerate`; client id เดิม, **secret เก่าตายทันที** ไม่มีช่วงผ่อนผัน |
| ปิดโดยไม่ลบ | สวิตช์ Active | `PATCH …/bu-api-key { is_active }`; key ที่ inactive ถูกปฏิเสธด้วย 401 ในทุกการเรียก ext |
| ส่งสัญญาให้ผู้เชื่อมระบบ | ส่วน **API documentation** | curl quick start ที่เติมไว้ล่วงหน้า (placeholder `$CARMEN_CLIENT_SECRET` ไม่ใช่ secret จริง), ดาวน์โหลด `openapi.json`, ลิงก์คัดลอกไปหน้า `/developers/api` สาธารณะ (Scalar, ไม่ต้องล็อกอิน, EN/TH) |

ไม่มี action ลบ key ใน UI หรือ API (ไม่มี route `DELETE`) ทุกอย่างที่หน้านี้ทำ **มีผลทันที** — บันทึกเมื่อคลิก จึงมีเส้นแบ่ง "takes effect immediately" (`external-interface-form.tsx`)

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | แหล่ง |
|---|---|---|
| 403 บนการเรียก `bu-api-key` ใด ๆ | ผู้เรียกไม่มี `system_admin.bu_api_key.view` (GET) / `.update` (POST create, regenerate, reveal; PATCH) หรือ BU ไม่มี / licence `interface.export.external` หมดอายุ | `config_bu-api-key.controller.ts`; `permission.route-map.ts:277,302,315` |
| 409 ตอนสร้าง | BU มี key ที่ใช้งานอยู่แล้ว (รวมถึง race ของ unique index: partial unique index บน `business_unit_id WHERE deleted_at IS NULL`) | `bu_api_key.service.ts` `create` |
| 404 ตอน regenerate / reveal / PATCH | BU ยังไม่มี key | `findLiveKey` |
| 400 `bu_code in query and path differ` | `BuCodePathQueryMatchGuard` | controller |
| 500 ตอนสร้าง / regenerate / reveal | micro-business ไม่มี `SECRET_ENCRYPTION_KEY` (32 ไบต์, เหมือนกันทุก instance) — secret ถูกเก็บแบบ hash (สำหรับ auth) **และ** เข้ารหัส (สำหรับ reveal) | BE `docs/external-api/accounting-export.md` |
| Reveal ล้มเหลวกับ key เก่าหลังเปลี่ยน env | การหมุน `SECRET_ENCRYPTION_KEY` ทำให้ reveal พัง; authentication ยังใช้งานได้ผ่าน hash | เหมือนกัน |
| ส่วน API Access / API documentation หายไปทั้งหมด | ผู้เรียกไม่มี `system_admin.bu_api_key.view` — ไม่ render ส่วนเหล่านี้ (ตัวหน้ายังเข้าถึงได้ด้วย licence) | `external-api-access-section.tsx` |
| หน้าแสดง "unavailable" ที่ card ของ key | อ่าน licence ไม่ได้ / หมดอายุ: หน้ายังดูได้ (`viewableWhenExpired`) แต่ซ่อนปุ่มเขียนและไม่ยิง `GET` ของ key | `external-api-access-section.tsx`, FE `87a67e55` |
| Base URL แสดง origin ของ frontend | ค่า Backstage `external_api.base_url` ว่างหรืออ่านไม่ได้; FE fallback เป็น `BACKEND_URL`/origin + `/api/ext/v1` gateway cache ค่านี้ 60 วินาที (10 วินาทีเมื่อล้มเหลว) | `external-api-base-url.service.ts`; `use-bu-api-key.ts` `externalApiBaseUrl` |

## 4. API อ่านภายนอก (`api/ext/v1/*`)

### 4.1 สายโซ่ authentication

`BuApiKeyGuard` (ไม่ใช่การล็อกอินผู้ใช้ — ไม่มี `Authorization` ไม่มี `x-app-id`; ผู้เรียกเป็น synthetic actor `external-api`) รันการตรวจต่อไปนี้ตามลำดับ (`bu-api-key.guard.ts`):

```
route has @ExternalApi(name)?            no  -> 403 "This API is not enabled"
x-client-id AND x-client-secret present? no  -> 401 "Invalid API credentials"
look up key by client_id; compare secret hash (dummy hash if id unknown -> no timing oracle)
mismatch | key inactive | BU deleted/inactive -> 401 "Invalid API credentials"   (one uniform body)
per-key rate limit: 300 requests / minute (fixed window)  -> 429
allowlist (tb_external_api, is_enabled, GET only)         -> 403 (503 until first load)
licence interface.export.external:  expired -> 403 | missing -> 403 | unresolvable -> 503
attach BU context; force query.bu_code = key's BU; throttle last_used_at (>= 60 s apart)
```

ข้อเท็จจริงที่ tester ต้องรู้: BU มาจาก key เสมอ (`bu_code` ใน query ถูกเมิน); `HEAD` เป็น 403 (GET เท่านั้น); การปฏิเสธ 403 และ 429 ยังนับเข้าโควตาต่อ key; มี throttle ต่อ IP ต้นทางระดับ global (`RATE_LIMIT_MAX`, ค่าเริ่มต้น 300/นาที) ด้วย ดังนั้นหลาย key ที่ poll จาก IP เดียวอาจเจอ 429 ก่อน; allowlist refresh ทุก 60 วินาที และการเพิกถอน licence ถึง API ภายในประมาณ 60 วินาที

### 4.2 Endpoint

| Endpoint | `api_name` (allowlist) | เอกสาร | ข้อมูล Dr/Cr |
|---|---|---|---|
| `GET /api/ext/v1/ap-invoices` | `apInvoice.list` | GRN (`committed`), CN (`completed`) | หนึ่ง record ต่อเอกสาร หนึ่งบรรทัดต่อ GRN item / CN detail; สองบัญชีตาม **role** (`debit_*` = inventory, `ap_*` = เจ้าหนี้) เพราะ CN สลับด้าน; ส่งเฉพาะจำนวนภาษี (บัญชี input-VAT อยู่ในระบบบัญชี); จำนวนเงินของ CN เป็นบวก |
| `GET /api/ext/v1/gl-journals` | `glJournal.list` | SR, SI, SO (`completed`) | หนึ่ง journal ที่สมดุลต่อเอกสาร; `side` Dr/Cr, `role` `inventory` / `adjustment` / `sr_in` / `sr_out`; `balanced` ถูกรายงาน ไม่เคยถูกบังคับ |

เอกสารอยู่ใน endpoint เดียวพอดี การขอ type ของ endpoint อื่นใน `doc_types` เป็น 400 endpoint `inventory-postings` เดิม (`inventoryPosting.list`) ถูกลบและถอดจาก allowlist โดย migration `20261017120000_external_api_ap_gl_export`

**พารามิเตอร์ query (ทั้งสอง endpoint, `accounting-export-query.ts`):**

| Param | จำเป็น | ค่าเริ่มต้น | กฎ |
|---|---|---|---|
| `date_from`, `date_to` | ใช่ | — | `YYYY-MM-DD`, รวมปลายทั้งสอง, เขตเวลาของ BU; `date_from <= date_to`; ช่วงไม่เกิน 366 วัน |
| `date_field` | ไม่ | `document` | `document` = วันที่เอกสาร; `updated` = แก้ไขล่าสุด (ใช้สำหรับ incremental sync) |
| `doc_types` | ไม่ | ทั้งหมดของ endpoint | รายการคั่นจุลภาค ไม่สนตัวพิมพ์ (AP: `GRN,CN`; GL: `SR,SI,SO`) |
| `page`, `perpage` | ไม่ | 1, 50 | `perpage` 1 ถึง 200 (เกิน = 400) |

Response: `{ data: [...], paginate: { total, page, perpage, pages } }` ฟิลด์เงินเป็นตัวเลข JSON ปัดแบบ half-up เป็น 2 ตำแหน่ง; `qty`, `price`, `tax_rate`, `exchange_rate` คงความละเอียดตามที่เก็บ บรรทัดที่มี `unmapped: true` มีจำนวนเงินถูกต้องแต่การ map บัญชี GL / AP ต้องแก้ใน Carmen Blue (`issues` / `issue` ระบุ reason code เช่น `missing_inventory_account`, `cost_not_found`)

### 4.3 สิ่งที่ถูก export (กฎการเลือก)

| กฎ | พฤติกรรม | แหล่ง |
|---|---|---|
| สถานะ | เฉพาะเอกสารที่เป็นฉบับสุดท้าย: GRN `committed`; CN, SR, SI, SO `completed` draft ไม่ถูก export | `export-core.service.ts` `HEADER[*].final` |
| Voided | export พร้อม `status: "voided"` **เฉพาะเมื่อเอกสารเคย post สต๊อก** (มี inventory transaction) ในทางปฏิบัติคือ SI / SO ที่ void หลัง completed; จำนวนเงินเป็นของเดิม ผู้ใช้ข้อมูลเป็นผู้กลับรายการ | `HEADER[*].posted`, `accounting-export.types.ts` `exportStatus` |
| Consignment | บรรทัด GRN / CN ที่ location แบบ consignment ถูกตัดออก (และไม่รวมในยอดรวม); เอกสารที่ไม่เหลือบรรทัดจะไม่ถูกคืนและไม่นับใน `total` SI / SO ที่ location ใน header เป็น consignment และ SR ที่ทั้งสองด้านเป็น consignment ถูกตัดออก; SR ที่ไม่มี transfer cost layer (ไม่มีการเคลื่อนไหวสต๊อก) ถูกตัดออก | `HEADER[*].owned` |
| การเรียงลำดับ | วันที่เอกสาร, เลขที่เอกสาร, doc type, id — ข้ามทุก type ที่ขอ และแบ่งหน้าด้วยกัน | docs |
| Idempotence | ไม่มีอะไรถูกทำเครื่องหมายว่า "exported"; ผู้ใช้ข้อมูล upsert ด้วย `(doc_type, id)` และแทนที่ทุกบรรทัด (การ map เปลี่ยนได้) | BE docs |

## 5. กรณีพิเศษ

- **ห้ามใส่ secret ใน test fixture, log หรือ query cache** FE เก็บ secret ที่เปิดดูไว้ใน state ของ component เท่านั้นและทิ้งเมื่อ dialog ปิด (`useSecretMutation`, `gcTime: 0`); backend ไม่เคย log มัน และ guard ลบ `x-client-secret` ออกจาก `request.headers` หลังตรวจสอบ
- **Reveal ถูก audit, regenerate และ toggle ถูก audit, `get` ไม่ถูก audit** ตรวจ activity log ([activity-log](/th/inventory/system-config/activity-log)) ด้วย entity `bu_api_key` หลัง reveal
- **Regenerate และ PATCH ใช้ optimistic locking** (`where: { id, doc_version }`): สองแอดมินที่ regenerate พร้อมกันได้ผู้ชนะหนึ่งและ 409 หนึ่ง แทนที่จะสูญเสีย secret (ดู [doc-version](/th/inventory/system-config/doc-version))
- **client id ที่ไม่รู้จักและ secret ที่ผิดแยกไม่ออก** (body 401 เดียวกัน งานเท่ากัน) test ที่ assert ว่า body ต่างกันคือบั๊กของ test
- **Incremental sync คือรูปแบบที่รองรับ** การแก้ไขและ void หลังอ่านครั้งแรกมองเห็นได้ผ่าน `date_field=updated` เท่านั้น; รันครั้งแรกใช้ `document` ครั้งต่อ ๆ ไป poll `updated` จากหนึ่งวันก่อน sync สำเร็จครั้งล่าสุด และ upsert ด้วย `(doc_type, id)`
- **การปัดเศษของ SR และที่คล้าย SR:** จำนวนเงิน SR มาจากต้นทุนต่อ layer ดังนั้น `balanced: false` คลาดไม่กี่สตางค์เป็นเรื่องปกติ และ SR ที่ฝั่งหนึ่งเป็น consignment อาจไม่สมดุลเพราะฝั่งนั้นถูกตัดออก
- **5xx ไม่เคยรั่วข้อมูลภายใน** gateway แทนข้อความ 5xx ของ micro-business ด้วย `Internal server error` สำหรับการเรียก ext (`gl-journal.service.ts`, `ap-invoice.service.ts`)
- **Swagger สำหรับผู้เชื่อมระบบ** เป็นเอกสารแยกที่ `{base_url}/api/ext/docs` และ `/api/ext/docs-json` เปิดใน development หรือเมื่อ `SWAGGER_ENABLED=true`; หน้าในแอปลิงก์ไปหน้า docs สาธารณะแทนการฝัง Swagger UI (FE `af1bba88`) และไม่มี "Try it" เพื่อไม่ให้มีการวาง secret ลงในเบราว์เซอร์

## 6. สรุป interface ของ POS

brand ของ POS เก็บเป็นแถว `tb_application_config` `interface_pos_simphony` และ `interface_pos_micros3700` (ฟอร์ม POS รวมเดิมถูกแยก, FE `f0439af8`, `f447132b`) การมีอย่างน้อยหนึ่ง brand ที่ `enabled = true` คือสิ่งที่ทำให้เมนู Import POS และ Sales Consumption ปรากฏ (`licenseFeature: "interface.pos"`) Simphony พกการตั้งค่า SFTP pull (host, port, credential, โฟลเดอร์ปลายทาง, file pattern, เวลา schedule รายวัน); Micros 3700 เป็นแบบ upload อย่างเดียวและมีแค่สวิตช์ enable กฎระดับฟิลด์, สถานะการ import, พฤติกรรม duplicate/overwrite และ pull ตาม schedule บันทึกไว้ที่เดียวที่ [Import POS](/th/inventory/recipe/import-pos) (§6 ของหน้านั้น); Sales Consumption ที่ [sales-consumption](/th/inventory/recipe/sales-consumption)

## 7. ความเชื่อมโยงข้ามโมดูล

- [recipe/import-pos](/th/inventory/recipe/import-pos) — การตั้งค่า POS, flow การ import และสถานะ
- [general-ledger/ap-invoice-from-grn](/th/inventory/general-ledger/ap-invoice-from-grn) และ [general-ledger](/th/inventory/general-ledger) — การ export เกี่ยวข้องกับข้อมูล Dr/Cr ที่ฝั่ง ledger สร้างจาก GRN และเอกสารสต๊อกอย่างไร
- [system-config/application-config](/th/inventory/system-config/application-config) — key `interface_*` และการแยก licence (รายการ app-config ทั่วไปไม่คืนมันอีกแล้ว)
- [system-config/activity-log](/th/inventory/system-config/activity-log) — ที่ที่ event reveal / regenerate / toggle ของ key ไปลง
- [system-config/doc-version](/th/inventory/system-config/doc-version) — optimistic lock บน `tb_bu_api_key`
- [access-control/permission](/th/inventory/access-control/permission) — `system_admin.bu_api_key` (`view` สำหรับ GET, `update` สำหรับทุกอย่างอื่นรวมถึง reveal)

## 8. แหล่งอ้างอิง

- **Frontend:** `../carmen-frontend/routes/system-admin/interface/` — `external-interface-form.tsx`, `external-api-access-section.tsx`, `external-api-docs-section.tsx`, `use-bu-api-key.ts` (`EXTERNAL_API_PATH = "/api/ext/v1"`), `interface-read-mode.ts` (React context ที่ฟอร์ม brand อื่นใช้: ก่อน **Edit** ฟิลด์ว่างแสดง `—` แทนตัวอย่าง placeholder), `interface-registry.ts`, `hooks/use-interface-entitlement.ts`, `CLAUDE.md` (บันทึกของโมดูล) Permission key: `constant/permissions.ts` (`bu_api_key`)
- **Backend, การจัดการ key:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_bu-api-key/` และ `apps/micro-business/src/authen/bu_api_key/bu_api_key.service.ts`; schema `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`tb_bu_api_key`, `tb_external_api`); migration `20261016150000_bu_api_key`, `20261017120000_external_api_ap_gl_export`
- **Backend, ext API:** `apps/backend-gateway/src/external-api/` (`bu-api-key.guard.ts`, `external-api.constants.ts`, `gl-journal/`, `ap-invoice/`); builder ใน `apps/micro-business/src/inventory/accounting-export/`; สัญญา query `packages/rpc-contract/src/schemas/accounting-export-query.ts`; เอกสารสัญญาและ OpenAPI แบบ static `docs/external-api/{accounting-export.md,mapping-and-calculation.md,openapi.json}`
- **E2E:** `../carmen-frontend-e2e/docs/test-cases/1118-interface.md` — แคตตาล็อกเท่านั้น; เขียนก่อนการปรับ External ใหม่ และไม่มี case สำหรับ BU API key หรือ ext endpoint (ช่องว่าง)
