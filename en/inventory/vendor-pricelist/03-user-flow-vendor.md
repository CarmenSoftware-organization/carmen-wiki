---
title: Vendor Pricelist — User Flow — Vendor
description: Vendor's flow within the vendor-pricelist module — external party with portal-token access (no Carmen system login).
published: true
date: 2026-05-17T11:00:00.000Z
tags: vendor-pricelist, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Vendor

> **At a Glance**
> **Persona:** Vendor (external — token-authenticated portal session, no Carmen login) &nbsp;·&nbsp; **Module:** [[vendor-pricelist]] &nbsp;·&nbsp; **Workflow stages:** pricelist (none) → draft → submitted (then Purchaser approve / reject) &nbsp;·&nbsp; **Key permissions:** token-scoped portal access — enter / upload pricing, set currency / MOQ, save draft, submit
> **What this persona does:** Accesses the per-vendor portal via a cryptographic token, enters or uploads pricing per template, and submits for Purchaser review.

## 1. Role in This Module

The **Vendor** is an **external party with no Carmen system login**. Unlike most external personas (e.g., the vendor on the [[purchase-order]] module who interacts entirely through email / EDI), the vendor-pricelist module gives the vendor a **token-authenticated portal session** — the only place an external party drives system state directly within the Carmen ecosystem. The vendor receives an invitation email from a Purchaser-launched campaign, navigates to the per-vendor portal URL embedding the cryptographic `tb_request_for_pricing_detail.pricelist_url_token` ([[vendor-pricelist/01-data-model]] § 2.6), enters or uploads pricing for the products specified by the template, selects a submission currency, supplies MOQ tiers with units, saves drafts (auto-save every ~30 s), and finally clicks Submit — at which point `tb_pricelist.submitted_at` is written and the file routes to the Purchaser for review. The vendor's session is gated by `VPL_AUTH_007` (token-validity, IP allowlist if configured, session limits) and `VPL_AUTH_008` (currency must be in the tenant's permitted-currency list; unit conversion factors are read from master data, not vendor-supplied). The vendor never operates `tb_pricelist.status` directly beyond the implicit `(none) → draft` and `submit` action; approval, rejection, inactivation, and expiry are all driven by internal personas or the cron job. Because the vendor's primary surface is a single portal session with limited decision branches and no in-system RBAC matrix to enumerate, this file is intentionally shorter than the Purchaser file — comparable in size to the external Vendor file in [[purchase-order/03-user-flow-vendor]].

## 2. Entry Point and Primary Flow

