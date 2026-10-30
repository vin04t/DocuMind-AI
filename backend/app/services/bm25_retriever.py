import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.core.config import settings


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text for BM25."""
    clean = re.sub(r'[^\w\s]', ' ', text.lower())
    return [word for word in clean.split() if len(word) > 1]


class BM25RetrieverService:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1 or settings.BM25_K1
        self.b = b or settings.BM25_B
        self.chunks: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def index_chunks(self, chunks: List[Dict[str, Any]], append: bool = False) -> None:
        """
        Indexes a list of chunks into BM25.
        Each chunk is expected to have 'id', 'content', 'document_id', 'page_number'.
        """
        if not append:
            self.chunks = list(chunks)
        else:
            # Avoid duplicate chunks
            existing_ids = {c["id"] for c in self.chunks}
            for c in chunks:
                if c["id"] not in existing_ids:
                    self.chunks.append(c)

        self.corpus_tokens = [tokenize(c["content"]) for c in self.chunks]
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens, k1=self.k1, b=self.b)
        else:
            self.bm25 = None

    def remove_document(self, document_id: str) -> None:
        """Removes all chunks of a document and rebuilds the BM25 index."""
        self.chunks = [c for c in self.chunks if str(c.get("document_id")) != str(document_id)]
        self.corpus_tokens = [tokenize(c["content"]) for c in self.chunks]
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens, k1=self.k1, b=self.b)
        else:
            self.bm25 = None

    def search(
        self,
        query: str,
        top_k: int = 10,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs BM25 keyword search.
        Returns ranked list of matching chunks with bm25 score and rank.
        """
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        doc_scores = self.bm25.get_scores(query_tokens)

        # Pair chunks with scores
        scored_results = []
        for idx, score in enumerate(doc_scores):
            chunk = self.chunks[idx]
            if document_id and str(chunk.get("document_id")) != str(document_id):
                continue
            if score > 0.0:
                scored_results.append({
                    "id": chunk["id"],
                    "content": chunk["content"],
                    "document_id": chunk.get("document_id"),
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index"),
                    "bm25_score": float(score)
                })

        # Sort descending by BM25 score
        scored_results.sort(key=lambda x: x["bm25_score"], reverse=True)

        # Assign ranks
        results = scored_results[:top_k]
        for rank_idx, item in enumerate(results):
            item["rank"] = rank_idx + 1

        return results


bm25_retriever = BM25RetrieverService()
