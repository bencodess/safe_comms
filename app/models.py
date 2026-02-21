from pydantic import BaseModel, Field


class TextCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class ImageCheckRequest(BaseModel):
    description: str = Field(min_length=1, max_length=5000)


class AudioCheckRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=20000)


class CheckResponse(BaseModel):
    safe: bool
    category: str
    matched_terms: list[str]
    reason: str
