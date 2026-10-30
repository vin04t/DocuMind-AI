import re
from typing import List, Dict, Any, Optional
from app.core.config import settings


class TextChunker:
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        self.chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP

    def chunk_pages(
        self,
        document_id: str,
        pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunks pages of a document while preserving page numbers, character offsets,
        and semantic boundaries.
        """
        all_chunks = []
        global_chunk_idx = 0

        for page_data in pages:
            page_num = page_data["page_number"]
            page_text = page_data["text"]

            if not page_text or len(page_text.strip()) == 0:
                continue

            page_chunks = self._chunk_single_text(
                document_id=document_id,
                page_number=page_num,
                text=page_text,
                start_index=global_chunk_idx
            )
            all_chunks.extend(page_chunks)
            global_chunk_idx += len(page_chunks)

        return all_chunks

    def _chunk_single_text(
        self,
        document_id: str,
        page_number: int,
        text: str,
        start_index: int
    ) -> List[Dict[str, Any]]:
        # Split text into paragraphs first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk_text = ""
        current_start_char = 0
        char_cursor = 0
        local_idx = start_index

        for para in paragraphs:
            para = para.strip()
            if not para:
                char_cursor += 2
                continue

            # If a single paragraph is larger than chunk_size, split by sentences
            if len(para) > self.chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue

                    if len(current_chunk_text) + len(sent) + 1 > self.chunk_size and current_chunk_text:
                        # Finalize current chunk
                        chunk_end = current_start_char + len(current_chunk_text)
                        chunks.append(self._create_chunk_dict(
                            document_id=document_id,
                            page_number=page_number,
                            chunk_index=local_idx,
                            content=current_chunk_text.strip(),
                            start_char=current_start_char,
                            end_char=chunk_end
                        ))
                        local_idx += 1

                        # Compute overlap
                        overlap_text = current_chunk_text[-self.chunk_overlap:] if len(current_chunk_text) > self.chunk_overlap else ""
                        current_chunk_text = (overlap_text + " " + sent).strip()
                        current_start_char = chunk_end - len(overlap_text)
                    else:
                        if current_chunk_text:
                            current_chunk_text += " " + sent
                        else:
                            current_chunk_text = sent
                            current_start_char = char_cursor
            else:
                if len(current_chunk_text) + len(para) + 2 > self.chunk_size and current_chunk_text:
                    chunk_end = current_start_char + len(current_chunk_text)
                    chunks.append(self._create_chunk_dict(
                        document_id=document_id,
                        page_number=page_number,
                        chunk_index=local_idx,
                        content=current_chunk_text.strip(),
                        start_char=current_start_char,
                        end_char=chunk_end
                    ))
                    local_idx += 1

                    overlap_text = current_chunk_text[-self.chunk_overlap:] if len(current_chunk_text) > self.chunk_overlap else ""
                    current_chunk_text = (overlap_text + "\n\n" + para).strip()
                    current_start_char = chunk_end - len(overlap_text)
                else:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + para
                    else:
                        current_chunk_text = para
                        current_start_char = char_cursor

            char_cursor += len(para) + 2

        # Final trailing chunk
        if current_chunk_text.strip():
            chunks.append(self._create_chunk_dict(
                document_id=document_id,
                page_number=page_number,
                chunk_index=local_idx,
                content=current_chunk_text.strip(),
                start_char=current_start_char,
                end_char=current_start_char + len(current_chunk_text)
            ))

        return chunks

    def _create_chunk_dict(
        self,
        document_id: str,
        page_number: int,
        chunk_index: int,
        content: str,
        start_char: int,
        end_char: int
    ) -> Dict[str, Any]:
        # Rough token count estimate (~4 chars per token)
        token_count = max(1, len(content) // 4)
        chunk_id = f"{document_id}_p{page_number}_c{chunk_index}"
        return {
            "id": chunk_id,
            "document_id": document_id,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "content": content,
            "clean_content": content,
            "start_char": start_char,
            "end_char": end_char,
            "token_count": token_count
        }


chunker = TextChunker()
