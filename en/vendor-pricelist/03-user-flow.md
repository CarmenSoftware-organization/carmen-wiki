---
title: Vendor Pricelist — User Flow
description: Document lifecycle and persona-specific flow files for vendor-pricelist.
published: true
date: 2026-05-17T11:00:00.000Z
tags: vendor-pricelist, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow

> **At a Glance**
> **Module:** [[vendor-pricelist]] &nbsp;·&nbsp; **Personas:** Purchaser (+ Purchasing Manager) &nbsp;·&nbsp; Vendor &nbsp;·&nbsp; Finance &nbsp;·&nbsp; Audit / Config
> **Workflow lifecycle:** Template (draft → active → inactive) &nbsp;·&nbsp; Campaign (draft → active → completed / cancelled) &nbsp;·&nbsp; Invitation (pending → in-progress → submitted → approved / expired) &nbsp;·&nbsp; Pricelist (draft → submitted → active / inactive / expired)
> **Drill into per-persona views below for action-level detail**

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `vendor-pricelist` module. A vendor pricelist is the vendor-submitted artefact (`tb_pricelist` header + `tb_pricelist_detail` rows) produced through the 6-phase collection process: **vendor setup**, **template creation** (`tb_pricelist_template`), **campaign / request-for-pricing planning** (`tb_request_for_pricing`), **vendor invitation** (`tb_request_for_pricing_detail` carrying the cryptographic `pricelist_url_token`), **secure portal submission** (online entry / Excel upload / email), and **validation + approval**. The lifecycle in Section 2 spans the three status enums — `enum_pricelist_template_status` for templates, application-derived statuses for campaigns and invitations, and `enum_pricelist_status` for the vendor's pricelist — from initial template draft through campaign launch, vendor draft and submission, purchaser review, and approval to `active`, with the auto-expiry, rejection, and inactivation branches. The personas involved are the **Purchaser** (and Purchasing Manager — collapsed onto the same persona file: builds templates, runs campaigns, sends invitations, reviews and approves submitted pricelists, manages preferred-vendor flags, manually uploads emailed submissions, and exercises high-value sign-off as Manager), the **Vendor** (external party with no Carmen login — accesses portal via token, submits pricing), the **Finance** team (Finance Officer + Finance Manager — audits price variance, validates currency/FX, signs off on multi-currency pricelists), and the **Audit / Config** roles (Auditor for read-only review across pricelists / campaigns / invitations / submissions / validation / activity-log, System Administrator for numbering, RBAC, portal-token policy, email integration, validation rules, and audit retention). Receiver / Store Keeper is an **indirect consumer** via GRN price-variance — they appear in cross-persona scenarios but do not have their own persona file. The role catalogue itself is defined in [index.md](./index.md) Section 4.

Section 2 below is the **global state machine** — the canonical list of transitions across the three lifecycles, independent of who acts. Each per-persona file (linked from Section 3) describes that persona's *path through* the state machine — their entry point, the actions available to them, the decision branches they face, and the handoff that ends their involvement. Section 4 then summarises the cross-persona handoffs that stitch the individual paths together. Read this overview first to anchor the lifecycle, then drill into the persona file that matches your role.

## 2. Document Lifecycle

The module has three status surfaces. Template status is stored on `tb_pricelist_template.status` (`draft`, `active`, `inactive`). Pricelist status is stored on `tb_pricelist.status` (`draft`, `active`, `inactive`, `expired`). Campaign and invitation status are **not Prisma columns** — they are derived by the application from `tb_request_for_pricing.start_date` / `end_date`, the linked pricelists' `submitted_at` and `status`, and `info` JSON flags (see [02-business-rules.md](./02-business-rules.md) § 5.2 and § 5.3 for the full derivation rules).

### 2.1 Template lifecycle

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Purchaser | Header fields validated (`name` unique per `VPL_VAL_001`, default `currency_id`, `validity_period` if set). |
| `draft` | save (edit) | `draft` | Purchaser (owner / procurement-team role) | Detail rows can be added / edited freely; `MOQ tier` structure validated per `VPL_VAL_006`. |
| `draft` | activate | `active` | Purchaser | At least one detail row exists (`VPL_VAL_002`); product references valid; reminder schedule valid. |
| `active` | inactivate | `inactive` | Purchaser, System Administrator | Cannot inactivate while a campaign referencing the template is in-flight. |
| `inactive` | re-activate | `active` | Purchaser | Referenced products and currency must still be active. |
| `draft` | soft-delete | `(none)` | Purchaser | Allowed only on `draft`; unique index includes `deleted_at` to permit name reuse. |

