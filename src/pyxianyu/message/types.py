from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional, Union

from typing_extensions import TypedDict


class TextContent(TypedDict):
    type: Literal["text"]
    text: str


class ImageContent(TypedDict):
    type: Literal["image"]
    image_url: str
    width: int
    height: int


class AudioContent(TypedDict):
    type: Literal["audio"]
    audio_url: str
    duration_ms: int


Message = Union[TextContent, ImageContent, AudioContent]


def make_text(text: str) -> TextContent:
    return {"type": "text", "text": text}


def make_image(url: str, width: int = 0, height: int = 0) -> ImageContent:
    return {"type": "image", "image_url": url, "width": width, "height": height}


def make_audio(url: str, duration_ms: int = 0) -> AudioContent:
    return {"type": "audio", "audio_url": url, "duration_ms": duration_ms}


# ---------------------------------------------------------------------------
# 撤回 / 发送回执
# ---------------------------------------------------------------------------
class LwpResponseError(Exception):
    """WS lwp 请求-响应匹配过程中出现的业务级错误。"""

    def __init__(self, message: str, *, code: Any = None, body: Any = None, raw_response: Any = None, status: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.body = body
        self.raw_response = raw_response
        self.status = status


class LwpTimeout(LwpResponseError):
    """WS lwp 响应等待超时。"""


@dataclass
class SentMessageReceipt:
    cid: str
    messageId: str
    uuid: str
    status_code: Optional[int]
    raw: Any
    parse_path: str
    mid: str
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def __bool__(self) -> bool:
        return bool(self.messageId)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key, None)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class RecallResult:
    success: bool
    status: Literal["success", "timeout", "not_mine", "rate_limit", "unknown_error"]
    code: Any = None
    reason: Optional[str] = None
    raw: Any = None


