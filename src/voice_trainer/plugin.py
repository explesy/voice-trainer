"""Standalone Voice Trainer plugin for the Voice of Luna host."""

from __future__ import annotations

from dataclasses import replace
import json
import re
import time
from typing import Any
from uuid import uuid4

from app.plugin_api import Plugin, PluginTurnResult, ToolCallContext, ToolResult, ToolSpec, TurnContext
try:  # The released host may lag while this standalone package is developed.
    from app.plugin_api import OutputEvent, ResponseCandidate, ResponseDecision
except ImportError:  # pragma: no cover - compatibility with host <= 0.34
    from dataclasses import dataclass, field

    @dataclass(frozen=True)
    class OutputEvent:
        conversation_id: str
        turn_id: str
        clip_id: str
        state: str
        delivered_text: str | None = None
        metadata: dict[str, Any] = field(default_factory=dict)

    @dataclass(frozen=True)
    class ResponseCandidate:
        conversation_id: str
        user_message: str
        text: str
        metadata: dict[str, Any] = field(default_factory=dict)

    @dataclass(frozen=True)
    class ResponseDecision:
        action: str = "allow"
        text: str | None = None
        reason: str = ""
        metadata: dict[str, Any] = field(default_factory=dict)

from .application.context_assembler import ContextAssembler
from .application.debrief import build_debrief
from .domain import Controller, Phase, Requirement, SessionConfig, SessionState, SessionStatus
from .persistence import SessionRepository


def _text(value: Any) -> dict[str, str]:
    return {"type": "text", "text": str(value)}


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        lines = raw.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
            raw = "\n".join(lines[1:-1]).strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except (TypeError, ValueError):
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except (TypeError, ValueError):
            pass
    return None


