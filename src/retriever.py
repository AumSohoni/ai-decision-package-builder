from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import RiskCase, SimilarCase


class Retriever:
    def __init__(self, past_decisions_path: str | Path | None = None):
        if past_decisions_path is None:
            past_decisions_path = Path(__file__).parent.parent / "data" / "past_decisions.json"
        self.past_decisions_path = Path(past_decisions_path)
        with self.past_decisions_path.open("r", encoding="utf-8") as f:
            self.past_decisions = json.load(f)

    def _doc(self, case: dict) -> str:
        parts = [
            case.get("title", ""),
            case.get("description", ""),
            case.get("category", ""),
            case.get("outcome", ""),
            case.get("reasoning", ""),
        ]
        return " ".join(str(p) for p in parts).lower()

    def retrieve(self, risk_case: RiskCase | dict, top_k: int = 3) -> list[SimilarCase]:
        if isinstance(risk_case, RiskCase):
            query_case = risk_case.model_dump(exclude_none=True)
        else:
            query_case = dict(risk_case)

        query_doc = self._doc(query_case)
        corpus = [self._doc(c) for c in self.past_decisions]
        if not corpus:
            return []

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform([query_doc] + corpus)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        idxs = np.argsort(sims)[::-1][:top_k]

        results: list[SimilarCase] = []
        for i in idxs:
            c = self.past_decisions[i]
            results.append(
                SimilarCase(
                    id=c["id"],
                    title=c.get("title", ""),
                    category=c.get("category", ""),
                    severity=c.get("severity", ""),
                    outcome=c.get("outcome", ""),
                    reasoning=c.get("reasoning", ""),
                    score=float(sims[i]),
                )
            )
        return results
