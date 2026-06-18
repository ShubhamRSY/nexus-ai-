"""Tests for vector store relevance score handling."""

from langchain_core.documents import Document

from src.rag.vector_store import _filter_vector_hits, _normalize_relevance_scores


class TestRelevanceScoreNormalization:
    def test_maps_out_of_range_scores_to_unit_interval(self):
        docs = [
            (Document(page_content="a"), -0.5),
            (Document(page_content="b"), 1.5),
            (Document(page_content="c"), 0.2),
        ]
        normalized = _normalize_relevance_scores(docs)
        scores = [score for _, score in normalized]
        assert min(scores) == 0.0
        assert max(scores) == 1.0

    def test_keeps_valid_scores_unchanged(self):
        docs = [
            (Document(page_content="a"), 0.8),
            (Document(page_content="b"), 0.9),
        ]
        normalized = _normalize_relevance_scores(docs)
        assert [score for _, score in normalized] == [0.8, 0.9]

    def test_threshold_does_not_drop_all_chroma_hits(self):
        docs = [(Document(page_content="password reset steps"), -2.0)]
        hits = _filter_vector_hits(docs, threshold=0.7)
        assert len(hits) == 1
        assert hits[0]["content"] == "password reset steps"
        assert hits[0]["score"] == 1.0

    def test_threshold_filters_when_scores_are_comparable(self):
        docs = [
            (Document(page_content="strong match"), 0.95),
            (Document(page_content="weak match"), 0.4),
        ]
        hits = _filter_vector_hits(docs, threshold=0.7)
        assert len(hits) == 1
        assert hits[0]["content"] == "strong match"
