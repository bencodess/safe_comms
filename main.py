import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
import os
from pathlib import Path
from threading import Lock
from time import perf_counter
import secrets

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.admin_store import AdminStore
from app.local_toxic_model import ai_check_to_response
from app.models import AudioCheckRequest, CheckResponse, ErrorReportRequest, ErrorResolveRequest, TextCheckRequest
from app.moderation import moderate_text

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_DB_PATH = os.getenv("ADMIN_DB_PATH", "safecomms_admin.db")
ADMIN_SESSION_TTL_SECONDS = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", "43200"))
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_PATH_PREFIXES = tuple(
    p.strip() for p in os.getenv("RATE_LIMIT_PATH_PREFIXES", "/check").split(",") if p.strip()
)
admin_store = AdminStore(ADMIN_DB_PATH)


class HealthState:
    def __init__(self, probe_interval_seconds: int = 300, max_errors: int = 200) -> None:
        self.probe_interval_seconds = probe_interval_seconds
        self.max_errors = max_errors
        self.started_at = datetime.now(timezone.utc)
        self.last_probe_at: datetime | None = None
        self.last_probe_success: bool | None = None
        self.last_probe_error: str | None = None
        self.last_response_ms: float | None = None
        self.total_probes = 0
        self.failed_probes = 0
        self.last_failure_at: datetime | None = None
        self.errors: list[dict[str, str]] = []
        self._lock = Lock()

    def record_probe(self, success: bool, response_ms: float, error: str | None = None) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self.last_probe_at = now
            self.last_probe_success = success
            self.last_response_ms = round(response_ms, 2)
            self.last_probe_error = error
            self.total_probes += 1
            if not success:
                self.failed_probes += 1
                self.last_failure_at = now

    def record_error(self, path: str, error: str) -> None:
        entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "path": path,
            "error": error,
        }
        with self._lock:
            self.errors.append(entry)
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[-self.max_errors :]

    def snapshot(self) -> dict:
        now = datetime.now(timezone.utc)
        with self._lock:
            uptime_seconds = max(0.0, (now - self.started_at).total_seconds())
            downtime_seconds = float(self.failed_probes * self.probe_interval_seconds)
            if self.last_failure_at is None:
                steady_uptime_seconds = uptime_seconds
            else:
                steady_uptime_seconds = max(0.0, (now - self.last_failure_at).total_seconds())

            availability = 100.0
            if self.total_probes > 0:
                availability = (1.0 - (self.failed_probes / self.total_probes)) * 100.0

            return {
                "started_at": self.started_at.isoformat(),
                "now": now.isoformat(),
                "probe_interval_seconds": self.probe_interval_seconds,
                "uptime_seconds": round(uptime_seconds, 2),
                "steady_uptime_seconds": round(steady_uptime_seconds, 2),
                "downtime_seconds": round(downtime_seconds, 2),
                "total_probes": self.total_probes,
                "failed_probes": self.failed_probes,
                "availability_percent": round(availability, 4),
                "last_probe_at": self.last_probe_at.isoformat() if self.last_probe_at else None,
                "last_probe_success": self.last_probe_success,
                "last_probe_error": self.last_probe_error,
                "last_response_ms": self.last_response_ms,
                "reported_error_count": len(self.errors),
                "recent_errors": list(self.errors[-50:]),
            }


class RateLimiter:
    def __init__(
        self,
        enabled: bool,
        max_requests: int,
        window_seconds: int,
        path_prefixes: tuple[str, ...],
    ) -> None:
        self.enabled = enabled
        self.max_requests = max(1, max_requests)
        self.window_seconds = max(1, window_seconds)
        self.path_prefixes = path_prefixes
        self._lock = Lock()
        self._buckets: dict[str, tuple[float, int]] = {}

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()

    def should_limit_path(self, path: str) -> bool:
        if not self.path_prefixes:
            return False
        return any(path.startswith(prefix) for prefix in self.path_prefixes)

    def check_and_consume(self, key: str, now_ts: float) -> tuple[bool, float]:
        with self._lock:
            window_start, count = self._buckets.get(key, (now_ts, 0))
            elapsed = now_ts - window_start
            if elapsed >= self.window_seconds:
                window_start, count = now_ts, 0
            if count >= self.max_requests:
                retry_after = max(1.0, self.window_seconds - (now_ts - window_start))
                return False, retry_after
            self._buckets[key] = (window_start, count + 1)
            return True, 0.0


def get_health_state() -> HealthState:
    state = getattr(app.state, "health_state", None)
    if state is None:
        state = HealthState(probe_interval_seconds=300)
        app.state.health_state = state
    return state


def get_admin_sessions() -> dict[str, float]:
    sessions = getattr(app.state, "admin_sessions", None)
    if sessions is None:
        sessions = {}
        app.state.admin_sessions = sessions
    return sessions


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _is_valid_admin_session(token: str | None) -> bool:
    if not token:
        return False
    sessions = get_admin_sessions()
    exp = sessions.get(token)
    if exp is None:
        return False
    if exp < _now_ts():
        sessions.pop(token, None)
        return False
    return True


