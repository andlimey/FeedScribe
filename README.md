# FeedScribe — YouTube → Notes → Email

FeedScribe monitors YouTube channels for newly uploaded videos, fetches their transcripts, and uses an LLM via OpenRouter to generate structured markdown notes delivered to your inbox as an HTML email with a `.md` attachment — ready to drop into an Obsidian vault.

It runs entirely via GitHub Actions: a scheduled poll (Mon/Fri at 1am UTC) and an on-demand queue you can trigger from your phone by editing a text file.

## How it works

```
YouTube RSS → Transcript → OpenRouter LLM → Resend email + .md attachment
```

State is tracked in a committed JSON file so videos are never processed twice.

## Setup

```bash
git clone <your-repo-url>
cd feedscribe

python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env          # fill in your API keys
cp config.yaml.example config.yaml   # edit your channels
```

## Environment variables

Add these to `.env` for local use, and as GitHub repository secrets for the workflows:

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API key (get one free at [openrouter.ai](https://openrouter.ai)) |
| `RESEND_API_KEY` | Resend email API key |
| `RESEND_FROM_EMAIL` | Sender address (e.g. `feedscribe@yourdomain.com`) |
| `RESEND_TO_EMAIL` | Recipient address |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key — create a Google Cloud project, enable "YouTube Data API v3", and generate an API key (free, 10,000 units/day) |
| `WEBSHARE_PROXY_USERNAME` | Webshare residential proxy username — required to fetch transcripts. YouTube blocks the unofficial transcript API from most IPs (including GitHub Actions and many home connections); routing through a residential proxy works around this. Sign up at [webshare.io](https://www.webshare.io), buy a "Residential" proxy plan (not "Proxy Server" or "Static Residential"), then copy the "Proxy Username" from your [dashboard's Proxy Settings](https://dashboard.webshare.io/proxy/settings) |
| `WEBSHARE_PROXY_PASSWORD` | Webshare residential proxy password — the "Proxy Password" from the same dashboard page |

## Configuration

Edit `config.yaml` to control which channels to watch, which LLM models to use, how many videos to process per poll (default: 5), and where state is stored. See [config.yaml](config.yaml) for the full structure.

```yaml
channels:
  - url: https://www.youtube.com/@rationalreminder/videos
    name: rational_reminder
    type: youtube

llm:
  provider: openrouter
  models:
    - google/gemma-4-31b-it:free       # primary (free tier)
    - google/gemini-2.5-flash-lite     # fallback ($0.10/1M in)

polling:
  max_videos_per_poll: 5
```

The `models` list is tried in order — if the primary model fails (rate limit, outage, content filter), OpenRouter automatically falls back to the next one. Model IDs follow OpenRouter's `provider/model-name` format; you can swap in any model OpenRouter supports (e.g. `anthropic/claude-opus-4-8`, `openai/gpt-4o`) without any code changes.

## CLI

```bash
feedscribe poll                     # check all channels, process new videos
feedscribe process <url-or-id>      # process a specific video
feedscribe process <url> --force    # reprocess even if already seen
```

## On-demand processing from your phone

Add one YouTube URL per line to `queue.txt`, then commit and push. The `process.yml` workflow fires automatically, processes each URL, empties the file, and commits the updated state — all with `[skip ci]` to avoid loops.

```
# queue.txt
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/abc123
```

## GitHub Actions

Two workflows are included:

- **`poll.yml`** — runs Mon & Fri at 1am UTC (also triggerable manually via `workflow_dispatch`). Processes new videos from all configured channels and commits updated state.
- **`process.yml`** — triggers on any push that modifies `queue.txt`. Processes all URLs in the queue, then clears the file and commits in a single `[skip ci]` commit.

Both workflows require the 7 environment variables above to be set as GitHub repository secrets (`Settings → Secrets and variables → Actions`).

## Generated notes format

Notes are delivered as an email attachment named `{channel}_{title_in_snake_case}.md`:

```markdown
---
date: 2026-06-21
tags:
  - rational_reminder
  - personal_finance
  - behavioural_economics
source: https://youtube.com/watch?v=abc123
---

## TL;DR
3–5 sentences capturing the episode in a nutshell.

## Key Takeaways
- Point one
- Point two

## Detailed Notes

### Topic One
...
```

## Running tests

```bash
python3 -m pytest
```

All external services (OpenRouter, Resend, YouTube APIs) are mocked — no API keys needed for tests.
