"""Shared pytest fixtures for sync_nav tests."""
from pathlib import Path
import pytest


@pytest.fixture
def repo_root() -> Path:
    """Absolute path to the carmen-wiki repo root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent
