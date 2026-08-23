from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .apis import AuthApi, ItemApi, MediaApi, SearchApi, TradeApi, UserApi
from .core import (
    XianyuApiError,
    XianyuClient,
    XianyuConfigError,
    XianyuError,
    XianyuRequestError,
    XianyuResponseError,
    XianyuYhbRequiredError,
)
from .xianyu_apis import XianyuApis
from .xianyu_live import XianyuLive

try:
    __version__ = version("pyxianyu")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "AuthApi",
    "ItemApi",
    "MediaApi",
    "SearchApi",
    "TradeApi",
    "UserApi",
    "XianyuApiError",
    "XianyuClient",
    "XianyuConfigError",
    "XianyuError",
    "XianyuRequestError",
    "XianyuResponseError",
    "XianyuYhbRequiredError",
    "XianyuApis",
    "XianyuLive",
]
