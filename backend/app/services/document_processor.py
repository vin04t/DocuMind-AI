import os
import re
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF


class DocumentProcessingError(Exception):
    pass


class DocumentProcessor:
    def extract_document(self, file_path: str) -> Dict[str, Any]:
        """
        Validates, opens, and extracts structured text and metadata from a PDF file.
        Returns:
            {
                "page_count": int,
                "is_scanned": bool,
                "metadata": dict,
                "pages": [
                    {"page_number": int, "text": str, "char_count": int}
                ]
            }
        """
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"File not found: {file_path}")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise DocumentProcessingError(f"Failed to open PDF document: {str(e)}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise DocumentProcessingError("The provided PDF file contains zero pages.")

        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", "")
        }

        extracted_pages = []
        total_text_length = 0
        total_images = 0

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1
            
            # Extract plain text
            raw_text = page.get_text("text") or ""
            clean_text = self.clean_text(raw_text)
            
            # Count images for scanned PDF heuristic
            images = page.get_images(full=True)
            total_images += len(images)
            
            char_count = len(clean_text)
            total_text_length += char_count

            extracted_pages.append({
                "page_number": page_num,
                "text": clean_text,
                "char_count": char_count
            })

        doc.close()

        # Scanned PDF detection heuristic: few characters per page but multiple images
        is_scanned = False
        if page_count > 0 and (total_text_length / page_count < 40) and total_images >= page_count:
            is_scanned = True

        return {
            "page_count": page_count,
            "is_scanned": is_scanned,
            "metadata": metadata,
            "pages": extracted_pages
        }

    def clean_text(self, text: str) -> str:
        """Cleans and normalizes extracted text."""
        if not text:
            return ""
        # Replace non-breaking spaces and null bytes
        text = text.replace("\xa0", " ").replace("\x00", "")
        # Remove consecutive duplicate whitespace while preserving newlines
        lines = [line.strip() for line in text.split("\n")]
        # Group lines, collapsing excessive blank lines
        cleaned_lines = []
        consecutive_empty = 0
        for line in lines:
            if not line:
                consecutive_empty += 1
                if consecutive_empty <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_empty = 0
                cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()


document_processor = DocumentProcessor()
