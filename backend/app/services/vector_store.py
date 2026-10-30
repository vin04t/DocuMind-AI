import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from app.core.config import settings


class VectorStoreService:
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = os.path.abspath(persist_dir or settings.CHROMA_PERSIST_DIR)
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Cosine distance collection
        self.collection = self.client.get_or_create_collection(
            name="documind_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """
        Adds document chunks and precomputed embeddings to ChromaDB.
        """
        if not chunks:
            return

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [
            {
                "document_id": str(chunk["document_id"]),
                "page_number": int(chunk["page_number"]),
                "chunk_index": int(chunk["chunk_index"]),
                "start_char": int(chunk.get("start_char", 0)),
                "end_char": int(chunk.get("end_char", 0)),
                "token_count": int(chunk.get("token_count", 0))
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query_similar(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for the most similar chunks.
        Returns sorted list of matches with distance, score, and metadata.
        """
        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        matches = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            count = len(results["ids"][0])
            for i in range(count):
                chunk_id = results["ids"][0][i]
                content = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # In cosine distance: similarity = 1 - distance
                similarity_score = max(0.0, 1.0 - distance)

                matches.append({
                    "id": chunk_id,
                    "content": content,
                    "document_id": meta.get("document_id"),
                    "page_number": meta.get("page_number"),
                    "chunk_index": meta.get("chunk_index"),
                    "distance": distance,
                    "similarity_score": similarity_score,
                    "rank": i + 1
                })

        return matches

    def delete_document(self, document_id: str) -> None:
        """Deletes all chunks belonging to a document from ChromaDB."""
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            print(f"[VectorStore] Error deleting document {document_id}: {e}")

    def count(self) -> int:
        return self.collection.count()


vector_store = VectorStoreService()
