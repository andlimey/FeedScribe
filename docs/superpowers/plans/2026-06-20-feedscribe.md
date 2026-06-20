# FeedScribe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that monitors YouTube channels via RSS, generates LLM-powered Obsidian notes, and delivers them by email — triggered on a schedule and on-demand via GitHub Actions.

**Architecture:** Four abstract layers (Source → Transcriber → LLM → Notifier) wired by a Pipeline orchestrator. State persists in a committed JSON file. Two GitHub Actions workflows handle scheduled polling (Mon/Fri 1am UTC) and on-demand processing via `queue.txt` edits.

**Tech Stack:** Python 3.11+, Click, Pydantic v2, feedparser, yt-dlp, youtube-transcript-api, google-genai, resend, Markdown, pytest, pytest-mock, GitHub Actions

## Global Constraints

- Python ≥ 3.11
- Virtual environment at `.venv/` in project root
- `from google import genai` — use `google-genai` package (NOT `google-generativeai`)
- Gemini model: `gemini-2.5-flash`
- All secrets via environment variables (`.env` locally, GitHub secrets in CI)
- State file: `.feedscribe/processed.json` (committed to repo)
- Tags in snake_case throughout (channel names, topic tags)
- No real network calls in tests — mock all external services at the boundary
- TDD: write failing test first, then implement

---

## File Map

```
feedscribe/                         ← Python package
├── __init__.py
├── cli.py                          ← Click entry point (poll, process)
├── config.py                       ← YAML → Pydantic models
├── models.py                       ← ContentItem, Transcript, Notes
├── pipeline.py                     ← Orchestrator
├── state.py                        ← StateStore ABC + JsonStateStore
├── sources/
│   ├── __init__.py
│   ├── base.py                     ← ContentSource ABC
│   └── youtube.py                  ← RSS + yt-dlp fetch_by_url
├── transcripts/
│   ├── __init__.py
│   ├── base.py                     ← Transcriber ABC
│   └── youtube.py                  ← youtube-transcript-api
├── llm/
│   ├── __init__.py
│   ├── base.py                     ← LLMProvider ABC
│   └── gemini.py                   ← google-genai implementation
└── notifiers/
    ├── __init__.py
    ├── base.py                     ← Notifier ABC
    └── email.py                    ← Resend implementation

tests/
├── conftest.py
├── fixtures/
│   ├── rss_feed.xml
│   ├── transcript.txt
│   └── notes.md
├── test_state.py
├── test_pipeline.py
├── sources/
│   ├── __init__.py
│   └── test_youtube.py
├── transcripts/
│   ├── __init__.py
│   └── test_youtube.py
├── llm/
│   ├── __init__.py
│   └── test_gemini.py
└── notifiers/
    ├── __init__.py
    └── test_email.py

.github/workflows/
├── poll.yml
└── process.yml

.feedscribe/processed.json          ← committed state file
queue.txt                           ← on-demand trigger file (committed, emptied by CI)
config.yaml                         ← channel + LLM + notifier config
config.yaml.example
.env.example
pyproject.toml
.gitignore
docs/design.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `config.yaml`
- Create: `config.yaml.example`
- Create: `queue.txt`
- Create: `.feedscribe/processed.json`
- Create: all `__init__.py` files
- Create: `feedscribe/__init__.py`, `feedscribe/sources/__init__.py`, `feedscribe/transcripts/__init__.py`, `feedscribe/llm/__init__.py`, `feedscribe/notifiers/__init__.py`
- Create: `tests/__init__.py`, `tests/sources/__init__.py`, `tests/transcripts/__init__.py`, `tests/llm/__init__.py`, `tests/notifiers/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `feedscribe` package importable; `feedscribe` CLI entry point registered; `pytest` runnable

- [ ] **Step 1: Initialize git and create directory structure**

```bash
cd /home/andy-chanwy/Projects/FeedScribe
git init
mkdir -p feedscribe/sources feedscribe/transcripts feedscribe/llm feedscribe/notifiers
mkdir -p tests/fixtures tests/sources tests/transcripts tests/llm tests/notifiers
mkdir -p .feedscribe .github/workflows docs/superpowers/plans
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "feedscribe"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
    "feedparser>=6.0",
    "yt-dlp>=2024.0",
    "youtube-transcript-api>=0.6",
    "google-genai>=1.0",
    "resend>=2.0",
    "Markdown>=3.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.0",
]

[project.scripts]
feedscribe = "feedscribe.cli:cli"
```

- [ ] **Step 3: Create `.gitignore`**

```
.venv/
__pycache__/
*.pyc
*.egg-info/
dist/
.env
```

- [ ] **Step 4: Create `.env.example`**

```
GEMINI_API_KEY=your_gemini_api_key_here
RESEND_API_KEY=your_resend_api_key_here
RESEND_FROM_EMAIL=feedscribe@yourdomain.com
RESEND_TO_EMAIL=you@example.com
```

- [ ] **Step 5: Create `config.yaml`**

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

- [ ] **Step 6: Create `config.yaml.example`** (same content as `config.yaml`)

- [ ] **Step 7: Create `queue.txt`** (empty file)

- [ ] **Step 8: Create `.feedscribe/processed.json`**

```json
{
  "processed": []
}
```

- [ ] **Step 9: Create all `__init__.py` files** (all empty)

```bash
touch feedscribe/__init__.py
touch feedscribe/sources/__init__.py
touch feedscribe/transcripts/__init__.py
touch feedscribe/llm/__init__.py
touch feedscribe/notifiers/__init__.py
touch tests/__init__.py
touch tests/sources/__init__.py
touch tests/transcripts/__init__.py
touch tests/llm/__init__.py
touch tests/notifiers/__init__.py
```

- [ ] **Step 10: Create `tests/conftest.py`** (empty for now)

