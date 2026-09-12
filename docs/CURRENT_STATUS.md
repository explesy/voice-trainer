# Voice Trainer — Current Status

Updated: 2026-09-12
Current release: **0.1.0**

Purpose: compact current truth for fresh-session startup. This is not a changelog, roadmap, or replacement for active GitHub Issues.

## Product shape

Voice Trainer is a separately versioned, local-first training product installed into Voice of Luna as an external Python plugin.

Voice of Luna remains the generic voice/conversation host. Voice Trainer owns training semantics and plugin-scoped training state. Personal Relationship-training scenarios and durable personal history remain outside both code repositories.

## Implemented now

- standalone `voice-trainer` package;
- discovery through the `voice_of_luna.plugins` Python entry-point group;
- plugin settings for `skill` and session `goal`;
- modes: `practice`, `debrief`, `free`;
- prompt-context injection through the public Voice of Luna plugin API;
- bounded recent-session state;
- generic storage-backed `training.history`, `training.observe`, and `training.progress` tools;
- reset action;
- integration test covering host state and storage usage.

The package is installed against the public Voice of Luna backend package/API rather than importing private host implementation modules.

## Important current limitation

The repository does **not yet contain the intended deterministic training controller/state machine** as a separate domain layer.

The current `VoiceTrainerPlugin` is a minimal host-integrated implementation. Earlier extraction planning described a richer architecture with explicit phases, controller-owned transitions, reflection limits, replay validation, required-stage tracking, and structured debrief semantics. Those remain the target architecture and are documented in `docs/ARCHITECTURE.md` and `docs/PROTOCOL.md`; implementation work should be tracked in GitHub Issues.

Do not describe the deterministic controller as implemented until the code and tests actually exist here.

## Architectural boundaries

- **Voice Trainer owns:** training workflow semantics, controller rules, replay/debrief behavior, training-specific tests, and bounded plugin state.
- **Voice of Luna owns:** audio, STT/TTS, model/conversation transport, generic plugin lifecycle, generic storage/capabilities, and generic UI shell.
- **External personal/project memory owns:** private user scenarios, long-lived personal training history, and personal observations intended to survive independently of the plugin's operational state.

## State/privacy status

The current plugin stores a bounded list of the last 20 turn summaries in plugin-scoped local state, with user and assistant text truncated to 240 characters. This is operational session state, not the intended durable personal training memory.

Before expanding persistence, follow the state classes and retention rules in `docs/ARCHITECTURE.md`. Raw recordings, credentials, tokens, and unrestricted personal training transcripts must not be persisted by this package.

## Retrieval routing

- “What exists now?” → this file + current code.
- product/install boundary → `README.md`.
- architecture/state ownership → `docs/ARCHITECTURE.md`.
- session phases/transitions/invariants → `docs/PROTOCOL.md`.
- active implementation work → relevant GitHub Issue.
- historical evolution → `CHANGELOG.md` / Git history.

Do not reconstruct current truth from the old Voice of Luna migration issue when this repository's code and this file answer the question.
