from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.local_toxic_model import ai_check_to_response
from app.models import AudioCheckRequest, CheckResponse, TextCheckRequest
from app.moderation import moderate_text

load_dotenv()

app = FastAPI(title="safecomms API", version="2.2.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse("index.html")


@app.post("/check/text", response_model=CheckResponse)
def check_text(payload: TextCheckRequest) -> CheckResponse:
    safe, category, matched_terms, reason = moderate_text(payload.text)
    return CheckResponse(safe=safe, category=category, matched_terms=matched_terms, reason=reason)


@app.post("/check/audio", response_model=CheckResponse)
def check_audio(payload: AudioCheckRequest) -> CheckResponse:
    safe, category, matched_terms, reason = moderate_text(payload.transcript)
    return CheckResponse(safe=safe, category=category, matched_terms=matched_terms, reason=reason)


@app.post("/check/text-ai", response_model=CheckResponse)
def check_text_ai(payload: TextCheckRequest, threshold: float = Query(default=0.5, ge=0.0, le=1.0)) -> CheckResponse:
    try:
        return ai_check_to_response(payload.text, threshold=threshold)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local text model unavailable: {exc}",
        ) from exc