```python
```

- [ ] **Step 11: Create virtual environment and install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

- [ ] **Step 12: Verify pytest runs (zero tests)**

```bash
source .venv/bin/activate
pytest
```

Expected: `no tests ran` or `0 passed`

- [ ] **Step 13: Commit**

```bash
git add .
git commit -m "chore: initial project scaffolding"
```

---

### Task 2: Models

**Files:**
- Create: `feedscribe/models.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces:
  - `ContentItem(id, title, url, source, channel, published_at)` — Pydantic BaseModel
  - `Transcript(content_id, text)` — Pydantic BaseModel
  - `Notes(content_id, filename, markdown)` — Pydantic BaseModel

- [ ] **Step 1: Write failing test**

Create `tests/test_models.py`:

```python
from datetime import datetime, timezone
from feedscribe.models import ContentItem, Transcript, Notes


def test_content_item_fields():
    item = ContentItem(
        id="abc123",
        title="Test Episode",
        url="https://youtube.com/watch?v=abc123",
        source="youtube",
        channel="rational_reminder",
        published_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )
    assert item.id == "abc123"
    assert item.channel == "rational_reminder"


def test_transcript_fields():
    t = Transcript(content_id="abc123", text="Hello world.")
    assert t.content_id == "abc123"
    assert t.text == "Hello world."


def test_notes_fields():
    n = Notes(
        content_id="abc123",
        filename="rational_reminder_test.md",
        markdown="---\ndate: 2026-06-19\n---\n",
    )
    assert n.filename == "rational_reminder_test.md"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate
pytest tests/test_models.py -v
```

Expected: `ImportError: cannot import name 'ContentItem' from 'feedscribe.models'`

- [ ] **Step 3: Implement `feedscribe/models.py`**

```python
from datetime import datetime
from pydantic import BaseModel


class ContentItem(BaseModel):
    id: str
    title: str
    url: str
    source: str
    channel: str
    published_at: datetime


class Transcript(BaseModel):
    content_id: str
    text: str


class Notes(BaseModel):
    content_id: str
    filename: str
    markdown: str
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add feedscribe/models.py tests/test_models.py
git commit -m "feat: add core data models"
```

---

### Task 3: Config Loader

**Files:**
- Create: `feedscribe/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces:
  - `ChannelConfig(url: str, name: str, type: str)` — Pydantic BaseModel
  - `LLMConfig(provider: str, model: str)` — Pydantic BaseModel
  - `NotifierConfig(provider: str)` — Pydantic BaseModel
  - `PollingConfig(max_videos_per_poll: int = 5)` — Pydantic BaseModel
  - `StateConfig(path: str = ".feedscribe/processed.json")` — Pydantic BaseModel
  - `AppConfig(channels, llm, notifier, polling, state)` — Pydantic BaseModel
  - `load_config(path: str) -> AppConfig`

- [ ] **Step 1: Write failing test**

Create `tests/test_config.py`:

```python
import pytest
import yaml
from pathlib import Path
from feedscribe.config import load_config, AppConfig, ChannelConfig


def test_load_config(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
channels:
  - url: https://www.youtube.com/@test/videos
    name: test_channel
    type: youtube

llm:
  provider: gemini
  model: gemini-2.5-flash

notifier:
  provider: email

polling:
  max_videos_per_poll: 3

state:
  path: .feedscribe/processed.json
"""
    )
    config = load_config(str(cfg_file))

    assert isinstance(config, AppConfig)
    assert len(config.channels) == 1
    assert config.channels[0].name == "test_channel"
    assert config.llm.model == "gemini-2.5-flash"
    assert config.polling.max_videos_per_poll == 3
    assert config.state.path == ".feedscribe/processed.json"


def test_polling_defaults_to_5(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
channels: []
llm:
  provider: gemini
  model: gemini-2.5-flash
notifier:
  provider: email
"""
    )
    config = load_config(str(cfg_file))
    assert config.polling.max_videos_per_poll == 5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `feedscribe/config.py`**

```python
import yaml
from pydantic import BaseModel


class ChannelConfig(BaseModel):
    url: str
    name: str
    type: str


class LLMConfig(BaseModel):
    provider: str
    model: str


class NotifierConfig(BaseModel):
    provider: str


class PollingConfig(BaseModel):
    max_videos_per_poll: int = 5


class StateConfig(BaseModel):
    path: str = ".feedscribe/processed.json"


class AppConfig(BaseModel):
    channels: list[ChannelConfig]
    llm: LLMConfig
    notifier: NotifierConfig
    polling: PollingConfig = PollingConfig()
    state: StateConfig = StateConfig()


def load_config(path: str = "config.yaml") -> AppConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add feedscribe/config.py tests/test_config.py
git commit -m "feat: add config loader"
```

---

### Task 4: State Management

**Files:**
- Create: `feedscribe/state.py`
- Create: `tests/test_state.py`

**Interfaces:**
- Consumes: `ContentItem` from `feedscribe.models`
- Produces:
  - `StateStore` — ABC with `is_processed(content_id: str) -> bool`, `mark_processed(item: ContentItem) -> None`, `list_processed() -> list[dict]`
  - `JsonStateStore(path: str)` — reads/writes `processed.json`

- [ ] **Step 1: Write failing test**

Create `tests/test_state.py`:

```python
import pytest
from datetime import datetime, timezone
from feedscribe.state import JsonStateStore
from feedscribe.models import ContentItem


@pytest.fixture
def item():
    return ContentItem(
        id="abc123",
        title="Test Episode",
        url="https://youtube.com/watch?v=abc123",
        source="youtube",
        channel="test_channel",
        published_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )


@pytest.fixture
def store(tmp_path):
    return JsonStateStore(str(tmp_path / "processed.json"))


