# Available YIPs and Downloading

`yippy` ships a curated catalog of yield input packages (YIPs) that you can
download with a single function call. The data is hosted on Zenodo and
cached locally on first use via [pooch](https://www.fatiando.org/pooch/).

## Available datasets

The table below is generated from `yippy.datasets.CATALOG` at doc-build
time and lists every YIP yippy knows about.

```{include} _generated/yip_catalog.md
```

Entries marked **reserved** are catalogued for a future release but the
underlying data has not yet been delivered by the designer. Calling
`fetch_yip` on a reserved entry raises `LookupError`.

## Loading a YIP

Three styles, all equivalent for clean cases:

```python
from yippy import fetch_yip, Coronagraph

# Flat name (best when you already know it)
path = fetch_yip("eac1_aavc")

# Structured query (best for "give me eac1's vortex")
path = fetch_yip(telescope="eac1", coronagraph="aavc")

# Convenient: top-level re-exports
import yippy
path = yippy.fetch_yip("eac1_aavc")

# Then load it
coro = Coronagraph(path)
```

The first call downloads and unpacks the archive into the pooch cache
(roughly 30 MB per YIP). Subsequent calls hit the cache and are
instantaneous.

## Discovery helpers

```python
from yippy import list_yips, yip_exists, yip_info

# All names matching filters
list_yips(telescope="eac1")          # all eac1 variants
list_yips(coronagraph="optimal_order_6")  # one per telescope

# Check whether a name is published
yip_exists("eac1_aavc")  # True (post-v1)
yip_exists("eac3_spc")   # False - reserved

# Inspect metadata
yip_info("eac1_aavc")
# {"telescope": "eac1", "coronagraph": "aavc", "md5": "md5:..."}
```

## Migration from `fetch_coronagraph`

The old `fetch_coronagraph()` helper was removed in this release. The
mapping is:

| Old call | New call |
|---|---|
| `fetch_coronagraph()` | `fetch_yip("eac1_aavc")` |
| `fetch_coronagraph("eac1_aavc_512")` | `fetch_yip("eac1_aavc")` |
