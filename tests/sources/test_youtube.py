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
    return YouTubeSource(api_key="test-key")


def _make_feed_mock():
    entries = []
    for video_id, title, date_tuple in [
        ("abc12345678", "Test Episode One", (2026, 6, 19, 10, 0, 0, 0, 0, 0)),
        ("def45678901", "Test Episode Two", (2026, 6, 18, 10, 0, 0, 0, 0, 0)),
        ("ghi78901234", "Test Episode Three", (2026, 6, 17, 10, 0, 0, 0, 0, 0)),
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
    assert items[0].id == "abc12345678"
    assert items[0].title == "Test Episode One"
    assert items[0].channel == "test_channel"
    assert items[0].source == "youtube"
    assert items[0].url == "https://www.youtube.com/watch?v=abc12345678"


def test_fetch_recent_respects_max_items(source, channel_cfg):
    with patch.object(source, "_resolve_channel_id", return_value="UCtest123"), \
         patch("feedparser.parse", return_value=_make_feed_mock()):
        items = source.fetch_recent(channel_cfg, max_items=2)

    assert len(items) == 2
    assert items[0].id == "abc12345678"
    assert items[1].id == "def45678901"


def _make_video_snippet(title: str, channel_title: str) -> dict:
    return {"items": [{"snippet": {"title": title, "channelTitle": channel_title}}]}


def test_fetch_by_url_full_url(source):
    with patch.object(
        source, "_api_get", return_value=_make_video_snippet("Why You Should Index", "Rational Reminder")
    ):
        item = source.fetch_by_url("https://www.youtube.com/watch?v=abc12345678")

    assert item.id == "abc12345678"
    assert item.title == "Why You Should Index"
    assert item.channel == "rational_reminder"
    assert item.source == "youtube"
    assert item.url == "https://www.youtube.com/watch?v=abc12345678"


def test_fetch_by_url_bare_id(source):
    with patch.object(source, "_api_get", return_value=_make_video_snippet("Test Title", "Test Channel")):
        item = source.fetch_by_url("abc12345678")

    assert item.id == "abc12345678"
    assert item.channel == "test_channel"


def test_fetch_by_url_short_url(source):
    with patch.object(source, "_api_get", return_value=_make_video_snippet("Test Title", "Test Channel")):
        item = source.fetch_by_url("https://youtu.be/abc12345678")

    assert item.id == "abc12345678"


def test_resolve_channel_id_from_channel_url(source):
    with patch.object(source, "_api_get") as mock_api_get:
        channel_id = source._resolve_channel_id("https://www.youtube.com/channel/UCabc123def456/videos")

    mock_api_get.assert_not_called()
    assert channel_id == "UCabc123def456"


def test_resolve_channel_id_from_handle_url(source):
    with patch.object(source, "_api_get", return_value={"items": [{"id": "UCtest123"}]}) as mock_api_get:
        channel_id = source._resolve_channel_id("https://www.youtube.com/@testchannel/videos")

    mock_api_get.assert_called_once_with("channels", {"part": "id", "forHandle": "@testchannel"})
    assert channel_id == "UCtest123"
