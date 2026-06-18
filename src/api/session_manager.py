"""TTL-backed session store for chat orchestrators."""

import time
from dataclasses import dataclass, field

from src.workflows.orchestrator import AgentOrchestrator


@dataclass
class SessionEntry:
    orchestrator: AgentOrchestrator
    agent_id: str
    last_access: float = field(default_factory=time.time)


class SessionManager:
    """Manages orchestrator sessions with TTL eviction and max-size bounds."""

    def __init__(self, ttl_seconds: int = 3600, max_sessions: int = 1000) -> None:
        self._sessions: dict[str, SessionEntry] = {}
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions

    def get(self, session_id: str, agent_id: str) -> AgentOrchestrator:
        self.evict_stale()
        entry = self._sessions.get(session_id)
        if entry is None or entry.agent_id != agent_id:
            entry = SessionEntry(orchestrator=AgentOrchestrator(agent_id), agent_id=agent_id)
            self._sessions[session_id] = entry
        entry.last_access = time.time()
        return entry.orchestrator

    def remove(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def evict_stale(self) -> int:
        """Remove expired sessions. Returns count evicted."""
        now = time.time()
        stale_ids = [
            sid
            for sid, entry in self._sessions.items()
            if now - entry.last_access > self.ttl_seconds
        ]
        for sid in stale_ids:
            del self._sessions[sid]

        if len(self._sessions) > self.max_sessions:
            overflow = len(self._sessions) - self.max_sessions
            oldest = sorted(self._sessions.items(), key=lambda item: item[1].last_access)
            for sid, _ in oldest[:overflow]:
                del self._sessions[sid]
            stale_ids.extend(sid for sid, _ in oldest[:overflow])

        return len(stale_ids)

    @property
    def active_count(self) -> int:
        return len(self._sessions)
