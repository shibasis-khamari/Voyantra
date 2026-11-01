"""
Voyantra Semantic Chunker
Segments documents and entity summaries into coherent, heading-aware chunks
with token estimation and content-hash generation.
"""
import re
import hashlib
from typing import List, Optional
from ....schemas.knowledge import KnowledgeDocument, KnowledgeEntity, KnowledgeChunk, utc_now_iso


class TextChunker:
    def __init__(self, target_chunk_chars: int = 1000, overlap_chars: int = 150):
        self.target_chars = target_chunk_chars
        self.overlap = overlap_chars

    def chunk_document(self, document: KnowledgeDocument) -> List[KnowledgeChunk]:
        """Chunks a KnowledgeDocument preserving heading sections."""
        text = document.cleaned_content or ""
        lines = text.splitlines()

        chunks: List[KnowledgeChunk] = []
        current_heading = document.title or "General Information"
        current_buffer: List[str] = []
        current_len = 0
        chunk_idx = 0

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check if line looks like a heading (short, capitalised or ends with colon)
            if len(line_str) < 60 and (line_str.isupper() or line_str.endswith(":") or line_str.startswith("#")):
                if current_buffer and current_len > 300:
                    chunk_text = "\n".join(current_buffer)
                    chunks.append(self._create_chunk(
                        document_id=document.id,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        heading=current_heading,
                        source_url=document.url,
                        source_title=document.title,
                        language=document.language,
                    ))
                    chunk_idx += 1
                    current_buffer = []
                    current_len = 0
                current_heading = line_str.lstrip("#").strip().rstrip(":")

            current_buffer.append(line_str)
            current_len += len(line_str)

            if current_len >= self.target_chars:
                chunk_text = "\n".join(current_buffer)
                chunks.append(self._create_chunk(
                    document_id=document.id,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    heading=current_heading,
                    source_url=document.url,
                    source_title=document.title,
                    language=document.language,
                ))
                chunk_idx += 1
                # Retain overlap from end of current buffer
                overlap_text = line_str if len(line_str) <= self.overlap else line_str[-self.overlap:]
                current_buffer = [overlap_text]
                current_len = len(overlap_text)

        if current_buffer:
            chunk_text = "\n".join(current_buffer)
            chunks.append(self._create_chunk(
                document_id=document.id,
                chunk_index=chunk_idx,
                text=chunk_text,
                heading=current_heading,
                source_url=document.url,
                source_title=document.title,
                language=document.language,
            ))

        return chunks

    def chunk_entity(self, entity: KnowledgeEntity) -> List[KnowledgeChunk]:
        """Converts an entity and its highlights into searchable KnowledgeChunk(s)."""
        lines = [
            f"{entity.name} is a {entity.category or 'sightseeing spot'} located in {entity.city_id or 'India'}.",
            entity.description,
        ]
        if entity.highlights:
            lines.append("Key Highlights: " + ", ".join(entity.highlights))
        if entity.address:
            lines.append(f"Location Address: {entity.address}")
        if entity.opening_hours and entity.opening_hours_verified:
            lines.append(f"Operating Hours: {entity.opening_hours}")
        if entity.estimated_cost_inr and entity.estimated_cost_inr > 0:
            lines.append(f"Estimated Entry/Expense: ₹{entity.estimated_cost_inr}")

        full_text = "\n".join([ln for ln in lines if ln])
        chunk = self._create_chunk(
            document_id=None,
            chunk_index=0,
            text=full_text,
            heading=entity.name,
            entity_id=entity.id,
            source_url=entity.primary_source_url,
            source_title=entity.name,
            city_id=entity.city_id,
            category=entity.category,
        )
        return [chunk]

    def _create_chunk(
        self,
        chunk_index: int,
        text: str,
        heading: str,
        document_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        source_url: Optional[str] = None,
        source_title: Optional[str] = None,
        city_id: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
    ) -> KnowledgeChunk:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        tokens_est = len(text.split())
        prefix = f"chk-{document_id or entity_id or 'anon'}-{chunk_index}"
        chunk_id = f"{prefix}-{content_hash[:8]}"

        return KnowledgeChunk(
            id=chunk_id,
            document_id=document_id,
            entity_id=entity_id,
            chunk_index=chunk_index,
            content=text,
            content_hash=content_hash,
            token_count=tokens_est,
            heading_context=heading,
            language=language,
            is_active=True,
            source_url=source_url,
            source_title=source_title,
            city_id=city_id,
            category=category,
            created_at=utc_now_iso(),
        )
