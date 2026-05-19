# scripts/

Tooling for the carmen-wiki content repo.

## sync_nav.py

Mirrors the Wiki.js EN navigation tree into the TH locale.

Design: [`docs/superpowers/specs/2026-05-18-th-navigation-design.md`](../docs/superpowers/specs/2026-05-18-th-navigation-design.md).

### Prerequisites

- Python 3.11+
- A Wiki.js admin API token with navigation read + manage scopes
  (Wiki.js admin → API Access → New API Key)
- Wiki.js navigation mode set to **Static** (admin → Navigation → Mode)

### One-time setup

```bash
cd /path/to/carmen-wiki
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt

cp .env.example .env
# Edit .env and paste your WIKI_API_TOKEN
```

### Usage

Dry-run (recommended first):

```bash
source .venv/bin/activate
set -a; source .env; set +a
python3 scripts/sync_nav.py --dry-run --verbose
```

Read the per-item lines and the summary. Any `⚠ … [fallback]` line means
the TH label could not be resolved from frontmatter, home.md, or
overrides — fix the cause (write the TH page, add a heading to
`th/home.md`, or add an entry to `nav-overrides.yaml`) before pushing.

Live push:

```bash
python3 scripts/sync_nav.py
```

### Build mode (declarative)

To rebuild the entire nav tree (EN + TH) from `nav-overrides.yaml`:

```bash
python3 scripts/sync_nav.py --mode=build --dry-run    # preview
python3 scripts/sync_nav.py --mode=build              # apply
```

Build mode reads the `books:` block in `nav-overrides.yaml`. Each book
becomes a header followed by a link to its home page and one link per
module. A divider separates books. Both EN and TH locales are rebuilt
from the same config, with per-item TH labels resolved from
`label_th:`.

Use mirror mode (the default) when you maintain EN nav in Wiki.js admin
and only want TH to follow. Use build mode after a structural change
(adding a book, renaming a module).

### Label resolution

For each EN nav item, the TH label is resolved in this order:

1. **Frontmatter** (`link` + `targetType: page`):
   read `title:` from `th/<target>.md` or `th/<target>/index.md`.
2. **home.md** (`header`):
   pair `## N. …` headings between `en/home.md` and `th/home.md` by index.
3. **Override** (`nav-overrides.yaml`):
   manual map for headers and external URLs.
4. **Fallback:** EN label as-is (logged with ⚠ marker).

### Troubleshooting

| Symptom | Likely cause | Fix |
|--------|------|-----|
| Exit 4: `Wiki.js navigation mode is 'TREE', not STATIC.` | Wiki.js mode is auto-tree | Admin → Navigation → Mode: Static |
| Exit 2: `WIKI_API_URL and WIKI_API_TOKEN must be set` | `.env` not sourced or empty | `set -a; source .env; set +a` and verify token |
| `updateTree failed: code=Unauthorized` | Token lacks scopes or expired | Generate a new token with navigation: manage |
| Many `⚠ [fallback]` lines | TH translations missing / home.md headings drifted | Translate the TH pages or sync home.md; add entries to `nav-overrides.yaml` if needed |

### Files

| File | Purpose |
|------|---------|
| `sync_nav.py` | Main module + CLI entry |
| `test_sync_nav.py` | Pytest unit tests for pure functions |
| `conftest.py` | Shared pytest fixtures |
| `nav-overrides.yaml` | Manual label overrides (committed) |
| `requirements.txt` | Pinned Python dependencies |
