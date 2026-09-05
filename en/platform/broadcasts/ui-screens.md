---
title: Broadcasts — UI Screens
description: The three Broadcasts screens — BroadcastManagement (list, filters, CSV export), BroadcastCompose (target tabs, expiry presets, live preview), and BroadcastEdit (content lock, schedule/expiry editing) — plus the BroadcastPreview panel shared by Compose and Edit.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, broadcasts, ui
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts — UI Screens

> **At a Glance**
> **Screens:** `BroadcastManagement` (`/broadcasts`, list) · `BroadcastCompose` (`/broadcasts/new`, send) · `BroadcastEdit` (`/broadcasts/:id/edit`, view/edit) — **three separate components**, not one screen in different modes &nbsp;·&nbsp; **List:** status-summary strip, search, filters sheet, server-side table, CSV export &nbsp;·&nbsp; **Compose layout:** Audience tabs → Message fields → Type preset → Related-BU tag → Delivery (send time + expiry) beside a sticky **Preview** card &nbsp;·&nbsp; **Edit layout:** four cards (Info / Delivery / Content / Preview) — Content is read-only unless the broadcast is still `scheduled` &nbsp;·&nbsp; **Shared:** `BroadcastPreview` component, `useUnsavedChanges`, Ctrl/Cmd+S, Escape, a glassy sticky bottom action bar &nbsp;·&nbsp; **Persisted UI state:** 7 `localStorage` keys, List screen only

## 1. Overview

Broadcasts is a three-screen module now, not the single compose-only screen it used to be. `/broadcasts` → `BroadcastManagement` (§2) lists every `system_all`/`bu` broadcast; `/broadcasts/new` → `BroadcastCompose` (§3) sends a new one; `/broadcasts/:id/edit` → `BroadcastEdit` (§4) views one always and edits its schedule/expiry/content while still `scheduled`. **These are three distinct files and three distinct routes** — Compose and Edit in particular share no component, only a preview panel (`BroadcastPreview`, §3.7) and some validation/formatting utilities.

Standard furniture recurs across Compose and Edit: `useUnsavedChanges` arms a navigation guard as soon as a field deviates from its saved/default value, Ctrl/Cmd+S saves or sends, Escape resets or cancels, errors surface as red field messages plus a toast, and a dev-only Debug Sheet shows the last API response. Both use the same glassy "iOS-style" sticky bottom action bar (`.unsaved-bar`, added 2026-08-31) that shows an unsaved-changes dot indicator alongside Reset/Send or Cancel/Save.

## 2. The List screen (`BroadcastManagement`)

A `PageHeader` ("Broadcasts") with a subtitle plus an explicit note — *"Broadcasts sent to specific users don't appear here — they're recorded as individual notifications"* — sits above a clickable status-summary strip, a search-and-filter bar, and a server-side `DataTable`.

### 2.1 Header actions and summary strip

- **Export** (outline button, disabled while loading or empty) generates a CSV of the current page's rows via `generateCSV`/`downloadCSV`. Columns: Title, Message, Scope, BU Code, Severity, Status, Scheduled At, Expires At, Created At, Created By, Updated At, Updated By — **the last two are always blank**, because the API never returns `updated_at`/`updated_by` for a broadcast row even though the database now tracks both on every edit (see [Data Model](/en/platform/broadcasts/data-model) §5).
- **New Broadcast** (gated `<Can permission="broadcast.send">`) navigates to Compose.
- `BroadcastSummary` renders five clickable cells — All, Active, Scheduled, Expired, Deleted — sourced from the list response's own `summary` object (not a client-side count). Clicking All/Active/Scheduled/Expired toggles the matching `status` filter; **Deleted is different by design** — it toggles `include_deleted` instead of a status value, because the query param `status` only ever accepts `active|scheduled|expired` and deleted rows are reached via `include_deleted` alone. A load failure renders a retry state instead of the strip.

### 2.2 Search and filters

- A debounced (400 ms) `SearchInput` matches title or message, case-insensitively, resetting to page 1 on each new term.
- A **Filters** sheet (`BroadcastFilters`) offers: Status toggle-buttons (Active/Scheduled/Expired, multi-select), Scope toggle-buttons (System/Business Unit, multi-select), and a "Show deleted broadcasts" checkbox — plus a "Clear all" button once any filter is active. The header's Filters button carries a numeric badge counting active filter groups (status-any, scope-any, deleted).
- **Seven `localStorage` keys** persist List-screen state across visits: `search_broadcasts`, `filters_broadcast_status` (JSON array), `filters_broadcast_scope` (JSON array), `filter_broadcast_deleted` (JSON boolean), `page_broadcasts`, `perpage_broadcasts`, `sort_broadcasts` (default `created_at:desc`).

