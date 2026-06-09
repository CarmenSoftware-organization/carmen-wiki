# Docs Sync — Backend / Platform / micro-data split (post-2026-06-04)

**Date:** 2026-06-09
**Status:** Approved design — pending spec review
**Scope:** Sync carmen-wiki documentation to source-repo changes committed **after 2026-06-04**, across back-end (`carmen-turborepo-backend-v2`), the new `micro-data` microservice split out of `micro-report`, and `carmen-platform`. Front-end changes in this window are internal security hardening (sanitize/allow-list URLs) and are **out of scope**.

## Goal

Bring five independent areas of the wiki back in line with what the system now does. Every page is mirrored EN + TH. The work is sequenced **A → B → D → C → E**: A is the largest (an architecture change underpinning dashboard/reporting), B and D are small grounded edits, C requires a new concept page, E is independent in the platform book.

## Baseline & sources of truth

Changes since the wiki's last update (2026-06-04). Confirmed source commits:

- **micro-data** (new sibling repo `../micro-data/`): `7807cd8` initial repo, `9ae603a` dashboard datasets (68) + widget CRUD, `4a9cfcc` README with dashboard/widget API. README is the canonical description of the split.
- **back-end** (`../carmen-turborepo-backend-v2/`):
  - `44e2a47c` (06-08) `refactor(dashboard): proxy datasets + widgets to micro-data over HTTP`
  - `e150b6bc` (06-09) `feat: add my-approve.findAll to x-app-id permissions`
  - `f6a29ae2` (06-09) `feat: add permission keys for purchase request, purchase order, and store requisition comments and approval workflows`
  - `d925217b` (06-09) `refactor: update document download URL helper and attachment DTO`
  - `f3633855` / `f6694fbc` (06-04) `doc_version` optimistic-lock control rolled out across services
- **micro-report** (`../micro-report/`): `0bdd3ee` (06-08) `execute datasets via micro-data over HTTP`
- **platform** (`../carmen-platform/`): changelog feature (06-01) — public `/changelog` route, JSON-sourced changelog, `VersionBadge`.

Rule (from CLAUDE.md): implementation + E2E beat `../carmen/docs/`; `../carmen/docs/` beats memory. Read the source before writing each page; pull exact field/key lists from source at implementation time, not from this spec.

## Conventions (apply to every page)

- Wiki.js YAML frontmatter required. **Edited pages:** update `date` to `2026-06-09T00:00:00.000Z`, leave `dateCreated` untouched. **New pages:** set both `date` and `dateCreated` to `2026-06-09T00:00:00.000Z`.
- Numbered section hierarchy (`## 1.`, `### 1.1`), comparison tables for trade-offs, language-agnostic fenced pseudo-code, ฿ for currency.
- Cross-page links use absolute-URL markdown `[Display](/en/inventory/<mod>/<slug>)` — pipe wikilinks do not render here. No inline cross-locale links (Wiki.js handles the toggle).
- Every change is mirrored: EN page under `en/...` and TH page under the parallel `th/...` path. TH prose in Thai; code/field names stay English.
- No screenshots required for these edits unless an existing page already embeds one (preserve it).

---

## A — micro-data split (edit-only; no new page)

**The change.** Dataset execution was split out of `micro-report` into a new **`micro-data`** service. The boundary contract is the **`Dataset`** object (columns + rows + totals + summary).

