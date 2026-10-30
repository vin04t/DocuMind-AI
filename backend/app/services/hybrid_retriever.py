import time
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.bm25_retriever import bm25_retriever


class HybridRetrieverService:
    def __init__(self, rrf_k: Optional[int] = None):
        self.rrf_k = rrf_k or settings.RRF_K

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_id: Optional[str] = None,
        enable_reranker: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval:
        1. Dense Vector Search (ChromaDB + SentenceTransformers)
        2. Sparse Keyword Search (BM25Okapi)
        3. Reciprocal Rank Fusion (RRF)
        4. Optional Cross-Encoder reranking
        """
        start_time = time.time()
        k = top_k or settings.TOP_K_RETRIEVAL
        candidate_k = max(k * 3, 15)

        # 1. Dense Semantic Retrieval
        dense_start = time.time()
        query_embedding = embedding_service.embed_query(query)
        dense_results = vector_store.query_similar(
            query_embedding=query_embedding,
            top_k=candidate_k,
            document_id=document_id
        )
        dense_time = (time.time() - dense_start) * 1000

        # 2. Sparse BM25 Retrieval
        sparse_start = time.time()
        sparse_results = bm25_retriever.search(
            query=query,
            top_k=candidate_k,
            document_id=document_id
        )
        sparse_time = (time.time() - sparse_start) * 1000

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}

        for item in dense_results:
            cid = item["id"]
            dense_ranks[cid] = item["rank"]
            chunk_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + item["rank"]))

        for item in sparse_results:
            cid = item["id"]
            sparse_ranks[cid] = item["rank"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + item["rank"]))

        # Sort all candidates by RRF score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        fused_results = []
        max_rrf = sorted_candidates[0][1] if sorted_candidates else 1.0

        for cid, score in sorted_candidates[:candidate_k]:
            chunk_info = chunk_map[cid]
            # Normalized score relative to max RRF
            norm_score = round(score / max_rrf, 4) if max_rrf > 0 else 0.0
            fused_results.append({
                "id": cid,
                "content": chunk_info["content"],
                "document_id": chunk_info.get("document_id"),
                "page_number": chunk_info.get("page_number"),
                "chunk_index": chunk_info.get("chunk_index"),
                "rrf_score": round(score, 6),
                "confidence_score": norm_score,
                "dense_rank": dense_ranks.get(cid, None),
                "sparse_rank": sparse_ranks.get(cid, None),
                "in_dense": cid in dense_ranks,
                "in_sparse": cid in sparse_ranks
            })

        # 4. Optional Cross-Encoder Reranking
        should_rerank = enable_reranker if enable_reranker is not None else settings.ENABLE_CROSS_ENCODER
        rerank_time = 0.0

        if should_rerank and fused_results:
            from app.services.reranker import reranker_service
            rerank_start = time.time()
            fused_results = reranker_service.rerank(query, fused_results)
            rerank_time = (time.time() - rerank_start) * 1000

        final_top_k = fused_results[:k]
        total_latency_ms = (time.time() - start_time) * 1000

        return {
            "results": final_top_k,
            "total_candidates": len(sorted_candidates),
            "dense_count": len(dense_results),
            "sparse_count": len(sparse_results),
            "latency_ms": round(total_latency_ms, 2),
            "dense_latency_ms": round(dense_time, 2),
            "sparse_latency_ms": round(sparse_time, 2),
            "rerank_latency_ms": round(rerank_time, 2)
        }


hybrid_retriever = HybridRetrieverService()
