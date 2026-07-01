import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from feedscribe.llm.gemini import GeminiProvider
from feedscribe.utils import to_snake
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
    assert to_snake("Why You Should Index") == "why_you_should_index"


def test_title_to_snake_punctuation():
    assert to_snake("Personal Finance 101!") == "personal_finance_101"


def test_title_to_snake_extra_spaces():
    assert to_snake("  Hello   World  ") == "hello_world"
