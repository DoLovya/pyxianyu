from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .apis import AuthApi, ItemApi, MediaApi, SearchApi, UserApi
from .core import XianyuClient

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
    "UserApi",
    "XianyuClient",
]

