# Inventory book re-sync 2026-09-22 — progress log

Sibling of `.specs/resync-2026-09-22-progress.md` (Platform book, branch
`docs/resync-platform-2026-09-22`, PR #11). Same owner decisions apply: EN only
(TH deferred), diff-based + spot-check, no screenshots, merge is the owner's step.

Baseline: wiki `21fa189` (2026-07-29) → source HEADs on 2026-09-22: backend-v2
`ef4d6f08f` (1,905 commits in window, 14 breaking), frontend-react `0713cbc9`
(1,059 commits, 6 breaking), bruno `7f96637`, e2e `809d8e3`, micro-report
`c9ebf77`, micro-data `7f21905`, micro-cronjobs `5137b0a`. `carmen/docs` frozen
since 2026-04-27 — drift recorded in `.specs/carmen-docs-drift-2026-09-22.md`.

Method: 9 implementer agents, one per module group, each diffing its modules'
source since the baseline, correcting claims in place with `file:line`
citations, running a fabrication sweep, adding e2e catalog/gap cross-links to
`04-test-scenarios*` pages, and spot-checking one diff-untouched page.
Coordinator reviewed every report and committed per group.

| Group | Commit | Pages | Headline |
|---|---|---|---|
| General Ledger (new) | 8f3df14 | 2 new + book landing + nav | No inventory→GL posting exists (greps recorded); `gl_run_due` posts scheduled JVs; `tb_gl_period` ≠ `tb_inventory_period`; `routes/accounting` is a mock |
| Purchase Request + Templates | a8dd371 | 19/20 | `GET /api/my-pending` on view `sys_v_my_pending`; send-back → `in_progress`, never draft; no admin void; qty/FOC submit rules; budget/soft-commitment/PR type/delegation removed |
| Master Data + Product | a2a2cc0 | 30 (+3 new: shelf, chart-of-accounts, cost-center) | Extra-cost allocation live; GRN deviation limits on save; table renames; BU code platform-global; bulk import/barcode/soft-delete guards removed; likely live COA create contract gap flagged |
| Dashboard / Reporting & Audit / Recipe | 887545a | 28/38 | Personal widgets via micro-data + internal token; print-template mapping gone; notifications on `NotifyInput`; per-record Activity sheet; schedule `notify_at` |
| Purchase Order + Credit Note | a87c5d7 | 19/19 | Approval lands on `approved`; `sent_or_print` only via send-email / mark-sent; one row per location; CN `draft → completed`, no workflow/void/AP; e2e specs 402/403 lag the enum |
| Store Requisition + Vendor Pricelist | f303c27 | 26/32 | Three-qty invariant not enforced; `sr_type` derived; closed-period gate real; PATCH verbs; stock replenishment real API; vendor portal save/submit + token expiry; `submitted` status |
| System Config + Access Control | 3d46e95 | 22/22 | Inventory Period rename (only `closed` blocks posting); Email Profile/Template; app-config PR #10 finding still stands; workflow per type + skeleton lock; invitations replace `tb_temp_bu_user`; role controllers lack AppIdGuard/@Permission |
| GRN + Costing | 6fb37e2 | 24/25 | Commit posts; average BUs post at save (idempotent commit); void refuses once consumed; extra cost + FOC live; lot format `<loc><YYMM><seq4>`; per-product average, 2 dp; no GL wiring |
| Inventory / IA / Physical Count / Spot Check | 8783d3c | 44/48 | Period-end = start-counting + close, document-date period resolution, PR/PO no longer gate; IA draft→save→commit→void; wastage real API; physical-count submit never posts to ledger (confirmed code gap) |

Spot-checks (9 diff-untouched pages): 6 clean, 3 corrected (PO 01a comments missing `doc_version` ×2; master-data credit-note-reason default sort; reporting-audit attachment micro-file command list). No fabricated claim was found in the spot-check sample itself; every fabrication removed came from diff-touched pages.

Code findings worth tickets (documented on the pages, not fixed): FOC-only GRN commits and advances the PO FOC counter without a movement; PR `approve` skips the verify rules; COA create DTO requires `category` the FE never sends; role/permission controllers carry no AppIdGuard/@Permission; physical-count submit writes SI/SO rows but never posts; SR header commits `completed` before the on-hand check can throw; e2e 402/403 specs and FE copy still expect "Send to Vendor"/`SENT`; gateway swagger for widget `display` describes the old shape.

Not done (by decision): TH mirrors (all edited pages now lag EN); screenshots; GL master/budget/JV/reports content; `/system-admin/interface` and platform cron-jobs pages; e2e case mirroring. Bruno gaps noted on pages (missing `stock-movements`/`ref` requests, misfiled `currencies/fleet-summary`, stale `location-shelves` body, internal `run-due` auth shape) belong to that repo.

## TH round — 2026-09-23 (branch `docs/resync-th-2026-09-22`)

Owner asked for the TH mirrors the same morning the EN PRs merged. All 247 EN
pages changed by PRs #11 + #12 were mirrored into `th/` by 8 agents (one per
module group): 244 full mirrors, 3 Platform sub-page stubs corrected in place
(`business-units/{data-model,ui-screens}`, `clusters/ui-screens` — kept as
stubs per the standing deferral), 5 pages created in Thai (`general-ledger`,
`general-ledger/gl-posting`, `master-data/{shelf,chart-of-accounts,cost-center}`).
EN/TH file parity restored: 320 / 320. Every TH twin carries
`date: '2026-09-23T01:30:00.000Z'`, `dateCreated`/`tags` identical to EN,
`## N.` heading counts equal to EN except the three stubs.

Small EN defects found while translating and fixed in both locales in the
same commits: spot-check e2e catalog count (32 → 44); Landing At-a-Glance
still claiming Print Mapping was listed; inventory data-model intro still
saying movements land in the current period regardless of document date; a
stray `***Trigger:**`; vendor-pricelist test-scenarios "four screens" → five;
SR mermaid edge "recipe auto-create" → stock-replenishment auto-create.
Left as-is (identical in EN): two PO test-scenario rows with an unescaped `|`
inside a code span.
