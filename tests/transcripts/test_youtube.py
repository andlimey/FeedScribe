import pytest
from unittest.mock import patch
from feedscribe.transcripts.youtube import YouTubeTranscriber
from feedscribe.models import ContentItem
from datetime import datetime, timezone
from youtube_transcript_api import FetchedTranscriptSnippet


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
        FetchedTranscriptSnippet(text="Hello world", start=0.0, duration=1.0),
        FetchedTranscriptSnippet(text="how are you", start=1.0, duration=1.0),
    ]
    with patch(
        "youtube_transcript_api.YouTubeTranscriptApi.fetch",
        return_value=segments,
    ):
        transcriber = YouTubeTranscriber()
        transcript = transcriber.fetch(item)

    assert transcript.content_id == "abc123"
    assert transcript.text == "Hello world how are you"


def test_fetch_returns_correct_content_id(item):
    with patch(
        "youtube_transcript_api.YouTubeTranscriptApi.fetch",
        return_value=[FetchedTranscriptSnippet(text="Test", start=0.0, duration=1.0)],
    ):
        transcriber = YouTubeTranscriber()
        transcript = transcriber.fetch(item)

    assert transcript.content_id == item.id