### 2.2 Campaign (request-for-pricing) lifecycle — application-derived

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `draft` | Purchaser | Header fields validated (`name` unique per `VPL_VAL_008`, `pricelist_template_id` references an `active` template per `VPL_VAL_009`). |
| `draft` | edit / add vendors | `draft` | Purchaser | Invitation rows (`tb_request_for_pricing_detail`) can be added per `VPL_VAL_011`–`VPL_VAL_012`. |
| `draft` | launch | `active` | Purchaser | `start_date < end_date` per `VPL_VAL_010`; at least one invitation row; email template valid (`VPL_VAL_013`). On launch, invitation emails dispatch and `pricelist_url_token` is materialised per row. |
| `active` | pause | `paused` | Purchaser, Purchasing Manager | Suppresses reminders and locks new invitations; existing portal tokens remain valid. Application flag in `info` JSON. |
| `paused` | resume | `active` | Purchaser, Purchasing Manager | Clear the `paused` flag; reminders resume. |
| `active` | (auto) complete | `completed` | — | Triggered when `now() >= end_date` OR every detail row has its linked `tb_pricelist.status = active`. |
| `active` | cancel | `cancelled` | Purchaser, Purchasing Manager, System Administrator | Application flag in `info` JSON with reason `system` comment in `tb_request_for_pricing_comment`. All portal tokens revoked; vendors notified. |

### 2.3 Invitation lifecycle — application-derived

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | invite | `pending` | Purchaser (campaign launch) | Invitation row inserted in `tb_request_for_pricing_detail`; `pricelist_url_token` materialised; email dispatched. |
| `pending` | first portal access | `in-progress` | Vendor (token-authenticated) | First-access `system` comment recorded in `tb_request_for_pricing_detail_comment`; auto-save begins on first save. |
| `in-progress` | submit pricelist | `submitted` | Vendor | Vendor clicks Submit at the portal; `tb_pricelist.submitted_at` is written; purchaser notified. |
| `submitted` | approve pricelist | `approved` | Purchaser (or Manager / Finance Manager for high-value / multi-currency) | Triggered by `tb_pricelist.status = active`. Invitation lifecycle terminates here. |
| `submitted` | reject pricelist | `in-progress` | Purchaser (or Manager) | Vendor receives email + the original token; can resubmit through the same portal until expiry. |
| `pending` / `in-progress` | (auto) expire | `expired` | — | Campaign `end_date < now()` and no submission has been made. Token revoked automatically. |

### 2.4 Pricelist lifecycle (`enum_pricelist_status`)

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | vendor first save | `draft` | Vendor (token-authenticated) | Pricelist header inserted via portal; FK on invitation row populated; auto-save engaged. |
| `draft` | save (edit) | `draft` | Vendor (token-authenticated) | Online editing / Excel upload / email reception; `MOQ tier` structure validated per `VPL_VAL_018`–`VPL_VAL_022`. |
| `draft` | submit | `draft` (with `submitted_at` written) | Vendor | Vendor clicks Submit; validator runs `VPL_VAL_023`; quality score computed; purchaser notified for review. |
| `draft` (submitted) | approve | `active` | Purchaser (`VPL_AUTH_004`) or Purchasing Manager / Finance Manager (`VPL_AUTH_005` / `VPL_AUTH_010`) for high-value / multi-currency | Quality score and validation results pass thresholds; preferred-vendor flag set per business rules. |
| `draft` (submitted) | reject | `draft` (with `submitted_at` reset) | Purchaser, Purchasing Manager (`VPL_AUTH_006`) | Reason text required; vendor emailed for resubmission. |
| `active` | inactivate | `inactive` | Purchaser, System Administrator | Downstream PR / PO / GRN treat the pricelist as historical-only from this point. |
| `inactive` | re-activate | `active` | Purchaser | Allowed only within validity window. |
| `active` | (auto) expire | `expired` | — | Cron: `now() > effective_to_date` AND `status = active`. |
| `draft` | soft-delete | `(none)` | Purchaser | Allowed only at `draft` (before approval); unique index includes `deleted_at` to permit reference-number reuse. |

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the persona role; clicking the link opens the per-persona view.

- [Purchaser](./03-user-flow-purchaser.md) — Purchaser / Purchasing Staff + Purchasing Manager (collapsed). Builds templates, runs campaigns, sends invitations, reviews and approves submitted pricelists, manages individual price-item edits and preferred-vendor flags, manually uploads emailed vendor submissions. The Manager exercises high-value approval, business-rules configuration, and multi-currency sign-off.
- [Vendor](./03-user-flow-vendor.md) — External party with no Carmen system login. Receives invitation, accesses portal via `pricelist_url_token`, provides pricing (online / Excel / email), selects currency, supplies MOQ tiers with units and conversion factors, saves drafts, and resubmits after rejection.
- [Finance](./03-user-flow-finance.md) — Finance Officer / AP audits price variance against posted GRN / invoice; Finance Manager reviews variance reports, validates currency / FX, signs off on multi-currency pricelists. No write surface on the pricelist itself; reads pricelist + posts variance findings to the AP module.
- [Audit / Config](./03-user-flow-audit-config.md) — Auditor reads pricelists / campaigns / invitations / submissions / validation results / activity-log across the chain; System Administrator configures pricelist numbering, RBAC, template / campaign settings, portal token policy (expiration, IP restrictions, session limits), email integration, validation rules, token revocation, and audit retention.

