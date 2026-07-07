import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import feedparser

from feedscribe.config import ChannelConfig
from feedscribe.models import ContentItem
from feedscribe.utils import to_snake

API_BASE = "https://www.googleapis.com/youtube/v3"


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


class YouTubeSource:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def _api_get(self, endpoint: str, params: dict) -> dict:
        query = urllib.parse.urlencode({**params, "key": self._api_key})
        url = f"{API_BASE}/{endpoint}?{query}"
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"YouTube API request failed (HTTP {e.code}): {e.read().decode()}")

    def _resolve_channel_id(self, channel_url: str) -> str:
        match = re.search(r"/channel/(UC[\w-]+)", channel_url)
        if match:
            return match.group(1)

        handle_match = re.search(r"/(@[\w.-]+)", channel_url)
        if not handle_match:
            raise ValueError(f"Could not extract channel handle from: {channel_url}")
        handle = handle_match.group(1)

        data = self._api_get("channels", {"part": "id", "forHandle": handle})
        items = data.get("items", [])
        if not items:
            raise RuntimeError(f"No YouTube channel found for handle: {handle}")
        return items[0]["id"]

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

        data = self._api_get("videos", {"part": "snippet", "id": video_id})
        items = data.get("items", [])
        if not items:
            raise RuntimeError(f"No YouTube video found for ID: {video_id}")
        snippet = items[0]["snippet"]

        return ContentItem(
            id=video_id,
            title=snippet["title"],
            url=url,
            source="youtube",
            channel=to_snake(snippet["channelTitle"]),
            published_at=datetime.now(timezone.utc),
        )
