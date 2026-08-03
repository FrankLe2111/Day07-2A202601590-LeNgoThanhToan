from __future__ import annotations

import math
import re


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
        if not text:
            return []
        
        # Split using lookbehind to keep the delimiters with the sentences
        pattern = r'(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)'
        raw_sentences = re.split(pattern, text)
        
        # Filter out empty strings
        sentences = [s for s in raw_sentences if s]
        
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = "".join(chunk_sentences).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks


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
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            # Fallback: character-by-character chunking
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        if sep not in current_text:
            return self._split(current_text, next_seps)

        splits = current_text.split(sep)
        all_sub_chunks = []
        for part in splits:
            if len(part) > self.chunk_size:
                all_sub_chunks.extend(self._split(part, next_seps))
            else:
                all_sub_chunks.append(part)

        merged_chunks = []
        current_chunk = []
        current_length = 0
        for part in all_sub_chunks:
            part_len = len(part)
            sep_len = len(sep) if current_chunk else 0
            if current_length + sep_len + part_len <= self.chunk_size:
                current_chunk.append(part)
                current_length += sep_len + part_len
            else:
                if current_chunk:
                    merged_chunks.append(sep.join(current_chunk))
                current_chunk = [part]
                current_length = part_len
        if current_chunk:
            merged_chunks.append(sep.join(current_chunk))
        return merged_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(y * y for y in vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, min(50, chunk_size // 2)))
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        fixed_chunks = fixed_chunker.chunk(text)
        sentence_chunks = sentence_chunker.chunk(text)
        recursive_chunks = recursive_chunker.chunk(text)

        fixed_count = len(fixed_chunks)
        fixed_avg = sum(len(c) for c in fixed_chunks) / fixed_count if fixed_count > 0 else 0.0

        sentence_count = len(sentence_chunks)
        sentence_avg = sum(len(c) for c in sentence_chunks) / sentence_count if sentence_count > 0 else 0.0

        recursive_count = len(recursive_chunks)
        recursive_avg = sum(len(c) for c in recursive_chunks) / recursive_count if recursive_count > 0 else 0.0

        return {
            'fixed_size': {
                'count': fixed_count,
                'avg_length': fixed_avg,
                'chunks': fixed_chunks
            },
            'by_sentences': {
                'count': sentence_count,
                'avg_length': sentence_avg,
                'chunks': sentence_chunks
            },
            'recursive': {
                'count': recursive_count,
                'avg_length': recursive_avg,
                'chunks': recursive_chunks
            }
        }
