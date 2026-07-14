"""PDF Document parsing, text sanitization, and sliding-window chunking utilities."""

import re
from typing import Dict, List, Any
import pypdf


class ValidationDocumentParser:
    """PDF parsing and sanitization engine for CSV validation ingestion."""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Dict[int, str]:
        """Extracts and sanitizes text page-by-page from a PDF.

        Args:
            file_path: Path to the target PDF file.

        Returns:
            Dict mapping page numbers (1-indexed) to sanitized text content.

        Raises:
            ValueError: If the file is completely unreadable or scanned (requires OCR).
        """
        pages_content: Dict[int, str] = {}
        try:
            reader = pypdf.PdfReader(file_path)
            total_pages = len(reader.pages)
            total_chars = 0

            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text() or ""
                
                # Sanitization Hook: Remove hidden binary/control characters (keep common whitespace & punctuation)
                sanitized_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
                # Normalize line breaks and multiple spaces
                sanitized_text = re.sub(r"\r\n|\r", "\n", sanitized_text)
                sanitized_text = re.sub(r"[ \t]+", " ", sanitized_text)
                sanitized_text = sanitized_text.strip()
                
                pages_content[page_num + 1] = sanitized_text
                total_chars += len(sanitized_text)

            # Raise clean exception if no readable text is present (requires OCR)
            if total_chars == 0:
                raise ValueError(
                    f"PDF document '{file_path}' contains zero readable text characters. "
                    "Scanned image PDF detected. Upstream OCR is required."
                )

            return pages_content

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to process PDF '{file_path}': {str(e)}") from e

    @staticmethod
    def chunk_extracted_text(
        pages_dict: Dict[int, str],
        max_tokens_per_chunk: int = 2000,
        chunk_overlap_words: int = 150
    ) -> List[Dict[str, Any]]:
        """Splits page text into sliding-window chunks with metadata tracking.

        Estimates tokens using standard word-to-token ratio (approx. 1.33 tokens per word).

        Args:
            pages_dict: Page mapping from extract_text_from_pdf.
            max_tokens_per_chunk: The target maximum token count for each chunk.
            chunk_overlap_words: Word count overlap between sliding chunks.

        Returns:
            List of chunk dicts containing content, page number, and chunk index metadata.
        """
        chunks: List[Dict[str, Any]] = []
        # Target word count per chunk based on 1.33 tokens per word (2000 tokens ≈ 1500 words)
        words_per_chunk = int(max_tokens_per_chunk / 1.33)

        for page_num, text in pages_dict.items():
            if not text:
                continue

            words = text.split()
            if len(words) <= words_per_chunk:
                # Page fits entirely within a single chunk
                chunks.append({
                    "page": page_num,
                    "chunk_index": 0,
                    "content": " ".join(words),
                    "estimated_tokens": int(len(words) * 1.33)
                })
                continue

            # Sliding-window split for larger pages
            idx = 0
            start = 0
            while start < len(words):
                end = min(start + words_per_chunk, len(words))
                chunk_words = words[start:end]
                chunks.append({
                    "page": page_num,
                    "chunk_index": idx,
                    "content": " ".join(chunk_words),
                    "estimated_tokens": int(len(chunk_words) * 1.33)
                })
                start += (words_per_chunk - chunk_overlap_words)
                idx += 1

        return chunks
