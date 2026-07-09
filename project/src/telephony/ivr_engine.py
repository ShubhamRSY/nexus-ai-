"""Execute stored visual IVR flows on voice calls."""

from __future__ import annotations

from typing import Any

import structlog

from src.database import db

logger = structlog.get_logger()


class IvrEngine:
    """Walks a node graph: prompt → menu (DTMF) → AI → transfer."""

    def __init__(self, flow: dict):
        self.flow = flow
        self.nodes = {n["id"]: n for n in flow.get("nodes", [])}
        self.entry = flow.get("entry_node", "start")

    def get_node(self, node_id: str) -> dict | None:
        return self.nodes.get(node_id)

    def render_twiml_prompt(self, node_id: str) -> tuple[str, str]:
        """Return (prompt_text, next_node_id) for Say/Gather."""
        node = self.get_node(node_id) or self.get_node(self.entry) or {}
        ntype = node.get("type", "prompt")
        text = node.get("text", "Welcome. Please hold.")
        if ntype == "menu":
            options = node.get("options", {})
            menu_text = text + " " + " ".join(f"Press {k} for {v.get('label', '')}." for k, v in options.items())
            return menu_text, node_id
        nxt = node.get("next", "")
        return text, nxt

    def route_digit(self, node_id: str, digit: str) -> str | None:
        node = self.get_node(node_id)
        if not node or node.get("type") != "menu":
            return None
        opt = node.get("options", {}).get(digit)
        return opt.get("next") if opt else node.get("default_next")

    def node_action(self, node_id: str) -> dict[str, Any]:
        node = self.get_node(node_id) or {}
        return {
            "type": node.get("type", "prompt"),
            "transfer_number": node.get("transfer_number", ""),
            "agent_id": node.get("agent_id", "voice_support"),
            "text": node.get("text", ""),
            "next": node.get("next", ""),
        }


def get_active_engine(tenant_id: str = "default") -> IvrEngine | None:
    flow = db.get_active_ivr_flow(tenant_id)
    if not flow:
        return None
    return IvrEngine(flow)
