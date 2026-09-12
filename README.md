# Voice Trainer

Voice Trainer is a standalone, local-first training workflow for the [Voice of Luna](https://github.com/explesy/voice-of-luna) host. It is deliberately a plugin package: Voice of Luna remains responsible for audio, the Codex conversation bridge, transport and generic plugin capabilities; this repository owns the training product and its state.

## Install into a local Voice of Luna environment

```bash
cd /path/to/voice-of-luna/backend
uv pip install 'git+https://github.com/explesy/voice-trainer.git'
```

Restart Voice of Luna after installation. The host discovers the package through the `voice_of_luna.plugins` Python entry-point group, and the **Voice Trainer** plugin will appear in its plugin list.

The package intentionally receives only the generic host contexts: plugin-scoped state, configured settings, tool storage and declared capabilities. It must not receive or persist raw recordings, Codex credentials, tokens, or personal Relationship-training scenarios/history.

## Development

```bash
uv sync --group dev
uv run pytest -q
```

Tests use the generic host package APIs and do not make Codex, OpenAI, or paid-model calls.

## Product boundary

This is the canonical codebase for Voice Trainer. Future deterministic controller work (session phases, transition rules, replay and debrief) belongs here, not in Voice of Luna. Integration changes must extend only generic host/plugin contracts; product code must never import private Voice of Luna implementation modules beyond the documented plugin API.
