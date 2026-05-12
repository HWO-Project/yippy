"""yippy allows for a coronagraph object to be created from a yield input package."""

__all__ = [
    "Coronagraph",
    "EqxCoronagraph",
    "__version__",
    "fetch_yip",
    "list_yips",
    "logger",
    "yip_exists",
    "yip_info",
]

from ._version import __version__
from .coronagraph import Coronagraph
from .datasets import fetch_yip, list_yips, yip_exists, yip_info
from .eqx_coronagraph import EqxCoronagraph
from .logger import logger
