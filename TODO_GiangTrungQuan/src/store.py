from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": doc.metadata or {},
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_embedding = self._embedding_fn(query)
        results = []
        for r in records:
            score = compute_similarity(query_embedding, r["embedding"])
            results.append({
                "id": r["id"],
                "content": r["content"],
                "metadata": r["metadata"],
                "score": score
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma and self._collection is not None:
            ids = [doc.id for doc in docs]
            documents = [doc.content for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]
            metadatas = [doc.metadata for doc in docs]
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            query_res = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "embeddings"]
            )
            formatted = []
            if query_res and "ids" in query_res and len(query_res["ids"]) > 0:
                ids = query_res["ids"][0]
                documents = query_res["documents"][0]
                metadatas = query_res["metadatas"][0]
                embeddings = query_res["embeddings"][0]
                for i in range(len(ids)):
                    score = compute_similarity(query_embedding, embeddings[i])
                    formatted.append({
                        "id": ids[i],
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "score": score
                    })
            return formatted
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            query_res = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter,
                include=["documents", "metadatas", "embeddings"]
            )
            formatted = []
            if query_res and "ids" in query_res and len(query_res["ids"]) > 0:
                ids = query_res["ids"][0]
                documents = query_res["documents"][0]
                metadatas = query_res["metadatas"][0]
                embeddings = query_res["embeddings"][0]
                for i in range(len(ids)):
                    score = compute_similarity(query_embedding, embeddings[i])
                    formatted.append({
                        "id": ids[i],
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "score": score
                    })
            return formatted
        else:
            filtered_records = []
            for r in self._store:
                match = True
                for k, v in metadata_filter.items():
                    if r["metadata"].get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(r)
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            count_before = self._collection.count()
            self._collection.delete(where={"doc_id": doc_id})
            try:
                self._collection.delete(ids=[doc_id])
            except Exception:
                pass
            count_after = self._collection.count()
            return count_after < count_before
        else:
            removed = False
            new_store = []
            for r in self._store:
                if r["metadata"].get("doc_id") == doc_id or r["id"] == doc_id or r["id"].startswith(f"{doc_id}::"):
                    removed = True
                else:
                    new_store.append(r)
            self._store = new_store
            return removed
