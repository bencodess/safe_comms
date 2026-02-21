# safecomms moderation API

Einfache SafeComms-API ohne Auth und ohne Secrets.
Sie prueft Text/Bildbeschreibung/Audio-Transcript mit Wortliste,
und optional lokal mit einem heruntergeladenen Hugging Face Modell.

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Optional: martin-ha lokal herunterladen (keine Inference-API)

```bash
source .venv/bin/activate
pip install -r requirements-ai.txt
python scripts/download_martin_ha_model.py
```

Das Modell landet lokal in:
- `models/martin-ha-toxic-comment-model`

## Endpunkte

- `GET /` -> Web-UI
- `GET /health`
- `POST /check/text`
- `POST /check/image`
- `POST /check/audio`
- `POST /check/text-ai` (nutzt nur lokales Modell, falls vorhanden)

## AI-Check Beispiel (lokal)

```bash
curl -s -X POST 'localhost:8000/check/text-ai?threshold=0.5' \
  -H 'content-type: application/json' \
  -d '{"text":"you are stupid"}'
```

Wenn Modell oder AI-Dependencies fehlen, antwortet der Endpoint mit `503`.

## Tests

```bash
pytest -q
```
