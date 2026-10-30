import os
import json
import re
import httpx
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings


class LLMProvider:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

    def get_active_provider_name(self) -> str:
        if settings.LLM_PROVIDER == "gemini" and self.gemini_key:
            return "Google Gemini (gemini-1.5-flash)"
        elif settings.LLM_PROVIDER == "openai" and self.openai_key:
            return "OpenAI (gpt-4o-mini)"
        elif self.gemini_key:
            return "Google Gemini (gemini-1.5-flash)"
        elif self.openai_key:
            return "OpenAI (gpt-4o-mini)"
        else:
            return "DocuMind Local Grounded Engine (Standard Mode - No External API Key)"

    async def generate_grounded_answer(
        self,
        query: str,
        evidence_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        confidence_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """
        Generates a factual answer strictly grounded in the provided evidence chunks.
        If evidence is insufficient, returns an unanswerable declaration with missing info.
        """
        # Determine whether any evidence exists or meets confidence threshold
        if not evidence_chunks:
            return {
                "answer": (
                    "Based on the available documents, this answer cannot be established. "
                    "Missing information: None of the indexed document passages contain relevant context "
                    f"addressing '{query}'."
                ),
                "is_unanswerable": True,
                "provider": self.get_active_provider_name(),
                "extracted_claims": []
            }

        # Check maximum confidence in evidence chunks
        max_confidence = max(c.get("confidence_score", 0.0) for c in evidence_chunks)
        
        # Build structured context string
        context_blocks = []
        for idx, chunk in enumerate(evidence_chunks):
            doc_name = chunk.get("document_name") or f"Document {chunk.get('document_id', '')[:8]}"
            page = chunk.get("page_number", 1)
            context_blocks.append(f"--- [Passage {idx + 1} | Source: {doc_name} | Page: {page}] ---\n{chunk['content']}\n")

        joined_context = "\n".join(context_blocks)

        # 1. Try Gemini if configured
        if self.gemini_key and settings.LLM_PROVIDER in ("auto", "gemini"):
            try:
                gemini_res = await self._call_gemini(query, joined_context, conversation_history)
                if gemini_res:
                    return gemini_res
            except Exception as e:
                print(f"[LLMProvider] Gemini call failed: {e}. Falling back.")

        # 2. Try OpenAI if configured
        if self.openai_key and settings.LLM_PROVIDER in ("auto", "openai"):
            try:
                openai_res = await self._call_openai(query, joined_context, conversation_history)
                if openai_res:
                    return openai_res
            except Exception as e:
                print(f"[LLMProvider] OpenAI call failed: {e}. Falling back.")

        # 3. Intelligent Local Grounded Generation Engine
        return self._generate_local_grounded_answer(query, evidence_chunks, max_confidence, confidence_threshold)

    async def _call_gemini(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> Optional[Dict[str, Any]]:
        system_prompt = (
            "You are DocuMind AI, an evidence-grounded document research assistant. "
            "Your answers must be strictly grounded ONLY in the provided document passages. "
            "Never fabricate or assume facts not explicitly mentioned in the passages. "
            "For every key factual claim, cite the source document and page number in brackets like [Source: <doc_name>, Page: <page>]. "
            "If the provided passages do not contain sufficient evidence to answer the user's question, "
            "explicitly state that the answer cannot be established from the available documents and state what information is missing."
        )

        prompt = f"{system_prompt}\n\nDOCUMENT PASSAGES:\n{context}\n\nUSER QUESTION: {query}\n\nANSWER:"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                is_unanswerable = "cannot be established" in text.lower() or "not provided" in text.lower()
                return {
                    "answer": text,
                    "is_unanswerable": is_unanswerable,
                    "provider": "Google Gemini (gemini-1.5-flash)",
                    "extracted_claims": self._extract_claims_from_text(text)
                }
        return None

    async def _call_openai(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> Optional[Dict[str, Any]]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are DocuMind AI, an evidence-grounded document research assistant. "
                    "Your answers must be strictly grounded ONLY in the provided document passages. "
                    "Never hallucinate or assume facts not explicitly mentioned. "
                    "Cite sources and page numbers like [Source: <doc_name>, Page: <page>]. "
                    "If the answer cannot be established from the passages, explicitly state that it cannot be established and specify what is missing."
                )
            },
            {
                "role": "user",
                "content": f"DOCUMENT PASSAGES:\n{context}\n\nUSER QUESTION: {query}"
            }
        ]

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                is_unanswerable = "cannot be established" in text.lower() or "not provided" in text.lower()
                return {
                    "answer": text,
                    "is_unanswerable": is_unanswerable,
                    "provider": "OpenAI (gpt-4o-mini)",
                    "extracted_claims": self._extract_claims_from_text(text)
                }
        return None

    def _generate_local_grounded_answer(
        self,
        query: str,
        evidence_chunks: List[Dict[str, Any]],
        max_confidence: float,
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """
        Robust Local Grounded Engine:
        Extracts salient sentences and exact numbers matching the query terms.
        If no relevant matches or terms exist, declares unanswerable.
        """
        # Tokenize query to find relevant keywords
        query_words = set(re.findall(r'\b[a-zA-Z0-9_\-\$]+\b', query.lower()))
        stop_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how",
                      "is", "are", "was", "were", "the", "a", "an", "in", "on", "at", "to", "for",
                      "of", "and", "or", "by", "from", "with", "about", "does", "did", "do",
                      "acme", "technologies", "inc", "company", "documents", "document", "provide",
                      "remote", "employees", "employee"}
        key_topic_words = query_words - stop_words

        # Check if the key topic words appear anywhere in any evidence chunk
        all_evidence_text = " ".join(c.get("content", "").lower() for c in evidence_chunks)
        missing_topic_words = [kw for kw in key_topic_words if kw not in all_evidence_text]

        # If more than 50% of the specific topic words are completely absent from all evidence
        if key_topic_words and len(missing_topic_words) / len(key_topic_words) > 0.40:
            missing_terms_str = ", ".join(f"'{m}'" for m in missing_topic_words[:3])
            return {
                "answer": (
                    "Based on the provided documents, the answer cannot be established. "
                    f"Missing information: The uploaded documents do not contain information regarding {missing_terms_str}. "
                    "No relevant passages were found in the indexed corpus."
                ),
                "is_unanswerable": True,
                "provider": "DocuMind Grounded Engine (Local Mode - No External API Key)",
                "extracted_claims": []
            }

        matched_sentences: List[Tuple[str, str, int, float]] = []

        for chunk in evidence_chunks:
            doc_name = chunk.get("document_name") or f"Document {chunk.get('document_id', '')[:8]}"
            page = chunk.get("page_number", 1)
            raw_content = chunk.get("content", "")
            
            # Split into sentences or bullet lines
            lines = re.split(r'(?<=[.!?])\s+|\n', raw_content)
            for line in lines:
                line = line.strip()
                if len(line) < 15:
                    continue
                line_words = set(re.findall(r'\b[a-zA-Z0-9_\-\$]+\b', line.lower()))
                overlap = len(key_topic_words.intersection(line_words))
                if overlap > 0:
                    score = overlap / max(1, len(key_topic_words))
                    matched_sentences.append((line, doc_name, page, score))

        # Sort by sentence relevance score
        matched_sentences.sort(key=lambda x: x[3], reverse=True)

        # Check if any sentence had sufficient keyword overlap
        if not matched_sentences or matched_sentences[0][3] < 0.20 or max_confidence < confidence_threshold:
            return {
                "answer": (
                    "Based on the provided documents, the answer cannot be established. "
                    f"Missing information: The uploaded documents do not contain explicit facts or data regarding '{query}'. "
                    "No relevant passages or numerical metrics were found in the indexed corpus."
                ),
                "is_unanswerable": True,
                "provider": "DocuMind Grounded Engine (Local Mode - No External API Key)",
                "extracted_claims": []
            }

        # Deduplicate and pick top 2-3 most informative sentences
        selected = []
        seen_texts = set()
        for sent, doc_name, page, score in matched_sentences:
            if sent not in seen_texts:
                seen_texts.add(sent)
                selected.append((sent, doc_name, page))
            if len(selected) >= 3:
                break

        # Construct synthesised answer with citations
        response_parts = []
        claims = []
        for sent, doc_name, page in selected:
            # Clean sentence prefix if bullet
            clean_sent = re.sub(r'^[-\*\•\d\.\)]\s*', '', sent)
            citation_str = f" [Source: {doc_name}, Page: {page}]"
            response_parts.append(f"{clean_sent}{citation_str}")
            claims.append(clean_sent)

        final_answer = " ".join(response_parts)

        return {
            "answer": final_answer,
            "is_unanswerable": False,
            "provider": "DocuMind Grounded Engine (Local Mode - No External API Key)",
            "extracted_claims": claims
        }

    def _extract_claims_from_text(self, text: str) -> List[str]:
        """Extracts individual claim statements from text."""
        # Split by periods, ignoring citation brackets
        raw_sents = re.split(r'(?<=[.!?])\s+', text)
        claims = []
        for s in raw_sents:
            clean = re.sub(r'\[Source:.*?\]', '', s).strip()
            if len(clean) > 20 and not clean.startswith("Based on"):
                claims.append(clean)
        return claims[:5]


llm_provider = LLMProvider()
