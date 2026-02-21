from __future__ import annotations

import os
from dataclasses import dataclass

from app.models import CheckResponse


@dataclass
class ToxicResult:
    label: str
    score: float


class LocalToxicModel:
    def __init__(self, model_dir: str | None = None) -> None:
        self.model_dir = model_dir or os.getenv("LOCAL_TOXIC_MODEL_DIR", "models/martin-ha-toxic-comment-model")
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, TextClassificationPipeline
        except Exception as exc:
            raise RuntimeError("Missing optional dependencies. Install requirements-ai.txt") from exc

        tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(self.model_dir, local_files_only=True)
        self._pipeline = TextClassificationPipeline(model=model, tokenizer=tokenizer)

    def classify(self, text: str) -> ToxicResult:
        self._load()
        result = self._pipeline(text, truncation=True)[0]
        return ToxicResult(label=str(result.get("label", "")).upper(), score=float(result.get("score", 0.0)))


def ai_check_to_response(text: str, threshold: float = 0.5) -> CheckResponse:
    model = LocalToxicModel()
    out = model.classify(text)
    is_toxic = out.label in {"TOXIC", "LABEL_1", "1"} and out.score >= threshold

    if is_toxic:
        return CheckResponse(
            safe=False,
            category="toxicity_ai",
            matched_terms=[],
            reason=f"Local AI toxic score={out.score:.3f} (label={out.label}, threshold={threshold:.2f})",
        )

    return CheckResponse(
        safe=True,
        category="clean",
        matched_terms=[],
        reason=f"Local AI non-toxic score={out.score:.3f} (label={out.label}, threshold={threshold:.2f})",
    )
