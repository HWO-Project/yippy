# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "astropy",
#     "pooch",
# ]
# ///
r"""Build per-YIP zip archives ready for upload to Zenodo.

Reads source YIPs from a directory tree organized as
``<root>/<TELESCOPE>/<CORONAGRAPH>/`` (case-insensitive), stages the
5 canonical files, zips each YIP, computes md5 hashes, and emits an
updated CATALOG dict for ``yippy.datasets``.

Usage::

    uv run scripts/build_zenodo_archives.py \
        --source ~/path/to/for_rus \
        --out ./dist

After this runs, the engineer uploads dist/*.zip to a new Zenodo
record version, pastes the printed CATALOG block into
src/yippy/datasets.py, and updates ZENODO_DOI to the new DOI.

Cache files are excluded by name pattern (see :data:`EXCLUDE_BASENAMES`,
:data:`EXCLUDE_GLOBS`, and :data:`EXCLUDE_DIRS`).
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import importlib.util
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

# Load just yippy/datasets.py without going through yippy/__init__.py
# (which would trigger jax/equinox imports we don't need here).
_DATASETS_PATH = Path(__file__).resolve().parents[1] / "src" / "yippy" / "datasets.py"
_spec = importlib.util.spec_from_file_location("_yippy_datasets", _DATASETS_PATH)
_datasets = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_datasets)
CATALOG: dict[str, dict[str, Any]] = _datasets.CATALOG


CANONICAL_FILES: tuple[str, ...] = (
    "offax_psf.fits",
    "offax_psf_offset_list.fits",
    "stellar_intens.fits",
    "stellar_intens_diam_list.fits",
    "sky_trans.fits",
)

# Map catalog `coronagraph` value to the source subfolder name. (Telescope
# is uppercased directly: eac{1,2,3} -> EAC{1,2,3}.)
CORONAGRAPH_SUBDIR: dict[str, str] = {
    "aavc": "AAVC",
    "spc": "SPC",
    "lcppc_v1": "LCPPC",
    "optimal_order_6": "Optimal",
    "aplc": "APLC",
    "pic_400channels_order6": "PIC",
}

EXCLUDE_BASENAMES: frozenset[str] = frozenset({".DS_Store"})
EXCLUDE_GLOBS: tuple[str, ...] = (
    "*.npy",
    "coro_perf.fits",
    "coro_perf.fits_v*.fits",
    ".*",  # any hidden file
)
EXCLUDE_DIRS: frozenset[str] = frozenset({"yippy_cache"})


def is_excluded(basename: str) -> bool:
    """True if `basename` should be excluded from packaging."""
    if basename in EXCLUDE_BASENAMES:
        return True
    return any(fnmatch.fnmatchcase(basename, pat) for pat in EXCLUDE_GLOBS)


def locate_source_dir(root: Path, telescope: str, coronagraph: str) -> Path | None:
    """Return the source dir path for a (telescope, coronagraph) pair, or None.

    Returns None if the directory is missing or contains no canonical files.
    The match is case-insensitive on `telescope` (eac1 -> EAC1) and uses
    `CORONAGRAPH_SUBDIR` to translate `coronagraph` to the folder name.
    """
    telescope_dir = root / telescope.upper()
    coro_subdir = CORONAGRAPH_SUBDIR.get(coronagraph)
    if coro_subdir is None:
        return None
    candidate = telescope_dir / coro_subdir
    if not candidate.is_dir():
        return None
    # Must contain at least one canonical file with size > 0
    if not any(
        (candidate / name).is_file() and (candidate / name).stat().st_size > 0
        for name in CANONICAL_FILES
    ):
        return None
    return candidate


def stage_yip(src: Path, staging_root: Path, name: str) -> Path:
    """Copy the 5 canonical files from `src` into ``staging_root/name/``.

    Raises:
        FileNotFoundError: if any canonical file is missing or zero-size.
    """
    target = staging_root / name
    target.mkdir(parents=True, exist_ok=True)
    for fname in CANONICAL_FILES:
        srcfile = src / fname
        if not srcfile.is_file() or srcfile.stat().st_size == 0:
            raise FileNotFoundError(f"Missing or empty: {srcfile}")
        shutil.copy2(srcfile, target / fname)
    return target


def build_archive(src: Path, out_dir: Path, name: str) -> tuple[Path, str]:
    """Stage and zip a YIP. Returns ``(zip_path, md5_string)``.

    The zip is built deterministically: filenames sorted, timestamps
    fixed to the Unix epoch, no compression (FITS is already binary,
    compression adds little and complicates determinism).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{name}.zip"
    with tempfile.TemporaryDirectory() as staging_root:
        staged = stage_yip(src, Path(staging_root), name=name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for fname in sorted(CANONICAL_FILES):
                source_file = staged / fname
                info = zipfile.ZipInfo(filename=f"{name}/{fname}")
                info.date_time = (1980, 1, 1, 0, 0, 0)  # zip epoch
                info.compress_type = zipfile.ZIP_STORED
                with source_file.open("rb") as fh:
                    zf.writestr(info, fh.read())
    md5 = "md5:" + hashlib.md5(zip_path.read_bytes()).hexdigest()
    return zip_path, md5


def format_catalog_block(updates: dict[str, str | None]) -> str:
    """Return the full CATALOG dict as Python source code.

    Entries not in `updates` keep ``md5=None``. Entries in `updates`
    take the provided md5 string (or None for explicitly-reserved).
    """
    lines = ["CATALOG = {"]
    for name, meta in CATALOG.items():
        md5 = updates.get(name, meta["md5"])
        md5_repr = "None" if md5 is None else repr(md5)
        lines.append(
            f'    {name!r}: {{"telescope": {meta["telescope"]!r}, '
            f'"coronagraph": {meta["coronagraph"]!r}, '
            f'"designer": {meta["designer"]!r}, "md5": {md5_repr}}},'
        )
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    """CLI entry point: package every catalog YIP and print updated CATALOG."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Source data root (e.g. .../for_rus/).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("dist"),
        help="Output directory for zip archives (default: ./dist).",
    )
    args = ap.parse_args()

    updates: dict[str, str | None] = {}
    publishable = 0
    reserved = 0
    skipped = 0
    for name, meta in CATALOG.items():
        # Only the 1D YIPs come from the for_rus/ tree. 2D YIPs (and any
        # other out-of-band entries) are packaged separately and we leave
        # their existing md5 alone.
        if not name.endswith("_1d"):
            print(f"  SKIP      {name}  (not a 1D entry; packaged separately)")
            skipped += 1
            continue
        src = locate_source_dir(
            args.source,
            telescope=meta["telescope"],
            coronagraph=meta["coronagraph"],
        )
        if src is None:
            print(f"  RESERVED  {name}  (source missing or empty)")
            updates[name] = None
            reserved += 1
            continue
        zip_path, md5 = build_archive(src, args.out, name=name)
        print(f"  PUBLISH   {name}  ->  {zip_path.name}  {md5}")
        updates[name] = md5
        publishable += 1

    print()
    print(f"# {publishable} publishable, {reserved} reserved, {skipped} skipped")
    print()
    print(format_catalog_block(updates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