class VoiceTrainerPlugin(Plugin):
    """Model-led conversation with authoritative, persisted session context."""

    id = "training"
    name = "Voice Trainer"
    description = "A private, stateful practice and reflection workspace"
    delivery_mode = "gated"

    def __init__(self) -> None:
        self.repository = SessionRepository()
        self.controller = Controller()
        self.context_assembler = ContextAssembler(self.controller)
        self._last_output_event: OutputEvent | None = None

    async def configure(self, settings: dict[str, Any]) -> dict[str, Any]:
        goal = str(settings.get("goal", "")).strip()[:240]
        scenario = str(settings.get("scenario", "")).strip()[:1000]
        skill = str(settings.get("skill", "general")).strip()[:80] or "general"
        try:
            duration = max(60, min(7200, int(settings.get("duration_seconds", 900))))
            reflection_limit = max(0, min(20, int(settings.get("reflection_limit", 2))))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid training duration or reflection limit") from exc
        raw_requirements = settings.get("requirements", [])
        requirements = []
        if isinstance(raw_requirements, list):
            for index, item in enumerate(raw_requirements[:20]):
                label = str(item).strip()[:200]
                if label:
                    requirements.append({"id": f"requirement-{index + 1}", "label": label})
        return {
            "skill": skill,
            "goal": goal,
            "scenario": scenario,
            "duration_seconds": duration,
            "reflection_limit": reflection_limit,
            "requirements": requirements,
            "protocol_id": str(settings.get("protocol_id", "basic-scene"))[:80],
        }

    def panel_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "fields": [
                {"name": "skill", "type": "text", "label": "Skill", "placeholder": "conversation"},
                {"name": "goal", "type": "text", "label": "Session goal", "placeholder": "Describe what to practise"},
                {"name": "duration_seconds", "type": "number", "label": "Duration (seconds)", "placeholder": "900"},
                {"name": "scenario", "type": "textarea", "label": "Scenario", "placeholder": "Describe the scene"},
            ],
            "actions": [
                {"name": "start_session", "label": "Start"},
                {"name": "pause_session", "label": "Pause"},
                {"name": "resume_session", "label": "Resume"},
                {"name": "end_session", "label": "End"},
                {"name": "reset", "label": "Reset session"},
            ],
        }

    def get_modes(self) -> list[dict[str, str]]:
        return [{"id": "training", "label": "Training"}, {"id": "free", "label": "Free dialogue"}]

    async def _get_or_create(self, ctx: TurnContext) -> SessionState:
        session = await self.repository.load(ctx.state)
        if session is not None:
            return session
        settings = ctx.metadata.get("plugin_settings", {})
        requirements = tuple(Requirement(**item) for item in settings.get("requirements", []) if isinstance(item, dict))
        config = SessionConfig(
            duration_seconds=int(settings.get("duration_seconds", 900)),
            goal=str(settings.get("goal", "")),
            scenario=str(settings.get("scenario", "")),
            requirements=requirements,
            reflection_limit=int(settings.get("reflection_limit", 2)),
            protocol_id=str(settings.get("protocol_id", "basic-scene")),
        )
        session = SessionState(session_id=f"{ctx.conversation_id}:{uuid4().hex[:8]}", config=config)
        await self.repository.save(ctx.state, session)
        return session

    async def before_turn(self, ctx: TurnContext) -> PluginTurnResult:
        session = await self._get_or_create(ctx)
        if session.status is SessionStatus.PREPARED:
            self.controller.start(session, time.monotonic())
        settings = ctx.metadata.get("plugin_settings", {})
        prompt = self.context_assembler.build(session, user_message=ctx.user_message, recent_turns=ctx.turns_history)
        prompt = f"Current skill: {str(settings.get('skill', 'general'))}\n" + prompt
        self.controller.event(session, "model_context_issued", {"phase": session.phase.value, "remaining_seconds": session.remaining_seconds})
        await self.repository.save(ctx.state, session)
        return PluginTurnResult(
            prompt_context=prompt,
            mode_label=f"TRAINING // {session.phase.value.upper()}",
            metadata={"turn_taking_profile": "patient" if session.phase.value == "wait_user" else "normal", "session_id": session.session_id},
        )

    async def after_turn(self, ctx: TurnContext, assistant_response: str) -> None:
        session = await self._get_or_create(ctx)
        self.controller.event(session, "model_response_observed", {"text": assistant_response[:2000], "user_message": ctx.user_message[:1000]})
        await self.repository.save(ctx.state, session)
        # Compatibility view for older host panels and installations.
        if ctx.state is not None:
            raw = await ctx.state.get("recent_sessions")
            try:
                recent = json.loads(raw) if raw else []
            except (TypeError, ValueError):
                recent = []
            recent = recent if isinstance(recent, list) else []
            recent.append({"at": int(time.time()), "mode": ctx.active_mode, "user": ctx.user_message[:240], "assistant": assistant_response[:240]})
            await ctx.state.set("recent_sessions", json.dumps(recent[-20:], ensure_ascii=False))

    async def validate_response(self, ctx: TurnContext, candidate: ResponseCandidate) -> ResponseDecision:
        """Validate the model's proposal while leaving conversational quality to the model."""
        session = await self._get_or_create(ctx)
        if session.status is SessionStatus.PREPARED:
            self.controller.start(session, time.monotonic())

        payload = _extract_json_payload(candidate.text)
        if payload is None:
            clean_text = candidate.text.strip()
            if clean_text and not clean_text.startswith("{"):
                action = "continue_scene" if session.phase in {Phase.SCENE, Phase.WAIT_USER} else "reflect"
                payload = {
                    "spoken_text": clean_text,
                    "proposed_action": action,
                    "reason_code": "fallback_plain_text",
                }
            else:
                return ResponseDecision(action="reject", reason="invalid_json_response")

        if not isinstance(payload, dict):
            return ResponseDecision(action="reject", reason="response_not_object")
        spoken = payload.get("spoken_text")
        action = payload.get("proposed_action")
        if not isinstance(spoken, str) or not spoken.strip() or not isinstance(action, str):
            return ResponseDecision(action="reject", reason="response_schema_invalid")

        decision = self.controller.decide(session, action)
        self.controller.event(session, "controller_decision", {"action": action, "allowed": decision.allowed, "reason": decision.reason})
        await self.repository.save(ctx.state, session)
        if not decision.allowed:
            return ResponseDecision(action="reject", reason=decision.reason)
        self.controller.apply(session, decision)
        await self.repository.save(ctx.state, session)
        return ResponseDecision(action="allow", text=spoken.strip(), metadata={"proposed_action": action, "reason_code": payload.get("reason_code", "")})

    async def on_output_event(self, event: OutputEvent) -> None:
        """Record delivery facts without claiming that interrupted audio was heard."""
        # The host currently delivers a generic event without a state facade.
        # Keep the event in memory for the next context; persistence is done by
        # the subsequent before_turn through the host-provided state.
        self._last_output_event = event

    async def action(self, name: str, settings: dict[str, Any], state: Any = None) -> dict[str, Any]:
        if state is None:
            raise ValueError("Training state is unavailable")
        session = await self.repository.load(state)
        if name == "reset":
            await self.repository.clear(state)
            return {"ok": True, "action": name}

        def _sync_config(target_config: SessionConfig) -> SessionConfig:
            if not isinstance(settings, dict):
                return target_config
            updates: dict[str, Any] = {}
            if "goal" in settings and str(settings["goal"]).strip():
                updates["goal"] = str(settings["goal"]).strip()[:240]
            if "scenario" in settings and str(settings["scenario"]).strip():
                updates["scenario"] = str(settings["scenario"]).strip()[:1000]
            if "duration_seconds" in settings:
                try:
                    updates["duration_seconds"] = max(60, min(7200, int(settings["duration_seconds"])))
                except (TypeError, ValueError):
                    pass
            if "reflection_limit" in settings:
                try:
                    updates["reflection_limit"] = max(0, min(20, int(settings["reflection_limit"])))
                except (TypeError, ValueError):
                    pass
            return replace(target_config, **updates) if updates else target_config

        if session is None:
            config = _sync_config(SessionConfig())
            session = SessionState(session_id=f"{state.conversation_id}:{uuid4().hex[:8]}", config=config)
            await self.repository.save(state, session)
        now = time.monotonic()
        if name == "start_session":
            session.config = _sync_config(session.config)
            if session.status is SessionStatus.RUNNING:
                pass
            else:
                self.controller.start(session, now)
        elif name == "pause_session":
            self.controller.pause(session, now)
        elif name == "resume_session":
            if session.status is SessionStatus.RUNNING:
                pass
            else:
                self.controller.resume(session, now)
        elif name == "end_session":
            self.controller.end(session, "manual")
        elif name == "open_debrief":
            if session.status.value != "ended":
                raise ValueError("Debrief requires an ended session")
            return {"ok": True, "action": name, "debrief": build_debrief(session)}
        elif name == "request_repeat_last_line":
            source = next((item for item in reversed(session.utterances) if item.delivery_state.value == "completed"), None)
            if source is None:
                raise ValueError("No completed trainer line to repeat")
            return {"ok": True, "action": name, "speak_request": {"text": source.text, "source_utterance_id": source.utterance_id}}
        elif name == "report_protocol_issue":
            self.controller.event(session, "protocol_issue_reported", {"details": str(settings.get("details", ""))[:1000]})
        else:
            raise ValueError(f"Unknown Training action: {name}")
        await self.repository.save(state, session)
        return {"ok": True, "action": name, "session": self.controller.snapshot(session)}

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec("training", "status", "Read the authoritative current training session status and timer.", {"type": "object"}, "storage.read"),
            ToolSpec("training", "history", "Read recent training observations.", {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 20}}}, "storage.read"),
            ToolSpec("training", "observe", "Record a short, explicitly stated training observation.", {"type": "object", "properties": {"text": {"type": "string", "maxLength": 500}}, "required": ["text"]}, "storage.write"),
            ToolSpec("training", "progress", "Summarize current training progress.", {"type": "object"}, "storage.read"),
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any], ctx: ToolCallContext) -> ToolResult:
        storage = ctx.storage
        if storage is None:
            raise RuntimeError("Training storage is unavailable")
        qualified = str(ctx.metadata.get("tool_qualified_name", name))
        scope = str(ctx.metadata.get("project_scope", "plugin"))
        if qualified == "training.status":
            raw = await storage.get(self.id, f"conversation:{ctx.conversation_id}", SessionRepository.KEY)
            if not raw:
                return ToolResult(content_items=[_text("No active training session.")])
            try:
                session = SessionState.from_dict(json.loads(raw))
                return ToolResult(content_items=[_text(json.dumps(self.controller.snapshot(session), ensure_ascii=False))])
            except (TypeError, ValueError, KeyError):
                return ToolResult(content_items=[_text("Training session state is unavailable.")], success=False)
        if qualified == "training.history":
            rows = await storage.recent(self.id, scope, int(arguments.get("limit", 8)))
            return ToolResult(content_items=[_text(rows or "No training observations recorded.")])
        if qualified == "training.observe":
            text = str(arguments["text"]).strip()[:500]
            doc_id = await storage.remember(self.id, scope, text, "observation", [])
            return ToolResult(content_items=[_text(f"Recorded training observation #{doc_id}.")])
        if qualified == "training.progress":
            rows = await storage.recent(self.id, scope, 20)
            return ToolResult(content_items=[_text(f"Training observations recorded: {len(rows)}")])
        raise ValueError(f"Unknown Training tool: {qualified}")