def test_new_item_not_processed(store, item):
    assert not store.is_processed(item.id)


def test_mark_processed(store, item):
    store.mark_processed(item)
    assert store.is_processed(item.id)


def test_list_processed(store, item):
    store.mark_processed(item)
    entries = store.list_processed()
    assert len(entries) == 1
    assert entries[0]["id"] == "abc123"
    assert entries[0]["channel"] == "test_channel"


def test_state_persists_across_instances(tmp_path, item):
    path = str(tmp_path / "processed.json")
    store1 = JsonStateStore(path)
    store1.mark_processed(item)

    store2 = JsonStateStore(path)
    assert store2.is_processed(item.id)


def test_creates_parent_directory(tmp_path, item):
    path = str(tmp_path / "subdir" / "processed.json")
    store = JsonStateStore(path)
    store.mark_processed(item)
    assert store.is_processed(item.id)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_state.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `feedscribe/state.py`**

```python
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from feedscribe.models import ContentItem


class StateStore(ABC):
    @abstractmethod
    def is_processed(self, content_id: str) -> bool: ...

    @abstractmethod
    def mark_processed(self, item: ContentItem) -> None: ...

    @abstractmethod
    def list_processed(self) -> list[dict]: ...


class JsonStateStore(StateStore):
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({"processed": []}))

    def _load(self) -> dict:
        return json.loads(self._path.read_text())

    def _save(self, data: dict) -> None:
        self._path.write_text(json.dumps(data, indent=2, default=str))

    def is_processed(self, content_id: str) -> bool:
        data = self._load()
        return any(entry["id"] == content_id for entry in data["processed"])

    def mark_processed(self, item: ContentItem) -> None:
        data = self._load()
        data["processed"].append(
            {
                "id": item.id,
                "url": item.url,
                "title": item.title,
                "channel": item.channel,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save(data)

    def list_processed(self) -> list[dict]:
        return self._load()["processed"]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_state.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add feedscribe/state.py tests/test_state.py
git commit -m "feat: add state management"
```

---

### Task 5: YouTube Source

**Files:**
- Create: `feedscribe/sources/base.py`
- Create: `feedscribe/sources/youtube.py`
- Create: `tests/fixtures/rss_feed.xml`
- Create: `tests/sources/test_youtube.py`

**Interfaces:**
- Consumes: `ContentItem` from `feedscribe.models`; `ChannelConfig` from `feedscribe.config`
- Produces:
  - `ContentSource` — ABC with `fetch_recent(channel_cfg: ChannelConfig, max_items: int) -> list[ContentItem]` and `fetch_by_url(url_or_id: str) -> ContentItem`
  - `YouTubeSource()` — RSS + yt-dlp implementation

- [ ] **Step 1: Create RSS fixture**

Create `tests/fixtures/rss_feed.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>abc123</yt:videoId>
    <title>Test Episode One</title>
    <published>2026-06-19T10:00:00+00:00</published>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
  </entry>
  <entry>
    <yt:videoId>def456</yt:videoId>
    <title>Test Episode Two</title>
    <published>2026-06-18T10:00:00+00:00</published>
    <link rel="alternate" href="https://www.youtube.com/watch?v=def456"/>
  </entry>
  <entry>
    <yt:videoId>ghi789</yt:videoId>
    <title>Test Episode Three</title>
    <published>2026-06-17T10:00:00+00:00</published>
    <link rel="alternate" href="https://www.youtube.com/watch?v=ghi789"/>
  </entry>
</feed>
```

- [ ] **Step 2: Write failing tests**

Create `tests/sources/test_youtube.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from feedscribe.sources.youtube import YouTubeSource
from feedscribe.config import ChannelConfig


@pytest.fixture
def channel_cfg():
    return ChannelConfig(
        url="https://www.youtube.com/@testchannel/videos",
        name="test_channel",
        type="youtube",
    )


@pytest.fixture
def source():
    return YouTubeSource()


def _make_feed_mock():
    entries = []
    for video_id, title, date_tuple in [
        ("abc123", "Test Episode One", (2026, 6, 19, 10, 0, 0, 0, 0, 0)),
        ("def456", "Test Episode Two", (2026, 6, 18, 10, 0, 0, 0, 0, 0)),
        ("ghi789", "Test Episode Three", (2026, 6, 17, 10, 0, 0, 0, 0, 0)),
    ]:
        e = MagicMock()
        e.yt_videoid = video_id
        e.title = title
        e.published_parsed = date_tuple
        entries.append(e)
    feed = MagicMock()
    feed.entries = entries
    return feed


def test_fetch_recent_returns_content_items(source, channel_cfg):
    with patch.object(source, "_resolve_channel_id", return_value="UCtest123"), \
         patch("feedparser.parse", return_value=_make_feed_mock()):
        items = source.fetch_recent(channel_cfg, max_items=5)

    assert len(items) == 3
    assert items[0].id == "abc123"
    assert items[0].title == "Test Episode One"
    assert items[0].channel == "test_channel"
    assert items[0].source == "youtube"
    assert items[0].url == "https://www.youtube.com/watch?v=abc123"


def test_fetch_recent_respects_max_items(source, channel_cfg):
    with patch.object(source, "_resolve_channel_id", return_value="UCtest123"), \
         patch("feedparser.parse", return_value=_make_feed_mock()):
        items = source.fetch_recent(channel_cfg, max_items=2)

    assert len(items) == 2
    assert items[0].id == "abc123"
    assert items[1].id == "def456"


def test_fetch_by_url_full_url(source):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Why You Should Index\tRational Reminder\n",
            returncode=0,
        )
        item = source.fetch_by_url("https://www.youtube.com/watch?v=abc123")

    assert item.id == "abc123"
    assert item.title == "Why You Should Index"
    assert item.channel == "rational_reminder"
    assert item.source == "youtube"
    assert item.url == "https://www.youtube.com/watch?v=abc123"


def test_fetch_by_url_bare_id(source):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Test Title\tTest Channel\n",
            returncode=0,
        )
        item = source.fetch_by_url("abc123")

    assert item.id == "abc123"
    assert item.channel == "test_channel"


def test_fetch_by_url_short_url(source):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Test Title\tTest Channel\n",
            returncode=0,
        )
        item = source.fetch_by_url("https://youtu.be/abc123")

    assert item.id == "abc123"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/sources/test_youtube.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Implement `feedscribe/sources/base.py`**

```python
from abc import ABC, abstractmethod

