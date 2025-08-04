from enum import StrEnum
import json
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class Role(StrEnum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"


class ContentType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIPLE = "multiple"


class TextContent(BaseModel):
    content_type: Literal[ContentType.TEXT]
    text: str


class ImageContent(BaseModel):
    content_type: Literal[ContentType.IMAGE]
    image: bytes
    mime_type: str


class MultipleContent(BaseModel):
    content_type: Literal[ContentType.MULTIPLE]
    contents: list[Union["TextContent", "ImageContent"]]


Content = Annotated[Union[TextContent, ImageContent, MultipleContent], Field(discriminator="content_type")]


class Turn(BaseModel):
    role: Role
    content: Content
