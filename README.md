# safecomms moderation API

Clean local moderation API with English-only docs and UI.
It supports text checks and audio-transcript checks.

## Features

- `POST /check/text`: keyword-based moderation
- Term lists are stored in `app/data/moderation_terms.json`
- `POST /check/audio`: keyword-based moderation for transcripts
- `POST /check/text-ai`: local text classification model

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Optional local model

Install optional model dependencies:

```bash
pip install -r requirements-ai.txt
```

Download local text model:

```bash
python scripts/download_martin_ha_model.py
```

## API examples

Text check:

```bash
curl -s -X POST localhost:8000/check/text \
  -H 'content-type: application/json' \
  -d '{"text":"I will kill you"}'
```

Audio transcript check:

```bash
curl -s -X POST localhost:8000/check/audio \
  -H 'content-type: application/json' \
  -d '{"transcript":"hello and welcome"}'
```

Local text model check:

```bash
curl -s -X POST 'localhost:8000/check/text-ai?threshold=0.5' \
  -H 'content-type: application/json' \
  -d '{"text":"you are stupid"}'
```

## Notes

- `/check/text-ai` returns `503` if local model files or optional dependencies are missing.
- Open `http://127.0.0.1:8000/` for the UI.

## Tests

```bash
pytest -q
```
