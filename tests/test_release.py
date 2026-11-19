"""Release metadata stays consistent across the files that carry the version."""

from __future__ import annotations

import re
from pathlib import Path

import quality_profiles

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, re.M)
    assert match, "no version in pyproject.toml"
    return match.group(1)


def test_versions_agree():
    version = _pyproject_version()
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert re.search(rf"^version: {re.escape(version)}$", citation, re.M)
    assert quality_profiles.__version__ == version


def test_changelog_has_a_section_for_the_version():
    changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(rf"^## {re.escape(_pyproject_version())}\b", changelog, re.M)
