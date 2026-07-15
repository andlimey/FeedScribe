# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FeedScribe monitors YouTube channels for new uploads, fetches transcripts, generates structured
Markdown notes via an LLM (OpenRouter), and emails them (Resend) as an HTML body + `.md` attachment.
It runs unattended via GitHub Actions — there is no server or database; a JSON file committed to
the repo is the only state.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python3 -m pytest                          # run all tests
python3 -m pytest tests/test_pipeline.py   # run one file
python3 -m pytest tests/test_pipeline.py::test_poll_processes_new_items  # single test

feedscribe poll                            # check all channels, process new videos
feedscribe process <url-or-id>             # process a specific video
feedscribe process <url> --force           # reprocess even if already seen
```

There is no configured linter/formatter/type-checker in this repo (no ruff/black/mypy config) — don't
assume one when verifying changes.

## Architecture

The pipeline is a straight line, wired together at the boundary and unit-tested via `MagicMock` at
each seam (see `tests/test_pipeline.py`):

```
YouTubeSource.fetch_recent/fetch_by_url → YouTubeTranscriber.fetch → OpenRouterProvider.generate_notes → EmailNotifier.send → JsonStateStore.mark_processed
```

- **`feedscribe/pipeline.py`** — `Pipeline` orchestrates the five collaborators above via constructor
  injection (no framework/DI container). `process_item` is the single-video happy path; `poll` iterates
  configured channels and skips already-processed items via `state.is_processed`; `process_url` is the
  same for a single ad-hoc URL, with a `force` override.
- **`feedscribe/cli.py`** — `_build_pipeline()` is the composition root: loads `.env` and `config.yaml`,
  reads API keys from environment variables, and constructs all five collaborators. Click commands
  (`poll`, `process`) are thin wrappers over `Pipeline`.
- **`feedscribe/config.py`** — Pydantic models for `config.yaml` (`channels`, `llm.models`,
  `polling.max_videos_per_poll`, `state.path`). `llm.models` is an ordered list passed straight through
  to OpenRouter, which handles fallback between models itself (rate limit/outage/content filter) —
  no retry logic lives in this codebase.
- **`feedscribe/models.py`** — the three data objects that flow through the pipeline: `ContentItem`
  (a video), `Transcript`, `Notes` (rendered markdown + target filename). All Pydantic.
- **`feedscribe/sources/youtube.py`** — `YouTubeSource` talks to the YouTube Data API v3 directly via
  `urllib` (no google-api-python-client dependency). Resolves a channel handle/URL to a channel ID,
  derives the uploads playlist ID by swapping `UC` → `UU`, then filters out Shorts by duration
  (`SHORTS_MAX_DURATION_SECONDS = 180`).
- **`feedscribe/transcripts/youtube.py`** — wraps `youtube_transcript_api`. Requires a Webshare
  residential proxy in practice: YouTube blocks the transcript endpoint from most IPs including GitHub
  Actions runners, so `proxy_config` is threaded through from env vars in `cli.py`.
- **`feedscribe/llm/openrouter.py`** — builds one fixed prompt (`_PROMPT`) demanding a specific Markdown
  structure (YAML frontmatter with `date`/`tags`/`source`, then `## TL;DR`, `## Key Takeaways`,
  `## Detailed Notes`), sends it via the official `openrouter` SDK's `chat.send(models=[...])`, and
  derives the attachment filename as `{channel}_{snake_case(title)}.md`.
- **`feedscribe/notifiers/email.py`** — strips the YAML frontmatter before rendering Markdown → HTML
  (via `markdown-it-py`) for the email body, but the *raw* markdown (frontmatter included) is what gets
  base64-attached as the `.md` file, since that file is meant to be dropped straight into an Obsidian vault.
- **`feedscribe/state.py`** — `JsonStateStore` is a flat JSON file (`{"processed": [...]}`), rewritten
  in full on every write. No concurrency handling — the GitHub Actions workflows rely on jobs not
  overlapping, and `poll.yml`/`process.yml` each commit the updated state file back to the repo with
  `[skip ci]` to avoid triggering themselves.

## Test structure

Test layout mirrors `feedscribe/` package-for-package. Every external service (OpenRouter, Resend,
YouTube Data API, `youtube_transcript_api`) is mocked — no network calls, no API keys needed to run
the suite. `Pipeline` tests inject `MagicMock` for all five collaborators rather than hitting real
implementations.

## GitHub Actions are the only runtime

There's no long-running process. `poll.yml` runs on a schedule (Mon/Fri 1am UTC) plus manual dispatch;
`process.yml` triggers on any push touching `queue.txt` (the phone-friendly on-demand queue — one URL
per line, cleared after processing). Both workflows `pip install -e .` fresh, run a `feedscribe` CLI
command, then commit state changes back with `git push`. Keep this in mind when changing state-file
shape or CLI behavior — it must work non-interactively with no persistent environment between runs.
