---
title: Company Profile & Default Setting
description: Two system-admin screens that edit disjoint field groups of the same tb_business_unit row — Company Profile (identity, address, branding, date/time/number formats) and Default Setting (PR/SI/PO operational config + print-form template selection). /system-admin/business-setting is a dead redirect to Company Profile.
published: true
date: 2026-07-29T10:30:00.000Z
tags: system-config, business-unit, company-profile, default-setting, carmen-software
editor: markdown
dateCreated: 2026-07-29T10:30:00.000Z
---

# Company Profile & Default Setting

> **At a Glance**
> **Routes:** `/system-admin/company-profile`, `/system-admin/default-setting` &nbsp;·&nbsp; **Redirect:** `/system-admin/business-setting` → `/system-admin/company-profile` (client-side `<Navigate replace>`, no screen of its own) &nbsp;·&nbsp; **Table:** `tb_business_unit` (platform schema) — same row as [master-data/business-unit](/en/inventory/master-data/business-unit), disjoint field groups &nbsp;·&nbsp; **Endpoint:** `GET`/`PATCH /api/business-units` (no id in the URL — resolved server-side from the caller's token/BU context) &nbsp;·&nbsp; **Permission:** `system_configuration.view` (both screens; no dedicated key of their own).

## 1. What & Who

These are two separate screens that both read and partially edit the **current business unit's own `tb_business_unit` row** — the same table [master-data/business-unit](/en/inventory/master-data/business-unit) documents from the platform-admin console's angle. Where that page covers the platform admin's `carmen-platform` edit form (identity, currency, costing method, module enablement, tenant DB connection), these two screens are the **tenant-side, in-app** equivalents that a Sysadmin reaches from inside Carmen Inventory itself, and they edit a **different, non-overlapping subset** of the same row:

- **Company Profile** (`/system-admin/company-profile`) — identity (name, alias, description, info), read-only costing/licensing fields, default currency, hotel property address, company legal address, branding (logo/avatar, read-only), and date/time/number-format defaults.
- **Default Setting** (`/system-admin/default-setting`) — the `config` JSONB array on the same row: PR, SI, and PO operational toggles, plus a per-document-type print-form template selector.

Both screens share the exact same view/edit toggle pattern, the exact same `useBusinessUnit`/`useUpdateBusinessUnit` hooks, and the exact same `PATCH /api/business-units` endpoint — they differ only in *which* fields of `BusinessSettingFormValues` each screen renders and diffs. A single shared module (`company-profile-form-schema.ts`, `company-profile-config-registry.ts`, `company-profile-ui.tsx`) backs both screens' forms even though `default-setting-component.tsx` lives in its own route folder — confirmed by direct import (`../company-profile/company-profile-ui`, `../company-profile/company-profile-form-schema`).

**`/system-admin/business-setting` is a dead route** — `router.tsx` registers it as `{ path: "business-setting", element: <Navigate to="/system-admin/company-profile" replace /> }`, a bare client-side redirect with no component of its own. This is presumably a rename artifact: earlier planning documents in this repo (`docs/superpowers/plans/2026-07-09-business-setting-*-config-section.md`, `docs/superpowers/specs/2026-07-10-default-setting-page-split-design.md`) describe a single "Business Setting" page later split into these two screens, with the redirect left behind for old links/bookmarks.

**Maintained by** Sysadmin, in-app. **Read by** every module that consumes a `BusinessUnitDetail` field (costing engine reads `calculation_method`; PR/SI/PO screens read the `config` items Default Setting edits — see §6).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Edit business unit identity, address, or format defaults | Company Profile → **Edit** → change a field → **Save** | Sends only the changed fields as a `PATCH` (diff against the last-loaded snapshot) |
| Edit PR/SI/PO operational toggles | Default Setting → **Edit** → change a value → **Save** | Same diff-and-`PATCH` mechanism, scoped to the `config` array only |
| Pick a print form for a document type | Default Setting → Print Forms section → select a template per type | Dropdown is populated from [reporting-audit](/en/inventory/reporting-audit)'s report-template catalog, filtered to that document's `report_group`; see §6 |
| View (not edit) costing method or license cap | Company Profile → General section | `calculation_method` and `max_license_users` render as read-only `SettingField`s — no input, no matter what edit mode is active |
| Discard unsaved changes | **Cancel** while editing | Prompts a confirm dialog (`useDiscardConfirm`) only if the form is dirty |

## 3. Validation & Errors

| Symptom / Message | Cause | Confirmed? |
|---|---|---|
| Save fails with a version-conflict style error | `PATCH` payload always includes `doc_version` from the last load (`{ ...patch, doc_version: data.doc_version }`) | **Confirmed** — both screens attach `doc_version` to every save; a concurrent edit from elsewhere makes the second save's `doc_version` stale |
| Company email / hotel email rejected | `optionalEmail` Zod refinement — must be a valid email or exactly `""` | **Confirmed**, `company-profile-form-schema.ts` |
| `code` cannot be changed from either screen | `code` is a required field in `BusinessSettingFormValues` and in the Zod schema, but **no input anywhere in `company-profile-component.tsx` binds to it** | **Confirmed** — the field round-trips through `toFormValues`/`buildPatch` machinery but is never rendered; the form always keeps the loaded value, so validation trivially passes and `code` can never actually be edited from this screen |
| Print-form dropdown shows "⚠ Unknown template (…)" or a loading/unavailable placeholder | The stored `notification`-style config value references a report template id that isn't in the currently-loaded [reporting-audit](/en/inventory/reporting-audit) template list for that `report_group` (deleted template, load failure, or still loading) | **Confirmed** — `buildPrintFormOptions()` always synthesizes a placeholder option so the stored value is never silently dropped from the list on save |

## 4. Edge Cases

- **`config` is schema-less and frontend-seeded.** `tb_business_unit.config` is a bare `Json?` column — there is no fixed schema for its contents. The Default Setting screen only shows the **4 sections it knows about** (`CONFIG_SECTIONS` in `company-profile-config-registry.ts`: PR, SI, PO, Print Forms — 15 items total, 12 of them the per-document-type print-form selectors). Any `config` entry the backend has that isn't in this registry is silently **not rendered** by either screen (there is no "other settings" catch-all UI, even though the registry code has an internal `other` bucket type for this case that the component never renders).
- **Print-form config is frontend-seeded, not backend-required.** If a tenant's `config` array has no entry for a given print-form key (e.g. `print_form.pr`), the screen still shows the row (via `mergeSeededConfig`, defaulting to `""` = "Use the system default") — opening and saving the page for the first time is what actually writes the seeded defaults into the backend row.
- **`si.cost-from` has a calculation-method-conditional option.** The `average` option in the Stock-In "Default price for added items" dropdown is only shown when `data.calculation_method === "average"` (`visibleWhenCalcMethod`) — **unless** the BU's stored value is already `average` on a `fifo`-method tenant, in which case it stays visible so the stored value isn't silently dropped (`resolveConfigOptions()`).
- **Branding is read-only on both screens.** Logo/avatar render via a plain `<img>` with no upload control — the actual upload flow lives elsewhere (the user's own profile screen, per the component's own code comment), not here.
- **Number-format fields are structured, not raw strings.** `amount_format`/`quantity_format`/`perpage_format`/`recipe_format` are each `{ locales, minimumIntegerDigits }` — the UI shows this as an `Intl`-style locale string plus a digit count, not a free-text pattern like the `date_format`/`time_format` fields (which are plain enumerated strings from `company-profile-options.ts`).
- **`master-data/business-unit.md`'s address-field portrayal is stale relative to this page's own source read.** That page's §5.1 (last touched by an earlier resync pass) still lists single `hotel_address`/`company_address`/`*_zip_code` columns; the actual `BusinessUnitDetail` type and this screen's form both confirm 10 structured columns per address (`*_address_line1/line2/sub_district/district/city/province/postal_code/country/latitude/longitude`) plus `*_postal_code` (not `*_zip_code`) — matching the same structured-address finding the Platform book's `carmen-platform` resync pass independently made for `BusinessUnitEdit.tsx`. Flagging for a future correction pass on `master-data/business-unit.md` itself; not fixed here (out of this page's scope).

