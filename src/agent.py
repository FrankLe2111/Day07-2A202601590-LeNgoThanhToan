from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "No relevant context found in the knowledge base."

        context_lines = []
        for i, item in enumerate(results, 1):
            metadata = item.get("metadata", {})
            trace_id = metadata.get("doc_id") or item.get("id", "unknown")
            source = metadata.get("source")
            trace_label = f"{trace_id}"
            if source:
                trace_label = f"{trace_label} | {source}"
            context_lines.append(f"[{i}] ({trace_label}) {item['content']}")

        context = "\n\n".join(context_lines)
        prompt = (
            "Instruction: chỉ dùng context; nói rõ khi context không đủ.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        return self.llm_fn(prompt)
