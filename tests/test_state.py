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
