# FeedScribe — YouTube → Notes → Email

FeedScribe monitors YouTube channels for newly uploaded videos, fetches their transcripts, and uses Gemini to generate structured markdown notes delivered to your inbox as an HTML email with a `.md` attachment — ready to drop into an Obsidian vault.

It runs entirely via GitHub Actions: a scheduled poll (Mon/Fri at 1am UTC) and an on-demand queue you can trigger from your phone by editing a text file.

## How it works

```
YouTube RSS → Transcript → Gemini (gemini-2.5-flash) → Resend email + .md attachment
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
| `GEMINI_API_KEY` | Google Gemini API key |
| `RESEND_API_KEY` | Resend email API key |
| `RESEND_FROM_EMAIL` | Sender address (e.g. `feedscribe@yourdomain.com`) |
| `RESEND_TO_EMAIL` | Recipient address |

## Configuration

Edit `config.yaml` to control which channels to watch, the LLM model, how many videos to process per poll (default: 5), and where state is stored. See [config.yaml](config.yaml) for the full structure.

```yaml
channels:
  - url: https://www.youtube.com/@rationalreminder/videos
    name: rational_reminder
    type: youtube

llm:
  provider: gemini
  model: gemini-2.5-flash

polling:
  max_videos_per_poll: 5
```

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

Both workflows require the 4 environment variables above to be set as repository secrets (`Settings → Secrets and variables → Actions`).

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

All external services (Gemini, Resend, YouTube APIs) are mocked — no API keys needed for tests.
