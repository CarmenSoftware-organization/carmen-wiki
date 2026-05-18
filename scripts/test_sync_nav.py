"""Unit tests for sync_nav."""
from pathlib import Path

from scripts.sync_nav import parse_home_headings


def test_parse_home_headings_returns_index_keyed_dict(tmp_path: Path):
    """Headings are returned in index order as a list of strings."""
    home = tmp_path / "home.md"
    home.write_text(
        "---\ntitle: Home\n---\n\n"
        "# Title\n\n"
        "## 1. First\n\nbody\n\n"
        "## 2. Second\n\nbody\n\n"
        "## 3. Third\n",
        encoding="utf-8",
    )
    assert parse_home_headings(home) == ["First", "Second", "Third"]


def test_parse_home_headings_strips_leading_number(tmp_path: Path):
    """Numbering prefix `N. ` is stripped from each heading."""
    home = tmp_path / "home.md"
    home.write_text("## 1. Procure-to-Pay\n## 2. Inventory\n", encoding="utf-8")
    assert parse_home_headings(home) == ["Procure-to-Pay", "Inventory"]


def test_parse_home_headings_ignores_h1_and_h3(tmp_path: Path):
    """Only ## (h2) headings count."""
    home = tmp_path / "home.md"
    home.write_text(
        "# Top\n## 1. A\n### 1.1 A-sub\n## 2. B\n",
        encoding="utf-8",
    )
    assert parse_home_headings(home) == ["A", "B"]


from scripts.sync_nav import build_header_label_map


def test_build_header_label_map_pairs_by_index():
    en = ["About", "Dashboard", "Procure-to-Pay"]
    th = ["เกี่ยวกับ", "แดชบอร์ด", "Procure-to-Pay"]
    assert build_header_label_map(en, th) == {
        "About": "เกี่ยวกับ",
        "Dashboard": "แดชบอร์ด",
        "Procure-to-Pay": "Procure-to-Pay",
    }


def test_build_header_label_map_mismatch_returns_partial_and_warns(caplog):
    """If lists differ in length, pair up to min(len) and log a warning."""
    en = ["A", "B", "C"]
    th = ["ก", "ข"]
    with caplog.at_level("WARNING"):
        out = build_header_label_map(en, th)
    assert out == {"A": "ก", "B": "ข"}
    assert any("home.md heading count" in r.message for r in caplog.records)


from scripts.sync_nav import load_overrides


def test_load_overrides_parses_headers_and_links(tmp_path: Path):
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text(
        'headers:\n'
        '  "Procure-to-Pay": "จัดซื้อ"\n'
        'links:\n'
        '  "https://example.com": "ตัวอย่าง"\n',
        encoding="utf-8",
    )
    out = load_overrides(cfg)
    assert out == {
        "headers": {"Procure-to-Pay": "จัดซื้อ"},
        "links": {"https://example.com": "ตัวอย่าง"},
    }


def test_load_overrides_empty_sections(tmp_path: Path):
    """Empty mappings (`{}`) become empty dicts."""
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text("headers: {}\nlinks: {}\n", encoding="utf-8")
    assert load_overrides(cfg) == {"headers": {}, "links": {}}


def test_load_overrides_missing_section_defaults_to_empty(tmp_path: Path):
    """If `headers:` or `links:` is omitted, default to empty dict."""
    cfg = tmp_path / "nav-overrides.yaml"
    cfg.write_text("headers:\n  A: B\n", encoding="utf-8")
    out = load_overrides(cfg)
    assert out == {"headers": {"A": "B"}, "links": {}}
