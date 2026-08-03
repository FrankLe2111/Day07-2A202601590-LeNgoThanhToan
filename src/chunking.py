from __future__ import annotations

import math
import re
from collections import Counter


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
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])(?:\s+|$)", text.strip()) if s.strip()]
        n = self.max_sentences_per_chunk
        return [" ".join(sentences[i:i + n]).strip() for i in range(0, len(sentences), n)]


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
        chunks = self._split(text.strip(), self.separators or [""])
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i:i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
        separator = remaining_separators[0]
        if separator == "":
            return [current_text[i:i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
        parts = current_text.split(separator)
        if len(parts) == 1:
            return self._split(current_text, remaining_separators[1:])
        result: list[str] = []
        buffer = ""
        for part in parts:
            candidate = part if not buffer else buffer + separator + part
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    result.extend(self._split(buffer, remaining_separators[1:]))
                buffer = part
        if buffer:
            result.extend(self._split(buffer, remaining_separators[1:]))
        return result


def _split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])(?:\s+|$)", text.strip()) if s.strip()]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE)


def _vectorize(text: str, vocabulary: list[str]) -> list[float]:
    counts = Counter(_tokenize(text))
    return [float(counts.get(term, 0)) for term in vocabulary]


def _semantic_similarity(text_a: str, text_b: str, vocabulary: list[str]) -> float:
    return compute_similarity(_vectorize(text_a, vocabulary), _vectorize(text_b, vocabulary))


class SemanticChunker:
    """
    Split text into chunks by merging sentences that remain semantically similar.

    This implementation uses token-frequency cosine similarity as a lightweight
    semantic proxy so it works without external embedding dependencies.
    """

    def __init__(self, similarity_threshold: float = 0.22, max_chunk_size: int = 700) -> None:
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        sentences = _split_sentences(text)
        if not sentences:
            return []

        vocabulary = sorted({token for sentence in sentences for token in _tokenize(sentence)})
        if not vocabulary:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        current_sentences: list[str] = [sentences[0]]
        current_text = sentences[0]

        for sentence in sentences[1:]:
            candidate_text = f"{current_text} {sentence}".strip()
            similarity = _semantic_similarity(current_text, sentence, vocabulary)
            if (
                similarity < self.similarity_threshold
                or len(candidate_text) > self.max_chunk_size
            ) and current_sentences:
                chunks.append(" ".join(current_sentences).strip())
                current_sentences = [sentence]
                current_text = sentence
                continue

            current_sentences.append(sentence)
            current_text = candidate_text

        if current_sentences:
            chunks.append(" ".join(current_sentences).strip())

        return [chunk for chunk in chunks if chunk]


class AgenticChunker:
    """
    Split text using structure-aware heuristics that mimic an agent deciding
    where a document should break.

    The chunker prefers paragraph boundaries, then sentence boundaries, and it
    starts a new chunk when the next sentence looks like a new instruction,
    warning, or section.
    """

    TRANSITION_CUES = (
        "tuy nhiên",
        "lưu ý",
        "bước",
        "trường hợp",
        "nếu",
        "trong trường hợp",
        "ngoài ra",
        "tiếp theo",
        "cuối cùng",
    )

    def __init__(self, max_chunk_size: int = 800, similarity_threshold: float = 0.15) -> None:
        self.max_chunk_size = max_chunk_size
        self.similarity_threshold = similarity_threshold

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
        if not paragraphs:
            return []

        sentences = [sentence for paragraph in paragraphs for sentence in _split_sentences(paragraph)]
        if not sentences:
            return [text.strip()]

        vocabulary = sorted({token for sentence in sentences for token in _tokenize(sentence)})
        chunks: list[str] = []
        current_sentences: list[str] = []
        current_text = ""

        for sentence in sentences:
            should_break = False
            normalized = sentence.lower().strip()
            if current_sentences:
                candidate_text = f"{current_text} {sentence}".strip()
                semantic_score = _semantic_similarity(current_text, sentence, vocabulary) if vocabulary else 0.0
                transition_hit = normalized.startswith(tuple(self.TRANSITION_CUES))
                hard_boundary = bool(re.match(r"^(\d+\.|[IVXLC]+\.|[-*•])\s", sentence.strip()))
                should_break = (
                    hard_boundary
                    or transition_hit
                    or semantic_score < self.similarity_threshold
                    or len(candidate_text) > self.max_chunk_size
                )

            if should_break and current_sentences:
                chunks.append(" ".join(current_sentences).strip())
                current_sentences = [sentence]
                current_text = sentence
                continue

            current_sentences.append(sentence)
            current_text = sentence if not current_text else f"{current_text} {sentence}".strip()

        if current_sentences:
            chunks.append(" ".join(current_sentences).strip())

        return [chunk for chunk in chunks if chunk]


class ParentChildChunker:
    """
    Build a hierarchy of parent chunks and child chunks.

    ``chunk()`` returns the child chunks for compatibility with the other
    chunkers, while ``chunk_hierarchy()`` exposes both layers.
    """

    def __init__(
        self,
        parent_chunk_size: int = 1000,
        child_chunk_size: int = 250,
        overlap: int = 30,
    ) -> None:
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.overlap = overlap
        self.last_parent_chunks: list[str] = []
        self.last_child_chunks: list[str] = []
        self.last_children_by_parent: list[list[str]] = []

    def _child_chunker(self) -> FixedSizeChunker:
        return FixedSizeChunker(chunk_size=self.child_chunk_size, overlap=min(self.overlap, max(0, self.child_chunk_size - 1)))

    def _parent_chunker(self) -> RecursiveChunker:
        return RecursiveChunker(chunk_size=self.parent_chunk_size)

    def chunk_hierarchy(self, text: str) -> dict[str, list[str]]:
        if not text or not text.strip():
            self.last_parent_chunks = []
            self.last_child_chunks = []
            self.last_children_by_parent = []
            return {"parents": [], "children": []}

        parent_chunks = self._parent_chunker().chunk(text)
        child_chunker = self._child_chunker()
        children_by_parent: list[list[str]] = []
        all_children: list[str] = []

        for parent_chunk in parent_chunks:
            child_chunks = child_chunker.chunk(parent_chunk)
            if not child_chunks:
                child_chunks = [parent_chunk.strip()]
            children_by_parent.append(child_chunks)
            all_children.extend(child_chunks)

        self.last_parent_chunks = parent_chunks
        self.last_child_chunks = all_children
        self.last_children_by_parent = children_by_parent
        return {"parents": parent_chunks, "children": all_children}

    def chunk(self, text: str) -> list[str]:
        return self.chunk_hierarchy(text)["children"]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    return 0.0 if not norm_a or not norm_b else _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, max(0, chunk_size // 10))),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
            "semantic": SemanticChunker(max_chunk_size=max(chunk_size, 1)),
            "agentic": AgenticChunker(max_chunk_size=max(chunk_size, 1)),
            "parent_child": ParentChildChunker(parent_chunk_size=max(chunk_size * 2, chunk_size), child_chunk_size=max(chunk_size // 2, 1)),
        }
        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            result[name] = {"count": len(chunks), "avg_length": sum(map(len, chunks)) / len(chunks) if chunks else 0.0, "chunks": chunks}
        return result
