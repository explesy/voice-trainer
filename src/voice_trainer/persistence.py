from __future__ import annotations

import json
from typing import Any

from .domain.models import SessionState


class SessionRepository:
    """Stores one serialized session in host-provided PluginState."""

    KEY = "active_session"

    async def load(self, state: Any) -> SessionState | None:
        if state is None:
            return None
        raw = await state.get(self.KEY)
        if not raw:
            return None
        try:
            value = json.loads(raw)
            return SessionState.from_dict(value) if isinstance(value, dict) else None
        except (TypeError, ValueError, KeyError):
            return None

    async def save(self, state: Any, session: SessionState) -> None:
        if state is not None:
            await state.set(self.KEY, json.dumps(session.to_dict(), ensure_ascii=False, separators=(",", ":")))

    async def clear(self, state: Any) -> None:
        if state is not None:
            await state.delete(self.KEY)