def require_admin_session(admin_session: str | None = Cookie(default=None)) -> None:
    if not _is_valid_admin_session(admin_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin session required")


async def _run_probe_loop(health_state: HealthState) -> None:
    while True:
        start = perf_counter()
        success = True
        err: str | None = None
        try:
            moderate_text("health probe")
        except Exception as exc:
            success = False
            err = str(exc)
        duration_ms = (perf_counter() - start) * 1000.0
        health_state.record_probe(success=success, response_ms=duration_ms, error=err)
        await asyncio.sleep(health_state.probe_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    health_state = get_health_state()
    _ = get_admin_sessions()
    probe_task = asyncio.create_task(_run_probe_loop(health_state))
    try:
        yield
    finally:
        probe_task.cancel()
        with suppress(asyncio.CancelledError):
            await probe_task


app = FastAPI(title="safecomms API", version="2.6.0", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=PUBLIC_DIR / "assets"), name="assets")
rate_limiter = RateLimiter(
    enabled=RATE_LIMIT_ENABLED,
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    path_prefixes=RATE_LIMIT_PATH_PREFIXES,
)


def _request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    if not rate_limiter.enabled or not rate_limiter.should_limit_path(request.url.path):
        return await call_next(request)

    now_ts = _now_ts()
    key = f"{_request_ip(request)}:{request.url.path}"
    allowed, retry_after = rate_limiter.check_and_consume(key, now_ts)
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "rate limit exceeded"},
            headers={"Retry-After": str(int(retry_after))},
        )
    return await call_next(request)


@app.middleware("http")
async def report_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            get_health_state().record_error(request.url.path, f"http_{response.status_code}")
            admin_store.report_error("runtime", request.url.path, f"http_{response.status_code}")
        return response
    except Exception as exc:
        get_health_state().record_error(request.url.path, str(exc))
        admin_store.report_error("runtime", request.url.path, str(exc))
        raise


@app.get("/health")
def health_dashboard() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "health.html")


@app.get("/health/status")
def health_status() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/health/metrics")
def health_metrics() -> dict:
    out = get_health_state().snapshot()
    reports = admin_store.list_error_reports(include_resolved=True)
    out["reported_error_count"] = len(reports)
    out["recent_errors"] = [
        {
            "time": r["created_at"],
            "path": r["path"],
            "error": f"{r['source']}: {r['message']}" + (" [resolved]" if r.get("resolved_at") else ""),
        }
        for r in reports[:50]
    ]
    return out


@app.get("/admin-verify")
def admin_verify_page() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "admin_verify.html")


@app.post("/admin-verify")
def admin_verify(password: str = Form(...)):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="admin password not configured")

    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin password")

    token = secrets.token_urlsafe(32)
    get_admin_sessions()[token] = _now_ts() + ADMIN_SESSION_TTL_SECONDS

    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="admin_session",
        value=token,
        max_age=ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/admin/logout")
def admin_logout():
    response = RedirectResponse(url="/admin-verify", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_session")
    return response


@app.get("/admin")
def admin_dashboard(admin_session: str | None = Cookie(default=None)):
    if not _is_valid_admin_session(admin_session):
        return RedirectResponse(url="/admin-verify", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse(PUBLIC_DIR / "admin.html")


@app.get("/admin/api/errors")
def admin_list_errors(
    include_resolved: bool = Query(default=True),
    _: None = Depends(require_admin_session),
) -> dict:
    return {"errors": admin_store.list_error_reports(include_resolved=include_resolved)}


@app.post("/admin/api/errors/report")
def admin_report_error(payload: ErrorReportRequest, _: None = Depends(require_admin_session)) -> dict:
    row = admin_store.report_error("manual", payload.path, payload.message)
    return row


@app.post("/admin/api/errors/{report_id}/resolve")
def admin_resolve_error(
    report_id: int,
    payload: ErrorResolveRequest,
    _: None = Depends(require_admin_session),
) -> dict:
    ok = admin_store.resolve_error(report_id, payload.resolved_by)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="error report not found or already resolved")
    return {"status": "resolved", "report_id": report_id}


@app.delete("/admin/api/errors/{report_id}")
def admin_delete_error(report_id: int, _: None = Depends(require_admin_session)) -> dict:
    ok = admin_store.delete_error(report_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="error report not found")
    return {"status": "deleted", "report_id": report_id}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "index.html")


@app.post("/check/text", response_model=CheckResponse)
def check_text(payload: TextCheckRequest) -> CheckResponse:
    safe, category, matched_terms, reason = moderate_text(payload.text)
    return CheckResponse(safe=safe, category=category, matched_terms=matched_terms, reason=reason)


@app.post("/check/audio", response_model=CheckResponse)
def check_audio(payload: AudioCheckRequest) -> CheckResponse:
    safe, category, matched_terms, reason = moderate_text(payload.transcript)
    return CheckResponse(safe=safe, category=category, matched_terms=matched_terms, reason=reason)


@app.post("/check/text-ai", response_model=CheckResponse)
def check_text_ai(
    payload: TextCheckRequest,
    threshold: float = Query(default=0.5, ge=0.0, le=1.0),
) -> CheckResponse:
    try:
        return ai_check_to_response(payload.text, threshold=threshold)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local text model unavailable: {exc}",
        ) from exc