**Entry point:** Vendor receives the invitation email (or a one-off reminder per the campaign's reminder schedule). The email carries the per-vendor portal URL embedding the `pricelist_url_token`, the campaign window dates, and the custom message. Clicking the link opens the portal; the token is exchanged for a session cookie subject to the tenant's portal-token policy ([[vendor-pricelist/02-business-rules]] § `VPL_AUTH_007`).

**Primary flow (happy path — online entry):**

1. **Open the portal via the invitation link.** The portal renders the welcome page with invitation details, deadline countdown (`VPL_CALC_007`), progress indicator, and the three submission options: **Direct online entry**, **Download Excel template and upload**, **Download Excel template and email to purchasing staff**. A `system` comment is recorded on `tb_request_for_pricing_detail_comment` capturing first-access timestamp; the derived invitation status moves from `pending` to `in-progress` (`VPL_POST_011`).
2. **Select the submission currency.** The currency picker offers the tenant-permitted currencies; the chosen value writes to `tb_pricelist.currency_id` on first save (`VPL_AUTH_008`). Currency selection applies to **all** lines on this submission; there is no per-line currency.
3. **Pick the submission mode.**
   - **Online entry:** the portal renders the template's product list as a single-page editable form. Each product row shows the inventory unit, the default order unit from the template, and a `[+]` button to add additional MOQ tiers (`VPL_VAL_006`).
   - **Excel upload:** click **Download template**, fill in offline, and drag-and-drop the workbook back onto the portal. The portal parses the workbook (`submission_method = portal`) into `tb_pricelist_detail` rows.
   - **Email submission:** click **Download template**, fill in offline, email to the purchasing staff. The Purchaser uploads on the vendor's behalf (`submission_method = email`, `VPL_AUTH_003`) — the vendor's portal session can be closed; no further vendor action is needed except to respond to any rejection email.
4. **Enter pricing per product per MOQ tier (online-entry path).** For each product, supply `price_without_tax`, `tax_rate` (when applicable to the vendor's tax profile), `lead_time_days`, and any per-row note. Use `[+]` to add MOQ-tier rows for bulk pricing (e.g., MOQ 1 @ ฿12.50, MOQ 50 @ ฿10.50, MOQ 100 @ ฿9.75). The portal auto-sorts tiers and warns inline (`VPL_VAL_020`) if a higher MOQ carries a higher unit price than a lower MOQ. Real-time validation feedback flags missing fields or out-of-range values.
5. **Save and resume across sessions (auto-save).** The portal auto-saves the in-progress pricelist every ~30 s and on field-blur. The vendor can close the browser and return later via the same invitation link as long as (a) the campaign `end_date` has not passed, (b) the token has not been revoked, and (c) the session limit (default 5 concurrent) has not been exceeded. `tb_pricelist.status` remains `draft` throughout; `submitted_at IS NULL`.
6. **Review the validation panel before submit.** The portal surfaces the validator's running output — completeness percentage, missing fields, business-rule pass rate, and the computed `quality_score` (`VPL_CALC_006`). Inline error messages with correction guidance appear next to each affected row.
7. **Click Submit.** The validator runs the full pass (`VPL_VAL_018`–`VPL_VAL_023`). On success, `tb_pricelist.submitted_at = now()`, `submission_method` is finalised, the quality score is written to `info`, and a `system` comment is appended in `tb_pricelist_comment`. The portal renders a confirmation page with the submission reference and the expected review timeline; an automated confirmation email is dispatched to the vendor's contact. The invitation status moves to `submitted` (`VPL_POST_012`).
8. **Wait for purchaser review.** No further action is required from the vendor unless the Purchaser rejects the submission (see Decision Branches).

## 3. Decision Branches

- **If the vendor needs to update pricing after submit but before approval.** The submitted pricelist's portal page exposes a **Recall and edit** action while `tb_pricelist.status = draft` and `submitted_at IS NOT NULL`. The vendor clicks Recall; `submitted_at` is reset to `NULL`, the pricelist reverts to the editable draft surface, and a `system` comment records the recall. The vendor edits and resubmits. The Purchaser is notified that the submission was withdrawn and re-submitted; the review timeline restarts.
- **If the vendor's submission is rejected by the Purchaser** (`VPL_POST_018`): the vendor receives a rejection email containing the reason text and the same portal URL (the original token remains valid until campaign `end_date`). The vendor opens the portal, sees the rejection `system` comment on the pricelist, makes the required corrections, and clicks Submit again. The cycle returns to Step 7 above.
- **If the vendor wants to use a different submission method mid-flight** (e.g., started online but wants to upload an Excel instead): the portal allows the switch at any time before submit — clicking **Switch to Excel upload** discards the in-progress online entries (with a confirmation prompt) and renders the upload surface. The reverse switch is also permitted. The chosen `submission_method` is finalised at the moment of Submit click.
- **If the portal token has been revoked or the session limit is exceeded.** The portal returns `401 — token revoked` (per `VPL_AUTH_015`) or `429 — session limit exceeded`. The vendor cannot recover the session through the original link; they must contact the purchasing staff (the contact email on the invitation) to either receive a new invitation with a fresh token (under `VPL_AUTH_002`) or be issued a one-off bypass. Auto-save drafts are preserved on the server side; if a new invitation is issued, the new pricelist starts empty (the draft from the revoked token is not migrated automatically — it is preserved for the Purchaser's audit only).
- **If the vendor cannot meet the deadline.** The vendor can email or call the purchasing contact to request a campaign extension (`VPL_POST_006` window adjustment) or a one-off later submission via the email path (`VPL_AUTH_003`). The portal itself does not expose a self-service extension; the request is handled by the Purchaser through the campaign edit screens. Beyond the `end_date`, the invitation auto-expires (`VPL_POST_014`), the token is revoked, and any draft pricelist is preserved on Carmen but no longer accessible to the vendor.

## 4. Exit Point / Handoffs

The vendor's involvement on a given invitation ends at one of three points; the document state at handoff is anchored to the lifecycles in [03-user-flow.md](./03-user-flow.md) § 2.

- **Submit → purchaser review.** The vendor clicks Submit; `tb_pricelist.submitted_at IS NOT NULL`; invitation status moves to `submitted`. Handoff is to the **Purchaser** for review and approval / rejection. Document state at handoff: pricelist `draft + submitted_at`; invitation `submitted`. The vendor's subsequent involvement, if any, is triggered by a rejection email (returning to the portal under the original token).
- **Submit via email path → purchasing staff.** The vendor returns the Excel by email; the Purchaser uploads on the vendor's behalf. Document state at handoff: pricelist `draft + submitted_at` written by staff; invitation `submitted`; `submission_method = email`. The vendor's portal session, if opened, is now superseded — the email-uploaded pricelist is the canonical submission.
- **Token expires or is revoked.** Campaign `end_date` passes without submission, or the Sysadmin / Manager revokes the token. Invitation status moves to `expired`; the vendor's portal access is terminated. Document state at handoff: pricelist `(none)` or `draft` (preserved for audit); invitation `expired`. The handoff is **out-of-band** — the vendor's relationship continues only through future campaigns issued by the Purchaser.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global lifecycle and cross-persona handoff table; the Vendor row sits between Purchaser invitation launch and Purchaser approval review.
- Authorization: [02-business-rules.md](./02-business-rules.md) § 4 — `VPL_AUTH_007` (portal access via token), `VPL_AUTH_008` (currency and unit selection), `VPL_AUTH_014` (segregation of duties — Vendor ≠ Purchaser), `VPL_AUTH_015` (token revocation).
- Posting rules: [02-business-rules.md](./02-business-rules.md) § 5 — `VPL_POST_010`–`VPL_POST_014` (invitation lifecycle); `VPL_POST_015`–`VPL_POST_016` (vendor-driven pricelist transitions).
- Validation rules: [02-business-rules.md](./02-business-rules.md) § 2 — `VPL_VAL_018`–`VPL_VAL_023` (line-level validations the vendor triggers on save and submit), `VPL_VAL_020` (MOQ-tier non-increasing pricing check, surfaced inline on the portal).
- Calculation rules: [02-business-rules.md](./02-business-rules.md) § 3 — `VPL_CALC_001`–`VPL_CALC_003` (line price decomposition shown to the vendor), `VPL_CALC_007` (deadline countdown on the portal).
- `../carmen/docs/vendor-pricelist-management/design.md` § Phase 5 (Vendor Portal Price Submission) — primary carmen/docs source for the portal UX described in Section 2 above.
- `../carmen/docs/vendor-pricelist-management/VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — portal feature catalogue covering auto-save, multi-format submission, real-time validation, and progress tracking.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — internal persona that launched the campaign, reviews the vendor's submission, and approves / rejects.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator who configures the portal-token policy (`VPL_AUTH_007`) and may revoke the vendor's token (`VPL_AUTH_015`).
- Cross-link: [[product]] — every line on the vendor's submission references a product on the template.
