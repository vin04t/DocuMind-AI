from typing import List, Dict, Any
from app.core.config import settings

_cross_encoder = None


def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder(settings.CROSS_ENCODER_MODEL_NAME, device="cpu")
        except Exception as e:
            print(f"[RerankerService] Warning: CrossEncoder not loaded: {e}")
            _cross_encoder = None
    return _cross_encoder


class RerankerService:
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunks against a query using a Cross-Encoder.
        """
        if not candidates:
            return []

        model = get_cross_encoder()
        if model is None:
            return candidates

        try:
            pairs = [[query, c["content"]] for c in candidates]
            scores = model.predict(pairs)
            
            for idx, score in enumerate(scores):
                candidates[idx]["cross_encoder_score"] = float(score)

            # Sort by cross encoder score descending
            candidates.sort(key=lambda x: x.get("cross_encoder_score", 0.0), reverse=True)
            return candidates
        except Exception as e:
            print(f"[RerankerService] Reranking execution failed: {e}")
            return candidates


reranker_service = RerankerService()
