from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import DeliveryState, Phase, SessionState, SessionStatus, Utterance


@dataclass(frozen=True)
class Decision:
    allowed: bool
    action: str
    reason: str = ""
    next_phase: Phase | None = None


class Controller:
    """Small deterministic rulebook; conversational quality stays with the model."""

    _PHASES = {item.value: item for item in Phase}

    def decide(self, state: SessionState, proposed_action: str) -> Decision:
        action = str(proposed_action).strip().lower()
        if action == "end":
            return Decision(False, action, "model_cannot_end_session")
        if state.status is not SessionStatus.RUNNING:
            return Decision(False, action, "session_not_running")
        if action in {"continue_scene", "wait_user"} and state.phase in {Phase.SCENE, Phase.WAIT_USER}:
            return Decision(True, action, next_phase=Phase.SCENE if action == "continue_scene" else Phase.WAIT_USER)
        if action == "reflect":
            if state.reflection_count >= state.config.reflection_limit:
                return Decision(False, action, "reflection_limit_reached")
            if state.phase not in {Phase.SCENE, Phase.WAIT_USER, Phase.REFLECT}:
                return Decision(False, action, "reflection_not_allowed_in_phase")
            return Decision(True, action, next_phase=Phase.REFLECT)
        if action == "replay":
            if not state.last_completed_utterance_id:
                return Decision(False, action, "replay_source_missing")
            return Decision(True, action, next_phase=Phase.REPLAY)
        if action == "debrief":
            if state.phase is not Phase.DEBRIEF and state.status is not SessionStatus.ENDED:
                return Decision(False, action, "debrief_requires_end")
            return Decision(True, action, next_phase=Phase.DEBRIEF)
        if action in self._PHASES:
            return Decision(False, action, "direct_phase_transition_forbidden")
        return Decision(False, action, "unknown_action")

    def apply(self, state: SessionState, decision: Decision) -> None:
        if not decision.allowed:
            return
        if decision.action == "reflect":
            state.reflection_count += 1
        if decision.next_phase is not None:
            state.phase = decision.next_phase

    def start(self, state: SessionState, now: float) -> None:
        if state.status not in {SessionStatus.PREPARED, SessionStatus.PAUSED}:
            raise ValueError("session cannot be started")
        state.status = SessionStatus.RUNNING
        state.started_at = now
        state.paused_at = None
        if state.phase is Phase.PREPARE:
            state.phase = Phase.SCENE
        self.event(state, "session_started")

    def pause(self, state: SessionState, now: float) -> None:
        if state.status is not SessionStatus.RUNNING or state.started_at is None:
            raise ValueError("session is not running")
        state.active_elapsed_ms += max(0, int((now - state.started_at) * 1000))
        state.status = SessionStatus.PAUSED
        state.paused_at = now
        state.started_at = None
        self.event(state, "session_paused")

    def resume(self, state: SessionState, now: float) -> None:
        self.start(state, now)
        self.event(state, "session_resumed")

    def end(self, state: SessionState, reason: str = "manual") -> None:
        state.status = SessionStatus.ENDED
        state.phase = Phase.DEBRIEF
        state.started_at = None
        state.ended_reason = reason
        self.event(state, "session_ended", {"reason": reason})

    def record_utterance(self, state: SessionState, utterance: Utterance) -> None:
        state.utterances.append(utterance)
        if utterance.delivery_state is DeliveryState.COMPLETED:
            state.last_completed_utterance_id = utterance.utterance_id
        self.event(state, "utterance_recorded", {"utterance_id": utterance.utterance_id})

    def record_delivery(self, state: SessionState, utterance_id: str, delivery_state: DeliveryState) -> None:
        for utterance in state.utterances:
            if utterance.utterance_id == utterance_id:
                utterance.delivery_state = delivery_state
                if delivery_state is DeliveryState.COMPLETED:
                    state.last_completed_utterance_id = utterance_id
                self.event(state, "utterance_delivery", {"utterance_id": utterance_id, "state": delivery_state.value})
                return
        raise ValueError("unknown utterance")

    @staticmethod
    def event(state: SessionState, event_type: str, payload: dict[str, Any] | None = None) -> None:
        state.events.append({"sequence": len(state.events) + 1, "type": event_type, "payload": payload or {}})

    @staticmethod
    def snapshot(state: SessionState) -> dict[str, Any]:
        return {
            "session_id": state.session_id,
            "status": state.status.value,
            "phase": state.phase.value,
            "remaining_seconds": state.remaining_seconds,
            "remaining_display": state.remaining_display,
            "reflection_count": state.reflection_count,
            "reflection_limit": state.config.reflection_limit,
            "requirements": [item.__dict__ for item in state.requirements],
            "last_completed_utterance_id": state.last_completed_utterance_id,
            "goal": state.config.goal,
            "scenario": state.config.scenario,
            "protocol_id": state.config.protocol_id,
        }
