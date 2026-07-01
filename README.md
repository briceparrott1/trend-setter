# trend-setter

## What it does

`trend-setter` is a scheduled pipeline that monitors Google Trends,
YouTube, and NewsAPI for rising topics, filters them through a 4-gate
educational relevance check, uses Perplexity Sonar to find a surprising,
explainable angle with citations, generates a 30-45s narrated explainer
video (TTS voiceover + Kling AI B-roll clips + animated text overlays),
and posts it to Instagram Reels with on-screen source citations —
automatically, on a configurable schedule.

## Prerequisites

- Python 3.12+
- A Google AI Studio API key (for Gemini)
- A Kling AI account (for video generation)
- A Perplexity API account (for research)
- A Facebook Developer app with the Instagram Graph API product enabled
- A YouTube Data API v3 key
- A NewsAPI account

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

## Perplexity API setup

1. Go to [perplexity.ai/api](https://perplexity.ai/api) and create an
   account.
2. Generate an API key from the account dashboard.
3. Set `PERPLEXITY_API_KEY` in your `.env`.

## NewsAPI setup

1. Go to [newsapi.org](https://newsapi.org) and create a free account.
2. Copy your API key from the account dashboard.
3. Set `NEWSAPI_KEY` in your `.env`.

   Note: NewsAPI's free tier only works from `localhost`. For a production
   deployment, evaluate [newsdata.io](https://newsdata.io) or a paid
   NewsAPI plan.

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
| `PERPLEXITY_API_KEY` | Perplexity Sonar API key for topic research. |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key. |
| `NEWSAPI_KEY` | NewsAPI key for trending headline discovery. |
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

## Running tests

```bash
pytest
```

Tests mock all external API calls (Google Trends, YouTube, NewsAPI,
Perplexity, Wikipedia, Gemini, Kling AI, Instagram Graph API), so no
credentials are required to run the suite.