from feedscribe.config import ChannelConfig
from feedscribe.models import ContentItem


class ContentSource(ABC):
    @abstractmethod
    def fetch_recent(self, channel_cfg: ChannelConfig, max_items: int) -> list[ContentItem]: ...

    @abstractmethod
    def fetch_by_url(self, url_or_id: str) -> ContentItem: ...
```

- [ ] **Step 5: Implement `feedscribe/sources/youtube.py`**

```python
import re
import subprocess
from datetime import datetime, timezone

import feedparser

from feedscribe.config import ChannelConfig
from feedscribe.models import ContentItem
from feedscribe.sources.base import ContentSource


def _extract_video_id(url_or_id: str) -> str:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def _to_snake(text: str) -> str:
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", "_", text.strip())


class YouTubeSource(ContentSource):
    def _resolve_channel_id(self, channel_url: str) -> str:
        result = subprocess.run(
            ["yt-dlp", "--print", "channel_id", "--playlist-end", "1", channel_url],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def fetch_recent(self, channel_cfg: ChannelConfig, max_items: int) -> list[ContentItem]:
        channel_id = self._resolve_channel_id(channel_cfg.url)
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)

        items = []
        for entry in feed.entries[:max_items]:
            video_id = entry.yt_videoid
            items.append(
                ContentItem(
                    id=video_id,
                    title=entry.title,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    source="youtube",
                    channel=channel_cfg.name,
                    published_at=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
                )
            )
        return items

    def fetch_by_url(self, url_or_id: str) -> ContentItem:
        video_id = _extract_video_id(url_or_id)
        url = f"https://www.youtube.com/watch?v={video_id}"
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s\t%(channel)s", "--no-download", url],
            capture_output=True,
            text=True,
            check=True,
        )
        parts = result.stdout.strip().split("\t")
        title, channel = parts[0], parts[1]
        return ContentItem(
            id=video_id,
            title=title,
            url=url,
            source="youtube",
            channel=_to_snake(channel),
            published_at=datetime.now(timezone.utc),
        )
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/sources/test_youtube.py -v
```

Expected: `5 passed`

- [ ] **Step 7: Commit**

```bash
git add feedscribe/sources/ tests/fixtures/rss_feed.xml tests/sources/
git commit -m "feat: add YouTube RSS source"
```

---

### Task 6: YouTube Transcriber

**Files:**
- Create: `feedscribe/transcripts/base.py`
- Create: `feedscribe/transcripts/youtube.py`
- Create: `tests/fixtures/transcript.txt`
- Create: `tests/transcripts/test_youtube.py`

**Interfaces:**
- Consumes: `ContentItem`, `Transcript` from `feedscribe.models`
- Produces:
  - `Transcriber` — ABC with `fetch(item: ContentItem) -> Transcript`
  - `YouTubeTranscriber()` — uses `youtube_transcript_api.YouTubeTranscriptApi`

- [ ] **Step 1: Create transcript fixture**

Create `tests/fixtures/transcript.txt`:

```
Hello and welcome to today's episode. We are going to discuss personal finance and long-term investment strategies. The evidence strongly supports a diversified low-cost index fund approach. Staying the course during market downturns is critical to long-term success.
```

- [ ] **Step 2: Write failing test**

Create `tests/transcripts/test_youtube.py`:

```python
import pytest
from unittest.mock import patch
from feedscribe.transcripts.youtube import YouTubeTranscriber
from feedscribe.models import ContentItem
from datetime import datetime, timezone


@pytest.fixture
def item():
    return ContentItem(
        id="abc123",
        title="Test Episode",
        url="https://youtube.com/watch?v=abc123",
        source="youtube",
        channel="test_channel",
        published_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )


def test_fetch_joins_segments(item):
    segments = [
        {"text": "Hello world", "start": 0.0, "duration": 1.0},
        {"text": "how are you", "start": 1.0, "duration": 1.0},
    ]
    with patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        return_value=segments,
    ):
        transcriber = YouTubeTranscriber()
        transcript = transcriber.fetch(item)

    assert transcript.content_id == "abc123"
    assert transcript.text == "Hello world how are you"


def test_fetch_returns_correct_content_id(item):
    with patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        return_value=[{"text": "Test", "start": 0.0, "duration": 1.0}],
    ):
        transcriber = YouTubeTranscriber()
        transcript = transcriber.fetch(item)

    assert transcript.content_id == item.id
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/transcripts/test_youtube.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Implement `feedscribe/transcripts/base.py`**

```python
from abc import ABC, abstractmethod

from feedscribe.models import ContentItem, Transcript


class Transcriber(ABC):
    @abstractmethod
    def fetch(self, item: ContentItem) -> Transcript: ...
```

- [ ] **Step 5: Implement `feedscribe/transcripts/youtube.py`**

