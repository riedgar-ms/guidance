from enum import StrEnum
import json
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class Role(StrEnum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"


class ContentType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    MULTIPLE = "multiple"


class TextContent(BaseModel):
    content_type: Literal[ContentType.TEXT]
    text: str


class AudioContent(BaseModel):
    content_type: Literal[ContentType.AUDIO]
    audio: bytes
    mime_type: str


class ImageContent(BaseModel):
    content_type: Literal[ContentType.IMAGE]
    image: bytes
    mime_type: str


class MultipleContent(BaseModel):
    content_type: Literal[ContentType.MULTIPLE]
    contents: list[Union["TextContent", "AudioContent", "ImageContent"]]


Content = Annotated[
    Union[TextContent, AudioContent, ImageContent, MultipleContent], Field(discriminator="content_type")
]


class Turn(BaseModel):
    role: Role
    content: Content


class Conversation(BaseModel):
    turns: list[Turn] = Field(default_factory=list)


class ConstraintType(StrEnum):
    JSON_SCHEMA = "json_schema"
    LARK = "lark"


class JSONSchemaConstraint(BaseModel):
    constraint_type: Literal[ConstraintType.JSON_SCHEMA]
    json_schema: dict[str, Any]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class LarkConstraint(BaseModel):
    constraint_type: Literal[ConstraintType.LARK]
    lark_schema: str


Constraint = Annotated[Union[JSONSchemaConstraint, LarkConstraint], Field(discriminator="constraint_type")]


class ModelRequestParameters(BaseModel):
    temperature: float | None = None
    top_k: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    model_config = ConfigDict(extra="allow")


class UserRequest(BaseModel):
    input: list[Content] = Field(default_factory=list)
    constraint: Constraint | None = None
    model_parameters: ModelRequestParameters | None = None


print(json.dumps(UserRequest.model_json_schema(), indent=4))


class ModelResponse(BaseModel):
    output: list[Content] = Field(default_factory=list)
    captures: dict[str, Union[TextContent, AudioContent, ImageContent]] = Field(default_factory=dict)


print(json.dumps(ModelResponse.model_json_schema(), indent=4))
