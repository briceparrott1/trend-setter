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
  `pipeline.run_pipeline`. All stages are implemented now except
  `generation/video.py` (Kling AI) and `posting/instagram.py` (Instagram
  Graph API), which are still `NotImplementedError` stubs by design —
  separate tasks. Tests patch the stage functions directly in the
  `trend_setter.pipeline` namespace (not their defining module) since
  `pipeline.py` imports them by name.
- `run_pipeline` does NOT loop through candidates re-trying research on
  gate failure — it takes `candidates[0]` (the top filtered candidate) and
  researches only that one. Gates 2/3 (`filter.py`) are permanent
  pass-through stubs by design: they can't be evaluated pre-research, and
  nothing downstream currently re-checks `research["citations"]` count or
  a `has_surprising_angle` flag against them. If stricter post-research
  gating is wanted, it has to be added to `pipeline.run_pipeline` — don't
  assume it already happens just because `filter.py`'s docstrings mention
  Sonar/Wikipedia checks.
- Async: Instagram publish, Kling AI, Perplexity, Wikipedia, and
  NewsData.io calls are native `httpx`-based async functions. YouTube and
  Google Trends fetches are sync (neither client lib is async) and are
  run via `asyncio.to_thread` inside `run_pipeline`.
- Trend sources went through three swaps before this PR merged (captain's
  calls, not tech-debt fixes): TikTok -> Reddit -> NewsAPI ->
  **NewsData.io** (`trend_setter/trends/newsdataio.py`). NewsAPI was
  dropped because its free tier only works from `localhost`; NewsData.io's
  free tier (200 credits/day) works in cloud production. Reddit/PRAW,
  TikTok, and NewsAPI are all fully removed now.
- Video generation: **Kling AI** (`KLING_API_KEY`), replacing Veo 2 /
  Vertex AI entirely. Abstracted behind `VideoGenProvider`
  (`generation/__init__.py`) for future model swapping. Target cost is
  ~$0.14 per 5s clip at standard quality, ~$0.84 per video for the 6-clip
  format below.
- Research: **Perplexity Sonar** primary (`PERPLEXITY_API_KEY`),
  Wikipedia REST API (`research/wikipedia.py`) as a free enrichment
  layer — no API key needed for Wikipedia. `run_pipeline` fetches both
  concurrently for the top filtered candidate and merges the Wikipedia
  summary into the research dict under the `"wikipedia"` key.
- Gemini integration: **Google AI Studio** API key (`GEMINI_API_KEY`), not
  a Vertex AI service account — uses the `google-generativeai` SDK
  (`import google.generativeai as genai`), not `vertexai`.
- Video format: narrated explainer — Hook (0-3s) -> Core fact (4-20s) ->
  Supporting details (20-35s) -> Source/CTA (last 5-10s); 60-85 word
  script; 6 x 5s Kling clips; TTS voiceover + animated text overlays.
- Topic filter: 4-gate hard filter in `trends/filter.py`
  (`filter_topics`) — a candidate must pass every gate (explainable in
  <45s, surprising angle, >=2 authoritative sources, not pure
  gossip/celebrity/sports) before it reaches the research stage.
  `aggregate_trends` in `trends/aggregator.py` builds the candidate list
  (Google Trends + YouTube + a NewsData.io fetch it triggers itself) and
  applies the filter before returning.

## Sharp edges

- NewsData.io's free tier is 200 credits/day and works from cloud
  production (unlike the previous NewsAPI source, which was localhost-only
  on its free tier) — watch the credit budget if `max_trends_to_fetch` or
  poll frequency goes up.
- `pytrends` is unofficial (scrapes the Google Trends UI) and has
  undocumented rate limits — don't poll aggressively in real usage or
  tests that hit it live.
- `pytrends.related_queries()` batches by keyword and only accepts up to 5
  keywords per `build_payload()` call — `fetch_rising_queries` chunks
  `seed_keywords` into groups of 5. Its "rising" dataframe's `value`
  column is normally a numeric rising-percentage, but for a genuine spike
  pytrends reports the literal string `"Breakout"` instead of a number —
  `fetch_rising_queries` maps that to `float("inf")` so breakout queries
  always sort first, rather than crashing on `float("Breakout")`.
- Gate 1 (`passes_gate_1_explainability`) is a cheap heuristic, not NLP:
  it rejects titles under 4 words, and rejects titles where every word
  starts with a capital letter and there's no digit anywhere (read as "a
  bare proper name/entity with no explanatory framing", e.g. "Taylor
  Swift Eras Tour"). It will false-reject legitimate Title Case headlines
  that happen to have no digit and no lowercase connector word — a known
  false-positive-prone tradeoff, not a bug, per the task spec's own
  wording ("this is a heuristic").
- `aggregate_trends` is async (it calls `fetch_trending_news` itself)
  even though the other two trend fetches happen in `pipeline.py` before
  it's called — don't assume every `trends/*` function follows the same
  "fetch in pipeline, pass in the result" shape.
- **`google-generativeai` is fully deprecated upstream** ("All support...
  has ended... will no longer be receiving updates or bug fixes", per the
  package's own `FutureWarning` on import) — Google's migration guidance
  is the newer `google.genai` package. Used here anyway because the
  design spec named `google-generativeai` explicitly; re-check whether
  `google.genai` should replace it before this ships to production.
