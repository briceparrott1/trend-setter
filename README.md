# trend-setter

## What it does

`trend-setter` is a scheduled pipeline that monitors Google Trends,
YouTube, and NewsData.io for rising topics, filters them through a 3-gate
relevance check (and ranks the survivors so scandalous/polarizing topics
are prioritized), uses Perplexity Sonar to find a surprising, explainable
angle with citations, generates a 30-45s narrated explainer video (TTS
voiceover + Kling AI B-roll clips + burned-in captions), and posts it to
Instagram Reels with on-screen source citations — automatically, on a
configurable schedule.

## Prerequisites

- Python 3.12+
- A Google AI Studio API key (for Gemini)
- A Kling AI account (for video generation)
- An OpenAI API account (for TTS voiceover)
- `ffmpeg` installed and on `PATH` (used by moviepy for video assembly)
- ImageMagick installed and on `PATH` (used by moviepy's `TextClip` to
  burn in captions)
- A Perplexity API account (for research)
- A Facebook Developer app with the Instagram Graph API product enabled
- A YouTube Data API v3 key
- A NewsData.io account

## Instagram Graph API setup

1. Create a Facebook Developer account at
   [developers.facebook.com](https://developers.facebook.com).
2. Create an app (type "Business"), then add the **Instagram Graph API**
   product to it.
3. Generate a long-lived Page Access Token for the Facebook Page linked to
   your Instagram Business/Creator account (exchange a short-lived user
   token for a long-lived one via the `/oauth/access_token` endpoint).
4. In App Review, enable the `instagram_content_publish`,
   `instagram_basic`, and `pages_read_engagement` permissions.
5. Find your Instagram Business Account ID by querying
   `GET /{page-id}?fields=instagram_business_account` with your access
   token.
6. Set `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_ACCOUNT_ID` in your `.env`
   from the values above.

## YouTube Data API v3 setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and
   select (or create) your Google Cloud project.
2. Enable the **YouTube Data API v3** under APIs & Services > Library.
3. Under APIs & Services > Credentials, create an API key and restrict it
   to the YouTube Data API v3.
4. Set `YOUTUBE_API_KEY` in your `.env`.

## Google Trends

No API key is required. `trend-setter` uses [`pytrends`](https://github.com/GeneralMills/pytrends),
an unofficial client that scrapes the public Google Trends UI. Because it
is unofficial, it is subject to undocumented rate limits — avoid polling
too frequently, and expect occasional `429` responses under heavy use.
`GOOGLE_TRENDS_GEO` controls the geography (e.g. `US`) used for rising
query lookups.

## Google AI Studio setup

1. Go to [aistudio.google.com](https://aistudio.google.com).
2. Click "Get API key" and create a new key.
3. Set `GEMINI_API_KEY` in your `.env`. That's it — no billing account is
   needed for Gemini Flash usage.

## Kling AI setup

1. Go to [kling.ai/dev](https://kling.ai/dev) and sign up.
2. Copy your API key from the developer dashboard.
3. Set `KLING_API_KEY` in your `.env`.

## OpenAI TTS setup

1. Go to [platform.openai.com](https://platform.openai.com) and create an
   account (or use an existing one).
2. Generate an API key under API keys.
3. Set `OPENAI_API_KEY` in your `.env`. Used to synthesize the video's
   voiceover with the `tts-1` model and the `nova` voice.

## Perplexity API setup

1. Go to [perplexity.ai/api](https://perplexity.ai/api) and create an
   account.
2. Generate an API key from the account dashboard.
3. Set `PERPLEXITY_API_KEY` in your `.env`.

## NewsData.io setup

1. Go to [newsdata.io](https://newsdata.io) and sign up.
2. Copy the API key from the dashboard as `NEWSDATAIO_API_KEY`.
3. Set `NEWSDATAIO_API_KEY` in your `.env`.

   Free tier: 200 credits/day, works in production (no localhost
   restriction).

## Installation

```bash
pip install -e ".[dev]"
```

or with [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

## Configuration

Copy `.env.example` to `.env` and fill in every value:

```bash
cp .env.example .env
```

| Variable | Description |
| --- | --- |
| `INSTAGRAM_ACCESS_TOKEN` | Long-lived Page Access Token with Instagram publish permissions. |
| `INSTAGRAM_ACCOUNT_ID` | Instagram Business Account ID to publish Reels to. |
| `GEMINI_API_KEY` | Google AI Studio API key for Gemini. |
| `GEMINI_MODEL` | Gemini model used to write scripts/briefs, default `gemini-2.0-flash-001`. |
| `KLING_API_KEY` | Kling AI API key for video clip generation. |
| `OPENAI_API_KEY` | OpenAI API key for TTS voiceover generation. |
| `VIDEO_OUTPUT_DIR` | Directory for generated clips/voiceover/final MP4s and per-run `report_*.json` files, default `output`. |
| `PERPLEXITY_API_KEY` | Perplexity Sonar API key for topic research. |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key. |
| `NEWSDATAIO_API_KEY` | NewsData.io key for trending headline discovery. |
| `GOOGLE_TRENDS_GEO` | Geography for Google Trends rising queries, default `US`. |
| `TREND_CATEGORIES` | Comma-separated seed categories for trend discovery, default `education,science,technology,history`. |
| `POST_INTERVAL_HOURS` | Hours between scheduled pipeline runs, default `6`. |
| `MAX_TRENDS_TO_FETCH` | Max trends fetched per source per run, default `10`. |

## Running

```bash
python main.py
```

This loads settings from `.env` and starts the APScheduler job, which runs
the full trend → filter → research → brief → video → post pipeline
immediately, then again every `POST_INTERVAL_HOURS`.

To run a single pipeline cycle and exit (useful for end-to-end testing
without waiting on the scheduler):

```bash
python main.py --run-once
```

Each cycle that picks a topic writes a progressive run report to
`{VIDEO_OUTPUT_DIR}/report_{timestamp}.json`, rewritten after every stage
(topic chosen, research, brief, video, publish). If a run fails partway
through, the report still holds whatever was generated up to that point.

## Running tests

```bash
pytest
```

Tests mock all external API calls (Google Trends, YouTube, NewsData.io,
Perplexity, Wikipedia, Gemini, Kling AI, OpenAI TTS, Instagram Graph API),
so no credentials are required to run the suite.
