"""Precision policy: yippy follows the global jax_enable_x64 flag (default float32)."""

import jax
import numpy as np
from conftest import assert_eqx_arrays_match_active_dtype

from yippy import _precision as P


def test_float_dtype_is_f32_by_default():
    """Default (x64-off) process resolves the active float dtype to float32."""
    assert jax.config.jax_enable_x64 is False
    assert np.dtype(P.float_dtype()) == np.float32


def test_dtype_tag_is_f32_by_default():
    """The cache tag is 'f32' when x64 is off."""
    assert P.dtype_tag() == "f32"


def test_datacube_cache_path_is_dtype_keyed(coro):
    """The PSF datacube cache filename carries the active dtype tag."""
    # Default x64-off -> "f32" tag; quarter datacube is the default.
    p = coro._datacube_cache_path
    assert p.name == "psf_datacube_quarter_f32.npy"
    assert p.parent == coro._cache_dir


def test_eqx_stored_arrays_are_f32_by_default(eqx_coro):
    """In the default (x64-off) suite, EqxCoronagraph float arrays are float32."""
    assert_eqx_arrays_match_active_dtype(eqx_coro)
