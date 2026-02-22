from pydantic import BaseModel, Field


class TextCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class AudioCheckRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=20000)


class CheckResponse(BaseModel):
    safe: bool
    category: str
    matched_terms: list[str]
    reason: str


class ErrorReportRequest(BaseModel):
    path: str = Field(default="/manual", min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=2000)


class ErrorResolveRequest(BaseModel):
    resolved_by: str = Field(default="admin", min_length=1, max_length=120)