```python
from youtube_transcript_api import YouTubeTranscriptApi

from feedscribe.models import ContentItem, Transcript
from feedscribe.transcripts.base import Transcriber


class YouTubeTranscriber(Transcriber):
    def fetch(self, item: ContentItem) -> Transcript:
        segments = YouTubeTranscriptApi.get_transcript(item.id)
        text = " ".join(seg["text"] for seg in segments)
        return Transcript(content_id=item.id, text=text)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/transcripts/test_youtube.py -v
```

Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add feedscribe/transcripts/ tests/fixtures/transcript.txt tests/transcripts/
git commit -m "feat: add YouTube transcriber"
```

---

### Task 7: Gemini LLM Provider

**Files:**
- Create: `feedscribe/llm/base.py`
- Create: `feedscribe/llm/gemini.py`
- Create: `tests/fixtures/notes.md`
- Create: `tests/llm/test_gemini.py`

**Interfaces:**
- Consumes: `ContentItem`, `Transcript`, `Notes` from `feedscribe.models`
- Produces:
  - `LLMProvider` — ABC with `generate_notes(item: ContentItem, transcript: Transcript) -> Notes`
  - `GeminiProvider(api_key: str, model: str)` — `from google import genai`
  - `_title_to_snake(title: str) -> str` — exported helper

- [ ] **Step 1: Create notes fixture**

Create `tests/fixtures/notes.md`:

```markdown
---
date: 2026-06-19
tags:
  - test_channel
  - personal_finance
  - index_investing
source: https://youtube.com/watch?v=abc123
---

## TL;DR
This episode covers the fundamentals of index investing and why passive strategies outperform active ones over time.

## Key Takeaways
- Low-cost index funds beat most active managers over 20-year periods
- Diversification reduces unsystematic risk without sacrificing expected returns
- Behavioural discipline during downturns is the primary driver of investor outcomes

## Detailed Notes

### The Case for Passive Investing
Evidence from SPIVA reports consistently shows that fewer than 10% of active managers outperform their benchmark over 20 years.

### Behavioural Finance
Emotional reactions to short-term volatility are the leading cause of underperformance among retail investors.
```

- [ ] **Step 2: Write failing tests**

Create `tests/llm/test_gemini.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from feedscribe.llm.gemini import GeminiProvider, _title_to_snake
from feedscribe.models import ContentItem, Transcript
from datetime import datetime, timezone

SAMPLE_MARKDOWN = (Path(__file__).parent.parent / "fixtures" / "notes.md").read_text()


@pytest.fixture
def item():
    return ContentItem(
        id="abc123",
        title="Why You Should Index",
        url="https://youtube.com/watch?v=abc123",
        source="youtube",
        channel="test_channel",
        published_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )


@pytest.fixture
def transcript():
    return Transcript(content_id="abc123", text="This is the transcript text.")


def _make_gemini_mock(markdown: str):
    mock_response = MagicMock()
    mock_response.text = markdown
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


def test_generate_notes_returns_correct_content_id(item, transcript):
    mock_client = _make_gemini_mock(SAMPLE_MARKDOWN)
    with patch("feedscribe.llm.gemini.genai.Client", return_value=mock_client):
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash")
        notes = provider.generate_notes(item, transcript)

    assert notes.content_id == "abc123"


def test_generate_notes_markdown_contains_sections(item, transcript):
    mock_client = _make_gemini_mock(SAMPLE_MARKDOWN)
    with patch("feedscribe.llm.gemini.genai.Client", return_value=mock_client):
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash")
        notes = provider.generate_notes(item, transcript)

    assert "---" in notes.markdown
    assert "## TL;DR" in notes.markdown
    assert "## Key Takeaways" in notes.markdown
    assert "## Detailed Notes" in notes.markdown


def test_generate_notes_filename(item, transcript):
    mock_client = _make_gemini_mock(SAMPLE_MARKDOWN)
    with patch("feedscribe.llm.gemini.genai.Client", return_value=mock_client):
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash")
        notes = provider.generate_notes(item, transcript)

    assert notes.filename == "test_channel_why_you_should_index.md"


def test_title_to_snake_basic():
    assert _title_to_snake("Why You Should Index") == "why_you_should_index"


def test_title_to_snake_punctuation():
    assert _title_to_snake("Personal Finance 101!") == "personal_finance_101"


def test_title_to_snake_extra_spaces():
    assert _title_to_snake("  Hello   World  ") == "hello_world"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/llm/test_gemini.py -v
```

Expected: `ImportError`

- [ ] **Step 4: Implement `feedscribe/llm/base.py`**

```python
from abc import ABC, abstractmethod

from feedscribe.models import ContentItem, Notes, Transcript


class LLMProvider(ABC):
    @abstractmethod
    def generate_notes(self, item: ContentItem, transcript: Transcript) -> Notes: ...
```

- [ ] **Step 5: Implement `feedscribe/llm/gemini.py`**

```python
import re
from datetime import date

from google import genai

from feedscribe.llm.base import LLMProvider
from feedscribe.models import ContentItem, Notes, Transcript

_PROMPT = """\
You are a research assistant. Generate structured notes from the following YouTube video transcript.

Video title: {title}
Channel: {channel}
Source URL: {url}
Date: {date}

Transcript:
{transcript}

Output a complete Markdown document with this exact structure:

---
date: {date}
tags:
  - {channel}
  - <2-4 relevant topic tags in snake_case>
source: {url}
---

## TL;DR
<3-5 sentence summary>

## Key Takeaways
- <key point>
- <key point>
- <key point>

## Detailed Notes

### <Topic 1>
<notes>

### <Topic 2>
<notes>

Output only the Markdown document, nothing else.\
"""