### 2.3 Columns

| Column | Notes |
|---|---|
| Title | Links to `/broadcasts/:id/edit`; the message is shown beneath it, truncated |
| Scope | "System" or "BU · `<code>`" |
| Severity | Badge, colour keyed off the sender's cosmetic `metadata.severity` (Critical→destructive, Warning→warning, Info→info, Maintenance→secondary); not sortable |
| Status | Badge — Active (success), Scheduled (info), Expired (secondary), Deleted (destructive) |
| Scheduled Date | `YYYY-MM-DD HH:mm`, `-` when unscheduled |
| Expires | Same format; renders in amber when the row is `active`/`scheduled` and less than 24 hours from expiring |
| Created | The shared audit-columns helper, showing only the **Created** side — **there is no Updated column at all**, because `BroadcastListItem` carries no `updated_at`/`updated_by` field for it to read (a deliberate omission, per the source's own comment, to avoid a column that would render permanently empty) |
| Deleted Date | Appears only when "Show deleted" is on |
| Actions | Row dropdown, all three items conditionally rendered |

Row actions: **Edit** (`<Can permission="broadcast.update">`, hidden once `status === 'deleted'`) links to the Edit screen; **Expire Now** (`<Can permission="broadcast.update">`, shown only when `status === 'active'`) opens a confirm dialog and, on confirm, `PATCH`es `end_at` to the current instant; **Delete** (`<Can permission="broadcast.delete">`, hidden once already deleted) opens a confirm dialog and, on confirm, soft-deletes via `DELETE`. Deleting or expiring re-fetches the current page in place (no navigation).

### 2.4 Empty state, loading, debug

An empty state (no rows, no error) shows a "New Broadcast" CTA gated the same way as the header button. A first load shows a full-table skeleton; a subsequent refetch overlays a dimmed "Loading…" strip rather than clearing the table. A `DevDebugSheet` (dev-only) shows the raw `GET /api/notifications/broadcasts` response.

## 3. The Compose screen (`BroadcastCompose`)

`PageHeader` with `backTo="/broadcasts"` (the page now has somewhere to go back to — unlike the pre-redesign single-screen module, which had no back link at all), title "Send Broadcast", subtitle "Push a notification to all users, specific users, or a business unit." A two-column grid holds the Compose card and, sticky on the right, `BroadcastPreview`.

### 3.1 Audience

A `Tabs` strip — **All users** (Globe, `system_all`, default), **Specific users** (Users, `system_users`), **Business Unit** (Building2, `bu`). The two system tabs render only when the session holds `broadcast.send` (`canSendSystem`); since the route itself already requires that same key, every user who can reach this page sees all three tabs — this in-component gate is unreachable defensive code, re-verified against current source. Switching tabs swaps the conditional section below but **does not clear previously entered state** — see the stale-recipients edge case in [Permissions](/en/platform/broadcasts/permissions) §4.

- **Specific users**: `UserMultiSelect` — 400 ms debounced search (also fires an empty-query search on open, so the first 20 users typically populate before any keystroke), top 20 matches by name or email, each rendered as name over muted email (display name is `firstname middlename lastname`, falling back to `name`, `email`, then the raw id). Clicking a result adds a removable badge (already-selected rows disabled, tagged "Selected"); Backspace with an empty query removes the last badge; Escape closes the dropdown. "Pick at least one recipient" validation, cleared as soon as one is added.
- **Business Unit**: a native select loaded once via `businessUnitService.getAll({ page: 1, perpage: 100 })` — **only the first 100 BUs** are offered — filtered to active BUs, rendered `Name (CODE)`, submitting the code; a load failure shows an inline Retry.

### 3.2 Message

Title (≤200 chars, live counter, hard-truncated at the limit) and Message (≤2000 chars, textarea, same truncation), both trimmed before validation/submission.

### 3.3 Type (sender-only label)

A native select — Info (default), Warning, Critical, Maintenance, **Other…**. **This choice is never sent to recipients** — it resolves to `metadata.severity`, a plain string the admin List/Edit screens read back for their own badges; the wire has no `type` field at all anymore (see [Data Model](/en/platform/broadcasts/data-model) §4). Choosing Other… reveals a custom-type input (uppercases as typed, `[A-Z0-9_]+`, ≤50 chars).

### 3.4 Related Business Unit (optional metadata tag)

A second, independent BU select — **not** the audience picker — that tags any broadcast (system or BU) with `metadata.bu_code` for reference purposes (e.g. downstream navigation), regardless of who actually receives it. This is new since the last documented version of this screen and easy to confuse with the audience's own BU select in §3.1; they are unrelated fields on unrelated form controls.

### 3.5 Delivery — send time

A `Tabs` strip — **Send immediately** (default) vs **Schedule for later**, revealing a `datetime-local` input when scheduled (must be a parseable, future instant).

### 3.6 Delivery — expiry (mandatory)

A **new, required** field: an Expiry preset select — 7 days, 30 days (default), 90 days, or **Custom…** (reveals its own `datetime-local` input). `resolveExpiryIso()` computes the actual `end_at`: the preset's day-count is added to the *scheduled* instant when a schedule is set, otherwise to now — so a broadcast scheduled for the 20th with a "7 days" expiry expires on the 27th, not the 18th (which would have expired it before it was ever sent). Custom expiry must be later than any chosen schedule time.

### 3.7 `BroadcastPreview` (shared with Edit)

A single component (`src/components/BroadcastPreview.tsx`) reused by both Compose and Edit, recomputed on every keystroke:

- **Notification card** — a left accent bar and badge coloured by the chosen severity, the title (italic placeholder until typed), the message (clamped to 6 lines).
- **Reaches** — "Every user in the system" (`system_all`, warning tint + alert icon), "N selected user(s)"/"No recipients picked yet" (`system_users`), or the picked BU's label (`bu`).
- **Delivery** — "Sends immediately" or "Scheduled for `<datetime>`", plus, when resolvable, an "Expires `<datetime>`" line.
- **A standing disclaimer**: *"Colour and label are an internal categorisation — recipients see a standard notification."* — this is the UI's own acknowledgment that severity is sender-only decoration (see [Data Model](/en/platform/broadcasts/data-model) §4).

### 3.8 Send flow

The **Send** button (`<Can permission="broadcast.send">`; label flips to **Schedule** in schedule mode) validates first, then opens a `ConfirmDialog`:

| Target mode | Dialog title | Confirm button |
|---|---|---|
| `system_all` | **Send to ALL users?** | destructive (red) |
| `system_users` | Send to N user(s)? | default |
| `bu` | Send to {BU name}? (falls back to the code) | default |

The dialog description leads with timing ("Will be delivered immediately" or "Scheduled for `<when>`"), then the audience: the title being sent (`system_all`), the first five recipient names plus "and N more" (`system_users`), or "Business unit: Name (CODE)" (`bu`).

On success: a toast ("Broadcast sent"/"Broadcast scheduled for `<when>`"), the entire form resets, and the response populates the Debug Sheet. On failure: the parsed error shows both as a toast and as a persistent in-page banner, and any field-level errors are mapped onto the form. There is no redirect — a `system_all`/`bu` send now shows up on the List screen; a `system_users` send does not (§1).

**Reset** (also triggered by Escape) clears the form, recipients, and field errors immediately, without a confirmation dialog — the confirm-before-discard protection exists only on *navigation*, via `useUnsavedChanges`. Unlike the Edit screen's bottom bar, which only renders while editing, Compose's sticky bottom bar is **always present** on this screen, since Compose has no separate "editing" mode to toggle.

## 4. The Edit screen (`BroadcastEdit`)

Reached from the List's title link or row menu. **Its route requires only `broadcast.read`** — any reader can open it, always in view mode first; the Edit button additionally requires `broadcast.update`.

### 4.1 Loading, not-found, header

A skeleton shows while fetching. A missing/soft-deleted-but-unreachable/malformed id renders a `SearchX` `EmptyState` ("Broadcast not found") with a "Back to broadcasts" button — soft-deleted rows are **not** treated this way (§4.4). The `PageHeader` shows `backTo="/broadcasts"`, the current title, a status Badge next to it, and `audit={normalizeAudit(rawResponse)}` for the Created/Updated line. **In practice this line only ever shows "Created"** — never "Updated" — because the wire shape has no `updated_at`/`updated_by` field for `normalizeAudit()` to read, even on a broadcast that has genuinely been edited (see [Data Model](/en/platform/broadcasts/data-model) §5). The Edit button (Pencil) appears only when not already editing and `status !== 'deleted'`, gated `<Can permission="broadcast.update">`.

### 4.2 Card layout

Four cards in a two-column grid, always visible:

1. **Broadcast Info** — read-only always: Scope ("System" or "BU · `<code>`") and Event, captioned "(System generated)". The Event value shown here is the raw `event` column — which is always `info` for every broadcast this module can create (§1 of [Data Model](/en/platform/broadcasts/data-model)) — so this field is descriptive in name only; it never varies.
2. **Delivery** — Scheduled At and Expires At. Both switch to a `datetime-local` input while editing; Expires At additionally offers +7d/+30d/+90d quick-apply buttons **but no "Custom…" preset selector** — unlike Compose's dropdown-of-presets, Edit's quick-apply buttons are shortcuts on top of the same date input, always visible. Expires At is required.
3. **Content** — Title, Message, and a Severity select. **Editable only when `editing` is true AND the broadcast's current status is `scheduled`** (`contentEditable`); otherwise every field renders through `ReadOnlyField`, and while editing a non-scheduled row the card header shows an explicit warning: *"Already broadcast — content can't be edited, some recipients may have already seen it."* Attempting to send `title`/`message`/`metadata` in the PATCH anyway is rejected server-side with 400 `content_locked`.
4. **Preview** — the same `BroadcastPreview` component as Compose (§3.7), fed from the live form state; `recipientCount` is always 0 here since Edit never changes the audience.

### 4.3 Save flow

Save (in the sticky bottom bar) is disabled unless something changed. On submit, `handleSubmit()` runs client validation (required title/message/expiry while content-editable; expiry after schedule), then two confirmation branches before the actual `PATCH`:

- **Past-expiry confirm** — if the new `end_at` is now in the past and the row wasn't already `expired`/`deleted`, a dialog warns *"The broadcast disappears from recipients immediately"* before submitting (this is how an aired broadcast is expired from the Edit screen itself, distinct from the List's dedicated Expire Now action).
- **Reschedule confirm** — if the row is currently `active` and the new schedule pushes it back into the future, a dialog warns *"The message disappears from recipients until the new time"*.

