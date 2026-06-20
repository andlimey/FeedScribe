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