- **micro-data owns** the data-source concern: resolve a Postgres view / function (`RETURNS TABLE`/`SETOF`) / procedure (refcursor), compose WHERE/positional args from filters, fan out across tenant BUs in parallel, return the materialised `Dataset`. It renders nothing. Each dashboard dataset runs in a read-only transaction with `SET LOCAL search_path` pinned to the tenant schema.
- **micro-report owns** rendering: output format (PDF/Excel/CSV/JSON), template layout (`content`), `kind`, `report_group`, print mappings, job tracking. It calls `POST /api/datasets/execute` instead of running the query in-process.
- **micro-data also hosts** the 68 shaped dashboard datasets (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`) and widget CRUD, ported from `micro-business`/`micro-cluster`. The **backend-gateway proxies** these over HTTP.
- The `tb_report_template` row historically conflated two concerns; micro-data reads only the dataset columns (`source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key`), mapped onto `model.DatasetSource`. The table is unchanged for now (a `tb_dataset_source` extraction is a noted follow-up).

micro-data API surface (from its README — confirm at implementation):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/datasets/types` | dataset catalogue (`?category=`) |
| `POST` | `/api/datasets/execute` | execute a dataset (`key` **or** `name`, `bu_codes`, `filters`) → `Dataset` |
| `GET` | `/api/dashboard/datasets` | dashboard catalogue (`{items,count}`) |
| `GET` | `/api/dashboard/datasets/:id?bu_code=&user_id=` | execute one → `{meta,data}` |
| `GET/POST` | `/api/dashboard/bu-widgets?bu_code=` | list / create BU widgets |
| `GET/PATCH/DELETE` | `/api/dashboard/bu-widgets/:id` | one BU widget |
| `GET/POST` | `/api/dashboard/personal-widgets?user_id=` | list / create personal widgets |
| `GET/PATCH/DELETE` | `/api/dashboard/personal-widgets/:id` | one personal widget |
| `POST` | `/api/dashboard/personal-widgets/reorder?user_id=` | bulk reorder |

**Pages to edit:**

1. `en|th/inventory/system-config/dashboard-dataset.md`
   - At-a-Glance **Backing** is now wrong (says `micro-business/dashboard-dataset/registry/`). Change to: code-registered in **micro-data**, served at `GET /api/dashboard/datasets`, **backend-gateway proxies over HTTP**.
   - Update the "differs from" table row accordingly (stored in micro-data service, not micro-business).
   - State 68 shaped datasets across the six shapes; note read-only txn + `SET LOCAL search_path` per execution.
2. `en|th/inventory/reporting-audit/report.md`
   - Add a short subsection on the micro-data ⇄ micro-report split: which `tb_report_template` columns each side reads; micro-report calls `/api/datasets/execute` rather than running the query in-process; `Dataset` is the boundary object.
   - Keep the existing four-table description; clarify that dataset *resolution* now lives in micro-data while *render + job* stays micro-report.
3. `en|th/inventory/reporting-audit/widget.md`
   - Widget CRUD (BU + personal widgets, reorder) is now hosted in micro-data and proxied by the gateway; list the relevant endpoints.
4. `en|th/inventory/system-config/query-dataset.md`
   - Add a note: views/procedures/functions authored here are the data sources micro-data executes via `/api/datasets/execute`.

---

## B — New permission keys (edit-only)

**The change.** `apps/backend-gateway/x-app-id.json` gained permission keys for **comment** and **approval-workflow** actions on Purchase Request, Purchase Order, and Store Requisition, plus `my-approve.findAll`.

**Page to edit:** `en|th/inventory/access-control/permission.md`
- Enumerate the exact new keys from `x-app-id.json` at implementation time (do not guess shapes).
- Add them to the examples / catalogue framing: comment permissions and approval-workflow permissions per document type, and the `my-approve.findAll` cross-document approval-inbox permission.
- Keep the page's conceptual framing (atomic `(resource, action)` pairs bundled into roles); this is an additive update to the catalogue, not a structural change.

---

## D — Attachment download URL / DTO (edit-only)

**The change.** `d925217b` standardised the **document download URL helper** (`apps/backend-gateway/src/common/helpers/document-download-url.ts`) and the **comment-attachment DTO** (`comment-attachment.dto.ts`) to expose consistent file-retrieval fields.

**Page to edit:** `en|th/inventory/reporting-audit/attachment.md`
- Read both source files; document the consistent file-retrieval fields the DTO now exposes and how the download URL is resolved.
- Update the "Download attachment" common-task row and any field list to match the new shape.
- **Caution:** this page already uses `doc_version` to mean a *PDF re-render counter*. Do **not** conflate it with the optimistic-lock `doc_version` in part C — and add a one-line clarifier cross-linking to the new concept page so the two meanings are not confused.

---

## C — `doc_version` optimistic concurrency (new concept page + reference links)

**The change.** `doc_version` optimistic-lock control was rolled out across update DTOs of ~15 entities: purchase-request, purchase-order, GRN, credit-note, pricelist, pricelist-template, purchase-request-template, request-for-pricing, spot-check, stock-in, stock-out, store-requisition, plus several recipe/config masters (credit-term, extra-cost-type, recipe-category/cuisine/equipment(-category), running-code, vendor-business-type). Confirm the full list from the 06-04 commits at implementation time.

**New page:** `en|th/inventory/system-config/doc-version.md` — *"Document Version (Optimistic Concurrency)"*
- **1. What & Who** — version integer on the aggregate root; the client must echo the current `doc_version` on update; a mismatch means someone else saved first.
- **2. Behaviour** — pseudo-code of the compare-and-set; mismatch → **409 Conflict** (lost-update prevention). Success increments the version.
- **3. Entities that carry it** — table of the ~15 entities.
- **4. Test scenarios** — two clients load v5; client A saves (→ v6); client B saves with v5 → 409; client B must refetch and retry.
- **5. Not to be confused with** — `tb_attachment.doc_version` (a PDF re-render counter, not a concurrency guard); cross-link to [reporting-audit/attachment](/en/inventory/reporting-audit/attachment).
- Decision: lives under `system-config` (cross-cutting platform behaviour, alongside the other config-level concepts). Filename `doc-version.md`.

**Reference links (no duplication):** add a one-line "Concurrency: this entity uses [Document Version](/en/inventory/system-config/doc-version) optimistic locking on update" to the data-model or business-rules page of the main transactional entities (PR, PO, GRN, SR, spot-check). Do not restate the mechanics on each page.

Also add the new page to the `system-config` landing/index page link list (EN + TH).

---

## E — Platform Changelog (new page)

**The change.** `carmen-platform` added a public Changelog feature (06-01): a public `/changelog` route, a JSON-sourced changelog, and a `VersionBadge` shown in the sidebar footer and on the landing page.

**New page:** `en|th/platform/changelog.md` — *"Changelog"* (platform book, top-level)
- Confirm details from `../carmen-platform/` (the changelog source JSON, the route guard allowing `/changelog` as a public path, the `VersionBadge` component placements).
- **1. What & Who** — public changelog page (no auth); version badge surfaces the running platform version to all users.
- **2. How it's sourced** — JSON-sourced entries; where the data lives; date/timezone handling noted in the commits.
- **3. Where it appears** — public `/changelog` route, sidebar footer badge, landing-page badge.
- **4. For developers** — how to add a changelog entry (from the JSON shape), and the public-path auth-guard exception.
- Add a link to the new page from the platform landing page `en|th/platform.md` (or the platform nav index).

---

## Out of scope

- Front-end commits in this window (security hardening: `sanitizeText`, allow-list URLs, `safeInternalHref`) — internal, not user-manual-facing. User confirmed skip.
- micro-cronjobs (no relevant changes since 2026-06-04).
- The broader 58 "Partial" coverage backlog and physical-count/spot-check Steps gaps tracked in `.specs/process-coverage-checklist.md` — separate effort; not part of this sync.
- The `tb_dataset_source` extraction migration (noted as a future follow-up in micro-data's README) — not yet implemented, so not documented as current behaviour.

## Definition of done

- Parts A–E complete, each EN page mirrored in TH.
- Edited pages have `date` bumped to 2026-06-09, `dateCreated` preserved; new pages have both set to 2026-06-09.
- New pages (`doc-version`, `changelog`) linked from their section/landing index in both locales.
- No page still asserts the pre-split architecture (no remaining claim that dashboard datasets live in `micro-business/.../registry/`, no claim that micro-report runs dataset queries in-process).
- `attachment.md` distinguishes its re-render `doc_version` from the optimistic-lock concept page.
- Exact permission keys, DTO fields, and the entity list were pulled from source at implementation time (not from this spec's summaries).
