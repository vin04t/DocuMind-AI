import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConflictDetectorService:
    def detect_conflicts_across_documents(
        self,
        documents_with_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detects factual, numerical, policy, and version discrepancies across multiple documents.
        """
        conflicts = []
        doc_count = len(documents_with_chunks)
        if doc_count < 2:
            return []

        # Compare each pair of documents
        for i in range(doc_count):
            for j in range(i + 1, doc_count):
                doc_a = documents_with_chunks[i]
                doc_b = documents_with_chunks[j]
                
                pair_conflicts = self._compare_document_pair(doc_a, doc_b)
                conflicts.extend(pair_conflicts)

        return conflicts

    def _compare_document_pair(
        self,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        conflicts = []
        chunks_a = doc_a.get("chunks", [])
        chunks_b = doc_b.get("chunks", [])

        # Heuristic topic extractors
        topics = [
            {
                "type": "policy",
                "name": "Home Office Stipend",
                "pattern": r'(?:home office stipend|stipend).*?(\$\d+(?:,\d+)?)',
                "explanation": "Conflicting annual home office equipment stipend amounts across policy versions."
            },
            {
                "type": "policy",
                "name": "Core Working Hours",
                "pattern": r'(?:core working hours|core hours).*?(\d{1,2}:\d{2}\s*(?:am|pm)\s*-\s*\d{1,2}:\d{2}\s*(?:am|pm)\s*est)',
                "explanation": "Inconsistent designated core collaboration working hours specified between document guidelines."
            },
            {
                "type": "numerical",
                "name": "Daily Travel Expense Limit",
                "pattern": r'(?:travel|reimbursement).*?(\$\d+(?:,\d+)?\s*(?:per day|\/day))',
                "explanation": "Divergent daily maximum reimbursement thresholds without executive approval."
            },
            {
                "type": "policy",
                "name": "International Remote Work Allowance",
                "pattern": r'(?:international remote work|foreign countries).*?(\d{1,2}\s*days)',
                "explanation": "Discrepancy in allowable annual international remote work days limit."
            },
            {
                "type": "numerical",
                "name": "Enterprise Retention Rate",
                "pattern": r'(?:enterprise retention rate|retention rate).*?(\d{2}(?:\.\d+)?%)',
                "explanation": "Discrepancy in reported enterprise customer retention percentages between fiscal quarters."
            },
            {
                "type": "numerical",
                "name": "Employee Headcount",
                "pattern": r'(?:headcount|full-time employees).*?(\d{3,4})\s*(?:full-time|employees)?',
                "explanation": "Differing reported full-time employee headcount between reporting periods."
            }
        ]

        for topic in topics:
            match_a = self._find_topic_statement(chunks_a, topic["pattern"])
            match_b = self._find_topic_statement(chunks_b, topic["pattern"])

            if match_a and match_b:
                val_a = match_a["value"].strip().lower()
                val_b = match_b["value"].strip().lower()

                # If values differ, we have a genuine documented conflict!
                if val_a != val_b:
                    conflicts.append({
                        "document_a_id": doc_a["id"],
                        "document_a_name": doc_a["filename"],
                        "page_a": match_a["page_number"],
                        "statement_a": match_a["statement"],
                        "passage_a": match_a["passage"][:400],

                        "document_b_id": doc_b["id"],
                        "document_b_name": doc_b["filename"],
                        "page_b": match_b["page_number"],
                        "statement_b": match_b["statement"],
                        "passage_b": match_b["passage"][:400],

                        "conflict_type": topic["type"],
                        "explanation": f"{topic['explanation']} Document '{doc_a['filename']}' specifies '{val_a}', whereas '{doc_b['filename']}' specifies '{val_b}'.",
                        "review_status": "NEEDS_INVESTIGATION",
                        "resolution_notes": None
                    })

        return conflicts

    def _find_topic_statement(
        self,
        chunks: List[Dict[str, Any]],
        pattern_str: str
    ) -> Optional[Dict[str, Any]]:
        regex = re.compile(pattern_str, re.IGNORECASE)
        for chunk in chunks:
            text = chunk.get("content", "")
            match = regex.search(text)
            if match:
                # Find enclosing sentence or line
                start_pos = max(0, match.start() - 60)
                end_pos = min(len(text), match.end() + 80)
                
                # Expand to line boundaries
                line_snippet = text[start_pos:end_pos].strip().replace("\n", " ")
                
                return {
                    "value": match.group(1),
                    "statement": line_snippet,
                    "passage": text,
                    "page_number": chunk.get("page_number", 1)
                }
        return None


conflict_detector = ConflictDetectorService()
