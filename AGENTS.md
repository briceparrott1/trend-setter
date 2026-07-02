# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Build / test commands

- Install: `pip install -e ".[dev]"` (or `uv sync`)
- Lint: `ruff check .`
- Format check: `black --check .`
- Tests: `pytest`
- Run: `python main.py` (requires a filled-in `.env`, see README)
- Run once (no scheduler, for end-to-end testing): `python main.py --run-once`

## Stack decisions

- Config is a `pydantic-settings` `Settings` class (`trend_setter/config.py`)
  loading from `.env` via `SettingsConfigDict(env_file=".env")`. Required
  fields (tokens/keys/project id) have no defaults and raise a validation
  error at construction if unset — that's the intended fail-fast behavior.
- Pipeline stages are plain importable functions (`trend_setter/trends/*`,
  `generation/*`, `posting/instagram.py`), wired together in
  `pipeline.run_pipeline`. All stages are implemented now except
  `posting/instagram.py` (Instagram Graph API), which is still a
  `NotImplementedError` stub by design — a separate task.
  `generation/video.py` (Kling AI + OpenAI TTS + moviepy assembly) is
  fully implemented. Tests patch the stage functions directly in the
  `trend_setter.pipeline` namespace (not their defining module) since
  `pipeline.py` imports them by name.
- `run_pipeline` still unconditionally calls `publish_reel` after video
  generation, so a real (non-mocked) `--run-once` invocation succeeds
  through video generation and then raises `NotImplementedError` at the
  publish step until `posting/instagram.py` is implemented — expected,
  not a bug. `run_pipeline` now returns a dict (`topic`, `script`,
  `caption`, `shot_descriptions`, `citations`, `video_path`, `media_id`)
  instead of a bare media ID string.
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
  Vertex AI entirely. `VideoGenProvider` (`generation/__init__.py`) is an
  unused abstract base left over from an earlier design pass — its
  `generate_clip`/`generate_video` signatures no longer match the
  concrete functions in `generation/video.py` and nothing imports it;
  don't assume it's wired in. Target cost is ~$0.14 per 5s clip at
  standard quality, ~$0.84 per video for the 6-clip format below.
  Implementation (`generation/video.py`): submits a text2video task to
  `kling-v1` (9:16 aspect ratio, `std` mode, `kling_clip_duration`-second
  clips), polls the task status endpoint every 5s up to a 600s timeout
  (raised from 300s after observing legitimate >300s renders), then
  downloads the resulting MP4. `generate_all_clips` runs all clips
  concurrently through an `asyncio.Semaphore(3)` (max 3 concurrent Kling
  requests) to avoid rate limits, capped at `kling_clips_per_video`
  (default 6) shot descriptions from the brief. Every clip's prompt is
  prefixed with `settings.kling_style_prefix` (default: cinematic
  photorealistic footage of real people actively demonstrating/reacting/
  engaged in the action, dynamic handheld motion, 4K, professional
  lighting — see "Engagement revamp" below) and sent alongside
  `settings.kling_negative_prompt` (default: excludes cartoon/
  anime/CGI/illustration/low-quality) in the text2video payload — this
  keeps visual style consistent across all clips in a video instead of
  each shot description independently deciding style. Both are
  configurable via `KLING_STYLE_PREFIX` / `KLING_NEGATIVE_PROMPT` env
  vars, commented out with defaults shown in `.env.example`.
