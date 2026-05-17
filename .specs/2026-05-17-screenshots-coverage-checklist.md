# Screenshots Coverage Checklist

**Created:** 2026-05-17
**Baseline commit:** `f260b0f` — embedded 34 screenshots across 68 pages (34 EN + 34 TH)
**Round 2 (this update):** 34 existing PNGs refreshed from Carmen frontend; 27 NEW PNGs captured and embedded across 54 more pages (27 EN + 27 TH). Total: **61 PNGs embedded into 122 pages.**

## How to use

1. When a screenshot is captured, drop it at `assets/screenshots/<module>/<slug>.png` using the **1:1 filename rule** (image basename = page basename).
2. Embed into the matching page in **both** `en/<module>/<slug>.md` **and** `th/<module>/<slug>.md` using the established pattern:
   ```markdown
   ![<Page title> screen](/assets/screenshots/<module>/<slug>.png)
   ```
   Placement: one blank line after the `> **At a Glance**` blockquote, one blank line before `## 1.`
3. Bump `date:` in frontmatter on both edited pages (leave `dateCreated` alone).
4. Tick the box below and commit.

See `[[screenshot-pattern]]` memory for the full convention. Capture flow: log into `http://localhost:3000` as `admin@blueledgers.com`, then navigate to the route mapped below.

---

## Modules without an `assets/screenshots/<module>/` folder

- [x] `access-control/` — folder created round 2 (2 PNGs)
- [ ] `costing/` — **out of scope** (no UI route; concept-only module)
- [x] `system-config/` — folder created round 2 (7 PNGs)

---

## Module index pages

- [x] `dashboard/index.md` ← `dashboard/index.png` ← `/dashboard` (redirects to `/dashboard/main`)
- [x] `inventory/index.md` ← `inventory/index.png` ← `/inventory-management`
- [x] `reporting-audit/index.md` ← `reporting-audit/index.png` ← `/report`
- [x] `master-data/index.md` ← `master-data/index.png` ← `/config`
- [x] `system-config/index.md` ← `system-config/index.png` ← `/system-admin`
- [ ] `templates/index.md` — **deferred** (no `/templates` landing in app; module index is wiki-only. Could reuse one of `templates/price-list.png` or `templates/purchase-request.png`.)
- [ ] `costing/index.md` — **out of scope** (no UI route)
- [ ] `access-control/index.md` — **deferred** (no `/access-control` landing in app; closest is `/system-admin`)

---

## Sub-page screenshots

### costing — out of scope
- [ ] `costing/calculation-methods.md` — **out of scope** (concept page, no UI)

### reporting-audit
- [x] `reporting-audit/activity.md` ← `/system-admin/activity-log`
- [x] `reporting-audit/schedule.md` ← `/report/schedules`
- [x] `reporting-audit/user-activity.md` ← `/system-admin/user-activity`
- [ ] `reporting-audit/attachment.md` — **deferred** (no standalone route; attachments are nested inside transaction pages)
- [ ] `reporting-audit/notification.md` — **deferred** (no standalone route; notifications surface in the topbar bell)
- [ ] `reporting-audit/widget.md` — **deferred** (no standalone route; widgets are dashboard tiles)

### master-data — all 11 done
- [x] `master-data/adjustment-type.md` ← `/config/adjustment-type`
- [x] `master-data/business-unit.md` ← `/config/business-type`
- [x] `master-data/credit-note-reason.md` ← `/config/credit-note-reason`
- [x] `master-data/credit-term.md` ← `/config/credit-term`
- [x] `master-data/currency.md` ← `/config/currency`
- [x] `master-data/delivery-point.md` ← `/config/delivery-point`
- [x] `master-data/department.md` ← `/config/department`
- [x] `master-data/exchange-rate.md` ← `/config/exchange-rate`
- [x] `master-data/extra-cost-type.md` ← `/config/extra-cost`
- [x] `master-data/tax-profile.md` ← `/config/tax-profile`
- [x] `master-data/unit.md` ← `/config/unit`

### access-control
- [x] `access-control/application-role.md` ← `/system-admin/role`
- [x] `access-control/user.md` ← `/system-admin/user`
- [ ] `access-control/business-unit-user.md` — **deferred** (no standalone route; BU↔user mapping handled inside `/system-admin/user`)
- [ ] `access-control/permission.md` — **deferred** (permissions are configured inside `/system-admin/role/[id]`)
- [ ] `access-control/user-location.md` — **deferred** (location assignment handled inside user-edit page)

### system-config
- [x] `system-config/config-email.md` ← `/system-admin/config-email`
- [x] `system-config/document.md` ← `/system-admin/document`
- [x] `system-config/period.md` ← `/system-admin/period`
- [x] `system-config/query-dataset.md` ← `/system-admin/query-dataset`
- [x] `system-config/running-code.md` ← `/system-admin/running-code`
- [x] `system-config/workflow.md` ← `/system-admin/workflow`
- [ ] `system-config/application-config.md` — **deferred** (no standalone route surfaced in the app menu)
- [ ] `system-config/dimension.md` — **deferred** (no standalone route)
- [ ] `system-config/menu.md` — **deferred** (no standalone route)

---

## Round-2 outcome

| Bucket | Captured this round | Remaining (deferred) |
|---|---:|---:|
| Module index | 5 | 3 (`templates/index`, `costing/index`, `access-control/index`) |
| Sub-page | 22 | 10 (1 costing + 3 reporting-audit + 3 access-control + 3 system-config) |
| **Total** | **27** | **13** |

Embedded into 27 EN + 27 TH = 54 pages. Plus 34 refreshed PNGs (same paths, no .md edits needed) = **61 PNGs embedded into 122 pages total**.

## Out of scope (permanent)

- All 01–04 numbered sub-pages (`01-data-model.md`, `02-business-rules.md`, `03-user-flow*.md`, `04-test-scenarios*.md`) — textual reference, not UI tours.
- `costing/` module — design/concept docs, no Carmen UI counterpart.
- Wiki-only index pages (`templates/index`, `access-control/index`) — the app menu doesn't have a dedicated landing screen.

## Deferred pending UI surfacing

The 10 "deferred" pages above can be revisited if a standalone route appears, or if it's acceptable to capture a sub-section of a parent page and label it accordingly.
