import json

import pytest

from voice_trainer.application.context_assembler import ContextAssembler
from voice_trainer.domain import Controller, Phase, Requirement, SessionConfig, SessionState, SessionStatus
from app.plugin_storage import PluginStorage
from app.plugin_api import TurnContext
from voice_trainer.plugin import ResponseCandidate
from voice_trainer import VoiceTrainerPlugin


def make_state() -> SessionState:
    return SessionState(
        "s1",
        SessionConfig(duration_seconds=120, goal="listen", scenario="meeting", requirements=(Requirement("r1", "Ask one question"),), reflection_limit=1),
    )


def test_controller_blocks_model_end_and_reflection_over_limit():
    state = make_state()
    controller = Controller()
    controller.start(state, 10.0)
    assert controller.decide(state, "end").reason == "model_cannot_end_session"
    state.reflection_count = 1
    assert controller.decide(state, "reflect").reason == "reflection_limit_reached"


def test_manual_end_enters_debrief_and_restart_is_paused():
    state = make_state()
    controller = Controller()
    controller.start(state, 10.0)
    controller.end(state)
    assert state.status is SessionStatus.ENDED
    assert state.phase is Phase.DEBRIEF
    restored = SessionState.from_dict(json.loads(json.dumps(state.to_dict())))
    assert restored.phase is Phase.DEBRIEF


def test_context_contains_authoritative_snapshot_and_timer():
    state = make_state()
    controller = Controller()
    controller.start(state, 10.0)
    context = ContextAssembler(controller).build(state, user_message="Hello", recent_turns=[])
    assert "Remaining time: 02:00 (120 seconds)" in context
    assert "The session state and rules above are authoritative." in context
    assert "CURRENT USER MESSAGE: Hello" in context


@pytest.mark.anyio
async def test_plugin_gate_accepts_structured_allowed_action(tmp_path):
    plugin = VoiceTrainerPlugin()
    state = PluginStorage(tmp_path / "plugin.sqlite3").for_plugin("training", "conv")
    await plugin.action("start_session", {}, state)
    decision = await plugin.validate_response(
        TurnContext("conv", "hello", [], metadata={"plugin_settings": {}}, state=state),
        ResponseCandidate("conv", "hello", '{"spoken_text":"Try again.","proposed_action":"continue_scene"}'),
    )
    assert decision.action == "allow"
    assert decision.text == "Try again."