---

## 5. Field Groups (Dev)

Source: `types/business-unit.ts` (`BusinessUnitDetail`), cross-checked against `tb_business_unit` (platform schema) — see [master-data/business-unit](/en/inventory/master-data/business-unit) §5.1 for the authoritative Prisma field table. This section only maps which screen owns which fields.

### 5.1 Company Profile sections

| Section | Fields | Editable here? |
|---|---|---|
| General | `name`, `alias_name`, `cluster_name`, `description`, `info`, `default_currency_id` | Yes (except `cluster_name`) |
| General (read-only) | `calculation_method`, `max_license_users` | No — display only |
| Hotel | `hotel_name`, `hotel_email`, `hotel_tel`, `hotel_address_line1/2`, `hotel_sub_district`, `hotel_district`, `hotel_city`, `hotel_province`, `hotel_postal_code`, `hotel_country` | Yes |
| Company | `company_name`, `branch_no`, `tax_no`, `company_email`, `company_tel`, `company_address_line1/2`, `company_sub_district`, `company_district`, `company_city`, `company_province`, `company_postal_code`, `company_country` | Yes |
| Branding | `logo`, `avatar` | No — read-only image preview |
| Date & Time | `timezone`, `date_format`, `date_time_format`, `time_format`, `short_time_format`, `long_time_format` | Yes — all `<select>` from fixed option lists in `company-profile-options.ts` |
| Number Formats | `amount_format`, `quantity_format`, `perpage_format`, `recipe_format` | Yes — each a `{ locales, minimumIntegerDigits }` pair |

