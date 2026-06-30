import base64
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
    assert call_args["to"] == ["to@example.com"]
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


def test_attachment_content_is_base64(notifier, item, notes):
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item, notes)

    content = mock_send.call_args[0][0]["attachments"][0]["content"]
    expected = base64.b64encode(notes.markdown.encode("utf-8")).decode("ascii")
    assert content == expected


def test_channel_name_title_cased_in_subject(notifier, item, notes):
    item2 = item.model_copy(update={"channel": "pragmatic_engineer"})
    notes2 = notes.model_copy(update={"filename": "pragmatic_engineer_test.md"})
    with patch("resend.Emails.send") as mock_send:
        notifier.send(item2, notes2)

    subject = mock_send.call_args[0][0]["subject"]
    assert "[Pragmatic Engineer]" in subject
