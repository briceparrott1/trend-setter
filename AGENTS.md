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
- Async: only Instagram publish is a native `httpx`-based async function.
  Reddit (PRAW), YouTube, and Google Trends fetches are all sync (none of
  those client libs are async) and are run via `asyncio.to_thread` inside
  `run_pipeline`.
- TikTok was swapped for Reddit (`trend_setter/trends/reddit.py`, via
  `praw`) before this PR merged — captain's call, not a tech-debt fix.
  Config fields are `reddit_client_id`, `reddit_client_secret`,
  `reddit_user_agent` (default `trend-setter/1.0`), and
  `target_subreddits` (default `["popular", "trending"]`, comma-separated
  in env). `praw.Reddit(...)` is a sync/blocking client, same as the
  YouTube and Google Trends clients — don't reach for `httpx` there.

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
