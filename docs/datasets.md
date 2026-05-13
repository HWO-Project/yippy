# Available YIPs and Downloading

`yippy` ships a curated catalog of yield input packages (YIPs) that you can
download with a single function call. The data is hosted on Zenodo and
cached locally on first use via [pooch](https://www.fatiando.org/pooch/).

## Available datasets

The table below is generated from `yippy.datasets.CATALOG` at doc-build
time and lists every YIP yippy knows about. Every entry in the catalog
is fetchable; new YIPs are added only once their archive is on Zenodo
and the md5 hash is locked into the catalog.

```{include} _generated/yip_catalog.md
```

## Sampling

YIP names end with a sampling-regime suffix:

- `_1d` -- radially-symmetric sampling. The PSF cube is indexed by radial
  separation; lighter weight, suitable for back-of-envelope yield work.
- `_2d` -- full 2D off-axis grid. Captures azimuthal variation; required
  whenever PSF asymmetries matter (e.g. for spatially-resolved benchmarks).

## Loading a YIP

Three styles, all equivalent for clean cases:

```python
from yippy import fetch_yip, Coronagraph

# Flat name (best when you already know it)
path = fetch_yip("eac1_aavc_2d")

# Structured query (must resolve to a single entry). Pass sampling
# whenever a (telescope, coronagraph) pair has both 1D and 2D variants.
path = fetch_yip(telescope="eac1", coronagraph="aavc", sampling="2d")

# Convenient: top-level re-exports
import yippy
path = yippy.fetch_yip("eac1_aavc_2d")

# Then load it
coro = Coronagraph(path)
```

The first call downloads and unpacks the archive into the pooch cache
(roughly 30 MB per 1D YIP, ~75 MB for the 2D AAVC). Subsequent calls hit
the cache and are instantaneous.

## Discovery helpers

Three small helpers let you browse the catalog without downloading anything.

### `list_yips` -- filter the catalog

```python
>>> from yippy import list_yips
>>> list_yips(telescope="eac1")
['eac1_aavc_1d',
 'eac1_spc_1d',
 'eac1_lcppc_v1_1d',
 'eac1_optimal_order_6_1d',
 'eac1_pic_400channels_order6_1d',
 'eac1_aavc_2d']

>>> list_yips(coronagraph="optimal_order_6")
['eac1_optimal_order_6_1d',
 'eac2_optimal_order_6_1d',
 'eac3_optimal_order_6_1d']

>>> list_yips(sampling="2d")
['eac1_aavc_2d']

>>> list_yips()  # everything
```

Valid filter keys are `telescope`, `coronagraph`, and `sampling`. Combine
any of them; the call returns names whose metadata matches every filter.

### `yip_exists` -- membership check

```python
>>> from yippy import yip_exists
>>> yip_exists("eac1_aavc_2d")
True
>>> yip_exists("not_a_yip")
False
```

### `yip_info` -- inspect metadata

```python
>>> from yippy import yip_info
>>> yip_info("eac1_aavc_2d")
{'telescope': 'eac1',
 'coronagraph': 'aavc',
 'designer': 'Susan Redmond',
 'md5': 'md5:1f4892faff18e55cbec9781a055bea4d',
 'sampling': '2d'}
```

Descriptive metadata beyond these fields (wavelengths, dark-zone extent,
pixel scale, ...) lives in each YIP's FITS headers, not in the catalog.

## Migration from `fetch_coronagraph`

The old `fetch_coronagraph()` helper was removed in this release. The
default it returned was a 2D AAVC YIP; the direct replacement is:

| Old call | New call |
|---|---|
| `fetch_coronagraph()` | `fetch_yip("eac1_aavc_2d")` |
| `fetch_coronagraph("eac1_aavc_512")` | `fetch_yip("eac1_aavc_2d")` |
