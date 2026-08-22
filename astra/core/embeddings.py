from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from pathlib import Path

from .models import CodeChunk, SearchResult

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def _tokens(value: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(value.replace("_", " "))]


class VectorIndex:
    """Local vector index with optional Chroma/SentenceTransformer acceleration."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.data_path = self.directory / "chunks.json"
        self.chunks: list[CodeChunk] = []
        self._load()

    def _load(self) -> None:
        if self.data_path.exists():
            self.chunks = [
                CodeChunk(**item) for item in json.loads(self.data_path.read_text(encoding="utf-8"))
            ]

    def index(self, chunks: list[CodeChunk]) -> int:
        self.chunks = chunks
        self.data_path.write_text(
            json.dumps([chunk.__dict__ for chunk in chunks], indent=2), encoding="utf-8"
        )
        if os.getenv("ASTRA_ENABLE_EMBEDDINGS", "").lower() in {"1", "true", "yes"}:
            self._try_build_chroma()
        return len(chunks)

    def _try_build_chroma(self) -> None:
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            client = chromadb.PersistentClient(path=str(self.directory / "chroma"))
            collection = client.get_or_create_collection("astra_code")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            collection.upsert(
                ids=[c.id for c in self.chunks],
                documents=[c.source for c in self.chunks],
                metadatas=[c.as_metadata() for c in self.chunks],
                embeddings=model.encode([c.source for c in self.chunks]).tolist(),
            )
        except Exception:
            pass

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if os.getenv("ASTRA_ENABLE_EMBEDDINGS", "").lower() in {"1", "true", "yes"}:
            vector_results = self._search_chroma(query, limit)
            if vector_results is not None:
                return vector_results
        query_tokens = Counter(_tokens(query))
        scored: list[SearchResult] = []
        for chunk in self.chunks:
            text_tokens = Counter(_tokens(f"{chunk.name} {chunk.docstring} {chunk.source}"))
            dot = sum(query_tokens[token] * text_tokens[token] for token in query_tokens)
            norm = math.sqrt(
                sum(v * v for v in query_tokens.values()) * sum(v * v for v in text_tokens.values())
            )
            score = dot / norm if norm else 0.0
            if score > 0:
                scored.append(SearchResult(chunk, score))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

    def _search_chroma(self, query: str, limit: int) -> list[SearchResult] | None:
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            client = chromadb.PersistentClient(path=str(self.directory / "chroma"))
            collection = client.get_collection("astra_code")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            response = collection.query(
                query_embeddings=model.encode([query]).tolist(), n_results=limit
            )
            results: list[SearchResult] = []
            chunks_by_id = {chunk.id: chunk for chunk in self.chunks}
            for chunk_id, distance in zip(response["ids"][0], response["distances"][0]):
                chunk = chunks_by_id.get(chunk_id)
                if chunk is not None:
                    results.append(SearchResult(chunk, 1.0 / (1.0 + distance), distance))
            return results
        except Exception:
            return None
