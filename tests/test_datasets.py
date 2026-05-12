"""Tests for yippy.datasets - catalog integrity and public API."""

from __future__ import annotations

import re

import pytest

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


def test_list_yips_no_filter_returns_all():
    """list_yips() with no filters returns all catalog keys."""
    names = datasets.list_yips()
    assert sorted(names) == sorted(datasets.CATALOG.keys())


def test_list_yips_telescope_filter():
    """Filtering by telescope returns only matching entries."""
    names = datasets.list_yips(telescope="eac1")
    assert len(names) == 6
    assert all(n.startswith("eac1_") for n in names)


def test_list_yips_coronagraph_filter():
    """Filtering by coronagraph returns one entry per telescope."""
    names = datasets.list_yips(coronagraph="aavc")
    assert sorted(names) == ["eac1_aavc", "eac2_aavc", "eac3_aavc"]


def test_list_yips_combined_filter():
    """Combining telescope and coronagraph filters narrows to a single match."""
    names = datasets.list_yips(telescope="eac3", coronagraph="aplc")
    assert names == ["eac3_aplc"]


def test_list_yips_unknown_kwarg_raises_typeerror():
    """An unknown filter keyword raises TypeError with a helpful message."""
    with pytest.raises(TypeError, match="unknown filter"):
        datasets.list_yips(telescpoe="eac1")  # typo intentional


def test_list_yips_no_match_returns_empty():
    """list_yips() with no matching filters returns an empty list."""
    assert datasets.list_yips(telescope="lmt_42") == []


def test_yip_exists_published_after_build_is_skipped_when_md5_none():
    """yip_exists() returns True only when the entry has a real md5 hash.

    Before Task 8 runs, all md5s are None and exists() is always False.
    After Task 8 runs and CATALOG has real md5s for 12 entries, this test
    behaves accordingly.
    """
    # eac1_aavc is expected to be in the publishable set
    assert datasets.yip_exists("eac1_aavc") == (
        datasets.CATALOG["eac1_aavc"]["md5"] is not None
    )


def test_yip_exists_unknown_name():
    """yip_exists() returns False for an unknown YIP name."""
    assert datasets.yip_exists("not_a_real_yip") is False


def test_yip_exists_reserved_entry_returns_false():
    """eac3_spc is a reserved entry - never publishable."""
    assert datasets.yip_exists("eac3_spc") is False


def test_yip_info_returns_metadata_dict():
    """yip_info() returns the catalog metadata dict for a known entry."""
    info = datasets.yip_info("eac1_aavc")
    assert info["telescope"] == "eac1"
    assert info["coronagraph"] == "aavc"
    assert "md5" in info


def test_yip_info_unknown_raises_keyerror():
    """yip_info() raises KeyError for an unknown YIP name."""
    with pytest.raises(KeyError, match="not_a_real_yip"):
        datasets.yip_info("not_a_real_yip")


def test_fetch_yip_both_name_and_kwargs_raises():
    """Passing both a name and filter kwargs raises TypeError."""
    with pytest.raises(TypeError, match="either"):
        datasets.fetch_yip("eac1_aavc", telescope="eac1")


def test_fetch_yip_neither_name_nor_kwargs_raises():
    """Passing neither a name nor filter kwargs raises TypeError."""
    with pytest.raises(TypeError, match="either"):
        datasets.fetch_yip()


def test_fetch_yip_unknown_name_raises_keyerror_with_suggestions():
    """fetch_yip() suggests close catalog names when the lookup fails."""
    with pytest.raises(KeyError) as exc:
        datasets.fetch_yip("eac1_avc")  # typo: missing 'a'
    # difflib should suggest "eac1_aavc" (one of the close matches)
    assert "eac1_aavc" in str(exc.value)


def test_fetch_yip_zero_match_query_raises_valueerror():
    """A structured query with no matches raises ValueError."""
    with pytest.raises(ValueError, match="No YIP matches"):
        datasets.fetch_yip(telescope="lmt_42", coronagraph="aavc")


def test_fetch_yip_multi_match_query_raises_valueerror():
    """A structured query that matches multiple entries raises ValueError."""
    # No filters narrows to nothing - we need 2 entries with same field.
    # With the structured catalog every (telescope, coronagraph) pair is
    # unique, so we provoke a multi-match by only filtering on telescope
    # (returns 6 names).
    with pytest.raises(ValueError, match="multiple"):
        datasets.fetch_yip(telescope="eac1")


def test_fetch_yip_reserved_entry_raises_lookuperror():
    """eac3_spc is reserved (md5=None). Should raise LookupError."""
    with pytest.raises(LookupError, match="not yet hosted"):
        datasets.fetch_yip("eac3_spc")


def test_fetch_yip_calls_pooch_for_published(monkeypatch, tmp_path):
    """Verify the function resolves the catalog correctly and calls pooch.fetch.

    The pooch call itself is mocked.
    """
    from pooch import Unzip

    called = {}

    def fake_fetch(filename, processor=None):
        called["filename"] = filename
        called["processor"] = processor
        # pooch.fetch with Unzip returns a list of paths
        return [str(tmp_path / filename / "offax_psf.fits")]

    # Pretend eac1_aavc has been published
    monkeypatch.setitem(datasets.CATALOG["eac1_aavc"], "md5", "md5:" + "a" * 32)
    monkeypatch.setattr(datasets._POOCH, "fetch", fake_fetch, raising=False)
    # Also need to add to pooch registry so it accepts the fetch call
    datasets._POOCH.registry["eac1_aavc.zip"] = "md5:" + "a" * 32

    path = datasets.fetch_yip("eac1_aavc")
    assert called["filename"] == "eac1_aavc.zip"
    assert isinstance(called["processor"], Unzip)
    assert path.endswith("eac1_aavc")
