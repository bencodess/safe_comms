# SafeComms Moderation API

Local-first moderation API with:

- text moderation
- audio moderation
- optional local AI text scoring
- health monitoring dashboard
- password-protected admin panel

## Highlights

- FastAPI backend with JSON API endpoints
- Large moderation term list loaded from `app/data/moderation_terms.json`
- `/health` dashboard with uptime, downtime, response-time probes, and reported errors
- `/admin` workflow to report, resolve, and delete errors
- Optional local Hugging Face model for `/check/text-ai`

## Quick Start

### Option 1: One command setup + run

```bash
./src/start.sh
```

### Option 2: Manual setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Open in browser:

- App: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Admin: `http://127.0.0.1:8000/admin`

## Configuration

Create `.env` from `.env.example` and set values:

```env
ADMIN_PASSWORD=example123
LOCAL_TOXIC_MODEL_DIR=models/martin-ha-toxic-comment-model
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Main moderation UI |
| `/check/text` | `POST` | Rule-based text moderation |
| `/check/audio` | `POST` | Rule-based audio moderation |
| `/check/text-ai` | `POST` | Local model text moderation |
| `/health` | `GET` | Health dashboard page |
| `/health/status` | `GET` | Health status JSON |
| `/health/metrics` | `GET` | Health metrics JSON |
| `/admin-verify` | `GET, POST` | Admin login page and verify action |
| `/admin` | `GET` | Admin dashboard (session-based) |
| `/admin/api/errors` | `GET` | List error reports |
| `/admin/api/errors/report` | `POST` | Add manual error report |
| `/admin/api/errors/{id}/resolve` | `POST` | Mark error resolved |
| `/admin/api/errors/{id}` | `DELETE` | Delete error report |

## Request Examples

Text check:

```bash
curl -s -X POST http://127.0.0.1:8000/check/text \
  -H "content-type: application/json" \
  -d '{"text":"I will kill you"}'
```

Audio check:

```bash
curl -s -X POST http://127.0.0.1:8000/check/audio \
  -H "content-type: application/json" \
  -d '{"transcript":"hello and welcome"}'
```

Local AI text check:

```bash
curl -s -X POST "http://127.0.0.1:8000/check/text-ai?threshold=0.5" \
  -H "content-type: application/json" \
  -d '{"text":"you are stupid"}'
```

## Optional Local AI Model

Install AI dependencies:

```bash
pip install -r requirements-ai.txt
```

Download model files locally:

```bash
python src/scripts/download_martin_ha_model.py
```

## Keepalive Mode

Run API with auto-restart loop:

```bash
./src/keepalive.sh
```

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Project Layout

| Path | Purpose |
|---|---|
| `main.py` | FastAPI app and routes |
| `app/moderation.py` | Rule-based moderation engine |
| `app/data/moderation_terms.json` | Moderation term database |
| `app/local_toxic_model.py` | Local AI model wrapper |
| `app/admin_store.py` | SQLite admin error store |
| `public/` | Frontend pages (`index`, `health`, `admin`) |
| `src/start.sh` | Setup and start script |
| `src/keepalive.sh` | Auto-restart launcher |
| `src/scripts/download_martin_ha_model.py` | Local model downloader |
| `tests/` | API tests |

## Dependencies

- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- Optional: transformers, torch

## Credits

- bencodess
