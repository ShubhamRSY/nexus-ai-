"""Guardrails: marketing landing must not regress to old mock UI."""

from pathlib import Path

LANDING = Path(__file__).resolve().parents[1] / "static" / "landing.html"
LOGO = Path(__file__).resolve().parents[1] / "static" / "nexus-logo.svg"


def test_landing_has_no_mock_chat_copy() -> None:
    html = LANDING.read_text(encoding="utf-8")
    assert "order #4821" not in html
    assert "mock-chat" not in html
    assert "mock-bubble" not in html


def test_landing_has_deliver_grid_and_integration_lake() -> None:
    html = LANDING.read_text(encoding="utf-8")
    assert "showcase-tab" in html
    assert "deliver-panel" in html
    assert "integration-lake" in html
    assert "marquee-track" in html
    assert html.count("lake-pill") >= 124


def test_logo_uses_geometric_n_not_font_text() -> None:
    svg = LOGO.read_text(encoding="utf-8")
    assert "<text" not in svg.lower()
    assert 'd="M16 48V16' in svg or "letter N" in svg
