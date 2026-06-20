# FeedScribe — Design Document

## Context

FeedScribe is a personal tool that monitors YouTube channels for newly uploaded videos, downloads their transcripts, generates structured notes via an LLM, and delivers them by email (with a `.md` attachment) so they can be dropped into an Obsidian vault. The user doesn't have time to watch every episode and wants an async way to stay on top of content.

The system also supports on-demand processing of specific videos (triggered from a phone via GitHub), and is modular enough to swap out sources, LLMs, and notification channels in future.

---

## Architecture

Four abstract layers wired together by a `Pipeline` orchestrator:

```
Source → Transcriber → LLM → Notifier
```

State is tracked in a committed JSON file. Two GitHub Actions workflows handle scheduling and on-demand triggering. No long-running server required.

---

## Project Structure

```
feedscribe/
├── feedscribe/
│   ├── __init__.py
│   ├── cli.py                  # Click CLI: poll, process
│   ├── config.py               # YAML → Pydantic models
│   ├── models.py               # Shared dataclasses: ContentItem, Transcript, Notes
│   ├── pipeline.py             # Orchestrator
│   ├── state.py                # Abstract StateStore + JsonStateStore
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract ContentSource
│   │   └── youtube.py          # RSS feed implementation (feedparser)
│   ├── transcripts/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract Transcriber
│   │   └── youtube.py          # youtube-transcript-api implementation
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract LLMProvider
│   │   └── gemini.py           # google-genai (from google import genai)
│   └── notifiers/
│       ├── __init__.py
│       ├── base.py             # Abstract Notifier
│       └── email.py            # Resend implementation
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── rss_feed.xml        # Sample RSS response
│   │   ├── transcript.txt      # Sample transcript
│   │   └── notes.md            # Expected notes output (snapshot)
│   ├── test_state.py
│   ├── test_pipeline.py
│   ├── sources/
│   │   └── test_youtube.py
│   ├── transcripts/
│   │   └── test_youtube.py
│   ├── llm/
│   │   └── test_gemini.py
│   └── notifiers/
│       └── test_email.py
├── .github/
│   └── workflows/
│       ├── poll.yml
│       └── process.yml
├── .feedscribe/
│   └── processed.json          # State file (committed, updated by workflows)
├── queue.txt                   # On-demand queue (add URL, commit to trigger)
├── config.yaml
├── config.yaml.example
├── .env                        # Gitignored
├── .env.example
├── .gitignore
└── pyproject.toml
```

---

## Data Models (`models.py`)

```python
class ContentItem(BaseModel):
    id: str                  # YouTube video ID
    title: str
    url: str
    source: str              # "youtube"
    channel: str             # snake_case name from config, e.g. "rational_reminder"
    published_at: datetime

class Transcript(BaseModel):
    content_id: str
    text: str

class Notes(BaseModel):
    content_id: str
    filename: str            # e.g. rational_reminder_why_you_should_index.md
    markdown: str            # full markdown with frontmatter
```

---

## Abstract Interfaces

```python
# sources/base.py
class ContentSource(ABC):
    def fetch_recent(self, channel_cfg: ChannelConfig) -> list[ContentItem]: ...

# transcripts/base.py
class Transcriber(ABC):
    def fetch(self, item: ContentItem) -> Transcript: ...

# llm/base.py
class LLMProvider(ABC):
    def generate_notes(self, item: ContentItem, transcript: Transcript) -> Notes: ...

# notifiers/base.py
class Notifier(ABC):
    def send(self, item: ContentItem, notes: Notes) -> None: ...

# state.py
class StateStore(ABC):
    def is_processed(self, content_id: str) -> bool: ...
    def mark_processed(self, item: ContentItem) -> None: ...
    def list_processed(self) -> list[dict]: ...
```

---

## Concrete Implementations

### `sources/youtube.py` — RSS polling
- Resolves `@handle` URLs to channel IDs using `yt-dlp --print channel_id <channel_url>`
- Fetches `https://www.youtube.com/feeds/videos.xml?channel_id=UCxxx` via `feedparser`
- Returns up to `polling.max_videos_per_poll` recent `ContentItem`s sorted newest-first

### `transcripts/youtube.py` — Transcript fetching
- Uses `youtube-transcript-api` to fetch auto-generated or manual captions
- Joins transcript segments into a single text string

### `llm/gemini.py` — Notes generation
- Uses `from google import genai` (`google-genai` package)
- Model: `gemini-2.5-flash`
- Prompt instructs the model to output a complete markdown document with:
  - Frontmatter: `date`, `tags` (channel name + LLM-generated topic tags in `snake_case`), `source`
  - `## TL;DR` — 3–5 sentence summary
  - `## Key Takeaways` — bulleted list
  - `## Detailed Notes` — structured sections by topic
- Filename derived from title: title → snake_case, prepended with channel name

### `notifiers/email.py` — Resend email
- Subject: `FeedScribe [Rational Reminder]: Why You Should Index`
  (channel name title-cased from the `name` field in config)
- Body: markdown rendered to HTML via `markdown` package
- Attachment: the `.md` file (same content as body source)
- Recipient: `RESEND_TO_EMAIL` from env

