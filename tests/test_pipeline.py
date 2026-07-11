import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from feedscribe.pipeline import Pipeline
from feedscribe.models import ContentItem, Transcript, Notes
from feedscribe.config import AppConfig, ChannelConfig, LLMConfig


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
            )
        ],
        llm=LLMConfig(models=["google/gemma-4-31b-it:free", "google/gemini-2.5-flash-lite"]),
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
