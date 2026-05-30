"""Shared fixtures for yippy tests."""

import numpy as np
import pytest

from yippy import Coronagraph
from yippy._precision import float_dtype
from yippy.datasets import CATALOG, DATA_RELEASE_TAG


def assert_eqx_arrays_match_active_dtype(eqx_coro):
    """Assert every stored/forward float array on an EqxCoronagraph is the active dtype.

    Checks a directly stored array (``sky_trans``) plus forward evaluations that
    exercise the stellar-intensity spline, a performance interpolator, and the 2D
    core-intensity interpolant. The forward-output dtype doubles as the
    no-float32-leak guard. Shared by the float32 and float64 precision suites.

    Args:
        eqx_coro: An ``EqxCoronagraph`` built under the active x64 setting.
    """
    expected = np.dtype(float_dtype())
    assert np.dtype(eqx_coro.sky_trans.dtype) == expected, "sky_trans"
    assert np.dtype(eqx_coro.stellar_intens(0.0).dtype) == expected, "stellar_intens"
    assert np.dtype(eqx_coro.throughput(5.0).dtype) == expected, "throughput"
    if eqx_coro._has_2d_core_intensity:
        out_2d = eqx_coro.core_mean_intensity(5.0, 1e-3)
        assert np.dtype(out_2d.dtype) == expected, "core_mean_intensity_2d"


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
