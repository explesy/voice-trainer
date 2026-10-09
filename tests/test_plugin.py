from app.plugin_storage import PluginStorage
from app.plugin_api import ToolCallContext, TurnContext
import pytest

from voice_trainer import VoiceTrainerPlugin


@pytest.mark.anyio
async def test_plugin_persists_state_and_uses_host_storage(tmp_path):
    plugin = VoiceTrainerPlugin()
    state = PluginStorage(tmp_path / "plugins.sqlite3").for_plugin("training", "conv-1")
    result = await plugin.before_turn(
        TurnContext("conv-1", "Practise", [], active_mode="practice", metadata={"plugin_settings": {"skill": "listening"}}, state=state)
    )
    assert "Current skill: listening" in result.prompt_context
    await plugin.after_turn(TurnContext("conv-1", "Practise", [], active_mode="practice", state=state), "Keep going")
    assert "Keep going" in (await state.get("recent_sessions"))

    storage = PluginStorage(tmp_path / "tools.sqlite3")
    context = ToolCallContext("conv-1", "training", "practice", metadata={"tool_qualified_name": "training.observe", "project_scope": "project"}, storage=storage)
    observed = await plugin.call_tool("training.observe", {"text": "Good pacing"}, context)
    assert "Recorded training observation" in observed.content_items[0]["text"]


@pytest.mark.anyio
async def test_plugin_action_start_session_idempotent_and_syncs_settings(tmp_path):
    plugin = VoiceTrainerPlugin()
    state = PluginStorage(tmp_path / "plugins.sqlite3").for_plugin("training", "conv-2")

    # Start session with settings
    res1 = await plugin.action(
        "start_session",
        {"scenario": "Negotiations with director", "goal": "Find true reason", "duration_seconds": 300},
        state=state,
    )
    assert res1["ok"] is True
    assert res1["session"]["status"] == "running"
    assert res1["session"]["scenario"] == "Negotiations with director"
    assert res1["session"]["goal"] == "Find true reason"
    assert res1["session"]["remaining_seconds"] == 300

    # Repeat start_session must be idempotent and not raise ValueError
    res2 = await plugin.action(
        "start_session",
        {"scenario": "Updated scenario", "goal": "Find true reason"},
        state=state,
    )
    assert res2["ok"] is True
    assert res2["session"]["status"] == "running"
    assert res2["session"]["scenario"] == "Updated scenario"

