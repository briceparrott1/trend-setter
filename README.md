# trend-setter

## What it does

`trend-setter` is a scheduled pipeline that monitors TikTok, YouTube, and
Google Trends for rising topics, uses Gemini (Vertex AI) to synthesize a
short-form video brief and caption from the cross-platform trend signal,
generates a short video from that brief with Veo 2 (Vertex AI), and posts
the result to Instagram as a Reel — automatically, on a configurable
schedule.

## Prerequisites

- Python 3.12+
- A Google Cloud project with the Vertex AI API enabled (for Gemini + Veo 2)
- A Facebook Developer app with the Instagram Graph API product enabled
- A TikTok Developer account with Research API access
- A YouTube Data API v3 key

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

## TikTok Research API setup

1. Apply for TikTok for Developers Research API access at
   [developers.tiktok.com](https://developers.tiktok.com).
2. Create an app in the developer portal and request approval for the
   **Research API** product.
3. Once approved, obtain your app's `client_key` and `client_secret` from
   the app's credentials page.
4. Set `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` in your `.env`.

   Note: Research API access requires manual approval from TikTok and may
   take several days (or longer) to be granted.

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

## Google Cloud / Vertex AI setup

1. Create or select a GCP project at
   [console.cloud.google.com](https://console.cloud.google.com).
2. Enable the **Vertex AI API** under APIs & Services > Library.
3. In Vertex AI > Model Garden, enable access to the Gemini and Veo model
   families for your project.
4. Create a service account with the `Vertex AI User` role, download its
   JSON key, and set `GOOGLE_APPLICATION_CREDENTIALS` to the local path of
   that key file.
5. Set `GOOGLE_CLOUD_PROJECT` (and optionally `GOOGLE_CLOUD_LOCATION`,
   `GEMINI_MODEL`, `VEO_MODEL`) in your `.env`.

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
| `GOOGLE_CLOUD_PROJECT` | GCP project ID used for Vertex AI (Gemini + Veo 2). |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region, default `us-central1`. |
| `GEMINI_MODEL` | Gemini model used to write video briefs/captions, default `gemini-2.0-flash-001`. |
| `VEO_MODEL` | Veo model used for video generation, default `veo-002`. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to a GCP service account JSON key with Vertex AI access. |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key. |
| `TIKTOK_CLIENT_KEY` | TikTok for Developers app client key (Research API). |
| `TIKTOK_CLIENT_SECRET` | TikTok for Developers app client secret (Research API). |
| `GOOGLE_TRENDS_GEO` | Geography for Google Trends rising queries, default `US`. |
| `TREND_CATEGORIES` | Comma-separated seed categories for trend discovery, default `entertainment,technology,lifestyle`. |
| `POST_INTERVAL_HOURS` | Hours between scheduled pipeline runs, default `6`. |
| `MAX_TRENDS_TO_FETCH` | Max trends fetched per source per run, default `10`. |

## Running

```bash
python main.py
```

This loads settings from `.env` and starts the APScheduler job, which runs
the full trend → brief → video → post pipeline immediately, then again every
`POST_INTERVAL_HOURS`.

## Running tests

```bash
pytest
```

Tests mock all external API calls (TikTok, YouTube, Google Trends, Vertex
AI, Instagram Graph API), so no credentials are required to run the suite.
