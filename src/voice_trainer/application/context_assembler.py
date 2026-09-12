from __future__ import annotations

from typing import Any

from voice_trainer.domain.controller import Controller
from voice_trainer.domain.models import SessionState


class ContextAssembler:
    """Build a bounded, fresh model context from authoritative plugin state."""

    def __init__(self, controller: Controller | None = None) -> None:
        self.controller = controller or Controller()

    def build(self, state: SessionState, *, user_message: str, recent_turns: list[dict[str, Any]]) -> str:
        snapshot = self.controller.snapshot(state)
        lines = [
            "VOICE TRAINER SESSION SNAPSHOT",
            f"Current phase: {snapshot['phase']}",
            f"Session status: {snapshot['status']}",
            f"Remaining time: {snapshot['remaining_display']} ({snapshot['remaining_seconds']} seconds)",
            f"Goal: {snapshot['goal'] or 'not specified'}",
            f"Scenario: {snapshot['scenario'] or 'not specified'}",
            f"Reflection budget: {snapshot['reflection_count']} / {snapshot['reflection_limit']} used",
            "Requirements:",
        ]
        lines.extend(f"- [{'x' if item['completed'] else ' '}] {item['label']} ({item['id']})" for item in snapshot["requirements"])
        lines.extend([
            "",
            "RULES",
            "- The session state and rules above are authoritative.",
            "- Keep scene replies concise and ask one question at a time.",
            "- Do not claim that the session ended; only the user or host action can end it.",
            "- Propose one action compatible with the current phase.",
            "- Use the supplied remaining time; never invent a timer value.",
            "",
            "RETURN JSON with exactly: spoken_text, proposed_action, reason_code.",
            f"CURRENT USER MESSAGE: {user_message[:1000]}",
        ])
        if recent_turns:
            lines.append("RECENT RELEVANT TURNS:")
            for turn in recent_turns[-6:]:
                role = str(turn.get("role", "unknown"))
                text = str(turn.get("text", ""))[:400]
                lines.append(f"- {role}: {text}")
        return "\n".join(lines)