The PATCH body sends **only the fields that actually changed** (diffed against the last-saved snapshot, not the freshly-fetched row — because a `datetime-local` round-trip loses sub-minute precision and would otherwise always look "changed") plus the required `doc_version`. If nothing besides `doc_version` would be sent, the save is skipped entirely with a "No changes to save" toast rather than issuing an empty PATCH that would still bump `doc_version`. A 409 (stale `doc_version`) triggers the shared version-conflict toast and a silent refetch; other failures show a field-mapped error plus a toast.

### 4.4 Soft-deleted rows stay openable

Unlike most CRUD modules, `GET /api/notifications/broadcasts/:id` deliberately still returns a soft-deleted row (`status: "deleted"`) instead of 404 — so a deleted entry clicked from the List's history stays viewable. The Edit button is hidden for it (`status !== 'deleted'` gate), and content is naturally locked too (status isn't `scheduled`), so a deleted broadcast is effectively read-only everywhere on this screen.

### 4.5 Sticky bar, shortcuts, debug

The same glassy `.unsaved-bar` as Compose appears only while editing, showing Cancel/Save Changes. Ctrl/Cmd+S saves (only while editing and not already saving); Escape cancels the edit (only while editing) — a different binding from Compose, where Escape resets the whole form. The Debug Sheet here has **two tabs** — Response (last `GET`/`PATCH` payload) and Form State (live local state) — versus Compose's single tab.

