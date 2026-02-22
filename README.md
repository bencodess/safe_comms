# SafeComms Moderation API

Local-first moderation API with a web UI, health dashboard, and password-protected admin panel.

## Stats

![Top Language](https://img.shields.io/github/languages/top/bencodess/safe_comms?style=for-the-badge)
![Language Count](https://img.shields.io/github/languages/count/bencodess/safe_comms?style=for-the-badge)
![Repo Size](https://img.shields.io/github/repo-size/bencodess/safe_comms?style=for-the-badge)

## What It Does

- Moderates text via large local term lists
- Moderates audio transcripts via the same moderation engine
- Optionally runs local text-model classification (`/check/text-ai`)
- Tracks health metrics (uptime, downtime, response probe time)
- Supports admin workflows for error management

## Core Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | `GET` | Main moderation UI |
| `/check/text` | `POST` | Text moderation |
| `/check/audio` | `POST` | Transcript moderation |
| `/check/text-ai` | `POST` | Local model-based text check |
| `/health` | `GET` | Health dashboard page |
| `/health/status` | `GET` | Health status JSON |
| `/health/metrics` | `GET` | Health metrics JSON |
| `/admin` | `GET` | Admin panel (session protected) |
| `/admin-verify` | `GET/POST` | Admin password verification |

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Open:

- App: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Admin: `http://127.0.0.1:8000/admin`

Project structure:

- `public/` contains all HTML pages
- `src/` contains startup and utility scripts

## Configuration

Edit `.env`:

```env
ADMIN_PASSWORD=example123
LOCAL_TOXIC_MODEL_DIR=models/martin-ha-toxic-comment-model
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

Moderation terms live in:

- `app/data/moderation_terms.json`

## Admin Flow

1. Visit `/admin`
2. You are redirected to `/admin-verify`
3. Enter `ADMIN_PASSWORD`
4. You are redirected back to `/admin` with an admin session cookie

From the admin panel you can:

- report errors
- resolve errors
- delete errors

## Optional Local Text Model

Install optional dependencies:

```bash
pip install -r requirements-ai.txt
```

Download model locally:

```bash
python src/scripts/download_martin_ha_model.py
```

Start with installer script:

```bash
./src/start.sh
```

Keepalive mode:

```bash
./src/keepalive.sh
```

## Request Examples

### Text moderation

```bash
curl -s -X POST http://127.0.0.1:8000/check/text \
  -H 'content-type: application/json' \
  -d '{"text":"I will kill you"}'
```

### Audio transcript moderation

```bash
curl -s -X POST http://127.0.0.1:8000/check/audio \
  -H 'content-type: application/json' \
  -d '{"transcript":"hello and welcome"}'
```

### Local model text check

```bash
curl -s -X POST 'http://127.0.0.1:8000/check/text-ai?threshold=0.5' \
  -H 'content-type: application/json' \
  -d '{"text":"you are stupid"}'
```

## Tests

```bash
pytest -q
```

## Dependencies

- FastAPI
- Uvicorn
- Pydantic
- Hugging Face Transformers
- PyTorch

## Credits

- bencodess

## Contributors

- Ben
