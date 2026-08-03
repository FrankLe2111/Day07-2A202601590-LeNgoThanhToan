"""Run the five K4 retrieval benchmark queries.

Examples:
    python3 bench.py --provider mock
    python3 bench.py --provider local
    python3 bench.py --provider local --output benchmark_results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from ingest import build_knowledge_base
from src import (
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    PolicySectionChunker,
    SemanticChunker,
)


DEFAULT_DATA_DIR = Path("data/k4_ecommerce")


def select_embedder(provider: str) -> tuple[Callable[[str], list[float]], str]:
    if provider == "local":
        embedder = LocalEmbedder()
    elif provider == "openai":
        embedder = OpenAIEmbedder()
    else:
        embedder = MockEmbedder()
    return embedder, getattr(embedder, "_backend_name", provider)


def load_benchmark(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries")
    if not isinstance(queries, list) or len(queries) != 5:
        raise ValueError(f"Benchmark must contain exactly 5 queries: {path}")
    return queries


def query_filter(item: dict) -> dict | None:
    if not item.get("filter_required"):
        return None
    field = item.get("filter_field")
    if not field:
        raise ValueError(f"Query {item.get('id')} requires a filter_field")
    return {field: item.get("filter_value")}


def run_benchmark(data_dir: Path, provider: str, chunker_name: str, top_k: int = 3) -> dict:
    benchmark_path = data_dir / "benchmark_queries.json"
    queries = load_benchmark(benchmark_path)
    embedder, backend = select_embedder(provider)
    if chunker_name == "semantic":
        chunker = SemanticChunker(
            embedding_fn=embedder,
            similarity_threshold=0.35,
            min_chunk_size=250,
            max_chunk_size=900,
        )
        chunker_description = "SemanticChunker(threshold=0.35, min=250, max=900)"
    else:
        chunker = PolicySectionChunker(chunk_size=900)
        chunker_description = "PolicySectionChunker(chunk_size=900)"
    store = build_knowledge_base(
        data_dir,
        embedding_fn=embedder,
        chunker=chunker,
        collection_name="k4_benchmark",
    )

    evaluated = []
    hit_count = 0
    print(f"Embedding backend: {backend}")
    print(f"Chunker: {chunker_description}")
    if provider == "mock":
        print("WARNING: mock scores are deterministic but not semantically meaningful.")
    print(f"Indexed chunks: {store.get_collection_size()}\n")

    for item in queries:
        metadata_filter = query_filter(item)
        results = store.search_with_filter(
            item["query"], top_k=top_k, metadata_filter=metadata_filter
        )
        expected_doc = item["document_id"]
        hit = any(result["metadata"].get("doc_id") == expected_doc for result in results)
        hit_count += int(hit)

        print(f"[{item['id']}] {item['query']}")
        print(f"Filter: {metadata_filter or 'none'}")
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            preview = " ".join(result["content"].split())[:180]
            marker = " <-- expected document" if metadata.get("doc_id") == expected_doc else ""
            print(
                f"  {rank}. score={result['score']:.4f} "
                f"doc={metadata.get('doc_id')} chunk={metadata.get('chunk_index')}"
                f"{marker}\n     {preview}"
            )
        print(f"Top-{top_k} relevant document: {'YES' if hit else 'NO'}")
        print(f"Gold: {item['gold_answer']}\n")

        evaluated.append(
            {
                "id": item["id"],
                "query": item["query"],
                "metadata_filter": metadata_filter,
                "expected_document_id": expected_doc,
                "top_k_hit": hit,
                "results": [
                    {
                        "rank": rank,
                        "score": result["score"],
                        "document_id": result["metadata"].get("doc_id"),
                        "chunk_index": result["metadata"].get("chunk_index"),
                        "preview": " ".join(result["content"].split())[:300],
                    }
                    for rank, result in enumerate(results, start=1)
                ],
            }
        )

    print(f"Retrieval top-{top_k} hits: {hit_count}/5")
    print(f"Retrieval score: {hit_count * 2}/10")
    print("Note: this score checks retrieval only; verify agent answers against each gold answer.")
    return {
        "provider": provider,
        "backend": backend,
        "chunker": chunker_description,
        "top_k": top_k,
        "hits": hit_count,
        "retrieval_score": hit_count * 2,
        "queries": evaluated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the K4 retrieval benchmark")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--provider", choices=("mock", "local", "openai"), default="local")
    parser.add_argument("--chunker", choices=("semantic", "policy"), default="semantic")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.top_k <= 0:
        parser.error("--top-k must be positive")

    try:
        summary = run_benchmark(args.data_dir, args.provider, args.chunker, args.top_k)
    except (FileNotFoundError, ImportError, RuntimeError, ValueError) as exc:
        print(f"Benchmark failed: {exc}")
        if args.provider == "local":
            print("Install/cache the local model, or smoke-test with: python3 bench.py --provider mock")
        return 1

    if args.output:
        args.output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Saved results: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
