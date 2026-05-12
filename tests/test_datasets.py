"""Tests for yippy.datasets — catalog integrity and public API."""

from __future__ import annotations

import re

from yippy import datasets

VALID_HASH = re.compile(r"^md5:[0-9a-f]{32}$")


def test_catalog_has_18_entries():
    """Catalog must contain exactly 18 YIP entries."""
    assert len(datasets.CATALOG) == 18


def test_catalog_keys_match_telescope_coronagraph():
    """Each key must equal ``{telescope}_{coronagraph}``."""
    for name, meta in datasets.CATALOG.items():
        expected = f"{meta['telescope']}_{meta['coronagraph']}"
        assert name == expected, f"key {name!r} does not match {expected!r}"


def test_catalog_required_fields():
    """Every entry must carry telescope, coronagraph, and md5 fields."""
    required = {"telescope", "coronagraph", "md5"}
    for name, meta in datasets.CATALOG.items():
        missing = required - set(meta)
        assert not missing, f"{name!r} missing fields: {missing}"


def test_catalog_md5_format():
    """md5 must be None or match the ``md5:<32 hex>`` format."""
    for name, meta in datasets.CATALOG.items():
        md5 = meta["md5"]
        assert md5 is None or VALID_HASH.match(md5), f"{name!r} has bad md5: {md5!r}"


def test_no_duplicate_telescope_coronagraph_pairs():
    """No two entries may share the same (telescope, coronagraph) pair."""
    seen: set[tuple[str, str]] = set()
    for meta in datasets.CATALOG.values():
        pair = (meta["telescope"], meta["coronagraph"])
        assert pair not in seen, f"duplicate {pair}"
        seen.add(pair)


def test_publishable_count():
    """Publishable count must be 0 (pre-build) or 12 (post-Task-8 build).

    12 entries should be publishable (md5 != None) once Task 8 runs.
    Before Task 8: all are None and count is 0.
    """
    publishable = sum(1 for m in datasets.CATALOG.values() if m["md5"] is not None)
    assert publishable in {0, 12}, (
        f"expected 0 (pre-build) or 12 (post-build) publishable, got {publishable}"
    )


def test_fetch_coronagraph_removed():
    """Hard break of the legacy API."""
    assert not hasattr(datasets, "fetch_coronagraph")
