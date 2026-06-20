from abc import ABC, abstractmethod

from feedscribe.config import ChannelConfig
from feedscribe.models import ContentItem


class ContentSource(ABC):
    @abstractmethod
    def fetch_recent(self, channel_cfg: ChannelConfig, max_items: int) -> list[ContentItem]: ...

    @abstractmethod
    def fetch_by_url(self, url_or_id: str) -> ContentItem: ...
