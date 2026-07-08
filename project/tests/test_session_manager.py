"""Tests for session TTL eviction and bounds."""

import time

from src.api.session_manager import SessionManager


class TestSessionManager:
    def test_get_creates_session(self):
        mgr = SessionManager(ttl_seconds=60)
        orch = mgr.get("sess-1", "chat_support")
        assert orch.agent_id == "chat_support"
        assert mgr.active_count == 1

    def test_remove_session(self):
        mgr = SessionManager()
        mgr.get("sess-1", "chat_support")
        assert mgr.remove("sess-1") is True
        assert mgr.active_count == 0

    def test_evict_stale_sessions(self):
        mgr = SessionManager(ttl_seconds=1, max_sessions=10)
        mgr.get("stale", "chat_support")
        mgr._sessions["stale"].last_access = time.time() - 10
        evicted = mgr.evict_stale()
        assert evicted >= 1
        assert mgr.active_count == 0

    def test_max_sessions_eviction(self):
        mgr = SessionManager(ttl_seconds=3600, max_sessions=2)
        mgr.get("a", "chat_support")
        time.sleep(0.01)
        mgr.get("b", "chat_support")
        time.sleep(0.01)
        mgr.get("c", "chat_support")
        mgr.evict_stale()
        assert mgr.active_count <= 2

    def test_agent_change_recreates_session(self):
        mgr = SessionManager()
        first = mgr.get("sess", "chat_support")
        second = mgr.get("sess", "copilot")
        assert first is not second
        assert second.agent_id == "copilot"