def _title_to_snake(title: str) -> str:
    title = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", "_", title.strip())


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_notes(self, item: ContentItem, transcript: Transcript) -> Notes:
        today = date.today().isoformat()
        prompt = _PROMPT.format(
            title=item.title,
            channel=item.channel,
            url=item.url,
            date=today,
            transcript=transcript.text,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        markdown = response.text.strip()
        filename = f"{item.channel}_{_title_to_snake(item.title)}.md"
        return Notes(content_id=item.id, filename=filename, markdown=markdown)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/llm/test_gemini.py -v
```

Expected: `6 passed`

- [ ] **Step 7: Commit**

```bash
git add feedscribe/llm/ tests/fixtures/notes.md tests/llm/
git commit -m "feat: add Gemini LLM provider"
```

---

### Task 8: Email Notifier

**Files:**
- Create: `feedscribe/notifiers/base.py`
- Create: `feedscribe/notifiers/email.py`
- Create: `tests/notifiers/test_email.py`

**Interfaces:**
- Consumes: `ContentItem`, `Notes` from `feedscribe.models`
- Produces:
  - `Notifier` — ABC with `send(item: ContentItem, notes: Notes) -> None`
  - `EmailNotifier(api_key: str, from_email: str, to_email: str)`
  - Subject format: `FeedScribe [Channel Name]: Title Of Episode`
  - Body: markdown rendered to HTML via `markdown.markdown()`
  - Attachment: `notes.filename` with `list(notes.markdown.encode("utf-8"))` as content

- [ ] **Step 1: Write failing tests**

Create `tests/notifiers/test_email.py`:

```python
import pytest
from unittest.mock import patch

from feedscribe.notifiers.email import EmailNotifier
from feedscribe.models import ContentItem, Notes
from datetime import datetime, timezone


@pytest.fixture
def item():
    return ContentItem(
        id="abc123",
        title="Why You Should Index",
        url="https://youtube.com/watch?v=abc123",
        source="youtube",
        channel="rational_reminder",
        published_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )


@pytest.fixture
def notes():
    return Notes(
        content_id="abc123",
        filename="rational_reminder_why_you_should_index.md",
        markdown="---\ndate: 2026-06-19\n---\n\n## TL;DR\nSummary here.",
    )


@pytest.fixture
def notifier():
    return EmailNotifier(
        api_key="test-key",
        from_email="from@example.com",
        to_email="to@example.com",
    )


def test_subject_format(notifier, item, notes):
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item, notes)

    subject = mock_send.call_args[0][0]["subject"]
    assert subject == "FeedScribe [Rational Reminder]: Why You Should Index"


def test_recipient(notifier, item, notes):
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item, notes)

    call_args = mock_send.call_args[0][0]
    assert call_args["to"] == "to@example.com"
    assert call_args["from"] == "from@example.com"


def test_html_body_rendered(notifier, item, notes):
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item, notes)

    html = mock_send.call_args[0][0]["html"]
    assert "<" in html


def test_attachment_filename(notifier, item, notes):
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item, notes)

    attachments = mock_send.call_args[0][0]["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["filename"] == "rational_reminder_why_you_should_index.md"


def test_attachment_content_is_bytes(notifier, item, notes):
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item, notes)

    content = mock_send.call_args[0][0]["attachments"][0]["content"]
    assert isinstance(content, list)
    assert content == list(notes.markdown.encode("utf-8"))


def test_channel_name_title_cased_in_subject(notifier, item, notes):
    item2 = item.model_copy(update={"channel": "pragmatic_engineer"})
    notes2 = notes.model_copy(update={"filename": "pragmatic_engineer_test.md"})
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item2, notes2)

    subject = mock_send.call_args[0][0]["subject"]
    assert "[Pragmatic Engineer]" in subject
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/notifiers/test_email.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `feedscribe/notifiers/base.py`**

```python
from abc import ABC, abstractmethod

from feedscribe.models import ContentItem, Notes


class Notifier(ABC):
    @abstractmethod
    def send(self, item: ContentItem, notes: Notes) -> None: ...
```

- [ ] **Step 4: Implement `feedscribe/notifiers/email.py`**

```python
import markdown as md
import resend

from feedscribe.models import ContentItem, Notes
from feedscribe.notifiers.base import Notifier


def _channel_display(channel: str) -> str:
    return channel.replace("_", " ").title()


def _title_from_filename(filename: str, channel: str) -> str:
    name = filename
    if name.startswith(channel + "_"):
        name = name[len(channel) + 1:]
    name = name.removesuffix(".md")
    return name.replace("_", " ").title()


class EmailNotifier(Notifier):
    def __init__(self, api_key: str, from_email: str, to_email: str) -> None:
        resend.api_key = api_key
        self._from_email = from_email
        self._to_email = to_email

    def send(self, item: ContentItem, notes: Notes) -> None:
        channel_display = _channel_display(item.channel)
        title = _title_from_filename(notes.filename, item.channel)
        subject = f"FeedScribe [{channel_display}]: {title}"

        html_body = md.markdown(notes.markdown, extensions=["fenced_code", "tables"])

        resend.Emails.send(
            {
                "from": self._from_email,
                "to": self._to_email,
                "subject": subject,
                "html": html_body,
                "attachments": [
                    {
                        "filename": notes.filename,
                        "content": list(notes.markdown.encode("utf-8")),
                    }
                ],
            }
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/notifiers/test_email.py -v
```

Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
git add feedscribe/notifiers/ tests/notifiers/
git commit -m "feat: add email notifier"
```

---

### Task 9: Pipeline Orchestrator

**Files:**
- Create: `feedscribe/pipeline.py`
- Create: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `ContentSource`, `Transcriber`, `LLMProvider`, `Notifier`, `StateStore`, `AppConfig`, `ContentItem`
- Produces:
  - `Pipeline(source, transcriber, llm, notifier, state)`
  - `Pipeline.process_item(item: ContentItem) -> None`
  - `Pipeline.poll(config: AppConfig) -> list[str]` — returns list of processed video IDs
  - `Pipeline.process_url(url_or_id: str, force: bool = False) -> bool`

- [ ] **Step 1: Write failing tests**

Create `tests/test_pipeline.py`:

```python
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from feedscribe.pipeline import Pipeline
from feedscribe.models import ContentItem, Transcript, Notes
from feedscribe.config import AppConfig, ChannelConfig, LLMConfig, NotifierConfig


