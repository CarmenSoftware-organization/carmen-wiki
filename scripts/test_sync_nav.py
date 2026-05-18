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