Note: **Receiver / Store Keeper** is listed as an "indirect consumer" in [index.md](./index.md) Section 4 — GRN posting reads the active pricelist for variance calculation, but the persona has no write surface on the pricelist module itself. Receiver behaviour is captured in cross-persona scenarios (Section 4 below and in [04-test-scenarios.md](./04-test-scenarios.md)) rather than a dedicated persona file.

## 4. Cross-Persona Handoffs

The table below captures the moments where pricelist responsibility moves from one persona to another. Each handoff is anchored to the document state at the point of transfer.

| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Purchaser | Activate template | Purchaser (same persona, different surface — now usable as a campaign source) | Template `active` |
| Purchaser | Launch campaign (dispatch invitation emails) | Vendor | Invitation `pending` (token materialised; vendor receives email) |
| Vendor | First portal access | Vendor (continues) | Invitation `in-progress`; pricelist `(none)` until first save |
| Vendor | First save at portal | Vendor (continues) | Pricelist `draft`; invitation `in-progress` |
| Vendor | Submit pricelist | Purchaser | Pricelist `draft` with `submitted_at IS NOT NULL`; invitation `submitted` |
| Purchaser | Approve pricelist (below high-value threshold) | (terminal — pricelist live) | Pricelist `active`; invitation `approved` |
| Purchaser | Approve high-value pricelist | Purchasing Manager (Manager role on same persona file) | Pricelist `draft` with `submitted_at`; invitation `submitted` (Manager queue) |
| Purchasing Manager | Approve high-value pricelist | (terminal — pricelist live) | Pricelist `active`; invitation `approved` |
| Purchasing Manager | Co-approval required for multi-currency | Finance Manager | Pricelist `draft` with `submitted_at`; invitation `submitted` (Finance Manager queue) |
| Finance Manager | Sign off on multi-currency pricelist | Purchaser / Manager (returns for activation) | Pricelist `draft` with `submitted_at`; activation proceeds on receipt of sign-off |
| Purchaser / Manager | Reject pricelist | Vendor | Pricelist `draft` with `submitted_at` reset; invitation `in-progress`; vendor receives rejection email |
| Purchaser | Manually upload emailed pricelist | (continues) | Pricelist `draft` with `submission_method = email`; flows into the standard approval path |
| (cron) | Pricelist auto-expire | (terminal — historical) | Pricelist `expired`; no downstream live reference |
| (cron) | Invitation auto-expire | Auditor (post-hoc review only) | Invitation `expired`; token revoked |
| Purchaser / Manager / System Administrator | Cancel campaign | All invited vendors (notified by email) | Campaign `cancelled`; all tokens revoked |
| Finance Officer | Variance finding at GRN | Purchaser (for resolution) | Pricelist `active` (unchanged); variance entry logged against vendor / pricelist for analytics |
| System Administrator | Revoke portal token | Vendor (loses portal access) | Invitation `expired` (effective immediately); subsequent portal access returns `401` |
| System Administrator | Save validation-rule / RBAC / token-policy configuration change | (forward in time) | Existing pricelists / campaigns retain snapshotted configuration; new pricelists / campaigns use the new configuration |
| Auditor | Audit finding flagged (read-only) | Responsible business owner (Purchaser, Manager, Finance, or Sysadmin) for out-of-band remediation | No pricelist state change — Auditor exits via report; remediation is performed by the transactional persona under their respective authority |

## 5. References

- `../carmen/docs/vendor-pricelist-management/design.md` — primary carmen/docs source for the 6-phase architecture and the workflow diagrams referenced in Section 2.
- `../carmen/docs/vendor-pricelist-management/requirements.md` — functional requirements driving each persona's surface area.
- `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md` — business-rules-engine documentation underlying the preferred-vendor and price-assignment cross-persona handoffs.
- `../carmen/docs/vendor-pricelist-management/VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — vendor portal features behind the Vendor persona's primary surface.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical entity / enum reference for the lifecycles in Section 2.
- Sibling: [02-business-rules.md](./02-business-rules.md) — validation, calculation, authorization, posting (status-transition), and cross-module rules referenced by each row of Section 2 and each handoff in Section 4.
- Related modules: [[purchase-request]] (PR defaults price from active pricelist), [[purchase-order]] (PO snapshots pricelist price + tracks deviation), [[good-receive-note]] (GRN price-variance check), [[product]] (pricelist entries reference products).