@pytest.fixture
def item():
    return ContentItem(
        id="abc123",
        title="Test Episode",
        url="https://youtube.com/watch?v=abc123",
        source="youtube",
        channel="test_channel",
        published_at=datetime(2026, 6, 19, tzinfo=timezone.utc),
    )


@pytest.fixture
def transcript():
    return Transcript(content_id="abc123", text="Transcript text.")


@pytest.fixture
def notes():
    return Notes(
        content_id="abc123",
        filename="test_channel_test_episode.md",
        markdown="---\ndate: 2026-06-19\n---\n## TL;DR\nSummary.",
    )


@pytest.fixture
def app_config():
    return AppConfig(
        channels=[
            ChannelConfig(
                url="https://youtube.com/@test",
                name="test_channel",
                type="youtube",
            )
        ],
        llm=LLMConfig(provider="gemini", model="gemini-2.5-flash"),
        notifier=NotifierConfig(provider="email"),
    )


@pytest.fixture
def pipeline(item, transcript, notes):
    source = MagicMock()
    transcriber = MagicMock()
    llm = MagicMock()
    notifier = MagicMock()
    state = MagicMock()

    transcriber.fetch.return_value = transcript
    llm.generate_notes.return_value = notes
    state.is_processed.return_value = False
    source.fetch_recent.return_value = [item]
    source.fetch_by_url.return_value = item

    return Pipeline(source, transcriber, llm, notifier, state)


def test_process_item_calls_all_layers(pipeline, item, transcript, notes):
    pipeline.process_item(item)

    pipeline._transcriber.fetch.assert_called_once_with(item)
    pipeline._llm.generate_notes.assert_called_once_with(item, transcript)
    pipeline._notifier.send.assert_called_once_with(item, notes)
    pipeline._state.mark_processed.assert_called_once_with(item)


def test_poll_skips_already_processed(pipeline, item, app_config):
    pipeline._state.is_processed.return_value = True

    processed = pipeline.poll(app_config)

    assert processed == []
    pipeline._notifier.send.assert_not_called()


def test_poll_processes_new_items(pipeline, item, app_config):
    pipeline._state.is_processed.return_value = False

    processed = pipeline.poll(app_config)

    assert processed == ["abc123"]
    pipeline._notifier.send.assert_called_once()


def test_process_url_skips_if_seen(pipeline, item):
    pipeline._state.is_processed.return_value = True

    result = pipeline.process_url("https://youtube.com/watch?v=abc123", force=False)

    assert result is False
    pipeline._notifier.send.assert_not_called()


def test_process_url_force_reprocesses(pipeline, item):
    pipeline._state.is_processed.return_value = True

    result = pipeline.process_url("https://youtube.com/watch?v=abc123", force=True)

    assert result is True
    pipeline._notifier.send.assert_called_once()


def test_process_url_marks_processed(pipeline, item):
    pipeline._state.is_processed.return_value = False

    pipeline.process_url("https://youtube.com/watch?v=abc123")

    pipeline._state.mark_processed.assert_called_once_with(item)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pipeline.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `feedscribe/pipeline.py`**

```python
from feedscribe.config import AppConfig
from feedscribe.llm.base import LLMProvider
from feedscribe.models import ContentItem
from feedscribe.notifiers.base import Notifier
from feedscribe.sources.base import ContentSource
from feedscribe.state import StateStore
from feedscribe.transcripts.base import Transcriber


class Pipeline:
    def __init__(
        self,
        source: ContentSource,
        transcriber: Transcriber,
        llm: LLMProvider,
        notifier: Notifier,
        state: StateStore,
    ) -> None:
        self._source = source
        self._transcriber = transcriber
        self._llm = llm
        self._notifier = notifier
        self._state = state

    def process_item(self, item: ContentItem) -> None:
        transcript = self._transcriber.fetch(item)
        notes = self._llm.generate_notes(item, transcript)
        self._notifier.send(item, notes)
        self._state.mark_processed(item)

    def poll(self, config: AppConfig) -> list[str]:
        processed = []
        for channel_cfg in config.channels:
            items = self._source.fetch_recent(channel_cfg, config.polling.max_videos_per_poll)
            for item in items:
                if not self._state.is_processed(item.id):
                    self.process_item(item)
                    processed.append(item.id)
        return processed

    def process_url(self, url_or_id: str, force: bool = False) -> bool:
        item = self._source.fetch_by_url(url_or_id)
        if not force and self._state.is_processed(item.id):
            return False
        self.process_item(item)
        return True
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_pipeline.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add feedscribe/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator"
```

---

### Task 10: CLI

**Files:**
- Create: `feedscribe/cli.py`

**Interfaces:**
- Consumes: all layers + `load_config`, `JsonStateStore`, `YouTubeSource`, `YouTubeTranscriber`, `GeminiProvider`, `EmailNotifier`, `Pipeline`
- Produces:
  - `feedscribe poll [--config PATH]`
  - `feedscribe process URL [--force] [--config PATH]`

No unit tests for the CLI layer — it is thin wiring tested by the integration steps in Verification.

- [ ] **Step 1: Implement `feedscribe/cli.py`**

