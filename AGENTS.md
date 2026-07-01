# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Build / test commands

- Install: `pip install -e ".[dev]"` (or `uv sync`)
- Lint: `ruff check .`
- Format check: `black --check .`
- Tests: `pytest`
- Run: `python main.py` (requires a filled-in `.env`, see README)

## Stack decisions

- Config is a `pydantic-settings` `Settings` class (`trend_setter/config.py`)
  loading from `.env` via `SettingsConfigDict(env_file=".env")`. Required
  fields (tokens/keys/project id) have no defaults and raise a validation
  error at construction if unset — that's the intended fail-fast behavior.
- Pipeline stages are plain importable functions (`trend_setter/trends/*`,
  `generation/*`, `posting/instagram.py`), wired together in
  `pipeline.run_pipeline`. Every stage is currently a stub that raises
  `NotImplementedError` at its TODO point — tests patch the stage functions
  directly in the `trend_setter.pipeline` namespace (not their defining
  module) since `pipeline.py` imports them by name.
- Async: TikTok fetch and Instagram publish are `httpx`-based async
  functions; YouTube/Google Trends fetches are sync (client libs aren't
  async) and are run via `asyncio.to_thread` inside `run_pipeline`.

## Sharp edges

- **Veo has no dedicated Vertex AI SDK class in `google-cloud-aiplatform`
  1.159.0** — `vertexai.preview.vision_models.VideoGenerationModel` does
  not exist in this version, despite appearing in some docs/examples.
  `generation/video.py` instead targets the Vertex AI REST
  `{model}:predictLongRunning` endpoint directly via `httpx` +
  `google.auth.default()`. Re-check the installed SDK version before
  assuming a higher-level class exists.
- `pytrends` is unofficial (scrapes the Google Trends UI) and has
  undocumented rate limits — don't poll aggressively in real usage or
  tests that hit it live.
