from __future__ import annotations

import math
import re
from typing import Callable


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", text.strip())
            if sentence.strip()
        ]
        return [
            " ".join(sentences[index : index + self.max_sentences_per_chunk])
            for index in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [
                current_text[index : index + self.chunk_size]
                for index in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        if separator == "":
            return [
                current_text[index : index + self.chunk_size]
                for index in range(0, len(current_text), self.chunk_size)
            ]
        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        pieces = current_text.split(separator)
        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(buffer)
            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                chunks.extend(self._split(piece, remaining_separators[1:]))
                buffer = ""
        if buffer:
            chunks.append(buffer)
        return chunks


class PolicySectionChunker:
    """Split Vietnamese policy documents by headings, then cap long sections.

    Policy pages often express a rule as a heading followed by conditions,
    exceptions, or numbered steps. Keeping that block together makes retrieved
    evidence easier to understand than cutting at an arbitrary character.
    Oversized sections are delegated to ``RecursiveChunker``.
    """

    HEADING_PATTERN = re.compile(
        r"^(?:#{1,6}\s+.+|[IVXLCDM]+\.\s+.+|\d+(?:\.\d+)*[.)]\s+.+)$",
        re.IGNORECASE,
    )

    def __init__(self, chunk_size: int = 900) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections: list[str] = []
        buffer: list[str] = []
        for raw_line in text.strip().splitlines():
            line = raw_line.strip()
            if self.HEADING_PATTERN.match(line) and buffer:
                section = "\n".join(buffer).strip()
                if section:
                    sections.append(section)
                buffer = [line]
            else:
                buffer.append(raw_line)
        if buffer:
            section = "\n".join(buffer).strip()
            if section:
                sections.append(section)

        recursive = RecursiveChunker(chunk_size=self.chunk_size)
        chunks: list[str] = []
        for section in sections:
            pieces = recursive.chunk(section)
            heading = section.splitlines()[0].strip()
            if self.HEADING_PATTERN.match(heading):
                pieces = [
                    piece if index == 0 or piece.startswith(heading) else f"{heading}\n{piece}"
                    for index, piece in enumerate(pieces)
                ]
            chunks.extend(pieces)
        return chunks


class SemanticChunker:
    """Group adjacent text units while their embeddings remain semantically close.

    The input is first split at paragraph boundaries. Adjacent units are joined
    when their cosine similarity is at least ``similarity_threshold``. Minimum
    and maximum character limits prevent tiny or excessively broad chunks.
    """

    def __init__(
        self,
        embedding_fn: Callable[[str], list[float]],
        similarity_threshold: float = 0.35,
        min_chunk_size: int = 250,
        max_chunk_size: int = 900,
    ) -> None:
        if min_chunk_size <= 0 or max_chunk_size < min_chunk_size:
            raise ValueError("Require 0 < min_chunk_size <= max_chunk_size")
        self.embedding_fn = embedding_fn
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def _units(self, text: str) -> list[str]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        units: list[str] = []
        splitter = RecursiveChunker(chunk_size=self.max_chunk_size)
        for paragraph in paragraphs:
            units.extend(splitter.chunk(paragraph))
        return units

    def _embed_units(self, units: list[str]) -> list[list[float]]:
        model = getattr(self.embedding_fn, "model", None)
        if model is not None and hasattr(model, "encode"):
            vectors = model.encode(units, normalize_embeddings=True)
            return vectors.tolist() if hasattr(vectors, "tolist") else list(vectors)
        return [self.embedding_fn(unit) for unit in units]

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        units = self._units(text)
        if not units:
            return []
        vectors = self._embed_units(units)

        chunks: list[str] = []
        buffer = units[0]
        for index in range(1, len(units)):
            unit = units[index]
            candidate = f"{buffer}\n\n{unit}"
            similarity = compute_similarity(vectors[index - 1], vectors[index])
            topic_changed = similarity < self.similarity_threshold
            too_long = len(candidate) > self.max_chunk_size
            if too_long or (topic_changed and len(buffer) >= self.min_chunk_size):
                chunks.append(buffer)
                buffer = unit
            else:
                buffer = candidate
        if buffer:
            chunks.append(buffer)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 100)),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, strategy in strategies.items():
            chunks = strategy.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(map(len, chunks)) / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
