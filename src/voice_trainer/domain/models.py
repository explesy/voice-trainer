from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class SessionStatus(StrEnum):
    PREPARED = "prepared"
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"


class Phase(StrEnum):
    PREPARE = "prepare"
    SCENE = "scene"
    WAIT_USER = "wait_user"
    REFLECT = "reflect"
    REPLAY = "replay"
    DEBRIEF = "debrief"
    END = "end"


class DeliveryState(StrEnum):
    APPROVED = "approved"
    STARTED = "started"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    FAILED = "failed"


@dataclass(frozen=True)
class Requirement:
    id: str
    label: str
    completed: bool = False


@dataclass(frozen=True)
class SessionConfig:
    duration_seconds: int = 900
    goal: str = ""
    scenario: str = ""
    requirements: tuple[Requirement, ...] = ()
    reflection_limit: int = 2
    protocol_id: str = "basic-scene"

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if self.reflection_limit < 0:
            raise ValueError("reflection_limit cannot be negative")


@dataclass
class Utterance:
    utterance_id: str
    text: str
    source_turn_id: str
    created_at: float
    delivery_state: DeliveryState = DeliveryState.APPROVED


@dataclass
class SessionState:
    session_id: str
    config: SessionConfig
    status: SessionStatus = SessionStatus.PREPARED
    phase: Phase = Phase.PREPARE
    active_elapsed_ms: int = 0
    started_at: float | None = None
    paused_at: float | None = None
    reflection_count: int = 0
    requirements: list[Requirement] = field(default_factory=list)
    utterances: list[Utterance] = field(default_factory=list)
    last_completed_utterance_id: str | None = None
    ended_reason: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.requirements:
            self.requirements = list(self.config.requirements)

    @property
    def remaining_seconds(self) -> int:
        return max(0, self.config.duration_seconds - self.active_elapsed_ms // 1000)

    @property
    def remaining_display(self) -> str:
        seconds = self.remaining_seconds
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["phase"] = self.phase.value
        data["config"]["requirements"] = [asdict(item) for item in self.config.requirements]
        data["requirements"] = [asdict(item) for item in self.requirements]
        data["utterances"] = [
            {**asdict(item), "delivery_state": item.delivery_state.value}
            for item in self.utterances
        ]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        config_data = dict(data["config"])
        config_data["requirements"] = tuple(Requirement(**item) for item in config_data.get("requirements", []))
        state = cls(
            session_id=str(data["session_id"]),
            config=SessionConfig(**config_data),
            status=SessionStatus(data.get("status", SessionStatus.PREPARED)),
            phase=Phase(data.get("phase", Phase.PREPARE)),
            active_elapsed_ms=int(data.get("active_elapsed_ms", 0)),
            started_at=data.get("started_at"),
            paused_at=data.get("paused_at"),
            reflection_count=int(data.get("reflection_count", 0)),
            requirements=[Requirement(**item) for item in data.get("requirements", [])],
            utterances=[
                Utterance(**{**item, "delivery_state": DeliveryState(item.get("delivery_state", "approved"))})
                for item in data.get("utterances", [])
            ],
            last_completed_utterance_id=data.get("last_completed_utterance_id"),
            ended_reason=data.get("ended_reason"),
            events=list(data.get("events", [])),
        )
        return state
