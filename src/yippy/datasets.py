"""Public catalog and loader for yield input packages (YIPs).

The CATALOG dict is the source of truth: keys are flat YIP names like
``eac1_aavc``; values carry just enough metadata to drive downloads and
filtered discovery (``telescope``, ``coronagraph``, ``md5``). Descriptive
metadata (designer, wavelengths, dark-zone extent, ...) lives in the FITS
headers inside each YIP, not here.

Archives are hosted on Zenodo and fetched via pooch's DOI protocol. To
publish new YIPs: upload a new Zenodo record version, paste the new DOI
into ``ZENODO_DOI``, and refresh the md5 hashes via
``scripts/build_zenodo_archives.py``.

Public API:
- ``fetch_yip(name=None, *, telescope=None, coronagraph=None) -> str``
- ``list_yips(**filters) -> list[str]``
- ``yip_exists(name) -> bool``
- ``yip_info(name) -> dict``
"""

from __future__ import annotations

from typing import Any

import pooch

# ---------------------------------------------------------------------------
# Zenodo DOI for the published YIP archive. Updated when a new version of
# the record is published. Until the v1 upload happens, this is a TBD
# placeholder; integration tests are skipped while it points at the
# placeholder.
# ---------------------------------------------------------------------------
ZENODO_DOI: str = "10.5281/zenodo.PLACEHOLDER"


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
CATALOG: dict[str, dict[str, Any]] = {
    # EAC1
    "eac1_aavc": {"telescope": "eac1", "coronagraph": "aavc", "md5": None},
    "eac1_spc": {"telescope": "eac1", "coronagraph": "spc", "md5": None},
    "eac1_lcppc_v1": {"telescope": "eac1", "coronagraph": "lcppc_v1", "md5": None},
    "eac1_optimal_order_6": {
        "telescope": "eac1",
        "coronagraph": "optimal_order_6",
        "md5": None,
    },
    "eac1_aplc": {"telescope": "eac1", "coronagraph": "aplc", "md5": None},
    "eac1_pic_400channels_order6": {
        "telescope": "eac1",
        "coronagraph": "pic_400channels_order6",
        "md5": None,
    },
    # EAC2
    "eac2_aavc": {"telescope": "eac2", "coronagraph": "aavc", "md5": None},
    "eac2_spc": {"telescope": "eac2", "coronagraph": "spc", "md5": None},
    "eac2_lcppc_v1": {"telescope": "eac2", "coronagraph": "lcppc_v1", "md5": None},
    "eac2_optimal_order_6": {
        "telescope": "eac2",
        "coronagraph": "optimal_order_6",
        "md5": None,
    },
    "eac2_aplc": {"telescope": "eac2", "coronagraph": "aplc", "md5": None},
    "eac2_pic_400channels_order6": {
        "telescope": "eac2",
        "coronagraph": "pic_400channels_order6",
        "md5": None,
    },
    # EAC3
    "eac3_aavc": {"telescope": "eac3", "coronagraph": "aavc", "md5": None},
    "eac3_spc": {"telescope": "eac3", "coronagraph": "spc", "md5": None},
    "eac3_lcppc_v1": {"telescope": "eac3", "coronagraph": "lcppc_v1", "md5": None},
    "eac3_optimal_order_6": {
        "telescope": "eac3",
        "coronagraph": "optimal_order_6",
        "md5": None,
    },
    "eac3_aplc": {"telescope": "eac3", "coronagraph": "aplc", "md5": None},
    "eac3_pic_400channels_order6": {
        "telescope": "eac3",
        "coronagraph": "pic_400channels_order6",
        "md5": None,
    },
}


# Filled in lazily — pooch instance depends on the catalog state at import time.
_POOCH = pooch.create(
    path=pooch.os_cache("yippy"),
    base_url=f"doi:{ZENODO_DOI}/",
    registry={
        f"{name}.zip": meta["md5"]
        for name, meta in CATALOG.items()
        if meta["md5"] is not None
    },
)


# ---------------------------------------------------------------------------
# Public API (stubs — implemented in later tasks)
# ---------------------------------------------------------------------------
def fetch_yip(
    name: str | None = None,
    *,
    telescope: str | None = None,
    coronagraph: str | None = None,
) -> str:
    """Download and return the path to a YIP (implemented in Task 4-5)."""
    raise NotImplementedError  # Task 4-5


def list_yips(**filters: str) -> list[str]:
    """Return catalog names filtered by keyword arguments (implemented in Task 2)."""
    raise NotImplementedError  # Task 2


def yip_exists(name: str) -> bool:
    """Return True if ``name`` is a known catalog key (implemented in Task 3)."""
    raise NotImplementedError  # Task 3


def yip_info(name: str) -> dict[str, Any]:
    """Return the catalog metadata for ``name`` (implemented in Task 3)."""
    raise NotImplementedError  # Task 3
