"""Lightweight Python-native vector database and dense embedding generator for semantic RAG."""

import hashlib
import math
from typing import List, Dict, Any, Optional


class HashEmbeddingModel:
    """Python-native dense embedding generator using character n-gram and word feature hashing."""

    DIMENSIONS: int = 384

    @classmethod
    def compute_embedding(cls, text: str) -> List[float]:
        """Generates a dense, L2-normalized float vector (384 dimensions) representing the text.

        Uses word and character 3-gram feature hashing to capture semantic,
        morphological, and typo-tolerant variations.

        Args:
            text: Input string to embed.

        Returns:
            A list of 384 floats representing the normalized embedding vector.
        """
        # 1. Clean and tokenize text
        text_clean = text.lower().strip()
        if not text_clean:
            return [0.0] * cls.DIMENSIONS

        words = re_tokenize = re_words = [w for w in text_clean.split() if w]
        if not words:
            return [0.0] * cls.DIMENSIONS

        # Generate features: words and character 3-grams
        features: List[str] = list(words)
        for word in words:
            # Pad word for n-grams
            padded = f"^{word}$"
            if len(padded) >= 3:
                for i in range(len(padded) - 2):
                    features.append(padded[i:i+3])

        # 2. Hash features into dimensions with frequency weights
        vector = [0.0] * cls.DIMENSIONS
        for feature in features:
            # Use md5 to deterministically hash feature to dimension index
            h = hashlib.md5(feature.encode("utf-8")).hexdigest()
            index = int(h, 16) % cls.DIMENSIONS
            
            # Simple TF weight: increment dimension
            vector[index] += 1.0

        # 3. L2-Normalize the vector to unit length
        sq_sum = sum(val ** 2 for val in vector)
        l2_norm = math.sqrt(sq_sum)

        if l2_norm > 0:
            return [val / l2_norm for val in vector]
        return [0.0] * cls.DIMENSIONS


class QualityVectorStoreManager:
    """In-memory vector database manager for corporate SOP regulatory documents."""

    def __init__(self) -> None:
        # Each document entry stores: {"sop_id": str, "section_title": str, "content": str, "embedding": list[float]}
        self.index: List[Dict[str, Any]] = []
        self.lessons_index: List[Dict[str, Any]] = []

    def query_relevant_lessons(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Semantic search querying matched Correction Lessons using cosine similarity score."""
        query_vector = HashEmbeddingModel.compute_embedding(query_text)
        matches: List[Dict[str, Any]] = []

        for lesson in self.lessons_index:
            similarity = sum(q * l for q, l in zip(query_vector, lesson["embedding"]))
            matches.append({
                "lesson_id": lesson["lesson_id"],
                "system_context": lesson["system_context"],
                "extracted_rule": lesson["extracted_rule"],
                "original_ai_text": lesson["original_ai_text"],
                "human_corrected_text": lesson["human_corrected_text"],
                "similarity_score": round(float(similarity), 4)
            })

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:limit]

    def seed_regulatory_knowledge_base(self, documents: List[Dict[str, str]], tenant_id: Optional[str] = None) -> None:
        """Computes embeddings and indexes a batch of document structures.

        Args:
            documents: List of dicts containing 'sop_id', 'section_title', and 'content'.
            tenant_id: Optional tenant identifier to scope documents.
        """
        for doc in documents:
            content = doc.get("content", "")
            embedding = HashEmbeddingModel.compute_embedding(content)
            self.index.append({
                "sop_id": doc.get("sop_id", "UNKNOWN"),
                "section_title": doc.get("section_title", ""),
                "content": content,
                "embedding": embedding,
                "tenant_id": tenant_id
            })

    def query_relevant_guidelines(
        self,
        query_text: str,
        limit: int = 3,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search querying matched SOP guidelines using cosine similarity score.

        Args:
            query_text: Search query string.
            limit: Maximum matches to return.
            tenant_id: Optional tenant identifier to enforce logical separation.

        Returns:
            List of matched documents containing metadata and calculated 'similarity_score'.
        """
        query_vector = HashEmbeddingModel.compute_embedding(query_text)
        matches: List[Dict[str, Any]] = []

        for doc in self.index:
            # Enforce tenant isolation if tenant_id is specified
            if tenant_id and doc.get("tenant_id") != tenant_id:
                continue

            # Cosine similarity is the dot product of two L2-normalized unit vectors
            similarity = sum(q * d for q, d in zip(query_vector, doc["embedding"]))
            
            matches.append({
                "sop_id": doc["sop_id"],
                "section_title": doc["section_title"],
                "content": doc["content"],
                "similarity_score": round(float(similarity), 4)
            })

        # Sort matches by similarity score descending
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:limit]