### `state.py` — JsonStateStore
- Reads/writes `.feedscribe/processed.json`
- Schema:
  ```json
  {
    "processed": [
      {
        "id": "abc123",
        "url": "https://youtube.com/watch?v=abc123",
        "title": "Episode Title",
        "channel": "rational_reminder",
        "processed_at": "2026-06-19T09:00:00Z"
      }
    ]
  }
  ```

---

## CLI (`cli.py`)

Built with `click`:

```
feedscribe poll                     # check all channels, process unseen videos
feedscribe process <url-or-id>      # process a specific video (checks state)
feedscribe process <url> --force    # reprocess even if already seen
```

`poll` flow:
1. For each channel in config: fetch recent items via `ContentSource`
2. Filter out IDs already in `StateStore`
3. For each new item: `Transcriber.fetch` → `LLMProvider.generate_notes` → `Notifier.send` → `StateStore.mark_processed`

`process <url>` flow:
1. Construct `ContentItem` directly from URL (extract video ID, fetch metadata)
2. Check `StateStore.is_processed` — skip if already seen unless `--force` passed
3. Same pipeline as above; always calls `StateStore.mark_processed` after sending

---

## Config

`config.yaml` (committed to repo):
```yaml
channels:
  - url: https://www.youtube.com/@rationalreminder/videos
    name: rational_reminder
    type: youtube
  - url: https://www.youtube.com/@pragmaticengineer/videos
    name: pragmatic_engineer
    type: youtube

llm:
  provider: gemini
  model: gemini-2.5-flash

notifier:
  provider: email

polling:
  max_videos_per_poll: 5

state:
  path: .feedscribe/processed.json
```

`.env` (gitignored):
```
GEMINI_API_KEY=...
RESEND_API_KEY=...
RESEND_FROM_EMAIL=...
RESEND_TO_EMAIL=...
```

---

## Notes Markdown Format

Filename: `{channel}_{title_in_snake_case}.md`

```markdown
---
date: 2026-06-19
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

### Topic Two
...
```

---

## GitHub Actions Workflows

### `.github/workflows/poll.yml`
- Trigger: `schedule: cron: '0 1 * * 1,5'` (Mon & Fri, 1am UTC)
- Steps:
  1. `actions/checkout`
  2. Setup Python, create/activate `.venv`, install deps
  3. Run `feedscribe poll`
  4. Commit updated `processed.json` back if changed:
     `git diff --quiet || (git add .feedscribe/processed.json && git commit -m "chore: update processed state [skip ci]" && git push)`

### `.github/workflows/process.yml`
- Trigger: push when `queue.txt` changes
  ```yaml
  on:
    push:
      paths:
        - 'queue.txt'
  ```
- Steps:
  1. `actions/checkout`
  2. Setup Python, create/activate `.venv`, install deps
  3. Read each non-empty line from `queue.txt`, run `feedscribe process <url>` for each
  4. Empty `queue.txt`; commit both `queue.txt` and `processed.json` in a single commit with `[skip ci]`

Both workflows inject secrets as environment variables:
`GEMINI_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_TO_EMAIL`

---

## Dependencies (`pyproject.toml`)

```toml
[project]
name = "feedscribe"
requires-python = ">=3.11"
dependencies = [
    "click",
    "pydantic",
    "pyyaml",
    "python-dotenv",
    "feedparser",
    "yt-dlp",
    "youtube-transcript-api",
    "google-genai",
    "resend",
    "markdown",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-mock"]

[project.scripts]
feedscribe = "feedscribe.cli:cli"
```

Setup:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Testing Strategy

`pytest` + `pytest-mock`. No real network calls — all external services mocked at the boundary.

| Test file | What it tests |
|---|---|
| `test_state.py` | `JsonStateStore` CRUD against a temp file |
| `sources/test_youtube.py` | RSS XML parsing using `fixtures/rss_feed.xml`; asserts correct `ContentItem` list |
| `transcripts/test_youtube.py` | Mocked `youtube-transcript-api`; asserts `Transcript.text` assembled correctly |
| `llm/test_gemini.py` | Mocked `genai` client; asserts frontmatter fields and all three sections present in output |
| `notifiers/test_email.py` | Mocked `resend`; asserts subject format, attachment filename, and recipient |
| `test_pipeline.py` | Full pipeline with fixture data and mocked layers; asserts `Notifier.send` called with correct `Notes` |

---

## Verification

1. Set up `.env` with real API keys
2. Run `feedscribe process <any-youtube-url>` locally — confirm email arrives with correct subject, HTML body, and `.md` attachment
3. Open attachment — confirm frontmatter, TL;DR, Key Takeaways, and Detailed Notes sections are present
4. Run again without `--force` — confirm no duplicate email (state check works)
5. Add a URL to `queue.txt`, push — confirm GitHub Actions `process.yml` triggers, email arrives, `queue.txt` emptied
6. Wait for scheduled `poll.yml` run (or trigger manually) — confirm new channel videos are picked up
7. Run `pytest` — all tests pass
