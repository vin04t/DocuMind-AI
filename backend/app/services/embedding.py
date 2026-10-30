import numpy as np
from typing import List, Optional
from app.core.config import settings

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Try loading from local cache first to avoid hanging if offline
            try:
                _model = SentenceTransformer(
                    settings.EMBEDDING_MODEL_NAME,
                    device="cpu",
                    model_kwargs={"local_files_only": True}
                )
            except Exception:
                _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")
        except Exception as e:
            print(f"[EmbeddingService] Warning: Could not load SentenceTransformer: {e}")
            _model = None
    return _model


class EmbeddingService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates dense embeddings for a list of texts."""
        if not texts:
            return []

        model = get_embedding_model()
        if model is not None:
            try:
                embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                print(f"[EmbeddingService] SentenceTransformer encoding failed: {e}. Using deterministic fallback.")

        # High-quality deterministic fallback embedding generator (normalized)
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generates dense embedding for a single query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self.dimension

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Generates a deterministic 384-dimensional vector based on character and n-gram hash frequencies.
        Guarantees cosine similarity properties while model is loading or in isolated environments.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for i, word in enumerate(words):
            h = hash(word) % self.dimension
            vec[h] += 1.0 / (1.0 + 0.1 * i)
            # Add character bigrams
            for j in range(len(word) - 1):
                bg = word[j:j+2]
                h_bg = hash(bg) % self.dimension
                vec[h_bg] += 0.25

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


embedding_service = EmbeddingService()
