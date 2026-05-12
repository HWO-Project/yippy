"""Tests for yippy.datasets - catalog integrity and public API."""

from __future__ import annotations

import re

import pytest

from yippy import datasets

VALID_HASH = re.compile(r"^md5:[0-9a-f]{32}$")


VALID_SAMPLING_SUFFIXES = ("_1d", "_2d")


def test_catalog_has_19_entries():
    """Catalog must contain exactly 19 entries (18 1D + 1 2D)."""
    assert len(datasets.CATALOG) == 19


def test_catalog_keys_match_telescope_coronagraph_sampling():
    """Each key must equal ``{telescope}_{coronagraph}_(1d|2d)``."""
    for name, meta in datasets.CATALOG.items():
        prefix = f"{meta['telescope']}_{meta['coronagraph']}"
        assert name.startswith(prefix), f"key {name!r} doesn't start with {prefix!r}"
        suffix = name[len(prefix) :]
        assert suffix in VALID_SAMPLING_SUFFIXES, (
            f"key {name!r} has unknown sampling suffix {suffix!r}"
        )


def test_catalog_required_fields():
    """Every entry must carry telescope, coronagraph, designer, and md5 fields."""
    required = {"telescope", "coronagraph", "designer", "md5"}
    for name, meta in datasets.CATALOG.items():
        missing = required - set(meta)
        assert not missing, f"{name!r} missing fields: {missing}"


def test_catalog_md5_format():
    """md5 must be None or match the ``md5:<32 hex>`` format."""
    for name, meta in datasets.CATALOG.items():
        md5 = meta["md5"]
        assert md5 is None or VALID_HASH.match(md5), f"{name!r} has bad md5: {md5!r}"


def test_publishable_count():
    """Publishable count must be 0 (pre-build) or 13 (post-build, 12 1D + 1 2D)."""
    publishable = sum(1 for m in datasets.CATALOG.values() if m["md5"] is not None)
    assert publishable in {0, 13}, (
        f"expected 0 (pre-build) or 13 (post-build) publishable, got {publishable}"
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
    assert len(names) == 7  # 6 1D + 1 2D for eac1
    assert all(n.startswith("eac1_") for n in names)


def test_list_yips_coronagraph_filter():
    """Filtering by coronagraph returns matches across telescopes and samplings."""
    names = datasets.list_yips(coronagraph="aavc")
    assert sorted(names) == [
        "eac1_aavc_1d",
        "eac1_aavc_2d",
        "eac2_aavc_1d",
        "eac3_aavc_1d",
    ]


def test_list_yips_combined_filter():
    """Combining telescope and coronagraph filters narrows when sampling is unique."""
    names = datasets.list_yips(telescope="eac3", coronagraph="aplc")
    assert names == ["eac3_aplc_1d"]


def test_list_yips_unknown_kwarg_raises_typeerror():
    """An unknown filter keyword raises TypeError with a helpful message."""
    with pytest.raises(TypeError, match="unknown filter"):
        datasets.list_yips(telescpoe="eac1")  # typo intentional


def test_list_yips_no_match_returns_empty():
    """list_yips() with no matching filters returns an empty list."""
    assert datasets.list_yips(telescope="lmt_42") == []


def test_yip_exists_published_after_build_is_skipped_when_md5_none():
    """yip_exists() returns True only when the entry has a real md5 hash.

    Pre-build all md5s are None and exists() is always False. Once a real
    md5 is populated for an entry, this returns True.
    """
    assert datasets.yip_exists("eac1_aavc_2d") == (
        datasets.CATALOG["eac1_aavc_2d"]["md5"] is not None
    )


def test_yip_exists_unknown_name():
    """yip_exists() returns False for an unknown YIP name."""
    assert datasets.yip_exists("not_a_real_yip") is False


def test_yip_exists_reserved_entry_returns_false():
    """eac3_spc_1d is a reserved entry - never publishable."""
    assert datasets.yip_exists("eac3_spc_1d") is False


def test_yip_info_returns_metadata_dict():
    """yip_info() returns the catalog metadata dict for a known entry."""
    info = datasets.yip_info("eac1_aavc_1d")
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
        datasets.fetch_yip("eac1_aavc_1d", telescope="eac1")


def test_fetch_yip_neither_name_nor_kwargs_raises():
    """Passing neither a name nor filter kwargs raises TypeError."""
    with pytest.raises(TypeError, match="either"):
        datasets.fetch_yip()


def test_fetch_yip_unknown_name_raises_keyerror_with_suggestions():
    """fetch_yip() suggests close catalog names when the lookup fails."""
    with pytest.raises(KeyError) as exc:
        datasets.fetch_yip("eac1_aavc")  # missing sampling suffix
    # difflib should suggest one of the eac1_aavc_* entries
    assert "eac1_aavc" in str(exc.value)


def test_fetch_yip_zero_match_query_raises_valueerror():
    """A structured query with no matches raises ValueError."""
    with pytest.raises(ValueError, match="No YIP matches"):
        datasets.fetch_yip(telescope="lmt_42", coronagraph="aavc")


def test_fetch_yip_multi_match_query_raises_valueerror():
    """A structured query that matches multiple entries raises ValueError."""
    # Filtering by telescope alone matches every coronagraph and sampling
    # within that telescope (7 entries for eac1: 6 1D + 1 2D).
    with pytest.raises(ValueError, match="multiple"):
        datasets.fetch_yip(telescope="eac1")


def test_fetch_yip_reserved_entry_raises_lookuperror():
    """eac3_spc_1d is reserved (md5=None). Should raise LookupError."""
    with pytest.raises(LookupError, match="not yet hosted"):
        datasets.fetch_yip("eac3_spc_1d")


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

    # Pretend eac1_aavc_2d has been published
    monkeypatch.setitem(datasets.CATALOG["eac1_aavc_2d"], "md5", "md5:" + "a" * 32)
    monkeypatch.setattr(datasets._POOCH, "fetch", fake_fetch, raising=False)
    # Also need to add to pooch registry so it accepts the fetch call
    datasets._POOCH.registry["eac1_aavc_2d.zip"] = "md5:" + "a" * 32

    path = datasets.fetch_yip("eac1_aavc_2d")
    assert called["filename"] == "eac1_aavc_2d.zip"
    assert isinstance(called["processor"], Unzip)
    assert path.endswith("eac1_aavc_2d")


@pytest.mark.network
@pytest.mark.skipif(
    datasets.ZENODO_DOI.endswith("PLACEHOLDER"),
    reason="Zenodo DOI not yet set; v1 release pending.",
)
@pytest.mark.skipif(
    datasets.CATALOG["eac1_aavc_2d"]["md5"] is None,
    reason="eac1_aavc_2d md5 not yet populated; run packaging script.",
)
def test_fetch_smallest_yip_loads_as_coronagraph(tmp_path):
    """End-to-end: pull the smallest publishable YIP and load yippy.Coronagraph."""
    from pathlib import Path

    from yippy import Coronagraph

    yip_path = Path(datasets.fetch_yip("eac1_aavc_2d"))
    for required in (
        "offax_psf.fits",
        "offax_psf_offset_list.fits",
        "stellar_intens.fits",
        "stellar_intens_diam_list.fits",
        "sky_trans.fits",
    ):
        assert (yip_path / required).is_file(), f"missing {required}"

    coro = Coronagraph(yip_path)
    assert coro is not None
