---
title: Both-book EN re-sync 2026-10-27
author: Thammanoon
date: 2026-11-09
id: l-4219e59f
scope: repo
status: active
touches:
  - ".specs/resync-2026-10-27-progress.md"
  - CLAUDE.md
---

## Decided
Owner said "update it" then "ทำได้เลยไม่ต้องถาม" (do it, don't ask) on 2026-10-27. Claude reused the 2026-09-22 defaults (resync-2026-09-22): EN only, diff-based, no screenshots, one PR per book, push to dev before merge, **merge is the owner's step**.

**MERGED 2026-10-27 21:21 +07:** owner said "merge ทั้งสอง PR เลย"; #23 then #24 merged (merge commits, main at f78fec4). Progress-log add/add conflict resolved in bcb7645 (Backstage section, then Inventory). Worktree and local branches removed; remote branches left.

**State before merge:** PR #23 `docs/resync-platform-2026-10-27` (Backstage book, 8 commits) and PR #24 `docs/resync-inventory-2026-10-27` (Inventory, 15 commits, worktree `../carmen-wiki-inventory-2026-10-27`) are open. All pages are pushed to dev Wiki.js and the nav has been rebuilt. Checklists: Inventory 381 rows / 86%, Backstage 267 / 100%. TH not touched, so TH now lags EN on both books again.

**Watch out:** both PRs add `.specs/resync-2026-10-27-progress.md` with different sections, so whichever merges second gets an add/add conflict. Resolve it by keeping both sections. Wiki.js `description` is varchar(255) and longer frontmatter descriptions fail push_pages silently in the summary count. The repo hook blocks `git checkout --` and `--amend`, so use `git show HEAD:f > f` and new commits instead.

**Why:** next session may be asked to merge, do the TH round, or file the code-finding tickets listed in the progress log.

## Watch out
check `gh pr view 23` / `gh pr view 24` first; remove the worktree after #24 merges.

**TH round (2026-10-27, owner said "continue" then "merge PR #25 เลย"):** 287 pages mirrored by 9 agents, PR #25 merged (main `6846516`), pushed to dev (16 created / 307 updated / 0 failed), nav rebuilt. Branch deleted locally and on GitHub. Watch out: when briefing TH agents, do NOT say "dateCreated identical to EN" — two agents rewrote 18 TH `dateCreated` values (reverted); CLAUDE.md says never change it. Ticket filing for code findings still not done (outward-facing, needs owner OK).
…

_From Claude Code's memory of this repo, last updated Oct 27._
