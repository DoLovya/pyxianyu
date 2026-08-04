from __future__ import annotations

from typing import Literal, Union

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