- TTS voiceover: **OpenAI** (`OPENAI_API_KEY`, `generation/tts.py`) —
  `tts-1` model, voice/speed configurable via `Settings.tts_voice` /
  `Settings.tts_speed` (defaults `"shimmer"` / `1.2`, see "Engagement
  revamp" below), run via `asyncio.to_thread` since the `openai` SDK's
  `audio.speech.create` + `response.stream_to_file` are sync calls.
- Assembly (`generation/video.py:assemble_video`): **moviepy 1.x**
  (`from moviepy.editor import ...`) — pinned `<2.0.0` because moviepy 2.x
  renamed/removed the `moviepy.editor` module and changed several method
  names (breaking API change, not just a version bump). Concatenates all
  clips in order, lays the TTS voiceover over the full video, and matches
  video duration to voiceover duration by trimming (`subclip`) if the
  video is longer, or looping the last clip (`vfx.loop`) if the voiceover
  is longer. `generate_video` runs TTS and Kling clip generation
  concurrently via `asyncio.gather`, then runs the (blocking) moviepy
  assembly step via `asyncio.to_thread`.
- Output layout: final video at
  `{video_output_dir}/trend_setter_{timestamp}.mp4`; intermediate clips
  in `{video_output_dir}/clips_{timestamp}/clip_00.mp4` etc.; voiceover at
  `{video_output_dir}/voiceover_{timestamp}.mp3`. `video_output_dir`
  defaults to `output/` (`VIDEO_OUTPUT_DIR` env var) and is created if
  missing — nothing currently cleans up intermediate clips/voiceover
  files after assembly.
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
  script; 6 x 5s Kling clips; TTS voiceover + burned-in captions (see
  "Engagement revamp" below).
- Topic filter: 3-gate hard filter in `trends/filter.py`
  (`filter_topics`) — a candidate must pass every gate (explainable in
  <45s, surprising angle, >=2 authoritative sources) before it reaches the
  research stage. There is deliberately no gossip/celebrity/sports
  rejection gate (see "Engagement revamp" below — it was removed, not
  forgotten). `aggregate_trends` in `trends/aggregator.py` builds the
  candidate list (Google Trends + YouTube + a NewsData.io fetch it
  triggers itself), applies the filter, then ranks survivors by
  controversy score before truncating to `max_trends`.

- Progressive run report: `trend_setter/report.py`'s `RunReport` writes a
  JSON file to `{video_output_dir}/report_{timestamp}.json` and rewrites
  it (full overwrite, not append) to disk on every stage boundary in
  `run_pipeline` — topic chosen, research complete, brief generated,
  video generated, publish attempted/failed. This exists because a run
  that fails at or after brief generation (Kling/TTS failure, or the
  `posting/instagram.py` `NotImplementedError` stub) used to leave zero
  record on disk of what had already been generated; a prior scout run
  had to recover a lost script by transcribing the saved voiceover MP3
  with Whisper. `run_pipeline` wraps every stage from research onward in
  a single `try/except Exception`, calling `report.record_failure(exc)`
  (which tags the report with `failed_after_stage`, the last
  successfully-completed stage name) before re-raising — so the
  exception still propagates to callers (`main.py --run-once` still
  exits non-zero / logs the traceback) but the report file on disk
  captures everything generated up to that point. The report is only
  created *after* a topic survives the trend filter (`candidates[0]` is
  chosen) — the "no candidates survived filtering" early-return produces
  no report file at all, by design, since there's no topic yet to report
  on. `_clip_paths_for_video` (`pipeline.py`) derives the clip directory
  from the final video's `trend_setter_{timestamp}.mp4` filename to find
  the sibling `clips_{timestamp}/` dir — this is a convention lookup, not
  a value `generate_video` returns directly, so it silently returns `[]`
  if the naming convention ever changes. `output/` (the default
  `video_output_dir`) is now gitignored, since it accumulates run
  reports alongside videos/clips/voiceovers and was never meant to be
  committed.

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
- `fetch_rising_queries` (`trends/google_trends.py`) retries pytrends
  failures up to 3 attempts with exponential backoff (2s/4s/8s via
  `time.sleep`, not `asyncio.sleep` — the function is sync and is only
  ever called through `asyncio.to_thread` in `pipeline.py`) and returns
  `[]` (does not raise) if all 3 attempts fail. It only retries
  `requests.exceptions.ReadTimeout` and `requests.exceptions.ConnectionError`
  — note the real requests exception is `ReadTimeout`, **not**
  `ReadTimeoutError` (that name doesn't exist in `requests.exceptions`;
  `ReadTimeoutError` is a `urllib3` class). Other exceptions propagate
  unchanged.
- `generate_clip`'s (`generation/video.py`) Kling polling timeout
  (`max_wait_seconds`) is 600s, not 300s — raised after observing clips
  that legitimately take >300s to render. `generate_all_clips` retries a
  failing clip once (inline, inside the per-clip task) before treating it
  as a permanent failure, then uses `asyncio.gather(..., return_exceptions=True)`
  so one bad clip can't kill the whole batch — it raises only if fewer
  than `max(1, kling_clips_per_video // 2)` clips succeeded. Callers of
  `generate_all_clips` (i.e. `generate_video`) should expect the returned
  list to sometimes be shorter than the requested clip count.

## Engagement revamp (captain's direction, PR "reel-revamp")

- **Gossip/celebrity gate removed by design.** `filter.py` used to have a
  4th gate (`passes_gate_4_not_gossip` + `REJECT_CATEGORIES`) rejecting
  celebrity/gossip/sports/gaming/entertainment/music candidates. It has
  been deleted outright — the captain wants scandalous/polarizing content,
  not "safe" educational-only topics. `filter_topics` now runs 3 gates,
  not 4. Don't re-add a gossip gate without re-confirming with the captain
  first; that was a deliberate reversal, not an oversight.
- **Controversy ranking, not gating.** `aggregator.py`'s `aggregate_trends`
  now ranks filtered candidates by `_controversy_score` (a keyword-count
  heuristic over `_CONTROVERSY_KEYWORDS` — same cheap/deterministic style
  as gate 1's explainability heuristic, no LLM call) before truncating to
  `max_trends`, so a candidate whose title reads as scandalous/divisive
  ("accused", "scandal", "backlash", "banned", etc.) sorts ahead of a
  neutral one. This is a *ranking* step only — it never removes a
  candidate, it only reorders survivors of `filter_topics`. `sorted(...,
  reverse=True)` is stable, so ties keep their original (source-priority)
  order; this is depended on by
  `test_aggregate_trends_dedupes_case_and_whitespace_across_sources` in
  `tests/test_trends.py`, don't swap in an unstable sort.
- **Burned-in captions are timing-estimated, not exact.** OpenAI TTS
  returns no word/phoneme-level alignment data, so `video.py`'s
  `_estimate_caption_segments` splits the script on sentence/clause breaks
  (`_split_script_into_captions`, regex on `.!?,`) and distributes the
  final (voiceover-matched) duration across segments proportional to each
  segment's word count. This is "good enough" sync by design — expect
  captions to drift slightly from the actual spoken word, especially for
  segments with many short/long words. `assemble_video` now takes a
  required `script` param (signature change) and composites
  `_build_subtitle_clips`'s `TextClip`s over the trimmed/looped video via
  `CompositeVideoClip` before attaching audio. Caption styling (white
  text, black stroke, positioned at 70% of frame height via a *relative*
  `set_position(("center", 0.7), relative=True)`, sized to 90% of frame
  width) lives in `_build_subtitle_clips`, which takes the assembled
  video's actual `(width, height)` (`video.size`) as a parameter rather
  than a hardcoded constant — an earlier version hardcoded
  `CAPTION_VIDEO_SIZE = (1080, 1920)` assuming Kling's clips are always
  9:16, but that silently mispositioned captions whenever the assembled
  video's real dimensions differed; this was fixed by reading `video.size`
  directly. Adjust `_build_subtitle_clips` if legibility needs tuning.
  **New runtime dependency:** moviepy 1.x's `TextClip` shells out to
  ImageMagick's `convert` binary — it must be installed and on `PATH` in
  any environment that actually renders video (not needed for the test
  suite, which mocks `moviepy.editor.TextClip`/`CompositeVideoClip`
  entirely).
  **Font resolution: use a real font file path, never a bare ImageMagick
  font alias.** `_build_subtitle_clips` originally hardcoded
  `font="Arial-Bold"` (a bare ImageMagick font *alias*, not a file path).
  A live `--run-once` pipeline run (pipeline-run-5) crashed at this exact
  line with `OSError: ... [Errno 2] No such file or directory: 'unset'`
  even with ImageMagick installed — moviepy's `IMAGEMAGICK_BINARY` silently
  defaults to the literal string `'unset'` when auto-detection fails, and
  separately, a bare font alias only resolves if the host's ImageMagick
  font database happens to have that exact name registered, which it
  commonly doesn't (e.g. `convert -list font` returns **zero** fonts on a
  fresh macOS Homebrew `imagemagick` install, even though the OS itself
  has Arial via `fc-list`/Font Book). Fixed by `_resolve_caption_font()`
  (`video.py`), which checks a fixed list of well-known per-OS font *file
  paths* (`_CAPTION_FONT_CANDIDATES` — Liberation Sans Bold on Linux via
  the `fonts-liberation` package, DejaVu Sans Bold as a Linux fallback via
  `fonts-dejavu-core`, macOS's bundled Arial Bold.ttf) and passes the first
  one that exists as an explicit file path to `TextClip`, bypassing
  ImageMagick's font-alias database entirely. Raises a clear `RuntimeError`
  naming the packages to install if none of the candidates exist, instead
  of moviepy's confusing "unset" error. **Production/cloud deployment must
  have one of `fonts-liberation` or `fonts-dejavu-core` installed
  alongside ImageMagick** — verify this is in whatever base image/Dockerfile
  actually ships to production, since neither font package is a Python
  dependency and nothing currently checks for it at startup (only at the
  first real caption-render call).
- **TTS voice/speed are now `Settings` fields**, not hardcoded in
  `tts.py`: `tts_voice` (default `"shimmer"`, chosen as OpenAI's
  brightest/most energetic voice) and `tts_speed` (default `1.2`, in the
  API's 0.25-4.0 range) — both passed through from `generate_video` into
  `generate_voiceover`. Tune these directly via `.env` (`TTS_VOICE`,
  `TTS_SPEED`) without a code change if the captain wants a different
  voice/pace after listening to real output.
- **`kling_style_prefix` default now biases toward people-in-motion, not
  static b-roll** ("real people actively demonstrating, reacting to, or
  engaged in the action described, dynamic handheld motion" instead of
  "documentary footage"). This pairs with a `brief.py` prompt change:
  `SCRIPT_PROMPT`'s shot-description instruction used to explicitly say
  "no text/people" — that was the actual root cause of static, peopleless
  b-roll and has been reversed to *require* each shot feature people
  actively doing something concrete and relevant to the topic. The
  "no on-screen text" restriction was kept (Kling rendering in-scene text
  reliably looks bad) — only the "no people" half was reversed.
- **Hook attribution guardrail is a prompt-engineering change with no
  code-level verifier, by design.** The captain wants clip-1 hooks to use
  "did you know [named person] believes/claims [Y]" when research
  actually supports a specific sourced claim attributable to one named
  person, contextualized in the next beat with "according to [named
  person]...", but falling back to a non-attributed hook ("some
  believe...", "reportedly...") whenever it doesn't. `SCRIPT_PROMPT` in
  `brief.py` now spells out both branches and the condition explicitly,
  and `generate_brief` now builds a `research_notes` field (joining
  `research["raw_answer"]` — the full Perplexity prose — plus
  `research["wikipedia"]["extract"]` when present) and passes it into the
  prompt, since the pre-extracted `hook_fact`/`supporting_facts` fields
  are usually too condensed for the model to judge attribution quality
  from. **This is inherently a model-judgment call that cannot be
  deterministically unit-tested for content correctness** — there is no
  reliable code-level way to verify "did the model correctly judge
  whether this claim is attributable" (regex-matching for named-entity
  patterns would be unreliable and was deliberately not attempted). The
  tests in `tests/test_brief.py` only check the prompt text itself and
  that `generate_brief` feeds raw research context through — they cannot
  and do not verify the model actually picks the right branch. Treat any
  future concern about hallucinated attribution as something to spot-check
  manually against real pipeline output (or refine via prompt iteration),
  not something to chase with a stricter automated check.