## 5. References

- `../carmen-platform/src/pages/BroadcastManagement.tsx`, `src/pages/broadcastManagement/{BroadcastSummary,BroadcastFilters,broadcastColumns}.tsx` — the List screen.
- `../carmen-platform/src/pages/BroadcastCompose.tsx` — constants (`TITLE_MAX`, `MESSAGE_MAX`, `TYPE_CUSTOM_RE`), `resolveSeverity`, payload builders, `validate`, confirm title/description.
- `../carmen-platform/src/pages/BroadcastEdit.tsx` — `contentEditable`, the past/reschedule confirm dialogs, the changed-fields-only patch builder.
- `../carmen-platform/src/components/BroadcastPreview.tsx` — `severityStyle`, `reachSummary`, the internal-categorisation disclaimer.
- `../carmen-platform/src/utils/broadcastExpiry.ts` — `resolveExpiryIso()`, the 7/30/90-day presets.
- `../carmen-platform/src/components/UserMultiSelect.tsx` — debounce, page size, display-name fallback.
- `../carmen-platform/src/services/broadcastService.ts` — `sendSystem`/`sendBu`/`getAll`/`getById`/`update`/`remove`.
- `../carmen-platform/src/utils/audit.ts` — `normalizeAudit()` (the flat `created_by: { id, name }` shape broadcasts use, named directly in this file's own source comment as one of the endpoints without a nested `audit.*` shape).
- `../carmen-platform/src/utils/docVersion.ts` — `isVersionConflict`/`notifyVersionConflict`/`getDocVersion`.
- `../carmen-platform/src/components/KeyboardShortcuts.tsx`, `src/hooks/useUnsavedChanges.ts` — shortcuts and the navigation guard.
- `../carmen-platform/src/App.tsx` (three routes), `src/components/nav/platformNav.ts` ("Broadcasts" nav entry).

**Cross-links:** [Broadcasts landing](/en/platform/broadcasts) &nbsp;·&nbsp; [Data Model](/en/platform/broadcasts/data-model) &nbsp;·&nbsp; [Permissions](/en/platform/broadcasts/permissions)
