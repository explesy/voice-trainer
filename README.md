# Voice Trainer

Voice Trainer is a standalone, local-first training workflow for the [Voice of Luna](https://github.com/explesy/voice-of-luna) host. It is deliberately a separate plugin package: Voice of Luna remains responsible for audio, the Codex conversation bridge, transport and generic plugin capabilities; this repository owns the training product and its state.

## Current status

The current `0.1.0` implementation is a minimal external Voice of Luna plugin. It provides settings, `practice` / `debrief` / `free` modes, bounded recent-session state, a reset action, and storage-backed training tools.

The richer deterministic trainer controller described in `docs/PROTOCOL.md` is the **target architecture and is not yet implemented**. Current truth is summarized in `docs/CURRENT_STATUS.md`.

## Install into a local Voice of Luna environment

```bash
cd /path/to/voice-of-luna/backend
uv pip install 'git+https://github.com/explesy/voice-trainer.git'
```

Restart Voice of Luna after installation. The host discovers the package through the `voice_of_luna.plugins` Python entry-point group, and the **Voice Trainer** plugin will appear in its plugin list.

## Product boundary

Voice Trainer owns training workflow semantics, training-specific validation and bounded plugin state. Future deterministic controller work—session phases, transition rules, requirements/counters, replay and debrief semantics—belongs here, not in Voice of Luna.

Voice of Luna owns generic audio/STT/TTS, conversation/model transport, plugin discovery/lifecycle, generic state/storage capabilities and the generic UI shell. Integration changes should extend only generic host/plugin contracts; Voice Trainer must not depend on private Voice of Luna implementation modules beyond documented public plugin APIs.

## Privacy and state

The package intentionally receives only generic host contexts: plugin-scoped state, configured settings, tool storage and declared capabilities. It must not receive or persist raw recordings, Codex credentials, tokens, secret-bearing environment data, or unrestricted personal training transcripts.

The current plugin does keep bounded operational continuity state: up to 20 recent turn summaries, with user and assistant text truncated to 240 characters. This is not the canonical long-lived personal training history. Private Relationship-training scenarios, rich personal context and durable personal history remain external Project Memory/context and must not be committed to this repository.

See `docs/ARCHITECTURE.md` for the persistence/ownership rules.

## Documentation

For fresh work, read only what is relevant:

- `docs/CURRENT_STATUS.md` — compact current truth and implemented-vs-target distinction;
- `docs/ARCHITECTURE.md` — ownership, dependency direction, state and privacy boundaries;
- `docs/PROTOCOL.md` — target deterministic session phases, transitions and invariants;
- `AGENTS.md` — repository rules and task routing for coding agents;
- `CHANGELOG.md` — released and architecturally meaningful historical changes;
- GitHub Issues — active scoped implementation work.

## Development

```bash
uv sync --group dev
uv run pytest -q
```

Tests use the generic host package APIs and must not make Codex, OpenAI, or paid-model calls.
