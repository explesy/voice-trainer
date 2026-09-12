from __future__ import annotations

from typing import Any

from voice_trainer.domain.models import SessionState


def build_debrief(state: SessionState) -> dict[str, Any]:
    """Return controller facts only; model interpretation is kept separate."""
    return {
        "session_id": state.session_id,
        "ended_reason": state.ended_reason,
        "phase": state.phase.value,
        "duration_seconds": state.config.duration_seconds,
        "active_elapsed_seconds": state.active_elapsed_ms // 1000,
        "reflections": state.reflection_count,
        "requirements_completed": sum(item.completed for item in state.requirements),
        "requirements_total": len(state.requirements),
        "replays": sum(item.get("type") == "replay_requested" for item in state.events),
        "rejected_actions": sum(item.get("type") == "controller_decision" and not item.get("payload", {}).get("allowed", True) for item in state.events),
    }
