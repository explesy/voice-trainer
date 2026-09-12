# Changelog

All notable changes to Voice Trainer are documented here.

The project follows Semantic Versioning. Active implementation work belongs in GitHub Issues; this file records shipped or architecturally meaningful changes rather than serving as a TODO list.

## Unreleased

### Documentation

- Added canonical repository guidance for AI-assisted development.
- Added compact current-status documentation.
- Defined target domain/application/Voice-of-Luna integration boundaries.
- Defined the target deterministic training session protocol and controller invariants.
- Clarified bounded operational state versus long-lived personal/project memory.

## 0.1.0 — 2026-09-12

### Added

- Initial standalone Voice Trainer Python package.
- External plugin discovery through the `voice_of_luna.plugins` entry point.
- Practice, debrief and free-dialogue modes.
- Plugin settings, reset action and bounded recent-session state.
- Storage-backed history, observation and progress tools.
- Initial host integration test.

### Architecture

- Established Voice Trainer as the canonical repository for training-product semantics.
- Kept Voice of Luna responsible for generic audio/conversation/plugin-host infrastructure.
