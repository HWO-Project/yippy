"""Public catalog and loader for yield input packages (YIPs).

The CATALOG dict is the source of truth: keys are flat YIP names like
``eac1_aavc_2d``; values carry just enough metadata to drive downloads
and filtered discovery (``telescope``, ``coronagraph``, ``sampling``,
``md5``). Descriptive metadata (designer, wavelengths, dark-zone
extent, ...) lives in the FITS headers inside each YIP, not here.

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

import difflib
from pathlib import Path
from typing import Any

import pooch
from pooch import Unzip

# ---------------------------------------------------------------------------
# Zenodo DOI for the YIP archive. Updated when a new version of the record
# is published on Zenodo.
# ---------------------------------------------------------------------------
ZENODO_DOI: str = "10.5281/zenodo.20146086"


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
CATALOG: dict[str, dict[str, Any]] = {
    # EAC1 (1D)
    "eac1_aavc_1d": {
        "telescope": "eac1",
        "coronagraph": "aavc",
        "designer": "Susan Redmond",
        "md5": "md5:5cb5fe8bd29c8f4d2abf47b259535061",
    },
    "eac1_spc_1d": {
        "telescope": "eac1",
        "coronagraph": "spc",
        "designer": "Jessica Gersh-Range",
        "md5": "md5:1b70ddebb8b89226b206c6d08817542d",
    },
    "eac1_lcppc_v1_1d": {
        "telescope": "eac1",
        "coronagraph": "lcppc_v1",
        "designer": "David Doelman",
        "md5": "md5:189101a21fdffe7e2a013712f34da83b",
    },
    "eac1_optimal_order_6_1d": {
        "telescope": "eac1",
        "coronagraph": "optimal_order_6",
        "designer": "Rus Belikov",
        "md5": "md5:df52540008a0e85467720ec91c3a84b8",
    },
    "eac1_pic_400channels_order6_1d": {
        "telescope": "eac1",
        "coronagraph": "pic_400channels_order6",
        "designer": "Dan Sirbu",
        "md5": "md5:b90c4600fc32edfc6007c7fff2642036",
    },
    # EAC2 (1D)
    "eac2_lcppc_v1_1d": {
        "telescope": "eac2",
        "coronagraph": "lcppc_v1",
        "designer": "David Doelman",
        "md5": "md5:80cfbad3f63eb7c49b467342d19e32cc",
    },
    "eac2_optimal_order_6_1d": {
        "telescope": "eac2",
        "coronagraph": "optimal_order_6",
        "designer": "Rus Belikov",
        "md5": "md5:579c80c9e3f7f52a0ebd18858485fa4b",
    },
    "eac2_pic_400channels_order6_1d": {
        "telescope": "eac2",
        "coronagraph": "pic_400channels_order6",
        "designer": "Dan Sirbu",
        "md5": "md5:384c79d3ac1777c0c2680348cb84fcce",
    },
    # EAC3 (1D)
    "eac3_lcppc_v1_1d": {
        "telescope": "eac3",
        "coronagraph": "lcppc_v1",
        "designer": "David Doelman",
        "md5": "md5:dd97beca90e8a1f47c0efe8490d40f27",
    },
    "eac3_optimal_order_6_1d": {
        "telescope": "eac3",
        "coronagraph": "optimal_order_6",
        "designer": "Rus Belikov",
        "md5": "md5:7c7a76d324f5b62ba2f0523534dd8076",
    },
    "eac3_aplc_1d": {
        "telescope": "eac3",
        "coronagraph": "aplc",
        "designer": "Bryony Nickson",
        "md5": "md5:2c880190f36d92d7d4c5785a9ebf994a",
    },
    "eac3_pic_400channels_order6_1d": {
        "telescope": "eac3",
        "coronagraph": "pic_400channels_order6",
        "designer": "Dan Sirbu",
        "md5": "md5:5b530b87c2ee6020118455789ac4328e",
    },
    # EAC1 (2D)
    "eac1_aavc_2d": {
        "telescope": "eac1",
        "coronagraph": "aavc",
        "designer": "Susan Redmond",
        "md5": "md5:1f4892faff18e55cbec9781a055bea4d",
    },
}


# Inject the sampling regime as a derived field on each catalog entry, parsed
# from the key suffix. Keeps the manual CATALOG above tidy while exposing
# sampling as a filterable axis in list_yips / fetch_yip.
for _name, _meta in CATALOG.items():
    if _name.endswith("_1d"):
        _meta["sampling"] = "1d"
    elif _name.endswith("_2d"):
        _meta["sampling"] = "2d"
    else:
        raise RuntimeError(f"Catalog key {_name!r} must end with `_1d` or `_2d`")
del _name, _meta


# Pooch instance; every catalog entry is registered with its md5.
_POOCH = pooch.create(
    path=pooch.os_cache("yippy"),
    base_url=f"doi:{ZENODO_DOI}/",
    registry={f"{name}.zip": meta["md5"] for name, meta in CATALOG.items()},
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def fetch_yip(
    name: str | None = None,
    *,
    telescope: str | None = None,
    coronagraph: str | None = None,
    sampling: str | None = None,
) -> str:
    """Download a YIP archive (if not cached), unpack, and return its path.

    Pass either ``name`` (flat: ``"eac1_aavc_2d"``) OR keyword filters
    (structured: ``telescope="eac1", coronagraph="aavc", sampling="2d"``).
    The keyword form must resolve to exactly one catalog entry; pass
    ``sampling`` whenever a ``(telescope, coronagraph)`` pair has both
    1D and 2D variants.

    Raises:
        TypeError: if both ``name`` and filters are passed (or neither).
        KeyError: if ``name`` is not in the catalog.
        ValueError: if the structured query has zero or multiple matches.
    """
    filters: dict[str, str] = {}
    if telescope is not None:
        filters["telescope"] = telescope
    if coronagraph is not None:
        filters["coronagraph"] = coronagraph
    if sampling is not None:
        filters["sampling"] = sampling

    if name is not None and filters:
        raise TypeError("Pass either `name` or filter kwargs, not both.")
    if name is None and not filters:
        raise TypeError("Pass either `name` or filter kwargs.")

    if name is not None:
        if name not in CATALOG:
            suggestions = difflib.get_close_matches(name, CATALOG.keys(), n=5)
            hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            raise KeyError(f"Unknown YIP {name!r}.{hint}")
        resolved = name
    else:
        matches = list_yips(**filters)
        if not matches:
            raise ValueError(
                f"No YIP matches {filters!r}. Try yippy.list_yips() to see options."
            )
        if len(matches) > 1:
            raise ValueError(
                f"Filters {filters!r} matched multiple YIPs: {matches}. "
                "Pass `name=` directly or narrow filters."
            )
        resolved = matches[0]

    paths = _POOCH.fetch(f"{resolved}.zip", processor=Unzip())
    # Unzip returns a list of paths under the unzipped dir. The YIP itself
    # lives at the archive root under `{name}/`. Return the directory.
    sample_path = Path(paths[0])
    yip_dir = sample_path.parent
    # Walk up looking for a directory named after the YIP. If we hit a
    # `{resolved}.zip` directory first (e.g. the unzip cache folder),
    # treat its sibling/parent path as the YIP directory.
    while yip_dir.parent != yip_dir:
        if yip_dir.name == resolved:
            return str(yip_dir)
        if yip_dir.name == f"{resolved}.zip":
            return str(yip_dir.parent / resolved)
        yip_dir = yip_dir.parent
    # Fallback: return the immediate parent of the sample file.
    return str(sample_path.parent)


_FILTERABLE_FIELDS = frozenset({"telescope", "coronagraph", "sampling"})


def list_yips(**filters: str) -> list[str]:
    """Return catalog names matching all filters. No filters returns all names.

    Raises:
        TypeError: if a filter key is not a valid catalog field.
    """
    unknown = set(filters) - _FILTERABLE_FIELDS
    if unknown:
        raise TypeError(
            f"unknown filter keys: {sorted(unknown)}. "
            f"Valid keys are {sorted(_FILTERABLE_FIELDS)}."
        )
    out = []
    for name, meta in CATALOG.items():
        if all(meta.get(k) == v for k, v in filters.items()):
            out.append(name)
    return out


def yip_exists(name: str) -> bool:
    """True iff ``name`` is an available YIP in the catalog."""
    return name in CATALOG


def yip_info(name: str) -> dict[str, Any]:
    """Return the catalog metadata dict for ``name``.

    Raises:
        KeyError: if ``name`` is not in the catalog.
    """
    if name not in CATALOG:
        raise KeyError(name)
    return CATALOG[name]
