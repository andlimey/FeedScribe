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
