# AGENTS.md — Voice Trainer

Repository-wide rules for AI coding agents and maintainers.

## Start here

Voice Trainer is the standalone training product/plugin for the Voice of Luna host.

For a fresh task:
1. Read `docs/CURRENT_STATUS.md` for compact current truth.
2. Read only the task-specific canonical document next.
3. Use the relevant GitHub Issue for active implementation work instead of reconstructing TODOs from old chats, commits, or historical notes.

Routing:
- product boundary / current state → `README.md`, `docs/CURRENT_STATUS.md`
- architecture / ownership / state boundaries → `docs/ARCHITECTURE.md`
- deterministic session semantics → `docs/PROTOCOL.md`
- historical changes → `CHANGELOG.md` / Git
- active scoped work → GitHub Issues

## Non-negotiable boundaries

- Voice Trainer owns training-product semantics, deterministic session control, validation, replay/debrief rules, and training-specific state.
- Voice of Luna owns generic audio, STT/TTS, conversation/model transport, plugin discovery/lifecycle, generic UI shell, and generic plugin APIs.
- Keep a future pure domain/controller layer independent of Voice of Luna imports. Host integration should stay behind a thin adapter boundary.
- Do not commit personal Relationship-training scenarios, private session history, raw recordings, credentials, tokens, or secret-bearing environment data.
- Do not expand Voice of Luna with training-specific semantics to work around a limitation here. Extend only generic host/plugin contracts when genuinely required.
- Automated tests must not make real OpenAI/Codex/paid-model calls or consume user quota.

## State and privacy rule

Plugin-scoped operational state may contain bounded local session metadata needed for the product to function. Long-lived personal training memory belongs outside the code repositories. Any new persisted field must have an explicit purpose, retention rule, and ownership documented in `docs/ARCHITECTURE.md` before it becomes part of the durable contract.

## Completion gate

For code changes:
- run `uv run pytest -q`;
- keep public behavior and canonical docs synchronized;
- use Conventional Commit-style messages;
- update `CHANGELOG.md` for user-visible or architectural changes;
- apply SemVer deliberately when preparing a release.

For docs-only changes, tests are optional unless the documentation changes executable examples, package metadata, or an asserted contract that should be verified.

A task is not complete when implementation and canonical documentation materially disagree.
