"""RAG retriever with context formatting for agent prompts."""

import structlog

from src.config import get_settings, load_agent_config
from src.rag.keyword_search import search_faq
from src.rag.vector_store import VectorStore, tenant_collection_name
from src.request_context import get_request_tenant_id

logger = structlog.get_logger()


class KnowledgeRetriever:
    def __init__(self, vector_store: VectorStore | None = None, tenant_id: str = ""):
        tid = tenant_id or get_request_tenant_id() or "default"
        self.tenant_id = tid
        self.store = vector_store or VectorStore(
            collection_name=tenant_collection_name(tid),
            tenant_id=tid,
        )
        self.config = load_agent_config()["rag"]
        self._use_keyword_fallback = not bool(get_settings().openai_api_key)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        top_k = top_k or self.config["top_k"]
        try:
            results = self.store.similarity_search(query, k=top_k)
        except Exception as exc:
            logger.warning("vector_search_failed_using_keyword_fallback", error=str(exc))
            results = []
        if not results:
            results = search_faq(query, top_k=top_k)
        return results

    def format_context(self, query: str) -> str:
        results = self.retrieve(query)
        if not results:
            return "No relevant knowledge base articles found."

        parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "unknown")
            parts.append(
                f"[{i}] (relevance: {result['score']:.2f}, source: {source})\n"
                f"{result['content']}"
            )
        return "\n\n".join(parts)
