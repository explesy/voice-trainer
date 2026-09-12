# Voice Trainer — Architecture

## Purpose

Voice Trainer is a standalone training product that currently runs as a trusted external plugin inside Voice of Luna.

The architectural goal is to keep training semantics independently testable while reusing the host's generic voice/conversation infrastructure.

## Ownership boundary

### Voice Trainer owns

- training session model and phases;
- deterministic transition rules;
- training-specific validation and invariants;
- reflection/replay/debrief semantics;
- training-specific configuration and tests;
- bounded plugin operational state;
- translation between host events and trainer-domain commands/results.

### Voice of Luna owns

- microphone/browser transport;
- STT and TTS;
- model/Codex conversation transport;
- interruption/barge-in infrastructure;
- external plugin discovery and lifecycle;
- generic plugin settings, actions, tools, state/storage contexts and capability checks;
- generic UI shell.

Voice of Luna must not need knowledge of training phases, reflection limits, replay policy, session requirements, or personal training content.

## Target layers

The intended direction is:

```text
voice_trainer/
  domain/
    model.py
    controller.py
    rules.py
  application/
    session.py
    debrief.py
  integration/
    voice_of_luna.py
  plugin.py (temporary/simple facade or compatibility export)
```

Exact filenames may change; the dependency direction must not.

### Domain

Pure training concepts and deterministic rules.

Requirements:
- zero Voice of Luna imports;
- no filesystem/network/model calls;
- deterministic behavior for the same state + command;
- exhaustive unit tests for transition invariants.

### Application

Coordinates domain operations and training-specific use cases such as session setup, approved replay material, observations and debrief construction.

It may define ports/interfaces for storage or external context but should not depend on private host internals.

### Integration

The Voice of Luna adapter maps public host contracts (`Plugin`, turn/tool contexts, settings, actions, capabilities) to application/domain operations.

This is the only layer that should normally import `app.plugin_api` or other documented public host package APIs.

## Current implementation

As of v0.1.0, most behavior still lives directly in `VoiceTrainerPlugin` in `src/voice_trainer/plugin.py`. This is acceptable as an extraction/bootstrap state, but it is not the final architecture.

Do not build substantial deterministic training logic into that class. New controller semantics should move toward the layered boundary above.

## State model and privacy boundary

State is divided by purpose, not merely by storage mechanism.

### 1. Ephemeral turn/session state

Examples:
- active phase;
- counters;
- current requirement completion;
- temporary replay source references;
- current session clock/state.

Retention: session-scoped or otherwise minimal.

### 2. Bounded operational plugin state

Examples:
- compact recent-session summaries needed for continuity;
- plugin configuration or locally useful control metadata.

Current implementation stores up to 20 recent turn summaries, truncating each user and assistant text field to 240 characters.

Retention must remain bounded and documented. This state is not a substitute for durable personal memory.

### 3. Training observations

Short, intentional observations may be written through the host's generic plugin storage capability. They should be explicit product artifacts, not silent transcript capture.

Each new persisted observation type should define:
- why it exists;
- who creates it;
- who reads it;
- retention/deletion behavior;
- whether it may contain personal content.

### 4. External personal/project memory

Private Relationship-training scenarios, long-lived personal history, rich user context and personal source material belong outside both code repositories and outside accidental plugin logging.

The trainer may receive bounded context through generic host/project mechanisms, but must not turn that into an unrestricted duplicate personal-history store.

### Never persist here by default

- raw recordings;
- credentials or tokens;
- Codex/OpenAI authentication material;
- unrestricted full transcripts;
- secret-bearing environment data;
- committed personal Relationship scenarios/history.

## Host contract rule

If Trainer needs something the host does not expose:
1. first decide whether the capability is genuinely generic;
2. if generic, extend the documented Voice of Luna plugin contract narrowly;
3. keep training semantics in this repository;
4. never import a private Voice of Luna implementation module as a shortcut.

## Testing strategy

- domain/controller tests: pure and exhaustive around invariants and transitions;
- application tests: storage/port behavior with fakes;
- adapter tests: public Voice of Luna plugin contract only;
- host integration gate: verify external discovery and compatibility against a supported Voice of Luna version;
- no real paid-model calls in automated tests.

## Source-of-truth rule

- current implementation truth → code + `docs/CURRENT_STATUS.md`;
- architectural ownership → this file;
- deterministic protocol semantics → `docs/PROTOCOL.md`;
- active work → GitHub Issues;
- history → `CHANGELOG.md` and Git.