Not shown on this screen at all: `hotel_latitude/longitude`, `company_latitude/longitude`, `id`, `cluster_id`, `is_hq`, `is_active`, `db_connection`, `doc_version`, `audit` — these exist on `BusinessUnitDetail` but have no field on either in-app screen (some are edited only from the `carmen-platform` admin console — see [master-data/business-unit](/en/inventory/master-data/business-unit)).

### 5.2 Default Setting sections (`config[]` registry)

| Section id | Title | Item(s) | Datatype |
|---|---|---|---|
| `pr` | PR | `pr.allow-duplicate.product` — "Allow selecting duplicate products" | boolean |
| `si` | SI | `si.cost-from` — "Default price for added items" (`average`\*/`last_receiving`/`last_cost`) | enum |
| `po` | PO | `po.group-by-pr-comment` — "Group by PR comment" | boolean |
| `printForm` | Print Forms | 12 keys, one per document type: PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP | enum (report-template id, sourced from the [reporting-audit](/en/inventory/reporting-audit) template catalog filtered by `report_group`) |

\* `average` option only shown when `tb_business_unit.calculation_method = average` (or already selected).

Each print-form key is built as `printFormConfigKey(type)` (e.g. resolving to something like `print_form.pr`) — the exact string constant lives in `lib/print-form-config.ts`, not reproduced here to avoid re-deriving a value already centralized in one source file.

## 6. Business Rules

- **One row, two screens, no shared-lock conflict handling beyond `doc_version`.** Both screens PATCH the same `tb_business_unit` row independently; each attaches the `doc_version` it last loaded. Editing both screens in two tabs and saving both will make the second save's `doc_version` stale — standard optimistic-concurrency behavior, not screen-specific.
- **Default Setting's print-form selection feeds the print/report layer.** The per-document-type template id chosen here is what document printing defaults to when a user prints a PR/PO/GRN/etc. without picking a template explicitly — the exact consumption point is the report/print rendering path documented under [reporting-audit](/en/inventory/reporting-audit), not re-traced in this pass.
- **`si.cost-from` and `po.group-by-pr-comment` are read by their respective document modules at document-creation/pricing time** — this page documents only the config surface; consumption in [purchase-request](/en/inventory/purchase-request)/[purchase-order](/en/inventory/purchase-order)/[inventory-adjustment](/en/inventory/inventory-adjustment) (Stock In) was not re-traced in this pass and should be treated as **unconfirmed** pending a dedicated read of those modules' code.
- **No client-side restriction was found preventing `calculation_method` change from drifting out of sync with `si.cost-from = average`** if the BU's costing method later changes — see Edge Cases §4 for the one-directional guard that does exist (keeping an already-`average` selection visible, not preventing a mismatch from being introduced).

## 7. Cross-References

- [master-data/business-unit](/en/inventory/master-data/business-unit) — the authoritative `tb_business_unit` data model (platform schema) and the `carmen-platform` admin console's own edit surface for the fields these two screens don't expose.
- [system-config](/en/inventory/system-config) — parent module; these screens sit alongside [system-config/workflow](/en/inventory/system-config/workflow), [system-config/period](/en/inventory/system-config/period), etc. as Sysadmin-facing configuration.
- [reporting-audit](/en/inventory/reporting-audit) — source of the report-template catalog Default Setting's Print Forms section selects from.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [inventory-adjustment](/en/inventory/inventory-adjustment) — modules whose print/pricing behavior Default Setting's config items are intended to drive (consumption not independently re-traced this pass).

## 8. References

- **Frontend routes:** `../carmen-inventory-frontend-react/routes/system-admin/company-profile/company-profile.route.tsx` + `company-profile-component.tsx`; `routes/system-admin/default-setting/default-setting.route.tsx` + `default-setting-component.tsx`; redirect at `routes/router.tsx` (`business-setting` → `<Navigate>`).
- **Shared form/registry (imported by both screens):** `../carmen-inventory-frontend-react/routes/system-admin/company-profile/company-profile-form-schema.ts`, `company-profile-config-registry.ts`, `company-profile-ui.tsx`, `company-profile-options.ts`.
- **Frontend hooks:** `../carmen-inventory-frontend-react/hooks/use-business-unit.ts` — `useBusinessUnit()`, `useUpdateBusinessUnit()`.
- **Frontend types:** `../carmen-inventory-frontend-react/types/business-unit.ts` — `BusinessUnitDetail`, `BusinessUnitEditable`, `BusinessUnitConfigItem`.
- **API endpoint:** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` — `BUSINESS_UNIT: "/api/proxy/api/business-units"`.
- **Design history:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-07-10-default-setting-page-split-design.md`, `.../plans/2026-07-09-business-setting-{pr,si,po}-config-section-design.md` — the split from a single "Business Setting" page into these two screens.
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_business_unit` (line ~117); see [master-data/business-unit](/en/inventory/master-data/business-unit) §8 for the full citation.
