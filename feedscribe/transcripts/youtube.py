from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import ProxyConfig

from feedscribe.models import ContentItem, Transcript


class YouTubeTranscriber:
    def __init__(self, proxy_config: ProxyConfig | None = None):
        self._proxy_config = proxy_config

    def fetch(self, item: ContentItem) -> Transcript:
        segments = YouTubeTranscriptApi(proxy_config=self._proxy_config).fetch(item.id)
        text = " ".join(seg.text for seg in segments)
        return Transcript(content_id=item.id, text=text)
