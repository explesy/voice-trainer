# Voice Trainer — Current Status

Updated: 2026-10-25 (documentation verified against code; release dated 2026-10-09)
Current release: **0.2.2**

Purpose: compact current truth for fresh-session startup. This is not a changelog, roadmap, or replacement for active GitHub Issues.

## Product shape

Voice Trainer is a separately versioned, local-first training product installed into Voice of Luna as an external Python plugin.

Voice of Luna remains the generic voice/conversation host. Voice Trainer owns training semantics and plugin-scoped training state. Personal Relationship-training scenarios and durable personal history remain outside both code repositories.

## Implemented now

- standalone `voice-trainer` package;
- discovery through the `voice_of_luna.plugins` Python entry-point group;
- plugin settings for `skill` and session `goal`;
- training/free dialogue entry points, training settings (`goal`, `scenario`, duration, reflection limit and optional requirements);
- an initial deterministic domain `Controller` (`src/voice_trainer/domain/controller.py`) with explicit session status/phases, model-end rejection, phase/action validation, reflection-limit and replay-source checks;
- start, pause, resume, manual end, reset, a session snapshot/timer, serialized plugin-scoped session state and event records;
- a response-validation gate for structured model proposals, with plain-text fallback;
- prompt-context injection through the public Voice of Luna plugin API;
- storage-backed `training.history`, `training.observe`, and `training.progress` tools;
- domain and host-integration tests. See `README.md`, `CHANGELOG.md` and code for the exact shipped contract.

The package is installed against the public Voice of Luna backend package/API rather than importing private host implementation modules.

## Important current limitation

The initial deterministic domain controller **is implemented and tested**, but the full target protocol is **not**. Current code does not yet enforce all planned requirement-completion gates and exact-replay validation semantics; the complete structured debrief and lifecycle remain work in progress. `docs/PROTOCOL.md` describes target invariants, not a guarantee that each one ships in v0.2.2.

Do not describe the product as either controller-free or fully protocol-complete. Derive implementation claims from `src/voice_trainer/domain/`, `src/voice_trainer/plugin.py`, tests and `CHANGELOG.md`; active work belongs in GitHub Issues.

## Architectural boundaries

- **Voice Trainer owns:** training workflow semantics, controller rules, replay/debrief behavior, training-specific tests, and bounded plugin state.
- **Voice of Luna owns:** audio, STT/TTS, model/conversation transport, generic plugin lifecycle, generic storage/capabilities, and generic UI shell.
- **External personal/project memory owns:** private user scenarios, long-lived personal training history, and personal observations intended to survive independently of the plugin's operational state.

## State/privacy status

The plugin maintains a separate compatibility list of the last 20 turn summaries (each user/assistant field truncated to 240 characters) and supplies up to six recent turns to the model. It also serializes the active `SessionState` in host-provided plugin state, including an event list. In v0.2.2, `after_turn` appends `model_response_observed` events containing up to 2,000 characters of assistant text and 1,000 of user text **without an explicit event-count/retention bound** in the repository code. This is an observed privacy/retention gap, not a claim that personal training history is safely bounded.

Do not expand transcript-like persistence without an explicit retention/privacy decision. Raw recordings, credentials, tokens and unrestricted personal training transcripts must not be committed to the repository. See `docs/ARCHITECTURE.md` for intended state ownership and retention policy.

## Retrieval routing

- “What exists now?” → this file + current code.
- product/install boundary → `README.md`.
- architecture/state ownership → `docs/ARCHITECTURE.md`.
- session phases/transitions/invariants → `docs/PROTOCOL.md`.
- active implementation work → relevant GitHub Issue.
- historical evolution → `CHANGELOG.md` / Git history.

Do not reconstruct current truth from the old Voice of Luna migration issue when this repository's code and this file answer the question.