```python
import os

import click
from dotenv import load_dotenv

from feedscribe.config import load_config
from feedscribe.llm.gemini import GeminiProvider
from feedscribe.notifiers.email import EmailNotifier
from feedscribe.pipeline import Pipeline
from feedscribe.sources.youtube import YouTubeSource
from feedscribe.state import JsonStateStore
from feedscribe.transcripts.youtube import YouTubeTranscriber

load_dotenv()


def _build_pipeline(config_path: str) -> tuple[Pipeline, object]:
    config = load_config(config_path)
    state = JsonStateStore(config.state.path)
    source = YouTubeSource()
    transcriber = YouTubeTranscriber()
    llm = GeminiProvider(
        api_key=os.environ["GEMINI_API_KEY"],
        model=config.llm.model,
    )
    notifier = EmailNotifier(
        api_key=os.environ["RESEND_API_KEY"],
        from_email=os.environ["RESEND_FROM_EMAIL"],
        to_email=os.environ["RESEND_TO_EMAIL"],
    )
    return Pipeline(source, transcriber, llm, notifier, state), config


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--config", "config_path", default="config.yaml", show_default=True)
def poll(config_path: str) -> None:
    """Check all configured channels and process new videos."""
    pipeline, config = _build_pipeline(config_path)
    processed = pipeline.poll(config)
    if processed:
        click.echo(f"Processed {len(processed)} video(s): {', '.join(processed)}")
    else:
        click.echo("No new videos found.")


@cli.command()
@click.argument("url")
@click.option("--force", is_flag=True, help="Reprocess even if already seen.")
@click.option("--config", "config_path", default="config.yaml", show_default=True)
def process(url: str, force: bool, config_path: str) -> None:
    """Process a specific YouTube video by URL or ID."""
    pipeline, _ = _build_pipeline(config_path)
    success = pipeline.process_url(url, force=force)
    if success:
        click.echo(f"Processed: {url}")
    else:
        click.echo("Already processed. Use --force to reprocess.")
```

- [ ] **Step 2: Verify CLI is importable**

```bash
source .venv/bin/activate
feedscribe --help
```

Expected:
```
Usage: feedscribe [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  poll     Check all configured channels and process new videos.
  process  Process a specific YouTube video by URL or ID.
```

- [ ] **Step 3: Commit**

```bash
git add feedscribe/cli.py
git commit -m "feat: add CLI entry point"
```

---

### Task 11: GitHub Actions Workflows

**Files:**
- Create: `.github/workflows/poll.yml`
- Create: `.github/workflows/process.yml`

**Interfaces:**
- `poll.yml` — triggered Mon/Fri 1am UTC + `workflow_dispatch`; runs `feedscribe poll`; commits back updated `processed.json`
- `process.yml` — triggered on push when `queue.txt` changes; reads each non-empty line as a URL; runs `feedscribe process <url>`; empties `queue.txt`; commits both `queue.txt` and `processed.json`

- [ ] **Step 1: Create `.github/workflows/poll.yml`**

```yaml
name: Poll YouTube Channels

on:
  schedule:
    - cron: '0 1 * * 1,5'
  workflow_dispatch:

jobs:
  poll:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -e .

      - name: Poll channels
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          RESEND_FROM_EMAIL: ${{ secrets.RESEND_FROM_EMAIL }}
          RESEND_TO_EMAIL: ${{ secrets.RESEND_TO_EMAIL }}
        run: |
          source .venv/bin/activate
          feedscribe poll

      - name: Commit updated state
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git diff --quiet || (git add .feedscribe/processed.json && git commit -m "chore: update processed state [skip ci]" && git push)
```

- [ ] **Step 2: Create `.github/workflows/process.yml`**

```yaml
name: Process YouTube Video

on:
  push:
    paths:
      - 'queue.txt'

jobs:
  process:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -e .

      - name: Process queued videos
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          RESEND_FROM_EMAIL: ${{ secrets.RESEND_FROM_EMAIL }}
          RESEND_TO_EMAIL: ${{ secrets.RESEND_TO_EMAIL }}
        run: |
          source .venv/bin/activate
          while IFS= read -r url || [ -n "$url" ]; do
            [ -z "$url" ] && continue
            feedscribe process "$url"
          done < queue.txt

      - name: Clear queue and commit state
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          > queue.txt
          git add queue.txt .feedscribe/processed.json
          git diff --cached --quiet || (git commit -m "chore: clear queue and update state [skip ci]" && git push)
```

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Actions workflows"
```

---

## Verification

1. **Run full test suite**

   ```bash
   source .venv/bin/activate
   pytest -v
   ```

   Expected: all tests pass, no warnings about missing imports.

2. **Local end-to-end test**

   Copy `.env.example` to `.env` and fill in real API keys, then:

   ```bash
   source .venv/bin/activate
   feedscribe process "https://www.youtube.com/watch?v=<any-video-id>"
   ```

   - Email arrives with subject `FeedScribe [Channel Name]: Video Title`
   - Email body is rendered HTML with TL;DR, Key Takeaways, Detailed Notes sections
   - Attachment is `channel_video_title.md` with correct Obsidian frontmatter
   - `.feedscribe/processed.json` contains the video entry

3. **Idempotency check**

   Run the same command again:

   ```bash
   feedscribe process "https://www.youtube.com/watch?v=<same-video-id>"
   ```

   Expected: `Already processed. Use --force to reprocess.` — no second email.

4. **Force flag**

   ```bash
   feedscribe process "https://www.youtube.com/watch?v=<same-video-id>" --force
   ```

   Expected: processes again, second email arrives.

5. **Poll command**

   ```bash
   feedscribe poll
   ```

   Expected: fetches recent videos from both channels, processes any not in `processed.json`.

6. **GitHub Actions — on-demand**

   Add a YouTube URL to `queue.txt`, commit and push. The `process.yml` workflow triggers, processes the video, empties `queue.txt`, and commits back. Confirm email arrives and `queue.txt` is empty in the repo.

7. **GitHub Actions — scheduled**

   Trigger `poll.yml` manually via the GitHub Actions UI (Actions → Poll YouTube Channels → Run workflow). Confirm it completes without error and commits back updated `processed.json` if new videos were found.
