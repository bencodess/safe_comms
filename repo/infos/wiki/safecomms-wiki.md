# SafeComms Wiki

## 1. Overview

SafeComms is a local-first moderation platform built with FastAPI.
It provides:

- Rule-based moderation for text
- Rule-based moderation for audio transcripts
- Optional local AI moderation for text (`/check/text-ai`)
- Health monitoring with uptime/downtime and response-time probes
- Password-protected admin workflow for error management

Core principles:

- Local operation first
- Minimal external dependencies at runtime
- Transparent moderation decisions (`reason`, `matched_terms`, `category`)

## 2. Architecture

### Backend

- Framework: FastAPI (`main.py`)
- Data validation: Pydantic models (`app/models.py`)
- Rule-based moderation engine: `app/moderation.py`
- Optional AI text model wrapper: `app/local_toxic_model.py`
- Admin error persistence: SQLite via `app/admin_store.py`

### Frontend

Static pages live in `public/`:

- `public/index.html`: moderation UI
- `public/health.html`: health dashboard
- `public/admin_verify.html`: admin login page
- `public/admin.html`: admin dashboard

### Scripts

- `src/start.sh`: install + bootstrap + run server
- `src/keepalive.sh`: restart loop if server exits
- `src/scripts/download_martin_ha_model.py`: local AI model download

### Storage

- `safecomms.db`: moderation-related local db (if used by your setup)
- `safecomms_admin.db`: admin error reports

## 3. Repository Structure

```text
safe_comms/
├── app/
│   ├── data/moderation_terms.json
│   ├── admin_store.py
│   ├── local_toxic_model.py
│   ├── moderation.py
│   └── models.py
├── public/
│   ├── admin.html
│   ├── admin_verify.html
│   ├── health.html
│   └── index.html
├── src/
│   ├── keepalive.sh
│   ├── start.sh
│   └── scripts/download_martin_ha_model.py
├── tests/
├── main.py
├── requirements.txt
├── requirements-ai.txt
└── .env.example
```

## 4. Setup and Startup

### Prerequisites

- Python 3.10+
- `pip`
- Linux/macOS shell for the provided scripts

### Quick startup

```bash
./src/start.sh
```

### Manual startup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Server URL:

- `http://127.0.0.1:8000`

## 5. Configuration

Configure via `.env`:

```env
ADMIN_PASSWORD=change-me
ADMIN_DB_PATH=safecomms_admin.db
ADMIN_SESSION_TTL_SECONDS=43200
LOCAL_TOXIC_MODEL_DIR=models/martin-ha-toxic-comment-model
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

Notes:

- `.env` should stay local and never be committed.
- `.env.example` is the safe template for the repository.

## 6. API Reference

### `GET /`
Returns the main moderation UI page.

### `POST /check/text`
Checks text against the rule-based moderation set.

Request:

```json
{ "text": "example text" }
```

Response example:

```json
{
  "safe": false,
  "category": "violence",
  "matched_terms": ["kill"],
  "reason": "Matched prohibited terms"
}
```

### `POST /check/audio`
Checks transcript text with the same moderation logic.

Request:

```json
{ "transcript": "example transcript" }
```

### `POST /check/text-ai?threshold=0.5`
Uses the optional local AI text model.

Request:

```json
{ "text": "example text" }
```

Behavior:

- Returns a moderation decision if local model is available.
- Returns `503` if the model is unavailable locally.

### `GET /health`
Returns the HTML health dashboard.

### `GET /health/status`
Basic status endpoint.

### `GET /health/metrics`
Returns health metrics including:

- Uptime and steady uptime
- Downtime approximation based on failed probes
- Probe counts and availability percentage
- Last response-time measurement
- Recent reported errors

## 7. Admin Workflow

### Pages

- `GET /admin-verify`: login page
- `GET /admin`: admin dashboard (requires valid session cookie)

### Login flow

1. Open `/admin`
2. Redirects to `/admin-verify` if no valid session
3. Submit password to `POST /admin-verify`
4. Server sets `admin_session` cookie
5. Redirect to `/admin`

### Admin API

- `GET /admin/api/errors`: list reports
- `POST /admin/api/errors/report`: create report
- `POST /admin/api/errors/{id}/resolve`: resolve report
- `DELETE /admin/api/errors/{id}`: delete report manually
- `POST /admin/logout`: clear session cookie

## 8. Health Monitoring Model

The service runs an internal probe loop (default every 300 seconds).
Each probe executes a minimal moderation call and records:

- Success/failure
- Response time in milliseconds
- Last error message (if probe fails)

Runtime `5xx` responses and unhandled exceptions are also written to:

- In-memory health state
- Admin error storage (`safecomms_admin.db`)

## 9. Keepalive Operation

For auto-restart behavior:

```bash
./src/keepalive.sh
```

Behavior:

- Runs `./src/start.sh`
- If process exits, logs exit code
- Waits 3 seconds
- Restarts automatically

## 10. Local AI Mode

Install optional AI dependencies:

```bash
pip install -r requirements-ai.txt
```

Download model files:

```bash
python src/scripts/download_martin_ha_model.py
```

Recommended for offline use:

- Keep `HF_HUB_OFFLINE=1`
- Keep `TRANSFORMERS_OFFLINE=1`
- Ensure model files are present in `LOCAL_TOXIC_MODEL_DIR`

## 11. Testing

Run test suite:

```bash
.venv/bin/python -m pytest -q
```

Typical coverage in this project includes:

- Main routes availability
- Moderation behavior (safe/unsafe)
- Admin verify/session flow
- Error report lifecycle (report/resolve/delete)
- Health routes and metrics payloads

## 12. Troubleshooting

### NetworkError in browser UI

- Verify server is running on `127.0.0.1:8000`
- Verify UI base URL is correct
- Check browser console for failed request path

### `pip install requirements-ai.txt` fails

Use:

```bash
pip install -r requirements-ai.txt
```

### AI endpoint returns `503 Local text model unavailable`

- Confirm model directory exists
- Confirm local model files are complete
- Confirm offline env vars match your intent

### Admin page redirects repeatedly

- Ensure `ADMIN_PASSWORD` is set in `.env`
- Re-login via `/admin-verify`
- Clear stale cookies and retry

## 13. Security Notes

- Keep `.env` out of git
- Use a strong `ADMIN_PASSWORD`
- Use HTTPS and secure cookie settings when deployed publicly
- Do not expose development mode (`--reload`) in production

## 14. Maintainers

Credits: `bencodess`
