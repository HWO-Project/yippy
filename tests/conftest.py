"""Shared fixtures for yippy tests."""

import pytest

from yippy import Coronagraph
from yippy.datasets import CATALOG, DATA_RELEASE_TAG

requires_available_yip = pytest.mark.skipif(
    CATALOG["eac1_aavc_2d"]["md5"] is None or DATA_RELEASE_TAG.endswith("PLACEHOLDER"),
    reason="YIP not yet fetchable: md5 unset or release tag is placeholder.",
)


@pytest.fixture(scope="session")
def coro():
    """Session-scoped real coronagraph loaded from yippy's pooch registry."""
    from yippy import fetch_yip

    yip_path = fetch_yip("eac1_aavc_2d")
    return Coronagraph(yip_path)


@pytest.fixture(scope="session")
def eqx_coro(coro):
    """Session-scoped EqxCoronagraph built from the real coronagraph."""
    from yippy.eqx_coronagraph import EqxCoronagraph

    return EqxCoronagraph(yippy_coro=coro)
