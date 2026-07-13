"""Keyword-based FAQ search for offline/mock mode when vector scores are unreliable."""

import re
from functools import lru_cache
from src.config import DATA_DIR


@lru_cache
def load_faq_entries() -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    kb_dir = DATA_DIR / "knowledge_base"
    if not kb_dir.exists():
        return tuple()

    for path in sorted(kb_dir.glob("**/*")):
        if path.suffix not in {".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"Q:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\n##|\Z)", text, re.DOTALL):
            entries.append({
                "question": match.group(1).strip(),
                "answer": re.sub(r"\s+", " ", match.group(2).strip()),
                "source": str(path),
            })
    return tuple(entries)


def _tokenize(text: str) -> set[str]:
    stop = {
        "a", "an", "the", "to", "my", "i", "do", "how", "can", "you", "is", "are",
        "for", "me", "what", "when", "where", "why", "with", "your", "our", "and",
        "or", "of", "in", "on", "at", "it", "this", "that",
    }
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in stop and len(w) > 2}


def search_faq(query: str, top_k: int = 3) -> list[dict]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored: list[tuple[float, dict]] = []
    for entry in load_faq_entries():
        q_tokens = _tokenize(entry["question"])
        a_tokens = _tokenize(entry["answer"])
        overlap_q = len(query_tokens & q_tokens)
        overlap_a = len(query_tokens & a_tokens)
        # Require at least one question-token hit so answer-body noise can't win.
        if overlap_q == 0:
            continue
        score = overlap_q * 4.0 + overlap_a * 0.35
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, entry in scored[:top_k]:
        results.append({
            "content": f"Q: {entry['question']}\nA: {entry['answer']}",
            "metadata": {"source": entry["source"], "question": entry["question"]},
            "score": min(score / max(len(query_tokens) * 4.0, 1.0), 1.0),
            "answer": entry["answer"],
            "raw_score": score,
        })
    return results


def best_answer(query: str, *, min_score: float = 0.35) -> str | None:
    """Return the best FAQ answer only when match quality is strong enough."""
    results = search_faq(query, top_k=1)
    if not results:
        return None
    if results[0]["score"] < min_score:
        return None
    return results[0]["answer"]
