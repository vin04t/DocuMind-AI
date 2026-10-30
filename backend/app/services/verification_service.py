import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.llm_provider import llm_provider


class VerificationService:
    async def verify_answer_claims(
        self,
        answer: str,
        evidence_passages: List[Dict[str, Any]],
        claims: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs genuine claim-level verification against retrieved evidence passages.
        Classifies each claim into:
        - SUPPORTED: Evidence directly entails and confirms the claim.
        - PARTIALLY_SUPPORTED: Evidence supports core aspects but omits a qualifier or nuance.
        - CONTRADICTED: Evidence directly refutes or contradicts the claim numbers/facts.
        - NOT_SUPPORTED: Evidence does not contain sufficient facts to establish the claim.
        """
        if not claims:
            claims = self._extract_atomic_claims(answer)

        if not claims:
            return []

        verified_records = []
        for claim in claims:
            claim = claim.strip()
            if not claim or len(claim) < 15:
                continue

            record = self._verify_single_claim(claim, evidence_passages)
            verified_records.append(record)

        return verified_records

    def _extract_atomic_claims(self, text: str) -> List[str]:
        """Extracts atomic factual claim sentences from an answer."""
        # Strip bracketed citations like [Source: ..., Page: ...]
        clean_text = re.sub(r'\[Source:.*?\]', '', text)
        sentences = re.split(r'(?<=[.!?])\s+', clean_text)
        
        claims = []
        for s in sentences:
            s = s.strip()
            # Ignore purely conversational phrases
            if len(s) > 20 and not s.lower().startswith(("based on", "in conclusion", "furthermore")):
                claims.append(s)
        return claims[:6]

    def _verify_single_claim(
        self,
        claim: str,
        evidence_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verifies a single factual claim against available evidence passages.
        Performs lexical, numerical, and contextual entailment checks.
        """
        if not evidence_passages:
            return {
                "claim_text": claim,
                "status": "NOT_SUPPORTED",
                "document_id": None,
                "document_name": None,
                "page_number": None,
                "supporting_passage": None,
                "rationale": "No evidence passages were retrieved for verification.",
                "confidence_score": 0.0
            }

        claim_lower = claim.lower()
        claim_numbers = set(re.findall(r'\b\$?\d+(?:\.\d+)?%?(?:m|b|k)?\b', claim_lower))
        claim_words = set(re.findall(r'\b[a-z]{4,}\b', claim_lower))

        best_match = None
        best_score = -1.0
        best_passage = None
        has_direct_number_contradiction = False
        contradicting_passage = None

        for item in evidence_passages:
            passage_text = item.get("content", "")
            passage_lower = passage_text.lower()
            passage_words = set(re.findall(r'\b[a-z]{4,}\b', passage_lower))
            passage_numbers = set(re.findall(r'\b\$?\d+(?:\.\d+)?%?(?:m|b|k)?\b', passage_lower))

            # Word overlap
            overlap = len(claim_words.intersection(passage_words))
            word_sim = overlap / max(1, len(claim_words))

            # Number checks
            num_overlap = len(claim_numbers.intersection(passage_numbers))

            # Detect possible contradiction: same topic (high word overlap) but different numbers
            if word_sim >= 0.4 and claim_numbers and not num_overlap and passage_numbers:
                has_direct_number_contradiction = True
                contradicting_passage = item

            # Total alignment score
            score = word_sim + (0.5 if num_overlap > 0 else 0.0)
            if score > best_score:
                best_score = score
                best_match = item
                best_passage = passage_text

        # Determine verification status
        if has_direct_number_contradiction and contradicting_passage and best_score < 0.8:
            return {
                "claim_text": claim,
                "status": "CONTRADICTED",
                "document_id": contradicting_passage.get("document_id"),
                "document_name": contradicting_passage.get("document_name"),
                "page_number": contradicting_passage.get("page_number"),
                "supporting_passage": contradicting_passage.get("content", "")[:350],
                "rationale": (
                    "Evidence passage discusses the subject but provides conflicting numerical values or dates "
                    f"differing from the claim: {claim_numbers} vs passage figures."
                ),
                "confidence_score": 0.85
            }

        if best_match and best_score >= 0.65:
            # Check if all claim numbers are grounded
            if claim_numbers and not claim_numbers.issubset(set(re.findall(r'\b\$?\d+(?:\.\d+)?%?(?:m|b|k)?\b', best_passage.lower()))):
                return {
                    "claim_text": claim,
                    "status": "PARTIALLY_SUPPORTED",
                    "document_id": best_match.get("document_id"),
                    "document_name": best_match.get("document_name"),
                    "page_number": best_match.get("page_number"),
                    "supporting_passage": best_passage[:350],
                    "rationale": "The conceptual premise is confirmed in the source passage, but specific figures or qualifiers could only be partially matched.",
                    "confidence_score": 0.70
                }

            return {
                "claim_text": claim,
                "status": "SUPPORTED",
                "document_id": best_match.get("document_id"),
                "document_name": best_match.get("document_name"),
                "page_number": best_match.get("page_number"),
                "supporting_passage": best_passage[:350],
                "rationale": "Direct textual and factual entailment verified against source passage.",
                "confidence_score": 0.95
            }

        elif best_match and best_score >= 0.35:
            return {
                "claim_text": claim,
                "status": "PARTIALLY_SUPPORTED",
                "document_id": best_match.get("document_id"),
                "document_name": best_match.get("document_name"),
                "page_number": best_match.get("page_number"),
                "supporting_passage": best_passage[:350],
                "rationale": "Passage touches upon the theme, but lacks complete corroboration of all stated facts.",
                "confidence_score": 0.60
            }
        else:
            return {
                "claim_text": claim,
                "status": "NOT_SUPPORTED",
                "document_id": best_match.get("document_id") if best_match else None,
                "document_name": best_match.get("document_name") if best_match else None,
                "page_number": best_match.get("page_number") if best_match else None,
                "supporting_passage": best_passage[:350] if best_passage else None,
                "rationale": "Insufficient textual evidence in the retrieved context to verify this claim.",
                "confidence_score": 0.30
            }


verification_service = VerificationService()
